"""Plan `2026-11-06-mempalace-notes`, increment C: `drop`, `merge`, `review` and `keep`. The owner reviews one wing's drafts by exception (counts and only the
outliers, with a digest) and `keep` moves exactly the drafts the digest covers into the wing's folder, the one `mine` files. The design is
`docs/specs/mempalace-notes.md`. No test starts a process or reaches a network."""

import os
import re
import unittest
import unittest.mock

import support_notes


class Boom(BaseException):
    """A crash: it is not an `Exception`, so nothing in the helper catches it."""


def prose(tag, words=70):
    """About 500 characters whose words are all made from `tag`, so that two different tags never overlap."""
    return " ".join("%s%03dx" % (tag, number) for number in range(words))


class Review(support_notes.Notes):
    def setUp(self):
        support_notes.Notes.setUp(self)
        self.setting('{"format": 1, "wing": "proj"}')
        self.note("reviewed", "proj", "anchor", title="Anchor", body=prose("anchor") + "\n")   # the wing has a reviewed note, so it is not a new wing

    def draft(self, name, tag=None, **fields):
        fields.setdefault("title", name.replace("-", " ").title())
        fields.setdefault("body", prose(tag or name.replace("-", "")) + "\n")
        return self.note("draft", "proj", name, **fields)

    def text(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def path(self, state, name, wing="proj"):
        return os.path.join(self.folder(state, wing), name + ".txt")

    def review(self, *extra):
        code, out, err = self.run_helper("review", *extra)
        self.assertEqual((0, ""), (code, err), err)
        lines = out.rstrip("\n").split("\n")
        self.assertRegex(lines[-1], r"^digest: [0-9a-f]{32}$", out)
        return "\n".join(lines[:-1]), lines[-1].split()[1]

    def digest(self, *extra):
        return self.review(*extra)[1]

    def keep(self, digest, wing="proj"):
        return self.run_helper("keep", "--wing", wing, "--digest", digest)


class DropAndMerge(Review):
    def stamp(self):
        patch = unittest.mock.patch.object(self.helper, "utc_stamp", return_value="20261106T120000Z")
        patch.start()
        self.addCleanup(patch.stop)

    def test_drop_archives_a_draft_with_the_time_in_its_name_and_changes_nothing_else(self):
        self.stamp()
        self.draft("to-drop")
        reviewed = self.text(self.path("reviewed", "anchor"))
        code, out, err = self.run_helper("drop", "to-drop")
        self.assertEqual((0, ""), (code, err), err)
        self.assertIn("dropped draft proj/to-drop", out)
        self.assertFalse(os.path.exists(self.path("draft", "to-drop")))
        self.assertTrue(os.path.isfile(os.path.join(self.folder("archived", "proj"), "to-drop.20261106T120000Z.txt")))
        self.assertEqual(reviewed, self.text(self.path("reviewed", "anchor")))

    def test_drop_takes_a_title_and_a_wing_prefix_and_refuses_what_is_not_a_draft_or_not_there(self):
        self.stamp()
        self.draft("by-title", title="A Title To Drop")
        self.assertEqual(0, self.run_helper("drop", "A Title To Drop")[0])
        self.draft("by-prefix")
        self.assertEqual(0, self.run_helper("drop", "proj/by-prefix")[0])
        self.note("archived", "proj", "old.20261001T000000Z", title="Old")
        for target in ("anchor", "old", "nothing", "other/x", "../anchor", "proj/extra/anchor", "", "..", "/anchor"):
            self.refused("drop", target)
        self.assertTrue(os.path.isfile(self.path("reviewed", "anchor")))

    def test_a_malformed_draft_can_be_dropped_by_its_file_name_and_then_keep_goes_on(self):
        self.stamp()
        self.draft("good-one", "gd")
        with open(self.path("draft", "broken"), "w") as handle:
            handle.write("not a note at all\n")
        digest = self.digest()
        self.assertEqual(1, self.keep(digest)[0])
        code, out, err = self.run_helper("drop", "broken")
        self.assertEqual((0, ""), (code, err), err)
        self.assertTrue(os.path.isfile(os.path.join(self.folder("archived", "proj"), "broken.20261106T120000Z.txt")))
        self.assertEqual(0, self.keep(self.digest())[0])
        self.assertTrue(os.path.isfile(self.path("reviewed", "good-one")))

    def test_drop_never_replaces_an_archive_entry(self):
        self.stamp()
        self.draft("same")
        os.makedirs(self.folder("archived", "proj"))
        taken = os.path.join(self.folder("archived", "proj"), "same.20261106T120000Z.txt")
        with open(taken, "w") as handle:
            handle.write("already here\n")
        self.refused("drop", "same", contains="archive")
        self.assertEqual("already here\n", self.text(taken))
        self.assertTrue(os.path.isfile(self.path("draft", "same")))

    def test_the_archive_itself_refuses_to_replace_an_entry_that_appeared_after_the_check(self):
        self.stamp()
        self.draft("same")
        os.makedirs(self.folder("archived", "proj"))
        taken = os.path.join(self.folder("archived", "proj"), "same.20261106T120000Z.txt")
        with open(taken, "w") as handle:
            handle.write("appeared late\n")
        with unittest.mock.patch.object(self.helper, "archive_free"):   # the read-only check missed it, as a race would
            code, out, err = self.run_helper("drop", "same")
        self.assertEqual((1, ""), (code, out))
        self.assertIn("archive", err)
        self.assertEqual("appeared late\n", self.text(taken))
        self.assertTrue(os.path.isfile(self.path("draft", "same")))

    def test_merge_adds_the_text_to_a_draft_once_and_archives_the_source(self):
        self.stamp()
        self.draft("source-one", "src")
        self.draft("target-one", "tgt")
        before = self.text(self.path("draft", "target-one"))
        code, out, err = self.run_helper("merge", "source-one", "target-one")
        self.assertEqual((0, ""), (code, err), err)
        after = self.text(self.path("draft", "target-one"))
        self.assertTrue(after.split("\n\n", 1)[1].startswith(before.split("\n\n", 1)[1].rstrip("\n")), after)
        self.assertIn(prose("src"), after)
        self.assertEqual(1, len(re.findall(r"^merged from source-one [0-9a-f]{12}$", after, re.M)))
        self.assertFalse(os.path.exists(self.path("draft", "source-one")))
        self.assertTrue(os.path.isfile(os.path.join(self.folder("archived", "proj"), "source-one.20261106T120000Z.txt")))

    def test_merge_retried_after_a_crash_between_the_write_and_the_archive_adds_nothing_twice(self):
        self.stamp()
        self.draft("source-one", "src")
        self.draft("target-one", "tgt")
        with unittest.mock.patch.object(self.helper, "archive_draft", side_effect=Boom):
            with self.assertRaises(Boom):
                self.run_helper("merge", "source-one", "target-one")
        crashed = self.text(self.path("draft", "target-one"))
        self.assertIn(prose("src"), crashed)
        self.assertTrue(os.path.isfile(self.path("draft", "source-one")), "the text is in both places, not lost")
        self.assertEqual(0, self.run_helper("merge", "source-one", "target-one")[0])
        self.assertEqual(crashed.count(prose("src")), self.text(self.path("draft", "target-one")).count(prose("src")))
        self.assertEqual(1, self.text(self.path("draft", "target-one")).count(prose("src")))
        self.assertFalse(os.path.exists(self.path("draft", "source-one")))

    def test_merge_into_a_reviewed_note_makes_a_revision_draft_and_leaves_the_reviewed_note_alone(self):
        self.stamp()
        self.draft("source-one", "src")
        reviewed = self.text(self.path("reviewed", "anchor"))
        code, out, err = self.run_helper("merge", "source-one", "anchor")
        self.assertEqual((0, ""), (code, err), err)
        self.assertIn("revision draft proj/anchor", out)
        self.assertEqual(reviewed, self.text(self.path("reviewed", "anchor")))
        revision = self.text(self.path("draft", "anchor"))
        self.assertIn("revises: anchor", revision)
        self.assertIn(prose("src"), revision)
        self.assertIn(prose("anchor"), revision)

    def test_merge_with_a_revision_draft_in_place_needs_the_state_to_choose(self):
        self.stamp()
        self.draft("source-one", "src")
        self.draft("source-two", "snd")
        self.assertEqual(0, self.run_helper("merge", "source-one", "anchor")[0])
        self.refused("merge", "source-two", "anchor", contains="more than one")
        self.refused("merge", "source-two", "anchor", "--state", "reviewed", contains="revision draft")
        self.assertEqual(0, self.run_helper("merge", "source-two", "anchor", "--state", "draft")[0])
        self.assertIn(prose("snd"), self.text(self.path("draft", "anchor")))

    def test_merge_refuses_itself_a_non_draft_source_another_wing_and_unsafe_names(self):
        self.draft("source-one", "src")
        self.draft("target-one", "tgt")
        self.note("draft", "other", "elsewhere", title="Elsewhere")
        self.note("archived", "proj", "old.20261001T000000Z", title="Old")
        for args in (("source-one", "source-one"), ("source-one", "proj/source-one"), ("anchor", "target-one"), ("old", "target-one"), ("source-one", "old"),
                     ("source-one", "other/elsewhere"), ("other/elsewhere", "target-one"), ("source-one", "../target-one"), ("source-one", "a/b/c"),
                     ("source-one", ""), ("", "target-one"), ("source-one", "proj/extra/target-one"), ("nothing", "target-one"), ("source-one", "nothing")):
            self.refused("merge", *args)
        self.assertTrue(os.path.isfile(self.path("draft", "source-one")))

    def test_merge_never_looks_in_another_wing_for_a_name_that_exists_there_too(self):
        self.draft("source-one", "src")
        self.draft("target-one", "tgt")
        self.note("draft", "other", "source-one", title="Same slug elsewhere", body=prose("zzz") + "\n")
        self.note("draft", "other", "target-one", title="Same slug elsewhere", body=prose("yyy") + "\n")
        before = self.tree(self.notes)
        self.refused("merge", "source-one", "other/target-one")
        self.refused("merge", "other/source-one", "target-one")
        self.refused("merge", "other/source-one", "proj/target-one")
        self.assertEqual(before, self.tree(self.notes))
        self.assertEqual(0, self.run_helper("merge", "other/source-one", "other/target-one")[0])

    def test_merge_scans_the_result_for_credentials_and_keeps_the_size_limit(self):
        self.draft("source-one", "src", body=prose("src") + "\nGITHUB_" + "TOKEN=abcdef123456\n")
        self.draft("target-one", "tgt")
        before = self.text(self.path("draft", "target-one"))
        self.refused("merge", "source-one", "target-one", contains="credential")
        self.assertEqual(before, self.text(self.path("draft", "target-one")))
        self.draft("big-source", "big", body="y " * 8000)
        self.draft("big-target", "bgt", body="z " * 5000)
        self.refused("merge", "big-source", "big-target", contains="larger than")


class Summary(Review):
    def test_routine_drafts_are_counted_and_not_shown(self):
        for number in range(3):
            self.draft("routine-%d" % number, "rt%d" % number)
        shown, digest = self.review()
        self.assertIn("review of wing proj: 3 drafts, 3 routine, 0 need a look", shown)
        self.assertNotIn("routine-0", shown)

    def test_each_mechanical_flag_makes_an_outlier_with_a_reason_and_a_suggestion(self):
        self.draft("routine", "rt")
        self.draft("large-one", "lg", body=prose("lg", 800) + "\n")
        self.draft("email-one", "em", body=prose("em", 50) + " write to jane.doe@example.com for details\n")
        self.draft("phone-one", "ph", body=prose("ph", 50) + " call 555-123-4567 after noon\n")
        self.draft("address-one", "ad", body=prose("ad", 50) + " the shop is at 123 Main Street today\n")
        self.draft("digits-one", "dg", body=prose("dg", 50) + " the number 123456789012 is long\n")
        self.draft("copy-one", "anchor", body=prose("anchor", 65) + "\n")   # overlaps the reviewed note
        self.draft("old-one", "ol", updated="2026-10-20")
        shown, digest = self.review()
        self.assertIn("8 drafts, 1 routine, 7 need a look", shown)
        self.assertNotIn("routine |", shown)
        for name, reason in (("large-one", "large"), ("email-one", "email-address"), ("phone-one", "phone-number"), ("address-one", "street-address"),
                             ("digits-one", "long-digit-run"), ("copy-one", "overlaps anchor"), ("old-one", "older than 14 days")):
            line = [l for l in shown.splitlines() if "| " + name + " " in l or l.split(" | ")[0].endswith(name)]
            self.assertEqual(1, len(line), (name, shown))
            self.assertIn(reason, line[0], name)
            self.assertIn("suggestion:", line[0], name)

    def test_more_phone_and_address_shapes_are_found_and_a_long_word_costs_little(self):
        import time
        for name, text in (("p1", "call (555)123-4567 later"), ("p2", "call +49 30 1234567 later"), ("a1", "the office is at 12 main street downtown"),
                           ("a2", "the office is at 7 Oak Avenue downtown")):
            self.draft("shape-" + name, name, body=prose(name, 50) + " " + text + "\n")
        shown, _ = self.review()
        for name, kind in (("p1", "phone-number"), ("p2", "phone-number"), ("a1", "street-address"), ("a2", "street-address")):
            self.assertRegex(shown, r"shape-%s .*%s" % (name, kind), name)
        self.draft("slow", "sl", body="a" * 15000 + "\n")
        started = time.monotonic()
        self.review()
        self.assertLess(time.monotonic() - started, 3.0, "a long run without an at sign took too long")

    def test_a_new_wing_a_big_revision_a_draft_that_overlaps_another_draft_and_a_malformed_draft_are_outliers(self):
        self.note("draft", "fresh", "first-note", title="First", body=prose("fr") + "\n")
        shown, _ = self.review("--wing", "fresh")
        self.assertIn("new wing", shown)
        self.draft("revision-one", "rv", body=prose("rv", 80) + "\n", extra=("revises: anchor",))
        self.draft("twin-a", "tw", body=prose("tw", 60) + "\n")
        self.draft("twin-b", "tw", body=prose("tw", 62) + "\n")
        with open(self.path("draft", "broken"), "w") as handle:
            handle.write("title: Broken\nkind: opinion\nwing: proj\nwritten: 2026-11-01\nupdated: 2026-11-02\n\nBody.\n")
        shown, _ = self.review()
        self.assertRegex(shown, r"revision-one .*changes more than half of anchor")
        self.assertRegex(shown, r"twin-a .*overlaps twin-b")
        self.assertRegex(shown, r"twin-b .*overlaps twin-a")
        self.assertRegex(shown, r"broken .*malformed")

    def test_a_small_revision_is_routine_and_a_credential_shaped_draft_is_an_outlier_that_blocks_keep(self):
        body = prose("anchor") + "\n\n(added 2026-11-06) one more sentence\n"
        self.draft("anchor", title="Anchor", body=body, extra=("revises: anchor",), written="2026-11-01")
        shown, _ = self.review()
        self.assertIn("1 routine", shown)
        with open(self.path("draft", "leaky"), "w") as handle:
            handle.write("title: Leaky\nkind: idea\nwing: proj\nwritten: 2026-11-01\nupdated: 2026-11-02\n\n" + prose("lk") + "\nDB_" + "PASSWORD=hunter2hunter\n")
        shown, digest = self.review()
        self.assertRegex(shown, r"leaky .*credential-shaped \(line \d+ assigned-secret\)")
        self.assertNotIn("hunter2", shown)
        code, out, err = self.keep(digest)
        self.assertEqual(1, code)
        self.assertIn("leaky", err)
        self.assertTrue(os.path.isfile(self.path("draft", "leaky")))

    def test_the_output_is_short_plain_lines_between_markers_and_the_digest_is_last(self):
        self.draft("routine", "rt")
        self.draft("email-one", "em", body=prose("em", 50) + " write to jane.doe@example.com\n")
        code, out, err = self.run_helper("review")
        self.assertEqual(0, code, err)
        inner = out.split("\n")
        self.assertRegex(inner[0], r"^<<recalled-data [0-9a-f]{12} begin: mempalace-notes review>>$")
        self.assertRegex(out.rstrip("\n").split("\n")[-1], r"^digest: [0-9a-f]{32}$")
        for line in out.split("\n"):
            self.assertLess(len(line), 300, line)
        self.assertNotIn("jane.doe@example.com", out)   # a personal detail is flagged by its shape and not repeated

    def test_a_long_backlog_never_hides_a_draft_with_a_personal_detail_or_a_blocker(self):
        for number in range(60):
            self.draft("backlog-%02d" % number, "bk%02d" % number, updated="2026-10-20")   # old: every one is an outlier
        self.draft("zz-personal", "zp", body=prose("zp", 50) + " write to jane.doe@example.com\n")
        with open(self.path("draft", "zzz-broken"), "w") as handle:
            handle.write("not a note\n")
        shown, digest = self.review()
        self.assertRegex(shown, r"zz-personal .*personal detail \(email-address\)")
        self.assertRegex(shown, r"zzz-broken .*malformed")
        self.assertRegex(shown, r"\d+ more not shown.*older than 14 days x\d+")
        self.assertLessEqual(len(shown.splitlines()), 50)
        self.assertNotIn("backlog-59", shown)   # the plain old drafts at the end of the list are the ones left out, and counted

    def test_the_digest_is_stable_and_changes_with_a_draft_a_reviewed_target_or_the_set(self):
        self.draft("one", "ra")
        first = self.digest()
        self.assertEqual(first, self.digest())
        with open(self.path("draft", "one"), "a") as handle:
            handle.write("\nan edit\n")
        second = self.digest()
        self.assertNotEqual(first, second)
        self.draft("two", "rb")
        third = self.digest()
        self.assertNotEqual(second, third)
        os.remove(self.path("draft", "two"))
        self.assertEqual(second, self.digest())
        self.draft("rev", "rc", extra=("revises: anchor",))
        with_target = self.digest()
        with open(self.path("reviewed", "anchor"), "a") as handle:
            handle.write("\nthe reviewed note changed\n")
        self.assertNotEqual(with_target, self.digest())

    def test_a_revision_must_have_the_name_of_the_note_it_replaces_and_no_two_may_replace_the_same_note(self):
        self.draft("renamed", "rn", extra=("revises: anchor",))
        shown, digest = self.review()
        self.assertRegex(shown, r"renamed .*is named renamed but revises anchor")
        self.assertEqual(1, self.keep(digest)[0])
        os.remove(self.path("draft", "renamed"))
        self.draft("anchor", "ra1", extra=("revises: anchor",))
        self.draft("anchor-two", "ra2", extra=("revises: anchor",))
        shown, digest = self.review()
        self.assertRegex(shown, r"anchor-two .*is named anchor-two but revises anchor")
        os.remove(self.path("draft", "anchor-two"))
        self.assertEqual(0, self.keep(self.digest())[0])

    def test_a_revision_that_deletes_most_of_a_note_is_an_outlier_too(self):
        self.draft("anchor", title="Anchor", body=prose("anchor", 10) + "\n", extra=("revises: anchor",), written="2026-11-01")
        shown, _ = self.review()
        self.assertRegex(shown, r"anchor .*changes more than half of anchor")

    def test_a_revision_of_a_reviewed_note_that_cannot_be_read_blocks_without_a_traceback(self):
        self.note("reviewed", "proj", "huge", title="Huge", body="y" * 20000)
        self.draft("huge", "hg", extra=("revises: huge",))
        shown, digest = self.review()
        self.assertRegex(shown, r"huge .*which cannot be read")
        code, out, err = self.keep(digest)
        self.assertEqual((1, ""), (code, out))
        self.assertNotIn("Traceback", err)
        self.assertIn("huge", err)

    def test_a_revises_line_that_is_not_a_note_name_makes_the_draft_malformed(self):
        self.draft("odd", "od", extra=("revises: ../../etc/passwd",))
        shown, _ = self.review()
        self.assertRegex(shown, r"odd .*malformed")

    def test_the_digest_belongs_to_one_wing(self):
        self.draft("one", "ra")
        self.note("draft", "other", "two", title="Two", body=prose("rb") + "\n")
        self.assertNotEqual(self.digest(), self.digest("--wing", "other"))

    def test_a_wing_with_no_drafts_says_so(self):
        code, out, err = self.run_helper("review")
        self.assertEqual(0, code, err)
        self.assertIn("no drafts to review", out)

    def test_review_makes_nothing_and_the_wing_defaults_to_the_projects(self):
        self.draft("one", "ra")
        before = self.tree(self.notes)
        self.review()
        self.assertEqual(before, self.tree(self.notes))
        self.refused("review", "extra", contains="usage")


class Keep(Review):
    def test_keep_needs_the_wing_and_a_well_formed_digest(self):
        self.draft("one", "ra")
        for args in ((), ("--wing", "proj"), ("--digest", "a" * 32), ("--wing", "proj", "--digest", "short"), ("--wing", "proj", "--digest", "A" * 32),
                     ("--wing", "proj", "--digest", "a" * 32, "extra")):
            self.refused("keep", *args)

    def test_a_wrong_digest_moves_nothing(self):
        self.draft("one", "ra")
        before = self.tree(self.notes)
        err = self.refused("keep", "--wing", "proj", "--digest", "0" * 32, contains="the digest does not match")
        self.assertIn("nothing was moved", err)
        self.assertEqual(before, self.tree(self.notes))

    def test_keep_moves_every_draft_of_the_wing_into_its_folder_and_only_that_wing(self):
        self.draft("one", "ra")
        self.draft("two", "rb")
        self.note("draft", "other", "elsewhere", title="Elsewhere", body=prose("rc") + "\n")
        digest = self.digest()
        code, out, err = self.keep(digest)
        self.assertEqual((0, ""), (code, err), err)
        self.assertIn("kept 2 notes in wing proj", out)
        self.assertIn(os.path.join(self.notes, "proj"), out)
        for name in ("one", "two"):
            self.assertTrue(os.path.isfile(self.path("reviewed", name)))
            self.assertFalse(os.path.exists(self.path("draft", name)))
        self.assertTrue(os.path.isfile(self.path("draft", "elsewhere", "other")))
        self.assertEqual(["anchor.txt", "one.txt", "two.txt"], sorted(os.listdir(self.folder("reviewed", "proj"))))
        self.assertFalse(os.path.exists(os.path.join(self.folder("draft", "proj"), ".keep")))

    def test_a_digest_of_one_wing_is_refused_for_another(self):
        self.draft("one", "ra")
        self.note("draft", "other", "two", title="Two", body=prose("rb") + "\n")
        digest = self.digest()
        self.refused("keep", "--wing", "other", "--digest", digest, contains="the digest does not match")
        self.assertTrue(os.path.isfile(self.path("draft", "two", "other")))

    def test_a_draft_changed_added_or_dropped_after_the_review_refuses_the_old_digest(self):
        self.draft("one", "ra")
        digest = self.digest()
        self.draft("late", "rb")
        self.refused("keep", "--wing", "proj", "--digest", digest, contains="the digest does not match")
        os.remove(self.path("draft", "late"))
        with open(self.path("draft", "one"), "a") as handle:
            handle.write("\nedited after the review\n")
        self.refused("keep", "--wing", "proj", "--digest", digest, contains="the digest does not match")
        self.assertTrue(os.path.isfile(self.path("draft", "one")))

    def test_a_revision_replaces_the_reviewed_note_it_names_and_loses_the_revision_headers(self):
        self.draft("anchor", title="Anchor", body=prose("anchor") + "\n\n(added 2026-11-06) more\n", extra=("revises: anchor", "new-despite: x"), written="2026-11-01")
        digest = self.digest()
        code, out, err = self.keep(digest)
        self.assertEqual((0, ""), (code, err), err)
        kept = self.text(self.path("reviewed", "anchor"))
        self.assertIn("(added 2026-11-06) more", kept)
        self.assertNotIn("revises:", kept)
        self.assertNotIn("new-despite:", kept)
        self.assertFalse(os.path.exists(self.path("draft", "anchor")))
        code, out, err = self.run_helper("list", "--state", "reviewed")
        self.assertEqual(0, code, err)

    def test_nothing_is_kept_when_there_are_no_drafts_or_one_cannot_be_kept(self):
        self.refused("keep", "--wing", "proj", "--digest", "0" * 32, contains="no drafts")
        os.makedirs(self.folder("draft", "proj"), exist_ok=True)
        with open(self.path("draft", "bad"), "w") as handle:
            handle.write("not a note at all\n")
        digest = self.digest()
        err = self.refused("keep", "--wing", "proj", "--digest", digest, contains="bad")
        self.assertIn("malformed", err)

    def test_an_existing_reviewed_note_of_the_name_is_never_replaced_by_a_new_draft(self):
        self.draft("anchor", "zz")   # a draft named like the reviewed note, but not a revision of it
        digest = self.digest()
        before = self.text(self.path("reviewed", "anchor"))
        self.refused("keep", "--wing", "proj", "--digest", digest, contains="anchor")
        self.assertEqual(before, self.text(self.path("reviewed", "anchor")))

    def test_a_wing_with_more_drafts_than_keep_moves_at_a_time_is_refused(self):
        for number in range(self.helper.MAX_KEEP + 1):
            self.draft("many-%03d" % number, "mn%03d" % number)
        digest = self.digest()
        self.refused("keep", "--wing", "proj", "--digest", digest, contains="at most")

    def test_the_digest_is_checked_again_under_the_lock(self):
        self.draft("one", "ra")
        digest = self.digest()
        real = self.helper.drafts_and_reviewed
        calls = []

        def edited_in_between(root_fd, wing):
            calls.append(1)
            if len(calls) == 2:   # the second read is the one under the lock: someone edited a draft after the first
                with open(self.path("draft", "one"), "a") as handle:
                    handle.write("\nedited between the check and the lock\n")
            return real(root_fd, wing)

        with unittest.mock.patch.object(self.helper, "drafts_and_reviewed", edited_in_between):
            code, out, err = self.keep(digest)
        self.assertEqual((1, ""), (code, out))
        self.assertIn("the digest does not match", err)
        self.assertTrue(os.path.isfile(self.path("draft", "one")))
        self.assertFalse(os.path.exists(self.path("reviewed", "one")))

    def test_a_held_lock_is_waited_for_a_little_and_then_refused(self):
        import fcntl
        self.draft("one", "ra")
        digest = self.digest()
        os.makedirs(os.path.join(self.notes, ".locks"), exist_ok=True)
        descriptor = os.open(os.path.join(self.notes, ".locks", "proj"), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        self.addCleanup(os.close, descriptor)
        with unittest.mock.patch.object(self.helper, "LOCK_TRIES", 2), unittest.mock.patch.object(self.helper, "LOCK_PAUSE", 0.01):
            self.refused("keep", "--wing", "proj", "--digest", digest, contains="another")
        self.assertTrue(os.path.isfile(self.path("draft", "one")))


class MoveOne(Review):
    """The step `keep` repeats: it must never write over a different reviewed note or lose a draft."""

    def fingerprint(self, name):
        with open(self.path("draft", name), "rb") as handle:
            return self.helper.note_hash(handle.read())

    def folders(self):
        import os as _os
        drafts = _os.open(self.folder("draft", "proj"), _os.O_RDONLY | _os.O_DIRECTORY)
        reviewed = _os.open(self.folder("reviewed", "proj"), _os.O_RDONLY | _os.O_DIRECTORY)
        self.addCleanup(_os.close, drafts)
        self.addCleanup(_os.close, reviewed)
        return drafts, reviewed

    def test_a_new_draft_is_not_moved_over_a_different_reviewed_note_of_the_same_name(self):
        self.draft("clash", "cl")
        self.note("reviewed", "proj", "clash", title="Clash", body=prose("other") + "\n")
        drafts, reviewed = self.folders()
        before = self.text(self.path("reviewed", "clash"))
        with self.assertRaises(self.helper.Refused):
            self.helper.move_one(drafts, reviewed, "proj", "new", "clash.txt", "clash.txt", self.fingerprint("clash"))
        self.assertEqual(before, self.text(self.path("reviewed", "clash")))
        self.assertTrue(os.path.isfile(self.path("draft", "clash")), "the draft is not lost")

    def test_a_draft_that_is_already_in_the_reviewed_folder_is_simply_removed(self):
        self.draft("same", "sm")
        drafts, reviewed = self.folders()
        with open(self.path("draft", "same"), "rb") as handle:
            data = handle.read()
        os.makedirs(self.folder("reviewed", "proj"), exist_ok=True)
        with open(self.path("reviewed", "same"), "wb") as handle:
            handle.write(self.helper.final_bytes(data, "proj"))
        self.helper.move_one(drafts, reviewed, "proj", "new", "same.txt", "same.txt", self.fingerprint("same"))
        self.assertFalse(os.path.exists(self.path("draft", "same")))

    def test_a_draft_that_is_gone_is_a_move_that_was_done(self):
        os.makedirs(self.folder("draft", "proj"))
        drafts, reviewed = self.folders()
        self.helper.move_one(drafts, reviewed, "proj", "new", "gone.txt", "gone.txt", "0" * 32)


class Interrupted(Review):
    """`keep` journals the set, moves the drafts one at a time, and removes the journal; a crash at any step is finished by a retry."""

    def setUp(self):
        Review.setUp(self)
        self.draft("one", "ra")
        self.draft("two", "rb")
        self.draft("anchor", title="Anchor", body=prose("anchor") + "\n\n(added 2026-11-06) more\n", extra=("revises: anchor",), written="2026-11-01")
        self.digest_before = self.digest()
        self.texts = {name: self.text(self.path("draft", name)) for name in ("one", "two")}

    def journal(self):
        return os.path.join(self.folder("draft", "proj"), ".keep")

    def finished(self):
        self.assertEqual(["anchor.txt", "one.txt", "two.txt"], sorted(os.listdir(self.folder("reviewed", "proj"))))
        self.assertEqual([], [n for n in os.listdir(self.folder("draft", "proj")) if n.endswith(".txt") or n == ".keep"])
        self.assertIn("(added 2026-11-06) more", self.text(self.path("reviewed", "anchor")))
        for name, text in self.texts.items():
            self.assertEqual(text, self.text(self.path("reviewed", name)))

    def test_a_crash_before_each_move_is_finished_by_a_retry_with_the_same_digest(self):
        real = self.helper.move_one
        for crash_at in (1, 2, 3):
            self.setUp() if crash_at > 1 else None
            calls = []

            def crashing(*args, **kwargs):
                calls.append(1)
                if len(calls) == crash_at:
                    raise Boom
                return real(*args, **kwargs)

            with unittest.mock.patch.object(self.helper, "move_one", crashing):
                with self.assertRaises(Boom):
                    self.keep(self.digest_before)
            self.assertTrue(os.path.isfile(self.journal()), "the journal stays after a crash")
            code, out, err = self.keep(self.digest_before)
            self.assertEqual((0, ""), (code, err), (crash_at, err))
            self.finished()

    def test_a_crash_after_the_write_and_before_the_removal_of_the_draft_is_finished_by_a_retry(self):
        real_unlink = os.unlink
        done = []

        def failing(path, *args, **kwargs):
            if not done and str(path).endswith(".txt"):
                done.append(1)
                raise Boom
            return real_unlink(path, *args, **kwargs)

        with unittest.mock.patch("os.unlink", failing):
            with self.assertRaises(Boom):
                self.keep(self.digest_before)
        code, out, err = self.keep(self.digest_before)
        self.assertEqual((0, ""), (code, err), err)
        self.finished()

    def test_a_different_digest_while_a_journal_exists_finishes_the_old_keep_and_is_then_refused(self):
        real = self.helper.move_one
        calls = []

        def crashing(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                raise Boom
            return real(*args, **kwargs)

        with unittest.mock.patch.object(self.helper, "move_one", crashing):
            with self.assertRaises(Boom):
                self.keep(self.digest_before)
        err = self.refused_keep("f" * 32)
        self.assertIn("interrupted", err)
        self.assertFalse(os.path.exists(self.journal()))
        self.finished()

    def refused_keep(self, digest):
        code, out, err = self.keep(digest)
        self.assertEqual((1, ""), (code, out), err)
        return err

    def test_list_review_and_save_finish_an_interrupted_keep(self):
        for verb in ("list", "review", "save"):
            if verb != "list":
                self.setUp()
            real = self.helper.move_one
            calls = []

            def crashing(*args, **kwargs):
                calls.append(1)
                if len(calls) == 2:
                    raise Boom
                return real(*args, **kwargs)

            with unittest.mock.patch.object(self.helper, "move_one", crashing):
                with self.assertRaises(Boom):
                    self.keep(self.digest_before)
            self.assertTrue(os.path.isfile(self.journal()))
            args = {"list": ("list",), "review": ("review",), "save": ("save", "--title", "Fresh note", "--kind", "idea", "--body", prose("fresh"))}[verb]
            self.assertEqual(0, self.run_helper(*args)[0], verb)
            self.assertFalse(os.path.exists(self.journal()), verb)
            self.assertEqual(["anchor.txt", "one.txt", "two.txt"], sorted(os.listdir(self.folder("reviewed", "proj"))), verb)


class Journal(Review):
    def setUp(self):
        Review.setUp(self)
        self.draft("one", "ra")
        self.digest_before = self.digest()
        self.journal = os.path.join(self.folder("draft", "proj"), ".keep")

    def damaged(self, content=None, make=None):
        if make:
            make(self.journal)
        else:
            with open(self.journal, "w") as handle:
                handle.write(content)
        for args in (("keep", "--wing", "proj", "--digest", self.digest_before), ("save", "--title", "T", "--kind", "idea", "--body", prose("zz")),
                     ("drop", "one"), ("merge", "one", "anchor")):
            code, out, err = self.run_helper(*args)
            self.assertEqual(1, code, args)
            self.assertNotIn("Traceback", err, args)
            self.assertIn("journal", err, args)
        self.assertEqual(0, self.run_helper("list")[0])   # a read verb goes on
        self.assertEqual(0, self.run_helper("review")[0])
        self.assertTrue(os.path.isfile(self.path("draft", "one")), "nothing was moved")
        self.assertFalse(os.path.exists(self.path("reviewed", "one")))

    def test_a_journal_that_is_garbage_or_names_something_else_is_refused_and_moves_nothing(self):
        self.damaged("garbage\n")
        os.remove(self.journal)
        self.damaged("keep 1\ndigest " + "a" * 32 + "\nnew ../escape.txt\n")
        os.remove(self.journal)
        self.damaged("keep 1\ndigest " + "a" * 32 + "\nnew /etc/passwd\n")
        os.remove(self.journal)
        self.damaged("keep 1\ndigest " + "a" * 32 + "\nrevise one.txt\n")   # a revision needs its target
        os.remove(self.journal)
        self.damaged("keep 1\ndigest " + "a" * 32 + "\nnew one.txt other.txt\n")   # a new note has no target

    def test_a_journal_that_is_a_link_or_a_folder_is_refused_and_not_followed(self):
        outside = os.path.join(self.base, "outside-journal")
        with open(outside, "w") as handle:
            handle.write("keep 1\ndigest " + "a" * 32 + "\nnew one.txt\n")
        self.damaged(make=lambda path: os.symlink(outside, path))
        os.remove(self.journal)
        self.damaged(make=lambda path: os.mkdir(path))

    def test_a_crash_after_the_last_move_and_before_the_journal_is_removed_is_finished_by_a_retry(self):
        real_unlink = os.unlink
        done = []

        def failing(path, *args, **kwargs):
            if str(path) == ".keep" and not done:
                done.append(1)
                raise Boom
            return real_unlink(path, *args, **kwargs)

        with unittest.mock.patch("os.unlink", failing):
            with self.assertRaises(Boom):
                self.keep(self.digest_before)
        self.assertTrue(os.path.isfile(self.journal))
        self.assertTrue(os.path.isfile(self.path("reviewed", "one")))
        code, out, err = self.keep(self.digest_before)
        self.assertEqual((0, ""), (code, err), err)
        self.assertIn("finished the interrupted keep", out)
        self.assertFalse(os.path.exists(self.journal))

    def test_a_journal_for_a_large_wing_can_be_read_back(self):
        names = ["many-%03d" % number for number in range(self.helper.MAX_KEEP)]
        with open(self.journal, "w") as handle:
            handle.write("keep 1\ndigest " + "a" * 32 + "\n" + "".join("new %s.txt %s\n" % (name, "b" * 32) for name in names))
        self.assertGreater(os.path.getsize(self.journal), 0)
        read = self.helper.read_journal
        import os as _os
        fd = _os.open(self.folder("draft", "proj"), _os.O_RDONLY | _os.O_DIRECTORY)
        self.addCleanup(_os.close, fd)
        digest, entries = read(fd)
        self.assertEqual(self.helper.MAX_KEEP, len(entries))


class Mined(Review):
    def test_what_mine_would_file_is_only_the_reviewed_notes(self):
        self.draft("one", "ra")
        self.digest()
        self.assertEqual(["anchor.txt"], os.listdir(self.folder("reviewed", "proj")))
        self.keep(self.digest())
        files = []
        for base, dirs, names in os.walk(self.folder("reviewed", "proj")):
            files += names
        self.assertEqual(["anchor.txt", "one.txt"], sorted(files))


if __name__ == "__main__":
    unittest.main()
