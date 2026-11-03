# Redact secrets from what the action-review shadow stores

Status: Proposed
Created: 2026-11-03
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The shadow hook keeps, for each reviewed command, the command text and the engine's facts, a commit's diff included, in
`collected.jsonl`, and the model's reason in `collected.jsonl` and `verdicts.jsonl`. The security review of plan
`2026-10-29-action-review-shadow-hook` (Medium 1) found that these can hold a secret, in a file that nothing guards beyond mode 0600.
The owner decided on 2026-11-03 that the stored text is to be redacted, as a small plan of its own.

When the plan is done, the hook writes the command, the facts and the reason with every secret that a fixed list of patterns finds
replaced by a visible marker, the shape of the facts and the owner's ability to judge a command are kept, a redaction that cannot
finish writes no row instead of a raw one, and the spec says what is redacted and what is not.

## Scope

- One function in `hook/shadow_hook.py` that returns a copy of a text, a list or an object with the secrets it finds replaced, and
  its use on the three stored values (`command`, `facts`, `reason`) before a row is written.
- The patterns: private-key blocks; the prefixed tokens of the common services; `Authorization` and bearer values; a value assigned
  to a name that says secret, token, password, key or credential; the user and password of a URL; a JSON web token.
- The spec's data-files text, the owner's steps, and the line added on 2026-11-03 telling the owner not to share the file.

## Non-goals

- What is sent to the bridge's vendor. The facts, a diff included, still go to the model to be judged; this plan changes only what
  is kept on the owner's disk. The owner's steps already say what leaves the machine.
- Rewriting rows already stored. No real row has been collected yet; if the owner's directory holds rows by then, they stay as
  they are and the owner deletes or keeps them.
- Detecting a secret by its entropy or by its place in a file. A generic rule would redact the git hashes that the facts hold and
  that the owner needs in order to judge a command.
- The engine, the store's format, the labelling tool, the report and the test-set runner. The row fields stay as they are.
- A guarantee. The patterns find what they name; a secret in another shape is stored as it was.

## Assumptions and constraints

- The hook is stdlib-only, prints nothing and exits 0 whatever happens ("The shadow hook"); the redaction keeps both properties.
- A row's `command_sha256` stays the hash of the raw command, so a verdict row and a collected row still match. The engine's
  `facts_sha256` in `verdicts.jsonl` is of the facts as the engine saw them, so it no longer matches the stored, redacted facts; the
  spec says so. No tool compares them.
- The marker is `[redacted:<kind>]` with a short fixed kind (`private-key`, `token`, `bearer`, `assignment`, `url-credentials`,
  `jwt`). It holds nothing of the secret, not its length.
- A redacted text keeps its line breaks, so a diff still reads as a diff, and a long value does not make the work slow: each pattern
  is linear in the text, and a test pins a time limit on the largest allowed input (the facts cap, 393,216 characters).
- The hook is a shipped file, so a change to it changes the module hash. Each increment that changes the package is built and
  tested in a scratch clone, reviewed, copied into the tree and released by the owner, as in the earlier plans.
- Tests are written first and seen to fail, and the function and the hook are mutation-tested as in the earlier plans.

## Completion criteria

1. A function in `shadow_hook.py` redacts each kind named in the scope, in a string, in every string of a nested list or object,
   and in the keys' values only (a key is kept), and leaves a text without a secret byte-for-byte as it was; each kind has a test
   that fails without its pattern.
2. A row for a reviewed command holds a redacted `command`, redacted `facts` and a redacted `reason`, in `collected.jsonl`, and a
   redacted `reason` in `verdicts.jsonl`; `command_sha256` is still of the raw command; a test runs the hook as a subprocess with a
   fake engine that prints a secret in each of the three places and finds none in either file.
3. If the redaction raises, or the redacted row no longer passes the store's checks, no collected row is written, the verdict row
   is written without the reason, the hook prints nothing and exits 0, and a note goes to standard error.
4. The facts keep their shape: a redacted object has the same keys and value types, so `label.py` and `report.py` read it as before
   (their tests pass unchanged).
5. The spec's data-files text, "What leaves your machine" step and "As built" say what is redacted, what is not and the residual
   risk, and the 2026-11-03 line that tells the owner not to share the file now says the patterns are best-effort and the file is
   still not to be shared.
6. `python3 -B -W error tests/run_all.py` passes, `wb check .` and `wb run code-work check` report no problem, and every pin still
   matches (`test_actionreview_pins`).

## Increments

### Increment A — The redaction function

**Outcome:** `shadow_hook.py` has a pure function that returns a redacted copy of a string, a list or an object, with tests for each
pattern kind and for the cases that must not change.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/hook/shadow_hook.py`, a new test file in
`packages/workbench/action-review/tests/` (`test_hook_redact.py`).
**Steps:**
1. In a scratch clone, write the tests first: for each kind, a text with a secret and the expected marker (a PEM block, also one cut
   off by the text's end; a token of each prefix: `AKIA`, `ghp_`, `gho_`, `ghs_`, `github_pat_`, `sk-`, `xox`, `AIza`; `Authorization:
   Bearer` and `Basic` values; `password=...`, `"api_key": "..."`, `TOKEN: ...`; `https://user:pass@host`; a JWT).
2. Write the tests for what must not change: a 40-character git hash, a 64-character SHA-256, a path, a version, a word such as
   `token` or `password` with no assigned value, a name such as `author`, and a text with no secret (equal byte for byte).
3. Write the tests for the walk: a nested list and object are copied with every string redacted, the keys, numbers, booleans and
   nulls are kept, the input is not changed, and a depth or a size past the store's limits is handled the way the store handles it
   (not by recursion past the interpreter's limit).
4. Write a test that the largest allowed input, with the worst-case text for each pattern, finishes within a stated time.
5. See the tests fail, then write the function: one compiled pattern per kind, applied in a fixed order, each replacing only the
   secret and keeping the name, the separator and the line breaks around it.
6. Mutate the function one change at a time (drop a pattern, widen or narrow a character class, replace the marker, redact a key,
   change the order) until every mutation is caught.
**Verification:** the new test file under `-W error`, then the action-review test directory, then the mutation run; then
the `reviewer` agent on the diff, whose findings are decided one by one.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-redact-collected-diffs#A`, and the shipped approval records
that the owner's release writes.

### Increment B — The hook stores only redacted text

**Outcome:** the hook redacts the `command`, the `facts` and the `reason` before it writes a row, and writes no collected row when
the redaction fails.
**Dependencies:** Increment A.
**Affected areas:** `packages/workbench/action-review/hook/shadow_hook.py` (`record`), and `tests/test_hook_shadow_hook.py`
(which already runs the hook as a subprocess).
**Steps:**
1. Write the tests first: a fake engine that prints a secret in the command, in the facts (a diff) and in the reason; run the hook as
   a subprocess; read both data files and find no secret, a marker where each was, `command_sha256` equal to the hash of the raw
   command, and the same keys as before.
2. Write the failure tests: a redaction that raises (the function replaced in a test), and a redacted row that fails the store's check,
   each leave no collected row, a verdict row without a reason, nothing on standard output, exit 0 and a note on standard error.
3. See the tests fail, then change `record` to redact the three values, to hash the raw command, and to catch a failure as step 2 says.
4. Mutate `record` one change at a time (skip the command, the facts or the reason; hash the redacted command; write the raw row on
   failure) until every mutation is caught.
**Verification:** the hook's tests under `-W error`, the whole action-review test directory, the mutation run, and the `reviewer`
agent on the diff.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-redact-collected-diffs#B`, and the shipped approval records
that the owner's release writes.

### Increment C — The spec says what is redacted

**Outcome:** the spec describes the redaction, its limits and the owner's duty, and no text claims that the stored text is raw or
that the file is safe to share.
**Dependencies:** Increments A and B.
**Affected areas:** `docs/specs/action-review.md` ("The data files", "The shadow hook", the owner's steps, "As built", "Decided by
the owner"), `docs/development.md` if its shadow rows describe the stored text.
**Steps:**
1. In "The data files", say that `command`, `facts` and `reason` are stored redacted, name the kinds and the marker, and say that
   `facts_sha256` is of the unredacted facts.
2. In the owner's steps, replace the 2026-11-03 line with one that says the redaction is best-effort, lists what it does not find
   (a secret in another shape, or one split across lines) and still asks the owner not to copy, share or back up the file.
3. Add an "As built (Increment B)" paragraph with the departures, if any, and mark the Medium 1 decision as done.
4. Run the plan check and the project check.
**Verification:** `wb check .`, `wb run code-work check`, `git diff --check`, and a read of the changed text against the code.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-redact-collected-diffs#C`.

## Verification for the plan as a whole

From this repository's root, when every increment is done:

1. `python3 -B -W error tests/run_all.py`.
2. `python3 -m workbench check .` and `python3 -m workbench run code-work check`.
3. `git diff --check`.
4. The pins test, `python3 -B -m unittest discover -s packages/workbench/action-review/tests -t
   packages/workbench/action-review/tests -p 'test_actionreview_pins.py'`.

Not run by the agent: the hook against Claude Code, a real bridge and a real model. The redaction is tested against the patterns
the plan names, not against the owner's real commits.

## Risks and sensitive actions

- **Best-effort only.** A secret in a shape the patterns do not name is stored as it was. The plan says so in the spec and keeps the
  instruction not to share the file. The patterns are a list, and the owner can extend it by a plan of its own.
- **A pattern that is too wide** hides a fact the owner needs to judge a command. The tests pin what must not change (hashes, paths,
  plain words), and the owner can still read the command and the shape of the facts; a miss here costs a `skip` label, not a wrong one.
- **A pattern that backtracks** could make the hook slow on a hostile diff. The hook has a wait bound, so the prompt is not held, but
  the time test and the plain, anchored patterns are the defence.
- **The hook is security-relevant code** (untrusted text, the filesystem). Each package increment is reviewed by the `reviewer` agent,
  and the owner may ask for a security review afterwards.
- The package edits break the command gate until the owner runs `wb release-approvals`, as in the earlier plans. Nothing here pushes,
  installs or deletes.

## Review record

Empty until a review is asked for.

## Deferred work

- Rewriting rows that were stored before the redaction exists: none are known to exist.
- A rule by entropy or by file type, if the owner finds a secret that the patterns miss in real use.
- Keeping the facts out of the bridge's request when they hold a secret: a change to the engine, and a decision for the owner.

## Result

Empty until work starts.
