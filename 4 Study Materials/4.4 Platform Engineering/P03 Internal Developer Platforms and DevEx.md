# Chapter 3 — Internal Developer Platforms and Developer Experience (P03)

*Platform Engineering textbook · Chapter 3 of 4*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [P03 course detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) (about 32–40 hours, plus time to recruit and observe a trial user). |
| **Prerequisites** | [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) and [P02](P02%20Kubernetes%20Administration%20and%20Operations.md) (Harbour as sound Kubernetes workloads with day-2 operations). [D04](../4.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md), [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) and [D07](../4.1%20DevOps/D07%20Observability.md) strongly recommended; the Cloud path ([C03](../4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md)) is preferred but not required for the kind-based labs. AI optional. |
| **Status** | Authored; remediations after audits through `fbd5030` (YAML quota/PSA Pod dry-run, init-probe split) — **awaiting re-review (not signed off)** |

## How to study this chapter

This is the most important module in the programme. Everything before it makes Harbour *work*. P03 asks the only question that matters to a platform: **can somebody who did not build it use it, safely, without you?**

The common failure is to confuse a platform with its front-end. Installing Backstage (or Port, or a wiki) produces a website. It does not produce a platform. A platform is a **product**: it has users, the users have jobs to do, and it succeeds only when those jobs get measurably easier and safer. A developer portal is one possible interface to a platform. It is never the evidence that the platform works.

> **The standard this chapter teaches (read this twice):** Give a developer who has **not** built Harbour the written docs and the approved interface. They must **create a new service, follow the delivery path, understand operational status and investigate a failure** — with **no undocumented help from the platform author**. You measure stuck points, interventions and independent completion time. If the trial fails, the platform fails; you fix the platform and the docs, then run another trial.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. §3.1–§3.7 build the product, the golden path, the self-service guardrails and the measurement protocol. §3.8 runs the independent trial that decides whether any of it counts; §3.9 covers operating the platform afterwards. The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) P03 bar is: *a trial user stands up a service from the golden path **without 1:1 help** beyond written docs; capture their feedback.*

> **Safety and honesty boundary:** Use fabricated data and a disposable cluster (kind, from D06). Never ask a trial participant to use real credentials. Do not publish names or recordings of participants without consent; record roles ("backend developer, 3 years") instead. Treat a trial of **one** person as qualitative evidence, not a statistically valid result — say so in your write-up.

### Learning outcomes

1. Describe the platform as a product: users, jobs-to-be-done, golden path, success metrics and non-goals.
2. Reduce a developer's cognitive load by designing a golden path with explicit contracts (what the platform owns, what the developer owns).
3. Build a service template and safe self-service workflow that produce a deployable Harbour-compatible service.
4. Make services discoverable (catalogue, ownership, docs, runbooks, status) without depending on a portal product.
5. Write documentation a stranger can follow, and test it as you would test code.
6. Run a controlled usability trial; measure stuck points, interventions and independent completion time.
7. Turn trial findings into platform changes and re-test; define adoption metrics honestly.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"

for cmd in git kubectl kind flux docker python3; do
  command -v "$cmd" >/dev/null || { echo "Missing: $cmd (see D03/D06/P01)"; exit 1; }
done
test -d deploy/harbour-api/base || { echo "Complete D06 (deploy/harbour-api) first"; exit 1; }
test -f .github/workflows/python-validate.yml || {
  echo "Need the reusable validate workflow from D04 §4.7"; exit 1; }
kubectl config current-context | grep -q "kind-" || {
  echo "Expected a kind context (disposable cluster). Aborting."; exit 1; }

mkdir -p platform/{bin,templates,policy,tenants} \
         docs/platform/trials docs/services catalog services
```

You need a working Harbour (D03–D06) and a kind cluster running Flux. If you cannot find a trial participant yet, you can complete §3.1–§3.7 now; **do not** tick the P03 checklist row until §3.8 has run with a real second person.

---

## Section 3.1 — Platform as a product

### 3.1.1 Concept: a platform has customers

A platform team that ships tools without studying users builds what engineers call a *ticket queue with extra steps*. Product thinking asks four questions before any code:

| Question | Platform answer for Harbour |
| --- | --- |
| **Who** are the users? | Application developers who write services but are not Kubernetes, Terraform or observability specialists |
| **What job** are they hiring the platform for? | "Get a new service from idea to a running, observable, recoverable deployment this afternoon, without learning every underlying tool" |
| **How do we know it works?** | Measured by *their* outcomes (time, interventions, completion), not our activity (features shipped) |
| **What will we *not* do?** | Non-goals, written down, so scope does not drift into a commercial PaaS |

### 3.1.2 Users and jobs-to-be-done

Write down real personas, not marketing ones. Each persona should be someone you could recruit.

| Persona | Context | Job-to-be-done (JTBD) | Fears |
| --- | --- | --- | --- |
| **Priya — product developer** | Strong Python, little Kubernetes | "When I start a new service, I want a safe default that deploys, so I can ship my feature instead of YAML." | Breaking prod; asking "stupid" questions |
| **Marcus — on-call developer** | Owns services, paged occasionally | "When my service misbehaves at 2 a.m., I want to see what is wrong and the first safe action, without waking the platform team." | Opaque dashboards; missing runbooks |
| **Sam — reviewer / tech lead** | Approves changes | "I want to approve a change knowing the platform already checked the basics." | Rubber-stamping unreviewable diffs |
| **You — platform engineer** | Builds and supports it | "I want fewer interrupts and a platform that improves from evidence." | Becoming a human API |

JTBD statements follow the form: **When** *(situation)*, **I want** *(motivation)*, **so I can** *(outcome)*. A feature that serves no JTBD is a candidate for deletion.

### 3.1.3 Worked example — the platform product brief

Create `docs/platform/PRODUCT.md` (about one page):

```markdown
# Harbour platform — product brief (version 1)
## Users
Primary: product developers who can write a Python API but have not operated Kubernetes.
Secondary: on-call developers, reviewers.
## Jobs-to-be-done
J1 Create a deployable, observable service by default. J2 Ship a reviewed change to an approved
environment without cluster admin. J3 See whether my service is healthy and what changed.
J4 Investigate a failure and take the first safe action using only documented steps.
## Golden path (summary) and interface decision
Template → reviewed change → trusted build (digest) → promotion by PR → GitOps deploy → health,
telemetry, runbook. Approved interface for v1: `platform/bin/*` CLI + repository docs.
## Non-goals (v1)
No custom build system or DSL; no production traffic or real data; not mandatory (escape hatch).
## Success metrics
Independent completion of J1–J4 by a user who did not build Harbour (yes/no); independent
completion time; undocumented interventions (must be 0); stuck points; golden-path ÷ total services.
## Known limitations
Single-author platform; tiny trial samples; kind is not production.
```

### 3.1.4 Success metrics: measure the user's outcome

| Metric | Definition | Why it matters | Trap |
| --- | --- | --- | --- |
| **Independent completion time** | Wall-clock minutes from "task card handed over" to "acceptance check passes", excluding documented waits (e.g. CI) | Primary DevEx signal | Rewarding speed that hides unsafe shortcuts |
| **Intervention count** | Times the observer gave information that is **not already in the written docs** | Pass/fail honesty test (§3.8) | Counting only "big" hints |
| **Stuck points** | Moments the user paused > 2 min, reversed, or searched without progress | Where the product is confusing | Treating stuck points as user error |
| **Time to first deploy (TTFD)** | New service created → first healthy pod | Onboarding speed | Ignoring second-service speed (learning effect) |
| **Cognitive load rating** | One question after each task: "How mentally demanding was that?" (1–7) | Subjective but comparable | Using it as proof alone |
| **Adoption** | Services using the golden path ÷ services in catalogue | Only meaningful when use is voluntary | Mandating use then calling it adoption |
| **Change failure / recovery** | Failed promotions and time to recover (borrow from DORA, but see limits) | Safety of self-service | Gaming by not deploying |

**Honest limits:** with a trial of one or two people you can find *problems*, not estimate *rates*. Report counts and quotes, not percentages that imply precision you do not have.

### 3.1.5 Why a portal alone is not sufficient

| What you installed | What it proves | What it does *not* prove |
| --- | --- | --- |
| Backstage / Port / Cortex running | A web app is up | That anyone can create a deployable service |
| Software templates configured | A form submits | That the output builds, passes policy, deploys and is observable |
| A catalogue populated | Entities exist | That owners, runbooks and status are correct |
| Beautiful docs site | Pages exist | That a stranger can follow them without help |
| Positive internal demo | The author can drive it | Anything about independent use |

**Rule for this programme:** a portal, CLI, repo template or README is an **interface**. The evidence is a trial (§3.8), not a screenshot. You may build a portal if you wish (§3.5.5 compares options), but the checklist is satisfied only by independent completion.

**Practice — decide:** In `docs/platform/PRODUCT.md` add a one-paragraph "interface decision" stating which interface is *approved* for v1 (for example: the `platform/bin/harbour-new-service` CLI plus repository docs) and why. Trial users will be told to use only that interface and the docs.

**Verify:** A reader can state your users, four jobs, three non-goals, and the exact pass/fail trial standard without asking you.

---

## Section 3.2 — Cognitive load and the golden path

### 3.2.1 Concept: reduce load, do not hide it

Cognitive load comes in three kinds: **intrinsic** (the problem is hard), **extraneous** (the tooling makes it harder than it needs to be) and **germane** (effort that builds useful understanding). Platforms exist to cut *extraneous* load: ten YAML dialects, five dashboards, unwritten rules.

A **golden path** (a "paved road") is the opinionated, supported, *easiest* way to do a common job. It is **not** a cage:

| Property | Meaning |
| --- | --- |
| **Opinionated** | One default for language, packaging, deploy and observability |
| **Complete** | Covers create → build → deploy → operate, not just scaffolding |
| **Supported** | The platform team fixes it when it breaks |
| **Optional but attractive** | Leaving the path is allowed; you then own more (escape hatch) |
| **Understandable** | Developers can see *what* the path did and *why* (no magic they cannot inspect) |

### 3.2.2 The platform contract: who owns what

| Concern | Platform owns | Developer owns |
| --- | --- | --- |
| Namespace, quota, deployer identity | ✔ (tenant manifest, policy) | Chooses service name and owner |
| Build pipeline and artifact signing/provenance | ✔ (reusable workflows) | Writes code and tests |
| Deploy mechanism (GitOps) | ✔ | Decides *when* to promote |
| Probes, resource limits, security context defaults | ✔ (template) | Tunes values within limits |
| Telemetry plumbing, dashboard template | ✔ | Adds business metrics, keeps runbook current |
| Incident first response for the service | Support route and docs | Service-specific diagnosis and fixes |
| Data durability for stateful services | Patterns and guidance only | Backup choices and restore tests (see P04 §4.6) |

Write this table into `docs/platform/golden-path.md`. A contract nobody wrote down is an assumption.

### 3.2.3 Worked example — golden path specification

`docs/platform/golden-path.md`:

```markdown
# Golden path — new Harbour service (v1)

Audience: a developer who has never seen Harbour internals.
Time budget: first service in under 90 minutes (target to be validated by trial).

## Prerequisites (one-time)
1. Tools installed: git, docker, python 3.12, kubectl, flux (versions in docs/platform/START-HERE.md).
2. Access: read access to the Harbour repo; fork or branch permission; read-only kube
   context named `harbour-dev` (provided by the platform — see START-HERE §Access).

## Steps
1. Create: `platform/bin/harbour-new-service <name> --owner <handle>`
2. Review: open a pull request. Required checks: validate, policy. Reviewer approves.
3. Build: merge to main → release workflow publishes `image@sha256:…`.
4. Promote: `platform/bin/harbour-promote <name> staging <digest>` → pull request → merge.
5. Observe: `platform/bin/harbour-status <name>` and the service README links.
6. Investigate: follow services/<name>/RUNBOOK.md ("Symptoms" table).

## Done means
- Pod Ready in `<name>-staging`
- `harbour-status <name>` reports HEALTHY
- Catalogue lists the service with an owner and a runbook link

## Not covered (v1)
Production promotion, stateful dependencies, custom domains. See "Escape hatch".

## Escape hatch
If the path blocks a legitimate need, open an issue labelled `platform-gap`
with what you tried. You may deviate; record it in the service README
("Deviations") and accept that support is best-effort.
```

### 3.2.4 Onboarding: the first 30 minutes

Onboarding is where most platforms lose users. Create `docs/platform/START-HERE.md` as the *only* entry point. It must contain, in this order:

1. What the platform does for you (three sentences) and what it will not do.
2. A **tool checklist** with exact versions and a one-line verification command each.
3. **Access** — how a new developer obtains the read-only kube context, repo permission and registry access, *including who approves it and the expected wait* (a documented wait is fine; an unwritten one is a defect).
4. A **"hello" smoke test** that proves the environment before touching the platform (`kubectl --context harbour-dev get ns`).
5. Link to the golden path and the "I'm stuck" page.

**Practice — reproduce:** On a clean user account (or container) follow START-HERE verbatim. Every command you must improvise is a defect; fix the doc, not your memory.

**Verify:** START-HERE has no step that requires knowing something only the author knows (private URLs, undocumented environment variables, "ask me for the token").

---

## Section 3.3 — The service template

### 3.3.1 Concept: a template is a product artefact

A template that generates code is easy. A template that generates a service which **builds, passes policy, deploys, reports health, has a runbook and appears in the catalogue** is the golden path. Test the template exactly as you would test an application (§3.3.4).

Design rules:

- **Generate only what the developer would otherwise copy-paste.** Keep generated files short and readable.
- **Platform-owned logic lives outside the generated service** (reusable workflows, shared base manifests) so fixes propagate. Generated code *calls* it.
- **Everything generated is inspectable plain files.** No hidden state.
- **Fail early with helpful errors** (naming rules, missing owner).

### 3.3.2 Layout

```text
services/<name>/                 # application + tests + Dockerfile
deploy/<name>/base/              # Deployment, Service (defaults from template)
deploy/<name>/overlays/staging/  # digest pin (platform/bin/harbour-promote edits this)
platform/tenants/<name>/         # namespace, quota, deployer identity, Flux object
catalog/<name>.yaml              # catalogue entry (owner, lifecycle, links)
docs/services/<name>/{README.md,RUNBOOK.md}
.github/workflows/<name>-validate.yml
.github/workflows/<name>-release.yml
```

This monorepo layout matches Harbour (D01). A repo-per-service variant is valid; it trades simpler permissions for harder platform-wide changes. Record the choice in an ADR (P04 §4.2).

### 3.3.3 Worked example — the scaffold CLI

First, the platform-owned **reusable release workflow** (extended with provenance and SBOM in P04 §4.4). `.github/workflows/service-release.yml`:

```yaml
name: service-release
on:
  workflow_call:
    inputs:
      service: {required: true, type: string}
    outputs:
      digest: {description: Registry digest of the pushed image, value: "${{ jobs.release.outputs.digest }}"}
permissions:
  contents: read
jobs:
  release:
    runs-on: ubuntu-latest
    permissions: {contents: read, packages: write}
    outputs:
      digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      - id: meta
        run: |
          OWNER_LC='${{ github.repository_owner }}'
          echo "image=ghcr.io/${OWNER_LC,,}/${{ inputs.service }}" >> "$GITHUB_OUTPUT"
      - uses: docker/login-action@v3
        with: {registry: ghcr.io, username: "${{ github.actor }}", password: "${{ secrets.GITHUB_TOKEN }}"}
      - uses: docker/setup-buildx-action@v3
      - id: push
        uses: docker/build-push-action@v6
        with:
          context: services/${{ inputs.service }}
          push: true
          tags: ${{ steps.meta.outputs.image }}:${{ github.sha }}
      - name: Summary (what a developer copies next)
        run: |
          echo "digest: \`${{ steps.push.outputs.digest }}\` — next: \`platform/bin/harbour-promote ${{ inputs.service }} staging ${{ steps.push.outputs.digest }}\`" >> "$GITHUB_STEP_SUMMARY"
```

Notice the **next step is printed where the developer is already looking**. Good platforms put the next action at the point of need.

Now `platform/bin/harbour-new-service` (chmod +x). It is deliberately plain Bash with heredocs so you can read exactly what it generates:

```bash
#!/usr/bin/env bash
set -euo pipefail
usage() { echo "usage: harbour-new-service <name> --owner <handle>" >&2; exit 2; }
NAME="${1:-}"; [ -n "$NAME" ] || usage; shift
OWNER=""
while [ $# -gt 0 ]; do
  case "$1" in --owner) OWNER="${2:?--owner needs a value}"; shift 2 ;; *) usage ;; esac
done
# DNS-label safe: start and end alphanumeric (no trailing hyphen). Enforce length 3–31 separately.
[[ "$NAME" =~ ^[a-z]([a-z0-9-]*[a-z0-9])?$ ]] || {
  echo "ERROR: name must be DNS-label safe (lowercase, digits, hyphens; start/end alphanumeric)." >&2; exit 1; }
(( ${#NAME} >= 3 && ${#NAME} <= 31 )) || {
  echo "ERROR: name length must be 3–31 (got ${#NAME})." >&2; exit 1; }
[ -n "$OWNER" ] || { echo "ERROR: --owner required (who reviews and is contacted?)." >&2; exit 1; }
[[ "$OWNER" =~ ^[a-z0-9][a-z0-9._-]{0,38}$ ]] || {
  echo "ERROR: --owner must be a safe handle for YAML/docs (alphanumeric, ._-)." >&2; exit 1; }
cd "$(git rev-parse --show-toplevel)"
[ ! -e "services/$NAME" ] || { echo "ERROR: services/$NAME already exists." >&2; exit 1; }
NS="${NAME}-staging"
GH_OWNER="$(git config --get remote.origin.url | sed -E 's#.*[:/]([^/]+)/[^/]+$#\1#' | tr 'A-Z' 'a-z')"
IMG="ghcr.io/$GH_OWNER/$NAME"
mkdir -p "services/$NAME" "deploy/$NAME/base" "deploy/$NAME/overlays/staging" \
         "platform/tenants/$NAME" "docs/services/$NAME" catalog

# --- application: small, readable, tested --------------------------------
cat > "services/$NAME/main.py" <<EOF
from fastapi import FastAPI

app = FastAPI(title="$NAME")


@app.get("/health")  # liveness: the process is up
def health():
    return {"status": "ok", "service": "$NAME"}


@app.get("/ready")  # readiness: safe to receive traffic (add dependency checks here)
def ready():
    return {"status": "ready", "service": "$NAME"}
EOF
cat > "services/$NAME/test_main.py" <<EOF
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_and_ready():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").status_code == 200
EOF
printf '%s\n' fastapi==0.115.6 uvicorn==0.32.1 httpx==0.28.1 pytest==8.3.4 > "services/$NAME/requirements.txt"
cat > "services/$NAME/Dockerfile" <<'EOF'
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --uid 10001 --create-home app
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
USER 10001
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# --- deploy: secure defaults come from the template, not from memory ------
cat > "deploy/$NAME/base/deployment.yaml" <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NAME
  labels: {app: $NAME, app.kubernetes.io/part-of: harbour, platform.harbour/owner: "$OWNER"}
spec:
  replicas: 2
  selector: {matchLabels: {app: $NAME}}
  template:
    metadata: {labels: {app: $NAME}}
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: $NAME
          image: $IMG
          ports: [{name: http, containerPort: 8000}]
          readinessProbe: {httpGet: {path: /ready, port: http}, periodSeconds: 5}
          livenessProbe: {httpGet: {path: /health, port: http}, initialDelaySeconds: 10, periodSeconds: 10}
          # Must satisfy tenant PSA enforce=restricted (drop ALL — same bar as P01/P04).
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: [ALL]}
          resources:
            requests: {cpu: 50m, memory: 64Mi}
            limits: {memory: 128Mi}   # CPU limit optional (P01/P04 platform policy)
          volumeMounts: [{name: tmp, mountPath: /tmp}]
      volumes: [{name: tmp, emptyDir: {}}]
---
apiVersion: v1
kind: Service
metadata: {name: $NAME, labels: {app: $NAME}}
spec:
  selector: {app: $NAME}
  ports: [{name: http, port: 80, targetPort: http}]
EOF
printf '%s\n' "apiVersion: kustomize.config.k8s.io/v1beta1" "kind: Kustomization" \
  "resources: [deployment.yaml]" > "deploy/$NAME/base/kustomization.yaml"
cat > "deploy/$NAME/overlays/staging/kustomization.yaml" <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: $NS
resources: [../../base]
replicas: [{name: $NAME, count: 0}]  # UNPROMOTED-REPLICAS (harbour-promote removes this line)
images:
  - name: $IMG
    newName: $IMG
    digest: sha256:0000000000000000000000000000000000000000000000000000000000000000  # UNPROMOTED
EOF

# --- tenant: what the platform grants this service ------------------------
# Reconciled by the platform-owned Kustomization (§3.4.4), not by the developer.
cat > "platform/tenants/$NAME/tenant.yaml" <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $NS
  labels:
    platform.harbour/service: $NAME
    platform.harbour/env: staging
    # Inherit P02 security baseline — namespace alone is not isolation.
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: v1
kind: ResourceQuota
metadata: {name: default, namespace: $NS}
# CPU limits are optional (P01/P02 ADR). Do NOT put a CPU-limit quota key in
# hard: — without a LimitRange, that would force every container to declare a
# CPU limit, and Pods would stall Pending forever.
spec: {hard: {pods: "6", requests.cpu: "500m", requests.memory: 512Mi, limits.memory: 1Gi}}
---
apiVersion: v1
kind: ServiceAccount
metadata: {name: reconciler, namespace: $NS}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: {name: reconciler, namespace: $NS}
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: admin}
subjects: [{kind: ServiceAccount, name: reconciler, namespace: $NS}]
---
# Platform-default NetworkPolicies (same contract as P02 harbour-staging).
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: default-deny-all, namespace: $NS}
spec: {podSelector: {}, policyTypes: [Ingress, Egress]}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: allow-dns-egress, namespace: $NS}
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: kube-system}}
          podSelector: {matchLabels: {k8s-app: kube-dns}}
      ports: [{protocol: UDP, port: 53}, {protocol: TCP, port: 53}]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: ${NAME}-ingress, namespace: $NS}
spec:
  podSelector: {matchLabels: {app: $NAME}}
  policyTypes: [Ingress]
  ingress:
    - from: [{podSelector: {matchLabels: {app: probe-client}}}]
      ports: [{protocol: TCP, port: 8000}]
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata: {name: $NAME, namespace: $NS}
spec:
  interval: 1m
  sourceRef: {kind: GitRepository, name: flux-system, namespace: flux-system}
  path: ./deploy/$NAME/overlays/staging
  prune: true
  wait: true
  timeout: 3m
  serviceAccountName: reconciler
EOF
# Post-provision proof (run after Flux reconciles the tenant):
#   platform/bin/harbour-check-service $NAME --allow-unpromoted
# must confirm PSA labels + default-deny exist — not merely that the namespace was created.

# --- discoverability + docs ----------------------------------------------
cat > "catalog/$NAME.yaml" <<EOF
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: $NAME
  description: Harbour golden-path service
spec:
  type: service
  lifecycle: experimental
  owner: $OWNER
  system: harbour
EOF
cat > "docs/services/$NAME/README.md" <<EOF
# $NAME
Owner: $OWNER · golden path v1 · status: \`platform/bin/harbour-status $NAME\` · [runbook](RUNBOOK.md)
Tests: \`cd services/$NAME && pip install -r requirements.txt && pytest -q\`
## Deviations from the golden path
None.
EOF
cat > "docs/services/$NAME/RUNBOOK.md" <<EOF
# $NAME runbook
Start: \`platform/bin/harbour-status $NAME\` — read the verdict and "Next step".

| Symptom | Likely cause | First safe action |
| --- | --- | --- |
| Pods not Ready; events show failing readiness probe | Faulty release | Promote the previous digest by pull request (see docs/releases/promotion-log.md) |
| \`ImagePullBackOff\` | Digest missing or registry access | Confirm the digest exists; promote a known-good one |
| Status UNKNOWN | No read access / not deployed yet | START-HERE §Access; golden path step 4 |

Escalate: issue labelled \`platform-support\`. Never edit live objects; Git is the source of truth.
EOF

# --- CI: thin callers of platform-owned workflows --------------------------
cat > ".github/workflows/$NAME-validate.yml" <<EOF
name: $NAME-validate
on:
  pull_request:
  push:
    branches: ["main"]
permissions:
  contents: read
jobs:
  test:
    uses: ./.github/workflows/python-validate.yml
    with:
      working-directory: services/$NAME
EOF
cat > ".github/workflows/$NAME-release.yml" <<EOF
name: $NAME-release
on:
  # Reviewed history only: push to the protected branch after merge.
  # Do NOT enable workflow_dispatch here — a manually selected branch can attest
  # an unmerged commit, and P04 promotion requires that attested source ∈ main.
  push:
    branches: ["main"]
    paths: ["services/$NAME/**"]
permissions:
  contents: read
  packages: write
  id-token: write
  attestations: write
jobs:
  release:
    uses: ./.github/workflows/service-release.yml
    with:
      service: $NAME
EOF
echo "Created $NAME. Next: platform/bin/harbour-check-service $NAME --allow-unpromoted, then open a pull request."
```

> **Registry access (decide and document):** kind must be able to pull `ghcr.io/<owner>/<service>@sha256:…`. Either make training packages public (fabricated sample code only) or provision an image pull secret per tenant (D06 §6.5.3). (If you keep the P01 local registry instead, CI cannot push to it — then your release step is a documented local script, and the trial must still cover it.) If you choose neither, the trial participant will hit `ImagePullBackOff` at T2 and you will have failed your own docs. Write the choice into START-HERE.

**Read it critically.** The generated validate workflow has **no path filter** (so the required check always reports, per D04 §4.3.4); the release workflow *does*, because it is not a required check. Release is **push-to-`main` only** — no `workflow_dispatch` — so attestations bind to reviewed history. The unpromoted digest is a visible sentinel, not a silent bug.

### 3.3.4 Test the template like software

A template that has never been generated in CI will rot. Split **offline** (unprivileged PR CI) from **cluster** (disposable kind lab):

**`platform/bin/test-template` — offline / required PR check** (no cluster credentials):

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
T="tpl-smoke-$$"
trap 'rm -rf "services/$T" "deploy/$T" "platform/tenants/$T" "docs/services/$T" "catalog/$T.yaml" \
  ".github/workflows/$T-validate.yml" ".github/workflows/$T-release.yml"' EXIT
platform/bin/harbour-new-service "$T" --owner template-test
( cd "services/$T" && python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt && pytest -q )
kubectl kustomize "deploy/$T/overlays/staging" >/dev/null
# Structural securityContext (YAML-aware — not a fragile single-line grep).
platform/bin/harbour-check-service "$T" --allow-unpromoted
echo "template OK (offline)"
```

**`platform/bin/test-template-admission` — lab / disposable cluster only** (not a required PR check). PSA enforce applies to **Pods**, not Deployments — extract the Pod template and dry-run a real Pod:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
T="${1:?usage: test-template-admission <generated-service-name>}"
NS="psa-probe-$T"
kubectl create namespace "$NS" --dry-run=client -o yaml \
  | kubectl label --local -f - \
      pod-security.kubernetes.io/enforce=restricted \
      pod-security.kubernetes.io/enforce-version=latest -o yaml \
  | kubectl apply -f -
# Build a Pod from the Deployment template (PSA evaluates Pod admission).
kubectl kustomize "deploy/$T/overlays/staging" | python3 - "$NS" <<'PY' \
  | kubectl apply --dry-run=server -f -
import sys, yaml, copy
ns = sys.argv[1]
docs = list(yaml.safe_load_all(sys.stdin))
dep = next(d for d in docs if d and d.get("kind") == "Deployment")
pod = {
  "apiVersion": "v1",
  "kind": "Pod",
  "metadata": {
    "name": f"{dep['metadata']['name']}-psa",
    "namespace": ns,
    "labels": copy.deepcopy(dep["spec"]["template"].get("metadata", {}).get("labels") or {}),
  },
  "spec": copy.deepcopy(dep["spec"]["template"]["spec"]),
}
pod["spec"]["restartPolicy"] = "Never"
yaml.safe_dump(pod, sys.stdout)
PY
# Negative: privileged Pod must be rejected by restricted PSA.
set +e
kubectl -n "$NS" apply --dry-run=server -f - <<'EOF' 2>/tmp/psa-deny.txt
apiVersion: v1
kind: Pod
metadata: {name: psa-bad}
spec:
  containers:
    - name: c
      image: busybox@sha256:0000000000000000000000000000000000000000000000000000000000000001
      command: ["sleep", "1"]
      securityContext: {privileged: true}
EOF
rc=$?; set -e
[ "$rc" -ne 0 ] || { echo "FAIL: privileged Pod was admitted under restricted PSA"; exit 1; }
grep -qiE 'privileged|pod security|violat' /tmp/psa-deny.txt \
  || { echo "FAIL: rejection was not PSA (got: $(cat /tmp/psa-deny.txt))"; exit 1; }
kubectl delete namespace "$NS" --wait=false
echo "template OK (Pod PSA dry-run + privileged denial)"
```

Wire `test-template` into a workflow on every change to `platform/` or the reusable workflows. Run `test-template-admission` on kind after Flux is up. (`.venv/` must be gitignored.) **Verify:** offline passes; breaking the template fails; valid Pod dry-run passes; privileged Pod is rejected.

**Practice — reproduce:** Generate `hello-docs`, run its tests and `kubectl kustomize` its staging overlay. **Challenge:** resist adding a `--db` flag; write down why stateful services are *not* in v1 (P04 §4.6 shows the cost of getting this wrong).

---

## Section 3.4 — Safe self-service

### 3.4.1 Concept: self-service is guardrails, not freedom

Self-service means a developer completes the job **without waiting for a human to run a command for them**, inside limits the platform enforces. The limits are the product:

| Guardrail | Enforced by | Developer sees |
| --- | --- | --- |
| Naming and ownership rules | Scaffold CLI + policy check | A clear error with the fix |
| Quota and defaults per namespace | Tenant manifest (ResourceQuota) | "Quota exceeded: pods 6/6" |
| No mutable tags, digest only | `harbour-promote` + `harbour-check-service` + (P04) admission policy | Rejection naming the rule |
| No cluster-admin for developers | RBAC; Flux reconciles via a namespaced identity (P04 §4.5) | Read-only status; changes via pull request |
| Review before change | Branch protection + CODEOWNERS (D01) | Required reviewer and checks |
| Secrets never in Git | Secret scanning + documented secret path | Blocked push or documented alternative |

**Documented human gates are acceptable.** If creating a tenant namespace needs a platform reviewer, that is a *designed* step. Record it with an expected response time in the golden path and measure the wait (§3.7). What fails the trial is an **undocumented** human step.

### 3.4.2 Worked example — promotion by pull request

`platform/bin/harbour-promote` changes **one** file, validates its input and leaves merge to review:

```bash
#!/usr/bin/env bash
set -euo pipefail
usage() { echo "usage: harbour-promote <service> <env> <sha256:digest>" >&2; exit 2; }
[ $# -eq 3 ] || usage
NAME="$1"; ENV="$2"; DIGEST="$3"
cd "$(git rev-parse --show-toplevel)"
case "$ENV" in staging) ;; *) echo "ERROR: env '$ENV' not self-service in v1 (allowed: staging)." >&2; exit 1 ;; esac
[[ "$DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]] || {
  echo "ERROR: expected sha256:<64 hex>. Copy the digest from the release run summary, not a tag." >&2; exit 1; }
F="deploy/$NAME/overlays/$ENV/kustomization.yaml"
[ -f "$F" ] || { echo "ERROR: $F not found. Did you create the service?" >&2; exit 1; }
PREV="$(sed -nE 's/^[[:space:]]+digest:[[:space:]]+(sha256:[0-9a-f]{64}).*/\1/p' "$F")"
sed -i -E "s#(digest:[[:space:]]+)sha256:[0-9a-f]{64}.*#\1$DIGEST#" "$F"
sed -i '/UNPROMOTED-REPLICAS/d' "$F"   # first promotion switches the service on (replicas from base)
mkdir -p docs/releases
printf '%s %s %s previous=%s new=%s\n' "$(date -u +%FT%TZ)" "$NAME" "$ENV" "${PREV:-none}" "$DIGEST" \
  >> docs/releases/promotion-log.md
echo "Updated $F (previous: ${PREV:-none})."
echo "Required next (P04): download the release-manifest artifact for this digest into"
echo "  docs/releases/$NAME/$DIGEST.json  (from the release workflow run),"
echo "then: git checkout -b promote/$NAME-$ENV && git add -A &&"
echo "  git commit -m 'promote($ENV): $NAME $DIGEST' && open a pull request."
```

Note what it does **not** do: it does not run `kubectl`, hold cluster credentials, push to `main`, or invent a release manifest. P04 `promotion-verify` requires the CI-produced `docs/releases/<svc>/<digest>.json` in the same PR (download the Actions artifact from the release run that built that digest). The cluster changes only when review merges and Flux reconciles (D06).

### 3.4.3 Worked example — the policy check

`platform/bin/harbour-check-service` is a *training-scale* conformance check. It uses simple rendered-manifest assertions; P04 §4.5 replaces the manifest checks with real policy-as-code (Kyverno) that also runs at admission.

```bash
#!/usr/bin/env bash
set -euo pipefail
NAME="${1:?usage: harbour-check-service <name> [--allow-unpromoted]}"
ALLOW="${2:-}"
cd "$(git rev-parse --show-toplevel)"
fail=0
bad() { echo "FAIL: $*"; fail=1; }
for f in "services/$NAME/Dockerfile" "services/$NAME/test_main.py" "catalog/$NAME.yaml" \
         "docs/services/$NAME/README.md" "docs/services/$NAME/RUNBOOK.md" \
         "platform/tenants/$NAME/tenant.yaml"; do
  [ -f "$f" ] || bad "missing $f"
done
grep -qE '^  owner: .+' "catalog/$NAME.yaml" || bad "catalog: owner missing"
R="$(kubectl kustomize "deploy/$NAME/overlays/staging")" || { echo "FAIL: kustomize build"; exit 1; }
# Structural YAML parse — do not grep multiline securityContext fields.
printf '%s\n' "$R" | python3 -c '
import sys, yaml
allow = sys.argv[1]
docs = list(yaml.safe_load_all(sys.stdin))
deploys = [d for d in docs if d and d.get("kind") == "Deployment"]
if not deploys:
    print("FAIL: no Deployment in rendered overlay"); sys.exit(1)
SENTINEL = "sha256:0000000000000000000000000000000000000000000000000000000000000000"

def check_container(c, *, require_probes):
    name = c.get("name", "?")
    img = c.get("image", "")
    if ":latest" in img.split("@")[0]:
        print(f"FAIL: container {name} uses :latest"); sys.exit(1)
    if "@sha256:" not in img:
        print(f"FAIL: container {name} image not digest-pinned: {img}"); sys.exit(1)
    digest = img.rsplit("@", 1)[-1]
    if digest == SENTINEL and allow != "--allow-unpromoted":
        print(f"FAIL: container {name} still has UNPROMOTED sentinel digest"); sys.exit(1)
    sc = c.get("securityContext") or {}
    if sc.get("allowPrivilegeEscalation") is not False:
        print(f"FAIL: container {name} missing allowPrivilegeEscalation: false"); sys.exit(1)
    drop = [str(x) for x in ((sc.get("capabilities") or {}).get("drop") or [])]
    if "ALL" not in drop:
        print(f"FAIL: container {name} capabilities.drop missing ALL (got {drop})"); sys.exit(1)
    res = c.get("resources") or {}
    if "memory" not in (res.get("limits") or {}):
        print(f"FAIL: container {name} missing memory limit"); sys.exit(1)
    req = res.get("requests") or {}
    if "cpu" not in req or "memory" not in req:
        print(f"FAIL: container {name} missing cpu/memory requests"); sys.exit(1)
    if require_probes:
        if not c.get("readinessProbe"):
            print(f"FAIL: container {name} missing readinessProbe"); sys.exit(1)
        if not c.get("livenessProbe"):
            print(f"FAIL: container {name} missing livenessProbe"); sys.exit(1)

for d in deploys:
    spec = d["spec"]["template"]["spec"]
    psc = spec.get("securityContext") or {}
    if psc.get("runAsNonRoot") is not True:
        print("FAIL: pod runAsNonRoot != true"); sys.exit(1)
    for c in (spec.get("containers") or []):
        check_container(c, require_probes=True)
    # Init containers share the security/resource bar but do not use app probes.
    for c in (spec.get("initContainers") or []):
        check_container(c, require_probes=False)
print("OK: structural Deployment security/resources")
' "$ALLOW" || bad "structural Deployment/securityContext check failed"
# Manifest contract (always — before merge): PSA + NetPol + quota keys via YAML (not comment grep).
TENANT="platform/tenants/$NAME/tenant.yaml"
grep -q 'pod-security.kubernetes.io/enforce: restricted' "$TENANT" || bad "tenant manifest missing PSA enforce=restricted"
grep -q 'name: default-deny-all' "$TENANT" || bad "tenant manifest missing default-deny-all"
python3 - "$TENANT" <<'PY' || bad "tenant ResourceQuota inspect failed"
import sys, yaml
from pathlib import Path
docs = list(yaml.safe_load_all(Path(sys.argv[1]).read_text()))
quotas = [d for d in docs if d and d.get("kind") == "ResourceQuota"]
if not quotas:
    print("FAIL: no ResourceQuota in tenant manifest"); sys.exit(1)
for q in quotas:
    hard = (q.get("spec") or {}).get("hard") or {}
    # Keys may be strings like "limits.cpu" — inspect the hard map, ignore comments.
    if "limits.cpu" in hard:
        print(f"FAIL: ResourceQuota {q.get('metadata',{}).get('name')} sets hard[limits.cpu]={hard['limits.cpu']}")
        sys.exit(1)
print("OK: ResourceQuota has no hard limits.cpu")
PY
# Effective-policy test (after Flux reconciles) — required post-deploy; object existence alone is not isolation.
TENANT_NS="$NAME-staging"
if [ "${HARBOUR_CHECK_EFFECTIVE:-0}" = "1" ]; then
  kubectl get ns "$TENANT_NS" >/dev/null 2>&1 || bad "effective check requested but namespace $TENANT_NS missing"
  kubectl get ns "$TENANT_NS" -o jsonpath='{.metadata.labels.pod-security\.kubernetes\.io/enforce}{"\n"}' \
    | grep -qx 'restricted' || bad "live namespace missing PSA enforce=restricted"
  kubectl -n "$TENANT_NS" get networkpolicy default-deny-all >/dev/null 2>&1 \
    || bad "live namespace missing default-deny-all"
  # Reuse P02 connectivity matrix (allow probe, deny lateral) — CNI enforcement, not YAML presence.
  NS="$TENANT_NS" ./deploy/platform/staging/test-connectivity.sh "$TENANT_NS" \
    || bad "connectivity matrix failed (CNI may not enforce NetworkPolicy)"
fi
[ "$fail" -eq 0 ] && echo "OK: $NAME conforms to golden path v1" || exit 1
```

Wire offline checks into the required PR `policy` job (P04 `.github/workflows/policy.yml`). After reconcile: `HARBOUR_CHECK_EFFECTIVE=1 platform/bin/harbour-check-service "$NAME"`.

### 3.4.4 One-time platform wiring (author task, documented)

Two pieces are set up **once** by the platform owner, before any developer arrives. Both are part of the documented platform, not hidden help:

```bash
# (a) The platform-owned Kustomization that reconciles every tenant folder with
#     cluster-level rights. Developers can only add tenant files via reviewed PRs
#     (CODEOWNERS: platform/tenants/ requires the platform reviewer).
flux create kustomization platform-tenants \
  --namespace=flux-system --source=GitRepository/flux-system \
  --path=./platform/tenants --prune=true --interval=1m \
  --export > clusters/harbour-local/platform-tenants.yaml
git add clusters/harbour-local/platform-tenants.yaml
git commit -m "platform: reconcile tenant manifests"; git push

# (b) A read-only developer identity (token is short-lived, delivered out of band, never committed).
kubectl create namespace platform-system --dry-run=client -o yaml | kubectl apply -f -
kubectl -n platform-system create serviceaccount dev-viewer --dry-run=client -o yaml | kubectl apply -f -
kubectl create clusterrole harbour-dev-extra-read --verb=get,list --resource=namespaces \
  --resource=kustomizations.kustomize.toolkit.fluxcd.io --dry-run=client -o yaml | kubectl apply -f -
for r in view harbour-dev-extra-read; do
  kubectl create clusterrolebinding "harbour-dev-$r" --clusterrole="$r" \
    --serviceaccount=platform-system:dev-viewer --dry-run=client -o yaml | kubectl apply -f -
done
kubectl -n platform-system create token dev-viewer --duration=8h
```

START-HERE §Access must tell the developer how to turn that token into a `harbour-dev` context (`kubectl config set-credentials`, `set-context`) **with exact commands**, and who to ask for a token plus the expected wait.

**Honest limits:** `view` is read-only but spans all namespaces except Secrets. That is acceptable on a training kind cluster; a real platform would scope developers to their own namespaces (P04 §4.5 tightens this). The tenant `admin` RoleBinding gives Flux's per-tenant identity rights **only inside its namespace**; it cannot create namespaces or cluster-scoped objects.

### 3.4.5 Escape hatch and exceptions

A path with no exit gets abandoned or worked around quietly. Define:

- **Deviation record** — in the service README: what, why, who owns the consequence.
- **Exception expiry** — deviations are reviewed (for example quarterly).
- **Platform gap issues** — every deviation is also a product signal.

**Verify:** From a fresh branch, run the scaffold, then `harbour-check-service <name> --allow-unpromoted`. Then deliberately remove the readiness probe and confirm the check fails with a message a developer could act on.

---

## Section 3.5 — Discoverability: catalogue, docs and ownership

### 3.5.1 Concept: if it cannot be found, it does not exist

Developers need to answer, without asking a person: *What services exist? Who owns this one? Where is its runbook? Is it healthy? How do I make a new one?* A catalogue answers these. A catalogue is data first (files in Git), interface second (portal, page or CLI).

### 3.5.2 Worked example — a catalogue as files

The scaffold already writes `catalog/<name>.yaml` in a Backstage-compatible shape, so a portal can ingest it later without migration. Generate a human-readable index with `platform/bin/harbour-catalog`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
{ echo "# Service catalogue (generated — do not edit)"; echo
  echo "| Service | Owner | Lifecycle | Runbook |"; echo "| --- | --- | --- | --- |"
  for f in catalog/*.yaml; do [ -e "$f" ] || continue
    printf '| %s | %s | %s | [runbook](../services/%s/RUNBOOK.md) |\n' \
      "$(awk '/^  name:/{print $2;exit}' "$f")" "$(awk '/^  owner:/{print $2;exit}' "$f")" \
      "$(awk '/^  lifecycle:/{print $2;exit}' "$f")" "$(awk '/^  name:/{print $2;exit}' "$f")"
  done; } > docs/platform/CATALOG.md
```

Run it in CI and fail the build when `CATALOG.md` is stale (`git diff --exit-code docs/platform/CATALOG.md`). Add Harbour's own `harbour-api` entry by hand so the catalogue is not empty.

### 3.5.3 Documentation as part of the product

Organise by the reader's need ([Diátaxis](https://diataxis.fr/)): **tutorial** (START-HERE → first service), **how-to** (promote, roll back, read status), **reference** (contract, quotas, allowed environments), **explanation** (ADRs, golden-path rationale). For a stranger audience:

1. Every command is copy-pasteable and states expected output; no assumed repository root, cluster context or account.
2. Errors are documented next to the step that causes them.
3. Accessibility basics: descriptive headings and link text, alt text, no meaning conveyed by colour alone, text equivalents for diagrams. (A basic checklist is not an accessibility audit — say so.)
4. Docs are tested: link-check in CI, and the trial (§3.8) as the real test.

### 3.5.4 Worked example — operational status a developer can read

Developers should not need `kubectl` fluency to answer "is it healthy?". `platform/bin/harbour-status` turns cluster facts into a verdict plus the next step. It uses read-only commands.

```bash
#!/usr/bin/env bash
set -euo pipefail
NAME="${1:?usage: harbour-status <service> [env]}"; ENV="${2:-staging}"; NS="$NAME-$ENV"
k() { kubectl --request-timeout=10s "$@"; }
if ! k get ns "$NS" >/dev/null 2>&1; then
  echo "VERDICT: UNKNOWN — namespace $NS not visible."
  echo "Next step: not deployed yet? Golden path step 4 (promote). No access? START-HERE §Access."
  exit 4
fi
read -r DESIRED READY <<<"$(k -n "$NS" get deploy "$NAME" -o jsonpath='{.spec.replicas} {.status.readyReplicas}' 2>/dev/null || echo '0 0')"
READY="${READY:-0}"; DESIRED="${DESIRED:-0}"
FLUX_READY="$(k -n "$NS" get kustomization "$NAME" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo n/a)"
echo "service:  $NAME ($ENV)"
echo "image:    $(k -n "$NS" get deploy "$NAME" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo n/a)"
echo "replicas: ready $READY / desired $DESIRED"
echo "gitops:   Ready=$FLUX_READY"
echo "recent events:"; k -n "$NS" get events --sort-by=.lastTimestamp 2>/dev/null | tail -n 5 | sed 's/^/  /'
# Exit codes: 0=HEALTHY (app+Flux), 2=DEGRADED, 3=DOWN, 4=UNKNOWN, 5=PARTIAL (app Ready, Flux missing/not Ready).
if [ "$READY" = "$DESIRED" ] && [ "$DESIRED" != "0" ]; then
  if [ "$FLUX_READY" = "True" ]; then
    echo "VERDICT: HEALTHY"
    exit 0
  fi
  echo "VERDICT: PARTIAL — replicas Ready but Flux evidence is '$FLUX_READY' (not True)."
  echo "Next step: kubectl -n $NS get kustomization $NAME -o yaml; do not treat this as unqualified HEALTHY."
  exit 5
elif [ "$READY" != "0" ]; then
  echo "VERDICT: DEGRADED — some replicas not ready."
  echo "Next step: docs/services/$NAME/RUNBOOK.md, row 'Pods not Ready'. Read the events above."
  exit 2
else
  echo "VERDICT: DOWN — no ready replicas."
  echo "Next step: docs/services/$NAME/RUNBOOK.md; if the last promotion caused it, promote the previous digest."
  exit 3
fi
```

**Contract:** Missing Flux (`n/a`) is **PARTIAL** (exit 5), never unqualified HEALTHY. CI must check `$?`.

**Limitations:** reports Kubernetes + Flux Ready, not user-journey health.

### 3.5.5 Portal options (decide with evidence)

| Option | Strength | Cost | Use when |
| --- | --- | --- | --- |
| Repo docs + CLI + generated catalogue | Cheap, versioned, testable | Less discoverable, no UI | First iteration; one-person platform |
| Backstage | Rich catalogue, templates, plugins | Heavy build/upgrade burden | Many teams, dedicated platform capacity |
| Hosted portals (Port, Cortex, OpsLevel) | Fast start | Cost, lock-in | UI needed quickly; vendor review done |

**Decision test:** *would a portal remove a stuck point you observed in a trial?* No trial yet means you do not know what to build. Record ADR `docs/decisions/0305-portal-decision.md`, including the evidence that would change your mind.

---

## Section 3.6 — Investigability: the developer's failure path

### 3.6.1 Concept

Marcus is paged. He did not build the platform. Within minutes he must find out *what is wrong* and *the first safe action*. The platform supplies: a standard status command, per-service runbooks, linked telemetry (D07), and safe rollback (promote the previous digest).

### 3.6.2 Plant a failure the stranger will investigate

For the trial (§3.8) you need a repeatable, **safe** failure that a developer can diagnose from docs only. Two good options:

| Failure | How to plant | What the user should find |
| --- | --- | --- |
| **Bad release** | Promote a digest whose `/ready` fails (e.g. build variant with `FAIL_READY=1`) | Pods running but not Ready; events show failing readiness probe; runbook row "Pods Ready? No" → roll back by promoting previous digest |
| **Missing image** | Promote a syntactically valid but nonexistent digest | `ImagePullBackOff`; runbook row for image pull errors |

Do **not** tell the participant the cause. The runbook table must be sufficient for them to reach the recovery action. Keep a "failure card" (author-only) with the injection command, expected symptoms, expected diagnosis and expected recovery.

**Runbook quality bar:**

- Starts with a command that produces a verdict (`harbour-status`).
- Symptoms in the *user's* words, not internal jargon.
- First safe action is reversible (re-promote a previous digest), never "edit the live Deployment".
- States when to stop and escalate.

**Verify:** A colleague (not the participant) can reach the correct recovery for each planted failure using only the runbook. Fix gaps now; each one would otherwise cost you a failed trial.

---

## Section 3.7 — Measuring the platform

### 3.7.1 The measurement protocol

Define everything *before* the trial so you cannot reinterpret afterwards.

| Item | Definition |
| --- | --- |
| **Start time** | Participant is handed the task card and the docs link |
| **Stop time** | The task's acceptance check passes (observer verifies), or the participant gives up, or the time-box (e.g. 3 hours) expires |
| **Documented waits** | CI runtime, review wait. Recorded separately and **subtracted** from independent time |
| **Stuck point** | Paused > 2 min, backtracked, or searched without progress. Record timestamp, what they were trying, which doc they were reading |
| **Intervention** | The observer says or shows anything not already in the written docs |
| **Doc pointer (not an intervention)** | Observer says only "the docs are at X" *when the participant asked where docs are* and START-HERE did not say. Log it as a **docs defect**. |
| **Independent completion time** | Stop − start − documented waits, counted only if there were **zero undocumented interventions** |

**Intervention classes** (record each):

| Class | Example | Effect on trial |
| --- | --- | --- |
| **I0** | Observer silent | Pass-eligible |
| **I1** | Observer repeats information that is verbatim in the docs | Docs-findability defect; trial still pass-eligible, logged |
| **I2** | Observer provides information **not** in docs (hint, command, URL, "try restarting") | **Trial fails.** Fix docs/product, run a new trial |
| **I3** | Observer takes the keyboard or fixes something | **Trial fails.** |

If you answer a question "just once", that is I2. The rule exists because the author is not present in real usage.

### 3.7.2 Worked example — trial record template

`docs/platform/trials/TRIAL-TEMPLATE.md`:

```markdown
# Trial NNN — golden path

| | |
| --- | --- |
| Date | |
| Participant role (anonymised) | e.g. backend developer, 3 yrs, no Kubernetes |
| Has seen Harbour internals before? | No (required) |
| Docs version (commit) | |
| Interface used | `platform/bin/harbour-new-service` + repository docs |
| Observer | |
| Environment | fresh clone / clean user; kind context `harbour-dev` |

## Tasks (pass/fail each)
| # | Task | Start | Stop | Pass? | Documented wait (min) | Cognitive load (1–7) |
| T1 | Create a new service from the golden path | | | | | |
| T2 | Deliver it: PR → checks → merge → build → promote → running in staging | | | | | |
| T3 | Read operational status and state whether it is healthy and why | | | | | |
| T4 | Investigate the planted failure and recover using the runbook | | | | | |

## Stuck points
| Time | Task | What they tried | Doc consulted | Root cause (doc / tool / concept) | Ticket |
| --- | --- | --- | --- | --- | --- |

## Interventions
| Time | Class (I1/I2/I3) | What was said or done | Which doc should have contained it |
| --- | --- | --- | --- |

## Result
- Interventions I2/I3: N → **PASS / FAIL**
- Independent completion time (excl. documented waits): __ min
- Stuck points: N
- Participant quotes (consented):
- What would have made this easier? (their words)

## Findings and actions
| ID | Severity | Finding | Fix | Owner | Re-test needed |
```

### 3.7.3 Adoption metrics (after the first pass)

Track: golden-path services ÷ catalogue services (meaningful only if use is **voluntary**); deviation count and age (product gaps); `platform-support` requests by category (docs defect vs bug vs missing feature); and time to a *second* service after a break (learning curve). Avoid vanity metrics: number of templates, portal page views, lines of YAML generated.

**Practice — reproduce:** Complete the trial template with a *rehearsal* run on yourself. Mark it clearly **REHEARSAL — author, not eligible**. Notice how many stuck points you cannot even *see* because you know the system. That is why the author cannot be the trial user.

**Verify:** Metric definitions are written before trial 1 and not edited afterwards except to correct typos (changes are logged).

---

## Section 3.8 — Run the independent trial

### 3.8.1 Who qualifies as a trial participant

| Participant | Eligible? | Note |
| --- | --- | --- |
| A developer who has **never** built or contributed to Harbour | **Yes** | Colleague, friend, community peer, another learner on this programme |
| A programme peer who studied DevOps/Cloud but not **your** Harbour | **Yes** | Ideal: knows tools, not your platform |
| You, after a cooling-off period | **No** | Still knows the system. Rehearsal only |
| An AI assistant "playing" a developer | **No** for the checklist | Optional additional signal (§3.8.5); it is not a person's experience |
| Someone who watched you build it | **No** | Contaminated |
| A person who has seen only the *docs* | Yes | That is the point |

If you cannot recruit anyone, leave the P03 checklist row **unticked** (`☐`) and record "trial pending". Do not substitute rehearsal for the trial.

### 3.8.2 Setup (do this the day before)

Author-side preflight — a clean clone must satisfy START-HERE and the template test must pass:

```bash
set -euo pipefail
T="$(mktemp -d)"
git clone --depth 1 "$(git -C "$HARBOUR_ROOT" config --get remote.origin.url)" "$T/harbour"
( cd "$T/harbour" && platform/bin/test-template )
rm -rf "$T"
kubectl --context harbour-dev get ns   # the participant's read-only context works
```

Then prepare: (1) a **fresh workspace** (new OS user, container or VM; no author dotfiles, tokens or shell history); (2) **access provisioned** exactly as START-HERE says (say so in the record if you must pre-grant); (3) the **task cards** below plus the repository link and START-HERE — nothing else; (4) the planted failure ready but **not applied until T4**, its failure card kept by the observer; (5) **consent**: what is recorded, that *the platform is being tested, not them*, and that they may stop at any time.

### 3.8.3 Task cards

```text
TASK CARD — Harbour platform trial

You are a developer on a team that uses the Harbour platform. You have the repository
link and docs/platform/START-HERE.md. The platform owner will not answer questions
about how things work (they are observing, not helping). If something is unclear,
note it aloud — that is useful feedback. Use only the documented interface.

T1  Create a new service named "trial-<yourinitials>" with yourself as owner.
    Done when: your service passes its tests locally.

T2  Get the service running in the staging environment through the normal
    delivery path. Done when: the platform reports your service as healthy.

T3  Tell us what state the service is in and how you know. Where would you look
    first if someone asked you, "is it okay?"

T4  A change has been released that the team suspects is faulty. Find out what is
    wrong and put the service back into a working state. Explain your reasoning.
```

### 3.8.4 Observer rules (the hardest part)

1. **Say nothing** except the scripted prompts (start, end, "please think aloud").
2. If asked a question: reply **"I can't help — what do the docs say?"** and log it as a stuck point. **If you then answer, it is an intervention (I2).**
3. Never touch their keyboard (I3).
4. Record timestamps in the template as you go; do not reconstruct afterwards.
5. If the participant is blocked for more than 15 minutes on one step, you may end the task as **FAIL (blocked)** — that is a valid, valuable result. Do **not** rescue them and call it a pass.
6. At the end, run the **acceptance checks yourself** (not the participant's word): service listed in the catalogue; `harbour-status <name>` = HEALTHY; promotion-log entry; recovery action traceable to a pull request.
7. Debrief: three questions — *What was most confusing? What would you remove? Would you use this voluntarily?* Capture verbatim quotes with consent.

Example acceptance verification (observer):

```bash
NAME=trial-xx
git log --oneline -n 5 -- "services/$NAME" "deploy/$NAME" | cat
grep -q "$NAME" docs/platform/CATALOG.md && echo "catalogued"
platform/bin/harbour-status "$NAME" | tail -n 1
tail -n 3 docs/releases/promotion-log.md
```

### 3.8.5 Pass standard and what to do when it fails

| Result | Meaning | Action |
| --- | --- | --- |
| **PASS** | All four tasks complete; **no I2/I3 interventions**; findings recorded | Tick checklist P03 (see Practical Assessment); still triage stuck points |
| **FAIL (intervention)** | You had to give undocumented help | Convert each I2/I3 into a doc/product fix; **recruit a new participant** (the first now knows the answers) |
| **FAIL (blocked)** | Participant could not proceed | Same as above; the stuck point is the finding |
| **INVALID** | Participant had prior Harbour knowledge, or setup leaked author context | Discard as evidence; record why |

**Why a new participant:** a returning participant benefits from learning; you would be measuring recall. You *may* invite them back later for a "second service" speed measurement, labelled as such.

**Optional extra signal:** an LLM given only the docs and a terminal in a sandbox can quickly expose ambiguous steps. Label it *"automated docs probe — not a trial"* and never use it to satisfy the pass standard.

### 3.8.6 Worked example — turning findings into changes

| Finding | Class | Fix | Re-test |
| --- | --- | --- | --- |
| Participant could not find which digest to promote | Docs | Golden path step 3 links the Actions run; summary prints the next command | Trial 2 |
| Did not know the `harbour-dev` context name | Docs | START-HERE §Access shows expected `kubectl config get-contexts` output | Trial 2 |
| Asked whether staging is "real" | Concept | Add "environments" reference and glossary | Trial 2 |

Severity: **S1** blocks completion (fix before re-trial), **S2** causes >5 min delay (fix and re-test), **S3** polish (backlog).

**Verify:** Every stuck point has a ticket or an explicit "won't fix because …". Re-run the template test after each fix.

---

## Section 3.9 — Operating the platform as a product

A passed trial is the start of the product, not the end.

| Practice | Minimum for Harbour |
| --- | --- |
| **Support model** | `platform-support` (broken/stuck) and `platform-gap` (path does not fit) issue labels with a stated response target (e.g. 1 business day). Convert every repeated question into docs or a fix within the week. |
| **Versioning** | Platform logic lives in reusable workflows and base manifests so fixes propagate by reference; generated services carry a `golden path vN` stamp; breaking changes need a deprecation note and migration guide (as D04 §4.7.2). |
| **Roadmap** | Rank work by *how many developers hit it, how badly, how often*, using trial findings and support categories. Write non-goals down to resist scope creep. |
| **Platform reliability** | Template test, link check, catalogue freshness and a periodic docs-only dry run on a clean machine. If the status command lies or template CI is red, trust collapses. |

**Practice — reproduce:** Write `docs/platform/ROADMAP.md` with three items, each justified by a specific rehearsal or trial finding.

---

## Section 3.10 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Scaffold fails with "name must be…" | Uppercase, underscore or too short | Naming rule in the error and in the golden path |
| `policy` check fails: UNPROMOTED sentinel | New service not yet promoted | Use `--allow-unpromoted` only on the creation PR; then promote a real digest |
| Release job green but no digest in summary | Path filter did not trigger or `workflow_call` output not wired | Actions run for `<name>-release`; `service-release` outputs |
| Promotion merged but pod `ImagePullBackOff` | Private package or wrong owner in image name | GHCR package visibility; `kubectl describe pod` events; D06 §6.5.3 |
| `harbour-status` says UNKNOWN | No read context or namespace not created | START-HERE §Access; tenant manifest reconciled? |
| Namespace missing after merge | Tenant manifests not reconciled by the platform Kustomization | P04 §4.5; `flux get kustomizations -A` |
| Trial participant stuck at access | Access instructions rely on author | Rewrite §Access; this is a docs defect, not user error |
| Template test passes locally but fails in CI | Dependency on local tools or `.venv` | Pinned installs (D04); clean-clone run |
| Participant "didn't read the docs" | Docs not where they looked | Findability defect — move the step to START-HERE |

---

## Practical Assessment — Chapter 3 — independent golden-path trial

Align with the [P03 Course Detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) and Final Project Checklist **P03**.

### Required deliverables

1. `docs/platform/PRODUCT.md` — users, JTBD, non-goals, success metrics, interface decision, known limitations.
2. `docs/platform/golden-path.md` and `docs/platform/START-HERE.md` written for a stranger audience (tool versions, access, smoke test, steps, done-means, escape hatch).
3. Working scaffold (`harbour-new-service`), promotion helper, conformance check, status command and catalogue generator, plus a passing **template test** from a clean clone.
4. Guardrails documented: naming, quota, digest-only, no cluster-admin for developers, review gates, **documented human gates with expected waits**.
5. Service runbook template covering the planted failure(s) without author help.
6. **Independent trial record(s)** per §3.7.2: participant role, docs commit, tasks T1–T4, timings, stuck points, interventions classified, independent completion time, cognitive-load ratings and verbatim feedback.
7. **Pass condition evidence:** at least one trial with **zero I2/I3 interventions** and all four tasks completed, *or* an honest `FAIL`/`pending` status plus the fix backlog and re-trial plan.
8. ADR `0305-portal-decision.md` with the evidence that would change the decision.
9. Findings triage: every S1/S2 fixed and re-tested; S3 backlog; `ROADMAP.md` with three evidence-based items.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Product thinking | Feature list; portal installed | Users, JTBD, non-goals, measurable success criteria | Metrics defined pre-trial and used to prioritise |
| Golden path | Scaffold only | Create → build → promote → observe → investigate, contract table | Escape hatch with expiry; versioning/upgrade policy |
| Safe self-service | Admin credentials or manual hand-offs | Digest-only, quota, review gates, documented human gates | Policy also enforced at admission (see P04) |
| Documentation | Author-oriented | Stranger-tested START-HERE; copy-paste commands with expected output | Docs CI (links, catalogue freshness) and accessibility notes |
| Independent trial | Self-test or friend "helped a bit" | Real second person; **zero undocumented interventions**; findings recorded | Second trial after fixes; improvement shown in stuck points/time |
| Measurement honesty | Percentages from n=1 | Counts, quotes, limitations stated | Distinguishes documented waits; labels rehearsal/automated probes |
| Investigation | Participant told the cause | Planted failure diagnosed from runbook/status only | Failure card, repeatable injection, recovery by promotion revert |

**Completion:** **Competent** on every row, including a genuine independent trial. A portal screenshot, a demo you drove, or a trial with undocumented help does **not** pass.

### Self-check

- Could you name your user, their four jobs and your non-goals from memory?
- Did the participant ever build or see Harbour before? (If yes, the trial is INVALID.)
- Count your interventions honestly: did you answer any question that the docs do not answer? (If yes, FAIL — fix docs and re-run with a new participant.)
- Is every human gate in the path **documented with an expected wait**?
- Can a developer recover from the planted failure without live edits to the cluster?
- Did you subtract only *documented* waits from the independent time?
- Did you record what you will **not** claim (n=1, kind scale, no accessibility audit)?
- Do trial findings appear as changes to the platform, not just notes?

### Example conclusion (evidence still required)

> Interface v1 is the repo CLI + docs (ADR 0305); a portal was deferred because no trial finding needed one. Trial 1 (backend developer, no Kubernetes, never seen Harbour): T1–T3 passed, T4 required one undocumented hint ("look at events") → **FAIL (I2)**. Findings: 4 stuck points (access context name; summary location; probe vs events; runbook jargon). Fixes shipped (START-HERE access output, runbook row rewritten, status prints events). Trial 2 (different participant, same tasks): 0 interventions, 3 stuck points (all S3), independent completion 74 min excluding 11 min documented CI/review wait; cognitive load ratings 3/3/2/4. n=2 qualitative only. Template test green on clean clone; docs commit abc123. P03 checklist ticked after trial 2.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Decide what to build | Writing JTBD and a pass/fail trial standard | Installing a portal first |
| Reduce developer load | Opinionated defaults + one entry doc | Offering twelve ways to deploy |
| Give self-service safely | Guardrails + review + digest-only + namespaced identity | Handing out cluster-admin |
| Prove it works | Trial with a stranger, zero undocumented help | Demoing it yourself |
| Handle a question during trial | "I can't help — what do the docs say?" | "Oh, you just need to…" |
| Make it discoverable | Catalogue as files with owner + runbook | A wiki nobody updates |
| Decide on a portal | Tie it to an observed stuck point | Choosing by popularity |
| Handle stateful needs | Document as out of v1; plan in P04 | Faking a database option |

## Glossary

| Term | Meaning |
| --- | --- |
| Platform as a product | Treating the platform as something with users, outcomes, metrics and a roadmap |
| Golden path | Supported, opinionated, easiest route for a common job; leaving it is allowed but you own more |
| JTBD | Jobs-to-be-done: the outcome a user is trying to achieve |
| Cognitive load | Mental effort required; platforms aim to reduce *extraneous* load |
| Self-service | Completing a job without waiting for a human to act for you, inside enforced guardrails |
| Intervention | Observer help not in the written docs (I2/I3 fail a trial) |
| Stuck point | Moment a participant pauses, backtracks or searches without progress |
| Documented wait | A designed delay (CI, review) subtracted from independent time |
| Escape hatch | Documented way to deviate from the path, owning the consequences |

## References

- [Team Topologies — platform as a product](https://teamtopologies.com/key-concepts) · [CNCF Platforms White Paper](https://tag-app-delivery.cncf.io/whitepapers/platforms/) · [CNCF Platform Engineering Maturity Model](https://tag-app-delivery.cncf.io/whitepapers/platform-eng-maturity-model/)
- [Backstage software catalog descriptor format](https://backstage.io/docs/features/software-catalog/descriptor-format)
- [Diátaxis documentation framework](https://diataxis.fr/)
- [Flux multi-tenancy guidance](https://fluxcd.io/flux/installation/configuration/multitenancy/)
- [DORA research programme](https://dora.dev/) — use metrics as signals, not targets
- [D04](../4.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md) · [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) · [D07](../4.1%20DevOps/D07%20Observability.md) · [DevOps Exit Assessment](../4.1%20DevOps/DevOps%20Exit%20Assessment.md)

**Previous chapter:** [P02 — Kubernetes Administration and Operations](P02%20Kubernetes%20Administration%20and%20Operations.md) · **Course detail:** [P03](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) · **Next:** [P04 — Platform Architecture and Final Project](P04%20Platform%20Architecture%20and%20Final%20Project.md) · **Checklist:** [Final Project Checklist · P03](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
