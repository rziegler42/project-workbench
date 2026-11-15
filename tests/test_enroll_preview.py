"""``wb preview enroll`` (``workbench/enroll.py``, wired in ``workbench/cli.py``): the read-only text of what ``wb enroll`` would write for a clone, and
the keys of the two commands in the levels registry (``docs/specs/clone-enrollment.md``, "The preview", "Level", "Registration")."""

import io
import os
import unittest

from tests import test_upgrade_preview as base_tests
from workbench import __version__, cli, enrollplan, levels, preview

SCRIPT = base_tests.SCRIPT


class EnrollPreview(base_tests.UpgradePreview):
    def new_machine(self):
        path = self.version()
        self.install(path, store_writes=False)
        return path

    def run_preview(self, *args, place=None):
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["preview", "enroll", place or self.place] + list(args), out, err, store_root=self.store_root)
        return code, out.getvalue(), err.getvalue()


class Text(EnrollPreview):
    def test_a_clone_on_a_new_machine_is_previewed_and_nothing_is_written(self):
        self.new_machine()
        before = (self.tree(self.place), self.tree(self.store_root))
        code, out, err = self.run_preview()
        self.assertEqual((0, ""), (code, err))
        self.assertTrue(out.startswith("target: %s\ncommand: enroll\nproject: %s\n" % (self.real, self.project_id)), out)
        self.assertIn("baselines to record:", out)
        self.assertIn(SCRIPT, out)
        self.assertTrue(out.endswith("%s\n" % preview.ENDING), out)
        self.assertEqual(before, (self.tree(self.place), self.tree(self.store_root)))

    def test_the_digest_printed_is_the_one_of_the_read(self):
        self.new_machine()
        code, out, err = self.run_preview()
        digests = [line[len("digest: "):] for line in out.splitlines() if line.startswith("digest: ")]
        self.assertEqual(1, len(digests))
        self.assertRegex(digests[0], r"\A[0-9a-f]{64}\Z")
        again = self.run_preview()[1]
        self.assertEqual(out, again)

    def test_the_text_is_what_the_read_side_renders(self):
        self.new_machine()
        code, out, err = self.run_preview()
        from workbench import target
        with target.open_target(self.place, self.store_root) as held:
            plan = enrollplan.examine(self.guarded, held, __version__)
        self.assertEqual(enrollplan.render(plan, self.real) + preview.ENDING + "\n", out)

    def test_a_project_the_machine_knows_is_refused_and_names_acknowledge(self):
        self.install(self.version())
        before = (self.tree(self.place), self.tree(self.store_root))
        code, out, err = self.run_preview()
        self.assertEqual((1, ""), (code, out))
        self.assertTrue(err.startswith("refused: "), err)
        self.assertIn("acknowledge", err)
        self.assertEqual(before, (self.tree(self.place), self.tree(self.store_root)))

    def test_an_edited_module_owned_file_is_refused_naming_its_path(self):
        self.new_machine()
        self.edit(SCRIPT, lambda data: data + b"# planted\n")
        code, out, err = self.run_preview()
        self.assertEqual((1, ""), (code, out))
        self.assertIn(SCRIPT, err)

    def test_a_directory_that_is_not_a_project_is_refused_by_the_target(self):
        os.makedirs(self.place)
        code, out, err = self.run_preview()
        self.assertEqual((1, ""), (code, out))
        self.assertTrue(err.startswith("refused: ") or "not an existing project" in err, err)

    def test_the_preview_takes_no_digest_and_no_other_option(self):
        self.new_machine()
        for argument in ("--digest", "--package"):
            code, out, err = self.run_preview(argument, "x")
            self.assertEqual((2, ""), (code, out), argument)
            self.assertIn("unknown option", err)

    def test_the_target_may_be_given_with_dir(self):
        self.new_machine()
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["preview", "enroll", "--dir", self.place], out, err, store_root=self.store_root)
        self.assertEqual((0, ""), (code, err.getvalue()))
        self.assertIn("command: enroll", out.getvalue())


class NotBuilt(unittest.TestCase):
    """``wb enroll`` itself is routed, and refuses until the increment that builds it."""

    def run_command(self, *tokens):
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["enroll"] + list(tokens), out, err, store_root="/nonexistent-store-for-this-test")
        return code, out.getvalue(), err.getvalue()

    def test_the_command_refuses_and_points_to_the_preview(self):
        code, out, err = self.run_command("somewhere")
        self.assertEqual((1, ""), (code, out))
        self.assertTrue(err.startswith("refused: "), err)
        self.assertIn("wb preview enroll", err)

    def test_a_bad_option_is_a_usage_error_and_still_refuses_nothing_else(self):
        code, out, err = self.run_command("--digest", "x")
        self.assertEqual((2, ""), (code, out))
        self.assertIn("unknown option", err)

    def test_it_is_a_routed_owner_run_command(self):
        from workbench import rules
        self.assertIn("enroll", rules.OWNER_RUN)
        self.assertEqual((), rules.NOT_YET_ROUTED)


class Keys(unittest.TestCase):
    def test_enroll_is_an_owner_run_command_that_offers_block_only(self):
        key = levels.registry()["wb enroll"]
        self.assertEqual(("command", "governs"), (key.kind, key.klass))
        self.assertEqual(("block",), tuple(key.offers))
        self.assertEqual("wb preview enroll", key.preview)
        self.assertIn("enroll", levels.OWNER_RUN)

    def test_the_preview_is_a_key_of_its_own_that_only_reads(self):
        key = levels.registry()["wb preview enroll"]
        self.assertEqual("reads", key.klass)
        self.assertEqual(("block", "none"), tuple(key.offers))
        self.assertEqual("none", key.default)
        self.assertIn("enroll", levels.PREVIEW_ACTIONS)


if __name__ == "__main__":
    unittest.main()
