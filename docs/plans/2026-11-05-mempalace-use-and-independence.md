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

Empty until work starts.
