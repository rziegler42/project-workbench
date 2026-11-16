"""Which added paths are the review engine's own records, so that a list shown to the owner may summarise them.

``acknowledge`` shows every difference between a project and what the owner last accepted. A clone of a project that
tracks its reviews holds hundreds of files that the manifest does not record, each review adding more, and a list that long
cannot be read. These files have one spelling, the engine's own, so a path that has exactly that spelling, and is a regular
file that was added, may be shown as a count instead of as a line. Everything else is still a line.

The rule is a function of a ``Difference`` and nothing else. It reads no file, follows nothing and opens nothing, and it
decides only what is *shown*: the digest and the baselines still cover every path. It does not say that a record is
genuine. The engine does that, with a seal made by a key that stays on one machine, and it uses no record it did not seal
there; so a forged file of this spelling is shown as a count and is of no use to the engine.

The spelling is copied from ``packages/workbench/review-engine/helper/review-engine`` (``KINDS``, ``FILE_NAME``,
``NAMESPACE`` and the form of ``review_key``), because installer code cannot import package code. A test reads that
source and fails when it differs.
"""

import re

from .acknowledgement import ADDED

KINDS = ("plan", "spec", "roadmap", "adr")
FOLDER = ".workbench/workbench/review-engine"
KEY_DIGITS = 16
NAME_PATTERN = r"state\.json|ledger\.md|schema\.json|round-[1-9][0-9]{0,3}\.json"

_FOLDER_PARTS = tuple(FOLDER.split("/"))
_DIRECTORY = re.compile(r"(%s)-[0-9a-f]{%d}" % ("|".join(KINDS), KEY_DIGITS))
_NAME = re.compile(NAME_PATTERN)
_SHA256 = re.compile(r"[0-9a-f]{64}")


def record_of(difference):
    """``(kind, directory name)`` when `difference` is an added review-engine record of exactly the engine's spelling,
    otherwise None.

    It is one only if the difference is an addition with no baseline, was hashed as a regular file (it has a digest and
    no reason, so it is not a link, a directory or a name that cannot be accepted), and its path is
    ``.workbench/workbench/review-engine/<kind>-<16 hex digits>/<name>`` with a kind and a name the engine uses, in that
    spelling and no other."""
    if difference.kind != ADDED or difference.baseline is not None or difference.reason:
        return None
    if not isinstance(difference.current, str) or _SHA256.fullmatch(difference.current) is None:
        return None
    path = difference.path
    if not isinstance(path, str):
        return None
    parts = path.split("/")
    if len(parts) != len(_FOLDER_PARTS) + 2 or tuple(parts[:len(_FOLDER_PARTS)]) != _FOLDER_PARTS:
        return None
    directory, name = parts[-2], parts[-1]
    found = _DIRECTORY.fullmatch(directory)
    if found is None or _NAME.fullmatch(name) is None:
        return None
    return found.group(1), directory
