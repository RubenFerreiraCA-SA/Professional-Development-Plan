# Chapter 6 — GitOps, Automation and Operations (D06)

*DevOps Engineering textbook · Chapter 6 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D06 course detail](../../3%20Course%20Detail/3.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) (about 30–44 hours). |
| **Prerequisites** | [D03](D03%20Docker%20and%20Containerization.md), [D04](D04%20CICD%20and%20Build%20Automation.md), [D05](D05%20Infrastructure%20as%20Code%20and%20Terraform.md); basic Kubernetes Deployments/Services. Deeper cluster admin is P01–P02. |

## How to study this chapter

GitOps is not “kubectl from a pipeline.” It is a **pull-based reconciliation loop**: Git holds desired state; a controller makes the cluster match it; drift and recovery are visible in Git history.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Where sync, prune, digests or secrets go wrong, this chapter **shows a working sequence first**, then asks you to reproduce it, then adds a harder challenge.

Examples use **kind** (local Kubernetes), **Flux v2**, and **Kustomize** under `deploy/`. Argo CD follows the same [OpenGitOps](https://opengitops.dev/) principles; §6.10 maps the same layout to Argo if you prefer that controller. This text teaches [D06 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md). The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) D06 bar is: *desired state in Git is what the isolated cluster reconciles; after deliberate drift or a bad revision, you return to a known-good state with auditable Git history.*

> **Safety boundary:** Use an isolated local cluster or a disposable cloud sandbox. Do not point a training GitOps controller at a production cluster or a production Git repo with broad write access. Keep secrets out of Git. Prefer digest-pinned images. Destroy the kind cluster when finished.

### Learning outcomes

1. Explain reconciliation, drift, pull-based delivery and the GitOps trust model.
2. Maintain Kustomize (or Helm) config across environments with immutable image digests.
3. Promote D04 artifacts by Git change — without giving CI unrestricted cluster admin.
4. Demonstrate rollout, health, rollback and recovery via desired-state commits.
5. Practise day-two ops: probes, resources, HPA, pod failure, runbooks.
6. Diagnose stalled sync, unhealthy workloads and config errors.
7. Draw the Terraform vs GitOps ownership line and least-privilege controller access.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"
kubectl version --client
kind version
flux version || echo "Install flux CLI from https://fluxcd.io/flux/installation/"
docker image inspect harbour-api:local >/dev/null 2>&1 \
  || (cd app && docker build --build-arg HARBOUR_COMMIT="$(git rev-parse HEAD)" -t harbour-api:local .)
mkdir -p deploy/harbour-api/{base,overlays/staging,overlays/prod} clusters
```

You need Docker, `kind`, `kubectl`, and the `flux` CLI. A Git remote (GitHub/GitLab) that Flux can **read** is required for the full loop; a private training repo is ideal. If you cannot bootstrap against a remote yet, complete §6.3 render checks and skip to §6.3.5 (`kubectl apply -k`) so Kustomize work is not blocked — then return to Flux when the remote is ready.

---

## Section 6.1 — The GitOps operating model

### 6.1.1 Pull vs push

| Model | Who changes the cluster | Audit trail |
| --- | --- | --- |
| Imperative / push | Human or CI runs `kubectl` / API calls | Often scattered in pipeline logs |
| GitOps / pull | Controller reconciles toward Git | Desired state commits + controller events |

CI still **builds and publishes** digests (D04). GitOps **declares which digest** each environment should run. CI should not need cluster-admin to “deploy.”

### 6.1.2 Trust boundaries

| System | Owns |
| --- | --- |
| Terraform (D05) | Cluster, network, IAM foundations |
| Git `deploy/` | Workload desired state (Deployment, Service, Kustomize/Helm) |
| Flux / Argo | Reconciliation into chosen namespaces |
| Humans (break-glass) | Emergencies — then return ownership to Git |

### 6.1.3 Source repo vs desired-state layout

| Pattern | Pros | Cons |
| --- | --- | --- |
| Mono-repo `app/` + `deploy/` | One clone; easy local demos | Blast radius / permission coupling |
| Separate desired-state repo | Clear prod CODEOWNERS; CI writes digests via PR | Two remotes to wire |
| App-of-apps / cluster tree | Scales many services | More Flux/Argo objects to learn |

Harbour training default: **mono-repo** with `deploy/harbour-api/` and `clusters/<name>/` for controller config. Record any deviation in an ADR.

**ADR prompt** (`docs/decisions/0006-gitops-model.md`): mono-repo vs separate desired-state; who approves prod; whether auto-sync / prune / self-heal are on; how image digests get updated; Terraform vs GitOps resource list.

**Reflect:** What happens if CI *and* Flux both manage the same Deployment?

**Verify:** You can sketch the trust table from memory without looking it up.

---

## Section 6.2 — Isolated cluster and Flux install

### 6.2.1 Worked example — kind cluster + load Harbour image

```bash
kind create cluster --name harbour
kubectl cluster-info --context kind-harbour

# Make the local image available inside the kind nodes
kind load docker-image harbour-api:local --name harbour
kubectl get nodes
```

**Expected:** One control-plane node Ready; `harbour-api:local` is loadable for later manifests (`crictl` / node inspect optional).

If `kind load` fails, rebuild `harbour-api:local` (D03) and retry — Flux cannot pull an image that was never loaded and has no registry.

### 6.2.2 Worked example — bootstrap Flux against your Git repo

Export your training repo. Flux needs **read** access (deploy key or token with contents/read only for pull). Bootstrap itself needs enough permission to **commit** the Flux manifests once; rotate afterward if the token was overly broad.

```bash
export GITHUB_USER="<your-user>"
export GITHUB_REPO="<harbour-platform>"   # name only, not URL
# Create a fine-scoped token / deploy key for Flux; store locally, not in git:
export GITHUB_TOKEN="<token>"

flux bootstrap github \
  --context kind-harbour \
  --owner="${GITHUB_USER}" \
  --repository="${GITHUB_REPO}" \
  --branch=main \
  --path=clusters/harbour-local \
  --personal \
  --token-auth
```

GitLab / SSH deploy keys: follow current Flux bootstrap docs for that provider — same idea: controller reads desired state from Git.

**Expected:**

```bash
kubectl -n flux-system get pods
flux check
```

Pods Running; `flux check` reports success.

### 6.2.3 Practice — reproduce

On a fresh shell with `kubectl` context `kind-harbour`, re-run `flux check` and `kubectl -n flux-system get kustomizations,gitrepositories`.

### 6.2.4 Challenge — credential blast radius

Document what the bootstrap token could have done if it had been `repo` write + org admin. Rotate to a read-focused deploy key for ongoing reconciliation. Note the difference between **bootstrap** (writes Flux config once) and **reconcile** (reads desired state forever).

### 6.2.5 Verify

You can name the Git path Flux watches for this cluster (`clusters/harbour-local`) and show controllers healthy.

---

## Section 6.3 — Harbour desired state with Kustomize

### 6.3.1 Layout (target)

```text
deploy/
  harbour-api/
    base/
      kustomization.yaml
      deployment.yaml
      service.yaml
    overlays/
      staging/
        kustomization.yaml
        namespace.yaml
      prod/
        kustomization.yaml
        namespace.yaml
    RUNBOOK.md
clusters/
  harbour-local/
    ...                 # flux bootstrap files
    harbour-api-staging.yaml
```

Base is **namespace-agnostic**. Overlays set `namespace:` and own the Namespace object.

### 6.3.2 Worked example — base manifests

`deploy/harbour-api/base/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: harbour-api
  labels:
    app: harbour-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: harbour-api
  template:
    metadata:
      labels:
        app: harbour-api
    spec:
      containers:
        - name: harbour-api
          image: harbour-api:local   # overlays may retag / digest-pin
          ports:
            - name: http
              containerPort: 8000
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 15
            periodSeconds: 10
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
```

`deploy/harbour-api/base/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: harbour-api
  labels:
    app: harbour-api
spec:
  selector:
    app: harbour-api
  ports:
    - name: http
      port: 80
      targetPort: http
```

`deploy/harbour-api/base/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
```

### 6.3.3 Worked example — staging and prod overlays

`deploy/harbour-api/overlays/staging/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: harbour-staging
```

`deploy/harbour-api/overlays/staging/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: harbour-staging
resources:
  - namespace.yaml
  - ../../base
images:
  - name: harbour-api
    newName: harbour-api
    newTag: local
# Registry promotion (D04/D05) — replace images: with digest pin:
# images:
#   - name: harbour-api
#     newName: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/harbour-stg-api
#     digest: sha256:REPLACE_WITH_RELEASE_DIGEST
```

`deploy/harbour-api/overlays/prod/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: harbour-prod
```

`deploy/harbour-api/overlays/prod/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: harbour-prod
resources:
  - namespace.yaml
  - ../../base
images:
  - name: harbour-api
    newName: harbour-api
    newTag: local
```

**Render check (no cluster required):**

```bash
kubectl kustomize deploy/harbour-api/overlays/staging | head -n 100
kubectl kustomize deploy/harbour-api/overlays/prod | grep -E 'namespace:|image:'
```

**Expected:** Staging objects land in `harbour-staging`; image shows `harbour-api:local` until you pin a digest.

### 6.3.4 Helm vs Kustomize (choose deliberately)

| Need | Prefer |
| --- | --- |
| Thin env diffs on one service | Kustomize overlays (this chapter’s default) |
| Packaged chart with many knobs / upstream chart | Helm |
| Both | Helm for packaging + Flux HelmRelease, or Kustomize invoking a chart — document why |

Do **not** maintain two parallel sources of truth for the same Deployment. If you pick Helm for Harbour, replace the Kustomize tree with a chart and a Flux `HelmRelease`; keep digest pinning and two envs as requirements.

### 6.3.5 Worked example — apply without Flux (unblock path)

If bootstrap is blocked on credentials, prove manifests first:

```bash
kubectl apply -k deploy/harbour-api/overlays/staging
kubectl -n harbour-staging rollout status deploy/harbour-api
kubectl -n harbour-staging port-forward svc/harbour-api 8080:80 &
sleep 2
curl -sS http://127.0.0.1:8080/health
```

Then delete and let Flux own the same path later (`kubectl delete -k ...` after Flux is ready), so you do not dual-own.

### 6.3.6 Practice — reproduce

Add a staging-only patch that sets `replicas: 3`. Show `kubectl kustomize` staging ≠ prod.

### 6.3.7 Verify

Base has probes and resources; overlays only change env-specific image/namespace (and intentional patches). No Secret values in Git.

---

## Section 6.4 — Point Flux at Harbour staging

### 6.4.1 Worked example — Flux Kustomization

Prefer generating objects with the CLI and **committing** the YAML Flux writes (or that you place under `clusters/harbour-local/`), so Git remains the source of truth for controller config too.

```bash
# Reuse the GitRepository bootstrap created (often named flux-system), or create an app source:
flux create kustomization harbour-api-staging \
  --namespace=flux-system \
  --source=GitRepository/flux-system \
  --path=./deploy/harbour-api/overlays/staging \
  --prune=true \
  --interval=1m \
  --wait=true \
  --timeout=3m \
  --export > clusters/harbour-local/harbour-api-staging.yaml

git add clusters/harbour-local/harbour-api-staging.yaml
git commit -m "gitops: reconcile harbour-api staging"
git push
```

If your bootstrap root already recursively applies `clusters/harbour-local/`, pushing is enough. Otherwise apply once:

```bash
kubectl apply -f clusters/harbour-local/harbour-api-staging.yaml
```

Example shape (adjust `sourceRef.name` to match bootstrap):

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: harbour-api-staging
  namespace: flux-system
spec:
  interval: 1m
  sourceRef:
    kind: GitRepository
    name: flux-system
  path: ./deploy/harbour-api/overlays/staging
  prune: true
  wait: true
  timeout: 3m
```

Reconcile and exercise the Service:

```bash
flux reconcile source git flux-system -n flux-system
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
flux get kustomizations -A
kubectl -n harbour-staging get deploy,pods,svc
kubectl -n harbour-staging port-forward svc/harbour-api 8080:80 &
sleep 2
curl -sS http://127.0.0.1:8080/health
```

**Expected:** Kustomization Ready=True; pods Ready; `/health` returns Harbour JSON.

### 6.4.2 Worked example — read controller signals

```bash
flux get kustomizations harbour-api-staging -n flux-system
kubectl -n flux-system logs deploy/kustomize-controller --tail=50
kubectl -n harbour-staging get events --sort-by=.lastTimestamp | tail -n 20
```

Learn the difference between **Source failed** (Git/auth), **Build failed** (Kustomize/YAML), and **Health check failed** (workload not Ready).

### 6.4.3 Practice — reproduce

Delete the port-forward. Explain how you would expose the Service in kind (port-forward / Ingress) vs cloud (LB / Ingress). Document the choice in the Progress Log — do not invent a production Ingress you did not install.

### 6.4.4 Challenge — prune

With a disposable resource only: set `prune: false`, remove a ConfigMap from Git, observe it remaining; then re-enable prune on a **non-PVC** object and watch deletion. Document when prune is dangerous (PVCs, shared CRDs, Terraform-owned objects).

### 6.4.5 Verify

`flux get kustomizations` matches the Git path that actually runs; you did not leave a long-lived `kubectl apply -k` dual path.

---

## Section 6.5 — Promote the same digest via Git

### 6.5.1 Concept

Promotion is a **reviewed change to desired state**, not a new CI deploy job with cluster credentials.

| Actor | Allowed |
| --- | --- |
| D04 release | Publish image `@sha256:…` + evidence |
| Human / bot PR | Update overlay `images:` to that digest |
| Flux | Pull and reconcile |
| CI with cluster-admin | Not required for promotion |

### 6.5.2 Worked example — digest promotion (registry path)

When using ECR/GHCR from D04/D05:

1. Record `CONTAINER_IMAGE=…@sha256:abc…` from release evidence (`image-ref.txt` or job summary).
2. Update staging overlay `images:` to `newName` + `digest` (not a floating tag).
3. Open a PR; require review. Example CODEOWNERS:

```text
# .github/CODEOWNERS
/deploy/harbour-api/overlays/prod/  @your-user
```

4. Merge; Flux reconciles; verify running image:

```bash
kubectl -n harbour-staging get pods -o jsonpath='{.items[0].status.containerStatuses[0].imageID}{"\n"}'
```

5. Promote **the same digest** to prod overlay in a second PR (separate approval).

### 6.5.3 Worked example — local kind promotion simulation

Without a registry, simulate good/bad tags:

```bash
docker tag harbour-api:local harbour-api:good
kind load docker-image harbour-api:good --name harbour
# Set staging images newTag: good — commit, push, reconcile
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging get pods -o jsonpath='{.items[0].status.containerStatuses[0].image}{"\n"}'
```

### 6.5.4 Optional — CI updates desired state (still no cluster-admin)

A release workflow may open a PR that only changes `deploy/**/kustomization.yaml` image fields (or use Flux Image Automation Controllers). That bot needs **contents** permission on the desired-state path — **not** a kubeconfig. Keep required status checks honest about path filters (lesson from D04).

### 6.5.5 Practice — reproduce

Show Git commit SHA that changed the image and the cluster `imageID` side by side in your Progress Log.

### 6.5.6 Verify

Checklist: promotion is a Git change; CI did not need `kubectl apply` to the app namespace.

---

## Section 6.6 — Drift and self-heal

### 6.6.1 Worked example — imperative drift

```bash
kubectl -n harbour-staging scale deploy/harbour-api --replicas=5
kubectl -n harbour-staging get deploy harbour-api
flux reconcile kustomization harbour-api-staging -n flux-system
kubectl -n harbour-staging get deploy harbour-api
```

**Expected with sync + heal:** replicas return to the Git-declared value.

If you disable auto-remediation, document that drift stays until policy says otherwise — and justify it in the ADR (some regulated teams prefer detect-only).

### 6.6.2 Worked example — live image patch is temporary

```bash
kubectl -n harbour-staging set image deploy/harbour-api harbour-api=harbour-api:does-not-exist
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging get deploy harbour-api -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

Git wins under active reconciliation. Break-glass patches must be followed by a Git commit or they will be reverted.

### 6.6.3 Worked example — suspend for true break-glass

```bash
flux suspend kustomization harbour-api-staging -n flux-system
# emergency kubectl fix (training only)
flux resume kustomization harbour-api-staging -n flux-system
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
```

**Expected after resume:** Git desired state reasserts. Suspend is an explicit, auditable exception — ticket it.

### 6.6.4 Practice — reproduce

Capture evidence: `kubectl -n harbour-staging describe deploy harbour-api` and `flux get kustomizations`.

### 6.6.5 Verify

You can explain Ready vs Suspended vs Failed from `flux get` without guessing.

---

## Section 6.7 — Broken release and rollback via Git

### 6.7.1 Worked example — ship a broken desired state

Prefer a **training branch or disposable overlay path** if `main` must stay healthy. For a personal training repo:

```bash
cd "$HARBOUR_ROOT"
git switch -c demo/bad-rollout
# In staging overlay, set newTag: missing-tag (or a digest that does not exist)
git add deploy/harbour-api/overlays/staging
git commit -m "demo: broken harbour image for rollback drill"
git push -u origin HEAD
# Merge to the branch Flux tracks, or retarget Flux temporarily for the drill
```

```bash
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging get pods
kubectl -n harbour-staging get events --sort-by=.lastTimestamp | tail -n 30
flux get kustomizations harbour-api-staging -n flux-system
```

**Investigation order:** Flux Kustomization status → ReplicaSet/Pod events → image pull errors → probes → controller logs.

### 6.7.2 Worked example — recover by reverting desired state

```bash
git revert HEAD --no-edit   # or checkout known-good overlay files
git push
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging rollout status deploy/harbour-api
curl -sS http://127.0.0.1:8080/health
```

**Expected:** Recovery is a Git commit, not `kubectl delete pod` folklore.

### 6.7.3 Data and migrations (hard limit)

Reverting manifests does **not** reverse incompatible database migrations. Record in the runbook: schema changes need expand/contract (or equivalent) so old and new digests can coexist during rollout. GitOps rollback ≠ data rollback.

### 6.7.4 Progressive delivery (awareness)

| Strategy | Platform need |
| --- | --- |
| Rolling update | Default Deployment; readiness gates traffic |
| Blue/green | Two versions + traffic switch (Service/Ingress) |
| Canary / progressive | Extra controller (e.g. Flagger) + metrics |

For D06 Competent, a healthy rolling update + Git rollback is enough. Advanced: document what you would add for canary (metrics from D07, progressive controller) without pretending you installed it.

### 6.7.5 Practice — reproduce

Write three investigation bullets you actually used (events, pods, flux). Include the bad commit SHA and the revert SHA.

### 6.7.6 Challenge

Suspend Flux, “fix” live with kubectl, resume, and watch Git overwrite you. Document the lesson in the Progress Log.

### 6.7.7 Verify

Known-good image is running; Git history shows bad commit + revert; no secret credential was pasted into chat or commits.

---

## Section 6.8 — Day-two operations

### 6.8.1 Worked example — pod kill and client impact

```bash
# Terminal A — client loop
while true; do curl -sf http://127.0.0.1:8080/health || echo FAIL; sleep 0.2; done

# Terminal B — kill
POD="$(kubectl -n harbour-staging get pod -l app=harbour-api -o jsonpath='{.items[0].metadata.name}')"
kubectl -n harbour-staging delete pod "$POD"
kubectl -n harbour-staging get pods -w
```

Pod replacement ≠ zero downtime. With `replicas: 2` and readiness probes, record whether Terminal A printed `FAIL`. That observation belongs in the assessment evidence.

### 6.8.2 Worked example — HPA (metrics-server required)

kind often lacks metrics-server. If `kubectl top pods` fails, install metrics-server per current kind docs (typically a components YAML plus a kubelet TLS patch for kind). Only then:

`deploy/harbour-api/overlays/staging/hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: harbour-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: harbour-api
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

Add `- hpa.yaml` under staging `resources:`. Commit, reconcile, then:

```bash
kubectl -n harbour-staging get hpa
kubectl -n harbour-staging describe hpa harbour-api
```

If metrics stay `<unknown>`, fix metrics-server before claiming the HPA experiment passed — or document the gap and stop at “HPA object exists, metrics not available.”

### 6.8.3 Secrets (do not commit plaintext)

| Approach | Use when |
| --- | --- |
| Out-of-band Secret + `secretKeyRef` / `envFrom` | Local kind training |
| Sealed Secrets / SOPS | Encrypted material may live in Git with key mgmt |
| External Secrets Operator | Cloud secret manager is source of truth |

**Worked example — local only (never commit the applied values):**

```bash
kubectl -n harbour-staging create secret generic harbour-db \
  --from-literal=password='training-only-not-real' \
  --dry-run=client -o yaml | kubectl apply -f -
```

Reference via a Kustomize patch that names the key — not the value. Certificate rotation: document expiry monitoring and who renews TLS secrets; do not leave forever-valid training certs as a production pattern.

### 6.8.4 Backups and data ownership

| Question | Harbour training answer (fill in yours) |
| --- | --- |
| Where is durable state? | Usually **outside** the Deployment (managed DB / volume) |
| Who restores DB? | Platform/data runbook — not `git revert` |
| Who restores cluster? | Terraform / cluster rebuild, then Flux, then data |

### 6.8.5 Runbook stub

Create `deploy/harbour-api/RUNBOOK.md`:

```markdown
# harbour-api runbook

## Failed rollout
1. flux get kustomizations
2. kubectl -n harbour-staging get pods,events
3. Compare Git digest to imageID
4. Revert desired-state commit; reconcile

## Stalled reconciliation
1. Source auth / GitConnectivity
2. kustomize build errors
3. wait/timeout / probe failures

## Secrets
- Source of truth: ________
- Rotation owner: ________

## Data
- Backup location: ________
- Restore order: cluster → Flux → application data
```

### 6.8.6 Practice — reproduce

Kill a pod while curling; record client-visible errors. Note HPA metrics status honestly.

### 6.8.7 Verify

Runbook is in Git; secrets are not; you did not claim zero downtime without evidence.

---

## Section 6.9 — Safety, access and Terraform contract

### 6.9.1 Controller least privilege

- Prefer namespaced permissions for app reconciliation.
- Git credentials: read-only on application desired state for ongoing sync.
- Separate prod Kustomization + stronger CODEOWNERS.
- Avoid cluster-admin “for convenience.”
- Admission policies (OPA/Kyverno) are Advanced — mention if you add them.

### 6.9.2 Prune and shared resources

Do not let GitOps prune Terraform-managed or stateful resources. Keep an ownership list in ADR 0006:

| Resource | Owner |
| --- | --- |
| VPC, cluster, IAM, node groups | Terraform |
| Namespaces for apps (optional) | Terraform **or** GitOps — pick one |
| Deployment/Service/HPA | GitOps |
| PersistentVolumeClaims | Explicit decision; prune carefully |

### 6.9.3 Disaster recovery order (training notes)

1. Restore cluster / control plane capability (often Terraform).
2. Restore Flux / sync credentials.
3. Reconcile desired state from Git.
4. Restore application data from backups **if** the app depends on it.

### 6.9.4 Verify

ADR states Terraform owns foundations; Flux owns workloads under `deploy/`; dual ownership is absent.

---

## Section 6.10 — Argo CD mapping (optional path)

If you choose Argo CD instead of Flux, keep the **same** `deploy/harbour-api` tree. Rough mapping:

| Flux | Argo CD |
| --- | --- |
| GitRepository + Kustomization | Application (`source.path` → overlay) |
| `prune: true` | `syncPolicy.automated.prune` |
| self-heal | `syncPolicy.automated.selfHeal` |
| `flux reconcile` | Sync button / `argocd app sync` |
| suspend | disable auto-sync |

Install Argo into kind per current upstream getting-started; point one Application at `deploy/harbour-api/overlays/staging`. Assessment evidence is the same: Git desired state, digest promotion, drift, Git rollback, day-two notes.

---

## Section 6.11 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Kustomization not Ready | Bad path / YAML / auth | `flux get` message; `kubectl kustomize` locally |
| ImagePullBackOff | Digest/tag missing on nodes/registry | `imageID`; `kind load` / registry auth |
| CrashLoopBackOff | App/config error | logs; probes too aggressive? |
| Remains drifted | Suspended or no reconcile | `flux get`; resume |
| Prune deleted shared object | Ownership mistake | ADR; restore from TF/Git carefully |
| HPA unknown metrics | No metrics-server | `kubectl top`; install/fix metrics |

---

## Practical Assessment — Chapter 6 — controlled release and recovery

Align with [D06 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) and Final Project Checklist D06.

### Required deliverables

1. GitOps controller on an isolated cluster with clear Git path and RBAC/secret boundaries.
2. Two env overlays (staging/prod) with immutable image references (digest or documented local tag policy).
3. Reviewed promotion of a D04 artifact (or simulated digest) between envs via Git.
4. Broken-release drill with diagnosis and **Git** rollback.
5. Drift drill with reconcile or documented non-auto policy.
6. Pod kill / HPA experiment evaluated against client-facing behaviour.
7. Runbook covering rollout failure, secrets and data assumptions.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Model | Can sync an app | Explains pull loop, trust, TF vs GitOps | Guardrails making Git easier than kubectl |
| Config | Single manifest | Kustomize/Helm envs + digests | Progressive delivery awareness |
| Promotion | CI kubectl | GitOps PR promotion of same digest | Image-update automation with review |
| Recovery | Delete pods | Git revert restores known-good | Data/migration limits documented |
| Drift | Confused by reset | Demonstrates heal or justified suspend | Policy for prune/exceptions |
| Day-two | Happy path only | Probes, resources, runbook, kill test | HPA with real metrics + client impact notes |

**Completion standard:** **Competent** on every row. Another engineer can answer what should run, what runs, why they differ, and how to recover **without** undocumented live edits.

### Self-check

- Does Flux/Argo show the same image Git declares?
- Can you promote without cluster creds in CI?
- Did rollback go through Git?
- Are secrets absent from the repo?
- Is prune scoped safely?
- Does the runbook admit what Git revert cannot fix?

### Example assessment conclusion (evidence still required)

> kind cluster `harbour` runs Flux against `deploy/harbour-api/overlays/staging`. Promotion PRs change image digests only. A bad tag was reverted in Git; Flux restored Ready pods. Manual scale drift self-healed. Pod kill showed brief client errors with two replicas. HPA object present; metrics-server noted. Runbook committed. Terraform remains out of the Deployment ownership path.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Deploy a new digest | PR to overlay `images:` | `kubectl set image` as permanent fix |
| Debug sync | `flux get`, controller logs, events | Only deleting pods |
| Handle drift | Reconcile or suspend with ticket | Silent console edits |
| Roll back | `git revert` known-good | Hope registry still has `:latest` |
| Secrets | External/sealed/out-of-band | Plain Secret YAML with values in Git |
| Own a resource | ADR: Terraform xor GitOps | Dual controllers on one object |
| Prove availability | Client curl loop during kill | Equating new pod with zero downtime |

## Glossary

| Term | Definition |
| --- | --- |
| Reconciliation | Loop comparing desired vs live state and acting |
| Drift | Live state differs from desired state |
| Prune | Delete live resources removed from desired state |
| Self-heal | Revert manual/live changes back to Git |
| Overlay | Env-specific Kustomize layer on a shared base |
| Digest pin | Image reference by `@sha256:…` |
| Break-glass | Emergency imperative access outside normal GitOps |
| Suspend | Pause reconciliation so live edits can stick temporarily |

## References

- [OpenGitOps](https://opengitops.dev/)
- [Flux](https://fluxcd.io/flux/)
- [Argo CD](https://argo-cd.readthedocs.io/)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [kind](https://kind.sigs.k8s.io/)
- [Kustomize](https://kubectl.docs.kubernetes.io/references/kustomize/)

**Previous chapter:** [Chapter 5 — Infrastructure as Code and Terraform](D05%20Infrastructure%20as%20Code%20and%20Terraform.md) · **Course detail:** [D06 — GitOps, Automation and Operations](../../3%20Course%20Detail/3.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) · **Next chapter:** Chapter 7 — Observability (not yet authored) · **Checklist:** [Final Project Checklist · D06](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
