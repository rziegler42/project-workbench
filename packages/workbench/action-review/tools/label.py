#!/usr/bin/env python3
"""Label the commands the shadow hook collected: the owner's judgment of what the engine said.

The owner copies this file and ``shadow_store.py`` out of the project to a directory of their own and runs it at a terminal:

    python3 -B /path/to/label.py [--skipped]

(``docs/specs/action-review.md``, "Labelling and the report"). It shows one collected command at a time with the engine's verdict
and records ``right``, ``wrong`` or ``skip`` in ``labels.jsonl``, with an optional note: ``r``, ``w`` or ``s``, then a space and
the note. ``f`` shows the facts in full, ``q`` stops. A command already labelled is not shown again; with ``--skipped`` the ones
that were skipped are shown once more. ``right`` means the owner would have judged as the engine did, ``wrong`` that they
would not.

It runs only when standard input and standard output are terminals, because the label is the owner's own act. What it shows
is made harmless: every character that is not printable ASCII, escape sequences included, is written as a visible escape, so
nothing in a command or a diff can drive the terminal. A fact is shown by name and size until the owner asks for it. It starts
no program, reads no file but the store, and each label is one whole row or none.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import shadow_store as store  # noqa: E402  the store beside this file

USAGE = "usage: label.py [--skipped]"
PROMPT = "[r]ight  [w]rong  [s]kip  [f]acts  [q]uit > "
# Printed with every command: a flipped reading of "right" for a decline would corrupt the counts the cutover rests on.
MEANING = "right = you would have judged as the engine did; wrong = you would not"
MAX_COMMAND = 8000
MAX_REASON = 600
MAX_NOTE = 300
MAX_FACT = 4000
MAX_FACTS_SHOWN = 40000
MAX_ITEMS = 50
MAX_DEPTH = 6


def visible(text, limit):
    """`text` as printable ASCII on one line: every other character, and the backslash, as an escape; cut to `limit` characters
    with a count of what was left out."""
    parts = []
    for char in text:
        code = ord(char)
        if char == "\\":
            parts.append("\\\\")
        elif char == "\n":
            parts.append("\\n")
        elif char == "\t":
            parts.append("\\t")
        elif char == "\r":
            parts.append("\\r")
        elif 0x20 <= code <= 0x7E:
            parts.append(char)
        elif code < 0x100:
            parts.append("\\x%02x" % code)
        elif code < 0x10000:
            parts.append("\\u%04x" % code)
        else:
            parts.append("\\U%08x" % code)
    cleaned = "".join(parts)
    if len(cleaned) > limit:
        return "%s [%d more characters]" % (cleaned[:limit], len(cleaned) - limit)
    return cleaned


def summary_lines(facts):
    """One line per fact: the name, and the value only where it is short and plain; text is shown by its length."""
    inner = facts.get("facts") if isinstance(facts, dict) and isinstance(facts.get("facts"), dict) else facts
    if not isinstance(inner, dict):
        return ["  (the facts are not an object; ask for them with f)"]
    lines = []
    for name, value in list(inner.items())[:MAX_ITEMS]:
        label = visible(str(name), 64)
        if isinstance(value, bool) or value is None or isinstance(value, int):
            lines.append("  %s = %s" % (label, visible(str(value), 24)))
        elif isinstance(value, str):
            lines.append("  %s: text of %d characters" % (label, len(value)))
        elif isinstance(value, list):
            lines.append("  %s: list of %d" % (label, len(value)))
        elif isinstance(value, dict):
            lines.append("  %s: object of %d" % (label, len(value)))
        else:
            lines.append("  %s: a value" % label)
    if len(inner) > MAX_ITEMS:
        lines.append("  [%d more facts]" % (len(inner) - MAX_ITEMS))
    return lines


def full_lines(value, indent=0, name=None):
    """Every fact, cleaned, with each text cut at MAX_FACT characters and each list at MAX_ITEMS entries."""
    pad = "  " * indent
    head = "%s%s: " % (pad, visible(str(name), 64)) if name is not None else pad
    if indent > MAX_DEPTH:
        return [head + "[deeper than shown]"]
    if isinstance(value, dict):
        lines = [head + "{%d}" % len(value)] if name is not None else []
        for key, item in list(value.items())[:MAX_ITEMS]:
            lines.extend(full_lines(item, indent + (1 if name is not None else 0), key))
        if len(value) > MAX_ITEMS:
            lines.append("%s  [%d more]" % (pad, len(value) - MAX_ITEMS))
        return lines
    if isinstance(value, list):
        lines = [head + "[%d]" % len(value)]
        for number, item in enumerate(value[:MAX_ITEMS]):
            lines.extend(full_lines(item, indent + 1, number))
        if len(value) > MAX_ITEMS:
            lines.append("%s  [%d more]" % (pad, len(value) - MAX_ITEMS))
        return lines
    if isinstance(value, str):
        return [head + visible(value, MAX_FACT)]
    return [head + visible(str(value), 40)]


def show(stdout, row, number, total):
    stdout.write("\n%d of %d   %s   rule %s\n" % (number, total, visible(row["ts"], 24), visible(row["rule"], 64)))
    stdout.write("command: %s\n" % visible(row["command"], MAX_COMMAND))
    checks = ", ".join(visible(name, 64) for name in row["failed_checks"]) or "none"
    stdout.write("the engine said: %s (failed checks: %s)\n" % (visible(row["verdict"], 16), checks))
    # The reason is the model's own words when a model was asked, and a hostile commit message can steer them. A decline by the
    # engine's own checks (a fixed check, or a prompt too large for the bridge) carries the engine's fixed text instead; the
    # collected row does not mark which, so the line says "when". A model's reply can imitate that fixed text: do not rely on it.
    stdout.write("the reason (the model's own words when a model was asked, which the commit's own text may have steered): %s\n"
                 % visible(row["reason"], MAX_REASON))
    stdout.write("facts (ask for the rest with f):\n")
    for line in summary_lines(row["facts"]):
        stdout.write(line + "\n")
    stdout.write(MEANING + "\n")


def show_facts(stdout, row):
    text = "\n".join(full_lines(row["facts"]))
    if len(text) > MAX_FACTS_SHOWN:
        text = text[:MAX_FACTS_SHOWN] + "\n[%d more characters]" % (len(text) - MAX_FACTS_SHOWN)
    stdout.write("--- the facts, cleaned ---\n%s\n--- end of the facts ---\n" % text)


def read_choice(line):
    """``(choice, note)`` from the owner's line, or None when it is not a choice."""
    text = line.strip()
    if not text:
        return None
    first, rest = text[0].lower(), text[1:]
    if first in "fq" and not rest:
        return first, None
    if first in "rws" and (not rest or rest[0].isspace()):
        note = "".join(char if " " <= char <= "~" else "?" for char in rest.strip())[:MAX_NOTE].strip()
        return first, note or None
    return None


def run(argv, stdin, stdout, stderr, home):
    if argv not in ([], ["--skipped"]):
        stderr.write(USAGE + "\n")
        return 2
    if not (stdin.isatty() and stdout.isatty()):
        stderr.write("label.py records your judgment and runs only at a terminal\n")
        return 2
    wanted = "skip" if argv else None
    try:
        collected, unread_c = store.read("collected.jsonl", home)
        labels, unread_l = store.read("labels.jsonl", home)
    except store.StoreError as exc:
        stderr.write("the store cannot be read: %s\n" % visible(str(exc), 200))
        return 1
    latest = {row["id"]: row["label"] for row in labels}  # a later row for the same command replaces an earlier one
    queue = [row for row in collected if latest.get(row["id"]) == wanted]
    unread = unread_c + unread_l
    if unread:
        stdout.write("%d line%s of the files could not be read and %s not shown.\n"
                     % (unread, "" if unread == 1 else "s", "is" if unread == 1 else "are"))
    if not queue:
        stdout.write("Nothing to label.\n")
        return 0
    stdout.write("%d command%s to label.\n" % (len(queue), "" if len(queue) == 1 else "s"))
    done = 0
    for number, row in enumerate(queue, 1):
        show(stdout, row, number, len(queue))
        while True:
            stdout.write(PROMPT)
            stdout.flush()
            line = stdin.readline()
            if line == "":
                stdout.write("\nEnd of input.\n")
                stdout.write("Recorded %d, %d left.\n" % (done, len(queue) - done))
                return 0
            choice = read_choice(line)
            if choice is None:
                stdout.write("Answer r, w, s, f or q (r, w and s may be followed by a note).\n")
                continue
            if choice[0] == "f":
                show_facts(stdout, row)
                continue
            if choice[0] == "q":
                stdout.write("Recorded %d, %d left.\n" % (done, len(queue) - done))
                return 0
            label = {"r": "right", "w": "wrong", "s": "skip"}[choice[0]]
            entry = {"id": row["id"], "label": label, "ts": store.now()}
            if choice[1]:
                entry["note"] = choice[1]
            try:
                store.append("labels.jsonl", entry, home)
            except store.StoreError as exc:
                stderr.write("the label could not be recorded: %s\n" % visible(str(exc), 200))
                return 1
            done += 1
            break
    stdout.write("\nRecorded %d, none left.\n" % done)
    return 0


def main(argv, stdin, stdout, stderr, home=None):
    """Run the tool and return its exit status: 0 done, 1 the store failed, 2 not a terminal or a bad argument, 130 interrupted."""
    try:
        return run(argv, stdin, stdout, stderr, home)
    except KeyboardInterrupt:
        try:
            stdout.write("\nInterrupted; every label recorded so far is whole.\n")
        except (OSError, ValueError):
            pass
        return 130
    except UnicodeError:
        stderr.write("what you typed could not be read as text; nothing more was recorded\n")
        return 1
    except (OSError, ValueError) as exc:
        stderr.write("the tool stopped on %s; every label recorded so far is whole\n" % type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout, sys.stderr))
