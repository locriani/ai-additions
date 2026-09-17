# atuin

**Upstream:** [`atuinsh/atuin`](https://github.com/atuinsh/atuin) · <https://atuin.sh/>
**Install method:** `brew install atuin` (18.22.0 at time of writing)
**Status:** enabled 2026-09-16 on "reference-points, claude-statusline, atuin, security-guidance, are approved for enabling". The binary was already on the machine via Homebrew (18.22.0) with an empty database; the shell init line and the import were the missing steps.

Improved shell history for zsh, bash, fish and nushell. Replaces the flat
`.zsh_history` with a SQLite database: full-text and fuzzy search over every
command, recorded with its working directory, exit code, duration and session —
plus optional end-to-end encrypted sync across machines.

## Why it is here

It is the one item on this list that is not a Claude Code plugin at all — no
skill, no hook, no MCP. It earns its place because shell history is the record of
what was actually run, and a searchable, directory-aware, exit-code-aware history
is the difference between reconstructing a past session and guessing at it.

It also sits oddly against this repo's premise: `atuin` is a machine tool that
would normally belong in `Standard Configs/machine/dev-essentials`' Brewfile,
where it is currently **absent**. Recorded here because it was approved here; the
placement is worth revisiting.

## Install

```sh
brew install atuin
atuin import auto          # pull in existing shell history
echo 'eval "$(atuin init zsh)"' >> ~/.zshrc
```

Sync is opt-in and off by default (`atuin register` / `atuin login`). Init line
and import run 2026-09-16; 344 entries imported.
