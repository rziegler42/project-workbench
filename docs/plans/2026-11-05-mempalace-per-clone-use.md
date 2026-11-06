# Make mempalace work per clone without setup, and run mine and sync at ask

Status: Proposed
Created: 2026-11-05
Candidate: workbench-v1#mempalace-per-clone-use
Specs: mempalace, command-permissions

## Goal

Using the `mempalace` module for a few days showed what a clone needs and what it should not leave behind (the evidence of `mempalace.md`, 2026-11-05).
The owner's direction: not every developer uses mempalace in a clone, so a tracked setting is wrong; the files `init` writes must not clutter the
working tree; `mine` should be runnable from a session like the other owner commands; a clone without the program must not be nagged. After this plan:

1. the project's setting is read from `.workbench/local/mempalace.json` (untracked, per clone, covered by the `/local/` ignore) and not from
   `.workbench/mempalace.json`, which the helper no longer reads; the tracked file is removed;
2. with no setting, the wing defaults to the project folder's name when it is a valid wing name, and a search and a `mine` use it; the file only
   overrides the wing or names a palace;
3. when the `mempalace` program is not found, the helper's refusal says that mempalace is not set up on this machine and the search is skipped, and the
   `recall-memory` skill tells the agent to go on without reporting that one case; every other refusal is unchanged and stays reportable;
4. `wb run mempalace init` is gone;
5. `mine` and a new `sync` (the program's pruning of drawers whose source files are deleted, moved or now gitignored) offer the level `ask`, with a
   `preview` that prints what they would do and a digest, and run with `--digest`; the level `block` (a terminal) stays the default; the helper's own
   terminal test goes for these two;
6. after a `mine`, the helper prints one line if the program has created `mempalace.yaml`, `entities.json` or `.gitignore` (or the other spellings of the
   config) in the folder, and says they can be deleted;
7. the docs say what is now true: no `init` in `docs/development.md`, the right place of `hallways.json`, that the palace is rebuildable only from the
   folders mined, that a mine refreshes changed files and leaves deleted ones until `sync`, and where the embedding runtime keeps its device id.

## Scope

- `packages/workbench/mempalace/helper/mempalace`, `module.json`, `harness/neutral/skills/recall-memory/SKILL.md`, and the tests under
  `packages/workbench/mempalace/tests/` (`test_mempalace_owner.py`, `test_mempalace_run.py`, `test_mempalace_module.py`, `test_mempalace_launcher.py`,
  `test_mempalace_guidance.py`).
- `docs/specs/mempalace.md`, `docs/specs/command-permissions.md` (the item that lists `mempalace init` and `mine` among the owner-run arguments without
  `ask`) and `docs/development.md`.
- The owner's steps: the copy and release of each package edit, `wb upgrade` and `wb rerender` (the rendered deny rules in `.claude/settings.local.json`
  change with the declaration), removing the tracked `.workbench/mempalace.json` after the owner approves the list, and setting the level of
  `wb run mempalace mine` and `sync` to `ask` in the owner's settings.

## Non-goals

- Filing lessons and brainstorms: reviewed notes written by an agent, or a filtered export of finished sessions that keeps the conversation and drops
  tool output and secrets. A later candidate.
- The levels `none` and `delegated` for these commands; a command to edit the setting file; a `sources` key (a list of folders to mine); a module check;
  the program's embedder-identity warning (an owner command); confining `--wing`; adding the module to another project.
- Any change to `search`, `status`, the agent-safe commands' output, or the palace.

## Assumptions and constraints

- `.workbench` and `.workbench/local` must be real directories (`installer-interface.md`); a clone without `local` has no setting file, which is not an
  error. The file is read through the project's held descriptor as today, so a link in place of it or of a directory above it is refused.
- The validation of the setting is unchanged: the same keys (`format`, `palace`, `wing`), the same refusals. Only the path and the absence change.
- The default wing is the basename of the project root; it must match the name pattern the helper already uses for `--wing` (at most 64 letters, digits
  and `._:-`, not starting with `-` or `.`), else there is no default and a search covers every wing as it did before. The project root is the
  one the helper already finds. This changes a default: a clone with no file used to search every wing and now searches its own.
- The launcher reads the level and the terminal test for an owner-run argument (`ownerargs.py`); a command that offers `ask` declares `levels` and a
  `preview` argument, the preview prints the lines of what the command would do and, last, `digest: <32 hex>`, and the run takes `--digest`. The kit's
  `digest` module makes and checks the digest. At `block` the launcher still needs a terminal.
- The digest binds the project, the folder, the wing, the palace and the program's dry-run lines (file names and drawer counts). It does not cover the
  contents of the files. The preview shows what the owner approves; a file that changes its content but keeps its name between the preview and the run
  is not caught. The plan records this limit.
- `mine` has no time limit. At `ask` it runs inside a session whose own command timeout may end a long run; the plan notes it and does not change it.
- `sync` was tested on scratch data (2026-11-05): with no flag it is a dry run and changes nothing; `--apply` removes the drawers of missing files
  ("Missing: 1 (removed)"); it also removes the drawers of files that are now gitignored. It needs a wing or a folder to apply; the helper always gives both.
- The removal of the tracked setting changes what `wb acknowledge` lists; the owner acknowledges once more.
- The helper imports only the modules its test allows; the digest comes from the kit's `wbkit` package, which the helper already imports from.
- A change to `packages/` follows the package-edit process: a scratch clone, tests there, the owner's copy with the recorded-hash script, the release
  approvals, and the removal of stale shipped records after the owner approves the list. The command gate refuses Bash while the packages differ from
  the release.
- Nothing is pushed. A commit needs the owner's word.

## Completion criteria

1. A setting at `.workbench/local/mempalace.json` is read with the same validation as before; the same file at `.workbench/mempalace.json` is not read; a
   missing `local` directory means no file.
2. With no file, `search` and `mine` pass `--wing <folder name>` when it is a valid name and nothing when it is not; a file's `wing` and `palace` override.
3. The refusal for a missing program contains "not set up on this machine" and "skipped"; the skill says to go on without reporting it; the other
   refusals keep their wording and the skill's rule to report them.
4. `init` is refused as an unknown argument; `module.json` lists only `mine` and `sync` as owner-run arguments; no test, spec or doc offers `init`.
5. The digest is compared inside the helper's lock (`mempalace-helper.lock`, beside the palace), which a second run finds held and refuses. `preview mine <dir>` and `preview sync <dir>` print lines and a digest and write nothing; `mine <dir> --confirm --digest <d>` and
   `sync <dir> --confirm --digest <d>` run only with the digest of the lines as they are now, and refuse otherwise; a missing digest at `ask` is refused;
   at `block` the launcher requires a terminal (its test passes); the keys `wb run mempalace mine` and `sync` offer `block` and `ask`, and
   `wb run mempalace preview` reads `none`; the permission tests that read declarations pass.
6. After a `mine` that leaves one of the six names in the folder, one line on standard error names it; with none left, nothing is printed; the helper
   deletes nothing.
7. The docs say what is true and carry none of the stale statements listed in Goal item 7.
8. The owner's live checks: from a session at `ask`, a `preview` and a confirmed `mine` of a small folder, and a `sync` dry run; recorded in the spec's evidence.

## Increments

### Increment A — The setting is per clone, and the wing has a default

**Outcome:** the setting is read from `.workbench/local/mempalace.json`, the wing defaults to the folder name, and the tracked file can go.
**Dependencies:** none.
**Affected areas:** `helper/mempalace` (`project_setting`, `search`, `owner`), `tests/test_mempalace_owner.py` (the `Setting` and `Wing` classes) and
`test_mempalace_run.py`, `docs/specs/mempalace.md` ("Palace location", "First use in a project"), the package's release records (the owner's steps).
**Steps:**
1. In a scratch clone, write the tests first and see them fail: the new path is read and the old is not; every malformed shape is refused at the
   new path with the same messages; no `local` directory or no file is no setting; the default wing from the folder name (valid, invalid, a name that
   starts with `-` or `.`, a long name, a name with a space); a file's wing overrides the default; `status` and `init`-free commands take none; the
   default reaches the fake program as `--wing`.
2. Change the path and add the default in `project_setting`; `search` and `mine` use the wing it returns.
3. Edit the spec: the path, the default, the first-use steps (no file needed), and the note that the old path is ignored.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps: copy, release, remove the stale shipped records; then, after the commit, remove the tracked `.workbench/mempalace.json` with a
   `safe-git remove` preview and the owner's word, acknowledge, and commit the removal with the install-state files.
**Verification:** the `mempalace` module tests as the repository's runner runs them, and `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-per-clone-use#A`.

### Increment B — A clone without the program is told to skip

**Outcome:** a missing program is a skip, not an error to report.
**Dependencies:** none.
**Affected areas:** `helper/mempalace` (the refusal when the program is not found, in `query_program` and `run_owner`), `harness/neutral/skills/recall-memory/SKILL.md`
("If the command refuses or fails"), `tests/test_mempalace_run.py`, `tests/test_mempalace_guidance.py`, `docs/specs/mempalace.md`.
**Steps:**
1. Write the tests first and see them fail: with the program absent from the trusted path, `status` and `search` refuse with a one-line message that
   contains "not set up on this machine" and "skipped" and still say no program was started; a refusal for a malformed setting, a missing model, a
   failing program or an unknown option keeps its wording; the skill contains the skip rule for exactly that message and keeps "Read the reason, stop, and
   report it to the owner" for the others; the skill's line "Never run `init` or `mine`…" stays as it is in B (C rewords it); the block is unchanged
   and has at most 14 lines.
2. Change the message; add the sentence to the skill, which pins the words of the message.
3. Edit the spec's description of the refusals.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps as in A, and `wb upgrade` and `wb rerender` (the skill is installed under `.claude/skills/`).
**Verification:** the `mempalace` module tests and `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-per-clone-use#B`.

### Increment C — `init` is removed

**Outcome:** the module has no `init`.
**Dependencies:** none.
**Affected areas:** `helper/mempalace` (`owner`, `parse_owner`, `OWNER_FLAGS`, `OWNER_VALUES`, `USAGE`, `main`), `module.json` (`arguments`, `owner`),
`tests/test_mempalace_owner.py` (the `Init` class and the init cases of the others), `test_mempalace_run.py`, `test_mempalace_module.py`,
`test_mempalace_launcher.py`, `harness/neutral/skills/recall-memory/SKILL.md` (line 50, "Never run `init` or `mine`") and `test_mempalace_guidance.py`
(line 222 pins that sentence; line 96 and line 166 search for `init`), `docs/specs/mempalace.md`, `docs/specs/command-permissions.md` (the item that names `wb run mempalace init`),
`docs/development.md`, the rendered rules in `.claude/settings.local.json` (the owner's rerender), the package's release records.
**Steps:**
1. Write the tests first and see them fail: `init` is refused as unknown with the usage line; the declaration lists `status`, `search` and `mine`
   only, with `mine` the only owner-run argument; no helper code path mentions `--no-llm`; the skill's line forbids the owner's commands without naming
   `init` ("Never run `mine`, and never use the program directly. Those are the owner's."), and the guidance test pins the new sentence. E adds `sync` to
   the sentence and its pin.
2. Remove the argument, its checks and its constants; reword the skill's line and its pin; keep the checks `mine` shares (the folder rules, the planted-config refusal, the palace overlap).
3. Edit the specs and the guide: no `init`, and why (the program writes two files into the scanned folder, `mine` needs neither).
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps as in B.
**Verification:** the `mempalace` module tests, `wb run code-work check`, and the repository tests that read declarations and permission keys
(`tests/test_owner_argument_run.py`, `tests/test_rendering.py`, `tests/test_settingscmd.py`, `tests/test_permissions_drift.py`), because the
declaration and the set of keys change.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-per-clone-use#C`.

### Increment D — `mine` runs at `ask`, with a preview and a safeguard

**Outcome:** `mine` offers `ask`, previews with a digest, and says if the program left an `init` file behind.
**Dependencies:** C.
**Affected areas:** `helper/mempalace` (a `preview` argument, the digest check in `mine`, the removal of the terminal test for `mine`, the check after
`mine`), `module.json` (`levels`, `preview`), `tests/test_mempalace_owner.py`, `test_mempalace_run.py`, `test_mempalace_module.py`,
`test_mempalace_launcher.py`, `docs/specs/mempalace.md`, `docs/specs/command-permissions.md` (the item moves from "not built" to built for `mine`),
`docs/development.md`, the package's release records.
**Steps:**
1. Write the tests first and see them fail: `preview mine <dir>` runs the program's dry run and prints the lines and `digest: <32 hex>` and writes nothing;
   the lines hold the project, the folder, the wing, the palace and the dry run's file names and drawer counts and no file content; `mine <dir>
   --confirm --digest <d>` with that digest runs, with another digest or none refuses with the kit's line and starts no filing; changing a file's
   name or the number of files between the preview and the run changes the digest; without a terminal and with the level `ask` the helper does not
   refuse for lack of a terminal; the safeguard prints one line naming a created `mempalace.yaml`, `entities.json` or `.gitignore` (any case) and
   prints nothing when none was created, and deletes nothing; the folder rules (not the project root, not `.git` or `.workbench`, no link, no palace
   overlap) apply to the preview as to the run; the declaration lists `levels` `{"mine": ["ask"]}` and `preview: "preview"`; with the lock held by
   another process (a test holds it), `mine --confirm --digest` refuses at once and starts no program; the lock is taken before the lines are
   rebuilt (a fake program that changes the folder between the preview and the run shows a changed digest refused); a link at the lock's path or
   at the palace's parent is refused; on a machine with no palace parent directory and no lock file the preview succeeds and a listing of the filesystem before and after is identical; a run
   makes an absent palace parent with mode 0700 and refuses one whose own parent is absent; a clone with
   no `.workbench/local` runs at `block` and at `ask` and gains no directory; the lock is free again after a run, after a refusal and after a
   killed run; the helper's import pin names `fcntl`.
2. Add the preview and the digest check using the kit's `digest`, taken inside the helper's own lock (see "The lock" below); remove the helper's
   terminal test for `mine`; add the check after the run.

   **The lock.** `command-permissions.md` has a module compare an `ask` digest inside its own lock; the helper has none, so D adds one. What two
   runs contend for is the palace, which every clone of the owner shares, so the lock sits beside the palace and not in a clone: an exclusive,
   non-blocking `flock` on `mempalace-helper.lock` in the palace's parent directory (`~/.mempalace` for the default palace). That directory is
   opened without following a link and must be a real directory; if it is absent the helper makes it (one level, mode 0700, as the program
   would) and refuses if its own parent is missing. The file is opened without following a link, mode 0600, and refused if it is not a regular
   file. No directory of the clone is created. Only a run (`mine` or, in E, `sync`) takes the lock and creates what it needs: it rebuilds the
   preview lines from the state as it is then, compares the digest, and keeps the lock until the program has exited. The preview takes no lock
   and creates nothing, so its "writes nothing" holds on a fresh machine; the digest it printed is checked again under the lock. A second
   helper run that finds it held refuses at once with "another mempalace run is in progress" and starts no program. The operating system drops
   the lock on exit, including a kill. It applies to the terminal runs at `block` too. The helper's import pin gains `fcntl`, and the plan
   records the limit: the lock excludes another helper run, not an edit made to the folder by hand between the digest check and the program
   reading it.
3. Edit the specs and the guide: `mine` at `ask`, the digest's limit (names and counts, not contents), the safeguard, the correct place of `hallways.json`
   (`~/.mempalace/hallways.json`), where the embedding runtime keeps its device id, and that the palace is rebuildable only from the folders mined.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan. Ask the owner whether to run a security review
   of D and E together: an agent can now start a write to the palace, with the owner's confirmation of each command.
5. The owner's steps as in B, then setting the level of `wb run mempalace mine` to `ask` in the owner's settings and a `wb rerender`.
**Verification:** the `mempalace` module tests, `wb run code-work check`, and the four repository tests named in C. A live check is criterion 8.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-per-clone-use#D`.

### Increment E — `sync`, at `ask`

**Outcome:** the owner can prune the drawers of deleted files from a session, with a preview and a digest.
**Dependencies:** D.
**Affected areas:** `helper/mempalace` (a `sync` argument, its preview), `module.json` (`arguments`, `owner`, `levels`), the same tests as D, `docs/specs/mempalace.md`,
`docs/specs/command-permissions.md`, `docs/development.md`, the package's release records.
**Steps:**
1. Write the tests first and see them fail, with a fake program that records its arguments: `preview sync <dir>` runs the program's `sync <dir> --wing <w>` with
   no `--apply` and prints its report with a digest; `sync <dir> --confirm --digest <d>` runs it with `--apply` only with the digest of the report as it is
   now; any other option is refused; the wing is the setting's or the default and never another; the folder rules of `mine` apply; the keys offer `block` and
   `ask`; the report is cleaned and bounded like the other outputs.
2. Add `sync` and its preview, reusing D's digest, folder checks and lock; a test holds the lock and `sync --confirm --digest` refuses.
3. Edit the specs and the guide: what `sync` removes (the drawers of deleted or moved files, and of files now gitignored), that the dry run is the default,
   and the scratch test that showed it.
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan. The security review of D and E, if the owner asks for it.
5. The owner's steps as in D, with the level of `wb run mempalace sync`.
**Verification:** as in D.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-per-clone-use#E`.

### Increment F — Close the findings of the security review of D and E

**Outcome:** the folder rules of `mine` and `sync` cannot be walked around by another spelling of a path; the folder is checked again just before the
program starts; a helper killed without warning no longer leaves the lock free while the program runs.
**Dependencies:** E.
**Affected areas:** `helper/mempalace` (`owner_directory`, `refuse_palace_overlap`, `run_owner_captured` and the point where the program is started), the tests
of D and E, `docs/specs/mempalace.md`, the package's release records.
**Steps:**
1. Write the tests first and see them fail, on the case-insensitive filesystem of the scratch clone and with spellings made by hand where it is
   case-sensitive. Refused, for both `mine` and `sync`, at a terminal and at `ask`: `.GIT`, `.Git`, `.WORKBENCH` and `.WorkBench/local` (inside the project);
   the project root and its parent in another case, without `--allow-project-root`; the palace folder, a subfolder of it and a folder holding it in another
   case; the same with composed and decomposed Unicode in a name. A folder that only looks like one of these (`.github`, a sibling named `palace2`) is still
   allowed.
2. Compare paths by identity, not by spelling: `os.path.samefile` or the device and inode of each path and of its parents against `.git`, `.workbench`, the
   root and each palace, with the case-folded and normalised spelling as a second test where a path does not exist yet. Keep the messages.
3. Check the folder again immediately before the program starts, after the digest is verified inside the lock: the same `lstat`, `realpath` and identity
   checks, and the same device and inode as the first check, else refuse with nothing started. A test swaps the folder for a link between the digest check
   and the start. The race is narrowed, not closed, because the program takes a path; say so in the spec.
4. Keep the lock for as long as the program lives: the descriptor is inherited by the program (or the program is made to end when the helper dies), so a
   second run is refused after the helper was killed with `SIGKILL`. A test kills a helper that runs a fake program that sleeps, then starts a second
   confirmed run and expects the refusal. If this cannot be done within the helper's pinned imports and forbidden words, stop and report, and record it as a
   documented limit instead.
5. Edit `docs/specs/mempalace.md`: the folder rules compare by identity; the second check and what remains of the race; the lock and a killed helper.
6. Run the verification and ask the `reviewer` agent to read the change, and ask the owner whether the security reviewer looks at the fix, because a fix is
   new attack surface. Write the result in this plan.
7. The owner's steps as in D.
**Verification:** as in D.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-per-clone-use#F`.

### Increment G — Close the Low findings of the security review of F

**Outcome:** a program configuration that is a link no longer switches off the palace-overlap guard; a malformed saved palace path no longer ends in a traceback; a lock held by a process
the program left behind says so; the documents state what remains. (The security review of F, 2026-11-06, found no Critical, High or Medium issue and four Low ones; this increment takes the
first three and records the fourth.)
**Dependencies:** F.
**Affected areas:** `helper/mempalace` (`saved_palaces`, `ready()` in `owner`, the refusal of a held lock), the tests of F, `docs/specs/mempalace.md`, the package's release records.
**Steps:**
1. Write the tests first and see them fail: (a) a `~/.config/mempalace/config.json` (and `~/.mempalace/config.json`) that is a symlink to a file naming a palace is read, so a folder that is
   or holds that palace is refused, and `preview` lists that palace under "palaces the program may use"; a dangling link, a link to a directory and a file that is not JSON add nothing and do not
   refuse a folder that overlaps nothing; (b) a saved `palace_path` that cannot be encoded as a path (a lone surrogate) or holds a NUL is skipped, and neither `preview`, a terminal run nor a
   digest run ends in a traceback, the last also when the file is changed between the digest check and the start of the program; (c) a held lock is refused with the existing words and, in the same
   line, says that a process an earlier run's program started may still hold it; the existing assertions on "another mempalace run is in progress" still pass.
2. Make the read of the program's configuration follow a link for that one read (the content only decides which path to compare; the path is resolved, then opened without following a link
   at the end), skip a saved value that `os.fsencode` rejects, and let `ready()` treat any `ValueError` as a change. Add the clause to the held-lock refusal. Change nothing else.
3. Edit `docs/specs/mempalace.md`: that the program's configuration may be a link and is followed for the comparison; that a saved relative `palace_path` is not compared, because the program
   runs in its own scratch directory; that a descendant the program leaves running (in its own session) keeps the lock until it ends and the helper cannot stop it; and that a run with a wrong
   digest holds the lock for the length of the dry run, up to 300 seconds, so an agent can make the owner's confirm be retried (a limit that F did not change and G does not remove).
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps as in D.
**Verification:** as in D.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-per-clone-use#G`.

## Verification for the plan as a whole

Each increment's recorded verification stands. After E the owner runs the live checks of criterion 8 at the level `ask`, and the result goes into the spec's
evidence with the commands read from the session. The whole suite is not run: no installer file changes; the four repository tests named in C are run
because the declaration and the permission keys change.

## Risks and sensitive actions

- An agent can start a `mine` or a `sync` at `ask`: a write to the owner's palace, bound to a digest that covers names and counts and not contents, and
  confirmed by the owner in the harness's prompt. `--mode convos` can file session transcripts the same way. The folder rules stay; the owner reads the
  folder before confirming. A security review of D and E was run at the owner's request on 2026-11-06; its findings are the work of increment F.
- `sync` deletes drawers. It is a dry run by default, limited to the project's wing, and applied only with a matching digest; the program also removes the
  drawers of files that are now gitignored, which the preview shows.
- The default wing changes what a search covers for a clone with no file. It narrows it, which is the safer default.
- Removing `init` removes a command an owner might use. Nothing is released; `mempalace init` can still be run directly, without the wrapper's checks.
- The rendered deny rules and the owner's level settings change; a clone that has not rerendered still denies `mine` to the agent, which is safe.
- The helper's imports are pinned by a test; the digest comes from the kit and should not add an import.

## Review record

Reviewer: the review engine's bridge to the second model (`gpt-5.6-terra` in rounds 1 and 2, `gpt-6.1-sol` in round 3), on 2026-11-05. Rounds: 3 of 3, the
bound; the third round did not converge. Four findings, each major, all applied, none rejected.

- R1-F1: Increment D named no lock for the `ask` digest, which `command-permissions.md` requires of a module command. Applied: D now defines an exclusive,
  non-blocking `flock`, its refusals and lifetime, and tests for contention; E reuses it.
- R2-F1: C removed `init` but not the skill's sentence and the guidance test that pin it. Applied: C lists both and gives the replacement sentence; B keeps
  the old line until C.
- R2-F2: the first lock location needed a directory that a fresh clone lacks. Applied: the lock moved beside the palace, the resource that clones
  share, and no directory of the clone is created.
- R3-F1: the preview was to write nothing yet to take a lock that creates files. Applied: the preview takes no lock and creates nothing; only a run
  does, and it checks the digest again under the lock.

Left for the owner: the fourth round the bound does not allow (`extend` is the owner's), or approval as it stands; whether to run a security review of D and
E, which the plan asks again at D. The last change (R3-F1) was not read by the reviewer.

## Deferred work

- Filing lessons and brainstorms: reviewed notes the agent drafts into an untracked folder that `mine` accepts, with a nudge from the `brainstorm` skill;
  and a filtered export of finished sessions (conversation kept, tool output dropped, secrets redacted) for the discussions the owner wants in full.
  Raw `mine --mode convos` was tried on a scratch palace and files the tool output too. Session files are kept for about 30 days.
- A `sources` key in the setting (folders to mine), a check of the module for `wb doctor`, the embedder-identity warning, and the level `none`.
- Adding the module to the knowledge-base project, which would get this version if it is added after the plan is released.

## Result

**Increment A (2026-11-05), done in a scratch clone at commit `bf64236`; not yet copied, released or committed.**

- Changed in the clone: `helper/mempalace` (`load_setting` reads only `.workbench/local/mempalace.json`; `default_wing` takes the last part of the real project
  path when it is a valid wing name; `project_setting` keeps its two values; `mine` says whether the wing came from the file or from the folder name),
  `tests/test_mempalace_owner.py` (the `Setting`, `Wing` and `Directory` tests moved to the new path; the palace-only test now expects the default wing; a
  new class `Location` with 12 tests) and `tests/test_mempalace_run.py` (one expected argument list now carries `--wing project`). Changed in the live
  tree: `docs/specs/mempalace.md` ("First use in a project", "Palace location", the behaviour list).
- Verification as run: before the helper change the new and updated tests failed (23 failures and 5 errors in `test_mempalace_owner.py`); after it, and after the
  review fixes, `PYTHONPATH=. python3 -B -W error -m unittest discover -s packages/workbench/mempalace/tests -t packages/workbench/mempalace/tests`
  gave `Ran 186 tests ... OK` (174 before). `wb run code-work check` passed. Not run: the repository's own tests (no installer file changed), the real `mempalace`.
- Review: the `reviewer` agent, one exchange. No blocking finding. Applied: `test_a_palace_elsewhere_does_not_get_in_the_way` still wrote the old path and so
  passed without testing anything; it now writes the new path and asserts that `--palace` reaches the program. Applied: the `Wing` docstring named the old path.
  Applied: the spec now says the default wing is taken from the real path, so a folder reached through a link is named by its target. Deferred, not in this
  plan's scope: `docs/specs/knowledge-tools.md` line 123 still says the program's own setting is `.workbench/mempalace.json`; `docs/development.md` line 242 is
  Increment E's. Not checked by the reviewer: it could not run the tests, and did not read `_descend_present` or `module.json`.
- A finding of my own: the old `Directory` palace-overlap test planted its palace through the old path and would have stopped testing the overlap refusal
  once the helper changed; it was moved to the new path and still refuses.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/pc_install_files.py`,
  which writes three files only if their hashes are those recorded), the release approvals, the removal of the tracked `.workbench/mempalace.json`
  and the acknowledgement. Until the copy and release, `.workbench/mempalace.json` stays and is read by the installed (old) helper.

**Increment A was committed as `7c8a241`** (the owner copied and released it; the upgrade and the removal of the tracked `.workbench/mempalace.json` are still the owner's steps).

**Increment B (2026-11-05), done in a scratch clone at commit `7c8a241`; not yet copied, released or committed.**

- Changed in the clone: `helper/mempalace` (`NOT_SET_UP`, the message of `query_program` when no trusted program is found; `search` looks for the program before the
  cached model), `harness/neutral/skills/recall-memory/SKILL.md` (the skip rule), `tests/test_mempalace_run.py` (a class `Absent`, 7 tests) and
  `tests/test_mempalace_guidance.py` (one test that pins the quoted words in the skill and the helper). Changed in the live tree: `docs/specs/mempalace.md` (the line
  about a missing program). `run_owner` is unchanged on purpose: the owner's `mine` keeps "mempalace was not found in a trusted PATH entry …", since a skipped
  search is not what it does. The plan's affected-areas list names `run_owner`; this is why it was read and left alone.
- Verification as run: before the change the two skip-message tests and the guidance test failed for the right reason; after it,
  `PYTHONPATH=. python3 -B -W error -m unittest discover -s packages/workbench/mempalace/tests -t packages/workbench/mempalace/tests` gave `Ran 194 tests ... OK`
  (186 before). `wb run code-work check` passed. Not run: the repository's own tests (no installer file changed), the real `mempalace`.
- Review: the `reviewer` agent, two exchanges (cap 6). First read: one blocking finding, applied. `search` refused with "the embedding model is not cached" before it
  looked for the program, so a clone with neither the program nor the model (the usual case for a developer who does not use the palace) was still told to report a
  refusal; my tests missed it because their setup always creates the model files. Fixed by looking for the program first, with a test that removes both. Applied:
  `test_the_owners_mine_keeps_its_own_words` ran without a terminal and so passed whatever `run_owner` said (it now uses a terminal and asserts the old words);
  `test_a_program_in_an_untrusted_place…` planted no program (it now plants a working fake inside the project and on a relative entry and asserts it is never run).
  Second read of the fix: no blocking finding.
- Open for the owner, not decided by this increment: a program that exists but sits in an untrusted `PATH` entry (inside the repository, on a relative entry, behind a
  link) gets the same "not set up on this machine, so the search is skipped" message, so the agent goes on silently and the owner is never told the program was
  refused for being untrusted. The bracketed words still say so, and `wb run mempalace status` from a terminal shows them. Giving that case its own, reportable wording
  would need the helper to look in untrusted entries to tell the two apart, which it does not do today. Recommendation: leave it.
- Not checked by the reviewers: any test run (they only read), the real program, the repository's own tests.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/pcb_install_files.py`,
  four files, only if their hashes are those recorded), the release approvals, and, after the commit, `wb upgrade` and `wb rerender` (the skill is installed under
  `.claude/skills/`; the installed copy still has the old rule until then).

**Increment B was committed as `8cc697b`** (copied and released by the owner).

**Increment C (2026-11-05), done in a scratch clone at commit `8cc697b`; not yet copied, released or committed.**

- Changed in the clone (seven files): `helper/mempalace` (no `init` argument, flag table, usage, branch or `--no-llm`; the terminal refusal now reads "mine is the owner's
  command and runs only from a terminal"; `owner()` is `mine` only), `module.json` (`arguments`: `status`, `search`, `mine`; `owner`: `mine`),
  `harness/neutral/skills/recall-memory/SKILL.md` ("Never run `mine`, and never use the program directly"), and four test files. In `test_mempalace_owner.py` the old `Init`
  class is gone: three of its tests that were not about `init` moved to `Mine` (relative directory, terminal handed on, exit code), the others were `init`-only or
  duplicated `Mine`; every test that used `init` as a vehicle for a folder rule now uses `mine`; a new class `NoInit` (3 tests) pins that `init` is refused with the usage
  line, that the helper's tables and source name no `init` and no `--no-llm`, and that no command starts the program with `init`. Changed in the live tree:
  `docs/specs/mempalace.md`, `docs/specs/command-permissions.md` (the deferred item) and `docs/development.md`; the dated evidence entries were left as history.
- Verification as run: before the helper change the 4 new tests failed; after it `PYTHONPATH=. python3 -B -W error -m unittest discover -s packages/workbench/mempalace/tests
  -t packages/workbench/mempalace/tests` gave `Ran 193 tests ... OK` (194 before), and in the clone `tests/test_owner_argument_run.py` (25), `test_rendering.py` (85),
  `test_settingscmd.py` (44) and `test_permissions_drift.py` (22) passed. `wb run code-work check` passed. Not run: the real `mempalace`.
- Review: the `reviewer` agent, one exchange. No blocking finding. It checked each removed or changed test and found no check lost, that `mine` keeps every folder rule and the wing
  default, and that the `NoInit` tests are not vacuous. Applied, all wording: the planted-config refusal stays as a precaution because `mine` reads the configuration it finds
  (my "for a hand-run program" was wrong: the helper's check cannot protect a program the owner starts directly); `init` also appends a block to a git repository's `.gitignore`
  (`cli/cmd_init.py`, `_ensure_mempalace_files_gitignored`, which I confirmed in the source), so the "two files" statements now say so; the claim about the program was narrowed to
  "from the program's command line"; the git sentence is in the present tense; the skill test uses `\binit\b`; the deferred-item sentence in `command-permissions.md` is plain.
  Not applied: the roadmap file still describes `init` at lines 180, 517 and 986 as what was planned and built; I read criterion 4 as covering tests, specs and the guide, and left the
  roadmap, which line 1006 already corrects. The reviewer ran nothing.
- A correction of my own: I first changed the helper comment and a test docstring to say `mine` runs git. I checked the program's source (`project_scanner`, the only module
  that runs git, is imported by `cli/cmd_init.py` and not by `mine`), found that wrong, and wrote what is true. The git settings stay for every command.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/pcc_install_files.py`,
  seven files, only if their hashes are those recorded), the release approvals, and after the commit `wb upgrade` and `wb rerender`: the rendered permission rules in
  `.claude/settings.local.json` still list `mempalace init` until the rerender, and the installed helper still has `init` until the upgrade.

**Increment C was committed as `835da71`** (copied and released by the owner), and the upgrade, the rerender and the removal of the tracked `.workbench/mempalace.json` as `cb2b6cf`.

**Increment D (2026-11-05), done in a scratch clone at commit `cb2b6cf`; not yet copied, released or committed.**

- Changed in the clone (seven files, one new): `helper/mempalace`; `module.json` (`arguments` gain `preview`; `levels`: `{"mine": ["ask"]}`; `preview`: `"preview"`); the skill; and the tests
  `test_mempalace_ask.py` (new, 40 tests in the classes `Preview`, `Run`, `Lock` and `Safeguard`), `test_mempalace_guidance.py`, `test_mempalace_module.py` (the declaration and a
  registry test) and `support_mempalace.py` (the fake program can print a different text for a dry run, write a file during a real run, sleep, leave a child, print much, and exit
  differently for a real run). Changed in the live tree: `docs/specs/mempalace.md`, `docs/specs/command-permissions.md`, `docs/development.md` and `tests/test_permissions_drift.py`.
- What the helper does now. `preview mine <dir> [--wing] [--mode] [--allow-project-root]` runs the program's dry run (captured, at most 1 MiB and 300 seconds) and prints, between recalled-data
  markers, the project, folder, wing, mode, palace (or the palaces the program may choose) and the dry run's lines with the file lines sorted and the `Device:` and `Palace:` lines dropped, then
  `digest: <32 hex>` last. It refuses when the embedding model is not cached. `mine <dir> --confirm --digest <digest>` runs with no terminal: it checks the program and the model, takes an
  exclusive non-blocking `flock` on `mempalace-helper.lock` in the palace's parent directory (`~/.mempalace` by default; made 0700 if missing, refused if a link, or if its own parent is missing),
  rebuilds the lines, compares the digest, and only then runs the program with its output going to files (no cap, no time limit), printing the cleaned last 64 K characters framed as data.
  The whole process group is stopped on a terminate signal. Without `--digest` the run needs a terminal as before and is handed the terminal, and also takes the lock. After a real mine one
  line on standard error names any of `mempalace.yaml`, `mempalace.yml`, `mempal.yaml`, `mempal.yml`, `entities.json` or `.gitignore` that the program created in the folder; nothing is deleted.
- Verification as run: the new tests failed before the helper change (37 failures); after it, with the review fixes, `PYTHONPATH=. python3 -B -W error -m unittest discover -s packages/workbench/mempalace/tests
  -t packages/workbench/mempalace/tests` gave `Ran 241 tests ... OK` (193 before), and in the clone, with the new documents, `tests/test_owner_argument_run.py` (25), `test_rendering.py` (85),
  `test_settingscmd.py` (44) and `test_permissions_drift.py` (22) passed. `wb run code-work check` passed. The helper was also run against the real `mempalace` 3.11.0 in a scratch home, project and
  palace with the network denied (`scratchpad/pcd_real.py`): the preview was the same on a second run, a stale digest was refused with nothing filed, a digest-bound `mine` filed 12 files with
  no terminal and left nothing in the folder, the lock file was made (0600, directory 0700) beside the program's own files, and a search found the notes. Not run: the whole repository suite,
  and the owner's live checks of criterion 8.
- Review: the `reviewer` agent, two exchanges (cap 6). First read: one blocking finding, applied. My spec sentence said the drawer count follows the text's length, "so most edits change"
  the digest; it follows how many pieces a file is cut into, so most small edits do not. The spec now says plainly that the digest does not bind contents. Applied, not blocking: the captured
  run stopped only the program's leader and not its process group (now `killpg`, with a test that sends the launcher's terminate signal to a forked helper and requires the program and a child
  it started to be gone); the preview's lines were unframed (now framed, with `digest:` last); with no palace in the setting the destination was not in the digest (the program's possible
  palaces now are); lines were cut before hashing (now only for display, with `...`); a failed dry run hid the program's messages (now shown); a refused run could make `~/.mempalace` on a
  machine that cannot mine (the program and the model are checked first); `search`'s rule that an agent never starts the 79 MB download now holds for the preview and a run with a digest;
  the registry has a test for the keys; a test that asserted only an exit code now asserts the digest message and no second run; the `rerender` half of a drift fixture could never fire and
  is gone. Second read of the fixes: no blocking finding; I closed two of its gaps (the cap on the program's own lines could be bypassed by lines that begin like the heading; a shortened
  line gave no sign). Not closed, documented: a terminate signal in the instant between starting the program and noting its process.
- Deviations from the plan, for the owner to judge. (1) The skill and `tests/test_permissions_drift.py` are not in this increment's affected-areas list. The permission-drift test, which the plan's
  verification names, failed because the skill said "Never run `mine`" while `mine` now offers `ask`, and the skill must give the ask flow (`wb settings`, the preview, `--digest`) for the test to pass;
  the skill now says so, its guidance tests were updated to match, and two fixtures that used `mine` as their example of a block-only key now use `fetch-overwrite`. (2) The plan says the helper's
  own terminal test goes for `mine`; it stays for a run without a digest (the launcher also requires the digest at `ask`), so a helper run by hand with no terminal and no digest is refused. (3) The
  helper's note said a first `mine` "writes $HOME/hallways.json"; in 3.11.0 `hallways.json` goes beside the palace and only when entity links are found (a scratch mine wrote none), so the note and the
  documents say so. (4) The preview and the digest route refuse an uncached model, which the plan did not say.
- Open for the owner, not decided by this increment. At `ask` an agent names the folder. The folder rules are those of the owner's terminal use: any existing directory with no link in its path that is
  not inside `.git` or `.workbench`, so a directory outside the project (the owner's notes folder is one) and `--mode convos` are reachable, and what is filed is searchable by the agent afterwards.
  The harness shows the owner the command line, which carries an opaque digest, and the preview only if the agent shows it. Restricting an agent's folder to the project, or `--mode convos` to the
  terminal, would close this and would also stop the owner's notes folder from being filed at `ask`. The plan asks whether to run a security review of D and E together; that is the owner's to ask for.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/pcd_install_files.py`, seven files, only if their
  hashes are those recorded), the release approvals, and after the commit `wb upgrade` and `wb rerender` (the rendered rules gain the key `wb run mempalace mine` at `ask` and `wb run mempalace preview`
  at `none`); to use it, setting the level of `wb run mempalace mine` to `ask` in the owner's settings, and the live checks of criterion 8.

**Increment D was committed as `ea53436`** (copied and released by the owner).

**Increment E (2026-11-05), done in a scratch clone at commit `ea53436`; not yet copied, released or committed.**

- Changed in the clone (eight files): `helper/mempalace` (`sync` and `preview sync`; `sync_wing`, `sync_tail`, `sync_lines`, `report_lines`, `dry_failure`; `owner()`, `preview()`,
  `owner_directory()` and `owner_terminal()` take the command; `NO_MODEL` per command), `module.json` (`arguments` gain `sync`; `owner`: `mine`, `sync`; `levels` gain `sync: ["ask"]`),
  `harness/neutral/skills/recall-memory/SKILL.md` (the `sync` flow), and five test files: a new `test_mempalace_sync.py` (27 tests: Preview, Run, Lock) and small updates to
  `test_mempalace_ask.py`, `test_mempalace_guidance.py`, `test_mempalace_module.py` and `test_mempalace_owner.py`. Changed in the live tree: `docs/specs/mempalace.md` (the `sync` section,
  the table, the Non-goals line, the acceptance criteria, the skill paragraph), `docs/specs/command-permissions.md` (two sentences) and `docs/development.md` (the owner-run row, the module
  paragraph, and the stale setting format of line 242, now `.workbench/local/mempalace.json`).
- Deviations from the plan's wording: the helper passes `--dry-run` explicitly for the preview (the plan says "no `--apply`"; both hold); `sync` takes no `--allow-project-root`, so the project root is
  refused for it; a folder that no longer exists cannot be named, so the drawers of a deleted folder are not pruned through the helper (documented); the model check applies to `sync` as to `mine`.
- Verification as run: before the helper change all 26 new tests failed; after it `python3 -B -m unittest discover -s packages/workbench/mempalace/tests -p 'test_mempalace_*.py'` in the clone
  gave 267 tests with one failure, a pinned set of owner commands in `test_mempalace_owner.py`, which I updated, and that file (75) then passed; the review added one test (27 in the new file,
  which pass); `tests.test_owner_argument_run`, `test_rendering`, `test_settingscmd` and `test_permissions_drift` (176) pass in the clone. A scratch run against the real `mempalace` 3.11.0
  (scratch home and palace, network denied): `mine` of six notes, two deleted, `preview sync` showed Missing 4 and the two sources with a digest and was the same twice; a wrong digest and
  `--wing other` were refused; the digest run removed 4 drawers and 2 closets and a later search found only the remaining notes; a second preview showed Missing 0. Not run: `wb run code-work check`
  (until the files are in the live tree).
- Review: the `reviewer` agent, one exchange. No blocking finding. Applied: the Non-goals line in the spec still said that `sync` and filing were not wrapped; the skill said the wing was the
  setting's only (it is the setting's or the project folder's name); a test said "says nothing" and did not check it; the folder rules were tested for the run with the project root only (now also a link, a
  planted configuration, `.git` and a palace overlap); no test pinned the refusal when no wing exists, which is the property that keeps the program from working on every wing (added); the spec now says
  that the lock does not exclude a change made between the digest check and `--apply`, and that a tie in the program's top five could refuse a run (it fails safe). The reviewer ran nothing.
- What the digest does not cover: the complete list of sources removed (the program prints the counts and its top five) and the files' contents. The removal is not undone by the helper.
- Open for the owner: whether to run a security review of D and E together (an agent can now start a write and a removal at `ask`); the folder and `--mode convos` question under D.
- Left for the owner: the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/pce_install_files.py`, eight files, only if their
  hashes are those recorded), the release approvals, and after the commit the installer's upgrade and rerender steps (the rendered rules gain the key `wb run mempalace sync` at `ask`); to use it,
  setting the level of `wb run mempalace sync` to `ask`.

**Increment E was committed as `28e1d1a`** (copied and released by the owner), and its install-state files as `a2d56b8`. The security review of D and E was run on 2026-11-06 at the owner's request (a
scratch clone, a fake program, a scratch home); its findings are the work of increment F, and the plan with F was approved and committed as `21071c7`.

**Increment F (2026-11-06), done in a scratch clone at commit `21071c7`; not yet copied, released or committed.**

- Findings closed. (1) Medium: the folder rules compared strings, so `.GIT`, `.WorkBench/local`, the project root and its parent, and the palace, a folder in it and a folder holding it, in another
  case, passed on macOS and could be mined or synced at `ask`. The rules now ask the file system whether two paths are the same place (`within`, `in_guarded_name`), and compare folded (NFC,
  case-folded) spellings only for a boundary that does not exist yet. (2) Low: after the digest check the folder is examined again just before the program starts (`ready()`: the same rules, the same
  device and inode), and a swap is refused with "nothing was filed" or "removed". The race between that check and the program opening the path remains, as the spec says. (3) Low: the program
  inherits the lock descriptor (`pass_fds`), so a helper killed with `SIGKILL` no longer frees the lock while the program runs.
- Changed in the clone (three files): `helper/mempalace`, `tests/test_mempalace_ask.py` (the test that pinned "a killed run frees the lock and the program does not hold it" now expects the lock held
  while the program lives and free once it ends; this reverses a choice made in D), and a new `tests/test_mempalace_spelling.py` (17 tests: Spelling, Places, Recheck). Changed in the live tree:
  `docs/specs/mempalace.md` (the folder rules compare places, the re-check and what remains of the race, the lock and a killed helper, and that a nested `.git` or `.workbench` counts).
- Verification as run: before the helper change 11 of the first 14 new tests and the changed ask test failed; after it `python3 -B -m unittest discover -s packages/workbench/mempalace/tests -p
  'test_mempalace_*.py'` in the clone gave 282 tests, all passing, and the spelling file (17 with the three `Places` tests the review asked for) and `tests/test_docs*.py` (15) pass. A scratch run against
  the real `mempalace` 3.11.0 (scratch home and palace, network denied): `mine`, `preview sync`, a wrong digest and `--wing other` refused, a digest `sync` that removed 4 drawers and 2 closets, and
  `preview mine .GIT` refused. Not run: `wb run code-work check` (until the files are in the live tree), the four repository tests (the declaration and the keys do not change), a case-sensitive
  volume (the spelling tests there only pass; the `Places` tests exercise the comparison on any volume).
- Review: the `reviewer` agent, one exchange. No blocking finding. Applied: the spec did not say that a nested `.git` or `.workbench` is now refused, and a case-sensitive `.Git` too; the spec claimed that
  what the program starts does not hold the lock, which was not checked (now: not checked, and a held lock only refuses a later run); three tests of the comparison that do not depend on the volume.
  Not applied: a SIGKILL test for the terminal run (the code passes the lock the same way). The reviewer ran nothing.
- Behaviour change to know: a run now refuses a `.git` or `.workbench` directory anywhere under the project root, not only the root's own.
- Left for the owner: whether the security reviewer looks at the fix (a fix is new attack surface); the copy (`python3 -I -B /private/tmp/claude-501/-Users-rziegler-projects-project-workbench/123b16b0-cb65-4586-88ec-122e23f59d31/scratchpad/pcf_install_files.py`,
  three files, only if their hashes are those recorded), the release approvals, and after the commit `wb upgrade` and `wb rerender` (the installed helper changes; no new keys).
