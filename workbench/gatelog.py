"""The refusal log of the command gate: what the gate refused, kept in the guarded store as the file ``gate-log``.

``docs/decisions/2026-11-02-command-gate-reads-gaps-and-data-positions.md``, decision 6. The gate appends one line for each
refusal, after the verdict is fixed::

    <time> <TAB> <rule> <TAB> <first 12 hexadecimal characters of the SHA-256 of the command>

It is tab-separated ASCII of at most ``MAX_LINE`` bytes and never holds the command's text. The writer follows ``levellog``: it
appends through ``safefs.append_line`` (no-follow, a regular file with one link), never reads the file, and stops appending at
``MAX_BYTES``. Every failure to write it, a full file, a link and a damaged store included, is swallowed: the log is a
diagnostic, not an audit record (the gate runs as the agent's process, so the agent can write or fill the file from a shell), and
it must not change a result or push the gate past its deadline. The owner reads it, and rotates it by hand when it is full;
``wb doctor`` (increment L of the plan) is to report a full log and print counts per rule.
"""

import hashlib
import re

from .wbkit import levels as kit, safefs

LOG = "gate-log"
MAX_BYTES = 1024 * 1024
MAX_LINE = 256
HASH_CHARS = 12
MAX_HASHED = 64 * 1024  # the gate reads no more of a command than this, so the hash costs no more
_RULE = re.compile(r"[a-z][a-z-]{0,39}\Z")


def fingerprint(command):
    """The first 12 hexadecimal characters of the SHA-256 of `command` (its first ``MAX_HASHED`` characters)."""
    return hashlib.sha256(command[:MAX_HASHED].encode("utf-8", "replace")).hexdigest()[:HASH_CHARS]


def line(time, rule, command):
    """The log line as bytes. ``ValueError`` for a time or rule the log would not read back."""
    if not isinstance(time, str) or not re.fullmatch(kit.TIME_PATTERN, time):
        raise ValueError("a gate log time is YYYY-MM-DDTHH:MM:SSZ")
    if not isinstance(rule, str) or not _RULE.match(rule):
        raise ValueError("a gate log rule is a short lowercase name")
    return ("%s\t%s\t%s\n" % (time, rule, fingerprint(command))).encode("ascii")


def record(root_path, rule, command):
    """Append the line for a refusal by `rule` of `command` below the existing directory `root_path`. Never raises."""
    try:
        safefs.append_line(root_path, LOG, line(kit.utc_now(), rule, command), MAX_BYTES, MAX_LINE)
    except Exception:  # a log that cannot be written changes nothing: the refusal stands
        pass


def writer(root_path):
    """The ``log(rule, command)`` function the gate takes (``command_gate.run``), appending below `root_path`."""
    def log(rule, command):
        record(root_path, rule, command)
    return log
