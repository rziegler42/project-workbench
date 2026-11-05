# Show the form of a palace search where an agent would guess it

Status: Proposed
Created: 2026-11-05
Candidate: workbench-v1#mempalace-search-form
Specs: mempalace

## Goal

In a live session on 2026-11-05 (recorded as a result of the plan `2026-11-05-mempalace-use-and-independence`, whose Increment B told the agent to
search before a brainstorm) a fresh agent did search, on its own, before its first question to the owner. It ran
`wb run mempalace search "model-assisted entity step during mempalace project setup"`, with no `--` before the query, twice (once with a
leading `cd`). Both were refused with "… is not an option of search". It did not retry, and it said so to the owner. The form that works,
`wb run mempalace search --results 5 -- "<question>"`, is in the `recall-memory` skill, which it had not loaded; the policy line only says
"with `wb run mempalace search`", and the refusal does not say what the form is. After this plan:

1. a `search` whose arguments are refused because one is not an option says, in the same one-line refusal, what the form is: the options, then
   `--`, then one query, with an example;
2. the policy line that names the command shows the form, `wb run mempalace search -- "<question>"`, and the block still fits its limit of
   14 lines;
3. `mempalace.md` says so.

## Scope

- `packages/workbench/mempalace/helper/mempalace` (the message in `parse_search`), `packages/workbench/mempalace/files/blocks/policy.md` (the
  first bullet), `packages/workbench/mempalace/tests/test_mempalace_run.py` and `test_mempalace_guidance.py`.
- `docs/specs/mempalace.md` ("Behavior", the paragraph on `search`, and "The policy block and the skill").
- The owner's steps: the copy and release of each package edit, and an upgrade of each project that should receive the new text.

## Non-goals

- The arguments `search` accepts. A bare word before `--` is still refused; only the message changes.
- Loading the `recall-memory` skill automatically, a retry rule for the agent ("one reworded retry"), or anything about how the agent words a query.
- The messages of `init` and `mine`, which only the owner runs from a terminal.
- Any change to the palace, to the other modules' skills or to the permission levels.

## Assumptions and constraints

- The existing tests for the refusal look for the words "is not an option" (`test_mempalace_run.py`, `test_mempalace_owner.py`); the new message
  keeps them. A refusal is one line on standard error (`refused: …`); the new text stays one line.
- The message already echoes up to 60 printable characters of the caller's text (`display.ascii_text`); the new words are constant and add
  no new path from the caller's text to the output.
- The policy block is exactly 14 lines, which its test allows at most; the change reflows its first bullet and must not add a line. The test
  that pins the commands the block names expects the set `{"wb run mempalace search"}`, which the new text keeps.
- A change to `packages/` follows the package-edit process: a scratch clone, tests there, the owner's copy with the recorded-hash script, the
  release approvals and the removal of stale shipped records after the owner approves the list. The command gate refuses Bash while the packages
  differ from the release.
- Nothing is pushed. A commit needs the owner's word.

## Completion criteria

1. `search "free text"`, `search "free text" --wing x` and an unknown option such as `--include-media` are refused with a one-line message that
   contains "is not an option of search", the list of the five options, "then -- and one query" and an example with `search -- "`; the program is
   not started; `search -- "query"` and every form that worked before behave as before.
2. The first bullet of the block shows `wb run mempalace search -- "<question>"` and keeps every rule it pinned; the block has at most 14 lines; the
   guidance tests pass.
3. `mempalace.md` describes both, and the mempalace tests pass.
4. After the owner's upgrade, the same fresh-session task as on 2026-11-05 (or another that makes the agent search) is run, and what the agent typed
   is recorded in the spec's evidence, whether or not it now found the right form.

## Increments

### Increment A — The refusal shows the form

**Outcome:** a refused argument of `search` comes with the form in the same line.
**Dependencies:** none.
**Affected areas:** `helper/mempalace` (`parse_search`), `tests/test_mempalace_run.py`, `docs/specs/mempalace.md` (the paragraph on `search`), the
package's release records (the owner's steps).
**Steps:**
1. In a scratch clone, write the tests first and see them fail:
   - a bare sentence as the only argument, a bare word followed by `--` and a query, and `--include-media` each give a one-line refusal that
     contains "is not an option of search", the five option names, "then -- and one query" and `search -- "`, and start no program;
   - the echoed text is still cut to 60 characters and is printable ASCII (a long argument with a control character and a non-ASCII letter);
   - `search -- "why SQLite"`, `search --wing w -- "q"` and the other accepted forms give the same arguments to the program as before;
   - the refusals of a missing `--`, an option given twice, an option with no value and an empty query keep their messages.
2. Change the message of the first refusal in `parse_search` (the option not in the allowed list).
3. Edit the paragraph on `search` in `mempalace.md`.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps: copy the changed files with the recorded-hash script, `wb preview release-approvals` and `wb release-approvals --digest`, and the
   removal of the stale shipped records after approving the list.
**Verification:** the tests of the `mempalace` module, run as the repository's runner does, and `wb run code-work check`. Not run: the whole suite and
`tests/test_boundary.py`, because no installer file changes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-search-form#A`.

### Increment B — The policy line shows the form

**Outcome:** the block names the command with its form, within 14 lines.
**Dependencies:** A.
**Affected areas:** `files/blocks/policy.md`, `tests/test_mempalace_guidance.py`, `docs/specs/mempalace.md` ("The policy block and the skill"), the
package's release records (the owner's steps).
**Steps:**
1. Write the tests first and see them fail: the block contains `wb run mempalace search -- "<question>"`; it still contains every rule pinned
   by the existing tests; it has at most 14 lines; the commands it names are exactly `{"wb run mempalace search"}`.
2. Reflow the first bullet of the block with the form after the command.
3. Edit the spec sentence about the policy block.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps as in A, then `wb upgrade` in each project that should receive the text, starting with this one.
**Verification:** the tests of the `mempalace` module and `wb run code-work check`. After the owner's upgrade, a search of the rendered `AGENTS.md`
for the form.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-search-form#B`.

## Verification for the plan as a whole

Each increment's recorded verification stands. Completion criterion 4 is the live check and is the owner's: a fresh session and a task that makes the
agent search; the record of what it typed goes into the spec's evidence, with the commands read from the session's transcript (command text only).
The wider suite is not run: the change is a message, a line of text and their tests.

## Risks and sensitive actions

- The helper's message changes, so a script that matched the old text would stop matching. The only tests that do are in this module and keep
  the words they look for.
- The block has no spare line; a reflow that adds one fails its test, and the fix is to shorten the line, not to raise the limit.
- A fix of the text does not make an agent search or use the form. The first live session found one search attempt; this plan removes one cause of
  its failure and nothing else.
- None of this is security-sensitive: the message adds constant text to a refusal that already echoes the caller's text, and no new input reaches a
  path, a command or the program.

## Review record

Empty until a review is asked for.

## Deferred work

- A retry rule for the agent ("one reworded retry when the results do not answer"), which is not needed until the agent searches with the right form.
- Loading the `recall-memory` skill when the policy line is read, if the harness offers a way.
- The same hint for `init` and `mine`, whose arguments only the owner types.

## Result

Empty until work starts.
