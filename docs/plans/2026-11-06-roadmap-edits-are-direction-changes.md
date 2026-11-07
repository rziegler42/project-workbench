# Say, in every shipped text, that a change to a roadmap is a change of direction and waits for the owner

Status: Proposed
Created: 2026-11-06
Candidate: none (a correction that follows from a finding: the shipped roadmap text says an agent adds a candidate when the finish line is shared, and also that a roadmap changes only when direction changes and that changing direction needs the owner, and it never says whether adding a candidate is such a change)
Specs: groundwork, code-work

## Goal

The shipped text answers one question the same way in every place: who writes a change to a roadmap. After this plan every place that tells an agent how to place a new candidate says that the agent runs the placement test and shows the owner the candidate it would add, and writes it only on the owner's word, because any change to a roadmap other than correcting a typo is the `change-direction` checkpoint, which always stops (it offers `block` only). The owner's request to add a candidate ("add that as a candidate") is that word. No shipped text still says an agent adds a candidate, or records work "in a roadmap", on its own, and a test fails if one of those sentences returns anywhere in the shipped set.

The finding is in the skill itself. `draft-roadmap` step 1 says "If it does, add it there", and the same skill's rules say "The file changes only when direction changes, and changing direction needs the owner. Stop and ask before doing it." The roadmaps README and the groundwork spec say both too. The accepted record `2026-11-06-roadmaps-are-scoped-by-finish-line` decides where a candidate goes (decision 2: "it is added to that roadmap as a candidate") and lists only creating or replacing a roadmap as a change of direction. The record is not rewritten: increment A adds the dated clarification that the project's rule for an accepted record allows (`draft-decision`: "A narrow clarification of an accepted record needs the owner's approval and is a dated note after the unchanged body"), and the owner's approval of this plan, which holds the note's exact words, is that approval.

## Scope

- Increment A: a dated clarification note after the unchanged body of `docs/decisions/2026-11-06-roadmaps-are-scoped-by-finish-line.md`.
- Increment B, the `groundwork` module text: `harness/neutral/skills/draft-roadmap/SKILL.md` (the description, step 1, step 6 and the rules), `files/docs/roadmaps/README.md`, and one new sentence in `files/blocks/policy.md`; the test `tests/test_groundwork_roadmap_scope.py`; and `docs/specs/groundwork.md` (the roadmap bullets and the checkpoint table).
- Increment C, the `code-work` module text: `files/docs/plans/README.md` (the out-of-scope sentence and the checkpoint sentence) and `files/blocks/policy.md` line 3; the test `tests/test_codework_candidate_text.py`; and `docs/specs/code-work.md` (the same two sentences).
- Increment D: this repository's own seeded copies of the two READMEs, after the owner's upgrade and rerender of B and C, and a check of the regenerated root `AGENTS.md`.

**Audit of the shipped text (2026-11-06).** Lens: every statement about who may change a roadmap or a spec's direction, where a candidate is placed, and the `change-direction` checkpoint. Method: the 82 shipped markdown files of the base and the 13 modules (skills, agents, templates, READMEs, policy blocks, doc-index blocks; not tests) were searched for `roadmap`, `candidate`, `direction`, `checkpoint`, `add to`, `add it`, `in place`, `stop and ask` and `needs the owner`; every hit was read in its paragraph, and `draft-roadmap`, both policy blocks, the roadmaps README and the plans README were read whole. The `freecad` and `verilog` skills (about 40 files) hold no roadmap text; their word "direction" is geometric. Not audited: any other kind of conflict between shipped rules.

| Shipped place | What it says | Finding | Action |
|---|---|---|---|
| `draft-roadmap/SKILL.md`, description (line 3) | "…or add a candidate to one" | invites a write, no owner step | B: reword |
| same, step 1 (line 14) | "If it does, add it there." | contradicts the rules below | B: reword |
| same, step 6 | "Mark an abandoned candidate as dropped" | a direction change with no owner step | B: add the owner's word |
| same, rules (lines 44 and 45) | "changes only when direction changes… Stop and ask" | right, but does not say that a candidate is such a change | B: define |
| `groundwork/files/docs/roadmaps/README.md`, lines 13 to 15 and 39 to 40 | "is added to it as a candidate"; "changing direction needs the owner" | same tension | B: reword and define |
| same, line 46 | "update it in place" | an unqualified write | B: add the owner's word |
| `groundwork/files/blocks/policy.md` | names only the `accept-decision` checkpoint | gap: the always-loaded policy never names `change-direction` | B: one sentence |
| `groundwork/files/docs/specs/README.md` line 24; `draft-spec/SKILL.md` line 26 | "Changing what a spec says about direction needs the owner" | consistent | none |
| `draft-decision`, `brainstorm`, the three templates, `docs-index` blocks, `decisions` and `references` READMEs | no roadmap-editing text | clean | none |
| `code-work/files/docs/plans/README.md` line 88 | "record out-of-scope work as deferred or in a roadmap" | tells an agent to write a roadmap | C: reword |
| same, lines 92 to 94 | checkpoint list names "a spec's or roadmap's direction" | does not say a candidate counts | C: add the clause |
| `code-work/files/blocks/policy.md` line 3 | "Work moves from a roadmap candidate to a plan" | candidate-first, against decision 4 | C: reword |
| `draft-plan` skill and template; `run-increment`, `delegate-approval` | `Candidate: none` forms; "a roadmap does not authorize work" | consistent | none |
| `code-work/module.json`; `workbench/levels.py` | declare `change-direction`; offer `block` only | not text; confirms the checkpoint cannot be loosened | none |
| `mempalace` policy line 3 and `recall-memory` lines 9 and 88 | "draft a roadmap candidate" (search first) | compatible: draft means propose | none |
| `peer-review`; `reviewer.md`; `security-reviewer.md`; `rubric.md` | `review-roadmap` only; no roadmap text | clean | none |
| `base/README.md`, `base/AGENTS.md`, `base/docs/README.md` | no roadmap text | clean (the root `AGENTS.md` follows by rerender) | none |
| `safe-git`, `remote-runner`, `security-review`, `freecad`, `verilog` skills | no roadmap text | clean | none |
| `docs/specs/groundwork.md` lines 73, 95, 106 to 110, 246 to 251; `docs/specs/code-work.md` line 131 | restate the same sentences | specs, edited in place | B and C: edit |
| `docs/decisions/2026-11-06-roadmaps-are-scoped-by-finish-line.md`, decision 2 | "it is added to that roadmap as a candidate" | says where, not who writes | A: dated note |

## Non-goals

- The checkpoint itself: its level (`block` only), its place in `module.json` and `levels.py`, and any mechanical enforcement. The groundwork spec already says the checkpoint is enforced by instruction, because a typo and a direction change cannot be told apart by the harness.
- The body of the accepted record, which stays as written; only a dated note is added after it, and the record's status line and the decisions index do not change.
- The placement test, the 15-candidate prompt and `Candidate: none`, which stay as the record decides.
- `workbench-v1` and every other project document (plans, roadmaps, other decisions). Only the two READMEs that were seeded from the modules are matched, in D.
- Any other conflict between shipped rules, which the audit did not look for.

## Assumptions and constraints

- The reading is the agent's proposal and the owner's to confirm by approving this plan: in the groundwork spec, "the roadmap file changes only when direction changes" (line 110) together with the `change-direction` checkpoint (line 251) means any edit of a roadmap other than a typo is a direction change, and decision 2 settles where a candidate goes without saying who writes it. The alternative, that adding a candidate that passes the placement test is routine and only creating, dropping or retiring is a direction change, is consistent with the decision's wording but not with the skill's own rule, and it would let an agent grow a roadmap without the owner. The owner's own practice in this project (the request "add that as a candidate") fits the first reading.
- The note of increment A reads, in full: "*Clarified 2026-11-06, with the owner's approval of the plan `2026-11-06-roadmap-edits-are-direction-changes`:* Decision 2 says where a candidate goes. Adding a candidate to a roadmap, like any change to a roadmap other than correcting a typo, is a change of direction and the `change-direction` checkpoint, which always stops for the owner. The agent runs the placement test, shows the owner the candidate it would add, and writes it on the owner's word; the owner's request to add a candidate is that word. The proposal of a new roadmap, and the rest of this record, stand as written."
- The sentence for the policy block is the agent's proposal: "A change to what a spec says about direction, and any change to a roadmap other than correcting a typo (adding, dropping or rewording a candidate, changing a roadmap's purpose, scope or status, or creating, retiring or replacing a roadmap), is the `change-direction` checkpoint and always stops for the owner. Do the placement test, show the owner the candidate you would add, and write it only on the owner's word; the owner's request to add a candidate is that word."
- The `draft-roadmap` skill, the roadmaps README and the groundwork policy block ship with `groundwork`, and the plans README and its policy block with `code-work`, so the text reaches an installed project only after a release, an upgrade and a rerender, which are the owner's. The root `AGENTS.md` and `.claude/skills/` are generated by those steps; the agent does not edit them, and the install-state commit after each of B and C carries the regenerated `AGENTS.md`.
- The specs are read by tests as one of the places the sentences must appear, so each spec is edited in the increment whose test reads it.
- The tests that guard the old sentences walk the whole shipped set (every markdown file under `base/` and `packages/` outside `tests/`) and both specs, not only the named files, so a later occurrence anywhere fails.
- Each increment is made and tested in a scratch clone and copied by the owner's script, with the files' hashes recorded; tests run with `python3 -B`.

## Completion criteria

1. Decision 2's record holds the dated note of increment A after its unchanged body, and its status and the index are unchanged.
2. The rule is stated in the groundwork policy block, in the `draft-roadmap` skill (description, step 1, step 6 and the rules) and in the roadmaps README, and says: what counts, that the checkpoint always stops, that the agent proposes the candidate and writes it on the owner's word, that the owner's request to add one is that word, and that a typo is not a change.
3. The sentences "If it does, add it there", "is added to it as a candidate" and "or in a roadmap" appear in no shipped markdown file and in neither spec, and the code-work policy block's first work sentence no longer says work starts only from a candidate. Two tests that walk the shipped set and both specs fail if any returns, and the placement test, the 15-candidate prompt and `Candidate: none` are still said where they were.
4. The audit table above is true of the tree when the plan is done: every row's action is carried out and no row marked "none" has changed.
5. The groundwork and code-work module tests, `tests.test_rendering` and `tests.test_permissions_drift` pass, and `wb run code-work check` passes.
6. After the owner's upgrade and rerender, this repository's `docs/roadmaps/README.md` and `docs/plans/README.md` match the shipped files, and the regenerated root `AGENTS.md` holds the new policy sentences.

## Increments

### Increment A — The clarification note on decision 2

**Outcome:** completion criterion 1 is true.
**Dependencies:** the owner's approval of this plan, which holds the note's words.
**Affected areas:** `docs/decisions/2026-11-06-roadmaps-are-scoped-by-finish-line.md`.
**Steps:**
1. Add the note of "Assumptions and constraints", verbatim, as a paragraph after the last section of the record, leaving every earlier line as it is.
2. Check that the record's body is unchanged (`git diff` shows only added lines at the end) and that its status line and the row of `docs/decisions/README.md` are untouched.
3. Ask the `reviewer` for a read.
**Verification:** `git diff` of the record; `wb run code-work check`; the groundwork document check as `wb check` reports it. Not run: any test suite (no code or shipped file changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-roadmap-edits-are-direction-changes#A`.

### Increment B — The rule in the groundwork text

**Outcome:** completion criteria 2 to 4 are true for the `groundwork` module and `docs/specs/groundwork.md`.
**Dependencies:** A.
**Affected areas:** `packages/workbench/groundwork/harness/neutral/skills/draft-roadmap/SKILL.md`, `packages/workbench/groundwork/files/docs/roadmaps/README.md`, `packages/workbench/groundwork/files/blocks/policy.md`, `packages/workbench/groundwork/tests/test_groundwork_roadmap_scope.py`, `docs/specs/groundwork.md`; the root `AGENTS.md` is regenerated by the owner's rerender and is not edited.
**Steps:**
1. Write the tests first in `test_groundwork_roadmap_scope.py`, and change its docstring so that it names this plan as well as the earlier one and describes the rule under test: each of the skill, the README and the spec says the candidate is shown to the owner and written on the owner's word and names the `change-direction` checkpoint; the skill's description does not say it adds a candidate; step 6 and the README's "update it in place" carry the owner's word; the policy block holds the sentence; the placement test, the 15-candidate prompt and the new-roadmap proposal are still said; and one test walks every markdown file under `base/` and `packages/` outside `tests/`, and the groundwork spec, and fails for "If it does, add it there" or "is added to it as a candidate". See them fail.
2. Edit the five files. Keep the existing tests of that file passing.
3. Search the repository for another copy of the changed sentences (the other module, the specs, `docs/development.md`); report one and change it only if it states the old sentence.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_groundwork_roadmap_scope.py` and the rest of the groundwork module tests; `tests.test_rendering` and `tests.test_permissions_drift`, always, because the skill and the policy block are rendered; `wb run code-work check`. Not run: the whole suite (no code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-roadmap-edits-are-direction-changes#B`.

### Increment C — The rule in the code-work text

**Outcome:** completion criteria 2 to 4 are true for the `code-work` module and `docs/specs/code-work.md`.
**Dependencies:** A (B and C may be copied and released together).
**Affected areas:** `packages/workbench/code-work/files/docs/plans/README.md`, `packages/workbench/code-work/files/blocks/policy.md`, `packages/workbench/code-work/tests/test_codework_candidate_text.py`, `docs/specs/code-work.md`; the root `AGENTS.md` is regenerated by the owner's rerender and is not edited.
**Steps:**
1. Write the tests first in `test_codework_candidate_text.py`, and change its docstring so that it names this plan as well as the earlier ones: the plans README and the spec say out-of-scope work is deferred or proposed to the owner as a roadmap candidate; the checkpoint sentence in both says a change to a roadmap other than a typo is the checkpoint; the policy block's first work sentence names both starts (a candidate, and work too small to need one); and one test walks every markdown file under `base/` and `packages/` outside `tests/`, and the code-work spec, and fails for "or in a roadmap". See them fail.
2. Edit the four files.
3. Search for another copy, as in B.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** the code-work module tests, `tests.test_rendering`, `tests.test_permissions_drift`, `wb run code-work check`. Not run: the whole suite.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-roadmap-edits-are-direction-changes#C`.

### Increment D — Match this repository's two READMEs and check the generated policy

**Outcome:** completion criterion 6 is true.
**Dependencies:** B and C committed, and the owner's acknowledge, upgrade and rerender of both.
**Affected areas:** `docs/roadmaps/README.md`, `docs/plans/README.md`; the root `AGENTS.md` is read, not edited.
**Steps:**
1. Compare each README with its shipped file (`diff`, a plain read); they differ by the sentences of B and C only.
2. Edit each to equal the shipped file.
3. Read the root `AGENTS.md`, as regenerated and committed with the install state of B and C, and check that it holds the new policy sentences of both blocks; if it does not, stop and report it for the owner.
4. Ask the `reviewer` for a read.
**Verification:** `diff` of each README against its shipped file prints nothing; a `grep` of `AGENTS.md` for the two sentences; `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-roadmap-edits-are-direction-changes#D`.

## Verification for the plan as a whole

Each increment's recorded verification stands. Whether an agent now stops before writing a candidate is for a live run: ask an agent, in a scratch clone, to add a clear new candidate to a roadmap and see that it shows the candidate and waits, and that the same request with the owner's word writes it.

## Risks and sensitive actions

- The rule makes agents ask more often: every candidate waits for the owner. That is the existing checkpoint, which offers `block` only. It adds a question and removes no capability.
- Increment A edits an accepted record, by a dated note only, with the owner's approval of the plan as its approval; if the owner would rather not touch the record, the plan is redrafted without A and the rule stays in the shipped text and the specs.
- The sentence "other than correcting a typo" mirrors the specs' rule and leaves a judgment to the agent; the groundwork spec already says the harness cannot tell the two apart.
- Two packages change: the release approvals, the removal of their stale shipped records after the owner approves each list, the acknowledge, the upgrade and the rerender are the owner's, once per increment or once for B and C together. Nothing is pushed without the owner's word.
- No secret, input parsing, filesystem write by code, subprocess or network is touched. A security review is not suggested.

## Review record

Codex (`gpt-5.6-terra`), plan review, 2 rounds of 3, converged with no meaningful finding in round 2.

- Applied (round 1, blocker): the plan chose the reading that a candidate waits for the owner although decision 2 of the accepted record says it "is added to that roadmap" and states neither reading; no superseding or clarifying record existed. The plan now adds increment A, a dated clarification note after the unchanged body of the record, with its exact words, citing the `draft-decision` rule that a narrow clarification of an accepted record needs the owner's approval and is such a note; the owner's approval of this plan is that approval. The plan says that if the owner would rather not touch the record, it is redrafted without that increment.
- Applied (round 1, major): the completion criterion promised a guarantee across the shipped set but the tests read only named files. Two tests, one in each module increment, now walk every markdown file under `base/` and `packages/` outside `tests/` and both specs.
- Applied (round 1, major): the regenerated root `AGENTS.md` was required to hold the new policy but was in no increment. It is stated as regenerated by the owner's rerender and carried by the install-state commit after each module increment, and the last increment reads it and stops and reports if the sentences are missing.
- Applied (round 1, minor): the two test docstrings that name the earlier plan are updated to name this one and the rule under test.
- Rejected: none. Left for the owner: whether the note on decision 2 may be added by approving this plan.

## Deferred work

- A wider audit for conflicts between shipped rules of other kinds, which this audit did not look for.
- The `workbench-v1` roadmap's own text and its size, which the owner has left for later.

## Result

### Increment A

Done, not committed. Added the dated clarification note, verbatim from "Assumptions and constraints", as a paragraph after the last paragraph of the Evidence section of `docs/decisions/2026-11-06-roadmaps-are-scoped-by-finish-line.md`. `git diff` shows two added lines (a blank line and the note) and no changed line; the status line is untouched.

- Verification run: `git diff -U0` of the record; `wb run code-work check` (checked 107 plans, no problems); `wb check` (no problems). No test suite (no code or shipped file changed).
- Reviewer (`reviewer` agent), one exchange: no blocking finding. It confirmed the note matches the plan's words and fits the `draft-decision` rule. One non-blocking observation, which I checked with `grep -c`: `docs/decisions/README.md` holds no row for this record (count 0), so step 2's "row" has nothing to touch and the index is unchanged; the missing row is an earlier gap outside this increment.
- Not done: increments C and D (B is below).

### Increment B

Made and tested in a scratch clone; waiting for the owner to copy six files into the live tree (a script with the files' recorded hashes) and for the owner's word to commit. Nothing in the live tree has changed yet.

- Tests first: `test_groundwork_roadmap_scope.py` was rewritten with a new class `WhoWritesAChange` (9 tests) and a docstring that names this plan; 8 of its 14 tests failed before the text changed. One test walks all 82 shipped markdown files under `base/` and `packages/` outside `tests/`, plus the spec, and fails for "If it does, add it there" or "is added to it as a candidate".
- Text: the `draft-roadmap` skill (description now "propose a candidate for one", step 1, step 6, the rules), the roadmaps README (Naming, Contents, Retiring), one new bullet in the policy block, and `docs/specs/groundwork.md` (the roadmap bullets, the candidate-definition bullet and the checkpoint section).
- Verification run: all 9 groundwork module test files plus `tests.test_rendering` and `tests.test_permissions_drift`, 374 tests, OK; `wb run code-work check` OK. Not run: the whole suite.
- Deviations from the plan, both small. (1) The policy sentence says "Check that a candidate shares the finish line of the roadmap it would join" where the plan's proposal says "Do the placement test", because "placement test" is defined in no shipped text. (2) `test_groundwork_module.py` also changed, one number: its cap on the policy block's length went from 16 to 21 lines, because the one new policy sentence takes the block from 16 to 21; the owner chose this over shortening the sentence. The plan named neither.
- Committed: the files as `6ad1b86`, the install state as `d7ef145`.
- Reviewer, one exchange, no blocking finding. Applied: the spec's candidate-definition bullet said "investigative work may reshuffle, add or drop candidates" with no owner step, so it now ends "each on the owner's word", with a test; a missing blank line in the test file. Noted, not changed: the first deviation above; the walk test is case-sensitive on exact sentences, which is what the plan names. The old sentences remain in this repository's seeded `docs/roadmaps/README.md` and in the installed copies, which are increment D and the rerender.
- Done after this entry: the six-file copy, the release approvals, the removal of the stale records, and the acknowledge, upgrade and rerender, all by the owner.

### Increment C

Made and tested in a scratch clone; waiting for the owner to copy four files into the live tree (a script with the files' recorded hashes) and for the owner's word to commit. Nothing in the live tree has changed yet.

- Tests first: `test_codework_candidate_text.py` got a docstring that names this plan and a new class `WhoWritesACandidate` (5 tests); 4 of the 10 tests failed before the text changed. One test walks all 82 shipped markdown files and the spec and fails for "or in a roadmap".
- Text: the plans README (the opening sentence, the out-of-scope sentence now "deferred, or propose it to the owner as a roadmap candidate", and a new paragraph after the checkpoint list), the policy block line 3 (a candidate, or work too small to need one), and `docs/specs/code-work.md` (the same sentence and a paragraph after the checkpoint table notes).
- Verification run: all 16 code-work module test files plus `tests.test_rendering` and `tests.test_permissions_drift`, 465 tests, OK (2 skipped as before). Not run: the whole suite.
- Reviewer, one exchange, no blocking finding. Applied: the plans README opening line "It is how a roadmap candidate becomes a verified, reviewed, committed result" was candidate-first and missing from the audit table, so it now names both starts, with a test; the new checkpoint paragraphs now say "it always stops", the README adding "whatever level is set", pinned in the tests. Noted, not changed: the new paragraphs are shorter than the groundwork text (no list of what counts; the code-work spec points to the groundwork spec); spec line 245 calls `change-direction` "delegable" while later lines say it offers `block` only, which is earlier text.
- Left for the owner: the four-file copy, release approvals, removal of the stale shipped records, acknowledge, upgrade and rerender.
