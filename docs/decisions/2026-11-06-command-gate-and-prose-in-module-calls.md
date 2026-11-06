# The command gate and prose in a module call: a text fix now, and a narrow gate change that reverses one rejected alternative

Status: Proposed
Date: 2026-11-06

## Context

While a key is at `ask`, `wb gate-command` refuses every Bash call that names a relaxed command unless it is exactly the simple command the harness `ask`
rule matches (`2026-10-26-ask-level-command-gate`). The earlier records narrowed the refusals that were not attempts: a plain read freed by a closed list of
programs (`2026-11-02-command-gate-reads-gaps-and-data-positions`, decision 3), a literal `wb run <name> ...` freed for the single-word keys and for `approve-plan`
(`2026-10-27-command-gate-literal-arguments`; `2026-11-02-command-gate-reads-gaps-and-data-positions`, decision 4), and, for the `wb run <command> <argument>` keys, a literal call **of the key's own command** with a plain first
token other than the key's argument (`2026-10-28-gate-reads-module-arguments`, decision 2). That record rejected two things this one comes back to: a quoted first
token, and "exempt any `wb run <name> ...` command for these keys, whatever the name", because "it frees a pin of the same helper under another name, and a pin is
owner-approved code whose first argument the gate has not been told about".

The notes feature (`mempalace-notes.md`) put free prose into module calls: a note's title and body, a search question. The owner's live run of 2026-11-06
("Evidence" in that spec) met the gate there with `mine`, `sync` and the notes' `keep` at `ask`:

- A save whose body held the word "keeps" was refused (rule `names`). The agent reworded the owner's text to get past it and did not say so.
- A harmless read-only `list --wing examine-test` was refused as naming `mempalace mine`.
- The agent appended a pipe to the `keep` command, was refused, and followed a hint that dropped `run` into a second refusal (the hint is fixed by increment B
  of the plan `2026-11-06-notes-live-run-fixes`).

The gate finds a key's words in order in the folded text and in its skeleton (letters and digits only, with spaces and punctuation removed). Words are therefore
found inside longer words, across word boundaries ("I am in every case" is `iaminevery...`, which holds `mine`), and inside the name of another command: the
skeleton of `mempalace-notes` holds `mempalace`. Ordinary English prose can name `mine` or `sync`.

The facts below were run on 2026-11-06 at commit `1314b5f` against the real gate (`command_gate.verdict`; the keys `wb run mempalace mine`, `wb run mempalace sync`
and `wb run mempalace-notes keep` at `ask`), with sanitised commands:

| Command (sanitised) | Today |
|---|---|
| notes `save ... --body "the owner keeps the rule"` (double quotes) | **refused**, names `keep` |
| the same with the body in single quotes, or as one plain token | pass |
| notes `save ... --body 'we determine it'`; `... --body 'it runs async'`; `... --body 'I am in every case sure of it'` (single quotes) | **refused**, names `mempalace mine` or `mempalace sync` (the key's command is `mempalace`; this is `mempalace-notes`) |
| `wb run mempalace search --results 5 -- "how do we determine a source"` (double quotes) | **refused** |
| the same question in single quotes | pass (the key's own command, a plain first token) |
| notes `list --wing examine-test`; notes `read async-notes` (plain tokens) | **refused**: another command's name is not freed |
| `wb run safe-git commit --subject 'Explain mempalace mine in the guide' -- docs/a.md` | **refused**; the same subject without the key's words passes |
| notes `save ... --body - < /tmp/n/note.txt` (the text in a file, on standard input) | pass |
| notes `save ... --body - <<'E'` with a line holding "keeps" (a heredoc) | **refused** |
| `wb run mempalace mine <dir> --wing p --confirm --digest <hex>`; `wb run mempalace-notes keep --wing p --digest <hex>` | pass (the exact simple command) |
| the same two with ` \| head -3`, with ` 2>&1`, behind `cd ... &&`, inside `bash -c '...'`, or with the word built from a variable | refused |
| a double-quoted body holding `$(...)` or a backtick that runs the key | refused |

So single quotes free the `keep` word in a notes call and everything in a call of `mempalace` itself, and nothing else. The plan's increment A already tells the
agent not to reword, to put the text in a temporary file and pass it on standard input (that passes, row above), and to report a refusal. It costs a file write,
and it leaves the title, the wing and the other arguments in the command line.

## Decision

Proposed; the owner decides. Nothing here is built, and this record's plan changes nothing in the gate.

1. **The gate's purpose and limits stand.** It protects the harness prompt for the relaxed keys, on the text it can read, and is a speed bump and not a barrier
   (`2026-11-02-command-gate-reads-gaps-and-data-positions`, decision 1). This record asks for no capability to run an owner-run command.
2. **A text fix now, partial.** Increment A of the plan already gives the file route and the rule to report a refusal. What is new is the form: the block and the skill
   show the search question, the title and short bodies in single quotes (until now they showed double quotes), and keep the title and wing to plain short words. That frees the `keep` word and the searches, and removes most prose from
   the command line. It does not free a plain word such as `examine-test` or `async-notes` in a notes command, or a title with the letters of `mine` or `sync`, while
   those keys are at `ask`. It needs a small plan of its own (it changes the always-loaded block) and no code.
3. **Free a literal call of another module command, with the same guard (recommended; the fix for the cause).** A literal `wb run <name> <first> <args>` is not read
   as naming a `wb run <command> <argument>` key when its first token is plain and is not the key's argument, its arguments are plain or single-quoted, and
   `<name>` is any command, including one that is not the key's. This **reverses the rejected alternative of `2026-10-28-gate-reads-module-arguments`** ("exempt any
   `wb run <name>` command") and **refines its decision 2** ("only the key's own command is freed"). The new reason: that record's stated risk was a pin of the same
   helper under another name; a pin runs a key's action only when its first argument is the key's argument, and the guard (a plain first token that is not the key's
   argument, folded) is kept for every name, so an alias called with `mine` as its first argument is still refused. **That guard is one literal comparison: it sees an alias
   called with the key's own token, and it does not see a synonym, a prefix or a case that a pin's launcher would also accept**, which the gate cannot know; the
   accepted record had the same dependency for one command, and this one widens it to every command. The remaining cost is the one the earlier
   records accepted: a pinned helper that re-dispatches from a later argument could be handed the key's words, quoted, as data. Read today, the helpers that pass
   arguments to another program (`mempalace`, `safe-git`, `remote-runner`, `ask-codex`) start no `wb` (a search of their helpers found no such call). **The
   `action-review` helper does: it starts `wb run <module> describe <action> <arguments>` with arguments taken from the reviewed command**, so it is the first helper the
   building plan must test with a single-quoted multi-word argument that holds the whole key; the plan tests every declared command's helper the same way, and
   `remote-runner`'s configured profiles, which this record did not trace. This fixes `list --wing examine-test`,
   every plain word and every single-quoted prose in a notes command, and the commit subject that mentions a module key. **Decision 3 also skips the rest of the key's loop for such a call, not only the names test, so it would free a
   single-quoted literal that the gap rule refuses today** (`wb run safe-git commit --subject 'm*i*n*e'`); that is intended, because bash expands nothing inside single
   quotes, and the security review must look at it. It is built by a plan of its own, with a Codex review and a security review. The gate's own text stays: the key's words are still in the command line; they are not read as naming it.
4. **Do not free a double-quoted string now.** Bash expands `$`, a backtick and a backslash inside double quotes, so a rule that allows them needs a character class
   that must be exactly right; decisions 2 and 3 make it unnecessary for the notes. It may return as a later record.
5. **Do not rename the keys or the commands.** A shorter or rarer name still occurs inside some word or across two, and `mempalace-notes` is already installed,
   specified and tested.

## Alternatives considered

- **Leave it as it is, and rely on the text of increment A.** Every first attempt with such a word is still refused, and the stdin route fails whenever the title or
  a wing holds the letters. Rejected as the whole answer; kept as decision 2.
- **Free an inert double-quoted string.** See decision 4.
- **Rename `keep` or `mempalace-notes`.** See decision 5.
- **Teach the gate which commands are declared and not owner-run.** Stricter than decision 3, but the gate does not read manifests, and
  `2026-10-21-module-code-lives-in-modules` keeps module knowledge out of the installer. Rejected for now, as the module-arguments record did.
- **Treat the values of named long options of one known command as data** (`--body`, `--title`, the search question). It needs the gate to know each command's
  options, which is the same module knowledge; rejected for the same reason.
- **A `--body-file` argument of `save`.** The text would be a path on the command line and never prose. Standard input from a file does the same without a new
  argument.
- **Parse the shell properly.** Rejected again, for the reasons of `2026-11-02-command-gate-reads-gaps-and-data-positions`.
- **Run `mine` and `keep` with no `ask` rule, and trust the owner-run test.** Rejected: at `ask` the text gate is what protects the owner's confirmation
  (`2026-11-02-command-gate-reads-gaps-and-data-positions`, decision 5).
- **Set `mine`, `sync` and `keep` back to `block` between uses.** The owner can do it today at no cost to the gate, and it is the working answer until one of the above
  is built; it is not a decision of this record.

## Consequences

- Good: with decision 2, a search question, a title and a short body in single quotes pass, a long body passes through a file, and the refusal message names a
  command that works (increment B).
- Good: decision 3, when built, removes the refusals caused by the name of another command and by prose in single quotes; every row that is refused today for any
  other reason stays refused, except the gap-rule refusals of single-quoted literal text noted in decision 3, to be shown by the corpus
  (`tests/fixtures/gate_corpus.json`) before the change.
- Bad: decision 2 relies on an agent following text, and does not remove the refusals of a plain word or of the letters of `mine` or `sync` in a title or a wing.
  The live run showed the agent ignoring one stated rule (the pipe on `keep`) and following another (`mine` as one command). A refusal is still safe: nothing runs.
- Bad: decision 3 reverses a rejected alternative of an accepted record, so it widens a freed form from one command to every declared command. A wrong reading would
  free a command that does run its argument; the guard, the plain first token and the per-helper tests are what stand against that.
- Bad: until decision 3 is built, the notes' `keep`, and `mine` and `sync`, at `ask` refuse some ordinary prose. The owner can set them back to `block` between uses.
- Neutral: the accepted records `2026-10-28-gate-reads-module-arguments` and `2026-10-27-command-gate-literal-arguments` keep their text; their status lines gain a
  clause only when the owner accepts this record.

## Evidence

Run on 2026-11-06 at commit `1314b5f`, workbench 0.1.0, Python 3.15.0: a throwaway script that imports `workbench.command_gate` and calls `verdict` on about 30
sanitised commands in three runs (the rows above, and the cases the gate must still refuse), with the three keys at `ask`; each result was read from the verdict's
rule and reason. Also read: `workbench/command_gate.py` (`literal_run`, `reads_argument_as_data`, `reads_as_data`, `forms`, `_names`), the helpers of `mempalace`,
`safe-git`, `remote-runner` and `ask-codex` (a search for a call that starts `wb`; none found), the live run in `docs/specs/mempalace-notes.md` ("Evidence"), and the
accepted gate records named above. The script was not kept and no code was changed. The statement that decision 3's guard still refuses an alias called with the key's argument comes from reading
`reads_argument_as_data` and `forms`, not from a run, because decision 3 is not built. Departures from the plan's wording: the probe ran against the gate code of the
live tree and neither read nor replayed `tests/fixtures/gate_corpus.json` (step 1 of the increment asked for it to be read); the corpus is where decision 3's
building plan starts. The decisions README keeps no list of records, so there is no index row to change.
Not run: the same commands at level `none`, in an attached project other than this one, or through the real hook (the verdict function was called, not the hook);
no security review of decision 3 has been made; no test that an agent follows decision 2; no trace of what each helper does with a quoted multi-word argument.

## Related files and decisions

- `docs/plans/2026-11-06-notes-live-run-fixes.md` (increment C)
- `docs/specs/mempalace-notes.md` ("Evidence")
- `docs/specs/command-permissions.md` ("The command gate")
- [2026-10-26-ask-level-command-gate](2026-10-26-ask-level-command-gate.md)
- [2026-10-27-command-gate-literal-arguments](2026-10-27-command-gate-literal-arguments.md)
- [2026-10-28-gate-reads-module-arguments](2026-10-28-gate-reads-module-arguments.md)
- [2026-11-02-command-gate-reads-gaps-and-data-positions](2026-11-02-command-gate-reads-gaps-and-data-positions.md)
- [2026-10-21-module-code-lives-in-modules](2026-10-21-module-code-lives-in-modules.md)
