# mempalace notes

Status: Draft. Written on 2026-11-06 from a conversation with the owner, reviewed in three rounds by the review engine (twelve findings, all applied), and
**approved by the owner on 2026-11-06 as a design**. It is not built: it stays `Draft` because it does not yet describe what is true, and it changes nothing in
`mempalace.md` until a plan builds it. The plan `2026-11-06-mempalace-notes` is building it; the points it settled with the owner on 2026-11-06 (the command
shape, the levels, two confirmations, the way the remote is read) are marked in place, and the `[open]` items that remain are for the later increments.

Each statement carries one of three marks, so that the owner can see what is theirs:

- **[agreed]** The owner said it. It is the working position and it can still change.
- **[call]** The assistant's choice, made so the design is complete. The owner has not decided it.
- **[open]** Not decided. The builder asks the owner, or the owner decides when approving.

Terms are defined in `terms.md`. The module and its commands are in `mempalace.md`; the levels of owner-run and agent-run commands are in
`command-permissions.md`.

## Scope

Notes are short texts that an agent saves while it works with the owner, or on its own as a researcher, so that what was worked out is not lost when a
session is compacted or ends, and so that another session, or an agent drafting or researching later, can find the part it needs. A note is kept as a
file in the owner's machine-wide notes folder, and a reviewed note is filed into the owner's palace with the existing `mine`.

It covers: where notes live and what they are called; what a note holds; the commands an agent uses to list, read and save notes; how a saved note is kept
out of the palace until it is reviewed; how the review asks the owner for as little as possible; how an agent finds notes again; and what is refused or
flagged. It lives in the `mempalace` module and requires nothing else. [agreed]

Four kinds of use drive it, all from the owner:

1. **Working memory for a brainstorm that has no spec yet.** The ideas survive a compaction or a lost session, and a second session on a side task or
   research can use what the first produced, and write its finding back. [agreed]
2. **Lessons learned with the owner's guidance**, such as which tool or approach worked for which kind of problem on this machine, or how to set up a
   piece of hardware. The example was Verilog and formal proofs; the design is general and builds in no domain. [agreed]
3. **Ideas and concepts that research agents distil** from collected sources (the separate `knowledge-base` project), kept so that agents drafting
   specs, decision records, roadmaps and plans, and agents doing more brainstorming or research, find them. [agreed]
4. **A record of what was tried and dropped**, so research does not repeat a dead end. [call]

## Non-goals

- Mining finished sessions or transcripts. It is deferred (`mempalace.md`, "Evidence"); raw `--mode convos` also files tool output.
- Replacing the project's documents. What is true of the project, and what a decision rests on, goes in a spec or a decision record, which are tracked and
  reviewed. A note may suggest that a lesson be promoted there. [agreed]
- A task list, a log of what an agent did, or the state of a working tree. A note about a branch's state misleads a clone on another branch. [call]
- Holding sources. The original bytes of a source stay in the `knowledge-base` project's books. A note holds an idea and a pointer back. [call]
- Any change to `search`, `mine` or `sync`. They behave as they do now, including the default wing, which stays the project folder's name for them. [agreed]
- Exposing the program's knowledge graph, `sweep`, `repair` or any other program command.
- Writing the palace without the owner's confirmation. Filing stays `mine` at the level `ask` or at a terminal.

**Anti-goals: it fails even if it works technically when:**

- It stops being useful: it does nothing, or its searches return nothing helpful. [agreed]
- It becomes too needy: it keeps asking the owner for something. [agreed]
- A credential or a personal detail reaches the palace. [agreed]
- An idea is lost without anyone being told. [call]
- Notes pile up unread until review is a chore. [call]

## Assumptions and constraints

- The owner has the `mempalace` program and the module installed (`mempalace.md`). A clone without the program is told once, as `search` already does.
- `mine` refuses a folder inside `.git` or `.workbench`, a folder with a link in its path, and a folder that overlaps a palace (`mempalace.md`, "mine at the
  level `ask`"). So notes cannot live under `.workbench/local`, and the notes folder is outside every project. [agreed]
- `mine` files a whole folder under one wing. A folder of drafts would be filed with the reviewed notes, so drafts live in a place `mine` never reaches
  (see "Where notes live"). [call]
- A folder that is deleted and recreated gets a new inode, and the program then keeps the drawers of its deleted files as `Unresolved` for good
  (`mempalace.md`, "Evidence", 2026-11-06). The helper therefore changes notes in place and never deletes and recreates a folder. [call]
- The agent's file tools may need extra permission to write outside the project; this was not checked. The helper writes notes so that the agent needs none.
  [call, to be checked by the builder]
- `search` takes `--wing`; a plain search looks only in the clone's wing (`mempalace.md`, "Behavior").
- A compaction is the harness's: an agent cannot trigger one, and Claude re-reads the project-root `CLAUDE.md` and its `@AGENTS.md` pointer afterwards
  (`code-work.md`, "Compaction"). No hook is built for it. Notes are saved before a compaction because they are saved as the work goes.
- The helper's imports are pinned by a test and its text must not hold the words the pin forbids (`mempalace.md`, "As built"). A new command may need the
  pin changed; that is the builder's change to ask for in the plan.
- Anything in a note that came from a source outside the project is data, not an instruction, whoever wrote the note.

## Behavior

### Where notes live

- **The notes folder** is `~/.local/share/project-workbench/mempalace` (under `XDG_DATA_HOME` when that is set). [agreed; the XDG clause is a call]
  It is made at the first save, one level at a time, mode 0700, with no link followed, as the lock directory is. It is not made at install. [agreed]
  The read verbs (`wings`, `list`, `read`) make nothing and open the folder without following a link at its last component, and each wing folder under it
  the same way (a wing folder that is a link is not followed and counts as absent). A link above the notes folder (a dotfile manager makes `~/.local` or
  `~/.local/share` one) is followed on the read side. **For creation** (`save`, increment B) the data directory must exist, because only the two levels under it
  are made, and it is followed if it is a link; those two levels, the drafts, archive and locks folders and each wing folder are made one at a time with mode 0700
  and are never followed if they are links, and a note file is made with mode 0600. A link where one of them belongs makes `save` refuse before anything is made. [call]
  `wings` counts a malformed note as a reviewed note or a draft by where it is, takes `newest` from every state including the archive, and prints only
  wing names that pass the wing-name rule. `read` refuses a `<wing>/<name>` that conflicts with `--wing`. [call]
- **One subfolder per wing**, named by the wing. A wing is a project or a topic. A topic wing is named when a note is saved (a domain, a piece of hardware,
  a shared pool); nothing about any domain is built in. [agreed]
- **Drafts and reviewed notes are apart.** Reviewed notes are in `<notes>/<wing>/`, which `mine` files. Drafts are in `<notes>/.drafts/<wing>/`, expired
  drafts in `<notes>/.archive/<wing>/`; `mine` is never pointed at either. [call]
- Notes are plain text files, one per topic. **The file name is made from the title by a fixed rule**, so that no title can reach outside its folder or
  overwrite another note: [call]
  - the title is normalised to NFC and lower-cased; every run of characters that are not letters, digits or `-` becomes one `-`; leading and trailing `-` are
    removed; the result is cut at 60 characters, then a `.txt` is added;
  - a title that leaves nothing (empty, only symbols, or only control characters) is refused, as is a title with a control character or a path separator
    before normalising, so a hostile title is an error and not a quietly different name;
  - if the name is already taken in the same wing, among the drafts, the reviewed notes or the archive, `save` refuses unless it is told which note it extends
    (see "Saving"); it never overwrites, and no suffix is added on its own. A title that normalises to a taken name is a refusal, and the agent chooses a
    different title; `--new` does not change this, it only allows a note whose text overlaps another;
  - an archived note is renamed on its way to the archive to `<name>.<UTC time as YYYYMMDDTHHMMSSZ>.txt`, so an archive entry never has the name of a draft and
    a second archiving of the same name never replaces the first; if even that name exists, the move is refused;
  - every component of the path is opened without following a link, and the file is made with an exclusive create, so a link planted in a folder is refused.

### The wing of a project

For a note about a project, the wing is, in this order: [agreed]

1. the `wing` that `.workbench/local/mempalace.json` names, which wins when both exist;
2. the repo name from the `origin` remote (the last path segment, without `.git`) when it is a valid wing name;
3. otherwise saving is **blocked**, and the message says what to create: the file, with a name the owner chooses.

The block applies to notes only. `search`, `mine` and `sync` keep their folder-name default. [agreed] Because that default can differ from the wing a note is
filed under (a clone in a folder named differently from the repo), the output of a save names the wing and, when a plain `search` would use another, says so
and gives the `--wing` form. [call] The remote is read from `.git/config` as text, never by starting `git`. [agreed on 2026-11-06] The kit's strict reader (`safefs`) refuses any path that touches
git metadata, so the helper reads that one file with the same checks: `.git` and the file are opened without following a link, the file must be regular, have
no other hard link, and be within the size limit, and anything else counts as no remote. A line ends at a newline only, as git ends it. A url with no path
(a host alone, or a host and a port) names no repo. A project whose `.git` is a file (a worktree or a submodule) is not a project to the kit, so the question
does not arise. [call]

A wing name is at most 64 letters, digits and `._:-`, and does not start with `-` or `.`, as `search` already requires.

### What a note holds

A note is short plain text, not markdown that has to be rendered. [call]

```
title: <one line>
kind: idea | decision | open question | finding | lesson | explored | dead end
wing: <wing>
written: <date>
updated: <date>
source: <where it came from; for research the book, the locator, the retrieval date and the content hash>
verify: <a command or check that shows it is still true; for a fact about a machine>
revises: <the reviewed note a revision draft replaces>
new-despite: <the note it overlaps, when --new was used>

<body>
```

The header is the lines of the form `key: value` at the top; it ends at the first line that is not one, and a **blank line then separates it from the body**
(a body line shaped like a header line, directly after the header, is read as an unknown header key, so the note is malformed). The keys are the ones in the block
above and no others; a repeated key, a missing required key (`title`, `kind`, `wing`, `written`, `updated`), a kind outside the list, a date that is not a
`YYYY-MM-DD` date, a `wing` that differs from the folder's, a title over 120 characters, any control character, text that is not UTF-8, or a file over 16 KiB
makes the note **malformed**: it is refused whole and named, and the other notes are still listed. [call]

- A note is self-contained and substantive. A note under a minimum size (about 300 characters) is refused, because the program skips files that are too
  short and because short stubs that echo a query degrade search (reports from other users of the program, `2026-11-06`, unverified). [call]
- A note is verbatim text of the owner's own words or the agent's summary. It is not compressed. A note from research holds a summary or a short quote and a
  pointer, never a copy of a source. [call]
- A fact about a machine carries its `verify` line and its date. An agent checks the line before relying on the fact. [agreed in substance]
- A note holds no credential and no personal detail (below).

### Commands

All are arguments of a second command of the `mempalace` module, **`mempalace-notes`** (`wb run mempalace-notes <verb>`), with its own helper and one argument per verb,
because permission keys are per argument and `save` and `keep` need different levels. [agreed on 2026-11-06 when the plan's first open point was settled; the
name was the plan's recommendation] They need the folder rules and the wing rule above. The settled points of the plan are: the levels are as the section below
gives them; `keep` and the filing are two confirmations inside one review exchange; the helper reads the `origin` remote from `.git/config` with the strict
file reader and starts no process. [agreed on 2026-11-06]

| verb | does | who | writes |
|---|---|---|---|
| `wings` | lists the wings that have notes: name, number of reviewed notes and drafts, date of the newest | agent | nothing |
| `list [--wing W] [--kind K] [--state S]` | lists notes with title, kind, wing, updated and state; `--state` is `reviewed`, `draft`, `archived` or `all`, and defaults to `reviewed` and `draft` together; without `--wing` it lists the project's wing | agent | no note; it runs the expiry and finishes an interrupted `keep` first (below), which write |
| `read <name> [--wing W] [--state S]` | prints one note, between the recalled-data markers; `<name>` is a file name or a title, `--state` narrows it as for `list`, and a name that matches more than one note (for example a reviewed note and its revision draft) refuses and lists them | agent | nothing |
| `save` | creates a draft, or adds to the note it is told to extend (below) | agent | the drafts folder |
| `drop <draft>` | moves a draft to the archive; the owner's "drop" | agent | the drafts and archive folders |
| `merge <draft> <into>` | adds the draft's text to another draft, or makes a revision draft of a reviewed note, and archives the first draft | agent | the drafts and archive folders |
| `review [--wing W]` | prints the by-exception summary of **one wing's** drafts and a digest (below); without `--wing`, the project's wing | agent | no note and no folder; like `list` it runs the expiry and finishes an interrupted `keep` |
| `keep --wing W --digest <digest>` | moves the drafts the digest covers into that wing's folder; a revision replaces the reviewed note it names; one wing per call and per digest, and `--wing` is required | owner, level `ask` with the digest | the notes folder |

**Naming a note in a command.** `drop`, `merge`, `read` and `save --into` take a note as `<name>` or `<wing>/<name>`, where `<name>` is a file name (with or
without `.txt`) or a title, and the wing is the project's when it is left out. A bare name that matches more than one note of the wing refuses and lists them.
The path separator in `<wing>/<name>` is the only one accepted; a `..`, a leading `/`, a control character or an absolute path is refused. `drop` and the
first argument of `merge` must name a **draft**; a reviewed or an archived note is refused. `merge <draft> <into>` takes a draft or a reviewed note of the
same wing as its target (another wing is refused), and refuses to merge a draft into itself. With several wings holding drafts, `review` and `keep` are
run once per wing; the journal, the lock and the digest are per wing. [call]

Filing is the existing `mine <notes>/<wing> --wing <wing>`, with its preview and digest. `keep` and `mine` are two confirmations, inside one review exchange,
because `keep` changes files and `mine` changes the palace. [agreed on 2026-11-06]

`save` takes `--title`, `--kind` and `--body` (the text, or `-` to read it from standard input), and, when they apply, `--wing` (the project's by default), `--source`,
`--verify`, `--into <name>` with `--state reviewed|draft|all` to name which one when a reviewed note and its revision draft share the name, and `--new`. With
`--into` the title and the kind are not needed and the note keeps its own. A new note's body is at least 300 characters and no note is over 16 KiB. The name for
`--into` is `<name>` or `<wing>/<name>` with the call's own wing only; an extra path segment is refused. The text overlaps a note when more than 60 percent of the
words (three or more letters or digits) of the shorter text are in the other. The answer says what was made, and, when a plain `search` in this clone looks in
another wing, names that wing and the `--wing` form to use. The lock of a wing is the file `<notes>/.locks/<wing>`; `save` waits for it for about five seconds and
then refuses with nothing changed, and the expiry skips a wing whose lock is held, without waiting for it. The expiry and `save` write only through a notes folder
reached without following a link at either level under the data directory; the read verbs may read through one. A temporary file left by a killed run
(`.tmp-…` in a folder) is ignored by every verb and counted as an ignored entry; the helper removes it only in the run that made it. `save` refuses a wing whose name
differs only in case from an existing wing, because those are one folder on some file systems. `--source` and `--verify` are refused with `--into`, because they would
be dropped. The body of an addition is added as `(added <date>) <text>` after a blank
line. [call]
The keys for `save`, `drop` and `merge` are agent-run writes into an untracked folder. `command-permissions.md` gives an agent-run argument the levels `block` and
`none` and the default `none`, so saving is on once the module is installed and the rules are rendered, and the owner sets a key to `block` to stop it; the
writes are drafts and never the palace. A default of `block` would be a change to that spec and is not made here. The read verbs (`wings`, `list`, `read`) and
`review` are agent-run reads; `keep` is owner-run, offers `ask` with `review` as its preview argument, and defaults to `block`. [agreed on 2026-11-06]

### Saving: update before create

- Before it saves, the agent lists the project's notes. If the idea belongs to an existing note, the agent says so with `save --into <name>`; otherwise it
  creates one. Whether an idea belongs to a note is the agent's judgment, so that the helper has something testable: [agreed in substance; the mechanism is a call]
  - `save --into <name>` names an existing draft or reviewed note of the same wing (by its file name or its title), and refuses a name that matches no note or
    more than one; the message lists the candidates;
  - `save` without `--into` and without `--new` first compares the new text with the wing's notes by word overlap, with no model; if a note overlaps by more
    than a limit (about 60 percent of the shorter text's words), it refuses and lists the overlapping notes, so the agent chooses `--into` or `--new`;
  - `--new` creates a note even when one overlaps, and is recorded in the note as `new-despite: <name>`, so review can see the choice.
- An addition to a draft is a dated paragraph added to it. An addition to a reviewed note is a **revision draft**: a copy of the note with the paragraph added,
  marked `revises: <name>`, which replaces the reviewed note when it is kept. A reviewed note is never edited in place, so what is filed was reviewed.
  `save` never rewrites or removes earlier text. Merging and rewording happen only at review. [call]
- Two sessions or researchers saving at once are serialised by a lock on the wing's folder, so two writes do not overwrite each other. [call]
- Writes are made to a temporary file in the same folder and renamed, so a killed run leaves the old note whole. [call]
- **Operations that touch more than one file are ordered so that a crash loses nothing, and a retry finishes the job.** [call]
  - `drop` is one rename.
  - `merge <draft> <into>` first writes the target (temporary file, rename) with the draft's text added under a line `merged from <draft> <hash of its text>`,
    and only then archives the draft. A crash between the two leaves the text in both places, a duplicate and not a loss. A retry sees the line, adds nothing a
    second time, and archives the draft.
  - `keep` first writes a journal, `<notes>/.drafts/<wing>/.keep`, holding the digest and the set (the names, and for a revision the note it replaces), then makes the moves one rename at a time
    in a fixed order, and last removes the journal. Any later `keep`, `review`, `list` or `save` in that wing that finds a journal finishes the moves it
    lists, which are renames and so safe to repeat, before it does anything else; it refuses to start a different `keep` while a journal exists. A revision
    replaces its reviewed note by a rename over it, so the reviewed note is never absent.
  - Each of these has a test that stops the operation after every step and then retries it (see the acceptance criteria).

### Credentials and personal details

- **At save, the helper refuses a note that holds credential-shaped text.** The owner is not asked: the agent rewords ("the API key, not recorded"). [agreed in
  substance; the rest is a call]
  - **Scope.** The whole note as it would be written is scanned before anything is written: the title, kind, source and verify lines, the body, and, for
    `--into`, the complete resulting note including the earlier text. A credential in a field, or in an appended paragraph, is refused like one in the body.
    The scan runs again at `review` and `keep`, over what is on disk.
  - **Patterns**, a minimum that a test pins; more may be added and none removed. The text is first normalised (NFKC), so a fullwidth or other compatibility form is read
    as the plain one. Every quantifier in a pattern is bounded, and the URL and assignment patterns run only on a line that holds `://` or `:`/`=`, so that one long line
    costs time in proportion to its length (a test pins this with 16 KB lines). The patterns: a private-key block (`-----BEGIN … PRIVATE KEY-----`); an AWS access key id
    (`AKIA` or `ASIA` and 16 upper-case letters or digits); a GitLab token (`glpat-`), an npm token (`npm_`) and a Stripe key (`sk_live_`, `sk_test_`, `rk_…`); a GitHub token (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` or `github_pat_` and a long run of letters, digits and
    `_`); a Slack token (`xox` and a letter, a dash and a run); a Google API key (`AIza` and 35 characters); a JSON web token (three dot-separated base64
    parts, the first two beginning `eyJ`); a key in the `sk-` form (20 or more characters); an `Authorization: Bearer` or `Basic` header with a long token; a URL with a
    user name (or none) and a password before the `@`; and a line that assigns a value of 6 or more non-space characters, with `:`, `=`, `:=` or `=>` (a closing quote may come
    before it and an opening quote after it), to a name that holds `password`, `passwd`, `passphrase`, `pass`, `pwd`, `secret`, `token`, `api_key`, `access_key`, `private_key` or
    `credential` in any case, with any prefix or
    suffix of letters, digits and underscores (`GITHUB_TOKEN=`, `client_secret =`, `DB_PASSWORD=`, `SECRET_KEY=`, `"password": "..."`). A token of the fixed shapes that a
    wrap split over two lines is found by joining the last word of a line to the first word of the next, and is named at the first line. A token wrapped
    over three or more lines, or a value that is only secret by meaning, is not found (a known limit). The title is scanned before the file name is made, so a name
    that comes from a credential is never echoed.
  - **Report.** The message gives the line number and the pattern's name, never the text. A false positive (a note about passwords, say) is refused too, and
    the agent rewords; there is no override flag, because a flag would defeat the scan.
- **At review, the helper flags personal-detail shapes**: email addresses, phone numbers, street-address shapes and long digit runs. A flagged note is never
  routine. The owner always sees it before it is kept. [call]
- **A known limit.** A scan finds shapes, not meaning. A plain sentence that names a person or a home town passes. The skill tells the agent not to write
  them, and the agent's judgment is the second guard. The spec does not claim the scan covers them. [call]

### Review by exception

The owner does not read notes to approve them. [agreed]

- `review` sorts the drafts into **routine** and **outliers** and prints a few lines: counts, and one line per outlier with the reason and a suggestion the
  owner can accept. Routine drafts are counted and not shown. It ends with a digest of the set, as `preview` does. [agreed in substance]
- **Mechanical flags**, computed by the helper, never by the agent's say-so. A draft is routine only if none fires: [call]
  - larger than a limit (about 4,000 characters);
  - a personal-detail shape;
  - near-duplicate of a reviewed note or another draft, by word overlap (no model is needed);
  - a new wing name;
  - a revision that changes more than half of a reviewed note;
  - older than a limit (14 days) and not yet reviewed.
- **Judged flags**, proposed by the agent and labelled as its opinion: a contradiction with another note or with a spec or decision, a suggestion to merge two
  notes, or to promote a lesson to a tracked document (a spec, or a skill such as `verilog-sby-formal`) because it is true for anyone. [call]
- A suggestion is one line the owner can approve with a short answer ("drop 3, merge 2 into 1, the rest are fine"). [agreed in substance]
- **The owner's answer is applied by commands, then checked again.** The numbers in the summary refer to the drafts as `review` printed them. The agent applies
  the answer with `drop` and `merge` (above), which change only drafts and the archive and cannot reach a reviewed note or the palace; then it runs `review`
  again, which prints the new set and a new digest; then the owner's `keep --wing W --digest <digest>` is confirmed. [call]
- **The digest covers the exact set `keep` moves**: for each draft, its wing, file name and whole text (framed by its length in bytes), and for a revision the reviewed note it
  replaces and that note's hash. `keep` recomputes it inside the wing's lock and refuses when anything differs, so a draft changed or added after the review
  is not moved by the old digest. A draft that is not in the set stays a draft. [call]
- **As built (increment C).** `review` prints `review of wing W: N drafts, R routine, O need a look`, then one line per outlier (`<number>. <name> | <kind> |
  <reasons> | suggestion: <suggestions>`), between the recalled-data markers, and, after them, `digest: <32 hex>`; with no drafts it prints "no drafts to review" and
  no digest. The set `keep` moves is **every draft of the wing**, so the owner's "drop 3, merge 2 into 1, the rest are fine" is applied with `drop` and `merge` and a
  second `review`. The digest is taken over, for each draft sorted by name, its file name, what it revises, its whole text and, for a revision, the whole text of the
  reviewed note. A draft that is malformed, holds credential-shaped text, revises a note that is not there, or has the name of a reviewed note without revising it
  **blocks** `keep` (it names the draft and moves nothing); a personal-detail shape, a size over 4,000 characters, an overlap, a new wing, a revision that adds more than
  half of a reviewed note's words, or an age over 14 days only makes it an outlier. `keep` checks the digest and the blockers before it takes the lock or makes
  anything, takes the lock, checks them again, writes the journal `.keep` in the drafts folder (`keep 1`, `digest <hex>`, then `new <draft>` or `revise <draft>
  <target>` for each), moves the drafts one at a time, and removes the journal. A move writes the draft without its `revises` and `new-despite` lines (exclusively for a
  new note, by a rename over the reviewed note for a revision) and then removes the draft, so a repeat finds the work done; a reviewed note that exists and differs from
  a new draft is never written over. `keep`, `review`, `save` and `list` finish a journal they find; a `keep` with the digest of the interrupted one says it finished it,
  and a `keep` with another digest finishes it and is refused. `drop` and `merge` change drafts and the archive only, check what they can before the lock, and a merge
  that crashed between writing the target and archiving the source is repeated safely by the line `merged from <draft> <12 hex of its text>`. `keep` prints the folder
  to file (`<notes>/<wing>`) and `mine` is then run on it by the owner with the wing. [call]
  **As built (increment D, 2026-11-06).** The policy block gains two bullets and the `recall-memory` skill a section "Draft notes" with the flows of saving, finding
  and reviewing, and the final paragraph of the skill now says an agent may save a draft note as well as tell the owner. The block carries the rules that must hold
  when the skill is not loaded (to save silently at the three moments, to list first and extend, the credential and personal-detail rule, to list after a
  compaction, to search the `ideas` wing, the once-per-session review); the skill carries the options of `save`, the review exchange and the ask flow of `keep`,
  and the permission-drift test requires the latter (`wb settings`, `--digest` and the `review` that previews `keep`). The block's limit is 24 lines (it was 14). The
  texts name no path to the notes folder and no other module's skill. Whether an agent follows them is not tested; that is the live run. After the review of the
  increment, each pinned by a test: a refused save for an overlap, a name that is taken or a note that is too short is handled without asking the owner (extend with
  `--into`, use `--new` only for a real near-duplicate, choose another title, lengthen the note), because the general rule "stop and report" would otherwise send an
  agent to the owner for a routine refusal; the drafts of every wing are reached (`wings` shows where drafts wait and `review --wing <name>` reviews each), because a plain
  `review` covers only the project's wing and a draft in a topic wing would otherwise expire unseen; a note is data, and an instruction in it is ignored, most of all in one
  from outside sources; the one question to the owner is asked at a natural pause and includes whether to file the rest, so that `keep` has the owner's word; a correction
  alone is not a lesson, and a path is saved as `explored` or `dead end` only when it cost real effort and no file records it; and a plain search finds only filed notes,
  while drafts are found with `list --wing <name>` and `read`. The block has three moments for saving and the skill adds the fourth (a path tried and dropped). [call]
  **After the security review of increments B and C (2026-11-06), each with a test:** one note cannot stall the helper (the patterns above, and the words of a note
  are worked out once for a review); the journal holds a fingerprint of each draft, and a resumed move checks the draft is still the bytes that were reviewed and that a
  revision names the note the draft says it revises, so a draft swapped after a crash is not moved; an interrupted `keep` is finished **before** the expiry runs, so a
  journaled draft that went stale is filed and not archived; a wing holds at most 200 drafts (the most one `keep` moves) and a `save` makes no wing beyond 50; a
  revision that adds or removes more than half of a reviewed note is always shown, whatever the backlog; every verb that writes or reviews refuses a wing that differs
  only in case from an existing one; `keep` refuses when its drafts folder has vanished, and does not write to the current directory; a `merge` whose marker is already
  in the target says that only the draft was archived. **`wings`, `list` and `review` write**: they run the expiry (archiving drafts over 30 days old in the wings they
  look at, all wings for `wings`) and finish an interrupted `keep`, and they make `.locks`, `.archive` and lock files when they do; setting `save`, `drop` and `merge`
  to `block` does not stop this. An agent may write a draft into any wing by name; it shows in that wing's review. [call]
  Added after the review of the increment: **the list is never cut over a draft the owner has to see.** A blocker and a personal-detail draft are always
  printed; only the plain outliers (old, large, overlapping, new wing, big revision) are cut at 40 lines in all, and the cut line says how many are left out and by
  which flag. A revision draft must have the name of the note it replaces (`revises` is a note name, else the draft is malformed), no two drafts may replace the same
  note, a reviewed note that cannot be read blocks its revision, and a revision that adds **or removes** more than half of the reviewed note's words is an outlier.
  `keep` moves at most 200 drafts at a time, so that its journal is read back (up to 64 KiB). `drop` can archive a malformed draft by its file name, so that the owner
  is never left with a wing that nothing clears. `merge` stays in one wing: a name with a prefix must name the wing the other name, `--wing` or the project names, and
  a prefix is never used to look for the source in a wing the target is not in. The reviewed notes that are not the target of a revision are not in the digest; they
  can change the overlap and new-wing flags, which only advise, and a name that a reviewed note holds still blocks a draft under the lock. [call]
- Output is short plain lines. It never prints a note's whole text unless the owner asks for it with `read`. [agreed in substance]
- **Expiry.** A draft whose `updated` date is more than 30 days old is moved to the archive folder. The helper deletes no note. [call]
  - It is done lazily, at the start of `save`, `list`, `wings` and `review`, by the same routine, and by no scheduled process. It is idempotent, and each move is a
    rename within the notes folder, so a killed run leaves the draft where it was or archived, never both.
  - An archived note is excluded from `list` and from the counts of `wings` unless `list --state archived` (or `all`) is asked for, and `wings` shows the
    archive's count apart. `read <name> --state archived` prints one. Recovery is the owner's: moving the file back; the helper has no restore command. [call]

### Not needy

- While a brainstorm is going, the agent saves silently and does not ask about notes. [agreed]
- The owner is asked about notes at most once per session, when something is waiting. That one **review exchange** is: the summary (counts and the outliers),
  the owner's one short reply, and the harness's confirmation of the commands the reply leads to, which are `keep` and then `mine`. The agent runs both after
  one reply ("file them"), so the confirmations are the harness's two prompts for one answer and not two questions from the agent. Nothing is asked when
  nothing is waiting. [agreed in substance; the exchange is defined here to match command-permissions.md, where each confirmed command is a prompt]
- A refused credential is handled by the agent rewording, with no question to the owner. [call]
- A status line (`wings`) shows counts of drafts, reviewed notes and the last filing, so the owner can see whether the feature is doing anything. [call]

### When a note is saved

- **A brainstorm with no spec.** After a playback that the owner accepted (the `brainstorm` skill plays back what it understands in short chunks and asks what is
  wrong), the agent saves the point as a note or adds it to the one it belongs to. The `brainstorm` skill belongs to `groundwork`; this module's own skill
  gives the same instruction for any brainstorm, and the `groundwork` nudge is an optional extra. [agreed]
- **A problem solved after the owner steered.** A correction alone is not a lesson. When the work then succeeds, the agent saves a `lesson` that keeps the
  owner's guidance: the situation, what worked, why, and how to verify it. [agreed]
- **A researcher's run.** A research agent saves the ideas it distils, each with its source, locator, retrieval date and content hash, as drafts. It does not
  file them; the owner reviews. The note says it came from outside sources. [agreed]
- **A dead end.** A path tried and dropped is saved as `explored` or `dead end`, so the next researcher does not repeat it. [call]
- **The agent's own finding.** When the note it concerns holds something the owner accepted, the agent's finding or guess goes in a note of its own (`finding` or
  `open question`) that says which note it concerns; the accepted note is not extended with it. The live run of 2026-11-06 showed a guess added to a `decision`. [call]
- **Forms and refusals (plan `2026-11-06-notes-live-run-fixes`, increment A).** The always-loaded block shows the form of `save` and `read` and the seven kinds, because
  the live run showed a fresh agent spending about ten calls guessing them. `keep` and each `mine` step are run as one command with nothing appended (no pipe, no
  redirect, no `cd`, no `2>&1`). The question about filing is asked once, with the review question. A command the gate refuses with the rule `names` is not met by
  rewording the note: the text goes to a file and reaches `save` on standard input (`--body - < <file>`), which the gate was seen to allow, or the owner is told. The block
  is 24 lines, its limit. Whether an agent follows this text is for the next live run. [call]

### Finding notes again

- Before drafting a spec, a decision record, a roadmap candidate or a plan, and before brainstorming or researching, the agent searches the project's wing and the
  shared `ideas` wing (the rule already says to search once per task; this adds the wing). [call]
- General concepts and analogies from research go to the shared **`ideas`** wing; an idea aimed at one project goes to that project's wing. [call]
- When starting work in an area of tools or hardware, the agent runs `notes wings`, then searches the topic wings that look relevant with `--wing`. [agreed in
  substance]
- After a compaction or in a new session on a brainstorm with no spec, the agent runs `notes list` (drafts included) and reads the relevant notes. The policy
  block says so, because the root file is re-read after a compaction. [call]
- A side session with its own task reads only what the task needs and saves its finding back as a note. [agreed]
- Everything it reads is recalled data and possibly stale. A fact about a machine is checked with its `verify` line. A note's age is shown in the result.

## Acceptance criteria

1. With no `.workbench/local/mempalace.json` and no `origin`, `notes save` writes nothing and says what to create. With the file, it saves under that wing;
   with both, the file's wing wins. With a remote only, the wing is the repo name.
2. `search`, `mine` and `sync` behave as before, including the default wing.
3. The first save makes the notes folder and the wing's draft folder at mode 0700, follows no link, and writes nothing else. Nothing is made at install.
4. A note holding a credential-shaped line is refused, naming the line and pattern and not the text; the same note reworded is saved.
5. A note under the minimum size is refused.
6. A save that belongs to an existing note adds a dated paragraph and changes no earlier text; two saves at once leave both additions; a killed save leaves the old note whole.
7. `review` prints counts and only the outliers; a draft with a personal-detail shape, a new wing name, a large size or a near-duplicate is an outlier; the digest
   is the same on a second call and differs when a draft changes.
8. `keep` moves only the drafts the digest covers, refuses a changed set (a draft changed, added or dropped after the review), replaces a reviewed note only
   from a revision that names it, and `mine` is not pointed at the drafts or the archive.
9. A draft whose `updated` date is more than 30 days old is archived by the next `save`, `list`, `wings` or `review`, and not deleted; a second call changes
   nothing; the archived draft is absent from `list` and the counts unless asked for.
13. A title with `/`, `..`, a control character or only symbols is refused; two titles that normalise alike do not overwrite each other; a link planted in the
    notes folder is refused.
14. `save` with text that overlaps an existing note refuses and lists it; `--into` extends the named note; `--into` with no match or two matches refuses;
    an addition to a reviewed note makes a revision draft and leaves the reviewed note unchanged until `keep`.
15. After `drop` and `merge`, `review` prints a new digest that differs from the first, and `keep` with the first digest is refused.
16. `list --state archived` shows the archived notes and `read <name> --state archived` prints one; the default `list` shows reviewed notes and drafts only.
17. For `merge` and `keep`, a test stops the operation after each step (a fake crash) and retries it: no text is lost, `merge` adds the text once, `keep` finishes
    the moves it journaled and then matches its digest, and a different `keep` is refused while the journal exists.
18. A credential in the title, the source line, the verify line, the body, or the paragraph added with `--into` is refused with the line number and the
    pattern's name and without the text; each pattern in the list has a test; the same note reworded is saved.
19. One review exchange covers a reply and the confirmations of `keep` and `mine`; no other question about notes is put to the owner in the session.
20. `review` and `keep` work on one wing: `keep` without `--wing` is refused, a digest from one wing is refused for another, and drafts in other wings are
    untouched by a `keep`.
21. A title that normalises to the name of a draft, a reviewed note or an archived note is refused, with and without `--new`; archiving gives the name a UTC
    time suffix, a second archiving of the same name keeps both, and a draft never replaces an archive entry.
22. `drop` refuses a reviewed or an archived note; `merge` refuses a source that is not a draft, a target in another wing, a target equal to its source, a name
    that matches two notes, and a `..`, absolute path or control character in a name; both accept `<wing>/<name>` and the project's wing when none is given.
10. A live run: brainstorm, compact the session, resume, and the agent picks up from the notes; then a side session on one topic finds only that note and
    writes its finding back; the owner is asked at most once.
11. A researcher's draft carries its source, locator, date and hash and says it came from outside sources.
12. The test of the helper's imports and forbidden words passes, or the plan changes it with the owner's approval.

## Known limits and risks

- Saving depends on the agent following the skill. A missed save is possible; other users report wanting deterministic save hooks. A hook is harness-specific
  and none is built. [call]
- A scan cannot find a person's name or a home town in a plain sentence (above).
- A search of the palace is only as good as what was reviewed and filed; the first sessions will show whether the notes earn their place.
- Notes from outside sources can carry text that tries to give instructions. They are recalled as data, and the review flags nothing about meaning.
- Two spellings of one wing, or a project renamed after notes were filed, split the notes across wings. Renaming is the owner's act. [open]
- Where `keep` and `mine` are two confirmations, the owner confirms twice per review. [open]

## Evidence

**Live run, 2026-11-06, reported by the owner from real sessions** (the keep, mine and sync arguments at `ask`; `save`, `drop` and `merge` at `none`; helper at commit `e98c027`).
Recorded as reported, not edited into a pass.

What happened:

1. *Brainstorm with no mention of notes.* The owner began a brainstorm of a scheduled research agent's source selection, with no spec. The agent searched the palace and listed
   notes first, asked its questions, and after the owner accepted a playback ("good so far") saved one draft, `research-agent-source-selection-rules` (kind `decision`),
   without asking. It asked no question about notes. It told the owner of the draft only after the owner listed the drafts.
2. *Cost of the save.* The agent needed four tries to save: `save --help` is refused (the usage text was all it got); a combined command with a `kinds` call and `--kind design`
   was refused by the harness's command gate because the body contained a word with the letters of `keep` in it (rule `names`, since `keep` is at `ask`), and the agent reworded the
   text without telling the owner; then `design` is not a kind. The fourth try saved.
3. *Compaction.* After `/compact` and "where were we?", the agent answered with no tool call, from the harness's compaction summary. The answer was complete. This did not
   test the notes, and the rule "after a compaction, list the notes" was not followed.
4. *New session, same topic.* The agent listed the notes first, read the draft with `read`, restated the owner's three rules, and marked its own guess ("drop and report")
   as its call. It asked nothing about notes. It also searched the palace (nothing relevant, low scores), and ran one `grep` of the spec to learn the syntax.
5. *Side session.* Asked to work out how to tell a paper from a write-up and to note what it found, the agent listed the notes, read the draft, and extended it with
   `save --into ... --body -`, labelling the text as its own reasoning with nothing fetched. It spent about six calls on wrong forms (`show`, `--help`, `search ... --wing` after
   `--`, a bare `save`, a grep of the spec). It put its hypotheses into the same note as the owner's accepted rules, a note of kind `decision`.
6. *Review.* "Let's go through the notes" gave `1 drafts, 0 routine, 1 need a look` (flag: new wing), a plain summary, the digest and one question. The owner answered "fine, file it".
   The agent then ran `keep` with `2>&1 | head -30` appended; the gate refused it (the exact simple command only), its hint named a command without `run` (not a valid
   command), the agent tried that, was refused again, and gave the owner the same wrong form. The owner ran `wb run mempalace-notes keep --wing project-workbench --digest ...`
   and it printed `kept 1 notes in wing project-workbench`. The agent then asked whether to file ("your call"), a second question after the owner's answer.
7. *Filing.* On "Now preview and file that folder" the agent ran the preview, then the `mine` step with `--confirm --digest` as one command with nothing attached; the owner confirmed it
   (6 drawers). The program's standard error said the wing would be `project_workbench` by auto-detection; the wing used was `project-workbench`.
8. *Search.* A search from outside the session found the note first (cosine 0.725), against 0.47 for the best unrelated result.

What it shows: a fresh session continued an unspecced brainstorm from a note alone; a side session found and extended it; the owner was asked once, in plain lines; keep and mine
completed; the filed note was found by a plain search. The agent asked nothing about notes outside the review.

What it does not show: the notes after a compaction (the harness's own summary carried everything); more than one topic, one side session and one review; whether the agent saves
at the other moments (a lesson, a dead end, a researcher's idea); a run with more than one draft, an outlier, a revision or a second wing; any run after weeks.

Defects found (for a follow-up, not a widening of the first plan): (1) the always-loaded block gives no command form or kinds, which cost about ten calls over three sessions; (2) with
the three arguments at `ask`, the command gate refuses any command whose text, prose included, contains a word with their letters in it, and the agent hid the cause by rewording;
(3) the agent appended a pipe to `keep`, and the gate's hint omits `run`; (4) the agent mixed its findings into a note of the owner's accepted decision; (5) `review` prints
"1 drafts"; (6) the filing asked a second question. Neither anti-goal was met: the run offered value and was not needy beyond (6).

Follow-up: plan `2026-11-06-notes-live-run-fixes` addresses (1), (3), (4) and (6) in the block and the skill (increment A), the plural and the gate's hint (5 and the hint in 3) in
increment B, and drafts the decision on (2) in increment C. Whether the new text is followed is for the next live run.

## What is left to the builder

The command shapes, the file format and the flags are calls, and each can be changed with the owner's word. A plan would likely build, in order: the folder, the
wing rule and `save`, `list`, `read`, `wings` with the refusals; then `review` and `keep`; then the skill and the policy-block text; then expiry and the
status line. Each is one verified, reviewed commit. The sizes are the builder's.

## Governing decisions and references

- Decisions: `2026-10-21-module-code-lives-in-modules`, `2026-10-19-tracked-pointer-rule`, `2026-10-23-one-owner-per-skill-name`.
- Specifications: `mempalace.md` (the module, `mine`, the folder rules, the evidence of 2026-11-06), `command-permissions.md` (levels and the digest),
  `code-work.md` (compaction), `knowledge-tools.md`.
- What other users do, from web search snippets of 2026-11-06, **not opened and not verified**, so they carry no content hash and govern nothing here:
  notes written at checkpoints and curated, not saved by default; auto-saved memory goes stale; verbatim storage with scoping beats summarising;
  short entries that echo a query degrade the corpus. No page is cited as authority; the conversation gave the links, and the builder should read them
  before relying on any claim.
