"""`delegated` for an action a module can describe: the `levels` field of a command may name an agent-run argument that the command also
`describes`, and only with `delegated`; the key of that argument then offers it. Increment B of the cutover plan of
2026-11-08; the decision is `2026-11-03-delegated-for-an-action-key-and-named-risk-profiles`.

Everything here is synthetic: a module named `sample-notes` with a command `run-it`. The installer knows no module, and no rule of a bridge:
the declaration says the command can describe the action, and the engine's rule is the hook's concern, not the installer's."""

import copy
import unittest

from tests.test_declarations import dump, module
from workbench import declarations as d
from workbench import levels, rendering, settings

ARGUMENTS = ["commit", "remove", "check", "wipe", "describe"]


def declared(**fields):
    base = {"helper": "scripts/run", "arguments": ARGUMENTS, "owner": ["wipe"], "describes": ["commit", "remove", "push"]}
    base.update(fields)
    return module(ships=["scripts"], commands={"run-it": base})


class Declaration(unittest.TestCase):
    def parse(self, decl):
        return d.parse_module(dump(decl), "sample", decl.get("name", "sample-notes"))

    def command(self, **fields):
        return self.parse(declared(**fields)).commands[0]

    def refused(self, **fields):
        with self.assertRaises(d.DeclarationError) as ctx:
            self.parse(declared(**fields))
        self.assertEqual("commands", ctx.exception.rule)
        self.assertNotIn("unknown key", str(ctx.exception))  # refused for its value, not as a field nobody knows
        return str(ctx.exception)

    def test_a_described_agent_run_argument_may_offer_delegated(self):
        got = self.command(levels={"commit": ["delegated"]})
        self.assertEqual((("commit", ("delegated",)),), got.levels)
        self.assertIsNone(got.preview)

    def test_it_may_sit_beside_the_levels_of_an_owner_run_argument(self):
        got = self.command(levels={"wipe": ["none"], "commit": ["delegated"]})
        self.assertEqual((("wipe", ("none",)), ("commit", ("delegated",))), got.levels)

    def test_an_argument_the_command_does_not_describe_is_refused(self):
        message = self.refused(levels={"check": ["delegated"]})
        self.assertIn("check", message)
        self.assertIn("describes", message)

    def test_an_action_that_is_described_but_is_not_an_argument_is_refused(self):
        self.assertIn("push", self.refused(levels={"push": ["delegated"]}))

    def test_describe_itself_is_refused_even_when_it_is_listed_as_an_action(self):
        self.refused(levels={"describe": ["delegated"]})
        self.refused(describes=["describe", "commit"], levels={"describe": ["delegated"]})

    def test_a_name_that_is_nowhere_is_refused(self):
        self.refused(levels={"nowhere": ["delegated"]})

    def test_only_delegated_is_offered_to_an_agent_run_argument(self):
        for bad in (["ask"], ["none"], ["block"], ["maybe"], ["DELEGATED"], ["delegated", "none"], ["delegated", "delegated"],
                    ["ask", "delegated"], [], "delegated", None, 3, [3], [None], [["delegated"]]):
            with self.subTest(wanted=bad):
                self.refused(levels={"commit": bad})

    def test_an_owner_run_argument_still_cannot_offer_delegated(self):
        self.assertIn("delegated", self.refused(levels={"wipe": ["delegated"]}, preview="check"))
        self.refused(owner=["commit"], levels={"commit": ["delegated"]})

    def test_an_argument_that_carries_an_asks_is_refused(self):
        self.refused(asks=["remove"], levels={"remove": ["delegated"]})

    def test_a_checkpoint_cannot_be_mapped_to_an_agent_run_argument(self):
        self.refused(levels={"commit": ["delegated"]}, checkpoint_of={"commit": "some-checkpoint"})

    def test_a_preview_goes_only_with_ask_so_delegated_alone_takes_none(self):
        self.refused(levels={"commit": ["delegated"]}, preview="check")

    def test_levels_that_are_not_an_object_are_still_refused(self):
        for bad in (["commit"], "commit", 3, None, True):
            self.refused(levels=bad)

    def test_a_declaration_without_the_field_is_unchanged(self):
        got = self.command()
        self.assertEqual((), got.levels)

    def test_the_field_is_part_of_the_declaration_hash(self):
        plain = copy.deepcopy(declared())
        marked = copy.deepcopy(declared(levels={"commit": ["delegated"]}))
        self.assertNotEqual(self.parse(plain).declaration, self.parse(marked).declaration)


class Keys(unittest.TestCase):
    """The registry reads the command as ``levels.command_entry`` hands it over."""

    def keys(self, **fields):
        decl = d.parse_module(dump(declared(**fields)), "sample", "sample-notes")
        return levels.registry(commands=[levels.command_entry(c) for c in decl.commands])

    def test_the_key_of_a_delegated_argument_offers_it_after_block_with_none_as_the_default(self):
        key = self.keys(levels={"commit": ["delegated"]})["wb run run-it commit"]
        self.assertEqual((levels.BLOCK, levels.DELEGATED, levels.NONE), key.offers)
        self.assertEqual(levels.NONE, key.default)
        self.assertTrue(key.agent)

    def test_another_described_argument_without_levels_offers_block_and_none_only(self):
        key = self.keys(levels={"commit": ["delegated"]})["wb run run-it remove"]
        self.assertEqual((levels.BLOCK, levels.NONE), key.offers)

    def test_without_the_field_the_key_offers_block_and_none_as_before(self):
        key = self.keys()["wb run run-it commit"]
        self.assertEqual((levels.BLOCK, levels.NONE), key.offers)

    def test_an_owner_run_key_is_unchanged(self):
        key = self.keys(levels={"wipe": ["none"], "commit": ["delegated"]})["wb run run-it wipe"]
        self.assertEqual((levels.BLOCK, levels.NONE), key.offers)
        self.assertEqual(levels.BLOCK, key.default)

    def test_with_agent_keys_left_out_the_argument_has_no_key(self):
        decl = d.parse_module(dump(declared(levels={"commit": ["delegated"]})), "sample", "sample-notes")
        found = levels.registry(commands=[levels.command_entry(c) for c in decl.commands], agent=False)
        self.assertNotIn("wb run run-it commit", found)

    def test_a_hand_built_command_cannot_offer_an_agent_run_argument_anything_but_delegated(self):
        for given in ("ask", "none", "block", "maybe"):
            keys = levels.registry(commands=[("t", (), ("go",), (("go", (given,)),))])
            self.assertEqual((levels.BLOCK, levels.NONE), keys["wb run t go"].offers, given)
        keys = levels.registry(commands=[("t", (), ("go",), (("go", ("delegated",)),))])
        self.assertEqual((levels.BLOCK, levels.DELEGATED, levels.NONE), keys["wb run t go"].offers)

    def test_a_hand_built_level_that_only_contains_the_word_does_not_offer_it(self):
        for given in ("delegated", "xdelegatedx", ["xdelegated"], (("delegated",),)):
            keys = levels.registry(commands=[("t", (), ("go",), (("go", given),))])
            self.assertEqual((levels.BLOCK, levels.NONE), keys["wb run t go"].offers, repr(given))

    def test_a_hand_built_command_still_cannot_offer_delegated_to_an_owner_run_argument(self):
        keys = levels.registry(commands=[("t", ("go",), ("go",), (("go", ("delegated",)),))])
        self.assertEqual((levels.BLOCK,), keys["wb run t go"].offers)

    def test_the_class_of_the_key_is_still_derived_reads(self):
        key = self.keys(levels={"commit": ["delegated"]})["wb run run-it commit"]
        self.assertEqual(levels.READS, key.klass)

    def test_no_profile_sets_the_key_to_delegated(self):
        key = self.keys(levels={"commit": ["delegated"]})["wb run run-it commit"]
        for profile in settings.PROFILES:
            self.assertIsNone(settings.profile_level(profile, key), profile)


class Rendering(unittest.TestCase):
    def test_until_the_rendering_knows_the_level_a_key_at_delegated_renders_a_deny(self):
        plan = rendering.plan({"wb run run-it commit": levels.DELEGATED})
        self.assertEqual("deny", plan.keys["wb run run-it commit"])
        self.assertEqual([], plan.ask)
        self.assertEqual([], plan.open)
        self.assertTrue(plan.deny)


if __name__ == "__main__":
    unittest.main()
