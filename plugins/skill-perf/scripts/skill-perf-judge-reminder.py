#!/usr/bin/env python3
"""skill-perf UserPromptSubmit hook — nudge the agent to judge unscored skill uses.

Fires on every user prompt. Keeps a turn counter; every SKILL_PERF_REMINDER_EVERY
turns (default 25), if the ledger holds unjudged rows, prints a short reminder to
stdout (which the harness injects into the turn context). The MAIN agent then
decides whether to run the report skill — no background LLM, no token spend until
the user/agent acts.

WHAT THIS TOUCHES:
  * Reads + writes ~/.claude/skill-perf/reminder-state.json (a turn counter).
  * Reads (never writes) the ledger to count unjudged rows.
  * Prints a markdown nudge to stdout at most once per N turns.

WHAT IT DOES NOT DO: never blocks, never runs an LLM, never touches the ledger's
skill_uses rows. Any exception → print nothing, exit 0.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

DB_DIR = Path.home() / ".claude" / "skill-perf"
DB_PATH = DB_DIR / "ledger.db"
STATE_PATH = DB_DIR / "reminder-state.json"
DEFAULT_EVERY = 25


def _every() -> int:
    try:
        n = int(os.environ.get("SKILL_PERF_REMINDER_EVERY", DEFAULT_EVERY))
        return n if n > 0 else DEFAULT_EVERY
    except ValueError:
        return DEFAULT_EVERY


def _bump_counter() -> int:
    count = 0
    try:
        if STATE_PATH.exists():
            count = int(json.loads(STATE_PATH.read_text()).get("turn_count", 0))
    except (json.JSONDecodeError, OSError, ValueError):
        count = 0
    count += 1
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps({"turn_count": count}))
    except OSError:
        pass
    return count


def _unjudged() -> int:
    if not DB_PATH.exists():
        return 0
    try:
        con = sqlite3.connect(str(DB_PATH), timeout=3)
        con.execute("PRAGMA busy_timeout=2000;")
        n = con.execute("SELECT COUNT(*) FROM skill_uses WHERE judged_at IS NULL").fetchone()[0]
        con.close()
        return int(n)
    except sqlite3.Error:
        return 0


def main() -> int:
    try:
        sys.stdin.read()  # drain; payload unused
    except Exception:
        pass

    try:
        count = _bump_counter()
        if count % _every() != 0:
            return 0
        pending = _unjudged()
        if pending <= 0:
            return 0
        print(
            f"# skill-perf reminder\n"
            f"{pending} skill invocation(s) in the ledger are unscored. "
            f"When convenient, run the **skill-perf-judge** skill to score their "
            f"adherence + compliance + completion/success — then review the rollup."
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
