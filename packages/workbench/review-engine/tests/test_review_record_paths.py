"""`review-engine record-paths`: the files of a review that a commit holds, read from the state and not from the
directory (`docs/specs/review-engine.md`, "The commands"). Plan `2026-11-07-review-record-paths`, increment A.

No test starts a bridge or a model. A round is a forged entry in a state sealed with the stored key, as the other state
tests do, and its file is written beside the state."""

import json
import os
import unittest

from support_review import OTHER_PLAN, PLAN, SPEC, Review, round_entry


class RecordPaths(Review):
    def folder(self, kind="plan", path=PLAN):
        return self.review_dir(kind, path)

    def with_rounds(self, count, path=PLAN, kind="plan"):
        """A review of `path` whose state names `count` rounds, with the three fixed files and a file for each round."""
        if not os.path.exists(self.path(self.state_rel(kind, path))):
            self.document("init", path)
        body = self.state(kind, path)
        body["rounds"] = [round_entry(n) for n in range(1, count + 1)]
        self.forge(body, kind=kind, path=path)
        folder = self.folder(kind, path)
        for name in ("ledger.md", "schema.json"):
            self.write(folder + "/" + name, "x\n")
        for n in range(1, count + 1):
            self.write(folder + "/round-%d.json" % n, "{}\n")
        return folder

    def listed(self, path=PLAN):
        return self.document("record-paths", path)

    def test_a_review_of_two_rounds_lists_its_files_in_a_fixed_order(self):
        folder = self.with_rounds(2)
        self.assertEqual({"document": PLAN, "paths": [folder + "/" + name for name in (
            "state.json", "ledger.md", "schema.json", "round-1.json", "round-2.json")]}, self.listed())

    def test_a_review_with_no_round_lists_the_files_that_init_made(self):
        self.document("init", PLAN)
        folder = self.folder()
        made = sorted(os.listdir(self.path(folder)))
        got = self.listed()["paths"]
        self.assertEqual(sorted(folder + "/" + name for name in made), sorted(got))
        self.assertEqual(folder + "/state.json", got[0])

    def test_a_plan_with_no_review_is_refused(self):
        self.refused("record-paths", PLAN, contains="no review")

    def test_a_round_file_the_state_does_not_name_is_not_listed(self):
        folder = self.with_rounds(1)
        self.write(folder + "/round-999.json", "{}\n")
        self.write(folder + "/round-2.json", "{}\n")
        self.write(folder + "/notes.txt", "x\n")
        got = self.listed()["paths"]
        self.assertEqual([folder + "/" + name for name in ("state.json", "ledger.md", "schema.json", "round-1.json")], got)

    def test_a_round_the_state_names_whose_file_is_missing_is_not_listed(self):
        folder = self.with_rounds(2)
        os.remove(self.path(folder + "/round-2.json"))
        self.assertNotIn(folder + "/round-2.json", self.listed()["paths"])
        self.assertIn(folder + "/round-1.json", self.listed()["paths"])

    def test_a_link_in_the_directory_is_neither_followed_nor_listed(self):
        folder = self.with_rounds(1)
        outside = os.path.join(self.base, "outside.md")
        with open(outside, "w") as handle:
            handle.write("x\n")
        os.remove(self.path(folder + "/ledger.md"))
        os.symlink(outside, self.path(folder + "/ledger.md"))
        got = self.listed()["paths"]
        self.assertNotIn(folder + "/ledger.md", got)
        self.assertIn(folder + "/state.json", got)

    def test_an_unsealed_review_still_lists_its_files(self):
        folder = self.with_rounds(1)
        body = self.state()
        self.forge(body, key=b"k" * 32)
        self.assertIn(folder + "/state.json", self.listed()["paths"])

    def test_a_closed_review_still_lists_its_files(self):
        folder = self.with_rounds(1)
        body = self.state()
        body["closed"] = "2026-01-02T00:00:00Z"
        self.forge(body)
        self.assertIn(folder + "/round-1.json", self.listed()["paths"])

    def test_a_state_that_cannot_be_used_is_refused(self):
        folder = self.with_rounds(1)
        self.write(folder + "/state.json", "not json")
        self.refused("record-paths", PLAN)

    def test_the_command_writes_nothing(self):
        self.with_rounds(2)
        before = self.tree(self.root)
        store = self.tree(self.store)
        self.listed()
        self.assertEqual([], self.changed(before, self.tree(self.root)))
        self.assertEqual([], self.changed(store, self.tree(self.store)))

    def test_it_lists_the_review_of_another_kind_and_of_another_document_alone(self):
        spec_folder = self.with_rounds(1, path=SPEC, kind="spec")
        plan_folder = self.with_rounds(2, path=OTHER_PLAN)
        self.assertTrue(all(p.startswith(spec_folder + "/") for p in self.listed(SPEC)["paths"]))
        self.assertTrue(all(p.startswith(plan_folder + "/") for p in self.listed(OTHER_PLAN)["paths"]))

    def test_the_arguments_must_be_exactly_one_document(self):
        self.with_rounds(1)
        self.refused("record-paths")
        self.refused("record-paths", PLAN, OTHER_PLAN)
        self.refused("record-paths", PLAN, "--digest", "a" * 32)

    def test_a_document_outside_the_kinds_is_refused(self):
        self.refused("record-paths", "README.md")

    def test_the_object_is_one_line_of_json(self):
        self.with_rounds(1)
        code, out, err = self.call("record-paths", PLAN)
        self.assertEqual((0, ""), (code, err))
        self.assertEqual(["document", "paths"], sorted(json.loads(out)))


if __name__ == "__main__":
    unittest.main()
