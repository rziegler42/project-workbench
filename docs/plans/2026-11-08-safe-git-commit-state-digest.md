# Bind an approval of a commit to the state it reviewed: a state digest for `safe-git commit`

Status: Proposed
Created: 2026-11-08
Candidate: workbench-v1#action-review-engine
Specs: safe-git, action-review

## Goal

This is the prerequisite of the plan `2026-11-08-action-review-cutover-for-commit`, whose review found that an approval of a commit is bound to the text of the command and not to the state that the commit would record. The facts are taken when `safe-git describe commit` runs; a process that the agent started earlier could change a file before `safe-git commit` stages it, and a different diff would be committed under an approval of the earlier one. The spec lists this as an open limit ("Approval is not bound to the content that is committed", with the fix named as a change to another module). While the engine only recorded what it would say, the limit cost nothing. A hook that allows a commit would make it a hole.

After this plan:

- `safe-git describe commit` prints a `state_digest`: a SHA-256 of what the commit would record (the head and, for each named path, its mode and the id of the blob that `git add` would store, or a mark for a deletion). It prints nothing else new except `given_state_digest`, the value of `--state-digest` when the command line has one.
- `safe-git commit` takes an optional `--state-digest <64 hex>`. When it is given, the command stages as it does now, recomputes the digest from the **staged** entries, and refuses, unstaging as it does for any other refusal, if the digest differs from the one given. It checks again just before `git commit`, and after the commit it compares the blobs that the commit holds with the digest and says so loudly if they differ. Without the option nothing changes.
- The engine's commit rule accepts the flag, and a new fixed check, `state_digest_matches`, fails when a digest was given and differs from the one `describe` computes for the same arguments.
- The `commit-changes` skill has the agent run `describe` first with the arguments it will commit with, read the `state_digest`, and pass it to `commit`.

A digest in the command is data that the agent supplies, so what it proves is narrow and useful: the state at the moment the helper stages is the state the engine reviewed.

## Scope

- `packages/workbench/safe-git/helper/safe-git`: the digest, `describe commit`'s two facts, the option of `commit`, the two checks and the comparison after the commit.
- `packages/workbench/safe-git/tests/` (the commit and describe tests) and `docs/specs/safe-git.md` (the facts table and its caps, the options of `commit`, the codes, the order of the checks).
- `packages/workbench/safe-git/harness/neutral/skills/commit-changes/SKILL.md` and the test that pins its text.
- `packages/workbench/action-review/rules/safe-git-commit.json` (the flag and the check name), `packages/workbench/action-review/helper/action-review` (the check, the pin of the changed rule file), `packages/workbench/action-review/tests/`, and `docs/specs/action-review.md` (the checks table, the open limit).

## Non-goals

- A **strict** check, one that declines a command with no digest. My call, with the reason: the engine names every failing check in a decline, so a check that fails for every digest-less command would add `state_digest_matches` to the expected failed checks of every decline in the owner-reviewed test set of 29 cases and to every commit made before the skill changes. The presence of a digest is required where the allow is decided, by the hook, which reads the engine's own `facts:` line (`given_state_digest` present and equal to `state_digest`); the hook does not parse the command. This differs from the sentence in the cutover plan that says the engine's rule declines a command with no digest; increment E of this plan corrects that plan, with the owner's new approval, before its increment D (see Risks), and criterion 9 keeps this plan open until it is done.
- New cases in the shipped test set (`dangerous-cases.json`): the owner has reviewed those 29, and adding to them is for the owner's next review. The checks are tested by unit tests with a fake `describe` object and with the real helper.
- `--leave-other-staged`. `git commit --only` takes the work-tree content of the named paths at the moment it runs, so a digest of the index would not bind it. `--state-digest` together with `--leave-other-staged` is refused.
- Binding the message. The command carries the subject, the body and the trailers and the engine reviews the command as written.
- `remove`, a push, and any other action.
- The deciding hook, the installer, and the cutover: the cutover plan.
- A lock held across `git add` and `git commit`. There is none today and this plan does not add one (see Risks).

## Assumptions and constraints

- **The digest.** SHA-256 over the canonical JSON (keys sorted, no spaces, ASCII) of `{"format": 1, "head": <the 40-digit head, or "none">, "entries": [[<path>, <mode>, <blob id or null>], ...]}`, the entries sorted by path as bytes, one for each named path, with a blob id of `null` for a path whose deletion would be staged. It is written as 64 lowercase hex characters. The definition is recorded in the spec so that another implementation could reproduce it.
- **Both sides compute it from git's own view.** `describe` computes the blob ids read-only, from the bytes it already reads through its descriptor reader (`_read_work`, which does not follow a link), with `git hash-object --path=<path> --stdin`, which applies the conversion that `git add` applies and writes no object. `commit` reads the staged entries with `git ls-files -s -z -- <paths>`. A test shows that the two agree for a modified file, a new file, a deleted file, an executable file, an empty file, a non-ASCII path, a nested path, several paths given in any order, and a repository with `core.autocrlf` set to `true` and to `input`; where agreement cannot be shown for a configuration, the helper refuses `--state-digest` there with a code, and the spec says so.
- **The mode.** With `core.fileMode` true, which is what git reads when it is unset on a filesystem that keeps the executable bit, the mode of a regular file is `100755` when its work-tree file has an executable bit and `100644` otherwise, as `git add` stages it. With `core.fileMode` false, git ignores the work-tree bit and keeps the index's mode for a tracked path (and stages `100644` for a new one), and the safe-git spec already records that `describe` can differ from `git add` there. The digest does not try to follow that: where `core.fileMode` is not true, `describe` prints `state_digest` as null, `commit` refuses `--state-digest` with the code `state_digest_unsupported`, and the spec says so. A repository like that can still commit without a digest; it cannot be delegated. The tests cover `core.fileMode` true (executable and not, with a content change and with a mode-only change) and false (null and refusal).
- **Where it is checked.** After `git add` and the existing check that the staged set is exactly the named paths, and again at the existing "just before the commit" point; a difference is a refusal that unstages, as the other refusals do. After the commit, `verify_commit` compares the committed blobs with the digest; a difference there cannot undo a commit, so it is reported with the commit and "nothing was undone", as the other late findings are.
- **The residual window.** Between the last check and the moment `git commit` takes the index lock, a process with write access to `.git` could change the index. The window is milliseconds; the comparison after the commit detects it. The spec says so. Closing it needs a private index or a held lock and is deferred.
- **The facts.** `state_digest` is a string of 64 hex characters or null when `describe` could not compute it (a refused command); `given_state_digest` is a string or null. They are ASCII and well under the object cap. The facts are named in the spec's table, in the helper's list of fact names and in the engine's reading of the `describe` object, with the same caps and the same handling of a missing or mistyped fact as the others (a check that finds a fact missing or of the wrong type fails).
- **The check.** `state_digest_matches` passes when `given_state_digest` is null, passes when it equals `state_digest`, and fails when it is present and `state_digest` is null or different. It reads those two facts only. Its place in the order of checks is last, so that the expected `failed_checks` of every existing case is unchanged.
- **The agent's flow.** The skill's new step 6 runs `wb run safe-git describe commit` with exactly the arguments of the commit, as one command; the object it prints holds `state_digest`; the agent passes it to `commit` as `--state-digest <digest>`. If `describe` refuses, the agent stops and reports, as for any refusal. The skill's rule about the commands it may use gains the one read-only `describe`.
- **Order of increments.** The helper first, because nothing accepts a digest without it; the engine second, because it needs `describe` to print the facts; the skill last, because it tells the agent to pass the digest only after both accept it.
- Package files change in A, B and C: the release approvals, the removal of stale shipped records after the owner approves the list, the acknowledge, the upgrade and the rerender are the owner's steps after each. Nothing is pushed without the owner's word.
- Standard library only; `describe` writes nothing (a test compares the repository's bytes before and after).

## Completion criteria

1. `describe commit` prints `state_digest` and `given_state_digest`, added after the existing facts; every existing fact keeps its name, type, order and value, and the object of a refusal differs from today's only by the two added facts (`state_digest` null where it could not be computed, `given_state_digest` the value given or null); the tests that compare a whole `describe` object or the list of fact names are updated to that shape and to nothing else; a test shows that `describe` changes no byte of the repository.
2. `commit --state-digest <hex>` commits as before when the digest equals the staged state; it refuses with a named code, unstages, and makes no commit when it differs; it refuses a value that is not 64 lowercase hex characters (`usage`) and the option given twice, it refuses `--state-digest` with `--leave-other-staged`, and it refuses it, with its own code, in a repository whose configuration the digest does not support (`core.fileMode` not true). Without the option every existing test passes unchanged.
3. For each state in the list of the assumptions, the digest that `describe` prints equals the digest that `commit` recomputes from the staged entries; and a change of the head, of one byte of a named file, of a mode, of the set of paths or of a deletion changes it (a table test).
4. A file changed between `describe` and `commit` gives a refusal and no commit. An index entry changed between the first digest check and the second (the test's stand-in for `git` changes it while the cached whitespace check that runs between them is running) gives a refusal at the second check, with no commit and the paths unstaged. A commit whose blobs differ from the digest (the test's stand-in for `git commit` makes a different commit, so this runs after the second check and tests only the report) is reported after the fact with "nothing was undone". The window between the second check and the moment `git commit` takes the index lock is the one residual window and is not tested, because no test can place a change inside it.
5. The engine's rule accepts the flag as an optional value; `state_digest_matches` is in the table of checks and in the rule, last in order; a `describe` object with no digest passes it, with an equal one passes it, with a different or malformed one fails it, and a missing or mistyped fact fails it; the verdict shape, the exit table and the outcomes of the 29-case test set are unchanged (the shipped tests pass); the pin of the changed rule file is updated and `test_actionreview_pins` passes.
6. The skill says to run `describe` first with the arguments of the commit, to read the `state_digest` and to pass it; it allows the `describe` command; the test pins each sentence; a test shows that no sentence of the old flow now contradicts the new one.
7. `docs/specs/safe-git.md` and `docs/specs/action-review.md` state the digest and its definition, where it is checked, the residual window, and the strictness decision; the open limit "Approval is not bound to the content that is committed" says what is closed and what remains; `wb run code-work check` passes.
8. The owner has been asked whether to run a security review of this change, and the answer is in the Result. (Recommended: it changes what an approval means, and it touches a subprocess, the filesystem and the index.)
9. The two plans agree. The cutover plan `2026-11-08-action-review-cutover-for-commit` has been corrected where it differs from this one (increment E) and the owner has approved it again; until then this plan is not completed, and the cutover plan's increments D and F do not begin.

## Increments

### Increment A — The digest in the helper

**Outcome:** completion criteria 1 to 4 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/safe-git/helper/safe-git`, `packages/workbench/safe-git/tests/test_safegit_commit.py`, `test_safegit_describe_commit.py` and `support_git.py` if a helper is needed, `docs/specs/safe-git.md`.
**Steps:**
1. Read `parse_commit`, `check_commit`, `command_commit`, `verify_commit`, `describe_commit` and `_change_facts`, and the facts table and caps in the spec. Write the tests first in a scratch clone: the digest equality for each state of the assumptions on a scratch repository (the property test of criterion 3, with `core.fileMode` true and the unsupported refusal with it false), the refusals of criterion 2, the stale-digest refusal of criterion 4, an index change injected between the two checks (by a stand-in for `git` that acts while the cached whitespace check runs) and refused at the second, a different commit made by a stand-in for `git commit` and reported after the fact, and that `describe` changes nothing. See them fail.
2. Add `--state-digest` to the options of `commit`, the digest function used by both sides, the two new facts (named in `_COMMIT_FACTS` and in the caps), the two checks (after staging and just before the commit) and the comparison in `verify_commit`. Keep the codes of the other refusals, their order and their messages as they are, and add one code for a digest that differs.
3. Update `docs/specs/safe-git.md` (the options, the facts table, the codes, the definition of the digest, the residual window). Search the repository for another description of the options of `commit` (`docs/development.md`, the skill, the engine spec) and report one that disagrees.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** the safe-git module's tests, run as `python3 -I -B` through a runner in the scratch clone; a mutation pass over the digest (the head left out, the mode left out, the blob left out, a deletion treated as an empty file, the paths unsorted, the check dropped from either place, the comparison after the commit dropped); `wb run code-work check`. Not run: the whole repository suite, the engine's tests (increment B).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-safe-git-commit-state-digest#A`.

### Increment B — The engine checks a digest that is given

**Outcome:** completion criterion 5 is true.
**Dependencies:** A (released, so that `describe` prints the facts).
**Affected areas:** `packages/workbench/action-review/rules/safe-git-commit.json`, `packages/workbench/action-review/helper/action-review` (the check and the pin of the rule file), `packages/workbench/action-review/tests/`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first in a scratch clone, with a fake `describe` object and with the real helper: absent, equal, different, malformed, null digest on a refusal, a missing fact and a mistyped fact; the order of the checks and the shape of the verdict; and that the shipped test set still reads its 29 cases with the outcomes they have now. See them fail.
2. Add the flag to the rule and the check to the helper's table, last in the list; update the pin of the rule file; update the spec's checks table and open limit.
3. Run the verification below and ask the `reviewer` for a read.
**Verification:** the module's rule, bridge, module, pin and check tests and the test that reads the shipped test set, as `python3 -I -B`; `wb run code-work check`. The test-set runner against a real model is not run.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-safe-git-commit-state-digest#B`.

### Increment C — The agent passes the digest

**Outcome:** completion criterion 6 is true.
**Dependencies:** A and B, released and upgraded.
**Affected areas:** `packages/workbench/safe-git/harness/neutral/skills/commit-changes/SKILL.md`, the test that pins the skill, the rendering and drift tests that read every skill.
**Steps:**
1. Write the test first: the new step and the changed rule are pinned by phrase; the old text that says to run `commit` as the only command is gone. See it fail.
2. Reword the skill: a step between the subject and the commit that runs `describe`, reads `state_digest` and passes it; the rule on the commands the skill may use names `describe`. Say what to do if `describe` or `commit` refuses on the digest: stop, report, and run `describe` again only if the owner says so.
3. Run the verification below and ask the `reviewer` for a read.
**Verification:** the safe-git module tests, `tests.test_rendering`, `tests.test_permissions_drift`, `tests.test_rerender`; `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-safe-git-commit-state-digest#C`.

### Increment D — A real run, and the specs as built

**Outcome:** completion criteria 7 and 8 are true.
**Dependencies:** A, B and C, released, upgraded and rerendered by the owner.
**Affected areas:** `docs/specs/safe-git.md`, `docs/specs/action-review.md`, this plan's Result.
**Steps:**
1. In a scratch repository, through the installed launcher, run `describe`, change a named file, and run `commit` with the digest: it refuses and nothing is committed. Run `describe` and `commit` with no change: it commits. Record both with the commit and the version.
2. Mark the specs as built: the order of the checks, the two facts, the digest's definition, the strictness decision, the residual window, and what the cutover plan reads from the facts.
3. Ask the owner once whether to run a security review of the change; it runs only on the owner's word.
**Verification:** the two runs as the agent made them; the spec check.
**Evidence:** the Result of the plan, and the one local commit that records it, with the trailer `Plan: 2026-11-08-safe-git-commit-state-digest#D`.

### Increment E — Make the cutover plan say what this plan builds

**Outcome:** completion criterion 9 is true.
**Dependencies:** none for the text; it must be done before the cutover plan's increment D begins, and the owner's approval of the corrected plan is the owner's act.
**Affected areas:** `docs/plans/2026-11-08-action-review-cutover-for-commit.md` (its approved text, which is why the owner must approve it again), and its Result.
**Steps:**
1. Show the owner the sentences of the cutover plan that differ from this plan, and the corrected text, before editing: (a) its Goal says the digest is recomputed "inside its change lock"; `safe-git commit` has no lock, and the check is made after staging, just before `git commit`, and again after the commit; (b) its prerequisite bullet and its criterion 4 say that the engine's rule declines a command with no digest; this plan builds a check that fails only when a digest is given and differs, and the hook is what requires the digest, by reading `given_state_digest` and `state_digest` in the engine's `facts:` line (not by parsing the command); (c) the test list of its increment D, and its risk about the worktree, say the same; (d) it says `--leave-other-staged` is untouched, while a digest is refused with it, so the delegated flow commits without other staged paths.
2. On the owner's word, edit those sentences and nothing else, run `wb plan-status <plan> --digest`, show what it prints, and run `wb approve-plan <plan> --digest <digest>` for the owner to confirm. If the owner prefers a **strict** engine check instead, this plan is revised to that and re-approved, with the ripple on the 29-case test set that its Non-goals describe, and this increment changes the cutover plan not at all.
3. Record what was decided in the Result of both plans.
**Verification:** `wb plan-status` reads `approved` for the cutover plan after the owner's approval; `wb run code-work check`.
**Evidence:** the one local commit of the corrected cutover plan, with the trailer `Plan: 2026-11-08-safe-git-commit-state-digest#E`.

## Verification for the plan as a whole

The recorded verification of each increment stands. Whether agents in other projects pass the digest is for the next sessions and the report to show; the plan does not claim it.

## Risks and sensitive actions

- **This changes what an approval means and touches a subprocess, the filesystem and the index.** `safe-git commit` runs in every project that has the module. The option is optional and the behaviour without it is unchanged, which the existing tests pin; the new path is exercised only when a digest is given. A security review is recommended and runs only on the owner's word (criterion 8).
- **There is no lock around the commit.** The cutover plan speaks of checking the digest "inside the command's own lock", following the accepted decision for the owner-run keys. `safe-git commit` has no such lock of its own and relies on git's index lock; this plan checks after staging and again just before `git commit`, and reports a difference after the commit. Increment E corrects that plan's sentences, and the owner approves it again, before its increment D; its other text stands.
- **The digest is supplied by the agent.** A hostile agent can compute a digest of a state it later changes; the check at stage time refuses that. It can also give a digest and then leave the state alone, which is the honest case. It can omit the digest, which the engine passes (non-strict) and the hook, in the cutover plan, does not allow.
- **Repositories with conversions.** `core.autocrlf` and `core.eol` change the stored blob. A test per setting shows agreement or a refusal; a configuration that was not tested is not claimed.
- **Agents that follow the old skill text** (a session started before the upgrade) commit without a digest. That is the old, working behaviour; the engine passes it; the hook will not allow it.
- A package file changes in A, B and C: the release approvals, the stale-record removal, the acknowledge, the upgrade and the rerender are the owner's. Nothing is pushed without the owner's word.
- No network, no credential, no new file written outside the repository by the helper; `describe` writes nothing and `hash-object` is run without `-w`.

## Review record

Codex, plan review, 3 rounds of 3 (the bound); not converged: round 3 still had one major finding, which was applied and not read by a later round. Models: `gpt-5.6-terra` for rounds 1 and 2, `gpt-6.1-sol` for round 3.

- Applied (round 1, major): criterion 1 required the two new facts on a refused `describe` object and also that the whole refusal object be unchanged, which cannot both hold. It now says that every existing fact keeps its name, type, order and value, the two new ones are added after them, a refusal differs from today's only by those two, and the tests that compare a whole object or the list of fact names are updated to that shape and nothing else.
- Applied (round 1, major): how the mode is derived was not defined, and the safe-git spec records that `core.fileMode=false` makes `describe` differ from `git add`. The digest now supports only `core.fileMode` true, where the mode is the work-tree executable bit; with it false `describe` prints `state_digest` as null and `commit` refuses `--state-digest` with its own code (`state_digest_unsupported`), and the tests cover both settings (an executable change with content, a mode-only change, and the refusal).
- Applied (round 2, major): the plan named a conflict with the approved cutover plan (a non-strict check against its sentence that the engine declines a command with no digest) and left nobody responsible for resolving it. New increment E corrects the cutover plan's sentences with the owner's new approval of it (and states the strict alternative with its cost: the ripple on the 29-case test set), and new criterion 9 keeps this plan open until the two plans agree and the cutover plan's increments D and F wait for it.
- Applied (round 3, major): a stand-in for `git commit` acts after the second digest check, so the test could not show that the second check refuses. Criterion 4 and increment A step 1 now inject the index change while the cached whitespace check runs between the two checks (refusal, no commit, paths unstaged), and use the `git commit` stand-in only for the report after the fact; the window after the second check is stated as untestable.
- Not read by a later round: the round 3 fix, because the bound was reached. It is a correction to the wording of a test and does not change the design.
- Left for the owner: whether to extend the review for a fourth round (an owner-run `extend`), or to approve the plan as it stands; and the decision on the strict or the non-strict check, which increment E makes explicit.

## Deferred work

- A **strict** check, and the cases of the digest in the owner-reviewed test set, at the owner's next review of that set.
- A private index or a held lock around `git add` and `git commit`, to close the milliseconds of the residual window.
- `--leave-other-staged` with a digest.
- The same binding for `remove` (the preview and its confirmation already bind the list), and for a push when a rule for it exists.
- Putting the message into the digest, if a case is found where the command text is not the whole of what is committed.

## Result

**Increment A (2026-11-08), done in a scratch clone at commit `efe0bd0`; the specs are edited in the live tree; the package files are not yet copied, released or committed.**

- Built: in `packages/workbench/safe-git/helper/safe-git`, `state_digest(head, entries)` (the canonical JSON and SHA-256 of the plan, format 1, `"none"` for a branch with no commit, entries sorted by the bytes of the path, `null` and `null` for a deletion); `describe commit` prints `state_digest` and `given_state_digest` after `diff`, worked out from the bytes it already reads (SHA-1 blob ids computed in Python, nothing written); `commit --state-digest <64 hex>` reads the staged entries with `git ls-files -s -z` and checks after staging and the exact-set check (before the cached whitespace check) and again just before `git commit`, refusing with the code `state_changed` and unstaging; `verify_commit` compares the committed blobs, read with `git ls-tree -r -z`, with the digest and reports a difference with "nothing was undone". Refusals: a value that is not 64 lowercase hex (`usage`), the option given twice (`usage`), with `--leave-other-staged` (`usage`), and in a repository whose object names are not SHA-1 or whose `core.fileMode` is not true (`state_digest_unsupported`, by `describe` as an error and by `commit`). Three new read-only git shapes (`ls-tree -r -z HEAD --`, `rev-parse --show-object-format`, and `check-attr` of `text eol crlf`).
- No digest is offered (`state_digest` null, `describe` still `ok`) when a named file is over 262,144 bytes or not a regular file; when a named file holds a carriage return and `git add` could convert it (`core.autocrlf` on, or a `text`, `eol` or `crlf` attribute set to a value); when `--leave-other-staged` is given; and when a named path has nothing on either side. Two cases are known where a digest is offered and `commit` refuses it (the safe direction), recorded in the spec as from a reading of git and not run: `core.symlinks` false with a symlink replaced by a file, and a SHA-256 repository under a git too old to name its object format.
- **A deviation from the plan, accepted by the owner ("Go with your recommendation").** The plan said `describe` would compute the blob ids with `git hash-object --path --stdin`. The helper computes them in Python and offers no digest where a carriage return meets a possible conversion. It needs no new subprocess that feeds bytes to git and writes no object; the cost is that a file with a carriage return, in a repository with `core.autocrlf` or a `text`/`eol` attribute, cannot be delegated. The usage text of `commit` also changed, to show `--state-digest`; the plan said to keep messages as they are, and the usage string has to show the option.
- Tests (all in the scratch clone): `test_safegit_digest.py`, 43 tests, written first and failing for the missing digest before the code (the facts and their order; digest equality between `describe` and `commit` for a modified, new, deleted, executable, mode-only, empty, non-ASCII, nested, multi-path, intent-to-add, carriage-return, unborn-branch state; each input changes the digest and the message does not; the refusals; a stale digest; the first check before the whitespace check; a change injected between the two checks refused at the second, with a control that the same stand-in lets a commit with no digest through; a different commit reported after the fact; `core.fileMode` false, no SHA-1, `text=auto`, `core.autocrlf`, a large file; the listing reader on malformed index and tree listings; a raced irregular file), and one-line edits to three existing tests (the list of fact names in two, the allowed git commands in one).
- Verification as run: the whole safe-git suite in the clone, 690 tests, all passing on the final files; a mutation pass of 23 mutants of the digest (the head, the mode or the blob left out, unsorted paths, a wrong blob header, a deletion digested as an empty file, either check or the comparison after the commit dropped, the check always passing, a wrong form accepted, `--leave-other-staged` accepted, `core.fileMode` false or a non-SHA-1 repository supported, a conversion never possible, a carriage return never noted, a large or irregular file digested, the given digest not reported, the unsupported refusal dropped, a conflict stage accepted, a digest offered with `--leave-other-staged` or for a path with nothing on either side) killed all 23; the first pass left two survivors (the irregular-path and conflict-stage branches, reachable only in a race), closed by tests of the listing reader and of a raced file; `wb run code-work check` passes. `tests.test_boundary` has two failures that are not this change: they fail identically on the unchanged live tree (`test_the_exempt_files_are_the_two_the_decision_names_and_each_one_needs_it` and `test_the_installer_and_its_tests_name_no_module_helper_harness_or_path`, the second naming `tests/test_base_guidance.py:87`); they are reported to the owner. Not run: the whole repository suite, the engine's tests (increment B).
- Review: the `reviewer` agent, one exchange, no blocking finding. It read the digest against the staging step for every case the helper can reach (a path HEAD does not hold, an intent-to-add path, an unchanged path, a deletion, a mode change, `expected-head none`, a path given twice), found the soundness property to hold (any difference between what `describe` hashed and what git stored becomes a refusal and never a pass), found the two checks at the points the plan says with no early return, and the new git shapes as narrow as the others. Applied: no digest is offered with `--leave-other-staged` or for a path with nothing on either side (it had printed a digest that `commit` refuses); the two offered-and-refused cases are in the spec; a vacuous assertion and a stray comma were removed; tests for an intent-to-add path were added. Not applied: tests for `core.symlinks` false and for the executable bit under another umask (the plan's list for criterion 3 does not ask for them; the first rests on the reviewer's recollection of git), and a change to the usage text back to the old one. The reviewer ran nothing.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/sd_install_files.py`, five files, one of them new, only if their hashes are those recorded), the release approvals, the removal of the stale records after you approve the list, then "commit a"; after the commit the acknowledge, the upgrade and the rerender. Increment B (the engine) follows, and then C (the skill), E (correcting the cutover plan) and D (the real run); the plan asks the owner once, after the build, whether to run a security review (increment D).
