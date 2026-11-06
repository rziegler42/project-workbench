"""Plan `2026-11-06-mempalace-notes`, increments A to C: the declaration of the notes command (a second command of the `mempalace` module), its keys, and the pin
on its helper. The design is `docs/specs/mempalace-notes.md`."""

import json
import os
import re
import unittest

from tests import support_install
from workbench import declarations, levels

ROOT = support_install.ROOT
PACKAGE = os.path.join(ROOT, "packages", "workbench")
MODULE = os.path.join(PACKAGE, "mempalace")
HELPER = "helper/mempalace-notes"
AGENT_ARGUMENTS = ["wings", "list", "read", "save", "drop", "merge", "review"]
ARGUMENTS = AGENT_ARGUMENTS + ["keep"]


def declaration():
    with open(os.path.join(MODULE, "module.json"), encoding="utf-8") as handle:
        return json.load(handle)


class Declaration(unittest.TestCase):
    def test_the_module_still_verifies_and_ships_both_helpers(self):
        data = declaration()
        self.assertEqual([], list(declarations.load_package(PACKAGE, first_party=True).problems))
        self.assertEqual(["helper/mempalace", HELPER], data["ships"])
        self.assertEqual(["mempalace"], data["helpers"])   # the external program the first command starts; the notes command starts none

    def test_the_notes_command_is_a_second_command_with_its_own_helper_and_the_verbs_built_so_far(self):
        data = declaration()
        self.assertEqual(["mempalace", "mempalace-notes"], list(data["commands"]))
        command = data["commands"]["mempalace-notes"]
        self.assertEqual({"helper": HELPER, "runtime": "python", "kit": 1, "arguments": ARGUMENTS, "owner": ["keep"], "levels": {"keep": ["ask"]},
                          "preview": "review"}, command)

    def test_the_first_command_is_unchanged(self):
        command = declaration()["commands"]["mempalace"]
        self.assertEqual(["status", "search", "mine", "sync", "preview"], command["arguments"])
        self.assertEqual(["mine", "sync"], command["owner"])
        self.assertEqual({"mine": ["ask"], "sync": ["ask"]}, command["levels"])
        self.assertEqual("preview", command["preview"])

    def test_the_keys_are_agent_run_that_offer_block_and_none_and_default_to_none(self):
        loaded = declarations.load_package(PACKAGE, first_party=True)
        checkpoints = [name for module in loaded.modules if module.type == "process" for name in module.checkpoints]
        keys = levels.registry(checkpoints, [levels.command_entry(command) for module in loaded.modules for command in module.commands])
        for name in AGENT_ARGUMENTS:
            key = keys["wb run mempalace-notes " + name]
            self.assertEqual((("block", "none"), "none", True), (key.offers, key.default, key.agent), name)
        keep = keys["wb run mempalace-notes keep"]   # the owner's: block or ask, never none, and it is previewed by `review`
        self.assertEqual((("block", "ask"), "block", False, "wb run mempalace-notes review"), (keep.offers, keep.default, keep.agent, keep.preview))

    def test_the_helper_file_is_where_the_declaration_says(self):
        self.assertTrue(os.path.isfile(os.path.join(MODULE, HELPER)))


class Pin(unittest.TestCase):
    def text(self):
        with open(os.path.join(MODULE, HELPER), encoding="utf-8") as handle:
            return handle.read()

    def test_the_helper_imports_only_the_standard_library_it_needs_and_the_kit(self):
        imported = set(re.findall(r"^(?:import|from) ([a-z_.]+)", self.text(), re.M))
        self.assertEqual({"datetime", "fcntl", "os", "re", "secrets", "stat", "sys", "time", "unicodedata", "wbkit"}, imported)

    def test_the_helper_starts_no_process_opens_no_connection_and_names_no_other_module(self):
        text = self.text()
        for word in ("subprocess", "socket", "urllib", "http", "ssl", "claude", "codex", "safe-git", "code-work", "groundwork",
                     "os.system", "popen", "eval(", "exec(", "__import__", "shell=", "pickle", "marshal"):
            self.assertNotIn(word, text, word)


if __name__ == "__main__":
    unittest.main()
