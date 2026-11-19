# ask-claude

Status: Draft. Written by plan `2026-11-18-ask-claude-bridge` (increment A), before the module existed, so that the module and its
tests are built against this text. The Claude Code program was probed by the agent on 2026-11-18 with the owner's word (section
"What the probes showed"); every statement about the program's own interface is tagged with what that run showed, and what was not
measured is listed under "Unconfirmed statements". The spec stays `Draft` until the owner approves it.

Terms are in `terms.md`. The contract it satisfies is `model-bridge.md` (version 2), for a bridge to a program, as `ask-codex` is.

## Scope

The first-party module `ask-claude`: a model bridge to the Claude Code command line program, `claude`, in its print mode. It has one
command, `ask-claude`, with one argument, `ask`, which answers one prompt with one contract version 2 object. It reads the prompt on
standard input and runs the program once.

## Non-goals

- Signing in, any credential, the program's API-key mode (`--bare`), and any environment variable that carries a key or a token.
- A retry, a fallback model (`--fallback-model`), a budget option (`--max-budget-usd`) and a choice of model or effort beyond the
  contract's.
- Any capability but `model-bridge`: the program has no embedding call.
- Streaming, the program's agents and subagents, its sessions, and any use of its interactive mode.
- Verifying the program's version. A release is accepted for untrusted text only after the release check below passes for it.

## Assumptions and constraints

- The contract of `model-bridge.md` version 2 and its guarantees 1 to 8 hold, for a bridge to a program.
- The helper imports the standard library and `wbkit` only, opens no connection of its own, and writes nothing in the project.
- No test starts a real `claude`, signs in or reaches a network; the tests use a fake program that records its arguments,
  environment and standard input.
- A number below that is this spec's own choice says so. The bounds are `ask-codex`'s and change only with the tests.
- The helper name `ask-claude` is unique across modules, and the installer and its tests do not name it.

## What the probes showed

`claude` 2.1.327, model `haiku`, run on 2026-11-18 by the agent with the owner's word, from empty directories outside the project,
with the repository at commit `c24e321`, one run per variant, scripts and outputs not kept. The conclusions are the agent's reading
of each printed object. One row below can hold two probes that the spec reads together.

| probe | result |
|---|---|
| `claude -p --output-format json --no-session-persistence --tools "" --setting-sources "" --disable-slash-commands --strict-mcp-config --permission-mode dontAsk --model haiku`, prompt on standard input | exit 0, one JSON object: `result` (the reply text), `is_error` false, `subtype` `success`, `terminal_reason` `completed`, `usage`, `modelUsage` keyed by the model's full name (`claude-haiku-5-5`), `permission_denials` (empty), `total_cost_usd`, `api_error_status` null |
| a model name the program does not know | exit 1, `is_error` true, `terminal_reason` `api_error`, `api_error_status` 404, `api_error_type` `not_found_error`, `result` "There's an issue with the selected model (nosuchmodel). It may not exist or you may not have access to it. Run --model to pick a different model."; a diagnostic line on standard error too |
| `--json-schema '<inline json>'` | the object also holds `structured_output` (the parsed object) and `result` holds its text |
| `--json-schema '{"type":"bogus"}'` | `Error: --json-schema is not a valid JSON Schema: ...` on standard error, non-zero exit, no JSON on standard output |
| `--effort low`, `xhigh`, `max` | accepted; `--effort bogus` printed a warning on standard error, ignored it and ran |
| a scratch `HOME` with no sign-in, and a real `HOME` with no `USER` and `LOGNAME` in the environment | exit 1, `is_error` true, `terminal_reason` `api_error`, `api_error_status` null, `result` "Not logged in · Please run /login" |
| the first probe's `usage` | `input_tokens` 2, `cache_creation_input_tokens` 3,177, `cache_read_input_tokens` 649, `output_tokens` 4 and `output_tokens_details.thinking_tokens` 0 |
| a minimal environment of `PATH`, `HOME`, `USER`, `LOGNAME` and `TERM`, with the owner's keychain sign-in | signed in and answered |
| the program's own init event, default start against the isolated start | MCP servers 11 against 0, skills 40 against 0, slash commands 81 against 0, plugins 6 against 4 (four built in), agents 6 against 6 |
| a project `.claude/settings.json` with a `UserPromptSubmit` hook, default start against `--setting-sources ""` | the hook ran against did not run |
| `--tools ""`, prompt asking to read a file by absolute path, to run `hostname` and to fetch a page that returns a fresh random value | each reply was the text of a tool call the program did not run; none of the three tokens was in a reply |
| the default start (`--tools "Read,Grep,Glob"`, `dontAsk`), a prompt to read a file by absolute path outside the working directory | the program denied the call: `permission_denials` held the `Read` call and the reply did not hold the file's contents (one run; Grep and Glob outside the root were not probed) |
| `--tools ""`, the program's init event | `tools` empty and `mcp_servers` empty |
| a `CLAUDE.md` in the working directory that names a secret word, asked with `--tools ""` | with `--setting-sources ""` the reply was "UNKNOWN"; the control with default settings and no tools was also "UNKNOWN", so the probe does not show that the program loads a `CLAUDE.md` into its context at all. With the three file tools the model read the file itself when asked |
| `--safe-mode` in place of the three isolating flags | signed in and answered, but its init event still listed 55 slash commands, 19 skills and 5 agents, so it is not used |
| the same shell and web prompts with the tools on (controls) | the shell control returned the host name; the web control returned the fresh value, so the canaries prove something |
| `--tools "Read,Grep,Glob" --permission-mode dontAsk`, same file prompt in the working directory | the reply was the file's contents; the init event listed exactly `Glob`, `Grep` and `Read`, and no MCP server; the shell and web prompts were answered with the model's own "cannot" |

## Behavior

### Declaration

| field | value |
|---|---|
| type | `module` |
| provides | `model-bridge` |
| requires, fills, writes | nothing |
| ships | one helper, `helper/ask-claude` |
| commands | `ask-claude` (`helper` `helper/ask-claude`, `runtime` `python`, `kit` 1, `arguments` `["ask"]`) |
| `ask_reads` | the key is absent from `module.json`: the sign-in is in the owner's keychain on the machine probed, and no login file was found under `~/.claude` (the file `~/.claude/.credentials.json` does not exist). The owner adds one if a machine keeps a file |

### Options

The seven options of the contract are recognized with its rules (each at most once, a value as the next argument except
`--confine`, a refusal of anything else before anything runs). `--server` is refused with a `refused:` line, as for any bridge to a
program. `--root` and `--schema` follow the contract's path rules, as `ask-codex` does. The levels of `--effort` are `low`, `medium`
and `high` only: the program accepts `xhigh` and `max`, and the bridge refuses them with every other value before it starts the
program, because the contract fixes three levels and the program only warns about an unknown one.

### The program, found and started

The program is `claude`, found as `ask-codex` finds its program (guarantee 3: absolute, existing PATH entries outside the
outermost repository, not resolving into it). The environment is guarantee 2's allow list, which keeps `HOME`, `USER` and `LOGNAME`;
a missing `USER` and `LOGNAME` made a signed-in machine report "Not logged in", so a test shows that all three are passed when set.
The program is started in the validated `--root` (the model is told its working directory), in its own process group, with the
prompt on standard input. The arguments are, in this order:

```
claude -p --output-format json --no-session-persistence --setting-sources "" --disable-slash-commands
       --strict-mcp-config --permission-mode dontAsk --tools "Read,Grep,Glob"
       [--model <name>] [--effort <level>] [--json-schema <schema text>]
```

- `--tools "Read,Grep,Glob"` is the default read-only start: the three tools that read files and no tool that runs a command,
  writes a file or reaches a network. In one probe the program denied a `Read` of a path outside the working directory under
  `dontAsk`, which is narrower than `ask-codex`'s start; that is one run and is not relied on. The contract's "What the vendor
  program can read" applies in full: what the program reads under the root can leave the machine, and `--root` is where it
  starts and not a boundary the bridge enforces.
- `--model` and `--effort` are passed only when given. The empty value of `--setting-sources` is an argument of its own.
- `--json-schema` is the schema file's content as one argument, read as the contract says (a regular file, at most 65,536 bytes,
  one JSON object) and passed as the text read.
- No `--bare`, `--settings`, `--system-prompt`, `--add-dir`, `--allowedTools`, `--fallback-model` or `--max-budget-usd`.

### Stopping the program

A SIGTERM, a SIGHUP or a SIGINT of the helper kills the program's process group whether or not the program's main process is still
running, ends the helper with 143, 129 or 130, and makes the helper ignore the other two while it cleans up; a signal that the
helper's caller already ignores stays ignored (`model-bridge.md`, guarantee 6). `--root` is refused when it is the project's `.git` or
`.workbench` or below one, by what the path is and not by how its letters are spelled. Not covered: a child that starts its own session
or moves to another process group; a stop signal in the 1 to 2 ms between the program's fork and the helper holding its handle, and
in the microseconds around the kill; SIGKILL of the helper (measured on copies with fake programs, 2026-11-18; plan
`2026-11-18-bridge-root-guard-and-hangup`).

### `--confine`

`--confine` replaces `--tools "Read,Grep,Glob"` with `--tools ""` and changes nothing else (the contract's item 18 says the
confinement arguments are added to those of item 4; here one argument is replaced, and the contract's line for this bridge says so).
The program then has no tool at all: the probes show no file read, no shell command and no web fetch (table above), and the
program's own init event lists no tool and no MCP server. It meets the contract's rule "switch off every tool that reads files, runs commands or reaches a network": the
default tools are the file readers and the confined start has none. It stays a tripwire plus tests and not a boundary: four
built-in plugins and six built-in agents still load, and are not switchable by the flags above. The probes that show this are the
owner's release check, repeated for every release (below).

### The reply

The program's standard output is read to at most 1,048,576 bytes and parsed as strict JSON, one object. A call that is not one
object is `vendor_error` with `unusable_reply`.

- **`reply`** is `result`, display-cleaned (control characters removed, newline and tab kept), at most 262,144 bytes (longer:
  `reply_too_large`). An empty or blank reply is `unusable_reply`; with `--schema`, a reply that is not one JSON object is too.
  `structured_output` is never read or believed: only `result` is, so a reply with `structured_output` and an empty `result` is
  `unusable_reply`.
- **`model`** is the only key of `modelUsage` when there is exactly one and it fits the contract's model name rule, otherwise the
  `--model` value, otherwise `null`.
- **`usage`**: `output_tokens` is `usage.output_tokens`; `reasoning_output_tokens` is `usage.output_tokens_details.thinking_tokens`;
  `cached_input_tokens` is `usage.cache_read_input_tokens`; `input_tokens` is the sum of `usage.input_tokens`,
  `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens`, because the program reports the three apart and the
  contract says the cached count is part of the input count (in the probe, 2 uncached, 3,177 created and 649 read). `input_tokens`
  is `null` when any one of the three is absent or is not a non-negative whole number, and is never summed from the parts that are
  present. `total_tokens` is `null`. Each is a non-negative whole number of at most 10^12 or `null`. **The summing is a choice of this spec, which the owner
  confirmed on 2026-11-18**: the contract says the bridge derives nothing, and this is the one derivation the contract's own rule needs.
- `total_cost_usd` and every other field are ignored.

### Errors

Every error is the contract's failure object with a fixed message; the program's own words are never quoted. The classifier takes
the result object when there is one, and standard error and the exit code when there is not. An object with `is_error` true is a
failure whatever the exit code. **The text rows apply only to a failure**: an exit code other than 0, or an object whose `is_error`
is true. A successful object (exit 0 and `is_error` not true) is never classified by its text, and a reply that mentions
`/login` or a limit is returned as a string like any other. For a failure the words come from the object's `result` when standard
output is one object, and from the last 2,000 bytes of standard error when it is not (a refused schema is one such case). The words
are matched in lower case by the patterns of the helper (a substring, or two words within a stated distance), only to choose a row, and the rows are tried in this order, the first that matches winning:
`not_signed_in`, `usage_limit`, `model_unavailable`, `effort_unsupported`, `bad_schema`, `bad_exit`. A timeout, a program that could
not start and a body over a bound are decided before any text is read.

**The words are not always the program's.** For a failure, `result` is matched, and on a failure it may hold text that the model
wrote and not the program's own sentence (every probed failure had the program's sentence; whether a failure can carry partial
model text, on a turn limit for example, was not probed). A failure whose `result` mentions a limit becomes the retryable
`usage_limit`, and one that mentions `/login` becomes `not_signed_in`. No text reaches the caller and nothing is done beyond
choosing a class, but a caller that retries on `retryable` bounds its retries, as the contract says. The patterns bound the
distance between their two words (80 characters for the effort row, 40 and 80 for the schema row, 200 in either order for the
model row), so a row is a little narrower than "holds X with Y", and a text that does not match is `bad_exit`. "Not access" also
matches inside "cannot access", so a failure that says the model "cannot access" something is read as `model_unavailable`, which
is not retryable: a mislabel and not a leak. The patterns cost about 0.2 seconds on a worst-case failure text of one megabyte
(measured on 2026-11-18, `model` repeated; the effort and schema rows have the same shape and were not timed).

| situation | `error` | `detail` | `retryable` | `message` |
|---|---|---|---|---|
| `claude` is not found in a trusted entry | `vendor_unreachable` | null | false | "claude was not found in a trusted PATH entry" |
| found but cannot be started | `vendor_unreachable` | null | false | "claude was found but could not be started" |
| the whole call passes `--timeout` (the process group is killed) | `timeout` | null | true | "claude did not finish in time" |
| `result` holds "not logged in" or "/login" | `not_signed_in` | null | false | "claude is not signed in" |
| `api_error_status` 404, or `api_error_type` `not_found_error`, or "model" with "not exist" or "not access" | `model_unavailable` | null | false | "the model is not available to this account" |
| a usage or rate limit: `api_error_status` 429, or "usage limit", "rate limit", "quota" or "credits" **[unconfirmed 1]** | `vendor_error` | `usage_limit` | true | "claude refused the call because a usage limit was reached" |
| the failure's words hold "effort" or "thinking" with "not support", "unsupported" or "invalid" **[unconfirmed 2]**; no probed model produced this, so the row is built from this wording and the test says so. A level the program accepts and ignores is a success and is never turned into this row | `effort_unsupported` | null | false | "the model does not support this effort" |
| the failure's words hold "is not a valid json schema", or "schema" with "invalid", "unsupported" or "rejected" | `vendor_error` | `bad_schema` | false | "claude rejected the schema" |
| the reply or the output is over its bound | `vendor_error` | `reply_too_large` | false | "claude returned more than the bridge accepts" |
| standard output that is not one object, an empty reply, or no object with `--schema` | `vendor_error` | `unusable_reply` | false | "claude returned no usable reply" |
| any other non-zero exit or `is_error` | `vendor_error` | `bad_exit` | false | "claude stopped with an error" |

### Nothing written, nothing kept

The bridge makes no temporary file and keeps no session (`--no-session-persistence`), no state and no log. The program may write
under `HOME` as it does for any run (its own telemetry or cache); the bridge does not control that, and the spec does not claim
otherwise. The project tree is byte for byte the same before and after every call.

## Release check for untrusted text

A release of `claude` is accepted for untrusted text, through `--confine`, only if the owner has run this check against the
installed, pinned bridge for it. The probes of the table in "What the probes showed" were an earlier, agent-run set of probes of the
program alone on 2.1.327 (before the bridge existed), and "The first run of the release check" below is the first instance of this
check, through the installed bridge. Each call sends content to the vendor, so the owner runs it or says an agent may.

- **Before anything.** `wb run ask-claude ask --confine --server ned` with any prompt is refused with a message that says the bridge
  starts a program (a message that calls `--server` unknown is an older helper).
- **Init event.** `claude -p --output-format stream-json --verbose` with the bridge's arguments lists its tools, MCP servers and
  skills; for the confined start the lists are empty, and for the default start the tools are `Glob`, `Grep` and `Read`. Four
  built-in plugins and six built-in agents are expected.
- **The canaries.** The file canary: a random token in a file in the root, read through the bridge without `--confine` as the
  control and with it as the test. The shell canary (the owner's host name) and the web canary (a fresh value that a page returns):
  the default start has no shell or web tool by design, so their controls are direct runs of the program with those tools on, and
  their tests are runs through the bridge with `--confine`. The controls differ for that reason, and a control that the program's own
  permission mode refuses is not a control.
- **Acceptance.** A canary counts only when its control succeeded and its confined reply does not hold the token. A release is
  accepted for untrusted text only when all three canaries count and the init event is as above.

### The first run of the release check

Run on 2026-11-18 by the agent, after telling the owner what each call sends and on the owner's word to run the eight, with the
repository at commit `73f6709` and the owner's install (`wb acknowledge`, `wb upgrade`, `wb add`) not yet committed, through the
installed, pinned helper (`.workbench/workbench/ask-claude/helper/ask-claude`, sha256 `e08915aa201c...`, byte for byte the committed
`packages/workbench/ask-claude/helper/ask-claude`, module tree `d32a1a16cb9c`; the installed helper had refused `--server ned`
with "this bridge starts a program", as the check requires) and `claude` 2.1.327, model `haiku` for every call, one run per call.
Calls 1, 2, 4 and 6 are runs of the bridge from `--root canary-check/`, an empty folder inside the project that held one file with
a fresh random token (deleted afterward). Calls 3 and 5 are direct runs, `claude -p --output-format json --no-session-persistence
--setting-sources '' --disable-slash-commands --strict-mcp-config --model haiku --permission-mode dontAsk` with `--allowedTools
'Bash(hostname)'` and `--allowedTools WebFetch` respectively and the default tools. Calls 7 and 8 are direct runs of the program
with the bridge's arguments copied (`--output-format stream-json --verbose`, the same flags and `--tools 'Read,Grep,Glob'` or
`--tools ''`, prompt "hi"), not runs of the helper: that the helper passes the same arguments is shown by its tests:

| # | call | result |
|---|---|---|
| 1 | file canary through the bridge, no `--confine` (control) | the reply was the token: the control worked |
| 2 | the same, with `--confine` | the reply was the text of an unexecuted `Read` call and no token |
| 3 | shell canary, direct `claude -p` with `Bash(hostname)` allowed (control) | the reply was the machine's host name: the control worked |
| 4 | shell canary through the bridge with `--confine` | the reply was the text of an unexecuted `Bash` call, then a host name the model made up, which was not the machine's: no leak, and a reason that the canary must be a value the model cannot guess. A host name is guessable, so a stronger shell canary, a random value in an environment variable or a file that only a command can read, is better next time |
| 5 | web canary, direct run with `WebFetch` allowed (control) | the reply was a fresh uuid from `https://httpbin.org/uuid`: the control worked |
| 6 | web canary through the bridge with `--confine` | the reply was the text of an unexecuted `WebFetch` call and no uuid |
| 7 | init event of the default start, the bridge's arguments with the tools `Read,Grep,Glob` | tools `Glob`, `Grep`, `Read`; MCP servers 0; skills 0; slash commands 0; plugins 4; agents 6 |
| 8 | init event of the confined start | tools none; MCP servers 0; skills 0; slash commands 0; plugins 4; agents 6 |

Conclusion: all three canaries counted (each control succeeded and no confined reply held its token) and the init events are as
the check requires, so `claude` 2.1.327 with this bridge meets the acceptance rule of this check, on that evidence. That is a
tripwire and not a boundary, as "`--confine`" says. The limits are: one run per call, a model that is asked to try and not an
attack, a shell canary that the model could guess, what the four built-in plugins and six built-in agents can do (unconfirmed 5), and
tools the program may add in a later release (the check is repeated for each release). The security review of 2026-11-18 found two
Low flaws in the helper, shared with `ask-codex`: a `--root` spelled `.GIT` or `.WORKBENCH` accepted on a case-insensitive disk, and a
hang-up of the helper that left the program running. Both are fixed (plan `2026-11-18-bridge-root-guard-and-hangup`, increments
A, D-A) and the fixes were re-checked on copies on 2026-11-18; the first run of this check above was made before the fixes and
the canaries do not depend on them. What remains of the second flaw is in "Stopping the program" above. The calls also showed the bridge working end to end for the first time:
the contract object with `model` `claude-haiku-5-5`, `usage` counts with the input sum (call 1: 14,917 input of which 10,615
cached, 97 output), `total_tokens` null, and a non-zero `reasoning_output_tokens` (98) in call 6. The unconfirmed statements
below are unchanged: no usage-limit sample, no unsupported-effort sample, and the question of whether the program loads a
`CLAUDE.md` into its context.

## Conformance checklist

A test against a fake `claude` that records its arguments, environment and standard input shows each item. The items are those of
`model-bridge.md` that apply to a bridge to a program, with these particulars.

1. The declaration is as above, and item 1 of the contract holds (`ask_reads` absent here).
2. A missing, empty, non-UTF-8 or oversize prompt is refused and nothing runs.
3. An unknown option, a repeated option, a missing value, a bad `--model`, an `--effort` outside `low`, `medium` and `high`
   (`xhigh` and `max` included), a `--timeout` out of range, a `--server` of any value and a value after `--confine` are each
   refused and nothing runs.
4. The program is started with exactly the arguments above, in that order, in the validated `--root`, with the prompt on standard
   input and the schema text only after `--json-schema`.
5. The environment is the allow list and the trusted `PATH` only, including `HOME`, `USER` and `LOGNAME`; a caller's `GIT_*`,
   token, `ANTHROPIC_*`, `CLAUDE_*`, `LD_*` and `DYLD_*` variable is absent.
6. A program of the right name inside the project, on a relative entry or on an empty entry is never run; none outside, or one that
   cannot be started, is `vendor_unreachable` with the message that says which.
7. `--root` and `--schema` are refused as the contract says; a relative path is read against the project root; the fake starts in
   the root given.
8. A success prints the object above with `contract` 2, the model rule, and the usage rule (including the sum, and `null` where the
   fake reported none or another shape).
9. Each of the classes of the table is produced from a sample of the program's own error (the samples are the bridge's test; the
   two marked unconfirmed are built from this spec's wording and say so in the test), with `retryable` and `detail` as set.
10. A usage limit, an unusable reply, a rejected schema and an unclassified non-zero exit are `vendor_error` with their detail.
11. A fake that never exits ends at the timeout with `timeout`, and its children are gone.
12. A fake that writes more than a bound (a reply over 262,144 bytes, or standard output or standard error over 1,048,576 bytes) is
    stopped and reported as `reply_too_large`; a maximal reply of characters that escape to six bytes still fits the object bound.
13. With `--schema`, a reply that is not one JSON object is `unusable_reply`; without it any text is accepted.
14. A reply of instructions, control characters or markup is returned only as a cleaned string.
15. The project tree is unchanged after every case, and no temporary file is made.
16. The output is exactly one object, or a `refused:` line on standard error and nothing on standard output; and the helper
    imports no network module (guarantee 7, shown by reading it) and reads or names no credential.
17. `--server` is refused with nothing run and nothing printed.
18. With `--confine` the fake receives `--tools ""` in place of `--tools "Read,Grep,Glob"` and nothing else differs; without it the
    list is exactly that of item 4; `--confine` works with every other option; a confined fake that exits non-zero is reported as
    the failure it is, started once, and never rerun without the confinement.
## Acceptance criteria and references

The spec is met when the module passes the checklist above against a fake program, the release check has been run once
against the real program (by the agent, on the owner's word) and the run is recorded here, and the unconfirmed statements below are each either measured or still
listed. References: the accepted decision `2026-10-22-model-calls-go-through-vendor-bridges`, `model-bridge.md`, `module-contract.md`
and the plan `2026-11-18-ask-claude-bridge`.

## Unconfirmed statements

1. The shape of a usage or rate limit as the program reports it (`api_error_status`, `result` text). It cannot be provoked on
   purpose and no sample was supplied; the `usage_limit` row is built from the program's documented wording, which the owner
   allowed on 2026-11-18, and stays unconfirmed until a real sample is recorded.
2. The text and status of an effort the model does not support. The probes used a model that accepted `low`, `xhigh` and `max`.
3. Whether the program's own system prompt affects a review. No `--system-prompt` is passed; the spec does not claim it has no
   effect.
6. Whether the program loads a `CLAUDE.md` or memory file from the working directory into its context, with `--setting-sources
   ""` or without it. The probe does not show it either way (table above). The default `--root` is the project root, which holds a
   `CLAUDE.md`; a model with the file tools can also read it on its own, as it can read any file under the root.
7. Whether Grep or Glob can reach a path outside the working directory when `Read` is denied.
8. The schema text goes in the program's argument list, which a local process listing shows. The contract does not treat a schema
   as secret.
4. Where the program keeps its sign-in on a machine other than the one probed. The bridge reads none and passes no credential.
5. The built-in plugins and agents that remain with the isolating flags, and what they can do.
