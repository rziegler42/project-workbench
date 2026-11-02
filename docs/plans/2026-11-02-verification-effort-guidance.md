# Guide how much verification an agent runs

Status: Proposed
Created: 2026-11-02
Candidate: none (the owner asked for this on 2026-11-02 after the agents ran the full suite at almost every increment; the owner may add a roadmap candidate)
Specs: verification-effort, code-work

## Goal

An agent running the `code-work` increment loop tests the minimum that shows its change did not break what it touched, does not
rerun a check that already passed on unchanged inputs, and does not run the full suite by default. When it thinks a wider run
or a security review is needed, it says what specifically could go wrong, and the owner decides. The design is
`docs/specs/verification-effort.md`, approved by the owner on 2026-11-02. When the plan is done:

- `test-first`, `verify-before-claiming`, `run-increment` and `draft-plan` carry the rules of the spec's "What the agent runs
  without asking", "Recommending a wider run", "Recording", "After the last increment" and "Plans".
- `request-review`, `evaluate-findings` and the `reviewer` agent carry the rules for security findings.
- The policy line placed in `AGENTS.md` carries the wider-testing rule and the reworded security-review rule.
- `code-work.md` agrees with all of it.
- None of the changed text names a language, tool, build system or file layout.

## Scope

- The skills, the agent and the policy block of `packages/workbench/code-work/`, and their tests (increments A to C).
- The sections of `code-work.md` that the change makes stale, and the spec's own status (increments C and D).
- The close-out, the shipped approvals and the record of the upgrade (increments D and E).

## Non-goals

- Tiers of verification, a list of triggers for wider testing, a time threshold, a new checkpoint, setting or level, a template or
  table of a project's test commands, a plan status for an accepted-but-unrun check, new rules in `code-work check`, and any change to
  the installer, the helper or the levels table (all in the spec's non-goals).
- A change to any plan already written. An existing plan's verification line is run as written.
- Any other module's skills. A skill in a domain module may extend these, as `test-first` already says.

## Assumptions and constraints

- The owner's word is needed for each package change. The recent plans make a package change in one scripted pass that the owner
  authorizes with "run the pass", followed by one release by the owner; the hooks refuse other work while the pass runs. This plan
  follows that practice, and the owner confirms the exact steps at each increment.
- The plan `2026-11-02-bridge-request-controls` is under way in another session and makes package changes of its own in the same way. The
  two plans' passes must not overlap, so increments A to C wait until that plan's passes are finished or the owner says otherwise.
- The skills' wording is pinned by tests (`test_codework_practice.py`, `test_codework_skills.py` and the reviewer and module tests),
  so each change to a text carries a change to its test, written first and seen to fail.
- Tests are targeted, as the owner asked on 2026-11-02: the `code-work` module's tests and `wb verify` for a change to the module,
  and `wb check` and `wb run code-work check` for a document. A wider run is recommended to the owner with a named reason; the
  Result says which tests ran and why that was enough. This plan is its own first use of the rule.
- Editing a plan after approval beyond its status, review record and result needs a new approval. The owner's approval of this plan
  also covers the edits it names to `code-work.md`, which the spec requires the owner to approve.

## Completion criteria

1. `test-first` no longer sends the agent from the narrowest check to "the verification the plan names" as a matter of course; it states
   the rules of the spec.
2. `run-increment` step 4 tells the agent to run the check that fits the increment, and to stop and recommend, with a named reason,
   before a wider run or a security review.
3. `draft-plan` and its template no longer default a verification line to the whole suite, and the skills say that a plan's existing
   line is run as written.
4. `verify-before-claiming` scopes each claim to what was run and says what was not run.
5. `evaluate-findings` tells the agent to check the plan's `## Result` for a recorded recommendation and owner decision before it rejects a
   security finding as already accepted, and to cite that record; `request-review` does not pass the reviewer the agent's recommendations.
6. The `reviewer` agent names any concrete security risk it can identify as a finding, and is not asked to judge whether the agent tested
   enough.
7. The policy line reads as the spec says, and the listed areas of the security-review rule are examples of where to look.
8. `code-work.md` agrees: the last paragraph of "The increment loop", "Policy placed in `AGENTS.md`", the acceptance criteria and "As
   built". The plan template's "Verification for the plan as a whole" no longer implies a full run.
9. The module declares no new checkpoint, cap, setting or command (`module.json` is unchanged), and the changed text names no language,
   tool, build system or file layout (a test shows it).
10. The module's tests, `wb check`, `wb run code-work check` and `wb verify packages/workbench` report no problem, the shipped approvals are
    current, and the installed copies match the package.

## Increments

### Increment A — The practice skills, the loop and the plan template

**Outcome:** `test-first`, `verify-before-claiming`, `run-increment` and `draft-plan`, with its template, say what the spec says.
**Dependencies:** none.
**Affected areas:** `packages/workbench/code-work/harness/neutral/skills/test-first/SKILL.md`, `verify-before-claiming/SKILL.md`,
`run-increment/SKILL.md`, `draft-plan/SKILL.md` and `draft-plan/template.md`, and the tests that pin them
(`packages/workbench/code-work/tests/test_codework_practice.py`, `test_codework_skills.py`, and the test of the template if one exists).
**Steps:**
1. Read the spec's "Behavior" and the four skills. Write the tests first in a scratch copy, one per rule of criteria 1 to 4: the text
   states the default checks, the repeat rule, the named-reason rule and the record of a declined recommendation; `run-increment` step 4
   stops and recommends before a wider run; a claim is scoped to what ran; a plan's existing line is run as written; the template's
   whole-plan heading no longer implies a full run; and the changed files name no language, tool, build system or file layout.
2. See the new tests fail against the current text for the right reason.
3. Edit the five files in one scripted pass, with the owner's word and a release.
4. Ask the `reviewer` to read the increment.
**Verification:** the module's tests pass (the new ones failed first); `wb verify packages/workbench` reports no problem; a test shows
that the changed files name no tool or language.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-verification-effort-guidance#A`.

### Increment B — The review side

**Outcome:** the reviewer flags concrete security risks without being given the agent's recommendations, and the agent filters its
findings against the plan's recorded decisions.
**Dependencies:** A.
**Affected areas:** `packages/workbench/code-work/harness/neutral/skills/request-review/SKILL.md`, `evaluate-findings/SKILL.md`,
`packages/workbench/code-work/harness/neutral/agents/reviewer.md`, and their tests (`test_codework_reviewer.py`, `test_codework_skills.py`).
**Steps:**
1. Write the tests first: the reviewer's text names a concrete security risk as a finding, and says it does not judge test scope;
   `request-review` lists no recommendation among what it gives the reviewer; `evaluate-findings` says to check `## Result` for a
   recorded recommendation and decision before rejecting a security finding as already accepted, and to cite it. The reviewer's tools
   stay `read, search`.
2. See them fail, then edit the three files in one scripted pass with the owner's word and a release.
3. Ask the `reviewer` to read the increment.
**Verification:** the module's tests pass (the new ones failed first); `wb verify packages/workbench` reports no problem; the reviewer's
tools line is unchanged (shown by the diff).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-verification-effort-guidance#B`.

### Increment C — The policy line and the spec

**Outcome:** the policy line and `code-work.md` agree with the skills.
**Dependencies:** A and B.
**Affected areas:** `packages/workbench/code-work/files/blocks/policy.md`, `docs/specs/code-work.md` (the last paragraph of "The increment
loop", "Policy placed in `AGENTS.md`", the acceptance criteria, "As built"), the tests that pin the policy text, and the plan template
text in `packages/workbench/code-work/files/docs/plans/README.md` if it speaks of a full run (it lists "Verification for the plan as a
whole" as a heading only).
**Steps:**
1. Write the test first for the new policy text: the wider-testing rule, the reworded security-review rule that keeps the capability name
   `security-review` and names no module, and a review that runs only when the owner asks.
2. See it fail, then edit `policy.md` in one scripted pass with the owner's word and a release.
3. Edit `code-work.md` where the change makes it stale. The spec edits are the ones the plan names, and the owner's approval of the plan
   covers them.
4. Search `tests/` and the module tests for tests that read the policy block or the rendered `AGENTS.md`, and run those. The reason is
   named: the block is rendered into the `AGENTS.md` of every project that adopts the module.
5. Ask the `reviewer` to read the increment.
**Verification:** the module's tests pass (the new one failed first); the tests found in step 4 pass and the Result lists them; `wb check`
and `wb run code-work check` report no problem; `wb verify packages/workbench` reports no problem.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-verification-effort-guidance#C`.

### Increment D — Close out, documents and approvals

**Outcome:** the plan's result is written, the documents agree, and the shipped approvals are current.
**Dependencies:** A to C.
**Affected areas:** this plan's Result, the status line of `docs/specs/verification-effort.md`, the stale shipped approvals.
**Steps:**
1. Confirm that each increment's recorded verification still stands: no later increment changed the inputs of a check an earlier one
   passed. Rerun only what a later change invalidated, and say in the Result which that was.
2. With the owner's word, set the status of `verification-effort.md` to `Current`.
3. Run `wb check`, `wb run code-work check` and `wb verify packages/workbench`, and read each result.
4. List the stale shipped records with `wb preview release-approvals`, show the owner the exact list, and remove them through the commit
   helper only after the owner approves it.
5. Write the result of every increment under `## Result`, with the tests that ran, the ones that did not, and why that was enough.
**Verification:** the document checks and `wb verify` report no problem; the preview of the release reads `recorded` for the package and every
module.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-verification-effort-guidance#D`.

### Increment E — Record the upgrade

**Outcome:** the installed copies of the skills, the agent and the `AGENTS.md` policy match the package, and the manifest records them.
**Dependencies:** D.
**Affected areas:** `.workbench/manifest.json`, the installed skills and agent copies, and the policy block in `AGENTS.md`.
**Steps:**
1. The owner runs `wb upgrade` (and `wb acknowledge` if it asks). The agent shows the preview first, including the change to `AGENTS.md`.
2. Compare every installed file with its source in the package by hash and read `wb check`.
**Verification:** `wb check` reports no problem; every installed file has the hash of its source.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-verification-effort-guidance#E`.

## Verification for the plan as a whole

The module's tests once, after the last relevant change; `wb check`; `wb run code-work check`; `wb verify packages/workbench`;
`wb preview release-approvals` (every record `recorded`, none stale); and the hash comparison of increment E. Anything an earlier increment
passed on inputs that no later increment changed is not run again. The whole suite is not part of the plan's verification unless the owner
asks or an increment's risk calls for it; if one does, the agent recommends it with the reason and the owner decides.

## Risks and sensitive actions

- Agents may test too little. The mitigation is the named-reason rule, the owner's decision on each recommendation, the record of a declined
  one, and the reviewer. The owner may change the wording if under-testing shows up.
- Package changes run as scripted passes with the owner's word and a release. The hooks refuse other work during a pass, and the other
  session's plan makes passes of its own, so the two must not overlap.
- The policy line is rendered into the AGENTS.md of every project that adopts the module. The change reaches an adopter only when the
  owner of that project upgrades, and the upgrade preview shows it.
- No credential, authentication, parsing, network or subprocess change is made; the change is to text and to tests of text. No security
  exposure is identified. The reviewer is asked to flag any it can name.

## Review record

### Increment A

Reviewer: the `reviewer` agent (read-only). Rounds: 1 of 3. Outcome: no blocking findings; seven non-blocking findings.

- **Applied:** (1) the qualifier "ask again only if a later change alters how input reaches privileged use" is added to step 5 of
  `run-increment`; (2) the rule to use a documented way of selecting the affected tests is added to `test-first`; (4) the spec's
  acceptance criterion now says steps 4 and 5 of `run-increment`; (5) step 6 of `run-increment` now says to rerun the checks the fix
  affects.
- **Rejected:** (3) the reviewer did not read `test_codework_module.py`, which holds the runner and layout guard for `draft-plan` and its
  template; (6) "This skill names no language or runner" in `test-first` is existing wording, out of this plan's scope.
- **No action:** (7) the template's shorter wording is acceptable for a template.
- **Left for the owner:** nothing open. The second round was not asked for: the fixes are wording, pinned by tests that failed before
  and passed after.

## Deferred work

- An enforced checkpoint for a wider run, with levels, if the conversational stop proves too weak.
- A reviewer finding for a missed wider-testing risk, if agents are found to under-test in a way that cost the owner.
- A project test-table convention, a plan status for an accepted-but-unrun check, and rules in `code-work check`.

## Result

### Increment A

**Done, not committed:** the five texts (`test-first`, `verify-before-claiming`, `run-increment`, `draft-plan`, and the plan template) and the
three test files of `packages/workbench/code-work/`, in two scripted passes (the owner's word "run the pass" each time, and the owner's
`wb release-approvals` after each). A first pass wrote the guidance; the second applied review findings 1, 2 and 5. The spec
`docs/specs/verification-effort.md` has one correction (finding 4).

**Verification as run** (macOS, Python 3.15.0, `-I -B -W error`): the module's tests before any change: 340 ran, OK, 2 skipped. In each pass, the
new tests ran first against the old text and failed (first pass: 4 tests, all on a missing phrase; second pass: 2 tests, on the three new
phrases; no import or syntax error in either), then against the new text: 343 ran, OK, 2 skipped. After the second release the module's tests
were run again: 343 ran, OK, 2 skipped. `wb verify packages/workbench` listed all 13 modules and no refusal; `wb check` reported no problems;
`wb plan-status` still reads `approved`; `git status` shows only the 8 package paths and the spec changed.

**Not run, and why:** the whole suite and the tests of other modules. The repo-level search for tests that name these skills found two
(`mempalace` and `groundwork`), and each checks only that its own skill text does not name these skills, so no way for this change to break
them could be named. `wb run code-work check` was run after this record was written: 80 plans, no problems.

**Deviations and choices, for the owner:** (1) the two passes cost two releases; the second was for review findings. (2) Two new tests are
guards that pass before and after by design (the text names no tool, language or layout, and `run-increment` does not mention the whole
suite). A first version of one guard flagged the ordinary word "make", which the dry run caught; it now refuses only a command spelling.
(3) The plan's wording puts "stop and recommend" in step 4 of `run-increment`; the skill has it in a new step 5, so later steps are
renumbered, and no other file cites those numbers. (4) Two old phrases of `test-first` that pinned the text removed here were replaced in
`test_codework_practice.py`, for the stated reason. (5) The release printed two warnings about stale shipped records
(`670a75728168`, `67192317fbbb`); increment D removes them.
