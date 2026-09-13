#!/usr/bin/env python3
"""Retire ledger rows that can NEVER be judged — their session transcript is gone.

Usage:
  sweep-unjudgeable.py             # DRY RUN (default): list pending rows whose
                                   #   transcript is missing; write nothing.
  sweep-unjudgeable.py --apply     # mark each such row unjudgeable.
  sweep-unjudgeable.py --json      # machine-readable list (composable with --apply).

WHY: a skill use is only judgeable while its session transcript still exists under
~/.claude/projects/. Once cleanupPeriodDays ages the transcript out, extract-span.py
can never rebuild the span, so the row is stuck at judged_at IS NULL forever — it
re-enters the judge backlog every run and every reminder, and dispatching an LLM
judge at it only wastes tokens to SKIP. This sweep is the cheap, LLM-free drain:
it selects those rows by checking transcript existence (no span build, no model)
and retires them via the single write path.

WHAT THIS TOUCHES:
  * Reads (never writes) skill_uses to list pending rows (judged_at IS NULL).
  * Read-only checks transcript existence via span_lib.find_transcript.
  * With --apply ONLY: shells out to record-judgement.py --unjudgeable once per
    missing-transcript row, so the actual UPDATE stays in that one write path
    (no duplicated SQL here).

WHAT IT EXPLICITLY DOES NOT DO: never builds a span, never runs an LLM, never
scores, never touches rows whose transcript still exists (those remain judgeable),
never edits mechanical columns. Dry run by default — nothing is written without
--apply.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import span_lib

DB_PATH = span_lib.DB_PATH
RECORD_JUDGEMENT = Path(__file__).resolve().parent / "record-judgement.py"
REASON = "no transcript for session (aged out)"


def _pending_missing_transcript():
    """Pending rows (judged_at IS NULL) whose session transcript no longer exists."""
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, skill_name, session_id FROM skill_uses "
        "WHERE judged_at IS NULL ORDER BY id"
    ).fetchall()
    con.close()
    missing = []
    for r in rows:
        if span_lib.find_transcript(r["session_id"]) is None:
            missing.append({"id": r["id"], "skill_name": r["skill_name"],
                            "session_id": r["session_id"]})
    return missing


def _apply(row_id):
    """Retire one row via the single write path. Returns True on success."""
    proc = subprocess.run(
        [sys.executable, str(RECORD_JUDGEMENT), "--id", str(row_id),
         "--unjudgeable", "--reason", REASON, "--model", "sweep"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(f"FAIL: id={row_id}: {proc.stderr.strip()}", file=sys.stderr)
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Retire never-judgeable rows (transcript gone).")
    ap.add_argument("--apply", action="store_true",
                    help="actually mark the rows unjudgeable (default is a dry run).")
    ap.add_argument("--json", action="store_true", help="emit the row list as JSON.")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"FAIL: ledger not found at {DB_PATH}", file=sys.stderr)
        return 1

    missing = _pending_missing_transcript()

    if args.json:
        print(json.dumps(missing, indent=2))
    else:
        verb = "Retiring" if args.apply else "Would retire (dry run)"
        print(f"{verb} {len(missing)} pending row(s) with no transcript:")
        for m in missing:
            print(f"  id={m['id']:<5} {m['skill_name']}  (session {m['session_id'][:8]}…)")

    if not args.apply:
        if missing and not args.json:
            print("\nRe-run with --apply to retire them.")
        return 0

    failed = 0
    for m in missing:
        if not _apply(m["id"]):
            failed += 1
    done = len(missing) - failed
    print(f"\nretired {done} row(s) as unjudgeable"
          + (f"; {failed} failed" if failed else ""), file=sys.stderr if failed else sys.stdout)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
