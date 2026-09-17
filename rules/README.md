# rules/

Prose rule documents, copied **verbatim** from
`Standard Configs/claude-core/claude-md/templates/global/` at `d36d794`.

## Status: three deployed, three not

`CRAFT_VS_YAGNI`, `PLAN_AUDIT`, `CEILINGS` were copied verbatim to `~/.claude/<NAME>.md` on 2026-09-16 ("install CRAFT_VS_YAGNI, PLAN_AUDIT, CEILINGS"). No `~/.claude/CLAUDE.md` exists on this machine to reference them, so they are present but inert until one does. The other three: nothing deploys them. In Standard Configs they are
written to `~/.claude/<NAME>.md` by `pair-map.sh` and reached through the frame's
reference index; here they are content only, and enabling them is a separate
decision. See [`../SETUP-LIST.md`](../SETUP-LIST.md).

## Why they are not skills

Each was authored as a routed prose document with a `**Purpose**:` header, not as
a skill — none carries `name`/`description` frontmatter, so none can fire on its
own triggers. Converting them would mean authoring trigger descriptions, which is
design work on content that was approved as-is. They are kept byte-identical so
that decision stays open and reversible.

Two of them already load conditionally rather than always-on, and say so in their
own text: `PLAN_AUDIT.md` loads only on `call(ExitPlanMode ∧ plan_has_new)`, and
`CEILINGS.md` only once a candidate limiting sentence exists.

`LOGIC_RENDERING.md` is the exception that proves the rule and is **not** here:
it already carried skill frontmatter, so it went to
[`../plugins/logic-rendering/`](../plugins/logic-rendering/) as a real skill
rather than into this directory.

## Contents

| File | Lines | What it carries |
|---|---|---|
| `CRAFT_VS_YAGNI.md` | 136 | Where YAGNI governs and where invoking it is a category error — it kills speculative *architecture*, not clean-code *structure*. |
| `PLAN_AUDIT.md` | 50 | The §6 speculation gate, run against a plan before it is presented. |
| `CEILINGS.md` | 32 | §11 once a limiting claim is in hand: sentences that are never invariants, and the four arguments that get one written anyway. |
| `GITHUB.md` | 70 | GitHub workflow discipline — structured surfaces, native relationships, `gh` CLI over web-API calls. Enforced by [`../plugins/github-utilities/`](../plugins/github-utilities/). |
| `SKILL_AUTHORING.md` | 59 | How to author a skill — defers to the official `skill-creator` plugin for the mechanics. |
| `NEW_REPO_BOOTSTRAP.md` | 50 | What to do on landing in a `~/Developer/` repo that has no `CLAUDE.md`. Paired with [`../plugins/repo-scaffold/`](../plugins/repo-scaffold/). |

## One deviation from verbatim

`GITHUB.md` is the only file here not byte-identical to its source. It linked
twice to its runtime enforcement as `../../../claude-plugins/github-utilities/`,
which resolved inside Standard Configs and not here; both now read
[`../plugins/github-utilities/`](../plugins/github-utilities/) and resolve. Two
lines, paths only — no prose changed. The other three files are unmodified.
