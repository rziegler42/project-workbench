# Review of docs/specs/clone-enrollment.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 4 of 4 rounds (ceiling 5)
- Rounds in all: 4
- Decisions recorded: 8
- Closed: no

## Rounds

- Round 1, 2026-11-15T15:02:39Z: the reviewer said changes_needed, the engine read changes_needed, 4 findings, model gpt-5.6-luna
- Round 2, 2026-11-15T15:04:47Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-luna
- Round 3, 2026-11-15T15:06:13Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-luna
- Round 4, 2026-11-15T15:08:29Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-luna

## Decisions

- R1-F1: applied on 2026-11-15T15:03:28Z: The fallback through the module flag is removed. The spec now says the commands run through the launcher, which an earlier setup step creates.
- R1-F2: applied on 2026-11-15T15:03:29Z: The spec now says this is the one command that needs the project to be unknown, handles one entry or a malformed entry, and writes both entries only after every check has passed.
- R1-F3: applied on 2026-11-15T15:03:29Z: The spec now covers slot blocks: how a block is found and compared, that a differing block is listed and not refused, and that its file gets one baseline of its whole bytes. Acceptance cases were a...
- R1-F4: applied on 2026-11-15T15:03:29Z: The title was misspelled by my own respelling script and is fixed.
- R2-F1: applied on 2026-11-15T15:05:06Z: The baselines written now include the manifest file itself, and the first acceptance case checks that the preview of the later command lists no difference for it.
- R2-F2: applied on 2026-11-15T15:05:06Z: I read the installer code: the block hash covers both marker lines and the text, with line endings. The spec now says so and names the scanner.
- R3-F1: applied on 2026-11-15T15:06:25Z: Check 3 now requires the strict manifest reader and the path and ownership rules for every recorded entry, with a refusal before any store write, and the third acceptance case covers it.
- R4-F1: applied on 2026-11-15T15:08:34Z: The first acceptance case now says the first run of the workbench has already written the store and the launcher, and it asserts no write for the project beyond that.
