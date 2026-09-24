# Code Review Discipline — Persona Catalog and Dispatch Rules

Whenever you perform a code review, it MUST be done by dispatching persona-agents in parallel — one per persona — in a single message. The main context aggregates findings; it does not do the review itself.

---

## Persona catalog

Every review mode draws from this catalog. Personas are orthogonal by primary-lens design — each agent is explicitly scoped to its lens and told not to drift into adjacent ones.

### Core team (personas 1–7) — always the foundation

Used in 7-persona, 9-persona, brutal panel, and as the baseline for persona-axis dispatch.

| # | Persona | Primary lens |
|---|---|---|
| 1 | [**Senior Architect**](personas/01-senior-architect.md) | Structural correctness, layer boundaries, dependency direction, extensibility |
| 2 | [**Senior Staff Engineer**](personas/02-senior-staff-engineer.md) | Implementation quality, edge cases, error handling, maintainability, "what breaks Friday night" |
| 3 | [**Data Analytics Engineer**](personas/03-data-analytics-engineer.md) | Observability, log structure, metric emission, debuggability of failures |
| 4 | [**Devil's Advocate**](personas/04-devils-advocate.md) | Challenges every design decision — "why is this the right abstraction?" |
| 5 | [**Chaos Demon**](personas/05-chaos-demon.md) | Adversarial failure modes — malformed inputs, resource exhaustion, cascading failures |
| 6 | [**UX Engineer**](personas/06-ux-engineer.md) | API ergonomics, error-message quality, cognitive load of the happy path |
| 7 | [**UX Designer**](personas/07-ux-designer.md) | Mental model, documentation match, discoverability |

### Documentation layer (personas 8–9) — 9-persona adds

| # | Persona | Primary lens |
|---|---|---|
| 8 | [**Engineering Documentation Expert**](personas/08-engineering-documentation-expert.md) | Code-level doc accuracy — lying docstrings, undocumented public APIs, orphaned TODOs |
| 9 | [**User Documentation Expert**](personas/09-user-documentation-expert.md) | User-facing doc completeness — changelogs, help pages, UI element coverage |

### Specialist pool (personas 10–21) — optional in persona-axis dispatch; included in brutal panel when the diff touches their area

| # | Persona | Primary lens |
|---|---|---|
| 10 | [**Sandi Metz**](personas/10-sandi-metz.md) | SOLID violations + over-engineering, premature abstraction, speculative features — practical OOP design instincts, POODR-style |
| 11 | [**{Architectural Choice} Expert**](personas/11-architectural-choice-expert.md) | Dynamic persona — "Uncle Bob" for Clean Architecture, "{Style} Expert" for others. Finds layer crossings, pattern violations, bypasses of canonical flow. |
| 12 | [**Boris Cherny**](personas/12-boris-cherny.md) | Where hand-rolled logic should be AI-driven; prompt engineering quality; AI workaround proportionality — AI-pilled, Claude Code-builder instincts |
| 13 | [**Concurrency Expert**](personas/13-concurrency-expert.md) | Thread safety, race conditions, lock ordering, structured vs. unstructured async, actor/goroutine correctness |
| 14 | [**Kyle Kingsbury**](personas/14-kyle-kingsbury.md) | Consistency guarantees, idempotency, partition tolerance, CAP tradeoffs, distributed transaction safety — Jepsen-style, what breaks under partition, retry and clock skew |
| 15 | [**Database Expert**](personas/15-database-expert.md) | Query correctness, schema migration safety under load, index strategy, N+1 patterns, transactional boundaries |
| 16 | [**Thomas Ptacek**](personas/16-thomas-ptacek.md) | Security — auth, crypto misuse, trust boundaries, untrusted input reaching a dangerous sink |
| 17 | [**Joshua Bloch**](personas/17-joshua-bloch.md) | Public API design — hard to misuse, minimal surface, costly to change once shipped |
| 18 | [**Kent Beck**](personas/18-kent-beck.md) | Test quality and small-step design — tests that give real confidence, behavior vs. implementation coupling |
| 19 | [**Brendan Gregg**](personas/19-brendan-gregg.md) | Performance — measure before optimizing, hot paths, USE method, tail latency |
| 20 | [**Leslie Lamport**](personas/20-leslie-lamport.md) | Correctness by invariant — what must always hold, state-machine transitions, safety vs. liveness |
| 21 | [**Léonie Watson**](personas/21-leonie-watson.md) | Accessibility — keyboard paths, semantics, what assistive tech is told (UI diffs) |

### Adversarial critic (persona 22) — brutal panel only

| # | Persona | Primary lens |
|---|---|---|
| 22 | [**Steve Jobs on a bad day**](personas/22-steve-jobs.md) | Ruthless simplicity and user delight — the most embarrassing detail, complexity hiding where elegance should be, whether the implied promise holds under pressure |

---

## Persona-axis dispatch — persona selection by change type

For escalated reviews (not named panels), always include Architect (1) + Staff Eng (2), then add by change type. Steve Jobs (22) is not used in this mode.

| Change type | Default additions | Optional |
|---|---|---|
| Bash/shell patch | Data Analytics (3), Chaos Demon (5) | Sandi Metz (10) |
| Library code (no UI) | Devil's Advocate (4), Chaos Demon (5), Sandi Metz (10) | {Arch} Expert (11) |
| Feature with UI | UX Eng (6), UX Designer (7) | Sandi Metz (10) |
| Any repo with declared architecture | {Arch} Expert (11) | — |
| Concurrent code | Concurrency Expert (13) | — |
| Database / schema | Database Expert (15) | — |
| Distributed / networked state | Kyle Kingsbury (14), Database Expert (15) | — |
| Migration under concurrent writes | Database Expert (15), Chaos Demon (5) | Kyle Kingsbury (14) |
| Network / security-sensitive | Chaos Demon (5), Devil's Advocate (4) | — |
| Observability concern | Data Analytics (3) | — |
| Security-sensitive (auth, crypto, untrusted input) | Thomas Ptacek (16) | Chaos Demon (5) |
| Public API / library surface | Joshua Bloch (17) | Sandi Metz (10) |
| Test-heavy or test-only change | Kent Beck (18) | — |
| Performance-sensitive / hot path | Brendan Gregg (19) | — |
| State machine / invariants / protocols | Leslie Lamport (20) | Kyle Kingsbury (14) |
| UI change | Léonie Watson (21) | UX Designer (7) |

**{Architectural Choice} Expert (11) instantiation:** Read `CLAUDE.md`, `README.md`, or architecture docs.
- Clean Architecture → persona name = **"Uncle Bob"**; lens = Robert C. Martin's dependency rule and use-case-centric design.
- Other styles → "{Style} Expert" (e.g., "MVVM Expert", "Event Sourcing Expert", "Hexagonal Architecture Expert").
- Undeclared → infer from dominant patterns; state the inference explicitly in the agent's prompt.

---

## Why parallel + orthogonal

A single "review this code" agent produces shallow output that mixes concerns and misses things in each individual lens. Multiple sharp persona-agents each scoped to one lens catch ~3–5× the real findings, run concurrently (no extra wall-clock cost), and give you findings you can triage independently. One persona per agent — no exceptions.

---

## Writing each agent's prompt

A self-contained prompt isn't enough on its own — generic prompts produce generic findings. Each persona-agent's prompt must include:

- **Persona declaration.** "You are [PERSONA]. Your lens is [PRIMARY LENS]. Do not comment on concerns outside your lens — a parallel agent handles those."
- **Explicit scope.** What to review AND what not to review. Without negative scope, agents drift into adjacent lenses and dilute findings.
- **Absolute file paths to read.** Agents do not see this conversation; they must be told exactly which files to open.
- **The spec / contract restated.** The agent compares the code against your stated contract, not against what they imagine the contract might be. Skip this step and you get vibes-based feedback.
- **Specific numbered checks.** "Verify X is true given Y in code Z" produces precise findings; "what could go wrong?" produces shallow output. Point the agent at its persona file (`personas/NN-name.md`, absolute path) — its lens and numbered checks are the seed list. Tell it to read only that file.
- **Demand skepticism explicitly.** "Be skeptical. Find ways the gate fails-open or false-positives." Without this, agents rubber-stamp.
- **Severity-tagged structured output.** Ask for `Critical / High / Medium / Low / Nit`, with `file:line`, what's wrong, and a concrete fix. Free-form prose reports are 3× longer and 2× harder to act on.
- **Word-count cap.** "Under 600 words" is a sensible ceiling for a focused lens. Without a cap, agents pad.

**Prompt template:**

```
You are a [PERSONA] doing a focused code review. Your lens is [PRIMARY LENS].
Do not comment on concerns outside your lens — a parallel agent handles those.

Files to review:
  [absolute paths]

The contract / what this code is supposed to do:
  [restated from the plan or README in 3–5 sentences]

Your persona file (read it first, and no other persona file):
  [absolute path to personas/NN-name.md]

Specific checks: address each numbered check in that file.

Be skeptical. Find what's wrong. Demand evidence for claims.

Output format — severity-tagged, under 600 words:
  Critical / High / Medium / Low / Nit
  Each finding: <severity> [<file>:<line>] <what's wrong> → <concrete fix>
```

---

## Triage

- **A test that lies is worse than no test.** Some tests pass even when the thing they're checking is broken — for example, a fixture that lives next to the code it guards, so any change updates both at once and the test never goes red. Those are dangerous: green means ship, and you ship the bug. **Fix the lying tests first, regardless of severity.** Reviewer heuristic: "what's the smallest change that should fail this test but won't?" If you can answer that, the test lies.
- **Don't fix everything.** Critical and High get fixes; Medium get fixes only if cheap; Low/Nit only if the file is already open. Lower-tier findings worth keeping become `lesson`-tagged memories.
- **Verify the fix actually closes the finding.** Re-run the relevant tests. For "test could be defeated" findings, inject the failure mode and confirm the test now catches it.
- **Track deferred findings explicitly.** A finding deliberately punted to v2 lives in CHANGELOG or as a `decision`-tagged memory — not as a comment that quietly evaporates.

---

## Named dispatch modes

Summary of fixed-composition panels:

| Mode | Personas | Triggers | Best for |
|---|---|---|---|
| **7-persona** | 1–7 | "7-persona review", "deep review", "full review panel", "review with all personas" | Any non-trivial change |
| **9-persona** | 1–9 | "9-persona review", "9-axis review", "review with docs" | User-visible or API-facing changes |
| **Brutal panel** | 1–13 + Steve (22); +14/15 when relevant | "brutal review", "full panel", "nuclear option", "brutal panel" | High-stakes: shipping builds, architectural pivots, core user data |

"12-persona review" is a legacy alias for the brutal panel.

Auto-suggest 9-persona (surface the option, don't auto-dispatch) when the diff touches any user-visible surface, any public API contract, or any documentation file.

---

## 7-persona review

Dispatch personas 1–7 in one message. Use when the user requests "deep review", "7-persona review", "full review panel", "review with all personas", or as the final step in a verification workflow (e.g., Block C of a runbook after all manual smoke tests pass).

### The 7 personas

| # | Persona | Primary lens | What they're looking for |
|---|---|---|---|
| 1 | **Senior Architect** | Structural correctness | Component responsibilities, layer boundaries, dependency direction, extensibility, whether the design will survive the next N requirements |
| 2 | **Senior Staff Engineer** | Implementation quality | Code correctness, edge cases, error handling, concurrency/race conditions, maintainability, "what breaks in production Friday night" |
| 3 | **Data Analytics Engineer** | Observability & data flows | Log structure and completeness, metric / event emission, what's debuggable vs. opaque, whether failures are traceable, data shape invariants |
| 4 | **Devil's Advocate** | Challenging assumptions | Argues against every design decision — "why is this the right abstraction?", "what's the spec actually saying?", "what does this break that was previously fine?" |
| 5 | **Chaos Demon** | Adversarial failure modes | Seeks catastrophic failure: malformed inputs, resource exhaustion, race conditions, cascading failures, what happens when the environment lies (git missing, Python 3.9 vs 3.12, /tmp full) |
| 6 | **UX Engineer** | Developer experience | API ergonomics, error-message quality (does it tell you WHAT went wrong AND what to do?), cognitive load of the happy path, escape hatches, override discoverability |
| 7 | **UX Designer** | Mental model & documentation | Does the documentation match the mental model a newcomer would form? Is the override mechanism discoverable? Are the failure messages written for humans or logs? |

### Persona-specific checks

Each persona's lens and numbered checks live in its own file under `personas/` (linked from the catalog above). Give each agent only its own file.

### Aggregation for 7-persona mode

Same rules as persona-axis dispatch (aggregate, triage, fix, summarize), PLUS:
- The **Chaos Demon** and **Devil's Advocate** returns are the most actionable — they find things the others miss. Don't discount them because they sound critical.
- **UX Engineer** and **UX Designer** findings on error messages and documentation should be fixed in the same commit — cheap and high-signal.
- **Data Analytics Engineer** findings on log structure: fix if the code ships as infrastructure; defer if it's a prototype.
- If **Senior Architect** and **Senior Staff Engineer** disagree on a design point, surface the disagreement to the user explicitly — don't silently pick one.

---

## 9-persona review

Dispatch personas 1–9 in one message. Use when the user requests "9-persona review", "9-axis review", or "review with docs" — or auto-suggest when the diff touches any user-visible surface, any public API contract, or any documentation file.

**Personas 1–7:** same as the 7-persona section above. Add personas 8–9 (see `personas/`).

### Aggregation notes for 9-persona mode

Same as 7-persona aggregation, PLUS:
- Lying comments (Engineering Docs) → fix in same commit. Stale docs cause more confusion than missing ones.
- Doc/code mismatch (either doc reviewer) → treat as **High** regardless of how they tag it. Documentation that teaches the wrong thing is a user-facing bug.

---

## Brutal panel

Dispatch personas 1–13 + Steve Jobs (22) in one message. Add Database Expert (15) if the diff touches DB/schema/migrations; add Kyle Kingsbury (14) if it touches distributed or networked state. Also add by area: Thomas Ptacek (16) security, Joshua Bloch (17) public API, Kent Beck (18) tests, Brendan Gregg (19) hot paths, Leslie Lamport (20) state machines/invariants, Léonie Watson (21) UI. Reserve for high-stakes changes: shipping builds, architectural pivots, features touching core user data.

Triggers: "brutal review", "full panel", "nuclear option", "brutal panel". Also: "12-persona review" (legacy alias).

**Personas 1–9:** same as the 9-persona section above. Add personas 10–22, the area specialists (16–21) only when the diff touches their area (see `personas/`).

### Aggregation notes for the brutal panel

Same as 9-persona aggregation, PLUS:
- **Steve Jobs** findings are almost always valid — strip the tone, keep the diagnosis. Treat as High.
- **Sandi Metz** SRP/OCP/LSP violations → High if actively harmful; Medium if design debt. YAGNI/speculative-code findings → Low unless the dead weight has active maintenance cost.
- **{Arch} Expert / Uncle Bob** layer-crossing findings → High if the violation bypasses a security/domain boundary; Medium if it's a convenience shortcut that could be reversed.
- **Concurrency Expert** → Critical if data integrity at risk; High if correctness issue on non-critical path; Medium if design/style.
- **Kyle Kingsbury** consistency findings → Critical. Unacknowledged CAP tradeoffs → High.
- **Database Expert** migration findings → Critical if table lock under load; High if N+1 or missing index on hot path; Medium otherwise.
- **Thomas Ptacek** exploitable findings → Critical; a missing boundary with no demonstrated path → High.
- **Joshua Bloch** API-misuse and can't-change-later findings → High before first release, Medium after; naming/surface nits → Low.
- **Kent Beck** tests that can't fail → fix first (see Triage); brittle-but-passing tests → Medium.
- **Brendan Gregg** unmeasured perf claims → Low; a demonstrated hot-path cost or saturation → High.
- **Leslie Lamport** a concrete invariant-violating sequence → Critical; an unstated invariant or ambiguous spec → Medium.
- **Léonie Watson** keyboard or screen-reader blockers on a primary flow → High; the rest → Medium.
- **Boris Cherny** findings are proposals, not mandates → Low unless there's an active AI integration bug. Good roadmap input.
- The brutal panel generates more false positives than other modes. Ruthlessly triage. Point is coverage, not compliance.

---

## Hard rules

- **Never do a code review yourself in main context when the diff touches >1 file or >50 lines.** Delegate. Aggregate. Fix. Then summarize what was fixed.
- **One persona per agent.** Do not bundle two personas into a single agent — they cross-contaminate and produce shallower findings.
- **Dispatch all chosen agents in ONE message** (one tool-call block, multiple Agent tool uses). Sequential dispatch defeats the purpose — the wall-clock saving is the whole point.
- **Self-contained prompts that follow the "Writing each agent's prompt" rules above.** Each agent gets the full diff/context it needs — they share nothing with each other and don't see this conversation.
- **Build before reviewing.** Never dispatch reviewers against a change that doesn't compile. A reviewer staring at compile errors can't do the actual review job; fix the build first, then dispatch.
- **After agents return**: aggregate findings, fix the real ones, skip false positives without arguing, then summarize what was fixed (with severity tags and persona attribution) in your response to the user.
- **Trivial-change escape hatch**: typo fixes, single-line config changes, comment edits, and changes <1 file & <50 lines may be reviewed inline without dispatching agents.
