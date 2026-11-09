# Let the command gate pass a relaxed `wb run` key's own call when its arguments are plain or single-quoted

Status: Proposed
Created: 2026-11-09
Candidate: none (a correction that follows from a finding of the cutover trial, increment F of `2026-11-08-action-review-cutover-for-commit`)
Specs: command-permissions

## Goal

The agent can make a commit through `wb run safe-git commit` while that key is at `delegated` (it offers `block`, `delegated` and `none`, not `ask`), so that the owner's prompt, or the hook that may answer it, is the barrier the key promises, instead of the gate refusing every commit before the prompt exists.

What was found (2026-11-09, the first use of the key at `delegated`): the command gate refused `wb run safe-git commit --expected-head <hash> --state-digest <digest> --subject '<words>' --trailer 'Plan: <stem>#F' -- <path>` with `the command names safe-git commit, which the owner has set to ask or none here, and is not exactly the simple command the ask rule matches (rule: names)`. In `workbench/command_gate.py`, for a relaxed key of the form `wb run <command> <argument>` the only form of the key's own call that `forms()` lets through is `wb run <command> <argument>` followed by plain tokens of `[A-Za-z0-9._/:=-]+`: no space and no single-quoted string. A commit always has a subject with spaces, so it can never pass. The harness's rendered rule is wider than that form: the rule rendered for the `remove` key, `Bash(wb run safe-git remove *)`, read today in `.claude/settings.local.json` as an example of the shape, is a prefix with a wildcard, and it matches whatever follows. The `commit` key has no rule there while it stands at `none`; its rule is rendered only at `ask` or `delegated`, so the rule that matters for this plan is the `commit` one, and increment A has to read it in a copy where the key is set, not infer it from `remove`. The accepted decision `2026-10-27-command-gate-literal-arguments` already lets a literal `wb run` command with single-quoted arguments through for a single-word key, and says "the keys `wb run <command> <argument>` ... are not exempted" (a different case: it frees a call that only names the key's word as data; the key's own call is the call the `ask` rule has to see). The cutover plan's increment C made `delegated` count as `ask` for the gate and tested only plain arguments, so it did not meet the limit. Any key of that form that offers `ask` and takes free text has the same limit (the commit key offers `delegated`, not `ask`); the keys that offer `ask` today take paths and plain words, so nobody had met it.

After this plan, for a relaxed key of the form `wb run <command> <argument>`, the key's own call is one the gate lets through when the whole text is `wb run <command> <argument>` (through `wb` or the guarded store's own `bin/wb`) followed by arguments that are each a plain token (`[A-Za-z0-9._/:=@,+-]+`) or one single-quoted string, as `literal_run` reads them, and nothing else. Every other form is judged as it is now.

## Scope

- A new decision record in `docs/decisions/`, Proposed, that says what changes and what stays of `2026-10-27-command-gate-literal-arguments` and `2026-10-28-gate-reads-module-arguments`; the owner accepts it.
- `workbench/command_gate.py` (`forms`) and its tests, and the part of `docs/specs/command-permissions.md` that describes the gate's form.
- A probe, on a throwaway copy, that the harness's rendered rule fires on a command with a single-quoted argument (the gate is meant to guarantee that the prompt exists; widening it needs that shown, not read).

## Non-goals

- Any other key, any single-word key, `approve-plan`, and the rules `gap`, `size-limit` and `dollar-quote-limit`: unchanged.
- Allowing a double-quoted, backslash-escaped, substituted or globbed argument, a compound command, a redirection or a newline outside quotes.
- Making the gate understand a shell. It still reads text.
- Cutting over `commit`: the owner's trial, in the cutover plan.
- Changing the engine, the hook or the levels.

## Assumptions and constraints

- **The widened form is the same literal-argument form the gate already trusts (my call).** `literal_run` and `reads_argument_as_data` use `_RUN_ARGUMENT` (a plain token or one single-quoted string with no quote inside) for the other free cases; the key's own call uses the same arguments. Bash expands nothing in a plain token of that alphabet or in a single-quoted string.
- **The words of another key of the same form inside a quoted argument are still refused (a fact of the code, to be pinned by a test).** The loop judges each relaxed key on its own: with the key `wb run review-engine extend` relaxed, a commit whose subject holds `review-engine extend` names that key, is a literal call of a different command (so `reads_argument_as_data` does not free it) and is not that key's form, so it stays refused; this plan changes nothing about it. The exemptions that exist today stay as they are: a literal `wb run` call is not searched for the word of `approve-plan` (decision 4 of `2026-11-02-command-gate-reads-gaps-and-data-positions`) or of a single-word `wb <word>` key (`2026-10-27-command-gate-literal-arguments`), so a commit whose subject holds `approve-plan` passes the gate today and still does.
- The harness's rule is a text match with a wildcard. Whether it fires on a quoted argument in every mode the owner uses (default and auto) is the probe's question; if it does not fire, this plan stops, because the gate would then let a call through that nothing prompts for.
- A decision outranks code. The plan writes the record as `Proposed` and stops. At `ask` for `accept-decision`, the owner runs the accept with the digest the preview prints; the plan does not accept it.
- The installer's tests are many; the change is in `forms()` and its callers only, and the verification names the tests that reach it.
- Standard library only.

## Completion criteria

1. A record on the owner's accepted-decision route says the key's own call may carry single-quoted arguments, why that is safe, what was probed and what stays refused.
2. On a throwaway copy with the key `wb run safe-git commit` at `delegated` (the only relaxed level that key offers; its rendered rule is an `ask` rule), the harness's rule fires (a prompt, or in auto mode the classifier's decision is not reached because the rule decides) for a call whose arguments include a single-quoted string with spaces and a `#`; the evidence names the Claude Code version, the mode, what was run and what was seen.
3. `forms()` for such a key accepts the text `wb run <command> <argument>` followed by plain or single-quoted arguments and refuses: a double quote, a backslash, `$`, a backtick, a glob character outside quotes, `;`, `&&`, `|`, a redirection, a newline outside quotes, a trailing newline, an unclosed quote, a path to `wb` that is neither `wb` nor the store's `bin/wb`, and, with the key `wb run review-engine extend` also relaxed, a commit whose quoted subject holds `review-engine extend`; the exemptions for `approve-plan` and for single-word keys stay intact and are not changed.
4. The commit that was refused on 2026-11-09 passes the gate as a whole; a name test, gap test and size tests still refuse what they refused.
5. The spec states the form; the test of the gate that pinned the old form is changed with a reason, and no test is skipped.
6. `wb run code-work check` passes.

## Increments

### Increment A — The probe, on a throwaway copy

**Outcome:** completion criterion 2 is true, or the plan stops with the reason.
**Dependencies:** none.
**Affected areas:** a scratch directory outside the project; the Result of this plan.
**Steps:**
1. Read how the installer renders the rule for a relaxed `wb run` key (`workbench/rendering.py`, `tests/test_rendering.py`) and render it for the `commit` key itself, in a scratch copy of the project where the table sets `wb run safe-git commit` to `delegated` (the only relaxed level that key offers; `wb settings` prints `offers=block,delegated,none`), and for one key of the same form that does offer `ask` (a real one, for example `wb run review-engine amend`), so that the shape of the `ask` rule is read for both (the agent imports the installer's rendering code from the copy and dumps the rule as data, and never runs a copy's `wb`, whose launcher would rewrite the shared one): write down the exact `commit` pattern the harness is given for each, and check that the probe command in step 2 matches that pattern as text.
2. Make a throwaway project in the scratch directory with the rendered `commit` rule (the exact pattern of step 1, for a fake `wb` that records its argv and not the real helper) and the same hook layout except for one substitution: the scratch copy's command-gate hook (the one that refuses the quoted commit today, which would stop the call before the rule could prompt) is replaced by a recording hook that logs the call it was given and allows it, so that the probe isolates the harness's rule from the gate; the Result names the substitution and says that the real gate is not part of what the probe tested. Give the owner the exact steps to run Claude Code against it in default mode and, if the owner uses it, auto mode, with a call of the shape of the refused commit: `wb run safe-git commit --expected-head <hash> --subject '<words with spaces>' --trailer 'Plan: <stem>#F' -- <path>`. The owner runs it and says what the prompt showed. The agent does not run the harness.
3. Record the Claude Code version, the steps, what was seen and the conclusion in the Result. If the rule did not fire in a mode the owner uses, stop and report.
**Verification:** the owner's observation and the fake program's record; nothing in the project changes.
**Evidence:** the one local commit that records the Result, with the trailer `Plan: 2026-11-09-command-gate-quoted-arguments-for-a-run-key#A`.

### Increment B — The decision record

**Outcome:** completion criterion 1 is true as `Proposed`, and the plan stops for the owner.
**Dependencies:** A.
**Affected areas:** `docs/decisions/` (the new record and the index `docs/decisions/README.md`).
**Steps:**
1. Follow the `draft-decision` skill: the context (the finding, the limit in `forms()`, the harness's rule), the decision (the form in the Goal, per key, never an early return for another key), the alternatives (leave the gate and tell the owner to commit by hand; a separate rendered key for commit with its own pattern; an agent-safe wrapper command for the subject; each rejected with its reason), the consequences (good and bad) and the evidence (the probe of A, the refusal text, the gate version and commit).
2. Set the status `Proposed`, update the index, run `wb run code-work check` and stop. The owner accepts it with the route of `accept-decision`; the agent does not accept it.
**Verification:** `wb run code-work check` (the document check reports a wrong status or index).
**Evidence:** the one local commit, trailer `...#B`.

### Increment C — The gate

**Outcome:** completion criteria 3, 4, 5 and 6 are true. It begins only when the record is accepted.
**Dependencies:** B, and the owner's acceptance of the record.
**Affected areas:** `workbench/command_gate.py`, its tests (`tests/` for the gate), `docs/specs/command-permissions.md`.
**Steps:**
1. Write the tests first in a scratch clone: the form in criterion 3 (each accepted and each refused text), the whole refused commit of 2026-11-09, a quoted subject that holds the words of the other run key `wb run review-engine extend` (refused, before and after), a quoted subject that holds `approve-plan` (passes, before and after: the existing exemption), the unchanged refusals of the other rules, and a key that is not of the form `wb run <command> <argument>`. See them fail.
2. Change `forms()` for a key of that form to the widened pattern, with one named constant shared with `literal_run`; leave every other key as it is.
3. Update the spec's description of the form and run the verification. Ask the `reviewer` for a read.
**Verification:** the gate's tests and the tests that reach `forms()` (rendering, doctor, delegated rendering); a mutation pass over the changed lines with each kill attributed to a named test; `wb run code-work check`. Before any wider run, tell the owner what could break outside the tested area: other keys' forms, which are meant to be unchanged.
**Evidence:** the one local commit, trailer `...#C`.

## Verification for the plan as a whole

The probe of A, the owner's acceptance of the record and the tests of C. After C the owner copies the file, releases and upgrades as for any change to the installer; the cutover plan's increment F resumes from its step 2.

## Risks and sensitive actions

- **This is the command gate, the barrier that keeps the agent from running a relaxed command without its prompt.** A form that is too wide lets a call through that nothing prompts for. The form is the literal form the gate already trusts; the probe shows the harness's rule fires on it; the tests pin what stays refused; and the owner is asked whether to run a security review of the change (recommended: yes).
- A bypass that builds a relaxed key's words at run time is still the accepted limit of the gate; this plan does not move it.
- An accepted decision is amended by a new record, which is the owner's act.
- A change to the installer: the copy, the release approvals, the stale-record removal and the upgrade are the owner's steps. Nothing is pushed.

## Review record

Codex, plan review, 5 rounds (the bound of 3, extended by 1 twice on the owner's word, 2026-11-09; the ceiling is 5); converged with no meaningful finding in round 5, which read the plan with the fixes of rounds 1 to 4 (the review record below is written after it). Models: `gpt-5.6-terra` for rounds 1 and 2, `gpt-6.1-sol` for rounds 3 to 5. Rounds 1 to 4 each found one major issue; all four were real and were applied.

- Applied (round 1, major): the plan named the rule of the `remove` key as the evidence for the `commit` key's rule. It now says the `remove` rule is only an example of the shape, and increment A reads the `commit` rule itself in a scratch copy where the key is set, and checks that the probe command matches it.
- Applied (round 2, major): the plan treated `wb run safe-git commit` as settable to `ask`; it offers `block`, `delegated` and `none`. The goal, criterion 2 and the probe now use `delegated` for the commit key, and the `ask` rule's shape is read from a real key that offers `ask`.
- Applied (round 3, major): the probe's hook layout included the command gate that refuses the quoted commit, so the call would stop before the rule could prompt. The scratch copy now replaces only that hook with a recording hook that allows the call, and the Result names the substitution and says that the real gate was not part of what the probe tested.
- Applied (round 4, major): the plan required that a commit whose subject holds `approve-plan` stay refused. The gate already frees a literal `wb run` call for `approve-plan` (`command_gate.py`, the `literal` test in `verdict`), so that would have changed behaviour outside the scope. The test of another key's words now uses the run key `wb run review-engine extend`, and the plan states that the existing exemptions stay intact.
- Round 5: no meaningful finding (the reviewer's words: the plan preserves the existing exemptions, requires probe evidence before implementation and gates the spec change on an accepted decision). The review is at its ceiling.
- Left for the owner: approval. A review with no finding is not an approval.

## Deferred work

- Why `wb run safe-git commit` with a quoted subject passed the gate while the key stood at `none` and not at `delegated`: the cause is probably that a key at `none` for an agent-safe command is not in the gate's relaxed list, but this was not read; increment C's tests should pin whichever it is.
- A plain-text or file-based way to give a commit subject that needs no quote (a different design).

## Result

**Increment A (2026-11-09), done outside the project, in a scratch directory; the Result is the only file of the project it changes.**

- Step 1, the rule as the installer renders it (read as data): the agent imported `workbench.rendering` of this project's tree and called its pure function `plan` with a table that sets `wb run safe-git commit` to `delegated` (as an action the module describes) and `wb run review-engine amend` to `ask`, with `python3 -I -B`; it ran no `wb` and read no settings. The `ask` patterns were, for the commit key: `wb run safe-git commit`, `wb run safe-git commit *`, `wb run --provides * safe-git commit` and `wb run --provides * safe-git commit *`, and the same four for `wb run review-engine amend`; the rendered file spells each as `Bash(<pattern>)`, once with `wb` and once with the guarded store's `bin/wb` (read in the live `.claude/settings.local.json`, where the existing `ask` list has that shape). The two keys render the same shape, so the commit key's rule is not special. The refused commit of 2026-11-09 matches `Bash(wb run safe-git commit *)` as text (it begins `wb run safe-git commit `).
- Step 2, the probe project: `<scratchpad>/gate_probe/` with `.claude/settings.local.json` (the eight `ask` rules of the commit key above), a fake `bin/wb` (records its arguments and prints a line) and `hooks/record.py`, which logs the event, the mode and the command and exits 0 with no output. **One substitution, as the plan says:** the layout's command-gate hook (`wb gate-command claude`, which refuses this commit today) is replaced by that recording hook, as a `PreToolUse` hook on `Bash`, and a recording `PermissionRequest` hook is added; so the probe did not test the real gate, and it tested nothing about the action-review hook. The owner ran Claude Code (version 2.1.319 as `claude --version` prints on this machine) in the probe directory with the fake `wb` first on the `PATH`, and typed: `Run this exact Bash command and nothing else, do not change it: wb run safe-git commit --expected-head 0123456789abcdef0123456789abcdef01234567 --subject 'A probe subject with spaces' --trailer 'Plan: probe-stem#F' -- a.txt`.
- Step 3, what was seen (the owner's pasted screens, and `log.jsonl`): **auto mode on:** a permission prompt, with the text "Ask rule Bash(wb run safe-git commit *) overrides auto mode for this command"; **auto mode off (default mode):** a permission prompt, with the text "Permission rule Bash(wb run safe-git commit *) requires confirmation for this command". `log.jsonl` has, for each run, a `pretool` and then a `permission-request` entry with the whole command as typed (the single-quoted subject with spaces and the trailer with `#` intact), in modes `auto` and `default`. No `calls.log` exists: the fake `wb` never ran, so the owner answered No or cancelled. Nothing in the project was touched and nothing was committed.
- Conclusion: criterion 2 is true for the key `wb run safe-git commit` at `delegated`, in the two modes the owner has: the harness's rendered rule fires on a call whose arguments hold a single-quoted string with spaces and a `#`, and in auto mode the rule overrides the classifier. The plan goes on. Not tested, and not claimed: the real gate (the point of increment C), the action-review hook answering the request (the probe's hook answered nothing), a key that offers `ask` (the shape is the same; the probe used the commit key), and other versions of Claude Code.
- Possible side effect, not checked: the owner's user-level hooks apply in the probe directory too, so the registered shadow hook may have reviewed the fake command and written a row to the owner's store (the report's count of prompted commands rose from 706 to 715 during the session, which includes this session's own commands, so the probe's share cannot be told). It cannot have allowed anything: the probe is not a project the installer knows, and no row says `allow` (the report printed no "hook allowed" lines).
- Left for the owner: the commit of this Result (say "commit it"); then increment B, the decision record, which the agent writes as `Proposed` and stops.
