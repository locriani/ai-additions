# mermaid-system-design

A Claude Code skill for drawing system architectures in Mermaid, plus a checker that renders
every diagram in a file before you ship it.

## Why

A system diagram asserts things through shape and edge style, and it asserts them before the
prose gets a chance to. If an external actor and a service you run are both rectangles, the
diagram has already told the reader those are the same kind of thing.

The skill fixes a vocabulary — actor, service, store, log, decision, boundary — and a set of
edge conventions, so the choice is made once instead of drifting per diagram. The rest is the
syntax traps that actually cost time — unquoted parens, `end` as a node id, an unbalanced shape
bracket — and the rule that an unrendered diagram is not a diagram.

## Install

```sh
brew install node
npm install -g @mermaid-js/mermaid-cli

claude plugin marketplace add locriani/ai-additions
claude plugin install mermaid-system-design@ai-additions
```

The first `mmdc` run downloads Puppeteer's Chromium — allow a minute for it. Plugin skills only
surface in **new** Claude Code sessions, so quit and reopen after installing.

Check it took:

```sh
mmdc --version
claude plugin list        # mermaid-system-design@ai-additions, enabled
```

## Checking diagrams

```sh
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/mermaid-system-design/scripts/mermaid-check.py design.md
```

Every ` ```mermaid ` block in a Markdown file goes through `mmdc`. Other fences — ` ```text `,
` ```python ` — are left alone, so a document that also ships its raw source as text does not
get checked twice. A `.mmd` file is treated as one diagram.

```
ok    design.md:14  (diagram 1 of 4)
FAIL  design.md:27  (diagram 2 of 4)
      Error: Parse error on line 29:
      ...flowchart LR  A[Svc (v2)] --> B
      -------------------^
      Expecting 'SQE', 'TEXT', got 'PS'

1 of 4 diagram(s) failed to render
```

Line numbers are rewritten from Mermaid's block-relative count to lines in the file you are
editing, so the caret points somewhere you can actually jump to.

`--keep` writes the rendered SVGs and prints the directory; `--outdir DIR` puts them somewhere
you choose. Use one of them — the checker clears syntax and nothing else, and a diagram that
parses can still be an unreadable tangle.

Exit codes: `0` everything rendered, `1` something failed, `2` `mmdc` is missing or a file
does not exist. A missing `mmdc` is a hard stop, never a silent pass.

## Layout

```
.claude-plugin/plugin.json                              marketplace metadata
skills/mermaid-system-design/SKILL.md                   the rules Claude loads
skills/mermaid-system-design/scripts/mermaid-check.py   the checker
skills/mermaid-system-design/scripts/test_mermaid_check.py   its tests — block extraction
                                                        and line arithmetic, no network
```

```sh
python3 skills/mermaid-system-design/scripts/test_mermaid_check.py
```

`${CLAUDE_PLUGIN_ROOT}` resolves to this plugin's installed copy, which is version-stamped under
`~/.claude/plugins/cache/`. Editing this repo does not change what a running session loads — run
`claude plugin marketplace update ai-additions` and reinstall to pick changes up.

## Scope

Diagrams only: vocabulary, edge semantics, how to split them, syntax, and verification. It has
nothing to say about the document around the diagram — write-up structure, trade-off tables,
appendices, or export.
