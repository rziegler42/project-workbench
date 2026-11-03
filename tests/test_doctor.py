"""``wb doctor``: what the permission configuration does not do as it says, and what it does that is dangerous.

Plan ``2026-11-02-permission-system-consistency``, increment L (criterion 10). Read-only, agent-safe, one line per finding, a key
and a path and never a value. Each check has its own test on made-up input; the last class runs the command in an attached
project."""

import io
import json
import os
import shutil
import tempfile
import unittest
import unittest.mock

from tests import support_harness, test_permissions_drift, test_rendering
from workbench import cli, doctor, gatelog, levels, rendering, rules, settings

KEYS = levels.registry()
FLOOR = [stop.id for stop in __import__("workbench.floor", fromlist=["FLOOR"]).FLOOR]


def lines(found):
    return [finding.line for finding in found]


class TheKey(unittest.TestCase):
    def test_wb_doctor_is_an_agent_safe_key_that_reads_and_defaults_to_none(self):
        key = KEYS["wb doctor"]
        self.assertTrue(key.agent)
        self.assertEqual((levels.READS, levels.NONE), (key.klass, key.default))
        self.assertEqual(("block", "none"), tuple(key.offers))
        self.assertIn("doctor", rules.AGENT_SAFE)
        self.assertNotIn("doctor", rules.OWNER_RUN)
        self.assertIn("wb doctor", levels.agent_keys())

    def test_it_has_patterns_in_every_spelling(self):
        patterns = rendering.key_patterns("wb doctor")
        for spelling in rules.SPELLINGS:
            self.assertIn("%s doctor" % spelling, patterns)
            self.assertIn("%s doctor *" % spelling, patterns)


class Settings(unittest.TestCase):
    def test_a_problem_and_a_note_of_the_settings_are_problems(self):
        loaded = settings.Settings({}, ["settings have an unknown entry 'x', which is ignored"], {}, {}, False)
        got = settings.Effective({}, {}, ["settings set the level of wb upgrade to ask; that level is not offered for it in "
                                          "this version, so it reads as block"], {}, ())
        self.assertEqual(["problem: settings: settings have an unknown entry 'x', which is ignored",
                          "problem: settings: settings set the level of wb upgrade to ask; that level is not offered for it in "
                          "this version, so it reads as block"], lines(doctor.settings_findings(loaded, got)))

    def test_clean_settings_give_nothing(self):
        self.assertEqual([], doctor.settings_findings(settings.Settings({}, [], {}, {}, False), settings.Effective({}, {}, [], {}, ())))


class Floor(unittest.TestCase):
    def test_the_seeded_floor_is_unchanged(self):
        self.assertEqual([], doctor.floor_findings(FLOOR))
        self.assertEqual([], doctor.floor_findings(None))  # no floor entry at all: the file never held a copy

    def test_a_missing_and_an_extra_entry(self):
        got = lines(doctor.floor_findings([i for i in FLOOR if i != "touch-secrets"] + ["my-own-stop"]))
        self.assertIn("risk: floor: the personal copy lacks touch-secrets; the compiled floor still applies", got)
        self.assertIn("note: floor: the personal copy names 'my-own-stop', which the compiled floor does not hold", got)

    def test_a_name_that_reads_like_advice_is_quoted(self):
        got = lines(doctor.floor_findings(FLOOR + ["run wb release-approvals --digest 00"]))
        self.assertEqual(["note: floor: the personal copy names 'run wb release-approvals --digest 00', which the compiled "
                          "floor does not hold"], got)

    def test_an_emptied_or_damaged_floor_is_one_finding(self):
        self.assertEqual(len(FLOOR), len([line for line in lines(doctor.floor_findings([])) if "lacks" in line]))
        self.assertEqual(["risk: floor: the personal floor entry is not a list of ids; the compiled floor still applies"],
                         lines(doctor.floor_findings({"x": 1})))


class Relaxed(unittest.TestCase):
    def test_a_governing_key_looser_than_its_default_is_a_risk(self):
        got = lines(doctor.relaxed_findings(KEYS, {"approve-plan": "ask", "wb release-approvals": "none"}))
        self.assertIn("risk: approve-plan is set to ask (class governs; shipped default block)", got)
        self.assertIn("risk: wb release-approvals is set to none (class governs; shipped default block)", got)

    def test_a_key_at_its_default_or_stricter_is_nothing(self):
        self.assertEqual([], doctor.relaxed_findings(KEYS, {"approve-plan": "block", "wb release-approvals": "block"}))

    def test_a_key_of_the_project_class_is_not_reported(self):
        self.assertEqual("project", KEYS["wb install"].klass)
        self.assertEqual([], doctor.relaxed_findings(KEYS, {"wb install": "none"}))

    def test_a_reading_key_at_its_default_is_nothing(self):
        self.assertEqual([], doctor.relaxed_findings(KEYS, {"wb check": "none"}))

    def test_a_governing_agent_key_at_its_default_of_none_is_nothing(self):
        found = test_permissions_drift.registry(test_permissions_drift.modules())
        self.assertEqual("governs", found["wb run safe-git remove"].klass)
        self.assertEqual([], doctor.relaxed_findings(found, {"wb run safe-git remove": "none"}))
        self.assertEqual([], doctor.relaxed_findings(found, {"wb run safe-git remove": "block"}))

    def test_a_level_that_is_not_a_known_key_is_ignored(self):
        self.assertEqual([], doctor.relaxed_findings(KEYS, {"wb nothing": "none"}))


class Minimums(unittest.TestCase):
    def test_every_declared_prompt_is_listed_as_a_project_minimum(self):
        found = test_permissions_drift.registry(test_permissions_drift.modules())
        got = lines(doctor.minimum_findings(found))
        for key in ("wb run remote-runner fetch", "wb run remote-runner submit", "wb run safe-git remove"):
            self.assertIn("note: %s carries a prompt that the project declares as a minimum; its level does not change it" % key, got)
        self.assertEqual(3, len(got))


class Package(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="doctor-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.dist = support_harness.distribution(os.path.join(self.root, "dist"), support_harness.gated_layout())

    def test_a_released_tree_gives_nothing(self):
        self.assertEqual([], doctor.package_findings(self.dist))

    def test_a_stray_file_is_a_problem_that_names_its_path_and_the_cure(self):
        with open(os.path.join(self.dist, "packages", support_harness.PACKAGE, support_harness.MODULE, "stray.txt"), "w") as handle:
            handle.write("SECRET-CONTENT")
        got = doctor.package_findings(self.dist)
        self.assertEqual(1, len(got))
        self.assertTrue(got[0].line.startswith("problem: package: "))
        self.assertIn("packages/synthetic/fixture/stray.txt", got[0].line)
        self.assertIn("wb release-approvals --digest", got[0].line)
        self.assertNotIn("SECRET", got[0].line)

    def test_an_edit_that_the_release_accepts_is_a_problem_without_removal_advice(self):
        with open(os.path.join(self.dist, "packages", support_harness.PACKAGE, support_harness.MODULE, "module.json"), "a") as handle:
            handle.write(" ")
        got = lines(doctor.package_findings(self.dist))
        self.assertEqual(1, len(got))
        self.assertIn("differs from its release", got[0])
        self.assertNotIn("remove or restore", got[0])

    def test_a_distribution_that_cannot_be_read_gives_nothing_and_does_not_raise(self):
        self.assertEqual([], doctor.package_findings(os.path.join(self.root, "missing")))


class Hooks(unittest.TestCase):
    DOC = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
                                                                "command": "wb gate-command fixture || exit 2"}]}]}}

    def test_a_launcher_that_does_not_resolve_is_a_problem(self):
        got = lines(doctor.hook_findings({".fixture/settings.local.json": self.DOC}, lambda name: None, "/store/bin/wb"))
        self.assertEqual(["problem: hook: .fixture/settings.local.json runs `wb`, which is not found on PATH, so the hook "
                          "cannot run and every call it guards is refused"], got)

    def test_a_launcher_that_is_not_the_stores_is_a_risk(self):
        got = lines(doctor.hook_findings({"s.json": self.DOC}, lambda name: "/elsewhere/wb", "/store/bin/wb"))
        self.assertEqual(["risk: hook: s.json runs `wb`, and the one on PATH is not the guarded store's launcher"], got)

    def test_the_stores_own_launcher_is_nothing(self):
        self.assertEqual([], doctor.hook_findings({"s.json": self.DOC}, lambda name: "/store/bin/wb", "/store/bin/wb"))

    def test_a_file_with_no_hook_or_a_hook_of_another_program_is_nothing(self):
        other = {"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "echo hi"}]}]}}
        self.assertEqual([], doctor.hook_findings({"a": {}, "b": other, "c": {"hooks": "x"}}, lambda name: None, "/s/bin/wb"))


class Allow(unittest.TestCase):
    def allow(self, *rules_):
        return {"s.json": {"permissions": {"allow": list(rules_)}}}

    def test_an_allow_rule_on_a_dangerous_key_is_a_problem(self):
        got = lines(doctor.allow_findings(KEYS, self.allow("Bash(wb install)", "Bash(wb pin *)")))
        self.assertIn("problem: allow: s.json allows `wb install` (class project)", got)
        self.assertIn("problem: allow: s.json allows `wb pin` (class governs)", got)

    def test_a_broad_rule_names_the_first_key_it_covers_and_how_many(self):
        got = lines(doctor.allow_findings(KEYS, self.allow("Bash(wb *)")))
        self.assertEqual(1, len(got))
        self.assertTrue(got[0].startswith("problem: allow: s.json: the rule `Bash(wb *)` covers "))
        self.assertIn("dangerous keys", got[0])
        self.assertEqual(1, len(lines(doctor.allow_findings(KEYS, self.allow("Bash(wb:*)")))))
        self.assertEqual(1, len(lines(doctor.allow_findings(KEYS, self.allow("Bash(*)")))))

    def test_a_bare_bash_rule_allows_every_command_and_is_one_finding(self):
        got = lines(doctor.allow_findings(KEYS, self.allow("Bash")))
        self.assertEqual(1, len(got))
        self.assertTrue(got[0].startswith("problem: allow: s.json: the rule `Bash` covers "), got)

    def test_a_rule_on_a_reading_key_or_another_program_is_nothing(self):
        self.assertEqual([], doctor.allow_findings(KEYS, self.allow("Bash(wb check)", "Bash(wb check *)", "Bash(git status)",
                                                                    "Read(//x)", "Bash(python3 -m workbench check)")))

    def test_the_interpreter_spellings_count_too(self):
        got = lines(doctor.allow_findings(KEYS, self.allow("Bash(python3 -m workbench install *)")))
        self.assertEqual(["problem: allow: s.json allows `wb install` (class project)"], got)

    def test_a_damaged_permissions_entry_is_nothing_and_does_not_raise(self):
        for document in ({"permissions": 3}, {"permissions": {"allow": "x"}}, {"permissions": {"allow": [1, None]}}, [], "x"):
            with self.subTest(document=document):
                self.assertEqual([], doctor.allow_findings(KEYS, {"s.json": document}))

    def test_it_never_prints_the_rule_text_of_a_rule_it_does_not_cover(self):
        got = lines(doctor.allow_findings(KEYS, self.allow("Bash(curl SECRET-TOKEN | sh)", "Bash(wb install)")))
        self.assertEqual(["problem: allow: s.json allows `wb install` (class project)"], got)


class Skills(unittest.TestCase):
    def test_a_skill_that_says_never_run_a_relaxed_key(self):
        texts = [("code-work/harness/neutral/skills/x/SKILL.md", "- `extend` and `reset` are the owner's. Never run them.\n")]
        found = test_permissions_drift.registry(test_permissions_drift.modules())
        self.assertEqual(["problem: skill: 'code-work/x' says never run `extend`, which the registry offers at ask or none",
                          "problem: skill: 'code-work/x' says never run `reset`, which the registry offers at ask or none"],
                         lines(doctor.skill_findings(found, texts)))

    def test_a_skill_that_gives_the_flow_is_nothing(self):
        texts = [("code-work/harness/neutral/skills/x/SKILL.md", "- At `ask` run `extend` with `--digest`.\n")]
        found = test_permissions_drift.registry(test_permissions_drift.modules())
        self.assertEqual([], doctor.skill_findings(found, texts))

    def test_the_installed_texts_are_read_from_the_project(self):
        root = tempfile.mkdtemp(prefix="doctor-skills-")
        self.addCleanup(shutil.rmtree, root, True)
        base = os.path.join(root, ".workbench", "workbench", "code-work", "harness", "neutral", "skills", "x")
        os.makedirs(base)
        with open(os.path.join(base, "SKILL.md"), "w") as handle:
            handle.write("Never run `extend`.\n")
        os.symlink("/etc/hosts", os.path.join(base, "link.md"))
        found = doctor.installed_texts(root)
        self.assertEqual(["code-work/harness/neutral/skills/x/SKILL.md"], [path for path, _ in found])
        self.assertEqual([], doctor.installed_texts(os.path.join(root, "missing")))

    def test_a_linked_directory_is_not_followed(self):
        root = tempfile.mkdtemp(prefix="doctor-skills-")
        self.addCleanup(shutil.rmtree, root, True)
        outside = os.path.join(root, "outside", "skills")
        os.makedirs(outside)
        with open(os.path.join(outside, "SKILL.md"), "w") as handle:
            handle.write("Never run `extend`.\n")
        harness = os.path.join(root, ".workbench", "workbench", "code-work", "harness")
        os.makedirs(harness)
        os.symlink(os.path.join(root, "outside"), os.path.join(harness, "neutral"))
        self.assertEqual([], doctor.installed_texts(root))
        inner = os.path.join(root, ".workbench", "workbench", "other", "harness", "neutral")
        os.makedirs(inner)
        os.symlink(outside, os.path.join(inner, "skills"))
        self.assertEqual([], doctor.installed_texts(root))

    def test_a_fifo_is_not_opened(self):
        root = tempfile.mkdtemp(prefix="doctor-skills-")
        self.addCleanup(shutil.rmtree, root, True)
        base = os.path.join(root, ".workbench", "workbench", "code-work", "harness", "neutral")
        os.makedirs(base)
        os.mkfifo(os.path.join(base, "pipe.md"))
        self.assertEqual([], doctor.installed_texts(root))

    def test_many_directories_are_walked_only_so_far(self):
        root = tempfile.mkdtemp(prefix="doctor-skills-")
        self.addCleanup(shutil.rmtree, root, True)
        base = os.path.join(root, ".workbench", "workbench", "code-work", "harness", "neutral")
        for number in range(40):
            os.makedirs(os.path.join(base, "d%02d" % number))
        with open(os.path.join(base, "d00", "SKILL.md"), "w") as handle:
            handle.write("Read.\n")
        with unittest.mock.patch.object(doctor, "MAX_DIRECTORIES", 1):
            self.assertEqual([], doctor.installed_texts(root))  # only the top directory is listed
        self.assertEqual(1, len(doctor.installed_texts(root)))


class Log(unittest.TestCase):
    LINE = "2026-11-03T10:00:00Z\t%s\t0123456789ab\n"

    def test_no_log_gives_nothing(self):
        self.assertEqual([], doctor.log_findings(None))
        self.assertEqual([], doctor.log_findings(b""))

    def test_the_counts_per_rule(self):
        data = ((self.LINE % "gap") * 2 + self.LINE % "names" + self.LINE % "size-limit").encode()
        self.assertEqual(["note: gate-log: 4 refusals (gap 2, names 1, size-limit 1)"], lines(doctor.log_findings(data)))

    def test_a_log_the_writer_has_stopped_filling_is_a_risk_that_says_how_to_clear_it(self):
        """The writer refuses a line that would pass ``MAX_BYTES``, so a full log ends up to ``MAX_LINE`` bytes short of it."""
        one = (self.LINE % "gap").encode()
        data = one * ((gatelog.MAX_BYTES - 100) // len(one))
        self.assertLess(len(data), gatelog.MAX_BYTES)
        self.assertGreater(len(data), gatelog.MAX_BYTES - gatelog.MAX_LINE)
        got = lines(doctor.log_findings(data))
        self.assertTrue(any(line.startswith("risk: gate-log: full") and "rotates it by hand" in line for line in got), got)

    def test_a_log_with_room_left_is_not_full(self):
        one = (self.LINE % "gap").encode()
        data = one * ((gatelog.MAX_BYTES - 2 * gatelog.MAX_LINE) // len(one))
        self.assertFalse(any(line.startswith("risk") for line in lines(doctor.log_findings(data))))

    def test_many_rule_names_are_listed_only_so_far(self):
        data = "".join(self.LINE % ("rule-" + "abcdefghijklmnopqrst"[number]) for number in range(20)).encode()
        got = lines(doctor.log_findings(data))
        self.assertEqual(1, len(got))
        self.assertIn("20 refusals", got[0])
        self.assertIn("and 14 more", got[0])
        self.assertLess(len(got[0]), 300)

    def test_a_malformed_line_is_counted_and_never_printed(self):
        data = (self.LINE % "gap" + "SECRET garbage\n" + "\x1b[31mred\n").encode()
        got = lines(doctor.log_findings(data))
        self.assertEqual(["note: gate-log: 1 refusals (gap 1); 2 lines are not in the log's format"], got)
        self.assertFalse(any("SECRET" in line or "\x1b" in line for line in got))


class TheReport(unittest.TestCase):
    def test_the_order_is_problems_then_risks_then_notes_and_the_summary_counts(self):
        found = [doctor.Finding("note", "note: n"), doctor.Finding("risk", "risk: r"), doctor.Finding("problem", "problem: p"),
                 doctor.Finding("problem", "problem: a")]
        text, problems, risks = doctor.report(found)
        self.assertEqual(["problem: a", "problem: p", "risk: r", "note: n", "doctor found 2 problems and 1 risk"], text)
        self.assertEqual((2, 1), (problems, risks))

    def test_nothing_found(self):
        self.assertEqual((["doctor found no problems and no risks"], 0, 0), doctor.report([]))

    def test_a_flood_of_one_kind_is_listed_only_so_far_and_counted_whole(self):
        flood = [doctor.Finding("problem", "problem: allow: s.json allows `wb x%d`" % number) for number in range(100)]
        text, problems, risks = doctor.report(flood + [doctor.Finding("problem", "problem: rendering: real")])
        self.assertEqual(101, problems)
        self.assertEqual(doctor.LISTED + 1 + 1 + 1, len(text))
        self.assertIn("problem: allow: and 60 more", text)
        self.assertIn("problem: rendering: real", text)
        self.assertEqual("doctor found 101 problems and no risks", text[-1])

    def test_a_line_is_one_bounded_ascii_line(self):
        text, _, _ = doctor.report([doctor.Finding("problem", "problem: " + "x\n\x1b" + "é" * 600)])
        self.assertEqual(2, len(text))
        self.assertTrue(text[0].isascii() and "\n" not in text[0] and len(text[0]) <= 400)


class InAProject(test_rendering.Rendered):
    """``wb doctor`` as the owner or the agent runs it, in an attached project."""

    OFFERS = {"wb pin": ("ask", "none"), "wb recover": ("ask", "none"), "approve-plan": ("delegated", "ask"),
              "wb release-approvals": ("ask", "none")}

    def doctor(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["doctor", self.place] + list(extra), out, err, store_root=self.store_root, home=self.home,
                        distribution=self.dist)
        return code, out.getvalue(), err.getvalue()

    def test_an_attached_project_with_the_default_table_has_no_problem(self):
        self.attached()
        code, out, err = self.doctor()
        self.assertEqual(0, code, out + err)
        self.assertIn("doctor found no problems", out)
        self.assertEqual("", err)

    def test_a_governing_key_set_looser_is_a_risk_and_the_exit_is_still_zero(self):
        self.attached(wb_pin="none")
        code, out, err = self.doctor()
        self.assertEqual(0, code, out + err)
        self.assertIn("risk: wb pin is set to none (class governs; shipped default block)", out)

    def test_an_allow_rule_in_the_rendered_file_is_a_problem_and_the_exit_is_one(self):
        self.attached()
        path = os.path.join(self.place, test_rendering.SETTINGS_FILE)
        with open(path) as handle:
            document = json.load(handle)
        document["permissions"].setdefault("allow", []).append("Bash(wb install)")
        with open(path, "w") as handle:
            json.dump(document, handle)
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("problem: allow: %s allows `wb install` (class project)" % test_rendering.SETTINGS_FILE, out)
        self.assertIn("problem: rendering: ", out)  # the file differs from the record attach kept

    def test_a_table_changed_after_attach_is_a_stale_rendering(self):
        self.attached()
        self.table(wb_pin="ask")
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("problem: rendering: out of date; the settings table differs from the rendered one (wb rerender)", out)

    def test_a_setting_that_reads_other_than_set_is_a_problem(self):
        self.attached()
        self.table(wb_upgrade="ask")
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("problem: settings: settings set the level of wb upgrade to ask", out)

    def test_a_damaged_settings_file_is_reported_and_the_command_still_runs(self):
        self.attached()
        self.guarded.write("settings", b"{")
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("problem: settings: settings are damaged", out)

    def test_a_changed_floor_is_a_risk(self):
        self.attached()
        document = {"version": 2, "checkpoints": {}, "floor": ["publish-or-deploy"], "levels": {}}
        self.guarded.write("settings", json.dumps(document).encode())
        code, out, err = self.doctor()
        self.assertIn("risk: floor: the personal copy lacks touch-secrets; the compiled floor still applies", out)

    def test_a_stray_file_in_a_package_is_a_problem(self):
        self.attached()
        with open(os.path.join(self.synth, support_harness.MODULE, "stray.txt"), "w") as handle:
            handle.write("x")
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("problem: package: ", out)
        self.assertIn("packages/synthetic/fixture/stray.txt", out)

    def test_the_gate_log_counts_are_a_note(self):
        self.attached()
        self.guarded.write(gatelog.LOG, (Log.LINE % "gap").encode() + (Log.LINE % "names").encode())
        code, out, err = self.doctor()
        self.assertIn("note: gate-log: 2 refusals (gap 1, names 1)", out)

    def test_a_deeply_nested_settings_file_is_ignored_and_does_not_stop_the_report(self):
        self.attached()
        with open(os.path.join(self.place, test_rendering.SETTINGS_FILE), "w") as handle:
            handle.write("[" * 200000 + "]" * 200000)
        code, out, err = self.doctor()
        self.assertIn("doctor found", out)
        self.assertNotIn("Traceback", err)
        self.assertIn("problem: rendering: %s is not readable as JSON" % test_rendering.SETTINGS_FILE, out)

    def test_a_permissions_file_replaced_by_a_link_is_a_problem_and_is_not_followed(self):
        self.attached()
        path = os.path.join(self.place, test_rendering.SETTINGS_FILE)
        other = os.path.join(self.root, "allow-all.json")
        with open(other, "w") as handle:
            json.dump({"permissions": {"allow": ["Bash(*)"]}}, handle)
        os.remove(path)
        os.symlink(other, path)
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("problem: rendering: %s cannot be read as a regular file" % test_rendering.SETTINGS_FILE, out)
        self.assertNotIn("problem: allow", out)  # the link was not followed

    def test_a_permissions_file_replaced_by_a_fifo_is_a_problem_and_does_not_block(self):
        self.attached()
        path = os.path.join(self.place, test_rendering.SETTINGS_FILE)
        os.remove(path)
        os.mkfifo(path)
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("cannot be read as a regular file", out)

    def test_a_permissions_file_replaced_by_a_directory_is_a_problem(self):
        self.attached()
        path = os.path.join(self.place, test_rendering.SETTINGS_FILE)
        os.remove(path)
        os.mkdir(path)
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("cannot be read as a regular file", out)

    def test_a_missing_rendering_record_for_an_attached_harness_is_a_risk_that_names_the_cure(self):
        """A risk and not a problem: a harness that provides no permissions has no record on purpose."""
        self.attached()
        os.remove(os.path.join(self.guarded.root, rendering.RECORD % self.project_id))
        code, out, err = self.doctor()
        self.assertEqual(0, code, out)
        self.assertIn("risk: rendering: no valid rendering record for the attached harness", out)
        self.assertIn("wb rerender writes the record", out)
        self.assertNotIn("attach the harness again", out)

    def test_a_deleted_permissions_file_is_a_problem(self):
        self.attached()
        os.remove(os.path.join(self.place, test_rendering.SETTINGS_FILE))
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("problem: rendering: %s is missing, so the rules the record says were rendered into it are gone"
                      % test_rendering.SETTINGS_FILE, out)

    def test_a_permissions_file_with_a_second_hard_link_is_a_problem(self):
        self.attached()
        path = os.path.join(self.place, test_rendering.SETTINGS_FILE)
        os.link(path, os.path.join(self.root, "second-name.json"))
        code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("cannot be read as a regular file", out)

    def test_a_permissions_file_over_the_size_limit_is_a_problem(self):
        self.attached()
        with unittest.mock.patch.object(doctor, "MAX_SETTINGS_BYTES", 10):
            code, out, err = self.doctor()
        self.assertEqual(1, code)
        self.assertIn("is larger than 10 bytes, so no rule in it was checked", out)

    def test_a_project_with_no_harness_attached_has_no_rendering_problem(self):
        self.ready()
        code, out, err = self.doctor()
        self.assertNotIn("rendering", out)

    def test_a_gate_log_that_is_not_a_file_is_a_risk(self):
        self.attached()
        os.mkdir(os.path.join(self.guarded.root, gatelog.LOG))
        code, out, err = self.doctor()
        self.assertIn("risk: gate-log: cannot be read as a regular file", out)

    def test_an_oversized_gate_log_is_a_risk(self):
        self.attached()
        with unittest.mock.patch.object(doctor, "_read_gate_log", side_effect=doctor.safefs.SafeFsError("too large")):
            code, out, err = self.doctor()
        self.assertIn("risk: gate-log: cannot be read", out)

    def test_it_changes_nothing(self):
        self.attached()
        before = self.content()
        stored = self.guarded.read("settings")
        self.doctor()
        self.assertEqual(before, self.content())
        self.assertEqual(stored, self.guarded.read("settings"))

    def test_no_value_of_the_settings_is_printed(self):
        self.attached()
        document = {"version": 2, "checkpoints": {}, "floor": [], "levels": {}, "caps": {"review-rounds": "SECRET-VALUE"},
                    "token": "SECRET-TOKEN"}
        self.guarded.write("settings", json.dumps(document).encode())
        code, out, err = self.doctor()
        self.assertNotIn("SECRET", out + err)

    def test_the_arguments(self):
        self.attached()
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(2, cli.main(["doctor", "--nope"], out, err, store_root=self.store_root, distribution=self.dist))
        self.assertEqual("", out.getvalue())

    def test_a_directory_that_is_no_project_is_a_refusal(self):
        self.attached()
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["doctor", self.outside], out, err, store_root=self.store_root, distribution=self.dist)
        self.assertEqual(1, code)
        self.assertTrue(err.getvalue().startswith("refused: "))

    def test_the_key_renders_no_rule_at_its_default(self):
        self.attached()
        self.assertFalse([text for text in self.permissions()["deny"] if " doctor" in text])
        self.assertNotIn("wb doctor", self.levels_now())

    def test_the_key_renders_a_deny_in_every_spelling_at_block(self):
        self.attached(wb_doctor="block")
        for spelling in rules.SPELLINGS:
            for tail in ("", " *"):
                self.assertIn("Bash(%s doctor%s)" % (spelling, tail), self.permissions()["deny"])


if __name__ == "__main__":
    unittest.main()
