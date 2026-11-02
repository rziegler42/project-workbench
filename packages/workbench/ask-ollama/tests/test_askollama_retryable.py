"""The retryable statuses 500, 502 and 503 of a bridge to a server (decision `2026-11-02-retryable-server-errors-in-bridges-to-a-server`;
checklist item 22 of `docs/specs/ask-ollama.md`). Plan `2026-11-02-bridge-request-controls`, increment E. The status alone chooses
the row, for a response that was read whole within its bound; every other status and the other rows are as before; the bridge makes
one request and copies nothing of the body."""

import json
import socket
import sys
import unittest

import support_ollama

CONTRACTS = {"ask": 2, "embed": 1, "models": 1}
RETRYABLE = (500, 502, 503)
BODIES = ({"error": "SECRET boom"}, {"error": "SECRET exceeds the available context size"},
          {"error": "SECRET exceed_context_size_error"}, {"error": "SECRET does not support thinking, format and schema"},
          {"error": "SECRET the input length exceeds the context length, too long"}, {"error": "SECRET model not found"},
          {"error": "SECRET does not support embeddings"}, {"error": 5}, {"other": "SECRET"}, [], b"SECRET not json", b"",
          b"\xff\xfe")
NOT_RETRYABLE = (300, 301, 302, 307, 308, 400, 401, 402, 403, 404, 405, 408, 409, 413, 422, 429, 499, 501, 504, 505, 507, 511, 599)


class Base(support_ollama.Bridge):
    def setUp(self):
        super().setUp()
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text"))

    def call(self, command, status, body, **spec):
        """The failure object of one call of `command` against a fake that answers `status` and `body`, after the checks
        every call must pass: exactly one request, one object, the fields of the failure object, and nothing of the body."""
        self.fake.reply(body, status=status, **spec)
        before = len(self.fake.requests)
        if command == "ask":
            code, out, err = self.ask()
        elif command == "embed":
            code, out, err = self.ask(prompt=json.dumps({"texts": ["alpha"]}).encode(), command="embed")
        else:
            code, out, err = self.ask(prompt=b"", command="models")
        where = (command, status, body if isinstance(body, bytes) and len(body) < 40 else type(body).__name__)
        self.assertEqual(("", 1), (err, code), where)
        self.assertEqual(before + 1, len(self.fake.requests), "not exactly one request: %s" % (where,))
        document = json.loads(out)
        self.assertEqual((CONTRACTS[command], False, "ollama"), (document["contract"], document["ok"], document["vendor"]), where)
        self.assertEqual({"contract", "ok", "vendor", "error", "detail", "retryable", "message"}, set(document), where)
        self.assertNotIn("SECRET", out)
        self.assertNotIn("127.0.0.1", out)
        self.assertNotIn(str(self.fake.port), out)
        return document

    def row(self, document, error, detail, retryable, where):
        self.assertEqual((error, detail, retryable), (document["error"], document["detail"], document["retryable"]), where)


class Statuses(Base):
    def test_a_500_502_or_503_is_the_retryable_bad_exit_in_ask_embed_and_models_whatever_the_body(self):
        for command in CONTRACTS:
            for status in RETRYABLE:
                for body in BODIES:
                    document = self.call(command, status, body)
                    self.row(document, "vendor_error", "bad_exit", True, (command, status, body))
                    self.assertEqual("the server answered with an error", document["message"])

    def test_every_other_status_is_a_row_that_is_not_retryable(self):
        for command in CONTRACTS:
            for status in NOT_RETRYABLE:
                document = self.call(command, status, {"error": "x"})
                self.row(document, "vendor_error", "bad_exit", False, (command, status))

    def test_a_501_that_says_a_chat_model_cannot_embed_is_model_unavailable_and_not_retryable(self):
        document = self.call("embed", 501, {"error": "This server does not support embeddings. Start it with `--embeddings`"})
        self.row(document, "model_unavailable", None, False, "embed 501")
        self.assertEqual(self.helper.MESSAGES["not_an_embedder"], document["message"])

    def test_any_other_501_is_bad_exit_and_not_retryable_in_every_command(self):
        for command in CONTRACTS:
            for body in ({"error": "something else"}, {"error": "does not support embedding"}, b"", b"not json"):
                self.row(self.call(command, 501, body), "vendor_error", "bad_exit", False, (command, body))

    def test_the_rows_of_the_400_and_the_404_are_chosen_before_the_status_rule_and_are_as_before(self):
        self.row(self.call("ask", 400, {"error": "exceeds the available context size"}), "vendor_error", "context_overflow", False, "400")
        self.row(self.call("ask", 400, {"error": "does not support thinking"}), "effort_unsupported", None, False, "think")
        self.row(self.call("ask", 400, {"error": "invalid format"}), "vendor_error", "bad_schema", False, "format")
        self.row(self.call("ask", 404, {"error": "model not found"}), "model_unavailable", None, False, "404")
        self.row(self.call("embed", 400, {"error": "the input length exceeds the context length"}), "vendor_error",
                 "context_overflow", False, "embed 400")
        self.row(self.call("embed", 404, {"error": "model not found"}), "model_unavailable", None, False, "embed 404")

    def test_a_5xx_with_the_words_of_another_row_is_still_the_retryable_bad_exit(self):
        self.row(self.call("ask", 500, {"error": "exceeds the available context size"}), "vendor_error", "bad_exit", True, "overflow")
        self.row(self.call("ask", 503, {"error": "model not found, think, format"}), "vendor_error", "bad_exit", True, "words")
        self.row(self.call("embed", 500, {"error": "the input length exceeds the context length"}), "vendor_error", "bad_exit", True,
                 "embed")
        self.row(self.call("embed", 502, {"error": "does not support embeddings"}), "vendor_error", "bad_exit", True, "embed 502")


class Precedence(Base):
    """A body over its bound and a connection cut after the status line are judged before any status."""

    def test_a_body_over_its_bound_is_reply_too_large_and_not_retryable_under_a_5xx(self):
        for command, bound in (("ask", self.helper.MAX_BODY), ("models", self.helper.MAX_BODY)):
            for status in RETRYABLE:
                document = self.call(command, status, b"x" * (bound + 1))
                self.row(document, "vendor_error", "reply_too_large", False, (command, status))
        document = self.call("embed", 502, b"x" * (self.helper.MAX_EMBED_BODY + 1))
        self.row(document, "vendor_error", "reply_too_large", False, "embed")

    def test_a_connection_cut_after_the_status_line_is_unusable_reply_and_not_retryable_under_a_5xx(self):
        for command in CONTRACTS:
            for status in RETRYABLE:
                document = self.call(command, status, {"error": "SECRET boom, a body that is cut"}, abort=True)
                self.row(document, "vendor_error", "unusable_reply", False, (command, status))

    def test_a_body_shorter_than_it_declares_that_ends_in_a_clean_close_is_unusable_reply_under_any_status(self):
        # the connection closed before the declared length: the reply was cut short, so the status does not decide the row
        for command in CONTRACTS:
            for status in RETRYABLE + (404, 501):
                document = self.call(command, status, {"error": "SECRET boom"}, declare_length=500)
                self.row(document, "vendor_error", "unusable_reply", False, (command, status))

    def test_a_complete_json_body_that_is_shorter_than_it_declares_is_not_a_success(self):
        bodies = {"ask": support_ollama.chat("fine"), "embed": {"model": "e", "embeddings": [[0.1, 0.2]], "prompt_eval_count": 1},
                  "models": {"models": [{"name": "llama3:8b"}]}}
        for command, body in bodies.items():
            document = self.call(command, 200, body, declare_length=len(json.dumps(body)) + 50)
            self.row(document, "vendor_error", "unusable_reply", False, command)

    def test_a_content_length_that_is_not_a_usable_number_is_ignored_and_never_a_traceback(self):
        # 5,000 digits: int() refuses more than 4,300, and http.client ignores such a length, so the body is read to the close
        if not 0 < sys.get_int_max_str_digits() < 5000:
            self.skipTest("the interpreter's limit on the digits of an integer is lifted or above 5,000")
        for command in CONTRACTS:
            document = self.call(command, 503, {"error": "SECRET boom"}, declare_length="9" * 5000)
            self.row(document, "vendor_error", "bad_exit", True, command)
            document = self.call(command, 503, {"error": "SECRET boom"}, declare_length="9" * 100)  # a length that int() reads
            self.row(document, "vendor_error", "unusable_reply", False, command)

    def test_a_chunked_reply_that_also_declares_a_content_length_is_read_by_its_chunks(self):
        payload = json.dumps({"error": "boom"}).encode()
        chunked = b"%x\r\n%s\r\n0\r\n\r\n" % (len(payload), payload)
        for command in CONTRACTS:
            document = self.call(command, 503, chunked, headers={"Transfer-Encoding": "chunked"}, declare_length=99999)
            self.row(document, "vendor_error", "bad_exit", True, command)
        success = json.dumps(support_ollama.chat("fine")).encode()
        self.fake.reply(b"%x\r\n%s\r\n0\r\n\r\n" % (len(success), success), headers={"Transfer-Encoding": "chunked"},
                        declare_length=99999)
        self.assertTrue(json.loads(self.ask()[1])["ok"])

    def test_a_304_that_declares_a_content_length_is_judged_by_its_status(self):
        for command in CONTRACTS:
            document = self.call(command, 304, b"", declare_length=500)
            self.row(document, "vendor_error", "bad_exit", False, command)

    def test_a_content_length_that_int_reads_but_isdigit_does_not_is_still_a_declared_length(self):
        for text in ("+500", "5_00"):
            for command in CONTRACTS:
                document = self.call(command, 503, {"error": "SECRET boom"}, declare_length=text)
                self.row(document, "vendor_error", "unusable_reply", False, (command, text))

    def test_a_body_that_is_exactly_as_long_as_it_declares_is_read_whole(self):
        self.fake.reply({"error": "boom"}, status=503)
        document = json.loads(self.ask()[1])
        self.row(document, "vendor_error", "bad_exit", True, "exact length")


class Others(Base):
    def run_command(self, command, *args):
        if command == "ask":
            return self.ask(*args)
        if command == "embed":
            return self.ask(*args, prompt=json.dumps({"texts": ["alpha"]}).encode(), command="embed")
        return self.ask(*args, prompt=b"", command="models")

    def test_a_close_with_no_answer_is_vendor_unreachable_and_retryable_in_each_command(self):
        for command in CONTRACTS:
            self.fake.reply(drop=True)
            code, out, err = self.run_command(command)
            document = json.loads(out)
            self.assertEqual((1, "vendor_unreachable", None, True), (code, document["error"], document["detail"],
                                                                      document["retryable"]), command)

    def test_a_refused_connection_is_vendor_unreachable_and_retryable_in_each_command(self):
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        self.endpoints(ned=self.record(port=port, embedding_model="nomic-embed-text"))
        for command in CONTRACTS:
            code, out, err = self.run_command(command)
            document = json.loads(out)
            self.assertEqual((1, "vendor_unreachable", None, True), (code, document["error"], document["detail"],
                                                                      document["retryable"]), command)

    def test_a_server_that_does_not_finish_is_a_timeout_and_retryable_in_each_command(self):
        for command in CONTRACTS:
            self.fake.reply(support_ollama.chat("late"), delay=5)
            code, out, err = self.run_command(command, "--timeout", "1")
            document = json.loads(out)
            self.assertEqual((1, "timeout", None, True), (code, document["error"], document["detail"], document["retryable"]),
                             command)

    def test_a_success_status_is_never_retryable(self):
        self.fake.reply(support_ollama.chat("fine"))
        self.assertTrue(json.loads(self.ask()[1])["ok"])
        self.fake.reply(b"not json", status=200)
        document = json.loads(self.ask()[1])
        self.assertEqual(("unusable_reply", False), (document["detail"], document["retryable"]))

    def test_the_helper_never_retries_a_5xx_by_itself(self):
        before = len(self.fake.requests)
        self.fake.reply({"error": "boom"}, status=503)
        self.ask()
        self.assertEqual(before + 1, len(self.fake.requests))


if __name__ == "__main__":
    unittest.main()
