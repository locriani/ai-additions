# Stack Profile: Kubernetes

Load this profile when the project meaningfully exercises Kubernetes — i.e. there are `*.yaml` / `*.yml` files under `k8s/`, `kubernetes/`, `manifests/`, `deploy/`, `charts/` (Helm), `kustomize/`, or the user is authoring/editing manifests, Helm charts, or operating a cluster. Also load when the work is **debugging a running cluster** (kubectl-heavy) regardless of repo shape.

## Toolchain

- **Target Kubernetes 1.34+** as your floor. As of mid-2026, supported minor releases are 1.34, 1.35, 1.36 — anything older is EOL and unpatched. The community supports the most recent three minors with ~14 months of patches each; 1.33 hit EOL mid-2026.
- **`kubectl`** — the Kubernetes CLI. `brew install kubectl` (or `kubernetes-cli`). Track latest stable; mismatched client/server versions cause subtle bugs (kubectl is forward+1 / backward+1 compatible with the API server).
- **`kubectx` + `kubens`** — context + namespace switching. `brew install kubectx`. Far better than typing `kubectl config use-context` repeatedly.
- **`k9s`** — TUI for cluster inspection. `brew install k9s`. Great for browsing pods/logs/events without memorizing `kubectl` flags.
- **`stern`** — multi-pod log tailing with regex filters. `brew install stern`. Replaces `kubectl logs <pod>` for anything beyond a single pod.
- **`helm`** — package manager (charts). `brew install helm`. **Helm 4** (released Nov 2025 at KubeCon) is current; Helm 3.20+ runs in parallel through ~mid-2026 EOL. Helm 4 switches **new** installs to Server-Side Apply by default and ships a redesigned Wasm-plugin system; existing 3.x releases keep client-side apply after upgrade — don't expect SSA semantics until you reinstall the release. Helm 2 (Tiller) has been dead for years.
- **`kustomize`** — overlay-based config management, built into `kubectl` (`kubectl apply -k`). The embedded version typically lags the standalone by 1–2 minor versions; install the standalone binary when you need newer transformers/generators (e.g. `replacements`, post-build component composition).
- **`yq`** — `jq` for YAML. `brew install yq`. Mandatory for any non-trivial manifest manipulation in scripts.
- **`kubeconform`** — schema validator, faster than `kubeval` (which is unmaintained). `brew install kubeconform`.
- **`kube-linter`** — production-readiness linter (StackRox). `brew install kube-linter`.
- **`trivy`** — security scanner for images + manifests + IaC. `brew install trivy`.
- **`kind`** / **`minikube`** / **`k3d`** for local clusters. `kind` is the most common for CI; `k3d` is fastest for laptops.

## Platform add-ons (the 2026 baseline)

Most prod clusters end up with the same handful of operators. Default to these unless you have a specific reason not to:

- **Cilium (eBPF CNI)** — the mainstream default in 2026. GKE, EKS, and AKS all ship eBPF-mode (Cilium or Cilium-derived) as their recommended dataplane. Pick Cilium for any new self-managed cluster: kube-proxy replacement, L7 policy without sidecars, native NetworkPolicy + CiliumNetworkPolicy, Hubble observability. Calico/Flannel are still fine for existing clusters but stop being the obvious choice for new builds.
- **cert-manager** — still THE standard for TLS issuance. ACME (Let's Encrypt), private CA, and Vault issuers all first-class. Treat it as part of the control plane.
- **external-dns** — automates DNS records from Ingress / Gateway / HTTPRoute / Service annotations. Standard. Works with most DNS providers.
- **External Secrets Operator (ESO)** — the standard sync layer between Kubernetes Secrets and AWS Secrets Manager / GCP Secret Manager / Vault / 1Password / etc. Don't roll your own. Sealed-secrets is a legitimate alternative when you want secrets-in-git, but ESO + a real secret manager is the more common 2026 pattern.
- **KEDA** — event-driven autoscaling. The default once HPA-on-CPU/memory isn't enough. Scales on Kafka lag, SQS depth, Prometheus queries, cron, and ~70 other scalers. CNCF graduated. Reach for KEDA before writing custom metrics-server adapters.
- **metrics-server** — required for `kubectl top` and HPA. Install it; it isn't on by default in vanilla clusters.
- **Kyverno** for policy as code. Kubernetes-native, YAML policies, supports validate + mutate + generate + verifyImages. Preferred over OPA Gatekeeper for new clusters in 2026 unless you specifically need cross-platform Rego (CI/CD, Terraform). Don't run both — pick one and commit.

## Project shape

- **`*.yaml`** for manifests (not `*.yml`) — the upstream convention. Keep one resource per file, OR multiple resources separated by `---` in a single file when they're tightly coupled (e.g. `Deployment` + `Service` + `ConfigMap` for one app).
- **Directory layout** — pick one and stick with it:
  - **Kustomize:** `base/` (default manifests) + `overlays/<env>/` (dev, staging, prod patches). Each `overlays/<env>/kustomization.yaml` references base + adds patches.
  - **Helm:** `charts/<name>/` containing `Chart.yaml`, `values.yaml`, `templates/`. `values-<env>.yaml` per environment.
  - **GitOps (Argo/Flux):** an `apps/` directory with `Application` / `Kustomization` resources pointing at the source.
- **No mixing Helm + Kustomize unprovoked.** They can compose (`helm template | kustomize build`), but the resulting workflow is harder to debug. Pick one per chart/app.
- **`.dockerignore`** alongside `Dockerfile` — keep build context small.

## kubectl discipline

- **`KUBECONFIG`** is your responsibility. Always check `kubectl config current-context` before running anything mutating. The classic disaster: you ran `kubectl delete ns staging` against prod because you forgot to `kubectx`.
- **`-n <namespace>` explicitly** in scripted use. The default namespace is whatever the kubeconfig says; relying on it across machines is fragile.
- **`--context=<ctx>`** in scripts that target a specific cluster. Don't rely on the operator's current context — name the target.
- **`--dry-run=client`** to validate manifests without applying. **`--dry-run=server`** sends to the API server for full admission validation (catches webhook rejections).
- **`-o yaml`** for full output, **`-o json | jq`** for parsing. **`-o jsonpath='{...}'`** for one-off scripted reads, but `jq` is more powerful when you need it.
- **`kubectl diff -f manifest.yaml`** before `apply` for any non-trivial change. Read the diff. Don't apply a diff you don't understand.
- **`kubectl apply -f`** is the default. **`kubectl create -f`** errors if the resource exists; **`kubectl replace -f`** errors if it doesn't. `apply` is idempotent and tracks the last-applied annotation for 3-way merges.
- **`kubectl edit`** is for emergencies. Edits made via `edit` aren't in git, so they're invisible to GitOps and the next `apply` will revert them. Treat `edit` as a debugging tool, not a config mechanism.

## Common commands

```bash
# Inspection
kubectl get pods -n <ns>                      # list pods
kubectl get all -n <ns>                       # list common resources
kubectl describe pod <pod> -n <ns>            # full status (events at the bottom)
kubectl logs <pod> -n <ns> -c <container>     # logs
kubectl logs -f <pod> -n <ns> --tail=100      # follow + tail
stern -n <ns> <regex>                         # multi-pod tailing
kubectl exec -it <pod> -n <ns> -- bash        # shell into a container
kubectl port-forward -n <ns> svc/<svc> 8080:80  # local tunnel

# Apply / diff
kubectl apply -f manifest.yaml                # apply (idempotent)
kubectl apply -k overlays/prod                # kustomize
kubectl diff -f manifest.yaml                 # show what would change
kubectl delete -f manifest.yaml               # delete resources defined in file

# Debugging
kubectl get events -n <ns> --sort-by=.lastTimestamp   # cluster events
kubectl top pod -n <ns>                       # resource usage (needs metrics-server)
kubectl rollout status deploy/<name> -n <ns>  # wait for rollout
kubectl rollout undo deploy/<name> -n <ns>    # rollback
kubectl rollout history deploy/<name> -n <ns> # past revisions

# Helm
helm install <release> <chart> -n <ns> --create-namespace -f values.yaml
helm upgrade <release> <chart> -n <ns> -f values.yaml
helm diff upgrade <release> <chart> -f values.yaml   # needs helm-diff plugin — install it
helm rollback <release> <revision> -n <ns>
helm template <release> <chart> -f values.yaml       # render without applying
```

## Ingress vs Gateway API (the 2026 inflection point)

- **Default to Gateway API for new projects.** Gateway API v1 has been GA since late 2023; v1.1+ rounded out the core (HTTPRoute, GRPCRoute, TLSRoute, BackendTLSPolicy). By 2026 it is the recommended path for new clusters and is what cloud-managed load-balancer controllers (AWS LBC, GKE Gateway, AKS App Routing) target as their first-class API. The role split — `GatewayClass` (infra), `Gateway` (operator), `*Route` (app team) — actually matches how teams already work; Ingress's single overloaded resource doesn't.
- **`ingress-nginx` (the kubernetes/ingress-nginx project) is end-of-life as of March 2026.** No more releases, no bug fixes, no security patches. Its planned successor "InGate" stalled. If you're on `ingress-nginx`, you have a migration project. Do not start new clusters on it.
- **Migration paths off `ingress-nginx`:**
  - **Preferred:** move to a Gateway API implementation — `kgateway` (formerly Gloo), Envoy Gateway, Cilium Gateway, GKE Gateway, AWS Load Balancer Controller (Gateway API GA in 2026), Istio (with its built-in Gateway API support), or Contour. Use `ingress2gateway` (1.0+) to translate existing Ingress + annotations.
  - **Acceptable bridge:** F5's separately-maintained `nginx-ingress` project (NIC) is a different product from the retired community `ingress-nginx` — same NGINX dataplane, actively maintained. Reasonable if you need a low-friction lift-and-shift, but it's a holding pattern, not a destination.
- **Existing Ingress resources keep working.** The Ingress API itself is GA and isn't being removed; only the specific `ingress-nginx` controller is dying. You don't have to migrate to Gateway API on a deadline — but new work should land there.

## Manifest conventions

- **Resource limits + requests on every container.** Not a suggestion. Without limits, one bad pod can starve the node:
  ```yaml
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  ```
  Memory limit hit = OOMKilled. CPU limit hit = throttling (slower, but no kill).
- **Liveness + readiness probes** on long-running services. Without readiness, traffic hits pods before they're ready. Without liveness, hung pods stay in the load-balancer rotation forever.
  - **Readiness** = "should I get traffic?" Cheap, frequent, fast-fail.
  - **Liveness** = "should I be killed and restarted?" Expensive, infrequent, slow-fail. A misconfigured liveness probe will restart-loop your healthy app.
  - **Startup probe** for slow-starting apps so liveness doesn't kill them during init.
- **Image tags pinned to a digest** (`@sha256:...`) for prod, OR an immutable tag (`v1.2.3`). Never `:latest` in committed manifests — what `latest` means depends on when the cluster pulled, which is unreproducible.
- **`imagePullPolicy: IfNotPresent`** for tagged images, **`Always`** only when you genuinely re-tag the same name (anti-pattern, but sometimes unavoidable).
- **Pod Security Admission (PSA)** is the policy enforcement layer. PodSecurityPolicy (PSP) was removed in 1.25 — gone, not deprecated, gone. PSA enforces three profiles (`privileged`, `baseline`, `restricted`) at the namespace level via labels. The 2026 baseline:
  ```yaml
  metadata:
    labels:
      pod-security.kubernetes.io/enforce: baseline
      pod-security.kubernetes.io/enforce-version: latest
      pod-security.kubernetes.io/audit: restricted
      pod-security.kubernetes.io/warn: restricted
  ```
  Start at `enforce: baseline` + `audit/warn: restricted`, fix violations iteratively, then promote `enforce` to `restricted`. The `kube-system` namespace stays `privileged` — don't fight it. PSA covers ~80% of common needs; reach for Kyverno only when you need mutate/generate/cross-resource policy.
- **`securityContext`** with `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, dropped capabilities. These are required by the `restricted` PSA profile. Pod-level for defaults, container-level for overrides:
  ```yaml
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
  ```
- **`Service` with explicit `port` + `targetPort`** even when they're the same. `targetPort: http` referencing a named container port is the most refactor-safe form.
- **`Deployment` `strategy.rollingUpdate.maxUnavailable: 0`** for zero-downtime rollouts (combined with sufficient replicas + readiness probes).
- **`PodDisruptionBudget`** for any service you'd page on losing — tells the cluster how many pods may be voluntarily disrupted (e.g. node drain) at once.
- **`HorizontalPodAutoscaler`** for variable load. Always set `minReplicas` ≥ 2 in prod; 1 means a single node failure = downtime.
- **`NetworkPolicy`** by default-deny in prod namespaces. Without one, every pod can talk to every other pod cluster-wide.
- **`ConfigMap` for non-secret config**, **`Secret` for secrets** — but Secrets are **base64, NOT encrypted at rest by default**. Use a real secret manager (External Secrets Operator + Vault / AWS Secrets Manager / GCP Secret Manager) for anything sensitive.

## Labels + selectors

- **Standard labels** (the official set):
  ```yaml
  metadata:
    labels:
      app.kubernetes.io/name: <app>
      app.kubernetes.io/instance: <release>
      app.kubernetes.io/version: <version>
      app.kubernetes.io/component: <component>
      app.kubernetes.io/part-of: <system>
      app.kubernetes.io/managed-by: <tool>
  ```
- **Selectors are immutable** on `Deployment` / `StatefulSet` / `DaemonSet`. Once you create one with `matchLabels: {app: foo}`, you cannot change that without delete-and-recreate. Pick selector labels carefully.
- **Don't use `app: <name>` as the only selector** — too generic, collides across namespaces, doesn't work with the recommended-labels scheme above.

## Helm-specific discipline

- **`helm-diff` plugin** mandatory: `helm plugin install https://github.com/databus23/helm-diff`. Run `helm diff upgrade ...` before every `helm upgrade`. Same rule as `kubectl diff` — never apply a diff you haven't read.
- **`Chart.yaml` `version`** bumped on every chart change (semver). `appVersion` separately tracks the app's version. Confusing but standard.
- **`values.yaml` documented** — every field has a comment explaining what it does and what valid values are.
- **`templates/_helpers.tpl`** for repeated logic. Don't copy-paste templated YAML across files.
- **`{{ include "..." . }}` over `{{ template "..." . }}`** — the former is pipeline-friendly (`| nindent 4`), the latter isn't.
- **`.Values.foo | default "bar"`** for safe defaults; **`required "msg" .Values.foo`** for mandatory inputs.
- **`helm template` output reviewed** for non-trivial chart changes. The rendered manifests are what actually ships.

## GitOps (Argo CD / Flux)

- **Both Argo CD and Flux are CNCF Graduated and production-grade in 2026.** There's no wrong answer, but adoption is heavily skewed: ~60% of GitOps clusters surveyed by CNCF run Argo CD, ~11% run Flux. **Default to Argo CD for new projects** — bigger ecosystem, an actual UI, ApplicationSets are excellent for fleets, and the broader Argo family (Workflows, Events, Rollouts) composes naturally. Pick Flux when you want a controller-only, mix-and-match toolkit and don't need the UI.
- **Manifests in git are the source of truth.** No imperative `kubectl apply` against a GitOps-managed cluster — the controller will revert it.
- **App-of-apps / ApplicationSets** for managing fleets via a single root. ApplicationSets (generators: list, cluster, git, matrix, scm) are the modern pattern; raw app-of-apps still works but is dated.
- **Sync waves** (`argocd.argoproj.io/sync-wave`) for ordering — CRDs install before resources that use them.
- **Health checks** for custom resources — Argo doesn't know if your CR is "healthy" without a `Health.lua` or built-in support.
- **Drift = a finding, not a feature.** If the cluster has drifted from git, the answer is to find what manually changed it and either codify it OR revert.

## Service mesh — do you actually need one?

Default answer in 2026: **probably not, yet.** A mesh is dead weight until you have a concrete need. Reach for one only when you can name which of these you want: workload-identity-based mTLS everywhere, L7 traffic policy (canary, header routing, fault injection), per-request authz, or cross-cluster service discovery. If you just want pod-to-pod encryption, Cilium WireGuard or IPsec at the CNI layer is simpler. If you just want telemetry, eBPF observability (Hubble, Pixie) gets you most of the way without a mesh.

When you DO need a mesh:

- **Linkerd** for ~60% of cases — small teams, single-cluster, "just turn on mTLS and tracing." Trivial install, negligible overhead, minimal operational surface.
- **Istio Ambient mode** for the rest — multi-cluster, multi-tenant, advanced L7 policy, teams that already know Istio. Ambient (sidecar-less, ztunnel + waypoint proxies) is GA and has eliminated the historical sidecar-overhead complaint. Don't start new Istio installs in sidecar mode.
- **Cilium Service Mesh** when you're already deep in Cilium and only need L4 mTLS + identity-aware policy. Extending Cilium beats deploying a second control plane. For L7 routing on top of Cilium, pair with Istio Ambient or use Cilium Gateway.

## Cluster operations

- **`kubectl cordon <node>`** before maintenance — marks unschedulable.
- **`kubectl drain <node> --ignore-daemonsets --delete-emptydir-data`** to evict pods cleanly. Respects PodDisruptionBudgets.
- **`kubectl uncordon <node>`** to return to service.
- **`kubectl rollout restart deploy/<name>`** to force a rolling restart without changing the manifest.
- **Don't `kubectl delete pod <pod>`** to "fix" things in prod without understanding why. The pod will respawn (if managed), but you've masked the underlying issue and lost the diagnostic state.
- **`kubectl debug`** for ephemeral debug containers attached to a running pod (stable since 1.25) — better than baking a shell into prod images. Modern usage:
  - `kubectl debug -it <pod> --image=busybox:1.36 --target=<container>` — share PID namespace with the target so you can `ps`, `nsenter`, etc.
  - `kubectl debug node/<node> -it --image=ubuntu` — node debugging without SSH.
  - `--profile=general` (or `netadmin` / `restricted` / `sysadmin`) — `--profile=legacy` is deprecated; specify a profile explicitly.
  - `--copy-to=<new-pod>` to debug a copy of a CrashLoopBackOff pod with a different image or command, leaving the original alone.

## CRDs and conversion webhooks

- **Pin CRD versions explicitly.** When a CRD ships v1alpha1 → v1beta1 → v1, the storage version is what's in etcd; served versions are what clients can read/write. A conversion webhook bridges them. Read the CRD's `spec.versions[].storage` and `spec.conversion.strategy` before upgrading the operator — a botched conversion webhook is a "stored objects unreadable" outage.
- **Operator upgrades that bump CRD versions** must run the operator's documented migration (`kubectl-convert`, an init job, or `helm upgrade --skip-crds` followed by manual CRD apply). Don't blindly `helm upgrade` operators that ship CRDs in the chart — Helm's CRD handling is famously incomplete.
- **`kubectl explain <resource>.<field> --recursive`** to inspect the schema of an installed CRD. Faster than reading the CRD YAML.

## Verification ritual

Before claiming a Kubernetes change is done:

1. **`kubeconform -strict <manifest>`** (or `-summary` for batches) clean — schema-valid against the target Kubernetes version.
2. **`kube-linter lint <manifest>`** — no production-readiness regressions.
3. **`trivy config <dir>`** — no new HIGH/CRITICAL misconfigurations.
4. **`kubectl diff -f manifest.yaml`** (or `helm diff upgrade`) reviewed — every line of the diff is intentional.
5. **`kubectl apply --dry-run=server`** clean — admission webhooks accept it.
6. For a real apply: **rollout watched** (`kubectl rollout status`) — pods come up healthy, no CrashLoopBackOff, no ImagePullBackOff, events clean.
7. For prod: a second engineer reviewed the diff before apply.

## Common traps

- **`OOMKilled` looks like a crash.** Container hit memory limit, kernel killed it. Either raise the limit OR fix the leak — `kubectl describe pod` shows `OOMKilled` in `Last State.Reason`.
- **`CrashLoopBackOff`** — exponential backoff between restarts. The actual error is in `kubectl logs <pod> --previous` (the LAST run, not the current one which hasn't started). Without `--previous` you see nothing.
- **`ImagePullBackOff` / `ErrImagePull`** — registry auth, typo'd image name, wrong tag, missing imagePullSecret. `kubectl describe pod` events are explicit.
- **`Pending` for a long time** — usually no node has the resources. Check `kubectl describe pod` events for `FailedScheduling`. Could also be a missing PVC, a taint without a toleration, or a node selector that matches nothing.
- **`Terminating` forever** — a finalizer hasn't completed. `kubectl get <resource> -o yaml` shows the finalizer list. Removing finalizers manually (`kubectl patch ... -p '{"metadata":{"finalizers":null}}'`) is a last resort — the finalizer was there for a reason (e.g. cleanup of external resources).
- **Service points at zero pods.** Selector mismatch. `kubectl get endpoints <svc>` shows what the service actually resolves to. If empty, the selector doesn't match any pod's labels.
- **DNS resolution flaky.** `nslookup` from inside a pod (or use `kubectl run -it --rm debug --image=busybox -- nslookup <svc>`). Common: forgot `<svc>.<ns>.svc.cluster.local` for cross-namespace, or `coredns` is unhealthy.
- **PVC stuck `Pending`** — no StorageClass that satisfies the claim, or no available PV (for static provisioning). Check `kubectl describe pvc`.
- **`kubectl apply` removed something you didn't expect.** Apply uses 3-way merge based on the `last-applied-configuration` annotation. If you previously created the resource without `apply` (e.g. via `create`), the annotation is missing and apply may overwrite fields you didn't intend.
- **HPA flapping** — scaling up + down rapidly. Tune `behavior.scaleDown.stabilizationWindowSeconds` (default 5m). Or your metric is too noisy (e.g. CPU when the workload is bursty).
- **Cluster autoscaler not scaling up** — pods Pending despite the ASG having capacity. Check the autoscaler's logs; usually a node group taint, instance type mismatch, or quota issue.
