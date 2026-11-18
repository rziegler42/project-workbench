"""A project, a fake `claude` outside it, and the helper loaded to be called in this process.

The fake is a script that records its arguments, environment, working directory and standard input, and then does
what a control file beside it says: print a result object or raw text, print error text, exit with a code, hang,
or write too much. No test starts a real `claude`."""

import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock

from tests import support_helpers

FAKE = """#!{python}
import json, os, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]
data = sys.stdin.buffer.read()
control = json.load(open(os.path.join(here, "control.json")))
record = {{"argv": argv, "env": dict(os.environ), "cwd": os.getcwd(), "stdin": data.decode("utf-8", "replace")}}
with open(os.path.join(here, "calls.jsonl"), "a") as handle:
    handle.write(json.dumps(record) + "\\n")
if control.get("orphan"):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"])
    open(os.path.join(here, "pids"), "w").write(str(child.pid))
    sys.exit(0)
if control.get("hang"):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"])
    open(os.path.join(here, "pids"), "w").write(str(child.pid))
    time.sleep(300)
if control.get("stdout_bytes"):
    sys.stdout.write("x" * control["stdout_bytes"])
if control.get("stderr_bytes"):
    sys.stderr.write("e" * control["stderr_bytes"])
if control.get("stdout_raw") is not None:
    sys.stdout.write(control["stdout_raw"])
if control.get("result") is not None:
    sys.stdout.write(json.dumps(control["result"]) + "\\n")
if control.get("stderr"):
    sys.stderr.write(control["stderr"])
if control.get("kill_self"):
    os.kill(os.getpid(), 9)
sys.exit(control.get("code", 0))
"""


def result(text="the reply\n", **fields):
    """The object the program printed in the probes of 2026-11-18, with `text` as its `result`."""
    document = {"type": "result", "subtype": "success", "is_error": False, "terminal_reason": "completed",
                "api_error_status": None, "result": text, "total_cost_usd": 0.0006,
                "usage": {"input_tokens": 2, "cache_creation_input_tokens": 3177, "cache_read_input_tokens": 649,
                          "output_tokens": 4, "output_tokens_details": {"thinking_tokens": 0}},
                "modelUsage": {"claude-haiku-5-5": {"inputTokens": 2}}, "permission_denials": []}
    document.update(fields)
    return document


class Bridge(unittest.TestCase):
    """The helper, a project at `self.root` and a fake `claude` in `self.outside` on the trusted `PATH`."""

    @classmethod
    def setUpClass(cls):
        cls.helper = support_helpers.load("ask-claude")

    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.base = os.path.realpath(holder.name)
        self.root = os.path.join(self.base, "project")
        self.outside = os.path.join(self.base, "outside")
        self.temp = os.path.join(self.base, "tmp")
        for folder in (os.path.join(self.root, ".git"), os.path.join(self.root, ".workbench"),
                       os.path.join(self.root, "bin"), os.path.join(self.root, "docs"), self.outside,
                       self.temp):
            os.makedirs(folder)
        with open(os.path.join(self.root, ".workbench", "manifest.json"), "w") as handle:
            handle.write("{}\n")
        with open(os.path.join(self.root, "docs", "plan.md"), "w") as handle:
            handle.write("# Plan\n")
        self.fake(self.outside)
        self.control(result=result())
        self.path([self.outside], TMPDIR=self.temp, HOME=os.path.join(self.base, "home"))

    def fake(self, folder):
        script = os.path.join(folder, "claude")
        with open(script, "w") as handle:
            handle.write(FAKE.format(python=sys.executable))
        os.chmod(script, 0o755)

    def control(self, folder=None, **fields):
        with open(os.path.join(folder or self.outside, "control.json"), "w") as handle:
            json.dump(fields, handle)

    def path(self, entries, **extra):
        patch = unittest.mock.patch.dict(os.environ, dict({"PATH": os.pathsep.join(entries)}, **extra))
        patch.start()
        self.addCleanup(patch.stop)

    def calls(self, folder=None):
        try:
            with open(os.path.join(folder or self.outside, "calls.jsonl")) as handle:
                return [json.loads(line) for line in handle]
        except FileNotFoundError:
            return []

    def ask(self, *args, prompt=b"Review docs/plan.md\n", cwd=None):
        """``(code, standard output, standard error)`` of ``ask-claude ask <args>`` with `prompt` on standard input."""
        out, err = io.StringIO(), io.StringIO()
        code = self.helper.main(["ask", *args], io.BytesIO(prompt), out, err, cwd or self.root)
        return code, out.getvalue(), err.getvalue()

    def document(self, *args, **kwargs):
        """The one object a call printed, after the checks every call must pass."""
        code, out, err = self.ask(*args, **kwargs)
        self.assertEqual("", err)
        self.assertTrue(out.endswith("\n") and "\n" not in out[:-1], "not one line")
        self.assertLessEqual(len(out.encode()), self.helper.MAX_OBJECT)
        document = json.loads(out)
        self.assertEqual(code, 0 if document["ok"] else 1)
        self.assertEqual(2, document["contract"])
        self.assertEqual("claude", document["vendor"])
        return document

    def refused(self, *args, contains="", **kwargs):
        code, out, err = self.ask(*args, **kwargs)
        self.assertEqual((1, ""), (code, out), err)
        self.assertTrue(err.startswith("refused: ") and err.count("\n") == 1, err)
        self.assertIn(contains, err)
        self.assertEqual([], self.calls(), "the program was started")
        return err

    def tree(self):
        found = {}
        for base, dirs, files in os.walk(self.root):
            for name in dirs + files:
                full = os.path.join(base, name)
                if os.path.islink(full):
                    found[os.path.relpath(full, self.root)] = os.readlink(full)
                elif os.path.isdir(full):
                    found[os.path.relpath(full, self.root)] = None
                else:
                    with open(full, "rb") as handle:
                        found[os.path.relpath(full, self.root)] = handle.read()
        return found
