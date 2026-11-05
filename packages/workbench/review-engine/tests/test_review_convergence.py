"""`review-engine convergence`: whether the last review of a plan converged, read from the sealed state alone
(`docs/specs/review-engine.md`, "Convergence"). Plan `2026-10-23-delegated-approval`, increment B.

No test starts a bridge or a model. A round is a forged entry in a state sealed with the stored key, as the
other state tests do."""

import json
import os
import unittest

from support_review import (NAMESPACE, OTHER_PLAN, PLAN, SPEC, Review, decision_entry, key_of, profile_entry,
                            round_entry)
from workbench import approvalcmd

FIELDS = {"format", "kind", "converged", "document_sha256", "rounds_used", "bound", "bridge", "model", "review",
          "closed", "last_requested"}


class Convergence(Review):
    def converge(self, path=PLAN):
        return self.document("convergence", path)

    def sealed(self, rounds, decisions=(), path=PLAN, **changes):
        """A review of `path` whose state holds `rounds` and `decisions`, sealed with the stored key."""
        if not os.path.exists(self.path(self.state_rel("plan", path))):
            self.document("init", path)
        body = self.state("plan", path)
        body["rounds"] = list(rounds)
        body["decisions"] = list(decisions)
        body.update(changes)
        return self.forge(body, path=path)

    # --- the object ------------------------------------------------------------------------------

    def test_a_clean_last_round_converges_and_the_object_has_exactly_the_documented_fields(self):
        self.sealed([round_entry(1)])
        got = self.converge()
        self.assertEqual(FIELDS, set(got))
        self.assertEqual({"format": 2, "kind": "plan", "converged": True, "document_sha256": "%064x" % 1001,
                          "rounds_used": 1, "bound": 3, "bridge": "ask-codex", "model": None,
                          "review": key_of("plan", PLAN), "closed": False, "last_requested": None}, got)

    def test_the_object_is_one_line_within_the_bound_and_types_are_exact(self):
        self.sealed([round_entry(1, model="gpt-5.6-luna")])
        code, out, err = self.call("convergence", PLAN)
        self.assertEqual((0, ""), (code, err))
        self.assertLessEqual(len(out.encode("utf-8")), 8192)
        got = json.loads(out)
        self.assertIs(True, got["converged"])
        self.assertIs(False, got["closed"])
        self.assertEqual(("gpt-5.6-luna", 1, 3), (got["model"], got["rounds_used"], got["bound"]))
        self.assertIs(int, type(got["rounds_used"]))

    def test_it_reports_the_last_rounds_hash_bridge_model_and_the_rounds_used(self):
        first = round_entry(1, ("major",), document_sha256="a" * 64)
        second = round_entry(2, (), document_sha256="b" * 64, bridge="other-bridge", model="m-2")
        self.sealed([first, second], [decision_entry("R1-F1")])
        got = self.converge()
        self.assertEqual(("b" * 64, "other-bridge", "m-2", 2, True),
                         (got["document_sha256"], got["bridge"], got["model"], got["rounds_used"], got["converged"]))

    def test_a_long_model_name_is_cut_to_200_characters_and_a_missing_one_is_null(self):
        self.sealed([round_entry(1, model="m" * 300)])
        self.assertEqual("m" * 200, self.converge()["model"])
        self.sealed([round_entry(1, model=None)])
        self.assertIsNone(self.converge()["model"])

    # --- what was asked (plan `2026-11-04-review-profiles`, increment H) ----------------------------

    ASKED = {"model": "phi4:latest", "effort": "low", "options": {"server": "lab", "context": "8192"}}

    def test_a_round_since_profiles_reports_the_request_and_the_profile(self):
        self.sealed([profile_entry(1, profile="quick", bridge="ask-ollama", requested=dict(self.ASKED))])
        self.assertEqual({"bridge": "ask-ollama", "model": "phi4:latest", "effort": "low",
                          "options": {"server": "lab", "context": "8192"}, "profile": "quick"},
                         self.converge()["last_requested"])

    def test_what_was_not_asked_is_null_and_no_options_is_the_empty_object(self):
        self.sealed([profile_entry(1, profile="bare")])
        self.assertEqual({"bridge": "ask-codex", "model": None, "effort": None, "options": {}, "profile": "bare"},
                         self.converge()["last_requested"])

    def test_a_round_stored_before_profiles_reports_a_null_request_and_converges_as_before(self):
        self.sealed([round_entry(1, requested={"model": "gpt-x", "effort": "low"})])
        got = self.converge()
        self.assertIsNone(got["last_requested"])
        self.assertIs(True, got["converged"])
        self.assertEqual(2, got["format"])

    def test_the_request_is_that_of_the_last_round_only(self):
        newer = profile_entry(2, profile="deep", requested={"model": "m-2", "effort": "high", "options": {}})
        self.sealed([round_entry(1), newer])
        self.assertEqual("deep", self.converge()["last_requested"]["profile"])
        self.sealed([profile_entry(1, profile="quick"), round_entry(2)])
        self.assertIsNone(self.converge()["last_requested"])

    def test_the_request_is_the_model_asked_for_and_not_the_one_the_bridge_reported(self):
        self.sealed([profile_entry(1, requested={"model": "asked", "effort": None, "options": {}}, model="reported")])
        got = self.converge()
        self.assertEqual(("reported", "asked"), (got["model"], got["last_requested"]["model"]))

    def test_the_request_is_the_profile_as_it_ran_and_not_the_one_the_file_names_today(self):
        self.setting(bridge="ask-codex", model="changed-since", effort="high")
        self.sealed([profile_entry(1, profile="p", requested={"model": "was", "effort": "low", "options": {}})])
        self.assertEqual(("was", "low"), tuple(self.converge()["last_requested"][k] for k in ("model", "effort")))

    def test_converged_does_not_depend_on_the_request(self):
        for entry in (round_entry(1), profile_entry(1), profile_entry(1, ("major",), verdict="changes_needed",
                                                                        reading="changes_needed", mismatch=False)):
            self.sealed([entry])
            self.assertEqual("major" not in [f["severity"] for f in entry["findings"]], self.converge()["converged"])

    def test_the_installer_reads_what_the_engine_prints_in_both_shapes(self):
        for entry in (round_entry(1), profile_entry(1, profile="quick", requested=dict(self.ASKED), bridge="ask-ollama")):
            self.sealed([entry])
            code, out, err = self.call("convergence", PLAN)
            self.assertEqual((0, ""), (code, err))
            read = approvalcmd.parse_convergence(out.encode("utf-8"))
            self.assertEqual(entry["bridge"], read.bridge)
            if "profile" in entry:
                self.assertEqual(("ask-ollama", "phi4:latest", "low", self.ASKED["options"], "quick"),
                                 tuple(read.last_requested))
            else:
                self.assertIsNone(read.last_requested)

    def test_the_worst_case_report_fits_the_installers_cap(self):
        # every character of every value is one that the JSON text doubles, and the reported model is non-ASCII
        options = {("n" * 31 + str(n)): '"' * 64 + "\\" * 64 for n in range(8)}
        self.sealed([profile_entry(1, profile="p" * 32, bridge="b" * 64, model="\u00e9" * 300,
                                   requested={"model": '"' * 64 + "\\" * 64, "effort": "medium", "options": options})])
        code, out, err = self.call("convergence", PLAN)
        self.assertEqual((0, ""), (code, err))
        self.assertLessEqual(len(out.encode("utf-8")), approvalcmd.MAX_CONVERGENCE_REPORT)
        self.assertEqual(options, approvalcmd.parse_convergence(out.encode("utf-8")).last_requested.options)

    def test_a_forged_request_the_state_check_refuses_gives_no_report(self):
        for asked in ({"model": "a b", "effort": None, "options": {}}, {"model": None, "effort": "max", "options": {}},
                      {"model": None, "effort": None, "options": {"model": "x"}},
                      {"model": None, "effort": None, "options": {"a": "x y"}},
                      {"model": None, "effort": None, "options": {"o%d" % n: "v" for n in range(9)}},
                      {"model": None, "effort": None}):
            self.sealed([round_entry(1)])
            self.forge(dict(self.state(), rounds=[profile_entry(1, requested=asked)]))
            self.refused("convergence", PLAN, contains="convergence")

    # --- what converges --------------------------------------------------------------------------

    def test_a_blocker_or_major_finding_in_the_last_round_does_not_converge(self):
        for severity in ("blocker", "major"):
            with self.subTest(severity):
                self.sealed([round_entry(1, (severity,), verdict="changes_needed", reading="changes_needed",
                                         mismatch=False)])
                self.assertFalse(self.converge()["converged"])

    def test_a_decided_meaningful_finding_in_the_last_round_still_does_not_converge(self):
        self.sealed([round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed")],
                    [decision_entry("R1-F1", "applied")])
        self.assertFalse(self.converge()["converged"])
        self.sealed([round_entry(1, ("blocker",), verdict="changes_needed", reading="changes_needed")],
                    [decision_entry("R1-F1", "rejected", "not so")])
        self.assertFalse(self.converge()["converged"])

    def test_minor_and_nit_findings_do_not_stop_a_review_converging(self):
        self.sealed([round_entry(1, ("minor", "nit", "minor"))])
        self.assertTrue(self.converge()["converged"])

    def test_an_undecided_meaningful_finding_of_an_earlier_round_does_not_converge(self):
        self.sealed([round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed"),
                     round_entry(2)])
        self.assertFalse(self.converge()["converged"])

    def test_a_decision_on_each_earlier_meaningful_finding_lets_a_clean_last_round_converge(self):
        for choice in ("applied", "rejected"):
            with self.subTest(choice):
                self.sealed([round_entry(1, ("blocker", "major"), verdict="changes_needed", reading="changes_needed"),
                             round_entry(2)], [decision_entry("R1-F1", choice), decision_entry("R1-F2", choice)])
                self.assertTrue(self.converge()["converged"])

    def test_one_undecided_finding_among_decided_ones_does_not_converge(self):
        self.sealed([round_entry(1, ("blocker", "major"), verdict="changes_needed", reading="changes_needed"),
                     round_entry(2)], [decision_entry("R1-F1")])
        self.assertFalse(self.converge()["converged"])

    def test_a_disagreement_between_the_reviewer_and_the_engine_does_not_converge(self):
        self.sealed([round_entry(1, verdict="changes_needed", reading="no_meaningful_changes", mismatch=True)])
        self.assertFalse(self.converge()["converged"])
        self.sealed([round_entry(1, ("major",), verdict="no_meaningful_changes", reading="changes_needed",
                                 mismatch=True)])
        self.assertFalse(self.converge()["converged"])

    def test_a_meaningful_finding_stops_it_even_if_the_stored_verdict_and_reading_say_otherwise(self):
        # the engine never writes such a round; the answer follows the findings the state names, not only the words
        for severity in ("blocker", "major"):
            with self.subTest(severity):
                self.sealed([round_entry(1, (severity,), verdict="no_meaningful_changes",
                                         reading="no_meaningful_changes", mismatch=False)],
                            [decision_entry("R1-F1")])
                self.assertFalse(self.converge()["converged"])

    def test_the_last_round_decides_not_the_first(self):
        self.sealed([round_entry(1), round_entry(2, ("major",), verdict="changes_needed", reading="changes_needed")])
        self.assertFalse(self.converge()["converged"])
        self.sealed([round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed"), round_entry(2)],
                    [decision_entry("R1-F1")])
        self.assertTrue(self.converge()["converged"])

    def test_a_reading_that_says_changes_needed_does_not_converge_even_if_the_findings_are_not_meaningful(self):
        self.sealed([round_entry(1, verdict="changes_needed", reading="changes_needed", mismatch=False)])
        self.assertFalse(self.converge()["converged"])

    def test_the_bound_used_up_without_a_clean_last_round_does_not_converge(self):
        rounds = [round_entry(n, ("major",), verdict="changes_needed", reading="changes_needed") for n in (1, 2, 3)]
        self.sealed(rounds, [decision_entry("R1-F1"), decision_entry("R2-F1")])
        got = self.converge()
        self.assertEqual((False, 3, 3), (got["converged"], got["rounds_used"], got["bound"]))

    def test_the_bound_used_up_with_a_clean_last_round_converges(self):
        rounds = [round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed"),
                  round_entry(2, ("major",), verdict="changes_needed", reading="changes_needed"), round_entry(3)]
        self.sealed(rounds, [decision_entry("R1-F1"), decision_entry("R2-F1")])
        got = self.converge()
        self.assertEqual((True, 3, 3), (got["converged"], got["rounds_used"], got["bound"]))

    def test_more_rounds_than_the_bound_do_not_converge(self):
        self.sealed([round_entry(1), round_entry(2)], window={"first": 1, "bound": 1})
        got = self.converge()
        self.assertEqual((False, 2, 1), (got["converged"], got["rounds_used"], got["bound"]))

    def test_an_extended_bound_is_reported(self):
        self.sealed([round_entry(1)], window={"first": 1, "bound": 5})
        self.assertEqual(5, self.converge()["bound"])

    def test_the_rounds_of_an_earlier_window_are_not_pending_and_are_not_counted(self):
        first = round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed")
        self.sealed([first, round_entry(2)], window={"first": 2, "bound": 3})
        got = self.converge()
        self.assertEqual((True, 1), (got["converged"], got["rounds_used"]))

    def test_a_closed_review_is_answered_as_closed_not_refused(self):
        self.sealed([round_entry(1)], closed="2026-01-02T00:00:00Z")
        got = self.converge()
        self.assertEqual((True, True), (got["converged"], got["closed"]))
        self.sealed([round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed")],
                    closed="2026-01-02T00:00:00Z")
        got = self.converge()
        self.assertEqual((False, True), (got["converged"], got["closed"]))

    def test_each_plan_has_its_own_review(self):
        self.sealed([round_entry(1)])
        self.sealed([round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed")], path=OTHER_PLAN)
        self.assertTrue(self.converge(PLAN)["converged"])
        got = self.converge(OTHER_PLAN)
        self.assertEqual((False, key_of("plan", OTHER_PLAN)), (got["converged"], got["review"]))

    def test_it_follows_the_state_and_not_the_ledger(self):
        self.sealed([round_entry(1, ("major",), verdict="changes_needed", reading="changes_needed")])
        folder = self.review_dir("plan", PLAN)
        self.write(folder + "/ledger.md", "# Review\n- converged, nothing pending\n")
        self.assertFalse(self.converge()["converged"])

    # --- what it refuses -------------------------------------------------------------------------

    def test_it_refuses_a_document_that_is_not_a_plan(self):
        self.document("init", SPEC)
        self.refused("convergence", SPEC, contains="plan")
        self.refused("convergence", "docs/roadmaps/r.md", contains="plan")
        self.refused("convergence", "docs/decisions/2026-01-01-d.md", contains="plan")

    def test_it_refuses_a_document_that_does_not_exist_or_is_not_a_path_below_docs(self):
        self.refused("convergence", "docs/plans/2026-01-09-missing.md", contains="does not exist")
        self.refused("convergence", "README.md")
        self.refused("convergence", "../docs/plans/x.md")
        self.refused("convergence", "/etc/passwd")
        self.refused("convergence", "")

    def test_it_refuses_a_plan_with_no_review(self):
        self.refused("convergence", PLAN, contains="there is no review")

    def test_it_refuses_a_review_with_no_round(self):
        self.document("init", PLAN)
        self.refused("convergence", PLAN, contains="no round")

    def test_it_refuses_a_review_with_no_round_in_the_window(self):
        self.sealed([round_entry(1)], window={"first": 2, "bound": 3})
        self.refused("convergence", PLAN, contains="no round")

    def test_it_refuses_an_unsealed_state(self):
        self.sealed([round_entry(1)])
        body = self.state()
        body["rounds"][0]["findings"] = []
        body["rounds"][0]["bridge"] = "edited-bridge"
        self.write(self.state_rel("plan", PLAN), json.dumps(body))  # edited, so the seal no longer matches
        self.refused("convergence", PLAN, contains="unsealed")

    def test_it_refuses_a_state_sealed_with_another_key(self):
        self.sealed([round_entry(1)])
        self.forge(self.state(), key=b"k" * 32)
        self.refused("convergence", PLAN, contains="unsealed")

    def test_it_refuses_when_there_is_no_seal_key(self):
        self.sealed([round_entry(1)])
        os.remove(self.store_path("seal-key"))
        self.refused("convergence", PLAN, contains="unsealed")

    def test_it_refuses_a_rolled_back_state(self):
        self.sealed([round_entry(1)])
        self.set_mark(key_of("plan", PLAN), rounds=2, decisions=0, generation=0)
        self.refused("convergence", PLAN, contains="rolled back")

    def test_it_refuses_a_state_that_is_gone_after_it_was_sealed_here(self):
        self.sealed([round_entry(1)])
        self.set_mark(key_of("plan", PLAN), rounds=1, decisions=0, generation=1)
        os.remove(self.path(self.state_rel("plan", PLAN)))
        self.refused("convergence", PLAN, contains="rolled back")

    def test_it_refuses_a_state_that_cannot_be_read(self):
        self.document("init", PLAN)
        for text in ("", "not json", "[]", '{"format": 1}', json.dumps(dict(self.state(), rounds="many"))):
            with self.subTest(text[:20]):
                self.write(self.state_rel("plan", PLAN), text)
                self.refused("convergence", PLAN, contains="not usable")

    def test_it_refuses_a_state_of_another_document(self):
        self.document("init", PLAN)
        self.document("init", OTHER_PLAN)
        self.write(self.state_rel("plan", PLAN), self.read(self.state_rel("plan", OTHER_PLAN)).decode())
        self.refused("convergence", PLAN, contains="not usable")

    def test_it_refuses_a_state_with_a_forged_round(self):
        self.sealed([round_entry(1)])
        body = self.state()
        body["rounds"][0]["findings"] = [{"id": "R9-F9", "severity": "nit"}]
        self.forge(body)
        self.refused("convergence", PLAN, contains="not usable")

    def test_the_wrong_number_of_arguments_is_a_usage_error(self):
        for argv in (["convergence"], ["convergence", PLAN, "extra"], ["convergence", PLAN, "--apply"]):
            with self.subTest(argv):
                self.refused(*argv, contains="usage")

    # --- what it leaves alone --------------------------------------------------------------------

    def test_it_writes_nothing_in_the_project_or_the_store(self):
        self.sealed([round_entry(1), round_entry(2, ("major",), verdict="changes_needed", reading="changes_needed")])
        project, store = self.tree(self.root), self.tree(self.store)
        self.converge()
        self.assertEqual(([], []), (self.changed(project, self.tree(self.root)), self.changed(store, self.tree(self.store))))

    def test_a_refusal_writes_nothing_either(self):
        self.document("init", PLAN)
        project, store = self.tree(self.root), self.tree(self.store)
        for argv in (["convergence", PLAN], ["convergence", SPEC], ["convergence", "docs/plans/none.md"],
                     ["convergence"]):
            self.call(*argv)
        self.assertEqual(([], []), (self.changed(project, self.tree(self.root)), self.changed(store, self.tree(self.store))))

    def test_it_makes_no_review_and_no_key_where_there_is_none(self):
        self.refused("convergence", PLAN)
        self.assertFalse(os.path.exists(self.path(NAMESPACE)))
        self.assertFalse(os.path.exists(self.store_path("seal-key")))

    def test_it_runs_no_bridge(self):
        # there is no profile file and no bridge in this project: a round would be refused for that, convergence is not
        self.sealed([round_entry(1)])
        self.assertFalse(os.path.exists(os.path.join(self.store, "review-profiles.json")))
        self.assertTrue(self.converge()["converged"])

    def test_status_is_unchanged_by_the_new_argument(self):
        self.sealed([round_entry(1)])
        got = self.document("status", PLAN)
        self.assertNotIn("converged", got)
        self.assertEqual("ok", got["seal"])


if __name__ == "__main__":
    unittest.main()
