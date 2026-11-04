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
        self.assertEqual((levels.BLOCK, levels.ASK, levels.NONE), key.offers)  # ask since increment B of the installer plan
        self.assertEqual(levels.BLOCK, key.default)
        self.assertEqual("docs/development.md", key.anchor)

    def test_a_command_without_a_preview_has_none(self):
        self.assertEqual("", levels.registry()["wb attach"].preview)

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

    def test_a_checkpoint_the_agent_follows_names_the_skills_that_state_it(self):
        keys = registry()
        self.assertEqual({"push-shared-branch": ("push-changes",), "submit-remote-job": ("run-remote-job",),
                          "fetch-remote-output": ("run-remote-job",), "change-direction": ("draft-roadmap", "draft-spec")},
                         {name: key.stated_by for name, key in keys.items() if key.stated_by})
        self.assertEqual(levels.STATED_BY, {name: key.stated_by for name, key in keys.items() if key.stated_by})

    def test_a_checkpoint_a_command_carries_names_no_skill_here(self):
        """Its skill is the one that runs the command (checked by increment K); the registry records the rules only."""
        keys = registry(GROUNDWORK)
        for name in ("approve-plan", "accept-decision", "acknowledge-first-tier", "acknowledge-second-tier", "wb install"):
            self.assertEqual((), keys[name].stated_by, name)

    def test_the_stated_skills_belong_to_declared_checkpoints_that_no_command_carries(self):
        keys = registry()
        for name in levels.STATED_BY:
            self.assertEqual(("checkpoint", ""), (keys[name].kind, keys[name].carried_by), name)

    def test_the_registry_keeps_no_pairing_of_a_checkpoint_with_a_command_of_a_module(self):
        """``2026-11-03-conformance-tests-name-modules-and-module-pins-follow-the-levels``, decision 2: the installer's source names no
        module, so the pairing that increment G recorded (``paired_with``, ``PAIRED_ACTS``) is gone. It is kept by the drift test
        (``CHECKPOINT_PAIRS``) and the spec. The two keep a level each, as decision 5 of
        ``2026-11-02-one-permission-registry-and-key-model`` settles: the checkpoint reads ``block``, the command ``none``."""
        self.assertNotIn("paired_with", levels.Key._fields)
        for name in ("PAIRED_ACTS", "_PAIRED_BACK"):
            self.assertFalse(hasattr(levels, name), name)
        keys = registry(REMOTE)
        for checkpoint, command in (("submit-remote-job", "wb run remote-runner submit"),
                                    ("fetch-remote-output", "wb run remote-runner fetch")):
            self.assertEqual(("block", "none"), (keys[checkpoint].default, keys[command].default), checkpoint)


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


def old_gate_words(key):
    """``command_gate.words`` as it was before increment F, frozen: it parsed a key's name on its own."""
    if key in levels.COMMAND_OF_CHECKPOINT:
        return [levels.COMMAND_OF_CHECKPOINT[key]]
    if key == "approve-plan":
        return ["approve-plan"]
    parts = key.split(" ")
    if parts[:2] == ["wb", "run"] and len(parts) >= 4:
        return parts[2:]
    if parts[0] == "wb" and len(parts) == 2:
        return [parts[1]]
    return []


def old_key_patterns(key):
    """``rendering.key_patterns`` as it was before increment F, frozen: it parsed a key's name a second way."""
    agent_words = frozenset(name[3:] for name in levels.agent_keys() if " " not in name[3:])
    if key == levels.APPROVE_PLAN:
        return rules.owner_run_command_patterns(key)
    if key in levels.COMMAND_OF_CHECKPOINT:
        return rules.owner_run_command_patterns(levels.COMMAND_OF_CHECKPOINT[key])
    if key.startswith("wb run "):
        parts = key.split(" ")
        if len(parts) >= 4:
            return rules.command_owner_patterns(parts[2], [" ".join(parts[3:])])
        return []
    if key.startswith("wb preview "):
        action = key[len("wb preview "):]
        return rules.owner_run_command_patterns("preview " + action) if action in rules.PREVIEW_ACTIONS else []
    if key.startswith("wb ") and (key[3:] in rules.OWNER_RUN or key[3:] in agent_words):
        return rules.owner_run_command_patterns(key[3:])
    return []


def old_by_launcher(key):
    """``command_gate._by_launcher`` as it was before increment F, frozen."""
    return bool(old_gate_words(key)) and key != "approve-plan" and not key.startswith("wb run ")


def old_forms(key, store_bin):
    """``command_gate.forms`` as it was before increment F, frozen: the patterns, as text."""
    import re
    from workbench import command_gate
    heads = ["wb", re.escape(store_bin)]
    if key == "approve-plan":
        return ["%s approve-plan %s( --digest %s)?" % (head, command_gate._PATH, command_gate._DIGEST) for head in heads]
    found = old_gate_words(key)
    if not found:
        return []
    tail = " ".join(re.escape(word) for word in found)
    middle = " run " if key.startswith("wb run ") else " "
    return ["%s%s%s(?: %s)*" % (head, middle, tail, command_gate._TOKEN) for head in heads]


def old_reads_argument_as_data(text, key, store_bin):
    """``command_gate.reads_argument_as_data`` as it was before increment F, frozen."""
    import re
    from workbench import command_gate
    found = old_gate_words(key)
    if not key.startswith("wb run ") or len(found) != 2 or not command_gate.literal_run(text, store_bin):
        return False
    heads = "|".join(["wb", re.escape(store_bin)])
    call = re.fullmatch(r"(?:%s) run (%s) (%s)(?: %s)*" % (heads, command_gate._RUN_NAME, command_gate._RUN_PLAIN,
                                                           command_gate._RUN_ARGUMENT), text)
    return bool(call) and call.group(1) == found[0] and command_gate._folded(call.group(2)) != command_gate._folded(found[1])


CALLS = ("wb run review-engine preview docs/x.md 2", "wb run review-engine extend docs/x.md 2", "wb run groundwork accept x",
         "wb run groundwork preview x", "wb run tool look", "wb run tool look extra", "wb install", "wb run a b c", "")
STORE_BIN = "/home/owner/.config/project-workbench/bin/wb"

ODD_KEYS = ("", "wb", "wb run", "wb run x", "wb run x y", "wb run x y z", "wb run  x y", "wb preview", "wb preview install",
            "wb preview release-approvals", "wb preview nonsense", "wb preview a b", "wb install", "wb nonsense", "approve-plan",
            "acknowledge-first-tier", "acknowledge-second-tier", "accept-decision", "push-shared-branch", "wb  install",
            " wb install", "wb install ", "WB install", "wb check", "wb gate", "wb run tool look", "wb acknowledge", "wb pin x")


class TheOneParserOfAKeysName(unittest.TestCase):
    """``levels.command_words`` is the single place a key's name is read as a command; the rendering and the command gate
    use it, and give the same answers as the two parsers they replaced."""

    @classmethod
    def setUpClass(cls):
        loaded = declarations.load_package(os.path.join(REPO, "packages", "workbench"), first_party=True)
        checkpoints = [name for m in loaded.modules if m.type == "process" for name in m.checkpoints]
        cls.real = list(levels.registry(checkpoints, [levels.command_entry(c) for m in loaded.modules for c in m.commands]))

    def test_the_words_of_the_keys_that_name_a_command(self):
        for key, words in (("approve-plan", ("approve-plan",)), ("acknowledge-first-tier", ("acknowledge",)),
                           ("wb install", ("install",)), ("wb pin", ("pin",)), ("wb check", ("check",)),
                           ("wb preview install", ("preview", "install")), ("wb run tool look", ("run", "tool", "look")),
                           ("wb run a b c", ("run", "a", "b", "c"))):
            with self.subTest(key=key):
                self.assertEqual(words, levels.command_words(key))

    def test_the_keys_that_name_no_command(self):
        for key in ("", "wb", "wb run x", "acknowledge-second-tier", "accept-decision", "push-shared-branch", "WB install",
                    " wb install", "wb preview a b"):
            with self.subTest(key=key):
                self.assertEqual((), levels.command_words(key))

    def test_the_gate_reads_the_same_words_as_before_for_every_key(self):
        from workbench import command_gate
        for key in self.real + list(ODD_KEYS):
            with self.subTest(key=key):
                self.assertEqual(old_gate_words(key), command_gate.words(key))

    def test_the_other_gate_readers_of_a_key_give_the_same_answers_as_before_for_every_key(self):
        """``_by_launcher``, ``forms`` and ``reads_argument_as_data`` were rewritten to ask ``command_words`` as well."""
        from workbench import command_gate
        for key in self.real + list(ODD_KEYS):
            with self.subTest(key=key):
                self.assertEqual(old_by_launcher(key), command_gate._by_launcher(key))
                self.assertEqual(old_forms(key, STORE_BIN), [form.pattern for form in command_gate.forms(key, STORE_BIN)])
                for text in CALLS:
                    self.assertEqual(old_reads_argument_as_data(text, key, STORE_BIN),
                                     command_gate.reads_argument_as_data(text, key, STORE_BIN), text)

    def test_the_rendering_reads_the_same_patterns_as_before_for_every_key(self):
        from workbench import rendering
        for key in self.real + list(ODD_KEYS):
            with self.subTest(key=key):
                self.assertEqual(old_key_patterns(key), rendering.key_patterns(key))

    def test_the_two_readers_no_longer_parse_a_key_themselves(self):
        for name in ("command_gate.py", "rendering.py"):
            with open(os.path.join(REPO, "workbench", name), encoding="utf-8") as handle:
                text = handle.read()
            with self.subTest(file=name):
                self.assertTrue("command_words(" in text, "%s does not use levels.command_words" % name)
                self.assertFalse('key.split(" ")' in text, "%s splits a key's name itself" % name)
                self.assertFalse('startswith("wb run ")' in text, "%s tests a key's name for a module argument itself" % name)


if __name__ == "__main__":
    unittest.main()
