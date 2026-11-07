# Review of docs/specs/harness-rerender.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 4 of 4 rounds (ceiling 5)
- Rounds in all: 4
- Decisions recorded: 8
- Closed: no

## Rounds

- Round 1, 2026-10-27T20:29:14Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 2, 2026-10-27T20:30:59Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 3, 2026-10-27T20:32:47Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 4, 2026-10-27T20:38:49Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-10-27T20:29:28Z: The spec offered the level none but required a terminal everywhere; I now say the terminal applies at block and that none runs without one, as upgrade does.
- R1-F2: applied on 2026-10-27T20:29:28Z: Nothing tied the confirmed digest to the writes; I added a rebuild of the whole plan just before the first write, with a refusal and no writes on any difference, and a matching acceptance criterion.
- R2-F1: applied on 2026-10-27T20:31:09Z: No digest was ambiguous; I now say none needs no supplied digest but still prints the one it computed, and the goal, design and criterion agree.
- R2-F2: applied on 2026-10-27T20:31:09Z: The governing spec logs only the non-terminal route at a verified none, so I limited the logging requirement to that route and said a terminal run writes no level-log entry.
- R3-F1: applied on 2026-10-27T20:33:09Z: The read-only preview is a separate routed action and needs its own key; I added an agent-safe key for wb preview rerender and left writes to the rerender key.
- R3-F2: applied on 2026-10-27T20:33:09Z: Writing the record first could leave the record and replaced gate files agreeing while the render is half done; I reversed the order so the record is written last and any earlier failure reads as b...
- R3-F3: applied on 2026-10-27T20:33:09Z: An edit can land after the hash check; I added a per-file check just before the atomic replace and listed the remaining window under Limits instead of claiming it is closed.
- R4-F1: applied on 2026-10-27T20:41:08Z: The none level cannot work for this command because the level read returns block exactly when a re-render is needed; at your choice I made the command terminal-only, offering block only, and remove...
