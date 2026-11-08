"""The shape of a python here-document that the command gate reads for its words and not for gaps: ``command_gate.python_heredoc``.

Plan ``2026-11-08-python-heredoc-gate``, increment A (decision ``2026-11-03-a-python-script-in-a-quoted-heredoc-is-not-read-for-gaps``,
1). The function recognises the shape on the raw text and returns its first line, or ``None`` for everything else. It is
not called by the gate yet; increment B wires it in."""

import unittest

from workbench import command_gate

shaped = command_gate.python_heredoc

BODY = "print('hi')\n"


def doc(head="python3 - <<'EOF'", body=BODY, tag="EOF", tail="\n"):
    """A command: the first line, the body (lines each ending in a newline), the terminator and what follows it."""
    return head + "\n" + body + tag + tail


class Shaped(unittest.TestCase):
    def test_the_plain_form_returns_its_first_line(self):
        self.assertEqual("python3 - <<'EOF'", shaped(doc()))

    def test_python_and_python3(self):
        for head in ("python - <<'EOF'", "python3 - <<'EOF'"):
            with self.subTest(head=head):
                self.assertEqual(head, shaped(doc(head)))

    def test_the_four_flags_alone_and_together(self):
        for flags in ("-B", "-I", "-E", "-u", "-I -B", "-B -I -E -u", "-u -u"):
            head = "python3 %s - <<'EOF'" % flags
            with self.subTest(head=head):
                self.assertEqual(head, shaped(doc(head)))

    def test_a_quoted_or_escaped_delimiter(self):
        for head in ("python3 - <<'EOF'", 'python3 - <<"EOF"', "python3 - <<\\EOF"):
            with self.subTest(head=head):
                self.assertEqual(head, shaped(doc(head)))

    def test_other_tags(self):
        for tag in ("E", "PYEOF", "end_of_script", "_x", "a1", "X" * 32):
            head = "python3 - <<'%s'" % tag
            with self.subTest(tag=tag):
                self.assertEqual(head, shaped(doc(head, tag=tag)))

    def test_a_cd_prefix_with_a_plain_token(self):
        for path in ("docs", "/tmp/x/y", "a.b-c_d", "a@b", "a:b", "a=b", "a,b", "a+b", "..", "-"):
            head = "cd %s && python3 -I - <<'EOF'" % path
            with self.subTest(path=path):
                self.assertEqual(head, shaped(doc(head)))

    def test_with_and_without_the_final_newline(self):
        self.assertEqual("python3 - <<'EOF'", shaped(doc(tail="")))
        self.assertEqual("python3 - <<'EOF'", shaped(doc(tail="\n")))

    def test_an_empty_body(self):
        self.assertEqual("python3 - <<'EOF'", shaped("python3 - <<'EOF'\nEOF"))

    def test_a_body_that_holds_anything_a_shell_would_read(self):
        bodies = (
            "x = ``name``\n",
            "x = `echo hi` + $(id) + ${HOME} + $HOME\n",
            "x = '*' + '[a]' + '{b}' + '?'\n",
            "x = \"it's\" + 'say \"hi\"' + '\\\\'\n",
            "wb release-approvals\n",
            "line one \\\n",
            "\n\n\n",
            "\tEOF\n",
            "EOF \n",
            "EOFX\n",
            "XEOF\n",
            "eof\n",
            "EOF\r\n",
            "\x0bEOF\n",
            "EOF\x0b\n",
            "EOF\x0c\n",
            "EOF\x85\n",
            "EOF\u2028\n",
            "a\u2028EOF\n",
            "a\x85EOF\n",
            "a\rEOF\n",
        )
        for body in bodies:
            with self.subTest(body=body):
                self.assertEqual("python3 - <<'EOF'", shaped(doc(body=body)))

    def test_a_body_with_line_separators_python_splits_on_is_still_one_body(self):
        """``str.splitlines`` would end the body at these; bash does not, and neither does the recogniser."""
        for separator in ("\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            body = "a" + separator + "EOF" + separator + "echo done\n"
            with self.subTest(separator=repr(separator)):
                self.assertEqual("python3 - <<'EOF'", shaped(doc(body=body)))


class NotShaped(unittest.TestCase):
    def none(self, text):
        self.assertIsNone(shaped(text), repr(text))

    def test_no_terminator(self):
        for text in ("python3 - <<'EOF'\nprint(1)\n", "python3 - <<'EOF'\nprint(1)", "python3 - <<'EOF'\n", "python3 - <<'EOF'",
                     "python3 - <<'EOF'\nEO", "python3 - <<'EOF'\nEOFX"):
            with self.subTest(text=text):
                self.none(text)

    def test_a_line_that_only_looks_like_the_tag_does_not_end_the_text(self):
        for tag in ("EOF ", "EOF\r", " EOF", "\tEOF", "eof", "Eof", "EOF\x0b", "EOF\u2028"):
            with self.subTest(tag=repr(tag)):
                self.none(doc(tag=tag))

    def test_text_after_the_terminator(self):
        for tail in ("\necho done", "\necho done\n", "\n\n", "\n \n", "\nEOF", "\nEOF\n", "\n\nEOF", "\r\n", "\n\r\n"):
            with self.subTest(tail=repr(tail)):
                self.none(doc(tail=tail))

    def test_the_tag_line_twice_or_a_command_after_the_first(self):
        self.none("python3 - <<'EOF'\nprint(1)\nEOF\nwb $(echo release)-approvals\nEOF\n")
        self.none("python3 - <<'EOF'\nEOF\nEOF\n")
        self.none("python3 - <<'EOF'\nEOF\nid\n")

    def test_other_interpreters_and_spellings(self):
        for head in ("bash <<'EOF'", "sh <<'EOF'", "zsh <<'EOF'", "dash <<'EOF'", "bash - <<'EOF'", "sh -s <<'EOF'",
                     "env python3 - <<'EOF'", "sudo python3 - <<'EOF'", "python3.13 - <<'EOF'", "/usr/bin/python3 - <<'EOF'",
                     "python2 - <<'EOF'", "pythonX - <<'EOF'", "Python3 - <<'EOF'", "python3- <<'EOF'", "python3 -<<'EOF'",
                     "python3  - <<'EOF'", "python3 -  <<'EOF'", "python3 -\t<<'EOF'", "python3\t- <<'EOF'", "python3 -I\t- <<'EOF'",
                     "python3 - <<'EOF'  ", " python3 - <<'EOF'", "python3 - <<  'EOF'", "python3 - << 'EOF'",
                     "eval python3 - <<'EOF'", "cat <<'EOF'", "cat - <<'EOF'", "tee x <<'EOF'", "xargs <<'EOF'",
                     "git commit -F - <<'EOF'", "source /dev/stdin <<'EOF'", ". /dev/stdin <<'EOF'"):
            with self.subTest(head=head):
                self.none(doc(head))

    def test_flags_other_than_the_four_and_stuck_flags(self):
        for flags in ("-c", "-m", "-S", "-W", "-X", "-O", "-OO", "-s", "-q", "-i", "-V", "-b", "-d", "-v", "-BI", "-IB", "-Iu",
                      "-B-I", "--", "-", "-I -c", "-x", "-I \t-B", "--version", "-W error", "-m json.tool"):
            head = "python3 %s - <<'EOF'" % flags
            with self.subTest(head=head):
                self.none(doc(head))

    def test_arguments_after_the_dash(self):
        for head in ("python3 - arg <<'EOF'", "python3 - -B <<'EOF'", "python3 - - <<'EOF'", "python3 script.py <<'EOF'",
                     "python3 <<'EOF'", "python3 -I <<'EOF'", "python3 -c 'x' - <<'EOF'"):
            with self.subTest(head=head):
                self.none(doc(head))

    def test_an_unquoted_delimiter_and_the_other_here_forms(self):
        for head in ("python3 - <<EOF", "python3 - <<-EOF", "python3 - <<-'EOF'", "python3 - <<<EOF", "python3 - <<<'EOF'",
                     "python3 - <<'EOF'<<'EOF'", "python3 - <<'EOF' <<'EOF'", "python3 - <<'EOF' <<'END'", "python3 - < <(echo)",
                     "python3 - <<\"EOF'", "python3 - <<'EOF\"", "python3 - <<'EOF", "python3 - <<EOF'", "python3 - <<\\'EOF'",
                     "python3 - <<$'EOF'", "python3 - <<$\"EOF\"", "python3 - <<\\\\EOF", "python3 - <<''", "python3 - <<\"\"",
                     "python3 - <<\\"):
            with self.subTest(head=head):
                self.none(doc(head))

    def test_a_tag_that_could_differ_from_the_line_that_ends_the_body(self):
        for tag in ("E\"O\"F", "E'O'F", "EO\\F", "E O F", "E$F", "E`F", "E(F", "E;F", "E&F", "E|F", "E>F", "E<F", "E*F", "E?F"):
            for head in ("python3 - <<'%s'" % tag, 'python3 - <<"%s"' % tag, "python3 - <<%s" % tag):
                with self.subTest(head=head):
                    self.none(doc(head, tag=tag))

    def test_a_valid_tag_outside_the_alphabet_or_too_long_is_judged_as_today(self):
        for tag in ("E-F", "E.F", "1EOF", "É", "EÉF", "X" * 33, "X" * 100, "0"):
            head = "python3 - <<'%s'" % tag
            with self.subTest(tag=tag):
                self.none(doc(head, tag=tag))

    def test_a_tag_that_matches_only_in_part(self):
        self.none(doc("python3 - <<'EOF'", tag="EOF"[:2] + "\n"))
        self.none("python3 - <<'EOF'\nprint(1)\nEOF1\n")

    def test_anything_after_the_tag_on_the_first_line(self):
        for after in ("; id", " ;id", ";id", " > out", ">out", " | cat", " && id", " || id", " & ", " ", "\t", " # c", " 2>&1",
                      " >&2", " 2>/dev/null", " arg", " -", " )", " }", "\\"):
            head = "python3 - <<'EOF'" + after
            with self.subTest(head=head):
                self.none(doc(head))

    def test_a_cd_prefix_that_is_not_plain(self):
        for prefix in ("cd $HOME && ", "cd ~ && ", "cd 'a b' && ", 'cd "a" && ', "cd a; ", "cd a && cd b && ", "cd a || ", "cd a | ",
                       "cd a & ", "cd a&& ", "cd a  && ", "cd  a && ", "cd && ", "cd a b && ", "cd a/$(id) && ", "cd `id` && ",
                       "cd a* && ", "cd a? && ", "cd [a] && ", "cd {a,b} && ", "cd a\\ b && ", "(cd a) && ", "cd a && FOO=1 ",
                       "FOO=1 ", "export A=1 && ", "true && ", "pushd a && ", "cd a >x && ", "cd\ta && ", "CD a && ", "echo hi\n",
                       "cd a\n"):
            head = prefix + "python3 - <<'EOF'"
            with self.subTest(prefix=prefix):
                self.none(doc(head))

    def test_a_nul_byte_anywhere(self):
        for text in (doc(body="a\0b\n"), "python3 - <<'EOF'\0\nx\nEOF\n", doc(head="python3\0 - <<'EOF'"), "\0" + doc(),
                     doc(tag="EOF\0")):
            with self.subTest(text=repr(text)):
                self.none(text)

    def test_text_before_the_first_line_or_a_different_first_line(self):
        for text in ("\n" + doc(), " " + doc(), "echo hi\n" + doc(), "# c\n" + doc(), "\r\n" + doc(), doc().replace("\n", "\r\n", 1)):
            with self.subTest(text=repr(text)):
                self.none(text)

    def test_empty_and_odd_inputs(self):
        for text in ("", "\n", "python3", "python3 -", "python3 - <<'EOF'\n\n", "EOF", "<<'EOF'\nEOF\n", "\nEOF\n"):
            with self.subTest(text=repr(text)):
                self.none(text)

    def test_a_case_that_differs(self):
        for head in ("PYTHON3 - <<'EOF'", "python3 -i - <<'EOF'", "python3 -b - <<'EOF'", "python3 -e - <<'EOF'", "python3 -U - <<'EOF'"):
            with self.subTest(head=head):
                self.none(doc(head))

    def test_the_result_is_a_string_for_the_shape_only(self):
        self.assertIsInstance(shaped(doc()), str)
        self.assertIsNone(shaped(doc(tail="\nid\n")))


if __name__ == "__main__":
    unittest.main()
