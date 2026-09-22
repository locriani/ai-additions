"""Which `gh api` endpoints a `gh` subcommand already covers, and which `gh api` calls write issue text."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))

import gh_api_coverage as cov  # noqa: E402


def call(command: str) -> cov.ApiCall:
    [one] = cov.api_calls(command)
    return one


class CoveredTest(unittest.TestCase):
    def test_covered_endpoints_name_their_subcommand(self):
        for endpoint, sub in (
            ("repos/o/r/issues", "gh issue"),
            ("repos/o/r/issues/3/comments", "gh issue"),
            ("repos/o/r/issues/3/sub_issues", "gh issue"),
            ("repos/o/r/issues/3/dependencies/blocked_by", "gh issue"),
            ("repos/{owner}/{repo}/issues", "gh issue"),
            ("/repos/o/r/pulls/9/files", "gh pr"),
            ("repos/o/r/actions/runs/1", "gh run"),
            ("repos/o/r/actions/workflows", "gh workflow"),
            ("repos/o/r/actions/secrets", "gh secret"),
            ("repos/o/r/actions/variables/X", "gh variable"),
            ("repos/o/r/releases/latest", "gh release"),
            ("repos/o/r/labels", "gh label"),
            ("repos/o/r/forks", "gh repo fork"),
            ("repos/o/r", "gh repo view"),
            ("search/issues?q=x", "gh search"),
            ("search/repositories", "gh search"),
            ("gists/abc", "gh gist"),
            ("https://api.github.com/repos/o/r/issues", "gh issue"),
        ):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(cov.covered(endpoint), sub)

    def test_uncovered_endpoints_are_allowed(self):
        for endpoint in (
            "graphql",
            "repos/o/r/contents/.github/ISSUE_TEMPLATE",
            "repos/o/r/milestones",
            "repos/o/r/rulesets",
            "repos/o/r/traffic/views",
            "repos/o/r/code-scanning/alerts",
            "user",
            "orgs/o/projects",
            "search/users",
        ):
            with self.subTest(endpoint=endpoint):
                self.assertIsNone(cov.covered(endpoint))


class ParseTest(unittest.TestCase):
    def test_endpoint_is_first_positional(self):
        self.assertEqual(call("gh api -H 'Accept: application/vnd.github.raw' repos/o/r/contents/x").endpoint,
                         "repos/o/r/contents/x")

    def test_method_inference(self):
        self.assertEqual(call("gh api repos/o/r/issues").method, "GET")
        self.assertEqual(call("gh api repos/o/r/issues -f title=x").method, "POST")
        self.assertEqual(call("gh api repos/o/r/issues --input body.json").method, "POST")
        self.assertEqual(call("gh api -X GET search/issues -f q=x").method, "GET")
        self.assertEqual(call("gh api --method=PATCH repos/o/r/issues/3 -f body=x").method, "PATCH")

    def test_fields_and_graphql_query(self):
        c = call("gh api graphql -f query='mutation { addComment(input: {}) { clientMutationId } }' -F n=1")
        self.assertIn("addComment", c.query)
        self.assertEqual(c.fields, {"query": "mutation { addComment(input: {}) { clientMutationId } }", "n": "1"})

    def test_segments_and_non_api_commands(self):
        self.assertEqual([c.endpoint for c in cov.api_calls("cd x && gh api user; gh api repos/o/r | jq .")],
                         ["user", "repos/o/r"])
        self.assertEqual(cov.api_calls("gh issue list; echo 'gh api repos/o/r/issues'"), [])

    def test_unparseable_raises(self):
        with self.assertRaises(ValueError):
            cov.api_calls("gh api repos/o/r/issues -f body='unbalanced")


class IssueTextWriteTest(unittest.TestCase):
    def test_writes_of_issue_text(self):
        for command in (
            "gh api repos/o/r/issues -f title=x -f body=y",
            "gh api -X PATCH repos/o/r/issues/3 -f body=y",
            "gh api repos/o/r/issues/3/comments -f body=x",
            "gh api -X PATCH repos/o/r/issues/comments/99 -f body=x",
            "gh api graphql -f query='mutation { createIssue(input: {}) { issue { number } } }'",
            "gh api graphql -f query='mutation { updateIssueComment(input: {}) { clientMutationId } }'",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(cov.issue_text_write(call(command)))

    def test_not_issue_text(self):
        for command in (
            "gh api repos/o/r/issues",
            "gh api repos/o/r/issues/3/comments",
            "gh api repos/o/r/issues/3/sub_issues -F sub_issue_id=1",
            "gh api -X PATCH repos/o/r/issues/3 -f state=closed",
            "gh api graphql -f query='{ repository(owner:\"o\", name:\"r\") { issues(first:1) { totalCount } } }'",
            "gh api repos/o/r/contents/x",
        ):
            with self.subTest(command=command):
                self.assertIsNone(cov.issue_text_write(call(command)))


if __name__ == "__main__":
    unittest.main()
