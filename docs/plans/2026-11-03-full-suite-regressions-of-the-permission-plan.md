# Fix the 15 full-suite regressions of the permission consistency plan

Status: Proposed
Created: 2026-11-03
Candidate: none (this repairs work of the plan `2026-11-02-permission-system-consistency`, which the owner reopened; it adds no roadmap candidate)
Specs: command-permissions, module-contract, module-boundary, code-work, review-engine

## Goal

A full run of the tests (`python3 -B -W error tests/run_all.py`: the repository's `tests/` and each module's own tests) passes again
after the work of the plan `2026-11-02-permission-system-consistency`. When this plan is done there is no failing test that passes on
the base commit `76df744`, the cause of each of the 15 failures is removed at its source or the rule it broke is changed by a decision
of the owner, and the plan `2026-11-02-permission-system-consistency` can be `Completed` again with a full run as its evidence.

## Scope

The full run on 2026-11-03 (7,018 tests, 14 roots, commit `76d7294`) failed in three roots. Every failing file passes on the base
commit `76df744`, so each failure is a regression of that plan:

1. **`tests/`, six failures.**
   - `test_kit.Boundary` twice: `workbench/wbkit/digest.py` (increment H) uses `compile` (the kit may not) and names two modules in its
     docstring (the kit may name none).
   - `test_run.TheInstallerNamesNoModuleCommand`: `workbench/levels.py` (increment G, `PAIRED_ACTS`) and `workbench/wbkit/digest.py`
     name a module command.
   - `test_boundary.Repository.test_the_installer_and_its_tests_name_no_module_helper_harness_or_path`: 97 places. One is
     `workbench/levels.py` (`PAIRED_ACTS` names `remote-runner`), four are `digest.py`, and 92 are in tests this plan added or changed
     that read the real shipped package and so name its modules (`test_levels_facts`, `test_permissions_drift`, `test_doctor`,
     `test_command_gate`, `test_gate_corpus`, `test_wbkit_digest`).
   - `test_self_hosting.Relation` twice: `docs/plans/README.md` was edited (the project's copy states how a plan is approved at each
     level) and now differs from the seeded copy, which the disposition record `tests/fixtures/self_hosting_dispositions.json` says is
     identical.
2. **`code-work` module tests, seven failures**, and 3. **`review-engine` module tests, two failures.** Increment K rewrote the
   `delegate-approval`, `draft-plan`, `run-increment` and `peer-review` skills and the `code-work` policy block so that they state the
   levels. Each module keeps pins on its own text: the delegate skill names two commands and reads the legacy `checkpoint
   approve-plan: delegate` line; `draft-plan` says "only the owner makes with the approve-plan command"; no skill of `code-work` runs a
   command beyond the plan check; its policy block is at most 32 lines, names no tool and does not contain "delegate"; the
   `peer-review` skill states that the five owner commands are the owner's and runs only `init`, `status`, `review-plan` and `decide`.
   The full list is in the Result of this plan when work starts.

In:

- the installer-side fixes that need no decision (the kit file and the self-hosting record);
- one decision record of the owner's on three questions that the failures raise (below);
- the change that the accepted record asks for;
- one scripted pass over the package files (module tests, skills, policy block and the seeded plans README), released and rendered by
  the owner;
- a full run.

## Non-goals

- Any change to a level, a default or a key. The text of the skills and the policy block keeps saying what the registry says
  (`2026-11-02-permission-system-consistency`, increment K); what changes is where it is said and what the module tests pin.
- The heredoc decision `2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps`, Low 3 of increment I and the plan
  `2026-11-02-permission-levels-for-every-command`.
- A push. The owner decides it after the full run is green.

## Assumptions and constraints

- Each failing file passes on the base commit (run on 2026-11-03 on an extract of `76df744`), so no failure is older than the plan.
- The rule that the installer and its tests name no first-party module is the owner's design (`tests/test_boundary.py`, "The installer
  and its tests name no first-party module, helper, command, harness or harness path"). A change to it is the owner's, by a decision.
- Several increments edit files under `packages/workbench/`. Each such edit closes the gates until the owner releases the approvals,
  so the package edits are one scripted pass that the owner starts, then the release and `wb upgrade`, `wb preview rerender` and
  `wb rerender`.
- Testing is targeted per increment, and the last increment runs the full suite, because the failures came from what targeted runs
  cannot show: each module's own tests and the tests of the repository that read the whole tree.
- A decision record is written `Proposed`; accepting it is a checkpoint (at the owner's level `ask`: preview, then the digest).

## Completion criteria

1. `python3 -B -W error tests/run_all.py` exits 0 with every root passing, run at the commit that ends the plan.
2. Each of the 15 failures has a recorded cause and fix in the Result, and no test was weakened without a decision of the owner that
   names it.
3. The decision record of increment B is `Accepted`, and the change it asks for is built and tested.
4. The rendered copies and `AGENTS.md` in this clone are current (`wb preview rerender` lists nothing to change), and `wb doctor`
   finds no problem.
5. The Result of `2026-11-02-permission-system-consistency` records the full run, and its status is `Completed` again by the owner's
   word.

## Increments

### Increment A — The kit file and the self-hosting record

**Outcome:** `test_kit`, `test_run` (for `digest.py`) and `test_self_hosting` pass, with no change to what the kit computes.
**Dependencies:** none.
**Affected areas:** `workbench/wbkit/digest.py`, `tests/test_wbkit_digest.py`, `tests/fixtures/self_hosting_dispositions.json`.
**Steps:**
1. Run the five failing tests and keep their output (they are the tests first: they fail now and name the cause).
2. `digest.py`: take `compile` out (match with `re.fullmatch` on a string pattern, or write the check by hand), and write the module
   docstring and comments without a module name; the behaviour and the kit API number stay as H built them, and the tests of
   `test_wbkit_digest.py` are unchanged except for the module names they hold (reworded to made-up ones).
3. Record `docs/plans/README.md` as `diverged` in the disposition record, with the reason: the project's copy states the approval
   flow at each level, and the seeded copy is brought level by increment D.
4. Ask the `reviewer` agent to review the diff.
**Verification:** `test_kit`, `test_run`, `test_self_hosting`, `test_wbkit_digest`, `test_boundary` (only the lines for `digest.py` go),
and the tests of the two helpers that use the kit digest (`groundwork` and `review-engine` helper tests, run as they are).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-full-suite-regressions-of-the-permission-plan#A`.

### Increment B — Decision: what the boundary rule covers, where module-owned facts live, and what a module may say

**Outcome:** a `Proposed` record that the owner accepts, answering three questions with a recommendation for each, so that the rest of
the plan builds one chosen thing.
**Dependencies:** A.
**Affected areas:** `docs/decisions/` (one new record).
**Steps:**
1. Write the record from the template, with the facts: the 97 places and their split, the precedent that the `groundwork` policy block
   already names `wb settings` and the preview command, and the module tests that pin the other modules' text.
2. Question 1, **conformance tests that read the real package.** The author recommends a short, named list of test files that are
   exempt from the boundary scan because reading the shipped package against the registry is their job (`test_levels_facts`,
   `test_permissions_drift`, `test_doctor`, and the parts of `test_command_gate`, `test_gate_corpus` and `test_wbkit_digest` that name
   a module, which the author would rather reword to made-up names); the alternative is to rewrite them all with made-up modules, which
   weakens them.
3. Question 2, **the facts that belong to a module** (`PAIRED_ACTS` names `remote-runner` in `levels.py`; `STATED_BY` names skills). The
   author recommends that a module declares them (a field on the command or the checkpoint in `module.json`, read by the registry),
   so the installer names no module; the alternatives are a recorded exception for `levels.py`, or dropping the table.
4. Question 3, **what a module's skills and policy block may name.** The author recommends that the pins of `code-work` and
   `review-engine` be updated to what K built (skills may run `wb settings`, `wb plan-status` and `wb approve-plan` at their levels,
   and the policy block may name them, as the `groundwork` block does), with the block's limit raised to what it now needs; the
   alternative is to shorten the block to a pointer ("`wb settings` says how; the `draft-plan` skill gives the flow") and keep its pins.
5. Stop at `Proposed` and ask the owner. Accepting is the owner's checkpoint.
**Verification:** `wb check` (the decision form) and the document check; no test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-full-suite-regressions-of-the-permission-plan#B`.

### Increment C — The installer side of the decision

**Outcome:** `test_boundary` and `test_run` pass as the accepted record says.
**Dependencies:** B accepted.
**Affected areas:** `tests/test_boundary.py` (a named exemption, if chosen), `workbench/levels.py`, `workbench/declarations.py` and
`docs/specs/module-contract.md` (a declared field, if chosen), the tests that name a module (reworded where the record says so).
**Steps:**
1. Write the tests first from the record: the boundary test names the exempt files and fails for any other file that names a module; a
   test that the registry reads the pairs and the stating skills from declarations (if chosen).
2. Build what the record chose. If it chose a declared field, the installer changes here and the two `module.json` lines are part of
   increment D's pass; until then the registry reads the table as before, and the test that needs the field is written to pass only
   after D.
3. Ask the `reviewer` agent to review. If the record put a rule in the installer's own source (`levels.py`), ask the owner whether to
   run a security review.
**Verification:** `test_boundary`, `test_run`, `test_levels`, `test_levels_facts`, `test_permissions_drift`, `test_declarations`,
`test_verify`, and the tests of the files reworded.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-full-suite-regressions-of-the-permission-plan#C`.

### Increment D — The module tests, skills and policy block (package pass)

**Outcome:** the `code-work` and `review-engine` module tests pass with the text of increment K as the record of B decides; the seeded
plans README equals the project's; the declared fields of C (if any) are in `module.json`.
**Dependencies:** B accepted, C.
**Affected areas:** under `packages/workbench/`: `code-work` (tests of the delegate skill and of the module, the skills, the policy
block, `files/docs/plans/README.md`, `module.json`), `review-engine` (the skill test), `remote-runner` (`module.json`, if a field is
chosen); `tests/fixtures/self_hosting_dispositions.json`; `AGENTS.md` and the rendered copies (the owner's rerender).
**Steps:**
1. List, for each of the nine module tests, the assertion that fails, what it protects, and whether the text or the test changes
   under the record; write the list into the Result before any edit.
2. One scripted pass in the scratch directory, each old text required to occur once, run first on a copy of the repository where the
   nine tests and the drift test are run; it updates the tests, and the skills or the policy block as the record decides, and makes
   the seeded plans README equal the project's.
3. The owner starts the pass, releases the approvals (preview, then the digest), and runs `wb upgrade`, `wb preview rerender` and
   `wb rerender` in a terminal.
4. Set the disposition of `docs/plans/README.md` back to `identical`.
5. Ask the `reviewer` agent to review the pass and the result.
**Verification:** the two module test roots (`code-work`, `review-engine`) run as roots, `test_permissions_drift`, `test_self_hosting`,
`test_verify`, the document check, and `wb preview rerender` listing each file current.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-full-suite-regressions-of-the-permission-plan#D`.

### Increment E — The full run

**Outcome:** the full suite passes, and the owner can complete the earlier plan.
**Dependencies:** D.
**Affected areas:** this plan's Result and the Result of `2026-11-02-permission-system-consistency` (a note); no code.
**Steps:**
1. Before the run, state to the owner what the run covers and what could still fail (a test that needs a tool or a network that the
   run lacks), and run `python3 -B -W error tests/run_all.py` once.
2. Record the output as run: the count per root and the exit code. A failure stops the increment: diagnose it, and do not widen it.
3. Add the note and the evidence to the Result of `2026-11-02-permission-system-consistency`; its status goes to `Completed` only by
   the owner's word.
**Verification:** the full run, as run.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-full-suite-regressions-of-the-permission-plan#E`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. After E, increment E's full run is the
evidence: it is the one wider run this plan names, with the reason above (the failures were in places that targeted runs do not
reach).

## Risks and sensitive actions

- **A rule of the owner's is changed.** Increment B asks the owner to change what the boundary test covers and where module facts
  live; nothing is built before they accept the record.
- **A package edit closes the gates** (increment D): the pass is the owner's to start, the release is theirs to confirm, and until then
  every hooked tool is refused, with the cause named.
- **Weakening a pin to make a test pass.** Increment D lists each assertion and what it protected before any edit; a pin that stays is
  met by changing the text, a pin that changes is named in the record of B.
- **The registry's reading of module declarations** (increment C, if a field is chosen) is installer code that every owner-run command
  reads: the tests of the registry and the drift test come first, and the author asks the owner once whether to run a security review.
- **A push before the run is green** would publish the 15 failures: the push waits for increment E.

## Review record

Empty until a review is asked for.

## Deferred work

- The heredoc build (`2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps`), Low 3 of increment I (globs and
  alternations) and the follow-on plan `2026-11-02-permission-levels-for-every-command`, which should be reviewed after this plan.

## Result

Empty until work starts.
