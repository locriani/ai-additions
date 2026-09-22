"""The Stop hook blocks `gh api` only where a `gh` subcommand covers the endpoint."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "github-api-stop-hook.py"
_loader = importlib.machinery.SourceFileLoader("github_api_stop_hook", str(HOOK))
_spec = importlib.util.spec_from_loader("github_api_stop_hook", _loader)
hook = importlib.util.module_from_spec(_spec)
_loader.exec_module(hook)


def bash(command: str) -> dict:
    return {"type": "tool_use", "name": "Bash", "input": {"command": command}}


class FindViolationsTest(unittest.TestCase):
    def test_uncovered_gh_api_is_allowed(self):
        for command in (
            "gh api repos/o/r/contents/.github/ISSUE_TEMPLATE",
            "gh api graphql -f query='{ viewer { login } }'",
            "gh api repos/o/r/rulesets",
            "gh api user",
        ):
            with self.subTest(command=command):
                self.assertEqual(hook.find_violations([bash(command)]), [])

    def test_covered_gh_api_is_a_violation_naming_the_subcommand(self):
        [v] = hook.find_violations([bash("gh api repos/o/r/issues --paginate")])
        self.assertIn("gh issue", v["kind"])
        self.assertIn("repos/o/r/issues", v["kind"])

    def test_one_violation_per_covered_call(self):
        got = hook.find_violations([bash("gh api repos/o/r/pulls && gh api user && gh api repos/o/r/releases")])
        self.assertEqual([("gh pr" in v["kind"], "gh release" in v["kind"]) for v in got],
                         [(True, False), (False, True)])

    def test_unparseable_gh_api_stays_a_violation(self):
        got = hook.find_violations([bash("gh api repos/o/r/contents -f x='unbalanced")])
        self.assertEqual(len(got), 1)

    def test_raw_http_and_webfetch_are_unchanged(self):
        self.assertEqual(len(hook.find_violations([bash("curl -s https://api.github.com/repos/o/r")])), 1)
        fetch = {"type": "tool_use", "name": "WebFetch", "input": {"url": "https://github.com/o/r/issues"}}
        self.assertEqual(len(hook.find_violations([fetch])), 1)

    def test_gh_issue_commands_are_not_api_calls(self):
        self.assertEqual(hook.find_violations([bash("gh issue list -R o/r; gh-issue templates -R o/r")]), [])


if __name__ == "__main__":
    unittest.main()
