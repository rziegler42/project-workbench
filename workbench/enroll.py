"""``wb enroll`` and ``wb preview enroll``: make a clone of an installed project known on a machine that has never held it.

``docs/specs/clone-enrollment.md`` is the design and ``enrollplan.py`` the read. This module is the command line's side. ``run_preview`` prints what an
enrollment would write and the digest of it and writes nothing. ``run`` is the owner-run command, like ``acknowledge``:

* standard input and output must be terminals, before anything is read (the key offers ``block`` only, so there is no level that runs it without one, and so
  no level log to write, as for ``rerender``);
* the clone is read as ``preview enroll`` reads it, and the owner types the first characters of the digest of that read; typed-ahead input is discarded,
  and anything else writes nothing;
* after the answer the clone is read again, and a different digest is refused;
* then the baselines and the first-seen record are written in the guarded store, both staged before either is put in place, and the entries are read back.

It writes no pin and reads no approval record: the helpers are pinned by ``upgrade`` with the package, which verifies it. Nothing in the project is written.
"""

from . import __version__, acknowledge, acknowledgement, approve, confirm, enrollplan, preview, sources, target
from .wbkit import display, safefs

TERMINAL_ONLY = ("enroll is owner-run: standard input and output must both be terminals. Run this command yourself, from your own terminal; "
                 "`preview enroll` shows what it would write without writing.")
NEXT = ("Next, from the project directory: `wb acknowledge` lists the files under .workbench/ that the manifest does not record; "
        "`wb upgrade --package <directory>` (for this repository `packages/workbench`) then verifies the package and pins the helpers; "
        "`wb attach` renders the harness.")


def parse(tokens):
    """The target spelling from ``[<target> | --dir <path>]``; a ``sources.UsageError`` otherwise. No ``--digest`` and no other option: the command
    offers the level ``block`` only (``levels.py``)."""
    return acknowledge.parse(tokens)


def _refuse(err, text):
    err.write("refused: %s\n" % display.clean(text))
    return 1


def _report(exc, err):
    for index, line in enumerate(exc.lines):
        err.write(("refused: %s\n" if not line.startswith("  ") or not index else "%s\n") % display.clean(line))
    return 1


def run_preview(guarded, spelling, out, err, version=None):
    """``wb preview enroll``: what an enrollment of the clone behind `spelling` would write, read-only, ending with the digest of the read and the line
    every preview ends with. Returns the exit code: 0, or 1 when the clone is refused."""
    try:
        with target.open_target(spelling, guarded.root) as held:
            plan = enrollplan.examine(guarded, held, version or __version__)
            text = enrollplan.render(plan, held.path)
    except enrollplan.Refused as exc:
        return _report(exc, err)
    except target.TargetError as exc:
        return target.write_refusal(err, exc)
    except safefs.SafeFsError as exc:
        return _refuse(err, str(exc))
    out.write(text)
    out.write(preview.ENDING + "\n")
    return 0


def _present(guarded, project):
    """The names of the entries of `project` that the store holds now."""
    return [name for name in ("baselines", "seen") if guarded.kind("projects/%s/%s" % (project, name)) is not None]


def _remains(left, project):
    """What the owner is told about the entries of `project` after a failed write: `left` is the names the store holds, or None when it could not be read."""
    where = "projects/%s/ in the guarded store" % project
    if left is None:
        return ("the store could not be read to say which entries it holds; run `wb preview enroll`, which says whether the project is known, "
                "and remove any entry of %s by hand before running `enroll` again" % where)
    if not left:
        return "nothing was written"
    if len(left) == 2:
        return ("the store holds both entries, but they did not read back as written: remove both from %s by hand, then run `enroll` again"
                % where)
    return ("the store holds the %s entry of this project only, and `enroll` refuses a project that has only some of its entries: remove it from "
            "%s by hand, then run `enroll` again" % (left[0], where))


def _write(guarded, plan, held_path, out, err):
    """Write the two entries in one call that stages both before either is put in place, and read them back. Returns the exit code."""
    entries = {"projects/%s/baselines" % plan.project: plan.baselines_bytes, "projects/%s/seen" % plan.project: plan.seen_bytes}
    try:
        safefs.write_tree(guarded.root, entries)
        baselines = acknowledgement.read_baselines(guarded, plan.project)
        seen = acknowledgement.read_seen(guarded, plan.project)
        acknowledgement.check_known(baselines, seen, held_path)
        if baselines != plan.baselines:
            raise safefs.SafeFsError("the baselines read back are not the ones written")
    except (Exception, KeyboardInterrupt) as exc:
        cause = "interrupted" if isinstance(exc, KeyboardInterrupt) else str(exc)
        try:
            left = _present(guarded, plan.project)
        except (Exception, KeyboardInterrupt):
            left = None
        err.write("failed: %s\n%s\n" % (display.ascii_text(cause), _remains(left, plan.project)))
        return 3
    out.write("enrolled %d paths; the project was not touched; no helper is pinned\n%s\n" % (len(plan.baselines), NEXT))
    return 0


def _run(guarded, spelling, stdin, out, err, version):
    try:
        with target.open_target(spelling, guarded.root) as held:
            plan = enrollplan.examine(guarded, held, version)
            out.write(enrollplan.render(plan, held.path))
            out.write("\nTo enroll this clone, type the first %d characters of the digest shown above and press Enter.\n"
                      "Anything else cancels and writes nothing.\n> " % confirm.CONFIRM_CHARS)
            out.flush()
            if not confirm.typed_matches(stdin, plan.digest):
                out.write("cancelled: nothing was written\n")
                return 1
            held.recheck()
            again = enrollplan.examine(guarded, held, version)
            if again.digest != plan.digest:
                return _refuse(err, "the clone changed while the list was shown; nothing was written")
            return _write(guarded, plan, held.path, out, err)
    except enrollplan.Refused as exc:
        return _report(exc, err)
    except target.TargetError as exc:
        return target.write_refusal(err, exc)
    except safefs.SafeFsError as exc:
        return _refuse(err, str(exc))


def require_terminal(stdin, out, err):
    """True when both streams are terminals; otherwise print the refusal and return False."""
    if approve.is_terminal(stdin) and approve.is_terminal(out):
        return True
    _refuse(err, TERMINAL_ONLY)
    return False


def run(guarded, spelling, stdin, out, err, version=None):
    """Enroll the clone after the owner types the digest. Returns the exit code: 0 done, 1 refused or cancelled, 3 failed while writing, 130
    interrupted."""
    if not require_terminal(stdin, out, err):
        return 1
    try:
        return _run(guarded, spelling, stdin, out, err, version or __version__)
    except KeyboardInterrupt:
        try:
            out.write("\ncancelled: nothing was written\n")
        except OSError:
            pass
        return 130
    except BrokenPipeError:
        return 1
