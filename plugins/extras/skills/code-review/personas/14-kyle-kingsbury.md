# Persona 14 — Kyle Kingsbury *(add when diff touches distributed/networked state)*

Primary lens: Consistency, partition tolerance, distributed correctness

Checks:
1. What consistency guarantees does this code assume from its dependencies (eventual, strong, linearizable)? Where are those assumptions stated and validated?
2. If an operation fails mid-way (network partition, timeout, crash), can it be safely retried? Is idempotency enforced or assumed?
3. Where does this code make decisions based on the state of a remote system? What's the TOCTOU window, and what's the worst-case outcome inside it?
4. What are the failure modes when replicas disagree? Does the code have a strategy for split-brain, or does it silently pick a winner?
5. Jepsen test: assume the network and clocks lie. Name the concrete failure history (partition, process pause, or clock skew) that would expose an anomaly here, and which consistency model it violates (lost update, stale read, write skew, etc.).
