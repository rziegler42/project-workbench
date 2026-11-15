# todo list

Status: Draft. **Approved by the owner on 2026-11-11 as a design.** It is built in part by the plan `2026-11-11-todo-list`: the command `todo` with `add`, `list`, `show` and `drop`, the `todo` capability and the policy block (increments A to D, "As built" below). The plan-close clause of `code-work` and the first use are not yet done. It stays `Draft` until they are, and becomes `Current` then. Reviewed by the review engine in two rounds (seven findings, all applied).

Written on 2026-11-11 from a conversation with the owner. Each statement carries one of three marks, so that the owner can see what is theirs:

- **[agreed]** The owner said it. It is the working position and it can still change.
- **[call]** The assistant's choice, made so the design is complete. The owner has not decided it.
- **[open]** Not decided. The builder asks the owner, or the owner decides when approving.

Terms are defined in `terms.md`. The module that would carry this is `groundwork` (`groundwork.md`); the places a module may write are in `repository-boundary.md` and `module-contract.md`.

## Scope

A personal list of things the owner wants to remember to do or fix in the current clone: deferred items, cleanups, bugs noticed and not fixed, missed close-outs, and larger work to come back to. [agreed]

The list serves two moments. The owner is not focused on the current task and wants to park a thing without losing it. The owner has a little time or energy left and asks what to do next, and wants to look at the small leftovers without searching every plan, spec and roadmap. [agreed]

It is a reference, not a schedule. Regular work is scheduled by plans and roadmaps, not by this list. [agreed]

It is part of `groundwork` and is usable on its own, with no process module. [agreed that it belongs to `groundwork`; the placement of the capture clause in `code-work` is a call, below]

## Non-goals

- A task queue, an order of work, a priority, a due date or an estimate that anyone relies on. [agreed]
- A second roadmap. A thing that needs direction, with an outcome, a boundary and a trigger, is a roadmap candidate. [agreed]
- A "done" state. An item that is implemented, or no longer wanted, is dropped. [agreed]
- A shared or tracked list, and any copy between clones. The list is this clone's; a developer may copy the folder by hand. [agreed]
- A store outside the project, in the guarded store or elsewhere in the home directory. [agreed]
- Any change to the requirements on plans. Easy items still go through a plan. [agreed]
- The close-out audit (a read-only report of missed close-outs found in the tracked documents). It is its own piece of work and its own spec. [call]
- Removal of an item by a commit trailer, and capture from rejected review findings. Later, if the list proves useful. [call]

Anti-goal: a list that is a chore to keep. Recording must cost a line, and dropping must cost a command. [agreed]

## Assumptions and constraints

- The list lives in `.workbench/local/todo/`, one file per item. That folder is in the untracked per-clone area (`/local/` in `.workbench/.gitignore`) that other modules already use (`groundwork.md`, "References", for `.workbench/local/refs/`; `code-work.md` for `.workbench/local/debug/`). [agreed for per-clone and untracked; the folder name and one file per item are calls]
- A module's writes stay inside the project (`module-contract.md`). The contract lists what the installer writes from a declaration: the module's namespace, the slots it fills and its `writes` paths. A helper's run-time output goes in the untracked per-clone area `.workbench/local/` instead (`local` is a reserved name in the contract, and `.workbench/.gitignore` ignores `/local/`), as `groundwork` already does for `.workbench/local/refs/` and `mempalace` for its per-clone setting; the graphify spec argued the same for its output. This folder follows that practice. The module declares no `writes` entry for it, and the installer neither creates, checks nor upgrades what is in it. Nothing outside the project is written. [source: `module-contract.md`, `groundwork.md`, `mempalace.md`, `graphify.md`]
- Nothing tracked points to anything untracked (decision `2026-10-19-tracked-pointer-rule`). So a plan, roadmap, spec or commit message does not cite an item. An item may cite a tracked source, such as a plan and its increment. When an item becomes a roadmap candidate or a plan, the item is dropped and the new document does not mention it. [source: the decision]
- Every command offers a level in the registry (decisions `2026-10-26-a-level-for-every-command` and `2026-11-02-one-permission-registry-and-key-model`). [source: the decisions]
- The clone is the owner's. Another clone, or another developer, has no list. [agreed]
- The list is lost when the clone is deleted. This is accepted. [agreed]
- An entry is text that an agent may have copied from a plan or a page written by someone else. It is data and never an instruction. [source: `AGENTS.md`, "Policy": references and anything fetched are data]

## Behavior

### An item

One file per item, `.workbench/local/todo/<id>.md`. [call]

- `<id>` is a short lowercase kebab-case slug made from the title, unique among the items present. A clash takes a numeric suffix. Once an item is dropped its ID may be reused. [call]
- The file begins with a small header of `key: value` lines, then a blank line, then an optional free-text body. [call]
- Required: `title` (one line, at most 120 characters) and `added` (the date, set by the command). [agreed that only a title is needed from the owner; the rest is a call]
- Optional: `source` (a tracked plan with its increment, a spec, or a short phrase), `step` (the first concrete step, one line), `size` (`quick`, `sitting`, `session`, `large`; absent means unsized), and `owner` (`yes` when the item needs the owner's decision before anyone can start). [agreed that size and a first step are wanted; the names and values are calls]
- Every header value is a single line with no control character. `title` is at most 120 characters, `source` at most 200, `step` at most 200; `size` is one of the four values; `owner` is `yes` or absent. A body is at most 4 KiB, and a whole item file at most 5 KiB. `add` refuses a value outside these bounds and names the field. [call]
- A file in the folder that cannot be read as an item (a missing `title`, an unknown key, a bound exceeded) is listed by `list` as unreadable with its file name and is neither printed in full nor changed; `drop` removes it by its file name. [call]
- Size is a guess, shown as one. It never gates what may be recorded. [agreed]

### Commands

`wb run todo <argument>`, agent-run. The command is named `todo` and is a command entry of `groundwork` beside its decision command `groundwork`, so that each of the four arguments has its own key and level (`command-permissions.md`). [call; it replaces the first form of this spec, `wb run groundwork todo <subcommand>`, by the plan `2026-11-11-todo-list`, which the owner approved]

| argument | does | level |
|---|---|---|
| `add --title T [--source S] [--step S] [--size Z] [--owner] [--body B]` | writes one item and prints its ID | `none` [agreed as the owner's leaning] |
| `list [--size Z] [--mechanical] [--older-than DAYS]` | prints the items, oldest first, each with its age, size, title and ID | `none` [call] |
| `show <id>` | prints one item in full | `none` [call] |
| `drop <id>` | removes the item's file, prints the item's full text and ID, and appends one line (date, ID, title) to a drop log | `none`, agent-run [agreed that `drop` is agent-run; the level is a call] |

- `add` needs only a title. [agreed]
- `add` refuses an exact repeat of a present item's title, and for a near match prints the IDs it resembles and still adds. [call]
- `list` shows every item unless a filter is given. `--size quick` and `--mechanical` (items not marked `owner`) are the filters for a short stretch of time or a tired day. The default view is the whole list. [agreed that small and easy items can be found without losing the rest; the flags are calls]
- `drop` has no recycle step, no confirmation and no done state. [agreed] Because the items are untracked, git keeps no record of a dropped one. So `drop` prints the item in full, which the agent keeps in its reply, and appends one line (date, ID, title) to a drop log beside the list; a mistaken drop is then recoverable by adding the item again from that text. The log is not a done state and no command reads it back in the first stage. [call]
- **How the levels fit the registry.** All four are agent-run arguments and offer `block` and `none`, with the default `none`; the owner may set `block` in their table (`command-permissions.md`, "The levels an owner-run argument of a module's command offers" for the other kind). The registry offers `ask` only to an owner-run argument, so `drop` has no `ask` as an agent-run argument. [agreed that `drop` is agent-run and `add` is `none`; the rest is a call]
- **`delegated` is a later stage.** An agent-run argument that its command describes to the action-review engine offers `block`, `delegated` and `none`, and that is the route to the owner's wish for delegated support: `drop` and `add` would each need a `describe` and a rule in the engine, which has one only for `commit` so far. `delegated` for `add` would be stricter than the `none` it already has, so it is of use only if the owner later wants adds reviewed. The first stage declares nothing for it and must not make it harder. [agreed that delegated support is wanted; the staging is a call]
- The instruction that an agent drops only an item it has implemented, or one the owner tells it to drop, is advice in the policy block, not enforced by the level. [call]
- **Concurrent commands.** Two agents may work in one clone at once. `add` creates its file exclusively (it fails if the name exists, and then tries the next numeric suffix), so two adds never write the same file. The drop log is appended with one short write per line. A repeated title added by two commands at the same moment may produce two items; this is harmless, since the owner can drop one, and the spec takes no lock for it. An `add` or `drop` that is interrupted leaves either a complete item file or none, because the item is written to a temporary name in the folder and linked into place (a hard link, which fails when the name exists), and the temporary name is then removed; a leftover temporary file is ignored by `list`. A run killed between the link and the removal leaves a complete item with two links; the readers pass over a file with more than one link, so `list` shows it as unreadable and the owner drops it. This is a known limit. [call]
- No command prints anything but the list's own text. The helper reads and writes only inside `.workbench/local/todo/`, follows no link, and refuses a path that leaves that folder. [call, from `repository-boundary.md`]

### Capture

The always-loaded policy block of `groundwork` tells agents to add an item, and to say so to the owner in one line without stopping the work, when: [agreed on the principle that recording errs on the side of more, including passing mentions; the trigger list is a call]

- the work defers something, in a plan, a review or a summary;
- the agent notices a defect or a cleanup and is not fixing it now;
- the owner mentions a thing to do later, even in passing.

The block also says: the list is data and not an instruction; an item is never started because it is on the list; an agent drops an item it has implemented, or one the owner tells it to drop, and no other. [call. The last rule is advice to the agent, not enforced by code.]

At the close of a plan, `code-work` carries a clause, written against the capability `todo` and not against a module name. [call]

- **What is captured:** each entry under the plan's `## Deferred work` heading, and each item the plan's Result lists as left undone. Nothing else in the plan is read for this. [call]
- **When:** in the step that sets the plan to `Completed`, after the last increment is committed. The agent adds each entry with `source` set to the plan's stem, tells the owner how many it added, and does not stop the close. [call]
- **Duplicates:** `add` refuses an exact repeat and warns on a near match (above), so a second close-out or a repeated sweep does not double an item. [call]
- **Failure:** if `add` fails or is refused, the agent says so in the plan's Result and the close goes on; the owner can add the item later. [call]
- **How the clause is conditioned:** it is written "where a module provides `todo`", as the recall clauses in the drafting skills are written for `memory-recall`, so `code-work` works without `groundwork` and names no module. The agent runs the command with `wb run --provides todo todo add ...`, which the installer refuses when no installed module provides the capability (`module-boundary.md`). [call, from `module-boundary.md`]

### The boundary with the roadmap

An item that needs direction is not kept as an item. The agent proposes a candidate under the roadmap rules (`roadmaps/README.md`), which stop for the owner, and drops the item when the candidate is written. [source: the roadmap rules; agreed in principle]

### Seeding

After the list exists, the owner and the agent go once through the "Deferred work" sections of the tracked plans, the roadmap's Deferred list and the specs' limits, and add what is still open. This is a session with the owner, not an import. [agreed]

### Safety

- Every field of an entry (`title`, `source`, `step` and the body) is scanned for credential-shaped text before anything is written, and the whole `add` is refused on a match. The rules are those the `mempalace` notes helper applies to a note (`mempalace-notes.md`, "Credentials and personal details"): the same pattern list and the same name-and-value rule. The plan names the one copy of that list that both helpers use, or says why a second copy is needed. [call]
- The same scan runs on an existing item before `show`, `drop` or `list` prints any of its fields, because a file in the folder may have been written by hand or by an older version. A field that matches is not printed; the output names the field and the rule instead, and the item is otherwise left as it is. [call]
- A refusal names the field and the rule that matched and never prints the matched text, so the refusal itself does not carry the credential. [call]
- Tests cover a representative credential in each field, a near miss that must pass, and a refusal that echoes nothing. [call]
- The text of an entry is never run, expanded or interpreted. [call]
- The module is subject to the security review the project policy offers for a new write and a parser. The owner decides whether it runs. [source: `AGENTS.md`, "Policy"]

### As built

Read from the helper `packages/workbench/groundwork/helper/todo` and its tests at the commit of increment D of the plan `2026-11-11-todo-list`. Where this section gives a number the sections above did not, the helper's constant is the source.

- **The item.** The header keys are `title`, `added`, `source`, `step`, `size` and `owner`, each at most once, as `key: value`; the file holds a blank line after the header and then the body. `add` writes them in that order. A header value is one line of printable characters with no space at either end. The bounds are those above: title 120, source 200, step 200, body 4096 bytes, item 5120 bytes (`MAX_TITLE`, `MAX_SOURCE`, `MAX_STEP`, `MAX_BODY`, `MAX_ITEM`). The list holds at most 1000 items (`MAX_ITEMS`); `add` refuses beyond that, and `list` reads at most the first 1000 file names and says how many more it did not read.
- **The ID.** The title in ASCII letters and digits in lower case, every other run one `-`, at most 60 characters; `item` when none is left; a clash takes `-2`, `-3` and so on, up to 99. A repeated title (compared with case and spacing ignored) is refused; a title of three or more words of three letters or more whose words in common with another item's (also three or more) are at least 60 percent of all the words of both titles is added, and `add` prints `similar: <id>` for up to three such items.
- **What a command reads.** A file is read only if it is a regular file with one link, opened without following a link, of at most 5120 bytes. A file that is not read as an item (a missing or repeated key, an unknown key, a bound exceeded, bytes that are not UTF-8, a link, a directory, a file with two links, or an ID that does not print safely) is listed by `list` as `unreadable: <file name>`, whatever the filter, after the items, and it is never printed. A file name that does not print safely (not ASCII, or credential-shaped) is shown as `(a file whose name is not shown)`. Only names ending in `.md` and not starting with `.` are items.
- **`list`.** One line for each item, oldest first (then by ID): the age (`<n>d`), the size or `-`, the title and `[<id>]`, then `(owner)` for an item that needs the owner. `--size Z` keeps items of that size, `--mechanical` leaves out items marked `owner`, and `--older-than DAYS` keeps items whose age is more than DAYS (a whole number up to six digits); the filters combine. A list with no item and no unreadable file prints `the list is empty`, whatever the filter, and a filter that matches none of the items prints `no item matches` when no unreadable file is listed; unreadable files are listed after the items in every case. At most 200 item lines and 200 unreadable lines are printed, with a count of the rest. `list` and `show` make nothing: with no folder the list is empty.
- **`show <id>`.** `id:`, then `title`, `added` (with the age in days), the optional fields that are present, and the body after a blank line. An ID that holds `/`, a NUL, a leading dot or a character that does not print safely, a missing item and an unreadable file are each refused, and a refusal prints no file content.
- **`drop <id>`.** The argument is an ID, or the file name of an unreadable file with its `.md`. It removes the one named file, prints `dropped: <id>` and the item as `show` prints it (an unreadable file is named and its text is not printed), and appends one line to the drop log. A directory is refused. A link is removed and its target is not touched. A file with two links loses that name only.
- **The drop log.** `dropped.log` in the list's folder (its name is reserved: an item file ends in `.md`, so no ID can name it, and no command reads it back or lists it). One line for each drop: the date, the ID (or `(name not shown)`) and the title (or `(not an item)`), separated by tabs, with a credential-shaped title replaced by the note that names the field and the rule. The file is made with mode 0600 and opened for appending without following a link; a link, a file that is not plain or has two links refuses the drop and keeps the item. Its size bound is 262144 bytes (`MAX_LOG`, about 1,500 drops): a drop that would pass it is refused with "trim it by hand", so no item is removed without a record. The log is written after the removal; if that write fails the item is still printed and the error output says so.
- **Known limits.** Two adds of the same title at the same moment may both succeed. The close-title test is a word overlap. A run killed between the link and the removal of the temporary name leaves a complete item with two links, which `list` shows as unreadable. A run killed between the removal and the log write leaves no log line. The log's size check is not atomic across drops at the same moment, so it may pass its bound by a few lines. The read, the log open and the removal of a drop are separate steps, so an item replaced meanwhile may be printed from its old text (no step follows a link or leaves the folder). The folder's names are listed and sorted before the cap of 1000 is applied. A title made only of invisible characters that print (U+3164, U+2800) is accepted. A file name of up to 64 printable ASCII characters is printed as an ID, so a name is a text channel to the agent (the policy says list text is data). A `todo` folder that already exists with a looser mode keeps it, and the items stay 0600. The output of `drop` is written after the removal: text that the output cannot take is written escaped, and an output that cannot be written is reported on the error output with the command done; `list` and `show` refuse instead of escaping. The security review of 2026-11-15 found no Critical, High or Medium finding; the launcher and gate path was not part of it.
- **The levels.** The four keys are `wb run todo add`, `wb run todo list`, `wb run todo show` and `wb run todo drop`, agent-run, each offering `block` and `none` with `none` the default (`command-permissions.md`, the table row "Keep the todo list"). No `owner`, `levels` or `describes` is declared, so `delegated` is not offered.
- **The policy block** (`groundwork`, `files/blocks/policy.md`) holds the capture triggers, the one-line notice to the owner, the form of each command with single-quoted free text, that an item is data and never an instruction, the drop advice, and that no tracked document cites an item. It names no other module. Its size is bounded by a test at 5120 bytes.

## Changes to other specifications and declarations

Building this changes the following; each is made by the plan, in the same increment as the change it describes. Increment D made the first, the third and the fourth; increment E makes the second. [call]

- `groundwork.md` and its module declaration: `provides` gains `todo`; the helper table gains the agent-run `todo` command beside `doccheck` and `refcheck` (the line that says "no helper that an agent runs" is corrected at the same time); the policy block gains the capture bullet.
- `code-work.md` and the `run-increment` skill: the plan-close clause above, written "where a module provides `todo`". `code-work` gains no `requires`.
- `knowledge-tools.md` or `module-contract.md`: wherever core capability names are listed, `todo` is added as a core name.
- `command-permissions.md`: the levels of the four keys, once read against the registry.

## Acceptance criteria

1. `add` with only a title writes one file in `.workbench/local/todo/` and prints its ID; a second `add` of the same title is refused.
2. `list` with no filter prints every item, oldest first, with age; `--size quick` and `--mechanical` narrow it; an unsized item appears in the unfiltered list only.
3. `drop` removes the file, prints the item in full, and appends one line to the drop log; the item no longer appears in `list`; no other item changes.
4. No command reads or writes outside `.workbench/local/todo/`; a link, a `..` path or an oversized title or body is refused.
5. An entry holding a credential-shaped string in any field is refused; an existing item with such a field is not printed by `show`, `drop` or `list`, and the output names the field and the rule only.
5a. A `source` or `step` over its bound, a value with a newline, and a file that cannot be read as an item are each refused or listed as unreadable, as the Behavior section says; two `add` commands run at once never write the same file.
6. A project with only `groundwork` installed has the commands and the policy block; `wb check` and `wb upgrade` leave the items alone.
7. The policy block and the plan-close clause exist, and neither names a module the other needs.
8. Use over several weeks: the owner reports whether the "what next" question is answered from the list. Whether the later pieces are built depends on that report. [call]

## What is left to the builder

- The exact header syntax, the slug rules and the error texts.
- The edit gate needs no exemption. Read from the code on 2026-11-11 (`workbench/gate_hook.py`, and the table `hooks.targets` in `packages/workbench/claude/module.json`): the gate judges only the file-writing tools `Edit`, `MultiEdit`, `NotebookEdit` and `Write`, and it refuses a target inside the project only while a plan under way is not approved, with no exception for `.workbench/local/`. `add` and `drop` run as a Bash command (`wb run todo ...`), and the helper writes the file itself, so the edit gate does not see them; the command gate governs those calls by their level. A direct `Write` of an item file would be gated during an unapproved plan, which is acceptable because the helper is the route. This was read from the code and not seen in a live session, so the plan's last increment includes one hand run of `add` while a plan under way is unapproved. [evidence note: code read at commit `07003c7`, conclusion above]
- Whether the log is read by any later command (none does in the first stage; its name and size bound are under "As built").
- Whether `show` is worth keeping beside `list`.
- The wording of the policy block and the plan-close clause, within the limits above.

## Governing decisions and references

- Decisions: `2026-10-19-tracked-pointer-rule`, `2026-10-26-a-level-for-every-command`, `2026-11-02-one-permission-registry-and-key-model`.
- Specs: `groundwork.md`, `module-contract.md`, `repository-boundary.md`, `code-work.md`, `command-permissions.md`.
- References: none.
