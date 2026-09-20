# auditor (working name)

**Upstream:** none yet — local only. `locriani/auditor` when Zach says so; precedent is
`frank-lloyd-aight` public and `chief-of-stuff` private.
**Local checkout:** `~/Developer/auditor`
**Status:** approved and enabled 2026-09-15 as `codebase-audit`, a plugin in this repo (see
`SETUP-LIST.md`). Extracted to its own repo 2026-09-19 and renamed, plugin id `codebase-audit` →
`auditor`, version 1.4.2 → 2.0.0. The six commits of its history came out with it via
`git subtree split`. **The name is provisional** — Zach, 2026-09-19: *"just call it Auditor for
now."* Installed from the new marketplace at 2026-09-19 21:05 on *"CIMP it"*, user scope, 2.0.0,
with `test_probe.sh` green on main first (179 passed, 0 failed, 2 skipped).

A Claude Code plugin that ships the `auditor` agent and the `codebase-audit` skill. It assesses a
codebase somebody else wrote, before work gets built on top of it: nine axes, severity from a
published matrix rather than felt, and a dedicated pass for the silent-success class — the defect
where exit status says success and only the output reveals the problem. Its one rule is *operate
the system, cite what it did, and name what each finding forbids you to build*; a finding with no
evidence is dropped, and a finding that constrains nothing downstream is decoration.

`skills/codebase-audit/scripts/probe.sh` collects the evidence in one pass so nine axes do not
re-derive the same twelve facts. It treats the target as untrusted: no configuration the target
ships is executed without `--run-toolchains`, and the host's containers are not enumerated without
`--host-containers`.

## What it needs from a workspace

Nothing. Unlike `chief-of-stuff` and `frank-lloyd-aight` it reads no block from the workspace
`CLAUDE.md` — the target directory is the only input, and every path it writes is a bundle
directory the operator names.

## Evals

None. It has `dev/mutations.py` and `dev/run_mutations.sh`, which prove the probe's own tests fail
when the probe is wrong, but no harness driving real `claude -p` the way the other two sidecars
have. Porting that harness is unplanned work, not a gap being tracked as nearly done.

## Install

```sh
claude plugin marketplace add ~/Developer/auditor
claude plugin install auditor@auditor
```

The installed copy is a version-stamped snapshot under `~/.claude/plugins/cache/`; after editing
the checkout, `claude plugin marketplace update auditor` and reinstall.
