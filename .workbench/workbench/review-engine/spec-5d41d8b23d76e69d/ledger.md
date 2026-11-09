# Review of docs/specs/graphify.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 4 of 4 rounds (ceiling 5)
- Rounds in all: 4
- Decisions recorded: 13
- Closed: no

## Rounds

- Round 1, 2026-11-09T16:23:00Z: the reviewer said changes_needed, the engine read changes_needed, 5 findings, model gpt-5.6-luna
- Round 2, 2026-11-09T16:26:36Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-luna
- Round 3, 2026-11-09T16:28:38Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-luna
- Round 4, 2026-11-09T16:31:57Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-luna

## Decisions

- R1-F1: applied on 2026-11-09T16:24:45Z: The contract text governs declared writes; a helper runtime folder outside the project has precedent in mempalace-notes; the spec now says so, makes the location a stated default, and adds a plan c...
- R1-F2: applied on 2026-11-09T16:24:50Z: No gitignore slot exists in the contract; the fill is removed, the ignore file is not claimed as a fill and its delivery is left to the plan after reading the writes rule.
- R1-F4: applied on 2026-11-09T16:24:51Z: Freshness is now over the full source inventory with new, deleted and moved files making the graph stale, with tests and a file cap.
- R1-F5: applied on 2026-11-09T16:24:51Z: The helper resolves the program only from absolute PATH entries outside the repository by file identity, prints the resolved path, and a test puts a planted program in the project; no hash because ...
- R1-F3: applied on 2026-11-09T16:24:51Z: The version is read from the graph record graphify version without running the program, unknown when there is no graph, and update and doctor report the installed version.
- R2-F1: applied on 2026-11-09T16:27:34Z: The manifest and build state are now untrusted input with caps, strict parsing, key validation and an unreadable state; no field is used to open a path.
- R2-F2: applied on 2026-11-09T16:27:34Z: A graph holding non-structural nodes is foreign: queries refuse it and update refuses to write over it, so the module never mixes in or deletes a layer it does not maintain.
- R2-F3: applied on 2026-11-09T16:27:34Z: Every command that starts the program first runs it with the version flag and refuses below the floor, unparseable, or silent; status reads the graph version and warns.
- R3-F1: applied on 2026-11-09T16:29:37Z: The foreign check covers nodes and edges by origin, with a test for a non-structural edge among structural nodes.
- R3-F2: applied on 2026-11-09T16:29:38Z: The helper no longer reproduces the program ignore rules: one conservative walker takes an inventory at update and at status and compares the two, with a cross-check against the manifest, so a diff...
- R4-F1: applied on 2026-11-09T16:32:54Z: Every invocation of the program is captured with separate stdout and stderr caps, a time limit, process group kill and a one-line failure state, with tests for oversized output.
- R4-F2: applied on 2026-11-09T16:32:54Z: inventory.json is now untrusted input with size, entry, schema and path caps and an unreadable state, listed in the acceptance tests.
- R4-F3: applied on 2026-11-09T16:32:54Z: The provenance schema is stated exactly from the scratch and surveyed graphs:  origin is the layer and only the text ast is structural, confidence is a separate edge field, and tests cover each form.
