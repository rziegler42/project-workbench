# Unconfirmed removals are outside the action-review measure

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-05

## Context

The shadow period of `action-review` measures the engine against the owner's labels and a test set
(`docs/specs/action-review.md`, "Accuracy and cutover"). The owner decided the cutover bound on 2026-10-29: at most 10%
false declines among the labelled real commands, at least 10 labelled commits and 10 labelled removals, and no false approve
on the labels or the test set.

The first labelling (2026-11-05, recorded in the spec's Evidence) gave `commit` 9 labelled and all right, and `remove` 11
labelled with 7 right and 4 wrong. All four wrong labels are false declines by the one fixed check `confirm_present`, which
declines every `remove` whose arguments lack `--confirm`. Each of the four was a preview, the dry-run listing that
`safe-git remove` prints before the owner approves a list (`commit-changes` skill, "Deleting files"). A preview deletes nothing.
The rate of those four among 11 is 36.3%, over the bound.

The cause is structural and not a matter of model quality. Every removal starts with a preview, so each removal the owner
makes adds a preview to the labelled set, and the rule declines it. By labelling alone the rate falls below 10% only after
about 29 more removals have been labelled right.

The hook that decides does not exist yet. How it treats a command without `--confirm` is open in the spec ("An open design point
this raises"). This record settles how the shadow counts such a command. It does not build the hook.

## Decision

A `remove` command without `--confirm` is outside what the engine is measured on, and the cutover test does not count it.

1. The report counts these commands on a separate line, "unconfirmed removals (previews)", with how many were labelled and how
   the engine judged them. They are not in the removal rate, the removal minimum of 10, or the false-decline count.
2. A preview that the engine declines stays visible in that line. It is never hidden, and a preview the engine approves is a
   false approve like any other and blocks cutover.
3. The bound (10% false declines, 10 labelled commits, 10 labelled confirmed removals, no false approve on the labels or the
   test set) is unchanged. Only the population it is applied to is defined: commands that would change something.
4. The labels already made do not change. The four previews keep their labels; the report classifies them by the command's
   `confirm` fact, not by relabelling.
5. What a hook does with an unconfirmed removal at cutover (the rule approves a valid preview, or the hook passes it by a fixed
   rule without calling the engine) is not decided here. It is decided in the plan for the hook, and until then nothing the
   engine says takes effect.

After this record the removal count stands at 7 labelled, all right, so the minimum needs 3 more confirmed removals.

## Alternatives considered

- **Change the rule so that a valid preview is approved.** Rejected for the measure: the four earlier declines stay in the
  history, so the rate stays over the bound until about 29 more removals are labelled. It may still be the right rule for the
  hook, and item 5 leaves that open.
- **Relabel the four previews as right.** Rejected: a label records what the owner judged at the time. A changed label to pass
  the bound is the wrong way to meet it.
- **Raise the bound.** Rejected: the bound measures the cost of a wrong decline and the preview problem is not a question of
  how many wrong declines the owner accepts. The bound is the owner's to change and is not changed here.
- **Wait for the rate to fall by labelling more removals.** Possible but slow, and the structural decline would count against the
  engine at every step.

## Consequences

- The cutover test measures the commands the engine is meant to judge, those that change something.
- Good: the evidence the owner has is used as it is, with no label changed and no bound moved.
- Bad: the engine is never shown to handle previews. If the hook later sends them to the engine, there is no measure for them
  and the separate line is the only evidence. Item 5 puts that choice in the hook plan.
- Bad: the report needs a change (a package edit, through a scratch clone, the owner's copy and a release), and the
  removal count restarts at 7 against a minimum of 10.
- The accepted cutover rule in the spec is clarified, not replaced: the spec's "Accuracy and cutover" is edited in place to say
  what is counted, and a dated note points to this record.

## Evidence

- The shadow report run on 2026-11-05 at commit `1d29cbd` (`python3 -B ~/action-review-shadow/report.py`, read-only): `commit`
  labelled 9, right 9, wrong 0; `remove` labelled 11, right 7, wrong 4, false declines 4, all by `confirm_present`; false approves
  0; test set 29 of 29 with 0 false approves and 0 false declines; cutover line "not yet".
- The first test-set run and the labels are recorded in `docs/specs/action-review.md` ("The first test-set run and the first
  labels of the shadow (2026-11-05)"), which also names the four false declines as previews.
- The check is `confirm_present` in the spec's table of fixed checks: `remove` declines when `confirm` is false.
