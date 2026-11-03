"""`truncate` false in the request of `ask` and the refusal of a prompt that the window cannot hold (the sections "`ask`: the
request", "Context window" and "Errors" of `docs/specs/ask-ollama.md`, checklist item 19). Plan
`2026-11-02-bridge-model-configurations`, increment G-B. The server's own refusal is `context_overflow`; the words that choose the
row are matched in lower case, are judged before the thinking and the format words, and are never copied; every other row of a 400
is unchanged. The text of the real server (Ollama 0.35.1, read by raw requests on 2026-11-02) is used as it came."""

import json
import unittest

import support_ollama
from support_ollama import chat

# What the server answered, as the `error` string of its body: a string that itself holds JSON text.
REAL = ('{"error":{"code":400,"message":"request (2167 tokens) exceeds the available context size (2048 tokens), try '
        'increasing it","type":"exceed_context_size_error","n_prompt_tokens":2167,"n_ctx":2048}}')
MESSAGE = "the prompt does not fit the context window"


class Truncate(support_ollama.Bridge):
    def body(self):
        return json.loads(self.fake.requests[-1]["body"])

    def sent(self, *args, prompt=b"Review docs/plan.md\n"):
        self.assertTrue(self.document(*args, prompt=prompt)["ok"])
        return self.body()


class Request(Truncate):
    def test_every_ask_carries_truncate_false_at_the_top_level_and_none_in_options(self):
        body = self.sent()
        self.assertIs(False, body["truncate"])
        self.assertNotIn("truncate", body["options"])
        self.assertEqual({"model", "messages", "stream", "truncate", "options"}, set(body))

    def test_it_is_sent_with_a_schema_a_thinking_default_an_output_limit_and_an_override(self):
        self.endpoints(ned=self.record(models={"m": {"kind": "chat", "context": 8192, "effort": "low", "output_limit": 100}},
                                       default_model="m"))
        with open(self.root + "/docs/schema.json", "w") as handle:
            handle.write('{"type": "object"}')
        self.fake.reply(chat('{"a": 1}'))
        body = self.sent("--schema", "docs/schema.json")
        self.assertEqual({"model", "messages", "stream", "truncate", "options", "format", "think"}, set(body))
        self.assertEqual((False, "low", {"num_ctx": 8192, "num_predict": 100}), (body["truncate"], body["think"], body["options"]))
        for args in (("--thinking", "off"), ("--effort", "high"), ("--max-output", "5"), ("--context", "4096")):
            body = self.sent(*args)
            self.assertIs(False, body["truncate"], args)
            self.assertNotIn("truncate", body["options"], args)

    def test_embed_still_sends_it_at_the_top_level_and_none_in_options(self):
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text"))
        self.fake.reply({"embeddings": [[0.5, 0.25]], "model": "nomic-embed-text"})
        code, out, err = self.ask(command="embed", prompt=json.dumps({"texts": ["alpha"]}).encode())
        self.assertEqual((0, ""), (code, err))
        body = self.body()
        self.assertIs(False, body["truncate"])
        self.assertNotIn("truncate", body["options"])


class Refusal(Truncate):
    def overflow(self, text, *args):
        self.fake.reply({"error": text}, status=400)
        document = self.failed(*args, error="vendor_error", detail="context_overflow")
        self.assertEqual(MESSAGE, document["message"])
        self.assertNotIn("reply", document)
        return document

    def test_the_text_of_the_real_server_is_context_overflow_not_retryable_with_the_fixed_message(self):
        document = self.overflow(REAL)
        self.assertFalse(document["retryable"])
        out = json.dumps(document)
        for word in ("2167", "2048", "exceeds", "exceed_context_size_error", "available"):
            self.assertNotIn(word, out)

    def test_either_word_alone_is_enough_and_the_case_does_not_matter(self):
        for text in ("request (3017 tokens) exceeds the available context size (2048 tokens)", "exceed_context_size_error",
                     "REQUEST EXCEEDS THE AVAILABLE CONTEXT SIZE", "Exceed_Context_Size_Error", "x " + REAL.upper()):
            self.overflow(text)

    def test_it_is_judged_before_the_thinking_and_the_format_words(self):
        for text in ("the thinking budget exceeds the available context size", "think: exceed_context_size_error",
                     "the format of the request exceeds the available context size", "schema: exceeds the available context size",
                     REAL + " think format schema"):
            self.overflow(text)

    def test_the_words_of_another_wording_are_not_matched(self):
        for text in ("the prompt is longer than the context length currently available to the model", "context length exceeded",
                     "exceeds the context size", "the input length exceeds the context length", "too long"):
            self.fake.reply({"error": text}, status=400)
            self.failed(error="vendor_error", detail="bad_exit")

    def test_the_words_with_a_status_other_than_400_are_not_the_overflow_row(self):
        for status in (300, 401, 403, 413, 429, 500, 503):
            self.fake.reply({"error": REAL}, status=status)
            self.failed(error="vendor_error", detail="bad_exit", retryable=status in (500, 503))

    def test_a_404_that_says_not_found_is_still_model_unavailable(self):
        self.fake.reply({"error": "model not found: " + REAL}, status=404)
        self.failed(error="model_unavailable")

    def test_a_400_that_holds_an_overflow_word_and_not_found_is_still_the_overflow_row(self):
        self.overflow("model not found: " + REAL)
        self.overflow("not found: exceed_context_size_error")

    def test_the_overflow_word_in_another_field_than_error_is_not_matched(self):
        for body in ({"error": "the request was bad", "message": REAL}, {"error": "bad", "detail": "exceed_context_size_error"},
                     {"error": "bad", "error_type": "exceed_context_size_error", "message": "exceeds the available context size"}):
            self.fake.reply(body, status=400)
            self.failed(error="vendor_error", detail="bad_exit")

    def test_a_400_whose_body_is_not_an_object_with_a_string_error_is_bad_exit(self):
        for body in (b"", b"not json", b"[]", b'{"error": 5}', b'{"error": null}', b'{"error": ["exceeds the available context size"]}',
                     b'{"message": "exceeds the available context size"}', b"\xff"):
            self.fake.reply(body, status=400)
            self.failed(error="vendor_error", detail="bad_exit")

    def test_the_other_400_rows_are_unchanged(self):
        self.fake.reply({"error": "\"llama3:8b\" does not support thinking"}, status=400)
        document = self.failed("--effort", "low", error="effort_unsupported")
        self.assertEqual("the model does not support this effort or thinking setting", document["message"])
        self.assertNotIn("llama3", json.dumps(document))
        for text in ("invalid format", "the schema is wrong", "FORMAT"):
            self.fake.reply({"error": text}, status=400)
            self.assertEqual("the server rejected the schema", self.failed(error="vendor_error", detail="bad_schema")["message"])
        self.fake.reply({"error": "something else"}, status=400)
        self.failed(error="vendor_error", detail="bad_exit")

    def test_a_refusal_by_the_server_leaves_nothing_of_the_prompt_in_the_object(self):
        self.fake.reply({"error": REAL}, status=400)
        code, out, err = self.ask(prompt=b"SECRET-PROMPT-TEXT\n")
        self.assertEqual((1, ""), (code, err))
        self.assertNotIn("SECRET", out)


class Unchanged(Truncate):
    def test_the_size_rule_and_the_check_of_the_count_are_as_before(self):
        self.endpoints(ned=self.record(context=100))
        document = self.failed(prompt=b"a" * 201, error="vendor_error", detail="context_overflow")
        self.assertEqual("the prompt is probably larger than the window", document["message"])
        self.assertEqual([], self.fake.requests)
        self.fake.reply(chat("an answer", prompt_eval_count=100))
        document = self.failed(prompt=b"a" * 50, error="vendor_error", detail="context_overflow")
        self.assertEqual(MESSAGE, document["message"])

    def test_a_refusal_by_the_server_and_the_count_check_give_the_same_object(self):
        self.endpoints(ned=self.record(context=100))
        self.fake.reply({"error": REAL}, status=400)
        refused = self.failed(prompt=b"a" * 50, error="vendor_error", detail="context_overflow")
        self.fake.reply(chat("an answer", prompt_eval_count=100))
        counted = self.failed(prompt=b"a" * 50, error="vendor_error", detail="context_overflow")
        self.assertEqual(refused, counted)


if __name__ == "__main__":
    unittest.main()
