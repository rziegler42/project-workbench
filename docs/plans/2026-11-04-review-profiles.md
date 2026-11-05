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

### Increment D-A — Harden the profile options after the security review

**Outcome:** a profile or a declaration cannot name an option that is a prefix of a name the engine sets (`model`, `effort`,
`timeout`, `schema`, `root`, `confine`), so a bridge that accepts abbreviated options cannot read it as one of those; and the kit and
the specs say exactly what the engine does and does not check. This answers the security review of increments B to D (2026-11-04):
no Critical, High or Medium finding and seven Low ones, whose fixes are this increment's.
**Dependencies:** D.
**Affected areas:** `workbench/wbkit/profiles.py`, `workbench/declarations.py`, `tests/test_kit_profiles.py`,
`tests/test_review_options.py`, `docs/specs/review-profiles.md`, `docs/specs/review-engine.md` and `docs/specs/model-bridge.md`.
Nothing under `packages/` changes: the engine's own check of a stored round is left as it is, because a stored round is written by
the engine from a validated profile and a forged one is within the known threat model (finding L7), so no release is needed.
**Steps:**
1. Read the security review's findings L1 to L7 and the code they name.
2. Write the tests first: every non-empty prefix of every reserved name is refused as an option of a profile and as a declared review
   option; a name that only begins with a reserved word (`model-id`) or shares a first letter without being a prefix (`server`) is
   still accepted; and a fake bridge that reads options with prefix matching shows that `--mod x` would have overridden `--model`.
3. Build one function in the kit that says whether a name is reserved or a prefix of a reserved name, and use it in the profile
   reader and in the declaration reader.
4. Correct the text: criterion 3 says the engine passes the options of the profile and the bridge refuses one it does not accept (L1);
   the model name and the option values are recorded in the review's state in the project, so nothing sensitive belongs in them (L3);
   a new engine on a kit without `profiles.py` fails to start and an older engine reads a round of the new shape as unusable, and
   recovery is to delete the review (L4); the kit's docstring says that only the last part of the store path is refused when it is a
   link (L5) and that `HOME` moves the whole store (L6); the rung is chosen from the sealed state, which an agent that can read the
   key can forge, as `converged` can (L7); a bridge matches option names exactly (`model-bridge.md`).
**Verification:** the new tests, `tests/test_kit_profiles.py`, `tests/test_review_options.py`, `tests/test_declarations.py`,
`tests/test_kit.py` and `tests/test_verify.py`; and the review engine's own folder, because the reader its tests use changes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#D-A`.

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
ladder, and no longer reads `review.json`; the owner's test-set runner takes its model and effort from the same rung. The time budget
is unchanged.
**Dependencies:** B and D.
**Affected areas:** `packages/workbench/action-review/helper/action-review` (its own `read_setting`), the owner's test-set runner
`packages/workbench/action-review/tools/run_testset.py`, their tests (including the scaffold of
`tests/test_actionreview_dangerous.py`, which writes the setting into each scratch project), `docs/specs/action-review.md`.
*(The runner was added to this increment on 2026-11-04, when the build found that it reads `.workbench/review.json` and that its
cases would all be refused once the engine stops reading that file.)*
**Steps:**
1. Read the helper's reader, its bridge call and the time budget.
2. Write the tests first: the one rung is used; a longer ladder, a missing ladder and a missing file are refused as no verdict; an
   uninstalled bridge is a refusal; the call still gets the time left of the budget.
3. Replace the reader and update the specification.
4. The runner reads the owner's real `action-review` rung through the kit reader (the checkout's own kit), requires that rung's bridge to
   be `ask-codex` (the only sign-in plumbing it has) and otherwise ends the run before anything is sent, and writes that profile as
   the `review-profiles.json` of each scratch home in place of a `review.json`. Its own copy of the model and effort patterns goes
   away, and the scaffold writes the profile file into the scratch home.
**Verification:** the action-review tests for the bridge, the module and the parser, the runner's tests and the end-to-end tests of
the dangerous cases.
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
`docs/specs/command-permissions.md`, `docs/specs/trust-and-approval.md`, `docs/specs/review-profiles.md` (its status tags and the text on
the ladder keys), and, added on 2026-11-05 when the build found that `tests/test_boundary.py` was failing, `tests/test_kit_profiles.py`
(increment B) and `tests/test_approvalcmd.py` (increment G), whose fixtures name modules that the installer's tests may not name.
*(The installer takes the ladder keys from the profile file because it may not name a kind of review, so it checks the profiles and the
names a ladder uses, and each engine keeps its own keys and its single rung; the registry of facts of the levels has no entry for this
setting, because it is not a level.)*
**Steps:**
1. Read `settings.py` (the versions and the strict loader), `settingscmd.py` and the gate in `delegation.py`.
2. Write the tests first: `any` changes nothing; an empty list, a list with `any`, a duplicate, a non-string, a long list and a damaged
   entry each refuse and are never read as `any`; a match accepts; a profile edited after the round, a missing name, an unreadable
   file, an unknown request and an invalid listed profile each refuse; the setting only counts while `approve-plan` reads `delegated`;
   `wb doctor` reports a listed name that is not in the file and a listed profile that names no model.
3. Build the file version, the printing and the comparison on the normal form of the record.
4. Update the specs in the same commit.
5. Replace the module names in the fixtures of `tests/test_kit_profiles.py` and `tests/test_approvalcmd.py` with neutral names, without
   changing what they test, so that `tests/test_boundary.py` passes again.
**Verification:** the four test modules named above, `tests/test_boundary.py`, `tests/test_kit_profiles.py`, `tests/test_approvalcmd.py`
and the drift test of the ladder keys of the three readers that may name modules (increment F, in the action-review package).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#I`.

### Increment I-A — Close the findings of the security review of increment I

**Outcome:** the delegated-approval gate decides from one reading of the owner's settings, so a file replaced or damaged between two
reads cannot read as `any`; it refuses when more than one installed module could be the bridge of a listed profile; and an entry in a
file older than version 4 prints one problem and not two. This answers the security review of increment I (2026-11-05): no Critical,
High or Medium finding, one Low (the second read) and two small points; its other point (`wb doctor` does not report an unusable
bridge) belongs to increment J.
**Dependencies:** I.
**Affected areas:** `workbench/delegation.py` (`_profile_gate`, `_unusable`), `workbench/settings.py` (the unknown-entry note),
`tests/test_delegation.py`, `tests/test_settings.py`, `tests/test_settingscmd.py`, `docs/specs/trust-and-approval.md`. No package changes.
**Steps:**
1. Read the review's findings L1, I1 and I3 and the code they name.
2. Write the tests first: with the settings read once, a file that stops delegating, is damaged, holds a duplicate key, is of an
   unsupported version, or loses the entry or holds `any` after the first read all refuse and none of them reaches the profile check
   (the gate takes the loaded settings and the process module as arguments, so the test passes it each state); two installed modules
   that provide `model-bridge` with a command of the bridge's name make a profile unusable; an entry of `delegate_profiles` in a file
   of version 1, 2 or 3 prints exactly one `settings:` line and its reading is still invalid.
3. Make `delegate_approve_plan` load the settings once and pass that reading to `_profile_gate`, which decides both whether the
   checkpoint still reads `delegate` and what `delegate_profiles` holds from that one reading, and treats an absent entry as `any`
   only when the reading had no problem; make `_unusable` refuse when more than one module matches; drop the loader's unknown-entry
   note for `delegate_profiles`, which its own problem already covers.
4. Update the specification where it describes the order of the checks.
**Verification:** the new tests, `tests/test_delegation.py`, `tests/test_settings.py`, `tests/test_settingscmd.py`, `tests/test_doctor.py`,
`tests/test_boundary.py`, and the wide set of tests that read the settings.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#I-A`.

### Increment J — The install default and `wb doctor`

**Outcome:** `wb install` writes a default `review-profiles.json` when it is absent, built only from the model-bridge modules that are
installed and naming no vendor, shown in the preview and bound to the `ask` digest. `wb doctor` reports the problems of the file, of
each profile against its bridge, and of an old `.workbench/review.json`. *(Changed on 2026-11-05, before J was built: the first text
had the installer write an effort ramp for one bridge and a profile for each record of another bridge's endpoint file, which names
those modules in the installer's code and so breaks `tests/test_boundary.py`, which allows no exemption. The owner chose the generic
default, in the spirit of the earlier decision "default model only": one profile that names its bridge and nothing else, so that each
bridge's own default model stands. The effort ramp and per-endpoint profiles are the owner's to add by hand.)*
**Dependencies:** B, C, D and I.
**Affected areas:** `workbench/install.py`, `workbench/installplan.py`, `workbench/preview.py`, `workbench/askdigest.py` if the digest
inputs change, `workbench/doctor.py`, `workbench/store.py`, `workbench/delegation.py` (the usable-profile check is shared with the
doctor), `tests/test_install_levels.py`, `tests/test_install.py`, `tests/test_doctor.py`, `tests/test_boundary.py` (run, not changed),
`docs/specs/installer-interface.md`, `docs/specs/command-permissions.md`, `docs/specs/review-profiles.md`.
**Steps:**
1. Read how install writes to the store, the preview and the digest it binds, and `doctor.py`.
2. Write the tests first, with made-up bridge modules (the installer's tests name none of the real ones):
   - the default: one profile for each installed, pinned module that provides `model-bridge`, named by the bridge's command and
     holding `bridge` only (no model, no effort, no options); a bridge whose name is not a profile name makes no profile and the install
     says why; the two ladders `default` and `action-review` are written only when exactly one profile was made, each naming it; with
     several bridges the profiles are written and no ladder is, and the install says that a review is refused until the owner chooses;
     with no bridge no file is written;
   - the file: written only when absent; an existing file is never changed, whether valid, invalid, a link or a directory; what is
     written passes `settings.read_profiles` and the kit reader; nothing outside the guarded store root is touched;
   - the preview and the digest: the preview prints the bytes that will be written (or says none will be), the digest at `ask` changes
     with the bytes and with nothing else of this feature, and a run with the wrong digest writes nothing;
   - the old file: the preview prints what an old `.workbench/review.json` said, as data, only the four known fields, each as ASCII
     with escapes and cut at 128 characters, and one line saying so when it is over 4,096 bytes or malformed; the text is not part of
     the digest and changes nothing that is written;
   - `wb doctor`: a missing file when a model bridge is installed, an invalid file, a ladder that names an absent profile, a profile whose
     bridge is not installed, each profile against its bridge's pinned declaration with the delegated-approval check's rules (an
     undeclared option, a value outside its grammar, a broken exclusion), and a file at `.workbench/review.json` reported as unused.
3. Build the writer, the preview lines and the checks; share the usable-profile check with `delegation.py` rather than copying it.
4. Update the specs, including the acceptance criterion 9 of `review-profiles.md`. If this grows beyond one reviewable commit, stop and
   report.
**Verification:** the install, preview and doctor tests named above, `tests/test_delegation.py` (the shared check) and
`tests/test_boundary.py`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#J`.

### Increment J-A — Close the findings of the security review of increment J

**Outcome:** the preview ties each profile of the default file to the module that provides its bridge; an install whose profile file
path becomes occupied after the plan was made finishes with the file left as it is and does not stop partway; `wb doctor` reports a
store fault in one line and prints the rest of its report; and the code that was meant to show an old `.workbench/review.json` in the
preview, which can never run because `wb install` and `wb adopt` refuse a target that has a `.workbench` directory, is removed. This
answers the security review of increment J (2026-11-05): no Critical, High or Medium finding and five small ones.
**Dependencies:** J.
**Affected areas:** `workbench/profiledefault.py`, `workbench/preview.py`, `workbench/installplan.py`, `workbench/install.py` (`_write`),
`workbench/doctor.py`, `tests/test_profiledefault.py`, `tests/test_install.py`, `tests/test_installplan.py`, `tests/test_doctor.py`,
`docs/specs/review-profiles.md`, `docs/specs/installer-interface.md`. No package changes.
**Steps:**
1. Read the review's findings 1 to 5 and the code they name.
2. Write the tests first:
   - the profile line names the module and the command, and two selected modules whose bridge commands share a name make a note and one
     profile;
   - a profile file that appears after the plan was made, injected where the install records its plan, is not overwritten: the install
     ends with exit 0, the owner's bytes are kept, the output says the file was left as it is, the other store files are written, and
     no marker is left;
   - the doctor, with `SafeFsError`, `OSError` and `ValueError` raised from the store, the installed-module reader and the usable-profile
     check, reports one `review-profiles` problem line each time and the rest of its report;
   - the preview prints no line about an old project file, and no function for it remains.
3. Build the changes. For the occupied path: the plan marks the files whose write is skipped when the path is occupied at write time
   (the default profile file), `_write` skips them and says so, and every other store write keeps its refusal. The window between the
   check and the rename inside the kit's write (microseconds, and only the owner's account can create the file) is not closed here; the
   spec says so.
4. Update the specs: remove the old-file bullet, name the module in the profile line, state the write-time skip.
**Verification:** the new tests, `tests/test_profiledefault.py`, `tests/test_install.py`, `tests/test_installplan.py`, `tests/test_doctor.py`,
`tests/test_boundary.py`, and the wide set of install, adopt, preview, recover and unfinished tests.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-review-profiles#J-A`.

### Increment K — Walk-through and the specs as built

**Outcome:** a walk-through in a scratch store with a scratch `HOME` shows the install default, a review that climbs its ladder, the
refusals, `status`, and a delegated approval limited by `delegate-profiles`; the specs say what is built; the sentence of
`module-contract.md` on the reserved option names says that their prefixes are refused too; and the accepted record of the delegated
check carries a dated note about the one place the build differs from its wording.
**Dependencies:** A to J.
**Affected areas:** the Result of this plan, `docs/specs/review-profiles.md` (to `Accepted` by the owner), the sections the earlier
increments marked not built, `docs/development.md`, and, added on 2026-11-05 after the builds of D-A to J-A: `docs/specs/module-contract.md`
(the one sentence on the names that `commands[].review_options` refuses) and a dated note after the unchanged body of
`docs/decisions/2026-11-04-delegated-approval-checks-the-profile-of-the-last-round.md`, written only with the owner's approval of its
text. The roadmap candidate `review-profiles` is not edited: a roadmap does not record completion, and this plan's Result does.
**Steps:**
1. Write the walk-through script. It sets a scratch `HOME` for every command and uses a fake bridge, so no model is called, nothing is
   spent and the owner's store is not touched.
2. Run it; the owner runs any step that needs a terminal (an install is owner-run).
3. Record the evidence with its limits and provenance, and update the specs to what is built.
4. Correct the sentence of `module-contract.md`.
5. Draft the dated note for the decision record and show its text to the owner. It says one thing: the installer, which may not name a
   module or a kind of review, takes the ladder keys from the profile file, so its reading of the file checks the profiles and the names a
   ladder uses and does not refuse an unknown ladder key or an `action-review` ladder of more than one rung; each engine still does
   (increments I and J). Write it only after the owner approves the text.
**Verification:** the document check and the plan check, and `tests/test_boundary.py` and `tests/test_kit_profiles.py` for the
neutral names. A wider run is named only with the specific risk: increment B changed the kit that every module imports, so the owner
decides whether the module test roots that use the kit are run.
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

Reviewed by Codex (`gpt-5.6-terra`) through the review engine on 2026-11-04, at the owner's request: two rounds of the bound of 3, and
the second came back with no meaningful finding.

- **Applied (round 1, major):** the plan did not record or check the roadmap candidate's prerequisites. The assumptions now say that
  `2026-11-01-ask-ollama-bridge` and `2026-11-02-bridge-model-configurations` read `Completed` when the plan was drafted (verified), and
  Increment A depends on them and rereads their status lines first.
- **Applied (round 1, major):** the accepted delegated-approval record requires `wb doctor` to report a `delegate-profiles` name that
  dangles, and no increment owned it. Increment I now owns that check and the one for a listed profile that names no model, with tests;
  Increment J keeps the file's checks; criterion 7 is split to match.
- **Not applied (round 1 minor, repeated in round 2 with no new evidence):** the roadmap candidate said the two decisions were still
  proposed. A roadmap changes only with the owner's word; the owner gave it, and the two phrases were corrected in the commit that holds
  the plan.
- **Also read by a reviewer agent:** the two decision records this plan builds, in a separate pass (not this plan).
- **Limits:** the review is a second model's read of the plan's shape. File and test names in the plan were checked by the agent; the
  details left to the first steps of increments B and I (the kit's API-number rule and the settings file's versioning) were not.
- **Left for the owner:** the verdict on each increment, the releases that increments C, D, E, F and H need, writing
  `review-profiles.json` before increment D is released, whether to run a security review at each surface the Risks section names, and
  the plan's `Status:` line.
- **Increment D-A (added 2026-11-04, after the plan was approved and after increment D).** The security review of increments B to D
  found no Critical, High or Medium finding and seven Low ones, and D-A holds their fixes. The owner chose to put them in a nested
  increment and approved the changed plan through the `ask` flow (region `d94d2b96...ed18d07`). The addition was not sent to a second
  model: it is one increment taken from the review's own findings, it changes core files and documents only, and the increment itself
  gets a reviewer agent's read and a Result before its commit.
- **Review of increment D-A (2026-11-04, a `reviewer` agent, one exchange).** No blocking finding. It found the function correct at
  its edges (empty string, non-string, a full reserved name, a longer name, `model-id`, `server`, `context`), found the function used in
  exactly the two places the plan names, and found no other place in `workbench/` or `packages/` that accepts an option name. **Applied:**
  the stale wording at `review-profiles.md` (the declared-name rule and criterion 2) and in the docstring of `declarations.py`, which
  still listed only the reserved names. **Deferred, not applied:** `module-contract.md` (the sentence that says the six names are
  refused) is not among the plan's affected areas; it needs the owner's word to widen D-A, or a later increment. **Noted, not changed:**
  the engine's own check of a stored round keeps `name in profiles.RESERVED` by design (finding L7). **Limits of its evidence:** it could
  run nothing and read the files, not the diff; I checked the `ask-ollama` option parser myself: it matches names exactly.
- **Review of increment E (2026-11-04, a `reviewer` agent, one exchange).** No blocking finding. It found the `used` arithmetic
  identical to the round's, `next` right after `reset`, `extend`, a used-up window, a closed review, a refused file and a kind with no
  ladder, no path on which `status` refuses, and every failure of the class lookup reading `unknown`. **Applied:** four wording notes:
  the class is what the bridge reports and cannot be checked (spec and skill); the engine never opens the endpoint file but the bridge
  does when it runs `check`; `next` names the profile by place in the window and does not say a round is allowed (an unsealed state or
  an undecided finding refuses it). **Rejected:** none. **Limits of its evidence:** it ran nothing and did not open the new tests.
- **Increment F widened (2026-11-04, before it was built).** Reading the code showed that `tools/run_testset.py` also reads
  `.workbench/review.json` and that the scaffold of the dangerous-case tests writes it, so every case would have been refused once the
  engine stopped reading the file. The owner chose to widen F to the runner and its tests and approved the changed plan through the
  `ask` flow (region `f50c585d...5c3a`); the build stopped for that choice before any edit.
- **Review of increment F (2026-11-04, a `reviewer` agent, one exchange).** No blocking finding. By reading it confirmed that nothing reads
  `.workbench/review.json`, that no project file can choose the bridge, model, effort or options, that the time budget and `--confine`
  are unchanged and come first, that a profile option cannot override a reserved option, that `read_setting` cannot fail open, and that
  the runner refuses before it sends anything. **Applied:** the stale sentence of `action-review.md` about a pulled change to the
  setting file; the two "decided" tags of `review-profiles.md`; a rung with options is refused by the runner before the prompt (a test
  first: it ran the whole test set before the change). **Rejected:** the note that the test "the runner reads the review.json of
  nothing" is a weak negative, because the runner has no other route to a project path and the positive tests (the rung is the
  owner's) carry the claim; the note that `kit()` could fail to import inside the `except` clause, because `project_setting()` calls
  it first and an `ImportError` there already ends the run with nothing sent. **Limits of its evidence:** it ran no test and did not
  read the launcher.
- **Review of increment G (2026-11-04, a `reviewer` agent, one exchange).** No blocking finding. By reading it confirmed that every
  field of `last_requested` is held to the rules of the owner's profile file and matched with `fullmatch`, that the field set is exact
  in both formats and a format-1 report behaves as before, that `last_requested` is stored and printed nowhere yet, that no other
  caller of `Convergence(` or `parse_convergence` is affected, and that the three specs match the code. **Rejected, with reasons:** the
  note that `parse_convergence` checks the format before the field set (both orders refuse; the message for a wrong format is the more
  useful one); that `len(model) <= MAX_MODEL` repeats the profile rule's cap of 128 (harmless defence kept beside the report's own
  limit); that `_object` is now used only by `parse_delegable` and its preamble is repeated in `parse_convergence` (the delegable
  report stays untouched, and a shared helper would change a reader that this increment does not own). **Limits of its evidence:** it
  ran no test and did not open the new tests or the decision record.
- **Review of increment H (2026-11-04, a `reviewer` agent, one exchange).** No blocking finding. By reading it confirmed that
  `last_requested` shows only what the sealed state recorded (the model asked for, not the one the bridge reported, and not today's
  profile), that `"profile" in last` is the same test `check_round` uses for the old shape and cannot be fooled because the key set is
  exact, that `converged` and every other field are computed as before, that the state format and the report format are kept apart, and
  that the installer's reader accepts what the engine prints in both shapes. **Applied:** the docstring of `last_requested` now says
  exactly what `check_round` checks (the engine refuses a reserved option name but not a prefix of one, by design: finding L7 of the
  security review) and that the installer refuses what the profile rules refuse; the worst-case test now doubles every character of
  every option value and uses a non-ASCII reported model. **Rejected:** none. **Limits of its evidence:** it ran nothing and did not
  diff the trees.
- **Increment I widened (2026-11-05, before it was finished).** Running the wider tests showed that `tests/test_boundary.py`, which
  forbids the installer and its tests to name a module, had been failing since increments B and G (their fixtures name `ask-codex`,
  `ask-ollama` and `action-review`; the agent had not run it, because its verification was targeted), and that the installer's own
  ladder keys in the first design of I named `action-review`. The owner chose to widen I to those two test files and to the status
  tags of `review-profiles.md`, and approved the changed plan through the `ask` flow (region `0caab305...2187`). The owner also
  acknowledged one departure from the wording of the accepted record, item 5 ("the same strict rules as the engine"): the installer
  takes the ladder keys from the profile file, so it checks the profiles and the names a ladder uses and no longer refuses an unknown
  ladder key or a longer `action-review` ladder; each engine still does. The record is not edited; `review-profiles.md` says it.
- **Review of increment I (2026-11-05, a `reviewer` agent, one exchange).** One blocking finding, which the agent already knew: the
  untracked `tests/test_review_ladder_keys.py` (the installer's drift test, which named a module and the constants that no longer
  exist); the owner approved its removal from a dry-run list and the agent removed it. **Applied:** the gate's second read of the
  settings could, if the file were damaged between the two reads, read as `any`; `_profile_gate` now asks first whether `approve-plan`
  still reads `delegate` for the process module and refuses otherwise (a test first, with a damaged, an emptied, a stopped and a
  changed file). **Rejected:** that two installed modules could declare the same bridge command (the launcher refuses it at run time,
  `commands.py`, and the install refuses it); that "the registry of facts" lacks an entry (the registry lists level keys, and
  `delegate-profiles` is not a level). **Acknowledged, not a change:** the departure from item 5 of the record, above. **Limits of its
  evidence:** it ran nothing and did not open the new tests.
- **Security review of increment I (2026-11-05, at the owner's request; a `security-reviewer` agent working on copies with a fake store,
  fake modules and a faked pin check, nothing real started).** No Critical, High or Medium finding. Hostile reports of format 1 and 2
  (extra and missing fields, reserved option names and prefixes, bad values, duplicate keys, NaN, non-UTF-8, nesting, the 8,192 byte cap),
  every invalid `delegate_profiles` value and the entry in a file of version 1 to 3, the profile file (duplicates, oversize, nesting,
  links, a directory, a FIFO, a ladder naming a missing profile), the checks of `_unusable` and the normal form of the comparison were
  all refused or accepted as the record says, with fixed wording and no text of the file or the report in a refusal. **One Low
  finding and two small points,** all fixed in the nested increment I-A: L1 the gate reads the settings twice, and a second read of a
  file that was damaged or replaced in between reads as `any` (the owner alone can cause it, in a window of milliseconds); I1 `_unusable`
  uses the first module that matches and does not refuse on two (the launcher refuses duplicate commands at run time, so the worst case
  was a refusal); I3 an entry in a file older than version 4 prints an "unknown entry ... ignored" note beside its refusal. **Left to
  increment J:** `wb doctor` does not report an unusable bridge, a bad option or a grammar mismatch (I2). **Limits of the evidence:**
  the reviewer could not run the repository's tests or `delegate-approve-plan` end to end, and faked the pin check; the stack-exhaustion
  path of very deep nesting was not exercised. **Accepted by the decision, not a finding:** the gate compares the request the review
  recorded and not what ran, and the sealed state can be forged by the agent, the trust level `converged` already has.
- **Increment I-A (added 2026-11-05, after the plan was approved and after increment I).** Drafted from the review's findings; the owner
  chose a nested increment and approved the changed plan through the `ask` flow (region `38206554...6249`).
- **Review of increment I-A (2026-11-05, a `reviewer` agent, one exchange).** No blocking finding. By reading it confirmed that the gate
  has exactly one `settings.load` and that no other call in it loads the settings; that `settings.effective(loaded, process.checkpoints,
  ())` is the expression `planapprovals.delegating` used; that every damaged, duplicate-key, unsupported-version, non-file, emptied or
  changed state refuses before the entry is looked at; that `_unusable` refuses on none or on more than one match and cannot accept two;
  and that the loader still keeps its note for a misspelt key, an unknown key at version 4 and `profile` in a file older than 3.
  **Applied:** the spec wording ("read once by this check", with the command's earlier check of the setting named as a separate read);
  a test that pins the accepted case (below). **Judged right, as asked:** a file that still delegates but lost the entry, or holds `any`,
  is the owner's current setting and is accepted as `any`; refusing it would need a comparison with the first reading, which brings the
  second-read problem back. **Rejected:** none. **Limits of its evidence:** it ran nothing and did not confirm the duplicate-module cases
  of the manifest.
- **Increment J changed (2026-11-05, before it was built).** Reading the installer showed that the first text of J (an effort ramp for
  one bridge and a profile per endpoint record for another) names those modules in the installer, which `tests/test_boundary.py` forbids
  without exemption. The owner chose a generic default, in the spirit of the earlier decision "default model only", and approved the
  changed plan through the `ask` flow (region `7818ca2d...a155`).
- **Review of increment J (2026-11-05, a `reviewer` agent, one exchange).** No blocking finding. By reading it confirmed that an existing
  file of any kind (valid, invalid, a link, a directory) is left as it is and planned as nothing; that the bytes written are the bytes
  bound by the digest and the notes are not; that nothing a module, a command or the old project file contains can add a line or a
  control character to the preview; that the old file is read for display only, with no link followed and no blocking on a FIFO; that
  the doctor fails quiet and not false when the installed modules cannot be read; and that `wb recover` and `wb adopt` take the same
  path. **Applied:** the preview now prints the file exactly as it will be written (a test first), where it had printed a hash and a
  description; the spec names the per-profile doctor checks and says that the store write is a check followed by a rename. **Answered:**
  the bridges named are pinned, because `installplan.build` pins the helpers of every selected module in the same step. **Accepted, not
  changed:** a file that the owner creates in the milliseconds between the install's last look and its write is replaced, like any other
  store write of the install; the write refuses at once when the path is occupied (a test covers a file created after the preview).
  **Limits of its evidence:** it ran nothing and read no test.
- **Security review of increment J (2026-11-05, at the owner's request; a `security-reviewer` agent working on copies with a temporary
  store, made-up packages and a patched first-party check, nothing real started).** No Critical, High or Medium finding. Hostile
  package, module and command names (newlines, escapes, bidi marks, look-alikes, overlong text, 32 and 33 bridges, two `ask` commands),
  the preview (every line ASCII; the `| ` block hashes to exactly the bytes the digest binds; no text of a package or a file can forge
  the `digest:` line or a write line), an existing path of every kind at the store path (a FIFO, a link, a dangling link, a file, a
  directory), a hostile profile file under `wb doctor` (14 variants) and the written file (ASCII, 1,399 bytes at 32 profiles, mode
  0644 under umask 022) were refused or accepted as the spec says. A third-party package cannot provide the unprefixed `model-bridge`,
  so it cannot become the default bridge. **Five small findings,** all answered in the nested increment J-A: (1) a file that appears
  between the existence check inside the kit's write and its rename is replaced (microseconds, the owner's account only, the shape of
  every store write of the install), and a file that appears after the digest recheck aborts the install partway so that `wb recover`
  refuses; (2) the preview lines about an old `.workbench/review.json` can never appear, because `wb install` and `wb adopt` refuse a
  target that has a `.workbench` directory, so the code is dead (the Result of J said it was tested on the function; the cause was
  this, which the agent had not seen); (3) a very long integer `format` in those lines is unbounded, moot with (2); (4) the preview
  names the bridge's command and not its module; (5) `wb doctor` stops on a store fault it does not catch. **Limits of the evidence:**
  first-party status was patched in the tests; `pins` and `installed_modules` were not read in full; the doctor fault cases were
  injected; `wb recover` was not run end to end on a partial install; the overwrite race was injected, not timed.
- **Increment J-A (added 2026-11-05, after the plan was approved and after increment J).** Drafted from the review's findings; the owner
  chose the nested increment that skips an occupied path at write time, removes the dead code and keeps the kit's write as it is, and
  approved the changed plan through the `ask` flow (region `4521bcd6...d49e`).
- **Review of increment J-A (2026-11-05, a `reviewer` agent, one exchange).** No blocking finding. By reading it confirmed that the
  skipped write covers the default profile file and nothing else (`plan.optional_store`), that any other occupied store path still stops
  the install, that the profile write is the last of the plan's store writes so a skip leaves nothing missing after it, that a link, a
  directory or a FIFO at the path counts as occupied and is not followed, that the skip message is printed for an install and an adoption
  before the attach step, and that nothing refers to the removed code. **Applied:** the read of the profile file for a `delegate-profiles`
  list in `examine` caught only the kit's refusal, so a store fault there still stopped `wb doctor`; it now reports one
  `delegate-profiles` problem line and the report goes on (a test first, shown red by weakening the fix on purpose and green again);
  `installer-interface.md` says that a file that appears after the preview is left as it is. **Rejected, with a reason:** that the doctor
  should not catch `ValueError`: the security review proposed it, the doctor only reads, and a crash that hides the whole report is a
  worse outcome than a mislabelled line. **Limits of its evidence:** it ran nothing and did not read `ProfileDefaultInstall`.
- **Increment K widened (2026-11-05, before it was built).** The owner approved the changed plan through the `ask` flow (region
  `b12d977f...3c3a`): the one stale sentence of `module-contract.md` and a dated note on the delegated-check record, written only with
  the owner's approval of its text. The roadmap candidate was left alone on purpose: a roadmap does not record completion.
- **Review of increment K (2026-11-05, a `reviewer` agent, one exchange; a consistency read of the specs against the code).** It found no
  wrong number (bounds, caps, versions, budgets) and confirmed that the install default, the ladder keys, `next`, `request` and
  `convergence` match the code. It found **one false statement and seven smaller ones, all applied:** `command-permissions.md` still said a
  review needs `.workbench/review.json` (now: the owner's `review-profiles.json` with a ladder for the kind or a `default` one);
  `review-engine.md` kept a parenthesis that the action-review engine still read that file, and cited a section ("Status") that does not
  exist; `development.md` listed the owner's personal setting as not built and had a doubled article; criterion 1 of `review-profiles.md`
  said the kit checks "a value outside its grammar" (it checks the generic value rule; the grammar is the doctor's and the gate's); a
  sentence of the spec still read as unbuilt. It also found that the walk-through lacked a delegated approval, `wb doctor` and the
  oversize and duplicate-key refusals: the last two and the doctor and the declaration refusals were added and run; the delegated
  approval and the action-review rung are recorded as limits in the Result. Its question about the effort shown for the first round
  of the ramp has a plain answer: the `quick` profile names an effort and no model, so codex was given no model option, while `standard`
  and `deep` name both. **Left for the owner:** nothing of this review (the dated note was approved and written, and the spec was marked `Current`). **Limits of its evidence:** it ran nothing and did not open the walk-through script.

## Deferred work

- A per-project choice of ladders, kept untracked in the store.
- A tracked review setting that can only narrow what the machine allows.
- A refusal, not only a warning, for a listed profile that names no model, and a check of the model the bridge reported.
- A check of the profiles against a vendor's own model list, by a bridge that declares the read.
- The profile and the request in the approval record.
- The cause of the review engine's `reply_too_large`.

## Result

### Increment A — The specification (2026-11-04)

- **Done:** `docs/specs/review-profiles.md` is written as a `Draft`. It states the file (place, strict reading, a size bound of 32,768
  bytes, up to 32 profiles), the profile fields and the rule for each, the closed list of option grammars (`word`, `name`, `count`,
  `onoff`) and the field `review_options` that a module's command declaration carries, the ladder rules, what a round records, `status`,
  the action-review engine's one rung, the install default, the `wb doctor` checks, the `convergence` report's `last_requested` and
  format 2, and `delegate-profiles` (settings file version 4). It marks each section as decided and not built, with the increment that
  builds it, and it gives a reason for each number the accepted records left to it. Seven specs were corrected in place:
  `review-engine.md`, `action-review.md`, `model-bridge.md`, `module-contract.md`, `command-permissions.md`, `installer-interface.md`
  and `trust-and-approval.md`. Each carries a "decided, not built" note, and the sentences that called the owner's personal setting
  unreadable by a helper were corrected in the two engine specs (they were false: the review engine reads its seal key from the store).
- **Prerequisites:** the `Status:` lines of `2026-11-01-ask-ollama-bridge` and `2026-11-02-bridge-model-configurations` were reread and
  read `Completed`.
- **Verification as run:** `wb check` and `wb run code-work check` report no problems, and `git diff --check` is clean. No code changed,
  so no test was run. `wb plan-status` still reads `approved`.
- **Review:** one `reviewer` agent pass (read-only; it had no shell, so it did not see `git diff` or the checks). It found no blocking
  finding and eleven not blocking ones. Applied: (1) an Ollama profile name `local-<record name>` could exceed the 32-character rule, so
  a record whose name is too long gets no profile and the install says why; (2) the comparison now says that the bridge, model, effort
  and options must all be equal; (3) the file's reader checks only the file's own rules and the declaration-dependent checks run when a
  profile is resolved, so one uninstalled bridge cannot invalidate the file; (4) the engine refuses a model with a space or a leading
  `-`; (5) settings file version 4 is stated (it accepts what version 3 accepts, a new file is still seeded at 3, an older workbench
  stops safely); (6) the report's size cap is raised from 4,096 to 8,192 bytes with the arithmetic, for increment G to confirm; (7) the
  preview's text of an old `review.json` is bounded and escaped and is not part of the digest; (8) the stale sentences about the
  personal setting in `review-engine.md` and `action-review.md` were corrected; (9) and (10) acceptance criteria were widened. Noted and
  not changed: `model-bridge.md` says a bridge accepts nothing beyond its option table, while `ask-ollama.md` already adds options; that
  tension was there before, and the new paragraph now says "as the bridge-specific options of `ask-ollama.md` already are".
- **Not done:** the owner's reading of the spec, which stays `Draft`. No code. Nothing is pushed. The open point about where the engine
  learns a server's location class is written into the spec for increment E.
- **Left for the owner:** the verdict, the word to commit, and approval of the spec's numbers (they are proposals), the file size bound,
  the 32 and 8 limits, the grammar names and the field name `review_options`.
- **Committed** as b369478 (the owner's word to commit, 2026-11-04).

### Increment B — The reader in the kit (2026-11-04)

- **Kit rules read first (step 1).** A new module of the kit needs no new API number: `module-boundary.md` says a module added to the
  kit that changes none a helper imports needs none, and `identity.py` and `digest.py` were added that way. Rule 2 says the kit knows no
  document kind and no module, so the reader cannot hold the ladder keys; the caller passes the keys it accepts and the keys whose
  ladder holds one rung. That is a change from the plan's wording only in that the keys are an argument, and it is written into
  `review-profiles.md` and `module-boundary.md`. The change is one commit, so the increment did not stop.
- **Done:** `workbench/wbkit/profiles.py` (new). `parse(data, ladder_keys, single_rung_keys)` is a strict parser of the bytes;
  `read(ladder_keys, single_rung_keys)` reads the file by its fixed path under the home directory through the no-follow layer, bounded,
  and parses it; `for_round(found, kind, number, default_allowed)` returns the name and profile of rung n and repeats the last rung.
  `ProfileError` carries the file's name and a fixed reason and never the file's text or a path, and it keeps no earlier exception
  (`from None`), so a traceback cannot show a path either. The two keys arguments have no default, so a caller cannot forget the
  one-rung rule.
- **Tests first:** `tests/test_kit_profiles.py` was written before the module (the first run failed on the missing module), then
  widened after the review (see below) and run again before the fixes, when eight of them failed for the reasons they were written
  for. It has 59 tests: a valid file, each refusal of criterion 2 of the plan, the limits at their edges (including 32 profiles of
  every bound), hostile content (a repeated key below the top, deep nesting, a huge integer, a lone surrogate, a name with a trailing
  newline, a letter that is not ASCII), the marker test (no refusal repeats the file's text), the ladder rules, the default fallback,
  the reading cases (missing file, missing store, a link, a directory, an oversize file, a file that cannot be read, a home that is
  not absolute, no variable moving the file) and the store root.
- **The record's inference is confirmed:** a store made by `Store.ensure` takes `review-profiles.json` in its root, keeps it through a
  second `ensure` and refuses nothing. That tests `store.py` only. Whether `wb doctor` and the other readers of the real store
  tolerate the file is for increment J's tests.
- **Verification as run:** `python3 -B -W error -m unittest tests.test_kit tests.test_kit_readers tests.test_safefs tests.test_kit_profiles`
  reports 175 tests OK, and `python3 -B -W error -m unittest discover -s tests -p 'test_store.py'` reports 23 OK. The kit's own
  boundary tests caught two mistakes of my first version (a use of `compile`, and a module name in a docstring); both are fixed.
  `wb check` and `wb run code-work check` report no problems, and `git diff --check` is clean. The full suite was not run: only the
  kit is touched, no module imports the new file yet, and the owner decides any wider run.
- **Review:** one `reviewer` agent pass (read-only; it ran nothing). No blocking finding. Applied: `raise ... from None` at the two
  places where a refusal replaced another exception (the earlier exception held the path); the two keys arguments made required; the
  garbled wording of the one-rung message; a kind that is not text or is `default` is refused; the tests it found missing (an empty
  `ladders`, the bounds, more marker cases, trailing newlines, non-ASCII, a repeated key below the top, deep nesting, a huge integer,
  a null `options`, a missing store, a store that is a link, an unreadable file). Noted and not changed: `_problem` classifies the
  safefs text by substring, as `ask-ollama` does, so a home path containing a classifying word could be misread (the message is still
  clean); a file with more than one hard link is read, as the other readers do; the returned dictionaries are mutable; and importing
  `call.NAME` brings `subprocess` into every importer, which the kit allows and which avoids a second copy of the name pattern.
- **Not done:** nothing in the engines or the installer calls the reader yet (C onward). The drift test that compares the ladder-key
  sets of the callers belongs to the increment that adds the second caller (F).
- **Left for the owner:** the verdict and the word to commit. A security review: this increment reads an owner file by a fixed path
  and parses it as untrusted text; the agent asks once whether to run a security review with an installed module that provides
  `security-review`, and runs it only if the owner says so. Releases: none needed, since nothing under `packages/` changed.
- **Committed** as d212882 (the owner's word to commit, 2026-11-04) and pushed.

### Increment C — The options a module declares for a review (2026-11-04)

- **Done, in the live tree (core, uncommitted):** `workbench/declarations.py` reads `commands[].review_options`: at most 8 options, each
  `{"grammar", "excludes"}`. The option name has the form of an argument and is refused if it is a fixed field of a profile or an
  option the engine sets (`profiles.RESERVED`); the grammar is one word of the kit's closed list; `excludes` is a list of different
  names, each `effort` or another option of the command, never the option itself. The `Command` record gains a last field with a
  default, so no consumer changes. `workbench/wbkit/profiles.py` gains `GRAMMARS` (`word`, `name`, `count`, `onoff`) and `fits`; the
  declaration reader takes its closed list from the kit, so there is one definition. `wb verify` refuses what the reader refuses
  because it reads declarations through it.
- **Done, in a scratch clone only (package):** `packages/workbench/ask-ollama/module.json` declares `server` (`name`), `thinking`
  (`onoff`, excludes `effort`), `context` and `max-output` (`count`), and the module's test is updated. The live copies of these two
  files are unchanged, so the live package hashes and approvals are untouched until the owner copies them.
- **Tests first:** `tests/test_review_options.py` (new, 24 tests), a `Grammars` class in `tests/test_kit_profiles.py`, and three new
  tests and one changed one in the Ollama module's test. The new refusal tests first passed for the wrong reason (the field was
  still an unknown one), so four deliberate weakenings of the reader were tried (reserved names allowed, extra grammars allowed, more
  than 8 options allowed, any option name allowed); each made a test fail. The module's declaration test failed against the unchanged
  `module.json`.
- **Verification as run:** live tree, `tests.test_review_options`, `test_kit_profiles`, `test_declarations`, `test_verify`, `test_kit`:
  269 tests OK; the levels, permissions-drift, first-party, commands and checkpoint-command tests OK. Scratch clone: the Ollama module's
  tests, 439 OK, and `verify_package('packages/workbench', first_party=True)` accepted. `wb check` and `wb run code-work check` report no
  problems; `git diff --check` is clean. The full suite was not run; the owner decides any wider run.
- **Review:** one `reviewer` agent pass (read-only; it ran nothing). No blocking finding. It found the code true to the spec and the
  decision, the Ollama declaration true to the helper (its `_NAME` and `_CONTEXT` patterns are the kit's `name` and `count` text), no
  input that raises anything but a `DeclarationError`, and no consumer of `Command` that unpacks it by position. Applied: tests for an
  `excludes` entry that is not text, for a reserved name other than `effort` in `excludes`, for two options that exclude each other and
  for a declared grammar the kit can check; a wording fix in the spec; the near-tautological Ollama test was dropped. Noted: the spec
  says "built" for the Ollama declaration while the live `module.json` still lacks it, until the owner copies the package files.
- **Open point for increment D (written into the spec):** the engine must learn a bridge's declared options from a source an agent
  cannot write. The installed copy of a declaration is a project file; the pinned declaration hash is the owner's. D reads the kit's
  `run_command` and the launcher first and stops and reports if the answer needs the launcher to supply the declared options.
- **The owner's steps, as done (2026-11-04):** (1) the owner copied the two package files from the scratch clone to the live tree and
  the hashes matched (`66e3ad8d...040c41`, `94bf729c...d69f4`); (2) the agent's release preview was refused by the command gate, which
  is closed while a package differs from its release, so (3) the owner ran `wb release-approvals` in a terminal, which wrote 14
  approvals for the 1 first-party package; (4) it warned of **eight** stale shipped records, not the two the agent had said to expect
  (two come from this change and six are leftovers of earlier increments; the records hold hashes only, so the agent cannot say which),
  and the owner approved the dry-run list and the agent removed the eight through `wb run safe-git remove --recursive --confirm`;
  (5) the agent reran the checks below.
- **Verification after the release, as run:** `wb preview release-approvals` reads `record recorded` for the package and all 13
  modules and `stale records: 0`; the Ollama module's tests in the live tree, 439 OK; `tests.test_review_options`, `test_kit_profiles`,
  `test_declarations`, `test_verify` and `test_kit`, 269 OK; the first-party, permissions-drift, levels and commands tests OK; `wb check`
  and `wb run code-work check` report no problems; `git diff --check` is clean.
- **Not done:** the commit and the push. The commit holds the core files and tests, the specs, the plan, the two package files, the two
  new shipped records and the deletion of the eight stale ones.
- **Left for the owner:** the verdict and the word to commit.
- **Committed** as 89f8c0e (the owner's word to commit, 2026-11-04) and pushed.

### Increment D — The review engine reads the profile file (2026-11-04)

- **The design point settled first (step 1, the stop condition).** The engine could not learn a bridge's declared options from a
  source an agent cannot write without a launcher change, which the plan does not name. The agent stopped and reported three options;
  the owner chose the second: the engine does not read a declaration. It passes the options of the owner's profile after the kit's
  checks of their form, the bridge refuses an option it does not accept (the refusal is reported with the profile's name), and
  `wb doctor` and the delegated-approval check read the pinned declaration (increments I and J). The spec says so. The accepted
  record says the engine takes only declared options, so a dated clarification note on it is **proposed and waits for the owner's
  approval** (its text is in the report of this increment).
- **Done, in the live tree (core, uncommitted):** `workbench/wbkit/profiles.py` makes its patterns public (`PROFILE_NAME`,
  `OPTION_NAME`, `TEXT`) so the engine validates a stored round with the kit's own text; `docs/specs/review-engine.md` ("The owner's
  profiles", the field list of a round, the limits and the as-built log) and `docs/specs/review-profiles.md` say what is built.
- **Done, in a scratch clone only (package, nine files):** `packages/workbench/review-engine/helper/review-engine`: `read_profiles`
  replaces `read_setting`; a round takes rung n of the ladder of its kind (else `default`) by its place in the window; the arguments
  are `ask`, `--timeout`, `--schema`, then the profile's model, effort and options in name order; a failure is prefixed with the
  profile's name; a round records `profile` and a request with `options`; `check_round` reads both shapes of a stored round; `status`'
  `request` compares the last round with the profile it names (a round from before profiles, or one whose profile is gone, reads
  `changed`). Eight test files: `test_review_ladder.py` (new), `test_review_setting.py` (rewritten for the owner's file),
  `test_review_commands.py` (status), `test_review_state.py` (both shapes, malformed new ones), `test_review_round.py`,
  `test_review_convergence.py`, `support_review.py` and `support_bridge.py`.
- **Tests first:** the new and changed tests were run against the unchanged engine and 54 failed, as they should; after the change all
  433 tests of the engine's folder pass. Five deliberate weakenings of the engine (the rung from the count of all rounds, options not
  passed, `status` always `same`, stored options not checked, `default` refused for a document kind) were each caught by a test.
- **Verification as run:** in the clone, the engine's folder, 433 tests OK; in the live tree, `tests.test_kit_profiles`,
  `test_review_options`, `test_kit` OK, `wb check` and `wb run code-work check` report no problems, `git diff --check` is clean. The
  full suite was not run; the owner decides any wider run.
- **Review:** one `reviewer` agent pass (read-only; it ran nothing). No blocking finding. It found the code matches the records and
  the spec for the ladder, the arguments, the record and `status`; that nothing from the owner's file or a stored state can reach the
  bridge in any form but one validated `--name value` pair; that old rounds are read and `convergence` does not read `requested`; and no
  remaining use of the removed names. Applied: the field list of a round in the spec, three stale passages of the spec, one false
  sentence in `action-review.md`, the reverse hybrid shape (an old round whose request has `options`) added to the state test, and a
  stray call removed from one ladder test. **Not changed, deferred to increment E:** the `peer-review` skill and the test that locks
  in its text still name `.workbench/review.json`.
- **Not done:** the package files are not in the live tree; no release, no commit, no upgrade of the installed copy. The action-review
  engine and the shadow hook still read `.workbench/review.json` until increment F, so **that file must stay**.
- **The owner's steps (one list):** (1) write the owner's file in the store (the commands are in the report of this increment; it
  reproduces today's setting and changes nothing by itself, because the installed copy of the engine still reads the old file); (2) run
  the copy script `d_install_files.py` in the scratchpad, which copies the nine files only if each source has the recorded hash and
  prints the hash of each file it wrote; (3) tell the agent; (4) run `wb release-approvals` in a terminal, because the command gate
  refuses the agent while a package differs from its release; (5) the agent lists the stale shipped records for the owner's approval
  and removes them, reruns the engine's tests in the live tree and the core checks, and asks for the owner's word to commit; (6) after
  the commit, `wb upgrade` of the installed copy is separate: it is what makes the next review use the new engine, and the owner
  chooses when.
- **The owner's steps, as done (2026-11-04):** the owner wrote the profile file (the agent read it back: one profile, `standard`, the
  same bridge, model and effort as the old setting, and the `default` and `action-review` ladders); ran the copy script, and the agent
  checked all nine files in the live tree against the recorded hashes (they match); ran `wb release-approvals` in a terminal. The
  release preview then read `record recorded` for the package and all 13 modules, and listed exactly two stale records (the
  `workbench` package record that increment C committed, and the old `review-engine` module record), which the owner approved from a
  dry-run list and the agent removed; `stale records: 0`.
- **Verification after the release, as run (live tree):** the engine's folder, 433 tests OK; `tests.test_kit_profiles`,
  `test_review_options`, `test_kit`, `test_declarations`, `test_verify`, 269 OK; the first-party, permissions-drift, levels and commands
  tests OK; `wb check` and `wb run code-work check` report no problems; `git diff --check` is clean.
- **Not done:** the commit and the push; the upgrade of the installed copy; the dated clarification note on the profiles record, which
  waits for the owner's approval (without it the accepted record says "declared options only" while the engine does not check
  that; the spec says so). `.workbench/review.json` stays until increment F.
- **Left for the owner:** the verdict and the word to commit.
- **Committed** as 02334f9 (the owner's word to commit, 2026-11-04) and pushed.
- **Security review of increments B to D (2026-11-04, at the owner's request; a `security-reviewer` agent working in a scratch copy
  with a fake store and fake bridges, nothing real started).** No Critical, High or Medium finding. About 330 hostile profile files
  all ended in a `ProfileError` with fixed words and no file text or path; links, FIFOs, directories, oversize and unreadable files at the
  path are refused; about 25 forged, validly sealed stored rounds made the state unusable or changed only what `status` and `convergence`
  print, and nothing from a stored round reaches an argument list or a path; the argument list a profile can produce is read by both
  first-party bridges without any shift between a name and a value; about 50 hostile declarations gave only `DeclarationError`; a
  profile file replaced during a round leaves the recorded request equal to what was sent. **Seven Low findings,** all caused by the
  owner's own file or by version skew: L1 the engine consults no declaration (the spec's criterion 3 said it did); L2 a prefix of a
  reserved name (`mod`, `eff`, `tim`, `sch`, `conf`) is accepted, which a third-party bridge that accepts abbreviated options would read
  as the reserved option (verified by the agent: the first-party bridges match exactly); L3 the model name and option values are copied
  into the review's state in the project; L4 version skew (no kit API number was raised); L5 and L6 two overstated sentences of the
  kit's docstring (a symlinked `~/.config` is followed; `HOME` moves the store); L7 a forged state can reset the ladder to rung 1,
  within the known threat model. **Disposition:** all seven are fixed or stated in the nested increment D-A (the code fix for L2, the
  rest as text). **Limits of the evidence:** the reviewer could not run `git clone` or `git diff`, so it copied the tree and read the old
  `check_round` from the installed copy; it did not test `HOME` unset; the forged-window rung case was read and not run.

### Increment D-A

- **Done:** `profiles.reserved_or_prefix(name)` in the kit (true for a reserved name or a non-empty prefix of one), used by the profile
  reader (`_profile`) and by the declaration reader (`_review_options`); the messages of both say "prefix". Text corrections: criterion 3
  of `review-profiles.md` (the engine passes the profile's options and reads no declaration; `wb doctor` and the delegated check report
  an undeclared one) (L1); the model name and option values are kept in the review's state (L3, also in `review-engine.md`); version
  skew and its recovery (L4); the kit docstring and the spec on the last-part-only link refusal and `HOME` (L5, L6); the sealed state
  can reset the ladder (L7); `model-bridge.md` says a bridge matches option names exactly.
- **Tests first:** `ReservedPrefixes` in `tests/test_kit_profiles.py` (the function; every prefix of every reserved name refused as a
  profile option; `model-id`, `server`, `efforts`, `root-dir` accepted; a fake bridge that resolves abbreviations shows `--mod` would
  read as `--model`) and two tests in `tests/test_review_options.py` (every prefix refused as a declared option; the accepted names).
  Before the code change they ran red: 5 failures and errors, all for the missing function and the missing refusal.
- **Verification, as run:** `tests.test_kit_profiles`, `test_review_options`, `test_declarations`, `test_kit`, `test_verify`: 276 OK
  (rerun after the last text fix); the review engine's folder: 433 OK; `wb check` and `wb run code-work check`: no problems;
  `git diff --check` clean. No package changed, so no release is needed.
- **Not done:** the `module-contract.md` sentence (above); the commit.
- **Left for the owner:** the verdict, the choice on `module-contract.md`, and the word to commit.

### Increment E

- **Decision made while building:** the engine learns a server's location class from the bridge's own `check` command (the open point
  of `review-profiles.md`), called through the launcher with `["check"]`; it never opens the endpoint file. `ask-ollama` prints
  `location=` for each endpoint and makes no network call; `ask-codex` has no `check`, so a Codex profile reads `unknown`.
- **Done (in a scratch clone, not yet in the live tree):** `status` prints `next` (`{"profile", "bridge", "location"}` or `null`):
  `location_class` and `next_round` in the helper; the skill's first step names the owner's `review-profiles.json` and the stop on a
  refusal, and its rules describe `request` and `next`, including that the class is what the bridge reports. The specs
  `review-profiles.md` ("Status") and `review-engine.md` are updated in the live tree.
- **Tests first:** `test_review_next.py` (16 tests: the rung after 0, 1 and 2 rounds, the last rung repeating, a reset, `default`, a used-up
  window, no ladder, a refused file with and without a round; the class of a named server, of the default record, an unlisted server,
  a class outside the three, a prefix of a name, seven kinds of failed call, a bridge with no `check`, and that `status` writes nothing).
  15 were red (`KeyError: 'next'`) before the code. The skill rules test was red on the old skill text and green on the new. One
  existing expectation of `status` in `test_review_commands.py` gained `next: None`.
- **Verification, as run (clone):** the engine's folder, 449 tests OK (433 before, 16 new); `tests.test_kit`, `test_verify`,
  `test_kit_profiles`, `test_declarations`, 250 OK; `git diff --check` clean.
- **Not done:** the owner's steps (copy the five files, `wb release-approvals`, remove the stale records), the check of the live tree
  after them, the commit and the push. The corrected sentence in `module-contract.md` (deferred from D-A) is still not in any
  increment's listed areas and needs the owner's choice.
- **Left for the owner:** the copy, the release and the verdict.

### Increment F

- **Done (in a scratch clone, not yet in the live tree):** the action-review helper reads the one rung of the `action-review` ladder
  through the kit (`read_setting()`, no argument; `LADDER_KEYS`, `SINGLE_RUNG`), refuses a missing file, a missing ladder (`default`
  never serves) and a longer ladder, and passes the model, effort and options after `--confine` in the order of their names; the
  time budget (25 and 20 seconds) is unchanged. `.workbench/review.json` is read by nothing in the module. The test-set runner reads the
  same rung through the checkout's kit, requires `ask-codex` and no options, and ends the run before sending anything otherwise;
  its copy of the model and effort patterns is gone. The shadow hook is not changed. `action-review.md` ("Settings and the bridge",
  the runner paragraph, the not-built lists) and two tags of `review-profiles.md` are updated in the live tree.
- **Tests first:** the `Setting` class of `test_actionreview_bridge.py` rewritten to the profile file (rung, options order, missing file,
  project file read by nothing, longer ladder, no `action-review` ladder with a `default`, kit refusals, reserved names and prefixes,
  no quoting of the file), two tests of the options in the call, the output, pins and dangerous-case scaffolds moved to the profile file,
  the runner's tests moved to the owner's rung (eleven refused files, a missing file, another bridge, a rung with options, the store
  holds only the test-set file and the unchanged profile file), and the drift test of the ladder keys of the review engine, this
  engine and the runner (new `test_actionreview_ladder_keys.py`, new `support_profile.py`). Before the code the edited folder ran red:
  84 failures and 32 errors of 769.
- **Verification, as run (clone):** the whole action-review folder, 773 tests, 2 failures that F did not cause: the shadow hook's
  environment test (`__CF_USER_TEXT_ENCODING` is in the environment of this shell; it fails the same way on the unchanged live tree)
  and the hook store's thread test (flaky: on the unchanged live tree it failed 6 of 10 runs, and 4 of 10 in the clone made before F).
  After the last change the runner's tests, 41, pass; the bridge, output and pins files pass.
- **The owner's steps, as done (2026-11-04):** the owner ran the copy script (all nine files in the live tree match the recorded
  hashes, checked by the agent) and the release; the preview then read `record recorded` for the package and all 13 modules and listed
  exactly two stale records (the old `action-review` module record and the package record that increment E committed), which the owner
  approved from a dry-run list and the agent removed; `stale records: 0`.
- **Verification after the release (live tree):** the whole action-review folder, 774 tests, the same two known failures and no other;
  `wb check` and `wb run code-work check` report no problems; `git diff --check` is clean.
- **Not done:** the commit and the push. `.workbench/review.json` stays until the owner has checked a live review on the new engines; the plan says
  it can be deleted after F ships.
- **Left for the owner:** the copy, the release and the verdict; the two failing hook tests are known and not part of F.

### Increment G

- **Done:** `workbench/approvalcmd.py` reads a `convergence` report of format 1 or 2. Format 1 has exactly the old fields and reads as an
  unknown request (`last_requested` is `None`); format 2 has exactly those fields and `last_requested`, which is null or an object of
  exactly `bridge`, `model`, `effort`, `options` and `profile`, each held to the rules of the owner's profile file through the kit's
  `profiles` (a command name; printable text of at most 128 characters with no space and no leading `-`; low, medium or high; at most
  eight options with names and values of the profile rules, a reserved name or a prefix of one refused; a profile name). Any other
  format, a missing or extra field in either format and a bad request are refused. `Convergence` gains the last field
  `last_requested` with a default of `None`, and `Requested` is new. `MAX_CONVERGENCE_REPORT` is 8,192. Nothing uses the request yet:
  `delegation.py` reads the report by attribute, is unchanged and still stores the same fields, so a delegated approval behaves as
  before until the engine emits format 2 (H) and the setting exists (I).
- **Measured:** today's report is 267 bytes; the worst case of format 2 is 2,172 bytes, and with every character of the option values
  escaped it can pass 4,096, so the raised cap stays (recorded in `review-profiles.md`).
- **Tests first:** `ConvergenceReport` in `tests/test_approvalcmd.py` (formats, the exact field sets, each field of the request and its
  refusals, reserved names and prefixes, the cap, the worst case, a duplicate key and NaN) and four tests in `tests/test_delegation.py`
  (format 2 with a request and with a null request is approved as before; without the request, or with a bad one, it is refused); the
  cap test now sends 8,300 bytes. They ran red before the code: 13 failures and 7 errors of 145.
- **Specs:** `trust-and-approval.md` (the report, both formats, 8,192 bytes), `review-engine.md` ("Convergence": the installer reads
  format 2; the engine still prints format 1 until H), `review-profiles.md` (the measurement and the status tag).
- **Verification, as run:** `tests.test_approvalcmd`, `test_delegation` and `test_kit_profiles`, 216 OK; `test_approve_levels`,
  `test_planapprovals`, `test_settingscmd`, `test_gate_hook`, `test_rendering` and `test_declarations`, 384 OK; `wb check` and `wb run
  code-work check` report no problems; `git diff --check` is clean. No package changed, so there is no release.
- **Not done:** the commit and the push.
- **Left for the owner:** the verdict and the word to commit.

### Increment H

- **Done (in a scratch clone, not yet in the live tree):** the review engine's `convergence` prints `format` 2 (a new constant
  `CONVERGENCE_FORMAT`; the state's `FORMAT` stays 1) and `last_requested`: the bridge, the model asked for, the effort, the options
  and the profile name of the last stored round, or `null` for a round stored before the profiles were built. `converged`, `model`,
  `bridge` and the other fields are computed as before. `docs/specs/review-engine.md` ("Convergence") and a status tag of
  `review-profiles.md` are updated in the live tree.
- **Tests first:** ten new tests in `test_review_convergence.py` (the request and profile of a round since profiles; nulls and the empty
  options; a round before profiles reads null and converges as before; only the last round counts; the model asked for and not the
  reported one; the profile as it ran and not as the file reads today; `converged` independent of the request; the installer's
  `parse_convergence` reads what the engine prints in both shapes; the worst case with every option character doubled stays within the
  installer's 8,192; a forged request is refused at load) and the existing expectations moved to format 2. Eight errors and one
  failure before the code.
- **Verification, as run (clone):** `test_review_convergence.py`, 51 OK; the engine's whole folder, 459 OK (449 before, 10 new); and, in
  the live tree, `tests.test_delegation`, 95 OK (the installer is unchanged since G); `git diff --check` clean.
- **The owner's steps, as done (2026-11-04):** the owner copied the two files (both match the recorded hashes in the live tree, checked
  by the agent) and ran the release; the preview then listed exactly two stale records (the package record that increment F committed
  and the `review-engine` module record that E committed), which the owner approved from a dry-run list and the agent removed;
  `stale records: 0`. The engine's whole folder then ran in the live tree: 459 OK; `wb check` reports no problems.
- **Not done:** the commit and the push; `wb upgrade` of the installed copy, which is what makes a live engine print format 2.
- **Left for the owner:** the copy, the release and the verdict.

### Increment I

- **Done:** the owner's settings file has version 4, which holds the entry `delegate_profiles` (`any`, or 1 to 8 distinct profile
  names, none `any`) and nothing older may: absent it reads as `any`, every other value and the entry in a file of version 1 to 3
  reads as `INVALID` with one `settings:` problem and is never read as `any`; a new file is still seeded at version 3, and version 4
  accepts what version 3 accepts. `wb settings` prints `delegate-profiles approve-plan: any|<names>|invalid` when the file holds the
  entry (nothing when it does not, so every existing output is unchanged). `wb delegate-approve-plan` runs `_profile_gate` after the
  review is known to have converged on the bytes of the plan and before anything is recorded or logged: the checkpoint still reads
  `delegate`; the setting is valid; the profile file is read (`settings.read_profiles`, the kit's rules, the ladder keys taken from the
  file); every listed name is present; every listed profile is usable (`_unusable`: its bridge an installed, pinned module that provides
  `model-bridge` with a command of that name, each option declared for a review with a value that fits the grammar, no excluded pair
  set); the recorded request is known; and one listed profile equals it on the normal form of the record. `wb doctor` reports a listed
  name the file lacks or a file that cannot be used as a problem, and a listed profile that names no model as a risk
  (`delegate_profile_findings`). Specs: `command-permissions.md`, `trust-and-approval.md`, `review-profiles.md`.
- **Decisions made while building, for the owner to overrule:** `wb settings` prints the `delegate-profiles` line only when the entry
  exists, because the existing tests compare whole outputs and the line matters only for a delegating owner; the entry in a file older
  than version 4 is invalid and not ignored, so that a list written into the wrong file cannot read as `any`.
- **Tests first:** `DelegateProfilesTest` and `ProfilesFileTest` in `tests/test_settings.py`, `DelegateProfilesPrinted` in
  `tests/test_settingscmd.py`, `ProfileGate` (21 tests: any, a match, the name not compared, absent and null equal, unordered options,
  one match among several, the request and never the rung, an edited profile, an extra option, a missing name, a missing, damaged or
  invalid file, the file's text never in the refusal, an unknown request, five kinds of unusable profile, every invalid setting, the entry
  in an older file, the setting only while `approve-plan` reads `delegated`, the order after convergence, nothing recorded or logged on a
  refusal, and the second read) in `tests/test_delegation.py`, and the doctor tests; the new tests ran red before the code. Four existing
  tests that used version 4 as their unsupported example moved to 5, and the fields test lists the new field.
- **Boundary repair (added by the widening):** the fixtures of `tests/test_kit_profiles.py` and `tests/test_approvalcmd.py` now use neutral
  names (`bridge-a`, `bridge-b`, `solo`) and `tests/test_boundary.py` passes; nothing they test changed.
- **Verification, as run:** the wide set of 1,183 tests (the settings, levels, permissions, gate, approve, rendering, doctor, delegation,
  kit, declarations, verify, planapprovals and boundary modules), OK; `test_settings` (115), `test_cli` and `test_store`, run by file, OK;
  `wb check` and `wb run code-work check` report no problems; `git diff --check` is clean. No package changed, so there is no release.
- **Not done:** the commit and the push. `wb doctor` does not run `_unusable`, as the plan did not ask for it. The walk-through of a real
  delegated approval with a list is increment K.
- **Left for the owner:** the verdict and the word to commit.

### Increment I-A

- **Done:** `_profile_gate` reads the settings once (`settings.load`) and decides from that one reading both whether the checkpoint still
  reads `delegate` for the process module (`settings.effective(...)`, the expression `planapprovals.delegating` used) and what
  `delegate_profiles` holds; a state that does not delegate (a damaged, emptied, duplicate-key, unsupported-version or non-file settings
  file, or a checkpoint that was changed) refuses before the entry or the profile file is looked at, and an absent entry is `any` only
  for a file that delegates. `_unusable` refuses unless exactly one installed module provides `model-bridge` with a command of the
  bridge's name. The loader no longer adds "unknown entry ... ignored" for `delegate_profiles`, so an entry in a file older than
  version 4 prints one problem. `trust-and-approval.md` says so.
- **Deviations from the plan's wording, recorded here because the plan text cannot change without a new approval:** (1) step 2 and step 3
  say the gate takes the loaded settings as an argument and that a file which "loses the entry or holds `any`" after the first read
  refuses. The gate loads the settings itself, once, and such a file is the owner's current setting and is accepted as `any` (the
  reviewer judged this right; a test pins it); what the gate refuses is a state that does not delegate. The command's earlier check of
  the setting (`_setting`) remains a separate read that runs before any helper. (2) Step 3 says an absent entry is `any` "only when the
  reading had no problem". The code does not test the problems: every state the loader cannot read gives no checkpoint and refuses
  first, and a delegating file with an unrelated problem (an unknown entry, a bad cap) delegated before and still does.
- **Tests first:** five in `ProfileGate` (one reading; a later reading that would differ cannot change the decision; each state that does
  not delegate refuses before the profile is looked at; two modules that could be the bridge; a file that delegates but lost the entry or
  holds `any` is accepted), one assertion in `test_settings.py` and one changed test in `test_settingscmd.py`. They ran red before the
  code (3 failures and 1 error, and 3 in the settings test).
- **Verification, as run:** `ProfileGate`, 26 OK; a wider set of 906 tests (delegation, settingscmd, doctor, boundary, kit profiles,
  approvalcmd, levels, levelrun, the gates, approve levels, rendering, planapprovals, permissions drift and check), OK; `test_settings`
  (115), OK; `wb check` and `wb run code-work check` report no problems; `git diff --check` is clean. No package changed.
- **Not done:** the commit and the push. `wb doctor` still does not run the bridge checks (finding I2; increment J).
- **Left for the owner:** the verdict and the word to commit.

### Increment J

- **Done:** `wb install` and `wb adopt` write a default `review-profiles.json` into the guarded store when nothing is at that path,
  built by the new `workbench/profiledefault.py` from the selected modules alone: one profile for each module that provides
  `model-bridge` and has exactly one command that takes `ask`, named by that command and holding `bridge` only (no model, effort or
  option), and the `default` ladder when exactly one profile was made. It is one more store write of the plan, so the existing digest
  binds its bytes; the preview prints the file exactly as it will be written and notes for the rest (a bridge that was not named and
  why, no ladder for several profiles, an existing file left as it is, no model bridge, more than 32). An existing file of any kind is
  never changed, and the write refuses at once when the path is occupied. The preview also prints what an old `.workbench/review.json`
  said, as data (the four known fields, ASCII with escapes, cut at 128 characters; one line when it is over 4,096 bytes or malformed),
  which changes nothing that is written and is not in the digest. `wb doctor` reports a file the kit refuses (a problem), each profile that
  cannot be used with its bridge by the delegated-approval check's rules (a problem; `delegation.unusable` is the one shared check), a
  missing file when a model bridge is installed (a risk) and the old project file as read by nothing (a note).
- **Deviations from the approved plan's wording, recorded here because the plan text cannot change without a new approval:** (1) the plan
  says the install writes "the two ladders `default` and `action-review`". Only `default` is written: `action-review` is the key of one
  module, the installer may not name a module, and the owner adds that ladder when they use that engine; the spec says so. (2) The plan's
  affected areas list `askdigest.py`, `store.py`, `command-permissions.md` and `test_install_levels.py`; none needed a change, because
  the store write is bound by the digest's existing `store_writes` field.
- **Tests first:** `tests/test_profiledefault.py` (new: the builder, the existing-file case and the old-file lines), three in
  `tests/test_installplan.py` (one more store write, the digest binds the bytes and not the notes, the preview), `ProfileDefaultInstall`
  in `tests/test_install.py` (9 tests with made-up bridges: one bridge, several, none, a wrong digest, an existing file of four kinds, a
  directory and a link, a file that appears after the preview, the installer's reader and the kit read what was written, the file's
  mode) and `ReviewProfiles` and four in-project tests in `tests/test_doctor.py`. They ran red before the code.
- **Verification, as run:** J's modules and the install, preview, adopt, recover, unfinished, doctor, delegation, approvalcmd and kit-profile
  modules, with `tests/test_boundary.py`, which passes; `test_settings` (115) by file; `wb check` and `wb run code-work check` report no
  problems; `git diff --check` is clean. No package changed, so there is no release. The full set ran 672 tests, OK.
- **Not done:** the commit and the push. The preview's lines about an old `.workbench/review.json` are tested on the function, not
  through an adoption of a project that has one. The walk-through of a real install is increment K.
- **Left for the owner:** the verdict and the word to commit.

### Increment J-A

- **Done:** (1) a profile line of the default file names the module as well as the command, and two selected modules that give one
  bridge command make one profile and a note that names both (the first by module name owns it); (2) the default profile file is the one
  store write that is skipped when its path is occupied at write time (`Plan.optional_store`): `_write` leaves the owner's file as it
  is, `_finish` says so, the install goes on and finishes without a marker, and every other occupied store path still stops the install;
  (3) `wb doctor` reports a fault of the guarded store or of the installed modules, in the profile checks and in the read for a
  `delegate-profiles` list, as one problem line each and prints the rest of the report; (4) the code that was to show an old
  `.workbench/review.json` in the preview (`read_old`, `old_setting_lines` and their constants, and their tests) is removed, because
  `wb install` and `wb adopt` refuse a target that has a `.workbench` directory, so it could never run. `wb doctor` still names the old
  file as read by nothing. `review-profiles.md` and `installer-interface.md` say all of this, including that the kit's write (a check
  and then a rename) is not changed and leaves a window of microseconds that only the owner's account can use.
- **Correction of an earlier claim:** the Result of increment J said the old-file lines were "tested on the function, not through an
  adoption"; the reason was not a gap in the tests but that the code could not run. It is removed here.
- **Tests first:** the profile line and the one-profile note, the absence of the old-file code, `Plan.optional_store`, an install in
  which the file appears after the plan was recorded (exit 0, the owner's bytes kept, the message printed, the manifest written, no
  marker), the doctor with five kinds of fault from the store, the installed modules and the check, and with a fault from the read for a
  list. They ran red before the code (6 failures and 5 errors; the last fix by weakening it on purpose).
- **Verification, as run:** the install, preview, adopt, recover, unfinished, doctor, delegation, approvalcmd and kit-profile modules with
  `tests/test_boundary.py`, 674 tests, OK (before the last fix); the doctor, profile-default, install-plan, install, boundary and
  delegation modules again after it, 330 tests, OK; `test_settings` (115) by file; `wb check` and `wb run code-work check` report no
  problems; `git diff --check` is clean. No package changed.
- **Not done:** the commit and the push (J and J-A go out together). The shown-file block of the preview and the written file are
  compared by the existing tests; a run of a real install is increment K.
- **Left for the owner:** the verdict and the word to commit.

### Increment K

- **Done:** the documents say what is built: `review-profiles.md` opens with what is true (both engines read the owner's file and nothing
  in the project, and its numbers are what was built); the sentence of `module-contract.md` on the names that `commands[].review_options`
  refuses includes their prefixes; `development.md` names the profile file for the action-review engine; the false row of
  `command-permissions.md`, the stale parenthesis and dangling reference of `review-engine.md` and the wording of criterion 1 are
  corrected. Those lines of `command-permissions.md`, `review-engine.md` and `development.md` are outside K's listed areas except
  `development.md`; they were false statements of what is built, which is what K is for, and the reviewer found them.
- **The walk-through, as run (2026-11-05, Python 3.15.0 on Darwin 25.6.0, at commit `5ed2c2f` with the document edits above uncommitted):**
  a scratch test module on the review engine's real-launcher fixture, which installs a project with the installer from a copy of the
  packages into a temporary directory and a temporary `HOME` (the installer's own typist answers the digest, as the install tests do),
  with the real `ask-codex` bridge, the real launcher and a fake `codex` program; no model was called and the owner's store was not
  touched. It printed, and the run ended `OK`:
  1. **the install default:** `review-profiles.json` holds one profile `ask-codex` (`{"bridge": "ask-codex"}`) and the ladder
     `default: ["ask-codex"]`;
  2. **a review on it:** round 1 of a plan ran on profile `ask-codex` and recorded `requested {effort null, model null, options {}}`;
     `status` read `request same`, `next` the same profile with location `unknown`; `convergence` printed `format 2`, `converged true`
     and `last_requested {bridge ask-codex, effort null, model null, options {}, profile ask-codex}`;
  3. **a ramp:** with profiles `quick` (low), `standard` and `deep` (the model and medium or high) and a `spec` ladder, three rounds ran on
     `quick`, `standard`, `deep` in that order, `status` named the next profile and `request same` before rounds 2 and 3, and the fake
     `codex` was given `model_reasoning_effort` `low`, `medium` and `high` (and a model option for the last two only);
  4. **an edit is noticed:** after `deep` was edited, `status` of the spec read `request changed`, while the plan's `convergence` still
     reported the request of the sealed round and not today's file;
  5. **the refusals,** each naming the file and a fixed rule and starting no `codex` (none was started): no file, not strict JSON, a duplicate key,
     an oversize file, a ladder naming an absent profile, an option that is a prefix of a reserved name, no ladder for the kind; and an
     option the bridge does not accept, which the bridge refused with the profile's name and no round spent;
  6. **the project file is read by nothing:** a `.workbench/review.json` naming a bridge that is not installed changed nothing: round 2
     of the plan ran on `ask-codex`;
  7. **`wb doctor`** on the project: exit 0 with the file in order (it noted the old project file as read by nothing), exit 1 and a
     `review-profiles` problem for a profile whose bridge is not an installed module;
  8. **the declaration refusals:** `review_options` with `server` accepted, `model` and `mod` refused as reserved or beginning a reserved
     name, and a grammar `.*` refused.
- **Limits of the walk-through, stated so nothing is read as shown that was not:** (1) the **delegated approval limited by
  `delegate-profiles`** and the settings file at version 4 were not walked end to end; they were run by the 26 gate tests of `ProfileGate`
  and the settings tests, and probed on copies by the security review of increment I, all with made-up modules; (2) the **action-review
  engine's one rung** and the **test-set runner** were not walked, because the fixture does not install that module; they are covered by
  its tests and by the review of increment F; (3) an **interactive install in a terminal** was not run, because an install is owner-run:
  the install tests and this walk-through drive `install.run` with a typist; (4) the **Ollama bridge**, a real model and a real
  `codex` were not used; the location class of a server is therefore shown only as `unknown`; (5) the numbers of the criteria are
  those the reviewer checked against the code; the criteria were not each re-run here beyond the steps above.
- **One observation, not part of K and not fixed:** a refusal for an option the bridge does not accept says "no round was spent" twice,
  because increment D's `profile <name>:` wrapper re-wraps a message that already ends that way (`Failed.__init__`). It is cosmetic; the
  fix is a package edit.
- **The dated note (done, 2026-11-05):** the owner approved its text, and it was appended as "Note, 2026-11-05" after the unchanged body of
  `docs/decisions/2026-11-04-delegated-approval-checks-the-profile-of-the-last-round.md` (six lines added, none removed). It says that the
  installer, which may not name a module or a kind of review, takes the ladder keys from the profile file, so it checks the profiles and
  the names a ladder uses and does not refuse an unknown ladder key or a longer `action-review` ladder, which each engine still does.
- **The spec's status (done, 2026-11-05):** the owner marked `review-profiles.md` `Current`.
- **Not done:** the commit and the push.
- **Left for the owner:** the verdict and the word to commit. Whether to run the module test roots that
  use the kit (increment B changed the kit every module imports) is the owner's decision; not every module's test root was run: those named in
  the earlier Results were (the review engine's, the action-review module's, the Ollama bridge's declaration test and the installer's).
