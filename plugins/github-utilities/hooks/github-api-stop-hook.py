#!/usr/bin/env python3
"""
Stop-hook enforcer for the "gh CLI is the only GitHub surface" rule.

Scans the trailing assistant turn for GitHub web-API attempts when `gh`'s
high-level subcommands could have covered the action. Blocks turn-end with
remediation guidance unless the assistant's final response carries an explicit
escape token.

Violations (regex against the tool_use's input):

  Bash `command` matches any of:
    * (curl|wget|http|httpie) ... api.github.com   → raw REST bypass
    * gh api <endpoint> where a gh subcommand covers the endpoint
      (gh_api_coverage.COVERED); an uncovered endpoint is gh api's to reach

  WebFetch / web_fetch / *fetch* / *navigate* / *open_url* MCP tools where
  any string-valued arg contains github.com (any subdomain or path).

Escape hatch: if the LAST assistant text block of the turn contains a line
starting with `WEB-API-FALLBACK-JUSTIFIED:` (case-insensitive, leading
whitespace allowed), exit 0 (allow Stop). Used when `gh` genuinely doesn't
cover the action.

Loop guard: if `stop_hook_active: true`, exit 0 (let the second Stop through).

Failure mode: any exception → log + exit 0. Never block on tooling failure.

Hook contract: https://docs.claude.com/en/docs/claude-code/hooks
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gh_api_coverage import api_calls, covered  # noqa: E402

LOG_PATH = Path.home() / ".claude" / "hooks" / "github-api-stop-hook.log"

# --- Violation patterns ---------------------------------------------------

# Raw REST clients hitting GitHub's API host.
RE_WEB_API_CLIENT = re.compile(
    r"\b(?:curl|wget|http|httpie)\b[^\n]*\bapi\.github\.com\b",
    re.IGNORECASE,
)

# `gh api` — a quick filter; `gh_api_coverage` decides whether the endpoint is covered.
# Must follow a word boundary so `something-gh api` (unlikely) doesn't match,
# and `gh apiserver` (also unlikely) doesn't either.
RE_GH_API = re.compile(r"(?:^|[\s;&|`(])gh\s+api\b", re.IGNORECASE)

# github.com URL anywhere in a tool input (web-fetch tools).
RE_GITHUB_URL = re.compile(r"\bhttps?://[^\s\"']*github\.com\b", re.IGNORECASE)

# Tool names that fetch web content. MCP servers use various conventions
# (`*__fetch`, `*__navigate`, `*__open_url`, plain `WebFetch`, etc.).
RE_FETCH_TOOL_NAME = re.compile(
    r"(?:^|[_\W])(?:web_?fetch|fetch|navigate|open_url|goto|visit|browse)(?:$|[_\W])",
    re.IGNORECASE,
)

ESCAPE_TOKEN_RE = re.compile(
    r"^\s*WEB-API-FALLBACK-JUSTIFIED\s*:",
    re.IGNORECASE | re.MULTILINE,
)


def log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def parse_transcript(path: str):
    """Yield each JSONL record. Tolerate malformed lines."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _unwrap(rec: dict) -> tuple[str | None, object]:
    """Return (role, content). Handles {"message": {...}} wrapping."""
    msg = rec.get("message") if isinstance(rec.get("message"), dict) else rec
    role = msg.get("role") or rec.get("role")
    content = msg.get("content")
    return role, content


def _is_tool_result(content) -> bool:
    """True when a role="user" record's content carries a tool_result block.
    Such records are tool output echoed back into the turn, NOT genuine user
    input, so they must not be treated as the turn boundary."""
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return True
    return False


def collect_last_turn(records: list[dict]) -> tuple[list[dict], str]:
    """
    Walk backwards from the end of the transcript to isolate the CURRENT turn.

    Returns (assistant_tool_uses, last_assistant_text):
      - assistant_tool_uses: every tool_use block from the trailing assistant
        run. The run ends at the last REAL user message; tool_result records
        (which are ALSO role="user") are skipped, NOT treated as the boundary.
        Otherwise a `tool_use -> tool_result -> final text` sequence — the
        normal shape of any multi-step turn — would hide the tool_use and the
        hook would miss the very violation it exists to catch.
      - last_assistant_text: concatenated text blocks from the LAST assistant
        message in the trailing run (this is where the escape token lives).
    """
    tool_uses: list[dict] = []
    last_assistant_text_parts: list[str] = []
    captured_text_from_one_message = False

    for rec in reversed(records):
        if not isinstance(rec, dict):
            continue
        # Skip non-message records (attachment / last-prompt / queue-operation)
        # when the transcript tags them; flat test fixtures omit `type`.
        rtype = rec.get("type")
        if rtype is not None and rtype not in ("user", "assistant"):
            continue

        role, content = _unwrap(rec)
        if content is None:
            continue

        if role == "user":
            if _is_tool_result(content):
                continue  # tool result echoed back — not a turn boundary
            break  # genuine user message — end of the trailing assistant run

        if role == "assistant":
            text_parts_this_msg: list[str] = []
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")
                    if btype == "tool_use":
                        tool_uses.append(block)
                    elif btype == "text":
                        t = block.get("text")
                        if isinstance(t, str):
                            text_parts_this_msg.append(t)
            elif isinstance(content, str):
                text_parts_this_msg.append(content)

            # The LAST assistant message (first one we hit walking backwards
            # that has text) holds the escape token.
            if text_parts_this_msg and not captured_text_from_one_message:
                last_assistant_text_parts = text_parts_this_msg
                captured_text_from_one_message = True

    return tool_uses, "\n".join(last_assistant_text_parts)


def _iter_string_values(obj) -> list[str]:
    """Walk a nested dict/list and yield every string leaf."""
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(_iter_string_values(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_iter_string_values(v))
    return out


def _gh_api_violations(cmd: str) -> list[dict]:
    """One violation per `gh api` call whose endpoint a gh subcommand covers.

    Zach, 2026-09-22 14:50: allow gh api for features that are not in the CLI yet. A command that
    does not parse cannot be judged, so it stays a violation as before.
    """
    try:
        calls = api_calls(cmd)
    except ValueError:
        return [{"tool": "Bash", "kind": "`gh api` in a command that does not parse",
                 "evidence": _truncate(cmd, 200)}]
    out = []
    for call in calls:
        sub = covered(call.endpoint)
        if sub:
            out.append({"tool": "Bash",
                        "kind": f"`gh api {call.endpoint}` — covered by `{sub}`; use it",
                        "evidence": _truncate(cmd, 200)})
    return out


def find_violations(tool_uses: list[dict]) -> list[dict]:
    """
    Returns a list of {"tool": str, "kind": str, "evidence": str} dicts.
    """
    violations: list[dict] = []
    for block in tool_uses:
        name = block.get("name") or ""
        inp = block.get("input") or {}
        if not isinstance(inp, dict):
            continue

        if name == "Bash":
            cmd = inp.get("command")
            if isinstance(cmd, str):
                if RE_WEB_API_CLIENT.search(cmd):
                    violations.append({
                        "tool": "Bash",
                        "kind": "raw HTTP client hitting api.github.com",
                        "evidence": _truncate(cmd, 200),
                    })
                if RE_GH_API.search(cmd):
                    violations.extend(_gh_api_violations(cmd))
            continue

        # Non-Bash tools: WebFetch + any MCP fetch/navigate/open_url tool.
        if RE_FETCH_TOOL_NAME.search(name):
            for s in _iter_string_values(inp):
                if RE_GITHUB_URL.search(s):
                    violations.append({
                        "tool": name,
                        "kind": "web-fetch tool targeting github.com",
                        "evidence": _truncate(s, 200),
                    })
                    break  # one violation per tool_use is enough

    return violations


def _truncate(s: str, n: int) -> str:
    s = s.strip()
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def build_block_reason(violations: list[dict]) -> str:
    lines = [
        "GitHub web-API call detected where a `gh` subcommand covers it. Use the subcommand.",
        "",
        "Violations this turn:",
    ]
    for v in violations:
        lines.append(f"  • [{v['tool']}] {v['kind']}")
        lines.append(f"      {v['evidence']}")
    lines += [
        "",
        "Remediation:",
        "  - `gh issue ...`, `gh pr ...`, `gh repo ...`, `gh run ...`, `gh workflow ...`",
        "    cover viewing/creating/commenting on issues + PRs, repo metadata,",
        "    workflow runs, releases. See rules/GITHUB.md in ai-additions.",
        "  - `gh api` is fine where no subcommand exists (graphql, contents,",
        "    rulesets, ...); the covered list is hooks/gh_api_coverage.py.",
        "  - If the subcommand genuinely can't do this particular call, end your",
        "    turn's final response with a line:",
        "        WEB-API-FALLBACK-JUSTIFIED: <one-sentence reason>",
        "    The hook reads this token and allows Stop.",
    ]
    return "\n".join(lines)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as e:
        log(f"stdin not JSON: {e}")
        return 0

    if payload.get("stop_hook_active") is True:
        return 0

    transcript_path = payload.get("transcript_path")
    if not isinstance(transcript_path, str) or not transcript_path:
        return 0
    if not Path(transcript_path).exists():
        return 0

    try:
        records = list(parse_transcript(transcript_path))
    except Exception as e:
        log(f"transcript read failed: {e}")
        return 0

    tool_uses, last_text = collect_last_turn(records)
    if not tool_uses:
        return 0

    violations = find_violations(tool_uses)
    if not violations:
        return 0

    if last_text and ESCAPE_TOKEN_RE.search(last_text):
        log(f"allowed via escape token; {len(violations)} violation(s)")
        return 0

    reason = build_block_reason(violations)
    log(f"BLOCK: {len(violations)} violation(s)")
    print(json.dumps({"decision": "block", "reason": reason}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"unhandled exception: {e!r}")
        sys.exit(0)
