# Installer commands offer the levels they can make safe, and the owner chooses

Status: Proposed
Created: 2026-11-02
Candidate: none (the closest, `workbench-v1#checkpoint-levels-beyond-block`, leaves the owner-run installer commands out of its boundary; this plan takes them, on the owner's direction of 2026-11-02; it is the second of three plans that split the first version of this plan, on the owner's direction of 2026-11-03: the others are `2026-11-03-delegated-levels-and-risk-profiles` and `2026-11-03-module-conformance-levels-and-hooks`)
Specs: command-permissions, harness-rerender, harness-refresh, installer-interface, trust-and-approval

## Goal

No command is limited to the terminal by design, except `wb rerender` while the accepted `2026-10-27-rerender-is-terminal-only`
stands; increment D may propose a record that supersedes it. Every owner-run installer command offers `ask` (bound to the digest of a
read-only preview) and `none` wherever an honest preview can be made, and says in the spec why where it cannot. Shipped defaults stay
as they are.

## Scope

In:

- how an installer command reads and verifies its level where no project is rendered yet;
- `ask` for `wb install`, `wb adopt`, `wb upgrade` and `wb add` (their previews exist), then previews and levels for `wb attach`,
  `wb recover`, `wb approve`, `wb pin` and the two acknowledge tiers;
- `wb rerender` under its own record;
- `wb doctor` for the new levels, and the specs as built.

## Non-goals

- Changing a shipped default, the compiled floor or the personal `floor` list.
- `delegated` for any key and named risk profiles: the plan `2026-11-03-delegated-levels-and-risk-profiles`.
- The owner-run arguments of first-party modules, `wb verify` and the author guide, and where a module's hook is registered: the plan
  `2026-11-03-module-conformance-levels-and-hooks`.
- Who may approve a plan.
- The harness's global configuration and its own prompts.
- Any change to the registry's structure; plan `2026-11-02-permission-system-consistency` builds it and this plan adds to it.

## Assumptions and constraints

- **This plan starts only after `2026-11-02-permission-system-consistency` is `Completed`** (it is). It builds on the registry, the kit's
  preview-digest helper, the corpus and `wb doctor` that plan delivers.
- Every installer command here has a preview or needs one built. A digest that does not bind the preview's content makes `ask` a
  rubber stamp, so each preview is tested to change when the content changes and to be recomputed inside the command's own lock.
- All increments edit the installer, tests and documents; none edits `packages/workbench/`.
- Any change to what a key offers changes the settings version and the rendering record; the owner runs `wb rerender` in a terminal
  after each increment that changes a rendered rule, and `wb doctor` says when it is due. The settings version is also bumped by
  `2026-11-03-delegated-levels-and-risk-profiles` (increment B, if profiles are kept); whichever builds second builds on the version
  the first left.
- A decision record is written `Proposed`; accepting it is a checkpoint at level `ask`.
- **A spec is never left false between increments.** An increment that changes what a command offers, or how it is run, updates the
  lines of the specs that its change makes false (`command-permissions.md`, `installer-interface.md`, `trust-and-approval.md` and the
  command's own spec) in the same commit; increment E then replaces what remains "intended" and checks the whole.
- Increments B, C and D are separable: the owner may drop any of them.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. The record of increment A is accepted. For increment D either a new record is accepted, or the existing accepted record
   `2026-10-27-rerender-is-terminal-only` is named by the spec as the one that stands. No accepted record is rewritten; a superseded
   record changes only its status line, once its successor is accepted.
2. `wb install`, `wb adopt`, `wb upgrade` and `wb add` offer `ask`; a run without a digest, or with a stale one, is refused; the
   attempt and the outcome are logged; each works in a project that is not yet rendered, or the spec names why it cannot.
3. `wb attach`, `wb recover`, `wb approve`, `wb pin` and the acknowledge tiers each offer `ask` with a preview and digest, or the
   spec names the reason one cannot and the record that keeps it so.
4. `wb rerender` is decided: it offers `ask` or `none` by a mechanism that a stale rendering cannot grant itself, or it stays
   `block` by a recorded decision that names the reason.
5. No setting an owner can write reads other than as written without `wb doctor` saying so.

## Increments

### Increment A — Decision: where an installer command reads its level

**Outcome:** a `Proposed` record states how `install`, `adopt`, `attach` and `add` read and verify their level when the project has
no rendered record, and what the `ask` flow is for them.
**Dependencies:** `2026-11-02-permission-system-consistency` completed (the registry, the kit's preview-digest helper, the drift
test, the gate corpus and `wb doctor`).
**Affected areas:** `docs/decisions/` and its index.
**Steps:**
1. Read `command-permissions.md` ("`wb release-approvals` at `ask`", "Rendering"), `harness-refresh.md`, `levelrun.py` and
   `2026-10-30-release-approvals-at-ask` (the plan).
2. State the problem: `ask` works through a rule rendered in a project's settings, and these commands run before or while a project
   is rendered. State how `release-approvals` solved it (the owner's own settings in the guarded store).
3. Decide, per command, whether the same route applies, what the preview must bind, and which commands cannot offer `ask` (and
   why). List the alternatives with the reason each was rejected.
4. Run `wb run code-work check`. Stop with the record `Proposed`.
**Verification:** the document check passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#A`.

### Increment B — `ask` for the installer commands that have a preview

**Outcome:** `wb install`, `wb adopt`, `wb upgrade` and `wb add` offer `ask`, bound to the digest of their `wb preview`.
**Dependencies:** A accepted.
**Affected areas:** the registry, `install.py`, `adoptplan.py`, `upgrade.py`, `levelrun.py`, `rendering.py`,
`tests/test_install_levels.py`, `tests/test_upgrade_levels.py`, `tests/test_upgrade_preview.py`, `tests/test_adopt_preview.py`,
`tests/test_levels.py`.
**Steps:**
1. Write the tests first: the key offers `ask`; a run without a digest, or with a stale one, is refused; the digest changes when
   the preview's content changes; the attempt and outcome are logged.
2. Build each as `release-approvals` is, using the kit's preview-digest helper (`workbench/wbkit/digest.py`, from
   `2026-11-02-permission-system-consistency`): the preview prints `digest:`, the command takes `--digest`,
   and the digest is recomputed inside the command's own lock.
3. Make `wb settings` and `wb doctor` stop reporting "not offered" for a setting the key now offers.
**Verification:** the tests named above, and the drift test (`tests/test_permissions_drift.py`, from
`2026-11-02-permission-system-consistency`).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#B`.

### Increment C — Previews and levels for the remaining installer commands

**Outcome:** `wb attach`, `wb recover`, `wb approve`, `wb pin` and the acknowledge tiers each offer `ask` with a read-only preview
and a digest, or the spec records why one cannot.
**Dependencies:** B.
**Affected areas:** `attach.py`, `recover.py`, `approve.py`, `pins.py`, `pinplan.py`, `acknowledge.py`, the registry, the matching
tests (`tests/test_approve_pin_levels.py`, `tests/test_ack_recover_levels.py`, `tests/test_levels.py`).
**Steps:**
1. For each command read what it changes and what a preview could show honestly. Where none can, record the reason in the spec;
   do not invent a digest of nothing.
2. Write the tests first, then build the preview and the `--digest` form as in B.
3. This increment may be split into a plan of its own if it grows beyond one reviewable commit.
**Verification:** the tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#C`.

### Increment D — `wb rerender` under its own record

**Outcome:** the owner's decision on whether `wb rerender` may offer `ask` or `none`, and the build if it does.
**Dependencies:** B.
**Affected areas:** `docs/decisions/` (a record), then `rerender.py`, `rendering.py`, the registry, `tests/test_rerender.py`, and in
the same commit as any change of behaviour every current spec that says rerender is terminal-only and `block` only:
`docs/specs/harness-rerender.md`, `harness-refresh.md`, `command-permissions.md` ("Re-rendering an attached clone", "Not built") and
`installer-interface.md`.
**Steps:**
1. Draft a `Proposed` record that names `2026-10-27-rerender-is-terminal-only` and either supersedes it with a mechanism or leaves it
   standing (then no record is needed, and this step ends with that statement). The old record's text is not touched; its status
   line, and nothing else, names the successor only after the owner accepts the new record (the `draft-decision` skill allows
   exactly that change). A rerender changes the rules that govern the agent and reads its own level through the record it
   repairs. State a design (for example `ask` bound to the digest of `wb preview rerender`, verified against the owner's settings
   file and not the rendering) or recommend leaving it `block`, with the reason. Stop for the owner.
2. If accepted with a mechanism, write the tests first (a stale rendering cannot grant itself the level), then build it, and update
   the four specs named above in the same commit, so that none says "terminal-only" of a command that now offers a level.
3. If the owner leaves it `block`, record that in the spec as a decision and close the increment.
**Verification:** `tests/test_rerender.py` and the tests of `rendering`.
**Evidence:** one or two local commits (the record, then the build), each with the trailer
`Plan: 2026-11-02-permission-levels-for-every-command#D`.

### Increment E — Walk-through and the specs as built

**Outcome:** each new level is run once in this clone and recorded; the specs describe what is built.
**Dependencies:** all earlier increments that the owner kept.
**Affected areas:** this plan's Result; `docs/specs/command-permissions.md`, `harness-rerender.md`, `harness-refresh.md`,
`installer-interface.md` (the "Agent may run it" line of each command that gained `ask`, today "by default no; the approver may set it
to `none`", and the terminal-only wording of `install`, `adopt`, `upgrade`, `add`, `attach`, `recover`, `pin` and `approve`),
`trust-and-approval.md` (the `via` of an approval made at `ask`, today "plan approval only", and the rendered enforcement of each
command that gained `ask`), `docs/development.md`.
**Steps:**
1. Run `wb doctor`; the owner fixes what it flags and reruns `wb rerender` in a terminal.
2. For each command that gained `ask`, run its preview and its command with the digest once, in a throwaway project where the command
   changes files; record the output.
3. Replace "intended" text with "built" in each spec named above, citing the increment and the test; remove from "Not built" only
   what is built; record what stays `block` and the decision that keeps it so. Tell the owner the roadmap file is not edited.
4. Run the document check.
**Verification:** the runs above, as run; the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#E`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. After E, rerun only `wb doctor`, the
document check and the drift test and gate corpus of `2026-11-02-permission-system-consistency` (`tests/test_permissions_drift.py`,
`tests/test_gate_corpus.py`). The full suite runs only if the owner decides after the author states what could break outside the
tested area.

## Risks and sensitive actions

- **Relaxing a level lets the agent run a dangerous command.** That is the owner's chosen risk. Defaults stay `block`, the floor is
  untouched, and `wb doctor` reports a relaxed dangerous key as a risk.
- **A digest that does not bind the preview's content makes `ask` a rubber stamp.** Each preview is tested to change when its
  content changes and to be recomputed inside the command's lock.
- **`wb rerender` changes the rules that govern the agent.** Increment D may leave it `block`; any mechanism must be one a stale
  rendering cannot grant itself.
- **Installer commands change installed files and a project's trust record.** Each `ask` is bound to the preview digest and logged.
- **Accepted decisions outrank code.** A conflict is settled by a new superseding record, never by rewriting an accepted one.

## Review record

- **Reviewer:** the project's review bridge `ask-codex`, model `gpt-5.6-terra`, effort `medium`, through
  `wb run review-engine review-plan` (2026-11-03), asked for by the owner after the additions about the `action-review` shadow hook.
- **Rounds:** 4 of the bound of 4 (the owner extended the bound from 3 at `ask`, with the digest of the preview), no convergence:
  each round returned meaningful findings, and the edits made for the last round have not been reviewed. Nine findings in all; 8
  applied, 1 rejected. The findings of rounds 1 and 2 were about the plan as first written; those of rounds 3 and 4 were about the
  additions made after round 2 (the pairing step and its specs), none about the hook material of increments G and H.
- **Applied:**
  - Round 1: the header and increment J did not name `installer-interface` and `trust-and-approval`, which still describe the
    commands as terminal-only and `ask` as plan approval only (both are named now, with their lines); criterion 1 counted three
    decisions while increment D may keep the existing record (it now names records for A and G and either a new or the standing
    record for D); "plan 1" was ambiguous in six places (each names the exact plan and artifact).
  - Round 2: `wb verify` would have run a candidate module's preview before the module is approved or pinned, which the module contract
    does not allow, and a throwaway project is not a sandbox. Increment F now keeps `wb verify` non-executing (it checks the declaration
    and the shipped text), and moves the preview's behaviour to a conformance test in the kit that a module's own tests run against its
    own helper; the risk, the criterion and the affected areas say so.
  - Round 3: nothing took the pairing of the `remote-runner` commands `submit` and `fetch` with the two remote checkpoints, which the
    spec and decision 5 of `2026-11-02-one-permission-registry-and-key-model` assign to this plan (increment E now drafts a record with
    options and a recommendation, stops for the owner, and builds the choice; criterion 5 and the scope name it); increment D could
    change `wb rerender` while four specs still said terminal-only (D now updates them in the same commit, and a plan-wide rule says
    no spec is left false between increments).
  - Round 4: the pairing step changes the specs of `mempalace` and `remote-runner`, which the header did not list (both are listed
    now, in the step that changes them and in increment J); one option of the pairing step moved the commands' shipped default from
    `none` to `block`, which the plan's goal and non-goals rule out (it is out of the step and listed under deferred work as a separate
    candidate for the owner's own scope and decision).
- **Rejected:** round 1, the claim that step 1 of increment D edits an accepted record. The step says the record's text is untouched and
  that only its status line names the successor once the owner accepts it, which the `draft-decision` skill allows; a clarifying
  clause was added instead.
- **Split (2026-11-03):** the owner redirected increment G of the first version (the `action-review` module is to be the delegate to a
  bridge that provides the approvals for delegated levels), approved the plan once, and then asked for the plan to be split in three
  after a fifth round could not run (the bridge refused with `vendor_error reply_too_large`, twice; no round was spent; the plan's
  Specs line named nine specs of about 485 KB, which Codex reads for a plan). This file keeps increments A to D of the first version
  unchanged, and its old walk-through as increment E. Increments G and I went to `2026-11-03-delegated-levels-and-risk-profiles`; E, F
  and H went to `2026-11-03-module-conformance-levels-and-hooks`. The review above covered the first version, in particular
  increments A to D as they stand here; it did not cover the split, and the owner's approval of the first version no longer holds
  (this plan reads "changed since approval"). The review engine's state for the first version stays with this file's review key (4 of
  the bound of 5 rounds used, the bound extended by the owner at `ask`).
- **Left for the owner:** review of this plan, with the rounds the engine allows, or the owner's decision to approve it as it stands;
  the plan stays `Proposed`, and approving it is the owner's act.

## Deferred work

- Reading the harness's global configuration (`workbench-v1#global-settings-check`).
- Per-project overrides of the owner's personal settings.
- `delegated` for keys other than `approve-plan`, and the hook that decides: `2026-11-03-delegated-levels-and-risk-profiles` and the
  `action-review` plan after its shadow period.
- Module arguments' levels, `wb verify` and the author guide: `2026-11-03-module-conformance-levels-and-hooks`.

## Result

Empty until work starts.
