# Make `wb verify` say it needs a package directory when the target has no package.json

Status: Proposed
Created: 2026-11-06
Candidate: workbench-v1#verify-names-a-package
Specs: installer-interface

## Goal

`wb verify` run with no argument at a repository root, or on any existing directory that has no `package.json`, refuses with a reason that says the directory is not a package and what to give instead. It no longer prints `package '.': package.json: path may not touch git metadata: .git`, which reads as a fault in a package. When the plan is done a test fails if the old text returns for such a directory.

## Scope

- `verify` in `workbench/cli.py`: before the verifier is called, an existing directory in which `package.json` does not exist is refused with the new text, exit 1, on standard error as a `refused:` line.
- The test of that refusal in `tests/test_cli.py`.
- The `verify` entry of `docs/specs/installer-interface.md` (lines 714 to 722): one sentence saying what happens when the directory has no `package.json`.

## Non-goals

- The safe-path rule in `workbench/wbkit/safefs.py` that rejects a `.git` segment. It is deliberate and stays.
- The default target (`.`) of `verify`.
- Any other command's refusal text, and the verifier's (`verify.verify_package`) and loader's (`declarations.load_package`) text. `approve`, `preview` and `install` call the same loader and keep their present messages.
- A directory that has a `package.json` and also a `.git`, a `package.json` that is a link or a directory, and a target that does not exist or is not a directory: they keep the refusals they give now.

## Assumptions and constraints

- The cause is established (read, and reproduced with `wb verify` on 2026-11-06): the loader walks the directory before it looks for `package.json`, and the walk reaches `.git` at a repository root and refuses it. `wb verify packages/workbench` accepts all 13 modules.
- Putting the check in `cli.py`, before `verify.verify_package`, keeps it to `verify`. This is the agent's proposal; if the implementation shows the check belongs in the verifier, the plan stops and asks.
- The wording is the agent's proposal, in the form `<path> has no package.json, so it is not a package directory; give the package directory, as in wb verify <package>`. A message that names a command says `wb` (`installer-interface.md`, the rule near line 46). It names no path of this repository, because the installer is generic.
- "No `package.json`" means `lstat` of `<dir>/package.json` fails with "no such file". Any other result of `lstat` (a file, a link including a dangling one, a directory, another error) leaves the case to the verifier, with its present refusal.
- `workbench/*.py` is the installer that every hook imports. The edit is made in a scratch clone and copied atomically by the owner, as in the earlier plans, and the owner's copy script records the file hashes.
- The installer root is not a shipped package, so there is no release, upgrade or rerender. `workbench/cli.py` and `tests/` are not under `packages/`.

## Completion criteria

1. `wb verify` with no argument at a directory that has no `package.json` (the repository root) prints one `refused:` line that says the directory has no `package.json` and names the form to run (`wb verify <package>`), and exits 1. The text does not contain `git metadata`.
2. `wb verify packages/workbench` and the other accepted and refused cases of the tests are unchanged.
3. A test fails against the present code and passes after the edit, and the other tests of `tests/test_cli.py` and `tests/test_verify.py` pass.
4. The spec's `verify` entry says what the new refusal is, and `wb run code-work check` passes.

## Increments

### Increment A — The refusal for a directory that is not a package

**Outcome:** completion criteria 1 to 4 are true.
**Dependencies:** none.
**Affected areas:** `workbench/cli.py`, `tests/test_cli.py`, `docs/specs/installer-interface.md`.
**Steps:**
1. Write the test first, in a scratch clone: a temporary directory that holds a `.git` directory and no `package.json`, verified with the target `.` and with an explicit path, refuses with exit 1 and a `refused:` line that names `package.json` and contains no `git metadata`; a directory with no `package.json` and no `.git` gives the same line. See it fail with the present text.
2. Add the check to `verify` in `cli.py`: the path is a directory (by `lstat`, no link followed) and `lstat` of its `package.json` fails with "no such file" (any other result falls through). Write the line to standard error and return 1. Leave every other case to the verifier.
3. Add a test that a directory with a `package.json` and a `.git` is not given the new text (it keeps the present refusal), that a dangling `package.json` link and a `package.json` that is a directory are not given the new text, and that a missing path is not given the new text.
4. Edit the `verify` entry of `installer-interface.md`. Search the documents for another description of `verify`'s default target or refusal (`docs/development.md`); report one that disagrees and change it only if it states the old text.
5. Run the verification below and ask the `reviewer` for a read.
**Verification:** `tests/test_cli.py` and `tests/test_verify.py`, run as `python3 -B -m unittest` on those modules; `wb verify packages/workbench` in the live tree after the copy; `wb run code-work check`. Not run: the whole suite (the change is one early return in one command) and the module suites.
**Evidence:** the one local commit, with the trailer `Plan: 2026-11-06-verify-names-a-package#A`.

## Verification for the plan as a whole

The recorded verification of increment A stands. That the refusal reads clearly to a person who runs a bare `wb verify` is for the owner to see.

## Risks and sensitive actions

- `workbench/cli.py` is imported by every hook; a half-written edit would lock every tool. The edit is made in a scratch clone and copied by the owner's script.
- The new check reads one `lstat` of a path the owner or agent gave, and writes nothing. A check that wrongly matched a real package would refuse it; the step 3 test and `wb verify packages/workbench` after the copy cover that.
- No secret, network, subprocess, authorization or write by code is touched. A security review is not suggested.

## Review record

Codex (`gpt-5.6-terra`), plan review, 2 rounds of 3, not converged: one finding is rejected and left for the owner.

- Applied (round 1): the wording now says `wb verify <package>`, because the spec requires a message that names a command to say `wb`; and "no `package.json`" is defined by `lstat` failing with "no such file", so a dangling link falls through to the loader's refusal, with tests for a dangling link and a directory.
- Rejected (round 2): the reviewer asked for a concrete example such as `wb verify packages/workbench` in the message, as the candidate's outcome has it. The candidate says "an example such as", and the installer runs in any project, where a path of this repository would mislead. The wording gives the form only. The owner decides whether the concrete example is wanted.
- Left for the owner: that choice. A third round was not run, because the only open point is the owner's.

## Deferred work

- A clearer refusal for the other commands that load a package (`approve`, `preview`), if the owner finds the same text there.

## Result

Empty until work starts.
