# Let the owner label a command the engine declined for a secret, without keeping the secret

Status: Proposed
Created: 2026-11-07
Candidate: workbench-v1#shadow-label-secret-declines
Specs: action-review

## Goal

A command the engine declines for `no_secret_lines` or `paths_not_credentials` can be labelled right or wrong. After this plan the shadow hook writes, for such a command, one handle row built from a fixed list of fields that hold no secret, the labelling tool shows it as a handle, and the report counts the labelled handles apart from ordinary commands and says whether they were folded into the rate. The design is "Labelling a declined secret" in `docs/specs/action-review.md`, decided by the owner on 2026-11-07: an allowlist and not a redaction, the engine unchanged, handle labels counted apart until the owner says to fold them.

The reason is the share of the evidence that is out of reach. On 2026-11-07 the report counted 65 of 187 reviewed commands as reviewed but not collectable, every one a decline for `no_secret_lines`. The false-decline rate and the cutover bound rest on labelled commands only, and the hook is registered for the owner's whole account, so the share grows with every project that works with secrets.

## Scope

- `packages/workbench/action-review/tools/report.py` and its tests: recognise a handle row, count the labelled handles apart, an option that folds them, and the line that says which.
- `packages/workbench/action-review/tools/label.py` and its tests: show a handle as a handle.
- `packages/workbench/action-review/hook/shadow_hook.py` and its tests: build and write the handle, from an allowlist, for a command declined for a secret; read the project's git index to decide which paths may be kept; pass the directory the command ran in to `record`.
- The pin of `hook/shadow_hook.py` in `helper/action-review` (`PINS`) and the test that pins it.
- `docs/specs/action-review.md`: the sentences that say a declined secret is never collected or can never be labelled, the data-file passage, the report passage and the owner's labelling step. The section "Labelling a declined secret" changes from proposed to built.

## Non-goals

- The engine, its secret scan, its checks and its rules. The engine keeps returning only whether it hit; the kind and the file of a hit are not asked of it (the owner's decision of 2026-11-07).
- The redactor for other commands, and what is stored for a command that is not a declined secret.
- `shadow_store.py` and the format of the data files. A handle is a row the existing `collected.jsonl` format already accepts, so the store and its pin do not change.
- The cutover decision, the bound, and folding handles into the rate. Folding happens only through the option the owner passes.
- Labelling the 65 commands already recorded. Their rows hold no text and no facts, so nothing can be recovered; they stay counted as not collectable. Only a command declined after the owner installs the new hook leaves a handle.
- A change to `store.py`'s rules, the hook that decides, the push rule and the test-set runner.

## Assumptions and constraints

- A handle is a row of `collected.jsonl` with these fields, none of them taken from the command text, the diff, the subject, the body, the trailers or the model's reason: `id`, `ts`, `rule` (the engine's, from its log row; a decline whose rule is not a string leaves no handle, as now), `command_sha256`, `command` (the fixed text `[declined for a secret; the command is not kept]`), `verdict` (`decline`), `failed_checks`, `reason` (a fixed text) and `facts`, an object `{"handle": true, "facts": {...}}` whose inner object holds only `confirm`, `paths` and `paths_dropped`. There is no project name: a directory name is a string the hook cannot prove harmless, and the owner knows the project from the time. The names and the shape are the agent's proposal; the store's schema already allows them (`command` text up to 4,096, `facts` an object, `reason` text up to 300).
- **A path is kept only if it is a path the project already tracks (decided by the owner on 2026-11-07, after the first review round).** The redactor is not the rule, because it cannot name every secret shape. The candidate paths are the union of the path lists of the facts (`paths`, `requested_paths`, `target_paths`, read from the engine's object, where `facts.facts` holds them), in first-seen order and deduplicated. A candidate is kept when it is printable ASCII, at most 256 characters, relative, free of `..` and of a leading `-`, and either equal to a path in the git index of the repository the command ran in, or a directory that is a leading part of at least one such path. A secret that is already a tracked filename is already in the repository, so keeping it adds no new exposure. Every other candidate is dropped and counted in `paths_dropped`, never shortened; at most 20 are kept. A new file that is not yet tracked is therefore never shown; the owner finds it from the time. The caps are the agent's proposal.
- **The index is read in the hook's own process, with no program started.** The repository is found by walking up from the command's directory, one directory at a time, and the path is resolved by descriptors, as `shadow_store.py` resolves its own directory: each directory is opened with `O_NOFOLLOW | O_DIRECTORY` relative to the descriptor of its parent, and `.git` is opened the same way from the descriptor of the directory that holds it. A `.git` that is a file (a worktree or a submodule), a link, or anything else that is not a directory gives no index and keeps no path. `index` is then opened with `O_NOFOLLOW | O_NONBLOCK` relative to the verified `.git` descriptor (the non-blocking flag so that a FIFO with no writer cannot hold the hook; `shadow_store.py` opens its files the same way), and the opened descriptor, not the name, is checked with `fstat`: a regular file with one link, owned by the current user, at most 32 MiB. No check is made on a name and then acted on by name, so a swap after the check cannot change what is read. the reader accepts index versions 2 and 3, checks the header, the entry count against the size and the trailing checksum, and stops at the first fault, with a bound on the work. Version 4, a split index, a sparse index and any parse fault keep no path. A project controls this file, so it is untrusted input: it is read as bytes and never executed, and nothing in it chooses a path the hook opens.
- Everything not on the list is ignored, whatever the facts hold or call it. No loop copies a key from the facts.
- When a handle cannot be built, or its line would be refused by the store, no handle is written, the verdict row stays as now, and the hook notes it on standard error in fixed text that quotes nothing. The hook never changes its exit status and never decides.
- A handle with no path (the facts were missing, or every path was dropped) is still written, so the owner can count it and skip it. This is the agent's call.
- The marker is the boolean `facts["handle"]`. The report reads that one boolean and `facts.facts.confirm` of a handle, nothing else of the facts, as `is_preview` reads one.
- The programs in `~/action-review-shadow` are the owner's read-only copies. The owner replaces `report.py` and `label.py` there before replacing `shadow_hook.py`, so that no handle exists before the tools know it. Increment order follows that order.
- The package changes under `packages/`: the release approvals, the removal of stale shipped records after the owner approves the list, the upgrade and the rerender are the owner's. Each increment is built and tested in a scratch clone and copied by the owner's script, as in the earlier plans. Nothing is pushed without the owner's word.
- Tests are run as `python3 -B` discovery on the module's tests directory, and the plan check as `wb run code-work check`.

## Completion criteria

1. A command the engine declines for `no_secret_lines` or `paths_not_credentials` leaves exactly one handle row in `collected.jsonl` besides its verdict row, and no other collected row.
2. A handle holds only the fields named above, and every path in it is a path of the project's git index or a directory above one. A test feeds hostile facts through the hook (a secret shape in a path that is not tracked, in a key, in every other fact; a path over 256 characters; a character outside printable ASCII; a control character; `..`, an absolute path, a leading `-`; more than 20 paths; facts that are not an object; facts nested deeper than expected) and finds no field outside the list and no untracked string in the row. A second set feeds hostile indexes (a link in place of the file, a file over the cap, a truncated file, a wrong checksum, an entry count that does not fit the size, version 4, a `.git` file, a `.git` directory that is a link, an `index` that is a link, a non-regular file, a FIFO with no writer (rejected promptly, inside a time limit the test sets), a file with more than one link, a file of another owner, and a `.git` directory or an `index` replaced by a link between the discovery of the repository and the open of the index) and finds that each keeps no path and leaves the hook's exit status and its other rows as they were.
3. A command that is not a declined secret is collected exactly as before.
4. The report counts the labelled handles in their own entry, apart from the ordinary actions and from the previews; without the option the per-action counts, the cutover bound and its verdict are unchanged; with the option the handles are folded into the counts of their action; the output says `handles: apart` or `handles: folded`.
5. The report's "reviewed but not collectable" count falls by the handles written, and its by-check line is unchanged for the rest.
6. The labelling tool shows a handle as a handle (the rule, the failed checks, the paths and the time), says the owner may look at the change in that project or skip, accepts `right`, `wrong` and `skip`, and runs no program.
7. The spec's sentences that said a declined secret is never collected or never labelled now describe the handle, and a test pins them against the hook.
8. `wb run code-work check` passes, and the module's tests pass.

## Increments

### Increment A — The report counts handles apart

**Outcome:** completion criteria 4 and 5 are true for a store that holds handle rows.
**Dependencies:** none.
**Affected areas:** `packages/workbench/action-review/tools/report.py`, `packages/workbench/action-review/tests/test_tools_report.py`, `docs/specs/action-review.md` (the report passage of "Labelling and the report" and the line of "The data files" that describes the count).
**Steps:**
1. Write the tests first, in a scratch clone: a labelled handle is in the handle entry and in no action entry and not in the previews; without the option the per-action counts, the cutover bound and the verdict equal those of the same store without the handles; with the option the handle is in its action's counts, and a handle whose rule is a removal is not taken for a preview; the output says `handles: apart` or `handles: folded`; a handle waiting for a label and a skipped handle are counted as waiting and skipped; a collected row with no `handle` marker is unaffected whatever its facts hold; the report reads no fact of a handle other than the marker and `confirm`; the count of not collectable falls by a handle that has a collected row. See them fail.
2. Add the marker test, the separate entry, the `--fold-handles` option and the output line to `report.py`. An unknown option is refused as now.
3. Edit the two passages of the spec. Search the repository for another description of the report's output (`docs/development.md`, the module's README or skill) and change one only if it states the old output.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_tools_report.py` and the rest of the `action-review` module suite; `wb run code-work check`. Not run: the whole suite (no installer code changes), the hook tests beyond the module suite.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-07-label-declined-secrets#A`.

### Increment B — The labelling tool shows a handle

**Outcome:** completion criterion 6 is true.
**Dependencies:** A (the report's marker is the one the tool reads).
**Affected areas:** `packages/workbench/action-review/tools/label.py`, `packages/workbench/action-review/tests/test_tools_label.py`, `docs/specs/action-review.md` (the owner's labelling step and the sentence of the labelling passage that says a declined secret is never collected).
**Steps:**
1. Write the tests first: a handle row is shown with its rule, failed checks, paths and time, and a line that says the owner may look at the change in that project (for example with `git diff -- <paths>` there) or skip; `r`, `w` and `s` record a label as for any row; no program is started (the existing test that the tool starts none covers the new path); the facts of a handle are shown through the same display cleaning as any other; a row without the marker is shown as before.
2. Add the display and the hint to `label.py`.
3. Edit the two places of the spec.
4. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_tools_label.py` and the module suite; `wb run code-work check`.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-07-label-declined-secrets#B`.

### Increment C — The hook writes the handle

**Outcome:** completion criteria 1, 2, 3, 7 and 8 are true.
**Dependencies:** A and B.
**Affected areas:** `packages/workbench/action-review/hook/shadow_hook.py`, `packages/workbench/action-review/tests/test_hook_shadow_hook.py`, `packages/workbench/action-review/tests/test_hook_redact.py` if the redactor's test needs a case, `packages/workbench/action-review/helper/action-review` (the pin of `hook/shadow_hook.py`), the pin test, and `docs/specs/action-review.md` (the passages that say a declined secret is never collected or can never be labelled, near the lines about the collected file, "Redaction", the owner's steps and the recorded limits; "Labelling a declined secret" changes from proposed to built).
**Steps:**
1. Write the tests first: a declined secret leaves one handle and no other collected row, with the fields named above and nothing else; each hostile input of criterion 2 leaves a row without the sentinel and without a field outside the list; a path that is not in the index is dropped and counted, even when it is plain ASCII and looks harmless; a tracked path and a directory above one are kept; a path that was staged and then removed from the index is dropped; more than 20 paths keep 20 and count the rest; facts that are not an object leave a handle with no path; each hostile index of criterion 2 keeps no path, the swap cases among them (the test replaces the directory or the file with a link through a hook point between the steps, so the case is run and not argued); the hook starts no program to read the index (a test fails if a subprocess is started on this path); a line the store would refuse leaves no handle and a fixed note on standard error; an ordinary command is collected as before; a decline for something else is collected as before; the verdict row of a declined secret is unchanged. A test pins the spec sentences that now describe the handle. See them fail.
2. Pass the directory of the command from `run` to `record`, add the index reader and the admission rule of the assumptions, build the handle from the allowlist, and write it in place of the skip. The builder copies named fields and never iterates the keys of the facts.
3. Update the pin of `hook/shadow_hook.py` in the helper, and the pin test, to the new hash of the shipped file. `shadow_store.py` and its pin do not change.
4. Edit the spec. Search it for each sentence that says a declined secret is never collected or labelled and change those that state the old behaviour. Report a sentence that now disagrees with the code and is not in the list.
5. Run the verification below and ask the `reviewer` for a read.
**Verification:** `test_hook_shadow_hook.py`, `test_hook_redact.py`, the pin test and the rest of the module suite; `wb run code-work check`. After the copy and the release, `wb verify packages/workbench` shows the new tree hash for `action-review`. Not run: the whole suite, and the engine tests beyond the module suite; the engine and its scan do not change.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-07-label-declined-secrets#C`.

## Verification for the plan as a whole

The recorded verification of each increment stands unless a later one changed its inputs. After the last increment the module suite runs once and `wb run code-work check` runs. Whether the handles answer the owner's question on the real store is for the owner to see: after the owner replaces the tools and then the hook in the dedicated directory, new declines leave handles, and the report shows them apart.

## Risks and sensitive actions

- **Secrets.** The change decides what the hook may write about a command that holds a secret. Two controls: the allowlist (a field not on the list cannot reach the row) and the admission rule (a path is kept only if the project already tracks it, so the handle adds no string that the repository does not already hold; the redactor is not relied on). What remains: a secret that is already a tracked filename is repeated in the handle, in a file that is not the repository (mode 0600, outside every project); and the owner sees fewer paths, because a new file that is not tracked yet is never shown.
- **A new read of untrusted input.** The hook now reads `.git/index` of the project the command ran in, and a project controls that file. The reader opens it without following a link, accepts only a regular file of the current user within a size cap, parses with bounded work, and starts no program. A fault keeps no path and changes nothing else. This is a new surface in a hook that runs for every project, so a security review is owed; it runs only if the owner asks.
- **The hook is user-level and runs on every Bash command of every project.** A fault in the new code could make the hook slow or write a bad row. The hook catches every error and never changes its exit status; the store refuses a bad line and the hook notes it. The tests cover a failing builder.
- **Judging from less.** A handle gives a path and a time. The owner may skip often. Counting handles apart keeps the bound from resting on them silently.
- **Copy order.** If the owner replaces the hook before the report and the labelling tool, handle rows exist that the old tools show as ordinary rows. The increments are ordered A, B, C so that the tools come first; the plan's Result says so when it reports.
- **A package file changes:** the release approvals, the removal of stale shipped records after the owner approves the list, the upgrade and the rerender are the owner's. The copies in `~/action-review-shadow` are the owner's to replace. Nothing is pushed without the owner's word.

## Review record

Codex, plan review, 3 rounds of 3 (the bound); not converged: every round found one meaningful finding, each applied, and the last change was not re-read. Models: `gpt-5.6-terra` for rounds 1 and 2, `gpt-6.1-sol` for round 3.

- Applied (round 1, blocker): the allowlist kept a path or the project name whenever the redactor left it unchanged, and the redactor cannot name every secret shape. The owner chose, on 2026-11-07, to keep a path only if the project already tracks it (read from the git index in the hook, no program started) and to drop the project name. The plan, the criteria, the tests, the risks and the spec section changed.
- Applied (round 2, major): the index was to be opened without following a link, but not by descriptors, so a swap between the check and the open was possible. The plan now resolves `.git` and `index` by no-follow descriptors from the verified parent and checks the opened descriptor; the hostile-index tests add the link and swap cases.
- Applied (round 3, major): a FIFO in place of the index could hold the open. The plan now opens the index with `O_NONBLOCK`, as `shadow_store.py` does, and tests a FIFO with no writer.
- Rejected: none.
- Left for the owner: the review is at its bound of 3 rounds and the fixes of rounds 2 and 3 were not read by a later round. Whether to ask for more rounds (`extend`) or to approve as it stands is the owner's. A security review of the built hook is owed and runs only if the owner asks.

## Deferred work

- The kind and the file of the hit, which the engine's scan could return so that a handle names them. The owner decided on 2026-11-07 that the engine does not change; a later candidate may ask again.
- Labelling the 65 commands already recorded: their rows hold nothing to recover.
- Showing the paths of new files that are not tracked yet, and the name of the project: neither can be shown without a string the hook cannot prove harmless.
- A rule for folding handles into the rate by default, which is the owner's cutover decision.

## Result

### Increment A — The report counts handles apart (built in a scratch clone at `a83a783`, 2026-11-07; not yet in the live tree)

- **Changed:** `tools/report.py` (`is_handle`, a handle entry in `tally`, `handle_line`, the option `--fold-handles` accepted alone, the module docstring), `tests/test_tools_report.py` (class `Handles`, 17 tests; the source test that limits which facts the report reads now allows `handle` in `is_handle` and still allows `confirm` only in `is_preview`, and names `paths` as never read), `docs/specs/action-review.md` (the report passage of "Labelling and the report" and the "As built" paragraph of the report, which now takes the one option), `docs/development.md` (one table row).
- **Verification run** (`python3 -I -B`, a runner that imports the clone's code): `test_tools_report.py` 92 tests pass (75 existed; the 17 of `Handles` are new, two of them added after the review). Before the code change, the first 15 failed or errored except two guards that pass on the old code (13 failures, 1 error in the run). A mutation check of nine changes to `report.py` (marker accepted for any value or never, a handle always or never folded, a false approve lost apart, any argument accepted, a removal handle taken as a preview, skipped handles not counted, the handles line always printed) was killed by the tests every time. The whole `action-review` module suite: 820 tests, 1 failure, `test_hook_shadow_hook.Launcher.test_the_environment_holds_exactly_path_home_and_lang` (`__CF_USER_TEXT_ENCODING` in the recorded environment), which fails identically on the unchanged tree with the changes stashed; it comes from the environment the tests were run in and not from this increment. Not run: the whole repository suite (no installer code changed), `wb run code-work check` (it runs from the live tree after the owner's copy).
- **Deviation:** the plan listed "the line of 'The data files' that describes the count" among the spec passages. It is unchanged: the sentences there (a declined secret is never collected and can never be labelled) stay true until Increment C, which rewrites them. The report passage says that a handle removes its command from the "not collectable" count.
- **Behaviour to know:** apart, the met-or-not verdict, the rate and the minimum are exactly those of a store without handles; the "still waiting" suffix of a met cutover line counts waiting and skipped handles as it counts any waiting command, and the spec and a test say so. A handle row that says approve and is labelled wrong blocks the cutover in either mode, counted once.
- **Review:** the `reviewer` agent, one exchange, no blocking finding. Applied: a test that the "still waiting" suffix counts waiting and skipped handles while the verdict is unchanged; a test that the alarm counts a folded handle's false approve once and that the handle line shows it; a test that folded waiting and skipped handles are counted as such; a sentence in the spec that the suffix includes handles. Not applied: the reviewer noted the source test cannot see an access through a non-literal key; accepted, as for the existing check. Not checked by the reviewer: it ran nothing, and I ran the tests and the mutation check.
- **Copy and release (the owner's):** the owner copies the four files with a script that checks each source against its recorded hash, makes the release approvals, and replaces the report in `~/action-review-shadow` after the release and before the hook is.
