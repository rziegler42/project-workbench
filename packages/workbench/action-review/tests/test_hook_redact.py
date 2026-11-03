"""The redaction the shadow hook applies to what it stores (`docs/specs/action-review.md`, "The shadow hook").

Plan `2026-11-03-redact-collected-diffs`, increment A. `redact` returns a copy of a text, a list or an object with every secret that
a fixed list of patterns finds replaced by `[redacted:<kind>]`, and changes nothing else. The secrets below are made up and are
joined from parts so that no scanner takes this file for a leak. Written before the code."""

import importlib.util
import os
import time
import unittest

from tests import support_install

ROOT = support_install.ROOT
HOOK = os.path.join(ROOT, "packages", "workbench", "action-review", "hook", "shadow_hook.py")
BIG = 393216  # the facts cap of safe-git.md, the largest text the hook can hold


def load():
    spec = importlib.util.spec_from_file_location("action_review_shadow_hook_redact", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HOOK_MODULE = load()
redact = HOOK_MODULE.redact
redact_text = HOOK_MODULE.redact_text

PEM = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA" + "x" * 40 + "\n-----END RSA PRIVATE KEY-----"
TOKENS = {
    "aws": "AKIA" + "IOSFODNN7EXAMPLE",
    "aws temporary": "ASIA" + "IOSFODNN7EXAMPLE",
    "github personal": "ghp_" + "a1B2c3D4e5F6g7H8i9J0" + "k1L2m3N4o5P6",
    "github oauth": "gho_" + "a1B2c3D4e5F6g7H8i9J0" + "k1L2m3N4o5P6",
    "github server": "ghs_" + "a1B2c3D4e5F6g7H8i9J0" + "k1L2m3N4o5P6",
    "github fine-grained": "github_pat_" + "11ABCDEFG0abcdefghij_" + "klmnopqrstuvwxyz0123456789",
    "openai style": "sk-" + "abcdefghijklmnopqrstuvwx" + "yz0123456789",
    "anthropic style": "sk-ant-" + "api03-abcdefghijklmnop" + "qrstuvwxyz",
    "slack": "xoxb-" + "123456789012-abcdefghijkl",
    "google": "AIza" + "SyA1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q",
}
JWT = "eyJhbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0" + "." + "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"


class Kinds(unittest.TestCase):
    def test_a_private_key_block_is_replaced_whole(self):
        self.assertEqual(redact_text("before\n%s\nafter" % PEM), "before\n[redacted:private-key]\nafter")

    def test_a_block_cut_off_by_the_end_of_the_text_is_replaced_to_the_end(self):
        self.assertEqual(redact_text("x\n-----BEGIN PRIVATE KEY-----\nabc\ndef\n"), "x\n[redacted:private-key]")

    def test_an_openssh_and_an_encrypted_block_are_replaced(self):
        for kind in ("OPENSSH PRIVATE KEY", "ENCRYPTED PRIVATE KEY", "EC PRIVATE KEY"):
            text = "-----BEGIN %s-----\nabc\n-----END %s-----" % (kind, kind)
            self.assertEqual(redact_text(text), "[redacted:private-key]", kind)

    def test_a_pgp_private_key_block_is_replaced(self):
        text = "-----BEGIN PGP PRIVATE KEY BLOCK-----\nabc\n-----END PGP PRIVATE KEY BLOCK-----\nafter"
        self.assertEqual(redact_text(text), "[redacted:private-key]\nafter")

    def test_a_public_key_block_is_kept(self):
        text = "-----BEGIN PUBLIC KEY-----\nabc\n-----END PUBLIC KEY-----"
        self.assertEqual(redact_text(text), text)

    def test_each_prefixed_token_is_replaced(self):
        for name, token in TOKENS.items():
            self.assertEqual(redact_text("see %s now" % token), "see [redacted:token] now", name)

    def test_a_prefixed_token_inside_a_url_or_a_flag_is_replaced(self):
        token = TOKENS["github personal"]
        self.assertEqual(redact_text("curl -H x https://h/?t=%s&u=1" % token), "curl -H x https://h/?t=[redacted:token]&u=1")

    def test_a_json_web_token_is_replaced(self):
        self.assertEqual(redact_text("jwt %s end" % JWT), "jwt [redacted:jwt] end")

    def test_an_authorization_header_loses_its_scheme_and_value(self):
        self.assertEqual(redact_text("Authorization: Bearer abcdef0123456789"), "Authorization: [redacted:bearer]")
        self.assertEqual(redact_text("authorization: Basic dXNlcjpwYXNz"), "authorization: [redacted:bearer]")
        self.assertEqual(redact_text('"Authorization": "Token abc12345678"'), '"Authorization": "[redacted:bearer]"')

    def test_a_bare_bearer_value_is_replaced_and_the_word_is_kept(self):
        self.assertEqual(redact_text("use Bearer abcdefghij0123456789 here"), "use Bearer [redacted:bearer] here")
        self.assertEqual(redact_text("use bearer abcdef0123456789xyz here"), "use bearer [redacted:bearer] here")
        self.assertEqual(redact_text("Bearer abcd-efghijklmnop1234"), "Bearer [redacted:bearer]")

    def test_a_value_assigned_to_a_secret_name_is_replaced_and_the_name_is_kept(self):
        cases = {
            "password=hunter22": "password=[redacted:assignment]",
            "export DB_PASSWORD=s3cr3tpw": "export DB_PASSWORD=[redacted:assignment]",
            "TOKEN: abcdefgh": "TOKEN: [redacted:assignment]",
            "client_secret = 'xyz123456'": "client_secret = '[redacted:assignment]'",
            '"api_key": "abcd1234efgh"': '"api_key": "[redacted:assignment]"',
            "private-key=abcdef123": "private-key=[redacted:assignment]",
            "aws_secret_access_key=abcdef123456": "aws_secret_access_key=[redacted:assignment]",
            "passphrase: 'two words here'": "passphrase: '[redacted:assignment]'",
            "--password hunter22": "--password [redacted:assignment]",
            "--token=abcdef123": "--token=[redacted:assignment]",
            "--api-key abcdef123": "--api-key [redacted:assignment]",
            "-token abcdef123": "-token [redacted:assignment]",
            "credential=abcdef123": "credential=[redacted:assignment]",
            "aws_credential: 'abcdef123456'": "aws_credential: '[redacted:assignment]'",
            "secret='abc12345' --other x": "secret='[redacted:assignment]' --other x",
        }
        for text, expected in cases.items():
            self.assertEqual(redact_text(text), expected, text)

    def test_a_value_of_four_characters_is_replaced_and_one_of_three_is_not(self):
        self.assertEqual(redact_text("PASSWORD=admin"), "PASSWORD=[redacted:assignment]")
        self.assertEqual(redact_text("secret=1234"), "secret=[redacted:assignment]")
        self.assertEqual(redact_text("secret=123"), "secret=123")

    def test_a_name_that_ends_in_key_is_a_secret_name_and_a_bare_key_is_not(self):
        self.assertEqual(redact_text("SSH_KEY=abcdef123"), "SSH_KEY=[redacted:assignment]")
        self.assertEqual(redact_text("signing-key: abcdef123"), "signing-key: [redacted:assignment]")
        for name in ("apikey", "accesskey", "privatekey", "authkey"):
            self.assertEqual(redact_text("%s=abcdef123" % name), "%s=[redacted:assignment]" % name, name)
        self.assertEqual(redact_text("key=abcdef123"), "key=abcdef123")

    def test_a_value_in_json_escaped_inside_a_shell_string_is_replaced(self):
        for text in ('curl -d "{\\"password\\":\\"hunter2abc\\"}" u', "curl -d '{\"password\":\"hunter2abc\"}' u"):
            out = redact_text(text)
            self.assertNotIn("hunter2abc", out, text)
            self.assertIn("[redacted:assignment]", out, text)
        out = redact_text('-H "{\\"Authorization\\": \\"Bearer abcdef0123456789\\"}"')
        self.assertNotIn("abcdef0123456789", out)
        out = redact_text('-H "{\\"Authorization\\": \\"Basic dXNlcjpwYXNz\\"}"')
        self.assertNotIn("dXNlcjpwYXNz", out)
        self.assertIn("[redacted:bearer]", out)

    def test_an_empty_quoted_value_is_kept(self):
        self.assertEqual(redact_text('password=""'), 'password=""')
        self.assertEqual(redact_text("password=''"), "password=''")

    def test_an_unclosed_quote_is_replaced_to_the_end_of_the_line(self):
        self.assertEqual(redact_text('password="abcd efgh\nnext'), 'password="[redacted:assignment]\nnext')

    def test_a_carriage_return_after_an_unclosed_quote_is_kept(self):
        self.assertEqual(redact_text('password="abcd efgh\r\nnext'), 'password="[redacted:assignment]\r\nnext')

    def test_a_password_with_an_at_sign_in_a_url_is_replaced_whole(self):
        self.assertEqual(redact_text("https://bob:p@ss@example.com/r"), "https://[redacted:url-credentials]@example.com/r")

    def test_the_user_and_password_of_a_url_are_replaced(self):
        self.assertEqual(redact_text("git clone https://bob:pa55w0rd@example.com/r.git"),
                         "git clone https://[redacted:url-credentials]@example.com/r.git")

    def test_two_secrets_in_one_text_are_both_replaced(self):
        text = "a %s b password=hunter22 c" % TOKENS["aws"]
        self.assertEqual(redact_text(text), "a [redacted:token] b password=[redacted:assignment] c")

    def test_the_line_breaks_of_a_diff_are_kept(self):
        diff = "+++ b/.env\n+DB_PASSWORD=s3cr3tpw\n+PORT=8080\n+KEY=%s\n" % TOKENS["github personal"]
        out = redact_text(diff)
        self.assertEqual(out.count("\n"), diff.count("\n"))
        self.assertNotIn("s3cr3tpw", out)
        self.assertIn("+PORT=8080", out)

    def test_redacting_twice_changes_nothing_more(self):
        text = "a %s b password=hunter22 Authorization: Bearer abcdef0123456789 %s %s" % (TOKENS["aws"], PEM, JWT)
        once = redact_text(text)
        self.assertEqual(redact_text(once), once)


class WhatMustNotChange(unittest.TestCase):
    def test_these_texts_are_returned_as_they_were(self):
        kept = [
            "", "plain text\nwith lines\n", "0123456789abcdef0123456789abcdef01234567",
            "a" * 64, "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "/home/user/.ssh/config", "version 1.2.3", "the password is checked", "token", "password", "author=bob",
            "Basic configuration of it", "Bearer authentication", "task-queue-length-abcdefghijklmnopqrstuvwxyz",
            "risk-assessment-of-something-quite-long-here", "key=value", "password=ab", "password=abc", "git@github.com:owner/repo.git",
            "https://example.com/path?a=1", "-----BEGIN-----", "ghp_short", "eyJ.not.a-jwt",
            "wb run safe-git commit --expected-head " + "a" * 40 + " --subject x -- a.txt",
            "prefix" + TOKENS["aws"], TOKENS["aws"] + "X", "Bearer authenticationmechanism", "a:b@c.example",
            "https://git@github.com/owner/repo.git", "--password --verbose-mode", "the token handling is done",
            "a one-time-token expires soon",
        ]
        for text in kept:
            self.assertEqual(redact_text(text), text, text)

    def test_a_marker_is_not_redacted_again_as_a_value(self):
        text = "token=[redacted:token]"
        self.assertEqual(redact_text(text), text)


class TheWalk(unittest.TestCase):
    def test_every_string_of_a_nested_value_is_redacted_and_the_rest_is_kept(self):
        value = {"facts": {"diff": "password=hunter22\n", "paths": ["a.txt", "k=%s" % TOKENS["aws"]], "n": 3, "f": 1.5,
                           "ok": True, "none": None}, "errors": []}
        expected = {"facts": {"diff": "password=[redacted:assignment]\n", "paths": ["a.txt", "k=[redacted:token]"], "n": 3,
                              "f": 1.5, "ok": True, "none": None}, "errors": []}
        self.assertEqual(redact(value), expected)

    def test_a_key_is_kept_even_when_it_looks_like_a_secret(self):
        key = TOKENS["aws"]
        self.assertEqual(redact({key: "x"}), {key: "x"})

    def test_the_input_is_not_changed_and_the_result_is_a_new_object(self):
        value = {"a": ["password=hunter22"]}
        out = redact(value)
        self.assertEqual(value, {"a": ["password=hunter22"]})
        self.assertIsNot(out, value)
        self.assertIsNot(out["a"], value["a"])

    def test_a_string_is_redacted_as_a_text(self):
        self.assertEqual(redact("password=hunter22"), "password=[redacted:assignment]")

    def test_a_value_of_another_type_is_refused_not_kept(self):
        for bad in (b"bytes", (1, 2), {1, 2}, object()):
            with self.assertRaises(ValueError, msg=repr(bad)):
                redact({"a": bad})

    def test_a_key_that_is_not_a_string_is_refused(self):
        with self.assertRaises(ValueError):
            redact({1: "x"})

    def test_a_value_nested_too_deep_is_refused(self):
        value = "x"
        for _ in range(200):
            value = [value]
        with self.assertRaises(ValueError):
            redact(value)

    def test_a_value_nested_to_the_limit_is_redacted(self):
        value = "password=hunter22"
        for _ in range(60):
            value = [value]
        out = redact(value)
        for _ in range(60):
            out = out[0]
        self.assertEqual(out, "password=[redacted:assignment]")


class TheTimeItTakes(unittest.TestCase):
    def test_the_largest_text_of_each_hostile_shape_is_redacted_within_the_limit(self):
        shapes = {
            "one long word": "a" * BIG,
            "secret names": "token" * (BIG // 5),
            "assignments": "password=" * (BIG // 9),
            "assignments with quotes": 'password="' * (BIG // 10),
            "url starts": "a://" * (BIG // 4),
            "url with colons": "a://b:" * (BIG // 6),
            "key starts": "-----BEGIN PRIVATE KEY-----" * (BIG // 27),
            "bearers": "Bearer " * (BIG // 7),
            "authorizations": "Authorization: " * (BIG // 15),
            "jwt starts": "eyJ" * (BIG // 3),
            "jwt starts after hyphens": "eyJ-" * (BIG // 4),
            "jwt starts after dots": "eyJ-aaaaaaaa." * (BIG // 13),
            "token starts after hyphens": "sk--" * (BIG // 4),
            "github starts": "ghp_a" * (BIG // 5),
            "bearer after hyphens": "Bearer-" * (BIG // 7),
            "escaped quotes": 'password=\\"' * (BIG // 11),
            "credentials with at signs": "a://b:c@" * (BIG // 8),
            "credentials with colons": "a://" + "b:" * (BIG // 2),
            "flags": "-token " * (BIG // 7),
            "flags with dashes": "-" * 5 + "token " * (BIG // 6),
            "prefixes": "sk-" * (BIG // 3),
            "separators": "=" * BIG,
            "names with separators": "api_key" + " " * 8 + "x" * (BIG - 15),
            "long name": "x" * 60 + "secret" + "y" * (BIG - 66),
        }
        for name, text in shapes.items():
            text = text[:BIG]
            begun = time.monotonic()
            out = redact_text(text)
            took = time.monotonic() - begun
            self.assertLess(took, 2.0, "%s took %.1f seconds" % (name, took))
            self.assertIsInstance(out, str)


if __name__ == "__main__":
    unittest.main()
