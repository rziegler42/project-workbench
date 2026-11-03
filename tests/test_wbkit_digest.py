"""The kit's preview digest: what an ``ask`` is bound to, computed and checked once (``workbench/wbkit/digest.py``).

Plan ``2026-11-02-permission-system-consistency``, increment H. The two helpers that carried their own copy must give the answers
they gave before; this file fixes the kit's side and the helpers' own tests fix theirs. The kit names no module and no installer
file, and neither does this file (``tests/test_boundary.py``)."""

import hashlib
import re
import unittest

from workbench import wbkit
from workbench.wbkit import digest


def old(lines):
    """The computation both helpers carried: the first 32 characters of the SHA-256 of the lines joined by a newline."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


class Of(unittest.TestCase):
    def test_it_is_32_lowercase_hex_characters(self):
        self.assertRegex(digest.of(["a", "b"]), r"\A[0-9a-f]{32}\Z")
        self.assertEqual(32, digest.CHARS)

    def test_it_is_the_value_the_helpers_computed_before(self):
        for lines in ([], [""], ["a"], ["a", "b"], ["x\ny"], ["café", "☃"], ["project: p", "sha256: " + "0" * 64]):
            with self.subTest(lines=lines):
                self.assertEqual(old(lines), digest.of(lines))

    def test_it_changes_when_any_line_changes_and_when_the_order_does(self):
        base = digest.of(["one", "two", "three"])
        self.assertNotEqual(base, digest.of(["one", "two", "four"]))
        self.assertNotEqual(base, digest.of(["two", "one", "three"]))
        self.assertNotEqual(base, digest.of(["one", "two"]))
        self.assertEqual(base, digest.of(("one", "two", "three")))

    def test_a_line_break_inside_a_line_is_not_a_second_line_but_the_join_is_the_same(self):
        """The lines are joined by a newline, so ``["a\\nb"]`` and ``["a", "b"]`` are one digest: a preview builds each line
        from one fact, and a caller that must tell them apart binds the fact itself (as a helper that binds a path binds it whole)."""
        self.assertEqual(digest.of(["a\nb"]), digest.of(["a", "b"]))


class WellFormed(unittest.TestCase):
    def test_exactly_32_lowercase_hex_characters(self):
        self.assertTrue(digest.well_formed("0123456789abcdef" * 2))

    def test_anything_else_is_not(self):
        for text in ("", "0" * 31, "0" * 33, "A" * 32, "g" * 32, "0" * 32 + "\n", " " + "0" * 31, "0" * 31 + "١", None, 5,
                     b"0" * 32, ["0" * 32]):
            with self.subTest(text=text):
                self.assertFalse(digest.well_formed(text))


class Mismatch(unittest.TestCase):
    LINES = ["accept a decision", "record: docs/decisions/x.md"]

    def test_the_digest_of_the_lines_is_accepted(self):
        self.assertIsNone(digest.mismatch(digest.of(self.LINES), self.LINES))

    def test_a_wrong_digest_is_refused_with_the_one_standard_line(self):
        for given in ("0" * 32, digest.of(["other"]), "", "short", digest.of(self.LINES).upper()):
            with self.subTest(given=given):
                self.assertEqual(digest.MISMATCH, digest.mismatch(given, self.LINES))

    def test_a_changed_preview_is_refused(self):
        given = digest.of(self.LINES)
        self.assertEqual(digest.MISMATCH, digest.mismatch(given, self.LINES + ["one more fact"]))

    def test_no_digest_given_is_the_callers_to_decide_and_is_refused_here(self):
        """The kit answers whether a digest matches; a caller that goes on with none (a terminal, the level ``none``) does not ask."""
        self.assertEqual(digest.MISMATCH, digest.mismatch(None, self.LINES))

    def test_a_value_that_is_not_text_is_refused_and_never_raises(self):
        for given in (None, 5, b"x", ["x"], {"x": 1}, object(), "☃" * 40, "\udc80" * 32):
            with self.subTest(given=given):
                self.assertEqual(digest.MISMATCH, digest.mismatch(given, self.LINES))

    def test_the_comparison_goes_through_the_constant_time_function(self):
        import unittest.mock
        with unittest.mock.patch.object(digest.hmac, "compare_digest", return_value=True) as compared:
            self.assertIsNone(digest.mismatch("0" * 32, self.LINES))
        self.assertEqual(1, compared.call_count)

    def test_the_standard_line_names_what_to_do(self):
        self.assertEqual("the digest does not match what the command would change now; preview it again with `preview`",
                         digest.MISMATCH)

    def test_it_compares_with_the_lines_it_is_given_so_the_caller_decides_when_they_are_built(self):
        """The kit takes the preview lines, not a path, so it reads nothing itself: a caller builds them in the critical section
        that makes the change. That the helpers do is shown by their own tests (the digest compared under the lock), not here."""
        before = ["state: 1"]
        given = digest.of(before)
        self.assertIsNone(digest.mismatch(given, before))
        self.assertEqual(digest.MISMATCH, digest.mismatch(given, ["state: 2"]))


class Shape(unittest.TestCase):
    def test_the_usage_line_is_the_one_both_helpers_printed(self):
        self.assertEqual("the digest is 32 lowercase hexadecimal characters, as `preview` prints it", digest.SHAPE)

    def test_it_is_ascii_and_one_line(self):
        for text in (digest.MISMATCH, digest.SHAPE):
            self.assertTrue(text.isascii() and "\n" not in text)


class TheKit(unittest.TestCase):
    def test_adding_the_module_did_not_raise_the_kit_api(self):
        # An addition changes no existing kit function, so a helper released against API 1 still loads.
        self.assertEqual(1, wbkit.API)

    def test_it_imports_only_the_standard_library(self):
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workbench", "wbkit", "digest.py")
        with open(path, encoding="utf-8") as handle:
            imports = re.findall(r"^(?:import|from) (\S+)", handle.read(), re.M)
        self.assertEqual(["hashlib", "hmac", "re"], sorted(imports))


if __name__ == "__main__":
    unittest.main()
