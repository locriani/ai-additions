  - cd "$REPO"
  - Author backend.tf with REMOTE state + locking BEFORE the first `terraform init`.
    Local state on a real project is technical debt the moment it touches a
    teammate's hands. (See stack profile for S3+DynamoDB / GCS / Azure shapes.)
  - terraform init
  - terraform fmt -recursive
  - Write your first module under modules/ and reference it from environments/dev.
  - Run tfsec + checkov locally before the first `plan`.
  - Edit CLAUDE.md: prevent_destroy lifecycle rules on stateful resources.
