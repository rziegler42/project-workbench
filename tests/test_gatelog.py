"""The refusal log of the command gate (``workbench/gatelog.py``): a rule and a short hash per refusal, never the command's text.

Plan ``2026-11-02-permission-system-consistency``, increment I (decision ``2026-11-02-command-gate-reads-gaps-and-data-positions``,
decision 6)."""

import hashlib
import os
import re
import shutil
import tempfile
import unittest
import unittest.mock

from workbench import gatelog

LINE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\t[a-z][a-z-]*\t[0-9a-f]{12}\n")
SECRET = "wb approve-plan docs/plans/secret-name.md"


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.chmod(self.root, 0o700)
        self.addCleanup(shutil.rmtree, self.root, True)

    def text(self):
        with open(os.path.join(self.root, gatelog.LOG), encoding="ascii") as handle:
            return handle.read()


class TheLine(unittest.TestCase):
    def test_it_is_time_rule_and_the_first_12_characters_of_a_sha256(self):
        line = gatelog.line("2026-11-02T10:00:00Z", "names", SECRET)
        self.assertRegex(line.decode("ascii"), LINE)
        want = hashlib.sha256(SECRET.encode("utf-8")).hexdigest()[:12]
        self.assertEqual(("2026-11-02T10:00:00Z\tnames\t%s\n" % want).encode("ascii"), line)

    def test_it_never_holds_the_text_of_the_command(self):
        line = gatelog.line("2026-11-02T10:00:00Z", "gap", SECRET).decode("ascii")
        for part in ("approve", "plan", "secret", "docs", "name", "md"):
            self.assertNotIn(part, line)

    def test_it_is_ascii_and_within_the_limit_whatever_the_command(self):
        for command in ("", "x" * 70000, "é☃\udc80", "tab\there\nnewline", "\x1b[31m"):
            with self.subTest(command=command[:20]):
                line = gatelog.line("2026-11-02T10:00:00Z", "names", command)
                self.assertLessEqual(len(line), gatelog.MAX_LINE)
                self.assertRegex(line.decode("ascii"), LINE)

    def test_a_longer_command_than_the_gate_reads_costs_no_more_to_hash(self):
        self.assertEqual(gatelog.fingerprint("a" * gatelog.MAX_HASHED), gatelog.fingerprint("a" * gatelog.MAX_HASHED + "b" * 5000))

    def test_a_time_or_a_rule_the_log_would_not_read_back_is_refused(self):
        for time, rule in (("yesterday", "names"), ("2026-11-02T10:00:00Z", "Names"), ("2026-11-02T10:00:00Z", "a\tb"),
                           ("2026-11-02T10:00:00Z", ""), ("2026-11-02T10:00:00Z", "x" * 50), ("2026-11-02T10:00:00Z", None),
                           (None, "names"), ("2026-11-02T10:00:00Z", "names\n")):
            with self.subTest(time=time, rule=rule):
                with self.assertRaises(ValueError):
                    gatelog.line(time, rule, "x")


class TheWriter(Base):
    def test_it_appends_one_line_per_refusal_and_never_rewrites(self):
        gatelog.record(self.root, "names", SECRET)
        first = self.text()
        gatelog.record(self.root, "gap", "wb appr$1ove-plan x")
        lines = self.text().splitlines(True)
        self.assertEqual(2, len(lines))
        self.assertEqual(first, lines[0])
        for line in lines:
            self.assertRegex(line, LINE)
        self.assertEqual(["names", "gap"], [line.split("\t")[1] for line in lines])

    def test_the_file_is_private_and_holds_no_text(self):
        gatelog.record(self.root, "names", SECRET)
        path = os.path.join(self.root, gatelog.LOG)
        self.assertEqual(0o600, os.stat(path).st_mode & 0o777)
        self.assertNotIn("approve", self.text())

    def test_it_stops_at_the_size_cap_and_does_not_raise(self):
        with unittest.mock.patch.object(gatelog, "MAX_BYTES", 120):
            for number in range(20):
                gatelog.record(self.root, "names", "command %d" % number)
        self.assertLessEqual(len(self.text().encode("ascii")), 120)
        self.assertGreaterEqual(len(self.text().splitlines()), 2)
        before = self.text()
        with unittest.mock.patch.object(gatelog, "MAX_BYTES", 120):
            gatelog.record(self.root, "names", "one more")
        self.assertEqual(before, self.text())

    def test_a_symbolic_link_in_place_of_the_file_is_not_followed(self):
        target = os.path.join(self.root, "elsewhere")
        with open(target, "w") as handle:
            handle.write("keep\n")
        os.symlink(target, os.path.join(self.root, gatelog.LOG))
        gatelog.record(self.root, "names", SECRET)
        with open(target) as handle:
            self.assertEqual("keep\n", handle.read())

    def test_a_second_hard_link_and_a_directory_are_refused_quietly(self):
        os.mkdir(os.path.join(self.root, gatelog.LOG))
        gatelog.record(self.root, "names", SECRET)  # a directory where the file should be: nothing raised
        shutil.rmtree(os.path.join(self.root, gatelog.LOG))
        other = os.path.join(self.root, "other")
        with open(other, "w") as handle:
            handle.write("x\n")
        os.link(other, os.path.join(self.root, gatelog.LOG))
        gatelog.record(self.root, "names", SECRET)
        with open(other) as handle:
            self.assertEqual("x\n", handle.read())

    def test_a_missing_store_does_not_raise(self):
        gatelog.record(os.path.join(self.root, "not-there"), "names", SECRET)

    def test_a_bad_rule_does_not_raise_and_writes_nothing(self):
        gatelog.record(self.root, "Not A Rule", SECRET)
        self.assertFalse(os.path.exists(os.path.join(self.root, gatelog.LOG)))

    def test_writer_gives_the_function_the_gate_calls(self):
        gatelog.writer(self.root)("names", SECRET)
        self.assertRegex(self.text(), LINE)


class TheGateUsesIt(unittest.TestCase):
    def test_the_command_line_hands_the_gate_the_writer_of_the_store(self):
        import inspect
        from workbench import cli
        source = inspect.getsource(cli._gate_command)
        self.assertIn("gatelog.writer(", source)


if __name__ == "__main__":
    unittest.main()
