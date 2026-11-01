"""The options of `ask` (checklist items 2, 3 and 7 of `docs/specs/model-bridge.md`, "ask: the options" of
`docs/specs/ask-ollama.md`). Plan `2026-11-01-ask-ollama-bridge`, increment C. A refusal is one `refused:` line made before
anything is sent."""

import io
import json
import os
import unittest
import unittest.mock

import support_ollama


class Options(support_ollama.Bridge):
    def test_a_name_that_is_not_an_option_or_is_given_twice_or_has_no_value_is_refused(self):
        self.refused("--sandbox", "danger-full-access", contains="not an option")
        self.refused("-m", "x", contains="not an option")
        self.refused("--model", "a", "--model", "b", contains="given twice")
        self.refused("--model", contains="needs a value")
        self.refused("--effort", "low", "--timeout", contains="needs a value")
        self.refused("extra", contains="not an option")
        self.refused("--MODEL", "a", contains="not an option")
        self.refused("--model=gpt-5", contains="not an option")
        self.refused("--confine=1", contains="not an option")
        self.refused("--server=ned", contains="not an option")
        self.refused("--", "--confine", contains="not an option")

    def test_a_model_outside_the_contract_rule_or_the_record_rule_is_refused(self):
        for bad in ("", "a b", "a;b", "$(x)", "a/b", "-x", "--effort", "m\n", "x" * 65, "é", "a=b", "a..b", "a...b"):
            self.refused("--model", bad, contains="--model")

    def test_a_model_at_the_limits_is_accepted_and_sent_as_given(self):
        for good in ("gpt-5", "a", "o3.mini:high_1", "x" * 64, "llama3:8b", "0"):
            self.assertTrue(self.document("--model", good)["ok"], good)
            self.assertEqual(good, json.loads(self.fake.requests[-1]["body"])["model"])

    def test_an_effort_outside_the_three_levels_is_refused(self):
        for bad in ("", "LOW", "max", "minimal", "low ", "none"):
            self.refused("--effort", bad, contains="--effort")

    def test_an_effort_is_sent_as_think_and_without_it_think_is_left_out(self):
        self.assertTrue(self.document()["ok"])
        self.assertNotIn("think", json.loads(self.fake.requests[-1]["body"]))
        for level in ("low", "medium", "high"):
            self.assertTrue(self.document("--effort", level)["ok"])
            self.assertEqual(level, json.loads(self.fake.requests[-1]["body"])["think"])

    def test_a_timeout_out_of_range_or_not_a_plain_number_is_refused(self):
        for bad in ("0", "3601", "-1", "1.5", "1e2", "abc", "", "+5", "٣", "00001", "10000", " 5"):
            self.refused("--timeout", bad, contains="--timeout")

    def test_a_timeout_at_the_limits_is_accepted(self):
        for good in ("1", "3600", "0600"):
            self.assertTrue(self.document("--timeout", good)["ok"], good)

    def test_a_server_name_outside_its_form_is_refused(self):
        for bad in ("", "Ned", "-x", "_x", "a b", "a/b", "x" * 33, "é", "a.b", "a;b"):
            self.refused("--server", bad, contains="--server")

    def test_confine_is_a_flag_with_no_value_given_at_most_once(self):
        self.refused("--confine", "--confine", contains="given twice")
        self.refused("--confine", "yes", contains="not an option")
        self.refused("--confine", "--model", contains="needs a value")
        self.assertTrue(self.document("--confine")["ok"])
        self.assertTrue(self.document("--model", "gpt-5", "--confine")["ok"])
        self.assertTrue(self.document("--confine", "--model", "gpt-5")["ok"])

    def test_confine_changes_nothing_in_the_request_because_there_is_no_tool_to_switch_off(self):
        self.assertTrue(self.document()["ok"])
        plain = self.fake.requests[-1]
        self.assertTrue(self.document("--confine")["ok"])
        confined = self.fake.requests[-1]
        self.assertEqual((plain["method"], plain["path"], plain["headers"], plain["body"]),
                         (confined["method"], confined["path"], confined["headers"], confined["body"]))

    def test_an_option_given_in_any_order_works(self):
        self.assertTrue(self.document("--timeout", "30", "--model", "gpt-5", "--effort", "low", "--confine")["ok"])

    def test_the_first_argument_must_be_ask_or_check(self):
        out, err = io.StringIO(), io.StringIO()
        for argv in ([], ["review"], ["--model", "x"], ["ASK"], ["embed"], ["Check"]):
            self.assertEqual(1, self.helper.main(argv, io.BytesIO(b"x"), out, err, self.root))
        self.assertEqual("", out.getvalue())
        self.assertEqual(6, err.getvalue().count("refused: usage: ask-ollama ask"))
        self.assertEqual([], self.fake.requests)

    def test_a_directory_that_is_not_a_project_is_refused(self):
        self.refused(cwd=self.base, contains="not inside a workbench project")

    def test_a_working_directory_that_is_gone_is_a_refusal_and_not_a_traceback(self):
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch("os.getcwd", side_effect=FileNotFoundError(2, "No such file or directory")):
            code = self.helper.main(["ask"], io.BytesIO(b"hello"), out, err)
        self.assertEqual((1, ""), (code, out.getvalue()))
        self.assertTrue(err.getvalue().startswith("refused: ") and err.getvalue().count("\n") == 1, err.getvalue())
        self.assertNotIn(self.base, err.getvalue())


class Prompt(support_ollama.Bridge):
    def test_a_prompt_that_is_missing_empty_or_blank_is_refused(self):
        for prompt in (b"", b"  \n\t\n"):
            self.refused(prompt=prompt, contains="empty")

    def test_a_prompt_that_is_not_utf8_or_is_too_large_is_refused(self):
        self.refused(prompt=b"\xff\xfe text", contains="UTF-8")
        self.refused(prompt=b"x" * (self.helper.MAX_PROMPT + 1), contains="larger than")

    def test_a_prompt_at_the_bound_is_accepted_and_sent_whole(self):
        self.assertTrue(self.document(prompt=b"x" * self.helper.MAX_PROMPT)["ok"])
        body = json.loads(self.fake.requests[-1]["body"])
        self.assertEqual(self.helper.MAX_PROMPT, len(body["messages"][0]["content"]))

    def test_the_largest_valid_request_fits_the_request_bound(self):
        schema = {"type": "object", "description": "€" * 20000}  # 60,000 bytes in the file, 120,000 written out again
        with open(os.path.join(self.root, "docs", "big.json"), "w", encoding="utf-8") as handle:
            json.dump(schema, handle, ensure_ascii=False)
        prompt = ("\x01" * self.helper.MAX_PROMPT).encode()
        self.assertTrue(self.helper.MAX_REQUEST >= 6 * self.helper.MAX_PROMPT + 6 * self.helper.MAX_SCHEMA + 70000)
        self.fake.reply(support_ollama.chat('{"a": 1}'))
        self.assertTrue(self.document("--schema", "docs/big.json", prompt=prompt)["ok"])
        self.assertLessEqual(len(self.fake.requests[-1]["body"]), self.helper.MAX_REQUEST)

    def test_the_prompt_is_the_content_of_one_user_message_and_nothing_of_it_is_elsewhere(self):
        prompt = "Review `docs/plan.md`; $(rm -rf /) --dangerously-bypass é \"q\" \\ \n"
        self.assertTrue(self.document(prompt=prompt.encode())["ok"])
        request = self.fake.requests[-1]
        body = json.loads(request["body"])
        self.assertEqual([{"role": "user", "content": prompt}], body["messages"])
        self.assertNotIn("rm -rf", request["path"] + "".join(k + v for k, v in request["headers"]))
        self.assertNotIn("rm -rf", json.dumps({k: v for k, v in body.items() if k != "messages"}))


class Paths(support_ollama.Bridge):
    def setUp(self):
        super().setUp()
        os.makedirs(os.path.join(self.root, "src", "deep"))
        with open(os.path.join(self.root, "schema.json"), "w") as handle:
            handle.write('{"type": "object"}')
        os.symlink(os.path.join(self.root, "src"), os.path.join(self.root, "linked"))
        os.symlink(os.path.join(self.root, "schema.json"), os.path.join(self.root, "schema-link.json"))
        os.makedirs(os.path.join(self.base, "elsewhere"))
        with open(os.path.join(self.base, "elsewhere", "schema.json"), "w") as handle:
            handle.write("{}")
        os.symlink(os.path.join(self.base, "elsewhere"), os.path.join(self.root, "away"))
        self.fake.reply(support_ollama.chat('{"a": 1}'))

    def test_a_root_or_schema_outside_the_project_is_refused(self):
        self.refused("--root", self.base, contains="outside the project")
        self.refused("--root", "../elsewhere", contains="parent directory")
        self.refused("--schema", os.path.join(self.base, "elsewhere", "schema.json"), contains="outside the project")
        self.refused("--schema", "../elsewhere/schema.json", contains="parent directory")

    def test_a_path_with_a_link_in_it_is_refused(self):
        self.refused("--root", "linked", contains="link")
        self.refused("--schema", "schema-link.json", contains="link")
        self.refused("--root", "away", contains="link")
        self.refused("--schema", "away/schema.json", contains="link")

    def test_a_path_that_does_not_exist_or_is_the_wrong_kind_is_refused(self):
        self.refused("--root", "nope", contains="does not exist")
        self.refused("--root", "schema.json", contains="not a directory")
        self.refused("--schema", "nope.json", contains="does not exist")
        self.refused("--schema", "src", contains="not a regular file")

    def test_a_root_inside_git_or_the_workbench_directory_is_refused(self):
        self.refused("--root", ".git", contains="--root")
        self.refused("--root", ".workbench", contains="--root")

    def test_a_schema_that_is_not_one_json_object_or_is_too_large_is_refused(self):
        deep = '{"a":' * 40 + "1" + "}" * 40
        for text in ("[]", "1", "null", '{"a": ', '{"a": 1, "a": 2}', "NaN", "", '{"a": 1e999}', '{"a": -1e999}', deep,
                     '{"a": "\\ud800"}'):
            with open(os.path.join(self.root, "bad.json"), "w") as handle:
                handle.write(text)
            self.refused("--schema", "bad.json", contains="--schema")
        with open(os.path.join(self.root, "bad.json"), "w") as handle:
            handle.write('{"a": "' + "x" * 65536 + '"}')
        self.refused("--schema", "bad.json", contains="larger than")

    def test_a_path_that_starts_with_a_dash_is_refused_so_a_flag_is_never_read_as_a_path(self):
        for name in ("--confine", "-x", "--server"):
            with open(os.path.join(self.root, name), "w") as handle:
                handle.write("{}")
        os.makedirs(os.path.join(self.root, "-dir"))
        for option, value in (("--schema", "--confine"), ("--schema", "-x"), ("--root", "-dir"), ("--root", "--confine"),
                              ("--schema", "--server")):
            self.refused(option, value, contains="start with a dash")
        self.assertTrue(self.document("--schema", "./-x")["ok"])
        self.assertTrue(self.document("--root", "./-dir")["ok"])
        self.assertTrue(self.document("--schema", os.path.join(self.root, "-x"))["ok"])

    def test_a_relative_path_is_read_against_the_project_root_whatever_the_working_directory(self):
        self.assertTrue(self.document("--schema", "schema.json", "--root", "src/deep", cwd=os.path.join(self.root, "src"))["ok"])

    def test_a_root_is_validated_and_then_ignored(self):
        self.assertTrue(self.document()["ok"])
        plain = self.fake.requests[-1]
        self.assertTrue(self.document("--root", "src/deep")["ok"])
        self.assertEqual((plain["path"], plain["headers"], plain["body"]),
                         (self.fake.requests[-1]["path"], self.fake.requests[-1]["headers"], self.fake.requests[-1]["body"]))

    def test_a_schema_is_sent_unchanged_as_the_format_and_a_fraction_survives(self):
        schema = {"type": "object", "properties": {"n": {"type": "number", "minimum": 0.5, "multipleOf": 0.25}},
                  "required": ["n"]}
        with open(os.path.join(self.root, "docs", "shape.json"), "w") as handle:
            json.dump(schema, handle)
        self.assertTrue(self.document("--schema", "docs/shape.json")["ok"])
        self.assertEqual(schema, json.loads(self.fake.requests[-1]["body"])["format"])

    def test_without_a_schema_no_format_is_sent(self):
        self.assertTrue(self.document()["ok"])
        self.assertNotIn("format", json.loads(self.fake.requests[-1]["body"]))


if __name__ == "__main__":
    unittest.main()
