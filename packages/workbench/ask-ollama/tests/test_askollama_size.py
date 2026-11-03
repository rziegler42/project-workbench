"""The size rule: a prompt that is probably larger than the window of its call is not sent (the section "Context window" of
`docs/specs/ask-ollama.md`, checklist item 15). Plan `2026-11-02-bridge-model-configurations`, increment E. The bound is the
window times the model's `bytes_per_token` (2 when the section has none), counted in bytes of UTF-8; a refused prompt is the
contract's failure object with `context_overflow` and nothing reaches the server."""

import json
import os
import unittest

import support_ollama
from support_ollama import chat


class Size(support_ollama.Bridge):
    def too_large(self, prompt, *args):
        before = len(self.fake.requests)
        document = self.failed(*args, prompt=prompt, error="vendor_error", detail="context_overflow")
        self.assertEqual("the prompt is probably larger than the window", document["message"])
        self.assertNotIn("reply", document)
        self.assertEqual(before, len(self.fake.requests), "a request was sent")
        return document

    def sent(self, prompt, *args):
        before = len(self.fake.requests)
        document = self.document(*args, prompt=prompt)
        self.assertTrue(document["ok"], document)
        self.assertEqual(before + 1, len(self.fake.requests))
        return document

    def test_a_prompt_of_exactly_the_window_times_two_bytes_is_sent_and_one_byte_more_is_not(self):
        self.endpoints(ned=self.record(context=100))
        self.sent(b"a" * 200)
        self.too_large(b"a" * 201)

    def test_the_figure_is_the_bytes_per_token_of_the_section(self):
        self.endpoints(ned=self.record(context=100, bytes_per_token=1))
        self.sent(b"a" * 100)
        self.too_large(b"a" * 101)
        self.endpoints(ned=self.record(context=100, bytes_per_token=8))
        self.sent(b"a" * 800)
        self.too_large(b"a" * 801)

    def test_the_window_used_is_the_one_of_the_call(self):
        self.endpoints(ned=self.record(context=1000, default_context=100))
        self.sent(b"a" * 200)
        self.too_large(b"a" * 201)
        self.sent(b"a" * 400, "--context", "200")
        self.too_large(b"a" * 401, "--context", "200")
        self.too_large(b"a" * 101, "--context", "50")

    def test_each_model_has_its_own_figure_and_window(self):
        models = {"small": {"kind": "chat", "context": 20, "bytes_per_token": 1},
                  "large": {"kind": "chat", "context": 1000, "bytes_per_token": 4}}
        self.endpoints(ned=self.record(models=models, default_model="small"))
        self.sent(b"a" * 20)
        self.too_large(b"a" * 21)
        self.sent(b"a" * 4000, "--model", "large")
        self.too_large(b"a" * 4001, "--model", "large")

    def test_the_size_is_counted_in_bytes_of_utf8_and_not_in_characters(self):
        self.endpoints(ned=self.record(context=100))
        self.sent("é".encode() * 100)
        self.too_large("é".encode() * 101)
        self.sent("\U0001f600".encode() * 50)
        self.too_large("\U0001f600".encode() * 51)

    def test_the_failure_is_the_object_of_the_contract_and_quotes_nothing_of_the_prompt(self):
        self.endpoints(ned=self.record(context=10))
        document = self.too_large(b"SECRET-PROMPT-TEXT " * 10)
        self.assertEqual(set(document), {"contract", "ok", "vendor", "error", "detail", "retryable", "message"})
        self.assertEqual((2, False, False), (document["contract"], document["ok"], document["retryable"]))
        self.assertNotIn("SECRET", json.dumps(document))

    def test_a_prompt_refused_by_the_rule_is_not_retryable_and_exits_with_one(self):
        self.endpoints(ned=self.record(context=10))
        code, out, err = self.ask(prompt=b"a" * 21)
        self.assertEqual((1, ""), (code, err))
        self.assertFalse(json.loads(out)["retryable"])

    def test_the_rule_runs_after_the_options_and_the_model_are_validated(self):
        self.endpoints(ned=self.record(context=10))
        big = b"a" * 1000
        self.refused("--context", "11", prompt=big, contains="--context")
        self.refused("--context", "007", prompt=big, contains="--context")
        self.refused("--model", "not-configured:1b", prompt=big, contains="--model")
        self.refused("--model", "nomic-embed-text", prompt=big, contains="other kind")

    def test_the_rule_runs_after_the_schema_is_read(self):
        self.endpoints(ned=self.record(context=10))
        with open(os.path.join(self.root, "docs", "schema.json"), "w") as handle:
            handle.write("not json")
        self.refused("--schema", "docs/schema.json", prompt=b"a" * 1000, contains="schema")

    def test_the_largest_prompt_is_refused_by_the_rule_and_a_large_window_sends_it(self):
        self.endpoints(ned=self.record(context=10))
        self.too_large(b"a" * 262144)
        self.endpoints(ned=self.record(context=200000))
        self.sent(b"a" * 262144)

    def test_a_blank_prompt_is_still_refused_before_the_rule(self):
        self.endpoints(ned=self.record(context=1))
        self.refused(prompt=b"   \n", contains="empty")

    def test_embed_is_not_subject_to_the_rule(self):
        self.endpoints(ned=self.record(context=10, embedding_model="nomic-embed-text"))
        self.fake.reply({"embeddings": [[0.5, 0.25]], "model": "nomic-embed-text"})
        texts = json.dumps({"texts": ["a" * 5000]}).encode()
        code, out, err = self.ask(command="embed", prompt=texts)
        self.assertEqual((0, ""), (code, err))
        self.assertEqual(1, len(self.fake.requests))

    def test_the_count_check_still_runs_for_a_prompt_the_rule_lets_through(self):
        self.endpoints(ned=self.record(context=100))
        body = chat("an answer", prompt_eval_count=100)
        self.fake.reply(body)
        document = self.failed(prompt=b"a" * 50, error="vendor_error", detail="context_overflow")
        self.assertEqual("the prompt does not fit the context window", document["message"])


if __name__ == "__main__":
    unittest.main()
