"""The ``todo`` helper of ``groundwork``: ``list`` and ``show``.

Plan ``2026-11-11-todo-list``, Increment B (``docs/specs/todo-list.md``). The helper is loaded by its path and run in process on a
synthetic project with a fixed date. Items are written straight into the folder, so that each test controls the file it reads."""

import datetime
import io
import json
import os
import unittest
import unittest.mock

from tests import support_docs, support_helpers

todo = support_helpers.load("todo")

FOLDER = ".workbench/local/todo"
TODAY = datetime.date(2026, 11, 11)
GITHUB = "gh" + "p_" + "A" * 36


def header(title, added, **more):
    lines = ["title: " + title, "added: " + added]
    lines += ["%s: %s" % (key, value) for key, value in more.items()]
    return "\n".join(lines) + "\n\n"


class Base(support_docs.Base):
    def setUp(self):
        super().setUp()
        os.mkdir(os.path.join(self.root, ".git"))
        os.mkdir(os.path.join(self.root, ".workbench"))
        self.put(".workbench/manifest.json", json.dumps({"seed": "seed-one"}))
        patcher = unittest.mock.patch.object(todo, "today", lambda: TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = todo.main(list(argv), io.StringIO(""), out, err, self.root, False)
        return code, out.getvalue(), err.getvalue()

    def path(self, name=""):
        return os.path.join(self.root, *FOLDER.split("/"), *([name] if name else []))

    def item(self, identifier, title, added, body="", **more):
        self.put("%s/%s.md" % (FOLDER, identifier), header(title, added, **more) + body)

    def lines(self, *argv):
        code, out, err = self.call(*argv)
        self.assertEqual((0, ""), (code, err), out)
        return out.split("\n")[:-1]

    def refused(self, *argv):
        code, out, err = self.call(*argv)
        self.assertEqual((1, ""), (code, out), err)
        self.assertTrue(err.startswith("refused: "), err)
        return err


class List(Base):
    def test_items_are_listed_oldest_first_with_age_size_title_and_id(self):
        self.item("newer", "Newer thing", "2026-11-05", size="quick")
        self.item("oldest", "Oldest thing", "2026-10-20", size="session")
        self.item("middle", "Middle thing", "2026-11-01")
        self.assertEqual(["  22d  session  Oldest thing  [oldest]",
                          "  10d  -        Middle thing  [middle]",
                          "   6d  quick    Newer thing  [newer]"], self.lines("list"))

    def test_an_item_that_needs_the_owner_is_marked_and_a_future_date_is_age_zero(self):
        self.item("a", "Ask first", "2026-12-01", owner="yes")
        self.assertEqual(["   0d  -        Ask first  [a] (owner)"], self.lines("list"))

    def test_the_same_day_is_ordered_by_id(self):
        self.item("b", "B thing", "2026-11-10")
        self.item("a", "A thing", "2026-11-10")
        self.assertEqual(["[a]", "[b]"], [line.split("  ")[-1][:3] for line in self.lines("list")])

    def test_size_shows_only_items_of_that_size_and_an_unsized_item_is_in_the_whole_list_only(self):
        self.item("q", "Quick one", "2026-11-01", size="quick")
        self.item("s", "Sitting one", "2026-11-01", size="sitting")
        self.item("u", "Unsized one", "2026-11-01")
        self.assertEqual(3, len(self.lines("list")))
        self.assertEqual(["Quick one"], [line.split("  ")[-2] for line in self.lines("list", "--size", "quick")])
        self.assertEqual(["Sitting one"], [line.split("  ")[-2] for line in self.lines("list", "--size", "sitting")])

    def test_mechanical_leaves_out_items_that_need_the_owner(self):
        self.item("m", "Mechanical", "2026-11-01")
        self.item("o", "Needs a decision", "2026-11-01", owner="yes")
        self.assertEqual(["  10d  -        Mechanical  [m]"], self.lines("list", "--mechanical"))

    def test_older_than_keeps_items_strictly_older_than_the_days(self):
        self.item("ten", "Ten days", "2026-11-01")
        self.item("nine", "Nine days", "2026-11-02")
        self.assertEqual(["  10d  -        Ten days  [ten]"], self.lines("list", "--older-than", "9"))
        self.assertEqual("no item matches\n", self.call("list", "--older-than", "10")[1])
        self.assertEqual(2, len(self.lines("list", "--older-than", "0")))

    def test_the_filters_combine(self):
        self.item("a", "Quick and mechanical", "2026-10-01", size="quick")
        self.item("b", "Quick but owner", "2026-10-01", size="quick", owner="yes")
        self.item("c", "Quick and young", "2026-11-10", size="quick")
        self.item("d", "Sitting and old", "2026-10-01", size="sitting")
        self.assertEqual(["  41d  quick    Quick and mechanical  [a]"],
                         self.lines("list", "--size", "quick", "--mechanical", "--older-than", "5"))

    def test_no_folder_is_an_empty_list_and_nothing_is_made(self):
        self.assertEqual((0, "the list is empty\n", ""), self.call("list"))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))

    def test_an_empty_folder_is_an_empty_list(self):
        os.makedirs(self.path())
        self.assertEqual((0, "the list is empty\n", ""), self.call("list"))
        self.assertEqual((0, "the list is empty\n", ""), self.call("list", "--size", "quick"))

    def test_a_filter_that_matches_nothing_says_so(self):
        self.item("a", "Something", "2026-11-01")
        self.assertEqual((0, "no item matches\n", ""), self.call("list", "--size", "quick"))

    def test_temporary_files_the_log_and_other_files_are_not_items_and_not_unreadable(self):
        self.item("a", "Something", "2026-11-01")
        for name in (".tmp-abcdef", "dropped.log", "notes.txt", "x.md.bak"):
            self.put("%s/%s" % (FOLDER, name), "title: junk\n")
        self.assertEqual(["  10d  -        Something  [a]"], self.lines("list"))

    def test_the_listing_does_not_change_the_folder(self):
        self.item("a", "Something", "2026-11-01")
        before = sorted((name, os.stat(self.path(name)).st_mtime_ns) for name in os.listdir(self.path()))
        self.lines("list")
        self.call("show", "a")
        self.assertEqual(before, sorted((name, os.stat(self.path(name)).st_mtime_ns) for name in os.listdir(self.path())))


class Unreadable(Base):
    def listed(self):
        return [line for line in self.lines("list") if line.startswith("unreadable: ")]

    def test_files_that_are_not_items_are_listed_by_name_and_never_printed(self):
        secret = "do not print this body"
        bad = {
            "no-title": "added: 2026-11-01\n\n" + secret,
            "unknown-key": header("T", "2026-11-01", colour="red") + secret,
            "repeated-key": "title: A\ntitle: B\nadded: 2026-11-01\n\n" + secret,
            "bad-date": header("T", "2026-13-45") + secret,
            "odd-date": header("T", "2026-1-5") + secret,
            "bad-size": header("T", "2026-11-01", size="huge") + secret,
            "bad-owner": header("T", "2026-11-01", owner="no") + secret,
            "no-blank-line": "title: T\nadded: 2026-11-01\n" + secret,
            "long-title": header("t" * 121, "2026-11-01") + secret,
            "control": header("T", "2026-11-01") + secret + "\x1b[31m",
            "too-big": header("T", "2026-11-01") + "x" * 5200,
            "body-too-big": header("T", "2026-11-01") + "x" * 4097,
        }
        for name, text in bad.items():
            self.put("%s/%s.md" % (FOLDER, name), text)
        self.put("%s/not-utf8.md" % FOLDER, b"title: T\nadded: 2026-11-01\n\n\xff\xfe")
        code, out, err = self.call("list")
        self.assertEqual((0, ""), (code, err))
        for name in list(bad) + ["not-utf8"]:
            self.assertIn("unreadable: %s.md\n" % name, out)
        self.assertNotIn(secret, out)
        self.assertNotIn("\x1b", out)

    def test_a_good_item_is_listed_beside_the_unreadable_ones_and_they_follow_it(self):
        self.put("%s/broken.md" % FOLDER, "nonsense")
        self.item("good", "Good", "2026-11-01")
        self.assertEqual(["  10d  -        Good  [good]", "unreadable: broken.md"], self.lines("list"))

    def test_unreadable_files_are_listed_whatever_the_filter(self):
        self.put("%s/broken.md" % FOLDER, "nonsense")
        self.assertEqual(["unreadable: broken.md"], self.lines("list", "--size", "quick"))

    def test_a_link_a_directory_and_a_file_with_two_links_are_unreadable(self):
        self.item("real", "Real", "2026-11-01")
        os.symlink(self.path("real.md"), self.path("link.md"))
        os.mkdir(self.path("dir.md"))
        os.link(self.path("real.md"), self.path("twice.md"))
        found = self.listed()
        self.assertIn("unreadable: link.md", found)
        self.assertIn("unreadable: dir.md", found)
        # `real.md` itself now has two links as well
        self.assertIn("unreadable: real.md", found)
        self.assertIn("unreadable: twice.md", found)

    def test_a_link_to_a_file_outside_is_not_read(self):
        outside = os.path.join(self.outside, "o.md")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write(header("Outside secret", "2026-11-01"))
        os.makedirs(self.path())
        os.symlink(outside, self.path("o.md"))
        code, out, err = self.call("list")
        self.assertNotIn("Outside secret", out)
        self.assertIn("unreadable: o.md", out)

    def test_a_file_name_that_does_not_print_safely_is_not_shown(self):
        self.put("%s/weird\x1b[31m.md" % FOLDER, "nonsense")
        self.put("%s/%s.md" % (FOLDER, GITHUB), "nonsense")
        code, out, err = self.call("list")
        self.assertEqual(["unreadable: (a file whose name is not shown)"] * 2, out.split("\n")[:-1])
        self.assertNotIn("\x1b", out)
        self.assertNotIn(GITHUB, out)

    def test_a_readable_item_whose_name_does_not_print_safely_is_listed_as_unreadable_and_never_shown(self):
        names = ["weird\x1b[2J", "password=hunter2xyz", GITHUB, "café"]
        for name in names:
            self.put("%s/%s.md" % (FOLDER, name), header("Hidden title", "2026-11-01"))
        code, out, err = self.call("list")
        self.assertEqual((0, ""), (code, err))
        self.assertEqual(["unreadable: (a file whose name is not shown)"] * 4, out.split("\n")[:-1])
        self.assertNotIn("Hidden title", out)
        for name in names:
            self.assertIn("there is no item", self.refused("show", name))

    def test_a_name_that_is_not_valid_utf8_does_not_stop_the_list(self):
        self.item("good", "Good", "2026-11-01")
        with unittest.mock.patch.object(todo.os, "listdir", lambda folder: ["good.md", "bad-\udcff.md"]):
            code, out, err = self.call("list")
        self.assertEqual((0, ""), (code, err))
        self.assertEqual(["  10d  -        Good  [good]", "unreadable: (a file whose name is not shown)"], out.split("\n")[:-1])
        out.encode("utf-8")

    def test_a_folder_that_is_a_link_is_refused(self):
        os.makedirs(os.path.join(self.root, ".workbench", "local"))
        os.symlink(self.outside, self.path())
        self.assertIn("link", self.refused("list"))
        self.assertIn("link", self.refused("show", "x"))


class Credentials(Base):
    def test_a_field_with_a_credential_shape_is_not_printed_and_is_named(self):
        self.item("a", "Rotate " + GITHUB, "2026-11-01")
        self.item("b", "Fine", "2026-11-02", body="x", source=GITHUB)
        code, out, err = self.call("list")
        self.assertEqual((0, ""), (code, err))
        self.assertNotIn(GITHUB, out)
        self.assertIn("[title not shown: credential-shaped text (github-token)]  [a]", out)
        self.assertIn("Fine  [b]", out)

    def test_show_prints_every_field_that_is_clean_and_names_the_ones_that_are_not(self):
        self.item("a", "Rotate " + GITHUB, "2026-11-01", body="the password: hunter2hunter2\nsecond line",
                  source="docs/plans/x.md#C", step="password=abcdefgh1234")
        code, out, err = self.call("show", "a")
        self.assertEqual((0, ""), (code, err))
        self.assertNotIn(GITHUB, out)
        self.assertNotIn("hunter2", out)
        self.assertNotIn("abcdefgh1234", out)
        self.assertIn("title: [title not shown: credential-shaped text (github-token)]\n", out)
        self.assertIn("source: docs/plans/x.md#C\n", out)
        self.assertIn("step: [step not shown: credential-shaped text (assigned-secret)]\n", out)
        self.assertIn("[body not shown: credential-shaped text (assigned-secret)]", out)
        self.assertNotIn("second line", out)

    def test_the_file_is_left_as_it_is(self):
        self.item("a", "Rotate " + GITHUB, "2026-11-01")
        with open(self.path("a.md"), encoding="utf-8") as handle:
            before = handle.read()
        self.call("list")
        self.call("show", "a")
        with open(self.path("a.md"), encoding="utf-8") as handle:
            self.assertEqual(before, handle.read())


class Show(Base):
    def test_one_item_is_printed_in_full(self):
        self.item("a", "Rename the thing", "2026-11-01", body="Line one\nLine two", source="docs/plans/x.md#C", step="Open the file",
                  size="quick", owner="yes")
        self.assertEqual((0, "id: a\ntitle: Rename the thing\nadded: 2026-11-01 (10 days ago)\nsource: docs/plans/x.md#C\nstep: Open the file\n"
                             "size: quick\nowner: yes\n\nLine one\nLine two\n", ""), self.call("show", "a"))

    def test_an_item_with_only_a_title_prints_no_empty_fields_and_no_body(self):
        self.item("a", "Only a title", "2026-11-11")
        self.assertEqual((0, "id: a\ntitle: Only a title\nadded: 2026-11-11 (0 days ago)\n", ""), self.call("show", "a"))

    def test_a_missing_id_is_refused(self):
        self.item("a", "Something", "2026-11-01")
        self.assertIn("there is no item nope", self.refused("show", "nope"))

    def test_no_folder_is_a_missing_item_and_nothing_is_made(self):
        self.assertIn("there is no item a", self.refused("show", "a"))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))

    def test_an_id_that_leaves_the_folder_or_names_a_hidden_file_is_refused(self):
        self.put(".workbench/local/secret.md", header("Outside the list", "2026-11-01"))
        for argument in ("../secret", "../../local/secret", "/etc/passwd", ".tmp-abc", "", "a\0b", "x" * 80):
            err = self.refused("show", argument)
            self.assertIn("there is no item", err)
            self.assertNotIn("Outside the list", err)

    def test_a_credential_shaped_argument_is_not_echoed_in_a_refusal(self):
        err = self.refused("show", GITHUB)
        self.assertNotIn(GITHUB, err)
        self.assertIn("there is no item (name not shown)", err)

    def test_the_id_in_a_refusal_is_printed_safely(self):
        err = self.refused("show", "bad\x1b[31m")
        self.assertNotIn("\x1b", err)

    def test_an_unreadable_file_is_refused_and_not_printed(self):
        self.put("%s/broken.md" % FOLDER, "title: T\nsecret words")
        err = self.refused("show", "broken")
        self.assertIn("cannot be read as an item", err)
        self.assertNotIn("secret words", err)

    def test_a_link_in_the_folder_is_not_followed(self):
        outside = os.path.join(self.outside, "o.md")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write(header("Outside secret", "2026-11-01"))
        os.makedirs(self.path())
        os.symlink(outside, self.path("o.md"))
        self.assertNotIn("Outside secret", self.refused("show", "o"))

    def test_the_log_and_a_temporary_file_are_not_items(self):
        self.put("%s/dropped.log" % FOLDER, header("Log", "2026-11-01"))
        self.assertIn("there is no item", self.refused("show", "dropped.log"))
        self.assertIn("there is no item", self.refused("show", "dropped"))


class Bounds(Base):
    def test_a_long_list_prints_at_most_the_limit_and_counts_the_rest(self):
        for number in range(7):
            self.item("i%d" % number, "Item %d" % number, "2026-11-0%d" % (number + 1))
        with unittest.mock.patch.object(todo, "LIST_SHOWN", 3):
            lines = self.lines("list")
        self.assertEqual(4, len(lines))
        self.assertTrue(lines[3].startswith("... 4 more are not shown"), lines)

    def test_unreadable_files_are_bounded_the_same_way(self):
        for number in range(6):
            self.put("%s/bad%d.md" % (FOLDER, number), "nonsense")
        with unittest.mock.patch.object(todo, "LIST_SHOWN", 2):
            lines = self.lines("list")
        self.assertEqual(["unreadable: bad0.md", "unreadable: bad1.md", "... 4 more files are unreadable"], lines)

    def test_files_beyond_the_item_cap_are_not_read_and_are_counted(self):
        for number in range(8):
            self.item("i%d" % number, "Item %d" % number, "2026-11-01")
        with unittest.mock.patch.object(todo, "MAX_ITEMS", 5):
            lines = self.lines("list")
        self.assertEqual(5, len([line for line in lines if line.startswith("  10d")]))
        self.assertEqual("... 3 more files in the folder were not read", lines[-1])

    def test_a_full_line_is_a_bounded_length(self):
        self.item("a", "t" * 120, "2026-11-01", size="session", owner="yes")
        self.assertLessEqual(len(self.lines("list")[0]), 160)


class Arguments(Base):
    def usage(self, *argv):
        code, out, err = self.call(*argv)
        self.assertEqual((2, ""), (code, out), err)
        self.assertIn("usage: todo", err)

    def test_wrong_forms_are_usage_errors(self):
        for argv in (["list", "extra"], ["list", "--mechanical", "--mechanical"], ["list", "--size"], ["list", "--size", "quick", "--size", "quick"],
                     ["list", "--older-than"], ["list", "--older-than", "3", "--older-than", "3"], ["list", "--other"], ["show"], ["show", "a", "b"]):
            with self.subTest(argv=argv):
                self.usage(*argv)

    def test_a_value_out_of_range_is_refused(self):
        self.assertIn("the size must be one of", self.refused("list", "--size", "huge"))
        for value in ("abc", "-1", "1.5", "1" * 7, ""):
            with self.subTest(value=value):
                self.assertIn("whole number of days", self.refused("list", "--older-than", value))


class Parse(unittest.TestCase):
    def test_a_good_item_gives_its_fields_and_body(self):
        fields = todo.parse_item(b"title: A: b\nadded: 2026-11-01\nsize: quick\n\nbody\n\nmore")
        self.assertEqual({"title": "A: b", "added": "2026-11-01", "size": "quick", "body": "body\n\nmore"}, fields)

    def test_an_item_made_by_add_is_read_back(self):
        data = todo.serialize({"title": "T", "source": "s", "step": "p", "size": "sitting"}, True, "b\nc")
        self.assertEqual({"title": "T", "added": todo.today().isoformat(), "source": "s", "step": "p", "size": "sitting", "owner": "yes", "body": "b\nc"},
                         todo.parse_item(data))


if __name__ == "__main__":
    unittest.main()
