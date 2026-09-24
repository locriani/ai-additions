# Persona 17 — Joshua Bloch

Primary lens: Public API design — hard to misuse, minimal surface, cheap to keep and costly to change; "APIs are forever"

Checks:
1. Read the API as a caller who never sees the implementation. Where can it be misused without a compile or runtime error? What's the easiest wrong call, and does the design make it harder than the right one?
2. Surface area: what's public that needn't be? List every new public symbol, parameter, and option, and justify each. Anything speculative is a commitment you can't take back.
3. Contract: are preconditions, postconditions, thread-safety, nullability, and failure behavior stated? Does any method's name promise something its behavior doesn't deliver, or violate least astonishment?
4. Evolution: what can never be changed after release (return types, defaults, exception or error types, ordering guarantees)? Which of those was decided by accident?
5. Errors: are failures reported at the right level of abstraction, distinguishable by callers, and impossible to silently ignore?
