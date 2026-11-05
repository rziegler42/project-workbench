# Make the shadow report count removal previews apart

Status: Completed
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

**Increment A.** Reviewer: the `reviewer` agent (read-only), one round of the cap of 3, no blocking finding. It was given the plan, the
decision, the diff, the verification as run and the spec sections, and not my conclusions.

- **Applied:** none needed. It found no way to leave a false approve out of the alarm or the cutover line (`label_approves` takes the
  previews' false approves first), no way to move a command out of the measure with a malformed `confirm` fact (only a dict `facts` with a
  dict `facts` and `confirm is False` makes a preview), nothing printed but counts and check names, and no mismatch between the plan,
  the decision and the code.
- **Rejected, with the reason:** *Finding 1, the guard test on the allowed reads is too weak* (it looks at string constants in function
  bodies only, so `inner.get("requested_paths")` or `dict(row)` would pass). Not blocking, and the plan asks for a printing check, which
  `test_the_preview_line_is_printed_with_no_label_at_all_and_prints_no_fact_command_reason_or_note` makes with a marker string. A stricter
  guard (no string key outside `is_preview`) would fail on the report's own `row["id"]` and `row["label"]`, and the reviewer itself
  calls the present test acceptable. Left as it is.
- **Noted:** *Finding 2*, `by_id.setdefault` keeps the first collected row of an id, so a later duplicate cannot flip a command's
  group. Existing behaviour, tested by `test_a_preview_collected_twice_is_counted_once`.
- **Not checked by the reviewer:** that the owner's steps and copy were done; `test_tools_label.py` and `label.py` (I ran the label tests
  myself; `label.py` is unchanged); the decision file itself.
- **Left for the owner:** the copy, the release and the decision to go on to B.

## Deferred work

- The plan for the hook that decides, the push rule, the cutover and the removal of `claude-workflow`, including what the hook does
  with a preview.
- The duplicated "no round was spent" in the review engine's refusal for an unaccepted option (a separate package edit).

## Result

**Increment A, built in a scratch clone (2026-11-05); not yet copied into the project, released or committed.** Base commit of the clone:
`445529f`. Changed in the clone: `packages/workbench/action-review/tools/report.py` (+ `is_preview`, `new_entry`, `preview_line`; `tally`
returns the previews apart; `report` prints the preview line and keeps `label_approves` over every group; docstring) and
`packages/workbench/action-review/tests/test_tools_report.py` (a `Previews` class of 14 tests, a `removal` helper, and one more
`Source` test). The spec's report paragraph and the "Clarified 2026-11-05" paragraph in `docs/specs/action-review.md` were edited in the
project (docs only); "Not built" was replaced by what is built.

**Verification as run.** Tests first: the 16 new or changed tests failed on the unchanged report (the first showed the live output,
`remove: labelled 11 (right 7, wrong 4)`, where 7 was expected); one fixture was wrong (the store requires `facts` to be an object) and
was corrected before the code change. After the change `tests/test_tools_report.py` and `tests/test_tools_label.py`: 102 tests OK. The
copied script on a synthetic store (9 right commits, 7 right confirmed removals, 4 wrong previews declined by `confirm_present`) printed
`remove: labelled 7 (right 7, wrong 0) ... not enough labels (10 needed)`, `unconfirmed removals (previews): labelled 4 (right 0, wrong 4);
false declines 4; false approves 0`, `false declines by check: confirm_present 4`, and a cutover line naming the commit and removal
minimums only (and the test set, which the synthetic store lacks). The existing test that the report reads no `facts["..."]` of a row
still passes because the new read is `.get("facts")` in one function; a new test pins that the constants `facts` and `confirm` occur in
`is_preview` only and that `command`, `reason` and `diff` occur nowhere. Not run: the whole suite and `tests/test_boundary.py`, because
the change is in one tool that nothing imports and touches no installer file.

**Hashes of the two files at the end of the clone's work** (SHA-256): `report.py`
`feceff72bdd1bf26185b9c96f42929f0402ceb5166e87dd4c99238becc14f815`, `test_tools_report.py`
`0d448b5e62cbd10479825bbbdf1fa2e0e568b5a9631abe6a703eb5bcb5c506ee`.

**Review:** one round, no blocking finding (see the review record).

**Not done in A:** Increment B. A was released by the owner, the stale shipped records were removed after the owner approved the list, and A
is committed as `45a3277`.

**Increment B (2026-11-05).** The owner replaced their copy of `report.py` (identical hash to the committed file, mode 444 kept) and the
agent ran it, read-only. It printed `commit` 9 labelled; `remove` 6 labelled (right 6); previews 5 labelled (right 1, wrong 4, all
false declines by `confirm_present`); 5 unlabelled waiting; test set 29 of 29 with no false approve; cutover "not yet (not enough labels
for commit; not enough labels for remove)". The Evidence entry is in `docs/specs/action-review.md`. **A correction:** the plan's Goal
and the decision expected `remove` at 7, on the assumption that the five previews were the four wrong ones plus none labelled right;
one preview was labelled `right`, so the confirmed removals are 6 and 4 more are needed, not 3. The plan's body is not changed
(it needs a new approval) and the accepted decision is not rewritten; the entry in the spec states the correction. Verification: the
entry's numbers equal the printed output; no file other than the spec and this plan changed.
