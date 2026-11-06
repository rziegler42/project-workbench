# Development

## Setup

There is nothing to set up and no dependency is installed. The code is Python 3 using
only the standard library, and the repository assumes git, a POSIX shell and `python3`,
as `docs/specs/repository-boundary.md` states.

Minimum Python version: 3.11, the lowest minor version that has every language feature
and standard-library module used so far (`tomllib`, which the `remote-runner` module reads
its project file with, is the newest). The checks have been run only on 3.14; the
minimum is derived from the features used, not from running older interpreters. Raise
it here whenever a later increment uses a newer feature.

## Commands

**Where to run them.** `python3 -m workbench ...` puts the current directory first on Python's
module search path. Run from inside a project you do not trust, a `workbench/` directory or a
`json.py` in that project would run instead of this code, with your privileges, whatever the
command (`approve` included). Run the commands below from a directory you trust, such as this
repository's root, or use the `wb` launcher (see "Pins and the launcher"), which does not have
this weakness. The examples keep the `python3 -m workbench` form because that is how the
checkout is run during development.

Keep this table accurate. Use `not applicable` rather than leaving an
ambiguous blank.

| Purpose | Command |
|---|---|
| Setup | not applicable (standard library only; nothing to install) |
| Run locally | `python3 -m workbench verify [<package> \| --dir <path>] [--select <module> ...] [--no-harness-required]` |
| Preview approving a package or one module: the request and a digest (read-only; verifies the package and records nothing; no `--source`) | `python3 -m workbench preview approve <package> [--module <name>]` |
| Owner-run: approve a package or one module (terminal only; at `wb approve` set to `ask` or `none`, an agent may run it with no terminal, which lets an agent make a package trusted; at `ask` only for a package directory, with the digest `preview approve` printed) | `python3 -m workbench approve (<package> \| --source <url> [--ref <ref>]) [--module <name>] [--digest <32 hex>]` |
| Preview pinning a helper: what would be recorded and replaced, and a digest (read-only) | `python3 -m workbench preview pin <project-id> <name> <helper> --root <project-dir> [--kit N]` |
| Owner-run: pin a helper's content (terminal only; at `wb pin` set to `ask` or `none`, an agent may run it for the project it works in; at `ask` only with the digest `preview pin` printed) | `python3 -m workbench pin <project-id> <name> <helper> --root <project-dir> [--kit N] [--digest <32 hex>]` |
| Preview an install (read-only) | `python3 -m workbench preview install [<target> \| --dir <path>] --package <source> [--ref <ref>] ... --select <module> ...` |
| Owner-run: install a new project (terminal only; with `wb install` set to `none` in the personal settings and the harness attached afterwards, an agent may run it with no terminal and nothing typed, and each such run is logged; at `ask` it runs without a terminal only with the digest `preview install` printed) | `python3 -m workbench install [<target> \| --dir <path>] --package <source> [--ref <ref>] ... --select <module> ... [--digest <32 hex>]` |
| Preview an adoption (read-only) | `python3 -m workbench preview adopt [<target> \| --dir <path>] --package <source> [--ref <ref>] ... --select <module> ...` |
| Owner-run: adopt a repository that has content (terminal only; at `wb adopt` set to `ask` or `none`, as for install) | `python3 -m workbench adopt [<target> \| --dir <path>] --package <source> [--ref <ref>] ... --select <module> ... [--digest <32 hex>]` |
| Preview accepting the changes made to a project: the differences, the pins that would move and a digest (read-only) | `python3 -m workbench preview acknowledge [<target> \| --dir <path>]` |
| Owner-run: accept changes made to a project (terminal only; with the checkpoint `acknowledge-first-tier` set to `ask` or `none`, an agent may run it with no terminal, which lets an agent accept changes to instruction-bearing and executable files; at `ask` only with the digest `preview acknowledge` printed) | `python3 -m workbench acknowledge [<target> \| --dir <path>] [--digest <32 hex>]` |
| Preview clearing the marker of an unfinished write: what would be removed and a digest (read-only) | `python3 -m workbench preview recover [<target> \| --dir <path>]` |
| Owner-run: clear the marker of an unfinished write (terminal only; at `wb recover` set to `ask` or `none`, an agent may run it with no terminal; at `ask` only with the digest `preview recover` printed) | `python3 -m workbench recover [<target> \| --dir <path>] [--digest <32 hex>]` |
| Preview attaching the harness to a clone: the files it would write and a digest (read-only) | `python3 -m workbench preview attach [<target> \| --dir <path>] --harness <package>/<module> [--package <source> [--ref <ref>]] ...` |
| Owner-run: attach the harness to a clone (no terminal test, denied to the agent by the harness; at `wb attach` set to `ask` or `none` the `deny` is not rendered and an unattended run is logged; at `ask` only with the digest `preview attach` printed) | `python3 -m workbench attach [<target> \| --dir <path>] --harness <package>/<module> [--package <source> [--ref <ref>]] ... [--digest <32 hex>]` |
| Preview a re-render of an attached clone's permissions and of its rendered skills, agents and root file that are behind their sources (read-only) | `python3 -m workbench preview rerender [<target> \| --dir <path>] [--package <source> [--ref <ref>]] ...` |
| Preview a release of the shipped approvals: the packages and modules it would record with their hashes, the stale records and a digest (read-only; takes no argument) | `python3 -m workbench preview release-approvals` |
| Owner-run: re-render an attached clone's permissions after changing the settings, and refresh its stale rendered skills, agents and root file (terminal only at every level; the key `wb rerender` offers `block` only) | `python3 -m workbench rerender [<target> \| --dir <path>] [--package <source> [--ref <ref>]] ...` |
| Check a clone (read-only) | `python3 -m workbench check [<target> \| --dir <path>]` |
| Report what the permission settings do not do as they say, and what they allow that is dangerous (read-only) | `python3 -m workbench doctor [<target> \| --dir <path>]` (`wb doctor`; the key `wb doctor`, class `reads`, default `none`; agent-safe). One line per finding, `problem:`, `risk:` or `note:`, with the key and the path and never a value, strictest first, then `doctor found <n> problems and <m> risks`. Exit 0 unless a problem is found; a risk or a note never fails it. It decides and changes nothing in the project (it opens the guarded store as `wb check` does, which may create it and seed the personal settings). A severity lists at most 40 lines of one area, then `and <n> more`. It reports: a setting that reads other than it was set (the problems and notes `wb settings` prints); the personal copy of the compiled floor lacking a stop or naming one the floor does not hold; a `governs` key set looser than its shipped default; every prompt a module declares as a minimum (`asks`); a package tree that differs from its release, with the first place and the commands that clear it; a harness permissions file that differs from the rendering record, was rendered from another table, is missing or cannot be read as a regular file (and a rendering record that is missing for an attached harness, as a risk); a hook that runs `wb` where `wb` does not resolve or is not the guarded store's launcher; an `allow` rule in the harness settings that covers a key the registry does not class as `reads`; an installed skill or agent that says never to run a key offered at `ask` or `none`; and the counts per rule of the gate log (`gate-log` in the guarded store), with a warning when it is full. Not read: a plan approval changed since it was given (`plan-status` says it), and the harness's own global configuration |
| Preview an upgrade (read-only) | `python3 -m workbench preview upgrade [<target> \| --dir <path>] [--package <source> [--ref <ref>]] ...` |
| Owner-run: upgrade a project (terminal only; at `wb upgrade` set to `ask` or `none`, as for install, with the plan for the project it is run from) | `python3 -m workbench upgrade [<target> \| --dir <path>] [--package <source> [--ref <ref>]] ... [--digest <32 hex>]` |
| Preview adding a module (read-only) | `python3 -m workbench preview add [<target> \| --dir <path>] --package <source> [--ref <ref>] ... --select <module> ...` |
| Owner-run: add a module (terminal only; at `wb add` set to `ask` or `none`, as for install) | `python3 -m workbench add [<target> \| --dir <path>] --package <source> [--ref <ref>] ... --select <module> ... [--digest <32 hex>]` |
| Run a pinned helper | `python3 -m workbench launch <project-id> <name> --root <project-dir> -- <args>` (an owner-run argument of a declared command is refused here unless standard input and output are both terminals; `wb run` also lets one through at the level `ask` or `none` that the declaration offers and the owner has set, see `docs/specs/command-permissions.md`) |
| Run a module command | `python3 -m workbench run [--provides <capability>] <command> [<argument> ...]` from anywhere in the project (agent-safe; the command must be installed and pinned; with `--provides` its module must provide the capability; the arguments after the first reach the helper unchanged) |
| Check, list or report the plans | `python3 -m workbench run code-work check\|plans\|report` (the `code-work` module's command; the installer pinned the helper when the install was confirmed) |
| Commit exact paths (local) | `python3 -m workbench run safe-git commit --expected-head <full hash or none> --subject <text> [--body <text>] [--trailer 'Key: value'] [--leave-other-staged] -- <path> ...` (the `safe-git` module's command; needs git; see "The safe-git helper") |
| Preview and remove exact project paths | `python3 -m workbench run safe-git remove [--recursive] -- <path> ...`, then the same with `--confirm` after the owner approves |
| Report what a commit, a removal or a push would act on (read-only) | `python3 -m workbench run safe-git describe commit\|remove <the arguments of the real command>` or `describe push <the arguments that follow git push>` (a push is described locally and never contacts the remote): prints one JSON object (`contract`, `action`, `ok`, `truncated`, `errors`, `facts`), changes nothing, and exits 0 for a refusal of the real command (`ok: false` with an error code); see `docs/specs/safe-git.md`, "Describe" |
| Ask a model one read-only question | `python3 -m workbench run --provides model-bridge ask-codex ask [--model <name>] [--effort low\|medium\|high] [--timeout <seconds>] [--root <path>] [--schema <path>] [--confine]` with the prompt on standard input (the `ask-codex` module's command; needs a `codex` program and a sign-in; `--server <name>` is recognized and refused, because this bridge starts a program; see "The ask-codex bridge") |
| Ask a model on a server one question, check the endpoint file, compare its models, or embed texts | `python3 -m workbench run --provides model-bridge ask-ollama ask [--model <name>] [--context <tokens>] [--effort <level> or --thinking on\|off] [--max-output <tokens>] [--temperature <value>] [--keep-alive <value>] [--timeout <seconds>] [--root <path>] [--schema <path>] [--server <name>] [--confine]` with the prompt on standard input; `python3 -m workbench run ask-ollama check` (reads the endpoint file, contacts no server, prints one line per record and one per model, and a warning for an unauthenticated `http` record away from loopback); `python3 -m workbench run ask-ollama models [--server <name>] [--timeout <seconds>]` (compares the models of the file with the server's list, names only); `python3 -m workbench run --provides text-embedding ask-ollama embed [--model <name>] [--context <tokens>] [--keep-alive <value>] [--timeout <seconds>] [--server <name>]` with `{"texts": [...]}` on standard input (the `ask-ollama` module's command; needs an Ollama server named in `~/.config/project-workbench/bridge-endpoints.json`; see "The ask-ollama bridge") |
| Review one command the harness is about to run (read-only) | `python3 -m workbench run action-review review [--log-row] [--collect] '<the command text>'` (the `action-review` module's command; needs the command's module and a `model-bridge` installed and pinned, and the `action-review` ladder of the owner's `review-profiles.json`; prints one verdict object and exits 0, or exits 1 or 2 (allow only on exit 0 with a whole, valid object); see "The action-review engine") |
| Owner-installed: record what the engine would say about each prompted command (the action-review shadow hook; registered by the owner in the user-level settings, never run by the agent; it prints nothing and always exits 0) | `/usr/bin/env -i <absolute interpreter> -I -B <dir>/shadow_hook.py --wb <absolute path of the wb launcher>` (`--wb` is required; the home directory comes from the account database) with the hook's JSON on standard input, from a directory that holds a copy of `hook/shadow_hook.py` and `hook/shadow_store.py` of the `action-review` module; rows go to `~/.config/project-workbench/action-review/`, with the command, the facts and the reason redacted; see "The shadow hook" in `docs/specs/action-review.md` |
| Owner-run: label the collected commands (terminal only) | `python3 -B <dir>/label.py [--skipped]` with a copy of `tools/label.py` and `hook/shadow_store.py` beside it; records `right`, `wrong` or `skip` in `labels.jsonl` |
| Owner-run: the shadow report (counts only; needs no terminal) | `python3 -B <dir>/report.py` with a copy of `tools/report.py` and `hook/shadow_store.py` beside it; prints the false declines and false approves against the labels and the test set, the bound, and the cutover line |
| Owner-run: run the dangerous cases against a real model (terminal only; from a trusted checkout; sends 3 synthetic prompts to Codex after you type `send 3`) | `python3 -B packages/workbench/action-review/tools/run_testset.py [--codex-dir <absolute path>]`; writes `testset.jsonl`; exit 3 on a false approve |
| Search the owner's memory (agent-safe) | `python3 -m workbench run mempalace status`, and `python3 -m workbench run mempalace search [--wing <name>] [--room <name>] [--results <1-20>] [--since <date>] [--before <date>] -- <query>` (the `mempalace` module's command; needs a `mempalace` program and its cached embedding model; see "The mempalace module") |
| Draft notes (agent-run; plan `2026-11-06-mempalace-notes`) | `python3 -m workbench run mempalace-notes save --title <title> --kind <kind> --body <text\|-> [--wing <name>] [--into <name>] [--new] [--source <text>] [--verify <text>]`, `... list`, `... read <name>`, `... wings`, `... drop <name>`, `... merge <draft> <into>`, `... review [--wing <name>]` (`docs/specs/mempalace-notes.md`; the notes folder is `~/.local/share/project-workbench/mempalace`, one folder per wing, drafts apart from reviewed notes; `list`, `wings` and `review` also archive drafts over 30 days old and finish an interrupted `keep`) |
| Owner-run: move the reviewed drafts into the folder `mine` files (terminal, or at `ask` with the digest of `review`) | `python3 -m workbench run mempalace-notes keep --wing <name> --digest <digest>` (refused unless the digest is that of the wing's drafts as they are now; prints the folder to file with `mine`) |
| Owner-run: build the memory (terminal only) | `python3 -m workbench run mempalace mine <dir> [--confirm] [--wing <name>] [--mode projects\|convos] [--allow-project-root]` (refuses unless standard input and output are terminals; a dry run without `--confirm`; the module has no `init`). At the level `ask` (the key `wb run mempalace mine`, set by the owner), an agent runs `python3 -m workbench run mempalace preview mine <dir> [--wing <name>] [--mode projects\|convos] [--allow-project-root]`, which prints what would be filed and `digest: <digest>`, and then `... mine <dir> --confirm --digest <digest>` with the same other arguments, which needs no terminal and files only if the digest is that of the preview as it is now. `python3 -m workbench run mempalace sync <dir> [--confirm]` prunes the drawers of files that were deleted, moved or are now ignored, from the wing the setting names and the one folder (a dry run without `--confirm`; no other option), and at `ask` it is `preview sync <dir>` and then `sync <dir> --confirm --digest <digest>` |
| Show a project's remote job profiles | `python3 -m workbench run remote-runner profiles` (the `remote-runner` module's command; reads `.workbench/remote-runner.toml`, starts no program; `wb check` also reports a refused file and a leftover `.claude/remote-runner.toml`; see `docs/specs/remote-runner.md`) |
| Fetch a finished job's files into the project | `python3 -m workbench run remote-runner fetch <job> <path> ... [--dest <folder>] [--as <name>]` (1 to 16 paths; refuses a target that exists or goes through a link; never overwrites; fetched files are untrusted). `fetch-overwrite` (same arguments, passes the program's `--force`) is owner-run only and is denied to the agent in the rendered Claude settings |
| Ask for runners, check a job, list its artifacts, submit a declared profile | `python3 -m workbench run remote-runner recommend --profile <name>`, `... status <job> [--expect <40 hex>]`, `... artifacts <job>`, `... submit (--remote <name> \| --best) --profile <name> [--ref <ref> \| --snapshot]` (starts only the external `remote-runner` program, found in an absolute `PATH` entry outside the project; prints one JSON line; submit only on the owner's word; tests use a fake program) |
| Owner-run: approve a plan (terminal only) | `python3 -m workbench approve-plan <plan>` from anywhere in the project: one argument, no option; runs the project's declared approval command and records the plan's path and region hash after the owner types back the first 12 characters. With the key `approve-plan` set to `ask` in the personal settings (`levels`, version 2 or later; attach the harness again afterwards) an agent may run `approve-plan <plan> --digest <32 hex>` with the digest `plan-status <plan> --digest` printed; at `none` it runs with no digest. Exit codes: 0 recorded, 1 refused, 2 usage, 3 recorded but the level log could not take the outcome, 130 interrupted. See `docs/specs/command-permissions.md` |
| Is a plan approved (read-only) | `python3 -m workbench plan-status <plan>`: prints `approved:`, `changed since approval:` or `not approved:` and exits 0 only for the first (agent-safe). `plan-status <plan> --digest` prints what an approval would bind and a line `digest: <32 hex>`, writes nothing and exits 0 |
| Show the checkpoint and cap values that apply (read-only) | `python3 -m workbench settings` from anywhere in the project: no argument, no option; prints `checkpoint <name>: stop\|delegate` and `cap <name>: <n>` lines for what the process module declares, then a `level <key>: <level>` line for every key it knows (the declared checkpoints, the installer's owner-run commands, the agent-safe actions, and `wb run <command> <argument>` for each argument the installed modules declare), then a `key <key>: class=<class> offers=<levels>` line for each of those keys (its danger class, `reads`, `project` or `governs`, and the levels the owner may set it to), then, only when the owner's settings name a risk profile, a `profile: <name>` line and a `profiled <key>: <level>` line for each key the profile moved, then a `translated <key>: <word> read as <level>` line for each checkpoint word it read as a level, then a `settings:` line per problem in the owner's settings (agent-safe). The settings file is seeded at version 3 with an empty `levels` object and no `profile` (`cautious`, `balanced` or `trusting`, version 3 only; `docs/specs/command-permissions.md`, "Named risk profiles"); a version 1 file's `checkpoints` words and a version 2 file are still read |
| Decide one call of a confined agent (read-only; the agent's hook runs it) | `python3 -m workbench agent-gate <harness> <agent>` with the hook's JSON on standard input: no output and exit 0 to allow; one `refused:` line on standard error and exit 2 to refuse, for a write outside the scratch directory or a command no pinned pattern matches ("The agent gate" in `docs/specs/harness-modules.md`); run by hand it is `echo '{...}' \| python3 -m workbench agent-gate <harness> <agent>` from inside a project (agent-safe) |
| Decide one Bash command (read-only; the harness's second hook runs it when a key is set to `ask` or `none`) | `python3 -m workbench gate-command <harness>` with the hook's JSON on standard input: no output and exit 0 to allow; one `refused:` line on standard error and exit 2 to block, for a command that names the relaxed command and is not exactly the simple command the `ask` rule matches, and for every failure (agent-safe; see `docs/specs/command-permissions.md`, "The command gate") |
| Decide one edit (read-only; the harness's hook runs it) | `python3 -m workbench gate <harness>` with the hook's JSON on standard input: no output and exit 0 to allow; one `refused:` line on standard error and exit 2 to refuse, for an edit while a plan under way is not approved; run by hand it is `echo '{...}' \| python3 -m workbench gate <harness>` from inside a project (agent-safe) |
| Owner-run: release time, write the approvals shipped with first-party packages (no terminal test; at `wb release-approvals` set to `none` the `deny` is not rendered and an unattended run is logged; at a verified level `ask` a run without a terminal takes `--digest` from `preview release-approvals` and writes only that plan, and the harness asks for the command; the key offers `block`, `ask` and `none`, defaulting to `block`) | `python3 -m workbench release-approvals [--digest <32 hex>]` |
| Verify the sample package | `python3 -m workbench verify tests/fixtures/sample-package --select sample-harness sample-notes` |
| One focused test file | `python3 -m unittest discover -s tests -p 'test_approvals.py'` (a test module that imports `support` only loads under `discover -s tests`); for a module's own tests, `python3 -B -m unittest discover -s packages/<package>/<module>/tests -t packages/<package>/<module>/tests` from the repository root |
| Full tests | `python3 -B -W error tests/run_all.py` (runs `tests/` and every `packages/*/*/tests/`, each as its own root) |
| Format | not applicable (none configured) |
| Lint or static analysis | not applicable (none configured) |
| Type check | not applicable (none configured) |
| Build | not applicable (none configured) |
| All required checks | `python3 -B -W error tests/run_all.py`; document checks are run by the owner in session, as `docs/README.md` states |

## The safe-git helper

The `code-work` helper reads the project and runs no program. The `safe-git` helper's `commit` and `remove`
change it and run only `git`: found in an absolute `PATH` entry outside the repository, with an environment of its own
(no `GIT_*` variable of the caller; literal pathspecs; no editor, pager, lazy fetch, file system monitor
or automatic maintenance), and only in the argument shapes the helper uses. A repository whose
configuration or hooks select a program is refused, so such a repository is committed to by hand.

- `commit` needs the full hash of HEAD, or `none` on a branch with no commit. A message that names a tool as
  its author is refused unless `.workbench/safe-git.json` says `"attribution": "allow"`.
- The tests that run it need `git` and skip with a reason without it. The expected-HEAD check detects a
  concurrent writer after the fact; it does not prevent one.
- The helper never writes the acknowledgement baselines. After a commit of a baselined path, `acknowledge`
  lists the change.
- Recorded limits are in the plan `2026-10-22-code-work-commit` (Result, increment F): the caller's `HOME`
  and `PATH` are trusted, a `git` in an absolute `PATH` entry outside the repository is run, and the
  look-alike letters of the attribution check are a list that cannot be complete.

## The ask-codex bridge

`ask-codex ask` is a model bridge (`docs/specs/model-bridge.md`): it sends the prompt on standard input to the
Codex command line program, read-only, and prints one JSON object of contract version 2 (a reply with five token
counts, or one of six error classes). It keeps no state and writes nothing in the project.

- **`--confine`** starts the program with its tool features, shell tool and web tool switched off. It is opt-in: the review
  engine needs the program's file access, and a caller that sends captured text always passes it. It is a tripwire plus
  tests and not a boundary; the spec's "Confinement" and "Release check for untrusted text" give what it stops, what remains
  and the check a new release of the program must pass.

- **What a real call needs.** A `codex` program in an absolute `PATH` entry outside the repository, and a sign-in
  that program already has under `HOME` (the bridge handles no credentials and reports `not_signed_in`). Installing
  the module is the owner's consent to send project content to that vendor. The program reads the repository
  itself, so keep secrets out of what it is pointed at.
- **What the tests need.** Neither. They use a fake `codex` program, send nothing, and never sign in or reach a
  network.
- **Time.** The default `--timeout` is 600 seconds. A caller's own time limit should be longer, so the bridge can
  report `timeout` and clean up.
- **A hand run** starts with `codex exec --help`, to check the flags the bridge passes against the installed version. The
  bridge has been run against a real Codex (`codex-cli` 0.163.0, by hand on 2026-10-23, and on 2026-11-01 through an agent
  session's shell tool, with the release check of `--confine`); see `docs/specs/model-bridge.md`, "As built, and its
  limits", for what was and was not tried, and for the places it could not run.
- **The launcher** passes standard input through to the helper, so `wb run` forwards the prompt.

## The ask-ollama bridge

`ask-ollama` is a model bridge to a server (`docs/specs/ask-ollama.md`, `docs/specs/model-bridge.md`): it sends the prompt to an
Ollama server named in the owner's endpoint file and prints one JSON object of contract version 2, as `ask-codex` does. Its `embed`
argument sends a batch of texts to the server's embedding route and prints one object of embedding contract 1 (a vector for each
text), and its `models` argument compares the models of the file with the server's list. It is one command with four arguments:
`ask`, `check`, `embed` and `models`. It keeps no state and writes nothing.

- **The endpoint file.** The owner writes `~/.config/project-workbench/bridge-endpoints.json` (the accepted decisions
  `2026-11-01-endpoint-records-in-the-store`, `2026-11-02-model-configurations-in-endpoint-records`,
  `2026-11-02-model-section-defaults-and-the-embedding-name` and `2026-11-02-temperature-and-keep-alive-in-model-sections`): `format` 2, an optional `default`, and an `endpoints` object of named
  records with `scheme`, `host`, `port`, `location` (`this-machine`, `owner-network` or `vendor-cloud`), `authenticated` (false only),
  the optional `default_model` and `embedding_model`, and a required `models` object with a section for each model that a call may
  use. A section holds `kind` (`chat` or `embedding`), `context` (the largest window the owner declares for the model),
  an optional `default_context` and `bytes_per_token` (2 when absent), and, for a chat model, `effort` or `thinking` (not both) and
  an `output_limit` and a `temperature`, and for a model of either kind a `keep_alive` (how long the server keeps the model loaded
  after a call). Both are JSON strings of an exact grammar, because the file's reader refuses a number with a fraction: a
  `temperature` from `"0"` to `"2"` with at most two decimals (`"0.2"`), a `keep_alive` of `"0"` (unload at once), `"-1"` (keep
  loaded) or a duration (`"30m"`). A file of format 1, or one under the old name `endpoints.json`, is not read. The agent never writes the file.
  `wb run ask-ollama check` reads it and prints one line per record and per model; it contacts no server. `ask-ollama.md`, "The
  endpoint file", has a worked example.
- **Which model.** Only a configured model of the kind the command needs is used: `--model`, else the record's `default_model` (or
  `embedding_model`). A model that is not configured, or is configured for the other kind, is refused before anything is sent. A
  name with a `/` can be given when it is configured.
- **The window and the size of a prompt.** The window of a call is `--context`, else the section's `default_context`, else its
  `context`; a larger `--context` is refused. A prompt whose size in bytes is more than the window times the section's
  `bytes_per_token` is not sent (`context_overflow`, "probably larger"); this is an estimate and a backstop, and a caller sizes its own
  input to the window. Every `ask` also sends `truncate` `false`, so a server that honours it refuses a prompt that the window
  cannot hold (`context_overflow` again, from the server's own count); a server that ignores the field may still cut a prompt without
  an error (`ask-ollama.md`, "Known limits").
- **Defaults and their options.** A chat section's `effort` or `thinking` and `output_limit` are used when a call passes nothing, so a
  module that calls the bridge passes only the model name. `--effort`, `--thinking on|off` and `--max-output <tokens>` replace
  them (the last is refused above the section's `output_limit`). `--temperature <value>` (for `ask`) and `--keep-alive <value>` (for
  `ask` and `embed`) replace a section's `temperature` and `keep_alive`, so a module can run at 0.2 and retry at 0.5 with one
  section. The values are sent as numbers where the server reads numbers (`0` and `-1` for a keep_alive are numbers on the wire,
  a duration a string). These options belong to this bridge and not to the contract's common core; `embed` refuses all but
  `--keep-alive`, and `models` refuses all of them. A temperature of 0 did not make replies differ in the run recorded (one model, one
  prompt, five calls), but equal replies are not guaranteed, so a caller whose cache key is built from the prompt includes the model and the temperature.
- **Server errors and retries.** A status 500, 502 or 503 from the server is `vendor_error` / `bad_exit` with `retryable` true, for
  `ask`, `embed` and `models` (decision `2026-11-02-retryable-server-errors-in-bridges-to-a-server`); every other status stays not
  retryable. The bridge never retries: a caller retries a few times with a wait of tens of seconds and then stops, because a 500
  can be permanent (the figure is a report, and no 5xx was seen in the run that tried to reproduce it). A reply that closes before
  its declared length is `unusable_reply` and not retryable. The unload by a `keep_alive` of `0` may finish a moment after the reply.
- **`models`.** One read of the server's list: `present` (configured and on the server), `missing`, `unconfigured` and a count of names
  set aside; names are compared as exact text, so configure the names as `ollama list` prints them.
- **What a real call needs.** The module installed (`wb add`, run by the owner), the endpoint file under its name, and a server that
  answers. A record that is not loopback and uses `http` sends the prompt in the clear; `check` warns of it. Installing the module
  and writing the record are the owner's consent to send project content to that server.
- **What the tests need.** Neither. They use a fake server on the loopback address, send nothing outside the machine and read no
  real endpoint file.
- **A hand run** starts with `wb run ask-ollama check` and `models`, then a short prompt, before anything larger. The bridge was run
  twice against a real server on 2026-11-02 through an agent session's shell tool on the owner's word (the second from a scratch
  home, with a file of format 2); `ask-ollama.md`, "The run against a real server", says what each run showed and what it did not
  reach; a later check, after the upgrade, ran `ask` through `--provides model-bridge` and `embed` through `--provides
  text-embedding` against the real server; a third run recorded the temperature, the keep_alive and sixteen pairs of a chat and an
  embedding call (no 5xx).
- **Calling it from a module.** A module that runs inside the workbench declares `requires` `model-bridge` (and `text-embedding` for
  vectors, a name that the owner confirmed as vendor-neutral) and calls the bridge through `wbkit.call.run_command` with
  `provides`, as the review engine does. It names no host: the file picks the server and `--server` picks the record.

## The action-review engine

`wb run action-review review` takes the text of one command (`wb run safe-git commit ...` or `wb run safe-git remove ...`)
and prints a verdict object, `approve` or `decline` with the failed checks and a reason (`docs/specs/action-review.md`).
It parses the text under a restricted grammar, asks the owning module's `describe` for the facts, runs fixed code checks,
and only if they all pass asks the model bridge named by the one rung of the `action-review` ladder of the owner's `review-profiles.json` for a verdict. It changes nothing and
writes no file; `--log-row` adds the row of the log as one `log-row:` line on standard error, and `--collect` adds a `facts:` line with the
`describe` object and a last `outcome:` line with the reason the review ended as it did (`docs/specs/action-review.md`, "The collect lines"). Exit 0 is a verdict, 1 a
refusal and 2 a failure. A refusal prints nothing on standard output; a failure prints nothing except when the row or a
flush could not be written after the object was printed, which exits 2 with the object already out. So a hook allows only
on exit 0 together with a whole, valid object.

- **What is built.** The engine for `commit` and `remove`, its rules, rubric, reply schema and pins, and a set of 29
  dangerous cases (`packages/workbench/action-review/tests/dangerous-cases.json`), and the shadow (plan
  `2026-10-29-action-review-shadow-hook`): the `--collect` flag, the hook that records and decides nothing, its store, the labelling
  tool, the report and the test-set runner, all in the rows above. **What is not:** a rule for a push, a hook that decides, the
  cutover and the removal of `claude-workflow`. (The owner's personal setting that was to come is the owner's profile file, which the engine reads.) Nothing the engine says takes effect anywhere, and
  no command is run on its word.
- **What a real call needs.** The `safe-git` module and a model bridge (`ask-codex`) installed and pinned, and an
  `action-review` ladder of one profile in the owner's `review-profiles.json` (`docs/specs/review-profiles.md`) naming the bridge, and a
  working directory inside the project where the command would run.
  The bridge sends the facts, including the diff of a commit, to its vendor; the tests use a fake bridge and send nothing.
- **Owner's steps.** Install the module into this repository (the first test of the pins through the installer):
  `python3 -m workbench preview add --dir <this checkout> --package packages/workbench --select action-review`, then the same
  with `add` instead of `preview add` (run `acknowledge` first if it lists changes). `add` is owner-run in a terminal,
  verifies the module and needs it approved on this machine, and the module's files changed after the shipped approvals
  were written, so `release-approvals` may have to run first; the installed `safe-git` must be current (it must declare
  `describe`), and `upgrade` brings it up to date. The shadow hook is built; the owner's steps to copy it out, register it,
  label, run the test set and read the report are in the spec, "The owner's steps".
- **Changing a shipped data file.** A rule, the rubric or the reply schema needs a new entry in `PINS` in the helper in
  the same change, and `release-approvals` afterwards; `test_actionreview_pins` fails otherwise.
- **The module's tests.** `PYTHONPATH=. python3 -B -W error -m unittest discover -s packages/workbench/action-review/tests -t packages/workbench/action-review/tests` (a few minutes; they run the real `git`, `sh`, `zsh` and `bash`, and the test-set runner's tests build 29 scratch projects against a fake `codex`).
- **Recorded limits** are in the spec, "As built, and its limits".

## The mempalace module

`wb run mempalace status` and `wb run mempalace search` let an agent read the owner's MemPalace; `mine` is the
owner's, and builds it (`docs/specs/mempalace.md`). The module runs the owner's `mempalace` program and holds no memory of
its own.

- **What a real call needs.** A `mempalace` program in an absolute `PATH` entry outside the repository (installed with
  `uv`; the module neither installs nor updates it), and for a search its embedding model in the cache, which only `mine`
  downloads. The tests need neither: they use a fake `mempalace`, send nothing and never start a real one.
- **Building the memory (the owner, from a terminal).** `wb run mempalace mine <dir>` shows what it would file, and
  `mine <dir> --confirm` files it. There is no `init`: `mine` needs none of what the program's `init` writes into the
  folder it scans (`mempalace.yaml`, `entities.json`, and a block appended to the `.gitignore` of a git repository). The first real `mine` downloads about 79 MB (the model, from the
  `chroma-onnx-models` bucket on Amazon S3), and a `mine` may write `hallways.json` beside the palace (`~/.mempalace/hallways.json` for the
  program's own palace) when it finds entity links. Keep the folders you mine, including a notes folder outside the project: the palace
  holds copies and can be rebuilt only from them; a mine again files the changed files and leaves the drawers of deleted ones. At the level
  `ask` the same command can be run from a session: `preview mine <dir>` first, then `mine <dir> --confirm --digest <digest>`; it takes a lock
  beside the palace, so two runs do not overlap, and says if the program left `mempalace.yaml`, `entities.json` or `.gitignore` in the folder.
  `sync <dir>` is a dry run that lists the drawers whose files are gone or ignored; `sync <dir> --confirm` removes them, only from the wing the setting
  names (or the project folder's name), and at `ask` it needs the digest of `preview sync <dir>` too. It cannot name a folder that no longer exists, and what
  it removes returns only by mining the files again.
  The program's embedding runtime keeps a device id and a small database under `~/Library/Application Support/Microsoft/DeveloperTools/.onnxruntime/`
  on macOS. `<dir>` is a directory you name: not the
  project root unless you add `--allow-project-root`, not one that holds or lies inside the palace, and not one in
  which a configuration file the program writes through is a link.
- **Naming a palace and a wing.** With nothing set, the program uses its own default palace and the wing is the project folder's name. A clone may
  name either in `.workbench/local/mempalace.json`, `{"format": 1, "palace": "<absolute path>", "wing": "<name>"}` (at least one of the two; the file is
  per clone and untracked); the helper passes the palace as `--palace` and the wing to `mine` and `sync`.
- **What the helper fixes.** The embedding model (`minilm`), the backend (`chroma`) and git's own settings are fixed by
  the helper, and only `HOME`, `LANG`, `LC_*` and the resolved `PATH` of the caller reach the program. A palace filed with
  another model is not supported through this module.
- **What a search does.** It never changes a stored drawer, but the program rewrites its own index files on every call,
  so do not run a search while a `mine` runs. A low match score means the memory has nothing on the subject: the program
  returns its nearest notes for any query.
- **Evidence and limits.** The run that settled how the program behaves is in `docs/specs/mempalace.md` ("Evidence"); the
  limits, including what no test covers, are in "As built, and its limits". The raw traces of that run were kept untracked,
  in scratch on the machine that made them, and are not part of the repository.
- **A first hand run** has not been made: no live Claude session has used the skill against a real palace.

## The verify command

`verify` reads a package and writes nothing into it or anywhere else except the guarded
store (see below). The package is the positional argument or
`--dir`, defaulting to `.`; the same path given both ways is accepted, two different
paths are a usage error. Without `--select` it checks every module on its own; with it,
it also checks the named modules as one install (`<module>` or `<package>/<module>`),
and prints the install order. A harness module is required in a selection unless
`--no-harness-required` is given.

| Exit code | Meaning |
|---|---|
| 0 | accepted; one line per module with its version and the first twelve characters of the declaration and tree hashes, then warnings |
| 1 | refused; one `refused:` line per problem on stderr, naming the package or module and the rule |
| 2 | usage error |

`release-approvals` uses the same codes: 0 done (or nothing to do), 1 refused, 2 usage; and 4 when a write failed part way, so that
some records were written (they are valid and a rerun is idempotent). A run that is logged (without a terminal, at `ask` or `none`) can
also exit 3, when the records were written but the outcome could not be logged, and 130 when it was interrupted.

## Inert download

`workbench/fetch.py` brings a package into the guarded store's cache as data only, so the
owner can read its declaration before approving anything. `approve --source` and `install` call it. `fetch.fetch(store, source, ref)` returns the new
directory `cache/<id>/package/` (and `cache/<id>/fetch.json` beside it, with the source, ref,
resolved commit and counts) or raises `FetchError` and leaves nothing in the cache.

- **Sources:** an `https://` URL without credentials, an `ssh://` URL, a `file://` URL, or a
  local directory. Other transports (`ext::`, `git://`, plain `http://`), scp-style
  `host:path`, and anything starting with `-` or holding whitespace are refused. A ref is a
  branch, tag or commit name of letters, digits and `._/@+-`, not starting with `-`.
- **Nothing runs and nothing is checked out.** The ref is fetched into a private bare
  repository in a temporary directory outside the store, made with an empty template and with
  `core.hooksPath` pointed at an empty directory. Every `GIT_*` variable is dropped, the
  user's and system git configuration are ignored, prompts are off, only the `file`, `https`
  and `ssh` transports are allowed, incoming objects are checked, and tags and submodules are
  not fetched. Files are read with `git ls-tree` and `git cat-file`; there is no `checkout`,
  `clone` or shell.
- **The whole listing is checked before any content is read.** Every entry must be a regular
  file (a symbolic link or a submodule refuses the download), every path must pass the path
  validator, names that collide ignoring case are refused, and the limits are 2048 files,
  16 MiB per file and 64 MiB in total. Only the owner execute bit is kept.
- **Resource limits.** Every git command runs in its own process group, with its output read
  in chunks and capped, a timeout (300 s for the fetch and for reading the files, 60 s for the
  rest), and a limit on the size of any file it writes (four times the total limit, 256 MiB).
  On a timeout or an excess, git and everything it started are killed. A tree can share
  subtrees, so a tiny repository can list millions of files; the listing is read incrementally
  and git is stopped once it passes what 2048 files allow. The fetch uses `--depth 1` and
  needs git 2.32 or newer (for `GIT_CONFIG_GLOBAL`); fetching a commit id the server does not
  advertise can fail on servers that refuse it. ssh runs with `BatchMode`, and agent and other
  forwarding turned off.
- **The cache holds data and no repository.** Files are written into a staging directory and
  moved into place with one rename; the temporary repository is removed. A failure removes the
  staging directory. A cache directory is never reused, so every fetch makes a new one. Files
  get the default mode (0644 under the usual umask), or 0755 when git recorded the execute bit.
- **Limits:** this does not defend against a flaw in git's own handling of objects or in the
  network transport, and it does not verify who runs the server. An `ssh` source uses your ssh
  configuration and keys; an `https` source may use your credential helpers. A process killed
  outright (`kill -9`) can leave a `workbench-fetch-*` directory in the temporary directory
  or a `.incoming-*` directory in the cache. The code removes only the temporary and staging
  directories it made, with the standard library's `shutil.rmtree`. Tests use local `file://`
  repositories and never the network.

## Approving a package

`python3 -m workbench approve (<package> | --source <url> [--ref <ref>]) [--module <name>]` is how
the owner records an approval. Run it yourself, from your own terminal; the agent's command permissions will deny
it once a harness renders that rule (`claude-harness`). The checks in the command are
friction, not the barrier: a process that allocates its own pseudo-terminal passes the
terminal test, and the 12 characters are not a secret, because the request and `verify` both
print them. The typed text guards against a mistaken approval, and it is not authentication.

1. It refuses unless standard input and standard output are both terminals (tested on the
   file descriptors, not on an environment variable). There is no `--yes` or similar option.
2. It verifies the package and refuses on any problem, recording nothing. A package given as
   a symbolic link is refused.
3. It prints the request (see below), rendered from that one verification, and asks you to
   type the first 12 characters of the tree hash shown: the package's, or with `--module`
   that module's. Anything else cancels and records nothing.
4. Just before writing it verifies the package again and compares every hash with what it
   showed. A package that changed while you were reading is refused.
5. It records a `module` record for each module and then a `package` record, or only the one
   `module` record with `--module`. A harness or process module is approved on its own
   record (`--module`, or as part of the package). It writes only into the guarded store.
   If an approval is already on file the first record is kept, and the command says so.
   Module records are written before the package record, so a package that is approved has
   all its modules approved. If a write fails part way, the earlier records stay (they are
   valid) and the error lists the records written by that run.

The recorded approver is your git identity, `Name <email>`, read from your global git
configuration (and never from the project or an environment variable), with the way the run
was authorized; it is text and grants nothing. Without a global `user.name` and
`user.email` the command refuses and says how to set them. Exit codes: 0 recorded, 1
refused or cancelled, 2 usage error.

**Approving from a source.** `--source` takes an `https://`, `ssh://` or `file://` URL or a
local repository, and `--ref` a branch, tag or commit (default `HEAD`). Give either a package
directory or `--source`, not both. The terminal test runs first, so nothing is downloaded when
it fails. The package is then downloaded inertly into the cache (see "Inert download"),
verified there, and the request, the hash you type and the records all come from that cached
copy; the request names the source, the resolved commit and where the copy is. The first
package approval stores the resolved commit as the pin.

- What is approved is the content, bound by the package tree hash. A ref that later moves to
  different content is a different tree hash and is not approved, and fetching the pinned
  commit again gives the approved content. The same content reached by another commit is the
  same approval: the first record, and its pin, is kept, and the command says so and names
  both commits when they differ.
- A module approved with `--module` has no package record and so no pin.
- A fetch that fails, or a copy that fails verification, records nothing. A copy that you
  decline or that fails stays in the cache so it can be read again; the command prints where.
  Nothing removes cache copies yet.
- A later install fetches the pinned commit and compares the tree hash with the approved one.

## Previewing and installing a project

`python3 -m workbench preview install [<target> | --dir <path>] --package <source> [--ref <ref>] ...
--select <module> ...` shows what an install would do and writes nothing. `python3 -m workbench
install` takes the same arguments and writes the project. `upgrade`, `add` and `acknowledge` are
in "Acknowledging, upgrading and adding" below, and `recover` in "Recovering from an unfinished
write".
The target goes before `--select`, or use `--dir`; `--package` may repeat and a `--ref` binds to
the `--package` before it. Options are not abbreviated.

- **A target** is a missing directory whose parent exists, an empty directory, or a directory
  holding only a real `.git`. A symbolic link, the root, a home directory, the guarded store
  or anything containing it, a directory with other content (`adopt` takes one that has its own
  real `.git`, see "Adopting a repository that has content"), an existing project and a
  directory holding `.workbench/local/incomplete` (an unfinished install or upgrade) are refused, before
  any source is read (`docs/specs/installer-interface.md`, "The target").
- **A source** is a local package directory (it holds `package.json`; a link is refused and a
  `--ref` cannot apply) or a URL. `preview` never fetches: a URL must already be in the cache
  from `approve --source`, and the newest matching copy is used. `install` downloads each URL
  source into the cache, inertly, after the target is accepted and before it prints the plan.
  Every module must be approved on this machine (the gate); neither command records an approval.
- **The preview** lists the target and its state, each module with its hashes, every action
  (directories, files with class, mode, size and hash, the `.git`), the store entries and each pin it will make
  for a declared helper. It uses a fresh seed each time, so the plan it shows differs from one run to the next, and
  it ends with a line saying what is drawn per run, `digest: <32 hex>` and `preview only: nothing was written`. That digest is
  taken over the plan with the seed and the time of the pins fixed, so it is the same from one run to the next and is the one a
  run at the level `ask` takes as `--digest` (`command-permissions.md`, "The installer commands at `ask`").
- **`install`** is owner-run: it refuses unless standard input and output are terminals, unless the owner has set the key `wb install`
  to `ask` or `none` and the rendering holds (`command-permissions.md`, "`install` and `adopt` at `none`", "The installer commands at
  `ask`"): then it runs without a terminal and asks nothing, and logs an attempt and an outcome; at `ask` it needs `--digest` with
  the digest of `preview install` and refuses a missing or stale one. At a terminal it
  prints the same plan with its digest and asks for the first 12 characters of the digest.
  Anything else, an empty answer included, prints `cancelled: nothing was written` and exits 1.
  Input typed ahead is discarded and the answer is read to at most 200 characters. The typed
  text is friction and not authentication; the barrier is the harness's deny rule.
- **After the answer** it checks the target again (same directory, same contents), rebuilds the
  plan from the packages as they are now and refuses a different digest. The bytes written are
  those of the plan that was shown.
- **The write** creates `.workbench/local/incomplete` first, then the `.git` when there is none,
  the directories and files (the manifest last), the store entries (the project record, the baselines
  and, when a module declares a helper, the pins) and last removes the marker. Git is not run: the empty `.git` is made with `mkdir` and a fixed skeleton written
  through held descriptors. Nothing is overwritten, and files get 0644 (0755 when
  executable), directories 0755, narrowed by the umask. It then prints the count of paths and
  `nothing was committed`.
- **The attach** is the last step, after the marker is gone: the plan lists the harness files, the
  `.git/info/exclude` lines and `.workbench/local/harness.json`, and the digest covers them. They
  are written as `wb attach` writes them (exclude lines, files, local manifest last) and the
  unfinished-write record does not list them. If the attach fails, `install` prints `failed:`,
  says the install is complete, names `wb attach --harness <package>/<module>` and exits 3;
  `wb attach` finishes it.
- **A failure after the first write** prints `failed:` with the cause, the paths written and not
  written, and that the marker is left, and names `wb recover`; the directory is then refused as
  an existing project until the marker is cleared. Nothing is cleaned up.

| Exit code | Meaning |
|---|---|
| 0 | done (`install`) or previewed (`preview install`) |
| 1 | refused or cancelled; nothing was written |
| 2 | usage error |
| 3 | stopped after writing; the marker is left |
| 130 | interrupted before anything was written |

### Adopting a repository that has content

`install` refuses a directory that has content, and names `adopt` when that directory has its own
real `.git`. `python3 -m workbench preview adopt` and `python3 -m workbench adopt` take the same
arguments as `preview install` and `install` and add the project around what is there. The
specification is "`adopt`" in `docs/specs/installer-interface.md`.

- **The target** is a directory with its own real `.git` (not a file or a link), at least one
  other entry, and no `.workbench` entry of any kind. A name that differs from `.workbench` only in
  case counts as one. An existing project is refused and `upgrade` is named.
- **Nothing that exists is written.** `adopt` creates only the paths that are missing and never
  opens an existing file for writing. A seeded file that exists is kept and the manifest records it at
  the hash of its own bytes. An existing directory is reused. A file where the plan needs a
  directory, a link, a name that differs only in case or form, and a kept file that is too large,
  not a regular file or hard-linked are conflicts. A conflict refuses the whole command, lists
  every one and writes nothing.
- **Unfilled blocks.** A slot block whose file exists is not filled by `adopt`. The summary counts
  these and names `wb upgrade`, which classifies the kept file **skip** and offers the block as an
  append.
- **No harness.** `adopt` does not attach. Run `wb attach --harness <package>/<module>`
  afterwards. It leaves a harness file with the same bytes as it would write and refuses one with
  other content, naming it. Resolve that first, and keep harness files untracked.
- **The digest** covers the bytes of every kept file, so the owner's answer confirms what was read.
  Nothing is committed.
- **A failure after the first write** is exit 3 as for `install`, and `wb recover` clears the
  marker. It refuses if a kept file was changed, removed or replaced since the adoption started.
- **Afterwards** an adopted project is an existing project: `check`, `acknowledge`, `upgrade` and
  `attach` work as they do on an installed one. `tests/test_adopt_lifecycle.py` runs each on a
  scratch repository.

## Acknowledging, upgrading and adding

Four commands work on an existing project, and each refuses a target that is not one (use
`install` for a new one).

```
python3 -m workbench acknowledge [<target> | --dir <path>]                    (owner-run)
python3 -m workbench preview upgrade [<target> | --dir <path>] [--package <source> [--ref <ref>]] ...
python3 -m workbench upgrade         <the same arguments>                     (owner-run)
python3 -m workbench preview add [<target> | --dir <path>] --package <source> [--ref <ref>] ...
                                 --select <module> ...
python3 -m workbench add             <the same arguments>                     (owner-run)
```

- **Before any of them acts.** The project must be known on this machine: the guarded store holds
  `projects/<id>/baselines` and a `seen` record at this resolved path. A copied or moved project is
  treated as new and refused. The manifest, every file under `.workbench/` outside `local/` (a
  file added or removed counts) and every file the command would write into must equal the
  baselines; any difference is refused, naming the paths, and the owner runs `acknowledge`. A
  project written by a higher workbench version than the running one is refused.
- **Packages.** Nothing is fetched. Each package the manifest records comes from `--package` when
  given, else from the newest cached download of its recorded source and ref (filled by `approve
  --source`); a package recorded as `local:<name>` must be given with `--package <directory>`.
  Every installed module is verified again and must be approved on this machine, even one whose
  files do not change; the harness-required rule is off, because the manifest names no harness. A module
  the package no longer declares is left in place.
- **The preview** classifies every path as `create`, `append`, `replace`, `skip` or `conflict`
  and shows each module with its declaration change, the directories and file writes with hashes,
  the store write, and `git: not run; nothing is committed`. A module-owned file is replaced only
  if it still equals what was installed; an edited, removed or retagged one is a conflict and is
  left alone. A seeded file's own text is never changed; only the blocks in the plan are written
  into it. A slot block is replaced only if its text is as
  installed, appended with its marker where the slot marker is missing, and skipped as "slot gone"
  where the owner removed the markers. Nothing is ever deleted. A preview ends `preview only:
  nothing was written`, or `nothing to change`.
- **`upgrade`** (owner-run) refuses unless standard input and output are terminals, prints the
  same plan with its digest and asks for the first 12 characters. It then re-reads the project
  and the packages, rebuilds the plan and refuses a different digest. It writes
  `.workbench/local/incomplete`, the new directories, the created files, the replaced files (each
  a hash-checked whole-file replace that keeps the original's narrower mode, never setuid, and
  0755 only for an executable), the manifest, the store's baselines and pins, reads every written file
  back against the plan, and last removes the marker. It ends with the count of paths written, the
  conflicts and notes left as they are, and `nothing was committed; committing the result as one
  change makes it revertable`. Git is not run and no clean-tree check is made.
- **`add`** is the same pipeline with the modules named by `--select` added to those the project
  has. A selected module must be new (`<module>` or `<package>/<module>`; a harness cannot be
  added), the installed ones are verified and approved with it, and counts, conflicts,
  requirements, slot owners and order are checked together. It writes only new files, new blocks
  and the manifest: a change to an installed module, a replaced file, or a package given from
  another source, ref or commit than the recorded one is refused and `upgrade` is named.
- **`acknowledge`** (owner-run) lists every difference (path, kind, baseline hash, current hash)
  for the manifest, every file under `.workbench/` outside `local/`, and every other path with a
  baseline, with a summary of the manifest (packages, sources, refs, commits, module hashes and
  every file entry) and every pin it will move (an installer-made pin whose helper changed; a pin
  typed with `pin` is not moved). It asks for the first 12 characters of the digest, re-reads, and replaces
  the baselines of exactly the listed paths in one atomic store write and then moves the pins. It writes nothing in the
  project. A link, a directory or another non-regular file where a file is expected, and a name
  under `.workbench/` that fails the path rules (a control character, bytes that are not UTF-8,
  a colon or a backslash), cannot be acknowledged: it is listed with its reason and nothing is
  written, and `upgrade` and `add` refuse with it listed. More than 500 differences are refused.
  With none it prints `nothing to acknowledge`.
- **Failure.** A failure after the marker was made prints `failed:` with the cause, the paths
  written and not written, and a hint naming `wb recover`, leaves the marker, and exits 3; the
  directory is then not an existing project until the marker is cleared. `wb recover` clears it
  only where that is safe; there is no automatic repair of files: put them back from version
  control or a copy (see "Recovering from an unfinished write"). A marker that cannot be made
  exits 1 with nothing written. An interrupt after writing began exits 3.

| Exit code | Meaning |
|---|---|
| 0 | done, previewed, or nothing to change or acknowledge |
| 1 | refused or cancelled; nothing was written |
| 2 | usage error |
| 3 | stopped after writing began; the marker is left |
| 130 | interrupted before anything was written |

**Limits.** A file with more than one hard link is refused, since its other name may be outside the
project. The check of a file's hash and the rename that replaces it are not one operation, so
a write by another process in between is lost; the typed text is friction, not authentication,
and the harness's deny rule is the barrier. The comparison of a project with its baselines reads
at most 256 MiB of file content in one scan (each file at most 16 MiB, 20000 entries under
`.workbench/`, 32 levels deep) and refuses beyond it; `acknowledge` compares every baselined file
in the project, not only those under `.workbench/`, and `upgrade` scans twice, each time with a
fresh budget. After a reinstall at the same path, a manifest carrying an old seed
from git history is checked against the baselines kept for that seed, and `acknowledge` shows
the project id but does not highlight a change in it. A manifest source with
credentials stripped may not match the cache record.

`wb check` reads a clone and writes nothing. It reports harness files (drift against the local
manifest, files of another harness, strays) and what git tracks: tracked files that look like harness
output or scratch (`CLAUDE.md`, `.claude/`, `.debug/`, `.workbench/local/` and the files of the other
harnesses it knows), tracked Markdown documents that link or import (`[x](path)`, `[x]: path`, `href`,
`src`, `@path`) into content git does not track or out of the project (code, plain mentions of a path
and source files are ignored), committed files that differ from the manifest beyond their owner class (the working tree is compared)
(a module-owned file or a slot block that was edited; a seeded file may change), and whether the
manifest is tracked. The checks that belong to a document module are that module's own. For `groundwork`
they are `packages/workbench/groundwork/helper/doccheck` (the form of `docs/specs`, `docs/roadmaps` and
`docs/decisions`: names, status, successor, candidate IDs) and `helper/refcheck` (the reference index
`docs/references/index.json` against the tracked files), run as below. The installer pinned each when the install was confirmed; `python3 -m workbench pin <project-id> <doccheck|refcheck> .workbench/workbench/groundwork/helper/<name> --root <dir> --kit 1` replaces a pin by hand.
After its own findings it runs the checks that installed modules declare (`checks` in `module.json`): each is a
pinned kit helper started from the project root, and its `problem:` and `warning:` lines are printed under the
module's name (`problem: <package>/<module>: <text>`). A module problem counts in "check found N problems" and
makes the exit code 1; a warning does not. A check that is not pinned, was pinned for another helper or kit, or
whose bytes changed is a problem and does not run; the other checks still run. A project whose modules declare
no checks prints what it printed before.
It never runs git: a repository can name programs git would run (a
filesystem monitor, a filter, an included file), so the paths come from `.git/index` itself, version
2, 3 or 4 with SHA-1 or SHA-256 names, in at most 16 MiB and 1,000,000 entries, paths of at most 4,096 bytes and 64 MiB in all. "Tracked" means in
the index, so a staged file counts. A split or sparse index is reported as a problem. At most 5,000
documents, 8 MiB of them and 5,000 existing-path lookups are examined, and a larger project is
reported as not fully looked at. The document checks add their own bounds: 2,000 documents, 4 MiB in
all, 1 MiB per document, 200 findings and 128 MiB of references (`groundwork.md`, "As built, and
its limits").

## Recovering from an unfinished write

`install`, `upgrade` and `add` write `.workbench/local/incomplete` first and remove it last. The
marker holds a record of the plan being written (`workbench/unfinished.py`, format 1): the
command, the project id when known, the workbench version, each file write (path, operation, the
hash before, the hash after), each directory the plan creates, the files of the `.git` skeleton
with their hashes, and each guarded-store write with its hash. It is canonical JSON, at most
1 MiB and 10000 entries, with the manifest's path rules; no path may be at or under
`.workbench/local`. The record is untrusted text and grants nothing: a marker that is empty (made
by an earlier version), truncated, oversized or malformed reads as "no record", and `recover` then
cannot help. A plan too large to record (about 5000 files) is refused before anything is written.

```
python3 -m workbench recover [<target> | --dir <path>]                    (owner-run)
```

- **Every other command that meets a marker** (`preview`, `install`, `upgrade`, `add`,
  `acknowledge`) refuses with the same report, and `recover` shows it without the last line: the
  command and version recorded, how many recorded files and store entries hold the state before
  the plan, the state after it, or something else, the paths to deal with, and that `wb
  recover` is the way forward. Reading is
  bounded (256 MiB in all), never follows a link and reads regular files only.
- **`recover`** is owner-run and terminal-only. It examines the project, shows the report and
  what it would remove, and asks for the first 12 characters of the digest, which covers the
  marker's bytes, the examination, the removals and the target's identity. After the answer it
  examines again and refuses a different digest.
- **It clears the marker only in these states** and refuses every other with the paths to deal
  with, writing nothing:
  - recorded files all in the state before the plan and the store entries all absent or old
    (nothing happened, or the owner put the files back): the marker goes, and so does each
    recorded directory that is empty, deepest first, with `rmdir` only; a failed `install` then
    leaves the target as it was and `install` can be run again;
  - files all in the state after the plan and every store entry written: only the marker was
    left, and it goes;
  - `upgrade` and `add` only, files after and no store entry written: the marker goes and
    `acknowledge` then lists exactly the written paths for the owner to accept;
  - `upgrade` and `add` only, files after and the store half written, each entry either old or new
    (the baselines are written first, then the pins): the marker goes and the report says which entry
    is still old. If the baselines, `acknowledge` lists the written paths; if the pins, the launcher
    refuses each replaced helper until the owner runs `pin` for it. An entry that holds anything else
    is refused. An `install` in
    either state, or with a partial store, is refused with the advice to put the project back,
    run `recover` again and install again. The workbench does not repair a store.
- **It never** writes or restores a file, removes a file other than the marker, removes a
  directory that holds anything, touches the store, or removes the target directory. More than
  500 removals, or `.workbench/local` holding more than the marker, are refused. The typed text
  is friction, not authentication.
- **Known limits.** The marker is unlinked by name a moment after the second examination, so a
  marker swapped in that window is removed instead of the one shown. A forged record can make
  `recover` remove empty directories the owner made, since `rmdir` refuses only non-empty ones;
  they are listed before the digest is typed.

| Exit code | Meaning |
|---|---|
| 0 | the marker was cleared, or there is none |
| 1 | refused or cancelled; nothing was removed |
| 2 | usage error |
| 3 | a removal failed or was interrupted after removal began; the message says whether the marker is still there |
| 130 | interrupted at the prompt |

## The distribution layout

The repository root is the distribution: `workbench/` (the code and `shipped_approvals/`),
`base/` (the content every project gets before any module: `AGENTS.md`, `README.md` and
`docs/README.md`; the first and last hold a slot marker), the first-party packages, `docs/` and `tests/`. `base/` is trusted as
the code is and has no approval record; its tree hash is recorded in each project's manifest.

## Pins and the launcher

A helper such as the commit helper is a file of a module, so a pulled edit could replace it. It is
pinned, by the installer in the step where the owner confirms the install, add or upgrade by digest for a
declared command or check, or by the owner with `pin` for any other. The launcher runs it only while its
bytes still match the pin
(`workbench/pins.py`, `workbench/launch.py`). A pull that edits the helper changes its hash, so
it is not run until the owner acknowledges the change (`wb acknowledge` moves a pin the installer made) or pins it again.

- **Pin** (owner-run, from a terminal, like `approve`):
  `python3 -m workbench pin <project-id> <name> <helper> --root <project-dir> [--kit N]`. `--kit N`
  records that the helper runs through the kit runner with kit API number N; without it the helper
  runs directly. A module command is refused unless this equals what its declaration says. The project id
  is 64 lowercase hex digits (the hash of the project's seed, once projects exist). The helper
  must be a regular file inside the root; a symbolic link, a directory, a FIFO or a path
  outside the root is refused. The command shows the path, size, SHA-256 and the start of the
  file, says if it replaces an earlier pin, and records nothing unless you type the first 12
  characters of the SHA-256. It checks again just before writing. The pin is stored in the
  guarded store as `projects/<id>/pins`, with the path relative to the root so that clones at
  different locations share it.
- **Launch**: `python3 -m workbench launch <project-id> <name> --root <project-dir> -- <args>`.
  The helper's location comes only from the pin; the caller cannot name another file. The
  launcher reads `<root>/<pinned path>` through the safe reader (a real root directory, no
  symbolic link on the way, a regular file), hashes it, and compares it with the pin. If they
  match it writes those exact bytes to a new file in a private directory under `bin/run/` in
  the store (mode 0700) and runs that file with the arguments, with no shell, so a file
  swapped after the check changes nothing. The copy is removed afterwards. The helper's own
  exit code is returned. Anything that stops it from running exits 1 with a line starting
  `refused:` on standard error: no pin, a damaged pins file, a missing or unreadable helper, a
  symbolic link, or a hash that no longer matches (the message says to review it and pin it
  again).
- **Limits.** This is a pin check and not a sandbox: the helper runs with your privileges and
  environment, and the copy lives in a store directory that your own account can write. A
  helper should be a single self-contained file, because it runs from a copy in a different
  directory. A helper that exits 1 looks the same as a refusal by exit code alone, and one that exits 2 looks like a
  usage error; the `refused:` line on standard error tells them apart.
- **Example.** With a helper at `tools/commit.sh` in a project:
  `python3 -m workbench pin <id> commit tools/commit.sh --root .` (type the 12 characters),
  then `python3 -m workbench launch <id> commit --root . -- -m "message"` runs it. After
  someone edits `tools/commit.sh`, the same `launch` exits 1 with
  `refused: the helper commit has changed since it was pinned`, until you pin it again.
- **The `wb` launcher.** Every command makes sure the store has `bin/wb`, a short script that
  runs this workbench under `python3 -I` (isolated mode) with the workbench directory added by
  hand. It is fixed text apart from that one path, and is rewritten if the path changes.
  Isolated mode keeps the current directory and `PYTHONPATH` off the module search path, so a
  project that ships its own `workbench` package, a `json.py` or a `sitecustomize.py` cannot
  run in place of the real ones. The name `wb` is kept as
  the specs state it. When the script is written and another command named `wb` is already on
  your `PATH`, a warning names it; the warning never stops a command. Nothing is added to your
  `PATH`: to use it, put `~/.config/project-workbench/bin` there yourself. How the workbench
  itself is installed is not decided yet, so the script assumes the workbench is a directory on
  this machine.

## First-party packages and shipped approvals

The workbench distribution is the repository root: code in `workbench/`, first-party
packages in `packages/` (`workbench`, whose module `claude` is the Claude harness), and the approvals made for them in
`workbench/shipped_approvals/`. Shipping with the workbench counts as explicit approval, and
the records are read from the installed workbench, never copied into the guarded store.

- A package is first-party only if its directory is directly inside `packages/` (and is not
  a symbolic link), its declared name equals the directory name, and a shipped package
  record for that name matches the package's current declaration and tree hashes. Otherwise
  it is third-party. `verify` sets the verifier's `first_party` flag from this, so only an
  unchanged released package may provide an unprefixed capability name.
- The shipped records are trusted because the distribution is. Anything that can write the
  repository can add a package and run `release-approvals`, and the records it writes count
  as approval, so review what a release changes in `workbench/shipped_approvals/` (its git
  diff) before accepting it. The command does not need a terminal, because releases may run
  unattended. At the level `ask` the digest of `python3 -m workbench preview release-approvals`
  binds the owner's confirmation to the hashes of the release, not to the content of the packages.
- `python3 -m workbench release-approvals` is a release-time command, not one for users of a
  project. It verifies every package under `packages/` as first-party, writes nothing if
  any module fails verification (exit 1; a write that fails part way can leave the earlier
  records of that run, which are valid and a rerun is idempotent), and otherwise writes one record per module and per package with
  a fixed approver (`workbench-release`) and time, so a second run changes nothing. Records
  of an earlier release are left in place and reported with a warning, because deletion is
  not provided; remove them by hand (`python3 -m workbench preview release-approvals` lists them first, and says when the shipped
  tree cannot be listed). With no packages it prints `no first-party packages` and exits 0.
- A first-party package changed since release has no shipped approval for its new hashes,
  so its modules are checked against the guarded store like any other package.

## Permission levels

`docs/specs/command-permissions.md` is the specification. In practice:

- **Turning a level on.** Back up `~/.config/project-workbench/settings`, change `"version"` to 2 and add `"levels": {"approve-plan": "ask"}`
  (or `"none"`). Nothing changes in a project until its harness is rendered again. A new clone is rendered by `wb attach`, which
  writes the rendering record and the harness files. A clone that already records a harness is rendered again by `wb rerender`:
  edit the settings, run `python3 -m workbench preview rerender --package <source>` and read the plan (the keys that move, the
  `allow` rules it keeps, the entries it removes, the shared settings file if it changed), then run `python3 -m workbench rerender
  --package <source>` from your terminal and type the first 12 characters of the digest. `wb check` says `rendering: out of date`
  and names the command when the settings and the rendering differ. `wb rerender` needs a terminal at every level (its key offers
  `block` only), and a clone attached before the command existed lacks its `deny` until it is re-rendered once. The same command
  brings the rendered skills, agents and root file up to date with the installed modules (`docs/specs/harness-refresh.md`). After a
  package changes, the sequence is `wb upgrade` (it prints a pointer line when it wrote a harness item), `wb preview rerender
  --package <source>` (each rendered file is current, stale, new, missing, applied or orphaned; an edited or linked file refuses
  the whole run, and you move an edited file aside to have it recreated), then `wb rerender --package <source>` from your
  terminal. `wb check` does not report a stale rendered file. `wb settings` prints a `level <key>:
  <level>` line for every key. The default is `block`, except for an agent-safe action and a declared module argument that is not owner-run, which default to `none`. A `block` set on an agent-safe action or a declared module argument is rendered as a `deny` at the next attach or re-render; at its default `none` nothing is rendered. A damaged settings file blocks every owner-run key and leaves the agent-safe ones at `none`, so `wb settings` and `wb check` still run to report it; an explicit `block` on an agent-safe key is not honored until the file is repaired. The checkpoint `accept-decision` offers `block` (the default), `ask` and `none`: at `ask`, `wb settings` prints `level accept-decision: ask` and the `draft-decision` skill has the agent show the preview of `wb run groundwork preview` and run `wb run groundwork accept` with its digest, which the owner confirms; at `none` the agent runs `accept` without a digest; otherwise only the owner accepts a decision (`AGENTS.md`). Not every key offers `none`: the owner-run arguments of module commands (except the review engine's `extend`, `reset`, `archive`, `amend` and `prune`, which offer `ask` and `none`), `push-shared-branch`, `submit-remote-job`, `fetch-remote-output`, `change-direction` and `wb rerender` offer `block` only (`docs/specs/command-permissions.md`, "Not built" and "Re-rendering an attached clone").
- **What it asks of the agent.** The agent runs `wb plan-status <plan> --digest`, shows you the preview, and runs
  `wb approve-plan <plan> --digest <digest>` as one simple command on its own; the harness then prompts you. A command that wraps or
  rewrites it (`bash -c`, `env`, a quote splice, an escape, an expansion) is blocked by `wb gate-command`, and a command that only
  names `approve-plan` (a `grep`, a commit message) is blocked too while the level is relaxed; run those yourself.
  A command key that is an ordinary word (`wb install`, `wb add`) is read in command position: only a command that names a
  launcher (`wb`, the store's `bin/wb`, `python3 -m workbench`) and the word, in either order, is blocked, so `npm install`, `git add`
  and a commit message that holds the word are not, and `wb preview <action>` is allowed. A compound command that holds both
  (`npm install && wb check`) is blocked: run it as two calls. A literal `wb run <name> <arguments>` (plain tokens and single-quoted
  strings) is not read for these words, so `wb run safe-git commit --subject 'Add tests' -- tests/test_add.py` passes; write a commit
  subject in single quotes. `wb approve-plan` is not taken for `wb approve`.
- **What it cannot stop.** A script or program that makes the call, a word built from variables or encodings, and a shell that writes
  the guarded store: see "Limits" in the spec. Leave a key at `block` if you do not accept them.
- **When Bash calls are blocked.** While a key is relaxed, `wb gate-command` runs on every Bash call. If the store, the settings file
  or the installed modules cannot be read, it blocks every call, `wb check` included. Fix it from your own terminal. "Yes, and don't
  ask again" in the prompt writes an allow rule into `.claude/settings.local.json`; the changed file makes the keys read `block`
  until you run `wb rerender`, which keeps the allow rule and lists it in the plan.
- **The level log.** `~/.config/project-workbench/level-log` is plain text, one line per attempt and one per outcome. It is not
  pruned; it holds about 4 MiB, and a full log refuses runs above `block`, so rotate it by hand.
- **Where the level code lives.** The level log's line format and its append, and the rule that a verified level of `none` runs
  without a terminal, are in the kit (`workbench/wbkit/levels.py`); `workbench/levellog.py` reads the log and calls the kit to write
  it, and `workbench/levelrun.py` adds the check of the rendering record for an owner-run command (`approve-plan` and the other
  owner-run commands use it). Tests: `tests/test_wbkit_levels.py`,
  `tests/test_levelrun.py`.
- **After editing a first-party module.** Any change under `packages/workbench/<module>/`, its `tests/` included, changes the
  module's hash and stales its shipped approvals. The project's own edit gate then refuses file edits until the owner runs
  `python3 -m workbench release-approvals` and removes the obsolete records it warns about with
  `python3 -m workbench run safe-git remove --recursive -- <paths>`.

## The approval request

`workbench/request.py` builds the text the owner reads before approving. No command prints
it yet; the `approve` command will. For a module it shows, in this order: a `HIGH RISK` line
when it applies, the identity (package, name, version, type, description, source), both
hashes in full, a size line with the count of each kind of entry, and then the details, one
section each: what it provides, requires (soft ones marked) and blocks (core capabilities
marked), the slots it owns and fills, the paths it writes into the project, every item it
ships (`[executable]` when a file under it has the owner execute bit, otherwise
`[code-bearing]`), any other executable file in the module (for example under `harness/` or
`files/`), the helpers it expects, and a harness module's layout, one line per leaf.

- A `harness` or `process` module, or one that blocks a core capability (an unprefixed name),
  is flagged `HIGH RISK`. A package request lists every module and which need an explicit
  approval of their own.
- Nothing a package controls is shortened: paths, layout values and lists are shown in full.
  A list of more than six entries gets a count and one line per entry, and the hashes and
  counts come before any list, so a long list cannot push them out of sight.
- Every package-supplied string is shown as ASCII. A non-ASCII character appears as an
  escape such as `\u0443`, so a lookalike letter cannot pass for a Latin one, and control,
  invisible and bidirectional characters become visible escapes.
- The text is built from the verification result: the parsed module, its hashes, and the
  files with the execute bit, all from the one tree walk that was hashed
  (`Verified.module`, `Verified.executable`). Nothing is read again, so what is shown cannot
  differ from what is recorded because a file changed between two reads.

`workbench/wbkit/display.py` (part of the kit) has the two cleaners. `clean` (used for the command's own messages)
keeps ordinary letters in any script and escapes control, invisible, combining, format,
separator and filler characters. `ascii_text` (used for the request) escapes everything
outside printable ASCII.

## The approval gate

`workbench/gate.py` answers whether a verified selection is fully approved on this machine.
`preview install` and `install` call it first, and it only reads. It takes the result of `verify_packages` for a selection and reports each
module in install order:

- A module is approved by a `module` record for its `<package>/<module>`, declaration hash
  and tree hash, or, for a plain module only, by a `package` record that matches the
  package's current hashes and lists the module with exactly its two hashes. A `harness` or
  `process` module always needs a record of its own.
- A first-party package is looked up in the shipped approvals first, then the guarded
  store; any other package only in the store. Each result says which supplied it.
- Only a module of type exactly `module` may use a package record. Any other type needs a
  record of its own.
- It fails closed: a refused verification, an empty selection, a malformed result, or a
  module the result does not describe is not approved, and a refused result looks nothing up.

Limits: the gate approves what `verify` hashed, not what an installer reads later, so an
installer must write from the exact bytes that were verified, or verify and gate again from
the same snapshot just before writing. The gate also takes each package's `first_party` flag
as given; the installer must set it from `firstparty.is_first_party`. A shipped record
matches only the exact subject and hashes it was made for, so a wrong claim gains nothing.

`verify`'s result now carries each module's type and, per package, the declaration hash and
whole-package tree hash (`Result.packages`), which the gate needs.

## The guarded store

Every command first makes sure the guarded store, `~/.config/project-workbench/`, exists.
It creates the directory and `packages/`, `cache/`, `projects/` and `bin/` with mode
`0700` when they are missing, and does nothing when they are there. The command line then
seeds the personal settings if they are missing (`Store.ensure` itself only makes the
directories, so settings depend on the store and not the reverse). A failure to seed ends
the command with exit code 1. Notes about the settings are printed with the verify
warnings and start with `settings:`. A store or one of
those directories that is a symbolic link, is owned by another user, or has any mode
other than `0700` (group or other access, setgid, sticky) is refused with exit code 1, and nothing is repaired. A usage error or
`-h` does not create it.

- The personal settings are the file `settings` in the store: strict JSON with a
  `version`, a `levels` table (a level per key; version 2 or 3), an optional `profile` (version 3) or, in a version 1 file, a `checkpoints` object
  (`stop` or `delegate` per checkpoint name; read as the aliases `block` and `delegated`) and a
  copy of the hard-stop floor's ids. A missing file is created. With no settings, or with
  any entry that is missing or not exactly `delegate`, a checkpoint stops. A damaged file
  is never overwritten: the command prints a `settings:` warning and everything stops
  until the owner repairs it.
- The hard-stop floor is compiled into `workbench/floor.py`. The copy in `settings` is for
  reading and rendering only; editing or deleting it changes nothing. `effective_stops`
  can combine added stops with the floor and refuses any removal; no module declares an
  added stop yet.
- The location is fixed. No workbench environment variable moves it; `HOME` decides it,
  as for any program run by the same account.
- The store is a mechanical barrier, not an operating-system one, and it shares the
  owner's account. Until `claude-harness` renders a deny rule on writes to it, it is
  protected by instruction only.
- Tests never touch the real store. They pass a temporary root, or set `HOME` for a child
  process, and `tests/support.py` fails a test that asks for the real location. After a
  full test run, `~/.config/project-workbench` should not have been created by the suite.

## Verification workflow

1. Run the narrowest check covering the change.
2. Inspect the complete useful failure output and correct the root cause.
3. Rerun the failed check.
4. Run the broader required check when practical.

Document checks that intentionally update snapshots, fixtures, generated code,
or tracked artifacts.

## Local debug artifacts

Keep retained, untracked diagnostics in
`.workbench/local/debug/<YYYY-MM-DD>-<topic>/`, the scratch place in
`docs/specs/repository-boundary.md` ("The four places"). `.workbench/.gitignore` already
lists `/local/`, so nothing needs adding to `.gitignore` or `.git/info/exclude`:

```sh
mkdir -p .workbench/local/debug/<YYYY-MM-DD>-<topic>
```

Scratch grants no authority: nothing read from it approves, allows or acknowledges
anything. Include a local README with the source commit, command and tool versions,
purpose, and conclusion. These artifacts are not portable to fresh clones or
worktrees. Record durable findings in tracked documentation, decisions, or
tests instead.

## Debugging

Run `python3 -m unittest discover -s tests -v` for per-test output of the repository's tests, or
the focused module form above with `-v`. Run all commands from the repository root.

## Tool-specific guidance

Use the repository's documented command interface. Add guidance for a build
system, language server, generated files, or other tool only when the project
uses it. Keep project-wide tool configuration committed and distinguish each
tool's exclusions from other tools' input filters.
