# Bridge contract version 2 for ask-codex: confinement, token detail and a corrected spec

Status: In Progress
Created: 2026-11-01
Candidate: workbench-v1#bridge-confine-and-usage
Specs: model-bridge, review-engine, action-review

## Goal

The `ask-codex` bridge meets contract version 2 as the accepted decision `2026-11-01-bridge-contract-version-2` sets it for a bridge
that starts a program. When the plan is done:

- `docs/specs/model-bridge.md` no longer implies that `--root` scopes what the program reads, and states the version 2 contract for a
  program bridge.
- `ask-codex --confine` starts the program with its tool features, shell tool and web tool disabled, and the spec records what that
  does and does not stop.
- The success object carries the cached and reasoning token counts, and the bridge uses the class `vendor_unreachable`.
- `review-engine` and `action-review` accept contract version 2 (and still 1), so the bridge can move without breaking its callers.
- A release check for untrusted text is written down, and the owner has run it against the installed program and recorded the result.

## Scope

- The spec `model-bridge.md`: the correction of "What the vendor program can read", the version 2 contract as it applies to a program
  bridge, and the release check.
- The `ask-codex` helper and its tests: contract number 2, the seven recognized options, `--confine`, `--server` recognized and
  refused, the class `vendor_unreachable`, and the two new `usage` fields.
- The two engines' reading of the bridge's object, with their tests and specs: contract 1 or 2, the class name tied to the contract
  number, and a `usage` of three or five fields. The counts the review engine stores stay the three it stores today.
- The release of the changed packages' approvals, which the owner makes.

## Non-goals

- Building the Ollama bridge, the guarded-store endpoint record's exact format and the embedding command:
  `workbench-v1#ask-ollama-bridge`. The contract text for a bridge to a server is not deferred: this plan writes guarantee 7 and the
  endpoint constraints of the accepted decision into the spec, and says that no bridge implements them yet.
- A bulk or batch option. Batching fits the existing prompt limit and is the engine's work.
- Making `--confine` an operating-system boundary, or running the program under another user.
- Changing the default: a call without `--confine` starts the program as it does today, and neither engine is changed to pass
  `--confine`.
- Retrying, falling back, or choosing a bridge, a model or an effort.

## Assumptions and constraints

- The decision is accepted, so its numbered items bind this plan. The plan does not reopen them. Where it fixes a detail the decision
  leaves to it, the plan says so, and the detail is in the increment.
- **Fixed disabled list (this plan's choice, for the owner to confirm at approval).** The bridge passes a fixed list of feature names
  and one web setting, for the program versions it was checked against. It does not ask the program for its feature list at run time.
  The reasons: a run-time list is vendor output, which the contract treats as data and not as a control; it adds a call; and it can
  silently change what is disabled. A tripwire in the release check (the tool-list comparison) is what notices a new tool.
- **Batch replies.** The contract already requires a reply with `--schema` to be one JSON object, and the schema file to be an object.
  A batch reply is therefore an object that holds an array. This plan states that in the spec and does not test an array at the top
  level of a schema; whether the program takes one is not needed.
- **The confinement arguments, as the owner measured them on 2026-11-01 with `codex-cli` 0.163.0.** Every name was taken from the
  program's own feature list in that version, where each of the thirteen flags is stable and defaults to true, and the final
  combination was run as one. The scripts were not kept, so the plan quotes them. `--confine` adds these arguments to the ones the
  bridge passes today, in this order, among the options of `exec` and before the `-` that reads the prompt:
  - `--strict-config`;
  - `--disable` followed by each of these twelve feature names, one `--disable` per name: `apps`, `browser_use`,
    `browser_use_external`, `browser_use_full_cdp_access`, `computer_use`, `in_app_browser`, `image_generation`, `multi_agent`,
    `plugins`, `remote_plugin`, `goals`, `hooks`;
  - `--disable shell_tool`, a thirteenth feature flag and not a setting;
  - `--config 'web_search="disabled"'`, a setting and not a feature flag.
- **Failure behaviour the owner measured.** A wrong feature name fails closed: `--disable bogus_feature_zz` stops with "Unknown feature
  flag" and exit code 1, so a renamed or removed flag breaks loudly. A wrong setting name fails open without `--strict-config`: a
  misspelt `web_search` gave a warning in the event stream, exit code 0, and the web tool stayed on; with `--strict-config` it is an
  error with exit code 1. The bridge therefore always passes `--strict-config` with `--confine`, and treats a non-zero exit of a
  confined call as a failure that it never retries without `--confine`.
- **Pinned version.** The list is for `codex-cli` 0.163.0. The spec records that version as the one the list was tested on, and the
  release check runs on every release of the program that the owner installs. The bridge does not read the version at run time.
- The measurements the plan rests on, quoted and not cited by path: with the default options the program read a file in its working
  directory, one above it and one outside the project by absolute path, listed the parent directory and ran a shell command; with the
  final combination above six probes (the same two reads, a read by absolute path outside the project, a shell command, a read through
  the exec function and the web tool) all failed for want of a tool, six of six, with the default-option reads as the controls; the
  confined program still listed an image viewer, a patch tool, MCP resource readers and functions that start agents; the setting
  `tools.view_image=false` did not remove the image viewer, but it was run without `--strict-config`, so whether the name is
  unrecognised or merely ineffective is not known. A tool list is the model's own report. A one-word prompt used 15,836 input
  tokens, 12,288 of them cached. The accepted decision records the residual exposure as accepted by the owner on 2026-11-01.
- The engines run a bridge only through the launcher (`2026-10-22-model-calls-go-through-vendor-bridges`), and a helper is a
  self-contained pinned script, so the three helpers cannot share code. The same small checks are therefore written in each.
- No test starts a real program or touches a network. The release check of increment D is run by the owner, with the installed
  program, because a call to the program sends content to the vendor.
- Editing a file under `packages/` makes the shipped approvals of that package stale. The owner releases the approvals again, and the
  stale records are deleted through the commit helper after the owner approves the listed paths.
- A new `wb` argument or a command needs the specs that describe it. This plan adds an option to an existing command, so
  `docs/specs/model-bridge.md` is the place.

## Completion criteria

1. `docs/specs/model-bridge.md` says in "What the vendor program can read" that `--root` does not confine what the program reads, and
   states contract version 2 for a program bridge, including the seven recognized options, `--confine`, the class
   `vendor_unreachable`, the two new `usage` fields and the relation of cached to input tokens.
2. `ask-codex` prints `"contract": 2` and the class `vendor_unreachable`, recognizes all seven options, refuses `--server` with a
   `refused:` line before anything runs, and a test against a fake program shows each.
3. `ask-codex ask --confine` passes `--strict-config`, the thirteen `--disable` flags and the web setting, in the order the plan
   gives, to the fake program, which records the argument list; a call without `--confine` passes exactly the argument list it passes
   today; a confined call whose program exits non-zero is a failure and is never run again without `--confine`.
4. The success object has `cached_input_tokens` and `reasoning_output_tokens`, each a non-negative whole number or `null`, and
   `total_tokens` is `null` unless the program reports a total.
5. `review-engine` and `action-review` accept a version 2 object from a fake bridge, reject a version 2 object that carries the old
   class name or a version 1 object that carries the new one, still accept version 1, and the review engine's stored round usage is
   unchanged in shape.
6. The spec holds the release check for untrusted text (four file and shell canaries, a web probe and a tool-list comparison), and the
   owner's run of it against the installed program is recorded with the program version and the date.
7. The whole test suite passes, `wb check` and the plan check report no problem, and the owner has released the changed packages'
   approvals again.

## Increments

### Increment A — Correct the spec about what `--root` confines

**Outcome:** `model-bridge.md` stops implying that the working directory scopes what the program reads, and records the measurement.
**Dependencies:** none.
**Affected areas:** `docs/specs/model-bridge.md` only.
**Steps:**
1. In "What the vendor program can read", state that `--root` sets the program's working directory and does not confine what it reads:
   in the owner's probes the program read a file one directory above, a file outside the project by absolute path, and listed the
   parent directory.
2. In the same section, state that the exposure of read-only mode includes running commands, and that `--confine` (written in
   increment C) is the opt-in that reduces it.
3. Add the measurements to "As built, and its limits", with the program version, the date and "one run per variant, scripts not
   kept", and without any path to an untracked file.
4. Correct the line in the option table that describes `--root`, so it says "the directory the program starts in".
**Verification:** `wb run code-work check` reports no problem; `wb check` reports no document problem; the added text names no path
outside the repository.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-bridge-confine-and-usage#A`.

### Increment B — Let the engines accept contract version 2

**Outcome:** `review-engine` and `action-review` accept a version 2 object from a bridge and still accept version 1, so a bridge can
move to version 2 without breaking them.
**Dependencies:** A (the spec text it cites).
**Affected areas:** `packages/workbench/review-engine/helper/review-engine`, `packages/workbench/action-review/helper/action-review`,
their tests and support files, `docs/specs/review-engine.md`, `docs/specs/action-review.md`.
**Steps:**
1. Write the tests first, against the fake bridge each engine's tests already use: a version 2 success with five `usage` fields is
   accepted; a version 2 failure with the class `vendor_unreachable` is accepted; a version 2 failure with `program_not_found` and a
   version 1 failure with `vendor_unreachable` are each rejected as an invalid object; a version 1 object is accepted as before; any
   other contract number, a missing or extra field, and a `usage` of any other field set are rejected.
2. In each helper, accept the contract numbers 1 and 2. Tie the class list and the `usage` field set to the number: version 1 has the
   six old names and three counts; version 2 has `vendor_unreachable` in place of `program_not_found` and five counts.
3. Keep what the review engine stores. A round stores the three counts it stores today, taken from the object, so the sealed state
   format and its checks do not change. The engine ignores the two new counts and relies on neither (the decision, item 8).
4. Update the engine specs where they list the contract number, the class names and the `usage` fields. State that a mismatch between
   the number and the class name is an invalid object.
**Verification:** the two engines' test roots pass, and the whole suite passes; the new tests are seen to fail before the change.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-bridge-confine-and-usage#B`.

### Increment C — Move `ask-codex` to contract version 2 with `--confine`

**Outcome:** `ask-codex` prints contract 2, uses `vendor_unreachable`, recognizes the seven options, reports the two new counts, and
starts the program with its tool features, shell tool and web tool disabled when `--confine` is given. The contract number and the
option that version 2 requires of every bridge arrive in one commit, so no commit advertises version 2 without it.
**Dependencies:** B.
**Affected areas:** `packages/workbench/ask-codex/helper/ask-codex`, the tests under `packages/workbench/ask-codex/tests/`,
`docs/specs/model-bridge.md`.
**Steps:**
1. Write the tests first, against the fake `codex` program in `support_codex.py`: contract 2 on every object; the class
   `vendor_unreachable` for a missing program and for a program that cannot be started, with `retryable` `false`, `detail` `null` and
   a message that says which; `--server` given with any value is refused with a `refused:` line, nothing run and nothing printed; the
   success object holds the five `usage` fields from a fake event stream that carries them, and `null` for any the stream lacks or
   reports in another shape; `total_tokens` is `null` unless the stream reports it; `--server` given twice, with no value or with a
   value outside 1 to 32 characters of `a-z0-9_-` starting with a letter or digit is refused as the grammar says.
2. Change `CONTRACT` to 2, rename the class and its message, and add `--server` to the recognized options with the grammar of the
   decision (item 2). The bridge refuses it with a message that names the option and says this bridge starts a program.
3. Read `cached_input_tokens` and `reasoning_output_tokens` from the event stream through the existing `count` check, and place them
   in the `usage` object with the other three.
4. Update `model-bridge.md`: the contract number, the option table (seven options and their grammar), the error classes, the `usage`
   object, the statement that `cached_input_tokens` is part of `input_tokens` (the decision's example is 12,288 of 15,836), the
   statement that `reasoning_output_tokens` is informational and that no caller adds it to or subtracts it from another count, and
   the rule for `--schema` and a batch (an object that holds the array). Update the checklist items that name the six classes, the
   options and the `usage` fields.
5. Replace guarantee 7 in the spec with the accepted decision's item 7, for both kinds of bridge: a bridge to a program opens no
   connection of its own; a bridge to a server connects only to the endpoint the store names, follows no redirect to another host, has
   a hard timeout, sends only the model request and the endpoint record's credential, and logs and exposes no prompt, reply or
   credential. Add the endpoint constraints (a safe name, `http` or `https` only, no credential in the address, authentication, the
   owner's declared location class, transport that follows the scheme, `https` required for an authenticated endpoint unless the host
   is a literal loopback address, a refusal for a record that breaks these) and the server-bridge checklist items the decision names
   (an invalid, missing or substituted record refused with nothing sent, a redirect not followed, a credential or address absent from
   the object, the message and the arguments, and the timeout ending a server that does not answer). Mark them as the rules for a
   bridge to a server, say that no bridge implements them yet, and say that the exact record format is written in the spec of the
   server bridge.
6. Write the tests for `--confine` first as well, against the same fake program: `--confine` is a flag with no value and is given at most once; a value after it is
   read as the next argument and refused as an unknown option; with `--confine` the fake receives `--strict-config`, the twelve
   feature flags and `--disable shell_tool`, then `--config 'web_search="disabled"'`, in addition to today's arguments and in the
   order the assumptions give, and nothing else differs; without it the argument list is byte for byte today's; `--confine` together
   with every other option (`--model`, `--effort`, `--schema`, `--root`, `--timeout`) works; the environment, the working directory
   and the temporary directory rules are unchanged; a fake that exits 1 with "Unknown feature flag" or with an error about a setting
   is reported as `vendor_error` with `bad_exit`, and the fake is started once and never again without the confinement arguments.
7. Add the flag to option parsing (the parser today requires a value for every option, so the flag needs its own rule) and the
   arguments as constants next to `PROGRAM`, so that the list is written once.
8. Make the confined argument list a single function whose result the test compares, so that a name cannot be added to one place and
   missed in another.
9. Write the spec: the flag and its syntax; the rule every bridge meets (the decision, item 5); the exact arguments and their order,
   with `codex-cli` 0.163.0 as the version they were tested on; why `--strict-config` is always passed (a wrong setting fails open
   without it); that a wrong feature name fails closed; that the protection is a tripwire plus tests and not a boundary; and what
   remains reachable (an image viewer with no known switch, a patch tool whose writes the read-only sandbox refuses, MCP resource
   readers and functions that start agents). Say that a caller that sends captured text always passes `--confine` and that the default
   stays unconfined.
10. Add the checklist items for `--confine` to the spec.
**Verification:** the `ask-codex` test root passes and the whole suite passes; the new tests are seen to fail before the change; the
checklist items that apply to a bridge to a program each have a test (the items for a bridge to a server have none until that bridge
exists); the argument list of a call without `--confine` is compared with the one recorded
before the change.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-bridge-confine-and-usage#C`.

### Increment D — Write the release check and record the owner's run

**Outcome:** the spec holds the check a release must pass before it is accepted for untrusted text, and the owner's run is recorded.
**Dependencies:** C.
**Affected areas:** `docs/specs/model-bridge.md`.
**Steps:**
1. Write the release check as a procedure the owner follows: four canaries (a file in the working directory, one above it, one
   outside the project by absolute path, and a shell command), a probe of the web tool, and a comparison of the program's reported
   tool list with the list recorded for that version. Say that the owner runs it with the installed program, because each call sends
   content to the vendor; that a probe uses a harmless prompt and a canary file the owner makes and deletes; and that a tool list is
   the model's own report, so a difference is a reason to stop and look and a match is not proof.
2. Ask the owner to run the check with `--confine` against the installed program. Record the program version, the date, each probe's
   result, the tool list the program reported, and the conclusion. Record that the image viewer remains, as the accepted decision
   says.
3. Record the list as the expected list for that version. A later release that differs is reported to the owner and is not accepted
   for untrusted text until the owner decides.
4. If any probe reads a file, runs a command or fetches a page in the confined configuration, stop and report; do not widen the plan.
**Verification:** `wb run code-work check` and `wb check` report no problem; the recorded run names a program version and a date; the
text cites no path to an untracked file.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-bridge-confine-and-usage#D`.

### Increment E — Close out and release the approvals

**Outcome:** the plan's result is written, the documents agree, the suite passes, and the owner has released the changed packages'
approvals again.
**Dependencies:** A to D.
**Affected areas:** this plan's result, `docs/specs/model-bridge.md` ("As built, and its limits"), `docs/development.md` if it lists the
bridge's options or exit behaviour.
**Steps:**
1. Update "As built, and its limits" in the spec: the version, the options, what `--confine` does, the checks made and the limits
   that remain. Remove the limit that says the model and the total are not reported, if the run in D showed otherwise.
2. Ask the owner whether to run a security review of the changes to the subprocess arguments and the option parsing, using the
   installed `security-review` skill. The review runs only when the owner asks. Record the answer.
3. Run the whole suite, `wb check`, the plan check and `wb verify` on the changed packages, and read each result.
4. The owner releases the approvals of the changed packages with the owner-run release command. List the stale shipped records and
   delete them through the commit helper only after the owner approves the exact list.
5. Write the result of every increment under `## Result`, with the verification as run.
**Verification:** the full suite reports no failure; `wb check`, `wb run code-work check` and `wb verify` on the changed packages report
no problem; `wb plan-status` reads the plan; the release leaves no stale shipped approval of a changed package.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-bridge-confine-and-usage#E`, and the owner's release recorded in
the result.

## Verification for the plan as a whole

- The whole suite through the repository's test runner, with warnings as errors, and the count of tests recorded.
- `wb check`, `wb run code-work check` and `wb verify` on the three changed packages.
- A fake `codex` that reports the five `usage` fields, run through `ask-codex` and then through both engines, in one test or one
  recorded manual run, showing that a version 2 object passes the whole chain and that the review engine stores three counts.
- The owner's run of the release check, recorded with the program version and the date.

## Risks and sensitive actions

- **Subprocess and argument construction.** `--confine` changes the arguments a program is started with. A wrong name could leave a tool
  on, or fail the program at start. The tests compare the exact argument list, and the release check is what shows that the program
  accepts the names. Increment E asks the owner whether to run a security review.
- **A false sense of safety.** The flag is called `--confine` but is a tripwire plus tests, with an image viewer, a patch tool, MCP
  readers and agent-starting functions still listed. The spec and the decision say so. A caller that treats it as a boundary would
  send captured text where it can be read by a tool no setting turns off; the accepted decision records the owner's acceptance of
  that exposure.
- **A contract break for the two engines.** The rename of a class and the number change break any caller that checks them exactly,
  and both engines do. Increment B makes them accept both versions before the bridge moves, and increment C moves the bridge only
  after B is committed. A project that has an older engine and the newer bridge is refused by the engine until it is current; the
  owner upgrades the engines with the bridge.
- **The engines do not pass `--confine`.** The review engine reads the plans, specs and decisions it reviews through the program's own
  file access, so a confined call would fail; this is why the default stays unconfined (the accepted decision, item 5). The caller
  that always passes `--confine` is a consumer of captured text, such as the knowledge base's library, and not these engines. Whether
  `action-review` should pass it, since it sends only the text of one command, is not decided here and is deferred.
- **Shipped approvals.** Three packages change, so three packages' approvals go stale until the owner releases them again. A scripted
  pass over the packages is made only on the owner's word.
- **Sending content to the vendor.** The release check calls the real program. The owner runs it, with a harmless prompt and a canary
  file the owner makes and deletes. The agent runs no call to the program.
- **The disabled list can fall behind.** A new program version can add a tool. The release check's tool-list comparison is the
  tripwire; a difference blocks acceptance for untrusted text until the owner decides.
- **Hard stops:** none identified.

## Review record

Reviewed by Codex (`gpt-5.6-terra`) through the review engine on 2026-11-01, at the owner's request; three rounds out of a bound of
3, raised to 4 by the owner after round 3 and to 5 after round 4. Outcome: converged. The fifth round, which read the plan with the
round-4 fix, returned no meaningful finding.

- R1-F1 (major, applied): the plan was wider than its candidate. The owner agreed, and the candidate's boundary now names the two
  engines that read the bridge's object, with their tests and specs.
- R1-F2 (major, applied): the confinement names were left to be supplied after approval. The plan now holds the exact names, the
  order, the strict-config flag and the tested program version, from the owner's measurements.
- R2-F1 (major, rejected): the engines should pass `--confine`. The rule that a caller of captured text always passes it concerns the
  knowledge base's library; the review engine needs the program's file access to read the plans it reviews. The plan says the engines
  do not pass it and defers the `action-review` question.
- R2-F2 (minor, applied): a stale risk about the candidate's boundary was replaced.
- R3-F1 (major, applied): the move to contract version 2 and `--confine` were separate commits, so one commit would have advertised
  version 2 without an option it requires. They are one increment, and the later increments were renumbered.

- R4-F1 (major, applied): the plan left guarantee 7 and the endpoint constraints out of the version 2 spec. Increment C now writes
  them, as rules for a bridge to a server that no bridge implements yet.

Left for the owner: whether `action-review` should pass `--confine`. The review is not an approval.

## Deferred work

- Building the Ollama bridge, the exact format of the endpoint record and the embedding command: `workbench-v1#ask-ollama-bridge`.
- A run-time derivation of the disable list, if the fixed list proves too hard to keep current.
- Whether `action-review` should pass `--confine`, which needs a look at what its prompt carries and a decision of the owner.
- A run-time check of the program's version against the tested one, which would add a call to every confined run.
- Trying `tools.view_image=false` with `--strict-config` to learn whether the name is unrecognised or ineffective.
- Whether the owner wants the tool-list comparison automated in a maintainer script. It needs the real program and a network, so it
  cannot be part of the suite; it is deferred until the owner asks.
- A switch that turns off the image viewer, if the program gains one.

## Result

### Increment A

**Done:** `docs/specs/model-bridge.md` changed in three places and nowhere else. The `--root` row of the option table now says the
directory the program starts in and that it does not limit what the program reads. "What the vendor program can read" says that
`--root` does not confine reads, summarizes the probes (a file in the working directory, one above it and one outside the project by
absolute path read; the parent directory listed; a shell command run; only file creation refused), says the exposure includes running
commands, and names `--confine` as planned and opt-in. The first bullet of that section now covers any file the program can open,
inside or outside the project. "As built, and its limits" has a new bullet with the measurements: the seven bridge calls, whose
program version was not recorded, and the direct `codex-cli` 0.163.0 runs, with the date, "one run per variant, scripts not kept", and
no path to an untracked file.

**Verification as run:** `wb run code-work check` reported "checked 76 plans, check found no problems" and `wb check` reported "check
found no problems", both after the last edit. The added text names no path outside the repository.

**Not done:** nothing in the increment. No package was touched, so no shipped approval is stale.

**Review:** one round by the read-only `reviewer` agent (one exchange). Findings:
- Blocking, rejected: several specifics (seven calls, a new empty directory, about 31,000 tokens for tool calls, the refused file
  creation, the failed host lookup) were not in the plan or the decision. They are in the owner's knowledge-base record, which I read;
  the reviewer could not. The bullet now says the figures come from the owner's report and keeps the two sets of runs apart.
- Not blocking, applied: it was unclear which figure belonged to which run (the bullet now separates the bridge calls from the
  direct runs); the first bullet of the section was scoped to the project (now inside or outside); the `--confine` sentence now names
  the shell and web tools as well as the tool features.
- Not blocking, applied: the checks were re-run after the corrections.
The reviewer's recommendation read "blocking findings", driven by the first item. After my evaluation no finding is left open.
