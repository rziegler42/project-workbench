"""The context window, a reply that was cut, a thinking model and the order of the conditions (the section "Context window,
truncation and thinking" and the order in "Errors" of `docs/specs/ask-ollama.md`). Plan `2026-11-01-ask-ollama-bridge`,
increment D. The server is a fake on the loopback address."""

import json
import unittest
import unittest.mock

import support_ollama
from support_ollama import chat


class Window(support_ollama.Bridge):
    """A prompt that fills the window of the record is reported and nothing is returned."""

    def overflow(self, body, *args):
        document = self.failed(*args, error="vendor_error", detail="context_overflow")
        self.assertEqual("the prompt does not fit the context window", document["message"])
        self.assertNotIn("reply", document)
        self.assertNotIn(body["message"]["content"], json.dumps(document))
        return document

    def test_a_prompt_that_reaches_the_window_is_context_overflow_and_nothing_is_returned(self):
        self.endpoints(ned=self.record(context=4096))
        for counted in (4096, 4097, 10 ** 6):
            body = chat("a perfectly good answer", prompt_eval_count=counted)
            self.fake.reply(body)
            self.overflow(body)

    def test_a_prompt_below_the_window_is_returned(self):
        self.endpoints(ned=self.record(context=4096))
        for counted in (0, 1, 4095):
            self.fake.reply(chat("the answer", prompt_eval_count=counted))
            document = self.document()
            self.assertEqual(("the answer", counted), (document["reply"], document["usage"]["input_tokens"]))

    def test_the_window_is_the_one_of_the_record_chosen_with_server(self):
        self.endpoints(default="small", small=self.record(context=100), large=self.record(context=100000))
        body = chat("answer", prompt_eval_count=5000)
        self.fake.reply(body)
        self.overflow(body)
        self.assertTrue(self.document("--server", "large")["ok"])

    def test_a_count_of_a_trillion_is_compared_and_one_more_is_not_a_count(self):
        self.endpoints(ned=self.record(context=4096))
        body = chat("an answer", prompt_eval_count=10 ** 12)
        self.fake.reply(body)
        self.overflow(body)
        self.fake.reply(chat("an answer", prompt_eval_count=10 ** 12 + 1))
        document = self.document()
        self.assertEqual(("an answer", None), (document["reply"], document["usage"]["input_tokens"]))

    def test_a_window_of_one_makes_every_prompt_with_a_count_an_overflow(self):
        self.endpoints(ned=self.record(context=1))
        body = chat("an answer", prompt_eval_count=1)
        self.fake.reply(body)
        self.overflow(body)
        self.fake.reply(chat("an answer", prompt_eval_count=0))
        self.assertTrue(self.document()["ok"])

    def test_every_call_has_a_window_that_is_sent_and_checked_against(self):
        self.assertTrue(self.document()["ok"])
        self.assertEqual({"num_ctx": 8192}, json.loads(self.fake.requests[-1]["body"])["options"])
        body = chat("the answer", prompt_eval_count=10 ** 9)
        self.fake.reply(body)
        self.overflow(body)

    def test_when_the_reply_has_no_usable_count_the_check_cannot_run_and_does_not(self):
        self.endpoints(ned=self.record(context=100))
        for counted in (None, "5000", -1, 5000.5, True, [5000], 10 ** 13):
            body = chat("the answer", prompt_eval_count=counted)
            self.fake.reply(body)
            document = self.document()
            self.assertEqual("the answer", document["reply"], counted)
            self.assertIsNone(document["usage"]["input_tokens"], counted)
        body = chat("the answer")
        del body["prompt_eval_count"]
        self.fake.reply(body)
        self.assertEqual("the answer", self.document()["reply"])

    def test_a_reply_that_is_not_done_is_judged_before_the_window(self):
        self.endpoints(ned=self.record(context=100))
        self.fake.reply(chat("the answer", done=False, prompt_eval_count=5000))
        self.failed(error="vendor_error", detail="unusable_reply")

    def test_an_error_status_is_judged_by_its_status_and_not_by_the_window(self):
        self.endpoints(ned=self.record(context=100))
        self.fake.reply(chat("x", prompt_eval_count=5000), status=500)
        self.failed(error="vendor_error", detail="bad_exit")


class Cut(support_ollama.Bridge):
    """A reply that the server stopped at its length limit is reported even if some text came back."""

    def cut(self, *args):
        document = self.failed(*args, error="vendor_error", detail="reply_cut")
        self.assertEqual("the server stopped the reply at its length limit", document["message"])
        self.assertNotIn("reply", document)
        return document

    def test_a_reply_stopped_at_the_length_limit_is_reply_cut_even_with_text(self):
        self.fake.reply(chat("half an answer that", done_reason="length"))
        document = self.cut()
        self.assertNotIn("half an answer", json.dumps(document))

    def test_any_other_reason_or_none_is_a_finished_reply(self):
        for reason in ("stop", "load", "unload", "", None, "Length", "length ", 5, ["length"]):
            self.fake.reply(chat("the answer", done_reason=reason))
            self.assertEqual("the answer", self.document()["reply"], reason)
        body = chat("the answer")
        del body["done_reason"]
        self.fake.reply(body)
        self.assertEqual("the answer", self.document()["reply"])

    def test_a_thinking_model_that_spent_its_limit_and_returned_nothing_is_reply_cut_and_names_the_cause(self):
        body = chat("", done_reason="length")
        body["message"]["thinking"] = "SECRET-THINKING I will begin by considering"
        self.fake.reply(body)
        document = self.cut("--effort", "high")
        self.assertNotIn("SECRET-THINKING", json.dumps(document))

    def test_the_window_is_judged_before_the_cut(self):
        self.endpoints(ned=self.record(context=100))
        self.fake.reply(chat("text", done_reason="length", prompt_eval_count=100))
        self.failed(error="vendor_error", detail="context_overflow")
        self.fake.reply(chat("text", done_reason="length", prompt_eval_count=99))
        self.cut()

    def test_a_reply_that_is_not_done_is_judged_before_the_cut(self):
        self.fake.reply(chat("text", done=False, done_reason="length"))
        self.failed(error="vendor_error", detail="unusable_reply")

    def test_the_cut_is_judged_before_the_text_is_looked_at(self):
        for text in ("", " ", "\x00"):
            self.fake.reply(chat(text, done_reason="length"))
            self.cut()

    def test_neither_a_cut_nor_an_overflow_can_be_retried_and_both_are_known_codes_of_the_object(self):
        self.endpoints(ned=self.record(context=100))
        self.fake.reply(chat("t", done_reason="length"))
        self.assertFalse(self.cut()["retryable"])
        self.fake.reply(chat("t", prompt_eval_count=100))
        self.assertFalse(self.failed(error="vendor_error", detail="context_overflow")["retryable"])


class Thinking(support_ollama.Bridge):
    """A reasoning model that returns nothing, and the effort that asks for reasoning."""

    def test_an_empty_reply_with_thinking_text_is_unusable_and_the_thinking_is_in_no_object(self):
        for content in ("", " ", "\n"):
            body = chat(content, done_reason="stop")
            body["message"]["thinking"] = "SECRET-THINKING step by step"
            self.fake.reply(body)
            code, out, err = self.ask("--effort", "medium")
            self.assertEqual((1, ""), (code, err))
            document = json.loads(out)
            self.assertEqual(("vendor_error", "unusable_reply", False), (document["error"], document["detail"], document["retryable"]))
            self.assertEqual("the server returned no usable reply", document["message"])
            self.assertNotIn("SECRET-THINKING", out)

    def test_thinking_text_is_never_the_reply_even_when_it_is_the_only_text(self):
        body = {"model": "llama3:8b", "done": True, "done_reason": "stop",
                "message": {"role": "assistant", "thinking": "SECRET-THINKING only", "content": ""}}
        self.fake.reply(body)
        code, out, err = self.ask("--effort", "low")
        self.assertEqual(1, code)
        self.assertNotIn("SECRET-THINKING", out + err)

    def test_the_thinking_text_is_in_no_object_on_a_success_and_in_no_count(self):
        body = chat("the answer")
        body["message"]["thinking"] = "SECRET-THINKING long " * 1000
        body["thinking"] = "SECRET-THINKING top level"
        self.fake.reply(body)
        code, out, err = self.ask("--effort", "high")
        self.assertEqual((0, ""), (code, err))
        self.assertNotIn("SECRET-THINKING", out)
        usage = json.loads(out)["usage"]
        self.assertIsNone(usage["reasoning_output_tokens"])

    def test_each_effort_is_sent_as_think_and_none_leaves_it_out(self):
        self.assertTrue(self.document()["ok"])
        self.assertNotIn("think", json.loads(self.fake.requests[-1]["body"]))
        for level in ("low", "medium", "high"):
            self.assertTrue(self.document("--effort", level)["ok"])
            self.assertEqual(level, json.loads(self.fake.requests[-1]["body"])["think"])

    def test_a_model_that_rejects_the_effort_is_effort_unsupported_with_its_fixed_message(self):
        self.fake.reply({"error": "\"llama3:8b\" does not support thinking"}, status=400)
        document = self.failed("--effort", "low", error="effort_unsupported")
        self.assertEqual("the model does not support this effort", document["message"])
        self.assertNotIn("llama3", json.dumps(document))


class Parser(support_ollama.Bridge):
    """The boundary of the nesting rule, which the tests of the reply exercise only far from the limit."""

    def test_a_document_nested_to_the_limit_is_read_and_one_level_deeper_is_refused(self):
        limit = self.helper.MAX_DEPTH
        self.assertEqual(32, limit)
        self.helper.parse_json(b"[" * limit + b"]" * limit)
        self.helper.parse_json(b'{"a":' * limit + b"1" + b"}" * limit)
        with self.assertRaises(ValueError) as caught:
            self.helper.parse_json(b"[" * (limit + 1) + b"]" * (limit + 1))
        self.assertIn("deeply", str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            self.helper.parse_json(b'{"a":' * (limit + 1) + b"1" + b"}" * (limit + 1))
        self.assertIn("deeply", str(caught.exception))


class Connection(support_ollama.Bridge):
    """A generic operating system error is judged by whether the server had begun to answer, as a reset is."""

    def test_an_operating_system_error_before_the_answer_began_is_vendor_unreachable(self):
        with unittest.mock.patch("http.client.HTTPConnection.getresponse", side_effect=OSError(5, "Input/output error")):
            self.failed(error="vendor_unreachable", retryable=True)

    def test_an_operating_system_error_after_the_answer_began_is_a_reply_cut_short(self):
        def broken(response, *args):
            raise OSError(5, "Input/output error")

        with unittest.mock.patch("http.client.HTTPResponse.read1", broken):
            self.failed(error="vendor_error", detail="unusable_reply")


if __name__ == "__main__":
    unittest.main()
