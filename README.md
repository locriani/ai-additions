# ai-additions

The governance home for Zach Gardner's Claude Code behaviour additions: the
approval ledger, the shared rules, and the plugins that still live here.

This began as a single plugin marketplace. The plugins that wanted their own
identity now have it — on 2026-10-10, five of them were extracted at `a01d7eb`
into their own public repositories, each its own Claude Code marketplace. What
stays here is the part that governs the family:

- [`SETUP-LIST.md`](SETUP-LIST.md) — the approval ledger. Read this first.
- [`rules/`](rules/) — six prose rule documents, verbatim copies from Standard
  Configs.
- [`referenced/`](referenced/) — one pointer per addition that lives elsewhere.
  Never a vendored copy.
- [`plugins/`](plugins/) — the seven additions that remain local.
- [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) —
  registers those seven.

## The one rule

Nothing enters this repo without Zach explicitly approving it by name.
Discussion is not approval. See [`SETUP-LIST.md`](SETUP-LIST.md) for the full
statement — it governs, and this paragraph is only a pointer to it.

## Installing

The extracted plugins install from their own marketplaces, one `marketplace
add` per repo:

```sh
claude plugin marketplace add locriani/<name>
claude plugin install <name>@<name>
```

The seven local plugins install from this marketplace as before:

```sh
claude plugin marketplace add locriani/ai-additions
claude plugin install <name>@ai-additions
```

Updates: `claude plugin marketplace update <marketplace>` then reinstall.

## The catalog

Extracted 2026-10-10 — public repos, each its own marketplace. Each plugin's
approval story lives in its pointer under [`referenced/`](referenced/):

| Plugin | Repo |
|---|---|
| `branch-graph` | [`locriani/branch-graph`](https://github.com/locriani/branch-graph) |
| `bug-hunt` | [`locriani/bug-hunt`](https://github.com/locriani/bug-hunt) |
| `datetime-inject` | [`locriani/datetime-inject`](https://github.com/locriani/datetime-inject) |
| `mermaid-system-design` | [`locriani/mermaid-system-design`](https://github.com/locriani/mermaid-system-design) |
| `stack-profiles` | [`locriani/stack-profiles`](https://github.com/locriani/stack-profiles) |

Still local — registered in this repo's marketplace, source under
[`plugins/`](plugins/):

| Plugin | What it is |
|---|---|
| [`extras`](plugins/extras/) | Five skills: code-review, time-estimation, defect-density, dev-velocity, skill-perf-judge. |
| [`github-utilities`](plugins/github-utilities/) | Enforces [`rules/GITHUB.md`](rules/GITHUB.md): `gh-issue` files issues from the repo's own templates with native relationships; a PreToolUse guard and a Stop hook hold `gh` to the same rules. |
| [`logic-rendering`](plugins/logic-rendering/) | Renders logic — conditionals, implications, multi-premise reasoning — as boolean/modal notation alongside short prose. |
| [`prd-design`](plugins/prd-design/) | Interviews before writing a PRD, then decomposes into ordered vertical slices led by a tracer bullet. |
| [`repo-scaffold`](plugins/repo-scaffold/) | One-shot per-stack new-repo scaffolding (see the ledger notes on its plugin deployment). |
| [`skill-perf`](plugins/skill-perf/) | Stop-hook SQLite ledger of skill-invocation cost, plus a judge reminder. |
| [`worktree-guard`](plugins/worktree-guard/) | Stop hook blocking writes that cross into another worktree of the same repo. |

## Why this is separate from Standard Configs

Standard Configs bootstraps *this Mac* — Homebrew, launchd agents, macOS
defaults, install runbooks. Its unit of work is "make this machine match the
snapshot."

This repo's unit of work is a behaviour: a rule Claude follows, a hook that
makes it hold, a skill it invokes. Those are portable — they are the same on a
second machine, in a cloud session, or under a different account profile.
Standard Configs consumes this repo through a thin `external/ai-additions/`
stub, the same pattern it already uses for side repos it does not own.
