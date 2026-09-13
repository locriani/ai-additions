# extras

Personal skills bundle — five skills, copied verbatim.

| Skill | Lines | What it does |
|---|---|---|
| `code-review` | 195 | Dispatches orthogonal review axes in parallel, triaging tests-that-lie first. Ships a 357-line `CODE_REVIEW.md` rule reference and a `code-reviewer.md` subagent prompt template. |
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

**Not enabled.** Registered in this marketplace, installed nowhere.

## Provenance

From `Standard Configs/claude-plugins/extras/templates/marketplace/extras/skills/`
at `d36d794`. All five skill directories byte-identical.
