# Stack Profile: React (Vite or Next.js)

Load this profile when the project is a React frontend — i.e. there's a `vite.config.*`, `next.config.*`, or `package.json` with `react` as a runtime dep, and the bulk of UI code is `*.tsx`. **This profile layers ON TOP of `node-typescript.md`** — load that first for the language-level rules, then this for React-specific patterns.

## Toolchain

- **Vite** for SPA / library dev — fast HMR, native ESM, simple config. Default for new SPAs. Vite's Rolldown migration is in progress; track it but don't pre-migrate.
- **Next.js 16 (App Router)** for anything that benefits from SSR/SSG/ISR. App Router with React Server Components is the only sensible default in 2026 — Pages Router is in maintenance mode. Turbopack is now the stable default bundler (10× faster cold starts); don't opt back to Webpack without reason.
- **`react` 19.2** is stable and the production target. Native `<form>` actions, ref-as-prop, `use()` hook for promises and context, Activity API, `useEffectEvent`.
- **React Compiler 1.0** shipped stable in Oct 2025 and is battle-tested in Meta production. **Turn it on for new projects** (`babel-plugin-react-compiler` + the ESLint plugin). It auto-memoizes — so manual `useMemo`/`useCallback`/`React.memo` become anti-patterns once it's enabled. Compatible back to React 17 via `react-compiler-runtime`.
- **TypeScript strict mode** mandatory (see `node-typescript.md` for the baseline `tsconfig.json`).

## Component conventions

- **Functional components only.** Class components are legacy — no new ones.
- **One component per file.** Filename matches the component (`Button.tsx` for `export function Button`). Co-locate component-specific styles, types, and tests next to it.
- **Named exports, no defaults** (per `node-typescript.md`). Default exports break refactor tools and tree-shaking.
- **Props typed as `interface` or `type`** with explicit `Props` suffix. Don't inline-destructure types in the param list for non-trivial shapes.
- **Children typed as `ReactNode`**, not `JSX.Element` (more permissive, accepts strings/numbers/fragments).
- **Use the React 19 ref-as-prop convention** — `forwardRef` is deprecated and lints as legacy. New components: `function Input({ ref, ...props }: Props & { ref?: Ref<HTMLInputElement> })`. Existing `forwardRef` calls can be auto-migrated via the `react-19-migration` codemod; don't hand-roll.
- **`use()` for unwrapping promises and context** is the new primitive. It's conditional-safe (unlike hooks), can be called inside `if` branches, and works with Suspense — the standard pattern for "I have a promise from a Server Component, render it on the client." Don't reach for `useEffect`+`useState` to await something anymore.

## Hooks discipline

- **Hooks at the top of the function**, before any conditionals or early returns. Rules of Hooks aren't suggestions — they're load-bearing for React's per-render hook order.
- **Never use `useEffect` for derived state.** If you can compute it from props/state, compute it inline (or `useMemo` if expensive). `useEffect` for derived state creates a render-then-correct loop and breaks SSR.
- **`useEffect` is for synchronizing with external systems** (subscriptions, DOM imperative APIs, browser-only APIs, non-React mutations). If the dep array contains only React state, you almost certainly don't need `useEffect`.
- **Custom hooks for shared stateful logic.** `use<Verb>` naming, returns the minimal shape callers need.
- **`useState` setter functional form** when the new value depends on the old: `setCount(c => c + 1)`. Avoids stale-closure bugs.
- **With React Compiler enabled (the default for new projects), stop writing `useCallback`, `useMemo`, and `React.memo` by hand.** The compiler memoizes more aggressively and more correctly than humans. Manual memoization fights the compiler and adds noise. Without the compiler: reach for them only when profiling shows measurable wasted work, never by default.
- **Run `eslint-plugin-react-compiler`** (now `eslint-plugin-react-hooks` v6 with the compiler rules folded in). It flags Rules-of-React violations the compiler can't optimize around — mutations during render, conditional hooks, etc.

## State management

- **The 2026 stack: TanStack Query + Zustand + React Hook Form.** Most apps need nothing else. Server state, client state, and form state are three distinct disciplines — don't conflate them in one store.
- **Local state by default** — `useState` / `useReducer`. Don't reach for global state until two non-sibling components actually need to share.
- **Server state ≠ UI state.** For data-fetching in client components, `@tanstack/react-query` v5 is the default. NOT Redux/RTK Query for new projects. NOT a hand-rolled `useEffect` + `useState` fetch. SWR is acceptable only for trivial Next.js needs where bundle size dominates — TanStack Query's mutation state machine + devtools win for anything non-trivial.
- **In Next.js App Router, prefer Server Components + `fetch()` + `use()` over TanStack Query** for read-heavy pages. Bring TanStack Query in for client-side mutations, optimistic updates, and infinite queries.
- **Global UI state:** `zustand` for new projects (small, no boilerplate, ~4M weekly downloads, the de facto winner). `jotai` only if state is genuinely atomic/derived and "stores" feel forced. Redux Toolkit only if the team already uses Redux — don't pick it for greenfield. Avoid Context for high-frequency updates — every consumer re-renders on any change.
- **Form state:** `react-hook-form` + `zod` (via `@hookform/resolvers/zod`) for validation. TanStack Form is a credible challenger with better TS inference but a smaller ecosystem — only choose it if RHF's uncontrolled model bites you. Hand-rolled forms with multiple `useState`s become unmaintainable past 3 fields.

## Routing

- **Vite SPA:** `react-router` v7 (the merged former Remix-router). File-based routing via `@react-router/fs-routes` if you want it, or declarative `<Route>` config.
- **Next.js:** App Router (`app/`) — file-based, RSC-aware. Don't mix App Router and Pages Router in the same repo unless mid-migration.

## Server Components (Next.js App Router specifically)

- **Default to Server Components.** They're zero-bundle, can `await` directly, and have full server access. Push the `"use client"` boundary as far down the tree as possible — leaves, not roots.
- **`"use client"` only when needed:** state, effects, browser APIs, event handlers. The directive is file-level — it makes that file AND its imports client-bundle. A common smell: a "use client" wrapper around a whole page when only a button needed it.
- **Server Actions** (`"use server"`) are stable for form submissions and mutations — RPC without writing a route. Treat them like any public endpoint: validate input with zod, check auth, never trust the closed-over scope. Next.js 14+ generates unguessable action IDs and dead-code-eliminates unused ones, but that is NOT auth.
- **`useActionState` + `useFormStatus`** are the React 19 primitives for action UX (pending state, error reduction, optimistic results). Pair with `useOptimistic` for instant UI feedback that rolls back on error.
- **Partial Prerendering (PPR)** is stable in Next.js 16 — combine a static shell with dynamic holes streamed in. Opt in per-route; don't blanket-enable.
- **Streaming + Suspense:** wrap async work in `<Suspense fallback={...}>`. Loading states get colocated with the component, not lifted to a top-level "is anything loading" flag.
- **Caching pitfall:** Next.js 15+ defaults flipped — `fetch` is no longer cached by default, `GET` route handlers are no longer cached. Be explicit with `cache: 'force-cache'`, `cacheLife`, and `cacheTag` (now stable, no `unstable_` prefix). Don't assume the old defaults.

## Styling

- **Pick one and stick with it per project.** Mixing CSS Modules + Tailwind + emotion = nobody knows where styles live.
- **Tailwind CSS v4** for new projects. v4 ships a Rust-based Oxide engine (5× faster full builds, 100× faster incremental), CSS-first config via `@theme` directives in your CSS file (no more `tailwind.config.js`), automatic content detection (no `content: []` array), and a single `@import "tailwindcss"` entry point. Use the `@tailwindcss/vite` plugin for Vite — tightest integration. Browser baseline is Safari 16.4+/Chrome 111+/Firefox 128+; verify your support matrix before adopting.
- **CSS Modules** if Tailwind doesn't fit (component libraries that ship CSS, projects with strict design systems wanting semantic class names).
- **CSS-in-JS (`emotion`, `styled-components`) is fading.** Runtime cost + RSC incompatibility. Don't pick for new work; existing projects can stay if they're working.
- **`clsx` / `cn`** for conditional class composition. Don't string-concat class names.

## Accessibility

- **`eslint-plugin-jsx-a11y`** in the lint config. Catches the cheap stuff (alt text, label associations, role typos).
- **Semantic HTML first.** `<button>` not `<div onClick>`. `<a>` not `<button>` for navigation. Roles are a fallback when semantics don't fit.
- **Keyboard navigation:** every interactive element must be reachable via Tab and operable via Enter/Space. Test with the keyboard before claiming a UI works.
- **`aria-*` attributes are last resort** — semantic HTML usually obviates them.
- **Color contrast ≥ 4.5:1** for body text. Use a checker; don't eyeball.

## Testing

- **`vitest` + `@testing-library/react`** — per `node-typescript.md`. Test behavior (what the user sees and does), not implementation (which hook fired, what the state value is internally).
- **`screen.getBy*` over `container.querySelector`.** Testing Library queries mirror how users find things (by label, by role, by text).
- **`userEvent` over `fireEvent`.** Higher-fidelity simulation (focus, keypress sequences).
- **Avoid `act()` wrappers** unless the warning specifically tells you to. Modern Testing Library auto-wraps.
- **Snapshot tests sparingly** — they rot fast and reviewers rubber-stamp updates. Use for stable presentational output (icons, formatted strings); avoid for whole-component output.
- **Component testing in isolation:** Storybook 9 is the current major (Vitest-powered, Test Addon merged in, ~half the install size of 8). Stories double as Vitest test cases via `@storybook/addon-vitest` — write the story once, get visual + interaction + a11y testing.
- **Playwright Component Testing** is still experimental — prefer Vitest browser mode (real browser, Vite-native) for component tests that need a real DOM. Reserve Playwright for full-page E2E.
- **Visual regression** (Chromatic, Percy, Playwright screenshots) for component libraries and design-system-heavy UIs.
- **End-to-end** (Playwright) for critical user journeys. Don't test everything E2E — the test pyramid still applies.

## Verification ritual

Before claiming a React change is done:

1. `pnpm tsc --noEmit` clean.
2. `pnpm eslint .` clean (jsx-a11y included).
3. `pnpm vitest run` passes.
4. **Run the dev server and exercise the change in a browser.** This is non-negotiable. Type-check passing means the code compiles, NOT that the feature works. Click the buttons, fill the forms, navigate the routes.
5. Check keyboard navigation for the affected UI.
6. Check the change in the smallest mobile viewport AND a desktop width — responsive issues are easy to ship.

## Common traps

- **`useEffect` infinite loop.** Effect that mutates state in its dep array → re-runs forever. Almost always means the effect is wrong (should be derived state).
- **Stale closures.** A function captured in `useCallback`/`useEffect` references state that's stale. Either include the dep correctly OR use the functional setter form OR use a ref for "always latest" reads.
- **`key` prop on lists** — must be stable and unique. Index-as-key is OK only if the list never reorders. Otherwise React re-uses DOM nodes incorrectly across renders.
- **Hydration mismatch (SSR).** Server renders one thing, client renders another → React tears down the server output. Common causes: `Date.now()` / `Math.random()` in render, `window`-gated branches without a `useEffect` flip, locale-sensitive formatting.
- **Context performance.** Context value reference changes → every consumer re-renders. Memoize the value if it's an object/array; split context if some consumers care about A and others about B.
- **Bundling client-only code into server bundles** (Next.js) — gates check `typeof window !== "undefined"` are a smell. Reorganize so the import only happens client-side. `import 'server-only'` and `import 'client-only'` are the canonical guards.
- **Forgetting Next.js 15+ caching flipped to opt-in.** Pages that "used to be fast" suddenly hit your DB on every request because `fetch` is no longer cached by default. Audit explicitly.
- **Manual `useMemo`/`useCallback` after enabling React Compiler.** The React team's framing is "no longer needed" — the compiler memoizes more aggressively and more correctly. Existing manual memoization rarely *hurts* but adds noise and can occasionally over-memoize compared to what the compiler infers. Default to deleting manual memoization in compiler-on code; keep it when profiling shows the compiler missed something specific.
- **Mixing async Server Components with client-side data libs.** If a parent Server Component already `await`-fetched the data, don't wrap the child in TanStack Query for the same resource — you'll fetch twice. Pass the data as props or pass the promise + `use()` it on the client.
