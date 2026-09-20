# Setup list

The authoritative record of what this repo installs, and what it does not.

## The rule

**Nothing enters this repo without explicit approval from Zach.**

Approval means a specific statement — *"X is approved for addition"* or similar
wording that names the item and grants it. It is **not** implied by:

- discussing an item, however favourably
- listing it as something wanted, or asking for it to be scoped
- an item being obviously useful, already written, or already working elsewhere
- a previous approval of a related or adjacent item

An item that has been discussed but not stated is **Pending**, and Pending items
are not built, not copied in, and not registered in `marketplace.json`.

This file is the ledger. Move a row between tables only when the approval phrase
has actually been given, and record the wording that granted it.

## Approved

"Keep to side" was settled on 2026-09-13: **added to this repo, not enabled for
Claude Code.** Present, versioned, registered where a marketplace entry applies —
but installed nowhere and switched on nowhere. Enabling each is a separate
approval, and for several it is more than one step (see the notes).

One exception stands: `mermaid-system-design` was enabled on 2026-09-15, on the instruction
"add / register in ai-additions" given while it was already loaded and working as a personal
skill. Registering it without enabling it would have removed a working skill, so it went in
switched on.

A second exception followed on 2026-09-15: `codebase-audit` was approved and enabled in the same
instruction, because the instruction was to build the skill *and* run it — "then use it to produce
AUDIT.md" — and keep-to-side would not have satisfied it. Approval named the item as `emr-audit`;
the name was changed to `codebase-audit` during the same exchange, on Zach's ruling that the tool
is general rather than EMR-specific. Recorded under the name it actually ships as, since a ledger
row pointing at a directory that does not exist is worse than an imprecise quote.

It has since been renamed a second time. On 2026-09-19 it was extracted to a sidecar repo and its
plugin id became `auditor`, so its row now sits in **Referenced** rather than **Plugins** and this
repo no longer carries the code. By the same rule as the first rename, the row reads `auditor` and
the wording that granted it is unchanged. The name is provisional — *"just call it Auditor for
now"* — and a third rename is expected.

Every other row is still keep-to-side.

### Plugins — `plugins/`, registered in `marketplace.json`

| Item | Approved | Wording | Enabled |
|---|---|---|---|
| `worktree-guard` | 2026-09-13 | "as well as ... worktree-guard" | No |
| `github-utilities` | 2026-09-13 | "oh add github utilities" | No |
| `datetime-inject` | 2026-09-13 | "pending list so far is approved" | **Yes** — 2026-09-16, "datetime-inject logic-rendering are approved for enabling": `claude plugin install datetime-inject@ai-additions` (user scope, 1.0.0) |
| `logic-rendering` | 2026-09-13 | "pending list so far is approved" | **Yes** — 2026-09-16, "datetime-inject logic-rendering are approved for enabling": `claude plugin install logic-rendering@ai-additions` (user scope, 1.0.0) |
| `skill-perf` | 2026-09-13 | "pending list so far is approved" | No |
| `extras` | 2026-09-13 | "pending list so far is approved" | No |
| `stack-profiles` | 2026-09-13 | "pending list so far is approved" | No |
| `repo-scaffold` | 2026-09-13 | "pending list so far is approved" | No |
| `prd-design` | 2026-09-15 | plan "prd-design — and the four around it" approved | No |
| `mermaid-system-design` | 2026-09-15 | "add / register in ai-additions" | **Yes** — installed from the local marketplace |

### Rules — `rules/`, copied verbatim, deployed nowhere

| Item | Approved | Wording | Enabled |
|---|---|---|---|
| `CRAFT_VS_YAGNI` | 2026-09-13 | "CRAFT_VS_YAGNI - add, but keep to side" | **Deployed** — 2026-09-16, "install CRAFT_VS_YAGNI, PLAN_AUDIT, CEILINGS": copied verbatim to `~/.claude/CRAFT_VS_YAGNI.md`. Inert until a `~/.claude/CLAUDE.md` references it; none exists on this machine |
| `PLAN_AUDIT` | 2026-09-13 | "as well as plan audit" | **Deployed** — 2026-09-16, "install CRAFT_VS_YAGNI, PLAN_AUDIT, CEILINGS": copied verbatim to `~/.claude/PLAN_AUDIT.md`. Inert until a `~/.claude/CLAUDE.md` references it; none exists on this machine |
| `CEILINGS` | 2026-09-13 | "as well as ... ceilings" | **Deployed** — 2026-09-16, "install CRAFT_VS_YAGNI, PLAN_AUDIT, CEILINGS": copied verbatim to `~/.claude/CEILINGS.md`. Inert until a `~/.claude/CLAUDE.md` references it; none exists on this machine |
| `GITHUB` | 2026-09-13 | "as well as ... github" | No |
| `SKILL_AUTHORING` | 2026-09-13 | "pending list so far is approved" | No |
| `NEW_REPO_BOOTSTRAP` | 2026-09-13 | "pending list so far is approved" | No |

### Referenced — `referenced/`, pointers only, nothing cloned or installed

| Item | Approved | Wording | Enabled |
|---|---|---|---|
| `asking-protocol` | 2026-09-13 | "pending list so far is approved" | No — MCP to stay **disabled** |
| `reference-points` | 2026-09-13 | "pending list so far is approved" | **Yes** — 2026-09-16, "reference-points, claude-statusline, atuin, security-guidance, are approved for enabling": `claude plugin marketplace add locriani/reference-points` + `claude plugin install reference-points@reference-points` (user scope) |
| `claude-statusline` | 2026-09-13 | "also add the entry for the statusline for claude code please" | **Yes** — 2026-09-16, "reference-points, claude-statusline, atuin, security-guidance, are approved for enabling": `~/Developer/claude-statusline/launchd/install.sh` (release build, binaries in `~/.local/bin`, `~/.claude/statusline` symlink, LaunchAgent `local.claude-statusline.collector` running) |
| `atuin` | 2026-09-13 | "add atuin to the new set" | **Yes** — 2026-09-16, "reference-points, claude-statusline, atuin, security-guidance, are approved for enabling": already `brew install`ed (18.22.0); `eval "$(atuin init zsh)"` appended to `~/.zshrc`; `atuin import auto` (344 entries) |
| `security-guidance@claude-plugins-official` | 2026-09-13 | "let's add security-guidance@claude-plugins-official and superpowers@" | **Yes** — 2026-09-16, "reference-points, claude-statusline, atuin, security-guidance, are approved for enabling": `claude plugin install security-guidance@claude-plugins-official` (user scope) |
| `superpowers@claude-plugins-official` | 2026-09-13 | same | No |
| `mattpocock-skills` | 2026-09-15 | plan "prd-design — and the four around it" approved | No |
| `yoke` | 2026-09-15 | plan "prd-design — and the four around it" approved | No |
| `terminalskills` | 2026-09-15 | plan "prd-design — and the four around it" approved | No |
| `chief-of-stuff` | 2026-09-16 | "Ok then create this as a sidecar repo like reference-points that will get referred to in ai-additions." | **Yes** — 2026-09-16, "chief of stuff is approved for enabling": `claude plugin marketplace add ~/Developer/chief-of-stuff` + `claude plugin install chief-of-stuff@chief-of-stuff` (user scope, 0.1.0; updated to 0.2.0 2026-09-16 on "commit, update, install"; to 0.3.0 the same evening on "deploy, merge, commit, whatever, including enablement"; to 0.3.1 2026-09-17 on "commit and merge and install is approved"; to 0.4.0 the same morning on "commit and continue" and "go ahead and push and install as well"; to 0.4.1 the same morning on "CIP when complete"; to 0.4.2 on "amazing. CIP"; to 0.4.3 on "please incorporate this logo and color scheme"; to 0.5.0 2026-09-17 on "CIP when green"; to 0.6.0 the same evening on "cip"; to 0.6.1 2026-09-18 on "fix 45 and plan C4 with 48"; to 0.6.2 the same night on "assume the plan is approved when it's done, CIP"; to 0.7.0 the same night on "assume the plan is approved when it's done, CIP, then go into the next planning phase"; to 0.8.0 2026-09-18 on "finish out this feature and then CIP" and "CIP on completion"; to 0.8.1 the same day under the same "CIP on completion", fixing a rule so scripts are read from ${CLAUDE_PLUGIN_ROOT} and never from the canonical dev tree; to 0.9.0 the same day on "I asked you to proceed through each bullet for this one until CIP" and "CIMP" — the session graph, the Lanes/Sessions join, and the first release under house rule 5, merged to main with the suite run on main afterwards; 0.9.1 the same day on "back out the colorblind changes for now … do this as an immediate step, install, deploy" — every fill flat again, the graph caption removed, 433 on main at de82ecd; 0.10.0 the same day on the approved C7 plan — derived estimates for owned lanes and folds that open onto sublane rows, 449 on main at 7daf71f, 6/6 agent-arm cases green; 0.10.1 the same day on the approved C8 plan — a lint over every eval case, mock peers minutes, the page's charset, the Verified reporting sentence, 460 on main at 02e89b2). Sidecar `locriani/chief-of-stuff` (private), checkout `~/Developer/chief-of-stuff` 0.11.0 installed 2026-09-19 00:41 (Zach: "install immediately please for a regen of the view"): a `size` column on Lanes, `done HH:MM–HH:MM` keeps the running start, estimates from per-size history with the 0.10.0 queue-drain as the labelled fallback, and `named lanes only` on a deadline line (findings 73, 77, 78). 0.11.1 installed 2026-09-19 01:00: a size arrives with its row, never in a move about another lane (finding 79; two reruns red, 3/3 green on the fix; 486 on main at ccabe88). 0.11.2 installed 2026-09-19 01:27: inline marks render and a mark pair is a span the cuts respect (finding 98); `gone` never reaches the Sessions state cell (finding 99, graded on orphaned-owner 3/3); 497 on main at 43fab18. 0.11.3 installed 2026-09-19 02:30 on the approved C12 plan: a table cell is a span too — `\|` and a pipe inside a backtick span are pipes, and an over-wide Lanes row is re-read from its state cell (finding 100; the live board's one malformed row had been hiding a closed L lane's 68 minutes from the estimator); new case `pipe-escaped-in-a-lane` 3/3, `board-republish-on-lane-change` green; 510 on main at c41c83b. 0.12.0 installed 2026-09-19 03:52 on the approved C13 plan, run as tracer bullets on Zach's "you have authorization to complete all tracer bullets without pausing": the assignment every dispatched session receives now carries grants as sharply as its prohibitions — two categories and no third, a flagged problem in your own paths is your assignment, the two errors priced — and `Write only: do not commit or push.` becomes his actual rule, commit small and never merge; a stop is an artifact at `.chief-of-stuff/stop.md` in four kinds that `audit_lanes.py` reads and counts into its exit code; the decision queue is audited the same way (findings 101–104). 559 on main at dbf2825. 0.12.1 installed 2026-09-19 04:00, two follow-ons taken under the rule 0.12.0 shipped (revertible, this repo, one of them blocking another session): `evals/run.py` named `claude` bare, so a GUI-launched tab could grade no eval case at all and board-ux's were stranded (finding 105); and the background security review caught the new stop reader failing open on an unreadable file and printing session-written fields into the terminal unguarded (finding 106). 575 on main at 93b4f56. 0.12.2 installed 2026-09-19 04:06: the assignment header carries house rule 3 to every dispatched session and tells it to carry the rule into anything it spawns (finding 91's revertible half; the workspace `CLAUDE.md` line stays Zach's), and tells a session told it overstepped to name the line and say where it comes from before accepting — impl-2's finding that capitulating to a confidently stated rule is the same failure as ignoring a well-founded one (findings 107, 108). 582 on main at 2d58eb8. 0.12.3 installed 2026-09-19 04:22: the audit's `main` line resolved the worktree's `HEAD` rather than `main`, so it named a branch tip while its unpushed count — which resolves the ref correctly — was right, on the one line the CIMP `Verified` gate rests on (finding 109, reported by gauntlet-b2 and verified here against the live trees before it was taken). 596 on main at 7f254a7. 0.12.4 installed 2026-09-19 06:02: every report a dispatched session sends ends naming one of two states — the one thing it is starting now, or `idle and available` — and never neither, because writing up what you did is not doing the next thing and the two are identical from inside (finding 111, arch's account of its own eighty-minute stop; a third failure class that neither 101 nor 108 reaches). 606 on main at 0ca5e43. 0.12.5 installed 2026-09-19 06:14: the lane audit joins File ownership to `## Sessions` on the `[ref]` where both cells carry one, the name deciding only when there is none — a ref is minted once and survives a rename, a name is a tab title, and one rewritten at 03:21 made the sweep call a live session's tree orphaned five minutes after it had committed there (finding 112, reported by gauntlet-b2, which filed it as decision A24 rather than editing a row to silence it). 611 on main at d83755e. 0.12.6 installed 2026-09-19 06:23: the same ref rule reaches `owns()`, the join that attributes a lane to an ownership row and so to a tree — 0.12.5 had put it in the roster join and stopped at the edge of the one that mattered. The tracker writes `impl-1 [4cd339]` in the lane owner column and `standing-task-implementer [4cd339]` in File ownership, the same for five other sessions, so twenty-three `done` lanes matched no row and a lane with no tree is checked for nothing at all (finding 115, spotted by gauntlet-b2 in an A/B run it was reading for something else). Live A/B in the same minute: reopen=2 before, reopen=8 after, the six being real lanes marked done whose branches are not on main. 615 on main at 291fc45. 0.12.7 installed 2026-09-19 07:03: the lane audit renders one reopen line per fact instead of one per lane — `visit()` asks git once per tree and fanned that single answer across every lane the tree owned, so thirteen lines on the live tracker carried three facts and the ratio got worse as a session closed more lanes in one worktree. Rendering only: detection, the finding list and the exit code are untouched, every tree still flagged and every lane still named, no existing test moved, and the live invariant checked at thirteen names before and after (finding 116c, from gauntlet-b2 by way of board-ux-improvements, which declined to build it in this lane's active file). It exposed a latent defect it did not cause: `short_name` cuts inside a `**` pair, so six grouped lanes rendered as six ellipses — unmark first. 621 on main at 78d5eab. 0.12.8 installed 2026-09-19 07:59: an eval run is a verdict on a snapshot and writes down what it decided. The allowlist carried absolute paths into the live checkout and so did `--plugin-dir` — six exposures, not five, the agent definition being as much a mid-run moving part as the scripts — so a sweep read whatever was on disk when each case reached it and silently held that tree read-only, a merge included. One copy per sweep under `evals/results/<stamp>/plugin`, `.git` and `evals/results` skipped, 2.2 MB. And the harness printed verdicts it never stored, so a 3.3-hour sweep piped through `tail -80` lost 56 of 58 case verdicts; each run writes `verdict.json` now, with `passed: null` on a harness error rather than false (findings 114 and 114b, both from board-ux-improvements out of its own sweep). 631 on main at f9725de. 0.12.9 installed 2026-09-19 17:39 on Zach's CIMP: five commits of board-ux-improvements' work that had been merged on main and unpushed since 15:00 — the resume strip reading as a strip rather than a document, the Resume block held to six lines with the check it could not run named as such, folding and warning separated into two questions that had shared one number, `short_name` split into `clip_name` (the hard character cut, for terminal lines) and a `short_name` that ends at a clause boundary and loses no letters, `table-layout:fixed` so opening a fold stops re-laying out the table, the six filter chips fixed after `~table` had been hopping to a sibling since stage 6's phone pass, the density cap measuring item text rather than the stylesheet's fixed cost, and a new grader for `resume-block-stays-short` where delete-and-stub had scored 9 of 9 because a preservation check was satisfied better by deletion than by filing. **Carried forward, not resolved, in that commit's own words: `resume-block-stays-short` has not been run on opus and needs `--model opus --runs 3` before anything in it is called green.** This lane's own change is one stale comment. 641 on main at b106c59. 0.13.0 installed 2026-09-19 22:42: a `done` lane may name the commit that closed it — `done 21:16–22:05 54b7eb3` — and `reopen` asks `merge-base --is-ancestor <sha> main` instead of asking whether the owner's whole tree is on main, which is a different question and was wrong about six of thirteen lanes. `landed()` is three-valued and only `landed` clears a lane: no sha, an unreadable one, one git cannot resolve, or git itself failing all fall back to today's tree-decides behaviour, because a false reopen is noisy and self-clearing while a false clear is silent and permanent (finding 116d; the false-clear rule is board-ux-improvements', made structural rather than advisory). Proved before shipping: A/B on the live tracker in the same minute was byte-identical with no sha yet written, and against the real `openemr-arch` worktree — the one the audit calls 'not on main' — all five hand-verified shas return `landed` while its own unmerged tip returns `not-landed`. The writer half is three edits, two of them in board-ux's files, and is a named handoff rather than built. 667 on main at 3c8476e. |
| `frank-lloyd-aight` | 2026-09-17 | plan "general-contradictor, a main-session architecture agent" approved in plan mode at 12:50 CT, after Zach chose the shape ("Sidecar repo"), the eval coverage, and the name from 22 candidates; "create the github repo as a public repo"; renamed at 13:24 CT: "We're renaming it to Frank Lloyd AIght" (GitHub repo renamed by Zach) | **Yes** — 2026-09-17 14:02 CT, "CIP and go on the next stage" after stages 0–1b (skeleton, harness port, question channel; agent file is frontmatter only until stage 2): `claude plugin marketplace add ~/Developer/frank-lloyd-aight` + `claude plugin install frank-lloyd-aight@frank-lloyd-aight` (user scope, 0.1.0; updated to 0.2.0 at 16:51 CT on "CIP" after stage 2.1; to 0.3.0 at 20:28 CT on "CIP and enter the next planning mode" after stage 2.2; to **0.4.0** on 2026-09-19 at 20:4x CT on "CIMP then plan the next step" after stage 2.3 was committed at last and stage 3.1 rewrote the agent's charter to four jobs — create, maintain, review, and grade compliance against the architectural documentation, which it owns; no direct code changes; to **0.5.0** on 2026-09-19 at 22:5x CT on "CIMP" after stage 3.2 gave the agent the fourth job in writing — grade compliance against the documentation, record it at `<architecture dir>/compliance.md` with file, line and owner, and relay each defect to the implementer and the coordinator; to **0.5.1** on 2026-09-19 at 23:5x CT on "CIMP" after stage 3.2h taught the eval arms to report, per grader, whether it discriminates between them or passes either way — harness only, the agent file unchanged; to **0.6.0** on 2026-09-20 at 01:5x CT on "CIMP then plan it" after stage 3.3 scoped compliance grading to a pass the user asks for — a compliance *question* is answered with a verdict and every gap cited, and nothing is filed, committed or relayed until he says so; to **0.7.0** on 2026-09-20 at 03:5x CT on "CIMP when done" after stage 3.4 added section 9 to the review page — where the code departs from the specification, carried on the page the review publishes, code defects only, a stale document staying in section 6). Sidecar `locriani/frank-lloyd-aight` (public), checkout `~/Developer/frank-lloyd-aight` |
| `auditor` | 2026-09-15 | "Build an ... Claude Code skill + audit subagent, then use it to produce AUDIT.md" | **Yes** — approved and enabled 2026-09-15 as the in-repo plugin `codebase-audit`, installed from the local marketplace. Extracted to a sidecar repo 2026-09-19 on "Let's find that audit agent I started working on and pull it out into it's own repo": `git subtree split` carried its six commits out to `~/Developer/auditor`, plugin id `codebase-audit` → `auditor`, 1.4.2 → 2.0.0, and this row moved from the Plugins table to this one. **The name is provisional** — "just call it Auditor for now". Sidecar `locriani/auditor` (private), created by Zach 2026-09-19 and pushed at 21:11, checkout `~/Developer/auditor`. Reinstalled from the new source 2026-09-19 21:05 on "CIMP it": `claude plugin uninstall codebase-audit@ai-additions` + `claude plugin marketplace update ai-additions` + `claude plugin marketplace add ~/Developer/auditor` + `claude plugin install auditor@auditor` (user scope, 2.0.0), suite green on main first — `test_probe.sh` 179 passed, 0 failed, 2 skipped at c16ea3a. The old cache was deleted 2026-09-19 22:35 on "kill the old one from setup": `~/.claude/plugins/cache/ai-additions/codebase-audit`, 1.0M, six snapshots 1.0.0–1.4.0. It records that the enabled install had been **1.4.0** while the tree was 1.4.2 — two patches behind itself until the swap. |

### Open — approved, shape unresolved

| Item | Approved | Wording | Blocker |
|---|---|---|---|
| autoupdates | 2026-09-13 | "and enable autoupdates" | Which updater, and it is an *enable* action — see below |

## Notes on the above

- **`superpowers@` was written with the marketplace blank.** Taken as
  `claude-plugins-official` — already registered here, and the marketplace named
  on the line immediately before it. Upstream documents two other routes; see
  [`referenced/upstream-plugins.md`](referenced/upstream-plugins.md).
- **autoupdates is the one thing that contradicts "not enabled".** Everything
  else was added and left off; this asks to switch something on, and it is not
  clear what: Claude Code's own CLI auto-updater, or `claude plugin marketplace
  update` on a schedule for the plugins above. Neither `marketplace add` nor
  `plugin install` exposes an autoupdate flag. Recorded, not acted on.
- **`skill-perf` and its judge are split across two plugins.** The judge is the
  `skill-perf-judge` skill inside `extras`. Enabling either alone gives a working
  half — capture with nothing scoring it, or a judge with nothing to read.
- **Two plugins need a second step beyond installing.** `skill-perf` needs its
  database created and `schema.sql` deployed to `~/.claude/skill-perf/`;
  `stack-profiles` needs its profiles deployed to `~/.claude/stacks/`. Each plugin
  README says so.
- **The CLIs are not a third case.** `github-utilities` and `repo-scaffold` each
  keep their executable at the default `bin/` location, which Claude Code adds to
  the Bash tool's `PATH` while the plugin is enabled — bare `gh-issue-rel` and
  `scaffold-repo` resolve on install, with nothing to link. This file previously
  asserted the opposite; it was wrong, and so were both READMEs.
- **`repo-scaffold` does not run as a plugin.** Its `bin/` shim execs
  `~/.local/share/repo-scaffold/scaffold-new-repo.sh` and its slash command names
  `~/.local/bin/scaffold-repo` — both Standard Configs deploy paths that `apply.py`
  created and a plugin install does not, while the real script sits unreferenced in
  the plugin root. Found 2026-09-15 while correcting the `PATH` claim. Recorded, not
  fixed: the repair is a behaviour change and the plugin is not enabled.
- **`GITHUB.md` is the only rule file not byte-identical** — two links repaired
  to point at `plugins/github-utilities/`. Paths only, no prose.
- **`security-guidance` now has two owners.** It is also in Standard Configs'
  `external/claude-plugins/templates/plugin-set.txt`. Deduplicate before either
  is enabled.
- **The tracer-bullet fold-in is an acceptance criterion, not a preference.** Whichever issue-tracking candidate is eventually chosen must state the vertical-slice rule explicitly in its decomposition step — a slice cuts every layer, a layer is not a slice. `prd-design` already does. Written down because "fold it in" is otherwise lost by the time the pick is made.
- **All three issue-tracking candidates share one blocker:** they publish blocking edges as prose, which `rules/GITHUB.md` forbids in favour of native links via `gh-issue-rel`. Adopting any of them means replacing its publish step. `mattpocock-skills` is closest — it computes the dependency graph correctly and only lands it wrong.
- **Two items look misfiled and are recorded where they were approved, not where
  they may belong.** `atuin` is a Homebrew CLI with no Claude surface at all;
  `claude-statusline` is Rust plus two binaries plus a LaunchAgent. Both read as
  machine configuration, which is Standard Configs' remit.

## Pending — discussed, NOT approved

| Item | What it is | Where it lives today |
|---|---|---|
| *(none)* | | |

## Declined

| Item | Reason |
|---|---|
| standalone `tracer-bullets` skill | Redundant with ordered vertical-slice decomposition, which already enforces the discipline. `dividedby/skills` built one and filed it under `.out-of-scope` for the same reason. Folded into `prd-design` instead. **Reversal condition:** a demonstrated gap the pipeline does not close — tickets routinely inflating into horizontal layers despite thin, ordered slices. |
