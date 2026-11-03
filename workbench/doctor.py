"""``doctor``: report what the permission configuration of this project does not do as it says, and what it does that is
dangerous. Read-only, and safe for an agent to run.

Plan ``2026-11-02-permission-system-consistency``, increment L (criterion 10), under the decision
``2026-11-02-one-permission-registry-and-key-model``. The command decides nothing and changes nothing. It prints one line per
finding, a key and a path and never a value, strictest first::

    problem: <area>: <text>    the configuration does not do what it says; the exit code is 1
    risk: <area>: <text>       it does what it says, and what it says is dangerous
    note: <area>: <text>       something the owner should see, such as a prompt the project declares or the refusal counts
    doctor found <n> problems and <m> risks

The checks, each a function of its input so that a test can feed it a made-up one:

* ``settings``: a setting that reads other than it was set (the loader's problems and the notes of ``settings.effective``);
* ``floor``: the personal copy of the compiled floor lacks a stop or names one the floor does not hold (the compiled floor
  applies whatever the copy says);
* a governing key set looser than its shipped default (the third danger class of the decision), and every prompt a module
  declares as a minimum (``asks``);
* ``package``: a package tree that differs from its release, with the first place and the command that clears it;
* ``rendering``: the harness's permissions file differs from the record, was rendered from another table than the settings
  give now (``check`` reads the same), is missing, or cannot be read as a regular file (a link, a hard link, a special file, a
  directory, too large, not JSON); and a record that is missing for an attached harness (a risk: a harness that provides no
  permissions has none on purpose);
* ``hook``: a hook of the harness runs ``wb`` and ``wb`` does not resolve, or resolves to something other than the guarded
  store's launcher;
* ``allow``: an ``allow`` rule in a settings file of the harness that covers a key the registry does not class as reading;
* ``skill``: an installed skill or agent that says to never run a key the registry offers at ``ask`` or ``none``;
* ``gate-log``: the refusal counts of the gate per rule, and a log that is full.

Not read here: a plan approval that changed since it was given (``wb plan-status`` says it, plan by plan), the spellings that a
document uses and the generated rules do not cover (decision 6 of the record), and the harness's own global configuration
(outside this project).
"""

import collections
import fnmatch
import json
import os
import re
import shutil
import stat

from . import (__version__, approvalcmd, check, declarations, firstparty, floor, gatelog, harnesses, installed, levels,
               localmanifest, manifest, projectfs, rendering, rules, settings, target)
from .wbkit import display, safefs

Finding = collections.namedtuple("Finding", "severity line")
PROBLEM, RISK, NOTE = "problem", "risk", "note"
MAX_LINE = 400
LISTED = 40  # lines of one area that a severity lists before it says how many more
MAX_RULES_LISTED = 6  # rule names of the gate log that its note lists
MAX_TEXT_FILES = 400
MAX_DIRECTORIES = 2000
MAX_TEXT_BYTES = 64 * 1024
MAX_SETTINGS_BYTES = 1024 * 1024
_ORDER = {PROBLEM: 0, RISK: 1, NOTE: 2}


def _name(text, limit=96):
    return display.ascii_text(text)[:limit]


def _quoted(text, limit=64):
    """`text` as a quoted ASCII string, cut at `limit` characters inside the quotes, for a name that someone else chose (a module
    directory, a floor id): it is shown as data and cannot read as a sentence of the report."""
    shown = repr(display.ascii_text(text))
    return shown if len(shown) <= limit + 2 else shown[:limit + 1] + "..." + shown[0]


# --- the checks -----------------------------------------------------------------------------------------------------------


def settings_findings(loaded, effective):
    """A setting that reads other than it was set: the loader's problems and the notes of ``settings.effective``."""
    return [Finding(PROBLEM, "problem: settings: %s" % text) for text in list(loaded.problems) + list(effective.notes)]


def floor_findings(raw):
    """The personal copy of the compiled floor (`raw` is the ``floor`` entry of the settings file, or ``None`` when the file
    has none) against the compiled one. The compiled floor applies whatever the copy says."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        return [Finding(RISK, "risk: floor: the personal floor entry is not a list of ids; the compiled floor still applies")]
    ids = [item for item in raw if isinstance(item, str)]
    found = []
    for stop in floor.FLOOR:
        if stop.id not in ids:
            found.append(Finding(RISK, "risk: floor: the personal copy lacks %s; the compiled floor still applies" % stop.id))
    compiled = {stop.id for stop in floor.FLOOR}
    for item in sorted(set(ids) - compiled):
        found.append(Finding(NOTE, "note: floor: the personal copy names %s, which the compiled floor does not hold"
                             % _quoted(item, 64)))
    return found


def relaxed_findings(keys, now):
    """A key of the third danger class (``governs``) set looser than its shipped default. `now` maps a key to its level."""
    found = []
    for name, level in sorted(now.items()):
        key = keys.get(name)
        if key is None or key.klass != levels.GOVERNS or level not in levels.LEVELS:
            continue
        if levels.LEVELS.index(level) > levels.LEVELS.index(key.default):
            found.append(Finding(RISK, "risk: %s is set to %s (class governs; shipped default %s)"
                                 % (_name(name), level, key.default)))
    return found


def minimum_findings(keys):
    """Every prompt a module declares as a minimum (``asks``): the level of its key does not change it."""
    return [Finding(NOTE, "note: %s carries a prompt that the project declares as a minimum; its level does not change it"
                    % _name(name)) for name, key in sorted(keys.items()) if key.asks]


def package_findings(distribution=None):
    """A package tree that differs from its release, with the first place and what clears it (``harnesses.lock_cause``)."""
    cause = harnesses.lock_cause(distribution)
    if cause is None:
        return []
    sentence, fix_first = cause
    return [Finding(PROBLEM, "problem: package: %s; %s" % (sentence, harnesses.lock_advice(fix_first)))]


def _commands(node, found, depth=0):
    """The ``command`` strings of the hook entries below `node`."""
    if depth > 8:
        return
    if isinstance(node, dict):
        if isinstance(node.get("command"), str):
            found.append(node["command"])
        for value in node.values():
            _commands(value, found, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _commands(value, found, depth + 1)


def hook_findings(documents, which, store_bin):
    """A hook that runs ``wb`` when ``wb`` does not resolve (the hook cannot run, and a hook that cannot run refuses every call it
    guards), or resolves to something other than the guarded store's launcher. `documents` maps a file label to its parsed JSON."""
    found = []
    for label, document in sorted(documents.items()):
        commands = []
        if isinstance(document, dict):
            _commands(document.get("hooks"), commands)
        if not any(command.split(" ", 1)[0] == "wb" for command in commands):
            continue
        resolved = which("wb")
        if resolved is None:
            found.append(Finding(PROBLEM, "problem: hook: %s runs `wb`, which is not found on PATH, so the hook cannot run and "
                                 "every call it guards is refused" % _name(label)))
        elif os.path.realpath(resolved) != os.path.realpath(store_bin):
            found.append(Finding(RISK, "risk: hook: %s runs `wb`, and the one on PATH is not the guarded store's launcher"
                                 % _name(label)))
    return found


def _covered(key, pattern):
    """Whether the allow `pattern` covers the command of `key` in some spelling, with or without arguments."""
    words = levels.command_words(key)
    if not words:
        return False
    for spelling in rules.SPELLINGS:
        text = "%s %s" % (spelling, " ".join(words))
        if fnmatch.fnmatchcase(text, pattern) or fnmatch.fnmatchcase(text + " x", pattern):
            return True
    return False


def allow_findings(keys, documents):
    """An ``allow`` rule that covers a key the registry does not class as reading. A rule that covers one key names it; a broader
    one (``Bash(wb *)``) is one finding that says how many it covers. The text of a rule that covers none is never printed."""
    dangerous = sorted(name for name, key in keys.items() if key.klass != levels.READS and levels.command_words(name))
    found = []
    for label, document in sorted(documents.items()):
        permissions = document.get("permissions") if isinstance(document, dict) else None
        allow = permissions.get("allow") if isinstance(permissions, dict) else None
        if not isinstance(allow, list):
            continue
        reported = set()
        for rule in allow:
            if not isinstance(rule, str):
                continue
            match = re.fullmatch(r"Bash\((.*)\)", rule, re.DOTALL)
            if rule == "Bash":  # a bare tool name allows every command
                pattern = "*"
            elif match:
                pattern = match.group(1).replace(":*", " *")
            else:
                continue
            covered = [name for name in dangerous if _covered(name, pattern)]
            if len(covered) == 1 and covered[0] not in reported:
                reported.add(covered[0])
                found.append(Finding(PROBLEM, "problem: allow: %s allows `wb %s` (class %s)" % (
                    _name(label), " ".join(levels.command_words(covered[0])), keys[covered[0]].klass)))
            elif len(covered) > 1:
                found.append(Finding(PROBLEM, "problem: allow: %s: the rule `%s` covers %d dangerous keys, the first `wb %s`"
                                     % (_name(label), _name(rule, 60), len(covered), " ".join(levels.command_words(covered[0])))))
    return found


# One reader of "never run <key>" in a skill or agent, used by ``wb doctor`` and by the drift test of the plan.
_NEVER = re.compile(r"(?i)\b(?:never|do not|don't)\s+run\b")


def groups(text):
    """The paragraphs and list items of `text`, each as one string."""
    current, found = [], []
    for line in text.splitlines():
        if not line.strip() or re.match(r"\s*(?:- |\d+\. )", line):
            if current:
                found.append(" ".join(current))
            current = [line.strip()] if line.strip() else []
        else:
            current.append(line.strip())
    if current:
        found.append(" ".join(current))
    return found


def named_token(key):
    """How a skill names `key`: the argument of ``wb run <command> <argument>`` (in backticks), the whole of ``wb <word>``
    (in backticks), or a checkpoint's name (in backticks or bare, but not inside a longer name such as
    ``delegate-approve-plan``)."""
    parts = key.split(" ")
    return parts[-1] if key.startswith("wb run ") else key


def names_key(group, key):
    token = named_token(key)
    if "`%s`" % token in group:
        return True
    return " " not in key and re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(token), group) is not None


def _label(path):
    parts = path.split(os.sep)
    return "%s/%s" % (parts[0], parts[-2] if parts[-1] == "SKILL.md" else os.path.splitext(parts[-1])[0])


def skill_findings(keys, texts):
    """A skill or agent (`texts` is ``(relative path, text)``) that says never to run a key the registry offers at ``ask`` or
    ``none`` to an owner."""
    relaxed = {name: key for name, key in keys.items()
               if not key.agent and (levels.ASK in key.offers or levels.NONE in key.offers)}
    found = []
    for path, text in texts:
        for group in groups(text):
            if not _NEVER.search(group):
                continue
            for name in sorted(relaxed):
                if names_key(group, name):
                    found.append(Finding(PROBLEM, "problem: skill: %s says never run `%s`, which the registry offers at ask or none"
                                         % (_quoted(_label(path), 80), named_token(name))))
    return found


def installed_texts(root):
    """``(path, text)`` of the neutral skills and agents installed below `root` (``.workbench/workbench/<module>/harness/neutral``),
    read without following a link in any directory or file, at most ``MAX_TEXT_FILES`` files of ``MAX_TEXT_BYTES`` each in at
    most ``MAX_DIRECTORIES`` directories. The path is relative to ``.workbench/workbench``."""
    base = os.path.join(root, ".workbench", "workbench")
    found, directories = [], 0
    if not _real_dir(os.path.join(root, ".workbench")) or not _real_dir(base):
        return []
    try:
        modules = sorted(os.listdir(base))
    except OSError:
        return []
    for module in modules:
        top = os.path.join(base, module, "harness", "neutral")
        if not all(_real_dir(part) for part in (os.path.join(base, module), os.path.dirname(top), top)):
            continue
        stack = [top]
        while stack and len(found) < MAX_TEXT_FILES and directories < MAX_DIRECTORIES:
            here = stack.pop()
            directories += 1
            try:
                names = sorted(os.listdir(here))
            except OSError:
                continue
            for name in names:
                full = os.path.join(here, name)
                try:
                    mode = os.lstat(full).st_mode
                except OSError:
                    continue
                if stat.S_ISDIR(mode):
                    stack.append(full)
                elif stat.S_ISREG(mode) and name.endswith(".md") and len(found) < MAX_TEXT_FILES:
                    text = _read_text(full)
                    if text is not None:
                        found.append((os.path.relpath(full, base), text))
    return sorted(found)


def _real_dir(path):
    """Whether `path` is a directory itself and not a link to one."""
    try:
        return stat.S_ISDIR(os.lstat(path).st_mode)
    except OSError:
        return False


def _read_text(path):
    """The text of the regular file `path`, opened without following a link and without blocking, or ``None`` when it is not a
    regular file, cannot be read or is longer than ``MAX_TEXT_BYTES``."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            return None
        data = os.read(descriptor, MAX_TEXT_BYTES + 1)
    except OSError:
        return None
    finally:
        os.close(descriptor)
    return data.decode("utf-8", "replace") if len(data) <= MAX_TEXT_BYTES else None


_LOG_LINE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\t([a-z][a-z-]{0,39})\t[0-9a-f]{12}")


def log_findings(data):
    """The refusal counts per rule of the gate log (``gatelog``), the lines that are not in its format counted and never printed,
    and a log that is full: the gate stops appending at ``MAX_BYTES``, so the owner rotates it by hand."""
    if not data:
        return []
    counts, strange = collections.Counter(), 0
    for line in data.decode("utf-8", "replace").split("\n"):
        if not line:
            continue
        match = _LOG_LINE.fullmatch(line)
        if match:
            counts[match.group(1)] += 1
        else:
            strange += 1
    found = []
    if counts or strange:
        names = sorted(counts)
        listed = ", ".join("%s %d" % (rule, counts[rule]) for rule in names[:MAX_RULES_LISTED])
        if len(names) > MAX_RULES_LISTED:
            listed += ", and %d more" % (len(names) - MAX_RULES_LISTED)
        text = "note: gate-log: %d refusals (%s)" % (sum(counts.values()), listed)
        if strange:
            text += "; %d lines are not in the log's format" % strange
        found.append(Finding(NOTE, text))
    if len(data) > gatelog.MAX_BYTES - gatelog.MAX_LINE:  # the writer refuses a line that would pass MAX_BYTES, so a full log stops short
        found.append(Finding(RISK, "risk: gate-log: full (%d bytes); new refusals are not recorded, and the owner rotates it by hand"
                             % len(data)))
    return found


# --- the report -----------------------------------------------------------------------------------------------------------


def _area(line):
    """The area of a finding line (``problem: <area>: <text>``), or ``""`` for a line of a key (``risk: <key> is set to ...``)."""
    parts = line.split(": ", 2)
    return parts[1] if len(parts) > 2 and " " not in parts[1] else ""


def report(findings):
    """``(lines, problems, risks)``: the findings, one bounded ASCII line each, problems first, then the summary line. A severity
    lists at most ``LISTED`` lines of one area and then says how many more there are, so that a flood of one kind (the agent can
    write the files it is read from) cannot push the others and the summary out of sight; the counts are of every finding."""
    unique = sorted(set(findings), key=lambda item: (_ORDER[item.severity], item.line))
    text = {PROBLEM: [], RISK: [], NOTE: []}
    seen = collections.Counter()
    for item in unique:
        area = _area(item.line)
        seen[(item.severity, area)] += 1
        if seen[(item.severity, area)] <= LISTED:
            text[item.severity].append(display.ascii_text(item.line)[:MAX_LINE])
    for (severity, area), count in sorted(seen.items()):
        if count > LISTED:
            text[severity].append("%s: %sand %d more" % (severity, area + ": " if area else "", count - LISTED))
    problems = sum(1 for item in unique if item.severity == PROBLEM)
    risks = sum(1 for item in unique if item.severity == RISK)
    text = text[PROBLEM] + text[RISK] + text[NOTE]
    text.append("doctor found %s and %s" % ("%d problem%s" % (problems, "" if problems == 1 else "s") if problems else "no problems",
                                            "%d risk%s" % (risks, "" if risks == 1 else "s") if risks else "no risks"))
    return text, problems, risks


# --- the command ----------------------------------------------------------------------------------------------------------


def _raw_floor(guarded):
    """The ``floor`` entry of the personal settings file, or ``None`` when the file is missing, damaged or has none."""
    try:
        if guarded.kind(settings.SETTINGS) != "file":
            return None
        document = declarations.parse_json(guarded.read(settings.SETTINGS))
    except (safefs.SafeFsError, ValueError, OSError):
        return None
    return document.get("floor") if isinstance(document, dict) else None


def _read_document(writer, rel, required=False):
    """``(document, finding)`` for the settings file `rel` of the harness: the parsed JSON, or a problem when the file cannot be
    read as a regular file (a link, a special file, a hard link, a directory: the harness may still read what doctor does not),
    is too large or is not JSON. A file that is missing is a problem when it is `required` (the permissions file the record names:
    every deny rule it held is gone) and nothing otherwise (the shared file, which the harness may create later). The file is one
    the agent can write."""
    shown = _name(rel)
    try:
        state = writer.read_file(rel)
    except (safefs.SafeFsError, OSError):
        return None, Finding(PROBLEM, "problem: rendering: %s cannot be read as a regular file (a link, a hard link, a special file "
                             "or a directory), so no rule in it was checked and the harness may still read it" % shown)
    if state is None:
        if required:
            return None, Finding(PROBLEM, "problem: rendering: %s is missing, so the rules the record says were rendered into it "
                                 "are gone (wb rerender writes it again)" % shown)
        return None, None
    if len(state.data) > MAX_SETTINGS_BYTES:
        return None, Finding(PROBLEM, "problem: rendering: %s is larger than %d bytes, so no rule in it was checked"
                             % (shown, MAX_SETTINGS_BYTES))
    try:
        return json.loads(state.data.decode("utf-8")), None
    except (ValueError, UnicodeDecodeError, RecursionError):
        return None, Finding(PROBLEM, "problem: rendering: %s is not readable as JSON (damaged, or nested too deeply), so no rule "
                             "in it was checked" % shown)


def _read_gate_log(guarded):
    kind = guarded.kind(gatelog.LOG)
    if kind is None:
        return None
    if kind != "file":
        raise safefs.SafeFsError("the gate log is not a regular file")
    return guarded.read(gatelog.LOG)


def _gate_log(guarded):
    """``(data, finding)``: the log, or a risk when it cannot be read as a regular file within the store's size limit (the gate
    then cannot append to it either)."""
    try:
        return _read_gate_log(guarded), None
    except (safefs.SafeFsError, OSError):
        return None, Finding(RISK, "risk: gate-log: cannot be read as a regular file within the store's size limit, so refusals "
                             "may not be recorded in it")


def _registry(guarded, root):
    """``(keys, loaded, effective, findings)``: the registry and the settings as the installed modules and the owner's file give
    them. A project with no process module is read with none; a registry that cannot be built is a problem."""
    try:
        _, _, found = approvalcmd.installed_modules(root)
    except approvalcmd.ApprovalError:
        found = []
    process = [item for item in found if item.module.type == "process"]
    checkpoints = process[0].module.checkpoints if len(process) == 1 else ()
    caps = process[0].module.caps if len(process) == 1 else ()
    commands = [levels.command_entry(command) for item in found for command in item.module.commands]
    loaded = settings.load(guarded)
    try:
        return (levels.registry(checkpoints, commands), loaded, settings.effective(loaded, checkpoints, caps, commands), [])
    except levels.RegistryError as exc:
        return (levels.registry(), loaded, None,
                [Finding(PROBLEM, "problem: registry: the installed modules do not give each owner-run command one key: %s"
                         % _name(str(exc), 200))])


def examine(guarded, writer, root, distribution=None, which=None):
    """The findings for the project `writer` holds at `root`. Reads only."""
    which = which or shutil.which
    keys, loaded, effective, found = _registry(guarded, root)
    found = list(found)
    if effective is not None:
        found += settings_findings(loaded, effective)
        found += relaxed_findings(keys, effective.levels)
    else:
        found += [Finding(PROBLEM, "problem: settings: %s" % text) for text in loaded.problems]
    found += floor_findings(_raw_floor(guarded))
    found += minimum_findings(keys)
    found += package_findings(distribution or firstparty.default_distribution())
    found += skill_findings(keys, installed_texts(root))
    data, trouble = _gate_log(guarded)
    found += log_findings(data) + ([trouble] if trouble else [])
    try:
        project = manifest.project_id(installed.read(writer, __version__).document["seed"])
    except (installed.InstalledError, manifest.ManifestError, KeyError):
        return found
    record = rendering.read(guarded, project)
    drift, stale = check.rendering_drift(guarded, writer, root)
    for text in list(drift) + list(stale):
        found.append(Finding(PROBLEM, "problem: rendering: %s" % text.removeprefix("rendering: ")))
    if record is None:
        try:
            recorded = localmanifest.read(writer)
        except localmanifest.LocalManifestError:
            recorded = None
        if recorded and recorded.get("harness"):
            # A harness that provides no permissions has no record on purpose, and the layout facts do not say which it is, so this
            # is a risk that says "if": `wb rerender` writes the record of a harness that renders permissions.
            found.append(Finding(RISK, "risk: rendering: no valid rendering record for the attached harness %s; if it renders "
                                 "permissions, its rules were not checked and a key at ask or none reads as block "
                                 "(wb rerender writes the record)" % _quoted(recorded["harness"], 40)))
    else:
        documents = {}
        for rel, required in ((record.get("file"), True), ((record.get("shared") or {}).get("path"), False)):
            if isinstance(rel, str) and rel not in documents:
                document, trouble = _read_document(writer, rel, required)
                if trouble:
                    found.append(trouble)
                if document is not None:
                    documents[rel] = document
        store_bin = os.path.join(os.path.realpath(guarded.root), "bin", "wb")
        found += hook_findings(documents, which, store_bin)
        found += allow_findings(keys, documents)
    return found


def run(guarded, command, out, err, distribution=None, which=None):
    """Print the report and return the exit code: 0 for no problem (a risk or a note never fails), 1 for a problem or a refusal."""
    try:
        with target.open_target(command.target, guarded.root) as held:
            if held.state != "existing":
                err.write("refused: the target is not an existing project\n")
                return 1
            writer = projectfs.Writer(held)
            try:
                installed.read(writer, __version__)
            except (installed.InstalledError, manifest.ManifestError) as exc:
                err.write("refused: not an installed project: %s\n" % display.clean(str(exc))[:200])
                return 1
            found = examine(guarded, writer, held.path, distribution, which)
    except target.TargetError as exc:
        return target.write_refusal(err, exc)
    except safefs.SafeFsError as exc:
        err.write("refused: %s\n" % display.clean(str(exc)))
        return 1
    text, problems, _ = report(found)
    try:
        out.write("\n".join(text) + "\n")
        out.flush()
    except BrokenPipeError:
        pass
    return 1 if problems else 0
