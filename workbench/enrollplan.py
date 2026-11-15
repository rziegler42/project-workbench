"""What ``wb enroll`` would write for a clone of an installed project on a machine that does not know it, read and never written.

``docs/specs/clone-enrollment.md`` and the decision ``2026-11-15-enroll-baselines-only-what-the-manifest-records`` are the design. A clone of a project
that is already installed has the committed manifest and the files it records, but the guarded store of a new machine holds no baselines and no
first-seen record for it, so every command that acts on a known project refuses it. ``examine`` reads the clone and the store and either refuses, with
the path or the entry that failed, or returns a ``Plan``: the baselines and the first-seen record to write, what the owner is told about, and the digest of
that. It writes nothing, reads no approval record and makes no pin: the helpers are pinned by ``upgrade`` with a package, which verifies the package.

What it checks, in this order:

* the target is an existing project (the target module has already refused the places it refuses);
* the store holds neither the baselines nor the first-seen record of the project (one of the two, or a malformed entry, is a refusal);
* the manifest reads through the strict reader (``installed.read``), and every entry is a regular file where one is expected;
* every module-owned file equals the manifest's hash; a seeded file or a slot block that differs, or a seeded file that is missing, is listed and does not refuse;
* each module's own ``module.json`` as copied into the clone parses and hashes to the declaration hash the manifest records (the command takes no package, so this
  is a consistency check on the manifest and not a trust anchor);
* every recorded path lies where its owner may write, and a block's module declares the slot it fills;
* a link or another non-regular file under ``.workbench/`` outside ``local/`` is a refusal; a regular file there that the manifest does not record is counted,
  not refused and not baselined.

The baselines hold every recorded file that is there, at the bytes in the clone (a file with slot blocks as a whole), and the manifest itself, as ``install``
records them.
"""

import collections

from . import acknowledgement, base, blocks, declarations, hashing, installed, installplan, manifest, projectfs
from .wbkit import display, safefs

MANIFEST = installed.MANIFEST
WORKBENCH = ".workbench"
STALE_ENTRIES = ("pins", "rendering", "plan-approvals")    # the other entries the installer makes in a project's folder of the store (a test lists them)
MAX_SHOWN = 400        # baselines printed one by one; the digest covers all of them
LIST_LIMIT = 10        # a group of unrecorded files that holds this many or fewer is listed path by path
MAX_REFUSED = 20       # paths named in one refusal

Differing = collections.namedtuple("Differing", "path recorded current")
Outside = collections.namedtuple("Outside", "path owner_class")
Block = collections.namedtuple("Block", "path block slot state")


class Refused(Exception):
    """The enrollment stops with these lines, each printed as ``refused: ...``; nothing was written."""

    def __init__(self, lines):
        Exception.__init__(self, "; ".join(lines))
        self.lines = list(lines)


class Plan:
    """The result of ``examine``. ``baselines`` maps a path to its SHA-256; ``unrecorded`` maps a group of unrecorded files to their paths."""

    def __init__(self, existing, project, path, identity, baselines, seeded_differ, seeded_missing, blocks_differ, unrecorded, outside=()):
        self.existing = existing
        self.project = project
        self.path = path
        self.identity = identity
        self.baselines = baselines
        self.seeded_differ = seeded_differ
        self.seeded_missing = seeded_missing
        self.blocks_differ = blocks_differ
        self.unrecorded = unrecorded
        self.outside = list(outside)
        self.unrecorded_total = sum(len(paths) for paths in unrecorded.values())
        self.fields = {
            "command": "enroll",
            "target": {"device": identity[0], "inode": identity[1]},
            "project": project,
            "path": path,
            "workbench": existing.document["workbench"],
            "manifest": existing.manifest_hash,
            "baselines": dict(sorted(baselines.items())),
            "seeded_differ": [[d.path, d.recorded, d.current] for d in seeded_differ],
            "seeded_missing": [item.path for item in seeded_missing],
            "blocks_differ": [[b.path, b.block, b.slot, b.state] for b in blocks_differ],
            "outside": [[item.path, item.owner_class] for item in self.outside],
            "unrecorded": {group: (paths if len(paths) <= LIST_LIMIT else len(paths)) for group, paths in sorted(unrecorded.items())},
        }
        self.digest = installplan.digest_of(self.fields)

    @property
    def baselines_bytes(self):
        return installplan.json_store({"baselines": self.baselines, "format": acknowledgement.FORMAT})

    @property
    def seen_bytes(self):
        return installplan.json_store({"format": acknowledgement.FORMAT, "kind": "path", "value": self.path})


def _shown(text, limit=120):
    return display.ascii_text(str(text))[:limit]


def _under_workbench(path):
    folded = path.casefold()
    return folded == WORKBENCH or folded.startswith(WORKBENCH + "/")


def group_of(path):
    """The group an unrecorded file is counted under: the module namespace ``.workbench/<package>/<module>`` for a path deeper than that, else its directory."""
    parts = path.split("/")
    return "/".join(parts[:3]) if len(parts) > 3 else path.rsplit("/", 1)[0]


def _check_unknown(guarded, project):
    try:
        baselines = acknowledgement.read_baselines(guarded, project)
        seen = acknowledgement.read_seen(guarded, project)
    except acknowledgement.AcknowledgementError as exc:
        raise Refused(["an entry of this project in the store is malformed: %s; nothing was written" % _shown(exc, 200)])
    if baselines is not None and seen is not None:
        raise Refused(["the project is already known on this machine; use acknowledge to accept changes to it"])
    if baselines is not None:
        raise Refused(["this machine holds the baselines of the project but no first-seen record; nothing was written"])
    if seen is not None:
        raise Refused(["this machine holds a first-seen record of the project but no baselines; nothing was written"])
    # Entries of an earlier project of the same identity: a pin binds a path and the hash of a helper, and the owner's earlier confirmation of it is not a
    # confirmation of this clone, so the folder is removed by hand first (the spec's non-goal: no use of an earlier project's pins).
    for name in STALE_ENTRIES:
        if guarded.kind("projects/%s/%s" % (project, name)) is not None:
            raise Refused(["this machine holds a %s entry of this project in the store, left from an earlier project of the same identity, "
                           "and `enroll` does not keep or replace it: remove the folder projects/%s/ from the guarded store by hand and run "
                           "this again; nothing was written" % (name, project)])


def _states(existing):
    """Refuse what cannot be enrolled; return ``(seeded entries that differ, missing seeded entries, blocks that differ)``."""
    stuck, differ, missing, blocks = [], [], [], []
    missing_files = {e.path for e in existing.entries if e.block is None and e.state == installed.MISSING}
    for entry in existing.entries:
        if entry.state == installed.UNREADABLE:
            stuck.append("%s (%s)" % (_shown(entry.path), _shown(entry.detail, 100)))
        elif entry.owner_class == "module-owned" and entry.state != installed.AS_INSTALLED:
            stuck.append("%s (a module-owned file that is %s the manifest records)"
                         % (_shown(entry.path), "missing; " if entry.state == installed.MISSING else "not what"))
        elif entry.owner_class == "seeded":
            if entry.state == installed.EDITED:
                differ.append(entry)
            elif entry.state == installed.MISSING:
                missing.append(entry)
        elif entry.owner_class == "slot block":
            if entry.path in missing_files:
                continue    # the file is missing and is listed as a missing seeded file
            if entry.state in (installed.EDITED, installed.GONE):
                blocks.append(entry)
    if stuck:
        lines = ["the clone cannot be enrolled as it is:"]
        lines += ["  " + line for line in stuck[:MAX_REFUSED]]
        if len(stuck) > MAX_REFUSED:
            lines.append("  and %d more" % (len(stuck) - MAX_REFUSED))
        raise Refused(lines)
    return differ, missing, blocks


def _modules(writer, existing):
    """``{(package, module): declarations.Module}`` from each module's own ``module.json`` in the clone, checked against the manifest's hash."""
    recorded = {e.path: e for e in existing.entries if e.block is None}
    found = {}
    for package in existing.document["packages"]:
        for item in package["modules"]:
            rel = ".workbench/%s/%s/module.json" % (package["name"], item["name"])
            entry = recorded.get(rel)
            if entry is None or entry.owner_class != "module-owned":
                raise Refused(["the manifest does not record the declaration file %s as a module-owned file" % _shown(rel)])
            try:
                state = writer.read_file(rel)
            except safefs.SafeFsError as exc:
                raise Refused(["%s cannot be read: %s" % (_shown(rel), _shown(exc))])
            if state is None:
                raise Refused(["%s is missing" % _shown(rel)])
            try:
                module = declarations.parse_module(state.data, package["name"], item["name"], first_party=True)
                declared = hashing.declaration_hash(module.declaration)
            except (declarations.DeclarationError, hashing.HashError) as exc:
                raise Refused(["%s is not a valid declaration: %s" % (_shown(rel), _shown(exc, 200))])
            if declared != item["declaration"]:
                raise Refused(["the declaration in %s is not the one the manifest records for %s/%s"
                               % (_shown(rel), _shown(package["name"]), _shown(item["name"]))])
            found[(package["name"], item["name"])] = module
    return found


def covered(path, prefixes):
    """Whether `path` is one of the `prefixes` or lies below one, matched by its parents (a set lookup per level, not a scan of every prefix)."""
    parts = path.split("/")
    return any("/".join(parts[:count]) in prefixes for count in range(1, len(parts) + 1))


def _places(existing, modules):
    """Refuse a recorded entry that lies where its owner may not write, or a block whose module does not declare its slot. Returns the entries
    outside ``.workbench/`` that the base does not supply, which rest only on a module's own declaration of what it writes."""
    namespaces = {".workbench/%s/%s" % key for key in modules}
    writes = {w for module in modules.values() for w in module.writes}
    fills = {"%s/%s" % key: {slot for slot, _ in module.fills} for key, module in modules.items()}
    try:
        supplied = set(base.load_base().files)
    except base.BaseError as exc:
        raise Refused(["the base of this workbench cannot be read: %s" % _shown(exc, 200)])
    seeded = {e.path for e in existing.entries if e.block is None and e.owner_class == "seeded"}
    bad, declared = [], []
    for entry in existing.entries:
        path = entry.path
        outside = not _under_workbench(path)
        if entry.owner_class == "slot block" and path not in seeded:
            bad.append("%s (slot block %s: a slot block must lie in a file the manifest records as seeded)"
                       % (_shown(path), _shown(entry.block, 80)))
            continue
        if entry.owner_class == "module-owned":
            ok = path == WORKBENCH + "/.gitignore" or covered(path, namespaces) or covered(path, writes)
        elif entry.owner_class == "seeded":
            ok = outside and (path in supplied or covered(path, writes))
        else:
            ok = (outside and (path in supplied or covered(path, writes))
                  and ("slot:" + entry.slot) in fills.get(entry.block, ()))
        if not ok:
            bad.append("%s (%s%s)" % (_shown(path), entry.owner_class,
                                      " block %s slot %s" % (_shown(entry.block, 80), _shown(entry.slot, 40)) if entry.block else ""))
        elif outside and entry.block is None and (entry.owner_class == "module-owned" or path not in supplied):
            # A seeded file at a path the base supplies is the owner's; a module-owned file outside `.workbench/` is never the base's, and rests on a
            # module's own declaration whatever its path is.
            declared.append(Outside(path, entry.owner_class))
    if bad:
        lines = ["the manifest names places its owner may not write, or a slot its module does not declare:"]
        lines += ["  " + line for line in bad[:MAX_REFUSED]]
        if len(bad) > MAX_REFUSED:
            lines.append("  and %d more" % (len(bad) - MAX_REFUSED))
        raise Refused(lines)
    return declared


def _same_as_judged(entries, state):
    """Whether the entries of one path, judged again on `state` (the second read of the file, or None when it is not there), come out as they did
    on the first read of ``installed.read``: the same state and the same hash for each."""
    if state is None:
        return all(entry.state == installed.MISSING for entry in entries)
    recorded = {(entry.block, entry.slot) for entry in entries if entry.block}
    scan, problem = None, ""
    if recorded:
        try:
            scan = blocks.scan(state.data)
        except blocks.BlockError as exc:
            problem = "the slot markers cannot be read: %s" % _shown(exc, 100)
    for entry in entries:
        item = {"class": entry.owner_class, "hash": entry.hash, "slot": entry.slot}
        now = installed._entry(entry.path, item, entry.block, state, "", scan, problem, recorded)
        if (now.state, now.current) != (entry.state, entry.current):
            return False
    return True


def _unrecorded(writer, existing):
    """``{group: [paths]}`` of the regular files under ``.workbench/`` outside ``local/`` that the manifest does not record; a link or another kind
    of file there is a refusal."""
    listing = {}
    acknowledgement._walk(writer, WORKBENCH, 0, listing)
    recorded = {e.path for e in existing.entries} | {MANIFEST}
    stuck, groups = [], {}
    for path, kind in sorted(listing.items()):
        if kind == "dir" or path in recorded:
            continue
        if kind != "file":
            stuck.append("%s (%s)" % (_shown(path), "a link" if kind == "symlink" else "not a regular file"))
            continue
        groups.setdefault(group_of(path), []).append(path)
    if stuck:
        lines = ["these paths under .workbench/ are not regular files and cannot be enrolled:"]
        lines += ["  " + line for line in stuck[:MAX_REFUSED]]
        raise Refused(lines)
    return groups


def examine(guarded, held, version):
    """Read the clone behind `held` and the store `guarded` and return a ``Plan``; raises ``Refused``. Nothing is written."""
    if held.state != "existing":
        raise Refused(["the target is not an existing project; use install"])
    writer = projectfs.Writer(held)
    try:
        existing = installed.read(writer, version)
        project = manifest.project_id(existing.document["seed"])
        _check_unknown(guarded, project)
        differ, missing, blocks = _states(existing)
        modules = _modules(writer, existing)
        outside = _places(existing, modules)
        unrecorded = _unrecorded(writer, existing)
        baselines, spent = {}, 0
        by_path = {}
        for entry in existing.entries:
            by_path.setdefault(entry.path, []).append(entry)
        for path in sorted(by_path):
            state = writer.read_file(path)
            # The states above come from one read of each file and the baseline from a second: every entry of the path is judged again on the bytes
            # of the second read, so a file changed in between (a block of a seeded file, a module-owned file, a file removed or put back) is refused.
            if not _same_as_judged(by_path[path], state):
                raise Refused(["%s changed while it was read; nothing was written" % _shown(path)])
            if state is None:
                continue
            spent += len(state.data)
            if spent > acknowledgement.MAX_READ_BYTES:
                raise Refused(["the recorded files hold more than %d bytes; deal with the project by hand first"
                               % acknowledgement.MAX_READ_BYTES])
            baselines[path] = state.hash
    except (installed.InstalledError, manifest.ManifestError, acknowledgement.AcknowledgementError, safefs.SafeFsError) as exc:
        raise Refused([_shown(exc, 300)])
    baselines[MANIFEST] = existing.manifest_hash
    return Plan(
        existing, project, held.path, held.identity, baselines,
        [Differing(e.path, e.hash, baselines[e.path]) for e in differ],
        missing,
        [Block(b.path, b.block, b.slot, b.state) for b in blocks],
        unrecorded, outside)


def render(plan, target_path):
    """The text the owner reads, ending with the digest."""
    document = plan.existing.document
    lines = ["target: %s" % display.ascii_text(target_path),
             "command: enroll",
             "project: %s" % plan.project,
             "manifest: sha256 %s" % plan.existing.manifest_hash,
             "recorded by workbench %s; base tree %s" % (display.ascii_text(document["workbench"]), document["base"]),
             "packages:"]
    for package in document["packages"]:
        lines.append("  %s from %s ref %s commit %s tree %s" % (
            display.ascii_text(package["name"]), display.ascii_text(package["source"])[:200],
            display.ascii_text(package["ref"] or "(none)")[:80], package["commit"] or "(none)", package["tree"]))
        for module in package["modules"]:
            lines.append("    %s %s declaration %s tree %s" % (
                display.ascii_text(module["name"]), display.ascii_text(module["version"]), module["declaration"], module["tree"]))
    lines.append("baselines to record: %d paths" % len(plan.baselines))
    classes = {}
    for entry in plan.existing.entries:
        classes.setdefault(entry.path, entry.owner_class)
    shown = sorted(plan.baselines)
    for path in shown[:MAX_SHOWN]:
        lines.append("  %s %s sha256 %s" % (display.ascii_text(path), classes.get(path, "manifest"), plan.baselines[path]))
    if len(shown) > MAX_SHOWN:
        lines.append("  and %d more (the digest covers all of them)" % (len(shown) - MAX_SHOWN))
    if plan.outside:
        lines.append("recorded outside .workbench/ on the strength of a module's own declaration of what it writes (a file of the clone, not checked "
                     "against anything): %d" % len(plan.outside))
        # Every one of them is listed: this heading is the owner's only notice of files that the clone alone vouches for, and it is as long as the
        # manifest allows, no longer.
        for item in plan.outside:
            lines.append("  %s %s" % (display.ascii_text(item.path), item.owner_class))
    for item in plan.seeded_differ:
        lines.append("%s differs from the manifest (seeded, yours)" % display.ascii_text(item.path))
        lines.append("    recorded %s" % item.recorded)
        lines.append("    in the clone %s" % item.current)
    for item in plan.seeded_missing:
        lines.append("%s is missing (seeded); no baseline is made for it" % display.ascii_text(item.path))
    for item in plan.blocks_differ:
        lines.append("%s: block differs from the manifest (seeded file, yours): block %s slot %s, %s" % (
            display.ascii_text(item.path), display.ascii_text(item.block), display.ascii_text(item.slot),
            "its markers are gone" if item.state == installed.GONE else "its text was edited"))
    if plan.unrecorded:
        lines.append("files under .workbench/ that the manifest does not record: %d (not baselined here; acknowledge lists them next)"
                     % plan.unrecorded_total)
        groups = sorted(plan.unrecorded.items())
        for group, paths in groups[:MAX_SHOWN]:
            lines.append("  %s: %d file%s" % (display.ascii_text(group), len(paths), "" if len(paths) == 1 else "s"))
            if len(paths) <= LIST_LIMIT:
                lines += ["    " + display.ascii_text(path) for path in paths]
        if len(groups) > MAX_SHOWN:
            lines.append("  and %d more directories, with %d files (not baselined)"
                         % (len(groups) - MAX_SHOWN, sum(len(paths) for _, paths in groups[MAX_SHOWN:])))
    lines.append("first-seen path to record: %s" % display.ascii_text(plan.path))
    lines.append("enrolling writes the baselines and the first-seen record in the guarded store and nothing in the project; it pins no helper "
                 "(an upgrade with the package does)")
    lines.append("digest: %s" % plan.digest)
    return "\n".join(lines) + "\n"
