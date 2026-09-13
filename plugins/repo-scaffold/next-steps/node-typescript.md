  - cd "$REPO"
  - pnpm init  (writes package.json)
  - pnpm add -D typescript @types/node vitest tsx
  - npx tsc --init --strict   (then tighten: noUncheckedIndexedAccess,
    exactOptionalPropertyTypes — per the stack profile)
  - Commit pnpm-lock.yaml.
  - Edit CLAUDE.md: fill Build & Test commands.
  - Optional: /init-ai-memory in the repo root.
