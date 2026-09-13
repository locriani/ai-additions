  - cd "$REPO"
  - uv init  (or `uv venv .venv && source .venv/bin/activate` if you've already
    written pyproject.toml by hand)
  - uv add --dev pytest ruff pyright
  - Edit pyproject.toml: project name, version, deps. Commit pyproject.toml
    AND uv.lock once they exist.
  - Edit CLAUDE.md: fill the Build & Test placeholders with your actual
    commands (e.g. `uv run pytest`, `uv run ruff check`).
  - Optional: /init-ai-memory in the repo root.
