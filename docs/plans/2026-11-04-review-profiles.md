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
