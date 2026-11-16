# `wb enroll` baselines only what the manifest records; unrecorded files under `.workbench/` are left for `acknowledge`

Status: Superseded
Superseded by 2026-11-16-acknowledge-counts-added-review-engine-records
Supersedes 2026-11-15-enroll-writes-no-pins-and-leaves-them-to-upgrade-from-a-package
Date: 2026-11-15

## Context

`2026-11-15-enroll-writes-no-pins-and-leaves-them-to-upgrade-from-a-package`, accepted the same day, says that `wb enroll` refuses a clone that has an unrecorded file under `.workbench/` outside `local/`, as `acknowledge` treats an added file.

Reading this repository against that rule showed it cannot hold. At commit `4b92f4e` the repository tracks `.workbench/remote-runner.toml`, which the manifest does not record, and 463 files of review records under `.workbench/workbench/review-engine/`, which it does not record either: the review engine keeps each review's files in a directory of its module's namespace and the project commits them with the plan or spec they review, so every review adds about 6 to 13 files. `wb preview acknowledge` in this repository, on 2026-11-15, lists the 13 review files committed that day as "added", which is the form such a file takes on a machine whose baselines are older than the commit. A clone of this repository would therefore be refused by its own enroll, and so would any project that commits a review.

The unrecorded files are not hashes the manifest vouches for, which is the basis of trust this command rests on, so baselining them would put files into the baselines on nothing but the owner's digest. Refusing them makes the repository unenrollable.

## Decision

- `wb enroll`, with `wb preview enroll`, writes in the guarded store, and nowhere else, the baselines and the first-seen record of a clone, and writes no pin and reads no approval record. The baselines hold what the manifest records (every recorded file that is present, at the bytes in the clone) and the manifest itself, and nothing else.
- A file under `.workbench/` outside `local/` that the manifest does not record is neither refused nor baselined. The preview says how many there are and under which directories (a count for each directory, and every path where a directory holds ten or fewer), and says that `acknowledge` lists them next. A link, a directory in place of a file, or another kind of file anywhere in that scope is refused, as before.
- Everything else of the earlier record stands as written, and is restated here so that this record can be read alone: the command runs through the `wb` launcher; it is owner-run and terminal-only at every level, its key offering `block` only; it shows the whole list and a digest and takes the first 12 characters typed back; it reads the committed manifest through the strict reader and checks every entry against the project's path and ownership rules; every file the manifest calls module-owned must equal the manifest's hash; a seeded file or a slot block that differs is listed for the owner and baselined at the bytes in the clone (a block's file is baselined whole); it requires the project to be wholly unknown on the machine and refuses one with one entry or a malformed entry; the basis of trust is the manifest's hashes and the owner's typed digest, with no comparison against another machine.
- The helpers of an enrolled clone are pinned by `wb upgrade --package <directory>`, as the earlier record says, and `upgrade` needs the clone's baselines to hold no difference, so the order on a new machine is `enroll`, `acknowledge`, `upgrade --package`, `attach`.

## Alternatives considered

- **Refuse any unrecorded file (the earlier record).** Rejected: it makes this repository, and any project that commits a review, unenrollable.
- **Baseline the unrecorded files in `enroll`.** Rejected: the manifest has no hash for them, so the baselines would rest on the owner's digest alone for several hundred files that no list of that length lets anyone read, in the command that is meant to add the least trust. `acknowledge` already is the owner's way to accept files added after the last baseline.
- **Skip the unrecorded files silently.** Rejected: the owner should see that they exist and that the next step lists them.

## Consequences

- One more owner step than the earlier record says, and it is the existing one: `acknowledge`, whose preview lists the added files with their hashes.
- `acknowledge` refuses a list of more than 500 paths (`MAX_LISTED` in `workbench/acknowledge.py`). This repository has about 476 unrecorded files at the time of this record, and each review adds more, so a clone of it is close to a list that `acknowledge` cannot show. That is a limit of `acknowledge`, not of this command, and it is raised with the owner separately; until it is settled, a clone with more unrecorded files than the bound cannot pass the `acknowledge` step.
- The preview of `enroll` does not list the unrecorded files one by one beyond the rule above, so what the owner confirms for them is nothing: they are not baselined.
- The earlier record is superseded as a whole, and its status line names this record once this one is accepted; its text is not touched.
- The spec `docs/specs/clone-enrollment.md` and the plan `2026-11-15-enroll-a-clone` change to match, and the plan needs the owner's new approval.

## Evidence

- Run 2026-11-15, Python 3.15.0 on Darwin, at commit `4b92f4e` and then at `6bd4d1b`: `git ls-files .workbench` lists 64 tracked files outside the review-engine directories, of which exactly one, `.workbench/remote-runner.toml`, is not recorded in `.workbench/manifest.json`, and 463 tracked files under `.workbench/workbench/review-engine/`, none recorded. `wb preview acknowledge` in this repository listed 13 "added" paths, all review files of 2026-11-15.
- Read at the same commit: `acknowledgement.differences` scopes the comparison to every file under `.workbench/` outside `local/`, so an unrecorded file is "added" unless it has a baseline; `acknowledge.MAX_LISTED` is 500.
- The flaw was found by the author when reading the repository before building the read side, not by the two model reviews of the spec and the plan.

## Related files and decisions

- `docs/specs/clone-enrollment.md`
- `docs/plans/2026-11-15-enroll-a-clone.md`
- [2026-11-15-enroll-writes-no-pins-and-leaves-them-to-upgrade-from-a-package](2026-11-15-enroll-writes-no-pins-and-leaves-them-to-upgrade-from-a-package.md)
- [2026-10-20-acknowledge-before-upgrade](2026-10-20-acknowledge-before-upgrade.md)
- [2026-10-19-guarded-store](2026-10-19-guarded-store.md)
