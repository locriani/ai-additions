"""`bug-hunt report` and `bug-hunt run` end to end, with a stub `claude` on PATH in place of a real session."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIN = HERE.parent / "bin" / "bug-hunt"
SEEDED = HERE / "fixtures" / "seeded"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def finding(**over):
    f = {
        "id": "BH-1", "title": "bulk discount skips exactly ten items", "severity": "high", "class": "boundary",
        "path": "pricing.py", "line": 7, "expected": "10% off at qty 10", "actual": "full price at qty 10",
        "intent_evidence": "docstring: '10% off for 10 or more items'", "root_cause": "`>` where `>=` is meant",
        "repro": {"path": "test_bh_1.py", "command": "python3 -m unittest test_bh_1",
                  "content": "assert bulk_discount(10) == 0.9\n", "failure_excerpt": "AssertionError: 1.0 != 0.9"},
    }
    f.update(over)
    return f


def report_doc(**over):
    d = {
        "version": 1, "repo": "seeded", "commit": "0123456789abcdef", "status": "complete", "incomplete_reasons": [],
        "scope": {"paths": [], "since": None, "files_hunted": ["pricing.py"], "files_skipped": []},
        "test_command": "python3 -m unittest", "baseline": {"command": "python3 -m unittest", "exit": 0, "passed": True},
        "candidates": 3, "refuted": 2, "findings": [],
    }
    d.update(over)
    return d


STUB = r'''#!{python}
"""Stands in for `claude -p`: logs what it was given, then acts out BH_STUB."""
import json, os, shlex, subprocess, sys
from pathlib import Path
argv = sys.argv[1:]
prompt = shlex.split(argv[argv.index("-p") + 1])
opt = lambda k: prompt[prompt.index(k) + 1]
wt, out = Path(opt("--worktree")), Path(opt("--out"))
Path(os.environ["BH_STUB_LOG"]).write_text(json.dumps({
    "argv": argv, "prompt": prompt, "wt_exists": wt.is_dir(),
    "wt_head": subprocess.run(["git", "-C", str(wt), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    "ceiling": os.environ.get("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS")}))
print(json.dumps({"type": "result", "total_cost_usd": 0.01}))
mode = os.environ["BH_STUB"]
docs = json.loads(os.environ["BH_STUB_DOCS"])
if mode == "crash":
    sys.exit(1)
if mode == "dirty":
    Path(os.environ["BH_STUB_REPO"], "pricing.py").write_text("tampered\n")
out.mkdir(parents=True, exist_ok=True)
(out / "findings.json").write_text(json.dumps(docs[mode]))
sys.exit(2 if mode == "budget" else 0)
'''


class Report(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.json = Path(self.tmp.name, "findings.json")
        self.md = Path(self.tmp.name, "findings.md")

    def tearDown(self):
        self.tmp.cleanup()

    def report(self, doc):
        self.json.write_text(doc if isinstance(doc, str) else json.dumps(doc))
        return subprocess.run([sys.executable, str(BIN), "report", str(self.json)], capture_output=True, text=True)

    def test_clean_run_exits_0(self):
        p = self.report(report_doc())
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("No bugs proven", self.md.read_text())
        self.assertIn(str(self.md), p.stdout)

    def test_findings_exit_1_and_render(self):
        p = self.report(report_doc(findings=[finding()]))
        self.assertEqual(p.returncode, 1, p.stderr)
        md = self.md.read_text()
        for text in ("bulk discount skips exactly ten items", "pricing.py:7", "high", "python3 -m unittest test_bh_1",
                     "assert bulk_discount(10) == 0.9", "AssertionError: 1.0 != 0.9", "docstring: '10% off"):
            self.assertIn(text, md)

    def test_findings_sorted_by_severity(self):
        doc = report_doc(findings=[finding(id="BH-1", title="low one", severity="low"),
                                   finding(id="BH-2", title="critical one", severity="critical")])
        self.report(doc)
        md = self.md.read_text()
        self.assertLess(md.index("critical one"), md.index("low one"))

    def test_incomplete_without_findings_exits_2(self):
        p = self.report(report_doc(status="incomplete", incomplete_reasons=["baseline suite would not run"]))
        self.assertEqual(p.returncode, 2)
        self.assertIn("baseline suite would not run", self.md.read_text())

    def test_incomplete_with_findings_still_exits_1(self):
        p = self.report(report_doc(status="incomplete", incomplete_reasons=["budget cap"], findings=[finding()]))
        self.assertEqual(p.returncode, 1)

    def test_incomplete_needs_a_reason(self):
        p = self.report(report_doc(status="incomplete"))
        self.assertEqual(p.returncode, 2)
        self.assertIn("incomplete_reasons", p.stderr)
        self.assertFalse(self.md.exists())

    def test_missing_key_is_invalid(self):
        doc = report_doc()
        del doc["commit"]
        p = self.report(doc)
        self.assertEqual(p.returncode, 2)
        self.assertIn("commit", p.stderr)
        self.assertFalse(self.md.exists())

    def test_bad_severity_is_invalid(self):
        p = self.report(report_doc(findings=[finding(severity="urgent")]))
        self.assertEqual(p.returncode, 2)
        self.assertIn("severity", p.stderr)

    def test_finding_without_repro_is_invalid(self):
        f = finding()
        f["repro"] = {"path": "x", "command": "x", "content": "", "failure_excerpt": "x"}
        p = self.report(report_doc(findings=[f]))
        self.assertEqual(p.returncode, 2)
        self.assertIn("repro.content", p.stderr)

    def test_bad_line_is_invalid(self):
        p = self.report(report_doc(findings=[finding(line=0)]))
        self.assertEqual(p.returncode, 2)
        self.assertIn("line", p.stderr)

    def test_not_json_is_invalid(self):
        p = self.report("{nope")
        self.assertEqual(p.returncode, 2)

    def test_missing_file_is_invalid(self):
        p = subprocess.run([sys.executable, str(BIN), "report", str(self.json)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_fence_survives_backticks_in_repro(self):
        f = finding()
        f["repro"]["content"] = "doc = '''\n```\n'''\n"
        self.report(report_doc(findings=[f]))
        self.assertIn("````", self.md.read_text())


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.repo = root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "pricing.py").write_text("X = 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
        self.head = git(self.repo, "rev-parse", "HEAD").strip()
        self.out = root / "out"
        self.log = root / "stub.json"
        stubs = root / "bin"
        stubs.mkdir()
        stub = stubs / "claude"
        stub.write_text(STUB.replace("{python}", sys.executable))
        stub.chmod(0o755)
        self.env = {**os.environ, "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}", "BH_STUB_LOG": str(self.log),
                    "BH_STUB_REPO": str(self.repo), "TMPDIR": str(root / "tmp"),
                    "BH_STUB_DOCS": json.dumps({
                        "clean": report_doc(), "dirty": report_doc(), "bugs": report_doc(findings=[finding()]),
                        "budget": report_doc(status="incomplete", incomplete_reasons=["in progress"],
                                             findings=[finding()])})}
        (root / "tmp").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, mode, *extra, out=True):
        argv = [sys.executable, str(BIN), "run", "--repo", str(self.repo), *(["--out", str(self.out)] if out else []), *extra]
        return subprocess.run(argv, capture_output=True, text=True, env={**self.env, "BH_STUB": mode})

    def logged(self):
        return json.loads(self.log.read_text())

    def assert_no_worktree_left(self):
        self.assertEqual(git(self.repo, "worktree", "list", "--porcelain").count("worktree "), 1,
                         git(self.repo, "worktree", "list"))
        self.assertFalse(Path(self.logged()["prompt"][self.logged()["prompt"].index("--worktree") + 1]).exists())

    def test_invocation(self):
        p = self.run_cli("bugs", "--path", "src", "--path", "lib", "--since", "main", "--budget", "3")
        self.assertEqual(p.returncode, 1, p.stderr)
        log = self.logged()
        argv, prompt = log["argv"], log["prompt"]
        self.assertEqual(prompt[0], "/bug-hunt:bug-hunt")
        self.assertEqual(prompt[prompt.index("--out") + 1], str(self.out))
        self.assertEqual([prompt[i + 1] for i, a in enumerate(prompt) if a == "--path"], ["src", "lib"])
        self.assertEqual(prompt[prompt.index("--since") + 1], "main")
        wt = prompt[prompt.index("--worktree") + 1]
        for flag, value in (("--permission-mode", "dontAsk"), ("--permission-prompts", "none"),
                            ("--max-budget-usd", "3.0"), ("--output-format", "json")):
            self.assertEqual(argv[argv.index(flag) + 1], value, flag)
        allowed = argv[argv.index("--allowedTools") + 1].split(",")
        for tool in ("Read", "Grep", "Glob", "Agent", "Bash", f"Edit(/{wt}/**)", f"Edit(/{self.out}/**)"):
            self.assertIn(tool, allowed)
        self.assertIn("Bash(git push *)", argv[argv.index("--disallowedTools") + 1].split(","))
        self.assertTrue(log["wt_exists"])
        self.assertEqual(log["wt_head"], self.head)
        self.assertTrue(log["ceiling"])
        self.assertFalse(Path(wt).is_relative_to(self.repo))
        self.assertTrue((self.out / "findings.md").exists())
        self.assert_no_worktree_left()

    def test_clean_run_exits_0_and_leaves_checkout_alone(self):
        before = git(self.repo, "status", "--porcelain")
        p = self.run_cli("clean")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)
        self.assert_no_worktree_left()

    def test_out_inside_the_checkout_is_not_a_change(self):
        self.out = self.repo / "bug-hunt-report"
        p = self.run_cli("clean")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue((self.out / "session.json").exists())

    def test_crash_writes_incomplete_report(self):
        p = self.run_cli("crash")
        self.assertEqual(p.returncode, 2)
        doc = json.loads((self.out / "findings.json").read_text())
        self.assertEqual(doc["status"], "incomplete")
        self.assertTrue(any("exited 1" in r for r in doc["incomplete_reasons"]))
        self.assertEqual(doc["commit"], self.head)
        self.assertTrue((self.out / "findings.md").exists())
        self.assert_no_worktree_left()

    def test_budget_cap_keeps_findings(self):
        p = self.run_cli("budget")
        self.assertEqual(p.returncode, 1)
        doc = json.loads((self.out / "findings.json").read_text())
        self.assertEqual(len(doc["findings"]), 1)
        self.assertTrue(any("exited 2" in r for r in doc["incomplete_reasons"]))

    def test_touched_checkout_is_reported(self):
        p = self.run_cli("dirty")
        self.assertEqual(p.returncode, 2)
        doc = json.loads((self.out / "findings.json").read_text())
        self.assertTrue(any("checkout changed" in r for r in doc["incomplete_reasons"]))

    def test_default_out_is_outside_the_repo(self):
        p = self.run_cli("clean", out=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = Path(self.logged()["prompt"][self.logged()["prompt"].index("--out") + 1])
        self.assertFalse(out.is_relative_to(self.repo))
        self.assertTrue((out / "findings.md").exists())
        self.assertIn(str(out), p.stdout)

    def test_not_a_repo_refuses(self):
        p = subprocess.run([sys.executable, str(BIN), "run", "--repo", self.tmp.name],
                           capture_output=True, text=True, env={**self.env, "BH_STUB": "clean"})
        self.assertEqual(p.returncode, 2)
        self.assertFalse(self.log.exists())


class Fixture(unittest.TestCase):
    """The seeded repo stays honest: its own suite passes, and the planted bug is still there."""

    def test_suite_passes_and_bug_is_planted(self):
        p = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=SEEDED, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        probe = "import pricing; print(pricing.bulk_discount(10, 100.0))"
        self.assertEqual(subprocess.run([sys.executable, "-c", probe], cwd=SEEDED, capture_output=True,
                                        text=True).stdout.strip(), "1000.0")


if __name__ == "__main__":
    unittest.main()
