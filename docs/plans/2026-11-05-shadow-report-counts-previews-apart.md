# Make the shadow report count removal previews apart

Status: Proposed
Created: 2026-11-05
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The accepted decision `2026-11-05-unconfirmed-removals-are-outside-the-action-review-measure` says that a `remove` without
`--confirm` (a preview, which deletes nothing) is outside what the shadow measures, and that the report shows such commands on a line of
their own. After this plan:

1. `report.py` puts a labelled `remove` whose collected facts say `confirm` is false in a separate group, "unconfirmed removals
   (previews)", and prints that group on its own line;
2. the removal rate, the minimum of 10 labelled removals, the false-decline count and the "false declines by check" line count only the
   other removals (the confirmed ones);
3. a preview that the engine approved and the owner labelled wrong is a false approve like any other: it is counted in the preview line
   and it still blocks the cutover and prints the alarm;
4. the labels, the bound (10% false declines, 10 labelled commits, 10 labelled confirmed removals, no false approve on the labels or
   the test set) and every other report line are unchanged;
5. the spec says the report does this, and the owner's copy of the report is replaced by the released one.

On the owner's data as of 2026-11-05 the report would then read `remove` labelled 7 (right 7, wrong 0) and not enough labels, and
the preview line labelled 4 (right 0, wrong 4, all false declines by `confirm_present`).

## Scope

- `tools/report.py` of the `action-review` package and its tests (`tests/test_tools_report.py`).
- The spec text that describes the report and says the change is not built (`docs/specs/action-review.md`, "Labelling and the report" and
  the paragraph "Clarified 2026-11-05").
- The release of the package edit and the owner's copy of the report, as the owner's steps.

## Non-goals

- Changing the bound, a label, `confirm_present`, the rules, the engine, the hook or the collector.
- Deciding what the hook does with a preview at cutover (it belongs to the plan for the hook).
- Relabelling the four previews, or changing what `label.py` shows.
- Counting a preview by anything but the collected `confirm` fact.

## Assumptions and constraints

- The collected row of a removal holds the engine's facts and the `confirm` fact among them (`rules/safe-git-remove.json`, the check
  `confirm_present`). The report reads the collected file already; this adds a read of that one boolean and prints no fact, command or
  reason (the report prints counts, rule names and check names only).
- A removal whose `confirm` fact is missing, is not a boolean, or sits where the report does not expect it is **not** a preview: it is
  counted with the confirmed removals, which is the stricter reading. The report never moves a command out of the measure on a guess.
- A change to `packages/` follows the package-edit process: a scratch clone, tests there, the owner's copy with the recorded-hash script,
  the release approvals, and the removal of stale shipped records after the owner approves the list. The command gate refuses Bash while
  the packages differ from the release, so the owner's steps are named and the agent waits.
- The report is copied out of the project with `shadow_store.py` and runs there; it imports nothing else from the package.
- Nothing is pushed. A commit needs the owner's word.

## Completion criteria

1. The new tests fail on the unchanged report and pass on the changed one, and the whole report test file passes.
2. Run on a synthetic store that holds the shapes of the owner's data (11 removals: 7 right confirmed, 4 wrong previews declined by
   `confirm_present`; 9 right commits), the report prints `remove` labelled 7 with "not enough labels (10 needed)", the preview line
   labelled 4 with 4 false declines by `confirm_present`, and a cutover line that names only the commit and removal minimums.
3. A synthetic preview that the engine approved and the owner labelled wrong still prints the alarm and "blocked by a false approve".
4. The spec describes the preview line and no longer says the change is not built.
5. After the owner runs the released report on their own store, the printed numbers are recorded in the spec's evidence with the
   provenance line.

## Increments

### Increment A — The report counts previews apart

**Outcome:** `tools/report.py` splits the labelled removals into confirmed ones and previews by the collected `confirm` fact, applies the
rate, the minimum and the by-check line to the confirmed ones only, prints one line for the previews, and keeps every false approve in
the cutover test.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/tools/report.py`, `packages/workbench/action-review/tests/test_tools_report.py`,
`docs/specs/action-review.md` (the report description, the "Clarified" paragraph), the package's release records (the owner's steps).
**Steps:**
1. In a scratch clone, write the tests first and see them fail on the unchanged report:
   - a labelled removal with `confirm` false is counted in the preview group and not in `remove`;
   - a preview labelled wrong and declined by `confirm_present` is a preview false decline and is not in the `remove` rate, minimum or
     by-check line;
   - the owner's shapes (7 right confirmed removals, 4 wrong previews) give `remove` labelled 7 and "not enough labels", and 3 more
     right confirmed removals give "within the bound" for `remove`;
   - a preview approved by the engine and labelled wrong is a false approve in the preview line, prints the alarm and blocks the cutover;
   - a removal whose `confirm` fact is missing or is not a boolean is counted as a confirmed removal;
   - a skipped or unlabelled preview is counted as skipped or unlabelled and not as labelled;
   - the preview line prints counts only (no fact, command, reason or note), and a command collected twice is counted once;
   - a commit is never split, whatever its facts hold.
2. Change `tally` so that a labelled command of the action `remove` whose facts hold `confirm` false goes to a group `previews` kept
   beside the actions, with the same fields, and `report` prints "unconfirmed removals (previews): labelled N (right R, wrong W); false
   declines F; false approves A" and, when it has false declines, the same "false declines by check" line indented under it. The sum
   of false approves for the alarm includes the previews.
3. Leave `action_line`, the bound, the minimums and the cutover reasons as they are for `commit` and `remove`; the removal reasons now see
   the confirmed removals only.
4. Update the module docstring of `report.py` and the spec's report description to name the preview line; remove "Not built" from the
   "Clarified 2026-11-05" paragraph and say the report does it.
5. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
6. The owner's steps, named when the code is ready: copy the changed files into the project with the recorded-hash script, run
   `wb preview release-approvals` and `wb release-approvals --digest`, remove the stale shipped records after approving the list, and
   copy the new `report.py` beside the owner's `shadow_store.py` for use.
**Verification:** the report test file (`tests/test_tools_report.py`) and the label test file (`tests/test_tools_label.py`), because the
two tools read the same store; `tests/test_boundary.py` is not touched by this change and is not rerun. A run of the released report on a
synthetic store as in completion criterion 2.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-shadow-report-counts-previews-apart#A`.

### Increment B — The owner's report numbers recorded

**Outcome:** the spec's evidence holds what the changed report printed on the owner's own store, so that the cutover decision rests on
the counts the decision defined.
**Dependencies:** A.
**Affected areas:** `docs/specs/action-review.md` (Evidence).
**Steps:**
1. The owner runs the released `report.py` at a terminal on their store and the agent reads its output (the report prints counts only).
2. Append an Evidence entry with the provenance line: what was run, the Python version, the commit of the report, and the printed
   counts for `commit`, `remove`, the previews, the test set and the cutover line.
3. State the remaining labels needed, as the report prints them. Do not change a label, the bound or the cutover rule.
**Verification:** the entry's numbers match the printed output; no other file changes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-shadow-report-counts-previews-apart#B`.

## Verification for the plan as a whole

Each increment's recorded verification stands. After B, the report's cutover line is the one thing read again; it is read from the
owner's store and recorded, not rerun in the project. The wider package suite is not run: the change is in one tool that nothing else
imports. The risk outside the tested area is that the owner's copy of `report.py` differs from the released one, which the recorded-hash
copy step and the owner's own run in B show.

## Risks and sensitive actions

- A mistake in the split could hide a false approve. The tests in A cover a preview approved by the engine and labelled wrong, and the
  alarm sum is taken over every group, so a preview false approve cannot be left out. A command with an unreadable `confirm` fact is
  counted in the confirmed group.
- The report reads one more field of the collected file, which holds command text and diffs. It prints none of them, and a test
  checks the preview line for that.
- The package edit closes the command gate until the owner has released it; the owner's steps are in A.
- The decision changes what the cutover measures. It does not change who decides: the cutover is still the owner's, in a later plan.

## Review record

Empty until a review is asked for.

## Deferred work

- The plan for the hook that decides, the push rule, the cutover and the removal of `claude-workflow`, including what the hook does
  with a preview.
- The duplicated "no round was spent" in the review engine's refusal for an unaccepted option (a separate package edit).

## Result

Empty until work starts.
