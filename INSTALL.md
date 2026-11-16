# Setting up a clone on a new machine

This page is for the owner who has cloned this repository to a machine that has never run it. The code is Python 3.11 or later (standard library only) and git;
nothing is installed. What a clone needs beyond the tracked files is per machine and untracked, and is listed at the end.

**What has been run.** On 2026-11-15 the owner ran steps 1, 2, 4, 5, 6, 7, 8 and 9 by hand at a real terminal on a second machine (Linux, home `/home/<user>`) at commit `2b1d9ee`;
every one passed with the numbers quoted under the steps. Before that, the steps were run on a fresh `git clone` at `7d70877` with a scratch `HOME`, driving the clone's own code in
process with a fake terminal. Step 3 (the `PATH`) was done on the second machine and not observed. On 2026-11-16, after the list of `acknowledge` was changed to summarise review records (step 6), steps 2, 4, 5, 6, 7 and 9 were run again on a fresh
`git clone` at `6fcef2c` with a scratch `HOME`, in process with a fake terminal. The same day the owner ran step 6 again by hand at a real terminal on the second machine at `aca027e` and saw the summary (below). Not run on either: a Mac as the second machine, and the action-review hook and
memory palace set-ups. If a step fails, note the step and the message; this page is corrected from that.

## Before you start

- Python 3.11 or later and git. Check `python3 --version`: the `wb` launcher calls plain `python3`, which is older than 3.11 on some Linux distributions. The clone's path must be
  absolute and hold no single quote, and the store directory must have mode 0700 (the first run makes it so).
- Run every `python3 -m workbench ...` command from the clone's root directory, which you trust. A `workbench/` directory or a `json.py` in the current directory would run
  instead of this code.
- `enroll` works only from a terminal, at every setting. `acknowledge`, `upgrade` and `attach` are owner-run commands that the agent harness denies to an agent; `acknowledge` and
  `upgrade` ask for a typed digest at a terminal, and `attach` has no digest prompt.
- Run the `wb` commands below from the clone's root directory: the target defaults to the current directory and there is no search upward.

## Steps

1. **Clone.** `git clone <url> project-workbench`, then `cd project-workbench`.

2. **First run.** `python3 -m workbench check`. It creates the guarded store, `~/.config/project-workbench/` (the directories `packages`, `cache`, `projects` and `bin`; the
   `settings` file is the owner's and is not created), and the `wb` launcher, `~/.config/project-workbench/bin/wb`, which names this clone's directory. *Run (the launcher file was
   not opened or executed).* On a fresh clone it printed `harness: none attached` (step 8) and reported three problems, which is expected: the helpers `doccheck`, `refcheck` and
   `remote-runner-check` "are not pinned" (pins are per machine, step 7).

3. **Put the launcher on your `PATH`.** Add `~/.config/project-workbench/bin` to `PATH` in your shell profile; `wb` then works from the clone's root directory. Do not run the
   command line of a second copy of the workbench: each run rewrites the launcher to the copy's path. *Not run (a change of your shell profile).*

4. **Preview the enrollment.** `wb preview enroll` is read-only. *Run.* For this repository at `2b1d9ee` it printed 123 lines (at `6fcef2c`, also 123, with 466 unrecorded files, one file and 465 review records): `baselines to record: 73 paths`; a heading "recorded outside
   `.workbench/` on the strength of a module's own declaration of what it writes", with 5 paths (read them: nothing else checks them); `files under .workbench/ that the manifest
   does not record: 461` (one file and 460 review records, which are not baselined here); the first-seen path; and a `digest:` line. Read the list. Seeded files that you have
   edited since the manifest was written (here `AGENTS.md`, `docs/README.md` and four of the `docs/*/README.md` files) are listed as "differs from the manifest (seeded, yours)"; that is
   expected, they are baselined as they are, and only a module-owned file that differs refuses. A refusal names the file or the
   entry that failed and writes nothing.

5. **Enroll.** `wb enroll`, in a terminal. It shows the same list and asks you to type the first 12 characters of the digest; anything else cancels. It reads the clone again, and if
   the digest is the same it writes two entries in the guarded store, the baselines and the first-seen record, and nothing in the project and no pin. *Run, with a fake terminal.*
   It printed `enrolled 73 paths; the project was not touched; no helper is pinned`. The project is now known on this machine; `wb check` still reports the same three problems
   (the unpinned helpers), and `wb doctor` reported no problems and 1 risk.
   If a write fails the message names the entry that remains and says to remove that entry from `projects/<id>/` in the guarded store by hand before running it again.

6. **Acknowledge.** `wb acknowledge`. It lists the files under `.workbench/` that the manifest does not record and records them after you type the digest. This repository tracks hundreds of
   files that its review engine wrote, under `.workbench/workbench/review-engine/`, and each review adds more; those that have exactly the engine's folder and file names are shown as a
   count by kind ("review records added: N files in M directories") and not one by one, and every one of them is still covered by the digest and recorded. Any other unrecorded file is a line of its
   own (here `.workbench/remote-runner.toml`). Run `wb preview acknowledge` first on your machine, and read the lines and the count: the numbers depend on the commit you cloned. It refuses more than 500 other paths; if you
   meet "more than 500", stop and tell the maintainer. *Run, with a fake terminal, at `6fcef2c`:* the preview printed 110 lines (the line of `.workbench/remote-runner.toml` and a summary of 465 review records in 87
   directories), and it acknowledged 466 paths. *Run by hand on the second machine at `2b1d9ee`, before the summary existed:* it listed 461 paths one by one and acknowledged them. *Run by hand at a real terminal on the second
   machine (Linux) at `aca027e` on 2026-11-16, after a `git pull`:* its baselines held the earlier 461, so the list was the 5 review files of one plan, printed as "review records added: 5 files in 1 directory" with
   one line for the kind (`plan: 5 files in 1 directory`); the typed digest was accepted and it acknowledged 5 paths. A run with hundreds of unrecorded records and older baselines has been done only in process with a fake terminal.

7. **Pin the helpers.** `wb preview upgrade --package packages/workbench`, read it, then `wb upgrade --package packages/workbench` and type the digest. *Run.* The preview listed
   14 pins to create and `77 skip, 1 conflict; 0 file writes` (the conflict is `README.md`, which the manifest never recorded, and it is left as it is); the upgrade, with a fake
   terminal, exited 0 and created the pins (it wrote 0 project paths). Whether the shipped approval records cover this repository's own modules on a machine with an empty
   approvals store was exercised only by that run; a module of another package needs `wb approve` first. Afterwards `wb check` reported no problems and `wb doctor` no problems and 1 risk.

8. **Attach the harness.** `wb preview attach --harness workbench/claude --package packages/workbench`, read it, then `wb attach --harness workbench/claude --package packages/workbench`.
   *Run on the second machine:* it wrote 26 files (25 under `.claude/` and `CLAUDE.md`), recorded `.workbench/local/harness.json`, added `CLAUDE.md` and `.claude/` to
   `.git/info/exclude`, and warned that `.claude/settings.local.json` changes what the agent may do; restart the Claude session to load it. It renders the per-clone harness files, records the
   rendering in the guarded store, writes the local manifest `.workbench/local/harness.json` and adds the files to `.git/info/exclude`; it is meant to write nothing that git
   tracks (not verified by a run).

9. **Check.** `wb check` and `wb doctor`. *Run after step 7, before step 8:* `check` found no problems; `doctor` found no problems and 1 risk, that `review-profiles.json` is
   missing (a review is refused until it exists; copy it from your other machine, see the table below), and three notes about commands whose prompt the project fixes. Run them again after step 8.

## Things that are per machine and not in git

| What | Where | Needed for |
|---|---|---|
| Guarded store, settings (the permission levels) | `~/.config/project-workbench/` | everything; copy `settings` from your other machine to get the same levels, then, after step 8, run `wb rerender` in a terminal |
| `wb` launcher | `~/.config/project-workbench/bin/wb` | running `wb`; written by the first run, and rewritten by the first command run from a clone |
| Baselines, first-seen record, pins, rendering record | the store, under `projects/<id>/` | every command that acts on the project; made by steps 5, 6, 7 and 8 |
| Review profiles | `~/.config/project-workbench/review-profiles.json` | any review through the review engine or the action-review engine; `doctor` reports it missing; format in `docs/specs/review-profiles.md` |
| Model bridge endpoints | `~/.config/project-workbench/bridge-endpoints.json` | only a bridge that needs an endpoint |
| Harness files | `.claude/` and `.workbench/local/harness.json` in the clone | the agent's permissions, hooks and skills; made by step 8 |
| Todo list | `.workbench/local/todo/` | the owner's list; it is not copied by git |
| Action-review hook files | a directory the owner chooses (this owner uses `~/action-review-shadow`), registered in the user-level Claude settings | the action-review hook and its report; see "The shadow hook" in `docs/specs/action-review.md` |
| `codex` command line | on the `PATH`, signed in | the Codex model bridge (`docs/development.md`, the `ask-codex` section) |
| `mempalace` | an absolute `PATH` entry, installed with `uv` | the memory search of the `mempalace` module, optional |

## If a step refuses

- `enroll`: "the project is already known on this machine" means a step already ran; use `acknowledge`. "holds a `pins` entry ... left from an earlier project" means the project's
  folder in the store holds an older entry: remove the folder it names by hand. A module-owned file that "differs from the manifest" means the clone is not what the manifest
  records; do not enroll it until you know why.
- `upgrade`: a refusal about a module not approved on this machine means `wb approve` for that package first.
- Anything about "treated as new here" after step 5 should not happen; if it does, run `wb preview enroll` and read what it says.

## Not covered

The action-review hook's first-time setup on a new machine, and the memory palace, have not been run on a second machine.
