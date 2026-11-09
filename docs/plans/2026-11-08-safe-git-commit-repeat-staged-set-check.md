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

**Increment A (2026-11-08), done in a scratch clone at commit `9e84d0a`; the two specs are edited in the live tree; the package files are not yet copied, released or committed.**

- Built: in `packages/workbench/safe-git/helper/safe-git`, a function `_expect_staged_set(root, expected, when=None)` that refuses unless the index holds exactly the paths expected, with the refusal "staging did not give exactly the named paths[ <when>] (no change: ...; extra: ...)". `command_commit` uses it twice: where the inline check was (no `when`, so the text is byte for byte the old one), and again as the last check before the `git commit` command is built, after the second head check and the second digest comparison, with the words "just before the commit". The expected set is the same expression in both, the paths already staged and the named paths. It applies with and without a digest and with and without `--leave-other-staged`; the refusal goes through the existing handler, so the named paths are unstaged, and an extra path stays staged.
- Tests, written first (class `ExtraStaged` in `test_safegit_digest.py`, six tests; a stand-in `git` stages `extra.txt` once at a chosen moment): on the unchanged helper the tests of criterion 1 failed because the extra path was committed ("the commit ... holds a.txt, extra.txt, not the named paths; nothing was undone"). Now: refused, nothing committed, the named paths unstaged and `extra.txt` still staged, when it is staged just before the cached whitespace check, at the second head check or at the second digest comparison, with a digest; at the first two without a digest; and with `--leave-other-staged` (criterion 1). Staged at `git commit` itself, the commit is made and reported afterwards, exit 1, "nothing was undone" (criterion 2: the window that stays, tested). Staged just before `git add`, the first check still refuses it in its old words and not the new ones. A normal commit is not refused. One error of mine in the tests was corrected: the stand-in's marker from one iteration made the next fire early, so it now clears its markers at each use.
- Verification as run, on the final files (helper `155d855a…`, test file `f3831adc…`): the whole safe-git module plus `tests.test_rendering`, `tests.test_permissions_drift` and `tests.test_rerender`, 885 tests, OK (criterion 3). A mutation pass of 8 mutants killed all 8 (criterion 4): the repeated check removed, expecting only the named paths, without the words for the moment, only with a digest, only without `--leave-other-staged`, looking only for extra and not missing paths, moved next to the first check, and the first check removed; the last survived the first time, which added the test of the path staged before `git add`. `wb run code-work check` passes (criterion 6). Not run: the whole repository suite; nothing outside the module reads the refusal text.
- Review: the `reviewer` agent, 2 exchanges (cap 6), no blocking finding in the end. The first reply called the repeated check missing from the helper, a blocking finding; it had read the helper while my mutation pass was rewriting it, with the check removed in the mutant under test. I restored and checked the file (the function at line 846, calls at lines 1100 and 1109), and the second reply withdrew the finding after reading the restored file, and confirmed the placement, the expected set in both modes, that the first check's text is unchanged, that the repeated check adds no new way to refuse a legitimate commit, the stand-in positions and that the refusals cannot come from the first check, and the spec text. Not applied, cosmetic: the docstring of the stand-in, and the cleanup of a `subTest` loop that is skipped after a failed assertion (it only adds noise to a failure already reported). The reviewer ran nothing. The one new refusal, noted by the reviewer and accepted: a legitimate writer that stages another file in that stretch now gets a refusal where its file would have been included.
- Specs: `docs/specs/safe-git.md` now describes one window, the milliseconds between the last two checks and git's lock, says where each check is made, and records that the check of the staged set ran once before this plan and the stretch for another path was the whole run of git programs to the commit; `docs/specs/action-review.md` says the same in one sentence. The private index file or held lock stays unbuilt.
- Security second look (criterion 5): asked of the owner once, with the concrete risk (the index and a subprocess, in the helper that makes every commit), and run on the owner's word ("Run the second look") by the `security-reviewer` agent on 2026-11-08, on copies of the live fixed files (helper `155d855a…`, test file `f3831adc…`; both hashes confirmed by the reviewer), with Apple Git 2.54.0. No Critical or High finding, and the reviewer found nothing that must be fixed before this increment is committed. Tested: the six `ExtraStaged` tests fail on the old helper in every position (the extra path is committed and reported, "nothing was undone") and pass on the fixed one (refused "just before the commit ... extra: extra.txt", the named paths unstaged, HEAD holding only `a.txt`); 247 tests of `test_safegit_digest`, `test_safegit_commit`, `test_safegit_describe_commit` and `test_safegit_git` pass, so exit codes, output, `describe` and the report after the commit are unchanged; a clean run gives the same JSON and an empty standard error; the listing `git diff --cached --no-renames --name-only -z` shows a plain staged file, a mode-only change, a `git rm --cached`, a skip-worktree or assume-unchanged entry, an unmerged entry, an entry under a symlinked directory and a rename (both names); a decomposed (NFD) name is listed under a different spelling and so refused (fails closed); an intent-to-add entry is not listed and is not committed either (a false "rest of the index is not as it was" after the commit at worst); `_unstage` resets only the named paths and only while HEAD is unchanged, and nothing new is started (the check reuses the allowed shape). Findings: **Medium (older than this fix, shared by the first check and by the report after the commit)**: `git diff` and `git diff-tree` honour `diff.ignoreSubmodules` and an `ignore = all` of an untracked `.gitmodules` in the work tree, so a gitlink staged by a writer of the index is absent from the listing, and `git commit` commits it; reproduced end to end (the success JSON named only `a.txt` while HEAD held a `160000` entry, when the entry was removed from the index again before the report); the payload is a gitlink and not file content; the reviewer's smallest correction is `--ignore-submodules=none` on the cached diff and on `diff-tree` (tested to make the entry visible), which means loosening two fixed command shapes, or comparing `ls-files -s -z` before and after and reading `ls-tree -r -z HEAD` after the commit (read only, shapes already allowed). **Low**: the new check runs after the second digest comparison, so a named path restaged during its own git run is committed and, with a digest, reported afterwards; the window is the length of that last git run, of the same kind as the recorded residual; no test fires at that call (the reviewer's correction: take the set and the blob ids from one snapshot, or record it). Older, stated plainly by the reviewer: with no digest nothing detects a content change of a named path in the stretch, and with `--leave-other-staged` the commit takes the named paths from the work tree at commit time. Not checked: case variants on a case-insensitive filesystem by experiment, other git versions, the real timing of the windows. Decisions: none of it is fixed here, as the plan's non-goals allow only the repeated check; the two limits are recorded in `docs/specs/safe-git.md`; the gitlink blind spot and the single-snapshot idea are for the owner to take into a follow-up plan or leave recorded.
- Left for the owner: whether to open a follow-up plan for the gitlink blind spot (and the single snapshot); "commit a" (the copy, the release approvals and the removal of the two stale records were done on 2026-11-08: the live helper and test file have the hashes above, and `wb verify packages/workbench` reads `safe-git` at tree `93495935b38b`); after the commit the acknowledge, the upgrade and the rerender.
