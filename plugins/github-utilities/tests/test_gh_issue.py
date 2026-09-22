"""`gh-issue`: file an issue from a repo's own template, with native relationships, or refuse."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures" / "ISSUE_TEMPLATE"
BIN = HERE.parent / "bin" / "gh-issue"

_loader = importlib.machinery.SourceFileLoader("gh_issue", str(BIN))
_spec = importlib.util.spec_from_loader("gh_issue", _loader)
cli = importlib.util.module_from_spec(_spec)
_loader.exec_module(cli)

REPO = "locriani/GauntletIssues"


class FakeGh:
    """Answers the three `gh` calls the tool makes; records every argv."""

    def __init__(self, templates: Path | None = FIXTURES, create_rc: int = 0):
        self.templates = templates
        self.create_rc = create_rc
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
        self.calls.append(list(args))
        if args[:2] == ["repo", "view"]:
            return 0, REPO + "\n", ""
        if args[:1] == ["api"] and args[-1].endswith("ISSUE_TEMPLATE"):
            if self.templates is None:
                return 1, "", "gh: Not Found (HTTP 404)"
            listing = [{"name": p.name, "path": f".github/ISSUE_TEMPLATE/{p.name}", "type": "file"}
                       for p in sorted(self.templates.iterdir())]
            return 0, json.dumps(listing), ""
        if args[:1] == ["api"]:
            name = args[-1].rsplit("/", 1)[-1]
            return 0, (self.templates / name).read_text(), ""
        if args[:2] == ["issue", "create"]:
            if self.create_rc:
                return self.create_rc, "", "could not create"
            return 0, f"https://github.com/{REPO}/issues/7\n", ""
        raise AssertionError(f"unexpected gh call: {args}")

    def created(self) -> list[str] | None:
        return next((c for c in self.calls if c[:2] == ["issue", "create"]), None)


def run(argv: list[str], gh: FakeGh) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = cli.main(argv, gh=gh, out=out, err=err)
    return rc, out.getvalue(), err.getvalue()


NEW = [
    "new", "-R", REPO, "--template", "task", "--title", "backlog.py reads GitHub",
    "--field", "outcome=backlog.py counts GitHub issues",
    "--field", "why=The board shows unknown",
    "--field", "acceptance=- [ ] count matches",
]


class NewTest(unittest.TestCase):
    def test_creates_with_template_labels_and_rendered_body(self):
        gh = FakeGh()
        rc, out, err = run(NEW, gh)
        self.assertEqual(rc, 0, err)
        argv = gh.created()
        self.assertEqual(argv[argv.index("--title") + 1], "backlog.py reads GitHub")
        self.assertIn("### Outcome\n\nbacklog.py counts GitHub issues", argv[argv.index("--body") + 1])
        self.assertEqual(argv[argv.index("--label") + 1], "enhancement")
        self.assertIn("issues/7", out)

    def test_relationships_are_native_flags(self):
        gh = FakeGh()
        rc, _, err = run(NEW + ["--parent", "3", "--blocked-by", "4,5", "--blocking", "6", "--label", "agent"], gh)
        self.assertEqual(rc, 0, err)
        argv = gh.created()
        self.assertEqual(argv[argv.index("--parent") + 1], "3")
        self.assertEqual(argv[argv.index("--blocked-by") + 1], "4,5")
        self.assertEqual(argv[argv.index("--blocking") + 1], "6")
        labels = [argv[i + 1] for i, a in enumerate(argv) if a == "--label"]
        self.assertEqual(labels, ["enhancement", "agent"])

    def test_template_matched_by_name_case_insensitively(self):
        gh = FakeGh()
        argv = NEW.copy()
        argv[argv.index("task")] = "Task"
        self.assertEqual(run(argv, gh)[0], 0)

    def test_dry_run_writes_nothing(self):
        gh = FakeGh()
        rc, out, _ = run(NEW + ["--dry-run"], gh)
        self.assertEqual(rc, 0)
        self.assertIsNone(gh.created())
        self.assertIn("### Why\n\nThe board shows unknown", out)

    def test_violation_refuses_and_writes_nothing(self):
        gh = FakeGh()
        argv = NEW.copy()
        argv[argv.index("why=The board shows unknown")] = "why=Follows #2"
        rc, _, err = run(argv, gh)
        self.assertEqual(rc, 1)
        self.assertIsNone(gh.created())
        self.assertIn("#2", err)

    def test_missing_required_field(self):
        gh = FakeGh()
        rc, _, err = run(NEW[:-2], gh)
        self.assertEqual(rc, 1)
        self.assertIn("Acceptance is required", err)
        self.assertIsNone(gh.created())

    def test_unknown_field_is_a_usage_error(self):
        rc, _, err = run(NEW + ["--field", "context=long story"], FakeGh())
        self.assertEqual(rc, 2)
        self.assertIn("context", err)
        self.assertIn("outcome, why, acceptance, notes", err)

    def test_unknown_template(self):
        argv = NEW.copy()
        argv[argv.index("task")] = "epic"
        rc, _, err = run(argv, FakeGh())
        self.assertEqual(rc, 2)
        self.assertIn("Task", err)
        self.assertIn("Bug", err)

    def test_field_value_from_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("- [ ] one\n- [ ] two\n")
        gh = FakeGh()
        argv = NEW[:-1] + [f"acceptance=@{f.name}"]
        rc, _, err = run(argv, gh)
        self.assertEqual(rc, 0, err)
        body = gh.created()[gh.created().index("--body") + 1]
        self.assertIn("### Acceptance\n\n- [ ] one\n- [ ] two\n\n### Notes", body)

    def test_repo_defaults_to_the_current_one(self):
        gh = FakeGh()
        argv = [a for a in NEW if a not in ("-R", REPO)]
        self.assertEqual(run(argv, gh)[0], 0)
        self.assertIn(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], gh.calls)

    def test_repo_without_templates(self):
        rc, _, err = run(NEW, FakeGh(templates=None))
        self.assertEqual(rc, 2)
        self.assertIn("no issue templates", err)

    def test_create_failure_is_reported(self):
        rc, _, err = run(NEW, FakeGh(create_rc=1))
        self.assertEqual(rc, 1)
        self.assertIn("could not create", err)


class CheckTest(unittest.TestCase):
    def body_file(self, text: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(text)
        return f.name

    def test_clean_comment(self):
        rc, _, _ = run(["check", "-R", REPO, "--kind", "comment", "--body-file", self.body_file("Deployed.")],
                       FakeGh())
        self.assertEqual(rc, 0)

    def test_comment_with_reference(self):
        rc, _, err = run(["check", "-R", REPO, "--kind", "comment", "--body-file", self.body_file("see #3")],
                         FakeGh())
        self.assertEqual(rc, 1)
        self.assertIn("#3", err)

    def test_comment_does_not_fetch_templates(self):
        gh = FakeGh()
        run(["check", "-R", REPO, "--kind", "comment", "--body-file", self.body_file("ok")], gh)
        self.assertFalse(any(c[:1] == ["api"] for c in gh.calls))

    def test_create_body_must_be_a_template(self):
        rc, _, err = run(["check", "-R", REPO, "--kind", "create", "--title", "t",
                          "--body-file", self.body_file("Just some prose.")], FakeGh())
        self.assertEqual(rc, 1)
        self.assertIn("no template", err)

    def test_title_only_edit(self):
        rc, _, err = run(["check", "-R", REPO, "--kind", "edit", "--title", "Fix #4"], FakeGh())
        self.assertEqual(rc, 1)
        self.assertIn("#4", err)

    def test_template_fetch_failure_is_not_a_pass(self):
        rc, _, _ = run(["check", "-R", REPO, "--kind", "create", "--title", "t",
                        "--body-file", self.body_file("x")], FakeGh(templates=None))
        self.assertEqual(rc, 2)


class TemplatesTest(unittest.TestCase):
    def test_lists_fields_with_caps(self):
        rc, out, _ = run(["templates", "-R", REPO], FakeGh())
        self.assertEqual(rc, 0)
        self.assertIn("task (Task) labels: enhancement", out)
        self.assertIn("  outcome  input  required  1 line, 100 chars", out)
        self.assertIn("  evidence  textarea  optional  20 lines", out)
        self.assertNotIn("config", out)


if __name__ == "__main__":
    unittest.main()
