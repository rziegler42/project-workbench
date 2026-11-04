# Review settings are owner profiles in the guarded store, chosen by a ladder for each kind of review, and a project tracks none

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-04
Date: 2026-11-04

## Context

Both engines that ask a model for a review read one project file, `.workbench/review.json`: strict JSON, `format` 1, a required
`bridge` and an optional `model` and `effort`, with no default bridge (`read_setting` in the review engine;
`docs/specs/review-engine.md`, "The project setting"). The accepted record `2026-10-26-action-review-reads-the-review-setting` made
the action-review engine read the same file, so that one place sets the three values, and it records the cost: the two engines cannot
use different bridges or models in one project.

Five facts bound the choice:

- **The file is a request and not a boundary.** Decision 5 of `2026-10-22-model-calls-go-through-vendor-bridges` says the setting is a
  default and a request, never an authorization; that the owner's personal setting is authoritative and may choose among the
  installed bridges; and that the personal setting is not built for either engine. The project file is the only setting there is, and
  it is a file the agent can write. In this clone it is untracked, hidden by a line the owner added to `.git/info/exclude`, so a
  fresh clone has no such protection.
- **One entry cannot express what a review needs.** To change the effort or the model the file is rewritten. A review has several kinds
  (plan, spec, roadmap and decision record, and the action-review engine beside them), a model's cost and strength differ, and the
  owner wants a different request for each round of one review.
- **Vendors change.** Models are renamed and retired and their cost moves. A setting that is edited for that must not make a project
  edit, and a project must not hold a model name that goes stale.
- **A bridge to a server needs more than a model and an effort.** The Ollama bridge takes `--server`, a model that is a configured key
  of the server's record (and may contain `/`), and either `--effort` or `--thinking`, never both
  (`2026-11-02-model-configurations-in-endpoint-records`, `2026-11-02-model-section-defaults-and-the-embedding-name`). Its window,
  output limit, temperature and keep-alive already live in the owner's `bridge-endpoints.json`, which is also the allow-list.
- **The store is the owner's.** `2026-10-20-fixed-store-location` fixes it at `~/.config/project-workbench/`. The harness denies the
  agent writes there and does not make it unreadable, and `2026-11-01-endpoint-records-in-the-store` put the owner's endpoint records
  in a file directly in the store root, which it inferred the store tolerates.

Measured evidence on cost and strength exists from before this project (Evidence, below). Its relevant result is that a higher effort of
the cheaper model found no more injected defects, so a ladder of efforts is a choice about cost, not about recall.

## Decision

1. **One owner file.** The account has one file, `review-profiles.json`, directly in the guarded store
   (`~/.config/project-workbench/review-profiles.json`). It is not per project. The owner writes it by hand, or `wb install` writes
   a default when it is absent (item 10). The harness denies the agent writes to the store. That is a guard against a mistaken or
   careless agent under the owner's account and not a boundary against a process that runs as the owner, as the review engine's
   specification says of its seal.
2. **Its format.** Strict JSON read as the endpoint file is read (no duplicate key, no `NaN`), one object, bounded in size, with exactly
   `format` (the integer 1), `profiles` and `ladders`. A field that is not listed, or a missing required one, is refused, and the
   refusal names the rule and never the value. An invalid file is refused as a whole, as the endpoint file is, so one bad profile stops
   every review until it is corrected. The exact bounds and the name rule go in the specification; a profile name follows the
   rule for the names of endpoint records.
3. **A profile** is a named record with a required `bridge`, an optional `model`, an optional `effort` (`low`, `medium` or `high`) and
   an optional `options` object. The `model` follows the rule of the bridge that is called (for a bridge to a server, the rule for the
   models of its endpoint records, which allows `/` and 128 characters; otherwise the contract's rule); the engine checks a generic
   bound and the bridge checks the rest. The keys of `options` are only options that the bridge's module declares for use by a review. The names `model`, `effort`,
   `timeout`, `schema`, `root` and `confine` belong to fixed fields or to the engine, and the module reader refuses a declaration
   that lists one of them as a review option, so a profile can never set the engine's time limit or its schema.
   Each value is a non-empty string of printable ASCII with no leading `-`, unless the module's declaration gives that option a grammar
   that allows one; the bridge's own grammar then checks the value. The engine passes `--model`, `--effort` and each declared option as
   `--<name> <value>`, beside its own `ask`, `--timeout` and `--schema`, and takes nothing else from a profile, so a profile can never
   carry a free-form argument. For the Ollama bridge the declared options are `server`, `thinking`, `context` and `max-output`; the last
   two are per-call overrides that the bridge already bounds by the model's section, so they can only lower the section's values. A
   pair of options that a bridge refuses together (`effort` and `thinking` for the Ollama bridge) is refused by the bridge, and a
   module's declaration may state the exclusion so that the reader refuses the profile earlier. A profile holds no window, output
   limit, temperature or keep-alive default of its own: that tuning stays in `bridge-endpoints.json`.
4. **A name is a label for a role.** Profiles are named for the role (`quick`, `standard`, `deep`, `local`), not for the model, so that a
   model change is one edit to the profile and everything that names it keeps working. Nothing in the file's meaning depends on the
   spelling of a name; what a profile requests is what it holds.
5. **A ladder** is an ordered list of 1 to 5 profile names, kept for each review kind in `ladders` under `plan`, `spec`, `roadmap`,
   `adr` and `action-review`, with an optional `default` ladder for a document kind (`plan`, `spec`, `roadmap` or `adr`) that has none. The `action-review` kind
   never uses `default` and needs a ladder of its own. The nth round of the review's current window
   uses rung n, and the last rung is used for every later round of the window; the `extend` of the review engine, up to its ceiling of
   5 rounds in a window, is covered by the ceiling of 5 rungs. A round is counted when it is spent: a bridge error spends no round, so a
   retry uses the same rung. After `reset` the window restarts, and the first round of the new window uses the first rung. The
   `action-review` ladder holds exactly one rung, because that engine makes one judgement per call and has no rounds; a longer one is
   refused. A kind with no ladder, and a document kind with no ladder and no `default`, is refused, naming the file. A ladder that names a profile the file does not hold, or
   a profile whose bridge is not installed, refuses the round naming the profile, and nothing else is tried in its place.
6. **Allowed is not authorized.** A profile names a bridge, and a bridge runs only when it is an installed, pinned module that provides
   `model-bridge` in this project, as decision 5 says. Installing the module is the owner's approval to send content to that vendor.
   The file lists what the owner permits; it grants nothing.
7. **A project tracks no review setting.** `.workbench/review.json` is retired: neither engine reads it, there is no fallback, and
   `wb doctor` reports a file at that path as unused. The owner of a clone makes the risk decision for their own account. For review
   settings, tracked project content may narrow what the owner's machine allows and may never widen it; no tracked review setting is
   defined here, and one would be defined by a later record, in a new format. A rule of that kind for every setting would be a record
   of its own.
8. **A missing or invalid file stops the review.** A review that cannot read the file is refused naming the file and how it is made.
   The engine never guesses a vendor.
9. **The record of a round.** Each round records the name of the profile and the request it resolved to (bridge, model, effort and
   options), beside the model the bridge reports having run. A round stored before this is built carries only the bridge, model and
   effort, and reads as having no options and no profile. `status` keeps its `request` values (`none`, `same`, `changed`,
   `unreadable`) and gives them this meaning: `same` when the request of the last round equals the current definition of the profile
   that its rung names, `changed` when it does not. It also prints, for the next round, the profile and the location class of its
   server. The request of a round already run is never rewritten by an edit to the file.
10. **`wb install` writes a default when the file is absent.** The write is part of the command's preview, the digest at `ask` binds
    the bytes that will be written, and an existing file is never overwritten or changed. `wb install` is the owner's command at the
    level the owner set, and the agent runs it only as that level allows. The default is built only from what is installed and pinned
    and from the owner's endpoint file. For `ask-codex`: the profiles `quick`, `standard` and `deep` at `low`, `medium` and `high` with
    no model named, so the bridge's own default stands. For `ask-ollama`: one profile for the `default_model` of each record of a valid
    `bridge-endpoints.json`, named `local` when there is one record and `local-<record name>` when there are several, with
    `options.server` set to the record's name; a record with no `default_model` gets none. Ladders are written only when exactly one
    bridge family is installed: for `ask-codex` following the shape the owner measured (the cheap profile for the early rounds and
    `deep` from round 3, that is `quick`, `quick`, `deep`), in `default`, and for `ask-ollama` a `default` ladder of the single `local` profile, since it has no cheap or strong one, and only
    when that profile was created: a record with no `default_model` creates no profile and no ladder, and the install says that the
    owner must configure a chat model. The `action-review` ladder is written beside `default` and holds one rung, `quick` for
    `ask-codex`, so that a judgement fits the engine's time budget, and `local` for `ask-ollama`. With several families, or several local profiles, the profiles are written, the ladders are not, and the
    install says that a review is refused until the owner chooses. With no bridge installed no file is written. The default is never
    seeded from the project's old `review.json`, which an agent can write; a clone that has one is moved by a one-time owner step whose
    preview shows what the old file said.
11. **Both engines read the file.** The action-review engine reads the `action-review` ladder, so the engines may now use different
    bridges or models. That engine keeps a time budget of 25 seconds for one judgement and gives the bridge a `--timeout` of 20 seconds,
    and a profile cannot change either, so a profile too slow for the budget fails as a timeout and the judgement yields no verdict. Its
    helper has a reader of the setting of its own, and the build changes both readers. Its record
    `2026-10-26-action-review-reads-the-review-setting` is superseded by this one, including the exception it made, in its item 3, to the
    rule that an engine names a file of its own.
12. **What this does not decide.** A per-project choice of ladders, kept untracked in the store under the project's entry, is left to a
    later record. A check of the profiles against a vendor's own model list is left to the bridge that can declare the read. How a
    delegated approval treats the request of the last round is `2026-11-04-delegated-approval-checks-the-profile-of-the-last-round`.

This supersedes decision 5 of `2026-10-22-model-calls-go-through-vendor-bridges` in part, and in no other part. In its item 5 it
replaces: the rule that an engine reads a project file `.workbench/<engine module>.json`; the project setting as the source of the
bridge, model and effort; the sentences that where a personal and a project setting disagree the personal one is used and that a
teammate with no personal setting gets the project's bridge (a missing owner file now refuses, item 8); the rule that a pulled change to
the project setting is a difference to acknowledge (there is no project setting); and the owner's personal setting being only a choice
among bridges and a lowering of the effort (the owner's file now chooses all three). It leaves standing that a setting is a request and
never an authorization, that a bridge runs only when it is an installed, pinned module that provides `model-bridge`, and that a refused
bridge is not replaced by another. Decision 5 is not edited; if this record is accepted, the status line of the record that holds
decision 5 names this record, as the status line of `2026-10-23-delegated-plan-approval` names the record that superseded its decision 6.

## Alternatives considered

- **Keep `.workbench/review.json`, with a list of entries.** It keeps one place in the project, but an agent can edit it to choose any
  installed bridge, and a vendor change becomes a project edit and a difference to acknowledge. Rejected.
- **Move the file to `.workbench/local/`.** It is ignored by git without a hand-made exclude line and is per clone, but it is still a file
  the agent can write, so it is a convenience and not a boundary. Rejected.
- **Let a tracked file choose among the owner's profiles.** The list could hold a cloud profile and a local one, so a cloned repository
  could steer content to the cloud. A flag on each profile that marks it selectable by a project would keep that safe; it was set aside
  because the owner prefers that a clone's owner makes the choice. It stays possible by a later record.
- **A call-time `--profile`.** It would let the agent break the ladder. Set aside; the ladder chooses.
- **Fall back to the project file when the owner's file is missing.** It keeps the agent-writable path alive and makes the new file a
  boundary only once it exists. Rejected: the owner is the only known user, and one migration step is cheaper than the fallback.
- **Profiles named for models.** A model change would then change the name and everything that names it. Rejected for role names.
- **A model named in the generated defaults.** It would go stale with the vendor. Not done; the bridge's own default stands, and
  `2026-11-04-delegated-approval-checks-the-profile-of-the-last-round` says what a gate needs instead.
- **A ladder of efforts only.** The measurement below found no gain in recall from a higher effort of the cheaper model, so the ladder
  is a cost tool and may name any profile.

## Consequences

- No project edit follows a change of vendor, model or cost: the file is the owner's and a project holds nothing to update. A removed or
  renamed profile refuses the round that needs it, with its name, and `wb doctor` reports a name that dangles.
- The agent can no longer redirect a review by editing a file in the project, and a change of the vendor is no longer a project
  difference to acknowledge, because it is not in the project.
- The two engines may use different bridges, models and efforts, and a review may use a cheap early round and a stronger later one.
- Cost: every account makes the file once. A new machine, and a teammate, needs its own file, and until it exists a review is refused.
  The owner of this clone has a one-time migration. A project can no longer say in a file which review it expects; it can say so in its
  documents.
- Cost: `wb install` widens what it writes in the store, which is a change to its preview and its digest, and that widening rests on the
  inference that the store tolerates a further file in its root. A test must confirm it before it is relied on.
- Cost: a bridge's module declaration gains a list of options a review may pass, which changes `module-contract.md` and the module
  reader. A profile whose option a bridge no longer declares is refused, and an upgrade of the bridge can cause that.
- The changes to specifications are `review-engine.md`, `action-review.md`, `model-bridge.md`, `module-contract.md`,
  `trust-and-approval.md` and the installer documents, and the engines (both readers of the setting), the installer and `wb doctor`
  change with them.
- `action-review.md` says that no helper can read the guarded store. The review engine already reads its seal key there and the Ollama
  bridge its endpoint file, so that sentence is corrected.
- The state that records each round's request is kept in the project and sealed with a key that the agent can read
  (`review-engine.md`, "The seal"). A forged state could claim a request. That is the trust level that `converged` already has, and
  the seal guards a mistaken or careless agent and not a deliberate one.
- The plan for a later step must keep the engines' behaviour with no `review.json` in step with this record; until it is accepted and
  built, the engines read the project file as they do now.

## Evidence

Read on 2026-11-04 at commit `1fff565` (working tree, nothing run): the reader `read_setting` and the setting passed to a bridge in
`packages/workbench/review-engine/helper/review-engine`; `docs/specs/review-engine.md` ("The project setting", the round and bound
rules, `status`); `docs/specs/action-review.md` ("Settings and the bridge"); decision 5 of
`2026-10-22-model-calls-go-through-vendor-bridges`; `2026-10-26-action-review-reads-the-review-setting`;
`2026-11-01-endpoint-records-in-the-store`; `2026-11-02-model-configurations-in-endpoint-records`;
`2026-11-02-model-section-defaults-and-the-embedding-name`; `2026-11-02-temperature-and-keep-alive-in-model-sections`; and the
`ask-codex` module declaration, which declares one read, `~/.codex/auth.json`. The conclusion is that the project file is the only
setting, that it is agent-writable, and that the owner's personal setting that decision 5 calls for is not built.

Reference, a measurement made before this project and not repeated: the specification `second-opinion-plan-review.md` of the owner's
repository at `git@github.com:rziegler42/claude_global_config.git`, at commit `6ae05669fb1c39c1a1f9303cbca7633970ffd79d`, retrieved
2026-11-04, sha256 `151ba86b245b46a3de6c4768a5806d5156749a9388c56a10b823f59ec16c4de6` (the committed bytes; the working copy equals
them). Its section "Model choice (2026-10-16)" reports a benchmark of four small repositories with six injected defects each (24 in
all), scored on blocker and major findings: the cheaper model found 23, 23 and 23 of 24 at low, medium and high effort, for 0.53, 0.53
and 0.77 credits, and the stronger tier found 23 of 24 at low for 4.62 credits. Its section "Escalating effort" records the policy it
adopted, low effort rising to high for later rounds, and its "Calibration result" records one plan reviewed once by two models. The
limits are the ones that section states: toy repositories, one run per configuration, recall only, a false-alarm gate not completed,
some configurations not run, and prices as of that date. The models measured are not the model this clone is configured for. The
conclusion used here is only that a higher effort of the cheaper model did not raise recall in that sample.

## Note, 2026-11-04

A clarification made at the owner's request; the decision above is unchanged.

Item 3 says the keys of a profile's `options` are only options that the bridge's module declares for use by a review, and that the
engine passes nothing else from a profile. The review engine does not read a declaration at run time. Only the installer can read a
declaration from a source an agent cannot write, and a launcher check on every call was set aside as larger than the gap it closes,
because the option names come from the owner's file, which an agent cannot write. The engine passes a profile's options after the
kit's checks of their form. The bridge refuses an option it does not accept. `wb doctor` and the delegated-approval check read the
pinned declaration and report an undeclared option, a value that does not fit its grammar, and a broken exclusion
(`docs/specs/review-profiles.md`, "Where each check runs").
