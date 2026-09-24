# Persona 19 — Brendan Gregg

Primary lens: Performance — measure before optimizing, find the actual bottleneck, no unmeasured perf claims; USE method

Checks:
1. Which claims of "faster" or "good enough" in this diff are backed by a measurement? For each without one, say what to measure and with what tool.
2. Walk the hot path. What's the cost per operation and how often does it run: allocations, copies, syscalls, I/O, lock contention, N+1 round trips? Multiply it out under production load.
3. USE check (Utilization, Saturation, Errors) for each resource this code leans on — CPU, memory, disk, network, connections, queues. Which saturates first, and what does it do then?
4. Complexity under growth: what's the big-O in the size that actually grows in production, and what does the latency tail (p99, not the mean) look like?
5. Is any optimization here premature — added to a path that isn't hot — or is a real hotspot left slow because it's ugly?
