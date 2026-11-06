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
