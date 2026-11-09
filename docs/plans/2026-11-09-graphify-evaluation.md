# Find out from real work whether a graphify module would help, before building it

Status: Proposed
Created: 2026-11-09
Candidate: workbench-v1#graphify-module
Specs: graphify

## Goal

The owner was "never happy with how little graphify actually helped" and the spec `graphify` (approved 2026-11-09) gates the module on evidence. After this plan the owner has, on real changes from their own projects (the semantic layer was dropped from the design on 2026-11-09 and is not tested here): a set of structure and impact questions with the files each real change touched as ground truth, which the owner reviewed; a measurement of how often the structural graph that the new module would use (the program's `update`, no model) names those files, how much it names that was not touched, and what `grep` alone gives for the same questions; a split of the questions into those `grep` answers and those it does not, because the owner's measure is return on compute and `grep` is nearly free; three checks that an online search of 2026-11-09 suggested (below): whether an incremental `update` leaves nodes of deleted code in the graph, what the program writes outside the output folder it was given, and how much of each graph is real relations and not plain containment; and a go or no-go decision of the owner's. Nothing of the module is built here. If the owner says no-go, the candidate is closed with this evidence. If go, the module gets its own plan, after the spec's final review round that this plan runs.

## Scope

- A question set, kept in this plan's Result under "The question set" (not under `docs/references/`: its index is for external material with a URL, a licence, a retrieval date and a hash, and these are the project's own derived records): 20 questions, each with its project, the commit before the change, the commit that made it, the symbol or module asked about, the kind (impact or structure), the language, and the ground-truth files. It holds **exactly 20 questions the owner approved** (the number the graphify spec's evaluation names); the owner reviews and corrects it.
- A measurement run, on scratch copies, with the results kept in this plan's Result under "The results".
- The spec's final review round (the spec says one more round runs before any module file is written) and the owner's decision.

## Non-goals

- Writing any file of the module: its declaration, helper, skill, policy block or tests. That is a later plan, and only on a go.
- Running the program in the owner's projects. Every run is on a scratch copy; no `graphify-out/` appears in any project, and nothing in a project changes.
- Any model call or key. The program's `update` needs none; `extract`, `label` and every other model-backed command are not run.
- The semantic layer. The owner dropped it from the design on 2026-11-09 (the spec, "Decisions of the owner"), so the plan neither tests it nor reads the old two-layer graphs for it; the reads that led to the decision are in the spec's evidence.
- Changing the roadmap, the spec's decisions or the module contract. Closing the candidate or answering decisions 2 and 4 of the spec is the owner's act after the evidence.

## Assumptions and constraints

- **The questions come from real changes (my call).** For `m65c02`, `m65c02risc` and this project, a question is built from a commit that changed an interface the rest of the code used: a function or module whose callers or users also had to change. Selection rule, stated before looking at any result: commits of the last six months that changed two to thirty files of source, not documents only, not generated files, not merges, not a mass rename; from each project the author lists candidates in date order and takes the first that fits, skipping none for any reason that depends on what the graph would answer. Mix: 8 from `m65c02risc`, 8 from `m65c02`, 4 from this project, so that the Verilog work, where the earlier graph failed, is represented in proportion to its use. **Replacement rule:** the author lists at least 30 candidates in date order, 12 from each old project and 6 from this one, and takes the first 8, 8 and 4 that qualify; when the owner drops or corrects away a question, or one turns out to have no scorable ground-truth file, the next candidate of the same project in date order replaces it, until there are exactly 20 the owner has approved. If a project has too few qualifying commits, the shortfall is reported to the owner, who decides the mix; the plan does not shrink the count.
- **The symbol asked about is chosen by a stated rule (my call).** The changed definition or module with the most added and removed lines in the commit, among those that other files refer to. The owner reviews every choice. The question is phrased as the agent would ask the module (`affected "<symbol>"`, or `query "<what depends on ...>"`), once, with no retry.
- **Ground truth is the files the real commit touched, minus documents and generated files, and only those that exist at the parent revision are scored.** The graph and `grep` run on the parent commit, so a file the commit adds cannot be found there and a file it deletes or renames exists only under its old name. The set therefore records, for each question, the scorable files (present at the parent, a renamed file under its old path as git reports it) apart from the files the commit added, deleted or renamed, which are context and are never counted as misses; a question with no scorable file is not a question and is replaced. The report says how many files were unscorable and why. A real change may touch fewer files than it should have (a bug fixed later) or more than the graph could know (a renamed concept); the report says so and does not hide it. The sample is small (20), so the results are counts per project and per language, not percentages claimed as rates.
- **The reading of the old projects is read-only.** The agent clones them into the scratch directory (a clone of a local repository with no hard links) and checks out the parent commit of each question there. If the harness refuses to let the agent read a project outside this one, the owner runs the extraction commands that the plan names and shows the output; the plan does not look for another route.
- **The program is the one installed: version 0.9.103**, run as the spec says (a clean environment, `GRAPHIFY_OUT` set to a scratch folder, `update` of the project root, no `--force`). The versions recorded in the old graphs (0.9.64) are not re-run.
- **What the online search of 2026-11-09 added.** People mostly use the program the opposite way to the spec: an always-on `CLAUDE.md` section and a hook before search calls, rebuilt by git hooks, with a semantic pass over documents, and the published numbers are the vendor's (a token-reduction figure with no method, and memory benchmarks). The criticism found is about the graph going stale: a write-up reports deleted functions staying in the graph after incremental updates while the program said "already clean"; the vendor's issue list has many open reports on incremental `update`; one reviewer found about 93% of a repo's edges were plain containment; and the README fetched online says query logging is on by default to a file under the home directory (the installed 0.9.103 says the opposite in its source: the log is off unless `GRAPHIFY_QUERY_LOG` or `GRAPHIFY_QUERY_LOG_ENABLE` is set, and `GRAPHIFY_QUERY_LOG_DISABLE=1` forces it off, so the online README is of a different version). None of that is independent measurement, and none of it was checked against version 0.9.103. The three checks below test the points that bear on the spec's design. The spec stays as approved; if a check finds a problem, the spec is amended after the owner's decision (increment C).
- **The `grep` class of a question is fixed before any graph is built (the owner's measure of return, 2026-11-09).** A question is `grep`-sufficient when every ground-truth file contains the literal name of the symbol asked about, so one `grep` of that name finds all of them; it is `grep`-hard when some ground-truth file does not contain it (reached through a call chain, a rename, an include, a generated name). The class is recorded in the set and reviewed by the owner with the rest. The graph is judged on the `grep`-hard questions: on the others it can add cost and no value, and its hits there are reported but not counted as return.
- **A measurement is not a verdict.** The report states hits, noise and the `grep` baseline; whether that is enough is the owner's judgement ("never helpful" is the bar). The author's expectation, written down before the run: a useful hit rate for impact questions in the languages the parser covers, and little or none for Verilog.
- **Nothing tracked points to anything untracked.** The Result cites the projects by name and by commit hash (a git commit is a content hash), the program by version, and no path outside this repository.
- Standard library only for any script; scripts are kept in the scratch directory and their command lines are recorded in the Result, so a run can be repeated.

## Completion criteria

1. The Result's "The question set" lists the questions with every field above, states the selection rule and the symbol rule, and records the owner's review: what the owner kept, corrected or dropped. Each question carries its kind (impact or structure) and its `grep` class.
2. The Result's "The results" records, for every question: the graph's state (nodes, edges, `update` time, coverage of the question's language), the files `affected` or `query` named, the hits against the ground truth, the files named that were not touched, whether the answer was empty, ambiguous or cut, and the files a `grep` for the symbol over the source found with its hits and noise; per project and per language: the sums; **the same split by `grep` class, with hits and noise on the `grep`-hard questions given apart**; **for every graph, the number and share of edges by relation (`contains` against `calls`, `imports`, `references` and the rest), and for every question how many non-`contains` edges the answer reached**; **the ghost-node check of increment B** (nodes still attributed to a deleted file after an incremental `update`, against a rebuild into a fresh folder); **the list of everything the program wrote outside the output folder it was given** (the scratch home directory compared before and after); **the git commands the program ran** (from the recording `git`); **the result of the run under a sandbox that denies the network and writes outside scratch**; and the provenance line (the program's version, the commits, the command lines, the date).
3. No project outside this repository has a changed file or a new file (checked by `git status` of each project before and after), and no `graphify-out/` exists in any of them; the program was run with a scratch home directory, so nothing was written to the owner's real home directory by it.
4. The spec's final review round has run and its findings are decided, and the owner has said go or no-go in their own words, which the Result quotes.
5. `wb run code-work check` passes.

## Increments

### Increment A — The question set, and the owner's review of it

**Outcome:** completion criterion 1 is true.
**Dependencies:** none (the spec is approved).
**Affected areas:** the Result of this plan ("The question set"); nothing else is tracked.
**Steps:**
1. Read the history of the three projects with read-only `git` in scratch clones, apply the selection rule and list candidates in date order, with the files each touched. Write the rule and the lists down first.
2. For each chosen commit, apply the symbol rule, write the question, and record the fields. Record the language of the files the symbol lives in, **and the `grep` class** (for each ground-truth file, whether it contains the literal symbol name).
3. Write the set into the Result with the provenance lines (project names, commit hashes, retrieval date). Check it with `wb run code-work check`.
4. Stop and show the owner the set. The owner keeps, corrects or drops each question; record that in the Result. If the harness stops a read, record it and ask the owner to run the command.
**Verification:** the check passes; every commit hash in the set resolves in its project's clone; every scorable ground-truth file exists at the parent commit and every unscorable one is recorded as an addition, deletion or rename (a scripted check on the clones).
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-09-graphify-evaluation#A`.

### Increment B — The run, and the report

**Outcome:** completion criteria 2 and 3 are true.
**Dependencies:** A, and the owner's review recorded in it.
**Affected areas:** the Result of this plan ("The results"). Scratch directory only otherwise.
**Steps:**
0. **Checkpoint: the security review.** Before anything runs, ask the owner once whether to run a security review of the evaluation's execution surface: an installed vendor program started on source trees of the owner's projects (read from the program's source: it runs `git` and may write outside its output folder), the recording `git` and the sandbox profile the plan builds. The `security-review` skill and the `security-reviewer` agent are installed in this project. State what would be examined (the runner's environment, what the program can reach, the sandbox's limits) and that it runs only if the owner asks. Record the answer in the Result.
1. Write the runner in the scratch directory: for each question, a clean checkout of the parent commit; `graphify update` with the spec's environment, the output folder in scratch **and `HOME` (and `XDG_CACHE_HOME`, `XDG_DATA_HOME`, `TMPDIR`) set to scratch folders that are empty before the run**, so that anything the program writes outside its output folder lands where it can be listed and does not touch the owner's home directory; the environment also carries `GRAPHIFY_QUERY_LOG_DISABLE=1` and git's own configuration through the environment (`core.fsmonitor=false`, `log.showSignature=false`, no lazy fetch, no terminal prompt) and none of the caller's `GIT_*` variables, as the `mempalace` helper's does; the question as `affected` or `query` (once); the program's exit code and bounded output; a `grep` of the symbol over the source files of the checkout; the comparison against the ground truth. Record the version first.
2. **Split by `grep` class.** Report the hits and the noise of the graph apart for the `grep`-sufficient and the `grep`-hard questions, with the `grep` baseline for each; the return is judged on the `grep`-hard ones.
3. **Ghost nodes.** In each scratch checkout used for a question, after measuring it, delete one source file that other files refer to (a real definition with at least one caller), run `update` again into the same output folder, and record the program's message, whether any node or edge still has the deleted file as its `source_file`, and whether `affected` on a symbol that lived in it still answers. Then run `update` into a fresh folder on the same tree and record the difference. This tests the reported failure on the owner's own code, not a vendor example.
4. **Relation shares.** For each built graph count nodes and edges by origin, edges by `relation`, and the share that is `contains`; for each question record how many of the edges in the answer are not `contains`. This tests the claim that most of a graph can be containment.
5. **Git calls.** For one project, put a recording `git` program first on the `PATH` (a script in scratch that logs its working directory and arguments, then runs the real `git`) and run `update` and each query command once; list every git command the program started. The spec says the helper runs none and the program runs some; this records which.
6. **Enforced run.** Run `update` and each query command once, on one project, under the macOS sandbox (`sandbox-exec` with a profile that denies network access and denies file writes outside the scratch folders), and record whether each succeeds and what the sandbox refused. This turns the checks on downloads and outside writes from observation into enforcement, the equivalent of `mempalace`'s "never a download" check. If `sandbox-exec` is missing or the harness refuses to run it, record that and fall back to the observation of step 8; the owner may run it in a terminal.
7. Run it. Write the results into the Result: hits, noise and the `grep` baseline per project and per language, the answers that were empty or cut, the `update` times and graph sizes, and the coverage lines.
8. List what the program created or changed under the scratch home, cache, data and temporary folders, and check the projects before and after: `git status` clean and unchanged, no `graphify-out/`.
**Verification:** the three added checks are each run by hand on one project first and compared with what the program printed; the runner is run on two questions by hand first and its numbers are compared with the program's own output; the Result states each command line; `git status` of each project before and after.
**Evidence:** the one local commit, trailer `...#B`.

### Increment C — The final review of the spec, and the decision

**Outcome:** completion criterion 4 is true.
**Dependencies:** B.
**Affected areas:** `docs/specs/graphify.md` (only to apply review findings, and a short note on what the evaluation showed); the Result of this plan; if the owner decides no-go, the roadmap candidate (the owner's word makes the change).
**Steps:**
1. Show the owner the report and ask for the go or no-go (the spec's open decisions are closed: the semantic layer is dropped and the graph lives in `.workbench/local/graphify-out/`). Record the answer in the owner's words. If a check found a problem (ghost nodes after an incremental `update`, a write outside the output folder, a graph that is mostly containment), say what in the spec it bears on: the `update` command (rebuild into a fresh folder when a source file is deleted), the clean-environment and no-other-writes statements, or the `layers` line of `status` (add relation counts), and ask the owner whether to amend the spec.
2. On a go: run the spec's final review round with Codex, decide each finding, apply them and any amendment the evaluation led to, **and run a further round on the spec as amended, until a round finds nothing meaningful or the owner accepts the unread fixes in words that the Result quotes** (the ceiling of five rounds is the owner's to extend); then stop. A round that comes back clean, or the owner's recorded acceptance, is a prerequisite for drafting the module's plan, which is a new plan drafted on the owner's word. On a no-go: write the evidence into the Result; the roadmap's candidate is marked dropped with this reason only when the owner says so, because changing a roadmap is the `change-direction` checkpoint.
**Verification:** `wb run code-work check`; the owner's decision quoted.
**Evidence:** the one local commit, trailer `...#C`.

## Verification for the plan as a whole

Each increment's verification stands. At the end: the Result holds the question set and the results and they agree, no project outside this repository changed, and the owner's decision is recorded.

## Risks and sensitive actions

- **Running the vendor program on copies of the owner's projects.** The program reads source files and writes to its output folder; `update` is offline and uses no model (read from its help and seen in a scratch run on 2026-11-09). Every run is on a scratch checkout with the output folder in scratch. A project with a secret in its source tree would be read by the program, not sent anywhere; the owner can drop a project from the set. **The owner is asked about a security review before increment B runs (below).** In the first draft of this plan the author did not propose one: nothing here crosses a trust boundary the owner did not already cross by installing the program, and no module code is written. Ask again if that changes.
- **The program writes outside its output folder, and runs `git`.** The installed program's source (read 2026-11-09) logs queries only when asked and runs `git ls-files -z --cached`, `git rev-parse HEAD` and `git config --get core.excludesFile` during a scan (from the comparison with the `mempalace` work: a repository can select a program for git to run, and `mempalace` fixes git's settings for that reason). The runs use a scratch home directory, set `GRAPHIFY_QUERY_LOG_DISABLE=1` and the fixed git settings of the spec's follow-up, put a recording `git` first on the `PATH` for one pass, and run once under a sandbox that denies the network and writes outside scratch; if the program needs the real home directory or the network to run, the run stops and the owner is told.
- **A biased question set.** The agent chooses the questions and the symbols. The stated rules, the order-of-date rule, and the owner's review are the guard; the report also states the cases where the graph and `grep` both failed. A sample of 20 shows a pattern and not a rate.
- **Reading projects outside this one.** If the harness refuses, the plan stops and asks the owner to run the command; it does not use another route.
- **Large graphs and long runs.** The larger old project's graph was 26.9 MB; a rebuild at each question's parent commit may take minutes. A time cap per `update` (ten minutes) is recorded; a run that passes it is reported as such.
- **The key is on.** The commits of this plan are made under `wb run safe-git commit` at `delegated`; the hook may allow each. Those are the first commits of a plan that is mostly documents and scratch scripts, and the owner labels them as they come.
- Nothing is pushed without the owner's word.

## Review record

Codex, plan review, 3 rounds of 3 (the bound); converged with no meaningful finding in round 3. Models: `gpt-5.6-terra` for rounds 1 and 2, `gpt-6.1-sol` for round 3.

- Applied (round 1, major): the sample could fall below the 20 questions the graphify spec names; the plan now holds exactly 20 owner-approved questions with a replacement rule from a candidate list in date order (at least 30 candidates: 12 from each old project, 6 from this one).
- Applied (round 1, major): ground-truth files that the target commit adds cannot be found at the parent revision where the graph and `grep` run, so they would be guaranteed misses; only files present at the parent are scored, and additions, deletions and renames are recorded as unscorable context.
- Applied (round 1, major): the final review of the spec ran before its own fixes were read; it now continues until a round finds nothing meaningful or the owner accepts the unread fixes in recorded words, and that is a prerequisite for drafting the module plan.
- Applied (round 1, major): the plan declined a security review on its own; it now asks the owner once before increment B (a checkpoint, step 0) and records the answer.
- Applied (round 2, major): the two tracked files planned under `docs/references/` would have needed entries in its index, which is for external material (URL, licence, retrieval date, hash); the question set and the results are the project's own derived records and now live in this plan's Result.
- Round 3: no meaningful finding.
- Left for the owner: approval of the plan.

## Deferred work

- The module itself (its plan, on a go).
- A deterministic tool from the workflow's own links (the plans that touched a file, from the `Plan:` trailers on commits; the documents a plan cites), if document-to-code answers are wanted: a separate idea with its own spec, not part of graphify. The triggers that would reopen a semantic layer are in the graphify spec.
- A second measurement after the module has been used for a while, from the questions the owner actually asks it.

## Result

Empty until work starts.
