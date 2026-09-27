# bug-hunt subagent prompts

Fill the `{…}` slots. Paths are absolute and point into the worktree `W`, never the user's checkout.

## Finder (5 × `Explore`, one message)

```
You are hunting correctness bugs from one angle: {ANGLE}.

Files (read them, plus whatever they call, as far as the angle needs): {FILES}
Repo root (a disposable worktree): {W}

Report only defects where the code does something other than what its own contract says. The contract is its
docstring, doc, type, name, the tests around it, the README, or an obvious universal rule such as no crash on valid
input or no silent data loss. Style, performance and "I'd have written it differently" are out of scope.

For each candidate, give:
  path:line | expected (what the contract says) | actual (what the code does) | the contract, quoted with its location
  | a repro idea: the concrete input or sequence that shows it
Give at most 8, the most damaging first. If you find none, say "none"; an invented candidate costs a prover.
```

**Angles**, one per finder:

1. **Boundaries and error paths.** Off-by-one, empty or single-element input, zero, negatives, max values,
   inclusive vs exclusive, and error branches that return a value indistinguishable from success.
2. **Hostile input and partial failure.** Malformed or huge input, unicode and odd paths, a dependency that errors
   or times out part way, cleanup skipped on an exception, retries that double-apply.
3. **State and invariants.** Something the code assumes stays true (sorted, unique, non-null, in sync with another
   store), and the sequence of calls that breaks it. Shared mutable state, caches that go stale, races and TOCTOU.
4. **Language pitfalls.** Mutable defaults, integer or float division, truthiness of 0 or "", identity vs
   equality, shadowing, late-binding closures, implicit conversions, unawaited promises, nil or optional handling,
   and whatever else this stack is known for.
5. **Contract drift.** Docs, docstrings, types, names or tests that promise one thing while the code does another.
   Cite both sides.

## Prover (`general-purpose`, one per candidate, one message)

```
Prove or drop one bug candidate. Work only in {W}; add exactly one new file and change no existing file.

Candidate {N}: {PATH}:{LINE} — expected {EXPECTED}, actual {ACTUAL}. Contract: {CONTRACT}. Idea: {IDEA}
Test command for this repo: {TEST_COMMAND} (baseline: {BASELINE})

1. Write the smallest repro as a new file named bug_hunt_{N}, in the repo's test framework and conventions where it
   has one, otherwise as a standalone script. It must go through the public entry point a caller would use, with no
   mocks that manufacture the failure. It must assert the expected value, so the failure message shows expected
   vs actual.
2. Run only that repro, twice.
3. Reply with exactly one of:
   PROVEN | repro path | command | the failure lines from both runs
   DROPPED | why (passed, flaky, or failed for a reason other than the claim: import, collection or setup error)
Paste the full repro file under PROVEN.
```

## Verifier (`general-purpose`, one at a time)

```
Try to refute one proven bug. You are the last check before a report nobody will second-guess. Work only in {W}.

Finding: {PATH}:{LINE} — expected {EXPECTED}, actual {ACTUAL}. Claimed contract: {CONTRACT}
Repro: {REPRO_PATH}, run with {COMMAND}

1. Run the repro and confirm it fails on the claimed assertion.
2. Make the smallest fix at the claimed root cause, run the repro, and confirm it now passes. Then restore:
   git -C {W} checkout -- <the file you changed>
   and confirm `git -C {W} status --porcelain` shows only the untracked repro files.
3. Refute if any of these hold:
   - the "expected" behaviour is not what the code intends (look for a doc, test or caller relying on the
     current behaviour)
   - the repro reaches the failure only through mocks, private internals, or an input the public API rejects
     earlier
   - the fix did not turn it green, or it is the same defect as {CONFIRMED_SO_FAR}
4. Reply with exactly one of:
   CONFIRMED | severity (per the table in SKILL.md) | intent_evidence (quoted, with its location) | root cause in
   one line | the failure excerpt
   REFUTED | the line or fact that refutes it, quoted
```
