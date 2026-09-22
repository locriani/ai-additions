# session-ledger

**Upstream:** `Standard Configs` (`~/Developer/Standard Configs/claude-plugins/session-ledger/`) — Zach's own machine-bootstrap repo, not an external project
**Install method:** `./apply.py` from that subfolder (deploys a `local.sessionledger` LaunchAgent + `claude-sessions` CLI + SQLite ledger)
**Status:** referenced, not installed.

Durable record of which Claude Code sessions were open at a given time. A
LaunchAgent polls every 60 seconds across every `~/.claude-profiles/*/` config
root plus bare `~/.claude`, recording session lifetimes (`started_at` /
`ended_before`) into `~/.claude/session-ledger/ledger.db`. `claude-sessions at
<time>` (`last-reboot` | `"2h ago"` | a timestamp) answers what was open then
and prints a `cd "<cwd>" && cl <profile> -r <id>` resume line per session;
`--exec` reopens them as iTerm2 tabs.

## Why it is here, and why it does not quite fit

Like `atuin`, this is not a Claude Code plugin — no skill, no hook, no MCP,
nothing `claude plugin install` can register. It is a LaunchAgent + CLI,
machine-resident state.

Unlike everything else in `referenced/`, its source is not an external repo or
package — it *is* Standard Configs. That inverts the direction this repo's own
[`README.md`](../README.md) describes ("Standard Configs will consume this repo
through a thin `external/ai-additions/` stub"): here, ai-additions is pointing
back at Standard Configs rather than the reverse. Recorded anyway because it was
approved by name, and a pointer costs little. Worth revisiting if this repo ever
needs to be usable independent of a Standard Configs checkout — the install
command below only works if `~/Developer/Standard Configs` exists on the
machine.

## Install

```sh
cd "$HOME/Developer/Standard Configs/claude-plugins/session-ledger"
./apply.py
./check.py
```

See that subfolder's own `README.md` for the full runbook, the liveness
predicate the poller uses, and troubleshooting.
