"""When a plan names a roadmap candidate and when it has none, and who writes a roadmap candidate.

Plan `2026-11-06-roadmap-scope-text`, increment B, carries out the accepted decision
`2026-11-06-roadmaps-are-scoped-by-finish-line`: when a plan names a candidate and when it has none.

Plan `2026-11-06-roadmap-edits-are-direction-changes`, increment C, says that out-of-scope work is deferred or proposed to the
owner as a roadmap candidate and never recorded in a roadmap by the agent alone, that a change to a roadmap other than correcting
a typo is the `change-direction` checkpoint, and that work starts from a candidate or from work too small to need one. The
sentences are pinned in the shipped plans README, in the `draft-plan` skill, in the policy block and in the code-work spec, so a
later edit of any one of them fails here, and one test walks the whole shipped set for the sentence that was removed."""

import os
import unittest

MODULE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(MODULE)))
README = os.path.join(MODULE, "files", "docs", "plans", "README.md")
SKILL = os.path.join(MODULE, "harness", "neutral", "skills", "draft-plan", "SKILL.md")
POLICY = os.path.join(MODULE, "files", "blocks", "policy.md")
SPEC = os.path.join(ROOT, "docs", "specs", "code-work.md")

EVERYWHERE = (
    "bounded new work that advances the finish line of a roadmap",
    "too small to need roadmap direction",
    "a correction that follows from a finding",
    "one-line reason",
    "<roadmap>#<id>",
)
# Said in the plans README and in the spec, where findings are classified and the checkpoints are listed.
OUT_OF_SCOPE = "record out-of-scope work as deferred, or propose it to the owner as a roadmap candidate"
CHECKPOINT = "any change to a roadmap other than correcting a typo, such as adding a candidate"
REMOVED = ("or in a roadmap",)


def text(path):
    with open(path, encoding="utf-8") as handle:
        return " ".join(handle.read().split())


def shipped_markdown():
    """Every markdown file the base and the modules ship, outside the tests directories."""
    found = []
    for top in ("base", "packages"):
        for directory, names, files in os.walk(os.path.join(ROOT, top)):
            names[:] = [name for name in names if name != "tests"]
            found.extend(os.path.join(directory, name) for name in files if name.endswith(".md"))
    return sorted(found)


class CandidateText(unittest.TestCase):
    def test_each_place_says_when_a_plan_names_a_candidate_and_when_it_has_none(self):
        for path in (README, SKILL, SPEC):
            found = text(path)
            for phrase in EVERYWHERE:
                self.assertIn(phrase, found, (os.path.basename(path), phrase))

    def test_each_place_spells_the_no_candidate_form_with_its_reason(self):
        self.assertIn("`Candidate: none` with a one-line reason", text(README))
        self.assertIn("`none` followed by a one-line reason", text(SKILL))
        self.assertIn("`Candidate: none` followed by a one-line reason", text(SPEC))

    def test_each_place_still_asks_for_exactly_one_candidate_line(self):
        self.assertIn("Exactly one.", text(README))
        self.assertIn("exactly one `Candidate:` line", text(SKILL))
        self.assertIn("has exactly one", text(SPEC))

    def test_the_skill_reads_the_roadmap_only_for_a_named_candidate(self):
        found = text(SKILL)
        self.assertIn("If the plan names a candidate, read the roadmap that holds it", found)
        self.assertIn("for a named candidate", found)
        self.assertNotIn("the roadmap that holds the candidate and the specs the work touches", found)

    def test_the_skill_keeps_the_search_that_makes_a_candidate_id_exist(self):
        self.assertIn("Search the roadmap so the candidate ID exists, for a named candidate", text(SKILL))

    def test_the_spec_purpose_and_lifecycle_allow_a_plan_with_no_candidate(self):
        found = text(SPEC)
        purpose = found.split("## Purpose and scope", 1)[1].split("Non-goals:", 1)[0]
        lifecycle = found.split("## Lifecycle", 1)[1].split("## Plans", 1)[0]
        self.assertIn("too small to need roadmap direction", purpose)
        self.assertIn("too small to need roadmap direction", lifecycle)
        self.assertIn("`Candidate: none`", lifecycle)


class WhoWritesACandidate(unittest.TestCase):
    def test_out_of_scope_work_is_deferred_or_proposed_to_the_owner(self):
        for path in (README, SPEC):
            self.assertIn(OUT_OF_SCOPE, text(path), os.path.basename(path))

    def test_the_checkpoint_list_says_what_a_roadmap_change_is(self):
        for path in (README, SPEC):
            found = text(path)
            self.assertIn(CHECKPOINT, found, os.path.basename(path))
            self.assertIn("shows the owner the candidate", found, os.path.basename(path))
            self.assertIn("on the owner's word", found, os.path.basename(path))
            self.assertIn("it always stops", found, os.path.basename(path))

    def test_the_readme_opening_names_both_ways_work_starts(self):
        self.assertIn("It is how a roadmap candidate, or work too small to need one, becomes a verified", text(README))

    def test_the_policy_block_names_both_ways_work_starts(self):
        found = text(POLICY)
        self.assertIn("Work moves from a roadmap candidate, or from work too small to need roadmap direction, to a plan", found)
        self.assertNotIn("Work moves from a roadmap candidate to a plan", found)

    def test_no_shipped_markdown_or_the_spec_tells_an_agent_to_record_work_in_a_roadmap(self):
        files = shipped_markdown() + [SPEC]
        self.assertGreater(len(files), 70)
        for path in files:
            found = text(path)
            for phrase in REMOVED:
                self.assertNotIn(phrase, found, (os.path.relpath(path, ROOT), phrase))


if __name__ == "__main__":
    unittest.main()
