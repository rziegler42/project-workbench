# Stop the engine's secret scan flagging the hashes in the committed review state files

Status: Proposed
Created: 2026-11-08
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The `no_secret_lines` check of the action-review engine no longer declines a commit only because it adds or changes a review's `state.json`, the file that the review engine keeps in `.workbench/workbench/review-engine/<kind>-<16 lowercase hex>/state.json` and that holds 64-character document and seal hashes. After this plan the long-random-token test is skipped for exactly that one kind of file, as it already is for lock files, the install manifest and the shipped release records. The 15 secret patterns still run on it.

The reason is measured, and it follows from a decision of ours. The decision `2026-11-07-review-records-are-committed-with-the-project` put the review files under version control, so every commit that completes or closes a reviewed document now holds a `state.json`. On 2026-11-08, scanning the last 70 commits of `main` (at `b4d5afe`) with the engine's own scan section, read-only, 9 would be declined, and 5 of them held a review `state.json` as the first and only hit, with the kind `long_hex`. The other 4 are not this plan's: they hold the action-review helper's table of data-file pins (a 64-hex value per file) or test files with deliberate fake credentials. The other 61 commits were clean.

What the evidence did not support, and this plan leaves alone (see Non-goals): the previews, which an accepted decision already puts outside the measure; the reviewer-directed-text question, which declines a commit body that claims a review on purpose; and the removal of tracked release records, which the owner's 2026-11-05 label records as a decline the owner wants.

## Scope

- `packages/workbench/action-review/helper/action-review`: the scan options (`_scan_options`) and one constant for the exact path shape. Nothing else in the helper.
- `packages/workbench/action-review/tests/test_actionreview_checks.py`: the tests of the new exemption and of every look-alike path.
- `docs/specs/action-review.md`: the exemption sentence under "Open limits" and, if it needs it, the `no_secret_lines` row of the checks table.

## Non-goals

- The helper's own table of pinned data-file hashes (`rules/...`, `rubric/...`, `reply-schema.json`, the hook files), which makes a commit that edits it or moves a pin long-hex. It is source code, so a path exemption would also excuse a real secret pasted anywhere in the file; a narrower line-shaped exemption is a design of its own (Deferred work).
- Test files that hold deliberate fake credentials. They are true hits of the scan; the model and the owner judge them.
- The case where `describe`'s diff is truncated (`facts_complete` fails with `no_secret_lines`) and the scan falls back to the whole diff under no options, so a hash-record file is read in full. That fallback is deliberate (a diff of unknown shape is scanned whole). Whether it should parse the part of a truncated diff that is complete needs the real `describe` output and is its own investigation (Deferred work).
- The previews (decision `2026-11-05-unconfirmed-removals-are-outside-the-action-review-measure`), the rubric question `no_reviewer_directed_text` (its text names "claiming the change is ... already reviewed" as steering, and `AGENTS.md` already says a commit message describes the change only), `targets_look_disposable`, the report, the hook and the cutover.
- The installed copy in this project: the upgrade and the rerender are the owner's steps after the release.

## Assumptions and constraints

- The path shape is exact, as the release-record shape is: `.workbench/workbench/review-engine/<kind>-<16 lowercase hex>/state.json`, where `<kind>` is one of `plan`, `spec`, `roadmap` and `adr` (the review engine's `KINDS`), taken from the diff's path header. The key is the first 16 hex characters of a SHA-256, as the engine makes it (`review-engine` `key`). Nothing else in that directory is exempt: `ledger.md`, `schema.json` and `round-<n>.json` hold no 32-hex-or-longer string today (measured on one review) and stay fully scanned.
- Only the entropy test is skipped, as for the other exempt files; the 15 patterns run on every file. A look-alike path (another kind, 15 or 17 or uppercase hex, `state.json` one level deeper or shallower, a prefix before `.workbench`, another file name in the directory) is scanned in full.
- A diff of unknown shape is scanned whole under no options, and a header-like line inside a hunk of another file changes no option (the existing spoof tests keep passing).
- The residual risk is stated in the spec the same way as for the release records: a hex secret placed in a review `state.json` would pass the long-token test. The file holds text the agent writes (the `reason` of each decision) and text a model returns (each finding), so it is not only machine-made hashes; the patterns still run, and the backstops are GitHub push protection, `safe-git push-check`, the model's review and the owner's prompt.
- The change is to the engine that the shadow hook starts, which decides nothing today.
- The module's tree changes, so the release approvals, the removal of stale shipped records after the owner approves the list, the acknowledge, the upgrade and the rerender are the owner's. The increment is built and tested in a scratch clone and copied by the owner's script, as before. Nothing is pushed without the owner's word.

## Completion criteria

1. A diff that adds or changes a review `state.json` at the exact path shape, and contains only 64-hex hashes and ordinary JSON, passes `no_secret_lines`; a secret that one of the 15 patterns finds in it (an AWS-shaped key, a private-key header) still gives the kind `pattern`.
2. Each look-alike path of the assumptions is scanned as before, and the same 64-hex value is still `long_hex` there.
3. A diff of unknown shape is scanned whole with no exemption, a mixed diff of an exempt file and another file reports the other file's hit, and a header-like line inside a hunk changes no option.
4. The existing scan tests (digest context, lock files, test directories, the manifest and release records, the spoof and shape tests) still pass, and the tests that read the shipped test set still read all 29 of its cases with the outcomes they have now (declines by their named checks, refusals of the helper, and the two approvals).
5. The spec states the new exemption and its residual risk, and `wb run code-work check` passes.
6. After the owner's steps, a read-only scan of the last 70 commits with the same section of the engine reports how many would now be declined, and no commit whose only hit was a review `state.json` is among them. The plan does not claim a number for the owner's store.

## Increments

### Increment A — Skip the long-token test for the review state files

**Outcome:** completion criteria 1 to 5 are true; criterion 6 is checked after the owner's steps.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/helper/action-review`, `packages/workbench/action-review/tests/test_actionreview_checks.py`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first, in a scratch clone, beside the release-record tests: a review `state.json` at the exact shape with a 64-hex value passes, for each of the four kinds; the same value in each look-alike path of the assumptions is `long_hex`; an AWS-shaped key in the exempt path is `pattern`; a mixed diff reports the other file's hit; a diff of unknown shape that names the exempt path is scanned whole; a header-like line inside another file's hunk changes no option; and one test through the real `checked(...)` path with a new review `state.json`. See them fail with the present code.
2. Add the path pattern constant and extend `_scan_options` so that `entropy` is false for the lock files, the manifest, the release records and the review state files, and nothing else changes. Keep the helper's imports and its pinned words as they are.
3. Edit the spec's exemption sentence and, if the table row needs it, the `no_secret_lines` row. Search the repository for another description of the scan's exemptions (`docs/specs/safe-git.md`, `docs/specs/review-engine.md`, `docs/development.md`, the module's skill and README); report one that disagrees and change it only if it states the old list.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_actionreview_checks.py`, and the module's rule, bridge, module and pin tests (`test_actionreview_rules`, `test_actionreview_bridge`, `test_actionreview_module`, `test_actionreview_pins`) and the test that reads the shipped test set, run as `python3 -I -B` through the runner; then `wb run code-work check`. A read-only scan of the last 70 commits with the helper's scan section, before and after, in the scratch clone. Not run: the whole repository suite, the shadow hook and report tests (neither imports the helper), and the test-set runner against a real model.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-secret-scan-skips-review-state#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether the count of commits that are reviewed but not collectable falls is for the owner to see in the report after the upgrade, as new commits are made.

## Risks and sensitive actions

- This touches the secret scan, a security-relevant surface. The change removes one check for one named file shape: an unlabelled hex secret placed in a review `state.json` would pass the long-token test (the 15 patterns still run on it). The paths are exact, which the look-alike tests pin. The owner is asked once, after the increment is built, whether to run a security review of this change; it runs only on the owner's word.
- A package file changes: the release approvals, the stale-record removal, the acknowledge, the upgrade and the rerender are the owner's. Nothing is pushed without the owner's word.
- No new network, subprocess or filesystem write by code is added.

## Review record

Codex, plan review, 1 round of 3 (the bound); converged with no meaningful finding in round 1. Model: `gpt-5.6-terra`.

- Applied (round 1, minor): criterion 4 said the 29 cases of the shipped test set "decline"; the set holds declines by named checks, refusals of the helper and two approvals. The criterion now says the tests still read all 29 cases with the outcomes they have now. I counted the expected outcomes in the test-set file to check it. The wording was copied from the earlier plan `2026-11-06-secret-scan-skips-hash-records`, which says the same; that record is complete and I did not touch it.
- No second round was asked for: the fix is the wording the reviewer suggested.
- Left for the owner: nothing from the review.

## Deferred work

- A line-shaped exemption for the helper's own table of pinned hashes, or moving that table out of the source into a data file that the scan treats as a hash record.
- Reading the complete part of a truncated `describe` diff, so that a file under an exemption keeps it when the diff is cut; this needs the real `describe` output of a case that failed `facts_complete` and `no_secret_lines` together.
- A sentence for the guidance that agents follow when they write a commit message: the engine treats a claim that the change was reviewed or approved as steering, and `AGENTS.md` already says to describe the change only.

## Result

Empty until work starts.
