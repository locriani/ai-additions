# SKILL_AUTHORING.md — creating or editing a skill

Use the official **`skill-creator`** plugin for the mechanics — scaffolding, frontmatter,
directory layout, packaging, validation:

```bash
claude plugin install skill-creator@claude-plugins-official
```

Everything below is the delta this machine adds on top of it. Where `skill-creator`
and this file disagree about mechanics, `skill-creator` wins.

## Description = triggers, never workflow

```
description ⊨ {when it fires}
description ⊭ {what it does, what it outputs}
```

A workflow summary in the description creates a shortcut the model takes *instead of*
reading the body. One sentence: the trigger, then why the skill rather than doing it
inline, then at most one `Do NOT use for…` clause — and only where a sibling skill is a
real mis-fire risk.

```
paraphrased_user_phrasings ⊬ trigger        keyword stuffing dilutes the one routing signal
```

**Self-verify before shipping:** read the description back. Can a future-you tell from
the triggers alone whether the skill applies? If not, rewrite it.

## Paths

```
correct:  ${CLAUDE_PLUGIN_ROOT}/skills/<name>/…
wrong:    ~/.claude/skills/<name>/…          does not exist post-install
```

The installed path is version-stamped (`~/.claude/plugins/cache/<mkt>/<plugin>/<version>/…`),
so a hard-coded `~/.claude/skills/` script reference is dead on arrival. `extras/check.py`
asserts no `SKILL.md` contains that literal.

## Discipline-enforcing skills carry a rationalization block

Any skill that enforces discipline (TDD, debugging, code review, estimation) MUST render
its red flags as the inference that fails — premise, the step drawn from it, and the fact
that defeats it:

```
felt(done)        ⊬ done              run the test the rule names
knew(t₀)          ⊬ knows(t₁)         when did you last check?
```

A two-column "thought | reality" table lets a row assert *that* something is wrong
without naming *which step* is wrong. See `LOGIC_RENDERING.md` for the schemas.

## Body

The rules themselves. Concrete, scannable, ordered by priority.
