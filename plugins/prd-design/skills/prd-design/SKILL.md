---
name: prd-design
description: Use when a feature or change has been discussed enough that it needs writing down before work starts — "write this up", "let's spec this", "we need a PRD", or a conversation that has produced a shape nobody has committed to a document. Do NOT use for a single bug, a chore, or work already decomposed into tickets.
---

# PRD Design

Ask first, write second. A PRD is only worth the document if the answers in it
came from the user rather than from you — a synthesized spec reads identically
whether its scope section was established or invented, and that is the failure
this skill exists to prevent.

## The one rule that governs everything

**The interview precedes the draft. Every time.**

```
always:  interview → draft
never:   draft_first = ✗          (never "here's a draft, correct me")
never:   fill(gap) = ✗            (an unanswered question is MARKED, not filled)
```

"Here's a first pass, tell me what's wrong" inverts the work: it makes the user
audit your guesses instead of stating their intent, and a plausible guess is
harder to spot than a blank.

## The interview

Six questions, in order. Ask them as a group, not one at a time — the user reads
fast and answering six at once is cheaper than six round-trips.

| # | question | feeds |
|---|---|---|
| 1 | Who hits this problem today, and what do they do instead? | Problem Statement |
| 2 | What is observably different for them when it's done? | Solution |
| 3 | What is explicitly **out** of scope? | Out of Scope |
| 4 | How do we know it worked — what is the test? | Success Criteria |
| 5 | What is the smallest version still worth shipping? | **first vertical slice** |
| 6 | What existing code does this touch, and at what seam is it tested? | Implementation / Testing Decisions |

**Q6 is answered against the codebase, not from memory.** Explore for the seam
and cite `file:line`. An answer you recall is an answer you are guessing.

```
knew(t₀) ⊬ knows(t₁)          when did you last read that file?
```

### Gaps are marked, never filled

A question the user skipped, deflected, or answered partially produces a section
reading exactly:

```
⚠ not established — <the question, restated>
```

The PRD is not finished while a `⚠` stands. It is resolved, or it is explicitly
waived in writing. It is never quietly replaced with something reasonable.

## The document

| section | content |
|---|---|
| Problem Statement | user-centric, from Q1 |
| Solution | user-centric, from Q2 |
| User Stories | numbered. `As a [role], I want [x], so that [y]` |
| Implementation Decisions | modules, interfaces, schema/API contracts, the seam from Q6 with its `file:line` |
| Testing Decisions | what is under test; precedents cited from the codebase, not asserted |
| Vertical Slices | ordered — see below |
| Out of Scope | from Q3, in the user's words |
| Success Criteria | from Q4, as a test someone could run |

## Vertical slices — state the rule, don't assume it

This is the section the whole document exists to produce, and the rule is
explicit because leaving it implied is how it gets broken.

```
slice  ≡  schema → API → UI → tests        one narrow path through EVERY layer
slice  ≠  layer                            "the database work" is not a slice
```

Four constraints, all of them checkable:

1. **Complete path.** A slice cuts through every integration layer the feature
   touches. A slice that needs a sibling slice finished before anyone can look at
   it is a layer wearing a slice's name.
2. **Independently demoable.** You can show the result to someone and they can
   tell whether it works. If demonstrating it requires "imagine the UI", it isn't
   one.
3. **One context window.** A slice too big to hold is a slice that will be
   half-done and misreported as done.
4. **Dependency order, blockers first.** The frontier stays legible: at any point
   the next grabbable slice is obvious.

**Slice 1 is the tracer bullet** — the Q5 answer, the thinnest end-to-end path
that proves the whole stack connects. It is not the easiest slice and not the
most valuable one; it is the one that makes every later slice cheaper by
retiring the integration risk first.

Ordered slicing is the *only* place tracer-bullet discipline is enforced here.
There is no separate tracer-bullet skill and there should not be one:

```
D := work decomposed as ordered vertical slices, taken one at a time
T := tracer-bullet discipline holds

D → T            the decomposition carries it
∴ T ⊬ skill(T)   a second skill enforcing it is redundant
```

## Where the PRD lands

Write the document and stop. **Default: a file at `docs/prd/<slug>.md`** — it
works with no remote, in a private repo, with any tracker or none.

Publishing to GitHub is supported but is not the default, and when it is used the
structure carries the relationships — never prose:

```sh
gh-issue new --template prd --title T --field id=value         # .github/ISSUE_TEMPLATE/prd.yml, YAML form schema
gh-issue new --template slice … --parent <prd#>                # slices are NATIVE sub-issues
gh issue edit <slice#> --add-blocked-by <blocker#>             # dependencies are NATIVE, not "blocked by #12"
```

Native links are mandatory for both. Writing "blocked by #12" in the body instead creates a second source of truth that rots as the issues move, and `github-utilities` refuses it.

## Red flags — the inference that fails

| Thought | Checksum | Reality |
|---|---|---|
| "We discussed this enough — I can skip the interview." | `knew(t₀) ↛ knows(t₁)` | The conversation established a shape, not the six answers. Scope and success criteria are the two that never come up unprompted, and they're the two the document is for. |
| "They'd have said so if my out-of-scope were wrong." | `¬obs(P) ↛ ¬P` | Silence on a scope boundary is silence, not assent. Nobody audits a section that looks reasonable — which is exactly why an invented one survives. |
| "The user stories cover the scope." | `A ⊊ B` | Stories are what's in. Out of Scope is what's deliberately excluded, and it's a different set — the gap between them is where the work grows. |
| "This slice is obviously demoable." | `felt(P) ↛ tested(P)` | Name who you'd show it to and what they'd see. If the answer needs "imagine the UI", it's a layer. |
| "Each slice is small, so the PRD is small." | `∀i small(cᵢ) ↛ small(Σcᵢ)` | Eight one-window slices is eight windows. Count them before calling the thing scoped. |
| "The PRD is written, so the work is scoped." | `planned ↛ landed` | An unresolved `⚠` means the document is a draft with a hole in it, and the hole is load-bearing. Resolve it or waive it in writing. |
| "I'll draft it and they can correct me." | `draft_first → audit(guesses)` | This is the one rule, inverted. Correcting a plausible draft is strictly harder than answering six questions, because the guesses don't look like guesses. |
