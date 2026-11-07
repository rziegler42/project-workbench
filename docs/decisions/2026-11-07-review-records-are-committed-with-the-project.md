# The files of a review are committed with the project, all of them

Status: Proposed

## Context

The `review-engine` module keeps each review in a directory of the project, `.workbench/workbench/review-engine/<key>/`, with `state.json`, `ledger.md`, `schema.json` and one `round-<n>.json` per round. Its spec says the directory "is committed with the project, so a clone and a teammate keep the history" (`docs/specs/review-engine.md`, "State" and "Record paths"). Nothing in a decision record said why, and two projects acted differently:

- In this repository `.git/info/exclude`, a file local to one clone, held four lines (`plan-*`, `spec-*`, `roadmap-*`, `adr-*` under the review-engine directory), so 370 files of 70 reviews were never committed and a fresh clone had the plans' Review records and none of the evidence behind them.
- In knowledge-base, a project that uses the workbench, the same directories were tracked, and on 2026-11-07 a report from there showed that the commit completing a plan left its review directory out. The module then gained `record-paths` and a step in its `peer-review` skill that tells an agent to name those files in the commit that completes or closes the plan (plan `2026-11-07-review-record-paths`).

The owner asked on 2026-11-07 which is better, tracked or untracked, learned that the remote of this repository is public, and decided: "If we are going to track them, then I would track everything. If we are not going to track them, then I wouldn't track anything. I want consistency." The agent had recommended tracking; the choice below is the owner's.

Constraints: `wb run safe-git commit` takes exact files and refuses a directory; a review's files hold what a model said about a document (findings, the agent's reasons for applying or rejecting them, model and bridge names, token counts) and no document text beyond what the findings quote; the plans, specs, decisions and roadmaps they discuss are tracked and, here, public.

## Decision

1. **The files of every review are committed with the project.** A project that installs `review-engine` does not exclude them from git, by `.gitignore`, by `.git/info/exclude` or by any other rule. A project tracks all of its reviews or none; this repository tracks all.
2. **The commit that completes or closes a plan holds the files of that plan's review**, named one at a time with `record-paths <plan>`, as the `peer-review` skill says. *(Author's call, which the owner confirms by accepting this record:)* the files of a review of a spec, a decision record or a roadmap are committed in the commit that makes the change the review informed (the edit of the spec or roadmap, or the commit that accepts the decision record); when the review led to no change, they are committed in a commit of their own before the next push. They are never left untracked past that push.
3. **Before the files of a review reach a public remote, they are checked.** The owner's `push-check` scans the diff of every push; in addition, the first time a project starts to track its reviews, the agent scans the existing files for home or temporary paths, the owner's name or address, key headers and the common token shapes, and reports what it finds before committing.
4. **This repository's own history was brought in line before this record was written, on the owner's instruction of 2026-11-07 and not by this record:** the owner removed the four exclude lines (a local file) and the 370 files that had been left out were committed in one commit and pushed. This record states the policy that action followed and gives no authority to it after the fact; if the owner does not accept the record, that commit stands as the owner's act and the record is rejected or superseded.

## Alternatives considered

- **Track none, in every project.** It keeps model output out of a public history and adds no commits. Rejected: a plan's Review record would summarise a review whose evidence is on one disk; the engine's sealed state, which `extend`, `reset` and `archive` act on, would not survive a lost disk or exist in another clone; and the spec, the skill and knowledge-base already assume the opposite.
- **Track, but only the reviews of plans that are completed.** It keeps noise down. Rejected as the owner's "consistency": it makes the history depend on which reviews happened to finish, and the older reviews would still need a rule.
- **Track the state and the ledger, ignore the round files.** The round files are the largest part and hold the model's raw findings. Rejected: the ledger and the state point at the rounds, the seal covers them, and a partial record cannot be checked.
- **Leave it to each clone's exclude file.** Rejected: that is how this repository and knowledge-base came to differ without anyone choosing it.
- **Keep the exclude lines and commit the reviews of the two newest plans by force.** Rejected by the owner: the records would be a mix, and the reason for the mix would be nowhere in the repository.

## Consequences

- **Good:** the Review record of a plan has the evidence behind it in the same history; a clone, a second machine or a teammate has the state, so the owner can `extend`, `reset` or `archive` a review anywhere; the engine's spec, its skill and the two projects agree; the push scan covers what is published.
- **Bad:** model output about the project's documents is public here, and so is the trail of how each finding was judged. The scan found nothing that is not already in the public plans, but a scan by patterns cannot prove it, and a later plan that quotes a secret in a finding would publish it (the plan itself would have quoted it first, and the push scan runs on both).
- **Bad:** the history grows (370 files and 16,018 lines at the first commit, then on average about five files and 230 lines for each review) and each completing commit has more paths. The files that `record-paths` prints must be named one at a time, which makes the command long.
- **Bad:** two people reviewing the same document will conflict in the committed state; the spec already says the owner `reset`s the review.
- **Neutral:** a project that must not publish review text (a private remote that is later made public, for example) must decide again, by a new record, and rewrite its own history with the owner's word; this record does not allow an exclude rule in place of that.
- **Follow-up, not decided here:** whether `wb check` or the module's check should report a review directory that is excluded from git, so that the two projects cannot drift again. That would be a roadmap candidate, and it needs the owner's word before it is written.

## Evidence

This section reports what was done before the record was written, on the owner's instructions; it is not an outcome of the decision.

- Run on 2026-11-07 at `ab7e0f0` (this repository): `git ls-files --others --exclude-standard` after the exclude lines were removed listed 370 untracked files, all under `.workbench/workbench/review-engine/` (15 `adr-`, 46 `plan-`, 8 `spec-`, 1 `roadmap-` directories) and nothing else.
- A pattern search over those 370 files (git 2.54.0 and BSD grep on Darwin 25.6.0; the patterns were home and temporary paths, the owner's login name, email addresses, private-key headers, AWS, GitHub, OpenAI-style, Slack and bearer tokens, and password or API-key assignments) found no hit. A scan of the two reviews of that day for the word "token" found only the engine's usage counts and the findings about secrets.
- `wb run review-engine record-paths docs/plans/2026-11-07-label-declined-secrets.md` and the same for `2026-11-07-handle-paths-are-shell-safe.md` each printed six files (Python 3.15.0, `review-engine` helper of `ab7e0f0`).
- Committed as `e0dd789` ("Track the review records of the review engine", 370 files, 16,018 insertions); `wb run safe-git push-check` reported no finding; pushed to `origin/main` as `ab7e0f0..e0dd789`.
- Sources: `docs/specs/review-engine.md` ("State", "Record paths"); plan `2026-11-07-review-record-paths` (knowledge-base report, 2026-11-07); the owner's words quoted above, 2026-11-07.
