#!/usr/bin/env python3
"""Tests for bug-tally.py — run with: /usr/bin/python3 test_bug_tally.py

No venv, no third-party deps (project rule: system python3 + stdlib only).
"""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("bug_tally", HERE / "bug-tally.py")
bug_tally = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bug_tally)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    )


class GetCommitsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("a\n")
        _git(self.repo, "add", "a.txt")
        _git(self.repo, "commit", "-q", "-m", "feat: initial")
        (self.repo / "a.txt").write_text("b\n")
        _git(self.repo, "add", "a.txt")
        # Body deliberately contains the bare sentinel word "COMMIT" and a
        # multi-line body to prove the field split is correct and robust.
        _git(
            self.repo, "commit", "-q",
            "-m", "fix: null crash in parser",
            "-m", "Mentions the word COMMIT in prose.\nSecond paragraph here.",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parses_real_repo_without_embedded_null_byte_crash(self) -> None:
        # Pre-fix this raises ValueError: embedded null byte because the
        # \x00 separator is injected into the git argv element.
        commits = bug_tally.get_commits(str(self.repo), None)

        self.assertEqual(len(commits), 2)
        # git log is reverse-chronological: newest (the fix) first.
        self.assertEqual(commits[0]["subject"], "fix: null crash in parser")
        self.assertIn("Mentions the word COMMIT in prose.", commits[0]["body"])
        self.assertIn("Second paragraph here.", commits[0]["body"])
        self.assertEqual(commits[1]["subject"], "feat: initial")
        # SHA is a 40-char hex string, not contaminated by the separator.
        self.assertRegex(commits[0]["sha"], r"^[0-9a-f]{40}$")


class EndBodyTokenInCommitBodyTest(unittest.TestCase):
    """A commit body that literally contains the record-terminator token
    must not split the record stream mid-commit (truncating or dropping it).
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("a\n")
        _git(self.repo, "add", "a.txt")
        _git(self.repo, "commit", "-q", "-m", "feat: initial")
        (self.repo / "a.txt").write_text("b\n")
        _git(self.repo, "add", "a.txt")
        # Body deliberately embeds the bare record-terminator token END_BODY
        # *inline* (not at the end), plus trailing prose, to prove the record
        # split survives a literal occurrence anywhere in the body.
        _git(
            self.repo, "commit", "-q",
            "-m", "fix: record terminator robustness",
            "-m", "Trailing note: END_BODY appears here inline.\nSecond line.",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_literal_END_BODY_in_body_does_not_corrupt_records(self) -> None:
        commits = bug_tally.get_commits(str(self.repo), None)

        self.assertEqual(len(commits), 2)
        # git log is reverse-chronological: the fix commit is newest.
        self.assertEqual(commits[0]["subject"], "fix: record terminator robustness")
        # The literal token and everything after it must survive intact —
        # pre-fix, raw.split("END_BODY") truncates the body at "Trailing note:".
        self.assertIn("END_BODY appears here inline.", commits[0]["body"])
        self.assertIn("Second line.", commits[0]["body"])
        self.assertEqual(commits[1]["subject"], "feat: initial")
        self.assertRegex(commits[0]["sha"], r"^[0-9a-f]{40}$")
        self.assertRegex(commits[1]["sha"], r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
