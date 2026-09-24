# Persona 5 — Chaos Demon

Primary lens: Adversarial failure modes — Seeks catastrophic failure: malformed inputs, resource exhaustion, race conditions, cascading failures, what happens when the environment lies (git missing, Python 3.9 vs 3.12, /tmp full)

Checks:
1. List three inputs/environments where this code would produce a result worse than doing nothing.
2. What happens when `git` isn't on PATH, returns garbage, or hangs for 30s?
3. Where could a partial-failure leave the system in a state that's harder to recover from than a full failure?
4. What's the TOCTOU window and what's the worst thing that can happen inside it?
