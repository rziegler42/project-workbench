# Show review records as a summary in the list that the owner acknowledges

Status: In Progress
Created: 2026-11-16
Candidate: none (the bound of 500 paths in the owner-run command that accepts changes surfaced while enrolling a second machine; it needs no roadmap direction)
Specs: clone-enrollment, installer-interface

## Goal

`wb acknowledge` stops refusing a clone because of how many review-engine files it holds. The files of the review engine that were added, and that have exactly the names and place the engine gives them, are shown as one summary instead of one line each. Every other difference is still shown on its own line. The digest the owner types still covers every path, and the baselines recorded still hold every path. When the plan is done, the list of a clone of this repository fits on a screen, and it keeps fitting as reviews are added.

## Scope

- A rule, in installer code, that says which added paths are review-engine records: a regular file, added, with no baseline, at `.workbench/workbench/review-engine/<kind>-<16 hex>/<name>`, where `<kind>` is `plan`, `spec`, `roadmap` or `adr`, and `<name>` is `state.json`, `ledger.md`, `schema.json` or `round-<n>.json`. The spelling is the engine's own (`KINDS`, `FILE_NAME` and the key form in `packages/workbench/review-engine/helper/review-engine`).
- `workbench/acknowledge.py`: the 500-path refusal applies to the lines that are shown, not to the summarised records. The summary names the count of files and of directories, by kind. The total work stays bounded by the existing `MAX_WALKED` (20000 entries) and `MAX_READ_BYTES` of `workbench/acknowledgement.py`.
- The two specs and `INSTALL.md` that state the 500-path bound.

## Non-goals

- No change to `acknowledgement.differences`, to what `upgrade`, `add` or `enroll` refuse or list, or to the baselines written.
- No change to the review engine, to its files, or to the decision to track reviews in git.
- No change to `recover.py` or `unfinished.py`, which have their own bound.
- No collapse of a changed, removed, link, directory or misnamed path, and none of anything outside the engine's folder, such as `.workbench/remote-runner.toml`.
- No acknowledgement without the owner's typed digest, and no change to who may run it.

## Assumptions and constraints

- Read, not run: the engine reads a review only from a sealed state. The seal is an HMAC with a key kept in the guarded store of one machine (`NO_KEY`, `NO_MATCH` and `ROLLED_BACK` in the helper), and a command that changes a review refuses a state whose seal is not `ok`. So a record added by someone else, or copied from another machine, is "unsealed" here and is not used. Increment A runs this on a scratch `HOME` before the rule is built, and stops the plan if it does not hold.
- The rule duplicates the engine's spelling, because installer code cannot import package code. A test reads the helper's source and fails when the two differ.
- Installer code in `workbench/` is imported by the harness hooks, so each edit is built and tested in a scratch copy with a scratch `HOME` and applied to the real tree in one scripted pass with a backup. A copy's command line is never run against the real `HOME`.
- Nothing tracked points to anything untracked: no document written by this plan cites the owner's todo list.

## Completion criteria

1. A test shows 3000 added review records of the exact shape are summarised, listed nowhere else, and covered by the digest, that the command does not refuse, and that the summary prints the exact numbers of files and of distinct directories, in total and for each kind, from a fixture with several recognised files in one review directory and directories of at least two kinds.
2. A test shows each of these is listed on its own line and not summarised: a changed or removed review file, a link with a review record's name, a directory with a review record's name that holds files (an added directory is no difference of its own, as now, so its files are what is listed), a file one character off the pattern (case, extra suffix, extra directory level, wrong hash length), a file of the right name in another folder, and `.workbench/remote-runner.toml`.
3. A test shows that more than 500 listed lines is still refused, and that a summarised record that changes changes the digest.
4. A test fails when the engine's kinds or file-name pattern differ from the rule's.
5. A run on a fresh clone of this repository with a scratch `HOME` shows `wb preview acknowledge` compact, and the owner-run step is the owner's to type.
6. The two specs and `INSTALL.md` state the new behaviour and no longer state a bound of 500 paths on the whole list; none cites the todo list.

## Increments

### Increment A — The rule, and the check that the engine ignores a forged record

**Outcome:** a pure function in a new module `workbench/reviewrecords.py` says whether a `Difference` is a summarised review record, with its tests; and the claim in the assumptions has been run.
**Dependencies:** none.
**Affected areas:** `workbench/reviewrecords.py` (new), `tests/test_reviewrecords.py` (new). Nothing else.
**Steps:**
1. In a scratch `HOME` with a scratch copy of this repository, make a review record by hand (a `state.json` with a wrong or missing seal, in the engine's folder) and run `wb run review-engine status` and a command that would change it, from the copy's own code in process. Record that the state reads `unsealed` and that nothing uses it. Stop and report if it is used.
2. Write the failing tests first: the shape cases of criterion 2, case spellings, a path with `..`, an empty or very long name, a `round-0.json`, a `round-` number of five digits, and the drift test of criterion 4.
3. Write the function: it takes a path and the kind, reason, baseline and current of a `Difference`, matches the whole path with `re.fullmatch`, and says yes only for an added, hashed, reasonless difference of the exact shape. It reads no file and follows nothing.
4. Run the tests, and a mutation pass (one mutant for each clause of the rule) and confirm each is killed.
5. Ask the `reviewer` agent to review the increment as `run-increment` says, judge the findings with `evaluate-findings`, and record the review under this plan's Result, before the owner is asked to commit.
**Verification:** `python3 -B -W default -m unittest tests.test_reviewrecords` with a scratch `HOME`, and the recorded result of step 1.
**Evidence:** one local commit with the trailer `Plan: 2026-11-16-collapse-review-records-in-the-list#A`.

### Increment B — `acknowledge` shows the summary and bounds the lines

**Outcome:** `examine` and `render` of `workbench/acknowledge.py` use the rule: the summarised records are in the digest and the baselines but not in the listed lines, and the refusal at 500 counts only the listed lines.
**Dependencies:** A.
**Affected areas:** `workbench/acknowledge.py`, `tests/test_acknowledge.py` (the nearest tests of the area), and any other reader of `review.found` or of `render` that the search in step 1 finds.
**Steps:**
1. Search for every reader of `Review.found`, `render` and `MAX_LISTED` (the preview, the level-run route and its log) and record which of them print the list; each must print the same summary or say why not.
2. Write the failing tests first, for criteria 1 to 3, including a run that adds 3000 records to a scratch project and one that adds 501 other files.
3. Change `examine` to split `found` into listed lines and summarised records, refusing when the listed lines exceed `MAX_LISTED`, and keeping `Review.fields["differences"]` as every difference so the digest and the baselines are unchanged in form. Change `render` to print the summary (files and directories, by kind) and a line that says every path is covered by the digest.
4. Add to the tests a fixture with several recognised files in one review directory and directories of at least two kinds, asserting the exact counts of files and of distinct directories printed in total and for each kind, and a mutant of the aggregation that the test kills.
5. Apply to the real tree in one scripted pass with a backup, as the assumptions say, and run the tests there.
6. Ask the `reviewer` agent to review the increment, record it under this plan's Result as in A, and stop for the security review the owner asked for; its findings are judged and fixed, with a regression test each, before the owner is asked to commit.
**Verification:** `python3 -B -W default -m unittest tests.test_acknowledge tests.test_reviewrecords tests.test_acknowledgement` and the tests of each other reader found in step 1, with a scratch `HOME`.
**Evidence:** one local commit with the trailer `Plan: 2026-11-16-collapse-review-records-in-the-list#B`.

### Increment C — The documents, and the run on a fresh clone

**Outcome:** the two specs and `INSTALL.md` state what is built, and a fresh clone shows the compact list.
**Dependencies:** B.
**Affected areas:** `docs/specs/clone-enrollment.md`, `docs/specs/installer-interface.md`, `INSTALL.md`, this plan's Result.
**Steps:**
1. Replace the statements of a bound of 500 paths on the whole list with the new rule, name the engine-spelling coupling as a known limit, and remove the words that send the reader to the todo list from `INSTALL.md`.
2. On a fresh `git clone` at the new commit with a scratch `HOME`, run `enroll` and the preview of `acknowledge` in process with a fake terminal and record the number of lines and the summary printed. The owner-run command stays the owner's.
3. Run the document check and the plan check.
4. Ask the `reviewer` agent to review the increment, and record the review under this plan's Result as in A.
**Verification:** the run of step 2, `wb run code-work check`, and the document check, as run.
**Evidence:** one local commit with the trailer `Plan: 2026-11-16-collapse-review-records-in-the-list#C`.

## Verification for the plan as a whole

Confirmed: A's tests and B's tests stand unless C changes code, and C changes none. Rerun after C: the three test modules named in B once, and the fresh-clone run. No whole-suite run is planned; I would recommend one only if step 1 of B finds a reader of `render` outside the tests named.

## Risks and sensitive actions

- **What the owner types.** The owner confirms a list in which one class is summarised. If the summary hid something that matters, the owner would accept it without seeing it. The rule is narrow (exact folder, exact names, regular files, added only) and the engine ignores an unsealed state, but the engine's spelling is copied; criterion 4 is the guard against drift. I recommend a security review of B, by the `security-review` module, since this changes what an owner-run acceptance shows; it runs only if the owner asks.
- **A path that looks like a record and is not** (a hostile file in the engine's folder). It is added and unsealed, so the engine will not use it, and it is baselined as the owner would have baselined it before. A residual risk is that a file of the right name holds hostile content that another tool reads; no other reader of that folder is known, and step 1 of A says whether one is found.
- Installer code is imported by hooks: a half-edit locks every tool. The scratch-copy workflow in the assumptions is the control.
- Nothing is pushed by this plan, and no file is deleted.

## Review record

Empty until a review is asked for.

## Deferred work

- The 500-path bounds of `recover.py` and `unfinished.py` are left as they are.
- `.workbench/remote-runner.toml` stays an unrecorded file in the list, one line.
- Whether tracking review records is right is not reopened here; the earlier decision stands.

## Result

### Increment A

**Built and committed as `c185b11`.** `workbench/reviewrecords.py` (new, imported by nothing yet) with `record_of(difference)`, and `tests/test_reviewrecords.py` (new).

**Step 1, run on 2026-11-16** with a scratch `git clone` of this repository at `6cc997a` and a scratch `HOME`, driving the clone's own engine helper (`python3 -B <clone>/packages/workbench/review-engine/helper/review-engine`, `PYTHONPATH=<clone>/workbench`, Python 3.15). With no seal key on the machine, a committed review read `unsealed` ("there is no seal key on this machine") and `decide` and `convergence` refused it. After a key was made by `init` of a document with no review, the same committed review read `unsealed` ("the seal does not match") and `decide`, `convergence` and `extend` refused it. An edit of a record sealed there that left it malformed read "the state is not usable" and `decide` and `extend` refused it; that case did not reach the seal comparison, so the second case is the evidence for a mismatch. Not run: a review round (it calls a bridge), so the round command's refusal of an unsealed state is read in the engine's source (the `changeable` check) and not exercised. Readers of the engine's folder found by search: the engine, and `action-review`, which holds its own pattern of the same spelling (`REVIEW_STATE_PATH`, `REVIEW_FILE_PATH`); that is a third copy that the drift test does not cover.

**Steps 2 to 4.** The tests were written first and failed on the missing module. With the module: 12 tests, OK (`python3 -B -W default -m unittest tests.test_reviewrecords`, scratch `HOME`). A mutation pass of 28 mutants on a scratch copy, one per clause and constant, killed all 28. The first pass left four alive: the kind check (tests changed another field with it), a digest with trailing characters, a non-text path, and a path-length clause. Three got tests; the length clause was removed, since a path of the exact shape is under 100 characters and the clause could not change an outcome.

**Step 5, review.** The `reviewer` agent read the module, the tests, the engine helper and the plan. No blocking findings; it found the rule equal to the engine's `KINDS`, `NAMESPACE`, `FILE_NAME` and `review_key`, found no path outside the engine's records that matches, and found no conflict with the non-goals. Two non-blocking notes. (1) The drift test is partly textual: a reformat of the helper's `KINDS` or `FILE_NAME` line makes it raise, and reordering `KINDS` fails it; it fails loudly, not silently, so I left it. (2) This Result was empty; it is written here. The reviewer could not run anything and did not trace every writer of the engine's folder.

**Left for the owner.** Nothing for A; B follows.

### Increment B

**Built and committed (the commit that holds this record).** `workbench/acknowledge.py` (modified) and `tests/test_acknowledge.py` (modified, new class `ReviewRecords`). `split` and `summary_lines` are new; `Review` keeps `found` whole and adds `listed` and `records`; `examine` refuses when more than `MAX_LISTED` lines would be shown, not when more paths differ; `render` prints the listed lines, then the summary. `Review.fields`, the digest and the baselines are built from every difference, as before.

**Step 1.** A search of `workbench/` found no reader of this command's `Review.found`, `render`, `examine` or `MAX_LISTED` outside `workbench/acknowledge.py` (`recover.py` and `unfinished.py` have their own, unrelated ones); `workbench/cli.py` and `workbench/levelrun.py` take the digest and the `log` and read no list. The preview and the level-run route reach the same `examine` and `render`.

**Steps 2 to 5.** The tests were written first in a scratch copy of the tree: eight, of which six failed on the old code (the two that passed guard a refusal that must not change). With the change, the new class passes. A ninth test (no records, no summary) and a tenth (the real constant of 500 against 501 other files) were added after the mutation pass and the review. The tests of the area (`test_acknowledge`, `test_acknowledgement`, `test_reviewrecords`, `test_acknowledge_pins`, `test_ack_recover_ask`, `test_ack_recover_levels`): 201 tests, OK, 1 skipped, in the real tree with a scratch `HOME` (Python 3.15). A mutation pass of 18 mutants of the summary counts, the split, the bound, the printing and the digest and baseline coverage killed 17; the survivor drops the records from `Review.fields["differences"]`, and is equivalent, because `baselines_after` carries each record's hash too, so the digest still changes with any record (the test that changes a record's bytes checks both digests). The change was applied to the real tree in one scripted pass with a backup, after checking that both files equalled `HEAD`; the installer imported afterwards. `git status` shows only the two files.

**Step 6, reviews.** `reviewer` agent: no blocking findings. It confirmed the digest and the baselines still hold every path, that the bound counts the printed lines, and that the numbers printed are right. It noted that the plan's wording of a run with 501 other files was exercised only with the bound patched to 2 (applied: the tenth test), that no test has a directory with a record's name that holds files (rejected: `spec-<h>/ledger.md/inner.txt` in `test_whatever_is_not_exactly_a_record_is_a_line` is a directory named `ledger.md` holding a file, and the test asserts the inner file is a line), and two cosmetic notes (the refusal wording when no record exists, and `split` run twice per `examine`), left as they are. It ran nothing and did not trace `cli.py` or `levelrun.py` line by line.

`security-reviewer` agent, at the owner's request, on a copy with its own `HOME`: no Critical, High or Medium finding. Tested: look-alike names (trailing space or dot, `round-0`, `round-01`, `round-10000`, an extra name, an extra level, a Cyrillic letter, a full-width digit, a 15-digit key) are each a line and only the exact four are counted; a name with a control character or a trailing newline cannot be accepted and the command refuses; a FIFO, links, a directory and an unreadable file with a record's name are each refused and none is counted; the digest changes when a summarised file changes, is removed or is added and returns when restored, and is built from the whole list; a run of 480 records printed the right counts and wrote exactly 480 baselines; 4800 records took 0.5 s and printed 27 lines; more than `MAX_WALKED` entries are refused. Not tested: a case-sensitive filesystem (case variants collided with the real files on the reviewer's machine; read only). Low 1: the content of a summarised file is not shown to the owner, so a hostile clone's bytes in such a file reach no one who reads only the list; the reviewer could not confirm that nothing reads those files without the seal. I then read the engine: it reads `state.json` only through the seal check, reads a `round-N.json` only after comparing its hash with the sealed state, and writes `ledger.md` and never reads it back; the `peer-review` skill names the files only to say what to commit. Residual: anyone or any agent that opens such a file by hand reads whatever a hostile clone put there, with or without this change. Low 2: a record-named path with a baseline that changes is listed as `changed`; no correction needed. No fix is made, so there is no regression test and no second look.

**Not run.** The whole suite (`tests/run_all.py`); `test_levels` and `test_enroll`, which mention the preview of this command (they do not read the list); a case-sensitive filesystem; a run in a real terminal.

**Left for the owner.** Nothing for B; C follows.
