# terminalskills

**Upstream:** [`TerminalSkills/skills`](https://github.com/TerminalSkills/skills) (public)
**Local checkout:** none
**Status:** referenced, not installed.

*A candidate for the issue-tracking half of the PRD pipeline. Not chosen — see
the blocker below.*

One skill, **`prd-to-issues`**: locate the PRD (a GitHub issue), explore the
codebase, draft vertical slices, quiz the user on the breakdown, then create
issues in dependency order with `gh issue create`. Slices are tagged **HITL**
(needs a human in the loop) or **AFK** (can merge unattended) — a distinction
neither other candidate makes, and a genuinely useful one for unattended runs.

## Why it is worth recording

Smallest surface of the three. One skill, no setup step, no sibling skills to
ignore, no workflow to adopt. If the publishing step were right, this would be
the cheapest thing to take.

## The blocker

Same as the others, and here it is the whole skill: relationships are written with `gh issue create` and prose — "blocked by #12", "parent: #4" — which [`rules/GITHUB.md`](../rules/GITHUB.md) forbids in favour of native links through `gh`'s relationship flags.

It also assumes the PRD is already a GitHub issue, so it cannot read a
`docs/prd/<slug>.md` file — which is the default destination
[`prd-design`](../plugins/prd-design/) writes to.

```
A := PRD is a GitHub issue
prd-to-issues requires A
prd-design defaults to ¬A            ∴ needs a bridge either way
```

The HITL/AFK tag is the one idea here worth lifting even if the skill is not.

## Install (when enabled)

```sh
claude plugin marketplace add TerminalSkills/skills
claude plugin install prd-to-issues@terminalskills
```

Nothing above has been run.
