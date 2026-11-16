"""The rule that says which added paths are the review engine's own records (`workbench/reviewrecords.py`).

The rule is narrow on purpose: a list that the owner types a digest over may summarise only what has exactly the engine's
spelling. The engine's spelling is read from its helper's source, so a change there fails here.
"""

import ast
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


class ActionReviewSpellingIsTied(unittest.TestCase):
    """The `action-review` helper holds its own patterns for the engine's folder and file names (`REVIEW_STATE_PATH` and
    `REVIEW_FILE_PATH`), because a helper cannot import another's code. They are tied to the engine here: the sources are read
    with `ast` and never run, a universe of paths is built from the spelling of both, and the patterns must say what the engine
    says. The one difference that is meant is pinned by name: a round number above the engine's `MAX_ROUNDS`.
    """

    UNIVERSE_NUMBERS = ("0", "00", "01", "1", "2", "9", "10", "99", "100", "999", "1000", "1001", "9999", "10000")
    DECOY_KINDS = ("plans", "Plan", "PLAN", "decision", "docs", "todo", "")
    DECOY_NAMES = ("State.json", "state.json.bak", "state.jsonx", "notes.md", "other.json", "round-.json", "rounds-1.json",
                   "ledger.MD", "sub/ledger.md", "stateXjson", "ledgerXmd", "schemaXjson", "round-1Xjson", "state2.json",
                   "ledger-2.md")
    WHERE = ("the review engine (packages/workbench/review-engine/helper/review-engine), the installer's rule "
             "(workbench/reviewrecords.py) and the action-review helper (REVIEW_STATE_PATH and REVIEW_FILE_PATH) spell this "
             "alike and must be changed together")

    @classmethod
    def setUpClass(cls):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = cls.parse(HELPER)
        action = cls.parse(os.path.join(root, "packages", "workbench", "action-review", "helper", "action-review"))
        cls.engine_kinds = tuple(kind for kind, _ in ast.literal_eval(cls.assigned(engine, "KINDS")))
        cls.engine_folder = ast.literal_eval(cls.assigned(engine, "NAMESPACE"))
        cls.max_rounds = ast.literal_eval(cls.assigned(engine, "MAX_ROUNDS"))
        cls.engine_names_pattern = cls.compiled_text(engine, "FILE_NAME")
        cls.engine_names = re.compile(cls.engine_names_pattern)
        cls.file_text = cls.compiled_text(action, "REVIEW_FILE_PATH")
        cls.state_text = cls.compiled_text(action, "REVIEW_STATE_PATH")
        cls.file_path = re.compile(cls.file_text)
        cls.state_path = re.compile(cls.state_text)

    @staticmethod
    def parse(path):
        with open(path, encoding="utf-8") as handle:
            return ast.parse(handle.read())

    @staticmethod
    def assigned(tree, name):
        found = [node.value for node in tree.body if isinstance(node, ast.Assign) and len(node.targets) == 1
                 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name]
        if len(found) != 1:
            raise AssertionError("%s is not assigned exactly once at the top of a helper" % name)
        return found[0]

    @classmethod
    def compiled_text(cls, tree, name):
        call = cls.assigned(tree, name)
        if not (isinstance(call, ast.Call) and len(call.args) == 1 and not call.keywords
                and isinstance(call.func, ast.Attribute) and call.func.attr == "compile"
                and isinstance(call.func.value, ast.Name) and call.func.value.id == "re"):
            raise AssertionError("%s is no longer a single re.compile(<text>) with no flags" % name)
        return ast.literal_eval(call.args[0])

    @staticmethod
    def alternatives(text):
        """`text` split on the `|` that are not inside a group, a class or a count, and not escaped."""
        parts, depth, current, escaped = [], 0, "", False
        for char in text:
            if escaped:
                current, escaped = current + char, False
                continue
            if char == "\\":
                current, escaped = current + char, True
                continue
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            if char == "|" and depth == 0:
                parts.append(current)
                current = ""
            else:
                current += char
        parts.append(current)
        return parts

    @classmethod
    def plain_names(cls, text, after_key=True):
        """The file names a pattern spells out in full, such as `state.json` (not the round files, which hold a count), read
        from the alternatives that follow the key (`after_key`) or from the whole text."""
        tail = text.split("}/", 1)[1] if after_key else text
        if tail.startswith("(?:") and tail.endswith(")"):
            tail = tail[3:-1]
        return {re.sub(r"\\(.)", r"\1", alternative) for alternative in cls.alternatives(tail)
                if re.fullmatch(r"(?:[A-Za-z0-9_\-]|\\\.)+", alternative)}

    def kinds_and_digits(self, text):
        found = re.search(r"\(\?:([a-z]+(?:\|[a-z]+)*)\)-\[0-9a-f\]\{(\d+)\}", text)
        self.assertIsNotNone(found, "the kinds and the key of a pattern are no longer of the form this test reads: %r" % text)
        return tuple(found.group(1).split("|")), int(found.group(2))

    def action_kinds_and_digits(self):
        return self.kinds_and_digits(self.file_text)

    def paths(self):
        """Every path of a universe built from the spelling of the engine and of both action-review patterns, with decoys, and
        the kind, the key and the name of each."""
        action_kinds = set(self.kinds_and_digits(self.file_text)[0]) | set(self.kinds_and_digits(self.state_text)[0])
        kinds = sorted(set(self.engine_kinds) | action_kinds | set(self.DECOY_KINDS))
        names = sorted(self.plain_names(self.engine_names_pattern, after_key=False) | self.plain_names(self.file_text)
                       | self.plain_names(self.state_text) | set(self.DECOY_NAMES))
        names += ["round-%s.json" % number for number in self.UNIVERSE_NUMBERS]
        keys = ["ab12" * 4, "ab12" * 3 + "ab1", "ab12" * 4 + "a", "AB12" * 4, "g" * 16, ""]
        folders = [self.engine_folder, self.engine_folder + "2", self.engine_folder.replace("workbench/", "other/", 1),
                   ".workbench/workbench/Review-Engine", self.engine_folder.replace(".workbench", "xworkbench", 1),
                   self.engine_folder.replace("review-engine", "reviewXengine", 1)]
        for folder in folders:
            for kind in kinds:
                for key in keys:
                    for name in names:
                        yield "%s/%s-%s/%s" % (folder, kind, key, name), folder, kind, key, name

    def test_the_kinds_and_the_names_read_out_of_the_patterns_are_the_engines(self):
        """The same, read from the text of each pattern, so that a kind or a name that only one pattern holds is seen
        whatever the universe contains."""
        engine_plain = self.plain_names(self.engine_names_pattern, after_key=False)
        self.assertTrue({"state.json", "ledger.md", "schema.json"} <= engine_plain, "the engine's plain file names: %r" % engine_plain)
        self.assertEqual(engine_plain, self.plain_names(self.file_text), "the plain file names of REVIEW_FILE_PATH; " + self.WHERE)
        self.assertEqual({"state.json"}, self.plain_names(self.state_text), "the file name of REVIEW_STATE_PATH; " + self.WHERE)
        for label, text in (("REVIEW_FILE_PATH", self.file_text), ("REVIEW_STATE_PATH", self.state_text)):
            kinds, digits = self.kinds_and_digits(text)
            self.assertEqual(set(self.engine_kinds), set(kinds), "the kinds of %s; %s" % (label, self.WHERE))
            self.assertEqual(reviewrecords.KEY_DIGITS, digits, "the key of %s; %s" % (label, self.WHERE))

    def test_the_patterns_say_what_the_engine_says(self):
        _, digits = self.action_kinds_and_digits()
        self.assertEqual(digits, reviewrecords.KEY_DIGITS, "the key of the action-review patterns is %d digits; %s"
                         % (digits, self.WHERE))
        for path, folder, kind, key, name in self.paths():
            in_engine = (folder == self.engine_folder and kind in self.engine_kinds
                         and re.fullmatch("[0-9a-f]{%d}" % reviewrecords.KEY_DIGITS, key) is not None
                         and self.engine_names.fullmatch(name) is not None)  # the engine's own spelling of this path
            round_number = re.fullmatch(r"round-([1-9][0-9]*)\.json", name)
            expected_file = in_engine and (round_number is None or int(round_number.group(1)) <= self.max_rounds)
            self.assertEqual(expected_file, self.file_path.fullmatch(path) is not None,
                             "REVIEW_FILE_PATH on %r; %s" % (path, self.WHERE))
            self.assertEqual(in_engine and name == "state.json", self.state_path.fullmatch(path) is not None,
                             "REVIEW_STATE_PATH on %r; %s" % (path, self.WHERE))

    def test_the_installer_rule_agrees_except_above_the_engines_round_cap(self):
        for path, folder, kind, key, name in self.paths():
            rule = reviewrecords.record_of(added(path)) is not None
            patterns = self.file_path.fullmatch(path) is not None
            round_number = re.fullmatch(r"round-([1-9][0-9]*)\.json", name)
            if rule and not patterns:
                self.assertIsNotNone(round_number, "the installer's rule takes %r and REVIEW_FILE_PATH does not; %s"
                                     % (path, self.WHERE))
                self.assertTrue(self.max_rounds < int(round_number.group(1)) <= 9999,
                                "the installer's rule takes %r and REVIEW_FILE_PATH does not; %s" % (path, self.WHERE))
            else:
                self.assertEqual(rule, patterns, "%r; %s" % (path, self.WHERE))

    def test_the_one_meant_difference_is_pinned(self):
        """A round number above the engine's cap and up to 9999 is a record to the installer's rule, as to the engine's own
        `FILE_NAME`, and not to the action-review pattern, which stops at the cap. No real review reaches it."""
        above = record(name="round-%d.json" % (self.max_rounds + 1))
        self.assertIsNotNone(self.engine_names.fullmatch("round-%d.json" % (self.max_rounds + 1)))
        self.assertIsNotNone(reviewrecords.record_of(added(above)))
        self.assertIsNone(self.file_path.fullmatch(above))
        at = record(name="round-%d.json" % self.max_rounds)
        self.assertIsNotNone(reviewrecords.record_of(added(at)))
        self.assertIsNotNone(self.file_path.fullmatch(at))


if __name__ == "__main__":
    unittest.main()
