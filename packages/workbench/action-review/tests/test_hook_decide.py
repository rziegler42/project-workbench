"""The hook that may answer `allow` (`docs/specs/action-review.md`, "The shadow hook" and "The enforcement point").

Plan `2026-11-08-action-review-cutover-for-commit`, increment D. `hook/shadow_hook.py` still records what the engine said about each
prompted command. It now also answers `allow`, once, and only when everything below holds; in every other case it answers nothing, as
before, and it never answers `deny`:

* the engine reviewed the exact command: the outcome is `reviewed`, agrees with the exit code, and the verdict object is whole with
  `approve` and no failed check;
* the engine's `facts:` line (the describe object) is `ok`, whole, and holds `given_state_digest` and `state_digest` that are the same
  64 lowercase hexadecimal characters, and `leave_other_staged` is false; the command text carries `--state-digest` and that digest,
  and not `--leave-other-staged`;
* `wb settings`, run from the command's directory, prints exactly one line for the key of the action (`wb run <command> <action>`,
  worked out from the rule's name and the object's action) and it says `delegated`.

The engine's own bytes are made by the real engine (as in `test_hook_shadow_hook`); a fake `wb` replays them and answers `settings`.
Written before the code."""

import io
import json
import os
import stat
import sys
import time
import unittest
import unittest.mock

from test_actionreview_output import HEAD, answered, bridge_failed, commit_doc, described, reply
from test_hook_shadow_hook import HOOK, NO_RULE, Base, Replay
from workbench.wbkit import call

DIGEST = "c" * 64
OTHER = "d" * 64
KEY = "wb run safe-git commit"
DECIDED = "wb run safe-git commit --expected-head %s --subject 'Add it' --state-digest %s -- a.txt" % (HEAD, DIGEST)
ALLOW = {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}

WB_SOURCE = """#!%s
import json, os, sys, time
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "spec2.json")) as handle:
    spec = json.load(handle)
with open(os.path.join(here, "calls.jsonl"), "a") as handle:
    handle.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "env": dict(os.environ)}) + "\\n")
part = spec["settings"] if sys.argv[1:2] == ["settings"] else spec["engine"]
time.sleep(part["sleep"])
sys.stdout.buffer.write(bytes.fromhex(part["out"]))
sys.stderr.buffer.write(bytes.fromhex(part["err"]))
sys.exit(part["code"])
"""


def settings_text(level="delegated", key=KEY, extra=()):
    """What `wb settings` prints: many `level` lines, one for the key, and the other lines it prints."""
    lines = ["checkpoint approve-plan: stop", "cap review-rounds: 3", "level approve-plan: ask", "level wb run safe-git remove: none",
             "level wb run safe-git describe: none"]
    if level is not None:
        lines.append("level %s: %s" % (key, level))
    lines += list(extra) + ["key %s: class=reads offers=block,delegated,none" % key, "risk: approve-plan is set to ask"]
    return ("\n".join(lines) + "\n").encode("ascii")


class Decide(Base):
    def approve(self, command=DECIDED, **facts):
        base = dict(state_digest=DIGEST, given_state_digest=DIGEST)
        base.update(facts)
        return self.engine(command, describe=described(commit_doc(**base)))

    def install(self, engine, settings=None):
        settings = Replay(0, settings_text()) if settings is None else settings
        with open(self.wb, "w") as handle:
            handle.write(WB_SOURCE % sys.executable)
        os.chmod(self.wb, 0o755)
        path = os.path.join(self.wbdir, "calls.jsonl")
        if os.path.exists(path):
            os.remove(path)
        with open(os.path.join(self.wbdir, "spec2.json"), "w") as handle:
            json.dump({"engine": {"code": engine.code, "out": engine.out.hex(), "err": engine.err.hex(), "sleep": engine.sleep},
                       "settings": {"code": settings.code, "out": settings.out.hex(), "err": settings.err.hex(),
                                    "sleep": settings.sleep}}, handle)

    def calls(self):
        path = os.path.join(self.wbdir, "calls.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def go(self, engine, settings=None, command=DECIDED):
        """``(exit code, what was written to the answer stream, standard error)`` of one run of the hook."""
        self.install(engine, settings)
        out, err = io.StringIO(), io.StringIO()
        code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(command)).encode("utf-8")), err,
                             home=self.home, out=out)
        return code, out.getvalue(), err.getvalue()

    def allowed(self, result):
        self.assertEqual(0, result[0], result[2])
        self.assertEqual(ALLOW, json.loads(result[1]), result)
        self.assertEqual(json.dumps(ALLOW, separators=(",", ":")) + "\n", result[1])

    def silent(self, result, note=""):
        self.assertEqual((0, ""), result[:2], (note, result[2]))

    def edited(self, replay, edit):
        """`replay` with its `facts:` line changed by `edit(document)`; ``None`` from `edit` removes the line."""
        lines = replay.err.decode("ascii").split("\n")
        for position, line in enumerate(lines):
            if line.startswith("facts: "):
                document = edit(json.loads(line[len("facts: "):]))
                if document is None:
                    del lines[position]
                else:
                    lines[position] = "facts: " + json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
                return Replay(replay.code, replay.out, "\n".join(lines).encode("ascii"))
        self.fail("the engine printed no facts line")


class Allowing(Decide):
    def test_a_whole_approve_with_a_bound_digest_and_the_key_at_delegated_gives_exactly_one_allow(self):
        self.allowed(self.go(self.approve()))

    def test_the_answer_has_no_updated_input_and_nothing_else(self):
        out = self.go(self.approve())[1]
        self.assertEqual(1, out.count("\n"))
        self.assertNotIn("updatedInput", out)
        self.assertEqual({"hookSpecificOutput"}, set(json.loads(out)))
        self.assertEqual({"hookEventName", "decision"}, set(json.loads(out)["hookSpecificOutput"]))
        self.assertEqual({"behavior"}, set(json.loads(out)["hookSpecificOutput"]["decision"]))

    def test_run_as_a_program_it_prints_the_same_bytes_to_standard_output(self):
        self.install(self.approve())
        run = self.program(["--wb", self.wb], json.dumps(self.event(DECIDED)).encode("utf-8"))
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertEqual((json.dumps(ALLOW, separators=(",", ":")) + "\n").encode("ascii"), run.stdout)

    def test_it_asks_the_installer_from_the_commands_directory_with_the_clean_environment(self):
        self.go(self.approve())
        calls = self.calls()
        self.assertEqual(2, len(calls), calls)
        self.assertEqual(["run", "action-review", "review", "--log-row", "--collect", DECIDED], calls[0]["argv"])
        self.assertEqual(["settings"], calls[1]["argv"])
        self.assertEqual(os.path.realpath(self.cwd), os.path.realpath(calls[1]["cwd"]))
        self.assertEqual({"PATH", "HOME", "LANG"}, set(calls[1]["env"]) & {"PATH", "HOME", "LANG", "PYTHONPATH", "WB_ENV"})
        self.assertTrue(calls[1]["env"]["PATH"].startswith(self.wbdir + os.pathsep))

    def test_the_row_says_allow_and_is_written_before_the_answer(self):
        seen = []
        real = self.mod.emit

        def watching(*arguments):
            rows, _ = self.rows("verdicts.jsonl")
            seen.append([row.get("answer") for row in rows])
            return real(*arguments)

        with unittest.mock.patch.object(self.mod, "emit", watching):
            result = self.go(self.approve())
        self.allowed(result)
        self.assertEqual([["allow"]], seen)
        row = self.one_verdict()
        self.assertEqual(("reviewed", "approve", [], "allow"), (row["outcome"], row["verdict"], row["failed_checks"], row["answer"]))

    def test_a_row_that_cannot_be_written_gives_no_answer_whatever_way_the_write_fails(self):
        """After the security review of increment D: a delegated commit with no record of it is not accepted. The engine's approve
        still stands (the prompt is the owner's), but the hook does not skip the prompt."""
        for name, effect in (("an OSError", OSError("disk")), ("a store error", self.store.StoreError("the store refuses")),
                             ("any exception", RuntimeError("boom"))):
            with self.subTest(case=name):
                with unittest.mock.patch.object(self.store, "append", side_effect=effect):
                    result = self.go(self.approve())
                self.silent(result, name)
                self.assertEqual(2, len(self.calls()), "the engine and the settings were still asked: the review itself ran")

    def test_an_unwritable_store_gives_no_answer(self):
        self.install(self.approve())
        os.chmod(self.home, 0o500)
        self.addCleanup(os.chmod, self.home, 0o700)
        err = io.StringIO()
        out = io.StringIO()
        code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(DECIDED)).encode("utf-8")), err, home=self.home, out=out)
        self.assertEqual((0, ""), (code, out.getvalue()), err.getvalue())
        self.assertIn("could not record", err.getvalue())

    def test_a_row_written_through_the_fallback_still_carries_the_answer_and_is_answered(self):
        """The first write of the verdict row is refused (for a field the store dislikes); the plain row is then written, with the
        answer, and that is a row: the answer follows."""
        real = self.store.append
        calls = []

        def refusing_once(name, row, home):
            calls.append(name)
            if len(calls) == 1:
                raise self.store.StoreError("the first row is refused")
            return real(name, row, home)

        with unittest.mock.patch.object(self.store, "append", refusing_once):
            result = self.go(self.approve())
        self.allowed(result)
        self.assertEqual("allow", self.one_verdict()["answer"])

    def test_the_answer_is_not_sent_before_the_row_is_known_to_be_written(self):
        order = []
        real_append, real_emit = self.store.append, self.mod.emit

        def appending(name, row, home):
            order.append("row:" + name)
            return real_append(name, row, home)

        def emitting(*arguments):
            order.append("emit")
            return real_emit(*arguments)

        with unittest.mock.patch.object(self.store, "append", appending), unittest.mock.patch.object(self.mod, "emit", emitting):
            self.allowed(self.go(self.approve()))
        self.assertEqual("emit", order[-1])
        self.assertIn("row:verdicts.jsonl", order[:-1])

    def test_an_answer_stream_that_cannot_be_written_is_noted_by_emit_and_the_row_still_says_the_hook_decided(self):
        self.install(self.approve())
        out, err = io.StringIO(), io.StringIO()
        out.close()
        code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(DECIDED)).encode("utf-8")), err, home=self.home, out=out)
        self.assertEqual(0, code)
        self.assertIn("the answer could not be written", err.getvalue())
        self.assertNotIn("the hook stopped on", err.getvalue())
        self.assertEqual("allow", self.one_verdict()["answer"])

    def test_a_row_that_was_not_answered_has_no_answer_field(self):
        self.silent(self.go(self.approve(), Replay(0, settings_text("none"))))
        self.assertNotIn("answer", self.one_verdict())

    def test_without_an_answer_stream_it_answers_nothing(self):
        self.install(self.approve())
        err = io.StringIO()
        code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(DECIDED)).encode("utf-8")), err, home=self.home)
        self.assertEqual(0, code)
        self.assertNotIn("answer", self.one_verdict())


FLOOD = """#!%s
import os, sys
with open(%r, "w") as handle:
    handle.write(str(os.getpid()))
block = b"x" * 65536
stream = sys.stdout.buffer if %r == "stdout" else sys.stderr.buffer
while True:
    stream.write(block)
    stream.flush()
"""

FLOODING_SETTINGS = """#!%s
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
if sys.argv[1:2] == ["settings"]:
    with open(os.path.join(here, "pid"), "w") as handle:
        handle.write(str(os.getpid()))
    block = b"x" * 65536
    while True:
        sys.stdout.buffer.write(block)
        sys.stdout.buffer.flush()
with open(os.path.join(here, "spec2.json")) as handle:
    part = json.load(handle)["engine"]
sys.stdout.buffer.write(bytes.fromhex(part["out"]))
sys.stderr.buffer.write(bytes.fromhex(part["err"]))
sys.exit(part["code"])
"""


class TheCap(Decide):
    """After the security review of increment D: a child's output is read up to the cap and no further. A child that passes the cap is
    stopped (its whole process group), the part read is no more than the cap and one read over, and the hook gives no answer."""
    def flood(self, which):
        pidfile = os.path.join(self.wbdir, "pid")
        with open(self.wb, "w") as handle:
            handle.write(FLOOD % (sys.executable, pidfile, which))
        os.chmod(self.wb, 0o755)
        return pidfile

    def test_a_child_that_never_stops_writing_is_stopped_at_the_cap_on_either_stream(self):
        for which in ("stdout", "stderr"):
            with self.subTest(stream=which):
                pidfile = self.flood(which)
                started = time.monotonic()
                with unittest.mock.patch.object(self.mod, "MAX_STREAM", 200000):
                    code, out, err, timed_out = self.mod._launch(self.wb, ["settings"], self.cwd, self.home, 20, 1)
                self.assertLess(time.monotonic() - started, 10, "it stopped at the cap, not at the time limit")
                self.assertFalse(timed_out)
                held = out if which == "stdout" else err
                self.assertGreater(len(held), 200000, "the part read is over the cap, so the caller can tell")
                self.assertLessEqual(len(held), 200000 + (1 << 17), "and not much over it")
                self.assertLessEqual(len(out if which == "stderr" else err), 200000)
                with open(pidfile) as handle:
                    pid = int(handle.read())
                time.sleep(0.3)
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)

    def test_an_engine_that_floods_is_a_failure_with_a_row_and_no_answer(self):
        self.flood("stderr")
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.object(self.mod, "MAX_STREAM", 200000):
            code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(DECIDED)).encode("utf-8")), err, home=self.home,
                                 out=out)
        self.assertEqual((0, ""), (code, out.getvalue()))
        self.assertEqual("failed", self.one_verdict()["outcome"])

    def test_a_settings_command_that_floods_gives_no_answer_and_is_stopped(self):
        """The engine's bytes are the real ones; only `settings` floods."""
        pidfile = os.path.join(self.wbdir, "pid")
        self.install(self.approve())
        with open(self.wb, "w") as handle:
            handle.write(FLOODING_SETTINGS % sys.executable)
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.object(self.mod, "MAX_STREAM", 200000):
            code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(DECIDED)).encode("utf-8")), err, home=self.home,
                                 out=out)
        self.assertEqual((0, ""), (code, out.getvalue()), err.getvalue())
        with open(pidfile) as handle:
            pid = int(handle.read())
        time.sleep(0.3)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_a_child_that_ignores_a_closed_pipe_is_killed_not_left_running(self):
        """Closing the pipes ends a child that dies of the broken pipe; this one catches it and carries on, so only the kill stops it."""
        pidfile = os.path.join(self.wbdir, "pid")
        with open(self.wb, "w") as handle:
            handle.write("#!%s\nimport os, signal, sys, time\nsignal.signal(signal.SIGPIPE, signal.SIG_IGN)\n"
                         "open(%r, 'w').write(str(os.getpid()))\nblock = b'x' * 65536\nwhile True:\n    try:\n"
                         "        sys.stdout.buffer.write(block)\n        sys.stdout.buffer.flush()\n    except OSError:\n"
                         "        time.sleep(0.05)\n" % (sys.executable, pidfile))
        os.chmod(self.wb, 0o755)
        with unittest.mock.patch.object(self.mod, "MAX_STREAM", 200000):
            self.mod._launch(self.wb, ["settings"], self.cwd, self.home, 20, 1)
        with open(pidfile) as handle:
            pid = int(handle.read())
        time.sleep(0.3)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        os.kill(pid, 9)
        self.fail("the child that passed the cap is still running")

    def test_a_child_that_closes_its_pipes_and_stays_running_is_timed_out_and_killed(self):
        pidfile = os.path.join(self.wbdir, "pid")
        with open(self.wb, "w") as handle:
            handle.write("#!%s\nimport os, time\nopen(%r, 'w').write(str(os.getpid()))\nos.close(1)\nos.close(2)\ntime.sleep(60)\n"
                         % (sys.executable, pidfile))
        os.chmod(self.wb, 0o755)
        started = time.monotonic()
        code, out, err, timed_out = self.mod._launch(self.wb, ["settings"], self.cwd, self.home, 1, 1)
        self.assertTrue(timed_out)
        self.assertLess(time.monotonic() - started, 6)
        with open(pidfile) as handle:
            pid = int(handle.read())
        time.sleep(0.3)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_a_settings_command_whose_error_stream_passes_the_cap_gives_no_answer(self):
        """The second look: a child that was cut at the cap on its error stream may have exited 0 with its output half read."""
        real = self.mod._launch

        def cut(wb, arguments, cwd, home_dir, wait, second):
            if arguments[:1] == ["settings"]:
                return 0, settings_text("delegated"), b"x" * (self.mod.MAX_STREAM + 1), False
            return real(wb, arguments, cwd, home_dir, wait, second)

        self.install(self.approve())
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.object(self.mod, "_launch", cut):
            code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(DECIDED)).encode("utf-8")), err, home=self.home,
                                 out=out)
        self.assertEqual((0, ""), (code, out.getvalue()), err.getvalue())

    def test_a_row_for_the_collected_facts_that_fails_after_the_verdict_row_does_not_leave_the_prompt_or_the_row_in_doubt(self):
        """The second look: the verdict row is on disk with `answer: allow`; a later write raising something other than a store error must
        not make the hook give no answer for a row that exists. The prompt is skipped, as the row says."""
        real = self.store.append
        calls = []

        def second_fails(name, row, home):
            calls.append(name)
            if len(calls) == 2:
                raise RuntimeError("the second write breaks")
            return real(name, row, home)

        with unittest.mock.patch.object(self.store, "append", second_fails):
            result = self.go(self.approve())
        self.assertEqual(["verdicts.jsonl", "collected.jsonl"], calls)
        self.allowed(result)
        self.assertEqual("allow", self.one_verdict()["answer"])

    def test_output_exactly_at_the_cap_is_still_read_whole(self):
        with open(self.wb, "w") as handle:
            handle.write("#!%s\nimport sys\nsys.stdout.buffer.write(b'y' * 1000)\n" % sys.executable)
        os.chmod(self.wb, 0o755)
        with unittest.mock.patch.object(self.mod, "MAX_STREAM", 1000):
            code, out, err, timed_out = self.mod._launch(self.wb, ["settings"], self.cwd, self.home, 20, 1)
        self.assertEqual((0, b"y" * 1000, b"", False), (code, out, err, timed_out))


class NotAnApprove(Decide):
    """Every outcome of the engine that is not a whole approve gives no answer, and does not ask the installer."""

    def cases(self):
        base = self.approve()
        lines = base.err.decode("ascii").split("\n")
        body = json.loads(base.out)
        yield "model decline", self.engine(DECIDED, describe=described(commit_doc(state_digest=DIGEST, given_state_digest=DIGEST)),
                                           bridge=answered(reply("decline", ["scope_is_coherent"], "Mixed.")))
        yield "code decline", self.engine(DECIDED, describe=described(commit_doc(head="b" * 40, state_digest=DIGEST,
                                                                               given_state_digest=DIGEST)))
        yield "state digest differs, so the engine declines", self.engine(DECIDED, describe=described(commit_doc(
            state_digest=OTHER, given_state_digest=DIGEST)))
        yield "no rule", self.engine(NO_RULE)
        yield "outside the grammar", self.engine(DECIDED + " && ls")
        yield "describe fails", self.engine(DECIDED, describe=call.Result(1, b"", b"", False, False))
        yield "bridge fails", self.engine(DECIDED, bridge=bridge_failed())
        yield "exit 1, no lines", Replay(1)
        yield "exit 2, no lines", Replay(2)
        yield "exit 0, garbage", Replay(0, b"allow\n", b"outcome: nonsense\n")
        yield "exit 7", Replay(7, b"{}", b"x")
        yield "engine prints allow-shaped JSON", Replay(0, json.dumps(ALLOW).encode() + b"\n")
        yield "an exit code that disagrees", Replay(1, base.out, base.err)
        yield "an exit 2 for an approve", Replay(2, base.out, base.err)
        yield "a malformed outcome line", Replay(0, base.out, "\n".join(lines[:-2] + ["outcome: nonsense", ""]).encode("ascii"))
        yield "an approve with a failed check", Replay(0, (json.dumps(dict(body, failed_checks=["scope_is_coherent"])) + "\n").encode(),
                                                      base.err)
        yield "a verdict with an extra field", Replay(0, (json.dumps(dict(body, extra=1)) + "\n").encode(), base.err)
        yield "a verdict of allow", Replay(0, (json.dumps(dict(body, verdict="allow")) + "\n").encode(), base.err)
        yield "two lines of verdict", Replay(0, base.out + base.out, base.err)
        yield "an empty answer", Replay(0, b"", base.err)

    def test_none_of_them_gives_an_answer_or_asks_the_installer(self):
        for name, replay in self.cases():
            with self.subTest(case=name):
                result = self.go(replay)
                self.silent(result, name)
                self.assertEqual(1, len(self.calls()), name)

    def test_a_timeout_of_the_engine_gives_no_answer(self):
        self.install(self.approve())
        with unittest.mock.patch.object(self.mod, "WAIT_SECONDS", 1), unittest.mock.patch.object(self.mod, "SECOND_WAIT", 1):
            slow = self.approve()
            result = self.go(Replay(slow.code, slow.out, slow.err, sleep=4))
        self.silent(result)
        self.assertEqual("timeout", self.one_verdict()["outcome"])


class TheDigest(Decide):
    def test_the_edit_helper_changes_a_fact_and_a_changed_approve_is_no_longer_answered(self):
        base = self.approve()
        self.silent(self.go(self.edited(base, lambda d: dict(d, ok=False))))

    def test_the_hook_reads_the_two_digests_in_the_facts_line_and_wants_them_equal_and_whole(self):
        def facts(**changes):
            return lambda d: dict(d, facts=dict(d["facts"], **changes))

        cases = {
            "both null": facts(state_digest=None, given_state_digest=None),
            "given null": facts(given_state_digest=None),
            "computed null": facts(state_digest=None),
            "they differ": facts(state_digest=OTHER),
            "uppercase": facts(state_digest=DIGEST.upper(), given_state_digest=DIGEST.upper()),
            "63 characters": facts(state_digest=DIGEST[:63], given_state_digest=DIGEST[:63]),
            "65 characters": facts(state_digest=DIGEST + "c", given_state_digest=DIGEST + "c"),
            "not hexadecimal": facts(state_digest="g" * 64, given_state_digest="g" * 64),
            "a number": facts(state_digest=5, given_state_digest=5),
            "a list": facts(state_digest=[DIGEST], given_state_digest=[DIGEST]),
            "padded": facts(state_digest=DIGEST + "\n", given_state_digest=DIGEST + "\n"),
            "leave other staged": facts(leave_other_staged=True),
            "leave other staged missing": lambda d: dict(d, facts={k: v for k, v in d["facts"].items() if k != "leave_other_staged"}),
            "the digests missing": lambda d: dict(d, facts={k: v for k, v in d["facts"].items()
                                                           if k not in ("state_digest", "given_state_digest")}),
            "not ok": lambda d: dict(d, ok=False),
            "truncated": lambda d: dict(d, truncated=True),
            "errors": lambda d: dict(d, errors=["path_unknown"]),
            "ok missing": lambda d: {k: v for k, v in d.items() if k != "ok"},
            "facts not an object": lambda d: dict(d, facts=[DIGEST]),
            "facts missing": lambda d: {k: v for k, v in d.items() if k != "facts"},
            "another action": lambda d: dict(d, action="remove"),
            "no action": lambda d: {k: v for k, v in d.items() if k != "action"},
            "an action of the wrong form": lambda d: dict(d, action="Commit"),
            "the line is gone": lambda d: None,
        }
        base = self.approve()
        for name, edit in cases.items():
            with self.subTest(case=name):
                self.silent(self.go(self.edited(base, edit)), name)

    def test_a_digest_of_the_wrong_form_gives_no_answer_even_when_the_command_carries_it(self):
        """The second line cannot stand in for the first: the command holds the odd digest, so only the form of it can stop the hook."""
        base = self.approve()
        for name, odd in (("65 characters", DIGEST + "c"), ("a newline after it", DIGEST + "\n"), ("a space after it", DIGEST + " "),
                          ("uppercase", DIGEST.upper()), ("63 characters", DIGEST[:63]), ("not hexadecimal", "g" * 64),
                          ("a prefix of a longer one", DIGEST + "0123")):
            with self.subTest(case=name):
                edited = self.edited(base, lambda d: dict(d, facts=dict(d["facts"], state_digest=odd, given_state_digest=odd)))
                self.silent(self.go(edited, command=DECIDED.replace(DIGEST, odd)), name)

    def test_the_facts_line_that_is_not_json_gives_no_answer(self):
        base = self.approve()
        lines = base.err.decode("ascii").split("\n")
        broken = [("facts: {" if line.startswith("facts: ") else line) for line in lines]
        self.silent(self.go(Replay(base.code, base.out, "\n".join(broken).encode("ascii"))))

    def test_a_command_with_no_digest_gets_no_answer_although_the_engine_approves_it(self):
        replay = self.engine("wb run safe-git commit --expected-head %s --subject 'Add it' -- a.txt" % HEAD)
        self.assertEqual("approve", json.loads(replay.out)["verdict"])
        self.silent(self.go(replay, command="wb run safe-git commit --expected-head %s --subject 'Add it' -- a.txt" % HEAD))

    def test_the_command_text_must_carry_the_option_and_the_digest_and_not_leave_other_staged(self):
        base = self.approve()
        plain = "wb run safe-git commit --expected-head %s --subject 'Add it' -- a.txt" % HEAD
        other = DECIDED.replace(DIGEST, OTHER)
        staged = DECIDED.replace("-- a.txt", "--leave-other-staged -- a.txt")
        for name, command in (("no option", plain), ("another digest", other), ("leave other staged", staged)):
            with self.subTest(case=name):
                self.silent(self.go(base, command=command), name)

    def test_a_command_that_holds_the_digest_but_not_the_option_gets_no_answer(self):
        """The first clause of the second line on its own: the digest is in the command (in the subject), the option is not."""
        base = self.approve()
        command = "wb run safe-git commit --expected-head %s --subject '%s' -- a.txt" % (HEAD, DIGEST)
        self.silent(self.go(base, command=command))

    def test_a_facts_line_that_comes_before_the_log_row_is_not_believed(self):
        base = self.approve()
        lines = base.err.decode("ascii").split("\n")
        facts = [line for line in lines if line.startswith("facts: ")][0]
        row = [line for line in lines if line.startswith("log-row: ")][0]
        moved = [line for line in lines if line != facts]
        moved.insert(moved.index(row), facts)
        self.assertLess(moved.index(facts), moved.index(row))
        self.silent(self.go(Replay(base.code, base.out, "\n".join(moved).encode("ascii"))))
        self.allowed(self.go(base))     # in the engine's own order it is answered

    def test_a_digest_only_inside_the_body_is_not_a_digest(self):
        command = "wb run safe-git commit --expected-head %s --subject 'x' --body 'see --state-digest %s' -- a.txt" % (HEAD, DIGEST)
        replay = self.engine(command, describe=described(commit_doc(state_digest=DIGEST, given_state_digest=None)))
        self.assertEqual("approve", json.loads(replay.out)["verdict"])
        self.silent(self.go(replay, command=command))

    def test_the_real_engine_with_leave_other_staged_is_not_answered_either(self):
        command = DECIDED.replace("-- a.txt", "--leave-other-staged -- a.txt")
        replay = self.engine(command, describe=described(commit_doc(state_digest=DIGEST, given_state_digest=DIGEST,
                                                                    leave_other_staged=True)))
        self.silent(self.go(replay, command=command))


class TheKey(Decide):
    def go_with(self, settings, engine=None):
        return self.go(self.approve() if engine is None else engine, settings)

    def test_only_the_exact_word_delegated_gives_an_answer(self):
        for level in ("none", "block", "ask", "Delegated", "delegated ", " delegated", "delegate", "", "delegated\tx", "deleg"):
            with self.subTest(level=level):
                self.silent(self.go_with(Replay(0, settings_text(level))), level)

    def test_a_key_with_no_line_or_with_two_gives_no_answer(self):
        self.silent(self.go_with(Replay(0, settings_text(None))))
        doubled = settings_text("delegated", extra=("level %s: delegated" % KEY,))
        self.silent(self.go_with(Replay(0, doubled)))
        mixed = settings_text("delegated", extra=("level %s: none" % KEY,))
        self.silent(self.go_with(Replay(0, mixed)))

    def test_another_keys_line_is_not_this_keys(self):
        other = settings_text("delegated", key="wb run safe-git remove")
        self.silent(self.go_with(Replay(0, other)))
        longer = settings_text("delegated", key=KEY + "-more")
        self.silent(self.go_with(Replay(0, longer)))
        prefix = settings_text("delegated", key="wb run safe-git")
        self.silent(self.go_with(Replay(0, prefix)))

    def test_a_settings_command_that_fails_or_prints_badly_gives_no_answer(self):
        good = settings_text("delegated")
        for name, replay in (("exit 1", Replay(1, good)), ("exit 2", Replay(2, good)), ("exit 127", Replay(127, good)),
                             ("empty", Replay(0, b"")), ("garbage", Replay(0, b"allow\n")),
                             ("not ascii", Replay(0, good + "level é: x\n".encode("utf-8"))),
                             ("a NUL byte", Replay(0, good + b"\x00")), ("a refusal", Replay(1, b"", b"refused: no project\n"))):
            with self.subTest(case=name):
                self.silent(self.go_with(replay), name)

    def test_an_output_over_the_limit_gives_no_answer(self):
        big = settings_text("delegated") + b"x" * ((2 << 20) + 10)
        self.silent(self.go_with(Replay(0, big)))

    def test_a_settings_command_that_is_too_slow_gives_no_answer_in_time(self):
        started = time.monotonic()
        with unittest.mock.patch.object(self.mod, "SETTINGS_SECONDS", 1):
            result = self.go_with(Replay(0, settings_text("delegated"), sleep=8))
        self.silent(result)
        self.assertLess(time.monotonic() - started, 6)

    def test_the_removal_is_not_answered_even_when_the_table_says_delegated_for_it(self):
        replay = self.engine("wb run safe-git remove --confirm -- old.txt")
        self.silent(self.go(replay, Replay(0, settings_text("delegated", key="wb run safe-git remove")),
                            command="wb run safe-git remove --confirm -- old.txt"))

    def test_a_rule_that_is_not_named_after_its_action_gives_no_key_and_no_answer(self):
        base = self.approve()
        lines = base.err.decode("ascii").split("\n")
        row = [line for line in lines if line.startswith("log-row: ")][0]
        renamed = json.loads(row[len("log-row: "):])
        for rule in ("safe-git", "safe-git-remove", "commit", "-commit", "Safe-git-commit", "x" * 200 + "-commit", 5, None):
            with self.subTest(rule=rule):
                changed = [("log-row: " + json.dumps(dict(renamed, rule=rule))) if line == row else line for line in lines]
                # The settings print a line for the key the rule would give if nothing checked its form, so that only the check stops it.
                key = "wb run %s commit" % rule[:-len("-commit")] if isinstance(rule, str) and rule.endswith("-commit") else KEY
                self.silent(self.go(Replay(base.code, base.out, "\n".join(changed).encode("ascii")),
                                    Replay(0, settings_text("delegated", key=key))), repr(rule))

    def test_an_action_of_the_wrong_form_gives_no_answer_although_the_settings_name_its_key(self):
        base = self.approve()
        lines = base.err.decode("ascii").split("\n")
        row = [line for line in lines if line.startswith("log-row: ")][0]
        renamed = json.loads(row[len("log-row: "):])
        for action in ("Commit", "commit!", "1commit", "c" * 33, "com mit"):
            with self.subTest(action=action):
                edited = self.edited(Replay(base.code, base.out, "\n".join(
                    [("log-row: " + json.dumps(dict(renamed, rule="safe-git-" + action))) if line == row else line
                     for line in lines]).encode("ascii")), lambda d: dict(d, action=action))
                self.silent(self.go(edited, Replay(0, settings_text("delegated", key="wb run safe-git " + action))), action)

    def test_a_project_the_installer_does_not_know_gives_no_answer(self):
        self.silent(self.go_with(Replay(1, b"", b"refused: this is not inside a workbench project\n")))

    def test_no_time_left_gives_no_answer_and_does_not_ask(self):
        with unittest.mock.patch.object(self.mod, "DECIDE_BEFORE", -1), \
                unittest.mock.patch.object(self.mod, "read_level", return_value="delegated") as asked:
            result = self.go(self.approve())
        self.silent(result)
        self.assertEqual(0, asked.call_count)

    def test_the_settings_are_given_no_more_time_than_is_left(self):
        """The limit of the settings call is the smaller of its own and the time left: it is slow (4 s) but within its own 10 s."""
        started = time.monotonic()
        with unittest.mock.patch.object(self.mod, "DECIDE_BEFORE", 2.0), unittest.mock.patch.object(self.mod, "SETTINGS_SECONDS", 10):
            result = self.go(self.approve(), Replay(0, settings_text("delegated"), sleep=4))
        self.silent(result)
        self.assertLess(time.monotonic() - started, 8)

    def test_with_enough_time_the_same_slow_settings_are_answered(self):
        with unittest.mock.patch.object(self.mod, "DECIDE_BEFORE", 28.0), unittest.mock.patch.object(self.mod, "SETTINGS_SECONDS", 10):
            self.allowed(self.go(self.approve(), Replay(0, settings_text("delegated"), sleep=1)))


class TheRow(Decide):
    def row(self, **changes):
        base = {"ts": "2026-11-08T10:00:00Z", "command_sha256": "a" * 64, "outcome": "reviewed", "verdict": "approve",
                "failed_checks": [], "reason": "ok", "reviewed": True, "no_review_reason": None}
        base.update(changes)
        return base

    def test_the_store_accepts_the_answer_on_a_reviewed_approve_only(self):
        check = self.store.check_row
        self.assertIsNone(check("verdicts.jsonl", self.row(answer="allow")))
        self.assertIsNone(check("verdicts.jsonl", self.row(answer=None)))
        self.assertIsNone(check("verdicts.jsonl", self.row()))
        self.assertIsNotNone(check("verdicts.jsonl", self.row(answer="deny")))
        self.assertIsNotNone(check("verdicts.jsonl", self.row(answer="allowed")))
        self.assertIsNotNone(check("verdicts.jsonl", self.row(answer=True)))
        self.assertIsNotNone(check("verdicts.jsonl", self.row(verdict="decline", failed_checks=["x"], answer="allow")))
        self.assertIsNotNone(check("verdicts.jsonl", self.row(outcome="no_rule", reviewed=False, verdict=None, failed_checks=[],
                                                              no_review_reason="no_rule", answer="allow")))

    def test_an_old_row_without_the_field_is_still_read(self):
        self.assertIsNone(self.store.check_row("verdicts.jsonl", self.row()))


class Static(Decide):
    """What the file may contain: one function writes the answer, and nothing in it is a denial."""

    def parsed(self):
        import ast
        with open(HOOK, "rb") as handle:
            text = handle.read().decode()
        return text, ast.parse(text)

    def test_no_code_path_prints_and_only_the_emit_function_touches_standard_output(self):
        import ast
        text, tree = self.parsed()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotEqual("print", node.func.id)
        emitters = []
        for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            names = {a.attr for a in ast.walk(function) if isinstance(a, ast.Attribute)}
            if names & {"stdout", "__stdout__", "fdopen", "dup2", "write"} and function.name == "emit":
                emitters.append(function.name)
            if function.name != "emit":
                for attribute in ast.walk(function):
                    if isinstance(attribute, ast.Attribute):
                        # `_launch` reads the pipe of the child it started (`proc.stdout`), which is not the hook's own standard output
                        child_pipe = function.name == "_launch" and attribute.attr == "stdout" \
                            and isinstance(attribute.value, ast.Name) and attribute.value.id == "proc"
                        if not child_pipe:
                            self.assertNotIn(attribute.attr, ("stdout", "__stdout__", "fdopen", "dup2"), function.name)
        self.assertEqual(["emit"], emitters)
        # What the shadow's own rule forbade, kept: no write by file descriptor, no program started or replaced, and nothing written to
        # the answer stream outside `emit`.
        for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name != "emit"]:
            for node in ast.walk(function):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id == "os":
                        self.assertNotIn(node.attr, ("write", "writev", "sendfile", "system", "popen", "exec", "execv", "execve"),
                                         function.name)
                    if node.value.id == "out":
                        self.assertNotIn(node.attr, ("write", "writelines", "buffer", "fileno"), function.name)

    def test_the_word_deny_and_updated_input_are_nowhere_and_the_answer_is_built_once(self):
        text, _ = self.parsed()
        for word in ("\"deny\"", "'deny'", "updatedInput", "updated_input", "\"ask\"", "suggestions"):
            self.assertNotIn(word, text, word)
        self.assertEqual(1, text.count("hookSpecificOutput"))
        self.assertEqual(1, text.count("\"behavior\""))

    def test_the_hook_imports_only_the_standard_library_and_the_store_beside_it(self):
        import ast
        _, tree = self.parsed()
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(0, node.level)
                names.add((node.module or "").split(".")[0])
        self.assertTrue(names <= set(sys.stdlib_module_names) | {"shadow_store"}, sorted(names))

    def test_main_never_raises_and_returns_zero_when_the_decision_code_fails(self):
        self.install(self.approve())
        for name in ("decide", "read_level", "emit"):
            with self.subTest(function=name):
                with unittest.mock.patch.object(self.mod, name, side_effect=RuntimeError("boom")):
                    out, err = io.StringIO(), io.StringIO()
                    code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event(DECIDED)).encode("utf-8")), err,
                                         home=self.home, out=out)
                self.assertEqual((0, ""), (code, out.getvalue()))


if __name__ == "__main__":
    unittest.main()
