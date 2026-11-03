# The level `delegated` for an action key, and named risk profiles

Status: In Progress
Created: 2026-11-03
Candidate: none (the closest, `workbench-v1#checkpoint-levels-beyond-block`, leaves `delegated` for keys other than the plan approval out of its boundary; this plan decides what it means, on the owner's direction of 2026-11-03, without building the hook that carries it; it is the first of three plans that split `2026-11-02-permission-levels-for-every-command`)
Specs: command-permissions, trust-and-approval, action-review

## Goal

The owner's vision (2026-11-03, confirmed step by step): the owner sets an action, such as extending a review, to `delegated`. If the
proper modules are installed and configured, then when the action is needed a request goes through the bridge (`ask-codex`,
`ask-ollama` or another) for approval, alongside the owner's own prompt. A decline from the bridge waits for the owner to confirm, and
the owner can override it. A bridge that fails is treated as a decline, so the system fails closed and waits for the owner. When the
owner or the bridge approves, work continues. The goal is to keep a project moving with the help of a bridge when the owner is away
or distracted; the risk is the owner's to define and accept.

This plan writes that down as a decision, so that the hook which `action-review` builds after its shadow period is built into a rule
of the level system and not beside one, and it adds named risk profiles with a per-key override, so that the owner picks a risk
appetite once instead of key by key. Shipped defaults stay as they are.

## Scope

In:

- a decision on what `delegated` means for an action key: which keys offer it, what a bridge's verdict stands in for, the owner's
  prompt alongside, what a decline or a failure does, the owner's override, whether a profile may set it, and which keys never offer it;
- a decision on named profiles (or their rejection, with the reason);
- the accepted decision written into the specs, labelled "Decided, not built";
- profiles in the settings (`wb settings`, `wb doctor`), if the owner accepts them;
- the specs as built.

## Non-goals

- Building `delegated` for any key other than `approve-plan`, and building any hook that decides: that is the `action-review` plan
  after its shadow period.
- Changing a shipped default, the compiled floor or the personal `floor` list.
- Changing the shadow hook, or installing it.
- Any change to the registry's structure; plan `2026-11-02-permission-system-consistency` builds it and this plan adds to it.
- The installer commands' levels and the module conformance work: the plans `2026-11-02-permission-levels-for-every-command` and
  `2026-11-03-module-conformance-levels-and-hooks`.

## Assumptions and constraints

- **This plan starts only after `2026-11-02-permission-system-consistency` is `Completed`** (it is). It builds on the registry, the
  kit's preview-digest helper, the corpus and `wb doctor` that plan delivers.
- The `action-review` shadow hook (built by another session and merged into `main`, commit `8dc30ca`; not yet installed by the owner)
  is a `PermissionRequest` hook for `Bash` that records what the review engine would say about each prompted command and decides
  nothing (`docs/specs/action-review.md`, "The shadow hook"). The engine is built for `commit` and `remove` (rules for `safe-git`
  commit and remove); no hook decides yet, and the shadow period that measures it (the owner's labels, a test set, the cutover bound)
  has not started. `delegated` today is offered by the plan approval only, by a converged, sealed review.
- The original design (`docs/specs/action-review.md`, "Purpose and reason", "Non-goals and anti-goals") is a hook in the owner's
  user-level configuration that, for a command an `ask` rule prompted, collects facts, runs fixed checks, asks a model through a bridge
  for a verdict against a rubric, and for the actions the owner delegates (`DELEGABLE` was commit and remove) can allow the command, a
  decline falling back to the normal prompt.
- Any change to what a key offers changes the settings version and the rendering record; the owner runs `wb rerender` in a terminal
  after each increment that changes a rendered rule, and `wb doctor` says when it is due. The settings version is also bumped by the
  sibling plan `2026-11-02-permission-levels-for-every-command` (increment B; here increment C); whichever builds second builds on the version the first
  left.
- A decision record is written `Proposed`; accepting it is a checkpoint at level `ask`.
- **A spec is never left false between increments.** An increment that changes what a key offers updates the lines of the specs that its
  change makes false in the same commit. A decision that builds nothing leaves those lines true and, once accepted, is added to the
  specs as a paragraph labelled "Decided, not built" (increment B); increment D replaces a label with a "built" statement only for
  what is built, and checks the whole.
- Increment C is separable: the owner may drop it if the record rejects profiles.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. The record of increment A is accepted. No accepted record is rewritten.
2. The record says what `delegated` means for an action key: which keys offer it, what a bridge's verdict stands in for, that the
   owner's prompt shows alongside the bridge's request, that a decline, an error, a timeout or a command with no rule waits for the
   owner, who can override a decline, whether a profile may set it, and which keys never offer it (the author recommends: the floor and
   the compiled hard stops only; a digest-bound key offers `delegated`, with the same digest checked, and the plan approval is a key
   like the others), and whether the present restriction on a delegable plan (one Risks section with no hard-stop action) is kept.
3. The record says whether the harness shows the owner's prompt while a `PermissionRequest` hook runs, or names the test that finds
   out before a hook is built (the harness documentation does not say).
4. If profiles are accepted, the owner can select a profile (cautious, balanced, trusting, as the record defines them) and override any
   key; `wb settings` prints the profile and what it set; `wb doctor` reports a relaxed key in a dangerous class as a risk.
5. No setting an owner can write reads other than as written without `wb doctor` saying so.

## Increments

### Increment A — Decision: `delegated` for an action key, and risk profiles

**Outcome:** a `Proposed` record decides what the level `delegated` means for an action key (the owner's goal that the `action-review`
engine, through a bridge, provides the approvals), and defines named profiles or rejects them with the reason.
**Dependencies:** `2026-11-02-permission-system-consistency` completed.
**Affected areas:** `docs/decisions/` and its index.
**Steps:**
1. Define what each profile sets per danger class (cautious is today's shipped defaults; the others relax named classes only), that
   a per-key entry overrides the profile, and that no profile relaxes the floor or a key whose class the record marks dangerous
   beyond `ask`. Say whether a profile may set `delegated` for the keys that offer it, and whether `delegated` counts as beyond
   `ask` for that rule (the registry orders it after `ask`; but a verdict that falls back to the prompt on any doubt is not the
   relaxation that `none` is, which is the question the record answers).
2. List the alternative of per-key levels only, and why a profile is or is not worth the second concept.
3. **`delegated` for an action key.** The owner's vision is in the Goal. The record decides, and the author recommends, in this shape:
   - **Meaning.** `delegated` offers the same thing as `ask` (the same preview, the same digest, the same check in the command's
     own lock) and changes only who may confirm: the owner at the prompt, or the bridge, whichever answers first. The bridge reviews
     the exact command and its facts and approves that exact digest. Anything but an approve (a decline, an error, a timeout, an
     unreviewable command, no rule, no hook installed, a failed hook) leaves the decision to the owner. Without the modules,
     `delegated` reads as `ask`. It never lets through what `ask` would not.
   - **Alongside.** The owner's prompt is shown while the bridge works, so the owner never waits on a slow bridge. Whether the
     harness shows the prompt while a `PermissionRequest` hook runs is not stated in its documentation (checked 2026-11-03: the page
     says nothing on it, only that a hook's output decides when it returns and that a hook's failure or timeout is not a deny unless
     `onFailure` is set). A test on a copy, in the shadow's install steps or by the `action-review` plan, finds out before anything is
     built; if the harness holds the prompt until the hook returns, the record says what the owner sees and for how long, and the
     hook's time limit is chosen from that.
   - **Which keys offer it.** Every key that can offer it, if configured, so the owner can keep a project moving: a key whose module
     declares `delegated` and whose action has a bridge rule (a `describe` that gives the engine its facts). Today the engine has rules
     for `safe-git commit` and `remove` only; the review engine's `extend` and the other digest-bound keys each need a `describe` and
     a rule, which the `action-review` plan builds one action at a time. The registry's rule "`delegated` for the plan approval only"
     becomes "the keys whose declaration offers it".
   - **The plan approval is a key like the others** (the owner prefers consistency): it is approved at `delegated` by the same route,
     a bridge's approval of the exact digest alongside the owner's prompt. Its present route (a converged, sealed review and the
     delegate command) is judged by the record: kept as the way a plan's rule approves, or folded into the general route.
   - **What a plan may contain to be delegable.** Today a plan is delegable only when it has exactly one Risks section and that
     section lists no hard-stop action (`trust-and-approval.md`, "Checkpoints, delegation and hard stops" and "Delegable"), because
     hard stops stop at the time of the action whatever the plan says. The record says whether that restriction is kept in the
     general route (the author recommends: kept, for the plan approval, whoever confirms it) or replaced, and why; and that the
     enforcement and its tests are part of the build that is not in this plan.
   - **Never offered.** The floor and the compiled hard stops only, as keys; the plan-content restriction above is separate.
   - **The owner's override and the record.** A bridge decline is shown to the owner at the prompt as far as the harness allows (the
     reason is not important to the owner); the owner confirms and work continues. Each verdict, each failure and each override is
     logged, as the `ask` runs are.
   - **Where the hook is.** In the owner's user-level configuration, as the `action-review` design requires ("the enforcement point
     ... outside a project's reach"), reading the owner's levels table in the guarded store to know which keys are `delegated`; not
     in the two project files the installer hashes. `wb doctor` cannot read the user level, so for a key at `delegated` it notes that
     the bridge's approval depends on a hook it cannot see.
   - **The precondition for building it** is the one the owner already set in the spec: at most 10% false declines among the labelled
     real commands, at least 10 labelled commits and 10 labelled removals, no false approve on the labels or the test set, and the
     owner's word to cut over. The old approver's log shows why the false declines are the thing to measure: of its 336 declines, 146
     failed a fixed check before the model was asked, led by `no_reviewer_directed_text` (102), `no_secret_lines` (102) and
     `targets_look_disposable` (48), and the new rules and rubric still hold those checks; the shadow labels them first. The shadow has
     not started; building the hook, and so the first `delegated` level, is the `action-review` plan's after it.
   The alternatives to list: a profile element only; a separate mechanism outside the levels (this work's earlier recommendation,
   given before the owner's goal was clear, and the reason it is not recommended: it would leave the owner two settings for one
   decision, the thing plan `2026-11-02-permission-system-consistency` removed). Read the shadow's spec before writing the record.
4. Run `wb run code-work check`. Stop with the record `Proposed`.
**Verification:** the document check passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-delegated-levels-and-risk-profiles#A`.

### Increment B — The decision in the specs, labelled "Decided, not built"

**Outcome:** each spec that today says only the plan approval offers `delegated` also says what the accepted record decides, labelled
so that no line claims it is built.
**Dependencies:** A accepted.
**Affected areas:** `docs/specs/command-permissions.md`, `docs/specs/trust-and-approval.md` and `docs/specs/action-review.md`.
**Steps:**
1. Add to each spec a paragraph headed "Decided, not built" that names the record and says what it decides (the meaning of
   `delegated` for an action key, the alongside prompt, the fail-closed fallback, the keys that offer it and never offer it, the
   plan-content restriction, and the profiles if accepted). Leave the lines that describe what is built as they are: a spec states
   what is true now, so the decision is labelled and not written as built.
2. Run the document check.
**Verification:** the document check passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-delegated-levels-and-risk-profiles#B`.

### Increment C — Profiles in the settings

**Outcome:** the owner can select a profile and override a key; `wb settings` and `wb doctor` show what it set.
**Dependencies:** A accepted, with profiles in it; B.
**Affected areas:** `workbench/settings.py`, `workbench/settingscmd.py`, the registry, `workbench/doctor.py`, `tests/test_settings.py`,
`tests/test_settingscmd.py`, `tests/test_doctor.py`.
**Steps:**
1. Write the tests first: a profile sets the levels the record defines; a key entry overrides it; an unknown profile, or one that
   would relax a key past what the key offers, reads as `block` and is reported; the settings version is bumped and the old
   version still reads.
2. Build it; keep the file's strict form.
3. `wb doctor` reports the profile and each key it relaxed in a dangerous class.
**Verification:** the tests named above and the drift test (`tests/test_permissions_drift.py`).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-delegated-levels-and-risk-profiles#C`.

### Increment D — The specs as built

**Outcome:** the specs say what is decided and what is built.
**Dependencies:** B, and C if it was kept.
**Affected areas:** this plan's Result; `docs/specs/command-permissions.md` (the levels, the profiles, `delegated` as decided and what is
not built), `docs/specs/trust-and-approval.md` (the `via` of an approval and the plan approval as a key like the others), and
`docs/specs/action-review.md` (the owner's goal, the level the hook is built into, the alongside question), `docs/development.md`.
**Steps:**
1. If C was built, run `wb doctor`; the owner fixes what it flags and reruns `wb rerender` in a terminal, and the profile is run once
   in this clone and recorded.
2. Replace a "Decided, not built" label with a "built" statement only for what C built (the profiles); where `delegated` is only
   decided, the label stays and says that the `action-review` plan builds it after its shadow period. Tell the owner the roadmap
   file is not edited.
3. Run the document check.
**Verification:** the run above, as run; the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-delegated-levels-and-risk-profiles#D`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. After D, rerun only `wb doctor`, the
document check and the drift test and gate corpus of `2026-11-02-permission-system-consistency` (`tests/test_permissions_drift.py`,
`tests/test_gate_corpus.py`). The full suite runs only if the owner decides after the author states what could break outside the
tested area.

## Risks and sensitive actions

- **A `delegated` level lets a bridge's verdict stand in for the owner's prompt.** Increment A only decides what it means: the owner's
  prompt is shown alongside the bridge's request, every outcome but an approve leaves the decision to the owner, the record keeps it
  away from the floor and the hard stops only, and building the hook is the `action-review` plan's, after its shadow period and the
  owner's cutover bound. A model's verdict can be wrong in the harmful direction (a false approve), which is why the bound allows none
  on the labels and the test set. The old approver's false declines came from fixed checks, and the new rules still hold them.
- **Relaxing a level lets the agent run a dangerous command.** That is the owner's chosen risk. Defaults stay `block`, the floor is
  untouched, profiles cannot relax a dangerous class past `ask`, and `wb doctor` reports a relaxed dangerous key as a risk.
- **The harness may hold the owner's prompt while a hook runs.** Its documentation does not say. The record names the test that finds
  out before a hook is built; until then `delegated` is a decision, not a feature.
- **Accepted decisions outrank code.** A conflict is settled by a new superseding record, never by rewriting an accepted one.

## Review record

- **Reviewer:** the project's review bridge `ask-codex`, model `gpt-5.6-terra`, effort `medium`, through
  `wb run review-engine review-plan` (2026-11-03), asked for by the owner. This plan was split out of
  `2026-11-02-permission-levels-for-every-command`, whose own review covered the earlier text and not this split.
- **Rounds:** 3 of the bound of 3; round 3 returned no meaningful finding and the review converged. Four findings in all; 3 applied,
  1 rejected.
- **Applied:**
  - Round 1 (major): the plan did not say whether the present restriction on a delegable plan (exactly one Risks section, no
    hard-stop action, `trust-and-approval.md`) is kept when the plan approval joins the general route; increment A now decides it,
    with the enforcement left to the build, and criterion 2 names it.
  - Round 1 (major): increment A changed only records while the specs say that only the plan approval offers `delegated`; the
    accepted decision now goes into the three specs as a paragraph labelled "Decided, not built", so no spec is false.
  - Round 2 (major): that spec step made increment A two commits; it is now its own increment B, profiles are C and the as-built
    pass is D.
- **Rejected:** round 2 (major), that the plan names no roadmap candidate. The `draft-plan` skill allows `Candidate: none` with a
  one-line reason, the owner directed this work, and adding a candidate means editing a roadmap, which is the owner's decision. The
  owner may still want one.
- **Left for the owner:** approval of this plan, which is the owner's act; a converged review is not an approval. At `ask`, the
  agent shows the preview and the digest and runs the approval on the owner's confirmation. Whether the owner wants a roadmap
  candidate for this work.

## Deferred work

- Building `delegated` for the keys other than `approve-plan` (`checkpoint-levels-beyond-block`), and the hook that decides (the review
  engine answering `PermissionRequest` for a key at `delegated`), with the rule and `describe` for each action (`extend`, the other
  review-engine arguments, the release, the acceptance of a decision): the `action-review` plan after its shadow period, and the
  owner's steps to install and label the shadow.
- Reading the harness's global configuration (`workbench-v1#global-settings-check`).
- Per-project overrides of the owner's personal settings.

## Result

### Increment A (2026-11-03)

- **Done:** wrote the record `docs/decisions/2026-11-03-delegated-for-an-action-key-and-named-risk-profiles.md` with the status
  `Proposed`; ten numbered decisions (the meaning of `delegated` for an action key, the owner's prompt alongside, the keys that offer
  it, the plan approval as a key like the others, the plan-content restriction, the keys never offered, decline, failure and
  override, where the hook is registered, what must be true before a hook that decides is built, and the three profiles with the
  danger class they act on), the alternatives, the consequences and the evidence. The plan's status is `In Progress`. No code and no
  spec changed.
- **Verification run:** `wb run code-work check` -> "checked 88 plans, check found no problems" (it checks plans, not decision
  records). The key counts in the record (73 keys: 44 `reads`, 23 `governs`, 6 `project`) come from `wb settings` run in this clone.
- **Review:** one round by the `reviewer` agent, no bridge. Seven findings, one blocking, all applied or answered:
  - Blocking: the record said both that `delegated` reads as `ask` without the modules and that the plan approval keeps its working gate
    (a converged review with no hook); decisions 1 and 4 now say the general route is for a key with a bridge rule and the plan
    approval keeps its gate.
  - The record changes two lines of present specs (the engine "does not widen delegation" and "a code constant", and `verify`
    refusing `delegated` in a module's `levels`); decision 3 now names both, for increment B to label.
  - The record now names `governs` as the dangerous class, says `delegated` counts as beyond `ask` for it and not for `project`, and
    that the plan approval, a `governs` key, gets `delegated` only by the owner's own entry.
  - The profiles change almost nothing today (the six `project` keys offer `block` and `none` only; three `governs` keys offer
    `ask`); the record says so and that this depends on the sibling plans.
  - The decline counts (102, 102, 48) were worded as if inside the 146; they are over all 336 declines.
  - The alternative "`delegated` through a profile alone" was added; the evidence names tool versions.
- **Not done / not checked:** the record is `Proposed`; accepting it is the owner's checkpoint at `ask`. Not checked: the hooks
  documentation beyond the part read verbatim (no content hash), the harness's behaviour with a `PermissionRequest` hook, and the
  claim in decision 8 about the hashed project files, which is the spec's.
- **For the owner:** the decision whether the plan approval's present gate stays until the hook is built (decision 4), and whether
  `delegated` may never be set by a profile for `governs` (decision 10), are the two choices most worth a look before accepting.
