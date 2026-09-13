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
approval, and for several it is more than one step (see the notes).

### Plugins — `plugins/`, registered in `marketplace.json`

| Item | Approved | Wording | Enabled |
|---|---|---|---|
| `worktree-guard` | 2026-09-13 | "as well as ... worktree-guard" | No |
| `github-utilities` | 2026-09-13 | "oh add github utilities" | No |
| `datetime-inject` | 2026-09-13 | "pending list so far is approved" | No |
| `logic-rendering` | 2026-09-13 | "pending list so far is approved" | No |
| `skill-perf` | 2026-09-13 | "pending list so far is approved" | No |
| `extras` | 2026-09-13 | "pending list so far is approved" | No |
| `stack-profiles` | 2026-09-13 | "pending list so far is approved" | No |
| `repo-scaffold` | 2026-09-13 | "pending list so far is approved" | No |

### Rules — `rules/`, copied verbatim, deployed nowhere

| Item | Approved | Wording | Enabled |
|---|---|---|---|
| `CRAFT_VS_YAGNI` | 2026-09-13 | "CRAFT_VS_YAGNI - add, but keep to side" | No |
| `PLAN_AUDIT` | 2026-09-13 | "as well as plan audit" | No |
| `CEILINGS` | 2026-09-13 | "as well as ... ceilings" | No |
| `GITHUB` | 2026-09-13 | "as well as ... github" | No |
| `SKILL_AUTHORING` | 2026-09-13 | "pending list so far is approved" | No |
| `NEW_REPO_BOOTSTRAP` | 2026-09-13 | "pending list so far is approved" | No |

### Referenced — `referenced/`, pointers only, nothing cloned or installed

| Item | Approved | Wording | Enabled |
|---|---|---|---|
| `asking-protocol` | 2026-09-13 | "pending list so far is approved" | No — MCP to stay **disabled** |
| `reference-points` | 2026-09-13 | "pending list so far is approved" | No |
| `claude-statusline` | 2026-09-13 | "also add the entry for the statusline for claude code please" | No |
| `atuin` | 2026-09-13 | "add atuin to the new set" | No |
| `security-guidance@claude-plugins-official` | 2026-09-13 | "let's add security-guidance@claude-plugins-official and superpowers@" | No |
| `superpowers@claude-plugins-official` | 2026-09-13 | same | No |

### Open — approved, shape unresolved

| Item | Approved | Wording | Blocker |
|---|---|---|---|
| autoupdates | 2026-09-13 | "and enable autoupdates" | Which updater, and it is an *enable* action — see below |

## Notes on the above

- **`superpowers@` was written with the marketplace blank.** Taken as
  `claude-plugins-official` — already registered here, and the marketplace named
  on the line immediately before it. Upstream documents two other routes; see
  [`referenced/upstream-plugins.md`](referenced/upstream-plugins.md).
- **autoupdates is the one thing that contradicts "not enabled".** Everything
  else was added and left off; this asks to switch something on, and it is not
  clear what: Claude Code's own CLI auto-updater, or `claude plugin marketplace
  update` on a schedule for the plugins above. Neither `marketplace add` nor
  `plugin install` exposes an autoupdate flag. Recorded, not acted on.
- **`skill-perf` and its judge are split across two plugins.** The judge is the
  `skill-perf-judge` skill inside `extras`. Enabling either alone gives a working
  half — capture with nothing scoring it, or a judge with nothing to read.
- **Three plugins need a second step beyond installing.** `skill-perf` needs its
  database created and `schema.sql` deployed to `~/.claude/skill-perf/`;
  `stack-profiles` needs its profiles deployed to `~/.claude/stacks/`;
  `github-utilities` and `repo-scaffold` each ship a CLI that a plugin cannot put
  on `PATH`. Each plugin README says so.
- **`GITHUB.md` is the only rule file not byte-identical** — two links repaired
  to point at `plugins/github-utilities/`. Paths only, no prose.
- **`security-guidance` now has two owners.** It is also in Standard Configs'
  `external/claude-plugins/templates/plugin-set.txt`. Deduplicate before either
  is enabled.
- **Two items look misfiled and are recorded where they were approved, not where
  they may belong.** `atuin` is a Homebrew CLI with no Claude surface at all;
  `claude-statusline` is Rust plus two binaries plus a LaunchAgent. Both read as
  machine configuration, which is Standard Configs' remit.

## Pending — discussed, NOT approved

| Item | What it is | Where it lives today |
|---|---|---|
| *(none)* | | |

## Declined

| Item | Reason |
|---|---|
| *(none yet)* | |
