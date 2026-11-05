"""The kit's reader of the owner's ``review-profiles.json`` (plan ``2026-11-04-review-profiles``, increment B).

The kit knows no document kind, so the caller names the ladder keys it accepts. Each refusal names the rule and never the
value, because the value is the owner's file text.
"""

import json
import os
import tempfile
import traceback
import unittest
from unittest import mock

from workbench import store
from workbench.wbkit import profiles

KEYS = ("plan", "spec", "roadmap", "adr", "solo", "default")
SINGLE = ("solo",)


def document(**changes):
    body = {
        "format": 1,
        "profiles": {
            "quick": {"bridge": "bridge-a", "effort": "low"},
            "deep": {"bridge": "bridge-a", "effort": "high"},
            "local": {"bridge": "bridge-b", "model": "phi4:latest", "options": {"server": "home", "thinking": "on"}},
        },
        "ladders": {"default": ["quick", "quick", "deep"], "solo": ["quick"]},
    }
    body.update(changes)
    return body


def encode(body):
    return json.dumps(body).encode("utf-8")


def parse(body, keys=KEYS, single=SINGLE):
    return profiles.parse(body if isinstance(body, bytes) else encode(body), keys, single)


class Valid(unittest.TestCase):
    def test_a_file_is_read(self):
        got = parse(document())
        self.assertEqual(["deep", "local", "quick"], sorted(got.profiles))
        self.assertEqual(("quick", "quick", "deep"), got.ladders["default"])
        local = got.profiles["local"]
        self.assertEqual(("bridge-b", "phi4:latest", None, {"server": "home", "thinking": "on"}),
                         (local.bridge, local.model, local.effort, local.options))
        self.assertEqual({}, got.profiles["quick"].options)

    def test_the_order_of_the_keys_does_not_matter(self):
        body = document()
        reordered = {"ladders": body["ladders"], "profiles": body["profiles"], "format": 1}
        self.assertEqual(parse(body), parse(reordered))

    def test_a_ladder_may_repeat_a_profile_and_hold_five_rungs(self):
        got = parse(document(ladders={"plan": ["quick"] * 5}))
        self.assertEqual(("quick",) * 5, got.ladders["plan"])

    def test_a_name_of_thirty_two_characters_is_accepted(self):
        name = "a" + "b" * 31
        got = parse({"format": 1, "profiles": {name: {"bridge": "bridge-a"}}, "ladders": {"plan": [name]}})
        self.assertIn(name, got.profiles)

    def test_a_model_of_a_bridge_to_a_server_may_hold_a_slash(self):
        body = document()
        body["profiles"]["local"]["model"] = "freehuntx/qwen3-coder:14b"
        self.assertEqual("freehuntx/qwen3-coder:14b", parse(body).profiles["local"].model)


class Refused(unittest.TestCase):
    MARK = "SECRETMARK"

    def refuse(self, body, keys=KEYS, single=SINGLE):
        with self.assertRaises(profiles.ProfileError) as caught:
            parse(body, keys, single)
        self.assertNotIn(self.MARK, str(caught.exception), "a refusal repeats the file's text")
        return str(caught.exception)

    def change(self, path, value):
        body = document()
        node = body
        for part in path[:-1]:
            node = node[part]
        node[path[-1]] = value
        return body

    def test_the_file_as_a_whole(self):
        self.refuse(b"not json")
        self.refuse(b'{"format": 1, "format": 1, "profiles": {}, "ladders": {}}')
        self.refuse(b'{"format": NaN, "profiles": {}, "ladders": {}}')
        self.refuse(b"[]")
        self.refuse(b"\xff\xfe")
        self.refuse(encode(document()) + b" " * (profiles.MAX_BYTES + 1))

    def test_the_top_level_fields(self):
        for body in (document(extra=1), {"profiles": document()["profiles"], "ladders": {}},
                     {"format": 1, "ladders": document()["ladders"]},
                     {"format": 1, "profiles": document()["profiles"]}):
            self.refuse(body)

    def test_the_format(self):
        for value in (2, 0, True, "1", 1.5, None):
            self.refuse(document(format=value))

    def test_the_profiles_object(self):
        self.refuse(document(profiles={}))
        self.refuse(document(profiles=[]))
        many = {"p%02d" % n: {"bridge": "bridge-a"} for n in range(33)}
        self.refuse({"format": 1, "profiles": many, "ladders": {"plan": ["p00"]}})

    def test_a_profile_name(self):
        for name in ("Quick", "_quick", "-quick", "a" * 33, "", "q uick", "quick.deep"):
            self.refuse({"format": 1, "profiles": {name: {"bridge": "bridge-a"}}, "ladders": {}})

    def test_a_profile_record(self):
        self.refuse(self.change(("profiles", "quick"), "bridge-a"))
        self.refuse(self.change(("profiles", "quick"), {"effort": "low"}))
        self.refuse(self.change(("profiles", "quick"), {"bridge": "bridge-a", "extra": 1}))

    def test_the_bridge(self):
        for value in (1, "", "Bridge A", "../x", "-x", None, ["bridge-a"]):
            self.refuse(self.change(("profiles", "quick", "bridge"), value))

    def test_the_effort(self):
        for value in ("max", "", 1, None, ["low"], "LOW"):
            self.refuse(self.change(("profiles", "quick", "effort"), value))

    def test_the_model(self):
        for value in ("a b", "-x", "", "a" * 129, 1, None, "a\n", "café", "a\tb"):
            self.refuse(self.change(("profiles", "quick", "model"), value))

    def test_the_options_object(self):
        self.refuse(self.change(("profiles", "local", "options"), []))
        self.refuse(self.change(("profiles", "local", "options"), {"opt%d" % n: "x" for n in range(9)}))

    def test_an_option_name(self):
        for name in ("model", "effort", "timeout", "schema", "root", "confine", "Server", "1x", "", "a" * 33, "a_b"):
            self.refuse(self.change(("profiles", "local", "options"), {name: "x"}))

    def test_an_option_value(self):
        for value in ("", "a b", "-1", "-x", "a" * 129, 1, True, None, "café", "a\n", "\x7f"):
            self.refuse(self.change(("profiles", "local", "options"), {"server": value}))

    def test_the_ladders_object(self):
        self.refuse(document(ladders=[]))
        self.refuse(document(ladders={"unknown": ["quick"]}))
        self.refuse(document(ladders={"Plan": ["quick"]}))

    def test_a_ladder(self):
        for rungs in ([], ["quick"] * 6, ["absent"], [1], "quick", None, ["quick", None]):
            self.refuse(document(ladders={"plan": rungs}))

    def test_a_ladder_that_must_hold_one_rung(self):
        self.refuse(document(ladders={"solo": ["quick", "deep"]}))
        self.refuse(document(ladders={"solo": []}))

    def test_the_reason_names_the_rule(self):
        self.assertIn("ladder", self.refuse(document(ladders={"plan": ["absent"]})))
        self.assertIn("format", self.refuse(document(format=2)))

    def test_no_text_of_the_file_is_repeated(self):
        body = document()
        body["profiles"]["quick"]["model"] = self.MARK + " bad"
        self.refuse(body)
        body = document()
        body["profiles"]["quick"]["options"] = {"server": self.MARK + " bad"}
        self.refuse(body)
        body = document(ladders={self.MARK: ["quick"]})
        self.refuse(body)
        self.refuse({"format": 1, "profiles": {self.MARK: {"bridge": "bridge-a"}}, "ladders": {}})


class ReservedPrefixes(unittest.TestCase):
    """A bridge that reads abbreviated options would take `--mod x` for `--model`, so a prefix of a reserved name is refused too."""

    def prefixes(self):
        for name in sorted(profiles.RESERVED):
            for size in range(1, len(name) + 1):
                yield name[:size]

    def test_the_function_says_reserved_or_a_prefix_of_one(self):
        for name in self.prefixes():
            self.assertTrue(profiles.reserved_or_prefix(name), name)

    def test_other_names_are_not_reserved(self):
        for name in ("model-id", "server", "thinking", "context", "max-output", "efforts", "x", "m-x", "timeouts", ""):
            self.assertFalse(profiles.reserved_or_prefix(name), name)

    def test_every_prefix_is_refused_as_a_profile_option(self):
        for name in self.prefixes():
            body = document()
            body["profiles"]["local"]["options"] = {name: "x"}
            with self.assertRaises(profiles.ProfileError, msg=name):
                parse(body)

    def test_a_name_that_only_begins_with_a_reserved_word_is_accepted(self):
        for name in ("model-id", "server", "efforts", "root-dir"):
            body = document()
            body["profiles"]["local"]["options"] = {name: "x"}
            self.assertEqual({name: "x"}, parse(body).profiles["local"].options)

    def test_a_bridge_that_matches_prefixes_would_have_taken_the_option_for_a_reserved_one(self):
        """The fake reader that stands for a third-party bridge: it resolves an abbreviation to the unique option it begins."""
        known = ["--model", "--effort", "--timeout", "--schema", "--root", "--confine", "--server"]

        def resolve(argument):
            matches = [name for name in known if name.startswith(argument)]
            return matches[0] if len(matches) == 1 else None

        self.assertEqual("--model", resolve("--mod"))
        for name in self.prefixes():
            if resolve("--" + name) in ["--" + reserved for reserved in profiles.RESERVED]:
                self.assertTrue(profiles.reserved_or_prefix(name), name)


class Resolution(unittest.TestCase):
    def setUp(self):
        self.got = parse(document(ladders={"plan": ["quick", "local", "deep"], "default": ["quick", "deep"],
                                           "solo": ["quick"]}))

    def test_round_n_uses_rung_n_and_the_last_rung_repeats(self):
        names = [profiles.for_round(self.got, "plan", n, True)[0] for n in range(1, 7)]
        self.assertEqual(["quick", "local", "deep", "deep", "deep", "deep"], names)

    def test_the_profile_is_returned_with_its_name(self):
        name, profile = profiles.for_round(self.got, "plan", 2, True)
        self.assertEqual(("local", "bridge-b"), (name, profile.bridge))

    def test_a_kind_without_a_ladder_uses_default_when_allowed(self):
        self.assertEqual("quick", profiles.for_round(self.got, "spec", 1, True)[0])
        self.assertEqual("deep", profiles.for_round(self.got, "spec", 2, True)[0])

    def test_default_never_serves_a_kind_that_may_not_use_it(self):
        with self.assertRaises(profiles.ProfileError):
            profiles.for_round(self.got, "spec", 1, False)

    def test_a_kind_with_neither_ladder_is_refused_naming_the_file(self):
        bare = parse(document(ladders={"plan": ["quick"]}))
        with self.assertRaises(profiles.ProfileError) as caught:
            profiles.for_round(bare, "adr", 1, True)
        self.assertIn(profiles.FILE, str(caught.exception))

    def test_a_round_below_one_is_refused(self):
        for n in (0, -1, True, 1.5, None):
            with self.assertRaises(profiles.ProfileError):
                profiles.for_round(self.got, "plan", n, True)


class Reading(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.home = os.path.realpath(holder.name)
        self.folder = os.path.join(self.home, ".config", "project-workbench")
        os.makedirs(self.folder)
        patcher = mock.patch.dict(os.environ, {"HOME": self.home})
        patcher.start()
        self.addCleanup(patcher.stop)

    def put(self, data):
        with open(os.path.join(self.folder, profiles.FILE), "wb") as handle:
            handle.write(data)

    def read(self):
        return profiles.read(KEYS, SINGLE)

    def refused(self):
        with self.assertRaises(profiles.ProfileError) as caught:
            self.read()
        message = str(caught.exception)
        self.assertNotIn(self.home, message, "a refusal repeats a path")
        self.assertIn(profiles.FILE, message)
        return message

    def test_the_file_is_read_by_its_fixed_path(self):
        self.put(encode(document()))
        self.assertIn("quick", self.read().profiles)

    def test_a_missing_file_is_refused_and_says_how_it_is_made(self):
        message = self.refused()
        self.assertIn("missing", message)
        self.assertIn("wb install", message)

    def test_a_link_is_refused(self):
        target = os.path.join(self.home, "elsewhere.json")
        with open(target, "wb") as handle:
            handle.write(encode(document()))
        os.symlink(target, os.path.join(self.folder, profiles.FILE))
        self.assertIn("linked", self.refused())

    def test_a_directory_is_refused(self):
        os.mkdir(os.path.join(self.folder, profiles.FILE))
        self.assertIn("regular", self.refused())

    def test_an_oversize_file_is_refused(self):
        self.put(b" " * (profiles.MAX_BYTES + 1))
        self.assertIn("large", self.refused())

    def test_an_invalid_file_is_refused_whole(self):
        body = document()
        body["profiles"]["quick"]["effort"] = "max"
        self.put(encode(body))
        self.assertIn("effort", self.refused())

    def test_a_home_directory_that_is_not_absolute_is_refused(self):
        with mock.patch.dict(os.environ, {"HOME": "relative"}):
            with self.assertRaises(profiles.ProfileError):
                self.read()

    def test_no_environment_variable_moves_the_file(self):
        other = os.path.join(self.home, "other")
        os.makedirs(os.path.join(other, ".config", "project-workbench"))
        with open(os.path.join(other, ".config", "project-workbench", profiles.FILE), "wb") as handle:
            handle.write(encode(document()))
        with mock.patch.dict(os.environ, {"WORKBENCH_STORE": other, "XDG_CONFIG_HOME": other}):
            self.refused()


class TheStoreRoot(unittest.TestCase):
    """The accepted record infers that the store tolerates one more file directly in its root; this is the test."""

    def test_a_further_file_in_the_root_is_tolerated_and_untouched(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = os.path.join(os.path.realpath(holder.name), "store")
        os.mkdir(root, 0o700)
        guarded = store.Store(root)
        guarded.ensure()
        data = encode(document())
        guarded.write(profiles.FILE, data)
        guarded.ensure()
        self.assertEqual(data, guarded.read(profiles.FILE))
        self.assertIn(profiles.FILE, os.listdir(root))


class Limits(unittest.TestCase):
    """What is accepted at the edge, so that a bound is not tighter than the specification says."""

    def test_a_file_with_no_ladders_is_accepted(self):
        # `wb install` writes profiles and no ladders when it will not choose a vendor for the owner.
        self.assertEqual({}, parse(document(ladders={})).ladders)

    def test_every_bound_may_be_reached(self):
        record = {"bridge": "a" * 64, "model": "m" * 128, "options": {"o" + "x" * 31: "v" * 128}}
        body = {"format": 1, "profiles": {"p%02d" % n: dict(record) for n in range(32)}, "ladders": {}}
        self.assertEqual(32, len(parse(body).profiles))

    def test_eight_options_may_be_held(self):
        body = document()
        body["profiles"]["local"]["options"] = {"o%d" % n: "v" for n in range(8)}
        self.assertEqual(8, len(parse(body).profiles["local"].options))

    def test_a_bridge_may_hold_the_characters_of_a_command_name(self):
        for bridge in ("bridge.a", "a+b", "Bridge-A", "9bridge"):
            body = document()
            body["profiles"]["quick"]["bridge"] = bridge
            self.assertEqual(bridge, parse(body).profiles["quick"].bridge)

    def test_the_whole_size_may_be_reached(self):
        body = encode(document())
        body += b" " * (profiles.MAX_BYTES - len(body))
        self.assertIn("quick", parse(body).profiles)


class Hostile(unittest.TestCase):
    MARK = "SECRETMARK"

    def refuse(self, body, keys=KEYS, single=SINGLE):
        with self.assertRaises(profiles.ProfileError) as caught:
            parse(body, keys, single)
        self.assertNotIn(self.MARK, str(caught.exception))
        return caught.exception

    def test_a_trailing_newline_is_part_of_a_name(self):
        for change in ({"profiles": {"quick\n": {"bridge": "bridge-a"}}, "ladders": {}},
                       {"profiles": {"quick": {"bridge": "bridge-a\n"}}, "ladders": {}},
                       {"profiles": {"quick": {"bridge": "bridge-a", "options": {"server\n": "x"}}}, "ladders": {}}):
            self.refuse(dict({"format": 1}, **change))

    def test_a_letter_that_is_not_ascii_is_refused(self):
        for change in ({"profiles": {"\uff51uick": {"bridge": "bridge-a"}}, "ladders": {}},
                       {"profiles": {"quick": {"bridge": "bridge-a", "model": "m\u00e9"}}, "ladders": {}},
                       {"profiles": {"quick": {"bridge": "ask-cod\u0435x"}}, "ladders": {}}):
            self.refuse(dict({"format": 1}, **change))

    def test_a_lone_surrogate_is_refused(self):
        self.refuse(b'{"format": 1, "profiles": {"q": {"bridge": "bridge-a", "model": "\\ud800"}}, "ladders": {}}')

    def test_a_repeated_key_below_the_top_is_refused(self):
        self.refuse(b'{"format": 1, "profiles": {"q": {"bridge": "bridge-a"}, "q": {"bridge": "bridge-a"}}, "ladders": {}}')
        self.refuse(b'{"format": 1, "profiles": {"q": {"bridge": "bridge-a", "options": {"a": "x", "a": "y"}}}, "ladders": {}}')

    def test_deep_nesting_is_a_refusal_and_not_a_crash(self):
        deep = b"[" * 100000 + b"]" * 100000
        self.refuse(b'{"format": 1, "profiles": ' + deep + b', "ladders": {}}')

    def test_a_huge_integer_is_a_refusal_and_not_a_crash(self):
        self.refuse(b'{"format": ' + b"9" * 5000 + b', "profiles": {}, "ladders": {}}')

    def test_options_that_are_null_are_refused(self):
        body = document()
        body["profiles"]["quick"]["options"] = None
        self.refuse(body)

    def test_the_marker_is_never_repeated(self):
        cases = []
        for field in ("bridge", "effort", "model"):
            body = document()
            body["profiles"]["quick"][field] = self.MARK + " x"
            cases.append(body)
        body = document()
        body["profiles"]["quick"][self.MARK] = 1
        cases.append(body)
        cases.append(document(**{self.MARK: 1}))
        body = document()
        body["profiles"]["quick"]["options"] = {self.MARK: "x"}
        cases.append(body)
        cases.append(document(ladders={"plan": [self.MARK]}))
        cases.append(document(ladders={"plan": [[self.MARK]]}))
        for body in cases:
            self.refuse(body)

    def test_a_refusal_carries_no_earlier_exception_that_holds_the_text(self):
        # A traceback prints the exception that was being handled, so a refusal must not keep one.
        failure = self.refuse(b'{"format": 12345.678, "profiles": {}, "ladders": {}}')
        shown = "".join(traceback.format_exception(type(failure), failure, failure.__traceback__))
        self.assertNotIn("12345.678", shown)


class Grammars(unittest.TestCase):
    """The closed list of grammars a module's declaration may give an option, and what each accepts."""

    def test_the_list_is_closed(self):
        self.assertEqual(["count", "name", "onoff", "word"], sorted(profiles.GRAMMARS))

    def test_word(self):
        for value in ("a", "gpt-5.6", "phi4:latest", "A_b", "9x", "a" * 64):
            self.assertTrue(profiles.fits("word", value), value)
        for value in ("", "-a", ".a", "a b", "a" * 65, "a/b", "caf\u00e9", "a\n", 1, None):
            self.assertFalse(profiles.fits("word", value), repr(value))

    def test_name(self):
        for value in ("home", "a", "my-box_1", "9", "a" * 32):
            self.assertTrue(profiles.fits("name", value), value)
        for value in ("", "Home", "-a", "_a", "a" * 33, "a b", "a.b", "a\n", 1):
            self.assertFalse(profiles.fits("name", value), repr(value))

    def test_count(self):
        for value in ("1", "10", "12345678", "9"):
            self.assertTrue(profiles.fits("count", value), value)
        for value in ("0", "01", "123456789", "-1", "+1", "1.5", "", " 1", "1\n", "\u0661", "1e3", 1, True):
            self.assertFalse(profiles.fits("count", value), repr(value))

    def test_onoff(self):
        for value in ("on", "off"):
            self.assertTrue(profiles.fits("onoff", value), value)
        for value in ("", "On", "ON", "true", "1", "on\n", " on", "of", True):
            self.assertFalse(profiles.fits("onoff", value), repr(value))

    def test_no_grammar_allows_a_leading_dash(self):
        for grammar in profiles.GRAMMARS:
            for value in ("-1", "-a", "-on", "--x"):
                self.assertFalse(profiles.fits(grammar, value), (grammar, value))

    def test_a_grammar_outside_the_list_fits_nothing(self):
        for grammar in ("any", "", None, ".*", ["word"]):
            self.assertFalse(profiles.fits(grammar, "x"), repr(grammar))


class Required(unittest.TestCase):
    def test_the_caller_must_say_which_ladders_hold_one_rung(self):
        # A default of "none" would silently drop the rule for a caller that forgot it.
        with self.assertRaises(TypeError):
            profiles.parse(encode(document()), KEYS)
        with self.assertRaises(TypeError):
            profiles.read(KEYS)


class MoreResolution(unittest.TestCase):
    def setUp(self):
        self.got = parse(document(ladders={"plan": ["quick"], "default": ["deep"]}))

    def test_a_kind_that_may_not_use_default_and_has_no_ladder_is_refused(self):
        with self.assertRaises(profiles.ProfileError):
            profiles.for_round(self.got, "solo", 1, False)

    def test_default_is_not_a_kind(self):
        with self.assertRaises(profiles.ProfileError):
            profiles.for_round(self.got, "default", 1, True)

    def test_a_kind_that_is_not_text_is_refused(self):
        for kind in (["plan"], None, 1, {"plan": 1}):
            with self.assertRaises(profiles.ProfileError):
                profiles.for_round(self.got, kind, 1, True)


class MoreReading(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.home = os.path.realpath(holder.name)
        self.folder = os.path.join(self.home, ".config", "project-workbench")
        patcher = mock.patch.dict(os.environ, {"HOME": self.home})
        patcher.start()
        self.addCleanup(patcher.stop)

    def refused(self):
        with self.assertRaises(profiles.ProfileError) as caught:
            profiles.read(KEYS, SINGLE)
        shown = "".join(traceback.format_exception(type(caught.exception), caught.exception, caught.exception.__traceback__))
        self.assertNotIn(self.home, shown, "a refusal, or the exception it replaced, repeats a path")
        return str(caught.exception)

    def test_a_missing_store_is_refused(self):
        self.assertIn("missing", self.refused())

    def test_a_store_that_is_a_link_is_refused(self):
        real = os.path.join(self.home, "real")
        os.makedirs(real)
        with open(os.path.join(real, profiles.FILE), "wb") as handle:
            handle.write(encode(document()))
        os.makedirs(os.path.dirname(self.folder))
        os.symlink(real, self.folder)
        self.refused()

    def test_a_file_that_cannot_be_read_is_refused(self):
        os.makedirs(self.folder)
        path = os.path.join(self.folder, profiles.FILE)
        with open(path, "wb") as handle:
            handle.write(encode(document()))
        os.chmod(path, 0)
        self.addCleanup(os.chmod, path, 0o600)
        if os.access(path, os.R_OK):
            self.skipTest("this account can read a file with no permissions")
        self.assertIn("cannot be read", self.refused())

    def test_a_missing_file_leaves_no_path_in_the_traceback(self):
        os.makedirs(self.folder)
        self.assertIn("missing", self.refused())


if __name__ == "__main__":
    unittest.main()
