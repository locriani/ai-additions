# atuin

**Upstream:** [`atuinsh/atuin`](https://github.com/atuinsh/atuin) · <https://atuin.sh/>
**Install method:** `Standard Configs/machine/atuin/apply.py` (see below — no longer raw `brew`/shell commands run from here)
**Status:** enabled 2026-09-16 on "reference-points, claude-statusline, atuin, security-guidance, are approved for enabling". The binary was already on the machine via Homebrew (18.22.0) with an empty database; the shell init line and the import were the missing steps. Given a proper Standard Configs runbook 2026-09-21 on "also bring atuin and the default setup for that into ai-additions as well" — see **Placement** below.

Improved shell history for zsh, bash, fish and nushell. Replaces the flat
`.zsh_history` with a SQLite database: full-text and fuzzy search over every
command, recorded with its working directory, exit code, duration and session —
plus optional end-to-end encrypted sync across machines.

## Why it is here

It is one of the few items on this list that is not a Claude Code plugin at all —
no skill, no hook, no MCP. It earns its place because shell history is the record
of what was actually run, and a searchable, directory-aware, exit-code-aware
history is the difference between reconstructing a past session and guessing at
it.

## Placement

This row used to carry its own copy of the install commands, with a note that
`atuin` "sits oddly against this repo's premise" and "would normally belong in
`Standard Configs/machine/dev-essentials`' Brewfile". That gap is closed:
[`Standard Configs/machine/atuin/`](https://github.com/locriani/Standard-Configs/tree/main/machine/atuin)
is now the real runbook — its own subfolder rather than a Brewfile line, since
atuin needs a `~/.zshrc` init line and a one-time history import on top of the
formula install (same shape as `machine/postgres` there: formula plus runtime).
This row stays in `referenced/` rather than moving to `plugins/` because it is
still not a Claude Code plugin — nothing here for `claude plugin install` to
register — it just now points at a real runbook instead of prose.

## Install

```sh
cd "$HOME/Developer/Standard Configs/machine/atuin"
./apply.py
./check.py
```

`apply.py` is idempotent: it installs the `atuin` formula via Homebrew (skipped
if already present), appends `eval "$(atuin init zsh)"` to `~/.zshrc` (skipped if
the exact line is already there), and imports `~/.zsh_history` **once** (skipped
once atuin's own database is non-empty, since import is a backfill, not a sync).
`check.py` confirms the binary, the init line, a non-empty history database, and
a working search.

Sync is opt-in and off by default (`atuin register` / `atuin login`) — not
configured by the runbook. Init line and import first ran 2026-09-16; 344
entries imported then, 587 as of the runbook landing 2026-09-21.
