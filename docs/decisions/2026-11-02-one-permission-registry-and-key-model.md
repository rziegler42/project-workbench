# The permission system has one registry, three danger classes and one rule for which mechanism governs

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-02
Date: 2026-11-02

## Context

The permission system was decided in pieces, each accepted, and built in pieces. The accepted records are:

- `2026-10-26-a-level-for-every-command`: every command has a key; no key is limited to `block` (decision 3); the settings table is
  the single source of a level and wins over a checkpoint word in either direction (decision 5); there is no master profile that
  turns every protection off (decision 4).
- `2026-10-27-owner-run-arguments-take-a-level`: a module declares `levels` and a `preview` for an owner-run argument.
- `2026-10-27-rerender-is-terminal-only`: `wb rerender` offers `block` only and always needs a terminal, the one exception to
  decision 3 beside the module arguments that had not yet been given a level.
- `2026-10-28-every-key-offers-the-approve-plan-levels`: the eight checkpoint and command keys offer the levels `approve-plan`
  offers; a checkpoint that runs no command is a rule the agent follows.
- `2026-10-29-workbench-asks-for-remove-submit-and-fetch`: a module may declare `asks`, a prompt the harness renders for an
  argument whatever the argument's level.

Three mechanisms now govern the same acts, and no record says which one wins when they meet: a **level** (the owner's table), a
**checkpoint** (a named stop; a command, or a rule the agent follows) and an **`asks`** (a module's declared minimum prompt).
`submit-remote-job` and `wb run remote-runner submit` are one example: the checkpoint reads `block`, the command's key reads
`none`, and the module's `asks` renders a prompt anyway. The owner's settings file shows the same overlap in a second place: a
`checkpoints` word (the form a version 1 file uses, still read in a version 2 file) beside a `levels` entry for `approve-plan`;
decision 5 already says the table wins, so that case is decided, but the seed (`workbench/settings.py`, `_seed_document`) still
writes an empty `checkpoints` object into every new file.

The facts about a key (what it is, what levels it offers, its default, its spellings, its preview, the command or rule it governs,
where it is documented) are kept by hand in `workbench/levels.py` (`_OFFERS`, `_DEFAULTS`), `workbench/rules.py` (`OWNER_RUN`,
`AGENT_SAFE`, `PREVIEW_ACTIONS`, `SPELLINGS`), the module declarations, `command-permissions.md`, `docs/development.md` and the
shipped skills. They have drifted, and the owner has met the results: a `release-approvals` the agent could run but handed back, an
`extend` that failed because a skill said the agent never runs it while the key reads `ask`, an `ask` set for a key that does not
offer it and that quietly reads `block`.

The plan `2026-11-02-permission-system-consistency` consolidates this and `2026-11-02-permission-levels-for-every-command` widens
it. This record settles what both build on. It changes no level any key offers and no shipped default.

## Decision

Proposed; the owner decides. Nothing here is built; the plan `2026-11-02-permission-system-consistency` builds it.

1. **The earlier decisions stand.** Decisions 1 to 6 of `2026-10-26-a-level-for-every-command` and the records listed in Context are
   unchanged, `wb rerender` included: it stays terminal-only and `block`-only under `2026-10-27-rerender-is-terminal-only` until a
   record supersedes it. No key is terminal-only by design, except that one and what the clarification note of 2026-10-27 records:
   until the follow-on plan declares levels for them, the owner-run module arguments that have none (`mempalace` `init` and
   `mine`, `remote-runner fetch-overwrite`) offer `block` only, and `wb launch` stays terminal-only for an owner-run argument.
   This record does not restate any of this as new.
2. **One registry holds the facts about a key.** The installer keeps one registry with one entry per key: its kind, its danger
   class, the levels it offers, its default, its spellings, its preview, the command or rule it governs, and its documentation
   anchor. Two directions, stated once. A module's declaration (`module-contract.md`) is the authoritative input for the facts that
   are the module's own: its commands, `owner` arguments, `levels`, `preview`, `asks` and `checkpoint_of`. The facts that are the
   installer's own (its owner-run commands, its agent-safe actions, its spellings, its checkpoints) are written once, in the
   registry. The registry is the one reconciled view of both and rejects a declaration that conflicts with it. Every rendered rule,
   `wb settings` line and gate input is generated from it. Every other text that states a fact (specs, `docs/development.md`,
   skills, agents) is checked against it by a test; it is not required to omit the fact.
3. **Four kinds of key.** An installer command; an owner-run argument of a module's command; a checkpoint, which is either backed
   by a command or is a rule the agent follows (`2026-10-28-every-key-offers-the-approve-plan-levels`, decision 5); and an
   agent-safe action. The hook entry points `gate`, `agent-gate` and `gate-command` are not keys, as before.
4. **Three danger classes, as information.** Each key is in exactly one class, and the class is declared for the key, not inferred
   from its default. The class does not change a default or the levels a key offers; every default stays as shipped. It is what
   `wb settings` prints, what `wb doctor` reports (a key in the third class set looser than its shipped default is a risk) and
   what any later profile would be built from. The classes, with the keys proposed for each (the author's call; the owner may move
   a key):
   - *Reads*: the agent-safe actions and the declared module arguments that only read (for example `wb preview ...`,
     `wb run mempalace search`, `wb run remote-runner status`).
   - *Changes the project or what it installed, with a preview*: `wb install`, `wb adopt`, `wb upgrade`, `wb add`, `wb attach`,
     `wb recover` and the review engine's `extend`, `archive` and `amend`.
   - *Changes what governs the agent, leaves the project, deletes or publishes*: `approve-plan`, `accept-decision`,
     `wb release-approvals`, `acknowledge-first-tier`, `acknowledge-second-tier`, `wb approve`, `wb pin`, `wb rerender`,
     `push-shared-branch`, `submit-remote-job`, `fetch-remote-output`, `change-direction`, `remote-runner fetch-overwrite`,
     `mempalace` `init` and `mine`, the review engine's `reset` and `prune` (they discard or delete review history), and the three
     agent-safe module arguments that act outward or delete and carry an `asks`: `wb run remote-runner submit`, `wb run
     remote-runner fetch` and `wb run safe-git remove`. Those three keep their shipped default of `none`, so `wb doctor` reports
     a risk only for a level looser than that.
5. **Which mechanism governs.** When two mechanisms name the same act:
   - A command that implements a checkpoint is mapped to it with `checkpoint_of`, and the checkpoint's key governs it. This is how
     `groundwork accept` and `accept-decision` already work. This record does **not** map `wb run remote-runner submit` and `fetch`
     to `submit-remote-job` and `fetch-remote-output`: `checkpoint_of` today applies only to an `owner` argument that offers
     `levels` (`module-contract.md`), and `submit` and `fetch` are neither, so mapping them would change the module contract and
     move their default from `none` to the checkpoint's `block`. Whether to pair them is for the follow-on plan and a record of
     its own.
   - A checkpoint with one setting has one level. The settings table is the source (decision 5 of
     `2026-10-26-a-level-for-every-command`). A version 1 `checkpoints` word is read as a fallback for a key the table does not
     mention, and `wb settings` prints how it read it. The plan changes the seed so that a new file is written with the table and
     not the old object; a version 1 file is still read.
   - An `asks` is a module's declared minimum prompt, a first line and not a guarantee, under
     `2026-10-29-workbench-asks-for-remove-submit-and-fetch` and `2026-10-24-project-guarantees-a-floor`. It is rendered whatever
     the level of the argument's key. Today it is not a level: `command-permissions.md` ("A module can also declare a prompt that
     is not a key") says the table does not carry it and the approver cannot lower it from the personal settings.
     **Open for the owner:** whether to change that, so that an owner may lower it with their own level. The author
     recommends it stays a project minimum for now, because the checkpoints it backs, `submit-remote-job` and `fetch-remote-output`,
     have no digest-bound `ask` yet and the prompt is their only enforcement; `wb doctor` lists every `asks` as a
     project-declared minimum so the owner sees what it sets. When the follow-on plan gives those keys a real `ask`, a new record
     decides whether the `asks` for them is retired.
6. **Launcher spellings are generated, not refused.** The rendered rules for a key are generated from the registry's one list of
   launcher spellings, so their number no longer matters. `wb doctor` reports a spelling that the documents or skills use and the
   generated rules do not cover. The shipped skills and agents use `wb`. Refusing the `python -m workbench` forms is not adopted.
   This rests on a claim about the gate that is untested: that an unlisted spelling is refused at a relaxed level unless it is the
   exact simple form, and by the command's own terminal test at `block`. Increment D of the plan tests it. The policy is
   provisional until then; if the corpus shows an unlisted spelling slipping through, a new record reopens it before any later
   increment relies on it.
7. **A key that cannot offer `ask` says why.** Where a key has no honest preview, the spec names the reason and the record that keeps
   it so, and `wb settings` prints it. `ask` is never offered with a digest of nothing.
8. **What the follow-on plan adds.** `2026-11-02-permission-levels-for-every-command` gives the keys that offer fewer levels the
   levels they can make safe: `ask` for the installer commands that have a preview, previews for the rest, `wb rerender` under its
   own record, levels and previews for the `mempalace` and `remote-runner` owner-run arguments, a conformance check for modules,
   and the question of pairing the remote commands with their checkpoints. This record decides none of it.
9. **Out of scope.** Any new level for any key, any new preview, any change to a shipped default (all in
   `2026-11-02-permission-levels-for-every-command`), the compiled floor and the personal `floor` list, and the harness's own
   prompts. Named risk profiles are for a later record; `2026-10-26-a-level-for-every-command` decision 4 rejected a master profile
   that turns every protection off, and a profile must be consistent with that.

## Alternatives considered

- **Restate "no key is terminal-only" as a new decision.** Rejected: it is decision 3 of an accepted record, and the exception for
  `wb rerender` is an accepted record. Restating would invite a second reading.
- **Let the class set the default.** Rejected: the defaults are already what each command does today
  (`2026-10-26-a-level-for-every-command`, decision 2), and a default that moves is a change for an owner who changed nothing. The
  class informs; it does not decide.
- **Keep the facts where they are and add a test that they agree.** Rejected as the whole answer: a test finds a disagreement
  after it is written; a registry that generates the rules prevents it. The test remains, as the check on the texts that cannot be
  generated.
- **Make the registry generate the module declarations.** Rejected: the module contract makes the declaration the source for a
  module's own facts, and a module author, first-party or external, writes it. The registry reconciles; it does not author.
- **Retire `asks` now.** Rejected for now (decision 5): it would remove the only enforcement two checkpoints have.
- **Let the `asks` follow the owner's level from the start.** Not chosen, and left open for the owner. It is the owner's risk to take,
  and it is the cleaner model once those keys have an `ask` of their own.
- **Refuse every launcher spelling but `wb` with one rule.** Rejected: it adds refusals where the goal is fewer (the module form is
  documented in about 43 documents and was used for roughly one Bash call in twelve in the author's sessions), and the safety does
  not rest on the list: with a key relaxed, the gate matches a launcher and the word, so an unlisted spelling is refused unless it
  is the exact simple form, and at `block` the command's own terminal test refuses it. This is the author's call, from the spec and
  a count; the gate's behaviour on an unlisted spelling is to be tested by the corpus of the plan.
- **Edit the accepted records.** Not allowed. This record refines them, and the owner marks their status lines.

## Consequences

- Good: one place to read what a key is and offers, and the rendering, `wb settings`, the gates and `wb verify` cannot disagree
  with it; the next widening of the levels is made once.
- Good: the three mechanisms have a stated order, so a key's level, its checkpoint and its `asks` no longer contradict each other
  without anyone having chosen it.
- Good: the owner's risk appetite stays the owner's: nothing here removes a level an accepted record gave.
- Bad: a refactor of the code that every owner-run command reads. The plan runs it under characterization tests that must pass
  unchanged, and stops if one must change.
- Bad: while `asks` stays a project minimum, an owner who sets `submit-remote-job` or `fetch-remote-output` to `none` still gets a
  prompt for the command. That is deliberate and `wb doctor` says so, and it is the one place the owner's level does not decide.
- Bad: the class list is the author's proposal and a wrong class makes `wb doctor` report a false risk or miss a true one.
- Neutral: this record needs the plan's increments D to M to take effect; until then the facts are still kept in several places.
- Neutral: a security review of the registry and the gate is offered by the plan at the increments that touch them.

## Evidence

Read, not run, on 2026-11-02 at commit `870cf4b` (no tool version applies): the accepted records named above;
`docs/specs/command-permissions.md` ("Which levels a key offers", "Shipped defaults", "Not built"); `docs/specs/trust-and-approval.md`
("Effective values"); `docs/specs/remote-runner.md` and `docs/specs/safe-git.md` ("Asks"); `workbench/levels.py`
(`_OFFERS`, `_DEFAULTS`, `_AGENT_OFFERS`), `workbench/rules.py`, `workbench/harnesses.py` and `packages/workbench/remote-runner/module.json`
(the `owner` and `asks` fields) and `packages/workbench/groundwork/module.json` (`checkpoint_of`). The output of `wb settings` run
from this repository on 2026-11-02 shows `level wb run remote-runner submit: none` beside `level submit-remote-job: block`, and
a `settings:` line for each of `wb upgrade`, `wb attach`, `wb approve` and `acknowledge-first-tier` set to `ask` that reads `block`.
The review of the plan by the project's review bridge (`ask-codex`, two rounds) raised the accepted `wb rerender` record and the
direction of the declarations; both are reflected above. Not run: any rule against the harness, the corpus of gate cases, or a
module declared with a conflicting fact. The count of spellings in the documents (about 43 documents) and in the author's sessions
(about one call in twelve) is from a search and is approximate.

## Related files and decisions

- `docs/plans/2026-11-02-permission-system-consistency.md`, `docs/plans/2026-11-02-permission-levels-for-every-command.md`
- `docs/specs/command-permissions.md`, `docs/specs/module-contract.md`, `docs/specs/trust-and-approval.md`
- [2026-10-26-a-level-for-every-command](2026-10-26-a-level-for-every-command.md)
- [2026-10-27-owner-run-arguments-take-a-level](2026-10-27-owner-run-arguments-take-a-level.md)
- [2026-10-27-rerender-is-terminal-only](2026-10-27-rerender-is-terminal-only.md)
- [2026-10-28-every-key-offers-the-approve-plan-levels](2026-10-28-every-key-offers-the-approve-plan-levels.md)
- [2026-10-29-workbench-asks-for-remove-submit-and-fetch](2026-10-29-workbench-asks-for-remove-submit-and-fetch.md)
- [2026-10-24-project-guarantees-a-floor](2026-10-24-project-guarantees-a-floor.md)
