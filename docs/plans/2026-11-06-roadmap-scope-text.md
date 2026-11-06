# Say how work is placed in roadmaps, and when a plan needs no candidate

Status: Proposed
Created: 2026-11-06
Candidate: none (decision 6 of the accepted record `2026-11-06-roadmaps-are-scoped-by-finish-line`, a text change with no roadmap of its own)
Specs: groundwork, code-work

## Goal

An agent that drafts a roadmap or a plan is told what a scope is, how to place new work (an existing roadmap, a new scoped roadmap, or no candidate), and when to ask the owner
about the size of a roadmap. When the plan is done the shipped skills, READMEs and specs say what the accepted record decides, and tests pin each sentence.

## Scope

- Groundwork package: the `draft-roadmap` skill (step 1 and the rule on a new roadmap), the shipped `docs/roadmaps/README.md` (Naming and Retiring a roadmap) and `docs/specs/groundwork.md`
  (the roadmap bullet near line 75).
- Code-work package: the shipped `docs/plans/README.md` (the `Candidate:` item), the `draft-plan` skill (steps 1 and 4) and `docs/specs/code-work.md` (the `Candidate:` item near line 81).
- The tests that pin guidance text in those two packages.

## Non-goals

- Splitting, rewriting or annotating `workbench-v1`, or moving a candidate (decision 5 of the record).
- Any change to the plan check, the document check, or code that reads a `Candidate:` line. `Candidate: none` with a reason already passes.
- A hard cap on candidates, a list of scopes, or several active roadmaps on one scope (rejected in the record).
- Reordering or rewording anything else in these files.

## Assumptions and constraints

- The record decides the content: a scope is a body of work with its own finish line; new work is placed by asking whether it shares the finish line of the roadmap it would join;
  a new roadmap is proposed with its scope and finish line and written only after the owner accepts or renames it; past about 15 candidates the agent asks whether the roadmap has
  outgrown its scope, and the owner may say to go on; a candidate is bounded new work that advances a roadmap's finish line; `Candidate: none` is for work too small to need roadmap direction.
- The shipped `docs/roadmaps/README.md` and `docs/plans/README.md` are package files; the tracked copies in `docs/` and in `.workbench/` change only when the owner runs the upgrade
  and the rerender after the commit.
- The skill `draft-roadmap` may not run commands and may not add to a roadmap on its own; it asks for the owner where the text says so. The text keeps that.
- The shipped READMEs and skills are read by agents in other projects; the sentences use no word that belongs to this project.
- The two packages are released separately, so each increment has its own release approvals.

## Completion criteria

1. The `draft-roadmap` skill, the shipped roadmaps README and `groundwork.md` say what a scope is, the placement test, that a new roadmap is proposed to the owner with its scope and
   finish line, and the size prompt at about 15 candidates (a prompt, not a cap).
2. The shipped plans README, the `draft-plan` skill and `code-work.md` say when `Candidate: none` applies (work too small to need roadmap direction, such as a correction that follows
   from a finding) and when a candidate is right (bounded new work that advances a roadmap's finish line). Step 1 of the skill asks for the roadmap that holds the candidate only
   when the plan names a `<roadmap>#<id>` candidate.
3. No sentence says or implies that new work is added to the nearest or only roadmap by default, and none says there is exactly one roadmap.
4. Tests pin each new sentence, in the skill, the shipped README and the spec, and fail if one is removed.
5. The module suites of both packages, the drift and rendering tests and `wb run code-work check` pass.

## Increments

### Increment A — Roadmap placement in the groundwork package

**Outcome:** completion criterion 1 is true, with tests.
**Dependencies:** none.
**Affected areas:** `packages/workbench/groundwork/harness/neutral/skills/draft-roadmap/SKILL.md`, `packages/workbench/groundwork/files/docs/roadmaps/README.md`,
`packages/workbench/groundwork/tests/test_groundwork_module.py` (or a new guidance test file beside it), `docs/specs/groundwork.md`.
**Steps:**
1. Write the tests first: each sentence of criterion 1 is present once in the skill, the README and `docs/specs/groundwork.md` (the test reads the spec from the repository root), and the skill no longer says only "add to it instead of writing a second" without
   the placement test. See them fail.
2. Edit step 1 of the skill: search for roadmaps; ask whether the candidate shares the finish line of the roadmap it would join; add if so; otherwise propose a new roadmap to the owner
   with its scope and finish line and write nothing until the owner accepts or renames it; past about 15 candidates ask whether the roadmap has outgrown its scope before adding another.
3. Edit the README (Naming: what a scope is; Retiring: the one-non-archived-roadmap-per-scope sentence stays, with the finish line named) and the spec bullet to match.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** the groundwork module tests; `tests.test_rendering` and `tests.test_permissions_drift`, always, because skills and shipped files are rendered and checked for drift;
`wb run code-work check`. After the copy and the release, the upgrade and the rerender are the owner's. Not run: the whole suite (no code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-roadmap-scope-text#A`.

### Increment B — When a plan has no candidate, in the code-work package

**Outcome:** completion criteria 2 and 3 are true, with tests.
**Dependencies:** A (the plans text points at the roadmap placement it states).
**Affected areas:** `packages/workbench/code-work/files/docs/plans/README.md`, `packages/workbench/code-work/harness/neutral/skills/draft-plan/SKILL.md`,
`packages/workbench/code-work/tests/test_codework_practice.py` (or a guidance test beside it), `docs/specs/code-work.md`.
**Steps:**
1. Write the tests first: the `Candidate:` item in the README, step 4 of the skill and the `Candidate:` item of `docs/specs/code-work.md` (read from the repository root) state when `Candidate: none` applies and
   when a candidate is right, and step 1 of the skill asks for the roadmap only when the plan names `<roadmap>#<id>`. See them fail.
2. Edit the README item, steps 1 and 4 of the skill and the spec item: `<roadmap>#<id>` for bounded new work that advances a roadmap's finish line; `none` with a one-line reason for work too
   small to need roadmap direction, such as a correction that follows from a finding. Keep "exactly one" and "search the roadmap so the candidate ID exists" (the latter for a named candidate). In step 1, read the roadmap that holds the candidate only for a named candidate.
3. Run the verification below and ask the `reviewer` for a read.
**Verification:** the code-work practice tests and the plan-check tests; the code-work module suite; `tests.test_rendering` and `tests.test_permissions_drift`, always; `wb run code-work check`. After the copy and the release, the upgrade and the
rerender are the owner's. Not run: the whole suite (no code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-roadmap-scope-text#B`.

## Verification for the plan as a whole

Each increment's recorded verification stands. After both, `wb run code-work check` is rerun for the plan; the drift and rendering tests were run in each increment and are not rerun unless a later change touched their inputs. Whether an agent follows the text (it proposes a new roadmap for new work with
a different finish line, and uses `Candidate: none` for a small correction) is for a live run, which this plan does not run.

## Risks and sensitive actions

- The skills and READMEs are read by agents in every project that installs these packages; a vague sentence could make an agent create roadmaps too readily. The record keeps the owner's
  acceptance of a new roadmap, and the text keeps it.
- An agent that reads "past about 15 candidates" as a rule may stop adding candidates; the text says it is a question to the owner.
- Package files change, so the release approvals, the upgrade and the rerender are the owner's; nothing is pushed.
- No secret, no code that reads input, no filesystem write by code and no network is touched. A security review is not suggested.

## Review record

Empty until a review is asked for.

## Deferred work

- A note on `workbench-v1` that new work is scoped from here on (decision 5 of the record leaves it to the owner).
- A live run of an agent placing a new candidate.
- Status clauses on older accepted records if any are found to conflict. None is known.

## Result

Empty until work starts.
