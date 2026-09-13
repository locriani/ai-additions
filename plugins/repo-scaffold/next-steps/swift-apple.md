  - cd "$REPO"
  - Decide project shape: SwiftPM-only (Package.swift), xcodegen (project.yml),
    or Tuist. The stack profile at ~/.claude/stacks/swift-apple.md covers each.
  - For xcodegen: write project.yml, then `xcodegen generate` to produce the
    .xcodeproj. xcodegen sets up the layout for you.
  - For SwiftPM: `swift package init --type executable` (or --type library).
  - Wire xcode-build-server for the LSP: see external/swift-lsp/.
  - Edit CLAUDE.md to fill stack-specific placeholders (build command, test
    framework, simulator vs macOS target).
  - Optional: /init-ai-memory in the repo root for per-project memory.
