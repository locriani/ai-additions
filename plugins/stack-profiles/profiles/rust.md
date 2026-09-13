# Stack Profile: Rust

Load this profile when the project is Rust — i.e. there's a `Cargo.toml` at the repo root or in any workspace member, and the bulk of tracked code is `*.rs`.

## Toolchain

- **`rustup`** — toolchain manager. Install via `brew install rustup-init && rustup-init`.
- **`cargo`** — build/test/dep manager. Ships with rustup.
- **`clippy`** — linter (`rustup component add clippy`).
- **`rustfmt`** — formatter (`rustup component add rustfmt`).
- **`cargo nextest`** — the recommended test runner for anything beyond a tiny crate. Up to ~3× faster than `cargo test`, expression-language test selection, JUnit output, CI partitioning. Install: `cargo install cargo-nextest --locked`.
- **`sccache`** — shared compilation cache wrapper around `rustc`. On macOS this is the highest-leverage build-perf win (mold is Linux-only; don't bother on Darwin — use the default `ld` or `lld`). Wire via `RUSTC_WRAPPER=sccache` or `.cargo/config.toml`.
- **`rust-analyzer`** — LSP, used by Claude Code's built-in `LSP` tool when present. Install via rustup or your editor.

Skip `cargo-edit` — `cargo add` / `cargo rm` / `cargo upgrade` have shipped in stable cargo since 1.62 (2022). Anything still recommending the standalone crate is stale.

## Project shape

- **`Cargo.toml`** with `edition = "2024"` for new projects. Edition 2024 stabilized in Rust 1.85 (Feb 2025) and is the current default for `cargo new`. Existing 2021 projects: migrate via `cargo fix --edition` when convenient — it's a controlled, lint-driven migration, not a rewrite. The edition is not the toolchain version; it's a language opt-in. Also set `rust-version = "1.85"` (or your minimum) so the resolver respects MSRV.
- **`Cargo.lock`** committed for binaries; library-only crates can opt out but the modern guidance is "commit it for libraries too."
- **Workspaces** (`[workspace]` in root `Cargo.toml`) for multi-crate repos — share `Cargo.lock`, target dir, and dependency resolution.
- **`rust-toolchain.toml`** at the repo root pinning channel + components — makes `cargo` invocations reproducible across contributors.
- **`.cargo/config.toml`** for per-repo build/lint settings; don't dump these in env vars.

## Strict lints — minimum baseline

In `Cargo.toml` (or `clippy.toml`):

```toml
[lints.rust]
unsafe_code = "forbid"  # if no unsafe needed; "deny" if some is, with audit
missing_debug_implementations = "warn"
unreachable_pub = "warn"

[lints.clippy]
pedantic = { level = "warn", priority = -1 }
nursery = { level = "warn", priority = -1 }
# explicit denies
unwrap_used = "deny"
expect_used = "warn"
panic = "warn"
# 2025-era lints worth turning on explicitly
ptr_eq = "warn"            # 1.87+ — prefer std::ptr::eq for raw-pointer compares
io_other_error = "warn"    # 1.87+ — std::io::Error::other(_) over ::new(Other, …)
```

Override `pedantic`/`nursery` lints case-by-case with `#[allow(clippy::<lint>)]` and a one-line comment explaining why. Clippy's feature freeze ended Oct 2025 — expect a steady stream of new lints; re-baseline after each toolchain bump.

## Common commands

```bash
cargo build                          # debug build
cargo build --release                # release build
cargo run                            # debug run
cargo run --release                  # release run
cargo nextest run                    # tests (preferred)
cargo test                           # tests (fallback)
cargo clippy --all-targets --all-features -- -D warnings   # lint, warnings as errors
cargo fmt --check                    # format check
cargo fmt                            # format in place
cargo doc --open                     # build + open rustdoc
cargo update                         # bump deps within constraints
cargo audit                          # security audit (cargo install cargo-audit)
cargo machete                        # find unused deps (cargo install cargo-machete)
```

## Code conventions

- **`unwrap()` and `expect()` are banned in lib code.** They're acceptable in `fn main`, in tests, and in scripts where the failure mode is "we abort with a clear panic message and that's fine." Anywhere else, return `Result<_, _>`.
- **`?` for error propagation** — handle the error or propagate. `match` on `Result` only when you do something different per variant.
- **`thiserror` 2.x** for library-grade error types (derive `Error`). 2.0 (Nov 2024) is the current line — it requires `thiserror` as a direct dep wherever the derive is invoked, supports `no_std` via disabling the `std` feature, and tightened format-string handling (raw-identifier `{r#type}` is gone — use `{type}`). Migrate from 1.x; the breakage is small and the `no_std` story alone is worth it. **`anyhow`** for application/binary code where the error chain is what matters and you don't need typed branching. Don't mix the two in the same crate's public API.
- **`#[must_use]`** on builders, on functions returning `Result`/`Option` that callers must inspect, and on any return value where ignoring it is a bug.
- **No `unsafe` without a `// SAFETY:` comment** stating exactly what invariant the call upholds. `unsafe { ... }` blocks without justification are non-mergeable.
- **`Box<dyn Trait>` over `impl Trait` returns** when the function may return different concrete types from different code paths. Use `impl Trait` for "I'm returning some concrete type and the caller doesn't need to know which."
- **Lifetimes:** elide where possible (the compiler's elision rules cover most cases). Where you must name them, prefer single-letter (`'a`) for short scopes, descriptive (`'arena`, `'src`) for longer-lived references.
- **Don't fight the borrow checker — restructure.** A borrow checker error means the design has shared mutability that wasn't designed in. Reach for `&mut self` or interior mutability (`Cell`/`RefCell`/`Mutex`) deliberately, not by tacking on `Rc<RefCell<T>>` reflexively.
- **`String` vs `&str`:** owned (`String`) for storage, borrowed (`&str`) for params. `&str` is the default param type unless you specifically need ownership.
- **`Vec<T>` vs `&[T]`:** same — owned for storage, borrowed for params.

## Async

- **`tokio`** is the default runtime. `async-std` is dead. `smol` for niche use cases.
- **Don't mix runtimes.** Picking `tokio` is a project-level choice, not a per-crate one.
- **`async fn` in traits (AFIT) and return-position `impl Trait` in traits (RPITIT)** stable since Rust 1.75 (Dec 2023). Use the native syntax for static dispatch. **The `async-trait` macro is NOT obsolete** — AFIT traits are not dyn-compatible (no `dyn Trait` / no trait objects). If you need dynamic dispatch over an async trait, you still need `async-trait` (which boxes the future) or hand-roll `Pin<Box<dyn Future<Output = …> + Send>>`. The `trait-variant` crate is the modern middle ground: write the trait once natively, generate a `Send`-bounded variant for spawning. Default: native AFIT; reach for `async-trait` only when you've actually hit the dyn-compatibility wall.
- **`Send + Sync` bounds** — every spawned task needs `Send`. If you find yourself wrapping `!Send` types in `Arc<Mutex<...>>` to satisfy this, the code wants a redesign.
- **Cancellation** — `tokio::select!` is the dropping mechanism. Don't assume futures clean up on cancel; they only `drop`. Resource cleanup goes in `Drop` impls or explicit cancellation handlers.

## Testing

- **`cargo nextest run`** — faster, better output, parallel by default. Configure in `.config/nextest.toml` at the workspace root with named profiles (`default`, `ci`, etc.). For CI, set a `ci` profile with `junit` output and use nextest's partition expressions to shard across jobs. Doctests still go through `cargo test --doc` — nextest doesn't run them.
- **Inline `#[cfg(test)] mod tests { ... }`** at the bottom of each source file. Integration tests in `tests/`.
- **`#[test]`** for sync, **`#[tokio::test]`** for async (with the `tokio` test feature).
- **`assert_eq!` over `assert!(a == b)`** — better diagnostic on failure.
- **`pretty_assertions`** dev-dep for prettier diffs in failing assertions.
- **`insta`** for snapshot testing — far better than hand-rolled equality assertions for complex structs.
- **`proptest` / `quickcheck`** for property-based testing where the input space is large.

## Verification ritual

Before claiming a Rust change is done:

1. `cargo build` clean — no warnings.
2. `cargo clippy --all-targets --all-features -- -D warnings` clean.
3. `cargo fmt --check` clean.
4. `cargo nextest run` (or `cargo test`) passes; affected tests added/updated.
5. `cargo doc` builds with no warnings if the change touches `pub` items (rustdoc warnings turn into broken docs.rs renders).
6. For binary crates: `cargo run --release` actually exercises the change end-to-end.

## Common traps

- **`.clone()` in tight loops** — easy to write, expensive to run. Profile before assuming it's fine; restructure to borrow if it's hot.
- **`Vec::push` in a hot loop without `with_capacity`** — repeated reallocations. If you know the size, set capacity upfront.
- **`HashMap` default hasher** — DoS-resistant but slow. For internal-only maps, `ahash` or `rustc-hash` is 2-3× faster. Don't change for user-facing maps where the DoS resistance matters.
- **`async` function returning a borrow** — the returned future captures the borrow; the future's lifetime is tied to it. Often surfaces as confusing lifetime errors when storing futures in collections.
- **Macro-heavy crates** (especially proc macros) blow up compile times. `serde_derive` is ~unavoidable; `derivative`, `display-derive`, etc. are nice-to-have. Audit if compile times are a problem.
- **`println!` in lib code** — use `tracing` or `log` with a real backend. `tracing` is the default for new code; `log` for legacy or minimal binaries.
- **`async-trait` reflex** — reaching for the macro before checking whether you actually need `dyn Trait`. Native AFIT (Rust 1.75+) covers most cases; the macro adds a per-call heap allocation for the boxed future. Audit existing `#[async_trait]` annotations during any refactor.
- **Skipping `cargo fix --edition` on a 2021 crate** — the migration is tooled and incremental. Stay on 2021 deliberately, not by neglect.
- **No `rust-toolchain.toml` in a repo with multiple contributors** — silent toolchain drift. Pin the channel + components and commit it.
