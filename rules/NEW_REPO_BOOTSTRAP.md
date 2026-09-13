# NEW_REPO_BOOTSTRAP.md — new-repo / init protocol

When starting work in a repository under `~/Developer/` that does NOT yet have a `CLAUDE.md` (or when the user says "init this repo", `/init`, "set up CLAUDE.md", or similar):

**0. First, check git history — "missing" is not "new".** Before copying the template, run `git -C <repo> log --oneline -- CLAUDE.md` (and likewise for any other file you'd template, e.g. `README.md`, `DEV_TOOLS.md`). If the file has **any** commit history, it was tracked before and later gitignored/untracked — a fresh worktree or checkout simply isn't materializing it. Do **NOT** scaffold the blank template over it: recover the last real version instead (`git show <last-good-commit>:CLAUDE.md > CLAUDE.md` — for a file removed by a commit, its content is at that commit's `~1`), tell the user it was **recovered, not scaffolded**, and skip templating that file. Only template when the file has **no** history (a genuinely new repo). This is the trap that silently blanked tracked `CLAUDE.md` files (e.g. Vendle, FocusLog) gitignored in repos with worktrees.

1. Copy `~/Developer/CLAUDE_TEMPLATE.md` to the repo root as `CLAUDE.md`.
2. Read the repo to gather what you can infer automatically: language(s), build system, package manager, test framework, presence of `tasks/`, `.gitignore`, CI config, project type.
3. Ask the user a tailoring questionnaire — one question at a time, in this order. Skip any question whose answer is unambiguous from the repo:
   - Project name + one-line purpose.
   - Primary language(s) and runtime/SDK versions.
   - Build/test commands (the exact invocations to run unit tests, build, lint, type-check).
   - Test framework + test-run sizing rules.
   - Architectural commitments (Clean Arch? layered? functional core / imperative shell? none?).
   - Code organization rules (one public type per file? barrel exports? module/folder conventions?).
   - Documentation surfaces that must stay in sync with code changes (changelogs, help content, README, API docs, tooltips).
   - Generated artifacts and gitignore-must-haves.
   - Per-session ritual steps (bump build number? other always-do-this items).
   - Anything load-bearing or surprising (hydration gates, migration rules, sandbox quirks, parallel-run rules).
4. Fill the template's placeholders, delete unused sections, commit `CLAUDE.md` only after the user confirms. **§11 applies to every line you write here** — a scaffolded `CLAUDE.md` is the likeliest place for a ceiling to enter a repo, because everything in it reads as a rule from the first commit onward. Record why the code has the shape it has; never a dependency ledger, a count presented as a virtue, a service declared irrelevant, or a path treated as fixed. If you believe a limit is real, it is another question for step 3, not a sentence you add on your own.
5. **Verify README.md exists** (see "README is non-negotiable" below). If missing or stale, generate/update it in the SAME commit. The README serves humans; CLAUDE.md serves Claude — both are required.
6. **Memory: nothing to do.** Write capture and recall already work in every repo via the global hooks (against the global DB) — a new repo needs no memory setup. `/init-ai-memory` is **not** part of bootstrap; it's the separate, opt-in tool you run only if this specific repo should keep its memories in an *isolated* per-repo DB. Don't run it by default. Details: `claude-core/ai-memory/README.md` §16.
7. Register the project in Claude's **auto memory** (the file-based system at `~/.claude/projects/<dir-hash>/memory/`), NOT the ai-memory MCP. Auto memory loads into every session's system prompt automatically, so project-existence is an always-on identity fact that's in scope before any tool call — which the MCP (recalled per-turn, not always loaded) can't guarantee. **How**: drop a `*.md` file with YAML frontmatter (`name`, `description`, `type: project`) into `~/.claude/projects/<dir-hash>/memory/` and add a one-line pointer in that directory's `MEMORY.md` index. Don't invent extra metadata.

Do NOT silently overwrite **or re-scaffold over** an existing — **or git-historied** — `CLAUDE.md` or `README.md`. If a file is present, ask whether to merge, replace, or leave alone. If it's absent but has git history (gitignored/untracked), recover it from history per step 0 rather than templating.

## README is non-negotiable

```
□(ships_standalone(d) → ∃f(d/README.md))
ships_standalone ≡ repo ∨ package ∨ plugin ∨ skill ∨ library
□(user_facing_change → README ∈ same_commit)      stale ≻ missing in badness
□(new_repo → README ∈ initial_commit)             ¬"in a follow-up commit"
audience(README) = human   ·   audience(CLAUDE.md) = Claude
```

Written for a human skimming on GitHub at 11pm who has never seen the project. Short
sentences, real examples, no marketing fluff. The first screen answers "what is this and
should I use it?" Code blocks run as-is — no placeholders the reader has to guess at. If
the code already says it better via clear naming, delete the prose.

Order:

1. **One-line description** — what this is.
2. **Why** — the problem it solves.
3. **Quick start** — install + the smallest "make it run" example, copy-pasteable.
4. **Usage / common workflows** — what users will actually do, with examples.
5. **Architecture** — only as much as a contributor needs.
6. **Development** — local setup, tests, build, contributing.
7. **License** — if applicable.
