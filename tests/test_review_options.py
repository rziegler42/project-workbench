"""The options a module's command declares for use by a review (plan ``2026-11-04-review-profiles``, increment C).

``commands[].review_options`` maps an option name to ``{"grammar": <word of a closed list>, "excludes": [...]}``. The reader refuses
the names that belong to a profile's fixed fields or to the engine, a grammar outside the list, and an exclusion that names nothing
the command declares; ``wb verify`` refuses what the reader refuses.
"""

import copy
import json
import os
import unittest

from workbench import declarations as d
from workbench import hashing, verify
from workbench.wbkit import profiles

from tests.test_verify import Base

OLLAMA = {
    "server": {"grammar": "name"},
    "thinking": {"grammar": "onoff", "excludes": ["effort"]},
    "context": {"grammar": "count"},
    "max-output": {"grammar": "count"},
}


def declaration(options=None, **command):
    entry = {"helper": "scripts/run", "runtime": "python", "kit": 1, "arguments": ["ask"]}
    if options is not None:
        entry["review_options"] = options
    entry.update(command)
    return {"name": "bridge", "version": "1.0", "description": "A bridge.", "ships": ["scripts/run"],
            "commands": {"bridge": entry}}


def parse(decl):
    return d.parse_module(json.dumps(decl).encode("utf-8"), "sample", decl["name"])


class Declared(unittest.TestCase):
    def refused(self, options, **command):
        with self.assertRaises(d.DeclarationError) as caught:
            parse(declaration(options, **command))
        self.assertEqual("commands", caught.exception.rule)
        return str(caught.exception)

    def test_a_command_without_the_field_has_none(self):
        self.assertEqual((), parse(declaration()).commands[0].review_options)

    def test_the_options_of_the_ollama_bridge_are_read_in_the_order_written(self):
        got = parse(declaration(OLLAMA)).commands[0].review_options
        self.assertEqual((("server", "name", ()), ("thinking", "onoff", ("effort",)), ("context", "count", ()),
                          ("max-output", "count", ())), got)

    def test_every_grammar_of_the_closed_list_is_accepted(self):
        for grammar in ("word", "name", "count", "onoff"):
            self.assertEqual(grammar, parse(declaration({"x": {"grammar": grammar}})).commands[0].review_options[0][1])

    def test_the_list_of_grammars_is_the_kits(self):
        self.assertEqual(sorted(profiles.GRAMMARS), sorted(d.REVIEW_GRAMMARS))

    def test_a_grammar_outside_the_list_is_refused(self):
        for grammar in ("any", "regex", ".*", "", "Word", None, 1, ["word"], {"word": 1}):
            self.refused({"x": {"grammar": grammar}})

    def test_a_grammar_is_required(self):
        self.refused({"x": {}})
        self.refused({"x": {"excludes": []}})

    def test_the_names_of_fixed_fields_and_of_the_engine_are_refused(self):
        for name in sorted(profiles.RESERVED):
            self.refused({name: {"grammar": "word"}})
        self.assertEqual({"model", "effort", "timeout", "schema", "root", "confine"}, set(profiles.RESERVED))

    def test_a_prefix_of_a_reserved_name_is_refused(self):
        for reserved in sorted(profiles.RESERVED):
            for size in range(1, len(reserved) + 1):
                self.refused({reserved[:size]: {"grammar": "word"}})

    def test_a_name_that_only_begins_with_a_reserved_word_is_accepted(self):
        for name in ("model-id", "server", "efforts"):
            self.assertEqual(name, parse(declaration({name: {"grammar": "word"}})).commands[0].review_options[0][0])

    def test_an_option_name_has_the_form_of_an_argument(self):
        for name in ("Server", "1x", "", "a" * 33, "a_b", "a b", "-x", "x\n"):
            self.refused({name: {"grammar": "word"}})

    def test_at_most_eight_options(self):
        eight = {"o%d" % n: {"grammar": "word"} for n in range(8)}
        self.assertEqual(8, len(parse(declaration(eight)).commands[0].review_options))
        eight["o8"] = {"grammar": "word"}
        self.refused(eight)

    def test_the_field_and_its_entries_are_objects(self):
        for options in ([], "x", 1, {"x": "word"}, {"x": []}, {"x": None}):
            self.refused(options)

    def test_a_null_field_is_refused(self):
        decl = declaration()
        decl["commands"]["bridge"]["review_options"] = None
        with self.assertRaises(d.DeclarationError):
            parse(decl)

    def test_an_entry_with_an_unknown_field_is_refused(self):
        self.refused({"x": {"grammar": "word", "extra": 1}})

    def test_excludes_may_name_effort_or_another_declared_option(self):
        got = parse(declaration({"a": {"grammar": "word", "excludes": ["b", "effort"]}, "b": {"grammar": "word"}}))
        self.assertEqual(("b", "effort"), got.commands[0].review_options[0][2])

    def test_excludes_must_name_something_declared(self):
        self.refused({"a": {"grammar": "word", "excludes": ["nothing"]}})
        self.refused({"a": {"grammar": "word", "excludes": ["model"]}})

    def test_excludes_may_not_name_the_option_itself(self):
        self.refused({"a": {"grammar": "word", "excludes": ["a"]}})

    def test_excludes_is_a_list_of_different_names(self):
        self.refused({"a": {"grammar": "word", "excludes": "effort"}, "b": {"grammar": "word"}})
        self.refused({"a": {"grammar": "word", "excludes": [1]}})
        self.refused({"a": {"grammar": "word", "excludes": ["effort", "effort"]}})
        self.refused({"a": {"grammar": "word", "excludes": ["effort"] * 9}})

    def test_an_excludes_entry_that_is_not_text_is_refused(self):
        for item in ([], {}, None, 1, True):
            self.refused({"a": {"grammar": "word", "excludes": [item]}})

    def test_excludes_may_not_name_any_other_reserved_name(self):
        for name in sorted(profiles.RESERVED - {"effort"}):
            self.refused({"a": {"grammar": "word", "excludes": [name]}})

    def test_two_options_may_exclude_each_other(self):
        got = parse(declaration({"a": {"grammar": "word", "excludes": ["b"]}, "b": {"grammar": "word", "excludes": ["a"]}}))
        self.assertEqual(("b",), got.commands[0].review_options[0][2])

    def test_every_declared_grammar_is_one_the_kit_can_check(self):
        sample = {"name": "home", "onoff": "on", "count": "4096", "word": "x"}
        for _, grammar, _ in parse(declaration(OLLAMA)).commands[0].review_options:
            self.assertTrue(profiles.fits(grammar, sample[grammar]), grammar)

    def test_the_field_is_covered_by_the_declaration_hash_as_written(self):
        with_field = declaration(OLLAMA)
        without = declaration()
        self.assertNotEqual(hashing.declaration_hash(with_field), hashing.declaration_hash(without))
        changed = copy.deepcopy(with_field)
        changed["commands"]["bridge"]["review_options"]["server"]["grammar"] = "word"
        self.assertNotEqual(hashing.declaration_hash(with_field), hashing.declaration_hash(changed))


class Verified(Base):
    def package_with(self, options):
        fields = declaration(options)
        path = self.package("p", {"a": {"ships": ["scripts/run"], "commands": fields["commands"]}})
        os.makedirs(os.path.join(path, "a", "scripts"))
        with open(os.path.join(path, "a", "scripts", "run"), "w") as handle:
            handle.write("# helper\n")
        return path

    def test_verify_accepts_a_declaration_that_fits(self):
        result = verify.verify_package(self.package_with(OLLAMA), harness_required=False, first_party=True,
                                       which=lambda name: "/bin/" + name)
        self.assertTrue(result.accepted, [str(problem) for problem in result.problems])

    def test_verify_refuses_a_reserved_name(self):
        result = verify.verify_package(self.package_with({"timeout": {"grammar": "count"}}), harness_required=False,
                                       first_party=True, which=lambda name: "/bin/" + name)
        self.assertFalse(result.accepted)

    def test_verify_refuses_a_grammar_outside_the_list(self):
        result = verify.verify_package(self.package_with({"x": {"grammar": ".*"}}), harness_required=False,
                                       first_party=True, which=lambda name: "/bin/" + name)
        self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
