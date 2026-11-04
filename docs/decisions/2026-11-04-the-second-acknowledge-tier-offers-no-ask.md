# The second acknowledge tier offers `block` and `none` and no `ask`, while no command carries it

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-04

## Context

The registry has two checkpoints for accepting changes someone else made: `acknowledge-first-tier` and `acknowledge-second-tier`
(`docs/specs/command-permissions.md`, "A level for every command"). The owner's table sets a level for each by name, and the policy
block of `AGENTS.md` describes what each stands for. `wb acknowledge` is carried by the first tier alone: every path it can list has
a baseline, and those paths are the manifest, files under `.workbench/`, `AGENTS.md` and seeded files, which are first-tier material.
The real direction documents (roadmaps, specs, plans, decisions) are not baselined, so no installer command lists a second-tier file.
The second tier is therefore a checkpoint that the agent follows as a rule; no command carries it (`workbench/levels.py`,
`INSTALLER_KEYS`: the key has no `word`, no `carried_by` and no preview), and it offers `block` and `none`.

The accepted decision
[2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest](2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest.md)
binds the level `ask` to the digest of a read-only preview of the command it governs, and says a key left without `ask` needs an
accepted record that names the reason. The plan `2026-11-03-levels-for-recover-pin-approve-attach` (increment C, criterion 3) asks for
the same of the second tier.

## Decision

`acknowledge-second-tier` offers `block` and `none` and does not offer `ask`, for as long as no installer command is governed by it.
Its default stays `block`.

The reason is specific: the level `ask` means "the command runs without a terminal only with the digest of its preview". There is
no command, hence no preview and no digest to bind. An `ask` offered for it would bind nothing, and a digest that binds nothing makes
`ask` a rubber stamp (the accepted decision, Alternatives). `none` stays, as the plan of 2026-10-27 listed it; it changes nothing the
installer does, and matters only to the agent's own checkpoint behaviour.

If a later command is governed by this checkpoint, that command's plan gives it a preview, and offers `ask` for the key in the same
change, with its own test and spec. That is a change in what the key offers, and it needs no new decision unless it departs from the
accepted record's rules.

## Alternatives considered

- **Offer `ask` with a preview invented for the purpose.** Rejected: there is nothing for it to show, because no command writes under
  this tier; a preview of nothing has a digest of nothing.
- **Remove the key.** Rejected: a process module declares the checkpoint, the policy block of `AGENTS.md` names it, and an owner's
  table that names it must keep reading as it does; removing it would turn an existing setting into an unknown key.
- **Make `wb acknowledge` governed by both tiers, with the stricter of the two.** Rejected here: the owner chose that the first tier
  stands for the command (`command-permissions.md`, "One way to run at `none`"), and a command that reaches more than one key takes
  the strictest level of them is a rule not built ("Not built"). It would be a separate decision.

## Consequences

- Good: the registry stays truthful: every key that offers `ask` has a preview and a digest, and the one that has no command offers
  none. The drift test and `wb settings` print it as it is.
- Good: no setting an owner writes for this key changes what any command does; `ask` for it is refused as not offered, like any level
  a key does not offer.
- Bad: an owner who wants the same stop-and-confirm for second-tier material has no `ask` to set; the checkpoint stays `block` or
  `none`, and the agent's own rule is what applies.
- Bad: the profiles `balanced` and `trusting` do not move this key (it offers no `ask`).

## Evidence

Read, not run: `workbench/levels.py` (`INSTALLER_KEYS`, the entry of `acknowledge-second-tier`) and `docs/specs/command-permissions.md`
("A level for every command", the paragraph on `acknowledge`) at commit `230fafa`; the accepted decision named above. The finding that
`wb acknowledge` lists no second-tier file is the spec's, and `workbench/acknowledge.py` examines every path that has a baseline. No
tool was run against a project, and nothing was changed except this record.
