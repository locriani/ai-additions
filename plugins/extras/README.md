# extras

Personal skills bundle — five skills. Four are copied verbatim; `code-review` has been extended locally (see Provenance).

| Skill | Lines | What it does |
|---|---|---|
| `code-review` | 195 | Dispatches orthogonal review axes in parallel, triaging tests-that-lie first. Ships a 237-line `CODE_REVIEW.md` catalog and dispatch reference, a `code-reviewer.md` subagent prompt template, and 22 one-file-per-persona definitions under `personas/` so each subagent loads only its own lens and checks. |
| `time-estimation` | 227 | Hours spent — inferred from commit clustering, not read off a log. |
| `defect-density` | 201 | Bug rate and escaped-to-production count, correlated against churn over a window. |
| `dev-velocity` | 116 | Output rate — churn measured over a window. |
| `skill-perf-judge` | 102 | The LLM-judge driver for the `skill-perf` ledger: one subagent per unscored row, read against that skill's own rules. |

The three measurement skills are mutually exclusive by construction — each
description routes explicitly away from the other two.

## `skill-perf-judge` lives here, not in `skill-perf`

It is the judging half of the [`skill-perf`](../skill-perf/) ledger, and the two
are useless apart: the ledger captures rows nothing scores, and the judge has
nothing to read.

They are nonetheless separate plugins, because that is how they were separated
upstream and both were approved as described. Enabling one without the other
gives you a working half. Noted in [`../../SETUP-LIST.md`](../../SETUP-LIST.md).

## Status

**Enabled** at user scope (1.1.0, 2026-09-24), all five skills, from the local marketplace. Approved for `code-review`; the bundle comes with it.

## Provenance

From `Standard Configs/claude-plugins/extras/templates/marketplace/extras/skills/`
at `d36d794`. `time-estimation`, `defect-density`, `dev-velocity` and `skill-perf-judge` are byte-identical.

`code-review` diverges from upstream (1.1.0, 2026-09-24):

- Personas 12 and 14 are named: **Boris Cherny** (AI-pilled, agent-first, terse; fifth check added) and **Kyle Kingsbury** (Jepsen-style; fifth check added).
- Six personas added as 16–21 (Steve Jobs moves to 22): **Thomas Ptacek** (security), **Joshua Bloch** (API design), **Kent Beck** (tests), **Brendan Gregg** (performance), **Leslie Lamport** (invariants), **Léonie Watson** (accessibility). Approval recorded in [`../../SETUP-LIST.md`](../../SETUP-LIST.md).
- Per-persona sections moved out of `CODE_REVIEW.md` into `skills/code-review/personas/NN-name.md`; the prompt template now points each agent at its own file.

Re-sync from upstream will need this merged by hand.
