# Stack Profile: Python (uv toolchain)

Load this profile when the project is Python — i.e. there's a `pyproject.toml`, `setup.py`, `requirements*.txt`, `*.py` files as the bulk of the tracked code, or the user is editing a `*.py` file. **Default to the modern `uv`-based toolchain** below; if the repo specifically uses `poetry` / `pipenv` / `conda` / raw `pip`, follow that convention but flag a one-line "consider migrating to uv" note in the end-of-turn summary.

## Toolchain (modern default)

- **`uv`** ([astral-sh/uv](https://github.com/astral-sh/uv)) — environment + dependency + Python version manager. Replaces `pip`, `pip-tools`, `pipx`, `virtualenv`, `pyenv`. Install: `brew install uv`. Use **uv workspaces** (Cargo-style, single root `uv.lock`, per-package `pyproject.toml`) for any repo with >1 deployable — don't reach for monorepo glue or path-deps.
- **`ruff`** — linter + formatter. Replaces `black` + `isort` + `flake8` + `pyupgrade`. Comes via `uv` deps. Don't install it standalone with brew — pin it in `pyproject.toml` so CI and local agree on rule versions.
- **`pytest`** — test runner. Add `pytest-xdist` (parallel) and `anyio` (test plugin, supersedes `pytest-asyncio` for new code; see Async section). Skip `pytest-asyncio` unless an existing project already uses it — running both conflicts.
- **Type checker** — `pyright` is the **default** for new projects (98% spec conformance, fast enough, best editor integration). `mypy --strict` is acceptable on legacy. **`ty`** ([astral-sh/ty](https://github.com/astral-sh/ty)) — Astral's Rust-based checker — entered beta in 2025 and Astral uses it in production internally. It's 10–60× faster than pyright but currently lags on conformance for advanced typing (Protocols, ParamSpec, recursive types, complex overloads). **Allowed for new projects with simple typing surface; otherwise stay on pyright.** Don't run two checkers in CI.

**Don't use globally-installed `pip install`.** Anything that escapes the project's venv is wrong. Use `uv add <pkg>` (registers in `pyproject.toml`) or `uv pip install <pkg>` (transient, in the project venv).

## Project shape

- **`pyproject.toml`** is the single source of truth. No `setup.py`, no `requirements.txt` (uv generates `uv.lock`).
- **`uv.lock`** is committed.
- **`.python-version`** pins the Python version. **Floor for new projects in 2026: Python 3.13** (`uv python pin 3.13`). 3.14 is GA (Oct 2025) but the ecosystem catch-up is still in flight; use it when you specifically want t-strings, deferred annotations, or the experimental JIT. **Don't target 3.12 for a greenfield project** unless a hard dependency forces it. **Free-threaded (no-GIL) builds are still opt-in** — single-threaded code runs ~9% slower on 3.14t and a meaningful slice of the C-extension ecosystem isn't free-thread-safe yet. Reach for `python3.14t` only when CPU-bound thread-parallelism is the actual bottleneck and you've measured it.
- **`src/<package>/`** layout preferred over flat layout — it forces correct import paths during testing and prevents accidentally importing the source dir instead of the installed package.

## Common commands

```bash
uv venv                     # create .venv (uv auto-creates on first use)
uv sync                     # install all deps from uv.lock (idempotent)
uv add httpx                # add a runtime dep
uv add --dev pytest         # add a dev dep
uv remove httpx             # remove a dep
uv run python script.py     # run inside the project's venv (no manual activate)
uv run pytest               # run tests
uv run ruff check --fix .   # lint + autofix
uv run ruff format .        # format
uv run pyright              # typecheck
uv lock --upgrade           # bump deps to latest within constraints
```

**Always prefer `uv run <cmd>` over manually activating the venv** — it's idempotent, can't get into a "wrong env activated" state, and works the same in CI.

## Code conventions

- **Type hints everywhere.** New code without hints is incomplete. On 3.13: keep `from __future__ import annotations` at the top of every file (PEP 563 strings-by-default). On 3.14+: PEP 649 makes annotations lazy by default — the `__future__` import is no longer needed and Ruff's `FA` rules will flag it; let it go.
- **`pathlib.Path` not `os.path`** for filesystem ops.
- **f-strings not `%`-formatting or `.format()`.** On 3.14+, prefer **t-strings** (PEP 750) for any string that crosses a security boundary (SQL, shell, HTML) — they're the structured alternative that lets the consumer escape correctly.
- **Structured data — pick by intent, not habit:**
  - **`dataclasses`** is the default. Plain, stdlib, fast, plays nice with type checkers. Reach for this first.
  - **`attrs`** when you want slots, converters, or validators without adopting a framework. Strictly more features than dataclasses, comparable perf.
  - **`msgspec`** for hot-path JSON/MessagePack encode-decode (4–17× faster than pydantic on object construction). Use in serialization-bound services.
  - **`pydantic` v2** *only* when you actually need validation at trust boundaries (HTTP request bodies, env config, untrusted JSON). Don't reach for it as a "fancy dataclass" — it's a validation framework with framework-sized overhead.
- **`match`/`case`** (PEP 634) for dispatch on shape. Don't reinvent visitor patterns.
- **Async only when there's actual I/O concurrency.** Don't sprinkle `async` for vibe.
- **No bare `except:`.** Catch the specific exception. `except Exception:` is the loosest acceptable.
- **`logging` not `print`** for anything that ships. `print` is for local debugging that gets removed before commit.

## Ruff configuration

Default to a strict ruleset in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
preview = true  # opt into the expanded default ruleset (B/UP/RUF on by default in preview)

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "RET", "PTH", "ERA", "PL", "RUF", "FA", "TCH", "ASYNC", "S"]
ignore = ["E501"]  # line-length handled by formatter

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "PLR2004"]  # asserts and magic numbers are fine in tests
```

`E,F,W` = pycodestyle/pyflakes. `I` = import sorting. `N` = naming. `UP` = pyupgrade. `B` = bugbear. `C4` = comprehensions. `SIM` = simplifications. `RET` = return statement smells. `PTH` = `pathlib` over `os.path`. `ERA` = no commented-out code. `PL` = pylint subset. `RUF` = ruff-specific. `FA` = future-annotations hygiene (catches stale `from __future__` on 3.14+). `TCH` = move type-only imports under `TYPE_CHECKING`. `ASYNC` = async-anti-patterns (blocking calls in coroutines, etc.). `S` = bandit security subset.

**Use `select`, not `extend-select`** — explicit ruleset, no surprise inheritance. Per Astral guidance, the default rule list is changing in preview; pinning ruff in `pyproject.toml` keeps CI and local consistent across releases.

## Testing

- **`pytest`**, not `unittest`. Fixtures over setUp/tearDown.
- **One file per module under test:** `src/foo/bar.py` → `tests/test_bar.py`.
- **Naming:** `def test_<unit>_<condition>_<expected>():` — descriptive, no underscores-as-separators within a single phrase.
- **`pytest-xdist`** for parallelism: `uv run pytest -n auto`.
- **`pytest --cov=src --cov-report=term-missing`** for coverage. Aim ≥ 80% on new code; 100% is a tax with diminishing returns.
- **No mocking the system under test.** Mock at boundaries (network, filesystem, time). Mocking your own code means the test is testing the mock.

## Type checking

```bash
uv run pyright                    # whole project
uv run pyright src/foo/bar.py     # single file
```

Configure in `pyproject.toml`:

```toml
[tool.pyright]
strict = ["src"]
typeCheckingMode = "strict"
reportMissingTypeStubs = false
pythonVersion = "3.13"
```

If a third-party library ships no stubs and the workaround is `# type: ignore[import]`, leave a comment naming the lib and a TODO link to its issue tracker.

**Considering `ty`?** Run a one-shot trial (`uvx ty check`) on the repo before committing. If the diagnostic count is near pyright's and the codebase doesn't lean on Protocol/ParamSpec/recursive-type tricks, switching is reasonable. If `ty` reports far fewer errors than pyright, that's not a feature — it's gaps in conformance. Stay on pyright until parity lands.

## Async

- **Default to `asyncio` with `TaskGroup` / `asyncio.timeout()` (3.11+).** These are direct ports of Trio's nurseries / AnyIO's `fail_after` and they make the structured-concurrency story in stdlib finally usable. **No bare `asyncio.create_task` without holding the returned reference** — orphaned tasks are the #1 async footgun.
- **Reach for `anyio` when writing a library** that should run on either backend, or when you want `anyio.create_task_group()` semantics on a 3.10 floor. Pair with `pytest` via the bundled `anyio` plugin (don't also install `pytest-asyncio` — they conflict).
- **Trio is a pure-Trio choice** — pick it deliberately for an end-to-end Trio app. Don't mix Trio into an asyncio codebase; bridge via anyio if you must.
- **Never `time.sleep` in a coroutine.** Ruff's `ASYNC` rules catch the obvious cases; the subtle ones (sync `requests`, sync `open()` on big files) need code review. Use `asyncio.to_thread` / `anyio.to_thread.run_sync` to push blocking calls off the event loop.

## Verification ritual

Before claiming a Python change is done:

1. `uv run ruff check .` passes (or `--fix` was run and the result is reviewed).
2. `uv run ruff format --check .` passes.
3. `uv run pyright` (or `mypy`) passes — no new errors.
4. `uv run pytest` passes; affected tests added/updated.
5. If the change is to a public API: `uv lock` is committed if deps changed.

## Common traps

- **`os.environ` mutation in tests** without restore — use `monkeypatch.setenv()` from pytest. Manual mutation leaks across tests.
- **Circular imports** — usually a sign that two modules want to be one, OR that a third "interface" module should host the shared type. Forward refs (`TYPE_CHECKING`) are the duct tape, not the fix.
- **`requirements.txt` drift** — if the repo still has one, regenerate from `uv export` rather than hand-editing.
- **`__init__.py` doing real work** — should re-export public symbols only. Side effects in `__init__` make import order load-bearing.
- **Free-threaded build assumed-equivalent.** Code that runs on `python3.14` does not necessarily run correctly on `python3.14t`. Many C extensions silently re-enable the GIL on import, and pure-Python code that relied on GIL-implicit atomicity (dict mutation, `+=` on shared ints) is now racy. If you opt in, run the test suite with `-X gil=0` and stress-test concurrency.
- **`async`-flavored `pytest-asyncio` + `anyio` plugin in the same repo.** Conflicts on event-loop fixtures. Pick one — for new code, anyio.
- **Reaching for pydantic where a dataclass would do.** Pydantic's validation cost shows up at every instantiation. If the data already comes from typed code (not untrusted input), you're paying the tax for nothing.
