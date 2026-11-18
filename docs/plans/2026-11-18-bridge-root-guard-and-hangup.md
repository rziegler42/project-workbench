# Fix the case-spelled root guard and the hang-up orphan in the model bridges

Status: Proposed
Created: 2026-11-18
Candidate: none (corrections that follow from the two Low findings of the security review in plan `2026-11-18-ask-claude-bridge`)
Specs: model-bridge, ask-claude, ask-ollama

## Goal

Close the two Low findings that the security review of `ask-claude` found and that the older bridges share. When the plan is done:

- `--root` is refused when it is `.git` or `.workbench`, or anything below either, by what the path is and not by how its name is
  spelled, in `ask-claude`, `ask-codex` and `ask-ollama`. On a case-insensitive disk `--root .GIT`, `.Git/` and `.WORKBENCH` are refused
  as `.git` and `.workbench` are, and the absolute spellings with them.
- A hang-up of the helper (SIGHUP, the terminal closing) stops the program it started, as SIGTERM already does, in `ask-claude` and
  `ask-codex`: the process group is killed and the helper exits. A caller that deliberately ignores SIGHUP (for example under `nohup`) is
  not overridden.
- Each fix has a regression test that failed before the fix, in the scratch copy of `HEAD`, and passes after it, and an independent
  second look, because a fix is new attack surface.
- `model-bridge.md` says both rules in words, written after the code that makes them true has landed.

## Scope

- `ask-claude`, `ask-codex` and `ask-ollama`: `working_root` (the guard), and for the first two the signal handlers of the helper's
  `__main__` block, with their tests.
- A re-check of both fixes by the `security-reviewer` agent, on a copy.
- Last, `docs/specs/model-bridge.md` (the path rule in "Input", and guarantee 6), and one line in `ask-claude.md` and `ask-ollama.md`
  where they restate the rule: written after the code, so that a current spec is never ahead of the code.

## Non-goals

- The other notes of the security review: a `--schema` file under `.git` or `.workbench` (the contract forbids those only for
  `--root`), the race between the path check and its use, a recycled process group id, a child that starts its own session, and a child
  that keeps the pipes open after a valid reply.
- Making `--root` a boundary: it is where the program starts and does not limit what it reads, as the contract says.
- SIGKILL of the helper, which cannot be handled.
- Any change to the kit, the installer, the review engine or the action-review engine, or a shared code file for the bridges (each
  helper is one file that imports only the standard library and `wbkit`).
- Changing the options, the objects or the error classes of any bridge.

## Assumptions and constraints

- The three guards are the same line today: `any(part in (".git", ".workbench") for part in os.path.relpath(path, base).split(os.sep))`
  (`ask-claude` line 215, `ask-codex` line 227, `ask-ollama` line 654). `ask-claude` and `ask-codex` already have `is_inside(path,
  boundary)`, which compares with `os.path.samefile` up the ancestors of the real path, so a case spelling that the disk treats as the
  same directory is found. `ask-ollama` has no program and ignores `--root` after validating it, so its fix is for the contract's rule
  and removes nothing it could reach.
- The security reviewer tested the first flaw on this Mac's case-insensitive disk. A case-sensitive disk cannot show it: there `.GIT` does
  not exist and the call is refused as a path that does not exist. A test of the case spelling is therefore skipped on a disk where
  `.GIT` does not resolve, and says so.
- The second flaw: the helper's `__main__` block handles SIGTERM only, so SIGHUP kills the helper and leaves the program, which runs in its
  own session, running. SIGINT already raises `KeyboardInterrupt`, which reaches the `finally` that kills the group.
- A write under `packages/workbench/` locks the tools until the owner releases the approvals: each increment that changes a module
  prepares its files in the scratchpad, applies them in one scripted pass, and then waits for the owner's release. Three release rounds.
- Tests are `unittest`. The verification of a module increment is that module's own tests, and `wb run code-work check`.
  `tests.test_boundary` has two failures on a clean `HEAD` that are not this plan's (on the owner's todo list) and is not part of any
  verification here.
- **Every increment is reviewed before its commit.** After its verification, each increment, the second look (D) and the contract text
  (E) included, goes to the `reviewer` agent (`request-review`), which gets the plan path and increment, the changed paths, the
  verification as run and the spec sections, and not this plan's conclusions. Each finding is judged (`evaluate-findings`), and is
  applied or deferred with its reason, in the increment's entry in the Result, before the commit is made. Stops are at the caps of
  `wb settings`: at most 3 review rounds and 6 reviewer exchanges.
- **The root matrix** (one definition, required of each bridge). In the test project, whose `.git` and `.workbench` are directories
  with a subdirectory in each (`hooks` and `local`): the names `N` are `.git`, `.GIT`, `.Git`, `.workbench`, `.WORKBENCH` and
  `.WorkBench`; the forms of each are `N`, `./N`, `N/` and the absolute `<project>/N`; and the descendants are `N/<sub>` in the same
  forms. Every cell is one `subTest` of a loop in the module's tests, expecting the module's existing refusal for the root and no
  program started or request sent. Cells whose name is not the exact lower-case `.git` or `.workbench` need a disk on which that
  spelling resolves to the real directory, and are skipped with the reason named where it does not. The exact lower-case cells are
  already covered where a module's tests have them (each increment lists which are retained and which are new, in the Result); the
  case variants and the descendants are the new regressions. Two more cases are part of the matrix and must be accepted: the project
  root itself, and a directory whose name only starts with the same letters (for example `.gitx`, made for the test).
- The helper names `ask-claude`, `ask-codex` and `ask-ollama` are unique across modules, and the installer and its tests do not name them.

## Completion criteria

1. In each of the three bridges, every cell of the root matrix above is refused with the existing message before anything runs, and the
   two accepted cases are accepted, shown by tests that run on a case-insensitive disk and are skipped, with the reason named, on a
   case-sensitive one.
2. In `ask-claude` and `ask-codex`, a SIGHUP sent to the helper while it waits for a hanging fake program kills the fake and its
   children and ends the helper with exit code 129, and the existing SIGTERM test still passes with exit code 143; with SIGHUP ignored
   by the caller the helper does not install a handler for it.
3. Each regression test failed against the unchanged helper in a scratch copy of `HEAD` and passes after the change.
4. The `security-reviewer` agent has re-checked both fixes on a copy and its report is recorded in the Result.
5. `model-bridge.md` states both rules, committed after the three bridges implement them, and `ask-claude.md` and `ask-ollama.md` agree.
6. The shipped approvals are released by the owner after each module change and the records are committed with it.

## Increments

### Increment A — `ask-claude`

**Outcome:** the two fixes in `ask-claude`, each with a test that failed first.
**Dependencies:** none.
**Affected areas:** `packages/workbench/ask-claude/helper/ask-claude` (`working_root`, the `__main__` block),
`packages/workbench/ask-claude/tests/test_askclaude_module.py` or `test_askclaude_run.py`, and the shipped approval records (owner-run).
**Steps:**
1. Write the tests: the whole root matrix of the assumptions, as one `subTest` loop (the cells that `ask-claude`'s tests already have
   are kept and listed as retained; the rest are new), including the two accepted cases; a copy of the existing SIGTERM test for
   SIGHUP: the helper run as a subprocess with a hanging fake, SIGHUP sent, the fake and its child gone, exit code 129; and a test
   that a caller that ignores SIGHUP is not overridden (the handler is not installed).
2. Prepare, in the scratchpad, a copy of `HEAD` with the tests only and see them fail for the right reason.
3. Change `working_root` to refuse a root that `is_inside` finds to be `.git` or `.workbench` of the project when that entry exists, in
   addition to the existing name check. Change the `__main__` block to install the same handler for SIGTERM and SIGHUP, exiting with
   128 plus the signal number, except where SIGHUP is already ignored.
4. Apply the change to the real tree in one scripted pass, with its verification; the owner releases the approvals.
**Verification:** `python3 -B -W error -m unittest discover -s packages/workbench/ask-claude/tests -t packages/workbench/ask-claude/tests`;
the `claude` module's tests after the release (they check the shipped records); `wb run code-work check`. No other module's tests
change.
**Evidence:** the reviewer's findings and what was done with each, recorded in the Result; then the one local commit, with the trailer
`Plan: 2026-11-18-bridge-root-guard-and-hangup#A`, holding the helper, the tests and the new release records.

### Increment B — `ask-codex`

**Outcome:** the same two fixes in `ask-codex`.
**Dependencies:** none (A is done first only so that its tests are the model for this one).
**Affected areas:** `packages/workbench/ask-codex/helper/ask-codex`, `packages/workbench/ask-codex/tests/test_askcodex_run.py` (and the
module test where the declaration is checked), and the shipped approval records (owner-run).
**Steps:**
1. Write the tests as in increment A: the whole root matrix, with the cells that the module's tests already have kept and listed as
   retained, the SIGHUP test adapted to the helper's own fake and its existing terminate test (which also checks that the scratch
   directory is removed: the SIGHUP test checks that too), and the ignored-SIGHUP test.
2. See them fail in a scratch copy of `HEAD`.
3. Make the change as in A; the scratch directory is removed by the same `finally`.
4. Apply in one scripted pass; the owner releases the approvals.
**Verification:** `python3 -B -W error -m unittest discover -s packages/workbench/ask-codex/tests -t packages/workbench/ask-codex/tests`;
the `claude` module's tests after the release; `wb run code-work check`.
**Evidence:** the reviewer's findings and what was done with each, recorded in the Result; then the one local commit, with the trailer
`Plan: 2026-11-18-bridge-root-guard-and-hangup#B`.

### Increment C — `ask-ollama`

**Outcome:** the guard fix in `ask-ollama` (no signal change: it starts no program).
**Dependencies:** none.
**Affected areas:** `packages/workbench/ask-ollama/helper/ask-ollama` (the guard at its line 654),
`packages/workbench/ask-ollama/tests/` (the file that tests the root rules), and the shipped approval records (owner-run).
**Steps:**
1. Find where the tests cover `--root` inside `.git` or `.workbench` and add the rest of the root matrix, with the cells already
   covered kept and listed as retained, the case variants and descendants as new, and the two accepted cases; skipped, with the
   reason named, on a case-sensitive disk.
2. See them fail in a scratch copy of `HEAD`.
3. Reuse the same `is_inside` rule: `ask-ollama` has no `is_inside`, so add the function (the same code as the other two) or compare
   with `os.path.samefile` directly, whichever is smaller; the helper must keep importing the standard library and `wbkit` only.
4. Apply in one scripted pass; the owner releases the approvals.
**Verification:** `python3 -B -W error -m unittest discover -s packages/workbench/ask-ollama/tests -t packages/workbench/ask-ollama/tests`;
the `claude` module's tests after the release; `wb run code-work check`.
**Evidence:** the reviewer's findings and what was done with each, recorded in the Result; then the one local commit, with the trailer
`Plan: 2026-11-18-bridge-root-guard-and-hangup#C`.

### Increment D — The second look

**Outcome:** an independent re-check of both fixes, recorded.
**Dependencies:** A, B and C.
**Affected areas:** this plan's Result only; no code changes unless the re-check finds a flaw, which becomes a new increment.
**Steps:**
1. Ask the owner (once for this surface) whether to run it, and then run the `security-reviewer` agent on a copy, with the
   three helpers and the fixes' diffs: the case spellings, a link to `.git`, a path below it, a root equal to the project root, a
   SIGHUP with the program ignoring SIGTERM and forking, a SIGHUP while the prompt is still being written, and SIGHUP ignored by the caller.
2. Record its report, what was tested and what was only read, and what it could not check.
**Verification:** `wb run code-work check`; the reviewer's own tests on the copy.
**Evidence:** the security report as recorded, a `reviewer` read of that record against the diffs (its findings and what was done with
each, recorded in the Result), and then the one local commit, with the trailer `Plan: 2026-11-18-bridge-root-guard-and-hangup#D`,
holding the plan's Result.

### Increment E — The contract text

**Outcome:** `model-bridge.md` says that the guard on `--root` compares what the path is, however its letters are spelled, and that a
hang-up of the helper stops the program as a termination does; `ask-claude.md` and `ask-ollama.md` agree. It is written after the code
and the second look, so that no committed spec is ahead of the code.
**Dependencies:** A, B, C and D.
**Affected areas:** `docs/specs/model-bridge.md` ("Input", "Paths" and the guarantee 6 text), `docs/specs/ask-claude.md` and
`docs/specs/ask-ollama.md` (one line each where they restate the path rule or the timeout).
**Steps:**
1. Read the places where the specs state "not inside `.git` or `.workbench`" and the timeout guarantee.
2. In "Paths", add that the comparison is by the directory the path names and not by its spelling, so a case variant on a
   case-insensitive disk is refused.
3. In guarantee 6, add that a hang-up or a termination of the helper kills the process group of the program, and that the helper does
   not override a hang-up that its caller ignores. Add one line to the conformance checklist item 11 for it.
4. Make the matching one-line statements in `ask-claude.md` and `ask-ollama.md`, and take the two Low findings out of the open limits
   of `ask-claude.md` ("The first run of the release check") with a pointer to this plan.
**Verification:** `wb run code-work check`; the changed text is read against the three helpers as they now are.
**Evidence:** the reviewer's findings and what was done with each, recorded in the Result; then the one local commit, with the trailer
`Plan: 2026-11-18-bridge-root-guard-and-hangup#E`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later one changed its inputs: the three helpers are separate files and the
three modules' tests do not share code, so A, B and C do not invalidate one another. What is rerun at the end: nothing beyond
increment E's check, except `wb verify packages/workbench` once after the last release. A run of the whole suite
(`python3 -B -W error tests/run_all.py`) is not planned; the one thing outside the modules that changes is the set of shipped approval
records, which the `claude` module's tests check after each release.

## Risks and sensitive actions

- **A signal handler in a program that starts another program.** A handler that exits from inside a blocking call is the same
  mechanism SIGTERM already uses, so it adds no new path, but a test must show the program's group is killed for SIGHUP and that a
  hang-up that the caller ignores is not overridden (a `nohup` run).
- **A guard that refuses too much.** `is_inside` climbs the ancestors of the real path and compares each with `samefile`. A project
  whose root is itself inside a directory named `.git` is not a case this plan changes (the guard compares with the project's own
  `.git`, below its root), and a root that is the project root must still be accepted: a test says so.
- **Case-sensitive disks.** The case-spelling tests cannot fail there and are skipped; the fix is then shown only by reading and by
  the second look on this Mac's disk. The plan says so in the Result.
- **Three package edits, three releases.** Each release is the owner's, in a terminal, with the tools locked until then.
- **Security.** The change touches a path guard, a subprocess and signals; increment D is the second look, and a fix that fails it
  is a new increment.

## Review record

Empty until a review is asked for.

## Deferred work

- The race between the path check and its use, and the notes of the security review that this plan does not take.
- A `--schema` file under `.git` or `.workbench`, if the owner wants the contract to forbid it.
- One shared copy of the path and signal code for the bridges, which the one-file rule of a helper forbids today.

## Result

### Increment A

- `ask-claude`: `working_root` now also refuses a root that `is_inside` finds to be the project's `.git` or `.workbench` or below one
  (when the entry exists), after the unchanged name check; the `__main__` block installs one handler, `sys.exit(128 + signum)`, for
  SIGTERM and, unless SIGHUP is already ignored, for SIGHUP. New `tests/test_askclaude_guards.py`: the root matrix as `subTest` loops
  (6 names x 4 forms x root and descendant = 48 cells: 16 lower-case, retained in kind from `test_askclaude_module.py`, which has the exact
  `.git` and `.workbench` as a relative path, and 32 case-variant cells, new), the two accepted cases (the project root in four spellings,
  and `.gitx`, `.workbench-old`, `.github`), a nested `sub/.git`, and the signals (SIGTERM gives 143, SIGHUP 129, SIGINT stops the
  program, an ignored SIGHUP is not overridden).
- Verification run on the real tree: the module's 75 tests OK (67 before); the `claude` module's tests 34 OK (12 skipped), also after
  the owner's release; `wb run code-work check` no problems; `wb verify packages/workbench` lists the module at its new tree. Red run in a
  scratch copy of `HEAD`: all 32 case-variant cells and the SIGHUP test failed against the unchanged helper (the rest passed, as
  they pin existing behaviour). Five deliberate breaks of the fixed helper (guard loop disabled, hang-up handler not installed, handler
  installed though SIGHUP is ignored, exit code fixed at 143, guard comparing with the project root) each failed tests. This Mac's disk
  is case-insensitive, so the case-variant cells ran; they skip on a case-sensitive disk. Not run: a case-sensitive disk, the full suite.
- The installed copy in this project (`.workbench/workbench/ask-claude/`) is the version before this increment until the owner runs
  `wb upgrade`; that is the owner's step and is not part of the commit.
- Review: one `reviewer` round, no blocking finding. Deferred to increment D, the second look: a SIGHUP or SIGTERM that lands between
  `Popen` returning and the `try` that holds the cleanup in `run_program` (the group could be left running; SIGTERM already had this window
  and SIGHUP now shares it), and a link into `.git`, a `.git` that is a file (a worktree) and a dangling `.git` (correct by reading, not
  tested). On the owner's todo list: skip the SIGINT test when the runner ignores SIGINT. Not changed: the case-variant test skips as
  a whole when any spelling does not resolve, which is what the plan says.
- Release: the owner released; two new records (the package and `ask-claude`) are committed with the increment.
- (Increment A was committed as `eb73eed`.)

### Increment B

- `ask-codex`: the same two changes as in A, line for line (the `__main__` block differs only in its comment): `working_root` also
  refuses a root that `is_inside` finds to be the project's `.git` or `.workbench` or below one, and one handler, `sys.exit(128 +
  signum)`, serves SIGTERM and, unless SIGHUP is already ignored, SIGHUP. New `tests/test_askcodex_guards.py`, generated from the
  `ask-claude` one with the names swapped: the root matrix (48 cells: the 16 lower-case ones are retained in kind from
  `test_a_root_inside_git_or_the_workbench_directory_is_refused`, which also has `docs/.git` and `docs/.git/x`; the 32 case-variant
  cells are new), the two accepted cases, a nested `sub/.git`, and the signals (SIGTERM 143, SIGHUP 129, SIGINT, an ignored SIGHUP not
  overridden), each also asserting that the scratch directory of the call is gone, which `ask-claude` does not have.
- Verification run on the real tree: the module's 111 tests OK (79 before); the `claude` module's tests 34 OK (12 skipped), also after the
  owner's release; `wb run code-work check` no problems; `wb verify packages/workbench` lists the module at its new tree. Red run in a
  scratch copy of `HEAD`: the 32 case-variant cells and the SIGHUP test failed against the unchanged helper. Five deliberate breaks of the
  fixed helper (guard loop disabled, handler not installed, handler installed though SIGHUP is ignored, exit code fixed at 143, guard
  comparing with the project root) each failed tests. Not run: a case-sensitive disk, the full suite.
- The installed copy of `ask-codex` in this project is the version before this increment until the owner runs `wb upgrade`.
- Review: one `reviewer` round, no blocking finding. Deferred to increment D, the second look: in `ask`, `mkdtemp` comes before the
  `try` that removes the scratch directory, so a signal that lands inside `mkdtemp` after its mkdir, or in the bytecodes before the `try`,
  leaves an empty `ask-codex-*` directory in the temporary directory (SIGTERM already had this window and SIGHUP shares it; it
  exposes nothing; a fix is `scratch = None` before the `try` with the `mkdtemp` inside it, and no test can pin it). Not changed: the
  docstring of the new test file says it "replaces" the older SIGTERM test, which is still in `test_askcodex_run.py` (harmless overlap);
  a failed signal assertion can leave the fake `codex` running its 300-second sleep, a leak on a failure path only; the SIGINT test
  fails if the runner ignores SIGINT (already on the owner's todo list).
- Release: the owner released; two new records (the package and `ask-codex`) are committed with the increment.
- (Increment B was committed as `4c19d0e`.)

### Increment C

- `ask-ollama`: a new `is_inside(path, boundary)` above `check_root` (a diff against the copies in `ask-claude` and `ask-codex` shows
  the three are identical), and `check_root` now also refuses a root that `is_inside` finds to be the project's `.git` or `.workbench`
  or below one, when that entry exists, after the unchanged name check. No signal change: this bridge starts no program. The helper
  imports nothing new. New `tests/test_askollama_guards.py`: the root matrix (48 cells: the exact lower-case `.git` and `.workbench` as a
  relative path are retained from `test_a_root_inside_git_or_the_workbench_directory_is_refused`, and the file also runs the other 14
  lower-case cells; the 32 case-variant cells are new), the accepted cases (the project root in four spellings, and `.gitx`,
  `.workbench-old`, `.github`, `docs`, each checked to reach the fake server), and a nested `sub/.git`.
- Verification run on the real tree: the module's 443 tests OK (439 before; they include the module's imports test); the `claude`
  module's tests 34 OK (12 skipped), also after the owner's release; `wb run code-work check` no problems; `wb verify packages/workbench`
  lists the module at its new tree. Red run in a scratch copy of `HEAD`: exactly the 32 case-variant cells failed against the unchanged
  helper, nothing else. Three deliberate breaks of the fixed helper (guard loop disabled, guard comparing with the project root, guard
  comparing only the path itself with `samefile` so that descendants slip through) each failed tests. Not run: a case-sensitive disk,
  the full suite.
- The installed copy of `ask-ollama` in this project is the version before this increment until the owner runs `wb upgrade`.
- Review: one `reviewer` round, no blocking finding and nothing to defer: the guard is called only from `ask` behind `--root`, the
  refusal text is constant and shows no address, an `OSError` in `is_inside` fails closed, and the tests cannot pass while the guard is
  too broad (the accepted cases) or too narrow (the matrix). Not changed: the case-variant test skips as a whole when any spelling does
  not resolve, as the plan says.
- Release: the owner released; two new records (the package and `ask-ollama`) are committed with the increment.
- (Increment C was committed as `0ff8b51`.)

### Increment D

- The owner said to run the second look. The `security-reviewer` agent worked on copies of the three helpers in its scratch directory
  (Python 3.15.0, this Mac's case-insensitive APFS), with fake programs; no real `claude` or `codex`, no network. The tree was clean
  before and after (`git status --short` printed nothing at `0ff8b51`). Its report, in short: no Critical, High or Medium finding; three
  Low.
- **Low 1, a flaw in what this plan set out to do.** The interrupt path of `run_program` (the `finally`, `if process.poll() is None`)
  kills the program's process group only while the program's main process is still running. If the main process has exited and a
  child of it still holds the output pipes, a SIGHUP, SIGTERM or SIGINT leaves that child running, in both `ask-claude` and `ask-codex`
  (tested: the child was alive after exit 129 and after exit 143). SIGTERM always had this; the new SIGHUP handler routes the hang-up
  into it. **So the plan's Goal bullet (a hang-up stops the program it started: the process group is killed and the helper exits) is
  not true in that case, and criterion 2, which is worded around a fake program that hangs and its children, is true only for the fake
  that the tests use, whose main process stays alive; the signal tests of increments A and B do not show the case for that reason.**
  The non-goal about a child that keeps the pipes open after a valid reply is the normal path and does not cover this. The reviewer's
  correction was an unconditional kill in the `finally`; that would also send a second `killpg` on every successful call, to a group
  that the normal path has already killed and reaped, and a `killpg` of the pid of a reaped leader could reach an unrelated group that
  took the number (the recycled process group id, a non-goal of this plan, which an interrupt would otherwise meet only when the
  leader is gone). So the better correction is a flag set after the normal path's kill, with the `finally` killing when it is unset (an
  interrupt that lands between the kill and the flag only gives a harmless second kill). This needs a plan change and the owner's
  approval (a new increment `D-A`, and a criterion 2 that covers a program whose main process has exited).
- **Low 2, three narrow windows**, shown on copies with a deliberate pause and measured, and not hit at normal timing: (2a) a signal
  between `Popen` returning and the `try` (a fraction of a microsecond), and inside `Popen` after the fork (a fraction of a millisecond)
  leaves the program's group running, in both helpers; (2b) a second signal while the first is being handled, before the kill in the
  `finally` (tens of microseconds), leaves the group running, because the handler stays installed and has no re-entry guard; (2c) in
  `ask-codex`, between `mkdtemp` and the `try`, leaves an empty `ask-codex-*` directory. Corrections named: (2b) the handler sets
  SIGTERM and SIGHUP to ignore on its first call, which is cheap and also covers the whole `finally`; (2c) `scratch = None` before the
  `try` and `mkdtemp` inside it; (2a) the first part by moving `Popen` inside the `try`, the fork-to-exec part not at all without signal
  masking that the program might inherit (untested).
- **Low 3, informational:** if `.git` or `.workbench` links to the project root or to an ancestor, the guard refuses every root,
  which fails closed.
- Tested and sound: the guard refuses every case spelling, descendant, link, worktree file and Unicode variant that resolves on this
  disk (Kelvin-sign spellings included, caught by `samefile`), and accepts the project root, names that share only a prefix, a
  project below a directory named `.git`, a worktree project and a dangling `.git`; the same results in all three bridges, whose three
  `is_inside` and three guard bodies are identical; SIGHUP and SIGTERM kill the group (exit 129 and 143) for a program that ignores
  SIGTERM and forks, one that closes its output and sleeps, and with a prompt still being written; an ignored or blocked SIGHUP is left
  alone; `ask-codex` removes its scratch directory on both signals when the signal lands inside the `try`. Read only: `ask-ollama`
  starts no program; a `.git` link whose target cannot be read (fails closed by reading); the `--schema` under `.git` allowance
  (a non-goal). Limits: one disk and one Python; nothing on a case-sensitive disk; no real program; the repository's tests and the spec
  text were not part of its review.
- Limits of this record: the measured results (the surviving child after exit 129 and 143, the timing figures, the Kelvin-sign and
  other Unicode cases, the clean tree before and after) are the security reviewer's, and the author did not rerun them; the author
  confirmed by reading the code only the logic of Low 1 and of the three windows, and ran `git status --short` (empty) at `0ff8b51`.
  Gaps in the corrections named: moving `Popen` inside the `try` also needs `process = None` before it and a guard in the `finally`; the
  ignore-on-first-call handler (2b) does not cover a second SIGINT, which raises `KeyboardInterrupt`; moving `mkdtemp` inside the `try`
  (2c) needs `if scratch` in the `finally` and still leaves a signal inside `mkdtemp` after its mkdir, before it returns (increment B's
  review named it; no test can pin it).
- Verification of this increment: it changes no code. `wb run code-work check` no problems. The `reviewer` read of this record
  (the plan's evidence step for D) found no blocking finding; it confirmed Low 1 by reading `run_program` and both fakes, and its notes
  are applied in this entry.
