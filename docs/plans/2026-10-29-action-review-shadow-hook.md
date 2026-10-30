# Build the action-review shadow hook, the labelled set and the report

Status: Proposed
Created: 2026-10-29
Candidate: workbench-v1#action-review-engine
Specs: action-review, safe-git, module-boundary, module-contract, harness-modules, command-permissions

## Goal

Plan 4 of the five in `docs/specs/action-review.md` ("Proposed split into plans"). The engine exists for `commit` and `remove`
(plan `2026-10-26-action-review-engine`) and nothing calls it. After this plan the owner can start a shadow period: a thin hook in
the owner's own configuration runs the engine on each prompted command and records what it would have said, the owner labels the
recorded commands right or wrong, and a report counts false declines and false approves against those labels and against the
test set. Nothing the engine says takes effect during the shadow.

The spec's shadow ran the engine beside the approver, whose answer still decided. The approver was removed when the user-level
configuration was reset on 2026-10-29, so no program decides today and the owner's own prompt is what the engine is measured
against. The hook therefore answers nothing: the owner sees the normal prompt, and the label records whether the owner would have
approved. This changes "Accuracy and cutover" steps 3 and 4 of the spec, and Increment A records it there.

Done means: the hook, the labelling tool, the report and the real-bridge test-set runner exist in the
`action-review` module (the hook and its store shipped, the other three as maintainer measuring scripts), are tested on a scratch copy, and are described with the owner's installation steps; the engine hands the
collector the facts it needs; and the owner has seen one prompted command reach the installed hook and land in the log. Gathering
the labels, measuring, and cutover are the owner's time and plan 5.

## Scope

- Increment A: `docs/specs/action-review.md` (the hook contract, the data files, the labelling and the report; the departure from
  the spec's shadow), with the Claude hook format verified against the installed Claude Code and cited as a reference.
- Increment B: the engine's helper in `packages/workbench/action-review/helper/`, its contract section and its tests.
- Increments C and D: new shipped files `hook/store.py` and `hook/shadow_hook.py` in `packages/workbench/action-review/`, their
  entries in `ships` and the module's data-file pins, and their tests in `tests/`.
- Increments E to G: new measuring scripts in `packages/workbench/action-review/tools/` and their tests in `tests/`.
- Increment H: `docs/specs/action-review.md` ("As built", the owner's steps), `docs/specs/safe-git.md` only if its facts change,
  and the command table of `docs/development.md`.

## Non-goals

- Cutover, the removal of anything, and the repointing of paragraphs of the global configuration (plan 5).
- Any `allow` rule, any decision by the hook, and any change to what `DELEGABLE` or the mode setting allow. The hook answers
  nothing in this plan.
- The push rule and its checks, and `remote-runner describe`: the hook passes a push and a remote-job command through unreviewed
  and the report says so.
- The owner's personal bridge setting, and a bridge option for a scratch root with no project content.
- Writing or editing anything at the user level. The agent prepares the programs; the owner copies them and edits the settings.
- Changing the timeouts. They are revisited after about 30 shadow reviews.

## Assumptions and constraints

- The hook is the owner's: it lives in the owner's configuration, outside any project's reach
  (`2026-10-24-project-guarantees-a-floor`). `module-boundary.md` puts a script that something runs at use time in `ships` and a
  script for measuring in `tools/`. The hook is run by the harness, so the hook and the store it imports are shipped data files
  (`hook/`), each with a pin, not commands: the module declares no command for them, so `wb run` cannot start them. The labelling
  tool, the report and the test-set runner measure, so they stay in `tools/`, never installed, hashed and covered by the module's
  approval. The owner copies all of them from the installed or checked-out module to a directory outside every project after
  comparing their hashes with the module's; a program run from inside a project would be code that project could change.
- Standard library only, Python 3.11 or later (`docs/development.md`). The tools use the kit's safe file layer where it fits and no
  other import from the installer.
- A `PermissionRequest` hook sees only a command that raised a prompt. The module declarations ask for `safe-git remove`, but the
  accepted decision `2026-10-29-workbench-asks-for-remove-submit-and-fetch` leaves out an `ask` for `safe-git commit`. To collect
  commits during the shadow the owner adds a user-level `ask` for it; the owner's steps say so. Whether a hook fires on a
  project `ask` in an interactive session was observed once for a bare push (`global-config-inventory.md`); Increment A and the
  owner's check in Increment H establish it for the two spellings.
- The hook must call `wb run action-review review --log-row '<command>'` from the directory where the command will run, with the
  shell reading the command running with no alias and no start-up option, allow nothing, and keep a limit of 30 seconds
  (`action-review.md`, "The owner's steps").
- The data directory is `~/.config/project-workbench/action-review/`, a subdirectory of the guarded store, found from the
  account's home directory. No environment variable, option or file moves it
  (`2026-10-20-fixed-store-location`). It is outside every project, mode 0700, its files 0600. The tools write only below it and
  never to the store's `settings`, `projects/`, `packages/`, `cache/` or `bin/`. The owner decided this on 2026-10-29.
- The engine hands the collector the facts on a `--collect` flag, so the command is parsed once, by the engine. The owner
  decided this on 2026-10-29.
- The cutover bound, decided by the owner on 2026-10-29: at most 10% false declines among the labelled real commands, with at
  least 10 labelled commits and 10 labelled removals, and no false approve on the labels or the test set. The earlier clause
  "strictly below the approver's rate" is dropped because no approver runs. The 10% is provisional.
- The collected file holds command text and the engine's facts, which may hold diffs and secrets. It is never tracked, never inside
  a project, and no tool prints a fact in full unless the owner is labelling at a terminal.
- A change to the engine's helper, `hook/` or `tools/` changes the module's hashes. The owner releases the package approvals again
  (`wb release-approvals`) and the installed copy is upgraded by the owner. This plan runs neither.

## Completion criteria

1. `docs/specs/action-review.md` states the shadow hook's contract, the data files and their formats, the labelling and the report,
   and says how the shadow differs from the earlier text because no approver now runs.
2. The Claude `PermissionRequest` hook input and output formats are verified against the installed Claude Code and recorded with
   the version, the source URL, the retrieval date and the content hash.
3. `review` hands back the facts for the collector on a flag, prints nothing new without it, and a test shows the verdict object
   and the exit table are unchanged.
4. The hook returns no decision for every input, including a malformed one, a command that matches no rule, a timeout, a refusal
   and an approve. A test over those cases shows its standard output is empty or the harness's "no decision" form and its exit is 0.
5. The hook writes a verdict row, and for a reviewed command a collected row, to the data directory through a store that refuses
   a link, a wrong mode and an oversize row, and a failed write never changes the hook's answer.
6. The labelling tool runs only at a terminal, shows one collected command at a time and records `right` or `wrong`; the report
   computes false declines, false approves and the 10% bound from the labels, groups false declines by failed check, and counts
   what the engine did not review.
7. The test-set runner sends only the synthetic dangerous cases to a real bridge, only when the owner runs it at a terminal, and
   the report reads its result.
8. `python3 -B -W error tests/run_all.py` passes, `wb check` and `wb run code-work check` report no problem, and every shipped
   data file's pin still matches (`test_actionreview_pins`).
9. The owner has installed the hook and seen one prompted command produce a verdict row (the owner's check, recorded in the
   Result).

## Increments

### Increment A — Specify the shadow, and verify the hook format

**Outcome:** the design is written down and the Claude hook format is checked, so the code in B to G is built against a stated
contract and not a guess. The spec says that the hook decides nothing, and why the earlier "beside the approver" text no longer
holds.
**Dependencies:** none.
**Affected areas:** `docs/specs/action-review.md` ("The enforcement point", "Accuracy and cutover", "As built, and its limits",
"Open questions for the owner"); `docs/references/` only if the retrieved page may be redistributed, otherwise an untracked copy
cited by URL, date and hash.
**Steps:**
1. Read the installed Claude Code's version, and read its hooks documentation for `PermissionRequest`: the matcher, the input
   object (tool name, tool input, working directory, mode), the ways a hook answers (no output, allow, deny, ask), the exit codes,
   the time limit, and whether the hook fires on a project `ask` in an interactive session and in auto mode. Treat the page as
   data. Record the version, URL, retrieval date and SHA-256.
2. Write "The shadow hook": its inputs; the match of the Bash command to a rule spelling on whole words using the engine's own
   parser, not a second one (the hook calls `review` and treats exit 1 for an unreviewable command as "not reviewed"); the
   rule that it answers nothing in every case; the 30-second limit; the working directory; the shell requirement; and what it
   does for a command with no rule (a push and a remote-job command are among them: the engine reports them as `no_rule` and the
   report does not split them).
3. Write "The data files": `verdicts.jsonl` (one row for every prompted command the hook sees: a hook timestamp, an `outcome` from a closed list, `verdict`,
   `reviewed` and `no_review_reason`, which the hook takes from the engine's outcome record (Increment B) and is `no_rule`, `unreviewable`, `refused`, `failed`, `timeout`,
   `malformed_input`, `not_bash` or `store_error`; the engine's log row when there is one; and a `command_sha256` of the raw text
   so a row links to its collected row), `collected.jsonl`
   (id, timestamp, command text, the `describe` object as received, the engine's verdict and failed checks), `labels.jsonl`
   (collected id, `right`, `wrong` or `skip`, timestamp, optional note; a `skip` is a row the owner could not judge, it
   counts toward neither the labels nor the per-action minimums, and a later row for the same id replaces an earlier one), and `testset.jsonl` (the real-bridge run of the dangerous cases).
   Fix the fields, the size caps, the modes, the append rule and the data directory.
   Read the installer's store check and its tests, and record whether it tolerates an unknown subdirectory of the store. If it
   does not, stop and ask the owner: the fallback is a sibling directory, which changes the path above.
   Read `module-boundary.md` ("Module directories") and the verifier against the placement in the assumptions (the hook and the
   store shipped as pinned data files with no command, the measuring scripts in `tools/`), and stop and ask the owner if either
   refuses it.
4. Write "Labelling and the report": what `right` and `wrong` mean for an approve and for a decline (a false decline is a decline the
   owner would have approved; a false approve is an approve the owner would not have), the 10% bound with at least 10 labelled commits and 10 labelled removals, the
   group-by-check, the "not reviewed" count, and the test-set rule. State that the comparison with the approver cannot be made on
   the same commands, and what replaces it (the approver's old rate in "Evidence", as context only).
5. Edit the sentences of the spec that this changes ("The approver's answer still decides", the shadow step, the cutover condition
   "strictly below the approver's rate") and record the owner's three decisions of 2026-10-29: the data directory, the `--collect`
   flag, and the bound without an approver to compare against.
6. Stop at the owner before B begins.
**Verification:** `wb check`, `wb run code-work check`, `git diff --check`; the document and reference checks that `wb check` runs
pass; a reread against `docs/specs/trust-and-approval.md` and `docs/specs/harness-modules.md` shows no contradiction.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#A`; the hook format has its provenance line in the spec
(version, URL, retrieval date, hash).

### Increment B — The engine hands back the facts

**Outcome:** `wb run action-review review --collect` prints, besides the verdict, two more kinds of line on standard error: an
`outcome:` line on every invocation, and a `facts:` line carrying the `describe` object when `describe` ran. So the hook never
reruns `describe`, parses the command a second time or guesses why a command was not reviewed. Without the flag nothing changes.
**Dependencies:** A.
**Affected areas:** `packages/workbench/action-review/helper/action-review`, `module.json` only if the declaration needs it,
`packages/workbench/action-review/tests/`, the engine sections of `docs/specs/action-review.md`, the command row of
`docs/development.md`.
**Steps:**
1. Write the tests first: with `--collect` the last standard-error line begins `facts: ` and holds the canonical JSON of the
   `describe` object; it is absent without the flag and on every refusal and failure that happens before `describe` ran; the
   line is at most the object cap of `safe-git.md`; the verdict object, the exit table and the `log-row:` line are byte-equal to
   those of the same call without the flag; the two flags together are accepted in either order.
   Also test the `outcome:` line: with `--collect` it is present on every exit (a verdict, a refusal, a failure, a timeout, a
   usage error), it is one line of strict JSON of a fixed size, and its `reason` is one word of the closed list `reviewed`,
   `no_rule`, `unreviewable`, `refused`, `failed` or `timeout`, derived from the engine's own parse and exit path and from no
   second reading of the command; the engine cannot tell a push or a remote-job command from any other command with no rule, and
   the test shows both as `no_rule`. Without `--collect` the standard error is byte-equal to today's on every path.
2. Add the flag to the argument reader and print the lines after the `log-row:` line, so the hook's rule (the last line that begins
   `log-row: `) still holds, and a rule-error note still comes first. The `outcome:` line is the last line.
3. Run the mutation checks the earlier increments used on the new branch of code.
4. Update "The call" and "The verdict, the output and the log" of the spec.
**Verification:** the module's tests (`python3 -B -m unittest discover -s packages/workbench/action-review/tests -t
packages/workbench/action-review/tests` from the repository root) and the full suite pass; `test_actionreview_pins` passes.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#B`.

### Increment C — The store the tools share

**Outcome:** one small library, the shipped file `hook/store.py`, that creates the data directory and appends to and reads its files safely, so the hook,
the labelling tool and the report cannot differ in how they treat a link, a mode or a bad row.
**Dependencies:** A.
**Affected areas:** `packages/workbench/action-review/hook/store.py`, the module's `ships` list and its pin for the file,
`tests/test_hook_store.py` in the module.
**Steps:**
1. Write the tests first: the directory is created 0700 and a wider existing mode is refused; a file is created 0600; a path that
   is a link, or a file with a second hard link, is refused; an append is one `O_APPEND` write of one line under a lock; a row over
   the cap, a row with a field the format does not name, and a line that is not strict JSON are refused on write and skipped, with a
   count, on read; two writers do not interleave.
2. Write the library: `append(name, row)`, `read(name)` returning rows and a skipped count, the field tables for the four files, and
   the data-directory lookup from Increment A.
3. Run the mutation checks.
**Verification:** the module's tests and the full suite pass.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#C`.

### Increment D — The shadow hook

**Outcome:** the shipped file `hook/shadow_hook.py` is the program the owner registers as a `PermissionRequest` hook for `Bash`. It reviews and
records, and it answers nothing.
**Dependencies:** B, C.
**Affected areas:** `packages/workbench/action-review/hook/shadow_hook.py`, the module's `ships` list and its pin for the file,
`tests/test_hook_shadow_hook.py`.
**Steps:**
1. Write the tests first, with a fake `wb` on a controlled `PATH` entry and a fake bridge: for an approve, a decline, a refusal
   (exit 1), a failure (exit 2), a timeout, a malformed object, an approve with a non-empty `failed_checks`, a command with no rule,
   a push, a non-Bash tool, an oversize or malformed hook input and a closed data directory, the hook's standard output is empty
   (or the harness's form of "no decision") and its exit is 0; a reviewed command leaves one verdict row and one collected row; every other case leaves
   exactly one verdict row with `reviewed` false, the matching `no_review_reason` and no collected row (a case where the store
   itself cannot be written is noted on standard error and is the one case that leaves no row).
2. Write the hook: read the input within a bound; take the Bash command text and the working directory; call `wb` by an absolute
   path the owner sets at install, never from `PATH` or the project; run `review --log-row --collect` from the working directory
   with a 30-second limit and a clean environment; take the `log-row:` and `facts:` lines only from the last matching lines of
   standard error; write the rows through the store; note a failed write on standard error and go on.
3. Test that no code path writes standard output other than the no-decision form, by a test that replaces the output stream and
   fails on any unexpected write.
4. Run the mutation checks on the answer path: a change that returns an allow must fail a test.
**Verification:** the module's tests and the full suite pass; a run of the hook on a scratch copy of this repository, with the real
engine and a fake bridge, leaves the two rows and prints nothing.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#D`.

### Increment E — The labelling tool

**Outcome:** `tools/label.py` lists the collected commands that have no label and records the owner's judgment of each. It runs
only at a terminal.
**Dependencies:** C.
**Affected areas:** `packages/workbench/action-review/tools/label.py`, `tests/test_tools_label.py`.
**Steps:**
1. Write the tests first: it refuses unless standard input and output are both terminals (a pseudo-terminal test); it shows the
   command text, the engine's verdict and failed checks and a bounded, display-cleaned view of the facts; it records `right`,
   `wrong` or a skip, with an optional note; it never shows a fact the owner has not asked to see in full; a collected row that
   is already labelled is not shown again; an interrupt leaves no half row.
2. Write the tool. Control characters and terminal escape sequences in the command text and the facts are made visible and not
   passed to the terminal.
3. Run the mutation checks.
**Verification:** the module's tests and the full suite pass.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#E`.

### Increment F — The report

**Outcome:** `tools/report.py` reads the verdict, collected, label and test-set files and prints the counts that the cutover
condition uses, and says plainly what it could not count.
**Dependencies:** C, E.
**Affected areas:** `packages/workbench/action-review/tools/report.py`, `tests/test_tools_report.py`.
**Steps:**
1. Write the tests first, on built files: false declines, false approves and agreements over the labels; the false-decline rate
   against the 10% bound and the minimums of 10 labelled commits and 10 labelled removals (below either it prints "not enough
   labels" for that action, not a pass); false declines grouped by
   failed check; the count of prompted commands the engine did not review, by reason (no rule, which includes pushes and remote jobs, unreviewable,
   refusal, failure, timeout); unlabelled and skipped counts; any false approve on the labels or the test set is printed first and
   blocks the cutover line; the output holds no command text and no fact.
2. Write the report. It prints counts and check names only.
3. Run the mutation checks on the bound and the false-approve rule.
**Verification:** the module's tests and the full suite pass.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#F`.

### Increment G — The test-set runner

**Outcome:** `tools/run_testset.py` sends the 29 synthetic dangerous cases of `tests/dangerous-cases.json` through the real engine
and a real bridge, so the cutover condition's "no false approve on the test set" has evidence from a real model and not a fake.
**Dependencies:** C, F.
**Affected areas:** `packages/workbench/action-review/tools/run_testset.py`, `tests/test_tools_run_testset.py`.
**Steps:**
1. Write the tests first, with a fake bridge: it refuses unless at a terminal; it prints the number of cases and the bridge before
   it sends anything and waits for the owner's typed confirmation; it records the engine's verdict per case with the case's
   expected verdict and a mismatch flag; it never sends a case that is not in the shipped file, whose hash it checks; a case
   expected to decline that is approved is printed first.
2. Write the runner. It sends nothing from the owner's own commands: only the shipped synthetic cases, which holds no secret.
3. Run the mutation checks.
**Verification:** the module's tests and the full suite pass. The runner is not run against a real bridge by the agent; that is the
owner's, and sends content to a vendor.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#G`.

### Increment H — Record the build and the owner's steps

**Outcome:** the spec says what is built and what is not, the owner has exact steps to install the hook and start the shadow, and
the command table lists the new tools.
**Dependencies:** A to G.
**Affected areas:** `docs/specs/action-review.md` ("As built, and its limits", "The owner's steps", "Proposed split into plans"),
`docs/development.md`, `docs/roadmaps/workbench-v1.md` only if the owner says the direction changed.
**Steps:**
1. Reread the spec against the built tools and correct every departure, as the earlier engine plan's last increment did.
2. Write the owner's steps: copy the two shipped files and the three measuring scripts to a directory outside every project and check their hashes against
   the module's; register
   the hook with its absolute `wb` path and limit; add the user-level `ask` for `wb run safe-git commit` if commits are to be
   collected; run `release-approvals` and `upgrade` as the owner decides; label with `label.py`; read `report.py`; run
   `run_testset.py` once with the real bridge. State that the hook allows nothing and that removing its settings entry stops it.
3. Add the four tools to the command table of `docs/development.md` with their owner-run marks.
4. Ask the owner whether to run a security review over the hook, the store and the engine flag (they touch a subprocess, the
   filesystem, untrusted command text and a network boundary through the bridge). It runs only when the owner asks.
5. Run the whole verification below.
**Verification:** the verification for the plan as a whole.
**Evidence:** one local commit, `Plan: 2026-10-29-action-review-shadow-hook#H`. The owner's own check (completion criterion 9) is
recorded in the Result and is not a commit.

## Verification for the plan as a whole

From a trusted directory (this repository's root), when every increment is done:

1. `python3 -B -W error tests/run_all.py`.
2. `python3 -m workbench check .` and `python3 -m workbench run code-work check`.
3. `git diff --check`.
4. A run of the hook on a scratch copy with the real engine and a fake bridge: two rows, empty standard output.
5. The owner's installed hook has produced one verdict row for a prompted command (the owner's check).

Not run by the agent: the hook against Claude Code in a live session, any real bridge, `release-approvals` and `upgrade`.

## Risks and sensitive actions

- **The hook is a trust boundary at the user level.** A bug that returns an allow would approve commands that were meant to prompt.
  The plan answers nothing from the hook, tests every path for it, and mutation-tests the answer path. The owner reads the hook
  before registering it.
- **The collected file holds command text and diffs.** It lives outside every project at mode 0700 and 0600, and the report holds
  counts only. A vendor program that opens files in a project cannot find it. A secret in a diff is in that file until the owner
  deletes it.
- **Untrusted input.** The command text and the facts come from a repository or an assistant under review. The labelling tool makes
  control characters visible; the hook and the store bound every read and write.
- **Subprocess and path.** The hook starts `wb` from an absolute path the owner sets; a `wb` found by `PATH` or in the project would
  be code a project controls.
- **Outward-facing.** `run_testset.py` and every shadow review send content to a vendor through the bridge. The first sends only
  synthetic cases and only after the owner types a confirmation; the second is the shadow period itself and the owner starts it.
- **Package edits.** The helper, the shipped `hook/` files and the maintainer directory change the module's hashes; the owner releases and upgrades.
- **No second reviewer for the fixes of a security pass**, as in earlier plans, unless the owner asks for one.

## Review record

Plan review, before approval: Codex (`gpt-5.6-terra`) through the review engine, three rounds, five findings. Applied: the `skip`
label value (R1-F2), one verdict row for every prompted command with a closed list of no-review reasons (R2-F1), the hook and
store as shipped pinned files with the measuring scripts in `tools/` (R3-F1), and an `outcome:` line on every `--collect` run
(R3-F2). Rejected: R1-F1, because a user-level `ask` is an ordinary rule in the owner's own settings file. The plan was approved
on 2026-10-30 by the owner at the `ask` level.

Increment A, `reviewer` agent, one exchange, seven findings.
- F3 (blocking, applied): the acceptance criteria still promised the approver's counts; they now say the comparison cannot be
  made.
- F1 (applied): the spec says `store_error` was dropped from the plan's list because it could never appear in a row. Increment D
  follows the spec's list.
- F2 (applied): `collected.jsonl` gained `rule` and `command_sha256`, so the report can count per action.
- F4 (applied for the stale sentences in the engine and split sections; "The owner's steps" and "As built" are Increment H's).
- F5 (applied): the spec now says the owner chose `--collect` and defines the `facts:` and `outcome:` lines.
- F6 (applied): the spec says where each program comes from and which hash is compared.
- F7 (applied): the spec says a `Read` deny does not stop a shell `cat`.

## Deferred work

- Cutover, removing anything the engine replaces, and the repointing of paragraphs of the global configuration (plan 5).
- The push rule and checks, and `remote-runner describe` with its rules.
- The owner's personal bridge, model and effort setting, and a scratch-root option on the bridge.
- A revisit of the timeouts and the object cap after about 30 shadow reviews.
- A hook that decides (an allow for a delegated rule), which needs the cutover conditions and the owner's word.
- Labelling by someone other than the owner, and any sharing of the collected file.

## Result

### Increment A

Changed: `docs/specs/action-review.md` only (uncommitted until the owner says to commit).

Done: the new section "The shadow hook" (Claude format with provenance, the hook's behaviour, the collect lines, the data files,
placement of the programs, labelling and the report, the recorded limit that the harness does not deny reads of the store);
steps 3 to 5 and the bound of "Accuracy and cutover" amended with the departure marked; the acceptance criteria, the plan split and
the log location sentences corrected.

Facts established. Claude Code 2.1.314; hooks page retrieved 2026-10-30, 283,477 bytes, SHA-256
`b755d9c7c166ec77e36ee2388e3299dd149a9f160171b6e97e427be439f942f9` (untracked, cited by URL, date and hash). A `PermissionRequest`
hook fires only when a prompt is about to show; empty output with exit 0 is no decision; a failure does not block unless
`onFailure` is `block`, and then it denies; the default time limit is 600 seconds. `Store.ensure` checks only the store root and
its four directories, so the `action-review/` subdirectory is tolerated. The rendered settings deny edits to the store and not
reads.

Not established: whether the hook fires in auto mode when the classifier decides without a prompt, and whether it fires on the two
module spellings in an interactive session. Both are the owner's check in Increment H. The plan's step 3 lists a `store_error`
outcome that the spec drops; Increment D follows the spec.

Verification as run on 2026-10-30: `wb check .` and `wb run code-work check` report no problems; `git diff --check` clean. Nothing
else exists to run.

Not done: "The owner's steps", "As built" and the open-questions list, which Increment H rewrites.

### Increment B

Where the work is. Editing a file of `packages/workbench/` changes the module's hash, the installer then stops treating the package
as first-party, and the project's command gate stops knowing the `claude` harness: every Bash command is refused until the owner runs
`wb release-approvals`. That happened once, when a test file was first written into the tree (the owner removed it, and the gate
returned). So Increment B was built and tested in a scratch clone of the repository at `d87de04` (session scratchpad,
`wb-b/`), and its three changed files plus one new test file are copied into the real tree only when the owner is ready to release
the approvals. Until then the real tree holds nothing of B. The same will apply to Increments C and D, which add shipped files.

Changed (in the scratch clone): `packages/workbench/action-review/helper/action-review`,
`packages/workbench/action-review/tests/test_actionreview_collect.py` (new), `docs/specs/action-review.md`, `docs/development.md`.

Done: `review` accepts `--collect` and `--log-row` in either order. With `--collect` it prints a `facts:` line (the `describe` object
in canonical ASCII JSON, left out over 393,216 characters) when `describe` produced a valid object, and an `outcome:` line, always
last, with one reason: `reviewed`, `no_rule`, `unreviewable`, `refused`, `failed` or `timeout`. The reasons come from exception
kinds set where the engine already decides (`NoRule`, `DescribeTimeout`, `BridgeTimeout`); the bridge's own `timeout` error counts as
a timeout. A flag that repeats is read as the text, so the call without `--collect` reads what it always read.

Verification as run in the scratch clone on 2026-10-30: the new tests failed before the change for the right reasons (the flag was a
usage error; `MAX_FACTS_LINE` absent); after it the module's 480 tests pass (3 skipped) and the full suite `python3 -B -W error
tests/run_all.py` passes (6,099 tests in 13 roots). Twelve mutations of the new code were each caught by the new tests.

Review: the `reviewer` agent, one exchange, four findings.
- F1 (blocking, applied): a repeated `--log-row` without `--collect` had become a usage error where it was a command text; the
  parser now reads a repeated flag as the text, and two tests pin it.
- F2 (blocking, applied): a bridge that reports `error: timeout` itself, which is the normal timeout, was classed `failed`; it is
  `timeout` now, with a test for it and for a non-timeout bridge error.
- F3 (applied): the spec says a failed write after the verdict may repeat the `facts:` line, and how a hook reads it.
- F4 (applied): the spec says a `reviewed` outcome with no `facts:` line is a command the hook cannot collect. Increment D must
  treat it so.

Then, on 2026-10-30: the four files were copied byte-for-byte into the real tree (`cmp` equal), the owner ran `wb release-approvals`
("wrote 13 approvals for 1 first-party packages"; it warned that the shipped records `81627aea5dba` and `b0ad94d0ff0f` belong to no
release and are to be removed by hand, which was not done), and in the real tree `wb check .`, `wb run code-work check`,
`python3 -B -W error tests/run_all.py` (6,099 tests in 13 roots, OK) and `git diff --check` were clean. The two new shipped package
records (`10a1da2fc18a…`, `9ea0fd32c92b…`, each an `approval.json`) are part of the increment's commit.

Not done: the two stale shipped records are still tracked, awaiting the owner's word to delete them (the owner said to remove them
later on 2026-10-30, and they were removed in commit `71cd4fb`). No hook reads the new lines yet (Increment D).

### Increment C

**A departure from the plan's text, for the owner to accept.** The plan names the shipped file `hook/store.py`. The installer's
boundary test (`test_the_installer_and_its_tests_name_no_module_helper_harness_or_path`) refuses a module file whose name is the
name of a file of the installer, and `workbench/store.py` exists. The file is `hook/shadow_store.py`. The plan's later text that
says `store.py` (Scope, the Increment C and D steps) means this file. Nothing else about the increment changes.

Where the work is. Built in a scratch clone at `71cd4fb`, as for B; copied into the real tree and released by the owner afterwards
(see the end of this section).

Changed: `packages/workbench/action-review/hook/shadow_store.py` (new), `packages/workbench/action-review/tests/test_hook_store.py`
(new), `packages/workbench/action-review/module.json` (`ships`), `packages/workbench/action-review/helper/action-review` (a `PINS`
entry; the helper reads no file of `hook/`, so the entry is for the owner's comparison of a copy), `tests/test_actionreview_module.py`
(the expected `ships`), `docs/specs/action-review.md` (the placement paragraph and the rules the store enforces).

Done: `shadow_store.py` keeps the four files below `~/.config/project-workbench/action-review/`. It imports only the standard
library. It finds the directory from the home directory with no environment variable or option; makes the store root and the
directory mode 0700 and refuses any other mode, a link, another owner or a file in place of either; opens files with no-follow,
non-blocking opens and checks the descriptor (regular, owner, one link, no group or other access); appends one ASCII line of strict
JSON under a lock, with a short-write loop, a cut-back after a failed or interrupted write, and a new line first if a killed writer
left a fragment; refuses a row that does not fit its format or line cap; and on read skips and counts any line that does not fit,
including raw non-ASCII, duplicate keys, a number too large for a float and an unfinished last line. The formats are those of
"The data files", with the rules written into the spec after the review.

Verification as run in the scratch clone on 2026-10-30: the new tests failed before the file existed; then 46 tests of
`test_hook_store.py` pass, the module's tests pass, and the full suite `python3 -B -W error tests/run_all.py` passes (6,145 tests in
13 roots). Twenty-seven mutations of `shadow_store.py` are each caught by the tests; nine first survived and were closed with new
tests, and six more were added for the review's fixes. One run of the full suite first failed on the boundary test above, which is
how the name clash was found.

Review: the `reviewer` agent, one exchange, eight findings, none blocking.
- F1 (applied): a FIFO in place of a file would hold the opener; the opens are non-blocking and the descriptor check refuses it.
- F2 (applied): a killed writer could leave a torn line that swallowed the next good row; the next row now starts a new line.
  An interrupt inside the write is cut back too.
- F3 (applied): the docstring now says what is made (the store root, the directory, and `~/.config` only if missing).
- F4 (applied): the reader is as strict as the writer (ASCII only, no infinite number).
- F5 (applied): the labels line cap is 4 KiB so that a 300-character note outside the Basic Multilingual Plane fits.
- F6 (applied): the spec states the approve/decline rule and that the hook records an approve that names a failed check as `failed`.
- F7 (applied): the spec says a `reviewed` outcome with no `facts:` line is a verdict row with no collected row, counted by the report
  as reviewed but not collectable. Increment D follows this.
- F8: the rename above, recorded here for the owner's acceptance.

Then, on 2026-10-30: the six files were copied byte-for-byte into the real tree (`cmp` equal), the owner ran `wb release-approvals`
("wrote 13 approvals for 1 first-party packages"), and in the real tree `wb check .`, `wb run code-work check`,
`python3 -B -W error tests/run_all.py` (6,145 tests in 13 roots, OK) and `git diff --check` were clean. The release wrote two new
shipped package records (`334b92357c9b…`, `7bb3173b7a69…`), which are part of the increment's commit, and warned that the two records
of the release before it (`10a1da2fc18a`, `9ea0fd32c92b`) belong to no release; they are still tracked, awaiting the owner's word.

Not done: no hook uses the store yet (Increment D).
