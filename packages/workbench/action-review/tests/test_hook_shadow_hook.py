"""The shadow hook (`docs/specs/action-review.md`, "The shadow hook").

Plan `2026-10-29-action-review-shadow-hook`, increment D. `hook/shadow_hook.py` is the program the owner registers as a
`PermissionRequest` hook for `Bash`. It runs the engine on each prompted command, records what the engine said, and answers
nothing, whatever happens. The engine's output is not invented here: the cases that the engine produces are produced by the
real helper (`main` with a fake launcher and bridge, as in `test_actionreview_output`), and a fake `wb` program replays those
bytes to the hook. Written before the code."""

import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock

from test_actionreview_output import (Base as EngineBase, COMMAND, HEAD, answered, bridge_failed, commit_doc, described, reply)
from tests import support_install
from workbench.wbkit import call

ROOT = support_install.ROOT
HOOK_DIR = os.path.join(ROOT, "packages", "workbench", "action-review", "hook")
HOOK = os.path.join(HOOK_DIR, "shadow_hook.py")
NO_RULE = "git push origin main"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Replay:
    """What the fake `wb` does: print these bytes, exit with this code, after this many seconds."""

    def __init__(self, code=0, out=b"", err=b"", sleep=0):
        self.code, self.out, self.err, self.sleep = code, out, err, sleep


WB_SOURCE = """#!%s
import json, os, sys, time
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "spec.json")) as handle:
    spec = json.load(handle)
with open(os.path.join(here, "args.json"), "w") as handle:
    json.dump({"argv": sys.argv[1:], "cwd": os.getcwd(), "env": dict(os.environ)}, handle)
if spec.get("child"):
    import subprocess
    subprocess.Popen([sys.executable, "-c", "import os, sys, time; open(sys.argv[1], 'w').write(str(os.getpid())); time.sleep(60)",
                      spec["child"]])
time.sleep(spec["sleep"])
sys.stdout.buffer.write(bytes.fromhex(spec["out"]))
sys.stderr.buffer.write(bytes.fromhex(spec["err"]))
sys.exit(spec["code"])
"""


# Started as `python3 -I -B stub.py <home> <hook> <arguments>`: the stub makes the account database name `<home>` as the account's
# home directory (the hook asks the database and not the environment, so no environment variable can point it at a scratch
# directory) and then runs the hook file as `__main__`. The interpreter's own start-up is the real one: its flags decide what
# it reads from the environment before any of this code runs.
STUB = """import pwd, runpy, sys
home, hook = sys.argv[1], sys.argv[2]
real = pwd.getpwuid


def named(uid):
    found = real(uid)
    return pwd.struct_passwd((found.pw_name, found.pw_passwd, found.pw_uid, found.pw_gid, found.pw_gecos, home, found.pw_shell))


pwd.getpwuid = named
sys.argv = [hook] + sys.argv[3:]
runpy.run_path(hook, run_name="__main__")
"""
ENV_PROGRAM = "/usr/bin/env"


class Base(EngineBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mod = load("action_review_shadow_hook_under_test", HOOK)
        cls.store = sys.modules["shadow_store"]

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.base = os.path.realpath(self.scratch.name)
        self.home = os.path.join(self.base, "home")
        self.cwd = os.path.join(self.base, "work")
        self.wbdir = os.path.join(self.base, "bin")
        for path in (self.home, self.cwd, self.wbdir):
            os.mkdir(path, 0o755)
        self.wb = os.path.join(self.wbdir, "wb")

    # -- the fake wb ---------------------------------------------------------------------------------------------------
    def install_wb(self, replay, child=""):
        with open(self.wb, "w") as handle:
            handle.write(WB_SOURCE % sys.executable)
        os.chmod(self.wb, 0o755)
        with open(os.path.join(self.wbdir, "spec.json"), "w") as handle:
            json.dump({"code": replay.code, "out": replay.out.hex(), "err": replay.err.hex(), "sleep": replay.sleep,
                       "child": child}, handle)

    def program(self, argv, raw=None, flags=("-I", "-B"), prefix=(), env=None):
        """Run the hook file as a program, as the settings entry does, with the account's home directory set to `self.home`."""
        stub = os.path.join(self.base, "stub.py")
        if not os.path.exists(stub):
            with open(stub, "w") as handle:
                handle.write(STUB)
        raw = json.dumps(self.event()).encode("utf-8") if raw is None else raw
        env = {"PATH": "/usr/bin:/bin"} if env is None else env
        return subprocess.run(list(prefix) + [sys.executable, *flags, stub, self.home, HOOK, *argv], input=raw, env=env,
                              capture_output=True, timeout=60)

    def wb_args(self):
        path = os.path.join(self.wbdir, "args.json")
        if not os.path.exists(path):
            return None
        with open(path) as handle:
            return json.load(handle)

    # -- the real engine's own bytes -----------------------------------------------------------------------------------
    def engine(self, text=COMMAND, **kwargs):
        code, out, err, _ = self.run_main(["review", "--log-row", "--collect", text], **kwargs)
        return Replay(code, out.encode("ascii"), err.encode("ascii"))

    # -- the hook ------------------------------------------------------------------------------------------------------
    def event(self, text=COMMAND, **changes):
        document = {"session_id": "s", "transcript_path": "/t.jsonl", "cwd": self.cwd, "permission_mode": "default",
                    "hook_event_name": "PermissionRequest", "tool_name": "Bash",
                    "tool_input": {"command": text, "description": "d"}}
        document.update(changes)
        return document

    def run_hook(self, replay=None, event=None, raw=None, argv=None, text=COMMAND):
        if replay is not None:
            self.install_wb(replay)
        if raw is None:
            raw = json.dumps(self.event(text) if event is None else event).encode("utf-8")
        err = io.StringIO()
        code = self.mod.main(["--wb", self.wb] if argv is None else argv, io.BytesIO(raw), err, home=self.home)
        return code, err.getvalue()

    def rows(self, name):
        return self.store.read(name, self.home)

    def one_verdict(self):
        rows, skipped = self.rows("verdicts.jsonl")
        self.assertEqual((1, 0), (len(rows), skipped), rows)
        return rows[0]

    def sha(self, text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Answer(Base):
    """The hook decides nothing and says nothing, for every input."""

    def cases(self):
        yield "approve", self.engine()
        yield "model decline", self.engine(bridge=answered(reply("decline", ["scope_is_coherent"], "Mixed.")))
        yield "code decline", self.engine(describe=described(commit_doc(head="b" * 40)))
        yield "no rule", self.engine(NO_RULE)
        yield "outside the grammar", self.engine(COMMAND + " && ls")
        yield "describe fails", self.engine(describe=call.Result(1, b"", b"", False, False))
        yield "bridge fails", self.engine(bridge=bridge_failed())
        yield "engine exit 1, no lines", Replay(1)
        yield "engine exit 2, no lines", Replay(2)
        yield "engine exit 0, garbage", Replay(0, b"allow\n", b"outcome: nonsense\n")
        yield "engine exit 7", Replay(7, b"{}", b"x")
        yield "engine prints allow-shaped JSON", Replay(0, json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}).encode() + b"\n")

    def test_the_script_prints_nothing_and_exits_0_for_every_engine_outcome(self):
        for name, replay in self.cases():
            self.install_wb(replay)
            run = self.program(["--wb", self.wb])
            self.assertEqual((0, b""), (run.returncode, run.stdout), (name, run.stderr))

    def test_the_script_prints_nothing_for_bad_input_too(self):
        bad = [b"", b"not json", b"[]", b"null", b'{"hook_event_name": "PermissionRequest"}', b"\xff\xfe",
               json.dumps(self.event(tool_name="Edit")).encode(), json.dumps(self.event(cwd="relative")).encode(),
               json.dumps(self.event(hook_event_name="PreToolUse")).encode(), b"{" * 5000, b"x" * 2000000]
        self.install_wb(self.engine())
        for raw in bad:
            run = self.program(["--wb", self.wb], raw)
            self.assertEqual((0, b""), (run.returncode, run.stdout), raw[:30])

    def test_the_script_prints_nothing_when_the_arguments_are_wrong_or_the_wb_is_missing(self):
        for argv in ([], ["--wb"], ["--wb", "relative/wb"], ["--wb", "/no/such/wb"], ["--other"], ["--wb", self.wb, "x"]):
            run = self.program(argv)
            self.assertEqual((0, b""), (run.returncode, run.stdout), argv)

    def test_main_returns_0_and_does_not_raise_for_an_interrupt_or_an_exit_inside_it(self):
        self.install_wb(self.engine())
        for exc in (KeyboardInterrupt(), SystemExit(3), RuntimeError("boom"), MemoryError()):
            with unittest.mock.patch.object(self.mod, "run_engine", side_effect=exc):
                code, err = self.run_hook()
            self.assertEqual(0, code, repr(exc))
            self.assertNotIn(COMMAND, err)

    def test_no_code_path_writes_to_standard_output(self):
        import ast
        with open(HOOK, "rb") as handle:
            text = handle.read().decode()
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotEqual("print", node.func.id)
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, ("stdout", "__stdout__", "fdopen", "dup2"))
                if isinstance(node.value, ast.Name) and node.value.id == "os":
                    self.assertNotIn(node.attr, ("write", "writev", "sendfile", "system", "popen", "exec", "execv", "execve"))
        for word in ("hookSpecificOutput", "decision", "behavior", "\"allow\"", "'allow'", "\"deny\"", "updatedInput"):
            self.assertNotIn(word, text, word)

    def test_the_hook_imports_only_the_standard_library_and_the_store_beside_it(self):
        import ast
        with open(HOOK, "rb") as handle:
            tree = ast.parse(handle.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(0, node.level)
                names.add((node.module or "").split(".")[0])
        allowed = set(sys.stdlib_module_names) | {"shadow_store"}
        self.assertTrue(names <= allowed, sorted(names - allowed))


class Recording(Base):
    def test_a_reviewed_approve_leaves_one_verdict_row_and_one_collected_row(self):
        replay = self.engine()
        code, err = self.run_hook(replay)
        self.assertEqual(0, code)
        row = self.one_verdict()
        self.assertEqual(("reviewed", "approve", [], True, None), (
            row["outcome"], row["verdict"], row["failed_checks"], row["reviewed"], row["no_review_reason"]))
        self.assertEqual(self.sha(COMMAND), row["command_sha256"])
        self.assertEqual("safe-git-commit", row["rule"])
        for field in ("facts_sha256", "rubric_sha256", "bridge", "model", "effort", "format"):
            self.assertIn(field, row)
        collected, skipped = self.rows("collected.jsonl")
        self.assertEqual((1, 0), (len(collected), skipped))
        item = collected[0]
        self.assertEqual((COMMAND, "safe-git-commit", self.sha(COMMAND), "approve"), (
            item["command"], item["rule"], item["command_sha256"], item["verdict"]))
        self.assertEqual(commit_doc(), item["facts"])
        self.assertRegex(item["id"], r"^[0-9a-f]{32}$")

    def test_a_decline_is_recorded_with_its_failed_checks(self):
        self.run_hook(self.engine(bridge=answered(reply("decline", ["scope_is_coherent"], "Mixed."))))
        row = self.one_verdict()
        self.assertEqual(("reviewed", "decline", ["scope_is_coherent"], "Mixed."),
                         (row["outcome"], row["verdict"], row["failed_checks"], row["reason"]))
        self.assertEqual(1, len(self.rows("collected.jsonl")[0]))

    def test_a_decline_by_a_code_check_is_recorded_and_collected(self):
        self.run_hook(self.engine(describe=described(commit_doc(head="b" * 40))))
        row = self.one_verdict()
        self.assertEqual(("reviewed", "decline", ["head_matches"]), (row["outcome"], row["verdict"], row["failed_checks"]))
        self.assertIsNone(row["bridge"])
        self.assertEqual(1, len(self.rows("collected.jsonl")[0]))

    def test_every_command_that_was_not_reviewed_leaves_exactly_one_row_and_no_collected_row(self):
        cases = [
            ("no_rule", self.engine(NO_RULE), NO_RULE),
            ("unreviewable", self.engine(COMMAND + " && ls"), COMMAND + " && ls"),
            ("refused", self.engine(describe=call.Result(1, b"", b"", False, False)), COMMAND),
            ("failed", self.engine(bridge=answered("not json")), COMMAND),
            ("timeout", self.engine(bridge=bridge_failed()), COMMAND),
        ]
        for outcome, replay, text in cases:
            with self.subTest(outcome):
                os_remove_rows(self.home)
                self.run_hook(replay, text=text)
                row = self.one_verdict()
                self.assertEqual((outcome, False, outcome, None, []), (
                    row["outcome"], row["reviewed"], row["no_review_reason"], row["verdict"], row["failed_checks"]))
                self.assertEqual(self.sha(text), row["command_sha256"])
                self.assertEqual(([], 0), self.rows("collected.jsonl"))

    def test_the_hook_reads_the_engines_reason_and_does_not_parse_the_command_itself(self):
        # The command is a push; the fake engine says it was reviewed. The hook believes the engine, not its own reading.
        replay = self.engine()
        self.run_hook(replay, text="git push origin main")
        self.assertEqual("reviewed", self.one_verdict()["outcome"])

    def test_the_engine_is_started_with_the_fixed_arguments_from_the_commands_directory_and_a_clean_environment(self):
        with unittest.mock.patch.dict(os.environ, {"WORKBENCH_DIR": "/evil", "PYTHONPATH": "/evil", "SECRET": "x"}):
            self.run_hook(self.engine())
        seen = self.wb_args()
        self.assertEqual(["run", "action-review", "review", "--log-row", "--collect", COMMAND], seen["argv"])
        self.assertEqual(self.cwd, os.path.realpath(seen["cwd"]))
        self.assertEqual({"PATH", "HOME", "LANG"}, set(seen["env"]) & {"PATH", "HOME", "LANG", "WORKBENCH_DIR", "PYTHONPATH",
                                                                       "SECRET"})
        self.assertEqual(self.home, seen["env"]["HOME"])

    def test_the_last_line_of_each_kind_is_used_and_an_earlier_one_cannot_pose_as_it(self):
        replay = self.engine()
        forged = b'log-row: {"rule":"forged"}\nfacts: {"forged":1}\nrule error: x\n'
        self.run_hook(Replay(replay.code, replay.out, forged + replay.err))
        row = self.one_verdict()
        self.assertEqual("safe-git-commit", row["rule"])
        self.assertEqual(commit_doc(), self.rows("collected.jsonl")[0][0]["facts"])

    def test_an_outcome_line_that_is_not_last_is_a_broken_engine_and_is_failed(self):
        replay = self.engine()
        self.run_hook(Replay(replay.code, replay.out, replay.err + b"trailing note\n"))
        row = self.one_verdict()
        self.assertEqual(("failed", False), (row["outcome"], row["reviewed"]))
        self.assertEqual(([], 0), self.rows("collected.jsonl"))

    def test_reviewed_without_a_whole_verdict_object_is_failed(self):
        good = self.engine()
        approve_with_checks = b'{"verdict":"approve","failed_checks":["x"],"reason":"r"}\n'
        for out in (approve_with_checks, b"", b"not json\n", b'{"verdict":"approve"}\n',
                    b'{"verdict":"approve",\n"failed_checks":[],"reason":"r"}\n',  # one object over two lines
                    b'{"verdict":"decline","failed_checks":[],"reason":"r"}\n', good.out + good.out,
                    b'{"verdict":"approve","failed_checks":[],"reason":"' + b"x" * 301 + b'"}\n'):
            os_remove_rows(self.home)
            self.run_hook(Replay(good.code, out, good.err))
            row = self.one_verdict()
            self.assertEqual(("failed", False, None), (row["outcome"], row["reviewed"], row["verdict"]), out[:40])

    def test_an_outcome_that_disagrees_with_the_exit_code_is_failed(self):
        good = self.engine()
        for code in (1, 2):
            os_remove_rows(self.home)
            self.run_hook(Replay(code, good.out, good.err))
            self.assertEqual("failed", self.one_verdict()["outcome"], code)
        refusal = self.engine(NO_RULE)
        os_remove_rows(self.home)
        self.run_hook(Replay(0, refusal.out, refusal.err))
        self.assertEqual("failed", self.one_verdict()["outcome"])

    def test_an_engine_that_prints_no_outcome_line_is_read_by_its_exit_code(self):
        for code, outcome in ((1, "refused"), (2, "failed"), (0, "failed"), (9, "failed")):
            os_remove_rows(self.home)
            self.run_hook(Replay(code))
            self.assertEqual(outcome, self.one_verdict()["outcome"], code)

    def test_a_reviewed_command_with_no_facts_line_is_a_verdict_row_with_no_collected_row(self):
        replay = self.engine()
        without = b"".join(line for line in replay.err.splitlines(keepends=True) if not line.startswith(b"facts: "))
        self.run_hook(Replay(replay.code, replay.out, without))
        row = self.one_verdict()
        self.assertEqual(("reviewed", True), (row["outcome"], row["reviewed"]))
        self.assertEqual(([], 0), self.rows("collected.jsonl"))

    def test_a_reviewed_command_with_no_log_row_is_recorded_and_not_collected(self):
        replay = self.engine()
        without = b"".join(line for line in replay.err.splitlines(keepends=True) if not line.startswith(b"log-row: "))
        code, err = self.run_hook(Replay(replay.code, replay.out, without))
        row = self.one_verdict()
        self.assertEqual(("reviewed", True), (row["outcome"], row["reviewed"]))
        self.assertNotIn("rule", row)
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertEqual("", err, "no collected row was tried, so no store error is noted")

    def test_a_log_row_that_does_not_fit_costs_the_engines_fields_and_not_the_verdict_row(self):
        replay = self.engine()
        bad_row = b'log-row: {"rule": "safe-git-commit", "model": ' + b'"' + b"m" * 500 + b'"}\n'
        lines = [line for line in replay.err.splitlines(keepends=True) if not line.startswith(b"log-row: ")]
        self.run_hook(Replay(replay.code, replay.out, bad_row + b"".join(lines)))
        row = self.one_verdict()
        self.assertEqual(("reviewed", "approve"), (row["outcome"], row["verdict"]))
        self.assertNotIn("model", row)

    def test_rows_hold_no_command_text_in_the_verdict_file(self):
        self.run_hook(self.engine())
        with open(os.path.join(self.store.data_dir(self.home), "verdicts.jsonl"), "rb") as handle:
            data = handle.read().decode()
        self.assertNotIn("safe-git", data.replace('"rule":"safe-git-commit"', ""))
        self.assertNotIn("a.txt", data)
        self.assertNotIn(COMMAND, data)


LEAKY_COMMAND = COMMAND + " # token=abcdef123456"  # the fake engine does not read it: the hook passes the text on and stores it
LEAKY_DIFF = "--- HEAD/.env\n+++ work/.env\n@@ -0,0 +1 @@\n+DB_PASSWORD=hunter22abc\n"
LEAKY_REASON = "The change adds secret=s3cr3tvalue1 to a file."
SECRETS = ("abcdef123456", "hunter22abc", "s3cr3tvalue1")


class Redacting(Base):
    """What the hook stores is redacted (plan `2026-11-03-redact-collected-diffs`, increment B). The engine's own bytes are used:
    in `leaky` a model is asked and its reason holds a secret; in `leaky_diff` the diff holds one, and the diff stays in the facts
    that the hook collects."""

    def leaky(self, reason=LEAKY_REASON):
        return self.engine(bridge=answered(reply("approve", [], reason)))

    def leaky_diff(self):
        return self.engine(describe=described(commit_doc(diff=LEAKY_DIFF)))

    def stored(self, name):
        with open(os.path.join(self.store.data_dir(self.home), name), "rb") as handle:
            return handle.read().decode("utf-8")

    def test_the_engine_runs_the_tests_use_really_carry_the_secrets(self):
        replay = self.leaky()
        self.assertIn("s3cr3tvalue1", (replay.out + replay.err).decode("ascii"))
        self.assertIn("hunter22abc", self.leaky_diff().err.decode("ascii"))

    def run_counting(self, replay, text):
        """Run the hook and name the files it tried to append a row to."""
        real, tried = self.mod.store.append, []

        def counting(name, row, home=None):
            tried.append(name)
            return real(name, row, home)

        with unittest.mock.patch.object(self.mod.store, "append", counting):
            code, err = self.run_hook(replay, text=text)
        return code, err, tried

    def stored_text(self):
        return self.stored("verdicts.jsonl") + self.stored("collected.jsonl")

    def test_no_secret_reaches_either_file_and_a_marker_stands_in_its_place(self):
        self.run_hook(self.leaky(), text=LEAKY_COMMAND)
        data = self.stored_text()
        for secret in SECRETS:
            self.assertNotIn(secret, data, secret)
        verdict = self.one_verdict()
        self.assertEqual("The change adds secret=[redacted:assignment] to a file.", verdict["reason"])
        collected, skipped = self.rows("collected.jsonl")
        self.assertEqual((1, 0), (len(collected), skipped))
        item = collected[0]
        self.assertEqual("The change adds secret=[redacted:assignment] to a file.", item["reason"])
        self.assertEqual(COMMAND + " # token=[redacted:assignment]", item["command"])
        self.assertEqual(commit_doc(), item["facts"])

    def test_a_diff_that_carries_a_secret_is_collected_with_the_secret_redacted(self):
        self.run_hook(self.leaky_diff(), text=LEAKY_COMMAND)
        self.assertEqual("reviewed", self.one_verdict()["outcome"])
        data = self.stored_text()
        for secret in SECRETS:
            self.assertNotIn(secret, data, secret)
        item = self.rows("collected.jsonl")[0][0]
        self.assertIn("+DB_PASSWORD=[redacted:assignment]\n", item["facts"]["facts"]["diff"])
        expected = commit_doc(diff=LEAKY_DIFF.replace("hunter22abc", "[redacted:assignment]"))
        self.assertEqual(expected, item["facts"])

    def test_the_hash_is_still_of_the_raw_command_and_the_rows_keep_their_fields(self):
        self.run_hook(self.leaky(), text=LEAKY_COMMAND)
        self.assertEqual(self.sha(LEAKY_COMMAND), self.one_verdict()["command_sha256"])
        item = self.rows("collected.jsonl")[0][0]
        self.assertEqual(self.sha(LEAKY_COMMAND), item["command_sha256"])
        self.assertEqual({"id", "ts", "rule", "command_sha256", "command", "facts", "verdict", "failed_checks", "reason"}, set(item))
        self.assertEqual(("approve", []), (item["verdict"], item["failed_checks"]))

    def test_a_decline_keeps_its_failed_checks_and_redacts_its_reason(self):
        replay = self.engine(bridge=answered(reply("decline", ["scope_is_coherent"], LEAKY_REASON)))
        self.run_hook(replay, text=LEAKY_COMMAND)
        row = self.one_verdict()
        self.assertEqual(("decline", ["scope_is_coherent"], "The change adds secret=[redacted:assignment] to a file."),
                         (row["verdict"], row["failed_checks"], row["reason"]))

    def test_the_script_writes_no_secret_to_standard_output_or_error(self):
        for replay in (self.leaky(), self.leaky_diff()):
            os_remove_rows(self.home)
            self.install_wb(replay)
            run = self.program(["--wb", self.wb], json.dumps(self.event(LEAKY_COMMAND)).encode())
            self.assertEqual((0, b""), (run.returncode, run.stdout))
            for secret in SECRETS:
                self.assertNotIn(secret.encode(), run.stderr)
                self.assertNotIn(secret, self.stored_text())
            self.assertEqual(1, len(self.rows("collected.jsonl")[0]))

    def test_a_redaction_that_raises_leaves_the_verdict_row_without_its_reason_and_no_collected_row(self):
        replay = self.leaky()
        for name, error in (("redact_text", RuntimeError("boom")), ("redact", ValueError("too deep"))):
            with self.subTest(name):
                os_remove_rows(self.home)
                with unittest.mock.patch.object(self.mod, name, side_effect=error):
                    code, err, tried = self.run_counting(replay, LEAKY_COMMAND)
                self.assertEqual((0, ["verdicts.jsonl"]), (code, tried), "no collected row is even tried")
                row = self.one_verdict()
                self.assertEqual(("reviewed", "approve", None), (row["outcome"], row["verdict"], row["reason"]))
                self.assertEqual(([], 0), self.rows("collected.jsonl"))
                self.assertTrue(err.strip(), "the failure is noted")
                for secret in SECRETS + ("boom", "too deep"):
                    self.assertNotIn(secret, err)
                    self.assertNotIn(secret, self.stored("verdicts.jsonl"))

    def test_a_redacted_reason_that_no_longer_fits_is_dropped_with_the_collected_row(self):
        reason = ("password=abcd " * 22)[:300]
        self.assertEqual(300, len(reason))
        code, err, tried = self.run_counting(self.leaky(reason), LEAKY_COMMAND)
        self.assertEqual((0, ["verdicts.jsonl"]), (code, tried))
        row = self.one_verdict()
        self.assertEqual(("reviewed", None), (row["outcome"], row["reason"]))
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertTrue(err.strip())

    def test_a_reason_of_exactly_the_limit_that_needs_no_redaction_is_stored_whole(self):
        reason = "a" * 300
        self.run_hook(self.leaky(reason), text=LEAKY_COMMAND)
        self.assertEqual(reason, self.one_verdict()["reason"])
        self.assertEqual(reason, self.rows("collected.jsonl")[0][0]["reason"])

    def test_a_redacted_command_that_no_longer_fits_costs_the_collected_row_and_the_reason_and_not_the_verdict_row(self):
        text = LEAKY_COMMAND + " # " + "password=abcd " * 250
        self.assertLessEqual(len(text), 4096)
        code, err, tried = self.run_counting(self.leaky(), text)
        self.assertEqual((0, ["verdicts.jsonl"]), (code, tried))
        row = self.one_verdict()
        self.assertEqual(("reviewed", self.sha(text), None), (row["outcome"], row["command_sha256"], row["reason"]))
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertTrue(err.strip())

    def test_facts_whose_redacted_form_no_longer_fits_a_line_cost_the_collected_row_and_keep_the_redacted_reason(self):
        diff = "password=abcd\n" * 28000  # 392,000 characters, a line that fits; redacted it is over the store's 512 KB
        facts = commit_doc(diff=diff)
        row = {"rule": "safe-git-commit"}
        self.store.append("collected.jsonl", {"id": "0123456789abcdef0123456789abcdef", "ts": "2026-10-30T01:02:03Z",
                          "rule": "safe-git-commit", "command_sha256": "a" * 64, "command": "x", "facts": facts,
                          "verdict": "approve", "failed_checks": [], "reason": "ok"}, self.home)
        os_remove_rows(self.home)
        err = io.StringIO()
        self.mod.record(err, self.home, "reviewed", COMMAND, ("approve", [], "Adds password=abcd to it."), row, facts)
        verdict = self.one_verdict()
        self.assertEqual("Adds password=[redacted:assignment] to it.", verdict["reason"])
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertTrue(err.getvalue().strip())
        self.assertNotIn("abcd", err.getvalue() + self.stored("verdicts.jsonl"))

    def test_a_row_that_was_not_reviewed_still_holds_no_reason_and_costs_no_note(self):
        code, err = self.run_hook(self.engine(NO_RULE), text=NO_RULE)
        row = self.one_verdict()
        self.assertEqual((0, "", "no_rule", None), (code, err, row["outcome"], row["reason"]))

    def test_a_malformed_event_costs_no_note(self):
        code, err = self.run_hook(Replay(0), raw=b"not json")
        self.assertEqual((0, ""), (code, err))
        self.assertEqual("malformed_input", self.one_verdict()["outcome"])

    def test_facts_that_come_with_an_outcome_that_was_not_reviewed_are_not_collected(self):
        err = io.StringIO()
        self.mod.record(err, self.home, "failed", LEAKY_COMMAND, None, {"rule": "safe-git-commit"}, commit_doc())
        self.assertEqual("failed", self.one_verdict()["outcome"])
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertEqual("", err.getvalue())


# Shapes of secret that the security review of 2026-11-04 found the hook's redactor does not name. The engine's own scan
# (`no_secret_lines`) names most of them: where it does, the commit is declined and the hook collects nothing of it.
SHAPES = {
    "gitlab": "glpat-a1b2c3d4e5f6g7h8i9j0",
    "npm": "npm_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
    "stripe": "sk_live_4eC39HqLyjWDarjtT1zdp7dc",
    "pwd": "pwd=Tr0ub4dor3xyzq",
    "basic": "Basic dXNlcjpwYXNzd29yZDEyMw==",
    "aws": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY",
    "pass": "pass=Tr0ub4dor3xyzq",
    "slack": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
}


def diff_adding(text, path="a.txt"):
    return "--- a/%s\n+++ b/%s\n@@ -0,0 +1 @@\n+%s\n" % (path, path, text)


class DeclinedSecrets(Base):
    """A commit the engine declines because it holds a secret, or touches a credential-named path, leaves no collected row, whatever
    shape the secret has (the redactor is a list of patterns; the engine's own scan is the better judge of a diff)."""

    def stored_text(self):
        data = ""
        for name in ("verdicts.jsonl", "collected.jsonl"):
            path = os.path.join(self.store.data_dir(self.home), name)
            if os.path.exists(path):
                with open(path, "rb") as handle:
                    data += handle.read().decode("utf-8")
        return data

    def test_every_shape_the_engine_declines_leaves_no_collected_row_and_no_text(self):
        declined = []
        for name, shape in SHAPES.items():
            with self.subTest(name):
                os_remove_rows(self.home)
                self.run_hook(self.engine(describe=described(commit_doc(diff=diff_adding("x = " + shape)))))
                row = self.one_verdict()
                if "no_secret_lines" not in row["failed_checks"]:
                    continue  # the engine does not name this shape; the hook cannot tell it from any other diff
                declined.append(name)
                self.assertEqual(([], 0), self.rows("collected.jsonl"))
                self.assertNotIn(shape, self.stored_text())
        # What the engine's scan names today. A shape that is not here is approved by the engine and collected as the redactor leaves
        # it: that gap is the scan's and the redactor's, and this test says so (the spec's "Redaction"). If the scan learns another
        # shape this assertion fails, and the list is updated with the spec.
        self.assertEqual(["basic", "gitlab", "npm", "pwd", "stripe"], sorted(declined))

    def test_a_decline_for_a_credential_named_path_leaves_no_collected_row(self):
        facts = commit_doc(paths=[".env"], requested_paths=[".env"], diff=diff_adding("PLAIN=value", ".env"))
        self.run_hook(self.engine(describe=described(facts)))
        row = self.one_verdict()
        self.assertEqual(("reviewed", "decline"), (row["outcome"], row["verdict"]))
        self.assertIn("paths_not_credentials", row["failed_checks"])
        self.assertNotIn("no_secret_lines", row["failed_checks"])
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertNotIn("PLAIN=value", self.stored_text())

    def test_a_decline_for_another_reason_is_still_collected(self):
        self.run_hook(self.engine(bridge=answered(reply("decline", ["scope_is_coherent"], "Mixed."))))
        self.assertEqual(1, len(self.rows("collected.jsonl")[0]))
        os_remove_rows(self.home)
        self.run_hook(self.engine(describe=described(commit_doc(head="b" * 40))))
        self.assertEqual(["head_matches"], self.one_verdict()["failed_checks"])
        self.assertEqual(1, len(self.rows("collected.jsonl")[0]))

    def test_a_decline_for_a_secret_among_other_failed_checks_is_not_collected(self):
        # Several checks fail at once: the secret one is enough to drop the collected row.
        self.run_hook(self.engine(describe=described(commit_doc(head="b" * 40, diff=diff_adding("x = " + SHAPES["gitlab"])))))
        row = self.one_verdict()
        self.assertIn("no_secret_lines", row["failed_checks"])
        self.assertEqual(([], 0), self.rows("collected.jsonl"))

    def test_the_verdict_row_keeps_its_failed_checks_and_a_redacted_reason(self):
        self.run_hook(self.engine(describe=described(commit_doc(diff=diff_adding("x = " + SHAPES["gitlab"])))))
        row = self.one_verdict()
        self.assertEqual("decline", row["verdict"])
        self.assertTrue(row["reviewed"])
        self.assertNotIn(SHAPES["gitlab"], self.stored_text())


class Isolation(Base):
    """The hook takes nothing from its inherited environment (plan `2026-11-04-shadow-hook-security-review-fixes`, increment B; the
    second security review, Medium 2). A Python script cannot defend itself against what the interpreter runs before it, so the
    entry that starts it is `/usr/bin/env -i <absolute interpreter> -I -B <hook> --wb <launcher>`; what the script itself does is to
    take its home from the account database, to need `--wb`, and to stop at once when it was not started isolated."""

    def setUp(self):
        super().setUp()
        self.hostile = os.path.join(self.base, "hostile")
        self.json_only = os.path.join(self.base, "json-only")
        self.other_home = os.path.join(self.base, "other-home")
        for path in (self.hostile, self.json_only, self.other_home):
            os.mkdir(path)
        self.user_base = os.path.join(self.base, "user-base")
        probe = subprocess.run([sys.executable, "-c", "import site; print(site.getusersitepackages())"],
                               env={"PYTHONUSERBASE": self.user_base, "PATH": "/usr/bin:/bin"}, capture_output=True, timeout=60)
        self.user_site = probe.stdout.decode().strip()
        os.makedirs(self.user_site)
        self.markers = {}
        for directory, name in ((self.hostile, "json"), (self.hostile, "sitecustomize"), (self.json_only, "json"),
                                (self.user_site, "usercustomize")):
            marker = os.path.join(self.base, "%s-%s.ran" % (os.path.basename(directory) or "user", name))
            self.markers[(directory, name)] = marker
            with open(os.path.join(directory, name + ".py"), "w") as handle:
                handle.write("open(%r, 'w').close()\n" % marker)
        self.install_wb(self.engine())

    def hostile_environment(self, **extra):
        env = {"PATH": "/usr/bin:/bin", "HOME": self.other_home, "PYTHONPATH": self.hostile, "PYTHONUSERBASE": self.user_base}
        env.update(extra)
        return env

    def ran(self):
        found = [os.path.basename(path) for path in self.markers.values() if os.path.exists(path)]
        return sorted(found)

    def test_the_control_without_any_protection_the_hostile_environment_does_run_code(self):
        # Without this the tests below could pass because the hostile layout does nothing at all. A plain interpreter with the same
        # environment imports the hostile `json.py`, `sitecustomize.py` and `usercustomize.py`. (`PYTHONSTARTUP` is read only by an
        # interactive session, so neither this test nor the hook's run can show it; it is not claimed.)
        run = subprocess.run([sys.executable, "-B", "-c", "import json"], env=self.hostile_environment(), capture_output=True,
                             timeout=60)
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertEqual(["hostile-json.ran", "hostile-sitecustomize.ran", "site-packages-usercustomize.ran"], self.ran())

    def test_started_as_the_documented_entry_nothing_hostile_runs_and_the_row_is_recorded(self):
        run = self.program(["--wb", self.wb], prefix=[ENV_PROGRAM, "-i"], env=self.hostile_environment())
        self.assertEqual((0, b""), (run.returncode, run.stdout), run.stderr)
        self.assertEqual([], self.ran())
        self.assertEqual("reviewed", self.one_verdict()["outcome"])

    def test_isolated_mode_alone_ignores_the_path_the_startup_file_and_the_user_site(self):
        run = self.program(["--wb", self.wb], env=self.hostile_environment())
        self.assertEqual((0, b""), (run.returncode, run.stdout), run.stderr)
        self.assertEqual([], self.ran())
        self.assertEqual("reviewed", self.one_verdict()["outcome"])

    def test_a_different_home_variable_moves_neither_the_data_directory_nor_the_launcher(self):
        run = self.program(["--wb", self.wb], env=self.hostile_environment())
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertEqual("reviewed", self.one_verdict()["outcome"])
        self.assertFalse(os.path.exists(os.path.join(self.other_home, ".config")), "the data went below the HOME variable")
        seen = self.wb_args()
        self.assertEqual(self.home, seen["env"]["HOME"])  # the engine is given the account's home, not the variable

    def test_started_without_isolation_the_hook_stops_at_once_and_records_nothing(self):
        # Only `json.py` is on this path: the guard sits above every other import of the file, so the hook's own imports are not
        # taken from it. This does not claim that code the interpreter ran at start-up (`sitecustomize`) did not run.
        env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": self.json_only}
        run = self.program(["--wb", self.wb], flags=("-B",), env=env)
        self.assertEqual((0, b""), (run.returncode, run.stdout))
        self.assertIn(b"python3 -I", run.stderr)
        self.assertNotIn(b"hunter", run.stderr)
        self.assertFalse(os.path.exists(self.markers[(self.json_only, "json")]), "a hostile json.py was imported")
        self.assertEqual(([], 0), self.rows("verdicts.jsonl"))
        self.assertIsNone(self.wb_args(), "the engine was started by a hook that was not isolated")

    def test_the_data_directory_and_the_home_the_engine_gets_come_from_the_account_database(self):
        import pwd
        found = pwd.getpwuid(os.getuid())
        named = pwd.struct_passwd((found.pw_name, found.pw_passwd, found.pw_uid, found.pw_gid, found.pw_gecos, self.home,
                                   found.pw_shell))
        with unittest.mock.patch.dict(os.environ, {"HOME": self.other_home}), \
                unittest.mock.patch.object(pwd, "getpwuid", return_value=named):
            self.assertEqual(self.home, self.mod.account_home())
            code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event()).encode()), io.StringIO())
        self.assertEqual(0, code)
        self.assertEqual("reviewed", self.one_verdict()["outcome"])
        self.assertFalse(os.path.exists(os.path.join(self.other_home, ".config")))

    def test_an_account_database_that_cannot_answer_records_nothing_and_notes_it(self):
        import pwd
        with unittest.mock.patch.object(pwd, "getpwuid", side_effect=KeyError("uid")):
            self.assertIsNone(self.mod.account_home())
            err = io.StringIO()
            code = self.mod.main(["--wb", self.wb], io.BytesIO(json.dumps(self.event()).encode()), err)
        self.assertEqual(0, code)
        self.assertIn("home directory", err.getvalue())
        self.assertIsNone(self.wb_args())
        self.assertEqual(([], 0), self.rows("verdicts.jsonl"))


class Inputs(Base):
    def test_malformed_input_leaves_a_row_with_no_command_hash_and_runs_no_engine(self):
        self.install_wb(self.engine())
        raws = [b"", b"not json", b"[]", b"\xff\xfe", b"x" * 2000000,
                json.dumps(self.event(hook_event_name="PreToolUse")).encode(),
                json.dumps(self.event(cwd="relative")).encode(), json.dumps(self.event(cwd="/no/such/dir")).encode(),
                json.dumps(self.event(tool_input={})).encode(), json.dumps(self.event(tool_input={"command": 7})).encode(),
                json.dumps(self.event(tool_input={"command": ""})).encode(), json.dumps(self.event(tool_input=[])).encode()]
        for raw in raws:
            os_remove_rows(self.home)
            code, _ = self.run_hook(raw=raw)
            self.assertEqual(0, code)
            row = self.one_verdict()
            self.assertEqual(("malformed_input", False, "malformed_input", None), (
                row["outcome"], row["reviewed"], row["no_review_reason"], row["command_sha256"]), raw[:40])
        self.assertIsNone(self.wb_args())

    def test_a_tool_other_than_bash_is_not_bash_and_runs_no_engine(self):
        self.install_wb(self.engine())
        self.run_hook(event=self.event(tool_name="Edit", tool_input={"file_path": "/x"}))
        row = self.one_verdict()
        self.assertEqual(("not_bash", False, None), (row["outcome"], row["reviewed"], row["command_sha256"]))
        self.assertIsNone(self.wb_args())

    def test_a_command_longer_than_the_engine_takes_is_unreviewable_and_runs_no_engine(self):
        self.install_wb(self.engine())
        text = "echo " + "a" * 5000
        self.run_hook(text=text)
        row = self.one_verdict()
        self.assertEqual(("unreviewable", self.sha(text)), (row["outcome"], row["command_sha256"]))
        self.assertIsNone(self.wb_args())

    def test_a_command_with_a_lone_surrogate_does_not_stop_the_hook(self):
        self.install_wb(self.engine())
        raw = b'{"hook_event_name":"PermissionRequest","tool_name":"Bash","cwd":"%s","tool_input":{"command":"x\\ud800"}}' % \
            self.cwd.encode()
        code, _ = self.run_hook(raw=raw)
        self.assertEqual(0, code)
        row = self.one_verdict()
        self.assertEqual(("failed", False), (row["outcome"], row["reviewed"]))
        self.assertIsNone(self.wb_args(), "the engine was started for a command it cannot be given")

    def test_a_command_with_a_nul_is_failed_and_the_engine_is_not_started(self):
        self.install_wb(self.engine())
        self.run_hook(text="echo a\0b")
        self.assertEqual("failed", self.one_verdict()["outcome"])
        self.assertIsNone(self.wb_args())

    def test_a_command_reaches_the_engine_as_one_last_argument_whatever_it_holds(self):
        texts = ["-x", "--collect", "--log-row", "echo 'a\nb'", "x; rm -rf /", "$(id)", "`id`", "a | b > c", "a  b   c", " lead",
                 "tab\there", "*", "~/x", "a\\b", "é ‮"]
        for text in texts:
            os_remove_rows(self.home)
            self.run_hook(self.engine(), text=text)
            seen = self.wb_args()
            self.assertEqual(["run", "action-review", "review", "--log-row", "--collect", text], seen["argv"], text)

    def test_a_describe_that_times_out_is_a_timeout_as_the_engine_says(self):
        replay = self.engine(describe=call.Result(0, b"", b"", False, True))
        self.assertEqual(1, replay.code)  # the engine refuses (exit 1) and names the reason
        self.run_hook(replay)
        self.assertEqual("timeout", self.one_verdict()["outcome"])


class Program(Base):
    def test_a_wb_that_is_not_an_absolute_existing_executable_file_is_not_run(self):
        self.install_wb(self.engine())
        for wb in ("relative/wb", "/no/such/wb", self.wbdir):
            os_remove_rows(self.home)
            code, err = self.run_hook(argv=["--wb", wb])
            self.assertEqual(0, code, wb)
            self.assertEqual("failed", self.one_verdict()["outcome"], wb)
        self.assertIsNone(self.wb_args())

    def test_a_relative_path_to_a_wb_that_exists_from_here_is_still_not_run(self):
        self.install_wb(self.engine())
        relative = os.path.relpath(self.wb, os.getcwd())
        self.assertFalse(os.path.isabs(relative))
        self.assertTrue(os.path.isfile(relative))
        code, _ = self.run_hook(argv=["--wb", relative])
        self.assertEqual(0, code)
        self.assertEqual("failed", self.one_verdict()["outcome"])
        self.assertIsNone(self.wb_args())

    def test_a_relative_wb_never_runs_a_program_the_repository_planted_under_that_name(self):
        marker = os.path.join(self.base, "planted-ran")
        planted = "#!%s\nopen(%r, 'w').close()\n" % (sys.executable, marker)
        for directory in (self.base, self.cwd):  # the hook's own directory, and the command's, which the repository controls
            with open(os.path.join(directory, "wb"), "w") as handle:
                handle.write(planted)
            os.chmod(os.path.join(directory, "wb"), 0o755)
        before = os.getcwd()
        os.chdir(self.base)
        try:
            code, _ = self.run_hook(self.engine(), argv=["--wb", "./wb"])
        finally:
            os.chdir(before)
        self.assertEqual(0, code)
        self.assertFalse(os.path.exists(marker), "the planted program ran")
        self.assertEqual("failed", self.one_verdict()["outcome"])

    def test_a_wb_inside_the_commands_directory_is_not_run(self):
        inside = os.path.join(self.cwd, "wb")
        self.install_wb(self.engine())
        with open(self.wb, "rb") as source, open(inside, "wb") as target:
            target.write(source.read())
        os.chmod(inside, 0o755)
        link = os.path.join(self.base, "link-to-inside")
        os.symlink(inside, link)
        for wb in (inside, link):
            os_remove_rows(self.home)
            code, _ = self.run_hook(argv=["--wb", wb])
            self.assertEqual(0, code)
            self.assertEqual("failed", self.one_verdict()["outcome"], wb)
        self.assertIsNone(self.wb_args())

    def test_without_wb_there_is_no_default_launcher_and_the_hook_runs_nothing(self):
        # Plan `2026-11-04-shadow-hook-security-review-fixes`, increment B: the launcher is always the one the owner's entry names.
        launcher = os.path.join(self.home, ".config", "project-workbench", "bin", "wb")
        os.makedirs(os.path.dirname(launcher), mode=0o700)
        os.chmod(os.path.join(self.home, ".config", "project-workbench"), 0o700)
        os.chmod(os.path.dirname(launcher), 0o700)
        self.wbdir = os.path.dirname(launcher)
        self.wb = launcher
        self.install_wb(self.engine())
        code, err = self.run_hook(argv=[])
        self.assertEqual(0, code)
        self.assertIn("usage", err)
        self.assertIn("--wb", err)
        self.assertIsNone(self.wb_args(), "the engine was started without a launcher the owner named")
        self.assertEqual(([], 0), self.rows("verdicts.jsonl"))

    def test_an_unknown_argument_or_a_missing_value_is_noted_and_runs_nothing(self):
        self.install_wb(self.engine())
        for argv in (["--wb"], ["--other"], ["--wb", self.wb, "extra"]):
            code, err = self.run_hook(argv=argv)
            self.assertEqual(0, code, argv)
            self.assertIn("usage", err)
        self.assertIsNone(self.wb_args())
        self.assertEqual(([], 0), self.rows("verdicts.jsonl"))

    def test_a_wb_that_takes_too_long_is_stopped_and_recorded_as_a_timeout(self):
        self.install_wb(Replay(0, b"", b"", sleep=30))
        started = time.monotonic()
        with unittest.mock.patch.object(self.mod, "WAIT_SECONDS", 0.5):
            code, _ = self.run_hook()
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual(0, code)
        self.assertEqual("timeout", self.one_verdict()["outcome"])

    def test_a_program_the_engine_started_is_stopped_with_it_when_the_wait_runs_out(self):
        pidfile = os.path.join(self.base, "grandchild.pid")
        self.install_wb(Replay(0, b"", b"", sleep=30), child=pidfile)
        started = time.monotonic()
        with unittest.mock.patch.object(self.mod, "WAIT_SECONDS", 1.5):
            code, _ = self.run_hook()
        elapsed = time.monotonic() - started
        pid = None
        if os.path.exists(pidfile):
            with open(pidfile) as handle:
                pid = int(handle.read() or 0)
        self.assertTrue(pid, "the grandchild did not start")
        self.addCleanup(lambda: self._kill(pid))
        time.sleep(0.2)
        self.assertFalse(self._alive(pid), "the program the engine started is still running")
        self.assertLess(elapsed, 20)
        self.assertEqual(0, code)
        self.assertEqual("timeout", self.one_verdict()["outcome"])

    @staticmethod
    def _alive(pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        try:  # a zombie of this test process is not running
            with open("/proc/%d/stat" % pid) as handle:
                return handle.read().rsplit(")", 1)[1].split()[0] != "Z"
        except OSError:
            return False

    @staticmethod
    def _kill(pid):
        try:
            os.kill(pid, 9)
        except OSError:
            pass

    def test_a_wb_that_leaves_its_pipes_open_after_the_kill_does_not_hold_the_hook(self):
        # The program leaves the process group, so the group kill does not reach it; the hook still returns.
        pidfile = os.path.join(self.base, "escaped.pid")
        self.install_wb(Replay(0, b"", b"", sleep=30), child=pidfile)
        with open(self.wb, "a") as handle:
            pass
        source = WB_SOURCE.replace("subprocess.Popen([sys.executable", "subprocess.Popen(start_new_session=True, args=[sys.executable")
        with open(self.wb, "w") as handle:
            handle.write(source % sys.executable)
        started = time.monotonic()
        with unittest.mock.patch.object(self.mod, "WAIT_SECONDS", 1.0):
            code, _ = self.run_hook()
        elapsed = time.monotonic() - started
        if os.path.exists(pidfile):
            with open(pidfile) as handle:
                self.addCleanup(lambda pid=int(handle.read() or 0): self._kill(pid))
        self.assertLess(elapsed, 15, "the hook waited for a program outside the group")
        self.assertEqual(0, code)
        self.assertEqual("timeout", self.one_verdict()["outcome"])

    def test_the_wait_is_shorter_than_the_hooks_own_30_seconds_and_longer_than_the_engines_25(self):
        self.assertTrue(25 < self.mod.WAIT_SECONDS < 30, self.mod.WAIT_SECONDS)


class Launcher(Base):
    """The engine finds `wb` by name in the trusted entries of the PATH it inherits (`wbkit/call.py`), so the hook's PATH must
    hold the launcher's own directory. Security review of the shadow, finding Low 4: it did not, and every review was refused."""

    def recorded_environment(self):
        self.run_hook(self.engine())
        return self.wb_args()["env"]

    def test_the_path_the_engine_gets_begins_with_the_launchers_own_directory_then_the_fixed_entries(self):
        path = self.recorded_environment()["PATH"].split(os.pathsep)
        self.assertEqual(self.wbdir, path[0])
        self.assertEqual(self.mod.ENVIRONMENT["PATH"].split(os.pathsep), path[1:])

    def test_the_engine_finds_the_launcher_by_its_own_lookup_in_the_environment_the_hook_gives_it(self):
        from workbench.wbkit import call
        env = self.recorded_environment()
        with unittest.mock.patch.dict(os.environ, {"PATH": env["PATH"]}):
            found = call.trusted_which("wb", call.outermost_boundary(self.cwd))
        self.assertEqual(self.wb, found)

    def test_a_directory_inside_a_repository_is_dropped_by_the_engines_own_lookup_even_when_it_is_first_on_the_path(self):
        # The hook already refuses a launcher in the command's directory; this shows that the engine would not use one in a
        # repository above it either, which is what makes a PATH that begins with the launcher's directory safe to give.
        from workbench.wbkit import call
        repo = os.path.join(self.base, "repo")
        for folder in (os.path.join(repo, ".git"), os.path.join(repo, "bin"), os.path.join(repo, "sub")):
            os.makedirs(folder)
        planted = os.path.join(repo, "bin", "wb")
        with open(planted, "w") as handle:
            handle.write("#!/bin/sh\n")
        os.chmod(planted, 0o755)
        path = os.pathsep.join([os.path.join(repo, "bin"), self.mod.ENVIRONMENT["PATH"]])
        with unittest.mock.patch.dict(os.environ, {"PATH": path}):
            self.assertIsNone(call.trusted_which("wb", call.outermost_boundary(os.path.join(repo, "sub"))))

    def test_the_environment_holds_exactly_path_home_and_lang(self):
        self.assertEqual({"PATH", "HOME", "LANG"}, set(self.recorded_environment()))

    def test_a_launcher_that_is_not_named_wb_is_not_run_because_the_engine_looks_for_that_name(self):
        other = os.path.join(self.wbdir, "mywb")
        self.install_wb(self.engine())
        with open(self.wb, "rb") as source, open(other, "wb") as target:
            target.write(source.read())
        os.chmod(other, 0o755)
        code, err = self.run_hook(argv=["--wb", other])
        self.assertEqual(0, code)
        self.assertEqual("failed", self.one_verdict()["outcome"])
        self.assertIsNone(self.wb_args())

    def test_a_launcher_in_a_directory_whose_name_holds_the_path_separator_is_not_run(self):
        odd = os.path.join(self.base, "a" + os.pathsep + "b")
        os.mkdir(odd)
        self.install_wb(self.engine())
        with open(self.wb, "rb") as source, open(os.path.join(odd, "wb"), "wb") as target:
            target.write(source.read())
        os.chmod(os.path.join(odd, "wb"), 0o755)
        code, _ = self.run_hook(argv=["--wb", os.path.join(odd, "wb")])
        self.assertEqual(0, code)
        self.assertEqual("failed", self.one_verdict()["outcome"])
        self.assertIsNone(self.wb_args())

    def test_the_two_waits_add_up_to_less_than_the_hooks_own_30_seconds_and_more_than_the_engines_25(self):
        total = self.mod.WAIT_SECONDS + self.mod.SECOND_WAIT
        self.assertGreater(total, 25)
        self.assertLessEqual(total, 29)


class Failing(Base):
    def test_a_store_that_cannot_be_written_is_noted_and_the_answer_is_unchanged(self):
        os.makedirs(os.path.join(self.home, ".config", "project-workbench", "action-review"), mode=0o755)
        os.chmod(os.path.join(self.home, ".config", "project-workbench"), 0o700)
        os.chmod(os.path.join(self.home, ".config", "project-workbench", "action-review"), 0o755)
        code, err = self.run_hook(self.engine())
        self.assertEqual(0, code)
        self.assertTrue(err.strip(), "the failure is noted on standard error")
        self.assertNotIn(COMMAND, err)

    def test_the_second_write_failing_leaves_the_first_row(self):
        self.install_wb(self.engine())
        real = self.store.append
        calls = []

        def flaky(name, row, home=None):
            calls.append(name)
            if name == "collected.jsonl":
                raise self.store.StoreError("disk full")
            return real(name, row, home)

        with unittest.mock.patch.object(self.mod.store, "append", flaky):
            code, err = self.run_hook()
        self.assertEqual((0, ["verdicts.jsonl", "collected.jsonl"]), (code, calls))
        self.assertEqual("reviewed", self.one_verdict()["outcome"])
        self.assertTrue(err.strip())

    def test_two_hooks_at_once_do_not_lose_a_row(self):
        import threading
        self.install_wb(self.engine())
        threads = [threading.Thread(target=self.run_hook) for _ in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual((6, 0), (len(self.rows("verdicts.jsonl")[0]), self.rows("verdicts.jsonl")[1]))


def os_remove_rows(home):
    """Empty the data directory between the cases of one test."""
    directory = os.path.join(home, ".config", "project-workbench", "action-review")
    if os.path.isdir(directory):
        for name in os.listdir(directory):
            os.remove(os.path.join(directory, name))


if __name__ == "__main__":
    unittest.main()
