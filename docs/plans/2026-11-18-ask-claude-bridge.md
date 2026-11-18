# A bridge for the Claude Code command line program

Status: Proposed
Created: 2026-11-18
Candidate: none (a further bridge under the accepted decision `2026-10-22-model-calls-go-through-vendor-bridges`; the plan `2026-10-22-ask-codex-bridge` named `ask-claude` as a later module that passes the same checklist)
Specs: model-bridge, module-contract, terms

## Goal

A first-party module `ask-claude` that lets an engine or a library ask a Claude model one read-only question through the same
contract (version 2) as `ask-codex`, so that the two bridges can replace one another. When the plan is done:

- `wb run --provides model-bridge ask-claude ask` answers one prompt with one contract version 2 object, with the options of the
  contract accepted as for `ask-codex`: `--model`, `--effort`, `--timeout`, `--root`, `--schema` and `--confine`; `--server` is
  refused as it is for any bridge to a program.
- The program is `claude` in print mode, started read-only, as the contract asks and as `ask-codex` is: its tools are only the file readers
  (`Read`, `Grep` and `Glob`, the spec fixes the list) with every other tool, MCP server, skill and hook off, no saved session, and
  no user, project or local settings, in an environment built by the bridge, found only on a PATH entry outside the repository.
  The default must read files because the review engine points the model at the documents it reviews.
- `--confine` starts the program with `--tools ""` (no tool at all), and it is shown by canary runs that the confined program
  cannot read a file, run a command or reach the web.
- The bridge never reads or handles a credential: it reports that the program is not signed in.
- No test starts a real `claude`. One real run is made by the owner and recorded.

## Scope

- `docs/specs/ask-claude.md`, indexed in `docs/specs/README.md`, written before the module: the arguments the helper passes, the
  mapping of the program's JSON result to the contract's object, the mapping of its errors, and the conformance checklist.
- `packages/workbench/ask-claude/`: `module.json`, `helper/ask-claude` and tests against a fake `claude` program, and its name in the `modules` list of
  `packages/workbench/package.json`. `tests/run_all.py` finds a module's `tests/` directory by itself and is not edited.
- Small corrections to `model-bridge.md` and the roadmap text where they list the bridges.

## Non-goals

- Signing in, any credential, the API-key mode (`--bare`), a retry, a fallback model (`--fallback-model`) or a budget option.
- A second command or an embedding capability. Claude has no embedding call.
- Changing `ask-codex`, `ask-ollama`, the review engine or the action-review engine.
- A real call to `claude` in any test.
- Installing the module into the owner's project, or releasing its pins. Those are owner steps.

## Assumptions and constraints

- Python standard library and `wbkit` only; tests with `unittest`; the helper name `ask-claude` is unique across modules.
- The installer and its tests must not name `ask-claude` (`tests/test_boundary.py`).
- The capability `model-bridge` has no prefix, so only the first-party package may provide it.
- What the program does, as probed by the agent on 2026-11-18 with the owner's word, `claude` 2.1.327, model `haiku`, one run per
  variant, scripts not kept (to be recorded again in the spec with the content hash of nothing, since no file was fetched):
  - `claude -p --output-format json --no-session-persistence --tools "" --setting-sources "" --disable-slash-commands
    --strict-mcp-config --permission-mode dontAsk`, with the prompt on standard input, printed one JSON object with `result` (the
    text), `is_error`, `subtype`, `terminal_reason`, `usage` (`input_tokens`, `output_tokens`, `cache_read_input_tokens`,
    `cache_creation_input_tokens`), `modelUsage` (keyed by the model's full name, `claude-haiku-5-5`), `permission_denials`,
    `total_cost_usd` and `api_error_status`.
  - A model the program does not know exited 1 with `is_error` true, `api_error_status` 404, `api_error_type` `not_found_error`
    and a sentence in `result`; a diagnostic line was also printed on standard error.
  - `--json-schema '<inline json>'` added `structured_output` (the parsed object) and `result` held its text.
  - `--effort low` was accepted.
  - With `--tools ""`, a prompt to read a file by absolute path produced a reply that tried to call the Read tool and no content of
    the file; `permission_denials` was empty. So the canary did not leak. Whether the program has other ways to read is not shown.
  - On this machine the sign-in is not in `~/.claude/.credentials.json` (the file does not exist), so the bridge cannot name a
    login file for `ask_reads`; it may declare none. The result carried `credential_expires_at`.
- A second round of probes, same day and version, answered most of what was open:
  - `--setting-sources ""` with `--disable-slash-commands` and `--strict-mcp-config` loaded no MCP server, no skill, no slash
    command and none of the owner's synced plugins, as the program's own init event lists them (default: 11 MCP servers, 40 skills,
    6 plugins; isolated: 0, 0 and 4). Four built-in plugins and six built-in agents still load, and are not switchable by these
    flags. A hook in a project `.claude/settings.json` fired by default and did not fire with `--setting-sources ""`.
  - Not signed in: exit 1, `is_error` true, `terminal_reason` `api_error`, `api_error_status` null, `result` "Not logged in ·
    Please run /login". The same text appeared when the environment lacked `USER` and `LOGNAME` while the keychain login existed, so
    the bridge's environment allow list must keep `HOME`, `USER` and `LOGNAME` (the `ask-codex` list does) or every call looks
    signed out. A minimal environment of `PATH`, `HOME`, `USER`, `LOGNAME` and `TERM` signed in.
  - `--effort xhigh` and `max` were accepted by the program; an unknown level only warned on standard error and was ignored. The
    contract fixes `--effort` to `low`, `medium` and `high`, so the bridge accepts only those three and refuses `xhigh`, `max` and
    every other value before it starts the program; the program's wider list is vendor behaviour and not a choice of this bridge. With `--tools ""` a request to run `hostname` returned only an unexecuted tool-call text, and with the
    tools on (control) it returned the host name, so the shell probe passed and proved something. An invalid `--json-schema` is
    refused by the program on standard error with exit non-zero and no JSON on standard output.
  - The model answered about its working directory, so the program tells the model its cwd; the bridge starts it in the validated
    `--root`.
- A web probe (same day and version, one run per variant, scripts not kept) asked the model to fetch `https://httpbin.org/uuid`,
  which returns a fresh random value. With the tools on (control, `--allowedTools WebFetch WebSearch`) the reply held a uuid
  (the program also refused a `curl` through its shell tool: one `permission_denials` entry). With `--tools ""` the reply was an
  unexecuted `WebFetch` call text and no uuid. So the web probe passed and proved something: the no-tools start removes the web
  tool on this version. The probes ran with `--tools ""`, which is the planned `--confine` start and not the planned default start,
  which keeps `Read`, `Grep` and `Glob` (not yet probed: increment A runs the default start with those three, to show that it
  reads a file in the root and still has no shell or web tool).
- Still unmeasured: the shape of a usage-limit error (it cannot be provoked on purpose), which gates increment C's `usage_limit`
  row (see that increment); and whether a `--system-prompt` is needed to stop the program's own instructions from affecting a
  review, which is listed as unconfirmed.
- Each probe sends content to Anthropic. The owner's word is needed for each further run.

## Completion criteria

1. `docs/specs/ask-claude.md` exists, is indexed, and states the mapping the helper implements and every limit the probes showed.
2. `packages/workbench/ask-claude/` passes its own tests, which show each item of the `model-bridge.md` checklist that applies to
   a bridge to a program, against a fake `claude`.
3. `--confine` is accepted, is met by construction or by a measured start, and a test shows the fake receives exactly the
   documented arguments with and without it.
4. The helper imports no network module and reads no credential.
5. The owner has run one real call and the canary probes, and the run is recorded in the spec with its provenance.
6. The module is named in `packages/workbench/package.json`, its `tests/` directory is found by the existing `tests/run_all.py`
   without a change to it, and the installer boundary test still passes.

## Increments

### Increment A — The probe record and the spec

**Outcome:** `docs/specs/ask-claude.md` states the arguments, the result mapping, the error mapping and the checklist, built on
the probes above and on the further probes the owner allows; the unknowns of the assumptions are each measured or listed as
unconfirmed.
**Dependencies:** none.
**Affected areas:** `docs/specs/ask-claude.md`, `docs/specs/README.md`.
**Steps:**
1. Ask the owner for any usage-limit sample from a real limit message they have seen, and which further probes may run (the web
   probe is already recorded above). Run only those, from an empty directory outside the project.
2. Write the spec from `ask-ollama.md` and `model-bridge.md` as models: declaration, options and the flag each becomes, the
   result fields used and ignored (`result` is the reply; `structured_output` is checked, not trusted; `modelUsage` gives the
   model name; `usage` gives the counts, with `total_tokens` `null` and the cache counts as the contract defines them), the
   error table with sample texts, the environment, the confinement, and the checklist.
3. Decide in the spec, and mark for the owner, any choice the contract leaves open: the effect
   of `--effort` on a model without it, the model name when the result gives none.
4. Index the spec.
**Verification:** `wb run code-work check`; the spec's own statements are read against the recorded probe output.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-18-ask-claude-bridge#A`.

### Increment B — The module and its fake program

**Outcome:** `ask-claude ask` works against a fake `claude` for every option except `--confine`: it is found outside the repository,
started with the documented arguments in a built environment, its stdout is parsed as one JSON object, and the reply, model and
usage are copied by the rules of the spec.
**Dependencies:** A.
**Affected areas:** `packages/workbench/ask-claude/` (`module.json`, `helper/ask-claude`, `tests/`), `packages/workbench/package.json`.
**Steps:**
1. Write the fake `claude` in the tests' support file: it records its arguments, environment and standard input, and prints a
   chosen result object.
2. Write the failing tests for checklist items 1 to 5, 7, 8, 12 to 17 (declaration, prompt, options, arguments, environment,
   paths, success object, bounds, schema, hostile text, no writes, one object, `--server`), see them fail for the right reason.
3. Write `helper/ask-claude` from `ask-codex`, replacing the program arguments, the reply source (the result object, not a file)
   and the reading of usage. Pass `--schema` as the inline text read from the validated file.
4. Add `module.json` with `provides` `model-bridge`, command `ask-claude` with the argument `ask`, `runtime` `python`, `kit` 1.
5. Add `ask-claude` to the `modules` array of `packages/workbench/package.json`, in the same scripted pass as the module files,
   because a write under `packages/` is held until the owner releases it.
**Verification:** `python3 -B -W error -m unittest discover -s packages/workbench/ask-claude/tests`; the package declaration
check that the tests of the installer run over `packages/workbench` (the list, the directory name and `module.json` name agree);
and `python3 -B -W error -m unittest tests.test_boundary` because the module must not be named by the installer.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-18-ask-claude-bridge#B`.

### Increment C — Errors and classification

**Outcome:** each class of the contract is produced from a sample of the program's own error, with `retryable` as the contract
sets it, and a timeout, an over-large reply and a program that cannot start are reported as the contract says.
**Dependencies:** B.
**Affected areas:** `helper/ask-claude`, `tests/test_askclaude_engine.py`.
**Steps:**
0. Prerequisite: the spec holds a sample of the program's own usage-limit text, from the owner. If none exists, stop and ask the
   owner whether to build the `usage_limit` row from the program's documented wording and mark that row unconfirmed. Without
   the owner's word to do so, the plan does not claim item 9 of the checklist for the `usage_limit` class, and the Result says so.
1. Add tests for checklist items 6, 9, 10 and 11 with the samples recorded in the spec: an `is_error` result with
   `api_error_status` 404 is `model_unavailable`, a sign-in text is `not_signed_in`, a limit text is `usage_limit`, and an
   unrecognised failure is `bad_exit`. The status and the text are used only to choose a row and are never copied.
2. Implement the classifier on the result object first and on standard error second; an exit 0 with `is_error` true is a failure.
3. Add the cases of an empty `result`, a `structured_output` that is not an object with `--schema`, and a non-JSON stdout
   (`unusable_reply`).
**Verification:** the module's tests; no other root.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-18-ask-claude-bridge#C`.

### Increment D — Confinement

**Outcome:** `--confine` is accepted and the fake receives the documented confinement arguments in the documented order, and
only then.
**Dependencies:** C.
**Affected areas:** `helper/ask-claude`, tests, `docs/specs/ask-claude.md`, `docs/specs/model-bridge.md` (one line listing the
bridge's confinement).
**Steps:**
0. Prerequisite: the web probe is recorded in the assumptions above (it passed on 2.1.327). Repeat it against the installed
   program in the owner's release check. If a later probe shows the confined start reaching the web, add the flag that
   switches the web tools off (`--disallowed-tools` for them) and run the probe again; if no known flag removes a tool that
   reads files, runs commands or reaches a network, `--confine` is refused with a `refused:` line and the spec says why, as the
   contract's rule for a bridge that can switch off none of the three kinds. A tool that stays on is listed in the spec as
   remaining exposure and is not left for the release check alone.
1. Fix the confined start from the spec: `--tools ""` in place of the default's file readers, with the rest of the default
   arguments unchanged, and the spec says what it removes. Where a probe shows a tool still reachable, add the flag that removes it
   (for example `--disallowed-tools`) or refuse as in step 0.
2. Add tests for checklist item 18: the exact arguments with and without it, it works with every other option, and a confined
   failure is reported once and never rerun unconfined.
3. Write the release check for this bridge in the spec, as `model-bridge.md` does for `ask-codex`: the file, the shell and the web
   canaries, run by the owner. The file canary has its control through the bridge without `--confine` (the default reads files) and
   its confined run through the bridge with it. The shell and web canaries cannot succeed through the bridge without `--confine`,
   because the default start has no shell or web tool by design; their controls are direct runs of the program with those tools
   on, and their confined runs are through the bridge with `--confine`. The spec says why the controls differ. A canary passes
   when the confined reply does not hold its token and the control's reply does; a canary without a successful control proves
   nothing and does not count towards release acceptance, so a release is accepted for untrusted text only when all three canaries
   passed with a successful control, and the init-event count of the isolated start is as the spec records.
**Verification:** the module's tests; `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-18-ask-claude-bridge#D`.

### Increment E — The owner's real run and the release

**Outcome:** the owner has run the bridge against the real program once, and the canary check, and the results are recorded in the
spec with provenance. The shipped approvals are released by the owner.
**Dependencies:** D.
**Affected areas:** `docs/specs/ask-claude.md`, `docs/specs/model-bridge.md`, the shipped approvals (owner-run).
**Steps:**
1. Tell the owner which commands to run, with the installed, pinned copy, and what each will send to Anthropic; wait for the
   owner's word.
2. Record each run: what was run, the program version, the commit, and the conclusion.
3. Correct any statement of the spec that the run contradicts, and list what is still unconfirmed.
4. The owner releases the approvals; the agent does not.
**Verification:** the recorded run is read against the spec; `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-18-ask-claude-bridge#E`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. Increment C and D change the helper, so
the module's own tests are rerun after D. No full suite is planned. The one edit outside the module is the new entry in
`packages/workbench/package.json`; the check named in increment B covers it, and a wider run is named only if that check fails
for a reason outside the module.

## Risks and sensitive actions

- **Content leaves the machine.** Every probe and the owner's real run sends a prompt to Anthropic; a probe needs the owner's word.
- **The program's reach.** The first probe shows that `--tools ""` stops a file read, but that is one run on one version. As with
  `ask-codex`, the protection is a tripwire plus tests and not a boundary, and a release is accepted for untrusted text only after
  the release check passes for it.
- **The program is an agent that loads configuration.** The probes show that the isolating flags drop the owner's hooks, MCP
  servers, skills and synced plugins, but four built-in plugins and six built-in agents remain. A test with a fake cannot show
  this; the owner's release check must repeat the init-event count for each release of the program.
- **A call from inside a Claude session** starts a nested session. The bridge must not pass the caller's session variables, and a
  test checks the environment allow list.
- **Cost.** `total_cost_usd` is reported by the program and the bridge does not copy or limit it.
- **Credentials.** The sign-in is the program's own. The bridge reads none and passes no credential variable; if a variable is
  needed for the program to find its login, the spec names it and the owner approves it.
- **Security review.** The bridge touches a subprocess, the filesystem and untrusted text. I will ask the owner whether to run a
  security review with an installed `security-review` module before increment E.

## Review record

Empty until a review is asked for.

## Deferred work

- A roadmap candidate for `ask-claude`, if the owner wants one: that is the `change-direction` checkpoint and is the owner's word.
- A default bridge or an engine setting that chooses this bridge.
- A budget option, once the owner decides how a bridge should bound cost.

## Result

### Increment A (not yet committed)

- Wrote `docs/specs/ask-claude.md`. Ran the default-start probe the plan named (three file tools: reads a file in the root, no
  shell, no web), and three more probes the review's findings called for: a read outside the root (denied by the program under
  `dontAsk`), a `CLAUDE.md` in the working directory (no auto-loading shown, with or without the isolating flags; unconfirmed), and
  the confined start's init event (no tools, no MCP servers). `--safe-mode` was tried and not used (it left 55 slash commands, 19
  skills and 5 agents).
- Verification run: `wb run code-work check` (126 plans, no problems). No test exists for a spec.
- Review: one `reviewer` round, 11 findings, two blocking (no trigger for `effort_unsupported`; no rule that text rows apply only to a
  failure, and no order). Both applied, with the usage-sum null rule, the untagged statements, the `CLAUDE.md` and outside-root
  unconfirmed items, the stderr bound and six-byte clause, `ask_reads` absent, the acceptance and references section. Not
  applied as written: finding 9 (indexing). `docs/specs/README.md` holds no list of specs, so there is nothing to index and the
  plan's step 4 was not done; the plan's criterion 1 ("is indexed") rests on that wrong assumption and is recorded here and not
  changed. Finding 6 (plan says `structured_output` is "checked"): the spec says only `result` is read; the plan text stays.
- (Increment A was committed as `e555d9f`.)
- Owner decisions, 2026-11-18: the input-token sum is confirmed, and the `usage_limit` row may be built from the program's
  documented wording and marked unconfirmed (so increment C's step 0 is met by that word). Not done: the usage-limit sample itself,
  which is on the owner's todo list.

### Increment B

- Built `packages/workbench/ask-claude/` (`module.json`, `helper/ask-claude`, three test files), added it to `packages/workbench/package.json`
  and extended the module lists that three other modules' tests assert (`code-work`, `groundwork`, `claude`), all in one scripted pass
  because a write under `packages/` locks the tools until the owner releases. The plan named `tests/run_all.py` earlier and the first
  review removed that; it is not touched. The helper already carries `--confine`, the timeout and the over-bound paths and a
  generic `bad_exit`, so C and D have less to build than the plan's outcome text says.
- Verification run, on the real tree: the module's 42 tests OK; `code-work` 369 OK (2 skipped); `groundwork` 399 OK (one failure
  before the owner's release of the shipped approvals, gone after it); `claude` 34 OK (12 skipped); `wb run code-work check` no
  problems; `wb verify packages/workbench` lists all 14 modules. Before that, in a scratch copy of `HEAD`: the tests failed with the
  helper absent for that reason, and three deliberate breaks of the helper (tools widened, `USER` and `LOGNAME` dropped, text classified
  on success) each failed tests. Not run: the full suite (`tests/run_all.py`) and a real `claude`.
- `tests.test_boundary` has two failures that are identical on a clean export of `HEAD` and on this tree; they are not caused by this
  increment and are on the owner's todo list.
- The owner released the shipped approvals (preview digest `e377f7d4...`); five new records, for the package and the four changed
  modules, are committed with this increment. They name the helper as it is now, and increment C or D will make them stale and need
  another release.
- Review: one `reviewer` round, no blocking finding. Not applied now, deferred to increment C, which edits the helper and so
  releases again: (1) `emit` returns its exit code from the original document and not from the text it wrote, so an oversized object
  swapped for a `reply_too_large` failure would exit 0 (it cannot happen at the reply bound; also inherited from `ask-codex`); the
  maximal-reply test should use an astral character, which has the largest escape ratio; (2) the environment test's allowed set
  includes `PWD`, `SHLVL` and similar, so a helper that started passing one would not fail; compare against the helper's own
  `environment()` keys. Not changed: a `--timeout` of `0001` is accepted as 1, as in `ask-codex`. (Increment B was committed as
  `ce4edfc`.)

### Increment C

- Added the classifier to `helper/ask-claude`: a failure (exit code not zero, or an object with `is_error` true) is read for its
  words, from `result` when standard output is one object and else from the last 2,000 bytes of standard error, and a status of 429
  or 404 or a type `not_found_error` of the object chooses a row as well as the words. Order: sign-in, limit, model, effort, schema,
  `bad_exit`. A successful object is never classified by its text. Fixed messages for each row. Also the two items deferred from B:
  `emit` returns the exit code of the document it wrote, and the environment test compares with the helper's own `_KEPT`. New
  `tests/test_askclaude_errors.py`: the program found or not (item 6), each class from samples on both sources (items 9 and 10),
  the order, the status rows, text read only for a failure, the timeout with the children gone (item 11), `emit` and an astral
  maximal reply.
- Verification run: the module's 60 tests OK (42 before); `claude` module tests 34 OK (12 skipped), also after the owner's release;
  `wb run code-work check` no problems; `wb verify packages/workbench` lists the module at its new tree. Red run in a scratch copy of
  `HEAD`: 9 of the new tests failed against the old helper. Four deliberate breaks of the new helper (two rows swapped, status
  loosened to any truthy value, the standard error window widened, `emit` keeping the old exit code) each failed a test. Not run:
  the full suite, the other modules' tests (nothing outside this module changed), a real `claude`.
- Owner release: done; two new records (the package and `ask-claude`). The records of increment B for the same two subjects are now
  stale and are left for the owner to remove by hand.
- Review: one `reviewer` round, no blocking finding. Deferred to increment D, which edits the same files and releases again:
  (1) tests for the 2,000-byte window at 1,999 and 2,001, for a failing object with `/login` only on standard error (not read),
  and for a failing object whose `result` is missing or not a string; (2) mark every constructed sample in the error tests, not
  only the two the spec names, and correct the unclear comment above `SAMPLES`; (3) `_NO_MODEL` matches "model" with "not exist" or
  "not access" in the spec's either order and without the 80-character window (the probed case is caught by its 404 status);
  (4) one sentence in the spec's Errors section that the words of a failure may be text the model wrote, so that a caller that
  retries on `retryable` knows a failure whose `result` mentions a limit becomes the retryable `usage_limit`, and that the
  patterns' windows make a row narrower than "holds X with Y"; (5) a comment in the environment test that the explicit list of names
  that must be absent is its guard when `_KEPT` changes. None of these is a behaviour the spec contradicts today.
  (Increment C was committed as `dcfc2d7`.)

### Increment D

- `--confine` was already built by B (`--tools ""` in place of `--tools "Read,Grep,Glob"`, nothing else); D added its remaining tests
  (every other option in three positions with schema and root, a confined failure run once and never rerun unconfined, the default's
  tool list for a failing call) and the five items deferred from C: the model pattern in either order without the 80-character window
  (now 200, `(?s)`), the 2,000-byte window pinned at 1,999 and 2,001, standard error not read beside an object, a failing object
  with no usable `result`, every constructed sample marked, and the environment test's comment. Docs: `model-bridge.md` has an
  `ask-claude` paragraph in "Confinement" and item 18 reads "in place of its tool list" for it (the plan said one line; it is a short
  paragraph); `ask-claude.md` has the paragraph on model-written words, the exact unknown-model sentence of the probe, the
  `cannot access` mislabel and the measured cost of the patterns. The spec's release check already holds the three canaries with
  their controls (written in A), so step 3 of the plan needed no new text.
- Verification run: the module's 67 tests OK (60 before); `claude` module tests 34 OK (12 skipped) also after the owner's release;
  `wb run code-work check` no problems; `wb verify packages/workbench` lists the module at its new tree. Red run in a scratch copy of
  `HEAD`: 3 of the new tests failed against the old helper (those that need the new pattern); the others pin behaviour that B and C
  built. Four deliberate breaks of the helper (the gap widened, the standard error window narrowed, the confinement dropped,
  standard error also read beside an object) each failed a test. The pattern's cost on a worst-case megabyte was timed: about 0.2 s.
  Not run: the full suite, a real `claude`, and the release check of the spec (the owner's, in increment E).
- Review: one `reviewer` round, no blocking finding. Applied in docs: the "by substring" wording, the `cannot access` mislabel, the
  measured cost. Not applied, on the owner's todo list because each needs a package edit and a release: a word boundary before
  `not exist` and `not access` in `_NO_MODEL`, and tests of the gap at exactly 200 and 201 in both orders (the test named for the
  200-character gap does not pin the edge; a widened pattern would pass it). The mislabel only picks a non-retryable class and
  copies no text.
- Release: the owner released; two new records (package and `ask-claude`) are committed with the increment.
