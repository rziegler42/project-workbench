# Model configurations in the endpoint file, a context ceiling, per-model defaults, and a rename of the file

Status: Proposed
Created: 2026-11-02
Candidate: workbench-v1#bridge-model-configurations
Specs: ask-ollama, model-bridge, terms, module-contract

## Goal

Today an endpoint record names one server and holds one `default_model`, one `embedding_model` and one `context`, and a caller may
name any model the server has. The first run (2026-11-02) showed what that costs: the window belongs to the model and not to the
endpoint, and a prompt longer than the window is cut by the server without an error. When the plan is done:

- Each endpoint record holds a configuration section for every model the owner allows on that server, with the model's kind (chat or
  embedding) and the largest context it accepts. Five models on one server are five sections in one record.
- A bridge that reads the file uses only a configured model. A model that is not configured, or that is configured for the other
  kind, is refused before anything is sent.
- The window of a call is the model's configured maximum, unless the owner configured a lower default for that model, or the caller
  asks for a smaller one with `--context`. A caller who asks for more than the model's maximum gets an error and nothing is sent.
- A prompt that is probably larger than the call's window is refused before it is sent, by a size rule the owner can tune for each
  model, so that the common case of a silent cut is stopped; the rule is an estimate and the plan says so.
- `ask-ollama models` shows which configured models the server has and which of its models are not configured.
- A model section can also hold the defaults of a call that a module should not have to know: the effort of thinking (or, for a
  model that only switches thinking on and off, whether it thinks) and a limit on the output. A caller that passes nothing gets
  them, and a call argument overrides them, so a module that calls the bridge by capability passes only the model name
  (`gpt-oss:20b` cannot turn thinking off, and its reasoning counts against the output limit).
- The capability name `text-embedding` is confirmed by the owner as vendor-neutral, in the decision and in the documents, so that a
  module may require it and a cloud embedding bridge may provide it later.
- The file is named for what it holds, `bridge-endpoints.json`, in a separate increment after the run.
- The result is shown against a real server, with the owner's word, and recorded without its address.

## Scope

- A decision record that supersedes `2026-11-01-endpoint-records-in-the-store` where this plan changes it: the format of a record,
  the allowlist, the context rules, the option `--context`, the refusal of the older format and the new file name (increment A). It
  is written as `Proposed` and the owner accepts it.
- The spec changes in `ask-ollama.md` and `model-bridge.md` (increment B).
- The helper `ask-ollama` and its tests: the new reader and validator, the allowlist, the kinds, the context rules and `--context`
  for `ask` (increment C), then `embed` and `check` on the same records (increment D).
- The size rule for a prompt (increment E) and the command `models` (increment F), each with its tests and its place in the spec.
- The defaults of a model section and the confirmation of the name `text-embedding`: a second decision record (increment F-A), the
  spec (F-B), and the helper, its tests and the documents that carry the name (F-C). Added on 2026-11-02 at the owner's request,
  after increments A to D were committed; the plan needs the owner's new approval for them.
- The owner's run against a real server, recorded in the spec (increment G).
- The rename of the file, the helper's constant, the module's `ask_reads` and every document that names it (increment H).
- The close-out, and the record of the upgrade (increments I and J).

## Non-goals

- An exact count of tokens, by a tokenizer or by a call to the server. The size rule is an estimate from bytes, and a prompt cut by
  the server's own window is still not detected exactly (see "Deferred work").
- A command or skill that writes the file. The owner writes it by hand.
- A credential, an authenticated endpoint, and a second bridge to a server. The file stays read only by `ask-ollama`.
- Changing `ask-codex`, the contract's common core or the contract version. `--context` is an option of `ask-ollama` only (see the
  assumptions).
- Reading the real window from the server, and any call to a server other than the owner's run in increment G.
- Replacing the test certificates.
- A default for the sampling options, the system prompt or any other request field than the three below (the temperature is
  deferred, not dropped: see "Deferred work"), and defaults for `embed`.
- Mapping `--effort` for a model that has levels and also an on-off switch, beyond what the real run shows.

## Assumptions and constraints

- The owner's word is needed for the real call of increment G, as for every call to a real server.
- The agent cannot write the guarded store. The owner writes the new file, and the plan gives the exact content. The helper does not
  read the older format: it refuses it with a message that names the rule and not a value. There is no fallback to the older file
  name or format, because a decision that no longer covers a file must not be read from it.
- Each package change (increments C, D, E, F, F-C and H) is one scripted pass and needs the owner's explicit word "run the pass", then one
  `wb release-approvals` by the owner. The new tests are written first and are seen to fail against the old helper.
- The record fields of the older format that stay are `scheme`, `host`, `port`, `location`, `authenticated`, `default_model` and
  `embedding_model`. The field `context` of the record is removed and becomes a field of each model section. A new field `models`
  is an object from a model name to its section.
- A model section holds `kind` (`chat` or `embedding`), `context` (a whole number, the largest window the owner declares for the
  model, taken from the model's own limit) and an optional `default_context` (a whole number from 1 to `context`; when it is absent
  the call uses `context`). A record holds 1 to 64 model sections; the keys follow the model-name rule of the older decision. A
  `default_model` must name a configured chat model and an `embedding_model` a configured embedding model.
- A call's window is, in order: the value of `--context`, else the model's `default_context`, else the model's `context`. It is
  sent as `num_ctx`. The check of the prompt against the window (`context_overflow`) uses that window.
- `--context` is a whole number from 1 to the model's `context`. A larger value, a value that is not a whole number, or the option
  with a model that is not configured is a refusal (`refused: ...` on standard error, exit 1, nothing sent), as every other bad
  option is. The option is not part of the contract's common core, so a caller that wants interchangeable bridges does not pass it;
  the decision of increment A confirms this or moves the option into the contract.
- `--model` is checked against the record's configured names. A name with a `/` therefore becomes usable through the file; the
  decision states the rule the bridge uses in place of the contract's character set for a bridge to a server, because the
  contract's set refuses the `/`.
- The defaults of a chat section (decision of increment F-A; embedding sections hold none of them): `effort` (`low`, `medium` or
  `high`) or `thinking` (a boolean, for a model that only switches thinking on and off), at most one of the two; and `output_limit`
  (a whole number from 1 to 10,000,000, in tokens). With no `--effort` and no `--thinking` the call sends `think` with the section's
  `effort` (a word) or `thinking` (a boolean); `--effort <level>` (already an option of the contract) and the new `--thinking on|off`
  replace it, and the two together are refused. `output_limit` is sent as the server's output cap (`options.num_predict`) and is
  both the default and the ceiling of the new option `--max-output <tokens>` (1 to 8 digits, as `--context` is; larger than the
  section's `output_limit` is refused with nothing sent; a section with no `output_limit` has no ceiling below 10,000,000). The new
  options belong to `ask-ollama` and not to the contract's common core, as `--context` does. A reply stopped at the output cap is
  `reply_cut`, as before. The mapping to the server's `think` and `num_predict` is from memory of the server's documentation, and
  the run of increment G confirms or corrects it; the on-off case may not be testable on the owner's server.
- The size rule: before a call the bridge compares the size of the prompt in bytes with the window of the call times a number of
  bytes per token. A model section may hold `bytes_per_token` (a whole number from 1 to 8); the decision of increment A sets the
  default, recommended as 2 (a token is at least one byte, so 1 never passes a cut prompt but refuses up to three times too much;
  2 passes ordinary text and code, and the owner sets 1 for a model whose work must never lose the start of a prompt, such as a
  review, or a higher figure for plain English). A larger prompt is `vendor_error` with `context_overflow`, not retryable, with a message that says the
  prompt is probably too long, and nothing is sent. It is an estimate: it refuses some prompts that would have fit, and it passes
  text that becomes more tokens than the figure allows, so it complements the check of the server's own count and does not replace
  it.
- The command `models` makes one read of the server's list of models (from memory of the server's documentation, `GET /api/tags`
  with a `models` list whose entries have a `name`; increment G confirms it). It is a call to the server, so a real one needs the
  owner's word; the tests use the fake server.
- The owner confirmed the name `text-embedding` on 2026-11-02 in the words "keep it, and keep it vendor-neutral": the knowledge-base
  module needs vectors from a pinned model and records which model made each vector, so the name must not mention Ollama; a cloud
  embedding bridge should satisfy the same requirement later; a hard requirement is right for its first version. The name `model-bridge`
  stays unconfirmed. Recording the confirmation changes `terms.md`, `module-contract.md`, `ask-ollama.md` and the module test that
  checks their wording, which is a package change, so it goes in increment F-C with the helper.
- The window the server reports for a prompt it cut is about half the window it was given (2026-11-02, Ollama 0.35.1). This plan
  does not change that, and its documents say so.
- No host address, port or home path is written to a tracked file. Examples use a placeholder host.

## Completion criteria

1. The decision record is `Accepted` by the owner, supersedes the older record on the points it changes, and the older record names
   it in its status line.
2. `ask-ollama.md` and `model-bridge.md` describe the new file, the allowlist, the kinds, the context rules and `--context`, and each
   rule has a test against a fake server.
3. A call with a model that is not configured, with a model of the wrong kind, with `--context` above the model's maximum, or with a
   file in the older format is refused before any request is made, and a test shows that no request reached the fake server.
4. A call without `--context` sends the model's `default_context`, or its `context` when there is none; a call with a smaller
   `--context` sends that value.
5. A prompt larger than the window times the model's bytes per token is refused before any request, as `context_overflow`; one at
   the bound is sent.
6. `ask-ollama models` prints `present`, `missing` and `unconfigured`, names only, against the fake server.
7. The owner's run against a real server shows an allowed model working, a model that is not allowed refused, `--context` above
   the maximum refused, the size rule refusing an oversize prompt, `models` agreeing with `ollama list`, and the defaults at work
   on `gpt-oss:20b` (the section's effort used with no argument, an argument overriding it, an output limit applied); the spec
   records the server version and the date with no address.
8. A model section may hold `effort` or `thinking` and an `output_limit`, validated by the rules above; a call that passes no
   `--effort` and no `--thinking` sends the section's `think`, the arguments override it, and `--max-output` is sent as the output
   cap and is refused above the section's `output_limit`; each rule has a test against a fake server, and `embed` and an embedding
   section refuse them.
9. The documents call `text-embedding` confirmed by the owner, and the module test checks that wording.
10. The file is `bridge-endpoints.json` everywhere (the helper, `ask_reads`, tests, documents), and a helper looking for the old name
   was removed, not kept as a fallback.
11. The whole suite, `wb check`, `wb run code-work check` and `wb verify` report no failure, and the release preview reads `recorded`.

## Increments

### Increment A — Decide the format, the allowlist, the context rules and the new file name

**Outcome:** a `Proposed` decision record that supersedes `2026-11-01-endpoint-records-in-the-store` on the format, with the
choices below stated and the owner's acceptance asked for.
**Dependencies:** none.
**Affected areas:** `docs/decisions/` (a new record and the index row); the status line of the older record, only after the owner
accepts.
**Steps:**
1. Read `docs/decisions/README.md` and the older record, and use the `draft-decision` skill.
2. State the format of a record with its `models` object and the rules of "Assumptions and constraints": the kinds, the context
   rules, the bounds (64 models, the largest `context`), the refusal of the older format and the name rule for a configured model.
3. Decide `--context`: an option of `ask-ollama` only, or part of the contract's common core (which would change `ask-codex` and the
   contract). Recommend the first and give the reason (a caller that passes it to `ask-codex` would be refused).
4. Decide how a configured name with a `/` is passed as `--model` (the configured set replaces the contract's character set for a
   bridge to a server), and record the effect on the contract's rule that an unknown `--model` is refused.
5. Decide the size rule: the default number of bytes per token (recommended 2), the field `bytes_per_token` of a model section,
   and that the refusal is `vendor_error` with `context_overflow` and not a refusal of the options (recommended, because a caller
   already handles that class). Decide the output of `models` and that it is an argument of the one command.
6. Decide the new name `bridge-endpoints.json`, that it changes in increment H and not before, and that there is no fallback.
7. Write the record with the alternatives rejected (a list of model names without sections, a `models` object in a second file, a
   server-reported window instead of the owner's) and the honest consequences: the older file stops working until the owner
   rewrites it, and the owner's declared `context` can be wrong for the server.
8. Stop at `Proposed` and ask the owner, unless `wb settings` prints `level accept-decision: none`.
**Verification:** `wb run groundwork check` (or the project's document check) reports no problem; the record has every section of the
template; the index lists it with its status.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#A`; the owner's acceptance is a
separate commit if the record changes status.

### Increment B — Specify the new file and the context rules

**Outcome:** `ask-ollama.md` and `model-bridge.md` state what the decision sets, as they will be built.
**Dependencies:** A accepted.
**Affected areas:** `docs/specs/ask-ollama.md`, `docs/specs/model-bridge.md` (guarantee 7 and the checklist item for the endpoint
file), `docs/specs/module-contract.md` only if `ask_reads` is described there.
**Steps:**
1. Rewrite the endpoint file section of `ask-ollama.md`: the format, the `models` object and its fields, the bounds, the
   refusals (each a sentence naming the rule, never a value), the older format refused, and one worked example with a placeholder
   host and three models of two kinds.
2. Rewrite the rules for `--model`, add `--context`, and rewrite "The window" and the rule that a prompt that does not fit is an
   error, using the window defined above. Keep the limit that the server cuts a prompt silently and reports about half the window.
3. Add the size rule and the section of `models`, and update the conformance checklist: a model not configured, a model of the other kind, `--context` out of range, the older
   format, the window sent for each of the three cases, the size rule at and over its bound, and `models`. Each item is testable against the fake server.
4. Update `model-bridge.md` where it says the endpoint record holds `context` or that `--model` is a free name, and say that the
   decision replaces the character set for a bridge to a server.
5. Do not name the new file yet in the places that increment H changes; the documents name `endpoints.json` until H.
**Verification:** `wb check` and `wb run code-work check` report no problem; a reviewer reads every checklist item and finds it
testable.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#B`.

### Increment C — The reader, the allowlist, the context rules and `--context` for `ask`

**Outcome:** `ask-ollama ask` reads the new format, refuses a model that is not configured and applies the window rules.
**Dependencies:** B.
**Affected areas:** `packages/workbench/ask-ollama/helper/ask-ollama` and the tests under `packages/workbench/ask-ollama/tests/`,
the fixtures of the fake-server tests, and `.workbench/` only through the owner's later upgrade.
**Steps:**
1. Write the tests first in the scratchpad copy: the format and every refusal of the validator, the allowlist and the kind check
   for `ask`, the window sent in the three cases, `--context` out of range and without a configured model (nothing sent), the
   older format refused, and the window check using the sent window. Move the fixtures of the existing tests to the new format.
2. Make the helper pass them: `validate_record` and `validate_document` for the new fields, `select_model`, the new option
   `--context` in `parse_options`, and the request's `num_ctx` from the chosen window.
3. Run the module's tests against the old helper (the new tests must fail), copy the new helper, run them again. This is one
   scripted pass and needs the owner's word, then one release.
4. Ask the `reviewer` to read the increment; ask the owner whether a security review runs (the change touches parsing of an
   owner file and an option that sets a request field).
**Verification:** the module's tests pass; the whole suite passes; `wb verify` reports no problem; a test shows that a refused call
made no request.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#C`.

### Increment D — `embed` and `check` on the model sections

**Outcome:** `embed` takes its model from the configured embedding models, and `check` prints each record with its models.
**Dependencies:** C.
**Affected areas:** the helper and its tests as in C.
**Steps:**
1. Tests first: `embed` refuses a model that is not configured or is a chat model, uses `embedding_model` when `--model` is absent,
   sends the window rules of C when the model's `context` applies, and accepts `--context` within range; `check` prints one line per
   record and one per model (name, kind, `context`, the default window) and still contacts no server; the cleartext warning stays.
2. Make the helper pass them in the same scripted pass pattern, with the owner's word and a release.
3. The chat model sent to the embedding route (the 501 that increment F of the earlier plan found) is now refused before the call;
   keep the 501 row for a model that is configured as an embedding model but is not one on the server.
**Verification:** as in C.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#D`.

### Increment E — The size rule for a prompt

**Outcome:** a prompt that is probably larger than the window of its call is refused before it is sent, as an error the caller
already handles.
**Dependencies:** D.
**Affected areas:** the helper and its tests, as in C.
**Steps:**
1. Tests first: a prompt of at most the window times the bytes per token is sent; a larger one is `vendor_error` with
   `context_overflow`, not retryable, with the message "the prompt is probably larger than the window", and no request reaches the
   fake server; the figure is the model's `bytes_per_token` or the default of the decision; the window used is the one of increment
   C (`--context`, `default_context`, `context`); the rule runs after the options and the model are validated; no part of the prompt
   is in the message; a prompt exactly at the bound is sent.
2. `embed` is not changed: the server already answers a text that is too long with a 400 that is `context_overflow` (confirmed on
   2026-11-02).
3. Make the helper pass them in a scripted pass, with the owner's word and a release.
4. Ask the `reviewer` to read the increment.
**Verification:** as in C; a test shows that a refused prompt made no request.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#E`.

### Increment F — The command `models`

**Outcome:** `ask-ollama models` prints which of the configured models the server has, and which models of the server are not
configured.
**Dependencies:** E.
**Affected areas:** the helper and its tests, `packages/workbench/ask-ollama/module.json` (`arguments` gains `models`), and the
module's declaration test.
**Steps:**
1. Tests first, against the fake server: one `GET` of the server's list of models, with no body and no query, to the record chosen
   by `--server`; one object of its own contract 1, with `present` (configured, and on the server), `missing` (configured, not on the
   server) and `unconfigured` (on the server, not configured), names only, at most 512 names in a list, a name that does not fit the
   model-name rule is not printed and is counted; the same failure objects and bounds as the other commands (a server that is not
   reachable, a reply that is not usable, a body over its bound); it changes nothing and reads only the endpoint file.
2. Make the helper pass them, add `models` to the declaration, in a scripted pass with the owner's word and a release.
3. The shape of the server's reply (`models`, each with a `name`) is an unconfirmed statement of `ask-ollama.md`; increment G
   confirms or corrects it.
4. Ask the `reviewer` to read the increment.
**Verification:** as in C; the verifier accepts the declaration with the new argument.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#F`.

### Increment F-A — Decide the defaults of a model section and confirm the name `text-embedding`

**Outcome:** a `Proposed` decision record that amends item 3 of `2026-11-02-model-configurations-in-endpoint-records` (a model section
holds exactly four fields) with the optional defaults and their overrides, and records the owner's confirmation of the capability
name `text-embedding`; the owner's acceptance is asked for.
**Dependencies:** F.
**Affected areas:** `docs/decisions/` (a new record).
**Steps:**
1. Read `docs/decisions/README.md` and the record to amend, and use the `draft-decision` skill. The new record names the one it
   changes and leaves every other item of it standing; the older record is not edited.
2. State the fields (`effort`, `thinking`, `output_limit`), their forms and bounds, that a chat section may hold them and an
   embedding section may not, that a section holds at most one of `effort` and `thinking`, and how each is sent (`think` with a word,
   `think` with a boolean, `options.num_predict`).
3. State the call arguments: `--effort` (already of the contract) and the new `--thinking on|off` replace the section's setting and
   are refused together; the new `--max-output <tokens>` replaces the section's `output_limit` and is refused above it. State that the
   new options belong to `ask-ollama` and not to the common core, as `--context` does, and that `embed` refuses them.
4. State that the mapping to the server's `think` and `num_predict` is from memory of its documentation and is confirmed or
   corrected by the run of increment G, and that a model that only switches thinking may not be testable.
5. Record the confirmation of `text-embedding` in the owner's words (vendor-neutral, a hard requirement for a first version, a cloud
   bridge may provide it) and that `model-bridge` stays unconfirmed.
6. Write the alternatives (a default in the caller, a default for the whole record, one `think` field that takes a word or a boolean,
   an output limit with no ceiling) and the consequences, the bad ones included: a default hides what a call sends, the file grows,
   and an owner can set an effort that a model rejects, which then shows as `effort_unsupported` on every call to it.
7. Stop at `Proposed` and ask the owner, unless `wb settings` prints `level accept-decision: none`.
**Verification:** `wb check` and `wb run code-work check` report no problem; the record has every section of the template.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#F-A`.

### Increment F-B — Specify the defaults

**Outcome:** `ask-ollama.md` (and `model-bridge.md` where it speaks of `--effort`) state what the accepted decision of F-A sets, as it
will be built.
**Dependencies:** F-A accepted.
**Affected areas:** `docs/specs/ask-ollama.md`, `docs/specs/model-bridge.md`.
**Steps:**
1. Add the three fields to the section rules of "The endpoint file" with their bounds and refusals, and the worked example.
2. Add `--thinking` and `--max-output` to the options of `ask`, say which are refused for `embed`, and say how `--effort` now
   reads (a default from the section).
3. Add the request mapping (`think`, `options.num_predict`) to "`ask`: the request", the rule for a reply stopped at the cap to the
   section on a cut reply, and the three fields to the model line of `check`.
4. Add checklist items for the validator, the defaults, the overrides, the refusals and the request, each testable against a fake
   server. Tag the server's mapping as unconfirmed for increment G, and change the lines that call `text-embedding` the spec's
   proposal.
**Verification:** `wb check` and `wb run code-work check` report no problem; a reviewer reads every checklist item and finds it
testable.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#F-B`.

### Increment F-C — The defaults in the helper, and the confirmed name in the documents

**Outcome:** a section's `effort`, `thinking` and `output_limit` are read, validated and used as the specification says, and the
documents and the module test say that the owner confirmed `text-embedding`.
**Dependencies:** F-B.
**Affected areas:** `packages/workbench/ask-ollama/helper/ask-ollama` and its tests; `docs/specs/terms.md` and
`docs/specs/module-contract.md` (the wording about the name) and the module test that checks it.
**Steps:**
1. Write the tests first in the scratchpad copy: the validator for each field and every refusal (bool or float where a whole number
   belongs, a word outside the three, both `effort` and `thinking`, a field on an embedding section), the request for each default
   (`think` with a word, `think` with a boolean, `options.num_predict`), each override, `--effort` and `--thinking` together refused,
   `--max-output` above the ceiling, out of its form and with no configured model refused with nothing sent, `embed` refusing the new
   options, and the model line of `check` with the new fields. Change the module test so that it checks that the documents say
   the owner has confirmed `text-embedding` and still say that `model-bridge` is unconfirmed.
2. Make the helper pass them and reword the two documents, in one scripted pass with the owner's word, then a release. The new tests
   must fail against the old helper.
3. Carry in the same pass the two small items deferred from D (the docstring of `test_askollama_sections.py`, and one constant for
   the digit-run pattern that the reply parser and the file reader share).
4. Ask the `reviewer` to read the increment; ask the owner whether a security review runs (new options that set request fields).
**Verification:** the module's tests pass; the whole suite passes; `wb verify` reports no problem; a test shows that a refused call
made no request.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#F-C`.

### Increment G — The run against a real server

**Outcome:** the allowlist and the context rules are shown against a real server and recorded.
**Dependencies:** F-C, and the owner's word for the calls.
**Affected areas:** `docs/specs/ask-ollama.md` ("The run against a real server" and the statements it tags), the helper if the run
shows a difference.
**Steps:**
1. Give the owner the exact file to write (the new format, with the models of the server that the owner names, and `context` for each
   taken from the model's own limit as `ollama show` prints it; the agent reads `ollama show` for each model only on the owner's
   word) and the commands to run.
2. The cases: a plain prompt with an allowed model; the same with a second model; a model that is not configured (refused, nothing
   sent); `--context` below, at and above the maximum; a prompt under the size rule's bound but over the window (a record with a high
   `bytes_per_token` for the test, to see again what the server does with it); an embedding
   with a configured embedding model; an embedding with a configured chat model (refused); the older file format (refused); a
   prompt larger than the size rule (refused, nothing sent); `models`, compared with `ollama list`; and the defaults on
   `gpt-oss:20b`: a section with `effort` low and no argument (the call sends the level), `--effort high` overriding it, an
   `output_limit` applied and `--max-output` below and above it (refused above), `thinking` on and off on `gemma4:12b` (the owner's
   server reports it as taking on or off; if the model is gone, recorded as not shown), and the two combinations that the
   knowledge-base module did not try: `thinking` false sent to `gpt-oss:20b` and a level sent to `gemma4:12b`, each recorded as the
   server answers it. The example file of step 1 sets, for the two chat models, the context at the model's limit, a
   `default_context` of 16384, an `output_limit` of 10000 for `gpt-oss:20b` and 6000 for `gemma4:12b`, and a `bytes_per_token` that
   the owner chooses for the prompts it sends (the figure of 2 is the default).
3. Look for a way to make the server refuse an oversize chat prompt instead of cutting it (a setting that does for chat what
   `truncate` false does for an embedding), and for a way to have it count the tokens of a prompt. Record what the server version
   offers or that it offers nothing. If it offers one, stop and ask the owner: using it is a new increment, since it changes the
   request and the errors, and the size rule would then be the backstop.
4. Record the server version, the models, the date and each result without the address. Correct the spec and the helper where the
   server differs, with a test that fails first, in a scripted pass.
**Verification:** the recorded run names a server version and a date and holds no address; the whole suite and the checks pass after
any correction.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#G`.

### Increment H — Rename the file to `bridge-endpoints.json`

**Outcome:** the file is `bridge-endpoints.json` everywhere and the helper reads no other name.
**Dependencies:** G.
**Affected areas:** the helper's `ENDPOINT_FILE`, `packages/workbench/ask-ollama/module.json` (`ask_reads`), the tests that read the
path, `ask-ollama.md`, `model-bridge.md`, `docs/development.md`, the older decision's status line (already superseded by A), and the
owner's file on disk.
**Steps:**
1. Tests first: a call with only the old name present is refused with the message for a missing file, and the helper's text names the
   new name only.
2. Change the constant, `ask_reads`, the tests and the documents in one scripted pass, with the owner's word and a release.
3. The owner renames the file on disk in the terminal (`mv`, given exactly), and the agent runs `wb run ask-ollama check` once.
**Verification:** a search of the tracked files for the old name finds it only in decisions and plans (history); `wb run ask-ollama
check` prints the records of the renamed file; the whole suite passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#H`.

### Increment I — Close out, documents and approvals

**Outcome:** the plan's result is written, the documents agree, and the shipped approvals are current.
**Dependencies:** A to H.
**Affected areas:** this plan's Result, `docs/development.md`, the stale shipped approvals.
**Steps:**
1. Update `docs/development.md` for the new file, `--context`, the allowlist and the defaults (`--thinking`, `--max-output`), and
   `model-bridge.md`'s "As built".
2. Run the whole suite, `wb check`, the plan check and `wb verify` on the package, and read each result.
3. List the stale shipped records with `wb preview release-approvals`, show the owner the exact list, and remove them through the
   commit helper only after the owner approves it.
4. Write the result of every increment under `## Result`.
**Verification:** the full suite reports no failure; `wb check`, `wb run code-work check` and `wb verify` report no problem; the
preview of the release reads `recorded` for the package and every module.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#I`.

### Increment J — Record the upgrade

**Outcome:** the installed copy of the helper matches the package and the manifest records it.
**Dependencies:** I.
**Affected areas:** `.workbench/manifest.json` and the installed helper copies under `.workbench/workbench/`.
**Steps:**
1. The owner runs `wb upgrade` (and `wb acknowledge` if it asks).
2. Read what changed and check that each installed helper is byte for byte the helper in the package.
**Verification:** `wb check` reports no problem; the installed helper has the same hash as the helper in `packages/workbench/`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-02-bridge-model-configurations#J`.

## Verification for the plan as a whole

The whole suite, `python3 -B -W error tests/run_all.py`; `wb check`; `wb run code-work check`; `wb verify packages/workbench`;
`wb preview release-approvals` (every record `recorded`, none stale); a search of the tracked files for a host address, a home path
and the old file name; and the owner's run of increment G.

## Risks and sensitive actions

- **A breaking change to an owner file.** After increment C the helper refuses the older file until the owner rewrites it. The plan
  gives the exact new content; nothing falls back to the older format.
- **A declared maximum that is wrong.** `context` is the owner's declaration. A value above what the server gives is sent as
  `num_ctx` and the server may clamp or refuse it; the run of increment G shows what Ned does. A value that is too high costs the
  server memory.
- **A prompt cut by the server can still pass.** The window is set per model and the size rule refuses most oversize prompts, but it
  is an estimate and the count the server reports for a cut prompt still defeats the check (2026-11-02). The size rule also refuses
  some prompts that would have fit. The documents say both.
- **Parsing an owner file and a new option.** The validator reads a larger file and the option sets a request field. The bounds and
  the refusals are tested, and a security review is the owner's choice in C.
- **A real call.** Increment G sends content to the owner's server in the clear if the record is `http`; only the owner's word starts
  it, and the prompts are test prompts.
- **Defaults that hide what a call sends.** A section's effort or output limit is applied when the caller passes nothing, so a caller
  cannot see it from its own arguments; `check` prints the defaults, and an effort that the model rejects shows as
  `effort_unsupported` on every call to it.
- **A mapping from memory.** The server's `think` (a word or a boolean) and `num_predict` are from memory of its documentation; the
  run of increment G checks them, and the on-off case may not be testable on the owner's server.
- **Releases and passes.** C, D, E, F, F-C and H are package changes that make the shipped approval stale until the owner releases; each needs
  the owner's word "run the pass" and one release, so the hooks refuse all work meanwhile.
- **A rename that leaves a stale name.** A search of the tracked files and the removal of any fallback are the checks.
- **Deleting stale approval records** (increment I) needs the owner's approval of the exact list.

## Review record

**2026-11-02, round 1 of 3, by the review engine through the Codex bridge** (model reported as `gpt-5.6-terra`; reading
`changes_needed`, one finding, not converged).

- R1-F1, major: the plan has `Candidate: none` and so no roadmap candidate. **Rejected**: the plans README allows `none` with a
  one-line reason and the plan gives it, and adding a candidate changes a roadmap, which is the owner's decision. The owner then asked
  for the candidate: `workbench-v1#bridge-model-configurations` was added and the Candidate line names it, so the plan's bytes
  changed after this round.

The reviewer found nothing else in the plan's content; it called it detailed and aligned with the two specs named.

**2026-11-02, after increment D:** the plan was extended at the owner's request with increments F-A, F-B and F-C (the defaults of a
model section, and the confirmation of `text-embedding`) and the matching goal, scope, assumptions, criteria, risks and run cases. The
owner re-approves it. The extension was not reviewed by the engine; the owner may ask for a round.

**2026-11-02, after the knowledge-base module's review of the bridge:** four items were added to "Deferred work" (the temperature as
a section default, the loaded models from `/api/ps`, `keep_alive`, and a retryable 5xx), the temperature line of the non-goals was
reworded to say it is deferred, and increment G was given the example values and the two combinations of thinking that the review
asked for. The owner re-approves the plan.

## Deferred work

- An exact count of tokens, and a command that reads each model's real window from the server, so that the owner need not declare it.
- A field on a record that names the bridge it is for, if a second bridge to a server reads the file.
- A credential for an authenticated endpoint, which needs a decision of its own.
- Generating the test certificates at run time instead of keeping them in the repository.
- The temperature as a section default with a call override. It matters for the knowledge-base module, which validated its prompts
  at 0.2 (0.5 on a retry) while the server's own default is higher, and whose idempotence key assumes outputs that are reasonably
  stable.
- A default for any other request field, and defaults for `embed`.
- The models that are loaded on the server (`/api/ps`), as part of `models` or as a new argument, for a diagnostic.
- `keep_alive`, a request field: on a server with one 12 GB card an embedding call right after a chat call failed once with a 500.
- Whether a transient 5xx status (memory pressure on the server) should be retryable. Today every 5xx is `bad_exit`, not retryable;
  a change is a question for the contract of `model-bridge.md`.
- The roadmap candidate `workbench-v1#bridge-model-configurations` names the allowlist, the windows, the size rule and `models` but
  not the defaults of a section; its text may be extended if the owner wants direction recorded there.

## Result

### Increment A

**Done:** the decision record `docs/decisions/2026-11-02-model-configurations-in-endpoint-records.md`, written as `Proposed`. Its nine
numbered decisions set: format 2 (format 1 refused, no fallback); the record without `context` and with `models` (1 to 64 sections of
`kind`, `context`, optional `default_context` and optional `bytes_per_token`), and a file bound raised from 65,536 to 262,144 bytes;
the allowlist and the kinds, and the record's model rule in place of the contract's character set for a bridge to a server; the
window of a call (`--context`, else `default_context`, else `context`) with `--context` an option of `ask-ollama` only; the size rule
with a default of 2 bytes per token; the `models` argument; the rename to `bridge-endpoints.json` in increment H, with no fallback;
and what stands from the earlier record. The earlier record is not edited; the new record lists the items it supersedes.

**Verification as run:** `wb check` and `wb run code-work check` report no problems. `wb run groundwork preview` on the record prints
sha256 `c557be5e…` and a digest, and the status line `Proposed`.

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied: item 1 no longer contradicts item 8 (format 1 is
refused from the new reader and the old name after the rename); the supersession is listed item by item; the file bound's reason is
stated by arithmetic and flagged as an addition the plan does not name; the evidence says which readings of the server are not yet in
the spec (increment B adds them); claims not measured are marked as estimates or unconfirmed; the effect on the contract's `--model`
rule is stated; the two handlings of the file and the half-window question are consequences. One finding is left for increment G
or a plan change: whether a prompt between half the window and the whole window is cut is not tested by any case of G, and a plan
edit after approval needs the owner's new approval. A security review was not asked for: this is a decision record.

**Acceptance:** the owner asked for it and `wb run groundwork accept` ran with the previewed digest (`b68fef57…`, level `ask`); the
record now carries the owner's acceptance in its status line and its recorded sha256 is `c557be5e…`.

**Not done in A:** increments B to J were not started. The decisions README has no index list to update.

**Open for the owner:** whether the earlier record, which this one
supersedes in part, stays `Accepted` (recommended, because it still governs the items that stand) or gets a `Superseded by` line;
the default of 2 bytes per token; the file bound; and whether to add a case for the range between half the window and the whole
window to increment G.

### Increment B

**Done:** `docs/specs/ask-ollama.md` and `docs/specs/model-bridge.md` state what the accepted decision sets, as the module will be
built by increments C to F (the header of `ask-ollama.md` says that until each is built the module reads format 1). In
`ask-ollama.md`: the endpoint file of format 2 with every field and bound of a record and of a model section, the refusal of format 1
(and of any other `format`), a worked example with a documentation-range placeholder host, the allowlist and kinds; `--model` as a
configured key and the new option `--context` (1 to 8 ASCII digits, no sign, no leading zero); the window of a call and the request's
`num_ctx` always sent; the size rule (default 2 bytes per token) with its row in the table of errors; `check` printing a line for each
model; the new argument `models` (`GET /api/tags`, three lists and a `skipped` count); the `embed` options and request; checklist items
3 and 4 changed and items 12 to 16 added; the readings of the run that the decision cited (the model's limit of 16384, the loaded
windows, the text of the 501); unconfirmed 16 (the list route) and the tags moved to the end of their items; and Known limits (the
cut that can still pass, the owner's declared `context`, the estimate, the allowlist as no boundary). In `model-bridge.md`: the
`--model` row, the endpoint-record paragraph of guarantee 7, and checklist items 3 and 19. `docs/specs/module-contract.md` was not
touched: it does not describe `ask_reads`.

**Verification as run** (Python 3.15.0, macOS): `wb check` and `wb run code-work check` report no problems; the whole suite,
`python3 -B -W error tests/run_all.py`: 6,548 tests in 14 roots, OK. A scan of both specs finds one dotted address, `192.0.2.10`
(the placeholder of the example), and no home path.

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied: the older-format wording is for format 1 only and any
other `format` has its own line; the `embed` synopsis names `--context`; `models` states its options, that it reads no standard input,
that it needs no model and that names are compared as exact text, and its checklist item tests `--server`, `--timeout`, `skipped`, the
order of the lists and a bad file; checklist item 12 adds a section that is not an object, a `models` of the wrong type and 64
against 65 sections; `--context` has an exact syntax; "Known limits" no longer speaks of `context` in a record; and the `--model` row
of `model-bridge.md` says a configured name must fit the record's model rule. Noted, not changed: the specs add details that the decision
does not state (the `skipped` key and the 512-name cap, the path and headers of `models`, the `window=` and `bytes_per_token=` fields of
`check`, and the size rule running after the schema is read); the unconfirmed list still carries items the run did not reach, each
with its reason, as the acceptance criterion allows. A security review was not asked for: documents only.

**Not done in B:** the module is not changed; increments C to J are not started.

**Open for the owner:** the details the specs add beyond the decision, listed above.

### Increment C

**Done:** `packages/workbench/ask-ollama/helper/ask-ollama` reads the endpoint file of format 2: `format` 1 is refused as an older
format and any other number as "not 2"; the file bound is 262,144 bytes; a record has no `context` and requires `models` (1 to 64
sections of `kind`, `context`, optional `default_context` and optional `bytes_per_token`, each with its bounds); `default_model` and
`embedding_model` must be configured and of their kind. `select_model` uses only a configured model of the kind the command needs
(a refusal never quotes the name); `--model` is checked by the record's model rule (so a name with a `/` can be given when it is
configured); `--context` (1 to 8 digits, no sign, no leading zero) is an option of `ask` and `embed`, refused above the section's
`context`; the window of a call is `--context`, else `default_context`, else `context`, always sent as `num_ctx`, and the check of the
server's count uses it. The shared test fixture `record()` builds format 2 (standard models are configured in every record that gives
no `models`, so the allowlist tests use names outside that set); existing tests moved to format 2; a new file,
`test_askollama_sections.py`, holds the format, allowlist and window tests (and a float where a whole number belongs is shown to be
refused as not strict JSON).

**Deviation from the plan:** because the record's shape changed, `embed` already takes its model from the configured embedding models
and sends the window rules in this increment; increment D adds its own new tests for `embed` and the `check` model lines.

**Verification as run** (Python 3.15.0, macOS): the module's tests in a scripted pass that copied the tests first: against the old
helper 257 tests ran and 192 failed (191 failures and 1 error, as expected, since the fixtures are in format 2); against the new helper
all 257 pass. The whole suite, `python3 -B -W error tests/run_all.py`: 6,582 tests in 14 roots, OK. `wb verify packages/workbench`
prints no refusal; `wb check` and `wb run code-work check` report no problems. `wb preview release-approvals` after the release:
14 records `recorded`, 2 stale (`ec712287…` and `f50d8904…`, the records of the earlier plan's increment G, replaced by the new tree).

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied (spec only): item 12 and the header of `ask-ollama.md`
(a fraction such as 2.5 for `format` is not strict JSON and is refused as that; the header says what C built). Deferred to the pass
of increment D, to avoid a release for each: (a) `validate_document` refuses unknown top-level fields before it reads `format`, so a
format 1 file with an extra top-level key gets "field not allowed" and not "older format" (still refused, nothing sent; check
`format` first); (b) the docstring and the name of one test in `test_askollama_window.py` still speak of the old record ("the window of
the record", plan of 2026-11-01); (c) the endpoint file goes through the kit's `jsonstrict`, which has no guard for a run of more than
4,300 digits, so such a number is refused only by Python's own limit (a caller who lifts the limit could make parsing slow; the file
is the owner's and bounded); a test and a decision about a guard are open. Not applied: the digit-count case "123456789" of the
`--context` test is also refused by the ceiling (the behaviour is the same either way), and the `Windows` and `Window` test classes
overlap (harmless).

**Security review** (asked by the owner; the `security-reviewer`, on a copy with a loopback fake server and a temporary home, the
tree untouched): no Critical, High or Medium finding. About 90 hostile endpoint files (every field with odd types, bools and floats,
huge integers and a 5,000-digit run, deep nesting, duplicate keys, 65 models, option-like and control-character names, wrong kinds)
and about 20 hostile option values were each refused with a `refused:` line, no request reached the server, and no refusal quoted a
file value, host, port or model name; no route was found from the file or the options to the destination, path, headers or method,
or for an unconfigured or wrong-kind model to the server (`embed` included); the window arithmetic and the `--context` ceiling are
exact; the largest valid file parses in about 10 ms; imports and calls are unchanged apart from the new functions, with no write,
subprocess, `eval` or `exec`. Low findings: (1) a model name is matched as exact text, while a server may treat `m` and
`m:latest` as one model, so an owner file that configures them with different kinds is accepted (an owner mistake, no attacker path):
documented in "Known limits" of `ask-ollama.md`; a parse-time refusal is possible and is the owner's choice for increment D's pass;
(2) `parse_options` echoes an unknown option name of the caller (cut to 60 characters and ASCII-filtered, unchanged by this
increment); (3) `context` up to 10,000,000 becomes `num_ctx` and could cost the server memory (the owner's declaration, already a
known limit). Limits of the evidence: the reviewer ran the helper in-process from a copy, not as a separate process, could not run
`git` or the project's own tests, and did not retest the transport or TLS code, which this increment does not change.

**Releases:** one of `wb release-approvals` by the owner in this increment (the first plain attempt was refused at level `ask`
and the owner then ran it in a terminal).

**Not done in C:** the size rule, the `models` argument and the model lines of `check` (increments E, F and D); the two stale shipped
records and the new untracked ones stay out of the commit until increment I.

**Open for the owner:** whether increment D's pass also refuses two model names of one record that are equal after lower-casing and
dropping a trailing `:latest` (Low 1 of the security review; documented as a known limit otherwise). (Done in D; see below.)

### Increment D

**Done:** `ask-ollama check` prints, after each record line, one line for each model of the record
(`model <record>/<model> kind=… context=… window=… bytes_per_token=…`, the window being `default_context` else `context`, the figure
2 when absent, the constant `DEFAULT_BYTES_PER_TOKEN`); the warnings still come after every record and model line and host and port
are never printed. The items deferred from C went into the same pass: `validate_document` reads `format` before the other top-level
fields (a format 1 file with another field is still "older format"); the reader refuses a run of more than 4,300 digits anywhere in the
file as "not strict JSON" before parsing (a test lifts the interpreter's limit and shows the guard still holds); the window test's
wording is fixed; and, as the owner left it to the recommendation, two model names of one record that are equal after lower-casing and
dropping a trailing `:latest` are refused (the same name in two records is read). The alias rule is recorded in the spec (the file
section, checklist item 12 and "Known limits") and not by a new decision: it tightens the validator and leaves the exact-text
allowlist of decision item 4 as it is; a decision amendment would be a superseding record, which the reviewer and I judged
disproportionate, and the owner may still ask for one.

**Deviation from the plan:** step 1 of D asked for new `embed` tests (a model not configured, a chat model, `embedding_model` used
when `--model` is absent, `--context` in range). They were written in C, in the classes `Allowlist` and `Windows` of
`test_askollama_sections.py`, when `embed` moved to the new records; D adds none for `embed`. The 501 row for a model that is
configured as an embedding model and that the server cannot embed with is unchanged and is covered by the existing error test.

**Verification as run** (Python 3.15.0, macOS): the module's tests in a scripted pass that copied the tests first: against the
committed helper 265 tests ran and 6 failed (the new tests); against the new helper all 265 pass. The whole suite,
`python3 -B -W error tests/run_all.py`: 6,590 tests in 14 roots, OK. `wb verify packages/workbench` prints no refusal; `wb check` and
`wb run code-work check` report no problems. `wb preview release-approvals` after the owner's release: 14 records `recorded`; four stale
shipped records are warned about (`2cff7146…`, `ec712287…`, `f50d8904…` and `f877b2db…`).

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied (spec only): the header names the digit guard and the
reading of `format` first. Deferred to the pass of increment E, which changes the helper anyway: the docstring of
`test_askollama_sections.py` still says "increment C" and "items 12 to 14", and the digit-run regex literal appears twice in the
helper (the reply parser and the file reader), which a shared constant would keep in step. Noted: two of the digit cases (a number
`"x": 99…9` of 4,301 digits) are refused as "not strict JSON" even without the guard, because the interpreter's own limit raises;
the in-string case and the case with the limit lifted are the ones that discriminate. A security review was not asked for: no new
boundary, and the alias and digit rules only refuse more.

**Releases:** one more of `wb release-approvals` by the owner in this increment (in a terminal).

**Not done in D:** the size rule, the `models` argument (E and F); the stale shipped records stay out of the commit until I.

**Open for the owner:** whether to record the alias rule in a decision as well.

### Increment E

**Done:** `ask` refuses a prompt before sending it when its size in bytes of UTF-8 is greater than the window of the call times the
section's `bytes_per_token` (2 when absent). The result is the contract's failure object `vendor_error` / `context_overflow`, not
retryable, with the message "the prompt is probably larger than the window", exit 1, no part of the prompt in it and nothing sent.
The rule runs after the options, the model and the schema are validated, and `embed` is not subject to it. The new file
`test_askollama_size.py` tests the bound (exactly window times the figure sent, one byte more refused, for the figures 1, 2 and 8),
the window of the call (`--context`, `default_context`, `context`), a figure and a window for each model, bytes against characters,
the object and the absence of the prompt in it, the order after validation and after the schema, the largest prompt, the blank
prompt, the `embed` exemption and the check of the server's count for a prompt the rule lets through. Four older tests were adjusted
because the rule now refuses what they sent (a larger window for the two tests of the largest prompt, a shorter prompt and a larger
figure for the window-of-one test, a shorter prompt for the `--context 1` case); they test what they said before. The spec's header
says the size rule is built, says that the rule is a backstop and not a substitute for a caller that sizes its own input, and
records a caller's measurement of bytes per token in "Known limits" as reported by the knowledge-base module's session, a small
sample not repeated here (2.9 to 4.6, median 4.0, with the tokenizers of `phi4` and `gpt-oss:20b`).

**Verification as run** (Python 3.15.0, macOS): the module's tests in a scripted pass that copied the tests first: against the
committed helper 278 tests ran and 7 failed (the new size tests that need the rule); against the new helper all 278 pass. The whole
suite, `python3 -B -W error tests/run_all.py`: 6,603 tests in 14 roots, OK. `wb verify packages/workbench` prints no refusal; `wb check`
and `wb run code-work check` report no problems. `wb preview release-approvals` after the owner's release: 14 records `recorded`
and six stale shipped records (`24a7ae0d…`, `2cff7146…`, `aa4dc1b6…`, `ec712287…`, `f50d8904…`, `f877b2db…`).

**Review:** one read by the read-only `reviewer`: no blocking finding; it checked the helper against the decision and the spec, found
no vacuous test, read each adjusted older test, and found that the bound computed from the decoded text equals the bytes read (strict
UTF-8, no normalisation, a byte order mark stays three bytes). Applied (spec only): the sentence that a figure of 1 "never passes a
prompt that the window would cut" was too strong (the chat template adds tokens and the reply shares the window), and now says so.
Deferred to the pass of increment F-C: a clause on the size rule in the helper's module docstring. A security review was not asked
for: the rule only refuses more and adds no input, no file and no request field.

**Releases:** one more of `wb release-approvals` by the owner in this increment (in a terminal); the owner re-approved the plan
twice before it, for the extension of the plan and for the deferred items from the knowledge-base module's review.

**Not done in E:** the `models` argument (F), the defaults and the confirmation of `text-embedding` (F-A to F-C); the stale shipped
records stay out of the commit until increment I.

**Open for the owner:** nothing new.
