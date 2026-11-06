"""Plan `2026-11-06-mempalace-notes`, increment B: `save`, which makes a draft, extends a note, or makes a revision draft of a reviewed note; the notes folder and
its permissions; the file-name rule; the minimum size; the credential scan; the overlap check; the lock; the atomic write; and the lazy expiry of old drafts.
The design is `docs/specs/mempalace-notes.md`. No test starts a process or reaches a network."""

import datetime
import fcntl
import os
import stat
import threading
import unittest
import unittest.mock

import support_notes


def prose(tag, words=70):
    """About 500 characters of text whose words are all made from `tag`, so that two different tags never overlap."""
    return " ".join("%s%03dx" % (tag, number) for number in range(words))


def fake(*parts):
    """A credential-shaped string built from pieces, so that this file holds no token shape."""
    return "".join(parts)


class Save(support_notes.Notes):
    def setUp(self):
        support_notes.Notes.setUp(self)
        self.setting('{"format": 1, "wing": "proj"}')

    def save(self, title="First idea", body=None, kind="idea", *extra, stdin=b""):
        args = ["save", "--title", title, "--kind", kind, "--body", prose("alpha") if body is None else body] + list(extra)
        return self.run_helper(*args, stdin=stdin)

    def saved(self, title="First idea", body=None, kind="idea", *extra):
        code, out, err = self.save(title, body, kind, *extra)
        self.assertEqual(0, code, err)
        return out

    def draft_path(self, name, wing="proj"):
        return os.path.join(self.folder("draft", wing), name + ".txt")

    def text(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()


class Basics(Save):
    def test_a_save_makes_a_draft_in_the_exact_format_and_says_what_it_made(self):
        body = prose("alpha")
        out = self.saved("First idea", body, "idea", "--source", "a talk", "--verify", "echo ok")
        self.assertIn("saved draft proj/first-idea", out)
        self.assertEqual("title: First idea\nkind: idea\nwing: proj\nwritten: 2026-11-06\nupdated: 2026-11-06\nsource: a talk\nverify: echo ok\n\n" + body + "\n",
                         self.text(self.draft_path("first-idea")))

    def test_the_saved_draft_is_listed_and_read_back(self):
        self.saved("First idea")
        code, out, err = self.run_helper("list", "--state", "draft")
        self.assertEqual((0, ""), (code, err), err)
        self.assertRegex(self.body(out, "list"), r"draft\s+proj/first-idea \| idea \| updated 2026-11-06 \(today\) \| First idea")
        code, out, err = self.run_helper("read", "first-idea")
        self.assertEqual((0, ""), (code, err), err)
        self.assertIn("title: First idea", self.body(out, "read"))

    def test_the_folders_are_made_one_level_at_a_time_private_and_the_file_is_private(self):
        self.saved()
        for path in (os.path.join(self.data, "project-workbench"), self.notes, os.path.join(self.notes, ".drafts"), os.path.join(self.notes, ".drafts", "proj"),
                     os.path.join(self.notes, ".locks")):
            self.assertEqual(0o700, stat.S_IMODE(os.stat(path).st_mode), path)
        self.assertEqual(0o600, stat.S_IMODE(os.stat(self.draft_path("first-idea")).st_mode))
        self.assertFalse(os.path.exists(os.path.join(self.notes, "proj")), "the reviewed folder is not made by a save")

    def test_a_missing_data_directory_is_not_made(self):
        os.rmdir(self.data)
        err = self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), contains="does not exist")
        self.assertNotIn("Traceback", err)

    def test_a_link_in_the_notes_path_below_the_data_directory_is_not_followed(self):
        real = os.path.join(self.base, "real")
        os.makedirs(real)
        os.makedirs(os.path.join(self.data, "project-workbench"))
        os.symlink(real, self.notes)
        self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), contains="link")
        self.assertEqual([], os.listdir(real))

    def test_a_link_at_the_drafts_folder_or_the_wing_folder_is_not_followed(self):
        real = os.path.join(self.base, "real")
        os.makedirs(real)
        os.makedirs(self.notes)
        os.symlink(real, os.path.join(self.notes, ".drafts"))
        self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), contains="link")
        os.remove(os.path.join(self.notes, ".drafts"))
        os.makedirs(os.path.join(self.notes, ".drafts"))
        os.symlink(real, os.path.join(self.notes, ".drafts", "proj"))
        self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), contains="link")
        self.assertEqual([], os.listdir(real))

    def test_a_link_above_the_notes_folder_is_followed_as_a_dotfile_manager_makes_one(self):
        elsewhere = os.path.join(self.base, "dotfiles-share")
        os.rmdir(self.data)
        os.makedirs(elsewhere)
        os.symlink(elsewhere, self.data)
        self.saved()
        self.assertTrue(os.path.isfile(os.path.join(elsewhere, "project-workbench", "mempalace", ".drafts", "proj", "first-idea.txt")))

    def test_a_topic_wing_is_made_by_naming_it_and_a_plain_search_wing_is_named_when_it_differs(self):
        out = self.saved("Tool notes", prose("beta"), "lesson", "--wing", "verilog")
        self.assertIn("saved draft verilog/tool-notes", out)
        self.assertIn("a plain search in this clone looks in wing proj", out)
        self.assertIn("--wing verilog", out)
        self.assertNotIn("a plain search", self.saved("Project note", prose("gamma")))

    def test_the_project_wing_comes_from_the_remote_when_there_is_no_file_and_blocks_when_there_is_neither(self):
        os.remove(os.path.join(self.root, ".workbench", "local", "mempalace.json"))
        self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), contains="mempalace.json")
        self.origin("git@github.com:owner/from-remote.git")
        self.assertIn("saved draft from-remote/first-idea", self.saved())

    def test_a_wing_name_that_could_reach_another_place_is_refused(self):
        for name in ("../x", ".x", "-x", "a/b", "x" * 65):
            self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), "--wing", name, contains="--wing")

    def test_options_are_checked(self):
        full = ["--title", "T", "--kind", "idea", "--body", prose("alpha")]
        self.refused("save", *full[2:], contains="--title")                       # no title
        self.refused("save", "--title", "T", "--body", prose("alpha"), contains="--kind")
        self.refused("save", "--title", "T", "--kind", "opinion", "--body", prose("alpha"), contains="--kind")
        self.refused("save", *full, "--kind", "idea", contains="twice")
        self.refused("save", *full, "--surprise", "x", contains="usage")
        self.refused("save", "--title", "--kind", "--kind", "idea", "--body", prose("alpha"), contains="looks like an option")
        self.refused("save", "--title", "T", "--kind", "idea", contains="--body")
        self.refused("save", *full, "positional", contains="usage")

    def test_source_and_verify_are_refused_with_into_and_not_dropped(self):
        self.saved("Base note", prose("alpha"))
        for option in ("--source", "--verify"):
            self.refused("save", "--title", "x", "--kind", "idea", "--body", "more", "--into", "base-note", option, "a line", contains=option)

    def test_a_wing_that_differs_only_in_case_from_an_existing_wing_is_refused(self):
        self.note("reviewed", "foo", "n1", title="In foo")
        self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), "--wing", "Foo", contains="differs only in case")
        self.assertEqual(0, self.save("T", prose("alpha"), "idea", "--wing", "foo")[0])

    def test_the_body_can_come_from_standard_input(self):
        body = prose("alpha")
        code, out, err = self.run_helper("save", "--title", "From input", "--kind", "idea", "--body", "-", stdin=body.encode())
        self.assertEqual(0, code, err)
        self.assertIn(body, self.text(self.draft_path("from-input")))

    def test_the_body_must_be_text_and_within_the_size_limit(self):
        code, out, err = self.run_helper("save", "--title", "T", "--kind", "idea", "--body", "-", stdin=b"\xff\xfe" * 200)
        self.assertEqual((1, ""), (code, out))
        self.assertIn("UTF-8", err)
        self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha") * 40, contains="larger than")

    def test_a_save_over_the_minimum_size_only(self):
        self.refused("save", "--title", "T", "--kind", "idea", "--body", "x" * 299, contains="at least 300")
        self.assertEqual(0, self.save("Exact", "y" * 300)[0])


class Names(Save):
    def test_the_file_name_is_made_from_the_title_by_the_fixed_rule(self):
        cases = [("First Idea", "first-idea"), ("Café notes", "caf-notes"), ("a--b", "a--b"), ("-Lead and trail-", "lead-and-trail"),
                 ("X" * 100, "x" * 60), ("Mixed_Case.and.dots", "mixed-case-and-dots"), ("100% sure", "100-sure"), ("Spaces   and    runs", "spaces-and-runs")]
        for number, (title, name) in enumerate(cases):
            code, out, err = self.save(title, prose("t%d" % number))
            self.assertEqual(0, code, (title, err))
            self.assertTrue(os.path.isfile(self.draft_path(name)), (title, os.listdir(self.folder("draft", "proj"))))

    def test_a_title_that_leaves_nothing_or_holds_a_separator_or_a_control_character_is_refused(self):
        for title in ("", "   ", "!!!", "éè", "a/b", "a\\b", "bad\x00title", "bad\ntitle", "bad\x1btitle", "x" * 121, "..", "../x"):
            self.refused("save", "--title", title, "--kind", "idea", "--body", prose("alpha"), contains="title")

    def test_a_name_that_is_taken_is_refused_with_and_without_new_and_nothing_is_overwritten(self):
        self.saved("Same Name", prose("alpha"))
        before = self.text(self.draft_path("same-name"))
        for extra in ((), ("--new",)):
            self.refused("save", "--title", "same name!", "--kind", "idea", "--body", prose("beta"), *extra, contains="already")
        self.note("reviewed", "proj", "in-reviewed", title="In reviewed")
        self.refused("save", "--title", "In Reviewed", "--kind", "idea", "--body", prose("gamma"), contains="already")
        self.note("archived", "proj", "in-archive.20261001T000000Z", title="In archive")
        self.refused("save", "--title", "In Archive", "--kind", "idea", "--body", prose("delta"), contains="already")
        self.assertEqual(before, self.text(self.draft_path("same-name")))

    def test_two_titles_that_make_the_same_name_do_not_overwrite_each_other(self):
        self.saved("Some Idea", prose("alpha"))
        self.refused("save", "--title", "some-idea", "--kind", "idea", "--body", prose("beta"), contains="already")
        self.assertIn(prose("alpha"), self.text(self.draft_path("some-idea")))

    def test_a_new_note_is_made_with_an_exclusive_create_even_if_the_name_appears_after_the_check(self):
        real_link = os.link

        def late(src, dst, *args, **kwargs):
            with open(os.path.join(self.folder("draft", "proj"), "raced.txt"), "w") as handle:
                handle.write("someone else's note\n")
            return real_link(src, dst, *args, **kwargs)

        with unittest.mock.patch("os.link", late):
            code, out, err = self.save("Raced", prose("alpha"))
        self.assertEqual(1, code)
        self.assertEqual("someone else's note\n", self.text(self.draft_path("raced")))
        self.assertEqual([], [n for n in os.listdir(self.folder("draft", "proj")) if n.startswith(".tmp")])


class Credentials(Save):
    CASES = {
        "private-key-block": "-----BEGIN RSA " + "PRIVATE KEY-----",
        "aws-access-key-id": fake("AK", "IA", "A" * 16),
        "github-token": fake("gh", "p_", "a" * 36),
        "github-fine-grained-token": fake("github", "_pat_", "a" * 30),
        "slack-token": fake("xo", "xb-", "1" * 12),
        "google-api-key": fake("AI", "za", "a" * 35),
        "json-web-token": fake("ey", "J", "a" * 10, ".ey", "J", "b" * 10, ".", "c" * 8),
        "sk-key": fake("s", "k-", "a" * 24),
        "bearer-header": "Authorization: Bearer " + "a" * 20,
        "url-with-password": "https://user:" + "pw" + "@example.com/path",
        "assigned-secret": "pass" + "word: hunter22",
    }

    def test_each_pattern_is_refused_with_its_line_number_and_name_and_never_the_text(self):
        for name, secret in self.CASES.items():
            body = prose("alpha", 40) + "\nsecond line\n" + secret + "\n"
            code, out, err = self.save("Pattern " + name, body)
            self.assertEqual((1, ""), (code, out), name)
            self.assertIn(name, err)
            self.assertRegex(err, r"line \d+")
            self.assertNotIn(secret, err)
            self.assertNotIn(secret[:12], err)
        self.assertFalse(os.path.exists(self.folder("draft", "proj")) and os.listdir(self.folder("draft", "proj")))

    def test_assignments_with_a_prefix_a_suffix_an_underscore_or_a_quote_are_refused(self):
        shapes = {"env-style": "GITHUB_" + "TOKEN=abc123xyz789", "client": "client_" + "secret = s3cr3tvalue", "db": "DB_" + "PASSWORD=hunter2hunter",
                  "django": "SECRET_" + "KEY=abcdef123456", "json": '"pass' + 'word": "hunter2xx"', "json-token": '"api_' + 'key": "abcdef123456"',
                  "access-key": "aws_access_" + "key = abcdef123456"}
        for label, line in shapes.items():
            code, out, err = self.save("Shape " + label, prose("alpha", 40) + "\n" + line)
            self.assertEqual((1, ""), (code, out), label)
            self.assertIn("assigned-secret", err, label)
            self.assertNotIn(line, err, label)

    def test_a_token_wrapped_over_two_lines_is_found_by_the_joined_pass_and_named_at_its_first_line(self):
        key = fake("AK", "IA", "B" * 16)
        code, out, err = self.save("Wrapped", prose("alpha", 40) + "\n" + key[:9] + "\n" + key[9:] + "\n")
        self.assertEqual((1, ""), (code, out))
        self.assertIn("aws-access-key-id", err)
        self.assertRegex(err, r"line 8\b")
        self.assertNotIn(key[:9], err)

    def test_ordinary_text_that_mentions_these_words_is_saved(self):
        text = prose("alpha", 40) + "\nthe token limit: 100000 tokens per request\nask for the secret: ask\nrotate the password: soon\nan api key is needed for this\n"
        self.assertEqual(0, self.save("Benign", text)[0])

    def test_the_line_number_is_the_line_of_the_whole_note_not_of_the_body(self):
        code, out, err = self.save("Lines", prose("alpha", 40) + "\n" + self.CASES["aws-access-key-id"])
        self.assertEqual(1, code)
        self.assertRegex(err, r"line 8\b")   # five header lines, a blank line, the first body line (7), and then the line with the key (8)

    def test_a_credential_in_any_field_is_refused(self):
        secret = self.CASES["github-token"]
        for option, value in (("--title", "Token " + secret), ("--source", secret), ("--verify", "curl -H " + secret)):
            args = ["save", "--title", "Fields", "--kind", "idea", "--body", prose("alpha")]
            if option == "--title":
                args[2] = "Token " + secret
            else:
                args += [option, value]
            code, out, err = self.run_helper(*args)
            self.assertEqual((1, ""), (code, out), option)
            self.assertIn("github-token", err)
            self.assertNotIn(secret, err)

    def test_a_credential_in_the_paragraph_added_with_into_is_refused_and_the_note_is_unchanged(self):
        self.saved("Base note", prose("alpha"))
        before = self.text(self.draft_path("base-note"))
        code, out, err = self.save("ignored", "an addition " + self.CASES["slack-token"], "idea", "--into", "base-note")
        self.assertEqual((1, ""), (code, out))
        self.assertIn("slack-token", err)
        self.assertEqual(before, self.text(self.draft_path("base-note")))

    def test_an_existing_credential_in_a_note_is_found_when_the_note_is_extended(self):
        self.note("draft", "proj", "old-note", title="Old note", body=prose("alpha") + "\n" + self.CASES["sk-key"] + "\n")
        code, out, err = self.save("ignored", "a harmless addition " + prose("beta", 30), "idea", "--into", "old-note")
        self.assertEqual((1, ""), (code, out))
        self.assertIn("sk-key", err)

    def test_a_credential_in_the_title_is_refused_before_the_name_is_checked_or_echoed(self):
        secret = self.CASES["github-token"]
        title = "taken " + secret
        stem = self.helper.slug(title)
        self.note("draft", "proj", stem, title="A note whose name the credential title would make")
        code, out, err = self.save(title, prose("beta"))
        self.assertEqual((1, ""), (code, out))
        self.assertIn("github-token", err)
        self.assertNotIn("already", err)
        self.assertNotIn(stem[:20], err)

    def test_the_same_note_reworded_is_saved_and_ordinary_talk_of_passwords_is_not_refused(self):
        self.refused("save", "--title", "Reworded", "--kind", "idea", "--body", prose("alpha", 40) + " " + self.CASES["assigned-secret"], contains="assigned-secret")
        self.assertEqual(0, self.save("Reworded", prose("alpha", 40) + " the password is kept in the owner's manager, not recorded here")[0])


class Overlap(Save):
    def test_text_that_overlaps_a_note_is_refused_and_lists_it(self):
        self.saved("Original", prose("alpha"))
        self.note("reviewed", "proj", "reviewed-one", title="Reviewed one", body=prose("alpha", 60) + "\n")
        err = self.refused("save", "--title", "Copy", "--kind", "idea", "--body", prose("alpha", 65), contains="overlaps")
        self.assertIn("proj/original", err)
        self.assertIn("proj/reviewed-one", err)
        self.assertIn("--into", err)
        self.assertIn("--new", err)

    def test_a_different_text_does_not_overlap_and_the_archive_is_not_compared(self):
        self.note("archived", "proj", "old.20261001T000000Z", title="Old", body=prose("alpha") + "\n")
        self.saved("Fresh", prose("alpha"))   # only an archived note has these words
        self.assertEqual(0, self.save("Unrelated", prose("beta"))[0])

    def test_new_creates_the_note_anyway_and_records_the_choice(self):
        self.saved("Original", prose("alpha"))
        out = self.saved("Deliberate copy", prose("alpha", 65), "idea", "--new")
        self.assertIn("proj/deliberate-copy", out)
        self.assertIn("new-despite: original", self.text(self.draft_path("deliberate-copy")))

    def test_new_without_an_overlap_records_nothing(self):
        self.saved("Plain", prose("alpha"), "idea", "--new")
        self.assertNotIn("new-despite", self.text(self.draft_path("plain")))


class Into(Save):
    def test_an_addition_to_a_draft_is_a_dated_paragraph_and_changes_no_earlier_text(self):
        self.saved("Base note", prose("alpha"))
        path = self.draft_path("base-note")
        before = self.text(path)
        with unittest.mock.patch.object(self.helper, "today", return_value=datetime.date(2026, 11, 20)):
            out = self.saved("ignored title", prose("beta", 30), "idea", "--into", "base-note")
        self.assertIn("extended draft proj/base-note", out)
        after = self.text(path)
        self.assertTrue(after.startswith(before.replace("updated: 2026-11-06", "updated: 2026-11-20")[:-1]), after)
        self.assertIn("written: 2026-11-06", after)
        self.assertIn("updated: 2026-11-20", after)
        self.assertIn("(added 2026-11-20) " + prose("beta", 30), after)
        self.assertEqual(["base-note.txt"], os.listdir(self.folder("draft", "proj")))

    def test_into_takes_a_title_a_wing_prefix_and_needs_no_minimum_size(self):
        self.saved("Base note", prose("alpha"))
        self.assertEqual(0, self.save("x", "short", "idea", "--into", "Base Note")[0])
        self.assertEqual(0, self.save("x", "shorter", "idea", "--into", "proj/base-note")[0])
        self.assertIn("(added 2026-11-06) shorter", self.text(self.draft_path("base-note")))

    def test_into_a_reviewed_note_makes_a_revision_draft_and_leaves_the_reviewed_note_alone(self):
        path = self.note("reviewed", "proj", "design-notes", title="Design notes", written="2026-10-01", updated="2026-10-02", body=prose("alpha") + "\n")
        before = self.text(path)
        out = self.saved("x", prose("beta", 30), "idea", "--into", "design-notes")
        self.assertIn("revision draft proj/design-notes", out)
        self.assertEqual(before, self.text(path))
        draft = self.text(self.draft_path("design-notes"))
        self.assertIn("revises: design-notes", draft)
        self.assertIn("written: 2026-10-01", draft)
        self.assertIn("updated: 2026-11-06", draft)
        self.assertIn(prose("alpha"), draft)
        self.assertIn("(added 2026-11-06) " + prose("beta", 30), draft)

    def test_with_a_revision_draft_in_place_the_reviewed_note_cannot_be_extended_again_but_the_draft_can(self):
        self.note("reviewed", "proj", "design-notes", title="Design notes", body=prose("alpha") + "\n")
        self.saved("x", prose("beta", 30), "idea", "--into", "design-notes")
        self.refused("save", "--title", "x", "--kind", "idea", "--body", "more", "--into", "design-notes", contains="more than one")
        self.refused("save", "--title", "x", "--kind", "idea", "--body", "more", "--into", "design-notes", "--state", "reviewed", contains="revision draft")
        self.assertEqual(0, self.save("x", "more words", "idea", "--into", "design-notes", "--state", "draft")[0])
        self.assertIn("(added 2026-11-06) more words", self.text(self.draft_path("design-notes")))

    def test_into_refuses_a_note_that_is_not_there_is_archived_or_is_in_another_wing(self):
        self.note("archived", "proj", "gone.20261001T000000Z", title="Gone")
        self.note("reviewed", "other", "elsewhere", title="Elsewhere")
        self.saved("Base note", prose("alpha"))
        for target in ("nothing", "gone", "other/elsewhere", "../x", "a/b/c", "", "..", "proj/extra/base-note", "proj/../base-note", "/base-note", "proj//base-note"):
            self.refused("save", "--title", "x", "--kind", "idea", "--body", "word", "--into", target)

    def test_into_with_the_kind_and_the_title_of_the_call_leaves_the_notes_own_header(self):
        self.saved("Base note", prose("alpha"), "decision")
        self.saved("a different title", prose("beta", 30), "lesson", "--into", "base-note")
        shown = self.text(self.draft_path("base-note"))
        self.assertIn("title: Base note", shown)
        self.assertIn("kind: decision", shown)

    def test_the_resulting_note_must_stay_within_the_size_limit(self):
        self.note("draft", "proj", "nearly-full", title="Nearly full", body="y " * 8000)
        self.refused("save", "--title", "x", "--kind", "idea", "--body", "z " * 400, "--into", "nearly-full", contains="larger than")


class Atomic(Save):
    def test_a_write_that_fails_before_the_rename_leaves_the_old_note_whole_and_no_temporary_file(self):
        self.saved("Base note", prose("alpha"))
        before = self.text(self.draft_path("base-note"))
        with unittest.mock.patch("os.fsync", side_effect=OSError(5, "boom")):
            code, out, err = self.save("x", "an addition", "idea", "--into", "base-note")
        self.assertEqual((1, ""), (code, out))
        self.assertEqual(before, self.text(self.draft_path("base-note")))
        self.assertEqual(["base-note.txt"], os.listdir(self.folder("draft", "proj")))

    def test_a_failed_link_makes_no_note_and_leaves_no_temporary_file(self):
        with unittest.mock.patch("os.link", side_effect=OSError(5, "boom")):
            code, out, err = self.save("Brand new")
        self.assertEqual((1, ""), (code, out))
        self.assertEqual([], os.listdir(self.folder("draft", "proj")))


class Lock(Save):
    def lock_file(self):
        return os.path.join(self.notes, ".locks", "proj")

    def hold(self):
        self.saved("Base note", prose("alpha"))
        descriptor = os.open(self.lock_file(), os.O_RDWR)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        self.addCleanup(os.close, descriptor)

    def test_a_held_lock_is_waited_for_a_little_and_then_refused_with_nothing_changed(self):
        self.hold()
        before = self.tree(self.notes)
        with unittest.mock.patch.object(self.helper, "LOCK_TRIES", 3), unittest.mock.patch.object(self.helper, "LOCK_PAUSE", 0.01):
            self.refused("save", "--title", "x", "--kind", "idea", "--body", "word", "--into", "base-note", contains="another save is in progress")
        self.assertEqual(before, self.tree(self.notes))

    def test_a_lock_that_is_a_link_is_refused(self):
        self.saved("Base note", prose("alpha"))
        victim = os.path.join(self.base, "victim")
        os.remove(self.lock_file())
        os.symlink(victim, self.lock_file())
        self.refused("save", "--title", "x", "--kind", "idea", "--body", "word", "--into", "base-note", contains="lock")
        self.assertFalse(os.path.exists(victim))

    def test_two_saves_at_once_to_the_same_note_both_land(self):
        self.saved("Base note", prose("alpha"))
        results = []

        def add(number):
            results.append(self.run_helper("save", "--title", "x", "--kind", "idea", "--body", "addition number %d" % number, "--into", "base-note")[0])

        threads = [threading.Thread(target=add, args=(n,)) for n in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual([0, 0], results)
        text = self.text(self.draft_path("base-note"))
        self.assertIn("addition number 0", text)
        self.assertIn("addition number 1", text)


class Expiry(Save):
    def old_draft(self, name, updated, wing="proj"):
        return self.note("draft", wing, name, title=name.title(), updated=updated, written="2026-09-01")

    def stamp(self):
        patch = unittest.mock.patch.object(self.helper, "utc_stamp", return_value="20261106T120000Z")
        patch.start()
        self.addCleanup(patch.stop)

    def test_a_draft_more_than_thirty_days_old_is_archived_by_the_next_save_list_or_wings(self):
        self.stamp()
        for verb, args in (("save", ("--title", "New one", "--kind", "idea", "--body", prose("beta"))), ("list", ()), ("wings", ())):
            name = "stale-" + verb
            self.old_draft(name, "2026-10-01")   # 36 days before the fixed clock
            code, out, err = self.run_helper(verb, *args)
            self.assertEqual(0, code, err)
            self.assertFalse(os.path.exists(self.draft_path(name)), verb)
            self.assertTrue(os.path.isfile(os.path.join(self.folder("archived", "proj"), name + ".20261106T120000Z.txt")), verb)

    def test_thirty_days_exactly_and_reviewed_notes_are_not_archived(self):
        self.stamp()
        self.old_draft("on-the-line", "2026-10-07")   # 30 days
        self.note("reviewed", "proj", "ancient", title="Ancient", updated="2026-01-01")
        self.assertEqual(0, self.run_helper("list")[0])
        self.assertTrue(os.path.isfile(self.draft_path("on-the-line")))
        self.assertTrue(os.path.isfile(os.path.join(self.folder("reviewed", "proj"), "ancient.txt")))

    def test_it_is_idempotent_and_archived_notes_are_hidden_unless_asked_for(self):
        self.stamp()
        self.old_draft("stale", "2026-10-01")
        self.run_helper("list")
        before = self.tree(self.notes)
        self.run_helper("list")
        self.assertEqual(before, self.tree(self.notes))
        code, out, err = self.run_helper("list")
        self.assertNotIn("Stale", out)
        code, out, err = self.run_helper("list", "--state", "archived")
        self.assertIn("Stale", out)
        code, out, err = self.run_helper("wings")
        self.assertRegex(out, r"proj \| reviewed 0 \| drafts 0 \| newest 2026-10-01 \| archived 1")

    def test_an_archive_name_that_exists_is_not_replaced_and_the_draft_stays(self):
        self.stamp()
        self.old_draft("stale", "2026-10-01")
        os.makedirs(self.folder("archived", "proj"))
        taken = os.path.join(self.folder("archived", "proj"), "stale.20261106T120000Z.txt")
        with open(taken, "w") as handle:
            handle.write("already here\n")
        self.assertEqual(0, self.run_helper("list")[0])
        self.assertEqual("already here\n", self.text(taken))
        self.assertTrue(os.path.isfile(self.draft_path("stale")))

    def test_expiry_does_nothing_when_there_is_no_folder_and_makes_the_archive_folder_private(self):
        self.stamp()
        before = self.tree()
        self.assertEqual(0, self.run_helper("wings")[0])
        self.assertEqual(before, self.tree())
        self.old_draft("stale", "2026-10-01")
        self.run_helper("list")
        self.assertEqual(0o700, stat.S_IMODE(os.stat(self.folder("archived", "proj")).st_mode))

    def test_a_held_lock_skips_the_expiry_without_waiting_and_the_listing_still_works(self):
        import time
        self.stamp()
        self.old_draft("stale", "2026-10-01")
        os.makedirs(os.path.join(self.notes, ".locks"), exist_ok=True)
        descriptor = os.open(os.path.join(self.notes, ".locks", "proj"), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        self.addCleanup(os.close, descriptor)
        started = time.monotonic()
        for verb in ("list", "wings"):
            self.assertEqual(0, self.run_helper(verb)[0])
        self.assertLess(time.monotonic() - started, 1.0, "the expiry waited for a lock that was held")
        self.assertTrue(os.path.isfile(self.draft_path("stale")))

    def test_a_draft_that_another_run_archived_between_the_check_and_the_lock_is_not_an_error(self):
        self.stamp()
        self.old_draft("stale", "2026-10-01")
        real = self.helper.take_lock

        def meanwhile(root_fd, wing, tries):
            descriptor = real(root_fd, wing, tries)
            os.makedirs(self.folder("archived", "proj"), exist_ok=True)
            os.rename(self.draft_path("stale"), os.path.join(self.folder("archived", "proj"), "stale.20261106T110000Z.txt"))
            return descriptor

        with unittest.mock.patch.object(self.helper, "take_lock", meanwhile):
            code, out, err = self.run_helper("list")
        self.assertEqual((0, ""), (code, err), err)

    def test_nothing_is_archived_or_made_through_a_link_in_the_notes_path(self):
        self.stamp()
        real = os.path.join(self.base, "real-project-workbench")
        os.makedirs(os.path.join(real, "mempalace", ".drafts", "proj"))
        os.makedirs(self.data, exist_ok=True)
        os.symlink(real, os.path.join(self.data, "project-workbench"))
        with open(os.path.join(real, "mempalace", ".drafts", "proj", "stale.txt"), "w") as handle:
            handle.write("title: Stale\nkind: idea\nwing: proj\nwritten: 2026-09-01\nupdated: 2026-10-01\n\nBody.\n")
        before = self.tree(real)
        for verb in (("list",), ("wings",)):
            self.assertEqual(0, self.run_helper(*verb)[0])
        self.assertEqual(before, self.tree(real), "the expiry wrote through a link")
        self.assertEqual(before, self.tree(real))
        self.refused("save", "--title", "T", "--kind", "idea", "--body", prose("alpha"), contains="link")
        self.assertEqual(before, self.tree(real))


if __name__ == "__main__":
    unittest.main()
