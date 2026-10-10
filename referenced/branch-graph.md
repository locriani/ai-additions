# branch-graph

**Upstream:** [`locriani/branch-graph`](https://github.com/locriani/branch-graph) (public) — split out
of this repo 2026-10-10; CI green at head `739cd59` (116 tests).
**Status:** approved and enabled 2026-09-23 on *"branch-graph is approved for addition and enabling"*
(Zach, 18:42) — see `SETUP-LIST.md`. Installed from this repo's local marketplace the same evening on
*"merged, install it"* (0.1.0, user scope), then updated through 0.5.0 on *"commit / merge /
install"*; the ledger row records each step. Extracted 2026-10-10 from
[`locriani/ai-additions`](https://github.com/locriani/ai-additions) at `a01d7eb`, history carried
with the extraction and authorship preserved; the row moved from the Plugins table to Referenced
with wording unchanged. Plugin id and version are unchanged (0.6.0 at extraction).

A Claude Code plugin and CLI that draws a branch's diff as a before/after module import diagram —
modules and import edges added, removed and changed, each linked to the hunks and `file:line` that
created them — and flags drift where a new import violates an `import-rules` block. Languages plug
in as modules under `lib/branch_graph/languages/`; Python, PHP and Swift ship. Optional `lizard` and
`radon` add complexity, duplication and coverage metrics as branch deltas. Its SKILL.md render-check
step pairs with the `mermaid-system-design` plugin's checker, with a documented fallback when that
plugin is not installed.

## Install

```sh
claude plugin marketplace add locriani/branch-graph
claude plugin install branch-graph@branch-graph
```

The installed copy is a version-stamped snapshot under `~/.claude/plugins/cache/`; after a new
release, `claude plugin marketplace update branch-graph` and reinstall.
