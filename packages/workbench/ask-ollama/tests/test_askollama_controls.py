"""The temperature and the keep_alive of a model section and the options `--temperature` and `--keep-alive` (decision
`2026-11-02-temperature-and-keep-alive-in-model-sections`; checklist items 20 and 21 of `docs/specs/ask-ollama.md`). Plan
`2026-11-02-bridge-request-controls`, increment D. Every refusal is made before a request and quotes no value; a default is
applied only when the call passes nothing, and an argument replaces it."""

import json
import unittest

import support_ollama
from support_ollama import chat

CHAT = {"kind": "chat", "context": 8192}
EMBEDDING = {"kind": "embedding", "context": 8192}

GOOD_TEMPERATURES = ("0", "0.2", "0.50", "1", "2", "2.0", "2.00", "1.99", "0.01", "1.5")
BAD_TEMPERATURES = ("-0.2", "+1", "00.2", "01", ".5", "1.", "0.123", "2.01", "2.1", "3", "10", "1e0", "0.2e1", " 0.2", "0.2 ",
                    "0.2\n", "\n0.2", "", "0,2", "NaN", "٠.٢", "０.２", "0..2", "0.2.1", "-0", "1 ", "two")
GOOD_KEEP_ALIVES = ("0", "-1", "1s", "30m", "9999h", "1h", "10s", "5m")
BAD_KEEP_ALIVES = ("-2", "+5m", "01s", "00m", "30", "5d", "1.5h", "10000s", "1 s", " 1s", "1s ", "1s\n", "", "-1m", "-0", "0s",
                   "1S", "30 m", "٣٠m", "１ｍ", "m", "s", "-", "+1", "1ms", "0m", "forever")


def embedding():
    """The body of a finished embedding reply of the server."""
    return {"model": "e", "prompt_eval_count": 7, "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]}


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

    def good_file(self, section, kind=CHAT):
        self.endpoints(ned=self.record(models={"m": dict(kind, **section)}, default_model=None))
        self.assertEqual(0, self.ask(command="check")[0], section)

    def test_each_temperature_of_the_grammar_is_read(self):
        for text in GOOD_TEMPERATURES:
            self.good_file({"temperature": text})

    def test_each_form_outside_the_grammar_is_refused_without_the_value(self):
        for text in BAD_TEMPERATURES:
            self.not_quoted(text, self.bad_file({"m": dict(CHAT, temperature=text)}, "temperature"))

    def test_a_temperature_that_is_not_a_string_is_refused(self):
        for value in (0, 1, 2, -1, True, False, None, ["0.2"], {"a": "0.2"}, 10 ** 30):
            self.not_quoted(value, self.bad_file({"m": dict(CHAT, temperature=value)}, "temperature"))

    def test_a_fraction_in_the_file_is_not_strict_json_and_a_string_is_the_way(self):
        document = json.dumps({"format": 2, "endpoints": {"ned": self.record(models={"m": dict(CHAT, temperature="0.2")},
                                                                              default_model=None)}})
        self.write_endpoint_file(document.replace('"temperature": "0.2"', '"temperature": 0.2').encode())
        self.refused(command="check", contains="strict JSON")

    def test_each_keep_alive_of_the_grammar_is_read_in_a_chat_and_in_an_embedding_section(self):
        for text in GOOD_KEEP_ALIVES:
            self.good_file({"keep_alive": text})
            self.good_file({"keep_alive": text}, EMBEDDING)

    def test_each_keep_alive_outside_the_grammar_is_refused_without_the_value(self):
        for text in BAD_KEEP_ALIVES:
            self.not_quoted(text, self.bad_file({"m": dict(CHAT, keep_alive=text)}, "keep_alive"))
            self.bad_file({"m": dict(EMBEDDING, keep_alive=text)}, "keep_alive")

    def test_a_keep_alive_that_is_not_a_string_is_refused(self):
        for value in (0, -1, 5, True, False, None, ["0"], {"a": "0"}):
            self.not_quoted(value, self.bad_file({"m": dict(CHAT, keep_alive=value)}, "keep_alive"))

    def test_an_embedding_section_holds_no_temperature(self):
        for text in GOOD_TEMPERATURES[:3]:
            self.bad_file({"m": dict(EMBEDDING, temperature=text)}, "chat")

    def test_a_section_may_hold_every_field_at_once(self):
        self.good_file({"effort": "low", "output_limit": 100, "temperature": "0.2", "keep_alive": "5m"})
        self.good_file({"thinking": False, "temperature": "1", "keep_alive": "-1"})

    def test_a_field_that_is_still_not_allowed_is_refused(self):
        for field in ("top_p", "seed", "num_predict", "keepalive", "Temperature", "keep-alive"):
            self.bad_file({"m": dict(CHAT, **{field: "1"})}, "not allowed")


class Request(Base):
    def test_a_section_with_neither_field_sends_what_it_sent_before(self):
        self.section()
        self.assertEqual({"model": "m", "messages": [{"role": "user", "content": "Review docs/plan.md\n"}], "stream": False,
                          "truncate": False, "options": {"num_ctx": 8192}}, self.sent())

    def test_the_section_temperature_is_sent_as_a_number_inside_options(self):
        for text, number in (("0", 0.0), ("0.2", 0.2), ("0.50", 0.5), ("1", 1.0), ("2", 2.0), ("2.00", 2.0), ("1.99", 1.99)):
            self.section(temperature=text)
            body = self.sent()
            self.assertEqual({"num_ctx": 8192, "temperature": number}, body["options"])
            self.assertIs(float, type(body["options"]["temperature"]), text)
            self.assertNotIn("temperature", body)
            self.assertNotIn("keep_alive", body)

    def test_the_section_keep_alive_is_sent_at_the_top_level_with_zero_and_minus_one_as_numbers(self):
        for text, wire in (("0", 0), ("-1", -1), ("30m", "30m"), ("1s", "1s"), ("9999h", "9999h")):
            self.section(keep_alive=text)
            body = self.sent()
            self.assertEqual(wire, body["keep_alive"])
            self.assertIs(type(wire), type(body["keep_alive"]), text)
            self.assertEqual({"num_ctx": 8192}, body["options"])

    def test_zero_is_sent_and_not_dropped(self):
        self.section(temperature="0", keep_alive="0")
        body = self.sent()
        self.assertEqual((0.0, 0), (body["options"]["temperature"], body["keep_alive"]))
        self.assertIs(int, type(body["keep_alive"]))

    def test_the_two_fields_with_the_other_defaults_and_the_schema_keep_their_places(self):
        self.section(effort="low", output_limit=500, temperature="0.2", keep_alive="5m")
        with open(self.root + "/docs/schema.json", "w") as handle:
            handle.write('{"type": "object"}')
        self.fake.reply(chat('{"a": 1}'))
        body = self.sent("--schema", "docs/schema.json")
        self.assertEqual({"model", "messages", "stream", "truncate", "options", "format", "think", "keep_alive"}, set(body))
        self.assertEqual({"num_ctx": 8192, "num_predict": 500, "temperature": 0.2}, body["options"])
        self.assertEqual("5m", body["keep_alive"])

    def test_each_model_has_its_own_values(self):
        models = {"a": dict(CHAT, temperature="0.2", keep_alive="0"), "b": dict(CHAT, temperature="1"), "c": dict(CHAT)}
        self.endpoints(ned=self.record(models=models, default_model="a"))
        body = self.sent()
        self.assertEqual((0.2, 0), (body["options"]["temperature"], body["keep_alive"]))
        body = self.sent("--model", "b")
        self.assertEqual((1.0, False), (body["options"]["temperature"], "keep_alive" in body))
        body = self.sent("--model", "c")
        self.assertEqual(({"num_ctx": 8192}, False), (body["options"], "keep_alive" in body))

    def test_the_request_is_one_request(self):
        self.section(temperature="0.2", keep_alive="5m")
        self.sent()
        self.assertEqual(1, len(self.fake.requests))


class Overrides(Base):
    def test_a_temperature_argument_replaces_the_section_value(self):
        self.section(temperature="0.2")
        self.assertEqual(0.5, self.sent("--temperature", "0.5")["options"]["temperature"])
        self.assertEqual(0.2, self.sent()["options"]["temperature"])

    def test_zero_as_an_argument_replaces_and_is_sent(self):
        self.section(temperature="1")
        body = self.sent("--temperature", "0")
        self.assertEqual(0.0, body["options"]["temperature"])
        self.assertIs(float, type(body["options"]["temperature"]))

    def test_the_two_values_the_knowledge_base_module_uses_are_sent(self):
        self.section(temperature="0.2")
        self.assertEqual(0.2, self.sent()["options"]["temperature"])
        self.assertEqual(0.5, self.sent("--temperature", "0.5")["options"]["temperature"])

    def test_a_temperature_argument_is_sent_to_a_section_that_holds_none(self):
        self.section()
        for text, number in (("0", 0.0), ("2", 2.0), ("2.00", 2.0), ("0.75", 0.75)):
            self.assertEqual(number, self.sent("--temperature", text)["options"]["temperature"])

    def test_a_keep_alive_argument_replaces_the_section_value_in_the_wire_form(self):
        self.section(keep_alive="30m")
        for text, wire in (("0", 0), ("-1", -1), ("1h", "1h"), ("10s", "10s")):
            body = self.sent("--keep-alive", text)
            self.assertEqual(wire, body["keep_alive"], text)
            self.assertIs(type(wire), type(body["keep_alive"]), text)
        self.assertEqual("30m", self.sent()["keep_alive"])

    def test_a_keep_alive_argument_is_sent_to_a_section_that_holds_none(self):
        self.section()
        self.assertEqual(-1, self.sent("--keep-alive", "-1")["keep_alive"])
        self.assertEqual(0, self.sent("--keep-alive", "0")["keep_alive"])

    def test_the_arguments_work_with_the_other_options_in_one_call(self):
        self.section(effort="low", output_limit=500)
        body = self.sent("--temperature", "0.3", "--keep-alive", "10m", "--effort", "high", "--max-output", "50")
        self.assertEqual({"num_ctx": 8192, "num_predict": 50, "temperature": 0.3}, body["options"])
        self.assertEqual(("high", "10m"), (body["think"], body["keep_alive"]))
        body = self.sent("--thinking", "off", "--temperature", "1", "--keep-alive", "0")
        self.assertEqual((False, 1.0, 0), (body["think"], body["options"]["temperature"], body["keep_alive"]))

    def test_each_form_outside_the_grammar_is_refused_for_the_option_and_nothing_is_sent(self):
        self.section(temperature="0.2", keep_alive="5m")
        for text in BAD_TEMPERATURES:
            err = self.refused("--temperature", text, contains="--temperature")
            if len(text) > 4:
                self.assertNotIn(text, err)
        for text in BAD_KEEP_ALIVES:
            err = self.refused("--keep-alive", text, contains="--keep-alive")
            if len(text) > 4:
                self.assertNotIn(text, err)
        self.assertEqual([], self.fake.requests)

    def test_a_repeated_option_and_an_option_without_a_value_are_refused(self):
        self.section()
        self.refused("--temperature", contains="needs a value")
        self.refused("--keep-alive", contains="needs a value")
        self.refused("--temperature", "0.1", "--temperature", "0.2", contains="given twice")
        self.refused("--keep-alive", "0", "--keep-alive", "5m", contains="given twice")

    def test_an_option_with_a_model_that_is_not_configured_is_refused_for_the_model(self):
        self.section()
        for args in (("--temperature", "0.5"), ("--keep-alive", "5m")):
            err = self.refused(*args, "--model", "not-configured:1b", contains="--model")
            self.assertNotIn("not-configured", err)

    def test_a_model_of_the_other_kind_is_refused_before_anything_is_sent(self):
        self.endpoints(ned=self.record(models={"m": dict(CHAT), "e": dict(EMBEDDING)}, default_model="m", embedding_model="e"))
        self.refused("--temperature", "0.5", "--model", "e", contains="other kind")
        self.refused("--keep-alive", "5m", "--model", "e", contains="other kind")

    def test_a_refusal_comes_before_the_size_rule_and_before_anything_is_sent(self):
        self.endpoints(ned=self.record(models={"m": dict(CHAT, context=10)}, default_model="m"))
        self.refused("--temperature", "2.5", prompt=b"a" * 1000, contains="--temperature")
        self.refused("--keep-alive", "5d", prompt=b"a" * 1000, contains="--keep-alive")
        self.assertEqual([], self.fake.requests)

    def test_a_leading_minus_one_is_a_value_and_not_an_option(self):
        self.section()
        self.assertEqual(-1, self.sent("--keep-alive", "-1", "--temperature", "0.5")["keep_alive"])


class Embed(Base):
    def setUp(self):
        super().setUp()
        self.fake.reply(embedding())

    def embed_file(self, **fields):
        self.endpoints(ned=self.record(models={"e": dict(EMBEDDING, **fields), "m": dict(CHAT)}, default_model="m",
                                       embedding_model="e"))

    def embed(self, *args, texts=("alpha", "beta")):
        code, out, err = self.ask(*args, prompt=json.dumps({"texts": list(texts)}).encode(), command="embed")
        return code, out, err

    def sent(self, *args):
        code, out, err = self.embed(*args)
        self.assertEqual((0, ""), (code, err), out)
        self.assertTrue(json.loads(out)["ok"])
        return self.body()

    def test_an_embedding_section_without_a_keep_alive_sends_what_it_sent_before(self):
        self.embed_file()
        self.assertEqual({"model": "e", "input": ["alpha", "beta"], "truncate": False, "options": {"num_ctx": 8192}}, self.sent())

    def test_the_section_keep_alive_is_sent_at_the_top_level_in_the_wire_form(self):
        for text, wire in (("0", 0), ("-1", -1), ("30m", "30m")):
            self.embed_file(keep_alive=text)
            body = self.sent()
            self.assertEqual(wire, body["keep_alive"])
            self.assertIs(type(wire), type(body["keep_alive"]), text)
            self.assertEqual({"model", "input", "truncate", "options", "keep_alive"}, set(body))
            self.assertEqual({"num_ctx": 8192}, body["options"])

    def test_the_argument_replaces_the_section_value_and_is_sent_to_a_section_that_holds_none(self):
        self.embed_file(keep_alive="30m")
        self.assertEqual(0, self.sent("--keep-alive", "0")["keep_alive"])
        self.embed_file()
        self.assertEqual("5m", self.sent("--keep-alive", "5m")["keep_alive"])
        self.assertEqual(-1, self.sent("--keep-alive", "-1")["keep_alive"])

    def test_a_form_outside_the_grammar_is_refused_with_nothing_sent(self):
        self.embed_file()
        before = len(self.fake.requests)
        for text in BAD_KEEP_ALIVES:
            code, out, err = self.embed("--keep-alive", text)
            self.assertEqual((1, ""), (code, out), text)
            self.assertTrue(err.startswith("refused: ") and "--keep-alive" in err and err.count("\n") == 1, err)
        self.assertEqual(before, len(self.fake.requests))

    def test_a_temperature_is_refused_by_embed_as_an_unknown_option(self):
        self.embed_file()
        code, out, err = self.embed("--temperature", "0.5")
        self.assertEqual((1, ""), (code, out))
        self.assertIn("not an option of embed", err)
        self.assertEqual([], self.fake.requests)

    def test_the_section_temperature_cannot_be_given_to_an_embedding_section(self):
        self.endpoints(ned=self.record(models={"e": dict(EMBEDDING, temperature="0.2")}, default_model=None,
                                       embedding_model="e"))
        self.refused(command="check", contains="only a chat model")


class Models(Base):
    def test_models_refuses_both_options(self):
        self.section()
        for args in (("--temperature", "0.5"), ("--keep-alive", "5m")):
            err = self.refused(*args, command="models", prompt=b"", contains="not an option of models")
            self.assertNotIn("127.0.0.1", err)


class Check(Base):
    def lines(self):
        code, out, err = self.ask(command="check")
        self.assertEqual((0, ""), (code, err))
        return [line for line in out.splitlines() if line.startswith("model ")]

    def test_the_two_fields_follow_the_other_defaults_in_a_fixed_order_and_only_when_the_section_holds_them(self):
        models = {"a": dict(CHAT, effort="high", output_limit=6000, temperature="0.2", keep_alive="0"),
                  "b": dict(CHAT, thinking=False, bytes_per_token=3, temperature="2.00"),
                  "c": dict(CHAT, keep_alive="-1"), "d": dict(CHAT), "e": dict(EMBEDDING, keep_alive="30m"),
                  "f": dict(EMBEDDING, default_context=100)}
        self.endpoints(ned=self.record(models=models, default_model="a", embedding_model="e"))
        self.assertEqual([
            "model ned/a kind=chat context=8192 window=8192 bytes_per_token=2 effort=high output_limit=6000 temperature=0.2 keep_alive=0",
            "model ned/b kind=chat context=8192 window=8192 bytes_per_token=3 thinking=off temperature=2.00",
            "model ned/c kind=chat context=8192 window=8192 bytes_per_token=2 keep_alive=-1",
            "model ned/d kind=chat context=8192 window=8192 bytes_per_token=2",
            "model ned/e kind=embedding context=8192 window=8192 bytes_per_token=2 keep_alive=30m",
            "model ned/f kind=embedding context=8192 window=100 bytes_per_token=2"], self.lines())

    def test_the_order_does_not_follow_the_order_of_the_keys_in_the_file(self):
        section = {"keep_alive": "5m", "temperature": "0.50", "output_limit": 7, "effort": "low", "kind": "chat", "context": 100}
        self.endpoints(ned=self.record(models={"m": section}, default_model="m"))
        self.assertEqual(["model ned/m kind=chat context=100 window=100 bytes_per_token=2 effort=low output_limit=7 "
                          "temperature=0.50 keep_alive=5m"], self.lines())

    def test_the_text_is_printed_as_the_file_holds_it(self):
        self.endpoints(ned=self.record(models={"m": dict(CHAT, temperature="1", keep_alive="9999h")}, default_model="m"))
        self.assertIn(" temperature=1 keep_alive=9999h", self.lines()[0])


if __name__ == "__main__":
    unittest.main()
