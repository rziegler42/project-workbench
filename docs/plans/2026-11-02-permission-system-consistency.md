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
- **Accepted** by the owner on 2026-11-02 through `groundwork accept` at `ask` (digest `55a716cf8a797b8f8ca0d790dbfd96b9`), and the
  status line committed.

### Increment B — Decision: the command gate reads where a launcher is, not the letters of a word

- **Done:** `docs/decisions/2026-11-02-command-gate-reads-gaps-and-data-positions.md`, `Proposed`. It does not adopt the plan's
  step 3 as worded ("the in-order test applies only to a command that holds a launcher"): a probe showed that rule would stop
  catching `W=w; Z=b; X=ove; $W$Z appr${X}-plan x`, which the gate refuses today. It proposes instead (1) a gap rule for the
  in-order test (a key's letters match only with wildcards between them: expansions, bare parameters, globs, brace groups and
  escapes); (2) a data position that frees a plain read by `cat`, `head`, `tail`, `grep`, `ls`, `wc` or `diff` that names a word;
  (3) a literal `wb run` call freed for `approve-plan` only; (4) a named rule on every refusal and a capped refusal log with a rule
  and a hash and no text; and answers the plan's question: the owner-run commands cannot tell whether the harness showed the
  prompt, so the text gate stays.
- **Verification as run:** `wb check` without problems. The real gate (`wb gate-command claude`) was run on 42 sanitised commands
  and a throwaway prototype of the gap rule on about 30; nothing was kept and no code changed. The in-order false positives
  reproduced from the full text of commands refused earlier the same day; shortened copies did not.
- **Review:** the `reviewer` agent, one exchange: ten findings, three blocking. Applied after checking each against the code:
  (1) the first draft of the gap rule left out bare `$1`, `$name` and special parameters, so it stopped catching
  `wb appr$1ove-plan` and the pinned `wb approve-$1plan p` (reproduced with the prototype, fixed by counting them as
  wildcards); (2) decision 4 now frees `approve-plan` only and leaves the review engine's five keys on their narrower rule;
  (4) `git` is removed from the data-position list because its options can run a program, and the rest of the list is
  `cat`, `head`, `tail`, `grep`, `ls`, `wc`, `diff`. Also applied: the earlier record's reason for `approve-plan` is cited and
  argued (3), the data position's interaction with the gap rule and the log's format, cap, write scope and hash are stated (5, 6),
  expected results and the per-level effect are stated (7), and the spec text that changes is named (10). The corrected text was
  then reviewed by the project's review bridge (`ask-codex`, model `gpt-5.6-terra`, through the review engine, `review-adr`):
  round 1 of a bound of 3 returned no findings and `no_meaningful_changes`. That is not proof of soundness: the same reviewer
  found nothing wrong with nothing that was run, and the record's own limits (a prototype on about 30 commands, no hostile
  option run on the seven listed programs, no security review) still stand.
- **Owner's choice, in the record:** a literal `wb run` call may be freed for `approve-plan` (the owner said yes on 2026-11-02, while
  the record was `Proposed`; it is accepted or rejected with the record).
- **Not done:** acceptance, the owner's checkpoint (the digest changes with every edit of the record, so it is taken from a fresh
  `wb run groundwork preview` at the time). No security review was run; the plan offers one at increment I.
- **Accepted** by the owner on 2026-11-02 through `groundwork accept` at `ask` (digest `b8a55261affa7cc1c11347259e23fc05`) after
  one Codex round with no findings, and the status line committed.

### Increment C — Decision: what the gates do while a package tree differs from its release

- **Done:** `docs/decisions/2026-11-02-gates-while-a-package-tree-differs-from-its-release.md`, `Proposed`. It decides that the
  gates stay closed while the harness cannot be shown to match its release, and that the refusal names the cause and the first path
  that differs and the command that clears it (built by increment J). It does **not** decide narrowing the lock to the harness
  module; that is described as an option, with what it needs and the tamper path it opens, and left for a later record. The
  author recommends waiting.
- **Found while reading, corrected in the record, and affecting this plan's text:** (1) the lock refuses only the hooked tools
  (`Edit`, `MultiEdit`, `NotebookEdit`, `Write`, `Bash`), not "every tool call" as Scope item 6 says; `Read`, `Grep`, `Glob`, the
  agent tool and the owner's terminal are unaffected. (2) The lock does not guard a running command: `wb run` is governed by the
  installed copy's manifest hash and the pin, not by the shipped records (`firstparty` is not imported by `commands.py` or
  `launch.py`), so a package edit reaches a command only at the owner-run `wb upgrade`. (3) The tree hash covers every regular
  file of the whole package, so an edit to any of 13 modules, a stray cache file, or a link anywhere closes the gates for the
  harness; reproduced on a copy. (4) `verify_package` and `load_package` fail the whole package on one problem in any module, so
  trusting the harness module alone needs new loading code. The plan's approved text is not edited; its increment J still fits
  (the message and the first differing path), and increment J does not build narrowing.
- **Verification as run:** `wb check` without problems. Two throwaway scripts on a copy of the distribution in a scratch directory
  (the first reproduced the table of causes; the second showed the `claude` module's own record still matches when another module
  changes); nothing was kept and this tree was not changed.
- **Review:** the `reviewer` agent, one exchange: eleven findings, four blocking. Applied after checking the central one against the
  code: the first draft's decision 4 (a changed module's commands refuse) was false, since `wb run` does not consult the shipped
  records, and its decision 3 (narrowing) could not be built with the existing loaders and opened an unanalysed path in which an
  agent releases its own edit through the `ask` prompt and can restore an older released `claude` module. The record was
  rewritten: narrowing is an option left open with its needs and a per-option table of what an attacker who can edit a package gains
  (the plan's step 3 asked for it), the false decision is replaced by a statement of what protects a running command, the
  contradiction between narrowing and the stray-file decision is gone, and the lock is no longer presented as covering the gate
  code or the shipped records. The rewritten text was then reviewed by the project's review bridge (`ask-codex`, model
  `gpt-5.6-terra`, `review-adr`): round 1 of a bound of 3 returned two major findings, both applied. One said the record presented
  the owner's conversational choice to wait as settled while it was `Proposed` (reworded: it becomes part of the decision on
  acceptance). The other said the claim that Python loads a cache file found beside imported code was unsupported (removed; the
  rationale is that the tree hash must cover everything below the package, and loadability was not checked). The two edits were
  not reviewed again.
- **Owner's choice, noted in the record:** wait on the narrowing (the owner said so on 2026-11-02, while the record was `Proposed`;
  it becomes part of the decision when the record is accepted).
- **Accepted** by the owner on 2026-11-02 through `groundwork accept` at `ask` (digest `4b43c679b67a5b478c9f0c3c6583e0ea`); the
  status line is committed separately. No security review.

### Increment D — Characterize today: the corpus and the drift test

- **Done:** three new files and no production change: `tests/fixtures/gate_corpus.json` (79 cases), `tests/test_gate_corpus.py` and
  `tests/test_permissions_drift.py`. The corpus records, for each command, the level it runs under (`ask`, `none` or `block`),
  what the gate does today and the rule that fired, and the result the accepted gate decision wants; 9 cases differ (the false
  positives of the decision, 7 at `ask` and 2 at `none`), each naming increment I as the one that ends the difference. The other
  70 are 10 ordinary commands that pass, 9 exact forms the ask rule matches, 30 attempts that must stay refused (including the
  forms found while testing the gap rule: brace groups, bare parameters, a built launcher), the 3 block and 5 none cases that do not
  differ, and 13 boundary cases that keep the data position and the freed `wb run` form from widening. The drift test reads the registry built from
  the shipped declarations, the spec's bullet of offered levels, the owner-run rows of the development table, the settings seed
  and every shipped skill and agent, and lists 13 disagreements, each with the increment that ends it (E, G, K or M).
- **Findings recorded in the tests, not fixed here:** the `remote-runner` `submit` and `fetch` and `safe-git remove` keys default to
  `none` while their module renders an ask (E); a checkpoint and its command carry different defaults (G); the settings seed
  still writes the version 1 `checkpoints` object (G); the `peer-review` skill says never run five review-engine arguments and the
  `delegate-approval` skill says never run `approve-plan`, though all are at `ask` (K); the development table does not show
  `release-approvals` as an owner-run row (M). The spec's offered-levels bullet agrees with the registry.
- **Verification as run:** `python3 -B -W error -m unittest tests.test_permissions_drift tests.test_gate_corpus tests.test_levels
  tests.test_command_gate`: 156 tests, OK (28 new; the two neighbours unchanged). `tests.test_approve_levels` (cited by the
  corpus for the block side): 54 tests with the corpus, OK. With an empty known list the drift test failed and listed the
  disagreements. Nothing wider was run: no production code changed.
- **Not covered, stated in the test's docstring:** the rendering plan and the `wb settings` lines (increment F), the launcher spellings
  against any text, the checkpoints that no command runs against the skill that states them (G with K), a level the owner's own
  file sets that the key does not offer (`wb doctor`, increment L), the skills' omission of the `ask` flow, and the `git push` ask
  rule against `push-shared-branch`. The size and NUL checks of `command_gate.run` sit outside `judge` and stay in
  `tests/test_command_gate.py`.
- **Review:** the `reviewer` agent, one exchange: eight findings, one blocking. Applied after checking each: the corpus had no
  `block` and `none` side (it now carries a level on every case, with block cases that show the gate is not engaged and a test that
  the launcher spelling is read only by the gate and the rules, so the command's own terminal test, tested in
  `tests/test_approve_levels.py`, is spelling-independent); boundary attempts for the data position and the freed run form were
  added; the mislabelled development-table disagreement was reworded; the spec reader no longer drops a name the registry lacks;
  every reader has a negative test (one caught a mistake in my own test input); the test that edited the known list was replaced by a
  pure comparison; an unused name was removed. Two points were not changed: the `rule` field reads the refusal's prose, and
  increment I replaces that with the structured rule name; facts the drift test does not read are listed above. The fixes were not
  reviewed again.
- **Committed** as `9b947b0286e097a2a602e5d5711c7011e9203576`. A security review was not part of this increment (it changed no
  production code).

### Increment E — The registry

- **Done:** `workbench/levels.py` is now the registry. `INSTALLER_KEYS` is the one table of the installer's own keys (its owner-run
  commands and the checkpoints it names), each with its kind, danger class, offered levels, command word, the command that carries
  it out, preview key and documentation anchor; `OWNER_RUN`, `PREVIEW_ACTIONS`, `CHECKPOINTED_COMMANDS`, `COMMAND_OF_CHECKPOINT`
  and `_OFFERS` are derived from it, and the lists of agent-safe words and the spellings are defined there, with `rules.py`
  re-exporting all of them so no call site or test changed. `Key` gained `kind`, `klass`, `carried_by`, `spellings`, `preview`,
  `asks` and `anchor`, all with defaults. `levels.command_entry(command)` builds the seven facts the registry reads from a
  declaration (the `asks` and the preview argument are new); `harnessstage.py`, `rendering.py` and `settingscmd.py` call it
  instead of each building the five-item tuple, and a five-item tuple still works. The drift test's list fell from 13 to 10: a
  module's `asks` is now recorded in the registry as a declared minimum, so it is no longer a disagreement.
- **Beyond the plan's list of affected areas:** the three call sites above (the outcome says the registry's callers read it) and two
  new or changed tests: `tests/test_levels_facts.py` (new, so `tests/test_levels.py` stays unchanged as the proof) and the D tests
  (`test_permissions_drift.py`: the asks entries removed, the anchor reader added; `test_gate_corpus.py`: the file that defines the
  spelling list is now `levels.py`).
- **Verification as run:** 183 tests OK (`test_levels_facts`, `test_levels` unchanged, `test_permissions_drift`,
  `test_gate_corpus`, `test_command_gate`). A broader run of 29 test modules that use the rules, the levels or the rendering: 1004
  tests OK; three modules (`test_settings`, `test_gate`, `test_levellog`) do a bare `import support` and cannot load as
  `tests.test_x`, and pass (135 tests) when loaded as `tests/run_all.py` loads them. The full suite was not run. The output of `wb
  settings` is identical to its output before the change. A comparison of the committed tree (`HEAD`, extracted) with the working
  tree, in separate processes: the seven lists, the derived tables, all 72 keys with their offers, default, agent flag and order,
  the deny patterns of every key, the rendering plan for the default table (300 deny patterns) and its digest are identical.
- **An incident, stated plainly:** renaming a constant in `levels.py` across several edits left the tree unimportable after the
  first one. The two hooks import the workbench code from this working tree, both crashed, and every `Edit`, `Write` and `Bash` call
  was refused until the owner ran a one-line `sed` in a terminal. No gate was worked around. The lesson is in memory: an edit to
  installer code must leave the tree importable at each step. It is also a fact for the record of the lock decision: in this
  self-hosted repository a change to `workbench/` can close the gates as well as a change to `packages/`.
- **Review:** the `reviewer` agent, one exchange: five findings, none blocking. Applied: the module docstring was updated and no
  longer names a module; the test that compared the new code with itself says so and points to the comparison above. Not changed,
  and for the owner:
- **A divergence from an accepted record, and the owner's decision.** Decision 4 of
  `2026-11-02-one-permission-registry-and-key-model` puts the review engine's `extend`, `archive` and `amend` in the class of
  `project`. The installer names no module and a declaration has no class field, so the registry derives a module argument's
  class (owner-run or asks-bearing: `governs`; other: `reads`) and those three read as `governs`. The class changes no default
  and no offered level, so nothing behaves differently. The owner chose, on 2026-11-02, to add a class a module can declare to
  the module contract (option b). It lands in the follow-on plan `2026-11-02-permission-levels-for-every-command`, increment F,
  step 0 (a package edit there). That plan starts after this one completes, so it comes **after** increment L, not before it as
  the author first said. Until then **increment L does not report a risk for a module argument whose class is derived**; it
  reports one for the installer's keys, the checkpoints and an argument that carries an `asks`, and for a module argument only
  once a module declares its class. The divergence is pinned by a test (`tests/test_levels_facts.py`) so it cannot change unseen.
- **Committed** as `c6b18ce02e75315cc7a967a2c1b549a89814dcf5`. Not done: a security review of this increment (the code decides which
  commands get a deny rule and which level a key may be set to, but the comparison above shows both unchanged); `anchor` is
  recorded only for the installer's keys and checkpoints, and a module argument has none because its module documents it.

### Increment F — The readers move onto the registry

- **Done:** one function now reads a key's name as a command. `levels.command_words(key)` returns the words of the command a key
  names (`("approve-plan",)`, `("install",)`, `("preview", "install")`, `("run", "<command>", "<argument>")`, or `()`), and the
  rendering (`key_patterns`) and the command gate (`words`, `_by_launcher`, `reads_argument_as_data`, `forms`, through a
  new `_run_key`) use it instead of each splitting the name themselves. `wb settings` prints a `key <key>: class=<class>
  offers=<levels>` line for each key, after the `level` lines (the plan's step 3). The line kind is documented in the
  `settingscmd.py` docstring, `docs/development.md`, `docs/specs/command-permissions.md` and `docs/specs/installer-interface.md`.
- **Found while reading, a correction to the plan's list:** four of the six readers the plan names have nothing to move.
  `verify.py` and `rerender.py` use no permission fact; `settings.py` already builds its keys from `levels.registry`; `ownerargs.py`
  compares one level constant. The readers that parsed a key's name by hand were `rendering.key_patterns` and `command_gate.words`
  and its three neighbours, which the plan does not list, so they were changed. Step 2: no spelling changed and the rendering
  record's content did not change (its digest is identical), so its format was not bumped and no old format needs reading.
- **Beyond the plan's list of affected areas:** `workbench/levels.py` and `workbench/command_gate.py` (above), the three documents
  that describe the `wb settings` output, and `tests/test_levels_facts.py` (the parser tests) beside `tests/test_settingscmd.py`.
  `tests/test_settingscmd.py`'s expected output gained the `key` lines through its one helper; that is the plan's step 3 and no
  other assertion changed.
- **Verification as run:** 1303 tests OK across 30 modules that use the rendering, the gate, the settings command or the registry
  (including `test_command_gate`, `test_gate_corpus`, `test_permissions_drift`, `test_rendering`, `test_rerender`, `test_attach`,
  `test_owner_argument_levels`, `test_check`, `test_verify`), and 135 more in `test_settings`, `test_gate` and `test_levellog`
  loaded the way `tests/run_all.py` loads them. `tests/test_levels_facts.py` freezes the old parsers (`words`, `key_patterns`,
  `_by_launcher`, `forms`, `reads_argument_as_data`) and shows the new code gives the same answers for all 72 real keys and 28
  odd strings. A dump of the compiled lists, all keys with their offers, defaults and order, the deny patterns of every key, the
  rendering plan (300 deny patterns) and its digest, taken from the committed tree and the working tree in separate processes, is
  identical; the 88 existing lines of `wb settings` are identical and 72 `key` lines are added. The full suite was not run.
- **A second incident, stated plainly:** to compare outputs I ran the command line of an extracted copy of `HEAD`. A command
  initializes the guarded store and rewrites its launcher (`~/.config/project-workbench/bin/wb`) to the copy's tree, which has no
  `packages/`; the hooks then found no known harness and refused every `Edit`, `Write` and `Bash` call, and rewrote the launcher to
  the same path each time. A search for stray files in `packages/` found nothing and was a dead end; reading the launcher showed
  the cause. The owner repaired it with `python3 -B -m workbench settings` from the repository root in a terminal. No gate was worked
  around. The lesson is in memory (compare by importing a copy and dumping data, never by running its command line). It is also a fact
  for the lock record: the launcher is a shared piece of state that any workbench command can repoint.
- **Review:** the `reviewer` agent, one exchange: four findings, none blocking. Applied: the `key` lines are documented, and the
  differential test covers the other gate readers too. Not changed: the guard test that the two readers no longer split a key is a text
  search (brittle, harmless), and the `key` loop skips a name the registry lacks (it cannot happen today). No security review was
  run: the gate's answers are proved unchanged by the differential tests, and the plan offers one at increment I.
- **Committed** as `f09c62dd890e8f0470bb58f03b396db96295db4e`.

### Increment G — Checkpoints as keys, one setting each

- **Done:** (1) A new settings file is seeded as `{"floor": [...], "levels": {}, "version": 2}`: the table, with no `checkpoints`
  object (`settings.VERSION` is 2, `_seed_document`). A version 1 file is still read, its words read as levels for a key the table
  does not name, and `wb settings` prints each reading; nothing writes the old object. Migrating an existing file is the owner's edit.
  (2) The registry's `Key` gained `paired_with` and `stated_by`. `levels.PAIRED_ACTS` records `submit-remote-job` with `wb run
  remote-runner submit` and `fetch-remote-output` with `wb run remote-runner fetch` on both keys, and `levels.STATED_BY` records the
  skill that states each checkpoint the agent follows: `push-shared-branch` in `push-changes`, the two remote checkpoints in
  `run-remote-job`, `change-direction` in `draft-roadmap` and `draft-spec`. (3) The drift test no longer lists the two pairs or the
  seed; `KNOWN` is down from 10 entries to 7 (1 for M, 6 for K). The spec, `trust-and-approval.md` and `development.md` describe the seed.
- **What "resolved" means for the pairs: recorded, not merged.** Decision 5 of `2026-11-02-one-permission-registry-and-key-model`
  does not map the remote commands to the checkpoints (the contract's `checkpoint_of` does not apply to them, and mapping them would
  move their default from `none` to `block`) and leaves the question to the follow-on plan. So each pair still has two levels
  (`block` for the checkpoint, `none` for the command, with the module's `asks` rendering a prompt either way). G makes the choice
  visible: the drift reader reports a pair only when the registry does not record it. The reader cannot fire on the real registry by
  design; its negative test feeds it an unrecorded pair. `wb doctor` (L) is to list the recorded pairs.
- **A departure from step 3, for the owner:** the plan lists "the acknowledge wording" among the skill-stated rules. No shipped skill
  states the acknowledge checkpoints; `wb acknowledge` carries them and their wording is the policy block of `AGENTS.md`. The registry
  records no `stated_by` for them, and the spec says why. Increment K may find other skills that state `change-direction`.
- **Step 1, as built:** the existing tests already covered "a key in both takes the table entry"; G added one that the word beside
  an entry is not also translated, and the seed tests. A command that implements a checkpoint reading the checkpoint's key
  (`accept-decision`) was already tested and is unchanged.
- **Verification as run:** `test_levels_facts` 37, `test_levels` 35, `test_settings` 84, `test_settingscmd` 33,
  `test_permissions_drift` 14, `test_checkpoint_command` 51, `test_checkpoint_command_run` 36, `test_rendering` 84 and
  `test_gate_corpus` 15, all OK (`-W error`). The tests were written before the code, but I did not run them against the old code to
  see them fail; they name attributes and a seed shape that did not exist. The full suite was not run.
- **Review:** the `reviewer` agent, one exchange: five findings, none blocking. All were checks or notes: the pair is recorded and not
  merged (above), no reader of the seed assumes version 1, `stated_by` matches the skills with the acknowledge omission (above), the
  tests are sound. Nothing was changed after the review. No security review: nothing here widens a level, and the seed carries
  the same values.
- **Committed** as `78fcd4c2e623d884c54d78d9056666d50a335114`.

### Increment H — The kit: preview digest and the `ask` flow, once

- **Step 1, what was duplicated:** `groundwork` and `review-engine` each carried the same four things: the digest (the first 32
  characters of the SHA-256 of the preview lines joined by a newline), the 32-lowercase-hex shape check, the usage line for a
  malformed digest, and the refusal line for a digest that is not the preview's now. Only those moved. Not moved, on purpose:
  the installer's own digests (`planapprovals.digest_of`, `firstparty.digest_of`, `installplan.digest_of`) hash other inputs than
  preview lines and are not helpers; `safe-git` and `remote-runner` check no digest (they use `--confirm`); `refcheck`,
  `code-work` and `action-review` hash content but have no preview digest. The line `digest: <digest>` that ends a preview is still
  written in each of the two helpers (one expression); I left it because a kit function for one line would also have to own the
  preview's other lines, which are each helper's.
- **Done:** a new kit module `workbench/wbkit/digest.py` (`of`, `well_formed`, `mismatch`, and the two standard lines `MISMATCH`
  and `SHAPE`); it reads nothing and imports only the standard library, so the kit API stays 1. Both helpers use it and drop their
  copies. `review-engine` keeps "; nothing was changed" after the standard line. `tests/support_helpers.py` loads the module;
  `docs/specs/module-boundary.md` lists it.
- **Behaviour:** the digest value, the shape rule and both refusal texts are the same as before (pinned by a test against the old
  formula). One difference, unreachable by a user because the shape check comes first: a non-ASCII or non-text value now yields the
  refusal and never raises.
- **Where the check happens:** `review-engine` compares inside its lock (both call sites, `mutate` and the prune path). `groundwork`
  has no lock; its protection is the held root and the sha-checked replace, which binds the sha the digest binds. That is unchanged,
  and the kit docstring and the spec say it so (the first draft said "inside the caller's lock" for both; the reviewer caught it).
- **Beyond the plan:** a package edit changes the package tree, so the gates were closed until the owner released the approvals.
  Step 4 says the package edits are one scripted pass that the owner starts; I edited the two helpers directly instead, which
  closed every hooked call until the owner ran `wb release-approvals`. No gate was worked around. Three new directories under
  `workbench/shipped_approvals/packages/` are that release and are part of the commit. The five `review-engine` tests that patch
  `hmac.compare_digest` first failed because the kit passed bytes; the kit now compares text, and no package test was edited.
- **Verification as run:** `tests/test_wbkit_digest.py` 18, the `review-engine` package tests 409, the `groundwork` package tests
  251, `test_wbkit_levels` 22, `test_owner_argument_levels` 29, `test_kit_readers` 26, `test_runner` 37, all OK (`-W error`). The
  full suite was not run.
- **Review:** the `reviewer` agent, one exchange: four findings, none blocking. Applied: the lock claim in the kit docstring and the
  spec; two kit tests were renamed because their names overclaimed, and a duplicate case was removed. Recorded above: the
  `digest:` line left in each helper. No security review was run; the plan has the author ask the owner once.
- **Committed** as `5979b5f6cd900ce05d2ee3f089f100020bb36bb4`.

### Increment I — The gate stops refusing by letters; refusals are named and logged

- **Step 1 (tests first):** the nine corpus cases that differed from their intent were set to their intended result and failed
  against the old gate; new cases were added (the data position for each listed program, a literal call that names the word, the
  edges that stay refused, three padded-letter attempts, a preview with an expansion). The corpus is now 102 cases and no case
  differs from its intent. `classify`, which read the prose of a refusal, is gone: the test reads the rule from the gate.
- **Done, as decision B says:** (a) the in-order rule is replaced by the gap rule (`_spelled`, `_gap_match`): the letters of a key
  match only where nothing but wildcards separates them, at least a third written out; an expansion, a brace group and a bare
  parameter count as eight wildcard characters, a `*` as three, a `?`, a bracket class and an escape as one, and each wildcard
  stands for one letter or none. (b) The data position (`reads_as_data`, `DATA_PROGRAMS`): one command or a pipeline of
  `cat`, `diff`, `grep`, `head`, `ls`, `tail`, `wc`, every argument a plain token or a single-quoted string, only `2>/dev/null` and
  `2>&1` as redirections, matched in full on the raw text; a test per program and a test of each way out of it. (c) A literal
  `wb run <name> ...` call frees `approve-plan` (`literal and key == "approve-plan"`), and no other `wb run <command> <argument>` key.
  (d) Every refusal names its rule and ends `(rule: names|gap|dollar-quote-limit|size-limit)`: `verdict()` returns the rule and
  the reason, `judge()` the reason. (e) The refusal log (`workbench/gatelog.py`, `gate-log` in the guarded store): time, rule and
  the first 12 hex characters of the SHA-256 of the command, never its text; appended through `safefs.append_line` (no-follow, one
  link), capped at 1 MiB, written after the verdict is fixed, and every failure of it is swallowed. `prepare` may return the writer
  as a fifth item (`cli._gate_command` does); a four-item `prepare` still works.
- **Two additions the decision does not make, for the owner to accept or reject:**
  1. `substituted()`: a simple assignment in the same command text (`a=approve b=plan; wb $a-$b x`) has its uses put in before the
     name tests run; `${A//x/}` and the like put the value in as the content of an expansion. Two existing tests pin the refusal of
     `a=approve b=plan; wb $a-$b x` and `a=appr b=oveplan; wb ${a}${b} x`, which the gap rule alone does not give (the assignment's
     own letters are written between the word's letters). It only adds views to read, so it cannot turn a refusal into a pass.
  2. `_free_match`: inside an expansion (`$(...)`, `${...}`, a backtick pair), other characters may sit between two letters of the
     word, within a span of three times the word's length. The reviewer's blocking finding: `wb $(printf 'inst%s' all) x`,
     `A=xaxp...; wb ${A//x/}` and `wb $(tr -d x <<< xaxp...)` pass the gap rule and were refused by the old gate (checked by running
     both). Decision B says "the padding that can be run lives inside an expansion, and an expansion is already a wildcard"; that is
     not so when the letters are written inside it. A literal letter written outside an expansion still breaks the match.
- **Changes in results beyond the decision's five rows**, all found by a run of the old gate (extracted from `HEAD`) and this gate over
  the 102 cases: passes now that the old gate refused: the nine named, the data-position and literal-call cases added, an
  unrelated pair of globs, and `wb preview release-approvals --dir $PWD` (a literal `preview` sits between the letters; the
  expansion stands for no letter of the word). Refused now that the old gate passed: `wb $A-plan x` (an expansion beside `-plan`
  stands for `approve`; also `A=approve; : xxxxxxxx...; wb $A-plan x`, which the old test recorded as a known limit). No attempt of
  the corpus passes that the old gate refused. Existing tests whose expectation changed, each because the decision frees it:
  `grep approve-plan docs` and `grep -r approve-plan docs` (data position), `wb run x 'approve-plan'` and `wb run vault preview
  'approve-plan'` (decision 4), `wb preview install --dir $PWD`, and the far-variable test (now refused).
- **Not changed, as accepted limits:** a script file, a function or alias, a word built by a transformation whose input does not
  hold the letters in order (`rev`, base64), a variable set by `read` or an expansion rather than a simple assignment, and an
  all-wildcard spelling with fewer than a third of the letters written out (`wb $a$b` with `a` and `b` set elsewhere). The match is
  not anchored to a word: the skeleton drops spaces, so `echo approve $(true) the plan` is refused as the old gate refused it.
- **Verification as run:** `test_command_gate` 127, `test_gate_hook` 72, `test_gate_corpus` 15, `test_levelrun` 22,
  `test_agent_gate` 58, `test_gatelog` 14, `test_gate` 27, `test_rendering` 84, `test_permissions_drift` 14, `test_levels_facts` 37 and
  `test_settingscmd` 33, all OK (`-W error`); a probe of 40 attempts and ordinary commands against the live gate; the new gate was built
  and tested in a scratch copy and swapped in. The full suite was not run. The refusal log was seen to be created in the store by the
  first refusal after the swap (its size, not its content, was read).
- **Review:** the `reviewer` agent, one exchange: seven findings, one blocking (above, fixed and rechecked by running the three
  forms, not reviewed again). Not blocking and applied: the `gatelog` docstring said `wb doctor` reports the log, which increment L
  builds; the gate's docstring said an expansion had to supply the rest. Not changed: the reviewer's note that GNU `diff -l` and
  `--paginate` run `pr` from `PATH` (it cannot run an owner-run verb); the decision's own text that still reads "Proposed; the owner
  decides" under an `Accepted` status line. The reviewer could not run anything, so its claims about the old gate were checked by
  running the gate extracted from `HEAD`.
- **The owner accepted both additions** (`substituted` and `_free_match`) in conversation on 2026-11-02. The security review followed (below). The spec text for the gate ("The command gate", "Limits") is updated in
  increment M, as the plan says, and is to record both additions.
- **Security review (the owner asked for it):** the `security-reviewer` agent, no Critical or High finding. Found sound and tested: the
  data position (about 280 option forms of its seven programs launched nothing in a run with a fake `PATH`; the regexes are
  linear), the refusal log (links, FIFOs, a directory in its place, the cap, eight concurrent writers, hostile text), the gap
  and free-match dynamic programs (6,000 random cases each against brute force), and that no malformed `prepare` return leads
  to an allow. Findings, and what was done (the owner said "fix 1 and 2"):
  1. **Medium, fixed.** A value the text sets in a way the tracker does not follow (`eval 'x=…; wb ${x/Q/}'`, `for`, `+=`,
     `printf -v`, `set --`, an array) and then pads, with the padding removed by a parameter operator, was refused by the old gate
     and passed this one. The statement above that "padding lives inside an expansion" was wrong for assigned values. Fix: a
     command that holds a parameter operator (`${name<operator>…}`) is also read by the old in-order rule (`_subsequence`, three
     times the word's length, a third written out). Ordinary commands (`${HOME#/}`, `${DIR:-.}`) are not refused. Four corpus
     cases and two tests added; the four forms passed before the fix and are refused after it (run on both trees).
  2. **Low, fixed.** `substituted()` could build hundreds of megabytes from a 64 KiB command (a long value used thousands of
     times; 24 MB for a 60 KB probe, more for worse). It now returns the text unchanged when the result would pass four times
     `MAX_COMMAND`; the same probe gives 52 KB. A test added.
  3. **Low, not changed, not a regression.** `wb approve-*`, `wb appro*` and, in bash with `extglob` or in zsh, `wb appr(ov|zz)e-plan`
     run the command when a file of that name sits in the working directory; both gates allow them (a `*` counts as three
     letters; the alternation forms hold no pattern character). Adding `(`, `|`, `@(`, `+(`, `!(` to `_PATTERN_CHARS` is the
     option. It widens the gate and is left to the owner as its own item.
  4. **Info, fixed.** The "no expansion form tested makes bash join them" text and the docstring are reworded as above.
  Second look: the reviewer's fuzz (`probe3`, 30,000 generated spellings run in bash against the new gate with the old gate for
  comparison) was run again on the fix: no spelling executes that the old gate refused; the brute-force comparisons of the
  gap and free-match programs still agree (6,000 cases each). Reran after the fix: `test_command_gate` 130, `test_gate_corpus` 15,
  `test_gatelog` 14, `test_gate_hook` 72, `test_levelrun` 22, `test_agent_gate` 58, all OK. An independent second look at the
  fix by an agent has not been run.
- **Committed as** `f9a71d6924978caa1113ef558a8f085fc5886501`. Not pushed.

### Increment J — A changed package tree is explained

- **Done:** a gate that cannot find its harness now says why. `harnesses.refusal_text(harness, distribution, needs)` returns the line
  and never raises; `cli._gate`, `cli._gate_command` and `agent_gate.known` print it instead of "is not a known harness whose layout
  ...". While a package tree differs from its release it reads, for example: `claude is not available: the package tree differs from
  its release: first at 'packages/workbench/ask-ollama'; the owner clears it in a terminal with `wb preview release-approvals` and
  then `wb release-approvals --digest <digest>`, with the digest the preview prints`. When the harness is known, or no package
  differs, the old plain line is printed (the tests that look for "not a known harness" still hold).
  Causes named, each as a path and never a value: a package directory that is a link; a link, a special file or a refused name inside a
  package (full path); a file no module accounts for (full path, found through `verify_package`); no release approval at all; a
  module whose files differ from its release (the module directory); a change outside every module (the first file there, else
  `package.json`). A cause the release itself refuses (the link, special-file, name and unaccounted-file causes, a module the
  verifier refuses) adds "remove or restore it first". Paths are shown quoted and in ASCII, so a file name cannot read as part of the
  sentence.
- **Deviation from the decision's wording, for the owner to know:** decision 2 says "the first path that differs". The shipped
  records hold only a hash for the package and one per module, so a deliberate edit to a file can be located to its module directory
  and not to the file; a deleted file is the same. A stray file is named by its full path. Locating the file would need a
  per-file manifest in the release records, which is not in this plan. `cli.py` was changed although the plan's affected areas do not
  list it, because the two messages are raised there; `gate.py`, `gate_hook.py`, `command_gate.py` and `firstparty.py` were not
  changed (the last is read, through its private `_package_hashes`).
- **Tests first:** `tests/test_harness_lock.py` (20 tests), written before the code and seen to fail on the missing function: separate
  cases for a deliberate edit (a module file, `module.json`, `package.json`) and for a stray untracked file (in a module, a cache file,
  beside the modules), a link, a link as the package directory, a missing approval, a file value never printed, a hostile name (an
  escape character; printable text that reads like advice, shown quoted), never raises, one bounded line, the tree not changed,
  a stray file beside the packages not taken for a package. One CLI-level test each for the command gate (`test_rendering`), the edit
  gate (`test_gate_hook`) and the agent gate (`test_agent_gate`).
- **Verification as run** (`-W error`): `test_harness_lock` 20, `test_harnesses` 28, `test_gate` 27, `test_gate_hook` 73,
  `test_agent_gate` 59, `test_command_gate` 130, `test_rendering` 85, `test_firstparty` 57, `test_check` 45, all OK. On a copy of the
  real `packages/` and shipped records (a scratch directory): a released copy gives the plain line; a stray cache file and a comment
  added to a helper give the lines above, each in about 0.1 s (the gate deadline is 10 s). The full suite was not run. No package
  file was changed by this increment.
- **Review:** the `reviewer` agent, one exchange, no blocking finding, six findings. Applied: printable text in a file name could read
  as advice (paths are now quoted); the clearing commands were advised for causes the release refuses (now "remove or restore it
  first" for those); the docstring claimed a pure sorted order (reworded to the walk's order); a stray file beside the packages
  (`.DS_Store`) was taken for a package (skipped). Accepted as stated: the module-directory deviation (above). Not changed: the
  cause names the first package that differs, not the one holding the harness (every package of this distribution is first-party by
  design); a cache file is named as "no module accounts for it" only where the verifier says so. The reviewer could not run anything.
- **Security review (the owner asked for it):** the `security-reviewer` agent, on copies; no Critical, High or Medium finding. Found
  sound and tested: a quoted ASCII `repr` of every path (an advice-like name, quotes, backslashes, newline, ESC, a U+202E override,
  a 250-character name stayed inside the quotes; no forged `refused:` line); a FIFO, a link loop, a mode-0 directory, a package that
  is a link and a 20 MB file all returned in under 0.25 s without a blocking open; `refusal_text` returned a string for odd
  arguments and every caller raises a refusal regardless, so no path turns a refusal into an allow; no file content, environment
  value or path outside the distribution is printed. Findings, all Low, and what was done (the owner said "fix 1 to 4"):
  1. **Fixed.** A non-directory entry in `packages/` (`.DS_Store`) with a stray file in the package: the line gave no "remove it
     first" advice although the release refuses that tree. Now any such entry makes the cause fix-first and the line says
     "packages/ also holds an entry that is not a package".
  2. **Fixed.** The gate cuts the line at 600 characters; a 64-character harness name and a backslash-heavy path cut off the
     clearing command (`repr` doubles backslashes). A quoted path is now capped at 120 characters; the same case gives a line under
     600 with the command intact (a test).
  3. **Fixed.** A file named `evil is not module.json tail` was shown as `evil`. The path is now cut only when the message ends with
     the verifier's own fixed tail, and shown whole otherwise.
  4. **Fixed.** Time: the extra `known` call is gone (the callers pass whether the harness was found, `declared`), `_first_trouble`
     uses a deque and stops after 20,000 entries (it was quadratic in the number of directories), and the search for the cause stops
     after 3 seconds with "the cause was not searched, because the tree is large" and the clearing commands. 30,000 small files in a
     module now give that line in 3.3 s (the reviewer measured 7.7 s for the search alone before).
  5. **Wording only.** A file over the 16 MB limit was reported as "cannot be read as a package (package.json)"; the line now adds
     "or a file over the size limit". Not changed: with `packages/` itself a link the line shows a name from outside the
     distribution (the old code read through the same link and printed nothing; the agent can list those names); the cause names the
     first package that differs, not the one that holds the harness.
  Reran after the fixes (`-W error`): `test_harness_lock` 26, `test_harnesses` 28, `test_gate` 27, `test_gate_hook` 73,
  `test_agent_gate` 59, `test_command_gate` 130, `test_rendering` 85, `test_firstparty` 57, `test_check` 45, all OK. The six new
  tests were run against the module before the fixes in a copy, and all of that file's tests errored there (the new `declared`
  parameter), which shows they did not pass by accident but not that each fails for its own reason.
- **Second look at the fixes (the owner asked for it):** the `reviewer` agent, one exchange, no blocking finding; it read and ran
  nothing. Sound by its reading: the deque keeps the walk's order; the entry cap is safe because the hash raises for every kind the
  walk finds (a link, a special file, a refused name, an unreadable entry); `declared=bool(facts)` is exactly "the harness is
  known". Applied: a cut path is closed with the quote it opened with (it ended in `'` after a `"`); the rule name in the line is
  cut at 24 characters and the "not searched" text shortened, so that the worst case of about 590 characters has room under the
  gate's 600; tests added for the walk's order, a link past the entry cap (the hash finds it and the line says to fix it first),
  the quote, an unaccounted-file message that is not the verifier's own, and the budget case saying nothing of removal; the
  length test is now under 600. Not changed: when the time budget stops the search (or no release approval exists) the line
  omits "remove it first" even if the release would refuse the tree; it says the cause was not searched and still gives the
  commands, which is less advice and not a false one. After these edits: `test_harness_lock` 30, and the others as above, all OK.
- **Committed as** `cad9f18683fa516b64e81beb3a43ca9459a3152a`. Not pushed. Not done: narrowing the lock, which the decision leaves
  open; `wb doctor`'s report of the same cause (increment L); the spec text (increment M).

### Increment K — Skills and agents agree with the registry

- **Step 1, the list.** Every shipped skill and agent was read (the FreeCAD and Verilog skills name no key). What depends on a level
  or a checkpoint, and what it said:
  - `delegate-approval`: "never run" `approve-plan`, which the registry offers at `ask` and `none`; a closed list without
    `wb settings` was not the fault (it had it), but step 1 read the legacy `checkpoint approve-plan: delegate` line and not
    `level approve-plan:`, which is what the delegate command honours (reviewer's reading of `settings.effective` and
    `planapprovals.delegating`: the two lines agree today, the level is the authoritative one).
  - `peer-review`: "never run" `extend`, `reset`, `archive`, `prune` and `amend`, the five that offer `ask` and `none`; no ask flow;
    a closed list without `wb settings`.
  - `draft-plan`: "only the owner makes" the approval record with the command, and a closed list of one command; no level read.
  - The `code-work` policy block (rendered into `AGENTS.md`): the approval line and "Each checkpoint stops for the owner" gave no
    level and no ask flow (the `groundwork` block and `draft-decision` already did, for `accept-decision`).
  - Sound as they are: `draft-decision` (the model the plan names), `push-changes`, `run-remote-job`, `draft-roadmap`, `draft-spec`
    (each states the rule of its `block`-only checkpoint, as `STATED_BY` says), `recall-memory` ("never" for `init` and `mine`,
    which offer `block` only), `commit-changes`, `request-review`, `evaluate-findings`, `run-increment` (it names no key; one
    sentence about who approves now points at `draft-plan`), `security-review`, `brainstorm`, the `reviewer` agent.
- **Test first.** `tests/test_permissions_drift.py` gains three readers on the model of the existing "never run" reader:
  `skills_state_their_checkpoints` (the skill the registry names for an agent-followed checkpoint exists and says its rule,
  `STATED_RULES`), `ask_flow` (a skill, agent or policy block of the governing modules that names a key the owner may set to `ask`
  must hold `wb settings`, `--digest` and the key's preview) and `closed_lists` (a closed command list in a text that names a relaxed
  key holds `wb settings`); reading a level (`level approve-plan: delegated`) does not count as naming a key to use it. The six K
  entries are removed from `KNOWN`, which now holds only the development-table entry of M. Each reader has negative tests. Run on
  the unchanged text it fails and lists 17 disagreements besides the known one (the ask flow missing in `delegate-approval`,
  `draft-plan`, the policy block and `peer-review`; three closed lists; the six "never run" lines).
- **The text pass.** One script that rewrites five files atomically, each old text required to occur exactly once: the three
  skills above and `run-increment` (one sentence), and `code-work/files/blocks/policy.md`. It writes the rule on the model of
  `draft-decision`: at `block`, and at any other reading, the owner; at `ask` the preview, shown in full, then the command with
  `--digest <digest>`, which the owner confirms; at `none` the agent runs it; `delegated` reads `block` except for `approve-plan`
  (`delegate-approval`). `draft-plan` step 8 carries the approval flow and runs only once the owner has said to approve; its
  closed list now holds `wb settings`, `wb plan-status`, `wb approve-plan` and the `delegated` commands. "Never" stays for the status
  line and for `init` and `mine`. The pass was run on a copy of the repository: there the drift test (22), `test_verify` (69) and
  `test_skill_names` (8) pass, and the drift list is the one development-table entry. The owner starts the pass on this tree.
- **Review:** the `reviewer` agent, one exchange, no blocking finding; the flows were checked against the spec and the registry
  and the readers against the shipped text. Applied: the policy block says the `ask` and `none` routes begin once the owner has said
  to approve, and that `delegated` has its own skill; the `draft-plan` closed list adds the `delegated` commands; `peer-review`
  keeps "show the preview when the owner asks" at every level; `delegate-approval` says `delegated`; a leftover fragment in the
  test's comment is removed. Not changed: `code-work/files/docs/plans/README.md` (a seeded document, not read by the test) still
  says the owner makes the approval with the command; it does not contradict a level, since the same file says a level can lower
  the stop; the readers match a key named in the form the existing reader reads (a backticked argument or whole name), so a text
  that names only the long form would not be read. The `security-reviewer` agent's pinned list (`python3 -I -B` on four probe
  scripts in its scratch directory) fits the `security-review` skill, which names no command.
- **The pass, the release and the rerender (the owner's steps).** The owner ran the pass on this tree; the gates closed at once and
  the refusal line named the cause and its first place (`first at 'packages/workbench/code-work'`, from increment J); the owner
  ran `wb release-approvals` (14 approvals for the package, three new directories under `workbench/shipped_approvals/packages/`,
  six older shipped records reported as not part of the release, left for a later sweep by hand), then `wb upgrade` and
  `wb rerender`. The rerender also refreshed the tracked copies under `.workbench/` and `AGENTS.md` (the new policy lines
  above), and the two helpers of increment H (`groundwork`, `review-engine`), which the earlier upgrade had not pulled.
- **Verification as run on the real tree** (`-W error`): `test_permissions_drift` 22, `test_verify` 69, `test_skill_names` 8,
  `test_harnesses` 28, `test_firstparty` 57, `test_gate` 27, `test_agent_gate` 59, `test_rendering` 85, all OK; `wb run code-work
  check`: 82 plans, no problems; `wb preview rerender --package <the local package>` lists the root file, the settings files and every
  rendered skill and agent (two agents, twenty-one skill files) as "left as it is" and ends "nothing to change"; the rendered
  `peer-review` skill holds the new sentence. `test_gate_hook` was not rerun (this increment changes skill text and a policy block,
  not code it reads; it passed after J).
- **Not done:** the commit; the six stale shipped records; `code-work/files/docs/plans/README.md` still says "the owner makes it"
  (a seeded document the test does not read).
