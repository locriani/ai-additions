  - cd "$REPO"
  - cargo init   (or `cargo init --lib` for a library crate)
    NOTE: cargo init refuses inside a non-empty repo. If it complains, move
    the scaffolded files out, run cargo init, then move them back — or use
    `cargo new <name>` in a fresh dir and rsync into here.
  - Edit Cargo.toml: name, version, edition, deps.
  - Commit Cargo.lock for binaries; libraries: your call.
  - Edit CLAUDE.md: confirm build/test commands (default: `cargo build`,
    `cargo nextest run`).
  - Optional: /init-ai-memory in the repo root.
