# A clone is made known on a new machine by `wb enroll`, on the manifest's hashes, the approvals already there and the owner's digest

Status: Superseded
Superseded by 2026-11-15-enroll-writes-no-pins-and-leaves-them-to-upgrade-from-a-package
Date: 2026-11-15

## Context

Every command that acts on an installed project (`attach`, `upgrade`, `add`, `acknowledge`) first requires that the guarded store hold the project's baselines and a first-seen record at the clone's resolved path, and treats the project as new otherwise (`2026-10-20-acknowledge-before-upgrade`). That record says a project cloned a second time "is refused until `attach` settles recording a remote or a move"; `attach` was never given that job. Only `install` and `adopt` write the baselines, the first-seen record and the helper pins, and `adopt` refuses a repository that already has a manifest.

So a clone of an installed project on a machine that has never held it cannot be made known by any command. On 2026-11-15 the owner ran the first steps on a second machine and met exactly that: `acknowledge` refused with "treated as new here" and `adopt` refused with "the target is an existing project". The design that answers it is `docs/specs/clone-enrollment.md`; the roadmap candidate is `workbench-v1#enrol-a-clone`.

The choice needs a record because it decides what the machine will trust: the files of a clone are untrusted bytes until the owner says otherwise, and the new command is the one place where the owner's word makes them baselines and lets their helpers run.

## Decision

- A new owner-run command, `wb enroll`, with a read-only `wb preview enroll`, writes in the guarded store, and nowhere else, the baselines, the first-seen record and the helper pins of a clone. It runs through the `wb` launcher, is terminal-only at every level (its key offers `block` only), shows the whole list and a digest, and takes the first 12 characters of the digest typed back by the owner, as `acknowledge` does.
- What the owner confirms is a hash list taken from the clone and checked against the committed manifest: every file the manifest calls module-owned must equal the manifest's hash, an unrecorded file under `.workbench/` outside `local/` refuses, a seeded file or a slot block that differs is listed for the owner and baselined at the bytes in the clone, and every manifest entry must lie where its owner may write.
- A module's helper is pinned only if its declaration and tree are already approved on this machine, through an owner's record or a shipped release record. The command reads approvals and writes none.
- The basis of trust is the manifest's hashes, those approvals and the owner's typed digest. Nothing is compared with another machine or a remote.
- The command is the one exception to "the project must be known first", and it requires the project to be wholly unknown: a project with one of the two entries, or a malformed entry, is refused and nothing is written.

## Alternatives considered

- **Copy the project's store entry from the first machine.** Rejected: the first-seen record holds an absolute path that differs between machines, the copy is a manual edit of the guarded store, and it carries the first machine's pins and approvals along with its baselines.
- **Let `acknowledge` or `adopt` handle an unknown project.** Rejected: `acknowledge` exists to accept differences for a project already known, and the refusal of an unknown one is the property that protects it. `adopt` is for repositories with no manifest. Widening either would weaken a check that works.
- **The digest alone, with no check of approvals.** Rejected on the review of the spec: the owner's digest would then be the only thing standing between a planted helper in a clone and a pin that lets the launcher run it, and a hash list does not show what a helper does. Checking the approvals that `install` and `attach` already require adds an independent barrier at no cost for this repository's own modules, whose shipped records are tracked.
- **A second check against the first machine, such as an exported baseline file.** Rejected by the owner: the manifest's hashes plus the digest the owner confirms are enough. It would also add a file to copy between machines and a new format to trust.
- **Re-run `install` over the clone.** Rejected: it would rewrite the owner's files or refuse them, and it needs the packages.

## Consequences

- A second machine can run the harness and the helpers after three owner steps: the first run of the workbench, `wb enroll`, and `attach`.
- A clone whose manifest or module-owned files were altered in transit or on that machine is refused with the path. A seeded file the owner has edited, such as `AGENTS.md`, is not refused: the owner sees it listed and its bytes become the baseline, so an attacker who can edit a seeded file before the owner runs `enroll` can plant instructions that the owner may fail to notice in a long list. The preview lists each such file by name to keep it visible; it is the same risk the owner already takes in `acknowledge`, and accepting this record is the owner's word that it is taken here too.
- A third-party module cannot be enrolled until the owner has approved it on that machine.
- The command writes trust state, so it gets a security review when it is built (plan `2026-11-15-enroll-a-clone`, increment F), and its key and deny rule are added to the rendered permissions, which the owner refreshes with `wb rerender`.
- The older record stays as it is: it is not superseded, because its rule (an unknown project is refused) still holds for every command except this one.

## Evidence

- Run 2026-11-15 at commit `459dde9`, Python 3.15.0 on Darwin, on a fresh clone with a scratch `HOME`: `wb check` reported three helpers not pinned and no harness attached, and `preview attach` refused with "this machine holds no acknowledgement baselines for the project; it is treated as new here". Run by the owner on a second machine (home directory `/home/rziegler`; the owner pasted the output): `check` gave the same three problems, `preview acknowledge` gave the same refusal, and `preview adopt --dir . --package packages/workbench --select <the ten modules of the manifest>` refused with "the target is an existing project; use wb upgrade or wb add".
- Read at the same commit: `acknowledgement.check_known` is called by `attach`, `upgrade` and `acknowledge`, and the only writer of the baselines and the first-seen record is the install plan (`installplan.py`, `store_writes`).
- The spec was reviewed by a second model through the review engine in four rounds (nine findings, all applied) and the plan in three rounds (six findings, all applied, converged); the review files are in `.workbench/workbench/review-engine/`.

## Related files and decisions

- `docs/specs/clone-enrollment.md`
- `docs/plans/2026-11-15-enroll-a-clone.md`
- [2026-10-20-acknowledge-before-upgrade](2026-10-20-acknowledge-before-upgrade.md)
- [2026-10-19-guarded-store](2026-10-19-guarded-store.md)
- [2026-10-22-installer-pins-declared-helpers](2026-10-22-installer-pins-declared-helpers.md)
- [2026-10-27-rerender-is-terminal-only](2026-10-27-rerender-is-terminal-only.md)

## Clarification, 2026-11-15

Added with the owner's approval on the day the record was accepted, after a review of the record against its sources. The body above is unchanged.

- An unapproved module refuses the whole enrollment and nothing is written. The Decision's "a module's helper is pinned only if its declaration and tree are already approved" does not mean that an unapproved module is skipped while the rest is enrolled. Check 8 and acceptance criterion 5 of `docs/specs/clone-enrollment.md` say so, and the spec governs where the two read differently.
- In the Context, "write" means "create" for the baselines and the first-seen record: `install` and `adopt` are the only commands that create them, while `upgrade` and `acknowledge` rewrite the baselines of a project that is already known.
- `attach` is among the commands that refuse an unknown project because it calls the same check (`acknowledgement.check_known`), although `2026-10-20-acknowledge-before-upgrade` names only `upgrade`, `add` and `acknowledge`.
