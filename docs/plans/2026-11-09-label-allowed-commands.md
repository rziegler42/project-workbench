# Let the labelling tool show only the commands the hook allowed, with their ids

Status: Completed
Created: 2026-11-09
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The owner can label the commands that the deciding hook allowed, and only those, with the id that the report prints beside them.

Today `tools/label.py` walks every unlabelled collected row, oldest first, and shows no id (found by the review of increment E of `2026-11-08-action-review-cutover-for-commit`, who read `label.py`). Once the key `wb run safe-git commit` is set to `delegated`, the commands the hook allows get no prompt, so the owner's label is the only measure of whether an allow was right; and those commands sit at the end of the queue, behind every older unlabelled command (110 at the first reading of the bound on 2026-11-08). A trial that cannot label them ends with "no false approve found" when nobody looked.

After this plan `python3 -B label.py --allowed` shows only the unlabelled collected rows that belong to a command the hook allowed, oldest first, and every command the tool shows carries its id on the line that names its number, time and rule. `--allowed` can be combined with `--skipped`. Nothing else about the tool changes: the same screens, the same keys, the same meaning of `right` and `wrong`, and a terminal is still required.

## Scope

- `packages/workbench/action-review/tools/label.py`: the option, the read of `verdicts.jsonl` when the option is given, the id on the header line, the usage text and the docstring.
- `packages/workbench/action-review/tests/test_tools_label.py`: the tests.
- `docs/specs/action-review.md`: the runbook paragraph "See what it allowed" (it now says the tool cannot pick the allowed commands out) and the "As built" paragraph of the labelling tool.

## Non-goals

- Changing the report, the store, the hook or the engine. The report already prints the ids of the collected rows of the allowed commands; this plan makes the tool able to show them.
- Choosing a sample. The tool shows every unlabelled allowed command, and the owner stops with `q` when they have labelled enough.
- Changing what `right`, `wrong` and `skip` mean, the bound, the minimums or the cutover line.
- Installing the tool. It is still copied by the owner to their own directory with the store, outside every project.
- Running the owner's trial or setting the key: increment F of the cutover plan, the owner's.

## Assumptions and constraints

- **The link is the command's hash (my call).** A verdict row has `command_sha256` and so has a collected row; the hook writes both for a reviewed command, and the report already matches them this way. A command reviewed more than once offers every collected row of its hash. This is rare for an allowed command, because its text carries the state digest, so the same hash is the same command again.
- **An allowed command is a verdict row whose `answer` is `allow` (a fact).** The store accepts that field only on a reviewed approve, so a malformed one is an unreadable line and never an allow.
- **The id is shown on every command, with or without the option (my call).** It is one field on a line the tool already prints, and it saves a second mode. An id is 32 lowercase hexadecimal characters, printable ASCII; it is shown through the tool's own `visible` so nothing else could reach the terminal.
- **The verdict rows are read only when `--allowed` is given (my call).** The default run reads the same two files as today and fails in the same ways.
- The tool starts no program, reads no file but the store and writes one whole label row or none; those rules, and the exit codes (0, 1, 2 and 130), stay.
- Standard library only.

## Completion criteria

1. `label.py --allowed` shows exactly the unlabelled collected rows whose command hash is the hash of a verdict row with `answer: allow`, oldest first, with their count; `--allowed --skipped` shows the skipped ones among them; with none to show it says so in a sentence that names the hook.
2. Every command the tool shows carries its id on its header line; nothing else on the screen changes, and a handle is shown as a handle with its id.
3. An argument other than `--allowed`, `--skipped` or both (in either order), and either of them twice, is a usage error with exit 2 and nothing read or written; without a terminal the tool still refuses, with exit 2.
4. A verdict file that cannot be read ends the tool with exit 1 and a fixed ASCII note only when `--allowed` is given; unreadable lines of `verdicts.jsonl` are counted in the sentence that says how many lines could not be read.
5. Without the option the tool reads the same files, shows the same queue and writes the same rows as before.
6. The spec says what the option does and no longer says that the tool cannot pick the allowed commands out.
7. `wb run code-work check` passes.

## Increments

### Increment A — `label.py --allowed` and the id

**Outcome:** completion criteria 1 to 7 are true.
**Dependencies:** none (the cutover plan's increments D and E are committed).
**Affected areas:** `packages/workbench/action-review/tools/label.py`, `tests/test_tools_label.py`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first, in the style of the file (a fake terminal, a scratch store): the id is on the header of an ordinary command and of a handle; `--allowed` shows only the commands whose hash a verdict row allowed, in file order, with the right count, and skips a labelled one; a command collected under another hash, a verdict row that only approved (no `answer`), a verdict row of a decline and a hash with no collected row are not shown; `--allowed --skipped` and `--skipped --allowed` show the skipped allowed ones only; nothing waiting gives the sentence that names the hook; unreadable lines of the verdicts are counted; a verdict file the store refuses ends with exit 1 and a fixed ASCII note and writes nothing; the default run does not open `verdicts.jsonl`; the options twice, an unknown option and an extra word give the usage line and exit 2; labelling a command shown by `--allowed` writes one whole row for its id as before. Run them and see them fail.
2. Add the option, the read of the verdicts (`store.read("verdicts.jsonl", home)`, only with the option), the queue filter, the id on the header line, the usage text and the docstring.
3. Update the spec: the runbook paragraph "See what it allowed" (use the option and the ids) and the "As built" paragraph of the tool.
4. Run the verification and ask the `reviewer` for a read.
**Verification:** `tests/test_tools_label.py`, `tests/test_tools_report.py` (the report is unchanged and its ids are those the tool now shows) and `tests/test_actionreview_module.py` (the file list of the module); a mutation pass over the new lines of the tool with each kill attributed to a named test; `wb run code-work check`. No whole-module run: the change is one tool that nothing imports. What could break outside the tested area: the tests that pin the tool's header line (they are in `test_tools_label.py` and are updated, not skipped), and the module's tree hash, which the manifest records, so the install state needs the owner's upgrade after the copy and the release approvals.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-09-label-allowed-commands#A`.

## Verification for the plan as a whole

The one increment's verification is the plan's. The report and the hook are untouched, and nothing is run against the owner's real store.

## Risks and sensitive actions

- The tool writes the owner's labels, which the cutover rests on. The change adds a filter and a field to the screen and a read of a second file; it does not change what is written, and the tests pin that one whole row is written for the id shown.
- A hash can link to a collected row of an earlier review of the same command text, which the engine may have judged differently. The text of an allowed commit carries the state digest, so the same text is the same command again; the spec says that the link is the hash.
- A package file of the module changes (the tool is in `tools/`, which is not installed, but the module's tree hash is in the manifest): the release approvals, the removal of the stale shipped records after the owner approves the list, the acknowledge, the upgrade and "commit install state" are the owner's steps, as for every package change. Nothing is pushed.

## Review record

Empty until a review is asked for.

## Deferred work

- A tool that draws a sample for the owner, or shows the commit's diff beside the engine's verdict. Not needed to measure a false approve; the owner can stop when they have labelled enough.

## Result

**Increment A is committed as `73f0e8d`** (trailer `#A`; 8 paths: the plan, the spec, the tool and its tests, two new shipped records and two old ones removed with the owner's approval of the list), and its install state as `8a93862`. The plan is completed.

**Increment A (2026-11-09), done in a scratch clone at commit `82fb997`; the spec is edited in the live tree; the two package files were then copied, released and committed as above.**

- Built, in `packages/workbench/action-review/tools/label.py`: `--allowed` (each option once, in either order, any other word is the usage line `usage: label.py [--allowed] [--skipped]` and exit 2, checked before the terminal check and before any read); with it `verdicts.jsonl` is read (only then), the unlabelled queue is kept to the rows whose command hash is the hash of a verdict row with `answer == "allow"`, unreadable verdict lines join the count of unreadable lines, a store failure on the verdicts is exit 1 with the existing fixed note, the count line says "(the hook allowed each one)" and an empty queue says "Nothing the hook allowed is waiting to be labelled."; and every command, handles included, shows its id as `id <id>` at the end of its header line, through `visible(row["id"], 40)`. Without `--allowed` the files read, their order, the queue, the messages and the exit codes are as before.
- Tests, written first (`tests/test_tools_label.py`, class `Allowed`; 76 tests in the file): 14 of the new tests failed on the unchanged tool for the right reason (no id, no option). They cover the id on both headers; only the allowed rows, in file order, with the count; rows not shown (approved but never answered, a decline, an allow with no collected row); labelled and skipped rows with both orders of the options; skipped alone unchanged; unreadable verdict lines; a store refusal on the verdicts (exit 1, ASCII note, nothing written); the default run never opening the verdicts; the usage errors with nothing read; no terminal with nothing read; one whole label row for the id shown; a handle with its id; the id through the cleaner; and the tool itself taking only the answer `allow`.
- Verification as run (Python 3.15.0, Darwin): `test_tools_label.py` 76 tests pass; with `test_tools_report.py`, `test_actionreview_module.py` and `test_actionreview_pins.py`, 217 tests pass (run before the last two test edits below; `test_tools_label.py` was run again after them); a mutation pass of 16 mutants of the new lines, each kill attributed to a named test: 15 killed at once, one survived (any answer counted as an allow: the store already refuses other answers) and was killed after a test that calls the tool with a store that returns them; `wb run code-work check` passes. Not run: the whole module (the plan says why: nothing imports the tool), the tool at a real terminal and against the owner's real store (the owner's directory).
- Review: the `reviewer` agent, one exchange, ran nothing, no blocking finding. Applied: the two tests that said "reads nothing" now watch `store.read` (the code was right; the tests were loose). Not applied, deferred: `docs/development.md` line 65 still documents the tool as `label.py [--skipped]`; the file is outside this plan's scope, and the line is incomplete rather than false. Its caveat: it read only the new class and the tail of the test file, not the whole file (the whole file runs and passes).
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/l1_install_files.py`, two files, only if their hashes are those recorded); the release approvals; the removal of the stale shipped records after the list is approved; then "commit a"; after the commit the upgrade (the module's tree hash is in the manifest) and "commit install state". Your own `label.py` in `~/action-review-shadow` is not touched: copy it there with `shadow_store.py` to use `--allowed`.
