"""``wb pin`` and ``wb approve`` at the level ``ask``.

Plan ``2026-11-03-levels-for-recover-pin-approve-attach``, increment B. A run without a terminal at ``ask`` takes the digest that
``wb preview pin`` or ``wb preview approve`` printed (``docs/decisions/2026-11-03-installer-commands-read-their-level-and-take-an-
ask-digest.md`` and its note of 2026-11-04). The fixtures are those of ``test_approve_pin_levels``; the shared matrix of the plan is
``Matrix`` of ``test_ack_recover_ask``, run for each of the two commands."""

import os
import unittest
import unittest.mock

from tests.test_ack_recover_ask import DigestElsewhere, Matrix
from tests.test_approve_pin_levels import HELPER, VERIFY_PACKAGE, Base
from workbench import approvals, pins


class PinFixture(object):
    VERB, LOGKEY, KEY = "pin", "wb pin", "wb pin"
    NOTHING = "already pinned"

    def helper(self):
        return os.path.join(self.real, *HELPER.split("/"))

    def target(self, name="extra", *more):
        return [self.project_id, name, self.helper(), "--root", self.real] + list(more)

    def dirty(self):
        pass  # the helper exists and holds no pin yet

    def dirtier(self):
        self.put(HELPER, "#!/bin/sh\necho changed\n")

    def clean(self):
        pin = pins.load(self.guarded, self.project_id).get("extra")
        with open(self.helper(), "rb") as handle:
            return pin is not None and pin.sha256 == pins.hash_bytes(handle.read())


class PinAtAsk(PinFixture, Matrix, Base):
    def setUp(self):
        super().setUp()
        self.attach_at("ask")
        self.dirty()

    def test_the_preview_shows_what_the_run_pins_and_what_it_replaces(self):
        digest, out = self.previewed()
        self.assertIn("pin helper extra for project %s" % self.project_id, out)
        self.assertIn("path in the project: %s" % HELPER, out)
        self.assertIn("sha256:", out)
        self.assertNotIn("this REPLACES", out)
        self.assertEqual(0, self.ask("--digest", digest)[0])
        self.dirtier()
        _, again = self.previewed()
        self.assertIn("this REPLACES the pin %s" % HELPER, again)

    def test_the_kit_the_name_and_the_replaced_pin_are_in_the_digest(self):
        plain, _ = self.previewed()
        code, out, err = self.go(["preview", "pin"] + self.target("extra", "--kit", "1"))
        self.assertEqual((0, ""), (code, err), out)
        with_kit = self.DIGEST.findall(out)[0]
        code, out, err = self.go(["preview", "pin"] + self.target("other"))
        self.assertEqual((0, ""), (code, err), out)
        other_name = self.DIGEST.findall(out)[0]
        self.assertEqual(3, len({plain, with_kit, other_name}))

    def test_the_pin_a_run_at_ask_writes_says_ask(self):
        digest, _ = self.previewed()
        self.assertEqual(0, self.ask("--digest", digest)[0])
        pin = pins.lookup(self.guarded, self.project_id, "extra")
        self.assertEqual(("ask", self.who.text), (pin.via, pin.pinned_by))

    def test_a_run_with_the_digest_of_another_name_or_kit_is_refused(self):
        digest, _ = self.previewed()
        before = self.snapshot()
        code, out, err = self.ask("--digest", digest, "--kit", "1")
        self.assertEqual(1, code, (out, err))
        self.assertEqual(before, self.snapshot())


class PinDigestElsewhere(PinFixture, DigestElsewhere, Base):
    pass


class ApproveFixture(object):
    VERB, LOGKEY, KEY = "approve", "wb approve", "wb approve"
    NOTHING = "already approved"
    PROJECT_CHECK = False  # an approval is machine-wide

    def target(self, *more):
        return [self.package_dir] + list(more)

    def dirty(self):
        pass  # the package exists and holds no approval yet

    def dirtier(self):
        with open(os.path.join(self.package_dir, "sample-notes", "files", "docs", "notes.md"), "a") as handle:
            handle.write("another line\n")

    def clean(self):
        result = VERIFY_PACKAGE(self.package_dir, harness_required=False)
        info = result.packages[0]
        return approvals.check(self.guarded, "package", info.name, info.declaration_hash, info.tree_hash).approved


class ApproveAtAsk(ApproveFixture, Matrix, Base):
    def setUp(self):
        super().setUp()
        self.attach_at("ask")
        self.dirty()

    def test_a_stale_digest_with_nothing_to_change_is_refused(self):
        # The digest binds the request and not whether a record is already on file, so after the approval the same digest still
        # describes the same request: the run says it is already approved and changes and logs nothing. A request that changed
        # has another digest (`test_the_digest_of_what_the_project_held_before_it_changed_is_refused`).
        digest, _ = self.previewed()
        self.assertEqual(0, self.ask("--digest", digest)[0])
        log, before = self.log(), self.snapshot()
        code, out, err = self.ask("--digest", digest)
        self.assertEqual((0, ""), (code, err), out)
        self.assertIn("already approved", out)
        self.assertEqual(log, self.log())
        self.assertEqual(before, self.snapshot())
        code, out, err = self.ask("--digest", self.flipped(digest))
        self.assertEqual(1, code, (out, err))
        self.assertIn("preview approve", err)

    def test_the_preview_shows_the_request_and_records_no_approval(self):
        before = self.snapshot()
        digest, out = self.previewed()
        self.assertIn("sample", out)
        self.assertFalse(self.clean())
        self.assertEqual(before, self.snapshot())

    def test_a_module_approval_has_another_digest_than_the_package_approval(self):
        package, _ = self.previewed()
        code, out, err = self.go(["preview", "approve", self.package_dir, "--module", "sample-notes"])
        self.assertEqual((0, ""), (code, err), out)
        module = self.DIGEST.findall(out)[0]
        self.assertNotEqual(package, module)
        before = self.snapshot()
        code, out, err = self.ask("--digest", package, "--module", "sample-notes")
        self.assertEqual(1, code, (out, err))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(0, self.ask("--digest", module, "--module", "sample-notes")[0])

    def test_the_records_a_run_at_ask_writes_say_ask(self):
        digest, _ = self.previewed()
        self.assertEqual(0, self.ask("--digest", digest)[0])
        result = VERIFY_PACKAGE(self.package_dir, harness_required=False)
        info = result.packages[0]
        record = approvals.check(self.guarded, "package", info.name, info.declaration_hash, info.tree_hash).record
        self.assertEqual(("ask", self.who.text), (record.via, record.approver))
        for module in result.modules:
            found = approvals.check(self.guarded, "module", "%s/%s" % (info.name, module.name), module.declaration_hash,
                                    module.tree_hash).record
            self.assertEqual("ask", found.via, module.name)

    def test_a_download_has_no_preview_so_source_is_refused_at_ask_and_by_the_preview(self):
        before = self.snapshot()
        code, out, err = self.go(["approve", "--source", "file:///nonexistent", "--digest", "0" * 32])
        self.assertEqual(1, code, (out, err))
        self.assertIn("package directory", err)
        self.assertEqual(before, self.snapshot())
        code, out, err = self.go(["preview", "approve", "--source", "file:///nonexistent"])
        self.assertEqual(2, code, (out, err))
        self.assertEqual(before, self.snapshot())

    def test_a_package_that_does_not_verify_has_no_preview_digest(self):
        os.unlink(os.path.join(self.package_dir, "package.json"))
        code, out, err = self.go(["preview", "approve", self.package_dir])
        self.assertEqual(1, code, (out, err))
        self.assertNotRegex(out, r"^digest: ")


class ApproveDigestElsewhere(ApproveFixture, DigestElsewhere, Base):
    pass


if __name__ == "__main__":
    unittest.main()
