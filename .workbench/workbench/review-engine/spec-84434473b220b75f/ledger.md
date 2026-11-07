# Review of docs/specs/harness-refresh.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 3 of 4 rounds (ceiling 5)
- Rounds in all: 3
- Decisions recorded: 7
- Closed: no

## Rounds

- Round 1, 2026-10-28T16:43:40Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 2, 2026-10-28T16:48:00Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 3, 2026-10-28T16:49:43Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-10-28T16:44:25Z: The check warning rested on an unverified mechanism. The harness layout is not installed under the project, so check cannot translate the files. The requirement and its criterion are removed; stale...
- R1-F2: applied on 2026-10-28T16:44:25Z: Recovery could not work with the old state rules. Added an applied state tried first, so a replaced or created file that equals its staged hash is left alone and only the manifest is written; added...
- R1-F3: applied on 2026-10-28T16:44:25Z: The no-write promise was too strong. It now covers a re-read of every file and a digest rebuild before the first write; a change afterwards stops with exit 3 and is finished by a second run. No rol...
- R2-F1: applied on 2026-10-28T16:48:17Z: An owner-added allow rule would have made the permissions file read as edited and refused the whole refresh. The file is now explicitly outside the state table and keeps the rerender rules: carried...
- R3-F1: applied on 2026-10-28T16:50:04Z: The missing and orphaned rows overlapped. Orphaned is now tested before every other row, and missing means a path that is still staged.
- R3-F2: applied on 2026-10-28T16:50:04Z: A linked file with matching content could have been classed current. Every staged and listed path is now read without following links first, and a link is refused even when nothing else would change.
- R3-F3: applied on 2026-10-28T16:50:04Z: The hash-pair requirement could not hold for new and orphaned files. The criterion now shows none for a hash that does not exist.
