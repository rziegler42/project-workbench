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
- Owner decisions, 2026-11-18: the input-token sum is confirmed, and the `usage_limit` row may be built from the program's
  documented wording and marked unconfirmed (so increment C's step 0 is met by that word). Not done: the usage-limit sample itself,
  which is on the owner's todo list.
