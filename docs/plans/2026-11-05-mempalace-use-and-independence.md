# Use mempalace when a palace is available, and make it independent of the other knowledge modules

Status: Proposed
Created: 2026-11-05
Candidate: workbench-v1#memory-recall-use
Specs: mempalace, knowledge-tools

## Goal

The owner found that in the former system almost nothing was saved to MemPalace and almost nothing was read. In this project the palace
holds 54 drawers (1 in `global/preferences`, 53 in the `opencode` wing) and none about this project, no agent has searched it in a long
session, and the policy leaves the agent to judge when an earlier lesson "could change the work", which in practice does not fire. The
owner also wants `mempalace` and `graphify` to depend on neither the other. After this plan:

1. the `mempalace` policy block and its `recall-memory` skill name no other knowledge tool: the routing bullet that names `graphify` and
   the knowledge base is replaced by a statement of what the palace answers, and a test fails if the module's shipped text names another
   knowledge module;
2. `knowledge-tools.md` and `mempalace.md` say that each knowledge module's block states what its own tool answers and names no other
   tool, in place of the rule that every block carries the same routing words;
3. the policy block and the skill tell the agent to search the palace once, with the topic, when it starts to draft a plan, a spec, a
   decision record or a roadmap candidate, or to brainstorm a design, in addition to the existing case of an owner reference to an
   earlier decision; "not at session start" and "not out of habit" stay;
4. the skills that start those moments (`draft-plan` in `code-work`; `brainstorm`, `draft-spec`, `draft-decision` and `draft-roadmap` in
   `groundwork`) each allow, besides their closed list of commands, one search through a module that provides `memory-recall`, named by
   the capability and not by module, so that the policy and the skill no longer contradict each other;
5. a project can name its wing in `.workbench/mempalace.json`, and `search` and `mine` use it unless the caller names another, so that
   results are scoped to the project and the policy's "a result is about this project only when its wing names it" has a fixed wing to
   compare with (other users of the tool report that detecting the project from a folder or git remote was inconsistent);
6. the program's off switch for usage telemetry is found in its source and set by the helper, with a test, and what a probe could and could
   not see of the program's connections is recorded, so that the outcome does not depend on proving that nothing is sent;
7. the owner has run one live session with a palace that holds something about this project, and the result, good or bad, is recorded in
   the spec's account of what was exercised.

## Scope

- `packages/workbench/mempalace/files/blocks/policy.md`, `packages/workbench/mempalace/harness/neutral/skills/recall-memory/SKILL.md` and
  `packages/workbench/mempalace/tests/test_mempalace_guidance.py`.
- `docs/specs/knowledge-tools.md` (the "Routing" rule, the acceptance criterion and "What `mempalace` showed") and `docs/specs/mempalace.md`
  (the lines that say the block and the skill carry the routing rule, "As built, and its limits").
- The five skills named in the Goal (`packages/workbench/code-work/harness/neutral/skills/draft-plan/SKILL.md` and
  `packages/workbench/groundwork/harness/neutral/skills/{brainstorm,draft-spec,draft-decision,draft-roadmap}/SKILL.md`) and the tests that pin
  their command rules (`groundwork/tests/test_groundwork_module.py`, `groundwork/tests/test_groundwork_brainstorm.py`, and the code-work tests
  of `draft-plan` if they pin it).
- `packages/workbench/mempalace/helper/mempalace` (the setting reader, the defaults of `search` and `mine`, and the environment given to the
  program) and its tests, for Increments D and E only; `docs/specs/mempalace.md` ("Palace location" and the command descriptions).
- The owner's steps: the copy and release of each package edit, and an upgrade of each project that should receive the new text
  (`wb upgrade`, at the level `ask` or in a terminal).

## Non-goals

- A way for the owner to file what an agent proposes to keep (an inbox and an owner-run command), a count of searches, a `wb doctor`
  note for a palace with nothing about the project, and mining finished sessions. They are the later steps of the owner's list and are
  not planned here.
- Any `graphify` or knowledge-base work, including the text of their future blocks. The rule this plan writes for them is only that a
  block names no other tool.
- Any change to the helper beyond the wing default of Increment D and the telemetry setting of Increment E; no change to the arguments the
  commands accept (`--wing` is already accepted by `search` and `mine`), the palace, the embedding model or an owner-run argument.
- A default wing for `init`: the program takes the wing of `init` from the folder name, and the owner renames it at the `[edit]` step.
- Mining finished sessions, which the research found to be the usual way a palace is filled (see Deferred work).
- Writing to the palace by an agent. An agent still cannot add to or change it.
- Choosing what the owner files. The plan proposes nothing to be filed; the owner decides what goes in the palace.

## Assumptions and constraints

- The module has no `requires` and nothing outside `mempalace/` names it in a module file; the coupling is in text only: the block's second
  bullet and the skill's list of "which tool answers which question" name `graphify` and the knowledge base, and
  `test_mempalace_guidance.py` pins those words.
- `knowledge-tools.md` (Current, approved 2026-10-24) and `mempalace.md` (Current) state the routing rule as one rule written into each
  block in the same words. This plan changes that rule; approving the plan is the owner's approval of the edit to both specs, which are
  edited in place.
- Where the harness's built-in memory could also answer, it is read first (the existing sentence stays). Whether Claude searches at the
  named moments is advice in text and is not enforced; the live run in Increment C is the evidence.
- A change to `packages/` follows the package-edit process: a scratch clone, tests there, the owner's copy with the recorded-hash script,
  the release approvals and the removal of stale shipped records after the owner approves the list. The command gate refuses Bash while
  the packages differ from the release.
- **The skills forbid other commands.** `brainstorm`, `draft-spec` and `draft-roadmap` end with "Use only reading, searching and editing. Do not
  run commands."; `draft-decision` and `draft-plan` close their lists of commands with "Run no other command." A policy that tells the agent
  to search at these moments would contradict them, and a careful agent obeys the stricter text and does not search. Increment C adds the
  allowance to each skill, by capability, and keeps every other command forbidden.
- The tests pin those sentences, and `tests/test_permissions_drift.py` checks that a closed list of commands in a text that names a key the
  owner may relax holds every command the text relies on; the edits keep both green.
- The policy block and the skills must be released and upgraded together. Until Increment C is released, Increment B's moments rule and the
  skills disagree, so the owner's `wb upgrade` of a project follows C and not B.
- This project's `AGENTS.md` carries a rendered copy of the policy block; it changes only when the owner runs `wb upgrade` here.
- Nothing is pushed. A commit needs the owner's word.

## Completion criteria

1. No file shipped by the `mempalace` module names `graphify` or the knowledge base, and the test that pins this passes.
2. The block and the skill carry the search-at-the-moments rule and the unchanged rules that a result is data, that nothing is searched at
   session start or out of habit, and that an agent cannot write to the palace; the guidance tests pass.
3. The two specs describe the new rule, and the old routing sentence is gone from both.
4. Each of the five skills contains the allowance, in words that name the capability `memory-recall` and no module, and still forbids every
   other command; the tests that pin their command rules, the module tests of `groundwork` and `code-work` that cover them, and the
   permission drift test pass.
5. After the owner's upgrade, this project's rendered `AGENTS.md` carries the new text, and the skills it installs carry the allowance.
6. With `"wing"` in the setting, a `search` without `--wing` passes the project's wing and one with `--wing` passes the caller's; the same for
   `mine`; a setting with only a `palace` still works as before; the setting refuses any other key, a relative path and a malformed wing.
7. The spec records the installed program's version, where its source names the switch that turns usage telemetry off, and what a probe saw
   and could not see. The child's environment carries that switch (a test that fails before the change and passes after), whatever the
   probe saw. If the source names no such switch, the entry says so and the helper is not changed, and the plan records the question as open.
8. The owner's live run is recorded in `mempalace.md` with what was seen: whether the agent searched at the named moments, what came
   back, and whether the result was used as data.

## Increments

### Increment A — The block and the skill name only their own tool

**Outcome:** the `mempalace` block and skill state what the palace answers and name no other knowledge tool; the two specs say that each
knowledge module's block does the same; a test pins it.
**Dependencies:** none.
**Affected areas:** the three `mempalace` files named under Scope, `docs/specs/knowledge-tools.md`, `docs/specs/mempalace.md`, the package's
release records (the owner's steps).
**Steps:**
1. In a scratch clone, write the tests first and see them fail on the unchanged text:
   - the block and the skill contain no mention of `graphify` and none of the knowledge base;
   - the block says what the palace answers (what was decided, tried or preferred before) and that a question the current files answer
     is answered from the files;
   - the block and the skill still carry the data-not-authority rule, the built-in-memory-first sentence and the "an agent cannot
     add to the palace" rule;
   - no other file of the module names another knowledge module.
   Change the `ROUTING` constant of the existing test to the new words.
2. Replace the second bullet of the block with a statement of what `mempalace` answers and that a question the current files answer is
   answered from the files, and take the three-way list out of the skill, keeping its first line.
3. Edit `knowledge-tools.md`: the "Routing" paragraph says that each module's block states what its own tool answers and names no other
   tool, and the acceptance criterion and "What `mempalace` showed" say the same; edit `mempalace.md` where it says the block and the
   skill carry the routing rule.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps, named when the code is ready: copy the changed files into the project with the recorded-hash script, run
   `wb preview release-approvals` and `wb release-approvals --digest`, remove the stale shipped records after approving the list.
**Verification:** the tests of the `mempalace` module (`packages/workbench/mempalace/tests`), because the change is to text those tests
pin, and `wb run code-work check` for the specs. Not run: the whole suite and `tests/test_boundary.py`, because no installer file changes;
the risk outside the tested area is a test elsewhere that pins the old routing words, which a search of the repository for them finds
(`global-config-inventory.md` mentions the rule only by topic).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-use-and-independence#A`.

### Increment B — Search at the moments that change the work

**Outcome:** the block and the skill tell the agent to search once, with the topic, when it starts to draft a plan, a spec, a decision
record or a roadmap candidate, or to brainstorm a design.
**Dependencies:** A.
**Affected areas:** the block, the skill, `test_mempalace_guidance.py`, `docs/specs/mempalace.md` ("The policy block and the skill"), the
package's release records (the owner's steps).
**Steps:**
1. Write the tests first and see them fail:
   - the block names the moments (drafting a plan, a spec, a decision record or a roadmap candidate; a brainstorm) and says to search once;
   - the "only when" rule is reworded so that the named moments are the exception to it, and "not at session start" and "not for what
     the current files answer" remain;
   - the skill gives the way to word the question for that search (the subject, the thing chosen or rejected, the reason) and says
     that a low match means the memory has nothing on the subject and to say so;
   - neither text asks the agent to write to the palace or to run `init` or `mine`.
2. Edit the block and the skill; edit `mempalace.md` to describe the moments.
3. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
4. The owner's copy and release as in A. The owner does not run `wb upgrade` yet: the moments rule would disagree with the skills until C is
   released.
**Verification:** the tests of the `mempalace` module and `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-use-and-independence#B`.

### Increment C — The skills that start those moments allow one memory search

**Outcome:** `draft-plan`, `brainstorm`, `draft-spec`, `draft-decision` and `draft-roadmap` each allow one search through a module that
provides `memory-recall`, so the policy of B and the skills agree; every other command stays forbidden.
**Dependencies:** B.
**Affected areas:** the five `SKILL.md` files named under Scope, the tests that pin their command rules, the package's release records
(the owner's steps).
**Steps:**
1. In a scratch clone, write the tests first and see them fail:
   - each of the five skills contains an allowance that names the capability `memory-recall`, says the search is made once, and names no
     module and no command of one;
   - each still contains its closed list of commands, with every command it had, and still forbids any other;
   - the tests that pin the exact sentences ("Use only reading, searching and editing. Do not run commands." and the `draft-decision`
     list) are changed to the new sentences, and no other sentence of those skills changes;
   - `tests/test_permissions_drift.py` still passes on the new texts.
2. Edit the five skills. For the three that end "Do not run commands.", the sentence becomes "Use only reading, searching and editing, and, where a
   module provides `memory-recall`, one search through it. Run no other command." For `draft-decision` and `draft-plan` the same clause is
   added to their lists.
3. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
4. The owner's steps as in A, and then `wb upgrade` in each project that should receive the texts of B and C, starting with this one.
**Verification:** the tests of the `groundwork` and `code-work` modules, `tests/test_permissions_drift.py` (named with its specific risk: it
reads the closed command lists of these skills), and `wb run code-work check`. After the owner's upgrade, a search of this project's
`AGENTS.md` for the moments sentence and of its installed skills for the allowance.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-use-and-independence#C`.

### Increment D — The project names its wing

**Outcome:** `.workbench/mempalace.json` may hold `"wing": "<name>"`; `search` and `mine` pass it to the program unless the caller gives `--wing`.
**Dependencies:** A (independent of B and C; it is placed after them so that the texts are released first).
**Affected areas:** `packages/workbench/mempalace/helper/mempalace` (`palace_setting` and the code that builds the arguments of `search` and
`mine`), `packages/workbench/mempalace/tests` (the setting and command tests), `docs/specs/mempalace.md` ("Palace location", the command
descriptions), the block and the skill (one sentence: the project's wing is the default; name another with `--wing`), the package's release
records (the owner's steps).
**Steps:**
1. In a scratch clone, write the tests first and see them fail:
   - a setting with `format` 1 and `wing` only, and one with `palace` and `wing`, are read; a setting with `palace` only is read as today; one
     with neither, an unknown key, a wing that is not a name (at most 64 letters, digits and `._:-`, not starting with `-` or `.`), a wing that is
     not text, or a relative or unclean palace is refused with a reason;
   - `search` with no `--wing` passes `--wing <setting>` to a fake program, `search --wing other` passes `other` and not the setting, and with no
     wing in the setting nothing is added;
   - `mine` behaves the same, and `init` is unchanged;
   - the settings file is still read without following a link, bounded, and is still a change `wb acknowledge` lists.
2. Change the setting reader to accept the keys `format` plus `palace` and/or `wing`, and the argument builders to add the default.
3. Edit the specs, the block and the skill for the sentence above.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan. Ask the owner whether to run a security
   review: the change reads a project file and builds the arguments of a program, which is a place to look.
5. The owner's steps as in A.
**Verification:** the tests of the `mempalace` module and `wb run code-work check`. Not run: the whole suite, because no installer file changes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-use-and-independence#D`.

### Increment E — Turn the program's usage telemetry off

**Outcome:** the helper's environment carries the program's own switch for usage telemetry, so the question whether it reports does not depend
on a probe; the spec records the switch and what a probe saw.
**Dependencies:** A.
**Affected areas:** `packages/workbench/mempalace/helper/mempalace` (`environment`), its tests, `docs/specs/mempalace.md` ("Evidence" and the
account of the child's environment), the package's release records (the owner's steps).
**Steps:**
1. Read the installed program's source for usage reporting (a search tool and one user report say ChromaDB's reporting may be on by default).
   Name the variable or setting that turns it off, the program's version, and where it was found. If the source names none, stop: write that
   in the spec, make no change to the helper, and report the question as open to the owner.
2. Write the test first and see it fail: the environment the helper builds for the program carries the switch, with the value the source
   requires, and carries no other new variable.
3. Add the switch to `environment` and run the test.
4. Run the probes for the record. They inform and do not gate, and neither may send anything off the machine, so each runs inside the
   operating system's sandbox (`sandbox-exec`) with a profile that permits connections to the loopback address only and denies every other
   outbound connection. Before either probe, a canary inside the same sandbox tries to connect to a documentation address (`192.0.2.1`) and
   must be refused; if the sandbox cannot be made to work without administrator rights, or the canary is not refused, no probe is run and the
   entry records that limitation. The helper passes the program a fixed environment with no proxy variable, so a proxy around the helper would
   not reach the program; a script in the scratch directory therefore imports the helper's `environment()` without the new switch, builds
   the command line the helper builds for `status` and `search`, and runs the program directly in a scratch home with a scratch palace.
   Probe 1 adds the proxy variables for every scheme pointing at a loopback listener that records and refuses what it receives, and records
   every connection the listener sees (a client that honours the variables). Probe 2 runs the same command with a profile that also denies
   loopback and ends the process on the first outbound attempt, so a direct connection that ignores the proxy variables shows as a signal exit.
   No palace of the owner's is touched.
5. Write the entry in the spec with the provenance line: the program's version, the date, the commit, the probes, and for each what it can
   and cannot see. A seen connection is evidence that the program reports; "none seen" is not proof that it does not, and the entry says so.
**Verification:** the `mempalace` module tests, including the new one; the probe output is recorded and is not a pass condition.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-use-and-independence#E`.

### Increment F — A live run, recorded

**Outcome:** `mempalace.md` records what happened in a real session with a palace that holds something about this project.
**Dependencies:** C and D, and the owner's steps below.
**Affected areas:** `docs/specs/mempalace.md` ("As built, and its limits" and "Evidence").
**Steps:**
1. The owner files a few drawers about this project into the palace with `mempalace` directly, in a wing that names this project. The
   agent does not choose them or file them.
2. In a fresh session after the upgrade, the owner asks for a drafting task (a brainstorm or the start of a plan) that an earlier
   decision bears on. The agent says what it searched and what came back.
3. The agent records, with the provenance line (the program's version, the commit, the date), whether it searched at the named moment,
   the question it wrote, the match it got, whether it quoted the result as recalled data and checked it against the files, and any
   noise or cost. The "hand run in a live session" item in "What was not exercised" is updated to what was seen, including a failure.
**Verification:** the entry matches what the session showed; no other file changes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-use-and-independence#F`.

## Verification for the plan as a whole

Each increment's recorded verification stands. After F, the guidance tests are not rerun unless a later change touched the block or a skill.
The wider suite is not run: the change is to text and its tests, and the one root test that reads those texts is named in C. The risk
outside the tested area is that Claude does not follow the new sentence, which no test can show and Increment F observes once; a single
session is a small sample, and the plan says so in the entry.

## Risks and sensitive actions

- A search at every drafting costs a call and its tokens. One search of five results is small, and "once" is in the rule.
- A palace with nothing about the project returns only background, so the new moments could add noise. The skill already says a low
  match means the memory has nothing, and to say so; Increment C looks for the effect.
- The edit changes two approved specs. It is part of the plan the owner approves and is made in place with the reasons in the plan's
  Result.
- The package edit closes the command gate until the owner has released it; the owner's steps are named in each increment.
- Recalled text is data. The change adds no instruction path from the palace to the agent and no write to the palace.
- Increments D and E change the helper, which reads a project file, builds the arguments of a program and sets its environment. The new setting
  key is validated as strictly as the old ones, an explicit `--wing` still wins, and nothing is added to the program's environment except one
  variable that turns reporting off, and only when the program's source names one. The owner is asked whether to run a security review of D
  and E.
- Increment E's probes run the program in a scratch home inside the operating system's sandbox, which allows the loopback address only, after a
  canary has shown that an outside address is refused; without that canary no probe is run. They send nothing off the machine and read no
  palace of the owner's. A probe cannot prove that nothing is sent, so the plan sets the switch whatever the probes see.
- The allowance widens five closed command lists by one search. It is limited by the capability, it names no command line, and the search
  command is itself read-only and bounded (`mempalace.md`). A skill that now permits a search could be read as permitting `init` or `mine`;
  the text says "one search", and the `recall-memory` skill still says an agent never runs the owner arguments.
- The edits reach into `groundwork` and `code-work`, whose other work is unrelated, and the owner copies and releases three times (A, B and C).
  Each edit to those two modules is one clause per skill, and the tests pin the rest of each text.

## Review record

**Review of the plan, 2026-11-05.** Reviewer: the review engine through `ask-codex`, on the owner's `plan` ladder (rounds 1 and 2 on the
profile `standard`, model `gpt-5.6-terra`; round 3 on `second-opinion`, model `gpt-6.1-sol`). Three rounds of the bound of 3. The review did
not converge: each round raised one major finding about the same step, Increment E's telemetry probe, and each was applied.

- **R1-F1 (applied).** The helper gives the program a fixed environment with no proxy variable, so a proxy around the helper cannot see its
  traffic. Increment E runs the program directly with the helper's environment plus proxy variables.
- **R2-F1 (applied).** A probe cannot prove that nothing is sent, so the plan must not depend on it. Increment E now sets the program's own
  off switch whatever the probes see (and reports the question as open if the source names none), and records what the probes could and
  could not see.
- **R3-F1 (applied).** The proxy probe ran without confinement, so a client ignoring the proxy variables could connect outside the machine.
  Both probes now run inside the operating system's sandbox that allows only the loopback address, after a canary shows an outside address is
  refused; without the canary no probe is run.
- **Rejected:** none.
- **Left for the owner:** the third fix was not reviewed, because the review stopped at its bound; extending the bound is the owner's. The
  three findings were all in Increment E, which changes at most one line of the helper and runs only a scratch probe. Nothing else in the
  plan was found wanting by any round: each summary says the plan aligns with its roadmap candidate and its specs.

**Increment A.** Reviewer: the `reviewer` agent (read-only), one round of the cap of 3, no blocking finding. It was given the plan, the
diff of the three package files, the diff of the two specs and the verification as run, and not my conclusions.

- **Applied:** the dropped sentences "a tool that is not installed is skipped" are now recorded in the dated note of `knowledge-tools.md`;
  the skill's lead-in "What the palace answers. The palace answers…" is reworded to start with the statement; the declaration test asserts
  that `memory-recall` is among the capabilities and that nothing is required, not that it is the only capability; the note's last sentence
  is reworded to say that the agent chooses among the statements of scope when several modules are installed.
- **Rejected, with the reason:** *the block test pins the exact sentence "…and the palace is not searched for it"* (a small over-pin of
  wording): the other tests in this file pin wording the same way, and the plan's own step 1 asks for the sentence. *The substring "the
  three" would fail an innocent use*: it is there to catch the old routing text, and the file is short. *"its 145 tests" in `mempalace.md`
  "As built"*: it describes what the earlier plan built and stays true as history.
- **Noted:** the redundancy between the first bullet ("not for what the current files answer") and the new one is intended by the plan's step
  1; `knowledge-tools.md` still names all three tools, which is allowed because the rule is for each module's block and not for the spec.
- **Not checked by the reviewer:** that the tests fail and pass as reported (I ran them), that the copied files equal the clone's, and
  whether Claude follows the skill.

**Increment B.** Reviewer: the `reviewer` agent (read-only), one round of the cap of 3, no blocking finding. It was given the plan, the diff of
the three package files, the diff of the spec edit and the verification as run, and not my conclusions.

- **Applied:** "once" is now "once per task" in the block and the skill, because a session may draft a plan and then a spec; the test that
  the skill names no other module's skill is tightened as the reviewer suggested (remove the one phrase "to brainstorm a design" and require
  that no `brainstorm` remains, in any case or form) and the same check is made on the block; the test that the block asks for no write uses
  word boundaries for `init` and `mine`, so "determine" cannot trip it; the spec bullet no longer cites the plan or a third party's claim, and
  says that the clause about a search that finds nothing is the skill's and not the block's.
- **Rejected, with the reason:** none.
- **Noted:** the block is exactly 14 lines, the test's limit, so the next sentence added to it needs a shorter one elsewhere or a new limit
  decided then; the new text disagrees with the five drafting skills until Increment C, as the plan says, which the release order (no
  `wb upgrade` before C) answers; whether Claude follows the new sentence is for Increment F.
- **Not checked by the reviewer:** the test results as reported (I ran them), and whether another test in the repository pins the old first
  bullet (a search of the repository found none).

**Increment C.** Reviewer: the `reviewer` agent (read-only), one round of the cap of 3, no blocking finding. It was given the plan, the
diff of the eight files and the verification as run, and not my conclusions.

- **Applied:** the clause says "one search per task", because it said "one search" for each skill and the policy says once per task, so a
  task that moved from `brainstorm` to `draft-spec` could have read two allowances; the tests pin the new sentence.
- **Rejected, with the reason:** none.
- **Noted, not done:** `docs/specs/command-permissions.md` lines 681 and 683 (the table of what the drafting and brainstorm skills run) say
  the drafting skills ran no command except `wb run code-work check` and `wb settings`, and that `brainstorm` "reads, asks, writes a spec". After
  C each may also run one search through a module that provides `memory-recall`. The row is dated ("as rendered … on 2026-10-27") and the plan's
  Scope does not list this spec, so I did not edit it; it is for the owner to say. The clause lets the agent run `search` and not `status`,
  although `recall-memory` lets it use `status`; the closing "Run no other command" still forbids the rest, and the difference is mild. The
  shipped wording is a separate sentence and not the "and, where…" clause of the plan's step 2; it meets criterion 4.
- **Not checked by the reviewer:** the test counts as reported (I ran them), that `wb run mempalace search` is level `none` and agent-safe
  (it is, in `wb settings`), and how a live agent reads the clause, which is Increment F.

**Increment D.** Reviewer: the `reviewer` agent (read-only), one round of the cap of 3, no blocking finding. It was given the plan, the diff of
the four package files, the diff of the spec and the verification as run, a list of the points to attack (the wing value reaching the program
as an option, the old shapes still refused, the overlap and root checks, one read of the file, the note shown to the terminal), and the
deviation from the plan, and not my conclusions.

- **Applied:** the new `Wing` test class inherited the tests of `Setting`, which ran twice; it now subclasses the base `Owner` class and
  borrows only the three helpers it needs (169 tests, from 177).
- **Confirmed by the reviewer, by reading the helper:** the wing is checked by `re.fullmatch` against the name pattern in the setting, in
  the caller's `--wing` for `mine` and for `search`, so a wing that starts with `-`, has a space, a newline or a non-ASCII character, or is
  longer than 64 cannot be used on any path; it reaches the program as its own element of an argument list, with no shell, and the `--`
  before the query still holds; every shape the old reader refused is still refused (unknown keys, a missing format, a bool or float
  format, duplicate keys, a relative or unclean palace, a link, size); `{"format": 1}` alone is refused; the overlap and root checks use
  the palace from the setting as before; the file is read once per command; `status` and `init` never receive the wing; the wing in the
  `mine` note has already passed the name pattern, so it is ASCII with no control character or markup; the only other caller of
  `palace_setting` is `status`, and its meaning there is unchanged.
- **Rejected, with the reason:** none.
- **Noted:** the deviation from step 3 (the sentence is in the skill and not in the block, which is at its 14-line limit) is recorded in the
  Result for the owner to accept.
- **Not checked by the reviewer:** the test counts as reported (I ran them), the base-class helpers of the tests, and `jsonstrict` and
  `safefs`, which this change does not touch.
- **Left for the owner:** whether to ask for a security review of D and E together, once E is built.

**Increment E.** Reviewer: the `reviewer` agent (read-only), one round of the cap of 3, no blocking finding. It was given the plan, the diff of
the three package files, the diff of the spec, the probe script and its saved output, and the paths of the installed program's source to check
the cited lines itself, and not my conclusions. It checked the cited source lines, the versions, the commit, the probe output and that
`environment()` is the only builder of the program's environment (both call sites use it).

- **Applied:** the spec's "Result" sentence said the source and the probes agreed that the setting is off whether or not the caller exported
  it; the probes ran without the variable and saw connections, not the setting, and the exported-`True` case rests on the source reading, so
  the paragraph now keeps the two findings apart and says that "none seen" is not proof; the source reading is marked "the Python source only"
  (ChromaDB's compiled core was not read); the paragraph says that the probe script used the program's own command line and not the one the
  helper builds, that its profiles confine the network and not the file system so writes outside the scratch directory were not checked, that
  the canary was refused with an error and did not time out (no timing was taken), that the whole script was run twice and the second output
  kept, and gives the probe's Python version (3.15.0) and says that `sandbox-exec` has no version of its own.
- **Rejected, with the reason:** none.
- **Noted:** the script has no `try/finally` around the removal of its scratch directory (cosmetic, and the script is not part of the
  repository); precedence between an explicit `Settings` argument and the environment variable was not shown in anything read, and the spec
  does not claim it.
- **Not checked by the reviewer:** the test results as reported (I ran them), that the clone's helper is the file the owner will copy, and
  the probe by running it.

## Deferred work

- A way to file what an agent proposes to keep, without letting the agent write (an inbox and an owner-run command), including a short record
  of each brainstorm (the question, the options, the choice, the reasons, the rejected options) and, as a lighter step, an "alternatives
  considered" section that the `brainstorm` skill asks for in the spec.
- A count of searches and hits, and a `wb doctor` note for a palace with nothing about the project. Research on other users found that capture
  that saves nothing without telling anyone is the most reported failure, so any capture step needs a visible count first.
- Mining finished sessions into the palace, with redaction. Other users fill a palace mainly this way (`mine --mode convos` or `sweep` over
  the transcripts), and the maintainers warn that Claude Code deletes a session after about 30 days. This project's oldest transcript is from
  29 October. A transcript holds everything shown on screen, secrets included, so the owner decides whether to mine and with what redaction; this
  plan does neither.
- `wake-up`, the program's start-of-session load (reported at 600 to 900 tokens, against 170 in its own README), which this plan does not use
  because the policy says not to search at session start.
- The blocks of `graphify` and the knowledge base, which follow the rule this plan writes: each names only its own tool.

## Result

**Increment A, built in a scratch clone (2026-11-05); not yet copied into the project, released or committed.** Base commit of the clone:
`414864a`. Changed in the clone: `packages/workbench/mempalace/files/blocks/policy.md` (the routing bullet that named `graphify` and the
knowledge base is replaced by "The palace answers what was decided, tried or preferred before. A question the current files answer is
answered from the files, and the palace is not searched for it. Where the harness's built-in memory could also answer, read it first and
search the palace only when it does not."), `packages/workbench/mempalace/harness/neutral/skills/recall-memory/SKILL.md` (the list of "which
tool answers which question" is replaced by the same two sentences) and `packages/workbench/mempalace/tests/test_mempalace_guidance.py` (the
`ROUTING` constant is now `SCOPE`, the two routing tests say what the palace answers and that neither text names another tool, and a new
`Independence` class checks that no shipped file of the module names `graphify` or the knowledge base and that the declaration has no
`requires`). In the project, docs only: `docs/specs/knowledge-tools.md` ("What each tool answers" in place of "Routing", the acceptance
criterion, "What `mempalace` showed", and a dated note that also records that the "skip a tool that is not installed" sentences went with
the routing) and `docs/specs/mempalace.md` (the two lines that said the block and the skill carry the routing rule).

**Verification as run.** Tests first: three of the new tests failed on the unchanged text (the block, the skill and the shipped-files check).
After the change, all 154 tests of the `mempalace` test directory pass, run as the repository's runner does (discover with the tests
directory as start and top, `PYTHONPATH` at the repository root; the first attempt, with the wrong start directory, failed to import and was
not counted). `wb run code-work check`: 93 plans, no problems. Not run: the whole suite and `tests/test_boundary.py`, because no installer
file changes. A search of the repository for the old routing words found them only in the completed plan `2026-10-24-mempalace-module` (a
record, not edited), the installed copy under `.workbench/` and the rendered `AGENTS.md`, which change only when the owner runs `wb upgrade`.

**Hashes of the three package files at the end of the clone's work** (SHA-256): `policy.md`
`1f30314879aa046a3656e583b729eb624acebaa8cf91b51bad969fdbdfdd02ca`, `SKILL.md`
`ba231ae0857b3e7444694de7f4d73b8865dffe2c7a4dbaa00c5de1056674413d`, `test_mempalace_guidance.py`
`debfd9aa92c80961b733d73db2183469e12551a8b7c7e3b6ec0d3f53a1c25b0e`.

**Review:** one round with the `reviewer` agent, no blocking finding (see the review record).

**Not done in A:** Increments B to F. A was copied and released by the owner, the stale shipped records were removed after the owner approved
the list, and A is committed as `0b450a6`.

**Increment B, built in a scratch clone (2026-11-05); not yet copied into the project, released or committed.** Base commit of the clone:
`0b450a6`. Changed in the clone: `policy.md` (the first bullet now reads "…only when an earlier decision, preference or lesson could change
the work, or, once per task and with the topic, before you draft a plan, a spec, a decision record or a roadmap candidate, or brainstorm a
design. Do not search at session start for its own sake, and not for what the current files answer."; still 14 lines, the test's limit),
`SKILL.md` (the opening says the same in the skill's words with "search once per task for that, with the topic"; step 1 says how to word the
question for a drafting task; step 3 says that a search that finds nothing is an answer and the agent goes on and says so in one line) and
`test_mempalace_guidance.py` (the pins of the first bullet changed to the new sentences; two new block tests and one new skill test for the
moments and for the block asking for no write; the existing test that the skill names no other module's skill is tightened, see below). In the
project, docs only: the first bullet of "The policy block and the skill" in `docs/specs/mempalace.md`.

**Verification as run.** Tests first: three of the new or changed tests failed on the unchanged text. After the change all 157 tests of the
`mempalace` test directory pass. One existing test failed on the first run: it forbade the word `brainstorm` anywhere in the skill, to keep the
skill from naming another module's skill, and the new sentence uses it as a verb. It now removes the one phrase "to brainstorm a design" from the
whitespace-normalised text and requires that no `brainstorm`, in any case or form, remains, which is stricter about references to the skill than
a list of spellings; the same check is made on the block. `wb run code-work check`: 93 plans, no problems. Not run: the whole suite and
`tests/test_boundary.py`, because no installer file changes.

**Hashes of the three package files at the end of the clone's work** (SHA-256): `policy.md`
`7a2b33d73083eb7c96e34ecc41c0b2d77755e1c80a22bae8bf9cbe85c489da3d`, `SKILL.md`
`0b17ffd47ee8eb1497506213b6fbf6f1b1c98cd760c891488ce1f975fdb1a9b2`, `test_mempalace_guidance.py`
`743aae873bb63223269b58fa4f4e6e7539843a5e198e8e8f2a34c0b6ff3d14e6`.

**Review:** one round with the `reviewer` agent, no blocking finding (see the review record).

**Not done in B:** Increments C to F. B was copied and released by the owner, the stale shipped records were removed after the owner approved the
list, and B is committed as `53c13b9`. The owner does not run `wb upgrade` for B alone: the new sentence disagrees with the five drafting skills
until C is released.

**Increment C, built in a scratch clone (2026-11-05); not yet copied into the project, released or committed.** Base commit of the clone:
`53c13b9`. Changed in the clone, in two modules: the five skills `code-work/…/draft-plan`, `groundwork/…/brainstorm`, `…/draft-spec`,
`…/draft-decision` and `…/draft-roadmap` each gain the sentence "Where a module provides `memory-recall`, one search per task through it is
also allowed." before their closing "Run no other command."; the three that said "Do not run commands." now end with that clause (the only
added permission) and "Run no other command."; `draft-decision` and `draft-plan` keep their lists of commands. Tests: `test_groundwork_module.py`
(the pin of the three skills' closing sentence and of the `draft-decision` list changed, and a new test checks, for every groundwork skill, that
the sentence occurs once, that `memory-recall` occurs once, that no `mempalace`, `wb run mempalace`, `graphify` or `palace` occurs, and that
"Do not run commands" is gone), `test_groundwork_brainstorm.py` (the same pin for `brainstorm`) and `test_codework_skills.py` (a new test that
`draft-plan` keeps its closed list, ends with the clause and "Run no other command.", and names no module).

**Verification as run.** Tests first: five of the new or changed tests failed on the unchanged skills. After the change the groundwork tests
(252) pass, the code-work tests (347, 2 skipped as before) pass, and `tests/test_permissions_drift.py` (22) passes with and without the change.
One slip while editing: the first rewording to "per task" missed three skills whose sentence wraps across a line, and three tests failed until
I fixed them. Not run: the whole suite and `tests/test_boundary.py`, because no installer file changes.

**Hashes of the eight files at the end of the clone's work** (SHA-256): `draft-plan/SKILL.md`
`ec5a68c2e600573b8e1dd39e24832cf518df97f81270471e4477ea2457419f17`, `test_codework_skills.py`
`a1c5bafd4f638cb19e3d3c8849ee1964d750079b61c9c176c6922601cc3c647d`, `brainstorm/SKILL.md`
`3fe31a0955cdedb37f6f6a464e7698fdc41152bbed7adbdb1c52eea725023101`, `draft-decision/SKILL.md`
`3cba3088aca2504f236bad0adb169209b7ea1547de9c1ebe3fa06c482fd94a48`, `draft-roadmap/SKILL.md`
`020cffb167c8e0850d82089df452fa2359e8b85bec65da084766bda2a2b8bddb`, `draft-spec/SKILL.md`
`d132f80cd94024624f2c0faa7c6ce3396c409e5291692e4fd016a208b32b229d`, `test_groundwork_brainstorm.py`
`f3732912dbcd1c6ee24cdc03a28282280ae1ccf82f17f07584d675fed33f091f`, `test_groundwork_module.py`
`28714ee502f9b33e4ae578c59defb5a6429365d272d704a45f0d1f3bbe0acc32`.

**Review:** one round with the `reviewer` agent, no blocking finding (see the review record).

**Not done in C:** Increments D to F. C was copied and released by the owner, the stale shipped records were removed after the owner approved the
list, and C is committed as `b7b118d`; the owner ran `wb upgrade`, and the install-state files are committed as `ed661a8`.

**Increment D, built in a scratch clone (2026-11-05); not yet copied into the project, released or committed.** Base commit of the clone:
`ed661a8`. Changed in the clone: `helper/mempalace` (the reader of `.workbench/mempalace.json` is now `project_setting`, which returns the
pair `(palace, wing)`; `palace_setting` remains as a one-line wrapper for `status`; the file may hold `format` and a palace, a wing or both,
any other key or neither is refused, a wing must match the helper's existing name pattern; `search` adds `--wing <the project's wing>` unless
the caller gave one; `mine` does the same, in the position `--wing` already had, and its note says "the wing is <w>, from
.workbench/mempalace.json (name another with --wing)"; `status` and `init` take none), `harness/neutral/skills/recall-memory/SKILL.md` (one
sentence: "When the project names its wing, a search is limited to it unless you give another with `--wing <name>`."), `tests/test_mempalace_owner.py`
(a class `Wing` of ten tests) and `tests/test_mempalace_guidance.py` (one skill test). In the project, docs only: `docs/specs/mempalace.md`
("Palace location" and the acceptance bullet for the setting).

**Deviation from the plan, for the owner to accept.** Step 3 says the block and the skill get the sentence. The block is exactly 14 lines,
which its test allows at most, so the sentence is in the skill only; the block is unchanged. The sentence is about how a search is scoped, which
the skill carries, and the block's rule that a result counts as about the project only when its wing names it is unchanged. A longer limit for
the block would be a decision for the owner.

**Verification as run.** Tests first: seven of the new tests failed on the unchanged helper (it refused the `wing` key); four others passed
at once because they check refusals the old reader already made, and stay to keep the stricter reader strict. After the change all 169 tests of
the `mempalace` test directory pass, run as the repository's runner does. Two slips while editing, both fixed: an edit script that took its end
marker from the wrong place duplicated part of the helper (found by the helper's own tests; the final file has no duplicated function, which I
checked), and a `collections` import, which the helper's test of its allowed imports refuses, was replaced by a plain pair. `wb run code-work
check`: 93 plans, no problems. Not run: the whole suite and `tests/test_boundary.py`, because no installer file changes.

**Hashes of the four files at the end of the clone's work** (SHA-256): `helper/mempalace`
`a2bf1f39b219ee87a48abfe0c7e894071b4c5492d07c373ac66698e417a3f53a`, `SKILL.md`
`e3cb54b9347991f6e113668aca1df6ff5d0f4ec26a8790cfdfbee411e81e0d97`, `test_mempalace_owner.py`
`7346e6ad197188b063e7216956d858467f10e0e9e4d8d2b74aa7faccdf0716e6`, `test_mempalace_guidance.py`
`7c639952d564a007ab10c994478495009da49aa37024f18b0b55fb5a9b152541`.

**Review:** one round with the `reviewer` agent, no blocking finding (see the review record). A security review of D and E is the owner's to ask for.

**Not done in D:** Increments E and F, and the security review, which is asked for once, for D and E together (see E). D was copied and released by
the owner, the stale shipped records were removed after the owner approved the list, and D is committed as `d0a81bb`.

**Increment E, built in a scratch clone (2026-11-05); not yet copied into the project, released or committed.** Base commit of the clone:
`d0a81bb`. Changed in the clone: `helper/mempalace` (`environment()` now also sets `ANONYMIZED_TELEMETRY` to `False`, with a comment and a
sentence in its docstring), `tests/test_mempalace_run.py` and `tests/test_mempalace_owner.py` (the two tests that pin the program's exact
environment add the variable to the set, assert its value for the agent commands and the owner commands, and export `ANONYMIZED_TELEMETRY=True`
to show that the caller's value is replaced). In the project, docs only: `docs/specs/mempalace.md` (the sentence about the child's
environment, the acceptance bullet, and a new paragraph "Usage reporting" at the end of "Evidence").

**What step 1 found.** The source names the switch: ChromaDB 1.5.9's `Settings.anonymized_telemetry` defaults to on, the environment variable
`ANONYMIZED_TELEMETRY` sets it, ChromaDB's client for it is a no-op in this version and `posthog` is not installed, and MemPalace 3.11.0
already turns it off at import (with `setdefault`) and in the settings it gives every client. The step 1 stop condition (no switch named) did
not apply. **What the probes found (step 4).** Canaries first (an outside address refused, a proxy-honouring client seen by the loopback
listener, a loopback connection ended under the kill profile); then `init`, `mine`, `search` and `status` of the real program in a scratch
home under each profile: all exited 0, the listener saw no connection, and the kill profile ended none. Run twice, same result. The probes
inform and do not gate; "none seen" is not proof, and the spec paragraph says what each profile can and cannot see.

**Verification as run.** Tests first: the two environment tests failed on the unchanged helper. After the change all 169 tests of the
`mempalace` test directory pass. `wb run code-work check`: 93 plans, no problems. Not run: the whole suite and `tests/test_boundary.py`, because
no installer file changes.

**Hashes of the three files at the end of the clone's work** (SHA-256): `helper/mempalace`
`c982f1e43f8da20a135074bbcd377a6de2bfd18caa101a980e87f361e2d6a727`, `test_mempalace_run.py`
`e566986e9ef6c9962482675ec1462f6cf208ca9c59f667eb06b710dd8a42266a`, `test_mempalace_owner.py`
`61f965e2afdca46d61395e05cb1210862d2353f91ffb7798fc58b6e6179b0b8a`.

**Review:** one round with the `reviewer` agent, no blocking finding (see the review record).

**Not done in E:** the owner's copy and release, the commit, the security review of D and E (the owner's to ask for), and Increment F.
