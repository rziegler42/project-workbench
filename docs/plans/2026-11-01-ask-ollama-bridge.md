# A bridge for a local Ollama server, and an embedding command

Status: Proposed
Created: 2026-11-01
Candidate: workbench-v1#ask-ollama-bridge
Specs: model-bridge, module-contract, terms

## Goal

A first-party module `ask-ollama` that lets an engine or a library call a model on an Ollama server through the same contract as
`ask-codex`, so that the two bridges can replace one another, and that lets a library embed texts through a second command. When the
plan is done:

- `wb run --provides model-bridge ask-ollama ask` answers one prompt with one contract version 2 object, with the seven options of the
  contract accepted as the accepted decision `2026-11-01-bridge-contract-version-2` sets them: `--server` selects a record of the
  owner's endpoint file, `--schema` becomes the server's structured output, `--confine` is met by construction, `--root` is ignored,
  and `--effort` is mapped to the server's thinking setting.
- The server's address is never an argument, an environment variable or a tracked file. It is a named record in an owner-only file
  in the guarded store, validated by the rules of guarantee 7 of `model-bridge.md`, and the bridge reaches only the host and port
  that record names.
- A prompt that does not fit the context window, a reply that is cut off, and a reasoning model that returns nothing are each an
  error and never a success.
- A second command takes a batch of texts and returns the model name, the dimension and the vectors, under a capability of its own.
- The first run against a real server is made by the owner and recorded.

## Scope

- A decision record for where the endpoint records live and how a bridge reads them (increment A), which the owner accepts.
- A spec for the bridge, `docs/specs/ask-ollama.md` (increment B): the endpoint file, the mapping of every option, the request and
  the reply, the errors, the bounds, the rules for context, truncation and thinking, the embedding contract and the read-only
  `check` command; and an amendment of the declaration rule of `model-bridge.md` (see the assumptions).
- The module `packages/workbench/ask-ollama/`: its declaration, its helper, its tests against a fake server that the tests start
  on the loopback address, and its entry in `packages/workbench/package.json` (increments C to E).
- The lists and documents that name the first-party modules or the capabilities, so that a new module is not missed (increment G).
- The owner's run against a real server, recorded in the spec (increment F).

## Non-goals

- Authenticated endpoints, and any credential in the store. The agent can read the store (the harness denies it writes, not reads), so
  a credential there would not be protected from it. A record that says `authenticated: true` is refused as not supported yet. A
  credential needs a decision of its own.
- A command or a skill that writes the endpoint file. The owner writes it by hand in this plan.
- Installing, pulling, listing or starting a model, and choosing a model, retrying or falling back to another bridge.
- Routing between model machines, quotas and the library's registry: they belong to the knowledge base.
- Making the review engine work through this bridge. That engine relies on the vendor program opening the document from its working
  directory; this bridge reads no files. Sending the document in the prompt is separate work.
- Streaming replies, and any use of a server's tool or function features.
- A change to the kit or the launcher.

## Assumptions and constraints

- The accepted decision `2026-11-01-bridge-contract-version-2` binds this plan and is not reopened. It set the seven options, the
  class `vendor_unreachable`, the five token counts, the network guarantee (guarantee 7 of `model-bridge.md`) and the endpoint
  constraints (a safe name, `http` or `https` only, no credential in the address, a location class the owner declares, `https` for an
  authenticated endpoint except on a literal loopback address, a refusal for a record that breaks these). It left to this plan: the
  exact format and place of the record, the mapping of `--effort`, and the embedding contract.
- **A helper reads the store by path.** The kit has no store accessor, and the review engine already reads its own key from the store
  by a fixed path through the kit's no-follow layer (`review-engine.md`). This bridge does the same for the endpoint file. No
  launcher or kit change is needed. Increment A states this as a decision for the owner to accept, with the alternatives.
- **The agent can read the store.** The harness denies it writes there, not reads. So the file holds no credential. The module
  declares `ask_reads` for the endpoint file, so that a harness which provides `permissions` asks before the agent reads it, as
  `ask-codex` does for its login file.
- **The Ollama API is described from memory and is confirmed only by the owner's run (increment F).** The plan uses `POST /api/chat`
  with `stream` false for a prompt, its `format` field for structured output, its `think` field and `options.num_ctx` for thinking
  and context, its `prompt_eval_count`, `eval_count` and `done_reason` fields for the counts and the end of the reply, and
  `POST /api/embed` for a batch of texts. The spec marks each of these as unconfirmed until increment F. A difference found there is
  corrected in increment F.
- The helper imports the standard library and `wbkit` only, and uses `http.client` with a connection to the record's host and port
  and no redirect handling, so that a redirect is never followed, and `ssl` with a default context for `https`.
- The HTTPS tests need certificates. They are made once with the system's `openssl`, as throwaway keys valid for a hundred years
  (a certificate for `127.0.0.1` and `localhost`, and one for another name), plus one otherwise trusted certificate that has already
  expired (made with the `ca` command's start and end dates, which can be set in the past), and kept in the module's tests folder.
  They guard nothing; the spec and the Result say so, so that no one mistakes them for secrets. If the system's `openssl` cannot
  make an expired certificate, the test for expiry raises the library's certificate-verification error with the reason
  "certificate has expired" from inside the connection, and the Result says that the expired case was shown that way.
- The tests start a fake server on the loopback address inside the test process. No test reaches another host. No test starts a real
  Ollama or touches the owner's network.
- **Package edits and the gate.** Editing any file under `packages/workbench/` makes the shipped approval of the package stale, and
  until the owner releases the approvals the harness hooks refuse every edit and command. The earlier plan handled this with scripted
  passes (one command that writes all the edits of a pass and runs the tests, with the owner's word) and a release by the owner after
  each. This plan does the same for increments C, D and E, and the owner's releases are counted in each Result. A new module also
  changes the package record and adds module records.
- An agent runs no call to a real server unless the owner says so. The owner's own terminal could not start `codex` and the shell
  that the owner's session offers has no network (Increment D of the earlier plan); whether either can reach the owner's Ollama
  server is not known and is part of increment F.
- **The declaration rule of `model-bridge.md` needs an amendment.** Today it says a bridge provides only `model-bridge`, ships one
  helper, and has one command with the argument `ask`. This plan puts the embedding command in the same module, under a further
  capability, and adds a read-only `check` argument, so increment B amends the rule: a bridge module may also provide a further
  capability through a further command, and its `ask` command may be joined by a read-only `check` that makes no connection; consent
  to send content to the vendor, which installing the bridge is, covers the further command. The alternative is a separate module
  for embeddings, which would copy the endpoint-reading code (a helper cannot import another module's) and double the surface that
  must be kept consistent. The plan chooses the amendment; the owner may choose the separate module at approval.
- Hard-coded lists of the modules exist in tests of other modules and in a self-hosting fixture (found by a search for `ask-codex` and
  `freecad`). Increment C finds and updates them.

## Completion criteria

1. The owner has accepted a decision for the endpoint records, and `docs/specs/ask-ollama.md` states the endpoint file, every option,
   the request and the reply mapping, the errors, the bounds and the embedding contract.
2. `packages/workbench/ask-ollama/` exists, is listed in the package, passes `wb verify`, and its tests pass against a fake server
   on the loopback address.
3. `ask-ollama ask` prints a contract version 2 object for every case of the conformance checklist that applies to a bridge to a
   server, including items 17 and 19 of `model-bridge.md`: a record that is missing, unreadable, outside the rules or names another
   scheme is refused with nothing sent; a redirect is not followed; no address or credential is in the object, the message or the
   arguments; an `authenticated` record is refused; a server that does not answer ends at the timeout as `vendor_unreachable`; and
   an `https` server whose certificate is not trusted, has expired or is made for another host is refused as `vendor_unreachable`,
   with no way to turn verification off.
   `ask-ollama check` reads the endpoint file, opens no connection, prints for each record its name, scheme, location class and
   whether it is authenticated and the default, with no host or port, and prints a warning for an unauthenticated `http` record away
   from a literal loopback address, saying that content to it is sent in the clear.
4. A prompt over the context window, a reply cut off by the server's length limit, and an empty reply from a reasoning model are
   each an error with a detail code, and none is a success.
5. `--server`, `--schema`, `--effort`, `--root`, `--confine`, `--model` and `--timeout` behave as the spec says, and the same
   arguments that work for `ask-codex` work for `ask-ollama`, apart from a vendor-specific refusal the spec names.
6. The embedding command returns the model, the dimension and the vectors for a batch, refuses a batch over its bound, and is
   provided under a capability of its own that is named in `terms.md` and `module-contract.md`; `model-bridge.md` says how a bridge
   module may declare a further capability and the `check` argument.
7. The owner has run the bridge against a real server, with a model and an embedding model of the owner's choice, and the result is
   recorded in the spec with the server's version and the date.
8. The whole suite, `wb check`, the plan check and `wb verify` pass, and the shipped approvals are current.

## Increments

### Increment A — Decide where the endpoint records live and how a bridge reads them

**Outcome:** a decision record in `docs/decisions/`, `Proposed`, that states the endpoint file and the way a bridge reads it, and that
the owner can accept. Nothing is built.
**Dependencies:** none.
**Affected areas:** a new file `docs/decisions/2026-11-01-endpoint-records-in-the-store.md` only.
**Steps:**
1. Read `docs/decisions/README.md`, `2026-10-20-fixed-store-location`, `2026-11-01-bridge-contract-version-2` and `review-engine.md`
   (how it reads its key from the store).
2. Write the record from the template of the `draft-decision` skill. It decides: the file is `endpoints.json` directly in the guarded
   store (`~/.config/project-workbench/`, the fixed location), strict JSON, at most 64 KB, format 1, with `endpoints`, an object of
   named records, and an optional `default` naming one of them; a record holds `scheme` (`http` or `https`), `host`, `port` (1 to
   65535, a JSON number and not a string or a boolean), `location` (`this-machine`, `owner-network` or `vendor-cloud`),
   `authenticated` (a boolean, which must be `false` in this plan), a `host` of one of three forms and no other, with the grammar
   written in the decision: a DNS name of at most 253 ASCII characters in lower case, in labels of 1 to 63 letters, digits and
   hyphens that neither start nor end with a hyphen, with no trailing dot and no underscore; an IPv4 literal of four decimal numbers
   from 0 to 255 without leading zeros; or an IPv6 literal written without brackets and without a zone, which the standard
   library's address parser accepts (the bridge adds brackets itself where a `Host` header needs them). A host with a delimiter
   (`@`, `:` outside an IPv6 literal, `/`, `?`, `#`, `\`, a bracket), whitespace, a control or non-ASCII character, upper case,
   an empty label, a numeric form other than the dotted decimal one, or a zone identifier is refused. Loopback means an IP
   literal that the address parser calls loopback (`127.0.0.0/8` and `::1`); the name `localhost` is not treated as loopback,
   because a name is resolved by the machine, and optionally `default_model`, `embedding_model` and `context` (a positive whole number of tokens); a record holds no
   credential, no path and no URL; the bridge reads the file by its fixed path through the kit's no-follow layer, refuses a link, a
   file that is not a regular file, a file over the bound and a file that is not strict JSON of this format, and reads it again on
   every call; the owner writes the file by hand and the agent cannot write the store; and the module declares `ask_reads` for it.
3. Write the alternatives and why they are rejected: a kit accessor for the store (a kit change and a version number for one
   module); the launcher passing the record to the helper (a new declaration field, a launcher change and several specs); an
   environment variable or an option for the address (rejected by `2026-10-20-fixed-store-location`); a record in the project (a
   tracked address, rejected by the same decision); and a credential in the file (the agent can read the store, so it is not
   protected).
4. Write the consequences, the bad ones too: the helper reads the store by a hand-coded path as the review engine does, which is a
   precedent and not a sanctioned accessor; the owner edits a file by hand; the agent can read the addresses, which is why `ask_reads`
   is declared; authenticated endpoints wait for a later decision. State the evidence with a provenance line.
5. Set the status `Proposed` and stop. Accepting is the owner's act, at the level `wb settings` prints for `accept-decision`.
**Verification:** `wb run code-work check` and `wb check` report no problems; the record cites no path to an untracked file; the
status is `Proposed`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#A`. The plan then waits for the owner's
acceptance of the record before increment B begins.

### Increment B — Write the spec of the bridge

**Outcome:** `docs/specs/ask-ollama.md`, `Draft`, states the bridge in enough detail to build and to test it, including the embedding
contract, and marks every statement about the Ollama API that only the owner's run can confirm.
**Dependencies:** A, accepted by the owner.
**Affected areas:** a new file `docs/specs/ask-ollama.md`; `docs/specs/model-bridge.md`, which is amended so that it describes both
kinds of bridge consistently: its purpose and non-goals (a bridge translates to a vendor's program or to its server), the
declaration rule and checklist item 1 (a bridge module may also provide a further capability through a further command, and may
have a read-only `check` argument that makes no connection), the guarantees (1 to 4 and 8 scoped to a bridge to a program, with
the ones that apply to a bridge to a server named: bounds, a timeout that ends the call, the network guarantee 7, and output as
data), the endpoint-record and authentication rules (a bridge may decline an authenticated record until a credential has a decision,
by refusing it before anything is sent, and the rule then says what the bridge does with the credential when it supports one), and
the conformance checklist (the items that apply to a program are scoped to it, and the server items stand beside them).
**Steps:**
1. Copy the template of the `draft-spec` skill. State the module and its commands (`ask-ollama` with `ask` and `check`, and an
   embedding command), the endpoint file as the accepted decision sets it, the grammar of every field of a record including the
   host (the forms that are accepted, their length limits, and every form that is refused), and how a record is validated, with
   each refusal.
2. Map the options: `--model` (the record's `default_model` when absent, and a refusal when neither names a model, because a
   server has no default), `--effort` (the mapping to the server's `think` setting, and what a model that does not support it
   produces), `--timeout`, `--root` (validated and ignored), `--schema` (read as `ask-codex` reads it, and passed as the server's
   `format`), `--server` (the record, or the `default`), and `--confine` (accepted, nothing to switch off).
3. Map the reply: the text, the model name (the server's, when it reports one), the five counts (the server's prompt and
   generation counts for input and output, and `null` for the counts it does not report), and the end of the reply.
4. Define the errors: `vendor_unreachable` (refused connection, no answer, a reset, a name that does not resolve; retryable), `timeout`,
   `model_unavailable` (the server does not have the model), `effort_unsupported`, `not_signed_in` (never produced, because no
   endpoint is authenticated), and `vendor_error` with details `unusable_reply` (empty or not one JSON object with a schema),
   `reply_too_large`, `bad_schema`, `bad_exit` (any other status) and two new codes, `context_overflow` (the prompt does not fit the
   window) and `reply_cut` (the server stopped at its length limit).
5. State the bounds: the request, the reply (262,144 bytes), the whole response body read (a fixed bound), the schema file (65,536
   bytes), the object (2,000,000 bytes), and the connection and total timeouts. State the rules for the context window (the record's
   `context`, passed as `num_ctx`, and the check against the server's prompt count), for truncation (`done_reason`), and for a
   thinking model (an empty reply is `unusable_reply`; the thinking text is never returned as the reply).
6. Define the embedding contract: the capability name (proposed here: `text-embedding`; the name is the owner's to confirm, as
   `model-bridge` still is), the command `embed-ollama embed`, its options (`--model`, `--server`, `--timeout`), the input (one JSON
   object on standard input with `texts`, a list of at most 100 strings, each at most 32,768 bytes and the whole input at most
   262,144 bytes), and the output (`contract` 1, `ok`, `vendor`, `model`, `dimension`, `vectors`, `usage`), with the same failure
   object and classes. State that vectors are numbers as the server returns them, that the dimension must equal the length of
   every vector, that a batch whose object would pass 2,000,000 bytes is refused as `reply_too_large`, and that a model that is not
   an embedding model produces an error and never a wrong shape.
7. Define `check`: it reads the endpoint file by the same rules, makes no connection and writes nothing, and prints one line per
   record with the name, the scheme, the location class, whether it is authenticated and whether it is the default, never the host or
   the port, and a warning line for an unauthenticated `http` record away from a literal loopback address that says content sent to
   it travels in the clear. It prints a refusal for a file that breaks the rules. The per-call object is never changed by this: the
   contract allows one object, so the warning belongs to `check` and not to `ask`. Say what the owner or an agent runs it for.
8. Define the transport. A connection is made to the record's host and port only. For `https` the bridge verifies the server: it
   builds its context in one function with the system's trusted certificates, hostname checking on and a protocol of TLS 1.2 or
   later, sends the record's host as the server name, and treats a certificate that is not trusted, has expired or does not match
   the host as `vendor_unreachable` with the message "the server's certificate was not accepted", not retryable. No option, variable
   or file turns verification off or adds a trusted certificate; the context function is the one place the tests replace. For
   `http` nothing is verified and `check` warns where the rules say.
9. Correct item 19 of the checklist of `model-bridge.md` in the same pass: the server necessarily sees the connection's destination
   and the `Host` header, which come only from the selected validated record, so the item says that a credential, a host or a port
   is absent from the object, the message, any diagnostic and the arguments of the bridge's process, and that nothing of the
   record beyond the destination is sent to the server. Write the conformance checklist: every item of `model-bridge.md` that
   applies, items 17 and 19, the embedding items, the
   transport items (an untrusted certificate refused, a certificate for another host refused, a trusted matching certificate
   accepted, and no way to turn verification off) and the `check` items (the warning for the plain `http` record, no host or port
   in its output, no connection made).
10. Mark each statement about the server's API as "unconfirmed until the owner's run" and list them in one place. Set the status
    `Draft`: the owner approves a spec.
**Verification:** `wb run code-work check` and `wb check` report no problems; every option and every error class of the contract is
covered by a statement; the unconfirmed statements are listed in one place; the spec cites no path to an untracked file.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#B`.

### Increment C — The module, the endpoint file and a prompt with structured output

**Outcome:** `packages/workbench/ask-ollama/` exists and `ask-ollama ask` answers a prompt against a fake server, with all seven
options, the endpoint file rules, the error mapping and the contract version 2 object.
**Dependencies:** B.
**Affected areas:** the new `packages/workbench/ask-ollama/` (declaration, helper, tests), `packages/workbench/package.json`, the
tests and fixtures that hard-code the module list, `docs/specs/ask-ollama.md` (statements the build corrects).
**Steps:**
1. Find every place that lists the first-party modules: a search for `freecad` and `ask-codex` outside `docs/plans/`, `docs/decisions/`
   and `.workbench/`, including the install-order lists in the tests of `claude`, `code-work` and `groundwork`, and the
   self-hosting fixture. Decide for each whether the new module belongs.
2. Write the tests first, against a fake server that the tests start on the loopback address and that records the request line,
   the headers and the body: the options and the record rules of the spec; a missing, unreadable, linked, oversize, non-JSON or
   mis-shaped endpoint file refused with nothing sent; a record with an unknown field, a bad scheme, an `authenticated` record, a
   bad port (zero, 65536, a string, a boolean, a float) or a bad name refused; and every malformed host refused without a connection
   and without the value in the output: an empty host, one over 253 characters or with a label over 63, upper case, a trailing
   dot, an underscore, an `@`, a `:` outside an IPv6 literal, a `/`, `?`, `#`, `\`, a bracket, whitespace, a newline, a NUL and
   other control characters, a non-ASCII character, an IPv4 form with leading zeros or fewer or more than four parts or a part over
   255, a hexadecimal or octal or single-number form, an IPv6 literal with a zone or with brackets, and a URL in the host field;
   and the accepted forms accepted (a name, an IPv4 literal, an IPv6 literal); the request the fake receives (path, method, body fields, and that no
   other header or field carries the prompt or the record); a redirect not followed; a reset, a refusal and a hang ended at the
   timeout as `vendor_unreachable` and `timeout`; verified HTTPS against a fake server that the tests start with a throwaway
   certificate (a certificate that is not trusted, one that is trusted but made for another host, one that is trusted and has
   expired, and one that is trusted and matches, the trust given by replacing the helper's one context function inside the test and
   by nothing the helper reads from its environment or its files), each of the three refusals mapped as the spec says, as a
   non-retryable `vendor_unreachable` with the fixed message and no host, port or certificate detail in the object; the five counts; the error mapping from status codes and bodies; a reply over
   the bound; a schema passed as the server's format and a non-object reply refused; the destination of the connection and the
   `Host` header taken only from the selected validated record, which the server necessarily sees, and nothing else of the record
   (the location class, the default, other records) in the request line, the headers or the body; no host, port or credential in
   any result object, message or diagnostic, or in the arguments of the bridge's own process; the project and the store unchanged
   after every call.
3. Write the declaration (`type module`, `provides ["model-bridge"]`, one helper, the command `ask-ollama` with `arguments ["ask",
   "check"]`, `runtime python`, `kit 1`, and `ask_reads` for the endpoint file), the helper, and the entry in the package list.
   Tests for `check` come first as well: one line per record with the name, scheme, location class, authentication and default and
   never the host or port; the warning for an unauthenticated `http` record on a name that is not a literal loopback address, and
   none for `https` or for a loopback address (`127.0.0.1`, `::1`); no connection made (the fake server sees nothing); a refusal for
   a file that breaks the rules; nothing written.
4. Update the lists found in step 1 and the spec where the build shows it to be wrong.
5. Ask the owner whether to run a security review of this module. It opens a network connection and reads an owner file, so the
   policy asks; the review runs only when the owner asks. Record the answer.
**Verification:** the module's test root passes; the tests are seen to fail before the helper exists; `wb verify packages/workbench`
reports no problem; the whole suite passes; the argument list and object of every case of the checklist are compared with the spec.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#C`, after the owner's releases that the
package edits require.

### Increment D — The context window, truncation and thinking

**Outcome:** a prompt that does not fit, a reply that is cut off, and a reasoning model that returns nothing are each reported as
the spec says, and `--effort` is mapped to the server's thinking setting.
**Dependencies:** C.
**Affected areas:** `packages/workbench/ask-ollama/` (helper and tests), `docs/specs/ask-ollama.md`.
**Steps:**
1. Write the tests first, against the fake server: the record's `context` passed as the window and a prompt whose server count
   reaches it reported as `context_overflow` with nothing returned; `done_reason` at the length limit reported as `reply_cut`; an
   empty reply with thinking text reported as `unusable_reply`, with the thinking text in no object; `--effort low`, `medium` and
   `high` sent as the spec says, an `--effort` the server rejects reported as `effort_unsupported`, and no `--effort` leaving the
   setting out; a record with no `context` leaving the server's window and doing no overflow check, with the spec saying so.
2. Implement them in the helper and correct the spec where the build disagrees.
**Verification:** the module's test root passes; the new tests are seen to fail before the change; the whole suite passes;
`wb verify packages/workbench` reports no problem.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#D`, after the owner's releases.

### Increment E — The embedding command

**Outcome:** `embed-ollama embed` returns the model, the dimension and the vectors for a batch of texts, under its own capability.
**Dependencies:** D.
**Affected areas:** `packages/workbench/ask-ollama/` (declaration, helper and tests), `docs/specs/ask-ollama.md`,
`docs/specs/terms.md` and `docs/specs/module-contract.md` where they list capabilities, and the tests that check capability names.
**Steps:**
1. Write the tests first, against the fake server: a batch of texts sent as the spec says and the vectors returned with the
   model and the dimension; every vector the length of the dimension; a batch of 101 texts, a text over its bound, an input over
   its bound, an empty list and input that is not one object with `texts` refused with nothing sent; a vector of the wrong length,
   a non-number, a non-finite number, a missing vector and a different count of vectors refused as `unusable_reply`; a batch whose
   object would pass 2,000,000 bytes refused as `reply_too_large`; the same record, timeout and error rules as `ask`.
2. Add the second command to the declaration with the new capability, implement it, and add the capability name to `terms.md` and
   `module-contract.md` with the note that its name is the owner's to confirm.
3. Check what verifies capability names: a capability without a prefix is accepted only from the first-party package; make sure
   `wb verify` accepts the new name from this module and refuses it from another.
**Verification:** the module's test root passes; the new tests are seen to fail before the change; the whole suite passes;
`wb verify packages/workbench` reports no problem.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#E`, after the owner's releases.

### Increment F — The first run against a real server

**Outcome:** the owner has run the bridge against a real Ollama server and the result is in the spec; the statements about the
server's API are confirmed or corrected.
**Dependencies:** E.
**Affected areas:** `docs/specs/ask-ollama.md`; the helper and its tests if the run shows the API to differ.
**Steps:**
1. Give the owner the exact steps: the endpoint file to write (with a placeholder host in the document, never the real address),
   how to update the installed helper (`wb upgrade`), and the commands for each case, from a terminal where the bridge can reach the
   server. If the owner's terminal cannot run it, say so and agree another route with the owner (the earlier plan's run was made
   through the agent's shell tool, with the owner's word).
2. The cases: a plain prompt; a prompt with `--schema`; a prompt larger than the window; a reasoning model with and without
   `--effort`; a model the server does not have; a server that is switched off; an embedding batch of 2 and of 100; an embedding
   with a chat model. A reply cut at the server's length limit cannot be caused reliably, because the contract has no output
   limit option: the deterministic fake-server test of increments C and D is the required proof of that handling, and the real
   run records it only if the owner has a model whose own configuration sets a small output limit. Record, without the host, the
   server's version, the models, the date, and each result.
3. Correct the spec and the helper wherever the server differs from the unconfirmed statements, with a test that fails before the
   correction. A correction to the helper is a package edit and follows the same releases.
4. Move every confirmed statement out of the unconfirmed list.
**Verification:** the recorded run names a server version and a date and holds no address; the whole suite and the checks pass after
any correction.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#F`.

### Increment G — Close out, documents and approvals

**Outcome:** the plan's result is written, the documents that name the modules agree, the suite passes, and the shipped approvals are
current.
**Dependencies:** A to F.
**Affected areas:** this plan's Result; `docs/development.md`; `docs/specs/model-bridge.md` ("As built"); the shipped approvals.
**Steps:**
1. Add the bridge, its `check` and the embedding command to `docs/development.md` (the command rows and a section), and to "As
   built, and its limits" in `model-bridge.md`, with what was run and where.
2. Run the whole suite, `wb check`, the plan check and `wb verify` on the package, and read each result.
3. The owner releases the approvals if the package changed since the last release. List the stale shipped records, and remove them
   through the commit helper only after the owner approves the exact list.
4. Write the result of every increment under `## Result` with the verification as run, the releases counted, and what is open.
**Verification:** the full suite reports no failure; `wb check`, `wb run code-work check` and `wb verify` report no problem; the
preview of the release reads `recorded` for the package and every module.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#G`.

### Increment H — Record the upgrade

**Outcome:** the installed copies of the helpers in this repository match the package, and the manifest records them.
**Dependencies:** G.
**Affected areas:** `.workbench/manifest.json` and the installed helper copies under `.workbench/workbench/` that the owner's upgrade
changed (the new module and any engine whose helper changed).
**Steps:**
1. The owner acknowledges the changes under `.workbench/` (the review state of the reviews run in this plan) and runs the upgrade.
2. Read what changed and check that each installed helper is byte for byte the helper in the package.
**Verification:** `wb check` reports no problem; the installed helper of each changed module has the same hash as the helper in
`packages/workbench/`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-01-ask-ollama-bridge#H`.

## Verification for the plan as a whole

- The whole suite, `python3 -B -W error tests/run_all.py`, with the count of tests recorded.
- `wb check`, `wb run code-work check` and `wb verify packages/workbench`.
- A call of each of the two commands through `wb run --provides` against the fake server, showing that the capability finds the
  module and that the object passes the review engine's and the action review engine's reading of a bridge object (both accept
  contract version 2).
- The owner's run against a real server, recorded in the spec.

## Risks and sensitive actions

- **A network boundary.** The bridge opens a connection to an address from a file. The rules are: only the host and port the record
  names, no redirect followed, a hard timeout, bounded reads, `http` or `https` only, and no address in any output. The tests check
  each against a fake server. Increment C asks the owner whether to run a security review.
- **An owner file the agent can read.** The endpoint file holds addresses and no credential, and `ask_reads` makes the harness ask
  before the agent reads it. The agent cannot write the store. This is not a boundary: a shell command can read the file.
- **The location class is the owner's word.** The bridge does not verify where a host is, so a record that names a remote host sends
  the text there. The spec and the decision say so.
- **A model's reply is untrusted.** It is returned only as a string, never run or used as a path, as `ask-codex` does. The thinking
  text is never returned as the reply.
- **Unconfirmed API details.** The plan is written from memory of the Ollama API. A wrong field name would fail closed in the
  tests against the fake server and be found in increment F, not before. The spec lists every such statement.
- **The gate and the releases.** Increments C, D, E and possibly F edit `packages/`, so each needs the owner's releases between the
  scripted passes, as in the earlier plan (six releases for two increments there). A scripted pass needs the owner's word.
- **A real server needs the owner.** Increment F needs a server, a model and an embedding model that the owner chooses, and a place
  from which the bridge can reach it. If none exists the plan stops at E and F is left open.
- **The set of lists.** A module list in a test or a fixture that is missed would fail the suite; increment C finds them with a
  search and the suite shows any that remain.
- **Hard stops:** none identified.

## Review record

Reviewed by Codex (`gpt-5.6-terra`) through the review engine on 2026-11-01, at the owner's request; five rounds, the bound raised
from 3 to 4 and then to 5 (the ceiling) by the owner. Outcome: not converged. The fifth round's finding was applied afterwards and
not reviewed again.

- R1-F1 (major, rejected): the plan lacks a `## Result` section. It ends with that heading, and the plan check passes; the only
  other occurrence of the text is an inline mention in a step.
- R1-F2 (major, applied): the embedding command conflicted with the declaration rule of the bridge spec. Increment B amends the
  rule, and a separate module is named as the alternative for the owner to choose.
- R1-F3 (major, applied): no warning for an unauthenticated `http` endpoint away from loopback. A read-only `check` command prints
  it and never prints a host or port.
- R1-F4 (major, applied): the close-out increment had two commits. Recording the upgrade is its own increment, H.
- R2-F1 (major, applied): the amendment of the bridge spec was too narrow. Increment B amends its purpose, guarantees,
  authentication rule and checklist for both kinds of bridge.
- R2-F2 (major, applied): no verified HTTPS. The transport is specified and tested with throwaway certificates.
- R3-F1 (major, applied): the test that no host or port reaches the server could not hold, because a request carries the `Host`
  header. The test and the spec checklist item now say that only the selected validated record decides the destination.
- R3-F2 (major, applied): a cut reply cannot be caused reliably on a real server. The fake-server tests are the required proof.
- R4-F1 (major, applied): the grammar of the `host` field was unspecified. The decision, the spec and the tests fix it.
- R5-F1 (major, applied): no test used an expired certificate. A fixture and a fallback were added.

Left for the owner: whether the embedding command stays in this module or becomes a separate one, and whether throwaway private
keys for the HTTPS tests may be kept in the repository. The review is not an approval.

## Deferred work

- Authenticated endpoints and a place for a credential that the agent cannot read.
- An owner-run command that writes and checks the endpoint file, and a read-only listing of the records without their addresses.
- Sending the document in the prompt so that the review engine can use this bridge as a reviewer.
- The knowledge base's own doctor, which may call `ask-ollama check` for the warning about a plain `http` endpoint away from
  loopback; the warning itself is in `check`, in this plan.
- Streaming, tools and any other feature of the server beyond a prompt, structured output, thinking and embeddings.
- A decision whether `action-review` should pass `--confine` (carried over from the earlier plan).

## Result

### Increment A

**Done:** `docs/decisions/2026-11-01-endpoint-records-in-the-store.md`, `Proposed`. It decides: one file `endpoints.json` directly in
the guarded store, for the whole account and written by the owner by hand; strict JSON of format 1, at most 65,536 bytes and 64
records, with an optional `default`; a record of exactly `scheme`, `host`, `port`, `location`, `authenticated` (which must be `false`
for now) and optionally `default_model`, `embedding_model` and `context`; a closed grammar for `host` (an IPv4 literal, an IPv6
literal or a lower-case DNS name whose last label is not a number), with the addresses a server is never at refused; loopback
written out and independent of the library's version; the bridge reads the file by a fixed path through the kit's no-follow layer,
as the review engine reads its key, and refuses the whole file for any bad record; the module declares `ask_reads` for it; a
call without `--server` uses `default`. Alternatives (a kit accessor, the launcher passing the record, a variable or an option, a
tracked record, a per-project record, a credential in the file, skipping a bad record, trusting the library) are rejected with
reasons, and the bad consequences are listed, among them that a namespaced model can be named only by the record and not by
`--model`.

**Verification as run:** `wb run code-work check` (77 plans) and `wb check` report no problems after the last edit. No code was
run for the decision. Two short measurements with Python 3.15.0 on macOS (scripts not kept) are in its Evidence: how the standard
library and the system resolver read numeric host forms, and how the library classifies special addresses.

**Review:** two rounds by the read-only `reviewer` agent.
- Round 1 found one blocking problem and nine smaller ones. The blocking one: the DNS-name form admitted strings such as `127.1`,
  `2130706433`, `0177.0.0.1` and `0x7f.1`, which the resolver reads as `127.0.0.1` and the library refuses. Applied: a name's last
  label may not be a number, the IPv6 form and loopback are written out in words, unspecified, multicast, link-local and broadcast
  addresses are refused, numbers are integers, the missing-file and unknown-name refusals are listed, the sentence on a bad record
  is rewritten, the https-unless-loopback rule is carried forward, citations are corrected, and the Evidence has the versions.
- Round 2 (on the rewrite) found no blocking problem and five wording or grammar gaps. Applied: `0x` followed by zero or more digits;
  any spelling of the IPv6 address 1 is loopback; the IPv6 form no longer defers to the library; `0.0.0.0/8` and `240.0.0.0/4` are
  refused; a `default` that names no record is named in the refusals; the home of the diagnostic is stated; the `settings` claim and
  the `ask_reads` source are cited. I measured the forms involved before editing (the resolver read `0`, `00` and `0x0` as `0.0.0.0`,
  and refused a bare `0x`). The rewrite after round 2 has not been read by the reviewer again.

**Not done:** the owner's acceptance. The record is `Proposed`, and Increment B waits for it. The accept level of `accept-decision`
that `wb settings` prints is `ask`.

**Open for the owner:** whether to accept the record; the narrowing of the contract decision (no authenticated record yet); and the
question of widening the contract's `--model` charset (64 characters, no `/`), which the record lists as open.

**Afterwards, the decision was reviewed by Codex** (`review-adr`, one round, converged, one minor finding on provenance, applied)
and **accepted by the owner** at the level `ask` (`wb run groundwork preview`, then `accept` with the digest it printed). The
accepted record is committed in its own commit, `c69b0f2`, after the increment's commit `51d908f`.

### Increment B

**Done:** the new spec `docs/specs/ask-ollama.md`, `Draft`, and an amendment of `docs/specs/model-bridge.md`. The new spec states:
the module and its two commands that share one helper (`ask-ollama` with `ask` and `check`, `embed-ollama` with `embed`), its
declaration and `ask_reads`; how the endpoint file is read and refused (the grammar itself stays in the accepted decision); the
mapping of the seven options; the request and the reply; the five counts; the context window, truncation and thinking rules; an
eleven-row table of errors with fixed messages, the rule for connecting versus timing out, how an error text is matched and the order
when several conditions hold; the transport, with verified HTTPS and the bounds; the exact output of `check`; the embedding
contract (input, options, request, output, failure, checks, the batch); a conformance checklist; fifteen numbered unconfirmed
statements about the server, tagged where they are used; and acceptance criteria. The amendment of `model-bridge.md` names a
bridge to a program and a bridge to a server, lets a bridge module provide a further capability through a further command and
have a read-only `check`, says which guarantees and checklist items apply to which, lets a bridge decline authenticated records,
notes that omitting `--model` is not interchangeable, and corrects checklist item 19 (the `Host` header and the destination come
only from the selected record).

**Verification as run:** `wb run code-work check` (77 plans) and `wb check` report no problems after the last edit. Measured once on
2026-11-01 (Python 3.15.0, OpenSSL 4.0.3): with `SSL_CERT_FILE` set, `get_default_verify_paths().cafile` changed and `openssl_cafile`
did not; the spec's context is built from the compile-time locations for that reason.

**Review:** one round by the read-only `reviewer` agent, no blocking finding and eleven others. Applied: the trust-store claim was
false for the obvious build (the default context honours `SSL_CERT_FILE` and `SSL_CERT_DIR`), so `tls_context()` is specified from
the compile-time locations with a test that sets both variables; a connection that is not made is `vendor_unreachable` and only a
connection that was made and then ran out of time is `timeout`; the order of the error conditions, the matching of error text and the
absent `prompt_eval_count` are stated; the retryable rule names a rejected certificate; checklist items 7, 9, 10 and 15 are adapted
for a server and item 1 names the endpoint file; the declaration table, the `--model` default and the sentence about what the bridge
reads are no longer program-only; `embed` has a `model` rule, separate failure rows, input rules and a size estimate marked
unconfirmed; the response bound is 4 MiB for `ask` because an escaped reply can reach about 1.6 MB; the request bound is counted after
escaping; the output format of `check` is exact; and more unconfirmed statements are listed and tagged inline. Noted, not changed: the
plan's step 9 and completion criterion 3 say that items 17 and 19 of `model-bridge.md` apply to this module, and item 17 (a program
bridge's refusal of `--server`) cannot; the spec scopes it out and the plan is not edited. The module's `reply_cut` refines the contract
decision's wording that a cut-off reply is `unusable_reply` (both are `vendor_error`), and the spec says so. The rewrite after the
review has not been read by the reviewer again.

**Codex review of the spec** (`review-spec` of `ask-ollama.md`, at the owner's request, `gpt-5.6-terra`): five rounds, the bound
raised from 3 to 4 and then to 5 (the ceiling) by the owner; not converged; every finding was applied and the last fix has not been
read again.
- R1-F1 (major): the request bound was below what valid inputs need (an escaped prompt and a re-written schema). It is 2,100,000
  bytes with the arithmetic, and an oversize request is refused before any connection.
- R1-F2 (major): `--model` is validated by the contract's rule, which allows `a..b` that the record rule refuses, so the fallback
  could not always fit. A name is now validated by both.
- R1-F3 (minor): the `User-Agent` had no value. It is `ask-ollama/1`, and each header's content is named.
- R2-F1 (major): the order of conditions contradicted the error-text rule for a non-object body. It is scoped: a body over its bound
  is `reply_too_large` for any status, an error status follows the status rows, and the order applies to a success status.
- R2-F2 (major): the embedding body was "exactly" three fields and also required `options.num_ctx`. It is those three plus
  `options` only when the record has `context`.
- R2-F3 (major): the embedding request named no headers. It uses those of `ask`, with the same transport and bounds.
- R3-F1 (major): `done: false` was missing from the order of conditions. It is placed after the body check and before the overflow
  and cut-reply checks.
- R4-F1 (major): the embedding command inherited the order for `ask`, which requires `done: true`, a field an embedding reply does
  not have; the round-3 fix had caused it. `embed` now has its own order: the body, the embeddings, then the size of the object.
- R5-F1 (major): the embedding `usage.input_tokens` had no validation. It follows the rule for `ask`: a whole number from 0 to
  10^12, else `null`, and a malformed count never makes a reply unusable.
Two of the five rounds found a flaw that the previous round's fix had introduced, which is why the last two fixes (the order for
`embed` and the usage rule) are the parts nobody has read after they were written.

**Not done:** the owner's approval of the spec, which stays `Draft`; no code, no module, no test. The two specs go in one commit so
that no tracked file points to an untracked one.

**Open for the owner:** the capability name `text-embedding` (proposed, as `model-bridge` still is); the bounds this spec chose (4
MiB and 16 MiB responses, 100 texts of 32 KB, a 10-second connection); whether two commands may name one helper (unconfirmed; the
fallback is one command with three arguments); and whether to have Codex read the spec before it is committed.

### Increment C

**Done:** the module `packages/workbench/ask-ollama/` (`module.json`, `helper/ask-ollama`, and tests with throwaway certificate
fixtures in `tests/certs/`) with the arguments `ask` and `check`; the module is added to `packages/workbench/package.json` and to
the install-order lists of three module tests (claude, code-work, groundwork); `docs/specs/ask-ollama.md` was amended to what was
built, with a new "Known limits" section; `docs/specs/model-bridge.md` says in four places that a bridge to a server is now built
for `ask` and `check`.

**Deviation from the plan:** the plan says two commands, `ask-ollama` and `embed-ollama`. The verifier (`workbench/declarations.py`)
refuses two commands that name the same helper, so the module has ONE command `ask-ollama` with the arguments `ask`, `check` and,
in increment E, `embed`. The spec says so. The plan is not edited, because that needs a new approval. Also, checklist item 17 of
`model-bridge.md` does not apply to this module (noted in B).

**Verification as run** (Python 3.15.0, macOS): the module's 144 tests pass; the new tests of the last pass failed against the
old helper first (2 failures and 1 error) and pass against the new one. The whole suite: `python3 -B -W error tests/run_all.py`,
6,469 tests in 14 roots, OK. `wb verify packages/workbench` accepts the modules. `wb check` and `wb run code-work check` report no
problems. No call was made to a real Ollama server; every test uses a fake server on the loopback address, with real TLS for the
https cases.

**Review:**
- The read-only `reviewer`, two reads. The first found no blocking finding; its points were applied (a reset after the answer
  began is `unusable_reply`, before it `vendor_unreachable`; `1e999` and a deep or lone-surrogate document are refused by the
  helper's own parser; the endpoint-file refusal names one of five causes; more tests). The second read, after the fixes, found no
  blocking finding and nothing broken. Applied: the four stale statements in `model-bridge.md`, and five corrections and additions
  in "Known limits". Deferred to increment D's pass, which edits the same helper and tests: the generic `OSError` branch should use
  the `responded` flag, the digit-rule test needs a truer name, and a test of exactly 32 and 33 levels of nesting.
- A security review at the owner's request (`security-reviewer`, read-only, with its own probes): no Critical or High finding; one
  Medium (a cut reply or a silently cut prompt is returned as a success, which is increment D by the plan) and six Low items.
  Applied: a deleted working directory is a refusal and not a traceback; a run of more than 4,300 digits in a server reply or a
  schema is refused before parsing. Recorded in "Known limits" and not changed: `HOME` finds the store (the accepted decision
  says so), a stuck name lookup, IPv6 ranges the decision does not refuse, a schema below `.workbench/` or a hard link (as
  `ask-codex`), the model name a server asserts, and the unbounded wait for the prompt.
- My own 747 probes (hostile options, endpoint file, server replies, environment, timing, TLS) are not independent of the code
  and are no evidence of its soundness beyond what they show. They found nothing that was not already a known limit. The proxy
  variables are not honoured, redirects are not followed, and the `SSL_CERT_*` variables do not change the trust.

**Releases:** four of `wb release-approvals` by the owner in this increment, each after a scripted package edit.

**Not done:** increments D to H; no real server; the shipped approvals of the new module are untracked and stay out of the commit
until increment G; the six stale approval records still await the owner's list.

**Open for the owner:** do not push between C and D (the module returns a cut reply as a success until D); the private-key fixtures
in `tests/certs/` may be flagged by `safe-git push-check` (they guard nothing, and the spec says so); whether to test from your
terminal that your Ollama server is reachable before F.

### Increment D

**Done:** in `packages/workbench/ask-ollama/helper/ask-ollama`, a prompt that fills the record's `context` (the server's
`prompt_eval_count` at least the window) is `vendor_error` with `context_overflow`, and a reply with `done_reason` `length` is
`reply_cut`; neither is retryable and neither returns text. The conditions of a success status are judged in the spec's order: the
body, `done`, the window, the cut, then the text, so a reasoning model that spent its limit is a cut and an empty reply with another
reason is `unusable_reply`. A generic operating system error is now `vendor_unreachable` before the server began to answer and
`unusable_reply` after (a point deferred from C's second review). Already built in C and now pinned by tests: `num_ctx` from the
record, `--effort` sent as `think` and left out when absent, `effort_unsupported`, the thinking text in no object. New tests are in
`tests/test_askollama_window.py` (22), plus one renamed test in `test_askollama_request.py`. `docs/specs/ask-ollama.md` and
`docs/specs/model-bridge.md` say that D is built; "Known limits" drops the entry that D resolves and adds that a server which
caches the prompt may report a count below the window.

**Verification as run** (Python 3.15.0, macOS): before the change, 8 of the new tests failed against the old helper (3 failures and
5 errors, each because it returned a success where the spec requires a failure); after it the module's 166 tests pass. The whole
suite, `python3 -B -W error tests/run_all.py`: 6,491 tests in 14 roots, OK. `wb verify packages/workbench` accepts the modules;
`wb check` and `wb run code-work check` report no problems. No call was made to a real server. The test of the nesting limit
(exactly 32 and 33 levels) passed against the old helper too, as the boundary was already right: it is a pin and not a proof of a
change, as is the test of an operating system error after the answer began.

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied: the spec's "A thinking model" bullet contradicted its
order of conditions (an empty reply is `reply_cut` when the server reports `length`, else `unusable_reply`); the heading of "Known
limits" and a new entry on a server that reports a smaller count for a cut prompt (unconfirmed 6, settled only by increment F).
Deferred to increment E's pass, which edits the same tests: a test of a count of exactly 10^12 and of a record `context` of 1; the
retry test should assert the code `context_overflow`; the `--server` window test should serve the body it checks. A security review
was not asked for; D adds no input path, only judgement of a parsed reply.

**Releases:** one of `wb release-approvals` by the owner in this increment.

**Not done:** increments E to H; no real server; whether a real Ollama server reports `prompt_eval_count` and `done_reason` as the
spec assumes (unconfirmed 6 and 8, increment F).

**Open for the owner:** the push rule that held between C and D ends with this commit: the module no longer returns a cut reply as a
success. Pushing the five unpushed commits and this one is still your word to give.

### Increment E

**Done:** the argument `embed` of the one command `ask-ollama`, in `packages/workbench/ask-ollama/helper/ask-ollama`: one JSON
object `{"texts": [...]}` on standard input (at most 262,144 bytes, 1 to 100 strings of 1 to 32,768 bytes with a visible
character, strict JSON) is posted to `/api/embed` with `truncate` false and `options.num_ctx` only when the record has `context`; the
object printed is `contract` 1 with `model`, `dimension` (1 to 8,192), `vectors` and `usage.input_tokens`; vectors that are missing,
not finite numbers, of different lengths or not as many as the texts are `unusable_reply`; an object over 2,000,000 bytes is
`reply_too_large`; a 400 about the input length is `context_overflow` with its own message, a 404 about the model is
`model_unavailable`, and any other error status is `bad_exit`; the response body is read to 16 MiB. `module.json` provides
`text-embedding` as well as `model-bridge` and lists `embed`. The failure code is shared with `ask` (`transport_failure`), and
`_check_depth` pushes only lists and objects, so that a list of millions of numbers costs no memory beyond itself; the old code raised
for a scalar never, so this changes memory and not behaviour. Tests: `test_askollama_embed.py` (50), a `Capability` class in
`test_askollama_module.py`, and the three tightenings deferred from D in `test_askollama_window.py`. Docs: `ask-ollama.md` (the
`embed` section made exact, "Known limits"), `model-bridge.md`, a new `text embedding` term in `terms.md`, and the name in the list of
core names in `module-contract.md`, each saying the owner has not confirmed `text-embedding`.

**Deviation from the plan:** the plan says a second command `embed-ollama`. The verifier refuses two commands that name one helper,
so `embed` is an argument of the one command; a caller asks as `wb run --provides text-embedding ask-ollama embed`. The plan is not
edited, because that needs a new approval. That launcher path is not run by any test (it needs an install); increment F is the first
to use it.

**Verification as run** (Python 3.15.0, macOS): before the change, 45 of the module's 221 tests failed against the old helper (44
failures and 1 error); after it all 221 pass, among them the capability tests that read from `packages/`: the verifier accepts the
declaration from the first-party package and refuses `text-embedding` from any other, naming it. The whole suite, `python3 -B -W
error tests/run_all.py`: 6,546 tests in 14 roots, OK. `wb verify packages/workbench` accepts the modules; `wb check` and `wb run
code-work check` report no problems. A measurement on 2026-11-01: parsing a 16 MiB body of numbers cost at most about 195 MiB and two
seconds (in "Known limits"). No call was made to a real server. The refusal tests (a bad input is refused) pass against the old
helper too, because the old helper refuses every `embed`; each is paired with a test of what is accepted, and those fail.

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied: the spec now says `--model` is checked by the
contract's rule and the record's rule for `embed` as for `ask`; "Known limits" says that the `model` a server reports is printed if
it fits the name rule, even if it looks like an address; the printing of numbers is described exactly (`-0`, `1E+3`). Deferred to
the next package pass (probably increment F's, which corrects the module against the real server): the 4,301-digit case of
`test_a_deep_or_hostile_document_is_refused` is refused by the one-key rule and so never reaches the digit check, and its 200-deep
case is refused by the type rule and only guards against a crash (the depth rule cannot be seen alone through `embed`); the check
that the port is absent from the output can fail by chance on a vector of `n/7.0` digits (about one run in ten thousand); the test
of `terms.md` and `module-contract.md` looks only for strings. A security review was not asked for: `embed` reads standard input
and a reply with the same parser and transport as `ask`, which had one.

**Releases:** two of `wb release-approvals` by the owner in this increment; the first was run before the pass and so released
nothing.

**Not done:** increments F to H; no real server (unconfirmed 9, 10, 14, 15 are open); the shipped approvals of the changed package
are untracked and stay out of the commit until increment G; the stale approval records still await the owner's list.

**Open for the owner:** the name `text-embedding`; the bounds chosen for `embed` (100 texts of 32 KB, an input of 262,144 bytes, a
dimension of 8,192, 16 MiB of response, an object of 2,000,000 bytes); and whether to test from your terminal that the Ollama server
is reachable before F.

### Increment F

**Done:** the bridge was run on 2026-11-02, on the owner's word and by the agent through `wb run ask-ollama`, against one Ollama
server (version 0.35.1) on the owner's network over plain `http`. The results are in `ask-ollama.md`, section "The run against a real
server", without the host; each of the statements 1 to 15 carries a tag (confirmed, corrected or not shown). Corrections found:
(6) a prompt that does not fit is cut without an error and the server reports about half the window plus 2 as `prompt_eval_count`
(8194, 4098 and 2050 for the window unset, 8192 and 4096), so the check "at least `context`" does not fire on that server; the spec
now says so in "The window" and "Known limits", and the helper is unchanged because no rule on the count separates a cut prompt from
a long one that fits; (10) a chat model sent to `/api/embed` gets status 501 "does not support embeddings", which the helper now
reports as `model_unavailable` with the message "the model cannot produce embeddings" (it was `bad_exit`). Confirmed: the plain
prompt, `--schema`, the missing model (404), `--effort low` on `gpt-oss:20b`, `effort_unsupported` for `phi4:latest`, embedding
batches of 2 and 100 (768 values) and `bge-m3` (1024 values), and the 400 for a text over the embedding window. The three tightenings
deferred from E went in: the port-absent check looks only in failure objects, the 200-deep case is renamed as a crash guard, and
the 4,300-digit rule is pinned as it is (a run of more than 4,300 digits is refused even in a text, 4,300 is accepted); the
`terms.md` and `module-contract.md` test now checks that both say the owner has not confirmed the name.

**Deviation from the plan:** the owner did not run the cases; the agent did, after the owner wrote `endpoints.json`, ran
`wb acknowledge` and `wb add`, because the agent's shell tool reaches the server. `--schema` had to sit inside the project, so a
throwaway schema file was written under the ignored folder `.workbench/local/` (untracked; it remains until the owner says it may be
removed). `wb upgrade` was not needed, since `wb add` installed the module.

**Verification as run** (Python 3.15.0, macOS): before the correction the new 501 test failed against the old helper; after the first
pass 222 of 223 module tests passed, the one failure being my own test of the 4,300-digit rule (wrong premise: the rule applies inside
a text); after the second pass all 223 pass. The whole suite, `python3 -B -W error tests/run_all.py`: 6,548 tests in 14 roots, OK.
`wb verify packages/workbench`, `wb check` and `wb run code-work check` report no problems.

**Not run:** a server switched off (the agent cannot switch off the owner's server) and a reply cut at the limit (it cannot be
caused reliably); the fake-server tests are the proof of both. Statements 4 (the boolean case), 7, 8, 13 (thinking and format
errors), 14 (`num_ctx` for an embedding, a missing embedding model) and 15 stay unconfirmed and are tagged as such.

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied (spec only): the header and two sentences that still
spoke of the run as future; the statement 1 tag (everything but `done_reason` is shown), the statement 13 tag (the thinking error is
shown through `effort_unsupported`; the format and schema errors are not), the 501 words in "Matching the server's error text", and
the estimate in "embed" now says no run has measured it. The `--provides text-embedding` route was not used by the run (the cases
called `wb run ask-ollama embed`) and the spec says so. Not applied: the reviewer's note that the Result omits the switched-off server
(it is under "Not run"); an optional test that a 400 or 404 carrying the 501 text stays on its own row (the order of the rules
makes it so). A security review was not asked for: the change adds one status row and moves no boundary.

**Releases:** two of `wb release-approvals` by the owner in this increment (after the first pass and after the second).

**Open for the owner:** whether the silent cut is worth a later plan (counting the tokens of a prompt ahead of the call, or a
conservative size rule), because the bridge cannot see it; whether `.workbench/manifest.json`, which `wb add` changed, goes in this
commit; and whether the throwaway file under `.workbench/local/` may be removed.

### Increment G

**Done:** `docs/development.md` has a command row for `ask-ollama` (`ask`, `check` and `embed`) and a section "The ask-ollama bridge"
(the endpoint file, what a real call needs, what the tests need, the window limit, a hand run). `docs/specs/model-bridge.md`, "As
built", has a paragraph on the second bridge, and the status under guarantee 7 and the acceptance criteria say that the bridge was run
once against a real server and that it is built for `embed` as well. The reviewer found those two places still stale; they were
corrected. The shipped approvals: the
preview of `wb release-approvals` read `recorded` for the package and all 13 modules, so no release was needed in this increment.
It listed 16 stale records; the owner approved that exact list ("Approve") and
`wb run safe-git remove --recursive --confirm` removed the 16 directories (4 tracked, 12 never committed). After that the preview
lists 14 records, all `recorded`, and 0 stale. The commit adds the 5 new untracked records of the current package and modules and
deletes the 4 tracked stale ones.

**Verification as run** (Python 3.15.0, macOS): the whole suite, `python3 -B -W error tests/run_all.py`: 6,548 tests in 14 roots,
OK. `wb check` and `wb run code-work check` report no problems, and `wb verify packages/workbench` prints no refusal.
`wb preview release-approvals` after the removal: 14 `record recorded`, `stale records: 0`.

**Not done:** increment H (the upgrade of the installed copies; `.workbench/manifest.json` and the installed copy of the new
module's helper, which the owner's `wb add` made, stay out of this commit); nothing is pushed.

**Review:** one read by the read-only `reviewer`: one blocking finding, applied (the two places in `model-bridge.md` that still said
no real server had been tried and named only `ask` and `check`, and a third that said no bridge to a server meets its items). Also
applied: the Result no longer names an untracked path. Not applied: `--confine` is not listed for `embed` in `development.md`
(accepted by the helper with no effect, per `ask-ollama.md`). A security review was not asked for: documents and approval records
only.

**Releases:** none in this increment.

**Open for the owner:** the same four items as at the end of F, and the push of the local commits.

### Increment H

**Done:** the owner ran `wb acknowledge`, which found nothing to acknowledge, and `wb upgrade`, which completed. The upgrade
installed the new module under `.workbench/workbench/ask-ollama/` (its helper and `module.json`) and changed
`.workbench/manifest.json`: two new rows for those files, the new module in the package's module list, and new trees for the package
and for `code-work` and `groundwork` (whose changes were in tests only, so no installed file of theirs changed).

**Verification as run** (Python 3.15.0, macOS): every installed helper under `.workbench/workbench/` was hashed against the helper of
the same module in `packages/workbench/`: 12 compared, 0 differences, among them the installed `ask-ollama`. The manifest's package
tree (`d570ecc9…`) and the `ask-ollama` tree (`96e4b594…`) are those of `wb preview release-approvals`. `wb check` reports no problem.

**Not done:** no engine was set to use `ask-ollama` (choosing a bridge is the owner's setting, and this plan did not change it). H is committed locally and is not pushed.

**Push of A to G:** made after G on the owner's word (`origin/main` at `ceb4df7`), with the six findings of the credential check on
the test certificates accepted by the owner. G's "nothing is pushed" was true when G was committed.

**Review:** one read by the read-only `reviewer`: no blocking finding. Applied: the push is reported under its own line. The reviewer
could not hash the helpers itself; the comparison above is the author's run. A security review was not asked for: the increment
records an installation and changes no code.

**Releases:** none.

**Open for the owner:** whether to plan a size rule for the silent cut of an oversize prompt; whether the test certificates and keys
should be generated at run time instead of kept (a new increment); the name `text-embedding` and the bounds chosen for `embed`; and
whether `action-review` should pass `--confine`.
