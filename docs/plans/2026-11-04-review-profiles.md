# Review profiles in the guarded store

Status: Proposed
Created: 2026-11-04
Candidate: workbench-v1#review-profiles
Specs: review-engine, action-review, model-bridge, module-contract, command-permissions, installer-interface, trust-and-approval

## Goal

The bridge, model and effort of a review are read from the owner's `review-profiles.json` in the guarded store, chosen by a ladder for
each kind of review, and no project file sets them. This builds the two accepted records
`2026-11-04-review-profiles-in-the-guarded-store` and `2026-11-04-delegated-approval-checks-the-profile-of-the-last-round`. When it is
done: both engines read the profile file and `.workbench/review.json` is read by neither; a round uses the rung of its place in the
window and records the profile and the request it resolved to; a module can declare the options a review may pass, and the Ollama
bridge's `server` and `thinking` options travel in a profile; a delegated plan approval can be limited by the owner's
`delegate-profiles` setting to a review whose last round ran on a listed profile; `wb install` writes a default file when none exists;
and `wb doctor` reports the profile file's problems.

## Scope

- A specification of the file, the ladders, the options a module declares and the setting, and the corrections it makes to the
  specs of the two engines, the bridge contract and the module contract.
- One strict reader of the file in the kit, shared by the review engine, the action-review engine, the installer and `wb doctor`.
- The module declaration of the options a review may pass, its refusals and `wb verify`, with the Ollama bridge's options.
- The review engine: the file in place of `review.json`, the ladder, the record of each round, and `status`.
- The action-review engine: its one-rung ladder in place of its own reader of `review.json`.
- The `convergence` report's new field, the owner's `delegate-profiles` setting and the installer's check.
- The default file written by `wb install`, and the checks of `wb doctor`.
- A walk-through in a scratch store, and the specs and documents as built.

## Non-goals

- A per-project choice of ladders, kept in the store. A tracked review setting of any kind. A call-time `--profile`.
- A check of a profile against a vendor's own model list.
- A change to the tuning kept in `bridge-endpoints.json`, to `ask-codex`, or to the contract of a bridge.
- Putting the profile or the request into the approval record, which needs a new format of that record.
- Refusing a gating profile that names no model: `wb doctor` warns, as the record says.
- Finding the cause of the intermittent `reply_too_large` of the review engine.

## Assumptions and constraints

- The roadmap candidate depends on `ask-ollama-bridge` and `bridge-model-configurations`. Both plans, `2026-11-01-ask-ollama-bridge` and
  `2026-11-02-bridge-model-configurations`, read `Completed` when this plan was drafted, and the Ollama options and the endpoint file
  that increments C, D and J rely on are those they built.
- The two records above are accepted and outrank this plan and the code. Until the engines are built, they still read `review.json`.
- The store root tolerates a further file. The records state it as an inference from `workbench/store.py`; increment B tests it.
- A helper reaches the store by a fixed path under the home directory through the kit's no-follow layer, and the kit has no store
  accessor. A reader in the kit may be a kit change with a new API number. Increment B reads the kit's rules first and stops if the
  change is larger than one commit.
- Every edit under `packages/` changes module hashes and closes the command gate until the owner releases approvals, so those increments
  are built in a scratch clone by a scripted pass and the owner copies the files and releases, as in the earlier plans. The increments
  that edit `packages/` are C, D, E, F and H.
- `workbench/*.py` is imported by the hooks, so every edit to it is atomic: the new text is checked to compile before it is written.
- The plan `2026-11-03-module-conformance-levels-and-hooks` is drafted, not reviewed or approved, and also edits `declarations.py`,
  `module-contract.md` and the `review-engine` declaration. This plan does not depend on it. Whichever lands second rebases onto the
  first.
- The owner's `review-profiles.json` must exist before increment D is released, or the engines refuse. The owner writes it by hand;
  increment D gives the lines.

## Completion criteria

1. `docs/specs/review-profiles.md` states the file, the ladders, the options a module declares, the status values and the setting as
   built, and the specs of the two engines, the bridge contract and the module contract agree with it.
2. The reader refuses, with a reason that names the rule and never the value, every malformed file: a duplicate key, an unknown field,
   an oversize file, a bad name, a ladder of more than five rungs, a ladder that names a profile the file lacks, a profile that holds a
   reserved option, and a file in the wrong format.
3. A module declares the options a review may pass; a declaration that lists `model`, `effort`, `timeout`, `schema`, `root` or
   `confine` is refused; and a profile passes only declared options with values that fit the stated grammar.
4. The review engine runs the nth round of a window on rung n, repeats the last rung, spends no round on a bridge error, records the
   profile and request of each round, starts a reset window on the first rung, refuses with a message that names the file and how it
   is made when the file is missing or invalid, and never reads `.workbench/review.json`. `status` prints the next round's profile.
5. The action-review engine runs the one rung of its own ladder, refuses a longer one, and never reads `review.json`.
6. `converged` means what it meant. With `delegate-profiles` at `any`, delegated approval behaves as it does today. With a list, it is
   refused for every case that the record names and accepted only for a round whose recorded request equals a listed profile.
7. `wb install` writes the default only when the file is absent, shows it in its preview, binds it to the `ask` digest, never
   overwrites, and never chooses a vendor. `wb doctor` reports a missing or invalid file, a ladder name that dangles, a bridge that is not
   installed and an unused `review.json` (increment J), and a `delegate-profiles` name that dangles or a listed profile that names no
   model (increment I).
8. The walk-through in a scratch store shows each of the above, the targeted tests pass, `wb check` and the plan check report no
   problems, and the shipped approvals are current.

## Increments

### Increment A — The specification

**Outcome:** `docs/specs/review-profiles.md` exists as a draft and states the file, its bounds and name rules, the profile fields, the
ladder rules, the options a module declares, the record of a round, `status`, the install default, the `wb doctor` checks, the
`convergence` field and the `delegate-profiles` setting. The specs it touches say what is true now and what is not built.
**Dependencies:** the completed plans `2026-11-01-ask-ollama-bridge` and `2026-11-02-bridge-model-configurations`, whose `Status:` lines step 1 rereads.
**Affected areas:** `docs/specs/review-profiles.md` (new); the sections of `review-engine.md` ("The project setting", the rounds and
`status`), `action-review.md` ("Settings and the bridge", and the sentence that no helper can read the guarded store),
`model-bridge.md`, `module-contract.md`, `command-permissions.md` (the settings), `installer-interface.md` and `trust-and-approval.md`.
**Steps:**
1. Reread the `Status:` lines of the two plans this depends on and stop if either is not `Completed`. Read the two accepted records,
   `review-engine.md`, `action-review.md`, `ask-ollama.md` and `module-contract.md`.
2. Write the specification from the records. Where a record leaves a number to the specification (the file's size bound, the bound on
   profiles, the bound on the `delegate-profiles` list, the name rule), choose it and give the reason.
3. Correct the lines of the other specs that the records make false, and mark what is not built.
4. Run the document check.
**Verification:** `wb check` and the plan check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#A`. The spec stays `Draft` until the owner
approves it.

### Increment B — The reader in the kit

**Outcome:** one strict reader of `review-profiles.json` and one function that names the profile for a review kind and a round, usable
by the engines, the installer and `wb doctor`. A test confirms that a file in the store root is tolerated.
**Dependencies:** A.
**Affected areas:** `workbench/wbkit/` (a new reader), the tests of the kit under `tests/`, `docs/specs/review-profiles.md`, and the
kit's own specification if the kit's API number changes.
**Steps:**
1. Read how the kit reaches a fixed path under the home directory, how the review engine reads its seal key, how the endpoint file
   is read in `ask-ollama`, and the rules for the kit's API number. If the change is larger than one commit, stop and report.
2. Write the tests first: a valid file; each refusal of criterion 2; a ladder that falls to `default` for a document kind and never for
   `action-review`; the rung for round n, with the last rung repeated; the file in the store root.
3. Build the reader on the kit's strict JSON and no-follow layer, with the bounds the specification chose.
4. Update the specification where the build shows a gap.
**Verification:** the new tests, the kit's tests (`tests/test_kit.py`, `tests/test_kit_readers.py`, `tests/test_safefs.py`) and
`tests/test_store.py` for the store root.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#B`.

### Increment C — The options a module declares for a review

**Outcome:** a module's command declaration may list the options a review may pass, with the grammar of each. The reader refuses a
reserved name, and `wb verify` refuses a declaration that does not fit. The Ollama bridge declares `server`, `thinking`, `context` and
`max-output`; `ask-codex` declares none.
**Dependencies:** A.
**Affected areas:** `workbench/declarations.py`, `workbench/verify.py`, `packages/workbench/ask-ollama/module.json` (a package edit),
`docs/specs/module-contract.md`, `tests/test_declarations.py`, the Ollama module test. The overlap with the conformance plan is
recorded in the Assumptions.
**Steps:**
1. Read `declarations.py`, the arguments the Ollama helper accepts and the grammar of each of the four options.
2. Write the tests first: a declaration with the options; each reserved name refused; a value outside a stated grammar; an unknown field.
3. Build the field, its refusals and its check in `wb verify`; declare the four options in the Ollama module.
4. Update the module contract and the Ollama spec.
**Verification:** the new and changed declaration tests, the Ollama module's tests, and `wb verify` on the package.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#C`. The package edit needs a scripted pass and
the owner's release.

### Increment D — The review engine reads the profile file

**Outcome:** the review engine reads the profile file and the ladder, passes only the profile's model, effort and declared options,
records the profile and the request of each round, and no longer reads `.workbench/review.json`. A missing or invalid file is refused
with a message that names the file and how it is made.
**Dependencies:** B and C.
**Affected areas:** `packages/workbench/review-engine/helper/review-engine` (`read_setting`, the round, the saved fields),
the engine's `module.json`, its tests, `docs/specs/review-engine.md`.
**Steps:**
1. Read `read_setting`, `run_round`, the round entry and the seal, and the tests that use a setting.
2. Write the tests first: round n uses rung n and the last rung repeats; a bridge error spends no round and retries the same rung; the
   first round after `reset` uses the first rung; `extend` stays within five rungs; a missing and an invalid file are refused with
   the message; `review.json` is ignored; a profile that names an uninstalled bridge refuses the round; an option the module did not
   declare is never passed; the round entry holds the profile and the request.
3. Replace the reader and the request, add the record fields, keep the bridge call otherwise as it is.
4. Update the specification. If this grows beyond one reviewable commit, stop and report.
5. Give the owner the lines of the file to write before the release.
**Verification:** the review engine's tests, the changed test of the engine's module declaration, and the tests of the kit.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#D`. The package edit needs a scripted pass and
the owner's release, and the owner writes `review-profiles.json` before it.

### Increment E — `status`, the next profile and the skill

**Outcome:** `status` prints the profile of the next round and the location class of its server, and gives `request` the meaning of
the record. The `peer-review` skill tells the agent where the setting is and to stop when it is refused.
**Dependencies:** D.
**Affected areas:** the engine's `status`, the `peer-review` skill under `packages/workbench/review-engine/harness/`, their tests,
`docs/specs/review-engine.md`.
**Steps:**
1. Read `status` and the skill.
2. Write the tests first: `same` and `changed` against the profile that the last round's rung names; `next` printed; a server's
   location class printed; `unreadable` when the file is refused.
3. Build them and update the skill's first step.
**Verification:** the engine's `status` tests and the harness file tests.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#E`. The package edit needs a scripted pass and
the owner's release.

### Increment F — The action-review engine reads its one-rung ladder

**Outcome:** the action-review helper reads the `action-review` ladder through the kit reader, runs that one rung, refuses a longer
ladder, and no longer reads `review.json`. The time budget is unchanged.
**Dependencies:** B and D.
**Affected areas:** `packages/workbench/action-review/helper/action-review` (its own `read_setting`), its tests,
`docs/specs/action-review.md`.
**Steps:**
1. Read the helper's reader, its bridge call and the time budget.
2. Write the tests first: the one rung is used; a longer ladder, a missing ladder and a missing file are refused as no verdict; an
   uninstalled bridge is a refusal; the call still gets the time left of the budget.
3. Replace the reader and update the specification.
**Verification:** the action-review tests for the bridge, the module and the parser.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#F`. The package edit needs a scripted pass and
the owner's release. The shadow hook is not changed.

### Increment G — The installer reads the new `convergence` report

**Outcome:** the installer reads a `convergence` object of format 1 or 2, with the `last_requested` field, and treats a missing or
null value as an unknown request. Its behaviour is unchanged until the engine emits format 2.
**Dependencies:** A.
**Affected areas:** `workbench/approvalcmd.py` (`parse_convergence` and its size cap), `workbench/delegation.py`, `tests/test_delegation.py`,
`docs/specs/review-engine.md` ("Convergence"), `docs/specs/trust-and-approval.md`.
**Steps:**
1. Read `parse_convergence`, the check in `delegation.py` and their tests.
2. Write the tests first: format 1 reads as unknown; format 2 with each field; an oversize report; an extra field refused.
3. Build the reader for both formats with the restated size cap.
**Verification:** `tests/test_delegation.py` and `tests/test_approvalcmd.py`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#G`.

### Increment H — The engine reports what was asked

**Outcome:** the review engine's `convergence` prints `format` 2 with `last_requested` (bridge, model, effort, options and profile name,
or null for what the round did not record), and the meaning of `converged` is unchanged.
**Dependencies:** D and G.
**Affected areas:** the `convergence` code of `packages/workbench/review-engine/helper/review-engine`, its tests,
`docs/specs/review-engine.md`.
**Steps:**
1. Read the convergence code and the rounds that are stored before D.
2. Write the tests first: a round after D reports its request and profile; a round before D reports null; `converged` is the same for
   every case of the existing tests.
3. Build the field and the new format number.
**Verification:** the engine's convergence tests and `tests/test_delegation.py`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#H`. The package edit needs a scripted pass and
the owner's release.

### Increment I — The `delegate-profiles` setting and the installer's check

**Outcome:** the owner's settings hold `delegate-profiles`, `wb settings` prints it, a delegated approval with a list is refused or
accepted by the comparison and the fail-closed cases of the record, and `wb doctor` reports a listed name that dangles and a listed
profile that names no model.
**Dependencies:** B, G and H.
**Affected areas:** `workbench/settings.py` (a new file version), `workbench/settingscmd.py`, `workbench/delegation.py`, `workbench/doctor.py`, the registry of
facts where the setting is listed, `tests/test_settings.py`, `tests/test_settingscmd.py`, `tests/test_delegation.py`, `tests/test_doctor.py`,
`docs/specs/command-permissions.md`, `docs/specs/trust-and-approval.md`.
**Steps:**
1. Read `settings.py` (the versions and the strict loader), `settingscmd.py` and the gate in `delegation.py`.
2. Write the tests first: `any` changes nothing; an empty list, a list with `any`, a duplicate, a non-string, a long list and a damaged
   entry each refuse and are never read as `any`; a match accepts; a profile edited after the round, a missing name, an unreadable
   file, an unknown request and an invalid listed profile each refuse; the setting only counts while `approve-plan` reads `delegated`;
   `wb doctor` reports a listed name that is not in the file and a listed profile that names no model.
3. Build the file version, the printing and the comparison on the normal form of the record.
4. Update the specs in the same commit.
**Verification:** the four test modules named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#I`.

### Increment J — The install default and `wb doctor`

**Outcome:** `wb install` writes the default `review-profiles.json` when it is absent, shown in the preview and bound to the `ask`
digest. `wb doctor` reports the file's problems of criterion 7 (the checks of the delegated setting are increment I's).
**Dependencies:** B, C and D.
**Affected areas:** `workbench/install.py`, `workbench/installplan.py`, `workbench/preview.py`, `workbench/askdigest.py` if the digest
inputs change, `workbench/doctor.py`, `workbench/store.py`, `tests/test_install_levels.py`, `tests/test_install.py`, `tests/test_doctor.py`,
`docs/specs/installer-interface.md`, `docs/specs/command-permissions.md`.
**Steps:**
1. Read how install writes to the store, the preview and the digest it binds, and `doctor.py`.
2. Write the tests first: a default for `ask-codex`; a default for `ask-ollama` from a valid endpoint file; no profile for a record
   with no `default_model`; ladders only for one family and only for a profile that was made; no file when no bridge is installed;
   an existing file never changed; the digest changes with the bytes; the preview prints what an old `review.json` said as data.
3. Build the writer, the preview lines and the checks.
4. Update the specs. If this grows beyond one reviewable commit, stop and report.
**Verification:** the install, preview and doctor tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#J`.

### Increment K — Walk-through and the specs as built

**Outcome:** a walk-through in a scratch store with a scratch `HOME` shows the install default, a review that climbs its ladder, the
refusals, `status`, and a delegated approval limited by `delegate-profiles`; the specs say what is built.
**Dependencies:** A to J.
**Affected areas:** the Result of this plan, `docs/specs/review-profiles.md` (to `Accepted` by the owner), the sections the earlier
increments marked not built, `docs/development.md`.
**Steps:**
1. Write the walk-through script. It sets a scratch `HOME` for every command and uses a fake bridge, so no model is called, nothing is
   spent and the owner's store is not touched.
2. Run it; the owner runs any step that needs a terminal.
3. Record the evidence with its limits and provenance, and update the specs to what is built.
**Verification:** the document check and the plan check. A wider run is named only with the specific risk: increment B changed the kit
that every module imports, so the owner decides whether the module test roots that use the kit are run.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#K`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs, and only what that change invalidated is rerun.
The specific wider risk is the kit: every module's helper imports it, so a change there could break a helper that no increment names. The
agent tells the owner what could break before any run wider than the plan names, and the owner decides.

## Risks and sensitive actions

- **Security-relevant surfaces.** Helpers read a file in the guarded store (B, D, F). A file's values become arguments of a subprocess
  (C, D). The delegated approval path changes (G, H, I). `wb install` writes the store (J). For each, the agent asks the owner once whether
  to run a security review with an installed module that provides `security-review`, and runs it only if the owner says so.
- **The owner's own clone.** After D is released the engines refuse until `review-profiles.json` exists, so the owner writes it first.
  If the order is wrong, reviews and the shadow hook stop until the file is written.
- **Releases.** C, D, E, F and H edit `packages/`. Each needs a scripted pass and the owner's release between passes. They are built in a
  scratch clone and the owner copies the files.
- **The kit.** B may change the kit's API number, which every module sees. The step to stop and report is written into B.
- **The delegation gate.** G to I change the path by which an agent can obtain a recorded approval. The check fails closed, the
  default `any` keeps today's behaviour, and the comparison is tested for each refusal case.
- **The conformance plan.** It edits the same files as C. The second to land rebases onto the first.
- **The review of this plan.** The review engine's `reply_too_large` has been intermittent; if it recurs, the agent stops and reports.
- **The record's inference** that the store root tolerates a further file is tested in B before anything relies on it.

## Review record

Empty until a review is asked for.

## Deferred work

- A per-project choice of ladders, kept untracked in the store.
- A tracked review setting that can only narrow what the machine allows.
- A refusal, not only a warning, for a listed profile that names no model, and a check of the model the bridge reported.
- A check of the profiles against a vendor's own model list, by a bridge that declares the read.
- The profile and the request in the approval record.
- The cause of the review engine's `reply_too_large`.

## Result

Empty until work starts.
