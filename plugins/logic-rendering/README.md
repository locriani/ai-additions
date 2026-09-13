# logic-rendering

A skill. Renders logic — conditionals, implications, `requires`/`unless`,
multi-premise reasoning — as boolean/modal notation **alongside** short prose.

## Why

A truth table or a `⊢` derivation is a checksum. If the formalization is wrong,
that is visible in one glance; the same error buried in a paragraph is not. The
point is verifying *comprehension*, not decorating the answer.

It fires on its own triggers and skips statements with no logic to check — plain
facts, single unconditional instructions, opinions.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere.

## Provenance

From `Standard Configs/claude-core/claude-md/templates/global/LOGIC_RENDERING.md`
at `d36d794`, byte-identical. Only its path changed, from an always-on
`~/.claude/LOGIC_RENDERING.md` rule file to `skills/logic-rendering/SKILL.md`.

That file already carried `name` and `description` frontmatter — it was authored
as a skill and deployed as a resident rule. This packaging is what it was written
for, so it is the one rule file in this repo that did not need a decision about
whether to convert it.
