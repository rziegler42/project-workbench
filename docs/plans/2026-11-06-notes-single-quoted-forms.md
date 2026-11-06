# Show the notes and search forms in single quotes

Status: Proposed
Created: 2026-11-06
Candidate: none (decision 2 of the accepted record `2026-11-06-command-gate-and-prose-in-module-calls`, a follow-up to the plan `2026-11-06-notes-live-run-fixes`)
Specs: mempalace, mempalace-notes

## Goal

An agent that copies the forms in the always-loaded block or the `recall-memory` skill writes a search question, a note title and a short note body in single quotes, which the
command gate reads as data, and not in double quotes, which the gate refuses whenever the text holds the letters of a key set to `ask`. When the plan is done the block and
the skill show the single-quoted forms and say what to do with a text that holds an apostrophe or a refused title, and the tests pin each.

## Scope

- The block (`files/blocks/policy.md`) and the skill (`recall-memory/SKILL.md`): the form of the search and of `save` in single quotes; the sentences on an apostrophe in a
  question, a title or a body, and on a refused title.
- The tests that pin the double-quoted forms (`test_mempalace_guidance.py`, `test_mempalace_notes_guidance.py`).
- The spec sentences that show those forms (`mempalace.md`, `mempalace-notes.md`).

## Non-goals

- Any change to the command gate, the helpers or the keys. Freeing a literal call of another module command is decision 3 of the accepted record and has its own plan.
- A rule for the letters of `mine` or `sync` inside a plain word in a notes command (a wing, a note name). Only that gate change removes it.
- Rewording anything else in the block or the skill.

## Assumptions and constraints

- The record says what single quotes free and do not free: the search question in single quotes passes (a call of the key's own command, a plain first token); a notes call
  with single quotes frees the `keep` word and not the `mine` or `sync` letters of prose. This plan does not claim more.
- The block's limit is 24 lines and it stays within it. It names no owner-run command with `wb run`, and never `mine`.
- A single-quoted string cannot hold an apostrophe. The text says how to avoid one; it does not teach shell escapes, which the gate does not read as data.
- The installed copies and the rendered `AGENTS.md` change only when the owner runs the upgrade and the rerender after the commit.

## Completion criteria

1. The block shows `wb run mempalace search -- '<question>'` and `wb run mempalace-notes save --title '<title>' --kind <kind> --body '<text>'`, and the skill shows
   `wb run mempalace search --results 5 -- '<question>'` and the same `save` form; no double-quoted form of either remains in the block or the skill.
2. The skill says: a question, a title or a body has no apostrophe (reword the question or the title; give a body that needs one to `save` from a file on standard input);
   if the refusal comes from the title or the question, choose other words (they are your label, not the owner's words), and the body is never reworded to get past the gate
   (increment A of the plan `2026-11-06-notes-live-run-fixes`).
3. Tests pin each sentence and fail if a form returns to double quotes.
4. The block is within 24 lines, and the module suite and the drift and rendering tests pass.

## Increments

### Increment A — Single-quoted forms and the sentences around them

**Outcome:** completion criteria 1 to 4 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/mempalace/files/blocks/policy.md`, `packages/workbench/mempalace/harness/neutral/skills/recall-memory/SKILL.md`,
`packages/workbench/mempalace/tests/test_mempalace_guidance.py`, `packages/workbench/mempalace/tests/test_mempalace_notes_guidance.py`, `docs/specs/mempalace.md` (the sentence at
the search form), `docs/specs/mempalace-notes.md` (the "Forms and refusals" bullet).
**Steps:**
1. Write the tests first: the four single-quoted forms are present once where the old tests count them; no `"<question>"`, `"<title>"` or `"<text>"` remains in either file;
   the skill's sentences of criterion 2 are present. See them fail.
2. Edit the block and the skill. In the block change only the two forms and, if it needs room, join a wrapped line (it is at its 24 lines now). In the skill change the two forms
   and add the sentences of criterion 2 beside step 2 of the search and step 2 and step 5 of the notes.
3. Update the two spec sentences. Add a line under the "Evidence" follow-up of `mempalace-notes.md` saying which defect this addresses (the forms I gave in the first fix).
4. Run the verification below; ask the `reviewer` for a read.
**Verification:** the two guidance test files and `test_mempalace_module.py`; the mempalace module suite; `tests.test_permissions_drift` and `tests.test_rendering`, because the block
is rendered into `AGENTS.md`; `wb run code-work check`. After the copy and release, the upgrade and the rerender are the owner's. Not run: the whole suite (no code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-notes-single-quoted-forms#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether an agent follows the forms is for the next live run.

## Risks and sensitive actions

- Text added to the always-loaded block is read by every agent in every session; only the two forms change and the line count does not grow.
- An agent that still double-quotes is refused (nothing runs) and reports it, as now.
- A question with an apostrophe in a single-quoted form breaks the quote; the gate refuses a mispaired quote. The sentence of criterion 2 is the guard, and the refusal is safe.
- No secret, no filesystem write by the code and no network is touched.

## Review record

Empty until a review is asked for.

## Deferred work

- The gate change of decision 3 of the accepted record (a literal call of another module command, only for commands that declare and verify exact first-argument dispatch),
  in a plan of its own with a Codex review and a security review.
- The status clauses on `2026-10-28-gate-reads-module-arguments` and `2026-10-27-command-gate-literal-arguments`, which need the owner's word.
- A second live run on a different topic, with a lesson or a dead end.

## Result

Empty until work starts.

**Increment A (2026-11-06), done in a scratch clone at commit `6054dee`; not yet copied, released or committed.**

- Built: the search form and the `save` form in the block and the skill are in single quotes (`'<question>'`, `'<title>'`, `'<text>'`); the skill says to write the question in single quotes with no apostrophe
  (reword it), the title and the body in single quotes with no apostrophe in either (reword a title), that a body that needs an apostrophe, or that the harness refuses, goes to `save` from a file on
  standard input, that a refused title or question gets other words (they are the agent's label), and that the body is never reworded to get past the gate. The block is still 24 lines and names no `mine`.
  Changed in the clone (four files): the block, the skill, and the two guidance tests (the pinned forms, and new tests: no double-quoted placeholder in the block or the skill, by name and by pattern; the
  sentences). In the live tree: `docs/specs/mempalace.md` (the search-form sentence) and `docs/specs/mempalace-notes.md` (a bullet "Single-quoted forms", naming the defect it corrects).
- Verification as run: 8 of the new or changed tests failed before the text; afterwards the mempalace module suite in the clone gave 502 tests, all passing, and `tests.test_permissions_drift` and
  `tests.test_rendering` (107) pass; `wb run code-work check` passes. Not run: the whole suite (no code changed); an agent following the text (the next live run).
- Review: the `reviewer` agent, one exchange, no blocking finding. Applied: a title with an apostrophe is reworded (the text gave no remedy); "short body" is gone (a body is at least 300 characters, so it is
  rarely short; a body the harness refuses goes through the file); the spec bullet names the defect it corrects; the "no double-quoted form" test also matches the pattern of a double-quoted placeholder.
  Not applied: telling the agent which part of a refusal matched (the message does not say, and the rule works without it). The reviewer ran nothing.
- A remaining double-quoted form, outside this plan: the helper's refusal of a search with no `--` prints `wb run mempalace search -- "your question"` (`helper/mempalace`, and `mempalace.md` line 66 and
  `test_mempalace_run.py` describe it). The plan changes no code, so it is left; it is recorded here and should join the gate plan or a small code fix.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/sq_install_files.py`, four files, only if their hashes are those recorded), the release approvals, the removal of the stale records
  after you approve the list, then "commit a"; after the commit the upgrade and the rerender (the rendered `AGENTS.md` and the skill gain the new forms).
