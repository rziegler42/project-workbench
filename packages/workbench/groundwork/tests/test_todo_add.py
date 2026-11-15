"""The ``todo`` helper of ``groundwork``: the declaration and ``add``.

Plan ``2026-11-11-todo-list``, Increment A (``docs/specs/todo-list.md``). The helper is one file over the kit, loaded here by
its path and run in process on a synthetic project with a fixed date. The list is the untracked folder
``.workbench/local/todo/``; one file per item. How the launcher starts the helper is tested elsewhere; this file tests
the declaration and what ``add`` writes and refuses."""

import datetime
import io
import json
import os
import stat
import unittest
import unittest.mock

from tests import support_docs, support_helpers

todo = support_helpers.load("todo")
notes = support_helpers.load("mempalace-notes")

MODULE = os.path.join(support_helpers.support_install.ROOT, "packages", "workbench", "groundwork")
FOLDER = ".workbench/local/todo"
TODAY = datetime.date(2026, 11, 11)


def token(prefix, count, letter="A"):
    """A credential-shaped string built here, so that this file holds none."""
    return prefix + letter * count


GITHUB = token("gh" + "p_", 36)
AWS = token("AK" + "IA", 16)


class Declaration(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(MODULE, "module.json"), encoding="utf-8") as handle:
            self.document = json.load(handle)

    def test_groundwork_provides_todo_beside_its_four_capabilities(self):
        self.assertEqual(["specs", "roadmaps", "decisions", "references", "todo"], self.document["provides"])

    def test_the_helper_is_shipped_and_the_command_is_declared_with_four_agent_run_arguments(self):
        self.assertIn("helper/todo", self.document["ships"])
        command = self.document["commands"]["todo"]
        self.assertEqual("helper/todo", command["helper"])
        self.assertEqual(["add", "list", "show", "drop"], command["arguments"])
        for field in ("owner", "levels", "preview", "checkpoint_of", "describes", "describe", "asks"):
            self.assertNotIn(field, command)

    def test_the_decision_command_is_untouched(self):
        command = self.document["commands"]["groundwork"]
        self.assertEqual(["preview", "accept"], command["arguments"])
        self.assertEqual(["accept"], command["owner"])

    def test_the_credential_rules_equal_those_of_the_notes_helper(self):
        mine = [(name, pattern.pattern, pattern.flags) for name, pattern in todo.CREDENTIAL_PATTERNS]
        theirs = [(name, pattern.pattern, pattern.flags) for name, pattern in notes.CREDENTIAL_PATTERNS]
        self.assertEqual(theirs, mine)
        self.assertEqual(notes.JOINED, todo.JOINED)

    def test_the_credential_scan_gives_the_notes_helpers_answers(self):
        for text in (GITHUB, AWS, "password: hunter2hunter2", "plain words", "the api key is not recorded",
                     "rotate the password policy"):
            self.assertEqual(notes.credential_hits(text), todo.credential_hits(text), text)


class Base(support_docs.Base):
    def setUp(self):
        super().setUp()
        os.mkdir(os.path.join(self.root, ".git"))
        os.mkdir(os.path.join(self.root, ".workbench"))
        self.put(".workbench/manifest.json", json.dumps({"seed": "seed-one"}))
        patcher = unittest.mock.patch.object(todo, "today", lambda: TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, *argv, cwd=None):
        out, err = io.StringIO(), io.StringIO()
        code = todo.main(list(argv), io.StringIO(""), out, err, cwd or self.root, False)
        return code, out.getvalue(), err.getvalue()

    def add(self, title, *more):
        return self.call("add", "--title", title, *more)

    def path(self, name=""):
        return os.path.join(self.root, *FOLDER.split("/"), *([name] if name else []))

    def files(self):
        found = os.listdir(self.path()) if os.path.isdir(self.path()) else []
        return sorted(found)

    def read(self, name):
        with open(self.path(name), encoding="utf-8") as handle:
            return handle.read()

    def refused(self, *argv):
        code, out, err = self.call(*argv)
        self.assertEqual((1, ""), (code, out), err)
        self.assertTrue(err.startswith("refused: "), err)
        return err


class Add(Base):
    def test_a_title_alone_writes_one_item_and_prints_its_id(self):
        code, out, err = self.add("Fix the stale line in groundwork")
        self.assertEqual((0, "added: fix-the-stale-line-in-groundwork\n", ""), (code, out, err))
        self.assertEqual(["fix-the-stale-line-in-groundwork.md"], self.files())
        self.assertEqual("title: Fix the stale line in groundwork\nadded: 2026-11-11\n\n", self.read(self.files()[0]))

    def test_the_optional_fields_are_written_in_a_fixed_order_and_a_body_follows_a_blank_line(self):
        code, out, err = self.add("Rename the thing", "--body", "Line one\nLine two", "--owner", "--size", "quick",
                                  "--step", "Open the file", "--source", "docs/plans/x.md#C")
        self.assertEqual((0, ""), (code, err), out)
        self.assertEqual("title: Rename the thing\nadded: 2026-11-11\nsource: docs/plans/x.md#C\nstep: Open the file\n"
                         "size: quick\nowner: yes\n\nLine one\nLine two", self.read("rename-the-thing.md"))

    def test_the_folder_is_made_mode_0700_below_the_workbench_directory(self):
        self.assertEqual(0, self.add("One")[0])
        for rel in (".workbench/local", FOLDER):
            self.assertEqual(0o700, stat.S_IMODE(os.stat(os.path.join(self.root, *rel.split("/"))).st_mode), rel)

    def test_the_id_is_a_slug_of_the_title_and_a_title_with_no_letters_gets_a_plain_id(self):
        self.assertEqual("added: a-b-c-d\n", self.add("A, B & C -- D!")[1])
        self.assertEqual("added: item\n", self.add("!!!")[1])

    def test_a_long_title_gives_a_short_id(self):
        out = self.add("w" * 120)[1]
        self.assertEqual("added: " + "w" * 60 + "\n", out)

    def test_two_titles_that_make_the_same_slug_take_a_numeric_suffix_and_never_overwrite(self):
        self.assertEqual("added: fix-it\n", self.add("Fix it")[1])
        code, out, err = self.add("Fix it!")
        self.assertEqual((0, "added: fix-it-2\n", ""), (code, out, err))
        self.assertEqual(["fix-it-2.md", "fix-it.md"], self.files())
        self.assertEqual("title: Fix it\nadded: 2026-11-11\n\n", self.read("fix-it.md"))

    def test_an_exact_repeat_of_a_title_is_refused_whatever_its_case_or_spacing(self):
        self.assertEqual(0, self.add("Fix  the   gate")[0])
        err = self.refused("add", "--title", "fix the gate")
        self.assertIn("fix-the-gate", err)
        self.assertEqual(["fix-the-gate.md"], self.files())

    def test_a_near_match_is_added_and_the_id_it_resembles_is_named_but_not_its_title(self):
        self.assertEqual(0, self.add("Correct the stale line about helpers in the groundwork spec")[0])
        code, out, err = self.add("Correct the stale line about the helpers in groundwork spec")
        self.assertEqual((0, ""), (code, err))
        self.assertIn("added: correct-the-stale-line-about-the-helpers-in-groundwork-spec\n", out)
        self.assertIn("similar: correct-the-stale-line-about-helpers-in-the-groundwork-spec\n", out)
        self.assertNotIn("title", out)
        self.assertEqual(2, len(self.files()))

    def test_a_short_unlike_title_is_not_called_similar(self):
        self.assertEqual(0, self.add("Fix the gate")[0])
        self.assertNotIn("similar", self.add("Fix the log")[1])

    def test_a_leftover_temporary_file_is_ignored(self):
        os.makedirs(self.path())
        with open(self.path(".tmp-0123456789ab"), "w") as handle:
            handle.write("title: half\n")
        self.assertEqual("added: one\n", self.add("One")[1])

    def test_a_file_of_another_name_in_the_folder_is_not_an_item_and_is_left_alone(self):
        os.makedirs(self.path())
        with open(self.path("notes.txt"), "w") as handle:
            handle.write("mine\n")
        self.assertEqual(0, self.add("One")[0])
        self.assertEqual("mine\n", self.read("notes.txt"))


class Bounds(Base):
    def test_every_field_has_a_bound_and_the_refusal_names_the_field(self):
        cases = (("title", ("--title", "t" * 121)), ("source", ("--source", "s" * 201)), ("step", ("--step", "p" * 201)),
                 ("body", ("--body", "b" * 4097)))
        for field, extra in cases:
            args = ("add", "--title", "ok") if field != "title" else ("add",)
            err = self.refused(*args, *extra)
            self.assertIn(field, err)
        self.assertEqual([], self.files())

    def test_values_at_the_bound_pass(self):
        code, out, err = self.call("add", "--title", "t" * 120, "--source", "s" * 200, "--step", "p" * 200)
        self.assertEqual((0, ""), (code, err), out)

    def test_the_whole_item_is_bounded_in_bytes(self):
        euro = "\u20ac"   # three bytes each, so the header alone is near 1.5 KiB
        err = self.refused("add", "--title", euro * 120, "--source", euro * 200, "--step", euro * 200, "--body", "b" * 4000)
        self.assertIn("5 KiB", err)
        self.assertEqual([], self.files())

    def test_the_body_bound_counts_bytes_not_characters(self):
        self.assertEqual(0, self.add("Fits", "--body", "\u20ac" * 1365)[0])   # 4095 bytes
        err = self.refused("add", "--title", "Too long", "--body", "\u20ac" * 1366)   # 4098 bytes
        self.assertIn("body", err)

    def test_a_newline_or_control_character_in_a_header_value_is_refused(self):
        for value in ("two\nlines", "tab\there", "esc\x1b[0m", "nul\x00", "line sep", "zero​width"):
            for flag in ("--title", "--source", "--step"):
                args = ["add", "--title", "ok"] if flag != "--title" else ["add"]
                err = self.refused(*args, flag, value)
                self.assertIn(flag[2:], err)
        self.assertEqual([], self.files())

    def test_a_value_with_leading_or_trailing_space_and_an_empty_title_are_refused(self):
        for value in (" x", "x ", "", "   "):
            self.refused("add", "--title", value)

    def test_the_body_may_hold_newlines_but_no_other_control_character(self):
        self.assertEqual(0, self.call("add", "--title", "ok", "--body", "a\nb\n\nc")[0])
        self.refused("add", "--title", "other", "--body", "a\x1bb")
        self.refused("add", "--title", "other", "--body", "a\rb")

    def test_size_must_be_one_of_the_four_words(self):
        for size in ("quick", "sitting", "session", "large"):
            self.assertEqual(0, self.add("Size " + size, "--size", size)[0])
        err = self.refused("add", "--title", "bad", "--size", "huge")
        self.assertIn("size", err)

    def test_arguments_are_strict(self):
        for argv in (["add"], ["add", "--title"], ["add", "--title", "a", "--title", "b"], ["add", "--bogus", "x", "--title", "a"],
                     ["add", "--title", "a", "extra"], ["add", "--title", "a", "--owner", "--owner"]):
            code, out, err = self.call(*argv)
            self.assertIn(code, (1, 2), argv)
            self.assertEqual("", out)
            self.assertNotEqual("", err)
        self.assertEqual([], self.files())
        self.assertEqual(2, self.call()[0])
        self.assertEqual(2, self.call("frobnicate")[0])

    def test_the_list_is_full_at_a_thousand_items(self):
        os.makedirs(self.path())
        for number in range(1000):
            with open(self.path("item-%d.md" % number), "w") as handle:
                handle.write("title: Item %d\nadded: 2026-11-01\n\n" % number)
        err = self.refused("add", "--title", "one more")
        self.assertIn("1000", err)


class Credentials(Base):
    def test_a_credential_in_any_field_refuses_the_whole_add_and_the_text_is_not_echoed(self):
        for field in ("--title", "--source", "--step", "--body"):
            for secret in (GITHUB, AWS, "password: hunter2hunter2"):
                args = ["add", "--title", "ok"] if field != "--title" else ["add"]
                code, out, err = self.call(*args, field, secret)
                self.assertEqual((1, ""), (code, out), (field, secret))
                self.assertIn(field[2:], err)
                self.assertNotIn(secret, err)
                self.assertNotIn("hunter2", err)
        self.assertEqual([], self.files())

    def test_the_refusal_names_the_rule_that_matched(self):
        err = self.refused("add", "--title", GITHUB)
        self.assertIn("github-token", err)

    def test_a_near_miss_passes(self):
        for text in ("rotate the password policy", "the api key is not recorded", "token budget for the review"):
            self.assertEqual(0, self.add(text)[0], text)


class Paths(Base):
    def test_a_link_in_place_of_the_local_folder_is_refused_and_nothing_is_written_through_it(self):
        os.symlink(self.outside, os.path.join(self.root, ".workbench", "local"))
        self.refused("add", "--title", "One")
        self.assertEqual([], os.listdir(self.outside))

    def test_a_link_in_place_of_the_list_folder_is_refused(self):
        os.makedirs(os.path.join(self.root, ".workbench", "local"))
        os.symlink(self.outside, self.path())
        self.refused("add", "--title", "One")
        self.assertEqual([], os.listdir(self.outside))

    def test_a_file_in_place_of_the_local_folder_is_refused(self):
        self.put(".workbench/local", "not a folder")
        self.refused("add", "--title", "One")

    def test_an_item_that_is_a_link_is_not_followed_when_the_titles_are_compared(self):
        os.makedirs(self.path())
        secret = os.path.join(self.outside, "other.md")
        with open(secret, "w") as handle:
            handle.write("title: Same title\nadded: 2026-11-01\n\n")
        os.symlink(secret, self.path("same-title.md"))
        code, out, err = self.add("Same title")
        self.assertEqual((0, ""), (code, err), out)
        self.assertIn("added: same-title-2\n", out)

    def test_it_runs_from_a_subdirectory_and_writes_at_the_project_root(self):
        sub = os.path.join(self.root, "docs", "deep")
        os.makedirs(sub)
        self.assertEqual(0, self.call("add", "--title", "From below", cwd=sub)[0])
        self.assertEqual(["from-below.md"], self.files())

    def test_outside_a_project_it_refuses_and_writes_nothing(self):
        code, out, err = self.call("add", "--title", "x", cwd=self.outside)
        self.assertEqual((1, ""), (code, out))
        self.assertTrue(err.startswith("refused: "), err)
        self.assertEqual([], os.listdir(self.outside))

    def test_nothing_else_in_the_project_changes(self):
        self.assertEqual(0, self.add("One")[0])
        found = []
        for base, dirs, names in os.walk(self.root):
            found += [os.path.relpath(os.path.join(base, name), self.root) for name in names]
        self.assertEqual([".workbench/local/todo/one.md", ".workbench/manifest.json"], sorted(found))


class Creation(Base):
    def folder(self):
        os.makedirs(self.path(), exist_ok=True)
        return os.open(self.path(), os.O_RDONLY | os.O_DIRECTORY)

    def test_create_never_overwrites_a_name_that_exists(self):
        folder = self.folder()
        try:
            self.assertTrue(todo.create(folder, "a.md", b"first"))
            self.assertFalse(todo.create(folder, "a.md", b"second"))
        finally:
            os.close(folder)
        self.assertEqual("first", self.read("a.md"))
        self.assertEqual(["a.md"], self.files())   # the temporary name of the refused one is gone too

    def test_a_name_that_appears_after_the_listing_makes_add_take_the_next_suffix(self):
        self.assertEqual(0, self.add("Fix it")[0])
        with unittest.mock.patch.object(todo, "item_names", lambda folder: []):   # the helper does not see fix-it.md, so only the link can refuse the name
            code, out, err = self.add("Fix it!")
        self.assertEqual((0, "added: fix-it-2\n", ""), (code, out, err))
        self.assertEqual("title: Fix it\nadded: 2026-11-11\n\n", self.read("fix-it.md"))

    def test_the_temporary_name_of_an_earlier_run_is_left_alone_and_not_counted(self):
        os.makedirs(self.path())
        with open(self.path(".tmp-0123456789ab"), "w") as handle:
            handle.write("title: half\n")
        self.assertEqual(0, self.add("One")[0])
        self.assertEqual([".tmp-0123456789ab", "one.md"], self.files())
        self.assertEqual("title: half\n", self.read(".tmp-0123456789ab"))


class Passed(Base):
    """A file in the folder that is not a readable item is passed over when the titles are compared."""

    SAME = "title: Same title\nadded: 2026-11-01\n\n"

    def test_an_item_with_two_links_is_passed_over(self):
        os.makedirs(self.path())
        with open(self.path("first.md"), "w") as handle:
            handle.write(self.SAME)
        os.link(self.path("first.md"), self.path("second.md"))
        code, out, err = self.add("Same title")
        self.assertEqual((0, "added: same-title\n", ""), (code, out, err))

    def test_an_item_that_is_too_large_is_passed_over(self):
        os.makedirs(self.path())
        with open(self.path("big.md"), "w") as handle:
            handle.write(self.SAME + "x" * 6000)
        self.assertEqual((0, "added: same-title\n", ""), self.add("Same title"))

    def test_a_fifo_with_an_item_name_does_not_hang_add(self):
        os.makedirs(self.path())
        os.mkfifo(self.path("pipe.md"))
        self.assertEqual((0, "added: one\n", ""), self.add("One"))

    def test_the_name_of_a_near_item_is_not_echoed_when_it_is_not_safe_to_print(self):
        title = "Correct the stale line about helpers in the groundwork spec"
        os.makedirs(self.path())
        for name in (GITHUB + ".md", "esc\x1b[31mred.md"):
            with open(self.path(name), "w") as handle:
                handle.write("title: %s\nadded: 2026-11-01\n\n" % title)
        code, out, err = self.add("Correct the stale line about the helpers in groundwork spec")
        self.assertEqual((0, ""), (code, err), out)
        self.assertEqual("added: correct-the-stale-line-about-the-helpers-in-groundwork-spec\n", out)

    def test_an_exact_repeat_of_an_item_with_an_unsafe_name_is_refused_without_the_name(self):
        os.makedirs(self.path())
        with open(self.path(GITHUB + ".md"), "w") as handle:
            handle.write("title: Same title\nadded: 2026-11-01\n\n")
        err = self.refused("add", "--title", "Same title")
        self.assertNotIn(GITHUB, err)
        self.assertIn("with that title", err)


if __name__ == "__main__":
    unittest.main()
