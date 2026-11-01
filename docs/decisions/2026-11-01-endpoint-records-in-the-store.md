# Endpoint records for a bridge to a server live in one owner file in the guarded store

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-01
Date: 2026-11-01

## Context

The accepted decision `2026-11-01-bridge-contract-version-2` lets a bridge call a server and says that the server is a named
record in the owner's guarded store, chosen by `--server <name>`, never an address in an argument, an environment variable or a
tracked file, with a safe name, a scheme of `http` or `https`, a host and a port, whether it is authenticated, a location class the
owner declares, and a credential held in the store. It leaves the exact place and format of the record to the spec and the plan that
build the first bridge to a server (`docs/plans/2026-11-01-ask-ollama-bridge.md`). `2026-10-20-fixed-store-location` fixes the store
at `~/.config/project-workbench/` and lets nothing move it: no variable, no option, no file.

Three facts bound the choice:

- A helper has no sanctioned way to read the store. The review engine reads its own seal key and marks from
  `projects/<id>/review-engine/` by a fixed path under the home directory, through the kit's no-follow layer, "because the kit has no
  store accessor", and says that a kit accessor is a kit change with a new API number, deferred (`docs/specs/review-engine.md`, "The
  seal").
- The store is a mechanical barrier under the owner's account. The harness denies the agent writes to it and does not make it
  unreadable (`docs/specs/review-engine.md`, "The seal"). Anything the agent must not read cannot be kept there.
- The store creates what is missing and changes nothing else (`workbench/store.py`, the module docstring), and a file directly in its
  root already exists: on 2026-11-01 the root held `bin`, `cache`, `level-log`, `packages`, `projects`, `settings` and `settings.bak`.
  A further file in the root is therefore tolerated; that is an inference, because `workbench/store.py` checks the directories it
  makes and has no scan for other entries.

## Decision

1. **One file, `endpoints.json`, directly in the guarded store** (`~/.config/project-workbench/endpoints.json`), for the whole
   account. It is not per project: an endpoint is one of the owner's machines, and a per-project record would have to be repeated
   for each project and clone. The owner writes it by hand. The agent cannot write the store, and no command writes it in the plan
   that builds the first bridge; a command to write and check it is deferred.
2. **Its format.** Strict JSON (no duplicate key, no `NaN`, as `wbkit.jsonstrict` reads it), one object, at most 65,536 bytes, with
   exactly `format` (the integer 1), `endpoints` (an object of at most 64 records, each named by 1 to 32 characters of `a-z0-9_-`
   that start with a letter or a digit) and optionally `default` (the name of one of those records; a `default` that names no
   record makes the file invalid). A field not listed here is refused, and so is a missing required one. Every number in the file
   is a JSON integer: a boolean or a float is never accepted in place of one.
3. **A record** holds exactly these fields, and no other:
   - `scheme`: `http` or `https`.
   - `host`: one of three forms and no other.
     - *An IPv4 literal*: four decimal numbers from 0 to 255, separated by dots, each without a leading zero (the number 0 is
       written `0`). Addresses in `0.0.0.0/8` (the unspecified address and "this network"), `224.0.0.0/4` (multicast),
       `240.0.0.0/4` (reserved, with the broadcast address `255.255.255.255`) and `169.254.0.0/16` (link-local) are refused: a
       server is never there, and `169.254.169.254` is a cloud metadata address.
     - *An IPv6 literal*: groups of 1 to 4 lower-case hexadecimal digits separated by `:`; written in full it has exactly eight
       groups, and with one `::`, which stands for one or more omitted groups of zeros, it has at most seven; there is no
       dotted-decimal tail, no bracket and no zone. The unspecified address `::`, an IPv4-mapped address (`::ffff:0:0/96`), a
       multicast address (`ff00::/8`) and a link-local address (`fe80::/10`) are refused. The grammar is these words and not a
       library's judgement; a test may compare the two, and a disagreement is a defect in one of them.
     - *A DNS name*: at most 253 ASCII characters in lower case, in labels of 1 to 63 letters, digits and hyphens that neither start
       nor end with a hyphen, with no trailing dot and no underscore, whose last label is not all digits and is not `0x` followed
       by zero or more hexadecimal digits. The last rule is there because a resolver may read a string such as `127.1`,
       `2130706433`, `0177.0.0.1`, `0x7f.0x1` or `0x0` as the number it spells, and the standard library's parser does not: in the
       measurement below the library refused all of them and the resolver's `inet_aton` read each as an address. Resolvers differ
       in what they read (the one measured refused a bare `0x` and the others may not), so the rule refuses every form. A host made of
       digits and dots is therefore valid only as an IPv4 literal.
     A host with a delimiter (`@`, a `:` outside an IPv6 literal, `/`, `?`, `#`, `\`, a bracket), whitespace, a control or non-ASCII
     character, upper case, an empty label or a zone identifier is refused.
   - `port`: a whole number from 1 to 65535.
   - `location`: `this-machine`, `owner-network` or `vendor-cloud`. It is the owner's declaration and is not verified.
   - `authenticated`: a boolean. In the plan that builds the first bridge it must be `false`: a record that says `true` is refused
     before anything is sent, with a message that says authentication is not supported yet.
   - optionally `default_model` and `embedding_model`: 1 to 128 characters of letters, digits and `._:-`, with `/` between
     segments, each segment starting with a letter or a digit, and no `//`, no `..` and no leading or trailing `/`.
   - optionally `context`: a whole number of tokens from 1 to 10,000,000, the server's context window for that endpoint.
   A record holds no credential, no path and no URL.
4. **Loopback** means an IPv4 literal in `127.0.0.0/8` or any spelling of the IPv6 address whose value is 1 (`::1`, `0::1`,
   `0:0:0:0:0:0:0:1`, `::0001`), and nothing else: no name (`localhost` is a name, and a name is resolved by the machine, not by
   the bridge) and no IPv4-mapped form. The rule does not call a library predicate for its meaning, so it does not depend on the
   version of Python.
5. **How a bridge reads it.** By the fixed path under the home directory, through the kit's no-follow layer, as the review engine
   reads its key. A missing file, an unreadable file, a link, a file that is not a regular file, a file over the bound, a file that
   is not strict JSON of this format, a record outside these rules, and a `default` that names no record are each refused before
   anything is sent, with a `refused:` line that names the rule and never the value. The file is read again on every call. A bridge does not repair, default or skip a
   bad record: the whole file is refused. If a bad record were skipped, a call that named it could fall to the `default` record, or
   a typo in a name could pass for a different record, and text would go somewhere the owner did not choose.
6. **The harness asks before the agent reads it.** The module of a bridge to a server declares `ask_reads` for this file, as
   `ask-codex` does for its login file (`packages/workbench/ask-codex/module.json`: `"ask_reads": ["~/.codex/auth.json"]`). This is
   the existing mechanism and adds no rule.
7. **Which record a call uses.** `--server <name>` names a record; without it the `default` record is used; with neither the call is
   refused, and a name that no record carries is refused (a `default` that names no record has already made the file invalid, item
   2). The name is only a key and is never an address.
8. **What this decision does not do.** It adds no kit accessor, no launcher feature and no declaration field. It does not support
   authenticated endpoints and does not say where a credential would live. It narrows the accepted contract decision, which lets an
   authenticated record exist, by declining to support one until a credential has a decision of its own. A later decision that lifts
   the refusal must keep the rule of the contract decision that an authenticated endpoint uses `https`, except on a literal loopback
   address.

## Alternatives considered

- **A kit accessor for the store.** One sanctioned way to read it, and the review engine could use it too. Rejected for now: it is a
  kit change with a new API number, for one record. The review engine's precedent already shows the cost of waiting, and the
  accessor stays deferred, as that spec says.
- **The launcher passes the record to the helper.** The helper would not read the store at all. Rejected: it would need a new
  declaration field, a launcher change, a pin and several specs and tests, and the launcher's channels are arguments and an
  environment, the very channels the fixed-store decision refuses for an address.
- **An environment variable or an option for the address.** Rejected by `2026-10-20-fixed-store-location`: an agent sets it for one
  command and points the bridge at a host it picks.
- **A record in the project, tracked.** Rejected by the same decision, and because an address would then sit in a tracked file
  (`2026-11-01-bridge-contract-version-2`).
- **A per-project record in `projects/<id>/`.** Keeps endpoints with the project's other store data. Rejected: the endpoints are the
  owner's machines, the project id differs for each clone, and the same list would have to be kept in each.
- **A credential in the file.** Needed for an authenticated server. Rejected for now: the agent can read the store, so the
  credential would not be protected from it; a reference to a credential held elsewhere is a separate decision.
- **Silently skipping a bad record.** Rejected for the reason in item 5.
- **Letting the standard library decide the host forms and loopback.** Less to write. Rejected: it accepts and refuses by its
  version (in the measurement below an IPv4-mapped loopback address counted as loopback), and the resolver reads numeric forms that
  the library refuses.

## Consequences

- Good: no kit, launcher or declaration change; the format is small and strict, so every refusal is testable; the harness asks before
  the agent reads the addresses; and a typo in one record stops the call instead of sending text somewhere else.
- Bad: the helper reads the store by a hand-coded path, as the review engine does. That is a precedent and not a sanctioned
  accessor, and it couples the helper to the store's root layout. It is one more reader to move when the accessor is built.
- Bad: the owner edits a file by hand, with no command to write it or to check it other than the bridge's own refusals. The plan
  adds a read-only `check` command to the bridge that prints each record without its host or port, and warns about a plain `http`
  record away from loopback. That command is where the diagnostic that the contract decision requires lives; a call does not warn,
  because a call prints one object.
- Bad: the agent can read the addresses with a shell command, because the store is not unreadable to it. `ask_reads` makes a harness
  ask before a file read, not before every route.
- Bad: no authenticated server can be called until a credential has a decision. A server behind a token cannot be used.
- Bad: the contract's `--model` allows at most 64 characters of `A-Za-z0-9._:-` and no `/`, and the record's model fields allow 128
  characters and a `/` between segments, because Ollama model names can carry a namespace. A model of that kind can be named only by
  `default_model` or `embedding_model`, not by `--model`, until the contract's charset is widened by a later change.
- Bad: a bad record anywhere in the file stops every call, including calls to a good record. That is the point of item 5, and it
  costs an owner's typo in one record the use of the others until it is fixed.
- Bad: private addresses and names are accepted, as an owner's network needs; only the addresses a server is never at are refused. A
  record can still point at any reachable host the owner names, and `location` is the owner's word, not checked.

## Open questions

- Whether the contract's `--model` charset should allow `/` between segments and more than 64 characters, so that a namespaced model
  can be named in a call.
- Where a credential would live so that the agent cannot read it, and what a reference to it is.
- Whether a kit accessor for the store should be built, now that a second reader exists.

## Evidence

- Read at commit `d581df4060645d2c43829eaf8abfc27b18d43628`: `docs/decisions/2026-10-20-fixed-store-location.md`,
  `docs/decisions/2026-11-01-bridge-contract-version-2.md`, `docs/specs/review-engine.md` ("The seal": the helper reaches the guarded
  store by the fixed path, through the kit's no-follow layer, because the kit has no store accessor; the harness denies the agent
  writes to the store and does not make it unreadable), `docs/specs/model-bridge.md` (guarantee 7 and the `--model` charset) and
  `workbench/store.py` (the location, the layout, and that `ensure` creates what is missing and changes nothing else).
- The listing of the store root on 2026-11-01 (`ls -A ~/.config/project-workbench`, the system `ls` on macOS, Darwin 25.6.0, run
  from zsh by an agent): `bin cache level-log packages projects settings settings.bak`. A file in the root is therefore normal. The
  files named above were read with the agent's file reader, and the standard library and `inet_aton` measurements ran in the same
  environment.
- Measured on 2026-11-01 with Python 3.15.0 on macOS (two short runs, scripts not kept): `ipaddress.ip_address` refused `127.1`,
  `2130706433`, `0177.0.0.1`, `0x7f.1`, `0x7f.0x1`, `127.00.0.1`, `0`, `00`, `0x0` and `999.999.999.999`; `socket.inet_aton` read
  all of those except the last as an address (`127.0.0.1` for the first seven, `0.0.0.0` for `0`, `00` and `0x0`) and refused
  the last; it refused a bare `0x`, `a.0x`, `0x7f.0x` and `1.2.3.4a`, and the library refused those too. `0.0.0.1` and `240.0.0.1`
  were valid to both. `::ffff:127.0.0.1` and `::FFFF:7F00:1` were IPv4-mapped and `is_loopback` was true for both; `0:0:0:0:0:0:0:1`,
  `0::1`, `0000::0001` and `::0001` all parsed and were loopback; `0.0.0.0` was unspecified, `169.254.169.254` link-local,
  `224.0.0.1` multicast, `255.255.255.255` reserved and `fe80::1` link-local, as the library defines them. Conclusion: the host
  grammar and the loopback rule above are written out in words and not by these predicates, so they do not change with the version
  of Python, and the resolver's wider reading of numbers is why a name may not end in a numeric label.
- An agent investigating the kit, the launcher and the store records reported on 2026-11-01 that it found no store accessor, no
  launcher feature that passes a store value to a helper, and no record type for an endpoint. The author did not re-read the
  launcher, and the rejection of the launcher alternative above does not depend on that report: it would need a new feature in any
  case.
- No part of the Ollama server is involved in this record. The format and the bounds are this record's own choice.

## Related files and decisions

- `docs/plans/2026-11-01-ask-ollama-bridge.md`
- `docs/specs/model-bridge.md` (guarantee 7: the endpoint record), `docs/specs/review-engine.md`, `docs/specs/module-boundary.md`
- [2026-10-20-fixed-store-location](2026-10-20-fixed-store-location.md)
- [2026-11-01-bridge-contract-version-2](2026-11-01-bridge-contract-version-2.md)
