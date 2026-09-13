# Stack Profile: Go

Load this profile when the project is Go — i.e. there's a `go.mod` at the repo root and the bulk of tracked code is `*.go`.

## Toolchain

- **Go itself** — `brew install go`. Go's release cadence is 6 months; track latest stable (Go 1.25 as of Aug 2025) unless the repo pins via `go.mod`'s `go 1.X` directive. Targets below assume **1.24+** as the floor for new code.
- **`gopls`** — official LSP, used by Claude Code's `LSP` tool. Installed via `go install golang.org/x/tools/gopls@latest`.
- **`golangci-lint` v2** — the lint aggregator. `brew install golangci-lint`. **v2 (March 2025) is the current line and the v1 config schema is incompatible** — if a repo still has a v1 `.golangci.yml`, run `golangci-lint migrate` once to upgrade. v2 also ships `golangci-lint fmt` (formatter aggregator). v2 has **no exclusions by default** — opt into the human-readable presets you want.
- **`gofumpt`** — stricter superset of `gofmt`. Recommended for new projects: `go install mvdan.cc/gofumpt@latest`. Can be wired through `golangci-lint fmt` so you don't run a second tool.

## Project shape

- **`go.mod`** with `go 1.24+` for new code. Key version floors: **1.22** (loop-var scoping fixed, range-over-int), **1.23** (range-over-function iterators — `for x := range seq` where `seq` is `func(yield func(T) bool)`; `iter` package, `slices.All`/`Values`/`Collect`), **1.24** (generic type aliases land for real, `testing/synctest` experimental, `T.Context`/`T.Chdir`, weak pointers, `os.Root`), **1.25** (`testing/synctest` stable, container-aware `GOMAXPROCS` on Linux cgroups, experimental `encoding/json/v2`).
- **`go.sum`** committed.
- **`go.work`** is for **local development of multiple modules together** (monorepo with internal modules, or working on a library + its consumer simultaneously). It is **per-developer, not committed** — gitignore `go.work` and `go.work.sum`. Don't use workspaces as a substitute for `replace` directives in production builds; the build machine should resolve from `go.mod` alone.
- **`/cmd/<binary>/main.go`** for executables; library code under `/internal/...` (private to this module) or top-level (public).
- **`internal/` is enforced by the toolchain** — no other module can import `<repo>/internal/...`. Use it aggressively.
- **No `vendor/`** unless there's a specific reason (air-gapped builds, reproducibility for compliance). Module mode is the default.

## Common commands

```bash
go build ./...                    # build every package in the module
go test ./...                     # test every package
go test -race ./...               # tests with race detector — DO THIS for any concurrent code
go vet ./...                      # static analysis
golangci-lint run                 # full lint
go fmt ./...                      # format (gofmt)
gofumpt -l -w .                   # stricter format (if installed)
go mod tidy                       # add missing / drop unused deps
go mod download                   # populate module cache
go run ./cmd/foo                  # build + run
```

## Code conventions

- **`error` is the last return value, always.** `func F() (T, error)`, never `func F() (error, T)`.
- **`errors.Is` / `errors.As` over `==` / type assertions.** Wrapped errors (via `fmt.Errorf("%w", err)`) need the `Is`/`As` machinery to inspect. String matching on error messages is a bug.
- **Sentinel errors** are package-level vars: `var ErrNotFound = errors.New("not found")`. Caller does `if errors.Is(err, pkg.ErrNotFound)`.
- **`context.Context` as the FIRST parameter** of any function that does I/O, makes RPCs, or is cancelable. `func F(ctx context.Context, ...)`. Never `ctx` after other args.
- **Don't store `context.Context` in struct fields** — pass it through call chains. Exception: long-lived workers that need a "cancel everything" handle, where the field IS the lifecycle root.
- **No `init()` for behavior.** `init` functions for registering codecs / types with reflection are fine; using `init` to do real setup work makes import order load-bearing.
- **No `panic` in lib code** unless it's a programmer error (impossible state). Recoverable failures = `error`. Programmer errors = `panic` is OK because the caller can't handle it.
- **`interface` defined where it's USED, not where it's implemented** — Go's structural typing means consumers declare what they need. Don't pre-declare "everything that might be useful" in the producer package.
- **Small interfaces.** `io.Reader`, `io.Writer`, `error` — one method each. If your interface has > 3-4 methods, it's probably wrong.
- **Accept interfaces, return concrete types.** A function takes `io.Reader` (caller flexibility), returns `*MyType` (caller has full API surface).
- **Zero values are useful.** A `bytes.Buffer{}` is ready to use. Make your types follow this — don't require `NewFoo()` for trivial cases.
- **Generics: use sparingly, and only for container/algorithm code.** The community has settled hard on "concrete types until you have ≥2 real callers with the same shape." Good fits: collections (`slices`, `maps`), constraints over numeric types, type-safe wrappers around `sync.Map` / `sync.Pool`. Bad fits: replacing `interface{}` in business logic, "future-proofing" a single-caller function, simulating inheritance. If a function has one type parameter and one caller, it should be a concrete function. Generic type aliases (Go 1.24) make wrappers cleaner — that's their main payoff.
- **`log/slog` is the default logger.** Stdlib since Go 1.21; **prefer it over `logrus`/`zap`/`zerolog` for new code**. Use `slog.NewJSONHandler(os.Stdout, ...)` in production (parseable by Loki/CloudWatch/ES), `slog.NewTextHandler` in dev. Implement `slog.LogValuer` on types holding sensitive fields (tokens, PII) so they redact consistently. Only reach for `zap` if you have a measured hot path where slog's ~650 ns/op is genuinely the bottleneck — for nearly everything, the stdlib wins on dependency cost and API stability.
- **Iterators (Go 1.23+):** prefer `slices.All`, `maps.Values`, etc. for new range-based code. When writing a custom iterator, return `iter.Seq[T]` or `iter.Seq2[K,V]` — these are now idiomatic and replace ad-hoc callback APIs.

## Concurrency

- **`go test -race`** for any concurrent code, every time. Race detector is cheap; data races are catastrophic.
- **Channels for ownership transfer**, mutexes for protecting shared state. "Don't communicate by sharing memory; share memory by communicating" — but mutex when it's the right tool, don't force a channel.
- **`sync.Mutex` over `sync.RWMutex`** unless reads vastly outnumber writes AND the read critical section is non-trivial. RWMutex has a fixed overhead that often eats the gain.
- **`sync.Once` for one-time init** — cleaner than a flag + mutex.
- **`context` for cancellation** — every blocking call inside a `goroutine` should be cancelable via the context.
- **Don't leak goroutines.** Every `go func() { ... }` needs an exit path that runs on `<-ctx.Done()` or equivalent. Use `errgroup.WithContext` for grouped goroutines with a unified cancel.

## Testing

- **Table-driven tests** — the canonical Go pattern:
  ```go
  func TestFoo(t *testing.T) {
      cases := []struct {
          name string
          in   T
          want T
      }{
          {"empty", T{}, T{}},
          // ...
      }
      for _, tc := range cases {
          t.Run(tc.name, func(t *testing.T) {
              got := Foo(tc.in)
              if !reflect.DeepEqual(got, tc.want) {
                  t.Errorf("Foo(%v) = %v, want %v", tc.in, got, tc.want)
              }
          })
      }
  }
  ```
- **`*_test.go` next to source.** Internal tests (`package foo`) for white-box; external tests (`package foo_test`) for black-box. Both can coexist.
- **`testify` is OK but not required** — `assert.Equal` etc. are nicer than hand-rolled `if got != want { t.Errorf(...) }`. The stdlib testing API is also fine.
- **`go test -count=1`** to force re-run (Go caches passing tests by default).
- **Benchmarks** (`func BenchmarkX(b *testing.B)`) — run with `go test -bench=.` Track via `benchstat` for regression detection.
- **Fuzz tests** (`func FuzzX(f *testing.F)`) — Go 1.18+. Worth it for parsers, decoders, anything that takes untrusted input.
- **`testing/synctest`** — stable in Go 1.25 (experimental in 1.24 behind `GOEXPERIMENT=synctest`). Run a "bubble" of goroutines under a fake clock so time-dependent tests pass deterministically and instantly — replaces hand-rolled clock injection for most cases. Reach for this before adding a `clockwork`-style dependency on a fresh project.
- **`t.Context()` / `t.Chdir()`** — Go 1.24+. `t.Context()` returns a context auto-cancelled on test completion (drop-in for the boilerplate `ctx, cancel := context.WithCancel(...); defer cancel()`). `t.Chdir()` changes working directory for the test's lifetime, auto-restoring after. Use these.
- **`reflect.DeepEqual` is fine but `cmp.Diff` (`github.com/google/go-cmp/cmp`) gives better failure messages** — and is the de-facto community standard for non-trivial comparisons.

## Verification ritual

Before claiming a Go change is done:

1. `go build ./...` — clean.
2. `go vet ./...` — clean.
3. `golangci-lint run` — clean.
4. `go test -race ./...` — passes; affected tests added/updated.
5. `go fmt ./...` (or `gofumpt`) — formatted.
6. `go mod tidy` — `go.mod` / `go.sum` consistent. Diff should be empty.

## Common traps

- **Loop variable capture pre-1.22.** `for _, v := range items { go func() { use(v) }() }` captured a single `v` shared across iterations. Fixed in 1.22 — and the fix is keyed off `go.mod`'s `go` directive, NOT the toolchain version. A repo with `go 1.21` built by a 1.25 toolchain still gets the OLD behavior. Either bump the directive or `v := v` inside the loop.
- **`nil` interface vs nil concrete.** `var err error = (*MyErr)(nil); err != nil` is `true` because the interface has a type even when the value is nil. Always return `nil` directly, not a typed nil.
- **`time.Now()` in tests.** Use `testing/synctest` (Go 1.25 stable) before reaching for a third-party clock library — it covers the common "advance time, assert behavior" case without an injection seam.
- **`map[K]V` iteration order is randomized.** Don't depend on it. Sort keys explicitly if order matters.
- **`make([]T, 0)` vs `var s []T`** — both are valid, but they differ in nil semantics. `var s []T` is `nil` (which equals nil and JSON-marshals to `null`); `make([]T, 0)` is non-nil empty (JSON-marshals to `[]`).
- **`defer` in a loop.** Each iteration's deferred call piles up until function return. For per-iteration cleanup, extract to a helper function or call cleanup explicitly.
