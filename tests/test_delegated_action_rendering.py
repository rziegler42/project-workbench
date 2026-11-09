"""What the level `delegated` renders for the key of an action that a module describes, and what the settings and the doctor say of it.
Increment C of the cutover plan of 2026-11-08; the decision is `2026-11-03-delegated-for-an-action-key-and-named-risk-profiles`.

At `delegated` the key renders the same `ask` rule as at `ask`, so that the owner's prompt exists whether or not the owner's own rules ask,
and it reads `delegated` only while the rendering record, the table and the harness files agree, as `ask` does. The plan approval keeps
its present rendering (a `deny` at `delegated`: its gate is another command). A key that does not offer `delegated` reads `block`.

Everything here is synthetic: a module named `tool` whose command `tool` describes the action `check`. The installer knows no module."""

import io
import json
import os
import unittest

from tests import support_harness, support_project, test_attach, test_rendering
from workbench import cli, doctor, levels, rendering, settings

KEY = "wb run tool check"
COMMANDS = {"tool": {"helper": support_project.HELPER_PATH, "arguments": ["check", "report", "wipe", "describe"],
                     "owner": ["wipe"], "describes": ["check"], "levels": {"check": ["delegated"]}}}
ASKS = ("Bash(wb run tool check)", "Bash(wb run tool check *)")


class Plan(unittest.TestCase):
    """`rendering.plan` over a table that names the keys of the actions it may relax."""

    def table(self, level, key=KEY, actions=(KEY,)):
        return rendering.Table({key: level}, actions=actions)

    def test_an_action_key_at_delegated_renders_what_it_renders_at_ask(self):
        delegated, asked = rendering.plan(self.table("delegated")), rendering.plan(self.table("ask"))
        self.assertEqual("ask", delegated.keys[KEY])
        self.assertEqual(asked.ask, delegated.ask)
        self.assertEqual(asked.open, delegated.open)
        self.assertEqual([], delegated.deny)
        self.assertTrue(delegated.ask)

    def test_a_key_that_the_table_does_not_name_as_an_action_is_denied_at_delegated(self):
        self.assertEqual("deny", rendering.plan(self.table("delegated", actions=())).keys[KEY])
        self.assertEqual("deny", rendering.plan(rendering.Table({KEY: "delegated"})).keys[KEY])
        self.assertEqual("deny", rendering.plan({KEY: "delegated"}).keys[KEY])

    def test_the_plan_approval_at_delegated_is_still_denied(self):
        got = rendering.plan(self.table("delegated", key="approve-plan"))
        self.assertEqual("deny", got.keys["approve-plan"])
        self.assertEqual([], got.ask)
        self.assertTrue(got.deny)

    def test_a_harness_that_cannot_render_the_gate_denies_it(self):
        got = rendering.plan(self.table("delegated"), gated=False)
        self.assertEqual("deny", got.keys[KEY])
        self.assertEqual([], got.ask)

    def test_the_other_levels_of_an_action_key_render_as_before(self):
        self.assertEqual("deny", rendering.plan(self.table("block")).keys[KEY])
        self.assertEqual("none", rendering.plan(self.table("none")).keys[KEY])
        self.assertEqual("ask", rendering.plan(self.table("ask")).keys[KEY])


class Attached(test_rendering.Rendered):
    MODULES = {"h": (test_attach.HARNESS, {}), "tool": support_project.tool(COMMANDS)}

    def commands(self):
        from workbench import approvalcmd
        _, _, found = approvalcmd.installed_modules(self.place)
        return [levels.command_entry(c) for item in found for c in item.module.commands]

    def levels_now(self):
        """The effective table with the installed module's commands, as attach builds it."""
        return rendering.table_of(self.guarded, (), self.commands())

    def run_doctor(self):
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["doctor", self.place], out, err, store_root=self.store_root, home=self.home, distribution=self.dist)
        return code, out.getvalue(), err.getvalue()


class Rendering(Attached):
    def test_the_key_is_offered_delegated_and_is_in_the_table_at_it(self):
        self.attached(wb_run_tool_check="delegated")
        self.assertEqual("delegated", self.levels_now()[KEY])
        self.assertIn(levels.DELEGATED, levels.registry((), self.commands())[KEY].offers)

    def test_the_permissions_file_gets_the_ask_rule_and_no_deny(self):
        self.attached(wb_run_tool_check="delegated")
        permissions = self.permissions()
        for rule in ASKS:
            self.assertIn(rule, permissions["ask"])
            self.assertNotIn(rule, permissions["deny"])
        self.assertEqual("ask", self.record()["keys"][KEY])

    def test_each_ask_rule_is_written_once(self):
        self.attached(wb_run_tool_check="delegated")
        for rule in ASKS:
            self.assertEqual(1, self.permissions()["ask"].count(rule))

    def test_the_effective_level_reads_delegated_while_the_record_and_the_files_agree(self):
        self.attached(wb_run_tool_check="delegated")
        self.assertEqual("delegated", self.level(KEY))

    def test_without_the_record_it_reads_block(self):
        self.attached(wb_run_tool_check="delegated")
        os.unlink(os.path.join(self.store_root, *(rendering.RECORD % self.project_id).split("/")))
        self.assertEqual("block", self.level(KEY))

    def test_a_damaged_record_reads_block(self):
        self.attached(wb_run_tool_check="delegated")
        for data in (b"{", b"[]", b"null", b'{"format": 2}', b"\xff"):
            with self.subTest(data=data):
                self.guarded.write(rendering.RECORD % self.project_id, data)
                self.assertEqual("block", self.level(KEY))

    def test_a_record_that_says_another_rule_reads_block(self):
        self.attached(wb_run_tool_check="delegated")
        for rule in ("deny", "none", "unruled"):
            with self.subTest(rule=rule):
                record = self.record()
                record["keys"][KEY] = rule
                self.guarded.write(rendering.RECORD % self.project_id, json.dumps(record).encode())
                self.assertEqual("block", self.level(KEY))

    def test_a_record_with_the_key_deleted_reads_block(self):
        self.attached(wb_run_tool_check="delegated")
        record = self.record()
        del record["keys"][KEY]
        self.guarded.write(rendering.RECORD % self.project_id, json.dumps(record).encode())
        self.assertEqual("block", self.level(KEY))

    def test_a_permissions_file_edited_after_attach_reads_block(self):
        self.attached(wb_run_tool_check="delegated")
        path = os.path.join(self.place, *test_rendering.SETTINGS_FILE.split("/"))
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\n")
        self.assertEqual("block", self.level(KEY))

    def test_a_table_that_changed_since_attach_reads_block(self):
        self.attached(wb_run_tool_check="delegated")
        self.table(wb_run_tool_check="delegated", wb_pin="ask")
        self.assertEqual("block", self.level(KEY))

    def test_a_harness_without_the_gate_denies_it_and_reads_block(self):
        self.attached(wb_run_tool_check="delegated")
        self.assertEqual("delegated", self.level(KEY))
        record = self.record()
        record["gate"] = False
        self.guarded.write(rendering.RECORD % self.project_id, json.dumps(record).encode())
        self.assertEqual("block", self.level(KEY))

    def test_a_plain_dict_table_reads_delegated_only_for_the_plan_approval(self):
        self.attached(wb_run_tool_check="delegated")
        self.assertEqual("block", self.level(KEY, table={KEY: "delegated"}))
        self.assertEqual("block", self.level(KEY, table=rendering.Table({KEY: "delegated"})))
        self.assertEqual("block", self.level(KEY, table=rendering.Table({KEY: "delegated"}, actions=("wb run tool other",))))
        self.assertEqual("delegated", self.level("approve-plan", table={"approve-plan": "delegated"}))

    def test_a_key_that_does_not_offer_delegated_reads_block(self):
        self.attached(wb_run_tool_report="delegated", wb_run_tool_wipe="delegated")
        for key in ("wb run tool report", "wb run tool wipe"):
            with self.subTest(key=key):
                self.assertNotEqual("delegated", self.levels_now().get(key))
                self.assertEqual("block", self.level(key))

    def test_a_project_that_does_not_set_the_key_is_unchanged(self):
        self.attached()
        self.assertNotIn(KEY, self.levels_now())
        self.assertNotIn(KEY, self.record()["keys"])
        for rule in ASKS:
            self.assertNotIn(rule, self.permissions().get("ask", []))

class Readers(Attached):
    def effective(self):
        return settings.effective(settings.load(self.guarded), (), (), self.commands())

    def test_the_settings_read_delegated_for_a_key_that_offers_it(self):
        self.attached(wb_run_tool_check="delegated")
        self.assertEqual("delegated", self.effective().levels[KEY])

    def test_the_settings_read_block_for_a_key_that_does_not_offer_it(self):
        self.attached(wb_run_tool_report="delegated")
        self.assertEqual("block", self.effective().levels["wb run tool report"])

    def test_the_doctor_says_that_the_approval_depends_on_a_hook_it_cannot_see(self):
        self.attached(wb_run_tool_check="delegated")
        code, out, err = self.run_doctor()
        self.assertEqual(0, code, out + err)
        lines = [line for line in out.splitlines() if KEY in line and line.startswith("note:")]
        self.assertEqual(1, len(lines), out)
        self.assertIn("delegated", lines[0])
        self.assertIn("hook", lines[0])
        self.assertIn("prompt", lines[0])
        self.assertIn("doctor found no problems", out)

    def said_nothing_at(self, level):
        self.attached(wb_run_tool_check=level)
        code, out, err = self.run_doctor()
        self.assertEqual(0, code, out + err)
        self.assertFalse([line for line in out.splitlines() if KEY in line and "hook" in line], out)

    def test_the_doctor_says_nothing_of_it_when_the_key_is_at_none(self):
        self.said_nothing_at("none")

    def test_the_doctor_says_nothing_of_it_when_the_key_is_at_block(self):
        self.said_nothing_at("block")

class Findings(unittest.TestCase):
    def keys(self, commands=None):
        return levels.registry((), commands or [("tool", ("wipe",), ("check", "report", "wipe"), (("check", ("delegated",)),))])

    def test_one_note_for_each_action_key_at_delegated(self):
        got = doctor.delegated_findings(self.keys(), {KEY: "delegated", "wb run tool report": "none"})
        self.assertEqual(1, len(got))
        self.assertEqual("note", got[0].severity)
        self.assertTrue(got[0].line.startswith("note: "))
        self.assertIn(KEY, got[0].line)

    def test_nothing_for_any_other_level_or_key(self):
        for level in ("block", "none", "ask"):
            self.assertEqual([], doctor.delegated_findings(self.keys(), {KEY: level}), level)
        self.assertEqual([], doctor.delegated_findings(self.keys(), {"approve-plan": "delegated"}))
        self.assertIn("wb check", self.keys())
        self.assertEqual([], doctor.delegated_findings(self.keys(), {"wb check": "delegated"}))
        self.assertEqual([], doctor.delegated_findings(self.keys(), {"nowhere": "delegated"}))
        self.assertEqual([], doctor.delegated_findings(self.keys(), {}))


if __name__ == "__main__":
    unittest.main()
