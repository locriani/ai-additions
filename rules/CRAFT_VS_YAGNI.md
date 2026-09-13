# CRAFT_VS_YAGNI.md — where refactoring is NOT speculation

**Purpose**: Draw the exact line between code where YAGNI governs and code where invoking it is a category error. YAGNI (§6) kills speculative *architecture*; it has nothing to say about clean-code *structure*. Confusing the two has Claude reject legitimate decomposition as "speculative" — this doc stops that.

## Two domains, opposite rules

There are two domains, and the rule flips between them:

- **Architectural / feature domain — YAGNI governs.** Unrequested features, APIs with no current caller, tests duplicating existing coverage, just-in-case flexibility, config knobs nobody set, extension points for hypothetical needs. These carry a real carrying cost AND **raise** the barrier to change. Don't build them. (Full canon: §6.)
- **Code-craft / structural domain — YAGNI is irrelevant; the clean-code defaults govern.** Small functions, low cyclomatic complexity, low mental overhead, tight class scope, SRP, OCP-correct factoring. **None of this is speculative.** It **lowers** the barrier to change.

The inversion that makes them opposites: **decomposition lowers the cost of change; speculative architecture raises it.** They point in opposite directions. So "this cyclo-5 function should be split" and "add an override hook for a future caller" are not the same kind of suggestion — the first is fundamentals, the second is the thing YAGNI forbids. Treating the first as the second is the category error this doc exists to prevent.

## YAGNI domain — don't build (real cost + RAISES the barrier to change)

- Unrequested features / endpoints / flags.
- APIs, hooks, or parameters with **no current caller**.
- Tests that re-prove the type system or duplicate existing coverage.
- "Just in case" config knobs, env vars, init params with defaults nobody changes.
- Extension seams added for a requirement **that does not yet exist**.

Each is a future migration cost paid every day, plus a foot-gun the day it drifts. Ship the value as a constant; revisit when a real second caller arrives.

## The six shapes

The frame names these six as bare nouns, because naming them is what makes you notice you are in §6 territory at all. Here is each one spelled out. Every one looks like good engineering in isolation and ships the bug it pretended to prevent:

- **Override hooks with no real override.** Making a field configurable "in case someone overrides the default" forces every caller to restate the default, and a copy-paste that updates one and not the other ships wrong.
- **Tests that re-prove the type system.** Asserting begin/end signpost IDs match when `endInterval(_:)` only accepts opaque state minted by `beginInterval(_:)` — no caller can produce a mismatch. The type is the proof.
- **DRY refactors the language won't let you finish.** `OSLogMessage` interpolation must be literal at the call site; extracting "the format string" drops to `String` and logs `<private>`. Accept structural duplication over lost correctness.
- **Defensive code against impossible callers.** Guarding empty arrays the contract forbids, `if let` on non-optionals, retrying what the framework retries, re-validating what the previous layer validated.
- **"Just in case" knobs.** Env vars, flags, init params nobody changes. Ship the constant; revisit at the second real caller.
- **Architecture from a follow-up issue.** Issues get deferred, rewritten, cancelled, renamed, rescoped. Roadmaps and design docs are not committed code. Build what *this* PR needs.

## Craft domain — always do (LOWERS the barrier to change)

- Small functions; one reason to exist each (SRP).
- Low cyclomatic complexity; low mental overhead per read.
- Tight class / module scope; no grab-bag types.
- OCP-correct factoring **for the requirements that already exist**.

None of this is "investment against an imagined future." It is correctness in the present. Skipping it doesn't save speculation — it ships debt.

## Complexity is a present-tense diagnosis, not a someday-maybe

A high complexity score is **not** "maybe refactor someday." It reads, in the present tense: *"you need this refactor badly, now."* The complexity already exists, is already a cost, is already a barrier to change. Decomposing it **pays down debt that exists** — it does not bet on debt that *might*. Low complexity is correctness today, not a hedge against tomorrow. So a complexity finding is never YAGNI-able by calling the resulting seam "speculative": the seam removes a cost that is already on the books.

## The OCP nuance (the sharp one)

OCP-correctness means: shape the code you **already have** so a class/function becomes invariant — closed for modification — **with respect to the requirements that ACTUALLY EXIST.** That is *not* the same as bolting on extension points for requirements that don't.

- "Factored right for what it does" → **fundamentals.** Do it.
- "Flexible for what it might do" → **the speculative architecture YAGNI forbids.** Don't.

The word "extensible" hides the trap. Closing a unit against the variation it *already* sees is craft; opening it for variation it has *never* seen is speculation.

## The tests nuance (same shape, opposite verdict)

A test answers the exact same discriminator as everything else — *does the need exist TODAY?* — and it cuts both ways. Writing a test is **craft** when it pins a **present, uncovered contract the type system does NOT enforce** for an **API in immediate use**: creating an API for immediate use and documenting its behavior with a test is a real present need, not speculative future flexibility. Writing a test is **YAGNI** when it re-proves what the type system already guarantees, duplicates existing coverage, or defends an impossible-by-construction caller.

```
test is craft  ↔  ¬type_enforced ∧ ¬already_covered ∧ api_in_immediate_use
test is YAGNI  ↔  type_enforced ∨ duplicate_coverage ∨ impossible_by_construction_caller
discriminator (as everywhere):  does the need exist TODAY?
```

Worked contrast: a thin app-layer conformer whose only real logic is `guard let key = try store.key(forDevice:) else { throw .missingPairingKey }`. The compiler forces *a* throw to exist but not *which* error — so `nil → .missingPairingKey` is a behavioral contract the type system does NOT enforce, and the lower-layer tests only exercise the valid-key path, leaving it uncovered. A test asserting `nil → that specific error` documents a real present contract → **craft.** Contrast a test re-proving something the type already guarantees — matching opaque IDs an API can only mint in pairs → **noise; the type system is the proof.** Same shape (a test), opposite verdict; the discriminator is solely whether the behavior is a real, presently-uncovered need. This is the *counter*-case that keeps "don't add tests that re-prove the type system" from collapsing into "don't add tests" — it does **not** license duplicate coverage or impossible-caller defenses.

## SOLID quick-ref

Each is a craft-domain fundamental — and each has a YAGNI failure mode when applied to needs that don't exist yet.

| Principle | One-line | YAGNI trap (over-applied speculatively) |
|---|---|---|
| **SRP** Single Responsibility | One reason to change per unit; split god-functions/classes. | Splitting along axes nothing varies on yet → fragmentation with no payoff. |
| **OCP** Open/Closed | Closed to modification for the variation that already exists. | Extension hooks/strategy patterns for variation never observed. |
| **LSP** Liskov Substitution | Subtypes honor the supertype's contract. | Inventing a hierarchy when there's exactly one concrete type. |
| **ISP** Interface Segregation | Clients depend only on methods they call. | Splitting interfaces for hypothetical future clients. |
| **DIP** Dependency Inversion | Depend on abstractions where a seam already earns its keep — a *multiply-implemented* abstraction that's the house pattern across sibling types earns the seam even with zero *new* callers this PR ("zero callers THIS slice" is the wrong lens for a codebase-wide convention). | Injecting an interface with a *single forever-implementation*. |

The left column is always-do; the right column is YAGNI. Same principle, opposite verdict — the discriminator is always *does the need already exist?*

## Decision procedure

When a reviewer / persona / future-you flags "split this" or "add this abstraction," ask one question:

> Does it **reduce the cost of changing code that ALREADY EXISTS** — or does it **add capability / flexibility for something NOT requested**?

- Reduces cost of existing code (decomposition, SRP split, naming, OCP-right factoring) → **do it.** Fundamentals. Not subject to YAGNI.
- Adds unrequested capability / a seam for a hypothetical caller → **skip it.** YAGNI. (Apply the §6 gate.)

If you can't tell, ask: *is there a caller today?* No caller → speculation. Caller exists → craft.

## Red flags — common rationalizations

| Thought | Checksum | Reality |
|---|---|---|
| "This decomposition is speculative architecture." | `new(seam) ↛ speculative(seam)`; speculative ↔ `¬∃need(today)` | No — the complexity already exists. Decomposition removes a **present** cost; it doesn't bet on a future one. Category error. |
| "The function works; splitting it is gold-plating." | `works ↛ ¬cost` — cost is paid per read, now | Cyclo > ~4 is a present-tense diagnosis. The mental-overhead cost is paid on every read, now — not someday. |
| "SRP / small functions is just taste." | `felt(P) ↛ tested(P)`; `SRP ⊢ ↓cost(change)` | It's a fundamental that **lowers** cost-of-change, not a feature you ship on demand. Taste-neutral. |
| "Extracting this seam might help a future caller." | `◇P ↛ P` | If no caller exists, THAT is the YAGNI line. Factor for what exists; stop there. |
| "YAGNI says don't add structure." | `A ⊊ B` | YAGNI says don't add *unrequested capability*. Structure for existing code is the opposite of capability for absent needs. |
| "Leave the god-function; refactor is risk." | `¬touch ↛ ¬risk` — already realized | The god-function is the risk already realized. The refactor pays it down; not touching it keeps paying interest. |

## Rationalizations — the step that does not follow

```
◇need(override)     ⊬ build(override)      ◇P ⊬ P; build ← ∃caller today
¬◇F                 ⊬ valuable(test(F))    a test for an impossible F hides the real ones
type_proves(P)      ⊬ ¬test(P)             A ⊊ B — the type may not cover the contract
                                             (see "The tests nuance" above)
rated(CRITICAL)     ⊬ real                 ↑proxy ⊬ ↑target — construct the caller
clear_cut(audit)    ⊬ ¬surface(criterion)  the criterion is the part a verdict hides
dropped(X)          ⊬ X ∈ plan             plan ⊨ {done} — delete the entry
small(cᵢ)           ⊬ small(Σcᵢ)           × N features = half the codebase is defense
◇change(API)        ⊬ defend(API)          whoever changes it owns the tests
◇flexible           ⊬ build(flexible)      flexibility ships when needed, not as a daily tax
for(test)           ⊬ ¬ships(prod)         test-only flexibility ships to production
planned(followup)   ⊬ landed(followup)     deferred, rewritten, cancelled, rescoped
```

The table above this one catches over-applying YAGNI to craft; this one catches under-applying it to architecture. Same file, opposite failure modes.

## Worked example — the borderline spelled out

A ~50-line, cyclomatic-complexity-~5 function that formats and emits a log line, with three optional `if line: parts.append(line)` blocks for three fixed message-lines.

1. **Decompose the god-function into small SRP pieces** → **correct (fundamentals).** The complexity already exists; splitting removes a present cost and lowers cost-of-change. Not speculative — there is nothing hypothetical about a function that is hard to read *today*.
2. **Collapse the three EXISTING optional-line kwargs into one `lines: Sequence[str]` parameter** → **also correct.** It removes **existing** duplication and is OCP-right *for what the code already does* (three lines, today). The seam earns its keep on the current requirement.
3. **Add that same `Sequence` seam purely "so a future 4th line is easy"** — when no fourth line is requested → **THE YAGNI line.** Identical-looking change, opposite verdict: here it's capability for an unrequested need. Skip it; the §6 gate applies.

Cases 1 and 2 are craft because they pay down cost on code that **exists**. Case 3 is speculation because it adds flexibility for a need that **doesn't**. The shape of the diff is the same; the discriminator is solely whether the need is present today.

---

Companion to §5 (Demand Elegance) and §6 (YAGNI) in `CLAUDE.md`. This file now holds both canons — don't-**build** (the six shapes and the rationalizations, relocated from §6) and don't-**misapply**. The plan-time gate lives in `PLAN_AUDIT.md`. Loaded by `apply(§6, refactor ∨ decomposition ∨ existing_code)` — when §6 is aimed at structure that already exists and the boundary is what is in question. Source/owner: `claude-core/claude-md/templates/global/CRAFT_VS_YAGNI.md`.
