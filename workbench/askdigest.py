"""The digest of an ``ask``: the command and the digest of what its preview shows, taken by the kit's helper.

``docs/decisions/2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest.md`` (and its note of 2026-11-04). It lives here
and not in ``preview.py`` so that ``pins.py`` and ``approve.py`` can use it: ``preview`` imports ``installplan``, which imports ``pins``.
``preview`` keeps the names it had.
"""

from .wbkit import digest as kitdigest

ENDING = "preview only: nothing was written"
EXAMINATION_NOTE = ("the digest above is the examination's own, which a terminal run types; a run at the level ask "
                    "takes the one below")


def ask_lines(verb, inner_digest):
    """The lines an ``ask`` digest is taken over: the command and the digest of what its preview shows."""
    return ["wb " + verb, inner_digest]


def ask_digest(verb, inner_digest):
    return kitdigest.of(ask_lines(verb, inner_digest))


def ask_mismatch(verb, inner_digest, given):
    """``None`` when `given` is the ``ask`` digest of what the preview shows, else the kit's refusal text."""
    return kitdigest.mismatch(given, ask_lines(verb, inner_digest))
