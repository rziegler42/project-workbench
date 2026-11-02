# ask-ollama

Status: Draft. Written by plan `2026-11-01-ask-ollama-bridge` (increment B), before the module existed, so that the module and its
tests are built against this text. Increment C built the module for `ask` and `check` (against a fake server in its tests);
increment D built the rules for the context window, a cut reply and thinking; increment E built the `embed` argument. Increment F
ran the bridge once against a real server (2026-11-02; section "The run against a real server").
Every statement about the Ollama server's own interface is listed under "Unconfirmed statements" and tagged with what that run
showed. The spec stays `Draft` until the owner approves it.

Plan `2026-11-02-bridge-model-configurations` (increment B) amended this text before the module changes, as the first plan did: the
endpoint file of format 2 (a section for each model), the allowlist, the window rules, `--context`, the size rule and the argument
`models` are specified here under the accepted decision `2026-11-02-model-configurations-in-endpoint-records`, and are built by
increments C to F of that plan. Until each is built the module reads format 1 and does what the text before this amendment says;
the file is named `endpoints.json` until increment H renames it `bridge-endpoints.json`.

Terms are in `terms.md`. The contract it satisfies is `model-bridge.md` (version 2), whose sections on a bridge to a server this
spec fills in. The endpoint file is set by the accepted decision `2026-11-01-endpoint-records-in-the-store` as amended by
`2026-11-02-model-configurations-in-endpoint-records`; the contract by `2026-11-01-bridge-contract-version-2`.

## Scope

The first-party module `ask-ollama`: a model bridge to an Ollama server. It has one command, `ask-ollama`, with four arguments:

- `ask` answers one prompt with one contract version 2 object, as `ask-codex` does.
- `check` is a read-only diagnostic of the endpoint file.
- `embed` takes a batch of texts and returns vectors, under the capability `text-embedding` (built by increment E of the plan).
- `models` is a read-only diagnostic of the server: which configured models it has and which of its models are not configured
  (increment F of the plan of 2026-11-02).

The verifier refuses two commands that name one helper, so the embedding is an argument of the one command and not a second command.
(An earlier draft of this spec had a second command, `embed-ollama`.)

This spec states the endpoint file as the module reads it, the mapping of every option, the request and the reply, the errors, the
bounds, the rules for the context window, truncation and thinking, the transport, `check`, the embedding contract and the
conformance checklist.

## Non-goals

- Authenticated endpoints and any credential. A record that says `authenticated: true` is refused (decision, item 3).
- A command that writes the endpoint file. The owner writes it by hand.
- Installing, pulling or starting a model, and choosing a model, retrying or falling back to another bridge. (`models` only reads.)
- Routing between machines, quotas, a registry and the library's doctor. They belong to the knowledge base.
- Sending a document to the server so that the review engine can use it. This bridge reads no project file but the schema file.
- Streaming, the server's tools or function calling, images, and any request that is not a prompt or an embedding.
- Verifying where a host is. The location class is the owner's word. The window that a model section declares is the owner's word too:
  the bridge does not read it from the server.
- An exact count of the tokens of a prompt. The size rule is an estimate.

## Assumptions and constraints

- The contract of `model-bridge.md` version 2 and its guarantees 5 to 8 hold. Guarantees 1 to 4 concern a vendor program and do not
  apply here; the guarantees that matter to a server are in "Transport" below.
- The helper imports the standard library and `wbkit` only, and uses `http.client` for the connection and `ssl` for `https`. It
  reads no proxy variable and no other environment variable that affects the connection.
- No test reaches a host other than one the test starts on the loopback address.
- The Ollama interface was described from memory of its documentation and was then checked against one real server on
  2026-11-02 (increment F). Section "The run against a real server" says what the run showed and did not show.
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
| commands | `ask-ollama` (`helper` `helper/ask-ollama`, `runtime` `python`, `kit` 1, `arguments` `["ask", "check", "embed", "models"]`) |
| `ask_reads` | `~/.config/project-workbench/endpoints.json` (`bridge-endpoints.json` after increment H), so that a harness which provides `permissions` asks before the agent reads it |

The capability name `text-embedding` is this spec's proposal. Like `model-bridge`, it is the owner's to confirm. It has no prefix, so
only the first-party package may provide it: the verifier accepts the module's declaration from the first-party package and refuses
the name from any other (shown by the module's tests). The module provides both `model-bridge` and `text-embedding`, and a caller
asks for an embedding as `wb run --provides text-embedding ask-ollama embed`. That launcher path is not run by the module's tests,
and the run of increment F called the command as `wb run ask-ollama embed`, so the `--provides` route is still not exercised.

### The endpoint file

The module reads the owner's file in the guarded store as two accepted decisions set it: `2026-11-01-endpoint-records-in-the-store`
(the place, strict JSON, the grammar of `host`, the meaning of loopback, the refusal of the whole file for one bad record) and
`2026-11-02-model-configurations-in-endpoint-records` (format 2, the `models` object, the allowlist). The file is
`~/.config/project-workbench/endpoints.json`, and `bridge-endpoints.json` from increment H of the plan of 2026-11-02. This spec does
not restate the host grammar; the first decision is its source. What the file holds, in format 2:

- **The file.** Strict JSON, one object, at most 262,144 bytes, with exactly `format` (the integer 2), `endpoints` (an object of at
  most 64 records named as before) and optionally `default` (the name of a record). A file with `format` 1 is
  refused with a line that says the file is in an older format and must be rewritten; a file with any other `format` is refused with
  a line that says the format is not 2. Nothing is read from either and there is no fallback.
- **A record** holds `scheme`, `host`, `port`, `location` and `authenticated` (false only) as before, optionally `default_model` and
  `embedding_model`, and the required `models`. It holds no `context`: the field moved into the model sections, and a record that
  still has it is refused as a field that is not allowed.
- **`models`** is an object of 1 to 64 entries from a model name to a section. A name follows the rule for the record's model fields
  (1 to 128 characters of letters, digits and `._:-`, with `/` between segments; each segment starts with a letter or a digit; no
  `//`, no `..`, no leading or trailing `/`). A section holds exactly: `kind` (`chat` or `embedding`, required); `context` (required,
  a whole number from 1 to 10,000,000: the largest window, in tokens, that the owner declares the model accepts); `default_context`
  (optional, a whole number from 1 to `context`); and `bytes_per_token` (optional, a whole number from 1 to 8, default 2). A float, a
  boolean or a string where a whole number belongs, a field not listed and a missing `kind` or `context` are each refused.
- **`default_model` and `embedding_model`**, when present, name a key of `models`: the first one of `kind` `chat`, the second one of
  `kind` `embedding`. A name that is not a key, or is a key of the other kind, makes the file invalid.

A worked example, with a placeholder host from the documentation range (a real file holds the owner's own host):

```json
{
  "format": 2,
  "default": "lab",
  "endpoints": {
    "lab": {
      "scheme": "http",
      "host": "192.0.2.10",
      "port": 11434,
      "location": "owner-network",
      "authenticated": false,
      "default_model": "chat-a:latest",
      "embedding_model": "embed-a:latest",
      "models": {
        "chat-a:latest": {"kind": "chat", "context": 16384, "default_context": 8192},
        "chat-b:7b": {"kind": "chat", "context": 32768, "bytes_per_token": 1},
        "embed-a:latest": {"kind": "embedding", "context": 8192}
      }
    }
  }
}
```

What the bridge adds:

- **Reading.** By the fixed path under the home directory, through the kit's no-follow layer, on every call. `HOME` is honoured, as
  the operating system does, and nothing else moves the path.
- **Refusals.** A missing, unreadable, linked, non-regular or oversize file, a file that is not strict JSON of the format, a file of
  an older format, a record or a model section outside the rules, a `default` that names no record, a `default_model` or
  `embedding_model` that is not a key of its kind, and a record with `authenticated: true` are each refused before a connection
  is made, with one `refused:` line on standard error, nothing on standard output and exit 1. The line names the rule and the field
  and never quotes the value, the host or the port.
- **Which record.** `--server <name>`, else `default`, else a refusal; a name that no record carries is a refusal.
- **Which model, and the allowlist.** A call uses a model only if it is a key of the selected record's `models`, compared as exact
  text, and only if its `kind` is the one the command needs (`ask`: `chat`; `embed`: `embedding`). A model that is not a key, or is a
  key of the other kind, is refused before anything is sent, with a line that names the rule and does not quote the name. Without
  `--model` the call uses `default_model` (`ask`) or `embedding_model` (`embed`), and with neither it is refused. The allowlist limits
  what the bridge sends; it does not limit the server, which anything that reaches its address can ask for any model.
- **What the bridge never does with a record.** It never prints, logs or passes on the host or the port: not in an object, a
  message, a refusal, a diagnostic or the arguments of its own process. The server necessarily sees the destination of the
  connection and the `Host` header, and both come only from the selected record.

### `ask`: the options

Every option of the contract is recognized (`model-bridge.md`, "Input"). The rules are those of the contract: each at most once, a
value as the next argument except `--confine`, and a refusal of anything else before anything is sent.

| option | what this bridge does |
|---|---|
| `--model <name>` | The model to use, which must be a key of the selected record's `models` of `kind` `chat` (the allowlist above). A bridge to a server checks the value against the configured names in place of the contract's character set: a value that fits the record's model rule and is configured is accepted, so a name with a `/` can be given; any other value is refused before anything is sent, which is how the contract's rule for an unknown `--model` is met for this bridge. Sent as the request's `model`. When absent, the record's `default_model` is used; when the record has none the call is refused ("no model is named; pass --model or set default_model in the record"), because a server has no default. |
| `--context <tokens>` | An option of this bridge only, not part of the contract's common core. A whole number: 1 to 8 ASCII digits, no sign, no leading zero, no space and no other character (so `007`, `+5`, `1e3` and ` 5` are refused), from 1 to the model's `context`; a larger value, a value that is not a whole number and the option without a configured model are refused before anything is sent. It sets the window of the call ("Context window" below). A caller that wants interchangeable bridges does not pass it. |
| `--effort <level>` | `low`, `medium` or `high`, validated as in the contract. Sent as the request's `think` with the same word. Without `--effort`, `think` is left out and the server decides. A server that rejects it for this model gives `effort_unsupported`. [unconfirmed 4] |
| `--timeout <seconds>` | The whole call, from the start of the connection to the last byte of the reply. The connection itself is given at most 10 seconds (this spec's choice) or the whole timeout if that is shorter. |
| `--root <path>` | Validated by the contract's path rules (inside the project, no link, exists, a directory, not in `.git` or `.workbench`) and then ignored: a server has no working directory. |
| `--schema <path>` | Located as `ask-codex` locates it: inside the project, no link, a regular file, at most 65,536 bytes, one JSON object. Parsed more strictly than `ask-codex` parses it, because the schema is read and written out again: a repeated key, `NaN`, a number too large for a finite float (`1e999`), a run of more than 4,300 digits, a lone surrogate or nesting deeper than 32 levels is refused here, and a schema that has one of these and that `ask-codex` passes on is refused by this bridge, which is the one refusal the two bridges do not share. Sent as the request's `format`, with the same keys and values. [unconfirmed 3] |
| `--server <name>` | Selects the record. |
| `--confine` | Accepted and has no effect: the bridge has no tool to switch off. The object does not say so. |

### `ask`: the request

One `POST` to the fixed path `/api/chat` with `Content-Type: application/json` [unconfirmed 1, 2]. The body is one JSON object with exactly: `model`;
`messages`, one message with `role` `user` and `content` the prompt (a string; the prompt is UTF-8 text); `stream` `false`; `options`
with `num_ctx` (the window of the call), and, only when they apply, `format` (the schema) and `think` (the effort). No other field is
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

- **The window.** Every model section has a `context`, so every call has a window: the value of `--context`, else the section's
  `default_context`, else its `context`. The request sets `options.num_ctx` to it. The window is what the owner declared and what
  the caller asked for, and the bridge does not read the server's own. The run showed that the server gives the window the request
  asks for (corrected 6).
- **The size rule.** Before any request, the bridge compares the size of the prompt in bytes of UTF-8 with the window of the call
  times the section's `bytes_per_token` (2 when absent). A larger prompt is not sent: the result is `vendor_error` with
  `context_overflow`, not retryable, with the message "the prompt is probably larger than the window", and no part of the prompt is
  in it. The rule runs after the options and the model are validated and after the schema is read, and it does not apply to `embed`,
  where the server already answers a text that is too long with an error. It is an estimate: a token covers at least one byte of
  text, so a figure of 1 never passes a prompt that the window would cut, and a higher figure passes more prompts that fit and some
  that the window cuts. The owner sets 1 for a model whose work must not lose the start of a prompt (a review, for example). The
  rule does not replace the next one, and the server's own count can still show a cut that this one let through.
- **A prompt that fills the window.** When `prompt_eval_count` is at least the window of the call, the prompt filled the window
  and may have been cut. The call is `vendor_error` with `context_overflow`, not retryable, and no reply is returned. If the reply
  carries no `prompt_eval_count`, the check cannot run and does not; the spec states that rather than implying it.
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
"format" or "schema" in a 400. For `embed` the words are "not found" in a 404, "does not support embeddings" in a 501 and "input length", "context length" or
"too long" in a 400 (section "`embed`"). A body that is not of that shape is not matched and the status falls to the `bad_exit` row. The text
is never copied into the object. [unconfirmed 13]

**When several conditions hold**, one rule decides. Before any request, the size rule of "Context window" may end an `ask` call as
`context_overflow` with nothing sent. A body over its bound is `reply_too_large`, whatever the status. For a status
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
| the prompt is larger than the size rule allows (nothing was sent) | `vendor_error` | `context_overflow` | false | "the prompt is probably larger than the window" |
| (`embed`) a 400 that says the input is too long for the model | `vendor_error` | `context_overflow` | false | "the input does not fit the context window" |
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
to standard output, in the file's order, for each record one line of this form (no other whitespace):

`<name> scheme=<scheme> location=<location> authenticated=<true|false> default=<yes|no>`

and after it, for each model of that record in the file's order, one line of this form:

`model <name>/<model> kind=<chat|embedding> context=<n> window=<n> bytes_per_token=<n>`

where `window` is the section's `default_context`, or its `context` when there is none, and `bytes_per_token` is the section's
figure or 2. After all the records come, for each unauthenticated `http` record whose host is not a loopback address (decision, item
4), one line of this form:

`warning: <name>: unauthenticated http away from loopback; content sent to it travels in the clear`

A file with no record prints the single line `no endpoints`. It exits 0 when the file is valid, whether or not it printed a warning,
and 1 with one `refused:` line on standard error and nothing on standard output when the file breaks a rule, including a file of an
older format. It never prints the host or the port; it prints the record names, the model names and the numbers above, which hold no
address. An owner runs it after editing the file; an agent may run it, because it prints no address. The warning lines are what the
contract decision calls the diagnostic.

### `models`

`ask-ollama models [--server <name>] [--timeout <seconds>]` makes one read of the server's list of models and compares it with the
selected record. It takes no input on standard input (it does not read it) and sends no body. `--server` and `--timeout` are as for
`ask`; every other option, `--model` and `--context` included, is refused as unknown. It needs no `default_model` and no `--model`,
so the refusal of a call with no model does not apply to it. A name is compared as exact text. A bad endpoint file is refused as for
the other arguments.

- **Request.** One `GET` to the fixed path `/api/tags`, with the headers `Host`, `Accept: application/json`, `Connection: close` and
  `User-Agent: ask-ollama/1` and no others. The transport, the bounds and the timeouts of "Transport" apply [unconfirmed 16].
- **Reply.** A strict JSON object with a list `models` whose entries are objects with a string `name`; anything else is `unusable_reply`.
- **Output**, one object: `{"contract": 1, "ok": true, "vendor": "ollama", "present": [...], "missing": [...], "unconfigured": [...],
  "skipped": <n>}`. `present` holds the configured models that the server has, in the file's order; `missing` the configured models
  that it does not have, in the file's order; `unconfigured` the models of the server that are not configured, in the server's order.
  A name is printed only if it fits the rule for the record's model fields; a name that does not is counted in `skipped` and never
  printed. A list of more than 512 names from the server is `reply_too_large`. Names only: no size, date, digest or detail of a model
  is read or printed.
- **Failure** is the contract's failure object with `"contract": 1` and the rows of the table of errors; any status outside 200 to 299
  is the `bad_exit` row. It changes nothing, writes nothing and reads only the endpoint file. It is a call to the server, so a
  real one is made on the owner's word; the tests use a fake server.

### `embed`

`ask-ollama embed [--model <name>] [--context <tokens>] [--server <name>] [--timeout <seconds>] [--confine]`, with one JSON object on
standard input.

- **Input.** Strict JSON, at most 262,144 bytes (this binds well before 100 texts of 32,768 bytes), exactly one key, `texts`: a list
  of 1 to 100 strings, each of 1 to 32,768 bytes of UTF-8 that holds at least one character other than white space, and that is
  valid text (a string with an unpaired surrogate is refused). Anything else is refused before a connection is made.
- **Options.** `--model` is the embedding model, a key of the selected record's `models` of `kind` `embedding` (the allowlist
  above, as for `ask`, so a namespaced name with a `/` can be given when it is configured); when absent, the record's
  `embedding_model`; when neither, a refusal. `--context` is as for `ask`, with the section's `context` as its ceiling. `--server`,
  `--timeout` and `--confine` are as for `ask` (`--confine` has no effect).
  `--effort`, `--root`, `--schema` and anything else are refused as unknown options.
- **Request.** One `POST` to the fixed path `/api/embed`. The body is one JSON object with `model`, `input` (the list of texts) and
  `truncate` `false`, so that a text longer than the model's window is an error and not a silent cut, and `options` holding `num_ctx`
  with the window of the call (the value of `--context`, else `default_context`, else `context`); no other field. The headers are exactly those of `ask` (above: `Host`,
  `Content-Type: application/json`, `Content-Length`, `Accept: application/json`, `Connection: close` and `User-Agent:
  ask-ollama/1`), and the transport, the bounds and the timeouts of "Transport" apply to it. [unconfirmed 9, 14]
- **Output**, one object on standard output, at most 2,000,000 bytes:
  `{"contract": 1, "ok": true, "vendor": "ollama", "model": "<name>", "dimension": <n>, "vectors": [[<numbers>], ...], "usage":
  {"input_tokens": <n or null>}}`. `contract` is the version of the embedding contract, which starts at 1 and is separate from the
  bridge contract; it lives in this spec, and a caller treats an object with a `contract` it does not know as a failure with no
  vectors, as the bridge contract says. `model` is the server's `model` when it fits the rule for the record's model fields and
  otherwise the name the call used, as for `ask`. `dimension` is 1 to 8,192 and is the length of every vector. `vectors` has one
  vector per text, in the order of the texts. A number is a finite JSON number as the server returned it, not a boolean, and it
  is printed in the form Python prints it (so a whole number prints as a whole number, `-0` as `0`, and `1E+3` as `1000.0`), so the
  size of the object follows the size of the server's body. `input_tokens` is the
  server's `prompt_eval_count` when that is a whole number (not a boolean) from 0 to 10^12, and `null` when it is absent or is
  anything else; a malformed count never makes a reply unusable and is never copied.
- **Failure** is the contract's failure object with `"contract": 1`, the same classes (`not_signed_in` and `effort_unsupported` are not
  produced), and the same rows of the table of errors, with these differences. A status 400 whose error, in lower case, holds
  "input length", "context length" or "too long" is `vendor_error` with `context_overflow`, not retryable, with the message "the
  input does not fit the context window"; any other 400 is `bad_exit` (the thinking and format rows do not apply to an embedding);
  a 404 whose error holds "not found" is `model_unavailable`, as for `ask`, and any other 404 is `bad_exit`. A status 501 whose
  error, in lower case, holds "does not support embeddings" (a chat model sent to `/api/embed`) is `model_unavailable` with the
  message "the model cannot produce embeddings"; any other 501 is `bad_exit`. A chat model is refused by the allowlist before any request is made; the 501 row is kept for a model that is configured as an
  embedding model and that the server does not support for embeddings. A model whose reply holds no usable vectors, or a
  count of vectors different from the count of texts, is `vendor_error` with `unusable_reply`. The server's
  words are matched only to choose a row and are never copied. [confirmed 9, 14 in part; corrected 10]
- **Checks on the reply, and their order.** The chat-only checks of `ask` (`done`, the window, the cut reply and the content) do
  not apply to an embedding reply, which has none of those fields. A body over its bound is `reply_too_large`, whatever the status.
  For a status outside 200 to 299 the status rows apply, with the matching rule and the differences above. For a status from 200
  to 299 the first of these applies: a body that is not one JSON object (`unusable_reply`); a missing `embeddings`, a vector that
  is not a non-empty list of finite numbers, vectors of different lengths, a dimension over the bound, or a count that differs
  from the number of texts (each `unusable_reply`); and an object that would pass 2,000,000 bytes (`reply_too_large`, not a cut
  and not a smaller batch).
- **What is refused on input, and how.** Every refusal of the input is one `refused:` line that names the rule and quotes nothing
  of the input (not a text, not a key): the input is empty, is over 262,144 bytes, is not strict JSON (a repeated key, `NaN`, a
  number with more than 4,300 digits, a lone surrogate, nesting deeper than 32 levels and a byte-order mark are each "not one strict
  JSON object"), is not one object with exactly the key `texts`, or holds a list or a text outside the bounds. The request is at
  most three times the input in the worst case (a four-byte character on input is twelve bytes of escapes), so it is under the
  request bound of "Transport" for any valid input.
- **The caller batches.** The bridge never splits or merges a batch. The caller chooses a batch it knows will fit. As an estimate
  that no run has measured yet: a server that prints each number of a 1,024-number vector in about 12 characters gives about 12 KB
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
   `port`, `location`, `authenticated`, `default_model`, `embedding_model`, `models` or a model section (item 12); a `host` in any
   form the decision refuses;
   an `authenticated` record; a `default` that names no record; an unknown `--server` name; and no model.
4. The request is exactly as above: the path, the method, the body fields and the headers; the prompt only in `content`; nothing of
   the record but the destination and the `Host` header; the schema only as `format`; `num_ctx` always, as the window of the call; `think` only when it applies.
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
12. The file of format 2: a file of format 1 is refused with nothing sent and with a line that says the file is older, and a file of
    any other `format` (0, 3, 2.5, a string) with a line that says the format is not 2; a record that still holds `context` is refused; a record with no `models`, with an empty `models`, with more than 64
    sections or with a bad model name is refused; a section with no `kind` or no `context`, a `kind` that is neither `chat` nor
    `embedding`, a `context` or `default_context` that is not a whole number in range, a `default_context` above `context`, a
    `bytes_per_token` outside 1 to 8 and a field not listed are each refused; a `default_model` that is not a key or is not of kind
    `chat`, and an `embedding_model` that is not a key or is not of kind `embedding`, are refused; a section that is not an object, a `kind` that is not a string, and a `models` that is not an object are refused; 64 sections
    are accepted and 65 are refused; and a file of 262,144 bytes is accepted and one byte more is refused.
13. The allowlist: a `--model` that is not a configured key (including one that fits the rule and one with a `/`) is refused with
    nothing sent and the name is not quoted; a configured name with a `/` is accepted; a model of kind `embedding` given to `ask`
    and a model of kind `chat` given to `embed` are refused; without `--model` the call uses `default_model` or `embedding_model`
    and with neither is refused.
14. The window: with no `--context` and no `default_context` the request carries the section's `context` as `num_ctx`; with a
    `default_context` it carries that; with `--context` it carries that, for `ask` and for `embed`; a `--context` of 0, above the
    section's `context`, not a whole number, or without a configured model is refused with nothing sent; one equal to the
    `context` is accepted; and the check of the server's count uses the window that was sent.
15. The size rule: a prompt of exactly the window times `bytes_per_token` bytes is sent; one byte more is not sent and is
    `context_overflow` with the message of the table and no part of the prompt; the figure is the section's `bytes_per_token`, and 2
    when absent; the size is counted in bytes of UTF-8; no request reaches the fake server for a refused prompt; and `embed` is not
    subject to it.
16. `models`: one `GET` to `/api/tags` with no body and the headers of the section, to the record that `--server` selects and
    within `--timeout`; every option but those two is refused as unknown; standard input is not read; `present`, `missing` and `unconfigured` as the
    section says; a name that does not fit the rule is counted in `skipped` and not printed; the order of the three lists is the file's, the
    file's and the server's; a bad endpoint file is refused with nothing sent; more than 512 names is `reply_too_large`; a reply
    that is not an object with a list of objects with a string `name` is `unusable_reply`; a failure is the contract's failure object;
    the host and the port are in no output; and `check` prints one line for each model.

## The run against a real server

Provenance: run on 2026-11-02 by the agent on the owner's word, through `wb run ask-ollama`, with the bridge as committed at
`dfc860e`, against one Ollama server of version 0.35.1 on the owner's network, over plain `http` (the cleartext warning of `check`
printed). The record named the models below; the host is not recorded here. Models on the server: the chat models `phi4:latest`,
`gemma4:12b`, `qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `qwen3-coder:latest` and `freehuntx/qwen3-coder:14b`; the reasoning model
`gpt-oss:20b`; the embedding models `nomic-embed-text:latest` (768 values) and `bge-m3:latest` (1024 values).

| Case | Result |
|---|---|
| Plain prompt, `phi4:latest` | success; a reply and a count of input and output tokens |
| `--schema` (an object with one integer) | success; the reply was one JSON object of that shape |
| A model the server does not have | `model_unavailable` |
| `gpt-oss:20b` without and with `--effort low` | success both times; fewer output tokens with `low` |
| `phi4:latest` with `--effort low` | `effort_unsupported` |
| Prompt of about 11,000 tokens, `phi4:latest` | success, cut silently: see "Known limits" |
| Embedding batch of 2, and of 100, `nomic-embed-text:latest` | success; 768 values each; 100 vectors for 100 texts |
| Embedding with `bge-m3:latest` | success; 1024 values |
| Embedding with `phi4:latest` | status 501, now `model_unavailable` "the model cannot produce embeddings" (was `bad_exit`) |
| One text of 30,000 bytes, `nomic-embed-text:latest` | status 400, `context_overflow` |

Readings from the same run that were not in this record before increment B of the plan of 2026-11-02: `ollama show phi4:latest`
printed `context length 16384` (the model's own limit; the limits of the other models were not read); `/api/ps` showed a loaded
window of 8192 while the record said 8192 and of 4096 while it said 4096; and the 501 for a chat model sent to `/api/embed` read
"This server does not support embeddings. Start it with `--embeddings`" (the bridge matches the lower-case words "does not support
embeddings").

Not run: a server switched off (the run cannot switch the owner's server off), and a reply cut at the limit (it cannot be caused
reliably). The fake-server tests are the proof for both.

## Unconfirmed statements

These came from memory of the Ollama documentation. Each is tagged with what the run of 2026-11-02 (section above) showed:
**confirmed**, **corrected** (the statement was wrong and the text above is the corrected one) or **not shown** (the run did not
reach it; the tests use a fake server and the statement stays unconfirmed).

1. `POST /api/chat` with `stream` false returns one JSON object with `message.content`, `model`, `done`, `done_reason`,
   `prompt_eval_count` and `eval_count`. **[confirmed for all but `done_reason`, which the printed objects do not show (see 7)]**
2. The request fields `model`, `messages`, `stream`, `options.num_ctx`, `format` and `think` have the meanings used above. **[confirmed]**
3. `format` accepts a JSON Schema object, and the reply then is one JSON object. **[confirmed]**
4. `think` accepts `low`, `medium` and `high` for a model that has levels, and a model without them rejects it with a status 400 whose
   error says the model does not support thinking. A model with only on and off may need a boolean; if so, the mapping of
   `--effort` for such a model is decided in the run. **[confirmed for `gpt-oss:20b` with `low`; the refusal text of a model without levels was shown only as `effort_unsupported`; the boolean case is not shown]**
5. A model that is not on the server gives a status 404 whose error says the model is not found. **[confirmed]**
6. The server's default context window is small, a prompt longer than the window is cut without an error, and when `num_ctx` is set
   and the prompt is longer than it, `prompt_eval_count` reaches `num_ctx`. The reply also always carries `prompt_eval_count`. **[corrected: the server cut a prompt that did not fit without an error, but with `num_ctx` set it reported about half the window plus 2 as `prompt_eval_count`, not the window; the unset default was not read]**
7. `done_reason` is `length` when the reply was stopped at a limit. **[not shown]**
8. A reasoning model can return an empty `message.content` with its thinking in `message.thinking`. **[not shown; `gpt-oss:20b` returned its reply in `message.content` for the prompts tried]**
9. `POST /api/embed` with `model`, `input` (a list) and `truncate` returns `embeddings`, a list of vectors in the order of the input,
   and `prompt_eval_count`; with `truncate` false a text longer than the window is an error. **[confirmed for the order, the count and the dimension; `truncate` false confirmed by the 400 below]**
10. A chat model sent to `/api/embed` gives an error or a result the checks refuse. **[corrected: the server answers 501 with an error, which is now `model_unavailable`]**
11. Resolved on 2026-11-01 (a workbench fact, not an Ollama one): the verifier refuses two commands of one module that name the same
    helper (`workbench/declarations.py`: "two commands name the helper"). The embedding is an argument of the one command.
12. The context built from `openssl_cafile` and `openssl_capath` verifies a certificate chain and a host name on the owner's machine
    with the machine's default bundle, and ignores `SSL_CERT_FILE` and `SSL_CERT_DIR` (a Python and OpenSSL fact, shown by the
    bridge's own test, and measured once on 2026-11-01 for `get_default_verify_paths`).
13. An error status carries a body that is one JSON object with a string `error`, and the words matched in section "Errors"
    ("not found", "think", "format", "schema") appear in the error for a missing model, an unsupported thinking setting and a bad
    format. **[confirmed for the missing model, the thinking error (a 400 with "think" in it gave `effort_unsupported`), the embedding 400 and the 501; not shown for the format and schema errors]**
14. `/api/embed` honours `options.num_ctx`, returns the `model` it used, answers 404 for an embedding model that is not present, and
    answers 400 with an error about the input length when `truncate` is false and a text is too long. The bridge recognizes that
    error by "input length", "context length" or "too long" in it (the first two from memory of the server's wording, "the input
    length exceeds the context length"); a different wording is `bad_exit` until the run corrects the words. **[the 400 about the input length confirmed ("the input length exceeds the context length"); `num_ctx` for an embedding, and the 404 for a missing embedding model, not shown]**
15. The size of a batch of embeddings, as printed, is close to the estimate in section "embed". **[not shown; no size was measured]**
16. `GET /api/tags` returns one JSON object with a list `models` whose entries have a string `name`, and the names are those of the
    models the server holds, as `ollama list` prints them. **[not shown; increment G of the plan of 2026-11-02 shows it]**

## Known limits

Left as they are, each with its reason. Most were found by the security review of increment C (2026-11-01); the first two come from
increment D and its review, and the one on embedding replies from increment E:

- **A prompt cut by the server can still pass.** Every model section has a window and the size rule refuses most prompts that are
  too large, but the rule is an estimate from bytes, and the check of the server's own count uses a count that, for a prompt the
  server cut, was about half the window. The server of the run reported 8194 with no window sent, 4098 with 8192 and 2050 with 4096
  for the same prompt. A prompt whose window is the model's limit and whose size passes the rule is sent, and what the server does
  with it is the server's. Whether a prompt between half the window and the whole window is cut was not tested. The check of the
  server's count is "at least the window", so a prompt that fills the window exactly is reported as an overflow whether or not
  anything was cut.
- **A server that cuts a prompt can report a `prompt_eval_count` far below the window, so the check for a prompt that does not fit
  does not see it.** Measured on 2026-11-02 against Ollama 0.35.1 with `phi4:latest` and the same prompt of about 11,000 tokens:
  with no `context` the count was 8194; with `context` 8192 (sent as `num_ctx`, the loaded window read as 8192) it was 4098; with
  `context` 4096 it was 2050. Each cut prompt was answered as a success. The count is about half the window plus 2 once the prompt
  is cut, so "at least `context`" never holds for it, and a prompt between half the window and the whole window is not told
  apart from a cut one by the count alone. Corrected 6. The bridge does not count the tokens of a prompt itself; a caller that
  must not lose the start of a prompt keeps it well under the window. A window of 1 makes every reply with a count of one or
  more an overflow, by the same rule.
- **A name lookup that is stuck in the system's resolver may not end at the timeout, or at all** ("Transport"): the alarm is handled
  between Python instructions and cannot run inside the resolver's call. An IP literal does no lookup.
- **A connection that fails while the request is being sent** (a broken pipe or a reset) is `vendor_unreachable` even if the server
  had begun to answer with an error status, and a garbage status line or any other protocol error is `unusable_reply` even before
  the server began to answer. A generic operating system error is judged like a reset: `vendor_unreachable` before the server began
  to answer and `unusable_reply` after. These are rare and are the same class either way for a caller that only retries
  `vendor_unreachable`.
- **No server name is sent for an IP literal** in a TLS handshake, because the library does not send one; the certificate is still
  checked against the address, so the fixture certificate for the loopback address works, and a name is sent as the server name.
- **An embedding reply of up to 16 MiB is parsed whole in memory.** Measured on 2026-11-01 (Python 3.15.0, macOS), a 16 MiB body of
  one vector of eight million whole numbers, of four million short fractions or of 840 thousand long ones cost at most about 195 MiB
  above the process's own size and under two seconds before it was refused as longer than the dimension bound. A caller that
  cannot spare that sends fewer texts; the bridge does not split a batch.
- **The `model` the server reports is printed if it fits the rule for model names, whatever it looks like.** A hostile server can
  report a name made of digits, dots and a colon, which reads like an address. `ask` and `embed` behave the same, the server
  already knows the address it was reached at, and `model` is not a record of which model answered. Only what the bridge itself
  puts in an object is promised to hold no host or port.
- **A run of more than 4,300 digits anywhere in a reply or a schema is refused**, including inside a string, so a legitimate reply
  that contains such a run is `unusable_reply`.
- **The owner's `context` can be wrong.** It is the owner's declaration of the model's limit and is not read from the server. A value
  above what the server gives is sent as `num_ctx` and the server may clamp it or refuse it; a value that is too high costs the
  server memory (not measured). `default_context` is the way to send less than the declared limit.
- **The size rule refuses some prompts that fit and passes some that do not.** It is the estimate of a byte count; see "Context
  window". It is not applied to `embed`.
- **The allowlist is not a boundary.** The agent can read the file and a shell can call the server directly; the allowlist limits what
  this bridge sends and nothing else.
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
  host in it, and the list of unconfirmed statements is empty or each remaining one says why. (Done on 2026-11-02: each statement
  carries its tag, and the ones not shown say why.)
- The owner has approved this spec, which makes it `Current`.

## Governing decisions and references

- Decisions:
  [2026-11-02-model-configurations-in-endpoint-records](../decisions/2026-11-02-model-configurations-in-endpoint-records.md),
  [2026-11-01-endpoint-records-in-the-store](../decisions/2026-11-01-endpoint-records-in-the-store.md) (superseded in part by the one
  above),
  [2026-11-01-bridge-contract-version-2](../decisions/2026-11-01-bridge-contract-version-2.md),
  [2026-10-22-model-calls-go-through-vendor-bridges](../decisions/2026-10-22-model-calls-go-through-vendor-bridges.md),
  [2026-10-20-fixed-store-location](../decisions/2026-10-20-fixed-store-location.md).
- Specs: `model-bridge.md` (the contract), `module-contract.md`, `module-boundary.md`, `terms.md`.
- Plans: `docs/plans/2026-11-01-ask-ollama-bridge.md` and `docs/plans/2026-11-02-bridge-model-configurations.md`.
- References: none. The Ollama interface was described from memory and checked on one server on 2026-11-02; the statements the
  run did not reach are tagged "not shown" above.
