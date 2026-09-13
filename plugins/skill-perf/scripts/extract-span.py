#!/usr/bin/env python3
"""Extract the post-invocation transcript span for one ledger row, for the judge.

Usage: extract-span.py --id 42            # emits JSON to stdout
       extract-span.py --id 42 --max-chars 1500

WHAT THIS TOUCHES: nothing. Pure read — delegates to span_lib.load_context() to
look up the row, find the session transcript, and build the window of assistant
actions that FOLLOWED the skill (up to the next Skill use). Each span turn is
INDEXED and carries precomputed elapsed_ms + cumulative_tokens, so the judge
chooses a completion INDEX without doing arithmetic — the math lives in
span_lib, and record-judgement.py derives the final numbers from that index.

Does NOT resolve SKILL.md (resolve-skill-md.py) and does NOT write the DB.
"""
from __future__ import annotations

import argparse
import json
import sys

import span_lib


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract a judge-ready transcript span for a ledger row.")
    ap.add_argument("--id", type=int, required=True)
    ap.add_argument("--max-chars", type=int, default=2000)
    args = ap.parse_args()

    try:
        ctx = span_lib.load_context(args.id, max_chars=args.max_chars)
    except span_lib.SpanError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print(json.dumps(ctx, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
