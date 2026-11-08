# Stop the engine's secret scan flagging the path of a review file

Status: Proposed
Created: 2026-11-08
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The `no_secret_lines` check of the action-review engine no longer declines a commit only because the path of a review file, in the header of its diff section, reads as a random token. After this plan the entropy test is skipped for the two header lines (`--- HEAD/<path>` and `+++ work/<path>`) of a section whose path is exactly one of the four files that the review engine keeps in a review directory: `state.json`, `ledger.md`, `schema.json` and `round-<n>.json` in `.workbench/workbench/review-engine/<kind>-<16 lowercase hex>/`. The content of each file is scanned exactly as it is today, and the 15 secret patterns still run on the header.

The reason is measured, and it finishes the work of the plan `2026-11-08-secret-scan-skips-review-state`, which left it out and said so. The scan reads the path in each section's header, and a review directory name (`<kind>-<16 hex>`) can score as a random token by chance (a letter-and-digit path segment of at least 16 characters with entropy of 3.8 or more). On 2026-11-08, at commit `37b1e8e`, with the helper as installed: of the 392 tracked review files, 55 are flagged by the header alone (13 `ledger.md`, 29 `round-<n>.json`, 13 `schema.json`; the 13 review directories whose key scores high). Scanned as new files with their whole content, the same 55 are flagged and no other file is; with the entropy test skipped on the header only, none is. So the header is the only blocker, and a commit that completes one of those 13 reviews is declined today for nothing a person would call a secret.

## Scope

- `packages/workbench/action-review/helper/action-review`: one constant for the exact path shape of the four files and the part of `diff_secret_kind` that scans a section, so that for a matching path the header lines are scanned with the entropy test off and the rest of the section with the file's own options. Nothing else in the helper.
- `packages/workbench/action-review/tests/test_actionreview_checks.py`: the tests of the new behaviour and of every look-alike.
- `docs/specs/action-review.md`: the "Open limits" bullet on the secret scan, whose "Not covered, and measured" sentence this plan ends.

## Non-goals

- Any other path. A header is still scanned in full for every other file, a file name that carries a secret is still caught as before, and `paths_not_credentials` is not touched.
- The content of the four files. `ledger.md`, `schema.json` and `round-<n>.json` keep the entropy test on their content, which holds a model's finding text; `state.json` keeps what the previous plan gave it (no entropy test on its content).
- Exempting the whole review directory, which would also drop the entropy test on the finding text. It clears nothing more than this plan does: of the last 70 commits at `37b1e8e` both options leave the same four commits flagged, none of which holds a review file.
- The four commits that remain flagged for other reasons: the helper's own table of pinned data-file hashes and the test files with deliberate fake credentials (named as deferred work in the previous plan).
- The case where `describe`'s diff is truncated and the scan falls back to the whole diff under no options.
- The installed copy in this project: the upgrade and the rerender are the owner's steps after the release.

## Assumptions and constraints

- The path shape is exact, as the earlier ones are: `.workbench/workbench/review-engine/<kind>-<16 lowercase hex>/<name>`, where `<kind>` is one of `plan`, `spec`, `roadmap` and `adr` (the review engine's `KINDS`), the key is the first 16 hex characters of a SHA-256 (`review-engine` `key`), and `<name>` is `state.json`, `ledger.md`, `schema.json` or `round-<n>.json` with `<n>` a number from 1 to 1000 without a leading zero (the review engine's `MAX_ROUNDS` is 1000 and it writes `round-%d.json`; the tests pin 1, 999 and 1000 as the shape and 0, 01 and 1001 as not). The review engine writes no other file in that directory (measured: the 75 tracked directories hold only these four kinds).
- The loosening is small by construction, which a general rule would not be: the exempt header is a fixed grammar whose only free part is 16 hex characters (64 bits) and a round number, so a file name in this shape cannot carry a secret of any size worth the name, unlike a path rule that skipped the entropy test on every header.
- The header is the first two lines of a section that has a path (`_diff_sections` builds them as `--- HEAD/<path>` and `+++ work/<path>` and requires the second to repeat the first's path). A section with no path (a mode line) and a diff of unknown shape keep their present treatment: a diff of unknown shape is scanned whole with no exemption, and a header-like line inside a hunk of another file changes no option (the existing spoof tests keep passing).
- Only the entropy test is skipped, and only on those two lines. The patterns run on them and on everything else. The option for `state.json` (the previous plan's `REVIEW_STATE_PATH`) stays as it is; its content is not entropy-scanned, and its header now is covered by the same rule.
- The previous plan's tests use a key that scores low; the new tests need a key that scores high. A real one is among the tracked directories (the key `53f19ce72c811b20` of an `adr` review scores high in its header; the test also derives candidates from the scan itself and asserts that the unchanged rule flags them, so that the test cannot pass on a key that was never a problem).
- The module's tree changes, so the release approvals, the removal of stale shipped records after the owner approves the list, the acknowledge, the upgrade and the rerender are the owner's. The increment is built and tested in a scratch clone and copied by the owner's script, as before. Nothing is pushed without the owner's word.

## Completion criteria

1. For each of the four kinds and each of the four file names, a diff section at the exact path with a key that scores high in its header, and ordinary content, passes `no_secret_lines`; with the unchanged helper the same section is `high_entropy`.
2. The content is still scanned: a random-looking token, a 64-hex value on a line that names no checksum, or a secret pattern in the content of `ledger.md`, `schema.json` or `round-<n>.json` at such a path is still reported (`high_entropy`, `long_hex`, `pattern`); in `state.json` a pattern is still reported and the entropy test stays off, as before.
3. Each look-alike path is scanned as before, header included, and a header that scores high is still `high_entropy` there: another kind, a key of 15 or 17 hex characters, an uppercase key, `ledger.mdx`, `round-0.json`, `round-01.json`, `round-1001.json`, `round-.json`, a name one directory deeper, a prefix before `.workbench`, a missing `workbench/`, and the same names in any other directory.
4. A diff of unknown shape is scanned whole with no exemption; a mixed diff reports a hit in the sections around an exempt header; a header-like line inside another file's hunk claims nothing; and the patterns still run on an exempt header. A real header in this grammar cannot hold any of the 15 patterns (its only free part is 16 hex characters and a number), so that last point is shown in a test by adding, for the test only, one pattern that matches the test's own key to the helper's pattern list and seeing the exempt section reported as `pattern`; without the exemption's patterns the same section would pass.
5. The existing scan tests (digest context, lock files, test directories, the manifest, the release records, the review state, the spoof and shape tests) still pass, and the tests that read the shipped test set still read all 29 of its cases with the outcomes they have now.
6. The spec states the new exemption, ends the "Not covered, and measured" sentence, and keeps the residual risk; `wb run code-work check` passes.
7. After the owner's steps, a read-only scan of every tracked review file with its content, and of the last 70 commits, reports no review file flagged, with the same section of the engine that the earlier measurements used. The plan does not claim a number for the owner's store.

## Increments

### Increment A — Skip the entropy test on the header of a review file

**Outcome:** completion criteria 1 to 6 are true; criterion 7 is checked after the owner's steps.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/helper/action-review`, `packages/workbench/action-review/tests/test_actionreview_checks.py`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first, in a scratch clone, beside the review-state tests: the cases of criteria 1 to 4, with a key that scores high found by the test itself and asserted to be flagged by the unchanged rule; and one test through the real `checked(...)` path with a new `ledger.md` in a directory whose key scores high, which passes, and the same file with a random token in its content, which fails `no_secret_lines`. See them fail with the present code.
2. Add the path pattern constant and extend `diff_secret_kind` so that for a matching path the first two lines of the section are scanned with the entropy test off and the rest with the file's own options. Keep `_scan_options`, `REVIEW_STATE_PATH`, the helper's imports and its pinned words as they are.
3. Edit the spec's bullet. Search the repository for another description of the scan's exemptions (`docs/specs/safe-git.md`, `docs/specs/review-engine.md`, `docs/development.md`, the module's skill and README); report one that disagrees and change it only if it states the old list.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_actionreview_checks.py`, and the module's rule, bridge, module and pin tests (`test_actionreview_rules`, `test_actionreview_bridge`, `test_actionreview_module`, `test_actionreview_pins`) and the test that reads the shipped test set, run as `python3 -I -B` through the runner; a mutation pass over the new rule (the path pattern, the number of header lines, the options of the rest of the section, the entropy flag on the header, the patterns on the header); then `wb run code-work check`. A read-only scan before and after in the scratch clone: every tracked review file with its content (55 flagged today, none expected) and the last 70 commits. Not run: the whole repository suite, the shadow hook and report tests (neither imports the helper), and the test-set runner against a real model.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-secret-scan-skips-review-file-paths#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. Whether the count of commits that are reviewed but not collectable falls is for the owner to see in the report after the upgrade, as new commits are made.

## Risks and sensitive actions

- This touches the secret scan, a security-relevant surface. The change removes one check for one named header shape: a path in this fixed grammar has 64 free bits and cannot carry a secret worth catching, and the content of each file keeps every check it has today. The paths are exact, which the look-alike tests pin. A security review of the previous exemption (2026-11-08) found no bypass beyond the exemptions that already existed; the owner is asked once, after the increment is built, whether to run one of this change, and it runs only on the owner's word.
- A package file changes: the release approvals, the stale-record removal, the acknowledge, the upgrade and the rerender are the owner's. Nothing is pushed without the owner's word.
- No new network, subprocess or filesystem write by code is added.

## Review record

Codex, plan review, 2 rounds of 3 (the bound); converged with no meaningful finding in round 2. Model: `gpt-5.6-terra` for both rounds.

- Applied (round 1, major): a criterion asked for a test that a secret pattern on an exempt header is still reported, which cannot be made with a valid header in the exact grammar (its only free part is 16 hex characters and a round number, which no pattern matches). The criterion now says that the patterns still run on an exempt header and shows it in a test by adding one pattern that matches the test's own key to the helper's pattern list, for the test only, and seeing the section reported as `pattern`.
- Applied (round 1, major): the round-file grammar stopped at 999; the review engine's `MAX_ROUNDS` is 1000 and it writes `round-%d.json`. The grammar now accepts 1 to 1000 without a leading zero, and the tests pin 1, 999 and 1000 as the shape and 0, 01 and 1001 as not. I checked the constant and the file name in the review engine's source.
- Left for the owner: nothing from the review.

## Deferred work

- A line-shaped exemption for the helper's own table of pinned hashes, or moving that table out of the source into a data file that the scan treats as a hash record.
- Reading the complete part of a truncated `describe` diff, so that a file under an exemption keeps it when the diff is cut.
- A narrower design for the three older exemptions (the manifest, the release records and the review state): skip only a 64-hex value on a line keyed `seal` or a checksum word, and not the whole entropy test.

## Result

Empty until work starts.
