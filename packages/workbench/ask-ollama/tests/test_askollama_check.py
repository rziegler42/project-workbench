"""`ask-ollama check`: the read-only diagnostic of the endpoint file (the `check` section of `docs/specs/ask-ollama.md`;
checklist item 9 there). Plan `2026-11-01-ask-ollama-bridge`, increment C."""

import os
import unittest

import support_ollama


class Check(support_ollama.Bridge):
    def check(self):
        code, out, err = self.ask(command="check")
        return code, out.splitlines(), err

    def test_one_line_per_record_in_the_files_order_without_host_or_port(self):
        self.endpoints(default="gpu", zed=self.record(host="zed.example", location="owner-network"),
                       gpu=self.record(host="10.0.0.5", location="vendor-cloud", scheme="https"))
        code, lines, err = self.check()
        self.assertEqual((0, ""), (code, err))
        self.assertEqual(["zed scheme=http location=owner-network authenticated=false default=no",
                          "gpu scheme=https location=vendor-cloud authenticated=false default=yes",
                          "warning: zed: unauthenticated http away from loopback; content sent to it travels in the clear"],
                         lines)

    def test_it_never_prints_a_host_a_port_a_model_or_a_context(self):
        self.endpoints(ned=self.record(host="marker-host.example", port=11434, default_model="marker-model",
                                       embedding_model="marker-embed", context=8192))
        out = self.ask(command="check")[1]
        for word in ("marker-host", "11434", "marker-model", "marker-embed", "8192", "example"):
            self.assertNotIn(word, out)

    def test_an_unauthenticated_http_record_away_from_loopback_is_warned_about_and_no_other_is(self):
        self.endpoints(default=None,
                       a=self.record(host="127.0.0.1"), b=self.record(host="127.9.9.9"), c=self.record(host="::1"),
                       d=self.record(host="0:0:0:0:0:0:0:1"), e=self.record(host="localhost"),
                       f=self.record(host="10.0.0.5"), g=self.record(host="ned.example"),
                       h=self.record(host="10.0.0.5", scheme="https"), i=self.record(host="fd00::1"))
        code, lines, err = self.check()
        warned = [line.split(":")[1].strip() for line in lines if line.startswith("warning: ")]
        self.assertEqual(["e", "f", "g", "i"], warned)

    def test_a_file_with_no_record_prints_one_line_and_succeeds(self):
        self.endpoints(default=None)
        self.write_endpoint_file(b'{"format": 1, "endpoints": {}}')
        code, lines, err = self.check()
        self.assertEqual((0, ["no endpoints"], ""), (code, lines, err))

    def test_only_the_default_is_marked(self):
        self.endpoints(default="b", a=self.record(), b=self.record(), c=self.record())
        lines = self.check()[1]
        self.assertEqual(["no", "yes", "no"], [line.rsplit("default=", 1)[1] for line in lines])

    def test_it_makes_no_connection_and_writes_nothing(self):
        before = (self.tree(self.root), self.tree(self.store))
        self.check()
        self.assertEqual([], self.fake.requests)
        self.assertEqual(before, (self.tree(self.root), self.tree(self.store)))

    def test_it_runs_without_a_project(self):
        out, err = self.ask(command="check", cwd=self.base)[1:]
        self.assertIn("ned scheme=http", out)
        self.assertEqual("", err)

    def test_it_takes_no_option(self):
        self.refused("--server", "ned", command="check", contains="no option")
        self.refused("extra", command="check", contains="no option")

    def test_a_file_that_breaks_a_rule_is_refused_with_one_line_and_nothing_on_standard_output(self):
        os.remove(os.path.join(self.store, "endpoints.json"))
        self.refused(command="check", contains="endpoint file")
        self.endpoints(ned=dict(self.record(), port=0))
        self.refused(command="check", contains="port")

    def test_a_record_that_says_it_is_authenticated_is_refused(self):
        self.endpoints(ned=dict(self.record(), authenticated=True))
        self.refused(command="check", contains="not supported yet")


if __name__ == "__main__":
    unittest.main()
