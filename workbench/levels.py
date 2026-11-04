"""The keys the owner's ``levels`` table may name, and every fact about each: the registry.

``docs/specs/command-permissions.md`` ("Which levels a key offers", "Shipped defaults"), decision
``2026-11-02-one-permission-registry-and-key-model``. The installer's own facts are written once, here, in
``INSTALLER_KEYS`` (its owner-run commands and the checkpoints it names) and in the lists below it (its agent-safe actions,
the words that only dispatch, the preview actions and the launcher spellings). ``rules`` re-exports the lists, and the old
tables ``_OFFERS`` and ``_DEFAULTS`` are derived from ``INSTALLER_KEYS``. A module's declaration stays the authoritative
input for the facts that are the module's own: ``registry`` takes the checkpoints a process module declares and, for each
installed command, ``command_entry(command)``, and gives every key its ``Key``. No module is named here
(``2026-10-21-module-code-lives-in-modules``). A hard stop of the compiled floor is never a key.

A ``Key`` holds: its ``kind`` (``command``, ``argument``, ``checkpoint`` or ``agent-safe``), its danger ``klass`` (``reads``,
``project`` or ``governs``), the levels it offers and its default, the ``spellings`` it can be written in, the ``preview`` whose
digest an ``ask`` is bound to, the command that carries it out (``carried_by``; empty for a checkpoint the agent follows as a
rule), whether a module declared an ``asks`` for it (a minimum prompt that is not a level), and the ``anchor`` document that
describes it. The class is information: it changes no default and no level a key offers. A module argument's class is
derived, not declared: an owner-run argument, or one that carries an ``asks``, is in the class that governs; any other reads.
The decision's list puts three owner-run arguments of one module in the class of ``project``; that needs a class a module can
declare, which the module contract does not have, so they read as ``governs`` until it does (a divergence from the decision that
the owner has been told of; ``tests/test_levels_facts.py`` pins it).

The levels a key offers: ``_OFFERS`` (derived from ``INSTALLER_KEYS``, and patched by a test) gives the levels beyond ``block`` of
a key the installer names. ``approve-plan`` offers ``delegated`` (``wb delegate-approve-plan`` is its gate), ``ask`` (a digest of
its preview) and ``none``; ``wb release-approvals`` offers ``ask`` (a digest of the preview of its release,
``2026-10-30-release-approvals-at-ask``) and ``none``; ``wb install``, ``wb adopt``, ``wb upgrade``, ``wb add``,
``wb attach``, ``wb recover``, ``wb approve``, ``wb pin`` and the first acknowledge tier offer ``ask`` (a digest of their preview) and
``none``;
the other owner-run installer commands, ``accept-decision`` and the second acknowledge tier offer ``none``; ``wb rerender`` offers ``block`` only (``2026-10-27-rerender-is-terminal-only``). No other key
offers ``ask`` unless an installed command's declaration gives its owner-run argument ``levels``
(``declarations.ARGUMENT_LEVELS``) and ``checkpoint_of`` maps that argument to a checkpoint (then the checkpoint offers the
levels the argument does; ``checkpoint_commands``). An agent-safe key and a declared argument that is not owner-run offer
``none`` and default to it; every other default is ``block``. ``_DEFAULTS`` is empty and exists so that a test can patch a
default: the shipped default of ``approve-plan`` becomes ``ask`` only after the probe the decision
``2026-10-26-ask-level-spelling-limit`` requires is recorded.
"""

import collections

from . import floor

BLOCK, ASK, DELEGATED, NONE = "block", "ask", "delegated", "none"
LEVELS = (BLOCK, ASK, DELEGATED, NONE)  # strictest first
APPROVE_PLAN = "approve-plan"

# What a key is.
COMMAND, ARGUMENT, CHECKPOINT, AGENT_SAFE_KIND = "command", "argument", "checkpoint", "agent-safe"
# How dangerous it is, as information (decision ``2026-11-02-one-permission-registry-and-key-model``, decision 4): it reads, it
# changes the project or what it installed, or it changes what governs the agent, leaves the project, deletes or publishes.
READS, PROJECT, GOVERNS = "reads", "project", "governs"

_DEVELOPMENT = "docs/development.md"
_PERMISSIONS = "docs/specs/command-permissions.md"

Key = collections.namedtuple(
    "Key", "name offers default agent kind klass carried_by spellings preview asks anchor stated_by",
    defaults=(False, "", "", "", (), "", False, "", ()))

Spec = collections.namedtuple("Spec", "kind klass offers word carried_by preview anchor")

# The keys the installer names, in the order of the registry: its owner-run commands and the checkpoints it knows offers for.
# `word` is the command word an owner-run command is run by (empty for a checkpoint the agent follows as a rule); `offers`
# the levels beyond ``block`` that the key offers in this version; `preview` the key of the read-only action whose digest an
# ``ask`` is bound to. A checkpoint named here that a command carries out is named by `carried_by`.
INSTALLER_KEYS = collections.OrderedDict([
    ("wb install", Spec(COMMAND, PROJECT, (ASK, NONE), "install", "wb install", "wb preview install", _DEVELOPMENT)),
    ("wb adopt", Spec(COMMAND, PROJECT, (ASK, NONE), "adopt", "wb adopt", "wb preview adopt", _DEVELOPMENT)),
    ("wb upgrade", Spec(COMMAND, PROJECT, (ASK, NONE), "upgrade", "wb upgrade", "wb preview upgrade", _DEVELOPMENT)),
    ("wb add", Spec(COMMAND, PROJECT, (ASK, NONE), "add", "wb add", "wb preview add", _DEVELOPMENT)),
    ("wb attach", Spec(COMMAND, PROJECT, (ASK, NONE), "attach", "wb attach", "wb preview attach", _DEVELOPMENT)),
    ("wb rerender", Spec(COMMAND, GOVERNS, (), "rerender", "wb rerender", "wb preview rerender", _DEVELOPMENT)),
    ("acknowledge-first-tier", Spec(CHECKPOINT, GOVERNS, (ASK, NONE), "acknowledge", "wb acknowledge", "wb preview acknowledge",
                                    _PERMISSIONS)),
    ("acknowledge-second-tier", Spec(CHECKPOINT, GOVERNS, (NONE,), "", "", "", _PERMISSIONS)),
    ("wb recover", Spec(COMMAND, PROJECT, (ASK, NONE), "recover", "wb recover", "wb preview recover", _DEVELOPMENT)),
    ("wb approve", Spec(COMMAND, GOVERNS, (ASK, NONE), "approve", "wb approve", "wb preview approve", _DEVELOPMENT)),
    ("wb pin", Spec(COMMAND, GOVERNS, (ASK, NONE), "pin", "wb pin", "wb preview pin", _DEVELOPMENT)),
    ("wb release-approvals", Spec(COMMAND, GOVERNS, (ASK, NONE), "release-approvals", "wb release-approvals",
                                  "wb preview release-approvals", _DEVELOPMENT)),
    (APPROVE_PLAN, Spec(CHECKPOINT, GOVERNS, (DELEGATED, ASK, NONE), APPROVE_PLAN, APPROVE_PLAN, "wb plan-status", _PERMISSIONS)),
    ("accept-decision", Spec(CHECKPOINT, GOVERNS, (NONE,), "", "", "", _PERMISSIONS)),
])


# A checkpoint and the command that does the same act keep a level each, on purpose (decision 5 of
# ``2026-11-02-one-permission-registry-and-key-model``). The registry does not record the pairing: it would name a module, and the
# installer names none (``2026-11-03-conformance-tests-name-modules-and-module-pins-follow-the-levels``, decision 2). The spec records
# it and the drift test checks that; whether to merge the pairs is for ``2026-11-02-permission-levels-for-every-command``.

# The skills that state a checkpoint the agent follows as a rule (no command carries it), for increment K to check.
STATED_BY = {"push-shared-branch": ("push-changes",), "submit-remote-job": ("run-remote-job",),
             "fetch-remote-output": ("run-remote-job",), "change-direction": ("draft-roadmap", "draft-spec")}


def _once(words):
    found = []
    for word in words:
        if word and word not in found:
            found.append(word)
    return tuple(found)


# The owner-run commands only the owner runs, from a terminal (``rules`` renders a deny for each), derived from the table.
OWNER_RUN = _once(spec.word for spec in INSTALLER_KEYS.values())
# Commands an agent may run: they only read, or run a helper that checks its own pin.
AGENT_SAFE = ("verify", "preview", "launch", "check", "run", "plan-status", "settings", "doctor", "gate",
              "agent-gate", "gate-command", "delegate-approve-plan")
# Of the agent-safe words, those that are not a key of the owner's ``levels`` table
# (``docs/specs/command-permissions.md``, "A level for every command"): the hook entry points, which the
# harness runs and the owner does not; the words that only dispatch to an action; and the action that reaches another
# action's key, so that no action reaches two keys.
HOOK_ENTRY_POINTS = ("gate", "agent-gate", "gate-command")
DISPATCHERS = ("preview", "run")
REACHES_ANOTHER_KEY = {"delegate-approve-plan": "approve-plan"}
# The actions ``wb preview`` dispatches to; each has a key. Derived from the table.
PREVIEW_ACTIONS = tuple(spec.preview.split(" ")[-1] for spec in INSTALLER_KEYS.values()
                        if spec.preview.startswith("wb preview ") and spec.word in OWNER_RUN)
# `python3 -B -m workbench` is how this repository's own checks are run; the flags a rule can name
# are limited to this one. Other interpreter spellings, a path-qualified `wb`, `env` and `bash -c`
# are not matched (a Bash deny is not a security boundary).
SPELLINGS = ("wb", "python3 -m workbench", "python3 -B -m workbench", "python -m workbench",
             "python -B -m workbench")

# The levels beyond ``block`` that a key offers in this version, by key (derived from the table; a test patches it).
_OFFERS = {name: spec.offers for name, spec in INSTALLER_KEYS.items() if spec.offers}
# The shipped default of a key that is not ``block``; none yet among the owner-run keys.
_DEFAULTS = {}
# An agent-safe action, and a declared module argument that is not owner-run, is one an agent may run today, so it
# defaults to ``none`` (``docs/specs/command-permissions.md``, "A level for every command"). Until the
# increment that renders a ``deny`` for it, a ``block`` here is read and reported but is not enforced.
_AGENT_OFFERS = (NONE,)

# Owner-run commands whose levels the declared checkpoints set, so the command spelling is not a key of its own: a
# checkpointed action uses its checkpoint's name (the first and second tier of ``acknowledge``). Derived from the table.
CHECKPOINTED_COMMANDS = _once(spec.word for name, spec in INSTALLER_KEYS.items()
                              if spec.kind == CHECKPOINT and spec.word and spec.word != name)
# The checkpoint whose level governs a command that is not a key of its own. ``wb acknowledge`` lists only paths that have a
# baseline (the manifest, the files under ``.workbench/``, ``AGENTS.md``, seeded files), which are first-tier material, so the
# first-tier checkpoint is its key (the owner's choice, ``docs/specs/command-permissions.md``, "One way to run at ``none``").
CHECKPOINT_ACKNOWLEDGE = "acknowledge-first-tier"
COMMAND_OF_CHECKPOINT = {name: spec.word for name, spec in INSTALLER_KEYS.items()
                         if spec.kind == CHECKPOINT and spec.word and spec.word != name}


class RegistryError(ValueError):
    """Two declarations give one key, so a level could not say which of them it sets."""


def strictest(*given):
    """The strictest of the given levels (``block`` strictest, ``none`` least strict)."""
    return min(given, key=LEVELS.index)


def command_words(key):
    """The words of the command the key `key` names, after the launcher: ``("approve-plan",)``, ``("install",)``,
    ``("preview", "install")``, ``("run", "<command>", "<argument>"...)``, or ``()`` for a key that names no command (a
    checkpoint the agent follows, or a name of another shape). It reads the shape of the name only: whether a word is a command
    the installer has is for the caller to ask (``OWNER_RUN``, ``AGENT_SAFE``, ``PREVIEW_ACTIONS``). The rendering and the command
    gate both read a key's name through this one function."""
    if key in COMMAND_OF_CHECKPOINT:
        return (COMMAND_OF_CHECKPOINT[key],)
    if key == APPROVE_PLAN:
        return (APPROVE_PLAN,)
    parts = key.split(" ")
    if parts[0] != "wb":
        return ()
    if parts[1:2] == ["run"] and len(parts) >= 4:
        return tuple(["run"] + parts[2:])
    if parts[1:2] == ["preview"] and len(parts) == 3:
        return ("preview", parts[2])
    if len(parts) == 2:
        return (parts[1],)
    return ()


def command_entry(command):
    """The facts of a declared command that the registry reads, as ``registry`` takes them: ``(name, owner-run arguments,
    all declared arguments, ``levels`` as ``((argument, (level, ...)), ...)``, ``checkpoint_of`` as
    ``((argument, checkpoint), ...)``, the arguments that carry an ``asks``, the name of the preview argument)``. One place
    builds it, so a caller cannot leave a fact out."""
    return (command.name, command.owner, command.arguments, command.levels, command.checkpoint_of,
            tuple(command.asks or ()), command.preview or "")


def _arguments(commands):
    """``{key: (class, asks, preview key)}`` for each argument that `commands` declare, a key ``wb run <command> <argument>``."""
    found = {}
    for entry in commands:
        command, owner = entry[0], entry[1]
        arguments = entry[2] if len(entry) > 2 else ()
        leveled = {argument: tuple(wanted) for argument, wanted in (entry[3] if len(entry) > 3 else ())}
        asks = tuple(entry[5]) if len(entry) > 5 else ()
        preview = entry[6] if len(entry) > 6 else ""
        for argument in tuple(owner) + tuple(a for a in arguments if a not in owner):
            key = "wb run %s %s" % (command, argument)
            asked = argument in asks
            klass = GOVERNS if argument in owner or asked else READS
            shown = "wb run %s %s" % (command, preview) if preview and argument in owner and ASK in leveled.get(argument, ()) else ""
            found[key] = (klass, asked, shown)
    return found


def _build(name, kind, agent, declared, arguments, carried):
    """The ``Key`` of `name`: `declared` the levels its declaration gives (``registry``); `arguments` the facts of the declared
    arguments (``_arguments``); `carried` the key of the command that carries a checkpoint out, by checkpoint."""
    spec = INSTALLER_KEYS.get(name)
    if agent:
        offers, default = (BLOCK,) + _AGENT_OFFERS, NONE
    else:
        fixed = _OFFERS.get(name, ())
        extra = tuple(level for level in (ASK, NONE) if level in declared and level not in fixed)
        offers = (BLOCK,) + (tuple(sorted(fixed + extra, key=LEVELS.index)) if extra and fixed else fixed + extra)
        default = _DEFAULTS.get(name, BLOCK)
    klass, asked, preview, anchor, carried_by = "", False, "", "", ""
    if spec is not None:
        klass, preview, anchor, carried_by = spec.klass, spec.preview, spec.anchor, spec.carried_by
    if name in arguments:
        klass, asked, preview = arguments[name]
        carried_by = name
    elif name in carried:
        carried_by = carried[name]
        preview = arguments[carried_by][2]
    if kind == CHECKPOINT:
        klass, anchor = klass or GOVERNS, anchor or _PERMISSIONS
    elif kind == AGENT_SAFE_KIND:
        klass, anchor, carried_by = READS, _DEVELOPMENT, name
    spellings = SPELLINGS if carried_by else ()
    stated = STATED_BY.get(name, ()) if kind == CHECKPOINT and not carried_by else ()
    return Key(name, offers, default, agent, kind, klass, carried_by, spellings, preview, asked, anchor, stated)


def checkpoint_commands(checkpoints, commands):
    """``{checkpoint: "wb run <command> <argument>"}`` for each ``checkpoint_of`` mapping of `commands` that applies: the
    checkpoint is one of the process module's declared `checkpoints`, and the argument is owner-run and offers a level.
    A mapping to a checkpoint nobody declares does not apply, and its argument keeps its own key. ``RegistryError`` when two
    arguments claim one declared checkpoint. `commands` are the entries ``registry`` takes; the mapping is their fifth item,
    ``((argument, checkpoint), ...)`` (``2026-10-29-accept-decision-at-ask``)."""
    declared = set(checkpoints)
    found = {}
    for entry in commands:
        owner = entry[1]
        leveled = {argument for argument, wanted in (entry[3] if len(entry) > 3 else ()) if wanted}
        for argument, checkpoint in (entry[4] if len(entry) > 4 else ()):
            if checkpoint in declared and argument in owner and argument in leveled:
                key = "wb run %s %s" % (entry[0], argument)
                if checkpoint in found and found[checkpoint] != key:
                    raise RegistryError("more than one declaration gives the key %s" % checkpoint)
                found[checkpoint] = key
    return found


def agent_keys():
    """The keys of the agent-safe actions, in the ``wb`` spelling, in the order of ``AGENT_SAFE``.

    A hook entry point, a word that only dispatches (``preview`` and ``run``; each action beneath ``preview`` has a key,
    and a module's arguments have theirs) and an action that reaches another action's key
    (``delegate-approve-plan``) are not keys, so no action reaches two keys and a parent cannot tighten or bypass an
    action beneath it."""
    names = []
    for command in AGENT_SAFE:
        if command in HOOK_ENTRY_POINTS or command in REACHES_ANOTHER_KEY:
            continue
        if command == "preview":
            names.extend("wb preview " + action for action in PREVIEW_ACTIONS)
        elif command not in DISPATCHERS:
            names.append("wb " + command)
    return tuple(names)


def registry(checkpoints=(), commands=(), agent=True):
    """The keys, in order, as ``{name: Key}``.

    First the process module's declared `checkpoints`, in declaration order; then one key for each owner-run
    command of ``OWNER_RUN`` in the ``wb`` spelling (``approve-plan`` is the checkpoint of that name); then,
    with `agent` true, one for each agent-safe action (``agent_keys``); then ``wb run <command> <argument>`` for each
    declared argument of `commands`, a sequence of ``(command name, owner-run arguments)``,
    ``(command name, owner-run arguments, all declared arguments)`` or that with a fourth item, the command's ``levels``
    as ``((argument, (level, ...)), ...)``, a fifth, its ``checkpoint_of`` as ``((argument, checkpoint), ...)`` (an
    argument so mapped to one of `checkpoints` has that checkpoint as its key and no key of its own, see
    ``checkpoint_commands``), a sixth, the arguments that carry an ``asks``, and a seventh, the name of its preview argument
    (``command_entry`` builds all seven from a declaration): an owner-run argument defaults to ``block`` and any
    other declared argument to ``none`` (with `agent` false the keys of the arguments that are not owner-run are left out
    with those of the agent-safe actions). Two declarations of one key are refused (``RegistryError``). A repeated
    checkpoint is one key, and a floor action is not a key.
    """
    names = []
    names.extend((name, CHECKPOINT, False) for name in checkpoints)
    for command in OWNER_RUN:
        if command in CHECKPOINTED_COMMANDS:
            continue
        name = APPROVE_PLAN if command == APPROVE_PLAN else "wb " + command
        names.append((name, INSTALLER_KEYS[name].kind, False))
    if agent:
        names.extend((name, AGENT_SAFE_KIND, True) for name in agent_keys())
    declared, declared_offers = [], {}
    carried = checkpoint_commands(checkpoints, commands)
    own = {key: checkpoint for checkpoint, key in carried.items()}
    for entry in commands:
        command, owner = entry[0], entry[1]
        arguments = entry[2] if len(entry) > 2 else ()
        declared.extend(("wb run %s %s" % (command, argument), ARGUMENT, False) for argument in owner
                        if "wb run %s %s" % (command, argument) not in own)
        for argument, wanted in (entry[3] if len(entry) > 3 else ()):
            if argument in owner:
                key = "wb run %s %s" % (command, argument)
                declared_offers[own.get(key, key)] = tuple(wanted)
        if agent:
            declared.extend(("wb run %s %s" % (command, argument), ARGUMENT, True) for argument in arguments
                            if argument not in owner)
    counted = [name for name, _, _ in declared]
    repeated = sorted({name for name in counted if counted.count(name) > 1})
    if repeated:
        raise RegistryError("more than one declaration gives the key %s" % repeated[0])
    names.extend(declared)
    ids = {stop.id for stop in floor.FLOOR}
    facts = _arguments(commands)
    keys = collections.OrderedDict()
    for name, kind, agent_safe in names:
        if name not in keys and name not in ids:
            keys[name] = _build(name, kind, agent_safe, declared_offers.get(name, ()), facts, carried)
    return keys
