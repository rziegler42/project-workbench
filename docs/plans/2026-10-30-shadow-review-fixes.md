# Fix what the security review of the action-review shadow found

Status: Proposed
Created: 2026-10-30
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The security review of the shadow built by plan `2026-10-29-action-review-shadow-hook` (its Review record; a reading-only pass, because
the agent gate refused the agent's commands) found one functional fault and several weaknesses in the evidence the cutover rests on.
After this plan:

- the hook gives the engine a `PATH` in which the engine finds the owner's `wb` launcher, so a review is no longer `refused:
  describe could not be started` for every command, and its waits add up to less than the hook's own 30 seconds;
- the test-set runner records a row only for a case that ran the way the case file says it should, so a model that was never asked
  (not signed in, a refused launcher) leaves no row that reads as a clean decline, and it prints nothing from the checkout's
  `review.json` that it has not cleaned;
- the report says the bound is met only when the test set has all 29 shipped cases and no run of any case ever approved wrongly;
- the labelling tool says that the engine's reason is the model's own words, which a commit message can steer.

It does not install the hook, and it does not redact the stored diffs (see Deferred work).

## Scope

- Increment A: `packages/workbench/action-review/hook/shadow_hook.py`, its tests, its `PINS` entry in the helper, and the spec's
  "As built (Increment D)" paragraph.
- Increment B: `packages/workbench/action-review/tools/run_testset.py`, its tests and the spec's "As built (Increment G)" paragraph.
- Increment C: `packages/workbench/action-review/tools/report.py`, its tests and the spec's "As built (Increment F)" paragraph.
- Increment D: `packages/workbench/action-review/tools/label.py`, its tests and the spec's "As built (Increment E)" paragraph.
- Every increment: the `Result` of this plan, and "The owner's steps" of the spec where a step changes.

## Non-goals

- The Medium 1 finding (a diff that the secret scan flagged is kept in `collected.jsonl`). Redacting it costs the owner the sight of
  the flagged line when labelling, which is the main reason for a `no_secret_lines` label; it is the owner's decision and is listed
  under Deferred work.
- Authenticating the four data files (Low 5, accepted by design: anything running as the owner can write them).
- Any change to the engine's helper, to the store's formats, to a hook that decides, or to a cutover.
- The tested security pass: it runs only when the owner asks, after this plan, with instructions that use the agent's own scratch
  directory.
- Installing, registering or running the hook, which stay the owner's.

## Assumptions and constraints

- The plan `2026-10-29-action-review-shadow-hook` is complete except for the owner's hand run; this plan changes the shipped hook and
  three tools after it. The owner has not installed anything, so no installed copy has to be upgraded.
- Editing a file of `packages/workbench/` makes the installer stop trusting the package until the owner runs `wb release-approvals`,
  and the project's command gate then refuses every command. So each increment is built and tested in a scratch clone, copied into
  the tree, released by the owner, verified, and committed (`package-edit-workflow` in the agent's notes; the same method as the
  earlier plan).
- The engine finds `wb` by name in the trusted entries of its own `PATH` (`wbkit/call.py`, `trusted_which("wb", boundary)`): absolute
  directories outside the project. The hook already requires the launcher to be an absolute executable file outside the command's
  directory.
- The bridge is given 20 seconds, the engine 25, the hook's registration 30; the hook waits 28 and then at most 2 more.
- The report is copied out of the checkout and cannot read the case file; the number of shipped cases is written into it and a test
  pins that number to the case file, as the runner pins the case file's hash.
- Tests are written first and seen to fail. Each tool and the hook is mutation-tested as in the earlier plan.

## Completion criteria

1. The `PATH` the hook gives the engine begins with the launcher's own directory, and a test shows the kit's `trusted_which("wb",
   ...)` finds the launcher with that `PATH`; a launcher not named `wb` is not run; the two waits add up to at most 29 seconds.
2. `run_testset.py` writes no row for a case whose engine run failed, was refused where the case file expects a verdict, or did not
   ask the model where the file expects it to, and names that case as not run; its summary says so; the model and effort it prints
   are cleaned.
3. `report.py` closes the cutover line if any run of any test case approved wrongly, and does not say the bound is met unless the test
   set holds all of the shipped cases; the number is pinned to the case file by a test.
4. `label.py` marks the engine's reason as the model's words, with a test.
5. The spec's "As built" paragraphs and "The owner's steps" say what changed, and name no behaviour that no longer holds.
6. `python3 -B -W error tests/run_all.py` passes, `wb check` and `wb run code-work check` report no problem, and every pin still
   matches (`test_actionreview_pins`).

## Increments

### Increment A — The hook finds the launcher, and waits less

**Outcome:** the engine started by the hook can find `wb`, which as built it could not.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/hook/shadow_hook.py`, `packages/workbench/action-review/tests/test_hook_shadow_hook.py`,
`PINS` in `packages/workbench/action-review/helper/action-review`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first. (a) The environment the fake `wb` records has a `PATH` whose first entry is the directory of the launcher it
   was started as, followed by the fixed entries, and no other variable beyond `HOME` and `LANG`. (b) With that recorded `PATH`
   patched into this process, `workbench.wbkit.call.trusted_which("wb", <the boundary of the command's directory>)` returns the fake
   launcher; this is the engine's own lookup, run on the hook's own environment. (c) A launcher whose file name is not `wb` is not
   run and is recorded as `failed`, because the engine looks for the name `wb`. (d) `WAIT_SECONDS` plus the second wait is at most
   29 and more than 25. Run them and see them fail.
2. In `shadow_hook.py`: `usable_launcher` also requires the file name `wb`; `run_engine` puts the launcher's directory first in
   `PATH`; `WAIT_SECONDS` becomes 27 and the second wait is a named constant of 2.
3. Add mutation checks: the directory not added, added last, the name check dropped, a wait over the bound.
4. Update the `PINS` entry for `hook/shadow_hook.py` and the spec ("As built (Increment D)": the `PATH`, the name `wb`, the waits;
   step 3 of "The owner's steps" says the launcher must be named `wb`).
**Verification:** the module's tests and the full suite pass; `test_actionreview_pins` passes; the mutations are caught.
**Evidence:** the one local commit, with the trailer `Plan: 2026-10-30-shadow-review-fixes#A`, and the shipped records of the release.

### Increment B — The runner records only what ran as the file says

**Outcome:** a test-set row means the case ran the way the case file expects; the rest are named as not run.
**Dependencies:** none (independent of A).
**Affected areas:** `packages/workbench/action-review/tools/run_testset.py`, `packages/workbench/action-review/tests/test_tools_run_testset.py`,
`docs/specs/action-review.md`.
**Steps:**
1. Write the tests first, with the fake `codex` of the existing tests. (a) With the fake in its failing mode, the two controls and the
   reviewer-directed case leave no row, appear under "not run" with the reason, and the exit status is 1. (b) A case the file expects
   to be decided by a check (exit 0) that the engine refuses (exit 1) leaves no row. (c) A case that expects the model to be asked
   and was not asked leaves no row. (d) A case the file expects to be refused (exit 1) and that is refused still leaves its
   `decline` row with `refused`. (e) A model or effort in the checkout's `review.json` that holds an escape sequence or a newline is
   printed cleaned, and a model that the engine's own pattern refuses ends the run before anything is sent with a one-line note.
   Run them and see them fail.
2. In `run_testset.py`: a case is recorded only when its exit equals the file's `expect.exit`, an engine failure is never a row, and
   a model case is recorded only when the model was asked; the others go to the not-run list with a reason; `model` and `effort` go
   through `plain()` and are checked against the same patterns the engine reads them by.
3. Mutation checks on the new conditions; update the spec ("As built (Increment G)": what is a row and what is not).
**Verification:** the module's tests and the full suite pass; the mutations are caught.
**Evidence:** the one local commit, with the trailer `Plan: 2026-10-30-shadow-review-fixes#B`, and the shipped records.

### Increment C — The report closes on any bad run and wants every case

**Outcome:** the cutover line cannot read "met" on a partial or contradicted test set.
**Dependencies:** B (a row now means a case ran as expected).
**Affected areas:** `packages/workbench/action-review/tools/report.py`, `packages/workbench/action-review/tests/test_tools_report.py`,
`docs/specs/action-review.md`.
**Steps:**
1. Write the tests first. (a) A case approved wrongly in an earlier run and declined in the latest closes the cutover line
   ("blocked") and the first line names it; today it only prints a count. (b) A test set with fewer cases than the shipped number
   reads "not yet (the test set has N of 29 cases)" even when every case is clean; a set of all 29 can read "met". (c) The number in
   `report.py` equals the number of cases in `tests/dangerous-cases.json`. (d) A test-set row for a case name that is not in the
   shipped file is counted apart and does not count toward the 29. Run them and see them fail.
2. In `report.py`: a false approve in any run blocks (the report says how to start again: delete `testset.jsonl` after changing the
   engine and run the test set again); a constant holds the shipped number of cases; the cutover line requires the full set; the
   "earlier runs" count becomes part of the alarm line.
3. The case names of the shipped file are not copied into the report; it counts distinct names and compares the count, and a test
   shows an extra name is reported. Mutation checks; update the spec ("As built (Increment F)", the limits paragraph).
**Verification:** the module's tests and the full suite pass; the mutations are caught.
**Evidence:** the one local commit, with the trailer `Plan: 2026-10-30-shadow-review-fixes#C`, and the shipped records.

### Increment D — The labelling tool says whose words the reason is

**Outcome:** the owner does not mistake the model's text for the engine's finding when judging.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/tools/label.py`, `packages/workbench/action-review/tests/test_tools_label.py`,
`docs/specs/action-review.md`, "The owner's steps".
**Steps:**
1. Write the tests first: the reason line is introduced as the model's words ("the model's reason, which the commit's own text may
   have steered:") and a reason is still cleaned; a command cut for length shows the number of characters left out beside its
   cut. Run them and see them fail.
2. Change the line in `show()`, mutation-check it, and update the spec ("As built (Increment E)").
3. Run the whole verification, update "The owner's steps" where steps A to C changed one, and ask the owner whether to run the tested
   security pass now (with the agent's own scratch directory).
**Verification:** the verification for the plan as a whole.
**Evidence:** the one local commit, with the trailer `Plan: 2026-10-30-shadow-review-fixes#D`, and the shipped records.

## Verification for the plan as a whole

From this repository's root, when every increment is done:

1. `python3 -B -W error tests/run_all.py`.
2. `python3 -m workbench check .` and `python3 -m workbench run code-work check`.
3. `git diff --check`.
4. `python3 -B -m unittest discover -s packages/workbench/action-review/tests -t packages/workbench/action-review/tests -p
   'test_actionreview_pins.py'`.

Not run by the agent: the hook against Claude Code, the real launcher with `action-review` installed, a real bridge and a real model.

## Risks and sensitive actions

- **A shipped file changes** (the hook), and the owner's registered entry would run it: nothing is registered yet, but the owner
  copies the file out after this plan, not before. The spec's steps say to copy from the approved commit.
- **Package edits** need the owner's `wb release-approvals` after each increment, four in all.
- **The report becomes stricter.** A single earlier false approve blocks until the owner starts the test set again; that is the
  intent, and the owner may veto it when approving this plan.
- **Security-relevant code** (a subprocess, the environment, untrusted text). Each increment is reviewed by the `reviewer` agent; the
  tested security pass is the owner's to ask for.
- **Outward-facing:** the runner's tests use a fake `codex`; no model is called.

## Review record

Empty until a review is asked for.

## Deferred work

- **Redacting stored diffs (Medium 1).** `collected.jsonl` keeps the whole `describe` object, so a diff that the secret scan flagged
  stays on disk in a file the assistant can read. The smallest correction is to drop the text facts (`diff`, `body`, `subject`,
  `trailers`) when `no_secret_lines` failed, either in the engine's `--collect` output or in the hook. It costs the owner the sight
  of the flagged line when labelling a secret decline. Until the owner decides, step 5 of "The owner's steps" (a user-level `Read`
  deny) and deleting `collected.jsonl` after labelling are the mitigation.
- The tested security pass over the hook, the store and the tools, with fake programs, hostile inputs and path-guard probes.
- Authenticating the data files, and a hook that decides, and the cutover (plan 5).

## Result

### Increment A

Built in a scratch clone at `6c0642a`, as in the earlier plan.

Changed: `packages/workbench/action-review/hook/shadow_hook.py`, `packages/workbench/action-review/tests/test_hook_shadow_hook.py`, the
`PINS` entry of `hook/shadow_hook.py` in `packages/workbench/action-review/helper/action-review`, and `docs/specs/action-review.md`
("As built (Increment D)" and step 3 of "The owner's steps").

Done: the `PATH` the hook gives the engine begins with the launcher's own directory, then `/usr/local/bin:/usr/bin:/bin`, so the
engine's lookup (`trusted_which("wb", ...)`) finds the launcher; the launcher's file name must be `wb` and its directory name must
not hold the path separator; the hook waits 27 seconds and then at most `SECOND_WAIT` (2), 29 in all. The environment given to the
engine is exactly `PATH`, `HOME` and `LANG`.

Verification as run in the scratch clone on 2026-10-30: the new tests failed before the change, among them a test that runs the
engine's own `trusted_which` on the environment the hook gave it and could not find the launcher (the fault, demonstrated); then the
48 tests of `test_hook_shadow_hook.py` pass under `-W error` and the full suite passes (6,290 tests in 13 roots). Thirty-one mutations
of the hook are each caught; three first survived or no longer matched the changed code and were closed (the planted-program test
now names its planted file `wb`, so it still proves the absolute-path check).

Review: the `reviewer` agent, one exchange, eight findings, none blocking.
- F1 (applied): the launcher's directory is first on the `PATH` of the engine and everything it starts; the spec now says it should
  hold nothing but `wb` and be writable by the owner alone.
- F3 (applied): the environment test is an exact comparison now, with a mutation for an extra variable.
- F7 (applied): a test that was nearly vacuous was replaced by one that plants a launcher under a fake `.git` ancestor and shows the
  engine's own lookup drops it though it is first on the `PATH`.
- F8 (applied): the spec explains the separator rule.
- F2 (recorded, not done): the hook refuses a launcher inside the command's own directory but not one in a repository above it
  (`<repo>/bin/wb` with the command in `<repo>/sub`). It predates this increment and needs the owner to name such a path with
  `--wb`; the engine's lookup would drop it. Closing it is more than this increment's steps allow and is for the owner to add.
- F4 (recorded, not done): the plan's Assumptions say "the hook waits 28"; the steps, the criterion and the code say 27 and 2. The
  approved text is not edited here.
- F5, F6 (no defect): the waits and the name and separator checks are right as built.

Then, on 2026-10-30: the four files were copied byte-for-byte into the real tree (`cmp` equal), the owner ran `wb release-approvals`
("wrote 13 approvals for 1 first-party packages"), and in the real tree `wb check .`, `wb run code-work check`,
`python3 -B -W error tests/run_all.py` (6,290 tests in 13 roots, OK) and `git diff --check` were clean. The release wrote two new
shipped package records (`b01a2ea3bdce…`, `b021ea3d9fbc…`), part of this commit, and named the two before them (`b5ed39948ae1`,
`b99368d22038`) as belonging to no release; they are still tracked, awaiting the owner's word.

Not done: the hook has not run against the real launcher, so the fix is shown by the engine's own lookup on the hook's environment
and not by a real review; that is the owner's hand run.

### Increment B

Built in a scratch clone at `f96fc89`, as for A.

Changed: `packages/workbench/action-review/tools/run_testset.py`, `packages/workbench/action-review/tests/test_tools_run_testset.py`,
`docs/specs/action-review.md` ("As built (Increment G)" and step 8 of "The owner's steps").

Done: a row is written only for a case that ran the way the case file says (`not_recorded`): the engine did not fail (exit 0 or 1;
any other code, a signal included, is a failure), it ended with the exit the file expects, and where the file expects the model to
be asked, the model was asked. Every other case, an exception included, leaves no row and is named under "not run" with its
reason; the exit status is 1. A refusal the file expects is still a `decline` row with `refused`. A model or effort in the
checkout's `review.json` that the engine would refuse (its own patterns; a value that is not text is refused too, not dropped)
ends the run, before anything is shown or sent, with one cleaned line on standard error and exit 2. After a partial run the tool
says to run the test set again before reading the report.

Verification as run in the scratch clone on 2026-10-30: the new tests failed before the change and pass after (38 tests of
`test_tools_run_testset.py` under `-W error`, about 50 s) and the full suite passes (6,301 tests in 13 roots). Forty-one mutations
of the tool are each caught; one first survived because the `ok` / `differs` test had become redundant once a recorded case always
has the file's exit, and it was simplified and retargeted.

Review: the `reviewer` agent, one exchange, six findings, none blocking.
- F3 (applied): `project_setting` silently dropped a non-text model or effort; it now keeps it and the setting check refuses it.
- F4 (applied): the closing line said "now run the report" even after a partial run; it says to run the test set again.
- F5 (applied): the owner's step 8 now says what exit 1 and a "not run" line mean.
- F6 (applied): unit tests of `not_recorded` for negative, `None` and other exit codes and a file entry with no `expect.exit`.
- F1 (recorded, not done): a refusal is recorded on the exit alone; the reason the file expects (`refusal_contains`) is not
  compared. A scratch project broken so that the engine refuses everything still records the seven expected refusals, but then no
  other case runs, and the summary and exit status show it.
- F2 (recorded, not done): a case that unexpectedly reached the model, or reached it twice, is recorded and shown ("the model was
  asked; the file expects the opposite") but not left out. Refusing to record it would go beyond the steps of this increment.
- The two patterns for the model and effort are copies of the engine's and are not pinned to them (recorded in the spec).

Then, on 2026-10-30: the three files were copied byte-for-byte into the real tree (`cmp` equal), the owner ran `wb release-approvals`
("wrote 13 approvals for 1 first-party packages"), and in the real tree `wb check .`, `wb run code-work check`,
`python3 -B -W error tests/run_all.py` (6,301 tests in 13 roots, OK) and `git diff --check` were clean. The release wrote two new
shipped package records (`dc7504aa9ea0…`, `e550e1f0bc85…`), part of this commit, and named four older ones (`b01a2ea3bdce`,
`b021ea3d9fbc`, `b5ed39948ae1`, `b99368d22038`) as belonging to no release; they are still tracked, awaiting the owner's word.

Not done: no real model has been asked.

### Increment C

Built in a scratch clone at `6a73d92`, as for A and B.

Changed: `packages/workbench/action-review/tools/report.py`, `packages/workbench/action-review/tests/test_tools_report.py`,
`docs/specs/action-review.md` ("As built (Increment F)" and step 9 of "The owner's steps").

Done: a false approve in **any run** of a test case counts, not only in the latest: the alarm line (the first line) names up to
five such cases and says how to start again (change the engine if it needs it, delete `testset.jsonl`, run the test set again), and
the cutover line says "blocked". The test-set line reads `cases N of 29, false approves A (in any run; L in the latest), false
declines D`. The cutover line is "met" only when the test set holds exactly 29 distinct case names: fewer reads "the test set has N
of 29 cases", more reads "more than the 29 shipped". `SHIPPED_TEST_CASES` is 29 and a test pins it to the number of cases in
`tests/dangerous-cases.json`. A case run many times counts once. The title and the docstring now say the report prints test case
names (the shipped synthetic ids, which the store's regex limits to 1 to 64 of `a-z`, `0-9`, `_` and `-`).

Verification as run in the scratch clone on 2026-10-30: the new tests failed before the change and pass after (52 tests of
`test_tools_report.py` under `-W error`) and the full suite passes (6,314 tests in 13 roots). Thirty-nine mutations of the report are
each caught; none survived (two older mutation entries no longer matched the changed code and were retargeted).

Review: the `reviewer` agent, one exchange, five findings, none blocking.
- F4 (applied): the printed title still said "counts, rule names and check names only"; it names test cases now, with a test.
- F5 (applied): tests for runs in any order, for one case name with an approve-expected and a decline-expected row, for an
  approve that was expected, and for a full test set without labels.
- F1, F2, F3 (recorded in the spec): the report counts names and does not know them, so any 29 names read as the full set; rows
  carry no engine hash, so a partial rerun after a change to the engine can leave a mix of old and new rows (a bad old run still
  blocks); and the report cannot check that `expected` is right. The first and third need rows written by hand; the second needs
  only a partial rerun.

Not done: nothing is collected yet, and no real model has been asked, so no real report has been read.

### Increment D

Built in a scratch clone at `02421c2`, as for A to C.

Changed: `packages/workbench/action-review/tools/label.py`, `packages/workbench/action-review/tests/test_tools_label.py`,
`docs/specs/action-review.md` ("As built (Increment E)", the status paragraph, and step 7 of "The owner's steps").

**A departure from the plan's quoted wording.** The plan's example line is "the model's reason, which the commit's own text may have
steered:". The line printed is "the reason (the model's own words when a model was asked, which the commit's own text may have
steered): ...". A decline by the engine's own checks (a fixed check, or a prompt too large for the bridge) carries the engine's fixed
text, not model output, and the collected row does not say whether the bridge was asked, so the tool cannot tell the two apart;
saying "the model's reason" outright would be false for those rows. The hedge is true for an approve (it can only come from a model
reply) and for both kinds of decline.

Done: the reason is introduced by that line and is still cleaned and cut by `visible()` (at 600 characters, with a count; the engine
limits it to 300 anyway); a command cut for length shows how many characters were left out on the command line itself (a test
guards it). The spec says that a model's reply can imitate the engine's fixed text, that the verdict and failed checks are the model's
too when it was asked, that a count of characters left out is of the escaped text, and step 7 tells the owner to judge from the
command and the facts and not from the reason.

Verification as run in the scratch clone on 2026-10-30: the new tests failed before the change and pass after (34 tests of
`test_tools_label.py` under `-W error`) and the full suite passes (6,317 tests in 13 roots). Thirty-seven mutations of the tool are
each caught (the thirty earlier ones and seven for this change).

Review: the `reviewer` agent, one exchange, five findings, none blocking; it confirmed the hedge against `code_decline`, `judge` and
`record()`.
- F1 (applied): the comment and the spec name the second fixed-text case and warn that a model's reply can imitate the fixed text.
- F3 (applied): the spec says the count of characters left out is of the escaped text.
- F4 (applied): the spec says the verdict and failed checks are the model's too when it was asked.
- F5 (applied): step 7 of the owner's steps is updated; steps 3, 8 and 9 were updated in A, B and C.
- F2 (no defect): the reason stays on one line and is cut with a count.

Then the three files were copied byte-for-byte into the real tree (`cmp` equal) and the owner ran `wb release-approvals` ("wrote 13
approvals for 1 first-party packages"). The release wrote two new shipped package records (`b0f147b2c4fb…`, `d875c43af91e…`), part of
this commit, and named eight older ones as belonging to no release (`0729b4e7ca1c`, `b01a2ea3bdce`, `b021ea3d9fbc`, `b5ed39948ae1`,
`b99368d22038`, `dc0ccd49870e`, `dc7504aa9ea0`, `e550e1f0bc85`); they are still tracked, awaiting the owner's word.

Verification of the plan as a whole, run in the real tree after the release at `02421c2` plus this increment's uncommitted changes:
`wb check .` and `wb run code-work check` report no problem (74 plans checked);
`python3 -B -W error tests/run_all.py` passes (6,317 tests in 13 roots, OK); `git diff --check` is clean;
`test_actionreview_pins.py` passes (17 tests). Completion criteria 1 to 6 are met by the increments A to D as recorded above.

Not run by the agent: the hook against Claude Code, the real launcher with `action-review` installed, a real bridge and a real
model. Medium 1 of the security review (diffs stored unredacted in `collected.jsonl`) stays deferred to the owner's decision.
