# Review of docs/decisions/2026-11-04-review-profiles-in-the-guarded-store.md

This file is a rendering of state.json for people. It is never read back.

- Kind: adr
- Rounds in this window: 2 of 3 rounds (ceiling 5)
- Rounds in all: 2
- Decisions recorded: 3
- Closed: no

## Rounds

- Round 1, 2026-11-04T18:36:03Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 2, 2026-11-04T18:38:19Z: the reviewer said no_meaningful_changes, the engine read no_meaningful_changes, 0 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-11-04T18:36:35Z: Real gap in item 10: a record with no default model made no profile but the Ollama ladder still named it. The ladder is now written only when the local profile exists, and the install says the owne...
- R1-F2: applied on 2026-11-04T18:36:40Z: Real gap in item 3: a declaration could have let a profile supply the engine-owned timeout or schema, defeating the action-review time limit. Item 3 now reserves model, effort, timeout, schema, roo...
- R1-F3: applied on 2026-11-04T18:36:51Z: Real conflict in item 5: a multi-rung default ladder could apply to action-review, which must hold one rung. The default ladder is now for the four document kinds only, and action-review needs a la...
