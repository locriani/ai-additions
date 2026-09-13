# Stack Profile: PostgreSQL / SQL

Load this profile when the project meaningfully exercises PostgreSQL — i.e. there's a `migrations/` or `db/` directory with `*.sql` files, the repo connects to a Postgres database, or the user is editing `*.sql` / writing queries against Postgres. Also load when the work is **query authoring or optimization** in a polyglot repo, regardless of the host language.

## Connection + tooling

- **`psql -X`** for scripted use — `-X` skips `~/.psqlrc`, so the script's behavior doesn't depend on the operator's local config. Always use `-X` in install scripts / CI / anything non-interactive.
- **`PAGER=cat`** for non-interactive use — otherwise long output paginates and hangs.
- **`-v ON_ERROR_STOP=1`** for scripts — abort on first error, don't keep running through a botched migration.
- **Standard one-shot invocation:** `psql -X -v ON_ERROR_STOP=1 -d <db> -f migration.sql`.
- **`\d+ <table>`**, **`\d+ <view>`**, **`\df <function>`** for schema inspection — use BEFORE guessing at column types or function signatures. Per the global rule (research, don't guess), `\d+` beats grepping a schema file.
- **`\timing on`** in interactive sessions — see how long each query takes without instrumenting.
- **Local dev DB** is owned by `machine/postgres/` in this repo (Postgres 17 brew service + per-user default DB). Postgres 18 (released 2025-09-25) is GA — upgrade target once the brew service rolls forward; pg_upgrade in 18 retains optimizer stats and supports `--swap` / parallel `--jobs`, so the post-upgrade ANALYZE stall is gone.

## Migrations

- **Every migration is reversible** unless the irreversibility is documented and intentional (e.g. dropping a deprecated table after a deprecation window). New code that adds an irreversible migration without a comment justifying it is wrong.
- **Migration files are immutable once committed.** Editing a migration that's been deployed is a footgun — it doesn't re-run on environments that already applied it. Add a NEW migration to fix.
- **Numbered or timestamped filenames**, never name-only. `20260508_120000_add_users_email_idx.sql` not `add_users_email_idx.sql`.
- **No `DROP COLUMN` without a deprecation window.** Even if the column "isn't used" — there's a long tail of deployed clients reading from it. Standard pattern: stop writing → wait → stop reading → wait → drop.
- **`DROP TABLE` requires explicit user sign-off**, period. Don't autonomously drop tables, ever.
- **Index creation:** prefer `CREATE INDEX CONCURRENTLY` for any table > 10k rows (avoids the `ShareLock` that blocks writes). Rules: (a) `CONCURRENTLY` cannot run inside a transaction, so it lives in its own migration file, only one per table at a time. (b) Partitioned tables: build the index `CONCURRENTLY` on each partition, then create the parent index non-concurrently — Postgres still doesn't support a single `CONCURRENTLY` on the partition root through pg18. (c) After failure, `CREATE INDEX CONCURRENTLY` leaves an `INVALID` index behind — drop it (`DROP INDEX CONCURRENTLY`) and retry, don't `REINDEX` it. Watch progress via `pg_stat_progress_create_index`.
- **`NOT NULL` on existing tables — the modern pattern is two phases, not three.** (1) Add column nullable, backfill in batches. (2) `ALTER TABLE ... ADD CONSTRAINT ... CHECK (col IS NOT NULL) NOT VALID` then `VALIDATE CONSTRAINT` in a separate transaction — this avoids the full-table `AccessExclusiveLock` of `SET NOT NULL` on a large table. (Postgres 12+ promotes a validated `IS NOT NULL` check to a true `NOT NULL` when you `SET NOT NULL` afterward, so the final `SET NOT NULL` is metadata-only.) `ADD COLUMN ... NOT NULL DEFAULT <constant>` is safe since pg11 (no rewrite for constant defaults) — still **not** safe for volatile defaults like `now()` or `gen_random_uuid()`, which DO rewrite the table.

## Query performance

**Mandatory rule: `EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)` before claiming a query is "fast" or "optimized".** Reading the plan is non-negotiable for any query touching > 1000 rows or running on a hot path. `BUFFERS` is the option people forget — without it you're flying blind on cache behavior. (Heads-up: in Postgres 18, `BUFFERS` becomes the default for `EXPLAIN ANALYZE`. Until everyone's on 18, type it explicitly.)

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)
SELECT ... ;
```

Use additional flags when warranted:

- **`SERIALIZE TEXT`** (pg17+) — measures time to convert tuples to wire format, including TOAST detoasting. Without it, `EXPLAIN ANALYZE` discards the result and hides serialization cost. Turn it on whenever a query returns wide rows, JSONB, or large `text` columns and the runtime feels slower than the plan suggests.
- **`MEMORY`** (pg17+) — reports planner memory usage; useful when partition pruning or large `IN (...)` lists are suspected of bloating planning time.
- **`FORMAT JSON`** — feed the plan into pgMustard / explain.dalibo / pev2 / pganalyze. JSON output is the right input for tooling; `FORMAT TEXT` is for humans reading at the terminal.

What to look for:

- **Seq Scan on a table > 10k rows** that should be selective → missing index.
- **Rows estimate vs. actual mismatch by >10×** → stale stats (`ANALYZE <table>`) or correlated columns the planner doesn't know about (`CREATE STATISTICS ... ON ... FROM ...`).
- **`Buffers: shared read=N`** indicates pages NOT in cache — high `read` vs. `hit` is a cold cache, not necessarily a query bug. Run twice and compare.
- **Sort Method: external merge** → `work_mem` too low for the query, or the sort can be eliminated via index.
- **Hash Join "Batches: > 1"** → spilled to disk, same `work_mem` issue.
- **JIT lines on a sub-100ms query** → JIT is doing more harm than good. Either lift the `jit_above_cost` threshold or set `jit = off` for the session.

For frequently-run analytical queries, capture the `EXPLAIN (ANALYZE, BUFFERS)` output in a comment in the migration or a doc — it's the only record of "this is what the plan looked like when I tuned it."

**Cluster-level observability.** `pg_stat_statements` is the first stop for "what's slow" — install the extension on every environment (it's nearly free). `pg_stat_io` (added pg16) breaks I/O down by backend type and context (normal/vacuum/bulkread/bulkwrite); pair it with `pg_stat_statements` to tell "this query is slow" from "the whole instance is bottlenecked on writes." Postgres 17 also added `pg_wait_events` — join against `pg_stat_activity` to see *why* a session is blocked, not just *that* it is.

## Schema design

- **`uuid` for public-facing primary keys**, `bigint` (auto-incrementing identity) for internal-only PKs. On pg18, prefer `uuidv7()` over `gen_random_uuid()` (v4) for any UUID that's also a PK or sort key — v7 is timestamp-prefixed, so insert order matches index order and B-tree fragmentation drops. On pg17 and older, fall back to `gen_random_uuid()` from `pgcrypto` or a v7 implementation in app code.
- **Identity columns over `serial`/`bigserial`.** `serial`/`bigserial` are legacy. Both `GENERATED ALWAYS AS IDENTITY` and `GENERATED BY DEFAULT AS IDENTITY` are correct choices — the Postgres docs treat them as neutral and the community is genuinely split. **Default opinion: prefer `ALWAYS`** — it enforces "the database owns the value" and prevents the classic "manually inserted id 100, sequence still at 50, next insert collides" footgun; `OVERRIDING SYSTEM VALUE` is the escape hatch when you need to override. **Pick `BY DEFAULT` instead** when the project does any of: `pg_dump`/restore round-trips that include identity values (the dump uses `OVERRIDING SYSTEM VALUE` with `ALWAYS` but it's friction), logical replication targets that receive identity values from upstream, ORM patterns that set the PK app-side, or seed-data files with hardcoded IDs. Pick one per project and document it; don't mix.
- **`timestamptz`, never `timestamp`.** A naked `timestamp` discards the timezone and creates pain that surfaces months later. There is no scenario where `timestamp` is the right choice over `timestamptz`.
- **`text` over `varchar(N)`** unless there's a hard business constraint on length. They have the same on-disk representation; `varchar(N)` just adds a check constraint.
- **`numeric(precision, scale)` for money**, never `float`/`double`. `bigint` cents is also acceptable.
- **`jsonb` over `json`** — binary form, indexable, faster. Modern access patterns: `jsonb_path_query` / `jsonb_path_exists` for jsonpath, and **`JSON_TABLE`** (pg17) to project JSONB into a relational shape inside the `FROM` clause — finally a clean way to flatten an array-of-objects column without a wall of `jsonb_array_elements + ->>`. Use the `jsonb_path_ops` GIN opclass when you only need containment (`@>`) — index is ~⅓ smaller and faster than the default `jsonb_ops`.
- **Enums:** prefer Postgres `ENUM` types over check constraints for a fixed small set; use a lookup table for anything that might grow.
- **Foreign keys ON every relationship.** With explicit `ON DELETE` semantics — `RESTRICT` (default), `CASCADE`, or `SET NULL`. No FK is a bug masquerading as flexibility.

## Query authoring

- **CTEs (`WITH ... AS`) for clarity** — prefer over deeply nested subqueries. Postgres 12+ no longer materializes single-use CTEs by default (they inline like subqueries) unless you write `MATERIALIZED`, so the readability win comes free. Reach for explicit `MATERIALIZED` only when the CTE is referenced multiple times *and* the planner is making a bad choice — verify with `EXPLAIN`, don't guess.
- **`MERGE` (pg15+, with `RETURNING` in pg17)** for upserts that need branching `WHEN MATCHED` / `WHEN NOT MATCHED` logic. For plain "insert or update", `INSERT ... ON CONFLICT (...) DO UPDATE` is still simpler and faster — pick `MERGE` when the conditional logic actually justifies it.
- **Window functions over self-joins** for ranking/running-totals/lag-lead patterns. `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` is almost always faster and clearer than a correlated subquery.
- **`SELECT *` is banned** in committed code. List columns explicitly. `SELECT *` in a view will silently break when the underlying table changes.
- **Always use parameterized queries** in application code — never string-concat user input into SQL. SQL injection is a 2026-still-real vulnerability.
- **`EXISTS` over `IN` for subqueries** when the subquery returns many rows — the planner's choices are usually similar but `EXISTS` short-circuits cleanly.

## Indexing

- **B-tree is the default** and right for ~95% of cases.
- **Partial indexes** when a query filters by a low-cardinality predicate: `CREATE INDEX ... ON tbl (col) WHERE active`.
- **Covering indexes** (`INCLUDE (...)`) for queries that hit only the index — avoids the heap fetch.
- **GIN for `jsonb` / arrays / full-text search.**
- **GiST for geometric / range types.**
- **Don't index small tables** (< 1000 rows) — sequential scan is faster than index lookup.
- **Composite index column order matters.** Query patterns that filter on `(a, b)` AND query patterns that filter on `(a)` can share `(a, b)`. Patterns that filter only on `(b)` cannot use it.

## Transactions + locking

- **`BEGIN; ... COMMIT;`** explicitly for multi-statement work. Don't rely on implicit autocommit boundaries.
- **`SELECT FOR UPDATE`** when you'll write based on what you read — locks the rows. Without it, two concurrent transactions can read the same row and both decide to update.
- **Advisory locks** (`pg_advisory_lock`) for application-level mutual exclusion — cheaper than a row lock when you just need "only one job runner at a time."
- **Migrations should run in a transaction** unless they can't (e.g. `CREATE INDEX CONCURRENTLY`, `VACUUM`, `ALTER TYPE ... ADD VALUE` pre-12). One file per non-transactional operation.

## Verification ritual

Before claiming a query / migration / schema change is done:

1. **Migration tested against a fresh DB** — `dropdb && createdb && run all migrations`. A migration that works on your local dev DB but fails on a fresh one is broken.
2. **Migration is reversible** OR explicitly documented as one-way.
3. **`EXPLAIN (ANALYZE, BUFFERS)`** for any query that's on a hot path or scans > 1000 rows. Read the plan, not just the runtime.
4. **App-level tests pass** against a real Postgres (not a SQLite stub or mock) — see the global rule about not mocking the database.
5. **Schema changes don't break existing apps** — new columns nullable or with defaults; no `DROP COLUMN` without deprecation.

## Common traps

- **`NULL` semantics.** `NULL = NULL` is `NULL`, not `TRUE`. Use `IS NULL` / `IS DISTINCT FROM`. Aggregates ignore `NULL` (except `COUNT(*)`). Indexes don't index `NULL` by default unless you say so.
- **Implicit casts in comparisons.** `WHERE int_col = '123'` works (Postgres casts), but `WHERE varchar_col = 123` may or may not. Be explicit.
- **`pg_dump` without `--no-owner --no-acl`** when restoring across environments — the dump embeds the source's role names and permission grants, which won't exist on the target.
- **`vacuumdb` / `ANALYZE` discipline** — autovacuum handles most cases, but bulk inserts/updates need a manual `ANALYZE` to refresh stats before queries hit the new data with stale plans.
- **Connection pooling** — every long-lived connection consumes Postgres resources. PgBouncer (transaction-pooling mode) is still the default and the right answer for ~95% of stacks: battle-tested, lightweight, in front of every managed Postgres. Reach for **PgCat** only when you actually need the things PgBouncer doesn't do — multi-core scale-out beyond ~750 concurrent clients, native read-replica load balancing, sharding, or zero-downtime config reload. **Transaction-pooling caveat:** session-scoped state (prepared statements pre-pg17, `SET LOCAL` outside the txn, advisory locks, `LISTEN/NOTIFY`, temp tables, cursors `WITH HOLD`) does not survive across statements. Postgres 17 + PgBouncer 1.21+ added protocol-level prepared statement support in transaction mode — until both sides are on those versions, disable client-side statement caching or you'll get cryptic "prepared statement does not exist" errors under load.
- **Logical replication on pg17:** failover slots finally exist (`failover = true` on the subscription + `sync_replication_slots = on` on the standby) — before pg17, a primary failover meant the logical subscriber re-syncing from scratch. Also: `pg_createsubscriber` converts a physical standby into a logical subscriber in place, which is the cheapest path to a near-zero-downtime major-version upgrade or to splitting a database.
