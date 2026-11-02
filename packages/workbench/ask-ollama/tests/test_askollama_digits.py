"""The guard against a run of more than 4,300 digits is linear and exact (security review of increments D and E, plan
`2026-11-02-bridge-request-controls`): a hostile reply of runs just under the limit used to cost about 4.6 seconds a megabyte,
past `--timeout`. The bounds are generous (a hundred times the cost of the linear guard) so that a slow machine does not fail
them, and far below the cost of the quadratic one."""

import json
import time
import unittest

import support_ollama

RUN = b"9" * 4300 + b","


class Timing(support_ollama.Bridge):
    def runs(self, size, digits=4300):
        unit = b"9" * digits + b","
        return b"[" + unit * (size // len(unit)) + b"0]"

    def test_the_parser_handles_a_hostile_body_of_long_runs_quickly(self):
        for digits in (4300, 4000, 4299):
            data = self.runs(3000000, digits)
            started = time.perf_counter()
            value = self.helper.parse_json(data)
            elapsed = time.perf_counter() - started
            self.assertEqual(0, value[-1])
            self.assertLess(elapsed, 3.0, "%d-digit runs took %.2f s" % (digits, elapsed))

    def test_a_whole_call_with_a_hostile_5xx_body_ends_quickly(self):
        self.fake.reply(self.runs(3000000), status=503)
        started = time.perf_counter()
        code, out, err = self.ask()
        elapsed = time.perf_counter() - started
        document = json.loads(out)
        self.assertEqual((1, "bad_exit", True), (code, document["detail"], document["retryable"]))
        self.assertLess(elapsed, 5.0, "the call took %.2f s" % elapsed)

    def test_the_endpoint_file_reader_handles_a_hostile_file_quickly(self):
        self.write_endpoint_file(b"[" + RUN * (250000 // len(RUN)) + b"0]")
        started = time.perf_counter()
        self.refused(command="check", contains="strict JSON")
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 0.5, "the file took %.2f s" % elapsed)


class Edges(support_ollama.Bridge):
    """The guard refuses a run of 4,301 digits or more wherever it starts, and not a run of 4,300 or fewer."""

    def refuses(self, data):
        with self.assertRaises(ValueError):
            self.helper.parse_json(data)

    def test_a_run_of_4300_is_accepted_and_a_run_of_4301_is_refused_in_each_position(self):
        for length, accepted in ((4299, True), (4300, True), (4301, False), (4302, False), (9000, False)):
            for before, after in ((b"[", b"]"), (b"[-", b"]"), (b'["', b'"]'), (b'["x', b'y"]'), (b'{"a": "', b'"}')):
                data = before + b"7" * length + after
                if accepted:
                    self.assertIsNotNone(self.helper.parse_json(data), (length, before))
                else:
                    self.refuses(data)

    def test_runs_that_are_each_short_enough_are_accepted_however_many_there_are(self):
        data = b"[" + (b"7" * 4300 + b",") * 20 + b"0]"
        self.assertEqual(21, len(self.helper.parse_json(data)))

    def test_a_run_split_by_one_character_is_two_short_runs(self):
        self.assertEqual(2, len(self.helper.parse_json(b'["' + b"7" * 4300 + b' ", "' + b"7" * 4300 + b'"]')))
        self.refuses(b'["' + b"7" * 4300 + b"7" + b'"]')

    def test_the_pattern_is_the_one_with_the_lookbehind(self):
        self.assertIn(b"(?<![0-9])", self.helper._DIGIT_RUN)


if __name__ == "__main__":
    unittest.main()
