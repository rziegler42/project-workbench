# Make the code-work spec's lifecycle allow a plan with no candidate

Status: Proposed
Created: 2026-11-06
Candidate: none (a correction that follows from a finding: the spec's purpose and lifecycle text reads as if every plan starts from a roadmap candidate, while `docs/plans/README.md` and decision 4 of the accepted record `2026-11-06-roadmaps-are-scoped-by-finish-line` allow `Candidate: none`)
Specs: code-work

## Goal

The code-work spec says in its purpose paragraph and in its lifecycle section what the plans README and the accepted record already say: a plan comes from a roadmap candidate, or, for work too small to need roadmap direction, names `Candidate: none` with a one-line reason. When the plan is done the two passages of the spec say so, and a test fails if either passage returns to the candidate-only reading.

## Scope

- `docs/specs/code-work.md`: the second sentence of "Purpose and scope" (lines 15 to 19), and the paragraph under "Lifecycle" (lines 55 to 60). The diagram line (line 52) stays as the normal path.
- `packages/workbench/code-work/tests/test_codework_candidate_text.py`: one new test that pins the two passages.

## Non-goals

- `packages/workbench/code-work/files/blocks/policy.md` line 3 and the matching line 47 of `AGENTS.md`: a shipped package file and its installed copy. Changing them needs a release, an upgrade and a rerender. They read as the normal path and agree with decision 4.
- The plans README, the skills and the template, which the earlier plans changed.
- The plan check, which already accepts `Candidate: none` with a reason.
- Any change to what the lifecycle is: the order of the steps, the review and the archive are unchanged.

## Assumptions and constraints

- The spec is a living document edited in place. A spec edit is not a package change, so there is no release, upgrade or rerender, and the test reads the spec from the repository as the earlier test does.
- The wording is the agent's proposal. The rule is decision 4 and `docs/plans/README.md` Content item 2; the passages cite them in effect and do not copy them in full.
- The diagram stays a single line: the normal path through a roadmap. The paragraph carries the exception.

## Completion criteria

1. "Purpose and scope" says a unit of work moves from a roadmap candidate, or from work too small to need roadmap direction, to a verified, reviewed, committed result.
2. The "Lifecycle" paragraph says a plan is drafted for a chosen candidate, and that a correction too small to need roadmap direction goes straight to a plan that names `Candidate: none` with a one-line reason, with no roadmap edit.
3. The new test fails against the present spec and passes after the edit, and the other tests of that file still pass.
4. `wb run code-work check` passes.

## Increments

### Increment A — The two spec passages

**Outcome:** completion criteria 1 to 4 are true.
**Dependencies:** none.
**Affected areas:** `docs/specs/code-work.md`, `packages/workbench/code-work/tests/test_codework_candidate_text.py`.
**Steps:**
1. Write the test first: in `test_codework_candidate_text.py`, one test that reads the spec and asserts that the purpose paragraph contains `too small to need roadmap direction` and that the text under "Lifecycle" contains `Candidate: none` and `too small to need roadmap direction`. See it fail.
2. Edit the two passages of the spec. Leave the diagram line as it is.
3. Search the repository for another copy of the two passages; report one if found and do not change it.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_codework_candidate_text.py` and the rest of the code-work suite; `wb run code-work check`. Not run: `tests.test_rendering` and `tests.test_permissions_drift` (no skill, template or shipped file changes) and the whole suite (no code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-spec-lifecycle-allows-no-candidate#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether an agent follows the text is for a live run; the run of 2026-11-06 showed it did for a small correction.

## Risks and sensitive actions

- A spec is an authority below the owner's instruction and the accepted decisions; the edit only brings it into agreement with them, so the risk is a wording that says more than decision 4. The reviewer reads for that.
- Nothing shipped changes, nothing is pushed, and no secret, input parsing, filesystem write by code or network is touched. A security review is not suggested.

## Review record

Empty until a review is asked for.

## Deferred work

- `files/blocks/policy.md` line 3 and `AGENTS.md` line 47, until a package release is made for another reason or the owner asks for one.

## Result

Empty until work starts.
