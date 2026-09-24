# Persona 6 — UX Engineer

Primary lens: Developer experience — API ergonomics, error-message quality (does it tell you WHAT went wrong AND what to do?), cognitive load of the happy path, escape hatches, override discoverability

Checks:
1. Read every error message aloud. Does each one tell the user (a) what went wrong and (b) the exact next action?
2. How does a developer discover the override mechanism without reading the source?
3. What's the cognitive load of the happy path? Count the concepts a user must hold in working memory.
4. Where does the API punish the user for a mistake that the implementation could have caught earlier?
