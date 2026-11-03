# Every command offers the levels it can make safe, and the owner chooses

Status: Proposed
Created: 2026-11-02
Candidate: none (the closest, `workbench-v1#checkpoint-levels-beyond-block`, leaves the owner-run installer commands out of its boundary; this plan takes them, on the owner's direction of 2026-11-02, and does not touch `delegated`)
Specs: command-permissions, module-contract, harness-rerender, harness-refresh

## Goal

No command is limited to the terminal by design, except `wb rerender` while the accepted `2026-10-27-rerender-is-terminal-only`
stands; increment D may propose a record that supersedes it. Every owner-run command and argument offers `ask` (bound to the digest of a
read-only preview) and `none` wherever an honest preview can be made, and says in the spec why where it cannot. The owner picks
a risk appetite per key, or a named profile, within the danger classes the registry holds, and shipped defaults stay as they are.
A module author, first-party or external, gets a `wb verify` check and a short guide that tell them when a declaration, a
preview or a shipped skill does not fit the system.

## Scope

In:

- how an installer command reads and verifies its level where no project is rendered yet;
- `ask` for `wb install`, `wb adopt`, `wb upgrade` and `wb add` (their previews exist), then previews and levels for `wb attach`,
  `wb recover`, `wb approve`, `wb pin` and the two acknowledge tiers;
- `wb rerender` under its own record;
- the owner-run arguments of `mempalace` (`init`, `mine`) and `remote-runner` (`fetch-overwrite`);
- the `wb verify` conformance checks for modules and the author guide;
- named risk profiles, with a per-key override;
- `wb doctor` for the new levels, and the specs as built.

## Non-goals

- Changing a shipped default, the compiled floor or the personal `floor` list.
- `delegated` for keys other than `approve-plan`.
- Who may approve a plan.
- The harness's global configuration and its own prompts.
- Any change to the registry's structure; plan `2026-11-02-permission-system-consistency` builds it and this plan adds to it.

## Assumptions and constraints

- **This plan starts only after `2026-11-02-permission-system-consistency` is `Completed`.** It builds on the registry, the kit's
  preview-digest helper, the corpus and `wb doctor` that plan delivers; none exist before.
- Every installer command here has a preview or needs one built. A digest that does not bind the preview's content makes `ask` a
  rubber stamp, so each preview is tested to change when the content changes and to be recomputed inside the command's own lock.
- Increments E and F edit `packages/workbench/` (scripted pass, owner's release). The others edit the installer, tests and documents.
- Any change to what a key offers changes the settings version and the rendering record; the owner runs `wb rerender` in a terminal
  after each increment that changes a rendered rule, and `wb doctor` says when it is due.
- A decision record is written `Proposed`; accepting it is a checkpoint at level `ask`.
- Increments B, C, D, E, G and H are separable: the owner may drop any of them.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. Three decisions are accepted and recorded, none rewriting an accepted record.
2. `wb install`, `wb adopt`, `wb upgrade` and `wb add` offer `ask`; a run without a digest, or with a stale one, is refused; the
   attempt and the outcome are logged; each works in a project that is not yet rendered, or the spec names why it cannot.
3. `wb attach`, `wb recover`, `wb approve`, `wb pin` and the acknowledge tiers each offer `ask` with a preview and digest, or the
   spec names the reason one cannot and the record that keeps it so.
4. `wb rerender` is decided: it offers `ask` or `none` by a mechanism that a stale rendering cannot grant itself, or it stays
   `block` by a recorded decision that names the reason.
5. The owner-run arguments of `mempalace` and `remote-runner` declare `levels` and `preview`, or the module spec names why they stay
   `block`.
6. `wb verify` refuses a module whose declared preview does not print a `digest:` line of 32 lowercase hex or whose wrong digest is
   not refused, and warns on a shipped skill or agent that says to never run an argument whose declared levels include `ask` or
   `none`; a module can declare the danger class of an owner-run argument, and the review engine's `extend`, `archive` and `amend`
   read as `project`; the author guide and a minimal example module exist.
7. The owner can select a profile (cautious, balanced, trusting, as the record defines them) and override any key; `wb settings`
   prints the profile and what it set; `wb doctor` reports a relaxed key in a dangerous class as a risk.
8. No setting an owner can write reads other than as written without `wb doctor` saying so.

## Increments

### Increment A — Decision: where an installer command reads its level

**Outcome:** a `Proposed` record states how `install`, `adopt`, `attach` and `add` read and verify their level when the project has
no rendered record, and what the `ask` flow is for them.
**Dependencies:** plan 1 completed.
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
2. Build each as `release-approvals` is, using the kit helper of plan 1: the preview prints `digest:`, the command takes `--digest`,
   and the digest is recomputed inside the command's own lock.
3. Make `wb settings` and `wb doctor` stop reporting "not offered" for a setting the key now offers.
**Verification:** the tests named above, and the drift test of plan 1.
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
**Affected areas:** `docs/decisions/` (a record), then `rerender.py`, `rendering.py`, the registry, `tests/test_rerender.py`,
`docs/specs/harness-rerender.md`.
**Steps:**
1. Draft a `Proposed` record that names `2026-10-27-rerender-is-terminal-only` and either supersedes it with a mechanism or leaves it
   standing (then no record is needed, and this step ends with that statement). The old record's text is not touched; its status
   line names the successor only after the owner accepts the new record. A rerender changes the rules that govern the agent and reads its own level through the record it
   repairs. State a design (for example `ask` bound to the digest of `wb preview rerender`, verified against the owner's settings
   file and not the rendering) or recommend leaving it `block`, with the reason. Stop for the owner.
2. If accepted with a mechanism, write the tests first (a stale rendering cannot grant itself the level), then build it.
3. If the owner leaves it `block`, record that in the spec as a decision and close the increment.
**Verification:** `tests/test_rerender.py` and the tests of `rendering`.
**Evidence:** one or two local commits (the record, then the build), each with the trailer
`Plan: 2026-11-02-permission-levels-for-every-command#D`.

### Increment E — First-party modules declare their owner-run arguments' levels

**Outcome:** `mempalace init` and `mine` and `remote-runner fetch-overwrite` declare `levels` and a `preview`, or the module spec
names why they stay `block`.
**Dependencies:** B; plan 1's kit helper.
**Affected areas:** the declarations, helpers and tests of `mempalace` and `remote-runner` under `packages/workbench/`; their specs.
**Steps:**
1. For each argument decide with the accepted records whether a preview can show the effect honestly (what `init` would write, what
   `mine` would index, what `fetch-overwrite` would replace). Where it can, write the test first, then the preview and the digest
   recomputed in the helper's lock using the kit helper.
2. Declare `levels` and `preview`; `wb verify` passes the module.
3. One scripted pass for the package edits; the owner starts it and releases the approvals.
**Verification:** the modules' own tests, `tests/test_verify.py`, `tests/test_owner_argument_levels.py`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#E`.

### Increment F — Module conformance: `wb verify` and the author guide

**Outcome:** a module author, first-party or external, is told when the module does not fit the permission system.
**Dependencies:** E.
**Affected areas:** `workbench/verify.py`, `workbench/declarations.py`, `workbench/levels.py`, `workbench/wbkit/` (only if a check
needs shared code), `tests/test_verify.py`, `tests/test_levels_facts.py`, `docs/specs/module-contract.md`, the `review-engine`
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
1. Write the tests first for `wb verify`: refuse a module whose declared preview does not print a `digest:` line of 32 lowercase
   hex, or whose wrong or missing digest is not refused; warn on a shipped skill or agent that says to never run an argument whose
   declared levels include `ask` or `none`; warn on a closed command list that leaves out `wb settings` while the skill depends on
   a level.
2. Build the checks. The preview runs only in a throwaway project and with the pinned helper, never against the owner's tree.
3. Write the guide: how to declare `owner`, `levels` and `preview`; the digest rule; what a skill may say; and the example module.
**Verification:** `tests/test_verify.py`, the kit tests. A module's helper runs in a throwaway project, which is a subprocess and
untrusted-input surface; the author asks the owner once whether to run a security review.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#F`.

### Increment G — Decision: risk profiles

**Outcome:** a `Proposed` record defines named profiles, or rejects them with the reason.
**Dependencies:** B.
**Affected areas:** `docs/decisions/` and its index.
**Steps:**
1. Define what each profile sets per danger class (cautious is today's shipped defaults; the others relax named classes only), that
   a per-key entry overrides the profile, and that no profile relaxes the floor or a key whose class the record marks dangerous
   beyond `ask`.
2. List the alternative of per-key levels only, and why a profile is or is not worth the second concept.
3. Run the document check. Stop with the record `Proposed`.
**Verification:** the document check passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#G`.

### Increment H — Profiles in the settings

**Outcome:** the owner can select a profile and override a key; `wb settings` and `wb doctor` show what it set.
**Dependencies:** G accepted.
**Affected areas:** `workbench/settings.py`, `workbench/settingscmd.py`, the registry, `workbench/doctor.py`, `tests/test_settings.py`,
`tests/test_settingscmd.py`, `tests/test_doctor.py`.
**Steps:**
1. Write the tests first: a profile sets the levels the record defines; a key entry overrides it; an unknown profile, or one that
   would relax a key past what the key offers, reads as `block` and is reported; the settings version is bumped and the old
   version still reads.
2. Build it; keep the file's strict form.
3. `wb doctor` reports the profile and each key it relaxed in a dangerous class.
**Verification:** the tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#H`.

### Increment I — Walk-through and the specs as built

**Outcome:** each new level is run once in this clone and recorded; the specs describe what is built.
**Dependencies:** all earlier increments that the owner kept.
**Affected areas:** this plan's Result; `docs/specs/command-permissions.md`, `module-contract.md`, `harness-rerender.md`,
`harness-refresh.md`, `docs/development.md`.
**Steps:**
1. Run `wb doctor`; the owner fixes what it flags and reruns `wb rerender` in a terminal.
2. For each command that gained `ask`, run its preview and its command with the digest once, in a throwaway project where the command
   changes files; record the output.
3. Replace "intended" text with "built"; remove from "Not built" only what is built; record what stays `block` and the decision that
   keeps it so. Tell the owner the roadmap file is not edited.
4. Run the document check.
**Verification:** the runs above, as run; the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#I`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. After I, rerun only `wb doctor`,
`wb verify packages/workbench`, the document check and the drift test and gate corpus of plan 1. The full suite runs only if the
owner decides after the author states what could break outside the tested area.

## Risks and sensitive actions

- **Relaxing a level lets the agent run a dangerous command.** That is the owner's chosen risk. Defaults stay `block`, the floor is
  untouched, profiles cannot relax a dangerous class past `ask`, and `wb doctor` reports a relaxed dangerous key as a risk.
- **A digest that does not bind the preview's content makes `ask` a rubber stamp.** Each preview is tested to change when its
  content changes and to be recomputed inside the command's lock.
- **`wb rerender` changes the rules that govern the agent.** Increment D may leave it `block`; any mechanism must be one a stale
  rendering cannot grant itself.
- **Installer commands change installed files and a project's trust record.** Each `ask` is bound to the preview digest and logged.
- **Package edits (E) make the shipped approval stale** until the owner's release; plan 1's behaviour then explains it.
- **A running helper in `wb verify` is a subprocess surface.** It runs in a throwaway project with the pinned helper only.
- **Accepted decisions outrank code.** A conflict is settled by a new superseding record, never by rewriting an accepted one.

## Review record

Empty until a review is asked for.

## Deferred work

- `delegated` for the keys other than `approve-plan` (`checkpoint-levels-beyond-block`).
- Reading the harness's global configuration (`workbench-v1#global-settings-check`).
- Per-project overrides of the owner's personal settings.

## Result

Empty until work starts.
