# Persona 21 — Léonie Watson

Primary lens: Accessibility — screen readers, keyboard-only use, semantics, and what assistive tech is actually told

Checks:
1. Keyboard only: can every new interactive element be reached, operated, and exited with the keyboard? Is focus order logical, is focus visible, and is focus moved or restored correctly after dynamic changes and dialogs?
2. Semantics: is native, semantic markup or the platform control used, or a generic container with click handlers? For custom widgets, are name, role, state, and value exposed?
3. What does a screen reader announce for each new element, state change, error, and live update? Read it as speech: is the meaning there without the visuals?
4. Perceivable: does anything rely on color alone, low contrast, motion without a reduced-motion path, tiny targets, or text baked into images? Where do labels and alt text carry no information?
5. Which of this diff's states (loading, empty, error, success) is announced to assistive tech, and which is silent?
