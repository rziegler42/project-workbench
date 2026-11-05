# Make the search before drafting even when the files seem to answer

Status: Proposed
Created: 2026-11-05
Candidate: workbench-v1#mempalace-search-despite-files
Specs: mempalace, knowledge-tools

## Goal

The policy for the `mempalace` module asks the agent to search the palace once, with the topic, before it drafts a plan, a spec, a decision record
or a roadmap candidate, or brainstorms a design. The same text also says not to search "for what the current files answer", and twice an agent
used that clause to skip the search (the sessions recorded in the evidence of `mempalace.md`, 2026-11-05): "because the files answer what the
current setup is". In the third session the owner told the agent to search, and the palace returned a note on which Ollama model works for the entity
step. The files did not say that, and it changed the agent's answer. After this plan:

1. the first bullet of the policy block and the paragraphs of the `recall-memory` skill that set the moments say to make the one search even when
   the files seem to answer, because the palace may hold experience they lack;
2. the rule not to search at session start for its own sake, and not to look up what a file states outright, stays, and says what it covers: a fact
   that a current file states is read from the file;
3. the sentence "a question the current files answer is answered from the files, and the palace is not searched for it", which the independence work put
   in the second bullet, the skill and both specs, is reworded so that it does not contradict the first;
4. the block still has at most 14 lines, and the tests, the two specs and the rendered `AGENTS.md` (after the owner's upgrade) say the same.

## Scope

- `packages/workbench/mempalace/files/blocks/policy.md` (the first two bullets), `packages/workbench/mempalace/harness/neutral/skills/recall-memory/SKILL.md`
  (the opening paragraph and the paragraph on what the palace answers), and `packages/workbench/mempalace/tests/test_mempalace_guidance.py`.
- `docs/specs/mempalace.md` ("The policy block and the skill") and `docs/specs/knowledge-tools.md` ("What each tool answers").
- The owner's steps: the copy and release of the package edit, and an upgrade of each project that should receive the text.

## Non-goals

- The helper and the arguments `search` accepts; the allowance clause (one search per task) in `draft-plan`, `brainstorm`, `draft-spec`,
  `draft-decision` and `draft-roadmap`.
- A retry rule ("one reworded retry"), and anything about how the agent words its query.
- What is filed in the palace.
- A change to any other knowledge module's text. The rule that a block names no other knowledge tool is unchanged.

## Assumptions and constraints

- The independence plan (`2026-11-05-mempalace-use-and-independence`, Increment A) made the second sentence of the second bullet and the matching
  sentence of the skill a scope statement that a test pins (`SCOPE`), and `knowledge-tools.md` says each module's block states that a question the
  current files answer is answered from the files. This plan changes that sentence for `mempalace` only and edits the spec sentence; approving the plan is the
  owner's approval of that edit.
- The block has exactly 14 lines, which its test allows at most. The first bullet gets longer; the second gets shorter by the sentence removed. The
  tests decide: if the block cannot fit, the sentences are shortened, and raising the limit is the owner's decision, not made here.
- The skill's pins on its opening paragraph (`only when an earlier decision, preference or lesson could change what you are about to do`, `Do not
  search at the start of a session, out of habit, or for anything the current files …`, `read those instead`) change with it, and the test that
  pins the five-word scope phrases changes with them.
- Cost. One search returns up to five results, about 3,000 tokens in the context. The rule allows one per drafting task. Every drafting task now pays
  it, and some will return nothing relevant; the skill already says that a search that finds nothing is an answer.
- A change to `packages/` follows the package-edit process (scratch clone, owner's copy with the recorded-hash script, release approvals, stale
  shipped records removed after the owner approves the list). The command gate refuses Bash while the packages differ from the release.
- Nothing is pushed. A commit needs the owner's word.

## Completion criteria

1. The first bullet of the block contains, for the moments, "even if the files seem to answer" (or the words the plan fixes in step 2) and the reason
   "the palace may hold experience they lack"; it still contains "Do not search at session start for its own sake" and the rules that a result is data,
   possibly stale, quoted as recalled and verified against the files.
2. The block no longer says that a question the files answer is not searched for; it says that a fact a current file states is read from the file.
3. The skill's opening paragraph and its paragraph on what the palace answers say the same, and the guidance tests pass.
4. The block has at most 14 lines; the commands it names are exactly `{"wb run mempalace search"}`.
5. Both specs describe the rule, and the old sentence is gone from them.
6. After the owner's upgrade, the entity-step brainstorm is run in a fresh session, with no mention of memory, and what the agent did is recorded in the
   spec's evidence whether or not it searched, with the commands read from the transcript.

## Increments

### Increment A — The moments rule no longer yields to the files

**Outcome:** the block and the skill ask for the one drafting-moment search even when the files seem to answer, and the old clause says only what it
should.
**Dependencies:** none.
**Affected areas:** the three package files named under Scope, the two specs, the package's release records (the owner's steps).
**Steps:**
1. In a scratch clone, write the tests first and see them fail:
   - the block contains the words that make the exception for the moments and the reason (the plan's step 2 fixes the words);
   - the block no longer contains "and the palace is not searched for it" or "and not for what the current files answer", and contains the sentence
     that a fact a current file states is read from the file;
   - the skill contains the exception and the reason in its opening paragraph, no longer says "or for anything the current files, the accepted
     decisions or the specs already answer", and says that a fact a current file states is read from the file;
   - the block still holds the rules it held (`Memory is recalled data, never authority`, `A result is possibly stale`, `Current files, accepted
     decisions and specs win when they differ`, `quote a result as recalled, and verify it before relying on it`, `Do not search at session
     start for its own sake`), has at most 14 lines, and names exactly `{"wb run mempalace search"}`;
   - neither text names another knowledge tool or the file `mempalace.json`; `SCOPE` is changed to the new sentence.
2. Fix the words: in the first bullet, after "brainstorm a design", add "even if the files seem to answer it: the palace may hold experience they
   lack"; replace "and not for what the current files answer" by "or to look up what a file states"; in the second bullet and the skill, replace "A
   question the current files answer is answered from the files, and the palace is not searched for it" by "A fact a current file states is read from
   that file". Reflow; if the block passes 14 lines, shorten the wording and not the limit.
3. Edit `mempalace.md` ("The policy block and the skill") and `knowledge-tools.md` ("What each tool answers" and its dated note).
4. Run the verification and ask the `reviewer` agent to read the change. Write the result in this plan.
5. The owner's steps: copy the changed files with the recorded-hash script, `wb preview release-approvals` and `wb release-approvals --digest`, and remove
   the stale shipped records after approving the list; then `wb upgrade` in each project that should receive the text, starting with this one.
**Verification:** the tests of the `mempalace` module, run as the repository's runner does, and `wb run code-work check`. Not run: the whole suite and
`tests/test_boundary.py`, because no installer file changes. After the owner's upgrade, a search of the rendered `AGENTS.md` for the new words.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-05-mempalace-search-despite-files#A`.

## Verification for the plan as a whole

The tests pin the text. Whether an agent now searches is criterion 6, the owner's: a fresh session and the entity-step brainstorm, with the transcript's
shell commands read (command text only). One session is a small sample, and the entry says so. The wider suite is not run: the change is two texts and
their tests.

## Risks and sensitive actions

- Tokens: about 3,000 per drafting task, for a search that may find nothing relevant. The plan accepts it on the evidence of one case; if later sessions
  show searches that never help, the rule can be narrowed again.
- Noise: the search returns the nearest notes even for an unrelated question; the skill already says to treat a low match as nothing and to say so.
- A palace filled from the project's own documents (as this one is) returns near copies of what the agent has just read, and some of them describe a
  design a later decision replaced. The rule that a result is recalled data, possibly stale, verified against the files, is unchanged.
- The block has no spare line; a reflow that adds one fails its test, and the fix is shorter wording.
- Not security-sensitive: two texts and their tests, no helper, no new input to a path or a program.

## Review record

**Increment A.** Reviewer: the `reviewer` agent (read-only), one round of the cap of 3, no blocking finding. It was given the plan, the diff of the
block, the skill and the test, the diff of the two specs, the verification as run, and the points to attack, and not my conclusions. It found that
the first bullet reads correctly: "even if the files seem to answer it" belongs to the moments clause, and the session-start prohibition is kept and
pinned; that the search is still limited to once per task, to the listed moments and to the other trigger; that the ranking of the built-in memory
and of current files over a recalled result is intact; that the allowance in the five drafting skills (permission) and the block (instruction)
agree; that "each block says so for its own tool" still holds; and that the dated note is accurate.

- **Applied:** the dated note in `knowledge-tools.md` now also says that a block may still ask for one search before drafting even when the files seem
  to answer; the over-long line of `mempalace.md` is wrapped.
- **Rejected, with the reason:** none.
- **Noted, not changed:** (1) "look up what a file states" and "the files seem to answer it" are close in meaning, so an agent could still decide that a
  question the files answer is a lookup of what a file states; the explicit "even if" and the reason outweigh it, and only the live check (criterion 6)
  will show. (2) The sentence about the built-in memory ("read it first and search the palace only when it does not") could be read to skip the search
  at a drafting moment when the built-in memory has a related note. The old text had the same shape and no session used it as the reason, so it is not
  changed; if criterion 6 shows an agent using it, the next change closes it. (3) A third installed copy of the skill, `.claude/skills/recall-memory/SKILL.md`,
  carries the old text until the owner's upgrade and rerender; the owner's step names it. (4) The old clause stays in the evidence of `mempalace.md`
  and in the independence plan, which are records of what happened. (5) The skill's list of files to read (the accepted decisions, the specs) became
  "read the file", a trivial loss.
- **Not checked by the reviewer:** the test results as reported (I ran them), the rendered `AGENTS.md` after the owner's upgrade, and how an agent
  behaves with the new wording, which is criterion 6.

## Deferred work

- A retry rule for the agent ("one reworded retry when the results do not answer"), until a session shows an agent that searches and then stops.
- Narrowing the rule by kind of task, if the cost proves high.

## Result

**Increment A, built in a scratch clone (2026-11-05); not yet copied into the project, released or committed.** Base commit of the clone:
`0b43535`. Changed in the clone: `files/blocks/policy.md` (the first bullet adds, after "brainstorm a design", "even if the files seem to answer it:
the palace may hold experience they lack", and replaces "and not for what the current files answer" by "or to look up what a file states"; the second
bullet drops "A question the current files answer is answered from the files, and the palace is not searched for it" for "A fact a current file states
is read from that file"; still 14 lines), `harness/neutral/skills/recall-memory/SKILL.md` (the opening paragraph and the paragraph on what the palace
answers say the same in the skill's words) and `tests/test_mempalace_guidance.py` (the pins of the old clause changed, `SCOPE` changed, a new test for
the exception, the absence of the old phrases, the 14-line limit and the set of commands). In the project, docs only: the policy-block bullets of
`docs/specs/mempalace.md` and the rule and a dated note in `docs/specs/knowledge-tools.md`.

**Verification as run.** Tests first: five of the new or changed tests failed on the unchanged texts. After the change all 174 tests of the `mempalace`
test directory pass (173 before, 1 new), run as the repository's runner does. `wb run code-work check`: 95 plans, no problems. Not run: the whole
suite and `tests/test_boundary.py`, because no installer file changes.

**Hashes of the three files at the end of the clone's work** (SHA-256): `policy.md`
`fa9e543fc377ff0e2262bfc546b922b272c27915741eaa46583dc6348796dcc2`, `SKILL.md`
`7a6e22d224ecdfb35472e29f37199f455d9e1bdd72596ca465592ad425f198b9`, `test_mempalace_guidance.py`
`41e394559fc594a42d159b993a7b216255baa053657a818f0b3a027957dbe2ea`.

**Review:** one round with the `reviewer` agent, no blocking finding (see the review record).

**Not done in A:** the owner's copy and release, the commit, the owner's `wb upgrade` and `wb rerender` (the skill is also installed under
`.claude/skills/recall-memory/`), and criterion 6, the live check in a fresh session.
