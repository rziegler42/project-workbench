# Stop the engine's secret scan flagging the hashes in the install manifest and the release records

Status: Proposed
Created: 2026-11-06
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The `no_secret_lines` check of the action-review engine no longer declines a commit only because it adds or changes the 64-character tree and declaration hashes that the installer writes into `.workbench/manifest.json` and into the shipped release records `workbench/shipped_approvals/packages/<hash>/approval.json`. After this plan the long-random-token test is skipped for exactly those two kinds of file, as it already is for lock files, while every one of the 15 patterns still runs on them and every other file is scanned as before. A test fails if either exemption widens beyond those paths or if a pattern stops running on them.

The reason is measured. On 2026-11-06, scanning the diffs of the last 40 commits of `main` with the engine's own scan section, 17 would be declined, every one with the first-hit kind `long_hex`, and every one in a file of those two kinds; the other 23 commits were clean. The hashes are public package hashes, but the check treats a bare 64-hex value as a secret unless its line names a checksum, and `tree_hash` and `declaration_hash` do not count as naming one (the word-boundary test does not see `hash` after an underscore). The owner's report of the same day counts 61 reviewed commits that the hook never collects, all declined for `no_secret_lines`, which cannot be labelled, so the commit false-decline rate the cutover reads cannot see them.

## Scope

- `packages/workbench/action-review/helper/action-review`: the per-file scan options (`_scan_options`) and the constants beside `LOCKFILES` and `TEST_DIRECTORIES`: an exact path `.workbench/manifest.json`, and a path of the form `workbench/shipped_approvals/packages/<64 lowercase hexadecimal characters>/approval.json`, skip the entropy test only.
- `packages/workbench/action-review/tests/test_actionreview_checks.py`: tests of the two exemptions, of the look-alike paths, and of the patterns still running.
- `docs/specs/action-review.md`: the sentence of "As built, and its limits" that lists the scan's exemptions (near line 930), and the `no_secret_lines` row of the check table if it needs a clause.

## Non-goals

- The 15 patterns, the entropy rules themselves, the lock-file and test-directory options, and the credential names.
- Widening the checksum context to key names such as `tree_hash` (option B of the discussion), which is easier to spoof and covers more than these two file kinds.
- The shipped test set (`tests/dangerous-cases.json`) and its count of 29, which the report pins; no case is added to it, so the owner's report and test-set run are not invalidated by this plan.
- The shadow hook's own redaction list, `safe-git push-check`'s scan, the report, the labels and the store.
- The other causes of a secret decline. This plan removes one measured cause and does not claim the 61 are all of it.
- Any change to what the verdicts of earlier commits say. Rows already in the store stay as they are.

## Assumptions and constraints

- The path the scan reads is the one in the `describe` diff's `--- HEAD/<path>` header, relative to the repository root, as for the lock-file and test-directory options. A diff whose shape the section parser does not understand is scanned as a whole with no option, so an exemption cannot be claimed by a malformed diff; the existing test that a header-like line inside a hunk changes no option is kept and extended to the new paths.
- The exemptions are by exact path shape, not by file name alone: `.workbench/manifest.json` only at the repository root, and `approval.json` only as the single file directly in a directory directly under `workbench/shipped_approvals/packages/` whose name is exactly 64 lowercase hexadecimal characters, the form of every release record (the hash is the record's directory name). A file of the same name elsewhere, or under a directory with any other name, is scanned as before. In a project that does not hold shipped records the second shape never matches.
- A hit used to withhold the diff from anything sent to a bridge. After this change the diff of these two file kinds can reach the model, which is acceptable: they hold public hashes and the patterns still run on them first.
- This plan changes the engine, so the verdicts of later commits differ from earlier ones. Labels made before the upgrade were made against the old engine; the plan records this and changes none of them.
- The engine the hook starts is the installed copy under `.workbench/`, so the change reaches the shadow only after the release approvals, the acknowledge, the upgrade and the rerender, which are the owner's.
- The edit is made and tested in a scratch clone and copied by the owner's script, as in the earlier plans. Tests run with `python3 -B` through a runner that puts the clone first on the search path.

## Completion criteria

1. A diff of `.workbench/manifest.json`, or of `workbench/shipped_approvals/packages/<64 lowercase hex>/approval.json`, that contains only 64-hex tree and declaration hashes and ordinary JSON passes `no_secret_lines`; a secret that one of the 15 patterns finds in either file (an AWS-shaped key, a private-key header) still gives the kind `pattern`.
2. Look-alike paths are scanned as before and the same 64-hex value is still `long_hex` in each: `sub/.workbench/manifest.json`, `workbench/shipped_approvals/approval.json`, `workbench/shipped_approvals/packages/a/b/approval.json`, `workbench/shipped_approvals/packages/a/other.json`, `other/approval.json`, and a single-segment path whose directory is not a 64-lowercase-hex name (`workbench/shipped_approvals/packages/not-a-hash/approval.json`, the same with 63 and with 65 hex characters, and the same with an uppercase hex digit).
3. A diff of unknown shape is scanned whole with no exemption, and a header-like line inside a hunk of another file changes no option.
4. The existing scan tests (digest context, lock files, test directories, each file under its own options, the spoof and shape tests) still pass, and the tests that read the shipped test set still see 29 cases that decline as they do now.
5. The spec states the two exemptions and the residual risk, and `wb run code-work check` passes.

## Increments

### Increment A — Skip the long-token test for the manifest and the release records

**Outcome:** completion criteria 1 to 5 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/helper/action-review`, `packages/workbench/action-review/tests/test_actionreview_checks.py`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first, in a scratch clone, beside the lock-file tests: the manifest and a release record at a 64-lowercase-hex directory with a 64-hex value pass; the same value in each look-alike path of criterion 2 is `long_hex`; an AWS-shaped key in either exempt path is `pattern`; a mixed diff of an exempt file and another file reports the other file's hit; a diff of unknown shape that names an exempt path is scanned whole; and one test through the real `checked(...)` path with a new `.workbench/manifest.json` of hashes. See them fail with the present code.
2. Add the constants and extend `_scan_options` so that `entropy` is false for the lock files and for the two exact path shapes, and nothing else changes. Keep the helper's imports and its pinned words as they are.
3. Edit the spec's exemption sentence and, if the table row needs it, the `no_secret_lines` row. Search the repository for another description of the scan's exemptions (`docs/specs/safe-git.md`, `docs/development.md`, the module's skill and README); report one that disagrees and change it only if it states the old list.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_actionreview_checks.py`, and the module's rule, bridge, module and pin tests (`test_actionreview_rules`, `test_actionreview_bridge`, `test_actionreview_module`, `test_actionreview_pins`) and the test that reads the shipped test set, run as `python3 -B` through the runner; then `wb run code-work check`. Not run: the whole repository suite, the shadow hook and report tests (neither imports the helper), and the test-set runner against a real model. After the owner's steps, the agent can scan the recent commits again with the same read-only script and report how many would now be declined.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-secret-scan-skips-hash-records#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether the 61 uncollectable commits in the owner's store fall is for the owner to see in the report after the upgrade, as new commits are made; the plan does not claim a number.

## Risks and sensitive actions

- This touches the secret scan, a security-relevant surface. The change removes a check for two named file shapes: an unlabelled hex secret placed in `.workbench/manifest.json` or in a release record would pass the long-token test (the 15 patterns still run on it). The backstops are GitHub push protection on the owner's repository, `safe-git push-check` before any push, the model's review of the diff, and the owner's own prompt at the shadow stage. The paths are exact, which the look-alike tests pin.
- The change is to the engine the hook starts, which is shadow-only today: it decides nothing and the owner still sees the normal prompt.
- A package file changes: the release approvals, the removal of the stale shipped records after the owner approves the list, the acknowledge, the upgrade and the rerender are the owner's. Nothing is pushed without the owner's word.
- No new network, subprocess or filesystem write by code is added. The owner was asked once whether to run a security review of this change and has not asked for one; the `security-reviewer` agent can run one on request.

## Review record

Codex (`gpt-5.6-terra`), plan review, 2 rounds of 3, converged with no meaningful finding in round 2.

- Applied (round 1): the release-record shape accepted any single directory name under `workbench/shipped_approvals/packages/`, wider than the goal's "hash records", so a file such as `.../not-a-hash/approval.json` could have skipped the long-token test. The directory name must now be exactly 64 lowercase hexadecimal characters, the form of every release record, in the scope, the assumptions and criteria 1 and 2; the look-alike tests add a non-hash name, 63 and 65 characters and an uppercase digit.
- Rejected: none. Left for the owner: nothing from the review.

## Deferred work

- The other causes of a secret decline, if the owner's report after the upgrade still shows many: a look at `facts_complete` (truncated diffs), at the 15 patterns on prose, and at a non-secret handle in the verdict row so that a secret decline can be inspected and labelled without the secret entering the store.
- A way to revisit a label in `label.py`, and the owner's question whether the earlier removal labels reflect the stance on approval records.

## Result

Empty until work starts.
