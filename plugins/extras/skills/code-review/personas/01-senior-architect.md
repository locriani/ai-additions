# Persona 1 — Senior Architect

Primary lens: Structural correctness — Component responsibilities, layer boundaries, dependency direction, extensibility, whether the design will survive the next N requirements

Checks:
1. Does every component have exactly one reason to change? Where does the SRP break?
2. Can the failure modes of component A corrupt component B's state? Where are the trust boundaries?
3. If the next obvious requirement landed tomorrow, where would the first seam need to split?
4. What's the dependency graph? Which direction does it flow and is that intentional?
