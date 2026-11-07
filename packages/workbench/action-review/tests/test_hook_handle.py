"""The handle that the shadow hook keeps of a command the engine declined for a secret (`docs/specs/action-review.md`, "Labelling a declined
secret").

Plan `2026-11-07-label-declined-secrets`, increment C. The hook writes, for a command declined for `no_secret_lines` or
`paths_not_credentials`, one row of `collected.jsonl` built from a fixed list of fields and from nothing else: a `handle` marker, the
paths of the facts that the project already tracks (read from its git index in the hook's own process, with no program started), a count
of the paths left out, and `confirm` when it is a boolean. Nothing of the command, the diff, the subject, the body, the trailers or the
model's reason goes into it. A path is kept only if it is a path of the index or a directory above one: the redactor is not the rule.

The first half of this file tests the index reader against real indexes made by git and against hostile ones made by hand; the second
half tests the row, with the real engine's own bytes replayed to the hook. Written before the code."""

import hashlib
import io
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock

from test_actionreview_output import COMMAND, commit_doc, described
from tests import support_install
from test_hook_shadow_hook import Base, Replay, SHAPES, diff_adding, os_remove_rows

ROOT = support_install.ROOT
SPEC = os.path.join(ROOT, "docs", "specs", "action-review.md")
GIT = shutil.which("git")
FIXED_COMMAND = "[declined for a secret; the command is not kept]"
FIXED_REASON = "declined for a secret; nothing of the command is kept"
SENTINEL = "SENTINEL-MUST-NOT-REACH-THE-ROW"
HEX = "0123456789abcdef"


def entry(name, extended=False):
    """One version 2 (or, with `extended`, version 3) index entry for `name`, padded as git pads it."""
    head = struct.pack(">10I", 1, 0, 1, 0, 1, 1, 0o100644, 0, 0, 0) + bytes(20)
    flags = min(len(name), 0xFFF) | (0x4000 if extended else 0)
    body = head + struct.pack(">H", flags) + (struct.pack(">H", 0) if extended else b"") + name
    return body + bytes(((len(body) + 8) & ~7) - len(body))


def make_index(names, version=2, count=None, tail=b"", sign=True):
    """The bytes of a git index holding `names` (bytes), with its trailing SHA-1."""
    entries = b"".join(entry(name, version == 3) for name in names)
    data = b"DIRC" + struct.pack(">II", version, len(names) if count is None else count) + entries + tail
    return data + (hashlib.sha1(data).digest() if sign else bytes(20))


class Repos(unittest.TestCase):
    """Throwaway repositories under a scratch directory; git is started by the tests, never by the hook."""

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.base = os.path.realpath(scratch.name)
        self.env = {"PATH": os.path.dirname(GIT) + ":/usr/bin:/bin", "HOME": self.base, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull}

    def git(self, root, *args):
        run = subprocess.run([GIT, "-C", root, *args], env=self.env, capture_output=True, timeout=60)
        self.assertEqual(0, run.returncode, (args, run.stderr))

    def repo(self, name="repo", tracked=(), untracked=()):
        root = os.path.join(self.base, name)
        os.makedirs(root)
        self.git(root, "init", "-q")
        for relative in list(tracked) + list(untracked):
            path = os.path.join(root, *relative.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as handle:
                handle.write("x\n")
        if tracked:
            self.git(root, "add", "--", *tracked)
        return root

    def write_index(self, root, data):
        path = os.path.join(root, ".git", "index")
        if os.path.lexists(path):
            os.remove(path)
        with open(path, "wb") as handle:
            handle.write(data)
        return path


class IndexReader(Repos):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_hook_shadow_hook import load, HOOK
        cls.hook = load("action_review_hook_handle_under_test", HOOK)

    def tracked(self, cwd, *wanted):
        return self.hook.tracked_among(cwd, set(wanted))

    def test_a_tracked_file_and_the_directories_above_it_are_admitted_and_an_untracked_one_is_not(self):
        root = self.repo(tracked=["a.txt", "dir/b.py", "dir/sub/c.py"], untracked=["new.txt"])
        got = self.tracked(root, "a.txt", "dir/b.py", "dir", "dir/sub", "new.txt", "nope.txt", "dir/b")
        self.assertEqual({"a.txt", "dir/b.py", "dir", "dir/sub"}, got)

    def test_only_what_was_asked_for_comes_back(self):
        root = self.repo(tracked=["a.txt", "b.txt"])
        self.assertEqual({"a.txt"}, self.tracked(root, "a.txt"))
        self.assertEqual(set(), self.tracked(root))

    def test_names_are_matched_exactly_and_case_matters(self):
        root = self.repo(tracked=["Readme.md"])
        self.assertEqual({"Readme.md"}, self.tracked(root, "Readme.md", "README.md", "readme.md", "Readme.m"))

    def test_a_file_staged_and_then_taken_out_of_the_index_is_not_admitted(self):
        root = self.repo(tracked=["a.txt", "b.txt"])
        self.git(root, "rm", "-q", "--cached", "--", "a.txt")
        self.assertEqual({"b.txt"}, self.tracked(root, "a.txt", "b.txt"))

    def test_a_version_3_index_with_an_intent_to_add_entry_is_read(self):
        root = self.repo(tracked=["a.txt"], untracked=["new.txt"])
        self.git(root, "add", "-N", "--", "new.txt")
        with open(os.path.join(root, ".git", "index"), "rb") as handle:
            self.assertEqual(3, struct.unpack(">I", handle.read(8)[4:])[0])
        self.assertEqual({"a.txt", "new.txt"}, self.tracked(root, "a.txt", "new.txt"))

    def test_a_version_4_index_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        self.git(root, "update-index", "--index-version", "4")
        self.assertEqual(set(), self.tracked(root, "a.txt"))

    def test_a_version_4_header_over_entries_laid_out_as_version_2_keeps_no_path(self):
        """The layout is not guessed from the entries: only versions 2 and 3 are read, whatever follows the header."""
        root = self.repo()
        self.write_index(root, make_index([b"a.txt"], version=4))
        self.assertEqual(set(), self.tracked(root, "a.txt"))
        self.write_index(root, make_index([b"a.txt"], version=2))
        self.assertEqual({"a.txt"}, self.tracked(root, "a.txt"))

    def test_a_subdirectory_of_the_repository_finds_the_repository_and_names_are_relative_to_its_root(self):
        root = self.repo(tracked=["sub/a.txt", "top.txt"])
        self.assertEqual({"sub/a.txt", "top.txt"}, self.tracked(os.path.join(root, "sub"), "sub/a.txt", "top.txt", "a.txt"))

    def test_the_nearest_repository_wins(self):
        outer = self.repo("outer", tracked=["outer.txt"])
        inner = os.path.join(outer, "inner")
        os.makedirs(inner)
        self.git(inner, "init", "-q")
        with open(os.path.join(inner, "in.txt"), "w") as handle:
            handle.write("x")
        self.git(inner, "add", "--", "in.txt")
        self.assertEqual({"in.txt"}, self.tracked(inner, "in.txt", "outer.txt"))

    def test_a_directory_with_no_repository_keeps_no_path(self):
        plain = os.path.join(self.base, "plain")
        os.makedirs(plain)
        self.assertEqual(set(), self.tracked(plain, "a.txt"))

    def test_a_working_directory_that_does_not_exist_or_is_not_a_directory_keeps_no_path(self):
        self.assertEqual(set(), self.tracked(os.path.join(self.base, "missing"), "a.txt"))
        path = os.path.join(self.base, "file")
        open(path, "w").close()
        self.assertEqual(set(), self.tracked(path, "a.txt"))
        self.assertEqual(set(), self.tracked("relative/dir", "a.txt"))

    def test_a_working_directory_reached_through_a_link_is_resolved_once_and_read(self):
        root = self.repo(tracked=["a.txt"])
        link = os.path.join(self.base, "link")
        os.symlink(root, link)
        self.assertEqual({"a.txt"}, self.tracked(link, "a.txt"))

    # -- hostile indexes ---------------------------------------------------------------------------------------------
    def test_an_index_that_is_a_link_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        other = self.repo("other", tracked=["a.txt"])
        os.rename(os.path.join(root, ".git", "index"), os.path.join(root, ".git", "real-index"))
        os.symlink(os.path.join(other, ".git", "index"), os.path.join(root, ".git", "index"))
        self.assertEqual(set(), self.tracked(root, "a.txt"))

    def test_a_git_directory_that_is_a_link_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        other = self.repo("other", tracked=["a.txt", "secret-looking.txt"])
        shutil.rmtree(os.path.join(root, ".git"))
        os.symlink(os.path.join(other, ".git"), os.path.join(root, ".git"))
        self.assertEqual(set(), self.tracked(root, "a.txt", "secret-looking.txt"))

    def test_a_git_file_keeps_no_path_and_does_not_fall_through_to_a_repository_above(self):
        outer = self.repo("outer", tracked=["outer.txt"])
        inner = os.path.join(outer, "inner")
        os.makedirs(inner)
        with open(os.path.join(inner, ".git"), "w") as handle:
            handle.write("gitdir: ../.git\n")
        self.assertEqual(set(), self.tracked(inner, "outer.txt"))

    def test_an_index_over_the_size_cap_keeps_no_path_and_is_not_read_whole(self):
        """A valid, signed index of 40 MiB: only the cap keeps it out (a file of zeros would fail on its magic)."""
        root = self.repo()
        data = make_index([b"a.txt"], tail=bytes(40 * 1024 * 1024))
        self.write_index(root, data)
        started = time.monotonic()
        self.assertEqual(set(), self.tracked(root, "a.txt"))
        self.assertLess(time.monotonic() - started, 5)
        self.write_index(root, make_index([b"a.txt"], tail=bytes(1024 * 1024)))
        self.assertEqual({"a.txt"}, self.tracked(root, "a.txt"))

    def test_more_entries_than_the_cap_keep_no_path_even_when_they_fit_the_size(self):
        root = self.repo()
        self.write_index(root, make_index([b"a"] * 200001))
        self.assertEqual(set(), self.tracked(root, "a"))
        self.write_index(root, make_index([b"a"] * 200000))
        self.assertEqual({"a"}, self.tracked(root, "a"))

    def test_an_index_read_that_runs_out_of_time_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        with unittest.mock.patch.object(self.hook, "INDEX_SECONDS", -1.0):
            self.assertEqual(set(), self.tracked(root, "a.txt"))
        self.assertEqual({"a.txt"}, self.tracked(root, "a.txt"))

    def test_a_split_or_sparse_index_is_read_as_the_main_file_lists_it(self):
        """The reader ignores the extensions: a split index lists only the entries of the main file, so it names less (fail closed); a
        sparse index lists a directory as `dir/`, and the directory above its entries is admitted, which is a tracked directory."""
        root = self.repo()
        self.write_index(root, make_index([b"dir/"], tail=b"link" + struct.pack(">I", 0)))
        self.assertEqual({"dir"}, self.tracked(root, "dir", "dir/x"))

    def test_a_truncated_empty_or_garbled_index_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        good = make_index([b"a.txt"])
        for name, data in (("empty", b""), ("short header", b"DIRC\0\0"), ("cut", good[:-30]), ("no checksum", good[:-20]),
                           ("magic", b"XXXX" + good[4:]), ("zeros", bytes(200))):
            with self.subTest(name):
                self.write_index(root, data)
                self.assertEqual(set(), self.tracked(root, "a.txt"))

    def test_a_wrong_checksum_keeps_no_path(self):
        root = self.repo()
        self.write_index(root, make_index([b"a.txt"], sign=False))
        self.assertEqual(set(), self.tracked(root, "a.txt"))
        self.write_index(root, make_index([b"a.txt"]))
        self.assertEqual({"a.txt"}, self.tracked(root, "a.txt"))

    def test_an_entry_count_that_does_not_fit_the_size_keeps_no_path(self):
        root = self.repo()
        for count in (2, 1000, 0xFFFFFFFF, 200001):
            with self.subTest(count):
                self.write_index(root, make_index([b"a.txt"], count=count))
                self.assertEqual(set(), self.tracked(root, "a.txt"))

    def test_an_entry_that_runs_past_the_end_keeps_no_path(self):
        root = self.repo()
        head = struct.pack(">10I", 1, 0, 1, 0, 1, 1, 0o100644, 0, 0, 0) + bytes(20) + struct.pack(">H", 100)
        data = b"DIRC" + struct.pack(">II", 2, 1) + head + b"abc"  # a name of 100 bytes, and three present
        self.write_index(root, data + hashlib.sha1(data).digest())
        self.assertEqual(set(), self.tracked(root, "a.txt", "abc"))
        data = b"DIRC" + struct.pack(">II", 2, 1) + head[:-2] + struct.pack(">H", 0xFFF) + b"abc"  # no NUL before the end
        self.write_index(root, data + hashlib.sha1(data).digest())
        self.assertEqual(set(), self.tracked(root, "a.txt", "abc"))

    def test_an_unknown_version_keeps_no_path(self):
        root = self.repo()
        for version in (0, 1, 5, 0xFFFFFFFF):
            with self.subTest(version):
                data = b"DIRC" + struct.pack(">II", version, 0)
                self.write_index(root, data + hashlib.sha1(data).digest())
                self.assertEqual(set(), self.tracked(root, "a.txt"))

    def test_a_name_that_is_not_ascii_is_ignored_and_does_not_spoil_the_rest(self):
        root = self.repo()
        self.write_index(root, make_index([b"a.txt", "café.txt".encode(), b"\xff\xfe", b"b.txt"]))
        self.assertEqual({"a.txt", "b.txt"}, self.tracked(root, "a.txt", "b.txt", "café.txt"))

    def test_an_index_that_is_a_directory_or_a_fifo_or_has_two_links_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        path = os.path.join(root, ".git", "index")
        os.rename(path, path + ".real")
        os.mkdir(path)
        self.assertEqual(set(), self.tracked(root, "a.txt"))
        os.rmdir(path)
        os.mkfifo(path)
        outcome = []
        worker = threading.Thread(target=lambda: outcome.append(self.tracked(root, "a.txt")), daemon=True)
        worker.start()
        worker.join(5)
        self.assertFalse(worker.is_alive(), "a FIFO with no writer must be rejected promptly, not held on")
        self.assertEqual([set()], outcome)
        os.remove(path)
        os.rename(path + ".real", path)
        os.link(path, path + ".twin")
        self.assertEqual(set(), self.tracked(root, "a.txt"))

    def test_an_index_of_another_owner_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        with unittest.mock.patch.object(self.hook.os, "geteuid", return_value=os.geteuid() + 1):
            self.assertEqual(set(), self.tracked(root, "a.txt"))
        self.assertEqual({"a.txt"}, self.tracked(root, "a.txt"))

    def test_the_reader_starts_no_program(self):
        root = self.repo(tracked=["a.txt"])
        with unittest.mock.patch.object(self.hook.subprocess, "Popen", side_effect=AssertionError("started a program")), \
                unittest.mock.patch.object(self.hook.os, "system", side_effect=AssertionError("started a program"), create=True):
            self.assertEqual({"a.txt"}, self.tracked(root, "a.txt"))

    def test_every_descriptor_it_opens_is_closed(self):
        root = self.repo(tracked=["a.txt"])
        before = set(os.listdir("/dev/fd"))
        for _ in range(3):
            self.tracked(root, "a.txt")
            self.tracked(os.path.join(self.base, "missing"), "a.txt")
            self.write_index(root, b"junk")
            self.tracked(root, "a.txt")
        self.assertEqual(before, set(os.listdir("/dev/fd")))

    # -- a swap between the discovery and the open --------------------------------------------------------------------
    def test_a_git_directory_swapped_for_a_link_after_it_was_found_does_not_change_what_is_read(self):
        root = self.repo(tracked=["a.txt"])
        other = self.repo("other", tracked=["other.txt"])
        descriptor = self.hook.open_git_directory(root)
        self.assertIsNotNone(descriptor)
        try:
            os.rename(os.path.join(root, ".git"), os.path.join(root, ".git-moved"))
            os.symlink(os.path.join(other, ".git"), os.path.join(root, ".git"))
            self.assertEqual({"a.txt"}, self.hook.read_index_names(descriptor, {"a.txt", "other.txt"}))
        finally:
            os.close(descriptor)

    def test_an_index_swapped_for_a_link_after_the_directory_was_found_keeps_no_path(self):
        root = self.repo(tracked=["a.txt"])
        other = self.repo("other", tracked=["other.txt"])
        descriptor = self.hook.open_git_directory(root)
        try:
            path = os.path.join(root, ".git", "index")
            os.remove(path)
            os.symlink(os.path.join(other, ".git", "index"), path)
            self.assertEqual(set(), self.hook.read_index_names(descriptor, {"a.txt", "other.txt"}))
        finally:
            os.close(descriptor)

    def test_the_directory_of_the_command_swapped_for_a_link_while_the_walk_is_made_is_not_followed(self):
        root = self.repo(tracked=["a.txt"])
        other = self.repo("other", tracked=["other.txt"])
        sub = os.path.join(root, "sub")
        os.makedirs(sub)
        real_open = os.open
        swapped = []

        def swapping(path, flags, *args, **kwargs):
            if path == "sub" and not swapped:
                swapped.append(True)
                os.rename(sub, sub + "-moved")
                os.symlink(other, sub)
            return real_open(path, flags, *args, **kwargs)

        with unittest.mock.patch.object(self.hook.os, "open", side_effect=swapping):
            self.assertEqual(set(), self.tracked(sub, "other.txt", "a.txt"))
        self.assertTrue(swapped)


class Candidates(Repos):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_hook_shadow_hook import load, HOOK
        cls.hook = load("action_review_hook_candidates_under_test", HOOK)

    def test_a_plain_relative_path_is_a_candidate(self):
        self.assertEqual((["a.txt", "dir/b.py", "x/y/z"], 0), self.hook.candidate_paths(["a.txt", "dir/b.py", "x/y/z"]))

    def test_paths_that_are_not_plain_relative_ascii_text_are_rejected_and_counted(self):
        bad = ["", "/abs/path", "../up", "a/../b", "a/..", "..", "-flag", "--x", "trailing/", "a//b", "tab\tname", "new\nline", "nul\0",
               "café", "bidi‮", "x" * 257, 5, None, ["a"], {"k": "v"}, True, 1.5, b"bytes", "./a", "a/./b", "\x7f", "emoji\U0001F600"]
        kept, dropped = self.hook.candidate_paths(bad)
        self.assertEqual(([], len(bad)), (kept, dropped))

    def test_a_path_of_exactly_256_printable_characters_is_a_candidate(self):
        path = "d/" + "x" * 254
        self.assertEqual(256, len(path))
        self.assertEqual(([path], 0), self.hook.candidate_paths([path]))

    def test_duplicates_are_kept_once_in_first_seen_order_and_not_counted_as_dropped(self):
        self.assertEqual((["b", "a"], 0), self.hook.candidate_paths(["b", "a", "b", "a"]))

    def test_only_the_first_hundred_are_considered_and_the_rest_are_counted(self):
        kept, dropped = self.hook.candidate_paths(["p%03d" % number for number in range(250)])
        self.assertEqual((100, 150), (len(kept), dropped))

    def test_what_is_not_a_list_gives_no_candidate_and_is_not_counted(self):
        for value in (None, "a.txt", 5, {"a": 1}):
            self.assertEqual(([], 0), self.hook.candidate_paths(value))


class HandleRow(Base):
    """The row, with the real engine's bytes replayed to the hook. The working directory is a repository that tracks `a.txt`."""

    def setUp(self):
        super().setUp()
        self.env = {"PATH": os.path.dirname(GIT) + ":/usr/bin:/bin", "HOME": self.base, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull}
        self.track("a.txt", "dir/b.py", ".env")

    def track(self, *names):
        subprocess.run([GIT, "-C", self.cwd, "init", "-q"], env=self.env, capture_output=True, timeout=60, check=True)
        for name in names:
            path = os.path.join(self.cwd, *name.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as handle:
                handle.write("x\n")
        subprocess.run([GIT, "-C", self.cwd, "add", "-f", "--", *names], env=self.env, capture_output=True, timeout=60, check=True)

    def declined(self, **facts):
        diff = facts.pop("diff", diff_adding("x = " + SHAPES["gitlab"]))
        return self.engine(describe=described(commit_doc(diff=diff, **facts)))

    def one_collected(self):
        rows, skipped = self.rows("collected.jsonl")
        self.assertEqual((1, 0), (len(rows), skipped), rows)
        return rows[0]

    def stored_text(self):
        data = ""
        for name in ("verdicts.jsonl", "collected.jsonl"):
            path = os.path.join(self.store.data_dir(self.home), name)
            if os.path.exists(path):
                with open(path, "rb") as handle:
                    data += handle.read().decode("utf-8")
        return data

    def test_a_decline_for_a_secret_leaves_one_handle_with_the_tracked_paths_and_nothing_of_the_command(self):
        code, err = self.run_hook(self.declined(paths=["a.txt", "new.txt"], requested_paths=["a.txt", "new.txt"]))
        self.assertEqual((0, ""), (code, err))
        row = self.one_collected()
        verdict = self.one_verdict()
        self.assertEqual("safe-git-commit", row["rule"])
        self.assertEqual(self.sha(COMMAND), row["command_sha256"])
        self.assertEqual(FIXED_COMMAND, row["command"])
        self.assertEqual(FIXED_REASON, row["reason"])
        self.assertEqual("decline", row["verdict"])
        self.assertIn("no_secret_lines", row["failed_checks"])
        self.assertEqual(verdict["ts"], row["ts"])
        self.assertRegex(row["id"], r"^[0-9a-f]{32}$")
        self.assertEqual({"handle": True, "facts": {"paths": ["a.txt"], "paths_dropped": 1}}, row["facts"])
        self.assertEqual({"id", "ts", "rule", "command_sha256", "command", "facts", "verdict", "failed_checks", "reason"}, set(row))
        self.assertNotIn(SHAPES["gitlab"], self.stored_text())
        self.assertNotIn(COMMAND, self.stored_text())

    def test_the_verdict_row_of_a_declined_secret_is_what_it_was(self):
        self.run_hook(self.declined())
        row = self.one_verdict()
        self.assertEqual(("reviewed", "decline", True), (row["outcome"], row["verdict"], row["reviewed"]))
        self.assertIn("no_secret_lines", row["failed_checks"])
        self.assertEqual(self.sha(COMMAND), row["command_sha256"])

    def test_a_decline_for_a_credential_named_path_leaves_a_handle_too(self):
        self.run_hook(self.engine(describe=described(commit_doc(paths=[".env"], requested_paths=[".env"],
                                                                  diff=diff_adding("PLAIN=value", ".env")))))
        row = self.one_collected()
        self.assertIn("paths_not_credentials", self.one_verdict()["failed_checks"])
        self.assertEqual([".env"], row["facts"]["facts"]["paths"])
        self.assertTrue(row["facts"]["handle"] is True)
        self.assertNotIn("PLAIN=value", self.stored_text())

    def test_a_decline_for_a_secret_among_other_failed_checks_leaves_a_handle(self):
        self.run_hook(self.declined(head="b" * 40))
        self.assertIn("head_matches", self.one_verdict()["failed_checks"])
        self.assertTrue(self.one_collected()["facts"]["handle"] is True)

    def test_a_decline_for_another_reason_is_collected_as_before_and_is_no_handle(self):
        self.run_hook(self.engine(describe=described(commit_doc(head="b" * 40))))
        row = self.one_collected()
        self.assertNotIn("handle", row["facts"])
        self.assertEqual(COMMAND, row["command"])

    def test_an_approve_is_collected_as_before_and_is_no_handle(self):
        self.run_hook(self.engine())
        row = self.one_collected()
        self.assertNotIn("handle", row["facts"])
        self.assertEqual("approve", row["verdict"])

    def test_the_paths_come_from_the_three_path_facts_without_repeats_and_in_first_seen_order(self):
        self.record_with({"paths": ["dir/b.py", "a.txt"], "requested_paths": ["a.txt", "dir"], "target_paths": [".env", "dir/b.py"]})
        facts = self.one_collected()["facts"]["facts"]
        self.assertEqual((["dir/b.py", "a.txt", "dir", ".env"], 0), (facts["paths"], facts["paths_dropped"]))

    def test_confirm_is_copied_only_when_it_is_a_boolean(self):
        for value, expected in ((True, True), (False, False)):
            os_remove_rows(self.home)
            self.record_with({"paths": ["a.txt"], "confirm": value})
            self.assertEqual(expected, self.one_collected()["facts"]["facts"]["confirm"])
        for value in ("yes", 1, None, [True], {"a": 1}):
            os_remove_rows(self.home)
            self.record_with({"paths": ["a.txt"], "confirm": value})
            self.assertNotIn("confirm", self.one_collected()["facts"]["facts"], value)

    def record_with(self, inner, top=None, rule="safe-git-commit", facts_value=None, command=COMMAND, cwd=None, **kwargs):
        """Call `record` directly with facts the real engine would not print, as the test of facts that come with an outcome does."""
        facts = {"contract": 1, "action": "commit", "ok": True, "truncated": False, "errors": [], "facts": inner}
        facts.update(top or {})
        if facts_value is not None:
            facts = facts_value
        err = io.StringIO()
        verdict = ("decline", ["no_secret_lines"], "Declined.")
        self.mod.record(err, self.home, "reviewed", command, verdict, {"rule": rule} if rule is not None else None, facts,
                        cwd=self.cwd if cwd is None else cwd, **kwargs)
        return err.getvalue()

    def test_more_than_twenty_tracked_paths_keep_twenty_and_count_the_rest(self):
        names = ["f%02d.txt" % number for number in range(30)]
        self.track(*names)
        self.record_with({"paths": names})
        self.assertEqual((names[:20], 10), (self.one_collected()["facts"]["facts"]["paths"],
                                             self.one_collected()["facts"]["facts"]["paths_dropped"]))

    def test_nothing_outside_the_list_reaches_the_row_however_hostile_the_facts(self):
        inner = {"paths": ["a.txt", SENTINEL + "-path", "../" + SENTINEL, "/" + SENTINEL], "requested_paths": [SENTINEL + "/x"],
                 "diff": SENTINEL, "subject": SENTINEL, "body": SENTINEL, "trailers": [SENTINEL], "program_findings": [SENTINEL],
                 "head": SENTINEL, SENTINEL + "_KEY": SENTINEL, "confirm": SENTINEL, "paths_dropped": SENTINEL,
                 "handle": SENTINEL, "nested": {SENTINEL: [SENTINEL, {SENTINEL: SENTINEL}]}}
        top = {SENTINEL + "_TOP": SENTINEL, "errors": [{"code": SENTINEL, "message": SENTINEL}], "action": SENTINEL}
        self.record_with(inner, top)
        row = self.one_collected()
        self.assertNotIn(SENTINEL, json.dumps(row))
        self.assertNotIn(SENTINEL, self.stored_text())
        self.assertEqual({"handle", "facts"}, set(row["facts"]))
        self.assertTrue(set(row["facts"]["facts"]) <= {"paths", "paths_dropped", "confirm"})
        self.assertEqual(["a.txt"], row["facts"]["facts"]["paths"])
        self.assertEqual(4, row["facts"]["facts"]["paths_dropped"])

    def test_a_path_that_looks_like_a_token_is_dropped_unless_the_project_tracks_it(self):
        token = "glpat-a1b2c3d4e5f6g7h8i9j0"
        self.record_with({"paths": [token + ".txt", "dir/" + token]})
        facts = self.one_collected()["facts"]["facts"]
        self.assertEqual(([], 2), (facts["paths"], facts["paths_dropped"]))
        self.assertNotIn(token, self.stored_text())

    def test_a_tracked_path_is_kept_even_when_its_name_looks_like_a_token(self):
        """The residual risk the plan states: a secret that is already a tracked filename is already in the repository, and the
        handle repeats it. The admission rule is the index, not the redactor."""
        token = "glpat-a1b2c3d4e5f6g7h8i9j0.txt"
        self.track(token)
        self.record_with({"paths": [token]})
        self.assertEqual([token], self.one_collected()["facts"]["facts"]["paths"])

    def test_facts_that_are_not_what_the_engine_prints_leave_a_handle_with_no_path(self):
        shapes = [None, [], "text", 5, {"facts": None}, {"facts": []}, {"facts": "x"}, {"facts": {"paths": "a.txt"}},
                  {"facts": {"paths": {"a": "a.txt"}}}, {"nope": {"paths": ["a.txt"]}}]
        for number, shape in enumerate(shapes):
            with self.subTest(shape):
                os_remove_rows(self.home)
                err = self.record_with({}, facts_value=shape if shape is not None else {})
                self.assertEqual("", err)
                row = self.one_collected()
                self.assertEqual({"handle": True, "facts": {"paths": [], "paths_dropped": 0}}, row["facts"])

    def test_a_decline_with_no_facts_line_leaves_a_handle_with_no_path(self):
        err = io.StringIO()
        self.mod.record(err, self.home, "reviewed", COMMAND, ("decline", ["no_secret_lines"], "Declined."),
                        {"rule": "safe-git-commit"}, None, cwd=self.cwd)
        self.assertEqual("", err.getvalue())
        self.assertEqual({"handle": True, "facts": {"paths": [], "paths_dropped": 0}}, self.one_collected()["facts"])

    def test_no_working_directory_given_leaves_a_handle_with_no_path(self):
        err = io.StringIO()
        self.mod.record(err, self.home, "reviewed", COMMAND, ("decline", ["no_secret_lines"], "Declined."),
                        {"rule": "safe-git-commit"}, commit_doc(paths=["a.txt"]))
        self.assertEqual({"handle": True, "facts": {"paths": [], "paths_dropped": 1}}, self.one_collected()["facts"])

    def test_a_command_not_declined_for_a_secret_and_without_facts_leaves_no_handle(self):
        for verdict in (("approve", [], "Plain."), ("decline", ["scope_is_coherent"], "Mixed."), ("decline", ["head_matches"], "Moved.")):
            os_remove_rows(self.home)
            err = io.StringIO()
            self.mod.record(err, self.home, "reviewed", COMMAND, verdict, {"rule": "safe-git-commit"}, None, cwd=self.cwd)
            self.assertEqual(([], 0), self.rows("collected.jsonl"), verdict)
            self.assertEqual("", err.getvalue(), verdict)
            self.assertEqual(1, len(self.rows("verdicts.jsonl")[0]))

    def test_a_decline_whose_rule_is_not_a_string_leaves_the_verdict_row_only(self):
        for rule in (None, 5, ["safe-git-commit"], ""):
            os_remove_rows(self.home)
            err = io.StringIO()
            self.mod.record(err, self.home, "reviewed", COMMAND, ("decline", ["no_secret_lines"], "Declined."),
                            {"rule": rule} if rule is not None else None, commit_doc(), cwd=self.cwd)
            self.assertEqual(([], 0), self.rows("collected.jsonl"), rule)
            self.assertEqual(1, len(self.rows("verdicts.jsonl")[0]))
            if rule != "":
                self.assertEqual("", err.getvalue(), "no handle is even tried when the rule is not a string")

    def test_a_rule_the_store_refuses_leaves_the_verdict_row_and_a_fixed_note(self):
        err = self.record_with({"paths": ["a.txt"]}, rule="Not A Rule!")
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertEqual(1, len(self.rows("verdicts.jsonl")[0]))
        self.assertIn("could not record a row in collected.jsonl", err)

    def test_an_outcome_that_was_not_reviewed_leaves_no_handle(self):
        err = io.StringIO()
        self.mod.record(err, self.home, "failed", COMMAND, ("decline", ["no_secret_lines"], "Declined."),
                        {"rule": "safe-git-commit"}, commit_doc(), cwd=self.cwd)
        self.assertEqual(([], 0), self.rows("collected.jsonl"))

    def test_a_builder_that_fails_leaves_the_verdict_row_a_fixed_note_and_no_handle(self):
        with unittest.mock.patch.object(self.mod, "tracked_among", side_effect=RuntimeError(SENTINEL)):
            err = self.record_with({"paths": ["a.txt"]})
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertEqual(1, len(self.rows("verdicts.jsonl")[0]))
        self.assertIn("could not keep a handle", err)
        self.assertNotIn(SENTINEL, err)

    def test_a_store_that_refuses_the_handle_changes_nothing_else(self):
        real = self.store.append

        def refusing(name, row, home):
            if name == "collected.jsonl":
                raise self.store.StoreError("refused " + SENTINEL)
            return real(name, row, home)

        with unittest.mock.patch.object(self.mod.store, "append", side_effect=refusing):
            err = self.record_with({"paths": ["a.txt"]})
        self.assertEqual(1, len(self.rows("verdicts.jsonl")[0]))
        self.assertEqual(([], 0), self.rows("collected.jsonl"))
        self.assertIn("could not record a row in collected.jsonl", err)

    def test_an_engine_that_took_nearly_all_the_time_leaves_a_handle_without_reading_the_index(self):
        clock = iter([0.0] + [100.0] * 50)
        with unittest.mock.patch.object(self.mod.time, "monotonic", side_effect=lambda: next(clock)), \
                unittest.mock.patch.object(self.mod, "tracked_among", side_effect=AssertionError("read the index")):
            code, err = self.run_hook(self.declined(paths=["a.txt", "new.txt"]))
        self.assertEqual((0, ""), (code, err))
        self.assertEqual({"handle": True, "facts": {"paths": [], "paths_dropped": 2}}, self.one_collected()["facts"])

    def test_a_staged_new_file_is_in_the_index_and_its_name_is_admitted(self):
        """The rule is the index, not the repository's history: a file added and not yet committed is in the index. This pins the
        residual risk the spec states."""
        self.track("staged-only.txt")
        self.record_with({"paths": ["staged-only.txt"]})
        self.assertEqual(["staged-only.txt"], self.one_collected()["facts"]["facts"]["paths"])

    def test_the_hook_started_as_a_program_writes_the_handle_prints_nothing_and_exits_0(self):
        self.install_wb(self.declined(paths=["a.txt", "new.txt"]))
        run = self.program(["--wb", self.wb])
        self.assertEqual((0, b""), (run.returncode, run.stdout), run.stderr)
        row = self.one_collected()
        self.assertEqual(["a.txt"], row["facts"]["facts"]["paths"])
        self.assertEqual(FIXED_COMMAND, row["command"])

    def test_the_hook_reads_the_index_of_the_directory_the_command_runs_in_and_of_no_other(self):
        elsewhere = os.path.join(self.base, "elsewhere")
        os.makedirs(elsewhere)
        subprocess.run([GIT, "-C", elsewhere, "init", "-q"], env=self.env, capture_output=True, timeout=60, check=True)
        with open(os.path.join(elsewhere, "only-there.txt"), "w") as handle:
            handle.write("x")
        subprocess.run([GIT, "-C", elsewhere, "add", "--", "only-there.txt"], env=self.env, capture_output=True, timeout=60, check=True)
        self.record_with({"paths": ["only-there.txt", "a.txt"]})
        self.assertEqual(["a.txt"], self.one_collected()["facts"]["facts"]["paths"])


class SpecPins(unittest.TestCase):
    """The spec sentences that said a declined secret is never collected or labelled now describe the handle, and a later edit that
    brings the old claim back fails here."""

    REMOVED = (
        "A decline for a secret can therefore never be labelled",
        "is never\n  collected, so a false decline of that kind cannot be labelled",
        "A commit the engine declined for a secret is never collected",
        "(none for a command declined for a secret or a credential-named path)",
        "which leaves a verdict row and no collected row",
    )
    PRESENT = (
        "Labelling a declined secret (built",
        "one handle row",
        "leaves a handle",
    )

    def text(self):
        with open(SPEC, encoding="utf-8") as handle:
            return handle.read()

    def test_no_sentence_of_the_spec_says_a_declined_secret_is_never_collected_or_never_labelled(self):
        found = self.text()
        flat = " ".join(found.split())
        for phrase in self.REMOVED:
            self.assertNotIn(" ".join(phrase.split()), flat, phrase)

    def test_the_spec_says_what_the_handle_is_and_that_the_section_is_built(self):
        flat = " ".join(self.text().split())
        for phrase in self.PRESENT:
            self.assertIn(phrase, flat, phrase)
        self.assertNotIn("(proposed; not built;", flat)
        self.assertNotIn("Nothing here is built", flat)


if __name__ == "__main__":
    unittest.main()
