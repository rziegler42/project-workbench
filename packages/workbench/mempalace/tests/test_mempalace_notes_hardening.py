"""Plan `2026-11-06-mempalace-notes`, increments B and C: the findings of the security review of the write side (2026-11-06). A note chosen by an agent must not stall the
helper, a resumed `keep` must move only what the owner reviewed, the credential scan must know the common shapes, and the limits must hold. The design is
`docs/specs/mempalace-notes.md`. No test starts a process or reaches a network."""

import os
import time
import unittest
import unittest.mock

import support_notes


def prose(tag, words=70):
    return " ".join("%s%03dx" % (tag, number) for number in range(words))


def fake(*parts):
    """A credential-shaped string built from pieces, so that this file holds no token shape."""
    return "".join(parts)


class Hardening(support_notes.Notes):
    def setUp(self):
        support_notes.Notes.setUp(self)
        self.setting('{"format": 1, "wing": "proj"}')
        self.note("reviewed", "proj", "anchor", title="Anchor", body=prose("anchor") + "\n")

    def draft(self, name, tag=None, **fields):
        fields.setdefault("title", name.replace("-", " ").title())
        fields.setdefault("body", prose(tag or name.replace("-", "")) + "\n")
        return self.note("draft", "proj", name, **fields)

    def path(self, state, name, wing="proj"):
        return os.path.join(self.folder(state, wing), name + ".txt")

    def text(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def review(self, *extra):
        code, out, err = self.run_helper("review", *extra)
        self.assertEqual((0, ""), (code, err), err)
        lines = out.rstrip("\n").split("\n")
        return "\n".join(lines[:-1]), lines[-1].split()[1]

    def keep(self, digest, wing="proj"):
        return self.run_helper("keep", "--wing", wing, "--digest", digest)

    def save(self, title, body, kind="idea", *extra):
        return self.run_helper("save", "--title", title, "--kind", kind, "--body", body, *extra)


class Cost(Hardening):
    """One note must not make the scan, the review or the keep take long."""

    def test_a_long_line_of_dots_or_letters_is_scanned_quickly(self):
        for label, line in (("dots", "a." * 7000), ("letters", "a" * 15000), ("dashes", "a-" * 7000), ("colons", "a:" * 7000), ("slashes", "a/" * 7000),
                            ("equals", "a=" * 7000), ("schemes", "ab+" * 5000 + "://"), ("dots and a colon", "a." * 7000 + ":"), ("letters and an equals sign", "a" * 15000 + "="),
                            ("dashes and a scheme", "a-" * 7000 + "://"), ("dots, a scheme and an at sign", "a." * 6000 + "://x:y")):
            started = time.monotonic()
            hits = self.helper.credential_hits("title: x\n\n" + line)
            elapsed = time.monotonic() - started
            self.assertLess(elapsed, 0.5, "%s took %.2f s (%s)" % (label, elapsed, hits))

    def test_a_save_of_such_a_note_and_a_review_of_several_are_quick(self):
        started = time.monotonic()
        code, out, err = self.save("Dots", "a." * 7000)
        self.assertEqual(0, code, err)
        self.assertLess(time.monotonic() - started, 2.0)
        for number in range(3):
            self.draft("slow-%d" % number, body="a." * 7000 + str(number) + "\n")
        started = time.monotonic()
        self.review()
        self.assertLess(time.monotonic() - started, 3.0)

    def test_the_words_of_a_note_are_worked_out_once_for_a_review(self):
        for number in range(30):
            self.draft("note-%02d" % number, "nt%02d" % number)
        real = self.helper.words
        calls = []
        with unittest.mock.patch.object(self.helper, "words", lambda text: calls.append(1) or real(text)):
            self.review()
        self.assertLessEqual(len(calls), 3 * 31, "words() was called %d times for 31 notes" % len(calls))


class Shapes(Hardening):
    SHAPES = {
        "stripe-key": fake("sk", "_live_", "a1" * 12),
        "npm-token": fake("npm", "_", "a" * 36),
        "gitlab-token": fake("glpat", "-", "a" * 22),
        "aws-access-key-id": fake("AS", "IA", "B" * 16),
        "basic-auth-header": "Authorization: " + "Basic " + "dXNlcjpwYXNzd29yZDEyMzQ1",
        "url-with-password": "redis://:" + "pw" + "@cache.example",
        "assigned-secret-pwd": "p" + "wd=hunter2hunter",
        "assigned-secret-passphrase": "pass" + "phrase: correct-horse-battery",
        "assigned-secret-credentials": "credentials = " + "s3cr3tvalue1",
        "assigned-secret-arrow": "pass" + "word => hunter2hunter",
        "assigned-secret-walrus": "sec" + "ret := hunter2hunter",
        "fullwidth": "ＡＫＩＡ" + "A" * 16,   # the fullwidth form of the key prefix, which a normaliser reads as the plain one
    }

    def test_the_common_shapes_the_review_found_missing_are_refused_without_echoing_them(self):
        for label, secret in self.SHAPES.items():
            code, out, err = self.save("Shape " + label, prose("alpha", 40) + "\n" + secret)
            self.assertEqual((1, ""), (code, out), label)
            self.assertIn("line 8", err, label)
            self.assertNotIn(secret[-8:], err, label)

    def test_ordinary_text_is_still_saved(self):
        body = prose("alpha", 40) + "\nthe token limit: 100000 tokens per request\nask for the secret: ask\nbypass the cache when the key is cold\nthe pass is open: yes\n"
        self.assertEqual(0, self.save("Benign", body)[0])


class Journal(Hardening):
    """A resumed keep moves the drafts the owner reviewed and nothing else."""

    def setUp(self):
        Hardening.setUp(self)
        self.draft("one", "ra")
        self.draft("two", "rb")
        self.digest = self.review()[1]
        self.journal = os.path.join(self.folder("draft", "proj"), ".keep")

    def crash_after_the_first_move(self):
        real = self.helper.move_one
        calls = []

        class Boom(BaseException):
            pass

        def crashing(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                raise Boom
            return real(*args, **kwargs)

        with unittest.mock.patch.object(self.helper, "move_one", crashing):
            with self.assertRaises(Boom):
                self.keep(self.digest)
        self.assertTrue(os.path.isfile(self.journal))

    def test_a_draft_swapped_after_the_crash_is_not_moved_and_the_owner_is_told(self):
        self.crash_after_the_first_move()
        with open(self.path("draft", "two"), "a") as handle:
            handle.write("\nswapped after the crash\n")
        code, out, err = self.keep(self.digest)
        self.assertEqual((1, ""), (code, out))
        self.assertIn("changed after the keep began", err)
        self.assertFalse(os.path.exists(self.path("reviewed", "two")))
        self.assertTrue(os.path.isfile(self.path("draft", "two")))

    def test_an_agent_verb_that_finds_a_journal_with_a_swapped_draft_moves_nothing_and_goes_on(self):
        self.crash_after_the_first_move()
        with open(self.path("draft", "two"), "a") as handle:
            handle.write("\nswapped after the crash\n")
        self.assertEqual(0, self.run_helper("list")[0])
        self.assertFalse(os.path.exists(self.path("reviewed", "two")))

    def test_a_forged_journal_with_a_hash_that_is_not_the_drafts_moves_nothing(self):
        with open(self.journal, "w") as handle:
            handle.write("keep 1\ndigest " + "a" * 32 + "\nnew one.txt " + "b" * 32 + "\n")
        self.assertEqual(0, self.run_helper("list")[0])
        self.assertFalse(os.path.exists(self.path("reviewed", "one")))
        self.assertTrue(os.path.isfile(self.path("draft", "one")))

    def test_a_revision_entry_must_name_the_note_the_draft_revises(self):
        self.draft("anchor", title="Anchor", body=prose("anchor") + "\n\n(added 2026-11-06) x\n", extra=("revises: anchor",), written="2026-11-01")
        with open(self.path("draft", "anchor"), "rb") as handle:
            data = handle.read()
        fingerprint = self.helper.note_hash(data)
        with open(self.journal, "w") as handle:
            handle.write("keep 1\ndigest " + "a" * 32 + "\nrevise anchor.txt one.txt " + fingerprint + "\n")   # a revision of anchor aimed at the note called one
        self.assertEqual(0, self.run_helper("list")[0])
        self.assertTrue(os.path.isfile(self.path("draft", "anchor")))
        self.assertFalse(os.path.exists(self.path("reviewed", "one")))

    def test_a_journal_is_settled_before_the_expiry_so_a_stale_journaled_draft_is_filed_and_not_archived(self):
        self.draft("old", "ol", updated="2026-09-01")   # more than 30 days before the fixed clock
        with open(self.path("draft", "old"), "rb") as handle:
            fingerprint = self.helper.note_hash(handle.read())
        for name in ("one", "two"):
            os.remove(self.path("draft", name))
        with open(self.journal, "w") as handle:
            handle.write("keep 1\ndigest " + "a" * 32 + "\nnew old.txt " + fingerprint + "\n")
        self.assertEqual(0, self.run_helper("list")[0])
        self.assertTrue(os.path.isfile(self.path("reviewed", "old")))
        self.assertFalse(os.path.exists(os.path.join(self.folder("archived", "proj"), "old.txt")))


class Limits(Hardening):
    def test_a_wing_that_holds_the_most_drafts_takes_no_new_one_but_an_existing_one_can_be_extended(self):
        for number in range(self.helper.MAX_KEEP):
            self.draft("d-%03d" % number, "dd%03d" % number)
        self.assertGreater(self.helper.MAX_KEEP, 0)
        code, out, err = self.save("One too many", prose("zz"))
        self.assertEqual((1, ""), (code, out))
        self.assertIn("drafts", err)
        self.assertEqual(0, self.save("x", "an addition", "idea", "--into", "d-000")[0])
        code, out, err = self.save("x", "a revision", "idea", "--into", "anchor")
        self.assertEqual(1, code)   # a revision draft is a new draft file

    def test_a_save_that_would_make_one_wing_too_many_is_refused(self):
        for number in range(self.helper.MAX_WINGS):
            os.makedirs(os.path.join(self.notes, "wing-%02d" % number))
        code, out, err = self.save("T", prose("zz"), "idea", "--wing", "one-more")
        self.assertEqual((1, ""), (code, out))
        self.assertIn("wings", err)
        self.assertEqual(0, self.save("T", prose("zz"), "idea", "--wing", "wing-00")[0])


class Review(Hardening):
    def test_a_big_revision_is_always_shown_whatever_the_backlog(self):
        self.note("reviewed", "proj", "zz-last", title="Last", body=prose("zl") + "\n")   # its revision sorts after the whole backlog
        for number in range(60):
            self.draft("backlog-%02d" % number, "bk%02d" % number, updated="2026-10-20")
        self.draft("zz-last", title="Last", body=prose("zl", 10) + "\n", extra=("revises: zz-last",), written="2026-11-01")
        shown, _ = self.review()
        self.assertRegex(shown, r"zz-last .*changes more than half of zz-last")
        self.assertNotIn("backlog-59", shown)


class Names(Hardening):
    def test_a_wing_prefix_with_a_control_character_is_refused_and_not_echoed(self):
        self.draft("source-one", "src")
        self.draft("target-one", "tgt")
        for raw in ("a\x1b[31mX/one", "a\nb/one"):
            code, out, err = self.run_helper("merge", raw, raw.replace("one", "two"), "--wing", "proj")
            self.assertEqual(1, code)
            self.assertNotIn("\x1b", err)
            self.assertEqual(1, err.count("\n"))

    def test_a_merge_whose_marker_is_already_there_says_so(self):
        import itertools
        counter = itertools.count()
        with unittest.mock.patch.object(self.helper, "utc_stamp", lambda: "20261106T12%04dZ" % next(counter)):
            self.draft("source-one", "src")
            self.draft("target-one", "tgt")
            self.assertEqual(0, self.run_helper("merge", "source-one", "target-one")[0])
            self.draft("source-one", "src")
            code, out, err = self.run_helper("merge", "source-one", "target-one")
        self.assertEqual((0, ""), (code, err), err)
        self.assertIn("already", out)

    def test_a_wing_that_differs_only_in_case_is_refused_by_every_verb_that_writes_or_reviews(self):
        self.draft("source-one", "src")
        self.draft("target-one", "tgt")
        for args in (("drop", "source-one", "--wing", "PROJ"), ("merge", "source-one", "target-one", "--wing", "PROJ"), ("review", "--wing", "PROJ"),
                     ("keep", "--wing", "PROJ", "--digest", "0" * 32)):
            code, out, err = self.run_helper(*args)
            if os.path.isdir(os.path.join(self.notes, "PROJ")):   # a volume that tells the cases apart has no alias to refuse
                continue
            self.assertEqual(1, code, args)
            self.assertIn("differs only in case", err, args)


class Guard(Hardening):
    def test_keep_refuses_when_the_drafts_folder_is_not_there_to_write_in(self):
        self.draft("one", "ra")
        digest = self.review()[1]
        real = self.helper.open_wing_folder
        seen = []   # how many times a keep opens the drafts folder; the last open is the one the journal is written through

        def counting(root_fd, state, wing):
            result = real(root_fd, state, wing)
            if state == "draft":
                seen.append(1)
            return result

        with unittest.mock.patch.object(self.helper, "open_wing_folder", counting):
            self.assertEqual(0, self.keep(digest)[0])
        total = len(seen)
        self.draft("two", "rb")
        second = self.review()[1]
        calls = []

        def vanishing(root_fd, state, wing):
            result = real(root_fd, state, wing)
            if state == "draft":
                calls.append(1)
                if len(calls) == total:   # the open that the journal write uses
                    if result is not None:
                        os.close(result)
                    return None
            return result

        elsewhere = os.path.join(self.base, "somewhere-else")
        os.makedirs(elsewhere)
        before = os.getcwd()
        os.chdir(elsewhere)
        self.addCleanup(os.chdir, before)
        with unittest.mock.patch.object(self.helper, "open_wing_folder", vanishing):
            code, out, err = self.keep(second)
        self.assertEqual((1, ""), (code, out))
        self.assertIn("drafts folder", err)
        self.assertEqual([], os.listdir(elsewhere), "nothing was written to the working directory")


if __name__ == "__main__":
    unittest.main()
