  - cd "$REPO"
  - rails new . --database=postgresql --skip-bundle   (forces creation
    inside the existing dir; --skip-bundle so you control gem install timing)
  - bundle install
  - bin/rails db:create db:migrate
  - Edit CLAUDE.md: confirm test framework (Minitest by default, RSpec if you
    swapped). Per stack profile: thin controllers / fat models / services.
  - Optional: /init-ai-memory in the repo root.
