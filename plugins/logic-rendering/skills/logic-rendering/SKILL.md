---
name: logic-rendering
description: Use when a message carries logic worth confirming — conditionals, implications, "requires"/"unless", or multi-premise reasoning — and a compact truth-checksum would let the user verify comprehension faster than prose. Skip when a statement has no logic to check (plain facts, single unconditional instructions, opinions).
---

# Logic Rendering (boolean / modal checksums)

Render logic — questions, instructions, derivations — as boolean/modal notation **alongside short prose**, so the user can verify your comprehension against a compact checksum instead of parsing a wall of text.

The user reads fast and multi-pass and needs to confirm you understood an instruction's *logic*, not just its words. A truth table or a `⊢` derivation is a checksum: if your formalization is wrong, the user sees it in one glance.

## The one rule that governs everything
**Boolean AUGMENTS prose; it never replaces it.**

```
always:  prose→shorter  ∧  render boolean alongside
never:   boolean_only = ✗          (never boolean-only, never boolean-instead-of)
```

When you reach for notation, the prose gets *shorter* — the boolean carries the structure, the prose carries the meaning. You never emit a block of symbols with no plain-English gloss, and you never drop the prose entirely.

## When to apply / when to skip

```
apply  when:  a question ∨ instruction ∨ discussion carries logic worth verifying
              (conditions, implications, "requires", "unless", multi-premise reasoning)
skip   when:  a plain statement with no logic to check
never:        boolean REPLACES prose         (boolean_only = ✗)
always:       boolean AUGMENTS shorter prose  (prose→shorter  ∧  render boolean)
```

### Symbol cheat-sheet:
| symbol | reads as |
|---|---|
| `¬` | not |
| `∧` | and |
| `∨` | or |
| `⊕` | xor / exclusive or |
| `→` | implies / "requires" (`A→B`: A only if B) |
| `↛` | does NOT imply — the non-sequitur most rationalizations turn on |
| `↔` | iff / biconditional |
| `≡` | logically equivalent |
| `⊢` | proves / therefore |
| `∴` | therefore |
| `⊤` | true / tautology |
| `⊥` | false / contradiction |
| `∀` | for all |
| `∃` | there exists |
| `□` | necessarily / required (modal) |
| `◇` | possibly (modal) |

### Named rules worth citing inline:

| rule | form |
|---|---|
| Modus ponens (MP) | `A, A→B ⊢ B` |
| Modus tollens (MT) | `A→B, ¬B ⊢ ¬A` |
| K (modal MP) | `□A ∧ □(A→B) ⊢ □B` |
| De Morgan | `¬(A∧B) ≡ ¬A∨¬B` · `¬(A∨B) ≡ ¬A∧¬B` |
| Contrapositive | `A→B ≡ ¬B→¬A` |

## How to render

The shape is **English → glossary → formalize → derive**:

1. **Glossary** — bind each atom to a single letter (`S := the test suite runs`).
   One letter, one proposition; no reused letters.
2. **Formalize** — write the premises in notation, one per line, each tagged with
   the English clause it came from so the reader can check the translation.
3. **Derive** — apply named rules line by line, citing the rule (`[K]`, `[MP]`)
   in the margin. End with `∴` and the conclusion.
4. **Gloss** — one short plain-English line so the checksum is legible without
   decoding every symbol. This is the "prose→shorter" half — it stays.

Put the notation in a fenced block; keep the surrounding prose tight.

### Red-flag tables carry a checksum column

A red-flag table is `Thought | Checksum | Reality` — never two columns. The
thought is a rationalization, so it always contains an inference, and the
checksum is that inference stated precisely enough to see it fail. Two columns
lets a row assert "that's wrong" without naming *which step* is wrong.

**Cite a schema; don't invent a formula.** Rationalizations are not endlessly
various — nearly all of them are one of these eight, and naming which one is
the test. A row gets a bespoke formula only when it is a mechanical fact
rather than a fallacy.

| schema | the error | what to test |
|---|---|---|
| `◇P ↛ P` | modal collapse — *might* need it read as *does* | is there a caller **today**? |
| `¬obs(P) ↛ ¬P` | absence of evidence read as evidence of absence | did you look, or just not see it? |
| `∀i small(cᵢ) ↛ small(Σcᵢ)` | local smallness read as aggregate smallness | × N occurrences — still small? |
| `↑proxy ↛ ↑target` | the measured quantity isn't the one that matters | does the proxy move with the target, or independently? |
| `knew(t₀) ↛ knows(t₁)` | remembered state read as current state | when did you last check? |
| `planned ↛ landed` | intent or deferral read as completion | has it merged? |
| `felt(P) ↛ tested(P)` | a feeling substituted for the test that decides it | run the test the rule actually names |
| `A ⊊ B` | a part taken for the whole | what's in B that isn't in A? |

The right-hand column is why this beats a bespoke formula per row: the schema
carries the *check*, so a reader who disagrees points at the schema instead of
arguing with the prose — and rows that share a schema share a rebuttal.

## Worked derivation

Premises: *"a release cannot skip the test suite; running the suite requires a
compiled binary; a compiled binary is required."*

```
S := the test suite runs
B := a compiled binary exists

1.  □S                     [P1:  "skipping S impossible" = □¬¬S = □S]
2.  □(S → B)               [P2:  S requires B]
3.  □S ∧ □(S→B) ⊢ □B       [K]
4.  □B                     [also asserted by P3 — over-determined]
∴   □B
```

Stripped of modality it is one modus ponens: `S, S→B ⊢ B`. The `□`s only add
"there was never a release where it came out otherwise." That one-line gloss is
the prose half — it is what makes the block a checksum rather than a puzzle.

## Red flags — render, or don't

Two failure modes, pointing opposite ways. Left column = the thought; right =
the correction.

**Thoughts that mean *stop — render the logic*:**

| Thought | Checksum | Reality |
|---|---|---|
| "I'll just explain the conditions in a paragraph." | `prose(logic) ↛ checkable(logic)` | A wall of prose is exactly what the user can't checksum. If there's an implication or a "requires", the notation IS the fast path — render it. |
| "The chain of premises is obvious, no need to formalize." | `knew(t₀) ↛ knows(t₁)` | If it's obvious, the formalization is cheap and confirms it in one glance. If it's *not* as obvious as you assume, the formalization is where the user catches your misread. |
| "It's a 'requires'/'unless', but only one of them." | `\|premises\| = 1 ↛ ¬direction`; `A→B ≠ B→A` | One `→` still carries direction (`A→B` ≠ `B→A`). A single arrow is the most common thing the user wants to verify you got pointing the right way. |
| "Modality is overkill here." | `"must" ∨ "impossible" ∨ "may" ∈ text ⊢ render(□ ∨ ◇)` | `□`/`◇` are cheap when "must"/"impossible"/"may" appear in the instruction. Strip them in the gloss if they add nothing; render them when the words are there. |

