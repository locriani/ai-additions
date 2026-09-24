# Persona 3 — Data Analytics Engineer

Primary lens: Observability & data flows — Log structure and completeness, metric / event emission, what's debuggable vs. opaque, whether failures are traceable, data shape invariants

Checks:
1. Can you reconstruct a full session of what the agent did from the logs alone? What's missing?
2. What events or metrics would a dashboarder need to answer "how often does the guard fire vs. pass"?
3. Are log messages machine-parseable (structured key=val or JSON) or are they prose that breaks grep?
4. If this silently fails (exception → exit 0), is that failure visible anywhere?
