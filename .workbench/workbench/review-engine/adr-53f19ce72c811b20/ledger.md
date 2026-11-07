# Review of docs/decisions/2026-10-26-per-command-permission-levels.md

This file is a rendering of state.json for people. It is never read back.

- Kind: adr
- Rounds in this window: 3 of 3 rounds (ceiling 5)
- Rounds in all: 3
- Decisions recorded: 5
- Closed: no

## Rounds

- Round 1, 2026-10-26T15:47:07Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 2, 2026-10-26T15:48:52Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 3, 2026-10-26T15:52:45Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-10-26T15:47:26Z: Checked against the installer spec: the command needs no terminal, so the context was wrong. Corrected it and moved the command to a block default because it writes shipped trust records.
- R2-F1: applied on 2026-10-26T15:49:31Z: Real ambiguity. Defined the table key as the checkpoint name or the wb command spelling, gave a strictness order for a command reaching several keys, and split the two acknowledge tiers into their ...
- R2-F2: applied on 2026-10-26T15:51:35Z: Correct: no agent-run preview digest is specified for most of these. An ask default now ships only once its spec names the command form and digest; until then the default stays block and ask is onl...
- R3-F1: applied on 2026-10-26T15:53:00Z: Fair: the table used informal names. It now uses the wb spelling for commands and the checkpoint names for checkpoints. This edit was not reviewed again, since the rounds are used up.
- R3-F2: rejected on 2026-10-26T15:53:06Z: The decision skill lets an accepted record change only its status line to name its successor, after the new one is accepted, and the owner agreed to that wording. Left as written, with a fallback n...
