# frank-lloyd-aight (Frank Lloyd AIght)

**Upstream:** [`locriani/frank-lloyd-aight`](https://github.com/locriani/frank-lloyd-aight) (public)
**Local checkout:** `~/Developer/frank-lloyd-aight`
**Status:** approved 2026-09-17 by plan approval ("general-contradictor, a main-session architecture agent", 12:50 CT); renamed by Zach to Frank Lloyd AIght at 13:24 CT, GitHub repo renamed by him; being built in stages, one red eval case turned green then a pause; not installed, not enabled. Enabling is a separate approval.

A Claude Code plugin that ships one agent, `frank-lloyd-aight`, meant to run as the
**main session**: `claude --agent frank-lloyd-aight`. It reviews the drawings and never
pours the concrete. It reviews and judges
architecture and does not build it: lays the current state out as a numbered review page
(deployed, in flight, designed, and where they disagree), answers "X is correct?" with a
judgment and a staging recommendation, relays settled decisions to the implementer and the
coordinator, owns the project's `architecture/` directory and keeps it canonical, renders every
diagram before approving it, files code defects instead of fixing them, and never commits.
Pinned to Opus.

## What it needs from a workspace

An `## Architecture` block in the workspace `CLAUDE.md`: user and pronouns, architecture
directory, canonical document, plan directory, publisher, coordinator and implementer session
name patterns, diagram renderer path, human-only actions. The agent never carries workspace
values itself; if the block is missing it proposes one and creates nothing.

## Evals

`evals/run.py` is the chief-of-stuff harness copied and stripped, plus a host-side answer
channel for `AskUserQuestion`. Eight cases planned, each red without the agent and green with
it on Opus x3. Record: `evals/results/PROGRESS.md`.

## Install (when enabled)

```sh
claude plugin marketplace add ~/Developer/frank-lloyd-aight
claude plugin install frank-lloyd-aight@frank-lloyd-aight
```

Not run. The installed copy will be a version-stamped snapshot under `~/.claude/plugins/cache/`; after editing the checkout, `claude plugin marketplace update frank-lloyd-aight` and reinstall.
