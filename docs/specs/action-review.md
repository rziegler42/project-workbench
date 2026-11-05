# action-review

Status: Draft. A design for the engine of roadmap candidate `action-review-engine`, written on 2026-10-25 from a
brainstorm in which the owner chose to skip the questions. The owner approved the design as written on 2026-10-25,
after settling the accuracy method, the false-decline bound, the name `describe`, and the fate of `safe-committer`
and `amend-message`. A call marked **(default)** was the author's and is approved with the design but was not
separately chosen; the owner may still change it. The approval is of the design only and approves no plan. The
`describe` interface is a decision record of its own, accepted by the owner on 2026-10-25
(`2026-10-25-describe-interface-for-action-review`). The rule schema, the module's layout and declaration, the bridge setting and the checks for `commit` and `remove` were
written on 2026-10-26 by Increment A of plan `2026-10-26-action-review-engine` and wait for the owner's reading
("The rule schema, the module and the checks"). The engine is built for `commit` and `remove` (plan `2026-10-26-action-review-engine`, Increments B to K; "As built, and its limits" at the end of the design says where it differs from the text and what it does not do), and so are the `describe` side of `safe-git` (for `commit`, `remove` and `push`) and the launcher rule (plans `2026-10-25-safe-git-describe` and `2026-10-26-safe-git-describe-push`). The shadow (the hook that records and decides nothing, its store, the labelling tool, the report and the test-set runner) is built by plan `2026-10-29-action-review-shadow-hook`, Increments A to H ("The shadow hook"), corrected after a security review by plan `2026-10-30-shadow-review-fixes`, and made to store redacted text by plan `2026-11-03-redact-collected-diffs`; the owner has installed it, and its report of 2026-11-05 counts 83 prompted commands (31 reviewed, 52 not), 20 of them waiting for a label and none labelled, and the test set not run. The status stays `Draft` because the owner has not read the engine's sections, because the shadow has no label and no test-set run to judge it by, and because the push rule, a hook that decides and the cutover are not built (the owner's profile file, which replaced the personal setting, has been read by this engine since plan `2026-11-04-review-profiles`, increment F) (plan 5 of
  the split below).

Terms are defined in `terms.md`. The engine sits above the bridge of `model-bridge.md` and beside the engine of
`review-engine.md`. The decision behind it is `2026-10-22-model-calls-go-through-vendor-bridges` (decisions 3, 6, 7
and 8); the authority rules are in `trust-and-approval.md`.

## Purpose and reason

The owner's approver is a program in the user level (item `codex_approver.py` of `global-config-inventory.md`,
role USER). A hook calls it when a command that an `ask` rule prompted for is about to run. It collects facts
about the action, runs fixed checks, asks a model for a verdict against a rubric, logs the verdict and, for two
delegated rules, can allow the command.

It cannot be moved or removed in pieces. Its facts for a commit and a removal come from the global
`claude-workflow` program, loaded as a library (`load_helper`, `collect_commit`, `collect_remove`, read on
2026-10-25, not run). So the program cannot be removed (move M14) without silencing review of every commit, and
the module spellings were added only by a narrow patch that keeps that dependence (accepted option 1a of
`2026-10-25-approver-coverage-for-the-module-commands`). Decision 7 of the vendor-bridges record says facts come
from the module that owns the action and leaves the interface open until this engine is planned. This spec
proposes that interface and the engine around it.

*Note, 2026-10-29.* The approver program, the global `claude-workflow` program, the `safe-committer` agent and `amend-message`
that this spec names were part of the owner's former user-level configuration, which was reset to factory defaults on 2026-10-29.
No approver now reviews a command, and the cutover step below has no program left to replace. The engine, the `describe`
interface and the decisions in this spec stand as the design; what changed is the starting point, not the engine.

## Goals

1. An engine, `action-review`, that takes facts about one action and returns a verdict with reasons as data,
   from a rubric, fixed checks and rules, calling a model only through a `model-bridge`.
2. A `describe` interface by which the module that owns an action reports the facts, read-only, before the action is
   made. No second copy of the owner's inspection code.
3. The approver's program can be replaced by a thin hook that asks the engine, so M1 stage 2 and M14 can happen
   and the global `claude-workflow` program can go.
4. The review is accurate against the owner's own judgment, not against the approver's verdicts. The owner reports
   that the approver gave many false declines (commands the owner would approve), so agreeing with it is not the
   target. Both errors are counted: a false decline (a safe action stopped) and a false approve (an unsafe action
   let through). A false approve is the worse one. Every kind of command the approver reviews is still reviewed.

## Non-goals and anti-goals

- The engine writes no `allow` rule, no setting and no hook entry, and its verdict authorizes nothing by itself
  (decision 6). A verdict that is missing, malformed, unavailable, timed out or not a verdict approves nothing.
- It is not a reviewer of documents (that is `review-engine`), and it names no vendor.
- It does not move the enforcement point. The hook stays in the owner's own configuration, outside a project's
  reach (`2026-10-24-project-guarantees-a-floor`). The agent does not write the user level.
- It does not widen delegation. Which actions a verdict may stand in for is the owner's personal setting and a
  code constant of the enforcement point, as `DELEGABLE` is today.
- Anti-goals: an engine that approves more than the approver does; a `describe` command that changes anything; facts
  trusted as instructions; a typo in a rule file that silently turns the review off for every command (the
  approver does this today, measured on 2026-10-25).

**Decided, not built: the delegate to a bridge for any action key** (accepted decision
[2026-11-03-delegated-for-an-action-key-and-named-risk-profiles](../decisions/2026-11-03-delegated-for-an-action-key-and-named-risk-profiles.md);
plan `2026-11-03-delegated-levels-and-risk-profiles`). The "does not widen delegation" line above and the `DELEGABLE` constant
describe what is built now. The owner's goal is that, for any action the owner sets to `delegated`, this module's engine, through the
configured bridge, approves the same confirmation `ask` asks for while the owner's own prompt is shown alongside. The decision
changes, when the hook is built and not before:

- Which actions a verdict may stand in for is decided by the owner's levels table and a module's declaration with a bridge rule,
  not by a code constant; `DELEGABLE` goes when the hook is built. Digest-bound keys (such as the review engine's `extend`) are
  eligible, each needing a `describe` and a rule, built one action at a time after the shadow period.
- A decline waits for the owner, who may override it. A failure of the bridge, the engine or the hook is a decline. The reason of a
  decline is shown as far as the harness allows and is not required.
- The hook is registered in the owner's user-level configuration, outside a project's reach, and reads the owner's levels table to
  learn which keys are `delegated`; `wb doctor` can only note that it depends on a hook it cannot see.
- Whether the harness shows the permission prompt while a `PermissionRequest` hook runs is not known; a test on a copy comes before
  the hook is built, and a record says what the owner sees and for how long if the prompt is held.
- The cutover bound ("Accuracy and cutover") is a precondition, and the old approver's declines by failed check are the evidence that
  false declines are what to measure.
- The `action-review` plans build all of this after the shadow period; none of it is built now. The named risk profiles of the same
  record are built in the installer (`command-permissions.md`, "Named risk profiles") and do not change this module.

## The design

### The `describe` interface (default)

A module that owns an action ships a read-only subcommand `describe` beside the action. `wb run safe-git describe
commit <the arguments of commit>` takes exactly the arguments of the real command and prints one JSON object of
the facts that the real command would act on, running the same validation code the real command runs. It makes no
commit, stages nothing, writes nothing and runs no program the repository selects. `describe remove` does the same for
`remove`, extending the `remove` preview it has. `push-check` has part of this shape for a push, and `describe push` the whole of it.

- The object has `contract` (a whole number), `action` (`commit`), `ok`, `truncated` (always present, a boolean),
  `errors` (the refusals the real command would give, as data, not as a failed run) and `facts` (a flat set of named
  values with a size cap). A module documents the names of its facts and its numeric caps in its own spec, and the
  engine's rules name them. A truncated object is incomplete and the verdict is a decline. The field rules and the
  behaviour at the cap are fixed by the accepted decision `2026-10-25-describe-interface-for-action-review`.
- A refusal is a fact: a commit the real helper would refuse is reported as `ok: false` with the reason, and the
  engine's check for it fails the verdict.
- The engine runs `describe` only through the launcher (`wb run`), the same rule decision 4 sets for bridges, and
  only for a command that an installed, pinned module declares as a `describe` provider. Its output is data.
- **Why this shape (default):** the real validation lives in one place and cannot drift; the call is free of side
  effects by construction; it needs no new capability of the launcher beyond running a pinned command. The
  alternative of a `--preview` flag on the action itself was rejected as default because a mistaken flag would run
  the action.

### The engine (default)

A module `action-review` providing the capability of that name (built; the module provides this name and the owner has not yet confirmed it as final, see "Open questions"), requiring `model-bridge`. One
command, `wb run action-review review`, takes the line of the command to be reviewed and, by that line, finds the
rule, runs the module's `describe`, applies the rule's checks, and only if the checks pass asks the bridge for a
verdict against the rubric. It prints one verdict object: `verdict` (`approve` or `decline`), `failed_checks` and
`reason`, the shape of today's verdict schema. It keeps a log of verdicts as hashes, not command text.

- **Rule properties fixed here; the schema is in "The rule schema, the module and the checks" below.** A rule file has
  a `format` number, and a rule is keyed by one spelling and one subcommand, matched on whole tokens (never a text
  prefix). Two rules with the same key are both refused, and neither reviews anything. A rule that does not load, or
  is ambiguous, refuses only the commands of its own key. Each flag it declares has a type (value, multi, boolean),
  and positionals are declared as exactly one named group. The versioned schema, its field types and bounds and the
  precedence rule were written by Increment A of plan `2026-10-26-action-review-engine`; the tests for malformed and
  overlapping rules are written by that plan's later increments, before the code they test.
- **Rules are data** (a JSON file per rule: the command spelling, the module and the action that `describe`
  reports on, the checks, the rubric section, the review questions). The module and the action are identifiers
  only: a rule holds no command text and no verb. The engine builds the launcher argument list itself, `wb run
  <module> describe <action> <the parsed arguments>`, with the fixed word `describe`. A rule format that can carry
  command text, an extra verb or a path to run is rejected, and a rule that names such a field does not load. **The checks are code in the module** and are fixed: a pure function of the facts.
  A rule can only name a check that exists. This keeps the owner's finding that a rule file is not a place to put
  logic.
- **Fail closed, and loudly.** A rule file that does not load makes `review` refuse that rule with a message the
  hook can show. It never disables the review of other commands. This is a change from the approver.
- **The prompt holds the facts and the rubric; the call is confined, which is a tripwire and not a boundary.** Content from a hostile
  repository (a diff, a message) is quoted as data and the rubric keeps the check that refuses text addressed to the
  reviewer (`no_reviewer_directed_text`). That is not an isolation boundary. The engine always passes `--confine` to the bridge
  (plan `2026-11-04-shadow-hook-security-review-fixes`, increment C; "The bridge call is confined" below), so the vendor program
  starts with its tools that read files, run commands or reach a network switched off. Without that, `model-bridge.md` ("What the
  vendor program can read") says it can open any file in the project, including untracked scratch and the repository's own
  instruction files, so repository text could reach the model by that route as well; what a confined program can still do is
  listed in "Confinement" there. The spec therefore claims only this: the engine puts nothing sensitive in the project for the
  vendor to find (the labelled set is stored outside any project, see below), and it does not rely on the model
  ignoring what it reads. A bridge option for a scratch root with no project content would be a change to
  `model-bridge.md`, which the engine's plan may propose; none exists today.

### The rule schema, the module and the checks (specified by plan `2026-10-26-action-review-engine`, Increment A; built by Increments B to K)

Everything here is the author's text for the owner to read; it is a default until the owner has read it and said to go
on. Marked calls are the author's. The module is built for `commit` and `remove`; where the build differs from this
text, the text below has been changed to the built form, and "As built, and its limits" lists the departures from what
Increment A first wrote and what remains open.

**The module.** `packages/workbench/action-review/` declares `type` `module`, `provides` `["action-review"]` and
`requires` `["model-bridge"]`. It ships `helper/action-review`, each rule file (`rules/safe-git-commit.json`,
`rules/safe-git-remove.json`), `rubric/rubric.md` and `reply-schema.json`, so they install at
`.workbench/<package>/action-review/<path>` (`module-contract.md`). The `ships` list names each file, not a `rules`
directory, because the installer's boundary test forbids a shipped item named by a word the declarations use; a new rule
is therefore added to `ships`. It declares one command, `action-review`, with `helper` `helper/action-review`, `runtime`
`python`, `kit` 1 and `arguments` `["review"]`, and no `owner` list: `review` reads and prints and writes nothing, and
the owner's hook calls it. The launcher runs the helper as a private copy with nothing beside it, so the helper reads its
rules, rubric and schema from the installed path below the project root that `project.find_root` finds from the working
directory (the nearest project); the package name in that path is the fixed word `workbench`.
It never takes a path from the caller or from a rule. Because the project tree is where a repository, or the assistant
under review, can write, the helper holds a SHA-256 for each shipped data file (`PINS`, keyed by the path under the
installed module) and uses a file only when its bytes match: a rule that does not match, or that was not shipped, is a rule
error for its own key and blocks it; a rubric or a reply schema that does not match ends the review (exit 1, nothing run).
A new or changed shipped data file therefore needs a new `PINS` entry in the same release, and a test checks every entry
against the package. The schema is passed to the bridge as its project-relative installed path, because the bridge reads
`--schema` from inside the project and the engine writes no file.

**The call.** `wb run action-review review [--log-row] [--collect] <command text>`. The command text is exactly one argument, the
raw text the harness is about to run; the launcher allows at most 4,096 characters, so a longer command is
unreviewable. `--log-row` and `--collect`, if given, come first, in either order and each once; a flag that repeats is read as the text, as a
second `--log-row` always was, so the call without `--collect` reads exactly what it read before. Any other option, a second
text, or none is a refusal (exit 1).

**The rule file.** One file per rule in `rules/`, named `<module>-<action>.json` (for example `safe-git-commit.json`),
UTF-8, strict JSON (a duplicate key, `NaN` or a non-object is an error, as for the owner's profile file), at most 16,384
bytes; at most 64 files and 262,144 bytes in all, and a file that is not a regular file, is read through a link or has a
second hard link is an error for its own key. The bytes must also equal the shipped file's SHA-256 (above). The object has
these fields and no others; a missing required field, an unknown field or a wrong type means the rule does not load.

| Field | Required | Type and bounds |
|---|---|---|
| `format` | yes | the whole number 1 |
| `spelling` | yes | a list of 1 to 4 words, each of the bare-word alphabet of the grammar below, not beginning with `-`, at most 64 characters: the leading words of the prompted command |
| `subcommand` | yes | `^[a-z][a-z0-9-]*$`, at most 32 characters: the word that follows the spelling |
| `module` | yes | the name of the command `describe` is asked of: `^[A-Za-z0-9][A-Za-z0-9._+-]*$`, at most 64 characters. `wb run` takes a command name, so this is that name; for a first-party module whose command carries its name (`safe-git`) it is also the module's name. The engine does not look it up: the launcher decides whether an installed, pinned command of that name exists. |
| `action` | yes | `^[a-z][a-z0-9-]*$`, at most 32 characters: the action `describe` is asked about |
| `flags` | yes (may be empty) | an object of at most 32 entries; a key is `--` and `^[a-z][a-z0-9-]*$` (at most 32 characters after the dashes); a value is `{"type": "value" \| "multi" \| "boolean", "required": true \| false}` with `required` defaulting to false; nothing else |
| `positionals` | yes | exactly one group, `{"name": <form of an action>, "separator": true \| false, "min": 0 to 61, "max": 0 to 61}`, `min` at most `max`; `separator` true means the group follows a lone `--` word that is itself required. The 61 is the kit's ceiling of 64 arguments to `run_command` less the fixed `describe` call's three (`<module> describe <action>`); a command whose parsed arguments pass 61 is unreviewable (exit 1), so a commit of more than about 50 paths is never reviewed |
| `checks` | yes | a list of at most 32 distinct names, each in the engine's fixed list (below); a name not in it means the rule does not load |
| `rubric` | yes | the name of a section of `rubric.md`, `^[a-z][a-z0-9_]*$`, at most 64 characters; the section must exist, which is checked when the review reads the rubric and not when the rule loads |
| `questions` | yes (may be empty) | a list of at most 16 distinct names, each `^[a-z][a-z0-9_]*$` and at most 64 characters, each a question defined in the named rubric section; a name not defined there is a rubric error for the rule's own key (exit 1), found at review time |
| `lists` | no | an object whose keys are in the engine's fixed list of list names (`credential_names`, `reviewer_facing_paths`) and whose values are lists of at most 256 distinct printable ASCII strings of at most 256 characters; data for the checks that name them, and it is where the approver's credential-name list and its list of reviewer-facing paths move. An entry may hold `*` (a glob over the final path segment) and may end in `/` (a directory name, matched against any directory above the file), because the approver's patterns cannot be said otherwise. A rule that names `paths_not_credentials` with no `credential_names` list fails that check |

A rule holds no command text, no verb and no path to run, and no field has a place for one: the engine builds
`wb run <module> describe <action> <the parsed arguments>` itself, with the fixed word `describe`, and `spelling` is
only what the prompted command is matched against and is never executed or passed on. Two loader rules keep the
reviewed command equal to the one that runs. The `subcommand` must equal the `action` or the rule does not load. And
where `spelling` begins `wb run`, its last word must equal `module` or the rule does not load. For another spelling
(`git push`, when a push rule is added) the equivalence is the module's own `describe` contract, which takes the
arguments of the real command (`describe push` takes those of `git push`, as `safe-git.md` says); that is why a later
push rule needs no change of this format. The file name must equal `<module>-<action>.json` or the rule does not load.

Example, `rules/safe-git-commit.json` (the checks are those of "The checks", below; the lists are abbreviated here):

```json
{"format": 1, "spelling": ["wb", "run", "safe-git"], "subcommand": "commit", "module": "safe-git", "action": "commit",
 "flags": {"--expected-head": {"type": "value", "required": true}, "--subject": {"type": "value", "required": true},
           "--body": {"type": "value"}, "--trailer": {"type": "multi"}, "--leave-other-staged": {"type": "boolean"}},
 "positionals": {"name": "paths", "separator": true, "min": 1, "max": 61},
 "checks": ["head_matches", "repo_config_safe", "staging_state_ok", "paths_valid", "message_valid",
            "paths_not_credentials", "paths_regular", "facts_complete", "no_secret_lines"],
 "rubric": "commit", "questions": ["message_matches_change", "scope_is_coherent", "change_is_safe_in_itself",
                                   "no_reviewer_directed_text"],
 "lists": {"credential_names": [".env", "id_rsa"], "reviewer_facing_paths": ["AGENTS.md", "CLAUDE.md"]}}
```

and `rules/safe-git-remove.json`: `subcommand` and `action` `remove`; `flags` `--confirm` and `--recursive`, both
boolean; `positionals` `paths` with `separator` true, `min` 1 and `max` 61; `checks` `facts_complete`,
`confirm_present`, `removal_valid`, `ignore_status_known`, `preview_matches_arguments` and `no_git_metadata`; `rubric`
`remove`; `questions` `targets_look_disposable`, `scope_is_narrow` and `no_reviewer_directed_text`. The flags of both
rules are those of the real commands in `safe-git.md`; the build checks them against the helper. (The flag names above
were read against `parse_commit` and `parse_remove` of `safe-git` by Increment D; they were read, not run against them,
and `describe` is the real validation.)

Cases that must not load, each with a test: a field outside the table; a missing required field; a `format` other than
1; a `module`, `action` or `spelling` word outside its form; a `subcommand` unequal to `action`; a `wb run` spelling
whose last word is not `module`; a file name that is not `<module>-<action>.json`; a check or list name that is not in
the engine's list; a question the rubric section does not define; a flag of an unknown type; two positional groups or
none; `min` over `max`; an over-long value, list or file; and any field that carries a command line, a verb, a path or
a program name (there is no field for one, so it is an unknown field).

**Matching and precedence.** The prompted command is parsed once under the grammar below into words. A rule matches
when the command's leading words equal `spelling` and the next word equals `subcommand`, whole word against whole word.
There is no precedence and no order among rules. If exactly one rule matches and it loads, it reviews. If no rule
matches, the command is not reviewed: a refusal (exit 1) that names no rule, which is also how a retired action
(`ask-codex archive`, `safe-committer`, `amend-message`) is refused, with no `describe` and no bridge call. If two or
more rules match, or two files carry one key, every one of them is refused and nothing is reviewed under that key. A
rule that does not load refuses only the commands of its own key: its key is read from its `spelling` and `subcommand`
when both are valid, and otherwise from its file name, where a command is refused when two adjacent words among its
first five, joined with a `-`, equal the file's name without `.json`. A rule error is reported on
standard error as `rule error: <file name>: <fixed reason>` (the name `ascii()`-escaped, the reason fixed text that never
quotes the file), never as a verdict, and does not disturb the review of any other key. These notes are not cut to the 500
characters of a refusal (at most 32 KB in all).

**Flags and positionals.** After the subcommand, a word beginning with `--` is a flag and must be declared by the rule.
A single-quoted word that begins with `-` is refused outright, so a quoted word is never a flag in the engine and a
flag in the real command; `--name=value` is refused as an undeclared flag. A `value` flag takes the next word as its value; a
`multi` flag may repeat and gathers its values in order; a `boolean` flag takes no value; a `value` or `boolean` flag
given twice is a refusal, and so is a `required` flag that is absent, an undeclared flag, a flag with no value, a
second `--` word, and a count of positional words outside `min` and `max`. A bare word that begins with `-` and is not
a declared flag is a refusal. Positional words are those after the lone `--` when `separator` is true, and the bare
words that follow the last flag when it is false. The result is an argument list in the order given, which is passed to
`describe` unchanged; the parse only decides whether the shape fits, and the real validation is `describe`'s.

**The checks.** The engine has a fixed list of code checks, each a pure function of the `describe` object (and, for two,
of a named list), run in the order of the list and not of the rule. A rule may name only checks in the list. `ok:
false` is a fact: each error code maps to the check that would have caught it, and that check fails (a code with no
mapping fails `facts_complete`). The checks for the two actions this plan covers, from `safe-git.md` ("Each check of the
approver, and where it goes"):

| Check | Action | Reads | Fails when | Error codes it also fails on |
|---|---|---|---|---|
| `head_matches` | commit | `head`, `expected_head` | they differ; a null `head` passes only with `expected_head` `none`, and any other null fails | `expected_head_invalid`, `head_mismatch`, `head_unreadable` |
| `repo_config_safe` | commit | `program_findings` | it is not empty | `repo_selects_program`, `operation_in_progress` |
| `staging_state_ok` | commit | `staged_paths`, `leave_other_staged` | something is staged without `leave_other_staged` | `index_has_staged_changes`, `path_already_staged` |
| `paths_valid` | commit | `ok` | a path error | `usage`, `path_refused`, `path_duplicate`, `path_unmerged`, `path_in_nested_repository`, `path_not_a_file`, `path_unknown`, `path_converts_on_add`, `whitespace_errors` |
| `message_valid` | commit | `ok` | a message error | `subject_invalid`, `body_invalid`, `trailer_invalid`, `message_character_refused`, `attribution_refused`, `setting_invalid` |
| `paths_not_credentials` | commit | `requested_paths`, `paths`, list `credential_names` | the final segment of a path, case-folded, equals a listed name, or ends with a listed name that begins with `.` (an extension such as `.pem`); as built, an entry may also hold `*` or end in `/` (see `lists`) | none |
| `paths_regular` | commit | `not_regular_paths` | it is not empty | none |
| `facts_complete` | commit, remove | `truncated`, and for a commit `binary_paths` | `truncated` is true, or a commit has a binary path | `repository_unreadable`, `index_unreadable`, and any unmapped code |
| `no_secret_lines` | commit | `diff`, `subject`, `body`, `trailers` | the secret scan (ported from the approver by Increment F) hits; a hit withholds the diff from anything sent to a bridge | none |
| `confirm_present` | remove | `confirm` | it is false | none |
| `removal_valid` | remove | `ok` | a removal error | `usage`, `path_duplicate`, `path_refused`, `target_missing`, `recursive_required`, `repository_root_refused`, `nested_repository`, `other_filesystem`, `tree_too_large`, `target_changed` |
| `ignore_status_known` | remove | `ignore_unknown_targets` | it is not empty | none |
| `preview_matches_arguments` | remove | `target_paths`, `requested_paths`, and the paths the command names | they differ from each other (same order and repeats) or from the command's own paths (added by Increment K: without them the check compares two lists that `describe` produced from one input) | none |
| `no_git_metadata` | remove | `requested_paths`, and the paths the command names | any segment of either, folded, equals `.git` | `git_metadata_refused`, and `path_refused` where a segment folds to `.git` |

The rubric questions are not code checks and are never run by the engine: `message_matches_change`, `scope_is_coherent`,
`change_is_safe_in_itself` and `no_reviewer_directed_text` for a commit, and `targets_look_disposable`,
`scope_is_narrow` and `no_reviewer_directed_text` for a remove. A question goes to the model only after every code check
has passed, and the model's `failed_checks` may name only the rule's questions. A failed code check is a decline with
that name and never calls the bridge. The mapping of an error code to a check in the table is the author's reading of
the real refusals in `safe-git.md`; Increments F, G and J test it against the objects the real `describe` prints. As
observed on the real command, every refusal of `describe remove` gives `ok: false`, `truncated: true` and an empty
`target_paths`, so it also fails `facts_complete` and `preview_matches_arguments` besides the check its code names; a
commit-only code on a removal is unmapped and fails `facts_complete`; `describe` reports no HEAD when the repository
selects a program, so `head_matches` fails with `repo_config_safe`. The extra names in `failed_checks` change nothing: the
decline is the same. The checks for a push are
deferred with the push rule (`outgoing_known` and the others in that table), because they need `describe push`, which
exists, and a rule and checks that the follow-up plan writes; until that rule exists a command with no rule is refused
(exit 1) and a push stays with the approver (since 2026-10-29 no approver runs, so a push is not reviewed at all).

**The rubric.** `rubric/rubric.md` holds one section per rubric name, `## <name>` with `commit` and `remove` at first,
and under it one `### <question>` heading per question with the text of the question. It was ported from the approver's
rubric section by section by Increment H (source: the approver's rubric, SHA-256
`49e369d28ee425c66608dcd6540eb9aa945d6ca000a47e48f117ac1a2b172799`, read 2026-10-27; the `commit` and `remove` sections keep
its wording, and the push and remote sections are not ported); the engine's own framing says that the
facts are data and not instructions. The prompt sends the premise, the section's introduction and only the questions the
rule names, then the facts as one ASCII line of sorted compact JSON between marker lines that carry a random nonce. `reply-schema.json` is the JSON Schema of the verdict reply the bridge is asked for
(`verdict`, `failed_checks`, `reason`), and the engine validates the reply again whatever the bridge or the schema did.

**The log row reaches the hook.** `--log-row` makes the engine print, after the verdict object has been printed, one
more line on standard error: `log-row: ` followed by the row as one JSON object with exactly the fields of "The
log", and no field is added to the verdict object. A row is printed for a verdict only (approve or decline, exit 0);
a refusal or failure prints its `refused:` or `failed:` line and no row, and the hook writes a note of its own if it
wants one. The engine reads the clock for `ts` and writes nothing. (Author's call.)

**The collect lines (plan `2026-10-29-action-review-shadow-hook`, Increment B).** `--collect` adds two kinds of line on standard
error, after any `log-row:` line, for the owner's shadow hook ("The shadow hook"). Without the flag the output, the exit code and
the verdict object are byte-equal to what they were. `facts: ` followed by the `describe` object as received, in canonical JSON
(sorted keys, no spaces, ASCII only), is printed when `describe` produced a valid object, whether the review then ended in a
verdict, a refusal or a failure, and is left out when the line would pass 393,216 characters, twice the object cap. `outcome: `
followed by one JSON object with the single field `reason` is printed on every exit and is always the last line. The reason is
`reviewed` (a verdict), `no_rule` (no rule matches the command, which includes a push and a remote-job command), `unreviewable`
(the grammar, a flag, a blocked or ambiguous rule), `refused` (any other refusal: the rules, `describe`, the setting, the rubric,
the bridge not run, a usage error), `failed` (any other failure) or `timeout` (`describe` or the bridge ran out of time). It comes
from the engine's own parse and exit path; the hook never parses the command. A bridge that reports its own timeout is
`timeout` too: the bridge is given a shorter time than the engine so that it reports first. A `reviewed` outcome with no `facts:`
line (the line was over the bound) is a command the hook cannot collect. If a write of these lines fails after the verdict
object was printed, the exit is 2 as for the row, and the fallback may repeat the `facts:` line before `failed:` and the final
`outcome:`; a hook that takes the last line of each kind and trusts the exit code reads it correctly. (Decided by the owner on
2026-10-29.)

**The time budget (author's call, provisional).** The engine's 25 seconds are one deadline for the whole review. `describe`
may use up to 5 of them and the bridge call gets the rest; the bridge is always passed `--timeout 20` and the engine's
time limit on the call is the deadline's remainder, so the two add to no more than 25. A `describe` that is not done in
5 seconds is a refusal (exit 1, as for any failed `describe` run in the plan). The 5 seconds are a guess and are
revisited with the other figures once the shadow period has logged the engine's own durations.

**The bridge call is confined** (plan `2026-11-04-shadow-hook-security-review-fixes`, increment C; found by the second security review of
the shadow, 2026-11-04). The prompt holds captured text that an agent can write (a commit's diff and message), and `model-bridge.md`
("Confinement") says a caller that sends captured text through a bridge to a program always passes `--confine`. The engine therefore
asks exactly `<bridge> ask --timeout 20 --schema <the shipped reply schema> --confine [--model <m>] [--effort <e>]`. A bridge that
refuses the option, with no output object, is a refusal (exit 1); a bridge that prints a failure object or fails some other way is a
failure (exit 2); either way the call is not repeated without the option. What is and is not shown: the bridge's own confinement
evidence stands (the probes of 2026-11-01 in `model-bridge.md`, which used no reply schema); the engine's confined call with its reply
schema has not been run against a real Codex, so the owner's test-set run is its first use. A case that fails there is reported by the
runner as not run, with the engine's exit code; the cause is in the engine's own `refused:` or `failed:` line, which the runner does not
show (a runner that showed it would be a change of its own). **Nothing in the engine checks that the installed `codex` is a release that
passed the release check** ("Release check for untrusted text" in `model-bridge.md`; `codex-cli` 0.163.0 passed it on 2026-11-01, and the
owner runs the check again for every release they install): the confinement arguments name the program's feature list as of that
release, and a renamed feature fails closed, but only the owner's check says the combination still holds. The owner's steps say so. A bridge that
cannot switch off any tool (a bridge to a server) meets the rule by construction, and one that cannot honour the option refuses it.

**A fact that is absent or of the wrong type.** A check reads only the facts named in its row. If an `ok: true` object
lacks one of them, or it has the wrong type, that check fails (it never passes by default), and `facts_complete` fails
with it. An `ok: false` object keeps the names the module always gives it (`safe-git.md`), so the same rule applies.

**Where `describe` runs.** The engine runs `describe` from the working directory it was started in, and the hook
starts `review` in the directory where the harness will run the command. The spec does not make the engine check this;
a hook that starts it elsewhere gets facts about another repository. That is a requirement on the owner's hook.

**A rules directory that cannot be read, or is too large.** If `rules/` cannot be read, has more than 64 files or
holds more than 262,144 bytes, no rule is trusted to match: every review is refused (exit 1) with that reason. Within
the limits, a single bad file refuses only its own key, as above.

**A code-check decline has no bridge.** The log row's `bridge`, `model`, `effort` and `rubric_sha256` are null when the bridge was not
called.

**What the loader does not check.** For a spelling that does not begin `wb run`, nothing ties `spelling` to `module`;
that rests on the owner's review of the shipped rule data and on the module's `describe` contract. A later push rule
is the intended case (`["git"]`).

### The reviewed command is the command that runs (default)

A review is useless if it examines something other than what executes. The engine takes the prompted command as the
raw text the harness is about to run, and as one canonical form from the hook to `describe`:

- **Accepted grammar (a restricted subset, so that every shell reads it alike).** The text is a sequence of words
  separated by exactly one space each, with no leading or trailing space, in at most 4,096 characters. A word is either a
  bare word made only of `A-Z a-z 0-9 . _ / : = @ % + , -` (not beginning with `-` unless it is a flag the rule
  declares), or a single-quoted string: `'`, any characters except `'` and newline, `'`. The built parser refuses, beyond
  the alphabet, five forms that some shell would read differently: a bare word that begins with `=` (zsh expands `=cmd` to
  a path); a bare first word that holds an `=` (an environment prefix, `A=1` and `A+=1` alike); a bare word that holds
  `==` or `:=` (zsh with `magic_equal_subst` expands the word after an `=` or a `:`); NUL inside quotes; and a character
  that cannot be encoded as UTF-8. A quoted word that begins with `-` is always refused. Nothing else is accepted: no double quote, backslash,
  `$`, backtick, `*`, `?`, `[`, `~`, `{`, `#`, `;`, `&`, `|`, `<`, `>`, `(`, `)`, newline or tab outside a
  single-quoted string, and no environment prefix. Inside single quotes every character is literal in POSIX shells
  and in zsh, so the word means the same to all of them. A command that does not fit is unreviewable and approves
  nothing; the owner then sees the normal prompt. A commit message that needs a single quote is written without one
  or in a body file the helper takes, which the plan of `describe` may add.
- **The corpus is a test of a stated grammar.** The grammar above is exact, so the equivalence test is a property
  test over generated command text and not a sample: every accepted text parses to the same argument list in the
  engine and in `sh` and `zsh`, and every other text is refused. As built (Increments C and K), the test compares the
  engine with an independent regular-expression reading of the grammar over about 9,000 generated and random texts and
  every pair of characters, and runs generated text through real `sh`, `zsh` and `bash` with a program that prints its
  arguments. Only `/bin/sh`, `zsh -f` and `bash` without start-up files were tested, so **it is a requirement on the
  hook that the shell reading the command runs with no alias, no global alias and no start-up file option**; the
  grammar cannot defend against those.
- **One parse.** The rule's declared flags parse the arguments once. The result is an argument list, never a shell
  string, and `describe` receives that list through the launcher, with the fixed verb `describe`, so the facts are of
  the arguments the real command will receive.
- **Unknown means unreviewed.** A flag the rule does not declare, a repeated single-valued flag and a missing
  required flag refuse the review.
- **Tested.** A corpus of quoting, spacing, wrapper and shell-metacharacter forms shows that the argument list the
  engine reviews equals the argument list the real command parses from the same text, or that the review is refused.

### The verdict, the output and the log (default)

These are the author's proposals, settled by plan `2026-10-25-describe-interface-documented` for the plan that
builds the engine, and built by Increments I and K of plan `2026-10-26-action-review-engine`. The rule schema is not
here: it is in "The rule schema, the module and the checks".

**The verdict object.** `wb run action-review review` prints exactly these fields and no other:

- `verdict`: the string `approve` or `decline`.
- `failed_checks`: an array of distinct strings, each a check name (`^[a-z][a-z0-9_]*$`, at most 64 characters) from the
  rule's checks, whether code checks or rubric questions. It is empty when the verdict is `approve` and not empty when
  it is `decline`; any other combination is malformed. At most 32 entries.
- `reason`: a string of at most 300 characters, display-cleaned (no control character, ASCII only). The bound is the
  length the approver already logs (`LOGGED_REASON`, read 2026-10-25).

A response from the bridge that does not fit this, once the engine has applied it, is not passed on: the engine's own
verdict is a decline or a failure, never a malformed object.

**Output and exit status.** One JSON object and a final newline on standard output, or nothing on standard output.

| Outcome | Standard output | Exit |
|---|---|---|
| a verdict, approve or decline | the verdict object | 0 |
| a refusal: a rule that does not load or is ambiguous, an unpinned or undeclared module or bridge, an unreviewable command, a `describe` object that is malformed (a `truncated: true` object is well formed and is a decline, not a refusal) | nothing; `refused: <reason>` on standard error | 1 |
| an engine failure: the bridge fails, times out or returns something unusable; an internal error, an interrupt or an exit inside the review; a verdict, a log row or a flush that could not be written | nothing from the review itself; `failed: <reason>` on standard error | 2 |

As built, a bridge that was not run because it was refused (exit 1 with no object) is a refusal, and every other bad
answer from a bridge, a timeout and an oversize answer are failures. The helper computes the verdict line and the row
first and writes afterwards: the object, then a flush, then the row, and it exits 0 only when all of them succeeded. If
the row cannot be written after the object was printed, the exit is 2 with a whole object already on standard output, so
**the hook must allow only on exit 0 together with a whole, valid object**, never on the object alone; a closed
standard error makes every review exit 2.

The reason is at most 300 characters and is display-cleaned, for the hook to show. A decline caused by `truncated:
true` or by `ok: false` is a verdict (exit 0, `decline`), because the review ran and the checks said no. Only an
object on standard output, with exit 0 and `verdict` equal to `approve`, can lead the hook to allow anything; every
other outcome leaves the owner at the normal prompt. The hook reads the object, never the exit status alone, and
applies the same field rules to it (an approve with a non-empty `failed_checks`, an extra field or a wrong type allows
nothing). A decline also exits 0, so a hook that tested the status alone would read a decline as an approval; the
spec rules that out and the hook's tests show it. This contract differs from the bridge's (`model-bridge.md`), where
exit 1 with a valid object is a failure; the engine's exit 1 and 2 print no object.

**The log.** The engine hands back the row (`--log-row`); the writer is the owner's shadow hook (`hook/shadow_hook.py`), which
keeps it in `verdicts.jsonl` with a hook timestamp and the outcome of every prompted command ("The data files"; the engine's
`command_sha256` is replaced there by the hash of the raw command text). The engine's row is one JSON line per review, append-only, with these fields and no others: `ts` (UTC, to the second);
`rule` (the rule file's name without `.json`, for example `safe-git-commit`, which the loader forces to equal
`<module>-<action>`; not the spelling-plus-subcommand key);
`verdict`; `failed_checks`; `reason` (as above); `command_sha256` (of the JSON of `[module, "describe", action, *arguments]`, the canonical argument list the engine
built, not of the raw text); `facts_sha256` (of the canonical serialization of the `describe` object as received);
`rubric_sha256` (of the rubric text sent); `bridge`, `model` and `effort` (`bridge` and `effort` are the setting's; `model` is the model the bridge reports, and the
setting's request only when the bridge reports none; all three null when the bridge was not called); and `format` (the engine's log
format number). It holds no command text, no fact and no diff, with two residual exposures: `reason` is bounded,
display-cleaned model output that could quote a path or a line it was shown, and a hash of a short argument list can be
guessed by dictionary, so "hashes, never text" is not secrecy. It lives outside every project, in the owner's own data
directory (`~/.config/project-workbench/action-review/`, see "The shadow hook"), so a vendor program that opens files in the project cannot find it. The owner
decided on 2026-10-25 that the owner's thin hook writes it, from the row the engine hands back, and that a failed write
never withholds an approve (below, "Decided by the owner"). The engine writes nothing outside the project; the row
reaches the hook through the `--log-row` flag, which prints it as one `log-row:` line on standard error, without
adding a field to the verdict object (see "The rule schema, the module and the checks").

**How the engine learns that a command is pinned and declared.** Only part of this is settled today:

- *Pinned: settled.* The engine does not look pins up. It starts the command with `wb run`, and the launcher refuses a
  command that no installed module declares, whose pin is absent or names another helper, or whose helper changed since the owner pinned it, and, for a pin the installer made, whose declaration changed
  (`module-boundary.md`, "A helper that runs another module's command"; a hand pin records no declaration hash). The
  engine treats any refusal as a refusal of its own (exit 1) and approves nothing. `wb run` takes a command name, not
  a module name, so a rule's module and action must map to a command name; the engine's plan fixes that mapping.
- *Declared: built.* The engine reading `module.json` itself would be a second check of a declaration the launcher
  already hash-checks, with a different trust. The owner decided on 2026-10-25 that the launcher enforces it: when a
  command's first argument is `describe`, `wb run` refuses unless the second argument is in the command's `describes`
  (`module-boundary.md`, "Declaration schema"). The rule is generic and names no module or action. The engine then
  needs no knowledge of declarations, and a refusal is a refusal of the engine (exit 1). Plan
  `2026-10-25-safe-git-describe` built the rule and `safe-git` declares it.

**The timeout.** Decided by the owner on 2026-10-25, as provisional figures: the bridge's `--timeout` is 20 seconds,
the engine's own limit is 25 seconds, and the hook's limit is 30 seconds, so each layer reports before the one outside
it ends it (`model-bridge.md` requires the engine's limit to exceed the bridge's). The source is the approver's log,
read on 2026-10-25: 876 reviews, the median model call 7.5 seconds, the 95th percentile 13.4 seconds, and 20 reviews
(about 2%) ended at the approver's 15-second limit with no verdict; the approver's hook limit is 25 seconds. The engine
adds the launcher, `describe` and a larger fact set, so the margin is wider. The figures are revisited when the shadow
period has logged about 30 of the engine's own reviews. A review that times out leaves the owner at the normal prompt.

### Settings and the bridge

**As built (plan `2026-11-04-review-profiles`, increment F).** The bridge, the model, the effort and the options come from the one rung
of the `action-review` ladder of the owner's `review-profiles.json` in the guarded store (accepted record
`2026-11-04-review-profiles-in-the-guarded-store`, which superseded `2026-10-26-action-review-reads-the-review-setting` and decision 5
of `2026-10-22-model-calls-go-through-vendor-bridges` for this file; the format and the ladder rules are in `review-profiles.md`).
It is a request and never an authorization. `.workbench/review.json` is read by nothing.

- **The reader is the kit's.** `wbkit/profiles.py` reads the file, whole or refused whole, as the review engine does. This engine
  names the ladder keys it accepts (the four kinds of document, `default` and `action-review`) and holds `action-review` to exactly one
  rung. A missing or refused file, a missing `action-review` ladder (`default` never serves it) and a ladder of more than one rung
  are refusals (exit 1) that name the file and a fixed rule and never quote the file; there is no default bridge, and the engine
  never guesses a vendor to send content to. The call is `ask --timeout 20 --schema <the shipped schema> --confine`, then
  `--model` and `--effort` when the profile has them, then each option as `--<name> <value>` in the order of their names. As in the
  review engine, the engine does not check an option against the bridge's declaration: the bridge refuses an option it does not
  accept, and that is a refusal of the review. A profile cannot change the time budget (25 seconds in all, the bridge given 20).
  A drift test compares the ladder keys of this engine, the review engine and the test-set runner.
- The bridge must be an installed, pinned module that provides `model-bridge`; the engine starts it through the kit's
  `run_command` with `--provides model-bridge`, and the launcher refuses one that is not. A name that is refused ends
  the review (exit 1) and no other vendor is tried.
- The bridge's object is checked again under `model-bridge.md`, whatever the bridge did. The engine accepts contract
  versions 1 and 2, and the object must fit the version it names: the error class `program_not_found` and a `usage` of
  three counts belong to version 1, and the class `vendor_unreachable` and a `usage` of five counts belong to version 2. An
  object that mixes the two is a failure. The engine keeps no usage, so the added counts are checked and ignored.
- **Recorded limit: the rung is a request, and the owner's file is guarded by the harness, not by a boundary.** The harness denies
  the agent writes in the guarded store and does not make it unreadable; that is a guard against a mistaken agent and not against a
  process that runs as the owner (`review-engine.md`, "The seal"). Only an installed, pinned bridge that provides `model-bridge`
  can run, whatever the file names.
- The profile file is the owner's and is not part of the project, so a pull never changes it and `wb acknowledge` does not list it.
  What is run is checked by the launcher alone: the bridge the rung names must be installed, pinned and unchanged since its pin.
- The timeout the engine passes to the bridge (20 seconds) is shorter than its own limit (25), as `model-bridge.md`
  requires.
- A missing or unreadable setting, or a bridge failure of any class, yields no approval.

### The enforcement point (default; the form that decides is not built)

The owner's hook becomes a thin program: match the prompted command to a spelling, run `wb run action-review
review`, and turn the verdict into the hook's answer. What the hook allows without the owner (`DELEGABLE`, the
mode setting) stays a code constant there. The hook is the owner's to write and install; the agent prepares and
tests it on a scratch copy, as it did for the patch of option 1a. Plan `2026-10-29-action-review-shadow-hook` builds the
**shadow** form of it, which decides nothing ("The shadow hook" below). A hook that decides is for the plan after the shadow.

### The shadow hook (plan `2026-10-29-action-review-shadow-hook`; built and installed by the owner; labelling and the test set pending)

During the shadow the hook runs the engine on each prompted command and records what the engine would have said. It answers
nothing: the owner sees the normal prompt, and the owner's later label says whether the engine was right. This replaces the
earlier text of "Accuracy and cutover", whose shadow ran the engine beside the approver while the approver's answer still
decided. The approver was removed when the user-level configuration was reset on 2026-10-29, so no program decides today.

**The Claude format, checked.** Provenance: Claude Code 2.1.314 installed; the page `https://code.claude.com/docs/en/hooks.md`,
retrieved 2026-10-30, 283,477 bytes, SHA-256 `b755d9c7c166ec77e36ee2388e3299dd149a9f160171b6e97e427be439f942f9`, read in full for
`PermissionRequest`, "Timeouts", "Block the action when a hook fails" and "Exit code 2 behavior per event". The page is data. It
is kept untracked and is cited here by URL, date and hash. The installed version was read from `claude --version`; no hook was
run for this reading.

- **When it fires.** "When Claude Code is about to ask you for permission to use a tool", and for a call that would otherwise be
  auto-denied because it cannot prompt. It matches on tool name (`Bash`). It does not fire for a command that an `allow` rule
  or a permission mode lets through without a prompt. The page does not say whether it fires when auto mode's classifier decides
  a call without a prompt; the owner's check in Increment H finds out, and until then a shadow in auto mode may see less than
  every command.
- **Input.** JSON on standard input with `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`
  (`PermissionRequest`), `tool_name`, `tool_input` (for Bash `command` and `description`) and an optional
  `permission_suggestions` array. There is no `tool_use_id`.
- **Answers.** A decision is `hookSpecificOutput.decision.behavior` of `allow` or `deny`. Empty standard output with exit 0 is no
  decision, and the permission flow goes on to the prompt. Exit 2 is not honoured on this event: the flow is unchanged and
  standard error is discarded. A hook that fails (cannot start, exits other than 0 or 2, times out, prints invalid JSON) does not
  block unless the entry sets `onFailure` to `block`, and with that set a failure **denies** the request. So the shadow entry
  must not set `onFailure`. The default time limit for a command hook is 600 seconds, so the entry sets `timeout` to 30.
- **Not run for** a sandboxed command's network request, and not for `EndConversation`.
- **In a session that cannot prompt** (a background subagent in non-interactive mode) the hook still runs and, if no hook decides,
  the call is denied. That is the harness's rule, not an effect of the shadow hook, which decides nothing.

**The engine's collect lines (decided by the owner on 2026-10-29; Increment B builds them).** With `--collect` the engine prints,
on standard error after the `log-row:` line, a `facts:` line holding the canonical JSON of the `describe` object when `describe`
ran, and an `outcome:` line, always last, of strict JSON with one `reason` of `reviewed`, `no_rule`, `unreviewable`, `refused`,
`failed` or `timeout`, taken from the engine's own parse and exit path. The command is parsed once, by the engine; the hook
never reruns `describe` and never parses the command. Without the flag the output is unchanged.

**What the hook does.** It reads the input within a bound and takes `tool_name`, `command` and `cwd`. It does nothing for a tool
other than `Bash`. It calls `wb run action-review review --log-row --collect '<command>'` from `cwd`, by an absolute path to
`wb` that the owner sets when installing it, never found through `PATH` or the project, with a clean environment, the shell
requirements of "The reviewed command is the command that runs", and a 30-second limit. It takes the `log-row:`, `facts:` and
`outcome:` lines only from the last line of each kind on standard error, writes its rows (below), and prints nothing to standard
output. In every case its exit status is 0. The engine's own parser decides whether a command is reviewable; the hook parses
nothing. A command that matches no rule, including a push and a remote-job command, is `no_rule`, and the engine cannot
tell the two apart from any other command with no rule, so the report does not split them.

*As built (Increment D, `hook/shadow_hook.py`; amended by plan `2026-11-04-shadow-hook-security-review-fixes`, increment B).* It is
called `/usr/bin/env -i <absolute interpreter> -I -B /path/to/shadow_hook.py --wb <absolute path>` with `shadow_store.py` beside it.
`--wb` is required: there is no default launcher, and any other argument, or none, is noted on standard error and nothing is
recorded. **The environment.** The hook takes its home directory, which decides where the rows go and which `HOME` the engine is given,
from the account database (`pwd`) and not from the `HOME` variable, and it notes the fixed line "the hook was not started with
python3 -I" and does nothing when it was not started isolated. That guard sits above every other import of the file, so the hook's own
imports are not taken from a path the environment named. **It cannot stop code the interpreter ran before the file**
(a `sitecustomize` or `usercustomize` found through a hostile `PYTHONPATH` or user site); `-I` makes the interpreter ignore those,
and `env -i` also removes the variables that load code into a process (`LD_PRELOAD`, `DYLD_*`) and still protects if `-I` is
ever dropped, which is why the owner's steps give the entry in that form. Neither protects against code installed with the interpreter
itself (its own `site-packages`): the interpreter is the owner's choice. The tests first show, with a plain interpreter, that the hostile
layout does run code, and then start the hook as a program with that environment and show that none of it runs (`Isolation` in
`test_hook_shadow_hook.py`); `PYTHONSTARTUP`, which only an interactive session reads, is not tested. The stub those tests use runs the
hook file with `runpy`, so they do not exercise the file as the interpreter's own script, nor the real account database. The labelling tool and the report are run by the owner at a terminal,
with the owner's own environment, and still find their directory from `HOME`. The launcher must be an absolute path to an executable file **named `wb`** that is not inside
the command's own directory (after links are resolved) and whose directory name does not hold the path separator; otherwise the
engine is not started and the command is recorded as `failed` (a `:` in the directory's name would split the `PATH` entry). The
launcher's directory is first on the `PATH` of the engine and of everything the engine starts, so it should hold nothing but `wb`
and be writable by the owner alone: anything named `git`, `python3` or `codex` there would shadow the system program (the guarded
store's `bin`, `~/.config/project-workbench/bin`, holds `wb` and a `run/` directory). The hook does not check the directory's owner or mode, and
it refuses a launcher inside the command's own directory but not one in a repository above it; the engine's own lookup drops any
`PATH` entry inside the outermost repository of the command's directory. The engine runs in its own process group with `PATH`, `HOME` and
`LANG` and nothing else in its environment. **The `PATH` begins with the launcher's own directory**, then `/usr/local/bin:/usr/bin:/bin`:
the engine finds `wb` by name in the trusted entries of the `PATH` it inherits (`wbkit/call.py`), so a `PATH` without that directory
made every review `refused: describe could not be started` (security review of the shadow, finding Low 4; plan
`2026-10-30-shadow-review-fixes`, Increment A). The engine is stopped after 27 seconds, which is between the engine's 25 and the
hook's 30, and recorded as `timeout`; its group is killed, and the hook waits at most 2 more seconds for the output of a program
that left the group, so the two waits total 29. The hook believes the engine's `outcome:`
line only when it is the last line of standard error and agrees with the exit code (0 for `reviewed`, 1 for `no_rule`,
`unreviewable` and `refused`, 2 for `failed`, and 1 or 2 for `timeout`: 1 when `describe` ran out of time, 2 when the bridge did) and, for `reviewed`, with a whole verdict object (one line, three
fields, an approve with no failed check); otherwise the command is `failed`. With no `outcome:` line, exit 1 is `refused` and any
other status is `failed`. A command over 4,096 characters is `unreviewable` without starting the engine; malformed input is
`malformed_input` and a tool other than `Bash` is `not_bash`, each with no command hash. A verdict row is written first, then the
collected row (none for a command declined for a secret or a credential-named path), and a failed write is noted without changing
anything else. Nothing the hook prints, writes or returns can be an
answer to the harness: its source holds no answer object and no write to standard output, and the tests read both.

**The data files.** The directory is `~/.config/project-workbench/action-review/`, a subdirectory of the guarded store found from
the account's home directory; no option or file moves it, and the hook takes that directory from the account database, not from
`HOME` (`2026-10-20-fixed-store-location`; the labelling tool and the report, run by the owner at a terminal, use `HOME`). The owner
decided this on 2026-10-29. The store check of the installer (`workbench/store.py`, `Store.ensure`) creates and checks only the
store's root and its four directories (`packages`, `cache`, `projects`, `bin`), reads no other entry, and so tolerates this
subdirectory; read on 2026-10-30. The hook creates it with mode 0700 and its files with 0600, and writes only below it, never to
`settings`, `projects/`, `packages/`, `cache/` or `bin/`. Every file is strict JSON lines, appended with one write under a lock,
through no link and with no second hard link; a line over its cap, with a field the format does not name or that is not strict
JSON is refused on write and skipped, with a count, on read.

- `verdicts.jsonl`: one row for every prompted command the hook sees. Fields: `ts` (UTC, to the second); `command_sha256` (of the
  raw command text, to link a collected row); `outcome`, one of `reviewed`, `no_rule`, `unreviewable`, `refused`, `failed`,
  `timeout`, `malformed_input`, `not_bash`; `verdict` (`approve`, `decline` or null); `failed_checks`; `reason`; `reviewed`
  (a boolean); `no_review_reason` (null when reviewed, else the outcome); and the engine's log-row fields when there is one
  (`rule`, `facts_sha256`, `rubric_sha256`, `bridge`, `model`, `effort`, `format`). It holds no command text, and its `reason` is
  redacted ("Redaction", below). A case where the
  directory cannot be written leaves no row and is noted on standard error; the plan's earlier `store_error` outcome is dropped
  for that reason, since it could never appear in a row.
- `collected.jsonl`: one row per reviewed command, except a command the engine declined because of `no_secret_lines` or
  `paths_not_credentials`, which leaves a verdict row and no collected row (below, "Redaction"). Fields: `id` (a random 128-bit hex string), `ts`, `rule` (the engine's rule
  name, such as `safe-git-commit`, which names the action for the per-action counts), `command_sha256` (of the raw text, equal to
  the verdict row's), `command` (the text as redacted, at most 4,096 characters), `facts` (a redacted copy of the `describe`
  object, at most the object cap of `safe-git.md`), `verdict`, `failed_checks`, `reason` (redacted). It may still hold what the
  redaction does not find, and it is never tracked or inside a project.
- `labels.jsonl`: `id` (a collected id), `label` (`right`, `wrong` or `skip`), `ts`, optional `note` (at most 300 characters). A
  `skip` is a row the owner could not judge; it counts toward neither the labels nor the per-action minimums, and a later row for
  the same `id` replaces an earlier one.
- `testset.jsonl`: one row per dangerous case run through a real bridge: `case`, `ts`, `expected`, `verdict`, `failed_checks`,
  `mismatch`, and the bridge, model and effort.

**Redaction (plan `2026-11-03-redact-collected-diffs`, Increments A and B; `hook/shadow_hook.py`).** The hook redacts the three
texts it keeps before it writes a row: the `command` and the `facts` of a collected row, and the `reason` of both files (the model's
words can quote a secret). A secret that a pattern finds is replaced by `[redacted:<kind>]`, which holds nothing of it, not even its
length. The kinds:
- `private-key`: a whole `-----BEGIN ... PRIVATE KEY-----` block, a PGP block included, or the text from its start to the end when
  the block is cut off;
- `jwt`; `token`: the prefixes `AKIA`, `ASIA`, `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `github_pat_`, `sk-`, `sk-ant-`, `xox[abprs]-`
  and `AIza`;
- `bearer`: the value of an `Authorization` header, or a `Bearer` value of 16 characters or more that holds a digit or a sign;
- `url-credentials`: the user and password before the `@` of a URL;
- `assignment`: the value given with `:` or `=` to a name that holds `secret`, `token`, `password`, `passphrase`, `credential`,
  `apikey`, `accesskey`, `privatekey`, `authkey`, `_key` or `-key`, or given after a flag of such a name, in plain or JSON-escaped
  quotes; an unquoted value is redacted from four characters, and a quoted one when it is not empty.

The keys, numbers, booleans and nulls of the facts are kept, the line breaks stay, and a text with no secret is stored as it was.
`command_sha256` is of the raw command in both files. `facts_sha256` in a verdict row is the engine's hash of the facts before
redaction, so it does not match the stored facts; no tool compares them.

*As built: it is best effort, not a guarantee.* It finds what it names and nothing else. Not found: another service's token prefix
(`sk_live_`, `glpat-`, `npm_`, `xapp-`), a bare `key=`, `pass=` or `pwd=`, a value cut at an escaped quote, a URL password over 200
characters or with a `/`, a value on the line after its name, and a secret that was split. The keys of the facts and the engine's own
fields (`rule`, `failed_checks`, `bridge`, `model`, `effort`) are stored as they are; the store limits the first three to a
lowercase pattern and the others come from the engine's settings, so a key that carried user text is the one gap. It also hides some
facts that are not secrets: `tokens = parse(line)`, a type hint such as `token: Optional[str]`, a path given to `--secret-file`, a branch name
that starts with `sk-` and runs on. The owner then judges from the command and the rest of the facts, or skips. There is no rule by
entropy, because it would hide the git hashes that the owner needs. The work is linear in the text: a test redacts the largest text
the hook can hold (393,216 characters) in each of 24 hostile shapes, with a limit of 2 seconds; the longest took under 0.1 second.

*As built: a command declined for a secret is not collected* (plan `2026-11-04-shadow-hook-security-review-fixes`, increment A; found by
the security review of 2026-11-04). When the verdict is a decline whose failed checks include `no_secret_lines` (the engine's own scan
found a secret in the diff or the message) or `paths_not_credentials` (a credential-named path), the hook writes the verdict row, with its
failed checks and its redacted reason, and no collected row, so the diff, the command text and the facts are not kept. The patterns above
cannot recognise every shape that the engine's scan does (the review found a `glpat-` token, a bare `npm_` token, `sk_live_`, `pwd=` and a
`Basic` header declined by the engine and not redacted). Two shapes were not declined by the engine in that review, `pass=...` and a Slack
webhook, so a commit with only those is approved by the engine and collected as the patterns leave it: that gap is the engine's scan and
the redactor's, it is not closed here, and the report's "reviewed commands with no collected row" count includes the declined ones.

*As built: when a redaction cannot be done.* It raises (an object nested deeper than 64, a key that is not a string, a value that is
not JSON), or the redacted reason would be over 300 characters, or the redacted command over 4,096. The verdict row is then written
without its reason, no collected row is written, and the hook notes it on standard error in fixed text. If the redacted facts make
a line that the store refuses (over 512 KiB), the collected row is lost and the verdict row keeps its redacted reason. Rows written
before this change are not rewritten; none existed when it was made.

Rules the store enforces on every row, written and read (`hook/shadow_store.py`, built by Increment C): a reviewed row names an
approve with no failed check or a decline with at least one, as the engine's verdict does, and a row that was not reviewed holds no
verdict; `reviewed` agrees with `outcome`, and `no_review_reason` is null exactly when it does; `mismatch` agrees with `expected`
and `verdict`. A row with a field the format does not name, a duplicate key, a number too large for a float, text that is not
ASCII, or a line over its cap (verdicts and testset 8 KiB, collected 512 KiB, labels 4 KiB) is refused on write and skipped, with a
count, on read. A file is full at 128 MiB. A writer killed part-way leaves a fragment; the next row starts a new line, so the
fragment is one skipped line. So the hook cannot record an approve that names a failed check as `reviewed`: it records that case
as `failed`. A `reviewed` outcome with no `facts:` line, and a decline for `no_secret_lines` or `paths_not_credentials`, is recorded as a
verdict row with `reviewed` true and no collected row, and the report counts it as reviewed but not collectable, by the `command_sha256`
that links the two files. **A decline for a secret can therefore never be labelled**, so a false decline of that kind does not reach the
labelled set that the false-decline rate is computed from; the owner reads the count of such commands in the report when judging a
cutover.

**Placement of the programs.** `module-boundary.md` ("Module directories") puts a script that something runs at use time in
`ships` and a script for measuring in `tools/`. The hook and the store library it imports are shipped data files under `hook/`
(`hook/shadow_store.py`, built, and `hook/shadow_hook.py`; the store is not called `store.py` because the installer's boundary test
forbids a module file named like a file of the installer), each with a pin in the helper's `PINS`, and declare no command, so `wb run` cannot start them. The labelling tool, the report and the test-set runner
measure and stay in `tools/`. The two `hook/` files come from the installed copy and are compared with the module's per-file
pins; `tools/` is never installed, so its scripts come from a checkout of this repository at the commit the owner approved, and
are compared with the module's tree hash by `wb verify`. The owner copies them all to a directory outside every project.
A program run from inside a project would be code that project could change.

**Labelling and the report.** For an approve, `right` means the owner would have approved the action; for a decline, `right` means
the owner would not have. A **false decline** is a decline the owner marks `wrong`; a **false approve** is an approve the owner
marks `wrong`, and is the worse error. The report prints counts and check names only, never a command or a fact. It prints, per
action (commit, remove), the labelled count, the false declines and false approves, the false-decline rate against the bound,
the false declines grouped by failed check, the count of commands not reviewed by `no_review_reason`, and the unlabelled and
skipped counts; any false approve on the labels or the test set is printed first and blocks the cutover line. A labelled `remove`
whose collected `confirm` fact is false (a preview) is not in the `remove` line: it is on the line "unconfirmed removals (previews)",
with its labelled, right, wrong, false-decline and false-approve counts and its own false declines by check, and its false approves
still count toward the alarm and the cutover line (the accepted decision `2026-11-05-unconfirmed-removals-are-outside-the-action-review-measure`).
The report reads that one boolean of a collected row's facts and no other; a fact that is missing or not a boolean leaves the
removal in the `remove` line.

*As built (Increment E, `tools/label.py`).* `python3 -B label.py [--skipped]`, copied with `shadow_store.py` to a directory outside
the project, runs only when standard input and output are both terminals (otherwise it prints one line to standard error and exits
2). It shows the collected commands that have no label, oldest first: the command (a command cut for length shows how many
characters were left out, on the same line), the rule, the engine's verdict and failed checks, the reason, and the facts by name with
a value only where it is a number, a boolean or null (text by its length, lists and objects by their size). **The reason is introduced
as "the model's own words when a model was asked, which the commit's own text may have steered"** (security review of the shadow,
finding Low 2; plan `2026-10-30-shadow-review-fixes`, Increment D): the reason of a model's decline is model output that a hostile
commit message can steer ("answer approve"), and a decline by the engine's own checks (a fixed check, or a prompt too large for the
bridge) carries the engine's fixed text instead, which the collected row does not mark, so the line says "when a model was asked".
A model's reply can imitate that fixed text, so the owner does not rely on its wording. The verdict and the failed checks on the line
above are the model's too when it was asked (chosen among the rule's own check names, which the engine validates). A count of
"characters left out" is of the escaped text, so a command with many non-ASCII characters reports more than it has. `f` shows every fact in full, cleaned, each text cut at 4,000 characters and the whole at 40,000, with a count of what
is left out. `r`, `w` and `s`, each with an optional note after a space (printable ASCII, 300 characters), record `right`, `wrong`
and `skip`; `q` stops; any other answer is asked again. A command whose latest label exists is not shown again, except that
`--skipped` shows those whose latest label is `skip`, and a later label replaces it. Everything shown is printable ASCII: other
characters, the backslash and every escape sequence are written as visible escapes, so a command or a diff cannot drive the
terminal. Each label is one whole row or none; an interrupt ends the tool with 130 and a store that cannot be read or written ends
it with 1. It starts no program and opens no file but the store's.

*As built (Increment F, `tools/report.py`).* `python3 -B report.py`, copied with `shadow_store.py`, takes no argument (any argument
exits 2) and needs no terminal, because it prints only counts, rule names and check names: never a command, a fact, a reason or a
note, and nothing that is not printable ASCII. It writes nothing. The latest label of each collected command is the one counted; a
skipped command is counted as skipped and not as labelled; a label of a command with no collected row is counted apart. Per action
(the last word of the rule's name, so `commit` and `remove`; others appear as they are met) it prints the labelled count, the
agreements (`right`), the false declines (`wrong` on an engine decline) and the false approves (`wrong` on an engine approve), the
false-decline rate rounded down to a tenth of a percent against the 10% bound ("within" is at most 10%), and the false declines
grouped by failed check. An action of the two with fewer than 10 labelled commands prints "not enough labels" and no rate. The test
set counts each case once however often it ran: a false approve is an expected decline that was approved, a false decline an expected
approve that was declined. **A false approve in any run of a case counts**, not only in the latest (security review of the shadow,
finding Medium 2(a); plan `2026-10-30-shadow-review-fixes`, Increment C): a model is not deterministic, so a clean rerun does not
clear a bad run. The test-set line gives the count in any run and, beside it, in the latest run; the alarm line names up to five of
the cases approved wrongly (their shipped synthetic ids, which the report therefore prints besides counts and rule and check names)
and says how to start again: change the engine if it needs it, delete `testset.jsonl` and run the test set again. **The cutover line
is "met" only when the test set holds exactly the shipped number of distinct cases** (`SHIPPED_TEST_CASES`, 29, which a test pins to
the case file; the report is copied out of the checkout and cannot read the file): fewer reads "the test set has N of 29 cases", more
reads "more than the 29 shipped". It counts the prompted commands from `verdicts.jsonl`, the reviewed ones and the others by reason (the `no_rule`
count says it includes pushes and remote jobs), the reviewed commands with no collected row (matched by the hash of the command
text), the unlabelled and skipped, and the lines each file could not be read from. A false approve on the labels or the test set is
the first line printed and the cutover line then says "blocked". Otherwise the cutover line says "not yet", with its reasons (fewer
than 10 labelled of either action, a rate over the bound for either, or a test set that is missing, short or over), or that the bound
is met on the labels and the test set, which leaves the cutover to the owner; the line then gives the number of test cases and, when
any command is still unlabelled, skipped or reviewed but not collectable, says so. A false decline on the test set is reported and
does not block. Limits: the report counts distinct case names and does not know the names, so any 29 names read as the full set: a
runner that skipped a case plus a stray name, or a hand-written row that replaces a shipped name by another, keeps the count at 29. Rows
carry no engine, rubric or case-file hash, so after a change to the engine a partial rerun can leave a mix of old and new rows (a bad
old run still blocks; to start afresh, delete `testset.jsonl`). The report cannot check that `expected` is right for a case, so a
hand-written row with `expected: approve` for a case that must be declined can never count as a false approve. The limits about
names and `expected` need rows written by hand (the files are not authenticated, and anything running as the owner can write them);
the mix of engine versions needs only a partial rerun after a change. A later
`skip` replaces an earlier `wrong`, as a later label always does, and the skipped count stays visible; and a rule of another module
whose name ends in `commit` or `remove` would be counted with that action (only the `safe-git` rules exist today).

*As built (Increment G, `tools/run_testset.py`).* `python3 -B packages/workbench/action-review/tools/run_testset.py
[--codex-dir <absolute path>]` runs the 29 cases of `tests/dangerous-cases.json` through the real engine and the real `ask-codex`
bridge and records one row per case in `testset.jsonl`. **It runs from a checkout of this repository**, as the one tool of the shadow
that imports the repository: it reuses the scratch-project scaffold of `test_actionreview_dangerous` (the real `safe-git` through the
real launcher in a fresh Git repository, the real engine), with the unit tests' fake bridge replaced by the real `ask-codex` (the
class `EndToEnd` gained `bridge_module` and `review_setting` hooks for it). It runs only when standard input and output are terminals
and the SHA-256 of the case file is the one written in the tool. Only 3 of the 29 cases reach the model (the two controls, which must
be approved, and the reviewer-directed message, which must be declined); the other 26 are decided by fixed code or refused before the
bridge is asked, and send nothing. Before it starts it says so, names the bridge, the model and effort of the `action-review` rung of the owner's
`review-profiles.json`, the Codex directory and that nothing of the owner's is used, and waits for the owner to type `send 3`.
Each case runs in a temporary home into which the Codex directory (`~/.codex`, or `--codex-dir`) is linked, so that the bridge finds
the sign-in; the tool does not read or change anything in it, but the Codex program the bridge runs may refresh its own sign-in there.
The store it writes is the owner's own, found from the real home
directory, never the scratch one. A row holds the expected verdict (`approve` for a control, `decline` for every other case, a
refusal included), what the engine said, and `mismatch`. **A row is written only for a case that ran the way the case file says:**
the engine did not fail, it ended with the exit the file expects, and where the file expects the model to be asked, the model was
asked. A refusal that the file expects is a `decline` with the check name `refused`. Any other case leaves no row and is named under
"not run" with its reason (the engine failed, the engine ended with another exit than the file expects, the model was not asked, or
the scratch project could not be built), so a model that was never asked (not signed in, a refused launcher) cannot read as a clean
decline (security review of the shadow, finding Medium 2(b); plan `2026-10-30-shadow-review-fixes`, Increment B). A profile file the engine would refuse, a missing
file, a rung whose bridge is not `ask-codex` (the only sign-in the tool puts in place) and a rung with options (`ask-codex` takes
none) end the run, before anything is sent, with one
line on standard error; the tool reads the rung through the kit as the engine does. A case that is approved and must be declined is printed first, after the run. A recorded case
decided by other checks than the file names is shown as `differs`, though it is no false approve. After a partial run the tool says
to run the test set again before reading the report. Limits, recorded and not closed: a refusal is recorded on the exit alone, so the reason the file expects
(`refusal_contains`) is not compared, and a scratch project broken so that the engine refuses everything still records the seven
expected refusals (every other case then does not run, which the summary and the exit status show); a case that unexpectedly reached
the model, or reached it twice, is recorded and shown ("the model was asked; the file expects the opposite"), not left out; the two
patterns for the model and effort are copies of the engine's and are not pinned to them. Exit status: 0 done, 1 a case did
not run or the store failed, 2 not a terminal, a bad argument or a refused setting, 3 a false approve, 130 interrupted. The tool was
tested with a fake `codex`; a real model has not been asked.

**Recorded limit: the harness does not deny the agent's reads of the store.** The rendered rules deny edits to
`~/.config/project-workbench/**` and not reads (read on 2026-10-30 in the rendered `settings.local.json`). The collected file is
outside every project, so the vendor program, which starts in the project, does not find it by walking the project, but an agent
that can read user-level paths can read it. The owner's steps include a user-level `Read` deny for
`~/.config/project-workbench/action-review/**`. This is the owner's rule, not one the workbench renders, and a `Read` deny does
not stop a `cat` through the shell, so it narrows the gap and does not close it.

### Accuracy and cutover (default)

The approver is not the standard, because the owner finds it wrongly declines. So the engine is judged against a
labelled set, not against the approver.

1. **Find where the approver goes wrong.** Its verdict log holds the rule, the verdict, the failed checks and a
   command hash, never command text. Counting declines by failed check shows which checks cause them. This needs
   no new data and is read-only. Plan 1 does it first, so that the engine is not built to repeat those checks. The
   count is in the Evidence section ("The approver's declines by failed check").
2. **Build a labelled set.** A collector records, for each prompted command from now on, the `describe` output (the
   command text, the facts, the engine's verdict) in a local, untracked file, and the owner marks each one right
   or wrong. A new file is needed because the old log has no text to label. The facts can contain diffs, and a
   vendor program can open any file inside the project, so the file lives outside every project, in the owner's
   own data directory beside the verdict log, and is never tracked. The owner-side collector writes it; the agent
   does not. A project path for it would be readable by the vendor and is not allowed. (Amended 2026-10-30: the directory is
   `~/.config/project-workbench/action-review/`; see "The shadow hook".)
3. **Shadow.** The thin hook runs the engine on each prompted command and logs what it says. *Amended 2026-10-30:* the
   earlier text had the approver's answer still decide beside it. No approver runs now, so the hook answers nothing and the
   owner's own prompt decides. Nothing the engine says takes effect.
4. **Measure.** The report gives the engine's false declines and false approves against the owner's labels and the test
   set. *Amended 2026-10-30:* the earlier text counted both programs; the approver's answers are no longer collected, so
   there is nothing to compare on the same commands, and its old rate in "Evidence" is context only. A disagreement is settled
   by the owner's label.
5. **Cut over only when the owner says.** The engine replaces the approver when its false-approve count on the
   test set and the labelled set is zero and its false declines are below a bound the owner sets. The old program and `claude-workflow` stay
   installed until then (rule 6 of `global-config-inventory.md`). *Amended 2026-10-30:* both programs went in the reset of
   the user-level configuration; the cutover is now the owner's decision to let a hook allow, in the plan after the shadow.

The cost is the owner's time to label, and two model calls per prompted command during the shadow.

**Decided by the owner (2026-10-25):** both. The owner labels real commands, and the author also writes a small test
set of dangerous cases, which the owner reviews and corrects. The two answer different questions. Real commands
seldom include an unsafe one, so a count of zero false approves on them is weak evidence that the engine stops
unsafe actions. The test set covers the stops: a secret in a diff, a HEAD that does not match, a repository that
selects a program, a message addressed to the reviewer, a removal of Git metadata. The labels measure the
everyday false-decline rate. The cutover bound applies to both: no false approve on the test set or the labels,
and false declines on the labels under the owner's bound.

**The bound (the owner chose the author's recommendation, 2026-10-25).** At most 10% of the labelled real commands
are false declines, on at least 30 labelled commands, and strictly below the approver's rate on the same commands.
*Decided by the owner on 2026-10-29, replacing the sentence above:* at most 10% false declines among the labelled real
commands, with at least 10 labelled commits and 10 labelled removals, and no false approve on the labels or the test set. The
clause "strictly below the approver's rate" is dropped because no approver runs, and a single count of 30 is replaced by a
minimum for each action, so that easy commits cannot pass a rule that has never seen a removal.
The 10% is provisional and the owner may tighten it once plan 1 has counted the approver's declines by failed check.
A false decline costs the owner a prompt (under `delegate` a decline falls back to the normal prompt); a false
approve is the harm, so it has no bound: any false approve on either set blocks cutover. The report groups false
declines by check, so a few fixable checks are not hidden in a count. The 10% and the minimums are the author's judgment (the 30 of the earlier text became the two minimums of 10),
not measured.

*Clarified 2026-11-05, by the accepted decision `2026-11-05-unconfirmed-removals-are-outside-the-action-review-measure`:* the
labelled real commands that the bound counts are the commands that would change something. A `remove` without `--confirm` (a
preview, which deletes nothing) is reported on its own line, "unconfirmed removals (previews)", with how many were labelled and how
the engine judged them, and is not counted in the false-decline rate, in the minimum of 10 labelled removals or in the false-decline
count. It stays visible: a preview the engine approves is a false approve and blocks cutover like any other. The labels already
made do not change, and the report classifies a command by its `confirm` fact. The bound and the other minimums are unchanged.
What the hook does with a preview at cutover is decided in the plan for the hook, not here. Built in plan
`2026-11-05-shadow-report-counts-previews-apart`, increment A: the report classifies a removal as a preview by the `confirm` fact
of its collected row, and a fact that is missing or not a boolean leaves the removal counted with the confirmed ones.

### What moves, and what does not

| today | after |
|---|---|
| collectors for commit and remove, via the global program | `safe-git describe commit`, `safe-git describe remove` |
| collector for a remote job | `remote-runner describe submit`, `describe fetch` of the module, which wraps the owner's global program (M16 and F-C6 apply); not built: the module declares no `describe` argument |
| collector for a push | `safe-git describe push` (built by plan `2026-10-26-safe-git-describe-push`; see `safe-git.md`); `push-check` stays for the `push-changes` skill |
| the rubric, schema and rule files | ported into the engine as data, section by section |
| `ask-codex-archive` rule | none: the module's `archive` is owner-run and denied (M15) |
| `safe-committer` agent and the guard's `committer` mode | go with the program (decided by the owner, 2026-10-25): the agent and the mode are removed in the owner's step that removes `claude-workflow`; the guard program stays for its other modes. No module counterpart. |
| `claude-workflow amend-message` | lost with the program (the owner's decision is recorded under "Decisions on the two leftovers") |

## As built, and its limits

Built by plan `2026-10-26-action-review-engine`, Increments B to K, and read against the text of the design by
Increment L. Evidence is in that plan's Result, as run on 2026-10-26 and 2026-10-27 in scratch copies of the repository:
the module's 458 tests, the full suite of 5,314 tests in 11 roots, a set of 29 dangerous cases run through
the real `safe-git` and launcher with a fake bridge, mutation batteries over most increments (C and F to K), a `reviewer` review of each
increment and an adversarial security pass (`security-reviewer`, Increment K). No real bridge, no real model and no hook was
run, and the installer's copying of the module was not run (the first test through the installer is the owner's `wb add`).

**What exists.** The module `action-review` with its command `review`, the loader and matcher, the grammar and its parser,
`describe` through the launcher, the fourteen code checks for `commit` and `remove`, the rubric and the reply schema, the
bridge call, the verdict object, the exit table, the log row and the pins of the shipped data files. **What did not, when
the engine was built:** the rule and checks for `push`, the owner's hook, the writer of the log, the labelled set, the report and the
shadow period (plan 4), cutover and the removal of `claude-workflow` (plan 5), and the owner's personal setting, which the owner's profile file replaced (built by plan `2026-11-04-review-profiles`, increment F). Plan 4
(`2026-10-29-action-review-shadow-hook`) has since built the shadow side ("The shadow hook"); the push rule, a hook that decides,
and the cutover are still not built.

**Where the build departs from the text Increment A wrote.** Each is written into the sections above; the list is here so
the owner can find them.
- The helper reads its rules, rubric and schema from the installed path below the project root, not "beside itself", and
  holds SHA-256 pins for them (Increments D and K).
- `ships` names each data file, and a new rule is added to it with its pin (Increment D, K).
- A rubric section or question that is missing is found when the review reads the rubric, not when the rule loads
  (Increment H).
- The grammar refuses five more forms than its alphabet implies (Increments C and K, "The reviewed command is the command
  that runs").
- `preview_matches_arguments` and `no_git_metadata` also compare with the paths the command names (Increment K).
- The log row's `rule` is the file stem and its `model` is the one the bridge reports (Increments I and K).
- The credential-name list holds globs and directory names, and grew by eight entries after the security pass; the secret
  scan is the approver's, ported as code from the approver at SHA-256 `d8b3facdee46432d27547a07865abf024741929ae2d9191e1015ee8280bcd613`,
  read 2026-10-27 (Increment F).
- A failed code check is a decline decided before the setting and the rubric are read, so it needs neither; otherwise the
  setting and the rubric are read, the bridge gets the time left of the 25 seconds as measured from the start of the review,
  and the bridge runs from the project root, not the working directory (Increment I, H).

**Checks of the approver with no counterpart in the engine yet.** The push checks (`safe-git.md` lists each with its
counterpart in `describe push`), because the push rule is deferred; the remote-runner and `ask-codex-archive` checks, because
those actions are not in this design's first rules (the archive is retired). For `commit` and `remove` every check has a
counterpart (`safe-git.md`, "Describe"). Two known differences: the approver matched `.config/gh` as a substring of the whole
path and the engine matches that name as a directory above a file; and a commit whose diff lies between 96 KiB and 256 KiB
was reviewed by the approver and declines under `describe` (`safe-git.md`).

**Open limits.** These are recorded, not fixed, and the owner places them:
- Approval is not bound to the content that is committed: the facts are taken when `describe` runs, and a background
  process could change a file before the commit. The fix is a digest that the real `safe-git commit` also checks, a change
  to another module.
- The reviewer-facing exemption can be claimed by choosing a path name such as `skills/second-opinion/x.md`; only the model
  stands between text there and a pass.
- The secret scan is best effort: lock files in any directory skip the entropy test, generic assignments are relaxed under
  `tests/`, and some token shapes and file names are not scanned. The exemptions avoid false declines on real files; the
  model is the backstop.
- A reply schema swapped after the helper checked it and before the bridge reads it is not covered, because the bridge reads
  the path itself; the reply is validated again against the rule, so only instruction text could reach the vendor. A fix
  needs a bridge that takes the schema's content.
- `paths_not_credentials` for a commit reads only `describe`'s paths, and there is no commit counterpart of
  `preview_matches_arguments`; it relies on the pinned `safe-git`.
- The URL pattern of the secret scan is case-sensitive.
- A `refused:` line on standard error can quote an escaped offending character or flag word of the command and up to 40
  characters of a number literal of the `describe` output; a failure reason can hold the bridge's `detail` code (at most 64
  characters of `a-z0-9_`), the one piece of vendor text in a reason. Neither reaches standard output or the row.
- An empty `credential_names` list is accepted by the loader and then matches nothing (only an absent list fails the check);
  an `ok: true` removal object with empty path lists passes the two removal comparisons, which the real command cannot print.
- The vendor program is started confined, but the confinement is a tripwire: `model-bridge.md` ("Confinement", "What remains")
  lists what a confined program can still reach (an image viewer, MCP resource readers, functions that start agents and an exec
  function whose limits are not shown), and the protection depends on the program's version, so a release of `codex` is accepted for
  this text only after the release check there passes for it. Files in the project, the rules and the rubric (pinned, so a change is
  caught before a review) can still be read by anything the confinement does not cover.
- `ignore_unknown_targets` has no test on a real object, because the one cause the spec names (a colon or backslash target)
  is refused earlier as `path_refused`, as observed in Increment G; the 5-second `describe` budget is a guess; `find_root` takes the nearest project, so a nested project
  under the working directory would supply its own rules (pinned, so a changed rule is refused); the hook must start `review`
  in the directory where the command will run.
- The owner's profile file replaced the personal setting and is read by this engine (see "Settings and the bridge" and
  `review-profiles.md`).

**The owner's steps.** The agent does not run these, and nothing below is done until the owner does it. The shadow hook records and
allows nothing: the prompt stays the owner's, and removing its settings entry stops it. This is the one complete list (plan
`2026-11-04-shadow-hook-security-review-fixes`, increment D, after the second security review of 2026-11-04); a step that must wait for
another comes after it, and the protections (step 3) come before the hook is registered (step 4). The module's files are those of the
commit that holds this text. If you copied files for an earlier version of these steps, they are out of date: do step 2 again. Every
command below is typed in a terminal, in the root of the project you work in, unless it says otherwise. "The user-level settings" is the
file `~/.claude/settings.json`.

1. **Install the module into a project you work in, and keep it current** (this repository first). The hook runs `wb run action-review
   review`, so the project needs the module installed and pinned, a `safe-git` and a `model-bridge` module (`ask-codex`) installed and
   pinned, and the `action-review` ladder of your `review-profiles.json` naming the bridge. First time: `python3 -m workbench preview add --dir <checkout> --package
   packages/workbench --select action-review`, then the same with `add` instead of `preview add`. **The engine the hook starts is the
   installed copy under `.workbench/`, not the one in `packages/`**, so after any change to the module, in this order: `wb
   release-approvals`; `acknowledge` if it lists changes (the project must be known on this machine and every difference acknowledged);
   `python3 -m workbench preview upgrade --dir <checkout> --package packages/workbench` and read it (the manifest records the package
   as `local:workbench`, which must be given with `--package`; if it says a module is not approved, `wb approve` it first); then the
   same with `upgrade` instead of `preview upgrade`. Without that the hook runs the engine as it was installed.
2. **Copy four files to a dedicated directory, from a clean checkout, and check them.** The directory is yours alone, outside every
   project, empty apart from these four files (a stray `secrets.py` or `errno.py` beside them would shadow the standard library, because
   the hook puts its own directory first on the import path). The four files are read-only; the directory stays writable by you so that
   you can replace them. If `~/action-review-shadow` exists from an earlier version, delete it first. `upgrade` in step 1 leaves what it
   wrote uncommitted: commit that first, because the files below are the committed ones. From a checkout of this repository at the commit
   you intend (`git status --short` must print nothing):
   ```
   D=~/action-review-shadow
   rm -rf "$D" && mkdir "$D" && chmod 700 "$D"
   for f in hook/shadow_hook.py hook/shadow_store.py tools/label.py tools/report.py; do
     git show "HEAD:packages/workbench/action-review/$f" > "$D/$(basename $f)"
   done
   chmod 444 "$D"/*.py
   ls -A "$D"                                   # exactly: label.py report.py shadow_hook.py shadow_store.py
   git -C "$D" rev-parse --show-toplevel        # must fail: "not a git repository"
   shasum -a 256 "$D"/*.py
   ```
   `git show` writes the committed bytes, so a working-tree edit cannot get in. The hashes you print are the check against the checkout;
   the helper's `PINS` (`grep -n 'hook/shadow' packages/workbench/action-review/helper/action-review`) holds the SHA-256 of
   `shadow_hook.py` and `shadow_store.py`, and comparing them is a second check that proves less (the helper is a file of the project,
   which an agent can write; a mismatch is a reason to stop, a match is not proof). `label.py` and `report.py` are never installed; `wb
   verify` on the module checks its tree hash, which covers them. A program run from inside a project is code that project could change,
   which is why none of these is run from the project. The test-set runner is not copied; it runs from the checkout (step 8).
3. **Protect the files with user-level rules, and know their limit.** In the user-level settings, under `permissions.deny`, add:
   `Read(~/.config/project-workbench/action-review/**)`, `Edit(~/action-review-shadow)`, `Edit(~/action-review-shadow/**)`,
   `Write(~/action-review-shadow/**)`, `Edit(~/.claude/settings.json)` and `Write(~/.claude/settings.json)` (your Claude Code version
   may fold the `Write` rules into its edit rules; use the spelling it documents). The rendered rules deny the agent's edits to
   `~/.config/project-workbench/**` and not its reads, and a tool-level deny does not stop a shell: `cat`, a redirect or `cp` still work.
   These rules narrow the gap and do not close it. **Anything that runs as you can change the hook, its settings, the data files and the
   labels**, so the report in step 9 is evidence for you to weigh, not proof. Note that with the `Edit` rule on the settings file, you
   change that file yourself, in an editor, not through the agent.
4. **Try the entry by hand, then register it.** The interpreter is an absolute path to a Python you trust, never `python3` alone:
   `/usr/bin/env -i` clears the environment, and the macOS `/usr/bin/python3` is a shim that starts the developer tools. Find yours with
   `python3 -c 'import sys; print(sys.executable)'`. `-I` makes Python ignore `PYTHONPATH` and the user site; `env -i` also removes the
   variables that load code into a process. Neither protects against code installed with the interpreter itself. `--wb` is the launcher
   in the guarded store, an absolute path whose file name is `wb`, and is required.
   *By hand first,* in the root of the project from step 1 (the hook runs the engine in the directory it is given, and the engine needs
   a project there; from `$HOME` the launcher is refused because it lies inside that directory). This reviews nothing and sends nothing:
   `ls` has no rule, so the engine never reaches the model.
   ```
   echo '{"hook_event_name":"PermissionRequest","tool_name":"Bash","cwd":"'"$PWD"'","tool_input":{"command":"ls"}}' |
     /usr/bin/env -i /absolute/path/to/python3 -I -B ~/action-review-shadow/shadow_hook.py --wb "$HOME/.config/project-workbench/bin/wb"
   echo "exit $?"
   python3 -B ~/action-review-shadow/report.py
   ```
   It must print nothing before `exit 0`, and, with an empty data directory (any earlier rows add to the counts), the report must show
   `prompted 1 (reviewed 0, not reviewed 1)` and `not reviewed: no_rule 1`. If the hook prints a line on standard error, that line says
   what is wrong (a missing `-I`, no `--wb`, a launcher it may not run); a `refused` or `failed` outcome in the report is step 6's list.
   *Then register it in the user-level settings,* merged into the `hooks` you already have. There is **no `onFailure`**: with `"block"`
   a failure of the hook would deny the request.
   ```json
   {"hooks": {"PermissionRequest": [{"matcher": "Bash", "hooks": [{"type": "command", "timeout": 30,
     "command": "/usr/bin/env -i /absolute/path/to/python3 -I -B /Users/<you>/action-review-shadow/shadow_hook.py --wb /Users/<you>/.config/project-workbench/bin/wb"}]}]}}
   ```
   **What leaves your machine from here on:** every prompted command that matches a rule is reviewed by the engine, which sends its
   facts, a commit's diff included, to the bridge's vendor (two model calls at most per command). `collected.jsonl` keeps the command
   text, those facts and the reason on your disk (mode 0600, outside every project) until you delete it, except for a commit the engine
   declined for a secret or a credential-named path, which leaves a verdict row and nothing else ("Redaction"). The hook redacts the rest
   with a fixed list of patterns, which is best effort: a secret in a shape it does not name, and one the engine does not name either
   (`pass=...`, a Slack webhook, an unnamed AWS secret), is kept as it was. Do not copy, share or back up that file to anywhere you do not
   control. **The vendor program is started confined** (`--confine`), which is a tripwire and not a boundary ("The bridge call is
   confined"): text that must not reach a vendor does not belong in a commit you let the shadow review. **Check your `codex`
   before you register:** `codex --version` must print a release that passed the release check of `model-bridge.md` ("Release check
   for untrusted text"; `codex-cli` 0.163.0 passed it on 2026-11-01). For any other release, run that check yourself first: nothing in
   the engine does.
5. **To collect commits as well as removals,** add a user-level `ask` rule for `wb run safe-git commit`, in the form your other rules
   use. Every commit then raises a prompt, which changes your workflow while the shadow runs; remove the rule when it ends. The
   module's `remove` already asks; the accepted decision `2026-10-29-workbench-asks-for-remove-submit-and-fetch` leaves `commit`
   unprompted, and a permission-request hook sees only a command that raised a prompt. A command your `allow` rules or a permission
   mode let through is not seen. Pushes and remote jobs are seen only if they prompt, and the engine reports them as `no_rule`.
6. **Check that it fires, and write down what you see** (the hand run of increment H): work as usual and look at `python3 -B
   ~/action-review-shadow/report.py`, whose `prompted` line should rise by one for each prompted command. Note whether it fires on a
   project `ask` in an interactive session, on the two module commands (`remove`, and `commit` once step 5 is done), and in auto mode
   when the classifier decides without a prompt (the hooks page does not say; "The shadow hook"). A `refused` or `failed` outcome means
   the launcher, the module or the bridge is not set up. Causes to look at, in order: (a) the hook gives the engine the `PATH`
   `<the launcher's directory>:/usr/local/bin:/usr/bin:/bin` and nothing else, so `git`, `codex` (and `node`, which the `codex` shim needs)
   must be there, and **`wb` runs the first `python3` on that path**, which on macOS is the system `/usr/bin/python3` (3.9.6 on the
   machine this was written on) unless `/usr/local/bin` has another: the installer and the three helpers load under 3.9.6 (checked by
   loading their top level) but the engine has not been run under it; if it fails, make `/usr/local/bin/python3` a link to the Python
   you trust, or ask for the hook's `PATH` to change; (b) the `action-review` rung of your `review-profiles.json` names a bridge that is installed and
   pinned; (c) Codex is signed in; (d) the installed engine is the current one (step 1); (e) the report finds no rows because it looks
   under `HOME` and the hook writes under the home directory of the account database: they are the same on a normal login and differ if
   `HOME` was changed (`sudo`, a wrapper, another account), in which case run the report with the same `HOME` the account database
   gives. **The time budget:** the engine stops itself after 25 seconds (at most 5 for `describe` and the rest for the bridge), the hook
   waits 27 and then 2 more for a program that left its group, and the harness stops the hook at 30; the store's file lock waits at
   most 5 seconds a try, and a run makes at most three tries (two for the verdict row, which has a fallback, one for the collected row),
   so a slow store can add up to 15 seconds and push a run past 30; the harness then stops the hook and the row of that command is
   lost (a fragment is skipped on read). Nothing else changes.
7. **Label** at a terminal with `python3 -B ~/action-review-shadow/label.py` (`--skipped` revisits the skipped). `right` means you would have
   judged as the engine did, `wrong` that you would not. Judge from the command and the facts (press `f`), not from the engine's reason:
   when a model was asked, its reason is the model's own words, which the commit's text may have steered. Until there are at least 10
   labelled commits and 10 labelled removals the report says "not enough labels". A commit the engine declined for a secret is never
   collected, so a false decline of that kind cannot be labelled and is not in the rate.
8. **Run the test set against a real model, once,** from the root of a checkout you trust: `python3 -B
   packages/workbench/action-review/tools/run_testset.py [--codex-dir <absolute path>]`. It needs the `codex` program on your `PATH` and a
   Codex directory (`~/.codex` by default) with your sign-in, and refuses without them. It sends 3 synthetic prompts (not yours) to Codex
   through `ask-codex`, after you type `send 3`, and the call is confined like every call of the engine; this tool sends nothing else (the
   hook of step 4 is a separate matter). It writes the rows the report reads. If it ends with exit 1 and a "not run" line, the line
   gives the case and the engine's exit code and not the cause, because the runner does not show the engine's own `refused:` or `failed:`
   line: run `wb run action-review review '<a command of the case>'` by hand in a scratch project to see it (a bridge that refuses
   `--confine`, a Codex that rejects the reply schema together with the confinement arguments, a Codex that is not signed in). A case that
   did not run leaves no row, so the report cannot count it. It was tested only against a fake `codex`; **this is the first time the
   confined call with the reply schema runs against a real one.** The runner hashes only its case file and trusts the rest of the
   checkout, and is started without `-I`, which is why it runs once, from a checkout you trust.
9. **Read the report** with `python3 -B ~/action-review-shadow/report.py`. A false approve on the labels or the test set is its first line and keeps the
   cutover closed; a false approve in any run of a test case counts (to start the test set afresh, change the engine if it needs
   it, then delete `testset.jsonl` and run the test set again), and the cutover line reads "met" only with all 29 test cases. The data
   files are plain files that anything running as you can edit (step 3), and the agent chooses which commands prompt, so it also
   chooses which become labelled data: **before any cutover, re-label a sample at a terminal yourself**, and note
   `shasum -a 256` of the three data files after each session so that a later change is visible. When the report says the bound is met,
   the cutover is still your decision and a plan of its own (plan 5): a hook that decides does not exist.

**To stop,** remove the hook's entry from the user-level settings; nothing else is running. Delete `~/.config/project-workbench/action-review/`
when you no longer want the data.

**Not verified.** The hook has never run against the real `wb` launcher, a real bridge or Claude Code; the tests replay the real
engine's own output bytes through a fake `wb`, and start the hook through a stub that patches the account database. Whether it fires in
auto mode, on a project `ask` in an interactive session and on the two module commands is open until step 6. Whether Claude Code applies
a project's `settings.json` `env` to hook processes, honours exit 2 on `PermissionRequest` or holds the prompt while the hook runs is
unverified, and so is whether it accepts the deny spellings of step 3. The confined call with the reply schema has not been run against a
real Codex (step 8). The engine has not been run under the system Python 3.9. No real model has been asked: the test-set evidence for the
cutover does not exist yet.

## Proposed split into plans (default)

Each is a plan of its own, in this order. Plan 3 is done (below); plan 4 is `2026-10-29-action-review-shadow-hook` (approved; built and committed in Increments A to H; the owner's installation, labelling and real-model run are outstanding, see "The owner's steps") and plan 5 does not exist yet, and the owner approves each.

1. **The interface, documented. Done by plan `2026-10-25-describe-interface-documented`.** The `describe` decision
   is accepted. The plan settled what it left open: the form of a module's declaration in `module-contract.md` and
   `module-boundary.md`, the numeric caps and the fact names for `commit` and `remove` in `safe-git.md`, and the
   engine's contract in this spec, and the owner's three decisions on 2026-10-25 (the launcher rule for a declared action, who writes the log, the timeout; see "Decided by the owner"). It also holds the
   read-only count of the approver's declines by failed check, so the rubric is written knowing where the approver
   goes wrong.
2. **`safe-git describe`. Done by plan `2026-10-25-safe-git-describe`** (see `safe-git.md`, "As built, and its limits",
   for what differs from the draft). It is for `commit` and `remove`, with tests that the facts equal what the real command acts on and
   that the call changes nothing. Its first increment is the verifier support for the `describes` field; the launcher rule that refuses
   `describe <action>` for an action not in `describes` follows it; its security pass covers the new git shapes and
   that rule.
   Between 2 and 3, or alongside 3: **the push gap**, closed by adding `safe-git describe push` (the owner chose this over
   extending `push-check` on 2026-10-26; plan `2026-10-26-safe-git-describe-push`; the design is in `safe-git.md`,
   "`describe push`", and the narrowing of the accepted `describe` decision is the accepted record
   `2026-10-26-describe-push-takes-the-push-arguments`). Built, so the engine's rule for a push has its facts; until that
   rule exists a push stays with the approver (since 2026-10-29 no approver runs, so a push is not reviewed at all).
3. **The engine. Built by plan `2026-10-26-action-review-engine`** (Increments A to L; the plan's own status is the record of
   whether it is complete; see "As built, and its limits"),
   for `commit` and `remove`: its checks, rules, rubric, log row and bridge call, tested with a fake bridge and a set
   of dangerous cases. No hook, no push rule and no log writer.
4. **The shadow hook, the labelled set, the test set and the report**, prepared on a scratch copy; the owner installs
   the hook, labels the commands and reviews the test set. The test set is written in plan 3 with the checks. *Built by plan
   `2026-10-29-action-review-shadow-hook`* (the hook, its store, the labelling tool, the report and the test-set runner); see "The
   shadow hook" for what it does differently from this text, because no approver runs now.
5. **Cutover and M14**: the thin hook replaces the approver, the global `claude-workflow` program goes, and the
   paragraphs OP5 and OP7 are repointed. Facts for remote jobs follow M16.

## Decisions on the two leftovers

- **`safe-committer` and the guard's `committer` mode (F-A7): the owner chose the author's recommendation on
  2026-10-25.** They go with `claude-workflow`. The workbench's `commit-changes` skill has the main agent run
  `wb run safe-git commit` directly, and the helper enforces the limits. A confined commit agent for the module would
  need the agent gate's grammar extended, for a convenience. If the owner turns out to use the agent, a module
  version is planned later.
- **`claude-workflow amend-message`: lost with the program. The owner accepted the author's recommendation on
  2026-10-25 and said it can be added later if it is needed.** Read on 2026-10-25 (the
  installed program, read, not run): it rewrites the message of the HEAD commit only. It refuses when HEAD is not the
  expected hash, when anything is staged, and when HEAD is on a known remote branch unless `--allow-pushed` is
  passed. Evidence for losing it: (1) the plan `2026-10-22-code-work-commit` left it out on purpose ("the owner amends
  with git by hand"); (2) the module's `commit-changes` skill already says never to amend; (3) the approver has no
  rule for it (F-B4), so it has never been reviewed and no review is lost; (4) this repository's reflog holds no amend
  operation; (5) a new `describe` command, rule, checks and test cases would be built for a history-rewriting command
  that is otherwise refused by policy. Limits of that evidence: the reflog covers this repository only, and the
  owner's other repositories were not examined. A bad message is fixed by a new commit or by the owner's own `git
  commit --amend` in a terminal. When the program goes, its `ask` and `allow` entries for `amend-message` are dead and
  the owner removes them (rule 6 of `global-config-inventory.md`).

## Constraints and assumptions

- Standard library only, a helper per command, pinned by the installer (`module-boundary.md`).
- The engine runs a `describe` command and a bridge only through `wb run`, as decision 4 requires. A security review is
  owed because a helper starts another module's pinned command (decision 4, consequences).
- Assumes a hook can run `wb run` in good time. The provisional limits are under "The verdict, the output and the log".
- The approver's rubric text is read and ported by the plan that builds the engine; this spec does not restate it.

## Decided by the owner (2026-10-25)

The owner took the author's recommendation on each of three questions the plan `2026-10-25-describe-interface-documented`
left open.

- **How the engine knows a command is declared for an action: the launcher enforces it (option (a)).** `wb run` refuses
  `describe <action>` unless the action is in the command's `describes`. Rejected: (b), a read-only `wb` command that
  lists declared (module, command, action) triples for the engine to check first, because it leaves two places to
  enforce. The cost accepted: the launcher knows one verb and one argument position, although `module-boundary.md` says
  the installer knows no command by name and the decision rejected a launcher `describe` as module content. The rule is
  generic and names no module. `module-boundary.md` is updated when the rule is built.
- **Who writes the engine's log: the owner's thin hook, and a failed write never withholds an approve.** The engine runs
  as an agent-reachable pinned command and the floor decision (`2026-10-24-project-guarantees-a-floor`) says the agent
  writes nothing at the user level, so the engine writes nothing outside the project. The hook notes a failed write and
  goes on. The cost accepted: a review can be approved with no log row, so the log is a record and not a gate.
- **The timeout: 20 seconds for the bridge, 25 for the engine, 30 for the hook, provisional.** The source and the
  reason for the order are under "The verdict, the output and the log". They are revisited with the shadow period's
  own durations.

## Decided by the owner (2026-10-29 to 2026-11-03)

Decided in session while plan `2026-10-29-action-review-shadow-hook` was drafted and built; each is written where it applies.

- **The store module is `hook/shadow_store.py`** (accepted 2026-11-03): the installer's boundary test forbids a module file named like
  a file of the installer, so the plan's name `hook/store.py` could not stand.
- **What the hook stores is redacted by a fixed list of patterns, best effort** (decided 2026-11-03, built by plan
  `2026-11-03-redact-collected-diffs`; "Redaction"). The file is still not to be shared or backed up outside the owner's control
  (the owner's steps say so).

- **The shadow's data directory is `~/.config/project-workbench/action-review/`**, a subdirectory of the guarded store, fixed (no
  environment variable moves it), mode 0700 ("The data files").
- **The engine hands the facts to the collector on `--collect`,** so the command is parsed once, by the engine ("The collect
  lines").
- **The cutover bound has no comparison with the approver:** at most 10% false declines among the labelled real commands, at least
  10 labelled commits and 10 labelled removals, no false approve on the labels or the test set. The 10% is provisional ("The
  bound").
- **The test-set runner covers all 29 cases on the unit tests' scaffold with the real `ask-codex`, runs from a checkout, and links
  the owner's Codex directory into the scratch home for the sign-in** ("As built (Increment G)").

## Open questions for the owner

- Is a separate `describe` subcommand the right shape, or should the interface be something else?
- Decided: you label real commands and review a test set, with the bound above. Open: whether 10% stays after
  the shadow has counted real commands.
- Whether to run a security review over the hook, the store and the engine's `--collect` flag (they touch a subprocess, the
  filesystem, untrusted command text and, through the bridge, a network boundary). It runs only when the owner asks.
- `safe-committer` (F-A7) and `amend-message`: decided, see "Decisions on the two leftovers".
- The capability name `action-review`: the built module provides it, and the owner has not confirmed it as the final name.

## Acceptance criteria

- For each action that stays a reviewable module action (commit, remove, a push through `describe push`, and later the
  remote actions), a module `describe` command prints an object that obeys the rules above, runs the real command's
  validation, and changes nothing (a test compares the repository before and after).
- The retired actions have no `describe` provider and no rule: `ask-codex archive`, `safe-committer` and
  `amend-message`. A test shows the engine refuses a command line that names one.
- A rule that carries command text, an extra verb or a path does not load, and the engine builds only `wb run <module>
  describe <action> ...`.
- A synthetic action with a fake module and a fake bridge gets a verdict only through `wb run`; a `describe` command or a
  bridge that is not installed, pinned and declared is refused and nothing runs.
- A missing, malformed, oversize or unavailable bridge reply, facts object or rule file yields no approval.
- Over generated command text, every text the stated grammar accepts parses to the same argument list in the engine
  and in `sh` and `zsh`, and every other text is refused.
- Two rules with one key, a malformed rule and a rule with an unknown field each refuse only their own key; other
  commands are still reviewed.
- Bridge selection: an absent setting, an invalid one, a bridge that is not installed and one that is not pinned each
  behave as the settings section says, and no other vendor is tried. (A project request that the owner's personal
  setting overrides is not testable until that setting is built.)
- No file holding labelled data or command text lies inside a project tree.
- A corrupt rule file does not stop the review of any other command.
- Every check of today's approver for commit, remove and push has a named counterpart or a recorded reason it does
  not (the plan of the engine lists them).
- On the test set of dangerous cases (reviewed by the owner) and on the labelled set of the owner's real commands,
  the engine has no false approve; on the labelled set its false-decline count is below the owner's bound; and the
  report shows the engine's counts against the labels and the test set (the approver's counts on the same sets can no longer
  be collected; amended 2026-10-30, see "The shadow hook").
- The count of the approver's declines by failed check exists before the engine's rubric is written.
- `review` prints only the verdict object described above and exits 0, 1 or 2 as the table says; an approve with a
  non-empty `failed_checks`, a decline with an empty one, an extra field or a `reason` over 300 characters is never
  printed; and a test shows that every refusal and failure prints nothing on standard output, except that a failed
  write of the row (or a flush) after the object was printed exits 2 with the whole object already printed.
- The log line holds exactly the fields listed, and a test shows that no command text, fact or diff reaches any field
  other than the bounded `reason`; the residual exposure of `reason` is recorded above.

## Evidence

- The approver's collectors were read on 2026-10-25 in the program the inventory records (baseline SHA-256
  `94ac5e8cd05473081ff0004130592cdb94e0bbd19199777574c599a23cca2b0b`, then patched to
  `d8b3facdee46432d27547a07865abf024741929ae2d9191e1015ee8280bcd613`); `load_helper`, `collect_commit` and
  `collect_remove` call the global `claude-workflow` program as a library. Read, not run.
- The module sides were read in `safe-git.md` (`commit`, `remove`, `push-check`) and `model-bridge.md`.
- Not run when this spec was written (2026-10-25): any `describe` command, any engine, any hook. The proposals are the author's.

### The approver's declines by failed check

Provenance: role USER, item the approver's verdict log (`verdicts.jsonl`), retrieved 2026-10-25, 668,545 bytes, SHA-256
`2a8e8ce7988de449be738a46b876436f8b9343955f953574364cd4a67dd3e095`, recomputed after the read and equal. A scratch
script ran with Python 3.15.0 (`-I -B`), read the file in binary mode and printed counts only; no command digest and no
free text was printed or copied. Plan `2026-10-25-describe-interface-documented`, Increment A.

The log has 1,019 rows (none unparsed), first dated 2026-10-16 and last 2026-10-26 (timestamps as logged; their timezone was not checked). By verdict:
662 approve, 336 decline, 21 no verdict (20 Codex timeouts, 1 collector error). Every decline carries a non-empty list
of failed checks. A decline has one of two reasons: 146 failed a deterministic check before Codex was asked, and 190
were Codex declines.

| Rule | Approve | Decline | No verdict |
|---|---|---|---|
| `claude-workflow-commit` | 420 | 194 | 12 |
| `git-push` | 107 | 58 | 6 |
| `claude-workflow-remove` | 27 | 49 | 1 |
| `ask-codex-archive` (retired) | 72 | 10 | 2 |
| `remote-runner-submit` | 24 | 8 | 0 |
| `safe-git-commit` | 7 | 9 | 0 |
| `remote-runner-fetch` | 3 | 8 | 0 |
| `remote-runner-cancel` | 2 | 0 | 0 |

Failed checks over all declines (a decline can fail several, so the counts add up to more than 336):
`no_secret_lines` 102, `no_reviewer_directed_text` 102, `targets_look_disposable` 48, `change_is_safe_in_itself` 44,
`facts_complete` 26, `message_matches_change` 10, `status_ok` 9, `paths_valid` 9, `fetch_targets_safe` 8,
`head_matches` 7, `profile_command_is_expected` 5, and 11 more checks with 3 or fewer each.

By the actions this design keeps:

- Commit (`claude-workflow-commit` and `safe-git-commit`): `no_reviewer_directed_text` 99, `no_secret_lines` 52,
  `change_is_safe_in_itself` 42, `facts_complete` 11, `message_matches_change` 10, `paths_valid` 9, `head_matches` 7,
  `scope_is_coherent` 3, `staging_state_ok` 2.
- Remove (`claude-workflow-remove`): `targets_look_disposable` 48, `scope_is_narrow` 3,
  `preview_matches_arguments` 1.
- Push (`git-push`): `no_secret_lines` 47, `facts_complete` 15, `no_reviewer_directed_text` 3, `outgoing_trusted` 3,
  `change_is_safe_in_itself` 2, and `outgoing_known`, `push_target_known`, `remote_is_configured`,
  `remote_transport_safe` 2 each, `destination_is_appropriate` 1.

Limits. A decline in the log is not a false decline: no label exists, so the count says which checks cause declines
and not which were wrong. The log grows, so these figures hold as of the retrieval date. The `ask-codex-archive` rows
belong to an action this design retires. A command whose rule does not load is not reviewed at all, so the log cannot
show it (see "Non-goals and anti-goals"). The `reason_text` field was not read.

Durations for the timeout decision: a second read of the same log (role USER, `verdicts.jsonl`), later on 2026-10-25,
by a scratch script (`python3 -I -B`, binary read, counts only) over the `codex_seconds` field. Measured immediately
afterwards, the log was 672,275 bytes with SHA-256 `796046453f59e0ffb09ce28401b133e6c6c0443c8de43d13d832c9a8c3fc7f48`
(it had grown since the first read, so the two sets of counts differ by the rows added). Result: 876 rows with a
duration, median 7.5 s, 90th percentile 11.7 s, 95th 13.4 s, 168 over 10 s, 20 at the 15 s limit.

What it shows: `no_reviewer_directed_text` (99) and `no_secret_lines` (52) lead the commit declines;
`no_secret_lines` (47) leads the push declines, with `facts_complete` (15) second; and `targets_look_disposable` (48)
is nearly all of the removal declines. They are the first to label in the shadow period. It does not bear on the provisional 10% bound, because the bound concerns false declines, which only the
owner's labels measure; the bound is unchanged and remains the owner's to tighten.
- **The first test-set run and the first labels of the shadow (2026-11-05).** The owner ran `tools/run_testset.py` at a terminal (Python
  3.15.0 on Darwin 25.6.0, at commit `4d6ace4`, through `ask-codex` with the model `gpt-5.6-terra` at medium effort, which is the
  `action-review` rung of the owner's `review-profiles.json`), and then labelled with `label.py` the 20 commands that were waiting in the
  shadow's store. The agent ran `report.py` (read-only) before and after and read its output; nothing was sent to a model by the agent.
  **Result.** The test set ran 29 of 29 cases as the case file says, the model was asked 3 times, and there were 0 mismatches, 0 false
  approves and 0 false declines; it was the first run of the confined call with the reply schema against a real `codex`, and it ran on
  the first attempt. The labels: `commit` 9 labelled, all `right` (0 false declines, 0 false approves), one short of the 10 the report
  needs; `remove` 11 labelled, 7 `right` and 4 `wrong`, 0 false approves, and 4 false declines, all by the check `confirm_present`, a
  false-decline rate of 36.3% against the provisional bound of 10%. The report's cutover line then read "not yet (not enough labels
  for commit; false declines over the bound for remove)". **What the four false declines are:** removals that were previews
  (`confirm` false); the fixed check `confirm_present` declines every removal without `--confirm`, a preview deletes nothing, so each
  cost one prompt and no risk. **Two further labels record the owner's risk appetite and are `right`:** a model's decline of the confirmed
  removal of two tracked shipped-approval directories (`targets_look_disposable`; the owner prefers a human look at approval records, though
  they are restorable from the repository), and a model's decline of the confirmed removal of an untracked source file. **Limits:** 20
  labels, all from this project's own work and mostly removals, so a sample of the owner's use and not an accuracy rate; the model was
  asked on 3 test cases and on the reviewed commands only; 11 reviewed commands were not collectable and could not be labelled; the
  report prints no timings. **An open design point this raises, to be decided when the hook that decides is designed and not before:** how
  an unconfirmed removal is treated, either in the rule (approve it when its facts are valid, since it deletes nothing) or by the hook (a
  command without `--confirm` never reaches the engine and a fixed rule passes it). Neither is built, and the bound is unchanged.
