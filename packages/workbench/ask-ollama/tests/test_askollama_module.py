"""The `ask-ollama` module as a package member: its declaration, what it ships, what its helper may import and what it must not
contain (checklist item 1 of `docs/specs/model-bridge.md` and `docs/specs/ask-ollama.md`). Plan
`2026-11-01-ask-ollama-bridge`, increment C."""

import json
import os
import re
import unittest

from tests import support_install

ROOT = support_install.ROOT
PACKAGE = os.path.join(ROOT, "packages", "workbench")
MODULE = os.path.join(PACKAGE, "ask-ollama")
HELPER = "helper/ask-ollama"


def declaration():
    with open(os.path.join(MODULE, "module.json"), encoding="utf-8") as handle:
        return json.load(handle)


def helper_text():
    with open(os.path.join(MODULE, HELPER), encoding="utf-8") as handle:
        return handle.read()


class Declaration(unittest.TestCase):
    def test_it_is_a_bridge_with_one_helper_and_one_command(self):
        fields = declaration()
        self.assertEqual(("ask-ollama", "module", ["model-bridge"], [HELPER]),
                         (fields["name"], fields["type"], fields["provides"], fields["ships"]))
        for absent in ("requires", "fills", "writes", "slots", "checks"):
            self.assertNotIn(absent, fields)
        self.assertEqual({"ask-ollama": {"helper": HELPER, "runtime": "python", "kit": 1, "arguments": ["ask", "check"]}},
                         fields["commands"])

    def test_it_asks_before_the_agent_reads_the_endpoint_file(self):
        self.assertEqual(["~/.config/project-workbench/endpoints.json"], declaration()["ask_reads"])

    def test_the_package_lists_it_after_the_other_bridge(self):
        with open(os.path.join(PACKAGE, "package.json"), encoding="utf-8") as handle:
            modules = json.load(handle)["modules"]
        self.assertIn("ask-ollama", modules)
        self.assertEqual(modules.index("ask-codex") + 1, modules.index("ask-ollama"))

    def test_every_file_is_the_declaration_or_the_helper(self):
        found = []
        for base, dirs, files in os.walk(MODULE):
            if base == MODULE:
                dirs.remove("tests")  # the module's own tests are not part of what it installs
            for name in files:
                found.append(os.path.relpath(os.path.join(base, name), MODULE))
        self.assertEqual(sorted(["module.json", HELPER]), sorted(found))

    def test_the_helper_is_not_executable_and_names_its_interpreter(self):
        self.assertEqual(0, os.stat(os.path.join(MODULE, HELPER)).st_mode & 0o111)
        self.assertTrue(helper_text().startswith("#!/usr/bin/env python3\n"))


class Helper(unittest.TestCase):
    def test_it_imports_the_standard_library_and_the_kit_only(self):
        imported = set(re.findall(r"^(?:import|from) ([a-z_.]+)", helper_text(), re.M))
        self.assertEqual({"contextlib", "http.client", "ipaddress", "json", "math", "os", "re", "signal", "socket", "ssl",
                          "stat", "sys", "threading", "time", "unicodedata", "wbkit"}, imported)

    def test_it_names_no_other_vendor_or_module_and_runs_no_program(self):
        text = helper_text()
        for word in ("claude", "gemini", "codex", "safe-git", "code-work", "groundwork", "wb run", "subprocess", "os.system",
                     "Popen", "urllib", "requests"):
            self.assertNotIn(word, text, word)

    def test_it_reads_no_environment_variable_and_no_proxy(self):
        text = helper_text()
        for word in ("os.environ", "getenv", "environb", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY", "proxy"):
            self.assertNotIn(word, text, word)

    def test_it_trusts_the_libraries_own_locations_and_not_the_default_context(self):
        text = helper_text()
        self.assertNotIn("create_default_context", text)
        self.assertIn("openssl_cafile", text)
        self.assertIn("openssl_capath", text)

    def test_it_opens_nothing_for_writing_and_makes_no_directory(self):
        text = helper_text()
        for word in ("O_WRONLY", "O_RDWR", "O_CREAT", "O_APPEND", "O_TRUNC", "mkdir", "makedirs", "rename", "unlink", "rmtree",
                     "tempfile", "chmod", "\"w\"", "'w'", "\"wb\"", "\"a\""):
            self.assertNotIn(word, text, word)

    def test_it_has_no_redirect_handling_and_follows_none(self):
        text = helper_text()
        for word in ("HTTPRedirectHandler", "Location", "urlopen", "redirect_request", "max_redirects"):
            self.assertNotIn(word, text, word)

    def test_the_contract_numbers_are_those_of_the_spec(self):
        text = helper_text()
        self.assertIn("CONTRACT = 2", text)
        self.assertIn('USER_AGENT = "ask-ollama/1"', text)
        self.assertIn('CHAT_PATH = "/api/chat"', text)


if __name__ == "__main__":
    unittest.main()
