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

from test_actionreview_output import (Base as EngineBase, COMMAND, answered, bridge_failed, commit_doc, described, reply)
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
            run = subprocess.run([sys.executable, "-B", HOOK, "--wb", self.wb], input=json.dumps(self.event()).encode(),
                                 env={"HOME": self.home, "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, timeout=60)
            self.assertEqual((0, b""), (run.returncode, run.stdout), (name, run.stderr))

    def test_the_script_prints_nothing_for_bad_input_too(self):
        bad = [b"", b"not json", b"[]", b"null", b'{"hook_event_name": "PermissionRequest"}', b"\xff\xfe",
               json.dumps(self.event(tool_name="Edit")).encode(), json.dumps(self.event(cwd="relative")).encode(),
               json.dumps(self.event(hook_event_name="PreToolUse")).encode(), b"{" * 5000, b"x" * 2000000]
        self.install_wb(self.engine())
        for raw in bad:
            run = subprocess.run([sys.executable, "-B", HOOK, "--wb", self.wb], input=raw,
                                 env={"HOME": self.home, "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, timeout=60)
            self.assertEqual((0, b""), (run.returncode, run.stdout), raw[:30])

    def test_the_script_prints_nothing_when_the_arguments_are_wrong_or_the_wb_is_missing(self):
        for argv in ([], ["--wb"], ["--wb", "relative/wb"], ["--wb", "/no/such/wb"], ["--other"], ["--wb", self.wb, "x"]):
            run = subprocess.run([sys.executable, "-B", HOOK, *argv], input=json.dumps(self.event()).encode(),
                                 env={"HOME": self.home, "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, timeout=60)
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
            with open(os.path.join(directory, "evilwb"), "w") as handle:
                handle.write(planted)
            os.chmod(os.path.join(directory, "evilwb"), 0o755)
        before = os.getcwd()
        os.chdir(self.base)
        try:
            code, _ = self.run_hook(self.engine(), argv=["--wb", "./evilwb"])
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

    def test_the_default_wb_is_the_launcher_in_the_guarded_store_of_the_home_directory(self):
        launcher = os.path.join(self.home, ".config", "project-workbench", "bin", "wb")
        os.makedirs(os.path.dirname(launcher), mode=0o700)
        os.chmod(os.path.join(self.home, ".config", "project-workbench"), 0o700)
        os.chmod(os.path.dirname(launcher), 0o700)
        self.wbdir = os.path.dirname(launcher)
        self.wb = launcher
        self.install_wb(self.engine())
        self.run_hook(argv=[])
        self.assertEqual("reviewed", self.one_verdict()["outcome"])

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
