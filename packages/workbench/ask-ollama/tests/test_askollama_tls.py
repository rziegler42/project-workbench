"""Verified HTTPS (the transport section of `docs/specs/ask-ollama.md`; checklist item 6 there). Plan
`2026-11-01-ask-ollama-bridge`, increment C. The fake server speaks TLS on the loopback address with a throwaway certificate
from `certs/`. Trust is given only by replacing `tls_context()` inside the test; nothing the helper reads from its environment
or its files adds a trusted certificate."""

import os
import ssl
import unittest
import unittest.mock

import support_ollama
from support_ollama import CERTS, chat, server_context, trusting

CERTIFICATE = "the server's certificate was not accepted"


class Https(support_ollama.Bridge):
    def serve(self, certificate):
        self.fake.close()
        self.fake = support_ollama.Fake(server_context(certificate))
        self.addCleanup(self.fake.close)
        self.endpoints(ned=self.record(scheme="https"))

    def trust(self, certificate):
        patch = unittest.mock.patch.object(self.helper, "tls_context", lambda: trusting(certificate))
        patch.start()
        self.addCleanup(patch.stop)

    def rejected(self, *args):
        document = self.failed(*args, error="vendor_unreachable", retryable=False)
        self.assertEqual(CERTIFICATE, document["message"])
        self.assertIsNone(document["detail"])
        return document

    def test_a_trusted_certificate_that_matches_the_host_is_accepted(self):
        self.serve("trusted")
        self.trust("trusted")
        document = self.document()
        self.assertTrue(document["ok"])
        self.assertEqual("the reply", document["reply"])
        self.assertEqual(1, len(self.fake.requests))
        self.assertEqual("127.0.0.1:%d" % self.fake.port, dict(self.fake.requests[0]["headers"])["Host"])

    def test_a_certificate_that_is_not_trusted_is_refused_and_nothing_is_sent(self):
        self.serve("trusted")
        self.rejected()
        self.assertEqual([], self.fake.requests)

    def test_a_trusted_certificate_made_for_another_host_is_refused(self):
        self.serve("other-host")
        self.trust("other-host")
        self.rejected()
        self.assertEqual([], self.fake.requests)

    def test_a_trusted_certificate_that_has_expired_is_refused(self):
        self.serve("expired")
        self.trust("expired")
        self.rejected()
        self.assertEqual([], self.fake.requests)

    def test_the_environment_cannot_add_a_trusted_certificate(self):
        self.serve("trusted")
        with unittest.mock.patch.dict(os.environ, {"SSL_CERT_FILE": os.path.join(CERTS, "trusted.pem"),
                                                   "SSL_CERT_DIR": CERTS}):
            self.rejected()
        self.assertEqual([], self.fake.requests)

    def test_the_default_context_checks_the_certificate_and_the_host_and_needs_tls_1_2(self):
        context = self.helper.tls_context()
        self.assertIs(True, context.check_hostname)
        self.assertEqual(ssl.CERT_REQUIRED, context.verify_mode)
        self.assertGreaterEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)

    def test_the_default_context_ignores_the_variables_that_move_the_trust_store(self):
        plain = self.helper.tls_context().cert_store_stats()
        with unittest.mock.patch.dict(os.environ, {"SSL_CERT_FILE": os.path.join(CERTS, "trusted.pem"),
                                                   "SSL_CERT_DIR": CERTS}):
            moved = self.helper.tls_context().cert_store_stats()
        self.assertEqual(plain, moved)

    def test_no_option_or_variable_turns_verification_off(self):
        text = self._source()
        for word in ("CERT_NONE", "check_hostname = False", "_create_unverified_context", "_create_default_https_context"):
            self.assertNotIn(word, text)

    def _source(self):
        with open(self.helper.__file__, encoding="utf-8") as handle:
            return handle.read()

    def test_a_server_that_speaks_plain_http_to_an_https_client_is_unreachable_and_can_be_retried(self):
        self.endpoints(ned=self.record(scheme="https"))
        self.failed(error="vendor_unreachable", retryable=True)

    def test_a_plain_http_record_does_not_use_tls(self):
        self.assertTrue(self.document()["ok"])

    def test_the_message_names_no_host_port_or_certificate_detail(self):
        self.serve("expired")
        self.trust("expired")
        out = self.ask()[1]
        for word in ("127.0.0.1", str(self.fake.port), "localhost", "expired", "CN="):
            self.assertNotIn(word, out)


if __name__ == "__main__":
    unittest.main()
