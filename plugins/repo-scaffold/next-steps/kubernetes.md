  - cd "$REPO"
  - Choose: Kustomize-first (kustomize/base + overlays) OR Helm (charts/).
    Don't mix without a clear seam — the scaffold left both dirs in place,
    delete the one you won't use.
  - Always set kubectl --context explicitly (never rely on current-context).
  - Add resources.requests/limits + readinessProbe/livenessProbe to every
    Deployment from the start. The stack profile's "Common traps" section
    has the debug runbooks (OOMKilled, CrashLoopBackOff, Pending, etc.).
  - Edit CLAUDE.md: which clusters this repo deploys to, gitops controller
    (ArgoCD/Flux/none).
