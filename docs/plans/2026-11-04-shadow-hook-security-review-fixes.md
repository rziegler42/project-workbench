# Fix what the second security review of the action-review shadow hook found

Status: Proposed
Created: 2026-11-04
Candidate: workbench-v1#action-review-engine
Specs: action-review

## Goal

The owner asked for a security review of the shadow hook, its store, its tools, the engine's `--collect` flag and the installation steps
before installing it (2026-11-04, a read-and-probe pass on a scratch copy of commit 488efc1; the hook was not registered and no data
directory existed). It found no Critical or High issue and five Medium ones. After this plan:

1. a commit the engine declines because it holds a secret, or a credential-named path, leaves no diff, command text or facts in
   `collected.jsonl` (Medium 1);
2. the hook does not take its home directory, its data directory or its launcher from the inherited environment, and the settings
   entry that starts it keeps the interpreter's own start-up from reading it: the entry is
   `/usr/bin/env -i <absolute interpreter> -I -B <dir>/shadow_hook.py --wb <absolute launcher>`, because a Python script cannot defend
   itself against what the interpreter runs before the script (`sitecustomize`, `usercustomize`, `PYTHONSTARTUP`); the hook takes the
   home directory from the account database, needs `--wb`, and notes and does nothing when it was not started isolated (Medium 2);
3. the engine's call to the model bridge is confined, if the bridge's contract allows it, so that a model steered by hostile commit text
   has no local shell, tools or web search (Medium 5);
4. the specification and the owner's steps say what they left out: the copied files need a dedicated, read-only directory and a deny of
   edits to it; the report is advisory and the owner re-labels a sample at a terminal before any cutover; the exposure to the vendor
   model; the time budget; the `PATH` the hook gives the engine (Mediums 3 and 4, and the Lows that are text).

Shipped defaults, the registry and the permission levels do not change.

## Scope

In:

- `packages/workbench/action-review/hook/shadow_hook.py` and `shadow_store.py`, and the helper `helper/action-review` where it calls
  the bridge, with their tests under `packages/workbench/action-review/tests/` and the pins that name the files (`PINS`, and the
  module's own tests of them);
- `docs/specs/action-review.md` ("The shadow hook", "The data files", "Redaction", "The owner's steps", "As built, and its limits") and
  `docs/development.md` where it describes the hook.

## Non-goals

- Registering the hook, copying its files, labelling, running the test set: the owner's steps, which the agent never runs.
- Making the report authoritative against an agent that runs as the owner: nothing here separates them (Medium 4); the plan says so.
- A hook that decides, the cutover, and plan 5 of the action-review split.
- The redaction patterns beyond what Medium 1 needs (Low 3), the pinning of `run_testset.py`'s checkout and its `-I` start (Low 4), and
  the silent stop of recording on a full file (Low 5): listed under Deferred work with the reason.
- Re-reviewing `safe-git describe` and its git-configuration isolation: the security pass of its own module.

## Assumptions and constraints

- The plan `2026-10-29-action-review-shadow-hook` stays as it is (`In Progress`, approved; its criterion 9 is the owner's). This plan
  starts only after the owner approves it, and builds on the committed shadow.
- The review's evidence has limits the plan does not hide: no real `wb`, bridge, Codex or Claude Code was used; whether Claude Code
  applies a project's `settings.json` `env` to hook processes, honours exit 2 on `PermissionRequest` or holds the prompt while the hook
  runs is unverified; the confinement flag was not tried against a real Codex.
- A change under `packages/workbench/action-review/` changes the module's tree hash and the helper's pins. Each increment updates the
  pins and their tests in the same commit, and the approvals of the shipped packages go stale until the owner runs
  `wb release-approvals` (at `ask` the agent runs it with the digest the preview printed, and the owner confirms) and `wb upgrade`. The
  Results of `2026-10-29-action-review-shadow-hook` record how each earlier increment dealt with this; the author reads them before
  increment A and states the sequence under that increment's Result.
- **After this plan, the four files the owner copied to `~/action-review-shadow` (hook, store, `label.py`, `report.py`) are out of date
  and are copied again and re-checked**; the owner's steps say so, and the hook is not registered before that (it is not registered
  today).
- Everything the hook reads (command text, commit messages, diffs, file names, project files, `.workbench/review.json`) is attacker
  input, as the earlier review treated it.
- **A spec is never left false between increments.** An increment that changes what the hook, the store or the engine does updates, in the
  same commit, every line of `docs/specs/action-review.md` and `docs/development.md` that its change makes false (the rule that a row is
  collected for every reviewed command, the default launcher path, the `python3 -B` invocation and the `--wb` default, the bridge call);
  increment D then consolidates and completes the owner's procedure and adds what the review found that no code changes.
- Each fix has a regression test that fails before the fix and passes after it. Testing is targeted; before any wider run the author
  states what could break outside the tested area. No test contacts the network or the owner's store: the tests use a fake `wb`, a fake
  bridge and a scratch `HOME`.

## Completion criteria

1. A row of `collected.jsonl` is never written for a verdict whose failed checks include `no_secret_lines` or `paths_not_credentials`, and
   the verdict row of such a command holds only a redacted reason; a test with the shapes the review found (`glpat-`, a bare `npm_`
   token, `sk_live_`, `pass=`, `pwd=`, a Slack webhook, an unnamed AWS secret, a `Basic` header without its name) leaves none of them in
   either file.
2. Started as the settings entry says (`env -i`, an absolute interpreter, `-I -B`), the hook runs none of a hostile `json.py`,
   `sitecustomize.py` or `usercustomize.py` on a `PYTHONPATH`, and uses no `HOME` or `PYTHONSTARTUP`: tests set all of them and show it.
   Started without `-I`, the hook notes a fixed line on standard error, records nothing and exits 0 as soon as its own code runs; the spec
   says that this guard makes a missing `-I` visible and stops the hook's work, and that it cannot stop code the interpreter ran before
   the script, which only the entry's `env -i` and `-I` prevent. The data directory and the default home come from the account
   database, and without `--wb` the hook does nothing.
3. The engine's bridge call is confined, or the spec records the reason it is not and the exposure, as the bridge's contract decides
   (`docs/specs/model-bridge.md`, "Confinement"); a test with a fake bridge shows the arguments it received.
4. The spec's "The owner's steps" gives one complete list: a dedicated, empty, read-only directory; the settings entry
   `/usr/bin/env -i <absolute interpreter> -I -B <dir>/shadow_hook.py --wb <absolute launcher>` (the same entry in the Goal, in
   increments B and D, and nowhere the PATH-selected form `python3 -I -B ...`); user-level denies of edits to the directory and the settings file and of
   reads of the data directory, with the limit that a shell bypasses them; a comparison against the committed blob in a checkout, not
   against the pins in the project tree; the report is advisory and a sample is re-labelled at a terminal before any cutover; what a
   steered model can do; the time budget with the store's lock waits; the hook's fixed `PATH` and what to do if `codex` or the
   launcher's interpreter is not on it. The document check passes.
5. The tests of the module's hook, store, helper and pins pass, and the drift between the hook files and their pins is zero.

## Increments

### Increment A — A declined secret leaves no text in the collected data

**Outcome:** the hook stores no command text, diff or facts for a command the engine declined because of a secret or a credential-named
path, and the reason it stores is redacted.
**Dependencies:** none.
**Affected areas:** `hook/shadow_hook.py` (`record`, `redacted_text`), `tests/test_hook_shadow_hook.py`, `tests/test_hook_redact.py`, the
pins of the hook file (`helper/action-review`, `tests/test_actionreview_pins.py`), `docs/specs/action-review.md` ("Redaction").
**Steps:**
1. Read the engine's check names (`no_secret_lines`, `paths_not_credentials`) and how the hook reads `failed_checks` from the verdict.
2. Write the tests first, each with the shapes the review reported, through the hook with a fake `wb` that returns a decline with
   `no_secret_lines` in its failed checks and the facts holding the secret: no `collected.jsonl` row exists, and the secret is in
   neither file. A separate test does the same for a decline whose failed checks hold `paths_not_credentials`, with the command text and
   the facts present (a misspelt or missing second name must fail it). Also a decline with another failed check still collects, so the
   evidence for the labels is not lost.
3. Change `record` so that a failed check of those two names turns `collecting` off. The verdict row stays, with its redacted reason.
4. Update the pin of `shadow_hook.py` and its test in the same commit, and every line of the spec that says a collected row is written
   for each reviewed command ("The shadow hook", "The data files", "Redaction", "As built, and its limits"): say what is and is not
   collected.
**Verification:** the module's hook, redaction and pin tests (`test_hook_shadow_hook`, `test_hook_redact`, `test_hook_store`,
`test_actionreview_pins`, `test_actionreview_module`).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-shadow-hook-security-review-fixes#A`.

### Increment B — The hook trusts nothing from its environment

**Outcome:** the hook finds its home in the account database, does nothing without `--wb`, and stops at once when it was not started
isolated; the documented entry starts it with a clean environment, so the interpreter's own start-up reads none.
**Dependencies:** A (the same file, so the pins change once per commit).
**Affected areas:** `hook/shadow_hook.py` (the start of the file, `run`, `parse_arguments`), `hook/shadow_store.py` (`data_dir`),
`tests/test_hook_shadow_hook.py`, `tests/test_hook_store.py`, the pins of both files and their tests, `docs/specs/action-review.md`
("The shadow hook", "The owner's steps" entry only).
**Steps:**
1. Write the tests first, as subprocesses with a scratch `HOME` and a fake `wb`:
   - a `PYTHONPATH` that holds a `json.py`, a `sitecustomize.py` and a `usercustomize.py`, each recording that it ran, and a
     `PYTHONSTARTUP`; started as the documented entry says (`/usr/bin/env -i`, an absolute interpreter, `-I -B`) none of them runs and the
     hook records a row; started with `-I` only, the `json.py` does not run either;
   - started without `-I`, the hook notes the fixed line, writes nothing and exits 0 (the guard sits at the top of the file and acts only
     when the file is run as a program; the test does not claim that no hostile code ran before it);
   - a different `HOME` does not move the data directory or the launcher; no `--wb` gives the usage note and no engine call.
2. Add the guard (`sys.flags.isolated`), take the home from `pwd.getpwuid(os.getuid()).pw_dir` where the code uses `expanduser("~")` (the hook and the store;
   the `home` argument that tests pass stays), and drop the default launcher path.
3. Update the pins and, in the same commit, every line of the spec and of `docs/development.md` that names the default launcher path, the
   `--wb` default or the `python3 -B` entry ("The shadow hook", "The owner's steps", the hook's row of the command table).
**Verification:** the tests named in A, and a run of the hook as a program with and without `-I` against a scratch `HOME` and a fake `wb`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-shadow-hook-security-review-fixes#B`.

### Increment C — The bridge call is confined

**Outcome:** the engine's call to the model bridge passes `--confine` where the bridge's contract allows, or the spec says why it does
not.
**Dependencies:** none beyond A and B being committed (the pins).
**Affected areas:** `helper/action-review` (`ask_bridge`), `tests/test_actionreview_bridge.py`, the pins, `docs/specs/action-review.md` and,
if it must, a sentence of `docs/specs/model-bridge.md`; no change to `ask-codex` itself.
**Steps:**
1. Read `docs/specs/model-bridge.md` ("Confinement"): it says a caller that sends captured text through a bridge to a program always
   passes `--confine`, and records confined `ask-codex` probes of 2026-11-01 (the engine's facts are captured text). Decide whether a
   reply under `--schema` still works confined. If the contract says it may not, stop: record the reason and the exposure in the spec
   (criterion 3) and leave the code as it is; the owner decides whether a later plan changes the bridge.
2. Write the test first: with a fake bridge that records its arguments, the engine's call carries `--confine`, and a bridge that refuses
   the flag makes the review `failed`, never an unconfined retry.
3. Pass `--confine`; update the pins and, in the same commit, the lines of the spec that describe the bridge call ("The shadow hook",
   "As built, and its limits").
4. Say in the spec what is and is not shown: the bridge's own confinement evidence stands (`model-bridge.md`, "Confinement", the probes
   of 2026-11-01, which this plan does not repeat); the action-review engine's confined call with its reply schema has not been run
   against a real Codex, so the owner's test-set run (step 8) is its first use and a `failed` case there names the cause.
**Verification:** `test_actionreview_bridge`, `test_actionreview_module`, `test_actionreview_pins`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-shadow-hook-security-review-fixes#C`.

### Increment D — The owner's steps are complete

**Outcome:** the spec's "The owner's steps" is the one list the owner follows, with nothing the review found left out, and no step that
is later withdrawn.
**Dependencies:** A, B and C (what the steps say must be true).
**Affected areas:** `docs/specs/action-review.md` ("The shadow hook", "The data files", "The owner's steps", "As built, and its limits",
"Open questions"), `docs/development.md`.
**Steps:**
1. Rewrite the steps in order and in full (criterion 4), each with its command or entry verbatim: the dedicated directory
   (`mkdir`, copy, `chmod`), the check of the copies against the committed blobs of a checkout at the approved commit (the comparison
   with the project's `PINS` is a second check and says what it does not prove), the settings entry
   `/usr/bin/env -i <absolute interpreter> -I -B <dir>/shadow_hook.py --wb <absolute launcher>` (with how to find the interpreter and why
   `env -i` is there), the Edit and Write
   denies, the Read deny, the `ask` for commits, the hand run, labelling, the test set, the report. A step that must wait for another is
   written after it.
2. Add "what a steered model can do", "the report is advisory", "the time budget" (the engine's 25 seconds, the hook's 27 and the store's
   lock waits, against the harness's 30), "the hook's `PATH`" and the Lows that are text.
3. Name the files the owner copies again after this plan, and why.
4. Run `wb check`.
**Verification:** the document check, and a reading of the steps against the built hook by the reviewer.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-04-shadow-hook-security-review-fixes#D`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later one changed its inputs. At the end run the module's tests
(`packages/workbench/action-review/tests/`), `wb check`, `wb run code-work check` and `wb doctor`; the module's pins and its release
approvals must agree, and the author says what the owner still runs (`wb release-approvals`, `wb upgrade`, the copies). The full suite
runs only if the owner decides after the author states what could break outside the tested area. A security re-review of the fixes
(a fix is new attack surface) runs only when the owner asks.

## Risks and sensitive actions

- **The hook runs at every prompt as the owner and may send diffs to a vendor.** Nothing here registers it; the plan only makes the
  built hook safer and the steps complete. The owner registers it.
- **A fix can hide a secret from the labels.** Increment A drops the rows of declined secrets; a test shows other declines still collect.
- **A clean environment and isolated mode can stop the hook working where the owner's setup relies on the environment** (the `PATH` that
  finds `codex`, a `HOME`-relative Codex directory). The hook builds its own `PATH` and takes the home from the account database; if the
  engine then reports `failed`, the owner's steps name the causes to look at.
- **The `-I` guard is not a defence by itself.** The script runs after the interpreter's start-up, so only the entry's `env -i` and `-I`
  keep a hostile `PYTHONPATH` out; the spec says so and the owner writes the entry.
- **A change to the module's files makes its approvals stale.** The owner runs the release and upgrade steps.
- **The copies the owner made are out of date after this plan.** Said in the plan and in the steps.

## Review record

- **Reviewer:** the project's review engine, model `gpt-5.6-terra`, through `wb run review-engine review-plan`.
- **Rounds:** 3 of the bound of 3. Not converged: every round found major points, and the last round's fixes were reviewed in no further
  round.
- **Applied (5):** every spec line a change makes false is updated in the same increment, and increment D only consolidates (R1-F1);
  a separate test for `paths_not_credentials` (R1-F2); a Python guard cannot stop code the interpreter ran before the script, so the
  entry is `/usr/bin/env -i <absolute interpreter> -I -B ...`, the guard only notes a missing `-I`, and `sitecustomize` and
  `usercustomize` are tested (R2-F1, the most consequential finding); criterion 4 names the same entry as the goal and increments B and
  D (R3-F1); increment C cites the bridge spec's confinement rule and its recorded probes, and says only that the engine's confined call
  with its schema has not run against a real Codex (R3-F2).
- **Rejected:** none.
- **Left for the owner:** the verdict, a further round (the engine's bound is reached; `extend` is the owner's), or approval as it stands.
  Not checked by any reviewer: the plan's reading of the helper's secret checks (`no_secret_lines`, `paths_not_credentials`) beyond their
  names, and whether `--confine` works with the engine's reply schema.

## Deferred work

- Low 3 (redaction quirks: a value that begins `[redacted:`, an unterminated quote) and the broader redaction patterns: Increment A removes
  the rows that matter most, and a longer list of patterns is best effort that the spec already says it is.
- Low 4 (`run_testset.py` hashes only its case file and is started without `-I`): it runs only from a checkout the owner trusts, once,
  with 3 synthetic prompts; the owner's steps say so.
- Low 5 (recording stops silently on a full file): the stop is conservative and noted on standard error.
- The unverified behaviour of Claude Code (project `env` for hooks, exit 2 on `PermissionRequest`, whether a prompt waits): the owner's
  hand run (step 6 of the steps) answers it.

## Result

### Increment A — A declined secret leaves no text in the collected data (built in a scratch clone, 2026-11-04)

- **Where the work is.** Editing a file under `packages/workbench/` in the real tree changes the module's hash and the command gate then
  refuses every Bash command until the owner releases the approvals (the Result of increment B of `2026-10-29-action-review-shadow-hook`).
  So the increment was built and tested in a scratch clone at `2bf78db` (session scratchpad, `wb-sa/`); the real tree holds nothing of it
  yet. Four files differ: `hook/shadow_hook.py`, `helper/action-review` (the hook's pin, now `12b8bc5ac3a1…`),
  `tests/test_hook_shadow_hook.py`, and `docs/specs/action-review.md`.
- **Done.** `record` writes no collected row for a decline whose failed checks include `no_secret_lines` or `paths_not_credentials`
  (`NO_COLLECT_CHECKS`); the verdict row stays, with its failed checks and its redacted reason; a decline for another reason still
  collects. The spec says so ("Redaction", the `collected.jsonl` bullet, the report's "reviewed but not collectable") and says what follows:
  **a decline for a secret can never be labelled**, so a false decline of that kind never reaches the labelled set.
- **Criterion 1 is met only for the shapes the engine's scan declines.** The test, through the real engine, found the engine declines
  `glpat-`, a bare `npm_` token, `sk_live_`, `pwd=` and a `Basic` header (and the test pins that list), and does not decline an unnamed 40-character
  AWS secret, `pass=` or a Slack webhook. For those three the engine approves, the redactor does not name them, and a commit that holds only one of
  them is still collected as it stands. The plan's wording lists `pass=` and a Slack webhook among the shapes that leave nothing; that is not
  true and is recorded here and in the spec. Closing it needs a pattern in the redactor or the engine's scan; it is the owner's to
  decide whether a later plan does (Deferred work already names the redaction patterns; this adds these three shapes).
- **Verification as run in the clone** (HOME and the store set to scratch directories, `PYTHONPATH` to the clone): the new tests failed before
  the change (9 tests) for the right reason, the collected row existing; after it `test_hook_shadow_hook`, `test_hook_redact`,
  `test_hook_store`, `test_actionreview_pins`, `test_actionreview_module` and `test_tools_report` pass (226 tests) except
  `Launcher.test_the_environment_holds_exactly_path_home_and_lang`, which fails the same way on the unchanged real tree (macOS adds
  `__CF_USER_TEXT_ENCODING` to the fake `wb`'s environment, as the security review noted). Removing `paths_not_credentials` from the tuple
  made exactly the credential-path test fail. The whole module set (755 tests) in the clone had four failures: that one, a thread test that
  passes alone, and two tests that read the real project's untracked `.workbench/review.json`, which a clone does not have.
- **Review:** one `reviewer` exchange, no blocking finding; applied: the test now pins exactly which shapes the engine declines (so a
  vacuous pass at a floor of four is gone), a stale "below" in the spec, and the spec's lines on "reviewed but not collectable" and on
  the unlabelled secret declines. Not applied: the status header of the spec, which does not list this plan (minor).
- **Not done yet:** copy the four files into the real tree, the owner's `wb release-approvals` (the preview is `wb preview
  release-approvals`; the real run is the owner's at a terminal, because the gate is closed by then), the checks in the real tree, and the
  commit with the two new shipped approval records.
