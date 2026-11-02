# ask-ollama

Status: Draft. Written by plan `2026-11-01-ask-ollama-bridge` (increment B), before the module existed, so that the module and its
tests are built against this text. Increment C built the module for `ask` and `check` (against a fake server in its tests);
increment D built the rules for the context window, a cut reply and thinking; the `embed` argument (increment E) is not built yet.
Every statement about the Ollama server's own interface is listed under "Unconfirmed statements" and is confirmed or corrected by
the owner's run against a real server (increment F of the plan). The spec stays `Draft` until the owner approves it.

Terms are in `terms.md`. The contract it satisfies is `model-bridge.md` (version 2), whose sections on a bridge to a server this
spec fills in. The endpoint file is set by the accepted decision `2026-11-01-endpoint-records-in-the-store`; the contract by
`2026-11-01-bridge-contract-version-2`.

## Scope

The first-party module `ask-ollama`: a model bridge to an Ollama server. It has one command, `ask-ollama`, with three arguments:

- `ask` answers one prompt with one contract version 2 object, as `ask-codex` does.
- `check` is a read-only diagnostic of the endpoint file.
- `embed` takes a batch of texts and returns vectors, under the capability `text-embedding`. It is added by increment E of the plan;
  until then the command has `ask` and `check` only.

The verifier refuses two commands that name one helper, so the embedding is an argument of the one command and not a second command.
(An earlier draft of this spec had a second command, `embed-ollama`.)

This spec states the endpoint file as the module reads it, the mapping of every option, the request and the reply, the errors, the
bounds, the rules for the context window, truncation and thinking, the transport, `check`, the embedding contract and the
conformance checklist.

## Non-goals

- Authenticated endpoints and any credential. A record that says `authenticated: true` is refused (decision, item 3).
- A command that writes the endpoint file. The owner writes it by hand.
- Installing, pulling, listing or starting a model, and choosing a model, retrying or falling back to another bridge.
- Routing between machines, quotas, a registry and the library's doctor. They belong to the knowledge base.
- Sending a document to the server so that the review engine can use it. This bridge reads no project file but the schema file.
- Streaming, the server's tools or function calling, images, and any request that is not a prompt or an embedding.
- Verifying where a host is. The location class is the owner's word.

## Assumptions and constraints

- The contract of `model-bridge.md` version 2 and its guarantees 5 to 8 hold. Guarantees 1 to 4 concern a vendor program and do not
  apply here; the guarantees that matter to a server are in "Transport" below.
- The helper imports the standard library and `wbkit` only, and uses `http.client` for the connection and `ssl` for `https`. It
  reads no proxy variable and no other environment variable that affects the connection.
- No test reaches a host other than one the test starts on the loopback address.
- The Ollama interface is described from memory of its documentation. It is unconfirmed until increment F.
- A number below that is this spec's own choice (a bound, a limit) says so. The bounds can be changed by editing this spec and the
  tests together.

## Behavior

### Declaration

| field | value |
|---|---|
| type | `module` |
| provides | `model-bridge` and `text-embedding` |
| requires, fills, writes | nothing |
| ships | one helper, `helper/ask-ollama` |
| commands | `ask-ollama` (`helper` `helper/ask-ollama`, `runtime` `python`, `kit` 1, `arguments` `["ask", "check"]`, and `"embed"` once increment E adds it) |
| `ask_reads` | `~/.config/project-workbench/endpoints.json`, so that a harness which provides `permissions` asks before the agent reads it |

The capability name `text-embedding` is this spec's proposal. Like `model-bridge`, it is the owner's to confirm. It has no prefix, so
only the first-party package may provide it. The module provides both `model-bridge` and `text-embedding` (the second from increment
E), and a caller asks for an embedding as `wb run --provides text-embedding ask-ollama embed`.

### The endpoint file

The module reads `~/.config/project-workbench/endpoints.json` as the accepted decision sets it: its place, its format (`format` 1,
`endpoints`, `default`), its bounds, the fields of a record, the grammar of `host`, the meaning of loopback and the refusal of the
whole file for any bad record. This spec does not restate the grammar; the decision is its source. What the bridge adds:

- **Reading.** By the fixed path under the home directory, through the kit's no-follow layer, on every call. `HOME` is honoured, as
  the operating system does, and nothing else moves the path.
- **Refusals.** A missing, unreadable, linked, non-regular or oversize file, a file that is not strict JSON of the format, a record
  outside the rules, a `default` that names no record, and a record with `authenticated: true` are each refused before a
  connection is made, with one `refused:` line on standard error, nothing on standard output and exit 1. The line names the rule
  and the field and never quotes the value, the host or the port.
- **Which record.** `--server <name>`, else `default`, else a refusal; a name that no record carries is a refusal.
- **What the bridge never does with a record.** It never prints, logs or passes on the host or the port: not in an object, a
  message, a refusal, a diagnostic or the arguments of its own process. The server necessarily sees the destination of the
  connection and the `Host` header, and both come only from the selected record.

### `ask`: the options

Every option of the contract is recognized (`model-bridge.md`, "Input"). The rules are those of the contract: each at most once, a
value as the next argument except `--confine`, and a refusal of anything else before anything is sent.

| option | what this bridge does |
|---|---|
| `--model <name>` | Validated by the contract's rule and also by the rule for the record's model fields (decision, item 3), so a value such as `a..b`, which the contract allows and the record rule refuses, is refused for this bridge. Sent as the request's `model`. When absent, the record's `default_model` is used. When neither names a model the call is refused ("no model is named; pass --model or set default_model in the record"), because a server has no default. |
| `--effort <level>` | `low`, `medium` or `high`, validated as in the contract. Sent as the request's `think` with the same word. Without `--effort`, `think` is left out and the server decides. A server that rejects it for this model gives `effort_unsupported`. [unconfirmed 4] |
| `--timeout <seconds>` | The whole call, from the start of the connection to the last byte of the reply. The connection itself is given at most 10 seconds (this spec's choice) or the whole timeout if that is shorter. |
| `--root <path>` | Validated by the contract's path rules (inside the project, no link, exists, a directory, not in `.git` or `.workbench`) and then ignored: a server has no working directory. |
| `--schema <path>` | Located as `ask-codex` locates it: inside the project, no link, a regular file, at most 65,536 bytes, one JSON object. Parsed more strictly than `ask-codex` parses it, because the schema is read and written out again: a repeated key, `NaN`, a number too large for a finite float (`1e999`), a run of more than 4,300 digits, a lone surrogate or nesting deeper than 32 levels is refused here, and a schema that has one of these and that `ask-codex` passes on is refused by this bridge, which is the one refusal the two bridges do not share. Sent as the request's `format`, with the same keys and values. [unconfirmed 3] |
| `--server <name>` | Selects the record. |
| `--confine` | Accepted and has no effect: the bridge has no tool to switch off. The object does not say so. |

### `ask`: the request

One `POST` to the fixed path `/api/chat` with `Content-Type: application/json` [unconfirmed 1, 2]. The body is one JSON object with exactly: `model`;
`messages`, one message with `role` `user` and `content` the prompt (a string; the prompt is UTF-8 text); `stream` `false`; and, only
when they apply, `options` with `num_ctx` (the record's `context`), `format` (the schema) and `think` (the effort). No other field is
sent, and the prompt appears nowhere else. The headers are `Host` (the record's host, with brackets for an IPv6 literal, and the
port when it is not the scheme's default), `Content-Type: application/json`, `Content-Length`, `Accept: application/json`,
`Connection: close` and `User-Agent: ask-ollama/1` (a fixed string that does not change with the version of the module); no other
header is sent. The request is built from the validated options and the selected record only.

### `ask`: the reply

The reply is read to a bound (below) and parsed as strict JSON: valid UTF-8, no repeated key, no `NaN` and no number that is too
large to be finite, no lone surrogate, nested at most 32 levels, and no run of more than 4,300 digits anywhere (refused before it
is parsed, because Python's own limit on the digits of an integer can be lifted by an environment variable of the caller). A reply
that is not one object is `vendor_error` with `unusable_reply`. From the object the bridge takes `message.content` (a string), `model`, `done`, `done_reason`,
`prompt_eval_count` and `eval_count`, and ignores everything else [unconfirmed 1]. In particular `message.thinking`, if present, is
never returned, never put in a message and never counted as the reply [unconfirmed 8].

- **`reply`** is `message.content`, display-cleaned (control characters removed, newline and tab kept) and at most 262,144 bytes. A
  longer reply is `reply_too_large`, not a cut. An empty reply, or one that is blank after cleaning, is `unusable_reply`; with
  `--schema`, a reply that is not one JSON object is `unusable_reply` too.
- **`model`** is the server's `model` when it is a string that fits the rule for the record's model fields (decision, item 3) and
  otherwise the name the call used (the `--model` value or the record's `default_model`), which fits that rule because both are
  validated by it; so `model` is never `null` for a call that was sent. A namespaced name, with a `/`, is printed as it is: the
  contract's output does not limit the characters of `model`, and only the `--model` option does.
- **`usage`**: `input_tokens` is `prompt_eval_count` and `output_tokens` is `eval_count`, each a non-negative whole number of at most
  10^12 or `null`; `total_tokens`, `cached_input_tokens` and `reasoning_output_tokens` are `null`, because the server does not
  report them as the contract defines them and the bridge derives nothing.

### Context window, truncation and thinking

- **The window.** When the record has `context`, the request sets `options.num_ctx` to it. When it has none, the request leaves the
  server's own window, and the bridge makes no overflow check, because it does not know the window. The spec states this because
  the server's default window is small and a long prompt may be cut silently. [unconfirmed 6]
- **A prompt that does not fit.** When the record has `context` and `prompt_eval_count` is at least `context`, the prompt was
  filled to the window and may have been cut. The call is `vendor_error` with `context_overflow`, not retryable, and no reply is
  returned. If the reply carries no `prompt_eval_count`, the check cannot run and does not; the spec states that rather than
  implying it. [unconfirmed 6]
- **A reply that was cut.** When `done_reason` is `length`, the server stopped at a limit. The call is `vendor_error` with
  `reply_cut`, not retryable, even if some text came back.
- **A thinking model.** A model that reasons may spend its limit in its reasoning and return an empty `message.content`. When the
  server reports `done_reason` `length`, that is `reply_cut`, which names the cause; the cut is judged before the text. When it
  reports anything else, or nothing, an empty or blank `message.content` is `unusable_reply`. The thinking text is never returned
  as the reply.
- **A server that closes the connection or resets it after it began to answer, or sends a reply that is `done` false,** is
  `unusable_reply`. Before it began to answer, a close or a reset is `vendor_unreachable` (below).

### Errors

Every error is the contract's failure object, with a fixed message; the server's own words are never quoted.

**Connecting and timing out.** Anything that goes wrong before the connection is made is `vendor_unreachable`: a refusal, a reset, no
route, a name that does not resolve, and a connection that is not made within its limit, even when that limit is the whole
`--timeout`. `timeout` is only for a connection that was made and then did not finish in time. So a server that never accepts is
`vendor_unreachable`, and a server that accepts and never replies is `timeout`.

**Matching the server's error text.** An error status comes with a body. The bridge takes it as strict JSON of one object with a
string `error` and matches that string in lower case by substring, only to choose a row: "not found" in a 404; "think" in a 400;
"format" or "schema" in a 400. A body that is not of that shape is not matched and the status falls to the `bad_exit` row. The text
is never copied into the object. [unconfirmed 13]

**When several conditions hold**, one rule decides. A body over its bound is `reply_too_large`, whatever the status. For a status
outside 200 to 299 the status rows of the table apply, and the body is used only as the matching rule above says, so an error
status whose body is not one JSON object with a string `error` is the `bad_exit` row and never `unusable_reply`. For a status from 200
to 299 the first of these applies: a body that is not one JSON object (`unusable_reply`); a reply whose `done` is not `true`
(`unusable_reply`; an unfinished reply has no reliable `done_reason`, so it is judged before the next two); a prompt that filled the
window (`context_overflow`); a reply cut at the server's limit, `done_reason` `length` (`reply_cut`); an empty or blank reply, or a
reply that with `--schema` is not one object (`unusable_reply`). So a thinking model that spends its
limit and returns nothing is `reply_cut`, which names the cause. The bridge refines the contract decision's wording that an empty or
cut-off reply is `unusable_reply`: both are `vendor_error`, so a caller sees the same class, and the detail is more exact.

| situation | `error` | `detail` | `retryable` | `message` |
|---|---|---|---|---|
| the connection is refused, not made in time, reset or closed before the server began to answer, no route, a name that does not resolve, a handshake that does not finish | `vendor_unreachable` | null | true | "the server did not answer" |
| `https` and the certificate is not trusted, has expired or is for another host | `vendor_unreachable` | null | false | "the server's certificate was not accepted" |
| the connection was made and the whole call passes `--timeout` | `timeout` | null | true | "the server did not finish in time" |
| status 404 with an error saying the model is not found | `model_unavailable` | null | false | "the server does not have the model" |
| a status 400 whose error says the model does not support thinking | `effort_unsupported` | null | false | "the model does not support this effort" |
| a status 400 whose error is about the format or schema | `vendor_error` | `bad_schema` | false | "the server rejected the schema" |
| any other status outside 200 to 299, including a redirect (which is never followed) | `vendor_error` | `bad_exit` | false | "the server answered with an error" |
| the reply is not one object, is empty, is not `done`, or was cut short by a reset or an early close after the answer began | `vendor_error` | `unusable_reply` | false | "the server returned no usable reply" |
| the reply or the response body is over its bound | `vendor_error` | `reply_too_large` | false | "the server returned more than the bridge accepts" |
| the prompt filled the window | `vendor_error` | `context_overflow` | false | "the prompt does not fit the context window" |
| the reply was cut at the server's limit | `vendor_error` | `reply_cut` | false | "the server stopped the reply at its length limit" |

`not_signed_in` is never produced: no endpoint is authenticated. `context_overflow` and `reply_cut` are codes this bridge adds, as
the contract allows; an engine treats an unknown code as `vendor_error`.

### Transport

- **The connection** is made to the selected record's host and port, and to nothing else: the address a redirect, a reply or the
  prompt supplies is never used. Name resolution is the system's. No proxy is used and no proxy variable is read.
- **No redirect** is followed: any status of 300 to 399 is the `bad_exit` row of the table.
- **`https`** verifies the server. The bridge builds its context in one function, `tls_context()`, which makes a client context
  with hostname checking on and a protocol of TLS 1.2 or later, loads the trusted certificates from the locations compiled into
  the library (`ssl.get_default_verify_paths().openssl_cafile` and `.openssl_capath`, whichever exist) and from nowhere else, and
  sends the record's host as the server name. It does not use `ssl.create_default_context()` for this, because that function honours
  `SSL_CERT_FILE` and `SSL_CERT_DIR`, which a command can set for itself and so add a certificate it trusts; on 2026-11-01, with
  Python 3.15.0, setting `SSL_CERT_FILE` changed `get_default_verify_paths().cafile` and left `openssl_cafile` as it was. An
  untrusted, expired or mismatched certificate is the second row of the table. No option, environment variable or file turns
  verification off or adds a trusted certificate: a test sets both variables to a bundle that holds the fixture certificate and
  shows that the connection is still refused. The function is the one place a test replaces to give trust, and it does so in the
  test's own process. An `https` endpoint needs the library's default bundle to exist on the machine; where it does not, every call
  to such an endpoint is refused as a certificate not accepted, and the owner installs a bundle. [unconfirmed 12]
- **`http`** verifies nothing. `check` warns where the decision says.
- **Bounds** (this spec's choice, changeable with the tests): the request body, counted after JSON encoding, is at most 2,100,000
  bytes. That covers the largest valid input: a prompt (or the texts of an embedding) of 262,144 bytes escapes to at most six times
  that, 1,572,864; a schema of 65,536 bytes, parsed and written out again, to at most 393,216 (a control character grows to six
  bytes); and the other fields add well under 70,000, which is 2,036,080 in all. A request that is nevertheless over the bound (it
  cannot be with valid inputs) is refused before any connection, with a `refused:` line "the request is too large". The response
  body is read to at most 4,194,304 bytes for `ask` (a reply of 262,144 bytes can escape to about 1.6 MB, and a reasoning model's
  thinking text counts against the same body) and 16,777,216 bytes for `embed`, and the call stops when it passes the bound; the
  printed object is at most 2,000,000 bytes, as the contract says.
- **A deadline** covers the whole call. Each read is limited to the time left, and an alarm of the whole call ends it at the
  timeout, so a server that sends a byte at a time ends at the timeout. **Limit:** the alarm is a signal that Python handles
  between instructions, so a name lookup that is stuck inside the system's resolver may not be cut at the timeout; a record that
  holds an IP literal does no lookup. The alarm needs the main thread, which a helper run by the launcher is.
- **Nothing is written** in the project or the store, nothing is logged, and no file is made but none is needed: the schema is read,
  not copied.

### `check`

`ask-ollama check` takes no option. It reads the endpoint file by the rules above, opens no connection and writes nothing. It prints
to standard output, in the file's order, for each record exactly one line of this form (no other whitespace):

`<name> scheme=<scheme> location=<location> authenticated=<true|false> default=<yes|no>`

and then, for each unauthenticated `http` record whose host is not a loopback address (decision, item 4), one line of this form:

`warning: <name>: unauthenticated http away from loopback; content sent to it travels in the clear`

A file with no record prints the single line `no endpoints`. It exits 0 when the file is valid, whether or not it printed a warning,
and 1 with one `refused:` line on standard error and nothing on standard output when the file breaks a rule. It never prints the
host, the port, a model name or the context. An owner runs it after editing the file; an agent may run it, because it prints no
address. The warning lines are what the contract decision calls the diagnostic.

### `embed`

`ask-ollama embed [--model <name>] [--server <name>] [--timeout <seconds>] [--confine]`, with one JSON object on standard input.

- **Input.** Strict JSON, at most 262,144 bytes (this binds well before 100 texts of 32,768 bytes), exactly one key, `texts`: a list
  of 1 to 100 strings, each of 1 to 32,768 bytes of UTF-8 that holds at least one character other than white space, and that is
  valid text (a string with an unpaired surrogate is refused). Anything else is refused before a connection is made.
- **Options.** `--model` is the embedding model, validated by the rule for the record's model fields; when absent, the record's
  `embedding_model`; when neither, a refusal. `--server`, `--timeout` and `--confine` are as for `ask` (`--confine` has no effect).
  `--effort`, `--root`, `--schema` and anything else are refused as unknown options.
- **Request.** One `POST` to the fixed path `/api/embed`. The body is one JSON object with `model`, `input` (the list of texts) and
  `truncate` `false`, so that a text longer than the model's window is an error and not a silent cut, and, only when the record has
  `context`, `options` holding `num_ctx` with that value; no other field. The headers are exactly those of `ask` (above: `Host`,
  `Content-Type: application/json`, `Content-Length`, `Accept: application/json`, `Connection: close` and `User-Agent:
  ask-ollama/1`), and the transport, the bounds and the timeouts of "Transport" apply to it. [unconfirmed 9, 14]
- **Output**, one object on standard output, at most 2,000,000 bytes:
  `{"contract": 1, "ok": true, "vendor": "ollama", "model": "<name>", "dimension": <n>, "vectors": [[<numbers>], ...], "usage":
  {"input_tokens": <n or null>}}`. `contract` is the version of the embedding contract, which starts at 1 and is separate from the
  bridge contract; it lives in this spec, and a caller treats an object with a `contract` it does not know as a failure with no
  vectors, as the bridge contract says. `model` is the server's `model` when it fits the rule for the record's model fields and
  otherwise the name the call used, as for `ask`. `dimension` is 1 to 8,192 and is the length of every vector. `vectors` has one
  vector per text, in the order of the texts. A number is a finite JSON number as the server returned it, not a boolean, and it
  is printed in the form Python prints it, so the size of the object follows the size of the server's body. `input_tokens` is the
  server's `prompt_eval_count` when that is a whole number (not a boolean) from 0 to 10^12, and `null` when it is absent or is
  anything else; a malformed count never makes a reply unusable and is never copied.
- **Failure** is the contract's failure object with `"contract": 1`, the same classes (`not_signed_in` and `effort_unsupported` are not
  produced), and the same rows of the table of errors, with these differences. A status 400 whose error says the input is too long
  for the model is `vendor_error` with `context_overflow`; any other 400 is `bad_exit`; a 404 is `model_unavailable`. A model that
  is not an embedding model, or a count of vectors different from the count of texts, is `vendor_error` with `unusable_reply`.
  [unconfirmed 9, 10, 14]
- **Checks on the reply, and their order.** The chat-only checks of `ask` (`done`, the window, the cut reply and the content) do
  not apply to an embedding reply, which has none of those fields. A body over its bound is `reply_too_large`, whatever the status.
  For a status outside 200 to 299 the status rows apply, with the matching rule and the differences above. For a status from 200
  to 299 the first of these applies: a body that is not one JSON object (`unusable_reply`); a missing `embeddings`, a vector that
  is not a non-empty list of finite numbers, vectors of different lengths, a dimension over the bound, or a count that differs
  from the number of texts (each `unusable_reply`); and an object that would pass 2,000,000 bytes (`reply_too_large`, not a cut
  and not a smaller batch).
- **The caller batches.** The bridge never splits or merges a batch. The caller chooses a batch it knows will fit. As an estimate
  that increment F measures: a server that prints each number of a 1,024-number vector in about 12 characters gives about 12 KB
  per vector, so a batch of 100 prints to about 1.2 MB, inside the bound; longer numbers or larger vectors can pass it, and the
  call is then `reply_too_large`. [unconfirmed 15]

## Conformance checklist

A bridge to a server conforms when a test against a fake server, which the test starts on the loopback address and which records
the request line, headers and body, shows each item. No item needs a real Ollama.

1. The declaration is as above, and the item 1 rules of `model-bridge.md` hold, with the amendment for a further capability.
2. The items of `model-bridge.md` that apply to a bridge to a server hold, adapted as follows: 2 (the prompt); 3 (the options,
   including `--server` and `--confine`); 7 (`--root` and `--schema` are validated, with a root that is not entered because it is
   ignored); 8 (the success object, with the usage of this spec); 9 and 10 (the classes and codes this bridge can produce, which
   exclude `not_signed_in`, `effort_unsupported` for an embedding, and `usage_limit`); 12 (the bounds, with the response bounds of
   this spec); 13 (the schema and the object reply); 14 (hostile reply text); 15 (nothing written in the project or the store, and
   no temporary directory is made); 16 (one object, or one `refused:` line); and 19 (the server items, restated below). Items 4, 5,
   6, 11, 17 and 18 concern a bridge to a program and do not apply.
3. Every refusal of the endpoint file and of a record is made before a connection and shows no host: a missing, unreadable,
   linked, non-regular or oversize file; a file that is not strict JSON (a duplicate key, `NaN`, a float or a boolean where an
   integer belongs); a wrong `format`; an unknown or missing field; more than 64 records; a bad record name; a bad `scheme`,
   `port`, `location`, `authenticated`, `default_model`, `embedding_model` or `context`; a `host` in any form the decision refuses;
   an `authenticated` record; a `default` that names no record; an unknown `--server` name; and no model.
4. The request is exactly as above: the path, the method, the body fields and the headers; the prompt only in `content`; nothing of
   the record but the destination and the `Host` header; the schema only as `format`; `think` and `num_ctx` only when they apply.
5. A redirect is not followed and is `bad_exit`; a connection that is refused, reset or not made within its limit is
   `vendor_unreachable`, and a server that accepts and then never replies, or sends a byte at a time, ends at the timeout as
   `timeout`.
6. `https`: an untrusted certificate, an expired one and one for another host are each refused as the table says, and a trusted
   matching one is accepted, the trust given by replacing `tls_context()` in the test and by nothing else; with `SSL_CERT_FILE`
   and `SSL_CERT_DIR` set to a bundle that holds the fixture certificate, the connection is still refused.
7. The mapping of the reply: the five counts, `total_tokens` `null`, the thinking text never returned, an empty reply, a cut reply
   and a prompt that fills the window as the section above says.
8. No host, port or credential is in any object, message, `refused:` line, `check` output or the arguments of the process.
9. `check` prints one line per record without host or port, warns for an unauthenticated `http` record that is not loopback and for
   none other, makes no connection, writes nothing, and refuses a bad file.
10. `embed`: the input rules, the request, the output shape, the checks on the reply and the size bound as above.
11. The project and the store are byte for byte the same after every call.

## Unconfirmed statements

These come from memory of the Ollama documentation and are not shown by any test, since the tests use a fake server. The owner's run
(increment F) confirms or corrects each. A correction is made in this spec and the module with a test that fails before it.

1. `POST /api/chat` with `stream` false returns one JSON object with `message.content`, `model`, `done`, `done_reason`,
   `prompt_eval_count` and `eval_count`.
2. The request fields `model`, `messages`, `stream`, `options.num_ctx`, `format` and `think` have the meanings used above.
3. `format` accepts a JSON Schema object, and the reply then is one JSON object.
4. `think` accepts `low`, `medium` and `high` for a model that has levels, and a model without them rejects it with a status 400 whose
   error says the model does not support thinking. A model with only on and off may need a boolean; if so, the mapping of
   `--effort` for such a model is decided in the run.
5. A model that is not on the server gives a status 404 whose error says the model is not found.
6. The server's default context window is small, a prompt longer than the window is cut without an error, and when `num_ctx` is set
   and the prompt is longer than it, `prompt_eval_count` reaches `num_ctx`. The reply also always carries `prompt_eval_count`.
7. `done_reason` is `length` when the reply was stopped at a limit.
8. A reasoning model can return an empty `message.content` with its thinking in `message.thinking`.
9. `POST /api/embed` with `model`, `input` (a list) and `truncate` returns `embeddings`, a list of vectors in the order of the input,
   and `prompt_eval_count`; with `truncate` false a text longer than the window is an error.
10. A chat model sent to `/api/embed` gives an error or a result the checks refuse.
11. Resolved on 2026-11-01 (a workbench fact, not an Ollama one): the verifier refuses two commands of one module that name the same
    helper (`workbench/declarations.py`: "two commands name the helper"). The embedding is an argument of the one command.
12. The context built from `openssl_cafile` and `openssl_capath` verifies a certificate chain and a host name on the owner's machine
    with the machine's default bundle, and ignores `SSL_CERT_FILE` and `SSL_CERT_DIR` (a Python and OpenSSL fact, shown by the
    bridge's own test, and measured once on 2026-11-01 for `get_default_verify_paths`).
13. An error status carries a body that is one JSON object with a string `error`, and the words matched in section "Errors"
    ("not found", "think", "format", "schema") appear in the error for a missing model, an unsupported thinking setting and a bad
    format.
14. `/api/embed` honours `options.num_ctx`, returns the `model` it used, answers 404 for an embedding model that is not present, and
    answers 400 with an error about the input length when `truncate` is false and a text is too long.
15. The size of a batch of embeddings, as printed, is close to the estimate in section "embed".

## Known limits

Left as they are, each with its reason. Most were found by the security review of increment C (2026-11-01); the first two come from
increment D and its review:

- **Without `context` in the record a prompt cut by the server's own window is not detected.** The bridge does not know the window
  then, and the server's default is small [unconfirmed 6]. With `context`, the check is "at least the window", so a prompt that
  fills the window exactly is reported as an overflow whether or not anything was cut. (Increment C had neither this check nor
  `reply_cut` and returned both cases as a success; increment D built them.)
- **A server that caches the prompt or counts it differently may report a `prompt_eval_count` below the window for a prompt that
  was cut,** and that prompt passes unreported. Whether a real server does is unconfirmed 6 and is settled only by the owner's run
  (increment F). A record whose `context` is 1 makes every reply with a count of one or more an overflow, by the same rule.
- **A name lookup that is stuck in the system's resolver may not end at the timeout, or at all** ("Transport"): the alarm is handled
  between Python instructions and cannot run inside the resolver's call. An IP literal does no lookup.
- **A connection that fails while the request is being sent** (a broken pipe or a reset) is `vendor_unreachable` even if the server
  had begun to answer with an error status, and a garbage status line or any other protocol error is `unusable_reply` even before
  the server began to answer. A generic operating system error is judged like a reset: `vendor_unreachable` before the server began
  to answer and `unusable_reply` after. These are rare and are the same class either way for a caller that only retries
  `vendor_unreachable`.
- **No server name is sent for an IP literal** in a TLS handshake, because the library does not send one; the certificate is still
  checked against the address, so the fixture certificate for the loopback address works, and a name is sent as the server name.
- **A run of more than 4,300 digits anywhere in a reply or a schema is refused**, including inside a string, so a legitimate reply
  that contains such a run is `unusable_reply`.
- **`HOME` finds the store**, as it does for the rest of the workbench (`2026-10-20-fixed-store-location`: `HOME` is honoured, as
  the operating system does). A process that sets `HOME` for the helper chooses which endpoint file it reads; it is already the
  caller, and the launcher's pin and approval live in the same store.
- **The decision's refusals of IPv6 ranges are exactly the unspecified, IPv4-mapped, multicast and link-local ones.** Deprecated
  and transitional ranges (IPv4-compatible `::/96`, NAT64, 6to4, site-local) are accepted. Apart from `::1` itself, which is loopback,
  none of the addresses in them is loopback, so an unauthenticated `http` record in one of them gets the warning of `check`.
  Refusing more needs a new decision.
- **`--schema` may be a file below `.workbench/` and may be a hard link to a file outside the project.** The engines pass a schema
  from `.workbench/`, so refusing it would break them, and `ask-codex` behaves the same way. The contract's rule is "no symbolic
  link in the path"; an intermediate directory swapped for a link between the check and the open is not caught here, as in
  `ask-codex`. Whoever can do that has write access to the project and already controls the prompt.
- **The `model` in a reply is what the server says**, if it fits the rule for model names. It is cosmetic and is not a record
  of which model answered.
- **Reading the prompt has no deadline.** A caller that never closes standard input blocks the helper; the alarm starts at the
  request. The read is bounded in memory (at most one byte over 262,144) and only the wait is not. The launcher passes the caller's
  input through, and `ask-codex` behaves the same way.

## Acceptance criteria

- Every item of the checklist above is shown by a test against a fake server, and the module passes `wb verify`.
- The owner has run the bridge against a real server and the result is recorded here with the server's version and the date, with no
  host in it, and the list of unconfirmed statements is empty or each remaining one says why.
- The owner has approved this spec, which makes it `Current`.

## Governing decisions and references

- Decisions:
  [2026-11-01-endpoint-records-in-the-store](../decisions/2026-11-01-endpoint-records-in-the-store.md),
  [2026-11-01-bridge-contract-version-2](../decisions/2026-11-01-bridge-contract-version-2.md),
  [2026-10-22-model-calls-go-through-vendor-bridges](../decisions/2026-10-22-model-calls-go-through-vendor-bridges.md),
  [2026-10-20-fixed-store-location](../decisions/2026-10-20-fixed-store-location.md).
- Specs: `model-bridge.md` (the contract), `module-contract.md`, `module-boundary.md`, `terms.md`.
- Plan: `docs/plans/2026-11-01-ask-ollama-bridge.md`.
- References: none. The Ollama interface is described from memory and is listed above as unconfirmed.
