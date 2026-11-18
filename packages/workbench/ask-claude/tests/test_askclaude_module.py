"""The real `ask-claude` module in `packages/workbench/`: its declaration and its file list, and what the helper
refuses before it starts anything (conformance checklist items 1 to 3 and 7 of `docs/specs/ask-claude.md`).

Plan `2026-11-18-ask-claude-bridge`, increment B. The package tree hash changes with this module, so the shipped
approvals are stale until the owner releases them."""

import json
import os
import re
import unittest

from tests import support_install
from workbench import verify

import support_claude

ROOT = support_install.ROOT
PACKAGE = os.path.join(ROOT, "packages", "workbench")
MODULE = os.path.join(PACKAGE, "ask-claude")
HELPER = "helper/ask-claude"


def declaration():
    with open(os.path.join(MODULE, "module.json"), encoding="utf-8") as handle:
        return json.load(handle)


class Declaration(unittest.TestCase):
    def test_it_verifies_as_a_first_party_module(self):
        result = verify.verify_package(PACKAGE, first_party=True, select=("ask-claude",), harness_required=False)
        self.assertTrue(result.accepted, [str(p) for p in result.problems])
        self.assertIn("ask-claude", [m.name for m in result.modules])

    def test_it_provides_a_model_bridge_requires_nothing_and_ships_only_the_helper(self):
        document = declaration()
        self.assertEqual("module", document["type"])
        self.assertEqual(["model-bridge"], document["provides"])
        self.assertEqual([HELPER], document["ships"])
        for field in ("requires", "writes", "fills", "checks", "helpers", "blocks", "slots", "layout", "ask_reads"):
            self.assertNotIn(field, document)

    def test_the_command_takes_ask_as_its_only_argument(self):
        self.assertEqual(["ask-claude"], list(declaration()["commands"]))
        command = declaration()["commands"]["ask-claude"]
        self.assertEqual(["ask"], command["arguments"])
        self.assertEqual((HELPER, "python", 1), (command["helper"], command["runtime"], command["kit"]))

    def test_every_file_is_the_declaration_or_the_helper(self):
        found = []
        for base, dirs, files in os.walk(MODULE):
            if base == MODULE:
                dirs.remove("tests")  # the module's own tests are not part of what it installs
            for name in files:
                found.append(os.path.relpath(os.path.join(base, name), MODULE))
        self.assertEqual(sorted(["module.json", HELPER]), sorted(found))

    def test_the_package_lists_it(self):
        with open(os.path.join(PACKAGE, "package.json"), encoding="utf-8") as handle:
            self.assertIn("ask-claude", json.load(handle)["modules"])

    def test_the_helper_opens_no_connection_and_names_no_other_vendor_or_module(self):
        with open(os.path.join(MODULE, HELPER), encoding="utf-8") as handle:
            text = handle.read()
        imported = set(re.findall(r"^(?:import|from) ([a-z_.]+)", text, re.M))
        self.assertEqual({"json", "os", "re", "selectors", "signal", "stat", "subprocess", "sys", "time",
                          "unicodedata", "wbkit"}, imported)
        for word in ("socket", "urllib", "http", "ssl", "codex", "gemini", "safe-git", "code-work",
                     "groundwork", "wb run", "ANTHROPIC", "CLAUDE_CODE", "credentials", "keychain"):
            self.assertNotIn(word, text, word)


class Prompt(support_claude.Bridge):
    def test_a_prompt_that_is_missing_empty_or_blank_is_refused(self):
        for prompt in (b"", b"  \n\t\n"):
            self.refused(prompt=prompt, contains="empty")

    def test_a_prompt_that_is_not_utf8_or_is_too_large_is_refused(self):
        self.refused(prompt=b"\xff\xfe text", contains="UTF-8")
        self.refused(prompt=b"x" * (self.helper.MAX_PROMPT + 1), contains="larger than")

    def test_a_prompt_at_the_bound_is_accepted(self):
        document = self.document(prompt=b"x" * self.helper.MAX_PROMPT)
        self.assertTrue(document["ok"])
        self.assertEqual(self.helper.MAX_PROMPT, len(self.calls()[0]["stdin"]))


class Options(support_claude.Bridge):
    def test_a_name_that_is_not_an_option_or_is_given_twice_or_has_no_value(self):
        self.refused("--tools", "Bash", contains="not an option")
        self.refused("-p", contains="not an option")
        self.refused("--model", "a", "--model", "b", contains="given twice")
        self.refused("--model", contains="needs a value")
        self.refused("--effort", "low", "--timeout", contains="needs a value")
        self.refused("extra", contains="not an option")
        self.refused("--MODEL", "a", contains="not an option")

    def test_confine_is_a_flag_with_no_value_given_at_most_once(self):
        self.refused("--confine", "--confine", contains="given twice")
        self.refused("--confine", "yes", contains="not an option")
        self.refused("--confine", "--model", contains="needs a value")
        self.assertTrue(self.document("--confine")["ok"])

    def test_the_model_is_a_name_of_the_contract_and_never_reads_as_an_option(self):
        for bad in ("", "-x", "--confine", "a b", "a/b", "é", "x" * 65, "a;b", ".a", "_a"):
            self.refused("--model", bad, contains="--model")
        for good in ("haiku", "claude-haiku-5-5", "a", "x" * 64, "opus:1m", "a.b_c-d"):
            self.assertTrue(self.document("--model", good)["ok"], good)

    def test_effort_is_one_of_the_three_levels_and_no_other(self):
        for bad in ("", "LOW", "xhigh", "max", "none", "medium ", "1"):
            self.refused("--effort", bad, contains="--effort")
        for good in ("low", "medium", "high"):
            self.assertTrue(self.document("--effort", good)["ok"], good)

    def test_the_timeout_is_a_whole_number_of_seconds_from_1_to_3600(self):
        for bad in ("0", "3601", "-1", "1.5", "1e3", "", "abc", "00001", "+5", " 5"):
            self.refused("--timeout", bad, contains="--timeout")
        for good in ("1", "3600", "600"):
            self.assertTrue(self.document("--timeout", good)["ok"], good)

    def test_server_is_recognized_and_refused_by_a_bridge_to_a_program(self):
        for good in ("ned", "a", "gpu-1_b", "x" * 32, "0"):
            self.refused("--server", good, contains="starts a program")
        for bad in ("", "Ned", "-x", "_x", "a b", "a/b", "x" * 33, "é", "a.b", "a;b"):
            self.refused("--server", bad, contains="--server")
        self.refused("--server", "a", "--server", "b", contains="given twice")
        self.refused("--server", contains="needs a value")
        self.refused("--confine", "--server", "ned", contains="starts a program")

    def test_a_path_that_starts_with_a_dash_is_refused_so_a_flag_is_never_read_as_a_path(self):
        for name in ("--confine", "-x", "--server"):
            with open(os.path.join(self.root, name), "w") as handle:
                handle.write("{}")
        os.makedirs(os.path.join(self.root, "-dir"))
        for option, value in (("--schema", "--confine"), ("--schema", "-x"), ("--root", "-dir"),
                              ("--root", "--confine"), ("--schema", "--server")):
            self.refused(option, value, contains="start with a dash")
        self.control(result=support_claude.result('{"a": 1}'))
        self.assertTrue(self.document("--schema", "./-x")["ok"])
        self.assertTrue(self.document("--root", "./-dir")["ok"])


class Paths(support_claude.Bridge):
    def test_a_root_or_schema_that_breaks_a_path_rule_is_refused_and_nothing_runs(self):
        os.makedirs(os.path.join(self.root, "real", "sub"))
        os.symlink(os.path.join(self.root, "real"), os.path.join(self.root, "link"))
        outside_file = os.path.join(self.base, "outside.json")
        with open(outside_file, "w") as handle:
            handle.write("{}")
        for value, contains in ((os.path.join(self.base), "outside the project"), ("../x", "parent"),
                                ("link", "link"), ("link/sub", "link"), ("missing", "does not exist"),
                                ("docs/plan.md", "directory"), (".git", ".git or .workbench"),
                                (".workbench", ".git or .workbench"), ("a\0b", "usable path"), ("", "usable path")):
            self.refused("--root", value, contains=contains)
        for value, contains in ((outside_file, "outside the project"), ("../x.json", "parent"),
                                ("missing.json", "does not exist"), ("docs", "regular file"),
                                ("docs/plan.md", "JSON object")):
            self.refused("--schema", value, contains=contains)

    def test_a_schema_must_be_one_json_object_of_at_most_65536_bytes(self):
        for name, data in (("array.json", b"[1]"), ("text.json", b"nope"), ("big.json", b" " * 65537)):
            with open(os.path.join(self.root, name), "wb") as handle:
                handle.write(data)
            self.refused("--schema", name, contains="--schema")
        with open(os.path.join(self.root, "edge.json"), "wb") as handle:
            handle.write(b'{"a": 1}' + b" " * (65536 - 8))
        self.control(result=support_claude.result('{"a": 1}'))
        self.assertTrue(self.document("--schema", "edge.json")["ok"])

    def test_a_relative_path_is_read_against_the_project_root_and_the_program_starts_in_the_root_given(self):
        os.makedirs(os.path.join(self.root, "sub", "deep"))
        self.assertTrue(self.document("--root", "sub", cwd=os.path.join(self.root, "sub", "deep"))["ok"])
        self.assertEqual(os.path.join(self.root, "sub"), os.path.realpath(self.calls()[0]["cwd"]))
        self.assertTrue(self.document(cwd=os.path.join(self.root, "sub"))["ok"])
        self.assertEqual(self.root, os.path.realpath(self.calls()[1]["cwd"]))


if __name__ == "__main__":
    unittest.main()
