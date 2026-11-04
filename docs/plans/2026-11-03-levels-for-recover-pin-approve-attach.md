# Levels for recover, acknowledge, pin, approve and attach

Status: Proposed
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

- The method is that of increment B of `2026-11-02-permission-levels-for-every-command` (committed as 7e4512f): the command reads the
  verified level only and fails closed where it has a terminal test; the preview prints `digest: <32 hex>`; the run takes `--digest`;
  the digest is taken over the plan built with the fixed seed and time, and is recomputed inside the command's own lock.
- Every preview is read-only and is tested to change when the content it binds changes, and to be refused when stale.
- Each preview adds an agent-safe key to the registry, the corpus and `wb settings`; the drift test must pass in the same commit.
- An increment that changes what a command offers updates the lines of the specs it makes false in the same commit.
- Any change to what a key offers changes a rendered rule; the owner runs `wb rerender` in a terminal afterwards, and `wb doctor` says
  when it is due.
- The three increments are independent; the owner may drop any of them and name it under Deferred work. Completion criteria apply to the
  increments kept.
- Edits to `workbench/*.py` are made atomically so the installer stays importable.
- Testing is targeted; before any wider run the author states what could break outside the tested area.

## Completion criteria

1. If A is kept: `wb recover` and each acknowledge tier offer `ask`; a run without a digest, or with a stale one, is refused; the attempt
   and the outcome are logged.
2. If B is kept: `wb pin` and `wb approve` offer `ask` on the same terms.
3. If C is kept: `wb attach` offers `ask` on the same terms, and `acknowledge-second-tier` is either given `ask` or kept without it by
   an accepted record that the spec names.
4. Each of these commands, when set to `ask`, passes the drift test and shows in `wb settings` and `wb doctor`.
5. No setting an owner can write reads other than as written without `wb doctor` saying so.

## Increments

### Increment A — `ask` for recover and the acknowledge tiers

**Outcome:** `wb recover` and the acknowledge tiers that govern a command offer `ask`, bound to the digest of a `wb preview` entry.
**Dependencies:** none beyond the committed B of the plan `2026-11-02-permission-levels-for-every-command`.
**Affected areas:** the registry (`levels.py`), `recover.py`, `acknowledge.py`, `preview.py`, `cli.py`, `levelrun.py`, the parser in
`sources.py`, `tests/test_ack_recover_levels.py`, `tests/test_levels.py`, `tests/test_permissions_drift.py`; and, in the same
commit, the lines of `docs/specs/command-permissions.md`, `docs/specs/installer-interface.md`, `docs/specs/trust-and-approval.md` and
`docs/development.md` that this makes false.
**Steps:**
1. Read `recover.examine`, `acknowledge.examine`, their typed confirmation and the route of B (`levelrun.route_ask`).
2. Write the tests first: the key offers `ask`; a run without a digest, or with a stale one, is refused; the digest changes when the
   examined content changes; the attempt and outcome are logged.
3. Build the `wb preview recover` and `wb preview acknowledge` entries on the existing examinations, the `--digest` option and the check.
4. Update the specs and the registry facts in the same commit. If this grows beyond one reviewable commit, stop and report.
**Verification:** the tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-levels-for-recover-pin-approve-attach#A`.

### Increment B — `ask` for pin and approve

**Outcome:** `wb pin` and `wb approve` offer `ask`, bound to the digest of a `wb preview` entry that records nothing.
**Dependencies:** A.
**Affected areas:** the registry, `pins.py`, `pinplan.py`, `approve.py`, `preview.py`, `cli.py`, `levelrun.py`, the parser,
`tests/test_approve_pin_levels.py`, `tests/test_levels.py`, `tests/test_permissions_drift.py`; the same four documents as A.
**Steps:**
1. Read what `pin` shows (path, size, sha256) and what `approve` verifies and confirms.
2. Write the tests first, including that the `approve` preview verifies the package and records no approval, and that a changed package
   or helper changes the digest.
3. Build the previews, the `--digest` option and the check as in A.
4. Update the specs and the registry facts in the same commit. If this grows beyond one reviewable commit, stop and report.
**Verification:** the tests named above and the drift test.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-03-levels-for-recover-pin-approve-attach#B`.

### Increment C — `ask` for attach, and a record for the second acknowledge tier

**Outcome:** `wb attach` offers `ask`, bound to the digest of a preview of what it would write; `acknowledge-second-tier` is decided.
**Dependencies:** A.
**Affected areas:** the registry, `attach.py`, `preview.py`, `cli.py` (`_owner_reading`, parameterised by key), `levelrun.py`, the parser,
`tests/test_levels.py`, `tests/test_permissions_drift.py` and a new attach test file; `docs/decisions/` (one record); the same four
documents as A.
**Steps:**
1. Read `attach.py` and the accepted record's first decision, second bullet (`attach` has no terminal test and also reads the owner's own
   setting).
2. Draft a `Proposed` record (the `draft-decision` skill) that keeps `acknowledge-second-tier` without `ask` while it governs no command,
   or give it `ask` if A found a command it governs. Stop for the owner's acceptance at the `accept-decision` checkpoint before the spec
   cites it.
3. Write the tests first, including that the owner's own setting alone does not grant a run that the verified rendering would refuse
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

Empty until a review is asked for.

## Deferred work

- `wb rerender` and the other plans of the split: `2026-11-02-permission-levels-for-every-command` (D, E, F),
  `2026-11-03-module-conformance-levels-and-hooks`.

## Result

Empty until work starts.
