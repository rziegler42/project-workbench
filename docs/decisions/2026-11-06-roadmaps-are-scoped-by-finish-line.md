# Roadmaps are scoped by finish line, and small corrections need no candidate

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-06

## Context

The roadmaps README and `docs/specs/groundwork.md` say a roadmap is named by its scope and that one roadmap that is not archived is kept for each scope. They
say there may be several roadmaps. Neither says what a scope is, or how to tell new work that belongs in an existing roadmap from new work that needs a roadmap of its own.
The `draft-roadmap` skill, step 1, says to search for a roadmap "on the same scope" and add to it. With no test for "same scope", an agent adds to the nearest file.

The project has one roadmap, `workbench-v1`, which has 58 `###` headings and 1,061 lines. A spec change that follows from a finding, or a new spec, has meant adding
candidates to that file, and the file keeps growing. The owner expected several roadmaps, each with a finish line.

A plan already allows `Candidate: none` with a one-line reason (`docs/plans/README.md`, the `draft-plan` skill), but nothing says when a plan should use it.

Constraints: a candidate is cited as `<roadmap>#<id>` and a roadmap file is never moved or renamed, so splitting an existing roadmap leaves its old references pointing at
moved candidates. Creating or replacing a roadmap changes direction and needs the owner.

## Decision

1. **A scope is a body of work that has its own finish line:** one the owner can call finished, or pause, without that deciding anything about other scopes. A release, a
   subsystem or a cross-cutting concern can each be a scope. A roadmap whose finish line cannot be stated is too wide.
2. **New work is placed by a test, not by default.** The agent asks whether the new candidate shares the finish line of the roadmap it would join.
   - If it does, it is added to that roadmap as a candidate.
   - If it does not, or no roadmap fits, the agent proposes a new roadmap, naming its scope and its finish line, and the owner accepts or renames it before the file is written.
   - Neither answer is the default. An agent never adds to the nearest file because it is nearest.
3. **A size signal prompts the question and caps nothing.** When a roadmap passes about 15 candidates, the agent asks the owner whether it has outgrown its scope before
   adding another. The owner may say to go on.
4. **A small correction needs no candidate.** A spec change that follows from a finding, or a fix too small to be a body of work, goes straight to a plan with
   `Candidate: none` and a one-line reason. A candidate is for bounded new work that advances the finish line of a roadmap, whether an existing one (decision 2) or a
   new one. `Candidate: none` is for work too small to need roadmap direction.
5. **`workbench-v1` is not split or rewritten by this record.** New work is scoped from here on. A later change to that roadmap, such as a status note that new scopes get their own
   roadmaps, is the owner's call and a separate step.
6. **The text follows in a plan.** The `draft-roadmap` skill, the roadmaps README, the plans README sentence on `Candidate: none`, `docs/specs/groundwork.md` and, if it needs it, the
   `draft-plan` skill are edited to say the above. This record does not edit them.

## Alternatives considered

- **Split `workbench-v1` into scoped roadmaps now.** Rejected by the owner. Candidates are cited as `<roadmap>#<id>`, files are never renamed, and plans that cite
  `workbench-v1#...` would need "moved to" markers. Scoping new work gets the benefit without that cost.
- **A hard cap on candidates per roadmap.** Rejected. It repeats the problem of a rule that is too restrictive; a roadmap with a clear finish line may legitimately be large. A prompt asks the
  question without forcing a split.
- **Every spec-changing finding becomes a candidate.** Rejected by the owner. It sends all small work through a roadmap, which is the pressure on the single file.
- **A fixed list of scopes written in the README.** Rejected. A list goes stale and needs the owner for every new topic; a test applied at the time of the work does not.
- **Allow several active roadmaps on one scope.** Rejected for now. The cause was missing scopes, not the one-per-scope rule; two roadmaps with the same finish line would make the
  "add or new" question harder.
- **Leave the text as it is.** Rejected: it gives no test, so the default stays "append".

## Consequences

- Good: new work is placed by a question an agent can answer and the owner can check. Small findings leave the roadmap alone. Several roadmaps, each with a finish line, become the norm.
- Good: nothing existing is renamed, so no reference breaks.
- Bad: "shares a finish line" is a judgment and agents will differ; the owner's acceptance of a new roadmap is the check, and the first uses will show whether the wording needs a second record.
- Bad: `workbench-v1` stays large; this record only stops it growing by default. It still takes an owner decision to change it.
- Bad: the size signal at about 15 candidates is a guess. It is a prompt, so a wrong number costs a question, not a refusal.
- The `draft-roadmap` skill ships with the groundwork package, so the new text reaches an installed project only after the package is released, and the owner runs the upgrade and the rerender.
- Nothing is built by this record. The plan in decision 6 does the edits, and needs the owner's approval.

## Evidence

Read at commit `f3640f6` on `main` (2026-11-06), on macOS 26.7.1, with `grep` (ugrep 7.8.4) and the system `wc`, which prints no version: `docs/roadmaps/README.md` (Naming, Retiring a roadmap), `docs/specs/groundwork.md` (roadmap bullet near line 75),
`packages/workbench/groundwork/harness/neutral/skills/draft-roadmap/SKILL.md` (step 1), `docs/plans/README.md` (line 21), the `draft-plan` skill (step 4), and the size of
`docs/roadmaps/workbench-v1.md` (`grep -c '^### '` gave 58; `wc -l` gave 1061). `grep` over `docs/` found no earlier record on how many roadmaps may be active; the rule comes from the plans
`2026-10-27-give-shipped-text-the-missing-rules` and `2026-10-27-retire-carried-instructions` (item RP5). The positions on splitting, on small corrections and on a size prompt are the owner's,
given in conversation on 2026-11-06; the finish-line wording and the figure of 15 are the agent's proposal.

*Clarified 2026-11-06, with the owner's approval of the plan `2026-11-06-roadmap-edits-are-direction-changes`:* Decision 2 says where a candidate goes. Adding a candidate to a roadmap, like any change to a roadmap other than correcting a typo, is a change of direction and the `change-direction` checkpoint, which always stops for the owner. The agent runs the placement test, shows the owner the candidate it would add, and writes it on the owner's word; the owner's request to add a candidate is that word. The proposal of a new roadmap, and the rest of this record, stand as written.
