# `delegated` is a bridge's approval of the same confirmation an action key asks for, and the owner may choose a named risk profile

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-03
Date: 2026-11-03

## Context

The levels are `block`, `ask`, `delegated` and `none`. Today only the plan approval offers `delegated`, and its gate is a converged,
sealed review of the exact bytes (`docs/specs/command-permissions.md`, "Which levels a key offers"). The `action-review` module was
designed so that its engine, through a bridge such as `ask-codex` or `ask-ollama`, could approve a command that an `ask` rule had
prompted for the actions the owner delegates (`DELEGABLE` was commit and remove), a decline falling back to the normal prompt
(`docs/specs/action-review.md`, "Purpose and reason", "Non-goals and anti-goals"). The engine is built for `commit` and `remove`; the
shadow hook records what it would say and decides nothing; no hook answers, and the shadow period that measures it has not started.

The owner's vision (2026-11-03, confirmed step by step): the owner sets an action, such as extending a review, to `delegated`. If the
proper modules are installed and configured, then when the action is needed a request goes through the bridge for approval, alongside
the owner's own prompt. A decline from the bridge waits for the owner to confirm, and the owner can override it. A bridge that fails
is treated as a decline, so the system fails closed and waits for the owner. When the owner or the bridge approves, work continues.
The goal is to keep a project moving with the help of a bridge when the owner is away or distracted; the risk is the owner's to define
and accept. Every action that can be delegated should be, if configured; the owner prefers consistency, so the plan approval is
treated like the others; the reason a bridge gave for a decline matters little to the owner.

The earlier record `2026-11-02-one-permission-registry-and-key-model` left named risk profiles "for a later record", and
`2026-10-26-a-level-for-every-command` decision 4 rejected a master profile that turns every protection off. This record is that later
one. The plan is `2026-11-03-delegated-levels-and-risk-profiles`, increment A.

## Decision

**1. What `delegated` means for an action key.** `delegated` offers the same thing as `ask`: the same read-only preview, the same
digest, and the same check of that digest inside the command's own lock. It changes only who may confirm: the owner at the prompt, or
the bridge, whichever answers first. The bridge reviews the exact command and its facts and approves that exact digest. Every other
outcome (a decline, an error, a timeout, an unreviewable command, no rule for the action, no hook installed, a failed hook) leaves the
decision to the owner. Without the modules, `delegated` reads as `ask`. It never lets through what `ask` would not. Decisions 1, 2
and 7 describe the general route for an action key that has a bridge rule. The one key at `delegated` today, the plan approval, keeps
the gate it has (decision 4) and does not read as `ask`.

**2. Alongside.** The owner's prompt is shown while the bridge works, so the owner never waits on a slow bridge. The harness's hooks
documentation does not say whether the prompt is shown while a `PermissionRequest` hook runs (see Evidence). Before any hook is built,
the `action-review` plan finds out by a test on a copy; if the harness holds the prompt until the hook returns, a record says what the
owner sees and for how long, and the hook's time limit is chosen from that.

**3. Which keys offer it.** Every key that can offer it, when configured: a key whose module declares `delegated` in its `levels` and
whose action has a bridge rule, that is, a `describe` that gives the engine its facts and a rule. The registry's rule "`delegated`
for the plan approval only" becomes "the keys whose declaration offers it". Today the engine has rules for `safe-git commit` and
`remove` only. The review engine's `extend` and the other digest-bound keys (the release, the acceptance of a decision, the other
review-engine arguments) each need a `describe` and a rule; the `action-review` plan builds them one action at a time, after its
shadow period. A digest-bound key offers `delegated` with the same digest checked, because the bridge approves that exact digest and
not an open command. This changes two lines of the present specs, which increment B labels: `docs/specs/action-review.md`
("Non-goals and anti-goals") says the engine "does not widen delegation" and that which actions a verdict may stand in for is "a code
constant of the enforcement point, as `DELEGABLE` is today"; under this decision the owner's levels table decides, and a module's
declaration with a bridge rule makes an action eligible, so the code constant goes when the hook is built. And
`docs/specs/command-permissions.md` ("Which levels a key offers") says `verify` refuses `delegated` in a module's `levels`; the build
lifts that refusal for a command that gives a `describe` and a rule. Neither changes until the build.

**4. The plan approval is a key like the others.** The end state is that it is approved at `delegated` by the same route: a bridge's
approval of the exact digest, with the owner's prompt alongside. Until the hook is built it keeps the gate it has, which works today
with no hook and no prompt: a converged, sealed review of the exact bytes, run by the agent with `wb delegate-approve-plan`. That
review is the bridge's rule for that key. It does not read as `ask` before the hook exists; the line in decision 1 that `delegated`
reads as `ask` without the modules is for a key whose only gate would be the hook. The `action-review` plan then decides whether the
review folds into the general route. This record changes no code.

**5. A plan's content restricts delegation, whoever confirms.** A plan is delegable only when it has exactly one Risks section and that
section lists no hard-stop action (`docs/specs/trust-and-approval.md`, "Checkpoints, delegation and hard stops" and "Delegable"),
because hard stops stop at the time of the action whatever the plan says. This is kept for the plan approval at `delegated`, whether
the route is the converged review or a bridge's approval. Its enforcement and tests are part of the build that is not in this plan.

**6. Never offered.** The floor and the compiled hard stops, as keys. No other key is excluded by its class or by being digest-bound.

**7. Decline, failure and override.** A decline waits for the owner, who can override it by confirming at the prompt; work then
continues. A failure of the bridge or the hook is a decline. The reason a bridge gave is shown at the prompt as far as the harness
allows and is not required. Each verdict, each failure and each override is logged, as the `ask` runs are.

**8. Where the hook is registered.** In the owner's user-level configuration, as the `action-review` design requires ("the enforcement
point ... outside a project's reach"), reading the owner's levels table in the guarded store to learn which keys are `delegated`; not
in the two project files the installer hashes, since an edit to either makes the keys at `ask` and `none` read `block` until a
rerender. `wb doctor` cannot read the user level, so for a key at `delegated` it notes that the bridge's approval depends on a hook it
cannot see.

**9. What must be true before a hook that decides is built.** The cutover bound the owner set in `docs/specs/action-review.md`
("Accuracy and cutover"): at most 10% false declines among the labelled real commands (provisional), at least 10 labelled commits and
10 labelled removals, no false approve on the labels or the test set, and the owner's word to cut over. The old approver's log shows why
false declines are the thing to measure: of its 336 declines, 146 failed a fixed check before the model was asked and 190 were the
model's. Counted over all 336 declines (a decline can fail several checks), the checks that failed most were `no_secret_lines` (102),
`no_reviewer_directed_text` (102) and `targets_look_disposable` (48), and the rules and rubric of the engine still hold those checks. The owner's steps to install the shadow and label real commands come first.

**10. Named risk profiles.** The owner may set one `profile` in the settings; a per-key entry overrides it. A profile sets a level only
for a key that offers it, and a key it cannot set reads as its shipped default. The registry's danger classes are the unit:

| Profile | `reads` | `project` | `governs` |
|---|---|---|---|
| `cautious` | shipped | shipped | shipped |
| `balanced` | shipped | `ask` | shipped |
| `trusting` | shipped | `delegated` where offered, else `ask` | `ask` |

`cautious` is today's behaviour and the default. The dangerous class is `governs` (a key that changes the rules that govern the agent;
decision 4 of `2026-11-02-one-permission-registry-and-key-model`). `delegated` counts as beyond `ask` for that class: no profile sets
it there, because a bridge's approval is a relaxation of the owner's own confirmation where a mistake changes the rules themselves. It
does not count as beyond `ask` for `project`, where `delegated` reads as `ask` without the modules and the owner's confirmation or the
bridge's approval of the exact digest is still required. No profile touches the floor or the compiled hard stops, and none sets `none`.
An owner who wants `delegated` for a `governs` key, the plan approval included, or `none` anywhere, writes that key's entry, as today. An unknown profile name reads as `block` for the
whole table and `wb settings` and `wb doctor` report it. `wb settings` prints the profile and what it set; `wb doctor` reports a key
relaxed in a dangerous class as a risk. The settings version is bumped and the old version still reads. Building this is increment C
of the plan, which the owner may drop.

## Alternatives considered

- **A separate mechanism outside the levels** (this work's own first recommendation, written before the owner's goal was clear): a
  deciding hook that runs where no key governs the command. Rejected: it leaves the owner two settings for one decision, which plan
  `2026-11-02-permission-system-consistency` removed, and it cannot serve the owner's wish to delegate any action.
- **`delegated` only for keys with a rule today** (commit and remove). Rejected as the definition: the owner wants every action that
  can be delegated to be. It is the build order, one action at a time.
- **Excluding digest-bound keys from `delegated`.** Rejected: the bridge approves the exact digest, which is the same confirmation `ask`
  asks for, and `extend` is the owner's own first example.
- **Prompt held until the bridge answers.** Rejected as a design: the owner would wait on a slow bridge. Whether the harness does it
  is unknown (Evidence), so the test comes first.
- **A bridge's decline that blocks.** Rejected: a decline waits for the owner, who may override it, as the owner described.
- **A second route for the plan approval** (a bridge's approval beside the converged review). Rejected for now: it would be two routes
  for one key; the present review is kept as that key's rule until the hook is built.
- **Per-key levels only, with no profiles.** Not rejected: it is how it works today, and the owner may drop increment C. Profiles are
  worth the second concept only because the registry holds 73 keys in this project (44 `reads`, 23 `governs`, 6 `project`) and the
  owner wants one choice of appetite; the owner's per-key entry still wins. A profile changes only a `project` key or a `governs` key
  that offers `ask`. Today that is almost nothing: the six `project` keys (`wb install`, `adopt`, `upgrade`, `add`, `attach` and
  `recover`) offer `block` and `none` only, and of the `governs` keys only `approve-plan`, `accept-decision` and
  `wb release-approvals` offer `ask` (`workbench/levels.py`, `INSTALLER_KEYS`; `wb settings`). A profile starts to matter as the plans
  `2026-11-02-permission-levels-for-every-command` and `2026-11-03-module-conformance-levels-and-hooks` give more keys `ask`, which is
  why increment C is separable and the owner may drop it.
- **`delegated` set through a profile alone, with no per-key level.** Rejected: a profile names a risk appetite for a class of keys and
  cannot say which action has a bridge rule; the level of a key stays its own, and a profile only chooses among the levels a key
  offers.
- **A profile that sets `none`, or that relaxes `governs` beyond `ask`.** Rejected: decision 4 of `2026-10-26-a-level-for-every-command`
  rejected a master profile that turns protections off, and `governs` keys change the rules that govern the agent.

## Consequences

- `delegated` becomes a general level in the decision, but it is built for no key besides the plan approval until the `action-review`
  plan builds the hook, after the shadow period. Until then a key at `delegated` that the engine cannot serve reads as `ask`.
- Each action needs its own `describe` and rule before it can be delegated, which is real work and the place where false declines come
  from. The shadow's labels measure them first.
- The owner's prompt may be held by the harness while the hook runs; if so, "alongside" costs the owner a wait up to the hook's time
  limit, which the test will show. A hook cannot answer after it has returned.
- A model's verdict can be wrong in the harmful direction (a false approve). The cutover bound allows none on the labels and the test
  set, and the owner accepts the rest of the risk by setting a key to `delegated`.
- A hook registered at the user level is outside the installer's rendering record, so `wb doctor` can only note it.
- The plan-content restriction is kept, so a plan that lists a hard stop is never approved by a bridge, whichever route is used.
- Specs get a paragraph labelled "Decided, not built" (increment B) and a later "built" statement for the profiles only (increment D).

## Evidence

Provenance of the claims above, retrieved or run on 2026-11-03 at commit `451686062e68` in this clone:

- The meaning of the levels, the single key that offers `delegated`, and the registry's classes: read from
  `docs/specs/command-permissions.md` ("Which levels a key offers", "Reading rules") and `workbench/levels.py`; the plan content
  restriction from `docs/specs/trust-and-approval.md` ("Checkpoints, delegation and hard stops", "Delegable").
- The original design, the cutover bound and the old approver's declines by failed check (1,019 rows, 336 declines, retrieved
  2026-10-25): from `docs/specs/action-review.md` ("Purpose and reason", "Non-goals and anti-goals", "Accuracy and cutover", "The
  approver's declines by failed check"), which carries its own provenance and hash. That log is not read again here.
- The engine's rules: `packages/workbench/action-review/rules/` holds `safe-git-commit.json` and `safe-git-remove.json`, and
  `rubric/rubric.md`, `rules/` and `helper/action-review` contain the check names `no_reviewer_directed_text`, `no_secret_lines`,
  `targets_look_disposable`, `change_is_safe_in_itself` and `facts_complete` (searched with `grep -rl`).
- What the hooks documentation says: source `https://code.claude.com/docs/en/hooks.md`, retrieved 2026-11-03, about 284,000
  characters, read through a fetching agent in four parts of which only about the first 160,000 characters came back verbatim; no
  content hash was recorded, because the reader gave none. On the question of whether the permission prompt is shown while a
  `PermissionRequest` hook runs, the page does not say. It says exit code 2 is not honoured for the event, that a hook failure or
  timeout otherwise lets the action go ahead unless `onFailure` is set, and that a hook's `decision` can allow or deny. This is
  evidence that the question is open, not that the answer is no.
- The count of keys and classes: `wb settings` (workbench 0.1.0, Python 3.15.0) run in this clone on 2026-11-03 printed 73 `key`
  lines, 44 `class=reads`, 23 `class=governs` and 6 `class=project`, each of the six `project` keys offering `block,none` (counted
  with `grep -c` and `sort | uniq -c`), which `workbench/levels.py` (`INSTALLER_KEYS`) agrees with.
- The owner's statements of 2026-11-03 are in the conversation of that day, not in a file.

Conclusion: the design can be recorded now, and the build waits for the shadow's data and for the test of the prompt.
