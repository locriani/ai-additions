#!/usr/bin/env python3
"""skill-perf Stop hook — log each Skill invocation's MECHANICAL metrics.

Fires at end of EVERY turn (machine-wide Stop hook). Scans the just-completed
transcript for `Skill` tool_use blocks and appends one row per *new* skill use
to ~/.claude/skill-perf/ledger.db. Pure observer.

WHAT THIS TOUCHES:
  * Appends rows to ~/.claude/skill-perf/ledger.db (INSERT OR IGNORE; dedupe on
    UNIQUE(turn_uuid, tool_use_id)). Ensures the table exists via the shared
    ~/.claude/skill-perf/schema.sql.

WHAT IT EXPLICITLY DOES NOT DO:
  * Never blocks the turn (never emits {"decision":"block"}). Never runs an LLM.
  * Never fills the judge-owned columns (completion/success/adherence/compliance).
  * Never edits settings.json or any file outside the ledger DB.

Failure mode: ANY exception → print nothing, exit 0. A telemetry hook must never
break a turn. stop_hook_active short-circuits the second-pass invocation.

Mechanical metrics captured per skill use:
  * invocation_ts          — ts of the assistant message bearing the Skill tool_use
  * first_token_latency_ms  — (ts of next assistant msg) - (ts of the tool_result)
  * output/input/cache tokens + model — from the immediate post-skill assistant turn
  * session_id, cwd, git_branch, turn_uuid, tool_use_id, skill_name, args_hash
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_DIR = Path.home() / ".claude" / "skill-perf"
DB_PATH = DB_DIR / "ledger.db"
SCHEMA_PATH = DB_DIR / "schema.sql"


def _parse_ts(value):
    """ISO8601 (with trailing Z, ms precision) -> aware datetime, or None."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _latency_ms(start_ts, end_ts):
    a, b = _parse_ts(start_ts), _parse_ts(end_ts)
    if a is None or b is None:
        return None
    return int(round((b - a).total_seconds() * 1000))


def _msg(rec):
    m = rec.get("message")
    return m if isinstance(m, dict) else {}


def _content(rec):
    c = _msg(rec).get("content")
    return c if isinstance(c, list) else []


def _role(rec):
    return _msg(rec).get("role") or rec.get("type")


def _iter_records(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _connect():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH), timeout=5)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA busy_timeout=4000;")
    if SCHEMA_PATH.exists():
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return con


def _find_tool_result_ts(records, start_idx, tool_use_id):
    """First record after start_idx carrying a tool_result for tool_use_id."""
    for rec in records[start_idx + 1:]:
        for block in _content(rec):
            if isinstance(block, dict) and block.get("type") == "tool_result" \
                    and block.get("tool_use_id") == tool_use_id:
                return rec.get("timestamp")
    return None


def _find_next_assistant(records, start_idx):
    """First assistant record after start_idx (the immediate post-skill response)."""
    for rec in records[start_idx + 1:]:
        if _role(rec) == "assistant":
            return rec
    return None


def _row_from_skill_use(records, idx, block, fallback_cwd):
    rec = records[idx]
    tool_use_id = block.get("id")
    skill_input = block.get("input") if isinstance(block.get("input"), dict) else {}
    skill_name = skill_input.get("skill")
    if not tool_use_id or not skill_name:
        return None

    invocation_ts = rec.get("timestamp")
    turn_uuid = rec.get("uuid") or tool_use_id
    session_id = rec.get("sessionId") or "unknown"
    if not invocation_ts:
        return None

    args = skill_input.get("args")
    args_hash = hashlib.sha256(args.encode("utf-8")).hexdigest() if isinstance(args, str) else None

    tool_result_ts = _find_tool_result_ts(records, idx, tool_use_id)
    nxt = _find_next_assistant(records, idx)

    first_token_latency_ms = _latency_ms(tool_result_ts, nxt.get("timestamp")) if nxt else None

    usage = _msg(nxt).get("usage") if nxt else None
    usage = usage if isinstance(usage, dict) else {}
    out_tok = usage.get("output_tokens")
    in_tok = usage.get("input_tokens")
    cache_tok = None
    if usage:
        cc = usage.get("cache_creation_input_tokens") or 0
        cr = usage.get("cache_read_input_tokens") or 0
        cache_tok = cc + cr if (usage.get("cache_creation_input_tokens") is not None
                                or usage.get("cache_read_input_tokens") is not None) else None
    model = _msg(nxt).get("model") if nxt else None

    return {
        "session_id": session_id,
        "turn_uuid": turn_uuid,
        "tool_use_id": tool_use_id,
        "skill_name": skill_name,
        "args_hash": args_hash,
        "invocation_ts": invocation_ts,
        "first_token_latency_ms": first_token_latency_ms,
        "output_tokens": out_tok,
        "input_tokens": in_tok,
        "cache_tokens": cache_tok,
        "model": model,
        "cwd": rec.get("cwd") or fallback_cwd,
        "git_branch": rec.get("gitBranch"),
    }


_COLS = ("session_id", "turn_uuid", "tool_use_id", "skill_name", "args_hash",
         "invocation_ts", "first_token_latency_ms", "output_tokens", "input_tokens",
         "cache_tokens", "model", "cwd", "git_branch")


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0

    if payload.get("stop_hook_active"):
        return 0

    transcript_path = payload.get("transcript_path")
    if not transcript_path or not Path(transcript_path).exists():
        return 0

    try:
        records = list(_iter_records(transcript_path))
    except OSError:
        return 0

    rows = []
    for idx, rec in enumerate(records):
        if _role(rec) != "assistant":
            continue
        for block in _content(rec):
            if isinstance(block, dict) and block.get("type") == "tool_use" \
                    and block.get("name") == "Skill":
                try:
                    row = _row_from_skill_use(records, idx, block, payload.get("cwd"))
                except Exception:
                    row = None
                if row:
                    rows.append(row)

    if not rows:
        return 0

    try:
        con = _connect()
        try:
            now = datetime.now().astimezone().isoformat()
            con.executemany(
                f"INSERT OR IGNORE INTO skill_uses "
                f"({', '.join(_COLS)}, created_at) "
                f"VALUES ({', '.join('?' for _ in _COLS)}, ?)",
                [tuple(r[c] for c in _COLS) + (now,) for r in rows],
            )
            con.commit()
        finally:
            con.close()
    except sqlite3.Error:
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
