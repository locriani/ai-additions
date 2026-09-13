# Stack Profile: Ruby on Rails

Load this profile when the project is Rails — i.e. there's a `Gemfile` with `gem "rails"`, a `config/application.rb`, or `bin/rails` at the repo root.

## Toolchain

- **Ruby version managed by `mise`, `rbenv`, or `chruby`** — pinned via `.ruby-version`. Don't use system Ruby.
- **Bundler** for gem management — `bundle install` / `bundle update`. Never `gem install` directly into a project.
- **`bin/rails`** for invoking Rails — uses the project-local Gemfile resolution. Plain `rails` may pick up the wrong version.
- **`bin/dev`** (Rails 7+) for the dev server — runs `Procfile.dev` (Puma + JS bundler + CSS bundler in parallel).
- **`rubocop`** for linting + autoformat. `rubocop-rails`, `rubocop-rspec`, `rubocop-performance` plugins as appropriate.

## Project shape

- **Rails 8.x** is the assumed default for new code (released Nov 2024). Rails 7.2 is the floor for active maintenance; anything older is upgrade territory, not greenfield. Rails 8 ships **Solid Queue** (jobs), **Solid Cache** (cache), and **Solid Cable** (Action Cable) as defaults — **Redis is no longer required out of the box**. Hotwire is the assumed frontend.
- **Ruby 3.3+ required**, **Ruby 3.4 strongly recommended**. Rails 8 enables **YJIT by default** on Ruby 3.3+ in production — don't disable it without a measured reason. Ruby 3.4 turns YJIT on by default at the language level too.
- **`Gemfile.lock`** committed.
- **`.ruby-version`** + `Gemfile`'s `ruby "..."` directive in sync.
- **`config/credentials.yml.enc`** + `config/master.key` — secrets via Rails encrypted credentials, NOT plaintext `config/secrets.yml`. `master.key` gitignored, distributed out of band.
- **`storage/`, `tmp/`, `log/`, `node_modules/`** in `.gitignore`.

## Hotwire-first frontend

- **Turbo + Stimulus over a SPA framework** unless there's a specific reason. Server-rendered HTML, Turbo Drive for navigation, Turbo Frames for partial updates, Turbo Streams for live updates, Stimulus for sprinkles of JS.
- **`turbo-rails`** + **`stimulus-rails`** are standard. **Turbo 8** brought **page morphing** (`turbo_refreshes_with method: :morph`) — prefer it over full-page replacement for live-updating views; it preserves scroll/focus/CSS-state and pairs cleanly with Turbo Streams broadcasts.
- **No React/Vue/Svelte by default.** They're not banned, but they fight the Rails grain. If you reach for one, justify it explicitly.
- **`importmap-rails`** for the JS pipeline on most apps — Rails 8 default, no Node, no build step. **`jsbundling-rails`** (esbuild/rollup) only when you actually need a bundler (TypeScript, JSX, npm packages that require transpilation). **`cssbundling-rails`** + Tailwind/PostCSS for CSS.
- **Propshaft is the asset pipeline** in Rails 8 — Sprockets is legacy. Propshaft fingerprints + serves; it does NOT transpile, bundle, or compress. Don't add Sprockets back unless you're maintaining a pre-existing app that depends on it.

## Common commands

```bash
bin/setup                      # one-shot dev setup (gems, db, seed)
bin/dev                        # dev server (Procfile.dev)
bin/rails server               # plain server (no JS/CSS watcher)
bin/rails console              # REPL
bin/rails db:migrate           # apply migrations
bin/rails db:rollback          # roll back the most recent migration
bin/rails db:seed              # run db/seeds.rb
bin/rails test                 # run all tests (Minitest, the default)
bin/rails test test/models/foo_test.rb     # single file
bin/rails test test/models/foo_test.rb:42  # single test by line
bin/rails routes               # all routes
bin/rails routes -g users      # filtered routes
bin/rails generate migration AddEmailToUsers email:string
bin/bundle exec rubocop --autocorrect-all
bin/brakeman                   # security scan (Rails 8 ships it in new apps)
bundle exec bundler-audit check --update   # CVE scan against Gemfile.lock
bin/kamal deploy               # deploy via Kamal 2 (Rails 8 default deploy tool)
```

## Code conventions

- **Convention over configuration.** Rails has opinions; follow them. Custom dir structure / non-standard naming costs you everything Rails does for free.
- **Controllers are thin.** Find the resource, authorize, hand off to a model method or service object. Controllers that do business logic become unmaintainable.
- **Fat models** are the Rails default — but past ~300 lines, extract concerns or service objects (`app/services/`).
- **`ActiveRecord::Base` subclasses for DB models, plain `ActiveModel` for form objects** that don't persist. Don't make a fake AR model for a form.
- **`Strong Parameters`** on every controller action that accepts user input. `params.require(:user).permit(:name, :email)`. Mass-assignment without strong params is a vulnerability.
- **`scope :name, -> { where(...) }`** for reusable queries. Beats class methods returning relations because chaining is the same.
- **`enum` for fixed-value columns** — `enum status: { draft: 0, published: 1 }`. Generates predicate methods (`record.draft?`).
- **Background jobs:** `ActiveJob` + **Solid Queue** for new Rails 8 projects — DB-backed, no Redis, transactional with your data, sufficient for ~95% of workloads (37signals runs HEY on it at 20M+ jobs/day). Reach for **Sidekiq** only when you've measured a need its Redis-backed throughput addresses, or you depend on its batches/unique-jobs/Pro features. **GoodJob** is a fine alternative if you're Postgres-only and want a more mature DB-backed option than Solid Queue. Anything > ~200ms moves out of the request cycle.
- **Authentication:** for new apps, start with the **Rails 8 built-in authentication generator** (`bin/rails generate authentication`) — DB-backed sessions, password reset, no gem dependency. It's a *starting point*, not a Devise replacement. Reach for **Devise** when you need OAuth, MFA/2FA, confirmable, lockable, or a mature ecosystem of plugins. **Sorcery** is a lighter middle ground but its momentum has faded — prefer built-in or Devise.
- **`I18n.t` everywhere** for user-facing strings, even if you're "only ever supporting English." It's free insurance.

## Testing

- **Minitest is the Rails default** and the recommended choice for new projects — fast, no extra gems, ships with Rails. **RSpec** is still widespread and totally fine if the team prefers its DSL or the project already uses it. Pick one per project; don't mix.
- **`bin/rails test`** for Minitest, `bundle exec rspec` for RSpec.
- **System tests** (`test/system/` or `spec/system/`) for end-to-end browser tests via Capybara. Use these for critical user flows.
- **Fixtures** (`test/fixtures/*.yml`) for Minitest's default — fast, but rigid. **`factory_bot`** is OK if the project's already on it; don't introduce both.
- **Database cleaning:** transactional fixtures (Minitest default). For System tests: DatabaseCleaner with truncation strategy if you hit "leftover data" issues.
- **Don't mock the database.** ActiveRecord-mocked tests miss SQL bugs that surface in prod.
- **`assert_changes` / `assert_difference`** for state changes — clearer than capturing a value before and asserting after.

## Database + migrations

- **`bin/rails generate migration`** for every schema change — never hand-edit `db/schema.rb`. The schema is generated from migrations.
- **Reversible migrations**: `change` block when possible; `up` + `down` when not. `change` infers the inverse for most operations.
- **`add_index` with `algorithm: :concurrently`** on Postgres for tables > 10k rows. Matches the rule from `postgres-sql.md`.
- **`add_reference :things, :user, foreign_key: true, null: false`** — FK + NOT NULL by default for new associations.
- **No `t.string :status, default: "active"` without a check constraint OR an enum.** Free-text status columns rot.
- **`bin/rails db:migrate` → commit `db/schema.rb`** as part of the same commit. Never commit a migration without the resulting schema diff.
- **Strong Migrations gem** (`gem "strong_migrations"`) catches dangerous patterns (adding a NOT NULL column without a default on a populated table, removing columns without `ignored_columns`, backfilling in the same migration as a schema change, etc.). Add it to every production app — non-negotiable on Postgres.

## Caching + performance

- **`Rails.cache`** with **Solid Cache** by default in Rails 8 (DB-backed, durable, no Redis). Reach for Redis/Memcached only if you've measured a need Solid Cache can't meet. `cache do ... end` view helpers for fragment caching — pairs especially well with Turbo 8 morphing.
- **Counter caches** (`belongs_to :post, counter_cache: true`) over `post.comments.count` in views.
- **Eager loading**: `Post.includes(:author).all` to avoid N+1. The `bullet` gem catches N+1 in dev — install it.
- **`find_each` for batched iteration** of large recordsets — avoids loading 100k records into memory.
- **`pluck` over `map(&:attr)`** when you only need one column — `pluck` runs in SQL; `map` instantiates AR objects.

## Verification ritual

Before claiming a Rails change is done:

1. `bin/rails test` (or `bundle exec rspec`) passes; affected tests added/updated.
2. `bundle exec rubocop` clean (or `--autocorrect-all` was run and reviewed).
3. `bin/rails db:migrate` was run, `db/schema.rb` updated and committed.
4. `bin/dev` actually loads the affected pages without errors. Screenshot a UI change.
5. `bin/rails routes -g <new-resource>` shows the routes you expect.
6. `bin/brakeman` clean — security regressions caught. New Rails 8 apps include it by default.
7. `bundle exec bundler-audit check --update` clean — no known CVEs in `Gemfile.lock`. Wire it into CI.

## Common traps

- **N+1 queries.** The classic Rails footgun. Install `bullet` in dev; check the log for repeated identical queries.
- **`includes` vs `joins` vs `preload`** — `includes` is the smart default; `joins` for INNER JOIN with a WHERE; `preload` forces a separate query (no JOIN).
- **`belongs_to` is required by default** since Rails 5. `optional: true` to allow nil — don't disable globally.
- **`accepts_nested_attributes_for`** is a power tool that often becomes a maintenance nightmare. Form objects scale better.
- **Asset pipeline confusion (Sprockets vs. Propshaft vs. importmap vs. jsbundling).** Rails 8 new apps default to Propshaft + importmap-rails. Don't mix Sprockets and Propshaft. Propshaft does NOT compile/transpile — if you need that, you need jsbundling-rails or cssbundling-rails on top.
- **Solid Queue / Solid Cache / Solid Cable need their own DBs (or schemas).** Rails 8 generates separate `queue.sqlite3`/`cache.sqlite3`/`cable.sqlite3` (SQLite default) or expects `queue`, `cache`, `cable` databases under multi-DB config for Postgres/MySQL. Don't dump them into the primary DB without thinking — the queue tables churn hard and will bloat your primary's WAL/binlog.
- **Kamal 2 deploys assume an OCI-compliant container registry + Docker on the target host.** It's not Capistrano — there's no `bundle exec` over SSH. Build → push → pull → swap. The `Dockerfile` Rails 8 generates includes **Thruster** (HTTP/2 + asset caching/compression proxy in front of Puma) — keep it; don't strip it for "simplicity."
- **Don't write to `Time.zone.now` then read with `Time.now`.** Mixed time-zone handling is one of the most expensive Rails bugs to debug because tests pass in UTC and prod fails in user-local. Use `Time.current` / `Date.current` everywhere.
- **Time zone bugs.** `Time.now` is system tz; `Time.zone.now` is Rails-configured. Always use `Time.zone.now` (or the `Time.current` shorthand) for user-facing times. Same for `Date.today` → `Date.current`.
- **`request.host` / `request.url` in mailers** — mailers don't have a request. Use `default_url_options` configured in `config/environments/*.rb`.
