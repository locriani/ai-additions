#!/usr/bin/env python3
"""Resolve a Skill name to its SKILL.md path. SINGLE source of this lookup.

Usage: resolve-skill-md.py "design:design-system"   ->  prints absolute path
       resolve-skill-md.py "brainstorming"           ->  bare name also works

WHAT THIS TOUCHES: nothing. Pure read — globs the plugin/skill install dirs and
prints one path to stdout. Exit 0 + path on success; exit 1 + stderr on miss.

A "plugin:skill" name splits on the first colon: the right half is the skill dir
under some `skills/<skill>/SKILL.md`; the left half (plugin) is used to prefer the
right match when several plugins ship a skill of the same name.
"""
from __future__ import annotations

import sys
from pathlib import Path

HOME = Path.home()
SEARCH_ROOTS = [
    HOME / ".claude" / "plugins" / "marketplaces",
    HOME / ".claude" / "plugins" / "cache",
    HOME / ".claude" / "skills",
    HOME / ".claude" / "plugins",
]


def resolve(name: str):
    plugin, _, skill = name.partition(":")
    if not skill:
        plugin, skill = "", plugin

    candidates: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        candidates.extend(root.glob(f"**/skills/{skill}/SKILL.md"))
        candidates.extend(root.glob(f"**/{skill}/SKILL.md"))

    # de-dupe, keep order
    seen, uniq = set(), []
    for c in candidates:
        rc = c.resolve()
        if rc not in seen:
            seen.add(rc)
            uniq.append(rc)

    if not uniq:
        return None
    if plugin:
        for c in uniq:
            if f"/{plugin}/" in str(c):
                return c
    return uniq[0]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: resolve-skill-md.py <plugin:skill | skill>", file=sys.stderr)
        return 2
    path = resolve(sys.argv[1].strip())
    if path is None:
        print(f"FAIL: no SKILL.md found for '{sys.argv[1]}'", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
