# rules/

Prose rule documents, copied **verbatim** from
`Standard Configs/claude-core/claude-md/templates/global/` at `d36d794`.

## Status: present, not deployed

These files are in the repo. Nothing deploys them. In Standard Configs they are
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

## Contents

| File | Lines | What it carries |
|---|---|---|
| `CRAFT_VS_YAGNI.md` | 136 | Where YAGNI governs and where invoking it is a category error — it kills speculative *architecture*, not clean-code *structure*. |
| `PLAN_AUDIT.md` | 50 | The §6 speculation gate, run against a plan before it is presented. |
| `CEILINGS.md` | 32 | §11 once a limiting claim is in hand: sentences that are never invariants, and the four arguments that get one written anyway. |
| `GITHUB.md` | 70 | GitHub workflow discipline — structured surfaces, native relationships, `gh` CLI over web-API calls. |

## Known dangling link

`GITHUB.md` links to `../../../claude-plugins/github-utilities/` for its runtime
enforcement — a Stop hook plus the `gh-issue-rel` CLI. That path resolved inside
Standard Configs and does not resolve here.

The link is left as-authored rather than patched, because `github-utilities` has
**not** been approved for addition. Fixing the link by bringing the hook across
would be adding an unapproved item; rewriting the link to point at nothing would
hide that the rule currently has no enforcement in this repo. When the hook is
approved, the link is repaired by the move. Until then the rule here is prose
without a runtime.
