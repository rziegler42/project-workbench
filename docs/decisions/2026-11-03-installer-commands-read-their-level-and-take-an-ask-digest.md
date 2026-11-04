# The owner-run installer commands read their level by the route of their kind, and take an `ask` digest of a preview that leaves out what a run generates

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-03
Date: 2026-11-03

## Context

`ask` is a level at which the harness prompts the owner for the exact command, and the command then goes on only if it is given the
digest of a read-only preview as it is now. It works through two things: a rule rendered into the settings of the project the agent
works in, and the rendering record that proves the rule is the one the owner's table asked for
(`docs/specs/command-permissions.md`, "Rendering", "The preview and the digest (`ask`)"). Four keys offer it today: the plan approval,
the five owner-run arguments of the review engine, `accept-decision` and `wb release-approvals`.

The installer's own commands do not. `wb install`, `wb adopt`, `wb upgrade` and `wb add` offer `block` and `none`; `wb attach`,
`wb recover`, `wb approve`, `wb pin` and the acknowledge tiers do too, or `block` only. The owner's direction of 2026-11-02 is that no
command is limited to the terminal by design, and that each offers `ask` wherever an honest preview can be made. The plan is
`2026-11-02-permission-levels-for-every-command`, increment A. This record decides the questions that increments B and C build on; it
changes no code.

Three facts decide the design (read at commit `c1e82df`, on 2026-11-03):

1. **How the existing commands read a level.** `install`, `adopt`, `upgrade` and `add` have a terminal test. At a terminal they print
   the plan and its digest and read the first twelve characters typed. Without one, `levelrun.route` reads the key's level for the
   project that holds the working directory, and the command goes on only at a verified `none`; any other state, an unreadable level
   included, refuses with the terminal-only text and nothing is written. `wb attach` and `wb release-approvals` have no terminal test:
   a run at `block` goes on as it always did and the harness's `deny` is the barrier, so the verified reading can be defeated by
   making the rendering record disagree, and `release-approvals` therefore also reads the owner's own settings in the guarded store
   (`cli._owner_reading`), which no project file, harness file or working directory can change. That reading was added after the
   security review of the plan `2026-10-30-release-approvals-at-ask`, which found the digest check could otherwise be skipped.
2. **Which project the level is read for.** For `install` and `adopt` it is the project the agent works in, never the target, which is
   a new or adoptable directory. For `upgrade` and `add` it is the project acted on. For `attach` it is the project the agent works
   in, and the target is the project being rendered, which has no rendering record until `attach` writes it.
3. **The plan's digest cannot be the `ask` digest as it stands.** The plan that `install` and `adopt` build holds a seed that
   `manifest.new_seed()` draws at random on every run, and the time its pins record. `wb preview install` and the run build the plan
   in two processes, so their digests differ even when nothing else does. The terminal flow does not mind, because it builds the
   plan, prints it and compares within one process. An `ask` digest taken from one process and checked in another does mind.
   `upgrade` and `add` act on a project that already has a seed, and they draw the time per run as well; it reaches their digest
   only through the hash of a pins file that a run creates or changes, so their preview and run may already agree when no pin
   changes. Increment B tests each of the four commands and does not assume.

## Decision

**1. A command reads its level by the route of its kind.**

- *A command with a terminal test* (`install`, `adopt`, `upgrade`, `add`, and, in increment C, `recover`, `approve`, `pin` and the
  acknowledge tiers) reads the **verified level only**, as `levelrun.route` reads it. `ask` and `none` hold only while the rendering
  record, the local manifest and the harness files agree (the rule in "Rendering"). `levelrun.route` does not yet go on at a
  verified `ask`, because the kit's `may_run` is true without a terminal only at `none`; `may_run` and `wbkit.API` do not change,
  and increment B adds a reading beside `route`, as `levelrun.unattended` is beside `optional`, that returns the route at `ask` and
  `none`. In any other state the key reads `block` and the
  command refuses without a terminal, as it does at `none` today. No fallback to the owner's settings is added, because the refusal
  is the barrier and an attacker who makes the record disagree gains a refusal, not a bypass. A project that is not rendered reads
  `block` for `ask` exactly as it does for `none`: the owner runs the command at a terminal there.
- *A command with no terminal test* (`wb attach`, as `release-approvals` already does) reads the verified level and, when that is not
  `ask` or `none`, the owner's own setting in the guarded store: where it says `ask`, or the settings cannot be read, the digest is
  required and checked. `_owner_reading` takes the key as a parameter for this; it stays one function. Its reading of a risk
  profile (decision 10 of `2026-11-03-delegated-for-an-action-key-and-named-risk-profiles`) applies to every key it is asked about.

**2. The flow at `ask` is the one the other keys use.** The agent runs `wb preview <command> …`, shows the owner what it prints, then
runs the command with `--digest <32 lowercase hex>`; the harness prompts for that exact command and the owner confirms it. At a
terminal the command is unchanged and takes no digest (a `--digest` at a terminal is refused, as for `release-approvals`). At `none`
a digest is refused before the run, saying a digest needs the level `ask`, as `release-approvals` does (not as an unknown argument,
as `approve-plan` does); a run with nothing to change and a valid digest at `ask` says so and writes and logs nothing. At `ask` a run without a digest, with a malformed digest or with a stale one is refused
and nothing is written; the refusal names the preview. A digest given twice is refused. The attempt is written to the level log just
before the first write and the outcome after, with the level `ask`.

**3. The `ask` digest binds what is decided and leaves out what the run generates.** The preview prints the lines that the owner
approves: the project the level was read for, the target and its state, each action with its path, kind and content hash, each module
with its declaration and tree hashes and its approval, the harness and the permissions it would render, and a line that says what the
digest does not cover. Everything else the plan's own digest covers stays in: the target's identity (device and inode), so that a
directory swapped between preview and run is caught, the git initialisation, the exclude lines, the local manifest's hash, the
paths a block was not filled at (adopt) and the baselines. It leaves out the values the run draws for itself: the seed and the time of the pins, and anything derived
only from them (the project identifier, the hash of the manifest that holds them). The last line is `digest: <32 hex>` from the
kit's helper (`wbkit/digest.py`), computed over those lines. The run builds the plan again from the held target, as the terminal
flow's second build does (these commands have no lock), takes the digest of the same lines from that plan and compares. The plan's own 64-character digest stays in the printed plan and in the
terminal confirmation and the `none` log entry, which are unchanged. Increment B lists the excluded fields and guards the list by test: the test fails if a field outside the
list can change without changing the digest, or if a field inside the list changes it. A field that cannot be
classified stays in the digest; a command whose preview then differs from its run offers no `ask`, and its spec says why.

**4. Per command.**

| Command | `ask` | Route | Preview | Note |
|---|---|---|---|---|
| `wb install`, `wb adopt` | offered in B | verified only | `wb preview install`, `wb preview adopt` | level read for the working project, not the target; the target is in the digest |
| `wb upgrade`, `wb add` | offered in B | verified only | `wb preview upgrade`, `wb preview add` | the plan's project must be the one the level was read for, as at `none` |
| `wb attach` | offered in C, after a preview exists | verified, then the owner's setting | `wb preview attach`, built in C | renders into a target with no record; binds the files it would write, their hashes and the permissions it would render |
| `recover`, `approve`, `pin`, the acknowledge tiers | decided in C | verified only | built or named in C | an accepted record is needed for any that stays without `ask` |
| `wb rerender` | not here | | | increment D |

**5. What `ask` does not prove, stated as for the other keys.** The owner sees the command and a digest, not the plan. The agent shows
the preview in the conversation before it asks, and no code enforces that. An approved `install` writes whatever the previewed
modules hold at the previewed hashes: the digest binds hashes, not the packages' behavior, and the owner reads the change before
confirming. A fetch of a `--source` happens before the attempt is logged, as at `none`.

## Alternatives considered

- **Read the owner's settings as the fallback for every command.** Rejected for commands with a terminal test: it adds a second
  reading where the first already fails closed, and a setting that said `ask` while the record disagreed would let the command run
  without a terminal at a project whose harness no longer prompts. It is kept for `attach`, which has no terminal test.
- **Use the plan's full digest as the `ask` digest.** Rejected: it contains the per-run seed and time, so the preview and the run
  never agree, and every `ask` run would be refused. Fixing the seed and the time at preview and passing them to the run would
  need new flags and would let an agent choose the seed; excluding them from the digest needs neither.
- **Keep a 12-character digest, as the terminal flow types.** Rejected for the reason recorded for `approve-plan`: the plan is
  attacker-controlled and 48 bits can be ground; the owner never types the digest at `ask`.
- **Offer `ask` for `attach` without a preview, bound to its arguments alone.** Rejected: a digest that binds no content makes `ask`
  a rubber stamp (the plan's assumptions). `attach` waits for a preview in increment C.
- **A single new key for "installer commands".** Rejected: the registry has one key per action and the owner chooses per command
  (`2026-11-02-one-permission-registry-and-key-model`).
- **Do nothing; keep them `none` or `block`.** Rejected by the owner's direction of 2026-11-02, but it is what happens to any command
  whose preview cannot be made honest (decision 3).

## Consequences

- Good: the same flow for every digest-bound key; no new way to read a level; a defeated rendering record cannot turn a check off for
  the four commands that already refuse without a terminal.
- Good: `wb doctor` and `wb settings` need only the registry change to report the new offers.
- Once B makes the four keys offer `ask`, an owner on the `balanced` or `trusting` profile (decision 10 of the profiles record: a
  key of the class `project` takes `ask` when it offers it and is not already less strict) reads them at `ask` with no edit of the
  settings. `wb doctor` reports it as a profile-set level, and the rendered rules change at the next `wb rerender`, which the owner
  runs in a terminal; the plan's constraint on the settings version and the rendering record applies.
- Bad: the preview's digest and the plan's digest are two digests of one plan, and the printed plan shows both. The excluded fields
  are a list that must be kept right: a field wrongly excluded is a field the owner's confirmation does not bind. The test in
  decision 3 is the guard and the reviewer reads the list.
- Bad: a project that is not rendered cannot use `ask` for these commands, and an `ask` rule exists only in a rendered project; the
  owner who wants `ask` has rendered the project they work in.
- Bad: for `attach` the owner's setting is read from the guarded store, which an edit tool must not write and a shell write can; the
  limit is the one recorded for `release-approvals`.
- Changes to specs, made by increments B and C in the commit that changes the behavior and not before: `command-permissions.md` ("A
  level for every command", "Which levels a key offers"), `installer-interface.md`, `trust-and-approval.md` and each command's own
  spec. Increment D deals with `wb rerender` and `2026-10-27-rerender-is-terminal-only`, which this record does not touch.

## Evidence

Read, not run: `docs/specs/command-permissions.md` ("Shipped defaults", "The preview and the digest (`ask`)", "Rendering",
"A level for every command", "`wb release-approvals` at `ask`") at commit `c1e82df4d919`; `workbench/levelrun.py` (`route`,
`optional`, `unattended`); `workbench/cli.py` (`_owner_reading`, `_release`, `_levelled`, `_unattended_call`, `_preview`);
`workbench/install.py` (the confirmation at lines 241 to 262); `workbench/preview.py` (`seed or manifest.new_seed()`);
`workbench/installplan.py` (`Plan`, `build`, the `now` argument); `workbench/wbkit/digest.py`; `workbench/upgrade.py` (the
confirmation and the second build, lines 434 to 500) and `workbench/wbkit/levels.py` (`may_run`). `docs/specs/harness-refresh.md` was
searched for its statements on attach and rendering, not read in full, and the plan `2026-10-30-release-approvals-at-ask` was not read:
its built behavior is taken from the spec section that describes it. The finding that the preview and the
run differ by their seed and time is from reading `preview.run` and `install.run`; increment B proves it by a test before building
on it. No tool was run against a project, and nothing was changed except this record.
