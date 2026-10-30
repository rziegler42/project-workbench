"""The store the shadow hook, the labelling tool and the report share (`docs/specs/action-review.md`, "The shadow hook",
"The data files").

Plan `2026-10-29-action-review-shadow-hook`, increment C. `hook/shadow_store.py` is a shipped file that the owner copies out of
the project, so it imports only the standard library. It keeps four files of strict JSON lines in
``~/.config/project-workbench/action-review/``: the directory is mode 0700, the files 0600, nothing is followed through a
link, a row is one append under a lock, and a row that does not fit its format is refused on write and skipped on read.
Written before the code."""

import ast
import importlib.util
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
import unittest.mock

from tests import support_install

ROOT = support_install.ROOT
SOURCE = os.path.join(ROOT, "packages", "workbench", "action-review", "hook", "shadow_store.py")
SHA = "a" * 64


def load():
    spec = importlib.util.spec_from_file_location("action_review_hook_store", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verdict_row(**changes):
    row = {"ts": "2026-10-30T01:02:03Z", "command_sha256": SHA, "outcome": "reviewed", "verdict": "approve",
           "failed_checks": [], "reason": "The change is plain.", "reviewed": True, "no_review_reason": None,
           "rule": "safe-git-commit", "facts_sha256": SHA, "rubric_sha256": SHA, "bridge": "ask-codex",
           "model": "m", "effort": "low", "format": 1}
    row.update(changes)
    return row


def collected_row(**changes):
    row = {"id": "0123456789abcdef0123456789abcdef", "ts": "2026-10-30T01:02:03Z", "rule": "safe-git-commit",
           "command_sha256": SHA, "command": "wb run safe-git commit -- a.txt",
           "facts": {"contract": 1, "action": "commit", "ok": True, "truncated": False, "errors": [], "facts": {}},
           "verdict": "approve", "failed_checks": [], "reason": "The change is plain."}
    row.update(changes)
    return row


def label_row(**changes):
    row = {"id": "0123456789abcdef0123456789abcdef", "label": "right", "ts": "2026-10-30T01:02:03Z"}
    row.update(changes)
    return row


def testset_row(**changes):
    row = {"case": "secret-in-diff", "ts": "2026-10-30T01:02:03Z", "expected": "decline", "verdict": "decline",
           "failed_checks": ["no_secret_lines"], "mismatch": False, "bridge": "ask-codex", "model": "m", "effort": None}
    row.update(changes)
    return row


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = load()

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.home = os.path.realpath(scratch.name)
        self.dir = os.path.join(self.home, ".config", "project-workbench", "action-review")

    def path(self, name):
        return os.path.join(self.dir, name)

    def lines(self, name):
        with open(self.path(name), "rb") as handle:
            return handle.read().splitlines(keepends=True)

    def mode(self, path):
        return stat.S_IMODE(os.stat(path).st_mode)

    def make_dir(self, mode=0o700):
        os.makedirs(os.path.join(self.home, ".config", "project-workbench"), mode=0o700)
        os.mkdir(self.dir, mode)
        os.chmod(self.dir, mode)


class Location(Base):
    def test_the_directory_is_below_the_guarded_store_in_the_home_directory(self):
        self.assertEqual(self.dir, self.store.data_dir(self.home))

    def test_the_default_comes_from_the_home_directory_and_nothing_else_moves_it(self):
        env = {"HOME": self.home, "XDG_CONFIG_HOME": "/elsewhere", "XDG_DATA_HOME": "/elsewhere",
               "WORKBENCH_HOME": "/elsewhere", "ACTION_REVIEW_DIR": "/elsewhere"}
        with unittest.mock.patch.dict(os.environ, env):
            self.assertEqual(self.dir, self.store.data_dir())

    def test_a_relative_or_missing_home_is_refused(self):
        for bad in ("", "relative/home", "a\0b"):
            with self.assertRaises(self.store.StoreError):
                self.store.data_dir(bad)

    def test_the_first_append_creates_the_store_and_the_directory_mode_0700_and_the_file_0600(self):
        self.store.append("labels.jsonl", label_row(), self.home)
        for path in (os.path.dirname(self.dir), self.dir):
            self.assertEqual(0o700, self.mode(path), path)
        self.assertEqual(0o600, self.mode(self.path("labels.jsonl")))

    def test_only_the_directory_below_the_store_is_made_and_nothing_else_in_the_store(self):
        self.store.append("labels.jsonl", label_row(), self.home)
        store = os.path.dirname(self.dir)
        self.assertEqual(["action-review"], os.listdir(store))
        self.assertEqual(["labels.jsonl"], os.listdir(self.dir))

    def test_a_link_for_the_ancestor_of_the_store_is_followed_as_the_store_does(self):
        real = os.path.join(self.home, "real-config")
        os.makedirs(real)
        os.symlink(real, os.path.join(self.home, ".config"))
        self.store.append("labels.jsonl", label_row(), self.home)
        self.assertTrue(os.path.isfile(os.path.join(real, "project-workbench", "action-review", "labels.jsonl")))


class Directories(Base):
    def test_an_existing_directory_with_a_wider_mode_is_refused_and_not_repaired(self):
        self.make_dir(0o755)
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)
        self.assertEqual(0o755, self.mode(self.dir))
        self.assertEqual([], os.listdir(self.dir))

    def test_a_store_root_with_a_wider_mode_is_refused(self):
        self.make_dir()
        os.chmod(os.path.dirname(self.dir), 0o755)
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)
        self.assertEqual([], os.listdir(self.dir))

    def test_a_link_in_place_of_the_directory_is_refused_and_nothing_is_written_through_it(self):
        self.make_dir()
        os.rmdir(self.dir)
        target = os.path.join(self.home, "other")
        os.mkdir(target, 0o700)
        os.symlink(target, self.dir)
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)
        self.assertEqual([], os.listdir(target))

    def test_a_link_in_place_of_the_store_root_is_refused(self):
        os.makedirs(os.path.join(self.home, ".config"))
        target = os.path.join(self.home, "other")
        os.mkdir(target, 0o700)
        os.symlink(target, os.path.join(self.home, ".config", "project-workbench"))
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)
        self.assertEqual([], os.listdir(target))

    def test_a_file_in_place_of_the_directory_is_refused(self):
        os.makedirs(os.path.join(self.home, ".config", "project-workbench"), mode=0o700)
        with open(self.dir, "w"):
            pass
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)


class Files(Base):
    def test_a_link_in_place_of_a_file_is_refused_and_the_target_is_not_written(self):
        self.make_dir()
        target = os.path.join(self.home, "victim")
        with open(target, "wb") as handle:
            handle.write(b"keep\n")
        os.chmod(target, 0o600)  # a target the store's own checks would accept, so only the link refuses it
        os.symlink(target, self.path("labels.jsonl"))
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)
        with open(target, "rb") as handle:
            self.assertEqual(b"keep\n", handle.read())
        with self.assertRaises(self.store.StoreError):
            self.store.read("labels.jsonl", self.home)

    def test_a_file_with_a_second_hard_link_is_refused_for_writing_and_reading(self):
        self.make_dir()
        other = os.path.join(self.home, "second")
        with open(self.path("labels.jsonl"), "wb") as handle:
            handle.write(b"")
        os.chmod(self.path("labels.jsonl"), 0o600)
        os.link(self.path("labels.jsonl"), other)
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)
        with self.assertRaises(self.store.StoreError):
            self.store.read("labels.jsonl", self.home)
        self.assertEqual(0, os.path.getsize(other))

    def test_a_file_with_a_wider_mode_is_refused_and_not_repaired(self):
        self.make_dir()
        with open(self.path("labels.jsonl"), "wb"):
            pass
        os.chmod(self.path("labels.jsonl"), 0o644)
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)
        with self.assertRaises(self.store.StoreError):
            self.store.read("labels.jsonl", self.home)
        self.assertEqual(0o644, self.mode(self.path("labels.jsonl")))

    def test_a_directory_or_file_of_another_owner_is_refused(self):
        self.store.append("labels.jsonl", label_row(), self.home)
        other = os.geteuid() + 1
        with unittest.mock.patch.object(self.store.os, "geteuid", return_value=other):
            with self.assertRaises(self.store.StoreError):  # the directory is refused
                self.store.append("labels.jsonl", label_row(), self.home)
            with unittest.mock.patch.object(self.store, "_check_directory"):  # and, apart from it, the file
                with self.assertRaises(self.store.StoreError):
                    self.store.append("labels.jsonl", label_row(), self.home)
                with self.assertRaises(self.store.StoreError):
                    self.store.read("labels.jsonl", self.home)

    def test_a_file_another_writer_holds_locked_is_not_waited_for_for_ever(self):
        import fcntl
        self.store.append("labels.jsonl", label_row(), self.home)
        holder = os.open(self.path("labels.jsonl"), os.O_RDONLY)
        self.addCleanup(os.close, holder)
        fcntl.flock(holder, fcntl.LOCK_EX)
        with unittest.mock.patch.object(self.store, "LOCK_SECONDS", 0.2):
            with self.assertRaises(self.store.StoreError):
                self.store.append("labels.jsonl", label_row(id="f" * 32), self.home)
        self.assertEqual(1, len(self.lines("labels.jsonl")))

    def test_a_directory_made_under_a_strict_umask_still_has_mode_0700(self):
        os.makedirs(os.path.join(self.home, ".config"))  # the owner's own directory, made before the strict umask
        old = os.umask(0o200)
        try:
            self.store.append("labels.jsonl", label_row(), self.home)
        finally:
            os.umask(old)
        self.assertEqual(0o700, self.mode(self.dir))
        self.assertEqual(0o700, self.mode(os.path.dirname(self.dir)))

    def test_a_directory_in_place_of_a_file_is_refused(self):
        self.make_dir()
        os.mkdir(self.path("labels.jsonl"), 0o700)
        with self.assertRaises(self.store.StoreError):
            self.store.append("labels.jsonl", label_row(), self.home)

    def test_a_name_that_is_not_one_of_the_four_files_is_refused(self):
        for name in ("settings", "../labels.jsonl", "labels.jsonl/x", "", "other.jsonl", "labels.jsonl\0"):
            with self.assertRaises(self.store.StoreError, msg=repr(name)):
                self.store.append(name, label_row(), self.home)
            with self.assertRaises(self.store.StoreError, msg=repr(name)):
                self.store.read(name, self.home)

    def test_a_file_over_the_size_cap_takes_no_more_rows_and_is_not_read(self):
        self.store.append("labels.jsonl", label_row(), self.home)
        with unittest.mock.patch.object(self.store, "MAX_FILE_BYTES", 10):
            with self.assertRaises(self.store.StoreError):
                self.store.append("labels.jsonl", label_row(), self.home)
            with self.assertRaises(self.store.StoreError):
                self.store.read("labels.jsonl", self.home)
        self.assertEqual(1, len(self.lines("labels.jsonl")))


class Appending(Base):
    def test_a_row_is_one_ascii_line_of_strict_json_that_ends_with_a_newline(self):
        self.store.append("collected.jsonl", collected_row(command="café ‮ 'x'"), self.home)
        (line,) = self.lines("collected.jsonl")
        self.assertTrue(line.endswith(b"\n"))
        self.assertEqual(1, line.count(b"\n"))
        self.assertTrue(all(32 <= byte < 127 or byte == 10 for byte in line))
        self.assertEqual("café ‮ 'x'", json.loads(line)["command"])

    def test_every_file_round_trips_its_rows_in_order(self):
        rows = {"verdicts.jsonl": [verdict_row(), verdict_row(outcome="no_rule", verdict=None, reviewed=False,
                                                              no_review_reason="no_rule", reason=None)],
                "collected.jsonl": [collected_row(), collected_row(id="f" * 32)],
                "labels.jsonl": [label_row(), label_row(label="skip", note="could not tell")],
                "testset.jsonl": [testset_row(), testset_row(case="head-mismatch")]}
        for name, items in rows.items():
            for row in items:
                self.store.append(name, row, self.home)
            got, skipped = self.store.read(name, self.home)
            self.assertEqual((items, 0), (got, skipped), name)

    def test_a_missing_file_reads_as_no_rows(self):
        self.assertEqual(([], 0), self.store.read("labels.jsonl", self.home))

    def test_the_caller_cannot_change_the_row_after_it_is_written(self):
        row = label_row()
        self.store.append("labels.jsonl", row, self.home)
        row["label"] = "wrong"
        self.assertEqual("right", self.store.read("labels.jsonl", self.home)[0][0]["label"])

    def test_a_row_the_format_refuses_is_not_written(self):
        bad = [
            ("labels.jsonl", label_row(extra=1)),
            ("labels.jsonl", {k: v for k, v in label_row().items() if k != "label"}),
            ("labels.jsonl", label_row(label="maybe")),
            ("labels.jsonl", label_row(id="short")),
            ("labels.jsonl", label_row(note="x" * 301)),
            ("labels.jsonl", label_row(note=5)),
            ("labels.jsonl", label_row(ts="yesterday")),
            ("labels.jsonl", [label_row()]),
            ("verdicts.jsonl", verdict_row(outcome="surprise")),
            ("verdicts.jsonl", verdict_row(reviewed=1)),
            ("verdicts.jsonl", verdict_row(reviewed=False)),
            ("verdicts.jsonl", verdict_row(outcome="no_rule", reviewed=False, no_review_reason=None, verdict=None)),
            ("verdicts.jsonl", verdict_row(outcome="no_rule", reviewed=False, no_review_reason="refused", verdict=None)),
            ("verdicts.jsonl", verdict_row(verdict="maybe")),
            ("verdicts.jsonl", verdict_row(failed_checks="head_matches")),
            ("verdicts.jsonl", verdict_row(failed_checks=["x"] * 33)),
            ("verdicts.jsonl", verdict_row(reason="x" * 301)),
            ("verdicts.jsonl", verdict_row(command_sha256="nothex")),
            ("verdicts.jsonl", verdict_row(command="wb run safe-git commit")),
            ("collected.jsonl", collected_row(command="x" * 4097)),
            ("collected.jsonl", collected_row(facts=[])),
            ("collected.jsonl", collected_row(verdict=None)),
            ("collected.jsonl", collected_row(facts={"blob": "x" * 700000})),
            ("testset.jsonl", testset_row(mismatch="no")),
            ("testset.jsonl", testset_row(expected="approve-ish")),
            ("testset.jsonl", testset_row(case="c" * 65)),
        ]
        for name, row in bad:
            with self.assertRaises(self.store.StoreError, msg=(name, row)):
                self.store.append(name, row, self.home)
        for name in {n for n, _ in bad}:
            self.assertEqual(([], 0), self.store.read(name, self.home), name)

    def test_a_row_that_is_not_json_data_is_not_written(self):
        for value in (float("nan"), float("inf"), object(), {1, 2}):
            with self.assertRaises(self.store.StoreError):
                self.store.append("collected.jsonl", collected_row(facts={"v": value}), self.home)

    def test_a_failed_write_raises_and_leaves_the_earlier_rows_whole(self):
        self.store.append("labels.jsonl", label_row(), self.home)
        before = self.lines("labels.jsonl")
        with unittest.mock.patch.object(self.store.os, "write", side_effect=OSError("disk full")):
            with self.assertRaises(self.store.StoreError):
                self.store.append("labels.jsonl", label_row(id="f" * 32), self.home)
        self.assertEqual(before, self.lines("labels.jsonl"))

    def test_a_write_that_fails_part_way_is_cut_back_to_the_earlier_rows(self):
        self.store.append("labels.jsonl", label_row(), self.home)
        before = self.lines("labels.jsonl")
        real = os.write
        calls = []

        def breaking(fd, data):
            calls.append(1)
            if len(calls) == 1:
                return real(fd, bytes(data[:9]))
            raise OSError("disk full")

        with unittest.mock.patch.object(self.store.os, "write", breaking):
            with self.assertRaises(self.store.StoreError):
                self.store.append("labels.jsonl", label_row(id="f" * 32), self.home)
        self.assertEqual(before, self.lines("labels.jsonl"))

    def test_a_row_whose_verdict_disagrees_with_its_failed_checks_is_not_written(self):
        bad = [("verdicts.jsonl", verdict_row(verdict="approve", failed_checks=["head_matches"])),
               ("verdicts.jsonl", verdict_row(verdict="decline", failed_checks=[])),
               ("collected.jsonl", collected_row(verdict="approve", failed_checks=["head_matches"])),
               ("collected.jsonl", collected_row(verdict="decline", failed_checks=[])),
               ("testset.jsonl", testset_row(expected="decline", verdict="decline", failed_checks=[])),
               ("testset.jsonl", testset_row(expected="approve", verdict="approve", failed_checks=["x"]))]
        for name, row in bad:
            with self.assertRaises(self.store.StoreError, msg=(name, row)):
                self.store.append(name, row, self.home)

    def test_a_row_marked_reviewed_with_an_outcome_that_was_not_is_not_written(self):
        row = verdict_row(outcome="no_rule", reviewed=True)  # the reviewed branch alone would accept it
        with self.assertRaises(self.store.StoreError):
            self.store.append("verdicts.jsonl", row, self.home)

    def test_a_fifo_in_place_of_a_file_is_refused_and_does_not_hang_the_opener(self):
        self.make_dir()
        os.mkfifo(self.path("labels.jsonl"), 0o600)
        for call in (lambda: self.store.append("labels.jsonl", label_row(), self.home),
                     lambda: self.store.read("labels.jsonl", self.home)):
            done = []
            thread = threading.Thread(target=lambda: done.append(self.result_of(call)), daemon=True)
            thread.start()
            thread.join(5)
            self.assertFalse(thread.is_alive(), "the opener is blocked on a FIFO")
            self.assertEqual(["StoreError"], done)

    def result_of(self, call):
        try:
            call()
        except self.store.StoreError:
            return "StoreError"
        return "returned"

    def test_a_row_after_a_torn_line_is_kept_and_the_fragment_stays_a_line_of_its_own(self):
        self.make_dir()
        with open(self.path("labels.jsonl"), "wb") as handle:
            handle.write(json.dumps(label_row()).encode() + b"\n" + b'{"id": "abc')
        os.chmod(self.path("labels.jsonl"), 0o600)
        self.store.append("labels.jsonl", label_row(id="f" * 32), self.home)
        rows, skipped = self.store.read("labels.jsonl", self.home)
        self.assertEqual([label_row(), label_row(id="f" * 32)], rows)
        self.assertEqual(1, skipped)

    def test_a_write_cut_short_by_an_interrupt_is_cut_back_and_the_interrupt_goes_on(self):
        self.store.append("labels.jsonl", label_row(), self.home)
        before = self.lines("labels.jsonl")
        real = os.write
        calls = []

        def interrupted(fd, data):
            calls.append(1)
            if len(calls) == 1:
                return real(fd, bytes(data[:9]))
            raise KeyboardInterrupt()

        with unittest.mock.patch.object(self.store.os, "write", interrupted):
            with self.assertRaises(KeyboardInterrupt):
                self.store.append("labels.jsonl", label_row(id="f" * 32), self.home)
        self.assertEqual(before, self.lines("labels.jsonl"))

    def test_a_long_note_of_characters_outside_the_basic_plane_still_fits_its_line(self):
        row = label_row(note="\U0001F600" * 300)
        self.store.append("labels.jsonl", row, self.home)
        self.assertEqual(([row], 0), self.store.read("labels.jsonl", self.home))

    def test_a_short_write_is_finished_as_one_row(self):
        real = os.write

        def short(fd, data):
            return real(fd, bytes(data[:7]))

        with unittest.mock.patch.object(self.store.os, "write", short):
            self.store.append("labels.jsonl", label_row(), self.home)
        self.assertEqual(([label_row()], 0), self.store.read("labels.jsonl", self.home))

    def test_writers_in_threads_do_not_interleave_their_rows(self):
        def writer(tag):
            for number in range(40):
                self.store.append("labels.jsonl", label_row(id=tag * 31 + format(number % 16, "x"),
                                                            note="n" * 200), self.home)

        threads = [threading.Thread(target=writer, args=(tag,)) for tag in "abcdef"]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        rows, skipped = self.store.read("labels.jsonl", self.home)
        self.assertEqual((240, 0), (len(rows), skipped))


class Reading(Base):
    def write_raw(self, name, data):
        self.make_dir() if not os.path.isdir(self.dir) else None
        with open(self.path(name), "ab") as handle:
            handle.write(data)
        os.chmod(self.path(name), 0o600)

    def test_a_line_the_format_refuses_is_skipped_and_counted_and_the_good_rows_are_kept(self):
        good = json.dumps(label_row()).encode()
        for raw in (b"not json", b"[1]", b"{}", b'{"id": 1}', b"", b"   ", b'{"id":"' + b"a" * 32 + b'","id":"' + b"b" * 32 + b'"}',
                    json.dumps(label_row(extra=1)).encode(), json.dumps(label_row(label="maybe")).encode(),
                    b'{"id": NaN}', b"\xff\xfe"):
            self.write_raw("labels.jsonl", raw + b"\n")
        self.write_raw("labels.jsonl", good + b"\n")
        rows, skipped = self.store.read("labels.jsonl", self.home)
        self.assertEqual([label_row()], rows)
        self.assertEqual(11, skipped)

    def test_a_line_the_store_would_not_have_written_is_skipped_too(self):
        # Raw non-ASCII text and a number too large for a float are not what `append` writes; the reader is as strict.
        self.write_raw("labels.jsonl", json.dumps(label_row(note="café"), ensure_ascii=False).encode() + b"\n")
        self.write_raw("labels.jsonl", json.dumps(label_row()).encode() + b"\n")
        self.assertEqual(([label_row()], 1), self.store.read("labels.jsonl", self.home))
        # `facts` is the one place a number can sit; a float too large for a float would read as infinity.
        huge = json.dumps(collected_row()).encode().replace(b'"facts": {', b'"facts": {"v": 1e999, ', 1)
        self.assertIn(b"1e999", huge)
        self.write_raw("collected.jsonl", huge + b"\n")
        self.write_raw("collected.jsonl", json.dumps(collected_row()).encode() + b"\n")
        self.assertEqual(([collected_row()], 1), self.store.read("collected.jsonl", self.home))

    def test_a_row_with_a_key_twice_is_skipped_even_when_every_field_is_there(self):
        text = json.dumps(label_row())
        twice = text[:-1] + ', "label": "wrong"}'
        self.assertEqual("wrong", json.loads(twice)["label"])  # a lenient reader would keep the last one
        self.write_raw("labels.jsonl", twice.encode() + b"\n")
        self.assertEqual(([], 1), self.store.read("labels.jsonl", self.home))

    def test_a_row_that_would_fit_but_for_its_line_cap_is_skipped(self):
        row = collected_row(facts={"blob": "x" * 600000})
        self.write_raw("collected.jsonl", json.dumps(row).encode() + b"\n")
        self.write_raw("collected.jsonl", json.dumps(collected_row()).encode() + b"\n")
        self.assertEqual(([collected_row()], 1), self.store.read("collected.jsonl", self.home))

    def test_a_last_line_without_a_newline_is_skipped_as_unfinished(self):
        self.write_raw("labels.jsonl", json.dumps(label_row()).encode() + b"\n")
        self.write_raw("labels.jsonl", json.dumps(label_row(id="f" * 32)).encode())
        rows, skipped = self.store.read("labels.jsonl", self.home)
        self.assertEqual(([label_row()], 1), (rows, skipped))

    def test_a_line_over_its_cap_is_skipped(self):
        self.write_raw("labels.jsonl", b'{"id":"' + b"a" * 5000 + b'"}\n')
        self.write_raw("labels.jsonl", json.dumps(label_row()).encode() + b"\n")
        self.assertEqual(([label_row()], 1), self.store.read("labels.jsonl", self.home))

    def test_the_cross_field_rule_of_a_verdict_row_holds_on_read_too(self):
        self.write_raw("verdicts.jsonl", json.dumps(verdict_row(reviewed=False)).encode() + b"\n")
        self.write_raw("verdicts.jsonl", json.dumps(verdict_row()).encode() + b"\n")
        self.assertEqual(([verdict_row()], 1), self.store.read("verdicts.jsonl", self.home))


class Ids(Base):
    def test_an_id_is_128_random_bits_as_32_hex_characters_and_differs_each_time(self):
        first, second = self.store.new_id(), self.store.new_id()
        self.assertRegex(first, r"^[0-9a-f]{32}$")
        self.assertNotEqual(first, second)


class Imports(Base):
    def test_the_file_imports_only_the_standard_library_so_that_it_can_be_copied_out(self):
        with open(SOURCE, "rb") as handle:
            tree = ast.parse(handle.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(0, node.level, "no relative import")
                names.add((node.module or "").split(".")[0])
        self.assertTrue(names <= set(sys.stdlib_module_names), sorted(names - set(sys.stdlib_module_names)))

    def test_the_file_has_no_command_line_entry_and_runs_nothing_when_imported(self):
        with open(SOURCE, "rb") as handle:
            text = handle.read().decode()
        self.assertNotIn("__main__", text)
        self.assertNotIn("subprocess", text)


if __name__ == "__main__":
    unittest.main()
