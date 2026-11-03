"""The registry holds every fact about a key, once: its kind, danger class, offered levels, default, spellings, preview, the
command that carries it out, whether a module declared a minimum prompt for it, and where it is documented.

Plan ``2026-11-02-permission-system-consistency``, increment E (decision ``2026-11-02-one-permission-registry-and-key-model``,
decisions 2 to 4). ``tests/test_levels.py`` is unchanged and still passes: the offered levels and the defaults do not move."""

import os
import unittest

from workbench import declarations, levels, rules

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A process module's checkpoints, as the code-work module declares them.
CHECKPOINTS = ("approve-plan", "push-shared-branch", "submit-remote-job", "fetch-remote-output", "change-direction",
               "accept-decision", "acknowledge-first-tier", "acknowledge-second-tier")
# (name, owner-run arguments, all arguments, levels, checkpoint_of, asks, preview) as ``levels.command_entry`` gives them.
GROUNDWORK = ("groundwork", ("accept",), ("accept", "preview"), (("accept", ("ask",)),), (("accept", "accept-decision"),),
              (), "preview")
REMOTE = ("remote-runner", ("fetch-overwrite",), ("profiles", "submit", "fetch", "fetch-overwrite"), (), (),
          ("submit", "fetch"), "")
REVIEW = ("review-engine", ("extend", "reset"), ("extend", "reset", "preview", "status"),
          (("extend", ("ask", "none")), ("reset", ("ask", "none"))), (), (), "preview")


def registry(*commands):
    return levels.registry(CHECKPOINTS, commands)


class WhereTheListsLive(unittest.TestCase):
    def test_the_installer_lists_are_defined_in_the_registry_module_and_rules_alias_them(self):
        for name in ("OWNER_RUN", "AGENT_SAFE", "HOOK_ENTRY_POINTS", "DISPATCHERS", "REACHES_ANOTHER_KEY", "PREVIEW_ACTIONS",
                     "SPELLINGS"):
            with self.subTest(name=name):
                self.assertTrue(hasattr(levels, name))
                self.assertIs(getattr(levels, name), getattr(rules, name))

    def test_the_old_tables_are_derived_from_the_one_table(self):
        self.assertEqual({name: spec.offers for name, spec in levels.INSTALLER_KEYS.items() if spec.offers}, levels._OFFERS)
        self.assertEqual({}, levels._DEFAULTS)

    def test_every_owner_run_command_is_in_the_one_table(self):
        names = set(levels.INSTALLER_KEYS)
        for command in rules.OWNER_RUN:
            if command == "acknowledge":
                self.assertIn("acknowledge-first-tier", names)
                self.assertIn("acknowledge-second-tier", names)
            else:
                self.assertIn("approve-plan" if command == "approve-plan" else "wb " + command, names)


class AnInstallerCommand(unittest.TestCase):
    def test_the_facts_of_a_command_with_a_preview(self):
        key = levels.registry()["wb install"]
        self.assertEqual(("command", "project", "wb preview install", rules.SPELLINGS, "wb install", False),
                         (key.kind, key.klass, key.preview, key.spellings, key.carried_by, key.asks))
        self.assertEqual((levels.BLOCK, levels.NONE), key.offers)
        self.assertEqual(levels.BLOCK, key.default)
        self.assertEqual("docs/development.md", key.anchor)

    def test_a_command_without_a_preview_has_none(self):
        self.assertEqual("", levels.registry()["wb attach"].preview)
        self.assertEqual("", levels.registry()["wb pin"].preview)

    def test_the_classes_of_the_installer_commands(self):
        keys = levels.registry()
        for name in ("wb install", "wb adopt", "wb upgrade", "wb add", "wb attach", "wb recover"):
            self.assertEqual("project", keys[name].klass, name)
        for name in ("wb approve", "wb pin", "wb rerender", "wb release-approvals", "approve-plan"):
            self.assertEqual("governs", keys[name].klass, name)

    def test_rerender_offers_block_only_and_says_so(self):
        key = levels.registry()["wb rerender"]
        self.assertEqual((levels.BLOCK,), key.offers)
        self.assertEqual("wb preview rerender", key.preview)

    def test_an_agent_safe_action_reads(self):
        key = levels.registry()["wb check"]
        self.assertEqual(("agent-safe", "reads", True, levels.NONE, rules.SPELLINGS),
                         (key.kind, key.klass, key.agent, key.default, key.spellings))
        self.assertEqual("reads", levels.registry()["wb preview install"].klass)


class ACheckpoint(unittest.TestCase):
    def test_a_checkpoint_the_agent_follows_is_a_rule_with_no_command(self):
        key = registry()["push-shared-branch"]
        self.assertEqual(("checkpoint", "governs", "", (), (levels.BLOCK,)),
                         (key.kind, key.klass, key.carried_by, key.spellings, key.offers))
        self.assertEqual("docs/specs/command-permissions.md", key.anchor)

    def test_every_checkpoint_is_in_the_class_that_governs(self):
        keys = registry()
        for name in CHECKPOINTS:
            self.assertEqual(("checkpoint", "governs"), (keys[name].kind, keys[name].klass), name)

    def test_approve_plan_is_a_checkpoint_carried_by_its_own_command(self):
        key = registry()["approve-plan"]
        self.assertEqual(("approve-plan", "wb plan-status", rules.SPELLINGS), (key.carried_by, key.preview, key.spellings))
        self.assertEqual((levels.BLOCK, levels.DELEGATED, levels.ASK, levels.NONE), key.offers)

    def test_a_checkpoint_mapped_to_a_command_is_carried_by_it_and_takes_its_preview(self):
        key = registry(GROUNDWORK)["accept-decision"]
        self.assertEqual(("wb run groundwork accept", "wb run groundwork preview", rules.SPELLINGS),
                         (key.carried_by, key.preview, key.spellings))
        self.assertIn(levels.ASK, key.offers)
        self.assertNotIn("wb run groundwork accept", registry(GROUNDWORK))

    def test_without_the_mapping_the_checkpoint_is_a_rule(self):
        key = registry()["accept-decision"]
        self.assertEqual(("", ()), (key.carried_by, key.spellings))

    def test_acknowledge_is_carried_by_its_command(self):
        self.assertEqual("wb acknowledge", registry()["acknowledge-first-tier"].carried_by)


class AModuleArgument(unittest.TestCase):
    def test_an_argument_with_an_asks_is_recorded_as_a_declared_minimum_and_is_in_the_class_that_governs(self):
        key = registry(REMOTE)["wb run remote-runner submit"]
        self.assertEqual(("argument", "governs", True, True, levels.NONE, rules.SPELLINGS),
                         (key.kind, key.klass, key.agent, key.asks, key.default, key.spellings))

    def test_an_argument_with_no_asks_that_only_reads_is_in_the_class_that_reads(self):
        key = registry(REMOTE)["wb run remote-runner profiles"]
        self.assertEqual(("argument", "reads", False, levels.NONE), (key.kind, key.klass, key.asks, key.default))

    def test_an_owner_run_argument_is_in_the_class_that_governs_and_defaults_to_block(self):
        key = registry(REMOTE)["wb run remote-runner fetch-overwrite"]
        self.assertEqual(("argument", "governs", False, False, levels.BLOCK),
                         (key.kind, key.klass, key.agent, key.asks, key.default))

    def test_the_review_engines_extend_reads_as_governs_until_a_module_can_declare_its_class(self):
        """Decision 4 puts ``extend``, ``archive`` and ``amend`` in the class of ``project``. The installer names no module and a
        declaration has no class field, so every owner-run argument reads as ``governs`` for now; a declared class (the
        follow-on plan) changes this test on purpose."""
        keys = registry(REVIEW)
        self.assertEqual("governs", keys["wb run review-engine extend"].klass)
        self.assertEqual("governs", keys["wb run review-engine reset"].klass)

    def test_an_owner_run_argument_that_offers_ask_names_its_declared_preview(self):
        keys = registry(REVIEW)
        self.assertEqual("wb run review-engine preview", keys["wb run review-engine extend"].preview)
        self.assertIn(levels.ASK, keys["wb run review-engine extend"].offers)

    def test_an_argument_that_offers_no_ask_has_no_preview(self):
        self.assertEqual("", registry(REMOTE)["wb run remote-runner fetch-overwrite"].preview)

    def test_an_argument_has_no_anchor_because_its_module_documents_it(self):
        self.assertEqual("", registry(REMOTE)["wb run remote-runner submit"].anchor)


class TheCommandEntry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loaded = declarations.load_package(os.path.join(REPO, "packages", "workbench"), first_party=True)
        cls.commands = {command.name: command for module in loaded.modules for command in module.commands}

    def test_it_gives_the_seven_facts_the_registry_reads_from_a_declaration(self):
        entry = levels.command_entry(self.commands["groundwork"])
        self.assertEqual(7, len(entry))
        command = self.commands["groundwork"]
        self.assertEqual((command.name, command.owner, command.arguments, command.levels, command.checkpoint_of,
                          command.asks, command.preview), entry)

    def test_it_carries_the_asks_of_a_module_that_declares_one(self):
        self.assertEqual(("submit", "fetch"), tuple(levels.command_entry(self.commands["remote-runner"])[5]))
        self.assertEqual(("remove",), tuple(levels.command_entry(self.commands["safe-git"])[5]))

    def test_the_registry_built_from_the_entries_records_the_asks(self):
        keys = levels.registry(CHECKPOINTS, [levels.command_entry(c) for c in self.commands.values()])
        for name in ("wb run remote-runner submit", "wb run remote-runner fetch", "wb run safe-git remove"):
            self.assertTrue(keys[name].asks, name)
        self.assertFalse(keys["wb run remote-runner status"].asks)


class TheOldFiveItemEntry(unittest.TestCase):
    def test_a_command_given_as_five_items_still_builds_the_same_keys_without_an_asks(self):
        old = ("remote-runner", ("fetch-overwrite",), ("profiles", "submit", "fetch", "fetch-overwrite"), (), ())
        keys = levels.registry(CHECKPOINTS, [old])
        self.assertFalse(keys["wb run remote-runner submit"].asks)
        self.assertEqual(levels.NONE, keys["wb run remote-runner submit"].default)
        self.assertEqual("governs", keys["wb run remote-runner fetch-overwrite"].klass)
        self.assertEqual("reads", keys["wb run remote-runner submit"].klass)


class TheOfferedLevelsAndDefaultsDoNotMove(unittest.TestCase):
    """The command entry adds facts and moves nothing: the five-item form and ``command_entry`` build the same keys, offers and
    defaults for the whole shipped package. This compares the new code with itself. What the offers and defaults were before the
    change is pinned by ``tests/test_levels.py`` (unchanged), by the drift test, and by a comparison of the committed tree with
    the working tree that the plan's Result records."""

    def test_the_offers_and_defaults_of_the_shipped_keys(self):
        loaded = declarations.load_package(os.path.join(REPO, "packages", "workbench"), first_party=True)
        checkpoints = [name for module in loaded.modules if module.type == "process" for name in module.checkpoints]
        old = levels.registry(checkpoints, [(c.name, c.owner, c.arguments, c.levels, c.checkpoint_of)
                                            for m in loaded.modules for c in m.commands])
        new = levels.registry(checkpoints, [levels.command_entry(c) for m in loaded.modules for c in m.commands])
        self.assertEqual(list(old), list(new))
        for name in old:
            self.assertEqual((old[name].offers, old[name].default, old[name].agent),
                             (new[name].offers, new[name].default, new[name].agent), name)


if __name__ == "__main__":
    unittest.main()
