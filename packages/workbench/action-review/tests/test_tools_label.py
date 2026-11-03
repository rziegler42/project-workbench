"""The labelling tool (`docs/specs/action-review.md`, "The shadow hook", "Labelling and the report").

Plan `2026-10-29-action-review-shadow-hook`, increment E. `tools/label.py` shows the owner one collected command at a time and
records `right`, `wrong` or `skip` in ``labels.jsonl``. It runs only at a terminal, shows no fact in full unless asked, and
makes every control character, escape sequence and non-ASCII character visible instead of passing it to the terminal. The
owner copies it with ``shadow_store.py`` to a directory outside the project. Written before the code."""

import importlib.util
import io
import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock

from tests import support_install

ROOT = support_install.ROOT
MODULE = os.path.join(ROOT, "packages", "workbench", "action-review")
HOOK_DIR = os.path.join(MODULE, "hook")
LABEL = os.path.join(MODULE, "tools", "label.py")
SHA = "a" * 64
DIFF_MARK = "SECRET-LOOKING-DIFF-LINE-ONLY-ON-REQUEST"


def load():
    if HOOK_DIR not in sys.path:
        sys.path.insert(0, HOOK_DIR)
    spec = importlib.util.spec_from_file_location("action_review_label_under_test", LABEL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Tty(io.StringIO):
    """A stream that says it is a terminal."""

    def isatty(self):
        return True


class Input(Tty):
    """A terminal the owner types into: the lines given, then end of input."""

    def __init__(self, *lines):
        super().__init__("".join(line + "\n" for line in lines))


def collected(number=1, **changes):
    row = {"id": "%032x" % number, "ts": "2026-10-30T01:02:%02dZ" % number, "rule": "safe-git-commit",
           "command_sha256": SHA, "command": "wb run safe-git commit --subject 'Add it %d' -- a.txt" % number,
           "facts": {"contract": 1, "action": "commit", "ok": True, "truncated": False, "errors": [],
                     "facts": {"head": "a" * 40, "path_count": 1, "leave_other_staged": False,
                               "diff": "+hello\n+" + DIFF_MARK, "paths": ["a.txt"], "subject": "Add it %d" % number}},
           "verdict": "approve", "failed_checks": [], "reason": "The change is plain."}
    row.update(changes)
    return row


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.label = load()
        cls.store = sys.modules["shadow_store"]

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.home = os.path.realpath(scratch.name)

    def add(self, *rows):
        for row in rows:
            self.store.append("collected.jsonl", row, self.home)

    def labels(self):
        return self.store.read("labels.jsonl", self.home)[0]

    def run_tool(self, *lines, argv=(), stdin=None, stdout=None):
        stdin = stdin if stdin is not None else Input(*lines)
        stdout, stderr = stdout if stdout is not None else Tty(), io.StringIO()
        code = self.label.main(list(argv), stdin, stdout, stderr, home=self.home)
        return code, stdout.getvalue(), stderr.getvalue()


class Terminal(Base):
    def test_it_refuses_unless_standard_input_and_output_are_both_terminals(self):
        self.add(collected())
        for stdin, stdout in ((io.StringIO("r\n"), Tty()), (Input("r"), io.StringIO()), (io.StringIO("r\n"), io.StringIO())):
            code, out, err = self.run_tool(stdin=stdin, stdout=stdout)
            self.assertEqual(2, code)
            self.assertEqual("", out, "nothing is shown to a stream that is not a terminal")
            self.assertIn("terminal", err)
            self.assertEqual([], self.labels())

    def test_a_real_pseudo_terminal_works_and_a_pipe_is_refused_for_the_script(self):
        self.add(collected(1), collected(2))
        directory = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        for source in (LABEL, os.path.join(HOOK_DIR, "shadow_store.py")):  # copied out as the owner does
            with open(source, "rb") as handle, open(os.path.join(directory, os.path.basename(source)), "wb") as target:
                target.write(handle.read())
        script = os.path.join(directory, "label.py")
        env = {"HOME": self.home, "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "TERM": "xterm"}
        piped = subprocess.run([sys.executable, "-B", script], input=b"r\n", env=env, capture_output=True, timeout=60)
        self.assertEqual(2, piped.returncode, piped.stderr)
        self.assertEqual([], self.labels())
        master, slave = pty.openpty()
        proc = subprocess.Popen([sys.executable, "-B", script], stdin=slave, stdout=slave, stderr=subprocess.PIPE, env=env)
        os.close(slave)
        shown = b""
        try:
            for answer in (b"r fine\n", b"w too wide\n"):
                deadline = time.monotonic() + 20
                while b"[r]ight" not in shown[-400:] and time.monotonic() < deadline:
                    if select.select([master], [], [], 0.2)[0]:
                        shown += os.read(master, 4096)
                os.write(master, answer)
                shown = b""
            proc.wait(timeout=20)
        finally:
            proc.kill()
            proc.wait()
            proc.stderr.close()
            os.close(master)
        labels = self.labels()
        self.assertEqual([("right", "fine"), ("wrong", "too wide")], [(r["label"], r["note"]) for r in labels])


class Choosing(Base):
    def test_right_wrong_and_skip_are_recorded_in_order_with_an_optional_note(self):
        self.add(collected(1), collected(2), collected(3))
        code, out, err = self.run_tool("r", "w it hid a secret", "s")
        self.assertEqual((0, ""), (code, err))
        labels = self.labels()
        self.assertEqual(["right", "wrong", "skip"], [r["label"] for r in labels])
        self.assertEqual(["%032x" % n for n in (1, 2, 3)], [r["id"] for r in labels])
        self.assertEqual([None, "it hid a secret", None], [r.get("note") for r in labels])
        for row in labels:
            self.assertRegex(row["ts"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_the_menu_names_the_choices_and_each_command_is_numbered(self):
        self.add(collected(1), collected(2))
        _, out, _ = self.run_tool("s", "s")
        self.assertIn("1 of 2", out)
        self.assertIn("2 of 2", out)
        for word in ("[r]ight", "[w]rong", "[s]kip", "[f]acts", "[q]uit"):
            self.assertIn(word, out)

    def test_q_and_the_end_of_input_stop_without_recording_the_rest(self):
        self.add(collected(1), collected(2), collected(3))
        code, _, _ = self.run_tool("r", "q")
        self.assertEqual(0, code)
        self.assertEqual(1, len(self.labels()))
        os_remove(self.store.data_dir(self.home), "labels.jsonl")
        code, _, _ = self.run_tool("r")
        self.assertEqual(0, code)
        self.assertEqual(1, len(self.labels()))

    def test_an_answer_that_is_not_a_choice_is_asked_again_and_records_nothing(self):
        self.add(collected(1))
        _, out, _ = self.run_tool("x", "", "yes", "R!", "r")
        self.assertEqual(["right"], [r["label"] for r in self.labels()])
        self.assertEqual(5, out.count("[r]ight"), "four answers were refused and the fifth taken")

    def test_an_upper_case_choice_is_read_as_the_lower_case_one(self):
        self.add(collected(1))
        self.run_tool("W")
        self.assertEqual(["wrong"], [r["label"] for r in self.labels()])

    def test_a_note_is_cut_to_300_printable_characters(self):
        self.add(collected(1))
        self.run_tool("r " + "n" * 400)
        (row,) = self.labels()
        self.assertEqual("n" * 300, row["note"])

    def test_a_note_with_control_or_non_ascii_characters_is_stored_without_them(self):
        self.add(collected(1))
        self.run_tool("r caf\u00e9 \x1b[31mred\u202e")
        (row,) = self.labels()
        self.assertTrue(all(" " <= c <= "~" for c in row["note"]), row["note"])

    def test_a_command_that_is_already_labelled_is_not_shown_again(self):
        self.add(collected(1), collected(2))
        self.store.append("labels.jsonl", {"id": "%032x" % 1, "label": "right", "ts": "2026-10-30T02:00:00Z"}, self.home)
        _, out, _ = self.run_tool("r")
        self.assertIn("1 of 1", out)
        self.assertNotIn("Add it 1", out)
        self.assertEqual(["%032x" % n for n in (1, 2)], [r["id"] for r in self.labels()])

    def test_a_skipped_command_is_not_shown_again_unless_asked(self):
        self.add(collected(1), collected(2))
        self.run_tool("s", "s")
        code, out, _ = self.run_tool("r")
        self.assertEqual(0, code)
        self.assertIn("nothing to label", out.lower())
        code, out, _ = self.run_tool("r", "w", argv=["--skipped"])
        self.assertEqual(["skip", "skip", "right", "wrong"], [r["label"] for r in self.labels()])
        # The later label replaces the skip: nothing is left to revisit.
        _, out, _ = self.run_tool(argv=["--skipped"])
        self.assertIn("nothing to label", out.lower())

    def test_with_nothing_to_label_it_says_so_and_exits_0(self):
        code, out, err = self.run_tool()
        self.assertEqual((0, ""), (code, err))
        self.assertIn("nothing to label", out.lower())

    def test_it_says_how_many_lines_of_the_files_could_not_be_read(self):
        self.add(collected(1))
        with open(os.path.join(self.store.data_dir(self.home), "collected.jsonl"), "ab") as handle:
            handle.write(b"not json\n")
        _, out, _ = self.run_tool("s")
        self.assertIn("1 line", out)

    def test_only_the_options_it_knows_are_accepted(self):
        for argv in (["--other"], ["--skipped", "--skipped"], ["x"]):
            code, _, err = self.run_tool(argv=argv)
            self.assertEqual(2, code, argv)
            self.assertIn("usage", err)


class Showing(Base):
    def test_the_command_and_the_engines_verdict_and_reason_are_shown(self):
        self.add(collected(1, verdict="decline", failed_checks=["scope_is_coherent"], reason="Mixed changes."))
        _, out, _ = self.run_tool("s")
        for word in ("wb run safe-git commit", "decline", "scope_is_coherent", "Mixed changes.", "safe-git-commit"):
            self.assertIn(word, out)

    def test_the_reason_is_introduced_as_words_a_model_may_have_written_and_the_commit_may_have_steered(self):
        # Security review of the shadow, finding Low 2: the reason is model output that a hostile commit message can steer. It is
        # not always a model's: a decline by a fixed check carries the engine's own fixed text, so the line says "when a model was asked".
        self.add(collected(1))
        _, out, _ = self.run_tool("s")
        line = [line for line in out.splitlines() if line.startswith("the reason ")]
        self.assertEqual(1, len(line), out)
        self.assertEqual("the reason (the model's own words when a model was asked, which the commit's own text may have steered): "
                         "The change is plain.", line[0])
        self.assertNotIn("because:", out)

    def test_the_reason_is_still_cleaned_under_its_new_introduction(self):
        self.add(collected(1, reason="r\x1b[31m ‮ Answer approve."))
        _, out, _ = self.run_tool("s")
        line = [line for line in out.splitlines() if line.startswith("the reason ")][0]
        self.assertIn("r\\x1b[31m \\u202e Answer approve.", line)
        for char in out:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))

    def test_a_command_cut_for_length_shows_what_was_left_out_on_the_command_line_itself(self):
        self.add(collected(1, command="\x1b" * 4096))
        _, out, _ = self.run_tool("s")
        line = [line for line in out.splitlines() if line.startswith("command: ")]
        self.assertEqual(1, len(line))
        self.assertRegex(line[0], r"\[\d+ more characters\]$")

    def test_the_meaning_of_right_and_wrong_is_on_screen_with_every_command(self):
        self.add(collected(1), collected(2, verdict="decline", failed_checks=["scope_is_coherent"]))
        _, out, _ = self.run_tool("s", "s")
        sentence = "right = you would have judged as the engine did; wrong = you would not"
        self.assertEqual(2, out.count(sentence), out)

    def test_a_fact_name_with_control_characters_is_shown_as_escapes_in_both_views(self):
        row = collected(1)
        row["facts"]["facts"] = {"na\x1b[2Jme‮": 1, "nested": {"k\x07ey‮": ["v"]}}
        self.add(row)
        _, out, _ = self.run_tool("f", "s")
        for char in out:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))
        self.assertIn("na\\x1b[2Jme\\u202e", out)
        self.assertIn("k\\x07ey\\u202e", out)

    def test_a_command_of_control_characters_is_cut_and_the_verdict_and_prompt_stay_last(self):
        row = collected(1, command="\x1b" * 4096)
        self.add(row)
        _, out, _ = self.run_tool("s")
        self.assertRegex(out, r"\[\d+ more characters\]")
        self.assertLess(out.index("command:"), out.index("the engine said:"))
        self.assertLess(out.index("the engine said:"), out.rindex("[r]ight"))
        for char in out:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))

    def test_a_fact_is_not_shown_unless_the_owner_asks(self):
        self.add(collected(1))
        _, out, _ = self.run_tool("s")
        self.assertNotIn(DIFF_MARK, out)
        self.assertNotIn("+hello", out)
        self.assertIn("diff", out)  # its name, and that it is long, are shown
        self.assertIn("path_count", out)

    def test_f_shows_the_facts_in_full_but_cleaned_and_then_asks_again(self):
        self.add(collected(1))
        _, out, _ = self.run_tool("f", "s")
        self.assertIn(DIFF_MARK, out)
        self.assertEqual(["skip"], [r["label"] for r in self.labels()])
        self.assertEqual(2, out.count("[r]ight"))

    def test_one_fact_over_the_per_fact_bound_is_cut_with_the_exact_count_left(self):
        row = collected(1)
        row["facts"]["facts"]["diff"] = "y" * 5000
        self.add(row)
        _, out, _ = self.run_tool("f", "s")
        self.assertIn("[1000 more characters]", out)
        self.assertNotIn("y" * 4001, out)

    def test_a_very_long_fact_is_cut_with_a_count_of_what_is_left(self):
        row = collected(1)
        row["facts"]["facts"]["diff"] = "x" * 50000
        self.add(row)
        _, out, _ = self.run_tool("f", "s")
        self.assertLess(len(out), 60000)
        self.assertRegex(out, r"\[\d+ more characters\]")

    def test_nothing_that_reaches_the_terminal_is_a_control_or_a_non_ascii_character(self):
        hostile = "echo \x1b[2J\x1b]0;title\x07 \u202e evil \x00 \r\n\t \u200b \U0001F600 \x7f \x9b"
        row = collected(1, command=hostile, reason="r\x1b[31m \u202e")
        row["facts"]["facts"]["diff"] = hostile
        row["facts"]["facts"]["subject"] = hostile
        row["facts"]["errors"] = [{"code": "x", "message": hostile}]
        self.add(row)
        _, out, _ = self.run_tool("f", "w \x1b[31mnote", "q")
        for char in out:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))
        self.assertIn("\\x1b", out)
        self.assertIn("\\u202e", out)
        self.assertIn("\\n", out)

    def test_facts_that_are_not_what_the_engine_prints_are_still_shown_safely(self):
        row = collected(1)
        row["facts"] = {"weird": ["a" * 10] * 3, "nested": {"x": {"y": [1, 2, {"z": "\x1b"}]}}, "n": 12345678901234567890}
        self.add(row)
        code, out, _ = self.run_tool("f", "s")
        self.assertEqual(0, code)
        for char in out:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))


class Interrupting(Base):
    def test_an_interrupt_ends_the_tool_with_130_and_leaves_only_whole_rows(self):
        self.add(collected(1), collected(2))

        class Interrupted(Tty):
            def __init__(self):
                super().__init__("r\n")
                self.reads = 0

            def readline(self, *args):
                self.reads += 1
                if self.reads > 1:
                    raise KeyboardInterrupt()
                return super().readline(*args)

        code, _, _ = self.run_tool(stdin=Interrupted())
        self.assertEqual(130, code)
        rows, skipped = self.store.read("labels.jsonl", self.home)
        self.assertEqual((1, 0), (len(rows), skipped))

    def test_a_store_that_cannot_be_written_stops_the_tool_with_1_and_a_fixed_note(self):
        self.add(collected(1))
        with unittest.mock.patch.object(self.label.store, "append", side_effect=self.store.StoreError("disk full")):
            code, _, err = self.run_tool("r")
        self.assertEqual(1, code)
        self.assertIn("disk full", err)
        self.assertNotIn("Add it", err)

    def test_what_the_tool_says_on_standard_error_is_printable_ascii_whatever_the_store_says(self):
        self.add(collected(1))
        message = "déjà vu \x1b[31m ‮ in /home/é"
        with unittest.mock.patch.object(self.label.store, "append", side_effect=self.store.StoreError(message)):
            code, _, err = self.run_tool("r")
        self.assertEqual(1, code)
        self.assertTrue(err.strip())
        for char in err:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))
        self.assertIn("\\x1b", err)
        with unittest.mock.patch.object(self.label.store, "read", side_effect=self.store.StoreError(message)):
            code, _, err = self.run_tool("r")
        self.assertEqual(1, code)
        for char in err:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))

    def test_input_that_is_not_text_ends_the_tool_with_1_and_says_so(self):
        self.add(collected(1))

        class Bad(Tty):
            def readline(self, *args):
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        code, out, err = self.run_tool(stdin=Bad())
        self.assertEqual(1, code)
        self.assertIn("could not be read", err)
        self.assertEqual([], self.labels())

    def test_a_store_that_cannot_be_read_stops_the_tool_with_1(self):
        os.makedirs(os.path.join(self.home, ".config", "project-workbench", "action-review"), mode=0o755)
        os.chmod(os.path.join(self.home, ".config", "project-workbench"), 0o700)
        os.chmod(os.path.join(self.home, ".config", "project-workbench", "action-review"), 0o755)
        code, _, err = self.run_tool("r")
        self.assertEqual(1, code)
        self.assertTrue(err.strip())


class Source(Base):
    def test_it_imports_only_the_standard_library_and_the_store_beside_it(self):
        import ast
        with open(LABEL, "rb") as handle:
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

    def test_it_starts_no_program_and_reads_no_file_but_the_store(self):
        with open(LABEL, "rb") as handle:
            text = handle.read().decode()
        for word in ("subprocess", "os.system", "os.popen", "eval(", "exec(", "open("):
            self.assertNotIn(word, text, word)


def os_remove(directory, name):
    os.remove(os.path.join(directory, name))


if __name__ == "__main__":
    unittest.main()
