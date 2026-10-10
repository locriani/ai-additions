# mermaid-system-design

**Upstream:**
[`locriani/mermaid-system-design`](https://github.com/locriani/mermaid-system-design) (public) —
split out of this repo 2026-10-10; CI green at head `ae68949` (18 tests).
**Status:** approved and enabled 2026-09-15 on *"add / register in ai-additions"* — given while the
skill was already loaded and working as a personal skill, so registering it without enabling it
would have removed a working skill, and it went in switched on. See `SETUP-LIST.md`. Extracted
2026-10-10 from [`locriani/ai-additions`](https://github.com/locriani/ai-additions) at `a01d7eb`,
history carried with the extraction; the row moved from the Plugins table to Referenced with
wording unchanged. Plugin id and version are unchanged (1.1.0 at extraction).

A skill for drawing system architectures in Mermaid: fix the shape (actor, service, store, log,
decision, boundary) and the edge vocabulary before drawing, because a diagram asserts through shape
before prose speaks. Ships `mermaid-check.py`, which renders every diagram in a file with `mmdc`
and fails on any that do not render — a diagram that did not render is not a diagram. `branch-graph`'s
render-check step pairs with this checker.

## Install

```sh
claude plugin marketplace add locriani/mermaid-system-design
claude plugin install mermaid-system-design@mermaid-system-design
```

The installed copy is a version-stamped snapshot under `~/.claude/plugins/cache/`; after a new
release, `claude plugin marketplace update mermaid-system-design` and reinstall.
