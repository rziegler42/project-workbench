"""``wb acknowledge`` and ``wb recover`` at the level ``ask``.

Plan ``2026-11-03-levels-for-recover-pin-approve-attach``, increment A. A run without a terminal at ``ask`` takes the digest that
``wb preview acknowledge`` or ``wb preview recover`` printed (``docs/decisions/2026-11-03-installer-commands-read-their-level-and-
take-an-ask-digest.md``, decisions 2 and 3, and its note of 2026-11-04). The fixtures are those of ``test_ack_recover_levels``.
The shared matrix of the plan is ``Matrix``: every digest case, for each of the two commands."""

import hashlib
import io
import os
import re
import unittest
import unittest.mock

from tests.test_ack_recover_levels import FILE, FIRST, Base, NoInput
from workbench import approve, levellog, levelrun, levels, projectfs, unfinished


class Matrix(object):
    """What every command that gains ``ask`` is tested for (completion criterion 1 and the plan's "Shared test matrix"). A
    subclass names its command (``VERB``), its key as the level log writes it (``LOGKEY``), and the four states below."""

    VERB = LOGKEY = None
    DIGEST = re.compile(r"^digest: ([0-9a-f]{32})$", re.M)
    NOTHING = "nothing to"       # what the run says when it has nothing to change
    PROJECT_CHECK = True         # the command acts on one project, which must be the one the level was read for

    def target(self):
        """The arguments after the command word, for the preview and for the run (a subclass whose command takes others)."""
        return [self.real]

    def dirty(self):
        """Put the project in a state where the command has something to do."""
        raise NotImplementedError

    def dirtier(self):
        """Change that state, so that what the preview shows is different."""
        raise NotImplementedError

    def clean(self):
        """True when the command has nothing to do here."""
        raise NotImplementedError

    def previewed(self, verb=None):
        code, out, err = self.go(["preview", verb or self.VERB] + self.target())
        self.assertEqual((0, ""), (code, err), out)
        found = self.DIGEST.findall(out)
        self.assertEqual(1, len(found), out)
        return found[0], out

    def flipped(self, digest):
        return digest[:-1] + ("0" if digest[-1] != "0" else "1")

    def ask(self, *extra):
        return self.go([self.VERB] + self.target() + list(extra))

    def entries(self):
        return [entry.split("\t") for entry in self.log()]

    # -- what the registry offers

    def test_the_key_offers_ask_and_none_and_defaults_to_block(self):
        key = levels.registry(checkpoints=(FIRST, "acknowledge-second-tier"))[self.KEY]
        self.assertEqual(("block", "ask", "none"), key.offers)
        self.assertEqual("block", key.default)

    # -- the preview

    def test_the_preview_prints_a_32_character_digest_and_writes_nothing(self):
        before = self.snapshot()
        digest, out = self.previewed()
        self.assertIn("preview only: nothing was written", out)
        self.assertIn("the digest above is the examination's own", out)
        self.assertEqual(before, self.snapshot())

    def test_the_preview_gives_one_digest_twice_and_another_when_what_it_shows_changes(self):
        first, _ = self.previewed()
        self.assertEqual(first, self.previewed()[0])
        self.dirtier()
        self.assertNotEqual(first, self.previewed()[0])

    def test_the_preview_takes_no_digest(self):
        digest, _ = self.previewed()
        code, out, err = self.go(["preview", self.VERB] + self.target() + ["--digest", digest])
        self.assertEqual(2, code, (out, err))

    # -- the run

    def test_a_run_with_the_digest_of_the_preview_asks_nothing_and_logs_the_attempt_and_the_outcome(self):
        digest, _ = self.previewed()
        code, out, err = self.ask("--digest", digest)
        self.assertEqual((0, ""), (code, err), out)
        self.assertIn("nothing is asked", out)
        self.assertTrue(self.clean())
        attempt, outcome = self.entries()
        self.assertEqual([self.LOGKEY, "ask"], attempt[3:5])
        self.assertEqual("digest:" + digest, attempt[5])
        self.assertEqual(["done", "written"], outcome[3:])

    def test_a_run_without_a_digest_is_refused_and_names_the_preview(self):
        before = self.snapshot()
        code, out, err = self.ask()
        self.assertEqual(1, code, (out, err))
        self.assertIn("preview %s" % self.VERB, err)
        self.assertEqual(before, self.snapshot())

    def test_a_malformed_digest_is_a_usage_error_and_nothing_changes(self):
        before = self.snapshot()
        code, out, err = self.ask("--digest", "not-a-digest")
        self.assertEqual(2, code, (out, err))
        self.assertIn("32 lowercase hexadecimal", err)
        self.assertEqual(before, self.snapshot())

    def test_a_digest_given_twice_is_a_usage_error_and_nothing_changes(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        code, out, err = self.ask("--digest", digest, "--digest", digest)
        self.assertEqual(2, code, (out, err))
        self.assertEqual(before, self.snapshot())

    def test_a_stale_digest_is_refused_and_nothing_changes(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        code, out, err = self.ask("--digest", self.flipped(digest))
        self.assertEqual(1, code, (out, err))
        self.assertIn("preview %s" % self.VERB, err)
        self.assertEqual(before, self.snapshot())

    def test_the_digest_of_what_the_project_held_before_it_changed_is_refused(self):
        digest, _ = self.previewed()
        self.dirtier()
        before = self.snapshot()
        code, out, err = self.ask("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertEqual(before, self.snapshot())

    def test_a_digest_at_a_terminal_is_refused_before_anything_is_read(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        with unittest.mock.patch.object(approve, "is_terminal", lambda stream: True):
            code, out, err = self.ask("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertIn("without a terminal", err)
        self.assertEqual(before, self.snapshot())

    def test_a_table_edited_after_attach_reads_block_even_with_the_right_digest(self):
        digest, _ = self.previewed()
        self.table(**{self.KEY: "ask", "wb adopt": "none"})
        self.refused([self.VERB] + self.target() + ["--digest", digest])

    def test_a_plan_for_another_project_than_the_level_was_read_for_is_refused_at_ask_too(self):
        if not self.PROJECT_CHECK:
            self.skipTest("the command is not for one project")
        digest, _ = self.previewed()
        before = self.snapshot()
        elsewhere = levelrun.Route(False, "ask", "0" * 64, self.real)
        with unittest.mock.patch.object(levelrun, "route_ask", lambda *a, **k: elsewhere):
            code, out, err = self.ask("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertRegex(err, "not the project|another project")
        self.assertEqual(before, self.snapshot())

    def test_an_attempt_that_cannot_be_written_changes_nothing(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        with unittest.mock.patch.object(levellog, "begin", side_effect=levellog.LogError("the log is full")):
            code, out, err = self.ask("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertEqual(before, self.snapshot())

    def test_an_outcome_that_cannot_be_written_after_the_change_exits_3(self):
        digest, _ = self.previewed()
        with unittest.mock.patch.object(levellog, "finish", side_effect=levellog.OutcomeError("no space")):
            code, out, err = self.ask("--digest", digest)
        self.assertEqual(3, code, (out, err))
        self.assertTrue(self.clean())

    # -- nothing to change

    def test_a_valid_digest_with_nothing_to_change_says_so_and_writes_and_logs_nothing(self):
        self.assertEqual(0, self.ask("--digest", self.previewed()[0])[0])
        self.assertTrue(self.clean())
        digest, out = self.previewed()
        log, before = self.log(), self.snapshot()
        code, out, err = self.ask("--digest", digest)
        self.assertEqual((0, ""), (code, err), out)
        self.assertIn(self.NOTHING, out)
        self.assertEqual(log, self.log())
        self.assertEqual(before, self.snapshot())

    def test_a_stale_digest_with_nothing_to_change_is_refused(self):
        old, _ = self.previewed()
        self.assertEqual(0, self.ask("--digest", old)[0])
        before = self.snapshot()
        code, out, err = self.ask("--digest", old)
        self.assertEqual(1, code, (out, err))
        self.assertIn("preview %s" % self.VERB, err)
        self.assertEqual(before, self.snapshot())


class DigestElsewhere(object):
    """A digest where the level is not ``ask``: ``none`` takes none, and ``block`` leaves the command to the owner."""

    DIGEST = "0" * 32

    def target(self):
        return [self.real]

    def test_a_digest_at_none_is_refused_saying_a_digest_needs_ask(self):
        self.attach_at("none")
        self.dirty()
        before = self.snapshot()
        code, out, err = self.go([self.VERB] + self.target() + ["--digest", self.DIGEST])
        self.assertEqual(1, code, (out, err))
        self.assertIn("needs the level ask", err)
        self.assertEqual(before, self.snapshot())

    def test_a_digest_at_block_is_refused_as_owner_run(self):
        self.attach_at("block")
        self.dirty()
        self.refused([self.VERB] + self.target() + ["--digest", self.DIGEST])


class AcknowledgeFixture(object):
    VERB, LOGKEY, KEY = "acknowledge", FIRST, FIRST

    def dirty(self):
        self.put(FILE, "# Docs\nedited by someone else\n")

    def dirtier(self):
        self.put(FILE, "# Docs\nedited again by someone else\n")

    def clean(self):
        return hashlib.sha256(self.read(FILE)).hexdigest() == self.baselines()[FILE]


class AcknowledgeAtAsk(AcknowledgeFixture, Matrix, Base):
    def setUp(self):
        super().setUp()
        self.attach_at("ask")
        self.dirty()

    def test_the_preview_lists_the_difference_the_run_accepts(self):
        digest, out = self.previewed()
        self.assertIn(FILE, out)
        self.assertIn("differences from what was last acknowledged: 1", out)


class AcknowledgeDigestElsewhere(DigestElsewhere, AcknowledgeFixture, Base):
    pass


class RecoverFixture(object):
    VERB, LOGKEY, KEY = "recover", "wb recover", "wb recover"

    def dirty(self):
        os.makedirs(os.path.join(self.real, "scratch"), exist_ok=True)
        marker = unfinished.build("upgrade", self.project_id, "1", [("zz/new.txt", "create", None, "1" * 64)],
                                  dirs=["scratch"], store=[("projects/%s/zz" % self.project_id, None, "1" * 64)])
        full = os.path.join(self.real, *projectfs.MARKER.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as handle:
            handle.write(marker)

    def dirtier(self):
        # Another directory the plan recorded, so the steps that would clear the marker are different.
        os.makedirs(os.path.join(self.real, "other"), exist_ok=True)
        marker = unfinished.build("upgrade", self.project_id, "1", [("zz/new.txt", "create", None, "1" * 64)],
                                  dirs=["scratch", "other"], store=[("projects/%s/zz" % self.project_id, None, "1" * 64)])
        with open(os.path.join(self.real, *projectfs.MARKER.split("/")), "wb") as handle:
            handle.write(marker)

    def clean(self):
        return not os.path.exists(os.path.join(self.real, *projectfs.MARKER.split("/")))


class RecoverAtAsk(RecoverFixture, Matrix, Base):
    def setUp(self):
        super().setUp()
        self.attach_at("ask")
        self.dirty()

    def test_the_preview_lists_what_the_run_removes(self):
        digest, out = self.previewed()
        self.assertIn("this removes:", out)
        self.assertIn("scratch", out)

    def test_a_marker_that_names_another_project_is_refused_at_ask_too(self):
        digest, _ = self.previewed()
        marker = unfinished.build("upgrade", "0" * 64, "1", [("zz/new.txt", "create", None, "1" * 64)], dirs=["scratch"],
                                  store=[("projects/%s/zz" % ("0" * 64), None, "1" * 64)])
        with open(os.path.join(self.real, *projectfs.MARKER.split("/")), "wb") as handle:
            handle.write(marker)
        before = self.snapshot()
        code, out, err = self.ask("--digest", digest)
        self.assertEqual(1, code, (out, err))
        self.assertEqual(before, self.snapshot())

    def test_a_marker_in_a_state_that_is_not_safe_has_no_preview_digest(self):
        with open(os.path.join(self.real, "zz-new.txt"), "w") as handle:
            handle.write("x")
        os.makedirs(os.path.join(self.real, "zz"), exist_ok=True)
        with open(os.path.join(self.real, "zz", "new.txt"), "w") as handle:
            handle.write("written")
        code, out, err = self.go(["preview", "recover", self.real])
        self.assertEqual(1, code, (out, err))
        self.assertNotRegex(out, r"^digest: ", "no digest is printed for a state the run would refuse")


class RecoverDigestElsewhere(DigestElsewhere, RecoverFixture, Base):
    pass


if __name__ == "__main__":
    unittest.main()
