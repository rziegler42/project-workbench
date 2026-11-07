# Make the code-work spec's lifecycle allow a plan with no candidate

Status: Completed
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

Codex (`gpt-5.6-terra`), plan review, 1 round of 3, converged with no meaningful finding; nothing to decide.

Increment A: the `reviewer` agent, one exchange, no blocking finding. Applied: the last sentence of the Lifecycle paragraph said the candidate is reported complete, which assumes every plan has one; it now begins "When the plan names a candidate". Applied: the re-wrapped purpose line was about 130 characters; it is wrapped again. The reviewer found the new wording says neither more nor less than decision 4 and the test not brittle. Not checked by the reviewer: the test runs and the repository-wide search (it ran nothing); both were run by me.

## Deferred work

- `files/blocks/policy.md` line 3 and `AGENTS.md` line 47, until a package release is made for another reason or the owner asks for one.

## Result

**Increment A (2026-11-06), done in a scratch clone at commit `0e16756`; copied and committed as `fc4ffcc`.**

- Built: the purpose paragraph of `docs/specs/code-work.md` says a unit of work moves from a roadmap candidate, or from work too small to need roadmap direction, to a verified, reviewed, committed result. The Lifecycle paragraph says such work, such as a correction that follows from a finding, goes straight to a plan naming `Candidate: none` with a one-line reason, with no roadmap edited, and that the candidate is reported complete only when the plan names one. The diagram line is unchanged. One new test in `test_codework_candidate_text.py` slices the purpose and lifecycle passages and pins `too small to need roadmap direction` in both and `Candidate: none` in the lifecycle.
- Verification as run: the new test failed before the spec edit and passes after; the code-work suite in the clone, run with `python3 -B -m unittest discover`, gave 353 tests, all passing (2 skipped, as before). A first run without `-B` wrote a `__pycache__` that made two module tests fail and made the project's command hook refuse every Bash call; the owner removed it, and the rerun is the one recorded. After the review edit the candidate-text file was run again (6 tests, OK); the whole suite was not rerun after that edit, which touches only the spec's wording. `wb run code-work check` passes (103 plans). A search of `docs/specs` found no other copy of the purpose wording. Not run: `tests.test_rendering` and `tests.test_permissions_drift` (no skill, template or shipped file changed) and the whole repository suite.
- Review: Codex on the plan, one round, no finding; the `reviewer` agent on the increment, two non-blocking findings, both applied.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/sl_install_files.py`, two files, only if their hashes are those recorded), then "commit a". The test file is under `packages/`, so run `wb preview release-approvals` after the copy to see whether the release asks for anything. The deferred wording in `policy.md` and `AGENTS.md` is untouched.
