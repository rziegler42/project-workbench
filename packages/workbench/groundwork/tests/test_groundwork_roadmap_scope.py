"""How work is placed in roadmaps: the scope of a roadmap, the test for an existing or a new one, and the size question.

Plan `2026-11-06-roadmap-scope-text`, increment A, which carries out the accepted decision
`2026-11-06-roadmaps-are-scoped-by-finish-line`. The sentences are pinned in the `draft-roadmap` skill, in the shipped
roadmaps README and in the groundwork spec, so a later edit of any one of them fails here."""

import os
import unittest

MODULE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(MODULE)))
SKILL = os.path.join(MODULE, "harness", "neutral", "skills", "draft-roadmap", "SKILL.md")
README = os.path.join(MODULE, "files", "docs", "roadmaps", "README.md")
SPEC = os.path.join(ROOT, "docs", "specs", "groundwork.md")

# Said in all three places.
EVERYWHERE = (
    "A scope is a body of work with its own finish line",
    "shares the finish line of the roadmap it would join",
    "accepts or renames it",
    "to the nearest roadmap because it is nearest",
    "bounded new work that advances the finish line of its roadmap",
    "too small to need roadmap direction",
    "`Candidate: none`",
    "about 15 candidates",
    "has outgrown its scope",
    "a question, not a limit",
)
# Said in the skill, which an agent follows step by step.
SKILL_ONLY = (
    "propose a new roadmap to the owner, naming its scope and its finish line",
    "or no roadmap fits",
    "write nothing until the owner accepts or renames it",
    "ask the owner whether it has outgrown its scope before adding another",
    "the owner may say to go on",
    "For a new roadmap that the owner has accepted, name the file",
)


def text(path):
    with open(path, encoding="utf-8") as handle:
        return " ".join(handle.read().split())


class RoadmapScope(unittest.TestCase):
    def test_each_place_says_what_a_scope_is_and_how_new_work_is_placed(self):
        for path in (SKILL, README, SPEC):
            found = text(path)
            for phrase in EVERYWHERE:
                self.assertIn(phrase, found, (os.path.basename(path), phrase))

    def test_a_new_roadmap_is_proposed_to_the_owner_in_each_place(self):
        self.assertIn("a new roadmap is proposed to the owner", text(README))
        self.assertIn("a new roadmap is proposed to the owner", text(SPEC))

    def test_the_skill_proposes_a_new_roadmap_and_waits_for_the_owner(self):
        found = text(SKILL)
        for phrase in SKILL_ONLY:
            self.assertIn(phrase, found)

    def test_the_skill_no_longer_adds_to_a_roadmap_by_default(self):
        self.assertNotIn("add to it instead of writing a second", text(SKILL))

    def test_a_roadmap_has_a_finish_line_per_scope_where_retiring_is_described(self):
        for path in (README, SPEC):
            self.assertIn("each with its own finish line", text(path), os.path.basename(path))

    def test_no_text_says_there_is_exactly_one_roadmap(self):
        for path in (SKILL, README, SPEC):
            found = text(path).lower()
            for phrase in ("only roadmap", "the one roadmap", "single roadmap", "exactly one roadmap",
                           "one roadmap in total", "used alternately", "instead of writing a second"):
                self.assertNotIn(phrase, found, (os.path.basename(path), phrase))


if __name__ == "__main__":
    unittest.main()
