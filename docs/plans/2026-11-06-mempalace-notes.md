# Let agents save short notes as they work, and let the owner review them by exception

Status: Proposed
Created: 2026-11-06
Candidate: workbench-v1#mempalace-notes
Specs: mempalace-notes, mempalace, command-permissions

## Goal

Work that is worked out in a session is lost when the session is compacted or ends, and a second session cannot use it. `docs/specs/mempalace-notes.md`
(approved by the owner on 2026-11-06 as a design, reviewed in three rounds by the review engine) specifies notes: short texts that an agent saves as it works,
kept as drafts in the owner's machine-wide notes folder, reviewed by exception, and filed into the palace with the existing `mine`.

After this plan: an agent can save, list and read notes under a wing that is the project's (the per-clone setting, else the `origin` repo name, else saving is
blocked and says what to create) or a named topic wing; a note with a credential-shaped line is refused; the owner reviews the drafts of a wing through a short
summary of counts and outliers and confirms one `keep`, then the filing; drafts that nobody reviews are archived after 30 days; and the skill and the policy block
tell an agent when to save and when to look. `search`, `mine` and `sync` behave as before.

## Scope

- A helper for the notes commands with the verbs `wings`, `list`, `read`, `save`, `drop`, `merge`, `review` and `keep`, the notes folder and its subfolders, the
  file-name rule, the note format, the credential scan, the personal-detail and other flags, the overlap check, the lock, the journal of `keep`, and lazy expiry.
- The declaration of the commands and their keys and levels, and the tests of both.
- The text that tells an agent when to save and where to look: the module's skill and its policy block.
- The sentences of `docs/specs/mempalace.md` and `docs/development.md` that describe the module, and "As built" of `mempalace-notes.md`.

## Non-goals

- Mining finished sessions or a filtered export of them; a hook that saves at a compaction; the program's knowledge graph.
- Any change to `search`, `mine` or `sync`, including their default wing.
- Installing the module in another project (the knowledge-base project is the next user, in its own plan).
- A scheduled or background process. Expiry is lazy.
- A deterministic save: saving depends on the agent following the skill, which the spec states as a limit.

## Assumptions and constraints

- The helper's imports are pinned by a test, and its text must not hold the words the pin forbids (`mempalace.md`, "As built"). A new helper starts with its own
  pin. If a new import is needed (for example `hashlib` for the digest and the hashes of notes), the increment that needs it changes the pin's set and says so in
  its Result.
- Permission keys are per argument (`wb run <command> <argument>`). The levels the spec wants differ by verb (`save` at `none`, `keep` at `ask`), so each verb
  that needs its own level is its own argument. The spec's `wb run mempalace notes <verb>` is therefore a call to settle (below).
- The folder rules of `mine` stand: the notes folder is outside every project and outside `.git` and `.workbench`; `mine` is pointed only at `<notes>/<wing>`,
  never at the drafts or the archive folders.
- A folder that is deleted and recreated strands its drawers (`mempalace.md`, "Evidence"). The helper changes notes in place and moves them by rename.
- Process: tests first in a scratch clone, targeted tests only, the `reviewer` agent reads each increment, the owner copies the files with a recorded-hash script
  and runs the release approvals, and each increment is one commit with the trailer `Plan: 2026-11-06-mempalace-notes#<label>`. Nothing is pushed without the
  owner's word naming the branch and the remote.
- Everything a note holds from outside sources is data. The plan builds no way for a note to give an instruction.

**Open for the owner, to settle at the start of Increment A (the plan stops there until the owner answers):**

1. *The command shape.* The spec says arguments of `wb run mempalace notes <verb>`. Keys are per argument, so one `notes` argument cannot have `save` at `none` and
   `keep` at `ask`. The recommendation is a second command of the module, `mempalace-notes`, with its own helper and one argument per verb
   (`wb run mempalace-notes save`), because it also keeps the already large helper and its pin out of this work. The alternative is verbs as separate arguments of
   the existing command, which grows that helper.
2. *The levels.* `command-permissions.md` says an agent-run argument offers `block` and `none` and **defaults to `none`**, and only an owner-run argument defaults to
   `block`. So `wings`, `list`, `read`, `review`, `save`, `drop` and `merge` default to `none`: once the module is installed and the rules are rendered, an agent
   can save drafts without asking, and the owner sets a key to `block` to stop it. `keep` is owner-run and offers `ask` with the preview argument `review`, and its
   default stays `block`. The recommendation is to accept this: the writes are drafts in an untracked folder, never the palace, and the folder rules, the file-name
   rule and the credential scan bound them. The alternative is a different default for these arguments, which is a change to `command-permissions.md` and the
   permission system and would be a plan of its own; this plan does not make it.
3. *One confirmation or two.* The recommendation: two, `keep` and then `mine`, inside one review exchange, as the spec defines it.
4. *Reading the remote.* The recommendation: read `.git/config` with the existing strict file reader and take the `origin` url, rather than starting `git`.

## Completion criteria

1. The acceptance criteria 1 to 22 of `mempalace-notes.md` hold, each shown by a test, except 10 and 19, which are shown by the live run.
2. `search`, `mine`, `sync` and their tests are unchanged and pass.
3. The module suite, and the four repository tests that cover the declaration, the keys and the rendering, pass in the scratch clone and, after the owner's copy, in
   the live tree (`wb run code-work check` passes).
4. A live run by the owner: a brainstorm saves notes without a question to the owner; after a compaction the agent finds them; a side session finds one note and
   saves its finding; the owner reviews once and files; the result is recorded in the spec's evidence.

## Increments

### Increment A — The command shape, the notes folder, the wing rule, and the read side

**Outcome:** `wings`, `list` and `read` work on the notes folder, with the wing rule, the folder creation rules and the note format; the declaration and keys exist.
**Dependencies:** the owner's answers to the four open points.
**Affected areas:** the new helper and its pin test, `module.json` (the new command, its arguments, keys and levels), the new test files, `docs/specs/mempalace-notes.md`
(the command name if it changes, and the settled points), `docs/specs/mempalace.md` (the table rows `helpers`, `ships` and `commands`, so that the module contract
is true from this commit and each later one), `docs/specs/command-permissions.md` (the sentence that names the modules that declare `ask`, only if `keep` is declared
in this increment), the package's release records.
**Steps:**
1. Stop and ask the owner the four open points. Record the answers in the spec and in this plan's Result.
2. Write the tests first and see them fail, with a scratch home: the wing is the file's, else the `origin` repo name, else the call is blocked with the text that
   says what to create, and the file wins when both exist; a remote whose name is not a valid wing name blocks; the notes folder is made at first use only, one
   level at a time, mode 0700, with no link followed, and is not made by `list` or `read`; `wings` shows names, counts of reviewed notes and drafts, the date of
   the newest, and the archive count apart; `list` filters by wing, kind and state with the defaults of the spec; `read` prints between the recalled-data
   markers, refuses an ambiguous name, and narrows by state; the note format is parsed strictly and a malformed file is refused whole and named; names with
   `..`, a separator or a control character are refused; the output is cleaned and bounded.
3. Write the helper's read side, the notes folder module, and the declaration; set the keys and levels as answered. Edit the rows of `mempalace.md` that the
   declaration changes in the same commit, so the spec never says what is no longer true.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps: copy the files with the recorded-hash script, run `wb preview release-approvals` and `wb release-approvals --digest`, the removal of the
   stale records only after the owner approves the list, then "commit a"; after the commit `wb upgrade` and `wb rerender` (the rendered rules gain the new keys).
**Verification:** the module's tests in the scratch clone (`python3 -B -m unittest discover -s packages/workbench/mempalace/tests -p 'test_mempalace_*.py'`), and
the four repository tests for the declaration, the keys and the rendering (`test_owner_argument_run`, `test_rendering`, `test_settingscmd`,
`test_permissions_drift`) because the declaration and the keys change. Not run: the whole suite.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-mempalace-notes#A`.

### Increment B — `save`: names, the credential scan, size, overlap, `--into`, revisions, and expiry

**Outcome:** an agent can save a draft, extend a note, and make a revision of a reviewed note; nothing unsafe reaches the folder; old drafts are archived.
**Dependencies:** A.
**Affected areas:** the helper, its tests, the spec ("As built" for this part) and the rows of `mempalace.md` that the commands change, the release records.
**Steps:**
1. Write the tests first and see them fail, each from the spec's acceptance criteria 3 to 6, 9, 13, 14 and 18 and the file-name rule: the normalisation, an unsafe or
   empty title refused, a collision refused with and without `--new`, no overwrite, exclusive create, no link followed; the minimum size; each credential pattern
   refused with the line number and the pattern's name and never the text, in the title, the source and verify lines, the body, and the paragraph added with
   `--into`, and the same note reworded saved; the overlap refusal and its listing, `--into` with no match and with two matches, `--new` recorded as
   `new despite`; an addition to a draft as a dated paragraph and to a reviewed note as a revision draft that leaves the reviewed note unchanged; two saves at once
   serialised by the wing's lock; a killed save leaves the old note whole; the lazy expiry at the start of `save`, `list`, `wings` and `review`, idempotent, by rename,
   with the archive name suffixed with the UTC time.
2. Write `save` and the expiry. The scan patterns are the spec's minimum list.
3. Run the verification and ask the `reviewer` agent to read the change. The security review of this increment (a filesystem surface, parsing, credentials) is the
   owner's to ask for. Write the result in this plan.
4. The owner's steps as in A, with the level of the `save` key.
**Verification:** as in A, the module tests; the repository tests only if the declaration changed.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-mempalace-notes#B`.

### Increment C — `drop`, `merge`, `review` and `keep`

**Outcome:** the owner can review one wing's drafts by exception and keep them, and the reviewed notes are what `mine` files.
**Dependencies:** B.
**Affected areas:** the helper, its tests, the declaration (the owner-run `keep` with the preview argument), the spec, the rows of `mempalace.md` and the sentence of
`command-permissions.md` that name the modules declaring `ask`, the release records.
**Steps:**
1. Write the tests first and see them fail, from the acceptance criteria 7, 8, 15, 17, 20, 21 and 22: the note syntax and the refusals of `drop` and `merge`; the
   routine and outlier sort with each mechanical flag (size, personal-detail shapes, near-duplicate by word overlap, a new wing, a revision that changes more than half
   of a note, age) and the judged flags kept separate and labelled; `review` prints counts and only the outliers, plain short lines, and a digest that is stable and
   changes with a draft; the credential scan runs again at `review` and `keep`; `keep` needs `--wing` and the digest, recomputes it inside the wing's lock, refuses a
   changed set, moves only what the digest covers, replaces a reviewed note only from a revision that names it; the journal and the retry for `keep` and the order
   and retry for `merge`, with a test that stops after every step; `drop` and `merge` archive with the time suffix and never replace; `mine` is not pointed at the
   drafts or the archive.
2. Write the four verbs and the sort. Keep the sort mechanical; the judged flags come from the agent and are only displayed.
3. Run the verification and ask the `reviewer` agent to read the change. The security review of this increment is the owner's to ask for. Write the result here.
4. The owner's steps as in A, with the level of `keep`.
**Verification:** as in A, and the repository tests because the declaration gains an owner-run argument with a preview.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-mempalace-notes#C`.

### Increment D — The skill and the policy text

**Outcome:** an agent knows when to save, how to find notes again, and how to run one review exchange, without asking the owner anything else.
**Dependencies:** C.
**Affected areas:** the module's skill `recall-memory` and its policy block, their guidance tests, `tests/test_permissions_drift.py` if a skill names a key that offers
`ask`, `docs/specs/mempalace.md`, `docs/specs/mempalace-notes.md` ("As built"), `docs/development.md`, the release records.
**Steps:**
1. Write the tests first and see them fail: the skill and the block say, in plain words, to save silently after an accepted playback of a brainstorm with no spec,
   after a problem solved under the owner's guidance, and for a researcher's run with its source, locator, date and hash; to list the project's notes before saving
   and extend rather than create; to search the project's wing and the `ideas` wing before drafting a spec, a decision record, a roadmap candidate or a plan and
   before brainstorming or researching; to run `list` after a compaction or in a new session on a brainstorm with no spec; to run `wings` and search the topic wings
   that look relevant when starting work with a tool or hardware; never to write a credential or a personal detail; to ask the owner about notes at most once per
   session, in one review exchange; and that a fact about a machine is checked with its `verify` line. The permission-drift test passes.
2. Write the text. It names no tracked path to an untracked folder.
3. Edit `mempalace.md` (the table and a short section that points to the new spec), `docs/development.md` (the commands), and "As built" of `mempalace-notes.md`.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result here.
5. The owner's steps as in A.
**Verification:** as in A, and the guidance and drift tests.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-mempalace-notes#D`.

### Increment E — A live run, recorded

**Outcome:** `mempalace-notes.md` records what happened in real sessions.
**Dependencies:** D, installed, and the owner's levels set (`save`, `drop` and `merge` at `none`, `keep` at `ask`).
**Affected areas:** `docs/specs/mempalace-notes.md` ("Evidence").
**Steps:**
1. The owner runs the live run of completion criterion 4 and reports what happened, including every question the agent put to the owner and every note that was
   wrong, missing or noisy.
2. Record the owner's report, dated, under the spec's evidence, as it was said: do not edit it into a pass. State what it shows and what it does not.
3. If the run shows a failure of the spec's anti-goals (no value, or too needy), say so and propose the change; do not widen this plan.
**Verification:** `wb run code-work check` passes.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-mempalace-notes#E`.

## Verification for the plan as a whole

Each increment's recorded verification stands. After E the owner's live run is the check of criteria 1 and 4 that tests cannot make. The whole suite is not run: the
installer's files do not change; the four repository tests named in A are run when the declaration or the keys change.

## Risks and sensitive actions

- An agent writes files in the owner's home, outside the project, without a confirmation per write, **by default**: the agent-run arguments default to `none` (open
  point 2), so installing the module and rendering the rules turns saving on until the owner sets a key to `block`. The folder rules, the
  file-name rule, the credential scan and the lock are what stand between a hostile or careless title or text and the disk. A security review of B and C together is
  the owner's to ask for; the plan asks again at B.
- A note can reach the palace only through `keep` and `mine`, both confirmed by the owner. Routine drafts are not read by the owner; the mechanical flags are what
  separate them from the outliers, and the spec states what a scan cannot find (a name or a home town in a plain sentence).
- Notes from outside sources can carry text that tries to give instructions. They are recalled as data, and nothing here makes them more.
- The notes folder is the only copy of the reviewed notes' sources, because the palace can be rebuilt only from the folders that were mined. The owner keeps it.
- Saving depends on the agent following the skill; a missed save is possible.
- The helper's pin test is changed if a new import is needed; that is a visible change in the increment that makes it.
- The rendered deny rules and the owner's level settings change with the new keys; a clone that has not rerendered still denies them to the agent, which is safe.

## Review record

Reviewer: the review engine's bridge to the second model (`gpt-5.6-terra`, through the `ask-codex` bridge), on 2026-11-06. Rounds: 2 of 3, converged: round 2 returned no
meaningful finding. Two findings, both major, both applied, none rejected. The design spec was reviewed separately, in three rounds with `gpt-5.6-luna`
(twelve findings, all applied).

- R1-F1: the plan gave `save`, `drop` and `merge` a default of `block`, which `command-permissions.md` does not allow for an agent-run argument (they default to
  `none`). Applied: open point 2 now says the default is `none`, that saving is therefore on by default once the module is installed and the rules are rendered, and
  that a different default is a separate change; the risk is named; the sentence in `mempalace-notes.md` that said `block` is corrected.
- R1-F2: Increment A would have added a command to the declaration while `mempalace.md` said the module ships one command until Increment D. Applied: A, B and C
  edit the rows of `mempalace.md` and the sentence of `command-permissions.md` that the declaration changes, in the same commit.

Left for the owner: approval of the plan as it stands, and the four open points, which the plan asks at the start of Increment A. The default of `none` for the
agent-run arguments is a change from what the owner was told in the design conversation (`block`); the owner decides whether to accept it.

## Deferred work

- Mining finished sessions, with redaction; a hook that saves at a compaction; a deterministic save.
- Exposing the program's knowledge graph for facts that change (the program has `invalidate` and a timeline).
- Installing the module in the knowledge-base project, and the researcher agents that would use it.
- A command to restore an archived note, and a rename of a wing.
- A check of the module for `wb doctor`, and the embedder-identity warning.

## Result

Empty until work starts.
