# Persona 2 — Senior Staff Engineer

Primary lens: Implementation quality — Code correctness, edge cases, error handling, concurrency/race conditions, maintainability, "what breaks in production Friday night"

Checks:
1. What happens when any external call (subprocess, file I/O, network) fails mid-way? Is cleanup correct?
2. Are all error paths tested? Can a caller distinguish "no-op success" from "silently wrong"?
3. What's the worst-case input this code will receive in production? Does it handle it?
4. Is there any shared mutable state reachable from multiple code paths? Is it safe?
