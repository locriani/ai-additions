# repo-scaffold

One-shot per-stack scaffolding for a new repo: `CLAUDE.md`, `DEV_TOOLS.md`,
`README`, `.gitignore`, the stack's directory skeleton, `git init`, and
optionally `gh repo create`.

Two entry points, one implementation:

- `commands/scaffold-repo.md` — the `/scaffold-repo` slash command.
- `bin/scaffold-repo` — a CLI shim.

Both call `scaffold-new-repo.sh`. The per-stack content lives in `dirs/`,
`gitignore/`, `readme/` and `next-steps/`.

When `--stack` or the target directory is missing, it asks in plain text with
numbered options rather than guessing.

## Two entry points, one install

Installing the plugin registers the `/scaffold-repo` slash command *and* makes
`scaffold-repo` a bare command: `bin/` is the default executables location, which
Claude Code adds to the Bash tool's `PATH` while the plugin is enabled.

Earlier revisions claimed a plugin cannot put a binary on `PATH` and prescribed a
`ln -s` into `~/.local/bin`. That was wrong; nothing needs linking.

## Known defect — the shim does not run as a plugin

`PATH` is not this plugin's problem. Both entry points still fail on a clean
install, because both point into Standard Configs' deploy layout rather than at
anything the plugin ships:

```
bin/scaffold-repo          execs $HOME/.local/share/repo-scaffold/scaffold-new-repo.sh
commands/scaffold-repo.md  names ~/.local/bin/scaffold-repo
plugin ships              ./scaffold-new-repo.sh          <- the real script, unreferenced
```

`apply.py` created both of those paths at deploy time in Standard Configs. A
plugin install creates neither, so the shim execs a missing file and the slash
command names a missing command — while the script they both want sits in the
plugin root, reachable as `${CLAUDE_PLUGIN_ROOT}/scaffold-new-repo.sh`.

This is the same class of error as a `SKILL.md` hard-coding `~/.claude/skills/`:
a path that exists on the authoring machine and nowhere after install. Recorded,
not fixed — converting the shim and the command to `${CLAUDE_PLUGIN_ROOT}` is a
behaviour change, and this plugin is not enabled.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere.

## Provenance

From `Standard Configs/claude-core/repo-scaffold/templates/` at `d36d794`, all
files byte-identical.
