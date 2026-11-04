"""The owner's review profiles: what the installer and a module's helper share to read ``review-profiles.json``.

It imports the standard library and the kit only, and knows no module and no document kind: the caller names the ladder keys it
accepts and the keys whose ladder holds one rung, so the kit never learns what any kind of review is. Adding it does not
raise ``wbkit.API``.

``docs/decisions/2026-11-04-review-profiles-in-the-guarded-store.md`` and ``docs/specs/review-profiles.md``. The file is the owner's, in
the guarded store at the fixed path under the home directory, read through the no-follow layer and bounded. It is read whole or
refused whole. Only the last part of the path is refused when it is a link, and ``HOME`` moves the whole store: the guard
is against a mistaken agent and not against a process that runs as the owner. A refusal names the file and the rule and never repeats the file's text or a path, because the text is the owner's
and a path is the account's.

What this does not do: it checks the file's own rules and nothing that needs a module's declaration (that an option is declared, its
grammar and its exclusions), so one bridge that is not installed never invalidates the file. Those checks run where a profile is
resolved for a round.
"""

import collections
import os
import re

from . import jsonstrict, safefs
from .call import NAME as BRIDGE_NAME

FILE = "review-profiles.json"
MAX_BYTES = 32768
MAX_PROFILES = 32
MAX_OPTIONS = 8
MAX_RUNGS = 5
EFFORTS = ("low", "medium", "high")
# Option names that belong to a fixed field of a profile or to the engine, and so can never be set from a profile.
RESERVED = frozenset(("model", "effort", "timeout", "schema", "root", "confine"))
DEFAULT = "default"

PROFILE_NAME = r"[a-z0-9][a-z0-9_-]{0,31}"
OPTION_NAME = r"[a-z][a-z0-9-]{0,31}"
# Printable ASCII with no space and no leading "-", 1 to 128 characters: text that can never read as an option.
TEXT = r"[!-,.-~][!-~]{0,127}"
# The closed list of grammars a module's declaration may give an option that a review passes. None allows a leading "-", and a
# module cannot supply an expression of its own (docs/specs/review-profiles.md, "The options a module declares for a review").
GRAMMARS = {
    "word": r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}",
    "name": PROFILE_NAME,
    "count": r"[1-9][0-9]{0,7}",
    "onoff": r"on|off",
}
_FIELDS = {"format", "profiles", "ladders"}
_PROFILE_FIELDS = {"bridge", "model", "effort", "options"}

Profile = collections.namedtuple("Profile", "bridge model effort options")
Profiles = collections.namedtuple("Profiles", "profiles ladders")


class ProfileError(Exception):
    """The file cannot be used. The message names the file and the rule, never the file's text or a path."""


def fail(why):
    return ProfileError("%s %s" % (FILE, why))


def reserved_or_prefix(name):
    """Whether `name` is a reserved option name or a non-empty prefix of one. A bridge that accepts abbreviated options would read
    ``--mod`` as ``--model``, so a prefix is as unusable as the name itself."""
    return type(name) is str and name != "" and any(reserved.startswith(name) for reserved in RESERVED)


def _text(value):
    return type(value) is str and re.fullmatch(TEXT, value) is not None


def fits(grammar, value):
    """Whether `value` is text of the grammar named `grammar`. A grammar outside ``GRAMMARS`` fits nothing."""
    return (type(grammar) is str and grammar in GRAMMARS and type(value) is str
            and re.fullmatch(GRAMMARS[grammar], value) is not None)


def _profile(record):
    if not isinstance(record, dict):
        raise fail("holds a profile that is not an object")
    if set(record) - _PROFILE_FIELDS:
        raise fail("holds a profile with a field that is not listed")
    bridge = record.get("bridge")
    if type(bridge) is not str or re.fullmatch(BRIDGE_NAME, bridge) is None:
        raise fail("holds a profile whose bridge is missing or is not one command name")
    model = record.get("model")
    if "model" in record and not _text(model):
        raise fail("holds a profile whose model is not printable ASCII of at most 128 characters with no space and no leading -")
    effort = record.get("effort")
    if "effort" in record and not (type(effort) is str and effort in EFFORTS):
        raise fail("holds a profile whose effort is not low, medium or high")
    options = record.get("options", {})
    if not isinstance(options, dict) or len(options) > MAX_OPTIONS:
        raise fail("holds a profile whose options are not an object of at most %d entries" % MAX_OPTIONS)
    for name, value in options.items():
        if re.fullmatch(OPTION_NAME, name) is None or reserved_or_prefix(name):
            raise fail("holds an option whose name is outside the name rule, is reserved or is a prefix of a reserved name")
        if not _text(value):
            raise fail("holds an option whose value is not printable ASCII of at most 128 characters with no space and no leading -")
    return Profile(bridge, model if "model" in record else None, effort if "effort" in record else None, dict(options))


def parse(data, ladder_keys, single_rung_keys):
    """The ``Profiles`` of the bytes `data`, or a ``ProfileError``.

    `ladder_keys` are the keys of ``ladders`` the caller accepts (``default`` among them if it uses it); `single_rung_keys` are the
    keys whose ladder must hold exactly one profile, passed as an empty tuple when none does (there is no default, so a caller
    cannot forget the rule). A key outside `ladder_keys` is refused.
    """
    try:
        body = jsonstrict.parse_object(data, MAX_BYTES)
    except ValueError as exc:
        raise fail("is too large" if "larger than" in str(exc) else "is not strict JSON") from None
    if set(body) - _FIELDS:
        raise fail("has a field that is not listed")
    if _FIELDS - set(body):
        raise fail("is missing a required field")
    if type(body["format"]) is not int or body["format"] != 1:
        raise fail("must have format 1")
    records = body["profiles"]
    if not isinstance(records, dict) or not 1 <= len(records) <= MAX_PROFILES:
        raise fail("must hold 1 to %d profiles" % MAX_PROFILES)
    found = {}
    for name, record in records.items():
        if re.fullmatch(PROFILE_NAME, name) is None:
            raise fail("holds a profile name outside the name rule")
        found[name] = _profile(record)
    ladders = body["ladders"]
    if not isinstance(ladders, dict):
        raise fail("must hold ladders as an object")
    kept = {}
    for key, rungs in ladders.items():
        if key not in ladder_keys:
            raise fail("holds a ladder that is not listed")
        if not isinstance(rungs, list) or not 1 <= len(rungs) <= MAX_RUNGS:
            raise fail("holds a ladder of fewer than 1 or more than %d profiles" % MAX_RUNGS)
        if key in single_rung_keys and len(rungs) != 1:
            raise fail("holds a ladder that must have exactly one profile")
        for name in rungs:
            if type(name) is not str:
                raise fail("holds a ladder with a name that is not a string")
            if name not in found:
                raise fail("holds a ladder that names a profile the file lacks")
        kept[key] = tuple(rungs)
    return Profiles(found, kept)


def _problem(exc):
    """Which cause made the reader fail, in fixed words. The kit's own text holds a path, so it is classified and not copied."""
    text = str(exc).lower()
    if "too large" in text:
        return "is too large"
    if "(symlink)" in text or "symbolic link" in text:
        return "is linked"
    if "not a regular file" in text:
        return "is not a regular file"
    if isinstance(exc, FileNotFoundError) or "no such file" in text or "does not exist" in text:
        return "is missing; `wb install` writes it, or write it by hand (docs/specs/review-profiles.md)"
    return "cannot be read"


def read(ladder_keys, single_rung_keys):
    """The owner's file, read by its fixed path under the home directory and parsed. Nothing moves the path: no variable of the
    workbench, no option and no file."""
    home = os.path.expanduser("~")
    if not os.path.isabs(home):
        raise fail("cannot be found: the home directory is unknown")
    folder = os.path.join(home, ".config", "project-workbench")
    try:
        with safefs.Root(folder, "the guarded store") as root:
            data = root.read_file(FILE, MAX_BYTES)
    except (safefs.SafeFsError, OSError) as exc:
        raise fail(_problem(exc)) from None
    return parse(data, ladder_keys, single_rung_keys)


def for_round(found, kind, number, default_allowed):
    """``(name, Profile)`` for the `number`-th round of a review of `kind`: rung `number` of the kind's ladder, the last rung for
    every later round. A kind with no ladder uses ``default`` only when `default_allowed`."""
    if type(kind) is not str or kind == DEFAULT:
        raise fail("is asked for a kind of review that has no ladder of its own")
    if type(number) is not int or number < 1:
        raise fail("is asked for a round that is not a whole number from 1")
    ladder = found.ladders.get(kind)
    if ladder is None and default_allowed:
        ladder = found.ladders.get(DEFAULT)
    if ladder is None:
        raise fail("has no ladder for this kind of review")
    name = ladder[min(number, len(ladder)) - 1]
    return name, found.profiles[name]
