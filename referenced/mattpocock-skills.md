# mattpocock-skills

**Upstream:** [`mattpocock/skills`](https://github.com/mattpocock/skills) (public)
**Local checkout:** none
**Status:** referenced, not installed.

*A candidate for the issue-tracking half of the PRD pipeline. Not chosen — see
the blocker below.*

The relevant pair lives under `skills/engineering/`: **`to-spec`** writes a spec
by synthesizing the conversation, and **`to-tickets`** breaks a plan, spec, or
conversation into tracer-bullet tickets, each declaring its blocking edges, then
publishes to the configured tracker.

## Why it is the closest of the three

`to-tickets` actually *computes* the dependency graph — it drafts vertical
slices, quizzes on granularity and blocking edges until approved, and publishes
in dependency order so the frontier stays clear. That graph is the expensive
part, and it is the part the other two candidates do least well.

It is also the only candidate with a **local tracker**: tickets can land in
`.scratch/` files instead of GitHub or Linear. For a private repo with no remote
that is the difference between usable and not.

## The blocker

Publishing writes blocking edges as prose. [`rules/GITHUB.md`](../rules/GITHUB.md) forbids it — sub-issues and blocked-by dependencies are native `gh issue` relationship flags, and §"Trust the relationships" specifically condemns restating a relationship in the body because it rots as the issues move.

```
computes(graph)  ∧  ¬publishes(graph, native)
```

Only the last step is wrong. Adopting this means replacing its publish step with `gh`'s native relationship flags, per [`rules/GITHUB.md`](../rules/GITHUB.md).

Second cost: `to-spec` depends on triage-label vocabulary established by a
`setup-matt-pocock-skills` step, and the repo ships Matt-specific siblings
(`ask-matt`, `wizard`) that would be installed and ignored.

`to-spec` itself is superseded here by [`prd-design`](../plugins/prd-design/),
which interviews rather than synthesizes.

## Install (when enabled)

```sh
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock-skills
```

Nothing above has been run.
