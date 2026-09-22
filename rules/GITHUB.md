# GITHUB.md — GitHub workflow discipline

**Purpose**: Non-negotiable rules for how Claude interacts with GitHub. Enforces structured surfaces (templates, native relationships, `gh` CLI) over freeform prose and direct web-API calls.

Runtime enforcement lives in [`plugins/github-utilities/`](../plugins/github-utilities/): a Stop hook that blocks turn-end when a web-API call slipped past `gh`; a PreToolUse guard that runs every raw `gh issue` write through `gh-issue check`; and `gh-issue`, the filing surface. See §5 below for the escape hatch.

## Issues — non-negotiable

- Every repo MUST ship at least one issue template at `.github/ISSUE_TEMPLATE/*.yml`, in GitHub's **YAML form schema** (`name:`, `description:`, `body:` with `type: input|textarea|dropdown|checkboxes`). Legacy markdown templates (`*.md` under `ISSUE_TEMPLATE/`) are not acceptable for new repos.
- Every repo MUST set `blank_issues_enabled: false` in `.github/ISSUE_TEMPLATE/config.yml`. Blank-issue filing is forbidden — every issue uses a template.
- One concern per issue. Don't bundle "X is broken AND Y would be nice" — file two issues.
- An issue never cites another issue in prose — no `#N`, `owner/repo#N`, `GH-N`, issue URL, or "issue N" in a title, body, or comment. Link it: `--parent` / `--blocked-by` / `--blocking` at create, `gh issue edit --add-sub-issue` / `--add-blocked-by` / `--add-blocking` after. Code blocks are exempt.
- The body is a filled template, and each field's type sets its cap: `input` 1 line of 100 chars, `textarea` 6 lines of 160 chars, `textarea` with `render:` 20 lines, `dropdown` one of its options. Title 72 chars. A comment gets the plain `textarea` cap. A wall does not fit.
- File with `gh-issue new --template KEY --field id=value …`; `gh-issue templates` lists the repo's templates and caps. A raw `gh issue create` is held to the same rules by the guard.

## Pull requests — non-negotiable

- Every repo MUST ship `.github/pull_request_template.md` (single template) or a `.github/PULL_REQUEST_TEMPLATE/` directory (multi-template repos selecting via the `?template=` query param).
- Every PR MUST declare its related issue using GitHub's **native closing keywords** in the PR body: `Closes #N`, `Fixes #N`, or `Resolves #N`. These keywords are what build the structural timeline link AND auto-close the issue on merge. Freeform prose like "this addresses issue 123" does neither and rots silently.
- PRs without a related-issue keyword are acceptable only for trivial chores (typo fixes, dependency bumps, generated-file refreshes). When in doubt, file the issue first.
- One issue per PR. Multiple `Closes #N, closes #M` is allowed when the issues genuinely collapse to one change, but the default expectation is 1:1. Multi-close → reconsider whether the issues should have been one to begin with.

## Branches

- Use `type/short-slug` naming: `fix/login-redirect`, `feat/oauth-rotation`, `chore/bump-deps`, `docs/runbook`, `refactor/auth-extract`. Imperative type prefix; kebab-case slug; no issue numbers in the branch name (the PR carries the linkage).
- Claude-generated `claude/<adjective-name-hash>` branches (FleetView-style placeholders) are renamed during plan mode per the global "worktree branch rename is part of the plan" rule. Never ship a PR from a `claude/`-prefixed branch.

## `gh` CLI is the only GitHub surface for Claude

Use the high-level `gh` subcommands for every GitHub interaction:

| Goal | Command |
|---|---|
| View / comment / close issue | `gh issue view N` / `gh issue comment N` / `gh issue close N` |
| File an issue from a template | `gh-issue new --template KEY --title T --field id=value` |
| View / create / review / merge PR | `gh pr view N` / `gh pr create` / `gh pr review N` / `gh pr merge N` |
| Check CI / workflow runs | `gh run list`, `gh run view N`, `gh run watch N` |
| Repo metadata, releases, workflows | `gh repo view`, `gh release ...`, `gh workflow ...` |
| Native sub-issues + blocked-by dependencies | at create: `gh-issue new … --parent N --blocked-by N,M --blocking N`; after: `gh issue edit N --add-sub-issue M` / `--add-blocked-by M` / `--add-blocking M`; read: `gh issue view N --json parent,subIssues,blockedBy,blocking` |

Relationships are native `gh` flags since gh 2.101 and take issue numbers. `gh-issue` reads a repo's templates with `gh api …/contents/…`, an endpoint no subcommand covers.

**Forbidden surfaces:**

- `curl`, `wget`, `httpie`, or any HTTP client targeting `api.github.com`. These bypass auth, rate limits, and the structured surface.
- `gh api` for anything a `gh` subcommand covers — issues, PRs, runs, workflows, secrets, variables, releases, labels, forks, repo metadata, search, gists; the table is `COVERED` in [`hooks/gh_api_coverage.py`](../plugins/github-utilities/hooks/gh_api_coverage.py). Where no subcommand exists — GraphQL, repo contents, rulesets, milestones, Projects — `gh api` **is** the surface and needs no token.
- `gh api` writes of issue text — `POST …/issues`, a title or body `PATCH`, comments, and the GraphQL `createIssue` / `updateIssue` / `addComment` / `updateIssueComment` mutations. The PreToolUse guard denies them: issue text goes through `gh-issue new`, `gh issue comment`, or `gh issue edit`, which it checks.
- WebFetch / web-fetch MCP tools targeting `github.com` URLs when the goal is reading repo state, issues, PRs, releases, or workflow runs. `gh` covers all of these structurally.

**Escape hatch.** When an endpoint is on the covered list but its subcommand genuinely can't make this particular call, end your turn's final response with a line beginning:

```
WEB-API-FALLBACK-JUSTIFIED: <one-sentence reason gh's high-level surface didn't cover this>
```

The Stop hook reads this token and allows the turn to end. Without the token, the turn is blocked and you must redo via `gh` or supply a justification.

Sub-issues and blocked-by dependencies are **not** an escape-hatch case — they are `gh issue` flags. Reaching for the token there means you skipped them.

## Trust the relationships — don't restate them

GitHub's structured surfaces — closing keywords, sub-issue / parent-issue links, milestones, project boards, draft state, requested reviewers, labels — are the durable record. PR-body prose like "this is related to issue #5 which we opened because the customer reported…" duplicates what the timeline already shows AND rots as the issues evolve. Write the relationship as structure; let GitHub render it. Sub-issue and blocked-by links are `gh issue` flags (see above); everything else has a `gh` subcommand.

## Verification quick-check (per repo)

```bash
# Templates present + blank issues disabled
ls .github/ISSUE_TEMPLATE/*.yml 2>/dev/null || echo "MISSING: YAML issue template"
test -f .github/ISSUE_TEMPLATE/config.yml \
  && grep -q '^blank_issues_enabled:\s*false' .github/ISSUE_TEMPLATE/config.yml \
  || echo "MISSING: blank_issues_enabled: false"
test -f .github/pull_request_template.md \
  || test -d .github/PULL_REQUEST_TEMPLATE \
  || echo "MISSING: pull_request_template.md"
```
