"""How work is placed in roadmaps, and who writes a change to one.

Plan `2026-11-06-roadmap-scope-text`, increment A, carries out the accepted decision `2026-11-06-roadmaps-are-scoped-by-finish-line`:
the scope of a roadmap, the test for an existing or a new one, and the size question.

Plan `2026-11-06-roadmap-edits-are-direction-changes`, increment B, states who writes a change: any change to a roadmap other
than correcting a typo is the `change-direction` checkpoint, which always stops for the owner; the agent shows the owner the
candidate it would add and writes it only on the owner's word, and the owner's request to add a candidate is that word. The
sentences are pinned in the `draft-roadmap` skill, in the shipped roadmaps README, in the policy block and in the groundwork
spec, so a later edit of any one of them fails here, and one test walks the whole shipped set for the sentences that were
removed."""

import os
import unittest

MODULE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(MODULE)))
SKILL = os.path.join(MODULE, "harness", "neutral", "skills", "draft-roadmap", "SKILL.md")
README = os.path.join(MODULE, "files", "docs", "roadmaps", "README.md")
POLICY = os.path.join(MODULE, "files", "blocks", "policy.md")
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
# Who writes a change to a roadmap: said in the skill, the README, the policy block and the spec.
WHO_WRITES = (
    "any change to a roadmap other than correcting a typo",
    "adding, dropping or rewording a candidate",
    "changing a roadmap's purpose, scope or status",
    "creating, retiring or replacing a roadmap",
    "`change-direction` checkpoint",
    "always stops for the owner",
    "the owner the candidate",
    "only on the owner's word",
    "the owner's request to add a candidate is that word",
)
# Sentences that said an agent adds a candidate, or changes a roadmap, on its own.
REMOVED = (
    "If it does, add it there",
    "is added to it as a candidate",
)


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


class WhoWritesAChange(unittest.TestCase):
    def test_each_place_says_what_counts_and_that_the_owner_decides(self):
        for path in (SKILL, README, POLICY, SPEC):
            found = text(path).lower()
            for phrase in WHO_WRITES:
                self.assertIn(phrase, found, (os.path.basename(path), phrase))

    def test_the_skill_description_does_not_say_it_adds_a_candidate(self):
        head = text(SKILL).split("# Draft a roadmap")[0]
        self.assertIn("description:", head)
        self.assertNotIn("add a candidate", head)
        self.assertIn("propose a candidate", head)

    def test_step_one_shows_the_candidate_before_writing_it(self):
        step = text(SKILL).split(" 2. For a new roadmap")[0]
        self.assertIn("show the owner the candidate you would add", step)
        self.assertNotIn("add it there", step)

    def test_dropping_a_candidate_waits_for_the_owner(self):
        found = text(SKILL)
        self.assertIn("dropping a candidate is a change of direction and waits for the owner's word", found)

    def test_the_readme_update_in_place_carries_the_owners_word(self):
        found = text(README)
        self.assertIn("update it in place on the owner's word", found)
        self.assertNotIn("and update it in place;", found)

    def test_the_policy_block_names_the_checkpoint_beside_accept_decision(self):
        found = text(POLICY)
        self.assertIn("Accepting a decision is a checkpoint", found)
        self.assertIn("A change to what a spec says about direction", found)

    def test_a_typo_is_not_a_change(self):
        for path in (SKILL, README, POLICY, SPEC):
            self.assertIn("other than correcting a typo", text(path), os.path.basename(path))

    def test_the_spec_candidate_definition_does_not_let_investigation_add_or_drop_alone(self):
        found = text(SPEC)
        self.assertIn("reshuffle, add or drop candidates, each on the owner's word", found)

    def test_no_shipped_markdown_or_the_spec_says_an_agent_adds_a_candidate_on_its_own(self):
        files = shipped_markdown() + [SPEC]
        self.assertGreater(len(files), 70)
        for path in files:
            found = text(path)
            for phrase in REMOVED:
                self.assertNotIn(phrase, found, (os.path.relpath(path, ROOT), phrase))


if __name__ == "__main__":
    unittest.main()
