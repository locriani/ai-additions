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

"Keep to side" was settled on 2026-09-13: **added to this repo, not enabled for
Claude Code.** Present, versioned, registered where a marketplace entry applies —
but installed nowhere and switched on nowhere. Enabling each is a separate
approval.

| Item | Approved | Wording | Where it landed | Enabled |
|---|---|---|---|---|
| `CRAFT_VS_YAGNI` | 2026-09-13 | "CRAFT_VS_YAGNI - add, but keep to side" | `rules/CRAFT_VS_YAGNI.md` | No |
| `PLAN_AUDIT` | 2026-09-13 | "as well as plan audit" | `rules/PLAN_AUDIT.md` | No |
| `CEILINGS` | 2026-09-13 | "as well as ... ceilings" | `rules/CEILINGS.md` | No |
| `worktree-guard` | 2026-09-13 | "as well as ... worktree-guard" | `plugins/worktree-guard/` | No |
| `github` | 2026-09-13 | "as well as ... github" | `rules/GITHUB.md` | No |
| `claude-statusline` | 2026-09-13 | "also add the entry for the statusline for claude code please" | `referenced/claude-statusline.md` | No |

### Scope notes on the above

- **`github` is the rule file only.** `GITHUB.md` was named; `github-utilities`
  (the Stop hook that enforces it, plus the `gh-issue-rel` CLI) was not. It is
  proposed as a bundle in **Pending** and needs its own approval. Consequence:
  `GITHUB.md`'s link to its runtime enforcement dangles here, deliberately —
  see [`rules/README.md`](rules/README.md).
- **The four rule files are byte-identical copies**, not skills. None carries
  frontmatter, so none fires on its own. Converting them is design work on
  content approved as-is, and is not assumed.
- **`claude-statusline` is referenced, not vendored** — it has its own repo.
  Flagged in its entry: it is Rust, macOS-only, and installs two binaries plus a
  LaunchAgent, which is closer to machine configuration than portable behaviour.
  Standard Configs may be its more natural owner.

## Pending — discussed, NOT approved

| Item | What it is | Where it lives today |
|---|---|---|
| datetime-inject | UserPromptSubmit hook injecting per-turn local date+time | `Standard Configs/claude-plugins/datetime-inject/` |
| asking-protocol (MCP disabled) | PreToolUse + Stop hooks, `asking` MCP, `asking` skill | `locriani/asking-protocol` (own repo, private) |
| logic-rendering | Skill: render logic as boolean/modal checksums | `Standard Configs/claude-md/templates/global/LOGIC_RENDERING.md` |
| reference-points | Citation grammar + section numbering (was called "section rendering") | `locriani/reference-points` (own repo) |
| skill-perf | Skill-invocation ledger + LLM judge | `Standard Configs/claude-plugins/skill-perf/` + `extras/skills/skill-perf-judge/` |
| github-utilities | Stop hook enforcing `GITHUB.md` + `gh-issue-rel` CLI. `GITHUB.md` is already approved and links to it | `Standard Configs/claude-plugins/github-utilities/` |
| SKILL_AUTHORING | Rule file: how to author skills | `Standard Configs/claude-md/templates/global/SKILL_AUTHORING.md` |
| stack-profiles | 11 per-stack addenda + a SessionStart detector | `Standard Configs/claude-core/stack-profiles/` |
| repo-scaffold + NEW_REPO_BOOTSTRAP | `/scaffold-repo` slash command + CLI, and its rule file | `Standard Configs/claude-core/repo-scaffold/` + snapshot |
| extras | 5 skills: code-review, time-estimation, defect-density, dev-velocity, skill-perf-judge | `Standard Configs/claude-plugins/extras/` |

## Declined

| Item | Reason |
|---|---|
| *(none yet)* | |
