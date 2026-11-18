"""What the cleanup of `ask-codex ask` does when the program's main process has already exited and a child of it still holds the
pipes, and what the handler and the kills do exactly.

Plan `2026-11-18-bridge-root-guard-and-hangup`, increment D-A. The fake's control `orphan` makes the program's main process exit at
once while a child, which holds the inherited output pipes, sleeps: the case that the second look found a hang-up did not stop."""

import ast
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock

import support_codex
from test_askcodex_guards import helper_path, kit_path


class Process(support_codex.Bridge):
    """The helper run as a process of its own with a fake `codex` that is told what to do."""

    def launch(self, ignore=(), **control):
        self.control(**control)
        env = {"PATH": self.outside, "TMPDIR": self.temp, "HOME": self.base, "PYTHONPATH": kit_path()}

        def preexec():
            for number in ignore:
                signal.signal(number, signal.SIG_IGN)

        process = subprocess.Popen([sys.executable, "-B", helper_path(), "ask"], cwd=self.root, env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   preexec_fn=preexec)
        self.addCleanup(self.finish, process)
        process.stdin.write(b"hello\n")
        process.stdin.close()
        pids = os.path.join(self.outside, "pids")
        for _ in range(100):
            if os.path.exists(pids) and self.calls():
                break
            time.sleep(0.1)
        else:
            self.fail("the program did not start")
        time.sleep(0.5)  # for an orphan: the program's main process has exited by now and its child holds the pipes
        with open(pids) as handle:
            child = int(handle.read())
        self.addCleanup(self.reap, child)
        self.assertIsNone(process.poll(), "the helper ended before the signal")
        os.kill(child, 0)
        return process, child

    @staticmethod
    def finish(process):
        process.kill()
        process.wait()
        for pipe in (process.stdout, process.stderr):
            pipe.close()

    @staticmethod
    def reap(pid):
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass

    @staticmethod
    def gone(pid):
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.1)
        return False


class Orphan(Process):
    def stops(self, number, code):
        process, child = self.launch(orphan=True)
        process.send_signal(number)
        process.wait(timeout=20)
        self.assertEqual(code, process.returncode)
        self.assertTrue(self.gone(child), "the child of the program is still running")
        self.assertFalse(os.path.exists(self.calls()[0]["scratch"]), "the scratch directory is still there")

    def test_a_hang_up_kills_the_child_of_a_program_whose_main_process_has_exited(self):
        self.stops(signal.SIGHUP, 129)

    def test_a_terminate_signal_kills_the_child_of_a_program_whose_main_process_has_exited(self):
        self.stops(signal.SIGTERM, 143)

    def test_an_interrupt_kills_the_child_of_a_program_whose_main_process_has_exited(self):
        self.stops(signal.SIGINT, 130)

    def test_a_timeout_kills_the_child_of_a_program_whose_main_process_has_exited(self):
        self.control(orphan=True)
        document = self.document("--timeout", "1")
        self.assertEqual(("timeout", None, True), (document["error"], document["detail"], document["retryable"]))
        with open(os.path.join(self.outside, "pids")) as handle:
            child = int(handle.read())
        self.addCleanup(self.reap, child)
        self.assertTrue(self.gone(child), "the child of the program is still running")


class Kills(support_codex.Bridge):
    """How often the program's group is killed: once on every normal call, and once, not twice, when an interrupt comes."""

    def counting(self, raise_when):
        """Patch `kill` to count and `Popen.wait` to raise `SystemExit` when `raise_when(timeout)` holds."""
        real = subprocess.Popen.wait

        def wait(process, timeout=None):
            if raise_when(timeout):
                raise SystemExit(143)
            return real(process, timeout=timeout)

        kills = unittest.mock.patch.object(self.helper, "kill", wraps=self.helper.kill)
        waits = unittest.mock.patch.object(subprocess.Popen, "wait", wait)
        counter = kills.start()
        self.addCleanup(kills.stop)
        waits.start()
        self.addCleanup(waits.stop)
        return counter

    def test_a_successful_call_kills_the_group_once(self):
        counter = self.counting(lambda timeout: False)
        self.assertTrue(self.document()["ok"])
        self.assertEqual(1, counter.call_count)

    def test_an_interrupt_before_the_kill_kills_the_group_once(self):
        counter = self.counting(lambda timeout: isinstance(timeout, float))  # the first wait, before the normal kill
        with self.assertRaises(SystemExit):
            self.ask()
        self.assertEqual(1, counter.call_count)

    def test_an_interrupt_during_the_waits_after_the_kill_does_not_kill_again(self):
        counter = self.counting(lambda timeout: timeout == 5)  # the wait after the normal kill
        with self.assertRaises(SystemExit):
            self.ask()
        self.assertEqual(1, counter.call_count)


class Handler(Process):
    def test_the_handler_ignores_the_stop_signals_and_ends_with_128_plus_the_number(self):
        self.assertEqual((signal.SIGTERM, signal.SIGHUP, signal.SIGINT), tuple(self.helper.STOP_SIGNALS))
        for number in self.helper.STOP_SIGNALS:
            with self.subTest(number=int(number)):
                with unittest.mock.patch.object(self.helper.signal, "signal") as recorder:
                    with self.assertRaises(SystemExit) as caught:
                        self.helper.stop(number, None)
                self.assertEqual(128 + number, caught.exception.code)
                self.assertEqual({signal.SIGTERM, signal.SIGHUP, signal.SIGINT}, {call.args[0] for call in recorder.call_args_list})
                self.assertEqual({signal.SIG_IGN}, {call.args[1] for call in recorder.call_args_list})

    def test_a_signal_that_the_caller_ignores_is_not_overridden(self):
        for number in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(number=int(number)):
                process, child = self.launch(ignore=(number,), hang=True)
                process.send_signal(number)
                time.sleep(1.0)
                self.assertIsNone(process.poll(), "the helper ended on a signal its caller ignored")
                process.send_signal(signal.SIGHUP)
                process.wait(timeout=20)
                self.assertEqual(129, process.returncode)
                self.assertTrue(self.gone(child), "the program's child is still running")
                os.remove(os.path.join(self.outside, "pids"))
                os.remove(os.path.join(self.outside, "calls.jsonl"))


def calls_named(nodes, name):
    """True when a call of a function or method called `name` is in any of the syntax nodes."""
    for node in nodes:
        for each in ast.walk(node):
            if isinstance(each, ast.Call):
                func = each.func
                if (isinstance(func, ast.Attribute) and func.attr == name) or (isinstance(func, ast.Name) and func.id == name):
                    return True
    return False


class Scratch(support_codex.Bridge):
    """A structural test: no signal can be made to land between `mkdtemp` and the `try` in a test, so the shape of `ask` is pinned."""

    def test_the_scratch_directory_is_made_inside_the_try_that_removes_it_and_removed_only_if_made(self):
        with open(helper_path(), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        ask = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "ask"]
        self.assertEqual(1, len(ask))
        guarded = [node for node in ast.walk(ask[0]) if isinstance(node, ast.Try) and calls_named(node.finalbody, "rmtree")]
        self.assertEqual(1, len(guarded), "one try removes the scratch directory")
        block = guarded[0]
        self.assertTrue(calls_named(block.body, "mkdtemp"), "the scratch directory is not made inside the try")
        every = [each for each in ast.walk(ask[0]) if isinstance(each, ast.Call) and
                 isinstance(each.func, ast.Attribute) and each.func.attr == "mkdtemp"]
        self.assertEqual(1, len(every), "the scratch directory is made in one place")
        self.assertTrue(any(isinstance(statement, ast.If) and calls_named(statement.body, "rmtree")
                            for statement in block.finalbody), "the removal does not check that the directory was made")

    def test_a_scratch_directory_that_cannot_be_made_is_a_refusal_and_not_a_crash(self):
        failing = unittest.mock.patch.object(tempfile, "mkdtemp", side_effect=OSError(28, "No space left on device"))
        with failing:
            code, out, err = self.ask()
        self.assertEqual((1, ""), (code, out))
        self.assertTrue(err.startswith("refused: the call could not be started"), err)
        self.assertEqual([], self.calls(), "the program was started")


if __name__ == "__main__":
    unittest.main()
