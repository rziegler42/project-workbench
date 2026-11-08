# Let the action-review hook approve a commit, when the owner sets the commit key to `delegated`

Status: Proposed
Created: 2026-11-08
Candidate: workbench-v1#action-review-engine
Specs: action-review, command-permissions, safe-git, module-contract

## Goal

Plan 5 of `docs/specs/action-review.md` ("Proposed split into plans"), narrowed to the one action where a mistake costs least. After this plan the owner can set the key `wb run safe-git commit` to `delegated` in a project, and then, for a commit the owner's prompt would otherwise ask about, the action-review hook may answer `allow` when the engine has reviewed the exact command and approved it. Every other outcome leaves the owner's prompt as it is: a decline, a command the engine cannot review, no rule, a timeout, a failed bridge, a failed hook, a malformed answer, a project whose key is not `delegated`. The hook never answers `deny`.

Nothing changes until the owner sets that key. Building this plan alters no behaviour of any project: the key's default stays as it is today, the shipped hook with the key unset answers nothing as it does now, and the owner's word to cut over is the act of setting the key, in one project, after seeing the report. The plan builds the means, the evidence of how the harness behaves, a way to see what the hook let through, and a way back; it does not cut over.

The approval is bound to the state it reviewed. The hook allows only a command that carries a digest of the state the commit would record, which the engine's own `describe` reproduces at review time and which `safe-git commit` recomputes inside its change lock before it commits; a file changed between the review and the commit makes the digests differ and the commit is refused. This is what decision 1 of the accepted record means by `delegated` offering "the same check of that digest inside the command's own lock" as `ask`, and it closes the open limit that the spec states ("Approval is not bound to the content that is committed"). `safe-git commit` has no such digest today, so the digest is a prerequisite plan (see Dependencies) and not part of this one.

This follows the accepted decision `2026-11-03-delegated-for-an-action-key-and-named-risk-profiles`: the owner's levels table is the switch (a separate mechanism outside the levels was rejected there), a decline waits for the owner, a failure is a decline, and the hook is registered in the owner's user-level configuration and reads the table. Where this plan makes a choice that the decision and the spec leave open, the choice is marked **(my call)** so that the owner can overrule it at review.

## Scope

- `docs/specs/action-review.md`: the evidence of increment A, the hook that decides ("The enforcement point", "The shadow hook"), the report's new lines, and the status of "Accuracy and cutover" step 5.
- The installer, for an action key at `delegated` (increments B and C): `workbench/declarations.py` (what `verify` accepts in a module's `levels`), `workbench/levels.py` (the registry of what a key offers; `settings.py` imports it as `keyset`), `workbench/rendering.py` (what the level renders), `workbench/settings.py`, `workbench/doctor.py`, with their tests, and `docs/specs/command-permissions.md` ("Which levels a key offers", "Decided, not built: `delegated` for an action key").
- `packages/workbench/safe-git/module.json`: the declaration that `commit` offers `delegated`, and nothing for `remove`.
- `packages/workbench/action-review/hook/shadow_hook.py`, its store and report (`tools/report.py`), and their tests: the deciding form, the log fields, the report lines. Registration of the hook stays the owner's.
- A short owner runbook in the spec: how to turn it on in one project, how to see what it allowed, how to turn it off.

## Non-goals

- Cutting over. The plan ends with the means and with a trial that the owner starts or does not start.
- `remove`. It stays at `block` and `none` **(my call)**: its key is in the `governs` class, the owner's label of 2026-11-05 records a preference for a human look at approval records, and a removal that deletes an untracked file cannot be undone. A later plan, on its own evidence.
- A push, a remote job, and every action without a rule. The engine has no rule for them (313 of 590 prompts on 2026-11-08 were not reviewed).
- The `plan approval` key and its converged-review gate; the other owner-run keys.
- A hook answer of `deny`, in any case.
- Changing the bound (10% false declines, 10 labelled commits and 10 labelled removals, no false approve), the labels, the engine's checks or its rubric.
- Registering the hook, copying its files to the owner's directory, editing the user-level settings: the owner's steps.

## Assumptions and constraints

- **Prerequisite plan, not drafted yet and first in order: the state digest of `safe-git commit`.** The plan to be written gives `safe-git describe commit` a digest of what the commit would record (the head, the requested paths with the content of each, the subject, the body and the trailers), gives `safe-git commit` a `--state-digest` argument that it recomputes inside its lock and refuses on a difference, adds a fixed check to the commit rule so that a command with no digest, or with one that the engine's own `describe` does not reproduce, is declined, and changes the `commit-changes` skill so that the agent runs `describe` first and passes the digest. It touches another module's helper and the engine's rule, so it has its own review and security pass. Increments D and F of this plan depend on it being completed; if the owner decides instead to accept the open limit of the spec, that is a record of its own and this plan is revised and approved again first. Increments A, B and C do not depend on it.
- **The cutover bound is a precondition, and the plan checks it.** The bound in `docs/specs/action-review.md` ("Accuracy and cutover") and in decision 9 of the accepted record is unchanged: at most 10% false declines among the labelled real commands, at least 10 labelled commits and 10 labelled removals, no false approve on the labels or the test set, and the owner's word. The test set is the author's 29 cases and the spec says the owner reviews and corrects it; whether the owner has done so is not recorded in this repository. The plan stops and tells the owner when the report's cutover line does not say the bound is met, and also when the owner has not said that the test set was reviewed (see criterion 9).
- The unknowns come first. The spec records that it is not known whether the harness shows the permission prompt while a `PermissionRequest` hook runs, whether an `allow` from the hook skips the prompt as the documentation says, and whether the hook fires in auto mode; decision 2 of the accepted record requires a test on a copy before any hook that decides is built. Increment A is that test and nothing is built on a guess: if the harness holds the prompt until the hook returns, the owner may see a wait of up to the hook's time limit (30 seconds) on every prompted commit while the key is `delegated`, and a record says so before increment D starts.
- A project's table decides **(my call, and the consequence of the decision)**. The hook runs for every project of the account. It learns the level by asking the installer, read-only (`wb settings` from the hook's `cwd`, a command that changes nothing), and decides only where that project's key reads `delegated`. The default of the key is not `delegated`, so a project the owner has not set, `knowledge-base` included, gets no decision. A reading that fails or cannot be parsed is no decision.
- The hook decides only on a strict result **(my call)**: the engine's `outcome:` line says `reviewed`, agrees with the exit code, and the verdict object is whole with `approve` and no failed check (the checks the shadow hook already makes). It answers `allow` once, with no `updatedInput`, no suggestions and no rule written. It writes its verdict row first, as the shadow does, and a failed write does not change the answer in either direction **(my call: the spec's decision that the log is a record and not a gate stands)**.
- The time limits stay as the spec has them (20 seconds for the bridge, 25 for the engine, 30 for the hook) until increment A shows what the owner sees; the entry sets no `onFailure`, so a failure of the hook is no decision.
- The installer renders the level **(my call, to be confirmed in increment B step 1)**: for an action key at `delegated` the project's permissions file gets an `ask` rule, so that the prompt exists whether or not the owner's user-level rule does, and the owner's prompt is the fall-back; the key reads `delegated` for `wb settings` and `wb doctor`, which says that the bridge's approval depends on a hook it cannot see. `approve-plan` keeps its present rendering (a `deny` at `delegated`, because its gate is another command).
- `verify` lifts its refusal of `delegated` only for a command that gives a `describe` and a rule for the same action, as the accepted decision says; `safe-git` declares it for `commit` and not for `remove`.
- The installer's tests are many (6,283 in 13 roots on 2026-10-30) and the change reaches the registry, `verify`, rendering and the settings, so increments B and C run the whole suite in a scratch clone and tell the owner what could break outside the tested area before they do.
- Package files change in B, C, D and E: the release approvals, the removal of stale shipped records after the owner approves the list, the acknowledge, the upgrade and the rerender are the owner's steps after each. The hook and the report are copied to the owner's directory by the owner's script, as before. Nothing is pushed without the owner's word.
- Standard library only; the hook starts no program but `wb` (to read the table) and the engine's `wb run`, as now.

## Completion criteria

1. The spec records, with provenance (the Claude Code version, what was run on a copy, the owner's observation and its date), what the harness does with a `PermissionRequest` hook that sleeps, that answers `allow`, that answers nothing and that fails, whether the prompt is shown while the hook runs, and whether the hook fires in the owner's mode.
2. A module declaration may offer `delegated` for an agent-run action argument that has a `describe` and a rule; `verify` refuses it for any other argument, still refuses it for an owner-run argument, and refuses an unknown level. `safe-git` offers it for `commit` only.
3. The key `wb run safe-git commit` offers `block`, `delegated` and `none`; its default does not change; the settings, `wb settings`, `wb doctor`, the rendering and the effective level read it as the decision says, a project whose key is not `delegated` renders and reads as before, and the whole installer suite passes apart from any failure the unchanged tree already has.
4. With the key at `delegated`, a hook run on a scratch copy with the real engine output replayed through a fake `wb` answers `allow` for a whole `approve` verdict of a command that carries the state digest (the engine's rule already declines one that does not, after the prerequisite plan) and answers nothing for every other input, outcome and failure listed in the Goal; it never prints `deny`; with the key at any other level, or the table unreadable, it answers nothing; the answer is one JSON object of exactly the documented form.
5. Each answer the hook gives is in the verdict row (the row records that the hook answered `allow`), and the report prints, apart from the shadow's counts, how many commands the hook allowed, by action and by day, and the ids needed to sample them.
6. The spec has the owner's runbook (turn on in one project, see what was allowed, turn off), says what the cutover line of the report means once the hook can decide, and states what is still not covered.
7. The owner has been asked whether to run a security review of the deciding hook and of the installer change, and the answer is in the Result. (Recommended: this is the first form of the system that allows something, and the plan's author recommends it.)
8. `wb run code-work check` passes.
9. The bound is checked, and the check is in the Result. Before increment D begins, and again before the owner is asked to set the key (increment F, step 2), the agent runs `report.py`'s reading with the owner, and the plan goes on only if its cutover line says that the bound is met (no false approve on the labels or the test set, false declines at or under 10%, at least 10 labelled commits and 10 labelled removals) and the owner has said that the test set was reviewed. If either is not so, the plan stops and the owner decides; the plan never revises the bound, and a trial that falls short of it is a revision of the governing spec by the owner, not a step of this plan. The prerequisite plan of the state digest is completed before D begins.

## Increments

### Increment A — What the harness does, tested on a copy

**Outcome:** completion criterion 1 is true.
**Dependencies:** none.
**Affected areas:** `docs/specs/action-review.md` (the evidence); no code.
**Steps:**
1. Write a probe hook for the owner to run on a scratch copy: a command hook for `PermissionRequest` on `Bash` that logs its input to a scratch file, sleeps for a stated time, and then answers nothing, `allow`, or fails, as an argument chooses. The agent writes the probe and the instructions in its scratch directory and does not run Claude Code with it.
2. The owner runs the cases in a session on a scratch project, in the mode used day to day: (a) no answer after 15 seconds (is the prompt shown at once, or after the hook returns?); (b) `allow` after 15 seconds; (c) `allow` at once; (d) a failure (exit 1, invalid JSON, time out) with and without `onFailure`; (e) a prompted command in the owner's usual mode, to see whether the hook fires. The owner reports what was seen, and the agent records it.
3. Record the result in the spec with the Claude Code version, the date and what each case did. If the prompt is held while the hook runs, say how long the owner waits and ask the owner whether a wait of that length is acceptable for a delegated commit, or whether the plan should stop here.
**Verification:** the owner's observation, as reported; the spec check. Not run: anything against the real engine or bridge.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-action-review-cutover-for-commit#A`.

### Increment B — A module may offer `delegated` for an action it can describe

**Outcome:** completion criterion 2 is true.
**Dependencies:** none (it may be built beside A; D waits for both).
**Affected areas:** `workbench/declarations.py` (the `levels` field), the registry that says what a key offers (`workbench/levels.py`), `docs/specs/command-permissions.md`, `docs/specs/module-contract.md`, `packages/workbench/safe-git/module.json`, the tests that read them.
**Steps:**
1. Read what builds the key of an agent-run argument and what its offered levels are today, and write the tests first in a scratch clone: a module that gives `describe` and a rule for an action may list `delegated` in `levels` for that action's argument; the same for an argument with no `describe`, for an owner-run argument, and for an unknown level is refused with a reason that names the field; a declaration without the field hashes as before. See them fail.
2. Change `verify` and the registry so that the key offers `block`, `delegated` and `none` (in the order the registry uses), with its default unchanged. Declare it for `commit` in `safe-git` and not for `remove`.
3. Update the two specs (the "Decided, not built" paragraph becomes built for this part). Search the repository for another place that says `delegated` is the plan approval's alone, and report one that disagrees.
4. Run the whole suite in the scratch clone, tell the owner what could break outside the tested area before running it, and ask the `reviewer` for a read.
**Verification:** the new tests, `tests.test_declarations`-class tests and the whole suite as above, `wb run code-work check`. Not run: a real attach.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-action-review-cutover-for-commit#B`.

### Increment C — What the level renders and what the settings say

**Outcome:** completion criterion 3 is true.
**Dependencies:** B.
**Affected areas:** `workbench/rendering.py`, `workbench/settings.py`, `workbench/doctor.py`, `workbench/levels.py`, `docs/specs/command-permissions.md`, their tests.
**Steps:**
1. Write the tests first in a scratch clone: a key of an action at `delegated` renders an `ask` rule and reads `delegated` through `wb settings`; `wb doctor` notes that the bridge's approval depends on a hook it cannot see; `approve-plan` at `delegated` still renders as it does; a table that names `delegated` for a key that does not offer it reads `block`, as an unoffered level does today; a project that does not set the key is unchanged. See them fail.
2. Change the rendering and the readers as the tests say. Keep the rendering record's format unless a test shows it must change; if it must, bump it as the installer does and say so.
3. Update the specs. Run the whole suite in the scratch clone and ask the `reviewer` for a read.
**Verification:** as for B; plus a render on a scratch attach of a project with the key at `delegated` (the permissions file and the record read back), and `wb settings` and `wb doctor` over it.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-action-review-cutover-for-commit#C`.

### Increment D — The hook may answer `allow`

**Outcome:** completion criterion 4 is true.
**Dependencies:** A (the result of the test), B and C (the key exists and is readable), the completed prerequisite plan of the state digest, and criterion 9 (the bound is checked first and the check is recorded).
**Affected areas:** `packages/workbench/action-review/hook/shadow_hook.py`, `hook/shadow_store.py` if the row needs a field, `docs/specs/action-review.md`, their tests.
**Steps:**
1. Write the tests first in a scratch clone: with the key at `delegated` in the scratch project, a whole `approve` replayed through a fake `wb` gives exactly one `allow` object; each of `decline`, `no_rule`, `unreviewable`, `refused`, `failed`, `timeout`, a malformed `outcome:`, an exit code that disagrees, an `approve` with a failed check, a verdict with extra fields, a replayed `approve` whose command carries no state digest or a digest that differs from the one the replayed `describe` object holds (the hook trusts the engine's own check and, as a second line, does not answer when the command text has no digest argument), an empty answer, a table that cannot be read or parsed, a key at any other level, a project the table does not name, and a hook run over time gives no output and exit 0; no input gives `deny`; the answer is one JSON object of the documented form and nothing else on standard output; the verdict row is written before the answer and a failed write does not change it. See them fail.
2. Add the deciding form to the hook: ask the installer for the table from the hook's `cwd` (read-only, within a stated bound of time), and answer only as the tests say. Keep the registration, the time limit and the absence of `onFailure` as they are.
3. Run the mutation passes on the decision (every condition dropped or loosened must fail a test), and a read-only check that the shipped hook with the key unset behaves as before on the shadow's own tests.
4. Update the spec ("The enforcement point", "The shadow hook"). Ask the `reviewer` for a read.
**Verification:** the hook, store and report tests in the scratch clone, run as `python3 -I -B`; the module's rule, bridge, module and pin tests; the mutation pass; `wb run code-work check`. Not run: the hook against Claude Code and a real bridge (increment F).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-action-review-cutover-for-commit#D`.

### Increment E — See what the hook allowed, and the way back

**Outcome:** completion criteria 5 and 6 are true.
**Dependencies:** D.
**Affected areas:** `packages/workbench/action-review/tools/report.py`, `tests/test_tools_report.py`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first: the report prints, apart from the shadow's counts, the number of commands the hook allowed by action and by day and the ids to sample, prints nothing new when no row records an allow, and does not count an allowed command as a labelled one; a row with a missing or malformed field is counted as unreadable and never as an allow. See them fail.
2. Add the lines. Add to the spec the owner's runbook: set the key in one project, run a commit, read the report, label a sample of what was allowed (the labelling tool already handles it), and turn off by setting the key back and, if wanted, removing the hook's entry.
3. State in the spec what the cutover line of the report means when the hook can decide, and what the bound does not cover (the coverage gap, the thin sample, the previews and `remove`).
4. Run the verification and ask the `reviewer` for a read.
**Verification:** `test_tools_report.py` and the module's tests as for D; `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-action-review-cutover-for-commit#E`.

### Increment F — The owner's trial, and the record of it

**Outcome:** completion criteria 7 and 8 are true, and the Result says what the first use showed, if the owner starts one.
**Dependencies:** D and E, released, upgraded and copied by the owner; the completed prerequisite plan of the state digest.
**Affected areas:** the Result of this plan; the spec's evidence.
**Steps:**
1. The agent asks the owner once whether to run a security review of the deciding hook and of the installer change. It runs only on the owner's word. The agent also tells the owner that the first form of the system that allows something is built, so that the review is not asked for as an afterthought.
2. The agent runs the check of criterion 9 with the owner: it shows the report's cutover line and the owner's statement about the test set, and goes on only if the bound is met. The owner then decides whether to set the key to `delegated` in this project, and for how long. This is the cutover and it is the owner's alone; the plan does not ask for it.
3. If the owner does, after the period the owner runs the report and shows it; the agent records the counts, the number allowed, what the owner saw of the prompt, and any command the owner thinks should not have been allowed, with the report's output as the evidence and no claim beyond it.
**Verification:** the report as the owner ran it; the spec check.
**Evidence:** the Result of the plan, and the local commit that records it, with the trailer `Plan: 2026-11-08-action-review-cutover-for-commit#F`.

## Verification for the plan as a whole

The recorded verification of each increment stands. The whole installer suite is run in the scratch clone for B and C. Whether the hook is right in use is for the owner's trial and the report; the plan does not claim an accuracy.

## Risks and sensitive actions

- **This is the first form of the system that allows something.** Everything so far recorded and decided nothing. A false approve here means a commit made without the owner's prompt. The commit is local and reversible and a push is a separate prompted action that the engine has no rule for, which is why the plan starts there, but the harm is not zero (a commit can record something that should not be recorded, in a repository whose history the owner then has to rewrite). The bound the owner set has no false approve on the labels or the test set; the labels are 75 commits and the test set 29 cases, which is thin evidence against a rare event.
- **The worktree can change between the review and the commit.** The facts are taken when `describe` runs, and a process that the agent started earlier could change a file before `safe-git commit` stages it, so that a different diff is committed under an approval of the earlier one. The state digest of the prerequisite plan, recomputed inside the commit's lock, is what closes this, and the plan does not build the deciding hook before it exists. The residual risk after it: a change that keeps the digest (none is known) and a bridge that approves a bad diff, which is the false-approve rate the bound measures.
- **The model's verdict is steered by text the agent controls.** The rubric treats text addressed to the reviewer as a failed check, and the fixed checks run before the model is asked; neither is proof. The mitigation is that a decline, any doubt and any failure fall back to the owner, and the runbook has the owner sample what was allowed.
- **The hook is a user-level program that runs for every project.** The per-project table is the only reason it decides in one project and not in another; a bug that read the wrong project's table would decide where the owner did not choose. The tests cover a project the table does not name, and the security review, if the owner asks for it, is asked to try this.
- **The installer change is cross-cutting** (the registry, `verify`, rendering, settings, `doctor`). It adds a level to one key and changes nothing for a project that does not set it; the whole suite and a scratch attach are the evidence.
- **A bridge call per prompted commit** sends the diff, redacted as the shadow does, to the vendor for each prompted commit while the key is `delegated`, as it already does for every reviewed command in the shadow; the owner chose that in the shadow's steps.
- A package file and the installer change: the release approvals, the stale-record removal, the acknowledge, the upgrade and the rerender are the owner's. Nothing is pushed without the owner's word.
- No credential is read or written by the hook; the code adds no network call of its own (the bridge is the engine's).

## Review record

Codex, plan review, 2 rounds of 3 (the bound); converged with no meaningful finding in round 2. Model: `gpt-5.6-terra` for both rounds.

- Applied (round 1, major): the approval was bound to the command text and not to the state that the commit would record, so a file changed between the review and the commit could be committed under an approval of the earlier diff. The spec already lists it as an open limit ("Approval is not bound to the content that is committed", with the fix named as a change to another module), and decision 1 of the accepted record says that `delegated` carries the same in-lock digest check as `ask`. The plan now states the binding in its Goal, makes a state digest of `safe-git commit` a prerequisite plan (not drafted yet, and first in order: `describe commit` prints it, `commit` takes `--state-digest` and checks it inside its lock, the engine's commit rule declines a command with no digest or a wrong one, and the `commit-changes` skill runs `describe` first), makes increments D and F depend on it, gives increment D a test for a replayed approve with no digest or a different one, and adds the risk with its residual.
- Applied (round 1, major): the trial could be started without checking the cutover bound that "Accuracy and cutover" and decision 9 of the accepted record set as a precondition (no false approve on the labels or the test set, at most 10% false declines, at least 10 labelled commits and 10 labelled removals, and the owner's word), while the plan's own non-goal said it does not change that bound. New criterion 9: the agent shows the owner the report's cutover line before increment D begins and again before the owner is asked to set the key, goes on only if the bound is met and the owner has said that the test set was reviewed (the spec says the owner reviews and corrects it; the repository does not record that they did), and otherwise stops; a trial that falls short of the bound would be a revision of the governing spec by the owner and not a step of this plan.
- Left for the owner: the question of whether to draft the prerequisite plan first (the plan says it is first in order); whether the roadmap candidate `action-review-engine` is the right home or a separate candidate for the cutover is wanted; and the calls marked "(my call)": commit only, the per-project table, the strict approve, and the `ask` rule that the installer renders for the level.

## Deferred work

- `remove` (and a rule for each other action), one at a time, each on its own evidence.
- What the hook does with a removal preview at cutover (decision `2026-11-05-unconfirmed-removals-are-outside-the-action-review-measure`).
- The coverage gap: 313 of 590 prompted commands were not reviewed on 2026-11-08 (125 with no rule, 186 outside the command grammar, 2 timed out), and the store keeps no command text to say what they are.
- The plan approval folding into the general route (decision 4 of the accepted record).
- A per-day or per-project cap on what the hook may allow, and a notification of each allow, if the trial shows the need.
- The check fixes that the report's false declines point at, each its own plan.

## Result

Empty until work starts.
