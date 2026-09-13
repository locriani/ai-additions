#!/usr/bin/env python3
"""Shared transcript-span loader + completion-math for the skill-perf judge.

SINGLE SOURCE of three things, so they never drift and the LLM judge never does
arithmetic:
  1. locating a ledger row's session transcript,
  2. building the post-skill span (the assistant turns that FOLLOWED the Skill
     use, up to the next Skill use), each turn INDEXED with precomputed
     per-turn numbers (elapsed_ms vs the invocation, running cumulative_tokens),
  3. deriving the completion-point numbers (completion_ts / completion_ms /
     span_total_tokens) from an AGENT-CHOSEN completion index.

WHAT THIS TOUCHES: nothing — pure read of the ledger DB (one row) and the
session transcript .jsonl. No writes. Imported by extract-span.py (to present
the indexed span to the judge) and record-judgement.py (to derive the
completion numbers from the judge's chosen index). The judge picks an index;
this module owns the math.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "skill-perf" / "ledger.db"
PROJECTS = Path.home() / ".claude" / "projects"


class SpanError(Exception):
    """Raised when a row / transcript / skill-use / index can't be resolved."""


def parse_ts(value):
    """ISO8601 (trailing Z ok, ms precision) -> aware datetime, or None."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def find_transcript(session_id):
    hits = list(PROJECTS.glob(f"*/{session_id}.jsonl"))
    return hits[0] if hits else None


def read_records(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def _msg(rec):
    m = rec.get("message")
    return m if isinstance(m, dict) else {}


def role(rec):
    return _msg(rec).get("role") or rec.get("type")


def content(rec):
    c = _msg(rec).get("content")
    return c if isinstance(c, list) else []


def has_skill_use(rec):
    return any(isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill"
               for b in content(rec))


def skill_use_index(records, tool_use_id):
    for i, rec in enumerate(records):
        for b in content(rec):
            if isinstance(b, dict) and b.get("type") == "tool_use" \
                    and b.get("name") == "Skill" and b.get("id") == tool_use_id:
                return i
    return None


def usage_total(usage):
    """Sum input + output + cache tokens for one turn; missing fields count as 0."""
    if not isinstance(usage, dict):
        return 0
    keys = ("input_tokens", "output_tokens",
            "cache_creation_input_tokens", "cache_read_input_tokens")
    return sum(int(usage.get(k) or 0) for k in keys)


def summarize_block(b, max_chars):
    if not isinstance(b, dict):
        return {"type": "unknown"}
    t = b.get("type")
    if t == "text":
        return {"type": "text", "text": (b.get("text") or "")[:max_chars]}
    if t == "thinking":
        return {"type": "thinking", "text": (b.get("thinking") or "")[:max_chars]}
    if t == "tool_use":
        inp = b.get("input")
        return {"type": "tool_use", "name": b.get("name"),
                "input_preview": (json.dumps(inp)[:max_chars] if inp is not None else None)}
    if t == "tool_result":
        c = b.get("content")
        return {"type": "tool_result", "preview": (json.dumps(c)[:max_chars] if c is not None else None)}
    return {"type": t}


def load_context(row_id, max_chars=None):
    """Resolve a ledger row -> its post-skill span with per-turn derived numbers.

    Returns: {id, session_id, skill_name, invocation_ts, transcript, span}.
    Each span entry carries: index, ts, role, usage_total, elapsed_ms (vs the
    invocation), cumulative_tokens (running sum of usage_total through it), and
    — only when max_chars is given — summarized blocks.

    Raises SpanError with a human-readable message on any resolution failure.
    """
    if not DB_PATH.exists():
        raise SpanError(f"ledger not found at {DB_PATH}")
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT session_id, tool_use_id, skill_name, invocation_ts "
        "FROM skill_uses WHERE id=?", (row_id,)).fetchone()
    con.close()
    if row is None:
        raise SpanError(f"no ledger row id={row_id}")

    transcript = find_transcript(row["session_id"])
    if transcript is None:
        raise SpanError(f"no transcript for session {row['session_id']} under {PROJECTS}")

    records = read_records(transcript)
    start = skill_use_index(records, row["tool_use_id"])
    if start is None:
        raise SpanError(f"skill tool_use {row['tool_use_id']} not found in transcript")

    inv_dt = parse_ts(row["invocation_ts"])
    span = []
    cumulative = 0
    for offset, rec in enumerate(records[start + 1:]):
        if role(rec) == "assistant" and has_skill_use(rec):
            break  # next skill invocation closes this span
        ts = rec.get("timestamp")
        tot = usage_total(_msg(rec).get("usage"))
        cumulative += tot
        end_dt = parse_ts(ts)
        elapsed_ms = (int(round((end_dt - inv_dt).total_seconds() * 1000))
                      if (inv_dt and end_dt) else None)
        entry = {
            "index": offset,
            "ts": ts,
            "role": role(rec),
            "usage_total": tot,
            "elapsed_ms": elapsed_ms,
            "cumulative_tokens": cumulative,
        }
        if max_chars is not None:
            entry["blocks"] = [summarize_block(b, max_chars) for b in content(rec)]
        span.append(entry)

    return {
        "id": row_id,
        "session_id": row["session_id"],
        "skill_name": row["skill_name"],
        "invocation_ts": row["invocation_ts"],
        "transcript": str(transcript),
        "span": span,
    }


def completion_fields(ctx, index):
    """Derive (completion_ts, completion_ms, span_total_tokens) for a chosen span
    index. The numbers are READ from the precomputed span entry — the judge picks
    the index, this code owns the math. Raises SpanError on an out-of-range or
    empty-span index.
    """
    span = ctx["span"]
    if not span:
        raise SpanError("span is empty — no completion turn to select")
    if not (0 <= index < len(span)):
        raise SpanError(f"completion index {index} out of range [0, {len(span) - 1}]")
    e = span[index]
    return {
        "completion_ts": e["ts"],
        "completion_ms": e["elapsed_ms"],
        "span_total_tokens": e["cumulative_tokens"],
    }
