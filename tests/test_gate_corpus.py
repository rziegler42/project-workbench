"""The command gate's regression corpus: what ``judge`` does with each command of ``fixtures/gate_corpus.json`` today.

Plan ``2026-11-02-permission-system-consistency``, increment D (decision ``2026-11-02-command-gate-reads-gaps-and-data-positions``).
Each case records the level the key runs under (``ask`` unless it says ``none`` or ``block``), the result the gate gives now
(``today``, and for a refusal the rule that fired) and the result the decision wants (``intended``). A case whose two differ
names the increment that ends the difference (``fixed_by``); increment I changes ``today`` for those cases and for no others.
Increment I also puts the rule's name in each refusal, and then replaces ``classify``, which reads the refusal's prose today,
with that name; the ``rule`` fields change with it and nothing else does. The commands are sanitised: no real path, host or digest.

The relaxed keys are the ones the owner's settings relax at ``ask``: ``approve-plan``, ``wb release-approvals``, the command that
implements the checkpoint ``accept-decision`` and the review engine's five. At ``block`` no key is relaxed, so the gate is not
engaged and lets everything through: the barrier there is the command's own terminal test, which ``tests/test_approve_levels.py``
tests and which does not depend on the launcher spelling (``test_only_the_gate_and_the_rules_read_the_launcher_spellings``).
What this file does not test: the size limit and the NUL check of ``command_gate.run`` (they sit outside ``judge``;
``tests/test_command_gate.py`` has them)."""

import json
import os
import re
import unittest

from workbench import command_gate

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CORPUS = os.path.join(HERE, "fixtures", "gate_corpus.json")
PLAN = "2026-11-02-permission-system-consistency"
GROUPS = ("ordinary", "exact", "attempt", "false-positive", "block-side", "none-side", "boundary")
LEVELS = ("ask", "none", "block")
RULES = ("names", "in-order", "dollar-quote-limit", "other")


def load():
    with open(CORPUS, encoding="utf-8") as handle:
        return json.load(handle)


def classify(reason):
    """The short name of the rule that produced a refusal reason, or ``None`` for an allow."""
    if reason is None:
        return None
    if "holds the letters of" in reason:
        return "in-order"
    if "names " in reason:
        return "names"
    if "more than" in reason:
        return "dollar-quote-limit"
    return "other"


def judged(case, corpus):
    """The gate's reason for `case` under the level it runs under: no key is relaxed at ``block``."""
    keys = [] if case["level"] == "block" else corpus["relaxed_keys"]
    return command_gate.judge(case["command"], keys, corpus["store_bin"], {key: case["level"] for key in keys})


def mismatch(case, corpus):
    """``None`` when the gate gives the case's recorded result today, otherwise a sentence that says how it differs."""
    reason = judged(case, corpus)
    today = "pass" if reason is None else "refuse"
    if today != case["today"]:
        return "%s: the gate now says %s, the corpus records %s" % (case["id"], today, case["today"])
    if classify(reason) != case["rule"]:
        return "%s: the rule that fired is now %s, the corpus records %s" % (case["id"], classify(reason), case["rule"])
    return None


class Corpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load()
        cls.cases = cls.corpus["cases"]

    def group(self, name):
        return [case for case in self.cases if case["group"] == name]

    def test_the_gate_gives_each_recorded_result_today(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertIsNone(mismatch(case, self.corpus))

    def test_a_changed_result_is_noticed(self):
        """The check can fail: a case recorded the other way round, or under another rule, is reported."""
        case = dict(self.cases[0])
        case["today"] = "refuse" if case["today"] == "pass" else "pass"
        self.assertIn("the gate now says", mismatch(case, self.corpus))
        rule = dict(next(c for c in self.cases if c["today"] == "refuse"))
        rule["rule"] = "other"
        self.assertIn("the rule that fired", mismatch(rule, self.corpus))
        level = dict(next(c for c in self.cases if c["id"] == "bash-c-wrapper"))
        level["level"] = "block"
        self.assertIn("the gate now says pass", mismatch(level, self.corpus))

    def test_every_case_is_well_formed_and_the_ids_are_unique(self):
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertRegex(case["id"], r"[a-z0-9]+(-[a-z0-9]+)*\Z")
                self.assertIn(case["group"], GROUPS)
                self.assertIn(case["level"], LEVELS)
                self.assertIn(case["today"], ("pass", "refuse"))
                self.assertIn(case["intended"], ("pass", "refuse"))
                self.assertEqual(case["rule"] is None, case["today"] == "pass")
                if case["rule"] is not None:
                    self.assertIn(case["rule"], RULES)
                self.assertIsInstance(case["command"], str)
                self.assertTrue(case["command"])

    def test_a_case_that_differs_from_its_intent_names_the_increment_that_ends_it(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                differs = case["today"] != case["intended"]
                self.assertEqual(differs, "fixed_by" in case)
                if differs:
                    found = re.fullmatch(r"%s#([A-Z]+)" % re.escape(PLAN), case["fixed_by"])
                    self.assertIsNotNone(found, case["fixed_by"])

    def test_the_cases_that_differ_are_the_false_positives_of_the_decision(self):
        differing = sorted(case["id"] for case in self.cases if case["today"] != case["intended"])
        self.assertEqual(["cat-file-name-holds-the-word", "commit-subject-names-the-word", "grep-for-the-word",
                          "grep-globs-ls-heredoc", "grep-quoted-word-with-glob", "grep-two-globs",
                          "none-cat-file-name-holds-the-word", "none-grep-two-globs", "printf-link"], differing)
        for case in self.group("false-positive"):
            self.assertEqual(("refuse", "pass"), (case["today"], case["intended"]), case["id"])

    def test_every_attempt_is_refused_now_and_stays_refused(self):
        """No attempt is recorded as allowed, and none is meant to be allowed."""
        attempts = self.group("attempt")
        self.assertGreaterEqual(len(attempts), 30)
        for case in attempts:
            with self.subTest(case=case["id"]):
                self.assertEqual(("ask", "refuse", "refuse"), (case["level"], case["today"], case["intended"]))

    def test_the_forms_the_ask_rule_matches_pass(self):
        exact = self.group("exact")
        self.assertGreaterEqual(len(exact), 8)
        for case in exact:
            with self.subTest(case=case["id"]):
                self.assertEqual(("pass", "pass"), (case["today"], case["intended"]))

    def test_at_block_the_gate_is_not_engaged_and_the_command_is_the_barrier(self):
        """The same command that is refused at ask passes the gate at block: it is not a relaxed key, so the harness's `deny`
        and the command's own terminal test decide. The unlisted spelling is among them."""
        block = self.group("block-side")
        self.assertGreaterEqual(len(block), 3)
        ids = {case["id"] for case in block}
        self.assertIn("block-unlisted-spelling", ids)
        for case in block:
            with self.subTest(case=case["id"]):
                self.assertEqual(("block", "pass", "pass"), (case["level"], case["today"], case["intended"]))

    def test_the_block_side_does_not_depend_on_the_launcher_spelling(self):
        """The spelling list is read by the gate and the rules and by nothing that decides whether a command may run, so the
        command's own terminal test (``tests/test_approve_levels.py``) judges every spelling alike."""
        users = set()
        for name in sorted(os.listdir(os.path.join(REPO, "workbench"))):
            if name.endswith(".py"):
                with open(os.path.join(REPO, "workbench", name), encoding="utf-8") as handle:
                    if "SPELLINGS" in handle.read():
                        users.add(name)
        self.assertEqual({"command_gate.py", "rules.py"}, users)

    def test_the_terminal_test_the_block_side_relies_on_exists(self):
        from tests import test_approve_levels
        for name in ("test_at_block_the_remote_forms_are_refused", "test_at_block_the_owner_run_refusal_comes_before_the_identity"):
            self.assertTrue(hasattr(test_approve_levels.AtBlockAndNone, name), name)

    def test_at_none_the_same_forms_are_judged_and_the_message_does_not_name_an_ask_rule(self):
        none = self.group("none-side")
        self.assertGreaterEqual(len(none), 6)
        compound = next(case for case in none if case["id"] == "none-compound")
        reason = judged(compound, self.corpus)
        self.assertIn("cannot tell from a call", reason)
        self.assertNotIn("ask rule matches; run it as", reason)
        for case in none:
            self.assertEqual("none", case["level"])

    def test_the_edges_of_the_data_position_and_the_freed_run_form_stay_refused(self):
        boundary = self.group("boundary")
        self.assertGreaterEqual(len(boundary), 12)
        for case in boundary:
            with self.subTest(case=case["id"]):
                self.assertEqual(("ask", "refuse", "refuse"), (case["level"], case["today"], case["intended"]))
        self.assertIn("dollar-quote-limit", {case["rule"] for case in boundary})
        ids = {case["id"] for case in boundary}
        for wanted in ("boundary-git-log-grep-word", "boundary-sed-word", "boundary-find-exec-word", "boundary-env-word",
                       "boundary-tee-word", "boundary-sort-word", "boundary-grep-redirect", "boundary-grep-unquoted-glob",
                       "boundary-literal-run-names-another-key"):
            self.assertIn(wanted, ids)

    def test_the_corpus_covers_the_obfuscations_the_decision_names(self):
        """The forms the gap rule must keep catching: brace groups, bare parameters, a built launcher, a glob."""
        ids = {case["id"] for case in self.cases}
        for wanted in ("bare-digit-between-letters", "pinned-digit-before-dash", "unset-name-quoted-letters",
                       "brace-with-junk-alternative", "launcher-and-word-both-built", "unlisted-launcher-spelling",
                       "single-letter-glob", "padding-in-expansion", "escape-built-word"):
            self.assertIn(wanted, ids)

    def test_the_relaxed_keys_are_the_ones_of_the_owners_ask_settings(self):
        self.assertEqual(["approve-plan", "wb release-approvals", "wb run groundwork accept",
                          "wb run review-engine amend", "wb run review-engine archive", "wb run review-engine extend",
                          "wb run review-engine prune", "wb run review-engine reset"], self.corpus["relaxed_keys"])

    def test_a_command_is_not_a_secret_or_a_real_path(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertNotIn("/Users/", case["command"])
                self.assertNotRegex(case["command"], r"(?i)\b(token|password|secret|passwd)\s*[=:]")
                self.assertNotRegex(case["command"], r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


if __name__ == "__main__":
    unittest.main()
