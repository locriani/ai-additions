# Upstream marketplace plugins

Plugins from marketplaces this repo does not own. Nothing to vendor and nothing
to clone — they are named as `<plugin>@<marketplace>` and installed from there.

**Status: referenced, not installed.** None of the commands below has been run.

| Plugin | Marketplace | Approved |
|---|---|---|
| `security-guidance` | `claude-plugins-official` | 2026-09-13 |
| `superpowers` | `claude-plugins-official` | 2026-09-13 |

## security-guidance

```sh
claude plugin install security-guidance@claude-plugins-official
```

From `anthropics/claude-plugins-official`, already a registered marketplace on
this machine. Also listed in `Standard Configs`'
`external/claude-plugins/templates/plugin-set.txt`, so there are two owners for
it now — see [`../SETUP-LIST.md`](../SETUP-LIST.md).

## superpowers

```sh
claude plugin install superpowers@claude-plugins-official
```

[`obra/superpowers`](https://github.com/obra/superpowers) — "an agentic skills
framework & software development methodology", v6.3.0. TDD, debugging,
collaboration patterns.

**On the marketplace choice.** The approval read `superpowers@` with the
marketplace left blank. Upstream documents three routes, and this takes the one
that needs no new marketplace registration:

| Route | Note |
|---|---|
| `superpowers@claude-plugins-official` | **Chosen.** Marketplace already registered; same one as `security-guidance` on the line above it. |
| `superpowers@superpowers-marketplace` | Requires `claude plugin marketplace add obra/superpowers-marketplace`. |
| `superpowers@superpowers-dev` | The manifest in `obra/superpowers` itself — a *development* marketplace by its own description. |

Already load-bearing in the frame, which cites `superpowers:test-driven-development`
and `superpowers:systematic-debugging` by name — so the skills are referenced by
`~/.claude/CLAUDE.md` today whether or not the plugin is installed.
