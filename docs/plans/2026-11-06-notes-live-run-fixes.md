# Fix what the live run of the notes found

Status: Proposed
Created: 2026-11-06
Candidate: none (a follow-up to `workbench-v1#mempalace-notes`, whose live run is recorded under "Evidence" in `mempalace-notes.md`; the owner may want it as a roadmap candidate first)
Specs: mempalace-notes, mempalace, command-permissions

## Goal

The six defects that the live run of 2026-11-06 found are fixed or, where the fix is a design choice, decided. When the plan is done: an agent in a fresh session saves, reads, reviews and files notes without guessing a command form; it files in the two confirmations with the exact commands; it keeps its own findings apart from a note the owner accepted; the gate's refusal names a command that works; and the owner has a recorded decision on how the gate treats ordinary prose that contains the letters of a key set to `ask`.

## Scope

- The always-loaded block and the `recall-memory` skill: the form of `read` and `save`, the kinds, the exact-command rule for `keep` and `mine`, the separate note for an agent's finding, one question about filing, and what to do when the gate refuses prose.
- `review`'s count line ("1 drafts").
- The gate's hint: the command it tells the agent to run.
- A decision record, `Proposed`, on how the gate's names test treats prose.

## Non-goals

- Changing how the gate judges a command. Any change to the names test is built only by a later plan, after the owner has accepted the decision of increment C.
- Hooks that save notes deterministically, a search over drafts, and other work deferred by the notes spec.
- The six drawers of the wing `live-check`.

## Assumptions and constraints

- The defects and their evidence are those in "Evidence" of `mempalace-notes.md`. Whether the new text makes an agent follow it is not tested here; it is seen in the next live run.
- The block has a test limit of 24 lines. If the forms do not fit, the plan stops and asks the owner whether to raise it; it does not shorten another module's text.
- The gate is the installer's security boundary (`command-permissions.md`, decision `2026-11-02-command-gate-reads-gaps-and-data-positions`). Increment B changes a message and nothing that decides allow or refuse.
- The owner decides whether to run a security review; the plan asks once for the gate surface, at B.

## Completion criteria

1. The block shows the form of `list`, `read` and `save` and the kinds, and a test pins it; the block stays within its line limit or the owner has raised it.
2. The skill says that `keep` and `mine` are run as one command with nothing appended (no pipe, no redirect, no `cd`), that an agent's own finding goes in a note of its own when the note it concerns holds something the owner accepted, that the question about filing is asked once and with the review question, and that a refusal of a command whose text holds the letters of an `ask` key is reported to the owner and the text is not reworded to get past it; tests pin each sentence.
3. `review` prints "1 draft" and "2 drafts" correctly.
4. The gate's refusal for a module command names `wb run <command> <argument> ...`, and a test pins it for a top-level key and a module key.
5. A decision record on the gate's treatment of prose is written as `Proposed` and waits for the owner.
6. `wb run code-work check` passes and the nearest tests pass.

## Increments

### Increment A — The block and the skill say what the run showed they must

**Outcome:** completion criteria 1 and 2 are true and pinned.
**Dependencies:** none.
**Affected areas:** `packages/workbench/mempalace/files/blocks/policy.md`, `packages/workbench/mempalace/harness/neutral/skills/recall-memory/SKILL.md`, `tests/test_mempalace_guidance.py`, `tests/test_mempalace_notes_guidance.py`, `docs/specs/mempalace-notes.md` ("When a note is saved", "Finding notes again", with a line in "Evidence" saying which defects are addressed).
**Steps:**
1. Write the tests first: the block holds the forms `mempalace-notes read <name>` and `mempalace-notes save --title --kind --body` and the seven kinds; the skill holds the four sentences of criterion 2.
2. Edit the block (form and kinds, in the fewest words) and the skill (the four sentences; and, for prose the gate refuses, the route of writing the text to a file with the file tool and passing it on standard input with `--body -`, only after step 3 shows the gate allows it).
3. Before relying on that route, run it by hand once in a scratch clone with a key at `ask` and report whether the gate allows it. If it does not, the skill says only to report the refusal.
4. If a pinned line count is exceeded, stop and ask the owner.
**Verification:** the two guidance test files and `test_mempalace_module.py`; the permission-drift test, because the block is rendered into `AGENTS.md`; `wb run code-work check`. After the copy and release, `wb upgrade` and `wb rerender` are the owner's.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-notes-live-run-fixes#A`.

### Increment B — The count line, and the gate's hint

**Outcome:** completion criteria 3 and 4 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/mempalace/helper/mempalace-notes` (the count line), its review tests, `workbench/command_gate.py` (`_reason` and the hint at its end), `tests/test_command_gate.py` and `tests/fixtures/gate_corpus.json` if the corpus pins the wording, `docs/specs/command-permissions.md` if it quotes the hint.
**Steps:**
1. Tests first: `review` with one draft and with two; the reason for a module key prints `wb run <command> <argument>`, and for a top-level key `wb <key>`, in the `ask` and the `none` wording.
2. Make the count agree in number. Build the hint from how the key is run, not from its words alone.
3. Ask the owner once whether to run a security review of this surface. The change alters message text only, and no verdict.
**Verification:** `tests/test_command_gate.py` and the gate corpus test, the notes review tests, `wb run code-work check`. Not run: the whole suite; the risk outside the tested area is a test elsewhere that pins the old wording, and a search for the old sentence finds it first.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-notes-live-run-fixes#B`.

### Increment C — A decision on how the gate treats prose

**Outcome:** a record in `docs/decisions/` with status `Proposed`, and a stop for the owner.
**Dependencies:** none.
**Affected areas:** a new file in `docs/decisions/`, and its row in the index.
**Steps:**
1. Read the accepted decision `2026-11-02-command-gate-reads-gaps-and-data-positions` and `command-permissions.md`, and the gate corpus, to state what the names test protects (splicing, folding, `$'...'`, variables) and what it costs (a word containing a key's letters in any argument, shown by the run).
2. Draft the record with the template: the context, the options with their costs (leave as is and rely on text; treat the value of named long options of one known command as data; require long text through standard input or a file so the command line holds none; rename the keys so their letters are rarer), the consequences, and evidence from the run and from tests on a scratch clone of the corpus.
3. Set it `Proposed`. Do not accept it, and do not change the gate. Stop and tell the owner.
**Verification:** `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-notes-live-run-fixes#C`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later one changed its inputs. At the end, `wb run code-work check`, and the guidance and gate tests once more only if B touched a file that A's tests read. A wider run is not named: nothing here changes how a command is judged.

## Risks and sensitive actions

- The gate hint (B) is security-adjacent code. A wrong hint is misleading, not permissive, but the change is made with tests first and a security review is offered once.
- A route that passes text to `save` through a file (A) puts untrusted-looking text outside the gate's view. The tests of the helper's credential scan still apply to it; the route is allowed only if step 3 of A shows the gate already allows it, and it adds no permission.
- Text added to the always-loaded block is read by every agent in every session; it is kept to what the run showed was missing.
- The gate decision (C) changes what the installer's boundary promises. It is only drafted here.

## Review record

Empty until a review is asked for.

## Deferred work

- Building whatever C is accepted to decide, in a plan of its own with a security review.
- The agent still depends on following the skill; the run showed it ignoring a stated rule once (the pipe on `keep`) and following it once (`mine`). If the new text does not hold, a deterministic check is the next step.
- A longer live run: a lesson, a dead end, a researcher's idea, several drafts, a revision, a second wing, and the notes after a real loss of context.

## Result

Empty until work starts.

**Increment A (2026-11-06), done in a scratch clone at commit `e53997f`; not yet copied, released or committed.**

- Built: in the block, the form of `save` and `read`, the seven kinds, `--body -`, "put your own finding or guess in a note of its own, not in a note that holds something the owner
  accepted", and "run each command the skill gives as one command with nothing appended (no pipe, no redirect, no `cd`)", all within the 24-line limit (a bullet was lengthened; no line was added
  past the limit). In the skill: step 3 (an own finding goes in a note of its own, which says which note it concerns), step 5 (a refusal by the rule `names` is not met by rewording: the text goes to a
  temporary file outside the repository and reaches `save` with `--body - < <file>`, or the owner is told), "do not ask again whether to file", and "run `keep` and each `mine` step as one command with
  nothing appended". Changed in the clone (four files): the block, the skill, `test_mempalace_notes_guidance.py` (eight new tests, with the review's fixes pinned) and `test_mempalace_guidance.py`
  (`BLOCK_COMMANDS` gains `read`). In the live tree: `docs/specs/mempalace-notes.md` (two bullets under "When a note is saved", and a follow-up line under "Evidence").
- Hand check of step 3 of the increment: `save --title x --kind finding --body -` fed from `/dev/null`, with the three owner arguments at `ask`, was allowed by the gate (the helper refused only the empty body
  and wrote nothing), so the file route is in the skill.
- Verification as run: the eight new tests failed before the text existed; afterwards the module suite in the clone gave 496 tests, all passing, and `tests.test_permissions_drift` and `tests.test_rendering`
  (107) pass. Not run: the whole suite; an agent following the text (the next live run).
- Review: the `reviewer` agent, one exchange, no blocking finding. Applied: "run `keep`, then the `mine` steps" is conditional on the levels; the temporary file is outside the repository and deleted
  after the save; the block's sentence says what it covers (the commands that move or file notes) without naming `mine`. Not applied: naming `keep` and `mine` in the block, because an earlier test
  pins that the block never names `mine`; a cosmetic docstring. The reviewer ran nothing.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/nf_install_files.py`, four files, only if their hashes are those recorded), the release approvals,
  the removal of the stale records after you approve the list, then "commit a"; after the commit the upgrade and the rerender.

**Increment B (2026-11-06), done in a scratch clone at commit `75407c9`; not yet copied, released or committed.**

- Built: `review` prints `1 draft` for one draft and `N drafts` otherwise (`helper/mempalace-notes`); the gate's refusal for a module argument names `wb run <command> <argument> ...`, in the `ask` wording, the
  `none` wording and the gap-rule wording, through a new `_hint_command` in `workbench/command_gate.py` (the other keys still read `wb <word> ...`). The verdicts, the rules and what is allowed or refused are unchanged;
  only the text after `run it as` changed. Changed in the clone (four files): `workbench/command_gate.py`, `tests/test_command_gate.py` (three new tests), the helper, and `test_mempalace_notes_review.py` (two new tests).
  In the live tree: `docs/specs/command-permissions.md` (one paragraph on the hint).
- A slip, found and fixed before any review: the first name I gave the new function was already in the file (`_spelled`), and it overrode the older one, which broke five tests of the hint; the new function is
  `_hint_command`.
- Verification as run: before the change, 3 of the new gate tests and both new review tests failed (the launcher-key test passed, as a guard); after it `tests.test_command_gate` and `tests.test_gate_corpus` (147),
  the nine test files that use the gate (`test_levels`, `test_levels_facts`, `test_checkpoint_command`, `test_settings`, `test_rendering`, `test_doctor`, `test_layout`, and the two named) (538 together; `test_settings`
  by discovery, 115), the claude module's tests (34, 12 skipped) and the mempalace module suite (498) pass. A search found no other test or document that pins the old wording. Not run: the whole suite.
- Review: the `reviewer` agent, one exchange, no blocking finding and nothing applied. It compared the old and new code for each key shape (a top-level key, a launcher key, a module argument and a preview
  key) and found only the module argument's text changed, in the three message strings; it found the hint names the exact command that the `ask` rule matches, the sixty-character slice unchanged, and
  that the new tests would fail on the old text. It did not search the whole repository for the old wording (my search of the tests and documents found only the tests named above, and the corpus test passes)
  and ran nothing. Whether a key can be longer than sixty characters was not checked and is not a regression.
- Left for the owner: the question of a security review of this surface (the plan asks once; the change is message text only), the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/nb_install_files.py`, four files, only if their hashes
  are those recorded; it moves each file into place in one step because the hooks import `command_gate.py`), the release approvals, the removal of the stale records after you approve the list, then "commit b"; after the
  commit the upgrade and the rerender (the installed helper changes).
