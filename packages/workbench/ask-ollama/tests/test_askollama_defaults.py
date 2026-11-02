"""The defaults of a model section (`effort` or `thinking`, and `output_limit`) and the options `--thinking` and `--max-output`
(decision `2026-11-02-model-section-defaults-and-the-embedding-name`; checklist items 17 and 18 of `docs/specs/ask-ollama.md`).
Plan `2026-11-02-bridge-model-configurations`, increment F-C. Every refusal is made before a request and quotes no value; a
default is applied only when the call passes nothing, and an argument replaces it."""

import json
import unittest

import support_ollama
from support_ollama import chat

CHAT = {"kind": "chat", "context": 8192}
EMBEDDING = {"kind": "embedding", "context": 8192}


class Base(support_ollama.Bridge):
    def section(self, **fields):
        """A file with the one chat model `m`, whose section holds `fields`, and make it the default."""
        self.endpoints(ned=self.record(models={"m": dict(CHAT, **fields)}, default_model="m"))

    def body(self):
        return json.loads(self.fake.requests[-1]["body"])

    def sent(self, *args, prompt=b"Review docs/plan.md\n"):
        self.assertTrue(self.document(*args, prompt=prompt)["ok"])
        return self.body()


class Validator(Base):
    def bad_file(self, models, contains):
        self.endpoints(ned=self.record(models=models, default_model=None))
        err = self.refused(command="check", contains=contains)
        self.refused(contains=contains)
        self.assertEqual([], self.fake.requests)
        return err

    def not_quoted(self, value, err):
        """No part of a hostile value is in the refusal (a value of four characters or fewer is skipped: a word of the rule
        may hold it)."""
        shown = value if isinstance(value, str) else json.dumps(value)
        if len(shown) > 4:
            self.assertNotIn(shown, err)

    def good_file(self, section):
        self.endpoints(ned=self.record(models={"m": dict(CHAT, **section)}, default_model=None))
        self.assertEqual(0, self.ask(command="check")[0], section)

    def test_each_default_at_its_limits_is_read(self):
        for section in ({"effort": "low"}, {"effort": "medium"}, {"effort": "high"}, {"thinking": True}, {"thinking": False},
                        {"output_limit": 1}, {"output_limit": 10000000}, {"effort": "high", "output_limit": 6000},
                        {"thinking": False, "output_limit": 3000}):
            self.good_file(section)

    def test_an_effort_outside_the_three_words_is_refused_without_the_value(self):
        for value in ("LOW", "max", "", "low ", "minimal", 5, None, True, ["low"], {"a": 1}):
            err = self.bad_file({"m": dict(CHAT, effort=value)}, "effort")
            self.not_quoted(value, err)

    def test_a_thinking_that_is_not_a_boolean_is_refused(self):
        for value in ("true", "on", "false", "SECRET-VALUE", 1, 0, None, [True], {"a": "SECRET-VALUE"}, "low"):
            self.not_quoted(value, self.bad_file({"m": dict(CHAT, thinking=value)}, "thinking"))

    def test_an_output_limit_that_is_not_a_whole_number_in_range_is_refused(self):
        for value in (0, -1, 10000001, "5", "SECRET-VALUE", True, False, None, [5], {"a": 1}, 10 ** 30):
            self.not_quoted(value, self.bad_file({"m": dict(CHAT, output_limit=value)}, "output_limit"))

    def test_a_float_for_an_output_limit_is_not_strict_json(self):
        document = json.dumps({"format": 2, "endpoints": {"ned": self.record(models={"m": dict(CHAT, output_limit=5)},
                                                                              default_model=None)}})
        self.write_endpoint_file(document.replace('"output_limit": 5', '"output_limit": 5.5').encode())
        self.refused(command="check", contains="strict JSON")

    def test_a_section_may_hold_effort_or_thinking_and_never_both(self):
        for effort in ("low", "high"):
            for thinking in (True, False):
                self.bad_file({"m": dict(CHAT, effort=effort, thinking=thinking)}, "both effort and thinking")
        self.bad_file({"m": dict(CHAT, effort="low", thinking=False, output_limit=5)}, "both effort and thinking")

    def test_an_embedding_section_holds_none_of_the_defaults(self):
        for fields in ({"effort": "low"}, {"thinking": True}, {"output_limit": 5}):
            self.bad_file({"m": dict(EMBEDDING, **fields)}, "chat")
        self.endpoints(ned=self.record(models={"e": dict(EMBEDDING)}, default_model=None, embedding_model="e"))
        self.assertEqual(0, self.ask(command="check")[0])

    def test_an_unknown_field_is_still_refused(self):
        self.bad_file({"m": dict(CHAT, temperature=2)}, "not allowed")
        self.bad_file({"m": dict(CHAT, think="low")}, "not allowed")
        self.bad_file({"m": dict(CHAT, num_predict=5)}, "not allowed")


class Request(Base):
    def test_a_section_with_no_default_sends_what_it_sent_before(self):
        self.section()
        self.assertEqual({"model": "m", "messages": [{"role": "user", "content": "Review docs/plan.md\n"}], "stream": False,
                          "truncate": False, "options": {"num_ctx": 8192}}, self.sent())

    def test_the_default_effort_is_sent_as_think_with_the_word(self):
        for word in ("low", "medium", "high"):
            self.section(effort=word)
            body = self.sent()
            self.assertEqual(word, body["think"])
            self.assertEqual({"num_ctx": 8192}, body["options"])

    def test_the_default_thinking_is_sent_as_a_boolean_and_false_is_sent(self):
        self.section(thinking=True)
        self.assertIs(True, self.sent()["think"])
        self.section(thinking=False)
        body = self.sent()
        self.assertIn("think", body)
        self.assertIs(False, body["think"])

    def test_the_output_limit_is_sent_as_num_predict_inside_options(self):
        self.section(output_limit=6000)
        body = self.sent()
        self.assertEqual({"num_ctx": 8192, "num_predict": 6000}, body["options"])
        self.assertNotIn("num_predict", body)
        self.assertNotIn("think", body)

    def test_the_defaults_together_and_the_schema_keep_their_places(self):
        self.section(effort="low", output_limit=10000)
        with open(self.root + "/docs/schema.json", "w") as handle:
            handle.write('{"type": "object"}')
        self.fake.reply(chat('{"a": 1}'))
        body = self.sent("--schema", "docs/schema.json")
        self.assertEqual({"model", "messages", "stream", "truncate", "options", "format", "think"}, set(body))
        self.assertEqual({"num_ctx": 8192, "num_predict": 10000}, body["options"])

    def test_a_reply_stopped_at_the_cap_is_reply_cut(self):
        self.section(output_limit=100)
        self.fake.reply(chat("half an answer", done_reason="length"))
        self.failed(error="vendor_error", detail="reply_cut")

    def test_each_model_has_its_own_defaults(self):
        models = {"a": dict(CHAT, effort="low", output_limit=100), "b": dict(CHAT, thinking=False), "c": dict(CHAT)}
        self.endpoints(ned=self.record(models=models, default_model="a"))
        self.assertEqual(("low", {"num_ctx": 8192, "num_predict": 100}),
                         (self.sent()["think"], self.body()["options"]))
        body = self.sent("--model", "b")
        self.assertEqual((False, {"num_ctx": 8192}), (body["think"], body["options"]))
        body = self.sent("--model", "c")
        self.assertEqual(({"num_ctx": 8192}, False), (body["options"], "think" in body))


class Overrides(Base):
    def test_effort_replaces_the_default_effort_and_the_default_thinking(self):
        self.section(effort="low")
        self.assertEqual("high", self.sent("--effort", "high")["think"])
        self.section(thinking=False)
        self.assertEqual("medium", self.sent("--effort", "medium")["think"])

    def test_thinking_replaces_the_default_effort_and_the_default_thinking_and_is_sent_as_a_boolean(self):
        self.section(effort="low")
        self.assertIs(True, self.sent("--thinking", "on")["think"])
        self.assertIs(False, self.sent("--thinking", "off")["think"])
        self.section(thinking=True)
        self.assertIs(False, self.sent("--thinking", "off")["think"])
        self.assertIs(True, self.sent("--thinking", "on")["think"])

    def test_the_arguments_are_sent_to_a_section_that_holds_no_default(self):
        self.section()
        self.assertEqual("low", self.sent("--effort", "low")["think"])
        self.assertIs(False, self.sent("--thinking", "off")["think"])
        self.assertEqual({"num_ctx": 8192, "num_predict": 50}, self.sent("--max-output", "50")["options"])

    def test_effort_and_thinking_together_are_refused_in_either_order(self):
        self.section(effort="low")
        self.refused("--effort", "high", "--thinking", "on", contains="together")
        self.refused("--thinking", "off", "--effort", "high", contains="together")

    def test_a_thinking_that_is_not_on_or_off_is_refused(self):
        for bad in ("", "yes", "ON", "Off", "true", "false", "1", "0", "on ", "low"):
            self.refused("--thinking", bad, contains="--thinking")
        self.refused("--thinking", contains="needs a value")
        self.refused("--thinking", "on", "--thinking", "off", contains="given twice")

    def test_max_output_replaces_the_limit_may_equal_it_and_is_refused_above_it(self):
        self.section(output_limit=6000)
        self.assertEqual(100, self.sent("--max-output", "100")["options"]["num_predict"])
        self.assertEqual(6000, self.sent("--max-output", "6000")["options"]["num_predict"])
        self.assertEqual(1, self.sent("--max-output", "1")["options"]["num_predict"])
        before = len(self.fake.requests)
        self.refused("--max-output", "6001", contains="--max-output")
        self.refused("--max-output", "10000000", contains="--max-output")
        self.assertEqual(before, len(self.fake.requests))

    def test_a_section_whose_limit_is_ten_million_takes_ten_million_and_refuses_one_more(self):
        self.section(output_limit=10000000)
        self.assertEqual(10000000, self.sent("--max-output", "10000000")["options"]["num_predict"])
        self.assertEqual(9999999, self.sent("--max-output", "9999999")["options"]["num_predict"])
        self.refused("--max-output", "10000001", contains="larger than the largest output limit")
        self.refused("--max-output", "99999999", contains="larger than the largest output limit")

    def test_a_section_with_no_limit_takes_a_value_up_to_ten_million(self):
        self.section()
        self.assertEqual(10000000, self.sent("--max-output", "10000000")["options"]["num_predict"])
        self.refused("--max-output", "10000001", contains="--max-output")

    def test_max_output_has_the_forms_of_context(self):
        self.section(output_limit=6000)
        for bad in ("", "0", "007", "+5", "-1", "1e3", " 5", "5 ", "5.0", "١٢", "0x10", "123456789", "5_0", "five"):
            # the form message, and not the message of the ceiling, which a nine-digit value would also earn
            self.refused("--max-output", bad, contains="a whole number of 1 to 8 digits")
        self.refused("--max-output", contains="needs a value")
        self.refused("--max-output", "5", "--max-output", "6", contains="given twice")

    def test_max_output_with_a_model_that_is_not_configured_is_refused_for_the_model(self):
        self.section(output_limit=6000)
        err = self.refused("--max-output", "5", "--model", "not-configured:1b", contains="--model")
        self.assertNotIn("not-configured", err)

    def test_a_refusal_comes_before_the_size_rule_and_before_anything_is_sent(self):
        self.endpoints(ned=self.record(models={"m": dict(CHAT, context=10, output_limit=5)}, default_model="m"))
        self.refused("--max-output", "6", prompt=b"a" * 1000, contains="--max-output")
        self.refused("--effort", "low", "--thinking", "on", prompt=b"a" * 1000, contains="together")
        self.assertEqual([], self.fake.requests)

    def test_the_new_options_are_refused_by_embed_and_by_models(self):
        texts = json.dumps({"texts": ["alpha"]}).encode()
        for args in (("--effort", "low"), ("--thinking", "on"), ("--max-output", "5")):
            err = self.refused(*args, command="embed", prompt=texts, contains="not an option of embed")
            self.refused(*args, command="models", prompt=b"", contains="not an option of models")
            self.assertNotIn("127.0.0.1", err)


class Check(Base):
    def lines(self):
        code, out, err = self.ask(command="check")
        self.assertEqual((0, ""), (code, err))
        return [line for line in out.splitlines() if line.startswith("model ")]

    def test_the_defaults_follow_the_figure_in_a_fixed_order_and_only_when_the_section_holds_them(self):
        models = {"a": dict(CHAT, effort="high", output_limit=6000), "b": dict(CHAT, thinking=False, bytes_per_token=3),
                  "c": dict(CHAT, thinking=True), "d": dict(CHAT, output_limit=1), "e": dict(CHAT),
                  "f": dict(EMBEDDING, default_context=100)}
        self.endpoints(ned=self.record(models=models, default_model="a", embedding_model="f"))
        self.assertEqual([
            "model ned/a kind=chat context=8192 window=8192 bytes_per_token=2 effort=high output_limit=6000",
            "model ned/b kind=chat context=8192 window=8192 bytes_per_token=3 thinking=off",
            "model ned/c kind=chat context=8192 window=8192 bytes_per_token=2 thinking=on",
            "model ned/d kind=chat context=8192 window=8192 bytes_per_token=2 output_limit=1",
            "model ned/e kind=chat context=8192 window=8192 bytes_per_token=2",
            "model ned/f kind=embedding context=8192 window=100 bytes_per_token=2"], self.lines())

    def test_the_order_does_not_follow_the_order_of_the_keys_in_the_file(self):
        section = {"output_limit": 7, "effort": "low", "bytes_per_token": 4, "kind": "chat", "context": 100}
        self.endpoints(ned=self.record(models={"m": section}, default_model="m"))
        self.assertEqual(["model ned/m kind=chat context=100 window=100 bytes_per_token=4 effort=low output_limit=7"],
                         self.lines())


if __name__ == "__main__":
    unittest.main()
