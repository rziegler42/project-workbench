# Tell the agent which command forms the gate accepts, in the base

Status: In Progress
Created: 2026-11-06
Candidate: none (a correction that follows from a finding: agents try command forms the gate refuses, then retry in another form; the accepted record `2026-11-06-command-gate-and-prose-in-module-calls` shows the same defect in a live run)
Specs: repository-boundary

## Goal

An agent that reads the project instructions knows, before its first Bash call, which command forms the command gate accepts while a key is at `ask` or `none`, which it
refuses, and what to do after a refusal. When the plan is done the base `AGENTS.md` that a new project is seeded with, and this repository's own `AGENTS.md`, hold one short
section on it, and a test pins the section.

## Scope

- A section "Commands the gate accepts" in `base/AGENTS.md`, between "Source of truth" and "Policy", with the text under "The section" below.
- A test that reads the real `base/AGENTS.md` and pins the section and the single `policy` slot marker.
- The sentence in `docs/specs/repository-boundary.md` that describes what the base `AGENTS.md` holds.
- The same section, byte for byte, in this repository's `AGENTS.md`, by a hand edit.

## Non-goals

- Any change to the command gate, its messages or its rules. A refusal that names the rule and the form to run instead already exists (`command-permissions.md`, "The command gate").
- A module's policy block. The section is about the permission tooling, which no module owns.
- Delivering the section to a project that is already installed (see the constraints).
- The harness-lock refusal (`claude is not a known harness ...`). The section does not mention it.

## Assumptions and constraints

- **The base `AGENTS.md` is seeded** (`installer-interface.md`, the seeded-file row; `repository-boundary.md`, "Classes at install"). The installer writes it once at first install and
  keeps it, hashed, on every later install, adopt or upgrade. A change to `base/AGENTS.md` therefore reaches new projects only. An installed project, this repository included, gets
  the section only when its owner edits its own `AGENTS.md`. The owner chose this route over a module block or a new base-owned slot; this plan does not claim that an upgrade delivers it.
  Not run: an upgrade of an installed project to see the base change recorded and `AGENTS.md` kept; the spec says so and increment A's verification does not exercise it.
- Hand-editing this repository's `AGENTS.md` changes a seeded file that the manifest hashed, so the project differs from what was last acknowledged until the owner runs
  `wb acknowledge`. That is the owner's step.
- The section is read by every agent in every session of a project that has it, so it is short (about 20 lines) and names no harness, no module and no module-specific option.
- The rules it states are those of `command-permissions.md` as built: the data-position pipeline of read programs, the exact simple command, the names test, the gap rule, the
  single-quoted `wb run` form and the refusal's closing hint. If the gate changes, the section is revised then.
- `base/` has no approval record; its tree hash is recorded in each project's manifest. `base/` is outside `packages/workbench/`, so the edit does not change a package tree hash.

## Completion criteria

1. `base/AGENTS.md` holds the section once, after "Source of truth" and before "Policy", and still holds exactly one `<!-- @slot: policy -->` marker and the same other headings.
2. The section says each of: run a relaxed command as one simple command on its own (no pipe, `&&`, `;`, redirect, `cd` prefix or variable, no `bash -c` or `env`); name a relaxed command
   as data only in the closed plain-read form of `command-permissions.md` rule 1, and in no other command, and edit a file that holds the word with the edit tools; give text to a `wb run` call in
   single quotes; never reword the owner's text to pass a refusal; use the form a `names` or `gap` refusal ends with once, and stop and report a second refusal or any other rule's refusal.
3. The section names no harness (`claude`, `codex`) and no module option.
4. A test reads the real `base/AGENTS.md` and fails if any of criteria 1 to 3 stops being true.
5. `docs/specs/repository-boundary.md` says the base `AGENTS.md` holds the section.
6. This repository's `AGENTS.md` holds the same section, byte for byte, between "Source of truth" and "Policy", and the rest of the file is unchanged.

## Increments

### Increment A — The section in the base, with its test and spec sentence

**Outcome:** criteria 1 to 5 are true.
**Dependencies:** none.
**Affected areas:** `base/AGENTS.md`, `tests/test_base.py` (or a new `tests/test_base_guidance.py` if the existing file's fixtures do not fit a read of the real base), `docs/specs/repository-boundary.md`
(the line that says what the base `AGENTS.md` holds).
**Steps:**
1. Write the test first. It loads the real base (`base.load_base()` from the distribution) and asserts the criteria: one heading "Commands the gate accepts" between the headings "Source of truth" and
   "Policy"; the five statements of criterion 2 by a phrase each; the one policy marker; no harness name; the section is at most 24 lines. See it fail for the right reason (the heading is absent).
2. Add the section to `base/AGENTS.md` (text below). Change nothing else in the file.
3. Edit the spec line to say the base `AGENTS.md` holds the project's working agreement, source of truth, the section on the command gate, and the `policy` slot marker.
4. Run the verification below. Ask the `reviewer` agent for a read of the increment.
**Verification:** the new or changed base test; `tests.test_base`; the tests that load the base through a fixture or the distribution (`tests.test_blocks`, `tests.test_installplan`,
`tests.test_manifest`, `tests.test_upgradeplan`), because the base content and its tree hash feed the install and upgrade plans; `wb run code-work check`. Not run: the whole suite (no code
changes), an upgrade of an installed project, and an agent following the section (the next live session).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-gate-forms-in-the-base#A`.

### Increment B — The same section in this repository's `AGENTS.md`

**Outcome:** criterion 6 is true.
**Dependencies:** increment A.
**Affected areas:** `AGENTS.md`.
**Steps:**
1. Insert the section, copied from `base/AGENTS.md` as committed in increment A, between "Source of truth" and "Policy" of this repository's `AGENTS.md`. Touch no module block between the
   `BEGIN` and `END` markers and no other line.
2. Compare the inserted lines with the base section byte for byte, and confirm the other lines of `AGENTS.md` are unchanged (`git diff` shows only added lines).
3. Stop and tell the owner that `wb acknowledge` is theirs to run, because a seeded file the manifest hashed has changed.
**Verification:** a byte comparison of the base section with the section in `AGENTS.md`; `git diff --stat` shows one file and only added lines; `wb run code-work check`. Not run: the test
suite (a prose file changed, and increment A pinned the text).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-gate-forms-in-the-base#B`.

## The section

This is the text increment A adds, under the heading `## Commands the gate accepts`. Increment B copies it without change.

```
## Commands the gate accepts

When `wb settings` prints a level of `ask` or `none` for a key, the command gate reads every Bash call for that key's words, in any spelling, and a refusal costs a call.
Write the form that passes the first time.

- Run a relaxed command as one simple command on its own: `wb approve-plan <plan>`, `wb run <command> <argument> ...`. Add no pipe, `&&`, `;`, redirect, `cd` prefix or variable,
  and do not wrap it in `bash -c` or `env`. Run the parts as separate calls.
- Name a relaxed command as data only in a plain read: one `cat`, `diff`, `grep`, `head`, `ls`, `tail` or `wc` call, or a ` | ` pipeline of them, with plain or single-quoted
  arguments and no `$`, backtick, `;`, `&&`, `||`, glob, double quote or redirect (`grep -c 'approve-plan' docs/plans/a.md | head -1`). Do not name it in any other command: not in
  a commit subject, a message, a question, a `grep` with a glob or a `cd` before it, or a script. The gate also finds the word inside longer words and across word breaks, so
  ordinary prose can trip it. Edit a file that holds the word with the edit tools: a `python3 - <<EOF` or `sed -i` pass over it is refused.
- Give free text to a `wb run` call in single quotes, never double quotes. Never reword the owner's text to get past a refusal; say so and stop.
- A refusal of the rules `names` and `gap` ends with the form to run instead. Use that form once. If it is refused again, or the refusal names another rule (`size-limit`,
  `dollar-quote-limit`), stop and report it; do not try a script, an expansion or another shell to reach the same call.
```

## Verification for the plan as a whole

Each increment's recorded verification stands. Increment B changes only a prose file after increment A's commit, so it reruns nothing from A. Whether an agent follows the section is for the
next live session, and whether an installed project can take it by upgrade is not claimed.

## Risks and sensitive actions

- The section is read by every agent in every session of a project that has it. It grows `AGENTS.md` by about 20 lines and its text is exact; a wrong rule would mislead each session.
  The review reads it against `command-permissions.md`, and the test pins the statements.
- A rule that the gate later loosens or tightens makes the section stale. It is revised with the gate change.
- Increment B edits a first-tier file of this project. It changes only added lines, and the owner runs `wb acknowledge` afterwards; nothing here runs it.
- No secret, no code, no subprocess, no network and no permission is touched, so no security review is proposed.

## Review record

**Round 1** (2026-11-06, `ask-codex`, profile `standard`; the engine reports the server's location class as `unknown`; verdict `changes_needed`, 2 meaningful findings, both applied).

- R1-F1, major, applied: the section said not to name a relaxed command in any other command and forbade pipes, but `command-permissions.md` rule 1 frees a closed plain-read form (a pipeline of
  `cat`, `diff`, `grep`, `head`, `ls`, `tail`, `wc`, plain or single-quoted arguments, no `$`, backtick, `;`, `&&`, glob, double quote or redirect). The second bullet and criterion 2 now describe that
  form and keep the ban for every other command.
- R1-F2, major, applied: only `names` and `gap` refusals end with a form to run. The fourth bullet and criterion 2 now say to use that form once and to stop and report a second refusal or a refusal of
  another rule (`size-limit`, `dollar-quote-limit`). The line cap of the test and the size estimates rose from 18 to 24 and from 16 to 20 for the longer text.

## Deferred work

- Delivery to installed projects. Because the base `AGENTS.md` is seeded, an upgrade does not carry the section. A base-owned slot that an upgrade rewrites would, but the base owns exactly two slots
  (`repository-boundary.md`), so it needs a decision and a spec change of its own.
- A closing hint on the gate's script and heredoc refusals ("edit the file with the edit tool"), which is a code change to the gate.
- A pointer from the plan-approval and decision-acceptance bullets in the module blocks to this section.
## Result

**Increment A (2026-11-06), done in the live tree on top of commit `fbe5465`; not yet committed.**

- Built: the section "Commands the gate accepts" in `base/AGENTS.md` (text as in "The section", 14 lines of text under the heading, cap 24); `tests/test_base_guidance.py` (8 tests that read the real
  base: heading once and in order, one policy marker, line cap, the five statements by bullet, the closed plain-read form, single quotes and never reword, retry only for `names` and `gap`, no harness or
  module option); the bullet in `docs/specs/repository-boundary.md` ("The base") now names the section and says the file is seeded, so an installed project does not receive a later change.
- Verification as run: the new tests failed before the section (1 failure, 6 errors, the heading absent) and pass after (8). `tests.test_base`, `tests.test_blocks`, `tests.test_installplan` and
  `tests.test_manifest` (85) pass; `tests.test_upgradeplan` (63) passes; `wb run code-work check` found no problems. Not run: the whole suite (no code changed); an upgrade of an installed
  project; an agent following the section.
- Review: the `reviewer` agent, one exchange, no blocking finding, no security risk named. Applied: the bullet-1 and retry assertions now read their own bullet, and "Use that form once" and "If it is
  refused again" are pinned (the first run pinned words that bullet 2 also holds). Not applied, because the section is the approved text and a change needs a new approval: bullet 2's "a commit
  subject" can be read as banning the literal single-quoted `wb run` form that the gate frees, and "ordinary prose can trip it" is true of `approve-plan` and the `wb run <command> <argument>` keys, not of
  the single-word keys (`wb install`, `wb add`). Both overstate and neither causes a refusal. Fixing the wording needs the owner's new approval of the plan; they are left for a later change.
- Committed as `8ef37c2` (trailer `Plan: 2026-11-06-gate-forms-in-the-base#A`).

**Increment B (2026-11-06), done in the live tree on top of `8ef37c2`; not yet committed.**

- Built: the section "Commands the gate accepts", copied from `base/AGENTS.md` as committed in increment A, inserted in this repository's `AGENTS.md` between "Source of truth" and "Policy". No other line
  changed and no module block was touched.
- Verification as run: a byte comparison of the two sections says identical (15 lines each); `git diff --numstat` for `AGENTS.md` says 15 added, 0 deleted; `wb run code-work check` found no problems.
  Not run: the test suite (a prose file changed and increment A pinned the text), `wb acknowledge` (the owner's).
- Review: the `reviewer` agent, one exchange, no findings and no security risk named. It compared by reading, not by byte, so the byte comparison above is mine.
- Left for the owner: the word to commit increment B, then `wb acknowledge` for the changed seeded file.
