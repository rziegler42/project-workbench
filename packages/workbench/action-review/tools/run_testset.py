#!/usr/bin/env python3
"""Run the dangerous cases of the action-review test set through the real engine and the real ``ask-codex`` bridge.

This tool runs from a checkout of the workbench repository, at a terminal, as the owner:

    python3 -B packages/workbench/action-review/tools/run_testset.py [--codex-dir <absolute path>]

It is the one tool of the shadow that imports the repository: it reuses the scratch-project scaffold of
``test_actionreview_dangerous`` (the real ``safe-git`` through the real launcher, a real Git repository, the real engine),
with the fake bridge of the unit tests replaced by the real ``ask-codex``. It is not copied out of the checkout, and it is
run from a checkout the owner trusts.

What it sends: nothing of the owner's. The 29 cases are the synthetic cases of ``tests/dangerous-cases.json``, whose
SHA-256 is checked against the one written here before anything else is read. Only the cases that reach the model send a
prompt (the two controls and the reviewer-directed message, three of the 29); the others are decided by fixed code and the
bridge is never asked. The tool says so, names the bridge, the model and the Codex directory, and waits for the owner to type
``send 3`` before it starts.

How the model gets its sign-in: each case runs in a scratch project in a temporary home directory, into which the owner's
Codex directory (``~/.codex``, or ``--codex-dir``) is linked. The tool never reads or changes anything in it, and it names
no file of it; the Codex program itself, run by the bridge, may refresh its own sign-in there.

What it records: one row per case in ``testset.jsonl`` of the shadow's store, as the report reads them: the expected
verdict (``approve`` for a control, ``decline`` for every case that must not be approved, a refusal included), what the
engine said, and whether the two differ. A row is written only for a case that ran the way the case file says: the engine did
not fail, it ended with the exit the file expects, and where the file expects the model to be asked, the model was asked. A
refusal that the file expects is a ``decline`` with the check name ``refused``. Any other case leaves no row and is named as not
run with its reason, so a model that was never asked (not signed in, a refused launcher) cannot read as a clean decline. A model
or effort comes from the one rung of the ``action-review`` ladder in the owner's ``review-profiles.json`` (the guarded store;
the project file ``.workbench/review.json`` is read by nothing). A file the engine would refuse, a rung whose bridge is not
``ask-codex`` (the only sign-in this tool puts in place) and a rung with options (``ask-codex`` takes none) end the run before
anything is sent. Exit status: 0 done, 1 a case did
not run or the store failed, 2 not a terminal, a bad argument or a refused setting, 3 a case that must be declined was approved,
130 interrupted.
"""

import hashlib
import json
import os
import sys
import time
import unittest.mock

HERE = os.path.dirname(os.path.realpath(__file__))
MODULE = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(MODULE)))
CASES = os.path.join(MODULE, "tests", "dangerous-cases.json")
# The SHA-256 of the case file the owner reviewed. Changing the cases means changing this, in a commit the owner reads.
CASES_SHA256 = "23b9498ce86996378c91855107754b48a2c7b07ab3d9e1ff567bd9ac6ec79312"
USAGE = "usage: run_testset.py [--codex-dir <absolute path>]"
BRIDGE = "ask-codex"
# The ladder keys the engine accepts and the keys whose ladder holds one rung (`LADDER_KEYS` and `SINGLE_RUNG` in the helper; a test
# compares them). A file the engine would refuse makes every case a refusal, so it ends the run before anything is sent.
LADDER_KEYS = ("plan", "spec", "roadmap", "adr", "action-review", "default")
SINGLE_RUNG = ("action-review",)

sys.path.insert(0, os.path.join(MODULE, "hook"))
import shadow_store as store  # noqa: E402  the store of the shadow, in the checkout beside this tool


def plain(text, limit=200):
    return "".join(char if " " <= char <= "~" else "?" for char in str(text))[:limit]


def read_cases():
    """The cases of the shipped file, or None when its bytes are not the ones this tool was written for."""
    with open(CASES, "rb") as handle:
        data = handle.read()
    if hashlib.sha256(data).hexdigest() != CASES_SHA256:
        return None
    return json.loads(data.decode("utf-8"))["cases"]


def kit():
    """The checkout's profile reader (``wbkit.profiles``), imported when it is needed so that a copy of this tool outside a checkout
    still reaches its own message."""
    try:
        from workbench.wbkit import profiles
    except ImportError:
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        from workbench.wbkit import profiles
    return profiles


def project_setting():
    """The fields of the one rung of the owner's ``action-review`` ladder (``bridge``, and ``model``, ``effort`` and ``options`` when
    it has them), read by the kit as the engine reads it. Raises the kit's ``ProfileError`` for a file or a ladder the engine would
    refuse; nothing in the project is read."""
    profiles = kit()
    found = profiles.read(LADDER_KEYS, SINGLE_RUNG)
    _, profile = profiles.for_round(found, "action-review", 1, False)
    setting = {"bridge": profile.bridge}
    if profile.model is not None:
        setting["model"] = profile.model
    if profile.effort is not None:
        setting["effort"] = profile.effort
    if profile.options:
        setting["options"] = dict(profile.options)
    return setting


def scaffold():
    """The scratch-project scaffold of the unit tests, imported from this checkout."""
    for path in (os.path.join(MODULE, "tests"), ROOT):
        if path not in sys.path:
            sys.path.insert(0, path)
    import test_actionreview_dangerous as dangerous
    return dangerous


def real_run_class(codex_dir, setting):
    dangerous = scaffold()

    class RealRun(dangerous.EndToEnd):
        BRIDGE = "ask-codex"
        BRIDGE_HELPER = "helper/ask-codex"
        BRIDGE_KIT = 1

        def bridge_module(self):
            package = os.path.join(dangerous.PACKAGE, "ask-codex")
            with open(os.path.join(package, "module.json"), encoding="utf-8") as handle:
                declared = json.load(handle)
            with open(os.path.join(package, "helper", "ask-codex"), "rb") as handle:
                real = handle.read()
            fields = {key: value for key, value in declared.items() if key not in ("name", "version", "description")}
            fields["provides"] = ["p:model-bridge"]  # the unprefixed capability is the first-party package's
            return fields, {"helper/ask-codex": real}

        def review_setting(self):
            return dict(setting)

        def setUp(self):
            super().setUp()
            os.symlink(codex_dir, os.path.join(self.home, ".codex"))
            self.asks = []
            real = self.helper.ask_bridge

            def counting(*args, **kwargs):
                self.asks.append(1)
                return real(*args, **kwargs)

            patch = unittest.mock.patch.object(self.helper, "ask_bridge", counting)
            patch.start()
            self.addCleanup(patch.stop)

    return RealRun


def run_case(case, codex_dir, setting):
    """``(exit code, standard output, times the model was asked)`` for one case, in a fresh scratch project."""
    run = real_run_class(codex_dir, setting)("run_case")
    try:
        run.setUp()  # inside the try: a project that fails half-built still has its patches and directories undone
        for step in case["setup"]:
            run.setup_step(step)
        code, out, _, _ = run.run_case(dict(case, setup=[]))
        return code, out, len(run.asks)
    finally:
        run.doCleanups()


def not_recorded(case, code, asked):
    """Why a case leaves no row, or None when it ran the way the case file says: the engine did not fail, it ended with the
    exit the file expects, and where the file expects the model to be asked, the model was asked. A case that fails these is a
    case that did not run as the test set means it, and a row would only read as a clean decline."""
    if code not in (0, 1):
        return "the engine failed (exit %s)" % code
    if code != case["expect"].get("exit"):
        return "the engine ended with exit %d where the file expects %s" % (code, case["expect"].get("exit"))
    if case["expect"].get("bridge_asked") and not asked:
        return "the model was not asked"
    return None


def judged(case, code, out):
    """``(expected, verdict, failed checks)`` as the report reads them, for a case that `not_recorded` let through: a refusal
    (exit 1, which the file expected) is a ``decline`` with the check name ``refused``."""
    expected = "approve" if case["expect"].get("verdict") == "approve" else "decline"
    if code == 0:
        body = json.loads(out)
        return expected, body["verdict"], list(body["failed_checks"])
    return expected, "decline", ["refused"]


def run(argv, stdin, stdout, stderr, home):
    codex_dir = os.path.join(home, ".codex")
    if argv:
        if len(argv) != 2 or argv[0] != "--codex-dir" or not os.path.isabs(argv[1]):
            stderr.write(USAGE + "\n")
            return 2
        codex_dir = argv[1]
    if not (stdin.isatty() and stdout.isatty()):
        stderr.write("run_testset.py sends prompts to a model for you and runs only at a terminal\n")
        return 2
    if not (os.path.isdir(os.path.join(ROOT, "workbench")) and os.path.isdir(os.path.join(ROOT, "tests"))):
        stderr.write("run_testset.py runs from a checkout of the workbench repository\n")
        return 2
    cases = read_cases()
    if cases is None:
        stderr.write("%s is not the shipped case file this tool was written for\n" % plain(CASES))
        return 2
    if not os.path.isdir(codex_dir):
        stderr.write("the Codex directory %s does not exist; sign in to Codex first or name it with --codex-dir\n"
                     % plain(codex_dir))
        return 2
    try:
        setting = project_setting()
    except kit().ProfileError as exc:
        stderr.write("%s; nothing was sent\n" % plain(exc, 300))
        return 2
    if setting["bridge"] != BRIDGE:
        stderr.write("the action-review rung of review-profiles.json names the bridge %s and this tool can only run %s; nothing was "
                     "sent\n" % (plain(setting["bridge"], 60), BRIDGE))
        return 2
    if setting.get("options"):
        stderr.write("the action-review rung of review-profiles.json passes options and %s takes none, so every case that asks the "
                     "model would be refused; nothing was sent\n" % BRIDGE)
        return 2
    sends = sum(1 for case in cases if case["expect"].get("bridge_asked"))
    stdout.write("Test set of the action-review shadow\n")
    stdout.write("  %d cases, all synthetic: the shipped dangerous cases (hash checked). Nothing of yours is used or sent.\n"
                 % len(cases))
    stdout.write("  %d of them are expected to send a prompt to the model through the bridge %s (model %s, effort %s),\n"
                 "  using your Codex sign-in in %s; the other %d are decided by fixed code and send nothing.\n"
                 % (sends, BRIDGE, setting.get("model", "the bridge's default"), setting.get("effort", "the bridge's default"),
                    plain(codex_dir), len(cases) - sends))
    stdout.write("  Each case runs in a scratch project in a temporary home; your Codex directory is linked into it.\n"
                 "  This tool does not read or change it, but the Codex program itself may refresh its sign-in there.\n")
    stdout.write('Type "send %d" to go on; anything else stops: ' % sends)
    stdout.flush()
    if stdin.readline().rstrip("\n") != "send %d" % sends:
        stdout.write("\nNothing was sent.\n")
        return 0
    stdout.write("Running the cases (one mark each, a dot when it is as expected): ")
    stdout.flush()
    results, not_run = [], []
    try:
        for case in cases:
            try:
                code, out, asked = run_case(case, codex_dir, setting)
                why = not_recorded(case, code, asked)
                if why is None:
                    expected, verdict, failed = judged(case, code, out)
            except Exception:
                why = "the scratch project could not be built or run"
            if why is not None:
                not_run += [(case["id"], why)]
                stdout.write("?")
                stdout.flush()
                continue
            row = {"case": case["id"], "ts": store.now(), "expected": expected, "verdict": verdict, "failed_checks": failed,
                   "mismatch": expected != verdict, "bridge": BRIDGE, "model": setting.get("model"),
                   "effort": setting.get("effort")}
            try:
                store.append("testset.jsonl", row, home)
            except store.StoreError as exc:
                stdout.write("\n")
                stderr.write("the row could not be recorded: %s\n" % plain(exc))
                return 1
            results += [(case, row, asked, code)]
            stdout.write("!" if row["mismatch"] else ".")
            stdout.flush()
    except KeyboardInterrupt:
        stdout.write("\nInterrupted; %d rows were written and are whole.\n" % len(results))
        return 130
    stdout.write("\n\n")
    approves = [row for _, row, _, _ in results if row["expected"] == "decline" and row["verdict"] == "approve"]
    declines = [row for _, row, _, _ in results if row["expected"] == "approve" and row["verdict"] == "decline"]
    for row in approves:
        stdout.write("FALSE APPROVE: %s was approved and must be declined\n" % plain(row["case"], 80))
    if approves:
        stdout.write("\n")
    for case, row, asked, code in results:
        # A recorded case ended with the exit the file expects (`not_recorded`); for a verdict it should also be decided by the
        # checks the file names. Another set is a drift between the engine and the file, shown here though it is no false approve.
        same = code != 0 or list(case["expect"].get("failed_checks", [])) == row["failed_checks"]
        mark = "MISMATCH" if row["mismatch"] else ("ok" if same else "differs")
        stdout.write("  %-8s %s: %s%s\n" % (mark, plain(row["case"], 80), row["verdict"],
                                           " (%s)" % ", ".join(row["failed_checks"]) if row["failed_checks"] else ""))
        if bool(asked) != bool(case["expect"].get("bridge_asked")):
            stdout.write("           the model %s asked; the file expects the opposite\n" % ("was" if asked else "was not"))
    asks = sum(asked for _, _, asked, _ in results)
    stdout.write("\ncases run %d of %d; mismatches %d; false approves %d; false declines %d; the model was asked %d times\n"
                 % (len(results), len(cases), sum(row["mismatch"] for _, row, _, _ in results), len(approves), len(declines), asks))
    if not_run:
        stdout.write("not run: %s\n" % ", ".join("%s (%s)" % (plain(ident, 80), plain(why, 120)) for ident, why in not_run))
    if not_run:
        stdout.write("Some cases did not run, so the test set is incomplete: fix the cause and run the test set again before "
                     "you read the report.\n")
    else:
        stdout.write("Now run the report to see the cutover line.\n")
    if approves:
        return 3
    return 1 if not_run else 0


def main(argv, stdin, stdout, stderr, home=None):
    """Run the tool and return its exit status (see the docstring of the file)."""
    try:
        return run(argv, stdin, stdout, stderr, home if home is not None else os.path.expanduser("~"))
    except KeyboardInterrupt:
        try:
            stdout.write("\nInterrupted.\n")
        except (OSError, ValueError):
            pass
        return 130
    except (OSError, ValueError) as exc:
        stderr.write("the tool stopped on %s\n" % type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout, sys.stderr))
