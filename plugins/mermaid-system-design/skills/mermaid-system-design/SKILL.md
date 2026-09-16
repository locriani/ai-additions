---
name: mermaid-system-design
description: Use when a system design, architecture, or data flow has to become a diagram — "draw the architecture", a design submission that must ship Mermaid source, an ARCHITECTURE.md with no picture in it — because the shape and edge vocabulary has to be fixed before the first node is written rather than discovered while drawing. Do NOT use for charts of data or for UI and screen mockups.
---

# Mermaid System-Design Diagrams

A system diagram is read before the prose and remembered after it. Everything it asserts, it
asserts through shape and edge style — so a diagram where an actor and a service are both
rectangles has told the reader those are the same kind of thing, and it did so before the
first sentence got a chance to say otherwise.

That is the failure this skill exists to prevent. It is not an aesthetic complaint. The
vocabulary is the content, and it has to be decided once, up front, and then obeyed.

## The one rule that governs everything

**Shape encodes type, edge style encodes delivery, and the legend is printed in the prose.**

```
always:  legend → nodes                          vocabulary fixed before the first node
never:   shape(a) = shape(b) ∧ type(a) ≠ type(b)   = ✗
never:   verb ∈ node_label                        = ✗   a node is a noun, an edge is a verb
```

Two kinds sharing a shape is a lie about the system. A legend the reader has to infer is the
same lie with deniability — one flat sentence naming the four shapes costs nothing and makes
the convention checkable by someone who did not write it.

## The vocabulary

| Role | Shape | Mermaid |
|---|---|---|
| External actor — human, or a system you don't run | stadium | `V(["Visitor"])` |
| Service or job — anything of yours that computes | rectangle | `RH["Redirect handler"]` |
| Data store — durable, queryable, addressable | cylinder | `DB[("Link DB")]` |
| Log, topic, queue — append-only, offset-addressed | subroutine | `LOG[["Click log"]]` |
| Decision — a branch the reader must follow | rhombus | `C{"cache hit?"}` |
| Boundary — POP, region, VPC, trust zone | subgraph | `subgraph edge ["Edge POP"]` |

"Service" is deliberately broad: a batch reconciliation sweep is a rectangle, same as an API.
The distinction the reader needs is *computes* against *stores* against *is outside your
control*, and three is as many as a legend can carry.

Six shapes is the ceiling. A seventh kind means the diagram is doing two jobs — split it.

## Edges

| Meaning | Syntax |
|---|---|
| Synchronous call, caller blocks on the result | `A --> B` |
| Async, replication, cache-miss, out-of-scope or future | `A -.-> B` |
| The mechanism, always quoted | `A -->\|"delete cache key"\| B` |

Label the arrow with what actually crosses it: `"idempotent insert"`, `"miss — read-through"`,
`"302 + Cache-Control: no-store"`. An unlabeled arrow asserts only that two things are related
somehow, which the reader already assumed from the fact that you drew them together.

Labels go on the edge, not in the box. `V["Visitor click"]` is a noun and a verb fused into
one node; it becomes `V(["Visitor"]) -->|"click"| RH`, and the diagram gets a reusable actor
out of the trade.

## One diagram per concern

```
subgraphs(d) > 2  →  split(d)
nodes(d) > ~12    →  split(d)
```

Subgraphs are the smell, not the solution. Three subgraphs in one flowchart is three diagrams
that have not been separated yet, and separating them is free: each one gets a heading, a
direction of its own, and room for edge labels that a crowded chart has no space for. Node ids
may repeat across diagrams — they only have to be unique within one.

Not every diagram is a flow. A store inventory — each store with its guarantee, retention, and
what writes to it — carries things no flow diagram can, and it is worth drawing on its own.

| Diagram kind | Direction |
|---|---|
| Request path, data flow, pipeline | `flowchart LR` — left to right reads as time |
| Store inventory, ownership, layering | `flowchart TB` |

## What the diagram is allowed to claim

**Draw only what you can defend.** Every node is a surface someone can ask about, and a node
labelled `"Fraud scoring — future"` invites "what signals?" from a reader you have handed the
question to. If it isn't designed, it belongs in a sentence, not a box.

**Numbers in labels are claims.** On a design exercise, write the quality and not a figure you
made up: `"extremely short TTL"`, not `"~60s TTL"`. Say once, in prose, that concrete values
are left for later determination. A fabricated number is the cheapest thing in the diagram to
challenge and the most expensive to defend.

**The diagram and the prose are one document.** A diagram showing a replicated cache beside
prose describing a read-through cache is a contradiction, and it is the first thing a careful
reader finds. Read them against each other before shipping, in both directions.

## Syntax traps

| Construct | What happens |
|---|---|
| `\n` inside a label | Breaks the line in 11.x, identically to `<br/>` — but only while it survives as two characters. Through HTML, JSON, or a JS string it becomes a real newline and breaks the label. Write `<br/>` |
| `A[Svc (v2)]` — unquoted parens | Parse error. **Quote every label**, always |
| `A["Svc" --> B[("DB")]` | Parse error, caret-pointed at the column that broke |
| node id `end` (also `graph`, `subgraph`) | Parse error. Reserved — rename the id |
| `<br/>` `→` `%` `,` `:` `#quot;` inside a quoted label | Fine. Quoting is what makes them safe |
| `[["log"]]` `[("store")]` `{"branch"}` `(["actor"])` | Fine, all balanced shapes |
| `A@{ shape: cyl }` — v11.3+ generic shapes | Renders, but version-gated. Verify in the target renderer before relying on it |
| `subgraph`+`direction`, `classDef`/`class`, `linkStyle`, `A --> B & C` | Fine |
| Inside an HTML page, `<br/>` in a label | Must be written `&lt;br/&gt;` or the browser eats it first |

`sequenceDiagram`, `erDiagram`, `stateDiagram-v2`, `C4Context`, `block-beta` and
`architecture-beta` all render. Reach past `flowchart` only when the thing being shown is
genuinely ordered in time (`sequenceDiagram`) or is a schema (`erDiagram`).

## Verify it renders

```
wrote(d) ⊬ renders(d)
```

```sh
python3 ${CLAUDE_PLUGIN_ROOT}/skills/mermaid-system-design/scripts/mermaid-check.py <file.md|file.mmd>
```

Every ```mermaid block in the file goes through `mmdc`, and a failure is reported with
Mermaid's own error against a line number in the file you are editing. Run it before every
handoff, not once at the end.

The checker clears syntax and nothing else. `--keep` writes the SVGs; open one. A diagram that
parses can still be an unreadable tangle, a wrong claim, or a legend nobody can follow, and
the parser will never say so.

## Red flags — the inference that fails

| Thought | Checksum | Reality |
|---|---|---|
| "It looks right — I can see the structure." | `felt(P) ↛ tested(P)` | Mermaid's parse errors are column-precise and unguessable. Reading the source is not running it. |
| "Mermaid supports that shape." | `knew(t₀) ↛ knows(t₁)` | Shape syntax is version-gated — `@{ shape: … }` landed in 11.3. Check it against the renderer that will actually draw it. |
| "It renders here, so it renders in the target." | `◇P ↛ P` | GitHub, the portal, `mmdc`, and an artifact are four renderers at three versions. Rendering somewhere is not rendering there. |
| "No parse error, so the diagram is right." | `¬obs(P) ↛ ¬P` | The parser never reads a label. A clean parse is silence about every claim the diagram makes. |
| "One more node would make it clearer." | `↑proxy ↛ ↑target` | Node count is not information. Past a dozen the reader stops tracing edges and starts skimming shapes. |
| "Every label is short, so it's readable." | `∀i small(cᵢ) ↛ small(Σcᵢ)` | Twelve short labels is a wall. Legibility is a property of the chart, not of its parts. |
| "The diagram covers the design." | `A ⊊ B` | The diagram carries components and edges. Guarantees, ordering, and failure behaviour live in prose — and have to agree with the picture. |
| "The source is written, so the diagram ships." | `planned ↛ landed` | Unrendered source is a claim about a picture nobody has seen. Render it, look at it, then ship. |
