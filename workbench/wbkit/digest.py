"""The kit's preview digest: what an ``ask`` is bound to, computed and checked once.

A command that offers the level ``ask`` has a read-only preview that prints the lines of what the command would change and, last,
``digest: <digest>``. The run takes ``--digest <digest>`` and goes on only if the digest is that of the lines as they are now
(``docs/specs/command-permissions.md``, "The levels"). Two helpers carried a copy of this; this module is the one place it is written.

The kit takes the preview *lines*, never a path, and reads nothing: a caller builds the lines inside the critical section that makes
the change, from the state it is about to change, so the digest compared is the one of that state (a helper that holds a lock takes
the lines under it; one that replaces a file takes them from its held root and the sha-checked replace, which also binds the sha the
digest binds). What the lines bind (the project, the path, a hash of the content) is the caller's; this module only makes the digest
of them and compares it. It imports only the standard library.
"""

import hashlib
import hmac
import re

CHARS = 32
# The one line a refusal prints when a digest is not that of what the command would change now. A caller may add to it (for
# example that nothing was changed); it does not reword it.
MISMATCH = "the digest does not match what the command would change now; preview it again with `preview`"
# The one line a usage error prints when a digest is not 32 lowercase hexadecimal characters.
SHAPE = "the digest is %d lowercase hexadecimal characters, as `preview` prints it" % CHARS

_HEX = "[0-9a-f]{%d}" % CHARS  # matched whole, with re.fullmatch: the kit builds no compiled pattern (``test_kit``)


def of(lines):
    """The digest of `lines`: the first 32 characters of the SHA-256 of the lines joined by a newline, in lowercase hex."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:CHARS]


def well_formed(text):
    """Whether `text` is exactly 32 lowercase hexadecimal characters (a string that a digest may be)."""
    return isinstance(text, str) and re.fullmatch(_HEX, text) is not None


def mismatch(given, lines):
    """``None`` when `given` is the digest of `lines`, else ``MISMATCH``. Never raises: a value that is not text, or text that
    cannot be encoded, does not match. The comparison takes the same time whatever the first difference."""
    if not isinstance(given, str) or not given.isascii():  # ``hmac.compare_digest`` takes text only when it is ASCII
        return MISMATCH
    if hmac.compare_digest(given, of(lines)):
        return None
    return MISMATCH
