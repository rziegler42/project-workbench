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
against the skill that states it (increment G, with K), a level that an owner's own settings file sets and the key does not
offer (that is the owner's file, so ``wb doctor`` reads it, increment L), the skills' omission of the ``ask`` flow and the
`push-shared-branch` rule against the ``git push`` ask rule (a floor action is not a key). Each reader below has a negative
test that feeds it a disagreement, so it cannot pass by finding nothing."""

import os
import re
import unittest
import unittest.mock

from workbench import declarations, levels, rules, settings

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PACKAGE = os.path.join(REPO, "packages", "workbench")
SPEC = os.path.join(REPO, "docs", "specs", "command-permissions.md")
DEVELOPMENT = os.path.join(REPO, "docs", "development.md")
INCREMENTS = tuple("ABCDEFGHIJKLM")

# The pairs of a checkpoint and the command that does the same act (decision ``2026-11-02-one-permission-registry-and-key-model``,
# decision 5): each has a key of its own, and the two can carry different defaults.
CHECKPOINT_PAIRS = {"submit-remote-job": "wb run remote-runner submit", "fetch-remote-output": "wb run remote-runner fetch"}

# Every disagreement that exists today, and the increment of the plan that ends it. (E ended three: the registry now records an
# ``asks`` as a module's declared minimum, so it is no longer a disagreement.) G: a checkpoint has one setting and a command that
# implements one reads it, and the seed stops writing the version 1 object; K: the skills say what the registry says; M: the
# document.
KNOWN = {
    "checkpoint-pair: fetch-remote-output (block) and wb run remote-runner fetch (none) govern one act": "G",
    "checkpoint-pair: submit-remote-job (block) and wb run remote-runner submit (none) govern one act": "G",
    "development-table: release-approvals is an owner-run command but no Owner-run row of docs/development.md shows it": "M",
    "settings-seed: a new settings file is written with the version 1 checkpoints object": "G",
    "skill-vs-level: code-work/delegate-approval says never run `approve-plan`, which the registry offers at ask or none": "K",
    "skill-vs-level: review-engine/peer-review says never run `amend`, which the registry offers at ask or none": "K",
    "skill-vs-level: review-engine/peer-review says never run `archive`, which the registry offers at ask or none": "K",
    "skill-vs-level: review-engine/peer-review says never run `extend`, which the registry offers at ask or none": "K",
    "skill-vs-level: review-engine/peer-review says never run `prune`, which the registry offers at ask or none": "K",
    "skill-vs-level: review-engine/peer-review says never run `reset`, which the registry offers at ask or none": "K",
}


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


def checkpoint_pairs(keys, pairs=None):
    for checkpoint, command in sorted((CHECKPOINT_PAIRS if pairs is None else pairs).items()):
        if checkpoint in keys and command in keys and keys[checkpoint].default != keys[command].default:
            yield "checkpoint-pair: %s (%s) and %s (%s) govern one act" % (
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


def groups(text):
    """The paragraphs and list items of `text`, each as one string."""
    current, found = [], []
    for line in text.splitlines():
        if not line.strip() or re.match(r"\s*(?:- |\d+\. )", line):
            if current:
                found.append(" ".join(current))
            current = [line.strip()] if line.strip() else []
        else:
            current.append(line.strip())
    if current:
        found.append(" ".join(current))
    return found


def named_token(key):
    """How a skill names `key`: the argument of ``wb run <command> <argument>`` (in backticks), the whole of ``wb <word>``
    (in backticks), or a checkpoint's name (in backticks or bare, but not inside a longer name such as
    ``delegate-approve-plan``)."""
    parts = key.split(" ")
    return parts[-1] if key.startswith("wb run ") else key


def names_key(group, key):
    token = named_token(key)
    if "`%s`" % token in group:
        return True
    return " " not in key and re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(token), group) is not None


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


def seed_against_version_two():
    if "checkpoints" in settings._seed_document():
        yield "settings-seed: a new settings file is written with the version 1 checkpoints object"


def disagreements():
    found = modules()
    keys = registry(found)
    result = []
    for source in (asks_against_level(found, keys), anchors_against_documents(keys), checkpoint_pairs(keys),
                   spec_against_registry(keys, read(SPEC)),
                   development_against_rules(read(DEVELOPMENT)), skills_against_levels(keys, neutral_texts()),
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
        fewer = {key: value for key, value in KNOWN.items() if not key.startswith("settings-seed")}
        self.assertEqual(1, len(compare(now, fewer)["not listed"]))

    def test_the_readers_are_not_empty(self):
        """A parser that finds nothing would pass the comparison for the wrong reason."""
        found = modules()
        keys = registry(found)
        self.assertGreaterEqual(len(found), 13)
        self.assertIn("approve-plan", keys)
        self.assertGreaterEqual(len(keys), 40)
        ask, none = spec_offers(read(SPEC))
        self.assertEqual({"approve-plan", "accept-decision", "wb release-approvals"}, ask)
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
        self.assertEqual(sorted("checkpoint-pair: %s" % name for name in CHECKPOINT_PAIRS),
                         sorted(line.split(" (")[0] for line in checkpoint_pairs(self.keys)))
        same = dict(self.keys)
        same["wb run remote-runner submit"] = same["submit-remote-job"]
        same["wb run remote-runner fetch"] = same["fetch-remote-output"]
        self.assertEqual([], list(checkpoint_pairs(same)))

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
        extra = text.replace("`ask`: `approve-plan`,", "`ask`: `approve-plan`, `wb install`,", 1)
        self.assertIn("spec-offers: the spec says wb install offers ask and the registry does not",
                      list(spec_against_registry(self.keys, extra)))

    def test_the_development_table_without_a_row(self):
        text = read(DEVELOPMENT)
        self.assertEqual(["development-table: release-approvals is an owner-run command but no Owner-run row of "
                          "docs/development.md shows it"], list(development_against_rules(text)))
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

    def test_a_seed_with_the_version_one_object(self):
        self.assertEqual(1, len(list(seed_against_version_two())))
        with unittest.mock.patch.object(settings, "_seed_document", lambda: {"version": 2, "levels": {}}):
            self.assertEqual([], list(seed_against_version_two()))


if __name__ == "__main__":
    unittest.main()
