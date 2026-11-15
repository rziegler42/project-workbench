# Raise the plan byte budget

Status: Proposed
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
Empty until a review is asked for.

## Deferred work
None.

## Result
Empty until work starts.
