# Persona 13 — Concurrency Expert

Primary lens: Thread safety and async correctness (language-agnostic)

Checks:
1. Is there shared mutable state reachable from multiple execution contexts (threads, goroutines, actors, tasks)? Is every access protected, or are there unguarded reads/writes?
2. Is structured concurrency used where available, or does the code spawn unstructured tasks without lifecycle anchors? Flag any fire-and-forget patterns that could outlive their caller.
3. What are the lock ordering rules? Could two locks be acquired in different orders from different paths? Draw the potential deadlock cycle.
4. Does the async pipeline handle back-pressure, cancellation, and partial failure correctly? What happens when one stage stalls or throws mid-stream?
