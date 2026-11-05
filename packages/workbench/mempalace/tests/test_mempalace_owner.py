"""`mempalace mine`, the owner's command (the module has no `init`), and the project's palace setting, with a fake
`mempalace` (criteria 5 to 7 of plan `2026-10-24-mempalace-module`, increment C). No test starts a real
`mempalace`; the terminal is a pseudo-terminal."""

import io
import json
import os
import signal
import subprocess
import sys
import time
import unittest
import unittest.mock

import support_mempalace

FORBIDDEN = ("--llm", "--llm-provider", "--llm-model", "--llm-endpoint", "--llm-api-key", "--accept-external-llm",
             "--daemon", "--direct", "--background", "--auto-mine", "--backend", "--palace", "--include-media")


class Owner(support_mempalace.Palace):
    def setUp(self):
        support_mempalace.Palace.setUp(self)
        self.corpus = os.path.join(self.base, "corpus")
        os.makedirs(self.corpus)

    def started(self):
        (call,) = self.calls()
        return call["argv"]


class NoInit(Owner):
    """Plan `2026-11-05-mempalace-per-clone-use`, increment C: the module has no `init`. `mine` needs none of what `init` writes
    into the folder it scans (two files, and a block appended to a git repository's `.gitignore`), and a command that offers it is a way to leave
    them in the working tree."""

    def test_init_is_refused_as_an_unknown_command_with_the_usage_line_and_starts_nothing(self):
        for argv in (("init", self.corpus), ("init", self.corpus, "--yes"), ("init",)):
            err = self.refused(*argv, contains="usage: mempalace status")
            self.assertNotIn("init", err)
        code, shown = self.owner("init", self.corpus)
        self.assertEqual(1, code, shown)
        self.assertIn("usage: mempalace status", shown)
        self.assertNotIn("init", shown.replace("note:", ""))
        self.assertEqual([], self.calls())

    def test_the_helper_names_no_init_and_no_language_model_option(self):
        self.assertNotIn("init", self.helper.USAGE)
        self.assertEqual({"mine"}, set(self.helper.OWNER_FLAGS) | set(self.helper.OWNER_VALUES))
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "helper", "mempalace"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("--no-llm", text)
        self.assertNotIn('"init"', text)

    def test_the_program_is_never_started_with_init_by_any_command(self):
        self.assertEqual(0, self.run_helper("status")[0])
        self.assertEqual(0, self.search()[0])
        self.assertEqual(0, self.owner("mine", self.corpus)[0])
        self.assertEqual(0, self.owner("mine", self.corpus, "--confirm")[0])
        self.assertEqual(["status", "search", "mine", "mine"], [call["argv"][0] for call in self.calls()])


class Mine(Owner):
    def test_a_mine_is_a_dry_run_unless_the_owner_confirms(self):
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(0, code, shown)
        self.assertEqual(["mine", self.corpus, "--wing", "project", "--dry-run"], self.started())
        self.assertIn("note: this is a dry run and files nothing; add --confirm", shown)

    def test_confirm_removes_the_dry_run_and_says_what_a_first_real_mine_does(self):
        code, shown = self.owner("mine", self.corpus, "--confirm")
        self.assertEqual(0, code, shown)
        self.assertEqual(["mine", self.corpus, "--wing", "project"], self.started())
        self.assertIn("downloads the embedding model", shown)
        self.assertIn("hallways.json", shown)

    def test_the_wing_and_the_mode_are_passed_from_their_allow_lists(self):
        self.assertEqual(0, self.owner("mine", self.corpus, "--wing", "proj", "--mode", "convos", "--confirm")[0])
        self.assertEqual(["mine", self.corpus, "--wing", "proj", "--mode", "convos"], self.started())

    def test_a_mode_outside_the_two_and_a_bad_wing_are_refused(self):
        for mode in ("extract", "", "PROJECTS", "projects;ls", "-x"):
            self.refused("mine", self.corpus, "--mode", mode, contains="--mode")
        for wing in ("", "-x", ".x", "a b", "x" * 65, "a/b"):
            self.refused("mine", self.corpus, "--wing", wing, contains="--wing")

    def test_an_option_the_helper_does_not_allow_is_refused(self):
        for name in FORBIDDEN + ("--yes", "--source", "--agent", "--limit", "--no-gitignore", "--extract",
                                 "--include-ignored", "--related-drawer-id", "--redetect-origin"):
            self.refused("mine", self.corpus, name, "x", contains="is not an option")

    def test_the_arguments_are_checked_for_shape(self):
        self.refused("mine", contains="needs the directory")
        self.refused("mine", self.corpus, self.corpus, contains="exactly one directory")
        self.refused("mine", self.corpus, "--wing", contains="needs a value")
        self.refused("mine", self.corpus, "--wing", "a", "--wing", "b", contains="given twice")
        self.refused("mine", self.corpus, "--confirm", "--confirm", contains="given twice")

    def test_a_relative_directory_is_read_against_the_current_directory(self):
        os.makedirs(os.path.join(self.root, "docs", "deep"))
        self.assertEqual(0, self.owner("mine", "deep", cwd=os.path.join(self.root, "docs"))[0])
        self.assertEqual(os.path.join(self.root, "docs", "deep"), self.started()[1])

    def test_the_terminal_is_handed_to_the_program(self):
        self.assertEqual(0, self.owner("mine", self.corpus)[0])
        self.assertEqual([True, True, True], self.calls()[0]["tty"])

    def test_the_program_exit_code_is_the_commands(self):
        self.control(code=3, stdout="partial\n")
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(3, code)
        self.assertIn("partial", shown)

    def test_the_program_may_run_for_longer_than_a_search_may(self):
        self.control(sleep=2, stdout="done\n")
        with unittest.mock.patch.object(self.helper, "TIMEOUT", 1):
            code, shown = self.owner("mine", self.corpus, "--confirm")
        self.assertEqual(0, code, shown)
        self.assertIn("done", shown)


class Terminal(Owner):
    def test_a_command_that_is_not_run_from_a_terminal_starts_nothing(self):
        for argv in (("mine", self.corpus), ("mine", self.corpus, "--confirm")):
            self.refused(*argv, contains="only from a terminal")

    def test_a_terminal_for_input_alone_is_not_enough(self):
        import io
        _, tin, tout, terr = self.terminal()
        for stdin, out in ((tin, io.StringIO()), (io.BytesIO(b""), tout)):
            err = io.StringIO()
            self.assertEqual(1, self.helper.main(["mine", self.corpus], stdin, out, err, self.root))
            self.assertIn("only from a terminal", err.getvalue())
        self.assertEqual([], self.calls())

    def test_a_closed_stream_is_not_a_terminal(self):
        import io
        _, tin, tout, terr = self.terminal()
        tin.close()
        err = io.StringIO()
        self.assertEqual(1, self.helper.main(["mine", self.corpus], tin, tout, err, self.root))
        self.assertIn("only from a terminal", err.getvalue())
        self.assertEqual([], self.calls())


class Directory(Owner):
    def owner_refused(self, *args, contains):
        """A refusal of an owner command run from a terminal: nothing was started, and the text says why."""
        code, shown = self.owner(*args)
        self.assertEqual(1, code, shown)
        self.assertTrue(shown.startswith("note: ") or shown.startswith("refused: "), shown)
        self.assertIn("refused: ", shown)
        self.assertIn(contains, shown)
        self.assertEqual([], self.calls(), "the program was started")

    def test_a_directory_that_does_not_exist_or_is_not_one_is_refused(self):
        self.owner_refused("mine", os.path.join(self.base, "nothing"), contains="does not exist")
        self.owner_refused("mine", os.path.join(self.root, "docs", "plan.md"), contains="not a directory")
        self.owner_refused("mine", "", contains="not a usable path")
        self.owner_refused("mine", self.corpus + "\0x", contains="not a usable path")

    def test_a_link_to_a_directory_or_a_link_in_the_path_is_refused(self):
        os.symlink(self.corpus, os.path.join(self.base, "linked"))
        self.owner_refused("mine", os.path.join(self.base, "linked"), contains="link")
        os.makedirs(os.path.join(self.corpus, "deep"))
        self.owner_refused("mine", os.path.join(self.base, "linked", "deep"), contains="link")

    def test_a_directory_in_git_or_the_workbench_directory_is_refused(self):
        os.makedirs(os.path.join(self.root, ".git", "x"))
        for name in (".git", ".git/x", ".workbench"):
            self.owner_refused("mine", os.path.join(self.root, name), contains=".git or .workbench")

    def test_the_project_root_and_a_directory_that_holds_it_need_the_explicit_flag(self):
        for target in (self.root, self.base, "."):
            self.owner_refused("mine", target, contains="--allow-project-root")
        self.assertEqual(0, self.owner("mine", self.root, "--allow-project-root")[0])

    def test_a_directory_inside_the_project_is_accepted(self):
        self.assertEqual(0, self.owner("mine", os.path.join(self.root, "docs"))[0])
        self.assertEqual(os.path.join(self.root, "docs"), self.calls()[0]["argv"][1])

    def test_a_project_config_that_is_a_link_a_directory_or_shared_is_refused_so_the_program_cannot_write_through_it(self):
        """Found by the security review of 2026-10-24 and reproduced against the real program: `init` opened
        `mempalace.yaml` for writing and followed a link, so a planted one overwrote a file outside the directory. The module no longer
        runs `init`, but the owner may run the program by hand, and `mine` reads the configuration it finds, so the refusal stays."""
        victim = os.path.join(self.base, "victim.yaml")
        with open(victim, "w") as handle:
            handle.write("ORIGINAL\n")
        outside_dir = os.path.join(self.base, "somewhere")
        os.makedirs(outside_dir)
        names = ("mempalace.yaml", "mempalace.yml", "mempal.yaml", "mempal.yml", "mempalace.yaml.bak",
                 "mempalace.yaml.bak.20261024T000000Z", "mempal.yml.bak-1", "entities.json", ".gitignore",
                 "entities.json.bak", "ENTITIES.JSON", "Mempalace.YAML", ".GitIgnore")
        for position, name in enumerate(names):
            for label in ("link to a file", "link to a directory", "dangling link", "directory", "hard link"):
                # numbered, so names that differ only in case stay apart on a case-insensitive volume
                folder = os.path.join(self.base, "corpus-%02d-%s" % (position, label.replace(" ", "_")))
                os.makedirs(folder)
                path = os.path.join(folder, name)
                if label == "link to a file":
                    os.symlink(victim, path)
                elif label == "link to a directory":
                    os.symlink(outside_dir, path)
                elif label == "dangling link":
                    os.symlink(os.path.join(self.base, "nothing"), path)
                elif label == "directory":
                    os.mkdir(path)
                else:
                    os.link(victim, path)
                self.owner_refused("mine", folder, contains="would write through it")
        self.assertEqual([], self.calls())
        with open(victim) as handle:
            self.assertEqual("ORIGINAL\n", handle.read())

    def test_a_plain_config_file_and_unrelated_names_are_not_in_the_way(self):
        folder = os.path.join(self.base, "fine")
        os.makedirs(folder)
        for name in ("mempalace.yaml", "mempalace.yaml.bak", "notes.md", "mempalace-notes.txt", "my-mempalace.yaml",
                     "entities.json", ".gitignore", "entities-old.json"):
            with open(os.path.join(folder, name), "w") as handle:
                handle.write("x\n")
        os.symlink(os.path.join(self.base, "nothing"), os.path.join(folder, "link-to-nothing.md"))
        self.assertEqual(0, self.owner("mine", folder)[0])

    def test_a_directory_that_is_the_palace_or_holds_it_or_is_inside_it_is_refused(self):
        """Found by the security review of 2026-10-24: `init` wrote `.mempalace/origin.json` under the palace, so a
        palace inside the directory made a planted link there a way to overwrite a file; `mine` would index the
        palace's own files."""
        palace = os.path.join(self.corpus, "store")
        os.makedirs(os.path.join(palace, ".mempalace"))
        with open(os.path.join(self.base, "victim.txt"), "w") as handle:
            handle.write("ORIGINAL\n")
        os.symlink(os.path.join(self.base, "victim.txt"), os.path.join(palace, ".mempalace", "origin.json"))
        os.makedirs(os.path.join(self.root, ".workbench", "local"))
        with open(os.path.join(self.root, ".workbench", "local", "mempalace.json"), "w") as handle:
            json.dump({"format": 1, "palace": palace}, handle)
        for target in (self.corpus, palace, os.path.join(palace, ".mempalace")):
            self.owner_refused("mine", target, contains="same place or one holds the other")
        self.assertEqual([], self.calls())
        with open(os.path.join(self.base, "victim.txt")) as handle:
            self.assertEqual("ORIGINAL\n", handle.read())

    def test_a_palace_the_program_saved_or_its_default_places_count_even_without_a_setting(self):
        for where in ((".config", "mempalace"), (".mempalace",)):
            folder = os.path.join(self.home, *where)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "config.json"), "w") as handle:
                # a decimal number, which a strict reader would refuse, must not hide the path
                json.dump({"palace_path": os.path.join(self.corpus, "saved-" + where[0]), "weight": 0.5}, handle)
            self.owner_refused("mine", self.corpus, contains="same place or one holds the other")
            os.remove(os.path.join(folder, "config.json"))
        for default in ((".config", "mempalace", "palace"), (".mempalace", "palace")):
            inside = os.path.join(self.home, *default)
            os.makedirs(inside, exist_ok=True)
            self.owner_refused("mine", inside, contains="same place or one holds the other")
            self.owner_refused("mine", os.path.dirname(inside), contains="same place or one holds the other")
        self.assertEqual([], self.calls())

    def test_a_palace_elsewhere_does_not_get_in_the_way(self):
        os.makedirs(os.path.join(self.root, ".workbench", "local"))
        with open(os.path.join(self.root, ".workbench", "local", "mempalace.json"), "w") as handle:
            json.dump({"format": 1, "palace": os.path.join(self.base, "palace-elsewhere")}, handle)
        self.assertEqual(0, self.owner("mine", self.corpus)[0])
        self.assertEqual(os.path.join(self.base, "palace-elsewhere"), self.calls()[0]["front"]["--palace"])

    def test_a_directory_that_cannot_be_entered_is_refused(self):
        folder = os.path.join(self.corpus, "locked")
        os.mkdir(folder)
        os.chmod(folder, 0)
        self.addCleanup(os.chmod, folder, 0o755)
        if os.access(folder, os.X_OK):
            self.skipTest("the permissions are not enforced for this user")
        self.owner_refused("mine", folder, contains="cannot be entered")


class Environment(Owner):
    def test_the_program_gets_the_same_short_environment_and_a_private_directory_that_is_removed(self):
        secrets = {"MEMPALACE_PALACE_PATH": "/x", "MEMPALACE_EMBEDDING_API_URL": "http://x", "OPENAI_API_KEY": "k",
                   "ANTHROPIC_API_KEY": "k", "GITHUB_TOKEN": "t", "GIT_DIR": "/x", "XDG_CONFIG_HOME": "/x", "MEMPALACE_EMBEDDING_MODEL": "embeddinggemma2",
                   "ANONYMIZED_TELEMETRY": "True"}
        with unittest.mock.patch.dict(os.environ, dict(secrets, LANG="C.UTF-8", LC_ALL="C")):
            self.assertEqual(0, self.owner("mine", self.corpus, "--confirm")[0])
        (call,) = self.calls()
        self.assertEqual({"HOME", "LANG", "LC_ALL", "PATH", "PYTHONDONTWRITEBYTECODE", "MEMPALACE_EMBEDDING_MODEL",
                          "ANONYMIZED_TELEMETRY", "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0", "GIT_CONFIG_KEY_1", "GIT_CONFIG_VALUE_1", "GIT_NO_LAZY_FETCH", "GIT_TERMINAL_PROMPT"}, set(call["env"]))
        self.assertEqual(self.helper.GIT_SETTINGS, {k: v for k, v in call["env"].items() if k.startswith("GIT_")})
        self.assertEqual("minilm", call["env"]["MEMPALACE_EMBEDDING_MODEL"])
        self.assertEqual("False", call["env"]["ANONYMIZED_TELEMETRY"])  # increment E: also for the owner commands
        self.assertEqual(self.outside, call["env"]["PATH"])
        self.assertTrue(os.path.realpath(call["cwd"]).startswith(self.temp + os.sep), call["cwd"])
        self.assertEqual([], os.listdir(self.temp))

    def test_a_program_inside_the_project_is_never_run_for_an_owner_command(self):
        os.remove(os.path.join(self.outside, "mempalace"))
        inside = os.path.join(self.root, "bin")
        os.makedirs(inside)
        self.fake(inside)
        self.path([inside], TMPDIR=self.temp, HOME=self.home)
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(1, code)
        self.assertIn("not found in a trusted PATH entry", shown)
        self.assertEqual([], self.calls(inside))

    def test_a_temporary_directory_inside_the_project_is_refused(self):
        self.path([self.outside], TMPDIR=os.path.join(self.root, "docs"), HOME=self.home)
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(1, code)
        self.assertIn("temporary directory", shown)
        self.assertEqual([], self.calls())

    def test_the_project_is_the_same_after_every_kind_of_call(self):
        before = self.tree()
        self.owner("mine", self.corpus)
        self.owner("mine", self.corpus, "--confirm")
        self.control(code=2)
        self.owner("mine", self.corpus, "--confirm")
        self.assertEqual(before, self.tree())
        self.assertEqual([], os.listdir(self.temp))

    def test_a_terminate_signal_stops_the_program_and_removes_the_scratch_directory(self):
        self.control(hang=True)
        helper = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "helper", "mempalace")
        workbench = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))), "workbench")
        master, tin, tout, terr = self.terminal()
        env = {"PATH": self.outside, "TMPDIR": self.temp, "HOME": self.home, "PYTHONPATH": workbench}
        process = subprocess.Popen([sys.executable, "-B", helper, "mine", self.corpus, "--confirm"], cwd=self.root,
                                   env=env, stdin=tin, stdout=tout, stderr=terr)
        self.addCleanup(process.kill)
        pids = os.path.join(self.outside, "pids")
        for _ in range(100):
            if os.path.exists(pids) and self.calls():
                break
            time.sleep(0.1)
        else:
            self.fail("the program did not start")
        time.sleep(0.2)
        with open(pids) as handle:
            grandchild = int(handle.read())
        self.addCleanup(self.reap, grandchild)
        program = self.calls()[0]["pid"]
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=30)
        for _ in range(50):
            try:
                os.kill(program, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail("the program is still running")
        self.assertFalse(os.path.exists(self.calls()[0]["cwd"]))

    @staticmethod
    def reap(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


class Setting(Owner):
    """`.workbench/local/mempalace.json` and the palace it names."""

    def write(self, text, name="mempalace.json"):
        os.makedirs(os.path.join(self.root, ".workbench", "local"), exist_ok=True)
        with open(os.path.join(self.root, ".workbench", "local", name), "w", encoding="utf-8") as handle:
            handle.write(text)

    def setting(self, **fields):
        document = {"format": 1, "palace": os.path.join(self.base, "palace")}
        document.update(fields)
        self.write(json.dumps(document))

    def every_command(self):
        """The three commands, each as (what to call it with, how to run it)."""
        return (("status", lambda: self.run_helper("status")),
                ("search", lambda: self.search()),
                ("mine", lambda: self.owner("mine", self.corpus)))

    def test_with_no_setting_the_program_is_not_told_a_palace(self):
        for _, run in self.every_command():
            run()
        for call in self.calls():
            self.assertEqual({"--backend": "chroma"}, call["front"])

    def test_a_valid_setting_is_passed_before_the_command_for_all_three(self):
        self.setting()
        palace = os.path.join(self.base, "palace")
        for name, run in self.every_command():
            self.assertEqual(0, run()[0], name)
        for call, name in zip(self.calls(), ("status", "search", "mine")):
            self.assertEqual({"--backend": "chroma", "--palace": palace}, call["front"])
            self.assertEqual(name, call["argv"][0])

    def test_a_setting_that_is_wrong_in_any_way_stops_every_command_before_the_program_starts(self):
        bad = {
            "malformed": "{", "empty": "", "not an object": "[]", "extra key": '{"format":1,"palace":"/x","a":1}',
            "missing palace": '{"format":1}', "missing format": '{"palace":"/x"}', "format two": '{"format":2,"palace":"/x"}',
            "format string": '{"format":"1","palace":"/x"}', "format true": '{"format":true,"palace":"/x"}',
            "format float": '{"format":1.0,"palace":"/x"}', "relative": '{"format":1,"palace":"palace"}',
            "dot dot": '{"format":1,"palace":"/x/../y"}', "double slash": '{"format":1,"palace":"/x//y"}',
            "trailing slash": '{"format":1,"palace":"/x/"}', "empty palace": '{"format":1,"palace":""}',
            "palace number": '{"format":1,"palace":5}', "control": '{"format":1,"palace":"/x\\u0007y"}',
            "newline": '{"format":1,"palace":"/x\\ny"}', "duplicate key": '{"format":1,"format":1,"palace":"/x"}',
            "long": json.dumps({"format": 1, "palace": "/" + "a" * 600}),
            "oversized": '{"format":1,"palace":"/x","pad":"%s"}' % ("x" * 5000), "nan": '{"format":NaN,"palace":"/x"}',
        }
        for label, text in bad.items():
            self.write(text)
            for name, run in self.every_command():
                if name == "mine":
                    code, shown = run()
                    self.assertIn("mempalace.json", shown, (label, name))
                else:
                    code, out, err = run()
                    self.assertIn("mempalace.json", err, (label, name))
                self.assertEqual(1, code, (label, name))
        self.assertEqual([], self.calls())

    def test_a_setting_that_is_a_link_or_a_directory_is_refused(self):
        target = os.path.join(self.base, "elsewhere.json")
        with open(target, "w") as handle:
            handle.write('{"format":1,"palace":"/x"}')
        os.makedirs(os.path.join(self.root, ".workbench", "local"))
        os.symlink(target, os.path.join(self.root, ".workbench", "local", "mempalace.json"))
        self.refused("status", contains="mempalace.json")
        os.remove(os.path.join(self.root, ".workbench", "local", "mempalace.json"))
        os.mkdir(os.path.join(self.root, ".workbench", "local", "mempalace.json"))
        self.refused("status", contains="mempalace.json")
        self.assertEqual([], self.calls())

    def test_a_workbench_directory_swapped_for_a_link_after_the_project_was_found_is_not_followed(self):
        """Found by the security review of 2026-10-24: the setting is read through the project's held
        descriptor, so a link put in place of `.workbench` after the project is found leads nowhere."""
        external = os.path.join(self.base, "external")
        os.makedirs(os.path.join(external, "local"))
        with open(os.path.join(external, "local", "mempalace.json"), "w") as handle:
            handle.write(json.dumps({"format": 1, "palace": "/attacker/palace"}))
        real = os.path.join(self.root, ".workbench")
        os.rename(real, real + ".real")
        os.symlink(external, real)
        with self.assertRaises(self.helper.Refused) as caught:
            self.helper.palace_setting(self.root)
        self.assertIn("mempalace.json", str(caught.exception))

    def test_a_setting_file_with_a_second_name_is_refused(self):
        self.setting()
        os.link(os.path.join(self.root, ".workbench", "local", "mempalace.json"), os.path.join(self.base, "second-name.json"))
        self.refused("status", contains="mempalace.json")

    def test_a_setting_file_is_read_from_the_project_root_whatever_the_current_directory(self):
        self.setting()
        self.assertEqual(0, self.run_helper("status", cwd=os.path.join(self.root, "docs"))[0])
        self.assertEqual(os.path.join(self.base, "palace"), self.calls()[0]["front"]["--palace"])

    def test_a_directory_that_is_not_a_project_is_refused(self):
        self.refused("status", cwd=self.base, contains="not inside a workbench project")


class Wing(Owner):
    """Plan `2026-11-05-mempalace-use-and-independence`, increment D: the project names its wing in `.workbench/local/mempalace.json`, and
    `search` and `mine` use it unless the caller names another. `status` takes no wing. It borrows the three helpers of
    `Setting` and does not inherit its tests, which would run twice."""

    WING = "project-workbench"
    write = Setting.write
    setting = Setting.setting
    every_command = Setting.every_command

    def with_wing(self, wing=None, palace=True):
        document = {"format": 1}
        if palace:
            document["palace"] = os.path.join(self.base, "palace")
        document["wing"] = wing or self.WING
        self.write(json.dumps(document))

    def test_a_setting_with_only_a_wing_is_read_and_passes_no_palace(self):
        self.with_wing(palace=False)
        self.assertEqual(0, self.search()[0])
        (call,) = self.calls()
        self.assertEqual({"--backend": "chroma"}, call["front"])
        self.assertEqual(["search", "--results", "5", "--wing", self.WING, "--", "why SQLite"], call["argv"])

    def test_a_setting_with_a_palace_and_a_wing_passes_both(self):
        self.with_wing()
        self.assertEqual(0, self.search()[0])
        (call,) = self.calls()
        self.assertEqual({"--backend": "chroma", "--palace": os.path.join(self.base, "palace")}, call["front"])
        self.assertEqual(["search", "--results", "5", "--wing", self.WING, "--", "why SQLite"], call["argv"])

    def test_a_setting_with_a_palace_only_passes_the_default_wing(self):
        self.setting()
        self.assertEqual(0, self.search()[0])
        argv = self.calls()[0]["argv"]
        self.assertEqual("project", argv[argv.index("--wing") + 1])

    def test_a_wing_the_caller_names_replaces_the_one_in_the_setting_for_search(self):
        self.with_wing()
        self.assertEqual(0, self.search("--wing", "other")[0])
        argv = self.calls()[0]["argv"]
        self.assertEqual(1, argv.count("--wing"))
        self.assertEqual("other", argv[argv.index("--wing") + 1])

    def test_a_room_and_the_other_options_are_passed_beside_the_default_wing(self):
        self.with_wing()
        self.assertEqual(0, self.search("--room", "decisions", "--since", "2026-01-01")[0])
        self.assertEqual(["search", "--results", "5", "--wing", self.WING, "--room", "decisions", "--since", "2026-01-01",
                          "--", "why SQLite"], self.calls()[0]["argv"])

    def test_mine_uses_the_wing_of_the_setting_and_says_so_and_a_wing_the_owner_names_replaces_it(self):
        self.with_wing()
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(0, code, shown)
        self.assertEqual(["mine", self.corpus, "--wing", self.WING, "--dry-run"], self.started())
        self.assertIn("the wing is %s" % self.WING, shown)
        self.assertIn("from .workbench/local/mempalace.json", shown)
        os.remove(os.path.join(self.outside, "calls.jsonl"))
        code, shown = self.owner("mine", self.corpus, "--wing", "other", "--confirm")
        self.assertEqual(0, code, shown)
        argv = self.started()
        self.assertEqual(["mine", self.corpus, "--wing", "other"], argv)
        self.assertNotIn(self.WING, shown)

    def test_mine_with_a_mode_keeps_the_wing_before_the_mode(self):
        self.with_wing()
        self.assertEqual(0, self.owner("mine", self.corpus, "--mode", "convos", "--confirm")[0])
        self.assertEqual(["mine", self.corpus, "--wing", self.WING, "--mode", "convos"], self.started())

    def test_status_passes_no_wing(self):
        self.with_wing()
        code, out, err = self.run_helper("status")
        self.assertEqual(0, code, err)
        self.assertEqual(1, len(self.calls()))
        self.assertNotIn("--wing", self.calls()[0]["argv"])

    def test_a_wing_that_is_not_a_name_stops_every_command_before_the_program_starts(self):
        for label, value in (("empty", ""), ("dash", "-x"), ("dot", ".x"), ("space", "a b"), ("long", "x" * 65),
                             ("slash", "a/b"), ("number", 5), ("null", None), ("true", True), ("list", ["a"]),
                             ("newline", "a\nb"), ("non-ascii", "caf\u00e9"), ("semicolon", "a;ls")):
            self.write(json.dumps({"format": 1, "wing": value}))
            for name, run in self.every_command():
                if name == "mine":
                    code, shown = run()
                    self.assertIn("mempalace.json", shown, (label, name))
                else:
                    code, out, err = run()
                    self.assertIn("mempalace.json", err, (label, name))
                self.assertEqual(1, code, (label, name))
        self.assertEqual([], self.calls())

    def test_a_setting_with_neither_a_palace_nor_a_wing_or_with_another_key_is_still_refused(self):
        for label, text in (("neither", '{"format":1}'), ("extra", '{"format":1,"wing":"w","room":"r"}'),
                            ("format two", '{"format":2,"wing":"w"}'), ("no format", '{"wing":"w"}'),
                            ("duplicate", '{"format":1,"wing":"w","wing":"w"}')):
            self.write(text)
            self.refused("status", contains="mempalace.json")
            self.refused_search(contains="mempalace.json")
        self.assertEqual([], self.calls())

    def test_the_wing_does_not_change_which_directories_are_refused(self):
        self.with_wing()
        self.assertEqual(1, self.owner("mine", self.root)[0])
        self.assertEqual([], self.calls())


class Location(Owner):
    """Plan `2026-11-05-mempalace-per-clone-use`, increment A: the setting is per clone, in `.workbench/local/mempalace.json`, the old
    tracked path is not read, and with no wing in a setting the wing is the project folder's name when that is a valid name. Like `Wing`,
    it borrows the helpers of `Setting` and does not inherit its tests."""

    write = Setting.write
    setting = Setting.setting
    every_command = Setting.every_command

    def argv_wing(self, call):
        argv = call["argv"]
        return argv[argv.index("--wing") + 1] if "--wing" in argv else None

    def project(self, name):
        """A project folder called `name` under the test's base, found as a project, and its path."""
        path = os.path.join(self.base, name)
        os.makedirs(os.path.join(path, ".git"))
        os.makedirs(os.path.join(path, ".workbench"))
        with open(os.path.join(path, ".workbench", "manifest.json"), "w") as handle:
            handle.write("{}\n")
        return path

    def test_the_setting_is_read_from_the_local_directory(self):
        self.setting()
        self.assertEqual(0, self.run_helper("status")[0])
        self.assertEqual(os.path.join(self.base, "palace"), self.calls()[0]["front"]["--palace"])

    def test_the_old_tracked_path_is_not_read_even_when_it_is_valid_or_malformed(self):
        for text in (json.dumps({"format": 1, "palace": os.path.join(self.base, "old-palace"), "wing": "old-wing"}), "{"):
            with open(os.path.join(self.root, ".workbench", "mempalace.json"), "w") as handle:
                handle.write(text)
            self.assertEqual(0, self.run_helper("status")[0])
            self.assertEqual(0, self.search()[0])
        for call in self.calls():
            self.assertEqual({"--backend": "chroma"}, call["front"])
            self.assertNotIn("old-wing", call["argv"])

    def test_no_local_directory_and_no_file_are_no_setting_and_nothing_is_created(self):
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))
        for name, run in self.every_command():
            self.assertEqual(0, run()[0], name)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".workbench", "local")))
        os.makedirs(os.path.join(self.root, ".workbench", "local"))
        self.assertEqual(0, self.run_helper("status")[0])

    def test_a_local_that_is_a_link_or_a_file_is_refused(self):
        local = os.path.join(self.root, ".workbench", "local")
        elsewhere = os.path.join(self.base, "elsewhere")
        os.makedirs(elsewhere)
        with open(os.path.join(elsewhere, "mempalace.json"), "w") as handle:
            handle.write(json.dumps({"format": 1, "palace": "/attacker/palace"}))
        os.symlink(elsewhere, local)
        self.refused("status", contains="mempalace.json")
        os.remove(local)
        with open(local, "w") as handle:
            handle.write("not a directory")
        self.refused("status", contains="mempalace.json")
        self.assertEqual([], self.calls())

    def test_a_malformed_setting_in_the_local_directory_names_the_new_path(self):
        self.write("{")
        self.refused("status", contains=".workbench/local/mempalace.json")

    def test_with_no_setting_the_wing_is_the_folder_name_for_search_and_mine(self):
        self.assertEqual(0, self.search()[0])
        self.assertEqual("project", self.argv_wing(self.calls()[0]))
        code, shown = self.owner("mine", self.corpus)
        self.assertEqual(0, code, shown)
        self.assertEqual(["mine", self.corpus, "--wing", "project", "--dry-run"], self.calls()[-1]["argv"])
        self.assertIn("the wing is project, from the folder name", shown)

    def test_status_passes_no_wing_whatever_the_folder_is_called(self):
        self.assertEqual(0, self.run_helper("status")[0])
        for call in self.calls():
            self.assertNotIn("--wing", call["argv"])

    def test_a_wing_in_the_setting_replaces_the_folder_name(self):
        self.write(json.dumps({"format": 1, "wing": "chosen"}))
        self.assertEqual(0, self.search()[0])
        self.assertEqual("chosen", self.argv_wing(self.calls()[0]))

    def test_a_wing_the_caller_names_replaces_the_folder_name(self):
        self.assertEqual(0, self.search("--wing", "other")[0])
        argv = self.calls()[0]["argv"]
        self.assertEqual(1, argv.count("--wing"))
        self.assertEqual("other", argv[argv.index("--wing") + 1])
        code, shown = self.owner("mine", self.corpus, "--wing", "other", "--confirm")
        self.assertEqual(0, code, shown)
        self.assertEqual(["mine", self.corpus, "--wing", "other"], self.calls()[-1]["argv"])

    def test_a_folder_name_that_is_a_valid_wing_is_the_default(self):
        for name in ("my.proj_1:x", "A", "x" * 64, "knowledge-base", "1abc"):
            self.assertEqual((None, name), self.helper.project_setting(self.project(name)), name)

    def test_a_folder_name_that_is_not_a_valid_wing_gives_no_default(self):
        for name in ("-x", ".x", "a b", "x" * 65, "caf\u00e9", "a;ls", "a,b"):
            self.assertEqual((None, None), self.helper.project_setting(self.project(name)), name)

    def test_a_folder_with_no_valid_name_searches_every_wing_as_before(self):
        path = self.project("a b")
        self.assertEqual(0, self.helper.main(["search", "--", "why"], io.BytesIO(b""), io.StringIO(), io.StringIO(), path))
        self.assertIsNone(self.argv_wing(self.calls()[0]))


class RecordedModel(Setting):
    def palace(self, text=None, link=False):
        folder = os.path.join(self.base, "palace")
        os.makedirs(folder, exist_ok=True)
        self.setting()
        if text is not None:
            path = os.path.join(folder, "mempalace_embedder.json")
            if link:
                if os.path.lexists(path):
                    os.remove(path)
                other = os.path.join(self.base, "other.json")
                with open(other, "w") as handle:
                    handle.write(text)
                os.symlink(other, path)
            else:
                with open(path, "w") as handle:
                    handle.write(text)

    GOOD = '{"mempalace_drawers": {"model_name": "minilm", "dimension": 0}, "mempalace_closets": {"model_name": "minilm"}}'

    def test_a_palace_recorded_as_minilm_or_not_recorded_yet_is_searched(self):
        self.palace(self.GOOD)
        self.assertEqual(0, self.search()[0])
        os.remove(os.path.join(self.base, "palace", "mempalace_embedder.json"))
        self.assertEqual(0, self.search()[0])

    def test_a_palace_recorded_with_another_model_or_unreadably_starts_nothing(self):
        for text in ('{"mempalace_drawers": {"model_name": "gemma", "dimension": 768}}', "{", "[]", "{}",
                     '{"mempalace_drawers": 5}', '{"mempalace_drawers": {"model_name": ["minilm"]}}'):
            self.palace(text)
            self.refused_search(contains="")
        self.palace(self.GOOD, link=True)
        self.refused_search(contains="mempalace_embedder.json")
        self.assertEqual([], self.calls())

    def test_the_other_model_is_named_without_its_control_characters(self):
        self.palace('{"mempalace_drawers": {"model_name": "bad\\u001b[31mname"}}')
        err = self.refused_search(contains="only minilm is cached")
        self.assertNotIn("\x1b", err)

    def test_status_does_not_look_at_the_recorded_model(self):
        self.palace('{"mempalace_drawers": {"model_name": "gemma"}}')
        self.assertEqual(0, self.run_helper("status")[0])


if __name__ == "__main__":
    unittest.main()
