# github-utilities

The runtime enforcement for [`../../rules/GITHUB.md`](../../rules/GITHUB.md).
That file states the rule; this makes it hold.

## Two parts

**`hooks/github-api-stop-hook.py`** — Stop hook. Scans the trailing assistant
turn for GitHub web-API attempts that `gh`'s high-level subcommands could have
covered, and blocks turn-end with remediation guidance:

- `curl` / `wget` / `http` / `httpie` against `api.github.com` — raw REST bypass
- `gh api …` — forces the high-level subcommands instead
- `WebFetch` of `github.com`

The escape hatch is an explicit `WEB-API-FALLBACK-JUSTIFIED` line in the final
response. See §5 of `GITHUB.md`.

**`bin/gh-issue-rel`** — GitHub exposes sub-issues and blocked-by dependencies
natively over REST, but `gh`'s subcommands don't cover them, and `GITHUB.md`
forbids raw `gh api`. This wrapper is therefore *the* sanctioned surface for
those two relationship types. It touches nothing locally, and never guesses the
repo: `-R owner/name`, else the caller's git repo, else exit 2 naming `-R` as the
fix.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere.

Note that enabling has **two** steps, not one — installing the plugin wires the
Stop hook, but `gh-issue-rel` has to reach `PATH` separately (the hook's guidance
and the rule both name the bare command). Something like:

```sh
ln -s "$PWD/bin/gh-issue-rel" ~/.local/bin/gh-issue-rel
```

A plugin cannot put a binary on `PATH`, so a plugin install alone leaves the
wrapper unreachable while the hook is busy telling you to use it — worth knowing
before enabling either half.

## Provenance

Extracted from `Standard Configs/claude-plugins/github-utilities/` at `d36d794`.
Both files are byte-identical to their source. Two things moved around them: the
hook's registration, from a `$HOME/.claude/hooks/` path in `settings.json` to
`${CLAUDE_PLUGIN_ROOT}` in `hooks/hooks.json`; and the wrapper's filename, from
`gh-issue-rel.sh` to `bin/gh-issue-rel` — the name it must carry on `PATH`, which
in Standard Configs was applied at deploy time by `apply.py`.
