"""Plan `2026-11-05-mempalace-per-clone-use`, increment G: the Low findings of the security review of increment F.

The program's own configuration (`~/.config/mempalace/config.json`, `~/.mempalace/config.json`) names a palace the helper must not mine into. It may be a
link (a dotfile manager makes it one), which is followed for that one read; a saved path that cannot be a path is skipped and never ends in a traceback;
a held lock says that a process the program left behind may be the one holding it. A fake `mempalace` is used throughout."""

import fcntl
import json
import os
import unittest
import unittest.mock

import support_mempalace

PLACES = ((".config", "mempalace"), (".mempalace",))


class Config(support_mempalace.Palace):
    def setUp(self):
        support_mempalace.Palace.setUp(self)
        self.corpus = os.path.join(self.base, "corpus")
        self.store = os.path.join(self.corpus, "store")
        self.other = os.path.join(self.base, "other")
        for folder in (self.store, self.other):
            os.makedirs(folder)
        self.dotfiles = os.path.join(self.base, "dotfiles")
        os.makedirs(self.dotfiles)

    def config_path(self, where):
        return os.path.join(self.home, *where, "config.json")

    def write_config(self, where, text):
        os.makedirs(os.path.dirname(self.config_path(where)), exist_ok=True)
        with open(self.config_path(where), "w") as handle:
            handle.write(text)

    def link_config(self, where, target):
        os.makedirs(os.path.dirname(self.config_path(where)), exist_ok=True)
        os.symlink(target, self.config_path(where))

    def real_config(self, text):
        path = os.path.join(self.dotfiles, "config.json")
        with open(path, "w") as handle:
            handle.write(text)
        return path

    def both_refuse_overlap(self, folder):
        for command in ("mine", "sync"):
            err = self.refused("preview", command, folder)
            self.assertIn("palace", err)
            code, shown = self.owner(command, folder)
            self.assertEqual(1, code, shown)
            self.assertIn("refused: ", shown)
            self.assertEqual([], self.calls())

    def both_accept(self, folder):
        for command in ("mine", "sync"):
            code, out, err = self.run_helper("preview", command, folder)
            self.assertEqual((0, ""), (code, err), err)

    def test_a_configuration_that_is_a_link_is_followed_so_the_palace_it_names_is_still_guarded(self):
        target = self.real_config(json.dumps({"palace_path": self.store}))
        for where in PLACES:
            self.link_config(where, target)
            self.both_refuse_overlap(self.corpus)    # the folder holds the palace
            self.both_refuse_overlap(self.store)     # the folder is the palace
            os.remove(self.config_path(where))

    def test_the_preview_lists_the_palace_a_linked_configuration_names(self):
        self.link_config(PLACES[0], self.real_config(json.dumps({"palace_path": self.store})))
        code, out, err = self.run_helper("preview", "mine", self.other)
        self.assertEqual((0, ""), (code, err), err)
        self.assertIn(self.store, out)

    def test_a_link_that_leads_nowhere_useful_adds_nothing_and_refuses_nothing_else(self):
        elsewhere = os.path.join(self.base, "somewhere")
        os.makedirs(elsewhere)
        broken = os.path.join(self.base, "no-such-file")
        notjson = self.real_config("this is not json")
        for target in (broken, elsewhere, notjson):
            for where in PLACES:
                self.link_config(where, target)
                self.both_accept(self.other)
                self.both_accept(self.corpus)    # holds a folder that is no palace of the configuration's
                os.remove(self.config_path(where))

    def test_a_saved_path_that_cannot_be_a_path_is_skipped_and_ends_in_no_traceback(self):
        for text in ('{"palace_path": "\\ud800x"}', '{"palace_path": "a\\u0000b"}', '{"palace_path": 7}'):
            self.write_config(PLACES[0], text)
            self.both_accept(self.corpus)
            code, shown = self.owner("mine", self.corpus)
            self.assertEqual(0, code, shown)
            self.assertNotIn("Traceback", shown)
            _, out, _ = self.run_helper("preview", "mine", self.corpus)
            digest = out.strip().splitlines()[-1].split()[1]
            code, out, err = self.run_helper("mine", self.corpus, "--confirm", "--digest", digest)
            self.assertEqual(0, code, err)

    def test_a_relative_saved_path_is_not_compared_against_a_place_that_is_not_the_programs(self):
        self.write_config(PLACES[0], json.dumps({"palace_path": "corpus/store"}))   # relative to the project folder's parent, in the test's cwd
        _, out, _ = self.run_helper("preview", "mine", self.other)
        self.assertNotIn("corpus/store", out)
        self.both_accept(self.corpus)
        self.write_config(PLACES[0], json.dumps({"palace_path": "~/.mempalace/saved"}))
        self.assertIn(os.path.join(self.home, ".mempalace", "saved"), self.run_helper("preview", "mine", self.other)[1])

    def test_a_configuration_changed_between_the_digest_check_and_the_start_ends_in_no_traceback(self):
        self.write_config(PLACES[0], json.dumps({"palace_path": os.path.join(self.base, "elsewhere")}))
        _, out, _ = self.run_helper("preview", "mine", self.corpus)
        digest = out.strip().splitlines()[-1].split()[1]
        real = self.helper.digest.mismatch

        def mismatch(*args, **kwargs):
            result = real(*args, **kwargs)
            self.write_config(PLACES[0], '{"palace_path": "\\ud800x"}')
            return result

        with unittest.mock.patch.object(self.helper.digest, "mismatch", mismatch):
            code, out, err = self.run_helper("mine", self.corpus, "--confirm", "--digest", digest)
        self.assertIn(code, (0, 1), err)
        self.assertNotIn("Traceback", err)

    def test_a_refused_lock_says_that_a_process_the_program_left_behind_may_still_hold_it(self):
        _, out, _ = self.run_helper("preview", "mine", self.corpus)
        digest = out.strip().splitlines()[-1].split()[1]
        folder = os.path.join(self.home, ".mempalace")
        os.makedirs(folder, exist_ok=True)
        descriptor = os.open(os.path.join(folder, "mempalace-helper.lock"), os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, descriptor)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        before = len(self.calls())
        code, out, err = self.run_helper("mine", self.corpus, "--confirm", "--digest", digest)
        self.assertEqual(1, code)
        self.assertEqual(1, err.count("\n"), err)
        self.assertIn("another mempalace run is in progress", err)
        self.assertIn("may still hold", err)
        self.assertEqual(before, len(self.calls()))


if __name__ == "__main__":
    unittest.main()
