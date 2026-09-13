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

## Enabling takes more than installing

Installing the plugin registers the slash command. `bin/scaffold-repo` is a CLI
and a plugin cannot put a binary on `PATH`, so the shim needs linking separately
if you want the non-slash entry point:

```sh
ln -s "$PWD/bin/scaffold-repo" ~/.local/bin/scaffold-repo
```

## Status

**Not enabled.** Registered in this marketplace, installed nowhere.

## Provenance

From `Standard Configs/claude-core/repo-scaffold/templates/` at `d36d794`, all
files byte-identical.
