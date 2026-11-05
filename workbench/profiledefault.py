"""The default ``review-profiles.json`` that ``wb install`` writes when the guarded store has none (plan `2026-11-04-review-profiles`,
increment J; ``docs/specs/review-profiles.md``, "The default `wb install` writes").

The installer names no module (``docs/specs/module-boundary.md``), so the default is built from what the selected modules declare and
from nothing else: a module that provides ``model-bridge`` and has exactly one command that takes ``ask`` is a bridge, named by that
command. Each bridge gets one profile that names it and nothing more (no model, no effort and no option), so that the bridge's own
default stands; the ``default`` ladder is written only when exactly one profile was made. A ladder for any other key belongs to the
engine that reads it and to the owner, and is not written here. The file is the owner's: it is written only when absent, and what is
written is shown in the preview and bound to the digest by being one of the plan's store writes. (A target that has a ``.workbench``
directory is refused by ``wb install`` and ``wb adopt``, so an old ``.workbench/review.json`` is never in the way and is not read here.)
"""

import collections
import json
import re

from .wbkit import display, profiles

CAPABILITY = "model-bridge"
ASK = "ask"
FILE = profiles.FILE
LADDER = "default"

# `data` is the bytes to write, or None when nothing is written; `notes` are the lines the preview prints under "review profiles:".
Default = collections.namedtuple("Default", "data notes")


def _shown(text, limit=64):
    return display.ascii_text(str(text))[:limit]


def _bridges(modules):
    """``(names, notes)``: the command that names each bridge among `modules`, sorted, and a line for each module that is a bridge but
    cannot be named. A name is a command that is also a valid profile name."""
    names, notes = {}, []
    for item in sorted(modules, key=lambda item: str(item.name)):
        module = item.module
        if CAPABILITY not in module.provides:
            continue
        asking = [command for command in module.commands if ASK in command.arguments]
        if len(asking) != 1:
            notes.append("no profile for %s: it provides %s and needs exactly one command that takes %s"
                         % (_shown(item.name), CAPABILITY, ASK))
            continue
        name = asking[0].name
        if not isinstance(name, str) or re.fullmatch(profiles.PROFILE_NAME, name) is None:
            notes.append("no profile for %s: its command %s is not a profile name" % (_shown(item.name), _shown(name)))
            continue
        if name in names:
            notes.append("the bridge command %s is provided by %s and by %s: one profile is made"
                         % (_shown(name), _shown(names[name]), _shown(item.name)))
            continue
        names[name] = item.name
    return names, notes


def build(modules):
    """The ``Default`` for the selected `modules`, as if the owner's file were absent."""
    modules_of, notes = _bridges(modules)
    names = sorted(modules_of)
    if not names:
        return Default(None, tuple(notes) + ("no model bridge is installed, so no %s is written" % FILE,))
    if len(names) > profiles.MAX_PROFILES:
        return Default(None, tuple(notes) + ("more than %d model bridges are installed, so no %s is written"
                                              % (profiles.MAX_PROFILES, FILE),))
    document = {"format": 1, "profiles": {name: {"bridge": name} for name in names},
                "ladders": {LADDER: [names[0]]} if len(names) == 1 else {}}
    data = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("ascii")
    try:
        profiles.parse(data, tuple(document["ladders"]), ())
    except profiles.ProfileError as exc:  # not reachable for these inputs; the file is never written unchecked
        return Default(None, tuple(notes) + ("the default %s was not written: %s" % (FILE, _shown(exc, 200)),))
    lines = ["%s is absent: this install writes it" % FILE]
    lines += ["profile %s: the bridge command %s of the module %s, with no model, effort or option named, so the bridge's own default "
              "stands" % (_shown(name), _shown(name), _shown(modules_of[name])) for name in names]
    if len(names) == 1:
        lines.append("ladder %s: %s; add the ladder of any other review, or stronger profiles, by hand" % (LADDER, _shown(names[0])))
    else:
        lines.append("no ladder is written, and a review is refused until you choose one in %s" % FILE)
    lines.append("the file, exactly as it will be written:")
    lines.extend("| " + line for line in data.decode("ascii").splitlines())
    return Default(data, tuple(notes) + tuple(lines))


def plan(modules, present):
    """The ``Default`` of an install: nothing is planned when the guarded store already holds something at the path (`present`),
    whatever it is, and the file is left as it is."""
    if present:
        return Default(None, ("%s exists in the guarded store and is left as it is" % FILE,))
    return build(modules)
