# Review of docs/specs/mempalace-notes.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 3 of 3 rounds (ceiling 5)
- Rounds in all: 3
- Decisions recorded: 12
- Closed: no

## Rounds

- Round 1, 2026-11-06T15:38:58Z: the reviewer said changes_needed, the engine read changes_needed, 4 findings, model gpt-5.6-luna
- Round 2, 2026-11-06T15:40:57Z: the reviewer said changes_needed, the engine read changes_needed, 4 findings, model gpt-5.6-luna
- Round 3, 2026-11-06T15:44:11Z: the reviewer said changes_needed, the engine read changes_needed, 4 findings, model gpt-5.6-luna

## Decisions

- R1-F1: applied on 2026-11-06T15:39:43Z: The spec said only that a note is named from its title. It now fixes a normalisation rule, refuses unsafe or empty titles, never overwrites, and requires no-follow opens.
- R1-F2: applied on 2026-11-06T15:39:43Z: Update-before-create had no testable rule for the helper. save now takes an explicit into target, refuses when the text overlaps a note by word count, and records a new-despite choice.
- R1-F3: applied on 2026-11-06T15:39:43Z: The path from the owner answer to keep was missing. The spec now has drop and merge commands, a second review for a new digest, and a digest that covers the exact set keep moves.
- R1-F4: applied on 2026-11-06T15:39:44Z: Expiry had no trigger or visibility. It now runs lazily at the start of save, list, wings and review, is idempotent, and archived notes are hidden unless asked for.
- R2-F1: applied on 2026-11-06T15:41:38Z: list and read had no way to name an archived note. Both now take a state option with reviewed, draft, archived and all, with a stated default and a refusal for an ambiguous name.
- R2-F3: applied on 2026-11-06T15:41:39Z: Atomicity covered one save only. Merge, drop and keep now have an ordered write sequence, a journal for keep, retry rules, and tests that stop each operation after every step.
- R2-F4: applied on 2026-11-06T15:41:39Z: The credential scan was not testable. The spec now lists a minimum set of patterns, scans the complete note including the result of an into save, reports the line number and pattern name only, and ...
- R2-F2: applied on 2026-11-06T15:41:49Z: Real conflict: at most one ask against two confirmed commands. The spec now defines one review exchange: the summary, one owner reply, and the harness confirmations of the keep command and the fili...
- R3-F1: applied on 2026-11-06T15:44:42Z: Review and keep had no wing selector. Both now work on one wing, keep requires a wing, and the journal, lock and digest are per wing.
- R3-F2: applied on 2026-11-06T15:44:43Z: The collision check skipped the archive, so reuse of a name could replace an archived note. The check now includes the archive, and archiving adds a UTC time suffix so no entry is ever replaced.
- R3-F3: applied on 2026-11-06T15:44:43Z: Drop and merge could not name a wing or tell a title from a file name. The spec now has one note syntax, limits drop and merge to drafts, keeps merge inside one wing, and refuses a self-merge and u...
- R3-F4: applied on 2026-11-06T15:44:43Z: The new option was said to cope with equal normalised names, which it could not. A name collision is now always a refusal and the agent picks another title; the option only allows overlapping text.
