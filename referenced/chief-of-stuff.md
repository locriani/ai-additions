# chief-of-stuff

**Upstream:** [`locriani/chief-of-stuff`](https://github.com/locriani/chief-of-stuff) (private)
**Local checkout:** `~/Developer/chief-of-stuff`
**Status:** referenced, not installed.

A Claude Code plugin that ships one agent, `chief-of-stuff`, meant to run as the
**main session**: `claude --agent chief-of-stuff`. It coordinates the user's day
and does no deep work itself: reads the real clock and the calendars, keeps the
daily log and a per-day tracker (lanes, decisions, file ownership, append-only
log), routes human-only actions to the user, and dispatches work to a new
context only on the user's explicit yes. Pinned to Opus.

## What it needs from a workspace

A `## Coordinator` block in the workspace `CLAUDE.md`: log dir, tracker path,
template, timezone, calendar tool and calendar ids, deadlines, human-only action
classes. The agent never carries workspace values itself.

## Evals

`evals/run.py` drives real `claude -p` in a sandbox (temp cwd, no user MCP, a
mock calendar server, `railway` and `git commit|add|push` denied). 15 cases,
each red without the agent and green with it on Opus x3. Record:
`evals/results/PROGRESS.md`.

## Install (when enabled)

```sh
claude plugin marketplace add ~/Developer/chief-of-stuff
claude plugin install chief-of-stuff@chief-of-stuff
```

Nothing above has been run.
