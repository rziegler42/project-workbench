# `wb acknowledge` prints added review-engine records as a count, and covers every one of them in its digest

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-16
Supersedes 2026-11-15-enroll-baselines-only-what-the-manifest-records
Date: 2026-11-16

## Context

`2026-11-15-enroll-baselines-only-what-the-manifest-records`, accepted the day before, decides that `wb enroll` leaves the files under `.workbench/` that the manifest does not record to `wb acknowledge`, and says in its consequences that `acknowledge` refuses a list of more than 500 paths (`MAX_LISTED` in `workbench/acknowledge.py`), that this repository had about 476 such files, and that each review adds 6 to 13 more, so that a clone could soon not pass that step. That limit was left to the owner.

It was close. The owner ran the setup steps by hand on a second machine on 2026-11-15, at commit `2b1d9ee`, and `acknowledge` listed and recorded 461 paths, about 39 below the bound. A review committed with each plan or spec raises the count, and the project's rule is that a review's files are committed with the document it reviews, so the count only grows. Nearly all of them (460 of 461) are the review engine's own files under `.workbench/workbench/review-engine/<kind>-<hash>/`, with names the engine alone chooses.

The accepted decision `2026-10-20-acknowledge-before-upgrade` says `acknowledge` "lists" the differences and replaces the baselines for exactly the listed paths after the typed digest. A list of several hundred lines of hashes is not read by anyone, so the typed digest over it confirms little that a count would not.

What the review engine does with a record is relevant to what showing it buys. The engine seals each review's state with a key kept in the guarded store of one machine, and uses a state, and the round files its state names by hash, only when the seal holds. A clone has no key, or a key that did not seal the records it holds, so a record that arrives by `git clone` or `git pull` is read by the engine as unsealed and refused; this was run against `decide`, `convergence` and `extend` on a scratch clone, and the refusal of a review round is read in the engine's source and not run.

## Decision

- **What is printed as a count.** `wb acknowledge`, and `wb preview acknowledge` with it, print a difference as a count by kind of document, and not as a line of its own, only when all of these hold: it is an addition with no baseline; it was read as a regular file (it has a digest and no reason, so it is not a link, a directory or a name that cannot be accepted); and its path is exactly `.workbench/workbench/review-engine/<kind>-<16 lowercase hex digits>/<name>` with `<kind>` one of `plan`, `spec`, `roadmap` and `adr`, and `<name>` one of `state.json`, `ledger.md`, `schema.json` and `round-<n>.json` with `<n>` from 1 to 9999, in the spelling of the review engine and in no other (no other case, suffix, depth, folder or character). Every other difference, including a changed or removed file of that spelling, is a line of its own.
- **What the digest and the baselines cover.** Every path, the counted ones too. The digest is built from the whole list and the baselines recorded after the typed digest hold every path, as before. The count says so in its own text. The owner is shown less, and confirms the same set.
- **The bound.** The limit of 500 counts the lines that are printed. The ceiling on the total work stays what it was: at most 20,000 entries under `.workbench/` and 256 MiB of file content read.
- **What the rule is.** A function of one difference, in `workbench/reviewrecords.py`. It reads no file and follows nothing, and it decides what is printed, never what is accepted. It does not say that a record is genuine; the engine's seal does, on the machine that holds the key.
- **Where the spelling comes from.** It is the review engine's, copied, because installer code cannot import package code, and a test reads the engine's helper and fails when the two differ.
- **What stays as decided before, restated so that this record can be read alone.** `wb enroll`, with `wb preview enroll`, writes in the guarded store, and nowhere else, the baselines and the first-seen record of a clone, and writes no pin and reads no approval record; the baselines hold what the manifest records and the manifest itself, and nothing else. A file under `.workbench/` outside `local/` that the manifest does not record is neither refused nor baselined by `enroll`; its preview says how many there are and under which directories, and says that `acknowledge` lists them next; a link, a directory in place of a file or another kind of file anywhere in that scope is refused. The command runs through the `wb` launcher; it is owner-run and terminal-only at every level, its key offering `block` only; it shows the whole list and a digest and takes the first 12 characters typed back; it reads the committed manifest through the strict reader and checks every entry against the project's path and ownership rules; every file the manifest calls module-owned must equal the manifest's hash; a seeded file or a slot block that differs is listed for the owner and baselined at the bytes in the clone; it requires the project to be wholly unknown on the machine and refuses one with one entry or a malformed entry; the basis of trust is the manifest's hashes and the owner's typed digest, with no comparison against another machine. The helpers of an enrolled clone are pinned by `wb upgrade --package <directory>`, which needs the clone's baselines to hold no difference, so the order on a new machine is `enroll`, `acknowledge`, `upgrade --package`, `attach`.
- **A refinement, not a change, of an earlier decision.** `2026-10-20-acknowledge-before-upgrade` stands, and `acknowledge` still lists every difference that is not of the spelling above. This record narrows what "lists" means for that one class and does not edit that record.
- **Review records stay tracked.** The project's rule that a review's files are committed with the document they review is not reopened here.

## Alternatives considered

- **Raise `MAX_LISTED`.** Rejected: it postpones the refusal by a number that the next reviews use up, and a list of that length is still not read.
- **Print the last few lines, or truncate the list.** Rejected: what is hidden is then decided by sort order, not by what matters, and a path the owner would want to see can fall in the part that is not shown.
- **Leave the engine's folder out of the comparison.** Rejected: a file there that does not have the engine's spelling, a changed or removed record, a link or a planted file would then be invisible to the owner and to the gate that `upgrade` and `add` read (`2026-10-20-acknowledge-before-upgrade`).
- **Stop tracking review records.** Rejected: plans cite their review files and the project's rule is that nothing tracked points to anything untracked; the engine keeps a rollback mark per machine and reads a state that was sealed on a machine and is gone from it as a rollback (read in the engine's source, not run), so the effect of untracked records on a second machine was not tested; the records already committed stay in history; and it would need a superseding record of the decision to track them. It also does not remove the need on the machine that already holds them untracked.
- **Count a record only when the engine verifies its seal.** Rejected: the key stays on one machine, so on a clone, where the list matters most, nothing would verify.
- **A dated note on the earlier enroll record instead of a new record.** Rejected: the change is not a clarification of that record; it decides what the owner is shown and confirms for a class of files, and a later reader looks for that under its own name.

## Consequences

- The owner types a digest over a list in which one class is a count. They cannot see the names or the hashes of those files in the list, and a hostile clone can put any bytes in a file of that spelling. Such a file is baselined as the owner would have baselined it before, and the engine does not use it unless its own seal holds; anyone who opens the file by hand reads whatever was put there, with or without this change.
- The spelling lives in three places: the engine, the installer's rule (tied to the engine by a test), and the `action-review` helper, which holds its own pattern of it and has no test that ties it.
- A project that commits another module's unrecorded files would see them listed again, a line each. A summary for any other class needs its own record.
- `2026-10-20-acknowledge-before-upgrade` says "lists" and is not edited; this record is its refinement. The earlier enroll record is superseded as a whole, and its status line names this record once this one is accepted; its text is not touched.
- The specs `clone-enrollment.md` and `installer-interface.md`, `INSTALL.md` and `docs/development.md` already state the behaviour (commit `154f03f`).

## Evidence

- Built by the plan `2026-11-16-collapse-review-records-in-the-list`, increments A (`c185b11`), B (`6fcef2c`) and C (`154f03f`), pushed to `origin/main`.
- Run 2026-11-16, Python 3.15.0 on Darwin: the tests of the area (`test_acknowledge`, `test_acknowledgement`, `test_reviewrecords`, `test_acknowledge_pins`, `test_ack_recover_ask`, `test_ack_recover_levels`), 201 tests, OK, 1 skipped, at `6fcef2c`; a mutation pass of 28 mutants of the rule and one of 18 mutants of the summary and the bound (all killed but one equivalent survivor); a test with 3,008 added records, which printed under 200 lines, and one with the real bound of 500 against 501 other files.
- Run 2026-11-16 on a fresh `git clone` of this repository at `6fcef2c` with a scratch `HOME`, driven in process with a fake terminal: 466 unrecorded files, of which 465 review records in 87 directories; `preview acknowledge` printed 110 lines; `acknowledge` recorded 466 paths; the preview then said nothing to acknowledge; `upgrade --package packages/workbench` created the 14 pins; `check` found no problems and `doctor` none and 1 risk (the missing `review-profiles.json`). The owner has not run the changed list by hand.
- Run 2026-11-16 on a scratch clone, the engine helper of the clone and a scratch `HOME`: a committed review read as unsealed with no key ("there is no seal key on this machine") and with a key that did not seal it ("the seal does not match"), and `decide`, `convergence` and `extend` refused it; read in the engine's source, not run: the refusal of a review round, and that the engine reads a round file only after comparing its hash with the sealed state and never reads `ledger.md` back.
- A `reviewer` agent for each of the three increments (no blocking finding after the plan's amendment) and a `security-reviewer` agent on the change to `acknowledge` (no Critical, High or Medium finding; two Low, recorded in the plan's Result).

## Related files and decisions

- `docs/specs/clone-enrollment.md`
- `docs/specs/installer-interface.md`
- `docs/plans/2026-11-16-collapse-review-records-in-the-list.md`
- [2026-11-15-enroll-baselines-only-what-the-manifest-records](2026-11-15-enroll-baselines-only-what-the-manifest-records.md)
- [2026-10-20-acknowledge-before-upgrade](2026-10-20-acknowledge-before-upgrade.md)
- [2026-10-19-guarded-store](2026-10-19-guarded-store.md)
