# Let the commit that completes a plan carry the review engine's record of it

Status: Completed
Created: 2026-11-07
Candidate: none (a correction that follows from a report in another project, knowledge-base, 2026-11-07: the commit that completes a plan leaves out the plan's review directory)
Specs: review-engine

## Goal

After this plan, an agent that commits the completion of a plan in a project that has the `review-engine` module can learn, from the module, the exact files of that plan's review, and the module's own skill tells it to include them. A project without the module sees no change and no mention of the engine.

The finding: `review-engine` keeps a review in `.workbench/workbench/review-engine/<key>/` (`state.json`, `ledger.md`, `schema.json` and one `round-<n>.json` per round) and its spec says the directory "is committed with the project". `safe-git commit` takes exact files and refuses a directory, and the `commit-changes` skill and `docs/plans/README.md` tell the agent to commit only paths it changed for the work and say nothing of the review directory. So the plan and its code are committed and the review files stay untracked or modified. In knowledge-base two such directories are untracked now, and the earlier ones reached git only through a separate manual commit.

The fix is placed with the module that creates the files, because the shared texts of `code-work` and `safe-git` must not name a module that may not be installed.

## Scope

- A read-only `record-paths <document>` command of `review-engine` that prints the project-relative paths of the files that make up the review of the document, in a form the agent can pass to `wb run safe-git commit`.
- Its declaration in `module.json`, its row and conformance item in `docs/specs/review-engine.md`, and tests.
- A step in the module's `peer-review` skill that says when to run it and to name its files in the commit that completes or closes the reviewed plan.

## Non-goals

- Any change to `code-work`, `safe-git`, `commit-changes` or `docs/plans/README.md`.
- Letting `safe-git commit` accept a directory.
- Committing anything in knowledge-base, or refreshing the installed copies of the module in any project. Those are the owner's step after this plan (see Deferred work).
- Any change to what the engine writes, to the seal or to the state format.

## Assumptions and constraints

- The files of a review are exactly the ones the spec lists. `record-paths` derives them from the validated state, not from the directory: `state.json`, `ledger.md` and `schema.json` when each exists as a regular file, and `round-<n>.json` only for a round the state names. A file in the directory that the state does not name is never listed.
- The command writes nothing and changes no file outside the review's directory, as every command of the engine (spec, "Commands").
- It prints one JSON object on standard output, as the other commands do, and refuses with a `refused:` line when there is no review of the document.
- The command is read-only, so it takes no owner level and needs no entry under `owner` or `levels` in `module.json`.
- The module's skills are rendered into a project only where the module is installed.
- Reaching an installed project needs the module to be refreshed there; this plan does not do it.

## Completion criteria

1. `wb run review-engine record-paths <document>` prints the review's existing files as project-relative paths, and refuses a document with no review, a closed or unsealed one excepted (it only lists files).
2. The command is declared in `module.json`, and the module's declaration test passes.
3. `docs/specs/review-engine.md` lists the command and a conformance item for it.
4. The `peer-review` skill tells the agent to include those files in the commit that completes or closes the reviewed plan, and the skill test passes.
5. Nothing outside `packages/workbench/review-engine/` and `docs/specs/review-engine.md` is changed.

## Increments

### Increment A — The `record-paths` command

**Outcome:** `wb run review-engine record-paths <document>` lists the files of the review of a document, and nothing else changes.
**Dependencies:** none.
**Affected areas:** `packages/workbench/review-engine/helper/review-engine`, `packages/workbench/review-engine/module.json`, `packages/workbench/review-engine/tests/` (a new test file for the command, and the declaration test where it counts the arguments), `docs/specs/review-engine.md`.
**Steps:**
1. Write the tests first (`test-first`): a review with two rounds lists `state.json`, `ledger.md`, `schema.json`, `round-1.json` and `round-2.json` in a fixed order; a review with no round lists the three files that exist; a document with no review is refused; a syntactically valid `round-<n>.json` that the state does not name (for example `round-999.json`) is not listed; any other extra file is not listed; a link in the directory is not followed or listed; a round the state names whose file is missing is not listed; the command writes nothing.
2. Add the command to `helper/review-engine`: resolve the document and load its state as `status` does, check each wanted file through the kit's no-follow file layer, and print `{"document": ..., "paths": [...]}` built from the key and the state's round entries. Add it to the argument shape check (one argument after the command).
3. Add `record-paths` to the `arguments` of the `review-engine` command in `module.json`.
4. Edit the spec: add the row to the commands table; add `record-paths` to the list of arguments in the Declaration section, saying it takes one document and is read-only and agent-safe, as `convergence` is; correct the counts of arguments in the spec's built-by notes (fourteen becomes fifteen); and add a conformance item that a review's committed files are listed from its state and nothing else.
**Verification:** the new test file, `test_review_module.py` and `test_review_commands.py` (the command declaration and the argument shapes). The change adds a branch to the command dispatch, which the rest of the engine's tests reach, so the other `test_review_*` files are not rerun unless one of these fails.
**Evidence:** one local commit, with the trailer `Plan: 2026-11-07-review-record-paths#A`.

### Increment B — The skill tells the agent to commit the record

**Outcome:** the `peer-review` skill says to run `record-paths` and name its files in the commit that completes or closes the reviewed plan.
**Dependencies:** A.
**Affected areas:** `packages/workbench/review-engine/harness/neutral/skills/peer-review/SKILL.md`, the skill test in `packages/workbench/review-engine/tests/test_review_module.py`.
**Steps:**
1. Write the test first: the skill text names `record-paths`, says the files go in the commit that completes or closes the plan, and says to pass them one by one because a directory is not accepted.
2. Add one numbered step after the decisions step, and a line in Rules, in the skill's own words: when a review of a plan exists, run `wb run review-engine record-paths <plan>` after the last `decide` and again just before the commit that completes the plan, and name every path it prints in that commit; a state edited after the commit that holds it is a change to commit.
3. Keep the text free of any name of `code-work` or `safe-git` beyond the `wb run safe-git commit` command that the sibling skills already name.
**Verification:** `test_review_module.py` (the skill checks) and the neutral-tree checks it runs. No other test reads this skill's text.
**Evidence:** one local commit, with the trailer `Plan: 2026-11-07-review-record-paths#B`.

## Verification for the plan as a whole

Increment A's tests stand after B unless B changed the helper or `module.json`, which it does not. The one rerun is `test_review_module.py`, which both increments touch, after B. The full suite is not run: the change adds one read-only command and one skill step, and the engine's other behaviour is not touched. What could break outside the tested area: a project that renders `review-engine`'s skills with a checker that counts the module's arguments or steps (the installer's tests of rendered modules). If the owner wants that checked, `tests/test_doctor.py` and the install tests are the ones to run, and the owner decides.

## Risks and sensitive actions

- The command reads a directory of the project. It uses the same no-follow file layer as `status`, lists only fixed names, and prints paths built from the document's key, not from directory entries, so a hostile name in the directory is neither printed nor followed. This touches the filesystem; the owner may ask for `security-review` of it.
- The skill step adds an instruction an agent will follow. It tells the agent to commit files it did not itself edit in that session, which is what the spec intends; the owner reads the commit's paths in the helper's one-line output.
- Installed copies, including knowledge-base's, do not change until the module is refreshed there. That is outside this plan.
- The module has a shipped approval record (`workbench/shipped_approvals/`). Changing the helper, `module.json` or the skill makes that record stale, as the spec says of earlier plans, until the owner releases it again. This plan does not release it; the owner does, and until then a check of shipped approvals (`wb doctor`) may report the stale record.

## Review record

Round 1, 2026-11-07, `review-engine` with the `ask-codex` bridge, profile `standard` (model `gpt-5.6-terra`); verdict `changes_needed`, two major findings.

- R1-F1 (major) — the file list came from directory names, so a stray `round-999.json` could be listed and committed. **Applied:** the list is built from the validated state, `Assumptions and constraints` and Increment A steps 1 and 2 say so, and a test covers an unreferenced round file.
- R1-F2 (major) — the spec's Declaration section, which lists every argument, was not in the plan's edits. **Applied:** Increment A step 4 now edits that list, the counts in the built-by notes, the table and the conformance items.
- Found while checking, not by the reviewer: the module's shipped approval record goes stale when the package changes. **Applied:** added to `Risks and sensitive actions` and to `Deferred work` as the owner's step.

A second round has not been asked for.

## Deferred work

- Release the new shipped approval of the `review-engine` package, then refresh the installed module in knowledge-base and in this repository, and commit knowledge-base's two untracked review directories. The owner's steps, after this plan is done.
- If an agent still omits the files because the skill is not in mind at commit time, add an optional hook to `commit-changes` that asks installed modules for paths. That is a cross-module design and needs its own plan or decision.

## Result

### Increment A — done and committed

- **Changed:** `helper/review-engine` (`record_paths`, its dispatch, the usage text and the argument shape), `module.json`, the new `tests/test_review_record_paths.py` (14 tests), `tests/test_review_module.py` (fifteen arguments, and a temporary skip of `record-paths` in the skill-mentions-every-argument test, which increment B removes), and `docs/specs/review-engine.md` (Declaration list, commands table, a "Record paths" subsection, the argument count, conformance item 15).
- **Verification as run:** from `packages/workbench/review-engine/tests`, `python3 -B -m unittest test_review_record_paths test_review_module test_review_commands`: 60 tests, OK. Before the helper change 10 of the 13 tests then written failed with the usage refusal. Not run: the other `test_review_*` files, the installer's tests of rendered modules, `wb doctor`.
- **Review:** one reviewer round, no blocking finding. Applied: a test that a closed review still lists its files. Not applied: a `ledger.md` or `schema.json` over 4 MiB is left out of the list without a message; the engine's own bound on those files was not checked, so it is an accepted limit and not a claim that it cannot happen.
- **Deviation:** the plan's A verification names `test_review_module.py`, which requires the skill to mention every argument, so A needed the temporary skip above; B removes it.
- **Gate:** the shipped approval of the package goes stale at every edit under `packages/workbench/review-engine/`, and the gate then refuses every tool call until the owner releases it. This cost many releases in A and will in B.
- **Security review:** recommended to the owner once for the surface (a directory read in the project); the owner declined it, 2026-11-07, accepting the risk. The reviewer of the increment found no concrete exposure.

### Completion, 2026-11-07

Both increments are committed (A `decd897`, B `52405ba`). Completion criteria:

1. `record-paths` lists the review's existing files from its state and refuses a document with no review; a closed or unsealed review is listed. Evidence: `tests/test_review_record_paths.py`, 14 tests, OK.
2. It is declared in `module.json`. Evidence: `test_review_module.py`, with `test_review_commands.py`, 61 tests with the other file, OK.
3. The spec lists it: Declaration arguments, commands table, "Record paths", the count, conformance item 15 (commit `decd897`).
4. The `peer-review` skill tells the agent to name its files in the commit that completes or closes the plan. Evidence: the step 7 test, in the same 61.
5. The two commits changed only `packages/workbench/review-engine/`, `docs/specs/review-engine.md` and this plan. The `workbench/shipped_approvals/` files that the owner's releases wrote are outside both commits.

Whole-plan verification: B changed no input of A's tests, which ran again inside B's run (61 tests, OK), so nothing else was rerun. Not run: the other `test_review_*` files, the installer's tests of rendered modules, `wb doctor`. Left to the owner, outside this plan: release the shipped approval for the final tree and commit the `shipped_approvals` files, refresh the installed `review-engine` in this repository and in knowledge-base, and commit knowledge-base's two untracked review directories. In this repository the review directories are excluded locally (`.git/info/exclude`), so its own plans' reviews are not tracked here.

### Increment B — done and committed

- **Changed:** `harness/neutral/skills/peer-review/SKILL.md` (a new step 7: run `record-paths` after the last `decide` and again just before the commit, and name every path it prints in the commit that completes or closes the plan, one file at a time) and `tests/test_review_module.py` (the temporary skip of A removed, a test of the step's phrases, and `record-paths` added to the commands the skill is expected to run).
- **Verification as run:** from `packages/workbench/review-engine/tests`, `python3 -B -m unittest test_review_module test_review_record_paths test_review_commands`: 61 tests, OK. The two tests of the step failed first; a first draft of the text then failed three (it named `safe-git`, which an existing test forbids; a phrase differed in case; the expected-commands set lacked `record-paths`), and the text and that set were corrected. Not run: the other `test_review_*` files, the installer's tests of rendered modules, `wb doctor`.
- **Review:** one reviewer round, no blocking finding. Not applied: the plan's "line in Rules" was dropped, because step 7 carries the whole instruction (a deviation from step 2 of the plan); the step reads as plan-only on purpose; the last sentence of the step is vague, but repeats the plan's wording and "again just before that commit" carries the instruction, and each package edit costs the owner two releases. Known, not new: the skill is read when a review is asked for and the commit comes later (the hook under Deferred work), and `commit-changes` says to commit paths changed for the work, which the review's files are, since the engine writes them while the work is reviewed.
