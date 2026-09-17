# chief-of-stuff

**Upstream:** [`locriani/chief-of-stuff`](https://github.com/locriani/chief-of-stuff) (private)
**Local checkout:** `~/Developer/chief-of-stuff`
**Status:** installed and enabled 2026-09-16 (user scope) on "chief of stuff is approved for enabling"; updated to 0.2.0 the same evening (filing moves within PARA, Config rule) and to 0.3.0 (the board: a task list and Gantt artifact rendered from the tracker by `scripts/render_board.py`, republished after every tracker edit); 0.3.1 on 2026-09-17 (the board draws the schedule only: unscheduled lanes fold into summary rows, deadline lines sit on the chart, long item histories open as one line per clause).

A Claude Code plugin that ships one agent, `chief-of-stuff`, meant to run as the
**main session**: `claude --agent chief-of-stuff`. It coordinates the user's day
and does no deep work itself: reads the real clock and the calendars, keeps the
daily log and a per-day tracker (lanes, decisions, file ownership, append-only
log), routes human-only actions to the user, and dispatches work to a new
context only on the user's explicit yes. Pinned to Opus.

## What it needs from a workspace

A `## Coordinator` block in the workspace `CLAUDE.md`: log dir, tracker path,
template, timezone, calendar tool and calendar ids, deadlines, human-only action
classes. The agent never carries workspace values itself; if the block is missing
it proposes one and creates nothing.

## Evals

`evals/run.py` drives real `claude -p` in a sandbox (temp cwd, no user MCP, a
mock calendar server, `railway` and `git commit|add|push` denied). 22 cases,
each red without the agent (two non-discriminating, kept as guards) and green with it on Opus x3. Record:
`evals/results/PROGRESS.md`.

## Install

```sh
claude plugin marketplace add ~/Developer/chief-of-stuff
claude plugin install chief-of-stuff@chief-of-stuff
```

Run 2026-09-16. The installed copy is a version-stamped snapshot under `~/.claude/plugins/cache/`; after editing the checkout, `claude plugin marketplace update chief-of-stuff` and reinstall.
