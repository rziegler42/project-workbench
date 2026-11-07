# Review of docs/specs/command-permissions.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 3 of 3 rounds (ceiling 5)
- Rounds in all: 3
- Decisions recorded: 5
- Closed: no

## Rounds

- Round 1, 2026-10-26T16:04:05Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 2, 2026-10-26T16:05:02Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 3, 2026-10-26T16:06:30Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-10-26T16:04:22Z: Right: the digest steps named none by mistake. They now apply to ask only, and none has its own short rule with no preview and a log entry.
- R1-F2: applied on 2026-10-26T16:04:29Z: The four review keys were bare names that the spec own key rule would reject. They now use the full wb spelling.
- R1-F3: applied on 2026-10-26T16:04:34Z: Fair: block assumed a terminal that one command does not have. It now means the harness denies the agent, with the terminal test only where the command has one today.
- R2-F1: applied on 2026-10-26T16:05:11Z: The criterion contradicted the accepted ask defaults. It now keeps the safety controls fixed, says nothing changes before the two keys are built, and says what changes after.
- R3-F1: applied on 2026-10-26T16:07:04Z: Correct: nothing a command could trust said the harness was attached and rendered. Added an attach-written record in the guarded store with a table digest, and every key fails closed to block witho...
