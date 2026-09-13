# ai-additions

Portable Claude Code behaviour additions — skills, hooks, and MCP servers that
change how Claude *works*, independent of any one machine.

**Status: 20 items added, none enabled.** See
[`SETUP-LIST.md`](SETUP-LIST.md) for what is approved, pending, and declined.

*Added* and *enabled* are separate states here. An addition is in the repo,
versioned, and registered where a marketplace entry applies — and installed
nowhere, switched on nowhere. Enabling is its own approval.

## Why this is separate from Standard Configs

[`Standard Configs`](../Standard%20Configs/) bootstraps *this Mac* — Homebrew,
launchd agents, macOS defaults, install runbooks. Its unit of work is "make this
machine match the snapshot."

This repo's unit of work is a behaviour: a rule Claude follows, a hook that makes
it hold, a skill it invokes. Those are portable — they are the same on a second
machine, in a cloud session, or under a different account profile — and they were
tangled into a machine-bootstrap repo only because that repo existed first.

Standard Configs will consume this repo through a thin `external/ai-additions/`
stub, the same pattern it already uses for side repos it does not own.

## Shape

A Claude Code plugin marketplace. Each addition is a plugin under `plugins/`,
registered in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json):

```
ai-additions/
├── .claude-plugin/marketplace.json   ← the registry
├── SETUP-LIST.md                     ← the approval ledger; read this first
├── plugins/                          ← 8 plugins: skills, hooks, commands
├── rules/                            ← 6 prose rule documents, verbatim copies
└── referenced/                       ← 6 items installed from elsewhere
```

Marketplace rather than a loose file collection because `claude plugin
install` / `enable` / `disable` already models the lifecycle these things need —
including installing something and deliberately leaving it off.

Additions that already live in their own repos are **referenced**, not absorbed:
they keep their own history, issues, and release cadence, and this marketplace
names them as required marketplaces instead of vendoring a copy that goes stale.

## The one rule

Nothing enters this repo without Zach explicitly approving it by name. Discussion
is not approval. See [`SETUP-LIST.md`](SETUP-LIST.md) for the full statement — it
governs, and this paragraph is only a pointer to it.
