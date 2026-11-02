"""The endpoint file of format 2: the model sections, the allowlist, the window of a call and `--context` (decision
`2026-11-02-model-configurations-in-endpoint-records`; checklist items 12 to 14 of `docs/specs/ask-ollama.md`). Plan
`2026-11-02-bridge-model-configurations`, increment C. Every refusal is made before a request, and no refusal quotes a
model name or a value. `check` is used where only the file is under test, because it reads the file by the same rules."""

import json
import unittest

import support_ollama
from support_ollama import chat

CHAT = {"kind": "chat", "context": 10}
EMBEDDING = {"kind": "embedding", "context": 10}


class Format(support_ollama.Bridge):
    def document_of(self, **fields):
        record = self.record(models={"m": dict(CHAT)}, default_model="m", **fields)
        return {"format": 2, "endpoints": {"ned": record}}

    def bad_file(self, document, contains="endpoint file"):
        self.write_endpoint_file(json.dumps(document).encode())
        err = self.refused(command="check", contains=contains)
        self.refused(contains=contains)
        self.assertEqual([], self.fake.requests)
        return err

    def good_file(self, document):
        self.write_endpoint_file(json.dumps(document).encode())
        self.assertEqual(0, self.ask(command="check")[0])

    def with_models(self, models, **fields):
        record = self.record(models=models, default_model=None, **fields)
        return {"format": 2, "endpoints": {"ned": record}}

    def test_format_1_is_refused_as_older_and_every_other_format_as_not_2(self):
        old = {"scheme": "http", "host": "127.0.0.1", "port": self.fake.port, "location": "this-machine",
               "authenticated": False, "default_model": "llama3:8b", "context": 4096}
        err = self.bad_file({"format": 1, "endpoints": {"ned": old}}, "older format")
        self.assertIn("rewritten", err)
        for number in (0, 3, "2", True, None, [2], 100):
            err = self.bad_file({"format": number, "endpoints": {"ned": self.record()}}, "format is not 2")
            self.assertNotIn("older", err)

    def test_the_older_file_is_refused_whole_even_when_every_record_is_otherwise_fine(self):
        self.bad_file({"format": 1, "endpoints": {"ned": self.record()}}, "older format")

    def test_models_is_an_object_of_1_to_64_models(self):
        for bad in (None, [], {}, "chat", 1, [dict(CHAT)], True):
            document = self.document_of()
            document["endpoints"]["ned"]["models"] = bad
            self.bad_file(document, "models")
        many = {"m%d" % number: dict(CHAT) for number in range(65)}
        self.bad_file(self.with_models(many), "1 to 64")
        self.good_file(self.with_models({key: many[key] for key in list(many)[:64]}))

    def test_a_record_without_models_is_refused(self):
        document = self.document_of()
        del document["endpoints"]["ned"]["models"]
        self.bad_file(document, "missing the field")

    def test_a_model_name_outside_the_rule_is_refused_without_the_name(self):
        for name in ("", "a b", "a..b", "/a", "a/", "a//b", "-a", "x" * 129, "é", "a;b"):
            err = self.bad_file(self.with_models({name: dict(CHAT)}), "model name")
            if len(name) > 3 and name.isprintable():
                self.assertNotIn(name, err)

    def test_a_repeated_model_name_is_not_strict_json(self):
        document = json.dumps(self.with_models({"m": dict(CHAT)}))
        self.write_endpoint_file(document.replace('"m": {', '"m": {"kind": "chat", "context": 5}, "m": {', 1).encode())
        self.refused(command="check", contains="strict JSON")

    def test_a_section_that_is_not_an_object_or_holds_an_unknown_field_or_lacks_a_required_one_is_refused(self):
        for section in ("chat", 1, [], None, True):
            self.bad_file(self.with_models({"m": section}), "not an object")
        self.bad_file(self.with_models({"m": dict(CHAT, extra=1)}), "not allowed")
        self.bad_file(self.with_models({"m": dict(CHAT, window=5)}), "not allowed")
        self.bad_file(self.with_models({"m": {"context": 10}}), "missing the field")
        self.bad_file(self.with_models({"m": {"kind": "chat"}}), "missing the field")
        self.bad_file(self.with_models({"m": {}}), "missing the field")

    def test_a_kind_that_is_not_chat_or_embedding_is_refused(self):
        for kind in (1, None, "Chat", "embed", "", ["chat"], True, "chat "):
            self.bad_file(self.with_models({"m": {"kind": kind, "context": 10}}), "kind")

    def test_a_context_outside_its_form_is_refused_and_the_limits_are_read(self):
        for context in (0, -1, 10000001, "4096", True, None, [1], 10 ** 30):
            self.bad_file(self.with_models({"m": {"kind": "chat", "context": context}}), "context")
        for context in (1, 4096, 10000000):
            self.good_file(self.with_models({"m": {"kind": "chat", "context": context}}))

    def test_a_default_context_outside_its_form_or_above_the_context_is_refused(self):
        for value in (0, -1, 11, "5", True, None, 10 ** 30, [5]):
            self.bad_file(self.with_models({"m": dict(CHAT, default_context=value)}), "default_context")
        for value in (1, 5, 10):
            self.good_file(self.with_models({"m": dict(CHAT, default_context=value)}))

    def test_a_bytes_per_token_outside_1_to_8_or_not_whole_is_refused(self):
        for value in (0, 9, -1, True, "2", None, [2], 10 ** 30):
            self.bad_file(self.with_models({"m": dict(CHAT, bytes_per_token=value)}), "bytes_per_token")
        for value in (1, 2, 8):
            self.good_file(self.with_models({"m": dict(CHAT, bytes_per_token=value)}))

    def test_a_float_where_a_whole_number_belongs_is_not_strict_json_and_is_refused(self):
        for text in ('"format": 2.0', '"context": 10.0', '"context": 1.5', '"default_context": 5.5', '"bytes_per_token": 2.0'):
            body = json.dumps(self.with_models({"m": dict(CHAT, default_context=5, bytes_per_token=2)}))
            for key in ("format", "context", "default_context", "bytes_per_token"):
                if text.startswith('"%s"' % key):
                    marker = '"%s": %s' % (key, {"format": "2", "context": "10", "default_context": "5",
                                                  "bytes_per_token": "2"}[key])
                    self.assertIn(marker, body)
                    self.write_endpoint_file(body.replace(marker, text, 1).encode())
                    self.refused(command="check", contains="strict JSON")

    def test_every_field_of_a_section_may_be_given_together(self):
        self.good_file(self.with_models({"m": {"kind": "chat", "context": 10, "default_context": 10, "bytes_per_token": 1}}))

    def test_default_model_and_embedding_model_must_be_configured_and_of_their_kind(self):
        models = {"c": dict(CHAT), "e": dict(EMBEDDING)}
        for key, bad in (("default_model", "e"), ("default_model", "zzz"), ("embedding_model", "c"),
                         ("embedding_model", "zzz")):
            document = self.with_models(models)
            document["endpoints"]["ned"][key] = bad
            err = self.bad_file(document, key)
            self.assertNotIn("zzz", err)
        document = self.with_models(models)
        document["endpoints"]["ned"].update(default_model="c", embedding_model="e")
        self.good_file(document)
        self.good_file(self.with_models(models))  # a record with neither is read; a call must then name its model

    def test_a_record_may_name_its_only_model_as_the_default(self):
        self.good_file(self.document_of())


class Hardening(support_ollama.Bridge):
    """The format is read first, two names a server may read as one model are refused, and a run of more than 4,300 digits is
    refused before the file is parsed (plan `2026-11-02-bridge-model-configurations`, increment D)."""

    def bad(self, document, contains):
        data = document if isinstance(document, bytes) else json.dumps(document).encode()
        self.write_endpoint_file(data)
        err = self.refused(command="check", contains=contains)
        self.refused(contains=contains)
        self.assertEqual([], self.fake.requests)
        return err

    def good(self, models):
        self.endpoints(ned=self.record(models=models, default_model=None))
        self.assertEqual(0, self.ask(command="check")[0])

    def test_the_format_is_judged_before_the_other_top_level_fields(self):
        self.bad({"format": 1, "endpoints": {}, "extra": 1}, "older format")
        self.bad({"format": 3, "endpoints": {}, "extra": 1}, "format is not 2")
        self.bad({"endpoints": {}, "extra": 1}, "format is not 2")
        self.bad({"format": 2, "endpoints": {}, "extra": 1}, "not allowed")

    def test_two_model_names_of_one_record_that_a_server_may_read_as_one_are_refused(self):
        for names in (("m", "m:latest"), ("M", "m"), ("a/B:latest", "a/b"), ("m:LATEST", "m"), ("Org/Model", "org/model:latest")):
            models = {name: {"kind": "chat", "context": 10} for name in names}
            err = self.bad({"format": 2, "endpoints": {"ned": self.record(models=models, default_model=None)}}, "same model")
            for name in names:
                if len(name) > 3:
                    self.assertNotIn(name, err)
        models = {"m": {"kind": "chat", "context": 10}, "m:latest": {"kind": "embedding", "context": 10}}
        self.bad({"format": 2, "endpoints": {"ned": self.record(models=models, default_model=None)}}, "same model")

    def test_names_that_differ_beyond_case_and_a_trailing_latest_are_read(self):
        self.good({"m": dict(CHAT), "n:latest": dict(CHAT), "m:7b": dict(CHAT), "m:latest:x": dict(CHAT), "latest": dict(CHAT)})
        self.good({"a/m": dict(CHAT), "b/m": dict(CHAT), "m:latest2": dict(CHAT)})

    def test_the_same_name_in_two_records_is_not_an_alias(self):
        self.endpoints(default=None, a=self.record(), b=self.record())
        self.assertEqual(0, self.ask(command="check")[0])

    def test_a_run_of_more_than_4300_digits_anywhere_in_the_file_is_refused_as_not_strict_json(self):
        good = json.dumps({"format": 2, "endpoints": {"ned": self.record()}})
        for where in ('"scheme": "http"', '"port": %d' % self.fake.port):
            self.bad(good.replace(where, where + ', "x": ' + "9" * 4301, 1).encode(), "strict JSON")
        self.bad(good.replace('"scheme": "http"', '"scheme": "' + "9" * 4301 + '"', 1).encode(), "strict JSON")
        self.write_endpoint_file(good.replace('"scheme": "http"', '"scheme": "' + "9" * 4300 + '"', 1).encode())
        self.refused(command="check", contains="scheme")

    def test_the_guard_holds_when_the_interpreter_limit_on_digits_is_lifted(self):
        import sys
        good = json.dumps({"format": 2, "endpoints": {"ned": self.record()}})
        data = good.replace('"authenticated"', '"x": ' + "9" * 5000 + ', "authenticated"', 1).encode()
        before = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(0)
        self.addCleanup(sys.set_int_max_str_digits, before)
        self.bad(data, "strict JSON")


class Allowlist(support_ollama.Bridge):
    """A call uses only a model the selected record configures, and only one of the kind the command needs."""

    def sent_model(self):
        return json.loads(self.fake.requests[-1]["body"])["model"]

    def test_a_model_that_is_not_configured_is_refused_before_anything_is_sent_and_is_not_quoted(self):
        err = self.refused("--model", "not-configured:1b", contains="--model")
        self.assertNotIn("not-configured", err)
        self.assertEqual([], self.fake.requests)

    def test_a_model_configured_for_the_other_kind_is_refused_for_ask(self):
        err = self.refused("--model", "nomic-embed-text", contains="other kind")
        self.assertNotIn("nomic", err)

    def test_a_chat_model_is_refused_for_embed_and_an_embedding_model_is_sent(self):
        texts = json.dumps({"texts": ["alpha"]}).encode()
        err = self.refused("--model", "llama3:8b", command="embed", prompt=texts, contains="other kind")
        self.assertNotIn("llama3", err)
        self.fake.reply({"embeddings": [[0.5, 0.25]], "model": "nomic-embed-text", "prompt_eval_count": 3})
        code, out, err = self.ask("--model", "nomic-embed-text", command="embed", prompt=texts)
        self.assertEqual((0, ""), (code, err))
        self.assertEqual("nomic-embed-text", self.sent_model())

    def test_a_model_that_is_not_configured_is_refused_for_embed_too(self):
        texts = json.dumps({"texts": ["alpha"]}).encode()
        self.refused("--model", "not-configured", command="embed", prompt=texts, contains="--model")

    def test_a_configured_model_with_a_slash_is_accepted_and_one_without_a_section_is_not(self):
        self.endpoints(ned=self.record(chat=("org/model:tag",)))
        self.assertTrue(self.document("--model", "org/model:tag")["ok"])
        self.assertEqual("org/model:tag", self.sent_model())
        self.refused("--model", "org/other:tag", contains="--model")

    def test_the_default_model_is_used_without_the_option_and_the_option_beats_it(self):
        self.assertTrue(self.document()["ok"])
        self.assertEqual("llama3:8b", self.sent_model())
        self.assertTrue(self.document("--model", "other:1b")["ok"])
        self.assertEqual("other:1b", self.sent_model())

    def test_a_record_with_no_default_model_needs_the_option_and_the_option_must_be_configured(self):
        self.endpoints(ned=self.record(default_model=None))
        self.refused(contains="no model is named")
        self.refused("--model", "not-configured:1b", contains="--model")
        self.assertTrue(self.document("--model", "gpt-oss:20b")["ok"])

    def test_the_models_of_another_record_are_not_configured_for_this_one(self):
        small = self.record(models={"only-here:1b": dict(CHAT, context=8192)}, default_model="only-here:1b")
        other = self.record(models={"only-there:1b": dict(CHAT, context=8192)}, default_model="only-there:1b")
        self.endpoints(default="a", a=small, b=other)
        self.refused("--model", "only-there:1b", contains="--model")
        self.assertTrue(self.document("--server", "b", "--model", "only-there:1b")["ok"])
        self.refused("--server", "b", "--model", "only-here:1b", contains="--model")


class Windows(support_ollama.Bridge):
    """The window of a call is `--context`, else the section's default window, else its context."""

    def window(self):
        return json.loads(self.fake.requests[-1]["body"])["options"]["num_ctx"]

    def test_without_the_option_the_window_is_the_context_of_the_model(self):
        self.endpoints(ned=self.record(context=4096))
        self.assertTrue(self.document()["ok"])
        self.assertEqual(4096, self.window())

    def test_a_default_context_is_the_window_when_no_option_is_given(self):
        self.endpoints(ned=self.record(context=16384, default_context=8192))
        self.assertTrue(self.document()["ok"])
        self.assertEqual(8192, self.window())

    def test_the_option_beats_the_default_context_and_may_equal_the_context_or_be_one(self):
        self.endpoints(ned=self.record(context=16384, default_context=8192))
        self.assertTrue(self.document("--context", "100")["ok"])
        self.assertEqual(100, self.window())
        self.assertTrue(self.document("--context", "16384")["ok"])
        self.assertEqual(16384, self.window())
        self.fake.reply(chat("an answer", prompt_eval_count=0))
        self.assertTrue(self.document("--context", "1", prompt=b"a\n")["ok"])  # two bytes: the size rule allows window times 2
        self.assertEqual(1, self.window())

    def test_an_option_above_the_context_is_refused_before_anything_is_sent(self):
        self.endpoints(ned=self.record(context=16384, default_context=8192))
        self.refused("--context", "16385", contains="--context")
        self.refused("--context", "99999999", contains="--context")
        self.assertEqual([], self.fake.requests)

    def test_an_option_that_is_not_a_plain_whole_number_is_refused(self):
        for bad in ("", "0", "007", "+5", "-1", "1e3", " 5", "5 ", "5.0", "١٢", "0x10", "123456789", "5_0", "five"):
            self.refused("--context", bad, contains="--context")

    def test_an_option_given_twice_or_without_a_value_is_refused(self):
        self.refused("--context", "5", "--context", "6", contains="given twice")
        self.refused("--context", contains="needs a value")

    def test_the_option_with_a_model_that_is_not_configured_is_refused_for_the_model(self):
        err = self.refused("--context", "5", "--model", "not-configured:1b", contains="--model")
        self.assertNotIn("not-configured", err)

    def test_each_model_has_its_own_window(self):
        models = {"small": {"kind": "chat", "context": 100}, "large": {"kind": "chat", "context": 100000}}
        self.endpoints(ned=self.record(models=models, default_model="small"))
        self.assertTrue(self.document()["ok"])
        self.assertEqual(100, self.window())
        self.assertTrue(self.document("--model", "large")["ok"])
        self.assertEqual(100000, self.window())
        self.refused("--context", "101", contains="--context")
        self.assertTrue(self.document("--model", "large", "--context", "101")["ok"])
        self.assertEqual(101, self.window())

    def test_the_check_of_the_count_uses_the_window_that_was_sent(self):
        self.endpoints(ned=self.record(context=1000))
        body = chat("an answer", prompt_eval_count=100)
        self.fake.reply(body)
        document = self.failed("--context", "100", error="vendor_error", detail="context_overflow")
        self.assertNotIn("reply", document)
        self.fake.reply(chat("an answer", prompt_eval_count=99))
        self.assertTrue(self.document("--context", "100")["ok"])
        self.fake.reply(chat("an answer", prompt_eval_count=100))
        self.assertTrue(self.document()["ok"])

    def test_the_check_of_the_count_uses_the_window_of_the_model_chosen(self):
        models = {"small": {"kind": "chat", "context": 100}, "large": {"kind": "chat", "context": 100000}}
        self.endpoints(ned=self.record(models=models, default_model="small"))
        self.fake.reply(chat("answer", prompt_eval_count=5000))
        self.failed(error="vendor_error", detail="context_overflow")
        self.assertTrue(self.document("--model", "large")["ok"])

    def test_embed_sends_its_window_and_takes_the_option_within_the_context(self):
        texts = json.dumps({"texts": ["alpha"]}).encode()
        self.endpoints(ned=self.record(context=4096, embedding_model="nomic-embed-text"))
        self.fake.reply({"embeddings": [[0.5, 0.25]], "model": "nomic-embed-text"})
        self.assertEqual(0, self.ask(command="embed", prompt=texts)[0])
        self.assertEqual(4096, self.window())
        self.assertEqual(0, self.ask("--context", "2000", command="embed", prompt=texts)[0])
        self.assertEqual(2000, self.window())
        self.refused("--context", "4097", command="embed", prompt=texts, contains="--context")


if __name__ == "__main__":
    unittest.main()
