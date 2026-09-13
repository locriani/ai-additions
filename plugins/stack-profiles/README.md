# stack-profiles

Per-stack rule addenda plus the SessionStart hook that picks the right one.

Eleven profiles: Swift/Apple, bash scripts, Python/uv, Node/TypeScript,
Postgres/SQL, Rust, Go, React/Vite, Rails, Terraform, Kubernetes.

## Why a detector

Eleven profiles loaded unconditionally is eleven profiles' worth of context to
say something about one repo. `stack-detect.py` runs at session start, works out
what the repo is, and loads only the matching profile — so the cost is one
profile, not the set.

## Enabling takes more than installing

`stack-detect.py` reads profiles from `~/.claude/stacks/` (or
`$CLAUDE_CONFIG_DIR/stacks/`), not from the plugin directory. Installing the
plugin wires the hook; the profiles in `profiles/` still have to be deployed to
`~/.claude/stacks/` or the detector finds nothing to load.

The script is byte-identical to source and has not been rewritten to read from
`${CLAUDE_PLUGIN_ROOT}` — that would change behaviour, and these were approved
as-is.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere, and no
profiles have been deployed.

## Provenance

From `Standard Configs/claude-core/stack-profiles/templates/` at `d36d794`.
Hook and all eleven profiles byte-identical.
