"""The ladder: which profile a round runs on, what it passes to the bridge and what it records (plan `2026-11-04-review-profiles`,
increment D; `docs/specs/review-profiles.md`, "The ladder"). The bridge call is replaced where a test needs the arguments, and the
real launcher and the real `ask-codex` bridge against a fake `codex` are used where a test needs the refusals of the hops."""

import unittest
import unittest.mock

import support_bridge
from support_bridge import Round, answer, failure, finding, reply, result
from support_review import NAMESPACE, PLAN, SPEC, key_of

DIR = "%s/%s" % (NAMESPACE, key_of("plan", PLAN))

PROFILES = {
    "quick": {"bridge": "ask-codex", "effort": "low"},
    "standard": {"bridge": "ask-codex", "effort": "medium"},
    "deep": {"bridge": "ask-codex", "effort": "high"},
}


def option(arguments, name):
    """The value that follows `name` in a list of arguments, or None."""
    return arguments[arguments.index(name) + 1] if name in arguments else None


class Ladder(Round):
    def ladders(self, profiles=None, **ladders):
        self.owner_file({"format": 1, "profiles": profiles or PROFILES, "ladders": ladders})

    def drive(self, *outcomes, kind="plan", document=PLAN):
        """Run one round for each of `outcomes` with the bridge call replaced; return the calls made as ``(bridge, arguments)``
        and the exit code of each round."""
        calls, codes, queue = [], [], list(outcomes)

        def fake(root, command, arguments=(), **kwargs):
            calls.append((command, list(arguments)))
            return queue.pop(0)

        with unittest.mock.patch.object(self.helper.call, "run_command", fake):
            for _ in outcomes:
                codes.append(self.call("review-" + kind, document)[0])
        return calls, codes

    def efforts(self, calls):
        return [option(arguments, "--effort") for _, arguments in calls]

    def ok(self):
        return result(answer())


class Rungs(Ladder):
    def test_round_n_of_a_window_runs_on_rung_n(self):
        self.ladders(plan=["quick", "standard", "deep"])
        calls, codes = self.drive(self.ok(), self.ok(), self.ok())
        self.assertEqual([0, 0, 0], codes)
        self.assertEqual(["low", "medium", "high"], self.efforts(calls))
        self.assertEqual(["quick", "standard", "deep"], [entry["profile"] for entry in self.state()["rounds"]])

    def test_the_last_rung_is_used_for_every_later_round(self):
        self.ladders(plan=["quick", "deep"])
        calls, _ = self.drive(self.ok(), self.ok(), self.ok())
        self.assertEqual(["low", "high", "high"], self.efforts(calls))

    def test_a_ladder_of_one_rung_serves_every_round(self):
        self.ladders(plan=["standard"])
        calls, _ = self.drive(self.ok(), self.ok())
        self.assertEqual(["medium", "medium"], self.efforts(calls))

    def test_a_kind_with_no_ladder_of_its_own_uses_default(self):
        self.ladders(plan=["quick"], default=["deep"])
        calls, _ = self.drive(self.ok(), kind="spec", document=SPEC)
        self.assertEqual(["high"], self.efforts(calls))
        self.assertEqual("deep", self.state("spec", SPEC)["rounds"][0]["profile"])

    def test_a_kind_with_a_ladder_of_its_own_does_not_use_default(self):
        self.ladders(plan=["quick"], default=["deep"])
        calls, _ = self.drive(self.ok())
        self.assertEqual(["low"], self.efforts(calls))

    def test_every_document_kind_is_served_by_its_own_name(self):
        self.ladders(plan=["quick"], spec=["standard"], roadmap=["deep"], adr=["quick"])
        for kind, document, effort in (("spec", SPEC, "medium"), ("roadmap", "docs/roadmaps/r.md", "high"),
                                       ("adr", "docs/decisions/2026-01-01-d.md", "low")):
            calls, _ = self.drive(self.ok(), kind=kind, document=document)
            self.assertEqual([effort], self.efforts(calls), kind)

    def test_a_document_kind_with_neither_a_ladder_nor_default_is_refused_naming_the_file(self):
        self.ladders(plan=["quick"])
        calls, codes = self.drive(kind="spec", document=SPEC)
        err = self.refused("review-spec", SPEC, contains="review-profiles.json")
        self.assertIn("no ladder", err)
        self.assertEqual([], self.calls())

    def test_the_ladder_of_the_other_engine_is_never_used_by_this_one(self):
        self.ladders(profiles=PROFILES, **{"action-review": ["deep"]})
        self.refused("review-plan", PLAN, contains="no ladder")


class Failures(Ladder):
    def test_a_bridge_error_spends_no_round_and_the_retry_uses_the_same_rung(self):
        self.ladders(plan=["quick", "standard", "deep"])
        calls, codes = self.drive(self.ok(), result(failure()), self.ok())
        self.assertEqual([0, 1, 0], codes)
        self.assertEqual(["low", "medium", "medium"], self.efforts(calls))
        self.assertEqual(["quick", "standard"], [entry["profile"] for entry in self.state()["rounds"]])

    def test_a_refusal_names_the_profile_that_failed(self):
        self.ladders(plan=["quick", "standard"])
        self.drive(self.ok())
        with unittest.mock.patch.object(self.helper.call, "run_command", lambda *a, **k: result(failure())):
            code, out, err = self.call("review-plan", PLAN)

        self.assertEqual((1, ""), (code, out))
        self.assertIn("profile standard", err)

    def test_the_first_round_after_a_reset_uses_the_first_rung(self):
        self.ladders(plan=["quick", "standard", "deep"])
        calls, _ = self.drive(self.ok(), self.ok())
        self.assertEqual(["low", "medium"], self.efforts(calls))
        self.document("reset", PLAN)
        calls, _ = self.drive(self.ok())
        self.assertEqual(["low"], self.efforts(calls))

    def test_an_extended_window_runs_the_fourth_and_fifth_rungs(self):
        self.ladders(plan=["quick", "standard", "deep", "standard", "quick"])
        calls, _ = self.drive(self.ok(), self.ok(), self.ok())
        self.document("extend", PLAN, "2")
        more, codes = self.drive(self.ok(), self.ok())
        self.assertEqual([0, 0], codes)
        self.assertEqual(["low", "medium", "high", "medium", "low"], self.efforts(calls + more))
        self.refused("review-plan", PLAN, contains="rounds in this window")


class Request(Ladder):
    def setUp(self):
        super().setUp()
        self.ladders(profiles={"local": {"bridge": "ask-codex", "model": "m1", "effort": "low",
                                         "options": {"zeta": "1", "alpha": "2"}}}, plan=["local"])

    def test_the_arguments_are_ours_then_the_model_the_effort_and_the_options_in_name_order(self):
        calls, _ = self.drive(self.ok())
        ((bridge, arguments),) = calls
        self.assertEqual("ask-codex", bridge)
        self.assertEqual(["ask", "--timeout", "600", "--schema", DIR + "/schema.json", "--model", "m1", "--effort", "low",
                          "--alpha", "2", "--zeta", "1"], arguments)

    def test_the_round_records_the_profile_and_the_request(self):
        self.drive(self.ok())
        (entry,) = self.state()["rounds"]
        self.assertEqual(("local", "ask-codex"), (entry["profile"], entry["bridge"]))
        self.assertEqual({"model": "m1", "effort": "low", "options": {"alpha": "2", "zeta": "1"}}, entry["requested"])

    def test_a_profile_with_nothing_but_a_bridge_passes_nothing_more(self):
        self.ladders(profiles={"bare": {"bridge": "ask-codex"}}, plan=["bare"])
        ((_, arguments),) = self.drive(self.ok())[0]
        self.assertEqual(["ask", "--timeout", "600", "--schema", DIR + "/schema.json"], arguments)

    def test_status_reads_the_request_as_the_same_until_the_profile_is_edited(self):
        self.drive(self.ok())
        self.assertEqual("same", self.document("status", PLAN)["request"])
        self.ladders(profiles={"local": {"bridge": "ask-codex", "model": "m2", "effort": "low",
                                         "options": {"zeta": "1", "alpha": "2"}}}, plan=["local"])
        self.assertEqual("changed", self.document("status", PLAN)["request"])


class Hops(Ladder):
    """The real launcher and the real bridge: what the profile asks of them is refused where the hop refuses it."""

    def test_an_option_the_bridge_does_not_accept_is_the_bridges_refusal_and_spends_no_round(self):
        self.setting(bridge="ask-codex", options={"server": "home"})
        err = self.refused("review-plan", PLAN, contains="profile p")
        self.assertEqual([], self.calls(), "the vendor program was started")
        self.assertFalse(self.state_exists())
        self.assertNotIn(self.home, err)

    def test_a_bridge_that_is_not_installed_is_refused_naming_the_profile(self):
        self.setting(bridge="ask-gemini")
        self.refused("review-plan", PLAN, contains="profile p")
        self.assertEqual([], self.calls())

    def test_the_project_file_does_not_choose_the_effort(self):
        self.setting(bridge="ask-codex", effort="low")
        self.write(".workbench/review.json", '{"format": 1, "bridge": "ask-codex", "effort": "high"}')
        self.round()
        (record,) = self.calls()
        self.assertIn('model_reasoning_effort="low"', record["argv"])
        self.assertNotIn('model_reasoning_effort="high"', record["argv"])

    def state_exists(self):
        import os
        return os.path.exists(self.path(DIR + "/state.json"))


if __name__ == "__main__":
    unittest.main()
