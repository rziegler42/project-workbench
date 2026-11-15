# Enroll a clone of an installed project on a new machine

Status: Proposed
Created: 2026-11-15
Candidate: workbench-v1#enrol-a-clone
Specs: clone-enrollment, installer-interface, trust-and-approval, command-permissions

## Goal

A clone of an already installed project, on a machine that has never held it, is made known there by one owner-run command, `wb enroll`, with a read-only `wb preview enroll`. Afterwards the checks, `attach`, `upgrade`, `add` and `acknowledge` work on the clone and its helpers are pinned. The design is `docs/specs/clone-enrollment.md` (Draft, reviewed in four rounds); this plan builds it. Where this plan makes a choice that the spec leaves open, the choice is marked **(my call)**, so that the owner can overrule it at review.

## Scope

- A decision record for the trust basis, written `Proposed` (increment A).
- A read-only plan of what an enrollment would write, with the checks of the spec (B), the preview command (C), the owner-run write (D), the registration and the tests and tables that list every key (E), a security review and its fixes (F), the setup page and the spec as built (G), and the record of the owner's run on the second machine (H).
- Code in `workbench/` (the installer) and its tests in `tests/`.

## Non-goals

- Anything the spec lists as a non-goal: moving a project between paths, a comparison with another machine, writing an approval, fetching a package, attaching a harness, copying settings.
- Changing what a baseline, a pin or an approval record means, or the format of any store file.
- A level other than `block` for `wb enroll` **(my call)**: the key offers `block` only, like `wb rerender`.
- Running anything on the owner's second machine myself: the owner runs the setup page there and reports back, and increment H records it.

## Assumptions and constraints

- The installer in `workbench/` is imported by the harness hooks, so a half-written edit can refuse every tool call. Each code increment is therefore prepared in a scratch copy of the repository, tested there by importing it (the command line of a copy is never run, because it rewrites the shared launcher), and applied to the real tree in one scripted pass followed by the tests. This is the rule the owner's memory records for this repository.
- The guarded store is under `HOME`. Every test uses a temporary `HOME` and a temporary project, as the existing tests do (`tests/support_install.py`).
- The command is modelled on `acknowledge` (terminal-only, a digest the owner types back, a re-read after the answer, one atomic store write, the level log) and on `install` for what it writes (`installplan.py`, `pinplan.py`).
- An approved plan changes only in its status, its review record and its result. A change of design after approval goes back to the owner.
- The plans directory is under the 16 MiB budget of the code-work helper since `2026-11-15-plan-byte-budget`.

## Completion criteria

1. The ten acceptance criteria of `docs/specs/clone-enrollment.md` hold, the last of them by the owner's reported run on a second machine (increment H). The plan is not `Completed` before that run passes.
2. `wb enroll` and `wb preview enroll` exist, the key `wb enroll` offers `block` only, and `wb settings`, `wb doctor` and the rendered deny rules name them.
3. The accepted decision record exists, the spec reads `Current` where the owner says so, and `installer-interface.md`, `command-permissions.md`, `development.md` and `INSTALL.md` describe what is built.
4. A security review of the built command was run, with its findings judged and its fixes tested.

## Increments

### Increment A — The decision record for the trust basis

**Outcome:** a decision record states that a clone is made known on the strength of the committed manifest's hashes, the approvals already on the machine and the digest the owner types, with no comparison against another machine, and the owner has accepted it. It is committed as `Accepted`; increment B does not begin before that commit.
**Dependencies:** none.
**Affected areas:** `docs/decisions/` (one new file), nothing else.
**Steps:**
1. Read `docs/decisions/README.md` and the `draft-decision` skill and write the record from its template, with the context, the options considered (a second check against the first machine, the digest alone, the digest plus the approval records), the choice and its consequences, citing `clone-enrollment.md` and the six decisions the spec names.
2. Run the document checks (`wb check`) and stop at `Proposed`: accepting a decision is a checkpoint that stops for the owner.
3. When the owner says to accept it, at the level `ask` I run the preview of the record, show it, and run the accept command with the digest, and the owner confirms. I then read the record again, check that it reads `Accepted`, and run `wb check`.
**Verification:** `wb check` before and after acceptance, and the record's status read after it; no code changes.
**Evidence:** one local commit of the accepted record, trailer `Plan: 2026-11-15-enroll-a-clone#A`.

### Increment B — The read side: what an enrollment would write

**Outcome:** a module of the installer, given a project and a store, either refuses with the path or entry that failed or returns the baselines, the first-seen record and the pins an enrollment would write, together with the review fields and digest. It reads and writes nothing.
**Dependencies:** A accepted.
**Affected areas:** `workbench/enrollplan.py` (new), `tests/test_enroll_plan.py` (new), reuse of `installed`, `manifest`, `blocks`, `pinplan`, `acknowledgement`, `approvals`, `projectfs`, `target`.
**Steps:**
1. Write the tests first, in a scratch copy, and see them fail: each refusal and each case of the spec's checks 1 to 8 (target, known project, one entry only, manifest paths and classes, module-owned hash, seeded file that differs, unrecorded file, block that differs and block hashed with both marker lines, unapproved module) and the result for a good clone, including the manifest's own baseline and the pins for approved modules only.
2. Write the module: the target and unknown-project checks, the strict manifest read, the path and ownership rules, the file and block comparisons, the approval check through the readers that `attach` uses, the pins through `pinplan.wanted` and `pinplan.changes`, and the digest through the same canonical form as `acknowledge`.
3. Run the new tests and the nearest existing ones (`test_acknowledge`, `test_acknowledgement`, `test_installplan`, `test_pinplan`, `test_blocks`).
**Verification:** the new test file and the five named files, in the scratch copy and again in the real tree after the scripted pass.
**Evidence:** one local commit, trailer `#B`.

### Increment C — `wb preview enroll`

**Outcome:** the read-only preview prints the project id, the path to be recorded, each file with its hash and class, each seeded file or block that differs, each pin and the digest, and writes no entry for the project.
**Dependencies:** B.
**Affected areas:** `workbench/cli.py`, `workbench/preview.py`, `workbench/levels.py` (the key `wb preview enroll`, class reads), `tests/test_enroll_preview.py` (new), `tests/test_levels.py` and the tests that list every key.
**Steps:**
1. Write the tests first, see them fail: output for a good clone, for each refusal, that nothing is written for the project, and that the key and its rule appear in `wb settings`.
2. Wire the preview through the existing preview dispatch and register the key with the same shape as `wb preview acknowledge`.
3. Run the new tests and `test_cli`, `test_preview`, `test_levels`, `test_settingscmd`.
**Verification:** as named; the scratch copy first.
**Evidence:** one local commit, trailer `#C`.

### Increment D — `wb enroll`

**Outcome:** the owner-run command runs the same read, shows the list and the digest, takes the first 12 characters typed back from a terminal, reads the clone again, and writes the three store entries in one atomic step with the level log's attempt before and outcome after.
**Dependencies:** C.
**Affected areas:** `workbench/enroll.py` (new), `workbench/cli.py`, `workbench/levels.py` (the key `wb enroll`, class governs, offers `block` only), `tests/test_enroll.py` (new).
**Steps:**
1. Write the tests first, see them fail: no terminal, wrong or typed-ahead digest, a clone changed between the preview and the answer, a write that fails part-way leaves no entry, a good run writes exactly the baselines, the first-seen record and the pins and the log, and a second run refuses and names `acknowledge`; afterwards `wb check`, `wb doctor` and the preview of `acknowledge` run on the enrolled clone and none of them gives the "treated as new" refusal, and the preview of `acknowledge` lists no difference.
2. Write the command from `acknowledge` and `install` as models, with the write through the store's atomic replacement.
3. Run the new tests and `test_acknowledge`, `test_levelrun`, `test_levellog`, `test_install`, `test_cli`.
**Verification:** as named; the scratch copy first. No command line of a copy is run.
**Evidence:** one local commit, trailer `#D`.

### Increment E — Registration, rendering and the tables

**Outcome:** the harness's deny rules, `wb doctor`, the command gate's key words and the command tables name the new commands, and every test that lists all keys passes.
**Dependencies:** D.
**Affected areas:** `workbench/levels.py` (if more is listed), the rendering and permission modules the tests show are affected, `docs/development.md`, `docs/specs/installer-interface.md`, `docs/specs/command-permissions.md`, `docs/specs/trust-and-approval.md` (its list of owner-run commands in the rendering rules), the tests found by running the whole installer suite once.
**Steps:**
1. Run the whole installer suite once, in the scratch copy, and read every failure: a test that counts or lists the keys is expected to change, and any other failure is reported.
2. Update the rendering inputs and the tests, then the four documents' tables and lists in one change with the code.
3. The owner runs `wb rerender` to refresh the deny rules; I read `wb settings` and `wb doctor` afterwards.
**Verification:** the whole installer suite (`tests/`) once, because the key list is read by tests of settings, rendering, doctor and the gate, which the earlier increments did not run; I tell the owner before it runs, as the project's rule asks. Then `wb check` and `wb doctor`.
**Evidence:** one local commit, trailer `#E`.

### Increment F — Security review and fixes

**Outcome:** a review of the built command by the `security-reviewer` agent, at the owner's word, with each finding judged and each fix tested first.
**Dependencies:** E.
**Affected areas:** the files of B to E; fixes with their tests.
**Steps:**
1. Ask the owner whether to run the review (the command writes trust state and reads untrusted files of a clone). Give the reviewer the spec, the changed paths and the attack cases the spec lists.
2. Judge each finding with `evaluate-findings`; for each applied fix write the test that fails first.
3. After the fixes, ask for an independent second look at them, by a fresh run of the `security-reviewer` agent on the fixed tree (counted against the review caps), record its outcome, and do not complete F while it has an unresolved finding. This is the rule of the `security-review` skill: a fix is itself attack surface.
**Verification:** the tests of each fix, the increments' tests they affect, and the second look's outcome.
**Evidence:** one local commit, trailer `#F`. If the owner declines the review, the plan stops here and stays `In Progress`: the spec's criterion 9 and this plan's criterion 4 require the review, so going on without it needs the owner's explicit change of the spec and a new approval of this plan.

### Increment G — The setup page and the spec as built

**Outcome:** `INSTALL.md` describes `enroll` and the steps around it, the spec has an "As built" section and the owner's word on its status, and a run on a fresh clone in a scratch `HOME` is recorded.
**Dependencies:** F.
**Affected areas:** `INSTALL.md`, `README.md` (the draft note), `docs/specs/clone-enrollment.md`, `docs/plans/` (this plan's Result).
**Steps:**
1. Run the steps of the page on a fresh clone with a scratch `HOME`, as far as the owner-run steps allow, and record what was run. After `enroll`, run `wb check`, `wb doctor` and the preview of `acknowledge` on that clone and record that none gives the "treated as new" refusal.
2. Correct `INSTALL.md` from what built and ran; remove the "draft" and "unverified" marks only for what ran.
3. Tell the owner what to run on the second machine.
**Verification:** `wb check`; the page's commands on the scratch clone.
**Evidence:** one local commit, trailer `#G`.

### Increment H — The owner's run on a second machine

**Outcome:** the owner's run of the setup page on a second machine is recorded in this plan's Result, and the plan is completed only if it passed.
**Dependencies:** G.
**Affected areas:** this plan's Result and status; `docs/specs/clone-enrollment.md` (its status, by the owner's word) and `INSTALL.md` (corrections from what the run shows).
**Steps:**
1. The owner runs the page on the second machine, with the new `wb enroll` after the first run of the workbench and the approval step, and pastes the output.
2. I record what was run and the result in the Result. A step that fails is a finding: I diagnose it, fix it as a new increment (`H-A`) if it is a defect, and the owner runs again.
3. When it passes, I set the plan `Completed` and tell the owner the spec is ready for their word to read `Current`.
**Verification:** the output of the owner's run, quoted as run; `wb check` in this repository.
**Evidence:** one local commit, trailer `#H`, holding the plan's Result and status and any correction to `INSTALL.md`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later one changed its inputs; the new tests of B to D and the registration of E are rerun after F's fixes. The whole installer suite is run once, at E, for the named reason. The second machine is the owner's run, recorded at H.

## Risks and sensitive actions

- **This command writes trust state.** A mistake could mark a changed clone as trusted. The owner's typed digest, the strict manifest read, the approval check and the re-read after the answer bound it, and F reviews it.
- **The installer is imported by the hooks.** A half-applied edit can lock every tool; each code increment is applied in one scripted pass after tests in a scratch copy.
- **Rendering changes the deny rules.** Until the owner runs `wb rerender` after E, the new command is not denied to the agent by the harness; the command itself refuses without two terminals.
- **A package write is not needed.** Nothing under `packages/` changes, so the package lock does not apply.

## Review record

Empty until a review is asked for.

## Deferred work

None identified.

## Result

Empty until work starts.
