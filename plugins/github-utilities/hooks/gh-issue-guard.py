#!/usr/bin/env python3
"""
PreToolUse guard for raw `gh issue` writes, per `rules/GITHUB.md`.

A Bash command that writes issue text — `gh issue create`, `comment`, `edit --title/--body`, or
`close`/`reopen --comment` — runs only if `bin/gh-issue check` passes that text: no issue cited in
prose, and a body that is a filled template. Anything the hook cannot read (stdin, `$(...)`, `$VAR`,
a heredoc, an interactive flag) is denied with the way to make it readable.

Fails closed: once a command is an issue write, a check that could not run is a deny, never a pass.
A payload that cannot be read at all is let through and logged — the hook cannot tell whether it
holds an issue write, and blocking every Bash call is not the rule.

Standard library only: the fast path is one regex per Bash call. PyYAML is `gh-issue`'s concern.

Hook contract: https://docs.claude.com/en/docs/claude-code/hooks
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GH_ISSUE = ROOT / "bin" / "gh-issue"
LOG_PATH = Path.home() / ".claude" / "hooks" / "gh-issue-guard.log"
TIMEOUT = 30

FAST = re.compile(r"\bgh\s+issue\s+(?:create|edit|comment|close|reopen)\b")
ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
EXPANDS = re.compile(r"`|\$(?:[A-Za-z_{(]|$)")
OPERATORS = set("();<>|&\n")

VALUE_FLAGS = {
    "-t": "title", "--title": "title",
    "-b": "body", "--body": "body",
    "-F": "body_file", "--body-file": "body_file",
    "-R": "repo", "--repo": "repo",
    "-c": "comment", "--comment": "comment",
}
INTERACTIVE = {"-w": "--web", "--web": "--web", "-e": "--editor", "--editor": "--editor",
               "-T": "--template", "--template": "--template", "--recover": "--recover",
               "--edit-last": "--edit-last"}
TAKES_VALUE = {"-T", "--template", "--recover"}

FILE_WITH = "file with gh-issue new --template KEY (gh-issue templates lists them)"


def unreadable(why: str) -> str:
    return (f"gh-issue-guard: cannot read this issue text ({why}). Write it to a file and pass "
            f"--body-file PATH, or {FILE_WITH}.")


def log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def segments(command: str) -> list[list[str]]:
    """Simple commands, split at shell operators and newlines. Raises ValueError when unparseable."""
    lex = shlex.shlex(command, posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    out, current = [], []
    for token in lex:
        if token and set(token) <= OPERATORS:
            if "<<" in token:
                current.append("<<")  # a heredoc: the text arrives on stdin
            out.append(current)
            current = []
        else:
            current.append(token)
    out.append(current)
    return [s for s in out if s]


def issue_write(words: list[str]) -> tuple[str, dict, list[str], bool] | None:
    """(verb, flag values, interactive flags, heredoc) for a `gh issue <write verb>` command."""
    while words and ASSIGNMENT.match(words[0]):
        words = words[1:]
    if len(words) < 3 or words[:2] != ["gh", "issue"] or words[2] not in ("create", "edit", "comment",
                                                                          "close", "reopen"):
        return None
    values, interactive, heredoc = {}, [], False
    args, i = words[3:], 0
    while i < len(args):
        arg = args[i]
        flag, eq, inline = arg.partition("=") if arg.startswith("--") else (arg, "", "")
        if arg == "<<":
            heredoc = True
        elif flag in VALUE_FLAGS and not (flag == "-c" and words[2] not in ("close", "reopen")):
            if eq:
                values[VALUE_FLAGS[flag]] = inline
            elif i + 1 < len(args):
                values[VALUE_FLAGS[flag]] = args[i + 1]
                i += 1
            else:
                values[VALUE_FLAGS[flag]] = ""
        elif flag in INTERACTIVE:
            interactive.append(INTERACTIVE[flag])
            if flag in TAKES_VALUE and not eq:
                i += 1
        i += 1
    return words[2], values, interactive, heredoc


def run_check(kind: str, repo: str | None, title: str | None, body_path: str | None, cwd: str | None):
    argv = [str(GH_ISSUE), "check", "--kind", kind]
    if repo:
        argv += ["-R", repo]
    if title is not None:
        argv += ["--title", title]
    if body_path is not None:
        argv += ["--body-file", body_path]
    p = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT,
                       cwd=cwd if cwd and os.path.isdir(cwd) else None)
    return p.returncode, p.stderr


def _verdict(kind, repo, title, body, body_file, cwd, check) -> str | None:
    for name, value in (("title", title), ("body", body)):
        if value is not None and EXPANDS.search(value):
            return unreadable(f"the {name} is expanded by the shell")
    if body_file == "-":
        return unreadable("--body-file - reads stdin")
    if body_file is not None and EXPANDS.search(body_file):
        return unreadable("the --body-file path is expanded by the shell")
    temp = None
    try:
        if body is not None:
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
                f.write(body)
            temp = body_file = f.name
        try:
            rc, stderr = check(kind, repo, title, body_file, cwd)
        except Exception as e:  # noqa: BLE001 — a check that could not run is never a pass
            return f"gh-issue-guard: could not verify: {type(e).__name__}: {e}"
    finally:
        if temp:
            try:
                os.unlink(temp)
            except OSError:
                pass
    if rc == 0:
        return None
    if rc == 1:
        return f"gh-issue-guard: refused by gh-issue check.\n{stderr.strip()}"
    return f"gh-issue-guard: could not verify: {stderr.strip() or f'gh-issue check exited {rc}'}"


def decide_segment(words: list[str], cwd: str | None, check) -> str | None:
    parsed = issue_write(words)
    if parsed is None:
        return None
    verb, v, interactive, heredoc = parsed
    if heredoc:
        return unreadable("a heredoc feeds stdin")
    body, body_file = v.get("body"), v.get("body_file")
    has_body = body is not None or body_file is not None
    if verb == "create":
        if interactive:
            return f"gh-issue-guard: {interactive[0]} cannot be checked; {FILE_WITH}."
        if not has_body:
            return f"gh-issue-guard: gh issue create needs a body the hook can check; {FILE_WITH}."
        return _verdict("create", v.get("repo"), v.get("title", ""), body, body_file, cwd, check)
    if verb == "comment":
        if not has_body:
            return ("gh-issue-guard: a comment needs --body or --body-file"
                    f"{' (not ' + interactive[0] + ')' if interactive else ''}, so it can be checked.")
        return _verdict("comment", v.get("repo"), None, body, body_file, cwd, check)
    if verb == "edit":
        if not has_body and "title" not in v:
            return None  # relationships, labels, assignees: nothing to read
        return _verdict("edit", v.get("repo"), v.get("title"), body, body_file, cwd, check)
    if "comment" not in v:  # close / reopen
        return None
    return _verdict("comment", v.get("repo"), None, v["comment"], None, cwd, check)


def decide(payload: dict, check=run_check) -> str | None:
    """The deny reason for this tool call, or None to let it run."""
    if payload.get("tool_name") != "Bash":
        return None
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not FAST.search(command):
        return None
    try:
        parts = segments(command)
    except ValueError as e:
        return unreadable(f"the command does not parse: {e}")
    try:
        for words in parts:
            reason = decide_segment(words, payload.get("cwd"), check)
            if reason:
                return reason
    except Exception as e:  # noqa: BLE001 — fail closed once the command is an issue write
        return f"gh-issue-guard: could not verify: hook error {type(e).__name__}: {e}"
    return None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception as e:  # noqa: BLE001
        log(f"unreadable payload, allowed: {e}")
        return 0
    reason = decide(payload)
    if reason:
        log(f"denied: {str((payload.get('tool_input') or {}).get('command'))[:300]!r}\n  {reason}")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
