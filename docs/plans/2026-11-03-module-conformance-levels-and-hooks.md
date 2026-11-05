# Modules declare their levels, `wb verify` checks them, and a module's hook says where it is registered

Status: Proposed
Created: 2026-11-03
Candidate: none (the closest, `workbench-v1#checkpoint-levels-beyond-block`, leaves module-owned arguments and module authoring out of its boundary; this plan takes them, on the owner's direction of 2026-11-02; it is the third of three plans that split `2026-11-02-permission-levels-for-every-command`)
Specs: command-permissions, module-contract, mempalace, remote-runner, action-review

## Goal

Every owner-run argument of a first-party module offers `ask` (bound to the digest of a read-only preview) and `none` wherever an
honest preview can be made, and the module's spec says why where it cannot. A module author, first-party or external, gets a
`wb verify` check and a short guide that tell them when a declaration, a preview or a shipped skill does not fit the system, and what a
module that ships a harness hook says about where the owner registers it, so that registering it does not make the rendering stale.
Shipped defaults stay as they are.

## Scope

In:

- the owner-run arguments of `mempalace` (`init`, `mine`) and `remote-runner` (`fetch-overwrite`), and the pairing of the
  `remote-runner` commands `submit` and `fetch` with the checkpoints `submit-remote-job` and `fetch-remote-output` (a decision, then
  its build);
- the `wb verify` conformance checks for modules, a class a module can declare, and the author guide with a minimal example module;
- what a module that ships a harness hook (today the `action-review` shadow hook) says about where the owner registers it, and what
  `wb doctor` notes about a hook the installer did not render;
- `wb doctor` for the new declarations, and the specs as built.

## Non-goals

- Changing a shipped default, the compiled floor or the personal `floor` list.
- `delegated` for any key, risk profiles, and building a hook that decides or changing the shadow hook: the plan
  `2026-11-03-delegated-levels-and-risk-profiles` decides them and the `action-review` plan after its shadow period builds the hook.
- The installer commands' levels: the plan `2026-11-02-permission-levels-for-every-command`.
- Any change to the registry's structure beyond a declared class and the pairing the record of increment A chooses; plan
  `2026-11-02-permission-system-consistency` builds the registry.

## Assumptions and constraints

- **This plan starts only after `2026-11-02-permission-system-consistency` is `Completed`** (it is). It builds on the registry, the
  kit's preview-digest helper, the corpus and `wb doctor` that plan delivers. The author found no use in increments A and B of the work
  of the installer-commands plan, so the two plans do not wait on each other. Increment C needs the record of increment A of
  `2026-11-03-delegated-levels-and-risk-profiles` accepted, since that record says where the bridge's hook lives.
- Increments A-A and B edit `packages/workbench/` (scripted pass, owner's release), and so does increment C if a declared hook field is
  chosen. The others edit the installer, tests and documents.
- The `action-review` shadow hook (built by another session and merged into `main`, commit `8dc30ca`; since installed by the owner, whose shadow log it writes)
  is a `PermissionRequest` hook for `Bash` that records what the review engine would say about each prompted command and decides
  nothing (`docs/specs/action-review.md`, "The shadow hook"). It is the first module to ship a harness hook. A command that raises a
  prompt is exactly what the level system makes prompt: a module's `asks` minimum, a key at `ask`, and the floor's asks. The installer
  hashes the two project settings files it renders into (the permissions file and the shared file), and an edit to either makes the
  keys at `ask` and `none` read `block` until a rerender (`command-permissions.md`, "Rendering"), so where the owner registers a hook
  matters.
- Any change to what a key offers changes the settings version and the rendering record; the owner runs `wb rerender` in a terminal
  after each increment that changes a rendered rule, and `wb doctor` says when it is due.
- A decision record is written `Proposed`; accepting it is a checkpoint at level `ask`.
- **A spec is never left false between increments.** An increment that changes what a command offers updates the lines of the specs
  that its change makes false (`command-permissions.md`, the module's own spec, `module-contract.md`) in the same commit; increment D
  then replaces what remains "intended" and checks the whole.
- Each later increment depends on the one before it (A, then A-A, then B, then C, then D), so the owner may stop the plan after any
  increment; a stopped plan leaves every earlier increment complete, and no increment can be dropped from the middle.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. The record of the pairing (increment A) is accepted, and the record of increment A of `2026-11-03-delegated-levels-and-risk-profiles`
   is accepted before increment C. No accepted record is rewritten; a superseded record changes only its status line, once its
   successor is accepted.
2. The owner-run arguments of `mempalace` and `remote-runner` declare `levels` and `preview`, or the module spec names why they stay
   `block` (increment A-A), and the pairing of the `remote-runner` commands `submit` and `fetch` with the two remote checkpoints is
   decided by an accepted record (increment A) and built as it says (increment A-A).
3. `wb verify` stays a check that runs nothing of the module: it refuses a declaration that does not fit the permission system (a
   declared `preview` that names no argument or an owner-run argument, `ask` offered without a preview, an unknown danger class)
   and warns on a shipped skill or agent that says to never run an argument whose declared levels include `ask` or `none`. The
   behaviour of a module's preview (a `digest:` line of 32 lowercase hex, a wrong or missing digest refused) is checked by a
   conformance test in the kit that the module's own tests run against its own helper, before the module is offered for approval.
   A module can declare the danger class of an owner-run argument, and the review engine's `extend`, `archive` and `amend` read as
   `project`; the author guide and a minimal example module exist.
4. The module guide and the `action-review` spec say where a module's hook is registered so that the rendering stays current (the
   owner's user-level configuration, which the `action-review` design requires, and not the two project files the installer
   hashes), and `wb doctor` notes a hook in a rendered project file that the installer did not render.
5. No setting an owner can write reads other than as written without `wb doctor` saying so.

## Increments

### Increment A — The pairing of the remote commands with their checkpoints (a decision record)

**Outcome:** a `Proposed` decision record says which key governs each of the acts of `submit` and `fetch` of `remote-runner`, with every
shipped default and offered level unchanged, and the owner has decided what to do with it. *(Split on 2026-11-05 after the first round
of the review: the first text of A also built the levels of three arguments and asked for "one or two local commits", and an
increment is one verified, reviewed local commit. The build is the nested increment A-A.)*
**Dependencies:** `2026-11-02-permission-system-consistency` completed (it is).
**Affected areas:** `docs/decisions/` (the pairing record, and the index row) and nothing else.
**Steps:**
1. **The pairing.** The checkpoints `submit-remote-job` and `fetch-remote-output` (read `block`) and the commands
   `wb run remote-runner submit` and `fetch` (read `none`, with the module's `asks` rendering a prompt either way) govern the same
   acts and keep a level each; the registry does not record the pairing since it would name a module
   (`2026-11-03-conformance-tests-name-modules-and-module-pins-follow-the-levels`, decision 2), and the spec records it. Draft a
   `Proposed` record that says which key governs each act, with every shipped default and offered level unchanged. The options: leave
   two keys and have the module declare the pairing (a field, read by the registry without naming a module) so that `wb doctor` can
   say when a checkpoint reads `block` while its command reads `none`; or keep the spec's record as it is. State the consequence of
   each, and recommend one. Mapping the commands to the checkpoints (extending `checkpoint_of` to an argument that carries an `asks`)
   would move the commands' default from `none` to `block`, a change of a shipped default that this plan does not make: it is a
   separate candidate for the owner's own scope and decision (see Deferred work), and the record may name it as such.
2. Stop for the owner, who decides the record. Writing it does not accept it (`accept-decision` is a checkpoint at level `ask`).
**Verification:** the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-module-conformance-levels-and-hooks#A`.

### Increment A-A — First-party modules declare their owner-run arguments' levels

**Outcome:** `mempalace init` and `mine` and `remote-runner fetch-overwrite` declare `levels` and a `preview`, or the module spec
names why they stay `block`; and the pairing is built as the accepted record of increment A says (the spec and decision 5 of
`2026-11-02-one-permission-registry-and-key-model` assign it to this work). If the owner keeps the spec's record as it is, there is
nothing to build for the pairing.
**Dependencies:** A, with its record decided by the owner.
**Affected areas:** the declarations, helpers and tests of `mempalace` and `remote-runner` under `packages/workbench/`; their specs
`docs/specs/mempalace.md` and `docs/specs/remote-runner.md` (the levels and previews of the three arguments and the pairing, in the
same commit as the change); and, as the record decides, `workbench/levels.py`, `workbench/declarations.py`,
`docs/specs/module-contract.md` and `docs/specs/command-permissions.md` ("Not built").
**Steps:**
0. If the record chose a mechanism: write the tests first, build it, and update the registry, the module contract and the specs in the
   same commit.
1. For each argument decide with the accepted records whether a preview can show the effect honestly (what `init` would write, what
   `mine` would index, what `fetch-overwrite` would replace). Where it can, write the test first, then the preview and the digest
   recomputed in the helper's lock using the kit helper.
2. Declare `levels` and `preview`; `wb verify` passes the module.
3. One scripted pass for the package edits; the owner starts it and releases the approvals.
**Verification:** the modules' own tests, `tests/test_verify.py`, `tests/test_owner_argument_levels.py`, and, for step 0, the tests of
the mechanism the record chose (`tests/test_levels_facts.py`, `tests/test_declarations.py`, `tests/test_permissions_drift.py`).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-module-conformance-levels-and-hooks#A-A`.

### Increment B — Module conformance: `wb verify` and the author guide

**Outcome:** a module author, first-party or external, is told when the module does not fit the permission system.
**Dependencies:** A-A.
**Affected areas:** `workbench/verify.py`, `workbench/declarations.py`, `workbench/levels.py`, `workbench/wbkit/` (the conformance
test, and its own kit test; the kit names no module), `tests/test_verify.py`, `tests/test_levels_facts.py`,
`docs/specs/module-contract.md`, the `review-engine`
declaration under `packages/workbench/` (a package edit: a scripted pass and the owner's release), a guide for module authors and
a minimal example module in `docs/`.
**Steps:**
0. **A class a module can declare** (the owner's decision of 2026-11-02, from the result of increment E of
   `2026-11-02-permission-system-consistency`). Add an optional field on a command's declaration, naming the danger class
   (`project` or `governs`) of an owner-run argument; `reads` stays the class of an argument that only reads, and a class on an
   argument that is not owner-run is refused. The registry uses a declared class and derives one only when none is declared. Write
   the tests first (`wb verify` refuses an unknown class; the registry reads the declared class; the three review-engine
   arguments `extend`, `archive` and `amend` read as `project`, which decision 4 of
   `2026-11-02-one-permission-registry-and-key-model` requires, and `reset` and `prune` as `governs`), then declare it in the
   `review-engine` module and update `tests/test_levels_facts.py`, whose pinned divergence changes on purpose.
1. **What `wb verify` checks, without running anything of the module** (it takes a package directory and has no effect today, and
   verification precedes approval and pinning, so no candidate code may run in it). Write the tests first: refuse a declared
   `preview` that names no argument, or names an owner-run one; refuse `ask` in `levels` without a `preview`; warn on a shipped skill
   or agent that says to never run an argument whose declared levels include `ask` or `none`; warn on a closed command list that
   leaves out `wb settings` while the skill depends on a level.
2. **The behaviour of a preview is a test the module runs itself.** Add to the kit a conformance test (a `unittest` mixin in
   `workbench/wbkit/` that takes the helper's path and a throwaway project the test makes): the preview prints a `digest:` last line of
   32 lowercase hex, the command refuses a wrong and a missing digest, and the digest changes when the content changes. A module's
   own tests include it, as the review engine's do for its five arguments; it runs under the author's own authority on the author's own
   code, not in `wb verify` and not on a module that is only being considered. Write its tests first against a fake helper.
3. Write the guide: how to declare `owner`, `levels` and `preview`; the digest rule; the conformance test and that the module's own
   tests run it; what a skill may say; and the example module.
**Verification:** `tests/test_verify.py`, `tests/test_declarations.py` and the kit tests. The conformance test starts a helper in a
throwaway project, which is a subprocess surface of the module's own test run (not of the installer); the author asks the owner once
whether to run a security review of the kit code that starts it.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-module-conformance-levels-and-hooks#B`.

### Increment C — A module's hook: where it is registered, what `wb verify` and `wb doctor` say

**Outcome:** the owner knows where to register a hook that a module ships so that the rendering stays current, a module author is
told what to say about their hook, and `wb doctor` notes a hook in a rendered project file that the installer did not render.
**Dependencies:** B; the record of increment A of `2026-11-03-delegated-levels-and-risk-profiles` accepted.
**Affected areas:** the module guide of increment B and `docs/specs/module-contract.md`; `docs/specs/action-review.md` (its owner steps
for installing the shadow hook); `workbench/doctor.py` and `tests/test_doctor.py`; and only if that record chooses a declared
hook field: `workbench/declarations.py`, `workbench/verify.py`, `tests/test_declarations.py`, `tests/test_verify.py` and the
`action-review` declaration under `packages/workbench/` (a package edit: a scripted pass and the owner's release).
**Steps:**
1. Read what the module ships today: `action-review` lists `hook/shadow_hook.py` and `hook/shadow_store.py` under `ships`, with no
   kind, and the spec says the owner registers `python3 -B <path>/shadow_hook.py` as a `PermissionRequest` hook for `Bash`. Check by a
   run on a copy that registering a hook in the permissions file, or in the shared file, makes a key at `ask` read `block` and makes
   `wb doctor` say the file differs from the record; record the output.
2. Write the guide section and the spec's owner steps: a module that ships a hook says which event and tool it registers for,
   whether it answers anything, and that the owner registers it in their user-level settings, not in the two project files the
   installer hashes (the `action-review` design already puts the enforcement point there); `action-review.md` is brought level with
   that (its owner steps today say only "registers"). If the harness shows the owner's prompt while a hook runs is still unknown,
   the owner steps include the test that finds out (a hook that waits, run on a copy, and whether the prompt shows meanwhile).
3. Write the tests first for `wb doctor`: a rendered project file that holds a hook the installer did not render gives a `note` that
   names the file, the event and the tool and not the command line's arguments; a hook the installer rendered (the edit gate and the
   command gate) gives none; a damaged or large file gives the finding of increment L of `2026-11-02-permission-system-consistency`.
   Then build the note.
4. Only if the record of the delegated plan chose a declared field (for example `hooks`, naming the event, the tool and whether the
   program answers): write the tests first (`wb verify` refuses an unknown event, a hook file that is not under `ships`, and a program
   that is declared as not answering but whose source holds an answer object, as the shadow's own test already checks for its source),
   build it, declare it in the `action-review` module and run the package pass. Otherwise leave the declaration as it is.
**Verification:** `tests/test_doctor.py`, `tests/test_verify.py` and `tests/test_declarations.py` (the last two only for step 4), the
document check. A declared field is parsing of a module's declaration, an untrusted-input surface; if step 4 runs, the author asks the
owner once whether to run a security review.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-module-conformance-levels-and-hooks#C`.

### Increment D — Walk-through and the specs as built

**Outcome:** each new level and check is run once in this clone and recorded; the specs describe what is built.
**Dependencies:** all earlier increments that the owner kept.
**Affected areas:** this plan's Result; `docs/specs/module-contract.md`, `mempalace.md` and `remote-runner.md` (what the levels and
previews of their arguments and the pairing now say), `command-permissions.md` ("Not built"), `action-review.md` (the owner steps for
the shadow hook, increment C), `docs/development.md`.
**Steps:**
1. Run `wb doctor`; the owner fixes what it flags and reruns `wb rerender` in a terminal.
2. For each argument that gained `ask`, run its preview and its command with the digest once, in a throwaway project where the command
   changes files; record the output.
3. Replace "intended" text with "built" in each spec named above, citing the increment and the test; remove from "Not built" only
   what is built; record what stays `block` and the decision that keeps it so. Tell the owner the roadmap file is not edited.
4. Run the document check.
**Verification:** the runs above, as run; the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-module-conformance-levels-and-hooks#D`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. After D, rerun only `wb doctor`,
`wb verify packages/workbench`, the document check and the drift test and gate corpus of `2026-11-02-permission-system-consistency`
(`tests/test_permissions_drift.py`, `tests/test_gate_corpus.py`). The full suite runs only if the owner decides after the author states
what could break outside the tested area; module test roots are part of that statement, since a change to a declaration reaches them.

## Risks and sensitive actions

- **Relaxing a level lets the agent run a dangerous command.** That is the owner's chosen risk. Defaults stay as shipped, the floor is
  untouched, and `wb doctor` reports a relaxed dangerous key as a risk.
- **A digest that does not bind the preview's content makes `ask` a rubber stamp.** Each preview is tested to change when its
  content changes and to be recomputed inside the command's lock.
- **Package edits (A-A, B and maybe C) make the shipped approval stale** until the owner's release; the refusal line of
  `2026-11-02-permission-system-consistency` (increment J) then explains it.
- **`wb verify` must never run candidate module code.** It checks the declaration and the shipped text only; verification comes
  before approval and pinning, and a throwaway project is not a sandbox. The preview's behaviour is a conformance test in the kit,
  run by the module's own tests under the author's authority, so the kit code that starts a helper is the one subprocess surface.
- **Registering a hook in a hashed project file makes the rendering stale.** Increment C records where to register it and has
  `wb doctor` note an unrendered hook; until the owner has done that, the owner's `ask` and `none` keys read `block` after such an edit.
- **Accepted decisions outrank code.** A conflict is settled by a new superseding record, never by rewriting an accepted one.

## Review record

- **Earlier review.** This plan was split out of `2026-11-02-permission-levels-for-every-command` (2026-11-03), whose review (4 rounds on
  the bridge, 9 findings) covered the earlier text, including the pairing step (round 3 and 4 findings, applied here) and the
  non-executing `wb verify` (round 2, applied here); it did not cover this split.
- **Review of this plan (2026-11-05, the review engine on the owner's `standard` profile, model `gpt-5.6-terra`; round 1 of 3, which found
  `changes_needed`).** Two findings, both checked against the plan and the project's rules and both applied:
  - **Major.** Increment A asked for "one or two local commits" although an increment is one verified, reviewed local commit. Increment A
    is now the pairing decision record alone, and its build is the nested increment A-A; B now depends on A-A, and the places that named
    A for the build (the package-edit assumptions and risk, completion criterion 2) name A-A.
  - **Minor.** The sentence that A, B and C are separable contradicted the chain of dependencies. It now says that the plan may be
    stopped after any increment and that no increment can be dropped from the middle.
  - **Also corrected on reading (not a finding of the engine):** the shadow hook is no longer "not yet installed by the owner".
- **Read against the code of 2026-11-05 by the author,** after the review profiles plan was built: the plans and records this plan depends
  on are completed or accepted (`2026-11-02-permission-system-consistency`, `2026-11-03-delegated-levels-and-risk-profiles` and its
  record), and `tests/test_owner_argument_levels.py`, `tests/test_levels_facts.py` and `tests/test_gate_corpus.py` exist. Not checked: the
  text of each increment against the current `declarations.py` and `module-contract.md`, which gained `review_options` and its prefix
  rule; increment B's tests must keep the installer's tests free of module names (`tests/test_boundary.py`, which allows only
  `tests/test_levels_facts.py` and `tests/test_permissions_drift.py` to name them).
- **Left for the owner:** a second round (it runs on `standard`; a third would run on `second-opinion`), or the
  owner's approval of the plan as it stands. This plan is not approved.

## Deferred work

- Reading the harness's global configuration (`workbench-v1#global-settings-check`).
- Per-project overrides of the owner's personal settings.
- Mapping the `remote-runner` commands `submit` and `fetch` onto the checkpoints `submit-remote-job` and `fetch-remote-output`
  (extending `checkpoint_of`): it moves the commands' shipped default from `none` to `block`, so it needs its own candidate, scope and
  decision by the owner.
- The hook that decides (the review engine answering `PermissionRequest` for a key at `delegated`), and the shadow's own install and
  labelling: the owner's steps and the `action-review` plan after its shadow period.

## Result

Empty until work starts.
