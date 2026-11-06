"""Plan `2026-11-05-mempalace-per-clone-use`, increment F: the findings of the security review of increments D and E.

The folder rules of `mine` and `sync` compare places, not spellings. On a volume that ignores case (macOS by default) or composes and decomposes
letters, `.GIT`, the project root in capitals or the palace in another case named the same place as the refused spelling and walked round the rules.
The folder is also checked again just before the program starts, so a folder swapped for a link after the digest was checked is refused. A fake
`mempalace` is used throughout; no test starts the real program."""

import json
import os
import unittest
import unittest.mock

import support_mempalace

DIGEST = r"[0-9a-f]{32}"


def swapcase_last(path):
    head, tail = os.path.split(path)
    return os.path.join(head, tail.swapcase())


class Spelling(support_mempalace.Palace):
    def setUp(self):
        support_mempalace.Palace.setUp(self)
        self.corpus = os.path.join(self.base, "corpus")
        os.makedirs(self.corpus)
        os.makedirs(os.path.join(self.root, ".workbench", "local"), exist_ok=True)
        self.folds = os.path.exists(os.path.join(self.base, "CORPUS"))   # false on a volume that tells the cases apart

    def palace_at(self, palace):
        os.makedirs(palace, exist_ok=True)
        with open(os.path.join(self.root, ".workbench", "local", "mempalace.json"), "w") as handle:
            json.dump({"format": 1, "palace": palace}, handle)

    def both_refuse(self, path):
        """`mine` and `sync` refuse `path`, in a preview and from a terminal, and no program is started."""
        for command in ("mine", "sync"):
            err = self.refused("preview", command, path)
            self.assertNotIn("Traceback", err)
            code, shown = self.owner(command, path)
            self.assertEqual(1, code, shown)
            self.assertIn("refused: ", shown)
            self.assertEqual([], self.calls(), "the program was started for %s %s" % (command, path))

    def both_accept(self, path):
        for command in ("mine", "sync"):
            code, out, err = self.run_helper("preview", command, path)
            self.assertEqual((0, ""), (code, err), err)
        self.assertTrue(self.calls())

    def test_the_spellings_of_git_and_the_workbench_directory_in_another_case_are_refused(self):
        for name in (".GIT", ".Git", ".WORKBENCH", ".WorkBench", os.path.join(".WorkBench", "local"),
                     os.path.join(".workbench", "LOCAL"), os.path.join(".GIT", "objects")):
            full = os.path.join(self.root, name)
            if self.folds or os.path.isdir(full):
                os.makedirs(os.path.join(self.root, ".git", "objects"), exist_ok=True)
                self.both_refuse(full)

    def test_a_nested_git_directory_in_another_case_is_refused(self):
        os.makedirs(os.path.join(self.root, "docs", "vendor", ".git"))
        self.both_refuse(os.path.join(self.root, "docs", "VENDOR", ".GIT"))

    def test_the_project_root_and_a_directory_holding_it_in_another_case_need_the_flag(self):
        for spelled in (swapcase_last(self.root), swapcase_last(self.base)):
            if not self.folds and not os.path.isdir(spelled):
                continue
            err = self.refused("preview", "mine", spelled)
            self.assertIn("--allow-project-root", err)
            self.refused("preview", "sync", spelled)
            code, shown = self.owner("mine", spelled)
            self.assertEqual(1, code, shown)
            self.assertEqual([], self.calls())

    def test_the_palace_a_folder_inside_it_and_a_folder_holding_it_in_another_case_are_refused(self):
        palace = os.path.join(self.corpus, "store")
        self.palace_at(palace)
        os.makedirs(os.path.join(palace, "sub"))
        for spelled in (os.path.join(self.corpus, "STORE"), os.path.join(self.corpus, "Store", "SUB"), swapcase_last(self.corpus)):
            if self.folds or os.path.isdir(spelled):
                self.both_refuse(spelled)

    def test_the_program_s_default_palace_in_another_case_is_refused(self):
        palace = os.path.join(self.home, ".mempalace", "palace")
        os.makedirs(palace)
        for spelled in (os.path.join(self.home, ".MEMPALACE", "PALACE"), os.path.join(self.home, ".MEMPALACE")):
            if self.folds or os.path.isdir(spelled):
                self.both_refuse(spelled)

    def test_letters_composed_and_decomposed_name_one_place(self):
        composed = os.path.join(self.base, "palé")
        decomposed = os.path.join(self.base, "palé")
        self.palace_at(composed)
        if not os.path.isdir(decomposed):
            self.skipTest("this volume tells composed and decomposed letters apart")
        self.both_refuse(decomposed)
        self.both_refuse(composed)

    def test_a_name_that_only_looks_like_one_of_these_is_still_accepted(self):
        palace = os.path.join(self.base, "palace")
        self.palace_at(palace)
        for name in (os.path.join(self.base, "palace2"), os.path.join(self.base, "Palace-notes"),
                     os.path.join(self.root, ".github"), os.path.join(self.root, ".gitignored"),
                     os.path.join(self.root, ".workbench-notes")):
            os.makedirs(name, exist_ok=True)
            self.both_accept(name)
            self.assertEqual(name, self.calls()[-1]["argv"][1])

    def test_the_exact_spellings_are_still_refused_with_their_old_messages(self):
        self.palace_at(os.path.join(self.base, "palace"))
        self.assertIn(".git or .workbench", self.refused("preview", "mine", os.path.join(self.root, ".git")))
        self.assertIn("--allow-project-root", self.refused("preview", "mine", self.root))
        self.assertIn("palace", self.refused("preview", "sync", os.path.join(self.base, "palace")))

    def test_a_confirmed_run_at_ask_cannot_be_pointed_at_a_spelling_of_git(self):
        if not self.folds:
            self.skipTest("this volume tells the cases apart")
        spelled = os.path.join(self.root, ".GIT")
        self.refused("preview", "mine", spelled)
        code, out, err = self.run_helper("mine", spelled, "--confirm", "--digest", "0" * 32)
        self.assertEqual(1, code, err)
        self.assertEqual([], self.calls())


class Places(support_mempalace.Palace):
    """The comparison itself, on any volume: it does not depend on the volume folding the names."""

    def test_a_guarded_name_is_found_in_any_case_and_composition_between_a_path_and_the_root(self):
        h = self.helper
        for name in (".git", ".GIT", ".Git", ".workbench", ".WORKBENCH", ".WorkBench"):
            self.assertTrue(h.in_guarded_name(os.path.join(self.root, name), self.root), name)
            self.assertTrue(h.in_guarded_name(os.path.join(self.root, name, "x", "y"), self.root), name)
            self.assertTrue(h.in_guarded_name(os.path.join(self.root, "docs", "v", name), self.root), name)
        for name in (".github", ".gitignored", ".workbench-notes", "git", "docs"):
            self.assertFalse(h.in_guarded_name(os.path.join(self.root, name), self.root), name)
        self.assertFalse(h.in_guarded_name(self.root, self.root))

    def test_a_boundary_that_does_not_exist_is_compared_by_its_folded_spelling(self):
        h = self.helper
        gone = os.path.join(self.base, "Pal\u00e9")
        for spelled in (gone, os.path.join(self.base, "PALE\u0301"), os.path.join(self.base, "palé", "sub")):
            self.assertTrue(h.within(spelled, gone), spelled)
        for other in (os.path.join(self.base, "pale2"), os.path.join(self.base, "pal"), self.base):
            self.assertFalse(h.within(other, gone), other)

    def test_a_boundary_that_exists_is_compared_by_identity_so_a_distinct_name_is_never_folded_into_it(self):
        h = self.helper
        os.makedirs(os.path.join(self.base, "Alpha"))
        os.makedirs(os.path.join(self.base, "alphabet"))
        self.assertFalse(h.within(os.path.join(self.base, "alphabet"), os.path.join(self.base, "Alpha")))
        self.assertTrue(h.within(os.path.join(self.base, "Alpha", "x"), os.path.join(self.base, "Alpha")))


class Recheck(support_mempalace.Palace):
    """The folder is examined again after the digest is verified and just before the program is started."""

    def setUp(self):
        support_mempalace.Palace.setUp(self)
        self.corpus = os.path.join(self.base, "corpus")
        os.makedirs(self.corpus)
        with open(os.path.join(self.corpus, "a.md"), "w") as handle:
            handle.write("# a\n")
        self.elsewhere = os.path.join(self.base, "elsewhere")
        os.makedirs(self.elsewhere)
        with open(os.path.join(self.elsewhere, "a.md"), "w") as handle:
            handle.write("# a\n")
        self.control(dry_stdout="Scanned: 1\nWould file: 1\n", stdout="Filed 1 drawers.\n")

    def digest(self, command="mine"):
        code, out, err = self.run_helper("preview", command, self.corpus)
        self.assertEqual((0, ""), (code, err), err)
        return out.strip().splitlines()[-1].split()[1]

    def real_calls(self):
        return [call for call in self.calls() if "--dry-run" not in call["argv"]]

    def swap_after_the_digest_check(self, how):
        real = self.helper.digest.mismatch
        done = []

        def mismatch(*args, **kwargs):
            result = real(*args, **kwargs)
            if not done:
                done.append(True)
                how()
            return result

        patch = unittest.mock.patch.object(self.helper.digest, "mismatch", mismatch)
        patch.start()
        self.addCleanup(patch.stop)

    def to_a_link(self):
        os.rename(self.corpus, self.corpus + ".old")
        os.symlink(self.elsewhere, self.corpus)

    def to_another_directory(self):
        os.rename(self.corpus, self.corpus + ".old")
        os.makedirs(self.corpus)
        with open(os.path.join(self.corpus, "a.md"), "w") as handle:
            handle.write("# a\n")

    def test_a_folder_swapped_for_a_link_after_the_digest_check_is_refused_and_nothing_is_started(self):
        digest = self.digest()
        self.swap_after_the_digest_check(self.to_a_link)
        code, out, err = self.run_helper("mine", self.corpus, "--confirm", "--digest", digest)
        self.assertEqual((1, ""), (code, out), err)
        self.assertIn("refused: ", err)
        self.assertEqual([], self.real_calls())

    def test_a_folder_swapped_for_another_directory_of_the_same_name_is_refused_and_nothing_is_started(self):
        digest = self.digest()
        self.swap_after_the_digest_check(self.to_another_directory)
        code, out, err = self.run_helper("mine", self.corpus, "--confirm", "--digest", digest)
        self.assertEqual((1, ""), (code, out), err)
        self.assertIn("changed", err)
        self.assertIn("nothing was filed", err)
        self.assertEqual([], self.real_calls())
        self.assertEqual([], os.listdir(self.temp), "the scratch directory was left")

    def test_the_same_for_sync_says_that_nothing_was_removed(self):
        self.control(dry_stdout="Scanned: 1\nMissing: 0  (would remove)\n", stdout="Removed 0 drawers.\n")
        digest = self.digest("sync")
        self.swap_after_the_digest_check(self.to_another_directory)
        code, out, err = self.run_helper("sync", self.corpus, "--confirm", "--digest", digest)
        self.assertEqual(1, code, err)
        self.assertIn("nothing was removed", err)
        self.assertEqual([], self.real_calls())

    def test_a_folder_swapped_after_a_terminal_confirm_is_refused_too(self):
        # no digest at a terminal: the swap happens in the first call that reads the folder after the lock
        real = self.helper.Lock.__enter__
        done = []

        def entered(lock):
            result = real(lock)
            if not done:
                done.append(True)
                self.to_another_directory()
            return result

        with unittest.mock.patch.object(self.helper.Lock, "__enter__", entered):
            code, shown = self.owner("mine", self.corpus, "--confirm")
        self.assertEqual(1, code, shown)
        self.assertIn("changed", shown)
        self.assertEqual([], self.real_calls())

    def test_an_unchanged_folder_still_runs(self):
        digest = self.digest()
        code, out, err = self.run_helper("mine", self.corpus, "--confirm", "--digest", digest)
        self.assertEqual(0, code, err)
        self.assertEqual(1, len(self.real_calls()))


if __name__ == "__main__":
    unittest.main()
