"""The permission facts are kept in several places; this test lists where they disagree today and fails on any other.

Plan ``2026-11-02-permission-system-consistency``, increment D (decision ``2026-11-02-one-permission-registry-and-key-model``).
It reads the registry (``levels.registry``, built from the shipped declarations as the installer builds it), ``rules``, the
module declarations, the settings seed, the keys named in ``docs/specs/command-permissions.md`` ("Which levels a key offers"),
the owner-run rows of the table in ``docs/development.md`` and the shipped skills and agents. ``KNOWN`` is every disagreement
that exists now, each with the increment that ends it; the test fails on a disagreement that is not listed and on a listed one
that no longer exists, so a later increment removes an entry when it fixes the disagreement. When the list is empty the
registry is the one place the facts are written (completion criterion 4 of the plan).

Not read here, and so not covered by an empty ``KNOWN``: the rendering plan and the lines of ``wb settings`` (increment F moves
them onto the registry and its tests cover them), the launcher spellings against any text, a checkpoint that no command runs
against the skill that states it (increment K reads the agent-followed ones, ``STATED_RULES``), a level that an owner's own
settings file sets and the key does not offer (that is the owner's file, so ``wb doctor`` reads it, increment L) and the
`push-shared-branch` rule against the ``git push`` ask rule (a floor action is not a key). Increment K adds the readers of the
skills against the registry: ``skills_against_levels`` (never run a relaxed key), ``skills_state_their_checkpoints``,
``ask_flow`` (a text that names a key the owner may set to ask gives the flow) and ``closed_lists`` (a closed command list
that depends on a level holds ``wb settings``). Each reader below has a negative test that feeds it a disagreement, so it
cannot pass by finding nothing."""

import os
import re
import unittest
import unittest.mock

from workbench import declarations, doctor, levels, rules, settings

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PACKAGE = os.path.join(REPO, "packages", "workbench")
SPEC = os.path.join(REPO, "docs", "specs", "command-permissions.md")
DEVELOPMENT = os.path.join(REPO, "docs", "development.md")
INCREMENTS = tuple("ABCDEFGHIJKLM")

# The pairs of a checkpoint and the command that does the same act (decision ``2026-11-02-one-permission-registry-and-key-model``,
# decision 5): each has a key of its own, and the two can carry different defaults.
CHECKPOINT_PAIRS = {"submit-remote-job": "wb run remote-runner submit", "fetch-remote-output": "wb run remote-runner fetch"}

# Every disagreement that exists today, and the increment of the plan that ends it. The list is empty (completion criterion 4 of the
# plan): E ended three (the registry records an ``asks`` as a module's declared minimum), G three (the two pairs of a checkpoint and a
# command are recorded as deliberate, and the seed writes the table and not the version 1 object), K six (a skill said never run a key
# that the registry offers at ask or none) and M the last (``docs/development.md`` had no Owner-run row for ``release-approvals``). A
# disagreement found later is added here with the increment that will end it, or fixed.
KNOWN = {}


def modules():
    loaded = declarations.load_package(PACKAGE, first_party=True)
    if loaded.problems:
        raise AssertionError("the shipped package does not load: %s" % "; ".join(map(str, loaded.problems)))
    return loaded.modules


def registry(found, entries=None):
    """The registry as the installer builds it from the shipped declarations. `entries` replaces the command entries (a test
    gives the five-item form that records no ``asks``)."""
    checkpoints = [name for module in found if module.type == "process" for name in module.checkpoints]
    commands = entries if entries is not None else [levels.command_entry(command)
                                                   for module in found for command in module.commands]
    return levels.registry(checkpoints, commands)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def asks_against_level(found, keys):
    """A module renders an ask for an argument whose key defaults to ``none`` and the registry does not record the ask as the
    module's declared minimum: two mechanisms, and nothing says which one governs. (A recorded ``asks`` is deliberate, under
    ``2026-10-29-workbench-asks-for-remove-submit-and-fetch`` and decision 5 of ``2026-11-02-one-permission-registry-and-key-model``.)"""
    for module in found:
        for command in module.commands:
            for argument in command.asks:
                key = "wb run %s %s" % (command.name, argument)
                if key in keys and keys[key].default == levels.NONE and not keys[key].asks:
                    yield "asks-vs-level: %s defaults to none and its module renders an ask" % key


def anchors_against_documents(keys, texts=None):
    """A key that names a document as its anchor must be named in it: a command as ``workbench <command>`` or ``wb <command>``,
    a checkpoint by its name."""
    texts = {} if texts is None else dict(texts)
    for name, key in keys.items():
        if not key.anchor:
            continue
        text = texts.setdefault(key.anchor, read(os.path.join(REPO, key.anchor)))
        if key.kind == levels.CHECKPOINT:
            found = name in text
        else:
            command = name[3:] if name.startswith("wb ") else name
            found = ("workbench %s" % command) in text or ("wb %s" % command) in text
        if not found:
            yield "anchor: %s is not named in %s" % (name, key.anchor)


def checkpoint_pairs(keys, pairs=None, spec=""):
    """A checkpoint and the command that does the same act, with different defaults, must be recorded as a pair on purpose: one
    paragraph of the spec (`spec` is its text) names both."""
    recorded = groups(spec)
    for checkpoint, command in sorted((CHECKPOINT_PAIRS if pairs is None else pairs).items()):
        if (checkpoint in keys and command in keys and keys[checkpoint].default != keys[command].default
                and not any(checkpoint in group and command in group for group in recorded)):
            yield "checkpoint-pair: %s (%s) and %s (%s) govern one act and the spec does not record the pair" % (
                checkpoint, keys[checkpoint].default, command, keys[command].default)


def spec_offers(text):
    """``(ask keys, none keys)`` named in the bullet of `text` that lists the keys offering ``ask`` and ``none``."""
    start = text.index("\n- `ask`:") + 1
    end = text.index("\n\n", start)
    bullet = " ".join(line.strip() for line in text[start:end].splitlines())
    ask_part, none_part = bullet.split("`none`:", 1)
    none_part = none_part.split("every agent-safe action")[0]
    token = re.compile(r"(?:wb [a-z]+(?:-[a-z]+)*|[a-z]+(?:-[a-z]+)+)\Z")

    def names(part):
        return {found for found in re.findall(r"`([^`]+)`", part) if token.match(found)}
    return names(ask_part), names(none_part)


def spec_against_registry(keys, text):
    """The keys the spec says offer ``ask`` and ``none``, against the registry's installer keys. A name the spec uses that is no
    key at all is reported, not dropped."""
    installer = {name for name, key in keys.items() if not key.agent and not name.startswith("wb run ")}
    ask, none = spec_offers(text)
    for level, spec in (("ask", ask), ("none", none)):
        for name in sorted(spec - set(keys)):
            yield "spec-offers: the spec names %s at %s and the registry has no such key" % (name, level)
    registry_ask = {name for name in installer if levels.ASK in keys[name].offers}
    registry_none = {name for name in installer if levels.NONE in keys[name].offers}
    for level, spec, registered in (("ask", ask & installer, registry_ask), ("none", none & installer, registry_none)):
        for name in sorted(spec - registered):
            yield "spec-offers: the spec says %s offers %s and the registry does not" % (name, level)
        for name in sorted(registered - spec):
            yield "spec-offers: the registry offers %s at %s and the spec does not say so" % (name, level)


def development_owner_run_rows(text):
    words = set()
    for line in text.splitlines():
        if line.startswith("| Owner-run"):
            found = re.search(r"python3 -m workbench ([a-z][a-z-]*)", line)
            if found:
                words.add(found.group(1))
    return words


def development_against_rules(text):
    shown = development_owner_run_rows(text)
    for command in rules.OWNER_RUN:
        if command not in shown:
            yield ("development-table: %s is an owner-run command but no Owner-run row of docs/development.md shows it"
                   % command)


def neutral_texts():
    """``(relative path, text)`` of every shipped skill and agent file."""
    found = []
    for module in sorted(os.listdir(PACKAGE)):
        base = os.path.join(PACKAGE, module, "harness", "neutral")
        for folder, _, names in sorted(os.walk(base)):
            for name in sorted(names):
                if name.endswith(".md"):
                    path = os.path.join(folder, name)
                    found.append((os.path.relpath(path, PACKAGE), read(path)))
    return found


# One reader of "never run <key>" for the shipped texts and for the installed ones (``wb doctor``).
groups, named_token, names_key = doctor.groups, doctor.named_token, doctor.names_key


def skills_against_levels(keys, texts):
    never = re.compile(r"(?i)\b(?:never|do not|don't)\s+run\b")
    relaxed = {name: key for name, key in keys.items()
               if not key.agent and (levels.ASK in key.offers or levels.NONE in key.offers)}
    for path, text in texts:
        for group in groups(text):
            if not never.search(group):
                continue
            for name in sorted(relaxed):
                if names_key(group, name):
                    parts = path.split(os.sep)
                    yield "skill-vs-level: %s/%s says never run `%s`, which the registry offers at ask or none" % (
                        parts[0], parts[-2], named_token(name))


# The modules whose skills, agents and policy blocks speak of the checkpoints and the owner's levels. The FreeCAD and Verilog skills
# do not, and a word such as `reset` in backticks there is not a key.
GOVERNING = ("code-work", "groundwork", "review-engine", "remote-runner", "safe-git", "security-review", "mempalace")

# How a skill that the registry names in ``stated_by`` states the rule of an agent-followed checkpoint (increment G records which
# skill, and this says what the skill must say). The checkpoints that no command runs (``acknowledge-*``) are carried by
# ``wb acknowledge`` and stated by the policy block in ``AGENTS.md``.
STATED_RULES = {
    "push-shared-branch": r"(?i)push only on the owner.s word",
    "submit-remote-job": r"(?i)submit and fetch only on the owner.s word",
    "fetch-remote-output": r"(?i)submit and fetch only on the owner.s word",
    "change-direction": r"(?i)direction.{0,80}needs the owner",
}


def governing(texts):
    return [(path, text) for path, text in texts if path.split(os.sep)[0] in GOVERNING]


def block_texts():
    """``(relative path, text)`` of the policy block that each shipped module renders into the root file."""
    found = []
    for module in sorted(os.listdir(PACKAGE)):
        path = os.path.join(PACKAGE, module, "files", "blocks", "policy.md")
        if os.path.exists(path):
            found.append((os.path.relpath(path, PACKAGE), read(path)))
    return found


def label(path):
    parts = path.split(os.sep)
    return "%s/%s" % (parts[0], parts[-2] if parts[-1] == "SKILL.md" else os.path.splitext(parts[-1])[0])


def names_to_use(group, key):
    """Whether `group` names `key` to use it. Reading its level (``level approve-plan: delegated``, ``checkpoint approve-plan:
    delegate``) is not using it."""
    return names_key(re.sub(r"\b(?:level|checkpoint)\s+[a-z][a-z -]*?:", " ", group), key)


def skills_state_their_checkpoints(keys, texts):
    """The skill that the registry names for an agent-followed checkpoint exists and says the rule that checkpoint holds."""
    for name, key in sorted(keys.items()):
        for skill in key.stated_by:
            found = [text for path, text in texts if path.split(os.sep)[-2:] == [skill, "SKILL.md"]]
            if not found:
                yield "stated-by: %s names the skill %s and no shipped skill has that name" % (name, skill)
            elif name not in STATED_RULES or not re.search(STATED_RULES[name], " ".join(groups(found[0]))):
                yield "stated-by: the skill %s does not state the rule of %s" % (skill, name)


def ask_flow(keys, texts):
    """A skill, agent or policy block that names a key the owner may set to ``ask`` gives the flow of that level: it reads
    ``wb settings``, runs the key's preview, and runs the command with ``--digest``."""
    asking = {name: key for name, key in keys.items() if not key.agent and levels.ASK in key.offers}
    for path, text in texts:
        for name in sorted(asking):
            if any(names_to_use(group, name) for group in groups(text)):
                missing = [part for part in ("wb settings", "--digest", asking[name].preview) if part and part not in text]
                if missing:
                    yield "ask-flow: %s names `%s` and does not state the ask flow (missing %s)" % (
                        label(path), named_token(name), ", ".join(missing))


def closed_lists(keys, texts):
    """A closed list of commands ("Use only ... Run no other command") in a text that names a key the owner may relax holds
    ``wb settings``, which is the command that reads the level."""
    relaxed = {name for name, key in keys.items() if not key.agent and (levels.ASK in key.offers or levels.NONE in key.offers)}
    closing = re.compile(r"(?i)\b(?:use only|run no other)\b")
    for path, text in texts:
        found = groups(text)
        if not any(names_to_use(group, name) for group in found for name in relaxed):
            continue
        for group in found:
            if closing.search(group) and "wb settings" not in group:
                yield "closed-list: %s names a command list that leaves out `wb settings`" % label(path)


def seed_against_version_two():
    if "checkpoints" in settings._seed_document():
        yield "settings-seed: a new settings file is written with the version 1 checkpoints object"


def disagreements():
    found = modules()
    keys = registry(found)
    result = []
    for source in (asks_against_level(found, keys), anchors_against_documents(keys), checkpoint_pairs(keys, spec=read(SPEC)),
                   spec_against_registry(keys, read(SPEC)),
                   development_against_rules(read(DEVELOPMENT)), skills_against_levels(keys, neutral_texts()),
                   skills_state_their_checkpoints(keys, neutral_texts()),
                   ask_flow(keys, governing(neutral_texts()) + block_texts()),
                   closed_lists(keys, governing(neutral_texts())),
                   seed_against_version_two()):
        result.extend(source)
    return sorted(set(result))


def compare(now, known):
    """What differs between the disagreements found `now` and the `known` ones."""
    return {"not listed": sorted(set(now) - set(known)), "listed but gone": sorted(set(known) - set(now))}


class Drift(unittest.TestCase):
    def test_the_disagreements_are_the_known_ones(self):
        self.assertEqual({"not listed": [], "listed but gone": []}, compare(disagreements(), KNOWN))

    def test_a_listed_disagreement_names_the_increment_that_ends_it(self):
        for disagreement, increment in KNOWN.items():
            with self.subTest(disagreement=disagreement):
                self.assertIn(increment, INCREMENTS)

    def test_a_stale_or_a_new_disagreement_fails_the_comparison(self):
        """The list shrinks only when a disagreement is fixed, and grows only on purpose."""
        now = disagreements()
        stale = dict(KNOWN, **{"asks-vs-level: wb run nothing nowhere defaults to none and its module renders an ask": "E"})
        self.assertEqual(["asks-vs-level: wb run nothing nowhere defaults to none and its module renders an ask"],
                         compare(now, stale)["listed but gone"])
        self.assertEqual([], compare(now, stale)["not listed"])
        self.assertEqual(["invented: a disagreement nobody listed"],
                         compare(now + ["invented: a disagreement nobody listed"], KNOWN)["not listed"])

    def test_the_readers_are_not_empty(self):
        """A parser that finds nothing would pass the comparison for the wrong reason."""
        found = modules()
        keys = registry(found)
        self.assertGreaterEqual(len(found), 13)
        self.assertIn("approve-plan", keys)
        self.assertGreaterEqual(len(keys), 40)
        ask, none = spec_offers(read(SPEC))
        self.assertEqual({"approve-plan", "accept-decision", "wb release-approvals", "wb install", "wb adopt", "wb upgrade",
                          "wb add", "wb recover", "acknowledge-first-tier", "wb approve", "wb pin"}, ask)
        self.assertGreaterEqual(len(none), 12)
        self.assertGreaterEqual(len(development_owner_run_rows(read(DEVELOPMENT))), 10)
        texts = neutral_texts()
        self.assertGreaterEqual(len(texts), 15)
        self.assertTrue(any(path.endswith("peer-review/SKILL.md") for path, _ in texts))


class EachReaderFindsADisagreementItIsGiven(unittest.TestCase):
    """The negative test of every reader: a changed input produces the disagreement, so none passes by finding nothing."""

    @classmethod
    def setUpClass(cls):
        cls.found = modules()
        cls.keys = registry(cls.found)

    def test_an_ask_against_a_level(self):
        """With the five-item entries, which carry no ``asks``, the registry does not record the minimum and the reader reports
        the three keys; with the entries the installer builds, it records them and the reader finds nothing."""
        old = [(c.name, c.owner, c.arguments, c.levels, c.checkpoint_of) for m in self.found for c in m.commands]
        unrecorded = registry(self.found, entries=old)
        self.assertEqual(["asks-vs-level: wb run remote-runner fetch defaults to none and its module renders an ask",
                          "asks-vs-level: wb run remote-runner submit defaults to none and its module renders an ask",
                          "asks-vs-level: wb run safe-git remove defaults to none and its module renders an ask"],
                         sorted(asks_against_level(self.found, unrecorded)))
        self.assertEqual([], list(asks_against_level(self.found, self.keys)))

    def test_an_anchor_that_does_not_name_its_key(self):
        self.assertEqual([], list(anchors_against_documents(self.keys)))
        empty = {key.anchor: "" for key in self.keys.values() if key.anchor}
        reported = list(anchors_against_documents(self.keys, empty))
        self.assertIn("anchor: wb install is not named in docs/development.md", reported)
        self.assertIn("anchor: approve-plan is not named in docs/specs/command-permissions.md", reported)

    def test_a_pair_of_a_checkpoint_and_a_command(self):
        """The pairing is recorded by the spec (decision 2 of ``2026-11-03-conformance-tests-name-modules-and-module-pins-follow-the-levels``),
        not by the registry: a pair whose defaults differ is a disagreement unless one paragraph of the spec names both."""
        spec = read(SPEC)
        self.assertEqual([], list(checkpoint_pairs(self.keys, spec=spec)))
        self.assertEqual(sorted("checkpoint-pair: %s" % name for name in CHECKPOINT_PAIRS),
                         sorted(line.split(" (")[0] for line in checkpoint_pairs(self.keys, spec="no pair is named here\n")))
        half = "\n\n".join(["The checkpoints `submit-remote-job` and `wb run remote-runner submit` keep a level each.",
                            "Another paragraph names `fetch-remote-output`.", "And this one `wb run remote-runner fetch`."])
        self.assertEqual(["checkpoint-pair: fetch-remote-output"],
                         [line.split(" (")[0] for line in checkpoint_pairs(self.keys, spec=half)])
        same = dict(self.keys)
        same["wb run remote-runner submit"] = same["submit-remote-job"]
        same["wb run remote-runner fetch"] = same["fetch-remote-output"]
        self.assertEqual([], list(checkpoint_pairs(same, spec="nothing")))  # one default for the pair: nothing to record

    def test_the_spec_names_a_key_that_does_not_exist_or_leaves_one_out(self):
        text = read(SPEC)
        self.assertEqual([], list(spec_against_registry(self.keys, text)))
        invented = text.replace("- `ask`: `approve-plan`,", "- `ask`: `approve-plan`, `wb bogus-command`,", 1)
        self.assertIn("spec-offers: the spec names wb bogus-command at ask and the registry has no such key",
                      list(spec_against_registry(self.keys, invented)))
        # The spec names it twice inside the ask bullet (the second time quoting the heading of its own section).
        left_out = text.replace(
            '`wb release-approvals` (a digest of the preview of its release, "`wb release-approvals` at `ask`")',
            '(a digest of the preview of its release, "the release at `ask`")', 1)
        self.assertNotEqual(text, left_out)
        self.assertIn("spec-offers: the registry offers wb release-approvals at ask and the spec does not say so",
                      list(spec_against_registry(self.keys, left_out)))
        extra = text.replace("`ask`: `approve-plan`,", "`ask`: `approve-plan`, `wb attach`,", 1)
        self.assertIn("spec-offers: the spec says wb attach offers ask and the registry does not",
                      list(spec_against_registry(self.keys, extra)))

    def test_the_development_table_without_a_row(self):
        text = read(DEVELOPMENT)
        self.assertEqual([], list(development_against_rules(text)))
        no_release = "\n".join(line for line in text.splitlines() if "python3 -m workbench release-approvals" not in line)
        self.assertIn("development-table: release-approvals is an owner-run command but no Owner-run row of "
                      "docs/development.md shows it", list(development_against_rules(no_release)))
        without = "\n".join(line for line in text.splitlines() if "python3 -m workbench pin " not in line)
        self.assertIn("development-table: pin is an owner-run command but no Owner-run row of docs/development.md shows it",
                      list(development_against_rules(without)))

    def test_a_skill_that_says_never_run_a_key_that_is_relaxed(self):
        said = [("some-module/harness/neutral/skills/x/SKILL.md",
                 "- `extend` and `reset` are the owner's. Never run them; ask the owner.\n")]
        self.assertEqual(["skill-vs-level: some-module/x says never run `extend`, which the registry offers at ask or none",
                          "skill-vs-level: some-module/x says never run `reset`, which the registry offers at ask or none"],
                         list(skills_against_levels(self.keys, said)))

    def test_a_skill_that_says_never_run_a_key_that_offers_only_block_is_not_a_disagreement(self):
        said = [("some-module/harness/neutral/skills/x/SKILL.md", "- Never run `init` or `mine`. Those are the owner's.\n")]
        self.assertEqual([], list(skills_against_levels(self.keys, said)))

    def test_a_skill_that_names_a_key_without_saying_never_run_is_not_a_disagreement(self):
        said = [("some-module/harness/neutral/skills/x/SKILL.md",
                 "- Run `extend` only after the preview. Never set the status to Accepted by hand.\n")]
        self.assertEqual([], list(skills_against_levels(self.keys, said)))

    def test_the_name_inside_a_longer_name_does_not_count(self):
        said = [("some-module/harness/neutral/skills/x/SKILL.md", "- Never run delegate-approve-plan early.\n")]
        self.assertEqual([], list(skills_against_levels(self.keys, said)))
        said = [("some-module/harness/neutral/skills/x/SKILL.md", "- Never run approve-plan early.\n")]
        self.assertEqual(1, len(list(skills_against_levels(self.keys, said))))

    def test_a_skill_that_is_missing_or_does_not_state_its_checkpoint(self):
        self.assertEqual([], list(skills_state_their_checkpoints(self.keys, neutral_texts())))
        self.assertIn("stated-by: push-shared-branch names the skill push-changes and no shipped skill has that name",
                      list(skills_state_their_checkpoints(self.keys, [])))
        silent = [("code-work/harness/neutral/skills/push-changes/SKILL.md", "# Push\n\nPush when it looks fine.\n")]
        self.assertEqual(["stated-by: the skill push-changes does not state the rule of push-shared-branch"],
                         [line for line in skills_state_their_checkpoints(self.keys, silent) if "push-changes" in line])

    def test_the_rule_of_each_agent_followed_checkpoint_is_set(self):
        stated = {name for name, key in self.keys.items() if key.stated_by}
        self.assertEqual({"push-shared-branch", "submit-remote-job", "fetch-remote-output", "change-direction"}, stated)
        self.assertEqual(stated, set(STATED_RULES))

    def test_a_text_that_names_a_key_at_ask_without_the_ask_flow(self):
        path = "some-module/harness/neutral/skills/x/SKILL.md"
        self.assertEqual(["ask-flow: some-module/x names `extend` and does not state the ask flow "
                          "(missing wb settings, --digest, wb run review-engine preview)"],
                         list(ask_flow(self.keys, [(path, "- Run `extend` when the owner asks.\n")])))
        whole = ("- Run `wb settings`. At ask run `wb run review-engine preview extend <document> <n>`, then `extend` "
                 "with `--digest <digest>`.\n")
        self.assertEqual([], list(ask_flow(self.keys, [(path, whole)])))
        partial = "- Run `wb settings`, then `extend` after `wb run review-engine preview extend`.\n"
        self.assertEqual(["ask-flow: some-module/x names `extend` and does not state the ask flow (missing --digest)"],
                         list(ask_flow(self.keys, [(path, partial)])))

    def test_reading_the_level_of_a_key_is_not_using_it(self):
        path = "some-module/harness/neutral/skills/x/SKILL.md"
        reads = "- Run `wb settings`. Go on only if it prints `level approve-plan: delegated`.\n- Use only reading.\n"
        self.assertEqual([], list(ask_flow(self.keys, [(path, reads)])))
        self.assertEqual([], list(closed_lists(self.keys, [(path, reads)])))
        uses = "- Run `wb approve-plan docs/plans/x.md` when it reads delegated.\n"
        self.assertEqual(1, len(list(ask_flow(self.keys, [(path, uses)]))))

    def test_a_text_that_names_a_key_that_cannot_be_set_to_ask_needs_no_ask_flow(self):
        path = "some-module/harness/neutral/skills/x/SKILL.md"
        self.assertEqual([], list(ask_flow(self.keys, [(path, "- Never run `init` or `mine`.\n- Run `wb run safe-git commit`.\n")])))

    def test_the_policy_blocks_are_read_by_the_ask_flow_reader(self):
        found = block_texts()
        self.assertGreaterEqual(len(found), 3)
        gone = [(path, text.replace("--digest", "")) for path, text in found]
        self.assertTrue(any(line.startswith("ask-flow: groundwork/policy names `accept-decision`")
                            for line in ask_flow(self.keys, gone)))

    def test_a_closed_command_list_that_leaves_out_the_command_that_reads_the_level(self):
        path = "some-module/harness/neutral/skills/x/SKILL.md"
        short = "- Run `extend` at the level.\n- Use only reading, searching and editing. Run no other command.\n"
        self.assertEqual(["closed-list: some-module/x names a command list that leaves out `wb settings`"],
                         list(closed_lists(self.keys, [(path, short)])))
        fixed = short.replace("editing.", "editing and `wb settings`.")
        self.assertEqual([], list(closed_lists(self.keys, [(path, fixed)])))
        unrelated = "- Use only reading and searching. Run no other command.\n"
        self.assertEqual([], list(closed_lists(self.keys, [(path, unrelated)])))

    def test_the_governing_texts_are_found(self):
        found = governing(neutral_texts())
        self.assertTrue(any(path.endswith("draft-plan/SKILL.md") for path, _ in found))
        self.assertFalse(any(path.startswith("freecad") for path, _ in found))

    def test_a_seed_with_the_version_one_object(self):
        self.assertEqual([], list(seed_against_version_two()))
        with unittest.mock.patch.object(settings, "_seed_document", lambda: {"version": 1, "checkpoints": {}}):
            self.assertEqual(1, len(list(seed_against_version_two())))


if __name__ == "__main__":
    unittest.main()
