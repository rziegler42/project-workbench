# Temperature and keep_alive for the Ollama bridge, and retryable server errors

Status: Proposed
Created: 2026-11-02
Candidate: none (a follow-up to the completed plan `2026-11-02-bridge-model-configurations`, whose "Deferred work" holds these three items; the owner may add a roadmap candidate)
Specs: ask-ollama, model-bridge

## Goal

The bridge to an Ollama server can set what a model thinks about (the effort), how much it may write (the output limit) and how large
a window it gets, but not how random its sampling is, how long the server keeps the model loaded, or whether a caller should retry
after a transient server error. The knowledge-base module needs all three: its card extraction runs at a temperature of 0.2 and
retries at 0.5, a server with one 12 GB card failed an embedding call right after a chat call with a 500, and every 5xx is today a
failure that a caller must not retry. When the plan is done:

- A chat section of the endpoint file may hold a default `temperature`, and a call may replace it with `--temperature`, so a caller
  can run at 0.2 and retry at 0.5 without a second section.
- A section of either kind may hold a default `keep_alive` (how long the server keeps the model loaded after a call), and a call may
  replace it with `--keep-alive`, so an owner can say that a chat model is unloaded at once and leave room for an embedding model.
- A status 500, 502 or 503 from the server is reported as a failure that a caller may retry (`retryable` true), for `ask`, `embed` and
  `models` alike. A status 501 stays what it is (the row for a chat model sent for an embedding), and every other status stays not
  retryable. The bridge never retries by itself.
- The rule is stated for a bridge to a server, so `ask-codex` (a bridge to a program, with no HTTP status) is unchanged in code and in
  behaviour, and the two engines that read the object are shown to behave as before.
- The temperature and the keep_alive are shown against the owner's real server, with the owner's word, and recorded without its
  address; the retryable rule is proved by the fake-server tests, and the run records a 5xx only if the server gives one.

## Scope

- Two decision records, each written as `Proposed` for the owner's acceptance: the request controls (the section fields, the call
  options, the grammar of a temperature and of a keep_alive, how each is sent) in increment A; and the retryable server errors (the
  statuses, the commands, whether the contract version changes, what `ask-codex` and the engines see) in increment B.
- The spec changes in `ask-ollama.md` and `model-bridge.md` (increment C).
- The helper `ask-ollama` and its tests: temperature and keep_alive (increment D), then the retryable statuses (increment E).
- The owner's run against a real server, recorded in the spec (increment F).
- The close-out and the record of the upgrade (increments G and H).

## Non-goals

- A retry loop in the bridge or in the helper. The bridge makes one request; a caller decides whether to retry.
- Statuses 429 and 504, and any 4xx: they stay `bad_exit`, not retryable (the owner named 500, 502 and 503). They are deferred.
- A default for any other request field (`top_p`, `top_k`, `seed`, the stop words, the system prompt), and a temperature or a
  `keep_alive` default for `models`.
- A token count, a credential, a field naming the bridge of a record, and the test certificates (the other deferred items of the
  earlier plan).
- Any change to `ask-codex`, to the contract's common core or to its version unless increment B decides otherwise with the owner.

## Assumptions and constraints

- The owner's word is needed for each real call to the server (increment F), as for every call to a real server. The agent cannot
  write the guarded store; the owner edits the file, and the plan gives the exact text.
- Each package change (increments D, E and H's upgrade, and F if it corrects the helper) is one scripted pass and needs the owner's
  explicit word "run the pass", then one `wb release-approvals` by the owner. The new tests are written first and are seen to fail
  against the old helper.
- Tests are targeted, as the owner asked on 2026-11-02: the module's tests and `wb verify` for a change to the helper, the tests of
  `review-engine` and `action-review` only if increment B finds that the change could alter what they read, and `wb check` and
  `wb run code-work check` for a document. The whole suite is not run unless an increment's own risk calls for it, and the Result
  says which tests ran and why.
- **The endpoint file refuses a fraction.** Its reader, `wbkit.jsonstrict`, refuses a number with a fraction or an exponent as "not
  strict JSON" (read on 2026-11-02), so a temperature of 0.2 cannot be a JSON number in the file without a change to the kit. The
  decision of increment A chooses how the file holds it; the recommendation is a JSON string of a small grammar (`"0.2"`), sent to the
  server as a number, because it needs no kit change. An integer in hundredths is the alternative; a change to the kit's reader is not
  recommended for one field.
- Recommended shape of a temperature (the decision decides): a value from 0 to 2 with at most two decimals, written as a string in a
  chat section (`"temperature": "0.2"`) and as the value of `--temperature` (`0.2`); a call's value replaces the section's. It is
  sent as `options.temperature` (a number). An embedding section holds none; `embed` and `models` refuse the option. The exact
  grammar is `[0-2]` or `[0-2].[0-9]` or `[0-2].[0-9][0-9]`, and a value above 2 (`2.01`) is refused. Accepted: `0`, `0.2`, `0.50`,
  `1`, `2`, `2.00`. Refused: a sign (`-0.2`, `+1`), an extra leading zero (`00.2`, `01`), no digit before or after the point (`.5`,
  `1.`), more than two decimals, an exponent, a space, an empty value and a non-string in the file.
- Recommended shape of a keep_alive (the decision decides): a duration string that the server reads, from the grammar `0` (unload at
  once), `-1` (keep loaded) or one to four digits followed by `s`, `m` or `h`; a string in a section of either kind
  (`"keep_alive": "0"`) and the value of `--keep-alive`; a call's value replaces the section's; sent as the request's top-level
  `keep_alive` for `ask` and for `embed`, and left out when neither is given (the server's own default stands). `models` has none.
  The wire form is chosen so that it does not depend on how the server parses a string: `0` and `-1` are sent as JSON numbers
  (`0`, `-1`) and a duration as a string (`"30m"`). A report from memory says that a server may refuse a string `"-1"`; that is not
  known and is not tested here, because the helper never sends it. Increment F sends only the forms the helper produces (`0` and
  `-1` as numbers, a duration as a string) and records the answer to each; if the server refuses `-1` as a number, the plan stops and
  the decision of increment A is revisited with the owner.
  The exact grammar is `0`, `-1`, or `[1-9][0-9]{0,3}` followed by `s`, `m` or `h`. Accepted: `0`, `-1`, `1s`, `30m`, `9999h`.
  Refused: any other sign or negative number (`-2`, `+5m`), a leading zero in a duration (`01s`, `00m`), a duration with no unit
  (`30`) or an unknown unit (`5d`), more than four digits, a fraction (`1.5h`), a space, an empty value and a non-string in the file.
- Recommended retry rule (the decision of increment B decides): a response whose status is 500, 502 or 503 is `vendor_error` with
  `bad_exit` (the class, detail and message stay) with `retryable` true. It applies to every request of the bridge to a server: the
  chat request of `ask`, the embedding request of `embed` and the list of `models`. A 501 keeps its row for `embed` (a chat model sent
  for an embedding is `model_unavailable`, not retryable) and is `bad_exit`, not retryable, otherwise. The status alone chooses the
  rule, and no word of the server's text is copied. The shape of the object does not change, so the contract version may stay 2.
- **Read on 2026-11-02:** the helper never retries and today sets `retryable` true only for an unreachable server (not for a
  certificate failure) and a timeout. Every `error_for`, `embed_error_for` and `models` status row is not retryable. Two helpers read
  the field, `review-engine` (`helper/review-engine`, about lines 663 to 675) and `action-review` (`helper/action-review`, about
  lines 1150 to 1163): each checks the exact key set and that `retryable` is a boolean, then reports "retryable" or "not retryable" in
  its message. Their tests state that a retryable failure is reported and not retried. Neither retries, so a 5xx reported as retryable
  changes only the word in their message. Increment B records this again from the code at that time.
- The text of the 500 seen once on an embedding call after a chat call is from the knowledge-base module's report, not from a reading
  made here; increment F shows what the owner's server does and records what it does not.
- **A value outside a grammar is a local refusal only.** The helper refuses it before any request, so the plan makes no claim about
  what the server does with a temperature above 2 or a malformed `keep_alive`, and increment F does not send one. The tests prove the
  refusal with a fake server that records that nothing arrived. A raw probe of the server with such a value is not in this plan; it
  would need the owner's word, its own request shape and a place to record it, and is deferred.
- No host address, port or home path is written to a tracked file. Examples use a placeholder host.

## Completion criteria

1. Two decision records are `Accepted` by the owner, one for the request controls and one for the retryable server errors, and each
   says what it changes in the earlier records.
2. `ask-ollama.md` and `model-bridge.md` describe the temperature, the keep_alive and the retryable statuses, and every rule has a
   test against a fake server.
3. A chat section may hold a `temperature`, a section of either kind a `keep_alive`, each validated by the grammar the decision sets,
   with every refusal naming the rule and never the value; `--temperature` and `--keep-alive` replace the section's values, are
   refused out of their form, and are refused by the commands that do not take them.
4. The request carries `options.temperature` and the top-level `keep_alive` only when a call or a section gives a value, and
   carries neither otherwise; `check` shows them on the model line.
5. A status 500, 502 or 503 is `retryable` true in `ask`, in `embed` and in `models`, with the same class, detail and message as
   before; 501 and every other status are as before; and no word of the server's is copied. The bridge makes one request.
6. `ask-codex`, its tests and the behaviour of the two engines are shown unchanged (by reading and by their tests of the field), or
   the plan has stopped and asked.
7. The owner's run against the real server records, from a small repeated sample (five short calls at temperature 0 and five at 1.0
   on a model with thinking off, and how many replies differ in each), that the temperature reached the server, without claiming
   that equal replies at 0 are guaranteed; a call's value replacing a section's; `keep_alive` acting on what the server keeps loaded
   (read from its list of loaded models), with `0` and `-1` sent as numbers and a duration sent as a string, as the helper sends
   them; and what the server does with an
   embedding call right after a chat call. If no 5xx appears, the record says "no 5xx seen" and the fake-server tests are the proof of
   the retryable rule. The spec records the server version and the date with no address.
8. `wb check`, `wb run code-work check` and `wb verify` report no problem, the targeted tests named in the Result pass, and the
   release preview reads `recorded`.

## Increments

### Increment A — Decide the request controls

**Outcome:** a `Proposed` decision record that amends the section fields of `2026-11-02-model-configurations-in-endpoint-records`
(as amended by `2026-11-02-model-section-defaults-and-the-embedding-name`) with a temperature and a keep_alive, with the owner's
acceptance asked for.
**Dependencies:** none.
**Affected areas:** `docs/decisions/` (a new record and its row in the index).
**Steps:**
1. Read `docs/decisions/README.md`, the two records to amend and `docs/specs/ask-ollama.md`, and use the `draft-decision` skill.
2. State how the file holds a temperature, given that its reader refuses a fraction: the string of a grammar (recommended), an integer
   in hundredths, or a change to the kit's reader (not recommended); the range, the number of decimals, and how the value is sent
   (`options.temperature`, a number).
3. State the section fields (`temperature` for a chat section only; `keep_alive` for both kinds), their grammar and refusals, and the
   rule that a section holds at most the fields of its kind.
4. State the call options `--temperature <value>` (for `ask` only) and `--keep-alive <value>` (for `ask` and `embed`), their forms,
   that a call's value replaces the section's, that `models` refuses both and `embed` refuses `--temperature`, and that both belong to
   `ask-ollama` and not to the contract's common core.
5. State what `check` prints, that a section with neither field sends what it sends today, and that the server's own default stands.
6. Write the alternatives (a number in the file by changing the kit; a default for the whole record; a call option with no section
   field; no `keep_alive`, with an owner-run unload; a temperature ceiling) and the honest consequences: a default hides what a call
   sends, `keep_alive` `-1` can starve other models on a one-card server, a temperature changes what a cache key built from the
   prompt must include, and the file grows.
7. Stop at `Proposed` and ask the owner, unless `wb settings` prints `level accept-decision: none`.
**Verification:** `wb check` and `wb run code-work check` report no problem; the record has every section of the template.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#A`.

### Increment B — Decide the retryable server errors

**Outcome:** a `Proposed` decision record that says which statuses of a bridge to a server are retryable, for which commands, and what
that means for the contract version, `ask-codex` and the engines, with the owner's acceptance asked for.
**Dependencies:** none (it may be written before A).
**Affected areas:** `docs/decisions/` (a new record and its row in the index).
**Steps:**
1. Read what `retryable` means in `docs/specs/model-bridge.md` and in the accepted decision `2026-11-01-bridge-contract-version-2`.
   Search the helpers and the kit for `retryable` and for any retry loop, and read what `review-engine.md` and `action-review.md` say
   about it. Record each reader and what it does with the field (on 2026-11-02 only `review-engine` and `action-review` read it, and
   neither retries). **If any reader retries on `retryable`, state how often and whether the new rule changes its behaviour for the
   worse, and stop and ask the owner before going on.**
2. State the rule: the statuses 500, 502 and 503 are `vendor_error` / `bad_exit` with `retryable` true (the recommendation), for
   `ask`, `embed` and `models` alike; 501 and every other status unchanged; the status alone chooses the row. State why 429 and 504
   are left out (the owner's list) and that a later record can add them.
3. State whether the contract version changes (recommended: no, since the shape of the object is the same and `retryable` already
   exists), what the contract text says (the rule is for a bridge to a server; a bridge to a program has no status), and that
   `ask-codex` is unchanged in code and in behaviour, with its tests unchanged.
4. Write the alternatives (a new detail such as `server_busy` with `retryable` true; making every 5xx retryable; retrying inside the
   bridge; leaving it to each caller) and the honest consequences: a caller may retry a 500 that is permanent (a corrupt model), a
   hostile server can choose the label, the retry budget is the caller's, and a retried embedding call repeats its cost.
5. Stop at `Proposed` and ask the owner, unless `wb settings` prints `level accept-decision: none`.
**Verification:** `wb check` and `wb run code-work check` report no problem; the record names every reader of `retryable` that it
found, with the file.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#B`.

### Increment C — Specify the three

**Outcome:** `ask-ollama.md` and `model-bridge.md` state what the two accepted decisions set, as the helper will be built.
**Dependencies:** A and B accepted.
**Affected areas:** `docs/specs/ask-ollama.md`, `docs/specs/model-bridge.md`.
**Steps:**
1. Add the two section fields to the section rules and the worked example, with the grammar and the refusals.
2. Add `--temperature` and `--keep-alive` to the options of `ask`, say which commands refuse them, add `options.temperature` and the
   top-level `keep_alive` to the request of `ask` and to `embed` (only `keep_alive`), and add the fields to the `check` model line.
3. Add the retryable rule to the table of errors and to the rule for when several conditions hold (the status alone chooses the row),
   and to `model-bridge.md` where it speaks of `retryable` and of a bridge to a server, with one sentence of guidance for a caller:
   a 500 can be permanent (a model that cannot load), so retry a few times with a wait of tens of seconds and then stop; the figure
   comes from a report and is marked as reported until increment F shows it.
4. Add checklist items for the validator, the request, the overrides, the refusals and the retryable statuses, each testable against a
   fake server; tag as unconfirmed, for increment F, the server behaviour that nobody has seen and that the helper can send (a
   temperature of exactly 2, the units of a keep_alive, the text of a 500); a value that the grammar refuses is a local refusal and
   is not tagged.
**Verification:** `wb check` and `wb run code-work check` report no problem; a reviewer reads every checklist item and finds it
testable.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#C`.

### Increment D — Temperature and keep_alive in the helper

**Outcome:** a section's `temperature` and `keep_alive` and the options `--temperature` and `--keep-alive` work as the specification says.
**Dependencies:** C.
**Affected areas:** `packages/workbench/ask-ollama/helper/ask-ollama` and its tests.
**Steps:**
1. Write the tests first in a scratch copy: the validator for each field (the grammar at its limits, every refusal, a field on the
   wrong kind of section, no value quoted), the request for each default and each override (`options.temperature` a number,
   `keep_alive` top level, a JSON number for `0` and `-1` and a string for a duration, neither when none is given, the exact key
   sets), and, separately for each grammar of "Assumptions and
   constraints", every accepted and every refused form that it lists (for the temperature `0`, `0.2`, `2.00` accepted and `-0.2`,
   `00.2`, `.5`, `2.01`, `0.123` refused; for the keep_alive `0`, `-1`, `30m` accepted and `-2`, `01s`, `30`, `5d`, `1.5h`
   refused), in the section field and in the option alike, each refused call making no request, `embed` and `models` refusing what
   they do not take, and the `check` line.
2. Make the helper pass them in one scripted pass, with the owner's word and a release.
3. Ask the `reviewer` to read the increment, and ask the owner whether a security review runs (two new options and two new request
   fields).
**Verification:** the module's tests pass (they ran against the old helper first and the new tests failed); `wb verify` reports no
problem; a test shows that a refused call made no request.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#D`.

### Increment E — The retryable statuses in the helper

**Outcome:** a status 500, 502 or 503 is reported with `retryable` true by `ask`, `embed` and `models`.
**Dependencies:** C.
**Affected areas:** `packages/workbench/ask-ollama/helper/ask-ollama` and its tests.
**Steps:**
1. Write the tests first: each of the three statuses in each of the three commands gives the same class, detail and message as
   before with `retryable` true, whatever the body (an object, an overflow text, `think`, not JSON); 501 (with and without the words
   of the embedding row), 429, 504, 400, 404 and 3xx are as before; the other rows (a refused connection, a timeout, a reply cut
   short) are as before; nothing of the body is copied; the helper makes one request.
2. Make the helper pass them in one scripted pass, with the owner's word and a release.
3. Run the tests of `review-engine` and `action-review` that read the field, to show that they are unaffected.
4. Ask the `reviewer` to read the increment.
**Verification:** the module's tests pass; `wb verify` reports no problem; the two engines' tests of the field pass; `ask-codex` and
its tests are untouched (shown by `git diff` listing no file of it).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#E`.

### Increment F — The run against a real server

**Outcome:** the three are shown against the owner's real server and recorded.
**Dependencies:** D and E, and the owner's word for the calls.
**Affected areas:** `docs/specs/ask-ollama.md` ("The run against a real server" and the statements it tags), and the helper if the
run shows a difference.
**Steps:**
1. Run the new helper from a scratch home with a file of format 2 that holds the new fields (as the earlier run did), reading the
   server's list of loaded models between calls.
2. The cases: a small repeated sample, five short calls at temperature 0 and five at 1.0, on a model with thinking off, counting
   how many replies differ in each (equal replies at 0 are not guaranteed, so the count is the record, not a pass or a fail); a
   call's `--temperature` replacing a section's; the top of the range (a temperature of exactly 2); `keep_alive` `0` on a chat call
   (is the model gone from the loaded list afterwards?), a short duration sent as a string (does it expire?), and `-1` sent as a
   number (does the server keep the model loaded?); the helper sends no other form, so a string `"-1"` and `-1m` are not cases of
   this run; no value that the grammar refuses is sent (those are refused by the helper
   and are shown by its tests, not by the server); an embedding call right after a chat call on the one-card server, with the chat
   model kept and with it unloaded, repeated enough times to see whether the 500 comes back, and, if it comes, how many tries a
   wait of tens of seconds needed (the knowledge-base module reported that six tries 20 seconds apart recovered every time on this
   server; that is a report, not a result of this plan); and, if a 5xx comes, what the bridge reports. If none comes, "no 5xx seen".
3. Record the server version, the models, the date and each result without the address, and what could not be caused. Correct the
   specification and the helper where the server differs, with a test that fails first, in a scripted pass.
**Verification:** the recorded run names a server version and a date and holds no address; the module's tests and the document
checks pass after any correction.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#F`.

### Increment G — Close out, documents and approvals

**Outcome:** the plan's result is written, the documents agree, and the shipped approvals are current.
**Dependencies:** A to F.
**Affected areas:** this plan's Result, `docs/development.md`, `docs/specs/model-bridge.md` ("As built"), the stale shipped approvals.
**Steps:**
1. Update `docs/development.md` for the new fields and options, and `model-bridge.md`'s "As built".
2. Run `wb check`, `wb run code-work check` and `wb verify`, and read each result.
3. List the stale shipped records with `wb preview release-approvals`, show the owner the exact list, and remove them through the
   commit helper only after the owner approves it.
4. Write the result of every increment under `## Result`, with the tests that ran and why that was enough.
**Verification:** the document checks and `wb verify` report no problem; the preview of the release reads `recorded` for the package
and every module.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#G`.

### Increment H — Record the upgrade

**Outcome:** the installed copy of the helper matches the package and the manifest records it.
**Dependencies:** G.
**Affected areas:** `.workbench/manifest.json` and the installed helper copy under `.workbench/workbench/`.
**Steps:**
1. The owner runs `wb upgrade` (and `wb acknowledge` if it asks). The new fields are optional, so the owner's file works unchanged;
   the owner may add them (the agent gives the exact text).
2. Compare every installed file with its source in the package by hash and read `wb check`; then, with the owner's word, make one
   call through the launcher to show that the installed helper answers.
**Verification:** `wb check` reports no problem; every installed file has the hash of its source.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-request-controls#H`.

## Verification for the plan as a whole

`wb check`; `wb run code-work check`; `wb verify packages/workbench`; the module's tests; the engines' tests of the field;
`wb preview release-approvals` (every record `recorded`, none stale); a search of the tracked files for a host address and a home
path; and the owner's run of increment F. The whole suite is not part of the plan's verification unless the owner asks or an
increment's risk calls for it.

## Risks and sensitive actions

- **A fraction in a file whose reader refuses one.** The temperature is held as a string (recommended), so the grammar and the
  conversion to a number are new code at a boundary. The grammar is exact, a refusal never quotes the value, and a test covers the
  hostile forms.
- **A contract change that reaches the engines.** Setting `retryable` true for more failures could change what a caller does. Both
  readers found (`review-engine`, `action-review`) report the field and do not retry; increment B reads them again and stops and asks
  if that has changed. `ask-codex` is unchanged.
- **A server answer that is not known.** The behaviour of the server for a keep_alive that it expires and for a transient 500 comes
  from a report, not from a reading made here; the run shows what it can and the specification says what it could not. A value that
  the grammar refuses never reaches the server, so the server's answer to one is neither claimed nor tested.
- **`keep_alive` `-1`.** It keeps a model loaded and can starve the other models on a one-card server. It is the owner's declaration
  in the file or the caller's choice by option; the specification says so.
- **A hostile server chooses a retryable row.** A server can answer 500 and so invite a retry. The label is advisory, the retry
  budget is the caller's, and the bridge never retries.
- **A temperature changes the output.** A caller whose cache key is built from the prompt must include it; the decision says so.
- **A real call.** Increment F sends test prompts to the owner's server, in the clear if the record is `http`; only the owner's word
  starts it, and the only effect on the server is what `keep_alive` is under test to do (unload or keep a model).
- **Releases and passes.** D, E (and F if it corrects the helper) are package changes that make the shipped approval stale until the
  owner releases; each needs the owner's word "run the pass" and one release, and the hooks refuse all work meanwhile.
- **Deleting stale approval records** (increment G) needs the owner's approval of the exact list.

## Review record

- **Reviewer:** the project's review engine through its bridge, model `gpt-5.6-terra`, at the owner's request.
- **Rounds:** 3 of a bound of 3. Each round returned `changes_needed` with one major finding; all three were applied; the text
  after the third fix was not reviewed again.
- **Applied:**
  - R1-F1: the tests of increment D named a general leading-zero and sign refusal that conflicted with valid values; each field now
    has an exact grammar with its accepted and refused forms.
  - R2-F1: increment F promised the server's answer to values that the helper refuses before sending; those are now local refusals
    only, and a raw probe is deferred.
  - R3-F1: criterion 7 and increment F named wire forms (`"-1"` as a string, `-1m`) that the helper never sends; they are limited
    to the forms the helper produces, and the other forms are deferred.
- **Rejected:** none.
- **Also applied, from the knowledge-base module's review (advice, not a reviewer round):** the helper sends `0` and `-1` as numbers;
  the temperature is recorded from a small repeated sample; the retry guidance for a caller; and the wording that the fake-server tests
  prove the retryable rule. Not applied: merging increments D and E.
- **Left for the owner:** the plan was approved by the owner without a fourth round.

## Deferred work

- Statuses 429 and 504 as retryable, and a retry loop in a caller library.
- A raw probe of what the server does with a temperature above 2, a malformed `keep_alive`, and the wire forms the helper never
  sends (`"-1"` as a string, `-1m`), which would need the owner's word, exact request shapes and a place to record them.
- A default for any other request field (`top_p`, `top_k`, `seed`, the stop words), and defaults for `models`.
- An exact count of tokens, a credential, a field naming the bridge of a record, and the test certificates generated at run time
  (the other deferred items of the earlier plan).
- A roadmap candidate for this work, if the owner wants one.

## Result

### Increment A

**Done:** `docs/decisions/2026-11-02-temperature-and-keep-alive-in-model-sections.md`, status `Proposed`, awaiting the owner's
acceptance (the level of `accept-decision` is `ask`). It amends the section fields of the two earlier records and nothing else: a
chat section may hold `temperature` and a section of either kind `keep_alive`, as exact grammars in ASCII; the temperature is held
as a string and sent as a number; `0` and `-1` of a keep_alive are sent as numbers and a duration as a string; `--temperature` (for
`ask`) and `--keep-alive` (for `ask` and `embed`) replace the section's value; `check` shows both. The wire mapping is marked as from
memory and a report, for increment F. The decisions directory has no index, so there was no row to add.

**Verification as run:** `wb check` and `wb run code-work check` report no problems; `wb run groundwork preview` printed the digest
for the owner's acceptance. No test was run (a document only).

**Review:** the `reviewer` agent read the record against the plan, the two earlier records, the spec, the kit and the helper: no
blocking finding and four non-blocking ones, all applied: the missing consequence that the file grows; the server's default
temperature marked as reported; the owner's quoted words replaced by a reference to the notes the owner pasted, because the quote
could not be shown to be the owner's; and the grammars made explicit as ASCII, whole-value matches, with the order of the `check`
line stated for an embedding section. One round of one.

**Accepted** by the owner with `wb run groundwork accept` (digest of the preview) and **committed** as `b5e3887`.

### Increment B

**Done:** `docs/decisions/2026-11-02-retryable-server-errors-in-bridges-to-a-server.md`, status `Proposed`, awaiting the owner's
acceptance. The rule: in a bridge to a server, a status 500, 502 or 503 is `vendor_error` / `bad_exit` with `retryable` true, the
message and detail as before, for `ask`, `embed` and `models`; 501 (the `embed` row and any other), 429, 504, every 4xx, every other
5xx and a redirect stay not retryable; the bridge never retries. The versions stay (bridge 2, embedding 1, `models` 1); `ask-codex`
and the two engines are unchanged. Readers of `retryable` found: `review-engine` and `action-review`, which report the flag and do
not retry; the kit's `call` module and every other helper do not read it.

**Verification as run:** `wb check` and `wb run code-work check` report no problems; `wb plan-status` reads `approved`;
`wb run groundwork preview` printed the digest. No test was run (a document only).

**Review:** the `reviewer` agent found no blocking finding and four non-blocking ones: (1) applied: a body over its bound
(`reply_too_large`) and a connection cut after the status line (`unusable_reply`) are judged before any status and keep their rows
under a 5xx, so the rule applies to a response read whole; (2) applied: the engines accept the versions they know, not "exactly";
(3) applied: the record says it leaves item 6 of the version-2 decision untouched; (4) not a defect: the owner's approval is read
by `wb plan-status`, which the reviewer did not run. **Note for increments C and E:** increment E's test line "whatever the body"
means whatever a body read whole within its bound; E also tests that an oversize and a cut-short 5xx response keep their rows.

**Choice for the owner at acceptance:** the record follows the approved plan (`bad_exit` with `retryable` true), which makes the
contract's sentence "false for the other codes defined here" untrue for a bridge to a server, and increment C amends it. The nearest
alternative, a new detail such as `server_busy`, is in the record. A change to it changes this plan's criterion 5 and increments C and
E and needs the owner's new approval of the plan.

**Accepted** by the owner with `wb run groundwork accept` (digest of the preview) as the plan recommended (`bad_exit` with
`retryable` true), and **committed** as `640d62f`.

### Increment C

**Done:** the specifications state what the two accepted decisions set, as the helper will be built (the helper is not changed).
`docs/specs/ask-ollama.md`: the header paragraph; the section fields `temperature` and `keep_alive` with their exact ASCII grammars,
accepted and refused forms, and the worked example; the rows `--temperature` (for `ask`) and `--keep-alive` (for `ask` and `embed`)
in the options table; `options.temperature` and the top-level `keep_alive` in the request of `ask` and of `embed` (only
`keep_alive`), with `0` and `-1` as numbers and a duration as a string; the errors table, with a row for a 500, 502 or 503 as the
retryable `bad_exit` and the precedence of `reply_too_large` and `unusable_reply`; a "Retrying" paragraph with the caller guidance,
marked as reported; the `check` line; the `models` and `embed` failure rules; checklist items 4 and 9 edited and items 20 (the
section fields), 21 (the call options) and 22 (the retryable statuses) added; unconfirmed statements 19 to 21 tagged "not shown"
for increment F; two Known limits; the governing decisions and plans. `docs/specs/model-bridge.md`: the exception in the `retryable`
sentence with one sentence of guidance for a caller, item 19 of the checklist, and the "As built" paragraph.

**Verification as run:** `wb check` and `wb run code-work check` report no problems; a search of the tests found none that reads
either specification, so no test was run (a document only); `wb plan-status` reads `approved`.

**Review:** the `reviewer` agent read both specifications against the two decisions and the helper: no blocking finding and three
non-blocking ones. (1) applied: the plan's step 3 asks for one sentence of guidance in `model-bridge.md` as well, now added next to
`retryable`; (2) applied: the clause "`ask-codex` and its tests are unchanged" is not a fake-server test, so it was removed from
checklist item 22 (the plan's verification shows it by `git diff`); (3) not a defect of C: `docs/development.md` still lists the old
fields and options, which increment G updates. One round of one.

**Open for the owner:** the commit of increment C.
