# Review profiles

Status: Draft

This spec describes behaviour that two accepted decisions require and that is **not built yet**. Today both engines that ask a model for
a review read the project file `.workbench/review.json` (`review-engine.md`, "The project setting"; `action-review.md`, "Settings and
the bridge"). Each section below says what is decided and which increment of the plan `2026-11-04-review-profiles` builds it. When an
increment is built, its section is edited to say what is true, and this spec becomes `Current` when the plan is done.

## Scope

- The owner's file `review-profiles.json` in the guarded store: its place, format, bounds and refusals.
- A profile (bridge, model, effort, options), a ladder for each kind of review, and the rule that picks the profile of a round.
- The options a module declares for use by a review, and what the engine may pass.
- What a round records, what `review-engine status` prints, and how the action-review engine uses its ladder.
- The default file `wb install` writes, and the checks of `wb doctor`.
- The new field of the `convergence` report and the owner setting `delegate-profiles`.
- The retirement of `.workbench/review.json`.

## Non-goals

- A per-project choice of ladders, a tracked review setting of any kind, and a call-time `--profile`.
- A check of a profile against a vendor's own list of models.
- The tuning of a model on a server (window, output limit, temperature, keep-alive), which stays in `bridge-endpoints.json`
  (`ask-ollama.md`).
- A change to a bridge's contract (`model-bridge.md`) or to `ask-codex`.
- Putting the profile or the request in the approval record.

## Assumptions and constraints

- The guarded store is at `~/.config/project-workbench/` and nothing moves it (`2026-10-20-fixed-store-location`). The harness denies
  the agent writes there and does not make it unreadable; that is a guard against a mistaken or careless agent and not a boundary
  against a process that runs as the owner (`review-engine.md`, "The seal").
- Only the last part of the store path is refused when it is a link; a symlinked `~/.config` is followed, as is any link above the
  store root. `HOME` moves the whole store, so a process that sets it reads another file: the guard is against a mistaken agent and
  not against a process that runs as the owner.
- A helper reaches the store by a fixed path under the home directory through the kit's no-follow layer; the kit has no store accessor
  (`review-engine.md`, "The seal"). The reader is a new module of the kit, `wbkit/profiles.py` *(built by increment B)*. The kit's rules
  allow it: two helpers and the installer need it, and a module added to the kit that changes none a helper imports needs no new
  API number (`module-boundary.md`, "The kit"; `wbkit/identity.py` and `wbkit/digest.py` were added the same way). The kit knows no
  document kind and no module, so the caller names the ladder keys it accepts and the keys whose ladder holds one rung, and the
  review engine, the action-review engine and `wb doctor` each pass theirs; a drift test compares the sets.
- A further file directly in the store root is tolerated. That was an inference from `workbench/store.py` (`2026-11-01-endpoint-records-
  in-the-store`); increment B tests it (`tests/test_kit_profiles.py`, "TheStoreRoot"): a store made by `Store.ensure` takes the file, keeps
  it through a second `ensure` and refuses nothing.
- A bridge runs only when it is an installed, pinned module that provides `model-bridge` in the project (decision 5 of
  `2026-10-22-model-calls-go-through-vendor-bridges`). The file lists what the owner permits and grants nothing.

## Behavior

Where the two accepted records leave a number to this spec, the choice and its reason are given. Every such number is a proposal for
the owner's approval of this spec and is refined by the increment that builds it.

### The file

- **Place.** `~/.config/project-workbench/review-profiles.json`, one file for the account (`2026-11-04-review-profiles-in-the-guarded-
  store`, item 1). The owner writes it by hand, or `wb install` writes the default when it is absent. No other command writes it.
- **Reading.** Strict JSON as the endpoint file is read: one object, no duplicate key, no `NaN`, at most **32,768 bytes** (a profile is
  about 200 bytes and 32 of them with six ladders are under 10 KB; the bound is an eighth of the endpoint file's 262,144 bytes, which holds up to 64
  records with up to 64 model sections each). Exactly the fields `format`, `profiles` and `ladders` are allowed. A field not listed, a
  missing one, an oversize file, a link or a file that is not regular is refused. An invalid file is refused whole, so one bad profile
  stops every review until it is corrected. A refusal names the rule and never the value.
- **`format`** is the integer 1.
- **`profiles`** is an object of 1 to **32** named records. A name is 1 to 32 characters of `a-z0-9_-` that start with a letter or a digit
  (the rule for the names of endpoint records). Names are labels for a role (`quick`, `standard`, `deep`, `local`) and the file's
  meaning depends on none of them.
- **`ladders`** is an object whose keys are among `plan`, `spec`, `roadmap`, `adr`, `action-review` and `default`; each value is a list of
  1 to 5 names of `profiles` (repeats are allowed: `quick, quick, deep` is a ladder). A key outside the six is refused. The `action-review`
  list holds exactly one name. `default` serves the four document kinds only and never `action-review`.

### A profile

- `bridge` (required): one command name, as the kit's `call.NAME` reads it.
- `model` (optional): follows the rule of the bridge that is called. For a bridge to a server it is a key of the record's `models`
  (letters, digits and `._:-`, `/` between segments, at most 128 characters; `ask-ollama.md`); otherwise the contract's rule (at most 64
  characters of `A-Za-z0-9._:-`). The engine checks a generic bound of 128 characters, printable ASCII with no space and no leading `-`, so that it never builds
  `--model <value>` from text that could read as an option, and the bridge checks the rest.
- `effort` (optional): `low`, `medium` or `high`.
- `options` (optional): an object of at most **8** entries from a name to a value. A name is one the bridge's module declares for use by
  a review (below), and never `model`, `effort`, `timeout`, `schema`, `root` or `confine`. A value is a non-empty string of 1 to 128
  printable ASCII characters with no space and no leading `-`; the declared grammar of the option then checks it.
- A profile whose options hold a name that the module declares as excluded by another field it also holds (for the Ollama bridge,
  `thinking` with `effort`) is invalid.
- **Where each check runs.** The reader of the file checks the file's own rules and nothing that needs a module: the bounds, the
  names, the reserved option names, the value rule above, and that a ladder names profiles that exist. It does not read a module's
    declaration, so one bridge that is not installed never invalidates the file. The checks that need the declaration (that an option
  is declared, its grammar and its exclusions) run in `wb doctor` and in the installer's check of a delegated approval, which read
  the pinned declaration. The engine runs none of them (see the open point under "The options a module declares for a review").
  For the installer's check, a listed profile is invalid if it fails either set.
- A profile holds no window, output limit, temperature or keep-alive default of its own.

### The options a module declares for a review

*(Built by increment C: the declaration reader, `wb verify` and the Ollama module's declaration. The engine's use of it is
increment D.)* A module's command declaration may carry `review_options`, an object from an option name to
`{"grammar": <name>, "excludes": [<name>, ...]}`.

- A name is `^[a-z][a-z0-9-]*$`, at most 32 characters. The reserved names above, and every non-empty prefix of one, are refused by the reader of the declaration, and `wb verify` refuses the declaration
  because it reads declarations through that same reader.
- `grammar` is one word of a **closed list**, so a module cannot supply an expression of its own: `word` (1 to 64 characters of
  `A-Za-z0-9._:-`, starting with a letter or digit), `name` (1 to 32 characters of `a-z0-9_-`, starting with a letter or digit), `count`
  (1 to 8 ASCII digits, no leading zero, no sign) and `onoff` (`on` or `off`). None of them allows a leading `-`.
- `excludes` lists options, or `effort`, that may not appear in one profile with this option. Each name is `effort` or another option
  of the same command, never the option itself, and the names are different from each other.
- The Ollama bridge declares `server` (`name`), `thinking` (`onoff`, excludes `effort`), `context` (`count`) and `max-output` (`count`).
  `context` and `max-output` are per-call overrides that the bridge already bounds by the model's section, so they can only lower the
  section's values. `ask-codex` declares none.
- The engine passes `--model`, `--effort` and each option of the profile as `--<name> <value>`, beside its own `ask`, `--timeout` and
  `--schema`, and nothing else from a profile.
- The grammars are defined once, in the kit (`wbkit/profiles.py`, `GRAMMARS` and `fits`), and the declaration reader takes its closed
  list from there. The Ollama helper's own patterns for `--server`, `--context` and `--max-output` are the same text, which its
  module test compares.
- **Where the declaration is checked (the owner's choice of 2026-11-04).** The engine does not read a declaration: it passes the
  options of the owner's profile and the bridge refuses one it does not accept, reported with the profile's name. Only the
  installer can read a declaration from a source an agent cannot write, so the checks that need it run in `wb doctor` and in the
  delegated-approval check (increments I and J). The alternative, a launcher check on every review call, was set aside as a larger
  change than the gap it closes: the option names come from the owner's file, which an agent cannot write, so only the owner's own
  mistake or a bridge the owner installed on purpose can put an undeclared option there.

### The ladder

*(Built by increment D for the review engine; increment F builds it for the action-review engine.)*

- The nth round of the review's current window uses rung n. The last rung is used for every later round of the window. `extend` raises
  the bound by 1 to 5 up to the ceiling of 5 rounds in a window (`review-engine.md`), which the ceiling of 5 rungs covers.
- A round is counted when it is spent. A bridge error, a refusal and a failure that spends no round leave the count where it was, so a
  retry uses the same rung.
- After `reset` the window restarts and the first round of the new window uses the first rung.
- The kind of a review picks the ladder: `plan`, `spec`, `roadmap` or `adr`, else `default`. The action-review engine uses `action-review`
  and never `default`. A missing ladder, or a document kind with neither its own ladder nor `default`, is refused naming the file.
- A ladder that names a profile the file lacks, or a profile whose bridge is not an installed, pinned `model-bridge` provider in the
  project, refuses the round naming the profile. Nothing is skipped and no other bridge is tried.
- A missing or invalid file is refused naming the file and how it is made. No default bridge exists and the engine never guesses a
  vendor to send content to.
- `.workbench/review.json` is read by neither engine from the increment that builds each. There is no fallback. `wb doctor` reports a
  file at that path as unused.

### What a round records and what `status` prints

*(Built by increment D: the record and `request`; increment E builds `next`.)*

- Each round records the name of the profile and the request it resolved to (bridge, model, effort and options), beside the model the
  bridge reported. A round stored before this is built carries only the bridge, the model and the effort asked for, and reads as having
  no options and no profile. The round entry gains the field `profile` (the name) and its `requested` gains `options` (an object of strings); both shapes are
  read (`review-engine.md`, "State").
- `status` keeps the `request` values `none`, `same`, `changed` and `unreadable`. `same` means the request of the last round equals the
  current definition of the profile that its rung names. `changed` means it does not. An edit to the file never rewrites a recorded round.
- `status` also prints, for the next round, the profile and the location class of its server (`this-machine`, `owner-network` or
  `vendor-cloud`). **Open point:** the records do not say where the engine learns a server's class, and the class is held in the Ollama
  bridge's endpoint file. Increment E uses the bridge's own `check` output and stops and reports if it would have the engine read that
  file; where no class can be told it prints `unknown`.

### The action-review engine

*(Decided; built by increment F.)* The helper reads the `action-review` ladder through the kit reader and runs its one rung. A longer
ladder, a missing one and a missing file are refused as no verdict. The time budget does not change: 25 seconds for one judgement, with the
bridge given `--timeout` 20 and the rest of the time left, and a profile cannot change either, so a profile too slow for the budget
fails as a timeout and yields no verdict.

### The default `wb install` writes

*(Decided; built by increment J.)*

- It writes the file only when it is absent, as part of the install's preview; the digest at `ask` binds the bytes; an existing file is
  never overwritten or changed. The command is the owner's at the level the owner set.
- It builds the default only from what is installed and pinned and from the owner's endpoint file. For `ask-codex`: the profiles `quick`,
  `standard` and `deep` at `low`, `medium` and `high` with no model named, so the bridge's own default stands. For `ask-ollama`: one
  profile for the `default_model` of each record of a valid `bridge-endpoints.json`, named `local` when there is one record and
  `local-<record name>` when there are several, with
  `options.server` set to the record's name; a record with no `default_model` gets none, and neither does a record whose name makes
  `local-<record name>` longer than the 32 characters a profile name may have (the install names it and says why).
- Ladders are written only when exactly one bridge family is installed. For `ask-codex`, `default` is `quick, quick, deep` and
  `action-review` is `quick`, so that a judgement fits the time budget. For `ask-ollama`, `default` and `action-review` are the single
  `local` profile, and only when that profile was made; a record with no `default_model` makes no profile and no ladder, and the install
  says that the owner must configure a chat model. With several families or several local profiles the profiles are written and the
  ladders are not, and the install says that a review is refused until the owner chooses. With no bridge installed no file is written.
- The preview prints what an old `.workbench/review.json` said, as data, so the owner can carry it into a profile: only the four
  known fields, each as ASCII with escapes and cut at 128 characters, and one line saying so when the file is over 4,096 bytes or
  malformed. The text changes nothing that is written, so it is not part of the digest. The default is never seeded from that file.

### `wb doctor`

*(Decided; built by increments I and J.)* It reports a missing or invalid file; a ladder that names a profile the file lacks; a profile
whose bridge is not installed; a file at `.workbench/review.json` as unused; a `delegate-profiles` name that is not in the file; and a
listed profile that names no model, which follows the vendor's own default and can change under the gate.

### The `convergence` report and `delegate-profiles`

*(Decided; built by increments G, H and I.)*

- `converged` keeps its meaning (`review-engine.md`, "Convergence").
- The report's `format` becomes 2 and it gains `last_requested`: the bridge, the model asked for, the effort, the options (a map of
  strings) and the profile name of the last stored round; a value the round did not record, and everything for a round stored before the
  profiles are built, is `null`. The installer reads formats 1 and 2, and a report of format 1 reads as an unknown request. The cap on
  the size of the report (`MAX_CONVERGENCE_REPORT`, 4,096 bytes in `workbench/approvalcmd.py`) is raised to **8,192** by increment G. A
  worst-case `last_requested` is 8 options of at most about 170 characters each (a name of 32, a value of 128, and the quoting), about
  1.4 KB, with the other fields about 0.3 KB more; increment G measures today's report and may refine the figure. The existing `model` is the model the bridge
  reported; `last_requested.model` is the model asked for.
- The owner's settings file gains the entry `delegate_profiles` in a new version, 4 (the reader accepts versions 1 to 3 today and refuses
  an entry it does not know). Version 4 accepts everything version 3 accepts, and `delegate_profiles` only at version 4, as `levels`
  is accepted only at versions 2 and 3. A new file is still seeded at version 3, and a file becomes version 4 when the owner adds the
  entry. A workbench that predates version 4 reads such a file as an unsupported version and stops every checkpoint, which fails
  safe. Absent means `any`. Otherwise it is a list of 1 to **8** distinct names of `profiles`, each a string.
  `wb settings` prints `delegate-profiles approve-plan: any` or the list. Every other value (an empty list, a list that holds `any`, a
  duplicate, a name that is not a string, a longer list, a damaged entry) is invalid and refuses a delegated approval; it is never read
  as `any`. It takes effect only while `approve-plan` reads `delegated`, and a project, a plan or a review cannot supply it.
- **The check, for a list.** The installer compares the `last_requested` of the report with the current definition of each listed
  profile on one normal form. The bridge, the model, the effort and the options must all be equal. An absent or `null` model or effort equals
  another absent or `null` one; absent options equal the empty
  map; options compare as unordered maps of exact strings and the whole map must be equal. The name is not compared, and what is compared
  is the recorded request, never the rung that the ladder names today. It proceeds only if one listed profile matches. For `any` there is
  no check, and an unknown request never fails it.
- **It fails closed** for a list when: a listed name is not in the file; the file cannot be read or is invalid (the installer applies the
  same strict rules as the engine); a listed profile is invalid; the request is unknown (an engine that cannot report it, a report of
  format 1, a round stored before the profiles were built, another provider of `peer-review`); or no listed profile matches, a profile
  edited after the round included. The reason is printed and the owner approves the plan themselves.
- The check is made once, when the approval is asked for. It is not read again when an approval is read, and tightening the setting
  later does not withdraw an approval given earlier. Item 9 of `2026-10-23-delegated-plan-approval` stands: a delegated entry counts
  only while `approve-plan` reads `delegate` at that moment.
- **What it proves.** The check compares what was requested and not what ran. A profile with no model follows the vendor's default. For
  the Ollama bridge a model is a key of the endpoint record and `server` names a record, so an edit to `bridge-endpoints.json` can change
  what runs while the profile's strings still match: an edit invalidates a round only if it is an edit to `review-profiles.json`. The
  state that holds the last round is kept in the project and sealed with a key the agent can read (`review-engine.md`, "The seal"), so
  a forged state could claim a request, and could reset the ladder to its first rung; that is the trust level `converged` already has.
- **What is kept in the project.** The review's state records the name of the profile, the model name and the option values of each
  round, so nothing sensitive belongs in a model name or an option value, and the owner's file is not the only place they appear.
- **Version skew.** A new engine on a kit that lacks `profiles.py` fails to start, and an older engine reads a round of the new shape
  as unusable. No kit API number was raised, so the installer does not catch this; the recovery is to delete the review
  (`review-engine.md`, `archive` and `prune`) or to bring the installed copy up as a whole.

## Acceptance criteria

Each is checkable by the increment named.

1. The reader refuses a duplicate key, an unknown field, an oversize file, a bad name, a ladder of more than five rungs or none, an
   `action-review` ladder of other than one rung, a ladder that names an absent profile, a profile that holds a reserved option or a
   prefix of a reserved name (D-A), a value outside its grammar, and a file whose `format` is not 1 (B).
2. A declaration that lists a reserved name (or a prefix of one, D-A) or a grammar outside the closed list is refused by the reader and by `wb verify` (C).
3. The nth round of a window uses rung n, the last rung repeats, a bridge error spends no round and retries the same rung, and the first
   round after `reset` uses the first rung (D). The engine passes `--model`, `--effort` and the options of the profile, and nothing
   else from a profile; it does not read the module's declaration, so a bridge refuses an option it does not accept, and `wb doctor`
   and the delegated-approval check report an undeclared one (D, I, J).
4. A missing or invalid file ends a review with a message that names the file, and `.workbench/review.json` changes nothing (D, F).
5. Each round records its profile and request, and `status` prints the next profile, its server's class or `unknown`, and `same` or
   `changed` by the meaning above (D, E).
6. The action-review engine runs one rung and refuses a longer ladder (F).
7. A report of format 1 or 2 is read within the raised size cap; `last_requested` is `null` where nothing was recorded (G, H).
8. With `delegate-profiles` at `any` a delegated approval behaves as it does today; with a list it is refused for every case above and
   accepted only on a match of the bridge, model, effort and options. A settings file at version 4 is read, one at version 3 without
   the entry reads as `any`, and an older reader stops safely at version 4 (I).
9. `wb install` writes the default only when the file is absent, shows it in its preview, binds it to the digest and never overwrites it;
   it writes no ladder for several families or several local profiles, none for a profile that was not made, and no profile for a
   record whose name is too long; `wb doctor` reports the problems above (I, J).
10. The Result of increment K records a walk-through in a scratch store of each criterion above, with its limits (K).

## Governing decisions and references

- Decisions: `2026-11-04-review-profiles-in-the-guarded-store`, `2026-11-04-delegated-approval-checks-the-profile-of-the-last-round`,
  `2026-10-22-model-calls-go-through-vendor-bridges` (decision 5 superseded in part), `2026-10-26-action-review-reads-the-review-setting`
  (superseded), `2026-10-23-delegated-plan-approval`, `2026-11-01-endpoint-records-in-the-store`,
  `2026-11-02-model-configurations-in-endpoint-records`, `2026-11-02-model-section-defaults-and-the-embedding-name`,
  `2026-10-20-fixed-store-location`.
- Specs: `review-engine.md`, `action-review.md`, `model-bridge.md`, `module-contract.md`, `ask-ollama.md`, `command-permissions.md`,
  `installer-interface.md`, `trust-and-approval.md`.
- Plan: `docs/plans/2026-11-04-review-profiles.md`.
- Reference: the benchmark of the owner's repository `claude_global_config`, cited in the first decision's evidence
  (`git@github.com:rziegler42/claude_global_config.git`, commit `6ae05669fb1c39c1a1f9303cbca7633970ffd79d`, sha256
  `151ba86b245b46a3de6c4768a5806d5156749a9388c56a10b823f59ec16c4de6`, retrieved 2026-11-04): a higher effort of the cheaper model found
  no more injected defects, so a ladder is a choice about cost and not about recall.
