# stack-profiles

**Upstream:** [`locriani/stack-profiles`](https://github.com/locriani/stack-profiles) (public) — split
out of this repo 2026-10-10; CI green at head `6764ed9`.
**Status:** approved 2026-09-13 on *"pending list so far is approved"*, kept to side — never enabled
here; enabling needs the deployment step below plus its own approval. See `SETUP-LIST.md`. Extracted
2026-10-10 from [`locriani/ai-additions`](https://github.com/locriani/ai-additions) at `a01d7eb`,
history carried with the extraction; the row moved from the Plugins table to Referenced with
wording unchanged. Plugin id and version are unchanged (1.0.0 at extraction).

Eleven per-stack rule addenda — Swift/Apple, bash scripts, Python/uv, Node/TypeScript,
Postgres/SQL, Rust, Go, React/Vite, Rails, Terraform, Kubernetes — plus a SessionStart hook
(`stack-detect.py`) that detects the repo's stack and loads only the matching profile: one profile's
context cost, not eleven. Deployment is a second step: the profiles are copied to
`~/.claude/stacks/` (the plugin README says so).

## Install

```sh
claude plugin marketplace add locriani/stack-profiles
claude plugin install stack-profiles@stack-profiles
```

The installed copy is a version-stamped snapshot under `~/.claude/plugins/cache/`; after a new
release, `claude plugin marketplace update stack-profiles` and reinstall.
