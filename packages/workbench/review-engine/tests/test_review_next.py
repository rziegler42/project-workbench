"""`status` prints the profile of the next round and the location class of its server (plan `2026-11-04-review-profiles`, increment E;
`docs/specs/review-profiles.md`, "Status"). The class is learned from the bridge's own `check` output, never from the endpoint file,
and where it cannot be told it reads `unknown`. The bridge call is replaced; no real bridge, server or network is used."""

import unittest
import unittest.mock

from support_bridge import result
from support_review import PLAN, SPEC
from test_review_ladder import Ladder
from workbench.wbkit import call

CHECK = (b"lab scheme=http location=owner-network authenticated=false default=yes\n"
         b"model lab/chat-a:latest kind=chat context=16384 window=8192 bytes_per_token=3\n"
         b"cloud scheme=https location=vendor-cloud authenticated=false default=no\n"
         b"here scheme=http location=this-machine authenticated=false default=no\n")

BARE = {"bridge": "ask-ollama", "model": "phi4:latest"}


class Next(Ladder):
    def status(self, outcome=None, document=PLAN):
        """``(status object, calls made to the bridge)`` with the bridge call replaced by one that answers `outcome`."""
        calls = []

        def fake(root, command, arguments=(), **kwargs):
            calls.append((command, list(arguments), kwargs.get("provides")))
            if isinstance(outcome, Exception):
                raise outcome
            return outcome if outcome is not None else result(raw=b"", code=1, stderr=b"refused: no such argument\n")

        with unittest.mock.patch.object(self.helper.call, "run_command", fake):
            return self.document("status", document), calls

    def start(self, document=PLAN):
        self.document("init", document)


class Which(Next):
    def test_the_next_round_names_the_first_rung_before_any_round(self):
        self.ladders(plan=["quick", "standard", "deep"])
        self.start()
        found, _ = self.status()
        self.assertEqual(("quick", "ask-codex"), (found["next"]["profile"], found["next"]["bridge"]))

    def test_it_follows_the_rounds_of_the_window_and_repeats_the_last_rung(self):
        self.ladders(plan=["quick", "deep"])
        self.start()
        names = []
        for _ in range(3):
            names.append(self.status()[0]["next"]["profile"])
            self.drive(self.ok())
        self.assertEqual(["quick", "deep", "deep"], names)

    def test_it_starts_again_at_the_first_rung_after_a_reset(self):
        self.ladders(plan=["quick", "deep"])
        self.drive(self.ok())
        self.assertEqual("deep", self.status()[0]["next"]["profile"])
        self.document("reset", PLAN)
        self.assertEqual("quick", self.status()[0]["next"]["profile"])

    def test_a_kind_with_no_ladder_of_its_own_uses_default(self):
        self.ladders(plan=["quick"], default=["deep"])
        self.start(SPEC)
        self.assertEqual("deep", self.status(document=SPEC)[0]["next"]["profile"])

    def test_there_is_no_next_round_when_the_window_is_used_up(self):
        self.ladders(plan=["quick"])
        self.drive(self.ok(), self.ok(), self.ok())
        self.assertIsNone(self.status()[0]["next"])

    def test_there_is_no_next_round_when_the_kind_has_no_ladder_and_status_does_not_refuse(self):
        self.ladders(plan=["quick"])
        self.start(SPEC)
        self.assertIsNone(self.status(document=SPEC)[0]["next"])

    def test_there_is_no_next_round_when_the_file_is_refused(self):
        self.ladders(plan=["quick"])
        self.start()
        self.owner_file("{")
        found, calls = self.status()
        self.assertEqual("none", found["request"])
        self.assertIsNone(found["next"])
        self.assertEqual([], calls)

    def test_a_refused_file_after_a_round_reads_unreadable_with_no_next_round(self):
        self.ladders(plan=["quick"])
        self.drive(self.ok())
        self.owner_file("{")
        found, _ = self.status()
        self.assertEqual("unreadable", found["request"])
        self.assertIsNone(found["next"])


class Location(Next):
    def location(self, profile, outcome):
        self.ladders(profiles={"p": profile}, plan=["p"])
        if not getattr(self, "started", False):
            self.start()
            self.started = True
        found, calls = self.status(outcome)
        return found["next"]["location"], calls

    def test_the_class_of_the_named_server_is_read_from_the_bridges_check(self):
        for server, expected in (("lab", "owner-network"), ("cloud", "vendor-cloud"), ("here", "this-machine")):
            profile = {"bridge": "ask-ollama", "options": {"server": server}}
            got, calls = self.location(profile, result(raw=CHECK, code=0))
            self.assertEqual(expected, got, server)
            self.assertEqual([("ask-ollama", ["check"], "model-bridge")], calls)

    def test_a_profile_with_no_server_uses_the_default_record(self):
        got, _ = self.location(BARE, result(raw=CHECK, code=0))
        self.assertEqual("owner-network", got)

    def test_a_server_the_check_does_not_list_is_unknown(self):
        got, _ = self.location({"bridge": "ask-ollama", "options": {"server": "nowhere"}}, result(raw=CHECK, code=0))
        self.assertEqual("unknown", got)

    def test_a_class_outside_the_three_is_unknown(self):
        for text in (b"lab scheme=http location=the-moon authenticated=false default=yes\n",
                     b"lab scheme=http location= authenticated=false default=yes\n",
                     b"lab scheme=http location=owner-network;rm authenticated=false default=yes\n",
                     b"lab scheme=http authenticated=false default=yes\n",
                     b"lab scheme=http location=owner-network location=vendor-cloud default=yes\n"):
            self.assertEqual("unknown", self.location(BARE, result(raw=text, code=0))[0], text)

    def test_a_name_that_only_begins_like_the_server_does_not_match(self):
        text = (b"labx scheme=http location=vendor-cloud authenticated=false default=no\n"
                b"lab scheme=http location=this-machine authenticated=false default=no\n")
        self.assertEqual("this-machine", self.location({"bridge": "ask-ollama", "options": {"server": "lab"}},
                                                       result(raw=text, code=0))[0])
        self.assertEqual("unknown", self.location({"bridge": "ask-ollama", "options": {"server": "la"}},
                                                  result(raw=text, code=0))[0])

    def test_every_way_the_check_can_fail_reads_unknown(self):
        for outcome in (result(raw=b"", code=1, stderr=b"refused: not an argument\n"),
                        result(raw=CHECK, code=1),
                        result(raw=CHECK, code=0, over=True),
                        result(raw=CHECK, code=0, timed_out=True),
                        result(raw=b"\xff\xfe", code=0),
                        result(raw=b"no endpoints\n", code=0),
                        call.CallError("the launcher could not be started")):
            self.assertEqual("unknown", self.location(BARE, outcome)[0], outcome)

    def test_a_bridge_with_no_endpoints_gets_one_call_and_no_class_is_guessed(self):
        got, calls = self.location({"bridge": "ask-codex"}, None)
        self.assertEqual("unknown", got)
        self.assertEqual(1, len(calls))

    def test_status_writes_nothing(self):
        self.ladders(profiles={"p": BARE}, plan=["p"])
        self.start()
        before = self.snapshot()
        self.status(result(raw=CHECK, code=0))
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
