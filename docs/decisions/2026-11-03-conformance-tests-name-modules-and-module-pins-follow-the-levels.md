# Two conformance tests may name the modules they read, the installer keeps no pairing of module-owned names, and a module's text pins follow the owner's levels

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-03
Date: 2026-11-03

## Context

A full run of the tests on 2026-11-03 (`python3 -B -W error tests/run_all.py`, 7,018 tests in 14 roots, commit `76d7294`) failed
in 15 places that pass on the base commit `76df744`. Six are in the repository's own tests, seven in the `code-work` module's tests and
two in the `review-engine` module's; the plan `2026-11-03-full-suite-regressions-of-the-permission-plan` repairs them, and its
increment A removed the ones that needed no decision (the kit file and the self-hosting record). What is left raises three
questions that change a rule of the owner's or a pin a module keeps, so they are decided here and not in code.

**1. The boundary rule and the tests that read the real package.** `tests/test_boundary.py` holds that the installer and its tests name
no first-party module, helper, command, harness or harness path (`module-boundary.md`: tests use made-up names). It scans
`workbench/` and `tests/` for every word that the `module.json` files of `packages/` give. After increment A it finds 90 places:

| File | Places | What names the modules |
|---|---|---|
| `workbench/levels.py` | 1 | `PAIRED_ACTS` (question 2) |
| `tests/test_levels_facts.py` | 36 | the facts of the real registry |
| `tests/test_permissions_drift.py` | 23 | it reads the real package against the registry, the specs and the skills |
| `tests/test_doctor.py` | 14 | module names in labels and in the list of declared prompts |
| `tests/test_command_gate.py` | 13 | examples with a real module command |
| `tests/test_gate_corpus.py` | 3 | the same |

Two of these files exist to read the shipped package: the drift test (the registry against the declarations, the documents and the
skills) and the facts test (what the registry says of each real key). Their purpose cannot be met with made-up modules, because the
claim they make is about the real ones. The other three name modules only as examples, and made-up names do the same job.

**2. A pairing of two module-owned names in the installer.** `workbench/levels.py` keeps `PAIRED_ACTS`, which says that the checkpoints
`submit-remote-job` and `fetch-remote-output` and the commands `wb run remote-runner submit` and `fetch` do the same acts and keep a level
each (decision 5 of `2026-11-02-one-permission-registry-and-key-model`: the registry records the pair on both keys, `paired_with`). It
names a module, so the boundary test refuses it. Read on 2026-11-03 with a search of the source and the tests: nothing in the
installer reads `paired_with` while it runs. Only `tests/test_levels_facts.py` reads it, and the drift test keeps its own copy of the pairs
(`CHECKPOINT_PAIRS`). The pairing is information about modules. Whether the pairs are merged is for the follow-on plan
`2026-11-02-permission-levels-for-every-command`, which may give a module a declared field for it. `STATED_BY` (the skills that state a
checkpoint) names skills, not modules, and the boundary test does not flag it.

**3. The pins a module keeps on its own text.** Increment K rewrote the `delegate-approval`, `draft-plan`, `run-increment` and
`peer-review` skills and the `code-work` policy block so that they state the owner's levels (the plan
`2026-11-02-permission-system-consistency`). Each module's tests pin its text. Nine assertions fail:

| # | Module and test | What the assertion pins | What K's text does |
|---|---|---|---|
| 1 | `code-work`, `test_the_only_wb_commands_named_are_the_two_it_runs_each_in_backticks` | the delegate skill names exactly two commands, each once, in backticks | a rule names `wb delegate-approve-plan` without its argument, a third spelling |
| 2 | `code-work`, `test_the_text_carries_the_phrases_of_the_routine` | the delegate skill carries the phrase `checkpoint approve-plan: delegate` | it reads `level approve-plan: delegated`, the line the delegate command honours |
| 3 | `code-work`, `test_draft_plan_and_run_increment_name_it_and_still_leave_the_approval_to_the_owner` | `draft-plan` says "only the owner makes with the approve-plan command" | it says the owner's statement makes it and the command's level decides how |
| 4 | `code-work`, `test_the_skill_states_the_naming_the_header_the_labels_and_that_only_the_owner_approves` | the same phrase | the same |
| 5 | `code-work`, `test_no_skill_file_runs_a_command_beyond_the_plan_check_or_names_a_tool` | the plan-drafting skill runs one command, `wb run code-work check` | step 8 runs `wb settings`, `wb plan-status` and `wb approve-plan` at the owner's level |
| 6 | `code-work`, `test_the_policy_block_is_short_and_names_no_tool` | at most 32 lines, no harness or vendor named | 38 lines, no harness or vendor named |
| 7 | `code-work`, `test_the_policy_block_says_every_checkpoint_stops_and_a_cap_stops_a_run_and_where_to_read_them` | the block does not contain "delegate" | it names the `delegated` level and the `delegate-approval` skill |
| 8 | `review-engine`, `test_it_states_the_rules` | the skill says the five owner commands "are the owner's" and "Never run them" | it says they take the owner's level and gives the `ask` flow |
| 9 | `review-engine`, `test_the_commands_it_runs_are_the_engines_and_the_owner_ones_are_only_named_as_the_owners` | the engine commands the skill runs are `init`, `status`, `review-plan` and `decide` | `preview` is added (the `ask` flow runs it first) |

The `groundwork` policy block already names `wb settings` and its preview command and carries the `ask` flow for `accept-decision`, and its
skill repeats it: the pattern exists. The `code-work` block's length limit has been raised before for required content (the comment in the test:
23 lines, then the testing and security-review bullets took 3 and 6).

## Decision

Proposed; the owner decides. Nothing here is built; the plan `2026-11-03-full-suite-regressions-of-the-permission-plan` builds it
(increments C and D).

1. **Two conformance tests are exempt from the boundary scan, by exact path.** `tests/test_levels_facts.py` and
   `tests/test_permissions_drift.py` read the real package on purpose and may name its modules; `tests/test_boundary.py` lists the two
   paths with this reason, as it already skips `tests/fixtures` and `workbench/shipped_approvals` by exact path. No file under
   `workbench/` is exempt, and no other test is: `test_doctor.py`, `test_command_gate.py` and `test_gate_corpus.py` are reworded to made-up
   module names, as `module-boundary.md` says. A new test that reads the real package is a decision of the owner, not an edit of the list
   by the author.
2. **The installer keeps no pairing of module-owned names.** `PAIRED_ACTS`, `_PAIRED_BACK` and the field `paired_with` are removed from
   `levels.py`. The pairs remain where modules may be named: `CHECKPOINT_PAIRS` in the drift test, which checks that no pair is left
   unrecorded, and the spec. The two checkpoints and the two commands keep a level each, as decision 5 of the registry record settles; this
   record changes only where the pairing is kept. Whether to merge the pairs, and with what declared field, is for the follow-on plan.
   `STATED_BY` stays.
3. **The module pins follow the owner's levels, one assertion at a time.** For each of the nine:
   - Text fixed, pin kept: **1** (write the command with its argument, `wb delegate-approve-plan <plan>`, so the delegate skill still
     names two commands) and **7** (the block says nothing of delegation; the `delegate-approval` skill is where it is said, and the block
     keeps the `block`, `ask` and `none` flows).
   - Pin updated to the phrase that is now true, its purpose kept: **2** (the line the delegate command honours is `level approve-plan:
     delegated`), **3** and **4** (the approval stays the owner's explicit statement and the skill still says so; the phrase pinned is now
     "Approval is the owner's explicit statement" and that the record follows the owner's saying to approve), **8** (the five commands take the
     owner's level: at `block` the owner's, at `ask` the preview and the digest, at `none` the agent runs it).
   - Limit raised with its reason: **5** (the plan-drafting skill runs the plan check, and in step 8 only, once the owner has said to
     approve, `wb settings`, `wb plan-status` and `wb approve-plan`; no other command and no raw git, as before), **6** (the block's limit
     goes from 32 lines to 40; it still names no harness or vendor), **9** (the commands the skill runs gain `preview`).
   - Every other pin in those modules stands: no harness, vendor or tool named, no raw git, a commit only through the git helper, the
     skill's length limits and the pins on the plan-drafting routine.

## Alternatives considered

- **Rewrite the drift and facts tests with made-up modules.** Rejected: they would stop checking the real package, which is their claim.
- **Exempt every test, or the whole `tests/` directory, from the boundary scan.** Rejected: the rule exists to stop the installer's tests
  growing a knowledge of modules; a short list by exact path is the narrowest change that lets two tests do their job.
- **Exempt `workbench/levels.py`.** Rejected: it is the installer's own source, where the rule matters most.
- **Declare the pairing in the module now (a field on the command, read by the registry).** Not chosen, and this reverses the
  recommendation the plan's increment B first gave: nothing reads `paired_with` at run time, and the follow-on plan decides whether to merge
  the pairs and with what mechanism. A field built now would likely be reshaped there. It stays a possibility for that plan.
- **Move the approval flow into a new skill and keep `draft-plan` as it was.** Rejected: it adds a shipped skill and a pin set to keep the
  old sentences true, and leaves the policy block, which the drift test reads for the flow, to repeat it; the `draft-decision` skill and the
  `groundwork` block already repeat their flow.
- **Shorten the block to a pointer ("`wb settings` says how; the skill gives the flow").** Rejected: the drift test requires a text that
  names an `ask` key to state the flow, and the `groundwork` block states it.
- **Revert increment K.** Rejected: the skills would again say "never run" a key the owner has set to `ask`.

## Consequences

- Good: the full suite can pass without weakening what a conformance test claims, and without a new mechanism.
- Good: nine pins change on the record, each with its reason; the rest of the modules' pins, which protect the way of working, stand.
- Good: the installer's source names no module again, and the registry loses a field nothing used.
- Bad: the boundary test now has a list. Two files may name modules, and the list can grow by a decision of the owner only if the owner
  keeps that practice.
- Bad: the pairing is no longer a fact the registry can print. A reader who wants it reads the spec or the drift test; the follow-on plan may
  restore it as a declared field.
- Bad: the module tests now describe a code-work skill that runs the installer's approval commands. That is what the owner's levels need, and
  it changes what the module says of itself.
- Neutral: this record does not change a level, a default or a key.

## Evidence

Run on 2026-11-03 at commit `e18b4cb` (after increment A), workbench 0.1.0, Python 3.15.0. The full run
(`python3 -B -W error tests/run_all.py`, written to a file, exit 1) reported 7,018 tests in 14 roots; the failing roots were `tests`
(6 failures), `packages/workbench/code-work/tests` (7) and `packages/workbench/review-engine/tests` (2). The same seven test files, run on an
extract of the base commit `76df744` in a scratch directory, passed. A scratch script that called the boundary scan
(`test_boundary.scan` with `support_words.sources()`) printed 97 violations before increment A and 90 after, by file as the table above
(36, 23, 14, 13, 3 and one in `levels.py`) and by word (`remote-runner` 27, `safe-git` 17, `review-engine` 15, `groundwork` 14,
`code-work` 12, then `freecad`, `verilog`, `mempalace` and `security-review`). A search of `workbench/` and `tests/` for `paired_with`,
`PAIRED_ACTS` and `_PAIRED_BACK` found only `levels.py` and `tests/test_levels_facts.py`. The nine assertions were read in
`packages/workbench/code-work/tests/test_codework_delegateskill.py`, `test_codework_module.py` and
`packages/workbench/review-engine/tests/test_review_module.py`. Not run: any change; whether other module test roots pin text that this
record's text changes touch (the full run says no, for the roots that passed).

## Related files and decisions

- `docs/plans/2026-11-03-full-suite-regressions-of-the-permission-plan.md`
- `docs/plans/2026-11-02-permission-system-consistency.md` (Result, "Reopened after the full suite")
- `docs/specs/module-boundary.md`, `docs/specs/command-permissions.md`
- [2026-11-02-one-permission-registry-and-key-model](2026-11-02-one-permission-registry-and-key-model.md) (decision 5, narrowed in what the registry records)
