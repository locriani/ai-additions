# bug-hunt

**Upstream:** [`locriani/bug-hunt`](https://github.com/locriani/bug-hunt) (public) — split out of this
repo 2026-10-10; CI green at head `0dee59d` (24 tests).
**Status:** approved 2026-09-26 on *"bug-hunt is approved for addition"* (Zach, 18:06), after the plan
was approved in plan mode; enabled the same evening on *"commit, merge, install, approved for
enablement"* at 0.1.0; updated to 0.1.1 on *"do it"* after a security review flagged unsandboxed
Bash — see `SETUP-LIST.md` for the full row. Extracted 2026-10-10 from
[`locriani/ai-additions`](https://github.com/locriani/ai-additions) at `a01d7eb`, history carried
with the extraction and authorship preserved; the row moved from the Plugins table to Referenced
with wording unchanged. Plugin id and version are unchanged (0.1.1 at extraction).

A headless, repo-agnostic bug hunt. Finder prompts read the hottest files from five angles; provers
write a repro that must fail against the current code; a verifier must turn it green with a fix
before a bug is reported. `bin/bug-hunt run` wraps `claude -p` in a throwaway git worktree at HEAD
with a spend cap, reports Markdown and JSON, and exits 1 when proven bugs exist. Report only — it
never fixes in place — and since 0.1.1 its Bash runs in a fail-closed sandbox.

## Install

```sh
claude plugin marketplace add locriani/bug-hunt
claude plugin install bug-hunt@bug-hunt
```

The installed copy is a version-stamped snapshot under `~/.claude/plugins/cache/`; after a new
release, `claude plugin marketplace update bug-hunt` and reinstall.
