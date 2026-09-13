# worktree-guard

Stop hook. When the session's CWD is inside a git worktree, a write that targets
a path inside **another** worktree of the same repo — the main checkout or a
sibling — is a violation: it corrupts a working tree the agent was not supposed
to touch and defeats the isolation the worktree was created to provide.

Two write surfaces are covered in the last assistant turn:

- **Structured tools** — `Write`, `Edit`, `MultiEdit`, `NotebookEdit`, where the
  path is in the tool input.
- **Bash** — redirections (`>`, `>>`, `2>`, `&>`, `tee [-a]`) and write verbs
  (`cp`, `mv`, `rm`, `mkdir`, `touch`, `ln`, `chmod`, `sed -i`, …). Read-only
  verbs are not flagged even when the command names a forbidden path.

There is an explicit-intent override; see the hook's own docstring.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere. Enabling is a
separate decision — see [`../../SETUP-LIST.md`](../../SETUP-LIST.md).

## Provenance

Extracted verbatim from `Standard Configs/claude-plugins/worktree-guard/` at
`d36d794`. The hook script is unchanged; only its invocation moved, from a
`$HOME/.claude/hooks/` path in `settings.json` to `${CLAUDE_PLUGIN_ROOT}` in
`hooks/hooks.json`, so the plugin carries its own registration.
