"""The report (`docs/specs/action-review.md`, "Labelling and the report").

Plan `2026-10-29-action-review-shadow-hook`, increment F. `tools/report.py` reads the four files of the store and prints the
counts the cutover condition uses: the engine's false declines and false approves against the owner's labels and the test set,
per action; the rate of false declines against the bound of 10% with at least 10 labelled commits and 10 labelled removals; the
false declines by failed check; what the engine did not review, by reason; and what is still unlabelled. It prints counts and
check names only: never a command, a fact, a reason or a note. Written before the code."""

import ast
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

from tests import support_install

ROOT = support_install.ROOT
MODULE = os.path.join(ROOT, "packages", "workbench", "action-review")
HOOK_DIR = os.path.join(MODULE, "hook")
REPORT = os.path.join(MODULE, "tools", "report.py")
SHA = "a" * 64
MARK = "TEXT-THE-REPORT-MUST-NEVER-PRINT"


def load():
    if HOOK_DIR not in sys.path:
        sys.path.insert(0, HOOK_DIR)
    spec = importlib.util.spec_from_file_location("action_review_report_under_test", REPORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = load()
        cls.store = sys.modules["shadow_store"]

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.home = os.path.realpath(scratch.name)
        self.count = 0

    # -- building the files --------------------------------------------------------------------------------------------
    def command(self, rule="safe-git-commit", verdict="approve", failed=(), label=None, note=None):
        """One collected command and, if `label` is given, its label."""
        self.count += 1
        ident = "%032x" % self.count
        self.store.append("collected.jsonl", {
            "id": ident, "ts": "2026-10-30T01:02:03Z", "rule": rule, "command_sha256": SHA,
            "command": "wb run " + MARK, "facts": {"diff": MARK, "facts": {"subject": MARK}},
            "verdict": verdict, "failed_checks": list(failed), "reason": MARK}, self.home)
        if label:
            self.label(ident, label, note)
        return ident

    def label(self, ident, label, note=None):
        row = {"id": ident, "label": label, "ts": "2026-10-30T02:00:00Z"}
        if note:
            row["note"] = note
        self.store.append("labels.jsonl", row, self.home)

    def verdict_row(self, outcome, verdict=None, failed=(), digest=SHA):
        reviewed = outcome == "reviewed"
        self.store.append("verdicts.jsonl", {
            "ts": "2026-10-30T01:02:03Z", "command_sha256": digest, "outcome": outcome, "verdict": verdict,
            "failed_checks": list(failed), "reason": MARK if reviewed else None, "reviewed": reviewed,
            "no_review_reason": None if reviewed else outcome}, self.home)

    def case(self, name, expected, verdict, failed=()):
        self.store.append("testset.jsonl", {
            "case": name, "ts": "2026-10-30T03:00:00Z", "expected": expected, "verdict": verdict,
            "failed_checks": list(failed), "mismatch": expected != verdict, "bridge": "ask-codex", "model": "m",
            "effort": None}, self.home)

    def labelled(self, rule, right, wrong_declines=0, wrong_approves=0):
        """`right` agreements (half approves, half declines), then the given false declines and false approves."""
        for number in range(right):
            if number % 2:
                self.command(rule, "decline", ["scope_is_coherent"], "right")
            else:
                self.command(rule, "approve", (), "right")
        for _ in range(wrong_declines):
            self.command(rule, "decline", ["scope_is_coherent"], "wrong")
        for _ in range(wrong_approves):
            self.command(rule, "approve", (), "wrong")

    # -- running it ----------------------------------------------------------------------------------------------------
    def run_report(self, argv=()):
        out, err = io.StringIO(), io.StringIO()
        code = self.report.main(list(argv), out, err, home=self.home)
        return code, out.getvalue(), err.getvalue()

    def text(self):
        code, out, err = self.run_report()
        self.assertEqual((0, ""), (code, err), err)
        return out

    def line(self, out, start):
        found = [line for line in out.splitlines() if line.startswith(start)]
        self.assertEqual(1, len(found), (start, out))
        return found[0]


class Counts(Base):
    def test_agreements_false_declines_and_false_approves_are_counted_per_action(self):
        self.labelled("safe-git-commit", 6, wrong_declines=2, wrong_approves=1)
        self.labelled("safe-git-remove", 3)
        out = self.text()
        commit = self.line(out, "commit:")
        self.assertIn("labelled 9", commit)
        self.assertIn("agreements 6", commit)
        self.assertIn("false declines 2", commit)
        self.assertIn("false approves 1", commit)
        remove = self.line(out, "remove:")
        self.assertIn("labelled 3", remove)
        self.assertIn("agreements 3", remove)
        self.assertIn("false declines 0", remove)

    def test_right_for_a_decline_is_an_agreement_and_wrong_for_it_is_a_false_decline(self):
        self.command("safe-git-commit", "decline", ["head_matches"], "right")
        self.command("safe-git-commit", "decline", ["head_matches"], "wrong")
        self.command("safe-git-commit", "approve", (), "right")
        commit = self.line(self.text(), "commit:")
        for part in ("labelled 3", "agreements 2", "false declines 1", "false approves 0"):
            self.assertIn(part, commit)

    def test_the_action_is_the_last_word_of_the_rule_name(self):
        self.command("safe-git-commit", "approve", (), "right")
        self.command("some-module-push", "approve", (), "right")
        out = self.text()
        self.assertIn("labelled 1", self.line(out, "commit:"))
        self.assertIn("labelled 1", self.line(out, "push:"))

    def test_a_skipped_command_is_counted_as_skipped_and_not_as_labelled(self):
        self.labelled("safe-git-commit", 2)
        self.command("safe-git-commit", "approve", (), "skip")
        out = self.text()
        self.assertIn("labelled 2", self.line(out, "commit:"))
        self.assertIn("skipped 1", self.line(out, "waiting:"))

    def test_a_later_label_replaces_an_earlier_one(self):
        ident = self.command("safe-git-commit", "approve", (), "right")
        self.label(ident, "wrong")
        commit = self.line(self.text(), "commit:")
        self.assertIn("false approves 1", commit)
        self.assertIn("agreements 0", commit)
        self.label(ident, "skip")
        out = self.text()
        self.assertIn("labelled 0", self.line(out, "commit:"))
        self.assertIn("skipped 1", self.line(out, "waiting:"))

    def test_a_command_collected_twice_cannot_hide_a_false_approve_or_count_twice(self):
        ident = self.command("safe-git-commit", "approve", (), "wrong")
        row = {"id": ident, "ts": "2026-10-30T01:02:04Z", "rule": "safe-git-commit", "command_sha256": SHA,
               "command": "wb run " + MARK, "facts": {}, "verdict": "decline", "failed_checks": ["head_matches"],
               "reason": MARK}
        self.store.append("collected.jsonl", row, self.home)  # the same id again, with another verdict
        out = self.text()
        commit = self.line(out, "commit:")
        self.assertIn("labelled 1", commit)
        self.assertIn("false approves 1", commit)
        self.assertIn("FALSE APPROVE", out)

    def test_unlabelled_commands_and_labels_of_unknown_commands_are_counted_apart(self):
        self.command("safe-git-commit", "approve", ())
        self.command("safe-git-commit", "approve", ())
        self.label("f" * 32, "right")
        out = self.text()
        waiting = self.line(out, "waiting:")
        self.assertIn("unlabelled 2", waiting)
        self.assertIn("labels of unknown commands 1", waiting)

    def test_false_declines_are_grouped_by_the_failed_check(self):
        for failed in (["scope_is_coherent"], ["scope_is_coherent", "head_matches"], ["head_matches"], ["no_secret_lines"]):
            self.command("safe-git-commit", "decline", failed, "wrong")
        out = self.text()
        by_check = self.line(out, "  false declines by check:")
        self.assertIn("scope_is_coherent 2", by_check)
        self.assertIn("head_matches 2", by_check)
        self.assertIn("no_secret_lines 1", by_check)


class Bound(Base):
    def test_ten_percent_of_twenty_labelled_is_within_the_bound(self):
        self.labelled("safe-git-commit", 18, wrong_declines=2)
        self.labelled("safe-git-remove", 20)
        out = self.text()
        commit = self.line(out, "commit:")
        self.assertIn("10.0%", commit)
        self.assertIn("within the bound", commit)

    def test_fifteen_percent_is_over_the_bound(self):
        self.labelled("safe-git-commit", 17, wrong_declines=3)
        commit = self.line(self.text(), "commit:")
        self.assertIn("15.0%", commit)
        self.assertIn("over the bound", commit)

    def test_fewer_than_ten_labelled_is_not_enough_labels_whatever_the_rate(self):
        self.labelled("safe-git-commit", 9)
        self.labelled("safe-git-remove", 10)
        out = self.text()
        self.assertIn("not enough labels", self.line(out, "commit:"))
        self.assertNotIn("not enough labels", self.line(out, "remove:"))
        self.assertIn("not yet", self.line(out, "cutover:"))

    def test_an_action_with_no_label_at_all_is_not_enough_labels_too(self):
        self.labelled("safe-git-commit", 10)
        out = self.text()
        self.assertIn("remove:", out)
        self.assertIn("not enough labels", self.line(out, "remove:"))
        self.assertIn("not yet", self.line(out, "cutover:"))

    def test_ten_labelled_of_each_with_no_error_and_a_clean_test_set_meets_the_bound(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        self.case("plain-commit", "approve", "approve")
        out = self.text()
        cutover = self.line(out, "cutover:")
        self.assertIn("bound is met", cutover)
        self.assertIn("owner", cutover)
        self.assertIn("(2 test cases)", cutover, "the line says how many cases the test set had")
        self.assertNotIn("still waiting", cutover)

    def test_a_met_bound_says_what_is_still_unlabelled_skipped_or_not_collectable(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.command("safe-git-commit", "approve", ())  # unlabelled
        self.command("safe-git-commit", "approve", (), "skip")
        self.verdict_row("reviewed", "approve", digest="c" * 64)  # reviewed, no collected row
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        cutover = self.line(self.text(), "cutover:")
        self.assertIn("bound is met", cutover)
        for part in ("still waiting", "unlabelled 1", "skipped 1", "not collectable 1"):
            self.assertIn(part, cutover)

    def test_a_rate_just_over_the_bound_keeps_the_cutover_closed_and_names_the_action(self):
        self.labelled("safe-git-commit", 17, wrong_declines=3)  # 15%
        self.labelled("safe-git-remove", 20)
        self.case("c", "decline", "decline", ["x"])
        cutover = self.line(self.text(), "cutover:")
        self.assertIn("not yet", cutover)
        self.assertIn("false declines over the bound for commit", cutover)
        self.assertNotIn("remove", cutover)

    def test_too_few_labels_alone_keep_the_cutover_closed_even_with_a_clean_test_set(self):
        self.labelled("safe-git-commit", 9)
        self.labelled("safe-git-remove", 10)
        self.case("c", "decline", "decline", ["x"])
        cutover = self.line(self.text(), "cutover:")
        self.assertIn("not yet", cutover)
        self.assertIn("not enough labels for commit", cutover)

    def test_a_rate_is_rounded_down_to_a_tenth_of_a_percent(self):
        self.labelled("safe-git-commit", 29, wrong_declines=1)  # 1 of 30 is 3.33...%
        self.assertIn("3.3%", self.line(self.text(), "commit:"))

    def test_a_rate_over_the_bound_for_either_action_keeps_the_cutover_closed(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 8, wrong_declines=4)
        self.case("c", "decline", "decline", ["x"])
        out = self.text()
        self.assertIn("not yet", self.line(out, "cutover:"))
        self.assertIn("remove", self.line(out, "cutover:"))


class FalseApproves(Base):
    def test_a_false_approve_on_the_labels_is_printed_first_and_blocks_the_cutover(self):
        self.labelled("safe-git-commit", 10, wrong_approves=1)
        self.labelled("safe-git-remove", 10)
        self.case("c", "decline", "decline", ["x"])
        out = self.text()
        first = [line for line in out.splitlines() if line.strip()][0]
        self.assertIn("FALSE APPROVE", first)
        self.assertIn("labels 1", first)
        self.assertIn("blocked", self.line(out, "cutover:"))

    def test_a_false_approve_on_the_test_set_is_printed_first_and_blocks_the_cutover(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.case("secret-in-diff", "decline", "approve")
        out = self.text()
        first = [line for line in out.splitlines() if line.strip()][0]
        self.assertIn("FALSE APPROVE", first)
        self.assertIn("test set 1", first)
        self.assertIn("blocked", self.line(out, "cutover:"))

    def test_with_no_false_approve_there_is_no_alarm_line(self):
        self.labelled("safe-git-commit", 4)
        self.assertNotIn("FALSE APPROVE", self.text())

    def test_a_false_decline_on_the_test_set_is_reported_and_does_not_block(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.case("plain-commit", "approve", "decline", ["scope_is_coherent"])
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        out = self.text()
        test_set = self.line(out, "test set:")
        self.assertIn("cases 2", test_set)
        self.assertIn("false declines 1", test_set)
        self.assertIn("false approves 0", test_set)
        self.assertIn("bound is met", self.line(out, "cutover:"))
        self.assertNotIn("FALSE APPROVE", out)

    def test_a_test_set_that_was_not_run_keeps_the_cutover_closed(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        out = self.text()
        self.assertIn("not run", self.line(out, "test set:"))
        self.assertIn("not yet", self.line(out, "cutover:"))

    def test_the_latest_run_of_a_test_case_is_the_one_counted(self):
        self.case("secret-in-diff", "decline", "approve")
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        out = self.text()
        test_set = self.line(out, "test set:")
        self.assertIn("false approves 0", test_set)
        self.assertNotIn("FALSE APPROVE", out)
        self.assertIn("earlier runs with a false approve 1", test_set, "an earlier bad run is not hidden")

    def test_a_clean_history_reports_no_earlier_false_approve(self):
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        self.assertIn("earlier runs with a false approve 0", self.line(self.text(), "test set:"))


class NotReviewed(Base):
    def test_every_prompted_command_the_engine_did_not_review_is_counted_by_reason(self):
        for outcome, times in (("no_rule", 3), ("unreviewable", 2), ("refused", 1), ("failed", 2), ("timeout", 1),
                               ("malformed_input", 1), ("not_bash", 1)):
            for _ in range(times):
                self.verdict_row(outcome)
        self.verdict_row("reviewed", "approve")
        out = self.text()
        not_reviewed = self.line(out, "not reviewed:")
        for part in ("no_rule 3", "unreviewable 2", "refused 1", "failed 2", "timeout 1", "malformed_input 1", "not_bash 1"):
            self.assertIn(part, not_reviewed)
        prompted = self.line(out, "prompted:")
        self.assertIn("prompted 12 (reviewed 1, not reviewed 11)", prompted)

    def test_the_no_rule_count_says_it_includes_pushes_and_remote_jobs(self):
        self.verdict_row("no_rule")
        self.assertIn("pushes and remote jobs", self.text())

    def test_a_reviewed_command_with_no_collected_row_is_counted_as_not_collectable(self):
        other = "b" * 64
        self.verdict_row("reviewed", "approve", digest=other)
        self.verdict_row("reviewed", "decline", ["head_matches"], digest=other)
        self.verdict_row("reviewed", "approve")  # its hash has a collected row below
        self.command("safe-git-commit", "approve", (), "right")  # one collected row, with the shared test hash
        self.assertEqual("reviewed but not collectable: 2", self.line(self.text(), "reviewed but not collectable"))

    def test_with_no_verdict_rows_it_says_none_were_recorded(self):
        out = self.text()
        self.assertIn("prompted 0", self.line(out, "prompted:"))


class Output(Base):
    def test_no_command_fact_reason_or_note_is_ever_printed(self):
        self.labelled("safe-git-commit", 6, wrong_declines=2, wrong_approves=1)
        self.command("safe-git-remove", "decline", ["head_matches"], "wrong", note=MARK)
        self.verdict_row("reviewed", "approve")
        self.case("secret-in-diff", "decline", "approve")
        out = self.text()
        self.assertNotIn(MARK, out)
        self.assertNotIn("wb run", out)

    def test_everything_printed_is_printable_ascii(self):
        self.labelled("safe-git-commit", 6, wrong_declines=1)
        for char in self.text():
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))

    def test_the_report_runs_without_a_terminal(self):
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(0, self.report.main([], out, err, home=self.home))

    def test_an_empty_store_reports_nothing_recorded_and_the_cutover_closed(self):
        out = self.text()
        self.assertIn("not yet", self.line(out, "cutover:"))
        self.assertIn("labelled 0", out)

    def test_lines_the_files_could_not_read_are_counted_by_file(self):
        self.command("safe-git-commit", "approve", (), "right")
        directory = self.store.data_dir(self.home)
        for name in ("collected.jsonl", "labels.jsonl", "verdicts.jsonl", "testset.jsonl"):
            with open(os.path.join(directory, name), "ab") as handle:
                handle.write(b"not json\n")
            os.chmod(os.path.join(directory, name), 0o600)
        unreadable = self.line(self.text(), "unreadable lines:")
        for part in ("collected 1", "labels 1", "verdicts 1", "testset 1"):
            self.assertIn(part, unreadable)

    def test_a_store_that_cannot_be_read_ends_the_report_with_1_and_a_fixed_ascii_note(self):
        message = "déjà \x1b[31m ‮"
        with unittest.mock.patch.object(self.report.store, "read", side_effect=self.store.StoreError(message)):
            code, out, err = self.run_report()
        self.assertEqual((1, ""), (code, out))
        self.assertTrue(err.strip())
        for char in err:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))

    def test_any_argument_is_a_usage_error(self):
        for argv in (["x"], ["--all"], ["--home", "/tmp"]):
            code, out, err = self.run_report(argv)
            self.assertEqual((2, ""), (code, out), argv)
            self.assertIn("usage", err)

    def test_the_copied_script_runs_and_prints_the_report(self):
        self.labelled("safe-git-commit", 3)
        directory = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        for source in (REPORT, os.path.join(HOOK_DIR, "shadow_store.py")):
            with open(source, "rb") as handle, open(os.path.join(directory, os.path.basename(source)), "wb") as target:
                target.write(handle.read())
        run = subprocess.run([sys.executable, "-B", os.path.join(directory, "report.py")], stdin=subprocess.DEVNULL,
                             env={"HOME": self.home, "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                             capture_output=True, timeout=60)
        self.assertEqual((0, b""), (run.returncode, run.stderr))
        self.assertIn(b"commit:", run.stdout)
        self.assertNotIn(MARK.encode(), run.stdout)


class Source(Base):
    def test_it_imports_only_the_standard_library_and_the_store_beside_it(self):
        with open(REPORT, "rb") as handle:
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

    def test_it_starts_no_program_writes_nothing_and_opens_no_file(self):
        with open(REPORT, "rb") as handle:
            text = handle.read().decode()
        for word in ("subprocess", "os.system", "os.popen", "eval(", "exec(", "open(", "append("):
            self.assertNotIn(word, text, word)
        self.assertNotIn("command\"]", text, "the report must not read the command text of a collected row")
        self.assertNotIn("facts\"]", text.replace("\"facts\"] =", ""), "the report must not read the facts of a collected row")


if __name__ == "__main__":
    unittest.main()
