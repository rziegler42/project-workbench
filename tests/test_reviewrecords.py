"""The rule that says which added paths are the review engine's own records (`workbench/reviewrecords.py`).

The rule is narrow on purpose: a list that the owner types a digest over may summarise only what has exactly the engine's
spelling. The engine's spelling is read from its helper's source, so a change there fails here.
"""

import os
import re
import unittest

from workbench import reviewrecords
from workbench.acknowledgement import ADDED, CHANGED, REMOVED, Difference

HASH = "ab" * 8
SHA = "cd" * 32
FOLDER = ".workbench/workbench/review-engine"
HELPER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packages", "workbench",
                      "review-engine", "helper", "review-engine")


def added(path, current=SHA, baseline=None, reason="", kind=ADDED):
    return Difference(path, kind, baseline, current, reason)


def record(kind="plan", key=HASH, name="state.json"):
    return "%s/%s-%s/%s" % (FOLDER, kind, key, name)


class Accepts(unittest.TestCase):
    def test_every_kind_and_every_name(self):
        for kind in ("plan", "spec", "roadmap", "adr"):
            for name in ("state.json", "ledger.md", "schema.json", "round-1.json", "round-12.json", "round-9999.json"):
                found = reviewrecords.record_of(added(record(kind=kind, name=name)))
                self.assertEqual(found, (kind, "%s-%s" % (kind, HASH)), (kind, name))

    def test_the_directory_is_what_groups_files(self):
        one = reviewrecords.record_of(added(record(name="state.json")))
        two = reviewrecords.record_of(added(record(name="ledger.md")))
        self.assertEqual(one, two)
        other = reviewrecords.record_of(added(record(key="12" * 8)))
        self.assertNotEqual(one, other)


class Refuses(unittest.TestCase):
    def none(self, difference):
        self.assertIsNone(reviewrecords.record_of(difference), difference)

    def test_only_an_added_hashed_file_with_no_reason(self):
        path = record()
        self.none(added(path, kind=CHANGED, baseline=SHA))
        self.none(added(path, current=None, baseline=SHA, kind=REMOVED))
        self.none(added(path, baseline=SHA))
        self.none(added(path, current=None))
        self.none(added(path, reason="a link", current=None))
        self.none(added(path, reason="a directory", current=None))
        self.none(added(path, reason="not a regular file"))
        self.none(added(path, current="not a digest"))
        self.none(added(path, current=SHA.upper()))
        self.none(added(path, current=SHA[:-1]))
        self.none(added(path, current=SHA + "cd"))
        self.none(added(path, current=SHA + "\n"))
        self.none(added(path, current=" " + SHA))
        self.none(added(path, current=b"x"))

    def test_the_kind_alone_decides_that_it_is_an_addition(self):
        path = record()
        self.none(Difference(path, CHANGED, None, SHA, ""))
        self.none(Difference(path, REMOVED, None, SHA, ""))
        self.none(Difference(path, "other", None, SHA, ""))
        self.assertIsNotNone(reviewrecords.record_of(Difference(path, ADDED, None, SHA, "")))

    def test_a_path_that_is_not_text(self):
        for path in (None, 5, b"%s" % record().encode(), ["a"], ("a",)):
            self.none(Difference(path, ADDED, None, SHA, ""))

    def test_a_name_one_character_off(self):
        for path in (
            record(name="State.json"), record(name="state.json.bak"), record(name="state.json "),
            record(name="state.json\n"), record(name=" state.json"), record(name="state.jsonx"),
            record(name="ledger.MD"), record(name="schema.json.old"), record(name="round-0.json"),
            record(name="round-01.json"), record(name="round-10000.json"), record(name="round-.json"),
            record(name="round-1.JSON"), record(name="round-1.json\n"), record(name="round-１.json"),
            record(name="round-1.json/"), record(name=""), record(name="notes.md"), record(name="a" * 4000),
        ):
            self.none(added(path))

    def test_a_directory_name_one_character_off(self):
        for key in ("ab" * 7 + "a", "ab" * 8 + "a", "AB" * 8, "g" * 16, "ab" * 8 + "\n", "", "-" * 16, "１" * 16):
            self.none(added(record(key=key)))
        for kind in ("plans", "Plan", "PLAN", "decision", "docs", "", "plan-", "plan-plan"):
            self.none(added(record(kind=kind)))
        self.none(added("%s/plan%s/state.json" % (FOLDER, HASH)))
        self.none(added("%s/plan_%s/state.json" % (FOLDER, HASH)))

    def test_the_wrong_place(self):
        name = "plan-%s/state.json" % HASH
        for path in (
            "%s/%s" % (".workbench/workbench/review-engine2", name),
            "%s/%s" % (".workbench/workbench/Review-Engine", name),
            "%s/%s" % (".Workbench/workbench/review-engine", name),
            "%s/%s" % (".workbench/other/review-engine", name),
            "%s/%s" % ("workbench/review-engine", name),
            "%s/%s" % ("docs/plans", name),
            "%s/%s" % (FOLDER + "/extra", name),
            "%s/plan-%s/sub/state.json" % (FOLDER, HASH),
            "%s/plan-%s" % (FOLDER, HASH),
            "%s/state.json" % FOLDER,
            "/%s/%s" % (FOLDER, name),
            "%s/%s/" % (FOLDER, name),
            FOLDER + "//" + name,
            "./%s/%s" % (FOLDER, name),
            "%s/../review-engine/%s" % (FOLDER, name),
            "%s/./%s" % (FOLDER, name),
            "%s\\%s" % (FOLDER, name.replace("/", "\\")),
            "%s/%s\x00" % (FOLDER, name),
            ".workbench/remote-runner.toml",
            ".workbench/manifest.json",
            "",
            "x" * 5000,
        ):
            self.none(added(path))

    def test_the_prefix_of_the_folder_is_not_the_folder(self):
        self.none(added(FOLDER[:-1] + "/plan-%s/state.json" % HASH))


class SpellingDoesNotDrift(unittest.TestCase):
    """The rule copies the engine's spelling, because installer code cannot import package code."""

    def source(self):
        with open(HELPER, encoding="utf-8") as handle:
            return handle.read()

    def test_the_kinds(self):
        line = re.search(r"^KINDS = (.*)$", self.source(), re.M).group(1)
        self.assertEqual(tuple(re.findall(r'\("(\w+)", "docs/', line)), reviewrecords.KINDS)

    def test_the_file_names(self):
        found = re.search(r'^FILE_NAME = re\.compile\(r"(.*)"\)$', self.source(), re.M).group(1)
        self.assertEqual(found, reviewrecords.NAME_PATTERN)

    def test_the_folder_and_the_form_of_the_key(self):
        source = self.source()
        self.assertIn('NAMESPACE = "%s"' % reviewrecords.FOLDER, source)
        self.assertIn('hashlib.sha256(fold(path).encode("utf-8")).hexdigest()[:%d]' % reviewrecords.KEY_DIGITS, source)
        self.assertIn('return "%s-%s" % (kind, hashlib.sha256', source)


if __name__ == "__main__":
    unittest.main()
