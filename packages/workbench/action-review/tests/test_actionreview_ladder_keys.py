"""The ladder keys of the readers of the owner's profile file agree (plan `2026-11-04-review-profiles`, increment F).

The kit reader refuses a ladder whose key the caller did not list, so two readers of one file that list different keys would accept the
file differently: a file that the review engine reads would be refused by the action-review engine, or the reverse. Each caller names
its own sets (the kit knows no kind of review), so this test is the one place that compares them: the review engine, the action-review
engine and the test-set runner. The installer's own set (`wb doctor`, increment J) is compared where it is built."""

import unittest

import test_tools_run_testset as runner_tests
from tests import support_helpers


class Drift(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = support_helpers.load("review-engine")
        cls.action = support_helpers.load("action-review")
        cls.runner = runner_tests.load()

    def test_the_three_readers_accept_the_same_ladder_keys(self):
        keys = set(self.engine.LADDER_KEYS)
        self.assertEqual(keys, set(self.action.LADDER_KEYS))
        self.assertEqual(keys, set(self.runner.LADDER_KEYS))

    def test_the_three_readers_hold_the_same_keys_to_one_rung(self):
        rungs = set(self.engine.SINGLE_RUNG)
        self.assertEqual(rungs, set(self.action.SINGLE_RUNG))
        self.assertEqual(rungs, set(self.runner.SINGLE_RUNG))
        self.assertEqual({"action-review"}, rungs)

    def test_the_four_kinds_of_document_the_default_and_action_review_are_all_there_is(self):
        self.assertEqual({"plan", "spec", "roadmap", "adr", "default", "action-review"}, set(self.engine.LADDER_KEYS))

    def test_no_key_is_listed_twice(self):
        for reader in (self.engine, self.action, self.runner):
            self.assertEqual(len(reader.LADDER_KEYS), len(set(reader.LADDER_KEYS)))
            self.assertTrue(set(reader.SINGLE_RUNG) <= set(reader.LADDER_KEYS))


if __name__ == "__main__":
    unittest.main()
