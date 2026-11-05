"""``settings``: print the checkpoint and cap values that apply to this project.

The installer reads the project's one process module's verified declaration (``approvalcmd.installed_modules``,
the same reading ``approve-plan`` uses), the owner's personal settings from the guarded store, and prints what
``settings.effective`` makes of the two (``docs/specs/installer-interface.md``, "``settings`` and ``gate``")::

    checkpoint <name>: stop|delegate     one per declared checkpoint, in declaration order
    cap <name>: <n>                      one per declared cap, in declaration order
    level <key>: <level>                 one per key the installer knows: the checkpoints, the owner-run commands, the
                                         agent-safe actions, then each argument an installed command declares
    key <key>: class=<class> offers=<levels>   one per level line, after them: the key's danger class (reads, project or
                                         governs) and the levels the owner may set it to, strictest first (the registry's facts)
    profile: <name>                      only when the owner's settings name a risk profile (version 3)
    profiled <key>: <level>              one per key the profile moved from its shipped default, in the order of the level lines
    translated <key>: <word> read as <level>   one per checkpoint word the table does not override, read as a level
    settings: <text>                     one per problem in the owner's settings

Nothing is started, written or approved here; the owner's settings are data. Exit 0 printed, 1 refused (a
``refused:`` line on standard error and nothing on standard output), 2 usage.
"""

import os

from . import approvalcmd, levels, settings
from .wbkit import display

USAGE = "usage: wb settings\n"


def _refuse(err, text):
    err.write("refused: %s\n" % display.clean(text))
    return 1


def run(guarded, tokens, out, err, *, cwd=None):
    if tokens:
        err.write(USAGE)
        return 2
    try:
        start = cwd if cwd is not None else os.getcwd()
    except OSError as exc:
        return _refuse(err, "the working directory cannot be read: %s" % (exc.strerror or "unknown error"))
    try:
        _, _, found = approvalcmd.installed_modules(start)
    except approvalcmd.ApprovalError as exc:
        return _refuse(err, str(exc))
    process = [item for item in found if item.module.type == "process"]
    if not process:
        return _refuse(err, "no installed module is a process module; there is nothing to set")
    if len(process) > 1:
        return _refuse(err, "more than one installed module is a process module: %s"
                       % ", ".join(sorted("%s/%s" % (item.package, item.module.name) for item in process)))
    module = process[0].module
    loaded = settings.load(guarded)
    owner_commands = [levels.command_entry(command) for item in found for command in item.module.commands]
    try:
        effective = settings.effective(loaded, module.checkpoints, module.caps, owner_commands)
    except levels.RegistryError as exc:
        return _refuse(err, "the installed modules do not give each owner-run command one key: %s" % exc)
    for name in module.checkpoints:
        out.write("checkpoint %s: %s\n" % (name, effective.checkpoints[name]))
    for cap in module.caps:
        out.write("cap %s: %d\n" % (cap.name, effective.caps[cap.name]))
    for name, level in effective.levels.items():
        out.write("level %s: %s\n" % (name, level))
    # What each key is and offers (the registry's facts): its danger class and the levels the owner may set it to.
    keys = levels.registry(module.checkpoints, owner_commands)
    for name in effective.levels:
        if name in keys:
            out.write("key %s: class=%s offers=%s\n" % (name, keys[name].klass, ",".join(keys[name].offers)))
    if loaded.profile is not None:
        out.write("profile: %s\n" % loaded.profile)
        for name, level in effective.profiled:
            out.write("profiled %s: %s\n" % (name, level))
    if loaded.delegate_profiles is not None:
        reading = loaded.delegate_profiles
        out.write("delegate-profiles %s: %s\n" % (settings.APPROVE_PLAN, reading if isinstance(reading, str) else ", ".join(reading)))
    for name, word, level in effective.translated:
        out.write("translated %s: %s read as %s\n" % (name, word, level))
    for text in list(loaded.problems) + list(effective.notes):
        out.write("settings: %s\n" % display.clean(text))
    return 0
