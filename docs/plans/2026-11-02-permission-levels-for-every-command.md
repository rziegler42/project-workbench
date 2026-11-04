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
- The owner-run arguments of first-party modules, the pairing of `wb run remote-runner submit` and `fetch` with the checkpoints
  `submit-remote-job` and `fetch-remote-output` (`command-permissions.md` now assigns it there), `wb verify` and the author guide, and
  where a module's hook is registered: the plan `2026-11-03-module-conformance-levels-and-hooks`.
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
  command's own spec) in the same commit; increment F then replaces what remains "intended" and checks the whole.
- C needs B, and D (the record), E (its build) and F (the walk-through) need B's registry work. The owner may drop C, or D with E,
  or both; dropping B drops all of them. The completion criteria apply to the increments the owner kept, and each one dropped is
  named under Deferred work with the reason.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. The record of increment A is accepted. For increment D either a new record is accepted, or the existing accepted record
   `2026-10-27-rerender-is-terminal-only` is named by the spec as the one that stands. No accepted record is rewritten; a superseded
   record changes only its status line, once its successor is accepted.
2. If B is kept: `wb install`, `wb adopt`, `wb upgrade` and `wb add` offer `ask`; a run without a digest, or with a stale one, is refused; the
   attempt and the outcome are logged; each works in a project that is not yet rendered, or the spec names why it cannot.
3. If C is kept: `wb attach`, `wb recover`, `wb approve`, `wb pin` and the acknowledge tiers each offer `ask` with a preview and digest, or the
   spec names the reason one cannot and the record that keeps it so.
4. If D is kept: `wb rerender` is decided: it offers `ask` or `none` by a mechanism that a stale rendering cannot grant itself, or it stays
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
`tests/test_levels.py`; and the specs the change makes false, in the same commit: `docs/specs/command-permissions.md`,
`docs/specs/installer-interface.md`, `docs/specs/trust-and-approval.md` and the command's own spec (`harness-refresh.md` for
`upgrade`).
**Steps:**
1. Write the tests first: the key offers `ask`; a run without a digest, or with a stale one, is refused; the digest changes when
   the preview's content changes; the attempt and outcome are logged.
2. Build each as `release-approvals` is, using the kit's preview-digest helper (`workbench/wbkit/digest.py`, from
   `2026-11-02-permission-system-consistency`): the preview prints `digest:`, the command takes `--digest`,
   and the digest is recomputed inside the command's own lock.
3. Make `wb settings` and `wb doctor` stop reporting "not offered" for a setting the key now offers.
4. Update, in the same commit, each line of the specs above that this change makes false (the "Agent may run it" line and the
   terminal-only wording of the four commands, the `via` of an approval made at `ask`); leave the rest "intended" for increment F.
**Verification:** the tests named above, and the drift test (`tests/test_permissions_drift.py`, from
`2026-11-02-permission-system-consistency`).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#B`.

### Increment C — Previews and levels for the remaining installer commands

**Deferred (2026-11-03, on the owner's direction):** C stopped at its step 4 because it does not fit one reviewable commit. Its scope and
criterion 3 move to the successor plan `2026-11-03-levels-for-recover-pin-approve-attach`, which splits it by command group. Nothing below
is built here; see Deferred work. D, E and F depend only on B and are unaffected.

**Outcome:** `wb attach`, `wb recover`, `wb approve`, `wb pin` and the acknowledge tiers each offer `ask` with a read-only preview
and a digest, or the spec records why one cannot.
**Dependencies:** B.
**Affected areas:** `attach.py`, `recover.py`, `approve.py`, `pins.py`, `pinplan.py`, `acknowledge.py`, the registry, the matching
tests (`tests/test_approve_pin_levels.py`, `tests/test_ack_recover_levels.py`, `tests/test_levels.py`); `docs/decisions/` (a record for
each command that stays without `ask`, unless an accepted record already keeps it so); and, in the same commit, the
specs the change makes false: `docs/specs/command-permissions.md`, `docs/specs/installer-interface.md`,
`docs/specs/trust-and-approval.md` and the command's own spec.
**Steps:**
1. For each command read what it changes and what a preview could show honestly. Where none can, do not invent a digest of nothing:
   cite a specific existing accepted record that keeps the command without `ask`, or draft a `Proposed` record (the `draft-decision`
   skill) that gives the reason and names the command, stop for the owner's acceptance at the `accept-decision` checkpoint, and then
   record the reason and the accepted record in the spec. A command is not left without `ask` on the spec's word alone
   (completion criterion 3).
2. Write the tests first, then build the preview and the `--digest` form as in B.
3. Update, in the same commit, each line of the specs above that this change makes false, as in B step 4.
4. If this increment grows beyond one reviewable commit, stop and report. Do not split it inside this plan. The owner then either
   marks C deferred here, with the reason under Deferred work (the completion criteria then apply without C, as the separability
   text says), or approves a successor plan that takes C's scope and criteria; no work on the successor begins before its own approval.
**Verification:** the tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#C`.

### Increment D — Decision: `wb rerender` under its own record

**Outcome:** the owner's decision on whether `wb rerender` may offer `ask` or `none`, recorded.
**Dependencies:** B.
**Affected areas:** `docs/decisions/` (a record, or none if the standing record is kept), and the spec that names the standing record
if it is kept: `docs/specs/command-permissions.md` ("Re-rendering an attached clone").
**Steps:**
1. Draft a `Proposed` record that names `2026-10-27-rerender-is-terminal-only` and either supersedes it with a mechanism or leaves it
   standing (then no record is needed, and this step ends with that statement). The old record's text is not touched; its status
   line, and nothing else, names the successor only after the owner accepts the new record (the `draft-decision` skill allows
   exactly that change). A rerender changes the rules that govern the agent and reads its own level through the record it
   repairs. State a design (for example `ask` bound to the digest of `wb preview rerender`, verified against the owner's settings
   file and not the rendering) or recommend leaving it `block`, with the reason. Stop for the owner.
2. If the owner leaves it `block`, record that in the spec as a decision and close the plan's work on rerender: increment E is not
   built.
**Verification:** the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#D`.

### Increment E — Build the rerender level the record accepts

**Outcome:** `wb rerender` offers the level the accepted record names, by a mechanism that a stale rendering cannot grant itself.
Not built if D ends with the standing record kept.
**Dependencies:** D, with a record accepted.
**Affected areas:** `rerender.py`, `rendering.py`, the registry, `tests/test_rerender.py`, and in the same commit every current spec
that says rerender is terminal-only and `block` only: `docs/specs/harness-rerender.md`, `harness-refresh.md`,
`command-permissions.md` ("Re-rendering an attached clone", "Not built") and `installer-interface.md`.
**Steps:**
1. Write the tests first (a stale rendering cannot grant itself the level), then build it as the record says.
2. Update the four specs named above in the same commit, so that none says "terminal-only" of a command that now offers a level.
**Verification:** `tests/test_rerender.py` and the tests of `rendering`, and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#E`.

### Increment F — Walk-through and the specs as built

**Outcome:** each new level is run once in this clone and recorded; the specs describe what is built.
**Dependencies:** all earlier increments that the owner kept.
**Affected areas:** this plan's Result; `docs/specs/command-permissions.md`, `harness-rerender.md`, `harness-refresh.md`,
`installer-interface.md` (the "Agent may run it" line of each command that gained `ask`, today "by default no; the approver may set it
to `none`", and the terminal-only wording of `install`, `adopt`, `upgrade`, `add`, `attach`, `recover`, `pin` and `approve`),
`trust-and-approval.md` (the `via` of an approval made at `ask`, today "plan approval only", and the rendered enforcement of each
command that gained `ask`), `docs/development.md`.
**Steps:**
1. Run `wb doctor`; the owner fixes what it flags and reruns `wb rerender` in a terminal.
2. For each command that gained `ask`, run its preview and its command with the digest once, in a throwaway project and with the
   store isolated: a throwaway project does not isolate the guarded store, which `wb approve`, `wb pin`, `wb attach` and others write,
   so each run sets `HOME` to a new empty scratch directory (the store is fixed under `HOME`, mode 0700; no installer variable moves
   it) and never uses the owner's store. Before the first run list the scratch directory; after each command list again and record
   every file it created or changed outside the project, with the command, so the non-project writes of each are enumerated by
   observation. Record the output, and say in the Result that the scratch directory holds only throwaway data and was left in place
   or removed (a removal is the owner's, through `wb run safe-git remove`).
3. Replace "intended" text with "built" in each spec named above, citing the increment and the test; remove from "Not built" only
   what is built; record what stays `block` and the decision that keeps it so. Tell the owner the roadmap file is not edited.
4. Run the document check.
**Verification:** the runs above, as run; the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#F`.

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
- **Fresh review of the split version (2026-11-03):** `ask-codex` (gpt-5.6-terra, medium) through the review engine, after the owner's
  reset (a new window, bound 3), 3 of 3 rounds used (engine rounds 5 to 7), not converged. Round 1, three major findings, all
  applied: the remote-runner pairing's assignment in `command-permissions.md` still named this plan (the spec now names
  `2026-11-03-module-conformance-levels-and-hooks`, and Non-goals say so); B and C named no specs although the plan requires
  same-commit spec updates (both now list them and step it); the walk-through did not isolate the guarded store (it now runs under a
  scratch `HOME` and records each non-project write by observation). Round 2, one major, applied: C allowed a spec-only reason for a
  command without `ask`, against completion criterion 3 (C now requires an accepted record). Round 3, two major, applied: the criteria
  were unconditional although B and C are separable (they now apply to the increments kept), and D held two commits (D is the record,
  E the build, F the walk-through). The edits after round 3 were not reviewed; the bound is reached, so another round needs the
  owner's extend.
- **Renumbered (2026-11-03), round 7:** the review of this split version found that increment D held two commits, so D (the record)
  and E (the build) are separate increments and the walk-through is F; the text above that speaks of the walk-through as increment
  E describes the first version.
- **Round 8 (2026-11-03), bound extended to 4 by the owner:** one major finding (R8-F1), applied: increment C's permitted split
  into a plan of its own had no completion path; step 4 now stops and reports, and the owner defers C or approves a successor plan.
  The round did not converge; its fix is unreviewed.
- **Left for the owner:** review of this plan, with the rounds the engine allows, or the owner's decision to approve it as it stands;
  the plan stays `Proposed`, and approving it is the owner's act.

## Deferred work

- Increment C (`ask` for `wb attach`, `wb recover`, `wb approve`, `wb pin` and the acknowledge tiers), with completion criterion 3: it
  does not fit one reviewable commit (reason in the Result, "Increment C — stopped at its step 4"). The successor plan
  `2026-11-03-levels-for-recover-pin-approve-attach` takes its scope and criterion, in three increments. Until that plan is approved and
  built, these commands stay at `block` and `none`, as the specs say.
- Reading the harness's global configuration (`workbench-v1#global-settings-check`).
- Per-project overrides of the owner's personal settings.
- `delegated` for keys other than `approve-plan`, and the hook that decides: `2026-11-03-delegated-levels-and-risk-profiles` and the
  `action-review` plan after its shadow period.
- Module arguments' levels, `wb verify` and the author guide: `2026-11-03-module-conformance-levels-and-hooks`.

## Result

### Increment A — Decision: where an installer command reads its level (2026-11-03)

- **Done:** one new record, `Proposed`:
  `docs/decisions/2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest.md`. It decides that a command with a terminal
  test (`install`, `adopt`, `upgrade`, `add`, and in C `recover`, `approve`, `pin` and the acknowledge tiers) reads the verified level
  only and fails closed; that `attach`, which has no terminal test, also reads the owner's setting, as `release-approvals` does; the
  `ask` flow; that the `ask` digest binds what is decided and leaves out the seed and time a run generates; and the per-command table
  for B and C. No code and no spec changed.
- **Found while reading:** `wb preview install` and the run build the plan in two processes with a random seed and a fresh time, so
  the plan's own digest cannot be the `ask` digest. For `upgrade` and `add` the record does not assume it; B tests each command.
- **Verification run:** `wb run code-work check` and `wb check`, both "check found no problems", after the review's edits.
- **Review:** `reviewer` agent, one round, no blocking finding, nine not blocking. All nine applied to the record: the need for a new
  reading beside `levelrun.route` (the kit's `may_run` is unchanged), the target identity and other fields the digest keeps, the
  upgrade and add claim narrowed, "lock" corrected, the test wording, a digest at `none` refused as `release-approvals` does, the
  effect of the `balanced` and `trusting` profiles, and the evidence list made honest about what was read in full.
- **Accepted:** by the owner on 2026-11-03 at the `accept-decision` checkpoint, level `ask` (`wb run groundwork preview`, then
  `accept` with the digest it printed). This is completion criterion 1 for increment A.
- **Not done:** nothing is committed (this was A's line; A is committed as `6bb2437`).

### Increment B — `ask` for the installer commands that have a preview (2026-11-03)

- **Done:** `wb install`, `wb adopt`, `wb upgrade` and `wb add` offer `block`, `ask` and `none` (`levels.py`). `--digest <32 hex>` is read once by
  `sources.parse_install(…, digest_ok=True)` for those four and refused by the previews. `levelrun.route_ask` reads the verified level and goes on
  at `ask` and `none` (the kit's `may_run` is unchanged); `levelrun.digest_refusal` refuses a digest at a terminal and at `none`, and a missing or
  malformed one at `ask`. `wb preview install|adopt|upgrade|add` print a note and `digest: <32 hex>` before `preview only: …`. The run builds the
  plan, builds it again with `preview.ASK_SEED` and `preview.ASK_NOW`, and compares the `ask` digest of that plan before it prints or writes; the
  attempt is logged at `ask` with `digest:<32 hex>`. Specs updated in the same change: `command-permissions.md` (new section "The installer
  commands at `ask`", and the lines for the offers, profiles, the two "at `none`" paragraphs and the summary), `installer-interface.md`,
  `docs/development.md`.
- **Differs from the record's wording (decision 3):** the digest is `wbkit.digest.of(["wb <command>", <digest of the plan built with the fixed
  seed and time>])`, not a hash of printed lines. It binds at least as much, and the spec describes it. The accepted record is not edited; the
  owner may want a dated clarification note.
- **Known limit, not closed:** the written plan and the plan the digest was taken over are two builds a moment apart (a package source rewritten
  mid-run to another approved tree). Recorded in the spec's "What it does not prove". Closing it needs a further build and a second comparison.
- **Effect on profiles:** `balanced` and `trusting` now read these four keys at `ask` (as the record says); a `wb rerender` is due for an owner
  who names one.
- **Verification run** (`python3 -B -W error -m unittest`, targeted; the full suite was not run): `test_install_levels`, `test_upgrade_levels`,
  `test_levelrun`, `test_levels`, `test_levels_facts`, `test_permissions_drift`, `test_preview`, `test_upgrade_preview`, `test_adopt_preview`,
  `test_install`, `test_upgrade`, `test_add`, `test_adopt`, `test_install_attach`, `test_install_pins`, `test_upgrade_pins`, `test_self_hosting`,
  `test_approve_levels`, `test_ack_recover_levels`, `test_approve_pin_levels`, `test_release_ask`, `test_recover`, `test_unfinished`,
  `test_acknowledge`, `test_installplan`, `test_upgradeplan`, `test_adopt_lifecycle`, `test_adopt_target`, `test_command_gate`,
  `test_gate_corpus`, `test_rendering`, `test_rerender`, `test_attach`, `test_permissions`, `test_wbkit_digest`, `test_wbkit_levels`,
  `test_settingscmd`, `test_doctor`, `test_planapprovals`, `test_delegation`: all OK. `test_settings` and `test_cli` by `discover`: OK.
  `wb run code-work check` and `wb check`: no problems. Existing tests that described the old registry or the old preview were updated (the
  list of keys that offer `ask`, the profile tests, the settings output, the preview endings).
- **Review:** `reviewer` agent, one round, no blocking finding, six not blocking. Applied: the spec lines that were still false (summary,
  "no flag" in two paragraphs, the `add` row, the "nothing is generated after the digest" rule), the usage-error row, the statement that a
  `--source` is fetched before the check, the limit above, and tests for a digest given twice on the install command line, a stale digest
  with nothing to change, and a plan for another project at `ask`. Not applied: an extra build to close the limit above (owner's call).
- **Not covered by a test:** a change to what the harness would render (this fixture's harness renders no permissions, so `home` does not move
  the plan); the exclusion list is guarded by the seed/time test and the module/target tests, not by one test per field.
- **Committed:** `7e4512f`, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#B`. The owner has not run `wb rerender` or set
  any of the four keys. The owner accepted the limit above; the clarification note on the record is to be proposed with increment C.

### Increment C — stopped at its step 4 (2026-11-03)

- **Nothing built, nothing changed in code or specs.** I read the entry points and the confirmation of each command and sized the increment
  against step 4 ("if this increment grows beyond one reviewable commit, stop and report").
- **What each command has today** (read, not run): `wb recover` and `wb acknowledge` already compute a read-only examination with a digest
  (`recover.examine`, `acknowledge.examine`; the typed flow compares the first 12 characters and the run examines again), so each needs a
  `wb preview` entry, a `--digest` option and the B route. `wb pin` shows the helper's path, size and sha256 and compares the first 12
  characters of that hash; it needs a preview entry and the same. `wb approve` verifies a package (and, with `--source`, fetches it) and
  confirms by typed digest of the request; it needs a preview that does the verification without recording. `wb attach` has no preview and no
  terminal test: it needs a preview of what it would write and the owner's-settings reading of the decision (decision 1, second bullet).
  `acknowledge-second-tier` governs no command today, so it has nothing to preview and needs an accepted record that keeps it without `ask`.
- **Size:** five commands, each with a preview (every preview adds an agent-safe key to the registry, the corpus and `wb settings`), a parser
  option, the route and a digest check, its tests, and the spec lines it makes false in four documents, plus one record. Increment B did one
  family of four commands whose previews existed and came to 25 files and about 780 added lines.
- **Left for the owner:** mark C deferred here (an edit to the plan's body, which needs a new approval) and approve a successor plan, or say
  how else to go on.
- **Afterwards:** C was marked deferred, the plan was approved again, and the work moved to `2026-11-03-levels-for-recover-pin-approve-attach`
  (increments A to C done, c4a0a75).

### Increment D — Decision: `wb rerender` under its own record (2026-11-04)

- **Decision (the owner's): leave `wb rerender` at `block`.** The accepted `2026-10-27-rerender-is-terminal-only` stands and no new record was
  written; the spec names it as the one that stands (completion criterion 1) and records, in "Re-rendering an attached clone" and under
  "Not built", that `ask` was considered again on 2026-11-04 and not offered, and why. Criterion 4 is met by that: the key stays
  `block` by a recorded decision that names the reason.
- **What was weighed.** The design that would offer `ask`: read the level from the owner's own settings in the guarded store (as `attach`
  does since increment C of the successor plan), add `wb preview rerender` as the digest's source (it already lists every rule that moves,
  every `allow` rule it keeps and every entry it removes), and take `--digest`. The reason it was not chosen: a re-render writes the
  permissions file that defines what the agent may do, and the skills, agents and root file the agent reads; it keeps the live file's
  `allow` rules and records them as trusted; at `ask` the owner confirms a digest and the agent's showing of the plan is not enforced, so an
  `allow` rule an agent got into the file would be kept unread. The narrowing that would remove this (refuse at `ask` when the plan keeps
  any `allow` rule) adds a second mode to a command that is rare and cheap to run at a terminal, and it would make `rerender` a third
  reader of the owner's own settings. No other installer command with an honest preview is left without `ask`.
- **Increment E is not built** (its text: "Not built if D ends with the standing record kept").
- **Files:** `docs/specs/command-permissions.md` and this plan. Nothing in `workbench/` or the tests changed; the drift test and the
  document check pass.
- **Left for the owner:** the verdict and the word to commit; then F, the walk-through.
- **Afterwards:** committed as 6570488.

### Increment F — Walk-through and the specs as built (2026-11-04)

- **Step 1.** `wb doctor` in this clone found no problems after the owner's `wb rerender` (twice: after the successor plan's three
  increments, and after the owner set `wb upgrade` and `acknowledge-first-tier` to `ask`).
- **Step 3, the specs.** Nothing was left to turn from "intended" to "built": each increment of this plan and of the successor plan
  updated the lines its change made false in the same commit (the "Agent may run it" lines and the terminal-only wording of the commands in
  `installer-interface.md`, the `via` values in `trust-and-approval.md`, the command tables of `docs/development.md`, and the sections
  "The installer commands at `ask`", "`recover` and `acknowledge` at `ask`", "`approve` and `pin` at `ask`" and "`attach` at `ask`" of
  `command-permissions.md`). The only "intended" left in the six documents is an unrelated word in `harness-refresh.md`. **What stays
  `block`, and the decision that keeps it so:** `wb rerender` (the standing `2026-10-27-rerender-is-terminal-only`, considered again in
  increment D), `acknowledge-second-tier` (`2026-11-04-the-second-acknowledge-tier-offers-no-ask`) and every key under "Not built" in the
  spec. The roadmap file is not edited. `harness-rerender.md` and `harness-refresh.md` needed no change: they describe `wb rerender`, which did not change.
- **Step 2, the walk-through, run by the owner in their own terminal** (a script of mine was refused by the permission classifier because
  it typed the owner's confirmation through a pseudo-terminal; the script that was run types nothing and starts the two steps that need
  a terminal on the owner's own). The scripts (`walk_all.py`, `walk_rest.py`, `walklib.py`; sha256 `263e9716...`, `c9a7a6c6...`, `94d9e3a3...`)
  set `HOME` to a new empty scratch directory for every command, so the guarded store was the scratch one, and listed the scratch store
  and the target project before and after every command; the record is `walk.log` (581 lines, sha256 `93481473...`). A grep of the
  owner's own store afterwards found none of the scratch projects, so it was not touched. The scratch directory holds only throwaway
  data and was left in place; removing it is the owner's, through `wb run safe-git remove`. Run on commit 6570488, harness `claude`.
- **The setting up.** The scratch store's settings had the nine keys at `ask` (`wb install`, `adopt`, `upgrade`, `add`, `attach`,
  `recover`, `approve`, `pin`, `acknowledge-first-tier`). The owner approved a copy of `tests/fixtures/sample-package` and installed the
  scratch project at a terminal (typed confirmations). `wb settings` there read all nine at `ask`, `wb rerender` and
  `acknowledge-second-tier` at `block`, and every preview key at `none`. The rendered permissions file had, for each of the nine commands,
  `Bash(wb <command>)` and `Bash(wb <command> *)` in `ask` and none in `deny` (the only deny on a similar name is `wb approve-plan`).
- **Each command, run from the scratch project, with no terminal.** For all nine: the preview printed exactly one 32-character digest and
  wrote nothing; the command without a digest was refused (exit 1, "is at the level ask: run `wb preview <command>` ...") and wrote
  nothing; the command with the digest exited 0 and wrote what is listed. Files written **outside the project the command acts on**
  (all of them in the scratch store; the level log gained one attempt and one outcome per run, each with the level `ask` and the 32-character digest the
  preview printed as its evidence):

| command (target) | written in the target project | written in the scratch store |
|---|---|---|
| `adopt` (a repository with a file) | 95 paths: `.workbench/`, `AGENTS.md`, `docs/` | the project's `baselines`, `pins`, `seen`; the level log |
| `approve` (a package directory) | nothing | two approval records under `packages/`; the level log |
| `upgrade` (the project, to the approved copy) | `.workbench/manifest.json`, one module-owned file | the project's `baselines`; the level log |
| `acknowledge` (one edited baselined file) | nothing | the project's `baselines`; the level log |
| `pin` (a helper) | nothing | the project's `pins`; the level log |
| `install` (a new directory, harness `claude`) | about 135 files and directories, the per-clone harness files included | the project's `baselines`, `pins`, `rendering`, `seen`; the level log |
| `add` (`ask-codex`) | the module's helper and `module.json`, `.workbench/manifest.json` | the project's `baselines`, `pins`; the level log |
| `attach` (a clone with its local manifest removed) | `.workbench/local/harness.json` (the rendered files held the planned bytes and were kept) | the level log (the rendering record was written with the same bytes) |
| `recover` (an unfinished-write marker) | the marker removed | the level log |

- **What this shows beyond the tests:** the real launcher and the real `claude` harness render the nine keys as `ask` rules; the previews
  write nothing in the project or the store; a refused run changes nothing; the level was read from the scratch project's own rendering
  record for the eight commands that read only the verified level, and `attach` consults the verified level first (`levelrun.unattended`)
  and the owner's own setting only when that is neither `ask` nor `none`; the working project was rendered with `wb attach: ask`, so by the
  code's order of reading `attach` ran by the **verified-`ask` route**, the one the tests of increment C did not cover, with another clone
  as the target. The log cannot tell the two routes apart (both read `ask`). The digest the preview printed is the evidence the log holds.
- **What it does not show.** (1) Claude Code's own prompt: the commands were run by a script, not through the harness, so that the
  harness prompts for a rendered `ask` rule is the harness's behaviour and was not exercised here. (2) The first run's script mistakes
  (an install selection without `groundwork`, an `add` of `review-engine`, which needs a `model-bridge` provider) refused two previews
  and crashed the script before `attach`; they were mine and the second script ran those four steps in the same scratch folder.
  (3) The `recover` marker was made with the installer's `unfinished.build`, as the tests do, not left by a failed install; the clone
  for `attach` was made by removing its local manifest. (4) `wb doctor` in the scratch project reported one problem, that its hook runs
  `wb`, which was not on the minimal `PATH` the script gave its children: an artefact of the walk. (5) `upgrade` and `add` skipped
  `docs/notes.md` ("a newer version exists; the project's file is not touched"), the installer's rule for seeded files, unrelated to `ask`.
- **Step 4:** the document check passes.
- **Completion criteria of the plan.** 1: the record of A is accepted, and for D the standing record is named by the spec. 2 (B kept):
  `install`, `adopt`, `upgrade` and `add` offer `ask`, a run without a digest or with a stale one is refused, the attempt and outcome are
  logged, and each works in a project that is rendered (seen in the walk-through; a project that is not rendered reads `block`, which the
  spec names). 3: C was deferred; its scope and criterion went to `2026-11-03-levels-for-recover-pin-approve-attach`, whose criteria are met.
  4: `wb rerender` stays `block` by a recorded decision that names the reason. 5: `wb doctor` finds no problems with the owner's settings as
  they stand.
- **Left for the owner:** the verdict; the plan's `Status:` line; and the word to commit.
