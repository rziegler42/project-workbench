"""The default ``review-profiles.json`` that ``wb install`` writes (plan `2026-11-04-review-profiles`, increment J;
`docs/specs/review-profiles.md`, "The default `wb install` writes").

The installer names no module, so the builder works from what the selected modules declare: a module that provides ``model-bridge`` and
has exactly one command that takes ``ask`` is a bridge, named by that command. The modules here are made up."""

import json
import types
import unittest
import unittest.mock

from workbench import profiledefault
from workbench.wbkit import profiles


def command(name, *arguments):
    return types.SimpleNamespace(name=name, arguments=tuple(arguments or ("ask",)))


def verified(name, provides=("model-bridge",), commands=None):
    return types.SimpleNamespace(name=name, module=types.SimpleNamespace(
        provides=tuple(provides), commands=tuple(commands if commands is not None else [command(name)])))


def document(default):
    return json.loads(default.data.decode("ascii"))


class Builder(unittest.TestCase):
    def test_one_bridge_gives_one_profile_that_names_the_bridge_and_nothing_else_and_the_default_ladder(self):
        got = profiledefault.build([verified("bridge-one")])
        self.assertEqual({"format": 1, "profiles": {"bridge-one": {"bridge": "bridge-one"}},
                          "ladders": {"default": ["bridge-one"]}}, document(got))

    def test_only_the_default_ladder_is_written_because_the_other_keys_belong_to_engines(self):
        got = document(profiledefault.build([verified("bridge-one")]))
        self.assertEqual(["default"], list(got["ladders"]))

    def test_several_bridges_give_profiles_and_no_ladder_and_a_line_that_says_a_review_is_refused(self):
        got = profiledefault.build([verified("bridge-b"), verified("bridge-a")])
        body = document(got)
        self.assertEqual(["bridge-a", "bridge-b"], list(body["profiles"]))
        self.assertEqual({}, body["ladders"])
        self.assertTrue(any("refused until" in line for line in got.notes), got.notes)

    def test_no_bridge_gives_no_file(self):
        for chosen in ([], [verified("tool", provides=("peer-review",))], [verified("tool", provides=())]):
            got = profiledefault.build(chosen)
            self.assertIsNone(got.data)
            self.assertTrue(any("no model bridge" in line for line in got.notes), got.notes)

    def test_a_capability_with_a_prefix_is_not_the_bridge_capability(self):
        self.assertIsNone(profiledefault.build([verified("tool", provides=("p:model-bridge",))]).data)

    def test_the_profile_names_nothing_but_the_bridge(self):
        profile = document(profiledefault.build([verified("bridge-one")]))["profiles"]["bridge-one"]
        self.assertEqual({"bridge": "bridge-one"}, profile)

    def test_a_module_with_no_ask_command_or_with_two_makes_no_profile_and_says_why(self):
        for commands in ([command("only-check", "check")], [command("one", "ask"), command("two", "ask", "check")], []):
            got = profiledefault.build([verified("bridge-one", commands=commands), verified("bridge-two")])
            self.assertEqual(["bridge-two"], list(document(got)["profiles"]))
            self.assertTrue(any("bridge-one" in line and "no profile" in line for line in got.notes), got.notes)

    def test_a_command_that_is_not_a_profile_name_makes_no_profile_and_says_why(self):
        for name in ("Bridge-One", "b" * 33, "-bridge", "bridge one", "bridge.one"):
            got = profiledefault.build([verified("m", commands=[command(name)]), verified("bridge-two")])
            self.assertEqual(["bridge-two"], list(document(got)["profiles"]), name)
            self.assertTrue(any("no profile" in line for line in got.notes), got.notes)

    def test_a_name_that_the_module_chose_is_shown_as_escaped_ascii_and_cannot_add_a_line(self):
        got = profiledefault.build([verified("m", commands=[command("bad\nname\x1b[2J" + "z" * 200)])])
        for line in got.notes:
            self.assertNotIn("\n", line)
            self.assertTrue(all(" " <= char <= "~" for char in line), repr(line))
            self.assertLess(len(line), 400)

    def test_more_profiles_than_a_file_may_hold_give_no_file(self):
        got = profiledefault.build([verified("bridge-%02d" % n) for n in range(profiles.MAX_PROFILES + 1)])
        self.assertIsNone(got.data)
        self.assertTrue(any("more than" in line for line in got.notes), got.notes)

    def test_the_bytes_are_deterministic_and_pass_the_kit_reader(self):
        chosen = [verified("bridge-b"), verified("bridge-a")]
        first, second = profiledefault.build(chosen), profiledefault.build(list(reversed(chosen)))
        self.assertEqual(first.data, second.data)
        self.assertTrue(first.data.endswith(b"\n"))
        parsed = profiles.parse(first.data, ("default",), ())
        self.assertEqual({"bridge-a", "bridge-b"}, set(parsed.profiles))
        one = profiledefault.build([verified("bridge-one")])
        parsed = profiles.parse(one.data, ("default",), ())
        self.assertEqual(("bridge-one",), parsed.ladders["default"])

    def test_a_profile_line_names_the_module_as_well_as_the_command(self):
        got = profiledefault.build([verified("module-one", commands=[command("bridge-one")])])
        line = next(line for line in got.notes if line.startswith("profile "))
        self.assertIn("bridge-one", line)
        self.assertIn("module-one", line)

    def test_two_modules_with_one_bridge_command_make_one_profile_and_a_note_naming_both(self):
        got = profiledefault.build([verified("module-a", commands=[command("same")]),
                                    verified("module-b", commands=[command("same")])])
        self.assertEqual(["same"], list(document(got)["profiles"]))
        line = next(line for line in got.notes if "module-a" in line and "module-b" in line)
        self.assertIn("same", line)

    def test_the_notes_show_the_file_exactly_as_it_will_be_written(self):
        for chosen in ([verified("bridge-one")], [verified("bridge-a"), verified("bridge-b")]):
            got = profiledefault.build(chosen)
            text = got.data.decode("ascii")
            self.assertIn("the file, exactly as it will be written:", got.notes)
            start = got.notes.index("the file, exactly as it will be written:") + 1
            self.assertEqual(["| " + line for line in text.splitlines()], list(got.notes[start:start + len(text.splitlines())]))

    def test_the_bytes_are_ascii_and_within_the_files_bound(self):
        got = profiledefault.build([verified("bridge-%02d" % n) for n in range(profiles.MAX_PROFILES)])
        self.assertLess(len(got.data), profiles.MAX_BYTES)
        got.data.decode("ascii")

    def test_nothing_is_taken_from_the_environment(self):
        with unittest.mock.patch.dict("os.environ", {"HOME": "/nonexistent-home"}):
            first = profiledefault.build([verified("bridge-one")])
        self.assertEqual(first.data, profiledefault.build([verified("bridge-one")]).data)


class Existing(unittest.TestCase):
    def test_an_existing_file_is_left_as_it_is_and_no_bytes_are_planned(self):
        got = profiledefault.plan([verified("bridge-one")], present=True)
        self.assertIsNone(got.data)
        self.assertTrue(any("left as it is" in line for line in got.notes), got.notes)

    def test_an_absent_file_is_planned(self):
        self.assertIsNotNone(profiledefault.plan([verified("bridge-one")], present=False).data)


class Removed(unittest.TestCase):
    def test_the_code_that_showed_an_old_project_file_is_gone_because_a_target_with_one_is_refused(self):
        for name in ("read_old", "old_setting_lines", "OLD", "MAX_OLD", "MAX_SHOWN"):
            self.assertFalse(hasattr(profiledefault, name), name)


if __name__ == "__main__":
    unittest.main()
