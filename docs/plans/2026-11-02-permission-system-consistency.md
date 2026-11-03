# One permission subsystem: remove the drift, fix the refusals

Status: Approved
Created: 2026-11-02
Candidate: none (the closest, `workbench-v1#checkpoint-levels-beyond-block`, widens levels and leaves this cleanup out of its boundary; the follow-on plan `2026-11-02-permission-levels-for-every-command` takes the widening; the owner directed both on 2026-11-02)
Specs: command-permissions, module-contract, trust-and-approval, harness-refresh, review-engine

## Goal

Make the permission system one thing. Today the same facts (which keys exist, what each offers, its default, its spellings, its
preview, whether it is a command or a rule the agent follows) are kept by hand in about six places, and they have drifted. When
this plan is done there is one registry that holds those facts, the installer's rendering, `wb settings`, the gates, `wb verify`,
`wb doctor` and the module kit all read it, the checkpoints are keys in it like any command, the skills and agents say what the
registry says, and the refusals that stopped the owner's work have a cause, a fix and a test.

This plan changes no level any key offers and no shipped default. It makes the system consistent and measurable first, so the
widening in the follow-on plan is built on one table and not on six.

## Scope

**What the author found on 2026-11-02** (read from the project's files, and from the author's session transcripts, which are not
tracked; refusal counts are by message and approximate).

1. **Facts kept in several places.** The offered levels are hand-listed in `levels._OFFERS`; the command words in `rules.py`
   (`OWNER_RUN`, `AGENT_SAFE`, `PREVIEW_ACTIONS`, `SPELLINGS`); the module arguments in declarations; the rendered rules are
   written once per launcher spelling (the owner's settings file holds about 470 rules); and the same keys are described again in
   `command-permissions.md`, `docs/development.md` and the skills. A change in one has not reached the others.
2. **Two settings for one checkpoint.** The owner's file holds a `checkpoints` word (`delegate`) and a `levels` entry (`ask`) for
   `approve-plan`; `wb settings` reports "the level applies". Two representations of one decision.
3. **Two keys for one action.** `submit-remote-job` and `fetch-remote-output` (checkpoints, `block`) and the commands
   `wb run remote-runner submit` and `fetch` (level `none`, with an `ask` rule rendered) appear to govern the same acts; likewise
   `push-shared-branch` and the `git push` ask rule, and `wb run safe-git remove` (level `none`, `ask` rendered). Which one
   governs is not written down.
4. **Checkpoints that no command runs** (`fetch-remote-output`, `change-direction`, and the agent half of `push-shared-branch`) are
   rules the agent follows, read from `wb settings`; the installer enforces nothing for them. Nothing reports whether a skill
   states them the way the setting does.
5. **The command gate refuses by text.** About 70 refusals came from the rule that reads a command holding `$ ? * [ {` or a
   backtick for the letters of an owner-run command in order; it fires on a heredoc or a script that never names the command. About
   24 more came from a command that merely names a relaxed word. The same intent passes or fails with its wording.
6. **A changed package tree makes the harness "unknown" and locks every tool call.** About 43 refusals read "claude is not a known
   harness". The cause is that the harness's package no longer matches its release (`harnesses.py`, `firstparty.is_first_party`):
   a deliberate package edit, or any stray file in a package directory such as a `__pycache__`. The message names neither cause,
   and during the lock even a preview cannot run.
7. **Settings that do not take effect.** `wb upgrade`, `wb attach`, `wb approve` and `acknowledge-first-tier` set to `ask` read
   `block`; `wb settings` says so, nothing else does.
8. **Skills that contradict the levels.** `peer-review` says the agent never runs `extend`, `reset`, `archive`, `prune` and `amend`
   (all at `ask`); `delegate-approval` says never run `approve-plan` (at `ask`); `draft-plan` and `run-increment` omit the `ask`
   flow; `recall-memory` hard-codes "never" for two commands whose level an owner could raise. How many other skills close their
   command list without `wb settings` was found by keyword search and is not yet verified skill by skill (increment K reads each).
9. **State changes that look like inconsistency.** A stale approval, a rendering that is out of date and a "Yes, and don't ask
   again" prompt (which writes an `allow` rule and makes keys read `block` until a rerender) each change what works, with no
   message that names the state. Smaller: the hook's shell once could not find `wb` (about six times); the edit gate refused
   "the command code-work is not pinned (the pins file does not have the expected format)" (about six times).
10. **Nothing measures any of this.** The gate logs an owner-run attempt but not its own refusals.

In:

- three decision records (the stance, the key model and the spelling policy; what the gate reads; what the gates do while a
  package tree differs from its release);
- a regression corpus and a drift test that record today's behaviour and today's disagreements, so the cleanup has a fixed target;
- the registry, and the readers moved onto it one at a time with no change of behaviour;
- one setting per checkpoint, the checkpoints as registry keys, and the migration of existing settings and renderings;
- a kit module for the helper side (preview digests, the `ask` flow, the refusal text) and its adoption by the first-party helpers
  that carry their own copy;
- the gate rule, the changed-package behaviour and a refusal log;
- the skills and agents brought into line, and `wb doctor`;
- a walk-through in this clone and the specs as built.

## Non-goals

- Any new level for any key, any new preview, any change to a shipped default (all in `2026-11-02-permission-levels-for-every-command`).
- The compiled hard-stop floor and the personal `floor` list. A level never overrides them.
- Who may approve a plan, and what an approval means.
- The harness's own prompts and classifier, and the harness's global configuration (`workbench-v1#global-settings-check`);
  `wb doctor` reads this project's configuration and the owner's personal settings only, prints names and paths, never values.
- Raising the owner's risk appetite by default. Defaults stay as shipped.

## Assumptions and constraints

- Several increments edit files under `packages/workbench/`. Each such edit makes the shipped approval stale and the harness
  unknown until released, so each ends with a scripted pass the owner starts with "run the pass", then `wb preview
  release-approvals` and `wb release-approvals` with its digest (at level `ask` the agent may run both, the harness prompting).
  The package increments are H, K and, if a skill is touched in M, M. All other increments edit the installer, the tests and
  the documents only.
- A decision record is written `Proposed`; accepting it is a checkpoint at level `ask`: the agent previews, the owner confirms
  with the digest.
- Characterization first: increments D to G change structure, not behaviour. The tests of D pass unchanged after each of them; a
  test that must change is a finding and stops the increment.
- The settings file and `.claude/settings.local.json` are the owner's; the agent cannot write them. A migration that needs a
  change there is the owner's step, shown by `wb doctor`.
- Testing is targeted (the nearest tests of the area changed). Before any wider run, the author states what could break outside
  the tested area; the levels and the gates are read by every owner-run command, so the owner decides.
- No tracked document cites the author's transcripts or the owner's settings by path. Cases that come from them are written as
  inline, sanitised fixtures.

## Completion criteria

1. Three decisions are accepted and recorded in `docs/decisions/` and its index; none rewrites an accepted record.
2. One registry names every key (command, owner-run argument, checkpoint, agent-safe action) with its kind, offered levels,
   default, spellings, preview, the command or rule it governs and its documentation anchor. A test fails if the rendering,
   `wb settings`, a gate or the declarations disagree with it.
3. Each checkpoint is one key with one setting; the two-settings case of `approve-plan` is migrated, and a command that implements
   a checkpoint reads the checkpoint's key, or the spec names why it keeps its own.
4. The drift test passes with an empty list of known disagreements. Two directions, stated once: a module's declaration
   (`workbench/declarations.py`, `module-contract.md`) is the authoritative input for the facts that are the module's own (its
   commands, `owner` arguments, `levels`, `preview`, `checkpoint_of`); the installer's own facts (its owner-run commands, agent-safe
   actions, spellings, checkpoints) are written once, in the registry. The registry is the one reconciled, machine-readable view of
   both and rejects a declaration that conflicts with it; every rendered rule, `wb settings` line and gate input is generated from the
   registry; and every other text that states a fact (the specs, `docs/development.md`, the skills and agents) is checked against it
   by a test, not required to omit it.
5. The kit offers one preview-digest and `ask`-flow helper, and every first-party helper that carried its own copy uses it.
6. The gate no longer refuses a command only because its letters appear in order inside an expansion or a script; the corpus shows
   the real attempts are still refused; every refusal names the rule that fired.
7. When a package tree differs from its release, the refusal names the cause and the first path that differs, and the behaviour
   during the lock is the one the accepted record says, tested for a deliberate edit and for a stray file.
8. A refusal log records the rule and a hash of each gate refusal, never the command text, and `wb doctor` reports counts.
9. No shipped skill or agent contradicts a level; each closed command list that depends on a level names `wb settings`; the
   rendered copies in this clone are current.
10. `wb doctor` reports, one line each, with the key and the path and no value: a setting that reads other than set; a rule that
    disagrees with the registry; a stale rendering or approval; a package tree that differs from its release; a hook whose
    launcher does not resolve; an `allow` rule on a command the registry marks dangerous; a key relaxed in a class the record
    calls dangerous; a changed `floor`; a skill or agent that contradicts a level.
11. The four examples the owner gave (a `release-approvals` the agent can run through preview and digest; an `extend` through
    preview and digest; a refusal after a package edit; a command with a heredoc) are each a named test or a recorded run.

## Increments

### Increment A — Decision: one subsystem, one key model

**Outcome:** a `Proposed` decision states the stance and the key model: no command is terminal-only by design, with one exception
that stands: the accepted `2026-10-27-rerender-is-terminal-only` keeps `wb rerender` terminal-only and `block`-only, and this
decision does not supersede it (the follow-on plan's increment D may propose a superseding record); every key is in one registry
with a kind (command, owner-run argument, checkpoint, agent rule) and a danger class; a checkpoint has one setting, its level; which
key governs when a command implements a checkpoint; and the launcher-spelling policy.
**Dependencies:** none.
**Affected areas:** `docs/decisions/` (one new record) and its index.
**Steps:**
1. Read `2026-10-26-a-level-for-every-command`, `2026-10-28-every-key-offers-the-approve-plan-levels`,
   `2026-10-27-owner-run-arguments-take-a-level`, `trust-and-approval.md` ("Effective values") and `command-permissions.md`.
2. State the three danger classes and their shipped defaults, unchanged from today's: *reads and agent-safe* (`none`); *changes
   the project or its installed files with a preview* (`block`); *changes what governs the agent, leaves the project, deletes or
   publishes* (`block`).
3. For each of the findings 2 to 4 above, decide: the single setting of a checkpoint (the `checkpoints` word is read as a level,
   as `wb settings` already translates it, and is written only as a level), and for each pair of keys that govern one act, which
   governs. List the alternative and why it was rejected.
4. Decide the spelling policy. Propose, as the recommendation: keep every spelling, generate the rendered rules from the registry's one
   spelling list (so the count no longer matters), have `wb doctor` report a spelling that the documents or skills use and the
   generated rules do not cover, and keep the shipped skills and agents on `wb`. Record as the rejected alternative: accept only
   `wb` (and the store's `bin/wb`) and refuse the `python -m workbench` forms with one rule. Reasons: it adds refusals where the goal
   is fewer (the module form was about 8% of the author's Bash calls in this project), it needs about 43 documents rewritten, and the
   safety does not rest on the list (with a key relaxed the gate matches a launcher and the word, so an unlisted spelling is refused
   unless it is the exact simple form; at `block` the command's own terminal test refuses it). Revisit only if `wb doctor` or the
   refusal log shows a bypass or a maintenance cost.
5. State what the follow-on plan will add (levels for the keys that offer fewer), so this record does not decide it.
6. Run `wb run code-work check`. Stop with the record `Proposed`.
**Verification:** the document check passes; the record has every section of the template.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#A`. Acceptance is a
separate checkpoint, run with the digest the preview prints.

### Increment B — Decision: the command gate reads where a launcher is, not the letters of a word

**Outcome:** a `Proposed` record states what makes a command "name" a relaxed key and what is not read.
**Dependencies:** none.
**Affected areas:** `docs/decisions/` and its index.
**Steps:**
1. Read `command-permissions.md` ("The command gate"), `2026-10-26-ask-level-command-gate`, `2026-10-26-ask-level-spelling-limit`,
   `2026-10-27-command-gate-command-position` and `2026-10-27-command-gate-literal-arguments`.
2. Write the cases the decision rests on as inline fixtures: the commands that were refused only by the in-order rule (a script
   that holds the letters, a heredoc, a file name), and the attempts the rule exists to catch (a quote splice, an escape, a
   variable-built word), each sanitised and with its expected result. Include an unlisted launcher spelling
   (`python3.12 -m workbench approve-plan`) at a relaxed level, expected refused unless it is the exact simple form.
3. Propose the rule: the in-order test applies only to a command that holds a launcher in command position; the content of a script
   file is not read, as the spec's limits already say. Name what stops being caught, what remains caught, and why each is
   acceptable at each level.
4. Ask the question the spec leaves open: can the owner-run commands enforce their own level, digest and terminal checks so the
   text gate only protects the harness prompt? Record the answer and, if it is no, the reason.
5. Propose that every refusal names the rule that fired and the form that passes, and that the gate records a refusal (rule and
   hash, no text) in a log the owner can read.
6. Run the document check. Stop with the record `Proposed`.
**Verification:** the document check passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#B`.

### Increment C — Decision: what the gates do while a package tree differs from its release

**Outcome:** a `Proposed` record chooses what happens to tool calls while a shipped package has no current approval, and names
the two causes.
**Dependencies:** none.
**Affected areas:** `docs/decisions/` and its index.
**Steps:**
1. Read `gate.py`, `gate_hook.py`, `agent_gate.py`, `command_gate.py`, `harnesses.py`, `firstparty.py` and the release sections of
   `command-permissions.md`; state which calls the lock now refuses and why it fails closed (a changed package could change the
   gate itself).
2. List the options with their consequences: keep the lock and explain it; let read-only tools and the preview and release commands
   through; have the pass restore a current approval request in the same step; warn at the start of a session; make a stray
   untracked file a warning and not a lock.
3. Recommend one. The lock is tamper evidence, so the recommendation keeps it for writes and for `Bash`, explains it, and reduces
   how often it happens (one pass and one release per plan, a check for stray files before the lock). Say what an attacker who can
   edit a package gains from each option.
4. Run the document check. Stop with the record `Proposed`.
**Verification:** the document check passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#C`.

### Increment D — Characterize today: the corpus and the drift test

**Outcome:** a fixed target before anything moves: a regression corpus of gate cases, and a test that lists every place the
permission facts are kept and every disagreement between them today.
**Dependencies:** A, B and C accepted by the owner.
**Affected areas:** `tests/test_gate_corpus.py` and `tests/test_permissions_drift.py` (new), `tests/fixtures/` for the cases.
**Steps:**
1. Write the corpus from the fixtures of B: each case is a command, the level setting it runs under and the expected result
   (pass, refuse with the rule). Include every attempt the spec's limits section lists, the real forms the owner uses, and the
   unlisted launcher spelling of B, run at a relaxed level and at `block`.
   Cases where today's gate is wrong are marked as expected-wrong with the increment that fixes them.
2. Write the drift test: it reads `levels`, `rules`, the declarations, the rendering plan, `wb settings`, the owner-run table of
   `docs/development.md`, the keys table of `command-permissions.md` and the shipped skills, extracts the keys and the offered
   levels from each, and reports the disagreements. The known disagreements (findings 1 to 4 and 7) are recorded in the test as a
   list that later increments empty; any other disagreement fails.
3. Run the new tests and the neighbours. No production file changes.
**Verification:** the new tests pass with the known-disagreement list as it is; `tests/test_levels.py` and
`tests/test_command_gate.py` unchanged and passing.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#D`.

### Increment E — The registry

**Outcome:** one registry holds every key and its facts; `levels.registry` and its callers read it; nothing else changes.
**Dependencies:** D.
**Affected areas:** `workbench/levels.py` (or a module split from it, named in this increment), `workbench/rules.py`,
`workbench/declarations.py` (read only: declarations stay the authoritative input for a module's own facts and the registry
validates against them), `tests/test_levels.py`, `tests/test_permissions_drift.py`.
**Steps:**
1. Extend the `Key` record with kind, danger class, governed command or rule, spellings, preview name and documentation anchor.
   Populate it from `_OFFERS`, `OWNER_RUN`, `AGENT_SAFE`, `PREVIEW_ACTIONS`, `SPELLINGS`, the checkpoints and the declared
   arguments, so each fact is written once. The old constants are derived from the registry or removed.
2. Keep the offered levels and defaults exactly as they are today; the test of D proves it.
3. Run `tests/test_levels.py` and the drift test; the known-disagreement list shrinks where the registry now carries the fact.
**Verification:** `tests/test_levels.py`, `tests/test_settings.py`, `tests/test_settingscmd.py`, `tests/test_permissions_drift.py`,
`tests/test_owner_argument_levels.py`. This is a refactor under characterization, so any test that must change stops the increment.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#E`.

### Increment F — The readers move onto the registry

**Outcome:** the rendering, `wb settings`, the owner-argument launcher and `wb verify` read the registry; the rendered rules for
the spellings are generated from it.
**Dependencies:** E.
**Affected areas:** `workbench/rendering.py`, `workbench/settings.py`, `workbench/settingscmd.py`, `workbench/ownerargs.py`,
`workbench/verify.py`, `workbench/rerender.py`, their tests.
**Steps:**
1. Move each reader in turn, running its tests after each: rendering first, then `wb settings`, then the launcher, then `verify`.
2. If the decision A chose fewer spellings, generate the rules for them only; otherwise generate every spelling from the one list.
   Bump the rendering record's format only if its content changes, and read the old format for one version so an existing clone
   renders correctly until its next rerender.
3. Print the levels a key offers and its class in `wb settings` (an added field; the existing lines are unchanged).
**Verification:** `tests/test_rerender.py`, `tests/test_settings.py`, `tests/test_settingscmd.py`,
`tests/test_owner_argument_levels.py`, `tests/test_verify.py`, `tests/test_permissions_drift.py`, `tests/test_check.py`. Because a
rendering change affects every attached project, the author states what could break outside this and asks the owner before any wider run.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#F`.

### Increment G — Checkpoints as keys, one setting each

**Outcome:** each checkpoint is one registry key with one setting; the pairs of finding 3 are resolved as decision A says; the
agent-followed checkpoints are listed as rules with the skill that states each.
**Dependencies:** F; A accepted.
**Affected areas:** `workbench/settings.py`, `workbench/levels.py`, `workbench/rendering.py`, `workbench/delegation.py` (read
only), `docs/specs/trust-and-approval.md`, `docs/specs/command-permissions.md`, tests.
**Steps:**
1. Write the tests first: a settings file with both a `checkpoints` word and a `levels` entry for one checkpoint reads as one
   level, reports the translation once, and `wb doctor` (increment M) will flag the pair; a command that implements a checkpoint
   reads the checkpoint's key or the governing key the record names.
2. Build it. Keep reading the version 1 `checkpoints` object; write nothing new in that form.
3. For each agent-followed checkpoint, record in the registry the skill that states it (`push-changes`, `run-remote-job`,
   `draft-roadmap`, `draft-spec` and the acknowledge wording), for increment K to check.
4. The migration of an existing settings file is the owner's edit; `wb settings` prints what it read and how.
**Verification:** `tests/test_settings.py`, `tests/test_settingscmd.py`, `tests/test_checkpoint_command.py`,
`tests/test_checkpoint_command_run.py`, `tests/test_levels.py`, the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#G`.

### Increment H — The kit: preview digest and the `ask` flow, once

**Outcome:** a kit module holds the helper side of the `ask` flow; the first-party helpers that carry their own copy use it.
**Dependencies:** E.
**Affected areas:** `workbench/wbkit/` (a new module only for code two or more helpers share), the helpers of `review-engine`,
`groundwork`, `safe-git` and any other that checks a digest, their tests, `tests/test_wbkit_*.py`.
**Steps:**
1. Read how each helper and `release-approvals` compute and check a preview digest and print the refusal. Record which logic is
   duplicated; move into the kit only that. If it exists in one place, record that and add nothing.
2. Write the kit tests first: the digest is 32 lowercase hex, changes when the content changes, a wrong or missing digest is
   refused with one standard line, and the check happens inside the caller's lock (the helper passes it).
3. Move the helpers onto the kit. Do not raise `wbkit.API` unless a kit function changes shape; an addition does not.
4. The package edits are one scripted pass; the owner starts it with "run the pass" and then releases the approvals.
**Verification:** the new kit tests, `tests/test_wbkit_levels.py`, each moved helper's own tests, `tests/test_owner_argument_levels.py`.
The preview and digest are what stops `ask` being a rubber stamp, so the author asks the owner once whether to run a security
review of this increment.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#H`.

### Increment I — The gate stops refusing by letters; refusals are named and logged

**Outcome:** the false refusals of the in-order rule are gone, the real attempts are still refused, every refusal names its rule,
and each refusal is logged without the command text.
**Dependencies:** D, F; B accepted.
**Affected areas:** `workbench/command_gate.py`, `workbench/rules.py`, `workbench/gate_hook.py`, the refusal log (a new file in the
guarded store, following `levellog.py`), `tests/test_command_gate.py`, `tests/test_gate_hook.py`, `tests/test_gate_corpus.py`.
**Steps:**
1. Flip the expected-wrong cases of the corpus to their intended result and see them fail.
2. Change the rule as decision B says. Keep the exact-simple-command and literal-argument exemptions.
3. Name the rule in each refusal line. Log the rule name and a hash of the command, never its text; cap the log's size and refuse to
   grow it past the cap without failing a call.
4. Run the gate's tests and the corpus.
**Verification:** `tests/test_command_gate.py`, `tests/test_gate_hook.py`, `tests/test_gate_corpus.py`, `tests/test_levelrun.py`,
`tests/test_agent_gate.py`. This changes the control that stops an agent running an owner-run command, so the author asks the owner
whether to run a security review of this increment before it is committed.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#I`.

### Increment J — A changed package tree is explained

**Outcome:** the lock of increment C's record is built as it says, and its refusal names the cause.
**Dependencies:** C accepted; I.
**Affected areas:** `workbench/gate.py`, `workbench/gate_hook.py`, `workbench/agent_gate.py`, `workbench/command_gate.py`,
`workbench/harnesses.py`, `workbench/firstparty.py` (read), their tests.
**Steps:**
1. Write the tests first, separately for a deliberate edit to a package file and for a stray untracked file in a package directory.
2. Replace "<harness> is not a known harness whose layout ..." with a line that says why: the package tree differs from its
   release, with the first path that differs, or the approval is missing; and which command the owner or the agent runs. A path,
   never a value.
3. Build the behaviour the record chose for each cause.
**Verification:** `tests/test_gate.py`, `tests/test_gate_hook.py`, `tests/test_agent_gate.py`, `tests/test_command_gate.py`. The
author asks the owner once whether to run a security review of this increment.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#J`.

### Increment K — Skills and agents agree with the registry

**Outcome:** no shipped skill or agent contradicts a level; each states the rule the registry holds.
**Dependencies:** G, H.
**Affected areas:** the shipped skills and agents under `packages/workbench/` (rendered into `.claude/skills/` and
`.claude/agents/`), the policy blocks that render into `AGENTS.md`, and a new test that reads them against the registry.
**Steps:**
1. Read every shipped skill and agent and list, per file, each instruction that depends on a level or a checkpoint. This replaces
   the keyword search of the findings.
2. Write the test first: it reads the shipped text against the registry (the agent-followed checkpoints of G, the `ask` flow, the
   closed command lists) and fails on the current text.
3. Rewrite each contradicting line on the model `draft-decision` already follows: "at `ask`, run the preview, show the digest, run
   the command with it; at `none`, run it; at `block`, ask the owner". Keep "never" only for the floor and the hard stops. Add
   `wb settings` to each closed command list that depends on a level.
4. Check that the `security-reviewer` agent's pinned command list fits `security-review`.
5. One scripted pass; the owner starts it and releases the approvals; then the owner runs `wb upgrade`, the preview of the rerender
   and `wb rerender` (terminal) to refresh the rendered copies. `wb rerender` refreshes the rendered skills, agents and root file as
   built by the plan `2026-10-28-refresh-rendered-harness` (`harness-refresh.md`, "As built" and acceptance 1 and 3, not the
   pre-build description in its "Assumptions and constraints"); the increment's verification shows `wb preview rerender` listing each file current.
**Verification:** the new test; `tests/test_verify.py`; the document check; after the owner's rerender, `wb preview rerender` lists
every rendered skill and agent as current.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#K`.

### Increment L — `wb doctor`

**Outcome:** `wb doctor` prints the problems and risks of criterion 10, read-only, agent-safe, one line each, key and path and no
value, with the one command that clears each state.
**Dependencies:** F, G, I, J, K.
**Affected areas:** `workbench/cli.py`, a new `workbench/doctor.py`, `workbench/rules.py` and the registry (`wb doctor` is added as an
agent-safe key), `tests/test_doctor.py` (new), `tests/test_levels.py`, `tests/test_settingscmd.py`, `docs/development.md`,
`docs/specs/command-permissions.md` (the agent-safe keys it enumerates).
**Steps:**
1. Write the tests first: `wb doctor` is a registry key of kind agent-safe with the shipped default `none`, appears in `wb settings`,
   renders no rule at its default and renders a `deny` if the owner sets it to `block`; then one test per check, each on a
   throwaway project.
2. Build it with two severities: `problem` (the configuration does not do what it says) and `risk` (it does what it says and the
   class is dangerous). Exit 0 unless a problem is found; a risk never fails. It reads the refusal log of I for counts.
3. It prints names and paths, never values; it decides nothing.
4. Record the command in `docs/development.md`.
**Verification:** `tests/test_doctor.py`, `tests/test_settingscmd.py`, `tests/test_check.py`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#L`.

### Increment M — Walk-through in this clone, and the specs as built

**Outcome:** each finding is re-run once in this clone and recorded; the specs and `docs/development.md` describe what is built.
**Dependencies:** L.
**Affected areas:** this plan's Result; `docs/specs/command-permissions.md`, `module-contract.md`, `trust-and-approval.md`,
`harness-refresh.md`, `review-engine.md`, `docs/development.md`.
**Steps:**
1. Run `wb doctor`; the owner fixes what it flags in their settings (the four `ask` lines and any `allow` rule). Ask the owner to
   run the `fewer-permission-prompts` skill for the harness's own read-only prompts, which are outside the workbench's gate.
2. Re-run, one call each: an `extend` through preview and digest; a `release-approvals` through preview and digest; a script with a
   heredoc; a compound command that holds a relaxed word as data; a stray file in a package directory; a deliberate package edit.
3. Record each as fixed, accepted limit or deferred, with the output.
4. Replace "intended" text with "built" text in the specs, citing the increment and the test; remove from "Not built" only what is
   built. Tell the owner that the roadmap file is not edited.
5. Run the document check.
**Verification:** the commands above, as run; the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-permission-system-consistency#M`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. After M, rerun only: `wb doctor` in this
clone, `wb verify packages/workbench`, the document check, the drift test and the gate corpus. The full suite runs only if the owner
decides after the author states what could break outside the tested area.

## Risks and sensitive actions

- **The gate is the control that stops an agent running an owner-run command.** I and J change it; the corpus names the attempts that
  must stay refused; the author asks once per surface whether to run a security review (H, I, J) and runs one only if the owner asks.
- **A refactor of the registry touches every owner-run command.** E to G run under the characterization tests of D; a test that must
  change stops the increment.
- **A digest that does not bind the preview's content would make `ask` a rubber stamp.** H tests that the digest changes with the
  content and is checked inside the caller's lock.
- **Package edits make the shipped approval stale** (H, K): each ends in a scripted pass the owner starts and a release the owner
  confirms; until then tool calls are refused, which J makes explicable.
- **The refusal log must not become a leak.** It holds a rule name and a hash, never the text, and its size is capped.
- **Rendering needs the owner's `wb rerender` in a terminal** after F and K; until then the rendered copies are old and `wb doctor`
  says so.
- **Accepted decisions outrank code.** If an accepted decision conflicts with a test written here, the decision wins and a new
  record supersedes it; no accepted record is rewritten.

## Review record

- **Reviewer:** the project's review bridge (`ask-codex`, model `gpt-5.6-terra`, effort medium), through the review engine.
- **Rounds:** 2 of a bound of 3 (ceiling 5). Both rounds read `changes_needed`; every finding is decided. No third round was run.
- **Applied (4):**
  - R1-F2: `wb doctor` is a new agent-safe key, so increment L lists the registry, `rules.py`, the spec's enumeration of agent-safe
    keys and tests for its `wb settings` line and its rendering.
  - R1-F3: criterion 4 made the registry the sole machine-readable source, with generated outputs and tested documents, instead of
    requiring that no other text state a fact.
  - R2-F1: increment A keeps `wb rerender` terminal-only under the accepted `2026-10-27-rerender-is-terminal-only` and does not
    supersede it; the follow-on plan was corrected the same way.
  - R2-F2: criterion 4 and increment E state two directions: a module's declaration is authoritative for the module's own facts,
    the registry holds the installer's facts and reconciles both and rejects a conflicting declaration.
- **Rejected (1):** R1-F1 (that `wb rerender` does not refresh rendered skills and agents). The text cited is the pre-build
  description in `harness-refresh.md`; its "As built" part and `docs/development.md` show the command does. Increment K now points
  to the as-built part and checks `wb preview rerender`.
- **Before the review**, the author's own pass changed the plan after the owner's questions: the spelling policy (keep every
  spelling, generate the rules), the changed-package cause, and the split into two plans.
- **Left for the owner:** a third review round was available and not used; the follow-on plan
  `2026-11-02-permission-levels-for-every-command` has had no review and waits on this plan's completion; the decisions A to C
  are the owner's to accept at their checkpoints.

## Deferred work

All of the following are in the plan `2026-11-02-permission-levels-for-every-command`: `ask` for the installer commands, previews
for the rest, `wb rerender` under its own record, the owner-run arguments of `mempalace` and `remote-runner`, the module
conformance check and author guide, and named risk profiles. Also deferred: `delegated` for keys other than `approve-plan`
(`checkpoint-levels-beyond-block`), and reading the harness's global configuration (`global-settings-check`).

## Result

### Increment A — Decision: one subsystem, one key model

- **Done:** `docs/decisions/2026-11-02-one-permission-registry-and-key-model.md`, `Proposed`. It reaffirms the accepted records
  (decisions 1 to 6 of `2026-10-26-a-level-for-every-command`, the `wb rerender` exception, the clarification note), puts the
  facts of every key in one registry (module declarations authoritative for a module's own facts, the registry reconciling),
  names four kinds of key and three danger classes (information only; no default or offered level changes), says which mechanism
  governs when a level, a checkpoint and an `asks` meet, and records the spelling policy (keep, generate, report gaps) as provisional
  until increment D's corpus tests it.
- **Found while reading, recorded in the decision:** two of this plan's Scope findings were partly decided already. The two
  settings for `approve-plan` follow decision 5 of `2026-10-26-a-level-for-every-command` (the table wins; the seed still writes
  an empty `checkpoints`); the "level `none` with an `ask` rule" mismatch for `remote-runner submit` and `fetch` and `safe-git remove`
  is the module `asks` of `2026-10-29-workbench-asks-for-remove-submit-and-fetch`, an accepted minimum prompt that the personal
  settings cannot lower. Scope items 2 and 3 are therefore overstated as "drift"; the plan's increments still hold.
- **Open for the owner, in the record:** whether an owner may lower an `asks` with a level (the author recommends not yet), and the
  class of each key.
- **Verification as run:** `wb check` and `wb run code-work check`, both without problems. No code changed.
- **Review:** the `reviewer` agent, one exchange: seven findings, one blocking. Applied all seven after checking each against the
  files: the record no longer promises to map the remote commands to their checkpoints (`checkpoint_of` applies only to an owner-run
  argument that offers `levels`, and the mapping would move a default); the three agent-safe keys that act outward or delete are in
  the third class and `reset` and `prune` moved there; the exceptions of the clarification note are named; the `checkpoints` wording
  is true for a version 2 file; the spec's rule on `asks` is cited; the spelling claim is marked provisional; the follow-on plan's
  additions are stated. The corrected text was not reviewed again.
- **Not done:** acceptance, which is the owner's checkpoint (`accept-decision` is at `ask`); the digest the preview printed is
  `55a716cf8a797b8f8ca0d790dbfd96b9`.
