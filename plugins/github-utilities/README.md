# github-utilities

The runtime enforcement for [`../../rules/GITHUB.md`](../../rules/GITHUB.md). That file states the rule; this makes it hold.

## Three parts

**`bin/gh-issue`** — files an issue from the repo's own template, or refuses. The rules live in `lib/issue_rules.py`: no issue cited in prose (link it with a native relationship), and the body is a filled template whose field types set the caps.

- `gh-issue templates [-R owner/name]` — each template's fields, types, and caps.
- `gh-issue new [-R owner/name] --template KEY --title T --field id=value [--field id=@file] [--parent N] [--blocked-by N,M] [--blocking N] [--label L] [--dry-run]` — renders the body exactly as GitHub's web form does, checks it, then runs `gh issue create` with gh's native relationship flags and the template's labels.
- `gh-issue check [-R owner/name] --kind create|edit|comment [--title T] [--body-file F]` — the same rules, no write.

It reads templates from `.github/ISSUE_TEMPLATE/` with `gh api`, and parses them with PyYAML through a PEP 723 header, so it needs [`uv`](https://docs.astral.sh/uv/) on `PATH`.

**`hooks/gh-issue-guard.py`** — PreToolUse hook on Bash. A raw `gh issue create`, `comment`, `edit --title/--body`, or `close`/`reopen --comment` runs only if `gh-issue check` passes its text. Text it cannot read — stdin, `$(...)`, `$VAR`, a heredoc, `--web`, `--editor` — is denied with the way to make it readable. Once a command is an issue write, a check that could not run is a deny. Relationship-, label-, and assignee-only edits pass untouched. Standard library only; one regex per Bash call on the fast path.

**`hooks/github-api-stop-hook.py`** — Stop hook. Scans the trailing assistant turn for GitHub web-API attempts that `gh`'s high-level subcommands could have covered, and blocks turn-end with remediation guidance:

- `curl` / `wget` / `http` / `httpie` against `api.github.com` — raw REST bypass
- `gh api <endpoint>` where a subcommand covers the endpoint — `COVERED` in `hooks/gh_api_coverage.py`, the one place to edit when `gh` grows a subcommand. Anywhere else `gh api` passes silently (Zach, 2026-09-22 14:50: *"allow gh api for features that are not in the CLI yet"*).
- `WebFetch` of `github.com`

The guard adds one `gh api` rule of its own: a call that writes issue text is denied, so allowing `gh api` is not the way around the issue rules.

The escape hatch is an explicit `WEB-API-FALLBACK-JUSTIFIED` line in the final response. See §5 of `GITHUB.md`.

## Tests

```
uv run --quiet --with pyyaml python -m unittest discover -s plugins/github-utilities/tests
```

`gh` is injected as a Python callable; the guard's end-to-end cases run the real hook against the real `gh-issue check`.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere.

Installing is the whole install. Both hooks are wired by `hooks/hooks.json`, and `bin/gh-issue` sits at the default `bin/` location, which Claude Code adds to the Bash tool's `PATH` while the plugin is enabled.

Earlier revisions of this file claimed a plugin cannot put a binary on `PATH` and prescribed a `~/.local/bin/` symlink. That was wrong, and the symlink is worse than unnecessary: it outlives `plugin disable`, leaving a bare command still reachable and pointing into a checkout after the plugin is off.

## Provenance

Extracted from `Standard Configs/claude-plugins/github-utilities/` at `d36d794`: the Stop hook and a `gh-issue-rel` wrapper, byte-identical to their source.

2.0.0 (2026-09-22) removed `gh-issue-rel`. It wrapped REST calls for sub-issues and blocked-by dependencies because `gh` had no subcommand for them; gh 2.101 has native `--parent`, `--blocked-by`, `--blocking` on `gh issue create` and `--add-sub-issue`, `--add-blocked-by`, `--add-blocking` on `gh issue edit`, which take issue numbers rather than database ids. The same release added `gh-issue` and the PreToolUse guard.

2.1.0 (2026-09-22) narrowed the Stop hook's `gh api` rule to covered endpoints and made the guard deny `gh api` writes of issue text.
