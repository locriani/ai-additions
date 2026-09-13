# PLAN_AUDIT.md — the pre-`ExitPlanMode` speculation audit

**Purpose**: Run the §6 gate against a plan before it is presented. Loads only on
`call(ExitPlanMode ∧ plan_has_new)`, so the procedure costs nothing in sessions that never
write a plan, and nothing on plans that add no new surface — where the gate was already a
no-op.

## The gate

For every claim proposing a new abstraction, test, field, parameter, override hook, or
defensive guard: construct its failure scenario; mark unconstructible ones DROP or
DOWNGRADE; dispatch ≥1 `general-purpose` subagent to repeat the audit against the code in
the repo (`git show origin/main:<path>`) with KEEP / DROP / DOWNGRADE verdicts; surface
every verdict and wait.

```
A := the audit returns a verdict     R := the user has ruled on it
I := the verdict is incorporated into the plan

□(I → R)   ≡   □(¬R → ¬I)      [contrapositive]
∴  A ∧ ¬R  ⊢  ¬I                unreviewed verdict ⊢ plan unchanged
```

**Surface the criterion, not just the verdict** — "no constructible caller", "the type
enforces it". A verdict reads identically whether the measure behind it was right or
irrelevant, so the criterion is the only part that can be checked. One turn, numbered rows,
recommendation first, flag any verdict whose criterion you doubt, then stop. Once ruled,
§10 applies.

## A DROP deletes the item

```
plan ⊨ {done}    ∴  ¬done(X) ⊢ X ∉ plan
```

`Not moved — X`, `Considered and rejected: Y`, and an "Open Questions" section restating a
settled decision are inventories of the null action and read as decisions the user never
made. Kill on sight: tests re-proving the type system, single-inhabitant enums, newtype
wrappers around the same struct, LOC budgets in a plan.

## When the verdict itself is contested

Whether something is speculative *at all* — the craft/architecture boundary, the six
shapes, the rationalization table — is `CRAFT_VS_YAGNI.md`. Read it when a KEEP/DROP turns
on that question rather than on constructibility.

---

Companion to §6 in `CLAUDE.md`. Source/owner:
`claude-core/claude-md/templates/global/PLAN_AUDIT.md`.
