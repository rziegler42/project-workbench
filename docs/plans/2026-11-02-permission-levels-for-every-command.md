# Every command offers the levels it can make safe, and the owner chooses

Status: Proposed
Created: 2026-11-02
Candidate: none (the closest, `workbench-v1#checkpoint-levels-beyond-block`, leaves the owner-run installer commands out of its boundary; this plan takes them, on the owner's direction of 2026-11-02, and does not touch `delegated`)
Specs: command-permissions, module-contract, harness-rerender, harness-refresh, installer-interface, trust-and-approval, action-review, mempalace, remote-runner

## Goal

No command is limited to the terminal by design, except `wb rerender` while the accepted `2026-10-27-rerender-is-terminal-only`
stands; increment D may propose a record that supersedes it. Every owner-run command and argument offers `ask` (bound to the digest of a
read-only preview) and `none` wherever an honest preview can be made, and says in the spec why where it cannot. The owner picks
a risk appetite per key, or a named profile, within the danger classes the registry holds, and shipped defaults stay as they are.
A module author, first-party or external, gets a `wb verify` check and a short guide that tell them when a declaration, a
preview or a shipped skill does not fit the system, and what a module that ships a harness hook says about where the owner
registers it. The record on risk profiles also says how a hook that answers permission requests (the review engine deciding, which
the `action-review` module builds after its shadow period) fits the levels, so that the first such hook is built into a rule and not
beside one.

## Scope

In:

- how an installer command reads and verifies its level where no project is rendered yet;
- `ask` for `wb install`, `wb adopt`, `wb upgrade` and `wb add` (their previews exist), then previews and levels for `wb attach`,
  `wb recover`, `wb approve`, `wb pin` and the two acknowledge tiers;
- `wb rerender` under its own record;
- the owner-run arguments of `mempalace` (`init`, `mine`) and `remote-runner` (`fetch-overwrite`), and the pairing of the
  `remote-runner` commands `submit` and `fetch` with the checkpoints `submit-remote-job` and `fetch-remote-output` (a decision, then
  its build);
- the `wb verify` conformance checks for modules and the author guide;
- named risk profiles, with a per-key override, and the decision of how a hook that decides (an engine that answers a permission
  request) relates to a level or a profile, including the keys it may never answer;
- what a module that ships a harness hook (today the `action-review` shadow hook) says about where the owner registers it, so
  that registering it does not make the rendering stale, and what `wb doctor` notes about a hook the installer did not render;
- `wb doctor` for the new levels, and the specs as built.

## Non-goals

- Changing a shipped default, the compiled floor or the personal `floor` list.
- `delegated` for keys other than `approve-plan`.
- Who may approve a plan.
- The harness's global configuration and its own prompts.
- Any change to the registry's structure; plan `2026-11-02-permission-system-consistency` builds it and this plan adds to it.
- Building a hook that decides, or changing the shadow hook: that is the `action-review` plan after its shadow period. This plan only
  decides how such a hook fits the levels, and writes down where a module's hook is registered.

## Assumptions and constraints

- **This plan starts only after `2026-11-02-permission-system-consistency` is `Completed`.** It builds on the registry, the kit's
  preview-digest helper, the corpus and `wb doctor` that plan delivers; none exist before.
- Every installer command here has a preview or needs one built. A digest that does not bind the preview's content makes `ask` a
  rubber stamp, so each preview is tested to change when the content changes and to be recomputed inside the command's own lock.
- Increments E and F edit `packages/workbench/` (scripted pass, owner's release), and so does increment H if the record of G chooses
  a declared hook field. The others edit the installer, tests and documents.
- The `action-review` shadow hook (built by another session and merged into `main`, commit `8dc30ca`; not yet installed by the owner)
  is a `PermissionRequest` hook for `Bash` that records what the review engine would say about each prompted command and decides
  nothing (`docs/specs/action-review.md`, "The shadow hook"). It is the first module to ship a harness hook. A command that raises a
  prompt is exactly what the level system makes prompt: a module's `asks` minimum, a key at `ask`, and the floor's asks. The installer
  hashes the two project settings files it renders into (the permissions file and the shared file), and an edit to either makes the
  keys at `ask` and `none` read `block` until a rerender (`command-permissions.md`, "Rendering"), so where the owner registers a hook
  matters.
- Any change to what a key offers changes the settings version and the rendering record; the owner runs `wb rerender` in a terminal
  after each increment that changes a rendered rule, and `wb doctor` says when it is due.
- A decision record is written `Proposed`; accepting it is a checkpoint at level `ask`.
- **A spec is never left false between increments.** An increment that changes what a command offers, or how it is run, updates the
  lines of the specs that its change makes false (`command-permissions.md`, `installer-interface.md`, `trust-and-approval.md` and the
  module's own spec) in the same commit; increment J then replaces what remains "intended" and checks the whole.
- Increments B, C, D, E, G, H and I are separable: the owner may drop any of them.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. The records of increments A and G are accepted. For increment D either a new record is accepted, or the existing accepted record
   `2026-10-27-rerender-is-terminal-only` is named by the spec as the one that stands. No accepted record is rewritten; a superseded
   record changes only its status line, once its successor is accepted.
2. `wb install`, `wb adopt`, `wb upgrade` and `wb add` offer `ask`; a run without a digest, or with a stale one, is refused; the
   attempt and the outcome are logged; each works in a project that is not yet rendered, or the spec names why it cannot.
3. `wb attach`, `wb recover`, `wb approve`, `wb pin` and the acknowledge tiers each offer `ask` with a preview and digest, or the
   spec names the reason one cannot and the record that keeps it so.
4. `wb rerender` is decided: it offers `ask` or `none` by a mechanism that a stale rendering cannot grant itself, or it stays
   `block` by a recorded decision that names the reason.
5. The owner-run arguments of `mempalace` and `remote-runner` declare `levels` and `preview`, or the module spec names why they stay
   `block`, and the pairing of the `remote-runner` commands `submit` and `fetch` with the two remote checkpoints is decided by an
   accepted record and built as it says.
6. `wb verify` stays a check that runs nothing of the module: it refuses a declaration that does not fit the permission system (a
   declared `preview` that names no argument or an owner-run argument, `ask` offered without a preview, an unknown danger class)
   and warns on a shipped skill or agent that says to never run an argument whose declared levels include `ask` or `none`. The
   behaviour of a module's preview (a `digest:` line of 32 lowercase hex, a wrong or missing digest refused) is checked by a
   conformance test in the kit that the module's own tests run against its own helper, before the module is offered for approval.
   A module can declare the danger class of an owner-run argument, and the review engine's `extend`, `archive` and `amend` read as
   `project`; the author guide and a minimal example module exist.
7. The owner can select a profile (cautious, balanced, trusting, as the record defines them) and override any key; `wb settings`
   prints the profile and what it set; `wb doctor` reports a relaxed key in a dangerous class as a risk.
8. No setting an owner can write reads other than as written without `wb doctor` saying so.
9. The record of increment G says whether a hook that answers permission requests is a level, a profile element or neither, and names
   the keys it may never answer (the author recommends: every key bound to a digest, that is the keys at `ask` that carry a
   preview). The module guide and the `action-review` spec say where a module's hook is registered so that the rendering stays
   current (the author recommends the owner's user-level settings, not the two project files the installer hashes), and `wb doctor`
   notes a hook in a rendered project file that the installer did not render.

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

### Increment E — First-party modules declare their owner-run arguments' levels

**Outcome:** `mempalace init` and `mine` and `remote-runner fetch-overwrite` declare `levels` and a `preview`, or the module spec
names why they stay `block`; and the pairing of the `remote-runner` commands `submit` and `fetch` with the checkpoints
`submit-remote-job` and `fetch-remote-output` is decided and built as the record says (the spec and decision 5 of
`2026-11-02-one-permission-registry-and-key-model` assign it to this plan).
**Dependencies:** B; the kit's preview-digest helper of `2026-11-02-permission-system-consistency`.
**Affected areas:** the declarations, helpers and tests of `mempalace` and `remote-runner` under `packages/workbench/`; their specs;
`docs/decisions/` (the pairing record); `docs/specs/mempalace.md` and `docs/specs/remote-runner.md` (the levels and previews of the
three arguments and the pairing, in the same commit as the change); and, as the record decides, `workbench/levels.py`,
`workbench/declarations.py`, `docs/specs/module-contract.md` and `docs/specs/command-permissions.md` ("Not built").
**Steps:**
0. **The pairing.** The checkpoints `submit-remote-job` and `fetch-remote-output` (read `block`) and the commands
   `wb run remote-runner submit` and `fetch` (read `none`, with the module's `asks` rendering a prompt either way) govern the same
   acts and keep a level each; the registry does not record the pairing since it would name a module
   (`2026-11-03-conformance-tests-name-modules-and-module-pins-follow-the-levels`, decision 2), and the spec records it. Draft a
   `Proposed` record that says which key governs each act, with every shipped default and offered level unchanged. The options: leave
   two keys and have the module declare the pairing (a field, read by the registry without naming a module) so that `wb doctor` can
   say when a checkpoint reads `block` while its command reads `none`; or keep the spec's record as it is. State the consequence of
   each, and recommend one. Mapping the commands to the checkpoints (extending `checkpoint_of` to an argument that carries an `asks`)
   would move the commands' default from `none` to `block`, a change of a shipped default that this plan does not make: it is a
   separate candidate for the owner's own scope and decision (see Deferred work), and the record may name it as such. Stop for the
   owner. If a mechanism is accepted, write the tests first, build it, and update the registry, the module contract and the specs in
   the same commit.
1. For each argument decide with the accepted records whether a preview can show the effect honestly (what `init` would write, what
   `mine` would index, what `fetch-overwrite` would replace). Where it can, write the test first, then the preview and the digest
   recomputed in the helper's lock using the kit helper.
2. Declare `levels` and `preview`; `wb verify` passes the module.
3. One scripted pass for the package edits; the owner starts it and releases the approvals.
**Verification:** the modules' own tests, `tests/test_verify.py`, `tests/test_owner_argument_levels.py`, and, for step 0, the tests of
the mechanism the record chose (`tests/test_levels_facts.py`, `tests/test_declarations.py`, `tests/test_permissions_drift.py`).
**Evidence:** one or two local commits (the record, then the build), each with the trailer
`Plan: 2026-11-02-permission-levels-for-every-command#E`.

### Increment F — Module conformance: `wb verify` and the author guide

**Outcome:** a module author, first-party or external, is told when the module does not fit the permission system.
**Dependencies:** E.
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
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#F`.

### Increment G — Decision: risk profiles, and how a hook that decides fits the levels

**Outcome:** a `Proposed` record defines named profiles, or rejects them with the reason, and says how a hook that answers
permission requests relates to the levels.
**Dependencies:** B.
**Affected areas:** `docs/decisions/` and its index.
**Steps:**
1. Define what each profile sets per danger class (cautious is today's shipped defaults; the others relax named classes only), that
   a per-key entry overrides the profile, and that no profile relaxes the floor or a key whose class the record marks dangerous
   beyond `ask`.
2. List the alternative of per-key levels only, and why a profile is or is not worth the second concept.
3. **A hook that decides.** The `action-review` shadow records what its engine would answer for each prompted `Bash` command; the
   plan after the shadow period builds a hook that answers (`allow` or `deny`) instead. State how that fits the levels. The options:
   a new level between `ask` and `none` that a key may offer; an element of a profile; or neither, the hook staying outside the
   levels and running only where no key governs the command. Whichever is chosen: a key bound to a preview digest (`ask` is the
   owner's confirmation of that exact digest) is never answered by an engine, because the engine would stand in for the owner's act;
   the floor and the compiled hard stops are never answered by it; a hook never changes the level a key reads, only answers a
   request that the level already lets reach a prompt; and what the shadow must show before the answering hook is built stays the
   action-review plan's to say. The author recommends the third option for the first answering hook (outside the levels, for the
   commands a module's `asks` and the engine's rules cover, such as `safe-git commit` and `remove`), and a level only if the owner
   later wants a key-by-key choice. Read the shadow's spec and its labelled data before writing the record.
4. Run the document check. Stop with the record `Proposed`.
**Verification:** the document check passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#G`.

### Increment H — A module's hook: where it is registered, what `wb verify` and `wb doctor` say

**Outcome:** the owner knows where to register a hook that a module ships so that the rendering stays current, a module author is
told what to say about their hook, and `wb doctor` notes a hook in a rendered project file that the installer did not render.
**Dependencies:** F, G accepted.
**Affected areas:** the module guide of increment F and `docs/specs/module-contract.md`; `docs/specs/action-review.md` (its owner steps
for installing the shadow hook); `workbench/doctor.py` and `tests/test_doctor.py`; and only if the record of G chooses a declared
hook field: `workbench/declarations.py`, `workbench/verify.py`, `tests/test_declarations.py`, `tests/test_verify.py` and the
`action-review` declaration under `packages/workbench/` (a package edit: a scripted pass and the owner's release).
**Steps:**
1. Read what the module ships today: `action-review` lists `hook/shadow_hook.py` and `hook/shadow_store.py` under `ships`, with no
   kind, and the spec says the owner registers `python3 -B <path>/shadow_hook.py` as a `PermissionRequest` hook for `Bash`. Check by a
   run on a copy that registering a hook in the permissions file, or in the shared file, makes a key at `ask` read `block` and makes
   `wb doctor` say the file differs from the record; record the output.
2. Write the guide section and the spec's owner steps: a module that ships a hook says which event and tool it registers for,
   whether it answers anything, and that the owner registers it in their user-level settings, not in the two project files the
   installer hashes; `action-review.md` is brought level with that (its owner steps today say only "registers").
3. Write the tests first for `wb doctor`: a rendered project file that holds a hook the installer did not render gives a `note` that
   names the file, the event and the tool and not the command line's arguments; a hook the installer rendered (the edit gate and the
   command gate) gives none; a damaged or large file gives the finding of increment L of `2026-11-02-permission-system-consistency`.
   Then build the note.
4. Only if the record of G chose a declared field (for example `hooks`, naming the event, the tool and whether the program answers):
   write the tests first (`wb verify` refuses an unknown event, a hook file that is not under `ships`, and a program that is declared
   as not answering but whose source holds an answer object, as the shadow's own test already checks for its source), build it,
   declare it in the `action-review` module and run the package pass. Otherwise leave the declaration as it is.
**Verification:** `tests/test_doctor.py`, `tests/test_verify.py` and `tests/test_declarations.py` (the last two only for step 4), the
document check. A declared field is parsing of a module's declaration, an untrusted-input surface; if step 4 runs, the author asks the
owner once whether to run a security review.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#H`.

### Increment I — Profiles in the settings

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
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#I`.

### Increment J — Walk-through and the specs as built

**Outcome:** each new level is run once in this clone and recorded; the specs describe what is built.
**Dependencies:** all earlier increments that the owner kept.
**Affected areas:** this plan's Result; `docs/specs/command-permissions.md`, `module-contract.md`, `harness-rerender.md`,
`harness-refresh.md`, `mempalace.md` and `remote-runner.md` (what the levels and previews of their arguments and the pairing now
say), `installer-interface.md` (the "Agent may run it" line of each command that gained `ask`, today "by default no;
the approver may set it to `none`", and the terminal-only wording of `install`, `adopt`, `upgrade`, `add`, `attach`, `recover`, `pin`
and `approve`), `trust-and-approval.md` (the `via` of an approval made at `ask`, today "plan approval only", and the rendered
enforcement of each command that gained `ask`), `action-review.md` (the owner steps for the shadow hook, increment H),
`docs/development.md`.
**Steps:**
1. Run `wb doctor`; the owner fixes what it flags and reruns `wb rerender` in a terminal.
2. For each command that gained `ask`, run its preview and its command with the digest once, in a throwaway project where the command
   changes files; record the output.
3. Replace "intended" text with "built" in each spec named above, citing the increment and the test; remove from "Not built" only
   what is built; record what stays `block` and the decision that keeps it so. Tell the owner the roadmap file is not edited.
4. Run the document check.
**Verification:** the runs above, as run; the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-levels-for-every-command#J`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. After J, rerun only `wb doctor`,
`wb verify packages/workbench`, the document check and the drift test and gate corpus of `2026-11-02-permission-system-consistency`
(`tests/test_permissions_drift.py`, `tests/test_gate_corpus.py`). The full suite runs only if the
owner decides after the author states what could break outside the tested area.

## Risks and sensitive actions

- **Relaxing a level lets the agent run a dangerous command.** That is the owner's chosen risk. Defaults stay `block`, the floor is
  untouched, profiles cannot relax a dangerous class past `ask`, and `wb doctor` reports a relaxed dangerous key as a risk.
- **A digest that does not bind the preview's content makes `ask` a rubber stamp.** Each preview is tested to change when its
  content changes and to be recomputed inside the command's lock.
- **`wb rerender` changes the rules that govern the agent.** Increment D may leave it `block`; any mechanism must be one a stale
  rendering cannot grant itself.
- **Installer commands change installed files and a project's trust record.** Each `ask` is bound to the preview digest and logged.
- **Package edits (E) make the shipped approval stale** until the owner's release; the refusal line of `2026-11-02-permission-system-consistency` (increment J) then explains it.
- **`wb verify` must never run candidate module code.** It checks the declaration and the shipped text only; verification comes
  before approval and pinning, and a throwaway project is not a sandbox. The preview's behaviour is a conformance test in the kit,
  run by the module's own tests under the author's authority, so the kit code that starts a helper is the one subprocess surface.
- **A hook that answers permission requests stands in for the owner's confirmation.** Increment G only decides how it fits; the
  record keeps it away from every key bound to a digest and from the floor, and building it is the `action-review` plan's, after
  its shadow period.
- **Registering a hook in a hashed project file makes the rendering stale.** Increment H records where to register it and has
  `wb doctor` note an unrendered hook; until the owner has done that, the owner's `ask` and `none` keys read `block` after such an edit.
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
- **Left for the owner:** the bound of 4 is used; the ceiling is 5. A fifth round needs the owner's `extend` of this review (at `ask`: a
  preview and then the command with its digest) and would check the edits of round 4, which are small (two specs added to a list,
  one option removed); or the owner accepts the plan as it stands. The plan stays
  `Proposed`: approving it is the owner's, and a review is not an approval. Note for the owner: this plan's increments E and H each stop
  for the owner at a `Proposed` record (the pairing; the profile and deciding-hook record is G's), and increment H may add a declared
  hook field only if the record of G chooses one.

## Deferred work

- `delegated` for the keys other than `approve-plan` (`checkpoint-levels-beyond-block`).
- Reading the harness's global configuration (`workbench-v1#global-settings-check`).
- Per-project overrides of the owner's personal settings.
- Mapping the `remote-runner` commands `submit` and `fetch` onto the checkpoints `submit-remote-job` and `fetch-remote-output`
  (extending `checkpoint_of`): it moves the commands' shipped default from `none` to `block`, so it needs its own candidate, scope and
  decision by the owner.
- The hook that decides (the review engine answering `PermissionRequest`), and the shadow's own install and labelling: the
  `action-review` plan after its shadow period.

## Result

Empty until work starts.
