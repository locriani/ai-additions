# Stack Profile: Swift / Apple Platforms

Load this profile when the current project is a Swift / SwiftUI / iOS / macOS / watchOS / tvOS / visionOS app or framework — i.e. there's a `*.xcodeproj`, `*.xcworkspace`, `Package.swift`, or `project.yml` in the repo root.

## Toolchain baseline

Assume **Xcode 26 / Swift 6.2** unless the repo's `CLAUDE.md` pins something older. Swift 6.2 ships **Approachable Concurrency** (`SWIFT_APPROACHABLE_CONCURRENCY=YES`) with **default actor isolation = MainActor** and **strict concurrency = complete** as the *new-project defaults* in Xcode 26 — i.e. all code is implicitly `@MainActor` unless you mark it `nonisolated` or pin it to another actor. New Xcode-26 projects are effectively single-threaded by default and you opt *out* with `nonisolated` when you want concurrency.

For older projects migrating, treat Approachable Concurrency as the target end state — turn it on at the project level, then fix `nonisolated` annotations on background work (networking, file I/O, CPU-bound). Don't sprinkle `@MainActor` everywhere; the default already covers it.

## Project generation: xcodegen, Tuist, or pure SPM — pick deliberately

Three legitimate shapes in 2026; pick by repo size and don't mix:

- **Pure Swift Package Manager** (`Package.swift` only, no `.xcodeproj`) — preferred for libraries, frameworks, CLI tools, and small apps that don't need Xcode-specific build phases. Xcode opens `Package.swift` directly. Zero generation step.
- **[XcodeGen](https://github.com/yonaskolb/XcodeGen) + `project.yml`** — preferred for single-target / small-to-medium apps that need an `.xcodeproj` (storyboards, asset catalogs, build phases, capabilities). YAML config, lightweight, still actively maintained.
- **[Tuist](https://tuist.dev)** — preferred for modular apps (3+ first-party modules), monorepos, or anything that benefits from build caching, scaffolding, and Swift-typed config. Tuist is the modern choice when XcodeGen's YAML starts to creak.

When the repo already has a generator, use it — don't migrate as a side effect of unrelated work.

**For XcodeGen repos:** `*.xcodeproj` is a generated artifact. Never hand-edit it, never commit conflicts in it. `project.yml` is the source of truth.

**Regenerate `*.xcodeproj` on every turn that touches `project.yml` or adds/removes/renames source files.** Concretely:

1. Before building, testing, or running: if any of the above changed since the last `xcodegen generate`, run it now.
2. After adding/removing/renaming a `.swift` file: run `xcodegen generate` immediately, then continue.
3. End-of-turn ritual on any turn that touched the file tree under a target's `sources:` glob: re-run `xcodegen generate` before reporting done. The generated `*.xcodeproj` should always be in sync with `project.yml` and the on-disk file tree at the moment of the commit.

For Tuist repos, the equivalent is `tuist generate` after editing `Project.swift` / `Workspace.swift` or moving sources.

If the repo has a raw `*.xcodeproj` with no generator, propose adopting one (XcodeGen for simple, Tuist for modular) before non-trivial structural changes. Don't silently keep editing the raw pbxproj.

If `xcodegen` isn't installed, install via `brew install xcodegen`. For Tuist: `curl -Ls https://install.tuist.dev | bash`.

**Per-repo automation:** there is an installable `PostToolUse` hook at [`~/Developer/Standard Configs/claude-plugins/xcodegen-hook/`](~/Developer/Standard%20Configs/claude-plugins/xcodegen-hook/) that runs `xcodegen generate` automatically whenever an `Edit` / `Write` touches a `project.yml`. Install with `~/Developer/Standard\ Configs/claude-plugins/xcodegen-hook/apply.py <repo>`. Idempotent, merges with any existing `.claude/settings.json`, no-ops cleanly when `xcodegen` isn't installed. Use this in any xcodegen repo where you want the regenerate step to be impossible to forget — it does not replace the rules above (file moves still need a manual regen), but it removes the most common failure mode.

## Build / test / run: xcodebuild + xcrun simctl

Use raw `xcodebuild`, `xcrun simctl`, and `xcrun xctrace` for every Xcode build/test/sim/device operation. Pipe through `xcbeautify` (or `xcpretty`) when the raw output is too noisy to skim — `brew install xcbeautify` if missing.

Canonical invocations:
- **Discover schemes/destinations:** `xcodebuild -workspace Foo.xcworkspace -list` (or `-project Foo.xcodeproj -list`); `xcrun simctl list devices available`.
- **Build for simulator:** `xcodebuild -workspace Foo.xcworkspace -scheme Foo -destination 'platform=iOS Simulator,name=iPhone 16' -configuration Debug build | xcbeautify`.
- **Test:** `xcodebuild -workspace Foo.xcworkspace -scheme Foo -destination 'platform=iOS Simulator,name=iPhone 16' test | xcbeautify`. Filter targets/tests via `-only-testing:FooTests/SomeSuite/test_case`.
- **Boot + install + launch:** `xcrun simctl boot <udid>` → `xcrun simctl install <udid> path/to/Foo.app` → `xcrun simctl launch --console <udid> com.example.Foo`.
- **Logs:** `xcrun simctl spawn <udid> log stream --predicate 'subsystem == "com.example.Foo"'`.

**Subagent rule (from global CLAUDE.md):** any build or test run produces multi-MB log output → dispatch a subagent to run the command and return a summary (failing tests, warning counts, exit status). Don't read raw build logs in main context.

## xcode-mcp (`xcrun mcpbridge`)

Active when Xcode is running. Query the Xcode workspace, build, test, run apps, manage simulators.

- Xcode must actually be open on the target project before you use the Xcode tools.
- Subagents can't bridge to Xcode unless you grant them the MCP tools.

**Never raise an xcode-mcp permission prompt outside an Apple project.** Both conditions are required:

```
ask_xcode_permission → swift ∧ (project.yml ∨ *.xcworkspace ∨ *.xcodeproj)
contrapositive:  ¬swift ∨ ¬(project.yml ∨ *.xcworkspace ∨ *.xcodeproj)  ⊢  ¬ask
```

A Swift package with no project file, or a non-Swift repo that merely has Xcode open, both fail the gate — of the user *and* on a subagent's behalf. Silence is correct; don't ask "just in case."

Install/wiring: `~/Developer/Standard Configs/external/xcode-mcp/README.md`.

## Code intelligence: swift-lsp

`sourcekit-lsp` (ships with Xcode) is wired into Claude Code's built-in `LSP` tool via the `swift-lsp@claude-plugins-official` plugin. Use `LSP` for goToDefinition, findReferences, hover, documentSymbol, etc. — don't grep when LSP can answer authoritatively.

For `*.xcodeproj` / `*.xcworkspace` projects, ensure `xcode-build-server` has been bootstrapped at least once via [`~/Developer/Standard Configs/external/swift-lsp/templates/setup-xcode-project.sh`](~/Developer/Standard Configs/external/swift-lsp/templates/setup-xcode-project.sh). For SwiftPM-only projects, no bootstrap needed — sourcekit-lsp reads `Package.swift` directly.

## Testing: swift-testing-toolkit plugin

For any work involving Xcode test targets — XCTest unit tests, Swift Testing (`import Testing` / `@Test` / `#expect`) tests, XCUITest UI tests, xcresult triage, or running the full suite — use the **`swift-testing-toolkit` Claude plugin** (from [`locriani/swift-testing-toolkit`](https://github.com/locriani/swift-testing-toolkit)). It exposes:

- `swift-xcuitest-author` skill — guidance for authoring or editing XCUITest code (selectors, accessibility identifiers on SwiftUI, waits, flake reduction, SwiftUI control gotchas like Menu/Picker/List swipe/NavigationStack, launch arguments, screenshots on failure, macOS vs iOS test-target splits).
- `xcresult-failure-triage` skill — parse `.xcresult` bundles via `xcrun xcresulttool` (handles the Xcode 16 `--legacy` deprecation), extract attachments, classify the failure (flake / selector / assertion / setup / infra), recommend a fix.
- `xctest-checklist` skill — run the FULL test suite across every test target a project ships (iOS / macOS / watchOS / tvOS / visionOS / Catalyst, Unit + UI). Build-once + `xcodebuild -parallel-testing-enabled YES` per target. Emits a three-tier Markdown checklist (per-class → per-target `_index.md` → top-level `Summary.md`) with machine-extractable failure references and JSON sidecars. Backed by a stdlib-Swift CLI orchestrator `stt-report` (built from `Sources/stt-report/` via SwiftPM).
- `uitest-scaffold` slash command — scaffold a new XCUITest file using the canonical `UITestCase` base class.
- `uitest-flake-triage` slash command — re-run a single XCUITest, parse the resulting xcresult, classify the failure.
- `ui-test-review` slash command + `ui-test-reviewer` subagent — review XCUITest changes against the 50-rule `XCUITEST_REFERENCE.md` checklist.

**Trigger conditions:**
- Authoring or editing UITest code → invoke `swift-xcuitest-author` before writing.
- New UITest file → invoke `/uitest-scaffold` rather than hand-rolling boilerplate.
- A test failed and you have an xcresult bundle → invoke `xcresult-failure-triage`.
- "Run all the tests / generate a test report" → invoke `xctest-checklist`.
- UITest changes ready for review → invoke `/ui-test-review`.

If the plugin isn't installed in this environment, install via the Standard Configs runbook at [`~/Developer/Standard Configs/external/swift-testing-toolkit/`](~/Developer/Standard Configs/external/swift-testing-toolkit/) (it clones [`locriani/swift-testing-toolkit`](https://github.com/locriani/swift-testing-toolkit) and registers the marketplace), or clone the side repo directly and run its `apply.sh`.

## Swift agent skills: /enable-swift-skills

A curated set of 8 Swift / Apple-platform **agent skills** (from the
`swift-agent-skills` marketplace) is available but installs **dormant** — they
are scoped to Swift projects only and must be enabled per repo. The set:
`swiftui-pro`, `swiftdata-pro`, `swift-concurrency-pro`, `swift-testing-pro`,
`swift-api-design-guidelines`, `swift-accessibility-skill`, `app-intents`,
`swift-architecture-skill`.

**Trigger conditions:**
- On landing in a Swift project (this profile's triggers: `*.xcodeproj`,
  `*.xcworkspace`, `Package.swift`, `project.yml`, or editing `*.swift`) and the
  skills are not yet enabled here → run **`/enable-swift-skills`** once. It
  enables all 8 at `--scope local` (writes `.claude/settings.local.json`,
  gitignored — personal, never committed into the repo). Re-running is
  idempotent; skip if the repo already has these in `settings.local.json`.

If `/enable-swift-skills` is missing or the marketplace isn't installed, install
via the Standard Configs runbook at [`~/Developer/Standard Configs/external/swift-agent-skills/`](~/Developer/Standard Configs/external/swift-agent-skills/) (`apply.py`). Update the skills with `./update-all.py swift-agent-skills`, never `claude plugin update`.

## Project conventions (apply when these aren't already set in the repo's own `CLAUDE.md`)

- **One public type per file.** Filename matches the type. Internal helpers can share a file.
- **Prefer SwiftUI over UIKit / AppKit** for new screens unless the repo's existing convention dictates otherwise. Where SwiftUI gaps require UIKit, wrap in `UIViewRepresentable` rather than scattering UIKit through the codebase.
- **State management: `@Observable` macro, not `ObservableObject`.** For any new model type that drives SwiftUI (iOS 17+ / macOS 14+), annotate the class with `@Observable` from the Observation framework. Drop `@Published`, drop `ObservableObject` conformance. Views own them with `@State` (not `@StateObject`); pass them down as plain properties (not `@ObservedObject`); inject via `.environment()` (not `.environmentObject()`). The macro gives precise per-property invalidation — `ObservableObject` re-renders every observer on any `@Published` change. Only fall back to `ObservableObject` when the deployment target is iOS 16 or earlier.
- **Persistence: SwiftData for new projects** when the deployment target is iOS 17+ / macOS 14+. CoreData is reserved for (a) projects pinned to iOS 16 or earlier, (b) Public CloudKit databases, (c) heavy migration / complex relationship graphs where SwiftData's abstraction still bites. SwiftData is CoreData under the hood — you don't lose performance fundamentals, you lose boilerplate. For greenfield, default to SwiftData; only justify CoreData with a specific reason from the list above.
- **Tests: Swift Testing for new unit tests, XCTest for UI tests.** Unit tests get `import Testing` + `@Test` + `#expect(...)` — parallel-by-default, randomized-by-default, parameterized-by-default. UI tests stay on XCTest because **XCUITest is XCTest-only** in 2026 — Swift Testing has no `XCUIApplication` equivalent. Don't migrate working XCTest unit suites; just write new tests in Swift Testing alongside the old ones (the runner handles both).
- **Targets isolated per platform.** iOS / macOS code that diverges goes in platform-specific targets or `#if os(...)` blocks — don't ship platform-conditional behavior buried inside shared types unless trivial.
- **Test naming:** Swift Testing uses descriptive names: `@Test("rejects negative balances")` — write it like prose. XCTest unit tests: `test_<methodOrBehavior>_<condition>_<expectedOutcome>`. UI tests: `test_<userJourney>`.
- **Bump CFBundleVersion every session that produces a release-candidate build.** The convention is monotonic integers per the project's release script — don't bump in dev-only sessions.
- **Format every `.swift` file before it lands.** Use the toolchain built-in `swift format` (ships with Swift 6 / Xcode 16+; zero install; respects a repo's `.swift-format` config if one exists, defaults otherwise). Don't hand-tune whitespace or fight the formatter — let it own layout. There is an installable per-repo `Stop` hook at [`~/Developer/Standard Configs/claude-plugins/swift-format-hook/`](~/Developer/Standard%20Configs/claude-plugins/swift-format-hook/) that runs `swift format --in-place` on the turn's dirtied `.swift` set automatically (end-of-turn, not per-edit, to avoid rewriting files mid-turn). Install with `~/Developer/Standard\ Configs/claude-plugins/swift-format-hook/apply.py <repo>` in any Swift repo so formatting is impossible to forget — it does not replace this convention (the hook no-ops on old toolchains), it enforces it.

## Common traps

- **iOS 18+ broke pre-iOS-18 Menu touch-response workarounds.** If the repo carries a `Menu` workaround (background-tap-through, custom gesture priority hack), it likely no-ops or actively misbehaves on iOS 18+. Verify on a current simulator before assuming inherited code still works. Check `#available(iOS 18, *)` branches.
- **Picker XCUITest still flakes via `adjust(toPickerWheelValue:)`** — it steps one item at a time toward the target, not jumping. Long lists time out. Prefer setting picker values via launch arguments + a debug hook, or use `.menu` style pickers (driven by tap, not wheel scroll). Defer to the `swift-xcuitest-author` skill before authoring picker tests.
- **`@Observable` + `@State` is NOT a drop-in for `@StateObject` + `ObservableObject`.** Initialization timing differs: `@State` constructs the value on first render and never reinitializes, while `@StateObject`'s autoclosure semantics differ. Don't rely on construction-side-effects firing on view re-creation.
- **Approachable Concurrency means most code is `@MainActor` by default in Xcode 26.** When porting library code in or hitting actor-isolation errors, the fix is often `nonisolated` on the type/method, not `@MainActor` somewhere else. Don't reflexively reach for `Task { @MainActor in ... }` — the wrapper's redundant when the call site is already main-isolated.
- **SwiftData migrations are not as forgiving as CoreData's.** For schemas that need versioned migration logic across releases, design the `VersionedSchema` + `SchemaMigrationPlan` up front; retrofitting is painful. If the project ships heavy migrations weekly, this is the strongest argument for staying on CoreData.
- **`*.xcodeproj` merge conflicts are a smell, not a normal event.** If you see one in an XcodeGen / Tuist repo, the fix is to regenerate, not to hand-resolve the pbxproj. Hand-resolving silently corrupts file references.
- **`Package.resolved` is generated — never hand-edit it.** It's rewritten by `swift package resolve` (and by any build/`xcodebuild` that resolves dependencies). Manual edits produce cryptic SwiftPM resolution failures. On a merge conflict, delete it and re-resolve rather than hand-merging the pins.

## Verification ritual

Before claiming a Swift/Apple-platform task is done:

1. `xcodegen generate` (XcodeGen repos) / `tuist generate` (Tuist repos) — if config or sources changed. SPM-only repos skip this step.
2. `xcodebuild ... build` succeeds — zero warnings on the changed code, including new Swift 6.2 concurrency / `Sendable` warnings. Don't ship "warning: capture of non-sendable type" past green.
3. `xcodebuild ... test` runs the affected target's tests; they pass. The runner executes both Swift Testing (`@Test`) and XCTest (`XCTestCase`) suites in one pass — no separate command needed.
4. For UI changes: actually launch the app on a simulator (`xcrun simctl boot` + `install` + `launch`) and exercise the path. Don't claim a UI feature works because it compiles.

If any step fails, fix the root cause — don't disable tests, don't skip xcodegen. Per the global rule: failing tests get fixed without being told how.
