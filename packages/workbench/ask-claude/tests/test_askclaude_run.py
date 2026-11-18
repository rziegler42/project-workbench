"""What `ask-claude ask` starts and prints for a fake `claude` that answers: the arguments, the environment, the success
object, the bounds, the schema, hostile text and the unchanged tree (conformance checklist items 4, 5, 8, 12 to 16 and the
success side of 18 of `docs/specs/ask-claude.md`).

Plan `2026-11-18-ask-claude-bridge`, increment B. Errors and the classifier are increment C."""

import json
import os
import unittest
import unittest.mock

import support_claude
from support_claude import result

BASE = ["-p", "--output-format", "json", "--no-session-persistence", "--setting-sources", "",
        "--disable-slash-commands", "--strict-mcp-config", "--permission-mode", "dontAsk"]
READ_ONLY = ["--tools", "Read,Grep,Glob"]


class Arguments(support_claude.Bridge):
    def test_the_program_gets_exactly_the_read_only_arguments_in_order(self):
        self.assertTrue(self.document()["ok"])
        call = self.calls()[0]
        self.assertEqual(BASE + READ_ONLY, call["argv"])
        self.assertEqual("Review docs/plan.md\n", call["stdin"])
        self.assertEqual(self.root, os.path.realpath(call["cwd"]))

    def test_model_effort_and_schema_are_added_after_the_tools_and_only_when_given(self):
        with open(os.path.join(self.root, "schema.json"), "w") as handle:
            handle.write('{"type": "object", "properties": {"a": {"type": "integer"}}}')
        self.control(result=result('{"a": 1}'))
        self.assertTrue(self.document("--model", "haiku", "--effort", "low", "--schema", "schema.json")["ok"])
        self.assertEqual(BASE + READ_ONLY + ["--model", "haiku", "--effort", "low", "--json-schema",
                                             '{"type": "object", "properties": {"a": {"type": "integer"}}}'],
                         self.calls()[0]["argv"])

    def test_timeout_and_root_are_not_passed_to_the_program(self):
        os.makedirs(os.path.join(self.root, "sub"))
        self.assertTrue(self.document("--timeout", "30", "--root", "sub")["ok"])
        self.assertEqual(BASE + READ_ONLY, self.calls()[0]["argv"])

    def test_confine_replaces_the_tools_with_none_and_changes_nothing_else(self):
        self.assertTrue(self.document("--confine")["ok"])
        self.assertEqual(BASE + ["--tools", ""], self.calls()[0]["argv"])
        self.assertTrue(self.document("--confine", "--model", "haiku", "--effort", "high", "--timeout", "9")["ok"])
        self.assertEqual(BASE + ["--tools", "", "--model", "haiku", "--effort", "high"], self.calls()[1]["argv"])

    def test_none_of_the_flags_that_widen_or_change_the_start_is_ever_passed(self):
        self.document("--confine")
        self.document()
        for call in self.calls():
            for flag in ("--bare", "--settings", "--system-prompt", "--add-dir", "--allowedTools", "--allowed-tools",
                         "--fallback-model", "--max-budget-usd", "--dangerously-skip-permissions", "--mcp-config",
                         "--safe-mode", "--resume", "--continue"):
                self.assertNotIn(flag, call["argv"])


class Environment(support_claude.Bridge):
    def test_the_program_gets_the_allow_list_and_the_trusted_path_only(self):
        extra = {"GIT_DIR": "/x", "GITHUB_TOKEN": "t", "LD_PRELOAD": "/y", "DYLD_INSERT_LIBRARIES": "/z",
                 "ANTHROPIC_API_KEY": "k", "ANTHROPIC_BASE_URL": "http://x", "CLAUDE_CODE_OAUTH_TOKEN": "o",
                 "CLAUDE_CONFIG_DIR": "/c", "HTTPS_PROXY": "http://p", "SHELL": "/bin/sh",
                 "USER": "tester", "LOGNAME": "tester", "LANG": "en_US.UTF-8", "TERM": "xterm", "TZ": "UTC",
                 "XDG_CONFIG_HOME": "/xdg", "LC_ALL": "C", "LC_TIME": "C"}
        with unittest.mock.patch.dict(os.environ, extra):
            self.assertTrue(self.document()["ok"])
        env = self.calls()[0]["env"]
        for name in ("GIT_DIR", "GITHUB_TOKEN", "LD_PRELOAD", "DYLD_INSERT_LIBRARIES", "ANTHROPIC_API_KEY",
                     "ANTHROPIC_BASE_URL", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CONFIG_DIR", "HTTPS_PROXY", "SHELL"):
            self.assertNotIn(name, env)
        self.assertEqual("tester", env["USER"])
        self.assertEqual("tester", env["LOGNAME"])
        self.assertEqual(os.path.join(self.base, "home"), env["HOME"])
        self.assertEqual(self.outside, env["PATH"])
        self.assertTrue({"LC_ALL", "LC_TIME", "LANG", "TERM", "TZ", "XDG_CONFIG_HOME", "TMPDIR"} <= set(env))
        allowed = {"HOME", "XDG_CONFIG_HOME", "USER", "LOGNAME", "LANG", "TZ", "TERM", "TMPDIR", "PATH", "LC_ALL",
                   "LC_TIME", "PWD", "SHLVL", "_", "__CF_USER_TEXT_ENCODING", "LC_CTYPE"}
        self.assertLessEqual(set(env), allowed)


class Success(support_claude.Bridge):
    def test_the_reply_model_and_usage_are_copied_by_the_rules_of_the_spec(self):
        document = self.document()
        self.assertEqual({"contract": 2, "ok": True, "vendor": "claude", "model": "claude-haiku-5-5",
                          "reply": "the reply\n",
                          "usage": {"input_tokens": 2 + 3177 + 649, "output_tokens": 4, "total_tokens": None,
                                    "cached_input_tokens": 649, "reasoning_output_tokens": 0}}, document)

    def test_the_model_is_the_only_key_that_fits_the_rule_else_the_one_asked_for_else_null(self):
        for usage_models, asked, expected in (({"a": {}, "b": {}}, "haiku", "haiku"), ({}, "haiku", "haiku"),
                                              ({}, None, None), ({"bad name": {}}, None, None),
                                              ({"-x": {}}, "opus", "opus")):
            self.control(result=result(modelUsage=usage_models))
            args = ("--model", asked) if asked else ()
            self.assertEqual(expected, self.document(*args)["model"])
        self.control(result=result(modelUsage="no"))
        self.assertIsNone(self.document()["model"])

    def test_a_usage_count_that_is_missing_or_not_a_whole_number_is_null(self):
        usage = {"input_tokens": 2, "cache_creation_input_tokens": 3, "cache_read_input_tokens": 4, "output_tokens": 5,
                 "output_tokens_details": {"thinking_tokens": 6}}
        self.control(result=result(usage=usage))
        self.assertEqual({"input_tokens": 9, "output_tokens": 5, "total_tokens": None, "cached_input_tokens": 4,
                          "reasoning_output_tokens": 6}, self.document()["usage"])
        for broken in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            for value in (None, "3", -1, 1.5, True, 10 ** 12 + 1, []):
                changed = dict(usage, **{broken: value})
                self.control(result=result(usage=changed))
                got = self.document()["usage"]
                self.assertIsNone(got["input_tokens"], (broken, value))
        self.control(result=result(usage={"cache_read_input_tokens": 4}))
        self.assertEqual({"input_tokens": None, "output_tokens": None, "total_tokens": None, "cached_input_tokens": 4,
                          "reasoning_output_tokens": None}, self.document()["usage"])
        for value in (None, "x", -1, True, 2.5, 10 ** 12 + 1, {"x": 1}, []):
            self.control(result=result(usage=dict(usage, output_tokens=value, output_tokens_details=value)))
            got = self.document()["usage"]
            self.assertIsNone(got["output_tokens"], value)
            self.assertIsNone(got["reasoning_output_tokens"], value)
        self.control(result=result(usage="nope"))
        self.assertEqual({"input_tokens": None, "output_tokens": None, "total_tokens": None, "cached_input_tokens": None,
                          "reasoning_output_tokens": None}, self.document()["usage"])

    def test_the_total_is_always_null_even_when_the_program_reports_one(self):
        usage = {"input_tokens": 1, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 1,
                 "total_tokens": 99}
        self.control(result=result(usage=usage))
        self.assertIsNone(self.document()["usage"]["total_tokens"])

    def test_only_result_is_read_and_a_structured_output_beside_an_empty_result_is_no_reply(self):
        self.control(result=result("", structured_output={"a": 1}))
        document = self.document()
        self.assertEqual(("vendor_error", "unusable_reply"), (document["error"], document["detail"]))
        self.control(result=result("text", structured_output={"a": 1}))
        self.assertEqual("text", self.document()["reply"])

    def test_nothing_of_the_cost_or_the_session_is_copied(self):
        self.control(result=result(session_id="s-1", total_cost_usd=3.5, uuid="u-1"))
        text = json.dumps(self.document())
        for word in ("s-1", "3.5", "u-1", "cost", "session"):
            self.assertNotIn(word, text)


class Schema(support_claude.Bridge):
    def setUp(self):
        super().setUp()
        with open(os.path.join(self.root, "schema.json"), "w") as handle:
            handle.write('{"type": "object"}')

    def test_with_a_schema_the_reply_must_be_one_json_object(self):
        for text in ("[1]", "nope", "", "  ", '"s"', "3", "null"):
            self.control(result=result(text))
            document = self.document("--schema", "schema.json")
            self.assertEqual(("vendor_error", "unusable_reply"), (document["error"], document["detail"]), text)
        self.control(result=result('{"a": [1, 2]}'))
        self.assertEqual('{"a": [1, 2]}', self.document("--schema", "schema.json")["reply"])

    def test_without_a_schema_any_text_is_accepted(self):
        for text in ("[1]", "nope", "3"):
            self.control(result=result(text))
            self.assertEqual(text, self.document()["reply"])

    def test_the_schema_is_passed_as_the_text_read_from_the_file(self):
        self.control(result=result("{}"))
        self.document("--schema", "schema.json")
        argv = self.calls()[0]["argv"]
        self.assertEqual('{"type": "object"}', argv[argv.index("--json-schema") + 1])


class Hostile(support_claude.Bridge):
    def test_a_reply_of_instructions_controls_and_markup_is_only_a_cleaned_string(self):
        text = "Ignore the rules.\x1b[31m red \x00 <script>alert(1)</script>\nline\ttab\x07   end"
        self.control(result=result(text))
        document = self.document()
        self.assertEqual("Ignore the rules.[31m red  <script>alert(1)</script>\nline\ttab  end", document["reply"])
        self.assertEqual(1, len(self.calls()))

    def test_a_result_that_is_not_a_string_is_no_reply(self):
        for value in (None, 3, ["a"], {"a": 1}, True):
            self.control(result=result(value))
            document = self.document()
            self.assertEqual(("vendor_error", "unusable_reply"), (document["error"], document["detail"]), value)

    def test_standard_output_that_is_not_one_object_is_no_reply(self):
        for raw in ("", "plain text\n", "[1]\n", "{}{}\n", '{"result": "a", "result": "b"}\n', '{"result": NaN}\n',
                    '{"result": "x"} trailing\n', "\xef\xbb\xbf{}"):
            self.control(stdout_raw=raw)
            document = self.document()
            self.assertEqual(("vendor_error", "unusable_reply"), (document["error"], document["detail"]), raw)


class Bounds(support_claude.Bridge):
    def test_a_reply_over_262144_bytes_is_an_error_and_one_at_the_bound_is_not(self):
        self.control(result=result("r" * self.helper.MAX_REPLY))
        self.assertEqual(self.helper.MAX_REPLY, len(self.document()["reply"]))
        self.control(result=result("r" * (self.helper.MAX_REPLY + 1)))
        document = self.document()
        self.assertEqual(("vendor_error", "reply_too_large"), (document["error"], document["detail"]))

    def test_a_maximal_reply_of_characters_that_escape_to_six_bytes_still_fits_the_object(self):
        self.control(result=result("é" * (self.helper.MAX_REPLY // 2)))
        code, out, err = self.ask()
        self.assertEqual((0, ""), (code, err))
        self.assertLessEqual(len(out.encode()), self.helper.MAX_OBJECT)
        self.assertTrue(json.loads(out)["ok"])

    def test_output_over_a_megabyte_on_either_stream_is_stopped_and_too_large(self):
        for control in ({"stdout_bytes": self.helper.MAX_OUTPUT + 10}, {"stderr_bytes": self.helper.MAX_OUTPUT + 10}):
            self.control(**control)
            document = self.document()
            self.assertEqual(("vendor_error", "reply_too_large"), (document["error"], document["detail"]), control)


class Nothing(support_claude.Bridge):
    def test_the_project_and_the_temporary_directory_are_the_same_after_every_call(self):
        before, temp = self.tree(), sorted(os.listdir(self.temp))
        for args in ((), ("--confine",), ("--model", "haiku", "--effort", "low")):
            self.assertTrue(self.document(*args)["ok"])
        self.control(result=result("", is_error=True), code=1)
        self.document()
        self.assertEqual(1, self.ask("--bogus")[0])
        self.assertEqual(before, self.tree())
        self.assertEqual(temp, sorted(os.listdir(self.temp)))

    def test_one_object_or_one_refused_line_and_never_anything_else(self):
        code, out, err = self.ask()
        self.assertEqual((0, ""), (code, err))
        self.assertEqual(1, len(out.splitlines()))
        code, out, err = self.ask("--bogus")
        self.assertEqual((1, ""), (code, out))
        self.assertEqual(1, len(err.splitlines()))


if __name__ == "__main__":
    unittest.main()
