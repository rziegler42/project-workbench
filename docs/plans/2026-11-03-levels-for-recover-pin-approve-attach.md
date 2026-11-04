# Levels for recover, acknowledge, pin, approve and attach

Status: Completed
Created: 2026-11-03
Candidate: none (the closest, `workbench-v1#checkpoint-levels-beyond-block`, leaves the owner-run installer commands out of its boundary; this plan takes increment C of `2026-11-02-permission-levels-for-every-command`, which stopped at its step 4 because it did not fit one reviewable commit and was deferred there, on the owner's direction of 2026-11-03)
Specs: command-permissions, installer-interface, trust-and-approval

## Goal

`wb recover`, the acknowledge tiers, `wb pin`, `wb approve` and `wb attach` each offer `ask`, bound to the digest of a read-only preview,
or the spec records the accepted decision that keeps one without it. Nothing else changes: shipped defaults, the compiled floor and the
personal `floor` list stay as they are.

## Scope

In:

- `ask` for `wb recover` and the acknowledge tiers, whose read-only examinations and digests exist;
- `ask` for `wb pin` and `wb approve`, with a `wb preview` entry for each (for `approve`, one that verifies the package and records nothing);
- `ask` for `wb attach`, with a preview of what it would write and the reading of the owner's own settings that the accepted record
  `2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest` names for it;
- an accepted record that keeps `acknowledge-second-tier` without `ask`, if it still governs no command when that increment runs;
- the specs and `wb doctor` as these changes make them false.

## Non-goals

- `wb rerender`, `delegated` for any key and module arguments: the other plans of the split.
- Changing the accepted record's rules for reading a level; this plan follows them.
- A shipped default, the compiled floor and who may approve a plan.

## Assumptions and constraints

- The rules are those of the accepted record `2026-11-03-installer-commands-read-their-level-and-take-an-ask-digest`: the command reads
  the level by the route of its kind (verified only and failing closed where it has a terminal test); the preview prints
  `digest: <32 hex>`; the run takes `--digest`, refuses a missing, malformed, repeated or stale one, and compares it before anything
  is written. The digest is per command: it binds what that command's preview shows and decides, and leaves out what a run generates
  for itself. It is not the install plan's digest, which `recover`, `acknowledge`, `pin`, `approve` and `attach` do not have. Each
  increment therefore lists, before it builds, the preview inputs its digest binds, the values it excludes and why, and where the run
  rechecks (inside the command's own lock where it has one). Increment B of the predecessor (7e4512f) is the worked example; how it
  fixes the generated values is not copied here, and a difference between it and the record is for the record's owner to settle.
- Every preview is read-only and is tested to change when the content it binds changes, and to be refused when stale.
- **Shared test matrix.** For every command that gains `ask`, its tests cover each of: a run with no digest; a malformed digest; a
  digest given twice; a stale digest; a `--digest` at a terminal (refused); a `--digest` at `none` (refused, saying a digest needs the
  level `ask`); and a valid digest with nothing to change (says so, writes nothing and logs nothing); and that the attempt and the
  outcome of a run at `ask` are logged.
- Each preview adds an agent-safe key to the registry, the corpus and `wb settings`; the drift test must pass in the same commit.
- An increment that changes what a command offers updates the lines of the specs it makes false in the same commit.
- Any change to what a key offers changes a rendered rule; the owner runs `wb rerender` in a terminal afterwards, and `wb doctor` says
  when it is due.
- Each increment depends only on the committed predecessor B (the registry, `levelrun.route_ask`, the digest refusal and the preview
  parser) and none on another increment here, so the owner may drop any of them and name it under Deferred work. Completion criteria
  apply to the increments kept. They run in the order A, B, C because the cheapest comes first, not because one needs another.
- Edits to `workbench/*.py` are made atomically so the installer stays importable.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. If A is kept: `wb recover` and each acknowledge tier that governs a command offer `ask` (a tier that governs none is decided in C); a run without a digest, or with a stale one, is refused; the attempt
   and the outcome are logged.
2. If B is kept: `wb pin` and `wb approve` offer `ask` on the same terms.
3. If C is kept: `wb attach` offers `ask` on the same terms, and `acknowledge-second-tier` is either given `ask` or kept without it by
   an accepted record that the spec names.
4. Each of these commands, when set to `ask`, passes the drift test and shows in `wb settings` and `wb doctor`.
5. No setting an owner can write reads other than as written without `wb doctor` saying so.

## Increments

### Increment A — `ask` for recover and the acknowledge tiers

**Outcome:** `wb recover` and the acknowledge tiers that govern a command offer `ask`, bound to the digest of a `wb preview` entry.
**Dependencies:** the committed B of the plan `2026-11-02-permission-levels-for-every-command`.
**Affected areas:** the registry (`levels.py`), `recover.py`, `acknowledge.py`, `preview.py`, `cli.py`, `levelrun.py`, the parser in
`sources.py`, `tests/test_ack_recover_levels.py`, `tests/test_levels.py`, `tests/test_permissions_drift.py`; and, in the same
commit, the lines of `docs/specs/command-permissions.md`, `docs/specs/installer-interface.md`, `docs/specs/trust-and-approval.md` and
`docs/development.md` that this makes false.
**Steps:**
1. Read `recover.examine`, `acknowledge.examine`, their typed confirmation and the route of B (`levelrun.route_ask`). List the inputs
   each digest binds, what it excludes and where the run rechecks.
2. Write the tests first: the key offers `ask`; the shared test matrix; the digest changes when the examined content changes.
3. Build the `wb preview recover` and `wb preview acknowledge` entries on the existing examinations, the `--digest` option and the check.
4. Update the specs and the registry facts in the same commit. If this grows beyond one reviewable commit, stop and report.
**Verification:** the tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-levels-for-recover-pin-approve-attach#A`.

### Increment B — `ask` for pin and approve

**Outcome:** `wb pin` and `wb approve` offer `ask`, bound to the digest of a `wb preview` entry that records nothing.
**Dependencies:** the committed B of the plan `2026-11-02-permission-levels-for-every-command`.
**Affected areas:** the registry, `pins.py`, `pinplan.py`, `approve.py`, `preview.py`, `cli.py`, `levelrun.py`, the parser,
`tests/test_approve_pin_levels.py`, `tests/test_levels.py`, `tests/test_permissions_drift.py`; the same four documents as A.
**Steps:**
1. Read what `pin` shows (path, size, sha256) and what `approve` verifies and confirms. List the inputs each digest binds, what it
   excludes and where the run rechecks.
2. Write the tests first: the shared test matrix, including that the `approve` preview verifies the package and records no approval, and that a changed package
   or helper changes the digest.
3. Build the previews, the `--digest` option and the check as in A.
4. Update the specs and the registry facts in the same commit. If this grows beyond one reviewable commit, stop and report.
**Verification:** the tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-levels-for-recover-pin-approve-attach#B`.

### Increment C — `ask` for attach, and a record for the second acknowledge tier

**Outcome:** `wb attach` offers `ask`, bound to the digest of a preview of what it would write; `acknowledge-second-tier` is decided.
**Dependencies:** the committed B of the plan `2026-11-02-permission-levels-for-every-command`.
**Affected areas:** the registry, `attach.py`, `preview.py`, `cli.py` (`_owner_reading`, parameterised by key), `levelrun.py`, the parser,
`tests/test_levels.py`, `tests/test_permissions_drift.py` and a new attach test file; `docs/decisions/` (one record); the same four
documents as A.
**Steps:**
1. Read `attach.py` and the accepted record's first decision, second bullet (`attach` has no terminal test and also reads the owner's own
   setting).
2. List the inputs the `attach` digest binds, what it excludes and where the run rechecks. Draft a `Proposed` record (the
   `draft-decision` skill) that keeps `acknowledge-second-tier` without `ask` while it governs no command, or give it `ask` if it now
   governs one. Stop for the owner's acceptance at the `accept-decision` checkpoint before the spec
   cites it.
3. Write the tests first: the shared test matrix, including that the owner's own setting alone does not grant a run that the verified rendering would refuse
   where the record says it must not, then build the preview, the option and the check.
4. Update the specs and the registry facts in the same commit. If this grows beyond one reviewable commit, stop and report.
**Verification:** the tests named above, the drift test and the document check.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-levels-for-recover-pin-approve-attach#C`.

## Verification for the plan as a whole

Each increment's recorded verification stands unless a later increment changed its inputs. At the end rerun only `wb doctor`, the
document check, and the drift test and gate corpus (`tests/test_permissions_drift.py`, `tests/test_gate_corpus.py`). The full suite runs
only if the owner decides after the author states what could break outside the tested area.

## Risks and sensitive actions

- **A digest that does not bind the preview's content makes `ask` a rubber stamp.** Each preview is tested to change with its content and
  to be recomputed inside the command's lock.
- **`approve` and `pin` record trust.** Their preview must verify and show, and write nothing; a test shows no record exists after it.
- **`attach` reads the owner's own settings, not only a rendering.** The accepted record limits this to `attach`; a test covers a
  setting that the rendering would refuse.
- **Relaxing a level lets the agent run a command.** That is the owner's chosen risk; defaults stay `block` and the owner sets `ask`.
- **The installer must stay importable.** Edits to `workbench/*.py` are atomic.
- A security review is offered after each increment that touches a boundary; it runs only when the owner asks.

## Review record

- **Reviewer:** the project's review engine, model `gpt-5.6-terra`, through `wb run review-engine review-plan`.
- **Rounds:** 2 of the bound of 3 (stopped at 2 on the owner's agreement). Not converged: each round found two major points, and the
  second round's fixes were reviewed in no further round.
- **Applied (4):** the digest rules follow the accepted record per command, and each increment lists what its digest binds, excludes and
  rechecks (R1-F1); B and C depend only on the committed predecessor B, so each of the three can be dropped alone (R1-F2); criterion 1
  covers only acknowledge tiers that govern a command, the other being decided in C (R2-F1); a shared test matrix of every digest case
  is required for each command that gains `ask` (R2-F2).
- **Rejected:** none.
- **Left for the owner:** another round (the engine allows a third), or approval as it stands. One point is not this plan's to settle:
  the accepted record says the `ask` digest leaves out the seed and time, while increment B of the predecessor fixed them; a dated
  clarification note on that record, which needs the owner's approval, would remove the difference.

## Deferred work

- `wb rerender` and the other plans of the split: `2026-11-02-permission-levels-for-every-command` (D, E, F),
  `2026-11-03-module-conformance-levels-and-hooks`.

## Result

### Increment A — `ask` for recover and the acknowledge tiers (2026-11-04)

- **Done (uncommitted until the owner says):** `wb recover` and the checkpoint `acknowledge-first-tier` (the key of `wb acknowledge`) offer
  `block`, `ask` and `none`. Two read-only previews, `wb preview recover` and `wb preview acknowledge`, print the examination the typed flow
  shows, a note that its own 64-character digest is the one a terminal run types, then `digest: <32 hex>`, which is
  `kitdigest.of(["wb <command>", <the examination's digest>])`, and `preview only: nothing was written`. A run without a terminal at `ask`
  takes it as `--digest`; `levelrun.route_ask` and `levelrun.digest_refusal` (increment B of the predecessor) read the level and refuse a
  missing, malformed, repeated or stale digest; the command compares it after its examination and before it prints or writes anything, also
  when there is nothing to change (`recover` binds the absence of a marker, `nothing_digest`). The project check (acknowledge: the project
  listed; recover: a marker that names a project) comes before the comparison. The attempt is logged with level `ask` and evidence
  `digest:<32>`. The second acknowledge tier, `attach`, `approve` and `pin` are unchanged.
- **Digest inputs** (listed before building, as the plan requires): acknowledge binds the target identity, project, workbench version,
  manifest hash, baselines before and after, each difference, the pins file hash and each pin that moves; it leaves out the time a moved pin
  records, which no field holds. Recover binds the target identity, the marker's fingerprint, the outcome, the files and store states, every
  item and every removal in order. The rechecks are the two examinations the command already makes (neither has a lock). Nothing a run draws is
  in a digest, so no fixed seed or time is needed.
- **Files:** `workbench/levels.py`, `acknowledge.py`, `recover.py`, `preview.py` (`EXAMINATION_NOTE`), `cli.py`; new `tests/test_ack_recover_ask.py`
  (the shared matrix for both commands, 42 tests); updated `test_ack_recover_levels`, `test_levels`, `test_permissions_drift`, `test_settings`,
  `test_settingscmd`; specs `command-permissions.md` (new section "`recover` and `acknowledge` at `ask`" and its neighbours),
  `installer-interface.md`, `trust-and-approval.md`, `code-work.md`, and `docs/development.md`.
- **Verification as run:** the new tests failed before the code (42 of 42), then passed; with the digest comparison disabled exactly the six
  stale-digest tests failed. Then, all passing: `test_ack_recover_ask`, `test_ack_recover_levels`, `test_levels`, `test_levels_facts`,
  `test_levelrun`, `test_permissions_drift`, `test_preview`, `test_doctor`, `test_rendering`, `test_gate_corpus`, `test_command_gate`,
  `test_approve_pin_levels`, `test_harness_lock`, `test_refresh`, `test_rerender`, `test_release_ask`, `test_upgrade`, and by discovery
  `test_settings`, `test_settingscmd`, `test_cli`, `test_firstparty`. `wb check` and `wb doctor` found no problems; the plan check found none.
  The full suite was not run.
- **Review:** one `reviewer` round, no blocking finding. Two not-blocking findings were applied: `code-work.md` still said the first tier offers
  `none`; and the previews printed two `digest:` lines, so a note now says which one a run takes (test added). Not checked by the reviewer
  and not by me: a run against a real harness's rendered `ask` rule (the drift tests and the corpus pass); the preview's use of
  `_open_store`, which seeds settings as every preview does.
- **A slip, recorded:** an edit script left `workbench/recover.py` with a syntax error, which locked every tool through the guard hooks until
  the owner repaired it with one command; no tracked change was lost.
- **Consequences for the owner:** the profile `balanced` now sets `wb recover` to `ask`, and `trusting` also sets `acknowledge-first-tier`
  wherever a module declares it; a `wb rerender` in a terminal is due for an owner who uses either. At `ask` an owner who confirms a digest lets
  the agent accept changes to instruction-bearing and executable files and move pins (written in the spec).
- **Left for the owner:** the verdict, and the word to commit.
- **Afterwards:** committed as 93faec7 with a follow-up 488efc1 (the spec's profile lines and the forged-marker limit, after the security
  review of A, which found no Critical, High or Medium issue).

### Increment B — `ask` for pin and approve (2026-11-04)

- **Done (uncommitted until the owner says):** `wb pin` and `wb approve` offer `block`, `ask` and `none`. Two read-only previews,
  `wb preview pin <project-id> <name> <helper> --root <dir> [--kit N]` and `wb preview approve <package> [--module <name>]`, print what the
  terminal command shows, the note that its own digest is the one a terminal run types, then `digest: <32 hex>` and `preview only: nothing
  was written`. A run without a terminal at `ask` takes it as `--digest` (`argparse` `append`; a repeated or malformed one is a usage error,
  exit 2). The new module `workbench/askdigest.py` holds the ask-digest helpers because `preview` imports `installplan`, which imports `pins`;
  `preview` keeps its names as aliases.
- **Digest inputs** (listed before building, as the plan requires). Pin: the project id, the name, the path in the project, the helper's
  SHA-256 and size, the kit, and the pin it would replace (path, hash, kit, declaration, time); the time the new pin records and the git
  identity are left out. Approve: the kind and the module, the name, declaration hash and tree hash of the package and every module, and
  the SHA-256 of the request text (which holds the package's absolute path); whether a record is already on file is left out. Rechecks: the
  helper is read again and the package verified again after the comparison, as at a terminal.
- **Decisions this increment made, for the owner to veto** (none needed a new record, as each follows the accepted record's rules):
  (1) a pin or an approval written at `ask` has `via` `ask`, so `pins.VIAS` and `approvals.VIAS` now include it (an older copy of the
  installer refuses such a record and a pins file it cannot read fails closed); (2) **`wb approve --source` is refused at `ask`** and
  `preview approve` takes no `--source`, because a preview must not download; the owner approves a downloaded package at a terminal or gives
  the directory it was fetched to; (3) a pin that already holds the same path, hash and kit says `already pinned` and writes and logs
  nothing, at `ask` only, and so leaves an installer-made declaration alone; (4) the approve digest does not bind whether a record is on
  file, so after an approval the same digest still matches and the run says `already approved`.
- **Files:** `workbench/askdigest.py` (new), `pins.py`, `approve.py`, `approvals.py`, `levels.py`, `cli.py`, `preview.py`; new
  `tests/test_pin_approve_ask.py` (the shared matrix, generalised in `test_ack_recover_ask.py` with `target()`, `NOTHING` and
  `PROJECT_CHECK`; 47 tests, one skipped by design: approve is machine-wide); updated `test_levels`, `test_levels_facts`, `test_settings`,
  `test_settingscmd`, `test_approvals`, `test_pins` (an `ask` via was the example of an invalid via), `test_permissions_drift`,
  `test_approve_levels`; specs `command-permissions.md` (new section "`approve` and `pin` at `ask`"), `installer-interface.md`,
  `trust-and-approval.md`, `docs/development.md`.
- **A miss of increment A, found here:** `test_approve_levels.OfferedLevels.test_no_other_owner_run_key_offers_ask_or_none` still said
  `wb recover` and the first acknowledge tier offer `none` only. Increment A's verification did not include that module, so A's commit left it
  failing. It is fixed in this increment's commit.
- **Verification as run:** the new tests failed before the code (46 of 47, one skipped); with the digest comparison disabled 8 of them fail.
  After the code, all of these pass: `test_pin_approve_ask`, `test_ack_recover_ask`, `test_approve_pin_levels`, `test_approve_levels`,
  `test_levels`, `test_levels_facts`, `test_permissions_drift`, `test_doctor`, `test_rendering`, `test_gate_corpus`, `test_command_gate`,
  `test_ack_recover_levels`, `test_levelrun`, `test_preview`, `test_install_levels`, `test_upgrade_levels`, `test_release_ask`, and by
  discovery `test_settings`, `test_settingscmd`, `test_cli`, `test_approvals`, `test_pins`, `test_approve`, `test_launch`, `test_install`,
  `test_attach`. `wb check` and `wb doctor` found no problems. The full suite was not run.
- **Review:** one `reviewer` exchange, no blocking finding; applied: a stale line in `trust-and-approval.md` (a pin's `via`), the spec says a
  declaration-bearing pin is left as it is at `ask`, that an older copy refuses `via: ask`, and that the approve digest names the absolute path.
  Not checked by the reviewer: the real harness behaviour of the rendered `ask` rules, and `_open_store`/`install_wrapper` beyond the launcher
  refresh every preview does.
- **Consequences for the owner:** `trusting` now also sets `wb approve` and `wb pin` to `ask` (they are `governs` keys); `balanced` does
  not. A `wb rerender` in a terminal is due for an owner who uses `trusting`. At `ask` an owner who confirms a digest lets the agent make
  a package trusted or a helper runnable; approve is machine-wide.
- **Left for the owner:** the verdict, the veto of decision (2) if `--source` should have a preview, and the word to commit.
- **Afterwards:** committed as 230fafa (22 files; I had said 25).

### Increment C — `ask` for attach, and a record for the second acknowledge tier (2026-11-04)

- **Done (uncommitted until the owner says):** `wb attach` offers `block`, `ask` and `none`. `wb preview attach [<target>|--dir] --harness
  <package>/<module> [--package <source> [--ref <ref>]] ...` makes the same `prepare` the run makes, prints what would be written (files
  created and kept, exclude lines, the local manifest, the settings file and what it changes, reports and notes) and `digest: <32 hex>`;
  it prints nothing for a clone that cannot be attached. `attach` has no terminal test, so, as the accepted record says, it reads the
  verified level (`levelrun.unattended`) and, when that is neither ask nor none (a project with no rendering record reads `block`),
  the owner's own setting in the guarded store: the new `cli._owner_level` (`_owner_reading` is now a thin wrapper for
  `release-approvals`, unchanged in effect). `ask`, a risk profile that sets it, or unreadable settings require the digest; the owner's
  `none` takes no digest and goes on unlogged. The digest is compared after `prepare`, **before the attempt is logged and before anything
  is written**; the write is then wrapped by `apply_logged`. A clone that already records a harness is refused by `prepare` at every
  level, so for `attach` the matrix's "nothing to change" is a refusal and logs nothing.
- **Digest inputs** (listed before building, as the plan requires): the target (path, device, inode), the project, the harness and its
  version, each created and each kept file with the hash and mode of its bytes, the exclude lines, the local manifest to write, the
  settings file, the rendering record as it would be written now (with the live hash of the shared settings file), and the reports,
  warnings and notes. Nothing is drawn by a run. Rechecks: `apply`'s `target.recheck()` (after the rendering record is written, as at a
  terminal) and the shared settings file's hash, read again when the record is written.
- **The record for the second acknowledge tier:** `docs/decisions/2026-11-04-the-second-acknowledge-tier-offers-no-ask.md`, written
  `Proposed`, previewed (digest `7e93a18f4fe6a57ca70ecf4d67ae262a`), and **accepted by the owner on 2026-11-04** at the `accept-decision`
  checkpoint (level `ask`: the owner confirmed `wb run groundwork accept ... --digest 7e93a18f...`). The spec now cites it.
- **Files:** `workbench/attach.py`, `cli.py`, `levels.py`, `levelrun.py` (docstrings); new `tests/test_attach_ask.py` (23 tests) and the
  decision record; updated `test_levels`, `test_levels_facts`, `test_doctor`, `test_release_ask`, `test_ack_recover_levels`,
  `test_approve_levels`, `test_permissions_drift`, `test_settings`, `test_settingscmd` (each had used `wb attach` as its example of a key
  that offers no `ask`); specs `command-permissions.md` (new section "`attach` at `ask`"), `installer-interface.md`, `development.md`.
  `cli._unattended_call` (no caller left) was removed.
- **Verification as run:** the new tests failed before the code (20 of 22); with the digest comparison disabled the two stale-digest tests
  fail. After the code all of these pass: `test_attach_ask`, `test_pin_approve_ask`, `test_ack_recover_ask`, `test_approve_pin_levels`,
  `test_approve_levels`, `test_levels`, `test_levels_facts`, `test_permissions_drift`, `test_doctor`, `test_rendering`,
  `test_gate_corpus`, `test_command_gate`, `test_ack_recover_levels`, `test_levelrun`, `test_preview`, `test_install_levels`,
  `test_upgrade_levels`, `test_release_ask`, `test_rerender`, `test_refresh`, `test_harness_lock`, and by discovery `test_settings`,
  `test_settingscmd`, `test_cli`, `test_approvals`, `test_pins`, `test_approve`, `test_launch`, `test_install`, `test_attach`,
  `test_upgrade`. `wb check` and `wb doctor` found no problems. The full suite was not run.
- **Not covered by a test:** the verified-`ask` route for `attach` (the working directory's project rendered with `wb attach: ask`, and
  another clone as the target); it shares `levelrun.unattended` with `release-approvals`.
- **Review:** one `reviewer` exchange, no blocking finding and no route to the writes at `ask` without a matching digest. Applied: stale
  lines in `command-permissions.md` about `levelrun.optional` and `unattended`, docstrings in `levelrun.py` and `attach.py`, the line in
  `installer-interface.md`, the dead helper, a table row and a test for the owner's own `none` with no digest, and a sentence about the
  record being written before the recheck. The reviewer could not diff `_owner_reading` against HEAD; I did, and it is the same reading.
- **Consequences for the owner:** `balanced` and `trusting` now both set `wb attach` to `ask` (a `project` key that offers it), so a
  `wb rerender` in a terminal is due for an owner who uses either. At `ask` an owner who confirms a digest lets the agent render the
  harness's permissions into a clone. **Completion criterion 3 is met**: `attach` offers `ask` with a preview and a digest, and the
  second acknowledge tier is kept without it by the accepted record, which the spec names.
- **Left for the owner:** the verdict, and the word to commit.
