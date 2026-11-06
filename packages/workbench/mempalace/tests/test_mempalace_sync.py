"""Plan `2026-11-05-mempalace-per-clone-use`, increment E: `sync`, which prunes the drawers of files that are gone or now ignored. `preview sync <dir>`
runs the program's dry run (the program's `sync` with `--dry-run`) and prints its report with a digest; `sync <dir> --confirm --digest <digest>` runs the
program's `sync --apply` only if the digest is that of the report as it is now, checked inside the helper's lock, without a terminal. The wing is the
setting's or the default, never another; no other option exists. A fake `mempalace` is used throughout; no test starts the real program."""

import fcntl
import json
import os
import re
import stat
import unittest
import unittest.mock

import support_mempalace

DIGEST = r"[0-9a-f]{32}"
SOURCES = (("/proj/notes/gone-1.md", 2), ("/proj/notes/gone-2.md", 1))


def sync_text(missing=3, gitignored=0, sources=SOURCES, palace="/somewhere/palace", mode="DRY RUN (no deletions)"):
    """What the real program's `sync` prints, as it did on 2026-11-05 (3.11.0): a header with the palace, wing and project, the counts, and the top five sources."""
    rule = "=" * 55
    lines = ["", rule, "  MemPalace Sync -- Gitignore-aware drawer prune", rule, "  Palace:   %s" % palace, "  Wing:     project",
             "  Project:  /proj/notes", "  Mode:     %s" % mode, "-" * 55, "", "  Scanned:        %d" % (missing + gitignored + 6),
             "  Kept:           6", "  Gitignored:     %d  (would remove)" % gitignored, "  Missing:        %d  (would remove)" % missing,
             "  Unresolved:     0  (kept)", "  No source:      0  (kept)", "  Out of scope:   0  (kept)"]
    if sources:
        lines += ["", "  Top sources to remove:"] + ["    %s  (%d)" % pair for pair in sources]
    if missing + gitignored:
        lines += ["", "  Re-run with --apply to commit these deletions."]
    return "\n".join(lines + ["", rule, ""])


REAL = "  Removed 3 drawers, 2 closets.\n"


class Sync(support_mempalace.Palace):
    def setUp(self):
        support_mempalace.Palace.setUp(self)
        self.corpus = os.path.join(self.base, "corpus")
        os.makedirs(self.corpus)
        self.control(dry_stdout=sync_text(), stdout=REAL)

    def preview(self, *extra, corpus=None):
        """``(the lines between the markers, the digest)`` of a preview that succeeded."""
        code, out, err = self.run_helper("preview", "sync", corpus or self.corpus, *extra)
        self.assertEqual((0, ""), (code, err), err)
        lines = out.splitlines()
        self.assertRegex(lines[0], r"^<<recalled-data [0-9a-f]{12} begin: mempalace preview sync>>$")
        self.assertEqual("<<recalled-data %s end>>" % lines[0].split()[1], lines[-2])
        self.assertRegex(lines[-1], "^digest: %s$" % DIGEST)
        return lines[2:-2], lines[-1].split()[1]

    def confirm(self, digest, *extra, corpus=None):
        return self.run_helper("sync", corpus or self.corpus, *extra, "--confirm", "--digest", digest)

    def real_calls(self):
        return [call for call in self.calls() if "--dry-run" not in call["argv"]]

    def listing(self):
        found = []
        for base, dirs, files in os.walk(self.base):
            if base.startswith(self.outside):
                continue
            found += [os.path.relpath(os.path.join(base, name), self.base) for name in dirs + files]
        return sorted(found)

    def local_setting(self, **fields):
        os.makedirs(os.path.join(self.root, ".workbench", "local"), exist_ok=True)
        with open(os.path.join(self.root, ".workbench", "local", "mempalace.json"), "w") as handle:
            json.dump(dict({"format": 1}, **fields), handle)


class Preview(Sync):
    def test_it_prints_the_report_and_a_digest_runs_only_the_dry_run_and_writes_nothing(self):
        before = self.listing()
        lines, digest = self.preview()
        (call,) = self.calls()
        self.assertEqual(["sync", self.corpus, "--wing", "project", "--dry-run"], call["argv"])
        self.assertNotIn("--apply", call["argv"])
        self.assertEqual("preview of sync", lines[0])
        for line in ("project: %s" % self.root, "directory: %s" % self.corpus, "wing: project", "palace: (the program's own)",
                     "Missing:        3  (would remove)", "/proj/notes/gone-1.md  (2)"):
            self.assertIn(line, lines)
        self.assertTrue([line for line in lines if line.startswith("palaces the program may use: ")], lines)
        self.assertFalse([line for line in lines if "/somewhere/palace" in line or line.startswith("Palace:")])
        self.assertEqual(before, self.listing())
        self.assertEqual([], os.listdir(self.temp))

    def test_the_same_report_gives_the_same_digest_and_a_change_of_what_would_go_changes_it(self):
        _, first = self.preview()
        self.assertEqual(first, self.preview()[1])
        self.control(dry_stdout=sync_text(palace="/another/palace"), stdout=REAL)
        self.assertEqual(first, self.preview()[1])   # the palace line the program prints is the program's own words
        digests = {"base": first}
        self.control(dry_stdout=sync_text(missing=4), stdout=REAL)
        digests["count"] = self.preview()[1]
        self.control(dry_stdout=sync_text(gitignored=1), stdout=REAL)
        digests["ignored"] = self.preview()[1]
        self.control(dry_stdout=sync_text(sources=SOURCES[:1]), stdout=REAL)
        digests["sources"] = self.preview()[1]
        self.control(dry_stdout=sync_text(), stdout=REAL)
        os.makedirs(os.path.join(self.base, "corpus2"))
        digests["directory"] = self.preview(corpus=os.path.join(self.base, "corpus2"))[1]
        self.local_setting(wing="other")
        digests["wing"] = self.preview()[1]
        self.local_setting(palace=os.path.join(self.base, "palace"))
        digests["palace"] = self.preview()[1]
        self.assertEqual(len(digests), len(set(digests.values())), digests)

    def test_a_change_of_the_palace_the_program_would_choose_changes_the_digest(self):
        _, first = self.preview()
        os.makedirs(os.path.join(self.home, ".mempalace"))
        with open(os.path.join(self.home, ".mempalace", "config.json"), "w") as handle:
            handle.write('{"palace_path": "%s"}' % os.path.join(self.base, "other-palace"))
        self.assertNotEqual(first, self.preview()[1])

    def test_the_wing_is_the_settings_or_the_default_and_no_option_names_another(self):
        self.local_setting(wing="chosen")
        lines, _ = self.preview()
        self.assertIn("wing: chosen", lines)
        self.assertEqual(["sync", self.corpus, "--wing", "chosen", "--dry-run"], self.calls()[0]["argv"])
        for option, value in (("--wing", "project"), ("--mode", "convos"), ("--root", self.root), ("--apply", None), ("--dry-run", None),
                              ("--direct", None), ("--allow-project-root", None)):
            code, out, err = self.run_helper("preview", "sync", self.corpus, *([option] + ([value] if value else [])))
            self.assertEqual((1, ""), (code, out), err)
            self.assertIn("is not an option of sync", err)
        self.assertEqual(1, len(self.calls()))

    def test_a_long_report_is_cut_but_the_digest_covers_all_of_it_and_a_long_line_says_it_was_cut(self):
        crowd = "\n".join("    /proj/notes/line-%03d.md  (1)" % n for n in range(300))
        self.control(dry_stdout=sync_text() + crowd + "\n", stdout=REAL)
        lines, first = self.preview()
        self.assertLess(len(lines), 150)
        self.assertTrue([line for line in lines if re.match(r"\(\d+ more lines not shown", line)], lines)
        self.control(dry_stdout=sync_text() + crowd.replace("(1)", "(2)", 1) + "\n", stdout=REAL)
        self.assertNotEqual(first, self.preview()[1])
        self.control(dry_stdout=sync_text(sources=((("e" * 400) + ".md", 1),)), stdout=REAL)
        lines, _ = self.preview()
        self.assertTrue([line for line in lines if line.endswith("...") and len(line) == 303], lines)

    def test_control_characters_in_the_report_are_removed(self):
        self.control(dry_stdout=sync_text(sources=(("/a\x1b[31mb\x07c‮d.md", 1),)), stdout=REAL)
        lines, _ = self.preview()
        for bad in ("\x1b", "\x07", "‮"):
            self.assertFalse([line for line in lines if bad in line])

    def test_an_uncached_model_is_refused_so_that_an_agent_never_starts_a_download(self):
        for name in self.helper.MODEL_FILES:
            os.remove(os.path.join(self.home, *self.helper.MODEL_DIR, name))
        self.refused("preview", "sync", self.corpus, contains="not cached")
        self.refused("sync", self.corpus, "--confirm", "--digest", "0" * 32, contains="not cached")
        self.assertFalse(os.path.exists(os.path.join(self.home, ".mempalace")))

    def test_the_folder_rules_of_mine_apply_to_the_preview(self):
        os.symlink(self.corpus, os.path.join(self.base, "linked"))
        planted = os.path.join(self.base, "planted")
        os.makedirs(planted)
        os.symlink(os.path.join(self.base, "nothing"), os.path.join(planted, "mempalace.yaml"))
        os.makedirs(os.path.join(self.root, ".git", "x"))
        palace = os.path.join(self.corpus, "store")
        os.makedirs(palace)
        for target, word in ((self.root, "project root"), (os.path.join(self.base, "linked"), "link"),
                             (planted, "would write through it"), (os.path.join(self.root, ".git", "x"), ".git or .workbench"),
                             (os.path.join(self.base, "nothing"), "does not exist")):
            self.refused("preview", "sync", target, contains=word)
        self.local_setting(palace=palace)
        self.refused("preview", "sync", self.corpus, contains="same place or one holds the other")

    def test_the_arguments_are_checked(self):
        self.refused("preview", "sync", contains="needs the directory")
        self.refused("preview", "sync", self.corpus, "--confirm", contains="--confirm is not an option of preview")
        self.refused("preview", "sync", self.corpus, "--digest", "0" * 32, contains="is not an option")
        self.refused("preview", "sync", self.corpus, self.corpus, contains="exactly one directory")
        self.refused("preview", "other", self.corpus, contains="preview takes mine or sync")

    def test_a_program_that_fails_gives_no_digest_and_a_missing_one_is_refused_in_the_owners_words(self):
        self.control(code=1, stdout="boom\n", stderr="err words\n")
        code, out, err = self.run_helper("preview", "sync", self.corpus)
        self.assertEqual(1, code)
        self.assertTrue(err.startswith("failed: "), err)
        self.assertIn("err words", out)
        self.assertNotIn("digest:", out)
        os.remove(os.path.join(self.outside, "mempalace"))
        code, out, err = self.run_helper("preview", "sync", self.corpus)
        self.assertEqual(1, code)
        self.assertIn("not found in a trusted PATH entry", err)
        self.assertNotIn("skipped", err)

    def test_it_takes_no_lock_and_makes_no_directory_for_one(self):
        self.preview()
        self.assertFalse(os.path.exists(os.path.join(self.home, ".mempalace")))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))


class Run(Sync):
    def test_a_run_with_the_digest_of_the_preview_applies_without_a_terminal_and_prints_the_tail_framed(self):
        _, digest = self.preview()
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        (real,) = self.real_calls()
        self.assertEqual(["sync", self.corpus, "--wing", "project", "--apply"], real["argv"])
        self.assertEqual([False, False, False], real["tty"])
        lines = out.split("\n")
        self.assertRegex(lines[0], r"^<<recalled-data [0-9a-f]{12} begin: mempalace sync>>$")
        self.assertEqual("<<recalled-data %s end>>" % lines[0].split()[1], lines[-2])
        self.assertIn("Removed 3 drawers", out)
        self.assertEqual(3, len(self.calls()))   # the preview, the check inside the lock, the run

    def test_a_wrong_digest_or_a_report_that_changed_after_the_preview_removes_nothing(self):
        _, digest = self.preview()
        code, out, err = self.confirm("0" * 32)
        self.assertEqual(1, code)
        self.assertIn(self.helper.digest.MISMATCH, err)
        self.assertIn("nothing was removed", err)
        self.control(dry_stdout=sync_text(missing=9), stdout=REAL)
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn(self.helper.digest.MISMATCH, err)
        self.assertEqual([], self.real_calls())

    def test_a_digest_goes_with_confirm_and_must_be_32_lowercase_hexadecimal_characters(self):
        self.refused("sync", self.corpus, "--digest", "0" * 32, contains="--confirm")
        for bad in ("zz", "0" * 31, "0" * 33, "A" * 32):
            code, out, err = self.run_helper("sync", self.corpus, "--confirm", "--digest", bad)
            self.assertEqual(1, code, bad)
            self.assertIn(self.helper.digest.SHAPE, err)
        self.refused("sync", self.corpus, "--digest", "0" * 32, "--confirm", contains="is not an option")
        self.assertEqual([], self.calls())

    def test_no_other_option_is_accepted_and_the_wing_is_the_settings(self):
        _, digest = self.preview()
        for extra in (("--wing", "other"), ("--apply",), ("--mode", "convos"), ("--allow-project-root",), ("--root", self.root)):
            code, out, err = self.run_helper("sync", self.corpus, *extra, "--confirm", "--digest", digest)
            self.assertEqual(1, code, extra)
            self.assertIn("is not an option of sync", err)
        self.assertEqual([], self.real_calls())
        self.local_setting(wing="chosen")
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        self.assertEqual(["sync", self.corpus, "--wing", "chosen", "--apply"], self.real_calls()[0]["argv"])

    def test_without_a_digest_a_terminal_is_needed_a_dry_run_there_applies_nothing_and_a_confirmed_one_applies(self):
        self.refused("sync", self.corpus, "--confirm", contains="only from a terminal")
        self.refused("sync", self.corpus, contains="only from a terminal")
        code, shown = self.owner("sync", self.corpus)
        self.assertEqual(0, code, shown)
        self.assertEqual([], self.real_calls())
        self.assertEqual(["sync", self.corpus, "--wing", "project", "--dry-run"], self.calls()[0]["argv"])
        self.assertIn("dry run", shown)
        code, shown = self.owner("sync", self.corpus, "--confirm")
        self.assertEqual(0, code, shown)
        self.assertEqual(["sync", self.corpus, "--wing", "project", "--apply"], self.real_calls()[0]["argv"])
        self.assertEqual([True, True, True], self.real_calls()[0]["tty"])

    def test_a_digest_at_a_terminal_runs_the_same_checked_way(self):
        _, digest = self.preview()
        code, shown = self.owner("sync", self.corpus, "--confirm", "--digest", digest)
        self.assertEqual(0, code, shown)
        self.assertIn("Removed 3 drawers", shown)
        self.assertEqual([False, False, False], self.real_calls()[0]["tty"])

    def test_the_folder_rules_apply_to_a_run_with_a_digest(self):
        _, digest = self.preview()
        before = len(self.calls())
        code, out, err = self.confirm(digest, corpus=self.root)
        self.assertEqual(1, code)
        self.assertIn("project root", err)
        self.assertEqual(before, len(self.calls()))
        os.symlink(self.corpus, os.path.join(self.base, "linked"))
        planted = os.path.join(self.base, "planted")
        os.makedirs(planted)
        os.symlink(os.path.join(self.base, "nothing"), os.path.join(planted, "mempalace.yaml"))
        os.makedirs(os.path.join(self.root, ".git", "x"))
        palace = os.path.join(self.corpus, "store")
        os.makedirs(palace)
        for target, word in ((os.path.join(self.base, "linked"), "link"), (planted, "would write through it"),
                             (os.path.join(self.root, ".git", "x"), ".git or .workbench")):
            code, out, err = self.confirm(digest, corpus=target)
            self.assertEqual(1, code, target)
            self.assertIn(word, err)
        self.local_setting(palace=palace)
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn("same place or one holds the other", err)
        self.assertEqual(before, len(self.calls()))

    def test_with_no_wing_to_work_on_nothing_is_run_because_the_program_would_then_take_every_wing(self):
        """Found by the review of increment E: the sharpest safety property of `sync` was not pinned."""
        with unittest.mock.patch.object(self.helper, "default_wing", return_value=None):
            self.refused("preview", "sync", self.corpus, contains="one wing")
            self.refused("sync", self.corpus, "--confirm", "--digest", "0" * 32, contains="one wing")

    def test_a_program_that_fails_is_a_failure_with_its_words_and_no_second_run(self):
        _, digest = self.preview()
        self.control(dry_stdout=sync_text(), stdout="oops\n", code_real=2)
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn("exited with code 2", err)
        self.assertIn("oops", out)
        self.assertEqual(1, len(self.real_calls()))

    def test_a_long_output_is_cut_to_its_tail_and_control_characters_are_removed(self):
        _, digest = self.preview()
        self.control(dry_stdout=sync_text(), stdout=REAL + "a\x1b[31mb\x07c\x00d‮e\n", real_bytes=2 * 1048576 + 10)
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        self.assertLess(len(out), self.helper.MAX_TEXT + 1000)
        self.assertIn("[earlier output cut]", out)
        for bad in ("\x1b", "\x07", "\x00", "‮"):
            self.assertNotIn(bad, out)

    def test_it_says_nothing_about_files_left_in_the_folder_and_the_helper_deletes_nothing(self):
        _, digest = self.preview()
        self.control(dry_stdout=sync_text(), stdout=REAL, write={os.path.join(self.corpus, "mempalace.yaml"): "x"})
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        self.assertTrue(os.path.exists(os.path.join(self.corpus, "mempalace.yaml")))
        self.assertNotIn("left", err)


class Lock(Sync):
    def lock_path(self):
        return os.path.join(self.home, ".mempalace", "mempalace-helper.lock")

    def hold(self):
        os.makedirs(os.path.dirname(self.lock_path()), exist_ok=True)
        descriptor = os.open(self.lock_path(), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        self.addCleanup(os.close, descriptor)

    def free(self):
        descriptor = os.open(self.lock_path(), os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(descriptor)

    def test_a_held_lock_refuses_a_run_at_once_before_any_program_is_started(self):
        _, digest = self.preview()
        self.hold()
        before = len(self.calls())
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn("another mempalace run is in progress", err)
        code, shown = self.owner("sync", self.corpus, "--confirm")
        self.assertEqual(1, code)
        self.assertIn("another mempalace run is in progress", shown)
        self.assertEqual(before, len(self.calls()))

    def test_a_preview_and_a_dry_run_do_not_wait_for_the_lock(self):
        self.hold()
        self.assertTrue(self.preview()[1])
        self.assertEqual(0, self.owner("sync", self.corpus)[0])

    def test_a_run_makes_the_lock_private_and_frees_it_after_a_run_a_refusal_and_a_failure(self):
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        self.assertEqual(0o700, stat.S_IMODE(os.stat(os.path.dirname(self.lock_path())).st_mode))
        self.assertEqual(0o600, stat.S_IMODE(os.stat(self.lock_path()).st_mode))
        self.free()
        self.assertEqual(1, self.confirm("0" * 32)[0])
        self.free()
        self.control(dry_stdout=sync_text(), stdout="oops\n", code_real=2)
        self.assertEqual(1, self.confirm(digest)[0])
        self.free()

    def test_a_link_in_place_of_the_lock_is_refused_and_nothing_is_written_through_it(self):
        victim = os.path.join(self.base, "victim.txt")
        with open(victim, "w") as handle:
            handle.write("ORIGINAL\n")
        os.makedirs(os.path.dirname(self.lock_path()))
        os.symlink(victim, self.lock_path())
        _, digest = self.preview()
        before = len(self.calls())
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertTrue(err.startswith("refused: "), err)
        self.assertEqual(before, len(self.calls()))
        with open(victim) as handle:
            self.assertEqual("ORIGINAL\n", handle.read())

    def test_a_machine_without_the_program_gets_no_directory_and_no_lock(self):
        _, digest = self.preview()
        os.remove(os.path.join(self.outside, "mempalace"))
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn("not found in a trusted PATH entry", err)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".mempalace")))


if __name__ == "__main__":
    unittest.main()
