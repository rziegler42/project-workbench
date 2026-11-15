"""The read side of ``wb enroll`` (``workbench/enrollplan.py``; ``docs/specs/clone-enrollment.md``, "What it checks"): what an enrollment would
write for a clone of an installed project on a machine that does not know it, or why it refuses. Nothing here writes, reads an approval record or
makes a pin. The fixture is the installer's own: ``install(path, store_writes=False)`` leaves a project written as `install` writes it and a store
with no entry for it, which is a clone on a new machine."""

import hashlib
import json
import os
import re
import shutil
import unittest
import unittest.mock

from tests import test_upgrade_preview as base_tests
from workbench import (__version__, acknowledgement, approvals, enrollplan, firstparty, installplan, manifest, pins,
                       projectfs, target)

MANIFEST = ".workbench/manifest.json"
SCRIPT = base_tests.SCRIPT
POLICY = ".workbench/p/a/policy.md"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Enroll(base_tests.UpgradePreview):
    def new_machine(self):
        path = self.version()
        self.install(path, store_writes=False)
        return path

    def examine(self):
        with target.open_target(self.place, self.store_root) as held:
            return enrollplan.examine(self.guarded, held, __version__)

    def refusal(self, contains):
        """Examine and expect a refusal that says `contains`; neither the project nor the store changes."""
        before = (self.tree(self.place), self.tree(self.store_root))
        with self.assertRaises(enrollplan.Refused) as caught:
            self.examine()
        text = "\n".join(caught.exception.lines)
        self.assertIn(contains, text)
        self.assertEqual(before, (self.tree(self.place), self.tree(self.store_root)))
        return text

    def rewrite_manifest(self, change):
        document = manifest.parse(self.read(MANIFEST))
        change(document)
        document["files"].sort(key=lambda f: (f["path"].encode("utf-8"), f.get("block", "")))
        with open(os.path.join(self.place, ".workbench", "manifest.json"), "wb") as handle:
            handle.write(manifest.serialize(document))

    def put(self, rel, data):
        full = os.path.join(self.place, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as handle:
            handle.write(data)


class Result(Enroll):
    def test_a_clone_on_a_new_machine_gives_the_baselines_and_the_first_seen_record(self):
        self.new_machine()
        plan = self.examine()
        self.assertEqual(self.project_id, plan.project)
        self.assertEqual(self.real, plan.path)
        document = manifest.parse(self.read(MANIFEST))
        self.assertEqual(sha(self.read(MANIFEST)), plan.baselines[MANIFEST])
        for item in document["files"]:
            if item["class"] == "module-owned":
                self.assertEqual(item["hash"], plan.baselines[item["path"]], item["path"])
        self.assertEqual(sha(self.read("AGENTS.md")), plan.baselines["AGENTS.md"])

    def test_the_entries_it_gives_are_the_ones_the_other_commands_read_and_find_nothing_to_change(self):
        self.new_machine()
        plan = self.examine()
        self.guarded.write("projects/%s/baselines" % plan.project, plan.baselines_bytes)
        self.guarded.write("projects/%s/seen" % plan.project, plan.seen_bytes)
        baselines = acknowledgement.read_baselines(self.guarded, plan.project)
        seen = acknowledgement.read_seen(self.guarded, plan.project)
        acknowledgement.check_known(baselines, seen, self.real)
        with target.open_target(self.place, self.store_root) as held:
            found = acknowledgement.differences(projectfs.Writer(held), baselines)
        self.assertEqual([], found)

    def test_it_writes_nothing_in_the_project_or_the_store(self):
        self.new_machine()
        before = (self.tree(self.place), self.tree(self.store_root))
        self.examine()
        self.assertEqual(before, (self.tree(self.place), self.tree(self.store_root)))

    def test_it_does_not_call_the_approval_checks_and_makes_no_pin(self):
        self.new_machine()
        boom = AssertionError("an approval record was read")
        with unittest.mock.patch.object(approvals, "check_module", side_effect=boom), \
                unittest.mock.patch.object(approvals, "check_package", side_effect=boom), \
                unittest.mock.patch.object(firstparty, "check_module", side_effect=boom):
            plan = self.examine()
        self.assertFalse(hasattr(plan, "pins"))

    def test_the_digest_is_the_same_on_a_second_look_and_changes_with_the_files(self):
        self.new_machine()
        first = self.examine()
        self.assertEqual(first.digest, self.examine().digest)
        self.edit("AGENTS.md", lambda data: data + b"\nMine.\n")
        self.assertNotEqual(first.digest, self.examine().digest)

    def test_the_digest_covers_the_baselines_and_the_first_seen_path(self):
        self.new_machine()
        plan = self.examine()
        self.assertEqual(plan.baselines, plan.fields["baselines"])
        self.assertEqual(self.real, plan.fields["path"])
        self.assertEqual(self.project_id, plan.fields["project"])

    def test_the_text_shown_names_the_project_the_path_the_files_and_the_digest(self):
        self.new_machine()
        plan = self.examine()
        text = enrollplan.render(plan, self.real)
        self.assertIn("command: enroll", text)
        self.assertIn("project: %s" % plan.project, text)
        self.assertIn("target: %s" % self.real, text)
        self.assertIn(SCRIPT, text)
        self.assertTrue(text.rstrip("\n").endswith("digest: %s" % plan.digest), text)


class Unknown(Enroll):
    def test_a_project_the_machine_knows_is_refused_and_names_acknowledge(self):
        self.install(self.version())
        text = self.refusal("acknowledge")
        self.assertIn("known", text)

    def test_a_project_with_only_the_first_seen_record_is_refused_naming_the_entry(self):
        self.install(self.version())
        os.unlink(os.path.join(self.store_root, "projects", self.project_id, "baselines"))
        self.refusal("baselines")

    def test_a_project_with_only_the_baselines_is_refused_naming_the_entry(self):
        self.install(self.version())
        os.unlink(os.path.join(self.store_root, "projects", self.project_id, "seen"))
        self.refusal("first-seen")

    def test_a_malformed_entry_is_refused(self):
        self.install(self.version())
        with open(os.path.join(self.store_root, "projects", self.project_id, "seen"), "wb") as handle:
            handle.write(b"{}")
        self.refusal("seen")

    def test_a_directory_that_is_not_an_existing_project_is_refused_by_the_target_and_by_the_read(self):
        self.new_machine()
        with target.open_target(self.place, self.store_root) as held:
            held.state = "new-empty"
            with self.assertRaises(enrollplan.Refused) as caught:
                enrollplan.examine(self.guarded, held, __version__)
        self.assertIn("not an existing project", "\n".join(caught.exception.lines))
        os.unlink(os.path.join(self.place, ".workbench", "manifest.json"))
        with self.assertRaises(target.TargetError):
            self.examine()


class Files(Enroll):
    def test_an_edited_module_owned_file_is_refused_naming_its_path(self):
        self.new_machine()
        self.edit(SCRIPT, lambda data: data + b"# planted\n")
        self.assertIn(SCRIPT, self.refusal("module-owned"))

    def test_a_missing_module_owned_file_is_refused_naming_its_path(self):
        self.new_machine()
        os.unlink(os.path.join(self.place, *SCRIPT.split("/")))
        self.assertIn(SCRIPT, self.refusal("missing"))

    def test_a_module_owned_file_that_is_a_link_is_refused(self):
        self.new_machine()
        full = os.path.join(self.place, *SCRIPT.split("/"))
        os.unlink(full)
        os.symlink("/etc/hosts", full)
        self.assertIn(SCRIPT, self.refusal(SCRIPT))

    def test_a_seeded_file_that_is_a_link_is_refused_naming_its_path(self):
        self.new_machine()
        full = os.path.join(self.place, "docs", "notes.md")
        os.unlink(full)
        os.symlink("/etc/hosts", full)
        self.assertIn("docs/notes.md", self.refusal("docs/notes.md"))

    def test_the_file_holding_the_blocks_as_a_link_is_refused(self):
        self.new_machine()
        full = os.path.join(self.place, "AGENTS.md")
        os.unlink(full)
        os.symlink("/etc/hosts", full)
        self.assertIn("AGENTS.md", self.refusal("AGENTS.md"))

    def test_an_edited_seeded_file_is_listed_and_baselined_at_the_bytes_in_the_clone(self):
        self.new_machine()
        self.edit("AGENTS.md", lambda data: data + b"\nMy own rule.\n")
        plan = self.examine()
        self.assertEqual(["AGENTS.md"], [item.path for item in plan.seeded_differ])
        self.assertEqual(sha(self.read("AGENTS.md")), plan.baselines["AGENTS.md"])
        self.assertIn("differs from the manifest (seeded, yours)", enrollplan.render(plan, self.real))

    def test_a_missing_seeded_file_is_listed_and_has_no_baseline(self):
        self.new_machine()
        os.unlink(os.path.join(self.place, "docs", "notes.md"))
        plan = self.examine()
        self.assertEqual(["docs/notes.md"], [item.path for item in plan.seeded_missing])
        self.assertNotIn("docs/notes.md", plan.baselines)

    def test_an_edited_slot_block_is_listed_and_its_file_is_baselined_whole(self):
        self.new_machine()
        self.edit("AGENTS.md", lambda data: data.replace(b"Rule A", b"Rule X"))
        plan = self.examine()
        self.assertEqual([("AGENTS.md", "p/a", "policy")], [(b.path, b.block, b.slot) for b in plan.blocks_differ])
        self.assertEqual(sha(self.read("AGENTS.md")), plan.baselines["AGENTS.md"])
        self.assertIn("block differs from the manifest (seeded file, yours)", enrollplan.render(plan, self.real))

    def test_a_block_with_its_markers_removed_is_listed(self):
        self.new_machine()
        self.edit("AGENTS.md", lambda data: b"\n".join(
            line for line in data.split(b"\n") if b"slot:policy -->" not in line))
        plan = self.examine()
        self.assertEqual(["AGENTS.md"], [b.path for b in plan.blocks_differ])

    def test_a_block_is_hashed_with_both_marker_lines(self):
        self.new_machine()
        data = self.read("AGENTS.md")
        begin = data.index(b"<!-- BEGIN p/a slot:policy -->")
        end = data.index(b"<!-- END p/a slot:policy -->") + len(b"<!-- END p/a slot:policy -->\n")
        entry = [item for item in manifest.parse(self.read(MANIFEST))["files"] if item.get("block") == "p/a"][0]
        self.assertEqual(entry["hash"], sha(data[begin:end]))
        self.assertEqual([], self.examine().blocks_differ)


class Manifest(Enroll):
    def test_a_path_under_the_scratch_directory_is_refused(self):
        self.new_machine()
        self.put(".workbench/local/x", b"x")
        self.rewrite_manifest(lambda doc: doc["files"].append(
            {"class": "module-owned", "hash": sha(b"x"), "path": ".workbench/local/x"}))
        self.refusal(".workbench/local/x")

    def test_a_module_owned_path_where_no_module_may_write_is_refused_naming_it(self):
        self.new_machine()
        self.put("evil/payload", b"x")
        self.rewrite_manifest(lambda doc: doc["files"].append(
            {"class": "module-owned", "hash": sha(b"x"), "path": "evil/payload"}))
        self.assertIn("evil/payload", self.refusal("may not write"))

    def test_a_module_owned_path_in_a_namespace_the_manifest_does_not_record_is_refused(self):
        self.new_machine()
        self.put(".workbench/q/other/file", b"x")
        self.rewrite_manifest(lambda doc: doc["files"].append(
            {"class": "module-owned", "hash": sha(b"x"), "path": ".workbench/q/other/file"}))
        self.refusal("may not write")

    def test_a_module_owned_path_in_a_declared_write_is_accepted(self):
        self.new_machine()
        notes = [item for item in manifest.parse(self.read(MANIFEST))["files"] if item["path"] == "docs/notes.md"][0]
        self.rewrite_manifest(lambda doc: [item.update({"class": "module-owned"}) for item in doc["files"]
                                           if item["path"] == "docs/notes.md"])
        plan = self.examine()
        self.assertEqual(notes["hash"], plan.baselines["docs/notes.md"])

    def test_a_seeded_path_under_the_workbench_directory_is_refused(self):
        self.new_machine()
        self.put(".workbench/seeded.txt", b"x")
        self.rewrite_manifest(lambda doc: doc["files"].append(
            {"class": "seeded", "hash": sha(b"x"), "path": ".workbench/seeded.txt"}))
        self.refusal("may not write")

    def test_a_block_whose_module_does_not_declare_the_slot_is_refused(self):
        self.new_machine()
        self.rewrite_manifest(lambda doc: [item.update({"slot": "docs-index"}) for item in doc["files"]
                                           if item.get("block") == "p/a" and item["path"] == "AGENTS.md"])
        self.refusal("slot")

    def test_a_declaration_that_differs_from_the_one_the_manifest_records_is_refused(self):
        self.new_machine()

        def change(doc):
            doc["packages"][0]["modules"][0]["declaration"] = "0" * 64
        self.rewrite_manifest(change)
        self.refusal("declaration")

    def test_a_module_whose_declaration_file_is_not_recorded_is_refused(self):
        self.new_machine()
        self.rewrite_manifest(lambda doc: doc["files"].remove(
            [item for item in doc["files"] if item["path"] == ".workbench/p/a/module.json"][0]))
        self.refusal("module.json")

    def test_a_slot_block_in_a_file_the_manifest_does_not_call_seeded_is_refused(self):
        self.new_machine()

        def change(doc):
            for item in doc["files"]:
                if item["path"] == "docs/notes.md":
                    item["class"] = "module-owned"
            doc["files"].append({"block": "p/a", "class": "slot block", "hash": "0" * 64, "path": "docs/notes.md", "slot": "policy"})
        self.rewrite_manifest(change)
        self.assertIn("docs/notes.md", self.refusal("seeded"))

    def test_a_slot_block_with_no_file_entry_for_its_path_is_refused(self):
        self.new_machine()
        self.rewrite_manifest(lambda doc: doc["files"].remove(
            [item for item in doc["files"] if item["path"] == "AGENTS.md" and "block" not in item][0]))
        self.refusal("seeded")

    def test_a_seeded_path_that_neither_the_base_nor_a_declared_write_supplies_is_refused(self):
        self.new_machine()
        self.put("rogue.txt", b"x")
        self.rewrite_manifest(lambda doc: doc["files"].append({"class": "seeded", "hash": sha(b"x"), "path": "rogue.txt"}))
        self.assertIn("rogue.txt", self.refusal("may not write"))

    def test_a_file_holding_blocks_whose_markers_cannot_be_read_is_refused(self):
        self.new_machine()
        self.edit("AGENTS.md", lambda data: data + b"\n<!-- BEGIN p/a slot:policy -->\n")
        self.assertIn("AGENTS.md", self.refusal("AGENTS.md"))

    def test_a_directory_in_place_of_a_recorded_file_is_refused(self):
        self.new_machine()
        full = os.path.join(self.place, *SCRIPT.split("/"))
        os.unlink(full)
        os.mkdir(full)
        self.assertIn(SCRIPT, self.refusal(SCRIPT))

    def test_more_refusals_than_the_limit_are_cut_and_counted(self):
        self.new_machine()
        for rel in (SCRIPT, POLICY, ".workbench/.gitignore"):
            self.edit(rel, lambda data: data + b"# planted\n")
        with unittest.mock.patch.object(enrollplan, "MAX_REFUSED", 2):
            self.assertIn("and 1 more", self.refusal("module-owned"))

    def test_a_recorded_file_that_changes_between_the_two_reads_is_refused(self):
        self.new_machine()
        real_walk = acknowledgement._walk

        def walk_then_change(writer, rel, depth, found):
            real_walk(writer, rel, depth, found)
            self.edit(SCRIPT, lambda data: data + b"# changed in between\n")
        store_before = self.tree(self.store_root)
        with unittest.mock.patch.object(acknowledgement, "_walk", walk_then_change):
            with self.assertRaises(enrollplan.Refused) as caught:
                self.examine()
        text = "\n".join(caught.exception.lines)
        self.assertIn("changed while", text)
        self.assertIn(SCRIPT, text)
        self.assertEqual(store_before, self.tree(self.store_root))

    def test_a_manifest_that_is_not_canonical_is_refused(self):
        self.new_machine()
        self.edit(MANIFEST, lambda data: data.replace(b"\n", b"\r\n", 1))
        self.refusal("manifest")


class Unrecorded(Enroll):
    def test_a_regular_file_the_manifest_does_not_record_is_neither_refused_nor_baselined(self):
        self.new_machine()
        self.put(".workbench/profile.toml", b"profile = 'x'\n")
        plan = self.examine()
        self.assertNotIn(".workbench/profile.toml", plan.baselines)
        self.assertEqual(1, plan.unrecorded_total)
        self.assertIn(".workbench/profile.toml", enrollplan.render(plan, self.real))

    def test_the_summary_counts_a_module_directory_and_lists_it_only_when_it_holds_ten_or_fewer(self):
        self.new_machine()
        for number in range(5):
            self.put(".workbench/p/small/one/f%d" % number, b"x")
            self.put(".workbench/p/small/two/f%d" % number, b"x")
        for number in range(11):
            self.put(".workbench/p/big/f%d" % number, b"x")
        plan = self.examine()
        self.assertEqual(21, plan.unrecorded_total)
        text = enrollplan.render(plan, self.real)
        self.assertIn(".workbench/p/small: 10 files", text)
        self.assertIn(".workbench/p/small/two/f3", text)
        self.assertNotIn(".workbench/p/big/f3", text)
        self.assertIn(".workbench/p/big: 11 files", text)

    def test_many_review_directories_under_one_module_are_one_group(self):
        self.new_machine()
        for review in range(40):
            for name in ("state.json", "ledger.md", "round-1.json"):
                self.put(".workbench/p/records/plan-%02d/%s" % (review, name), b"x")
        plan = self.examine()
        self.assertEqual(120, plan.unrecorded_total)
        self.assertEqual([".workbench/p/records"], sorted(plan.unrecorded))
        text = enrollplan.render(plan, self.real)
        self.assertIn(".workbench/p/records: 120 files", text)
        self.assertNotIn("plan-07/state.json", text)

    def test_the_scratch_directory_is_not_counted(self):
        self.new_machine()
        self.put(".workbench/local/notes", b"mine")
        self.assertEqual(0, self.examine().unrecorded_total)

    def test_a_link_in_the_workbench_directory_is_refused_naming_it(self):
        self.new_machine()
        os.symlink("/etc", os.path.join(self.place, ".workbench", "link"))
        self.assertIn(".workbench/link", self.refusal(".workbench/link"))

    def test_a_pipe_in_the_workbench_directory_is_refused_naming_it(self):
        self.new_machine()
        os.mkfifo(os.path.join(self.place, ".workbench", "pipe"))
        self.assertIn(".workbench/pipe", self.refusal("not a regular file"))

    def test_a_name_that_fails_the_path_rules_is_refused(self):
        self.new_machine()
        self.put(".workbench/bad\nname", b"x")
        self.refusal("not a regular file")

    def test_the_later_command_that_lists_added_files_lists_exactly_these(self):
        self.new_machine()
        self.put(".workbench/p/review/a", b"x")
        self.put(".workbench/p/review/b", b"y")
        plan = self.examine()
        self.guarded.write("projects/%s/baselines" % plan.project, plan.baselines_bytes)
        self.guarded.write("projects/%s/seen" % plan.project, plan.seen_bytes)
        baselines = acknowledgement.read_baselines(self.guarded, plan.project)
        with target.open_target(self.place, self.store_root) as held:
            found = acknowledgement.differences(projectfs.Writer(held), baselines)
        self.assertEqual([(".workbench/p/review/a", "added"), (".workbench/p/review/b", "added")],
                         [(item.path, item.kind) for item in found])


class Hardening(Enroll):
    """What the security review of the command found (plan ``2026-11-15-enroll-a-clone``, increment F): each test failed before its fix."""

    def change_between_the_reads(self, change):
        """Run ``examine`` with `change` made to the clone after the first read of the files and before the second."""
        real_walk = acknowledgement._walk
        done = []

        def walk_then_change(writer, rel, depth, found):
            real_walk(writer, rel, depth, found)
            if rel == ".workbench" and not done:    # the walk calls itself for each directory; the change is made once, after the whole walk
                done.append(1)
                change()
        with unittest.mock.patch.object(acknowledgement, "_walk", walk_then_change):
            with self.assertRaises(enrollplan.Refused) as caught:
                self.examine()
        return "\n".join(caught.exception.lines)

    def test_a_seeded_file_holding_blocks_that_is_tampered_between_the_two_reads_is_refused(self):
        self.new_machine()
        text = self.change_between_the_reads(lambda: self.edit("AGENTS.md", lambda data: data.replace(b"Rule A", b"Rule X")))
        self.assertIn("AGENTS.md", text)
        self.assertIn("changed while", text)

    def test_a_seeded_file_that_changes_between_the_two_reads_is_refused(self):
        self.new_machine()
        text = self.change_between_the_reads(lambda: self.edit("docs/notes.md", lambda data: data + b"mine\n"))
        self.assertIn("docs/notes.md", text)

    def test_a_recorded_file_that_is_removed_between_the_two_reads_is_refused(self):
        self.new_machine()
        text = self.change_between_the_reads(lambda: os.unlink(os.path.join(self.place, *SCRIPT.split("/"))))
        self.assertIn(SCRIPT, text)

    def test_a_recorded_file_that_appears_between_the_two_reads_is_refused(self):
        self.new_machine()
        os.unlink(os.path.join(self.place, "docs", "notes.md"))
        text = self.change_between_the_reads(lambda: self.put("docs/notes.md", b"# Notes\n"))
        self.assertIn("docs/notes.md", text)

    def test_an_older_pins_entry_of_the_same_project_is_refused_and_the_folder_is_named(self):
        self.new_machine()
        self.guarded.write("projects/%s/pins" % self.project_id, pins.serialize({}))
        text = self.refusal("pins")
        self.assertIn("projects/%s/" % self.project_id, text)
        self.assertIn("remove the folder", text)

    def test_an_older_rendering_entry_of_the_same_project_is_refused(self):
        self.new_machine()
        self.guarded.write("projects/%s/rendering" % self.project_id, b"{}\n")
        self.assertIn("rendering", self.refusal("rendering"))

    def test_an_older_plan_approvals_entry_of_the_same_project_is_refused(self):
        self.new_machine()
        self.guarded.write("projects/%s/plan-approvals" % self.project_id, b"{}\n")
        self.assertIn("plan-approvals", self.refusal("plan-approvals"))

    def test_every_entry_the_installer_writes_in_a_project_folder_is_one_the_check_knows(self):
        """A new kind of entry in the folder of a project must be weighed here: the two that `enroll` writes, and the ones it refuses to inherit."""
        names = set()
        folder = os.path.join(ROOT, "workbench")
        for name in sorted(os.listdir(folder)):
            if name.endswith(".py"):
                with open(os.path.join(folder, name), encoding="utf-8") as handle:
                    names.update(re.findall(r"projects/%s/([a-z][a-z-]*)", handle.read()))
        self.assertTrue({"baselines", "seen"} <= names, names)
        self.assertEqual(set(), names - {"baselines", "seen"} - set(enrollplan.STALE_ENTRIES), names)

    def test_a_module_owned_file_at_a_path_the_base_supplies_is_listed_under_the_heading(self):
        import types
        from workbench import declarations, installed
        data = json.dumps({"name": "m", "version": "1.0.0", "description": "d", "writes": ["AGENTS.md", "zz/new.txt"]}).encode()
        module = declarations.parse_module(data, "p", "m", first_party=True)
        entries = [installed.Entry("AGENTS.md", None, None, "module-owned", "0" * 64, installed.AS_INSTALLED, "0" * 64, ""),
                   installed.Entry("zz/new.txt", None, None, "module-owned", "0" * 64, installed.AS_INSTALLED, "0" * 64, "")]
        listed = enrollplan._places(types.SimpleNamespace(entries=entries), {("p", "m"): module})
        self.assertEqual(["AGENTS.md", "zz/new.txt"], sorted(item.path for item in listed))

    def test_the_heading_lists_every_path_even_when_the_baselines_are_cut(self):
        self.new_machine()
        plan = self.examine()
        plan.outside = [enrollplan.Outside("x/f%d" % number, "seeded") for number in range(6)]
        with unittest.mock.patch.object(enrollplan, "MAX_SHOWN", 3):
            text = enrollplan.render(plan, self.real)
        for number in range(6):
            self.assertIn("x/f%d seeded" % number, text)

    def test_the_groups_of_unrecorded_files_are_cut_and_counted(self):
        self.new_machine()
        plan = self.examine()
        plan.unrecorded = {".workbench/g%d" % number: [".workbench/g%d/f" % number] for number in range(10)}
        plan.unrecorded_total = 10
        with unittest.mock.patch.object(enrollplan, "MAX_SHOWN", 3):
            text = enrollplan.render(plan, self.real)
        self.assertIn(".workbench/g0: 1 file", text)
        self.assertNotIn(".workbench/g9: 1 file", text)
        self.assertIn("and 7 more directories", text)

    def test_covered_matches_a_path_its_parents_and_not_a_sibling_with_the_same_start(self):
        self.assertTrue(enrollplan.covered("a/b/c", {"a/b"}))
        self.assertTrue(enrollplan.covered("a/b", {"a/b"}))
        self.assertTrue(enrollplan.covered("a/b/c/d", {"a"}))
        self.assertFalse(enrollplan.covered("a/bc", {"a/b"}))
        self.assertFalse(enrollplan.covered("a", {"a/b"}))
        self.assertFalse(enrollplan.covered("x/y", set()))

    def test_a_path_outside_the_workbench_directory_that_rests_on_a_declaration_is_listed_under_its_own_heading(self):
        self.new_machine()
        plan = self.examine()
        self.assertEqual(["docs/notes.md"], [item.path for item in plan.outside])
        text = enrollplan.render(plan, self.real)
        self.assertIn("on the strength of a module's own declaration", text)
        self.assertEqual(plan.fields["outside"], [["docs/notes.md", "seeded"]])

    def test_the_files_the_base_supplies_are_not_listed_as_resting_on_a_declaration(self):
        self.new_machine()
        self.assertNotIn("AGENTS.md", [item.path for item in self.examine().outside])

    def test_the_list_of_baselines_is_cut_and_counted_and_the_digest_still_covers_them_all(self):
        self.new_machine()
        whole = self.examine()
        with unittest.mock.patch.object(enrollplan, "MAX_SHOWN", 3):
            cut = self.examine()
            text = enrollplan.render(cut, self.real)
        self.assertEqual(whole.digest, cut.digest)
        self.assertIn("and %d more (the digest covers all of them)" % (len(cut.baselines) - 3), text)
        shown = [line for line in text.splitlines() if line.startswith("  ") and line.split()[0] in cut.baselines
                 and line.endswith(cut.baselines[line.split()[0]])]
        self.assertEqual(3, len(shown), shown)


class ThisRepository(Enroll):
    """A copy of this repository's own installed files, read as a clone on a new machine: the read must not refuse it, and must count exactly the
    files it holds under ``.workbench/`` that its manifest does not record (a tracked profile and the review records of its plans and specs)."""

    def copy_in(self):
        with open(os.path.join(ROOT, MANIFEST), "rb") as handle:
            document = manifest.parse(handle.read())
        wanted = {item["path"] for item in document["files"]} | {MANIFEST}
        for base, dirs, files in os.walk(os.path.join(ROOT, ".workbench")):
            if os.path.relpath(base, ROOT) == ".workbench":
                dirs[:] = [name for name in dirs if name != "local"]
            for name in files:
                wanted.add(os.path.relpath(os.path.join(base, name), ROOT).replace(os.sep, "/"))
        for rel in sorted(wanted):
            source = os.path.join(ROOT, *rel.split("/"))
            if os.path.isfile(source):
                full = os.path.join(self.place, *rel.split("/"))
                os.makedirs(os.path.dirname(full), exist_ok=True)
                shutil.copy2(source, full)
        os.makedirs(os.path.join(self.place, ".git"))
        with open(os.path.join(self.place, ".git", "index"), "wb") as handle:
            handle.write(b"index")

    def test_it_is_not_refused_and_the_files_it_does_not_record_are_counted(self):
        self.copy_in()
        plan = self.examine()
        recorded = {item["path"] for item in manifest.parse(self.read(MANIFEST))["files"]} | {MANIFEST}
        held = set()
        for base, dirs, files in os.walk(os.path.join(self.place, ".workbench")):
            if os.path.relpath(base, self.place) == ".workbench":
                dirs[:] = [name for name in dirs if name != "local"]
            held.update(os.path.relpath(os.path.join(base, name), self.place).replace(os.sep, "/") for name in files)
        counted = {path for paths in plan.unrecorded.values() for path in paths}
        self.assertEqual(held - recorded, counted)
        self.assertGreaterEqual(plan.unrecorded_total, 1)
        self.assertIn("files under .workbench/ that the manifest does not record: %d" % plan.unrecorded_total,
                      enrollplan.render(plan, plan.path))
        with open(os.path.join(ROOT, MANIFEST), "rb") as handle:
            self.assertEqual(sha(handle.read()), plan.baselines[MANIFEST])
        self.assertTrue(all(path in plan.baselines for path in
                            [item["path"] for item in manifest.parse(self.read(MANIFEST))["files"]
                             if item["class"] == "module-owned"]))


if __name__ == "__main__":
    unittest.main()
