# Setup list

The authoritative record of what this repo installs, and what it does not.

## The rule

**Nothing enters this repo without explicit approval from Zach.**

Approval means a specific statement — *"X is approved for addition"* or similar
wording that names the item and grants it. It is **not** implied by:

- discussing an item, however favourably
- listing it as something wanted, or asking for it to be scoped
- an item being obviously useful, already written, or already working elsewhere
- a previous approval of a related or adjacent item

An item that has been discussed but not stated is **Pending**, and Pending items
are not built, not copied in, and not registered in `marketplace.json`.

This file is the ledger. Move a row between tables only when the approval phrase
has actually been given, and record the wording that granted it.

## Approved

| Item | Approved on | Wording | Status |
|---|---|---|---|
| *(none yet)* | | | |

## Pending — discussed, NOT approved

| Item | What it is | Where it lives today |
|---|---|---|
| datetime-inject | UserPromptSubmit hook injecting per-turn local date+time | `Standard Configs/claude-plugins/datetime-inject/` |
| asking-protocol (MCP disabled) | PreToolUse + Stop hooks, `asking` MCP, `asking` skill | `locriani/asking-protocol` (own repo, private) |
| logic-rendering | Skill: render logic as boolean/modal checksums | `Standard Configs/claude-md/templates/global/LOGIC_RENDERING.md` |
| reference-points | Citation grammar + section numbering (was called "section rendering") | `locriani/reference-points` (own repo) |
| skill-perf | Skill-invocation ledger + LLM judge | `Standard Configs/claude-plugins/skill-perf/` + `extras/skills/skill-perf-judge/` |

## Declined

| Item | Reason |
|---|---|
| *(none yet)* | |
