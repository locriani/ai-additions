"""Rules for GitHub issue text: no freeform issue references, and the body is a filled template."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))

import issue_rules as r  # noqa: E402

FIXTURES = HERE / "fixtures" / "ISSUE_TEMPLATE"


def template(name: str) -> r.Template:
    path = FIXTURES / f"{name}.yml"
    return r.parse_template(path.name, path.read_text())


TASK_VALUES = {
    "outcome": "backlog.py counts GitHub issues",
    "why": "The board shows unknown for the new tracker",
    "acceptance": "- [ ] count matches gh issue list\n- [ ] GitLab tests unchanged",
}

TASK_BODY = (
    "### Outcome\n\nbacklog.py counts GitHub issues\n\n"
    "### Why\n\nThe board shows unknown for the new tracker\n\n"
    "### Acceptance\n\n- [ ] count matches gh issue list\n- [ ] GitLab tests unchanged\n\n"
    "### Notes\n\n_No response_"
)


class ReferenceTest(unittest.TestCase):
    def test_each_reference_form_is_found(self):
        for text in (
            "blocked on #12",
            "see locriani/GauntletIssues#4",
            "same as GH-7",
            "https://github.com/locriani/GauntletIssues/issues/3",
            "https://github.com/locriani/chief-of-stuff/pull/9",
            "https://labs.gauntletai.com/zachgardner/openemr/-/issues/21",
            "follows issue 5",
            "after Issue #5",
            "see ticket 88",
            "waits on PR 14",
        ):
            with self.subTest(text=text):
                self.assertTrue(r.references(text), text)

    def test_code_is_not_prose(self):
        for text in (
            "```\nerror at step #12\n```",
            "the flag `--blocked-by #3` is the one",
            "### Outcome",
            "color &#35;fff",
            "a 5-step issue",
            "version 2.101",
        ):
            with self.subTest(text=text):
                self.assertEqual(r.references(text), [], text)


class TemplateTest(unittest.TestCase):
    def test_parse_reads_fields_and_labels(self):
        t = template("task")
        self.assertEqual(t.name, "Task")
        self.assertEqual(t.labels, ("enhancement",))
        self.assertEqual([f.id for f in t.fields], ["outcome", "why", "acceptance", "notes"])
        self.assertEqual([f.required for f in t.fields], [True, True, True, False])

    def test_markdown_blocks_are_not_fields(self):
        t = r.parse_template(
            "x.yml",
            "name: X\nbody:\n  - type: markdown\n    attributes:\n      value: hi\n"
            "  - type: input\n    id: a\n    attributes:\n      label: A\n",
        )
        self.assertEqual([f.id for f in t.fields], ["a"])

    def test_render_matches_github_form_output(self):
        self.assertEqual(r.render(template("task"), TASK_VALUES), TASK_BODY)

    def test_render_fences_a_render_field(self):
        body = r.render(
            template("bug"),
            {"observed": "500", "expected": "200", "repro": "1. GET /ready", "evidence": "Traceback"},
        )
        self.assertTrue(body.endswith("### Evidence\n\n```text\nTraceback\n```"), body)

    def test_caps_are_stated(self):
        t = template("bug")
        self.assertEqual(r.cap(t.fields[0]), "1 line, 100 chars")
        self.assertEqual(r.cap(t.fields[2]), "6 lines, 160 chars each")
        self.assertEqual(r.cap(t.fields[3]), "20 lines")


class BodyTest(unittest.TestCase):
    templates = (template("task"), template("bug"))

    def check(self, body: str) -> list[str]:
        return r.check_body(body, self.templates)

    def test_rendered_body_passes(self):
        self.assertEqual(self.check(TASK_BODY), [])

    def test_body_that_matches_no_template(self):
        problems = self.check("### Summary\n\nthings")
        self.assertEqual(len(problems), 1)
        self.assertIn("no template", problems[0])
        self.assertIn("Task: Outcome, Why, Acceptance, Notes", problems[0])

    def test_extra_section_matches_no_template(self):
        self.assertIn("no template", self.check(TASK_BODY + "\n\n### Context\n\nlong story")[0])

    def test_free_text_before_first_section(self):
        self.assertIn("no template", self.check("Preamble\n\n" + TASK_BODY)[0])

    def test_missing_required(self):
        body = TASK_BODY.replace("backlog.py counts GitHub issues", "_No response_")
        self.assertEqual(self.check(body), ["Outcome is required"])

    def test_input_is_one_line(self):
        body = TASK_BODY.replace("backlog.py counts GitHub issues", "one\ntwo")
        self.assertEqual(self.check(body), ["Outcome: 1 line, 100 chars (got 2 lines)"])

    def test_input_length(self):
        body = TASK_BODY.replace("backlog.py counts GitHub issues", "x" * 101)
        self.assertEqual(self.check(body), ["Outcome: 1 line, 100 chars (got 101 chars)"])

    def test_textarea_line_count(self):
        seven = "\n".join(f"- [ ] check {i}" for i in range(7))
        body = TASK_BODY.replace("- [ ] count matches gh issue list\n- [ ] GitLab tests unchanged", seven)
        self.assertEqual(self.check(body), ["Acceptance: 6 lines, 160 chars each (got 7 lines)"])

    def test_textarea_line_length(self):
        body = TASK_BODY.replace("- [ ] GitLab tests unchanged", "- [ ] " + "y" * 160)
        self.assertEqual(self.check(body), ["Acceptance: 6 lines, 160 chars each (line 2 is 166 chars)"])

    def test_blank_lines_do_not_count(self):
        body = TASK_BODY.replace("\n- [ ] GitLab", "\n\n- [ ] GitLab")
        self.assertEqual(self.check(body), [])

    def test_render_field_cap(self):
        log = "\n".join(f"line {i}" for i in range(21))
        body = r.render(
            template("bug"), {"observed": "500", "expected": "200", "repro": "1. GET", "evidence": log}
        )
        self.assertEqual(self.check(body), ["Evidence: 20 lines (got 21 lines)"])

    def test_reference_in_body(self):
        body = TASK_BODY.replace("GitLab tests unchanged", "done after #4")
        problems = self.check(body)
        self.assertEqual(len(problems), 1)
        self.assertIn("#4", problems[0])
        self.assertIn("--blocked-by", problems[0])

    def test_reference_inside_render_field_is_code(self):
        body = r.render(
            template("bug"),
            {"observed": "500", "expected": "200", "repro": "1. GET", "evidence": "step #12 failed"},
        )
        self.assertEqual(self.check(body), [])

    def test_dropdown_value_must_be_an_option(self):
        t = r.parse_template(
            "d.yml",
            "name: D\nbody:\n  - type: dropdown\n    id: area\n    attributes:\n      label: Area\n"
            "      options: [agent, board]\n    validations:\n      required: true\n",
        )
        self.assertEqual(r.check_body("### Area\n\nboard", (t,)), [])
        self.assertEqual(r.check_body("### Area\n\nkitchen", (t,)), ["Area: one of agent, board (got kitchen)"])


class TitleAndCommentTest(unittest.TestCase):
    def test_title_cap(self):
        self.assertEqual(r.check_title("t" * 72), [])
        self.assertEqual(r.check_title("t" * 73), ["title: 72 chars at most (got 73)"])

    def test_title_reference(self):
        self.assertIn("#9", r.check_title("Fix the follow-up to #9")[0])

    def test_empty_title(self):
        self.assertEqual(r.check_title("  "), ["title is empty"])

    def test_comment_passes(self):
        self.assertEqual(r.check_comment("Deployed. `/ready` returns 200."), [])

    def test_comment_cap(self):
        self.assertEqual(
            r.check_comment("\n".join("x" for _ in range(7))), ["comment: 6 lines, 160 chars each (got 7 lines)"]
        )

    def test_comment_reference(self):
        self.assertIn("#2", r.check_comment("dup of #2")[0])


if __name__ == "__main__":
    unittest.main()
