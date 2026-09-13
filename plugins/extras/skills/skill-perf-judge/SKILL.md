---
name: skill-perf-judge
description: Use when the skill-perf ledger has unscored invocations to score — the reminder fired, or the user asks to judge/score skill uses — because each row needs its own subagent reading the span against the skill's own rules. Do NOT use for the mechanical capture, which the Stop hook already owns.
---

# skill-perf-judge

Drives the on-demand LLM-judge half of the skill-perf ledger (`~/.claude/skill-perf/`). The Stop hook already captured the **mechanical** columns (tokens, latency, model) for free; this skill fills the **judge-owned** columns a machine can't — adherence, compliance, success, and the completion point — then shows the per-skill rollup.

## Execution model — DELEGATE ONE SUBAGENT PER ROW

Do NOT judge rows in the top-level session. Each row needs a full transcript-span read + the skill's own `SKILL.md` + reasoning — judging inline would bloat context. The top-level session is an **orchestrator**:

1. **Sweep the never-judgeable rows FIRST.** A row is only judgeable while its session transcript still exists; once `cleanupPeriodDays` ages the transcript out, the span is gone and the row can never be scored. Dispatching an LLM judge at such a row just burns tokens to SKIP. Retire them cheaply (no model) before enumerating:

   ```bash
   /usr/bin/python3 ~/.claude/skill-perf/sweep-unjudgeable.py --apply
   ```

   This marks each transcript-gone pending row **unjudgeable** (a terminal state: it leaves the backlog and is excluded from the quality averages). Rows whose transcript still exists are untouched. Relay the retired count to the user.

2. **Enumerate** the oldest still-judgeable rows. Default cap is **10**; if the user named a count, use that as the `LIMIT`. Run:

   ```bash
   /usr/bin/python3 - <<'PY'
   import sqlite3, pathlib, json
   db = pathlib.Path.home() / ".claude" / "skill-perf" / "ledger.db"
   if not db.exists():
       print("[]"); raise SystemExit
   con = sqlite3.connect(str(db)); con.row_factory = sqlite3.Row
   rows = con.execute(
       "SELECT id, skill_name FROM skill_uses "
       "WHERE judged_at IS NULL ORDER BY invocation_ts LIMIT 10"
   ).fetchall()
   print(json.dumps([dict(r) for r in rows]))
   PY
   ```

   (Swap `LIMIT 10` for the requested count.) If the result is `[]`, tell the user there's nothing left to judge and stop — do not dispatch anything.

3. **Dispatch one `general-purpose` subagent per row, in parallel** — put all the Agent calls in a SINGLE message so they run concurrently. Give each subagent the `## Subagent payload` below verbatim, with `<ID>` and `<SKILL_NAME>` substituted for that row.

4. **Collect** the one-line verdicts, then run the rollup and relay it verbatim:

   ```bash
   /usr/bin/python3 ~/.claude/skill-perf/skill-perf-stats.py
   ```

   Close with: `judged N · retired R (unjudgeable) · M still unjudged this run` (re-run to drain the rest), followed by the rollup table. No reformatting of the table.

## Subagent payload

You are an **adversarial** judge scoring ONE skill invocation in the skill-perf ledger. Be skeptical: when uncertain, score LOWER. Do not reward effort or politeness — only whether the skill did its job.

Row: `id=<ID>`, skill=`<SKILL_NAME>`.

1. **Get the post-invocation span** (the assistant actions that followed the skill, each with `ts` + `usage`, plus the row's `invocation_ts`):
   ```bash
   /usr/bin/python3 ~/.claude/skill-perf/extract-span.py --id <ID>
   ```
2. **Resolve + read the skill's own definition** — this is your ground-truth rubric (the skill's STATED purpose + instructions):
   ```bash
   /usr/bin/python3 ~/.claude/skill-perf/resolve-skill-md.py "<SKILL_NAME>"
   ```
   It prints one path; `Read` it.
3. **Score four dimensions** from the span vs the SKILL.md:
   - **adherence (0.0–1.0)** — did the OUTCOME meet the skill's stated purpose? About RESULTS. 1.0 = fully did what the skill exists to do; 0 = purpose unmet/ignored.
   - **compliance (0.0–1.0)** — did the agent FOLLOW the skill's instructions / steps / discipline? About PROCESS, independent of outcome. Lower for each skipped step, violated red-flag, or ignored required workflow.
   - **success (0 or 1)** — did the skill-driven work actually complete the user's underlying need? Binary.
   - **completion point** — the `index` (from the extract-span output) of the last span turn clearly part of the skill-driven work, before the user redirected or the task moved on. You **only choose the index** — do NOT compute timestamps or sum tokens. `record-judgement.py` derives `completion_ts` / `completion_ms` / `span_total_tokens` from the index via `span_lib`. Each span turn already shows its own `elapsed_ms` + `cumulative_tokens` if you want to sanity-check, but pass the **index**, never the numbers.
4. **Record the verdict** (the single validated write path; it does the completion math):
   ```bash
   /usr/bin/python3 ~/.claude/skill-perf/record-judgement.py --id <ID> \
     --adherence <A> --compliance <C> --success <0|1> \
     --completion-index <K> \
     --model <your-model-id> --notes "<≤1 sentence: why these scores>"
   ```
   `<K>` is the chosen span index. If the work never completed within the span, set `--success 0` and **omit** `--completion-index` (the completion columns stay NULL).
5. **Return EXACTLY one line**, nothing else:
   `id=<ID> <SKILL_NAME>: adherence=<A> compliance=<C> success=<0|1> (<≤8-word reason>)`

**If `extract-span.py` fails because the transcript is gone** (message contains "no transcript for session"): the row can never be scored. Do NOT leave it pending — retire it so it stops re-entering the backlog:
```bash
/usr/bin/python3 ~/.claude/skill-perf/record-judgement.py --id <ID> \
  --unjudgeable --reason "no transcript for session" --model <your-model-id>
```
then return `id=<ID> <SKILL_NAME>: UNJUDGEABLE (no transcript)`. (Step 1's sweep normally catches these first; this handles a transcript that aged out mid-run.)

**If `resolve-skill-md.py` fails** (the SKILL.md can't be located — a transient/fixable condition, NOT terminal): do NOT guess and do NOT retire the row. Record nothing and return `id=<ID> <SKILL_NAME>: SKIPPED (no SKILL.md)` so a later run can retry once the skill resolves.

## Red flags — judge rationalizations

| Thought | Checksum | Reality |
|---|---|---|
| "The agent seemed helpful — give it 0.9." | `↑proxy ↛ ↑target` | Adherence measures whether the skill's PURPOSE was met, not vibes. Re-read the SKILL.md purpose and check the span against it. |
| "It mostly followed the steps." | `felt(P) ↛ tested(P)` | "Mostly" is not 1.0. Each skipped or violated step lowers compliance. Name the gap in `--notes`. |
| "Adherence and compliance feel the same." | `compliance ⊥ adherence` — independent axes | They diverge: a skill can be followed to the letter (high compliance) yet miss its purpose (low adherence), and vice-versa. Score independently. |
| "I'll compute completion_ms / sum the span tokens myself." | `owner(math) = span_lib ≠ you` | Don't. Pass only `--completion-index`; `span_lib` owns the math. LLM arithmetic over timestamps + token sums is exactly the error this design removes. |
| "Can't tell where it completed — I'll include the whole span." | `¬obs(end) ↛ end = span_end`; `¬completed ⊢ success = 0` | Don't pad the window. Pick the index of the last turn clearly on-task; if the work never completes, `--success 0` and omit `--completion-index`. |
| "I'll judge all the rows myself to save agents." | `∀row: 1 subagent` — batching ⊢ ¬isolation | No — one subagent per row. Batched judging in one context defeats the isolation this skill is built on. |
| "The transcript is gone — I'll just SKIP and record nothing." | A silent SKIP leaves the row pending forever, so it re-enters the backlog and the reminder every run. Mark it `--unjudgeable` (terminal) instead. |
| "I'll guess scores from the skill name since the span is missing." | Never fabricate a verdict without the span. No transcript → `--unjudgeable`, not an invented adherence/compliance. |
