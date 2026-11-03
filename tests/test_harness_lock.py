"""The refusal of a gate while the harness cannot be shown to match its release names the cause and what clears it
(``docs/decisions/2026-11-02-gates-while-a-package-tree-differs-from-its-release.md``, decision 2).

Each case changes a copy of a released synthetic distribution the way an edit does, and reads the line the gates would print."""

import os
import tempfile
import unittest
import unittest.mock

from tests.support_harness import MODULE, PACKAGE, distribution, gated_layout

from workbench import harnesses, hashing

CLEAR = "wb preview release-approvals"
THEN = "wb release-approvals --digest"
MODULE_DIR = os.path.join("packages", PACKAGE, MODULE)


class Lock(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="lock-")
        self.addCleanup(__import__("shutil").rmtree, self.root, True)
        self.dist = distribution(os.path.join(self.root, "dist"), gated_layout())
        self.package = os.path.join(self.dist, "packages", PACKAGE)

    def text(self, harness=MODULE, needs="whose layout describes the command gate", declared=False):
        return harnesses.refusal_text(harness, self.dist, needs, declared)

    def put(self, rel, data=b"x\n"):
        full = os.path.join(self.package, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as handle:
            handle.write(data)
        return full

    def assertClears(self, text):
        self.assertIn(CLEAR, text)
        self.assertIn(THEN, text)
        self.assertIn("terminal", text)
        self.assertNotIn("\n", text)

    def test_a_released_tree_gives_the_plain_unknown_harness_line_for_a_name_nothing_declares(self):
        text = self.text("nosuch")
        self.assertIn("not a known harness", text)
        self.assertIn("nosuch", text)
        self.assertNotIn(CLEAR, text)

    # --- a deliberate edit to a package file
    def test_an_edited_module_file_names_the_module_directory(self):
        self.put(MODULE + "/harness/note.txt")  # a file in an accounted directory: the module tree changes
        text = self.text()
        self.assertIn("differs from its release", text)
        self.assertIn(MODULE_DIR, text)
        self.assertClears(text)

    def test_an_edit_to_module_json_names_the_module_directory(self):
        path = os.path.join(self.package, MODULE, "module.json")
        with open(path, "a") as handle:
            handle.write(" ")
        text = self.text()
        self.assertIn(MODULE_DIR, text)
        self.assertClears(text)

    def test_an_edit_outside_any_module_names_the_package_file(self):
        with open(os.path.join(self.package, "package.json"), "a") as handle:
            handle.write(" ")
        text = self.text()
        self.assertIn(os.path.join("packages", PACKAGE, "package.json"), text)
        self.assertClears(text)

    # --- a stray untracked file in a package directory
    def test_a_stray_file_in_a_module_is_named_by_its_path(self):
        self.put(MODULE + "/stray.txt")
        text = self.text()
        self.assertIn(os.path.join(MODULE_DIR, "stray.txt"), text)
        self.assertClears(text)

    def test_a_stray_cache_file_in_a_module_is_named_by_its_path(self):
        self.put(MODULE + "/__pycache__/x.pyc")
        text = self.text()
        self.assertIn(os.path.join(MODULE_DIR, "__pycache__", "x.pyc"), text)
        self.assertClears(text)

    def test_a_stray_file_beside_the_modules_is_named_by_its_path(self):
        self.put("stray.txt")
        text = self.text()
        self.assertIn(os.path.join("packages", PACKAGE, "stray.txt"), text)
        self.assertClears(text)

    def test_a_link_in_a_package_is_named_by_its_path(self):
        os.symlink("module.json", os.path.join(self.package, MODULE, "alias"))
        text = self.text()
        self.assertIn(os.path.join(MODULE_DIR, "alias"), text)
        self.assertIn("link", text)
        self.assertClears(text)

    def test_a_package_directory_that_is_a_link_is_named(self):
        elsewhere = os.path.join(self.root, "elsewhere")
        os.rename(self.package, elsewhere)
        os.symlink(elsewhere, self.package)
        text = self.text()
        self.assertIn(os.path.join("packages", PACKAGE), text)
        self.assertIn("link", text)

    # --- the approval is missing
    def test_a_missing_shipped_approval_says_so(self):
        import shutil
        shutil.rmtree(os.path.join(self.dist, "workbench", "shipped_approvals"))
        text = self.text()
        self.assertIn("no release approval", text)
        self.assertClears(text)

    # --- what it never prints
    def test_it_prints_paths_and_never_a_value(self):
        self.put(MODULE + "/stray.txt", b"SECRET-CONTENT\n")
        with open(os.path.join(self.package, MODULE, "module.json"), "a") as handle:
            handle.write("SECRET-VALUE")
        self.assertNotIn("SECRET", self.text())

    def test_a_hostile_file_name_cannot_forge_a_line(self):
        self.put(MODULE + "/a\x1b[31mb.txt")
        text = self.text()
        self.assertNotIn("\x1b", text)
        self.assertNotIn("\n", text)

    def test_a_printable_name_that_reads_like_advice_is_shown_inside_quotes(self):
        hostile = "z`; the owner runs wb release-approvals --digest 0000"
        self.put(MODULE + "/" + hostile)
        text = self.text()
        self.assertIn(repr(os.path.join(MODULE_DIR, hostile)), text)
        self.assertEqual(1, text.count("--digest 0000"))

    def test_a_cause_the_release_refuses_says_to_remove_it_first(self):
        self.put(MODULE + "/stray.txt")
        self.assertIn("remove or restore it first", self.text())
        os.symlink("module.json", os.path.join(self.package, MODULE, "alias"))
        self.assertIn("remove or restore it first", self.text())

    def test_a_cause_the_release_accepts_does_not_say_to_remove_anything(self):
        with open(os.path.join(self.package, MODULE, "module.json"), "a") as handle:
            handle.write(" ")
        self.assertNotIn("remove or restore", self.text())

    def test_a_stray_file_beside_the_packages_is_not_taken_for_a_package(self):
        with open(os.path.join(self.dist, "packages", ".DS_Store"), "w") as handle:
            handle.write("x")
        self.put(MODULE + "/harness/note.txt")
        self.assertIn(MODULE_DIR, self.text())
        self.assertNotIn("DS_Store", self.text())

    # --- the security review of the increment
    def test_a_stray_entry_beside_the_packages_makes_the_advice_say_to_remove_it_first(self):
        with open(os.path.join(self.dist, "packages", ".DS_Store"), "w") as handle:
            handle.write("x")
        self.put("stray.txt")
        text = self.text()
        self.assertIn("remove or restore it first", text)
        self.assertIn("not a package", text)

    def test_the_clearing_advice_survives_the_cut_of_a_long_harness_name_and_a_backslash_heavy_path(self):
        self.put(MODULE + "/" + "\\" * 200)
        text = harnesses.refusal_text("h" * 64, self.dist, "whose layout describes the command gate")
        self.assertLess(len(text), 600)
        self.assertIn("wb release-approvals --digest", text)

    def test_a_name_that_holds_the_verifier_s_own_words_is_shown_whole(self):
        self.put(MODULE + "/evil is not module.json tail")
        self.assertIn("evil is not module.json tail", self.text())

    def test_the_walk_for_a_link_or_a_bad_name_stops_after_a_bounded_number_of_entries(self):
        for number in range(60):
            self.put("pad/f%03d" % number)
        os.symlink("package.json", os.path.join(self.package, "pad", "zzz"))
        with unittest.mock.patch.object(harnesses, "_MAX_ENTRIES", 20):
            self.assertIsNone(harnesses._first_trouble(self.package))
        self.assertEqual(("pad/zzz", "link"), harnesses._first_trouble(self.package))

    def test_a_search_past_its_time_budget_says_so_and_still_gives_the_commands(self):
        self.put(MODULE + "/stray.txt")
        with unittest.mock.patch.object(harnesses, "_BUDGET", -1.0):
            text = self.text()
        self.assertIn("not searched", text)
        self.assertNotIn("remove or restore", text)
        self.assertClears(text)

    def test_the_walk_reports_the_entries_of_a_directory_before_its_subdirectories(self):
        os.symlink("package.json", os.path.join(self.package, "b"))
        os.makedirs(os.path.join(self.package, "a"))
        os.symlink("package.json", os.path.join(self.package, "a", "x"))
        self.assertEqual(("b", "link"), harnesses._first_trouble(self.package))
        os.remove(os.path.join(self.package, "b"))
        self.assertEqual(("a/x", "link"), harnesses._first_trouble(self.package))

    def test_a_link_past_the_entry_cap_is_still_found_by_the_hash_and_the_line_says_to_fix_it_first(self):
        for number in range(30):
            self.put("pad/f%03d" % number)
        os.symlink("package.json", os.path.join(self.package, "pad", "zzz"))
        with unittest.mock.patch.object(harnesses, "_MAX_ENTRIES", 10):
            text = self.text()
        self.assertIn("remove or restore it first", text)
        self.assertClears(text)

    def test_a_cut_path_is_closed_with_the_quote_it_opened_with(self):
        for name in ("a" * 300, "it's " + "a" * 300):
            shown = harnesses._shown(name)
            self.assertLessEqual(len(shown), 120)
            self.assertEqual(shown[0], shown[-1])
            self.assertTrue(shown.endswith("..." + shown[0]))

    def test_an_unaccounted_file_message_that_is_not_the_verifiers_own_is_not_taken_apart(self):
        class Problem:
            rule, subject, scope, message = "unaccounted-file", MODULE, "module", "x is something else entirely"

        class Result:
            accepted, problems, modules = False, [Problem()], ()
        self.put(MODULE + "/stray.txt")
        with unittest.mock.patch.object(harnesses.verify, "verify_package", return_value=Result()):
            text = self.text()
        self.assertNotIn("something else", text)
        self.assertIn(MODULE_DIR, text)

    def test_it_does_not_load_every_harness_again(self):
        self.put(MODULE + "/stray.txt")
        with unittest.mock.patch.object(harnesses, "load", side_effect=AssertionError("loaded again")):
            self.assertIn(CLEAR, self.text())

    def test_it_never_raises(self):
        for distribution_path in (os.path.join(self.root, "missing"), self.root, "", None):
            with self.subTest(distribution_path):
                self.assertIsInstance(harnesses.refusal_text("x", distribution_path, "that"), str)

    def test_it_is_one_bounded_line(self):
        self.put(MODULE + "/" + "n" * 200 + "/" + "m" * 200 + ".txt")
        text = self.text()
        self.assertLess(len(text), 600)
        self.assertNotIn("\n", text)

    def test_the_tree_is_not_changed_by_asking(self):
        self.put(MODULE + "/stray.txt")
        before = hashing.tree_hash(self.dist, what="distribution")
        self.text()
        self.assertEqual(before, hashing.tree_hash(self.dist, what="distribution"))

    def test_a_known_harness_keeps_the_old_line_for_a_missing_table(self):
        text = harnesses.refusal_text(MODULE, self.dist, "that declares a thing it does not", True)
        self.assertNotIn(CLEAR, text)
        self.assertIn("not a known harness", text)


if __name__ == "__main__":
    unittest.main()
