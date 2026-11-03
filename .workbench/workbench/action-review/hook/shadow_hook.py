#!/usr/bin/env python3
"""The action-review shadow hook: records what the engine would say about a command that raised a prompt, and says nothing.

The owner copies this file and ``shadow_store.py`` out of the project to a directory of their own and registers the hook for
the ``PermissionRequest`` event, matcher ``Bash``, with a time limit of 30 seconds and no ``onFailure`` setting:

    python3 /path/to/shadow_hook.py --wb /absolute/path/to/wb

(``docs/specs/action-review.md``, "The shadow hook"). For each prompt it runs ``wb run action-review review --log-row
--collect '<command>'`` from the directory the command will run in, reads the lines the engine prints on standard error, and
writes a row to ``~/.config/project-workbench/action-review/`` through ``shadow_store``. It writes nothing to standard output
and exits 0 in every case: the prompt stays the owner's, whatever the engine said and whatever went wrong here. A failure of the
hook is noted on standard error, with fixed text that never quotes the command.

What it does not do: parse the command (the engine's own parse and exit path give the reason), find ``wb`` through ``PATH`` or
inside the command's own directory, pass its environment on, or trust a line of standard error that is not the last line of its
kind. The ``wb`` launcher is given a clean environment. Standard library only, apart from the store beside it.
"""

import hashlib
import json
import os
import signal
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import shadow_store as store  # noqa: E402  the store beside this file, whose directory is the first on the path

# The engine's own limit is 25 seconds and the hook's, in the owner's settings, is 30: this wait is between them, so the engine
# reports first and the hook records a timeout before the harness stops it.
WAIT_SECONDS = 27
SECOND_WAIT = 2  # after the group is killed, for the output of a program that left it; the two add up to under 30
MAX_INPUT = 1 << 20
MAX_COMMAND = 4096
MAX_STREAM = 2 << 20
USAGE = "usage: shadow_hook.py [--wb <absolute path of the wb launcher>]"
REASONS = ("reviewed", "no_rule", "unreviewable", "refused", "failed", "timeout")
# A timeout is exit 1 when `describe` ran out of time (a refusal) and exit 2 when the bridge did (a failure).
EXIT_OF = {"reviewed": (0,), "no_rule": (1,), "unreviewable": (1,), "refused": (1,), "failed": (2,), "timeout": (1, 2)}
ENGINE_FIELDS = ("rule", "facts_sha256", "rubric_sha256", "bridge", "model", "effort", "format")
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}


def note(err, text):
    try:
        err.write(text + "\n")
    except (OSError, ValueError):
        pass


# -- the input --------------------------------------------------------------------------------------------------------

def read_event(stdin):
    """``(kind, command, cwd)``: kind is ``ok``, ``malformed_input`` or ``not_bash``."""
    try:
        data = stdin.read(MAX_INPUT + 1)
        if not isinstance(data, bytes) or len(data) > MAX_INPUT:
            return "malformed_input", None, None
        event = json.loads(data.decode("utf-8"))
    except (OSError, ValueError, RecursionError):
        return "malformed_input", None, None
    if not isinstance(event, dict) or event.get("hook_event_name") != "PermissionRequest":
        return "malformed_input", None, None
    if event.get("tool_name") != "Bash":
        return "not_bash", None, None
    tool_input, cwd = event.get("tool_input"), event.get("cwd")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command or not isinstance(cwd, str) or "\0" in cwd \
            or not os.path.isabs(cwd) or not os.path.isdir(cwd):
        return "malformed_input", None, None
    return "ok", command, cwd


def parse_arguments(argv, home_dir):
    """The path of the ``wb`` launcher, or None for a call this hook does not take."""
    if argv == []:
        return os.path.join(home_dir, ".config", "project-workbench", "bin", "wb")
    if len(argv) == 2 and argv[0] == "--wb":
        return argv[1]
    return None


def usable_launcher(wb, cwd):
    """True when `wb` is an absolute path to an executable file named ``wb`` that is not inside the command's own directory,
    which a repository could change. The name is `wb` because the engine looks for that name in the trusted entries of its
    ``PATH``, which the hook builds from the launcher's own directory (so that directory must not hold the path separator)."""
    if not isinstance(wb, str) or "\0" in wb or not os.path.isabs(wb) or not os.path.isfile(wb) \
            or not os.access(wb, os.X_OK) or os.path.basename(wb) != "wb" or os.pathsep in os.path.dirname(wb):
        return False
    real, base = os.path.realpath(wb), os.path.realpath(cwd)
    return not (real == base or real.startswith(base + os.sep))


# -- the engine ---------------------------------------------------------------------------------------------------------

def run_engine(wb, command, cwd, home_dir):
    """``(exit code, standard output, standard error, timed out)`` of the engine, run in its own process group."""
    # The engine finds `wb` by name in the trusted entries of the PATH it inherits, so the launcher's own directory comes first.
    environment = dict(ENVIRONMENT, HOME=home_dir, PATH=os.pathsep.join([os.path.dirname(wb), ENVIRONMENT["PATH"]]))
    proc = subprocess.Popen([wb, "run", "action-review", "review", "--log-row", "--collect", command], cwd=cwd,
                            env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True, close_fds=True)
    try:
        out, err = proc.communicate(timeout=WAIT_SECONDS)
        timed_out = False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            out, err = proc.communicate(timeout=SECOND_WAIT)
        except subprocess.TimeoutExpired:  # a program that left the group still holds the pipes: do not wait for it
            out, err = b"", b""
        timed_out = True
    return proc.returncode, out, err, timed_out


def last_line(lines, prefix):
    for line in reversed(lines):
        if line.startswith(prefix):
            return line[len(prefix):]
    return None


def parse_json(text):
    try:
        return json.loads(text)
    except (ValueError, RecursionError):
        return None


def read_verdict(out):
    """The engine's verdict object as ``(verdict, failed_checks, reason)``, or None unless it is exactly the object the
    engine promises: one line, three fields, an approve with no failed check and a decline with at least one."""
    try:
        text = out.decode("ascii")
    except UnicodeDecodeError:
        return None
    if not text.endswith("\n") or text.count("\n") != 1:
        return None
    body = parse_json(text)
    if not isinstance(body, dict) or set(body) != {"verdict", "failed_checks", "reason"}:
        return None
    verdict, failed, reason = body["verdict"], body["failed_checks"], body["reason"]
    if verdict not in ("approve", "decline") or not isinstance(failed, list) or len(failed) > 32 \
            or not all(isinstance(item, str) for item in failed) or (verdict == "approve") != (not failed) \
            or not isinstance(reason, str) or not 1 <= len(reason) <= 300 \
            or not all(" " <= char <= "~" for char in reason):
        return None
    return verdict, failed, reason


def classify(code, out, err, timed_out):
    """``(outcome, verdict, log_row, facts)`` from what the engine did. The outcome is the engine's own reason, taken from the
    last line of its standard error, and is believed only when it agrees with the exit code and, for a review, with a whole
    verdict object."""
    if timed_out:
        return "timeout", None, None, None
    if len(out) > MAX_STREAM or len(err) > MAX_STREAM:
        return "failed", None, None, None
    lines = err.decode("ascii", "replace").split("\n")
    present = [line for line in lines if line]
    body = parse_json(present[-1][len("outcome: "):]) if present and present[-1].startswith("outcome: ") else None
    reason = body.get("reason") if isinstance(body, dict) and set(body) == {"reason"} else None
    if reason not in REASONS:
        return ("refused" if code == 1 else "failed"), None, None, None
    if code not in EXIT_OF[reason]:
        return "failed", None, None, None
    if reason != "reviewed":
        return reason, None, None, None
    verdict = read_verdict(out)
    if verdict is None:
        return "failed", None, None, None
    row, facts = last_line(lines, "log-row: "), last_line(lines, "facts: ")
    row = parse_json(row) if row is not None else None
    facts = parse_json(facts) if facts is not None else None
    return "reviewed", verdict, row if isinstance(row, dict) else None, facts if isinstance(facts, dict) else None


# -- the rows ---------------------------------------------------------------------------------------------------------

def sha256(text):
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()


def write(err, name, row, home, fallback=None):
    """Append `row`; on a refusal try `fallback`; a store that cannot take it is noted and nothing else changes."""
    for candidate in (row, fallback):
        if candidate is None:
            continue
        try:
            store.append(name, candidate, home)
            return True
        except store.StoreError as exc:
            problem = str(exc)
    note(err, "the hook could not record a row in %s: %s" % (name, problem[:200]))
    return False


def record(err, home, outcome, command, verdict=None, log_row=None, facts=None):
    """Write the verdict row for one prompted command and, for a reviewed command with its facts, the collected row."""
    reviewed = outcome == "reviewed"
    digest = sha256(command) if command is not None else None
    row = {"ts": store.now(), "command_sha256": digest, "outcome": outcome,
           "verdict": verdict[0] if verdict else None, "failed_checks": list(verdict[1]) if verdict else [],
           "reason": verdict[2] if verdict else None, "reviewed": reviewed,
           "no_review_reason": None if reviewed else outcome}
    plain = dict(row)
    if reviewed and log_row:
        row.update({field: log_row[field] for field in ENGINE_FIELDS if field in log_row})
    write(err, "verdicts.jsonl", row, home, plain if row != plain else None)
    rule = log_row.get("rule") if log_row else None
    if reviewed and facts is not None and isinstance(rule, str):
        write(err, "collected.jsonl", {
            "id": store.new_id(), "ts": row["ts"], "rule": rule, "command_sha256": digest, "command": command,
            "facts": facts, "verdict": verdict[0], "failed_checks": list(verdict[1]), "reason": verdict[2]}, home)


def run(argv, stdin, err, home):
    home_dir = home if home is not None else os.path.expanduser("~")
    wb = parse_arguments(argv, home_dir)
    if wb is None:
        note(err, USAGE)
        return
    kind, command, cwd = read_event(stdin)
    if kind != "ok":
        record(err, home, kind, None)
        return
    if len(command) > MAX_COMMAND:
        record(err, home, "unreviewable", command)
        return
    if not usable_launcher(wb, cwd):
        note(err, "the hook was not given a wb it may run; nothing was reviewed")
        record(err, home, "failed", command)
        return
    try:
        code, out, errb, timed_out = run_engine(wb, command, cwd, home_dir)
    except (OSError, ValueError):
        note(err, "the engine could not be started")
        record(err, home, "failed", command)
        return
    outcome, verdict, log_row, facts = classify(code, out, errb, timed_out)
    record(err, home, outcome, command, verdict, log_row, facts)


def main(argv, stdin, err, home=None):
    """Record one prompted command and return 0. Nothing is written to standard output, and an error of any kind, an
    interrupt included, is noted and does not change the return value: the hook answers nothing."""
    try:
        run(argv, stdin, err, home)
    except BaseException as exc:
        note(err, "the hook stopped on %s; the prompt is unchanged" % type(exc).__name__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.buffer, sys.stderr))
