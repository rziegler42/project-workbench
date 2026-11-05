"""The default ``review-profiles.json`` that ``wb install`` writes when the guarded store has none (plan `2026-11-04-review-profiles`,
increment J; ``docs/specs/review-profiles.md``, "The default `wb install` writes").

The installer names no module (``docs/specs/module-boundary.md``), so the default is built from what the selected modules declare and
from nothing else: a module that provides ``model-bridge`` and has exactly one command that takes ``ask`` is a bridge, named by that
command. Each bridge gets one profile that names it and nothing more (no model, no effort and no option), so that the bridge's own
default stands; the ``default`` ladder is written only when exactly one profile was made. A ladder for any other key belongs to the
engine that reads it and to the owner, and is not written here. The file is the owner's: it is written only when absent, and what is
written is shown in the preview and bound to the digest by being one of the plan's store writes.
"""

import collections
import json
import re

from .wbkit import display, jsonstrict, profiles, safefs

CAPABILITY = "model-bridge"
ASK = "ask"
FILE = profiles.FILE
OLD = ".workbench/review.json"
MAX_OLD = 4096
MAX_SHOWN = 128
LADDER = "default"

# `data` is the bytes to write, or None when nothing is written; `notes` are the lines the preview prints under "review profiles:".
Default = collections.namedtuple("Default", "data notes")


def _shown(text, limit=64):
    return display.ascii_text(str(text))[:limit]


def _bridges(modules):
    """``(names, notes)``: the command that names each bridge among `modules`, sorted, and a line for each module that is a bridge but
    cannot be named. A name is a command that is also a valid profile name."""
    names, notes = {}, []
    for item in modules:
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
        names[name] = item.name
    return sorted(names), notes


def build(modules):
    """The ``Default`` for the selected `modules`, as if the owner's file were absent."""
    names, notes = _bridges(modules)
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
    lines += ["profile %s: bridge %s, with no model, effort or option named, so the bridge's own default stands"
              % (_shown(name), _shown(name)) for name in names]
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


def read_old(path):
    """The bytes of ``.workbench/review.json`` under the directory `path`, or None when there is none or the directory cannot be read.
    A file over the bound gives more bytes than the bound, which ``old_setting_lines`` reports as over it."""
    try:
        with safefs.Root(path, "target") as root:
            return root.read_if_present(OLD, MAX_OLD)
    except safefs.SafeFsError as exc:
        return b"\0" * (MAX_OLD + 1) if "larger than" in str(exc) or "too large" in str(exc) else None
    except OSError:
        return None


def old_setting_lines(data):
    """What an old ``.workbench/review.json`` said, as data for the owner to carry into a profile: only the four known fields, each
    as ASCII with escapes and cut at 128 characters, and one line saying so when the file is over 4,096 bytes or is not strict JSON.
    Nothing here is written anywhere, and the default is never made from it."""
    if data is None:
        return ()
    head = "old %s (read by nothing now)" % OLD
    try:
        if len(data) > MAX_OLD:
            raise ValueError("over the bound")
        body = jsonstrict.parse_object(data, MAX_OLD)
    except ValueError:
        return ("%s was not read: it is over %d bytes or not strict JSON" % (head, MAX_OLD),)
    shown = []
    if type(body.get("format")) is int:
        shown.append("format=%d" % body["format"])
    for field in ("bridge", "model", "effort"):
        value = body.get(field)
        if isinstance(value, str):
            shown.append("%s=%r" % (field, display.ascii_text(value)[:MAX_SHOWN]))
    return ("%s, carry what you want into a profile: %s" % (head, " ".join(shown) if shown else "none of its four known fields is plain text"),)
