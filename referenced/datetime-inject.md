# datetime-inject

**Upstream:** [`locriani/datetime-inject`](https://github.com/locriani/datetime-inject) (public) —
split out of this repo 2026-10-10; CI green at head `1c31f72`.
**Status:** approved 2026-09-13 on *"pending list so far is approved"*; enabled 2026-09-16 on
*"datetime-inject logic-rendering are approved for enabling"* — see `SETUP-LIST.md`. Extracted
2026-10-10 from [`locriani/ai-additions`](https://github.com/locriani/ai-additions) at `a01d7eb`,
history carried with the extraction; the row moved from the Plugins table to Referenced with
wording unchanged. Plugin id and version are unchanged (1.0.0 at extraction).

A UserPromptSubmit hook that injects the current *local* date and time into context once per turn,
as a single bracketed line — human long-form plus ISO machine form, e.g.
`[Current TimeStamp: Tuesday, June 2nd, 2026 | 2026-06-02 14:33:07 PDT (UTC-07:00)]`. The harness
stamps the date but not the wall clock, and "before EOD" and "overnight" turn on time of day. One
`date(1)` snapshot per turn so every field agrees.

## Install

```sh
claude plugin marketplace add locriani/datetime-inject
claude plugin install datetime-inject@datetime-inject
```

The installed copy is a version-stamped snapshot under `~/.claude/plugins/cache/`; after a new
release, `claude plugin marketplace update datetime-inject` and reinstall.
