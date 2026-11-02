"""The endpoint file and its records (decision `2026-11-01-endpoint-records-in-the-store`, checklist item 3 of
`docs/specs/ask-ollama.md`). Every refusal is made before a connection and shows no host. Plan
`2026-11-01-ask-ollama-bridge`, increment C. `check` is used where only the file is under test, because it reads the file by
the same rules and makes no connection."""

import json
import os
import unittest

import support_ollama


class Broken(support_ollama.Bridge):
    """A file or a record that breaks a rule is refused whole, before anything is sent."""

    def broken(self, contains="endpoint file"):
        self.refused(command="check", contains=contains)
        self.refused(contains=contains)

    def path(self):
        return os.path.join(self.store, "endpoints.json")

    def test_a_good_file_is_read(self):
        self.assertEqual(0, self.ask(command="check")[0])

    def test_a_missing_file_is_refused(self):
        os.remove(self.path())
        self.broken("missing")

    def test_a_directory_in_its_place_is_refused(self):
        os.remove(self.path())
        os.mkdir(self.path())
        self.broken("regular file")

    def test_a_link_in_its_place_is_refused(self):
        other = os.path.join(self.base, "other.json")
        os.replace(self.path(), other)
        os.symlink(other, self.path())
        self.broken("linked")

    def test_a_file_that_cannot_be_read_is_refused_and_says_so(self):
        if os.geteuid() == 0:
            self.skipTest("the permissions are not enforced for this user")
        os.chmod(self.path(), 0o000)
        self.addCleanup(os.chmod, self.path(), 0o600)
        self.broken("cannot be read")

    def test_each_cause_of_a_file_problem_is_named_in_fixed_words_without_a_path(self):
        words = {}
        os.remove(self.path())
        words["missing"] = self.refused(command="check", contains="is missing")
        os.mkdir(self.path())
        words["directory"] = self.refused(command="check", contains="is not a regular file")
        os.rmdir(self.path())
        other = os.path.join(self.base, "other.json")
        with open(other, "w") as handle:
            handle.write("{}")
        os.symlink(other, self.path())
        words["link"] = self.refused(command="check", contains="is linked")
        os.remove(self.path())
        self.write_endpoint_file(b" " * 262145)
        words["large"] = self.refused(command="check", contains="is too large")
        self.assertEqual(4, len(set(words.values())))
        for text in words.values():
            self.assertNotIn(self.base, text)

    def test_a_store_that_is_a_link_is_refused(self):
        moved = self.store + ".moved"
        os.rename(self.store, moved)
        os.symlink(moved, self.store)
        self.broken("linked")

    def test_a_file_over_its_bound_is_refused(self):
        self.write_endpoint_file(b" " * 262145)
        self.broken("too large")

    def test_a_file_at_its_bound_is_read(self):
        document = json.dumps({"format": 2, "endpoints": {"ned": self.record()}}).encode()
        self.write_endpoint_file(document + b" " * (262144 - len(document)))
        self.assertEqual(0, self.ask(command="check")[0])

    def test_a_file_that_is_not_strict_json_is_refused(self):
        good = {"format": 2, "endpoints": {"ned": self.record(port=11434)}}
        for data in (b"", b"not json", b"[]", b"[1]", b'{"format": 2', b"\xff\xfe",
                     b'{"format": 2, "format": 1, "endpoints": {}}',
                     b'{"format": NaN, "endpoints": {}}',
                     json.dumps(good).replace("11434", "11434.0").encode(),
                     json.dumps(good).replace("11434", "1.1e4").encode(),
                     b'{"format": 2, "endpoints": {"a": {"a": ' + b"[" * 200 + b"]" * 200 + b"}}}"):
            self.write_endpoint_file(data)
            self.broken("strict JSON")

    def test_a_wrong_format_or_an_unknown_or_missing_top_field_is_refused(self):
        for document in ({"format": 3, "endpoints": {}}, {"format": True, "endpoints": {}},
                         {"format": "2", "endpoints": {}}, {"endpoints": {}}, {"format": 2},
                         {"format": 2, "endpoints": []}, {"format": 2, "endpoints": {}, "extra": 1},
                         {"format": 2, "endpoints": {}, "default": 1}):
            self.write_endpoint_file(json.dumps(document).encode())
            self.broken()

    def test_more_than_64_records_are_refused_and_64_are_read(self):
        many = {"r%d" % number: self.record() for number in range(65)}
        self.endpoints(default=None, **many)
        self.broken("more than")
        self.endpoints(default=None, **{key: many[key] for key in list(many)[:64]})
        self.assertEqual(0, self.ask(command="check")[0])

    def test_a_record_name_outside_its_form_is_refused(self):
        for name in ("Ned", "a b", "", "x" * 33, "-a", "_a", "a.b", "é", "a/b"):
            self.endpoints(default=None, **{name: self.record()})
            self.broken("record name")

    def test_a_record_name_at_its_limits_is_read(self):
        for name in ("a", "0", "x" * 32, "gpu-1_b"):
            self.endpoints(default=None, **{name: self.record()})
            self.assertEqual(0, self.ask(command="check")[0], name)

    def test_a_record_that_is_not_an_object_or_has_a_field_that_is_not_allowed_is_refused(self):
        for record in ("ned", [], None, dict(self.record(), extra=1), dict(self.record(), url="http://x"),
                       dict(self.record(), credential="x"), dict(self.record(), token="x")):
            self.endpoints(ned=record)
            self.broken()

    def test_a_record_with_a_required_field_missing_is_refused(self):
        for key in ("scheme", "host", "port", "location", "authenticated", "models"):
            record = self.record()
            del record[key]
            self.endpoints(ned=record)
            self.broken("missing the field")

    def test_a_scheme_other_than_http_or_https_is_refused(self):
        for scheme in ("ftp", "HTTP", "", 1, None, ["http"], "http "):
            self.endpoints(ned=dict(self.record(), scheme=scheme))
            self.broken("scheme")

    def test_a_port_that_is_not_a_whole_number_from_1_to_65535_is_refused(self):
        for port in (0, 65536, -1, "11434", True, False, None, [1], 10 ** 30):
            self.endpoints(ned=dict(self.record(), port=port))
            self.broken("port")
        for port in (1, 11434, 65535):
            self.endpoints(ned=dict(self.record(), port=port))
            self.assertEqual(0, self.ask(command="check")[0], port)

    def test_a_location_outside_the_three_classes_is_refused(self):
        for location in ("here", "", "this machine", 1, None):
            self.endpoints(ned=dict(self.record(), location=location))
            self.broken("location")
        for location in ("this-machine", "owner-network", "vendor-cloud"):
            self.endpoints(ned=dict(self.record(), location=location))
            self.assertEqual(0, self.ask(command="check")[0], location)

    def test_an_authenticated_record_is_refused_before_anything_is_sent(self):
        self.endpoints(ned=dict(self.record(), authenticated=True))
        self.broken("not supported yet")

    def test_authenticated_must_be_a_boolean(self):
        for value in ("false", 0, 1, None, [], "no"):
            self.endpoints(ned=dict(self.record(), authenticated=value))
            self.broken("authenticated")

    def test_a_model_field_outside_its_form_is_refused(self):
        for key in ("default_model", "embedding_model"):
            for name in ("", "a b", "a..b", "/a", "a/", "a//b", "-a", "a/-b", "x" * 129, "a;b", "é", 3, None, ["a"]):
                self.endpoints(ned=dict(self.record(), **{key: name}))
                self.broken(key)

    def test_a_model_field_at_its_limits_is_read(self):
        for name in ("a", "llama3:8b", "nomic-embed-text:latest", "user/model:tag", "hf.co/org/model", "x" * 128, "a/b/c"):
            self.endpoints(ned=self.record(models={name: {"kind": "chat", "context": 4096}}, default_model=name))
            self.assertEqual(0, self.ask(command="check")[0], name)
            self.endpoints(ned=self.record(models={name: {"kind": "embedding", "context": 4096}}, default_model=None,
                                           embedding_model=name))
            self.assertEqual(0, self.ask(command="check")[0], name)

    def test_the_context_of_format_1_is_no_longer_a_field_of_the_record(self):
        for context in (0, 4096, 10000000):
            self.endpoints(ned=dict(self.record(), context=context))
            self.broken("not allowed")

    def test_a_default_that_names_no_record_is_refused(self):
        for default in ("alt", "", "Ned", 1, None, ["ned"]):
            self.write_endpoint_file(json.dumps({"format": 2, "endpoints": {"ned": self.record()},
                                                 "default": default}).encode())
            self.broken("default")

    def test_a_bad_record_stops_the_whole_file_and_a_good_one_beside_it_is_not_used(self):
        self.endpoints(ned=self.record(), alt=dict(self.record(), port=0))
        self.broken("port")
        self.assertEqual([], self.fake.requests)


class Hosts(support_ollama.Bridge):
    """The grammar of `host`: three forms and no other, and every form a resolver could read as something else refused."""

    ACCEPTED = ("127.0.0.1", "127.0.0.2", "127.255.255.254", "10.0.0.5", "172.16.0.1", "192.168.0.9", "8.8.8.8",
                "100.64.0.1", "1.1.1.1", "223.255.255.255",
                "::1", "0:0:0:0:0:0:0:1", "0::1", "fd00::1", "2001:db8::1", "1:2:3:4:5:6:7::", "::2", "1::",
                "ned", "ollama.local", "a-b.example", "1.example", "0.example", "1abc", "0xzz", "x" * 63 + ".example",
                ".".join(["a" * 61] * 4), "a.b.c.d.e.f", "xn--bcher-kva.example")
    REFUSED = ("", "x" * 254, "a" * 64 + ".example", "Ned", "ned.", ".ned", "a..b", "a_b", "a@b", "a:b", "a/b", "a?b", "a#b",
               "a\\b", "[::1]", "a b", " ned", "ned ", "a\nb", "a\x00b", "a\x7fb", "a\tb", "é.example", "nedé",
               "127.1", "2130706433", "0177.0.0.1", "127.00.0.1", "0x7f.1", "0x7f.0x1", "0x", "a.0x", "0x0", "0", "00", "1.2.3",
               "1.2.3.4.5", "256.1.1.1", "1.2.3.256", "999.999.999.999", "01.2.3.4", "1.2.3.04", "1.2.3.", ".1.2.3.4",
               "1.2.3.4 ", "http://ned", "ned:11434", "127.0.0.1:11434", "user@ned", "fe80::1", "fe80::1%eth0", "febf::1",
               "::", "::ffff:127.0.0.1", "::ffff:7f00:1", "::FFFF:1", "::1.2.3.4", "ff02::1", "ff00::", "1:2:3:4:5:6:7:8:9",
               "1::2::3", ":::1", "1:2:3:4:5:6:7", "1:2:3:4:5:6:7:8::", "::g", "12345::1", "::1%1", "FD00::1", "abc.123",
               "abc.0xff", "abc.0x", "-a", "a-", "a.-b", "a-.b", "0.0.0.0", "0.1.2.3", "0.255.255.255", "224.0.0.1",
               "239.255.255.255", "240.0.0.1", "255.255.255.255", "169.254.169.254", "169.254.0.1", "169.254.255.255")

    def host_file(self, host):
        self.endpoints(ned=dict(self.record(), host=host))

    def test_each_accepted_form_is_read(self):
        for host in self.ACCEPTED:
            self.host_file(host)
            code, out, err = self.ask(command="check")
            self.assertEqual((0, ""), (code, err), host)

    def test_each_refused_form_is_refused_without_a_connection_and_without_the_value(self):
        for host in self.REFUSED:
            self.host_file(host)
            err = self.refused(command="check", contains="host")
            if len(host) > 3 and host.isprintable():
                self.assertNotIn(host, err.replace("record ned:", "record:"))

    def test_the_host_is_never_printed_by_check(self):
        self.host_file("marker-host.example")
        code, out, err = self.ask(command="check")
        self.assertEqual(0, code)
        self.assertNotIn("marker-host", out + err)

    def test_the_host_is_never_printed_by_a_call_that_cannot_reach_it(self):
        self.host_file("marker-host.invalid")
        code, out, err = self.ask("--timeout", "3")
        self.assertEqual((1, ""), (code, err))
        self.assertNotIn("marker-host", out)
        self.assertEqual("vendor_unreachable", json.loads(out)["error"])

    def test_loopback_is_an_ipv4_literal_in_127_or_any_spelling_of_the_ipv6_address_1_and_nothing_else(self):
        for host in ("127.0.0.1", "127.5.5.5", "127.255.255.254", "::1", "0:0:0:0:0:0:0:1", "0::1", "0000::0001", "::0001"):
            self.assertTrue(self.helper.is_loopback(host), host)
        for host in ("localhost", "10.0.0.1", "ned", "::2", "126.0.0.1", "128.0.0.1", "::ffff:127.0.0.1", "127.1", "", "::",
                     "1.2.3", "fd00::1"):
            self.assertFalse(self.helper.is_loopback(host), host)

    def test_the_library_agrees_with_the_grammar_on_literals(self):
        import ipaddress
        for host in self.ACCEPTED:
            if host.replace(".", "").isdigit() or ":" in host:
                ipaddress.ip_address(host)
        for host in ("127.1", "2130706433", "0177.0.0.1", "0x7f.1"):
            with self.assertRaises(ValueError):
                ipaddress.ip_address(host)
            self.assertIsNone(self.helper.host_form(host))


class Selection(support_ollama.Bridge):
    """Which record a call uses."""

    def two(self, default="ned"):
        self.endpoints(default=default, ned=self.record(default_model="m-ned"), alt=self.record(default_model="m-alt"))

    def model_sent(self):
        return json.loads(self.fake.requests[-1]["body"])["model"]

    def test_the_default_record_is_used_without_server(self):
        self.two()
        self.assertTrue(self.document()["ok"])
        self.assertEqual("m-ned", self.model_sent())

    def test_server_names_the_record(self):
        self.two()
        self.assertTrue(self.document("--server", "alt")["ok"])
        self.assertEqual("m-alt", self.model_sent())

    def test_no_default_and_no_server_is_a_refusal(self):
        self.two(default=None)
        self.refused(contains="no endpoint is named")

    def test_a_name_no_record_carries_is_a_refusal(self):
        self.two()
        self.refused("--server", "nope", contains="no endpoint record")

    def test_the_name_is_only_a_key_and_never_an_address(self):
        self.two()
        self.refused("--server", "127.0.0.1:%d" % self.fake.port, contains="--server")
        self.refused("--server", "http://127.0.0.1", contains="--server")

    def test_no_model_anywhere_is_a_refusal_and_a_model_option_fixes_it(self):
        self.endpoints(ned=self.record(default_model=None))
        self.refused(contains="no model is named")
        self.assertTrue(self.document("--model", "gpt-oss:20b")["ok"])
        self.assertEqual("gpt-oss:20b", self.model_sent())

    def test_the_model_option_beats_the_default_model(self):
        self.assertTrue(self.document("--model", "other:1b")["ok"])
        self.assertEqual("other:1b", self.model_sent())


if __name__ == "__main__":
    unittest.main()
