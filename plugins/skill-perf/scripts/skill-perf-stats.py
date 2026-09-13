#!/usr/bin/env python3
"""skill-perf rollup report — read-only aggregate over the ledger.

Usage:
  skill-perf-stats.py                      # human table, all skills
  skill-perf-stats.py --skill design:design-system
  skill-perf-stats.py --since 2026-06-01   # filter by invocation date
  skill-perf-stats.py --json               # machine-readable

WHAT THIS TOUCHES: nothing. Opens the ledger read-only and prints a per-skill +
overall summary across the five tracked dimensions:
  token count, latency-to-first-token, time-to-completion (judged),
  adherence-to-goals (judged), overall-compliance (judged).

Never mutates the DB. Exit 0 on success; non-zero if the ledger is missing.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "skill-perf" / "ledger.db"


def _p(values, q):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(vals) - 1)
    return round(vals[lo] + (vals[hi] - vals[lo]) * (k - lo), 2)


def _stat(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return {
        "n": len(vals),
        "mean": round(statistics.mean(vals), 2),
        "median": round(statistics.median(vals), 2),
        "p90": _p(vals, 0.90),
        "min": min(vals),
        "max": max(vals),
    }


def _summarize(rows):
    n = len(rows)
    # A processed row (judged_at set) is either SCORED (carries an adherence verdict)
    # or UNJUDGEABLE (retired because its transcript is gone — every score is NULL).
    # Only scored rows feed the quality stats; unjudgeable rows are counted apart so
    # the averages aren't diluted by rows that were never actually judged.
    processed = [r for r in rows if r["judged_at"] is not None]
    scored = [r for r in processed if r["judge_adherence"] is not None]
    unjudgeable = len(processed) - len(scored)
    succ = [r["success"] for r in scored if r["success"] is not None]
    return {
        "uses": n,
        "judged": len(scored),
        "unjudgeable": unjudgeable,
        "output_tokens": _stat([r["output_tokens"] for r in rows]),
        "span_total_tokens": _stat([r["span_total_tokens"] for r in scored]),
        "first_token_latency_ms": _stat([r["first_token_latency_ms"] for r in rows]),
        "completion_ms": _stat([r["completion_ms"] for r in scored]),
        "success_rate": (round(sum(succ) / len(succ), 3) if succ else None),
        "adherence": _stat([r["judge_adherence"] for r in scored]),
        "compliance": _stat([r["judge_compliance"] for r in scored]),
    }


def _fmt(stat, unit="", scale=1.0):
    if not stat:
        return "—"
    m = stat["mean"] / scale
    p = stat["p90"] / scale if stat["p90"] is not None else None
    return f"{m:.0f}{unit} (p90 {p:.0f}{unit})" if p is not None else f"{m:.0f}{unit}"


def main() -> int:
    ap = argparse.ArgumentParser(description="skill-perf rollup report")
    ap.add_argument("--skill")
    ap.add_argument("--since", help="ISO date/time lower bound on invocation_ts")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"FAIL: ledger not found at {DB_PATH} (run init-ledger-db.py / apply.py)", file=sys.stderr)
        return 1

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    q = "SELECT * FROM skill_uses WHERE 1=1"
    params = []
    if args.skill:
        q += " AND skill_name=?"
        params.append(args.skill)
    if args.since:
        q += " AND invocation_ts >= ?"
        params.append(args.since)
    rows = con.execute(q, params).fetchall()
    con.close()

    by_skill = {}
    for r in rows:
        by_skill.setdefault(r["skill_name"], []).append(r)

    report = {
        "overall": _summarize(rows),
        "by_skill": {name: _summarize(rs) for name, rs in sorted(by_skill.items())},
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    o = report["overall"]
    print("=== skill-perf rollup ===")
    print(f"total skill uses: {o['uses']}  judged: {o['judged']}  "
          f"unjudgeable: {o['unjudgeable']}\n")
    if not rows:
        print("(no skill invocations recorded yet)")
        return 0
    header = f"{'skill':<34} {'uses':>5} {'judged':>6} {'unjdg':>6} {'out_tok':>16} {'latency':>16} {'compl_ms':>16} {'succ':>5} {'adher':>6} {'compl':>6}"
    print(header)
    print("-" * len(header))
    for name, s in sorted(report["by_skill"].items()):
        succ = f"{s['success_rate']*100:.0f}%" if s["success_rate"] is not None else "—"
        adher = f"{s['adherence']['mean']:.2f}" if s["adherence"] else "—"
        compl = f"{s['compliance']['mean']:.2f}" if s["compliance"] else "—"
        unjdg = s["unjudgeable"] or "—"
        print(f"{name[:34]:<34} {s['uses']:>5} {s['judged']:>6} {unjdg:>6} "
              f"{_fmt(s['output_tokens']):>16} {_fmt(s['first_token_latency_ms'], 's', 1000):>16} "
              f"{_fmt(s['completion_ms'], 's', 1000):>16} {succ:>5} {adher:>6} {compl:>6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
