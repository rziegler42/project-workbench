# Verification effort

Status: Draft

The owner approved this design on 2026-11-02, after two rounds of review. Nothing in it is built, so it stays a `Draft`
until the plan that builds it is complete. Where it says what an agent does, that is
the behavior proposed for the `code-work` module; the current behavior is in `code-work.md`.

## Scope

How much an agent running the `code-work` increment loop tests, how often, and when it asks the owner for more: a wider
test run, or a security review. It covers the guidance in the practice skills, the increment loop, the plan-drafting
skill, the reviewer, and the policy line the module places in `AGENTS.md`.

The guidance is for any project that adopts the module. It names no language, build system, test runner or directory
layout.

## Non-goals

- A testing methodology. The module guides developers toward good practice; it does not prescribe how a project tests.
- Tiers of verification, a list of triggers for wider testing, or any time threshold. What takes seconds on one machine
  takes a minute on another, so the module does not judge cost; the owner does.
- A new checkpoint, setting or level. The owner's decision to run a wider check is made in conversation.
- A template, table or convention for a project's test commands, or a selector that maps changed files to tests.
- A plan status for a long check that has been accepted but not yet run.
- New rules in `code-work check`, and any change to the installer, the helper or the levels table.

## Anti-goals

The change fails even if it works as written when:

- the agent recommends a wider run or a security review by reflex, so the owner is stopped as often as before;
- the full suite becomes the "safe" default again under another name;
- a project is pushed toward a particular test tool or layout;
- a skipped check is forgotten and not reported.

## Assumptions and constraints

- The owner's guidance, given on 2026-11-02 in the session that produced this design: test the minimum that shows the
  change did not break what it touched; do not run a module's tests when nothing affecting it changed; run the full suite
  only when the change is exceptionally risky or likely to have an impact the narrower tests would not detect.
- Projects differ widely in suite size. Some full suites take hours. The owner weighs the risk against the length of the
  run, so the agent recommends and the owner decides.
- A project documents its own test commands, and `AGENTS.md` already says to prefer them.
- The module already asks the owner about a security review when a change materially touches a listed area
  (`packages/workbench/code-work/files/blocks/policy.md`; `code-work.md`, "Policy placed in `AGENTS.md`"). What
  stays: it names the capability `security-review` and no module, and a review runs only when the owner asks. What
  changes: the trigger. "Materially touches a listed area" is replaced by a named, concrete exposure (see Behavior);
  the listed areas become places to look and are no longer triggers.
- An approved plan cannot be edited beyond its status, review record and result without a new approval (`AGENTS.md`).
  The new guidance therefore governs what an agent does from the day the updated module is installed, for every plan
  whatever its status, and it does not rewrite any plan. A verification line already in a plan is the owner's statement
  and is run as written. To narrow an approved plan's line, the owner re-approves the plan.
- The practice skills are checked by tests that assert on their wording, so a change to the text carries a change to those
  tests.

## Behavior

### What the agent runs without asking

1. While working, the checks nearest the code it changed.
2. Once per increment, the tests of the area the change belongs to, where the change could affect that area.
3. A check that already passed on unchanged inputs is not run again. If a broader command contains narrower ones, the
   agent runs the broadest one it needs once, after the last relevant change, and not the broad one and its parts.
4. If the project documents no command for a check, the agent runs the narrowest documented one and asks the owner once.
   It does not guess a command.

### Recommending a wider run

- The full suite is not run by default, and not because it is the safe choice.
- The agent recommends a wider run only when it can name a specific way the change could break something outside the
  tested area that those tests would not catch. Example of a reason: "this renames a field that another unit reads, and
  that unit's tests are not in the area I ran". A reason that only says the change is large, shared or risky is not a
  reason, and the agent does not ask.
- The recommendation states the reason and what it proposes to run, and the agent stops and waits. The owner answers
  that it should run, or that the risk is accepted.
- If the project documents a way to select the tests a change affects, the agent uses it before reasoning about scope.

### Recommending a security review

- The same shape applies. The agent recommends a review only when it can name what is exposed, for example "this reads a
  path from the request and opens it, and nothing here validates it". A change that merely touches a listed area, such
  as the filesystem or a subprocess, is a place to look and not a reason.
- The agent asks once per surface. After the owner declines or a review has run, it does not ask again for the same area
  unless the change alters how input reaches privileged use.
- A review runs only when the owner asks. If no installed module provides `security-review`, the agent says so.

### Recording

- A recommendation the owner declines is recorded under `## Result` in the plan: the reason, and that the owner accepted
  the risk. A run the owner approves is recorded as run, with its result.
- A report of an increment says what was run, what was not run and why, and scopes each claim to what ran: "the billing
  tests pass; the wider run was not made", not "the tests pass".

### After the last increment

- The whole-plan verification (`code-work.md`, "The increment loop") follows the same rules and is not a full-suite run
  by default. It confirms that each increment's recorded verification still stands, that is, that no later increment
  changed the inputs of a check an earlier one passed; it reruns only what a later change invalidated; and it recommends
  anything wider only with a named reason, as above.

### Plans

- The plan-drafting skill asks each increment for the check that fits its work, and no longer defaults the verification
  line to the whole suite. A plan may still name the full suite where the owner wants it. A plan not yet approved is drafted or revised under this
  rule; an approved plan's lines are honored as written (see "Assumptions and constraints").

### The reviewer

- The reviewer reads the increment as now and also flags, as a finding, any concrete security risk it can name in it,
  whether or not the agent recommended a review. `request-review` does not pass it the agent's recommendations or the
  owner's decisions, and it flags a risk whether or not the plan it reads records one. The agent judges each finding
  against what it has already recorded, through `evaluate-findings`, and a risk the owner already accepted is
  rejected with that reason. The reviewer does not rerun the agent's checks.
- The reviewer is deliberately not asked to judge whether the agent tested enough. A missed wider-testing risk is cheap
  to find on a later run, and asking a read-only reviewer to audit test scope would push toward more testing. This is a
  choice and not an omission; the reviewer may still raise a concrete breakage it sees as an ordinary finding.

### Where the text goes

Left to the builder, within these limits: the practice skills (`test-first`, `verify-before-claiming`), `run-increment`,
`draft-plan`, `request-review`, `evaluate-findings` and the reviewer agent, one reworded policy bullet that keeps the security-review rule and
adds the wider-testing rule, the matching sections of `code-work.md` (including the last paragraph of "The increment
loop" and the plan template's "Verification for the plan as a whole"), and the tests that assert on that text.

## Acceptance criteria

- `test-first` no longer sends the agent from the narrowest check to "the verification the plan names" as a matter of
  course; it states the rules under "What the agent runs without asking".
- `run-increment` steps 4 and 5 tell the agent to run the check that fits the increment, and to stop and recommend, with a
  named reason, before a wider run or a security review.
- `draft-plan` no longer defaults a verification line to the whole suite.
- A recommendation made without a specific reason is not within the guidance; the skills say so and give a generic
  example of a good reason.
- The reviewer's instructions name any concrete security risk it can identify as a finding, without needing the agent's
  recommendations.
- `evaluate-findings` tells the agent to check the plan's `## Result` for a recorded recommendation and owner decision
  before it rejects a security finding as already accepted, and to cite that record in the reason.
- A plan's existing verification line is run as written, and the skills say so.
- The whole-plan verification in `code-work.md` and the plan template no longer implies a full run; it follows the rules
  above.
- The security-review trigger in the policy line is the named exposure, and the listed areas are examples of where to look.
- A declined recommendation has a place in the plan's `## Result`, and the skills say to write it there.
- The module's tests pass with the changed wording, and the module declares no new checkpoint, cap, setting or command.
- The guidance names no language, tool, build system or file layout.

## Calls marked as mine

These were my choices, not the owner's, and the owner may change them:

- The name and shape of this document, and its status as a Draft spec of its own and not a section of `code-work.md`.
- Honoring a plan's existing verification lines as written, and applying the guidance to every plan from installation.
- "Once per increment" as the point to run the area's tests.
- Using a project's documented selector first, where one exists.
- Having the agent ask once when no command is documented.
- The reviewer flags unrecommended security risks only; a missed wider-testing risk is not a reviewer finding. The owner
  agreed to this on 2026-11-02 after my recommendation, so it is the owner's decision and not only my call.

## Governing decisions and references

- Decisions: none yet. None is needed unless the owner later asks for an enforced checkpoint.
- Related specs: `code-work.md`, `terms.md`, `trust-and-approval.md`.
- The owner's guidance on verification and the choices made in conversation on 2026-11-02 are the source of this design.
  Other projects of the owner were read for ideas; they are untracked here and are not cited by path.
