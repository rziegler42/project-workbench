# Review of docs/specs/action-review.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 3 of 3 rounds (ceiling 5)
- Rounds in all: 3
- Decisions recorded: 7
- Closed: no

## Rounds

- Round 1, 2026-10-26T00:03:30Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 2, 2026-10-26T00:05:32Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 3, 2026-10-26T00:07:05Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-10-26T00:04:04Z: The claim that the model reads only the facts was false given what the bridge allows. The spec now states the real exposure, stores the labelled data outside any project, claims no isolation, and a...
- R1-F2: applied on 2026-10-26T00:04:07Z: The binding from the hook command to the describe arguments was unspecified. The spec now defines one canonical form: single simple command only, one parse by the rule flags, an argument list to de...
- R1-F3: applied on 2026-10-26T00:04:10Z: The engine had no settings contract although the accepted bridge decision requires one. The spec now incorporates it: a project file, the owner setting winning, refusal for an uninstalled or unpinn...
- R2-F1: applied on 2026-10-26T00:05:40Z: The rule field for describe could be read as command text. Rules now hold a module and an action only, and the engine builds the launcher argument list with the fixed verb.
- R2-F2: applied on 2026-10-26T00:05:43Z: The criterion required a describe for every row, including retired actions that have none. It now covers only the retained actions, with separate criteria that the retired ones have no provider and...
- R3-F2: applied on 2026-10-26T00:07:25Z: Tokenizing was left undefined and a sample corpus cannot prove equivalence. The spec now states an exact restricted grammar of safe bare words and single-quoted strings, refuses everything else, an...
- R3-F1: applied on 2026-10-26T00:07:30Z: Partly. The spec now fixes the rule properties: a format number, whole-token keys, refusal of duplicate or malformed rules for their own key only, and typed flags. The full versioned JSON schema is...
