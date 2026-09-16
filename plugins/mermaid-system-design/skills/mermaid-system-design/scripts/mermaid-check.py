#!/usr/bin/env python3
"""Render every Mermaid diagram in a file with mmdc and report what fails.

    mermaid-check.py FILE [FILE ...] [--keep] [--outdir DIR]

FILE is Markdown (every ```mermaid fenced block is checked; ```text and every
other fence is ignored) or a .mmd file (the whole file is one diagram).

Exit codes: 0 all diagrams render · 1 at least one failed · 2 mmdc is missing.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FENCE = re.compile(r"^(?P<indent>[ \t]*)(?P<ticks>`{3,}|~{3,})[ \t]*(?P<info>[^\s`~]*)")
PARSE_LINE = re.compile(r"^(?P<head>.*?\bon line )(?P<num>\d+)(?P<tail>.*)$")
STACK_FRAME = re.compile(r"^\s*(?:at\s.*|[\w$.#<>]+\s*\(.*:\d+:\d+\))\s*$")

INSTALL_HINT = """mmdc (mermaid-cli) is not on PATH. Install it:

    brew install node
    npm install -g @mermaid-js/mermaid-cli

The first render downloads Puppeteer's Chromium, so allow a minute for it."""


def extract_blocks(text: str) -> list[tuple[int, str]]:
    """Return (first_content_line, code) for each ```mermaid block.

    Line numbers are 1-indexed against `text`, so they address the file the
    caller is editing. A block whose closing fence is missing is dropped.
    """
    blocks: list[tuple[int, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        opening = FENCE.match(lines[i])
        if not opening:
            i += 1
            continue
        marker = opening.group("ticks")
        char, width = marker[0], len(marker)
        wanted = opening.group("info").lower() == "mermaid"
        start = i + 1
        body: list[str] = []
        i += 1
        closed = False
        while i < len(lines):
            closing = FENCE.match(lines[i])
            if (
                closing
                and closing.group("info") == ""
                and closing.group("ticks")[0] == char
                and len(closing.group("ticks")) >= width
            ):
                closed = True
                i += 1
                break
            body.append(lines[i])
            i += 1
        if wanted and closed and any(line.strip() for line in body):
            blocks.append((start + 1, "\n".join(body) + "\n"))
    return blocks


def absolutize(message: str, first_content_line: int) -> str:
    """Rewrite Mermaid's block-relative 'on line N' to a line in the source file."""
    out = []
    for line in message.splitlines():
        m = PARSE_LINE.match(line)
        if m:
            absolute = first_content_line + int(m.group("num")) - 1
            line = f"{m.group('head')}{absolute}{m.group('tail')}"
        out.append(line)
    return "\n".join(out)


def trim_trace(message: str) -> str:
    """Drop the JavaScript stack frames mmdc appends after the real error."""
    kept: list[str] = []
    for line in message.splitlines():
        if STACK_FRAME.match(line):
            break
        kept.append(line)
    return "\n".join(kept).rstrip() or message.strip()


def render(code: str, out_svg: Path) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as fh:
        fh.write(code)
        src = Path(fh.name)
    try:
        proc = subprocess.run(
            ["mmdc", "--quiet", "--input", str(src), "--output", str(out_svg)],
            capture_output=True,
            text=True,
        )
    finally:
        src.unlink(missing_ok=True)
    if proc.returncode == 0 and out_svg.exists():
        return True, ""
    return False, (proc.stderr or proc.stdout or f"mmdc exited {proc.returncode}").strip()


def check_file(path: Path, outdir: Path, keep: bool) -> tuple[int, int]:
    text = path.read_text()
    if path.suffix == ".mmd":
        blocks = [(1, text)]
    else:
        blocks = extract_blocks(text)

    if not blocks:
        print(f"{path}: no mermaid blocks")
        return 0, 0

    failures = 0
    for n, (line, code) in enumerate(blocks, start=1):
        svg = outdir / f"{path.stem}-{n}.svg"
        ok, err = render(code, svg)
        where = f"{path}:{line}"
        if ok:
            print(f"ok    {where}  (diagram {n} of {len(blocks)})")
            if not keep:
                svg.unlink(missing_ok=True)
        else:
            failures += 1
            print(f"FAIL  {where}  (diagram {n} of {len(blocks)})")
            for out in absolutize(trim_trace(err), line).splitlines():
                print(f"      {out}")
    return failures, len(blocks)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--keep", action="store_true", help="keep the rendered SVGs and print where they are")
    ap.add_argument("--outdir", type=Path, help="directory for rendered SVGs (default: a temp dir)")
    args = ap.parse_args(argv)

    if shutil.which("mmdc") is None:
        print(INSTALL_HINT, file=sys.stderr)
        return 2

    missing = [f for f in args.files if not f.is_file()]
    if missing:
        for f in missing:
            print(f"no such file: {f}", file=sys.stderr)
        return 2

    keep = args.keep or args.outdir is not None
    tmp = None
    if args.outdir is not None:
        outdir = args.outdir
        outdir.mkdir(parents=True, exist_ok=True)
    elif keep:
        outdir = Path(tempfile.mkdtemp(prefix="mermaid-check-"))
    else:
        tmp = tempfile.TemporaryDirectory()
        outdir = Path(tmp.name)

    try:
        results = [check_file(f, outdir, keep) for f in args.files]
        failures = sum(f for f, _ in results)
        checked = sum(n for _, n in results)
        if keep and checked:
            print(f"\nSVGs in {outdir}")
        if failures:
            print(f"\n{failures} of {checked} diagram(s) failed to render")
            return 1
        if not checked:
            print("\nNothing to check — no mermaid blocks found.")
            return 0
        print(f"\nAll {checked} diagram(s) render. Syntax only — now look at them.")
        return 0
    finally:
        if tmp is not None:
            tmp.cleanup()


if __name__ == "__main__":
    sys.exit(main())
