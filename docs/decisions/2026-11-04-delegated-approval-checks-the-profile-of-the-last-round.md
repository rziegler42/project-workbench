# A delegated plan approval checks the request of the last round against an owner setting

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-04
Date: 2026-11-04

## Context

`2026-10-23-delegated-plan-approval` lets the installer record a plan approval for the agent when the owner's `approve-plan` is
`delegate` and a review of the exact bytes converged. The review engine says whether it converged through its `convergence` argument.
Convergence is strict: the last round has no `blocker` or `major` finding, no meaningful finding of the window is pending, the state is
sealed and not rolled back, and the rounds used do not exceed the bound. The approval record names its delegate: the provider module
with its declaration and helper hashes, the bridge, the model (null when unknown), the rounds used and the bound, the review key and the
file hash; the record is at format 3, which adds `via` and `approver`.

What the engine keeps of a round today is the bridge, the request as `requested` (a model and an effort) and the model the bridge
reported. It keeps no options and no profile name; those exist only once `2026-11-04-review-profiles-in-the-guarded-store` is built.
The `convergence` object's existing `model` is the model the bridge reported, and the existing `status` field `request` (`none`, `same`,
`changed`, `unreadable`) is a different thing again.

That proposed record gives a review a ladder of profiles, so a first round may run on a cheap profile. A cheap round that comes back
clean would make `converged` true, and a delegated approval could then rest on the weakest reviewer the owner has allowed. The owner
wants the ladder to be a cost tool only, with no round forced to the strongest profile, and wants to decide, per account, what a
delegated approval will accept. Only delegated plan approval reads `convergence`, and it resolves the document as a plan, so no other
review kind is affected. The owner expects to use delegated approval, and another developer may.

## Decision

1. **`converged` keeps its meaning.** The engine's definition is unchanged. The ladder does not make a round stronger or weaker for
   the purpose of convergence.
2. **The `convergence` object reports what was asked.** It gains one field, `last_requested`: the request of the last stored round, as
   the bridge, the model asked for, the effort, the options (a map of strings) and the name of the profile. A value that the round
   did not record, and every value of a round stored before the profiles are built, is `null`. The object's `format` becomes 2. The
   installer reads 1 and 2, and an object of format 1 reads as a request that is unknown. The specification restates the cap on the size
   of the report, which options enlarge.
3. **A new owner setting, `delegate-profiles`.** It sits in the owner's settings file beside `approve-plan`, and `wb settings` prints it.
   That file is strict and versioned and refuses a key it does not know, so the key needs a new version of the file, which the
   specification names. Its value is `any`, the default, or a list of 1 to 8 distinct profile names of `review-profiles.json`, each a
   string. Every other value, which is an empty list, a list that holds `any`, a duplicate, a name that is not a string, a longer
   list, or a damaged entry, is invalid and refuses a delegated approval; it is never read as `any`, as the existing reader sends a
   damaged setting to the safe side. The setting takes effect only while `approve-plan` reads `delegated` (a checkpoint `delegate` reads
   as `delegated`, and a table entry wins when both exist). A project, a plan or a review cannot supply it: delegation is never project
   policy (`2026-10-19-mandatory-review-personal-delegation`). Each account sets its own, and a project cannot impose one.
4. **The check, for a list.** The installer, in the place where it already checks that the review converged, compares `last_requested`
   with the current definition of each listed profile. The comparison has one form: an absent or `null` model or effort is the same
   as another absent or `null` one; an absent `options` is the empty map; the options compare as unordered maps of exact strings, and
   the whole map must be equal, so an option that one side has and the other lacks is a difference. The name of the profile is not
   compared, and what is compared is the request that the round recorded and never the rung that the ladder names today. The
   approval proceeds only if one listed profile matches. For `any` there is no check, and an unknown request never fails it.
5. **It fails closed.** For a list, the delegated approval is refused, with the reason, and the owner approves the plan themselves,
   when: a listed name is not in the file; the file cannot be read or is invalid (the installer reads it with the same strict rules as
   the engine, so a duplicate key or an oversize file refuses); a listed profile is invalid (for example one that holds both `effort`
   and `thinking`); the request is unknown, which includes an engine that cannot report it, an object of format 1, a round stored
   before the profiles were built and any other provider of `peer-review`; or no listed profile matches, a profile that was edited
   after the round included. An edit to a profile is therefore a reason to ask for one more round before a delegated approval, and
   never a reason to approve on the old round.
6. **The profile check is made once, when the approval is asked for.** `delegate-profiles` and the profile match are not read again
   when an approval is read, and the record stays as it was written. Tightening the setting later does not withdraw an approval that
   was given earlier. Item 9 of `2026-10-23-delegated-plan-approval` is not changed: `wb plan-status` and the edit gate still count a
   delegated entry only while the owner's setting for `approve-plan` reads `delegate` at that moment. This record does not extend the
   delegate object of the approval record; whether it should record the profile and the request is for the specification and needs a
   new format of that record.
7. **A model for a profile that gates.** A profile listed in `delegate-profiles` that names no model follows the vendor's own default,
   which can change under the gate. `wb doctor` warns about such a profile. Refusing it is left to a later record if the warning is not enough.
8. **The owner's own approval is unchanged.** `wb approve-plan` never reads this setting.

This refines `2026-10-23-delegated-plan-approval` in items 2 and 4 (what the engine reports and what the installer requires) and
leaves every other item standing, item 9 included. Its item 6 is already superseded by `2026-10-26-per-command-permission-levels`, so
this record does not rest on it. That record is not edited.

## Alternatives considered

- **The last round must run at the ladder's last rung.** It is simple, but it forces a strong, costly round at the end of every review
  and puts the policy in the engine and the ladder. Rejected by the owner.
- **A floor in the ladder.** A ladder would name the profile a clean round needs. It keeps the policy in a file that describes cost,
  and the owner would set it by kind. Not chosen; the setting is the owner's account policy and belongs with `approve-plan`.
- **Two clean rounds from different profiles.** It buys diversity and not strength, costs a second round, and needs two profiles.
  Kept as a later addition that combines with this record.
- **A strong round anywhere in the review.** The strong round would have read earlier bytes, so a later edit can pass unseen. Rejected
  for approval.
- **No rule.** The ladder would cost less and a delegated approval could rest on the weakest profile. Acceptable for an owner who
  never delegates, and the default value `any` gives the same behaviour. Rejected as the only choice because the owner expects to delegate.
- **Compare names.** A rename or an edit would pass or fail by accident. Rejected for comparing what was requested.

## Consequences

- No review is forced to a strong round. An owner who sets nothing sees today's behaviour. An owner or a developer who delegates can
  require a strong profile for the approving round, and can change that without editing the engine.
- The decision touches the engine's `convergence` output, the installer's delegation check, the settings file and its reader (a
  setting that holds a list of names, beside the `caps`, `checkpoints`, `floor`, `levels` and `profile` entries, in a new version of
  the file), `wb settings` and `wb doctor`, and the specifications that describe them.
- The match is strict. A model bump that edits a profile in the list invalidates a review that is waiting for approval and needs one
  more round, and that cost falls only on a review in progress.
- The setting names profiles of another file, so a name can dangle. The check refuses and `wb doctor` reports it.
- **What the check proves, and what it does not.** It compares what was requested and not what ran. A profile with no model follows
  the vendor's default (item 7). For the Ollama bridge the model is a key of a record in `bridge-endpoints.json` and `server` names a
  record, so an edit to the endpoint file can change what runs while the profile's strings still match: the guarantee that an edit
  invalidates a round holds for edits to `review-profiles.json` only. Comparing the model the bridge reported with a model the profile
  names is a possible later addition.
- **Its trust level.** The state that holds the last round is kept in the project and sealed with a key that the agent can read
  (`review-engine.md`, "The seal"), and the seal guards a mistaken or careless agent. A forged state could claim a strong request. That is
  the trust level `converged` already has, so this check adds no weaker link, and it is no stronger than that seal. The same holds for
  the setting and the profile file in the store, whose guard is the harness's denial of agent writes.
- Until the profile file is built, the setting has nothing to name and its only value is `any`.

## Evidence

Read on 2026-11-04 at commit `1fff565` (working tree, nothing run): `2026-10-23-delegated-plan-approval` (items 1 to 9 and its status
line), `2026-10-19-mandatory-review-personal-delegation`, the "Convergence" section of `docs/specs/review-engine.md` and "The seal", the
round fields of the review engine's helper (`ROUND_FIELDS`, `requested`, and the request compared in the convergence code), the settings
reader `workbench/settings.py` (a strict file at versions 1 to 3 with `caps`, `checkpoints`, `floor`, `levels` and `profile`), and the
output of `wb settings`, which prints `checkpoint`, `cap` and `level` lines and no list-valued line (the code also prints a `profile`
and a `translated` line). The conclusion is that the engine already records the bridge and the model and effort asked for in every
round, that it records no options and no profile name, that the installer checks convergence in one place, and that the one new fact
the installer lacks is the request of the last round with its options and profile. The code of `delegation.py` was not read; the place
of the check is the intended one, to be confirmed by the plan that builds it.

An independent read-only review of this record by a reviewer agent on 2026-11-04 found the gaps that items 2 to 6 and the
consequences above now close: a damaged setting, the comparison form, the unknown request, the setting file's version, and the limits
of what the check proves. One round of the review engine on this record found one conflict with item 9 of the 2026-10-23 record,
which item 6 now resolves.

## Note, 2026-11-05

A clarification made at the owner's request; the decision above is unchanged.

Item 5 says the installer reads the profile file "with the same strict rules as the engine, so a duplicate key or an oversize file refuses". That holds for the file, its bounds and its profiles: the installer reads it with the kit's reader, so a duplicate key, an oversize file, a damaged profile and a ladder that names a profile the file lacks still refuse. It differs in one place. The installer may not name a module or a kind of review (`docs/specs/module-boundary.md`), so it cannot list the ladder keys an engine accepts or know that the ladder of one key holds a single rung. It takes the ladder keys from the file itself. It therefore accepts a file with a ladder key that an engine would refuse, or with an `action-review` ladder of more than one rung, which each engine still refuses on its own reading. The installer's check uses only the profiles, so this changes no outcome of the comparison (`docs/specs/review-profiles.md`, "The `convergence` report and `delegate-profiles`").
