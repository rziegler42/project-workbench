"""The ``todo`` helper of ``groundwork``: ``drop`` and the drop log.

Plan ``2026-11-11-todo-list``, Increment C (``docs/specs/todo-list.md``). The helper is loaded by its path and run in process on a
synthetic project with a fixed date. The drop log is the file ``dropped.log`` in the list's folder."""

import datetime
import io
import json
import os
import stat
import threading
import unittest
import unittest.mock

from tests import support_docs, support_helpers

todo = support_helpers.load("todo")

FOLDER = ".workbench/local/todo"
TODAY = datetime.date(2026, 11, 11)
GITHUB = "gh" + "p_" + "A" * 36


def slurp(path):
    with open(path, "rb") as handle:
        return handle.read()


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

    def item(self, identifier, title, added="2026-11-01", body="", **more):
        self.put("%s/%s.md" % (FOLDER, identifier), header(title, added, **more) + body)

    def files(self):
        return sorted(os.listdir(self.path())) if os.path.isdir(self.path()) else []

    def log(self):
        with open(self.path("dropped.log"), encoding="utf-8") as handle:
            return handle.read()

    def refused(self, *argv):
        code, out, err = self.call(*argv)
        self.assertEqual((1, ""), (code, out), err)
        self.assertTrue(err.startswith("refused: "), err)
        return err


class Drop(Base):
    def test_the_file_is_removed_the_item_is_printed_in_full_and_one_line_is_logged(self):
        self.item("a", "Rename the thing", body="Line one\nLine two", source="docs/plans/x.md#C", step="Open it", size="quick", owner="yes")
        self.item("b", "Another")
        code, out, err = self.call("drop", "a")
        self.assertEqual((0, ""), (code, err))
        self.assertEqual("dropped: a\ntitle: Rename the thing\nadded: 2026-11-01 (10 days ago)\nsource: docs/plans/x.md#C\nstep: Open it\n"
                         "size: quick\nowner: yes\n\nLine one\nLine two\n", out)
        self.assertEqual(["b.md", "dropped.log"], self.files())
        self.assertEqual("2026-11-11\ta\tRename the thing\n", self.log())

    def test_the_item_no_longer_appears_and_no_other_item_changes(self):
        self.item("a", "First")
        self.item("b", "Second")
        before = (slurp(self.path("b.md")), os.stat(self.path("b.md")).st_mtime_ns)
        self.call("drop", "a")
        self.assertEqual("  10d  -        Second  [b]\n", self.call("list")[1])
        self.assertEqual(before, (slurp(self.path("b.md")), os.stat(self.path("b.md")).st_mtime_ns))

    def test_two_drops_append_two_lines_and_the_log_is_private(self):
        self.item("a", "First")
        self.item("b", "Second")
        self.call("drop", "a")
        self.call("drop", "b")
        self.assertEqual("2026-11-11\ta\tFirst\n2026-11-11\tb\tSecond\n", self.log())
        self.assertEqual(0o600, stat.S_IMODE(os.stat(self.path("dropped.log")).st_mode))

    def test_an_id_may_be_used_again_after_its_item_is_dropped(self):
        self.assertEqual("added: same-title\n", self.call("add", "--title", "Same title")[1])
        self.call("drop", "same-title")
        self.assertEqual("added: same-title\n", self.call("add", "--title", "Same title")[1])

    def test_a_missing_item_is_refused_and_no_log_is_made(self):
        self.item("a", "Something")
        self.assertIn("there is no item nope", self.refused("drop", "nope"))
        self.assertEqual(["a.md"], self.files())

    def test_no_folder_is_a_missing_item_and_nothing_is_made(self):
        self.assertIn("there is no item a", self.refused("drop", "a"))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))

    def test_the_name_may_be_given_with_its_suffix(self):
        self.item("a", "Something")
        self.assertEqual(0, self.call("drop", "a.md")[0])
        self.assertEqual(["dropped.log"], self.files())

    def test_wrong_forms_are_usage_errors(self):
        for argv in (["drop"], ["drop", "a", "b"]):
            code, out, err = self.call(*argv)
            self.assertEqual((2, ""), (code, out))
            self.assertIn("usage: todo", err)


class Names(Base):
    def test_an_argument_that_leaves_the_folder_or_names_a_hidden_file_is_refused(self):
        self.put(".workbench/local/secret.md", header("Outside the list", "2026-11-01"))
        self.item("a", "Kept")
        self.put("%s/.tmp-abc" % FOLDER, "temporary")
        for argument in ("../secret", "../../local/secret", "/etc/passwd", ".tmp-abc", "", "a\0b", "x" * 300):
            with self.subTest(argument=argument[:20]):
                self.assertIn("there is no item", self.refused("drop", argument))
        self.assertTrue(os.path.exists(os.path.join(self.root, ".workbench", "local", "secret.md")))
        self.assertEqual([".tmp-abc", "a.md"], self.files())

    def test_the_argument_in_a_refusal_is_printed_safely(self):
        self.assertNotIn("\x1b", self.refused("drop", "bad\x1b[31m"))

    def test_the_log_cannot_be_dropped_and_is_not_an_item(self):
        self.item("a", "Kept")
        self.call("drop", "a")
        for argument in ("dropped.log", "dropped", "dropped.log.md"):
            self.assertIn("there is no item", self.refused("drop", argument))
        self.assertEqual(["dropped.log"], self.files())
        self.assertEqual((0, "the list is empty\n", ""), self.call("list"))
        self.assertIn("there is no item", self.refused("show", "dropped"))

    def test_the_log_is_never_listed_even_beside_items_and_unreadable_files(self):
        self.item("a", "Kept")
        self.put("%s/dropped.log" % FOLDER, "2026-11-01\tx\tTitle\n")
        self.put("%s/broken.md" % FOLDER, "nonsense")
        self.assertEqual("  10d  -        Kept  [a]\nunreadable: broken.md\n", self.call("list")[1])

    def test_add_cannot_make_an_id_that_names_the_log(self):
        self.assertEqual("added: dropped-log\n", self.call("add", "--title", "dropped.log")[1])
        self.assertEqual("added: dropped\n", self.call("add", "--title", "dropped")[1])
        self.assertEqual(["dropped-log.md", "dropped.md"], self.files())


class Unreadable(Base):
    def test_a_file_that_is_not_an_item_is_dropped_by_its_name_and_never_printed(self):
        self.put("%s/broken.md" % FOLDER, "title: T\nsecret words")
        code, out, err = self.call("drop", "broken")
        self.assertEqual((0, "dropped: broken (not an item; its text is not shown)\n", ""), (code, out, err))
        self.assertEqual(["dropped.log"], self.files())
        self.assertEqual("2026-11-11\tbroken\t(not an item)\n", self.log())

    def test_a_file_whose_name_does_not_print_safely_is_dropped_only_by_its_exact_name(self):
        self.item("weird\x1b[2J", "Hidden title")
        code, out, err = self.call("drop", "weird\x1b[2J.md")
        self.assertEqual((0, ""), (code, err))
        self.assertNotIn("\x1b", out)
        self.assertNotIn("Hidden title", out)
        self.assertEqual("dropped: (name not shown) (not an item; its text is not shown)\n", out)
        self.assertEqual(["dropped.log"], self.files())
        self.assertNotIn("\x1b", self.log())
        self.assertEqual("2026-11-11\t(name not shown)\t(not an item)\n", self.log())

    def test_a_file_named_like_a_credential_is_dropped_without_echoing_the_name(self):
        self.put("%s/%s.md" % (FOLDER, GITHUB), "nonsense")
        code, out, err = self.call("drop", GITHUB + ".md")
        self.assertEqual((0, ""), (code, err))
        self.assertNotIn(GITHUB, out)
        self.assertNotIn(GITHUB, self.log())
        self.assertEqual(["dropped.log"], self.files())

    def test_a_directory_is_refused_and_stays(self):
        os.makedirs(self.path("dir.md"))
        self.assertIn("is a directory", self.refused("drop", "dir"))
        self.assertEqual(["dir.md"], self.files())

    def test_a_link_is_removed_and_its_target_is_not_touched(self):
        outside = os.path.join(self.outside, "o.md")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write(header("Outside secret", "2026-11-01"))
        os.makedirs(self.path())
        os.symlink(outside, self.path("o.md"))
        code, out, err = self.call("drop", "o")
        self.assertEqual((0, ""), (code, err))
        self.assertNotIn("Outside secret", out)
        self.assertTrue(os.path.exists(outside))
        self.assertEqual(["dropped.log"], self.files())

    def test_a_file_with_two_links_loses_this_name_only(self):
        self.item("a", "Twice")
        os.link(self.path("a.md"), self.path("b.md"))
        code, out, err = self.call("drop", "a")
        self.assertEqual((0, ""), (code, err))
        self.assertIn("not an item", out)
        self.assertEqual(["b.md", "dropped.log"], self.files())


class Credentials(Base):
    def test_a_field_with_a_credential_shape_is_not_printed_or_logged_and_the_file_is_removed(self):
        self.item("a", "Rotate " + GITHUB, body="the password: hunter2hunter2", source="docs/plans/x.md#C")
        code, out, err = self.call("drop", "a")
        self.assertEqual((0, ""), (code, err))
        for text in (out, self.log()):
            self.assertNotIn(GITHUB, text)
            self.assertNotIn("hunter2", text)
        self.assertIn("[title not shown: credential-shaped text (github-token)]", out)
        self.assertIn("[body not shown: credential-shaped text (assigned-secret)]", out)
        self.assertIn("source: docs/plans/x.md#C\n", out)
        self.assertEqual(["dropped.log"], self.files())
        self.assertIn("[title not shown", self.log())


class TheLog(Base):
    def test_a_log_at_its_bound_refuses_the_drop_and_keeps_the_item(self):
        self.item("a", "First")
        self.item("b", "Second")
        with unittest.mock.patch.object(todo, "MAX_LOG", 30):
            self.assertEqual(0, self.call("drop", "a")[0])   # the first line is 19 bytes, the second would make 39
            self.assertIn("trim it by hand", self.refused("drop", "b"))
        self.assertEqual(["b.md", "dropped.log"], self.files())
        self.assertEqual(19, os.path.getsize(self.path("dropped.log")))

    def test_the_bound_is_a_sensible_size(self):
        self.assertGreaterEqual(todo.MAX_LOG, 65536)
        self.assertLessEqual(todo.MAX_LOG, 1048576)

    def test_a_link_at_the_logs_place_is_refused_and_nothing_is_dropped_or_written(self):
        self.item("a", "Kept")
        target = os.path.join(self.outside, "elsewhere.log")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("before\n")
        os.symlink(target, self.path("dropped.log"))
        self.assertIn("nothing was dropped", self.refused("drop", "a"))
        self.assertEqual(b"before\n", slurp(target))
        self.assertIn("a.md", self.files())

    def test_a_log_with_two_links_is_refused(self):
        self.item("a", "Kept")
        self.put("%s/dropped.log" % FOLDER, "x\n")
        os.link(self.path("dropped.log"), os.path.join(self.outside, "copy.log"))
        self.assertIn("nothing was dropped", self.refused("drop", "a"))
        self.assertIn("a.md", self.files())

    def test_a_log_that_is_not_a_file_is_refused(self):
        self.item("a", "Kept")
        os.mkfifo(self.path("dropped.log"))
        self.assertIn("nothing was dropped", self.refused("drop", "a"))
        self.assertIn("a.md", self.files())

    def test_a_log_that_cannot_be_written_after_the_removal_is_reported_and_the_item_is_still_printed(self):
        self.item("a", "Printed anyway")
        with unittest.mock.patch.object(todo.os, "write", side_effect=OSError(28, "No space left on device")):
            code, out, err = self.call("drop", "a")
        self.assertEqual(0, code)
        self.assertIn("title: Printed anyway", out)
        self.assertIn("the drop log could not be written (No space left on device)", err)
        self.assertEqual(["dropped.log"], self.files())

    def test_a_short_write_to_the_log_is_reported(self):
        self.item("a", "Printed anyway")
        with unittest.mock.patch.object(todo.os, "write", return_value=3):
            code, out, err = self.call("drop", "a")
        self.assertEqual(0, code)
        self.assertIn("title: Printed anyway", out)
        self.assertIn("the drop log could not be written (a short write)", err)

    def test_two_drops_at_once_leave_two_whole_lines(self):
        for number in range(20):
            self.item("i%02d" % number, "Item %02d" % number)
        threads = [threading.Thread(target=self.call, args=("drop", "i%02d" % number)) for number in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        lines = self.log().split("\n")
        self.assertEqual("", lines.pop())
        self.assertEqual(sorted("2026-11-11\ti%02d\tItem %02d" % (number, number) for number in range(20)), sorted(lines))
        self.assertEqual(["dropped.log"], self.files())


if __name__ == "__main__":
    unittest.main()
