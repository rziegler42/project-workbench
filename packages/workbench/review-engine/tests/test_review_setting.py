"""The owner's profile file `review-profiles.json` as the engine reads it: through the kit's strict reader, whole or refused whole,
a request and never an authorization (checklist item 4 of `docs/specs/review-engine.md`; `docs/specs/review-profiles.md`). The
project file `.workbench/review.json` is read by nothing. Plan `2026-11-04-review-profiles`, increment D."""

import json
import os
import unittest

import support_review

NAME = "review-profiles.json"
OLD = ".workbench/review.json"

ALL_KEYS = {"format": 1,
            "profiles": {"quick": {"bridge": "ask-codex", "effort": "low"}, "deep": {"bridge": "ask-codex", "effort": "high"}},
            "ladders": {"plan": ["quick", "deep"], "spec": ["quick"], "roadmap": ["quick"], "adr": ["quick"], "default": ["deep"],
                        "action-review": ["quick"]}}


class Profiles(support_review.Review):
    def read(self, body=None):
        if body is not None:
            self.owner_file(body)
        return self.helper.read_profiles()

    def refused(self, body=None, contains=NAME):
        with self.assertRaises(self.helper.Refused) as caught:
            self.read(body)
        self.assertIn(contains, str(caught.exception))
        return str(caught.exception)

    def test_the_profiles_and_the_ladders_are_read(self):
        got = self.read(ALL_KEYS)
        self.assertEqual(["deep", "quick"], sorted(got.profiles))
        self.assertEqual(("quick", "deep"), got.ladders["plan"])

    def test_the_engine_accepts_the_whole_file_including_the_ladder_of_the_other_engine(self):
        # one file serves both engines, so a ladder the review engine never runs must not make the file invalid
        self.read(ALL_KEYS)
        body = json.loads(json.dumps(ALL_KEYS))
        body["ladders"]["action-review"] = ["quick", "deep"]
        self.refused(body)

    def test_a_ladder_of_no_listed_kind_is_refused(self):
        body = json.loads(json.dumps(ALL_KEYS))
        body["ladders"]["review"] = ["quick"]
        self.refused(body)

    def test_a_file_with_no_ladders_is_read(self):
        self.assertEqual({}, self.read({"format": 1, "profiles": {"quick": {"bridge": "ask-codex"}}, "ladders": {}}).ladders)

    def test_a_missing_file_is_a_refusal_that_names_it_and_says_how_it_is_made_and_no_bridge_is_chosen(self):
        text = self.refused()
        self.assertIn("wb install", text)
        self.assertNotIn(self.home, text)

    def test_a_file_that_is_not_one_strict_object_is_a_refusal(self):
        for text in ("", "not json", "[]", "null", '{"format": 1, "profiles": {}', '{"format": 1, "format": 1}',
                     '{"format": 1.0, "profiles": {}, "ladders": {}}', b"\xff\xfe"):
            self.refused(text)

    def test_a_file_over_its_bound_is_a_refusal(self):
        self.refused(json.dumps(ALL_KEYS) + " " * 40000, contains="large")

    def test_every_invalid_profile_stops_the_file(self):
        body = json.loads(json.dumps(ALL_KEYS))
        body["profiles"]["deep"]["effort"] = "max"
        self.refused(body, contains="effort")

    def test_a_refusal_does_not_repeat_the_text_of_the_file(self):
        body = json.loads(json.dumps(ALL_KEYS))
        body["profiles"]["deep"]["model"] = "SECRETMARK is bad"
        self.assertNotIn("SECRETMARK", self.refused(body))

    def test_a_file_that_is_a_link_is_a_refusal(self):
        os.symlink(os.path.join(self.base, "elsewhere.json"), os.path.join(self.store, NAME))
        self.refused()

    def test_the_project_file_is_read_by_nothing(self):
        self.write(OLD, json.dumps({"format": 1, "bridge": "ask-codex"}))
        self.refused()
        self.owner_file(ALL_KEYS)
        self.write(OLD, "not even json")
        self.assertEqual(["deep", "quick"], sorted(self.helper.read_profiles().profiles))

    def test_the_engine_has_no_reader_of_the_project_file_left(self):
        self.assertFalse(hasattr(self.helper, "read_setting"))
        self.assertFalse(hasattr(self.helper, "SETTING"))

    def test_reading_the_file_changes_nothing(self):
        self.owner_file(ALL_KEYS)
        before = (self.tree(self.root), self.tree(self.store))
        self.helper.read_profiles()
        self.assertEqual(before, (self.tree(self.root), self.tree(self.store)))


if __name__ == "__main__":
    unittest.main()
