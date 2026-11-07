# Review of docs/decisions/2026-11-01-bridge-contract-version-2.md

This file is a rendering of state.json for people. It is never read back.

- Kind: adr
- Rounds in this window: 4 of 4 rounds (ceiling 5)
- Rounds in all: 4
- Decisions recorded: 7
- Closed: no

## Rounds

- Round 1, 2026-11-01T16:39:48Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 2, 2026-11-01T16:41:15Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 3, 2026-11-01T16:42:45Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 4, 2026-11-01T16:51:28Z: the reviewer said no_meaningful_changes, the engine read no_meaningful_changes, 0 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-11-01T16:40:17Z: Valid. The record now gives the flag syntax, a value-less flag given once, and a rule every bridge meets that does not depend on one vendor; the choice of a fixed or derived feature list stays with...
- R1-F2: applied on 2026-11-01T16:40:21Z: Valid. The reasoning count is now an informational figure that no caller adds to or subtracts from another count, so the shape is complete without relying on a fact not yet checked against the prog...
- R1-F3: applied on 2026-11-01T16:40:25Z: Valid. The record now binds what an endpoint record must hold and refuse, how the host is chosen, and the tests against a fake server; the exact record format is left to the spec of the server bridge.
- R2-F1: applied on 2026-11-01T16:41:25Z: Valid. The core now lists seven options including the server option with its grammar, and says recognizing an option is not accepting it, so a refusal by a program bridge is the same everywhere and...
- R2-F2: applied on 2026-11-01T16:41:29Z: Valid. The guarantee now allows only the endpoint record credential in the mechanism the record names, and still forbids sending anything else the caller or prompt supplies and forbids logging or e...
- R3-F1: applied on 2026-11-01T16:43:01Z: Valid. The claim that the server bridge keeps text on the machine was too strong. The record now says the bridge reaches only the host the owners store record names, that the location class is the ...
- R3-F2: applied on 2026-11-01T16:43:07Z: Valid. The transport now follows the scheme so a TLS field cannot disagree with it, an authenticated endpoint must use https unless the host is a literal loopback address, and a record that breaks ...
