"""The state digest of `commit` (plan `2026-11-08-safe-git-commit-state-digest`, increment A; `docs/specs/safe-git.md`, "The state digest").

`describe commit` prints `state_digest`, a SHA-256 of the head and the mode and blob id of each named path as `git add` would stage it,
and `given_state_digest`, the value of `--state-digest`. `commit --state-digest <hex>` stages, recomputes the digest from the staged
entries, and refuses, unstaging, when it differs; it checks again just before `git commit` and compares the commit's blobs with the
digest afterwards. Real git and real repositories, built on the fixtures of the `describe commit` tests."""

import io
import os
import re
import stat
import unittest
import unittest.mock

import test_safegit_commit as C
import test_safegit_describe_commit as D
import test_safegit_describe_remove as DR
from support_git import REAL_GIT, git, needs_git

H = C.H
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
FACTS_AFTER_DIFF = ["state_digest", "given_state_digest", "omitted"]


@needs_git
class Digest(D.Describe):
    def with_digest(self, args, digest):
        at = args.index("--")
        return list(args[:at]) + ["--state-digest", digest] + list(args[at:])

    def facts(self, *paths, **kw):
        return self.describe(self.argv("S", *paths, **kw))["facts"]

    def digest(self, *paths, **kw):
        return self.facts(*paths, **kw)["state_digest"]

    def recomputed(self, paths, head="parent"):
        """The digest as the commit that was just made holds it, worked out here from `git ls-tree`. `head` is the parent the commit
        was made on: the first commit by default, ``None`` for a branch with no commit."""
        found = {}
        for item in git(self.repo, "ls-tree", "-r", "-z", "HEAD", "--", *paths).stdout.split("\0"):
            if item:
                meta, _, path = item.partition("\t")
                mode, _, blob = meta.split(" ")
                found[path] = (mode, blob)
        return H.state_digest(self.first if head == "parent" else head, [(path,) + found.get(path, (None, None)) for path in paths])

    def agrees(self, *paths, **kw):
        """`describe` gives a digest; `commit` given it commits; the commit holds the state the digest names."""
        args = self.argv("S", *paths, **kw)
        digest = self.describe(args)["facts"]["state_digest"]
        self.assertRegex(digest or "", HEX64)
        code, out, err = self.commit(*self.with_digest(args, digest))
        self.assertEqual((0, ""), (code, err), (out, err))
        self.assertEqual(digest, self.recomputed(paths))
        return digest


class Facts(Digest):
    def test_describe_prints_a_digest_and_no_given_one_after_the_other_facts(self):
        self.write("a.txt", "two\n")
        facts = self.facts("a.txt")
        self.assertRegex(facts["state_digest"], HEX64)
        self.assertIsNone(facts["given_state_digest"])
        self.assertEqual(FACTS_AFTER_DIFF, list(facts)[-3:])
        self.assertEqual(self.first, facts["head"])

    def test_describe_reports_the_digest_it_was_given_and_the_one_it_computes(self):
        self.write("a.txt", "two\n")
        real = self.digest("a.txt")
        for given in ("0" * 64, real):
            built = self.describe(self.with_digest(self.argv("S", "a.txt"), given))
            self.assertTrue(built["ok"], built)
            self.assertEqual((given, real), (built["facts"]["given_state_digest"], built["facts"]["state_digest"]))

    def test_no_digest_is_offered_with_the_option_that_commit_refuses_it_with(self):
        self.write("a.txt", "two\n")
        self.write("other.txt", "o\n")
        git(self.repo, "add", "other.txt")
        built = self.describe(self.argv("S", "a.txt", leave=True))
        self.assertTrue(built["ok"], built)
        self.assertIsNone(built["facts"]["state_digest"])
        git(self.repo, "reset", "-q", "other.txt")
        self.assertRegex(self.digest("a.txt") or "", HEX64)      # the same path without the option gets one

    def test_describe_changes_nothing(self):
        self.write("a.txt", "two\n")
        self.write("n.txt", "new\n")
        before = DR.snapshot(self.repo)
        self.describe(self.with_digest(self.argv("S", "a.txt", "n.txt"), "1" * 64))
        self.assertEqual(before, DR.snapshot(self.repo))
        self.assertEqual("", git(self.repo, "diff", "--cached", "--name-only").stdout)

    def test_a_refused_describe_has_the_two_facts_too_and_no_digest(self):
        built = self.describe(self.argv("S", "no-such.txt"))
        self.assertFalse(built["ok"])
        self.assertEqual((None, None), (built["facts"]["state_digest"], built["facts"]["given_state_digest"]))
        self.assertEqual(FACTS_AFTER_DIFF, list(built["facts"])[-3:])

    def test_the_message_is_not_part_of_the_digest(self):
        self.write("a.txt", "two\n")
        first = self.digest("a.txt")
        self.assertEqual(first, self.facts("a.txt")["state_digest"])
        other = self.describe(self.argv("Another subject", "a.txt", body="and a body", trailers=["Plan: x#A"]))["facts"]["state_digest"]
        self.assertEqual(first, other)


class Agreement(Digest):
    """`describe` and `commit` give the same digest for each state, and the commit holds what it names."""

    def test_a_modified_file(self):
        self.write("a.txt", "two\n")
        self.agrees("a.txt")

    def test_a_new_file(self):
        self.write("n.txt", "new\n")
        self.agrees("n.txt")

    def test_a_deleted_file(self):
        os.remove(os.path.join(self.repo, "a.txt"))
        self.agrees("a.txt")
        self.assertEqual("", git(self.repo, "ls-tree", "-r", "--name-only", "HEAD").stdout)

    def test_a_new_executable_file(self):
        self.write("x.sh", "echo\n", mode=0o755)
        self.agrees("x.sh")
        self.assertIn("100755", git(self.repo, "ls-tree", "HEAD", "x.sh").stdout)

    def test_a_change_of_mode_alone(self):
        os.chmod(os.path.join(self.repo, "a.txt"), 0o755)
        self.agrees("a.txt")
        self.assertIn("100755", git(self.repo, "ls-tree", "HEAD", "a.txt").stdout)

    def test_an_empty_new_file(self):
        self.write("e.txt", "")
        self.agrees("e.txt")

    def test_a_path_with_a_non_ascii_name_and_a_nested_one(self):
        self.write("café/ü.txt", "x\n")
        self.write("dir/sub/x.txt", "y\n")
        self.agrees("café/ü.txt", "dir/sub/x.txt")

    def test_several_paths_in_any_order_give_one_digest(self):
        self.write("a.txt", "two\n")
        self.write("b.txt", "bee\n")
        self.write("c.txt", "sea\n")
        forward = self.digest("a.txt", "b.txt", "c.txt")
        self.assertEqual(forward, self.digest("c.txt", "a.txt", "b.txt"))
        self.assertEqual(forward, self.agrees("b.txt", "c.txt", "a.txt"))

    def test_a_file_with_carriage_returns_when_nothing_converts_it(self):
        # git's own whitespace check calls a trailing carriage return an error unless it is told otherwise; that is not the digest
        self.config("core.whitespace", "cr-at-eol")
        self.write("c.txt", b"a\r\nb\r\n")
        self.agrees("c.txt")
        self.assertEqual("6", git(self.repo, "cat-file", "-s", "HEAD:c.txt").stdout.strip())      # the bytes as written, carriage returns kept

    def test_a_file_with_carriage_returns_in_a_repository_with_text_auto_is_not_digested(self):
        """`git add` would store converted bytes, so no digest is offered; a file without a carriage return still gets one."""
        self.write(".gitattributes", "*.txt text=auto\n")
        git(self.repo, "add", ".gitattributes")
        git(self.repo, "commit", "-q", "-m", "attrs")
        self.first = self.head()
        self.write("c.txt", b"a\r\nb\r\n")
        self.write("l.txt", "a\nb\n")
        self.assertIsNone(self.digest("c.txt"))
        self.assertTrue(self.describe(self.argv("S", "c.txt"))["ok"])
        self.assertRegex(self.digest("l.txt") or "", HEX64)
        self.agrees("l.txt")

    def test_a_file_with_carriage_returns_with_core_autocrlf_is_not_digested(self):
        for value in ("true", "input"):
            with self.subTest(value=value):
                self.config("core.autocrlf", value)
                self.write("c.txt", b"a\r\nb\r\n")
                self.assertIsNone(self.digest("c.txt"))
        self.config("core.autocrlf", "false")
        self.assertRegex(self.digest("c.txt") or "", HEX64)

    def test_a_file_over_the_read_limit_is_not_digested(self):
        self.write("big.bin", b"x" * (H.MAX_SIDE + 1))
        built = self.describe(self.argv("S", "big.bin"))
        self.assertIsNone(built["facts"]["state_digest"])

    def test_an_intent_to_add_path(self):
        self.write("n.txt", "new\n")
        git(self.repo, "add", "-N", "n.txt")
        self.agrees("n.txt")

    def test_an_intent_to_add_path_that_was_then_deleted_gets_no_digest(self):
        self.write("n.txt", "new\n")
        git(self.repo, "add", "-N", "n.txt")
        os.remove(os.path.join(self.repo, "n.txt"))
        built = self.describe(self.argv("S", "n.txt"))
        self.assertIsNone(built["facts"]["state_digest"], built)

    def test_a_branch_with_no_commit(self):
        git(self.repo, "symbolic-ref", "HEAD", "refs/heads/fresh")
        git(self.repo, "rm", "--cached", "-q", "a.txt")
        args = self.argv("S", "a.txt", expected="none")
        digest = self.describe(args)["facts"]["state_digest"]
        self.assertRegex(digest or "", HEX64)
        code, out, err = self.commit(*self.with_digest(args, digest))
        self.assertEqual((0, ""), (code, err), out)
        self.assertEqual(digest, self.recomputed(["a.txt"], head=None))


class Listings(unittest.TestCase):
    """The reader of the index and tree listings refuses what it does not understand. These forms cannot be made with a real repository in
    a test, because earlier checks refuse them first; they can appear if the index changes while the helper runs."""

    def refused(self, listing, kind, paths=("p",)):
        with self.assertRaises(H.Refused) as raised:
            H._entries_of(listing, kind, list(paths), "the entries")
        self.assertEqual("index_unreadable", raised.exception.code)

    def test_a_conflict_stage_is_refused(self):
        for stage in ("1", "2", "3"):
            self.refused("100644 %s %s\tp\0" % ("a" * 40, stage), "index")

    def test_an_entry_that_is_not_three_fields_is_refused(self):
        self.refused("100644 %s\tp\0" % ("a" * 40), "index")
        self.refused("100644 %s 0 x\tp\0" % ("a" * 40), "index")

    def test_a_path_that_was_not_asked_for_or_is_listed_twice_is_refused(self):
        self.refused("100644 %s 0\tq\0" % ("a" * 40), "index")
        self.refused("100644 %s 0\tp\0100644 %s 0\tp\0" % ("a" * 40, "b" * 40), "index")

    def test_a_tree_entry_that_is_not_a_file_is_refused(self):
        self.refused("160000 commit %s\tp\0" % ("a" * 40), "tree")
        self.refused("040000 tree %s\tp\0" % ("a" * 40), "tree")

    def test_the_good_forms_are_read(self):
        self.assertEqual({"p": ("100644", "a" * 40)}, H._entries_of("100644 %s 0\tp\0" % ("a" * 40), "index", ["p"], "x"))
        self.assertEqual({"p": ("100755", "b" * 40)}, H._entries_of("100755 blob %s\tp\0" % ("b" * 40), "tree", ["p"], "x"))
        self.assertEqual({}, H._entries_of("", "index", ["p"], "x"))


@needs_git
class Raced(Digest):
    def test_a_named_file_that_turns_into_something_else_after_the_checks_gives_no_digest(self):
        self.write("a.txt", "two\n")
        with unittest.mock.patch.object(H, "_read_work", side_effect=lambda fd, parts: ("irregular",)):
            built = self.describe(self.argv("S", "a.txt"))
        self.assertIsNone(built["facts"]["state_digest"])
        self.assertEqual(["a.txt"], built["facts"]["not_regular_paths"])
        self.assertRegex(self.digest("a.txt") or "", HEX64)      # the stub is gone with the block


class Sensitivity(Digest):
    """Every input that decides what the commit records changes the digest."""

    def test_each_input_changes_it_and_a_repeat_does_not(self):
        self.write("a.txt", "two\n")
        base = self.digest("a.txt")
        self.assertEqual(base, self.digest("a.txt"))
        self.write("a.txt", "twp\n")
        changed_byte = self.digest("a.txt")
        self.write("a.txt", "two\n")
        self.assertEqual(base, self.digest("a.txt"))
        os.chmod(os.path.join(self.repo, "a.txt"), 0o755)
        changed_mode = self.digest("a.txt")
        os.chmod(os.path.join(self.repo, "a.txt"), 0o644)
        self.write("b.txt", "bee\n")
        more_paths = self.digest("a.txt", "b.txt")
        os.remove(os.path.join(self.repo, "a.txt"))
        deleted = self.digest("a.txt")
        self.write("a.txt", "two\n")
        git(self.repo, "add", "b.txt")
        git(self.repo, "commit", "-q", "-m", "second")
        new_head = self.digest("a.txt", expected=self.head())
        self.assertEqual(6, len({base, changed_byte, changed_mode, more_paths, deleted, new_head}))
        for value in (base, changed_byte, changed_mode, more_paths, deleted, new_head):
            self.assertRegex(value, HEX64)


class Refusals(Digest):
    def setUp(self):
        super().setUp()
        self.write("a.txt", "two\n")
        self.index_before = self.index()

    def untouched(self, result, text=None):
        self.assertRefused(result, text)
        self.assertUntouched(self.index_before)
        self.assertEqual("two\n", open(os.path.join(self.repo, "a.txt")).read())

    def test_a_digest_of_the_wrong_form(self):
        for value in ("", "0" * 63, "0" * 65, "A" * 64, "g" * 64, "0" * 64 + "\n", " " + "0" * 63, "0x" + "0" * 62):
            with self.subTest(value=value):
                self.untouched(self.commit(*self.with_digest(self.argv("S", "a.txt"), value)), "--state-digest")

    def test_a_digest_given_twice(self):
        args = self.with_digest(self.with_digest(self.argv("S", "a.txt"), "0" * 64), "0" * 64)
        self.untouched(self.commit(*args), "more than once")

    def test_a_digest_without_a_value(self):
        args = ["--expected-head", self.first, "--subject", "S", "--state-digest"]
        self.untouched(self.commit(*args), "needs a value")

    def test_a_digest_with_the_option_that_leaves_other_staged_work(self):
        self.untouched(self.commit(*self.with_digest(self.argv("S", "a.txt", leave=True), "0" * 64)), "--leave-other-staged")

    def test_a_digest_that_is_not_the_state_is_refused_and_nothing_is_staged(self):
        self.untouched(self.commit(*self.with_digest(self.argv("S", "a.txt"), "0" * 64)), "state digest")

    def test_a_file_changed_after_describe_is_refused(self):
        args = self.argv("S", "a.txt")
        digest = self.digest("a.txt")
        self.write("a.txt", "three\n")
        code, out, err = self.commit(*self.with_digest(args, digest))
        self.assertRefused((code, out, err), "state digest")
        self.assertEqual(self.first, self.head())
        self.assertEqual("", git(self.repo, "diff", "--cached", "--name-only").stdout)
        self.assertEqual("three\n", open(os.path.join(self.repo, "a.txt")).read())

    def test_the_first_check_comes_before_the_whitespace_check(self):
        """A new file is not seen by the whitespace check made before staging, only by the cached one after it. A stale digest must be
        refused by the digest check that runs first, so the refusal names the state digest and not the whitespace error."""
        self.write("n.txt", "x\n")
        args = self.argv("S", "n.txt")
        digest = self.digest("n.txt")
        self.write("n.txt", "y \n")
        self.assertRefused(self.commit(*self.with_digest(args, digest)), "state digest")
        self.assertEqual("", git(self.repo, "diff", "--cached", "--name-only").stdout)

    def test_a_head_that_moved_after_describe_is_refused_with_the_head_message(self):
        args = self.argv("S", "a.txt")
        digest = self.digest("a.txt")
        self.write("b.txt", "bee\n")
        git(self.repo, "add", "b.txt")
        git(self.repo, "commit", "-q", "-m", "second")
        self.assertRefused(self.commit(*self.with_digest(args, digest)), "HEAD moved")

    def test_without_the_option_the_command_is_as_before(self):
        self.assertEqual(0, self.commit(*self.argv("S", "a.txt"))[0])


class Configuration(Digest):
    def setUp(self):
        super().setUp()
        self.write("a.txt", "two\n")

    def test_core_filemode_false_gives_no_digest_and_the_command_refuses_one(self):
        self.config("core.fileMode", "false")
        built = self.describe(self.argv("S", "a.txt"))
        self.assertTrue(built["ok"], built)
        self.assertIsNone(built["facts"]["state_digest"])
        given = self.describe(self.with_digest(self.argv("S", "a.txt"), "0" * 64))
        self.assertEqual(["state_digest_unsupported"], self.codes(given))
        self.assertFalse(given["ok"])
        before = self.index()
        self.assertRefused(self.commit(*self.with_digest(self.argv("S", "a.txt"), "0" * 64)), "core.fileMode")
        self.assertUntouched(before)
        self.assertEqual(0, self.commit(*self.argv("S", "a.txt"))[0])

    def test_core_filemode_true_or_unset_is_supported(self):
        for value in ("true", "yes", "1", "on"):
            with self.subTest(value=value):
                self.config("core.fileMode", value)
                self.assertRegex(self.digest("a.txt") or "", HEX64)
        git(self.repo, "config", "--unset", "core.fileMode")
        self.assertRegex(self.digest("a.txt") or "", HEX64)

    def test_a_repository_that_does_not_use_sha1_is_not_supported(self):
        other = os.path.join(self.scratch, "sha256")
        os.mkdir(other)
        made = git(other, "init", "-q", "--object-format=sha256", check=False)
        if made.returncode:
            self.skipTest("this git has no sha256 repositories")
        with open(os.path.join(other, "n.txt"), "w") as handle:
            handle.write("x\n")
        args = ["--expected-head", "none", "--subject", "S", "--", "n.txt"]
        self.assertIsNone(self.describe(args, cwd=other)["facts"]["state_digest"])
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.dict(os.environ, self.environment(), clear=True):
            code = H.main(["commit", "--expected-head", "none", "--subject", "S", "--state-digest", "0" * 64, "--", "n.txt"],
                          out, err, other)
        self.assertEqual(1, code)
        self.assertIn("SHA-1", err.getvalue())


class StandIn(Digest):
    """A `git` that changes something at a chosen moment, found first on the PATH the helper is given."""

    def stand_in(self, command, action):
        """A directory with a `git` that, when run with `command` as its first argument, first runs `action` (shell text),
        then the real git."""
        directory = os.path.join(self.scratch, "standin")
        os.makedirs(directory, exist_ok=True)
        script = os.path.join(directory, "git")
        with open(script, "w") as handle:
            handle.write("#!/bin/sh\nif [ \"$1\" = %s ]; then\n%s\nfi\nexec '%s' \"$@\"\n" % (command, action, REAL_GIT))
        os.chmod(script, 0o755)
        return directory + os.pathsep + C.STANDARD

    def restage_a_changed_file(self):
        return "printf 'changed\\n' >> '%s/a.txt'\n'%s' add -- a.txt\n" % (self.repo, REAL_GIT)

    def between_the_checks(self):
        """Run only for the cached whitespace check, which `commit` makes between its two digest checks (not for the other `git diff`
        runs, one of which comes before the first check)."""
        return "if [ \"$2\" = --cached ] && [ \"$3\" = --check ]; then\n%s\nfi" % self.restage_a_changed_file()

    def test_a_change_between_the_two_checks_is_refused_at_the_second(self):
        self.write("a.txt", "two\n")
        args = self.argv("S", "a.txt")
        digest = self.digest("a.txt")
        path = self.stand_in("diff", self.between_the_checks())
        code, out, err = self.commit(*self.with_digest(args, digest), path=path)
        self.assertRefused((code, out, err), "state digest")
        self.assertIn("unstaged", err)
        self.assertEqual(self.first, self.head())
        self.assertEqual("", git(self.repo, "diff", "--cached", "--name-only").stdout)

    def test_the_same_stand_in_lets_a_commit_with_no_digest_through_so_it_does_what_it_says(self):
        self.write("a.txt", "two\n")
        path = self.stand_in("diff", self.between_the_checks())
        code, out, err = self.commit(*self.argv("S", "a.txt"), path=path)
        self.assertEqual(0, code, err)
        self.assertEqual("two\nchanged\n", git(self.repo, "show", "HEAD:a.txt").stdout)

    def test_a_commit_that_holds_another_state_is_reported_after_the_fact(self):
        self.write("a.txt", "two\n")
        args = self.argv("S", "a.txt")
        digest = self.digest("a.txt")
        path = self.stand_in("commit", self.restage_a_changed_file())
        code, out, err = self.commit(*self.with_digest(args, digest), path=path)
        self.assertEqual((1, ""), (code, out), err)
        self.assertIn("state digest", err)
        self.assertIn("nothing was undone", err)
        self.assertNotEqual(self.first, self.head())


if __name__ == "__main__":
    unittest.main()
