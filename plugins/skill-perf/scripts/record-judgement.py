#!/usr/bin/env python3
"""Write the judge-owned columns for one ledger row. SINGLE write path for judging.

Usage:
  # normal verdict
  record-judgement.py --id 42 --adherence 0.9 --compliance 0.7 --success 1 \
      --completion-index 4 --model claude-opus-4-8 --notes "followed all steps"

  # terminal "cannot be scored" verdict (e.g. the session transcript aged out)
  record-judgement.py --id 42 --unjudgeable --reason "no transcript for session"

The judge supplies VERDICTS (adherence, compliance, success) and CHOOSES the
completion point as a span INDEX (--completion-index, taken from extract-span.py's
output). This script derives completion_ts / completion_ms / span_total_tokens
from that index via span_lib — the judge never does the arithmetic. Omit
--completion-index to leave the three completion columns NULL (e.g. a degenerate
span where the work never completed).

--unjudgeable records a TERMINAL non-verdict for a row that can never be scored
(its transcript is gone, so the span is unrecoverable). It sets judged_at (so the
row LEAVES the unjudged backlog and stops re-triggering the judge) but leaves every
score/completion column NULL and stamps judge_notes="UNJUDGEABLE: <reason>". That
NULL-adherence + non-NULL-judged_at shape is how the rollup tells an unjudgeable
row apart from a real judgement (which always carries an adherence score), so the
quality averages stay clean. --unjudgeable is mutually exclusive with the score
args — a row is either scored or retired, never both.

WHAT THIS TOUCHES:
  * UPDATEs exactly one row of skill_uses (by id): the judge-owned columns +
    judged_at=now. Reads the transcript (via span_lib, read-only) ONLY to derive
    the completion numbers from the chosen index. No other row, no other column,
    no writes anywhere else.

WHAT IT DOES NOT DO: never inserts, never edits mechanical columns, never judges,
and never lets the caller hand-pass completion math (that's why there is no
--completion-ts/--completion-ms/--span-tokens — only --completion-index).

Validates: adherence/compliance in [0,1]; success in {0,1}; completion-index in
range; --unjudgeable requires --reason and forbids score args. Bad input -> exit 2,
no write. Unknown id / unresolved transcript -> exit 1.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime

import span_lib

DB_PATH = span_lib.DB_PATH


def _unit(v, name):
    if v is None:
        return None
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"{name} must be in [0.0, 1.0], got {v}")
    return v


def _write_unjudgeable(row_id, reason, model):
    """Retire one row as terminally unscorable: set judged_at + an UNJUDGEABLE note,
    leave every score/completion column NULL. Exit 0 on success, 1 on unknown id / DB error."""
    now = datetime.now().astimezone().isoformat()
    try:
        con = sqlite3.connect(str(DB_PATH), timeout=5)
        con.execute("PRAGMA busy_timeout=4000;")
        cur = con.execute(
            "UPDATE skill_uses SET "
            "judge_adherence=NULL, judge_compliance=NULL, success=NULL, "
            "completion_ts=NULL, completion_ms=NULL, span_total_tokens=NULL, "
            "judge_notes=?, judge_model=?, judged_at=? "
            "WHERE id=?",
            (f"UNJUDGEABLE: {reason}", model, now, row_id),
        )
        con.commit()
        changed = cur.rowcount
        con.close()
    except sqlite3.Error as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    if changed == 0:
        print(f"FAIL: no ledger row with id={row_id}", file=sys.stderr)
        return 1
    print(f"ok: marked row id={row_id} unjudgeable ({reason})")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Record an LLM judgement for a skill-perf ledger row.")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--adherence", type=float)
    p.add_argument("--compliance", type=float)
    p.add_argument("--success", type=int, choices=(0, 1))
    p.add_argument("--completion-index", type=int,
                   help="span index (from extract-span.py) of the turn where the "
                        "skill-driven work completed; derives completion_ts/ms/tokens. "
                        "Omit to leave those columns NULL.")
    p.add_argument("--model")
    p.add_argument("--notes", default="")
    p.add_argument("--unjudgeable", action="store_true",
                   help="record a TERMINAL non-verdict: the row can never be scored "
                        "(transcript gone). Sets judged_at so it leaves the backlog; "
                        "leaves all scores NULL. Requires --reason; forbids score args.")
    p.add_argument("--reason", help="required with --unjudgeable: why the row can't be scored.")
    args = p.parse_args()

    if args.unjudgeable:
        score_args = {
            "--adherence": args.adherence, "--compliance": args.compliance,
            "--success": args.success, "--completion-index": args.completion_index,
        }
        offenders = [k for k, v in score_args.items() if v is not None]
        if offenders:
            print(f"FAIL: --unjudgeable is mutually exclusive with {', '.join(offenders)}",
                  file=sys.stderr)
            return 2
        if not (args.reason and args.reason.strip()):
            print("FAIL: --unjudgeable requires a non-empty --reason", file=sys.stderr)
            return 2
    elif args.reason is not None:
        print("FAIL: --reason is only valid with --unjudgeable", file=sys.stderr)
        return 2

    try:
        adherence = _unit(args.adherence, "adherence")
        compliance = _unit(args.compliance, "compliance")
    except ValueError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2

    if not DB_PATH.exists():
        print(f"FAIL: ledger not found at {DB_PATH} (run init-ledger-db.py)", file=sys.stderr)
        return 1

    if args.unjudgeable:
        return _write_unjudgeable(args.id, args.reason.strip(), args.model)

    # Derive completion numbers from the chosen index — the math lives in span_lib,
    # NOT in the judge. Absent index -> the three completion columns stay NULL.
    completion_ts = completion_ms = span_tokens = None
    if args.completion_index is not None:
        try:
            ctx = span_lib.load_context(args.id)
            fields = span_lib.completion_fields(ctx, args.completion_index)
        except span_lib.SpanError as e:
            print(f"FAIL: {e}", file=sys.stderr)
            # out-of-range / empty-span = caller error (2); unresolved row/transcript = 1
            return 2 if ("out of range" in str(e) or "empty" in str(e)) else 1
        completion_ts = fields["completion_ts"]
        completion_ms = fields["completion_ms"]
        span_tokens = fields["span_total_tokens"]

    now = datetime.now().astimezone().isoformat()
    try:
        con = sqlite3.connect(str(DB_PATH), timeout=5)
        con.execute("PRAGMA busy_timeout=4000;")
        cur = con.execute(
            "UPDATE skill_uses SET "
            "judge_adherence=?, judge_compliance=?, success=?, "
            "completion_ts=?, completion_ms=?, span_total_tokens=?, "
            "judge_notes=?, judge_model=?, judged_at=? "
            "WHERE id=?",
            (adherence, compliance, args.success,
             completion_ts, completion_ms, span_tokens,
             args.notes, args.model, now, args.id),
        )
        con.commit()
        changed = cur.rowcount
        con.close()
    except sqlite3.Error as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    if changed == 0:
        print(f"FAIL: no ledger row with id={args.id}", file=sys.stderr)
        return 1
    print(f"ok: judged row id={args.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
