# A model section may hold a temperature and a keep_alive, with call options that replace them

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-02
Date: 2026-11-02

## Context

`2026-11-02-model-configurations-in-endpoint-records` made each endpoint record hold a section for every model that a call may use,
with four fields (item 3), and `2026-11-02-model-section-defaults-and-the-embedding-name` added the optional `effort`, `thinking`
and `output_limit` to a chat section (its item 1). Two more settings that the knowledge-base module needs cannot be said in a section
or in a call today:

- **The temperature.** The knowledge-base module, an external module that calls the bridge by capability, validated its prompts at a
  temperature of 0.2 and retries at 0.5, and reported that the server's own default is higher (a report, not a reading made here). A
  section default alone is not enough for it, because the retry at 0.5 is a call-time choice. Notes that the owner pasted on
  2026-11-02 ask that a call may override the section default.
- **How long the server keeps a model loaded (`keep_alive`).** On a server with one 12 GB card, an embedding call right after a chat
  call failed once with a 500 (reported by the same module, relayed by the owner). Whether the chat model is unloaded at once or kept
  is the owner's to set for a model, and a caller may want a different value for one call.

The endpoint file is read by `wbkit.jsonstrict`, which refuses a number with a fraction or an exponent ("numbers with a fraction or
exponent are not allowed"; `workbench/wbkit/jsonstrict.py`, read on 2026-11-02). A temperature of 0.2 therefore cannot be a JSON
number in the file unless the reader of the kit changes. The helper's own reader of the server's replies accepts finite fractions;
only the file's reader does not.

The plan is `docs/plans/2026-11-02-bridge-request-controls.md` (increment A). The rule for retryable server errors is a separate record
(increment B).

## Decision

1. **This amends the section fields of the two earlier records, and nothing else of them.** A model section may also hold these
   optional fields, and no others are added:
   - `temperature` (a section of `kind` `chat` only): the default temperature of a call to this model.
   - `keep_alive` (a section of either kind): how long the server keeps the model loaded after a call.
   A section of `kind` `embedding` holds no `temperature`. A section that holds a field of the wrong kind, a value outside the
   grammar below, a value that is not a JSON string, or a field that is not listed here makes the file invalid, with a refusal that
   names the rule and never the value, as the bridge does for every other field of the file.
2. **The temperature is held in the file as a string, and sent as a number.** The file holds it as a JSON string, so the file's
   reader needs no change (a change to a shared kit for one field is not recommended). The grammar is exact, in ASCII digits only
   (`0` to `9`), and matches the whole value, with no trailing newline or space: one digit `0`, `1` or `2`, optionally followed by a
   point and one or two decimal digits, and the value is at most 2. The bridge reads the text as a decimal and sends it as a JSON
   number (`"2.00"` is sent as `2.0`). Accepted: `0`, `0.2`, `0.50`, `1`,
   `2`, `2.00`. Refused: a sign (`-0.2`, `+1`), an extra leading zero (`00.2`, `01`), a point with no digit before or after it (`.5`,
   `1.`), more than two decimals, a value above 2 (`2.01`), an exponent, a space, an empty value, and anything that is not a string.
   The bridge sends the value as the request's `options.temperature`, a JSON number. A temperature has no ceiling below 2 that the
   owner declares (the window and the output limit are costs that an owner caps; a temperature is not), so a call may pass any value
   of the grammar.
3. **The keep_alive grammar and the wire form.** The file holds it as a JSON string. The grammar is exact, in ASCII digits only,
   and matches the whole value, with no trailing newline or space: `0` (unload at once), `-1` (keep loaded), or one to four digits,
   the first from 1 to 9, followed by `s`, `m` or `h`. Accepted: `0`, `-1`, `1s`, `30m`,
   `9999h`. Refused: any other sign or negative number (`-2`, `+5m`), a leading zero in a duration (`01s`), a duration with no unit
   (`30`), another unit (`5d`), more than four digits, a fraction (`1.5h`), a space, an empty value, and anything that is not a
   string. The bridge sends it as the request's top-level `keep_alive`: `0` and `-1` as JSON numbers (`0`, `-1`) and a duration as
   a string (`"30m"`). The bridge never sends the string `"-1"` or a form such as `-1m`, so the plan does not depend on how the
   server parses them. It is sent for `ask` and for `embed`, and left out when no call and no section gives one, so the server's own
   default stands. `models` has none.
4. **The call options, and what they override.** Both belong to `ask-ollama` and not to the contract's common core, as `--context`,
   `--thinking` and `--max-output` do, so a caller that wants interchangeable bridges does not pass them:
   - `--temperature <value>` (for `ask` only) replaces the section's `temperature`, takes the grammar of item 2, and is sent as the
     number. A value above 2 is refused. A model whose section holds no `temperature` accepts the option and the value is sent.
   - `--keep-alive <value>` (for `ask` and for `embed`) replaces the section's `keep_alive`, takes the grammar of item 3, and is
     sent in the wire form of item 3.
   Each option is allowed once, needs a value, and is refused before anything is sent when its value is outside the grammar or the
   model is not configured. `embed` refuses `--temperature` and `models` refuses both, as unknown options, as they refuse
   `--effort` today.
5. **`check`** appends the fields that a section holds to its model line, after whatever the line already holds (`bytes_per_token`,
   then ` effort=` or ` thinking=`, then ` output_limit=`): first ` temperature=<text>` (a chat section only), then
   ` keep_alive=<text>`, each as the file's text. A line of an embedding section therefore ends with ` keep_alive=<text>` when the
   section holds one.
6. **What does not change.** A section that holds neither field sends what it sends today, and the server's own defaults stand. The
   size rule, the window, the defaults for the effort, the thinking and the output limit, and every other item of the earlier records
   stand. The bridge adds no retry.
7. **What the mapping to the server rests on.** That `options.temperature` is a number the server reads, that a top-level
   `keep_alive` accepts the number `0` and `-1` and a duration string on `/api/chat`, and that `/api/embed` accepts `keep_alive`
   are from memory of the server's documentation and of a report from the knowledge-base module, not from a reading made here.
   Increment F of the plan sends each form that the bridge produces and records the answer. If the server refuses `-1` as a number,
   the plan stops and this record is revisited with the owner. A correction of the specification or the helper is not a new record
   unless it changes the meaning of this one.

## Alternatives considered

- **A JSON number for the temperature in the file, with a change to the kit's reader.** Rejected: the reader is shared by the other
  modules, it refuses fractions on purpose, and one field does not justify loosening it. The string costs one small grammar.
- **An integer in hundredths for the temperature** (`20` for 0.2). Rejected: an owner reads `"0.2"` as what it is, and a number in
  hundredths invites an error of a hundredfold.
- **A default for the whole record.** Rejected: models on one server differ, and a default that suits a chat model is wrong for an
  embedding model.
- **A call option with no section field.** Rejected for the temperature, because an owner who wants a model to run cold would have to
  trust every caller to say so. Accepted as the way a call overrides the section, which is what the owner asked for.
- **A section field with no call option.** Rejected: the knowledge-base module retries at a different temperature, which is a call
  choice.
- **A temperature ceiling per section, as `output_limit` has.** Rejected: a temperature costs nothing, so an owner has no budget to
  protect, and a ceiling would stop a caller that needs a warmer retry.
- **No `keep_alive`, with an owner-run unload** (the owner stops the model by hand when the card is full). Rejected: the failure
  appeared on a call, and an owner who must unload by hand has no way to make a call safe.
- **Sending a keep_alive as a string always** (`"-1"`). Rejected: a report from memory says that a server may refuse a string with no
  unit, and sending the number removes the question.

## Consequences

- Good: a module that calls the bridge by capability passes only the model name, with a temperature and a keep_alive from the
  owner's file, and a call may run at 0.2 and retry at 0.5 without a second section.
- Good: the fields are optional, so a format-2 file that is written today keeps working and no one rewrites it.
- Good: the file's reader and the kit are unchanged, and a value outside a grammar never reaches the server.
- Bad: a default hides what a call sends. A caller cannot see a temperature or a keep_alive from its own arguments. `check` prints
  them, and the specification says so.
- Bad: `keep_alive` `-1` keeps a model loaded and can starve the other models on a one-card server. It is the owner's declaration in
  the file or the caller's choice by option.
- Bad: a temperature changes the output. A caller whose cache or idempotence key is built from the prompt must include the model and
  the temperature, as the knowledge-base module's key already does. A temperature of 0 does not guarantee equal replies on a server;
  an exact repeat needs a seed, which is deferred.
- Bad: the file holds a number as text, so the validator needs a small grammar at a boundary, and a test for each hostile form.
- Bad: the file grows, and every new field of a section is one more place to make a mistake that the validator then refuses for
  the whole file.
- Bad: the wire form is from memory, and a server that reads `keep_alive` differently may not behave as written. The run checks the
  forms that the bridge sends and no others; the server's answer to a form that the bridge refuses is neither claimed nor tested.
- Bad: the new options exist for one bridge. A caller that works with both bridges does not use them.

## Open questions

- Whether a seed should be the next section default, for a caller that needs exact repeats.
- Whether `--temperature` should later join the contract's common core, with `ask-codex` accepting and ignoring it.

## Evidence

- Read on 2026-11-02 at commit `ef96d37b626b3d6b1b7690b1d75032c5888d3393`:
  `docs/decisions/2026-11-02-model-configurations-in-endpoint-records.md` (item 3),
  `docs/decisions/2026-11-02-model-section-defaults-and-the-embedding-name.md` (items 1 to 4 and its open question on the
  temperature), `docs/specs/ask-ollama.md` ("The endpoint file", "`ask`: the options", "`check`", "`embed`"), `workbench/wbkit/jsonstrict.py`
  (the refusal of a fraction) and `packages/workbench/ask-ollama/helper/ask-ollama` (the section validator, `parse_options`,
  `chat_body`, which sends no `temperature` and no `keep_alive` today).
- The knowledge-base module's report, relayed by the owner on 2026-11-02: the temperature of 0.2 and the retry at 0.5, the 500 on an
  embedding call after a chat call, and its memory of how the server reads `keep_alive`. These are a report from another session and
  were not repeated here. No run of this decision's mapping has been made.
- The call override of the temperature was asked for in notes that the owner pasted into the session on 2026-11-02, and the owner
  then approved the plan that records it (`docs/plans/2026-11-02-bridge-request-controls.md`).
- The server's address is in no tracked file and is not recorded here.

## Related files and decisions

- `docs/plans/2026-11-02-bridge-request-controls.md`
- `docs/specs/ask-ollama.md`
- [2026-11-02-model-configurations-in-endpoint-records](2026-11-02-model-configurations-in-endpoint-records.md) (its item 3, amended by this record)
- [2026-11-02-model-section-defaults-and-the-embedding-name](2026-11-02-model-section-defaults-and-the-embedding-name.md) (its item 1, amended by this record)
- [2026-11-01-bridge-contract-version-2](2026-11-01-bridge-contract-version-2.md)
