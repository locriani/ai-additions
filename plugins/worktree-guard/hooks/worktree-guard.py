#!/usr/bin/env python3
"""
Stop-hook auditor for the worktree-isolation rule.

When an agent's CWD is inside a git worktree, any write that targets a path
inside another worktree of the SAME repo (main checkout OR a sibling worktree)
is a violation: it silently corrupts a working tree the agent wasn't supposed
to touch and bypasses the isolation the worktree was created to provide.

This hook covers two write surfaces in the transcript's last assistant turn:

  Tier-1 (structured tools):
    Write, Edit, MultiEdit, NotebookEdit — file_path is in tool input JSON.

  Tier-2 (Bash commands — Layer 1 coverage):
    a) Redirections: `> PATH`, `>> PATH`, `tee [-a] PATH`, plus `2>`/`&>`.
    b) Write-verb invocations: cp, mv, rm, mkdir, touch, ln, chmod, chown,
       chgrp, install, rmdir, truncate, shred, dd, sed -i, perl -i.
       Read-only verbs (ls, cat, grep, head, tail, find, git status/log/diff…)
       are NOT flagged even when the command mentions a forbidden path.
    c) Foreign git mutations: `git -C <forbidden-worktree> <mutating-subcmd>`
       (commit, reset, checkout, switch, merge, rebase, push, add, rm, mv,
       stash, worktree add/remove, gc, etc.).

Tier-2 known limitations (acceptable — override mechanism handles false
positives, and real false negatives become Layer 2 / Layer 3 work):
  - `cd /forbidden && echo > x.txt` is missed (Layer 2: cd-context tracking).
  - $VAR / $(…) / heredocs with dynamic content are not expanded.
  - `python -c '... open(P, "w") ...'` is a black box.

Override (the only override surface — no env var, no allow-file). A violation
is silently dropped if any in-scope user message contains:
  - the literal absolute path of the violating write/target, OR
  - the violating file's basename + a write-intent verb, OR
  - one of: "outside the worktree", "outside this worktree", "in the main repo",
    "in the main checkout", "in the other worktree", "in the sibling worktree",
    "across worktrees".

Loop guard: if `stop_hook_active: true`, exit 0 (let the second Stop through).

Failure mode: any exception → log + exit 0. Never block on tooling failure.

Hook contract: https://docs.claude.com/en/docs/claude-code/hooks
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
BASH_TOOL = "Bash"
SCANNED_TOOLS = WRITE_TOOLS | {BASH_TOOL}

# --- Tier-2 (Bash) classification sets -------------------------------------

# Verbs whose presence as a command's leading token means "this segment writes."
# All positional path-like args are treated as candidate write targets.
BASH_WRITE_VERBS = {
    "cp", "mv", "rm", "mkdir", "touch", "ln", "chmod", "chown", "chgrp",
    "install", "rmdir", "truncate", "shred", "dd",
}

# Verbs that only mutate when an in-place flag is present.
BASH_INPLACE_EDITORS = {"sed", "perl", "gawk"}
BASH_INPLACE_FLAGS = {"-i", "--in-place"}  # gawk uses `-i inplace` (handled too)

# Command-prefix tokens we transparently skip when finding the leading verb.
BASH_PREFIX_NOOPS = {"sudo", "command", "exec", "nice", "time", "nohup", "unbuffer"}

# git subcommands that mutate state. Anything not in here is treated read-only.
GIT_MUTATING_SUBCOMMANDS = {
    "add", "rm", "mv", "commit", "reset", "checkout", "switch", "restore",
    "merge", "rebase", "pull", "fetch", "push", "stash", "tag", "branch",
    "worktree", "gc", "repack", "prune", "apply", "am", "revert",
    "cherry-pick", "clean", "notes", "update-ref", "update-index",
    "filter-branch", "filter-repo",
}

# Segment delimiters in shell. We split commands by these to isolate "command
# segments" we can classify independently.
BASH_SEGMENT_SPLIT_RE = re.compile(r"(?:\|\||&&|\||;|\n|&(?!&))")

# Redirection target capture. Matches `>`, `>>`, `2>`, `2>>`, `&>`, `&>>` etc.
# followed by an optional space and a target token. The target token may be:
#   - a double-quoted string  →  capture group 1
#   - a single-quoted string  →  capture group 2
#   - a bare token            →  capture group 3
# We try each in order and take whichever matched.
BASH_REDIRECT_RE = re.compile(
    r"(?:^|[\s;&|`(])"          # boundary
    r"(?:\d+|\&)?"               # optional fd or `&`
    r">{1,2}"                    # `>` or `>>`
    r"\s*"
    r"(?:"
    r'"((?:\\.|[^"\\])*)"'       # group 1: double-quoted
    r"|"
    r"'([^']*)'"                 # group 2: single-quoted
    r"|"
    r"([^\s<>|;&`)]+)"           # group 3: bare
    r")"
)

OVERRIDE_PHRASES = (
    "outside the worktree",
    "outside this worktree",
    "in the main repo",
    "in the main checkout",
    "in the other worktree",
    "in the sibling worktree",
    "across worktrees",
)
WRITE_VERBS = ("write", "edit", "update", "patch", "modify", "apply", "create")

LOG_PATH = Path.home() / ".claude" / "hooks" / "worktree-guard.log"


def log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def git(cwd: str, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip()
    except Exception:
        return None


def list_worktrees(cwd: str) -> list[str]:
    """Return realpath'd worktree paths from `git worktree list --porcelain`."""
    raw = git(cwd, "worktree", "list", "--porcelain")
    if not raw:
        return []
    paths: list[str] = []
    for line in raw.splitlines():
        if line.startswith("worktree "):
            p = line[len("worktree ") :].strip()
            try:
                paths.append(str(Path(p).resolve()))
            except Exception:
                paths.append(p)
    return paths


def parse_transcript(path: str):
    """Yield each JSONL record. Tolerate malformed lines."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def collect_last_turn(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Walk backwards from the end of the transcript.

    Returns (assistant_tool_uses, user_text_blocks_in_scope).
      - assistant_tool_uses: every tool_use block from the trailing assistant
        run (stops at the previous user message).
      - user_text_blocks_in_scope: text blocks from the most recent user
        message AND the one immediately before it (gives the override
        heuristic a little extra reach for re-prompts).
    """
    tool_uses: list[dict] = []
    user_texts: list[str] = []
    user_msgs_seen = 0
    in_trailing_assistant_run = True

    for rec in reversed(records):
        # Records can be wrapped many ways depending on harness version.
        msg = rec.get("message") if isinstance(rec.get("message"), dict) else rec
        role = msg.get("role") or rec.get("role")
        content = msg.get("content")
        if content is None:
            continue

        if role == "assistant" and in_trailing_assistant_run:
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        if block.get("name") in SCANNED_TOOLS:
                            tool_uses.append(block)
            continue

        if role == "user":
            in_trailing_assistant_run = False
            if user_msgs_seen < 2:
                if isinstance(content, str):
                    user_texts.append(content)
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            t = block.get("text")
                            if isinstance(t, str):
                                user_texts.append(t)
                user_msgs_seen += 1
            else:
                break

    return tool_uses, user_texts


def _resolve_path(token: str, cwd: str) -> str | None:
    """Best-effort: turn a path-like token into an absolute realpath. None on error."""
    if not token:
        return None
    # Strip surrounding matched quotes.
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        token = token[1:-1]
    if not token:
        return None
    # Tilde expansion (only `~` and `~/...`; skip `~user/`).
    if token == "~":
        token = os.path.expanduser("~")
    elif token.startswith("~/"):
        token = os.path.expanduser("~") + token[1:]
    try:
        p = Path(token)
        if not p.is_absolute():
            p = Path(cwd) / p
        # Resolve without requiring existence (strict=False is default in 3.6+).
        return str(p.resolve())
    except Exception:
        return None


def extract_paths_from_structured(
    block: dict, cwd: str
) -> list[tuple[str, str]]:
    """[(realpath, tool_name), ...] for one Write/Edit/MultiEdit/NotebookEdit block."""
    name = block.get("name", "")
    inp = block.get("input") or {}
    fp = inp.get("file_path") or inp.get("notebook_path")
    if not isinstance(fp, str) or not fp:
        return []
    resolved = _resolve_path(fp, cwd)
    return [(resolved or fp, name)]


_PATH_LIKE_RE = re.compile(r"^(?:/|\./|\.\./|~/|~$)")


def _is_pathlike(token: str) -> bool:
    """True if the token looks like an absolute, relative, or tilde path."""
    if not token:
        return False
    # Strip surrounding quotes for the test.
    t = token
    if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"'):
        t = t[1:-1]
    return bool(_PATH_LIKE_RE.match(t))


def _segment_into_commands(command: str) -> list[str]:
    """Split a Bash command on `;`, `&&`, `||`, `|`, `&` (single), and newline."""
    return [s.strip() for s in BASH_SEGMENT_SPLIT_RE.split(command) if s.strip()]


def _tokenize(segment: str) -> list[str]:
    """Quote-aware tokenize via shlex (POSIX rules). Falls back to a dumb
    whitespace split if shlex chokes on unbalanced quotes / backticks etc.
    Tokens come back already unquoted by shlex."""
    try:
        return shlex.split(segment, posix=True, comments=False)
    except ValueError:
        return [t for t in re.split(r"\s+", segment) if t]


def _leading_verb(tokens: list[str]) -> tuple[str, list[str]]:
    """Skip prefix no-ops (sudo, env X=Y, …) and return (verb, rest_of_tokens).
    Returns ("", []) if the segment has no recognizable verb."""
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in BASH_PREFIX_NOOPS:
            i += 1
            continue
        # `env VAR=val ...` — skip env and any subsequent VAR=val tokens.
        if t == "env":
            i += 1
            while i < len(tokens) and "=" in tokens[i] and not tokens[i].startswith("-"):
                i += 1
            continue
        # Bare assignments like `FOO=bar cmd ...` — skip them.
        if "=" in t and not t.startswith("-") and t.split("=", 1)[0].replace("_", "").isalnum():
            i += 1
            continue
        return t, tokens[i + 1 :]
    return "", []


def _has_inplace_flag(rest_tokens: list[str], verb: str) -> bool:
    if verb == "gawk":
        # `gawk -i inplace …`
        for j, tok in enumerate(rest_tokens):
            if tok == "-i" and j + 1 < len(rest_tokens) and rest_tokens[j + 1] == "inplace":
                return True
        return False
    # sed / perl: any token equal to -i or --in-place, OR -iEXT for sed/perl.
    for tok in rest_tokens:
        if tok in BASH_INPLACE_FLAGS:
            return True
        # sed/perl combined flags like `-iEXT` or `-i.bak`
        if len(tok) >= 2 and tok[0] == "-" and "i" in tok[1:].split("=")[0] and not tok.startswith("--"):
            # Crude: any short-flag cluster containing 'i' counts.
            if any(c == "i" for c in tok[1:].lstrip("-")):
                return True
    return False


def _git_violation_target(
    tokens: list[str], cwd: str, forbidden: list[str]
) -> str | None:
    """If this is `git -C <forbidden> <mutating-subcmd>` or
    `git --git-dir=<forbidden>/.git`, return the forbidden worktree path.
    Otherwise None."""
    if not tokens or tokens[0] != "git":
        return None
    work_dir: str | None = None
    sub_idx: int | None = None
    j = 1
    while j < len(tokens):
        t = tokens[j]
        if t == "-C" and j + 1 < len(tokens):
            work_dir = _resolve_path(tokens[j + 1], cwd)
            j += 2
            continue
        if t.startswith("--git-dir="):
            d = _resolve_path(t.split("=", 1)[1], cwd)
            if d and d.endswith("/.git"):
                work_dir = d[:-5]
            j += 1
            continue
        if t.startswith("-"):
            j += 1
            continue
        sub_idx = j
        break
    if sub_idx is None or work_dir is None:
        return None
    subcmd = tokens[sub_idx]
    if subcmd not in GIT_MUTATING_SUBCOMMANDS:
        return None
    # `git worktree list` is read-only; only `add/remove/move/prune/repair` mutate.
    if subcmd == "worktree":
        if sub_idx + 1 >= len(tokens):
            return None
        if tokens[sub_idx + 1] in {"list", "lock", "unlock"}:
            return None
    # Resolve work_dir and check it's inside any forbidden worktree.
    for forb in forbidden:
        if path_inside(work_dir, forb):
            return work_dir
    return None


def extract_paths_from_bash(
    block: dict, cwd: str, forbidden: list[str]
) -> list[tuple[str, str]]:
    """Return [(realpath, "Bash:<verb>"), ...] for every candidate write target
    found in a Bash tool_use block.

    Two-pass per command segment:
      1. Regex sweep for redirection targets (`> X`, `>> X`).
      2. If the leading verb is a known write verb (or sed/perl with -i, or
         tee, or a foreign-git mutation), collect path-like positional args.
    """
    inp = block.get("input") or {}
    command = inp.get("command")
    if not isinstance(command, str) or not command.strip():
        return []

    out: list[tuple[str, str]] = []

    for segment in _segment_into_commands(command):
        # 1) Redirection sweep — works regardless of verb.
        for m in BASH_REDIRECT_RE.finditer(segment):
            target = m.group(1) or m.group(2) or m.group(3)
            resolved = _resolve_path(target, cwd)
            if resolved:
                out.append((resolved, "Bash:redirect"))

        # 2) Verb-driven sweep.
        tokens = _tokenize(segment)
        if not tokens:
            continue
        verb, rest = _leading_verb(tokens)
        if not verb:
            continue

        # tee / tee -a → all positional path-like args
        if verb == "tee":
            for tok in rest:
                if tok.startswith("-"):
                    continue
                resolved = _resolve_path(tok, cwd)
                if resolved:
                    out.append((resolved, "Bash:tee"))
            continue

        # In-place editors
        if verb in BASH_INPLACE_EDITORS:
            if not _has_inplace_flag(rest, verb):
                continue  # read-only invocation
            for tok in rest:
                if tok.startswith("-"):
                    continue
                if not _is_pathlike(tok):
                    continue
                resolved = _resolve_path(tok, cwd)
                if resolved:
                    out.append((resolved, f"Bash:{verb} -i"))
            continue

        # Plain write verbs
        if verb in BASH_WRITE_VERBS:
            for tok in rest:
                if tok.startswith("-"):
                    continue
                if not _is_pathlike(tok):
                    continue
                resolved = _resolve_path(tok, cwd)
                if resolved:
                    out.append((resolved, f"Bash:{verb}"))
            continue

        # Foreign git mutations
        if verb == "git":
            target = _git_violation_target(tokens, cwd, forbidden)
            if target:
                out.append((target, "Bash:git mutation"))
            continue

    # Dedupe while preserving first-seen tool label.
    seen: dict[str, str] = {}
    for path, label in out:
        seen.setdefault(path, label)
    return [(p, l) for p, l in seen.items()]


def extract_writes(
    tool_uses: list[dict], cwd: str, forbidden: list[str]
) -> list[tuple[str, str]]:
    """Top-level path collector: dispatch each tool_use to the right extractor."""
    writes: list[tuple[str, str]] = []
    for block in tool_uses:
        name = block.get("name", "")
        if name in WRITE_TOOLS:
            writes.extend(extract_paths_from_structured(block, cwd))
        elif name == BASH_TOOL:
            writes.extend(extract_paths_from_bash(block, cwd, forbidden))
    return writes


def path_inside(child: str, parent: str) -> bool:
    """True if child is parent or under parent (string-based, both realpath'd)."""
    if child == parent:
        return True
    sep = os.sep
    return child.startswith(parent + sep)


def classify_violations(
    writes: list[tuple[str, str]],
    worktree_root: str,
    forbidden_worktrees: list[str],
) -> list[tuple[str, str, str]]:
    """Return [(violating_path, tool_name, forbidden_worktree_path), ...]."""
    violations: list[tuple[str, str, str]] = []
    for path, tool in writes:
        if path_inside(path, worktree_root):
            continue
        for forb in forbidden_worktrees:
            if path_inside(path, forb):
                violations.append((path, tool, forb))
                break
    return violations


def user_intended(
    path: str, user_texts: list[str]
) -> bool:
    """True if any in-scope user message names this path or signals intent."""
    if not user_texts:
        return False
    basename = os.path.basename(path)
    for raw in user_texts:
        text = raw.lower()
        if path.lower() in text:
            return True
        for phrase in OVERRIDE_PHRASES:
            if phrase in text:
                return True
        if basename and basename.lower() in text:
            for verb in WRITE_VERBS:
                if verb in text:
                    return True
    return False


def filter_overrides(
    violations: list[tuple[str, str, str]], user_texts: list[str]
) -> list[tuple[str, str, str]]:
    return [v for v in violations if not user_intended(v[0], user_texts)]


def build_reason(
    violations: list[tuple[str, str, str]], worktree_root: str
) -> str:
    lines = [
        "worktree-guard: writes landed OUTSIDE this worktree.",
        f"  Current worktree: {worktree_root}",
        "",
        "Violations:",
    ]
    for path, tool, forb in violations:
        lines.append(f"  - {tool} → {path}")
        lines.append(f"      (lives in forbidden worktree: {forb})")
    lines.extend(
        [
            "",
            "These writes corrupted a working tree this session was meant to leave alone.",
            "Fix it before stopping:",
            f"  • If the change belongs in {worktree_root}: move/copy it there and revert the foreign write.",
            "  • Otherwise revert with:  git -C <forbidden-worktree> checkout -- <path>",
            "",
            "If the user explicitly asked for the foreign write, they can re-prompt naming the",
            "path or saying 'outside the worktree' / 'in the main repo' to override this guard.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        log(f"input parse failed: {e}")
        return 0

    if payload.get("stop_hook_active") is True:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    transcript_path = payload.get("transcript_path")
    if not transcript_path or not os.path.exists(transcript_path):
        log(f"no transcript at {transcript_path!r}; skipping")
        return 0

    try:
        worktree_root = git(cwd, "rev-parse", "--show-toplevel")
        if not worktree_root:
            return 0
        worktree_root = str(Path(worktree_root).resolve())

        all_worktrees = list_worktrees(cwd)
        forbidden = [p for p in all_worktrees if p != worktree_root]
        if not forbidden:
            return 0

        records = list(parse_transcript(transcript_path))
        if not records:
            return 0

        tool_uses, user_texts = collect_last_turn(records)
        if not tool_uses:
            return 0

        writes = extract_writes(tool_uses, cwd, forbidden)
        violations = classify_violations(writes, worktree_root, forbidden)
        if not violations:
            return 0

        violations = filter_overrides(violations, user_texts)
        if not violations:
            log(f"violations filtered by override heuristic: cwd={cwd}")
            return 0

        reason = build_reason(violations, worktree_root)
        out = {"decision": "block", "reason": reason}
        log(f"BLOCK cwd={cwd} violations={len(violations)}")
        print(json.dumps(out))
        return 0
    except Exception as e:
        log(f"unhandled exception: {e!r}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
