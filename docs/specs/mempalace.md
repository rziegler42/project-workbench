# mempalace

Status: Current. Approved by the owner on 2026-10-24. Built by plan `2026-10-24-mempalace-module` (increments A to F); "As built, and its limits" lists what was and was not exercised. "Evidence" records what the installed program was seen to do on 2026-10-24.

Terms are defined in `terms.md`. The declaration it must satisfy is defined in `module-contract.md`; the
launcher, the kit and module commands in `module-boundary.md`; the authority rules in `trust-and-approval.md`.
Its place among the knowledge modules is in `knowledge-tools.md`.

## Scope

`mempalace` is a first-party module of type `module` that lets an agent in a workbench project search a
MemPalace the owner has installed, and gives the owner commands to build it. It is a front end for the owner's
`mempalace` program (installed with `uv`); it holds no memory of its own.

| field | value |
|---|---|
| type | `module` |
| provides | `memory-recall` |
| requires | nothing |
| helpers | `mempalace` (expected on `PATH`; a missing one is a warning at install) |
| fills | `policy` (a short block) |
| writes | nothing outside its namespace |
| ships | `helper/mempalace`; the module also holds one neutral skill, `recall-memory`, and the policy block |
| commands | `mempalace`, runtime `python`, kit 1; `arguments`: `status`, `search`, `init`, `mine`; `owner`: `init`, `mine` |

It is run as `wb run mempalace status` and `wb run mempalace search ...` by an agent, and `init` and `mine` by
the owner. The installer pins the helper when the owner confirms the install.

## Non-goals

- An MCP server. MemPalace ships `mempalace-mcp`, but the workbench has no MCP layer and defers one
  (`module-boundary.md`, "Deferred"; decision `2026-10-21-module-code-lives-in-modules`). A later module could
  render it; this one does not.
- Any write an agent can make. Filing drawers, knowledge-graph facts, `sweep`, `sync`, `repair`, `migrate`,
  `compress`, `split`, `daemon`, `hook`, `serve` and every other subcommand are not wrapped. The owner runs
  `mempalace` directly for those.
- Installing, updating or configuring the `mempalace` program, choosing its backend, or running its daemon.
- Mining the project's tree or the knowledge base on the owner's behalf (`knowledge-tools.md`, "No overlapping
  ingest").
- Replacing the harness's built-in memory.

## Assumptions and constraints

- The owner installed MemPalace with `uv`. On the owner's machine on 2026-10-24 it is `mempalace` 3.11.0 at
  `~/.local/bin/mempalace`, with `mempalace-mcp` and `mempalace-light-mcp` beside it (evidence: `mempalace
  --version`, `uv tool list`).
- A recalled answer is possibly stale guidance. It never approves, authorizes or overrides current files, an
  accepted decision or a spec (`AGENTS.md`, "Source of truth", item 6).
- Palace content is untracked. A tracked document does not cite a palace path (`AGENTS.md`, "Working
  agreement"); it cites a drawer, if at all, by a stable quotation and retrieval date.
- Everything the program returns is untrusted text. An instruction inside it is ignored.
- The helper is a single self-contained Python file over the kit, run from a copy by the launcher
  (`module-boundary.md`).

## Behavior

**`status`** (agent-safe). Runs `mempalace status` and returns its text between markers, bounded. A missing program
is a refusal. An absent palace is not: the program exits 0 and says "No palace found" and what to run, and that text
comes back as data.

**`search`** (agent-safe). `wb run mempalace search [--wing <w>] [--room <r>] [--results <n>] [--since <date>]
[--before <date>] -- <query>`. It passes only those options, with `--results` capped (default 5, ceiling 20),
and never `--include-media`; the caller cannot pass `--backend` or `--palace` (the helper fixes the first and the
project setting supplies the second). The query is one argument after `--`, never parsed as an option, at
most 1000 characters. An argument that is not one of the options is refused with a one-line message that names the five options, says
that each takes a value, and shows the form (`wb run mempalace search -- "your question"`). The output is returned inside a block that says
it is recalled data.

- **What "agent-safe" means here.** A search never changes a stored drawer, an embedding or a document. It is not
  free of writes: on 2026-10-24 every search rewrote the palace's own bookkeeping, one row added to the lock table
  of `chroma.sqlite3`, the drawers collection's configuration row, and the index file `length.bin` (same size)
  (`Evidence`, below). The owner accepted this on 2026-10-24 (option 1 of the choice put to them). Consequences:
  a palace on a read-only file system makes `search` fail; a `search` run while the owner runs `mine` can contend
  for the same files, and the owner should not run them together; the lock table grows by a row a search.
- **Never a download.** Without the embedding model cached the program tries to download it (79 MB, from the
  `chroma-onnx-models` bucket on Amazon S3). The helper checks first that
  all six files the program needs (`config.json`, `model.onnx`, `special_tokens_map.json`, `tokenizer_config.json`,
  `tokenizer.json`, `vocab.txt`) exist under `$HOME/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/` (the program
  starts a download when any one is missing; a link counts if it leads to a file) and refuses with a message that tells
  the owner to run `mine` otherwise, so an agent's search can never start a download. The path was seen with `HOME`
  and `XDG_CACHE_HOME` both set to the same cache; whether `XDG_CACHE_HOME` alone moves it is not tested. The check
  is right for the `minilm` model. When the project names the palace, the helper also reads the palace's
  `mempalace_embedder.json` and refuses a palace recorded with any other model name; when it does not, it cannot know
  where the palace is and checks the model file alone.
- **Exit codes and streams.** The program exits 0 for a result and for "No results found", and 1 for an absent
  palace database and for an error, with its message on standard output. The helper reads the exit code and
  treats the text as data on either stream.

**`init`** and **`mine`** (owner-run). Listed under `owner`, so the harness denies them to the agent. The helper
also runs them only when standard input and output are terminals (the rule `approve` follows), so that a harness
with no deny rule does not let an agent run them; that test is friction and not authentication. It then hands the
terminal to the program, which asks its questions and prints its progress, and waits with no time limit. Without
`--yes`, `init` asks the owner to accept the detected rooms; the program crashes on end of input, which is why a
captured run could not serve it (`Evidence`, 2026-10-24).

- `init <dir>` writes `mempalace.yaml` **into `<dir>`**, so an `init` of the project root leaves an untracked file
  in the project. It also saves the palace path in `$HOME/.config/mempalace/config.json`. It always passes `--no-llm`, so that no provider is contacted. MemPalace's default is to refine
  entities with a language model, and its providers include remote ones (`ollama`, `openai-compat`,
  `anthropic`); the owner who wants one runs `mempalace init` directly and sees what it sends.
- `mine <dir>` passes `--dry-run` unless `--confirm` is given, so the owner sees what would be filed first. The
  first real `mine` downloads the embedding model, and it writes `$HOME/hallways.json` directly in the home
  directory. The helper says both before it runs without `--dry-run`.
  `mine` also takes `--wing <name>` and `--mode projects|convos`, and nothing else.
- For both, the directory is refused when any of `mempalace.yaml`, `mempalace.yml`, `mempal.yaml`, `mempal.yml`,
  `entities.json` and `.gitignore`, or a backup of one (a name that begins with one of them, compared without regard to
  case), is not a plain file with one name. The program opens those names for writing and follows a link, so a planted
  one made the real `init` overwrite a file outside the directory (reproduced 2026-10-24 for the configuration; the
  entities file and the `.gitignore` append are read from the program's source; security review).
- For both, the directory is refused when it is, holds or lies inside a palace the program may use here: the
  project's setting, the `palace_path` the program saved in its own configuration, or its two default places.
  `init` writes `.mempalace/origin.json` under the palace, and `mine` would index the palace's own files.
- For both, the directory is one the owner names: it exists, is not a link and has no link in its path, and is not
  inside `.git` or `.workbench`. It is refused when it is the project root or holds it, unless
  `--allow-project-root` is also given, so the default does not make the project's tree a second index
  (`knowledge-tools.md`). `init` takes only `--yes` and `--allow-project-root`.
- Neither takes `--llm-api-key`, `--llm-provider`, `--llm-endpoint`, `--accept-external-llm`, `--daemon`,
  `--background` or `--palace` (the project setting supplies that).

**First use in a project (as found on 2026-11-05; "Evidence", first use).** (1) Write nothing: the wing defaults to the project folder's name. Write
`.workbench/local/mempalace.json` (untracked, this clone's own) only to name another wing, `{"format": 1, "wing": "<name>"}`, or to keep this
project's notes in a palace of their own outside the project tree, with a `palace`.
(2) In the owner's own terminal, not in an agent session (a command run from a session has no terminal and `init` and `mine` refuse it):
`wb run mempalace mine <directory>`, which is a dry run, and then the same with `--confirm`. (3) Do not run `init`: `mine` does not need
it. Without a `mempalace.yaml` the program files every file of the directory in one room, `general`, under the wing it is given, prints
the hint "No mempalace.yaml found … using auto-detected defaults", and writes nothing into the directory. `init` adds room names guessed
from file names, a list of people and projects (`entities.json`, and the program's registry in the home directory), a note on the kind of
corpus, and per-directory patterns that exclude files from mining (the one capability that needs a `mempalace.yaml`); it writes the first
two files into the directory it scans, the program offers no option to put them elsewhere, and the config is read only from the directory
being mined. Run `init` only for those features, knowing that two files will sit in that directory. A `mine` of a directory is not
repeated for changed files by anything: it is run again by the owner.

**How the program runs.** As `knowledge-tools.md` states: found in an absolute `PATH` entry that exists and, with every
link resolved, is outside the repository (the resolved entries and the resolved program are what is used, and what the
child gets as its `PATH`; a containment check that cannot examine a path counts it as inside), no shell, a fixed argument shape, a time limit (60 seconds for `status` and `search`; none for `init` and `mine`, which the owner watches on their
own terminal), an output cap (for `status` and `search`, whose output is returned to the caller), the caller's
`HOME` used because MemPalace reads its configuration from it. No environment variable of the caller is passed on except `HOME`, `PATH`,
`LANG` and `LC_*`; in particular none that selects a backend or an API key. The installed program reads, among
others, `MEMPALACE_PALACE_PATH`, `MEMPALACE_BACKEND`, `MEMPALACE_EMBEDDING_API_URL` and `_MODEL` (remote
embeddings), `MEMPALACE_HUB_FORWARD`, `MEMPALACE_LOG_FILE` and URL and token variables for other stores, and none
of them reaches the child. The helper sets `PYTHONDONTWRITEBYTECODE=1`, so that running the program writes no
bytecode into its own install directory. The helper fixes `MEMPALACE_EMBEDDING_MODEL` to `minilm`, which the program reads before its
configuration file, so that the model it uses is the one whose cache was checked; it sets `ANONYMIZED_TELEMETRY=False`, ChromaDB's own
switch for usage reporting, which ChromaDB leaves on by default and the program sets for itself only as a default ("Evidence", usage
reporting); a palace filed with another model
makes the program refuse the read, and the module supports MiniLM only (the owner who wants another runs the program
directly). It also fixes the program's backend to `chroma` with the program's own `--backend` option, which ranks
above its configuration file, so that no read goes to a remote store the home configuration might name. And it sets
git's own configuration through the environment (`log.showSignature=false`, `core.fsmonitor=false`, no lazy fetch, no
prompt), which ranks above a repository's: `init` runs git inside the repositories it finds, and a repository can
select a program for git to run. The helper reads one file of the project, the setting below (through a held descriptor that refuses a link at
any component), and the
palace's `mempalace_embedder.json`, and writes nothing in the project. Every command runs from a project and
refuses outside one.

**Limits of the owner commands** (security review, 2026-10-24; recorded and not closed). The directory and
file-name checks are made before the program opens the path, so a writer that changes the owner's tree while the
command runs could swap a directory or a name afterwards; a program that works on path names cannot be made safe
against that without a sandbox, and the helper is not one. The miner skips symbolic links (its source tests for one;
a planted link to a secret was not ingested in a run), which limits what a link in a mined tree can reach. A terminate
signal stops the program but not what it started. The program stays in the helper's process group; moving it to a group
of its own is possible, but it needs the helper to hand the terminal to that group and take it back (and to survive the
signals that follow) or the program is stopped when it reads the owner's answers, and a mistake leaves the owner's
terminal stopped. That cost was judged larger than the risk of a worker outliving an interrupted `init` or `mine`, and
the read commands, which run in a session of their own, kill everything they started. The git settings above cover
the two settings known to run a program on a read; a repository can select others for commands the program does not
run today, so the owner who runs `init` on a tree they did not write is trusting git and the program to that extent.

**Palace location.** The helper does not choose one. MemPalace picks its own: `--palace` is honoured, and `init
--palace` saves the path in `$HOME/.config/mempalace/config.json`. Its `--help` names `~/.mempalace/palace`, which
the program did not use; with no palace the program looked in `~/.config/mempalace/palace` on 2026-10-24. What
decides the default for a fresh home was not isolated (the evidence run passed `--palace` and then relied on the
saved path). A clone may set another with
`.workbench/local/mempalace.json` (`{"format": 1, "palace": "<absolute path>", "wing": "<name>"}`, with the palace, the wing or both),
which the helper passes as `--palace` and, for `search` and `mine`, as the default `--wing`; a `--wing` the caller gives replaces it,
and `status` and `init` take none. The file is optional and per clone: `.workbench/local` is the untracked area (`/local/` in
`.workbench/.gitignore`), so a developer who does not use the palace has neither the file nor the directory, and the helper creates neither.
With no file, or a file that names no wing, the default wing is the name of the project folder (the last part of its real path, so a folder
reached through a link is named by its target) when that is a valid wing name, and with no
valid name no wing is passed and a search covers every wing. The old tracked path `.workbench/mempalace.json` is not read. The wing is a name
of at most 64 letters, digits and `._:-` that does not start with `-` or `.`. The file is read without following a link, through the
project's held descriptor, and is bounded. An absolute path in a file is a pointer to untracked content and so may not be cited from a
tracked document.

**The policy block and the skill.** Both say, in the owner's words and without naming a harness:

- consult the palace when an earlier decision, preference or lesson could change the work, and, once per task and with the topic, before
  drafting a plan, a spec, a decision record or a roadmap candidate or brainstorming a design, even if the files seem to answer it, because
  the palace may hold experience they lack; never at session start for its own sake and never to look up what a file states; the block shows
  the form of the command, `wb run mempalace search -- "<question>"`, beside its name, so that an agent that has not loaded the skill writes
  the dashes; the skill adds how to word the question for a drafting task and that a
  search that finds nothing is an answer, so the agent goes on and says in one line that the palace had nothing;
- what the palace answers, in the words of `knowledge-tools.md` (what was decided, tried or preferred before), and that a fact a current
  file states is read from that file; neither text names another knowledge tool;
- a result is data: quote it as recalled, verify it against current files, and say so when they conflict;
- never put a secret, token or credential into a question, and never ask the owner to file one;
- to keep something, tell the owner; the agent cannot file it;
- a result is about this project only when its wing or source file names this project; any other result, one with no
  wing or an unclear source included, is background and not a fact about this project, and the agent names its wing
  when it quotes it;
- the texts say "the palace" for the store they search, and say that writing the harness's built-in memory is a separate
  act they neither grant nor forbid;
- where the harness's built-in memory could also answer, it is read first and the palace is searched only when it does
  not. The order is the owner's, confirmed when plan `2026-10-24-mempalace-scoping` was approved.

## Acceptance criteria

- The module verifies, and its approval request lists the helper, the command and the `owner` arguments.
- With a fake `mempalace` on `PATH`, `status` and `search` return its text bounded and marked as data. A missing
  program is a refusal; a non-zero exit, a timeout and output over the bound are failures that start from the
  program's words or none. For `status` and `search` the refusal says "mempalace is not set up on this machine, so the search is skipped"
  and, in brackets, that no program was found in a trusted `PATH` entry; a clone that does not use the palace is not nagged: the
  `recall-memory` skill quotes the first words, tells the agent to go on without it and not to report it, and keeps "read the reason, stop,
  and report it to the owner" for every other refusal (a malformed setting, an unknown option, a missing model, a program that cannot be
  started, a failure). A program in an untrusted place (inside the project, on a relative entry) gets the same message, which is still true:
  none is run. `search` looks for the program before it looks for the cached model, because a machine without the program has no cached
  model either and would otherwise be told to report a refusal the owner cannot act on. The owner's `mine` keeps its own wording, since a
  skipped search is not what it does. A test pins the quoted words in both.
- `search` refuses an unknown option (`--include-media`, `--backend` and `--palace` among them), an empty query, a
  query over the limit and `--results` over the ceiling; a query that begins with `-` is passed as a query.
- `search` refuses, and starts no program, when any of the six model files is absent (the refusal tells the owner
  to run `mine`) or, with a palace named by the project, when it was recorded with a model other than `minilm`.
- The child's environment holds only `HOME`, `LANG`, `LC_*`, the resolved `PATH`, `PYTHONDONTWRITEBYTECODE=1`,
  `MEMPALACE_EMBEDDING_MODEL=minilm`, `ANONYMIZED_TELEMETRY=False` and the fixed git settings; the program is started with
  `--backend chroma`.
- `init` and `mine` are listed under `owner` and run only from a terminal; `init` always passes `--no-llm`; `mine`
  without `--confirm` passes `--dry-run`; a project-root target, a target that overlaps a palace, and a target holding
  a link, a directory or a shared file under a name the program writes through are refused.
- The helper writes nothing in the project, and no test starts a real `mempalace` or reaches a network.
- A setting (`.workbench/local/mempalace.json`) that is a link, malformed, oversized, has a key other than `format`, `palace` and `wing`, names
  neither a palace nor a wing, or holds a relative or unclean path or a wing that is not a name is refused, as is a `local` that is a link or
  a file; a missing `local` or file is no setting. `search` and `mine` pass the wing of the setting, else the project folder's name when it is
  a valid wing name, unless the caller gives `--wing`, and `mine` says which of the two it used before it runs. The old path is not read.
- The policy block and the skill carry the statement of what the palace answers and the data-not-authority rule and name no other
  knowledge tool, and an install adds no file
  outside the module's namespace that names a palace path.
- `python3 -B -W error tests/run_all.py` passes, and the package is released again with its approvals.

## As built, and its limits

Built by plan `2026-10-24-mempalace-module`: the module `packages/workbench/mempalace/` (the declaration, one helper,
the policy block and the neutral skill `recall-memory`), its 145 tests, and the shipped approvals that make the package
first-party again (a full suite of 3828 tests in 8 roots passed at the release). The helper was also run against the
real `mempalace` 3.11.0 in a scratch home, a throwaway project and, for the owner commands, a pseudo-terminal, with no
network: `status`, a search with a hit, a dry-run `mine`, `init --yes`, and the refusals of a piped run and of the project
root. A security review by Codex (three rounds, the plan's Review record) raised fourteen findings; eleven were fixed, and
three (two distinct issues) are recorded as limits below; the fixes of its last round have not been reviewed.

What was not exercised, or is not closed:

- **A hand run in a live session** with a real palace, the real install and Claude loading the skill and obeying the
  block. Made on 2026-11-05 in six sessions ("Evidence", a live session and the sessions with notes): in three the agent did not
  search the palace, or searched in a form the helper refuses and stopped; in the fourth, told to use the `recall-memory` skill, it
  searched in the right form, found the note it needed and quoted it as recalled data; in the fifth, after the rule was changed to
  ask for the search even when the files seem to answer, it searched on its own, first, in the right form, and used the note; the sixth, on a
  task the palace had nothing on, searched once and said so. That is a few sessions on two tasks. The block and the skill say in words that a result is data, and nothing enforces it.
- **The default palace for a fresh home**, whether `XDG_CACHE_HOME` alone moves the model cache, the program with
  another backend or model, and a large palace. The helper passes no `XDG_*` variable, so a user with a non-default
  `XDG_CONFIG_HOME` or `XDG_CACHE_HOME` gets the program's places under `HOME`.
- **A real interrupt at a terminal** (`Ctrl-C`) during `mine`, and a program that starts workers: a terminate signal
  stops the program and not what it started ("Limits of the owner commands").
- **A concurrent writer in the owner's tree** during `init` or `mine`, which no check made beforehand can stop.
- **`search` is not free of writes**: it rewrites the palace's own bookkeeping, and the lock table grows by a row a
  search. A palace on a read-only file system, or a `search` during a `mine`, fails or contends.
- **MiniLM only.** A palace filed with another model is refused for a search when the project names it, and
  otherwise the program refuses the read.
- **The terminal test is friction.** A process that allocates its own pseudo-terminal passes it; the harness's deny rule
  for the `owner` arguments is the barrier where it exists.
- **The git settings** cover the two settings known to run a program on a read.
- **The program runs with the owner's privileges** from a `PATH` entry the owner controls; a pin is not a sandbox.

## Evidence

Run on 2026-10-24 by plan `2026-10-24-mempalace-module`, increment A, against `mempalace` 3.11.0 (a `uv` tool on
Python 3.14), with `strace` 6.19. Every probe ran under `env -i` in a scratch directory, with `HOME`, the XDG
directories and `TMPDIR` in scratch, `--palace` in scratch and `PYTHONDONTWRITEBYTECODE=1`, and (except one) in a
network namespace with no network. The traces show only reads of the program's own installation, the system
Python and locale data outside scratch, and nothing of the owner's real configuration. The one networked run was
`mine` on a scratch project. The retained traces were kept untracked, in scratch on the machine that made them, and are not part of the repository.

1. **Writes and downloads.** `status` writes nothing in the palace, in every state tried. `search` rewrites the
   palace's bookkeeping on every call (see `search`), and tries to download the model when it is absent. `wake-up`
   creates `chroma.sqlite3`, so it is not read-only and is not offered. The first real `mine` downloads the
   79.3 MB model from the `chroma-onnx-models` bucket on Amazon S3, writes `$HOME/hallways.json`, lock files
   under `$HOME/.mempalace/locks`, and starts POSIX semaphores in `/dev/shm`; `onnxruntime` also keeps a small
   cache under `$HOME/.cache/Microsoft/DeveloperTools`.
2. **Output.** Plain text only. `search` prints a header and numbered hits with wing, room, source, scores and the
   stored text. It returns the nearest drawers even for an unrelated query. No machine-readable form was found.
3. **Exit codes.** `status` exits 0 even with no palace; `search` exits 1 with no database or on an error (message
   on standard output) and 0 for results and for "No results found" under a filter that matches nothing.
4. **Palace location.** `--palace` is honoured; `init --palace` saves the path in
   `$HOME/.config/mempalace/config.json`. What decides the default for a fresh home was not isolated.
5. **`mine --dry-run`** filed nothing and changed no palace file.
6. **`wake-up`** is not read-only. Not offered.
7. **A query that begins with `-`**, passed as one argument, was treated as a query.

Not determined: whether `XDG_CACHE_HOME` alone moves the model cache, the default palace for a fresh home, the
behavior with another backend, and the behavior against a large palace.

**Usage reporting (2026-11-05; plan `2026-11-05-mempalace-use-and-independence`, increment E).** A report on the web said that ChromaDB's
usage reporting might still be on in MemPalace. Run on the machine of the owner (Darwin 25.6.0), against `mempalace` 3.11.0 with ChromaDB
1.5.9 (a `uv` tool on Python 3.13), from the project at commit `d0a81bb`, the helper under test being the one of the increment.
*Source reading (the Python source only; ChromaDB's compiled core was not read).* ChromaDB's `Settings` has `anonymized_telemetry: bool = True` (`chromadb/config.py`), so its default is on, and the switch is
that setting, which the environment variable `ANONYMIZED_TELEMETRY` sets. In this version the client it would use,
`chromadb.telemetry.product.posthog.Posthog`, has a `capture` that does nothing, and the `posthog` package is not installed. MemPalace turns
the setting off in two places: `mempalace/__init__.py` sets `ANONYMIZED_TELEMETRY` to `False` with `os.environ.setdefault` at import (so a
value the caller exported wins), and `mempalace/backends/chroma.py` passes `Settings(anonymized_telemetry=False)` to every client it opens;
both comments cite an advisory (GHSA-8h77) and say that ChromaDB's default would otherwise apply. *Probes.* A script (Python 3.15.0) ran the program itself, with
its own command line and not the one the helper builds, in a scratch home with a scratch palace and a copy of the owner's cached embedding
model, with the helper's own environment less `ANONYMIZED_TELEMETRY`, inside `sandbox-exec` (part of the operating system; it has no version
of its own). Its profiles confine the network and not the file system, so what the program wrote outside the scratch directory was not
checked; the scratch directory was removed at the end. Canaries first: under a profile that allows the loopback address only, a
connection to the documentation address `192.0.2.1` was refused with an error and did not time out; a client that honours the proxy variables was seen by a loopback
listener (`GET http://example.invalid/`); and under a profile that ends the process on any outbound attempt, a loopback connection ended it
with SIGKILL. Then the four commands `init <dir> --yes --no-llm`, `mine <dir>`, `search` and `status`, once under each profile; the whole script was run
twice with the same result, and the output of the second run is the one kept. Under the
loopback-only profile, with the proxy variables for every scheme pointing at the listener: all four exited 0 and the listener saw no
connection. Under the profile that ends the process on any outbound attempt: all four exited 0 and none was ended. **Result.** The source shows the setting off whenever the program opens a ChromaDB
client, and the probes saw no outbound connection by these four commands, on this input, under either profile. The two are separate
findings: the probes ran without the variable and observed connections, not the setting, and the case of a caller who exports the variable
as `True` rests on the source reading alone. **Limits.** "None seen" is not proof that nothing is sent. The proxy listener sees only a client
that honours the proxy variables; the kill profile sees any outbound attempt by any client in the process, but only on the paths that ran,
so an error path, another command, the compiled core on a path not run, or another version is not shown to be silent. `sandbox-exec` is
deprecated by the operating system but was present and worked. **What the helper does about it:** it sets
`ANONYMIZED_TELEMETRY=False` for every run of the program, status, search, init and mine, so the setting does not depend on the program's
own `setdefault` or on a future ChromaDB default; a test pins the value and that a value the caller exported is replaced.

**Filling the palace and a live session (2026-11-05; plan `2026-11-05-mempalace-use-and-independence`, increment F).** On the owner's machine,
`mempalace` 3.11.0, the project at commit `541b462` with the owner's upgrade of that day installed. *First use.* The owner wrote
`.workbench/mempalace.json` with the wing `project-workbench`, ran `wb run mempalace init docs/decisions --yes` once (which left
`mempalace.yaml` and `entities.json` in that directory, three headings of the decision records as "people", an entry in the program's home
registry and a corpus note that says "likely AI dialogue, confidence 0.4, weak signal"; the two files were then removed), and then, in a
terminal, `wb run mempalace mine` with a dry run and `--confirm` for `docs/decisions` (77 files, 966 drawers) and, without `init`, for
`docs/plans` (94 files, 5,749 drawers), into the palace that already held 54 drawers of other wings. A `mine` without `init` was tested
first on scratch data (an empty directory initialised, or no `init` at all: the same palace files, the same search result, nothing written
into the mined directory). *Searches by the author.* With no `--wing`, a search is limited to the project's wing. A probe of eight
questions whose answer record the author knew, each worded as a story and in the words of the decision, found the record in the top five
for 6 and for 7 of the 8; the decision wording moved four records up and none down; the decision on the tracked-pointer rule was missed
in both because many plans quote it. Eight questions written by the author who knew the answers show the size of the wording effect and
not an accuracy rate. A story-worded question also returned plans that describe a design a later decision replaced, so the palace holds
history as well as what is true now. *A live session.* A fresh Claude Code session in the project, with the new policy and the five
drafting skills installed, was given two brainstorming tasks one after the other, neither mentioning memory, the palace or the decisions:
whether the action-review hook should pass removal previews automatically, and what delegated plan approval should do when the plan was
reviewed on a profile the owner does not list. The transcript's shell commands (command text only) were read: 18, all `grep`, `sed`, `cat`
and `ls` over repository files, in pairs (each once without and once with a leading `cd`; the results were not read); none named
`mempalace`; the session loaded the `brainstorm` skill and not `recall-memory`; its replies cite the specs, the decision records and a
skill, and quote nothing as recalled. **Reading.** The rule "once per task and with the topic, before you … brainstorm a design" did not
lead to a search. The same bullet says not to search for what the current files answer, and the files did answer both topics. **What this
shows and does not.** It does not show that the moments rule works, nor that it fails where the files lack the answer: both tasks were
ones the files answer, and the palace holds nothing the files lack, because everything in it for this project was mined from the same
documents. A palace filled only from the project's own documents duplicates what a search over the current files returns, and adds the
staleness of the copy. **Limits.** Two tasks in one session, chosen by the author; the agent's reasons are not visible; the pairs of
commands were not explained. **What would give the palace a use here:** content that is not in the files, such as the reasons behind a
choice that only the conversation holds, the owner's corrections and preferences, and lessons across projects. Filing such content (by an
inbox the owner reviews, or by mining finished sessions with redaction) is deferred work of the plan, and Claude Code keeps a session for
about 30 days (the oldest transcript of this project dates from 29 October).

**Notes the files lack, and four sessions (2026-11-05; plans `2026-11-05-mempalace-use-and-independence` and `2026-11-05-mempalace-search-form`).**
*The notes.* Because a palace filled from the project's documents holds nothing the files lack, the author wrote six short notes from a design
discussion (why the stock MCP servers are not offered to agents, where a hook is registered by its role, why compaction cannot be triggered by the
agent, which Ollama model works for the entity step, command-gate and terminal lessons, and what the owner asked of the knowledge tools),
the owner read and corrected them, and filed them with `wb run mempalace mine` from a folder outside the project, under the project's wing,
without `init` (6 files, 19 drawers; the palace then held 6,788). *Searches by the author.* A question worded as the user would ask it found the
Ollama note at rank 1 and 2 (cosine 0.70) and the MCP note at rank 1 (0.66); a story-worded question about the command-gate note returned older
plans on the same subject and missed it in the top three, and the note's own wording found it at rank 1 (0.67). *The sessions.* Each was a fresh
Claude Code session in the project with the policy and the drafting skills installed; the shell commands (command text only) were read from the
session's transcript. **(2)** Task: whether to run the model-assisted entity step when setting up mempalace on a new project. The agent ran
`wb run mempalace search "<question>"` with no `--`, twice (once with a leading `cd`), was refused with "is not an option of search", said so,
and did not search again; the `recall-memory` skill was not loaded. **(3)** The same task after the refusal was changed to show the form and the
policy line was changed to show it too (plan `2026-11-05-mempalace-search-form`, installed): six shell commands, all reads of repository files,
none a palace search; the agent said it had not searched "because the files answer what the current setup is". **(4)** In the same session
the owner told the agent to use the `recall-memory` skill and search the palace. The agent checked the built-in memory first and found nothing,
ran one search in the form `--results 5 -- "<question>"`, got the Ollama note at rank 1 and the owner-requirements note at ranks 2 and 3 (ranks 4
and 5 were the old module plan, which it ignored), quoted what it relied on as recalled with the source file of each point, said what it had not
checked (the notes are from the same day; it had not re-run `phi4:latest`), and changed its lean from the spec's account alone to include the
trial that the spec did not mention. It also saw the program's warning, printed with every search, that the collection has no recorded embedder
identity (`mempalace palace set-embedder --model <name>` records it) and left it alone. **Reading.** The search, the quoting and the checking
work once the agent searches. The weak link is the decision to search: in session 3 the agent named the clause "not for what the current files answer" as its reason, and
in session 1 it gave none while both of its topics were answered by the files; the notes show that the palace can hold, besides what the files say, the experience that bears on a question the files
answer. The form fix of the plan `2026-11-05-mempalace-search-form` was not exercised: no agent searched without the skill after it. **Limits.**
Four sessions, each on a task the owner gave, the last with a direct instruction to search; the notes are the author's and
about the same project; the agents' reasons are visible only where they said them; one question has a note that answers it, and a second kind of
question (one the notes do not answer) was not tried.

**A fifth session after the rule was changed (2026-11-05; plan `2026-11-05-mempalace-search-despite-files`, criterion 6).** With the policy block, the
`recall-memory` skill and the rendered `AGENTS.md` installed in the new wording ("even if the files seem to answer it: the palace may hold
experience they lack"), a fresh Claude Code session was given the same task as sessions 2 to 4, the entity-step brainstorm, with no mention of memory.
The shell commands (command text only) were read from the transcript: after loading the `brainstorm` skill the first command was
`wb run mempalace search -- "model-assisted entity step when setting up mempalace on a project: decisions, costs, results"` (in the form the block
shows; the same command appears again with a leading `cd`), and only then `grep` and reads of repository files. The `recall-memory` skill was not
loaded: the form came from the block. The search returned the Ollama note at rank 1 (cosine 0.565) and three plans of this module at ranks 2 to 4.
The agent's reply listed what it relied on as "from the palace, recalled and unverified" (gemma4:12b errored and fell back to heuristics, phi4:latest
reclassified 7 and dropped 3), then compared it with the spec's account, said that it had not re-run anything, leaned towards making the step opt-in
instead of the default, and asked the owner one question. **Reading.** The change of wording removed the reason that stopped the search in sessions
1 and 3, and the form shown in the block was enough for the right command. **Limits.** One session, on the same task for which the note was written,
so the topic is the one the palace answers; a drafting task with no relevant note was not tried, where the cost of the search (about 3,000 tokens) buys
nothing; the agent's reasons were not stated; the commands run in pairs (once without and once with a leading `cd`), whose cause was not read.

**A sixth session, on a task the palace has nothing on (2026-11-05; plan `2026-11-05-mempalace-search-despite-files`, the cost of the rule).** The
rule now asks for one search before every drafting task, so the case that matters for its cost is a task with no relevant note. A fresh Claude
Code session in the project was given, with no mention of memory, the brainstorm "how should we back up the shadow store and the palace?"; the
project holds no design for either backup. *Beforehand* the author ran the same kind of search: five hits with cosine 0.34 to 0.43 and BM25 about
2 to 3, against 0.56 to 0.83 and 6 to 13 for the hits that answered a question in the earlier sessions; 5,562 characters of output. *The session.*
The shell commands (command text and the size of each result, not the results) were read from the transcript. After loading the `brainstorm`
skill the first command was `wb run mempalace search -- "backing up the shadow store and the palace"` (in the form the block shows), with a result of
3,587 characters, about 900 tokens at four characters per token; then `grep` and reads over the specs and decisions. The agent's reply said: "I searched
the palace once. Nothing recalled or written says how either store is backed up", described what the files do say (where the shadow store and the
palace live, that no backup design exists) and asked the owner one question; it quoted none of the five weak hits. `/context` after the first reply
showed 22.1k tokens of messages in all, of which the search is about 4%. One command of the session was refused by the command gate because it named
`workbench upgrade` (the case of the note on the gate); the agent went on with other commands. **Reading.** On a miss the rule costs about 900
tokens and the agent treats the result as nothing, as the skill says; the 3,000 tokens the plan assumed was high for a miss. **Limits.** One
session; the measure of the weak hits (cosine below about 0.45, BM25 below about 3) comes from the author's one search and is not a threshold the
helper or the skill uses; the agent's reasons were not stated. **A correction.** Earlier entries say that the commands of a session appear in pairs,
once without and once with a leading `cd`. In this session the two entries of every pair are identical, because the agent wrote the `cd` itself,
which suggests (not confirmed) that the transcript records the agent's call and the harness's version with the working directory prepended, and
that each ran once.

## Governing decisions and references

- Decisions: `2026-10-21-module-code-lives-in-modules`, `2026-10-22-model-calls-go-through-vendor-bridges`
  (the same shape for an external program), `2026-10-19-tracked-pointer-rule`, `2026-10-23-one-owner-per-skill-name`.
- Specifications: `knowledge-tools.md`, `module-boundary.md`, `module-contract.md`, `model-bridge.md`
  (the model for running an external program).
