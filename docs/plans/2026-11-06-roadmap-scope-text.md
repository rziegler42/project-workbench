# Say how work is placed in roadmaps, and when a plan needs no candidate

Status: Completed
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

**Increment A (2026-11-06), done in a scratch clone at commit `bbeb0c3`; not yet copied, released or committed.**

- Built: step 1 of the `draft-roadmap` skill now defines a scope (a body of work with its own finish line, which the owner can call finished or pause), asks whether the new candidate
  shares the finish line of the roadmap it would join, adds it if so, otherwise proposes a new roadmap to the owner with its scope and finish line and writes nothing until the owner accepts or
  renames it, never adds to the nearest roadmap because it is nearest, says what a candidate is and that work too small to need roadmap direction is a plan with `Candidate: none`, and asks the
  owner at about 15 candidates whether the roadmap has outgrown its scope (a question, not a limit). Step 2 now applies to a new roadmap the owner has accepted. The shipped roadmaps README
  gains a paragraph with the same content, and its Retiring sentence says each roadmap has its own finish line. `docs/specs/groundwork.md` gains a bullet with the same content, citing the decision,
  and the same words in its retiring bullet. "used alternately" is gone from the spec. Four files changed in the clone: the skill, the README, the spec and a new test file
  (`tests/test_groundwork_roadmap_scope.py`, six tests).
- Verification as run: the six new tests failed before the text and pass after; the groundwork module suite in the clone gave 258 tests, all passing; `tests.test_permissions_drift` and
  `tests.test_rendering` (107) pass; `wb run code-work check` in the live tree passes (100 plans). Not run: the whole suite (no code changed); an agent following the text (a live run).
- Review: the `reviewer` agent, one exchange, no blocking finding. Applied: the tests now pin the placement, owner-gate, nearest-roadmap, candidate and size sentences in each of the three places
  and the skill-only steps, and a wider list of "exactly one roadmap" phrases; the Retiring sentences name the finish line (step 3 of this increment); steps 2 and 3 of the skill now apply only
  to an accepted new roadmap. Not changed: the reviewer's note that "Candidate: none" appears here though increment B owns the `draft-plan` side (it is what decision 4 says, and B must match it);
  the older rule in the skill that a roadmap changes only when direction changes and needs the owner's ask, which sits beside "add it there" for a shared finish line. That rule is older than this plan; it is
  reported to the owner and not changed. The reviewer ran nothing.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/rs_install_files.py`, four files, only if their hashes are those recorded), the release approvals, the removal of the stale records
  after you approve the list, then "commit a"; after the commit the upgrade and the rerender (the shipped README and the skill are installed from the package).

**Increment B (2026-11-06), done in a scratch clone at commit `39be69a`; not yet copied, released or committed.**

- Built: the `Candidate:` item of the plans README, step 4 of the `draft-plan` skill and the `Candidate:` item of `docs/specs/code-work.md` now say that a plan names `<roadmap>#<id>` for bounded new work that
  advances the finish line of a roadmap, and `Candidate: none` with a one-line reason for work too small to need roadmap direction, such as a correction that follows from a finding; "exactly one" is kept.
  Step 1 of the skill reads the roadmap that holds the candidate only when the plan names a candidate, and step 4 searches the roadmap so the ID exists "for a named candidate". Four files changed in the clone:
  the README, the skill, the spec and a new test file (`tests/test_codework_candidate_text.py`, five tests).
- Verification as run: before the text 2 of the first 4 tests failed (the others pin text kept); afterwards the five tests pass; the code-work module suite in the clone gave 352 tests, all passing (2 skipped,
  as before); `tests.test_permissions_drift` and `tests.test_rendering` (107) pass; `wb run code-work check` in the live tree passes. Not run: the whole suite (no code changed); an agent following the text (a live run).
- Review: the `reviewer` agent, one exchange, no blocking finding. Applied: the tests pin the exact no-candidate form in each place, "exactly one `Candidate:` line" in the skill, and the search sentence with
  "for a named candidate". Not applied, for the owner: `template.md` of the skill still shows only `Candidate: <roadmap>#<id>` (it is outside this plan's affected areas, and the non-goals bar rewording
  elsewhere, so a change needs a new approval); candidate-first wording that remains (the plans README introduction, the spec's flow lines 52 to 59, and `files/blocks/policy.md` line 3 "Work moves from a roadmap
  candidate to a plan"), which reads as the normal path and agrees with decision 4; the risk that "too small" is read loosely, which the record accepts as a judgment for the first uses to test. The reviewer ran nothing.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/rb_install_files.py`, four files, only if their hashes are those recorded), the release approvals, the removal of the stale records
  after you approve the list, then "commit b"; after the commit the upgrade and the rerender. The upgrade does not replace the project's own `docs/plans/README.md`; after it I compare that file with the package copy and, with
  your word, match it as was done for the roadmaps README.
