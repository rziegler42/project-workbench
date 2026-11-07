# Make the shadow report split "reviewed but not collectable" by failed check

Status: Proposed
Created: 2026-11-06
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The shadow report says how many reviewed commands could not be labelled, and now also why. After this plan the line `reviewed but not collectable: <n>` is followed by a line that groups those commands by the failed checks of their verdict rows, so the owner can see whether the count is made of declines for a secret (`no_secret_lines`, `paths_not_credentials`, which the hook never collects by design and which can therefore never be labelled) or of something else. A test fails if the line is missing or counts a command that has a collected row.

The reason is a blind spot the spec names: a false decline of the secret kind never reaches the labelled set, so the false-decline rate cannot see it, and the owner is told to read the count when judging a cutover. On the owner's store of 2026-11-06 the count is 59 of 160 reviewed commands, and the report cannot say what they are.

## Scope

- `packages/workbench/action-review/tools/report.py`: a function that groups the reviewed commands without a collected row by the failed checks of their verdict rows, and one new output line after `reviewed but not collectable: <n>` when that count is above zero.
- `packages/workbench/action-review/tests/test_tools_report.py`: tests of the grouping and of the line (class `NotReviewed`).
- `docs/specs/action-review.md`: the sentence about the count in "The data files" (near line 687 to 690) and the report paragraph of "Labelling and the report" (near line 703 to 711).

## Non-goals

- What the hook collects, the store's rules, the redaction, and the two checks that turn collection off. The secret declines stay uncollected and unlabelled.
- The bound, the cutover line and its reasons, the label counts, and the existing line `reviewed but not collectable: <n>`, which keeps its exact text.
- A breakdown of `unreviewable` or of `no_rule`. They are by design (the engine's grammar and its rules) and the report already counts them by reason.
- Any change to `label.py`, including a way to revisit a label.
- The hook that decides, the push rule and the cutover.

## Assumptions and constraints

- The verdict rows already hold what is needed: a reviewed row names `failed_checks` (an approve names none, a decline at least one; `shadow_store.py`), and the command's hash links it to the collected row. The report reads no fact, command, reason or note of a collected row, and prints check names and counts only, as it does for "false declines by check". A test that already forbids printing a command, fact, reason or note stays, and the test that limits the report to one fact of a collected row stays true.
- The shape of the line is the agent's proposal: `  by failed check (a row counts under each check it failed): no_secret_lines 41, paths_not_credentials 6, approve 12`, ordered like the other `by check` lines. A reviewed approve with no collected row (a row with no `facts:` line, or one too large to store) has no failed check, so it is counted under the name `approve`. The total of the groups can be above `<n>` when a row failed two checks, and the line says so.
- When a command was reviewed more times than it has collected rows, which of its verdict rows lack a collected row cannot be told. The report attributes the gap to the latest verdict rows of that command. This is the same hash-count matching `not_collectable` already uses and is stated in the function's docstring.
- The report is copied out of the project to the owner's own directory (`~/action-review-shadow`, whose files are read-only), so the owner's report does not change until the owner copies the new file there. The module is a package file: a tree under `packages/` changes, so the owner makes the release approvals, and the upgrade and the rerender follow the commit.
- The edit is made and tested in a scratch clone and copied by the owner's script, as in the earlier plans.

## Completion criteria

1. With reviewed commands that have no collected row, the report prints, directly after `reviewed but not collectable: <n>`, one line that groups them by failed check, with the counts, in the order of the other `by check` lines, and says that a row counts under each check it failed. With none, no extra line is printed.
2. The count `<n>` and its line are unchanged for every case the existing test covers.
3. A decline for `no_secret_lines` with no collected row appears under that name; an approve with no collected row appears under `approve`; a reviewed command that has a collected row appears in no group; when one command was reviewed more times than it has collected rows, the gap is grouped by the failed checks of its latest verdict rows, and the existing count is unchanged.
4. The report prints no command, fact, reason or note, and only printable ASCII, as before.
5. The spec says the report splits the count and why it matters, and `wb run code-work check` passes.

## Increments

### Increment A — Group the uncollectable commands by failed check

**Outcome:** completion criteria 1 to 5 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/tools/report.py`, `packages/workbench/action-review/tests/test_tools_report.py`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first, in a scratch clone, in `NotReviewed`: a decline for a secret check with no collected row appears under its name; an approve with no collected row appears under `approve`; a command with a collected row appears nowhere; a row that failed two checks counts under both and the line says a row counts under each; a command reviewed twice with one collected row, whose older verdict row failed one check and whose latest verdict row failed another, is grouped under the latest row's check only (one gap, so one row), and a command reviewed three times with one collected row is grouped under the failed checks of its latest two rows; the count of the existing line is the same as before in both; with none uncollectable the line is absent; the existing line keeps its text; the line prints no hash and no text of the store. See them fail.
2. Add the function and the line to `report.py`, reading only the verdict rows' `failed_checks`, `reviewed` and `command_sha256`, and the collected rows' `command_sha256`.
3. Edit the two passages of the spec. Search the repository for another description of the report's not-collectable line (`docs/development.md`, the module's README or skill); report one that disagrees and change it only if it states the old output.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_tools_report.py` and the rest of the `action-review` module suite, run as `python3 -B` discovery on the module's tests directory; `wb run code-work check`. Not run: the whole suite (no installer code changes), the hook tests beyond the module suite, and the test-set runner. After the copy and the release, `wb verify packages/workbench` shows the new tree hash for `action-review`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-shadow-report-splits-not-collectable#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether the line answers the owner's question on the real store is for the owner to see after replacing the report in the dedicated directory and running it.

## Risks and sensitive actions

- A package file changes: the release approvals, the removal of the stale shipped records after the owner approves the list, the upgrade and the rerender are the owner's. Nothing is pushed without the owner's word.
- The report prints derived data from the owner's store. It already prints check names and counts, and this adds the same kind of line. The test that no command, fact, reason or note is printed is kept, and the new tests assert it for the new line. A security review is not suggested; if the owner wants one, the surface is the report's reading of the store.
- The new line shows how many reviewed commands are declines for a secret. It names the check and prints no secret.
- The copy of `report.py` in `~/action-review-shadow` is the owner's to replace; this plan touches nothing outside the project.

## Review record

Codex (`gpt-5.6-terra`), plan review, 2 rounds of 3, converged with no meaningful finding in round 2.

- Applied (round 1): the plan stated that, for a command reviewed more often than it has collected rows, the gap goes to its latest verdict rows, but no test could tell that from attributing it to an older row. Step 1 now has a test for a command reviewed twice with one collected row (one gap, the latest row's check only) and one reviewed three times with one collected row (the latest two rows), each with the existing count unchanged; criterion 3 says the same. While applying it I corrected my own first wording, which said "three times" for the one-gap case.
- Rejected: none. Left for the owner: nothing from the review.

## Deferred work

- A breakdown of `unreviewable` (by the form that made it so), if the owner suspects reviewable commits are being missed.
- A way to revisit a label in `label.py`.
- The decision on what the hook does with an unconfirmed removal, and the rubric question about the disposable check, both left for the plan of the hook that decides.

## Result

Empty until work starts.
