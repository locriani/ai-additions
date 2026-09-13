# Stack Profile: Node.js / TypeScript

Load this profile when the project is Node/TypeScript — i.e. there's a `package.json` + `tsconfig.json`, or the bulk of tracked code is `*.ts` / `*.tsx`. **Default to the modern toolchain** below; if the repo uses different tools, follow that convention but flag a one-line "consider migrating to <X>" note in the end-of-turn summary if the gap is significant.

## Toolchain

- **`pnpm`** (v10+) — package manager. Content-addressable store, no `node_modules` duplication, strict by default, correct dependency isolation. The 2026 production default. Install: `brew install pnpm`. Never run `npm install` in a pnpm repo (creates a competing `package-lock.json`). **Bun** as a *package manager* is 3-5x faster on cold installs and viable, but it lacks built-in `audit` and has occasional compatibility edge cases — pick it only if install speed is a measured CI bottleneck. **Bun as a production *runtime*** is still not the default recommendation — use Node for server workloads unless the project is greenfield and the team has explicitly committed to the Bun ecosystem.
- **Node 24 LTS** — current LTS as of late 2025 / 2026. Pin via `.nvmrc` and `"engines.node": ">=24"`. Node 22 LTS is acceptable on legacy projects.
- **Native TS execution** — Node 24 strips type annotations from `.ts` files natively (no flag needed). For one-off scripts, just `node script.ts`. **Keep `tsx` only when you need `tsconfig.json` resolution (path aliases, JSX, decorators, downleveling)** — Node's stripper ignores `tsconfig`. Apps with bundlers (Vite/esbuild) don't need either.
- **`vitest`** (v3+, v4 stable as of Dec 2025) — test runner. Faster than Jest, ESM-native, same API. Browser Mode is now stable (Playwright/WebdriverIO under one Vite server). Use over Jest for new projects.
- **`prettier`** + **`eslint`** (flat config, `eslint.config.js`) — the safe, plugin-rich default. Legacy `.eslintrc.*` is dead.
- **`biome`** — viable Rust-based alternative covering lint + format in one binary, ~10-25x faster, ~80% rule parity with ESLint. Choose Biome on greenfield projects without heavy plugin needs; stay on ESLint+Prettier when you depend on `eslint-plugin-react-hooks`, `eslint-plugin-next`, type-aware lint rules, or custom rules. Don't mix — pick one.
- **`tsc --noEmit`** for type checking when the build pipeline does its own emit (Vite, esbuild, swc).

## Project shape

- **`package.json`** with `"type": "module"` — ESM-first. CommonJS is legacy. The CJS-only holdouts of 2023 (chalk, node-fetch, got, execa) all shipped ESM years ago; if you hit a CJS-only dep in 2026, it's almost always abandoned — find a replacement before working around it.
- **`tsconfig.json`** with `"strict": true` mandatory. Plus `"noUncheckedIndexedAccess": true` (catches the `arr[i]` undefined trap), `"noImplicitOverride": true`, `"exactOptionalPropertyTypes": true`, and **`"erasableSyntaxOnly": true`** (TS 5.8+) — bans `enum`, `namespace`, and constructor parameter properties so the code stays compatible with Node's native type-stripper, esbuild, and swc. The default Node TS template is too lax.
- **`pnpm-lock.yaml`** committed.
- **`.nvmrc`** or `"engines.node"` in `package.json` pins the Node version. Use the latest LTS unless there's a reason.
- **`src/`** holds source, **`dist/`** is the build output (gitignored).

## Strict tsconfig — minimum baseline

```json
{
  "compilerOptions": {
    "target": "ES2024",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noPropertyAccessFromIndexSignature": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

If the repo's `tsconfig` is laxer than this, that's tech debt — flag it but don't unilaterally tighten without the user's sign-off (a strict-mode flip can light up dozens of files).

`module: NodeNext` is the right call for pure Node services. Switch to `module: ESNext` + `moduleResolution: Bundler` when a bundler (Vite, esbuild, Rollup, webpack) owns module resolution — e.g. SSR frameworks, libraries shipping bundled output. Don't mix.

## Common commands

```bash
pnpm install               # install deps from lockfile
pnpm add <pkg>             # add runtime dep
pnpm add -D <pkg>          # add dev dep
pnpm remove <pkg>          # remove dep
pnpm dlx <pkg>             # one-shot run (npx equivalent)
pnpm run <script>          # run a package.json script
pnpm exec <bin>            # run a binary from local node_modules
pnpm tsc --noEmit          # typecheck
pnpm vitest                # run tests (watch mode by default; --run for CI)
pnpm vitest run            # one-shot test run
pnpm prettier --write .    # format
pnpm eslint . --fix        # lint + autofix
```

## Code conventions

- **`any` is banned.** Use `unknown` and narrow. If you must use `any`, leave a `// FIXME: <reason>` and a tracking note. Reviewers should reject `any` without explanation.
- **`type` over `interface`** for new code unless the repo's existing convention is `interface`. Less ambiguity around merging, identical capability for non-class types. (Class implementers and library boundaries that want declaration merging can use `interface` deliberately.)
- **`const` over `let`**, `let` over `var`. `var` is banned outright.
- **`async/await` over raw `.then()` chains** — flatter, easier to reason about.
- **No default exports.** Named exports only. Default exports break "find all references" and rename refactors, and make tree-shaking less reliable.
- **Discriminated unions** for state shapes — `{ status: "loading" } | { status: "ready"; data: T } | { status: "error"; err: Error }`. Exhaustiveness checks via `assertNever`.
- **No `enum`, no `namespace`, no constructor parameter properties.** `erasableSyntaxOnly` enforces this. Use `as const` objects + literal union types in place of enums — they're zero-cost at runtime, play better with tree-shaking, and survive Node's native type-stripper.
- **Path aliases via `tsconfig` `paths`** rather than relative `../../../` chains beyond depth 2.

## Async + error handling

- **Always `await` an async call OR explicitly `void`-mark it** (`void asyncFn()`). Floating promises are bugs.
- **`Promise.all` for parallel work**, `for await ... of` for sequential streaming. Don't sequentially `await` in a loop unless ordering matters.
- **Errors are `Error` instances**, not strings. Subclass `Error` for typed error hierarchies.
- **Result-type pattern** (`{ ok: true, value } | { ok: false, error }`) for callable APIs that have expected failures. Throw for genuinely exceptional conditions only.

## Testing (vitest)

- **`tests/`** mirroring `src/`, OR co-located `*.test.ts` next to source — pick one per repo.
- **`describe` + `test` (or `it`)** — same as Jest API.
- **`vi.mock()`** at module boundaries, never on the SUT.
- **`vi.useFakeTimers()`** when testing time-dependent code; restore in `afterEach`.
- **Coverage:** `vitest run --coverage` (uses v8 coverage by default). Aim 80%+ on new code.
- **Browser Mode** (stable in v3+, hardened in v4) — for component / DOM tests, prefer `vitest --browser` with Playwright over jsdom; real-browser semantics catch a class of bugs jsdom silently passes. Reach for it for component tests, not for pure-logic units.
- **In-source tests** (`if (import.meta.vitest) { ... }`) — fine for tiny pure helpers where colocation aids readability; don't use it for anything with mocks, fixtures, or non-trivial setup. External `*.test.ts` is still the default.
- **Workspace / projects** — Vitest 3 moved to inline `projects: [...]` config (the old standalone `vitest.workspace.ts` is deprecated). Use it for monorepos.

## Verification ritual

Before claiming a Node/TS change is done:

1. `pnpm tsc --noEmit` passes — zero new type errors. **Run this even on Node-native-TS projects** — Node strips types without checking them, so `node script.ts` succeeding tells you nothing about correctness.
2. `pnpm eslint .` passes (or `--fix` was run). On Biome repos: `pnpm biome check --write .`.
3. `pnpm prettier --check .` passes (skip on Biome repos — `biome check` covers it).
4. `pnpm vitest run` passes; affected tests added/updated.
5. For UI changes: actually run the dev server and exercise the path in a browser. Type-check passing ≠ feature working.

## Common traps

- **CJS/ESM mix.** A package's `"main"` is CJS, `"module"` is ESM, `"exports"` is the modern conditional resolver. If imports break in unexpected ways, suspect this first.
- **`__dirname` in ESM** — doesn't exist. Use `import.meta.url` + `fileURLToPath` + `path.dirname`.
- **`engines.node` ignored.** `pnpm` honors it with `engine-strict=true` in `.npmrc`. Set that if version drift matters.
- **Type-only imports** — `import type { X } from "..."` not just `import { X }` when the symbol is types-only. With `verbatimModuleSyntax: true`, the compiler enforces this.
- **`process.env` is `string | undefined`** under strict mode. Don't index without a default or runtime check.
- **Node native TS strip ≠ type check.** `node foo.ts` runs even with type errors — the stripper only removes annotations. Always pair with `tsc --noEmit` in CI, or you'll ship type-broken code.
- **`enum` and `namespace` won't compile** with `erasableSyntaxOnly` on. If a dep's `.d.ts` re-exports an enum, that's fine (declaration-only); the rule only fires on your own emitting code.
- **`tsconfig` paths don't work under native Node TS.** The stripper ignores `tsconfig.json`. If you rely on `paths`, you need `tsx`, a bundler, or `node --import` with a resolver hook.
