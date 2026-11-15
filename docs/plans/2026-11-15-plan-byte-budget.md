# Raise the plan byte budget

Status: Completed
Created: 2026-11-15
Candidate: none (a fix that follows from a finding: plans reached the 4 MiB budget)
Specs: none

## Goal
The code-work helper reads plans under 16 MiB, so a new plan is read whole.

## Scope
`MAX_BYTES` in the helper, its test, and the installed copy.

## Non-goals
The per-file bound, the file count, the doccheck budget.

## Assumptions and constraints
The owner chose 16 MiB. The gate runs the installed copy. A package edit is one scripted pass.

## Completion criteria
1. `MAX_BYTES` is 16 MiB in the helper and the installed copy.
2. A plan over 2 KB passes `wb run code-work check`.

## Increments

### Increment A — Raise the budget
**Outcome:** the helper's budget is 16 MiB.
**Dependencies:** none.
**Affected areas:** the helper, `test_codework_helper.py`.
**Steps:**
1. Make the total-bytes test follow the constants, add a test pinning 16 MiB; see them fail.
2. Set `MAX_BYTES`.
**Verification:** the code-work tests.
**Evidence:** one commit, trailer `Plan: 2026-11-15-plan-byte-budget#A`.

### Increment B — Update the installed copy
**Outcome:** the installed helper has the new budget.
**Dependencies:** A.
**Affected areas:** `.workbench/`, `AGENTS.md`.
**Steps:**
1. The owner runs the upgrade preview and upgrade; I read `wb run code-work check`.
**Verification:** `wb verify`, `wb check`.
**Evidence:** one commit, trailer `#B`.

## Verification for the plan as a whole
A and B as run.

## Risks and sensitive actions
The edit gate reads up to 16 MiB per edit: slower, not looser.

## Review record
Increment A: the `reviewer` agent, one exchange, read-only. No blocking finding; it found no other use of `MAX_BYTES` and no document that states the old budget, and named no security risk.
- Applied: the worst-case memory of the plan read rises from about 4 MiB to about 16 MiB (`collect` keeps each file's bytes). The Risks section names only the edit gate's read time, and it is in the approved region, so the memory point is recorded here in the Result.
- Rejected: the "still read" test only asserts that "not looked at" is absent, and the reviewer could not see where that text goes. It failed against the old helper (see the Result), so the text does reach stderr and the test fails for the right reason. Rejected: the test name has "4_mib" in it; cosmetic.
- Not reviewed: increment B, which writes the installed copy through the installer's own preview and digest.

## Deferred work
None.

## Result
Increment A is committed as `657495a` (trailer `#A`; 4 paths, the release record `8e879356…` included). Increment B is committed with the plan's completion (trailer `#B`; 3 paths).

**Increment A.** `MAX_BYTES` in `packages/workbench/code-work/helper/code-work` is `16 * 1024 * 1024` (was 4 MiB). In `test_codework_helper.py` the total-bytes test now writes `MAX_BYTES // MAX_DOCUMENT + 2` files, and two tests were added: one pins 16 MiB, one writes five 900 KiB plans and a small last plan and expects no "not looked at" on stderr. Test-first, run as one scripted pass (Python 3, Darwin): both new tests failed against the old helper (`16777216 != 4194304`; the last plan not looked at), then passed after the change. `test_codework_helper.py`: 56 tests OK (2 skipped). The code-work directory: 369 tests OK (2 skipped), 0 ResourceWarning lines, no stray caches under `packages/`. Not run: the whole suite, and tests outside code-work (nothing outside the helper and its test changed).

**Increment B.** The owner released the package lock after A. I ran `wb preview upgrade --package packages/workbench` (digest `a058c86d…`): 2 file writes (the installed helper and `.workbench/manifest.json`), 2 store writes (the baselines and the pin of `code-work`), 76 skips, and one conflict that was not touched (`README.md`, which the manifest never recorded). I then ran `wb upgrade --package packages/workbench --digest a058c86d…`, which applied it ("wrote 2 paths"). Read afterwards: `.workbench/workbench/code-work/helper/code-work` line 42 reads `MAX_BYTES = 16 * 1024 * 1024`; `wb run code-work check` reports 122 plans, no problems; `wb check` reports no problems; `wb verify packages/workbench` ran.

**Completion criteria.** (1) Met: 16 MiB in the helper and in the installed copy. (2) Met by the plan itself: before B this plan had about 260 bytes of room and could hold no review record; after B this Review record and Result, together far over 2 KB, are in it and the check reports no problems.

**Things to know.** (a) Memory: `collect` holds each plan's bytes, so a run now holds up to about 16 MiB, not 4 MiB (the plans total about 4.2 MB today). Not named in the Risks section, which is in the approved region. (b) The review record and this Result were written after B, at the owner's word ("commit a, write the record after b"), because the plan could not hold them before; A was committed with only its status change in the plan. (c) The installer left a second release record, `workbench/shipped_approvals/packages/d1141101…`, untracked; deleting it needs the owner's approval of the list. (d) The groundwork `doccheck` has its own 4 MiB budget; it is a non-goal here and its documents are far below it.
