# datetime-inject

UserPromptSubmit hook. Emits exactly one bracketed line to stdout, which Claude
Code appends to the conversation as context:

```
[Current TimeStamp: Tuesday, June 2nd, 2026 | 2026-06-02 14:33:07 PDT (UTC-07:00)]
```

## Why

The harness already stamps the **date**. It does not carry the wall clock, and
time-of-day is what "before EOD", "overnight", "how long has this been running"
all turn on.

The script takes a single `date(1)` snapshot so every field refers to the same
instant — no cross-call second-skew — and deliberately omits `set -e`, because a
non-zero exit from a UserPromptSubmit hook can block prompt submission. It always
exits 0.

Mutation surface: **none**. It reads the clock, writes one line to stdout, and
ignores its stdin.

## Status

**Not enabled.** Registered in this marketplace, installed nowhere.

## Provenance

From `Standard Configs/claude-plugins/datetime-inject/` at `d36d794`. Script
byte-identical; only its registration moved to `${CLAUDE_PLUGIN_ROOT}`.
