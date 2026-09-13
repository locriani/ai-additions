-- skill-perf ledger schema — SINGLE SOURCE OF TRUTH for the table DDL.
--
-- Read by BOTH init-ledger-db.py (apply time) and skill-perf-ledger.py (the Stop
-- hook, defensively at runtime). Deployed to ~/.claude/skill-perf/schema.sql so
-- every writer reads the same DDL from one stable path — no copy-pasted CREATE
-- TABLE drifting between scripts (per Standard Configs CLAUDE.md §7).
--
-- Column ownership:
--   * mechanical block  — written ONCE by the Stop hook the turn the skill is used.
--   * judge-owned block — NULL until the on-demand LLM judge scores the row
--                         (completion + success + span tokens + adherence/compliance).
--                         "Successful completion" is judge-determined (design choice C3).

CREATE TABLE IF NOT EXISTS skill_uses (
  id                     INTEGER PRIMARY KEY,

  -- identity / dedupe (a skill use is unique per (turn_uuid, tool_use_id))
  session_id             TEXT NOT NULL,
  turn_uuid              TEXT NOT NULL,
  tool_use_id            TEXT NOT NULL,

  -- what skill
  skill_name             TEXT NOT NULL,     -- e.g. "design:design-system"
  args_hash              TEXT,              -- sha256(input.args); raw args never stored

  -- mechanical metrics — written by the Stop hook
  invocation_ts          TEXT NOT NULL,     -- ISO8601 ms, assistant msg bearing the Skill tool_use
  first_token_latency_ms INTEGER,           -- (next assistant ts) - (tool_result ts)
  output_tokens          INTEGER,           -- usage of the immediate post-skill assistant turn
  input_tokens           INTEGER,
  cache_tokens           INTEGER,           -- cache_creation + cache_read
  model                  TEXT,
  cwd                    TEXT,
  git_branch             TEXT,

  -- judge-owned (C3) — NULL until judged
  completion_ts          TEXT,
  completion_ms          INTEGER,           -- invocation_ts -> completion_ts, judge-determined
  success                INTEGER,           -- 0/1, judge verdict on the skill-driven work
  span_total_tokens      INTEGER,           -- sum of usage across the judged completion span
  judge_adherence        REAL,              -- 0.0..1.0 — did the OUTCOME meet the skill's purpose
  judge_compliance       REAL,              -- 0.0..1.0 — did Claude FOLLOW the skill's instructions
  judge_notes            TEXT,
  judge_model            TEXT,
  judged_at              TEXT,

  -- bookkeeping
  created_at             TEXT NOT NULL,

  UNIQUE(turn_uuid, tool_use_id)
);

CREATE INDEX IF NOT EXISTS idx_skill_perf_skill    ON skill_uses(skill_name);
CREATE INDEX IF NOT EXISTS idx_skill_perf_unjudged ON skill_uses(judged_at);
