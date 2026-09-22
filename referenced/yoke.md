# yoke

**Upstream:** [`yokeloop/yoke`](https://github.com/yokeloop/yoke) (public)
**Local checkout:** none
**Status:** referenced, not installed.

*A candidate for the issue-tracking half of the PRD pipeline. Not chosen — see
the blocker below.*

A single plugin covering the full dev loop as 14 slash commands:
`/task → /plan → /do → /review → /gca → /gp → /pr`, plus `/prd`, `/issues`,
`/explore`, `/grill`, `/bootstrap`, `/handoff`. The two that matter here are
**`/yoke:prd`** (conversation + codebase → a PRD published as a GitHub epic
issue) and **`/yoke:issues`** (a plan or PRD → independently-grabbable GitHub
issues as vertical slices, tracer bullets named explicitly).

## Why it is worth recording

Cleanest install of the three — one marketplace, one plugin, no setup step, and
the tracer-bullet vocabulary is already in its own documentation rather than
implied.

## The blocker

Two, and the second is the larger.

1. **Prose blocking edges, GitHub only.** Same violation of [`rules/GITHUB.md`](../rules/GITHUB.md) as every candidate: dependencies are written into the body rather than through `gh`'s native relationship flags. And there is no local-tracker path at all, so a repo with no remote gets nothing.
2. **It is command-shaped, not skill-shaped.** `/do`, `/review`, `/merge`, `/pr` carry an entire opinionated workflow that overlaps `rules/GITHUB.md` on branches, PR templates, and closing keywords — without agreeing with it.

```
install(yoke) ≡ adopt(workflow)     ≠  add(skill)
```

Taking `/prd` and `/issues` alone is not offered; the commands share a plugin.

## Install (when enabled)

```sh
claude plugin marketplace add github:yokeloop/yoke
claude plugin install yoke@yoke
```

Nothing above has been run.
