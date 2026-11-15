# `wb enroll` writes the baselines and the first-seen record only, and the helper pins come from `upgrade` with a package

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-15
Supersedes 2026-11-15-enroll-makes-a-clone-known-on-the-manifest-hashes-and-the-owners-digest
Date: 2026-11-15

## Context

The record `2026-11-15-enroll-makes-a-clone-known-on-the-manifest-hashes-and-the-owners-digest` decided that `wb enroll` writes the baselines, the first-seen record and the helper pins of a clone, and pins a module's helpers only if the module's declaration and tree are already approved on the machine. It was accepted the same day.

While reading the installer for the first increment that builds it, the approval check was found not to bind what it was meant to bind. An approval record is looked up by the declaration hash and the tree hash of a module, and `enroll` can read both only from the clone's own committed manifest (`approvals.check_module`; `manifest` records them per module). The tree hash is the hash of the module's source directory in its package (`hashing.tree_hash_of`), and the copy in `.workbench/<package>/<module>/` holds only the files the module ships, so nothing in the clone ties the helper bytes there to the approved tree. Someone who can edit a clone can change a helper and the hash the manifest records for it, keep the real module's declaration and tree hashes (they are public in the repository), and pass both the manifest check and the approval check. The owner's digest would list the helper's hash, which does not show what the helper does. The invariant the earlier record states, that no helper of an unapproved module can run on the strength of the clone alone, did not hold.

`upgrade` with a package does bind the bytes. It verifies the package against the approvals, compares what is installed with what the package would write, and pins a helper that is left as it is and has no pin, but only if its acknowledged bytes equal the manifest's hash (`upgradeplan._pins`). That is what `enroll` leaves in the baselines for a module-owned file.

## Decision

- `wb enroll`, with `wb preview enroll`, writes in the guarded store, and nowhere else, the baselines and the first-seen record of a clone. It writes no pin and reads no approval record.
- Everything else of the earlier record stands as written, and is restated here so that this record can be read alone: the command runs through the `wb` launcher; it is owner-run and terminal-only at every level, its key offering `block` only; it shows the whole list and a digest and takes the first 12 characters typed back; it reads the committed manifest through the strict reader and checks every entry against the project's path and ownership rules; every file the manifest calls module-owned must equal the manifest's hash; an unrecorded file under `.workbench/` outside `local/` refuses; a seeded file or a slot block that differs is listed for the owner and baselined at the bytes in the clone; it requires the project to be wholly unknown on the machine and refuses one with one entry or a malformed entry; the basis of trust is the manifest's hashes and the owner's typed digest, with no comparison against another machine.
- The helpers of an enrolled clone are pinned by the next step, `wb upgrade --package <directory>` (for this repository, `packages/workbench`, which the clone holds), which verifies the package against the approvals on the machine, compares the installed files with the package, and creates the pins at the bytes it confirms. Until then no helper of the clone can run through the launcher.

## Alternatives considered

- **Keep the approval check in `enroll` (the earlier decision).** Rejected: it does not bind the helper bytes, as the context shows, and an enrollment that appears to check approvals but does not is worse than one that does not claim to.
- **Bind the bytes inside `enroll`, with a `--package` argument like `upgrade`'s.** Rejected for now: it repeats the package verification and comparison that `upgrade` already does and tests, in a second command that writes trust state, for the saving of one owner step. It can be reconsidered if the extra step proves a burden.
- **Pin from the manifest's hashes alone.** Rejected: that is the planted-helper case.
- **Enroll nothing until a package is given.** Rejected: baselines and the first-seen record are what every other command needs first, and writing them carries no authority to run a helper.

## Consequences

- A second machine needs one more owner step than the earlier record said: the first run of the workbench, `wb enroll`, `wb upgrade --package <directory>` (preview, then the digest), then `attach`. Until the `upgrade`, `wb check` still reports each helper as not pinned.
- The helper trust has one place: the package verification of `upgrade`. A third-party module is handled there, with its own approval step, and `enroll` needs no approval logic.
- A seeded file the owner has edited is baselined at the owner's bytes, so `upgrade` finds no difference there and leaves it alone ("a newer version exists; the project's file is not touched"), as it does for `AGENTS.md` in this repository; the preview of `enroll` lists each such file.
- The earlier record is superseded as a whole, and its status line names this record once this one is accepted; its text is not touched. Its clarification note of the same day, about refusing the whole enrollment for an unapproved module, no longer applies.
- The spec `docs/specs/clone-enrollment.md` and the plan `2026-11-15-enroll-a-clone` change to match, and the plan needs the owner's new approval.

## Evidence

- Read 2026-11-15 at commit `4b92f4e`, Python 3.15.0 on Darwin: `approvals.check_module` and `firstparty.check_module` (the lookup is by declaration hash and tree hash); `hashing.declaration_hash` (the hash of the parsed declaration) and `hashing.tree_hash_of` (the hash of a module source directory); `installed.read` (it compares each manifest entry with the file or block on disk, which is the check the earlier record relied on for the module-owned files); `upgradeplan._pins` and `pinplan.changes` (a helper left as it is and without a pin is pinned when its acknowledged bytes equal the manifest's hash). Not run: an `upgrade` on an enrolled clone, which the plan's acceptance criteria require once `enroll` exists.
- The flaw was found by the author while reading the code for the first build increment, not by the two model reviews of the spec and the plan, which accepted the approval check; the earlier record's alternative "the digest alone, with no check of approvals" was rejected on that reasoning, and this record reverses that part.

## Related files and decisions

- `docs/specs/clone-enrollment.md`
- `docs/plans/2026-11-15-enroll-a-clone.md`
- [2026-11-15-enroll-makes-a-clone-known-on-the-manifest-hashes-and-the-owners-digest](2026-11-15-enroll-makes-a-clone-known-on-the-manifest-hashes-and-the-owners-digest.md)
- [2026-10-20-acknowledge-before-upgrade](2026-10-20-acknowledge-before-upgrade.md)
- [2026-10-22-installer-pins-declared-helpers](2026-10-22-installer-pins-declared-helpers.md)
- [2026-10-19-guarded-store](2026-10-19-guarded-store.md)
