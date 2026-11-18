"""The root guard of `ask-ollama ask`: the matrix of `--root` spellings, forms and descendants that must be refused, and the cases that
must be accepted. `--root` is validated by the contract's rules and then ignored (a server has no working directory), so the guard keeps
the contract's rule and no more.

Plan `2026-11-18-bridge-root-guard-and-hangup`, increment C. The case-variant cells need a disk on which `.GIT` is the directory
`.git`; they are skipped, with the reason named, on a case-sensitive disk. Retained from `test_askollama_options.py`: the exact
lower-case `.git` and `.workbench` as a relative path. New here: the case variants, the forms `./N`, `N/` and the absolute path, the
descendants, the accepted cases and a nested `sub/.git`. `ask-ollama` starts no program, so it has no signal handler to test."""

import os

import support_ollama

GUARDED = (".git", ".workbench")
SUBDIRECTORY = {".git": "hooks", ".workbench": "local"}
LOWER = (".git", ".workbench")
VARIANTS = (".GIT", ".Git", ".WORKBENCH", ".WorkBench")
MESSAGE = ".git or .workbench"


class RootMatrix(support_ollama.Bridge):
    def setUp(self):
        super().setUp()
        for name, sub in SUBDIRECTORY.items():
            os.makedirs(os.path.join(self.root, name, sub), exist_ok=True)

    def forms(self, name, rest=""):
        """The four forms of the path `name/rest`: plain, `./`, a trailing slash and absolute."""
        tail = name + ("/" + rest if rest else "")
        return (tail, "./" + tail, tail + "/", os.path.join(self.root, tail))

    def cells(self, names):
        for name in names:
            canonical = name.lower() if name.lower() in GUARDED else name
            for rest in ("", SUBDIRECTORY[canonical]):
                for form in self.forms(name, rest):
                    yield name, rest, form

    def resolves(self, name):
        try:
            return os.path.samefile(os.path.join(self.root, name), os.path.join(self.root, name.lower()))
        except OSError:
            return False

    def test_the_lower_case_names_their_forms_and_descendants_are_refused(self):
        for name, rest, form in self.cells(LOWER):
            with self.subTest(name=name, rest=rest, form=form):
                self.refused("--root", form, contains=MESSAGE)

    def test_the_case_variants_their_forms_and_descendants_are_refused(self):
        missing = [name for name in VARIANTS if not self.resolves(name)]
        if missing:
            self.skipTest("this disk is case-sensitive: %s is not the directory %s here" % (missing[0], missing[0].lower()))
        for name, rest, form in self.cells(VARIANTS):
            with self.subTest(name=name, rest=rest, form=form):
                self.refused("--root", form, contains=MESSAGE)

    def test_the_project_root_itself_and_a_lookalike_directory_are_accepted(self):
        for name in (".gitx", ".workbench-old", ".github"):
            os.makedirs(os.path.join(self.root, name))
        before = len(self.fake.requests)
        values = (".", "./", self.root, ".gitx", "./.gitx/", ".workbench-old", ".github", "docs")
        for value in values:
            with self.subTest(root=value):
                self.assertTrue(self.document("--root", value)["ok"], value)
        self.assertEqual(before + len(values), len(self.fake.requests))

    def test_a_root_below_a_nested_git_directory_is_still_refused(self):
        os.makedirs(os.path.join(self.root, "sub", ".git", "hooks"))
        for value in ("sub/.git", "sub/.git/hooks", "./sub/.git/"):
            with self.subTest(root=value):
                self.refused("--root", value, contains=MESSAGE)


if __name__ == "__main__":
    import unittest
    unittest.main()
