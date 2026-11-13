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

> **Platform transition (read this):** [D05](D05%20Infrastructure%20as%20Code%20and%20Terraform.md) runs Harbour on **AWS ECS/Fargate**. This chapter deliberately switches the **runtime platform** to a **local kind Kubernetes cluster** so you can learn GitOps (controllers, namespaces, probes, HPA) without adding another always-on AWS control plane. You are **not** installing Flux onto the ECS service from D05. Digests and promotion habits still transfer; the compute substrate is different. When you later put GitOps on a real Kubernetes cluster in the cloud, Terraform (D05) still owns the cluster foundations and GitOps owns the workloads — same contract, different place.

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

### 6.2.4 Worked example — hand off from bootstrap token to read-only Git access

**Bootstrap** often needs write access so Flux can commit its install manifests once. **Ongoing reconciliation** should only **read** desired state. Rotating or deleting the personal access token in GitHub **does not** by itself replace the Secret already stored in the cluster.

**Planned transition ≠ uninterrupted availability.** On a training kind cluster, a short reconcile outage while you cut over credentials is acceptable if you treat it as a **maintenance window**: prepare the new identity, switch Secret and URL **together**, verify, then revoke the old token. Do not claim zero-downtime rotation unless you have dual credentials overlapping by design (advanced; not required here).

#### Path A — stay on HTTPS (simplest atomic swap)

Replace the token **inside** the existing HTTPS Secret. `GitRepository.spec.url` stays `https://…` — Secret and URL never disagree.

```bash
# Read-only PAT (contents:read) — store only in the cluster Secret, not in Git
flux create secret git flux-system \
  --namespace=flux-system \
  --url="https://github.com/${GITHUB_USER}/${GITHUB_REPO}.git" \
  --username=git \
  --password="${GITHUB_READONLY_TOKEN}"

flux reconcile source git flux-system -n flux-system
flux get sources git flux-system -n flux-system
```

**Expected:** Source Ready=True using the new token. **Then** revoke the bootstrap PAT. Reconcile once more to prove the revoked token is unused.

#### Path B — HTTPS → SSH deploy key (coordinate Secret + URL)

`GitRepository.spec.url` and the Secret’s credential material **must agree** (HTTPS Secret with `https://` URL, or SSH key Secret with `ssh://` URL). Changing only one first breaks fetch until the other catches up — that is a **planned cutover**, not a seamless handoff.

1. Create a **read-only deploy key** on the training repo. Save the private key locally (not in Git).

2. Capture known_hosts for the Git host (Flux SSH Secrets need host key material):

```bash
ssh-keyscan github.com > /tmp/flux-known_hosts 2>/dev/null
# Spot-check: file is non-empty and lists github.com
wc -l /tmp/flux-known_hosts
```

3. **Prepare** the new Secret YAML and the GitRepository URL edit **before** applying either permanently. Prefer a **new Secret name** so you can point the GitRepository at it in one commit:

```bash
flux create secret git flux-system-ssh \
  --namespace=flux-system \
  --url="ssh://git@github.com/${GITHUB_USER}/${GITHUB_REPO}.git" \
  --private-key-file="${HOME}/.ssh/harbour-flux-ro" \
  --known-hosts-file=/tmp/flux-known_hosts \
  --export > /tmp/flux-git-secret-ssh.yaml
# Inspect locally (no private key in git):
kubectl apply -f /tmp/flux-git-secret-ssh.yaml
shred -u /tmp/flux-git-secret-ssh.yaml 2>/dev/null || rm -f /tmp/flux-git-secret-ssh.yaml
rm -f /tmp/flux-known_hosts
```

4. In the same local change set under `clusters/harbour-local/` (bootstrap GitRepository manifest), set **both**:

- `.spec.url` → `ssh://git@github.com/${GITHUB_USER}/${GITHUB_REPO}.git`
- `.spec.secretRef.name` → `flux-system-ssh`

Commit and push that single change (or apply the patched GitRepository once if you are mid-bootstrap and the source cannot pull yet — then commit the same YAML so Git catches up):

```bash
# Example one-shot apply for the cutover window (still commit the same fields to Git):
kubectl -n flux-system patch gitrepository flux-system --type=merge -p '{
  "spec": {
    "url": "ssh://git@github.com/'"${GITHUB_USER}"'/'"${GITHUB_REPO}"'.git",
    "secretRef": { "name": "flux-system-ssh" }
  }
}'
```

**Do not** apply an SSH-only Secret to a GitRepository that still says `https://…`, and do not flip the URL to `ssh://` while the Secret still only holds an HTTPS token.

5. **Verify the new identity** before revoking anything:

```bash
kubectl -n flux-system get gitrepository flux-system \
  -o jsonpath='url={.spec.url} secret={.spec.secretRef.name}{"\n"}'
flux reconcile source git flux-system -n flux-system
flux get sources git flux-system -n flux-system
kubectl -n flux-system logs deploy/source-controller --tail=40 | grep -iE 'error|github|ssh|auth' || true
# After §6.4 exists:
# flux reconcile kustomization harbour-api-staging -n flux-system --with-source
```

**Expected:** `url` is `ssh://…`, `secretRef` is `flux-system-ssh`, Source Ready=True. If it fails (host key, deploy key not read-only on the right repo, wrong URL), **fix before** revoking the bootstrap token — you may temporarily patch back to HTTPS + old Secret to restore fetch while you debug.

6. **Only then** revoke the original bootstrap PAT in the Git host UI. Delete or leave unused the old `flux-system` HTTPS Secret once you are sure nothing references it. Force reconcile again.

7. Progress Log: path chosen (A/B), cutover window acknowledged, `url` + `secretRef` pair, revoke time, reconcile proof.

**Reflect:** Why is “update Secret, then later update URL” unsafe even if each step looks correct in isolation?

### 6.2.5 Challenge — credential blast radius

Document what the bootstrap token could have done if it had been `repo` write + org admin. Contrast that with the read-only deploy key now in use. Note the difference between **bootstrap** (writes Flux config once) and **reconcile** (reads desired state forever).

### 6.2.6 Verify

You can name the Git path Flux watches (`clusters/harbour-local`), show controllers healthy, and show that ongoing Git access is **read-only** after the handoff — with the bootstrap token already revoked.

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
    harbour-api-prod.yaml
```

Base is **namespace-agnostic**. Overlays set `namespace:` and own the Namespace object. Staging and prod each get their **own** Flux Kustomization (§6.4) so promotion is a real second environment, not a Git-only fiction.

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
              path: /ready
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

**Probe contract (carries forward from D03):**

| Probe | Endpoint | Meaning |
| --- | --- | --- |
| Liveness | `GET /health` | Process is up — restart if this fails |
| Readiness | `GET /ready` | Dependencies usable — remove from Service endpoints if this fails |

On kind **without** `DATABASE_HOST`, Harbour’s `/ready` still returns ready with `database: "unconfigured"` (D03). That is intentional for a DB-free local cluster: readiness means “app accepts traffic; no DB was configured,” **not** “Postgres was verified.” When you attach a database later, keep `/ready` as the readiness probe so a failing dependency stops traffic without restart-looping the process.

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
# Registry promotion (D04/D05) — replace images: with digest pin (§6.5.3 pull auth if private):
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
curl -sS http://127.0.0.1:8080/ready
```

Then delete and let Flux own the same path later (`kubectl delete -k ...` after Flux is ready), so you do not dual-own.

### 6.3.6 Practice — reproduce

Add a staging-only patch that sets `replicas: 3`. Show `kubectl kustomize` staging ≠ prod.

### 6.3.7 Verify

Base uses `/ready` for readiness and `/health` for liveness, plus resources; overlays only change env-specific image/namespace (and intentional patches). No Secret values in Git.

---

## Section 6.4 — Point Flux at Harbour staging and prod

### 6.4.1 Worked example — Flux Kustomizations (both environments)

Prefer generating objects with the CLI and **committing** the YAML under `clusters/harbour-local/`, so Git remains the source of truth for controller config too. Create **two** Kustomizations — staging and prod — so promotion later changes a live reconciled environment, not only a Git file.

```bash
# Reuse the GitRepository bootstrap created (often named flux-system):
flux create kustomization harbour-api-staging \
  --namespace=flux-system \
  --source=GitRepository/flux-system \
  --path=./deploy/harbour-api/overlays/staging \
  --prune=true \
  --interval=1m \
  --wait=true \
  --timeout=3m \
  --export > clusters/harbour-local/harbour-api-staging.yaml

flux create kustomization harbour-api-prod \
  --namespace=flux-system \
  --source=GitRepository/flux-system \
  --path=./deploy/harbour-api/overlays/prod \
  --prune=true \
  --interval=1m \
  --wait=true \
  --timeout=3m \
  --export > clusters/harbour-local/harbour-api-prod.yaml

git add clusters/harbour-local/harbour-api-staging.yaml \
        clusters/harbour-local/harbour-api-prod.yaml
git commit -m "gitops: reconcile harbour-api staging and prod"
git push
```

If your bootstrap root already recursively applies `clusters/harbour-local/`, pushing is enough. Otherwise apply once:

```bash
kubectl apply -f clusters/harbour-local/harbour-api-staging.yaml
kubectl apply -f clusters/harbour-local/harbour-api-prod.yaml
```

Example shape for staging (prod is identical except `name` and `path`):

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

Reconcile and exercise **both** namespaces:

```bash
flux reconcile source git flux-system -n flux-system
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
flux reconcile kustomization harbour-api-prod -n flux-system --with-source
flux get kustomizations -A
kubectl -n harbour-staging get deploy,pods,svc
kubectl -n harbour-prod get deploy,pods,svc
kubectl -n harbour-staging port-forward svc/harbour-api 8080:80 &
sleep 2
curl -sS http://127.0.0.1:8080/health
curl -sS http://127.0.0.1:8080/ready
# Optional: second forward on 8081 for prod
kubectl -n harbour-prod port-forward svc/harbour-api 8081:80 &
sleep 2
curl -sS http://127.0.0.1:8081/ready
```

**Expected:** Both Kustomizations Ready=True; pods Ready in `harbour-staging` and `harbour-prod`; `/health` and `/ready` succeed.

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

`flux get kustomizations` lists **both** `harbour-api-staging` and `harbour-api-prod` with paths that match Git; you did not leave a long-lived `kubectl apply -k` dual path.

---

## Section 6.5 — Promote the same digest via Git

### 6.5.1 Concept

Promotion is a **reviewed change to desired state**, not a new CI deploy job with cluster credentials.

| Actor | Allowed |
| --- | --- |
| D04 release | Publish image `@sha256:…` + evidence |
| Human / bot PR | Update overlay `images:` to that digest |
| Flux | Pull and reconcile **each** env Kustomization |
| CI with cluster-admin | Not required for promotion |

### 6.5.2 Image pull paths — local load vs registry

| Path | How the node gets the bits | Auth needed in-cluster? |
| --- | --- | --- |
| `kind load docker-image` + `harbour-api:local` / `:good` | Image already on the kind node | No |
| Public digest (e.g. disposable public training image) | kubelet pulls anonymously | No |
| Private ECR / GHCR digest | kubelet pulls with credentials | **Yes** — `imagePullSecrets` (or equivalent node/IRSA pattern on cloud) |

Docker CLI login on your laptop does **not** transfer to the kind kubelet. If you pin a private registry digest without pull credentials, expect `ImagePullBackOff`.

**Training default for this chapter:** keep using `kind load` + retags for the promotion drill (§6.5.4), **or** use a public disposable image digest if you want a true pull. Treat private ECR/GHCR as an explicit extension (§6.5.3).

### 6.5.3 Worked example — private registry pull (when you leave kind-load)

Only needed when overlays reference a **private** `newName` + `digest`. Prefer short-lived credentials and document rotation.

```bash
# Example: GHCR (PAT with read:packages) or ECR password from aws ecr get-login-password
export REGISTRY_SERVER="ghcr.io"          # or ACCOUNT.dkr.ecr.REGION.amazonaws.com
export REGISTRY_USER="<username-or-AWS>"
export REGISTRY_PASSWORD="<short-lived-token>"

for NS in harbour-staging harbour-prod; do
  kubectl -n "$NS" create secret docker-registry harbour-regcred \
    --docker-server="${REGISTRY_SERVER}" \
    --docker-username="${REGISTRY_USER}" \
    --docker-password="${REGISTRY_PASSWORD}" \
    --dry-run=client -o yaml | kubectl apply -f -
done
# Do not commit the Secret YAML with the password embedded.
```

Patch the Deployment (base or overlay) so pods use it:

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
        - name: harbour-regcred
```

**Rotation:** recreate the Secret when the token expires; force a rollout if pulls start failing. On EKS you would prefer IRSA / node roles over long-lived PATs — note that as the production direction; kind still needs an explicit Secret for private pulls.

**Alternative:** pin a **public** training image digest so pull auth is unnecessary, and keep Harbour digests for when the registry and cluster share a real auth path.

### 6.5.4 Worked example — promote between two reconciled environments (kind-load)

Complete sequence: change staging → verify cluster → promote **same** reference to prod → verify prod cluster.

```bash
cd "$HARBOUR_ROOT"
git switch main   # or the branch Flux tracks — confirm: flux get sources git
docker tag harbour-api:local harbour-api:good
kind load docker-image harbour-api:good --name harbour

# 1) Staging PR / commit: set images newTag: good (or digest if using a registry)
git switch -c promote/staging-good
# edit deploy/harbour-api/overlays/staging/kustomization.yaml images:
git add deploy/harbour-api/overlays/staging
git commit -m "deploy(staging): pin harbour-api:good"
STAGING_SHA="$(git rev-parse HEAD)"
git push -u origin HEAD
# Merge via PR (or merge locally on a personal training repo), then:
git switch main && git pull

flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging rollout status deploy/harbour-api
STAGING_IMG="$(kubectl -n harbour-staging get pods -o jsonpath='{.items[0].status.containerStatuses[0].image}{"\n"}')"
echo "staging sha=${STAGING_SHA} image=${STAGING_IMG}"

# 2) Prod PR: same image reference — separate approval
git switch -c promote/prod-good
# copy the same images: block into deploy/harbour-api/overlays/prod/kustomization.yaml
git add deploy/harbour-api/overlays/prod
git commit -m "deploy(prod): promote harbour-api:good (same artifact as staging)"
PROD_SHA="$(git rev-parse HEAD)"
git push -u origin HEAD
# Merge, then:
git switch main && git pull

flux reconcile kustomization harbour-api-prod -n flux-system --with-source
kubectl -n harbour-prod rollout status deploy/harbour-api
PROD_IMG="$(kubectl -n harbour-prod get pods -o jsonpath='{.items[0].status.containerStatuses[0].image}{"\n"}')"
echo "prod sha=${PROD_SHA} image=${PROD_IMG}"
test "$STAGING_IMG" = "$PROD_IMG" && echo "promotion: same running image in both envs"
```

Example CODEOWNERS for the second PR:

```text
# .github/CODEOWNERS
/deploy/harbour-api/overlays/prod/  @your-user
```

**Registry variant:** replace `newTag: good` with `newName` + `digest: sha256:…` from D04 evidence, ensure §6.5.3 pull auth (or a public digest), and compare `imageID` instead of the short image name:

```bash
kubectl -n harbour-staging get pods -o jsonpath='{.items[0].status.containerStatuses[0].imageID}{"\n"}'
kubectl -n harbour-prod get pods -o jsonpath='{.items[0].status.containerStatuses[0].imageID}{"\n"}'
```

### 6.5.5 Optional — CI updates desired state (still no cluster-admin)

A release workflow may open a PR that only changes `deploy/**/kustomization.yaml` image fields (or use Flux Image Automation Controllers). That bot needs **contents** permission on the desired-state path — **not** a kubeconfig. Keep required status checks honest about path filters (lesson from D04).

### 6.5.6 Practice — reproduce

Record staging commit SHA, prod commit SHA, and both namespaces’ `image` / `imageID` in the Progress Log. Confirm `harbour-api-prod` reconciled — not only that the prod overlay file changed.

### 6.5.7 Verify

Checklist: promotion is a Git change; **both** Flux Kustomizations reconciled; running images match across envs; CI did not need `kubectl apply` to app namespaces; private pulls (if used) had `imagePullSecrets` or an equivalent documented path.

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

### 6.7.1 Worked example — ship a broken desired state (record the SHA)

Do this on the branch Flux tracks (usually `main`) so reconcile and revert stay aligned. Record the **bad commit SHA** explicitly — do not rely on `HEAD` after merges or branch switches.

```bash
cd "$HARBOUR_ROOT"
FLUX_BRANCH="$(kubectl -n flux-system get gitrepository flux-system \
  -o jsonpath='{.spec.ref.branch}{"\n"}')"
FLUX_BRANCH="${FLUX_BRANCH:-main}"
echo "Flux tracks branch: ${FLUX_BRANCH}"

git fetch origin
git switch "${FLUX_BRANCH}"
git pull --ff-only origin "${FLUX_BRANCH}"

git switch -c demo/bad-rollout
# In staging overlay, set newTag: missing-tag (or a digest that does not exist)
git add deploy/harbour-api/overlays/staging
git commit -m "demo: broken harbour image for rollback drill"
BAD_SHA="$(git rev-parse HEAD)"
echo "BAD_SHA=${BAD_SHA}"   # copy into Progress Log now
git push -u origin demo/bad-rollout
```

Merge into the Flux branch with a **merge commit** or fast-forward (either is fine if you keep `BAD_SHA`):

```bash
git switch "${FLUX_BRANCH}"
git merge --no-ff demo/bad-rollout -m "Merge demo/bad-rollout for rollback drill"
MERGE_SHA="$(git rev-parse HEAD)"
git push origin "${FLUX_BRANCH}"
echo "MERGE_SHA=${MERGE_SHA} BAD_SHA=${BAD_SHA}"
```

```bash
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging get pods
kubectl -n harbour-staging get events --sort-by=.lastTimestamp | tail -n 30
flux get kustomizations harbour-api-staging -n flux-system
```

**Expected:** Pods fail to become Ready (ImagePullBackOff / invalid image); Flux may report health wait failures.

**Investigation order:** Flux Kustomization status → ReplicaSet/Pod events → image pull errors → probes → controller logs.

### 6.7.2 Worked example — recover by reverting the recorded bad commit

Stay on the Flux-tracked branch. Revert **`${BAD_SHA}`**, not a guessed `HEAD`.

```bash
git switch "${FLUX_BRANCH}"
git pull --ff-only origin "${FLUX_BRANCH}"

# Ordinary commit (the demo/bad-rollout tip):
git revert "${BAD_SHA}" --no-edit

# If instead you must revert a merge commit (MERGE_SHA), Git needs the mainline parent:
#   git revert -m 1 "${MERGE_SHA}" --no-edit
# -m 1 means "keep the first parent" (the Flux branch before the merge) and undo the merged side.
# Prefer reverting BAD_SHA when the bad change is a single ordinary commit — clearer history.

REVERT_SHA="$(git rev-parse HEAD)"
echo "REVERT_SHA=${REVERT_SHA} undoes BAD_SHA=${BAD_SHA}"
git push origin "${FLUX_BRANCH}"

flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging rollout status deploy/harbour-api
curl -sS http://127.0.0.1:8080/health
curl -sS http://127.0.0.1:8080/ready
```

**Expected:** Known-good image returns; pods Ready; recovery is a Git commit (`REVERT_SHA`), not `kubectl delete pod` folklore.

**Complete sequence evidence (required):** `BAD_SHA` → failing pods/events → `REVERT_SHA` → Ready pods + `/ready` OK.

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

Write three investigation bullets you actually used (events, pods, flux). Include `BAD_SHA`, `REVERT_SHA`, and the Flux branch name. Confirm you did **not** run a blind `git revert HEAD` after switching branches.

### 6.7.6 Challenge

Suspend Flux, “fix” live with kubectl, resume, and watch Git overwrite you. Document the lesson in the Progress Log.

### 6.7.7 Verify

Known-good image is running; Git history shows bad commit + revert of **that** SHA; cluster health matches Git; no secret credential was pasted into chat or commits.

---

## Section 6.8 — Day-two operations

### 6.8.1 Worked example — pod kill and client impact

```bash
# Terminal A — client loop (Service reachability; /ready matches readiness semantics)
while true; do curl -sf http://127.0.0.1:8080/ready || echo FAIL; sleep 0.2; done

# Terminal B — kill
POD="$(kubectl -n harbour-staging get pod -l app=harbour-api -o jsonpath='{.items[0].metadata.name}')"
kubectl -n harbour-staging delete pod "$POD"
kubectl -n harbour-staging get pods -w
```

Pod replacement ≠ zero downtime. With `replicas: 2` and readiness probes, record whether Terminal A printed `FAIL`. That observation belongs in the assessment evidence.

### 6.8.2 Worked example — metrics-server on kind, then HPA

kind does not ship metrics-server. Install it, patch kubelet TLS for kind, **confirm CPU metrics**, then add the HPA.

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# kind’s kubelet serves a self-signed cert — metrics-server must allow it (training only):
kubectl -n kube-system patch deployment metrics-server --type='json' -p='[
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"},
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname"}
]'

kubectl -n kube-system rollout status deploy/metrics-server
# Wait until metrics API answers (may take ~30–60s):
kubectl top nodes
kubectl -n harbour-staging top pods
```

**Expected:** `kubectl top` shows CPU/memory columns with numbers (not an metrics API error). If `top` still fails, fix metrics-server before claiming autoscaling evidence.

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
          averageUtilization: 50
```

Add `- hpa.yaml` under staging `resources:`. Commit and reconcile.

**Two different claims — keep them separate:**

| Claim | What proves it | What does **not** prove it |
| --- | --- | --- |
| **HPA configured** | Object exists; `TARGETS` shows a **numeric** CPU % (not `<unknown>`); scaleTargetRef points at `harbour-api` | HTTP load that barely moves CPU |
| **Scale-out demonstrated** | `REPLICAS` rises above `minReplicas` under load you caused, with `kubectl top` showing elevated CPU | Configuring the HPA alone |

```bash
flux reconcile kustomization harbour-api-staging -n flux-system --with-source
kubectl -n harbour-staging get hpa harbour-api
kubectl -n harbour-staging describe hpa harbour-api
# Competent bar for "HPA configured": TARGETS is numeric, e.g. 2%/50% — not <unknown>
```

**Optional HTTP load (may not scale):** Harbour’s `/health` is cheap. A busybox wget loop is fine for traffic/churn experiments but often **will not** drive CPU to the HPA threshold. Treat scale-out here as best-effort only.

```bash
kubectl -n harbour-staging run loadgen-http --rm -it --restart=Never --image=busybox:1.36 -- \
  /bin/sh -c 'while true; do wget -q -O- http://harbour-api/health >/dev/null; done'
```

**Controlled CPU load (prefer this to demonstrate scale-out):** burn CPU **inside** a Harbour pod so metrics-server sees utilisation on the HPA’s scale target. Training only — delete when done.

```bash
# Record baseline:
kubectl -n harbour-staging get deploy harbour-api -o jsonpath='replicas={.status.replicas}{"\n"}'
kubectl -n harbour-staging get hpa harbour-api

POD="$(kubectl -n harbour-staging get pod -l app=harbour-api -o jsonpath='{.items[0].metadata.name}')"
# Stress one replica's CPU (python is in the Harbour image from D03):
kubectl -n harbour-staging exec -it "$POD" -- python -c '
import multiprocessing as mp, time
def burn():
    while True:
        x = 0
        for i in range(10_000_000):
            x += i
if __name__ == "__main__":
    procs = [mp.Process(target=burn) for _ in range(2)]
    for p in procs: p.start()
    time.sleep(180)
    for p in procs: p.terminate()
'

# While that runs (second terminal):
kubectl -n harbour-staging top pods
kubectl -n harbour-staging get hpa harbour-api -w
```

**Expected for scale-out evidence:** `kubectl top` shows the stressed pod’s CPU clearly elevated; HPA `TARGETS` climbs; `REPLICAS` increases (allow a minute or two for the HPA sync period). Record baseline replicas, peak replicas, and a `top` sample. If replicas never move, say so honestly — you still pass **HPA configured** with numeric targets; mark **scale-out demonstrated** only when replicas actually rose.

When finished, delete any leftover loadgen pods and let the HPA (or a reconcile) return replicas toward `minReplicas`.

`--kubelet-insecure-tls` is a **kind training** compromise. Do not carry it into a production cluster hardening story without justification.

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

Install Argo into kind per current upstream getting-started; point **two** Applications at `deploy/harbour-api/overlays/staging` and `.../prod`. Assessment evidence is the same: Git desired state, digest promotion across both apps, drift, Git rollback of a recorded SHA, day-two notes.

---

## Section 6.11 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Kustomization not Ready | Bad path / YAML / auth | `flux get` message; `kubectl kustomize` locally |
| ImagePullBackOff | Missing on node, private registry, or bad digest | `kind load` vs `imagePullSecrets`; events; never assume laptop `docker login` applies |
| CrashLoopBackOff | App/config error | logs; probes too aggressive? |
| Remains drifted | Suspended or no reconcile | `flux get`; resume |
| Prune deleted shared object | Ownership mistake | ADR; restore from TF/Git carefully |
| HPA unknown metrics | No metrics-server | `kubectl top`; install/fix metrics |

---

## Practical Assessment — Chapter 6 — controlled release and recovery

Align with [D06 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) and Final Project Checklist D06.

### Required deliverables

1. GitOps controller on an isolated cluster with clear Git path and RBAC/secret boundaries (bootstrap credential handed off to read-only access, then revoked).
2. Two env overlays (staging/prod) with immutable image references (digest or documented local tag policy), each reconciled by its own Flux/Argo object.
3. Reviewed promotion of the **same** artifact between envs via Git, with **both** environments verified running that image after reconcile.
4. Broken-release drill with diagnosis and **Git** rollback of a **recorded** bad commit SHA (not a blind `revert HEAD`).
5. Drift drill with reconcile or documented non-auto policy.
6. Pod kill / HPA experiment evaluated against client-facing behaviour. Separate evidence: **HPA configured** (numeric targets via metrics-server) vs **scale-out demonstrated** (replicas rose under controlled CPU load — not assumed from HTTP wget alone).
7. Runbook covering rollout failure, secrets and data assumptions; image-pull auth path documented if private registries were used.

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

- Does Flux/Argo show the same image Git declares in **staging and prod**?
- Can you promote without cluster creds in CI?
- Did rollback revert the recorded `BAD_SHA` on the Flux-tracked branch?
- Are secrets absent from the repo? Did Secret + GitRepository URL agree during cutover, and was the bootstrap token revoked only after the new identity reconciled?
- Is prune scoped safely? Is the kind runtime vs D05 ECS platform difference clear in your ADR?
- Does the runbook admit what Git revert cannot fix?

### Example assessment conclusion (evidence still required)

> kind cluster `harbour` (not the D05 ECS service) runs Flux against staging and prod overlays. Bootstrap PAT → read-only path: HTTPS RO token swap (or atomic SSH URL+secretRef cutover with known_hosts); verified Ready; then PAT revoked. Promotion PRs pinned the same `harbour-api:good` (or digest) in both envs; both Kustomizations reconciled to matching images. `BAD_SHA` … was reverted as `REVERT_SHA` …; `/ready` recovered. Manual scale drift self-healed. Pod kill showed brief client errors with two replicas. HPA configured (numeric targets); scale-out demonstrated with in-pod CPU burn (replicas 2→N). Runbook committed. Terraform remains out of the Deployment ownership path.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Deploy a new digest | PR to overlay `images:` | `kubectl set image` as permanent fix |
| Debug sync | `flux get`, controller logs, events | Only deleting pods |
| Handle drift | Reconcile or suspend with ticket | Silent console edits |
| Roll back | `git revert ${BAD_SHA}` on the Flux branch | Blind `git revert HEAD` after merges |
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
| imagePullSecrets | Pod credentials for private registry pulls (independent of laptop `docker login`) |
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
