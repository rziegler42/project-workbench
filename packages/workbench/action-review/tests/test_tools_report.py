"""The report (`docs/specs/action-review.md`, "Labelling and the report").

Plan `2026-10-29-action-review-shadow-hook`, increment F. `tools/report.py` reads the four files of the store and prints the
counts the cutover condition uses: the engine's false declines and false approves against the owner's labels and the test set,
per action; the rate of false declines against the bound of 10% with at least 10 labelled commits and 10 labelled removals; the
false declines by failed check; what the engine did not review, by reason; and what is still unlabelled. It prints counts and
check names only: never a command, a fact, a reason or a note. Written before the code."""

import ast
import importlib.util
import io
import json
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
MISSING = object()
PREVIEWS = "unconfirmed removals (previews):"


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
        with open(os.path.join(MODULE, "tests", "dangerous-cases.json"), encoding="utf-8") as handle:
            cls.shipped = len(json.load(handle)["cases"])

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.home = os.path.realpath(scratch.name)
        self.count = 0

    # -- building the files --------------------------------------------------------------------------------------------
    def command(self, rule="safe-git-commit", verdict="approve", failed=(), label=None, note=None, facts=None):
        """One collected command and, if `label` is given, its label. `facts` replaces the inner facts of the describe object."""
        self.count += 1
        ident = "%032x" % self.count
        self.store.append("collected.jsonl", {
            "id": ident, "ts": "2026-10-30T01:02:03Z", "rule": rule, "command_sha256": SHA,
            "command": "wb run " + MARK, "facts": {"diff": MARK, "facts": facts if facts is not None else {"subject": MARK}},
            "verdict": verdict, "failed_checks": list(failed), "reason": MARK}, self.home)
        if label:
            self.label(ident, label, note)
        return ident

    def removal(self, confirm, verdict, failed=(), label=None, note=None):
        """One collected removal whose describe facts say `confirm` (a boolean, or any other value for a malformed fact); the
        value `MISSING` leaves the fact out."""
        facts = {"requested_paths": [MARK]}
        if confirm is not MISSING:
            facts["confirm"] = confirm
        return self.command("safe-git-remove", verdict, failed, label, note, facts=facts)

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

    def full_test_set(self, skip=0):
        """The shipped number of clean test cases, less `skip` (the caller adds those by name)."""
        for number in range(self.shipped - skip):
            self.case("case-%02d" % number, "decline", "decline", ["no_secret_lines"])

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
        self.full_test_set(skip=2)
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        self.case("plain-commit", "approve", "approve")
        out = self.text()
        cutover = self.line(out, "cutover:")
        self.assertIn("bound is met", cutover)
        self.assertIn("owner", cutover)
        self.assertIn("(%d test cases)" % self.shipped, cutover, "the line says how many cases the test set had")
        self.assertNotIn("still waiting", cutover)

    def test_the_number_of_shipped_cases_in_the_report_is_the_number_in_the_case_file(self):
        self.assertEqual(self.shipped, self.report.SHIPPED_TEST_CASES)

    def test_a_test_set_with_fewer_cases_than_the_shipped_ones_keeps_the_cutover_closed_though_every_case_is_clean(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set(skip=1)
        cutover = self.line(self.text(), "cutover:")
        self.assertIn("not yet", cutover)
        self.assertIn("the test set has %d of %d cases" % (self.shipped - 1, self.shipped), cutover)
        self.assertNotIn("bound is met", cutover)

    def test_a_full_test_set_does_not_make_up_for_missing_labels(self):
        self.full_test_set()
        cutover = self.line(self.text(), "cutover:")
        self.assertIn("not yet", cutover)
        self.assertIn("not enough labels for commit", cutover)
        self.assertIn("not enough labels for remove", cutover)
        self.assertNotIn("bound is met", cutover)

    def test_the_full_shipped_number_of_clean_cases_can_meet_the_bound(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set()
        self.assertIn("bound is met", self.line(self.text(), "cutover:"))

    def test_more_distinct_case_names_than_the_shipped_number_keeps_the_cutover_closed_and_says_so(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set()
        self.case("a-name-that-is-not-shipped", "decline", "decline", ["no_secret_lines"])
        cutover = self.line(self.text(), "cutover:")
        self.assertIn("not yet", cutover)
        self.assertIn("%d cases, more than the %d shipped" % (self.shipped + 1, self.shipped), cutover)
        self.assertNotIn("bound is met", cutover)

    def test_a_case_run_twice_counts_once_toward_the_shipped_number(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set()
        self.full_test_set()  # a second full run adds rows, not cases
        out = self.text()
        self.assertIn("cases %d of %d" % (self.shipped, self.shipped), self.line(out, "test set:"))
        self.assertIn("bound is met", self.line(out, "cutover:"))

    def test_a_met_bound_says_what_is_still_unlabelled_skipped_or_not_collectable(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.command("safe-git-commit", "approve", ())  # unlabelled
        self.command("safe-git-commit", "approve", (), "skip")
        self.verdict_row("reviewed", "approve", digest="c" * 64)  # reviewed, no collected row
        self.full_test_set()
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
        self.full_test_set(skip=2)
        self.case("plain-commit", "approve", "decline", ["scope_is_coherent"])
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        out = self.text()
        test_set = self.line(out, "test set:")
        self.assertIn("cases %d of %d" % (self.shipped, self.shipped), test_set)
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

    def test_a_case_approved_wrongly_in_an_earlier_run_closes_the_cutover_even_when_the_latest_run_declines_it(self):
        # Security review of the shadow, finding Medium 2(a): a model is not deterministic, so a clean rerun must not clear a bad run.
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set(skip=1)
        self.case("secret-in-diff", "decline", "approve")
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        out = self.text()
        first = [line for line in out.splitlines() if line.strip()][0]
        self.assertIn("FALSE APPROVE", first)
        self.assertIn("test set 1", first)
        self.assertIn("secret-in-diff", first, "the first line names the case")
        self.assertIn("blocked", self.line(out, "cutover:"))
        self.assertNotIn("bound is met", out)

    def test_the_test_set_line_counts_false_approves_in_any_run_and_in_the_latest(self):
        self.case("secret-in-diff", "decline", "approve")
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        self.case("head-mismatch", "decline", "approve")
        line = self.line(self.text(), "test set:")
        self.assertIn("false approves 2 (in any run; 1 in the latest)", line)

    def test_the_alarm_says_how_to_start_the_test_set_again(self):
        self.case("secret-in-diff", "decline", "approve")
        out = self.text()
        self.assertIn("delete testset.jsonl", out)
        self.assertIn("run the test set again", out)

    def test_the_title_says_what_the_report_prints_including_case_names(self):
        out = self.text()
        self.assertIn("Shadow report (counts, rule names, check names and test case names only)", out)
        self.assertNotIn("(counts, rule names and check names only)", out)

    def test_a_false_approve_is_found_whatever_the_order_of_the_runs(self):
        for order in ((("approve", "decline"), ("decline", "decline")), (("decline", "decline"), ("decline", "approve")),
                      (("decline", "approve"), ("decline", "decline"), ("decline", "decline"))):
            for name in os.listdir(self.store.data_dir(self.home)) if os.path.isdir(self.store.data_dir(self.home)) else ():
                os.remove(os.path.join(self.store.data_dir(self.home), name))
            for expected, verdict in order:
                checks = ["no_secret_lines"] if verdict == "decline" else []
                self.case("secret-in-diff", expected, verdict, checks)
            out = self.text()
            self.assertEqual(any(v == "approve" and e == "decline" for e, v in order), "FALSE APPROVE" in out, order)

    def test_the_same_case_name_with_rows_that_expect_approve_and_decline_counts_a_false_approve_only_for_a_decline_expected_row(self):
        self.case("odd-case", "approve", "approve")
        self.case("odd-case", "decline", "approve")
        out = self.text()
        self.assertIn("FALSE APPROVE", out)
        self.assertIn("test set 1 (odd-case)", out)

    def test_an_approve_that_was_expected_is_never_a_false_approve(self):
        self.case("odd-case", "approve", "approve")
        self.assertNotIn("FALSE APPROVE", self.text())

    def test_a_clean_history_has_no_false_approve_in_any_run(self):
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        self.case("secret-in-diff", "decline", "decline", ["no_secret_lines"])
        out = self.text()
        self.assertIn("false approves 0 (in any run; 0 in the latest)", self.line(out, "test set:"))
        self.assertNotIn("FALSE APPROVE", out)
        self.assertNotIn("delete testset.jsonl", out)

    def test_the_names_of_the_cases_approved_wrongly_are_listed_up_to_five_and_counted_beyond(self):
        for number in range(7):
            self.case("bad-%d" % number, "decline", "approve")
        first = [line for line in self.text().splitlines() if line.strip()][0]
        self.assertIn("test set 7", first)
        for number in range(5):
            self.assertIn("bad-%d" % number, first)
        self.assertNotIn("bad-5", first)
        self.assertIn("and 2 more", first)


class Previews(Base):
    """Decision `2026-11-05-unconfirmed-removals-are-outside-the-action-review-measure`; plan
    `2026-11-05-shadow-report-counts-previews-apart`, increment A. A labelled removal whose collected `confirm` fact is false is a
    preview: it is counted on a line of its own and not in the removal rate, minimum or by-check line, and a preview the engine
    approved wrongly is still a false approve."""

    def test_a_labelled_preview_is_counted_on_its_own_line_and_not_in_the_removal_count(self):
        self.removal(True, "approve", (), "right")
        self.removal(False, "decline", ["confirm_present"], "wrong")
        out = self.text()
        self.assertIn("labelled 1 (right 1, wrong 0)", self.line(out, "remove:"))
        preview = self.line(out, PREVIEWS)
        self.assertIn("labelled 1 (right 0, wrong 1)", preview)
        self.assertIn("false declines 1", preview)
        self.assertIn("false approves 0", preview)

    def test_the_owners_shapes_leave_seven_confirmed_removals_and_four_previews(self):
        self.labelled("safe-git-commit", 9)
        for _ in range(7):
            self.removal(True, "approve", (), "right")
        for _ in range(4):
            self.removal(False, "decline", ["confirm_present"], "wrong")
        out = self.text()
        remove = self.line(out, "remove:")
        self.assertIn("labelled 7 (right 7, wrong 0)", remove)
        self.assertIn("not enough labels (10 needed)", remove)
        preview = self.line(out, PREVIEWS)
        self.assertIn("labelled 4 (right 0, wrong 4)", preview)
        self.assertIn("false declines 4", preview)
        cutover = self.line(out, "cutover:")
        self.assertIn("not enough labels for commit", cutover)
        self.assertIn("not enough labels for remove", cutover)
        self.assertNotIn("false declines over the bound", cutover)

    def test_three_more_right_confirmed_removals_put_the_removal_line_within_the_bound(self):
        for _ in range(10):
            self.removal(True, "approve", (), "right")
        for _ in range(4):
            self.removal(False, "decline", ["confirm_present"], "wrong")
        remove = self.line(self.text(), "remove:")
        self.assertIn("labelled 10", remove)
        self.assertIn("false declines 0", remove)
        self.assertIn("within the bound", remove)

    def test_the_by_check_line_of_the_removals_leaves_out_the_previews_and_the_previews_have_their_own(self):
        self.removal(True, "decline", ["removal_valid"], "wrong")
        for _ in range(3):
            self.removal(False, "decline", ["confirm_present"], "wrong")
        lines = self.text().splitlines()
        by_check = [number for number, line in enumerate(lines) if line.startswith("  false declines by check")]
        self.assertEqual(2, len(by_check), lines)
        remove_at = next(number for number, line in enumerate(lines) if line.startswith("remove:"))
        preview_at = next(number for number, line in enumerate(lines) if line.startswith(PREVIEWS))
        self.assertEqual(remove_at + 1, by_check[0])
        self.assertIn("removal_valid 1", lines[by_check[0]])
        self.assertNotIn("confirm_present", lines[by_check[0]])
        self.assertEqual(preview_at + 1, by_check[1])
        self.assertIn("confirm_present 3", lines[by_check[1]])

    def test_a_preview_the_engine_approved_and_the_owner_labelled_wrong_is_a_false_approve_that_blocks_the_cutover(self):
        self.removal(False, "approve", (), "wrong")
        out = self.text()
        self.assertIn("false approves 1", self.line(out, PREVIEWS))
        self.assertIn("FALSE APPROVE: labels 1", out)
        self.assertIn("blocked by a false approve", self.line(out, "cutover:"))

    def test_a_preview_labelled_right_is_an_agreement_whatever_the_engine_said(self):
        self.removal(False, "decline", ["confirm_present"], "right")
        self.removal(False, "approve", (), "right")
        preview = self.line(self.text(), PREVIEWS)
        self.assertIn("labelled 2 (right 2, wrong 0)", preview)
        self.assertIn("false declines 0", preview)
        self.assertIn("false approves 0", preview)

    def test_a_removal_whose_confirm_fact_is_missing_or_not_a_boolean_is_counted_as_a_confirmed_removal(self):
        for value in (MISSING, None, "false", 0, [], {}):
            self.removal(value, "decline", ["confirm_present"], "wrong")
        out = self.text()
        self.assertIn("labelled 6 (right 0, wrong 6)", self.line(out, "remove:"))
        self.assertIn("labelled 0", self.line(out, PREVIEWS))

    def test_a_row_whose_facts_have_another_shape_is_counted_as_a_confirmed_removal(self):
        for facts in ({}, {"facts": "text"}, {"facts": None}, {"facts": [1]}, {"confirm": False}):  # the store keeps `facts` an object
            self.count += 1
            ident = "%032x" % self.count
            self.store.append("collected.jsonl", {
                "id": ident, "ts": "2026-10-30T01:02:03Z", "rule": "safe-git-remove", "command_sha256": SHA, "command": "x",
                "facts": facts, "verdict": "decline", "failed_checks": ["confirm_present"], "reason": "x"}, self.home)
            self.label(ident, "wrong")
        out = self.text()
        self.assertIn("labelled 5", self.line(out, "remove:"))
        self.assertIn("labelled 0", self.line(out, PREVIEWS))

    def test_a_skipped_or_unlabelled_preview_is_counted_as_skipped_or_unlabelled_and_not_as_labelled(self):
        self.removal(False, "decline", ["confirm_present"], "skip")
        self.removal(False, "decline", ["confirm_present"])
        out = self.text()
        self.assertIn("labelled 0", self.line(out, PREVIEWS))
        self.assertIn("unlabelled 1, skipped 1", self.line(out, "waiting:"))

    def test_a_later_label_moves_nothing_between_the_groups_and_replaces_the_earlier_one(self):
        ident = self.removal(False, "decline", ["confirm_present"], "wrong")
        self.label(ident, "right")
        preview = self.line(self.text(), PREVIEWS)
        self.assertIn("labelled 1 (right 1, wrong 0)", preview)

    def test_a_preview_collected_twice_is_counted_once(self):
        ident = self.removal(False, "decline", ["confirm_present"], "wrong")
        self.store.append("collected.jsonl", {
            "id": ident, "ts": "2026-10-30T01:02:04Z", "rule": "safe-git-remove", "command_sha256": SHA, "command": "x",
            "facts": {"facts": {"confirm": False}}, "verdict": "decline", "failed_checks": ["confirm_present"], "reason": "x"},
            self.home)
        self.assertIn("labelled 1 (right 0, wrong 1)", self.line(self.text(), PREVIEWS))

    def test_a_commit_is_never_counted_as_a_preview_whatever_its_facts_hold(self):
        self.command("safe-git-commit", "decline", ["head_matches"], "wrong", facts={"confirm": False})
        out = self.text()
        self.assertIn("labelled 1", self.line(out, "commit:"))
        self.assertIn("labelled 0", self.line(out, PREVIEWS))

    def test_the_preview_line_is_printed_with_no_label_at_all_and_prints_no_fact_command_reason_or_note(self):
        self.assertIn("labelled 0 (right 0, wrong 0)", self.line(self.text(), PREVIEWS))
        self.removal(False, "decline", ["confirm_present"], "wrong", note=MARK)
        out = self.text()
        self.assertNotIn(MARK, out)
        self.assertNotIn("wb run", out)
        self.assertNotIn("requested_paths", out)

    def test_a_preview_does_not_count_toward_the_removal_minimum_of_ten(self):
        self.labelled("safe-git-commit", 10)
        for _ in range(9):
            self.removal(True, "approve", (), "right")
        for _ in range(5):
            self.removal(False, "decline", ["confirm_present"], "wrong")
        self.full_test_set()
        cutover = self.line(self.text(), "cutover:")
        self.assertIn("not enough labels for remove", cutover)

    def test_ten_confirmed_removals_ten_commits_and_a_clean_test_set_meet_the_bound_whatever_the_previews_hold(self):
        self.labelled("safe-git-commit", 10)
        for _ in range(10):
            self.removal(True, "approve", (), "right")
        for _ in range(5):
            self.removal(False, "decline", ["confirm_present"], "wrong")
        self.full_test_set()
        self.assertIn("the bound is met", self.line(self.text(), "cutover:"))


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

    SPLIT = "  by failed check (a row counts under each check it failed): "

    def uncollected(self, digest, verdict, failed=()):
        """One reviewed verdict row with its own command hash (so it has no collected row unless the test makes one)."""
        self.verdict_row("reviewed", verdict, failed, digest=digest)

    def test_the_uncollectable_commands_are_grouped_by_their_failed_checks(self):
        for number in range(3):
            self.uncollected("%064x" % (number + 1), "decline", ["no_secret_lines"])
        self.uncollected("%064x" % 4, "decline", ["paths_not_credentials"])
        for number in (5, 6):
            self.uncollected("%064x" % number, "approve")
        self.verdict_row("reviewed", "approve")  # its hash has a collected row below
        self.command("safe-git-commit", "approve", (), "right")
        out = self.text()
        self.assertEqual("reviewed but not collectable: 6", self.line(out, "reviewed but not collectable"))
        self.assertEqual(self.SPLIT + "no_secret_lines 3, approve 2, paths_not_credentials 1", self.line(out, self.SPLIT[:12]))

    def test_the_split_line_follows_the_count_line_directly(self):
        self.uncollected("%064x" % 1, "decline", ["no_secret_lines"])
        lines = self.text().splitlines()
        at = lines.index("reviewed but not collectable: 1")
        self.assertTrue(lines[at + 1].startswith(self.SPLIT), lines)

    def test_a_decline_that_failed_two_checks_counts_under_both_and_the_count_stays_one(self):
        self.uncollected("%064x" % 1, "decline", ["no_secret_lines", "paths_not_credentials"])
        out = self.text()
        self.assertEqual("reviewed but not collectable: 1", self.line(out, "reviewed but not collectable"))
        self.assertEqual(self.SPLIT + "no_secret_lines 1, paths_not_credentials 1", self.line(out, self.SPLIT[:12]))

    def test_nothing_uncollectable_prints_no_split_line(self):
        self.verdict_row("reviewed", "approve")
        self.command("safe-git-commit", "approve", (), "right")  # the collected row of that hash
        out = self.text()
        self.assertEqual("reviewed but not collectable: 0", self.line(out, "reviewed but not collectable"))
        self.assertNotIn("a row counts under each check", out)

    def test_a_command_reviewed_twice_with_one_collected_row_is_grouped_by_its_latest_verdict_row(self):
        self.verdict_row("reviewed", "decline", ["no_secret_lines"])  # the older one
        self.verdict_row("reviewed", "decline", ["paths_not_credentials"])  # the latest
        self.command("safe-git-commit", "approve", (), "right")  # one collected row for the shared hash
        out = self.text()
        self.assertEqual("reviewed but not collectable: 1", self.line(out, "reviewed but not collectable"))
        self.assertEqual(self.SPLIT + "paths_not_credentials 1", self.line(out, self.SPLIT[:12]))

    def test_a_command_reviewed_three_times_with_one_collected_row_is_grouped_by_its_latest_two(self):
        self.verdict_row("reviewed", "decline", ["no_secret_lines"])
        self.verdict_row("reviewed", "approve")
        self.verdict_row("reviewed", "decline", ["paths_not_credentials"])
        self.command("safe-git-commit", "approve", (), "right")
        out = self.text()
        self.assertEqual("reviewed but not collectable: 2", self.line(out, "reviewed but not collectable"))
        self.assertEqual(self.SPLIT + "approve 1, paths_not_credentials 1", self.line(out, self.SPLIT[:12]))

    def test_the_split_line_prints_no_hash_reason_or_other_text_of_the_store(self):
        self.uncollected("%064x" % 7, "decline", ["no_secret_lines"])
        out = self.text()
        self.assertNotIn(MARK, out)
        self.assertNotIn("%064x" % 7, out)
        self.assertTrue(out.isascii())

    def test_with_no_verdict_rows_it_says_none_were_recorded(self):
        out = self.text()
        self.assertIn("prompted 0", self.line(out, "prompted:"))


class Handles(Base):
    """Plan `2026-11-07-label-declined-secrets`, increment A. A handle is a collected row for a command the engine declined for a
    secret: its facts carry the boolean `handle` and nothing the report reads but that. The report counts the labelled handles on a
    line of their own, apart from the actions and from the previews, and folds them into the counts of their action only when the
    owner passes `--fold-handles`; the line says which it did."""

    FOLD = "--fold-handles"
    FIXED = "[declined for a secret; the command is not kept]"

    def handle(self, rule="safe-git-commit", label=None, confirm=None, paths=("a.txt",), digest=SHA, failed=("no_secret_lines",),
               marker=True):
        """One collected handle and, if `label` is given, its label. `marker` replaces the value of the `handle` fact."""
        self.count += 1
        ident = "%032x" % self.count
        inner = {"paths": list(paths), "paths_dropped": 0}
        if confirm is not None:
            inner["confirm"] = confirm
        self.store.append("collected.jsonl", {
            "id": ident, "ts": "2026-10-30T01:02:03Z", "rule": rule, "command_sha256": digest, "command": self.FIXED,
            "facts": {"handle": marker, "facts": inner}, "verdict": "decline", "failed_checks": list(failed),
            "reason": "declined for a secret; nothing of the command is kept"}, self.home)
        if label:
            self.label(ident, label)
        return ident

    def folded(self):
        code, out, err = self.run_report([self.FOLD])
        self.assertEqual((0, ""), (code, err), err)
        return out

    def test_a_labelled_handle_is_counted_on_its_own_line_and_not_in_the_action_count(self):
        self.command("safe-git-commit", "approve", (), "right")
        self.handle("safe-git-commit", "wrong")
        out = self.text()
        self.assertIn("labelled 1 (right 1, wrong 0)", self.line(out, "commit:"))
        handles = self.line(out, "handles:")
        self.assertIn("apart", handles)
        self.assertIn("labelled 1 (right 0, wrong 1)", handles)
        self.assertIn("false declines 1", handles)

    def test_apart_the_counts_the_bound_and_the_verdict_are_those_of_the_same_store_without_handles(self):
        self.labelled("safe-git-commit", 10, wrong_declines=1)
        self.labelled("safe-git-remove", 10)
        self.full_test_set()
        before = self.text()
        for _ in range(5):
            self.handle("safe-git-commit", "wrong")
        self.handle("safe-git-remove", "wrong")
        after = self.text()
        for start in ("commit:", "remove:", "cutover:"):
            self.assertEqual(self.line(before, start), self.line(after, start), start)

    def test_folded_the_handles_join_the_counts_of_their_action_and_the_line_says_so(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.handle("safe-git-commit", "wrong")
        self.handle("safe-git-commit", "right")
        out = self.folded()
        self.assertIn("labelled 12 (right 11, wrong 1)", self.line(out, "commit:"))
        self.assertIn("false declines 1", self.line(out, "commit:"))
        handles = self.line(out, "handles:")
        self.assertIn("folded", handles)
        self.assertNotIn("apart", handles)

    def test_folded_handles_can_put_a_rate_over_the_bound_and_apart_they_cannot(self):
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set()
        for _ in range(3):
            self.handle("safe-git-commit", "wrong")
        self.assertIn("the bound is met", self.line(self.text(), "cutover:"))
        self.assertIn("false declines over the bound for commit", self.line(self.folded(), "cutover:"))

    def test_a_removal_handle_is_never_a_preview_whatever_its_confirm_fact_says(self):
        self.handle("safe-git-remove", "wrong", confirm=False)
        apart = self.text()
        self.assertIn("labelled 0", self.line(apart, PREVIEWS))
        self.assertIn("labelled 0", self.line(apart, "remove:"))
        folded = self.folded()
        self.assertIn("labelled 0", self.line(folded, PREVIEWS))
        self.assertIn("labelled 1 (right 0, wrong 1)", self.line(folded, "remove:"))

    def test_a_handle_that_waits_or_was_skipped_is_counted_as_waiting_or_skipped(self):
        self.handle("safe-git-commit")
        self.handle("safe-git-commit", "skip")
        out = self.text()
        self.assertIn("unlabelled 1, skipped 1", self.line(out, "waiting:"))
        handles = self.line(out, "handles:")
        self.assertIn("labelled 0", handles)
        self.assertIn("waiting 1", handles)
        self.assertIn("skipped 1", handles)

    def test_a_later_label_replaces_an_earlier_one_for_a_handle(self):
        ident = self.handle("safe-git-commit", "wrong")
        self.label(ident, "right")
        self.assertIn("labelled 1 (right 1, wrong 0)", self.line(self.text(), "handles:"))

    def test_a_row_whose_handle_fact_is_not_the_boolean_true_is_an_ordinary_command(self):
        for marker in (False, "yes", 1, None, ["handle"]):
            self.handle("safe-git-commit", "right", marker=marker)
        out = self.text()
        self.assertIn("labelled 5 (right 5, wrong 0)", self.line(out, "commit:"))
        self.assertEqual([], [line for line in out.splitlines() if line.startswith("handles:")])

    def test_a_fact_called_handle_in_the_inner_facts_does_not_make_a_handle(self):
        self.command("safe-git-commit", "decline", ["scope_is_coherent"], "wrong", facts={"handle": True})
        out = self.text()
        self.assertIn("labelled 1 (right 0, wrong 1)", self.line(out, "commit:"))
        self.assertEqual([], [line for line in out.splitlines() if line.startswith("handles:")])

    def test_with_no_handle_there_is_no_handles_line(self):
        self.labelled("safe-git-commit", 4, wrong_declines=1)
        self.assertEqual([], [line for line in self.text().splitlines() if line.startswith("handles:")])
        self.assertEqual([], [line for line in self.folded().splitlines() if line.startswith("handles:")])

    def test_the_false_declines_of_the_handles_are_grouped_by_check_under_their_line_and_not_under_the_actions(self):
        self.command("safe-git-commit", "decline", ["scope_is_coherent"], "wrong")
        self.handle("safe-git-commit", "wrong", failed=("no_secret_lines", "paths_not_credentials"))
        lines = self.text().splitlines()
        by_check = [number for number, line in enumerate(lines) if line.startswith("  false declines by check")]
        handles_at = next(number for number, line in enumerate(lines) if line.startswith("handles:"))
        self.assertEqual(2, len(by_check), lines)
        self.assertIn("scope_is_coherent 1", lines[by_check[0]])
        self.assertNotIn("no_secret_lines", lines[by_check[0]])
        self.assertEqual(handles_at + 1, by_check[1])
        self.assertIn("no_secret_lines 1", lines[by_check[1]])
        self.assertIn("paths_not_credentials 1", lines[by_check[1]])

    def test_a_handle_removes_a_command_from_the_not_collectable_count(self):
        other = "b" * 64
        self.verdict_row("reviewed", "decline", ["no_secret_lines"], digest=SHA)
        self.verdict_row("reviewed", "decline", ["no_secret_lines"], digest=other)
        self.assertIn("reviewed but not collectable: 2", self.text())
        self.handle("safe-git-commit", digest=SHA)
        out = self.text()
        self.assertIn("reviewed but not collectable: 1", out)
        self.assertIn("no_secret_lines 1", self.line(out, "  by failed check"))

    def test_the_handles_line_prints_no_path_fact_command_reason_or_note(self):
        self.handle("safe-git-commit", "wrong", paths=(MARK, "dir/" + MARK))
        out = self.text() + self.folded()
        self.assertNotIn(MARK, out)
        self.assertNotIn(self.FIXED, out)
        for char in out:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))

    def test_the_option_is_the_only_argument_and_stands_alone(self):
        for argv in (["--fold-handles", "x"], ["--fold-handles=1"], ["--fold-handles", "--fold-handles"], ["--fold"], ["fold-handles"]):
            code, out, err = self.run_report(argv)
            self.assertEqual((2, ""), (code, out), argv)
            self.assertIn("usage: report.py [--fold-handles]", err)

    def test_the_cutover_stays_blocked_by_a_false_approve_on_a_handle_row_that_says_approve(self):
        """A handle is always a decline. A row that says otherwise is not hidden: it is a false approve when the owner labels it wrong."""
        self.count += 1
        ident = "%032x" % self.count
        self.store.append("collected.jsonl", {
            "id": ident, "ts": "2026-10-30T01:02:03Z", "rule": "safe-git-commit", "command_sha256": SHA, "command": self.FIXED,
            "facts": {"handle": True, "facts": {"paths": [], "paths_dropped": 0}}, "verdict": "approve", "failed_checks": [],
            "reason": "x"}, self.home)
        self.label(ident, "wrong")
        for out in (self.text(), self.folded()):
            self.assertIn("blocked by a false approve", out)
            self.assertIn("FALSE APPROVE: labels 1, test set 0.", out)  # once, in either mode: a folded handle is not counted twice
        self.assertIn("false approves 1", self.line(self.text(), "handles:"))

    def test_the_bound_is_met_with_a_handle_waiting_and_the_still_waiting_suffix_counts_it(self):
        """The met-or-not verdict is that of the actions alone; the informational suffix counts the unlabelled and skipped commands,
        handles included, because the owner still has them to judge."""
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set()
        without = self.line(self.text(), "cutover:")
        self.assertIn("the bound is met", without)
        self.assertNotIn("still waiting", without)
        self.handle("safe-git-commit")
        self.handle("safe-git-commit", "skip")
        for out in (self.text(), self.folded()):
            cutover = self.line(out, "cutover:")
            self.assertIn("the bound is met", cutover)
            self.assertIn("still waiting: unlabelled 1, skipped 1, not collectable 0", cutover)

    def test_folded_a_waiting_or_skipped_handle_is_counted_as_waiting_or_skipped_and_not_as_labelled(self):
        self.handle("safe-git-commit")
        self.handle("safe-git-remove", "skip")
        out = self.folded()
        self.assertIn("unlabelled 1, skipped 1", self.line(out, "waiting:"))
        self.assertIn("labelled 0", self.line(out, "commit:"))
        self.assertIn("labelled 0", self.line(out, "remove:"))
        handles = self.line(out, "handles:")
        self.assertIn("folded", handles)
        self.assertIn("waiting 1, skipped 1", handles)


class Allowed(Base):
    """Plan `2026-11-08-action-review-cutover-for-commit`, increment E: what the hook allowed. A verdict row whose field `answer` is
    `allow` is a command the hook answered. The report counts them by action and by day and gives the ids of their collected rows to
    sample; it prints nothing new when no row records an allow; an allowed command is not a labelled one."""
    COUNT = "hook allowed: "
    DAYS = "hook allowed by day: "
    SAMPLE = "hook allowed, to sample (newest first): "

    def allow(self, number, rule="safe-git-commit", day="2026-11-10", collect=True, label=None, with_rule=True):
        """One command the hook allowed: a reviewed approve whose verdict row says `allow`, with its own command hash, and (unless
        `collect` is false) its collected row. Returns the id of the collected row, or None."""
        digest = "%064x" % (1000 + number)
        row = {"ts": day + "T01:02:03Z", "command_sha256": digest, "outcome": "reviewed", "verdict": "approve", "failed_checks": [],
               "reason": MARK, "reviewed": True, "no_review_reason": None, "answer": "allow"}
        if with_rule:
            row["rule"] = rule
        self.store.append("verdicts.jsonl", row, self.home)
        if not collect:
            return None
        self.count += 1
        ident = "%032x" % (5000 + self.count)
        self.store.append("collected.jsonl", {
            "id": ident, "ts": day + "T01:02:03Z", "rule": rule, "command_sha256": digest, "command": "wb run " + MARK,
            "facts": {"diff": MARK, "facts": {"subject": MARK}}, "verdict": "approve", "failed_checks": [], "reason": MARK},
            self.home)
        if label:
            self.label(ident, label)
        return ident

    def lines_with(self, out, start):
        return [line for line in out.splitlines() if line.startswith(start)]

    def test_no_allowed_row_prints_no_line_about_the_hook(self):
        self.labelled("safe-git-commit", 4)
        self.verdict_row("reviewed", "approve")
        self.assertNotIn("hook allowed", self.text())

    def test_the_allowed_commands_are_counted_by_action(self):
        for number in range(3):
            self.allow(number)
        self.allow(10, rule="safe-git-remove")
        self.assertEqual(self.COUNT + "4 (commit 3, remove 1)", self.line(self.text(), self.COUNT))

    def test_the_actions_are_ranked_by_count_then_name(self):
        self.allow(1, rule="safe-git-remove")
        self.allow(2, rule="safe-git-commit")
        self.assertEqual(self.COUNT + "2 (commit 1, remove 1)", self.line(self.text(), self.COUNT))

    def test_the_allowed_commands_are_counted_by_day_oldest_first(self):
        for number, day in enumerate(("2026-11-11", "2026-11-10", "2026-11-11", "2026-11-12", "2026-11-11")):
            self.allow(number, day=day)
        self.assertEqual(self.DAYS + "2026-11-10 1, 2026-11-11 3, 2026-11-12 1", self.line(self.text(), self.DAYS))

    def test_the_ids_to_sample_are_those_of_the_collected_rows_newest_first(self):
        first, second, third = (self.allow(number) for number in range(3))
        sample = self.line(self.text(), self.SAMPLE)
        self.assertEqual(self.SAMPLE + ", ".join([third, second, first]) + "; unlabelled 3; with no collected row 0", sample)

    def test_at_most_ten_ids_are_listed_and_the_rest_are_counted(self):
        ids = [self.allow(number) for number in range(13)]
        sample = self.line(self.text(), self.SAMPLE)
        self.assertEqual(10, sum(1 for ident in ids if ident in sample))
        for ident in ids[3:]:
            self.assertIn(ident, sample)
        for ident in ids[:3]:
            self.assertNotIn(ident, sample)
        self.assertIn("and 3 more", sample)

    def test_an_allowed_command_is_not_a_labelled_one(self):
        for number in range(5):
            self.allow(number)
        out = self.text()
        self.assertIn("commit: labelled 0 ", out)
        self.assertIn("not enough labels", self.line(out, "cutover:"))

    def test_an_allowed_command_the_owner_labelled_is_labelled_as_any_other_and_is_no_longer_unlabelled(self):
        self.allow(1, label="right")
        self.allow(2)
        out = self.text()
        self.assertIn("commit: labelled 1 (right 1, wrong 0)", out)
        self.assertIn("; unlabelled 1;", self.line(out, self.SAMPLE))

    def test_a_skipped_allowed_command_is_not_unlabelled(self):
        self.allow(1, label="skip")
        self.assertIn("; unlabelled 0;", self.line(self.text(), self.SAMPLE))

    def test_an_allowed_command_with_no_collected_row_is_counted_and_said_so(self):
        self.allow(1)
        self.allow(2, collect=False)
        out = self.text()
        self.assertEqual(self.COUNT + "2 (commit 2)", self.line(out, self.COUNT))
        self.assertTrue(self.line(out, self.SAMPLE).endswith("; with no collected row 1"))

    def test_a_command_allowed_twice_is_counted_twice_and_its_row_is_listed_once(self):
        ident = self.allow(1)
        row = {"ts": "2026-11-11T01:02:03Z", "command_sha256": "%064x" % 1001, "outcome": "reviewed", "verdict": "approve",
               "failed_checks": [], "reason": MARK, "reviewed": True, "no_review_reason": None, "answer": "allow",
               "rule": "safe-git-commit"}
        self.store.append("verdicts.jsonl", row, self.home)
        out = self.text()
        self.assertEqual(self.COUNT + "2 (commit 2)", self.line(out, self.COUNT))
        self.assertEqual(1, self.line(out, self.SAMPLE).count(ident))

    def test_a_verdict_row_without_a_rule_takes_its_action_from_the_collected_row_and_else_is_unknown(self):
        self.allow(1, rule="safe-git-remove", with_rule=False)
        self.allow(2, collect=False, with_rule=False)
        self.assertEqual(self.COUNT + "2 (remove 1, unknown 1)", self.line(self.text(), self.COUNT))

    def test_a_row_that_was_not_an_allow_is_never_counted_as_one(self):
        self.labelled("safe-git-commit", 2)
        self.verdict_row("reviewed", "approve")
        self.verdict_row("reviewed", "decline", ["head_matches"], digest="b" * 64)
        self.verdict_row("timeout")
        self.assertNotIn("hook allowed", self.text())

    def test_a_malformed_answer_is_an_unreadable_line_and_never_an_allow(self):
        self.allow(1)
        directory = self.store.data_dir(self.home)
        good = {"ts": "2026-11-10T01:02:03Z", "command_sha256": "%064x" % 7, "outcome": "reviewed", "verdict": "approve",
                "failed_checks": [], "reason": None, "reviewed": True, "no_review_reason": None}
        bad_rows = [dict(good, answer="deny"), dict(good, answer=True), dict(good, answer=["allow"]), dict(good, answer="ALLOW"),
                    dict(good, answer="allow", verdict="decline", failed_checks=["head_matches"]),
                    dict(good, answer="allow", outcome="timeout", reviewed=False, verdict=None, no_review_reason="timeout")]
        with open(os.path.join(directory, "verdicts.jsonl"), "ab") as handle:
            for row in bad_rows:
                handle.write((json.dumps(row) + "\n").encode("ascii"))
        out = self.text()
        self.assertEqual(self.COUNT + "1 (commit 1)", self.line(out, self.COUNT))
        self.assertIn("verdicts %d" % len(bad_rows), self.line(out, "unreadable lines:"))

    def test_the_function_itself_counts_only_the_answer_allow(self):
        """The store already refuses any other answer; the function does not rely on it."""
        good = {"ts": "2026-11-10T01:02:03Z", "command_sha256": "%064x" % 7, "outcome": "reviewed", "verdict": "approve",
                "failed_checks": [], "reason": None, "reviewed": True, "no_review_reason": None}
        for answer in ("deny", True, 1, "ALLOW", ["allow"]):
            self.assertEqual([], self.report.allowed_lines([dict(good, answer=answer)], [], []), answer)
        self.assertEqual(3, len(self.report.allowed_lines([dict(good, answer="allow")], [], [])))

    def test_only_the_collected_rows_of_the_allowed_commands_are_sampled(self):
        wanted = self.allow(1)
        self.command("safe-git-commit", "approve", (), None)  # collected under the shared test hash, never allowed
        self.command("safe-git-remove", "decline", ["head_matches"], "wrong")
        sample = self.line(self.text(), self.SAMPLE)
        self.assertEqual(self.SAMPLE + wanted + "; unlabelled 1; with no collected row 0", sample)

    def test_a_collected_row_written_twice_is_listed_once(self):
        ident = self.allow(1)
        directory = self.store.data_dir(self.home)
        with open(os.path.join(directory, "collected.jsonl"), "rb") as handle:
            line = handle.read().splitlines()[-1]
        with open(os.path.join(directory, "collected.jsonl"), "ab") as handle:
            handle.write(line + b"\n")
        sample = self.line(self.text(), self.SAMPLE)
        self.assertEqual(1, sample.count(ident))
        self.assertEqual(self.SAMPLE + ident + "; unlabelled 1; with no collected row 0", sample)

    SIDE = ("hook allowed", "waiting:", "prompted:", "not reviewed:", "reviewed but not collectable", "  by failed check (a row", "cutover:")

    def test_unlabelled_allowed_commands_move_no_labelled_count_and_only_the_waiting_ones(self):
        """An allowed command is counted as waiting like any collected row, and as prompted and reviewed; nothing about the labels, the
        rates, the test set or the met-or-not reading of the cutover line changes until the owner labels it."""
        self.labelled("safe-git-commit", 10)
        self.labelled("safe-git-remove", 10)
        self.full_test_set()
        before = self.text()
        for number in range(4):
            self.allow(number)
        after = self.text()
        keep = [line for line in after.splitlines() if not line.startswith(self.SIDE)]
        self.assertEqual([line for line in before.splitlines() if not line.startswith(self.SIDE)], keep)
        self.assertEqual(self.line(before, "cutover:"), self.line(after, "cutover:").split("; still waiting")[0])
        self.assertIn("waiting: unlabelled 4,", self.line(after, "waiting:"))

    def test_a_labelled_allowed_command_enters_the_labelled_counts_like_any_other(self):
        self.labelled("safe-git-commit", 2)
        before = self.line(self.text(), "commit:")
        self.allow(1, label="right")
        self.allow(2, label="wrong")
        after = self.line(self.text(), "commit:")
        self.assertIn("labelled 2 (right 2, wrong 0)", before)
        self.assertIn("labelled 4 (right 3, wrong 1)", after)

    def test_the_lines_print_no_hash_command_fact_reason_or_note_and_only_printable_ascii(self):
        self.allow(1)
        self.allow(2, collect=False)
        out = self.text()
        self.assertNotIn(MARK, out)
        self.assertNotIn("wb run", out)
        self.assertNotIn("%064x" % 1001, out)
        for char in out:
            self.assertTrue(char == "\n" or " " <= char <= "~", repr(char))

    def test_the_lines_come_before_the_cutover_line_and_after_the_unreadable_line(self):
        self.allow(1)
        lines = self.text().splitlines()
        positions = [next(at for at, line in enumerate(lines) if line.startswith(start))
                     for start in ("unreadable lines:", self.COUNT, self.DAYS, self.SAMPLE, "cutover:")]
        self.assertEqual(sorted(positions), positions)


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

    def test_the_only_facts_of_a_collected_row_it_reads_are_confirm_and_handle_each_in_one_function(self):
        """Plan `2026-11-05-shadow-report-counts-previews-apart`: the report reads one boolean of the facts, in `is_preview`. Plan
        `2026-11-07-label-declined-secrets`, increment A: and one more, `handle`, in `is_handle`. No other part of a collected row's
        facts, command or reason."""
        with open(REPORT, "rb") as handle:
            tree = ast.parse(handle.read())
        where = {}
        for function in [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]:
            for node in ast.walk(function):
                if isinstance(node, ast.Constant) and node.value in ("facts", "confirm", "handle", "command", "reason", "diff", "paths"):
                    where.setdefault(node.value, set()).add(function.name)
        self.assertEqual({"is_preview"}, where.get("confirm"))
        self.assertEqual({"is_handle"}, where.get("handle"))
        self.assertEqual({"is_preview", "is_handle"}, where.get("facts"))
        for name in ("command", "reason", "diff", "paths"):
            self.assertNotIn(name, where, name)


if __name__ == "__main__":
    unittest.main()
