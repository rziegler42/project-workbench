# A python script written as a quoted heredoc is read for the words it holds and not for gaps

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-03
Date: 2026-11-03

## Context

The command gate (`2026-11-02-command-gate-reads-gaps-and-data-positions`, accepted) refuses a command that spells a relaxed
command through wildcards: when the text holds any of `$ ? * [ {` or a backtick, it looks for the letters of the word with nothing
between two of them but wildcards (the gap rule), and inside an expansion `$(...)`, `${...}` or a backtick pair it lets other
characters sit between the letters (`_free_match`). That decision accepted, in writing, that a script file or program that makes
the call is not seen (`command-permissions.md`, "Limits").

A python script fed to `python3 -` through a heredoc is such a program. Its text is also read by the gap rule, as if it were shell
words, and that produces a false positive the owner and the author met while working on the plan
`2026-11-02-permission-system-consistency`: a 3 KiB script, quoted-delimiter heredoc, that rewrote one function of a module was refused
for `wb release-approvals` although it names no command and builds none. The cause is the backticks. A reStructuredText docstring
writes a name as ``name``, and the gate reads each pair of backticks as a command substitution, collapses it to wildcards, and lets
the letters of the docstring serve as padding inside it. The letters of `releaseapprovalsworkbench` (the key and a launcher word, read
in either order for a `wb <word>` key) are common enough that a long text finds them.

Run on 2026-11-03 against the gate of the working tree (see Evidence): the script was refused by the gap rule; the same text with its
double backticks removed passed; with every backtick removed it passed; removing only the triple quotes of its docstrings did not help.
A shorter python heredoc that held `[`, `{`, `$` and `*` and no backtick passed. Two things follow. The false positive is about backticks
in a body that no shell ever expands. And the owner's way round it, writing the script with the editor tool and running it as a file,
is a call the gate already lets through with no reading of the file at all, so the heredoc is the one spelling of the same act that is
read, and refused for nothing.

What bash does with a quoted heredoc matters for how far this can go. With a quoted delimiter (`<<'EOF'`, `<<"EOF"`, `<<\EOF`) the
shell that reads the command line expands nothing in the body. What happens to the body then depends on what reads it. `python3 -` runs
it as python: no shell expansion, no substitution by backticks. `bash <<'EOF'` runs it as a shell script, which expands everything in
it: run on 2026-11-03, a body `echo $(echo ins)tall` printed `install`. So a quoted heredoc is data for the outer shell and code for the
inner one, and only the inner interpreter decides whether the gap rule's worry (an expansion that builds a word) applies.

## Decision

Proposed; the owner decides. Nothing here is built.

1. **A quoted here-document body that is fed to the python interpreter is not read by the gap rule.** The shape, exact and matched on
   the raw text: one simple command, optionally preceded by `cd <plain path> && ` (the grammar of a plain token of the data position),
   that is `python3` or `python`, with only the flags `-B`, `-I`, `-E` or `-u`, then `-`, then a here-document whose delimiter is
   written quoted (`'TAG'` or `"TAG"`) or escaped (`\TAG`), the body, and the terminator line, with nothing after the terminator
   but a final newline. The terminator is a line that is exactly the tag, as bash reads it; anything after it, a line that only
   looks like the tag (a trailing space, a different case), a second here-document, `<<-`, `<<<`, a here-document with an unquoted
   delimiter, and every other command line are not this shape and are judged as they are today.
2. **What is still read.** The first line, the command up to the here-document, is read by every rule as before. The whole text,
   body included, is read by the names test as before: a body that writes `wb release-approvals`, or any word of a relaxed key, is
   refused (decision 3 of the gate record stands: a heredoc that writes text naming a command stays refused, here as there). Only
   the gap rule and the free-region test do not read the body.
3. **Shell interpreters are not covered.** `bash`, `sh`, `zsh`, `dash`, `eval`, `source`, `.`, `xargs` and any other command that
   runs the body as shell words keep the gap rule on the body, as do all other consumers of a heredoc (`cat`, `tee`, `git commit -F -`,
   a redirect). A consumer may be added by a later record when its body can be shown to be data.
4. **The accepted limit is the ground, not a new belief.** The record does not claim that a python body cannot build a word at run
   time and run it: it can, as `python3 x.py` can, and that is the limit the gate record accepted for a script file. What changes is
   that the one-call spelling of the same act is no longer refused for letters it shares with its docstrings.
5. **The corpus and the tests come first when it is built.** Cases for the attempts the new shape must not let through: a body
   whose terminator is not exactly the tag with a relaxed word spelled through an expansion on the next line; `bash` and `sh` in place
   of `python3`; a command line before the here-document that holds an expansion; a here-document with an unquoted delimiter; `<<-`;
   two here-documents; and the false positive itself (a python body with reStructuredText docstrings), as a passing case.

## Alternatives considered

- **Leave it and write the script with the editor tool (today).** It works and nothing in the gate changes. It was the author's
  way round in this session more than once, each time at the cost of a second tool call and of a refusal first. It leaves the heredoc as
  the only spelling of the act that is read, so it refuses the harmless and not the file. Not chosen, but it is the fallback.
- **Free the body of every quoted here-document.** Rejected: `bash <<'EOF'` expands the body (shown above), so it would let a shell
  spell a word through an expansion with no reading at all, and the gap rule exists for exactly that.
- **Read a doubled backtick pair differently.** Treat ``name`` as text and a single pair as a substitution. Rejected: in bash a pair
  of adjacent backticks is two empty command substitutions, so `` wb inst``all `` is a legal spelling that the change would stop seeing;
  and a single-backtick markdown span in a python string would still be read as a substitution.
- **Narrow the free region inside backticks.** Let only `$(...)` and `${...}` carry padding. Rejected: a backtick pair is a command
  substitution and the padding it strips (`` `echo ZZinst | cut -c3-` ``) is the case that decision I added `_free_match` for.
- **Add `cat <<'EOF'` and the other data consumers now.** Not chosen: a `cat` that writes a file by redirect is a different act from
  one that prints, and the decision should be as narrow as its evidence; the python case is the one met.

## Consequences

- Good: a python heredoc that edits or checks a file passes whatever its docstrings and strings hold, without a second call.
- Good: the change is narrow and each of its limits is a line of the corpus.
- Bad: it relies on the accepted limit that a script can spell a word the gate does not see. A python body can build `release-approvals`
  from pieces and call it. The gate did not see that in a script file before; it does not see it in this form now. The owner decided
  that limit; this record does not widen what is possible, only what is read.
- Bad: it adds a parser of here-documents to the gate. A mistake in where the body ends is a bypass: text the gate takes for body that
  bash takes for a command. The decision therefore asks for the exact terminator rule, tests for the near-misses and the intended
  security review of the built change. The author recommends the review.
- Bad: the false positive is shown for one script; the claim that the backticks are the whole cause is from removing text, and it
  holds for that script. Another body could trip the names test or the pattern rule through another route, and would be refused as
  today.
- Neutral: nothing changes for a command that has no here-document.

## Evidence

Run on 2026-11-03 at commit `76d7294`, workbench 0.1.0, Python 3.15.0, against `workbench/command_gate.py` of the working tree: one
scratch script that loaded the refused command's text from a file and called `command_gate.verdict` with `wb release-approvals`,
`approve-plan` and `wb run review-engine extend` relaxed at `ask`. As sent (2,973 characters, 38 backticks): refused, rule `gap`, key
`wb release-approvals`; `approve-plan` and the review-engine key passed. With every pair of double backticks removed: passed. With every
backtick removed: passed. With the triple quotes of its docstrings replaced: refused. A second heredoc (`python3 - <<'PYEOF'` printing a
formatted line, with `[`, `{`, `$` and `*` in its text) ran through the live gate and printed its line. `bash <<'EOF'` with the body
`echo $(echo ins)tall` printed `install`. The scripts were not kept. Read: `workbench/command_gate.py` (`_collapse`, `_segments`,
`_free_text`, `_free_match`, `verdict`), `docs/specs/command-permissions.md` ("The command gate", "Limits"). Not run: any change to the
gate; a security review; other scripts that might be refused for another reason.

## Related files and decisions

- `docs/plans/2026-11-02-permission-system-consistency.md` (Result of Increment M, the walk-through of the heredoc example)
- `docs/specs/command-permissions.md` ("The command gate", "Limits")
- [2026-11-02-command-gate-reads-gaps-and-data-positions](2026-11-02-command-gate-reads-gaps-and-data-positions.md)
- [2026-10-27-command-gate-literal-arguments](2026-10-27-command-gate-literal-arguments.md)
