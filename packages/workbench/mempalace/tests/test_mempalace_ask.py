"""Plan `2026-11-05-mempalace-per-clone-use`, increment D: `mine` at the level `ask`. `preview mine <dir>` runs the program's dry run and prints
what it would file with a digest; `mine <dir> --confirm --digest <digest>` runs only if the digest is that of the preview as it is now, checked
inside the helper's lock, without a terminal; a run without a digest still needs one. After a `mine` the helper says if the program left one of the
files `init` writes. A fake `mempalace` is used throughout; no test starts the real program."""

import fcntl
import os
import re
import shutil
import signal
import stat
import sys
import time
import unittest
import unittest.mock

import support_mempalace

DIGEST = r"[0-9a-f]{32}"
FILES = (("a.md", 2), ("b.md", 3))


def dry_text(files=FILES, device="coreml", palace="/somewhere/palace"):
    """What the real program's dry run prints, as it did on 2026-11-05 (3.11.0): a header, one line per file in no fixed order, a summary."""
    rule = "=" * 55
    lines = ["", rule, "  MemPalace Mine", rule, "  Wing:    project", "  Rooms:   general", "  Files:   %d" % len(files),
             "  Palace:  %s" % palace, "  Device:  %s" % device, "  DRY RUN -- nothing will be filed", "-" * 55, ""]
    lines += ["    [DRY RUN] %s -> room:general (%d drawers)" % (name, count) for name, count in files]
    lines += ["", rule, "  Done.", "  Files processed: %d" % len(files), "  Drawers filed: %d" % sum(c for _, c in files), "",
              "  By room:", "    general              %d files" % len(files), "", rule, ""]
    return "\n".join(lines)


REAL = "  Done.\n  Files processed: 2\n  Drawers filed: 5\n"


class Ask(support_mempalace.Palace):
    def setUp(self):
        support_mempalace.Palace.setUp(self)
        self.corpus = os.path.join(self.base, "corpus")
        os.makedirs(self.corpus)
        self.control(dry_stdout=dry_text(), stdout=REAL)

    def preview(self, *extra, corpus=None):
        """``(the lines between the markers, the digest)`` of a preview that succeeded: the lines are framed as data, and the digest is last."""
        code, out, err = self.run_helper("preview", "mine", corpus or self.corpus, *extra)
        self.assertEqual((0, ""), (code, err), err)
        lines = out.splitlines()
        self.assertRegex(lines[0], r"^<<recalled-data [0-9a-f]{12} begin: mempalace preview mine>>$")
        self.assertEqual("<<recalled-data %s end>>" % lines[0].split()[1], lines[-2])
        self.assertRegex(lines[-1], "^digest: %s$" % DIGEST)
        return lines[2:-2], lines[-1].split()[1]

    def confirm(self, digest, *extra, corpus=None):
        return self.run_helper("mine", corpus or self.corpus, *extra, "--confirm", "--digest", digest)

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
        import json
        os.makedirs(os.path.join(self.root, ".workbench", "local"), exist_ok=True)
        with open(os.path.join(self.root, ".workbench", "local", "mempalace.json"), "w") as handle:
            json.dump(dict({"format": 1}, **fields), handle)


class Preview(Ask):
    def test_it_prints_the_lines_and_a_digest_and_writes_nothing(self):
        before = self.listing()
        lines, digest = self.preview()
        self.assertEqual(["mine", self.corpus, "--wing", "project", "--dry-run"], self.calls()[0]["argv"])
        self.assertEqual(1, len(self.calls()))
        self.assertEqual("preview of mine", lines[0])
        for line in ("project: %s" % self.root, "directory: %s" % self.corpus, "wing: project", "mode: projects",
                     "palace: (the program's own)", "file: a.md -> room:general (2 drawers)",
                     "file: b.md -> room:general (3 drawers)"):
            self.assertIn(line, lines)
        self.assertFalse([line for line in lines if "Device" in line or "/somewhere/palace" in line])
        self.assertTrue([line for line in lines if line.startswith("palaces the program may use: ")], lines)
        self.assertEqual(before, self.listing())
        self.assertEqual([], os.listdir(self.temp))

    def test_the_order_of_the_files_and_the_device_and_the_programs_palace_line_do_not_change_the_digest(self):
        _, first = self.preview()
        self.control(dry_stdout=dry_text(tuple(reversed(FILES)), device="cpu", palace="/another/palace"), stdout=REAL)
        _, second = self.preview()
        self.assertEqual(first, second)

    def test_a_file_a_count_the_wing_the_mode_the_palace_and_the_directory_change_the_digest(self):
        digests = {"base": self.preview()[1]}
        self.control(dry_stdout=dry_text(FILES + (("c.md", 1),)), stdout=REAL)
        digests["file added"] = self.preview()[1]
        self.control(dry_stdout=dry_text((("a.md", 2), ("b.md", 4))), stdout=REAL)
        digests["count"] = self.preview()[1]
        self.control(dry_stdout=dry_text(), stdout=REAL)
        digests["wing"] = self.preview("--wing", "other")[1]
        digests["mode"] = self.preview("--mode", "convos")[1]
        os.makedirs(os.path.join(self.base, "corpus2"))
        digests["directory"] = self.preview(corpus=os.path.join(self.base, "corpus2"))[1]
        self.local_setting(palace=os.path.join(self.base, "palace"))
        digests["palace"] = self.preview()[1]
        self.assertEqual(len(digests), len(set(digests.values())), digests)

    def test_a_change_of_the_palace_the_program_would_choose_changes_the_digest(self):
        """Found by the review of increment D: with no palace in the setting the program picks one from its own configuration, which the
        digest must bind, or the filing could go to another palace than the one previewed."""
        _, first = self.preview()
        os.makedirs(os.path.join(self.home, ".mempalace"))
        with open(os.path.join(self.home, ".mempalace", "config.json"), "w") as handle:
            handle.write('{"palace_path": "%s"}' % os.path.join(self.base, "other-palace"))
        self.assertNotEqual(first, self.preview()[1])

    def test_two_long_names_that_differ_only_late_have_different_digests_and_what_is_printed_is_cut(self):
        long_a, long_b = "d" * 400 + "-a.md", "d" * 400 + "-b.md"
        self.control(dry_stdout=dry_text(((long_a, 1),)), stdout=REAL)
        lines, first = self.preview()
        self.control(dry_stdout=dry_text(((long_b, 1),)), stdout=REAL)
        _, second = self.preview()
        self.assertNotEqual(first, second)
        self.assertTrue(all(len(line) <= 400 for line in lines), max(len(line) for line in lines))

    def test_an_uncached_model_is_refused_so_that_an_agent_never_starts_a_download(self):
        for name in self.helper.MODEL_FILES:
            os.remove(os.path.join(self.home, *self.helper.MODEL_DIR, name))
        self.refused("preview", "mine", self.corpus, contains="not cached")
        err = self.refused("mine", self.corpus, "--confirm", "--digest", "0" * 32, contains="not cached")
        self.assertEqual([], self.calls())
        self.assertFalse(os.path.exists(os.path.join(self.home, ".mempalace")))

    def test_the_same_state_gives_the_same_digest_again(self):
        self.assertEqual(self.preview()[1], self.preview()[1])

    def test_a_long_listing_is_cut_but_the_digest_covers_all_of_it(self):
        many = tuple(("f%03d.md" % n, 1) for n in range(500))
        self.control(dry_stdout=dry_text(many), stdout=REAL)
        lines, first = self.preview()
        self.assertLess(len(lines), 260)
        self.assertTrue([line for line in lines if re.match(r"\(\d+ more files? not shown", line)], lines)
        self.control(dry_stdout=dry_text(many[:-1] + (("f499.md", 9),)), stdout=REAL)
        self.assertNotEqual(first, self.preview()[1])

    def test_program_lines_that_look_like_the_heading_are_still_counted_and_cut(self):
        """Found by the second review of increment D: the cap on the program's own lines was bypassed by lines that start like the heading."""
        crowd = "\n".join("project: line %d" % n for n in range(300))
        self.control(dry_stdout=dry_text() + crowd + "\n", stdout=REAL)
        lines, _ = self.preview()
        self.assertLess(len(lines), 150)
        self.assertTrue([line for line in lines if re.match(r"\(\d+ more lines not shown", line)], lines)

    def test_a_line_that_is_cut_for_display_says_so(self):
        self.control(dry_stdout=dry_text(((("e" * 400) + ".md", 1),)), stdout=REAL)
        lines, _ = self.preview()
        self.assertTrue([line for line in lines if line.endswith("...") and len(line) == 303], lines)

    def test_the_folder_rules_apply_to_the_preview(self):
        os.symlink(self.corpus, os.path.join(self.base, "linked"))
        planted = os.path.join(self.base, "planted")
        os.makedirs(planted)
        os.symlink(os.path.join(self.base, "nothing"), os.path.join(planted, "mempalace.yaml"))
        os.makedirs(os.path.join(self.root, ".git", "x"))
        palace = os.path.join(self.corpus, "store")
        os.makedirs(palace)
        for target, word in ((self.root, "--allow-project-root"), (os.path.join(self.base, "linked"), "link"),
                             (planted, "would write through it"), (os.path.join(self.root, ".git", "x"), ".git or .workbench"),
                             (os.path.join(self.base, "nothing"), "does not exist")):
            self.refused("preview", "mine", target, contains=word)
        self.local_setting(palace=palace)
        self.refused("preview", "mine", self.corpus, contains="same place or one holds the other")
        self.assertEqual([], self.calls())

    def test_the_arguments_are_checked(self):
        self.refused("preview", contains="preview takes mine")
        self.refused("preview", "other", self.corpus, contains="preview takes mine")
        self.refused("preview", "mine", contains="needs the directory")
        self.refused("preview", "mine", self.corpus, "--confirm", contains="--confirm is not an option of preview")
        self.refused("preview", "mine", self.corpus, "--digest", "0" * 32, contains="is not an option")
        self.refused("preview", "mine", self.corpus, "--wing", "a b", contains="--wing")
        self.refused("preview", "mine", self.corpus, "--mode", "extract", contains="--mode")
        self.refused("preview", "mine", self.corpus, self.corpus, contains="exactly one directory")

    def test_a_program_that_fails_gives_no_digest(self):
        self.control(code=1, stdout="boom\n")
        code, out, err = self.run_helper("preview", "mine", self.corpus)
        self.assertEqual(1, code)
        self.assertTrue(err.startswith("failed: "), err)
        self.assertNotIn("digest:", out)

    def test_a_failed_dry_run_shows_the_programs_messages_too(self):
        self.control(code=1, stdout="out words\n", stderr="err words\n")
        code, out, err = self.run_helper("preview", "mine", self.corpus)
        self.assertEqual(1, code)
        self.assertIn("out words", out)
        self.assertIn("err words", out)

    def test_a_missing_program_is_refused_in_the_owners_words_and_not_as_a_skipped_search(self):
        os.remove(os.path.join(self.outside, "mempalace"))
        err = self.refused("preview", "mine", self.corpus, contains="not found in a trusted PATH entry")
        self.assertNotIn("skipped", err)

    def test_a_dry_run_that_takes_too_long_is_stopped(self):
        self.control(sleep=3, dry_stdout=dry_text())
        with unittest.mock.patch.object(self.helper, "PREVIEW_TIMEOUT", 1):
            code, out, err = self.run_helper("preview", "mine", self.corpus)
        self.assertEqual(1, code)
        self.assertIn("did not finish", err)
        self.assertNotIn("digest:", out)

    def test_it_takes_no_lock_and_makes_no_directory_for_one(self):
        self.preview()
        self.assertFalse(os.path.exists(os.path.join(self.home, ".mempalace")))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))


class Run(Ask):
    def test_a_run_with_the_digest_of_the_preview_files_without_a_terminal_and_prints_the_tail_framed(self):
        _, digest = self.preview()
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        (real,) = self.real_calls()
        self.assertEqual(["mine", self.corpus, "--wing", "project"], real["argv"])
        self.assertEqual([False, False, False], real["tty"])
        lines = out.split("\n")
        self.assertRegex(lines[0], r"^<<recalled-data [0-9a-f]{12} begin: mempalace mine>>$")
        self.assertEqual("<<recalled-data %s end>>" % lines[0].split()[1], lines[-2])
        self.assertIn("Files processed: 2", out)
        self.assertEqual(3, len(self.calls()))   # the preview, the check inside the lock, the run

    def test_a_wrong_digest_files_nothing(self):
        self.preview()
        code, out, err = self.confirm("0" * 32)
        self.assertEqual(1, code)
        self.assertIn(self.helper.digest.MISMATCH, err)
        self.assertIn("nothing was filed", err)
        self.assertEqual([], self.real_calls())

    def test_a_folder_that_changed_after_the_preview_files_nothing(self):
        _, digest = self.preview()
        self.control(dry_stdout=dry_text(FILES + (("new.md", 1),)), stdout=REAL)
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn(self.helper.digest.MISMATCH, err)
        self.assertEqual([], self.real_calls())

    def test_a_digest_goes_with_confirm_and_must_be_32_lowercase_hexadecimal_characters(self):
        self.refused("mine", self.corpus, "--digest", "0" * 32, contains="--confirm")
        for bad in ("zz", "0" * 31, "0" * 33, "A" * 32):
            code, out, err = self.run_helper("mine", self.corpus, "--confirm", "--digest", bad)
            self.assertEqual(1, code, bad)
            self.assertIn(self.helper.digest.SHAPE, err)
        self.assertEqual([], self.calls())

    def test_a_digest_that_is_not_the_last_two_arguments_is_not_one(self):
        self.refused("mine", self.corpus, "--digest", "0" * 32, "--confirm", contains="is not an option")

    def test_without_a_digest_a_terminal_is_still_needed_and_with_one_it_is_not(self):
        self.refused("mine", self.corpus, "--confirm", contains="only from a terminal")
        self.refused("mine", self.corpus, contains="only from a terminal")
        code, shown = self.owner("mine", self.corpus, "--confirm")
        self.assertEqual(0, code, shown)
        self.assertEqual([True, True, True], self.real_calls()[0]["tty"])

    def test_a_digest_at_a_terminal_runs_the_same_checked_way(self):
        _, digest = self.preview()
        code, shown = self.owner("mine", self.corpus, "--confirm", "--digest", digest)
        self.assertEqual(0, code, shown)
        self.assertIn("Files processed: 2", shown)
        self.assertEqual([False, False, False], self.real_calls()[0]["tty"])

    def test_the_folder_rules_apply_to_a_run_with_a_digest(self):
        _, digest = self.preview()
        before = len(self.calls())
        code, out, err = self.confirm(digest, corpus=self.root)
        self.assertEqual(1, code)
        self.assertIn("--allow-project-root", err)
        self.assertEqual(before, len(self.calls()))

    def test_a_program_that_fails_is_a_failure_with_its_words_and_no_second_run(self):
        _, digest = self.preview()
        self.control(dry_stdout=dry_text(), stdout="oops\n", code_real=2)
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn("exited with code 2", err)
        self.assertIn("oops", out)
        self.assertEqual(1, len(self.real_calls()))

    def test_a_long_output_is_cut_to_its_tail_and_the_program_is_not_stopped_for_it(self):
        _, digest = self.preview()
        self.control(dry_stdout=dry_text(), stdout=REAL, real_bytes=2 * 1048576 + 10)
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        self.assertLess(len(out), self.helper.MAX_TEXT + 1000)
        self.assertIn("[earlier output cut]", out)
        self.assertIn("Files processed: 2", out)

    def test_control_characters_in_the_output_are_removed(self):
        _, digest = self.preview()
        self.control(dry_stdout=dry_text(), stdout="a\x1b[31mb\x07c\x00d‮e\n")
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        for bad in ("\x1b", "\x07", "\x00", "‮"):
            self.assertNotIn(bad, out)

    def test_the_run_has_no_time_limit(self):
        self.control(sleep=2, dry_stdout=dry_text(), stdout=REAL)
        _, digest = self.preview()
        with unittest.mock.patch.object(self.helper, "TIMEOUT", 1):
            code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)

    def test_the_wing_from_a_setting_or_the_folder_name_is_in_the_digest_and_the_run(self):
        self.local_setting(wing="chosen")
        _, digest = self.preview()
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        self.assertEqual(["mine", self.corpus, "--wing", "chosen"], self.real_calls()[0]["argv"])
        before = len(self.real_calls())
        code, out, err = self.confirm(digest, "--wing", "project")
        self.assertEqual(1, code)   # another wing is another digest
        self.assertIn(self.helper.digest.MISMATCH, err)
        self.assertEqual(before, len(self.real_calls()))


class Lock(Ask):
    def lock_path(self, folder=None):
        return os.path.join(folder or os.path.join(self.home, ".mempalace"), "mempalace-helper.lock")

    def hold(self, folder=None):
        folder = folder or os.path.join(self.home, ".mempalace")
        os.makedirs(folder, exist_ok=True)
        descriptor = os.open(self.lock_path(folder), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        self.addCleanup(os.close, descriptor)
        return descriptor

    def free(self, folder=None):
        descriptor = os.open(self.lock_path(folder), os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(descriptor)

    def test_a_run_makes_the_lock_beside_the_default_palace_with_private_modes(self):
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        folder = os.path.join(self.home, ".mempalace")
        self.assertEqual(0o700, stat.S_IMODE(os.stat(folder).st_mode))
        self.assertEqual(0o600, stat.S_IMODE(os.stat(self.lock_path()).st_mode))
        self.free()

    def test_the_lock_sits_beside_the_palace_a_setting_names(self):
        self.local_setting(palace=os.path.join(self.base, "elsewhere", "palace"))
        os.makedirs(os.path.join(self.base, "elsewhere"))
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        self.free(os.path.join(self.base, "elsewhere"))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".mempalace")))

    def test_a_held_lock_refuses_a_run_at_once_before_the_program_is_started_at_all(self):
        _, digest = self.preview()
        self.hold()
        before = len(self.calls())
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn("another mempalace run is in progress", err)
        self.assertEqual(before, len(self.calls()))   # not even the check of the digest was run
        code, shown = self.owner("mine", self.corpus, "--confirm")
        self.assertEqual(1, code)
        self.assertIn("another mempalace run is in progress", shown)
        self.assertEqual(before, len(self.calls()))

    def test_a_dry_run_and_a_preview_do_not_wait_for_the_lock(self):
        self.hold()
        lines, digest = self.preview()
        self.assertTrue(digest)
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(0, code, shown)

    def test_the_lock_is_free_after_a_run_a_refusal_and_a_failed_program(self):
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        self.free()
        self.assertEqual(1, self.confirm("0" * 32)[0])
        self.free()
        self.control(dry_stdout=dry_text(), stdout="oops\n", code_real=2)
        self.assertEqual(1, self.confirm(digest)[0])
        self.free()

    def test_an_absent_palace_directory_is_made_private_and_one_with_no_parent_is_refused(self):
        self.local_setting(palace=os.path.join(self.base, "newparent", "palace"))
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        self.assertEqual(0o700, stat.S_IMODE(os.stat(os.path.join(self.base, "newparent")).st_mode))
        self.local_setting(palace=os.path.join(self.base, "no", "such", "palace"))
        _, digest = self.preview()
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertTrue(err.startswith("refused: "), err)
        self.assertFalse(os.path.exists(os.path.join(self.base, "no")))

    def test_a_link_in_place_of_the_lock_or_its_directory_is_refused_and_nothing_is_written_through_it(self):
        victim = os.path.join(self.base, "victim.txt")
        with open(victim, "w") as handle:
            handle.write("ORIGINAL\n")
        folder = os.path.join(self.home, ".mempalace")
        os.makedirs(folder)
        os.symlink(victim, self.lock_path())
        _, digest = self.preview()
        before = len(self.calls())
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertTrue(err.startswith("refused: "), err)
        os.remove(self.lock_path())
        os.mkdir(self.lock_path())
        self.assertEqual(1, self.confirm(digest)[0])
        os.rmdir(self.lock_path())
        os.rename(folder, folder + ".real")
        os.symlink(folder + ".real", folder)
        self.assertEqual(1, self.confirm(digest)[0])
        self.assertEqual(before, len(self.calls()))
        with open(victim) as handle:
            self.assertEqual("ORIGINAL\n", handle.read())

    def test_a_machine_without_the_program_gets_no_directory_and_no_lock(self):
        _, digest = self.preview()
        os.remove(os.path.join(self.outside, "mempalace"))
        shutil.rmtree(os.path.join(self.home, ".mempalace"), ignore_errors=True)
        before = len(self.calls())
        code, out, err = self.confirm(digest)
        self.assertEqual(1, code)
        self.assertIn("not found in a trusted PATH entry", err)
        self.assertNotIn("skipped", err)
        self.assertEqual(before, len(self.calls()))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".mempalace")))

    def test_a_palace_that_sits_in_the_clone_puts_the_lock_there_and_it_is_still_a_regular_private_file(self):
        """Found by the review of increment D: the lock is beside the palace, so a setting that puts the palace in the clone puts an untracked
        file in the clone's root. That is the owner's choice of palace, and the spec says so."""
        self.local_setting(palace=os.path.join(self.root, "palace-store"))
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        lock = os.path.join(self.root, "mempalace-helper.lock")
        self.assertEqual(0o600, stat.S_IMODE(os.stat(lock).st_mode))
        self.assertTrue(stat.S_ISREG(os.stat(lock).st_mode))

    def test_a_clone_with_no_local_directory_runs_and_gains_none(self):
        _, digest = self.preview()
        self.assertEqual(0, self.confirm(digest)[0])
        self.assertEqual(0, self.owner("mine", self.corpus, "--confirm")[0])
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))

    def test_a_terminated_helper_stops_the_program_and_what_it_started_and_frees_the_lock(self):
        """Found by the review of increment D: the program runs in its own process group, and only its leader was stopped."""
        self.control(dry_stdout=dry_text(), stdout=REAL, real_sleep=60, real_leave_child=True)
        _, digest = self.preview()
        child = os.fork()
        if child == 0:   # the helper, with the handler the launcher installs for a terminate signal
            try:
                import io
                signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
                self.helper.main(["mine", self.corpus, "--confirm", "--digest", digest], io.BytesIO(b""), io.StringIO(), io.StringIO(), self.root)
            finally:
                os._exit(0)
        started = None
        for _ in range(100):
            if self.real_calls() and os.path.exists(os.path.join(self.outside, "pids")):
                started = self.real_calls()[0]["pid"]
                break
            time.sleep(0.1)
        grandchild = None
        try:
            self.assertIsNotNone(started, "the program was not started")
            with open(os.path.join(self.outside, "pids")) as handle:
                grandchild = int(handle.read())
            os.kill(child, signal.SIGTERM)
            os.waitpid(child, 0)
            for _ in range(50):
                alive = []
                for pid in (started, grandchild):
                    try:
                        os.kill(pid, 0)
                        alive.append(pid)
                    except ProcessLookupError:
                        pass
                if not alive:
                    break
                time.sleep(0.1)
            self.assertEqual([], alive, "the program or what it started is still running")
            self.free()
        finally:
            for pid in (started, grandchild):
                if pid:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_a_killed_run_frees_the_lock_and_the_program_does_not_hold_it(self):
        self.control(dry_stdout=dry_text(), stdout=REAL, real_sleep=60)   # only the real run waits; the dry runs do not
        _, digest = self.preview()
        child = os.fork()
        if child == 0:   # the helper, which is then killed
            try:
                import io
                self.helper.main(["mine", self.corpus, "--confirm", "--digest", digest], io.BytesIO(b""), io.StringIO(), io.StringIO(), self.root)
            finally:
                os._exit(0)
        started = None
        for _ in range(100):
            real = self.real_calls()
            if real:
                started = real[0]["pid"]
                break
            time.sleep(0.1)
        try:
            self.assertIsNotNone(started, "the program was not started")
            with self.assertRaises(BlockingIOError):
                self.free()   # held while the run lives
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
            self.free()      # the program is still running and does not hold it
        finally:
            if started:
                try:
                    os.kill(started, signal.SIGKILL)
                except ProcessLookupError:
                    pass


class Safeguard(Ask):
    def test_a_file_the_program_created_in_the_folder_is_named_in_one_line_and_not_deleted(self):
        _, digest = self.preview()
        files = {os.path.join(self.corpus, "mempalace.yaml"): "x", os.path.join(self.corpus, "entities.json"): "{}"}
        self.control(dry_stdout=dry_text(), stdout=REAL, write=files)
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        said = [line for line in err.splitlines() if "left" in line]
        self.assertEqual(1, len(said), err)
        self.assertIn("entities.json, mempalace.yaml", said[0])
        self.assertIn(self.corpus, said[0])
        self.assertIn("can be deleted", said[0])
        for path in files:
            self.assertTrue(os.path.exists(path))

    def test_the_same_line_at_a_terminal(self):
        self.control(dry_stdout=dry_text(), stdout=REAL, write={os.path.join(self.corpus, ".gitignore"): "x\n"})
        code, shown = self.owner("mine", self.corpus, "--confirm")
        self.assertEqual(0, code, shown)
        self.assertIn(".gitignore", [line for line in shown.splitlines() if "left" in line][0])

    def test_any_case_of_a_name_counts(self):
        _, digest = self.preview()
        self.control(dry_stdout=dry_text(), stdout=REAL, write={os.path.join(self.corpus, "ENTITIES.JSON"): "{}"})
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        self.assertIn("ENTITIES.JSON", err)

    def test_nothing_is_said_when_nothing_was_created_or_the_file_was_there_before(self):
        _, digest = self.preview()
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        self.assertNotIn("left", err)
        with open(os.path.join(self.corpus, "mempalace.yaml"), "w") as handle:
            handle.write("wing: x\n")
        _, digest = self.preview()
        self.control(dry_stdout=dry_text(), stdout=REAL, write={os.path.join(self.corpus, "mempalace.yaml"): "wing: y\n"})
        code, out, err = self.confirm(digest)
        self.assertEqual(0, code, err)
        self.assertNotIn("left", err)

    def test_a_dry_run_says_nothing_of_it(self):
        self.control(dry_stdout=dry_text(), stdout=REAL, write={os.path.join(self.corpus, "mempalace.yaml"): "x"})
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(0, code, shown)
        self.assertNotIn("left", shown)


if __name__ == "__main__":
    unittest.main()
