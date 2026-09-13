---
description: Scaffold a new repo (CLAUDE.md, README.md, .gitignore, stack dirs, git init, optional GitHub create). Wraps ~/.local/bin/scaffold-repo and adds an AI-surface confirmation for the GitHub step.
allowed-tools: Bash, Read
argument-hint: "<target-dir> --stack <stack> [--name <name>] [--github] [--force]"
---

# Scaffold a new repo

You are invoking the canonical repo-scaffold script on behalf of the user. The script (`~/.local/bin/scaffold-repo`, backed by `~/.local/share/repo-scaffold/scaffold-new-repo.sh`) does all the work — your job is to:

1. Parse `$ARGUMENTS` to extract `<target-dir>`, `--stack`, `--name`, `--github`, `--force`.
2. Apply the AI-surface confirmation rule for `--github` (see below).
3. Invoke the script via the Bash tool and report its output verbatim.
4. After it returns, surface any placeholders the user still needs to fill.

## Argument parsing

`$ARGUMENTS` is the raw string after `/scaffold-repo`. Forms accepted:

- `/scaffold-repo ~/Developer/myproj --stack python-uv`
- `/scaffold-repo ./infra --stack=infra-terraform --github`
- `/scaffold-repo /tmp/x --stack rust --name my-crate --force`

Required:
- A non-flag positional path → `<target-dir>`.
- `--stack <name>` (or `--stack=<name>`) → must be one of:
  `swift-apple bash-scripts python-uv node-typescript postgres-sql rust go react-vite rails infra-terraform kubernetes`

Optional flags: `--name <name>`, `--github`, `--force`.

If `<target-dir>` or `--stack` is missing, ask the user in plain text (per the `asking-protocol:asking` skill: one concern per turn, numbered options) before invoking the script. Don't guess.

## AI-surface GitHub confirmation

If the user did **not** pass `--github` AND did **not** pass any explicit "no github" signal, ask once in plain text with numbered options (per the `asking-protocol:asking` skill):

> Question: "Create a private GitHub repo for this scaffold (and push the initial commit)?"
> Options:
>   - "Yes — create + push" (sets `--github`)
>   - "No — local only" (skip; leave the local scaffold)

If the user passed `--github` explicitly, skip the prompt and pass it through.

This prompt only fires for `/scaffold-repo` (the AI surface). The bash CLI (`scaffold-repo`) is opt-in only — never prompts.

## Invocation

After argument resolution, invoke the script via Bash. Pass arguments through unchanged:

```bash
~/.local/bin/scaffold-repo <target-dir> --stack <stack> [<other flags>]
```

The script handles all idempotency, pretty output, and verification internally. Show its output to the user verbatim — don't summarize over it.

## Post-invocation

After the script exits 0:

1. Scan the script's output for "N placeholder(s) left for you" lines. If any file has placeholders, remind the user briefly:
   > CLAUDE.md and README.md still have `<<...>>` tokens to fill in. Open them in your editor and search for `<<` to find each one.
2. If `--github` ran successfully, surface the repo URL the script printed.
3. If the script exited non-zero, **do not claim success**. Report exactly what failed and what the user should do next.

## Failure modes

- `--stack` missing or unknown → script exits 2 with a list of available stacks; surface that list to the user.
- Target dir refused (`$HOME`, `/`, `/tmp`, inside Standard Configs) → relay the refusal; do not try to work around it.
- `gh` missing or unauthenticated → relay the error; suggest `gh auth login` or running without `--github`.
- `~/Developer/CLAUDE_TEMPLATE.md` missing → tell the user to run `claude-core/claude-md/apply.py` first.

Do not invent fallbacks. The script's error messages are the canonical guidance.
