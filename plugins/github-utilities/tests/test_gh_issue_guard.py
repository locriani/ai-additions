"""The PreToolUse guard: a raw `gh issue` write goes through `gh-issue check`, or it does not run."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = HERE.parent / "hooks" / "gh-issue-guard.py"

_loader = importlib.machinery.SourceFileLoader("gh_issue_guard", str(HOOK))
_spec = importlib.util.spec_from_loader("gh_issue_guard", _loader)
guard = importlib.util.module_from_spec(_spec)
_loader.exec_module(guard)

CWD = "/tmp/somewhere"


class FakeCheck:
    def __init__(self, rc: int = 0, stderr: str = "", raises: Exception | None = None):
        self.rc, self.stderr, self.raises = rc, stderr, raises
        self.calls: list[dict] = []

    def __call__(self, kind, repo, title, body_path, cwd):
        text = None
        if body_path and os.path.isabs(body_path) and os.path.exists(body_path):
            text = Path(body_path).read_text()
        self.calls.append(dict(kind=kind, repo=repo, title=title, body_path=body_path, body=text, cwd=cwd))
        if self.raises:
            raise self.raises
        return self.rc, self.stderr


def decide(command: str, check: FakeCheck | None = None) -> str | None:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": CWD}
    return guard.decide(payload, check=check if check is not None else FakeCheck())


class PassThroughTest(unittest.TestCase):
    def test_commands_that_write_no_issue_text(self):
        for command in (
            "ls -la",
            "gh issue list -R o/n",
            "gh issue view 3",
            "gh pr create --title x --body 'see #3'",
            "gh-issue new --template task --title T --field why=x",
            'echo "gh issue create --body see #3"',
            "gh issue edit 4 --add-blocked-by 3",
            "gh issue edit 4 --add-sub-issue 5 --add-label bug",
            "gh issue close 4",
            "gh issue close 4 --reason 'not planned'",
            "gh issue reopen 4",
        ):
            with self.subTest(command=command):
                check = FakeCheck()
                self.assertIsNone(decide(command, check))
                self.assertEqual(check.calls, [])

    def test_non_bash_tool(self):
        payload = {"tool_name": "Read", "tool_input": {"file_path": "x"}, "cwd": CWD}
        self.assertIsNone(guard.decide(payload, check=FakeCheck()))


class CheckedTest(unittest.TestCase):
    def test_create_is_checked_and_allowed(self):
        check = FakeCheck()
        self.assertIsNone(decide("gh issue create -R o/n --title T --body '### Outcome\n\nx'", check))
        [call] = check.calls
        self.assertEqual((call["kind"], call["repo"], call["title"], call["body"], call["cwd"]),
                         ("create", "o/n", "T", "### Outcome\n\nx", CWD))

    def test_equals_forms(self):
        check = FakeCheck()
        self.assertIsNone(decide("gh issue create --repo=o/n --title=T --body='B'", check))
        [call] = check.calls
        self.assertEqual((call["repo"], call["title"], call["body"]), ("o/n", "T", "B"))

    def test_short_flags(self):
        check = FakeCheck()
        decide("gh issue create -t T -b B", check)
        [call] = check.calls
        self.assertEqual((call["title"], call["body"], call["repo"]), ("T", "B", None))

    def test_refusal_is_the_reason(self):
        reason = decide("gh issue comment 4 --body 'see #3'", FakeCheck(rc=1, stderr="refused: \"#3\" cites an issue"))
        self.assertIn('"#3" cites an issue', reason)

    def test_could_not_verify(self):
        reason = decide("gh issue create --title T --body B", FakeCheck(rc=2, stderr="gh-issue: no templates"))
        self.assertIn("could not verify", reason)
        self.assertIn("no templates", reason)

    def test_check_that_raises_is_a_deny(self):
        reason = decide("gh issue comment 4 --body ok", FakeCheck(raises=FileNotFoundError("uv")))
        self.assertIn("could not verify", reason)

    def test_kinds(self):
        for command, kind, title, body in (
            ("gh issue comment 4 --body 'see #3'", "comment", None, "see #3"),
            ("gh issue comment 4 -b ok", "comment", None, "ok"),
            ("gh issue close 4 --comment done", "comment", None, "done"),
            ("gh issue close 4 -c done --reason completed", "comment", None, "done"),
            ("gh issue reopen 4 --comment again", "comment", None, "again"),
            ("gh issue edit 4 --title X", "edit", "X", None),
            ("gh issue edit 4 --body B --add-label bug", "edit", None, "B"),
        ):
            with self.subTest(command=command):
                check = FakeCheck()
                self.assertIsNone(decide(command, check))
                [call] = check.calls
                self.assertEqual((call["kind"], call["title"], call["body"]), (kind, title, body))

    def test_body_file_is_passed_through(self):
        check = FakeCheck()
        self.assertIsNone(decide("gh issue comment 4 --body-file notes.md", check))
        [call] = check.calls
        self.assertEqual((call["body_path"], call["cwd"]), ("notes.md", CWD))

    def test_short_body_file(self):
        check = FakeCheck()
        decide("gh issue comment 4 -F notes.md", check)
        self.assertEqual(check.calls[0]["body_path"], "notes.md")

    def test_compound_command_checks_the_issue_segment(self):
        check = FakeCheck()
        self.assertIsNone(decide("cd x && gh issue comment 1 --body ok; echo done", check))
        self.assertEqual(len(check.calls), 1)
        self.assertEqual(check.calls[0]["body"], "ok")

    def test_env_assignment_prefix(self):
        check = FakeCheck()
        decide("GH_REPO=o/n gh issue comment 1 --body ok", check)
        self.assertEqual(len(check.calls), 1)

    def test_every_segment_is_checked(self):
        check = FakeCheck()
        decide("gh issue comment 1 --body a && gh issue comment 2 --body b", check)
        self.assertEqual([c["body"] for c in check.calls], ["a", "b"])


class UnreadableTest(unittest.TestCase):
    def test_denied_without_a_check(self):
        for command in (
            "gh issue comment 4 --body-file -",
            'gh issue comment 4 --body "$(cat notes.md)"',
            "gh issue comment 4 --body \"`cat notes.md`\"",
            'gh issue comment 4 --body "$BODY"',
            'gh issue comment 4 --body "${BODY}"',
            "gh issue comment 4 --body 'unbalanced",
        ):
            with self.subTest(command=command):
                check = FakeCheck()
                reason = decide(command, check)
                self.assertIsNotNone(reason)
                self.assertIn("--body-file", reason)
                self.assertEqual(check.calls, [])

    def test_create_without_a_body(self):
        reason = decide("gh issue create --title T")
        self.assertIn("gh-issue new", reason)

    def test_interactive_create(self):
        for flag in ("--web", "--editor", "--template bug.yml", "--recover x.json"):
            with self.subTest(flag=flag):
                self.assertIn("gh-issue new", decide(f"gh issue create --title T --body B {flag}"))

    def test_interactive_comment(self):
        for command in ("gh issue comment 4", "gh issue comment 4 --web", "gh issue comment 4 --edit-last"):
            with self.subTest(command=command):
                self.assertIsNotNone(decide(command))

    def test_dollar_amount_is_not_a_variable(self):
        check = FakeCheck()
        self.assertIsNone(decide("gh issue comment 4 --body 'costs $5 a month'", check))
        self.assertEqual(len(check.calls), 1)


class GhApiTest(unittest.TestCase):
    """`gh api` is allowed where no subcommand exists, so it must not become the way around the rules."""

    def test_issue_text_writes_are_denied(self):
        for command in (
            "gh api repos/o/r/issues -f title=x -f body=y",
            "gh api repos/o/r/issues/3/comments -f body=x",
            "gh api graphql -f query='mutation { addComment(input: {}) { clientMutationId } }'",
            "cd x && gh api -X PATCH repos/o/r/issues/3 -f body=y",
        ):
            with self.subTest(command=command):
                check = FakeCheck()
                reason = decide(command, check)
                self.assertIsNotNone(reason)
                self.assertIn("gh-issue new", reason)
                self.assertEqual(check.calls, [])

    def test_other_gh_api_passes_the_guard(self):
        for command in ("gh api repos/o/r/contents/.github", "gh api repos/o/r/issues",
                        "gh api repos/o/r/issues/3/sub_issues -F sub_issue_id=1"):
            with self.subTest(command=command):
                check = FakeCheck()
                self.assertIsNone(decide(command, check))
                self.assertEqual(check.calls, [])

    def test_unparseable_gh_api_is_denied(self):
        self.assertIsNotNone(decide("gh api repos/o/r/issues -f body='unbalanced"))


class EndToEndTest(unittest.TestCase):
    """The real hook, the real `gh-issue check`. `--kind comment` needs no network."""

    def run_hook(self, command: str) -> subprocess.CompletedProcess:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(HERE),
                   "hook_event_name": "PreToolUse"}
        return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                              text=True, timeout=120)

    def test_reference_is_denied(self):
        p = self.run_hook("gh issue comment 1 -R o/n --body 'see #3'")
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("#3", out["permissionDecisionReason"])

    def test_clean_comment_is_allowed(self):
        p = self.run_hook("gh issue comment 1 -R o/n --body 'Deployed.'")
        self.assertEqual((p.returncode, p.stdout), (0, ""), p.stderr)

    def test_unreadable_payload_is_allowed(self):
        p = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual((p.returncode, p.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
