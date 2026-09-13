# skill-perf

A ledger of what skills actually cost, and whether they helped.

## Why

Skills get invoked constantly and nothing measures whether they earn it. This
splits the question in two:

- **Capture is free.** A Stop hook is a pure observer — it logs each `Skill`
  invocation's mechanical cost (tokens, first-token latency, model) into SQLite
  at zero token overhead.
- **Judgement is deliberate.** A UserPromptSubmit hook nudges every 25 turns to
  score the unscored rows, and an LLM judge rates what a machine cannot:
  adherence (did the outcome meet the skill's purpose), compliance (were its
  instructions followed), time-to-completion, success.

Keeping them apart is the design. Judging inline would put a token cost on every
skill use and defeat the measurement.

## Two halves, two plugins

The judge is the [`skill-perf-judge`](../extras/skills/skill-perf-judge/) skill,
which ships in [`extras`](../extras/). **Enabling this plugin alone gives you
capture with nothing to score the rows.** That split is upstream's, preserved
here because both were approved as described.

## Enabling takes more than installing

The scripts run from `${CLAUDE_PLUGIN_ROOT}`, but the ledger is per-machine data
and its paths are hardcoded to `~/.claude/skill-perf/`:

- `init-ledger-db.py` creates and migrates `~/.claude/skill-perf/ledger.db`, and
  reads its DDL from `~/.claude/skill-perf/schema.sql` — so `scripts/schema.sql`
  has to be deployed there first.
- `skill-perf-judge-reminder.py` keeps its turn counter in
  `~/.claude/skill-perf/reminder-state.json`.

Installing the plugin wires the hooks; it does not create the database. Both
steps are needed, in that order. The scripts are byte-identical to source and
have deliberately **not** been rewritten to run out of the plugin directory —
the ledger is data and belongs in `~/.claude`, not inside a plugin that a
reinstall could replace.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere, and no
database has been created.

## Provenance

From `Standard Configs/claude-plugins/skill-perf/templates/` at `d36d794`. All
twelve scripts byte-identical; `install-prompt.md` and `settings-snippet.json`
were left behind as Standard Configs machinery, replaced by `hooks/hooks.json`.
