# Bridges are interchangeable: contract version 2 with a common core and one unreachable class

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-01
Date: 2026-11-01

## Context

Decision 2 of `2026-10-22-model-calls-go-through-vendor-bridges` made a bridge a thin module for one vendor, with the contract in
`docs/specs/model-bridge.md` (version 1). The first bridge, `ask-codex`, wraps a command line program. The owner now wants a second
bridge for a local Ollama server, and requires that the two can replace one another without a change in the caller.

Contract version 1 was written for a bridge that starts a program, and three of its rules do not fit a bridge that calls a server:

- The six error classes include `program_not_found`. A server that cannot be reached has no class, and a bridge that invents its own
  makes every caller learn it.
- Guarantee 7 says a bridge opens no connection of its own. A server bridge must open one.
- The options are written around a program: `--root` is the directory the program works in, and `--effort` is a program setting.
  Nothing says what a bridge does with an option its vendor cannot use, so one bridge could refuse what another accepts.

The owner's measurements of 2026-11-01 with `codex-cli` 0.163.0 also show that a program bridge can read any file the owner's user
can, whatever `--root` says, so a caller that sends captured text has to be able to ask every bridge for confinement in the same way.
The cached and reasoning token counts that the program reports are not in the contract's `usage` object either.

Bounds: the six error classes and the object shape are what an engine parses today (`review-engine.md`), and an engine treats an
unknown `contract` as a failure with no reply. An accepted record is not rewritten (`docs/decisions/README.md`).

## Decision

1. **Contract version 2.** The contract moves to version 2 once, for all the changes below. `ask-codex` is changed to meet it in the
   same work as the Ollama bridge's contract rules, so the two never differ in version. The engines accept version 2.
2. **A common core.** Every bridge recognizes the same seven options: `--model`, `--effort`, `--timeout`, `--root` and `--schema` as
   in version 1, and two new ones, `--confine` (item 5) and `--server` (item 4). Recognizing an option is not accepting it: a bridge
   that cannot honour `--server` or `--confine` refuses it, as those items say, and it never treats either as an unknown option, so
   the refusal is the same on every bridge. `--server <name>` is given at most once with a value as the next argument, a name of 1 to
   32 characters of `a-z0-9_-` starting with a letter or digit. Every bridge prints the same success and failure objects.
3. **An option the vendor cannot use is ignored when it only tunes behaviour.** `--root` is ignored by a bridge to a server that has
   no working directory. It is validated as before, so a bad value is refused by every bridge, and the success object does not claim
   it took effect. `--effort` is not simply ignored by a server bridge: a model that reasons can use up its token limit in its
   reasoning and return an empty reply, so the plan for that bridge decides how the level maps to the server's thinking setting. A
   bridge never returns an empty reply as a success: an empty or cut-off reply is `vendor_error` with `unusable_reply`.
4. **An option that decides where content goes is refused when the bridge cannot honour it.** A new `--server <name>` names an
   endpoint in the owner's guarded store (`2026-10-20-fixed-store-location`), validated to a safe character set and never an
   address. A server bridge resolves it, and falls back to the store's default endpoint when it is absent. A program bridge refuses
   it, because ignoring it could send local-only content to a cloud vendor.
5. **`--confine` is part of the core, and it is opt-in.** A bridge that starts a program disables the program's tool features, its
   shell tool and its web tool. A bridge with no tools satisfies it by construction. A bridge that cannot confine refuses the option
   and does not ignore it. The default stays unconfined, because the review engine needs file access to read plans; a caller that
   sends captured text always passes `--confine`.
   - **Syntax.** `--confine` is a flag with no value, given at most once, unlike the other options. A value after it is read as the
     next argument and refused as an unknown option.
   - **The rule every bridge meets.** A bridge accepts `--confine` only if it switches off, in the vendor program, every tool that
     reads files, runs commands or reaches a network that the bridge knows how to switch off, and it refuses the option when it can
     switch off none of the three kinds. A bridge with no such tool meets the rule by construction. Whether the program's disabled
     features are a fixed list or derived from its feature list is an implementation detail for the plan, and the tests below are
     what shows the rule holds for a release.
   - **What confinement is.** A tripwire plus tests, not a boundary. The program still lists tools that cannot be switched off with
     a known setting: an image viewer, a patch tool (its writes are refused by the read-only sandbox), readers of MCP resources and
     functions that start agents. The bridge says so in its documentation and does not claim that the program cannot read or reach
     anything.
   - **The residual exposure is accepted.** On 2026-11-01 the owner accepted that a tool with no known switch (the image viewer) stays
     available in a confined program, and does not make `--confine` unavailable for that reason. The exposure is the prompt's own
     contents. Text that must not reach a vendor goes to a bridge with no tools, to an endpoint the owner has declared local (see item 7).
   - **Tests for each release.** The four canaries stay (a file in the working directory, one above it, one outside the project, a
     shell command), and two are added: a probe of the web tool, and a check of the tool list against the list recorded for that
     release. The list is the model's own report, so a difference is a reason to stop and look, and a match is not proof. A release is
     accepted for untrusted text only if all of them pass.
6. **One class for a vendor that cannot be reached.** `program_not_found` is renamed `vendor_unreachable`. A bridge uses it for a
   missing program and for a server that does not answer, and says which in `message`. `detail` stays `null`. `retryable` is `false`
   for a missing program and `true` for a server that did not answer or timed out. The other five classes are unchanged.
7. **Guarantee 7 is replaced.** A bridge to a program opens no connection of its own. A bridge to a server opens a connection only to
   the endpoint the store names, follows no redirect to another host, and has a hard timeout. It sends only the model request built from
   the prompt and the validated options, and, for an authenticated endpoint, the endpoint record's credential in the one mechanism the
   record names, and nothing else that the caller or the prompt supplies. No bridge logs a prompt, a reply or a credential, and none
   puts a credential in an object, a message or an argument.
   - **The endpoint record.** An endpoint is a record in the owner's guarded store, found by its name. The record format is written in
     the spec of the server bridge; this decision binds what it must hold and refuse: a name of the safe character set; a scheme of
     `http` or `https` and no other; a host and a port, with no user name, password or token in the address; whether the endpoint is
     authenticated; a location class the owner declares (this machine, the owner's network or a vendor's cloud); and a credential,
     where there is one, held in the store and never in an argument, an address, the object or a message. The transport follows the
     scheme: `https` means TLS with the server's certificate validated, and `http` means none, so there is no separate TLS field that
     could disagree with it. An authenticated endpoint must use `https`, except where the host is a literal loopback address, where
     `http` is allowed; a record that breaks this is refused. An unauthenticated `http` endpoint away from loopback is allowed, and a
     diagnostic warns that content is sent in the clear. A record that is missing, unreadable, has a field outside these rules, or names a scheme other
     than the two is refused before anything is sent, with a `refused:` line, and not turned into another endpoint or a default.
   - **Which host.** The bridge connects to the host and port the record names and to no other: an address that a redirect, a reply or
     the prompt supplies is never followed or used. The name the caller passes selects a record and is never itself an address.
   - **Tests.** The server bridge's checklist adds, against a fake server: an invalid, missing and substituted record each refused with
     nothing sent; a redirect to another host not followed; a credential or address absent from the object, the message and the
     arguments the fake saw; and the timeout ending a server that does not answer.
8. **`usage` gains the counts a program reports.** It adds `cached_input_tokens` and `reasoning_output_tokens`, each a non-negative
   whole number or `null`. `cached_input_tokens` is part of `input_tokens`, not in addition to it (in the owner's runs 15,836 input
   tokens included 12,288 cached), and the contract states that relation so that a caller does not count it twice.
   `reasoning_output_tokens` is an informational count as the vendor reports it: no caller adds it to, or subtracts it from, any other
   count, and every bridge and engine follows that rule. (Whether the vendor includes it in `output_tokens` is not decided here, so
   it is not relied on.) `total_tokens` stays `null` unless the vendor reports a total. Neither bridge derives a number the
   vendor did not report, as in version 1.
9. **One checklist for all.** The conformance checklist is run against every bridge, with a fake program for one kind and a fake server
   for the other.
10. **Embeddings are not decided here.** An embedding command is a capability of its own, with its own contract, decided when the
    Ollama bridge is planned.

This record changes decision 2 of the earlier record only where it lists the error classes and the options, and the contract text
that rests on it. The rest of that record stands. The earlier record is not edited by this one.

## Alternatives considered

- **Keep version 1 and let each bridge add its own class.** No version change, but every caller has to learn each bridge's classes, so
  the bridges are not interchangeable. Rejected.
- **Keep `program_not_found` and add `server_unreachable`.** Smaller change, but a caller that wants to know only that the vendor
  was not reachable still has to test two classes, and a future kind of bridge adds a third. Rejected in favour of one class and a
  message.
- **Ignore `--server` on a program bridge.** Fully interchangeable on paper, but a request for a local server could silently be
  served by a cloud vendor. Rejected: an option that decides where content goes is refused.
- **Make every unusable option a refusal.** Safe, but a caller could not pass the same options to both bridges, which is the
  requirement. Rejected for options that only tune behaviour.
- **Leave `--confine` as a codex-only option.** A caller sending captured text would then have to know the vendor. Rejected.
- **A separate contract for local bridges.** Two contracts for one capability name, and an engine would have to know which it holds.
  Rejected.

## Consequences

- Good: an engine or a registry can swap one bridge for the other by changing a setting, and one checklist and one set of canary
  probes cover both. A caller asks for confinement the same way from either.
- Good: the cached and reasoning counts reach the library's consumption report.
- Bad: `review-engine` and `action-review` must accept version 2 and the new class, and their tests change. A project that has an
  older engine and a newer bridge is refused until both are current.
- Bad: renaming a class is a break for any caller that matched `program_not_found`. The only callers are the first-party engines:
  `review-engine` and `action-review` each hold a fixed list of the six class names and refuse an object with any other, so both
  change, with their tests and specs. `remote-runner` uses the words only in its own refusal text and is unaffected (read on
  2026-11-01, not run).
- Bad: `--root` can be ignored, so a caller cannot tell from the object whether it took effect. The object does not say, and a caller
  that needs it chooses a program bridge.
- Bad: `--confine` is weaker than its name. A confined program still has tools, among them one that fetches a web page when its web
  tool is left on, so the exposure is the prompt's own contents. Captured text sent through a program bridge is therefore still a
  risk that the owner accepts. An Ollama bridge is the route for text that must not reach a vendor, but the bridge does not verify
  where a host is: the location class is the owner's declaration in the store record, and a record that names a remote host sends
  the text there. The guarantee is that the bridge reaches only the host the owner's record names, not that the host is on the
  machine.
- Bad: which endpoint received a call is not in the object. The caller knows the bridge and the name it passed.
- The shipped approvals of `ask-codex` and the spec change, so the owner releases the package again.
- Nothing is built by this record.

## Review record

Reviewed by Codex (`gpt-5.6-terra`) through the review engine on 2026-11-01, at the owner's request; three rounds out of a bound of
3, raised to 4 by the owner after round 3. Outcome: converged. The third round returned two major findings, both applied, and the
fourth round, which read the changed record, returned no meaningful finding.

- R1-F1 (major, applied): `--confine` had no syntax or vendor-neutral rule. Item 5 now gives both.
- R1-F2 (major, applied): the relation of `reasoning_output_tokens` to the output count was left open. Item 8 makes it an
  informational count that no caller adds or subtracts.
- R1-F3 (major, applied): the endpoint record and its constraints were undefined. Item 7 binds what it holds and refuses, and the
  tests.
- R2-F1 (major, applied): the option list omitted `--server`. Item 2 lists seven options and the grammar of `--server`.
- R2-F2 (major, applied): "nothing but the prompt" conflicted with a credential. Item 7 permits only the record's credential.
- R3-F1 (major, applied): the claim that the server bridge keeps text on the machine was too strong. The record now says the
  location class is the owner's declaration, not verified.
- R3-F2 (major, applied): scheme and TLS could disagree and a credential could travel in the clear. The transport follows the
  scheme, and an authenticated endpoint needs `https` unless the host is a literal loopback address.

The review is not an acceptance; accepting the record is the owner's act.

## Evidence

- Read `docs/specs/model-bridge.md` (contract version 1, its guarantees 1 to 8 and its checklist) and the earlier decision, at commit
  `b6c888df1b769890557526a7c190512834140563` with the roadmap candidates `bridge-confine-and-usage` and `ask-ollama-bridge` added in
  the working tree. No code was run for this record, and the conclusions are from reading.
- The owner's measurements of 2026-11-01 (`codex-cli` 0.163.0, run directly with the bridge's own safety options and through
  `ask-codex`, one run per variant, scripts not kept): with the default options the program read a file in its working directory, a
  file one directory above, a file outside the project by absolute path, listed the parent directory and ran a shell command; with
  twelve tool-adding features and the shell tool disabled, four canary probes (and a fifth, a read through the exec function) all
  failed for want of a tool. A later run of 2026-11-01 asked the confined program to list its tools: it still listed an image viewer,
  a patch tool, MCP resource readers, agent-starting functions and a web tool. In that configuration the web tool fetched a public
  page and returned its title; setting the program's `web_search` option to disabled removed it, and a repeat of the fetch failed.
  The setting `tools.view_image=false` did not remove the image viewer. A tool list is the model's own report. The figures come from
  the owner's knowledge-base project, whose spec is not tracked here, so they are quoted and not cited by path. Conclusion: a program
  bridge needs `--confine` with the web tool off, its protection depends on the program's version, and it is a tripwire plus tests and
  not a boundary.
