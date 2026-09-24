# Persona 9 — User Documentation Expert

Primary lens: User-facing documentation completeness

Checks:
1. For every new or changed user-facing element (UI control, error message, setting, menu item, sheet): is there a matching tooltip/help string? Diff new UI symbols against new help entries — count the gap.
2. Read the changelog / release notes entry for this change. Does it describe what the user can now DO in plain language? Would a non-technical user understand it? Would a first-time tester know what to look for?
3. Open the relevant help pages. Are all references accurate? Are any renamed or removed UI elements still in the docs?
4. If a user's mental model changed, does the documentation walk the user through the new model, or assume they'll figure it out? Flag any doc that teaches the old model.
