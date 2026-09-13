# Stack Profile: Infrastructure as Code (Terraform / OpenTofu)

Load this profile when the project is IaC — i.e. there are `*.tf` files at the repo root or under `infra/`, `terraform/`, `iac/`, etc., or the user is managing cloud resources declaratively. **Applies to OpenTofu (`tofu`) the same as Terraform (`terraform`)** — the syntax is compatible; substitute the binary name in the commands below as appropriate.

## Toolchain

- **`terraform`** (HashiCorp, BSL-licensed since 1.6) or **`tofu`** (OpenTofu, MPL-2.0 fork under the Linux Foundation). Pick one per project; the choice is consequential and reversible only with effort. **Evaluate per-project** — there's no one-size-fits-all default in mid-2026. **Pick OpenTofu** when you want native client-side state encryption (1.7+), early evaluation of variables/locals in backend config (1.8+), provider-defined functions, a faster release cadence, or you specifically want to avoid the BSL. **Pick Terraform** when you (or your org) use HCP Terraform / Terraform Cloud, depend on the official MCP server, have an existing HashiCorp contract, or need Sentinel policy. The HCL syntax remains compatible, so substitute `terraform` ↔ `tofu` in the commands below as appropriate. If the repo is greenfield with no enterprise gravity either way, OpenTofu is a defensible lean for the encryption/early-eval features alone.
- **`tflint`** — linter. Catches AWS/Azure/GCP-specific anti-patterns the core tool doesn't.
- **`trivy config`** — security scanner. **`tfsec` is deprecated and archived** (Aqua Security folded the entire check library into Trivy in 2024; check IDs like `AVD-AWS-0086` are unchanged). Migrate `tfsec .` → `trivy config .`. Don't bring `tfsec` into a new project. **`checkov`** (Bridgecrew/Prisma) is the credible alternative — broader policy coverage, slower, more opinionated; pick one, not both.
- **`terraform-docs`** — generates README sections from variable / output blocks. Auto-runs in CI to keep docs honest.
- **`pre-commit-terraform`** wraps the above into a pre-commit framework.
- **`tfenv`** / **`tofuenv`** — version manager. `.terraform-version` / `.opentofu-version` pin the binary. Pin the **exact** version, not a floor — `1.10.5`, not `>=1.10`.

## Project shape

- **`*.tf`** files for resources/data/variables/outputs. Conventional split:
  - `main.tf` — primary resources.
  - `variables.tf` — input variable declarations.
  - `outputs.tf` — outputs.
  - `versions.tf` — required_providers + required_version.
  - `data.tf` — `data` blocks if numerous.
  - `locals.tf` — locals if numerous.
- **`terraform.tfvars`** for default values, **`*.auto.tfvars`** for env-specific defaults loaded automatically. **NEVER commit secrets** in `.tfvars` — use a secret manager (AWS Secrets Manager, Vault, Doppler) and reference via data sources.
- **`.terraform.lock.hcl`** committed — pins provider versions **and per-platform cryptographic checksums (h1 hashes)**. Without it, two contributors resolve to different provider versions or pull tampered binaries. When working across OS/arch boundaries (Linux CI + macOS dev), run `terraform providers lock -platform=linux_amd64 -platform=darwin_arm64 ...` so the lockfile carries hashes for every platform that touches the code; otherwise the first CI run rewrites the lockfile and the diff churns forever.
- **State backend configured** (`backend "s3"`, `backend "gcs"`, Terraform Cloud / HCP Terraform, etc.) — never local state for shared infra. Local state on one engineer's laptop = bus factor of one + zero locking.

## State management

- **Remote state with locking.** On AWS, **S3 native state locking is now the default** — set `use_lockfile = true` on the S3 backend and drop DynamoDB. Native locking went GA in Terraform 1.11 (and is supported in OpenTofu) on top of S3 conditional writes; the `dynamodb_table` argument is deprecated and will be removed. Only keep DynamoDB locking on legacy state files until they migrate. GCS has native locking. Azure Blob has native locking via lease. Without locking, concurrent applies corrupt state.
- **One state file per environment** (dev / staging / prod) — separated **by directory**, not by workspace. CLI workspaces share a backend and are too easy to `terraform workspace select prod` into by accident; directory separation forces a `cd` and a different backend config. Workspaces are fine for ephemeral feature stacks within a single environment.
- **State is sensitive.** It contains plaintext secret values for many resources (RDS passwords, generated tokens, TLS keys). Encrypt at rest, restrict access. Prefer **OpenTofu's native state encryption** if you're on OpenTofu — it encrypts before the state leaves the process, so backend-side encryption is no longer the only line of defense. Never `terraform show` into a chat log or PR.
- **Use `import` and `removed` blocks, not the imperative CLI.** Terraform 1.5+ introduced declarative `import` blocks (plannable, reviewable, version-controlled) and `removed` blocks (drop a resource from state without destroying it via `removed { ... lifecycle { destroy = false } }`). Both belong in a PR like any other change. Reach for `terraform state rm` / `mv` / `terraform import` (CLI) only for surgical recovery after backing up state.
- **Use `check` blocks for post-apply assertions.** Terraform 1.5+ `check` blocks let you express "this endpoint must respond 200 after apply" or "this cert is valid for >30 days" without failing the apply — they surface as warnings and are the right place for drift / health invariants that aren't `validation` rules on inputs.

## Workflow discipline

**`plan` before every `apply`. Read the plan. Don't approve a plan you don't understand.**

```bash
terraform fmt -recursive          # format
terraform validate                # syntax + internal consistency
terraform init                    # download providers, configure backend
terraform plan -out=tfplan        # generate a plan, save it
terraform show tfplan             # inspect the plan
terraform apply tfplan            # apply EXACTLY the saved plan
```

- **`-out=tfplan` then `apply tfplan`** is the safe sequence. `apply` without a saved plan re-plans, which can pick up new drift between plan and apply.
- **Never `terraform apply -auto-approve`** outside CI/CD pipelines that have their own gates. Manually-run apply needs the diff confirmation.
- **Never manually edit infra in the cloud console** for resources Terraform manages. Drift is the enemy. If you NEED a one-off manual change, document it AND import it back into TF in the same change window.

## Resource conventions

- **Modules for repeated patterns.** A module that's used once is just abstraction tax. Three uses → extract.
- **Module versioning** — pin module versions in source URLs. For registry modules: exact `version = "1.2.3"` (not `~> 1.2`). For Git modules: pin to a tag (`?ref=v1.2.3`) for human-readable releases, OR pin to a **commit SHA** (`?ref=a1b2c3d...`) when the module is third-party and you need supply-chain immutability — tags are mutable on the server side, SHAs are not. **Never** `?ref=main`. Track third-party module updates the same way you track dependency CVEs.
- **`for_each` over `count` when iterating.** `count`-indexed resources rebuild ALL of them when an item is removed from the middle of the list (because indexes shift). `for_each` keys by string and only changes what changed.
- **`lifecycle { prevent_destroy = true }`** on stateful resources (databases, snapshots, KMS keys). The cost is a manual override on intentional destroys; the benefit is one accidental `terraform destroy` doesn't nuke prod data.
- **`lifecycle { ignore_changes = [...] }`** sparingly — only for fields legitimately managed outside TF (e.g. autoscaling group desired_capacity managed by an autoscaler).
- **Tagging strategy.** Every resource that supports tags gets `Project`, `Environment`, `ManagedBy = "terraform"`, `Owner`. Standardize via a `default_tags` provider block (AWS) or a `locals.common_tags` map merged in.

## Variables + outputs

- **Type every variable.** `variable "name" { type = string }`. Untyped variables accept anything and produce confusing errors downstream.
- **`description` on every variable + output.** It's what `terraform-docs` extracts; without it the README is empty.
- **`validation` blocks** for variables with constraints — `length(var.name) > 3`, regex matches, allowed enum values. Catches misuse at plan time.
- **Sensitive outputs marked `sensitive = true`** — keeps them out of `terraform output` plain text and the plan diff.
- **No outputs of secrets to the state's "outputs" section** unless absolutely needed for cross-stack consumption — and even then, prefer pulling from the secret manager directly.

## Security

- **`trivy config` (or `checkov`) in CI.** Don't merge with HIGH or CRITICAL findings. Documented exceptions go in a `.trivyignore` (or `trivy.yaml`) — not a `.tfsec.yml`, which is dead config for a dead tool.
- **No `*` in IAM policies** unless the resource genuinely requires it (and even then, justify in a comment). Wildcards are how prod keys get exfiltrated.
- **Encryption at rest:** opt in everywhere it's available. S3 default encryption. RDS `storage_encrypted = true`. EBS volumes encrypted. KMS keys with rotation enabled.
- **Encryption in transit:** TLS-only on load balancers (no HTTP listener without a redirect). Database connections require SSL.
- **Public buckets / open security groups:** `tfsec` catches these. Treat any finding as a real bug.
- **Provider credentials** never in `.tf` or `.tfvars`. Use the cloud's auth chain (AWS IAM Role / IRSA, GCP service account, Azure Managed Identity, env vars in CI).

## Verification ritual

Before claiming an IaC change is done:

1. `terraform fmt -recursive -check` clean.
2. `terraform validate` clean.
3. `tflint` clean.
4. `trivy config .` (or `checkov`) — no new HIGH/CRITICAL.
5. `terraform plan` reviewed — every line of the diff is intentional. No surprise resource recreations, no surprise destroys.
6. For shared/prod state: a second engineer reviewed the plan output before apply.
7. After apply: `terraform plan` again should show "No changes." Drift between expected and actual = something else mutated state.

## Module-level discipline

If you're authoring a reusable module:

- **`README.md`** generated by `terraform-docs` — auto-injects variables/outputs tables. Keep examples minimal and runnable.
- **`examples/`** subdirectory with at least one fully-runnable consumer. CI applies the example against a scratch project to catch regressions.
- **Pin `required_providers` versions** with `>=` floors and `<` ceilings (`>= 5.0, < 6.0`). Don't leave it open-ended — major-version bumps break consumers.
- **Semver the module.** Tag releases. Document breaking changes in the module CHANGELOG.

## Orchestration & automation

- **For a single repo with one or two environments, plain `terraform`/`tofu` + a thin Makefile or CI workflow is enough.** Reach for orchestration only when the wrapper earns its keep.
- **Terragrunt** is still relevant in 2026 but no longer the obvious default. It earns its place at scale (many environments × many accounts × DRY backend config). Below that threshold it adds a layer of indirection junior engineers stumble on. Newer alternatives — **Terramate**, **Terraspace** — target the same DRY-multi-stack problem with different ergonomics; evaluate before assuming Terragrunt.
- **CI/CD platforms.** **Atlantis** (self-hosted, PR-driven plan/apply comments) for teams that want OSS + control. **Spacelift** / **env0** for managed orchestration with policy-as-code, drift detection, and stack dependencies. **HCP Terraform / Terraform Cloud** is the HashiCorp-native option — required if you want the official MCP integration, but locks you to Terraform-the-binary (no OpenTofu). All four beat hand-rolled GitHub Actions once you have >2 engineers applying.
- **Provider auth in CI** uses OIDC federation (GitHub Actions → AWS IAM via `aws-actions/configure-aws-credentials`, equivalent for GCP/Azure). Long-lived access keys in CI secrets are a 2018 pattern; don't ship new ones.

## AWS provider 5.x → 6.x

- AWS provider **6.0 went GA mid-2025**. The headline change is **multi-region support per provider block** — a single provider can now manage resources across regions via the `region` argument on individual resources, eliminating the alias-explosion pattern.
- **Removed entirely:** all 16 `aws_opsworks_*` resources (OpsWorks itself was EOL). If you still have these, migrate before bumping.
- **`@<regionID>` import suffix** for cross-region imports.
- v5 receives only critical security fixes after the v6 GA window. Plan the bump deliberately: pin to v5 floor + v6 ceiling (`>= 5.80, < 7.0`) once you've migrated, and use the official v6 upgrade guide — there are individual resource-level breaking changes beyond the headline ones.

## Common traps

- **`terraform destroy` typed in the wrong terminal.** This is how clusters die. Always check `terraform workspace show` and `pwd` before any destructive command. Some teams disable `destroy` in CI entirely.
- **Provider version drift.** `terraform init -upgrade` updates `.terraform.lock.hcl`. Run it deliberately and review the diff.
- **`for_each` with a computed key** — Terraform errors out at plan time because it can't determine the resource map until apply. Restructure to use a known-at-plan-time key.
- **Cycles between modules.** Module A's output feeds module B's input which feeds module A. Refactor to a single owning module or use `terraform_remote_state`.
- **State file locked by a stuck process.** Last apply died mid-flight. Use `terraform force-unlock <LOCK_ID>` ONLY after confirming no other apply is genuinely running. Force-unlock during an active apply corrupts state.
- **Provider authentication drift in CI.** Token scoped too narrowly → plan succeeds, apply fails on a specific resource. Test the credentials' reach during pipeline setup, not in production at 3am.
- **Mixing `terraform` and `tofu` against the same state.** State written by a newer Terraform with HCP-only features can refuse to load in OpenTofu, and OpenTofu state encrypted natively can't be read by Terraform. Pick one binary per state file and enforce it via `.terraform-version` / `.opentofu-version` + the version manager's strict mode in CI.
- **Lockfile churn between platforms.** `terraform init` on macOS rewrites `.terraform.lock.hcl` to drop Linux hashes (or vice-versa), CI then re-rewrites on the next run, and the diff ping-pongs forever. Fix: `terraform providers lock -platform=linux_amd64 -platform=darwin_arm64 -platform=darwin_amd64` on every provider bump, commit the multi-platform lockfile, and gate CI on `terraform init -lockfile=readonly` so a rewrite is a hard failure.
- **Forgetting to remove an `import` block after the import lands.** `import` blocks are one-shot; leaving them in place is harmless but makes every subsequent plan noisy. Remove in the follow-up commit, the same way you'd remove a migration script.
