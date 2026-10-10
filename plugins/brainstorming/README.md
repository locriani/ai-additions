# brainstorming

A skill. Finds out what the user actually wants, and why, before anything gets
built: an open first question, one question per message, playback in chunks, a
size call, and a hard gate until the description is approved.

## Status

**Added, not enabled.** Approved 2026-10-09 on "1 only if it's license compatible"
(Zach), answering which destination the extracted skill should live in; the licenses
were checked and are compatible (MIT / MIT). Enabling is a separate approval.

## Provenance

The `SKILL.md` body of [`obra/superpowers`](https://github.com/obra/superpowers)
`skills/brainstorming/SKILL.md` at `main` on 2026-10-09, MIT, © 2025 Jesse Vincent.
The upstream license is kept in [`LICENSE-superpowers`](LICENSE-superpowers).

Only the body was taken. Edits, all to remove dependencies on the rest of
superpowers:

- Dropped the **Visual Companion** section, which needs upstream's server scripts
  and `visual-companion.md`; "show, don't tell" now offers a mockup or diagram.
- Builder check no longer reads `builder-check-prompt.md`; the instruction is inline.
- Design docs go to `docs/specs/`, not `docs/superpowers/specs/`.
- No hand-off to `superpowers:writing-plans`; the next step is just "the plan".

This is a copy, so it will not follow upstream. Re-diff against upstream to refresh it.
