"""The ``--collect`` flag of ``review`` (`docs/specs/action-review.md`, "The shadow hook", "The engine's collect lines").

Plan `2026-10-29-action-review-shadow-hook`, increment B. With the flag the engine prints, on standard error after any
``log-row:`` line, a ``facts:`` line when `describe` produced a valid object and an ``outcome:`` line on every exit, so the
shadow hook never reruns `describe` or parses the command. Without the flag nothing changes. Written before the code."""

import io
import json
import unittest
import unittest.mock

from test_actionreview_output import (Base, Breaking, COMMAND, Fakes, MARKER, answered, bridge_failed, commit_doc,
                                      described, reply)
from workbench.wbkit import call

def bridge_error(error, detail=None):
    """The answer of a bridge that was run and reported `error` itself (exit 1, an ok-false object)."""
    document = {"contract": 1, "ok": False, "vendor": "codex", "error": error, "detail": detail, "retryable": False,
                "message": MARKER}
    return call.Result(1, json.dumps(document).encode("utf-8") + b"\n", b"", False, False)


NO_RULE = "ask-codex archive"
REASONS = ("reviewed", "no_rule", "unreviewable", "refused", "failed", "timeout")


def extra(err, prefix):
    return [line for line in err.splitlines() if line.startswith(prefix)]


def strip(err):
    return "".join(line + "\n" for line in err.splitlines() if not line.startswith(("facts: ", "outcome: ")))


class Collect(Base):
    def collected(self, text=COMMAND, flags=("--collect",), **kwargs):
        return self.run_main(["review", *flags, text], **kwargs)

    def outcome(self, err):
        lines = extra(err, "outcome: ")
        self.assertEqual(1, len(lines), err)
        self.assertTrue(err.endswith(lines[0] + "\n"), "the outcome is the last line")
        body = json.loads(lines[0][len("outcome: "):])
        self.assertEqual(["reason"], list(body))
        self.assertIn(body["reason"], REASONS)
        return body["reason"]

    # The cases: (name, keyword arguments of run_main, text, exit code, reason, whether describe produced an object).
    def cases(self):
        timed_out = call.Result(0, b"", b"", False, True)
        return [
            ("approve", {}, COMMAND, 0, "reviewed", True),
            ("model decline", {"bridge": answered(reply("decline", ["scope_is_coherent"], "Mixed."))}, COMMAND, 0,
             "reviewed", True),
            ("code decline", {"describe": described(commit_doc(head="b" * 40))}, COMMAND, 0, "reviewed", True),
            ("no rule", {}, NO_RULE, 1, "no_rule", False),
            ("push is no rule", {}, "git push origin main", 1, "no_rule", False),
            ("outside the grammar", {}, COMMAND + " && ls", 1, "unreviewable", False),
            ("a flag not declared", {}, COMMAND + " --force", 1, "unreviewable", False),
            ("describe fails", {"describe": call.Result(1, b"", b"", False, False)}, COMMAND, 1, "refused", False),
            ("describe times out", {"describe": call.Result(0, b"", b"", False, True)}, COMMAND, 1, "timeout", False),
            ("describe too large", {"describe": call.Result(0, b"", b"", True, False)}, COMMAND, 1, "refused", False),
            ("describe malformed", {"describe": call.Result(0, b"not an object\n", b"", False, False)}, COMMAND, 1,
             "refused", False),
            ("no setting", {"root": "no setting"}, COMMAND, 1, "refused", True),
            ("bridge refused", {"bridge": call.Result(1, b"", b"", False, False)}, COMMAND, 1, "refused", True),
            ("bridge fails", {"bridge": bridge_error("program_not_found")}, COMMAND, 2, "failed", True),
            ("bridge reports its own timeout", {"bridge": bridge_failed()}, COMMAND, 2, "timeout", True),
            ("bridge reports a vendor error", {"bridge": bridge_error("vendor_error", "rate_limited")}, COMMAND, 2,
             "failed", True),
            ("bridge reply unusable", {"bridge": answered("not json")}, COMMAND, 2, "failed", True),
            ("bridge times out", {"bridge": timed_out}, COMMAND, 2, "timeout", True),
        ]

    def run_case(self, kwargs, text, flags):
        kwargs = dict(kwargs)
        if kwargs.pop("root", None) == "no setting":
            kwargs["root"] = self.project(setting=None)
        return self.run_main(["review", *flags, text], **kwargs)

    def test_every_exit_prints_one_outcome_line_last_with_the_expected_reason(self):
        for name, kwargs, text, code, reason, _ in self.cases():
            got, out, err, _ = self.run_case(kwargs, text, ("--collect",))
            self.assertEqual(code, got, (name, err))
            self.assertEqual(reason, self.outcome(err), (name, err))
            self.assertEqual(code != 0, out == "", name)

    def test_the_outcome_line_is_strict_json_of_one_field_and_short(self):
        for name, kwargs, text, _, _, _ in self.cases():
            _, _, err, _ = self.run_case(kwargs, text, ("--collect",))
            line = extra(err, "outcome: ")[0]
            self.assertLessEqual(len(line), 64, name)
            self.assertTrue(all(" " <= c <= "~" for c in line), name)

    def test_the_facts_line_is_present_exactly_when_describe_produced_an_object(self):
        for name, kwargs, text, _, _, ran in self.cases():
            _, _, err, _ = self.run_case(kwargs, text, ("--collect",))
            self.assertEqual(1 if ran else 0, len(extra(err, "facts: ")), (name, err))

    def test_the_facts_line_is_the_canonical_json_of_the_object_as_received(self):
        document = commit_doc()
        _, _, err, _ = self.collected()
        line = extra(err, "facts: ")[0][len("facts: "):]
        self.assertEqual(document, json.loads(line))
        self.assertEqual(json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":")), line)

    def test_the_facts_line_comes_before_the_outcome_and_after_the_row(self):
        _, _, err, _ = self.collected(flags=("--log-row", "--collect"))
        kinds = [line.split(":")[0] for line in err.splitlines()]
        self.assertEqual(["log-row", "facts", "outcome"], kinds)

    def test_the_two_flags_are_accepted_in_either_order_and_agree(self):
        first = self.collected(flags=("--log-row", "--collect"))
        second = self.collected(flags=("--collect", "--log-row"))
        self.assertEqual(first[:3], second[:3])

    def test_the_collect_flag_alone_prints_no_row(self):
        _, _, err, _ = self.collected()
        self.assertEqual([], extra(err, "log-row: "))

    def test_a_flag_given_twice_or_unknown_is_a_usage_refusal_with_an_outcome(self):
        for flags in (("--collect", "--collect"), ("--log-row", "--log-row", "--collect"), ("--collect", "--other")):
            code, out, err, fakes = self.collected(flags=flags)
            self.assertEqual((1, ""), (code, out), flags)
            self.assertIn("refused: usage: ", err)
            self.assertEqual("refused", self.outcome(err), flags)
            self.assertEqual([], fakes.calls)

    def test_a_repeated_flag_is_read_as_the_text_as_it_always_was(self):
        # Without --collect the call reads exactly what it read before: one leading --log-row, then one text. A second
        # --log-row is that text, so it is refused as a command, not as a usage error.
        code, out, err, fakes = self.run_main(["review", "--log-row", "--log-row"])
        self.assertEqual((1, ""), (code, out))
        self.assertTrue(err.startswith("refused: "), err)
        self.assertNotIn("usage:", err)
        self.assertEqual([], fakes.calls)
        code, out, err, _ = self.run_main(["review", "--log-row", "--log-row", COMMAND])
        self.assertIn("usage:", err)

    def test_a_text_equal_to_a_flag_is_a_command_that_no_rule_matches(self):
        for flags in (("--collect",), ("--log-row", "--collect")):
            for text in ("--collect", "--log-row"):
                if text in flags:
                    code, out, err, fakes = self.collected(text=text, flags=flags)
                    self.assertEqual((1, ""), (code, out), (flags, text))
                    self.assertEqual("no_rule", self.outcome(err), (flags, text))
                    self.assertEqual([], fakes.calls)

    def test_a_usage_error_with_the_flag_and_no_text_still_prints_an_outcome(self):
        code, out, err, _ = self.run_main(["review", "--collect"])
        self.assertEqual((1, ""), (code, out))
        self.assertEqual("refused", self.outcome(err))
        self.assertEqual([], extra(err, "facts: "))

    def test_without_the_flag_standard_output_error_and_the_exit_code_are_unchanged(self):
        for name, kwargs, text, _, _, _ in self.cases():
            for flags in ((), ("--log-row",)):
                plain = self.run_case(kwargs, text, flags)
                flagged = self.run_case(kwargs, text, tuple(flags) + ("--collect",))
                self.assertEqual(plain[0], flagged[0], name)
                self.assertEqual(plain[1], flagged[1], name)
                self.assertEqual(strip(flagged[2]), plain[2], name)
                self.assertEqual([], extra(plain[2], "facts: ") + extra(plain[2], "outcome: "), name)

    def test_the_verdict_object_and_the_exit_table_are_not_changed_by_the_flag(self):
        plain = self.review()
        flagged = self.collected()
        self.assertEqual((plain[0], plain[1]), (flagged[0], flagged[1]))

    def test_the_command_is_parsed_once_and_describe_runs_once(self):
        _, _, _, fakes = self.collected()
        self.assertEqual(1, len([c for c in fakes.calls if c[0] == "safe-git"]))

    def test_the_outcome_follows_the_failure_line_and_the_rule_errors_come_first(self):
        _, _, err, _ = self.collected(bridge=bridge_failed())
        kinds = [line.split(":")[0] for line in err.splitlines()]
        self.assertEqual(["facts", "failed", "outcome"], kinds)
        self.assertNotIn(MARKER, err)

    def test_an_internal_error_is_failed_and_its_text_is_not_quoted(self):
        with unittest.mock.patch.object(self.helper, "judge", side_effect=ZeroDivisionError(MARKER)):
            code, out, err, _ = self.collected()
        self.assertEqual((2, ""), (code, out))
        self.assertEqual("failed", self.outcome(err))
        self.assertNotIn(MARKER, err)

    def test_an_interrupt_inside_the_review_is_failed(self):
        for exc in (KeyboardInterrupt(), SystemExit(0)):
            code, out, err, _ = self.collected(bridge=exc)
            self.assertEqual((2, ""), (code, out), repr(exc))
            self.assertEqual("failed", self.outcome(err), repr(exc))

    def test_a_facts_line_over_the_bound_is_left_out_and_the_outcome_stays(self):
        with unittest.mock.patch.object(self.helper, "MAX_FACTS_LINE", 100):
            code, out, err, _ = self.collected()
        self.assertEqual(0, code)
        self.assertEqual([], extra(err, "facts: "))
        self.assertEqual("reviewed", self.outcome(err))

    def test_a_facts_line_is_ascii_whatever_the_object_holds(self):
        document = commit_doc(subject="café ‮")
        _, _, err, _ = self.collected(describe=described(document))
        line = extra(err, "facts: ")[0]
        self.assertTrue(all(" " <= c <= "~" for c in line))
        self.assertEqual(document, json.loads(line[len("facts: "):]))

    def test_a_failed_write_of_the_verdict_is_failed_with_an_outcome_when_standard_error_works(self):
        root = self.project()
        fakes = Fakes(described(commit_doc()), answered(reply()))
        out, err = Breaking(0), io.StringIO()
        with unittest.mock.patch.object(self.helper.call, "run_command", fakes):
            code = self.helper.main(["review", "--collect", COMMAND], io.BytesIO(b""), out, err, root)
        self.assertEqual(2, code)
        self.assertEqual("failed", self.outcome(err.getvalue()))

    def test_a_broken_standard_error_still_gives_exit_2(self):
        root = self.project()
        fakes = Fakes(described(commit_doc()), answered(reply()))
        with unittest.mock.patch.object(self.helper.call, "run_command", fakes):
            code = self.helper.main(["review", "--collect", COMMAND], io.BytesIO(b""), io.StringIO(), Breaking(0), root)
        self.assertEqual(2, code)

    def test_the_outcome_does_not_depend_on_the_hook_reading_the_command(self):
        # The reason comes from the engine's own path: the same text gives the same reason in every run.
        first = self.run_case({}, NO_RULE, ("--collect",))
        second = self.run_case({}, NO_RULE, ("--collect",))
        self.assertEqual(first[2], second[2])


if __name__ == "__main__":
    unittest.main()
