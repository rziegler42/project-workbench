"""``wb attach`` at the level ``ask``.

Plan ``2026-11-03-levels-for-recover-pin-approve-attach``, increment C. ``attach`` has no terminal test, so at ``ask`` it reads the
verified level and, when that is not ``ask`` or ``none`` (a project with no rendering record reads ``block``), the owner's own
setting in the guarded store (``docs/decisions/2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest.md``, decision
1, second bullet). ``wb preview attach`` prints what it would write and a digest, and the run takes it as ``--digest``. The fixtures
are those of ``test_attach``: an installed project and a synthetic first-party harness module. The plan's shared test matrix is run
for the cases that apply to a command with no terminal test and no "nothing to change" state: an attached clone is refused."""

import io
import json
import os
import re
import unittest
import unittest.mock

from tests import test_attach as base
from workbench import approve, attach, cli, levellog, levels, settings

DIGEST = re.compile(r"^digest: ([0-9a-f]{32})$", re.M)
KEY = "wb attach"


class Base(base.Base):
    def setUp(self):
        super().setUp()
        self.ready()

    def owner(self, level=None, **more):
        table = {} if level is None else {KEY: level}
        table.update(more)
        self.guarded.write("settings", json.dumps({"version": 2, "checkpoints": {}, "floor": [], "levels": table}).encode())

    def arguments(self):
        argv = [self.place, "--harness", base.support_harness.HARNESS]
        for given in (self.pkg, self.synth):
            argv += ["--package", given]
        return argv

    def go(self, argv):
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(list(argv), out, err, store_root=self.store_root, home=self.home, distribution=self.dist)
        return code, out.getvalue(), err.getvalue()

    def previewed(self):
        code, out, err = self.go(["preview", "attach"] + self.arguments())
        self.assertEqual((0, ""), (code, err), out)
        found = DIGEST.findall(out)
        self.assertEqual(1, len(found), out)
        return found[0], out

    def run_with(self, *extra):
        return self.go(["attach"] + self.arguments() + list(extra))

    def log(self):
        if self.guarded.kind(levellog.LOG) != "file":
            return []
        return self.guarded.read(levellog.LOG).decode("ascii").splitlines()

    def snapshot(self):
        store = {path: data for path, data in self.content(self.store_root).items() if path != "bin" and not path.startswith("bin/")}
        return self.content(), store, self.log()

    def flipped(self, digest):
        return digest[:-1] + ("0" if digest[-1] != "0" else "1")

    def attached(self):
        return os.path.exists(os.path.join(self.place, *base.LOCAL.split("/")))

    def put(self, rel, data):
        full = os.path.join(self.place, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as handle:
            handle.write(data)


class Registry(unittest.TestCase):
    def test_the_key_offers_block_ask_and_none_and_defaults_to_block(self):
        key = levels.registry()[KEY]
        self.assertEqual((("block", "ask", "none"), "block", "wb preview attach"), (key.offers, key.default, key.preview))


class Preview(Base):
    def test_the_preview_says_what_would_be_written_and_prints_one_digest_and_writes_nothing(self):
        before = self.snapshot()
        digest, out = self.previewed()
        self.assertIn("would create 5 files", out)
        self.assertIn(".fixture/settings.local.json", out)
        self.assertIn("would add to .git/info/exclude", out)
        self.assertIn("would record %s" % base.LOCAL, out)
        self.assertTrue(out.rstrip().endswith("preview only: nothing was written"), out)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.attached())

    def test_the_preview_gives_one_digest_twice(self):
        self.assertEqual(self.previewed()[0], self.previewed()[0])

    def test_the_digest_changes_with_what_would_be_written(self):
        first, _ = self.previewed()
        self.put("FIXTURE.md", b"@AGENTS.md\n")  # a file that already holds the planned bytes: created becomes kept
        self.assertNotEqual(first, self.previewed()[0])

    def test_the_preview_takes_no_digest_and_a_missing_harness_is_a_usage_error(self):
        digest, _ = self.previewed()
        code, out, err = self.go(["preview", "attach"] + self.arguments() + ["--digest", digest])
        self.assertEqual(2, code, (out, err))
        code, out, err = self.go(["preview", "attach", self.place])
        self.assertEqual(2, code, (out, err))

    def test_a_clone_that_cannot_be_attached_has_no_digest(self):
        self.assertEqual(0, self.attach()[0])
        code, out, err = self.go(["preview", "attach"] + self.arguments())
        self.assertEqual(1, code, (out, err))
        self.assertIn("already records the harness", err)
        self.assertNotRegex(out, r"^digest: ")


class AtAsk(Base):
    """The owner's own setting is ``ask`` and the project has no rendering record, so the verified level reads ``block``."""

    def setUp(self):
        super().setUp()
        self.owner("ask")

    def test_a_run_with_the_digest_of_the_preview_attaches_asks_nothing_and_logs_the_attempt_and_the_outcome(self):
        digest, _ = self.previewed()
        code, out, err = self.run_with("--digest", digest)
        self.assertEqual(0, code, (out, err))
        self.assertTrue(self.attached())
        attempt, outcome = (line.split("\t") for line in self.log())
        self.assertEqual([KEY, "ask", "digest:" + digest], attempt[3:])
        self.assertEqual(["done", "written"], outcome[3:])

    def test_what_it_writes_is_what_a_run_at_a_terminal_writes(self):
        digest, _ = self.previewed()
        self.assertEqual(0, self.run_with("--digest", digest)[0])
        document = self.planned()
        self.assertEqual("fixture", document["harness"])
        self.assertEqual(sorted(base.HARNESS_PATHS), [item["path"] for item in document["files"]])

    def test_a_run_without_a_digest_is_refused_and_names_the_preview(self):
        before = self.snapshot()
        code, out, err = self.run_with()
        self.assertEqual(1, code, (out, err))
        self.assertIn("preview attach", err)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.attached())

    def test_a_malformed_digest_and_a_digest_given_twice_are_usage_errors(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        code, out, err = self.run_with("--digest", "not-a-digest")
        self.assertEqual(2, code, (out, err))
        self.assertIn("32 lowercase hexadecimal", err)
        self.assertEqual(2, self.run_with("--digest", digest, "--digest", digest)[0])
        self.assertEqual(before, self.snapshot())

    def test_a_stale_digest_is_refused_and_nothing_is_written_or_logged(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        code, out, err = self.run_with("--digest", self.flipped(digest))
        self.assertEqual(1, code, (out, err))
        self.assertIn("preview attach", err)
        self.assertEqual(before, self.snapshot())

    def test_the_digest_of_what_the_project_held_before_it_changed_is_refused(self):
        digest, _ = self.previewed()
        self.put("FIXTURE.md", b"@AGENTS.md\n")  # a planned file that now holds the planned bytes: created becomes kept
        before = self.snapshot()
        code, out, err = self.run_with("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertEqual(before, self.snapshot())

    def test_a_digest_at_a_terminal_is_refused_before_anything_is_read(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        with unittest.mock.patch.object(approve, "is_terminal", lambda stream: True):
            code, out, err = self.run_with("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertIn("without a terminal", err)
        self.assertEqual(before, self.snapshot())

    def test_an_attached_clone_is_refused_with_a_valid_digest_and_logs_nothing(self):
        digest, _ = self.previewed()
        self.assertEqual(0, self.run_with("--digest", digest)[0])
        log, before = self.log(), self.snapshot()
        code, out, err = self.run_with("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertIn("already records the harness", err)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(log, self.log())

    def test_an_attempt_that_cannot_be_written_changes_nothing(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        with unittest.mock.patch.object(levellog, "begin", side_effect=levellog.LogError("the log is full")):
            code, out, err = self.run_with("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.attached())

    def test_an_outcome_that_cannot_be_written_after_the_files_exits_3(self):
        digest, _ = self.previewed()
        with unittest.mock.patch.object(levellog, "finish", side_effect=levellog.OutcomeError("no space")):
            code, out, err = self.run_with("--digest", digest)
        self.assertEqual(3, code, (out, err))
        self.assertTrue(self.attached())

    def test_damaged_owner_settings_read_as_ask_so_the_digest_is_still_required(self):
        self.guarded.write("settings", b"{")
        before = self.snapshot()
        code, out, err = self.run_with()
        self.assertEqual(1, code, (out, err))
        self.assertIn("damaged", err)
        self.assertEqual(before, self.snapshot())

    def test_a_risk_profile_that_sets_the_key_to_ask_requires_the_digest(self):
        self.guarded.write("settings", json.dumps({"version": 3, "checkpoints": {}, "floor": [], "levels": {},
                                                    "profile": "balanced"}).encode())
        before = self.snapshot()
        code, out, err = self.run_with()
        self.assertEqual(1, code, (out, err))
        self.assertIn("preview attach", err)
        self.assertEqual(before, self.snapshot())


class NotAtAsk(Base):
    def test_a_digest_at_none_is_refused_saying_a_digest_needs_ask(self):
        self.owner("none")
        digest = "0" * 32
        before = self.snapshot()
        code, out, err = self.run_with("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertIn("needs the level ask", err)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.attached())

    def test_at_block_attach_goes_on_as_it_always_did_unlogged_and_a_digest_changes_nothing(self):
        self.owner("block")
        code, out, err = self.run_with("--digest", "0" * 32)
        self.assertEqual(0, code, (out, err))
        self.assertTrue(self.attached())
        self.assertEqual([], self.log())

    def test_the_owners_own_none_with_no_digest_goes_on_as_it_always_did_unlogged(self):
        # The project has no rendering record, so the verified level reads block and there is nothing to log under.
        self.owner("none")
        code, out, err = self.run_with()
        self.assertEqual(0, code, (out, err))
        self.assertTrue(self.attached())
        self.assertEqual([], self.log())

    def test_with_no_setting_attach_goes_on_as_it_always_did(self):
        code, out, err = self.run_with()
        self.assertEqual(0, code, (out, err))
        self.assertEqual([], self.log())

    def test_at_a_terminal_no_level_is_read_and_nothing_is_logged(self):
        self.owner("ask")
        with unittest.mock.patch.object(approve, "is_terminal", lambda stream: True):
            code, out, err = self.run_with()
        self.assertEqual(0, code, (out, err))
        self.assertEqual([], self.log())


if __name__ == "__main__":
    unittest.main()
