# referenced/

Additions installed from somewhere else — another repo, a package manager, or a
marketplace this repo does not own. One pointer per item: coordinates, what it
is, how it installs. Never a vendored copy.

A vendored copy is a second source of truth that goes stale silently, and reads
exactly like a current one. See [`../CLAUDE.md`](../CLAUDE.md).

Nothing here is installed or enabled by being listed. See
[`../SETUP-LIST.md`](../SETUP-LIST.md) for approval state.

| Item | Source | Kind | Approved |
|---|---|---|---|
| [`asking-protocol`](asking-protocol.md) | [`locriani/asking-protocol`](https://github.com/locriani/asking-protocol) | Plugin (private repo) — MCP to stay disabled | 2026-09-13 |
| [`reference-points`](reference-points.md) | [`locriani/reference-points`](https://github.com/locriani/reference-points) | Plugin (public repo) | 2026-09-13 |
| [`claude-statusline`](claude-statusline.md) | [`locriani/claude-statusline`](https://github.com/locriani/claude-statusline) | Rust binaries + LaunchAgent | 2026-09-13 |
| [`atuin`](atuin.md) | [`atuinsh/atuin`](https://github.com/atuinsh/atuin) | Homebrew CLI | 2026-09-13 |
| [`upstream-plugins`](upstream-plugins.md) | `claude-plugins-official` | `security-guidance`, `superpowers` | 2026-09-13 |
| [`mattpocock-skills`](mattpocock-skills.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills) | Skills — `to-spec`, `to-tickets` | 2026-09-15 |
| [`chief-of-stuff`](chief-of-stuff.md) | [`locriani/chief-of-stuff`](https://github.com/locriani/chief-of-stuff) | Plugin (private repo) — one main-session agent | 2026-09-16 |
| [`frank-lloyd-aight`](frank-lloyd-aight.md) | [`locriani/frank-lloyd-aight`](https://github.com/locriani/frank-lloyd-aight) | Plugin (public repo) — one main-session architecture agent, Frank Lloyd AIght | 2026-09-17 |
| [`auditor`](auditor.md) | [`locriani/auditor`](https://github.com/locriani/auditor) | Plugin — the `auditor` agent and the `codebase-audit` skill; name provisional | 2026-09-15, extracted from `plugins/` 2026-09-19 |
| [`yoke`](yoke.md) | [`yokeloop/yoke`](https://github.com/yokeloop/yoke) | Plugin — 14 commands incl. `/prd`, `/issues` | 2026-09-15 |
| [`terminalskills`](terminalskills.md) | [`TerminalSkills/skills`](https://github.com/TerminalSkills/skills) | Skill — `prd-to-issues` | 2026-09-15 |
