# An endpoint record holds a configuration section for each allowed model, and a call may use only a configured model

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-02
Date: 2026-11-02

## Context

`2026-11-01-endpoint-records-in-the-store` put the records of a bridge to a server in one owner file, `endpoints.json`, in the
guarded store. A record names a server and holds one `default_model`, one `embedding_model` and one `context`, and a caller may name
any model the server has with `--model`. The first run of the bridge against a real server (2026-11-02, Ollama 0.35.1;
`docs/specs/ask-ollama.md`, "The run against a real server") showed what that costs:

- The window belongs to the model and not to the endpoint. The record's single `context` was sent as `num_ctx` for whatever model a
  call named. One server holds chat models and embedding models, and a model's own limit is its own (`phi4:latest` reports 16384;
  the limits of the other models were not read).
- A prompt longer than the window is cut by the server without an error, and the count the server reports for a cut prompt is about
  half the window, so the bridge's check of that count never fires.
- A caller can name any model on the server. The owner has no way to say which models a bridge may use.
- A model such as `freehuntx/qwen3-coder:14b` cannot be named by `--model`, because the contract's character set refuses the `/`.

The owner asked that a record hold a configuration section for each model on a server, that a bridge use only a configured model,
that the window default to the largest the model accepts, that a caller may use a smaller one and is refused when it asks for more,
and that the file be renamed for what it holds. The plan is `docs/plans/2026-11-02-bridge-model-configurations.md`, candidate
`workbench-v1#bridge-model-configurations`. The record of 2026-11-01 is accepted and is not rewritten; this record supersedes it on
the points below and leaves every other point of it standing. The changes, item by item of the earlier record: item 1 (the file's
name, from the rename of item 8 below); item 2 (`format` 1 becomes 2, and the bound of 65,536 bytes is raised); item 3 (`context` is
removed from the record, `models` is added, and `default_model` and `embedding_model` are tied to it); item 5 (the refusal of a
file that is not of this format now refuses format 1, and the file's bound changes); and its Consequence and Open question about
`--model` and the `/`, which item 4 below settles for a bridge to a server. Items 4, 6, 7 and 8 stand. The contract decision
`2026-11-01-bridge-contract-version-2` and `docs/specs/model-bridge.md` are not superseded; item 4 below says how it narrows the
`--model` character set that the specification gives for a bridge to a server, and the specification is amended to say so.

## Decision

1. **A new format number.** The file's `format` is 2. A file with `format` 1 is refused before anything is sent, with a message that
   says the file is in an older format and must be rewritten. This holds from the increment that builds the new reader. There is no
   fallback: no bridge reads format 1, and after the rename of item 8 no bridge reads a file under the old name. Until that rename
   the file is read under its old name, in format 2.
2. **A record** holds the fields of item 3 of the earlier record, except `context`, which is removed from the record, and one new
   required field, `models`. Everything else of the earlier item 3 (`scheme`, `host`, `port`, `location`, `authenticated` and its
   refusal of `true`, the host forms) stands. The file's bound is raised from 65,536 to 262,144 bytes, because a record may now hold
   up to 64 model sections: a section is about 100 bytes, so a record with 64 of them is about 6.4 KB and the bound holds about forty
   such records. It is a practical limit and not a bound that every file of 64 full records fits; the owner's file is far smaller.
   The plan's increment A does not name this bound, and the owner sees it here at acceptance. The record's other bounds (at most 64 records, the names of records, `default`) stand.
3. **`models`** is an object of 1 to 64 entries, from a model name to a section. A model name follows the rule of the earlier record
   for `default_model`: 1 to 128 characters of letters, digits and `._:-`, with `/` between segments, each segment starting with a
   letter or a digit, and no `//`, no `..` and no leading or trailing `/`. A name is the exact name the server knows. A section
   holds exactly these fields, and a field not listed, a missing required one, a boolean or a float in place of a whole number is
   refused:
   - `kind` (required): `chat` or `embedding`.
   - `context` (required): a whole number of tokens from 1 to 10,000,000, the largest window the owner declares that the model
     accepts, taken from the model's own limit. It is the owner's declaration and is not verified.
   - `default_context` (optional): a whole number from 1 to `context`. The window of a call that asks for none.
   - `bytes_per_token` (optional): a whole number from 1 to 8, used by the size rule (item 6). When it is absent the figure is 2.
   `default_model`, when present, names a key of `models` whose `kind` is `chat`; `embedding_model`, when present, names a key whose
   `kind` is `embedding`. Either failing makes the file invalid. A record with neither may be used only with `--model`.
4. **The allowlist.** A bridge uses a model only if it is a key of the `models` of the record the call selects, compared as exact
   text, and only if its `kind` is the kind the command needs (`ask`: `chat`; `embed`: `embedding`). A model that is not configured,
   or is configured for the other kind, is refused before anything is sent, with a `refused:` line that names the rule and never the
   value. Without `--model` the call uses the record's `default_model` (`ask`) or `embedding_model` (`embed`); with neither, it is
   refused. The record's model rule of item 3 replaces, for a bridge to a server, the contract's character set for `--model` (at
   most 64 characters of `A-Za-z0-9._:-`, no `/`): a value that fits the record's rule and is a configured key is accepted, so a
   namespaced model can be named in a call. A bridge to a program is unchanged. The effect on the contract's rule that a `--model` outside its character set or length is
   refused: for a bridge to a server the rule becomes that a `--model` that is not a configured key is refused, so a value outside the
   contract's set is refused unless the owner configured it, and the specification says so. The allowlist limits what the bridge sends. It does
   not limit the server: anything that can reach the server's address can ask it for any model.
5. **The window of a call.** It is, in this order, the value of `--context`, else the section's `default_context`, else the
   section's `context`. It is sent as `num_ctx`, for `ask` and for `embed` (that the embedding route honours `num_ctx` is unconfirmed 14 of
   `ask-ollama.md` until the owner's next run). `--context` is an option of `ask-ollama` and is not part
   of the contract's common core: a whole number from 1 to the section's `context`. A larger value, a value that is not a whole
   number, or the option without a configured model is refused before anything is sent, as every other bad option is. The check that
   the server's reported count of the prompt is not at least the window uses the window that was sent.
6. **The size rule.** For `ask`, before a request is made, a prompt whose size in bytes of UTF-8 is greater than the window of the
   call times the section's `bytes_per_token` is not sent. The result is the contract's failure object with `vendor_error` and
   `context_overflow`, not retryable, with the message "the prompt is probably larger than the window". The rule is an estimate and
   the specification says so: a token covers at least one byte of text, so a figure of 1 can never pass a prompt that the window
   would cut but refuses a good deal more than it must (ordinary English is often put at about three to four bytes per token;
   this is an estimate and was not measured here); the figure 2 is meant to pass ordinary text and code; the owner sets
   1 for a model whose work must not lose the start of a prompt, and a higher figure for plain English. The rule does not replace the
   check of the server's own count, and a prompt under the bound can still be cut. It is not applied to `embed`, where the server
   already answers a text that is too long with an error (confirmed on 2026-11-02).
7. **`models`.** A third argument of the one command, `ask-ollama models [--server <name>]`, makes one read of the server's list of
   models and prints one object of its own contract 1 with three lists of names: `present` (configured and on the server),
   `missing` (configured, not on the server) and `unconfigured` (on the server, not configured). It sends no body, changes nothing,
   reads only the endpoint file, and has the transport and failure rules of the other arguments. The shape of the server's reply is
   an unconfirmed statement of `ask-ollama.md` until the owner's run.
8. **The file's name.** The file is named `bridge-endpoints.json`, in the guarded store, for what it holds: the records of bridges
   to servers. The rename is made in one step of the plan (increment H), after the first real run of format 2, so that a change of
   format and a change of name are not mixed. Until then the file is `endpoints.json`. After it, a helper that looks for the old
   name is a defect and is not kept as a fallback, and the module's `ask_reads` names the new file. The earlier record's item 1 is
   superseded for the name from that step, and in no other respect.
9. **What stands from the earlier record.** The place (the guarded store, by the fixed path, through the kit's no-follow layer), one
   file for the whole account, strict JSON, the host grammar, loopback, a record that holds no credential, `authenticated` refused
   when `true`, the refusal of the whole file for one bad record, the file read again on every call, `--server` and `default`,
   `ask_reads`, and item 8 of the earlier record (no credential, no kit accessor, no launcher change).

## Alternatives considered

- **A list of model names without sections.** An allowlist only. Rejected: it cannot hold the window, which is the reason the
  record has to change, nor the kind, which refuses an embedding model for `ask` before a call.
- **Model sections in a second file.** Keeps the endpoint records small. Rejected: two files can disagree, and the owner must edit
  both to add a model.
- **Reading the window from the server instead of declaring it.** No declaration to get wrong. Rejected: it needs a call before
  each call or a cache, the server's answer is not the owner's allowance, and the run of 2026-11-02 showed that the window a
  request gets is the one asked for and not the model's limit. A command to read it is deferred in the plan.
- **A bound on the window only, with no `default_context`.** The owner's first wording: the window is the model's maximum. Kept as
  the default, and `default_context` is added, because a very large maximum may make the server allocate memory for it on every call (not measured).
- **`--context` in the contract's common core.** Every bridge would accept it, and `ask-codex` would accept and ignore it. Rejected:
  it changes `ask-codex` and the contract, and a caller that passes it to `ask-codex` would otherwise be refused. A caller that wants
  interchangeable bridges does not pass it.
- **Reading format 1 as a fallback.** No file to rewrite. Rejected: a decision that no longer covers a file must not be read from it,
  and a record without sections would have no window and no allowlist.
- **A default of 1 or of 3 for `bytes_per_token`.** 1 refuses up to three times too much and makes the bridge hard to use; 3 passes
  code and text in other scripts that the window then cuts. 2 with a per-model override was chosen.
- **A name for each model, apart from the server's name.** The record would map an alias to the server's name and `--model` would
  carry the alias, which has no `/`. Rejected: a second name to keep in step, for a problem the record's own model rule solves.
- **Renaming the file at once.** One change of format. Rejected: a rename and a format change together make a failed first run
  harder to read, and the rename touches the helper, the declaration and the documents.

## Consequences

- Good: the owner states which models a bridge may use and the window of each; a model that is not configured is refused before
  anything is sent; an embedding model cannot be sent a chat prompt, nor the reverse; a caller can lower the window and cannot raise
  it past the owner's declaration; and a prompt far over the window is stopped before it is sent.
- Good: a namespaced model name can be named in a call, closing the open question of the earlier record for a bridge to a server.
- Bad: the owner's file must be rewritten. The helper refuses format 1, so until the owner writes the new file every call is
  refused.
- Bad: `context` is the owner's declaration. A value above what the server gives is sent as `num_ctx` and the server may clamp it or
  refuse it; a value that is too high costs the server memory. `default_context` is there for that reason.
- Bad: it is not known whether a prompt between half the window and the whole window is cut. The count that the server reported
  for a cut prompt was about half the window, which may mean that it keeps only half; if so, the size rule, which passes a prompt up
  to the window times the figure, can pass a prompt that is cut. The run did not test a prompt in that range. The unset window of
  that server was not read (a count of 8194 with no `context` in the record suggests about 16384).
- Bad: the size rule is an estimate. It refuses some prompts that would have fit, and passes text that becomes more tokens than the
  figure allows. A prompt can still be cut silently, and the count the server reports for it still defeats the check of that count.
- Bad: the allowlist is not a security boundary. The agent can read the file, because the store is not unreadable to it, and a shell
  can call the server directly. It limits what the bridge sends and nothing else.
- Bad: the file is larger and edited by hand. A typo in one section stops every call, including calls to a good record, as in the
  earlier record.
- Bad: the contract's character set for `--model` no longer binds a bridge to a server. The configured set binds it more tightly,
  but a reader who knows only the contract will not expect a `/` to be accepted.
- Bad: the owner handles the file twice: rewriting it into format 2 when the new reader arrives, and renaming it at the rename.
  Between the two, the documents and the code name `endpoints.json` while this record names `bridge-endpoints.json`.
- Bad: `--context` exists for one bridge. A caller that works with both bridges does not use it, and the windows of the two bridges
  differ.

## Open questions

- Whether `--context` should later join the contract's common core, with `ask-codex` accepting and ignoring it.
- Whether a record should name the bridge it is for, if a second bridge to a server reads the file. Today every record is read as an
  Ollama server.
- Whether the owner's declared `context` should be checked against the server, by a command that reads each model's window.

## Evidence

- Read on 2026-11-02 at commit `798a3f1cc420d5f30af694496d820be7dd6f6101`: `docs/decisions/2026-11-01-endpoint-records-in-the-store.md`
  (the items this record supersedes and the ones it leaves), `docs/specs/ask-ollama.md` ("The run against a real server", "Known
  limits") and `docs/specs/model-bridge.md` (guarantee 7 and the `--model` character set).
- The run of 2026-11-02 against one Ollama server, version 0.35.1, through `wb run ask-ollama` from an agent session's shell on
  macOS, with the bridge as committed at `dfc860e`. The counts and the two error texts are those recorded in `docs/specs/ask-ollama.md`;
  the loaded window of 4096, the model's reported limit of 16384 and the capitalised text of the 501 were read from the server in the
  same session and are not yet in that document (increment B adds them to its run record): the same prompt of about 11,000 tokens to `phi4:latest` reported 8194 input tokens with no
  `context` in the record, 4098 with `context` 8192 and 2050 with `context` 4096 (`/api/ps` showed a loaded window of 8192 and of
  4096), and each was a success. `ollama show phi4:latest` printed `context length 16384`. A chat model sent to `/api/embed` was
  answered with status 501, "This server does not support embeddings"; a text of 30,000 bytes to `nomic-embed-text:latest` with
  `truncate` false was answered with status 400, "the input length exceeds the context length". Conclusion: the window follows
  what the request asks for, a cut prompt is reported at about half of it, and the model's own limit is a different number.
- The server's address is in no tracked file and is not recorded here.

## Related files and decisions

- `docs/plans/2026-11-02-bridge-model-configurations.md`
- `docs/specs/ask-ollama.md`, `docs/specs/model-bridge.md`
- [2026-11-01-endpoint-records-in-the-store](2026-11-01-endpoint-records-in-the-store.md) (superseded in part by this record)
- [2026-11-01-bridge-contract-version-2](2026-11-01-bridge-contract-version-2.md)
- [2026-10-20-fixed-store-location](2026-10-20-fixed-store-location.md)
