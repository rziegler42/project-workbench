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
  not overridden. (Increments A and B did this for a program whose main process is still running. The second look, increment D, found
  that a SIGHUP, SIGTERM or SIGINT leaves a child of the program running when the main process has already exited and the child still
  holds the pipes; increment D-A closes that, so that the group is killed whether or not the main process is still running.)
- Each fix has a regression test that failed before the fix, in the scratch copy of `HEAD`, and passes after it, and an independent
  second look, because a fix is new attack surface.
- `model-bridge.md` says both rules in words, written after the code that makes them true has landed.

## Scope

- `ask-claude`, `ask-codex` and `ask-ollama`: `working_root` (the guard), and for the first two the signal handlers of the helper's
  `__main__` block, with their tests.
- A re-check of both fixes by the `security-reviewer` agent, on a copy (done: increment D).
- Increment D-A, which the re-check made necessary: in `ask-claude` and `ask-codex`, the cleanup of `run_program` kills the program's group
  on an interrupt whether or not the main process has exited; the signal handler ignores a further stop signal once it has run; and in
  `ask-codex` the scratch directory is made inside the `try` that removes it.
- Last, `docs/specs/model-bridge.md` (the path rule in "Input", and guarantee 6), and one line in `ask-claude.md` and `ask-ollama.md`
  where they restate the rule: written after the code, so that a current spec is never ahead of the code.

## Non-goals

- The other notes of the security review: a `--schema` file under `.git` or `.workbench` (the contract forbids those only for
  `--root`), the race between the path check and its use, a recycled process group id, a child that starts its own session, and a child
  that keeps the pipes open after a valid reply.
- Making `--root` a boundary: it is where the program starts and does not limit what it reads, as the contract says.
- SIGKILL of the helper, which cannot be handled.
- A stop signal that lands between `subprocess.Popen` returning and the `try` that holds the cleanup, or inside `Popen` after the fork
  (found by the second look; a fraction of a microsecond and a fraction of a millisecond, shown only on copies with a deliberate
  pause). The fork-to-exec part cannot be closed without masking signals, which the program might inherit through the exec; the
  other part is a window of bytecodes. Both are recorded as residual risk, not fixed here.
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
  prepares its files in the scratchpad, applies them in one scripted pass, and then waits for the owner's release. Four release rounds
  (A, B, C and D-A).
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
   by the caller the helper does not install a handler for it. (Met by A and B for a fake whose main process is still running; widened
   by criterion 7.)
3. Each regression test failed against the unchanged helper in a scratch copy of `HEAD` and passes after the change.
4. The `security-reviewer` agent has re-checked both fixes on a copy and its report is recorded in the Result.
5. `model-bridge.md` states both rules, committed after the three bridges implement them, and `ask-claude.md` and `ask-ollama.md` agree.
6. The shipped approvals are released by the owner after each module change and the records are committed with it.
7. In `ask-claude` and `ask-codex`, a SIGHUP, a SIGTERM and a SIGINT sent to the helper while the program's main process has already
   exited and a child of it holds the pipes kill that child and end the helper with exit code 129, 143 and 130; and a successful call
   kills the program's group once, as before (a test counts the kills); and an interrupt during the normal path's waits does not kill
   again (a test raises in the first wait and counts the kills).
8. In both, once the handler has run, a further SIGTERM, SIGHUP or SIGINT does not interrupt the cleanup (a test calls the handler
   and checks that all three signals are then ignored); in `ask-codex` the scratch directory is made inside the `try` that removes it
   (a structural test), and the cleanup removes it only if it was made.

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

### Increment D-A — Kill the program's group on any interrupt, and close the small windows

**Outcome:** in `ask-claude` and `ask-codex`, an interrupt (SIGHUP, SIGTERM or SIGINT) kills the program's process group whether or not
the program's main process has exited; a first stop signal makes the handler ignore the others, so that the cleanup is not interrupted;
and in `ask-codex` the scratch directory is made inside the `try` that removes it. The three findings of increment D that are not
residual (Low 1, 2b and 2c) are closed, and each has a test that failed first.
**Dependencies:** A and B (it changes the same two helpers and extends their signal tests); D (its record is the reason).
**Affected areas:** `packages/workbench/ask-claude/helper/ask-claude` and `packages/workbench/ask-codex/helper/ask-codex` (`run_program`,
the handler and the `__main__` block, and in `ask-codex` `ask`), the fakes in `tests/support_claude.py` and `tests/support_codex.py` (one
new control), the signal tests of the two modules, and the shipped approval records (owner-run). One scripted pass for both modules, so
that one release serves both.
**Steps:**
1. Add to each fake a control `orphan`: the fake records its call, starts a child that sleeps and holds the inherited output pipes,
   writes the child's pid to `pids`, and exits at once, so that the program's main process is gone while a child holds the pipes.
2. Write the tests, in the scratch copy first: (a) with `orphan`, the helper run as a subprocess, a SIGHUP, a SIGTERM and a SIGINT each
   (three tests per module) end the helper with 129, 143 and 130 and leave the child gone; (b) with `orphan` and `--timeout 1`, the
   timeout kills the child (it must already pass); (c) a successful in-process call, with `kill` replaced by a counter, calls it once,
   and a call in which the first `process.wait` is made to raise `SystemExit` (as the handler does) calls it once too, the second
   test failing against a flag set after the waits;
   (d) the handler, a module-level function `stop(signum, frame)`, called with `signal.signal` replaced by a recorder, sets SIGTERM, SIGHUP
   and SIGINT to ignore and raises `SystemExit(128 + signum)`; (e) for `ask-codex`, a structural test (the syntax tree of `ask`) that
   the call of `tempfile.mkdtemp` lies inside the `try` whose `finally` removes the scratch directory, and that the `finally` removes it
   only if it was made; and the existing signal tests, with the SIGINT test now expecting 130. Run them against the unchanged helpers and
   see (a), (d) and (e) fail and (b) and (c) pass.
3. Change `run_program`: a flag, set immediately after the normal path's first `kill(process)` and before any of its waits; the
   `finally` kills the group and waits whenever the flag is unset, and does not call `poll()` first (so that an exited but unreaped
   main process keeps its pid, and a `killpg` of its group cannot reach a recycled number). An interrupt during the normal path's waits
   then finds the flag set and does not kill again: the group has already been sent SIGKILL, and a leader that is reaped by then is
   never the target of a second `killpg`. An interrupt in the few bytecodes between the kill and the flag finds the leader not yet
   reaped (no wait has run), so a second kill reaches the same group and not a recycled number. Change the handler to the module-level function of step 2 and install it for SIGTERM, for SIGHUP and for
   SIGINT, each unless the caller already ignores it. In `ask-codex`, set `scratch = None` before the `try`, make the directory inside
   it, and have the `finally` remove it only if it is set. Leave the window between `Popen` and the `try` as it is (residual).
4. Apply to the real tree in one scripted pass with the verification; mutation-check the helpers (the flag removed, the unconditional
   kill, the handler not ignoring, `mkdtemp` outside the `try`); the owner releases the approvals.
**Verification:** `python3 -B -W error -m unittest discover -s packages/workbench/ask-claude/tests -t packages/workbench/ask-claude/tests`
and the same for `ask-codex`; the `claude` module's tests after the release; `wb run code-work check`. `ask-ollama` and the other modules
are not touched.
**Evidence:** the reviewer's findings and what was done with each, recorded in the Result; then the one local commit, with the trailer
`Plan: 2026-11-18-bridge-root-guard-and-hangup#D-A`, holding the two helpers, the tests and the new release records. After it, a second
`security-reviewer` run on the two changed functions only, at the owner's word, is recommended and not required.

### Increment E — The contract text

**Outcome:** `model-bridge.md` says that the guard on `--root` compares what the path is, however its letters are spelled, and that a
hang-up, a termination or an interrupt of the helper kills the program's process group whether or not its main process is still
running (a child that starts its own session stays out of reach), and that the helper does not override a hang-up its caller ignores;
`ask-claude.md` and `ask-ollama.md` agree. It is written after the code and the second look, so that no committed spec is ahead of
the code.
**Dependencies:** A, B, C, D and D-A.
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
three modules' tests do not share code, so A, B and C do not invalidate one another; D-A changes the helpers and signal tests of A and
B, and reruns the whole of those two modules' tests, which is why it is verified with them. What is rerun at the end: nothing beyond
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
- **Four package edits, four releases.** Each release is the owner's, in a terminal, with the tools locked until then.
- **A handler that ignores signals.** After its first call the handler sets SIGTERM, SIGHUP and SIGINT to ignore. It runs only when the
  helper is about to exit, after the program has been started, and a signal ignored in the helper is not inherited by a program
  started before; the helper starts no other program. A test shows what the handler sets, and a test shows that the exit code is still
  128 plus the signal number.
- **The kill in the cleanup.** The `finally` kills the group on an interrupt even when the main process has exited, so that the pid
  used for `killpg` must still belong to the group: the cleanup does not call `poll()` first, so an exited but unreaped main process
  keeps its pid until the kill, and a group with no member left gives `ProcessLookupError`, which `kill` already ignores. The flag
  keeps the normal path to one kill, and it is set before the normal path's waits, because a wait reaps the leader and a later
  `killpg` of a reaped leader's number is the recycled-group risk that this plan accepts as residual; that risk remains only where the
  leader is reaped by something other than this helper's own waits, which nothing here does.
- **Security.** The change touches a path guard, a subprocess and signals; increment D is the second look, and a fix that fails it
  is a new increment.

## Review record

- The plan: three rounds of the review engine through `ask-codex` (findings: the contract text ahead of the code, an undefined test
  matrix, no per-increment review step; all applied), then, after the second look had found that a hang-up did not stop a child of a
  program whose main process had exited, increment D-A was added and a fourth round (the bound extended by the owner to 4) found one
  minor point, the placement of the flag, which was applied. Review files: `.workbench/workbench/review-engine/plan-bc90d9337431bde5/`.
- Each increment, A to E and D-A: one `reviewer` agent round, no blocking finding; the findings and what was done with each are in
  the Result. A second look by the `security-reviewer` agent after A to C (no finding above Low; one that contradicted the plan's
  claim and led to D-A) and a re-check after D-A (no finding above Low; three Low, one on the owner's todo list).

## Deferred work

- The race between the path check and its use, and the notes of the security review that this plan does not take.
- A stop signal between `Popen` returning and the `try` of `run_program`, or inside `Popen` after the fork, which can leave the
  program's group running (residual; see the non-goals). A signal inside `tempfile.mkdtemp` after its mkdir, before it returns, which
  leaves an empty scratch directory.
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
- (Increment D was committed as `7d540f3`. The plan was then changed by increment D-A, reviewed once more by Codex (round 4, bound
  extended by the owner to 4) and approved again.)

### Increment D-A

- `ask-claude` and `ask-codex`: in `run_program` a flag `killed`, set right after the normal path's first `kill(process)` and before
  its waits; the `finally` kills the group and waits when the flag is unset and no longer calls `poll()`. A module-level
  `STOP_SIGNALS` and handler `stop(signum, frame)`: it sets SIGTERM, SIGHUP and SIGINT to ignore and exits with 128 plus the number
  (129, 143, 130); the `__main__` block installs it for each of the three unless the caller already ignores that one (so SIGTERM
  and SIGINT are now left alone when ignored, which they were not for SIGTERM before). In `ask-codex`, `scratch = None` before the
  `try`, `mkdtemp` inside it, and the removal only `if scratch is not None`. New fake control `orphan` in both fakes; new
  `test_askclaude_cleanup.py` and `test_askcodex_cleanup.py` (the second also has the scratch directory checked after each stop, the
  structural test of `ask`, and a test that a failing `mkdtemp` is a refusal and not a crash); the SIGINT test of the guards files now
  expects 130.
- Deviation from the plan's text: step 2(c) says a test makes "the first `process.wait`" raise; the first wait comes before the
  normal path's kill, so it cannot show the ordering of the flag. The tests make the wait after the kill raise (the one that must
  not kill again) and, separately, the first wait (which must kill once): both are in `Kills`.
- Verification run on the real tree: the `ask-claude` tests 84 OK (75 before); the `ask-codex` tests 122 OK (111 before); the `claude`
  module's tests 34 OK (12 skipped), also after the owner's release; `wb run code-work check` no problems; `wb verify
  packages/workbench` lists both modules at their new trees. Red run in a scratch copy of `HEAD`: against the unchanged helpers the
  three orphan-stop tests (SIGHUP, SIGTERM, SIGINT), the handler test, the ignored-SIGTERM test, the interrupt-before-the-kill test
  (which confirms Low 1 from a second side: the old cleanup skips the kill once the main process has exited), the SIGINT-130 test
  and, in `ask-codex`, the structural test failed; the successful-call kill count, the interrupt-during-the-waits count and the
  timeout-with-an-orphan tests passed, as they pin behaviour that existed. Mutation checks, all caught: the flag set after the
  waits, an unconditional kill, a handler that does not ignore, the `poll()` guard back, SIGINT left out of the handler set, and in
  `ask-codex` `mkdtemp` outside the `try`, the removal unguarded (caught only after a test was added that a failing `mkdtemp` is a
  refusal; the structural test alone did not catch it) and the removal dropped. Not run: a case-sensitive disk, the full suite, a
  second `security-reviewer` run (recommended in the plan, at the owner's word).
- The installed copies of `ask-claude` and `ask-codex` in this project are the versions before A, B and D-A until the owner runs
  `wb upgrade`; `ask-ollama` too (increment C).
- Review: one `reviewer` round, no blocking finding. **A residual the review found, which the plan's Risks text does not say:** the
  normal path's first `wait()` reaps the program's main process and the flag is set only after the `kill` that follows it, so a stop
  signal in those few bytecodes reaches the `finally` with the flag unset and a reaped leader, and sends `killpg` to that pid. The old
  `poll()` guard avoided this. It needs the group to have no member left for the number to be reusable, it is not reachable from
  input, and it is a window of bytecodes; setting the flag earlier would trade it for a window in which the kill is skipped, which is
  worse. So the plan's sentence that the recycled-group risk "remains only where the leader is reaped by something other than this
  helper's own waits" is incomplete: the first wait counts. It is recorded here as part of the accepted recycled-group residual, and
  increment E says so in the contract text. Other notes, no action: a second signal that arrives before the handler has run can change
  the exit code only; a signal that a background-job runner ignores stays ignored, by design; the read of the `pids` file in the
  tests could in theory race with the fake writing it (a failure path only, as in the older tests); the tests couple to the helper's
  wait call shapes, which breaks them loudly and cannot make them pass wrongly.
- Release: the owner released; three new records (the package, `ask-claude` and `ask-codex`) are committed with the increment.
- (Increment D-A was committed as `2ca3424`.)

### The re-check after D-A (recommended by the plan, run at the owner's word)

- The `security-reviewer` agent again, on copies of both helpers at `2ca3424` with fake programs (APFS, Python 3.15.0; no real
  program, no network). The tree was untouched (a read-only walk of 2,526 entries found nothing newer than the agent's first scratch file).
  It disclosed that three scripts already in its scratch directory ran once before it had read them, and that it kept no output of
  those; every result below is from scripts it wrote afterwards. Result: no Critical, High or Medium finding; three Low.
- **Tested and sound:** the orphan case under SIGHUP, SIGTERM and SIGINT, each repeated, every ordered pair, and all three, with
  gaps of 0 and 1 ms and with a 250 KB unread prompt: in all of the cases the child was gone, TMPDIR was empty, and the exit codes were
  129, 143 or 130, with no hang; the 84 instrumented runs (a pause at seven points of the normal path, three signals, two fakes, two
  helpers) left nothing running and no scratch directory; a signal in `select` and a second signal inside the handler (exit 130,
  cleanup done, all three then ignored); a caller that ignores one, two or all three signals (not overridden), a blocked SIGHUP (stays
  pending, a later SIGTERM stops it), an ignored SIGCHLD; a failing `mkdtemp` (a clean refusal); SIGINT sent to a whole process group
  (helper 130, program group killed); and the shell behaviour on the new SIGINT exit, which is the same as before in `/bin/sh`,
  `bash` and `zsh`.
- **Width of the reaped-leader window** that increment D-A's review named (the first wait returning to the flag being set): 132 to 225
  microseconds in `ask-claude` and 124 to 196 in `ask-codex` (upper bounds). Reusing that pid as a group would need the pid space
  (99,999 here) to wrap, about 3.5 minutes of forking at the measured 450 forks a second, against a window of at most 0.2 ms; on this
  system it is not reachable. The agent assumed BSD semantics for XNU that a pid serving as a live group's id is not reallocated,
  and did not test that. The plan's Risks sentence that the leader is reaped "only by something other than this helper's own waits"
  is wrong, as D-A's review said: **every successful call sends its `killpg` to a leader that the first wait has already reaped** (to
  the live group, or `ESRCH`). The pid argument above is what covers it.
- **Low 1, `ask-codex` `ask`, the `finally` before and during `shutil.rmtree`** (a window of 100 to 300 microseconds, the median 99): a first
  stop signal that lands there leaves `ask-codex-*` in TMPDIR (mode 0700) holding `reply.txt` (the model's reply) and, with a
  schema, `schema.json`. It predates D-A; the handler has not run before the `finally` starts, so ignoring signals later does not
  protect it. Correction named: mask or ignore the stop signals around the removal. The owner decides whether to close it.
- **Low 2, a signal after the fork and before `process` is assigned** (the known residual): in 4 of 4 runs the program and its
  children kept running after the helper exited 129. Measured width **1.0 to 1.8 ms**, wider than the plan's "fraction of a
  millisecond"; the non-goal's text understates it. No cheap fix without signal masking, which the program inherits through the exec.
- **Low 3, the text of the plan and of increment E:** a child that calls `setpgid` into another group is out of reach exactly as a
  `setsid` child is (tested: it survives a normal end and a SIGHUP kill; the group's own members are killed). Increment E names both.
- Informational: two different signals within one bytecode boundary print `Exception ignored ... Signal N ignored due to race
  condition` and the exit code is that of the lowest-numbered signal; a signal after the result was written still gives exit
  128 plus the number with the complete object on standard output; the `finally`'s unbounded `process.wait()` would hang on a program
  that cannot be killed at all (read only); stdout closed at the start or a reader that has gone gives a crash or exit 120 (both predate
  this plan). Not checked: how the kit runner maps a child's exit status; the pid-reuse claim by forcing a wrap.
- (The re-check's Result entry is committed with increment E.)

### Increment E

- Wrote the contract text, after the code and the re-check: `model-bridge.md` ("Paths": the `.git` and `.workbench` rule by what the
  path is and not its spelling; guarantee 6: a SIGTERM, SIGHUP or SIGINT of the helper kills the program's group whether or not its
  main process is running, exit codes 143, 129 and 130, the others ignored once the first is handled, a caller-ignored signal left
  alone, and what is not covered; checklist item 11; the "As built" bullets for paths and interrupts, with the three measured
  windows); `ask-claude.md` (a section "Stopping the program", and the conclusion of the first run of the release check, which says
  the run was made before the fixes and that the two Low flaws are fixed); `ask-ollama.md` (the `--root` row). The plan's non-goal
  text and the Risks sentence that the re-check showed wrong are not edited (an approved plan's text is not changed after approval):
  this Result and the contract text state what is true.
- Verification: `wb run code-work check` no problems and `git diff --check` clean, after the edits. No test was run: this increment
  changes no code; the code and its tests were verified in A, B, C and D-A (84, 122 and 443 tests, and the re-check). Not checked: how
  the kit runner maps a helper's exit status of 129, 130 or 143.
- Review: one `reviewer` round, no blocking finding; it checked each new sentence against the code and found it true as written,
  and found no other statement of the old rule in `docs/specs`. Applied: the pointer "below" to "above"; the pid-reuse sentence now
  says it is an argument, that it assumes a BSD rule that was not tested here, that the wrap was not forced, and that the case is
  the normal path of every successful call and not only an interrupted one; the removal of the temporary directory is in guarantee
  6's list of what is not covered and the bullet cites guarantees 4 and 6; the window is given as 124 to 225 microseconds; a
  parenthesis says that two different signals in one bytecode boundary give the exit code of the lower-numbered one. Not changed: the
  conclusion of the release check says the canaries "do not depend on" the fixes, which is a reasonable statement and an assertion,
  and is worded as one.
- Completion criteria, as they stand: (1) met by the matrix tests of A, B and C on this Mac's case-insensitive disk (they skip, with
  the reason named, on a case-sensitive one; none was run there). (2) met for a fake whose main process stays alive, by A and B, and
  for one whose main process has exited, by D-A (criterion 7). (3) each regression test failed against the unchanged helper in a
  scratch copy of `HEAD` and passed after (the Result of each increment). (4) the second look (increment D) and a re-check after D-A
  are recorded. (5) met by this increment. (6) the owner released after A, B, C and D-A and the records are committed with each. (7)
  and (8) met by D-A. Not met or not claimed: a case-sensitive disk, a second look after E's text (docs only), and the three
  residual windows (fork, first wait to flag, removal of the temporary directory), which are recorded in the contract text.
- The installed copies of `ask-claude`, `ask-codex` and `ask-ollama` in this project are the versions before this plan until the
  owner runs `wb upgrade`.
