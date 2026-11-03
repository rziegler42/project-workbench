# The command gate reads a word only where it could run: a gap rule for the in-order test and a data position for plain reads

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-02
Date: 2026-11-02

## Context

While a key is at `ask` or `none`, `wb gate-command` reads every Bash call and refuses one that names a relaxed command unless it is
exactly the simple command the harness `ask` rule matches (`2026-10-26-ask-level-command-gate`). The gate is a speed bump in front of
a text-matching prompt, not a barrier: `command-permissions.md` ("Limits") already accepts that a script file, a word built from
variables whose parts lie farther apart than the window, a base64 or `rev` word and an alias are not seen.

It refuses two kinds of ordinary command that are not attempts to run anything. The owner has met both repeatedly, and so has the
author, in this repository:

1. **The word as data.** `approve-plan` is read as the word alone (`2026-10-27-command-gate-command-position`, decision 2), so a
   `cat` of a decision whose file name holds it, a `grep` for it, a commit subject that mentions it and a heredoc that writes text
   about it are all refused. The literal-arguments record (`2026-10-27-command-gate-literal-arguments`, decision 1) frees a literal
   `wb run <name> ...` for the single-word keys and expressly not for `approve-plan` or the `wb run <command> <argument>` keys.
2. **The in-order test fires on unrelated text.** When a command holds any of `$ ? * [ { ` ` (backtick), the gate looks for the
   letters of a relaxed key in order inside a window three times their number, with other letters allowed between and a `*`
   standing for up to three letters (`_subsequence`, `_WINDOW`). The letters of `groundwork accept` or `wb release-approvals` are
   common, so ordinary commands match: a `grep` across two globs, and a `printf` of a line that holds a `[..](..)` link.

The facts below were run on 2026-11-02 against the real gate (`wb gate-command claude`, the keys of the owner's settings relaxed
at `ask`), with sanitised commands. The in-order false positives reproduced from the full text of commands the gate refused earlier
the same day; a shortened copy of one of them did not reproduce, which shows how fragile the rule is.

| Command (sanitised) | Today |
|---|---|
| `ls docs/plans`, `python3 -I -B scratch/script.py`, `grep -n gate docs/development.md \| head -5` | pass |
| `grep -rn "checkpoint_of" packages/workbench/*/module.json packages/workbench/*/*.json 2>/dev/null \| head` | **refused**, in-order, "groundwork accept" |
| `printf '%s\n' '- [Release approvals at ask](notes.md) ...' >> MEMORY.md` | **refused**, in-order, "wb release-approvals" |
| `cat docs/decisions/<a name holding approve-plan>.md` | **refused**, names the word |
| `grep -n approve-plan docs/development.md` | **refused**, names the word |
| `wb run safe-git commit --subject 'Explain approve-plan in the guide' -- docs/development.md` | **refused**, names the word |
| `cat <<'E' > notes.txt` with a line that names the command | **refused**, names the word |
| `wb approve-plan docs/plans/x.md`, with or without `--digest <32 hex>` | pass (the exact simple form) |
| `echo hi && wb approve-plan ... --digest <hex>`; `bash -c 'wb approve-plan ...'`; `w""b approve-plan ...` | refused |
| `A=approve; wb ${A}-plan ...`; `wb $'\x61pprove-plan' ...`; `wb appro*-plan ...` | refused |
| `python3.12 -m workbench approve-plan ...` (an unlisted spelling) | refused |
| `python3 -m workbench approve-plan ...` (a listed spelling, simple form) | refused: only `wb` has the `ask` rule |
| `wb run review-engine preview extend docs/plans/x.md 2`; `wb run review-engine extend ... --digest <hex>` | pass |
| `wb run review-engine extend ... --digest <hex> && echo done` | refused |
| `wb preview release-approvals`; `wb release-approvals --digest <hex>` | pass |
| `python3 -I -B scratch/x.py wb release-approvals` (the word handed to an interpreter) | refused |
| `W=w; Z=b; X=ove; $W$Z appr${X}-plan ...` (launcher and word both built) | refused, in-order |
| `wb appr{ove-,junk}plan ...`; `wb app$(echo r)ove-plan ...`; `wb a${X}p${Y}r${Z}ove-plan ...`; `wb app?ove-plan ...` | refused, in-order |
| `wb appr$1ove-plan ...`; `wb approve-$1plan p`; `wb a$zz'p'$zz'p'$zz'r'$zz'o'$zz'v'$zz'e'-plan ...` (bare `$1` and an unset `$zz` expand to nothing in bash) | refused, in-order (the third by the rule alone; `tests/test_command_gate.py` pins `wb approve-$1plan p` as refused) |
| `for f in docs/plans/2026-11-0*.md; do echo "$f"; head -3 "$f"; done`; `echo "$HOME/projects/x" "$PWD/docs" "$1"` | pass |

Under this record the expected result changes for five rows only: the `grep` over two globs and the `printf` of a link pass (the gap
rule, decision 2); the `cat` and the `grep` that name `approve-plan` pass (the data position, decision 3); the commit subject that
mentions it passes if the owner accepts decision 4. The heredoc that writes text naming a command stays refused. Every row that is
refused today for any other reason stays refused, and every row that passes today still passes.

## Decision

Proposed; the owner decides. Nothing here is built; the plan `2026-11-02-permission-system-consistency` builds it (increment I).

1. **The gate's purpose and limits stand.** It protects the harness prompt for the relaxed keys, on the text it can read, and does
   not claim more. The accepted limits are unchanged. This record narrows two refusals that are not attempts; it adds no capability
   to run an owner-run command.
2. **The in-order test becomes a gap rule.** The letters of a relaxed key (its skeleton) match only where consecutive letters are
   separated by nothing but wildcards: the inside of an expansion (`$(...)`, `${...}`, a backtick pair), a bare parameter
   (`$name`, `$1` to `$9`, `$@`, `$*`, `$#`, `$-`, `$_`, `$!`, `$$`, `$?`, which bash expands to nothing or to anything), a glob
   (`*`, `?`, a bracket class), a brace group (`{a,b}`, counted as a wildcard block) and an escape sequence; at least a third of
   the letters stay written out as now. Another literal letter between two of the key's letters no longer counts, so letters of unrelated words
   do not add up to a key. The name tests are untouched: the folded text, the skeleton (quotes, backslashes and punctuation
   removed), the decoded `$'...'` views and the pair of launcher and word. Where the old rule allowed padding, the padding that can
   be run lives inside an expansion, and an expansion is already a wildcard.
3. **A data position frees the plain reads.** A relaxed word is not "named" when the whole command is one simple command, or a
   pipeline of simple commands, matched in full on the raw text, whose every program is on a closed list of programs that never
   run their arguments, whose arguments are plain tokens (`[A-Za-z0-9._/:=@,+-]+`) or single-quoted strings, and which holds no
   `$`, backtick, `;`, `&&`, `||`, newline outside quotes or redirection other than `2>/dev/null` and `2>&1`. A single-quoted
   string may hold `$ ? * [ {`, because bash does not expand inside single quotes; so a command that passes the data position is
   not read by the name tests or by the gap rule (`grep 'wb a?prove-plan' notes.md` passes). The list is `cat`, `head`, `tail`,
   `grep`, `ls`, `wc` and `diff`: programs whose arguments, as plain tokens and single-quoted strings with no `$`, redirection
   or glob, the reviewer found no way to run. It is kept in one place and is closed. An interpreter, `sed`, `awk`, `find`, `xargs`,
   `env`, `tee`, `sort`, every launcher and `git` are not on it. `git` is left out because its options can run a program: `-c` and
   `--config-env` set configuration, `--git-dir`, `--work-tree` and `-C` point it at a repository whose own configuration sets a
   pager, an external diff, a text conversion or a file-system monitor, and `log` and `diff` take `--ext-diff`, `--textconv` and
   `--output=<file>`. It may return only by a later record with an allowlist of options for each subcommand, not a list of
   forbidden ones. This is the same kind of match as the literal-run form of the literal-arguments record, a `fullmatch` on the raw
   text, and not a shell parser.
4. **A literal `wb run` call frees `approve-plan`, and only `approve-plan`.** The form of the literal-arguments record
   (`(wb|bin/wb) run <name>( <argument>)*`, plain tokens or single-quoted strings, no `--provides`) names a word only as data for
   the single-word keys already. It is extended to the key `approve-plan` and to no other key. The `wb run <command> <argument>`
   keys (the review engine's five) are **not** changed: they keep `reads_argument_as_data`, which frees a call only when it is the
   key's own command with a plain first token other than the key's argument, because that rule rests on the helper taking its
   action from its first argument alone; a literal `wb run review-engine extend ...` is not freed by this decision. The reason the
   earlier records read `approve-plan` as the word alone is that it is distinctive (`2026-10-27-command-gate-command-position`,
   decision 2), and the literal-arguments record then left it out of its exemption per key. That reason holds for the word
   written as a command; it does not hold for the word handed as an argument of `wb run`, which dispatches to a declared, pinned
   module command, refuses a reserved name such as `approve-plan`, and gives the helper its arguments as `argv`. The cost is the
   one the literal-arguments record already accepted for the single-word keys: a pinned helper that itself re-dispatches from its
   arguments could be handed the word. **The owner chose to accept that for `approve-plan`, the most sensitive key, on 2026-11-02,
   in conversation, when the record was `Proposed`.** The author had recommended it, because a commit subject that mentions the key
   is the commonest of the three false positives. That choice is part of this decision and is accepted or rejected with it.
   The spec text this changes (`command-permissions.md`, "The command gate" and "Limits") is updated in increment M of the plan.
5. **The commands cannot enforce the prompt themselves.** The question was whether the owner-run commands could check their own
   level, digest and terminal so that the text gate only guards the prompt. They already do: a run without a terminal needs the
   level to read `ask` or `none` through `rendering.effective_level` and, at `ask`, a digest recomputed in the command's own lock.
   What they cannot tell is whether the harness showed the prompt to the owner, so the prompt's text match, and the gate that
   protects it, stay the guard of the owner's confirmation at `ask`. This is the position of
   `2026-10-26-ask-level-spelling-limit`; no change.
6. **Every refusal names its rule and what passes.** The line says which test fired (the word was named; the gap rule; a wrapper or
   a compound command; an unlisted spelling; the size or `$'` limit) and the form that passes. The gate appends one line to a
   refusal log in the guarded store for each refusal: time, rule and the first 12 hexadecimal characters of a SHA-256 of the
   command, tab-separated ASCII of at most 256 bytes, never the text. The writer follows `levellog.py` (appends through
   `safefs.append_line`, never reads the file, refuses a link, a non-regular file and a second hard link). The append is made after
   the verdict is fixed and inside its own guard, so a full, unwritable or damaged log, and the cost of the hash (the command is
   already limited to 64 KiB), cannot change a result or push the gate past its deadline. At the size cap the gate stops
   appending and `wb doctor` reports the log as full; the owner rotates it by hand, as with the level log. The log is a
   diagnostic and not an audit record: the gate runs as the agent's process, so the agent can write or fill it from a shell, as
   `2026-10-26-ask-level-command-gate` accepted for the level log. An unsalted short hash can be confirmed by someone who guesses
   the command, which matters only to someone who can already read the owner's private store. `wb doctor` reads only the last
   64 KiB of the log, tolerates a corrupt line and prints counts per rule; the owner can also read the file, which tells them
   which rule fired and when, not what the command was.
7. **Spellings.** Only the exact simple command through `wb` (or the store's `bin/wb`) passes for a relaxed key, as now; a
   `python -m workbench` spelling and an unlisted one are refused at a relaxed level. This confirms the claim made in
   `2026-11-02-one-permission-registry-and-key-model` (decision 6) for a relaxed level. At `block` the command's own terminal
   test refuses, and the plan's corpus tests that side.
8. **What does not change.** The levels, the keys, the rendering, the 64 KiB and `$'` limits, the failure to a block, the exact
   forms the `ask` rule matches and the accepted limits stand. A heredoc or a redirect that writes text naming a command stays
   refused: the owner or the agent writes such a file with the Write tool, which has its own gate.

## Alternatives considered

- **Require a literal launcher before the in-order test runs.** Rejected after a probe: `W=w; Z=b; X=ove; $W$Z appr${X}-plan x`
  has no literal launcher and is refused today; it would pass. The gap rule keeps it.
- **Tune the window or the literal fraction.** Rejected: a smaller window or a larger fraction removes some false positives and
  keeps the cause, which is that unrelated letters add up to a key. The gap rule removes the cause.
- **Drop the in-order test.** Rejected: it is the only test that sees a word spelled with an expansion or a glob, which the tests
  pin, and the gap rule makes it cheap to keep.
- **Read `approve-plan` in command position like the ordinary-word keys.** Rejected: `$W approve-plan` with `W=wb` would not be seen.
  The data position frees the harmless uses without that cost.
- **A shell parser that judges the command position.** Rejected again, for the reason the literal-arguments record gave: a parser
  of untrusted text is larger and riskier than the folding. The data position is a `fullmatch` and a closed list.
- **An allowlist taken from module declarations.** Possible later; the list is installer-owned today and not a module's fact.
- **Tell the owner to run such commands themselves.** The state of things. It makes the common read-only commands unusable while a
  key is relaxed, against the owner's direction that the system should not get in the way of the owner's chosen risk.
- **Edit the accepted records.** Not allowed. This record refines decision 2 of `2026-10-27-command-gate-command-position` and
  decision 1 of `2026-10-27-command-gate-literal-arguments`; their status lines gain a clause once the owner accepts it.

## Consequences

- Good: the ordinary commands that were refused (a `grep` over two globs, a `printf` of a link, a `cat` or `grep` of a file that
  names a command, a commit subject that mentions one) run, and the refusals that remain say why.
- Good: every attempt in the table above that is refused today stays refused, in the samples run, including the ones the old rule
  caught by letters.
- Bad: the gap rule is a different rule from the one the existing tests pin; the plan's corpus (increment D) records today's
  results first, so any case it changes is visible, and the existing tests in `tests/test_command_gate.py` must pass unchanged.
  A prototype of the rule on about 30 sample commands, not kept, was quiet on the two false positives and on ordinary uses of
  `$f`, `$HOME` and `$1`, and fired on every attempt the old rule catches. It needed two things the first draft of this record
  lacked, both found by testing: brace groups counted as wildcards (without them it missed three) and bare parameters counted as
  wildcards (without them it missed `wb appr$1ove-plan` and the pinned `wb approve-$1plan p`, found by the reviewer). That is a
  small sample and not a proof, and a third gap of this kind is possible.
- Bad: a literal letter between two of the key's letters no longer counts. No expansion form tested makes bash join them, but the
  claim rests on the author's reading of bash and on the corpus; the plan offers a security review of this increment. The change is
  the same at `ask` and at `none`; at `none` there is no prompt, so the gate is the only text barrier left, and what stops being
  caught at either level is only the old rule's tolerance of ordinary letters between the key's letters.
- Bad: the data position adds a closed list of programs to the installer. A wrong entry would free a command that does run its
  argument, so the list is small, kept in one place and covered by a test per entry; `git` is left out until a later record gives
  it an allowlist of options.
- Bad: item 4 widens a form the earlier record narrowed, for one key. If the owner declines it, the commit subject that mentions
  `approve-plan` stays refused.
- Neutral: the refusal log stores a hash and a rule, not the command, and never changes a result. A command the owner would rather
  not have logged is not logged in clear.

## Evidence

Run on 2026-11-02 at commit `53da2b6`, workbench 0.1.0, Python 3.15.0: `wb gate-command claude` with JSON input on 34 sanitised
commands, in two scripts (25 for the table in Context and 9 replays of the refusals seen earlier that day with their cut-down
variants; all read from the gate's exit code and its refusal line); the same on 8 commands that vary how the launcher and the word
are built; and a throwaway prototype of the gap rule that imports the gate's own folding functions and was compared with
`_subsequence` on about 30 distinct samples in three runs (the second added brace groups, the third bare parameters after the
review of this record; the third also compared the prototype with the real gate on each sample). The prototype was not
kept and the gate's code was not changed. Read: `workbench/command_gate.py` (`judge`, `_subsequence`, `_collapse`, `_PATTERN_CHARS`),
`docs/specs/command-permissions.md` ("The command gate", "Limits"), and the four accepted gate records. Not run: the same commands at
level `block`, with a key at `none`, in an attached project other than this one, or against a command longer than a few hundred
characters; no security review has been made of the gap rule; the closed list of programs has not been tested one by one;
the options of `cat`, `head`, `tail`, `grep`, `ls`, `wc` and `diff` were checked by reading and reasoning of the reviewer and
the author, not by running each with a hostile option.

## Related files and decisions

- `docs/plans/2026-11-02-permission-system-consistency.md` (increments D and I)
- `docs/specs/command-permissions.md` ("The command gate" and "Limits" change at increment M of the plan, when this is built)
- `tests/test_command_gate.py`
- [2026-10-26-ask-level-command-gate](2026-10-26-ask-level-command-gate.md)
- [2026-10-26-ask-level-spelling-limit](2026-10-26-ask-level-spelling-limit.md)
- [2026-10-27-command-gate-command-position](2026-10-27-command-gate-command-position.md)
- [2026-10-27-command-gate-literal-arguments](2026-10-27-command-gate-literal-arguments.md)
- [2026-11-02-one-permission-registry-and-key-model](2026-11-02-one-permission-registry-and-key-model.md)
