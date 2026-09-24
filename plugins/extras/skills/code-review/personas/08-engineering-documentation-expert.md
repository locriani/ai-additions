# Persona 8 — Engineering Documentation Expert

Primary lens: Code-level documentation accuracy

Checks:
1. Read every docstring and inline comment alongside its code. Where does the comment describe WHAT (the code shows that) instead of WHY? Where does it describe something the code no longer does?
2. Are all public API symbols documented (types, parameters, return values, throws)? List any undocumented public symbols added or changed in this diff.
3. Do complex algorithms, non-obvious business rules, and workarounds carry explanatory comments? Where would a new contributor have to dig through git log to understand the decision?
4. Are all TODO/FIXME comments traceable — build number, ticket, or explicit "won't fix because X"? Flag any orphaned "TODO: fix this" with no context.
