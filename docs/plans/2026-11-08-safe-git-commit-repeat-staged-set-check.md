# Repeat the check of the staged set just before `safe-git commit` takes the index

Status: Proposed
Created: 2026-11-08
Candidate: workbench-v1#action-review-engine
Specs: safe-git, action-review

## Goal

Close the larger part of the window that the security review of the state digest found (finding M1 in the Result of plan
`2026-11-08-safe-git-commit-state-digest`, increment D). `safe-git commit` checks once, after `git add`, that the index holds exactly the
named paths plus the paths that were already staged. It then runs the cached whitespace check, the head check and the second digest
comparison, and then `git commit`, which takes the whole index. A process with write access to the index that stages another file in that
stretch gets the file committed: the digest comparison does not see it, because it covers only the named paths. The commit then exists and
`commit` reports that nothing was undone.

The plan is done when `commit` repeats the check of the staged set as its last check before `git commit`, so that the stretch in which an
extra staged path goes unseen is the few milliseconds between that check and git's own lock, as the specs already say of a changed named
path, and the specs say so accurately. The window that remains is not closed by this plan.

## Scope

- In `packages/workbench/safe-git/helper/safe-git`, `command_commit`: after the second head check and the second digest comparison, and
  immediately before the `git commit` command is built and run, read the staged set again (`names(root, cached=True)`) and refuse with the
  same refusal as the first check, marked as made just before the commit, when it is not exactly the paths that were already staged plus the
  named paths. The refusal unstages the named paths as every refusal in that block does. It applies whether or not a digest is given and
  whether or not `--leave-other-staged` is given.
- Tests, in the module's test files, written first: a stand-in `git` that stages an extra path when it is run with the chosen subcommand, in
  each position of the stretch the review named (during the cached whitespace check, during the second head check, during the second digest
  comparison), shows the commit refused and nothing committed; a stand-in at `commit` itself shows the residual (the commit exists and is
  reported, as for a named path today); the existing tests of the first check and of the digest still pass.
- `docs/specs/safe-git.md`, "The state digest" and the passage on the commit's checks, and the sentence in `docs/specs/action-review.md`
  that repeats the windows: the two windows become one, and say what is checked where.
- An independent read of the fix by the `reviewer` agent, and an offer of a security second look: the security-review method asks that a fix
  to a flaw get one, and this change touches the index and a subprocess. The second look runs only on the owner's word, asked at that point
  with the concrete risk; the owner's approval of this plan is not that word. If the owner asks for it, the `security-reviewer` agent retests
  the scenario of finding M1 on a copy and tries to walk around the new check.

## Non-goals

- A private index file (`GIT_INDEX_FILE`), a held lock, or any change that makes the check and the commit one atomic step. Either would
  change how `commit` stages and what it reports, and is a larger plan if the owner wants it. The window of a few milliseconds stays and is
  shown afterwards by the comparison of the committed state, as now.
- Any change to the digest, to `describe`, to the engine's check, to the rule file or to the skill. The refusal is a `commit` refusal and
  `describe` cannot predict it.
- The findings L1 and L2 of the review (a hook that requires both facts to be non-null and equal): they are for the cutover plan, and
  increment E of the digest plan carries them there.
- A change to the expected-head checks.

## Assumptions and constraints

- The check of the staged set is the existing one, `names(root, cached=True)` compared with the staged paths plus the named paths; repeating
  it costs one more `git ls-files` run in a block that already runs several git programs.
- With `--leave-other-staged`, `git commit --only -- <paths>` commits only the named paths, so an extra staged path is not committed; the
  repeated check refuses in that mode too, because the staged set is the same set in both modes and a refusal is the safe direction.
- The second digest comparison reads `git ls-files -s -z` for the named paths only; this plan does not widen it, since the set check is what
  covers the other paths.
- The incident is in the module `safe-git`; its helper, tests and spec are the only files changed. The helper is pinned by the manifest and
  the package approvals, so the owner's release steps follow as for any increment of that module.
- Recalled, and not relied on: an earlier plan (2026-10-22) put a second writer in the same repository outside the threat model. The current
  specs do not say so, and the security review treated a writer of the index as an attacker class.

## Completion criteria

1. A test with a stand-in `git` that stages an extra path during the cached whitespace check, during the second head check and during the
   second digest comparison, each in turn, shows `commit` refused, no commit made, the named paths unstaged and the refusal text naming the
   extra path; each of these tests fails on the current helper.
2. A test with a stand-in that stages an extra path at the `commit` command itself shows the commit made and the helper reporting that the
   commit holds more than the named paths, as it does for a changed named path: the residual is recorded and tested, not claimed closed.
3. The existing tests of the module, in particular those of the first check, of `--leave-other-staged` and of the digest, pass.
4. A mutation pass shows that removing the repeated check, moving it before the second digest comparison, comparing only the named paths and
   dropping the already-staged paths from the expected set are each caught.
5. The `reviewer` agent has read the change and its findings are decided and recorded; the owner has been asked whether to run the security
   second look, and the answer is recorded. If the owner asked for it, the `security-reviewer` agent, given the fix and the scenario, found
   the extra path refused in the three positions and reported what it tried, and any finding it raised is decided by the owner.
6. The specs state one remaining window and say where each check is made; `wb run code-work check` passes.

## Increments

### Increment A — Repeat the check of the staged set

**Outcome:** completion criteria 1 to 6 are true.
**Dependencies:** the digest plan's increment D committed (its spec edits describe the two windows that this plan merges).
**Affected areas:** `packages/workbench/safe-git/helper/safe-git`, the module's tests (`test_safegit_commit.py`, `test_safegit_digest.py`), `docs/specs/safe-git.md`, `docs/specs/action-review.md`, this plan's Result.
**Steps:**
1. In a scratch clone, write the tests first with the stand-in of `test_safegit_digest.py` (`StandIn`, extended to stage an extra path); see criteria 1 and 2 fail or pass for the right reason on the current helper (criterion 1 fails, criterion 2 passes).
2. Add the repeated check to `command_commit`, as the last check before `git commit`, with the refusal text of the first check and the words "just before the commit"; see the tests pass.
3. Run the module's tests, then the mutation pass of criterion 4.
4. Edit the two specs; run `wb run code-work check`.
5. Ask the `reviewer` for a read of the change. Then ask the owner, once, whether to run the security second look, naming the risk (the index and a subprocess, and a change to the helper that makes every commit); run the `security-reviewer` only on the owner's word.
6. Write the Result, copy the files for the owner as in the earlier increments, and stop for the owner's release steps.
**Verification:** the safe-git module's tests; the mutation pass; `wb run code-work check`; the second look if the owner asked for it. No wider run: nothing outside the module reads the refusal text, and the engine's checks do not read `commit` refusals (`describe` is where they read).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-safe-git-commit-repeat-staged-set-check#A`.

## Verification for the plan as a whole

Increment A's recorded verification stands. Nothing is rerun beyond it.

## Risks and sensitive actions

- The change is to the helper that makes every commit of this project. A mistake could refuse every commit or, worse, let an extra path through; the tests above, the mutation pass and the reviewer's read are the guard, and the owner's release steps pin the new helper.
- A refusal that unstages the named paths leaves an extra staged path staged (the paths the attacker staged are not the helper's to unstage); that is the behaviour of the first check today and is unchanged.
- The fix does not close the window that remains. The specs say so, and the cutover plan must not describe the digest as closing it.
- A security-sensitive surface (the index, a subprocess): the plan asks the owner, once, whether to run the security second look; it does not run without the owner's word.

## Review record

- Reviewer: the project's review engine through its bridge, model `gpt-5.6-terra`, on 2026-11-08. Rounds: 2 of 3, converged (round 2 gave no meaningful finding).
- Applied: R1-F1 (major), the plan made the security second look mandatory although the project's policy is that a security review runs only when the owner asks. The look is now an offer: step 5 asks the owner once, naming the risk, and runs the `security-reviewer` only on the owner's word; completion criterion 5 and the verification are conditional on that answer; the risks section says the same.
- Rejected: none.
- Left for the owner: whether to approve the plan, and, at increment A, whether to run the security second look.

## Deferred work

- A private index file or a held lock, which would close the remaining window: larger, changes how `commit` stages, and is the owner's to ask for.
- Findings L1 and L2 of the digest review: for the cutover plan, through increment E of the digest plan.

## Result

Empty until work starts.
