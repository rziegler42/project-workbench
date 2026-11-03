# A model section may hold defaults for thinking and the output limit, and the capability name `text-embedding` is confirmed

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-02
Date: 2026-11-02

## Context

`2026-11-02-model-configurations-in-endpoint-records` made each endpoint record hold a section for every model that a call may use,
and fixed a section at exactly four fields (`kind`, `context`, `default_context`, `bytes_per_token`; its item 3). The first real
use of the bridge by another module showed what a section cannot say. The knowledge-base module, an external module that runs
inside the workbench and calls the bridge by capability, reported (relayed by the owner, 2026-11-02):

- `gpt-oss:20b` cannot turn thinking off, and its reasoning tokens count against the output limit, so a call without a low effort
  and an output limit can spend its limit in its reasoning and return nothing. A module that calls the bridge by capability should
  not have to know this about one model.
- The module wants to pass only the model name, with the effort, the thinking and the output limit coming from the owner's file,
  and with a call argument that overrides them (a card and a theme want a different effort and a different output limit).
- A model that only switches thinking on and off (`gemma4:12b` on the owner's server) is a different case from one with levels.

The bridge already takes `--effort low|medium|high` for each call (the contract's common core) and sends it as the server's `think`
(`docs/specs/ask-ollama.md`, "`ask`: the options"). A reply stopped at the output cap is already `reply_cut`. The plan is
`docs/plans/2026-11-02-bridge-model-configurations.md`, increments F-A to F-C. The owner also answered, on 2026-11-02, the open
question about the name of the capability that a bridge provides for embeddings (below).

## Decision

1. **This amends item 3 of the earlier record, and nothing else of it.** A model section of `kind` `chat` may also hold these
   optional fields, and no others are added:
   - `effort`: `low`, `medium` or `high`. The default effort of a call to this model.
   - `thinking`: a JSON boolean. For a model that only switches thinking on and off: whether a call to it thinks.
   - `output_limit`: a whole number of tokens from 1 to 10,000,000. The output cap of a call to this model, and the ceiling of
     `--max-output`.
   A section holds at most one of `effort` and `thinking`. A section of `kind` `embedding` holds none of the three. A float, a
   boolean where a whole number belongs, a string, a word outside the three, or a section that breaks either rule makes the file
   invalid, with a refusal that names the rule and never the value, as the bridge does for every other field of the file.
2. **How a default is sent.** With no `--effort` and no `--thinking`, a section's `effort` is sent as the request's `think` with
   the same word, and its `thinking` as `think` with the boolean. A section's `output_limit` is sent as the request's
   `options.num_predict`. A field that the section does not hold sends nothing, so a section that holds none of them sends what it
   sends today. A call may still pass `--effort`, `--thinking` or `--max-output` to a model whose section holds no default; the argument
   is sent. An `output_limit` is not compared with the window, and a reply larger than the bridge accepts (262,144 bytes) is
   `reply_too_large`, as before.
3. **The call arguments, and what they override.** The new options (`--thinking` and `--max-output`) belong to `ask-ollama` and not to the contract's common core, as
   `--context` does, so a caller that wants interchangeable bridges does not pass the new ones:
   - `--effort <level>` (already an option of the contract) replaces the section's `effort` or `thinking`, and is sent as the word.
   - `--thinking on|off` (new) replaces the section's `effort` or `thinking`, and is sent as the boolean (`on` true, `off` false).
   - `--effort` and `--thinking` in one call are refused.
   - `--max-output <tokens>` (new; 1 to 8 ASCII digits, no sign and no leading zero, as `--context` is) replaces the section's
     `output_limit`. When the section holds one, a larger value is refused; when it holds none, a value up to 10,000,000 is
     accepted.
   Each refusal is made before anything is sent. `embed` and `models` refuse all three options as unknown, as they refuse
   `--effort` today.
4. **`check`** appends the defaults that a section holds to its model line, after `bytes_per_token`: ` effort=<word>`, or
   ` thinking=<on|off>`, then ` output_limit=<n>`.
5. **What does not change.** A reply stopped at the output cap is `reply_cut`, as before. An effort that a model rejects gives
   `effort_unsupported`, as before: an owner who sets an effort that the model rejects sees that error on every call to it. The size
   rule, the window and every other item of the earlier record stand.
6. **The mapping to the server is from memory.** That `think` takes a word for a model with levels and a boolean for a model that
   only switches, and that `options.num_predict` caps the output, is from memory of the server's documentation. The run of
   increment G of the plan confirms or corrects it, including the two combinations that nobody has tried (a boolean sent to a model
   with levels, and a level sent to a model that only switches). A correction is a change to the specification and the helper, not
   a new record, unless it changes this decision's meaning. The on-off case may not be testable on a given server; the
   knowledge-base module reports that `gemma4:12b` on the owner's server takes it.
7. **The capability name `text-embedding` is confirmed by the owner.** The owner's words on 2026-11-02: "keep it, and keep it
   vendor-neutral." The reasons given: the knowledge-base module needs vectors from a pinned model and records which model made
   each vector, which works with any provider of the capability, so the name must not mention Ollama; not every owner has a local
   model, so a cloud embedding bridge should be able to satisfy the same requirement later; a hard requirement is right for the
   first version of that module, because without vectors its catalog cannot search by meaning. The name stays free of any prefix, so
   only the first-party package may provide it. The name `model-bridge` stays unconfirmed. The documents that call the name the
   owner's to confirm (`terms.md`, `module-contract.md`, `ask-ollama.md`) and the module test that checks their wording are changed
   by increments F-B and F-C of the plan.

## Alternatives considered

- **The defaults in the caller.** The knowledge-base module would pass `--effort low` and an output limit for each call. Rejected:
  every module that calls the bridge would have to learn each model's quirks, and the owner has one place to say them.
- **One default for the whole record.** Rejected: models on one server differ (a model with levels, a model that only switches, a
  model that cannot think), and a default that suits one is rejected by another.
- **A single field `think` that holds a word or a boolean.** It would mirror the server's own field. Rejected: the two kinds are
  different things to an owner (a level, and a switch), a one-to-one pair with `--effort` and `--thinking` reads plainly, and each
  field has one form to validate.
- **An `output_limit` with no ceiling.** Rejected: a caller could then ask for any output, which the owner's declaration of the
  largest cap for a model is meant to stop, as `context` is for the window.
- **A separate default and ceiling for the output** (a `default_output_limit` beside the ceiling, as `default_context` is beside
  `context`). Rejected for now: one more field for one case. The owner sets `output_limit` at the largest value that any caller
  needs, and a caller that needs less passes a smaller `--max-output`. The consequence is that a caller that passes nothing gets
  the largest value. A later record may add the second field.
- **Defaults for more request fields** (the temperature, the sampling options, the system prompt). Rejected here and deferred in the
  plan: the temperature matters to the knowledge-base module and is a candidate for the next amendment.
- **Leaving the name `text-embedding` unconfirmed.** Rejected on the owner's word. Renaming it for a vendor was never proposed.

## Consequences

- Good: a module that calls the bridge by capability passes only the model name. The effort, the thinking and the output limit that
  a model needs come from the owner's file, and a call can still override them.
- Good: the fields are optional, so a format-2 file that is written today keeps working and no one rewrites it.
- Good: the name that other modules will require is settled, vendor-neutral, and a cloud bridge may provide it.
- Bad: a default hides what a call sends. A caller cannot see an effort or an output cap from its own arguments. `check` prints
  them, and the specification says so.
- Bad: an owner can set an effort that a model rejects, and then every call to that model is `effort_unsupported` until the file is
  corrected.
- Bad: the mapping to the server is from memory. A model that has levels and also a switch, or a server that reads a boolean
  differently, may not behave as written. The run checks the cases that the owner's server allows, and a model that is not on it
  stays unconfirmed.
- Bad: `output_limit` is both the default and the ceiling. A caller that passes nothing gets the largest value, and the owner must
  set the largest that any caller needs.
- Bad: the new options exist for one bridge. A caller that works with both bridges does not use them, and the defaults apply to a
  call that passes nothing.
- Bad: the file grows, and every section of a chat model is a place to make a mistake that the validator then refuses for the
  whole file.

## Open questions

- Whether the temperature should be the next section default (the knowledge-base module validated at 0.2, with 0.5 on a retry,
  while the server's own default is higher).
- Whether `--thinking` and `--max-output` should later join the contract's common core, with `ask-codex` accepting and ignoring
  them.

## Evidence

- Read on 2026-11-02 at commit `d1ca0a19a944714bdbfe24b2640e69f225590e19`:
  `docs/decisions/2026-11-02-model-configurations-in-endpoint-records.md` (item 3, the section fields), `docs/specs/ask-ollama.md`
  ("`ask`: the options", the model line of "`check`", "The run against a real server") and `docs/plans/2026-11-02-bridge-model-configurations.md`
  (increments F-A to F-C).
- The run of 2026-11-02 through `wb run ask-ollama` (macOS, bridge at `dfc860e`) against one Ollama server of version 0.35.1:
  `gpt-oss:20b` answered a prompt with and without `--effort low` (20 output tokens with it and 44 without: figures read in the session; the specification records only "fewer"), and `phi4:latest` answered
  `--effort low` with `effort_unsupported`. Conclusion: a level is accepted by a model that has levels and rejected by one that
  has none.
- The knowledge-base module's session reported, in two messages relayed by the owner on 2026-11-02, that `gemma4:12b` accepted
  `think: false`, that `gpt-oss:20b` accepted `think: "low"`, that the server reports the thinking capability for both, and that
  `gpt-oss:20b` needed about 6,000 output tokens for a card and 9,000 for a theme, `gemma4:12b` 3,000 and 6,000, because the reasoning
  counts against the output. These are a report from another session on a small sample and were not repeated here. The two
  combinations that it did not try are unconfirmed.
- The owner's words on the name `text-embedding` are quoted in item 7, as the owner gave them in a message of 2026-11-02.
- The server's address is in no tracked file and is not recorded here.

## Related files and decisions

- `docs/plans/2026-11-02-bridge-model-configurations.md`
- `docs/specs/ask-ollama.md`, `docs/specs/terms.md`, `docs/specs/module-contract.md`
- [2026-11-02-model-configurations-in-endpoint-records](2026-11-02-model-configurations-in-endpoint-records.md) (amended on item 3 by this record)
- [2026-11-01-bridge-contract-version-2](2026-11-01-bridge-contract-version-2.md)
