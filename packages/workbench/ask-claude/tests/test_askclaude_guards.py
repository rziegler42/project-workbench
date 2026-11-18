"""The root guard and the hang-up of `ask-claude ask`: the matrix of `--root` spellings, forms and descendants that must be refused
(and the two cases that must be accepted), and what a SIGTERM, a SIGHUP and an ignored SIGHUP do to the helper and its program.

Plan `2026-11-18-bridge-root-guard-and-hangup`, increment A. The case-variant cells need a disk on which `.GIT` is the directory
`.git`; they are skipped, with the reason named, on a case-sensitive disk. Retained from `test_askclaude_module.py`: the exact
lower-case `.git` and `.workbench` as a relative path. New here: the case variants, the forms `./N`, `N/` and the absolute path, the
descendants, the two accepted cases, and the signals."""

import os
import signal
import subprocess
import sys
import time

import support_claude

GUARDED = (".git", ".workbench")
SUBDIRECTORY = {".git": "hooks", ".workbench": "local"}
LOWER = (".git", ".workbench")
VARIANTS = (".GIT", ".Git", ".WORKBENCH", ".WorkBench")
MESSAGE = ".git or .workbench"


class RootMatrix(support_claude.Bridge):
    def setUp(self):
        super().setUp()
        for name, sub in SUBDIRECTORY.items():
            os.makedirs(os.path.join(self.root, name, sub), exist_ok=True)

    def forms(self, name, rest=""):
        """The four forms of the path `name/rest`: plain, `./`, a trailing slash and absolute."""
        tail = name + ("/" + rest if rest else "")
        return (tail, "./" + tail, tail + "/", os.path.join(self.root, tail))

    def cells(self, names):
        for name in names:
            canonical = name.lower() if name.lower() in GUARDED else name
            for rest in ("", SUBDIRECTORY[canonical]):
                for form in self.forms(name, rest):
                    yield name, rest, form

    def resolves(self, name):
        try:
            return os.path.samefile(os.path.join(self.root, name), os.path.join(self.root, name.lower()))
        except OSError:
            return False

    def test_the_lower_case_names_their_forms_and_descendants_are_refused(self):
        for name, rest, form in self.cells(LOWER):
            with self.subTest(name=name, rest=rest, form=form):
                self.refused("--root", form, contains=MESSAGE)

    def test_the_case_variants_their_forms_and_descendants_are_refused(self):
        missing = [name for name in VARIANTS if not self.resolves(name)]
        if missing:
            self.skipTest("this disk is case-sensitive: %s is not the directory %s here" % (missing[0], missing[0].lower()))
        for name, rest, form in self.cells(VARIANTS):
            with self.subTest(name=name, rest=rest, form=form):
                self.refused("--root", form, contains=MESSAGE)

    def test_the_project_root_itself_and_a_lookalike_directory_are_accepted(self):
        for name in (".gitx", ".workbench-old", ".github"):
            os.makedirs(os.path.join(self.root, name))
        for value in (".", "./", self.root, ".gitx", "./.gitx/", ".workbench-old", ".github", "docs"):
            with self.subTest(root=value):
                self.assertTrue(self.document("--root", value)["ok"], value)
        self.assertEqual(8, len(self.calls()))

    def test_a_root_below_a_nested_git_directory_is_still_refused(self):
        os.makedirs(os.path.join(self.root, "sub", ".git", "hooks"))
        for value in ("sub/.git", "sub/.git/hooks", "./sub/.git/"):
            with self.subTest(root=value):
                self.refused("--root", value, contains=MESSAGE)


def helper_path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "helper", "ask-claude")


def kit_path():
    here = os.path.abspath(__file__)
    for _ in range(5):
        here = os.path.dirname(here)
    return os.path.join(here, "workbench")


class Signals(support_claude.Bridge):
    """The helper run as a process of its own with a fake `claude` that never exits and starts a child."""

    def start(self, ignore_hangup=False):
        self.control(hang=True)
        env = {"PATH": self.outside, "TMPDIR": self.temp, "HOME": self.base, "PYTHONPATH": kit_path()}
        preexec = (lambda: signal.signal(signal.SIGHUP, signal.SIG_IGN)) if ignore_hangup else None
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
        time.sleep(0.2)
        with open(pids) as handle:
            child = int(handle.read())
        self.addCleanup(self.reap, child)
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

    def gone(self, pid):
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.1)
        return False

    def test_a_terminate_signal_stops_the_program_and_ends_the_helper_with_143(self):
        process, child = self.start()
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=20)
        self.assertEqual(143, process.returncode)
        self.assertTrue(self.gone(child), "the program's child is still running")

    def test_a_hang_up_stops_the_program_and_ends_the_helper_with_129(self):
        process, child = self.start()
        process.send_signal(signal.SIGHUP)
        process.wait(timeout=20)
        self.assertEqual(129, process.returncode)
        self.assertTrue(self.gone(child), "the program's child is still running")

    def test_an_interrupt_stops_the_program_too(self):
        process, child = self.start()
        process.send_signal(signal.SIGINT)
        process.wait(timeout=20)
        self.assertNotEqual(0, process.returncode)
        self.assertTrue(self.gone(child), "the program's child is still running")

    def test_a_hang_up_that_the_caller_ignores_is_not_overridden(self):
        process, child = self.start(ignore_hangup=True)
        process.send_signal(signal.SIGHUP)
        time.sleep(1.0)
        self.assertIsNone(process.poll(), "the helper ended on a hang-up its caller ignored")
        os.kill(child, 0)
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=20)
        self.assertEqual(143, process.returncode)
        self.assertTrue(self.gone(child), "the program's child is still running")


if __name__ == "__main__":
    import unittest
    unittest.main()
