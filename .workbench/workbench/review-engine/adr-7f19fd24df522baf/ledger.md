# Review of docs/decisions/2026-10-25-describe-interface-for-action-review.md

This file is a rendering of state.json for people. It is never read back.

- Kind: adr
- Rounds in this window: 4 of 4 rounds (ceiling 5)
- Rounds in all: 4
- Decisions recorded: 5
- Closed: no

## Rounds

- Round 1, 2026-10-25T23:59:50Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 2, 2026-10-26T00:01:04Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 3, 2026-10-26T00:01:53Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 4, 2026-10-26T00:22:40Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-10-26T00:00:09Z: The cap had no behaviour at the limit. The record now fixes silent-drop as forbidden, a truncated flag, and a decline when facts are incomplete, and leaves the numbers to the module spec as the bri...
- R1-F2: applied on 2026-10-26T00:00:13Z: Fair gap. Rather than invent a capability now, the record fixes the verb: the engine builds the describe command itself from a module and an action, and the existing pin check applies. That is enfo...
- R2-F1: applied on 2026-10-26T00:01:11Z: My earlier fix used a truncated signal the contract never defined. It is now a required top-level boolean, malformed if absent or not a boolean, with facts holding only whole values when it is true.
- R3-F1: applied on 2026-10-26T00:02:05Z: The spec and the record disagreed on whether a module declares describe. The owner approved the spec, so the record now requires the declaration, defers only its form to the module contract, and ke...
- R4-F1: applied on 2026-10-26T00:22:56Z: Only two fields had types. The record now types every top-level field, requires action to match the request, ties ok to an empty errors list, bounds the error and fact shapes, and treats any deviat...
