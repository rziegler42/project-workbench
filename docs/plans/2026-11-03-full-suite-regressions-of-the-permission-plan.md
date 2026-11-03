# Fix the 15 full-suite regressions of the permission consistency plan

Status: Completed
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

### Increment A — The kit file and the self-hosting record

- **Done:** `workbench/wbkit/digest.py`: the compiled pattern (`re.compile(r"[0-9a-f]{32}\Z")`, used with `match`) became a string used
  with `re.fullmatch`, so the kit builds no compiled pattern; the module docstring and a comment no longer name the two helpers (the
  parenthesis about how a caller builds its lines is generic: a helper that holds a lock takes them under it, one that replaces a file
  takes them from its held root and the sha-checked replace). Behaviour and the kit API number (1) are unchanged. `tests/test_wbkit_digest.py`:
  two docstrings no longer name a module. `tests/fixtures/self_hosting_dispositions.json`: `docs/plans/README.md` is recorded `diverged`
  with its reason (the project's copy states how a plan is approved at each level; increment D brings the seed level and records it
  `identical` again).
- **Tests first:** the failing tests were the ones that exist: before the change `test_kit` (2 failures), `test_self_hosting` (2),
  `test_run` (1) and `test_boundary` (1) failed, `test_wbkit_digest` (18) passed.
- **Verification as run** (`-W error`): `test_kit` 13 OK, `test_self_hosting` 3 OK, `test_wbkit_digest` 18 OK; `test_run` 27 and
  `test_boundary` 19 still fail with one failure each, as the plan says: `workbench/levels.py` naming a module command (increment C) and
  90 places in the tests that name modules (increments B and C), down from 97 (the four of `digest.py` and the three of
  `test_wbkit_digest.py` are gone); the `groundwork` helper test root 251 OK; the `review-engine` test root 409 with the two known
  skill-text failures of increment D, none about the kit digest.
- **Review:** the `reviewer` agent, one exchange, no blocking finding. It read `well_formed` as equivalent for every input (a trailing
  newline, uppercase hex, non-ASCII digits, other lengths and non-text; the tests of `test_wbkit_digest.py` pin them), the kit's rules as
  holding, the fixture reason as accurate and in the form `test_self_hosting.py` expects, and the three files as matching the
  plan's steps. It could not run anything or read the helpers' code.
- **Committed as** `e18b4cb88beec6bd4f3ddc6cac4c2e082f2e1357`. Not pushed.

### Increment B — Decision: the boundary list, module-owned pairing and module pins

- **Done:** `docs/decisions/2026-11-03-conformance-tests-name-modules-and-module-pins-follow-the-levels.md`, written `Proposed`, then
  accepted by the owner through `groundwork accept` at `ask` (digest `8df232b7f4f855f04f9944c45b2d64e8`). It decides three things:
  (1) `tests/test_levels_facts.py` and `tests/test_permissions_drift.py` are exempt from the boundary scan by exact path, nothing under
  `workbench/` is, and `test_doctor.py`, `test_command_gate.py` and `test_gate_corpus.py` are reworded to made-up module names;
  (2) `PAIRED_ACTS`, `_PAIRED_BACK` and `paired_with` leave `levels.py`, the pairs stay in the drift test's `CHECKPOINT_PAIRS` and the
  spec, and merging them is for the follow-on plan; (3) the nine module assertions change one at a time as the record's table says:
  two texts are fixed and their pins kept, five pins are updated to the phrase that is now true, and three limits are raised with a
  reason (the policy block from 32 to 40 lines, the plan-drafting skill's commands, the commands `peer-review` runs).
- **A change from the plan's own recommendation, for the owner to know:** the plan's step 3 recommended that a module declare the pairing.
  Reading the source showed that nothing in the installer reads `paired_with` while it runs (only one test does), and the follow-on
  plan decides whether to merge the pairs, so the record recommends removing it and says it reverses the first recommendation. The
  owner accepted it.
- **Verification as run:** `wb check` and `wb run code-work check`: no problems. The facts in the record were read from the full run, the
  extract of the base commit, a scan of the boundary test (97 places before increment A, 90 after, by file and word), a search for
  `paired_with` and `PAIRED_ACTS`, and the nine assertions in the module tests.
- **Review:** none run for this increment (it writes one record, which the owner reads and accepts at the checkpoint); the plan asks
  for none at B.
- **Committed as** `3acf439d96ff5fbb510b6ea596a5b6dd51c274b7`. Not pushed. Nothing in the record is built until increments C and D.

### Increment C — The installer side of the decision

- **Done** (decisions 1 and 2 of the accepted record): `tests/test_boundary.py` has `CONFORMANCE`, the two exempt paths
  (`tests/test_levels_facts.py`, `tests/test_permissions_drift.py`), and `scan(..., exempt=CONFORMANCE)` skips a file by its exact path
  and raises `ValueError` for a path under `workbench/`; `workbench/levels.py` loses `PAIRED_ACTS`, `_PAIRED_BACK` and the `Key` field
  `paired_with` (the one place that builds a `Key` is updated); `tests/test_levels_facts.py` now asserts that the registry keeps no
  pairing and that the checkpoint and the command of each pair still read `block` and `none`; `tests/test_permissions_drift.py`:
  `checkpoint_pairs` takes the spec text and fails a pair with different defaults that no paragraph of the spec names; the spec's
  "Not built" bullet records the two pairs in full and says the registry does not; `tests/test_doctor.py`, `tests/test_command_gate.py`
  and `tests/test_gate_corpus.py` name no module (made-up names `vault`, `ledger` and `notary`; the minimum and the governing-key tests
  compute their keys from the registry; the corpus test checks the structure of the relaxed keys, whose names the fixture holds).
- **Tests first:** the boundary tests for the exemption were written and failed on the missing parameter before `scan` changed; the
  pair tests and the drift reader were changed before `levels.py`, and failed on the field still being there.
- **Verification as run** (`-W error`): `test_boundary` 23, `test_run` 27, `test_levels_facts` 36, `test_permissions_drift` 22, `test_levels`
  35, `test_doctor` 72, `test_command_gate` 130, `test_gate_corpus` 15, `test_kit` 13, `test_self_hosting` 3, `test_settingscmd` 33,
  `test_declarations` 97, `test_verify` 69, and, because the registry's `Key` changed shape, the tests that read it: `test_settings` 84,
  `test_rendering` 85, `test_check` 45, `test_cli` 33, `test_agent_gate` 59, `test_gate_hook` 73, `test_levelrun` 22,
  `test_approve_levels` 39, `test_harnessplan` 68, `test_attach` 76, `test_rerender` 80, all OK; `test_boundary` and `test_run`, which
  failed in the full run, pass; the document check: no problems; `wb doctor`: no problems and 8 risks.
- **Review:** the `reviewer` agent, one exchange, no blocking finding. It confirmed that the exemption is by exact path and cannot hide a
  hit elsewhere, that nothing else read the removed field or built a `Key`, that the drift reader still fails on an unrecorded pair, and
  that the renamed tests mean what they meant (the gate treats `vault`, `ledger` and `notary` as plain tokens). Applied: a blank line
  between two comments in `levels.py`. Not changed, as the reviewer notes: the minimum test now restates the registry's `asks` (its
  independent guard is a count of at least three, and the drift test still pins the real ones), the corpus test checks structure only,
  and one list item that names both strings of a pair satisfies the drift reader.
- **Security review:** not asked for. Nothing in C reads a new input: it removes a table from the installer's source, adds a constant
  list to a test and changes test text. The owner may still ask.
- **Committed as** `018a02b459a47918341465c5226810f34d029b6e`. Not pushed.

### Increment D — The module tests, skills and policy block (package pass)

- **Step 1, the nine assertions** (listed before any edit; what each protects, and what changes under decision 3 of the accepted
  record). Reading the tests showed that three of the nine hold more than one failing phrase.
  1. `code-work`, `test_codework_delegateskill.Commands`, "only the two commands, each in backticks, each once": protects that the delegate
     skill runs `wb settings` and `wb delegate-approve-plan <plan>` and names no other. K's rule named the command a third time,
     without its argument. **Text fixed, pin kept:** the rule says "the delegate command", with no backticked command.
  2. `code-work`, `test_codework_delegateskill.Skill`, "the text carries the phrases of the routine": three phrases changed under K:
     `` `checkpoint approve-plan: delegate` `` (now `` `level approve-plan: delegated` ``, the line the delegate command honours),
     "the owner approves the plan" (now "the plan is approved by the route", pointing at the route `draft-plan` gives) and "never run
     that command" (now "is not a way to reach another route past its level": the skill must not claim that `wb approve-plan` is never
     run, which at `ask` and `none` it is). **Pins updated** to those three phrases; each protects the same thing, that this skill
     reads the delegated level and does not become a second route to approval.
  3. `code-work`, `test_codework_delegateskill.Pointers`, "draft-plan and run-increment name it and still leave the approval to the owner":
     the phrase "only the owner makes with the approve-plan command" in `draft-plan`. **Pin updated:** "Approval is the owner's explicit
     statement", plus "only after the owner has said to approve", which is what keeps the approval the owner's at `ask` and `none`.
  4. `code-work`, `test_codework_module.Skill`, "states the naming, the header, the labels and that only the owner approves": the same
     phrase in a list of eleven others, all of which hold. **Pin updated** the same way.
  5. `code-work`, `test_codework_module.Skill`, "no skill file runs a command beyond the plan check": the plan-drafting skill runs one
     command, `wb run code-work check` (two lines name it). Under K step 8 also names `wb settings`, `wb plan-status` and
     `wb approve-plan`. **Limit raised with its reason:** the test now requires that every command the skill names is one of those four
     and that no other `wb` appears outside backticks; the forbidden words and the no-raw-git pins in the same test stand.
  6. `code-work`, `test_codework_module.Blocks`, "the policy block is short and names no tool": at most 32 lines. K's block is 38.
     **Limit raised:** 40 (it was raised before for the testing and security-review bullets); the no-harness, no-vendor pin stands.
  7. `code-work`, `test_codework_module.Blocks`, "every checkpoint stops ... and where to read them": the block does not contain
     "delegate". K's block names `delegated` and the `delegate-approval` skill. **Text fixed, pin kept:** the block drops both; the
     delegate skill is where delegation is said.
  8. `review-engine`, `test_review_module.Skill`, "states the rules": the five owner commands "are the owner's" and "Never run them".
     Those words are what the owner's levels for the review workflow (`2026-10-27-levels-for-the-review-workflow`) replaced.
     **Pin updated:** the skill says they take the owner's level, that at `ask` the agent runs the preview and then the action with
     `--digest`, and that at `none` it runs it; the other rules in the list stand.
  9. `review-engine`, `test_review_module.Skill`, "the commands it runs are the engine's": the commands the skill runs are `init`, `status`,
     `review-plan` and `decide`, and no `wb ` remains outside them. **Limit raised:** `preview` joins the set, and `wb settings` and the
     `<action>` form of the preview are the only other `wb` text; the owner's five are still never named as commands the skill runs.
- **Also in the pass, from the decision and the plan:** the seeded `code-work/files/docs/plans/README.md` is made equal to the project's
  `docs/plans/README.md`, and the self-hosting record is set back to `identical` for that path.
- **The pass, built and tried on a copy.** One script writes the seven package files (the delegate skill, the policy block, the three
  module test files, the seeded plans README), checking every old text for exactly one occurrence in all files before it writes any,
  so the tree is either untouched or fully rewritten. On a copy of the repository the pass was run, and then the `code-work` test
  root (346 tests OK, 2 skipped, as before; 7 failed before), the `review-engine` root (409 OK; 2 failed before), `test_permissions_drift`
  22, `test_verify` 69, `test_boundary` 23 and `test_skill_names` 8 all pass. One slip of mine was found there and fixed before this
  record: the first version of the plan-drafting command test compared the spans with backticks. The owner starts the pass on this tree.
- **Review of the pass:** the `reviewer` agent, one exchange, no blocking finding; it read the nine assertions against the pass and
  the staged texts and ran nothing. It found the staged block and skill true against the registry and the spec, the seeded README a
  byte copy of the project's, and the drift readers still holding. Applied: the pass validates every file before writing any (a failure
  in a later file left earlier files rewritten); the plan-drafting skill's command check is now the exact set of seven spellings
  (it compared only the head of each), and one more pin keeps the `block` rule ("the owner makes the approval with `wb approve-plan
  <plan>` in a terminal"). Noted and accepted: the decision's own wording for the delegate skill ("write the command with its
  argument") would have added a second span and broken a pin that keeps it to one, so the rule says "the delegate command" and the
  Result list above is the record of what was built; the pins that replaced "never run that command" and "only the owner makes ..."
  say less, with the old protection held by pins that stand; the policy block says nothing of `delegated`, as decision 3 asks, so an
  agent that reads only `AGENTS.md` at that level is not pointed to the delegate route and would stop and ask.
- **The owner's steps and the real-tree checks (2026-11-03).** The pass wrote six files (five edited and the seeded README) and
  closed the gates: the refusal line read `... differs from its release: first at 'packages/workbench/code-work'; the owner clears
  it in a terminal with wb preview release-approvals and then wb release-approvals --digest <digest> ...`. The owner released the
  approvals (14 approvals for the package; three older shipped records, those of increment K, reported as no longer part of the
  release) and ran `wb upgrade` and `wb rerender`: `wb preview rerender --package <the local package>` then ends "nothing to change",
  and `AGENTS.md` carries the policy block without the `delegated` sentences. The disposition of `docs/plans/README.md` is back to
  `identical` in the self-hosting record.
- **Verification as run on the real tree** (`-W error`): the `code-work` test root 346 OK (2 skipped, as before; 7 failed before), the
  `review-engine` root 409 OK (2 failed before), `test_permissions_drift` 22, `test_verify` 69, `test_boundary` 23, `test_skill_names` 8,
  `test_firstparty` 57, `test_harnesses` 28, `test_harness_lock` 30, `test_gate` 27, `test_self_hosting` 3, `test_rerender` 80,
  `test_attach` 76, `test_check` 45, `test_rendering` 85, all OK; the document check: 83 plans, no problems; `wb check`: no
  problems; `wb doctor`: no problems and 8 risks. The full run is increment E.
- **Committed as** `989f5581c7e9144614ec2be61e5a1d07d7b486a7`. Not pushed.

### Increment E — The full run

- **Before the run:** the three shipped records of increment K, which the release of increment D reported as no longer part of it, were
  removed through `wb run safe-git remove` (the preview listed the three directories, each with one `approval.json`; the run with
  `--confirm` followed the owner's word); `wb preview release-approvals` then read `stale records: 0`. The deletion was in the working
  tree during the run and is committed after it.
- **Run:** `python3 -B -W error tests/run_all.py`, once, in the background, output written to a file (2026-11-03, on the commit of
  increment D plus those three deletions; workbench 0.1.0, Python 3.15.0). Result: **7,021 tests in 14 roots, OK, exit 0.** Per
  root: `tests` 4,011 (1 skipped), `action-review` 463, `ask-codex` 103, `ask-ollama` 437, `claude` 34, `code-work` 346 (2 skipped),
  `freecad` 23, `groundwork` 251, `mempalace` 152, `remote-runner` 107, `review-engine` 409, `safe-git` 647, `security-review` 24,
  `verilog` 14. The first full run of the day, at commit `76d7294`, had 7,018 tests and 15 failures in three roots (`tests` 6,
  `code-work` 7, `review-engine` 2); the 3 more tests are this plan's (the boundary tests for the exemption, increment C).
- **Skipped tests:** 3 in all, as in the first run (1 in `tests`, 2 in `code-work`); none was added by this plan.
- **Each of the 15 failures, and where it ended:** the kit file's `compile` and module names, and the self-hosting record
  (increment A); the boundary rule and the registry's module name (increments B and C, by the accepted record: two conformance tests
  exempt by path, the pairing out of the installer, three test files reworded); the seven `code-work` and two `review-engine` module
  pins (increment D, one assertion at a time, as the record's table says, with the seeded plans README made level).
- **The removal, committed as** `e0b920c9e796616a69ef7e9262851d3f1f0cdd47` (three deleted `approval.json` files, no plan trailer, as
  with the earlier removal). Not pushed.
- **Plan completed (2026-11-03, at the owner's word).** The completion criteria, against what is recorded: (1) the full run passes,
  7,021 tests in 14 roots, exit 0, run on the commit of increment D with the three deletions of the stale records, which were
  committed straight after; (2) each of the 15 failures has its cause and fix above, and the nine module pins changed only as the
  accepted record's table says; (3) the decision of increment B is `Accepted` and increments C and D built it; (4) `wb preview
  rerender` reads "nothing to change", `AGENTS.md` and the `.workbench` copies are current, and `wb doctor` reads no problems (8
  risks, the owner's chosen levels); (5) the Result of `2026-11-02-permission-system-consistency` records the full run, and its status
  is `Completed` again by the owner's word.
- **Not done:** the commit of this Result and of the two status lines; a push.
