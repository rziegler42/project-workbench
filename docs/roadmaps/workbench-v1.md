# Roadmap: workbench-v1

Status: Active
Updated: 2026-11-05

This roadmap is direction only. It does not authorize implementation and does not
change any plan. A candidate is referred to as `workbench-v1#<id>`. Candidates are
identified by a topic slug and carry no required order; the dependencies are hints, and
what is learned along the way may reshuffle, add or drop candidates.

## Purpose

Build the first version of the project-workbench installer and its first modules, as
specified in `docs/specs/`: a neutral installer that creates and maintains projects
from packages of modules, with a programming way of working (`code-work`) on top of a
shared `groundwork` module. Claude is the one harness that has a module; opencode is
specified and has none (`verify-opencode` and `opencode-harness`).

## Bootstrap

History, kept short. This repository was built before the system it describes existed, by hand under the
rules of its own `AGENTS.md` and `docs/plans/README.md`. `adopt-conventions` moved those documents to the
current conventions on 2026-10-19, and the first commit already left out the harness files and the old
template's manifest. The mechanical pieces that were once still to come (hash-bound approval, the guarded
store, the checks and the commit helper) are built, and plans here are approved with `wb approve-plan` and
committed through the git helper. The part of that order that is still open is `self-hosting` and
`adopt-existing-repository`.

## Current state

- The old template created this repository. `adopt-conventions` is done (2026-10-19):
  the repository's own documents follow the new conventions, and harness files and the
  old template manifest are excluded from git. The old template is retired as a source at
  `self-hosting`: nothing tracked here depends on it. What remains is the owner's, outside this repository: archiving the
  two old repositories (`global-config-migration`). The owner reset `~/.claude` to the harness's defaults on 2026-10-29 and
  kept the former configuration as a backup.
- Seven specifications are approved by the owner (2026-10-19) and read `Current`:
  `terms`, `module-contract`, `repository-boundary`, `trust-and-approval`,
  `groundwork`, `code-work` and `harness-modules`.
- Twelve decision records were accepted on 2026-10-19 and five more on 2026-10-20, recorded in
  `docs/decisions/`.
- `installer-core-verifier` is built and its language decision is accepted
  (`2026-10-19-implementation-language`, 2026-10-19): a Python 3
  package `workbench/` with the safe filesystem layer, hashing, declaration and module
  verification, set verification and `python3 -m workbench verify`. It writes nothing
  into a project. `module-contract` records the concrete schema it accepts.
- `module-approvals` is built (plan `2026-10-19-module-approvals`, increments A to K): the guarded
  store at a fixed location and its personal settings; the compiled hard-stop floor; approval
  records for modules and packages; first-party approvals shipped with the workbench; the approval
  request and gate; the owner-run `approve` command, from a directory or from a source downloaded
  inertly into the store's cache with its commit recorded; helper pins, the `launch` command and the
  `wb` launcher. It writes nothing into a project. `trust-and-approval`, `repository-boundary` and
  `module-contract` record the formats and rules it built. The two decisions it proposed were
  accepted on 2026-10-20.
- Found while building it, for later candidates: `python3 -m workbench` run from inside an
  untrusted project lets that project's code run first, so the harness must call the `wb` launcher
  and not the `-m` form (decision `2026-10-20-isolated-launcher-invocation`, accepted); a module has no field to declare an added hard stop; and nothing removes
  cache copies, shipped records of earlier releases or leftover `bin/run/` directories.
- `installer-interface` is done (plan `2026-10-20-installer-interface`, completed): the spec
  `docs/specs/installer-interface.md` is Current, approved by the owner on 2026-10-20, and covers the target rules, the
  commands, the preview and approval, the output and the exit codes. It departs from the wording of the candidate below in
  three places, listed in the spec under "Departures from the roadmap's wording".
- `base-and-manifests` is implemented (plan `2026-10-20-base-and-manifests`, increments A to I; its
  completion is derived from that plan): the `base/` content and its loader, the canonical
  committed manifest with the project seed and ID, the write plan with its digest, `wb preview
  install` (read-only) and the owner-run `wb install` into a missing, empty or lone-`.git` target,
  with the acknowledgement baselines and the first-seen record written to the guarded store.
  It ended with `harness not attached` until `claude-harness`. Its three decisions were
  accepted on 2026-10-20. It writes the empty `.git` itself and runs no program in the target, after a
  security review found that `git init` followed a link planted at `.git`.
- `ownership-and-upgrade` is implemented (plan `2026-10-20-ownership-and-upgrade`, increments A to M;
  its completion is derived from that plan): strict slot blocks, the hash-checked file replace, the
  readers for the acknowledgement baselines and the existing project, the owner-run `wb acknowledge`,
  `wb preview upgrade` and `wb preview add` (read-only), and the owner-run `wb upgrade` and `wb add`,
  with classification of every path, a marker and read-back on the write, and no git and no
  deletion. Its two decisions (`2026-10-20-acknowledge-before-upgrade`,
  `2026-10-20-upgrade-needs-no-git`) were accepted on 2026-10-20. The owner-class declaration field is
  deferred; a rerun after a part-way failure is not repaired (the plan's Result lists the limits).
- `claude-harness` is implemented (plan `2026-10-20-claude-harness`, increments A to L; its completion
  is derived from that plan): the Claude formats verified against Claude Code 2.1.305, the neutral
  skill, agent and command reader, the layout field, translation and rendering (the `deny` rules for
  every owner-run command), the first-party module `claude` in `packages/workbench/` with its
  shipped approval, the owner-run `wb attach`, `wb install` attaching as its last step, and the
  read-only `wb check` (harness drift, strays, other harnesses' files, tracked output and pointers,
  the manifest), which reads `.git/index` itself and runs no git. An adversarial security pass found
  nothing above Low unresolved. The hand run in a live `claude` session was not done. The plan's Result
  and `harness-modules.md` ("As built, and its limits") list the limits. The compaction guidance is
  a policy bullet from `compaction-guidance`; no Compact Instructions section is rendered.
- `groundwork-module` is implemented (plan `2026-10-21-groundwork-module`, increments A to I; its
  completion is derived from that plan): the first-party module `groundwork` in
  `packages/workbench/` with the four READMEs, the `docs-index` and policy blocks and three skills
  (`draft-spec`, `draft-roadmap`, `draft-decision`), shipping no code; the reference index format
  (`docs/references/index.json`, canonical JSON); and the document and reference checks, which the
  installer runs in `wb check` for a project that has the module. Two adversarial security passes
  found nothing above Medium unresolved. The package was released again with its approvals. The two
  decisions it proposed (`2026-10-21-reference-index-format`,
  `2026-10-21-installer-runs-document-checks`) were accepted on 2026-10-21. The hand run in a live `claude`
  session was not done. `groundwork.md` ("As built, and its limits") lists the limits.
- Git work lives in its own module (plan `2026-10-22-safe-git-module`, increments A to E; it carries out
  `2026-10-22-git-work-in-its-own-module` and has no roadmap candidate, so its completion is not derived).
  The first-party module `safe-git` provides the capability `commit` and ships `wb run safe-git commit` and
  `remove` and the neutral skill `commit-changes`. `code-work` keeps `check`, `plans` and `report` and
  requires `commit`. The code moved unchanged; the attribution setting is `.workbench/safe-git.json`.
  `docs/specs/safe-git.md` records it. The hand run of install and commit in a project is still to do.
- Model calls go through thin vendor bridges (plan `2026-10-22-ask-codex-bridge`, increments A to E; it carries
  out the first part of `2026-10-22-model-calls-go-through-vendor-bridges` and has no roadmap candidate, so its
  completion is not derived). `docs/specs/model-bridge.md` is the contract (version 1). A helper may run another
  installed module's pinned command through the kit's `wbkit/call.py` and `wb run --provides <capability>`
  (`module-boundary.md`). The first-party module `ask-codex` provides the capability `model-bridge` and the
  command `ask-codex ask`; it passes the conformance checklist against a fake `codex` program, and no test starts a
  real one. Security and workflow reviews found no Critical or High finding. The review engine and the
  action-review engine (candidates below), a second vendor and the hand run against a real Codex are still to do.
- Plan approval is a recorded approval (plan `2026-10-22-plan-approval-records`, increments A to F; it had
  `Candidate: none`, so its completion is not derived). The installer records an owner-made approval per project
  (`wb approve-plan`, `wb plan-status`); the process module declares an `approval` command and the `code-work` helper's
  `region` subcommand computes the plan's hashed region. The decision
  `2026-10-22-installer-records-plan-approval-module-computes-region` was accepted on 2026-10-22. The candidate
  The first candidate for this work was too large for one plan and is split into `checkpoint-settings-and-caps`,
  `increment-loop-and-review-skills`, `push-checkpoint`, `compaction-guidance` and `delegated-approval`; the older
  plans, specs and decisions that speak of that one candidate mean this group. Security and workflow reviews found
  nothing above Medium unresolved; the hand run in a live project is still to do.
- The checkpoint settings, the loop caps and the edit gate are implemented (plan
  `2026-10-22-checkpoint-settings-and-caps`, increments A to H; its completion is derived from that plan once it is
  completed). A process module declares `checkpoints`, `caps` and `approval.active`; `code-work` declares its eight
  checkpoints and three caps and ships the `active` subcommand; the personal settings gain `caps`; the read-only
  `wb settings` prints the effective values; and the installer's `wb gate <harness>` refuses a file edit while a plan
  under way is not approved, rendered into the Claude harness as a `PreToolUse` hook (the Claude module now provides
  `hooks`) together with a deny on edits to the rendered settings file. The tool-to-field table is the harness
  layout's, not the installer's, which departs from the wording of the plan. when this plan closed `delegate` had
  no effect (the delegated plan approval below gives it one for a plan's approval), nothing read a cap, a project could
  not lower one, and the hook was seen working in a live Claude session on 2026-10-22 (Claude Code 2.1.307; the owner's check,
  criterion 9 of the plan), which also found that the deny on the rendered settings file does not hold from a
  subdirectory (corrected by plan `2026-10-22-absolute-settings-deny`, which renders the absolute patterns; the owner's
  recheck on 2026-10-23 confirmed it). The decision `2026-10-22-installer-owns-the-edit-gate` is Accepted. A
  project-level setting that the installer can read without naming a module, so that a project may lower a cap, is
  not a candidate yet; add one if the owner wants it. A security review found one Medium finding, fixed; the fixes had
  no second reviewer.
- The increment loop and the review skills are implemented (plan `2026-10-23-increment-loop-and-review-skills`, increments
  A to C; completion derived): a neutral `reviewer` agent (`tools: read, search`; it returns findings and a recommendation,
  never a verdict) and the skills `run-increment`, `request-review` and `evaluate-findings` in `code-work`. The Claude layout
  renders the agent with a `Read`, `Grep` and `Glob` allowlist. Not seen in a live session; the caps the skills tell the agent
  to count are not enforced; no security pass over the agent's restriction.
- The push checkpoint is implemented (plan `2026-10-23-push-checkpoint`, increments A to D; completion derived):
  `wb run safe-git push-check` (a scan of the commits to be sent for credential patterns, local refs only),
  `wb run code-work shared` (reads `.workbench/shared-branches.json`) and the skill `push-changes`; the rendered Claude
  settings ask on every push. The skill is advice, the harness's prompt is what the owner answers, the scan's patterns are a
  narrow list, and no live session was used.
- The compaction guidance is implemented (plan `2026-10-23-compaction-guidance`, increments A and B; completion derived): a
  bullet of the `code-work` policy block. There is no rendered "Compact Instructions" section and no hook; it is advice only
  and was not used in a live session.
- The edit gate's input bound is checked only when a plan is under way (plan `2026-10-23-gate-input-bound-only-under-way`,
  `Candidate: none`): the hook reads at most 16 MiB and applies the 65,536-byte bound after `active` reports a plan under
  way. A test module stalled once during the work and the cause was not found.
- The review engine is implemented (plan `2026-10-23-review-engine`, increments A to F; completion derived): the module
  `review-engine` provides `peer-review`, keeps a sealed review state with bounded rounds, and runs a bridge only through
  `wb run --provides model-bridge`. A module command may declare `owner` arguments (`extend`, `reset`, `archive`, `prune`,
  `amend` here), which an attached harness that provides permissions denies the agent. The owner ran a real Codex through the
  `ask-codex` bridge by hand on 2026-10-23 (Codex CLI 0.163.0). No default bridge exists, the bridge reports no model name or
  token total without `--model`, and `--effort`, a missing sign-in and a malformed real reply were not tried.
- Delegated plan approval is implemented (plan `2026-10-23-delegated-approval`, increments A to F; completion derived): the
  installer's `wb delegate-approve-plan` records an approval made by a delegate from a converged, sealed review of the same
  bytes; the `review-engine` module answers `convergence`, a process module declares `delegable`, and the skill
  `delegate-approval` explains it. No vendor bridge ran against it; the owner waived that. Accepted limits: a provider may
  drift after approval, and two of this repository's 27 plans are no longer delegable.
- The superpowers inventory and the first ports are done (plan `2026-10-23-port-superpowers`, increments A to G; completion
  derived): `superpowers-ports.md` lists the plugin's 15 skills (version 7.0.0, with source URL, retrieval date and hashes), 11
  of them used by the owner's files, and what became of each; the decision `2026-10-23-one-owner-per-skill-name` was accepted
  on 2026-10-24; `brainstorm` is in `groundwork`, and `test-first`, `diagnose-failure` and `verify-before-claiming` are in
  `code-work`. The differences from `receiving-code-review` are recorded, not closed. No live session.
- `remote-runner` is a module (plan `2026-10-24-remote-runner-module`, increments A to G; completion derived): remote job
  profiles in `.workbench/remote-runner.toml`, a wrapper over the external `remote-runner` program, a checker, and the skill
  `run-remote-job`. `docs/specs/remote-runner.md` reads `Current`. It was tested only against fake programs; the external
  program must read the new project file before a real job can run, and that change is outside this repository.
- Owner-run arguments are enforced in code (plan `2026-10-24-owner-run-in-code`, increments A to D; `Candidate: none`): `wb run`
  and `wb launch` refuse an owner-run argument unless standard input and output are both terminals, and `wb launch` checks
  that an installer-made pin's declaration is the one the owner confirmed. A process that opens its own pseudo-terminal passes
  the test, the pinned helper run directly is not a workbench route, and a pin the owner typed trusts the project's own
  declaration. The security review found no Critical or High finding; its fixes had no second reviewer.
- The `mempalace` module is implemented (plan `2026-10-24-mempalace-module`, increments A to F; completion derived): it
  provides `memory-recall` with the agent-safe `status` and `search` and the owner-run `init` and `mine`, a policy block and
  the skill `recall-memory`. The facts come from running the real `mempalace` 3.11.0 in a scratch directory; `search`
  rewrites the program's bookkeeping, which the owner accepted. No live session; the last security-review fixes were not
  reviewed. `docs/specs/mempalace.md` and `docs/specs/knowledge-tools.md` record it.
- The former global Claude configuration held work that the design had not accounted for: agents, skills, hooks and
  instruction text. The owner reset it on 2026-10-29 and kept a backup; `docs/specs/global-config-inventory.md` is the record
  of the state before. The owner treats the old repositories and that configuration as lessons learned, not authority. The
  seven candidates that precede `global-config-migration` came from a first-pass inventory; what to re-adopt from the backup
  is settled in `global-config-migration`.
- `security-review-module` and `verilog-module` are built by the plans that name them
  (`2026-10-24-security-review-module`, `2026-10-28-verilog-module`).
- Out of the first version: Codex as a harness, a way of working for CAD and EDA,
  harness swap, three-way merge on upgrade, and migration of the old projects.

## Order

There is none. Candidates carry no required order, as `docs/roadmaps/README.md` says; read each candidate's dependencies and
promotion trigger. A list of identifiers here would drift as candidates are added.

## Candidates

### approve-specs — Approve the specifications and record the decisions

**Outcome:** the specifications are reviewed and approved by the owner, and the
durable choices are written as decision records, so later work is built against a
settled design.
**Dependencies:** none.
**Boundary:** documents only. Possibly an independent review of the specs, at the
owner's request. No code.
**Promotion trigger:** the owner judges the design closed enough to build against.

### adopt-conventions — Adopt the new document conventions in this repository

**Outcome:** this repository's own documents follow the new conventions, so the work
that follows is planned, recorded and archived the way the specs say. The plans,
decisions and roadmaps READMEs and `AGENTS.md` describe dated plan and decision names,
the `Candidate:` and `Specs:` lines, and no fixed `next.md`; the placeholder `next.md`
is replaced by that convention; harness files and the old template's manifest are
excluded before the first commit; and the documents state which checks are enforced by
the installer once built and until then by the owner in session.
**Dependencies:** `approve-specs`.
**Boundary:** documents and exclude entries only. No code. No mechanical enforcement.
Removing a stage-0 file uses the approved removal helper, with the owner's approval.
**Promotion trigger:** `approve-specs` complete.

### installer-core-verifier — Installer core and the declaration verifier

**Outcome:** a small installer core that writes only inside a target through a safe
layer, and a verifier that reads a package and its modules and accepts or refuses
them exactly as `module-contract` states, writing nothing when any module fails.
**Dependencies:** `adopt-conventions`.
**Boundary:** declarations, types, capabilities, requirements, conflicts and
verification. It writes nothing into a project. No approvals, manifests, harness or
upgrade. The safe-write rules are ported deliberately, with tests, from the old
template.
**Promotion trigger:** `adopt-conventions` complete.

### module-approvals — The guarded store and module approvals

**Outcome:** every command ensures the user-level guarded store exists and is seeded;
the hard-stop floor is compiled into the installer and also seeded into personal
settings; a package is downloaded inertly into the store's cache; module and package
approvals are recorded and verified against declaration and content hashes;
first-party approvals can be generated at release time and are read from the workbench
distribution; and the `wb` launcher and its pins exist.
**Dependencies:** `installer-core-verifier`.
**Boundary:** the store, module and package approvals, the verifier, and the launcher.
No project is written, and there is no plan approval or delegation helper yet.
**Promotion trigger:** `installer-core-verifier` complete.

### installer-interface — The installer's commands and options

**Outcome:** a specification of the installer's command line: the commands (install,
attach, upgrade preview, add module, verify, check), their options, exit codes, and the
preview and output contract. Requirements settled so far:

- The target directory is one value with two spellings, a positional `<target>` or
  `--dir <path>`, accepted by every project command. If neither is given the target is `.`.
  If both are given and resolve to the same directory that is accepted; if they
  differ the command refuses and writes nothing.
- The target is resolved to an absolute path once, and everything after that works
  from the resolved path.
- Whether a command creates a new project or works on an existing one is decided from
  the target's state, not from the spelling: an empty or missing directory (a lone
  `.git` is allowed) is new; a directory with its own `.git` and a manifest file is existing,
  decided from files without running git; anything else is refused with nothing written.
- Commands that write print the resolved absolute target before the preview.
- The home directory, the filesystem root and the guarded store are refused as targets.

**Dependencies:** `module-approvals`, because the approval and store behavior decides
which options are needed.
**Boundary:** a specification only, approved by the owner. Option names and formats stay
proposals until the code that uses them exists. `installer-core-verifier` defines only
its own verify command.
**Promotion trigger:** `module-approvals` complete.

### base-and-manifests — Base, manifests and installing into an empty target

**Outcome:** install creates the base content, the project seed and ID, the committed
manifest and the tracked `.workbench/.gitignore` in a new target, from a chosen set of
modules, without a harness step yet.
**Dependencies:** `module-approvals`, `installer-interface`.
**Boundary:** the base and the committed manifest only. Attach, upgrade and the local
manifest are later candidates. The mandatory-harness rule is enforced when attach
exists.
**Promotion trigger:** `module-approvals` and `installer-interface` complete.

### ownership-and-upgrade — Ownership, slots and non-destructive upgrade

**Outcome:** owner classes are recorded, slots and blocks work, and an upgrade shows a
full preview and changes nothing until approved, leaving conflicts alone and offering
an append on approval where a seeded file lacks a needed slot.
**Dependencies:** `base-and-manifests`.
**Boundary:** the upgrade and its preview only. Format migrations are not included.
**Promotion trigger:** `base-and-manifests` complete.

### claude-harness — Claude harness module, attach and check

**Outcome:** a Claude harness module, an attach operation that writes only per-clone
harness files, rendering of the neutral permission rules, the root file, and a check
that reports drift, stray files and tracked-pointer problems.
**Dependencies:** `ownership-and-upgrade`, `module-approvals`.
**Boundary:** Claude only. Translating neutral skills, agents and commands, with
fail-closed handling of restrictions the harness cannot express. It must render a `deny`
for the owner-run commands `wb install`, `upgrade`, `add`, `attach`, `acknowledge`, `recover`,
`approve`, `pin` and `release-approvals` (`trust-and-approval.md`, "Rendering rules"), and call `wb` and not the
`-m` form. `opencode-harness` carries the same duty.
**Promotion trigger:** `ownership-and-upgrade` and `module-approvals` complete.

### verify-opencode — Verify the installed opencode against the specification

**Outcome:** a written, evidence-based answer to the open questions about opencode:
the formats of its installed version, how a per-clone permission rendering can be done
without editing a tracked file, whether a specific tool can be given to one agent, and
how compaction guidance is delivered.
**Dependencies:** none technical; best after `claude-harness` so the comparison is
concrete.
**Boundary:** investigation and a recorded conclusion. No harness module is built.
**Promotion trigger:** the owner chooses to proceed with opencode.

### opencode-harness — opencode harness module

**Outcome:** an opencode harness module that attaches and checks as `claude-harness`
does, with whatever `verify-opencode` showed to be possible.
**Dependencies:** `claude-harness`, `verify-opencode`.
**Boundary:** opencode only.
**Promotion trigger:** `verify-opencode` concluded.

### groundwork-module — The `groundwork` module

**Outcome:** the module that provides specs, roadmaps, decisions and references, with
its templates, skills, indexes and checks. It ships no code.
**Dependencies:** `ownership-and-upgrade`, `claude-harness`.
**Boundary:** the four document areas and their checks. The researcher and the
`fetch-reference` tool are the separate `groundwork-research` module.
**Promotion trigger:** `claude-harness` complete.

### researcher-fetch-tool — The `groundwork-research` module

**Outcome:** the optional `groundwork-research` module: a least-privilege researcher
agent and a dedicated `fetch-reference` tool that only it holds, with the size, type
and provenance limits the specification states. The confinement is the tool, not a guard hook: the owner's earlier
researcher agent, which relied on a hook over raw web tools, is a lesson learned and is not ported.
**Dependencies:** `groundwork-module`, and a verified way for each harness to give one
tool to one agent (`claude-harness` for Claude, `verify-opencode` for opencode).
**Boundary:** web references only. Remote job output and the knowledge base are other
channels.
**Promotion trigger:** `groundwork-module` complete and tool exposure verified.

The `code-work` module (`docs/specs/code-work.md`) is too large for one plan, so it is
three candidates built in this order, each leaving a working module. The first plan
creates the module; the next two add to it and release the package again.

### code-work-plans — The `code-work` module: plans and its read-only helper

**Outcome:** the process module `code-work` exists in `packages/workbench/`: the plan
format, the `docs/plans/` README, a `docs-index` entry, a policy block, a skill for
drafting a plan, and one shipped, self-contained helper whose read-only subcommands
`check`, `plans` and `report` are run as `wb run code-work <subcommand>`, a command the module
declares, through the launcher; the installer pins the helper when the owner confirms the install. It
proves the path every later helper subcommand uses: shipping, pinning, launching and reading untrusted
plans.
**Dependencies:** `module-approvals`, `claude-harness`, `groundwork-module`.
**Boundary:** reading only. No commit or remove, no approval record, no review loop,
caps, checkpoint or push rule. Until plan `2026-10-22-plan-approval-records`, approval was the owner's
explicit statement in session and the policy block says so.
**Promotion trigger:** `groundwork-module` complete.

The next four candidates carry out `docs/specs/module-boundary.md` and the decision
`2026-10-21-module-code-lives-in-modules`: module-specific code, tests and tooling leave the
installer for the modules. The open `code-work-plans` plan was reconsidered after
`module-commands` and its increments F to H were amended for the installer pinning declared helpers
(`2026-10-22-installer-pins-declared-helpers`).

### module-boundary-kit — The kit and the maintainer directories

**Outcome:** the installer's reading code (`safefs`, `display`, project finding and the
project ID) lives in a standard-library kit, `wbkit`, with an API version; the launcher can
start a Python helper through a runner that enforces the version the module declared; a
module may hold `tests/` and `tools/`, which are hashed and approved and never installed;
one command runs the installer's tests and every module's.
**Dependencies:** `code-work-plans` (increments A to E).
**Boundary:** no new user-visible command and no module code moves except one module's
tests, as proof. `commands`, `checks` and `wb run` are later candidates.
**Promotion trigger:** the specification `module-boundary` is Current.

### module-commands — Module commands and `wb run`

**Outcome:** a module declares `commands`, the verifier checks them, and `wb run` runs the
pinned helper by the rules of the specification, including the pin-path check; `dispatch.py`
and the `code-work` entries in the installer are gone, and the `code-work` tests move into
the module.
**Dependencies:** `module-boundary-kit`.
**Boundary:** commands only. Checks and harness paths are separate.
**Promotion trigger:** `module-boundary-kit` complete.

### module-checks — Module checks and the groundwork move

**Outcome:** a module declares `checks`; `wb check` runs them and prints their bounded
lines; the document checks (`doccheck`, `refcheck`, `refindex`) and their tests move into
`groundwork` as check helpers over the kit.
**Dependencies:** `module-commands`.
**Boundary:** the rules a check reports do not change. A security pass is part of it,
because the helpers read hostile repository content.
**Promotion trigger:** `module-commands` complete.

### module-harness-paths — Harness paths from the harness module

**Outcome:** the harness table in `check.py` and the settings path in `layout.py` are read
from the harness module's `layout`; a
boundary test fails if the installer or its tests name a first-party module, helper,
harness name or harness path.
**Dependencies:** `module-checks`.
**Boundary:** no new harness. `opencode` and `codex` entries with no module are removed.
**Promotion trigger:** `module-checks` complete.

### code-work-commit — The commit helper

**Outcome:** the helper gains `commit` and `remove`, so a commit is local, lists exact
paths, carries no tool attribution unless a project says otherwise, and can be the first
commit in a repository with no commits; it leaves the acknowledgement baselines to the
owner, so a change made through it is listed by the next `wb acknowledge`. The helper was built in
`code-work` and then moved to the `safe-git` module (`2026-10-22-safe-git-module`).
**Dependencies:** `code-work-plans`.
**Boundary:** local commits and approved deletions only. It never pushes. The helper
reads a repository the project controls, so a security pass is part of it.
**Promotion trigger:** `code-work-plans` complete.

### checkpoint-settings-and-caps — The checkpoint settings, the loop caps and the gate

**Outcome:** the checkpoint settings (which actions stop for the owner), the loop caps (review rounds and
increment attempts), and an enforcement point that refuses work on a plan whose record does not read `approved`
(a hook or a deny rule the module renders; the record and the `plan-status` command exist already).
**Dependencies:** `code-work-commit`; plan `2026-10-22-plan-approval-records` (built).
**Boundary:** programming only. Settings and the enforcement point; no skills, no reviewer agent, no push rule.
The enforcement point is the installer's `wb gate`, rendered as a Claude hook (built).
**Promotion trigger:** the owner chooses to begin it.

### increment-loop-and-review-skills — The increment loop, the review skills and the reviewer agent

**Outcome:** the neutral skills for one increment (implement, verify, record, stop for the owner), the review
skills (what to ask a reviewer, how to evaluate findings, the review record), and the reviewer agent.
**Dependencies:** `checkpoint-settings-and-caps`.
**Boundary:** skills and one agent definition, in the owner's words and the project's own locations. No review
engine and no vendor.
**Promotion trigger:** `checkpoint-settings-and-caps` complete.

### push-checkpoint — The shared-branch push checkpoint

**Outcome:** a push to a shared branch is a checkpoint the owner decides, with the credential scan before it,
rendered as a rule the harness enforces.
**Dependencies:** `checkpoint-settings-and-caps`.
**Boundary:** the checkpoint and its rule. The commit helper and `remove` stay in `safe-git`.
**Promotion trigger:** `checkpoint-settings-and-caps` complete.

### compaction-guidance — The compaction guidance

**Outcome:** the preservation guidance for compaction, as a bullet of the `code-work` policy block.
**Dependencies:** `claude-harness`.
**Boundary:** the guidance text in the policy block. No rendered "Compact Instructions" section (Claude's
documentation names none), no hook and no wrapper that triggers compaction from outside a session.
**Promotion trigger:** the owner chooses to begin it.

### remote-runner-module — `remote-runner` as a generic module

**Outcome:** the remote-runner configuration moves under `.workbench/`, and fetching
remote job output follows the checkpoint and hard-stop rules.
**Dependencies:** `claude-harness`, `checkpoint-settings-and-caps`.
**Boundary:** the module and its configuration. The `remote-runner` tool itself must
learn the new path, which is a change outside this repository.
**Promotion trigger:** `checkpoint-settings-and-caps` complete.

### review-engine — The review engine

**Outcome:** the review module, which provides the `peer-review` capability and requires `model-bridge`. It holds
the rounds, the sealed review state, the findings schema (blocker, major, minor, nit), `decide`, and the
owner-only `extend`, `reset`, `archive` and `prune`; it reads its bridge, model and effort from its own project
setting `.workbench/<module>.json` and runs a bridge only through `wb run --provides model-bridge`. It replaces the
owner's personal review tool for a project.
**Dependencies:** `checkpoint-settings-and-caps` (the loop caps); the `ask-codex` bridge (plan
`2026-10-22-ask-codex-bridge`).
**Boundary:** one engine that knows no vendor. Where the sealed state lives is decided in its plan (the owner's
tool keeps it in untracked scratch, which a module must not depend on). The bridges are separate modules, one
per vendor.
**Promotion trigger:** `checkpoint-settings-and-caps` complete.

### delegated-approval — Delegated plan approval

**Outcome:** a plan approval made by a delegate under the owner's standing authorization, as the delegation
helper and a record that names its delegate and its review, bound to the same hashed region.
**Dependencies:** `review-engine` (it needs the `peer-review` capability); plan
`2026-10-22-plan-approval-records` (built).
**Boundary:** the delegation helper, its record fields and its verdict rule
(`trust-and-approval.md`, "Plan approval"). The owner's own approval stays as built.
**Promotion trigger:** `review-engine` complete.

### action-review-engine — The action-review engine

**Outcome:** the action-review module (the capability name `action-review` is a proposal), which requires
`model-bridge`, takes facts about an action and returns a verdict with reasons as data, from a rubric and rules.
It writes no `allow` rule and no setting, and its verdict authorizes nothing by itself
(`2026-10-22-model-calls-go-through-vendor-bridges`, decisions 6 and 7).
**Dependencies:** `checkpoint-settings-and-caps`; the `ask-codex` bridge; a way for the module that owns an action to give
the facts before the action is made (open in the accepted record).
**Boundary:** a rubric and rules engine, not a reviewer of documents; the enforcement point that uses its verdict
stays in the owner's own configuration. It is separate from `review-engine`, and a project may install either.
**Promotion trigger:** `checkpoint-settings-and-caps` complete and the facts interface decided.

The next three candidates are the knowledge modules, each solving a different problem and none replacing
another (`docs/specs/knowledge-tools.md`): `mempalace` recalls earlier sessions and decisions, `graphify` shows
structure and impact, and the knowledge base keeps classified online research. They are built in this order,
because the first is the smallest and the least entangled; a shared convention is written down only from what
the first two show.

### mempalace-module — The `mempalace` module

**Outcome:** the first-party module `mempalace`, which provides `memory-recall`: the agent-safe commands
`status` and `search` over the owner's installed MemPalace, the owner-run `init` and `mine`, a policy block and a
neutral skill that route questions and treat answers as data. It is tooling and not an MCP server.
**Dependencies:** `module-commands`, `claude-harness`. The first plan ran the real program in a scratch
palace outside the tracked tree; its findings are in `docs/specs/mempalace.md` ("Evidence").
**Boundary:** the module and its tests, with a fake `mempalace` in the tests. No change to drawer content an agent
can make (a search rewrites the palace's own bookkeeping, which the owner accepted), no
MCP rendering, and no installation or configuration of the program. Writes to the palace are owner-run only.
**Promotion trigger:** the owner approves `docs/specs/mempalace.md` and `docs/specs/knowledge-tools.md`.

### graphify-module — The `graphify` module

**Outcome:** the optional module `graphify`, which provides `code-graph` for questions of structure and impact. It is
designed afresh, with the owner's earlier `graphify` skill, helper and template module (held in the old template repository
and, in part, the former user-level backup) as lessons learned and not as a source to port. It keeps the freshness status and the rule that an old graph is orientation only, written as neutral
skills and a pinned helper. It carries no plan receipt and no gate: the discovery gate was dropped on 2026-10-19
(`code-work.md`: no discovery gate). Whether it is built at all is the owner's choice.
**Dependencies:** `mempalace-module` (for the shared conventions it shows).
**Boundary:** the module and a spec of its own. It does not ingest conversation history or the knowledge base.
The graph output is untracked. This candidate takes `graphify` out of `remaining-modules-rename`.
A read-only check on 2026-10-29 found that the module's files, its helper `tools/graphify` and its agent exist in full only in the old
template repository (module tree of 15 files, hash `00036b7b5933`; helper of 6 files, `a8a2a9e870e5`; head of that repository
`9b0decb8c07f`, 2026-10-19), and that the backup keeps only older dated copies of the skill and the agent (4 files, `7b85d96a59d6`;
`305059869319`). The old template repository is archived only after this candidate has taken what it needs from it. A hash here is the
first 12 hex digits of the SHA-256 of the sorted relative file names and contents.
**Promotion trigger:** `mempalace-module` complete and the owner chooses to begin it.

### knowledge-base-package — The knowledge base as a package

**Outcome:** the knowledge base adopts the workbench's package declaration, gets its
generic name, provides its own capability (`knowledge-base`), and is read through a read-only skill. It holds,
retains and classifies the owner's online research per domain, each item with its provenance.
**Dependencies:** `claude-harness`, `groundwork-module`; the conventions of `mempalace-module` and
`graphify-module`.
**Boundary:** the knowledge base's own repository changes. Its name is still open. The existing knowledge base and its
authoring skill are lessons learned: the package is designed against the workbench's contract, and nothing is carried over
because it exists. It does not hold decisions or conversation, and nothing tracked cites a path into it.
**Promotion trigger:** `groundwork-module` complete and the name chosen.

The next two candidates serve the knowledge base's model calls (`knowledge-base-package`), which go through the bridges. They rest on
the owner's measurements of 2026-11-01 with `codex-cli` 0.163.0, run directly with the bridge's own safety options and through
`ask-codex`, one run per variant, scripts not kept. The measurements are in the evidence notes of the knowledge base's overview spec,
which is untracked, so the figures are quoted here and not cited by path: a one-word prompt used 15,836 input tokens (12,288 cached);
disabling twelve tool-adding features gave 13,669 and also disabling the shell tool 13,029; with both disabled four canary probes (a
file in the working directory, one above it, one outside the project by absolute path, and a shell command) all failed for want of a
tool, while with the defaults the three reads succeeded and the shell command ran; a 400-item batch cost 17,050 input tokens and was
answered correctly. Cached counts varied from 0 to 12,288 between runs. A later run asked the confined program to list its tools: it
still listed an image viewer, a patch tool, MCP resource readers, agent-starting functions and a web tool, and the web tool fetched a
public page in that configuration; setting the program's `web_search` option to disabled removed it, and the setting that should
remove the image viewer did not. A tool list is the model's own report.

### bridge-confine-and-usage — Confine the vendor program, report its token detail, correct the bridge spec

**Outcome:** the `ask-codex` bridge can start its program with the tool features, the shell tool and the web tool disabled, so that in
the owner's probes a prompt of captured text could not make the program read files, run commands or fetch a page; it reports the cached
and reasoning token counts that the program's event stream carries, with a total only where the program reports one, and states that
the cached count is part of the input count; and `model-bridge.md` stops implying that `--root` scopes what the program reads. The
option is opt-in, because the review engine needs file access to read plans; a caller that sends captured text always passes it. Each
bridge release is accepted for untrusted text only if the four file and shell canaries, a probe of the web tool and a check of the
tool list against the list recorded for that release pass, because the protection depends on the program's version and feature list.
**Dependencies:** none. The bridge and its contract (version 1) are built.
**Boundary:** the `ask-codex` module, its tests and `model-bridge.md`, and the reading of the bridge's object by the two engines that
call a bridge (`review-engine` and `action-review`), with their tests and specs, because the accepted decision
`2026-11-01-bridge-contract-version-2` changes the contract number, a class name and the `usage` object that they check exactly. It
adds no bulk or batch option: batching many short items into
one call fits the existing 256 KB prompt limit and is the engine's work. `--confine` is a tripwire plus tests and not a boundary: the
confined program still lists an image viewer and a patch tool (its writes are refused by the read-only sandbox), MCP resource readers
and agent-starting functions, and the boundary text says so. The reasoning count is reported as an informational figure that no
caller adds to or subtracts from another count; whether the program includes it in the output count is not relied on.
Two questions are the plan's to settle: whether the list of disabled features is fixed or derived from the program's own feature list
(the canary test being the backstop either way), and whether `--schema` accepts an array at the top level or a batch reply must be an
object that holds the array, which has not been tested. A change to the `usage` object is a change to the contract and is decided in
the plan.
**Interchangeable bridges.** The owner requires that `ask-codex` and the Ollama bridge can replace one another without a change in
the caller. This candidate settles the common core in the contract, and the Ollama candidate meets it: the same command shape; the
same five options (`--model`, `--effort`, `--timeout`, `--root`, `--schema`) accepted by every bridge, plus `--confine`, which a
bridge with no tools satisfies by construction; the same success and failure objects; and one error class for a vendor that cannot
be reached, so that neither `program_not_found` nor a new Ollama-only class is the caller's concern. An option that only tunes
behaviour and that a vendor cannot use (`--root` for a server) is accepted and ignored. An option that decides where
content goes (`--server`) is refused by a bridge that cannot honour it, so that local-only content is never served by a cloud vendor
by accident. This is proposed by the decision `2026-11-01-bridge-contract-version-2`, which moves the contract to version 2. What differs between vendors (the model name, whether usage is reported, and
the reasons a call fails) stays in the object's existing fields. The same conformance checklist is run against both bridges.
**Promotion trigger:** the owner chooses to begin it.

### ask-ollama-bridge — A bridge for local models, and an embedding command

**Outcome:** a first-party bridge module for a local Ollama server, so that a model call needs no vendor program and no cloud: one
prompt in, one JSON reply out, the server's schema-constrained output used for `--schema`, and no file access by construction. The
server's address is never an argument and never in a tracked file: the bridge resolves a named endpoint from the owner's guarded store
(`2026-10-20-fixed-store-location`), chosen by a validated `--server <name>`, so a caller can pick between model machines without
holding an address. The store record says whether an endpoint is authenticated and declares its location class; the transport follows
the scheme (`https` validates the certificate), an authenticated endpoint must use `https` unless its host is a literal loopback
address, and a diagnostic warns when content is sent in the clear. The bridge reaches only the host the record names and does not
verify where that host is. A second command takes a batch of texts and returns the model name, the dimension and the vectors, within the
reply limit (a batch near 100 texts for vectors of about 1,000 numbers), and is offered as a capability of its own, so a consumer can
require embeddings alone.
**Dependencies:** `knowledge-base-package` for the first consumer; the guarded store (`module-approvals`). It follows
`bridge-confine-and-usage` so that the contract is amended once.
**Boundary:** the new module, its tests against a fake server, and the contract: the bridge opens a connection, so guarantee 7 of
`model-bridge.md` and the search for a vendor program are amended, by a decision record if the contract's version changes. Model
names stay an option, validated like the codex bridge's. Redirects to another host are not followed and every request has a hard
timeout. It installs, pulls and serves no model, and does not choose a model, retry or fall back. It reads no files, so the review
engine cannot use it as a reviewer yet: that engine relies on the vendor program opening the document from its working directory,
and a change to send the document in the prompt is a separate piece of work, not part of this candidate. Two behaviours of the server are the
plan's to settle, and neither was re-checked on 2026-11-01: the server's default context window is small and a longer prompt may be
cut silently, so the bridge sets the context size from the store's record for the endpoint and checks that the reply was not cut off;
and a model that reasons can use up its token limit in its reasoning and return an empty reply, so the plan maps `--effort` to the
server's thinking setting and reports an empty or cut-off reply as an unusable reply, never as a success.
**Promotion trigger:** `bridge-confine-and-usage` complete and the owner chooses to begin it.

### bridge-model-configurations — Model configurations for each endpoint, and a context ceiling

**Outcome:** the owner's endpoint file describes each model that may be used on a server, so that a bridge to a server uses only a
model the owner configured, and the window of a call is the model's own. Each endpoint record holds a configuration section for every
allowed model: its kind (chat or embedding), the largest context it accepts, an optional lower default window, and an optional
estimate of bytes per token. A model that is not configured, or is configured for the other kind, is refused before anything is sent.
A caller may ask for a smaller window and gets an error, with nothing sent, when it asks for more than the model's maximum. A prompt
that is probably larger than the window is refused before it is sent, because the server of the first run (2026-11-02) cut such a
prompt without an error and reported about half the window. A read-only command shows which configured models the server has. The
file is named for what it holds, in a step after the first real run of the new format.
**Dependencies:** `ask-ollama-bridge` complete. The accepted decision `2026-11-01-endpoint-records-in-the-store` is superseded on the
format of a record, by a new decision the owner accepts.
**Boundary:** the endpoint file's format and the one helper that reads it, its spec and its documents. The option for a smaller window
belongs to the Ollama bridge and not to the contract's common core, so `ask-codex` and the contract are unchanged. The older format is
refused and is not read as a fallback. It reads no token count from the server and holds no credential, and a second bridge to a
server, an exact count of tokens and a command that reads each model's window from the server are not part of it.
**Promotion trigger:** `ask-ollama-bridge` complete and the owner chooses to begin it.

### review-profiles — Review settings as owner profiles, with a ladder for each kind of review

**Outcome:** the choice of the bridge, model and effort for a review is the owner's, held in one file in the guarded store that lists
named profiles and, for each kind of review, a ladder that uses a different profile in each round. A project tracks no review
setting, so a vendor's change of model or cost is an edit to the owner's file and never to a project. Both engines that ask a model for
a review read it, the Ollama bridge's server and thinking options are carried by a profile, and `wb install` writes a default file when
none exists, from the bridges that are installed. A delegated plan approval can be limited, by an owner setting, to a review whose
converging round ran on a profile the owner lists.
**Dependencies:** `ask-ollama-bridge` and `bridge-model-configurations` complete. The decisions
`2026-11-04-review-profiles-in-the-guarded-store` and `2026-11-04-delegated-approval-checks-the-profile-of-the-last-round` are
accepted by the owner on 2026-11-04; the first supersedes `2026-10-26-action-review-reads-the-review-setting` and supersedes in part decision 5 of
`2026-10-22-model-calls-go-through-vendor-bridges`.
**Boundary:** the profile file and its reader, the ladder in the review engine and in the action-review engine, the option a bridge
declares for a review, the default written by the installer, `wb doctor`, the owner setting for delegated approval and the specs that
describe them. A per-project choice of ladders, a tracked setting of any kind, a call-time choice of profile and a check against a
vendor's model list are not part of it, and the tuning of a model stays in the endpoint file.
**Promotion trigger:** the two decisions are accepted (met on 2026-11-04) and the owner chooses to begin.

### port-superpowers — Port the superpowers skills the owner uses into neutral skills

**Outcome:** an inventory of the superpowers skills the owner's former global configuration (the backup) and agents
rely on (brainstorming, planning, plan execution, code review, test-driven development, systematic
debugging, verification before completion, worktrees and branch finishing), each recorded as used
or not, already covered by a workbench rule or skill, or a gap; the module each ported skill belongs
to; and the first ports as neutral skills, written in the workbench's own words, in the project's
own locations (`docs/specs/`, `docs/plans/`), with no harness named. Brainstorming is expected to
go to `groundwork` as a step before `draft-spec`; the rest to `code-work` or `safe-git`, unless
the inventory shows a practice that every process shares, which would argue for a module of its own.
**Dependencies:** `claude-harness`, `groundwork-module`, `increment-loop-and-review-skills` (which owns the
increment loop, review and reviewer-agent skills).
**Boundary:** the inventory, the placement decisions, and the skills the inventory selects first. The
git-specific slice was taken by `2026-10-22-safe-git-module`: the `commit-changes` skill is written, and
`using-git-worktrees` and `finishing-a-development-branch` are recorded as not ported, with the reasons, in
`docs/specs/safe-git.md`; this candidate starts from that and does not revisit git.
Each further port is its own candidate. Whether the superpowers wording may be reused is checked
against its licence before any text is copied, and the default is to write new text. The reset of `~/.claude` on 2026-10-29
moved the former configuration into a backup; whether any superpowers item returns is settled in `global-config-migration`.
**Promotion trigger:** `increment-loop-and-review-skills` complete.

The next seven candidates (`architecture-decisions-merge` to `mempalace-scoping`) came from a first-pass inventory of the owner's global Claude configuration and the two earlier
repositories, made on 2026-10-24. The owner treats those as lessons learned, not authority: each candidate asks what problem
the old item solved, whether it is still a problem, and what the best form is in the workbench, and the answer may be a port,
a redesign or a drop. The inventory was not compared line by line (the hook scripts, `settings.json` and `CLAUDE.md` were
read by their headers and first lines), so it is not claimed complete; `global-config-migration` completes it.

### architecture-decisions-merge — The decision rules the owner's skill carries

**Outcome:** `draft-decision` in `groundwork` carries the rules of the owner's `architecture-decisions` skill that it lacks
(never `Accepted` on design approval alone, supersede and never edit an accepted record, the status vocabulary and its
checks), in the workbench's own words; the workbench's dated names win where the two differ.
**Dependencies:** `groundwork-module`.
**Boundary:** the `draft-decision` skill and its tests. It edits a shipped package, so its approval is released again by
the owner.
**Promotion trigger:** the owner chooses to begin it.

### agent-confinement — Agents with declared limits

**Outcome:** a neutral agent declares its limits as data (the paths it may write and the commands it may run), and the
installer enforces them with a per-agent hook rendered into the harness, as it enforces the edit gate; the harness layout
declares where its session scratch directory is. An elevated agent has no general shell: scratch execution goes through one
pinned command matched by a fixed pattern.
**Dependencies:** the owner's acceptance of a decision on declared agent confinement (accepted on 2026-10-24: `declared-agent-confinement`);
`claude-harness`.
**Boundary:** the agent fields, the layout's scratch path, the installer's guard and the per-agent hook. It needs a
specification change and an installer change. A script the agent writes and runs is not confined, and the specification says
so. No agent ships with it.
**Promotion trigger:** the decision accepted.

### security-review-module — The security review as a module

**Outcome:** an optional module that holds the `security-review` skill and a security-reviewer agent together, and provides
a capability of that name, so declining the module declines both. `code-work` names no such module; it points to any module
that provides the capability.
**Dependencies:** `agent-confinement`, `code-work-plans`.
**Boundary:** the skill, the agent and its declared limits. The skill's text is read for accuracy and rewritten in the
workbench's words; it is not copied.
**Promotion trigger:** `agent-confinement` complete.

### verilog-module — The Verilog skills

**Outcome:** the optional module `verilog`, with the owner's Verilog simulation skill (`verilog-verilator-sim`) and formal
verification skill (`verilog-sby-formal`) as neutral skills, text only, after a read of their content for accuracy. Both are
written for plain Verilog-2001 and say not to use SystemVerilog, so the module is named for the language. A VHDL or
SystemVerilog module, if the owner writes either, is a separate candidate with its own tools; this one does not widen to cover
them. The skills are split by the rule of `2026-10-23-one-owner-per-skill-name`.
**Dependencies:** `claude-harness`, `code-work-plans` (the general practice skills it extends).
**Boundary:** two skills and their tests. No program is installed or run.
**Promotion trigger:** the owner chooses to begin it.

### cad-modules — The CAD modules

**Outcome:** an optional `freecad` module of twenty skills for scripting FreeCAD 1.1 from Python without the interface: the
original seventeen, plus `freecad-draft`, `freecad-surface` and `freecad-techdraw`. Each example was run headless on
FreeCAD 1.1.4, and anything not run is marked "read, not run". There is no base `cad` module and no owner conventions; the mesh
script is bundled as a plain file, not a pinned helper. The advice about the FreeCAD MCP server is kept as the `freecad-mcp` skill.
**Dependencies:** `claude-harness`, `groundwork-module`.
**Boundary:** the `freecad` module and its tests. No program is installed or pinned. A way of working for CAD (`cad-work`)
and skills for CAM, BIM, OpenSCAD and Material stay deferred. A read-only check on 2026-10-29 found the sources in full only in
the old template repository (`cad`, 6 files, hash `9aa7270b0ba8`; `cad-freecad`, 20 files, `f99af34499e2`, of which the skill is 12
files, `f2f93e728e78`); the backup keeps one dated copy of the skill's script and no more. The old template repository is archived
only after this candidate has taken what it needs from it. The hashes are computed as for `graphify-module`.
**Promotion trigger:** the owner chooses to begin it.

### global-settings-check — Where a global setting may conflict with a project's

**Outcome:** an owner-run, read-only command of the installer that reports where a global setting may widen or contradict a
project's: a global rule, a global hook, a skill or agent of the same name, the default permission mode. The installer's own
code reads the harness's global configuration, never a module's; it prints names and paths and never values, and decides
nothing.
**Dependencies:** the owner's acceptance of a decision that narrows the rule in `repository-boundary.md` that the workbench
never reads a harness's global configuration (accepted on 2026-10-24: `installer-reads-global-settings-on-request`); `claude-harness`.
**Boundary:** one command, owner-run and terminal-only, read-only, for the Claude harness first. It may never be built: the
decision can be deferred until the cases the 2026-10-24 trial did not cover are run.
**Promotion trigger:** the decision accepted and the owner chooses to begin it.

### mempalace-scoping — Project scoping in the `mempalace` module

**Outcome:** the `mempalace` skill and policy block say that a result that comes from another project or wing is background
and not a fact about this project, say "the palace" where they now say "a memory" (an agent may still write the harness's
built-in memory where the owner allows it), and state which store answers first for a question both could answer.
**Dependencies:** `mempalace-module`.
**Boundary:** the skill, the policy block and their tests. It edits a shipped package, so its approval is released again by
the owner. A default wing per project is a larger change and is not part of this.
**Promotion trigger:** the owner chooses to begin it.

### checkpoint-levels-beyond-block — Levels other than `block` for the keys that offer only `block`

**Outcome:** the four keys that `command-permissions.md` lists as limited to `block` (`submit-remote-job`,
`push-shared-branch`, `fetch-remote-output` and `change-direction`), the two that offer `block` and `none` only
(`acknowledge-first-tier` and `acknowledge-second-tier`), and `accept-decision` and `wb release-approvals`, which offer `block`, `ask`
and `none` (since the plans `2026-10-29-accept-decision-at-ask` and `2026-10-30-release-approvals-at-ask`) and still lack `delegated`,
each offer the same levels as `approve-plan`:
`block`, `ask`, `delegated` and `none`, with the same meaning (the owner's direction, 2026-10-28). The accepted decision says
no key should be limited to `block`; this closes the gap that spec lists. Today `delegate` takes effect for `approve-plan`
only, so this widens it.
**Dependencies:** `checkpoint-settings-and-caps`, `push-checkpoint`, `remote-runner-module` and `delegated-approval` (all
complete). The decision `2026-10-28-every-key-offers-the-approve-plan-levels`, accepted by the owner on 2026-10-29, on what `ask`,
`delegated` and `none` mean for each key, in particular for the two agent checkpoints that no installer command runs and for what a
review may stand for at a push or a remote job.
**Boundary:** the command keys need their own preview digest before `ask` can work, and a delegated route for each; the
agent checkpoints (`fetch-remote-output`, `change-direction`), which no command runs, need the decision and a way to record the
level. `accept-decision` has its command and its `ask` level (`groundwork accept`); its `delegated` level waits on a decision about
what a delegated review's subject is for a decision. `wb release-approvals` has its preview digest and its `ask` level; where the verified level
cannot be read it reads the owner's own settings in the guarded store, and its `delegated` level waits on a decision about what a
delegated review would stand for when it makes the first-party packages trusted. It does not change who may approve a plan, the hard
stops, or the owner-run commands. It may be split into a plan per key.
**Promotion trigger:** the owner chooses to begin it, after accepting the decision.

### debug-artifacts — Retained diagnostics in `code-work`

**Outcome:** a project that installs `code-work` tells its agent where to keep a diagnostic worth retaining (a trace, a
log, a probe's output): `.workbench/local/debug/<YYYY-MM-DD>-<topic>/`, the untracked scratch place that
`repository-boundary.md` defines, with a local README stating the commit, the commands and tool versions, the purpose and
the conclusion. A durable finding is recorded in a tracked document, a decision or a test and cites no path into scratch.
Today no shipped module says any of this: the rule was in the owner's global configuration and in this repository's own
`AGENTS.md`, which no longer carries it, and the inventory row for it (IV3) says `keep global`. The owner's direction,
2026-10-29: follow `repository-boundary.md` and call the folder `debug`, not `.debug`.
**Dependencies:** `port-superpowers` (the `diagnose-failure` skill, complete).
**Boundary:** the `diagnose-failure` skill, its tests and the specs that describe it. The `code-work` policy block is at its
tested length and is not changed. It edits a shipped package, so its approval is released again by the owner. It does not
add a command, a module or a rule that a check enforces, and it does not change `repository-boundary.md`'s layout.
**Promotion trigger:** the owner chooses to begin it.

### floor-rules-after-reset — Floor rules for what the global reset removed

**Outcome:** the compiled hard-stop floor renders `ask` rules for four actions that the owner's former global `deny` list stopped
and the project did not: `rmdir`, `unlink` and `shred` under the stop for deleting files, and reads of `~/.config/gh/**` under the
stop for touching secrets. The owner's direction, 2026-10-29, after the global configuration was reset: an `ask` and not a `deny`,
because every floor stop is a stop for the owner and not a wall. `git merge` is left out: it fits none of the five stops, and a push
is already asked. Reads of the Codex login file are left out of the installer too, because the installer may not name a harness; the
`ask-codex` module declares that rule once a module can declare an `ask`.
**Dependencies:** none. The floor and its rendering are built (`trust-and-approval.md`, "Hard stops and the floor").
**Boundary:** the compiled rule list, its tests and one sentence of spec text. It adds no stop to the floor and changes no rule's
action. A clone receives the rules after the owner's re-render. Matching stays a best-effort match on command text.
**Promotion trigger:** the owner chooses to begin it.

### docs-cleanup-after-reset — Specs and roadmap that match what is built and what the global reset changed

**Outcome:** the specifications and this roadmap say what is true on 2026-10-29. Statements that call built work "not built",
"proposed" or "draft", statements that depend on the owner's former global configuration or on the old template, and passages
that contradict each other or the modules, are corrected or marked as history; and `terms.md` defines the words the other specs
use, including the owner, the approver and an owner-run command (which the owner may let an agent run, level by level). The
inventory of the global configuration is marked as the record of a state that the reset ended. This follows the audit of
2026-10-29 and the owner's six decisions in session.
**Dependencies:** none. The decisions it rests on are accepted (`2026-10-29-workbench-asks-for-remove-submit-and-fetch`,
`2026-10-29-accept-decision-offers-the-ask-level`, `2026-10-29-approvals-name-the-approver-by-git-identity`).
**Boundary:** documents under `docs/specs/` and this roadmap only. No package, no code, no seeded README text and no change to the
base. It leaves to later candidates: the citations of `AGENTS.md` sections that the base will restore, the rule for who accepts a
decision, the identity convention in the module READMEs, the `verilog` module description, and any spec status that only the
owner can set to `Current`. Accepted decisions are not edited.
**Promotion trigger:** the owner chooses to begin it.

### policy-and-module-asks — Restore the dropped policy, and let a module declare an ask

**Outcome:** the policy that the audit of 2026-10-29 found dropped is back where it belongs, and a module can declare the prompts it
needs. The base `AGENTS.md` gains what no module already says: no unrelated cleanup; deploying, using secrets and destructive cleanup
need the owner's approval; pull request descriptions describe the change only; prefer the project's documented commands; and a
`## Source of truth` section that the specs already cite. The groundwork policy block says that the level of `accept-decision`
governs whether an agent may accept a decision. A module may declare, restrictively, an `ask` for an argument of its own command and
an `ask` for a read under the home directory; `safe-git remove`, `remote-runner submit` and `fetch`, and the Codex login file read
use it, as `2026-10-29-workbench-asks-for-remove-submit-and-fetch` decides. The seeded plans README stops saying that nothing reads a
setting, the READMEs state the identity convention, and the `verilog` description stops saying its second skill is later.
**Dependencies:** none. The decisions are accepted; the floor rules and the approval identity are built.
**Boundary:** `base/`, this repository's own `AGENTS.md`, the module declaration schema and its rendering in `workbench/`, the
declarations and text of the `safe-git`, `remote-runner`, `ask-codex`, `groundwork`, `code-work` and `verilog` modules, and the specs
that describe them. It adds no level, no check and no `allow` rule, and does not build the `ask` level for `accept-decision`
(`checkpoint-levels-beyond-block`). Each package edit is released again by the owner.
**Promotion trigger:** the owner chooses to begin it.

### approval-identity — Approvals that name the approver by git identity

**Outcome:** every approval record the installer writes names the approver as `Name <email>` from the person's global git
configuration, records how it was authorized (`via`: terminal, ask, delegated or none), and no longer falls back to the word
`owner`, as `2026-10-29-approvals-name-the-approver-by-git-identity` decides. The record formats that hold the approver are
raised one version, and the commands and the specs show the approval as one sentence.
**Dependencies:** none. The decision is accepted and the approval records are built (`module-approvals`, plan approval records,
`delegated-approval`).
**Boundary:** `workbench/` and its tests, and the specs that describe the records and the word "approver". It does not decide who
may approve, add a setting for an identity, or change the shipped approvals. The convention in the decisions and plans READMEs is
module text and goes with the policy and module-asks work.
**Promotion trigger:** the owner chooses to begin it.

### global-config-migration — What remains of the owner's global Claude configuration

**Outcome:** what `~/.claude` carried for project work is supplied by installed modules, so a project gives a consistent
workbench experience whatever the owner's global settings are. This overtook the first plan, which was to remove global items one
at a time, each only after a test showed a project behaving the same without it. On 2026-10-29 the owner reset the user level to
the harness's defaults in one step and kept the former configuration as a backup, so the guarantee that no hard stop, deny rule
or approver is ever absent in between no longer applies to the removal; the floor carries it from here. What remains is: (1)
re-adopting from the backup, one item at a time and only on the owner's word, what the workbench does not supply; (2) the floor
test, a recorded run, repeated against the reset configuration, that a project's `deny` and `ask` rules, edit gate, owner-run
refusals and hard stops hold under the owner's own global settings (the trial of 2026-10-24, Claude Code 2.1.310, found a project
`deny` and `ask` holding against a global `allow` and `auto` mode, a global hook running beside the project's, a global skill
replaced by a project skill of the same name, and a project agent replacing a global one); and (3) archiving the two earlier
repositories, `claude_global_config` and `claude_project_template`, once nothing is still needed from them. The owner keeps their
own `allow` rules (the workbench never writes `allow`), machine-level settings such as authentication, model choice and remote
hosts, and anything wanted in a project that has no workbench. The earlier repositories are lessons learned; there is no mirror to
keep in step.
**Dependencies:** `checkpoint-settings-and-caps`, `increment-loop-and-review-skills`, `push-checkpoint`,
`compaction-guidance`, `remote-runner-module`, `review-engine`, `action-review-engine`, and `groundwork-module`; hooks
rendering for Claude (built by `checkpoint-settings-and-caps`); and the candidates from the inventory of the global
configuration that supply a global item: `architecture-decisions-merge`, `security-review-module`, `verilog-module` and
`cad-modules`.
**Boundary:** the first step is to finish the comparison that `docs/specs/global-config-inventory.md` begins, of the agents,
skills, hooks, `settings.json` and `CLAUDE.md` in the backup against the specs and modules, recording what was and was not inspected
and a disposition for every item (move, redesign, drop, or keep global); the backup holds credential-bearing material, so the record
names items by role and existence and never by value. Then the floor test above, then one item at a time from the backup, each
re-adopted only on the owner's word. The superpowers dependencies are items to settle: the three agents' `skills:` lists that name plugin skills, the
routing in the owner's `CLAUDE.md`, the session-start rule that tells an agent to look for a skill, and the gaps recorded
in `superpowers-ports.md` (parallel agents, writing skills, a fresh implementer per increment). It also settles the open
question whether the settings file's own path is denied for edits (`harness-modules.md`, "As built, and its limits"). It
does not move the owner's `allow` rules and does not change what the installer writes.
**Promotion trigger:** `checkpoint-settings-and-caps`, `increment-loop-and-review-skills`, `push-checkpoint`,
`compaction-guidance`, `remote-runner-module`, `review-engine` and `action-review-engine` complete, and the owner chooses
to begin re-adopting items from the backup. Each of those earlier plans lists the global items it replaces, so this
candidate starts from that list.

### self-hosting — Self-hosting

**Outcome:** a test records how this repository's seeded files relate to what the installer
would seed, and the old template is retired as a source. The document conventions were already
adopted by `adopt-conventions`, so this candidate is only that record and the retirement.
**Dependencies:** `ownership-and-upgrade`, `claude-harness`, `groundwork-module`,
`checkpoint-settings-and-caps`, `increment-loop-and-review-skills`, `push-checkpoint`, `compaction-guidance`, and the
candidates from the inventory of the global configuration that change a shipped module: `architecture-decisions-merge`,
`mempalace-scoping` and `security-review-module`.
**Boundary:** the recorded relation between hand-maintained files and generated output, and the
retirement of the old template as a source. The installer cannot be run on a directory with content, so installing it
here and approving this repository's own plans with `wb approve-plan` moved to `adopt-existing-repository`. The installer
does not rewrite its own repository in this candidate.
**Promotion trigger:** `checkpoint-settings-and-caps`, `increment-loop-and-review-skills`, `push-checkpoint` and
`compaction-guidance` complete.

### adopt-existing-repository — Install the workbench into a repository that has content

**Outcome:** this repository becomes an installed project, so its own edits are gated and its own plans are approved
with `wb approve-plan`.
**Dependencies:** `self-hosting`.
**Boundary:** a way to install into a repository that already has content, with its own spec change, decision record and
security review. It must not overwrite an existing file, and it must treat the files already there as the owner's. The
disposition of each `diverged` seeded file recorded by `self-hosting` is decided here.
**Promotion trigger:** `self-hosting` completes and the owner chooses to begin.

### remaining-modules-rename — Remaining modules and the rename pass

**Outcome:** the module list is renamed consistently across the specs, the packages and the roadmap. (`graphify` moved to
`graphify-module`; the formal-verification and Verilog simulation skills to `verilog-module`; the CAD modules to
`cad-modules`.)
**Dependencies:** `claude-harness`.
**Boundary:** renaming only. Each renamed module is checked against its specification. Nothing here is required by
`code-work`.
**Promotion trigger:** the owner chooses to begin the rename pass.

### compaction-support — Recovery after a compaction, and advice on when to compact

**Outcome:** after a compaction in Claude Code the agent starts again from the plan's state and not from the summary alone, and the
owner is told when a compaction would be cheap. A read-only command of the process module prints what must survive (the active plan's
path and increment, the approvals and checkpoints reached, the next action); a Claude hook that runs after a compaction hands that to
the agent; and a status-line advisor shows, when the context is large and a unit of work has just ended (an increment committed and
its result written, no review round or finding open, no failing check), the `/compact` line to use. Compacting stays the owner's act.
**Dependencies:** `compaction-guidance` and `claude-harness` complete. The facts about Claude Code's hooks and status line that the
design rests on (what a hook receives after a compaction, what the status line is given about the size of the context, whether it may
call the workbench) are checked against the current documentation and an installed version before the plan is written.
**Boundary:** the neutral state command in `code-work`; the Claude-specific hook and advisor, shipped as files under `harness/claude/`
of a module (in `code-work`, or in a small module that requires it, which the plan decides) and registered by the owner by hand, as the
shadow hook is; and the rule that says when a moment is good. What the hook hands the agent is read from the approval records and the
plan's header (paths, increment labels, statuses), never the text of a plan, which may have been written by someone else. Not part of
it: anything that triggers a compaction, a hook that blocks an automatic compaction (a later candidate, if measuring the size at which
compaction happens shows a need), a change to the thresholds of automatic compaction, a rendered "Compact Instructions" section,
installer rendering of a `SessionStart` or status-line entry, and opencode.
**Promotion trigger:** the owner chooses to begin and the documentation facts above are checked.

## Deferred

- A way of working for CAD and EDA (`cad-work`), until a project shows it is needed.
- Codex as a harness.
- Changing harness as an installer feature; the supported route is a new clone.
- Three-way merge on upgrade.
- Migration of projects made from the old template.
- A local pre-push git hook that runs the check.
- A wrapper that triggers compaction from outside a session.

## Related decisions

Decisions are listed, with their status, in `docs/decisions/`. This roadmap keeps no copy of that list.
