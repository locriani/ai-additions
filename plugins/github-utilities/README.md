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

Installing is the whole install. The Stop hook is wired by `hooks/hooks.json`,
and `bin/gh-issue-rel` sits at the default `bin/` location, which Claude Code
adds to the Bash tool's `PATH` while the plugin is enabled — so the bare command
the hook's guidance and `GITHUB.md` both name resolves without linking anything.

Earlier revisions of this file claimed a plugin cannot put a binary on `PATH` and
prescribed `ln -s "$PWD/bin/gh-issue-rel" ~/.local/bin/`. That was wrong, and the
symlink is worse than unnecessary: it outlives `plugin disable`, leaving a bare
command still reachable and pointing into a checkout after the plugin is off.

## Provenance

Extracted from `Standard Configs/claude-plugins/github-utilities/` at `d36d794`.
Both files are byte-identical to their source. Two things moved around them: the
hook's registration, from a `$HOME/.claude/hooks/` path in `settings.json` to
`${CLAUDE_PLUGIN_ROOT}` in `hooks/hooks.json`; and the wrapper's filename, from
`gh-issue-rel.sh` to `bin/gh-issue-rel` — the name it must carry on `PATH`, which
in Standard Configs was applied at deploy time by `apply.py`.
