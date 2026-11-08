# Stop reading the body of a quoted python heredoc for gaps in the command gate

Status: Proposed
Created: 2026-11-08
Candidate: workbench-v1#command-gate-python-heredoc
Specs: command-permissions

## Goal

After this plan, a Bash call that is one python here-document, written exactly as decisions 1 and 2 of the accepted record `2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps` say, is no longer refused by the gap rule or the free-region test for letters its body shares with a relaxed command. The names test still reads the whole text, body included, so a body that writes a relaxed command's words stays refused. Every other command, and every here-document that is not that shape, is judged exactly as today.

The reason. On 2026-11-03 a 3 KiB python heredoc with reStructuredText docstrings was refused by the gap rule for `wb release-approvals` although it names no command: the gate read each pair of double backticks as a command substitution and let the docstring's letters serve as padding. The owner's way round it is to write the script with the editor tool and run it as a file, which the gate lets through with no reading at all, so the heredoc is the one spelling of the act that is read and refused for nothing. In this project it recurs: on 2026-11-07 the gate refused `python3 - <<'EOF'` scripts twice and each was written as a file at the cost of a second call.

## Scope

- `workbench/command_gate.py`: a function `python_heredoc(text)` that recognises the shape on the raw text and returns its first line, and `verdict`, which reads that first line instead of the whole text for the pattern characters, the gap rule, the free-region test and the parameter-operator rule. The module docstring says so.
- `tests/test_gate_heredoc.py` (new): the recogniser, case by case, including each near miss.
- `tests/test_command_gate.py` and `tests/fixtures/gate_corpus.json` with `tests/test_gate_corpus.py`: the corpus cases of decision 5 of the record, and the tests of what `verdict` does with the shape.
- `docs/specs/command-permissions.md`: "The command gate" (the gap rule, item 4), and the "Limits" bullet that calls this a known false positive.

## Non-goals

- Shell interpreters and every other consumer of a here-document: `bash`, `sh`, `zsh`, `dash`, `eval`, `source`, `.`, `xargs`, `cat`, `tee`, `git commit -F -`, a redirect. They keep the gap rule on the body (decision 3).
- An unquoted delimiter, `<<-`, `<<<`, two here-documents, and any command line that is not the shape (decision 1).
- The names test, the `dollar-quote-limit` rule, the size limit, any level or key, the refusal log, and the harness's own `ask` rule.
- The limit the gate record already accepts: a python body can build a word at run time and run it, as a script file can (decision 4). This plan does not claim otherwise.
- A dated note on the accepted record. Its Decision section still opens "Proposed; the owner decides. Nothing here is built.", which the status line `Accepted` has overtaken. An accepted record is not rewritten; a narrow clarification is the owner's to approve (see Deferred work).
- The text in `AGENTS.md` that tells an agent to edit a file that holds a relaxed word with the edit tools. It stays true: a heredoc whose body writes the word is still refused by the names test.

## Assumptions and constraints

- The shape, matched in full on the raw text and in no other way (decision 1): optionally `cd <plain token> && `, where a plain token is the data position's grammar `_RUN_PLAIN` (`[A-Za-z0-9._/:=@,+-]+`), as the record says; then `python3` or `python`; then any number of the separate flags `-B`, `-I`, `-E`, `-u`; then `-`; then `<<` and a delimiter written `'TAG'`, `"TAG"` or `\TAG`; then a newline; the body; and the terminator. The record names no alphabet for the tag, so the tag is the agent's proposal and it is narrower than bash allows: `[A-Za-z_][A-Za-z0-9_]{0,31}`, so that no quoting trick (`E"O"F`, `EO\F`) can make the tag differ from the line that ends the body. A valid tag outside it (`E-F`, a tag over 32 characters) is not the shape and is judged as today, the safe direction; the corpus pins that boundary, and widening it is the owner's call. Nothing may follow the tag on the first line.
- The terminator is as bash reads it: the first line of the text, after the first line of the command, that is exactly the tag. That line must be the last line of the text, optionally followed by one final newline. Lines are split on `\n` only, as bash splits them, never by `str.splitlines`, which also splits on `\r`, `\x0b`, `\x0c`, `\x85` and ` `. A line that only looks like the tag (a trailing space or `\r`, another case, a leading tab) does not end the body; if no exact line ends the text, the text is not the shape. A line equal to the tag before the last line means text follows the terminator, and the text is not the shape.
- What is read, with the shape (decision 2). The first line is read by every rule as today. The names test, `substituted`, `decoded_views` and the `dollar-quote-limit` count read the whole text as today. Only the pattern test (`$ ? * [ {` and the backtick) and what hangs from it, the gap rule, the free-region test and the parameter-operator rule, read the first line and not the body. The first line holds none of those characters by construction, so for the shape those rules do not fire; the code makes that explicit by passing the first line, so that a later widening of the first line's grammar cannot silently free the body.
- The names test already refuses a body that splices the word with quotes: it reads the skeleton (letters and digits only), so `'wb rel' 'ease-approvals'` and `"wb rel" + "ease-approvals"` are both refused. A body that builds the word from variables, `chr` or `base64` is not seen, as in a script file; that is the accepted limit.
- `workbench/command_gate.py` is installer code, not a module of a package: the manifest does not list it, so no release approval, no stale-record removal and no upgrade is involved. The owner copies the changed files by a script with recorded hashes, as before. In this self-hosted project the live gate reads the copied code at once, so the copy of increment B changes what the gate does in this session. Editing is atomic (one file copied whole), because the hooks import the installer and a half edit would lock every tool.
- Nothing is pushed without the owner's word.

## Completion criteria

1. `python_heredoc(text)` returns the first line for the shape and `None` for everything else, including each near miss listed in increment A.
2. `verdict` does not return `gap` for a shaped command, whatever its body holds, and returns the same verdicts as today for every command that is not the shape, which the corpus and the existing tests show.
3. A shaped command whose body names a relaxed command, spelled out or with its parts spliced by quotes, is still refused by `names`; a shaped command with more than 64 `$'` strings is still refused by `dollar-quote-limit`; one over 64 KiB is still refused by `size-limit`.
4. The corpus holds the cases of decision 5: the false positive itself (a python body with reStructuredText docstrings) passes; refused: a body whose terminator is not exactly the tag followed by a line that spells a relaxed word through an expansion, `bash`, `sh` and `zsh` in place of `python3`, a command line before the here-document that holds an expansion, an unquoted delimiter, `<<-`, `<<<`, two here-documents, and the other near misses of increment A.
5. `docs/specs/command-permissions.md` states the shape, what is and is not read, and no longer calls the case a known false positive; `wb run code-work check` passes.
6. The owner has been asked whether to run a security review of the built change, as the record asks, and the answer is in the Result.

## Increments

### Increment A — Recognise the shape

**Outcome:** completion criterion 1 is true. The recogniser exists and is tested; `verdict` does not call it yet, so no verdict changes.
**Dependencies:** none.
**Affected areas:** `workbench/command_gate.py`, `tests/test_gate_heredoc.py`.
**Steps:**
1. Write `tests/test_gate_heredoc.py` first, in a scratch clone, and see it fail. Shaped, returning the first line: `python3 -` and `python -` with each of `-B`, `-I`, `-E`, `-u` and several together; `'TAG'`, `"TAG"` and `\TAG`; with and without `cd <plain token> && ` (a token with `@`, `:`, `=`, `,` and `+` included); with and without the final newline; an empty body; a body that holds backticks, `$(...)`, `${...}`, `*`, `[`, `{`, a quote, a backslash, a line that starts with the tag followed by other characters (`EOFX`), and a line with a trailing space (`EOF `). Not shaped, returning `None`: no terminator; the terminator with a trailing space, a trailing `\r`, another case or a leading tab; the tag line followed by another line, however harmless; the tag line followed by a command; the tag line twice; the terminator spelled with `\x0b`, `\x0c`, `\x85` or ` ` before it, which a `splitlines` would take for line ends; `bash`, `sh`, `zsh`, `dash`, `env python3`, `sudo python3`, `python3.13`, `/usr/bin/python3`; flags other than the four (`-c`, `-m`, `-S`, `-W`, `-X`, `-O`) and a flag stuck to another (`-BI`); an argument after `-`; an unquoted tag; `<<-`; `<<<`; two here-documents; a tag with a quote or backslash inside it, a valid bash tag outside the alphabet (`E-F`) and a tag longer than 32 characters (all judged as today); anything after the tag on the first line (`; id`, `> out`, `| cat`, a trailing space); `cd` with a path that is not plain (`$HOME`, `~`, a quote) or joined by `;`, `||` or `|` instead of `&&`; a NUL byte; and no newline after the tag.
2. Add `python_heredoc(text)` and its compiled pattern to `workbench/command_gate.py`, beside the other forms. It does no splitting by `str.splitlines`.
3. Run the verification. Ask the `reviewer` for a read.
**Verification:** `tests/test_gate_heredoc.py`, `tests/test_command_gate.py`, `tests/test_gate_corpus.py` and `tests/test_gate_hook.py`, run in the scratch clone; a mutation pass over the recogniser (the terminator compared with `strip`; `splitlines` for `split("\n")`; the quote requirement dropped; the flag list widened; the tag alphabet widened; the last-line rule dropped) in which every mutant fails a test; `wb run code-work check`. Not run: the whole suite (the function is not called).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-python-heredoc-gate#A`.

### Increment B — Read the first line, not the body

**Outcome:** completion criteria 2 to 5 are true.
**Dependencies:** A.
**Affected areas:** `workbench/command_gate.py`, `tests/test_command_gate.py`, `tests/fixtures/gate_corpus.json`, `tests/test_gate_corpus.py` if its group list needs a group, `docs/specs/command-permissions.md`.
**Steps:**
1. Write the tests and the corpus cases first, in the scratch clone, and see the ones that must pass fail. Corpus: the false positive (a sanitised python body with reStructuredText docstrings and about thirty double backticks) passes at `ask` and at `none`; the refusals of criterion 4; a body that writes a relaxed command in full, and one that splices it with quotes, refused by `names`; a body that holds `$'` more than 64 times refused by `dollar-quote-limit`; the same body without the shape refused by `gap`, to show that the shape is what frees it. `test_command_gate.py`: a shaped command is never refused by `gap` whatever the body holds (a table of bodies, and a generated pass over many bodies built from the characters `` ` $ ( ) { } [ ] * ? \ ' " `` and letters of each relaxed word); the verdict of a shaped command equals the verdict of the same command with its body replaced by the same body in a form the names test alone reads (so the two differ in no rule but `gap`); the first line is still read (`python3 - <<'EOF'` after `FOO=$(true)`, an expansion in the `cd` path and a glob in a flag are not the shape and are judged as today); a block-level run still lets everything through.
2. In `verdict`, call `python_heredoc(text)`; read `head or text` for `pattern`, `wilds`, `expands`, `frees` and `ordered`. Everything else in `verdict` keeps reading `text`. Update the module docstring. Write the file whole and atomic.
3. Update `docs/specs/command-permissions.md`: item 4 of "The command gate" gains the shape and what it frees and does not free; the "Limits" bullet "A known false positive" becomes a statement of what is freed and what remains (shell interpreters and other consumers still read, a script that builds the word is not seen); the Limits bullet about "a heredoc to `python3 -`" is made consistent. Link the record.
4. Run the verification. Ask the `reviewer` for a read, with the near-miss list of increment A and the corpus.
5. After the owner's copy, run one harmless python heredoc that holds double-backtick docstrings and names nothing, through the live gate, and record that it ran; run a second whose body writes a relaxed command's words, and record that it was refused. The second never runs: the gate refuses it before the shell sees it.
**Verification:** `tests/test_gate_heredoc.py`, `tests/test_command_gate.py`, `tests/test_gate_corpus.py`, `tests/test_gate_hook.py`; the mutation pass of increment A repeated against `verdict` (the body read in full again; the head read where the names test should read the whole; `head or text` for `text` in `substituted` or `decoded_views`); the corpus test that a case recorded the other way is noticed; `wb run code-work check`. Before any wider run I tell the owner what could break outside this area: the gate is imported by `gate_hook` and by the rendered hooks of every attached project, so a crash blocks every Bash call; a run of `tests/test_rendering.py` and `tests.test_permissions_drift` would show whether rendering is touched, and I would ask first. Not run: the whole suite.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-08-python-heredoc-gate#B`.

## Verification for the plan as a whole

The recorded verification of increments A and B stands, with the two live heredocs of step 5 of B. Whether the refusals stop recurring is for the owner to see in the next sessions. The refusal log (`gate-log`, a rule and a short hash per refusal) will show whether `gap` refusals fall.

## Risks and sensitive actions

- **A parser mistake is a bypass.** The record says so: text the gate takes for body that bash takes for a command would escape the gap rule. The defences are the exact terminator rule (first exact line, which must be the last), line splitting on `\n` only, a tag alphabet with no quoting, a first line with nothing after the tag, and the near-miss tests and mutations of A and B. The names test still reads everything. A security review of the built change is recommended by the record and by this plan; it runs only on the owner's word (criterion 6), and its findings would be fixed in a further increment with a regression test.
- **The accepted limit is unchanged, not widened.** A python body can build a relaxed command's name at run time (`chr`, `base64`, a variable) and run it; the gate does not see that in a script file or in this form. Before, the heredoc form was also read by the gap rule, which saw `$`-expansions a python body does not use; after, it is not. The names test stays the barrier for a body that writes the word.
- **A bad edit locks every tool.** The hooks import the installer. The change is made in a scratch clone, tested, and copied whole by a script that checks recorded hashes; the owner's terminal is the recovery.
- **The copy changes this session's gate.** After the copy of B, this session's Bash calls are judged by the new code. That is intended; step 5 of B checks it with two calls.
- No credential, network or filesystem write by the code is added. The tests write only to temporary files they create.

## Review record

Codex, plan review, 2 rounds of 3 (the bound); converged with no meaningful finding in round 2. Model: `gpt-5.6-terra` for both rounds.

- Applied (round 1, major): the plan's shape was narrower than the record's. The `cd` path now uses the record's plain-token grammar (`_RUN_PLAIN`), with corpus cases for `@`, `:`, `=`, `,` and `+`.
- Applied in part (round 1, major): the tag alphabet. The record names none, so the plan keeps its narrower proposal, which frees less and fails safe (a valid bash tag outside it is judged as today), now says so in the shape bullet, and pins the boundary in the tests (`E-F`, a tag over 32 characters). Widening it is the owner's call.
- Left for the owner: whether to widen the tag alphabet, and the dated note on the accepted record (Deferred work).

## Deferred work

- A security review of the built change, on the owner's word (criterion 6).
- A dated note on the accepted record `2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps` saying that its Decision section's first line, "Proposed; the owner decides. Nothing here is built.", is overtaken by the status line, and that the tag alphabet is `[A-Za-z_][A-Za-z0-9_]{0,31}`. A clarification of an accepted record needs the owner's approval.
- Other consumers whose body can be shown to be data (`cat <<'EOF'` to the screen), each by a later record (decision 3).
- Whether the guidance that tells an agent to write a script with the editor tool should say that a python heredoc now passes, once the owner has seen it work.

## Result

Empty until work starts.
