#!/usr/bin/env bash
# scaffold-new-repo.sh — canonical scaffold for a fresh repo.
#
# What this script does:
#   1. mkdir -p <target>; chdir
#   2. git init (skip if .git already there)
#   3. Create standard dirs per stack (from $SHARE/dirs/<stack>.txt)
#   4. Write CLAUDE.md  (from ~/Developer/CLAUDE_TEMPLATE.md, placeholders filled)
#   5. Write .gitignore (concat _base + <stack>; append-missing if exists)
#   6. Write README.md (from $SHARE/readme/README.template.md, placeholders filled)
#   7. Append a one-line stack-profile pointer to CLAUDE.md (idempotent, marker-detected)
#   8. git add -A && git commit -m "scaffold <stack> repo"  (skip if tree clean)
#   9. If --github: gh repo create <name> --private --source=. --remote=origin --push
#   10. Print next-steps from $SHARE/next-steps/<stack>.md (if present)
#
# What this script DOES NOT touch:
#   - ~/.claude/* (no settings, no commands, no hooks; that's apply.py's job)
#   - ~/.local/bin/* (apply.py installs the shim)
#   - the Standard Configs repo itself (refuses if target == it)
#   - per-repo ai-memory init (that's /init-ai-memory)
#   - native scaffold tools like cargo new / rails new (out of scope; v1)
#
# Idempotency contract:
#   - Re-running with the same args on a fully scaffolded repo emits only
#     `skip:` / `ok:` lines and produces zero mutations (git status clean).
#   - On partial scaffold (e.g. user deleted .gitignore), only the missing
#     pieces rebuild.
#   - --force overwrites the 3 file templates (CLAUDE.md, README.md,
#     .gitignore). Dirs / git-init / commit always skip-if-present.
#
# Usage:
#   scaffold-new-repo.sh <target-dir> --stack <stack> [--name <name>] [--github] [--force]
#
# Resolves $SHARE in this order:
#   1. $REPO_SCAFFOLD_SHARE env var (set by apply.py when invoked in-tree)
#   2. ~/.local/share/repo-scaffold/ (canonical deployed location)
#   3. <dirname of this script>/  (works when invoked directly out of the repo)

set -euo pipefail

# ── inline helpers (no sourced lib — keeps the contract explicit) ────────────
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
ok()   { printf '  ok: %s\n' "$*"; }
skip() { printf '  skip: %s\n' "$*"; }
warn() { printf '  warn: %s\n' "$*" >&2; }
sep()  { printf '\n==================================================\n%s\n==================================================\n' "$*"; }

# Substitute <<KEY>> tokens in a string. Uses bash parameter expansion, NOT
# sed — paths and content may contain `&`, `|`, `\`, `/`, so sed would corrupt.
# Usage:  out=$(substitute "$body" "<<NAME>>" "$NAME" "<<STACK>>" "$STACK")
substitute() {
  local body="$1"; shift
  while (( $# >= 2 )); do
    local key="$1" val="$2"
    body="${body//$key/$val}"
    shift 2
  done
  printf '%s' "$body"
}

# Count remaining <<PLACEHOLDER>> tokens in a file. Used to report
# "N placeholders left for you" so the user knows the template isn't done.
count_placeholders() {
  # `grep` exits 1 when a fully-substituted template has zero `<<...>>` tokens
  # left. Under `set -euo pipefail` that non-zero status would propagate through
  # the pipe and abort the whole scaffold — so swallow it: zero matches is a
  # legitimate "0", not an error.
  grep -oE '<<[^>]+>>' "$1" 2>/dev/null | sort -u | wc -l | tr -d ' ' || true
}

# ── resolve script-share dir (templates/gitignore + dirs + readme + next-steps) ──
resolve_share() {
  local candidate
  if [[ -n "${REPO_SCAFFOLD_SHARE:-}" && -d "$REPO_SCAFFOLD_SHARE" ]]; then
    printf '%s' "$REPO_SCAFFOLD_SHARE"
    return
  fi
  candidate="$HOME/.local/share/repo-scaffold"
  if [[ -d "$candidate/gitignore" ]]; then
    printf '%s' "$candidate"
    return
  fi
  # Fallback: alongside this script.
  candidate="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -d "$candidate/gitignore" ]]; then
    printf '%s' "$candidate"
    return
  fi
  fail "cannot locate scaffold share dir; checked \$REPO_SCAFFOLD_SHARE, ~/.local/share/repo-scaffold, and \$(dirname \$0)"
}

SHARE="$(resolve_share)"

# Template input (deployed by claude-core/claude-md). Fail clearly if absent
# rather than scaffold a broken repo with a missing CLAUDE.md.
CLAUDE_TPL="$HOME/Developer/CLAUDE_TEMPLATE.md"

# ── argument parsing ────────────────────────────────────────────────────────
TARGET=""
STACK=""
NAME=""
GITHUB=0
FORCE=0

usage() {
  cat <<'USAGE' >&2
Usage:
  scaffold-repo <target-dir> --stack <stack> [--name <name>] [--github] [--force]

Args:
  <target-dir>     Absolute or relative path. Created if missing.
  --stack <name>   Required. One of the 11 stack profiles. See list:
                     swift-apple bash-scripts python-uv node-typescript
                     postgres-sql rust go react-vite rails
                     infra-terraform kubernetes
  --name <name>    Repo name. Defaults to basename of <target-dir>.
  --github         Create a private GitHub repo via `gh repo create` and push.
  --force          Overwrite existing CLAUDE.md/README.md/.gitignore.
                   Never touches existing dirs / .git / commits.

Examples:
  scaffold-repo ~/Developer/myproj --stack python-uv
  scaffold-repo ./infra --stack infra-terraform --github
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack)   [[ $# -ge 2 ]] || fail "--stack requires a value"; STACK="$2"; shift 2 ;;
    --stack=*) STACK="${1#--stack=}"; shift ;;
    --name)    [[ $# -ge 2 ]] || fail "--name requires a value"; NAME="$2"; shift 2 ;;
    --name=*)  NAME="${1#--name=}"; shift ;;
    --github)  GITHUB=1; shift ;;
    --force)   FORCE=1; shift ;;
    -h|--help) usage ;;
    --*) fail "unknown flag: $1" ;;
    *)
      if [[ -z "$TARGET" ]]; then
        TARGET="$1"
      else
        fail "unexpected positional arg: $1 (target already '$TARGET')"
      fi
      shift
      ;;
  esac
done

[[ -n "$TARGET" ]] || { usage; }
[[ -n "$STACK" ]] || fail "--stack is required (run --help for the list)"

# Validate stack against the deployed gitignore catalog (single source of
# truth). Missing entry here means the stack isn't supported.
if [[ ! -f "$SHARE/gitignore/${STACK}.gitignore" ]]; then
  available=""
  for gi in "$SHARE/gitignore"/*.gitignore; do
    name="$(basename "$gi" .gitignore)"
    [[ "$name" == _base ]] && continue
    available+="$name "
  done
  fail "unknown stack '$STACK'. Available: $available"
fi

# Resolve target to absolute path WITHOUT requiring it to exist yet.
case "$TARGET" in
  /*) ABS_TARGET="$TARGET" ;;
  *)  ABS_TARGET="$PWD/$TARGET" ;;
esac
# Collapse "/./" and trailing slash but don't resolve symlinks (target may not exist).
ABS_TARGET="${ABS_TARGET%/}"
ABS_TARGET="${ABS_TARGET//\/.\//\/}"

[[ -n "$NAME" ]] || NAME="$(basename "$ABS_TARGET")"

# Pre-flight refusals — these protect against catastrophic mis-invocations.
case "$ABS_TARGET" in
  /)            fail "refusing to scaffold at /" ;;
  "$HOME")      fail "refusing to scaffold at \$HOME ($HOME) — pick a subdir" ;;
  /tmp)         fail "refusing to scaffold at /tmp directly; pick /tmp/<subdir>" ;;
esac
if [[ "$ABS_TARGET" == *"/Standard Configs"* || "$ABS_TARGET" == *"/Standard\ Configs"* ]]; then
  fail "refusing to scaffold inside the Standard Configs repo (target: $ABS_TARGET)"
fi

# Template from claude-md must be present.
[[ -f "$CLAUDE_TPL" ]] || fail "missing $CLAUDE_TPL — run claude-core/claude-md/apply.py first"

# ── header ───────────────────────────────────────────────────────────────────
sep "scaffold-repo: $ABS_TARGET  [stack: $STACK, name: $NAME]"

# Step 1: create target dir.
if [[ -d "$ABS_TARGET" ]]; then
  if [[ -n "$(ls -A "$ABS_TARGET" 2>/dev/null)" ]]; then
    skip "target exists and is non-empty (re-using; --force overwrites template files)"
  else
    ok "target dir exists (empty)"
  fi
else
  mkdir -p "$ABS_TARGET" || fail "mkdir failed: $ABS_TARGET"
  ok "target dir created: $ABS_TARGET"
fi
cd "$ABS_TARGET" || fail "cd $ABS_TARGET failed"

# Step 2: git init (idempotent).
if [[ -d .git ]]; then
  skip "git init (already a git repo)"
else
  # Force branch=main regardless of user's global init.defaultBranch.
  git init -q -b main . || fail "git init failed"
  ok "git init (branch: main)"
fi

# Step 3: standard dirs from $SHARE/dirs/<stack>.txt
DIRS_FILE="$SHARE/dirs/${STACK}.txt"
if [[ -f "$DIRS_FILE" ]]; then
  created_dirs=()
  while IFS= read -r line; do
    # Skip blanks and comments.
    [[ -z "$line" || "$line" == \#* ]] && continue
    # Substitute <<NAME>> in dir names (e.g. python-uv uses src/<<NAME>>/).
    dir="${line//<<NAME>>/$NAME}"
    if [[ -d "$dir" ]]; then
      :  # already there; silent
    else
      mkdir -p "$dir" || fail "mkdir $dir failed"
      # Keep empty dirs trackable by git via a .gitkeep file. Idempotent.
      [[ -e "$dir/.gitkeep" ]] || : > "$dir/.gitkeep"
      created_dirs+=("$dir")
    fi
  done < "$DIRS_FILE"
  if (( ${#created_dirs[@]} > 0 )); then
    ok "created ${#created_dirs[@]} dir(s): ${created_dirs[*]}"
  else
    skip "standard dirs (all present)"
  fi
else
  skip "standard dirs (no $STACK.txt — stack has no standard layout)"
fi

# Step 4: CLAUDE.md
write_template_file() {
  local dest="$1" src="$2"
  shift 2
  # Remaining args are substitution pairs.
  local body
  body="$(cat "$src")"
  while (( $# >= 2 )); do
    body="${body//$1/$2}"
    shift 2
  done
  if [[ -e "$dest" && $FORCE -eq 0 ]]; then
    skip "$dest exists (use --force to overwrite)"
    return 0
  fi
  # Refuse to template over a file that has git history (tracked before, then
  # gitignored/untracked). Such a file is absent in fresh checkouts/worktrees, so
  # scaffolding the blank template here would clobber real content. Recover from
  # history instead (or pass --force to template anyway).
  if (( FORCE == 0 )) && git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
     && [[ -n "$(git log -n 1 --format=%H -- "$dest" 2>/dev/null)" ]]; then
    warn "$dest has git history — refusing to scaffold the blank template over it."
    warn "  Recover real content (e.g. git show <commit>~1:$dest > $dest) or re-run with --force."
    return 0
  fi
  printf '%s' "$body" > "$dest" || fail "write $dest failed"
  local remaining
  remaining=$(count_placeholders "$dest")
  if (( remaining > 0 )); then
    ok "$dest written ($remaining placeholder(s) left for you to fill)"
  else
    ok "$dest written"
  fi
}

write_template_file CLAUDE.md "$CLAUDE_TPL" \
  '<<NAME>>'         "$NAME" \
  '<<PROJECT NAME>>' "$NAME"

# Step 5: .gitignore (concat _base + <stack>; append-missing if exists)
BASE_GI="$SHARE/gitignore/_base.gitignore"
STACK_GI="$SHARE/gitignore/${STACK}.gitignore"
[[ -f "$BASE_GI"  ]] || fail "missing $BASE_GI"
[[ -f "$STACK_GI" ]] || fail "missing $STACK_GI"

if [[ -e .gitignore && $FORCE -eq 0 ]]; then
  # Append-missing — exact-line match via `grep -qxF`.
  added=0
  total=0
  while IFS= read -r line; do
    total=$((total + 1))
    # Skip pure-blank lines for the dedup check (they're cheap noise).
    if [[ -z "$line" ]]; then
      continue
    fi
    if ! grep -qxF -- "$line" .gitignore; then
      printf '%s\n' "$line" >> .gitignore
      added=$((added + 1))
    fi
  done < <(cat "$BASE_GI" "$STACK_GI")
  if (( added > 0 )); then
    ok ".gitignore: appended $added new line(s) (existing file preserved)"
  else
    skip ".gitignore (already has all $total lines)"
  fi
else
  cat "$BASE_GI" "$STACK_GI" > .gitignore || fail "write .gitignore failed"
  lines=$(wc -l < .gitignore | tr -d ' ')
  ok ".gitignore written ($lines line(s) from _base + ${STACK}.gitignore)"
fi

# Step 6: README.md
README_TPL="$SHARE/readme/README.template.md"
[[ -f "$README_TPL" ]] || fail "missing $README_TPL"

write_template_file README.md "$README_TPL" \
  '<<NAME>>'         "$NAME" \
  '<<PROJECT NAME>>' "$NAME" \
  '<<STACK>>'        "$STACK"

# Step 7: stack-profile pointer in CLAUDE.md (idempotent, marker-detected)
POINTER_MARKER="<!-- repo-scaffold:stack-profile -->"
POINTER_LINE="$POINTER_MARKER Load the **${STACK}** stack profile via \`Read ~/.claude/stacks/${STACK}.md\` per global CLAUDE.md."
if [[ -f CLAUDE.md ]]; then
  if grep -qF "$POINTER_MARKER" CLAUDE.md; then
    skip "CLAUDE.md stack-profile pointer (already present)"
  else
    {
      printf '\n## Stack Profile\n\n'
      printf '%s\n' "$POINTER_LINE"
    } >> CLAUDE.md
    ok "CLAUDE.md: appended stack-profile pointer ($STACK)"
  fi
else
  warn "CLAUDE.md missing — skipping stack-profile pointer"
fi

# Step 8: initial commit (skip if tree clean)
if [[ -z "$(git status --porcelain 2>/dev/null)" ]]; then
  skip "initial commit (working tree clean — nothing to commit)"
else
  git add -A || fail "git add failed"
  # Default commit author comes from git config; if neither user.name nor
  # user.email is set, git commit will fail with a clear error — let it.
  if git commit -q -m "scaffold $STACK repo"; then
    sha=$(git rev-parse --short HEAD)
    ok "initial commit (sha $sha)"
  else
    fail "git commit failed (check git config user.name / user.email)"
  fi
fi

# Step 9: GitHub repo (opt-in)
if (( GITHUB == 1 )); then
  if ! command -v gh >/dev/null 2>&1; then
    fail "--github requested but 'gh' CLI is not on PATH"
  fi
  if ! gh auth status >/dev/null 2>&1; then
    fail "--github requested but 'gh auth status' failed (run 'gh auth login')"
  fi
  if git remote get-url origin >/dev/null 2>&1; then
    skip "gh repo create (origin remote already set: $(git remote get-url origin))"
  else
    if gh repo create "$NAME" --private --source=. --remote=origin --push 2>&1 | sed 's/^/    /'; then
      ok "GitHub repo created and pushed: $(gh repo view "$NAME" --json url -q .url 2>/dev/null || echo "$NAME")"
    else
      fail "gh repo create failed (local scaffold is intact; fix gh issue then re-run with --github)"
    fi
  fi
else
  skip "--github not set; no GitHub repo created"
fi

# Step 10: next-steps
NEXT_STEPS="$SHARE/next-steps/${STACK}.md"
sep "Next steps ($STACK)"
if [[ -f "$NEXT_STEPS" ]]; then
  cat "$NEXT_STEPS"
else
  cat <<EOF
  - cd "$ABS_TARGET"
  - Edit CLAUDE.md — fill any remaining <<PLACEHOLDER>> tokens
  - Edit README.md — replace the placeholders with real content
  - Load the stack profile: ~/.claude/stacks/${STACK}.md (Claude does this on demand)
  - Optional: run /init-ai-memory inside the repo to bootstrap per-repo ai-memory
EOF
fi
printf '==================================================\n'
