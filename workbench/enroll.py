"""``wb enroll`` and ``wb preview enroll``: make a clone of an installed project known on a machine that has never held it.

``docs/specs/clone-enrollment.md`` is the design and ``enrollplan.py`` the read. This module is the command line's side: ``run_preview`` prints what an
enrollment would write and the digest of it and writes nothing. The owner-run command that writes the baselines and the first-seen record is added to this
module by the next increment of the plan ``2026-11-15-enroll-a-clone``.
"""

from . import __version__, acknowledge, enrollplan, preview, sources, target
from .wbkit import display, safefs


def parse(tokens):
    """The target spelling from ``[<target> | --dir <path>]``; a ``sources.UsageError`` otherwise. No ``--digest`` and no other option: the command
    offers the level ``block`` only (``levels.py``)."""
    return acknowledge.parse(tokens)


def _refuse(err, text):
    err.write("refused: %s\n" % display.clean(text))
    return 1


NOT_BUILT = ("wb enroll is not built in this version: the key and the preview exist, and the command that writes comes with the next increment of "
             "the plan 2026-11-15-enroll-a-clone. `wb preview enroll` shows what it would write.")


def run_not_built(tokens, err):
    """``wb enroll`` until the increment that builds it: it refuses, writes nothing and says where the preview is. Tokens are read for usage only."""
    try:
        parse(tokens)
    except sources.UsageError as exc:
        err.write("%s\n" % display.clean(str(exc)))
        return 2
    return _refuse(err, NOT_BUILT)


def run_preview(guarded, spelling, out, err, version=None):
    """``wb preview enroll``: what an enrollment of the clone behind `spelling` would write, read-only, ending with the digest of the read and the line
    every preview ends with. Returns the exit code: 0, or 1 when the clone is refused."""
    try:
        with target.open_target(spelling, guarded.root) as held:
            plan = enrollplan.examine(guarded, held, version or __version__)
            text = enrollplan.render(plan, held.path)
    except enrollplan.Refused as exc:
        for index, line in enumerate(exc.lines):
            err.write(("refused: %s\n" if not line.startswith("  ") or not index else "%s\n") % display.clean(line))
        return 1
    except target.TargetError as exc:
        return target.write_refusal(err, exc)
    except safefs.SafeFsError as exc:
        return _refuse(err, str(exc))
    out.write(text)
    out.write(preview.ENDING + "\n")
    return 0
