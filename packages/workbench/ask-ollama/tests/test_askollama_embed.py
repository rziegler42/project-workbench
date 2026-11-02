"""The `embed` argument (the section "`embed`" of `docs/specs/ask-ollama.md`; checklist item 10 there). Plan
`2026-11-01-ask-ollama-bridge`, increment E. The server is a fake on the loopback address that records what it receives."""

import json
import socket
import unittest
import unittest.mock

import support_ollama


def embedding(vectors=None, **fields):
    """The body of a finished embedding reply of the server."""
    body = {"model": "nomic-embed-text", "prompt_eval_count": 7,
            "embeddings": vectors if vectors is not None else [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]}
    body.update(fields)
    return body


def grid(count, dimension):
    """`count` vectors of `dimension` numbers that print long, so that a batch is large."""
    return [[(row * dimension + column + 1) / 7.0 for column in range(dimension)] for row in range(count)]


class Embed(support_ollama.Bridge):
    def setUp(self):
        super().setUp()
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text"))
        self.fake.reply(embedding())

    def embed(self, *args, texts=("alpha", "beta"), raw=None):
        data = raw if raw is not None else json.dumps({"texts": list(texts)}, ensure_ascii=False).encode("utf-8")
        return self.ask(*args, prompt=data, command="embed")

    def result(self, *args, **kwargs):
        """The one object an embedding call printed, after the checks every call must pass."""
        code, out, err = self.embed(*args, **kwargs)
        self.assertEqual("", err)
        self.assertTrue(out.endswith("\n") and "\n" not in out[:-1], "not one line")
        self.assertLessEqual(len(out.encode()), self.helper.MAX_OBJECT)
        document = json.loads(out)
        self.assertEqual(code, 0 if document["ok"] else 1)
        self.assertEqual((1, "ollama"), (document["contract"], document["vendor"]))
        self.assertNotIn("127.0.0.1", out)
        if not document["ok"]:  # a success holds digits that may spell the port by chance
            self.assertNotIn(str(self.fake.port), out)
        return document

    def bad(self, *args, error, detail=None, retryable=False, **kwargs):
        document = self.result(*args, **kwargs)
        self.assertEqual((False, error, detail, retryable),
                         (document["ok"], document["error"], document["detail"], document["retryable"]), document)
        self.assertEqual({"contract", "ok", "vendor", "error", "detail", "retryable", "message"}, set(document))
        self.assertNotIn("vectors", document)
        return document

    def unusable(self, body, **spec):
        self.fake.reply(body, **spec)
        return self.bad(error="vendor_error", detail="unusable_reply")

    def refused_embed(self, *args, contains="", **kwargs):
        before = len(self.fake.requests)
        code, out, err = self.embed(*args, **kwargs)
        self.assertEqual((1, ""), (code, out), err)
        self.assertTrue(err.startswith("refused: ") and err.count("\n") == 1, err)
        self.assertIn(contains, err)
        self.assertEqual(before, len(self.fake.requests), "a request was sent")
        self.assertNotIn("127.0.0.1", err)
        self.assertNotIn(str(self.fake.port), err)
        return err


class Request(Embed):
    def test_the_request_is_exactly_the_documented_post(self):
        self.assertTrue(self.result()["ok"])
        (request,) = self.fake.requests
        self.assertEqual(("POST", "/api/embed"), (request["method"], request["path"]))
        names = [name for name, value in request["headers"]]
        self.assertEqual(["Host", "Content-Type", "Content-Length", "Accept", "Connection", "User-Agent"], names)
        headers = dict(request["headers"])
        self.assertEqual("127.0.0.1:%d" % self.fake.port, headers["Host"])
        self.assertEqual(("application/json", "application/json", "close", "ask-ollama/1", str(len(request["body"]))),
                         (headers["Content-Type"], headers["Accept"], headers["Connection"], headers["User-Agent"],
                          headers["Content-Length"]))
        self.assertEqual({"model": "nomic-embed-text", "input": ["alpha", "beta"], "truncate": False,
                          "options": {"num_ctx": 8192}}, json.loads(request["body"]))

    def test_the_context_of_the_model_is_the_window_that_is_sent(self):
        self.assertTrue(self.result()["ok"])
        self.assertEqual({"num_ctx": 8192}, json.loads(self.fake.requests[-1]["body"])["options"])
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text", context=2048))
        self.assertTrue(self.result()["ok"])
        self.assertEqual({"num_ctx": 2048}, json.loads(self.fake.requests[-1]["body"])["options"])

    def test_nothing_of_the_record_but_the_destination_is_sent(self):
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text", location="owner-network", default_model="chat-one",
                                       context=8192))
        self.assertTrue(self.result()["ok"])
        request = self.fake.requests[-1]
        text = request["body"].decode() + "".join(name + value for name, value in request["headers"] if name != "Host")
        for word in ("owner-network", "chat-one", "ned", "this-machine", "authenticated", "location"):
            self.assertNotIn(word, text, word)
        self.assertEqual({"model", "input", "truncate", "options"}, set(json.loads(request["body"])))

    def test_texts_are_sent_as_given_and_in_order_with_escapes(self):
        texts = ["zeta", "alpha é \U0001f600", 'quote " and \\ and \n newline', "<script>$(id)</script>"]
        self.fake.reply(embedding(grid(4, 3)))
        self.assertTrue(self.result(texts=texts)["ok"])
        self.assertEqual(texts, json.loads(self.fake.requests[-1]["body"])["input"])

    def test_the_model_is_the_option_then_the_embedding_model_of_the_record_and_never_the_chat_model(self):
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text", default_model="chat-one"))
        self.result()
        self.assertEqual("nomic-embed-text", json.loads(self.fake.requests[-1]["body"])["model"])
        self.result("--model", "mxbai-embed-large")
        self.assertEqual("mxbai-embed-large", json.loads(self.fake.requests[-1]["body"])["model"])
        # A namespaced name can be given by the record only; the option follows the contract's rule, which has no "/".
        self.endpoints(ned=self.record(embedding_model="library/some-model:latest"))
        self.result()
        self.assertEqual("library/some-model:latest", json.loads(self.fake.requests[-1]["body"])["model"])
        self.refused_embed("--model", "library/some-model", contains="--model")

    def test_a_record_with_no_embedding_model_needs_the_option(self):
        self.endpoints(ned=self.record(default_model="chat-one"))
        self.refused_embed(contains="no embedding model is named")
        self.assertTrue(self.result("--model", "nomic-embed-text")["ok"])

    def test_the_server_option_selects_the_record(self):
        self.endpoints(default="a", a=self.record(embedding_model="model-a"), b=self.record(embedding_model="model-b"))
        self.result()
        self.assertEqual("model-a", json.loads(self.fake.requests[-1]["body"])["model"])
        self.result("--server", "b")
        self.assertEqual("model-b", json.loads(self.fake.requests[-1]["body"])["model"])
        err = self.refused_embed("--server", "nobody", contains="no endpoint record")
        self.assertNotIn("nobody", err)

    def test_the_options_of_ask_that_do_not_apply_are_unknown_options(self):
        for option, value in (("--effort", "low"), ("--root", "docs"), ("--schema", "docs/plan.md"), ("--bogus", "x"),
                              ("-x", "y")):
            self.refused_embed(option, value, contains="is not an option of embed")

    def test_the_options_that_apply_are_checked_as_for_ask(self):
        self.refused_embed("--model", "bad name", contains="--model")
        self.refused_embed("--model", "a..b", contains="--model")
        self.refused_embed("--timeout", "0", contains="--timeout")
        self.refused_embed("--timeout", "3601", contains="--timeout")
        self.refused_embed("--timeout", contains="needs a value")
        self.refused_embed("--server", "Bad Name", contains="--server")
        self.refused_embed("--model", "a-model", "--model", "b-model", contains="twice")
        self.refused_embed("positional", contains="positional")

    def test_confine_is_accepted_and_changes_nothing(self):
        plain = self.result()
        confined = self.result("--confine")
        self.assertEqual(plain, confined)
        self.assertEqual(self.fake.requests[0]["body"], self.fake.requests[1]["body"])


class Input(Embed):
    """What is on standard input is checked, and refused, before any connection is made."""

    def test_the_input_is_one_object_with_a_list_of_texts_and_nothing_else(self):
        for raw in (b"", b"  \n", b"not json", b"[]", b'["a"]', b"null", b'"a"', b"1", b"{}", b'{"text": ["a"]}',
                    b'{"texts": ["a"], "extra": 1}', b'{"texts": ["a"], "texts": ["b"]}', b'{"texts": "a"}', b'{"texts": null}',
                    b'{"texts": {"a": "b"}}', b'{"texts": []}', b'{"texts": ["a"]} {"texts": ["b"]}', b'{"texts": ["a"]',
                    b'\xef\xbb\xbf{"texts": ["a"]}', b"\xff\xfe", b'{"texts": ["a", NaN]}'):
            self.refused_embed(raw=raw)

    def test_each_text_is_a_string_with_a_visible_character(self):
        for texts in ([1], [None], [True], [["a"]], [{"a": 1}], ["a", 2], [""], [" "], ["\n\t \r"], ["a", ""], [" "]):
            self.refused_embed(raw=json.dumps({"texts": texts}).encode())

    def test_a_string_with_a_lone_surrogate_is_refused(self):
        self.refused_embed(raw=b'{"texts": ["a\\ud800b"]}')
        self.refused_embed(raw=b'{"texts": ["a", "\\udfff"]}')
        self.fake.reply(embedding([[0.1, 0.2]]))
        self.assertEqual(0, self.embed(raw=b'{"texts": ["\\ud83d\\ude00"]}')[0])

    def test_a_batch_of_100_is_taken_and_101_is_refused(self):
        self.fake.reply(embedding(grid(100, 2)))
        self.assertEqual(100, len(self.result(texts=["t%d" % n for n in range(100)])["vectors"]))
        self.refused_embed(texts=["t%d" % n for n in range(101)])

    def test_a_text_of_32768_bytes_is_taken_and_one_byte_more_is_refused(self):
        self.fake.reply(embedding([[0.1, 0.2]]))
        self.assertTrue(self.result(texts=["a" * 32768])["ok"])
        self.refused_embed(texts=["a" * 32769])
        self.assertTrue(self.result(texts=["é" * 16384])["ok"])
        self.refused_embed(texts=["é" * 16385])
        self.assertTrue(self.result(texts=["\U0001f600" * 8192])["ok"])
        self.refused_embed(texts=["\U0001f600" * 8193])

    def test_the_input_is_taken_at_262144_bytes_and_refused_one_byte_over(self):
        body = json.dumps({"texts": ["a" * 32768] * 7}).encode()
        self.fake.reply(embedding(grid(7, 2)))
        self.assertTrue(self.result(raw=body + b" " * (262144 - len(body)))["ok"])
        self.refused_embed(raw=body + b" " * (262145 - len(body)), contains="larger than")

    def test_a_deeply_nested_document_is_refused_and_does_not_crash(self):
        self.refused_embed(raw=b'{"texts": ' + b"[" * 200 + b"]" * 200 + b"}")

    def test_a_run_of_more_than_4300_digits_is_refused_even_inside_a_text(self):
        # The parser's own bound on a whole number applies to the document; the spec lists it among the known limits.
        self.fake.reply(embedding(grid(1, 2)))
        self.assertTrue(self.result(texts=["9" * 4300])["ok"])
        self.refused_embed(texts=["9" * 4301], contains="strict JSON")

    def test_nothing_is_echoed_in_a_refusal(self):
        err = self.refused_embed(raw=b'{"texts": ["SECRET-TEXT", 5]}')
        self.assertNotIn("SECRET-TEXT", err)
        err = self.refused_embed(raw=b'{"SECRET-KEY": ["SECRET-TEXT"]}')
        self.assertNotIn("SECRET", err)

    def test_the_largest_request_that_the_inputs_allow_is_under_the_request_bound(self):
        # An emoji is four bytes on standard input and twelve in the request (a surrogate pair of two six-byte escapes), the
        # worst ratio; the input is bound to 262,144 bytes, so the request cannot pass three times that.
        texts = ["\U0001f600" * 8192] * 7
        self.fake.reply(embedding(grid(7, 2)))
        self.assertTrue(self.result(texts=texts)["ok"])
        sent = len(self.fake.requests[-1]["body"])
        self.assertGreater(sent, 600000)
        self.assertLessEqual(sent, self.helper.MAX_REQUEST)


class Output(Embed):
    def test_the_object_is_exactly_the_documented_shape(self):
        document = self.result()
        self.assertEqual({"contract", "ok", "vendor", "model", "dimension", "vectors", "usage"}, set(document))
        self.assertEqual((1, True, "ollama", "nomic-embed-text", 3), (document["contract"], document["ok"], document["vendor"],
                                                                      document["model"], document["dimension"]))
        self.assertEqual([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], document["vectors"])
        self.assertEqual({"input_tokens": 7}, document["usage"])

    def test_the_numbers_are_printed_as_python_prints_them(self):
        self.fake.reply(b'{"model": "m1", "embeddings": [[1, 0.5, 1e-05, -2.5E+3], [0, 3, 4, 5]]}')
        code, out, err = self.embed()
        self.assertEqual((0, ""), (code, err))
        self.assertIn("[[1, 0.5, 1e-05, -2500.0], [0, 3, 4, 5]]", out)

    def test_the_model_is_the_servers_when_it_fits_the_rule_and_otherwise_the_one_the_call_used(self):
        for reported in ("nomic-embed-text:latest", "library/a-model"):
            self.fake.reply(embedding(model=reported))
            self.assertEqual(reported, self.result()["model"])
        for reported in (None, 5, "", "a b", "x\ny", "a..b", "x" * 129, ["m"]):
            self.fake.reply(embedding(model=reported))
            self.assertEqual("nomic-embed-text", self.result()["model"], reported)
        body = embedding()
        del body["model"]
        self.fake.reply(body)
        self.assertEqual("nomic-embed-text", self.result()["model"])

    def test_the_count_of_tokens_is_a_whole_number_or_null_and_never_makes_a_reply_unusable(self):
        for counted, shown in ((0, 0), (12, 12), (10 ** 12, 10 ** 12), (10 ** 12 + 1, None), (-1, None), (1.5, None),
                               (True, None), ("7", None), (None, None), ([7], None)):
            self.fake.reply(embedding(prompt_eval_count=counted))
            document = self.result()
            self.assertTrue(document["ok"], counted)
            self.assertEqual({"input_tokens": shown}, document["usage"], counted)
        body = embedding()
        del body["prompt_eval_count"]
        self.fake.reply(body)
        self.assertEqual({"input_tokens": None}, self.result()["usage"])

    def test_nothing_else_of_the_servers_reply_is_copied(self):
        self.fake.reply(embedding(note="SECRET-NOTE", total_duration=5, load_duration=6, thinking="SECRET-THINKING",
                                  message={"content": "SECRET-CHAT"}))
        code, out, err = self.embed()
        self.assertEqual((0, ""), (code, err))
        for word in ("SECRET", "total_duration", "duration"):
            self.assertNotIn(word, out)

    def test_a_dimension_of_8192_is_taken_and_8193_is_unusable(self):
        self.fake.reply(embedding([[0.5] * 8192, [0.25] * 8192]))
        document = self.result()
        self.assertEqual((8192, 2), (document["dimension"], len(document["vectors"])))
        self.unusable(embedding([[0.5] * 8193, [0.25] * 8193]))

    def test_a_batch_that_prints_large_but_inside_the_object_bound_is_taken(self):
        self.fake.reply(embedding(grid(60, 1024)))
        texts = ["t%d" % n for n in range(60)]
        document = self.result(texts=texts)
        self.assertEqual((1024, 60), (document["dimension"], len(document["vectors"])))

    def test_a_reply_body_is_read_to_16_mib_for_an_embedding_where_ask_reads_4(self):
        body = embedding(junk="x" * 5000000)
        self.assertGreater(len(json.dumps(body)), self.helper.MAX_BODY)
        self.fake.reply(body)
        self.assertTrue(self.result()["ok"])
        self.fake.reply(b"x" * (self.helper.MAX_EMBED_BODY + 1))
        self.bad(error="vendor_error", detail="reply_too_large")

    def test_a_batch_whose_object_would_pass_2000000_bytes_is_reply_too_large_and_not_a_smaller_batch(self):
        self.fake.reply(embedding(grid(20, 8192)))
        self.assertGreater(len(json.dumps(grid(20, 8192))), 2000000)
        document = self.bad(error="vendor_error", detail="reply_too_large", texts=["t%d" % n for n in range(20)])
        self.assertEqual("the server returned more than the bridge accepts", document["message"])


class Unusable(Embed):
    """A success status whose body is not a set of vectors that fit the texts."""

    def test_a_body_that_is_not_one_object_is_unusable(self):
        for body in (b"", b"not json", b"[]", b"[[0.1]]", b"null", b'{"embeddings": [[0.1], [0.2]]', b"\xff",
                     b'{"embeddings": [[1],[2]], "embeddings": [[1],[2]]}'):
            self.unusable(body)

    def test_a_missing_or_wrongly_typed_list_of_vectors_is_unusable(self):
        for vectors in (None, "x", 5, {"a": [1]}, [], [[]], [[], []], [None, None], ["a", "b"], [5, 6], [[0.1], None],
                        [{"a": 1}, {"a": 2}]):
            self.unusable({"model": "m", "embeddings": vectors})
        self.unusable({"model": "m"})
        self.unusable({"model": "m", "embedding": [[0.1], [0.2]]})

    def test_a_vector_with_a_value_that_is_not_a_finite_number_is_unusable(self):
        for vector in ([0.1, "0.2"], [0.1, None], [0.1, True], [0.1, False], [0.1, [0.2]], [0.1, {"a": 1}], ["x", "y"]):
            self.unusable({"model": "m", "embeddings": [[0.1, 0.2], vector]})
        for literal in (b"NaN", b"Infinity", b"-Infinity", b"1e999", b"-1e999"):
            self.unusable(b'{"embeddings": [[0.1, 0.2], [0.1, ' + literal + b"]]}")

    def test_vectors_of_different_lengths_are_unusable(self):
        self.unusable(embedding([[0.1, 0.2, 0.3], [0.4, 0.5]]))
        self.unusable(embedding([[0.1], [0.4, 0.5]]))

    def test_a_count_of_vectors_different_from_the_count_of_texts_is_unusable(self):
        self.unusable(embedding([[0.1, 0.2]]))
        self.unusable(embedding([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]))
        self.fake.reply(embedding([[0.1, 0.2]]))
        self.assertTrue(self.result(texts=["only one"])["ok"])

    def test_a_chat_reply_sent_to_the_embedding_path_is_unusable(self):
        self.unusable(support_ollama.chat("not a vector"))

    def test_a_body_cut_short_is_unusable(self):
        body = json.dumps(embedding()).encode()
        self.unusable(body[:20], declare_length=len(body))

    def test_a_reply_cut_by_a_reset_after_it_began_is_unusable(self):
        self.fake.reply(embedding(grid(2, 2000)), abort=True)
        self.bad(error="vendor_error", detail="unusable_reply")

    def test_the_chat_only_checks_do_not_apply(self):
        for fields in ({"done": False}, {"done_reason": "length"}, {"done": "no"}):
            self.fake.reply(embedding(**fields))
            self.assertTrue(self.result()["ok"], fields)
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text", context=5))
        self.fake.reply(embedding(prompt_eval_count=500))
        self.assertTrue(self.result()["ok"])


class Errors(Embed):
    def test_a_missing_model_is_model_unavailable(self):
        self.fake.reply({"error": "model 'nomic-embed-text' not found"}, status=404)
        document = self.bad(error="model_unavailable")
        self.assertEqual("the server does not have the model", document["message"])
        self.assertNotIn("nomic", json.dumps(document))

    def test_a_model_that_cannot_embed_is_model_unavailable_with_its_own_message(self):
        # Read from a real server (version 0.35.1): a chat model on /api/embed answers 501 with this text.
        self.fake.reply({"error": "This server does not support embeddings. Start it with `--embeddings`"}, status=501)
        document = self.bad(error="model_unavailable")
        self.assertEqual("the model cannot produce embeddings", document["message"])
        self.fake.reply({"error": "something else"}, status=501)
        self.bad(error="vendor_error", detail="bad_exit")

    def test_a_text_too_long_for_the_model_is_context_overflow_and_nothing_is_returned(self):
        for text in ("the input length exceeds the context length", "Input is TOO LONG for this model",
                     "exceeds the Context Length of the model"):
            self.fake.reply({"error": text}, status=400)
            document = self.bad(error="vendor_error", detail="context_overflow")
            self.assertEqual("the input does not fit the context window", document["message"])

    def test_every_other_status_is_bad_exit_and_a_400_about_something_else_never_names_a_chat_cause(self):
        for status, body in ((400, {"error": "something else"}), (400, {"error": "does not support thinking"}),
                             (400, {"error": "invalid format"}), (400, {"error": "schema"}), (404, {"error": "no such route"}),
                             (401, {"error": "x"}), (403, {}), (429, {"error": "busy"}), (500, {"error": "boom"}),
                             (503, {"error": "busy"}), (302, {"error": "too long"}), (300, {"error": "not found"})):
            self.fake.reply(body, status=status)
            self.bad(error="vendor_error", detail="bad_exit")

    def test_an_error_status_whose_body_is_not_the_expected_shape_is_bad_exit_and_never_unusable(self):
        for body in (b"", b"not json", b"[]", b'{"error": 5}', b'{"error": null}', b'{"error": ["too long"]}', b"\xff"):
            self.fake.reply(body, status=400)
            self.bad(error="vendor_error", detail="bad_exit")

    def test_a_body_over_its_bound_is_reply_too_large_whatever_the_status(self):
        for status in (200, 500):
            self.fake.reply(b"x" * (self.helper.MAX_EMBED_BODY + 1), status=status)
            self.bad(error="vendor_error", detail="reply_too_large")

    def test_a_connection_that_is_refused_or_closed_with_no_answer_is_vendor_unreachable(self):
        self.fake.reply(drop=True)
        document = self.bad(error="vendor_unreachable", retryable=True)
        self.assertEqual("the server did not answer", document["message"])
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text", port=port))
        self.bad(error="vendor_unreachable", retryable=True)

    def test_a_server_that_accepts_and_never_replies_ends_at_the_timeout(self):
        self.fake.reply(embedding(), delay=5)
        document = self.bad("--timeout", "1", error="timeout", retryable=True)
        self.assertEqual("the server did not finish in time", document["message"])

    def test_a_certificate_that_is_not_trusted_is_refused_and_nothing_is_sent(self):
        self.fake.close()
        self.fake = support_ollama.Fake(support_ollama.server_context("trusted"))
        self.addCleanup(self.fake.close)
        self.endpoints(ned=self.record(scheme="https", embedding_model="nomic-embed-text"))
        document = self.bad(error="vendor_unreachable", retryable=False)
        self.assertEqual("the server's certificate was not accepted", document["message"])
        self.assertEqual([], self.fake.requests)

    def test_a_trusted_server_over_https_is_taken(self):
        self.fake.close()
        self.fake = support_ollama.Fake(support_ollama.server_context("trusted"))
        self.addCleanup(self.fake.close)
        self.fake.reply(embedding())
        self.endpoints(ned=self.record(scheme="https", embedding_model="nomic-embed-text"))
        with unittest.mock.patch.object(self.helper, "tls_context", lambda: support_ollama.trusting("trusted")):
            self.assertTrue(self.result()["ok"])
        self.assertEqual("/api/embed", self.fake.requests[-1]["path"])

    def test_the_failure_objects_never_carry_the_servers_words_the_texts_or_the_address(self):
        self.fake.reply({"error": "SECRET-ERROR for host 127.0.0.1 text SECRET-TEXT"}, status=500)
        code, out, err = self.embed(texts=["SECRET-TEXT"])
        self.assertEqual((1, ""), (code, err))
        for word in ("SECRET", "127.0.0.1"):
            self.assertNotIn(word, out)


class Whole(Embed):
    def test_the_project_and_the_store_are_unchanged_after_every_kind_of_call(self):
        before = (self.tree(self.root), self.tree(self.store))
        for reply in ({"body": embedding()}, {"body": b"not json"}, {"body": embedding(), "status": 500}, {"drop": True}):
            self.fake.reply(**reply)
            self.embed()
        self.refused_embed(raw=b"")
        self.assertEqual(before, (self.tree(self.root), self.tree(self.store)))

    def test_ask_and_check_are_untouched_by_the_new_argument(self):
        self.endpoints(ned=self.record(embedding_model="nomic-embed-text"))
        self.fake.reply(support_ollama.chat("the answer"))
        document = self.document()
        self.assertEqual((2, True, "the answer"), (document["contract"], document["ok"], document["reply"]))
        self.assertEqual("/api/chat", self.fake.requests[-1]["path"])
        code, out, err = self.ask(command="check")
        self.assertEqual((0, ""), (code, err))
        self.assertTrue(out.startswith("ned scheme=http"), out)

    def test_an_unknown_argument_is_refused_with_a_usage_that_names_embed(self):
        for argument in ("embedding", "EMBED", ""):
            code, out, err = self.ask(command=argument)
            self.assertEqual((1, ""), (code, out))
            self.assertIn("embed", err)
            self.assertTrue(err.startswith("refused: ") and err.count("\n") == 1, err)


if __name__ == "__main__":
    unittest.main()
