# ai-additions

Portable Claude Code behaviour additions, shaped as a plugin marketplace.

## Rule 0 — the approval gate

**Nothing is added to this repo without Zach explicitly approving it by name.**

The approval phrase is a specific statement — *"X is approved for addition"* or
similar wording naming the item. Approval is **not** implied by discussion, by an
item appearing on a wishlist, by it being asked about or scoped, by it obviously
working, or by a prior approval of something adjacent.

Concretely, before creating any file under `plugins/` or adding any entry to
`.claude-plugin/marketplace.json`, check [`SETUP-LIST.md`](SETUP-LIST.md). If the
item is not in the **Approved** table, stop and ask for the approval phrase. Do
not build it "ready for when it's approved" — a built-but-unregistered plugin is
the thing this rule exists to prevent.

`SETUP-LIST.md` is the ledger and outranks any assumption about what was meant.
Moving a row into **Approved** requires recording the wording that granted it.

## Structure

- `.claude-plugin/marketplace.json` — the registry. One entry per approved plugin.
- `plugins/<name>/` — one directory per addition, each with its own
  `.claude-plugin/plugin.json`, plus `skills/`, `hooks/`, and/or MCP source.
- `SETUP-LIST.md` — approved / pending / declined.

## Referenced, not absorbed

An addition that already has its own repo stays there. This marketplace names it
as a required marketplace and `SETUP-LIST.md` records the coordinates. Vendoring
a copy creates a second source of truth that goes stale silently, which is the
failure mode this convention exists to avoid.

## Relationship to Standard Configs

`~/Developer/Standard Configs` bootstraps the machine and will consume this repo
via a thin `external/ai-additions/` stub. That stub is the *only* sanctioned
coupling: this repo must never depend on Standard Configs' `stdcfg/` library or
assume its directory layout. Plugins here run on a stranger's machine under
Claude Code alone.
