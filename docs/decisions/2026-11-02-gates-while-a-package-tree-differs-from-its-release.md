# The gates stay closed while the harness cannot be shown to match its release, and say why; narrowing the lock is an option and not decided here

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-02
Date: 2026-11-02

## Context

The edit gate (`wb gate claude`, for `Edit`, `MultiEdit`, `NotebookEdit` and `Write`), the command gate (`wb gate-command claude`,
for `Bash`) and a confined agent's gate (`wb agent-gate`) each begin by finding the harness's layout through `harnesses.known`.
That accepts a harness only when its module is in a package that `firstparty.is_first_party` accepts: the package's declaration
hash and its **tree hash** must match a record shipped with the workbench (`workbench/shipped_approvals/`). When that fails,
`claude` is not a known harness and each gate refuses with "claude is not a known harness whose layout describes the command
gate" (or "declares the tools its hook covers"). The wording names neither the cause nor the way out.

**What the lock refuses and what it does not**, from the code and the rendered hook configuration. Two hooks are rendered, for
`Edit|MultiEdit|NotebookEdit|Write` and for `Bash` only. While the harness is unknown, every call to those tools is refused,
including `wb preview release-approvals`, the one command that shows what would clear it. `Read`, `Grep`, `Glob`, the agent tool
and the owner's own terminal have no hook and are unaffected. (The plan `2026-11-02-permission-system-consistency` says the lock
refuses "every tool call"; that overstates it.)

**What the lock does not guard.** `firstparty` is used by `attach`, `upgrade`, `preview`, `approve`, `base`, `check`, the release
commands and the gates. It is not used by `wb run`: `commands.installed_module` reads the **installed** copy of a module's
`module.json` under `.workbench/`, compares its declaration hash with the project manifest, and the launcher runs the helper bytes
the pin names. So an edit to a file under `packages/` does not change what any installed command runs until the owner runs `wb
upgrade`. The lock covers the layout facts the gates read. It does not cover the gate code itself (`workbench/gate_hook.py`,
`command_gate.py`, `agent_gate.py`, `cli.py`) or `workbench/shipped_approvals/`, which sit outside any package tree hash;
`command-permissions.md` ("Limits") already says that in this self-hosted repository the code the launcher runs is in the agent's
write scope. The lock therefore arises where the distribution is a working tree the agent can edit, as it is here; this record
does not claim to know how often it arises in a project that uses an installed workbench, which was not run.

**What causes it**, run on 2026-11-02 against a throwaway copy of the distribution (not this tree):

| Change in the copy | Package first-party | `claude` known |
|---|---|---|
| none | yes | yes |
| a stray cache file in another module (`ask-ollama/helper/__pycache__/x.pyc`) | no | no |
| one new text file in another module's `tests/` | no | no |
| one comment line added to another module's helper | no | no |
| a symbolic link inside the `claude` module | no | no |
| one space appended to the `claude` module's declaration | no | no |
| each change undone (an empty cache directory left behind counts as undone) | yes | yes |

The tree hash covers every regular file below `packages/workbench/` (`hashing.hash_tree`), tests and caches included, refuses any
link or special file and counts the execute bit; and `packages/workbench/` is one package that holds all 13 modules. So an edit to
the tests of the `ask-ollama` module closes the gates for everything, although the harness the gates read is the `claude` module
alone. The same run showed that the `claude` module's own shipped record (subject `workbench/claude`) still matches when only
another module changes. It also showed the limit: with a stray file inside a module, `verify.verify_package` returned no `claude`
module at all, because it fails the whole package on any problem in any module (`Result(False, ..., modules=())`), and
`harnesses.load` drops a package whose `load_package` reports any problem.

**Why the gates fail closed:** the harness module's layout says which tools the hooks cover and which field of each call is read.
A changed `claude` module could change what the gates look at. Failing closed is the tamper evidence for that. The owner's cost is
that after any package edit, such as the scripted pass of a package increment, nothing hooked can run until the owner releases the
approvals from a terminal, and the agent cannot run the preview and the release that its `ask` level would otherwise let it run.
The release preview itself says it does not cover "the content of the packages" and tells the owner to read the change with `git
diff` first; that read is the review the terminal trip prompts.

## Decision

Proposed; the owner decides. Nothing here is built; the plan `2026-11-02-permission-system-consistency` builds it (increment J).

1. **The gates stay closed while the harness cannot be shown to match its release.** The edit gate and the command gate keep
   refusing, and a call is never let through on a guess. This record does not weaken the tamper evidence.
2. **The refusal says why and what clears it.** The line replaces "is not a known harness ..." and names the cause: the package
   tree differs from its release, with the first path (in sorted order) that differs, was added or is missing; or a link or
   special file was refused; or there is no shipped record. It names the command that clears it: `wb preview release-approvals`
   and then `wb release-approvals --digest <digest>`, which the owner runs in a terminal while the gates are closed. It prints
   paths, never file content.
3. **Narrowing the lock is not decided here.** The option is described under "The option left open" and is for a later record,
   after decisions 2, 5 and 6 are built and the refusal log and `wb doctor` show how often the lock bites. The author recommended
   waiting, for the reasons given there. The owner said in conversation on 2026-11-02, while this record is `Proposed`, that they
   wish to wait; that is the author's note of it and becomes part of the decision only when the owner accepts this record. Deciding
   it later needs the analysis the option lists and a new approval of the plan, because increment J lists `harnesses.py` and
   `firstparty.py` as files it only reads.
4. **What protects a running command is the installed copy.** This record states it so that no later text assumes otherwise:
   `wb run` is governed by the manifest hash of the installed `module.json` and by the pin, not by the shipped records, and a
   package edit reaches a command only at the owner-run `wb upgrade`. A test that a changed package's commands refuse would
   test something the code does not do; none is written.
5. **A stray file in a package is a lock like any other change, and is reported before it bites.** It is not ignored by the hash:
   the tree hash is the integrity check on everything below the package, and a carve-out for one kind of file makes it a check on
   less, with each exception needing a reason that has been verified. Whether a cache file there can ever be used as code depends on
   whether its source module is imported and the cache validates; that was not checked for any shipped helper, and this decision
   does not rest on it. The cure is not to make them: the tests of a package run with `python3 -B`, and `wb doctor` (increment L) reports a package whose tree differs from its release with
   the first differing path, so a stray file is found before the gates close. Removing it uses `wb run safe-git remove`, which
   previews and asks.
6. **Fewer locks by plan shape.** A plan with package increments does its package edits in as few passes as it can and releases
   once after the last, when the order allows; the plan names which increments are package increments, as plan 1 does.
7. **Not adopted:** letting a closed list of commands through while the harness is unknown, and keeping a recorded copy of the
   layout from the last attach for the gate to use. See the analysis below.

## The option left open: trusting the harness module's own record

A harness would be known when the harness module's own shipped record matches that module's declaration and tree hash. An edit to
another module would then not close the gates, and the agent could run `wb preview release-approvals` and `wb release-approvals
--digest` through the `ask` flow, so a package increment would end without a trip to the terminal. What it needs and what it costs,
from reading the code and the review of this record:

- **New loading code.** Every input reaches `harnesses.load` through `declarations.load_package`, which parses every module's
  `module.json` and reports any module's problem for the whole package, and through `verify.verify_package`, which fails the whole
  package on one unaccounted file (`modulefiles._accounted`). The option needs a per-module load and a per-module verification that
  never go through those, a way to read one `module.json` without the walk, and a way to give the harness's own unprefixed
  `provides` its first-party reading when its package as a whole is not first-party. It is a change to the root of the gates' trust.
- **A tamper path it opens.** Today a package edit locks the agent's hooked tools at once and the owner releases from a terminal.
  After narrowing, an agent that edits any module but `claude` keeps working with the gates open, and can run the preview and the
  release at `ask`; the prompt shows a digest and not the content, and the preview says the content is not covered. The owner
  would be confirming a release of the agent's own edit without its content in front of them, and the shipped records, once
  committed, would approve the edited package for the next `attach` or `upgrade` and for other clones. The terminal trip is a
  friction, not a control, but it is the moment the owner is told to read `git diff`.
- **A rollback target.** `write_release` leaves earlier records in place and `approvals` looks a record up by its hashes. Under a
  per-module check an older released `claude` module that still has a record would be known, and the agent could restore it from
  git and keep the gates open on an older layout. The option would have to count only the current release's records.
- **More than one harness module.** `harnesses.load` and `check.py` use all known harnesses. Each harness module would need its own
  record; the option would have to say so.
- **Inputs outside the module.** `package.json` is read by the loader and is covered today only by the package hash; the gate code
  and the shipped records are outside any hash already (above).

What an attacker who can edit a package gains, by option:

| Option | An agent that can edit a package gains |
|---|---|
| Keep the lock and say why (decision 1 and 2) | Nothing: after its edit every hooked tool is refused until the owner releases from a terminal. It can still read. |
| Trust the harness module's own record | Hooked tools stay open after an edit to another module; it can run the release itself at `ask`, and the owner confirms a digest. It can restore an older released `claude` unless only current records count. |
| Let a closed list of `Bash` commands through while the harness is unknown | The listed commands, in a state where the gate cannot read its own layout; the list is a second place for the facts. |
| A recorded copy of the layout from the last attach | The gates keep working through any package edit; the copy can go stale against the module, and its record is a new thing to protect. |
| Ignore caches in the tree hash | A cache file that is loaded as code without the owner having seen it. |

**The author's recommendation is to wait.** The lock fails closed as it should, the message and `wb doctor` will make it
understood and shorter to clear, and the option changes the root of the gates' trust and opens the tamper path above on
partial evidence. A later record can decide it with a measured frequency, a security review of the new loader and a chosen answer to
the rollback and self-release questions.

## Alternatives considered

- **Keep the lock as it is and only improve the message (decisions 1 and 2).** This is what is decided. It leaves the frequency; the
  option above is the answer to the frequency, deferred.
- **Decide the narrowing now.** Not chosen (decision 3): the code to do it does not exist, and the tamper analysis is new.
- **Let `Bash` through for a closed list (`wb preview release-approvals`, `wb release-approvals --digest`, `wb check`) while the
  harness is unknown.** Rejected: the gate would carry a list of its own in a state where its inputs cannot be trusted, and it
  duplicates the registry (`2026-11-02-one-permission-registry-and-key-model`, decision 2).
- **A recorded copy of the layout from the last attach.** Deferred: it keeps the gates working through any package edit, and adds a
  record to maintain and a way for the copy to go stale.
- **Ignore `__pycache__` and `.pyc` in the tree hash.** Rejected: the hash would cover less than everything below the package, and
  it would change every shipped hash and need a release before it helped. The cure is not to create them. (Whether such a file
  can be loaded as code was not checked, and this rejection does not depend on it.)
- **Remove the lock for edits made by the scripted pass.** Rejected: the pass is the agent's own act, so a lock it can skip protects
  nothing.
- **Make the pass run the release itself.** Rejected: the release is the owner's `ask` confirmation, and the gate is what keeps the
  agent from approving its own edit.
- **A warning at the start of a session that the tree differs.** Not rejected; `wb doctor` is where this lives (decision 5). A
  session-start hook is the harness's feature to wire later.
- **Edit the accepted records.** Not allowed. This record adds a stated cause and a way out to a failure that
  `2026-10-26-ask-level-command-gate` and the shipped-approval rules already produce.

## Consequences

- Good: the gates are never open on a guess, and the owner is told the cause and the cure instead of "not a known harness".
- Good: the record corrects two statements that the plan makes, that the lock refuses every tool call and that a changed module's
  commands refuse; it also names what the lock does not cover, which the owner should know when relying on it.
- Bad: the frequency of the lock is unchanged by this record. A package increment still ends with a trip to the terminal.
- Bad: a stray file still closes the gates until someone removes it. The message and `wb doctor` shorten the search; they do not
  remove the lock.
- Bad: the author's sense of how often the lock bites is from one project's sessions, not a measure. The refusal log of the
  gate decision is how it becomes one.
- Neutral: the agent still cannot clear the lock in a terminal-less state. If the owner decides the option later, that changes.

## Evidence

Run on 2026-11-02 at commit `2952c76`, workbench 0.1.0, Python 3.15.0: two throwaway scripts on a copy of `workbench/` and
`packages/` in a scratch directory (caches removed from the copy), calling `harnesses.known`, `firstparty.is_first_party`,
`verify.verify_package` and `approvals.check_module` on the copy before and after each change in the table, then undoing it. The
first reproduced the table; the second showed that the `claude` module record (`workbench/claude`) still matched after a new file
in another module's `tests/` and after a comment in another module's helper, did not match after one space in its own declaration,
and that with a stray cache file the verify step returned no `claude` module. The scripts were not kept and this tree was not
changed. Read: `workbench/harnesses.py`, `workbench/firstparty.py` (`is_first_party`, `_package_hashes`, `plan_release`, the
module docstring), `workbench/hashing.py` (`hash_tree`), `workbench/verify.py` (`verify_package` returns no modules on any
problem), `workbench/commands.py` (`installed_module`), a search showing `firstparty` is imported by `approve.py`, `attach.py`,
`base.py`, `cli.py`, `gate.py`, `harnesses.py`, `preview.py` and `upgrade.py` and not by `commands.py` or `launch.py`,
`workbench/cli.py` (`_gate`, `_gate_command`), `workbench/gate_hook.py` (docstring) and the rendered hook configuration (two
`PreToolUse` hooks, matchers `Edit|MultiEdit|NotebookEdit|Write` and `Bash`). A reviewer's reading of `declarations.load_package`,
`modulefiles._accounted`, `approvals._lookup`, `commands.resolve`, `launch.py` and `check.py` is reflected above and was
confirmed here for `commands.py`, `verify.py` and the `firstparty` imports. Not run: a real package edit followed by a gate call in
this tree (the lock was met here earlier in the day by an edit made in the course of the work); a project that uses an installed
workbench; whether any shipped helper imports a sibling module; a security review.

## Related files and decisions

- `docs/plans/2026-11-02-permission-system-consistency.md` (increments J and L)
- `docs/specs/command-permissions.md`, `docs/specs/module-contract.md`, `docs/specs/trust-and-approval.md`
- [2026-10-26-ask-level-command-gate](2026-10-26-ask-level-command-gate.md)
- [2026-11-02-one-permission-registry-and-key-model](2026-11-02-one-permission-registry-and-key-model.md)
- [2026-11-02-command-gate-reads-gaps-and-data-positions](2026-11-02-command-gate-reads-gaps-and-data-positions.md)
