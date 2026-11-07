# Tell the peer-review skill to name only the files of a review that are new or changed

Status: Proposed
Created: 2026-11-07
Candidate: none (a correction that follows from a finding: on 2026-11-07 the commit helper refused the unchanged files that step 7 of the peer-review skill says to name)
Specs: review-engine

## Goal

After this plan, step 7 of the `peer-review` skill no longer tells an agent to name every path that `record-paths` prints. It tells the agent to name the printed paths that the repository's status lists at all, whatever its code, and to leave out the others, and says how to read that status. It no longer depends on the commit helper's refusal. The command, the helper and the state format do not change.

The finding. Step 7 (plan `2026-11-07-review-record-paths`) says "name every path it prints in the commit that completes or closes the plan". `wb run safe-git commit` refuses a named path that has no change. On 2026-11-07, committing the roadmap with the files of its third review round, naming all six printed files was refused: `refused: staging did not give exactly the named paths (no change: …/round-1.json, …/schema.json …; extra: none); the named paths were unstaged`. The refusal text is cut at about 200 characters, so it does not always list every unchanged path. Only `state.json`, `ledger.md` and the new `round-2.json` and `round-3.json` had changed. The step is right for a review that no commit holds yet and wrong for one that an earlier commit already holds, which is the common case when a document is reviewed again.

## Scope

- `packages/workbench/review-engine/harness/neutral/skills/peer-review/SKILL.md`: the text of step 7, and the closing rule of the skill, which gains the one read-only command that the step uses.
- `packages/workbench/review-engine/tests/test_review_module.py`: the test that pins step 7 (`test_it_says_to_commit_the_files_of_the_review_with_the_plan_it_completes`).
- `docs/specs/review-engine.md`: the passage "Record paths", which says the command prints "the files to name", gets one sentence that the commit names the new or changed ones.

## Non-goals

- Any change to `record-paths` (what it prints, its object, its tests), to `safe-git commit` or its refusal text, or to the engine's state.
- Making `record-paths` say which files changed. That needs the repository's index, which the helper does not read; it would be its own plan and the owner's choice. The skill uses the repository's status instead, which an agent already reads before every commit (`commit-changes`, step 2).
- Any change to the decision `2026-11-07-review-records-are-committed-with-the-project`: it says the commit holds the files of the review and the files that changed are exactly those; this plan words the skill's step to match.
- The installed copies in this project and the rendered skill: the upgrade and the rerender are the owner's steps after the release.

## Assumptions and constraints

- Which files of a review a commit must hold is a fact of the repository, so the step reads it from there. Just before the commit, the agent runs `git status --short -- <the paths that record-paths printed>` (a read-only command, which the `commit-changes` skill already has an agent run) and names the printed paths that it lists, whatever the two-letter code (`??` new and untracked, ` M` modified in the work tree, `M ` modified and staged, `A ` added, `MM`, `AM` and the others), and no others: a path that `git status` does not list is clean, tracked and unchanged, and the commit helper refuses it. A review file is never deleted or renamed by the engine, so those codes are not expected; if one appears, the agent stops and tells the owner. This does not depend on the helper's refusal text, which is cut at about 200 characters and so can hide an unchanged path. What usually changes, from the design of the review (`docs/specs/review-engine.md`, "State"), is stated as an explanation and not as the rule: a round adds `round-<n>.json` and rewrites `state.json` and `ledger.md`; `schema.json` is written when the review begins and the earlier round files are never rewritten; a review that no commit holds yet has all of its files new.
- The wording, the agent's proposal: "name only the printed paths that `git status --short -- <those paths>` lists, whatever the code (untracked, modified, staged or added), run just before the commit; a printed path it does not list is clean, tracked and unchanged, and the commit helper refuses it. Usually that is `state.json`, `ledger.md` and the rounds added since the last commit; all of them for a review that no commit holds yet." The phrases `wb run review-engine record-paths <document>`, `in the commit that completes or closes the plan` and `a directory is not accepted` stay, and the test keeps them. The skill's closing rule, "Use only reading, searching and editing of other files, `wb settings` and the commands above", gains "and `git status --short` over the files of a review".
- The module's tree changes, so the release approvals, the removal of stale shipped records after the owner approves the list, the upgrade and the rerender are the owner's. The increment is built and tested in a scratch clone and copied by the owner's script, as before. Nothing is pushed without the owner's word.
- The skill text is pinned by `test_review_module.py` and by the tests that read every skill; the old phrase "name every path it prints" is replaced in the test by the new one, and the test also asserts the old phrase is gone.

## Completion criteria

1. Step 7 of the shipped `peer-review` skill says to name only the printed paths that `git status --short` over them lists, whatever the code (untracked, modified, staged or added), says to run it just before the commit, says that a printed path it does not list is clean and is left out, and says what usually changes; its closing rule allows that command over the files of a review; it no longer says "name every path it prints".
2. The test pins the new phrases and fails if "name every path it prints" comes back.
3. `docs/specs/review-engine.md` ("Record paths") says the same in one sentence.
4. The module's tests pass apart from any failure the unchanged tree already has, and `wb run code-work check` passes.

## Increments

### Increment A — Reword step 7 and pin it

**Outcome:** completion criteria 1 to 4 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/review-engine/harness/neutral/skills/peer-review/SKILL.md`, `packages/workbench/review-engine/tests/test_review_module.py`, `docs/specs/review-engine.md`.
**Steps:**
1. Write the test first, in a scratch clone: the new phrases (`git status --short`, `whatever the code`, `just before the commit`, `tracked and unchanged`) are in the skill text, and the text names an untracked, a modified and a staged file as cases to name; "name every path it prints" is not; the three kept phrases still are; the closing rule names `git status --short`. See it fail.
2. Reword step 7.
3. Add the sentence to "Record paths" in the spec. Search the repository for another description of step 7 (`docs/development.md`, other skills) and report one that disagrees.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_review_module.py` and the rest of the `review-engine` module suite, run as `python3 -I -B` on the module's tests; the tests that read every skill of the repository; `wb run code-work check`. Not run: the whole suite (no code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-07-review-record-paths-name-changed-files#A`, and the files of this plan's own review if one is asked for.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether an agent names the right files on its next review is for the owner to see.

## Risks and sensitive actions

- A skill is behaviour: a wrong sentence would make an agent leave out a changed file of a review, which `git status` would show as untracked or modified afterwards. The step keeps "and again just before that commit, run `record-paths`", and reads the status in the same moment, so both lists are of the moment of the commit. A review file that the status lists, in any state, is named; one it does not list is not named.
- A package file changes: the release approvals, the stale-record removal, the upgrade and the rerender are the owner's. Nothing is pushed without the owner's word.
- No security review is suggested: the change is the text of a skill and of its test.

## Review record

Codex, plan review, 3 rounds of 3 (the bound); converged with no meaningful finding in round 3. Models: `gpt-5.6-terra` for rounds 1 and 2, `gpt-6.1-sol` for round 3.

- Applied (round 1, major): taking out the paths named in the commit helper's refusal is not reliable, because the refusal text is cut at about 200 characters. The step now selects the files by the repository's status, read just before the commit, and the skill's closing rule and its test gain that one read-only command.
- Applied (round 2, major): the rule listed only the work-tree codes, so a review file that is already staged would be left out. The step now names every printed path that `git status` lists, whatever its code, and leaves out only the paths it does not list; the test pins an untracked, a modified and a staged case.
- Rejected (round 2, minor): the status line of the accepted decision `2026-11-07-review-records-are-committed-with-the-project` names the owner by git identity. That is the convention of `docs/decisions/README.md`, with the no-reply address that every commit of the project already carries; it is not a defect of this plan and the record is accepted.
- Left for the owner: nothing from the review.

## Deferred work

- A `record-paths` that marks each file new, changed or unchanged by reading the index, so that no judgement is left to the agent.
- The refusal text of the commit helper is cut at about 200 characters, so it can hide unchanged paths. That is a change to `safe-git`.

## Result

Empty until work starts.
