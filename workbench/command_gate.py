"""``gate-command <harness>``: the command gate, the Bash hook a harness's rendered settings run when a key is at
``ask`` or ``none``.

``docs/decisions/2026-10-26-ask-level-command-gate.md`` (with its clarification note) and the plan
``2026-10-26-command-permission-levels``, Increment J. At ``ask`` and ``none`` the terminal test no longer applies, so the
barrier is the harness's own ``ask`` rule, which matches the command text. A command that no rule names (``bash -c '...'``)
is decided by the harness's classifier in auto mode. This gate reads one Bash tool call as JSON on standard input and:

* allows a command that reads a word only as data: one simple command, or a pipeline of them, of a closed list of programs
  that never run their arguments (``cat``, ``head``, ``tail``, ``grep``, ``ls``, ``wc``, ``diff``), whose arguments are plain
  tokens or single-quoted strings, with no ``$``, backtick, ``;``, ``&&``, ``||``, newline outside quotes or redirection but
  ``2>/dev/null`` and ``2>&1`` (``reads_as_data``; decision ``2026-11-02-command-gate-reads-gaps-and-data-positions``, 3);
* allows a command that names no word of a relaxed command;
* allows a command that is exactly the simple command the ``ask`` rule matches, on the raw text with single spaces and case
  kept (``wb approve-plan <path> [--digest <32 hex>]``, or the same through the guarded store's own ``bin/wb``), so the
  harness then prompts the owner;
* reads a command that is exactly one quoted python here-document (``python_heredoc``: ``python3`` or ``python`` with only the flags
  ``-B``, ``-I``, ``-E`` and ``-u``, then ``-``, a quoted or escaped delimiter, a body and a terminator line that is exactly the tag and
  is the last line) for the words it holds, body included, and not for gaps: the gap rule, its free-region test and the parameter-operator
  rule read only the first line (decision ``2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps``, 1 and 2; plan
  ``2026-11-08-python-heredoc-gate``). Every other here-document, and every shell that runs one, is read whole;
* blocks every other command that names such a word, in its folded text or in its *skeleton* (the folded text with every
  character that is not a letter or a digit removed, so quote splicing, a backslash or a punctuation mark does not hide the
  word), also after the static ``$'...'`` strings are decoded as bash decodes them, and every command whose letters, read with
  each expansion, glob, brace group, bare parameter and escape as a wildcard, hold the word's letters with nothing but wildcards
  between them (the gap rule, ``_gap_match``);
* blocks on a malformed input, an oversized command, a failure to find the project and any crash or deadline.

Every refusal names the rule that fired (``names``, ``gap``, ``dollar-quote-limit`` or ``size-limit``): ``verdict`` returns
it with the reason, and the reason ends ``(rule: <name>)``. ``run`` then appends the rule and a short hash of the command, never
its text, to the refusal log (``gatelog``) after the verdict is fixed.

* for a key of the form ``wb <word>`` and for ``approve-plan``, allows a command that is exactly one literal ``wb run <name>
  <arguments>`` (plain tokens and single-quoted strings only, on the raw text): ``wb run`` dispatches to a declared, pinned
  module command and never to an owner-run verb, so a word in the arguments (a commit subject, a path) is data
  (``docs/decisions/2026-10-27-command-gate-literal-arguments.md``; ``approve-plan`` joins them by decision 4 of
  ``2026-11-02-command-gate-reads-gaps-and-data-positions``, which the owner chose);
* for a key of the form ``wb run <command> <argument>``, allows the same literal call of that command when its first
  argument is a plain token other than the key's ``<argument>`` (for example a ``preview <argument>`` of the command): the
  launcher runs only the first argument, so the key's argument is data
  (``docs/decisions/2026-10-28-gate-reads-module-arguments.md``). A quoted, escaped or expanded first token, a command of
  another name and a compound command are still searched;
* for such a key, does not take a launcher followed by the exact token of a sibling command that continues the word
  (``wb approve-plan`` for ``wb approve``) for the key's own word; the token alone, as data, is still the word.

It prints nothing and returns 0 to allow, or one ``refused:`` line and 2 to block (the only code a harness takes for a
block; ``gate_hook.guard`` makes every failure a block). The exact token ``delegate-approve-plan`` is removed before the
search: it is the agent-safe delegated command.

What it cannot see, and the owner accepted in writing: a word built at run time (variables whose parts lie apart, ``printf``
escapes, a decoded string), a script file that holds the call and is then run, a function or alias defined earlier, and a
settings file edited and restored between two commands. A literal letter written outside any expansion between two letters
of a word no longer counts as spelling it; inside an expansion it still does (``_free_match``), and a simple assignment in the
same text is put in at its uses (``substituted``). A value the text sets in another way (an array, ``for``, ``printf -v``,
``set --``, ``+=``) can still carry padding that a parameter operator removes (``${x/Q/}``), so a command that holds such an
operator is also read by the earlier in-order rule, within three times the word's length. A hook is a speed bump and not a
boundary.
"""

import collections
import re

from . import gate_hook, levels, rules
from .wbkit import display

USAGE = "usage: wb gate-command <harness>\n"
MAX_COMMAND = 64 * 1024
MAX_DOLLAR_QUOTES = 64  # decoding tries every ``$'``, so a command full of them costs time and memory
RELAXED = ("ask", "none")
# The agent-safe command whose name contains the word of ``approve-plan``.
EXEMPT = ("delegate-approve-plan",)
# A single-word command key (``wb install``) is read in command position: a launcher spelling, then the word. The launchers
# are the last words of the spellings an agent could submit (``wb``, and ``workbench`` of ``python3 -m workbench``; the
# guarded store's ``bin/wb`` ends in ``wb``). ``wb preview <action>`` is agent-safe and has its own key, so the exact pair
# ``preview <action>`` is removed before the search, as the agent-safe ``delegate-approve-plan`` is.
LAUNCHERS = tuple(sorted({spelling.split()[-1] for spelling in rules.SPELLINGS}))
PREVIEW_ACTIONS = tuple(rules.PREVIEW_ACTIONS)
_TOKEN = r"[A-Za-z0-9._/:=-]+"
# The literal ``wb run <name> <arguments>`` form: a name as a pin or a command name is spelled, then plain tokens or
# single-quoted strings (bash reads those literally, a newline included), each after one space.
_RUN_NAME = r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}"
_RUN_PLAIN = r"[A-Za-z0-9._/:=@,+-]+"
_RUN_ARGUMENT = r"(?:%s|'[^']*')" % _RUN_PLAIN
# A name that is a launcher or a verb is never the module command of a literal call.
RESERVED_NAMES = frozenset(rules.OWNER_RUN) | frozenset(rules.AGENT_SAFE) | frozenset(LAUNCHERS) | {"python", "python3"}
_PATH = r"[A-Za-z0-9._/][A-Za-z0-9._/-]*"
_DIGEST = r"[0-9a-f]{32}"

Refusal = gate_hook.Refusal

# What a refusal says about itself: the rule that fired and the reason in one line.
Verdict = collections.namedtuple("Verdict", "rule reason")
NAMES, GAP, DOLLAR_QUOTE_LIMIT, SIZE_LIMIT = "names", "gap", "dollar-quote-limit", "size-limit"

# The programs that never run their arguments, so a word among their arguments is data (decision
# ``2026-11-02-command-gate-reads-gaps-and-data-positions``, 3). The list is closed and kept here. An interpreter, ``sed``,
# ``awk``, ``find``, ``xargs``, ``env``, ``tee``, ``sort``, every launcher and ``git`` are not on it: ``git`` takes options that run
# a program (``-c``, ``--git-dir``, ``--ext-diff``, ``--textconv``), and may return only with an allowlist of options for each
# subcommand, by a later record.
DATA_PROGRAMS = ("cat", "diff", "grep", "head", "ls", "tail", "wc")
_DATA_ARGUMENT = r"(?:%s|'[^']*')" % _RUN_PLAIN
_DATA_REDIRECT = r"2>(?:/dev/null|&1)"
_DATA_SIMPLE = r"(?:%s)(?: (?:%s|%s))*" % ("|".join(DATA_PROGRAMS), _DATA_ARGUMENT, _DATA_REDIRECT)
_DATA_COMMAND = re.compile(r"%s(?: \| %s)*" % (_DATA_SIMPLE, _DATA_SIMPLE))


# The shape of a python here-document whose body the gap rule does not read (decision
# ``2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps``, 1; plan ``2026-11-08-python-heredoc-gate``): one
# simple command, optionally after ``cd <plain token> && ``, that is ``python3`` or ``python`` with only the separate flags
# ``-B``, ``-I``, ``-E`` and ``-u``, then ``-``, then ``<<`` and a quoted (``'TAG'``, ``"TAG"``) or escaped (``\TAG``) delimiter,
# single spaces throughout, and nothing after the delimiter. The tag is narrower than bash allows (no quoting can make it differ
# from the line that ends the body); a valid tag outside it is not the shape and is judged as before.
_HEREDOC_TAG = r"[A-Za-z_][A-Za-z0-9_]{0,31}"
_PYTHON_HEREDOC = re.compile(
    r"(?:cd %s && )?python3? (?:-[BEIu] )*- <<(?:'(?P<single>%s)'|\"(?P<double>%s)\"|\\(?P<bare>%s))"
    % (_RUN_PLAIN, _HEREDOC_TAG, _HEREDOC_TAG, _HEREDOC_TAG))


def python_heredoc(text):
    """The first line of `text` when `text` is exactly one python here-document of the shape above, otherwise ``None``.

    The terminator is as bash reads it: the first line after the first that is exactly the tag. It must be the last line of
    the text, with at most one final newline after it; a line that only looks like the tag, text after the terminator and a
    text with no terminator are not the shape. Lines are split on ``\\n`` and nothing else, as bash splits them (``splitlines``
    also splits on ``\\r``, ``\\x0b``, ``\\x0c``, ``\\x85`` and ``\\u2028``, which would end a body that bash does not end)."""
    head, newline, rest = text.partition("\n")
    if not newline or "\0" in text:
        return None
    found = _PYTHON_HEREDOC.fullmatch(head)
    if found is None:
        return None
    tag = found.group("single") or found.group("double") or found.group("bare")
    lines = rest.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if tag not in lines or lines.index(tag) != len(lines) - 1:
        return None
    return head


def words(key):
    """The words of the command `key` names, in order: ``approve-plan``; ``wb run <command> <argument>`` gives both."""
    found = levels.command_words(key)
    if found[:1] == ("run",) and len(found) >= 3:
        return list(found[1:])
    if found[:1] == ("preview",) and len(found) == 2:
        return []
    return list(found)


def _run_key(key):
    """Whether `key` is a module argument, ``wb run <command> <argument>``."""
    found = levels.command_words(key)
    return found[:1] == ("run",) and len(found) >= 3


def _hint_command(key):
    """The command `key` is run as, for a hint: ``wb run <command> <argument>`` for a module argument, else ``wb <words>``."""
    return ("wb run " if _run_key(key) else "wb ") + " ".join(words(key))[:60]


def _by_launcher(key):
    """Whether `key` is read as a launcher and then a word (not ``approve-plan`` and not ``wb run <command> <argument>``)."""
    return bool(words(key)) and key != "approve-plan" and not _run_key(key)


def alternatives(key):
    """The spellings of the command `key` names, each a list of words that must occur in order. ``approve-plan`` is read as
    the word alone, and ``wb run <command> <argument>`` as its words; any other ``wb <word>`` is a launcher and then the word,
    so that an ordinary command holding the word (``npm install``) is not taken for it."""
    found = words(key)
    if not found:
        return []
    if not _by_launcher(key):
        return [found]
    return [[launcher] + found for launcher in LAUNCHERS]


def siblings(key):
    """The commands of ``rules`` whose names continue the word of a single-word key (``approve-plan`` for ``wb approve``): they
    have their own key or rule, so their exact token is not the key's word."""
    if not _by_launcher(key):
        return ()
    word = words(key)[0]
    return tuple(name for name in rules.OWNER_RUN + rules.AGENT_SAFE if name.startswith(word + "-"))


def literal_run(text, store_bin):
    """Whether `text`, as written, is exactly one ``wb run <name> <arguments>`` with literal arguments (through ``wb`` or the
    guarded store's own ``bin/wb``), a name that is not a launcher or a verb, and nothing else."""
    heads = "|".join(["wb", re.escape(store_bin)])
    found = re.fullmatch(r"(?:%s) run (%s)(?: %s)*" % (heads, _RUN_NAME, _RUN_ARGUMENT), text)
    return bool(found) and found.group(1) not in RESERVED_NAMES


def reads_argument_as_data(text, key, store_bin):
    """Whether `text` is one literal ``wb run <command> <first> ...`` of the command of a key ``wb run <command> <argument>``,
    with a plain first token that is not the key's `<argument>`. The launcher dispatches on that first argument and refuses an
    undeclared one, so the key's argument is not run and its word is data
    (``docs/decisions/2026-10-28-gate-reads-module-arguments.md``). A quoted, escaped or expanded first token is not plain,
    and a command of another name is not freed. This holds only for a module command whose helper takes its action from the
    first argument alone; a helper that took it from a later position, or re-dispatched one, would need its key left out."""
    found = words(key)
    if not _run_key(key) or len(found) != 2 or not literal_run(text, store_bin):
        return False
    heads = "|".join(["wb", re.escape(store_bin)])
    call = re.fullmatch(r"(?:%s) run (%s) (%s)(?: %s)*" % (heads, _RUN_NAME, _RUN_PLAIN, _RUN_ARGUMENT), text)
    return bool(call) and call.group(1) == found[0] and _folded(call.group(2)) != _folded(found[1])


def reads_as_data(text):
    """Whether `text`, as written, is one simple command or a pipeline of simple commands of ``DATA_PROGRAMS``, every argument a
    plain token or a single-quoted string (bash expands nothing in either), and nothing else: no ``$``, backtick, ``;``, ``&&``,
    ``||``, newline outside quotes, glob, double quote or redirection but ``2>/dev/null`` and ``2>&1``. A word named in such a
    command is data, so the command is not read by the name tests or by the gap rule. A match on the raw text, as
    ``literal_run`` is; not a shell parser."""
    return _DATA_COMMAND.fullmatch(text) is not None


def forms(key, store_bin):
    """The compiled patterns of the exact simple commands the ``ask`` rule of `key` matches, through ``wb`` and through the
    guarded store's own ``bin/wb`` (`store_bin`)."""
    heads = ["wb", re.escape(store_bin)]
    if key == "approve-plan":
        return [re.compile("%s approve-plan %s( --digest %s)?" % (head, _PATH, _DIGEST)) for head in heads]
    found = words(key)
    if not found:
        return []
    tail = " ".join(re.escape(word) for word in found)
    middle = " run " if _run_key(key) else " "
    return [re.compile("%s%s%s(?: %s)*" % (head, middle, tail, _TOKEN)) for head in heads]


def _folded(text):
    return gate_hook.fold(text)


_ANSI_C = re.compile(r"\$'((?:[^'\\]|\\.)*)'", re.DOTALL)
_SIMPLE = {"a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v",
           "\\": "\\", "'": "'", '"': '"', "?": "?"}
_ESCAPE = re.compile(r"\\(?:x([0-9a-fA-F]{1,2})|u([0-9a-fA-F]{1,4})|U([0-9a-fA-F]{1,8})|([0-7]{1,3})|(.))", re.DOTALL)


def _escape(match):
    hexa, short, long_, octal, other = match.groups()
    try:
        if hexa:
            return chr(int(hexa, 16))
        if short:
            return chr(int(short, 16))
        if long_:
            return chr(int(long_, 16))
        if octal:
            return chr(int(octal, 8) & 0xFF)
    except (ValueError, OverflowError):
        return ""
    return _SIMPLE.get(other, "\\" + other)


def decoded_views(text):
    """`text` and, for every place a ``$'`` starts a string that closes, `text` with that one string decoded as bash decodes
    it. A ``$'`` is tried at every position, because a stray one earlier in the command (``echo '$'``, ``"$'"``) would pair
    with the wrong quote if the text were decoded from left to right in one pass."""
    views = [text]
    for at in range(len(text)):
        if text.startswith("$'", at):
            match = _ANSI_C.match(text, at)
            if match:
                views.append(text[:at] + _ESCAPE.sub(_escape, match.group(1)) + text[match.end():])
    return views


_ESCAPE_TOKEN = re.compile(r"\\(?:x[0-9a-fA-F]{1,2}|u[0-9a-fA-F]{1,4}|U[0-9a-fA-F]{1,8}|[0-7]{1,3})")
_WILD = "\0"
_GLOB_CLASS = re.compile(r"\[[^\]]*\]")
# A bare parameter (``$name``, ``$1``, ``$@``, ``$*``, ``$#``, ``$-``, ``$_``, ``$!``, ``$$``, ``$?``) and a brace group
# (``{a,b}``) expand to nothing or to anything, so each is a wildcard.
_BARE_PARAMETER = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|[0-9@*#?!$-])")
_BRACE_GROUP = re.compile(r"\{[^{}]*\}")
_GLOB_STAR = 3  # a ``*`` can stand for many letters; this many are allowed for (more would block most globs)
# Characters that let a command spell a word without writing it: parameter and command expansion, and the glob and
# brace characters. When one is present the letters of a guarded word are looked for with wildcards between them.
_PATTERN_CHARS = "$?*[{`"
_SUBSTITUTION_WILDS = 8  # an expansion can stand for many letters; its own text is dropped, as it may expand to nothing


def _skeleton(text):
    return "".join(char for char in text if char.isalnum())


def _in_order(text, pieces):
    """Whether the `pieces` occur in `text` one after another."""
    at = 0
    for piece in pieces:
        found = text.find(piece, at)
        if found < 0:
            return False
        at = found + len(piece)
    return True


def _collapse(text):
    """`text` with the inside of every ``$(...)``, ``${...}`` and backtick pair replaced by wildcards. What is inside an
    expansion can expand to nothing (``$(true padding)``, ``${unset:+padding}``), so it is not part of the spelling; what
    the expansion yields can be letters, so it stands for up to ``_SUBSTITUTION_WILDS`` of them. Nesting is balanced as far
    as the text allows; an unclosed one runs to the end."""
    out, at = [], 0
    while at < len(text):
        two = text[at:at + 2]
        if two in ("$(", "${"):
            close = ")" if two == "$(" else "}"
            depth, end = 1, at + 2
            while end < len(text) and depth:
                depth += (text[end] == two[1]) - (text[end] == close)
                end += 1
            out.append(_WILD * _SUBSTITUTION_WILDS)
            at = end
        elif text[at] == "`":
            end = at + 1
            while end < len(text) and text[end] != "`":
                end += 2 if text[end] == "\\" else 1
            out.append(_WILD * _SUBSTITUTION_WILDS)
            at = end + 1
        else:
            out.append(text[at])
            at += 1
    return "".join(out)


def _spelled(version):
    """`version` (folded text, with or without its expansions collapsed) reduced to letters, digits and wildcards: an escape
    sequence, a glob character or class, a bare parameter and a brace group each become a wildcard, and every other character
    that is not a letter or a digit is dropped, as the skeleton drops it."""
    text = _ESCAPE_TOKEN.sub(_WILD, version)
    text = _GLOB_CLASS.sub(_WILD, text)
    text = _BARE_PARAMETER.sub(_WILD * _SUBSTITUTION_WILDS, text)
    text = _BRACE_GROUP.sub(_WILD * _SUBSTITUTION_WILDS, text)
    text = text.replace("?", _WILD).replace("*", _WILD * _GLOB_STAR)
    return "".join(char for char in text if char.isalnum() or char == _WILD)


def _gap_match(spelled, letters):
    """Whether `spelled` holds the characters of `letters` one after another with nothing between two of them but wildcards
    (each ``\0`` stands for one letter or none), and at least a third of them written out. Another literal letter between
    two of the word's letters breaks the match, so letters of unrelated words do not add up to a word. The states are the
    letters matched so far, each with the most written-out letters that reach it, and a match may start anywhere."""
    size = len(letters)
    need = size // 3
    live = {}
    for char in spelled:
        live.setdefault(0, 0)
        if char == _WILD:
            step = dict(live)
            for count, written in live.items():
                if count < size and step.get(count + 1, -1) < written:
                    step[count + 1] = written
        else:
            step = {count + 1: written + 1 for count, written in live.items() if count < size and letters[count] == char}
        live = step
        if live.get(size, -1) >= need:
            return True
    return False


# A simple assignment (``name=value``, the value plain characters and quoted strings with no expansion) and the use of its
# name (``$name``, ``${name}``): a command that sets a variable and uses it in the same text spells the word with the value,
# which the letters-in-a-row tests cannot see apart from the use.
_ASSIGNMENT = re.compile(r"(?:(?<=[\s;&|(])|\A)([A-Za-z_][A-Za-z0-9_]*)=((?:[^\s;&|()<>'\"`$\\]|'[^']*'|\"[^\"`$\\]*\")*)(?=[\s;&|)]|\Z)")
_MAX_ASSIGNMENTS = 16
_MAX_SUBSTITUTED = 4 * MAX_COMMAND  # a value used many times could grow the text a thousandfold; past this it is not put in


def _unquoted(value):
    return "".join(piece[1:-1] if piece[:1] in ("'", '"') else piece
                   for piece in re.findall(r"'[^']*'|\"[^\"]*\"|[^'\"]+", value))


def substituted(text):
    """`text` with each use of a variable that the text itself sets by a simple assignment replaced by its value, or `text`
    unchanged when it sets none. One pass, the last assignment of a name wins, at most ``_MAX_ASSIGNMENTS`` names: a
    variable set from another variable, or from an expansion, is not followed (the gap rule still reads it). The result is
    never longer than ``_MAX_SUBSTITUTED``: a command whose uses would make it longer is returned unchanged."""
    values = {}
    for found in _ASSIGNMENT.finditer(text):
        if len(values) >= _MAX_ASSIGNMENTS and found.group(1) not in values:
            break
        values[found.group(1)] = _unquoted(found.group(2))
    if not values:
        return text
    original = text
    longest = max(len(value) for value in values.values())
    uses = len(re.findall(r"\$\{?[A-Za-z_]", text))
    if len(text) + uses * longest > _MAX_SUBSTITUTED:
        return original

    def use(found):
        return values.get(found.group(1) or found.group(2), found.group(0))
    text = re.sub(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))", use, text)

    def operated(found):
        # ``${A//x/}``, ``${A#pre}`` and the like change the value at run time; the value goes in as the content of an
        # expansion, where the free-region test below lets letters between the word's letters be padding.
        value = values.get(found.group(1))
        return found.group(0) if value is None else "$(" + value + ")"
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)[^A-Za-z0-9_}][^}]*\}", operated, text)


# The inside of an expansion can hold the word's letters with padding that the expansion strips or ignores
# (``$(printf 'inst%s' all)``, ``$(tr -d x <<< xaxp...)``), so there, and only there, other characters may sit between two
# letters of the word. The span still has to fit ``_WINDOW`` times the word's length, and a third of the letters stay written.
_NOISE = "\1"
_WINDOW = 3


def _segments(text):
    """`text` as ``(inside, piece)`` pairs: the inside of each ``$(...)``, ``${...}`` and backtick pair (same balancing as
    ``_collapse``) and the text around them."""
    out, start, at = [], 0, 0
    while at < len(text):
        two = text[at:at + 2]
        if two in ("$(", "${"):
            close = ")" if two == "$(" else "}"
            depth, end = 1, at + 2
            while end < len(text) and depth:
                depth += (text[end] == two[1]) - (text[end] == close)
                end += 1
            out.append((False, text[start:at]))
            out.append((True, text[at + 2:end - 1 if depth == 0 else end]))
            start = at = end
        elif text[at] == "`":
            end = at + 1
            while end < len(text) and text[end] != "`":
                end += 2 if text[end] == "\\" else 1
            out.append((False, text[start:at]))
            out.append((True, text[at + 1:end]))
            start = at = end + 1
        else:
            at += 1
    out.append((False, text[start:]))
    return out


def _free_text(version):
    """`version` as ``_spelled`` reads it outside an expansion; inside one, a letter is written in capitals (it may match a
    letter of the word or be skipped) and any other letter or digit is ``_NOISE`` (skipped). The expansion's output is not
    added as wildcards: ``_gap_match`` on the collapsed text reads that."""
    out = []
    for inside, piece in _segments(version):
        if inside:
            out.append("".join(char.upper() if char.isascii() and char.isalpha() else _NOISE
                               for char in piece if char.isalnum()))
        else:
            out.append(_spelled(piece))
    return "".join(out)


def _free_match(spelled, letters):
    """Whether `letters` are found in `spelled` within ``_WINDOW`` times their number, with nothing between two of them but
    wildcards and the free characters of ``_free_text``, and a third of them written out (a free letter that matches counts)."""
    size, need, width = len(letters), len(letters) // 3, _WINDOW * len(letters)
    for start, char in enumerate(spelled):
        if char == _WILD:
            if start and spelled[start - 1] == _WILD:
                continue
        elif char.lower() != letters[0]:
            continue
        live = {0: 0}
        for char in spelled[start:start + width]:
            if char == _WILD:
                step = dict(live)
                for count, written in live.items():
                    if count < size and step.get(count + 1, -1) < written:
                        step[count + 1] = written
            elif char == _NOISE:
                step = live
            elif char.isupper():
                step, lower = dict(live), char.lower()
                for count, written in live.items():
                    if count < size and letters[count] == lower and step.get(count + 1, -1) < written + 1:
                        step[count + 1] = written + 1
            else:
                step = {count + 1: written + 1 for count, written in live.items() if count < size and letters[count] == char}
            live = step
            if not live:
                break
            if live.get(size, -1) >= need:
                return True
    return False


# ``${name/Q/}``, ``${name#pre}``, ``${name:2}``: a parameter operator changes a value that the text sets in a way the
# assignment tracker does not follow (an array, ``for``, ``printf -v``, ``set --``, ``read``, ``+=``), so the value can sit in the
# text with padding that the operator removes. Only a command with such an operator is also read by the in-order rule that the
# gap rule replaced: the word's letters in order within ``_WINDOW`` times their number, a third of them written out.
_OPERATOR = re.compile(r"\$\{[A-Za-z_0-9@*#!]*[^A-Za-z0-9_}@*#!][^}]*\}")


def _literals(window, letters):
    """The most characters of `letters` that a stretch of text can supply as themselves when it holds all of them in order
    (a ``\0`` supplies any one), or ``-1`` when it does not hold them."""
    best = [-1] * (len(letters) + 1)
    best[0] = 0
    for char in window:
        for at in range(len(letters), 0, -1):
            if best[at - 1] >= 0 and (char == _WILD or char == letters[at - 1]):
                best[at] = max(best[at], best[at - 1] + (0 if char == _WILD else 1))
    return best[len(letters)]


def _subsequence(text, letters):
    """Whether the characters of `letters` occur in `text` in order, not necessarily next to each other, all within
    ``_WINDOW`` times their number, with at least a third of them written out; a ``\0`` matches any character."""
    width = _WINDOW * len(letters)
    need = len(letters) // 3
    for start in range(len(text)):
        if text[start] != letters[0] and text[start] != _WILD:
            continue
        window = text[start:start + width]
        chars = iter(window)
        if all(any(char == wanted or char == _WILD for char in chars) for wanted in letters) \
                and _literals(window, letters) >= need:
            return True
    return False


def _in_order_wilds(version):
    """`version` as the earlier in-order rule read it: escapes, classes and ``?`` as one wildcard, ``*`` as three, every
    other character that is not a letter or a digit dropped."""
    text = _ESCAPE_TOKEN.sub(_WILD, version)
    text = _GLOB_CLASS.sub(_WILD, text).replace("?", _WILD).replace("*", _WILD * _GLOB_STAR)
    return "".join(char for char in text if char.isalnum() or char == _WILD)


def _names(folded, skeleton, pieces):
    """Whether the command text names the words `pieces`, as written or by its skeleton."""
    return _in_order(folded, pieces) or _in_order(skeleton, [_skeleton(piece) for piece in pieces])


def _without(views, tokens):
    """`views` (folded text and skeleton) with each launcher spelling followed by one of the exact `tokens` taken out of the
    text, as ``preview <action>`` is: the token alone stays where it is data (``A=approve-plan; wb ${A%-plan}`` still holds
    the word)."""
    if not tokens:
        return views
    launchers = "|".join(re.escape(_folded(launcher)) for launcher in LAUNCHERS)
    out = []
    for folded, _ in views:
        for token in tokens:
            folded = re.sub(r"(?<![a-z0-9-])(?:%s) %s(?![a-z0-9-])" % (launchers, re.escape(_folded(token))), " ", folded)
        out.append((folded, _skeleton(folded)))
    return out


def _reason(key, spelling, level):
    if level == "none":
        return ("the command names %s, which the owner has set to none here, in a form the gate cannot tell from a call (a "
                "wrapper, a compound command, or a path with ~ or $VAR); run it as `%s ...` on its own, with the path spelled "
                "out" % (display.ascii_text(" ".join(_folded(word) for word in spelling))[:80], _hint_command(key)))
    return ("the command names %s, which the owner has set to ask or none here, and is not exactly the simple "
            "command the ask rule matches; run it as `%s ...` on its own" % (
                display.ascii_text(" ".join(_folded(word) for word in spelling))[:80], _hint_command(key)))


def _verdict(rule, reason):
    return Verdict(rule, "%s (rule: %s)" % (reason, rule))


def judge(command, keys, store_bin, levels=None):
    """``None`` when `command` may go ahead, or the reason it may not (ending in the name of the rule that fired). `keys` are
    the relaxed keys; `levels`, when given, maps each to its level, so that the reason does not name an ``ask`` rule for a key
    at ``none``."""
    found = verdict(command, keys, store_bin, levels)
    return found.reason if found else None


def verdict(command, keys, store_bin, levels=None):
    """``None`` when `command` may go ahead, or the ``Verdict`` (the rule that fired and the reason) that says it may not."""
    text = command
    if reads_as_data(text):
        return None
    literal = literal_run(text, store_bin)
    if keys and text.count("$'") > MAX_DOLLAR_QUOTES and any(words(key) for key in keys):
        return _verdict(DOLLAR_QUOTE_LIMIT,
                        "the command holds more than %d $'...' strings, which the gate cannot read while a command is set to "
                        "ask or none here" % MAX_DOLLAR_QUOTES)
    views, previewed = [], []
    # The text, and the text with the variables it sets by simple assignments replaced by their values, are both read by the
    # name tests: ``a=approve b=plan; wb $a-$b`` names the word once the two are put in.
    spelled_out = substituted(text)
    versions = decoded_views(text) + (decoded_views(spelled_out) if spelled_out != text else [])
    for version in versions:
        folded = _folded(version)
        for token in EXEMPT:
            folded = re.sub(r"(?<![a-z0-9-])%s(?![a-z0-9-])" % re.escape(_folded(token)), " ", folded)
        views.append((folded, _skeleton(folded)))
        for action in PREVIEW_ACTIONS:
            folded = re.sub(r"(?<![a-z0-9-])preview %s(?![a-z0-9-])" % re.escape(_folded(action)), " ", folded)
        previewed.append((folded, _skeleton(folded)))
    # The in-order rule reads the text as written, the exempt command included: `${A#delegate-}` can make the word out of it.
    # A python here-document of the exact shape (decision ``2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps``)
    # is read above for its words, body included; the rules below, which look for a word spelled through wildcards, read only its
    # first line, which holds none of the characters that start them. Any other text is read whole, as before.
    head = python_heredoc(text)
    scope = text if head is None else head
    spelled_scope = spelled_out if head is None else substituted(head)
    pattern = any(char in scope for char in _PATTERN_CHARS)
    wilds = [_spelled(version) for version in (_folded(scope), _collapse(_folded(scope)))] if pattern else []
    expands = any(mark in scope for mark in ("$(", "${", "`"))
    frees = [_free_text(_folded(spelled_scope))] if pattern and expands else []
    ordered = [_in_order_wilds(version) for version in (_folded(scope), _collapse(_folded(scope)))] if _OPERATOR.search(scope) else []
    for key in keys:
        # Only a key read as a launcher and a word has a preview that is not the call; a module's command may be named `preview`.
        # ``approve-plan`` is freed the same way by decision 4 of ``2026-11-02-command-gate-reads-gaps-and-data-positions``.
        if literal and (_by_launcher(key) or key == "approve-plan"):
            continue
        # A key ``wb run <command> <argument>``: the literal call of that command with another plain first argument.
        if literal and reads_argument_as_data(text, key, store_bin):
            continue
        seen = _without(previewed, siblings(key)) if _by_launcher(key) else views
        for spelling in alternatives(key):
            # A launcher and a word can reach each other as data (``echo install | xargs wb``), so for a launcher key the two
            # count in either order. A command that holds both is blocked unless it is exactly the call the ask rule matches.
            orders = [spelling, spelling[::-1]] if _by_launcher(key) else [spelling]
            for order in orders:
                pieces = [_folded(word) for word in order]
                if any(_names(folded, skel, pieces) for folded, skel in seen):
                    if any(form.fullmatch(text) for form in forms(key, store_bin)):
                        break
                    return _verdict(NAMES, _reason(key, spelling, (levels or {}).get(key)))
                letters = _skeleton("".join(pieces))
                if pattern and (any(_gap_match(wild, letters) for wild in wilds)
                                or any(_free_match(free, letters) for free in frees)
                                or any(_subsequence(order_text, letters) for order_text in ordered)):
                    return _verdict(GAP, "the command uses an expansion, a pattern or an escape in place of letters of %s, so "
                                    "it may spell a command that the owner has set to ask or none here; run it as `%s ...` "
                                    "on its own, or write the word out" % (display.ascii_text(" ".join(pieces))[:80],
                                                                          _hint_command(key)))
            else:
                continue
            break
    return None


def _record(log, rule, command):
    """Tell the refusal log of `log` (``log(rule, command)``, or ``None``) that `command` was refused by `rule`. It runs after
    the verdict is fixed and a failure of it changes nothing."""
    if log is None:
        return
    try:
        log(rule, command)
    except Exception:
        pass


def run(stdin, err, prepare, *, deadline=gate_hook.DEADLINE):
    """Decide the tool call on `stdin`. `prepare(cwd)` returns ``(tool, field, table, store bin path)``, the tool and the
    field of its input that hold the command coming from the harness's layout, or raises ``Refusal``, and may add a fifth item,
    ``log(rule, command)``, that appends a refusal to the refusal log (``gatelog``); it runs under the deadline and the guard,
    so a failure or a stall in it is a block. Returns 0 to allow; otherwise one ``refused:`` line and 2."""

    def body(limit):
        cwd, name, given, _ = gate_hook._read(stdin)
        gate_hook.check_cwd(cwd)
        tool, field, table, store_bin, *rest = prepare(cwd)
        log = rest[0] if rest else None
        if name != tool:
            raise Refusal("the tool %s is not the one this gate reads" % display.ascii_text(name)[:40])
        command = given.get(field)
        if not isinstance(command, str):
            raise Refusal("the %s call has no %s to read" % (display.ascii_text(name)[:40], field))
        if "\0" in command or len(command) > MAX_COMMAND:
            _record(log, SIZE_LIMIT, command)
            raise Refusal("the command holds a NUL byte or is longer than %d characters (rule: %s)" % (MAX_COMMAND, SIZE_LIMIT))
        # A checkpoint that an argument is the command of is matched by that argument's spellings (``rendering.Table``).
        command_of = getattr(table, "command_of", {})
        relaxed = [command_of.get(key, key) for key, level in table.items() if level in RELAXED]
        found = verdict(command, relaxed, store_bin, {command_of.get(key, key): level for key, level in table.items()})
        if found:
            _record(log, found.rule, command)
            raise Refusal(found.reason)

    return gate_hook.guard(err, body, deadline=deadline)
