"""`ask-ollama models`: which configured models the server has and which of its models are not configured (the section "`models`"
of `docs/specs/ask-ollama.md`, checklist item 16). Plan `2026-11-02-bridge-model-configurations`, increment F. One bodiless `GET`
to the fixed path `/api/tags`, one object of its own contract 1 with names only, and the failure objects and bounds of the other
arguments. The server is a fake on the loopback address."""

import io
import json
import socket
import unittest

import support_ollama

CHAT = {"kind": "chat", "context": 8192}
EMBEDDING = {"kind": "embedding", "context": 8192}


def tags(*names, **extra):
    """The body of the server's list of models, with an entry for each name."""
    return {"models": [dict({"name": name, "size": 1234, "digest": "abc"}, **extra) for name in names]}


class Models(support_ollama.Bridge):
    def setUp(self):
        super().setUp()
        self.configure({"alpha:1b": dict(CHAT), "beta:7b": dict(CHAT), "embed-one": dict(EMBEDDING)})

    def configure(self, models, **fields):
        self.endpoints(ned=self.record(models=models, default_model=None, **fields))

    def models(self, *args):
        """``(code, standard output, standard error)`` of ``ask-ollama models``; standard input is empty."""
        return self.ask(*args, command="models", prompt=b"")

    def result(self, *args):
        """The one object a call printed, after the checks every call must pass."""
        code, out, err = self.models(*args)
        self.assertEqual("", err)
        self.assertTrue(out.endswith("\n") and "\n" not in out[:-1], "not one line")
        self.assertLessEqual(len(out.encode()), self.helper.MAX_OBJECT)
        document = json.loads(out)
        self.assertEqual(code, 0 if document["ok"] else 1)
        self.assertEqual((1, "ollama"), (document["contract"], document["vendor"]))
        self.assertNotIn("127.0.0.1", out)
        self.assertNotIn(str(self.fake.port), out)
        return document

    def bad(self, *args, error, detail=None, retryable=False):
        document = self.result(*args)
        self.assertEqual((False, error, detail, retryable),
                         (document["ok"], document["error"], document["detail"], document["retryable"]), document)
        self.assertEqual({"contract", "ok", "vendor", "error", "detail", "retryable", "message"}, set(document))
        return document

    def refused_models(self, *args, contains=""):
        before = len(self.fake.requests)
        code, out, err = self.models(*args)
        self.assertEqual((1, ""), (code, out), err)
        self.assertTrue(err.startswith("refused: ") and err.count("\n") == 1, err)
        self.assertIn(contains, err)
        self.assertEqual(before, len(self.fake.requests), "a request was sent")
        self.assertNotIn("127.0.0.1", err)
        self.assertNotIn(str(self.fake.port), err)
        return err


class Request(Models):
    def test_the_request_is_exactly_one_bodiless_get_of_the_fixed_path(self):
        self.fake.reply(tags("alpha:1b"))
        self.assertTrue(self.result()["ok"])
        (request,) = self.fake.requests
        self.assertEqual(("GET", "/api/tags", b""), (request["method"], request["path"], request["body"]))
        self.assertEqual(["Host", "Accept", "Connection", "User-Agent"], [name for name, value in request["headers"]])
        headers = dict(request["headers"])
        self.assertEqual(("127.0.0.1:%d" % self.fake.port, "application/json", "close", "ask-ollama/1"),
                         (headers["Host"], headers["Accept"], headers["Connection"], headers["User-Agent"]))

    def test_nothing_of_the_record_but_the_destination_is_sent(self):
        self.configure({"alpha:1b": dict(CHAT)}, location="owner-network")
        self.fake.reply(tags("alpha:1b"))
        self.assertTrue(self.result()["ok"])
        request = self.fake.requests[-1]
        text = "".join(name + value for name, value in request["headers"] if name != "Host")
        for word in ("owner-network", "alpha", "ned", "authenticated", "location", "context"):
            self.assertNotIn(word, text, word)

    def test_a_record_without_a_default_model_needs_no_model(self):
        self.fake.reply(tags("alpha:1b"))
        self.assertTrue(self.result()["ok"])

    def test_the_server_option_names_the_record(self):
        self.endpoints(default="a", a=self.record(models={"only-a": dict(CHAT)}, default_model=None),
                       b=self.record(models={"only-b": dict(CHAT)}, default_model=None))
        self.fake.reply(tags("only-a", "only-b"))
        self.assertEqual((["only-a"], ["only-b"]), (self.result()["present"], self.result()["unconfigured"]))
        document = self.result("--server", "b")
        self.assertEqual((["only-b"], ["only-a"]), (document["present"], document["unconfigured"]))
        self.refused_models("--server", "nope", contains="no endpoint record")

    def test_standard_input_is_not_read(self):
        class Never(io.BytesIO):
            def read(self, *args):
                raise AssertionError("standard input was read")

        self.fake.reply(tags("alpha:1b"))
        out, err = io.StringIO(), io.StringIO()
        code = self.helper.main(["models"], Never(), out, err, self.root)
        self.assertEqual((0, ""), (code, err.getvalue()))

    def test_it_changes_nothing_in_the_project_or_the_store(self):
        self.fake.reply(tags("alpha:1b"))
        before = (self.tree(self.root), self.tree(self.store))
        self.models()
        self.assertEqual(before, (self.tree(self.root), self.tree(self.store)))


class Output(Models):
    def test_the_object_is_exactly_the_documented_shape(self):
        self.fake.reply(tags("alpha:1b", "gamma"))
        document = self.result()
        self.assertEqual({"contract", "ok", "vendor", "present", "missing", "unconfigured", "skipped"}, set(document))
        self.assertEqual((["alpha:1b"], ["beta:7b", "embed-one"], ["gamma"], 0),
                         (document["present"], document["missing"], document["unconfigured"], document["skipped"]))

    def test_present_and_missing_follow_the_files_order_and_unconfigured_the_servers(self):
        self.fake.reply(tags("zeta", "embed-one", "yankee", "beta:7b", "alpha:1b", "xray"))
        document = self.result()
        self.assertEqual(["alpha:1b", "beta:7b", "embed-one"], document["present"])
        self.assertEqual([], document["missing"])
        self.assertEqual(["zeta", "yankee", "xray"], document["unconfigured"])

    def test_every_configured_model_is_present_or_missing_and_never_both(self):
        self.fake.reply(tags("beta:7b"))
        document = self.result()
        self.assertEqual((["beta:7b"], ["alpha:1b", "embed-one"]), (document["present"], document["missing"]))

    def test_a_server_with_no_models_gives_all_missing(self):
        self.fake.reply({"models": []})
        document = self.result()
        self.assertEqual(([], ["alpha:1b", "beta:7b", "embed-one"], [], 0),
                         (document["present"], document["missing"], document["unconfigured"], document["skipped"]))

    def test_names_are_compared_as_exact_text(self):
        self.fake.reply(tags("Alpha:1b", "alpha:1b:latest", "beta:7b "))
        document = self.result()
        self.assertEqual([], document["present"])
        self.assertEqual(["alpha:1b", "beta:7b", "embed-one"], document["missing"])
        self.assertEqual(["Alpha:1b", "alpha:1b:latest"], document["unconfigured"])
        self.assertEqual(1, document["skipped"])

    def test_a_name_listed_twice_is_listed_once(self):
        self.fake.reply(tags("gamma", "gamma", "alpha:1b", "alpha:1b"))
        document = self.result()
        self.assertEqual((["alpha:1b"], ["gamma"]), (document["present"], document["unconfigured"]))

    def test_a_name_listed_twice_keeps_its_first_place(self):
        self.fake.reply(tags("gamma", "x", "gamma"))
        self.assertEqual(["gamma", "x"], self.result()["unconfigured"])
        self.fake.reply(tags("x", "gamma", "x", "y", "gamma"))
        self.assertEqual(["x", "gamma", "y"], self.result()["unconfigured"])

    def test_a_name_outside_the_model_rule_is_counted_and_never_printed(self):
        bad = ["", "a b", "a..b", "/a", "a/", "é", "-x", "x" * 129, "a\nb", "a\x00b", "SECRET name"]
        self.fake.reply(tags(*bad, "gamma"))
        code, out, err = self.models()
        document = json.loads(out)
        self.assertEqual((0, ["gamma"], len(bad)), (code, document["unconfigured"], document["skipped"]))
        self.assertNotIn("SECRET", out)

    def test_a_name_with_a_slash_in_its_segments_is_listed(self):
        self.configure({"org/model:tag": dict(CHAT)})
        self.fake.reply(tags("org/model:tag", "hf.co/org/other"))
        document = self.result()
        self.assertEqual((["org/model:tag"], ["hf.co/org/other"]), (document["present"], document["unconfigured"]))

    def test_the_fields_of_an_entry_but_its_name_are_never_read_or_printed(self):
        body = {"models": [{"name": "gamma", "digest": "SECRET-DIGEST", "details": {"family": "SECRET-FAMILY"}, "size": 5}]}
        self.fake.reply(body)
        code, out, err = self.models()
        self.assertEqual(0, code)
        self.assertNotIn("SECRET", out)

    def test_512_names_are_read_and_513_are_too_many(self):
        self.fake.reply(tags(*["m%d" % number for number in range(512)]))
        document = self.result()
        self.assertEqual(512, len(document["unconfigured"]))
        self.fake.reply(tags(*["m%d" % number for number in range(513)]))
        self.bad(error="vendor_error", detail="reply_too_large")

    def test_the_names_that_are_counted_still_count_towards_the_limit(self):
        self.fake.reply(tags(*["a b"] * 513))
        self.bad(error="vendor_error", detail="reply_too_large")

    def test_the_host_is_never_printed_by_a_call_that_cannot_reach_it(self):
        self.endpoints(ned=self.record(host="marker-host.invalid", port=self.fake.port, models={"alpha:1b": dict(CHAT)},
                                       default_model=None))
        code, out, err = self.models("--timeout", "3")
        self.assertEqual((1, ""), (code, err))  # the host does not resolve: unreachable
        self.assertNotIn("marker-host", out)
        self.assertEqual("vendor_unreachable", json.loads(out)["error"])


class Replies(Models):
    def unusable(self, body, **spec):
        self.fake.reply(body, **spec)
        return self.bad(error="vendor_error", detail="unusable_reply")

    def test_a_reply_that_is_not_an_object_with_a_list_of_entries_with_a_string_name_is_unusable(self):
        for body in (b"", b"not json", b"[]", b'"x"', b"null", b"{}", {"models": None}, {"models": {}}, {"models": "alpha"},
                     {"models": [None]}, {"models": ["alpha:1b"]}, {"models": [{}]}, {"models": [{"name": 5}]},
                     {"models": [{"name": None}]}, {"models": [{"name": ["a"]}]}, {"models": [{"id": "alpha:1b"}]},
                     {"models": [{"name": "alpha:1b"}, {"name": 5}]}, {"tags": [{"name": "alpha:1b"}]}):
            self.unusable(body)

    def test_a_nan_or_a_repeated_key_or_a_deep_nesting_is_unusable(self):
        for body in (b'{"models": [], "models": []}', b'{"models": [{"name": "a", "size": NaN}]}',
                     b'{"models": [' + b"[" * 200 + b"]" * 200 + b"]}",
                     b'{"models": [{"name": "a", "size": ' + b"9" * 4301 + b"}]}"):
            self.unusable(body)

    def test_a_status_outside_200_to_299_is_bad_exit_and_nothing_of_the_body_is_copied(self):
        for status in (300, 302, 400, 401, 404, 500, 503):
            self.fake.reply({"error": "SECRET-ERROR"}, status=status)
            document = self.bad(error="vendor_error", detail="bad_exit")
            self.assertEqual("the server answered with an error", document["message"])
            self.assertNotIn("SECRET", json.dumps(document))

    def test_a_redirect_is_not_followed_and_makes_no_second_request(self):
        target = "http://127.0.0.1:%d/api/tags" % self.fake.port
        for status in (301, 302, 307, 308):
            before = len(self.fake.requests)
            self.fake.reply(tags("alpha:1b"), status=status, headers={"Location": target})
            self.bad(error="vendor_error", detail="bad_exit")
            self.assertEqual(before + 1, len(self.fake.requests), status)

    def test_a_body_over_its_bound_is_reply_too_large(self):
        self.fake.reply(b"x" * (self.helper.MAX_BODY + 1))
        self.bad(error="vendor_error", detail="reply_too_large")

    def test_a_reply_cut_short_is_unusable(self):
        self.fake.reply(tags("alpha:1b"), abort=True)
        self.bad(error="vendor_error", detail="unusable_reply")


class Connection(Models):
    def test_a_server_that_refuses_the_connection_is_vendor_unreachable_and_retryable(self):
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        self.configure({"alpha:1b": dict(CHAT)}, port=port)
        self.bad(error="vendor_unreachable", retryable=True)

    def test_a_server_that_accepts_and_never_replies_ends_at_the_timeout(self):
        self.fake.reply(tags("alpha:1b"), delay=5)
        self.bad("--timeout", "1", error="timeout", retryable=True)


class Options(Models):
    def test_only_server_and_timeout_are_options_of_models(self):
        for args in (("--model", "alpha:1b"), ("--context", "5"), ("--effort", "low"), ("--root", "."),
                     ("--schema", "docs/plan.md"), ("--confine",), ("extra",), ("-x",)):
            self.refused_models(*args, contains="not an option of models")
        self.fake.reply(tags("alpha:1b"))
        self.assertTrue(self.result("--timeout", "30", "--server", "ned")["ok"])

    def test_an_option_given_twice_or_without_a_value_or_out_of_its_form_is_refused(self):
        self.refused_models("--timeout", "5", "--timeout", "6", contains="given twice")
        self.refused_models("--timeout", contains="needs a value")
        self.refused_models("--server", contains="needs a value")
        for bad in ("0", "3601", "-1", "1e3", "", "five"):
            self.refused_models("--timeout", bad, contains="--timeout")
        for bad in ("", "Ned", "a/b", "x" * 33):
            self.refused_models("--server", bad, contains="--server")

    def test_the_first_argument_models_is_known_and_the_usage_names_it(self):
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(1, self.helper.main(["list"], io.BytesIO(b""), out, err, self.root))
        self.assertIn("ask-ollama models", err.getvalue())


class File(Models):
    def test_a_bad_endpoint_file_is_refused_with_nothing_sent(self):
        self.write_endpoint_file(b"not json")
        self.refused_models(contains="strict JSON")
        self.endpoints(ned=dict(self.record(), port=0))
        self.refused_models(contains="port")
        self.write_endpoint_file(json.dumps({"format": 1, "endpoints": {}}).encode())
        self.refused_models(contains="older format")

    def test_a_missing_file_is_refused(self):
        import os
        os.remove(os.path.join(self.store, "endpoints.json"))
        self.refused_models(contains="missing")

    def test_no_default_and_no_server_is_a_refusal(self):
        self.endpoints(default=None, a=self.record(), b=self.record())
        self.refused_models(contains="no endpoint is named")


if __name__ == "__main__":
    unittest.main()
