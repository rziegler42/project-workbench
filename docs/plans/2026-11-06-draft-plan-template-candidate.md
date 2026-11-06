# Show both forms of the Candidate line in the plan template

Status: Proposed
Created: 2026-11-06
Candidate: none (deferred work of the plan `2026-11-06-roadmap-scope-text`, carrying out decision 6 of the accepted record `2026-11-06-roadmaps-are-scoped-by-finish-line` for the one shipped file that plan left out)
Specs: code-work

## Goal

An agent that copies the `draft-plan` template sees both forms of the `Candidate:` line, a named roadmap candidate and `none` with a one-line reason, and not only the named form. When the plan is done the
template shows both, the test that pins the template's header agrees, and a test fails if the template returns to the named form alone.

## Scope

- `harness/neutral/skills/draft-plan/template.md` in the `code-work` package: line 5, the `Candidate:` line.
- The test that pins the template's header (`test_codework_module.py`, `test_the_template_is_proposed_and_has_one_candidate_the_header_before_any_section`) and one new assertion that both forms appear.

## Non-goals

- The candidate-first wording elsewhere that the review of `2026-11-06-roadmap-scope-text` listed: the plans README introduction, the spec's flow lines near 52 to 59 and `files/blocks/policy.md` line 3. They read as the normal path and agree with decision 4.
- Any change to the plan check, which already accepts `Candidate: none` with a reason.
- The `draft-roadmap` template, which has no `Candidate:` line.
- Any change to what the skill or the READMEs say; they were changed by that plan.

## Assumptions and constraints

- A plan has exactly one `Candidate:` line, and the template keeps exactly one such line, before the first `##` heading, in its place after `Created:` and before `Specs:`.
- The line shows both forms in one line: `Candidate: <roadmap>#<id>, or none (a one-line reason)`. The wording is the agent's proposal; the forms are those of decision 4. A copied line that is left as it is fails the plan check, as the bare named form does now.
- The installed copy of the skill, its rendered copy under `.claude/skills/` and the tracked stored copy change only when the owner runs the upgrade and the rerender after the commit. The package is released separately, so the owner makes the release approvals and the copy.
- Nothing else in `docs/` holds a copy of the template. (To be confirmed when the work starts; a copy is reported and not changed.)

## Completion criteria

1. Line 5 of the template reads `Candidate: <roadmap>#<id>, or none (a one-line reason)` and the template has exactly one line that begins `Candidate:`.
2. The header test is updated to the new line and a test fails if either form is missing from that line.
3. The code-work module suite, the drift and rendering tests and `wb run code-work check` pass.

## Increments

### Increment A — Both forms in the template

**Outcome:** completion criteria 1 to 3 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/code-work/harness/neutral/skills/draft-plan/template.md`, `packages/workbench/code-work/tests/test_codework_module.py`.
**Steps:**
1. Write the test first: change the pinned header line in `test_the_template_is_proposed_and_has_one_candidate_the_header_before_any_section` to the new line, and assert that the line contains both `<roadmap>#<id>` and `none`.
   See it fail.
2. Edit line 5 of the template. Check that no other tracked file holds a copy of the line; report one if found.
3. Run the verification below and ask the `reviewer` for a read.
**Verification:** the code-work module tests (`test_codework_module.py`) and the rest of the code-work suite; `tests.test_rendering` and `tests.test_permissions_drift`, always, because the skill is rendered; `wb run code-work check`.
After the copy and the release, the upgrade and the rerender are the owner's. Not run: the whole suite (no code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-draft-plan-template-candidate#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether an agent writing a plan for a small correction chooses `none` is for a live run, which this plan does not run.

## Risks and sensitive actions

- The template is read by agents in every project that installs the package; a line that is unclear could make an agent keep both forms. The plan check refuses that, so the failure is loud and safe.
- A package file changes, so the release approvals, the upgrade and the rerender are the owner's; nothing is pushed.
- No secret, no code that reads input, no filesystem write by code and no network is touched. A security review is not suggested.

## Review record

Empty until a review is asked for.

## Deferred work

- The candidate-first wording listed under the non-goals, if the owner wants it changed.
- A live run of an agent drafting a plan for a small correction.

## Result

Empty until work starts.

**Increment A (2026-11-06), done in a scratch clone at commit `a9a4c98`; not yet copied, released or committed.**

- Built: line 5 of the `draft-plan` template reads `Candidate: <roadmap>#<id>, or none (a one-line reason)`, both forms of decision 4 in one line, and the template still has exactly one `Candidate:` line before
  `Specs:`. The header test now pins that line and asserts that both `<roadmap>#<id>` and `, or none (a one-line reason)` are in it. Two files changed in the clone: the template and `test_codework_module.py`.
- Verification as run: the header test failed before the template edit (the one failure; two errors in that file came from running it by dotted name and do not occur under discovery) and passes after; the code-work
  suite in the clone gave 352 tests, all passing (2 skipped, as before); `tests.test_permissions_drift` and `tests.test_rendering` (107) pass. A search of the live tree for the template line found it only in the template,
  its stored copy under `.workbench/` and its rendered copy under `.claude/skills/` (both refreshed by the upgrade and the rerender), and in documents that phrase it differently (the plans README, the code-work spec, the
  earlier plan and the test). `wb run code-work check` passes in the live tree (102 plans, run before this Result was written). Not run: the whole suite (no code changed); an agent following the text (a live run).
- Review: the `reviewer` agent, one exchange, no finding. It read the helper and found that a copied line left as it is fails the plan check (the value starts with `<`, so neither the named form nor `none` matches), which is
  the loud, safe failure the plan wants. The reviewer ran nothing.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/tp_install_files.py`, two files, only if their hashes are those recorded), the release approvals, the removal of the stale records
  after you approve the list, then "commit a"; after the commit the upgrade and the rerender (the stored and rendered copies of the template change). No project-owned copy of the template exists to match.
