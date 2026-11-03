"""The harnesses this workbench knows, with the facts ``wb check`` needs about each.

A harness is known when it is a module of type ``harness`` in a package that ``firstparty.is_first_party``
accepts in the workbench's distribution, whose layout verifies. The distribution is the trust root for the
layout, as it is for the shipped approvals. The facts are derived from that layout (``layout.facts``) and
from nothing else: no harness name or path is written here.

A name that two first-party packages both declare is refused as a name, not resolved by picking one. A
package that is not first-party, or does not load, or a layout that does not verify, contributes nothing.

``refusal_text`` is the line a gate prints when its harness is not known. It says why: which package tree differs from its
release and where, or that a link or a stray file is in the way, or that no release approval exists, and which commands the
owner runs in a terminal to clear it (``docs/decisions/2026-11-02-gates-while-a-package-tree-differs-from-its-release.md``,
decision 2). It reads the tree and prints paths, never a value, and never raises.
"""

import collections
import os
import stat
import time

from . import approvals, declarations, firstparty, layout, verify
from .wbkit import display, safefs

Known = collections.namedtuple("Known", "found refused")


def load(distribution=None):
    """``Known``: ``found`` maps each harness name to its ``layout.facts``; ``refused`` is the names that
    more than one first-party package declares."""
    distribution = distribution or firstparty.default_distribution()
    packages = os.path.join(distribution, firstparty.PACKAGES)
    try:
        names = sorted(os.listdir(packages)) if os.path.isdir(packages) else []
    except OSError:
        return Known({}, ())
    seen, refused = {}, set()
    for name in names:
        path = os.path.join(packages, name)
        if not firstparty.is_first_party(path, distribution):
            continue
        loaded = declarations.load_package(path, first_party=True)
        # The layout is read after the package was hashed, so it is hashed again: a package that changed
        # in between contributes nothing.
        if loaded.problems or not firstparty.is_first_party(path, distribution):
            continue
        for module in loaded.modules:
            if module.type != "harness" or layout.problems(module.layout):
                continue
            if module.name in seen:
                refused.add(module.name)
            seen.setdefault(module.name, layout.facts(module.layout))
    found = {name: facts for name, facts in seen.items() if name not in refused}
    return Known(found, tuple(sorted(refused)))


def known(distribution=None):
    """The facts of each known harness, by name."""
    return load(distribution).found


# --- the line a gate prints when the harness is not known ------------------------------------------------------------

CLEAR = ("the owner clears it in a terminal with `wb preview release-approvals` and then `wb release-approvals --digest "
         "<digest>`, with the digest the preview prints")
FIX_FIRST = "the release refuses a tree like this, so remove or restore it first, and then "
_SHOWN = 120  # characters of a quoted path in the line, so that the line stays under the 600 the gate prints
_MAX_ENTRIES = 20000  # entries `_first_trouble` looks at; a tree larger than this is still hashed, which finds a link or a bad name
_BUDGET = 3.0  # seconds after which the search for the cause stops, so that the gate's own 10 seconds are not spent on a message
# What the verifier says after the path of a file that no module accounts for (modulefiles._accounted); a message that does not
# end with it is not taken apart.
_UNACCOUNTED = " is not module.json, under harness/, templates/, files/, tests/ or tools/, or named by fills or ships"


def _shown(rel):
    """`rel` as a quoted ASCII string, so that a file name is shown as data and cannot read as part of the sentence."""
    shown = repr(display.ascii_text(rel))
    return shown if len(shown) <= _SHOWN else shown[:_SHOWN - 4] + "..." + shown[0]  # closed with the quote it opened with


def _first_trouble(path):
    """``(rel, what)`` for the first entry below `path`, in the order of a walk that sorts each directory's names and checks a
    directory's entries before it descends into one, that the tree hash refuses: a link, a special file or a
    name the workbench's path check refuses; ``None`` when there is none or after ``_MAX_ENTRIES`` entries. Nothing is followed or
    read."""
    stack = collections.deque([("", path)])
    seen = 0
    while stack:
        prefix, here = stack.popleft()
        try:
            names = sorted(os.listdir(here))
        except OSError:
            return prefix.rstrip("/") or ".", "unreadable"
        later = []
        for name in names:
            seen += 1
            if seen > _MAX_ENTRIES:
                return None
            rel = prefix + name
            try:
                safefs.validate_relpath(rel)
                mode = os.lstat(os.path.join(here, name)).st_mode
            except safefs.SafeFsError:
                return rel, "name"
            except OSError:
                return rel, "unreadable"
            if stat.S_ISLNK(mode):
                return rel, "link"
            if stat.S_ISDIR(mode):
                later.append((rel + "/", os.path.join(here, name)))
            elif not stat.S_ISREG(mode):
                return rel, "special"
        stack.extendleft(reversed(later))
    return None


def _package_file(path, modules):
    """The first file or directory of the package directory `path` that is not a module's and not ``package.json``, or
    ``package.json``: where a change outside every module is."""
    try:
        for name in sorted(os.listdir(path)):
            if name != "package.json" and name not in modules:
                return name
    except OSError:
        pass
    return "package.json"


def _differs(name, path, distribution, started):
    """The cause for the package `name` at `path`, which is not first-party: ``(sentence, fix_first)``. `fix_first` is true when
    the release would refuse the tree (a link, a special file, a refused name, a file no module accounts for, a package that
    cannot be read), so the owner removes or restores the file before releasing."""
    where = os.path.join(firstparty.PACKAGES, name)
    if os.path.islink(path.rstrip("/") or "/"):
        return "the package %s is a link, which the release refuses" % _shown(where), True
    trouble = _first_trouble(path)
    if trouble:
        rel, what = trouble
        kinds = {"link": "a link, which the release hash refuses", "special": "a file that is not a regular file",
                 "name": "a name the workbench refuses", "unreadable": "an entry that cannot be read"}
        return "the package tree holds %s at %s" % (kinds[what], _shown(os.path.join(where, rel))), True
    if time.monotonic() - started > _BUDGET:
        return ("the package tree differs from its release; the cause was not searched, as it took too long (%s)"
                % _shown(where)), False
    try:
        declaration, tree = firstparty._package_hashes(path, name)
    except (safefs.SafeFsError, declarations.DeclarationError, firstparty.ReleaseError, ValueError, OSError):
        return "the package %s cannot be read as a package (package.json, or a file over the size limit)" % _shown(where), True
    shipped = os.path.join(distribution, firstparty.SHIPPED, firstparty.PACKAGES)
    try:
        recorded = os.path.isdir(shipped) and bool(os.listdir(shipped))
    except OSError:
        recorded = False
    if not recorded:
        return "there is no release approval for the package tree (%s)" % _shown(where), False
    if time.monotonic() - started > _BUDGET:
        return ("the package tree differs from its release; the cause was not searched, as it took too long (%s)"
                % _shown(where)), False
    result = verify.verify_package(path, first_party=True, harness_required=False)
    if not result.accepted:
        for problem in sorted(result.problems, key=str):
            message = str(getattr(problem, "message", ""))
            if getattr(problem, "rule", "") == "unaccounted-file" and message.endswith(_UNACCOUNTED):
                rel = message[:-len(_UNACCOUNTED)]
                return ("the package tree differs from its release: %s is a file no module accounts for"
                        % _shown(os.path.join(where, str(problem.subject), rel))), True
        problem = sorted(result.problems, key=str)[0]
        scope = str(getattr(problem, "scope", "package"))
        at = os.path.join(where, str(problem.subject)) if scope == "module" and hasattr(problem, "subject") else where
        return ("the package tree differs from its release: first at %s (the %s is refused: %s)"
                % (_shown(at), scope, str(getattr(problem, "rule", ""))[:24])), True
    shipped_tree = firstparty.shipped_tree(distribution)
    for module in sorted(result.modules, key=lambda item: item.name):
        if not approvals.check_module(shipped_tree, "%s/%s" % (name, module.name), module.declaration_hash,
                                      module.tree_hash).approved:
            return ("the package tree differs from its release: first at %s"
                    % _shown(os.path.join(where, module.name))), False
    return ("the package tree differs from its release: first at %s"
            % _shown(os.path.join(where, _package_file(path, {module.name for module in result.modules})))), False


def _cause(distribution, started):
    """The sentence that says why no harness is known in `distribution`, or ``None`` when every package is first-party (the
    harness is then simply not declared, or the layout does not verify), as ``(sentence, fix_first)``."""
    packages = os.path.join(distribution, firstparty.PACKAGES)
    if not os.path.isdir(packages):
        return None
    names = sorted(os.listdir(packages))
    # A stray file beside the packages (``.DS_Store``) is not a package, and the release refuses a tree that holds one.
    stray = any(not os.path.isdir(os.path.join(packages, name)) and not os.path.islink(os.path.join(packages, name))
                for name in names)
    for name in names:
        path = os.path.join(packages, name)
        if not os.path.isdir(path) and not os.path.islink(path):
            continue
        if not firstparty.is_first_party(path, distribution):
            sentence, fix_first = _differs(name, path, distribution, started)
            if stray:
                return sentence + "; packages/ also holds an entry that is not a package", True
            return sentence, fix_first
    return None


def refusal_text(harness, distribution=None, needs="whose layout describes the gate", declared=False):
    """The one line a gate prints when `harness` is not known, or does not declare what the gate needs (`needs`). While a package
    tree differs from its release the line names the cause and the first place that differs, and the commands the owner runs in a
    terminal; otherwise it is the plain line. `declared` is true when the caller found the harness known (it lacks only what
    `needs` names), which is the plain line too; the caller has already loaded the harnesses, so this does not load them again.
    Never raises; prints paths and never a value."""
    name = display.ascii_text(harness)[:64]
    plain = "%s is not a known harness %s" % (name, needs)
    try:
        if declared:
            return plain
        distribution = distribution or firstparty.default_distribution()
        cause = _cause(distribution, time.monotonic())
    except Exception:  # the line explains a refusal; a failure to explain it must not become another one
        return plain
    if cause is None:
        return plain
    sentence, fix_first = cause
    return "%s is not available: %s; %s" % (name, sentence, (FIX_FIRST + CLEAR) if fix_first else CLEAR)
