"""The rules the workbench itself puts into every harness that provides ``permissions``.

Two lists are compiled in, like the floor, so no file can shorten them. They are defined once, in the registry
(``levels``, decision ``2026-11-02-one-permission-registry-and-key-model``), and named here for the code that reads them:

* ``OWNER_RUN``: the commands only the owner runs, from a terminal. A harness denies each one in
  both spellings an agent could submit, so an agent cannot install, upgrade, approve or pin.
  ``cli.py`` routes these commands, and a test fails when it routes one that is in neither this
  list nor ``AGENT_SAFE``.
* The owner-run arguments a module declares for its commands (``command_owner_patterns``): not
  compiled in, because they depend on which modules are installed, but built here from the same
  spellings, so an agent cannot run them either.
* ``FLOOR_RULES``: for each hard stop of ``floor.FLOOR``, the ``ask`` rules that make the
  harness stop for the owner. They are a best-effort match on the command text an agent submits,
  not a sandbox (``trust-and-approval.md``). A stop with no entry here fails a test, so adding a
  stop to the floor cannot silently render nothing.

A rule is ``(action, tool, pattern)`` in the neutral vocabulary of ``neutral.py``.
"""

from . import levels

# The compiled lists live in the registry (``levels``), written once; the names stay here for the code and the tests that
# read them as ``rules.OWNER_RUN`` and so on (decision ``2026-11-02-one-permission-registry-and-key-model``).
OWNER_RUN = levels.OWNER_RUN
# Commands an agent may run: they only read, or run a helper that checks its own pin.
AGENT_SAFE = levels.AGENT_SAFE
# The hook entry points, the words that only dispatch, and the action that reaches another action's key: not keys.
HOOK_ENTRY_POINTS = levels.HOOK_ENTRY_POINTS
DISPATCHERS = levels.DISPATCHERS
REACHES_ANOTHER_KEY = levels.REACHES_ANOTHER_KEY
# The actions ``wb preview`` dispatches to; each has a key.
PREVIEW_ACTIONS = levels.PREVIEW_ACTIONS
# The launcher spellings a rule names; `python3 -B -m workbench` is how this repository's own checks are run.
SPELLINGS = levels.SPELLINGS

# Not yet routed by cli.py; the drift test allows exactly these until their increment lands.
NOT_YET_ROUTED = ()

FLOOR_RULES = {
    "force-or-rewrite-history": (
        ("ask", "shell", "git push --force*"),
        ("ask", "shell", "git push -f*"),
        ("ask", "shell", "git push * --force*"),
        ("ask", "shell", "git push * -f*"),
        ("ask", "shell", "git rebase*"),
        ("ask", "shell", "git reset --hard*"),
        ("ask", "shell", "git filter-branch*"),
        ("ask", "shell", "git commit --amend*"),
    ),
    "delete-or-overwrite-files": (
        ("ask", "shell", "rm"),
        ("ask", "shell", "rm *"),
        ("ask", "shell", "rmdir"),
        ("ask", "shell", "rmdir *"),
        ("ask", "shell", "unlink"),
        ("ask", "shell", "unlink *"),
        ("ask", "shell", "shred"),
        ("ask", "shell", "shred *"),
        ("ask", "shell", "git clean*"),
        ("ask", "shell", "git checkout -- *"),
        ("ask", "shell", "git checkout ."),
        ("ask", "shell", "git stash drop*"),
        ("ask", "shell", "git restore*"),
    ),
    "publish-or-deploy": (
        ("ask", "shell", "git push"),
        ("ask", "shell", "git push *"),
        ("ask", "shell", "npm publish*"),
        ("ask", "shell", "twine upload*"),
        ("ask", "shell", "cargo publish*"),
        ("ask", "shell", "docker push*"),
        ("ask", "shell", "gh release create*"),
    ),
    "touch-secrets": (
        ("ask", "read", ".env"),
        ("ask", "read", ".env.*"),
        ("ask", "read", "**/.env"),
        ("ask", "read", "**/.env.*"),
        ("ask", "read", "~/.ssh/**"),
        ("ask", "read", "~/.aws/**"),
        ("ask", "read", "~/.config/gh/**"),
        ("ask", "read", "~/.gnupg/**"),
    ),
    "install-dependencies": (
        ("ask", "shell", "pip install*"),
        ("ask", "shell", "pip3 install*"),
        ("ask", "shell", "python3 -m pip install*"),
        ("ask", "shell", "npm install*"),
        ("ask", "shell", "npm i"),
        ("ask", "shell", "npm i *"),
        ("ask", "shell", "npm ci*"),
        ("ask", "shell", "pnpm install*"),
        ("ask", "shell", "pnpm i"),
        ("ask", "shell", "pnpm i *"),
        ("ask", "shell", "yarn"),
        ("ask", "shell", "yarn install*"),
        ("ask", "shell", "poetry install*"),
        ("ask", "shell", "uv sync*"),
        ("ask", "shell", "bundle install*"),
        ("ask", "shell", "cargo install*"),
        ("ask", "shell", "pipx install*"),
        ("ask", "shell", "python -m pip install*"),
        ("ask", "shell", "yarn add*"),
        ("ask", "shell", "pnpm add*"),
        ("ask", "shell", "cargo add*"),
        ("ask", "shell", "go get*"),
        ("ask", "shell", "gem install*"),
        ("ask", "shell", "brew install*"),
        ("ask", "shell", "apt install*"),
        ("ask", "shell", "apt-get install*"),
        ("ask", "shell", "uv add*"),
        ("ask", "shell", "uv pip install*"),
        ("ask", "shell", "poetry add*"),
    ),
}


def command_owner_patterns(command, arguments):
    """The shell patterns that deny the agent each of a module command's owner-run `arguments`.

    The launcher takes the capability option before the command name, so each argument is denied bare, with
    further arguments, and through ``--provides``. The first argument is all a declaration can authorize;
    the patterns are a best-effort match on the text submitted, as the rest of this file is."""
    out = []
    for spelling in SPELLINGS:
        for argument in arguments:
            for head in ("run", "run --provides *"):
                out.append("%s %s %s %s" % (spelling, head, command, argument))
                out.append("%s %s %s %s *" % (spelling, head, command, argument))
    return out


def owner_run_command_patterns(command):
    """The shell patterns that deny one owner-run `command`, bare and with arguments, in each spelling."""
    out = []
    for spelling in SPELLINGS:
        out.append("%s %s" % (spelling, command))
        out.append("%s %s *" % (spelling, command))
    return out


def owner_run_patterns():
    """The shell patterns that deny each owner-run command, bare and with arguments."""
    out = []
    for command in OWNER_RUN:
        out.extend(owner_run_command_patterns(command))
    return out
