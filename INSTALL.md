# Setting up a clone on a new machine

This page is for the owner who has cloned this repository to a machine that has never run it. It is a **draft**: each step
says whether it was run. Steps marked *run* were run on a fresh clone with a scratch `HOME` (2026-11-15, `HEAD` at `459dde9`).
Steps marked *not run* come from `docs/development.md` and are the ones to test. If one fails, note the step and the message;
the page is corrected from that.

Nothing here installs software. The code is Python 3.11 or later (standard library only) and git. Everything a clone needs
beyond the tracked files is per machine and untracked, and is listed at the end.

## Before you start

- Python 3.11 or later and git.
- Run every `python3 -m workbench ...` command from the clone's root directory, which you trust. A `workbench/` directory
  or a `json.py` in the current directory would run instead of this code.
- The owner-run steps below work only from a terminal. An agent session cannot run them.

## Steps

1. **Clone.** `git clone <url> project-workbench`, then `cd project-workbench`. *Run (a local clone).*

2. **First run.** `python3 -m workbench check`. *Run.*
   It creates the guarded store, `~/.config/project-workbench/` (settings, cache, projects, packages), and the `wb`
   launcher, `~/.config/project-workbench/bin/wb`. The launcher names this clone's directory, so it points at the
   clone you ran it from. On a fresh clone it reports problems, and that is expected:
   - three helpers "not pinned" (`doccheck`, `refcheck`, `remote-runner-check`): pins are per machine, see step 5;
   - `harness: none attached`: see step 4.

3. **Put the launcher on your `PATH`.** Add `~/.config/project-workbench/bin` to `PATH` in your shell profile. *Not run.*
   `wb` then works from any directory of the project. If another `wb` is already on the `PATH`, the check warns.
   Do not run the command line of a second copy of the workbench: each run rewrites the launcher to the copy's path.

4. **Record the baselines, then attach the harness.** Both are owner-run. *Not run; the preview of the second was refused
   until the first is done, which is what this order is for.*
   - `python3 -m workbench preview acknowledge` shows the differences, the pins that would move and a digest. It changes nothing.
   - `python3 -m workbench acknowledge` records the baselines for this machine. It asks for the first 12 characters of the digest.
   - `python3 -m workbench preview attach --harness workbench/claude`, then `python3 -m workbench attach --harness workbench/claude`.
     This renders the per-clone harness files (`.claude/`) and adds them to `.git/info/exclude`. It writes nothing that git tracks.
   The harness is not committed, so a clone always gets it this way.

5. **Pin the helpers.** Owner-run. *Not run.* `acknowledge` moves an installer-made pin whose helper changed, but a fresh machine
   has none. If `python3 -m workbench check` still says a helper is not pinned, pin it:
   `python3 -m workbench pin <project-id> <name> <helper> --root <clone directory> --kit 1`.
   The project id is the name of the directory under `~/.config/project-workbench/projects/`. The helper path for `doccheck` and
   `refcheck` is `.workbench/workbench/groundwork/helper/<name>`. `docs/development.md` ("pin") has the form for the others.

6. **Check.** `python3 -m workbench check` and `python3 -m workbench doctor`. *Run on the fresh clone before steps 3 to 5:
   `check` found 3 problems and `doctor` found none and 1 risk.* After steps 4 and 5, both should report no problems.

7. **Render the permissions, only if you changed the settings.** `python3 -m workbench rerender`, owner-run, terminal only.
   *Not run.* `wb settings` prints the levels in force.

## Things that are per machine and not in git

| What | Where | Needed for |
|---|---|---|
| Guarded store, settings (the permission levels) | `~/.config/project-workbench/` | everything; copy `settings` from your other machine to get the same levels |
| `wb` launcher | `~/.config/project-workbench/bin/wb` | running `wb`; rewritten by the first command run from a clone |
| Review profiles | `~/.config/project-workbench/review-profiles.json` | any review through the review engine or the action-review engine; `doctor` reports it missing; format in `docs/specs/review-profiles.md` |
| Model bridge endpoints | `~/.config/project-workbench/bridge-endpoints.json` | only a bridge that needs an endpoint |
| Acknowledgement baselines and pins | the store, under `projects/<id>/` | `attach`, `upgrade`, and every module helper |
| Harness files | `.claude/` in the clone | the agent's permissions, hooks and skills |
| Todo list | `.workbench/local/todo/` | the owner's list; it is not copied by git |
| Action-review hook files | a directory the owner chooses (this owner uses `~/action-review-shadow`), registered in the user-level Claude settings | the action-review hook and its report; see "The shadow hook" in `docs/specs/action-review.md` |
| `codex` command line | on the `PATH`, signed in | the Codex model bridge (`docs/development.md`, the `ask-codex` section) |
| `mempalace` | an absolute `PATH` entry, installed with `uv` | the memory search of the `mempalace` module, optional |

## Not covered

The action-review hook's first-time setup on a new machine, and the memory palace, have not been run on a second machine.
