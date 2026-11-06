"""When a plan names a roadmap candidate and when it has none.

Plan `2026-11-06-roadmap-scope-text`, increment B, which carries out the accepted decision
`2026-11-06-roadmaps-are-scoped-by-finish-line`. The sentences are pinned in the shipped plans README, in the
`draft-plan` skill and in the code-work spec, so a later edit of any one of them fails here."""

import os
import unittest

MODULE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(MODULE)))
README = os.path.join(MODULE, "files", "docs", "plans", "README.md")
SKILL = os.path.join(MODULE, "harness", "neutral", "skills", "draft-plan", "SKILL.md")
SPEC = os.path.join(ROOT, "docs", "specs", "code-work.md")

EVERYWHERE = (
    "bounded new work that advances the finish line of a roadmap",
    "too small to need roadmap direction",
    "a correction that follows from a finding",
    "one-line reason",
    "<roadmap>#<id>",
)


def text(path):
    with open(path, encoding="utf-8") as handle:
        return " ".join(handle.read().split())


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


if __name__ == "__main__":
    unittest.main()
