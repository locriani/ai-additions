# reference-points

**Upstream:** [`locriani/reference-points`](https://github.com/locriani/reference-points) (public)
**Local checkout:** `~/Developer/reference-points`
**Status:** installed and enabled 2026-09-16 (user scope) on "reference-points, claude-statusline, atuin, security-guidance, are approved for enabling".

*Called "section rendering" early in development; `reference-points` is the
canonical name.*

A citation grammar for pointing at the exact block of a chat message — a specific
table row, a specific sentence — that either **resolves exactly or fails
loudly**. It never silently resolves to the wrong object.

An address is `N<turn>-S<section>.<Entity><n>[.location]` — tur**N** · Section ·
Entity · Location. `N27-S1.T2.3` is turn 27, section 1, table 2, row 3.

## Why

In a fast back-and-forth, "that second table" or "the sentence about caching" is
ambiguous: by the time the reply lands the referent has moved, and the two sides
resolve the phrase to different things. A mechanical address does not drift.

The skill covers both directions — resolving an address someone else wrote, and
**numbering the sections of the reply you are writing** so later addresses can
land. Addresses are never composed by hand and turns are never hand-counted;
the parser owns the answer.

```sh
S=$(reference-points-session)
reference-points turns "$S"
reference-points resolve 'N27-S1.T2.3' "$S" -T
```

## Install

```sh
claude plugin marketplace add locriani/reference-points
claude plugin install reference-points@reference-points
```

Run 2026-09-16.
