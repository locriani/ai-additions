# Stack Profile: Bash Scripts

Load this profile when the project is primarily shell scripts — i.e. the bulk of the tracked code is `*.sh` / `*.bash`, or the repo's purpose is a CLI / runbook / automation tooling expressed in bash. Also load when editing any `*.sh` file in a polyglot repo, even if the rest of the repo isn't bash.

## Header discipline

Every script starts with this exact preamble. Non-negotiable:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

- `#!/usr/bin/env bash` not `/bin/sh` (macOS `/bin/bash` is still 3.2 on Sequoia 15.x — Apple has not budged off the GPLv2-era build, and there's no signal they ever will).
- `set -e` — fail on error.
- `set -u` — fail on unset variable.
- `set -o pipefail` — failed pipe segments propagate. **Caveat:** `pipefail` does NOT cause early termination — the full pipeline still runs, you just get the right exit code at the end. If you need early termination, restructure away from the pipe.
- Prefer `set -Eeuo pipefail` (capital `-E`) when the script uses `trap ... ERR` — without `-E`, ERR traps don't inherit into functions, command substitutions, or subshells.
- Add `IFS=$'\n\t'` if the script does any word splitting on lines (defensive against filenames with spaces).

**`set -e` is a 60% solution, not a 100% one.** It is silently disabled in: commands inside `if`/`while`/`until` conditions, every command in a pipeline except the last (without `pipefail`), command substitutions in older bash (`local x=$(false)` masks the failure — see SC2155), commands after `||` / `&&`, and most subshell contexts. Don't assume `set -euo pipefail` is a safety net — it catches the easy bugs and lets the hard ones through. When correctness matters in those zones, check `$?` explicitly or use `|| fail "..."`.

If a script intentionally tolerates failures, narrow the relaxation: `<cmd> || true` on the specific line, not by dropping `set -e` globally. Exception for verifier scripts that want to report ALL failures: use `set -uo pipefail` (no `-e`) so the script keeps going.

## Linting + formatting

Two tools, both non-negotiable, both run before commit:

### `shellcheck` — semantic lint

Every committed `*.sh` passes `shellcheck` clean. No `# shellcheck disable=...` without a one-line comment explaining why. Run with severity dialed up and source-following on:

```bash
shellcheck -x -S style path/to/script.sh
```

`-x` follows `source`d files; `-S style` surfaces the style-tier checks most projects leave off by default. Install: `brew install shellcheck`.

**Rules worth knowing (don't blanket-disable):**
- **SC2155** — `local x=$(cmd)` masks `cmd`'s exit code; the `local` always returns 0, so `set -e` and traps don't fire on the inner failure. Split into `local x; x=$(cmd)`.
- **SC2128** — referencing an array without an index (`$arr` instead of `${arr[@]}`) silently gives you element 0. Almost always a bug.
- **SC2086** — quote your expansions. The most-disabled rule in the wild; resist the urge — when you actually want word splitting, the right move is `# shellcheck disable=SC2086 # word-splitting intended` with a justification, not a blanket project-level disable.

### `shfmt` — formatter

`shfmt` is the de-facto bash formatter (Go binary by mvdan, the same author as the bash parser used by GitHub's syntax tooling). It is to bash what `gofmt` is to Go and `black` is to Python — no debate, just run it. Install: `brew install shfmt`. Canonical invocation, matching the Google Shell Style Guide:

```bash
shfmt -i 2 -ci -bn -s -w path/to/script.sh
```

- `-i 2` — 2-space indent.
- `-ci` — indent switch cases.
- `-bn` — binary ops at start of line on continuation.
- `-s` — simplify.
- `-w` — write in place (drop for a dry-run).

Run `shfmt -d` (diff) in CI to fail on unformatted scripts.

## Quoting + parameter expansion

- **Quote every variable** unless you specifically want word splitting: `"$var"`, `"${arr[@]}"`. The cost of an unquoted `$file` containing a space is a silently broken script — never worth it.
- **Use `[[ ]]` not `[ ]`** for tests. `[[` doesn't word-split, supports `=~`, and is the modern idiom.
- **Use parameter expansion over `sed`** for path-safe string operations:
  - `${var//pattern/replacement}` for global replace.
  - `${var#prefix}` / `${var%suffix}` for trimming.
  - `${var:-default}` for defaults.
  - This matters because paths can contain `&`, `|`, `\`, `/` — all of which break naive `sed s/foo/bar/`. A repo path with an `&` in it is not hypothetical, and `sed` turns it into the whole match.
- **`local` every variable in functions.** Unset variables leak to the caller's scope and `set -u` won't catch it.

## Subshells, pipes, and process substitution

- **`while read` loops:** prefer `while IFS= read -r line; do ... done < <(cmd)` over `cmd | while read line`. The pipe form runs the loop in a subshell, so any variable mutation inside is lost. Process substitution (`< <(...)`) keeps it in the parent shell.
- **`mapfile` / `readarray`** for slurping into an array (bash 4+; on macOS bash 3.2 use the `while read` form).
- **`$(cmd)` not backticks.**
- **`(( ... ))`** for arithmetic, not `expr` or `let`.

## Error handling + cleanup

- **`trap`** for cleanup on exit. Always `trap '<cleanup>' EXIT` before creating temp files / spawning background work.
- **`mktemp`** for temp files (never `/tmp/myscript.tmp` — race conditions, predictability):
  ```bash
  TMP=$(mktemp -t prefix.XXXXXX)
  trap 'rm -f "$TMP"' EXIT
  ```
- **Helper functions:**
  ```bash
  fail() { echo "FAIL: $*" >&2; exit 1; }
  ok()   { echo "  ok: $*"; }
  warn() { echo "  warn: $*" >&2; }
  ```
  Standardize across the project — one `fail()` shape, used everywhere.

## CLI niceties

- **`command -v <bin>` not `which <bin>`** — POSIX, no extra subprocess.
- **Argument parsing:** `case "${1:-}" in ... esac` for simple scripts; `getopts` for non-trivial. Avoid `getopt` (the BSD/GNU split is painful).
- **Exit codes:** 0 = success, non-zero = failure. Reserve specific codes if the script is composable (1 = generic, 2 = misuse, 64+ = sysexits style).

## macOS bash 3.2 caveats

Apple still ships bash 3.2.57 (frozen in 2007 over GPLv3) — confirmed on macOS Sequoia 15.x in 2025/2026. The system default interactive shell switched to zsh in Catalina, but `/bin/bash` is still 3.2 and there's no signal Apple will ever update it. On macOS, scripts that target the system bash CANNOT use:

- Associative arrays (`declare -A`) — use parallel indexed arrays: `ORDER=(...)` plus `DESC[i]=...`, indices kept in step, never a `declare -A DESC`.
- `mapfile` / `readarray` — use `while IFS= read -r line; do arr+=("$line"); done < <(...)`.
- `${var,,}` / `${var^^}` for case conversion — use `tr '[:upper:]' '[:lower:]'`.
- `wait -n` — use a polling loop or restructure.
- `${var@Q}` and other `@` parameter transformations (bash 4.4+).

`brew install bash` on Apple Silicon installs to `/opt/homebrew/bin/bash` (5.x); on Intel Macs, `/usr/local/bin/bash`. The shebang `#!/usr/bin/env bash` finds the Homebrew one if `/opt/homebrew/bin` is earlier on PATH — which is the standard Homebrew setup. Don't hard-code `/opt/homebrew/bin/bash` in the shebang; let `env` resolve it.

If you NEED bash 4+ features, the script must `#!/usr/bin/env bash` AND assert at the top:

```bash
if (( BASH_VERSINFO[0] < 4 )); then
  echo "ABORT: this script needs bash 4+. macOS ships 3.2 — install via 'brew install bash' and re-run with /opt/homebrew/bin/bash" >&2
  exit 1
fi
```

**Bash 5.2 / 5.3 features worth knowing** (Linux-only or Homebrew-only on macOS): rewritten command-substitution parser catches syntax errors earlier; `${var@Q}` for shell-safe quoting; `wait -n` returning the PID; and in 5.3, a new in-process command substitution form. Don't reach for these in scripts that might run against system bash on a Mac.

## Testing

- **`bats-core`** is still the canonical bash test runner — actively maintained (last release Nov 2025), TAP-compliant, works with bash 3.2+. Install: `brew install bats-core`. Tests live in `tests/*.bats`. Worth it for anything beyond a single script.
- **`shellspec`** is the serious alternative — BDD-style, POSIX-shell-compatible (works with dash/ksh/zsh, not just bash), built-in mocking, code coverage, and parameterized tests. Reach for it when you need cross-shell testing or richer test ergonomics; otherwise default to bats-core for the smaller learning curve and TAP integration.
- **For trivial scripts:** a hand-rolled `verify.sh` that exercises the script with known inputs and `diff`s against expected output is fine — no `bats` dependency, but disciplined assertions.

## Verification ritual

Before claiming a bash change is done:

1. `shellcheck -x -S style <script>` passes clean.
2. `shfmt -d -i 2 -ci -bn -s <script>` shows no diff (script is formatted).
3. `bash -n <script>` (parse-only) passes.
4. The script's own self-test / verify pass runs green (`bats tests/`, the project's check script, or whatever it uses).
5. For repo-shaping scripts (anything that creates files, mutates `~/`, runs `git`): test in a scratch dir or worktree first. Never iterate on a destructive script directly against `~/`.

## Common traps

- **`local x=$(cmd)` masks failures** — split the declaration. SC2155 catches this; don't disable it.
- **`cmd | while read` loses variable mutations** — the `while` runs in a subshell. Use `while read; do ...; done < <(cmd)`.
- **Unquoted `$arr` is element 0, not the array** — always `"${arr[@]}"`.
- **`set -e` in `if` conditions does nothing** — every command in an `if` is exempt. If you `set -e` and rely on a function failing inside `if foo; then`, it won't.
- **`pipefail` doesn't short-circuit** — every stage of the pipe still runs to completion. Pipefail only changes the exit code, not the timing.
- **`sed` on paths breaks on metacharacters** — `&`, `|`, `\`, `/` all need escaping in `sed s///`. Prefer parameter expansion (`${var//pattern/replacement}`) for path manipulation — `${content//\{\{HERE\}\}/$HERE}` substitutes a placeholder safely whatever the path contains, where the `sed` equivalent silently expands `&` into the whole match.
- **`declare -A` doesn't exist on macOS system bash** — use parallel indexed arrays (`ORDER=(...)` plus a same-indexed `DESC[i]=...`).
- **Hardcoding `/opt/homebrew/bin/bash` in shebang** — breaks on Intel Macs. Use `#!/usr/bin/env bash` and let PATH resolve it.
