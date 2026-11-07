# Review of docs/decisions/2026-10-29-approvals-name-the-approver-by-git-identity.md

This file is a rendering of state.json for people. It is never read back.

- Kind: adr
- Rounds in this window: 2 of 3 rounds (ceiling 5)
- Rounds in all: 2
- Decisions recorded: 5
- Closed: no

## Rounds

- Round 1, 2026-10-29T14:59:30Z: the reviewer said changes_needed, the engine read changes_needed, 4 findings, model gpt-5.6-terra
- Round 2, 2026-10-29T15:03:34Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-10-29T15:01:23Z: Git does not verify who owns an email, so calling it unique overstated the guarantee. The record now calls the identifier an unverified attribution label and says the email is only the part most li...
- R1-F2: applied on 2026-10-29T15:01:23Z: A cleaned environment was too vague to show that project configuration is excluded. The record now gives the exact two commands, the working directory, the minimal environment, the dropped git vari...
- R1-F3: applied on 2026-10-29T15:01:23Z: The grammar, normalization and length were left open although the record requires strict formats. The record now sets the name and email rules, a 210 character stored form, a 256 character field, c...
- R1-F4: applied on 2026-10-29T15:01:23Z: The example used a real personal identity that the format does not need. I replaced it with a placeholder in every example in the record.
- R2-F1: applied on 2026-10-29T15:03:42Z: The email rule banned a space but not tabs, line breaks or other control characters, which would break the one-line sentence and allow output injection. The email is now a positive set of printable...
