"""``wb enroll`` (``workbench/enroll.py``, routed in ``workbench/cli.py``): the owner-run command that writes the baselines and the first-seen record of a
clone on a machine that does not know it (``docs/specs/clone-enrollment.md``). It runs only at a terminal, shows the list and the digest, takes the first
characters of the digest typed back, reads the clone again and writes the two entries in one step; it writes no pin, and the pins follow from ``upgrade`` with
the package, which the last tests prove on a project installed in a store that does not know it."""

import hashlib
import io
import os
import shutil
import unittest
import unittest.mock

from tests import test_upgrade_pins as pin_tests
from tests import test_upgrade_preview as base_tests
from workbench import (__version__, acknowledgement, approve, cli, confirm, enrollplan, installplan, manifest, pins,
                       target)
from workbench.wbkit import safefs

MANIFEST = ".workbench/manifest.json"
TOOL = pin_tests.TOOL
HELPER = pin_tests.HELPER


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Enroll(pin_tests.Pins):
    """A project written the way `install` writes it, in a store that does not know it: a clone on a new machine."""

    def new_machine(self):
        path = self.version()
        self.install(path, store_writes=False)
        return path

    def run_it(self, answer=None, *args, place=None, during=None, stdin=None, store_root=None):
        out, err = io.StringIO(), io.StringIO()

        class Ask(io.StringIO):
            def readline(this, *a):
                if during:
                    during()
                if answer is not None:
                    return answer + "\n"
                digest = [line for line in out.getvalue().splitlines() if line.startswith("digest: ")][-1]
                return digest[len("digest: "):][:confirm.CONFIRM_CHARS] + "\n"

        code = cli.main(["enroll", place or self.place] + list(args), out, err,
                        store_root=store_root or self.store_root, stdin=stdin or Ask(""))
        return code, out.getvalue(), err.getvalue()

    def entries(self):
        return (acknowledgement.read_baselines(self.guarded, self.project_id), acknowledgement.read_seen(self.guarded, self.project_id))

    def plan(self):
        with target.open_target(self.place, self.store_root) as held:
            return enrollplan.examine(self.guarded, held, __version__)

    def rewrite_manifest(self, change):
        document = manifest.parse(self.read(MANIFEST))
        change(document)
        document["files"].sort(key=lambda f: (f["path"].encode("utf-8"), f.get("block", "")))
        with open(os.path.join(self.place, ".workbench", "manifest.json"), "wb") as handle:
            handle.write(manifest.serialize(document))

    def acknowledge_everything(self):
        out, err = io.StringIO(), io.StringIO()

        class Ask(io.StringIO):
            def readline(this, *a):
                digest = [line for line in out.getvalue().splitlines() if line.startswith("digest: ")][0]
                return digest[len("digest: "):][:confirm.CONFIRM_CHARS] + "\n"

        code = cli.main(["acknowledge", self.place], out, err, store_root=self.store_root, stdin=Ask(""))
        self.assertEqual((0, ""), (code, err.getvalue()), out.getvalue())


class Writing(Enroll):
    def test_a_clone_is_enrolled_after_the_typed_digest_and_only_the_two_entries_are_written(self):
        self.new_machine()
        plan = self.plan()
        project, store_before = self.tree(self.place), self.tree(self.store_root)
        code, out, err = self.run_it()
        self.assertEqual((0, ""), (code, err), out)
        baselines, seen = self.entries()
        self.assertEqual(plan.baselines, baselines)
        self.assertEqual(self.real, seen)
        self.assertEqual(project, self.tree(self.place))
        added = set(self.tree(self.store_root)) - set(store_before) - {"projects/%s" % self.project_id}
        self.assertEqual({"projects/%s/baselines" % self.project_id, "projects/%s/seen" % self.project_id}, added)
        now = self.tree(self.store_root)
        self.assertEqual({k: v for k, v in store_before.items() if k != "projects"}, {k: now[k] for k in store_before if k != "projects"})

    def test_it_shows_the_list_and_the_digest_and_says_what_comes_next(self):
        self.new_machine()
        code, out, err = self.run_it()
        self.assertEqual((0, ""), (code, err), out)
        self.assertIn("command: enroll", out)
        self.assertIn("baselines to record:", out)
        self.assertIn("type the first %d characters of the digest" % confirm.CONFIRM_CHARS, out)
        self.assertIn("enrolled %d paths" % len(self.entries()[0]), out)
        for word in ("acknowledge", "upgrade", "attach"):
            self.assertIn(word, out.rsplit("enrolled", 1)[1])

    def test_it_writes_no_pin(self):
        self.new_machine()
        self.run_it()
        self.assertEqual({}, pins.load(self.guarded, self.project_id))
        self.assertFalse(os.path.exists(os.path.join(self.store_root, "projects", self.project_id, "pins")))

    def test_a_wrong_answer_cancels_and_writes_nothing(self):
        self.new_machine()
        before = (self.tree(self.place), self.tree(self.store_root))
        code, out, err = self.run_it(answer="0" * confirm.CONFIRM_CHARS)
        self.assertEqual(1, code)
        self.assertIn("cancelled: nothing was written", out)
        self.assertEqual(before, (self.tree(self.place), self.tree(self.store_root)))

    def test_an_answer_that_is_too_short_cancels(self):
        self.new_machine()
        short = self.plan().digest[:confirm.CONFIRM_CHARS - 1]
        before = self.tree(self.store_root)
        code, out, err = self.run_it(answer=short)
        self.assertEqual(1, code)
        self.assertEqual(before, self.tree(self.store_root))

    def test_an_empty_answer_cancels(self):
        self.new_machine()
        before = self.tree(self.store_root)
        self.assertEqual(1, self.run_it(answer="")[0])
        self.assertEqual(before, self.tree(self.store_root))

    def test_a_clone_that_changes_while_the_list_is_shown_is_refused_and_nothing_is_written(self):
        self.new_machine()
        before = self.tree(self.store_root)
        code, out, err = self.run_it(during=lambda: self.edit("AGENTS.md", lambda data: data + b"\nChanged meanwhile.\n"))
        self.assertEqual((1, True), (code, "changed while the list was shown" in err), (out, err))
        self.assertEqual(before, self.tree(self.store_root))

    def test_an_interrupt_at_the_prompt_writes_nothing(self):
        self.new_machine()

        class Interrupted(io.StringIO):
            def readline(self, *a):
                raise KeyboardInterrupt

        before = self.tree(self.store_root)
        code, out, err = self.run_it(stdin=Interrupted(""))
        self.assertEqual(130, code)
        self.assertEqual(before, self.tree(self.store_root))

    def test_a_write_that_fails_leaves_no_entry_and_says_so(self):
        self.new_machine()
        before = self.tree(self.store_root)
        with unittest.mock.patch.object(safefs, "write_tree", side_effect=safefs.SafeFsError("no space left")):
            code, out, err = self.run_it()
        self.assertEqual(3, code)
        self.assertIn("failed: no space left", err)
        self.assertIn("nothing was written", err)
        self.assertEqual((None, None), self.entries())
        self.assertEqual(before, self.tree(self.store_root))

    def test_entries_that_do_not_read_back_as_written_are_a_failure(self):
        self.new_machine()
        real = safefs.write_tree

        def wrong_path(root, tree, *a, **k):
            tree = dict(tree)
            tree["projects/%s/seen" % self.project_id] = installplan.json_store({"format": 1, "kind": "path", "value": "/elsewhere"})
            return real(root, tree, *a, **k)
        with unittest.mock.patch.object(safefs, "write_tree", wrong_path):
            code, out, err = self.run_it()
        self.assertEqual(3, code)
        self.assertIn("failed:", err)
        self.assertNotIn("enrolled", out)
        # Both entries are there, so the message says so and does not claim that the project has only some of them.
        self.assertIn("holds both entries", err)
        self.assertNotIn("only some", err)

    def test_a_store_that_cannot_be_read_to_say_what_remains_is_said_so(self):
        from workbench import store
        self.new_machine()
        patcher = unittest.mock.patch.object(store.Tree, "kind", side_effect=store.StoreError("the store is gone"))

        def fail_then_break_the_store(*a, **k):
            patcher.start()
            self.addCleanup(patcher.stop)
            raise safefs.SafeFsError("no space left")
        with unittest.mock.patch.object(safefs, "write_tree", fail_then_break_the_store):
            code, out, err = self.run_it()
        self.assertEqual(3, code)
        self.assertIn("failed: no space left", err)
        self.assertIn("could not be read", err)

    def test_a_project_directory_that_is_replaced_while_the_list_is_shown_is_refused_and_nothing_is_written(self):
        self.new_machine()
        moved = self.place + ".moved"

        def swap():
            os.rename(self.place, moved)
            shutil.copytree(moved, self.place, symlinks=True)
        before = self.tree(self.store_root)
        code, out, err = self.run_it(during=swap)
        self.assertEqual(1, code, (out, err))
        self.assertIn("refused:", err)
        self.assertEqual(before, self.tree(self.store_root))
        self.assertEqual((None, None), self.entries())

    def test_a_failure_after_one_entry_is_named_and_says_what_remains(self):
        self.new_machine()
        real = safefs.write_tree

        def one_then_fail(root, tree, *a, **k):
            first = {key: value for key, value in tree.items() if key.endswith("/baselines")}
            real(root, first, *a, **k)
            raise safefs.SafeFsError("interrupted between the two")
        with unittest.mock.patch.object(safefs, "write_tree", one_then_fail):
            code, out, err = self.run_it()
        self.assertEqual(3, code)
        self.assertIn("baselines", err)
        self.assertIn("refuses", err)


class Refusals(Enroll):
    def test_a_project_the_machine_knows_is_refused_and_names_acknowledge(self):
        self.install(self.version())
        before = (self.tree(self.place), self.tree(self.store_root))
        code, out, err = self.run_it()
        self.assertEqual(1, code)
        self.assertIn("acknowledge", err)
        self.assertEqual(before, (self.tree(self.place), self.tree(self.store_root)))

    def test_an_edited_module_owned_file_is_refused_before_anything_is_asked(self):
        self.new_machine()
        self.edit(TOOL, lambda data: data + b"# planted\n")
        before = self.tree(self.store_root)
        code, out, err = self.run_it()
        self.assertEqual(1, code)
        self.assertIn(TOOL, err)
        self.assertNotIn("type the first", out)
        self.assertEqual(before, self.tree(self.store_root))

    def test_without_a_terminal_it_refuses_and_creates_no_store(self):
        self.new_machine()
        elsewhere = os.path.join(self.root, "no-store-here")
        with unittest.mock.patch.object(approve, "is_terminal", lambda stream: False):
            code, out, err = self.run_it(store_root=elsewhere)
        self.assertEqual((1, ""), (code, out))
        self.assertIn("terminals", err)
        self.assertFalse(os.path.exists(elsewhere))

    def test_without_a_terminal_it_refuses_even_with_a_store(self):
        self.new_machine()
        before = self.tree(self.store_root)
        with unittest.mock.patch.object(approve, "is_terminal", lambda stream: False):
            code, out, err = self.run_it()
        self.assertEqual((1, ""), (code, out))
        self.assertEqual(before, self.tree(self.store_root))

    def test_the_command_refuses_without_a_terminal_even_when_called_directly(self):
        from workbench import enroll
        self.new_machine()
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.object(approve, "is_terminal", lambda stream: False):
            code = enroll.run(self.guarded, self.place, io.StringIO(""), out, err)
        self.assertEqual((1, ""), (code, out.getvalue()))
        self.assertIn("terminals", err.getvalue())
        self.assertEqual((None, None), self.entries())

    def test_it_takes_no_digest_and_no_other_option(self):
        self.new_machine()
        for argument in ("--digest", "--package"):
            code, out, err = self.run_it(None, argument, "x")
            self.assertEqual((2, ""), (code, out), argument)
            self.assertIn("unknown option", err)

    def test_the_key_offers_block_only_so_no_level_can_run_it_without_a_terminal(self):
        from workbench import levels
        self.assertEqual(("block",), tuple(levels.registry()["wb enroll"].offers))


class Afterwards(Enroll):
    def test_the_other_commands_no_longer_call_the_project_new(self):
        self.new_machine()
        self.assertEqual(0, self.run_it()[0])
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["preview", "acknowledge", self.place], out, err, store_root=self.store_root)
        self.assertEqual((0, ""), (code, err.getvalue()), out.getvalue())
        out, err = io.StringIO(), io.StringIO()
        cli.main(["check", self.place], out, err, store_root=self.store_root)
        self.assertNotIn("treated as new", err.getvalue() + out.getvalue())
        # The helpers are not pinned yet, and the check says so: `upgrade` with the package pins them.
        self.assertIn("is not pinned", err.getvalue() + out.getvalue())

    def test_the_preview_of_the_later_command_lists_only_the_files_the_manifest_does_not_record(self):
        self.new_machine()
        for name in ("a", "b"):
            full = os.path.join(self.place, ".workbench", "p", "records", name)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as handle:
                handle.write(b"x")
        self.assertEqual(0, self.run_it()[0])
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["preview", "acknowledge", self.place], out, err, store_root=self.store_root)
        self.assertEqual((0, ""), (code, err.getvalue()))
        added = [line.split()[1] for line in out.getvalue().splitlines() if line.startswith("  added ")]
        self.assertEqual([".workbench/p/records/a", ".workbench/p/records/b"], added)
        self.assertNotIn("  changed ", out.getvalue())
        self.assertNotIn("  removed ", out.getvalue())

    def test_a_second_enrollment_is_refused_and_names_acknowledge(self):
        self.new_machine()
        self.assertEqual(0, self.run_it()[0])
        code, out, err = self.run_it()
        self.assertEqual(1, code)
        self.assertIn("acknowledge", err)


class ThePinsFollow(Enroll):
    """The design rests on this: after `enroll` and `acknowledge`, `upgrade` with the package creates the pins from bytes it verifies."""

    def test_upgrade_with_the_package_creates_a_pin_for_each_helper(self):
        path = self.new_machine()
        self.assertEqual(0, self.run_it()[0])
        self.acknowledge_everything()
        self.assertEqual({}, self.held())
        code, out, err = self.preview("--package", path)
        self.assertEqual((0, ""), (code, err), out)
        self.assertNotIn("treated as new", out + err)
        self.assertIn("create pin tool: %s sha256 %s" % (TOOL, sha(HELPER)), out)
        self.assertIn("create pin lint:", out)
        code, out, err = self.upgrade("--package", path)
        self.assertEqual((0, ""), (code, err), out)
        held = self.held()
        self.assertEqual({"tool", "lint"}, set(held))
        self.assertEqual((sha(HELPER), "workbench upgrade"), (held["tool"].sha256, held["tool"].pinned_by))

    def test_a_helper_planted_in_the_clone_with_its_manifest_hash_changed_is_replaced_by_the_package(self):
        path = self.new_machine()
        planted = b"#!/bin/sh\necho planted\n"
        self.edit(TOOL, lambda data: planted)

        def change(doc):
            for item in doc["files"]:
                if item["path"] == TOOL:
                    item["hash"] = sha(planted)
        self.rewrite_manifest(change)
        self.assertEqual(0, self.run_it()[0])
        self.acknowledge_everything()
        code, out, err = self.preview("--package", path)
        self.assertEqual((0, ""), (code, err), out)
        self.assertIn("replace %s" % TOOL, out)
        code, out, err = self.upgrade("--package", path)
        self.assertEqual((0, ""), (code, err), out)
        self.assertEqual(HELPER, self.read(TOOL))
        self.assertEqual(sha(HELPER), self.held()["tool"].sha256)


if __name__ == "__main__":
    unittest.main()
