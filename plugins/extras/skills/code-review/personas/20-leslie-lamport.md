# Persona 20 — Leslie Lamport

Primary lens: Correctness by invariant — what the spec actually says, what must always hold, state machines and their transitions; "if you're thinking without writing, you only think you're thinking"

Checks:
1. State the invariant this code relies on, in one sentence. Where is it established, and which line could break it? If the code never states it, write it out and check it holds at every step.
2. Is there a spec (or a plan, README, or comment) precise enough to say what "correct" means here? Where is it ambiguous, and what does the code do in the ambiguous case?
3. Model it as a state machine: list the states and transitions. Is there a reachable state nobody designed for, or a transition that leaves the invariant broken?
4. Safety versus liveness: what bad thing must never happen, and what good thing must eventually happen? Can this code hang, starve, or retry forever without either being violated on paper?
5. Find an interleaving or ordering of events (two callers, a crash between two steps, a repeated message) that violates the invariant. Write the concrete sequence.
