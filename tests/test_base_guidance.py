"""The section of the shipped base `AGENTS.md` that tells an agent which command forms the command gate accepts.

Plan `2026-11-06-gate-forms-in-the-base`, increment A. The tests read the real base, not a fixture.
"""

import unittest

from workbench import base

HEADING = "## Commands the gate accepts"
MARKER = "<!-- @slot: policy -->"
MAX_LINES = 24


def shipped():
    return base.load_base().files["AGENTS.md"].decode("utf-8")


def headings(text):
    return [line for line in text.split("\n") if line.startswith("## ")]


def section(text):
    lines = text.split("\n")
    start = lines.index(HEADING)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).rstrip("\n")


def bullets(body):
    """The bullets of a section, each joined onto one line."""
    found = []
    for line in body.split("\n"):
        if line.startswith("- "):
            found.append(line)
        elif found and line.startswith("  "):
            found[-1] += " " + line.strip()
    return found


class GateForms(unittest.TestCase):
    def setUp(self):
        self.text = shipped()

    def test_the_section_is_once_between_source_of_truth_and_policy(self):
        self.assertEqual(1, self.text.split("\n").count(HEADING))
        self.assertEqual(["## Working agreement", "## Source of truth", HEADING, "## Policy"], headings(self.text))

    def test_the_policy_marker_is_still_once(self):
        self.assertEqual(1, self.text.split("\n").count(MARKER))

    def test_the_section_is_short(self):
        self.assertLessEqual(len(section(self.text).split("\n")), MAX_LINES)

    def test_it_says_to_run_a_relaxed_command_as_one_simple_command(self):
        first = bullets(section(self.text))[0]
        self.assertIn("one simple command on its own", first)
        for word in ("pipe", "`&&`", "`;`", "redirect", "`cd` prefix", "variable", "`bash -c`", "`env`"):
            self.assertIn(word, first)

    def test_it_frees_only_the_closed_plain_read_form(self):
        body = section(self.text)
        self.assertIn("as data only in a plain read", body)
        for program in ("`cat`", "`diff`", "`grep`", "`head`", "`ls`", "`tail`", "`wc`"):
            self.assertIn(program, body)
        self.assertIn("Do not name it in any other command", body)
        self.assertIn("with the edit tools", body)

    def test_it_says_single_quotes_and_never_to_reword_the_owners_text(self):
        body = section(self.text)
        self.assertIn("in single quotes, never double quotes", body)
        self.assertIn("Never reword the owner's text to get past a refusal", body)

    def test_it_limits_the_retry_to_the_rules_that_name_a_form(self):
        body = section(self.text)
        last = bullets(body)[-1]
        self.assertIn("`names` and `gap`", last)
        self.assertIn("ends with the form to run instead", last)
        self.assertIn("Use that form once", last)
        self.assertIn("If it is refused again", last)
        self.assertIn("`size-limit`", last)
        self.assertIn("`dollar-quote-limit`", last)
        self.assertIn("stop and report it", last)

    def test_it_names_no_harness_and_no_module_option(self):
        body = section(self.text).lower()
        for word in ("claude", "codex", "--body", "mempalace", "known harness"):
            self.assertNotIn(word, body)


if __name__ == "__main__":
    unittest.main()
