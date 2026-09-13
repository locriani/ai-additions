#!/usr/bin/env python3
"""Create (idempotently) the skill-perf SQLite ledger from schema.sql.

WHAT THIS TOUCHES:
  * Creates the directory ~/.claude/skill-perf/ if absent.
  * Creates / migrates ~/.claude/skill-perf/ledger.db by executing the DDL in
    the sibling schema.sql (CREATE TABLE/INDEX IF NOT EXISTS — safe to re-run).
  * Sets WAL journal mode on the DB.

WHAT IT EXPLICITLY DOES NOT TOUCH:
  * Never writes rows. Never edits settings.json. Never installs hooks.
  * Never drops or alters existing columns (additive schema only).

Idempotent: re-running is a no-op once the table exists. Exits 0 on success,
non-zero with a message on failure.

Reads the DDL from schema.sql sitting NEXT TO this script (the deployed copy
lives at ~/.claude/skill-perf/schema.sql) so the table definition has exactly
one source.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB_DIR = Path.home() / ".claude" / "skill-perf"
DB_PATH = DB_DIR / "ledger.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"FAIL: schema.sql not found next to init script: {SCHEMA_PATH}", file=sys.stderr)
        return 1

    DB_DIR.mkdir(parents=True, exist_ok=True)
    ddl = SCHEMA_PATH.read_text(encoding="utf-8")

    try:
        con = sqlite3.connect(str(DB_PATH))
        try:
            con.execute("PRAGMA journal_mode=WAL;")
            con.executescript(ddl)
            con.commit()
        finally:
            con.close()
    except sqlite3.Error as e:
        print(f"FAIL: could not initialize {DB_PATH}: {e}", file=sys.stderr)
        return 1

    print(f"ok: ledger ready at {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
