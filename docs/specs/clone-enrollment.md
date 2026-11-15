# Clone enrollment

Status: Draft. Written on 2026-11-15 from a conversation with the owner, for the roadmap candidate `workbench-v1#enrol-a-clone`. It describes a command that is not built. It is `Current` only when the owner says so, after it is built.

Each statement carries one of three marks, so that the owner can see what is theirs:

- **[agreed]** The owner said it, or approved it in a playback on 2026-11-15. It is the working position and it can still change.
- **[call]** The assistant's choice, made so the design is complete. The owner has not decided it.
- **[open]** Not decided. The builder asks the owner, or the owner decides when approving.

Terms are defined in `terms.md`. The commands this one sits beside are in `installer-interface.md`, the store and the baselines in `trust-and-approval.md` ("Acknowledgement"), and the per-clone files in `repository-boundary.md`.

## Scope

A command that makes a clone of an already installed project known on a machine that has never held it, so that the checks, `attach`, `upgrade`, `add` and `acknowledge` work on that clone and the project's helpers are pinned. [agreed]

The commands are `wb enroll` and a read-only `wb preview enroll`. [call] They are run through the `wb` launcher, never as `python3 -m workbench`, which would put the clone's own directory first on the module search path (`installer-interface.md`, the launcher rule). [call] The launcher is written by the first run of the workbench in the clone, which is the first step of the setup page `INSTALL.md`; `enroll` is a later step. [call]

## Non-goals

- Moving or copying a project to another path on one machine, or any use of an earlier project's baselines or pins (`repository-boundary.md` says such a project is treated as new). [agreed]
- Comparing the clone with the first machine's store, or with a remote. The basis of trust is the committed manifest's hashes and the digest the owner confirms. [agreed]
- Writing an approval, fetching a package, or attaching a harness. The command checks the approvals that exist (below) and writes none; `approve` and `attach` stay the existing commands, run before or after as each needs. [agreed]
- Copying the owner's personal settings, review profiles or bridge endpoints. They are per machine, and `INSTALL.md` says so. [call]
- Any change to what a baseline or a pin means, or to the file formats of the store. [agreed]
- A way to enroll a project that was never installed. `install` and `adopt` do that. [call]

## Assumptions and constraints

- Every command that acts on an installed project first requires that the guarded store hold `projects/<id>/baselines` and a `seen` record equal to the clone's resolved path; otherwise the project is "treated as new here" and the command refuses. `enroll` is the one exception: it is the command that makes the project known. Source: `acknowledgement.check_known`, called by `attach`, `upgrade` and `acknowledge`; `trust-and-approval.md`, "What a command checks before it acts on a project".
- Today only `install` and `adopt` write the baselines, the `seen` record and the pins (`installplan.py`, the `store_writes` and `pinplan` steps), and `adopt` refuses an existing project ("use wb upgrade or wb add"). So a clone of an installed project cannot be made known by any command. Evidence, 2026-11-15, at commit `459dde9`: on a fresh clone with a scratch `HOME`, `preview attach` refused with "this machine holds no acknowledgement baselines for the project; it is treated as new here"; on the owner's second machine, `preview acknowledge` refused the same way and `preview adopt --dir . --package packages/workbench --select <the ten modules of the manifest>` refused with "the target is an existing project; use wb upgrade or wb add".
- The project's identity is the id derived from the manifest's seed (`manifest.project_id`), so the clone has the same id on every machine. The `seen` record holds an absolute path, so it differs between machines. Source: `acknowledgement.read_seen`, `check_known`.
- The baselines file is strict JSON, `{"baselines": {<path relative to the project root>: <sha256 hex of the bytes>}, "format": 1}`. Source: `trust-and-approval.md`, "Baselines file".
- An owner-run command is terminal-only unless its key offers `ask` or `none`; `wb rerender` offers `block` only. Source: `levels.py`, decision `2026-10-27-rerender-is-terminal-only`.
- A tracked document does not cite an untracked file. Source: decision `2026-10-19-tracked-pointer-rule`.

## Behavior

**Form.** `wb preview enroll [<target> | --dir <path>]` shows what would be written and a digest, and writes nothing. [call] `wb enroll [<target> | --dir <path>]` is owner-run: standard input and output must be terminals, the whole list and the digest are shown, and the owner types the first 12 characters of the digest. [agreed] Typed-ahead input is discarded, and anything else writes nothing; the 12 characters and the discarding follow `acknowledge`. [call]

**Level.** The key `wb enroll` is class `governs` and offers `block` only, so there is no `ask` or `none` and no run without a terminal, as for `wb rerender`. [call]

**Registration.** The key is added to the levels registry with `wb preview enroll` as its preview; the harness's deny rule for owner-run commands names it; the command gate's key words include it; and the command tables of `development.md`, `installer-interface.md` and `command-permissions.md` list it. [call]

**What it reads.** In the clone: the committed manifest, every file the manifest records, the names under `.workbench/` outside `local/` (to find a file the manifest does not record), and the top directory with its `.git` and manifest entries (for the target checks). In the guarded store: the project's `baselines`, `seen` and pins entries. [call] It runs no git and fetches nothing. [agreed]

**What it checks.** Before it shows anything:

1. The target is resolved and classified as every command does it (`installer-interface.md`, "Refused places" and the states table): a refused place is refused, and the target must be an existing project, a real directory with its own `.git` and a regular-file `.workbench/manifest.json`. Anything else is a refusal. [call]
2. The project has neither baselines nor a `seen` record for its id in the store. This is the one command that requires the project to be unknown on this machine; every other command requires it to be known. [agreed] If both entries exist, the project is known and the command refuses and names `acknowledge`. [agreed] If exactly one exists, or an entry is malformed, the command refuses, names the entry and writes nothing. [call] Both entries are created only after every check has passed. [call]
3. The manifest reads through the same strict reader the other commands use (`installed.read`), and every path it records passes the project's path rules (`repository-boundary.md`, `module-contract.md`). [call] Each recorded path lies where its owner may write: a module's own namespace under `.workbench/<package>/<module>/`, a path in that module's declared `writes`, a file the base supplies, `.workbench/.gitignore` or the manifest; never under `.workbench/local/`. An entry outside those places, a class other than the ones the installer writes, or a block whose slot its module does not declare is a refusal that names the entry, and nothing is written. [call] Every recorded path that exists is a regular file, never a link, a directory or another kind. [call]
4. Every file the manifest records as module-owned equals the hash the manifest records for it. A file that differs or is missing is a refusal that names its path. [agreed]
5. A file the manifest records as seeded, such as `AGENTS.md` or a `docs/*/README.md`, is the owner's to edit, so its bytes may differ from the hash the manifest records. It does not refuse. [agreed] The baseline is taken from the bytes now in the clone, and the preview lists the file as "differs from the manifest (seeded, yours)". [agreed] A seeded file that is missing is listed and given no baseline. [call]
6. A file under `.workbench/` outside `local/` that the manifest does not record is listed and refuses, as `acknowledge` treats an added file. [call]
7. A slot block the manifest records (class `slot block`, with the hash of its block text and the path of the file that holds it, such as a policy block in `AGENTS.md`) lives inside a seeded file. The command finds the block in the clone's file as the installer's block scanner does (`blocks.scan`) and compares the SHA-256 of its exact bytes, from the first byte of its BEGIN marker line through the last byte of its END marker line with their line endings, with the manifest's hash. That is the byte range `install` hashes (`installplan.py`, where the block is built from the two marker lines and the module's text). A block that matches is not listed. A block that differs or is missing does not refuse, because its file is the owner's to edit; the preview lists it as "block differs from the manifest (seeded file, yours)" with the file and the block's name. [call] The baseline of the containing file is the hash of the whole file as it is in the clone, as `install` records the bytes written, so a file with blocks gets one baseline whatever its blocks say. [call]
8. Every module the manifest records is approved on this machine: its declaration hash and its tree hash, as the manifest records them, match an approval record that `install` and `attach` accept (an owner's record in the guarded store, or a shipped release record of this repository; `trust-and-approval.md`, "Package and module approval"). A module with no such record is a refusal that names the module and says to run `approve`. The command reads these records and writes none. [agreed]

**What it writes.** In the guarded store, in one atomic step, for the project's id: `projects/<id>/baselines` (the hash of every file the manifest records, as checked above, and of `.workbench/manifest.json` itself, as `install` records it), `projects/<id>/seen` (the clone's resolved absolute path) and the pins. [agreed] It writes nothing in the project. [agreed] Besides the project's store directory it writes only the level log, with its attempt before the writes and its outcome after, as the other owner-run commands do. [call]

**The pins.** One pin for each command and each check of each module the manifest records, except a harness module, made as `pinplan.wanted` and `pinplan.changes` make them for an install: the name and the kit from the module's `module.json` as it is in the clone, which is module-owned and so already checked against the manifest; the path `.workbench/<package>/<module>/<helper>`; the SHA-256 of the helper, which equals the manifest's hash for it; the declaration hash the manifest records for the module; and `pinned_by` set to `workbench enroll`. [call] The preview lists each pin with those fields, and the digest covers them as `pinplan.fields` does. [call] A pin is made only for a module that passed check 8, so no helper of an unapproved module is pinned and none can run through the launcher on the strength of the clone alone. [agreed] The owner's digest then confirms the helper hashes and declaration hashes the preview lists, as for an install. [agreed] Whether the two together are enough is a question for the security review of the built command. [call]

**What it leaves to other commands.** After it, `wb check`, `wb doctor`, `acknowledge`, `upgrade` and `add` accept the clone. [agreed] The harness is attached by `attach`, which still needs each package approved on this machine. [agreed]

**The preview** shows: the project id and the path that would be recorded; each file with its hash and its class; each seeded file that differs; each pin it would make; and the digest. The digest covers the list, as `acknowledge`'s does, and the command re-reads the clone after the owner types it and refuses if the digest differs. [call]

**What stays open.** Whether the preview says, as a last line, that `attach` still needs each package approved on this machine. [open]

## Acceptance criteria

1. On a fresh clone with a scratch `HOME` and the commit of the day, after the first run of the workbench has written the guarded store and the launcher as every command's first run does (`installer-interface.md`), `preview enroll` lists the baselines, the `seen` path and the pins and writes no entry for the project in the store and nothing in the project.
2. `enroll` run from a terminal with the typed digest writes exactly the three store entries (the baselines, the first-seen record and the pins), the level log and nothing in the project; afterwards `wb check`, `wb doctor` and `preview acknowledge` run without the "treated as new" refusal, and `preview acknowledge` lists no difference for the manifest or for any other path of the clone.
3. It refuses, naming the entry, a manifest entry outside the places its owner may write (including one under `.workbench/local/`), an unknown class, and a block whose slot the module does not declare. It refuses, naming the path, a module-owned file whose hash differs from the manifest, a missing module-owned file, a link, a directory in place of a file, a file under `.workbench/` the manifest does not record, a refused place, and a directory that is not an existing project.
4. It does not refuse a seeded file that differs; the preview lists it and the baseline is the bytes in the clone.
5. It refuses, naming the module, a module with no approval record on this machine, writes no store entry in that case, and makes no pin for it.
6. It refuses a project the machine already knows and names `acknowledge`, and refuses, naming the entry and writing nothing, a project with only one of the two entries or a malformed one.
6a. A slot block that differs from the manifest does not refuse; the preview lists it with its file and name, and the baseline of its file is the hash of the whole file in the clone.
7. It refuses without two terminals, refuses a wrong or typed-ahead digest, and refuses when the clone changed between the preview and the answer.
8. `wb settings` prints the key `wb enroll` with `offers=` empty, and the command refuses to run with the key changed to any other level.
9. A security review of the built command finds no way for the files of a clone to be accepted without the owner's digest, no pin for an unapproved module, and no write in the store outside `projects/<id>/` and the level log.
10. `INSTALL.md` describes the command and the steps that follow it, and the owner has run them on a second machine.

## Governing decisions and references

- Decisions: `docs/decisions/2026-10-19-guarded-store.md`, `docs/decisions/2026-10-20-acknowledge-before-upgrade.md`, `docs/decisions/2026-10-22-installer-pins-declared-helpers.md`, `docs/decisions/2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest.md`, `docs/decisions/2026-10-27-rerender-is-terminal-only.md`, `docs/decisions/2026-10-19-tracked-pointer-rule.md`. A new decision record for the trust basis (the manifest's hashes plus the owner's digest, with no comparison against another machine) is written by the plan's first increment, as `Proposed`.
- Specs: `installer-interface.md`, `trust-and-approval.md`, `repository-boundary.md`, `command-permissions.md`.
- Roadmap: `workbench-v1#enrol-a-clone`. The candidate's id keeps the older spelling, because an id is never changed (`docs/roadmaps/README.md`); the command and this spec use "enroll".
