#!/usr/bin/env python3
"""stack-detect.py — SessionStart hook that names the stack profile(s) for this repo.

WHY THIS EXISTS
---------------
The eleven stack-profile triggers used to be a table in the resident CLAUDE.md,
re-read by the model in every session of every project so it could evaluate
`∃f(Cargo.toml)` against a directory it had not looked at yet. That is a
filesystem predicate, and a filesystem predicate is free in shell:

    T := the trigger table is resident prose
    D := this detector

    T ⊢ cost = |table| tokens × every session × every project,
        and the model must still stat the tree to decide
    D ⊢ cost = 0 tokens when nothing matches, one line when something does,
        and the answer is computed, not recalled

    ∴ D ≻ T   whenever the trigger is decidable from the filesystem

WHAT THIS HOOK DOES (and ONLY this)
-----------------------------------
Globs the session's cwd for stack markers, then emits one `additionalContext`
block naming the profile files to read.

    marker(p)  ≡ a file whose presence names the stack outright (Cargo.toml, go.mod)
    census(p)  ≡ |tracked files with p's extensions| ≥ BULK_FLOOR

    emit(p) ↔ marker(p) ∨ census(p)
    □(react-vite ∈ E → node-typescript ordered first)     the profile says to
    □(E = ∅ → stdout = ∅)                                 silent, not "no stack detected"
    □(error → exit 0 ∧ stdout = ∅)                        fail open, never wedge startup

WHAT IT DOES NOT TOUCH
----------------------
Never reads a profile's contents, never edits anything, never writes outside its
own log. It names files; the model decides whether to read them.

Escape hatch: env STACK_DETECT_DISABLE=1 → no-op.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

BULK_FLOOR = 5          # files of an extension before a census trigger fires
WALK_CAP = 4000         # files examined when the cwd is not a git repo
LOG_PATH = Path.home() / ".claude" / "hooks" / "stack-detect.log"

# profile → (marker globs, census extensions)
# Markers are matched against repo-root-relative paths; a marker glob containing
# "/" must match a path, one without it matches a basename anywhere in the tree.
PROFILES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "swift-apple":     (("*.xcodeproj", "*.xcworkspace", "Package.swift", "project.yml"), (".swift",)),
    "rust":            (("Cargo.toml",), (".rs",)),
    "go":              (("go.mod",), (".go",)),
    "python-uv":       (("pyproject.toml", "setup.py", "requirements.txt", "requirements-*.txt"), (".py",)),
    "node-typescript": ((), (".ts", ".tsx")),   # marker is a conjunction — see detect()
    "react-vite":      (("vite.config.*", "next.config.*"), ()),
    "rails":           (("config/application.rb", "bin/rails"), ()),
    "infra-terraform": (("*.tf",), (".tf",)),
    "kubernetes":      ((), ()),                # directory-scoped — see detect()
    "postgres-sql":    ((), ()),                # directory-scoped — see detect()
    "bash-scripts":    ((), (".sh", ".bash")),
}

K8S_DIRS = ("k8s", "kubernetes", "manifests", "deploy", "charts", "kustomize")
SQL_DIRS = ("migrations", "db")

# react-vite's own profile opens by requiring the TypeScript baseline first.
ORDER_BEFORE = {"react-vite": "node-typescript"}


def log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def profiles_dir() -> Path:
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(cfg) if cfg else Path.home() / ".claude"
    return base / "stacks"


def repo_files(cwd: str) -> list[str]:
    """cwd-relative paths: tracked files when git knows any, a bounded walk otherwise.

    An EMPTY tracked list is not an empty directory — a repo with no commits yet,
    or a cwd that its parent repo gitignores, both report zero. Falling through to
    the walk is what keeps those cases from going silently undetected.
    """
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "ls-files"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            tracked = [line for line in out.stdout.splitlines() if line]
            if tracked:
                return tracked
    except Exception:
        pass

    found: list[str] = []
    root = Path(cwd)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
        for name in filenames:
            found.append(str(Path(dirpath, name).relative_to(root)))
            if len(found) >= WALK_CAP:
                return found
    return found


def glob_to_re(pattern: str) -> re.Pattern[str]:
    """Translate a marker glob to a regex over cwd-relative paths.

    A pattern with "/" anchors to the root; one without matches any path
    COMPONENT at any depth. Component, not basename: `*.xcodeproj` and
    `*.xcworkspace` are bundle directories, so they only ever appear as an
    interior component of a file path.
    """
    body = re.escape(pattern).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return re.compile(rf"^{body}$" if "/" in pattern else rf"(^|/){body}(/|$)")


def matches_marker(files: list[str], patterns: tuple[str, ...]) -> bool:
    if not patterns:
        return False
    regexes = [glob_to_re(p) for p in patterns]
    return any(rx.search(f) for f in files for rx in regexes)


def census(files: list[str], extensions: tuple[str, ...]) -> bool:
    if not extensions:
        return False
    n = sum(1 for f in files if f.endswith(extensions))
    return n >= BULK_FLOOR


def in_dirs(files: list[str], dirs: tuple[str, ...], suffixes: tuple[str, ...]) -> bool:
    return any(
        f.endswith(suffixes) and any(part in dirs for part in Path(f).parts[:-1])
        for f in files
    )


def detect(files: list[str]) -> list[str]:
    hits: list[str] = []
    for name, (markers, exts) in PROFILES.items():
        if name == "node-typescript":
            # package.json AND tsconfig.json — a conjunction the marker list can't express.
            hit = (matches_marker(files, ("package.json",))
                   and matches_marker(files, ("tsconfig.json",))) or census(files, exts)
        elif name == "kubernetes":
            hit = in_dirs(files, K8S_DIRS, (".yaml", ".yml"))
        elif name == "postgres-sql":
            hit = in_dirs(files, SQL_DIRS, (".sql",))
        else:
            hit = matches_marker(files, markers) or census(files, exts)
        if hit:
            hits.append(name)

    for profile, prerequisite in ORDER_BEFORE.items():
        if profile in hits and prerequisite not in hits:
            hits.append(prerequisite)

    return sorted(hits, key=lambda n: (n in ORDER_BEFORE, n))


def render(names: list[str], directory: Path) -> str | None:
    present = [n for n in names if (directory / f"{n}.md").exists()]
    if not present:
        return None
    lines = [
        "Stack profile(s) detected for this repo. Read before writing code here:",
        "",
    ]
    lines += [f"  {directory / f'{n}.md'}" for n in present]
    if "react-vite" in present and "node-typescript" in present:
        lines += ["", "  node-typescript first — react-vite builds on its baseline."]
    return "\n".join(lines)


def main() -> int:
    if os.environ.get("STACK_DETECT_DISABLE") == "1":
        return 0

    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}
    cwd = (payload.get("cwd") if isinstance(payload, dict) else None) or os.getcwd()

    files = repo_files(cwd)
    if not files:
        return 0

    names = detect(files)
    if not names:
        return 0

    context = render(names, profiles_dir())
    if context is None:
        log(f"detected {names} but no profile files under {profiles_dir()}")
        return 0

    log(f"cwd={cwd} files={len(files)} → {names}")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"unhandled exception: {e!r}")
        sys.exit(0)
