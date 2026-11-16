# Tie the action-review path patterns to the review engine's spelling

Status: In Progress
Created: 2026-11-16
Candidate: none (a gap that the review of the plan `2026-11-16-collapse-review-records-in-the-list` found in increment A and that needs no roadmap direction)
Specs: clone-enrollment

## Goal

A change to how the review engine spells the folder and file names of its records fails a test, whichever of the places that copy the spelling it leaves behind. Today two of the three copies are tied to the engine by a test (the installer's rule `workbench/reviewrecords.py`) and one is not: the two patterns `REVIEW_STATE_PATH` and `REVIEW_FILE_PATH` of the `action-review` helper. When the plan is done, a test reads the engine's source and the `action-review` source and fails when the kinds, the folder, the length of the key, the file names or the largest round number differ, and the spec says so.

## Scope

- One new test class in `tests/test_reviewrecords.py`, which reads the two helpers' source and checks the `action-review` patterns against the engine's spelling, and against the installer's rule where the three are meant to agree.
- The sentence in `docs/specs/clone-enrollment.md` that says no test ties the third copy.

## Non-goals

- No change to the `action-review` helper, to the review engine, or to any file under `packages/`. A change there alters the module's tree, makes its release approval stale and locks the tools until the owner releases it.
- No change to the installer's rule or to what `acknowledge` prints.
- No change to the patterns themselves. If the test finds a difference other than the one recorded below, the plan stops and reports it; a fix to a package file is its own plan.
- No export of the engine's spelling for the other modules to import. That is a design change.

## Assumptions and constraints

- Read, not run: the engine takes a round file's name from `FILE_NAME` (`round-[1-9][0-9]{0,3}`, so 1 to 9999) and caps the number of rounds at `MAX_ROUNDS` (1000); the `action-review` pattern for a round file runs from 1 to 1000. The installer's rule follows the engine's `FILE_NAME`. So the three copies already differ for a round number from 1001 to 9999, which no real review reaches (a review is bounded at 5 rounds). The test records that difference as intended and does not remove it.
- The helpers are files with no `.py` extension. The test reads them as text and parses them with `ast`, and never imports or runs them; the patterns are taken from the first argument of the `re.compile` call of each assignment, so a reformat of the source does not matter and a change of the form of the assignment fails loudly.
- The test lives in the repository's own `tests/`, where the existing drift test already reads the engine's source, so no file under `packages/` is touched.
- Nothing tracked points to anything untracked: this plan and its test cite no item of the owner's todo list.

## Completion criteria

1. A test fails when each of these is changed in a scratch copy of either helper: a kind added or removed, the folder renamed, the length of the key, a file name added or removed, and the largest round number (for the `action-review` patterns, below or above the engine's `MAX_ROUNDS`).
2. The test passes on the repository as it is, with the one difference above recorded in it by name.
3. `git status` after the plan shows no file under `packages/` changed.
4. The spec states that a test ties the three copies, and names the intended difference.

## Increments

### Increment A — The test

**Outcome:** a test class that fails when the `action-review` patterns and the engine's spelling part company.
**Dependencies:** none.
**Affected areas:** `tests/test_reviewrecords.py`. Nothing else.
**Steps:**
1. Write the test first. From the engine's source, by `ast` and without running it, take `KINDS`, `NAMESPACE`, `FILE_NAME` and `MAX_ROUNDS`; from the `action-review` source, compile the two patterns of `REVIEW_STATE_PATH` and `REVIEW_FILE_PATH`. Build paths from the engine's spelling (every kind, a key of 16 hex digits, every file name, round numbers 1, 2, 999 and `MAX_ROUNDS`) and assert that `REVIEW_FILE_PATH` matches every one and `REVIEW_STATE_PATH` matches only `state.json`. Assert that it does not match each of: a kind the engine does not have, a key of 15 or 17 digits or in upper case, `round-0.json`, a round number above `MAX_ROUNDS`, another folder, and a name one character off.
2. Assert that, for every path of step 1 with a round number up to `MAX_ROUNDS`, the installer's rule (`reviewrecords.record_of` on an added regular file) and `REVIEW_FILE_PATH` agree; and assert, by name and with a comment, that a round number above `MAX_ROUNDS` and up to 9999 matches the installer's rule and not `REVIEW_FILE_PATH`, so that the difference cannot change unseen. The failure messages name the three places to change together.
3. Run it on the repository as it is: it passes. Then, in a scratch copy of the tree (never the real one), apply one mutant at a time to the `action-review` source (a kind added, a kind removed, the folder renamed, the key digits 15, a name added, a name removed, the round bound 999 and 1001) and to the engine's source (a kind added, `FILE_NAME` gaining a name, `MAX_ROUNDS` changed), and confirm that each fails the test. A mutant that survives is a missing assertion, and gets one.
4. Run `git status` and confirm that nothing under `packages/` changed.
5. Ask the `reviewer` agent to review the increment as `run-increment` says, judge the findings with `evaluate-findings`, and record the review under this plan's Result before the owner is asked to commit.
**Verification:** `python3 -B -W default -m unittest tests.test_reviewrecords` with a scratch `HOME`, the mutation pass of step 3, and the `git status` of step 4.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-16-tie-the-action-review-spelling-to-the-engine#A`.

### Increment B — The spec says the copies are tied

**Outcome:** the spec no longer says that no test ties the third copy.
**Dependencies:** A.
**Affected areas:** `docs/specs/clone-enrollment.md` (its known limit about the spelling, and nothing else), this plan's Result.
**Steps:**
1. Replace the clause that says the `action-review` helper holds a third copy "that no test ties" with a statement that a test in `tests/test_reviewrecords.py` ties it to the engine's source, and name the one intended difference (the largest round number).
2. Search the living documents for the old clause, ignoring case, and record what the search finds.
3. Run `wb check` and `wb run code-work check`.
4. Ask the `reviewer` agent to review the increment and record the review under this plan's Result.
**Verification:** the search of step 2, `wb check` (with the document check) and `wb run code-work check`, as run.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-16-tie-the-action-review-spelling-to-the-engine#B`.

## Verification for the plan as a whole

Confirmed: A's test and its mutation pass stand unless B changes code, and B changes none. Rerun after B: `tests.test_reviewrecords` once, and `wb check`. No whole-suite run is planned; I would recommend one only if A finds that the test needs a change under `packages/`.

## Risks and sensitive actions

- **A legitimate change to the engine's spelling now fails a test.** That is the point. The failure message names the three places to change, and the change to `action-review` is a package edit that needs the owner's release of the module's approval, which this plan does not do.
- **The test parses the helpers' source.** It parses with `ast` and never runs it, on a checkout the owner already trusts to run its own tests. A helper in a hostile clone could make the test fail or hang the parse, and nothing more.
- **A difference other than the recorded one.** If A finds one, the plan stops and reports it; it does not edit a package file.
- The accepted decision `2026-11-16-acknowledge-counts-added-review-engine-records` says in its consequences that the `action-review` copy has no test. After this plan that sentence is out of date. An accepted record is not edited; whether to add a dated note or a new record is the owner's, and the plan only reports it.
- Nothing is pushed by this plan, no file is deleted, and no file under `packages/` is changed.

## Review record

Empty until a review is asked for.

## Deferred work

- A single place that the engine exports its spelling from, for the installer and `action-review` to read, in place of three copies. It is a design change across two modules and would need its own plan.

## Result

### Increment A

**Built and committed (the commit that holds this record).** `tests/test_reviewrecords.py`: `import ast` and the class `ActionReviewSpellingIsTied` (four tests). Nothing else changed; `git status` shows only that file modified and this plan untracked, and nothing under `packages/`.

**Steps 1 and 2.** The class reads the engine's `KINDS`, `NAMESPACE`, `MAX_ROUNDS` and `FILE_NAME` and the two compiled patterns of the `action-review` helper with `ast` and never runs either helper. Tests: (1) the kinds, the plain file names and the key length read out of the text of each pattern (`REVIEW_FILE_PATH` and `REVIEW_STATE_PATH`) equal the engine's; (2) over a universe of about 5,000 paths built from both spellings and decoys (other kinds, keys of 15 and 17 digits, upper-case and non-hex keys, other folders, a folder with a bare character where the pattern has an escaped dot, names one character off, names with a digit or a hyphen, round numbers 0, 00, 01, 1, 2, 9, 10, 99, 100, 999, 1000, 1001, 9999 and 10000), each pattern matches exactly what the engine's spelling says it should; (3) the installer's rule agrees with `REVIEW_FILE_PATH` on every path of the universe except a round number above the engine's `MAX_ROUNDS` and up to 9999; (4) that one difference is pinned by name. Failure messages name the three places to change together.

**Step 3, the mutation pass** on a scratch copy of the tree (the real tree was not mutated), each mutant run against the new class alone. The first pass had 26 mutants (18 of the `action-review` patterns, 8 of the engine), all killed. After the review, 12 more were added for the findings below: a kind that only the state pattern holds, a kind swapped, a bare dot in either pattern's folder or in a name, a name with a digit in the `action-review` pattern or in the engine, a hyphen and a digit in the engine's names, and `flags=` or a second argument on `re.compile`. All 38 are killed, each by an assertion about the path or set it concerns (none by a parse error). The unmutated copy passes. `python3 -B -W default -m unittest tests.test_reviewrecords`, scratch `HOME`, Python 3.15: 16 tests, OK (12 earlier, 4 new).

**Step 5, review.** The `reviewer` agent found no blocking finding and five that did not block, all applied: (1) kinds and names of the universe were read only from `REVIEW_FILE_PATH`, so a kind or a name added to `REVIEW_STATE_PATH` alone could pass; both patterns are now read, and a test compares each pattern's kinds, names and key length with the engine's directly; (2) the plain file names were read with a pattern that could not see a digit or a hyphen; the alternatives are now split at the top level and unescaped; (3) `re.compile(..., flags=...)` passed unseen; the call must now have no keywords and be `re.compile`; (4) `assert` is stripped by `python -O`; explicit `AssertionError` raises replace them; (5) nothing told an escaped dot from a bare one; decoys were added (a folder and names with a letter where a dot belongs). It checked as sound: the round bounds, the key length, the pinned difference (it cannot change silently), the `ast` parse (loud on a non-literal or a changed form) and the scope. It could not run anything. The fixes were not given a second look of their own; each is guarded by the mutants above.

**Left for the owner.** Nothing for A (this plan has no review files of the review engine, so none are committed with it). Increment B follows.
