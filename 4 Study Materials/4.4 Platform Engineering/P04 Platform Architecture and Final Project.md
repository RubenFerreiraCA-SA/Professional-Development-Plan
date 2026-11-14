# Chapter 4 — Platform Architecture and Final Project (P04)

*Platform Engineering textbook · Chapter 4 of 4*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [P04 course detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P04%20Platform%20Architecture%20and%20Final%20Project.md) (about 40–50 hours, plus time to recruit an independent developer). |
| **Prerequisites** | [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md), [P02](P02%20Kubernetes%20Administration%20and%20Operations.md) and [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) (golden path, scaffold, self-service guardrails, trial protocol). The DevOps ([D04](../4.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md), [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md), [D07](../4.1%20DevOps/D07%20Observability.md)) and Cloud ([C02–C03](../4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md)) Harbour path is preferred. AI optional. |
| **Status** | Authored for study; documentation review pending. Clean-room execution of every script is **not** claimed. |

## How to study this chapter

P01–P03 gave you workloads, operations and a golden path. P04 asks you to **integrate them into one platform you can demonstrate and defend** — and to prove it with someone other than yourself.

The minimum integrated outcome is five linked capabilities, each with measurable acceptance:

| # | Outcome | Acceptance (measurable) |
| --- | --- | --- |
| 1 | **Developer creates a service** from the template / golden path | Scaffolded service passes tests and the conformance check; appears in the catalogue |
| 2 | **Reviewed change + trusted build** | Required checks block a bad PR; merge yields an **immutable digest** with tests, **provenance** and SBOM traceable to the merge commit |
| 3 | **Self-service deployment** to an approved environment | Promotion by PR to an allowed environment only; deployer identity is namespaced; **policy** rejects non-conforming workloads; no secrets in Git |
| 4 | **Health, failure, recovery** | Status/telemetry show health; at least one **stateless and one stateful** failure are injected and recovered via a runbook; evidence kept |
| 5 | **Independent developer acceptance** | A developer who did not build Harbour completes the path with **no author assistance**; every finding is recorded and dispositioned |

> **Why a stateful scenario is mandatory here:** [C03](../4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md) deliberately drilled a **stateless** API (task stop, bad deploy) — recovery meant "run another copy". Stateful recovery is different: data may be lost, corrupted or unreachable, and "restart it" can make things worse. P04 exercises at least one stateful failure and an honest restore with measured RPO/RTO.

Work in order: **Concept → ADR → Implementation → Drill → Reflect**. The last sections (§4.9–§4.10) cover architecture defence and Final Project demonstration rehearsal. The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) P04 bar is: *you satisfy every **Required** final-demonstration item for your in-scope pathway and can defend trade-offs from ADRs.*

> **Safety and cost boundary:** Use a disposable local cluster (kind) and fabricated data only. Never commit credentials, kubeconfigs, tokens or database dumps (add them to `.gitignore`). Do not point Flux or policy experiments at a shared or production cluster. Cloud resources (from C03) cost money — confirm your budget alarm still fires and tear down when finished. Obtain consent from your independent tester and record roles, not names.

### Learning outcomes

1. Define an integrated platform scope, an ownership model and trust boundaries, and record them as ADRs.
2. Wire template → review → trusted build → promotion → GitOps deployment into one traceable path.
3. Enforce policy as code at CI and admission; demonstrate a denied unauthorised action.
4. Run and recover a **stateful** failure (pod loss and destructive data change) and quantify RPO/RTO honestly.
5. Run an independent acceptance test and turn findings into platform changes.
6. Defend architecture trade-offs against evidence; distinguish proven, partial and unproven claims.
7. Rehearse and deliver a Final Project demonstration mapped to the checklist.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export SVC="${SVC:-ledger}"           # the integrated demo service (created in §4.3)
export GH_OWNER="${GH_OWNER:?set to your lowercase GitHub owner}"
cd "$HARBOUR_ROOT"

for cmd in git gh kubectl kind flux helm docker jq; do
  command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; exit 1; }
done
command -v kyverno >/dev/null || echo "Install the Kyverno CLI for CI policy checks (§4.5.2)"
for f in platform/bin/harbour-new-service platform/bin/harbour-promote \
         platform/bin/harbour-check-service platform/bin/harbour-status \
         docs/platform/golden-path.md docs/platform/START-HERE.md; do
  test -f "$f" || { echo "P03 artefact missing: $f"; exit 1; }
done
kubectl config current-context | grep -q "kind-" || { echo "Expected a kind context."; exit 1; }
flux check >/dev/null || { echo "Flux not healthy (D06)"; exit 1; }

mkdir -p docs/final/{acceptance,drills,defence,demo} platform/{components/postgres,policy,drills}
printf '%s\n' 'docs/final/drills/**/*.dump' '*.kubeconfig' >> .gitignore
```

You need the P03 golden path working, a Git remote Flux reconciles, GHCR (or another registry) the cluster can pull from, and `gh` authenticated. If P03's independent trial has not passed, finish it first — P04 builds on a golden path a stranger can use.

---

## Section 4.1 — Scope the integrated platform

### 4.1.1 Pick one runtime and say so

Harbour has two runtime stories in this programme: **AWS ECS/Fargate** ([D05](../4.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md), [C03](../4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md)) and **Kubernetes on kind** (D06, P01–P03). Do not blur them in the demonstration.

| Option | Choose when | Integrated claims you can make | Honest limits |
| --- | --- | --- | --- |
| **A. kind + Flux (this chapter's labs)** | Cost-free, repeatable, fully scripted | Entire path incl. tenancy, policy, stateful drills | Not production; single node; storage is local disk |
| **B. Cloud Kubernetes (e.g. EKS)** | You have budget and C03 foundations | Same manifests on real nodes/storage | Cost; Terraform for cluster is extra scope |
| **C. ECS path with a thin platform front-end** | You are not doing Kubernetes in your PDP | Template + CI + Terraform deploy | P01/P02 rows become `Adapted:` — record it |

Write the decision in **ADR 0306** (§4.2). The labs below assume Option A; adapt consciously, not silently.

### 4.1.2 The integrated outcome matrix

Create `docs/final/INTEGRATED-OUTCOME.md` and keep it updated. Nothing is "done" without a link to evidence you can open during the demonstration.

| Outcome | Modules it integrates | Checklist items served | Evidence path (fill in) |
| --- | --- | --- | --- |
| 1 Create service | P03, D01, D03 | Final demo: *another developer … contribute safely* | `services/$SVC`, `catalog/$SVC.yaml`, acceptance record |
| 2 Reviewed change + trusted build | D01, D04 | *reviewed change triggers build/test; traceable artefact* | PR URL, Actions run, digest, attestation output |
| 3 Self-service deploy | D05, D06, P02, P03 | *approved environment … service is deployed*; *security and access controls explained* | tenant manifests, promotion PR, policy denial transcript |
| 4 Health, failure, recovery | D07, P01, P02, C03 | *health visible; failure investigated and recovered* | drill timelines, runbooks, status output |
| 5 Independent acceptance | P03 | *another developer …* | `docs/final/acceptance/ACCEPT-001.md` |

**Scope notes.** AI (A01–A03) is optional: mark `N/A — out of scope` unless in your PDP. Datadog (D08) may be `N/A` for the Final Project if you meet an equivalent ops bar on your D07 stack — record the substitution. Neither blocks completion.

**Verify:** The matrix has no empty evidence cell for an in-scope outcome, and every path resolves.

---

## Section 4.2 — Architecture, ownership and ADRs

### 4.2.1 Views you need

Three small views beat one beautiful diagram. Keep them as text so they diff in Git (`docs/architecture.md`).

```text
Context:   Developer ──PR──> Git (main, protected) ──CI──> Registry (image@digest + attestation)
                                  │                              │
                             promotion PR                        │ pulled by digest
                                  ▼                              ▼
                       Flux (platform identity) ──reconcile──> Namespace <svc>-staging
                                                                  ├─ Deployment (stateless API)
                                                                  └─ StatefulSet Postgres + PVC + backup CronJob
Trust:     [Developer] -- write: PR only -- [Git] -- read-only --> [Flux/cluster]
           [CI] -- push image + attest, no cluster creds --> [Registry]
           [Kyverno admission] -- last line of defence on every Pod in tenant namespaces
```

**Ownership table** (extend D06 ADR 0006 and P01–P02 ADRs 0301–0304): who owns each thing, and what must *never* be pruned.

| Resource | Owner | Reconciled by | Prune? |
| --- | --- | --- | --- |
| Cluster, Flux, Kyverno, policies | Platform | Bootstrap / platform Kustomization | Platform only |
| Tenant namespace, quota, deployer identity | Platform (reviewed PR) | `platform-tenants` | Yes, after review |
| Service Deployment/Service | Service owner | Per-tenant Flux Kustomization | Yes |
| Postgres PVCs (data + backup) | Service owner with platform guidance | Per-tenant Kustomization | **No** (see §4.6.1) |
| Image digests and attestations | CI | Registry | Retention policy, not manual deletion |

### 4.2.2 The ADR set (minimum)

| ADR | Decision it records | Must include |
| --- | --- | --- |
| 0306 | Runtime and scope (kind+Flux vs cloud vs ECS); builds on P01's ADR 0301 | Alternatives, cost, what is *not* claimed |
| 0307 | Platform boundary and golden-path contract | Extends P03 contract table; non-goals |
| 0308 | Delivery trust model (review, CI, digest, provenance) | What provenance does **not** prove |
| 0309 | Deployment identity, tenancy and policy | Namespaced reconciler; admission policy; known RBAC gaps |
| 0310 | State and data (Postgres on Kubernetes) | Backup location, RPO/RTO targets and *measured* values, prune rules |
| 0311 | Observability, SLOs and runbook ownership | Signals per drill; alert → runbook link |
| 0312 | Secrets and access | Where secrets live; rotation; what kind does **not** protect |
| 0313 | Cost and operations | Teardown, idle policy, budgets |

ADR quality bar (the defence in §4.9 attacks exactly these): **context, decision, alternatives considered, consequences (good and bad), evidence link, revisit trigger**.

```markdown
# ADR 0310 — State and data for Harbour services (training)

## Status
Accepted (date) — revisit if: any service stores non-fabricated data.

## Context
C03 drilled a stateless service. Ledger uses Postgres on kind (local-path storage, single node).

## Decision
Single-replica Postgres StatefulSet; 5-minute logical backups (pg_dump -Fc) to a separate PVC
in the same namespace; off-cluster copy taken manually for drills.

## Alternatives
CloudNativePG operator (better, more to learn); RDS (C03 option, costs money); no database.

## Consequences
- Pod loss: data survives on PVC; target RTO < 3 min (measured: __ s).
- Destructive change: restore from last dump; target RPO <= 5 min (measured: __ min of writes lost).
- **Not covered:** node/cluster loss on kind (PVs live on the Docker host), PITR, HA failover.

## Evidence
docs/final/drills/stateful-YYYYMMDD/
```

### 4.2.3 The limitations register

Create `docs/final/LIMITATIONS.md` now, not the night before the demo. One row per honest gap: *Gap · Impact · Compensating control · Would fix by*. Typical entries: kind is single-node; `view` developer role is cluster-wide; secrets are base64 in etcd; backups share the cluster's fate; attestations depend on the CI platform plan.

**Practice — reproduce:** Write ADR 0306 and 0310 with real values from your environment. Every `…` must be provable from a command or file.

**Verify:** A reader can find, for each ADR, an evidence link and a stated limitation.

---

## Section 4.3 — Outcome 1: a developer creates a service

Use the **P03 scaffold** exactly as a trial user would. Create the integrated demo service on a feature branch:

```bash
git checkout -b feat/$SVC-golden-path
platform/bin/harbour-new-service "$SVC" --owner "$GH_OWNER"
platform/bin/harbour-check-service "$SVC" --allow-unpromoted
( cd services/$SVC && python3 -m venv .venv && . .venv/bin/activate \
    && pip install -q -r requirements.txt && pytest -q )
platform/bin/harbour-catalog
git add -A && git commit -m "feat($SVC): create from golden path v1" && git push -u origin HEAD
```

Open a pull request. **Do not** bypass review: the creation PR is the first integrated evidence (it touches `platform/tenants/$SVC`, which CODEOWNERS routes to the platform reviewer — a *documented human gate*; record its wait).

Add the stateful dependency in §4.6 only **after** the stateless path is green end to end. Integration debt compounds: fix one layer at a time.

**Verify:** PR shows required checks; reviewer approval is required; after merge the catalogue lists `$SVC` with owner and runbook; `harbour-status $SVC` reports `UNKNOWN` or `DOWN` (0 replicas, unpromoted) — not a false HEALTHY.

---

## Section 4.4 — Outcome 2: reviewed change and trusted build

### 4.4.1 Concept: what "trusted" means (and does not)

| Control | Claim it supports | What it does **not** prove |
| --- | --- | --- |
| Required review + CODEOWNERS | A second person saw the change | The reviewer understood it |
| Required tests | Known regressions are blocked | Absence of bugs |
| Immutable digest | The same bytes run everywhere | The bytes are safe |
| **Provenance attestation** | This digest was built by *this workflow* from *this commit* | The source or workflow is benign; a compromised CI could sign anything |
| SBOM | You know the contents | The contents are vulnerability-free |

Provenance is **evidence for tracing and verification**, not a guarantee. Say so in ADR 0308.

### 4.4.2 Worked example — extend the release workflow

Add tests as a gate, build with provenance/SBOM, and attest the digest. Replace the `release` job in `.github/workflows/service-release.yml` and add a `test` job:

```yaml
jobs:
  test:
    uses: ./.github/workflows/python-validate.yml
    with:
      working-directory: services/${{ inputs.service }}
  release:
    needs: test
    runs-on: ubuntu-latest
    permissions: {contents: read, packages: write, id-token: write, attestations: write}
    outputs:
      digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      # …meta, docker/login-action and setup-buildx exactly as in P03 §3.3.3…
      - id: push
        uses: docker/build-push-action@v6
        with:
          context: services/${{ inputs.service }}
          push: true
          tags: ${{ steps.meta.outputs.image }}:${{ github.sha }}
          provenance: mode=max
          sbom: true
      - uses: actions/attest-build-provenance@v2
        with:
          subject-name: ${{ steps.meta.outputs.image }}
          subject-digest: ${{ steps.push.outputs.digest }}
          push-to-registry: true
```

Callers (`<svc>-release.yml`) must now grant `id-token: write` and `attestations: write` as well, since a called workflow cannot exceed the caller's permissions. **Limitation:** artifact attestations on **private** repositories may require a paid plan; if unavailable, use a public training repo or document the gap and use Sigstore `cosign` keyless signing instead.

### 4.4.3 Worked example — verify before you promote

`platform/bin/harbour-verify-artifact` turns "I trust the build" into a command:

```bash
#!/usr/bin/env bash
set -euo pipefail
REF="${1:?usage: harbour-verify-artifact ghcr.io/<owner>/<svc>@sha256:<digest>}"
OWNER="${REF#ghcr.io/}"; OWNER="${OWNER%%/*}"
[[ "$REF" =~ @sha256:[0-9a-f]{64}$ ]] || { echo "ERROR: reference must be pinned by digest" >&2; exit 1; }
docker buildx imagetools inspect "$REF" >/dev/null   # image exists in the registry
gh attestation verify "oci://$REF" --owner "$OWNER" --format json \
  | jq -r '.[0].verificationResult.signature.certificate
           | "built-from-commit=\(.sourceRepositoryDigest)\nref=\(.sourceRepositoryRef)\nworkflow=\(.githubWorkflowName)"'
echo "VERIFIED: $REF"
```

(JSON field paths can differ between `gh` versions — inspect the raw output once and adjust.) The output answers *which commit built this digest*; compare it with `git log` for the merge commit.

Make promotion **impossible without verification** with a PR check, `.github/workflows/promotion-verify.yml`:

```yaml
name: promotion-verify
on:
  pull_request:
    paths: ["deploy/*/overlays/*/kustomization.yaml"]
permissions:
  contents: read
  attestations: read
  packages: read
jobs:
  verify:
    runs-on: ubuntu-latest
    env: {GH_TOKEN: "${{ github.token }}"}
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - name: Verify the digest pinned in every changed overlay
        run: |
          for f in $(git diff --name-only "origin/${{ github.base_ref }}"...HEAD -- 'deploy/*/overlays/*/kustomization.yaml'); do
            img="$(sed -nE 's/^[[:space:]]+newName:[[:space:]]+(.*)$/\1/p' "$f" | head -1)"
            d="$(grep -oE 'digest: sha256:[0-9a-f]{64}' "$f" | head -1 | cut -d' ' -f2)"
            grep -q UNPROMOTED "$f" && { echo "skip $f (unpromoted)"; continue; }
            gh attestation verify "oci://${img}@${d}" --owner "${{ github.repository_owner }}" >/dev/null \
              && echo "verified ${img}@${d}" || { echo "NO VALID ATTESTATION for ${img}@${d}"; exit 1; }
          done
```

This is deliberately simple (one image per overlay). Treat it as a starting point and test it with a **fabricated digest** — it must fail.

### 4.4.4 Review and branch protection are part of the trust story

Verify, don't assume (D01/D04):

```bash
# assumes the repository name equals the directory name; otherwise set REPO explicitly
gh api "repos/$GH_OWNER/$(basename "$HARBOUR_ROOT")/branches/main/protection" \
  | jq '{reviews: .required_pull_request_reviews.required_approving_review_count,
         codeowners: .required_pull_request_reviews.require_code_owner_reviews,
         checks: .required_status_checks.contexts, admins: .enforce_admins.enabled}'
```

Required checks must include the service validate job, `policy` and `promotion-verify`. If your plan cannot enforce this, write the gap into `LIMITATIONS.md` with a compensating control (e.g. you do not self-approve; a second reviewer is the independent tester).

**Practice — reproduce:** (1) Open a PR that breaks a test; show it is unmergeable. (2) Fix, merge, and record commit SHA, workflow run URL and digest. (3) Run `harbour-verify-artifact` on that digest and match the commit. (4) Promote a **fabricated** digest and show `promotion-verify` fails.

**Verify:** One page shows *merge commit → run URL → digest → attestation commit → promotion PR*. Without a break in that chain, the artefact is traceable.

---

## Section 4.5 — Outcome 3: self-service deployment under identity and policy

### 4.5.1 Approved environments and identities

| Question | Harbour answer (record in ADR 0309) |
| --- | --- |
| Which environments can a developer promote to? | `staging` via `harbour-promote`; any other is rejected (P03 §3.4.2). Production-shaped `harbour-prod` needs a platform reviewer — not self-service |
| Who applies manifests? | The per-tenant Flux `reconciler` ServiceAccount, `admin` only **inside its namespace** (P03 tenant manifest) |
| What can CI do? | Push images and attestations. **No cluster credentials** |
| What can a developer do in the cluster? | Read-only status; changes through pull requests |

Document it in `docs/platform/environments.md`: environment, who may promote, required checks, owner, data classification (fabricated only).

### 4.5.2 Policy as code: CI and admission

Policy in CI gives fast feedback; policy at admission catches everything that bypasses CI. Use the **same** rules in both. Install Kyverno (pin the chart version you tested):

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/ && helm repo update
helm upgrade --install kyverno kyverno/kyverno -n kyverno --create-namespace
kubectl -n kyverno rollout status deploy --timeout=180s
```

`platform/policy/harbour-baseline.yaml` (rule-level `failureAction` requires a recent Kyverno; older releases use `spec.validationFailureAction` — check your version's docs):

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: {name: harbour-baseline}
spec:
  background: false
  rules:
    - name: require-image-digest
      match: {any: [{resources: {kinds: [Pod]}}]}
      exclude: {any: [{resources: {namespaces: [kube-system, kyverno, flux-system, local-path-storage, platform-system]}}]}
      validate:
        failureAction: Enforce
        message: "Images must be pinned by digest (image@sha256:...). Mutable tags are rejected."
        pattern:
          spec:
            containers:
              - image: "*@sha256:*"
    - name: require-nonroot-and-limits
      match: {any: [{resources: {kinds: [Pod]}}]}
      exclude: {any: [{resources: {namespaces: [kube-system, kyverno, flux-system, local-path-storage, platform-system]}}]}
      validate:
        failureAction: Enforce
        message: "Pods must run as non-root, forbid privilege escalation and set CPU/memory limits."
        pattern:
          spec:
            securityContext: {runAsNonRoot: true}
            containers:
              - securityContext: {allowPrivilegeEscalation: false}
                resources: {limits: {cpu: "?*", memory: "?*"}}
```

**Relationship to P02:** P02 §2.4.3 shows a built-in `ValidatingAdmissionPolicy` for digest-addressed **Deployments**, and says plainly that StatefulSets, Jobs and bare Pods are not covered. Kyverno's Pod-level rules cover them (including the Postgres StatefulSet and backup CronJob) and run identically in CI. Use one mechanism per rule, or run both and note the overlap in ADR 0309; do not leave an uncovered kind unrecorded. NetworkPolicy and Pod Security admission (P02 §2.3–§2.4) remain additional controls — list any you did *not* apply in `LIMITATIONS.md`.

Commit it to `platform/policy/` and reconcile it through the platform Kustomization (a policy applied by hand is a snowflake). Now add the **same file** to CI — replace the grep checks in `harbour-check-service` with:

```bash
kubectl kustomize "deploy/$NAME/overlays/staging" > /tmp/rendered.yaml
kyverno apply platform/policy/harbour-baseline.yaml --resource /tmp/rendered.yaml
```

(Allow the UNPROMOTED sentinel digest as before; it is a valid digest *format*, and replicas are 0.)

### 4.5.3 Worked example — show what the controls deny

Capture a transcript in `docs/final/drills/access-denials.txt`. Each line below is evidence for the demonstration item *security and access controls are explained, gaps are honest*:

```bash
SA="system:serviceaccount:${SVC}-staging:reconciler"
{
  echo "# reconciler may manage workloads in its own namespace"
  kubectl auth can-i create deployments -n "${SVC}-staging" --as="$SA"
  echo "# ...but not create namespaces, or read other namespaces' secrets"
  kubectl auth can-i create namespaces --as="$SA"
  kubectl auth can-i get secrets -n kube-system --as="$SA"
  echo "# read-only developer identity cannot change anything"
  kubectl auth can-i delete pods -n "${SVC}-staging" --as=system:serviceaccount:platform-system:dev-viewer
  echo "# admission: a mutable-tag pod is rejected even for the privileged reconciler"
  kubectl -n "${SVC}-staging" run bad --image=nginx:latest --as="$SA" 2>&1 | tail -n 3
  echo "# promotion to an unapproved environment is refused"
  platform/bin/harbour-promote "$SVC" prod "sha256:$(printf '0%.0s' {1..64})" 2>&1
} | tee docs/final/drills/access-denials.txt
```

Expect `yes`, `no`, `no`, `no`, an admission denial quoting the policy message, and the promotion error. If any `no` is `yes`, you have found a privilege gap — fix it or record it.

### 4.5.4 Secrets

No secret may live in Git. For the demo database, the **platform operator** creates the credential out of band:

```bash
kubectl -n "${SVC}-staging" create secret generic postgres-credentials \
  --from-literal=password="$(openssl rand -base64 18)" --dry-run=client -o yaml | kubectl apply -f -
```

Document in ADR 0312: who creates it, rotation (manual here), and that on kind the value is **base64 in etcd, not encrypted**. Production-shaped options (External Secrets Operator, Sealed Secrets, SOPS) are the next step, not a claim.

### 4.5.5 Deploy

1. Make the golden path service real: wait for the release run, then `harbour-promote $SVC staging <digest>` and open the promotion PR; `promotion-verify` and `policy` must pass.
2. Merge; Flux reconciles `$SVC` in `${SVC}-staging`.
3. Confirm the **running** artefact is the verified digest:

```bash
kubectl -n "${SVC}-staging" get deploy "$SVC" -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl -n "${SVC}-staging" get pods -l app="$SVC" -o jsonpath='{range .items[*]}{.status.containerStatuses[0].imageID}{"\n"}{end}'
platform/bin/harbour-status "$SVC"
```

**Verify:** Running `imageID` digest equals the promoted digest equals the attested digest; `harbour-status` is HEALTHY; the denial transcript exists.

---

## Section 4.6 — Outcome 4: health, failure and recovery (including state)

### 4.6.1 Add a stateful dependency deliberately

Stateful services were out of P03's v1 golden path because they are expensive to get wrong. Add Postgres as a **platform component** the service opts into (StatefulSet and PVC concepts: P01 §1.8). This is a documented human gate: raise the tenant quota (`pods: "8"`, `requests.cpu: "1"`, `requests.memory: 1Gi`, `limits.cpu: "2"`, `limits.memory: 2Gi`) through a reviewed edit of `platform/tenants/$SVC/tenant.yaml`.

`platform/components/postgres/statefulset.yaml` (pin the image digest: `docker buildx imagetools inspect postgres:16-alpine --format '{{.Manifest.Digest}}'`):

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata: {name: postgres}
spec:
  serviceName: postgres
  replicas: 1
  selector: {matchLabels: {app: postgres}}
  template:
    metadata: {labels: {app: postgres}}
    spec:
      securityContext: {runAsNonRoot: true, runAsUser: 70, fsGroup: 70, seccompProfile: {type: RuntimeDefault}}
      containers:
        - name: postgres
          image: postgres@sha256:REPLACE_WITH_RESOLVED_DIGEST
          ports: [{name: pg, containerPort: 5432}]
          env:
            - {name: POSTGRES_USER, value: harbour}
            - {name: POSTGRES_DB, value: harbour}
            - {name: PGDATA, value: /var/lib/postgresql/data/pgdata}
            - {name: POSTGRES_PASSWORD, valueFrom: {secretKeyRef: {name: postgres-credentials, key: password}}}
          readinessProbe: {exec: {command: [pg_isready, -U, harbour, -d, harbour]}, periodSeconds: 5}
          securityContext: {allowPrivilegeEscalation: false}
          resources: {requests: {cpu: 100m, memory: 128Mi}, limits: {cpu: 250m, memory: 256Mi}}
          volumeMounts:
            - {name: data, mountPath: /var/lib/postgresql/data}
            - {name: backup, mountPath: /backup, readOnly: true}
      volumes:
        - name: backup
          persistentVolumeClaim: {claimName: postgres-backup}
  volumeClaimTemplates:
    - metadata: {name: data}
      spec: {accessModes: [ReadWriteOnce], resources: {requests: {storage: 1Gi}}}
---
apiVersion: v1
kind: Service
metadata: {name: postgres}
spec: {clusterIP: None, selector: {app: postgres}, ports: [{name: pg, port: 5432}]}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-backup
  annotations: {kustomize.toolkit.fluxcd.io/prune: disabled}   # never garbage-collect backups
spec: {accessModes: [ReadWriteOnce], resources: {requests: {storage: 1Gi}}}
```

`platform/components/postgres/backup-cronjob.yaml` (training cadence: every 5 minutes so RPO is measurable within one session):

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: {name: postgres-backup}
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          securityContext: {runAsNonRoot: true, runAsUser: 70, fsGroup: 70}
          containers:
            - name: dump
              image: postgres@sha256:REPLACE_WITH_RESOLVED_DIGEST
              command: [sh, -c]
              args:
                - >
                  set -e; f=/backup/harbour-$(date -u +%Y%m%dT%H%M%SZ).dump;
                  pg_dump -h postgres -U harbour -d harbour -Fc -f "$f";
                  ls -1t /backup/*.dump | tail -n +7 | xargs -r rm --;
                  echo "wrote $f"
              env: [{name: PGPASSWORD, valueFrom: {secretKeyRef: {name: postgres-credentials, key: password}}}]
              securityContext: {allowPrivilegeEscalation: false}
              resources: {limits: {cpu: 250m, memory: 128Mi}}
              volumeMounts: [{name: backup, mountPath: /backup}]
          volumes: [{name: backup, persistentVolumeClaim: {claimName: postgres-backup}}]
```

Add `kustomization.yaml` listing both files; include the component and the readiness dependency in `deploy/$SVC/overlays/staging/kustomization.yaml`:

```yaml
resources: [../../base, ../../../../platform/components/postgres]
patches:
  - target: {kind: Deployment, name: ledger}   # use your $SVC name
    patch: |-
      - {op: add, path: /spec/template/spec/containers/0/env, value: [{name: DATABASE_HOST, value: postgres}]}
```

Make readiness meaningful — the dependency check from D03, so a missing database removes the pod from traffic **without** restart-looping it. Replace `ready()` in `services/$SVC/main.py`:

```python
import os, socket
from fastapi.responses import JSONResponse


@app.get("/ready")
def ready():
    host = os.getenv("DATABASE_HOST", "")
    if not host:
        return {"status": "ready", "database": "unconfigured"}
    try:
        with socket.create_connection((host, 5432), timeout=1.5):
            return {"status": "ready", "database": "tcp_ok"}
    except OSError:
        return JSONResponse(status_code=503, content={"status": "not-ready", "database": "unreachable"})
```

Ship this through the **normal** path (PR → build → verify → promote). **Honest limits:** TCP reachability is not "queries work"; a single replica has no failover; kind's local-path volume lives on the Docker host; the backup PVC shares the cluster's fate (so you copy a dump **off-cluster** in the drill); prune must never touch data PVCs (hence the annotation and `volumeClaimTemplates`).

### 4.6.2 Define health and recovery targets first

Write them in ADR 0310/0311 *before* injecting failures:

| Signal | Where | Healthy |
| --- | --- | --- |
| Pod Ready / restarts | `harbour-status`, `kubectl get pods` | Ready; restarts stable |
| Readiness body | `/ready` | `database: tcp_ok` |
| Service endpoints | `kubectl get endpoints $SVC` | non-empty |
| Backup freshness | newest successful Job | < 10 min old (2× schedule) |
| SLI (if D07 stack present) | `docs/observability/slo-harbour.md` pattern | availability objective met |

Targets (training, state yours): **RTO ≤ 3 min** for DB pod loss; **RPO ≤ 5 min** for restore from backup. They are *hypotheses* until measured.

### 4.6.3 Stateless drill (brief)

Delete one `$SVC` pod; with two replicas the Service keeps serving (D06 §6.8.1). Record time to full readiness. This is C03-class evidence — necessary, not sufficient.

### 4.6.4 Stateful drills — the script

`platform/drills/stateful-drill.sh` (run phases in order; every phase appends to a timeline):

```bash
#!/usr/bin/env bash
set -euo pipefail
NS="${1:?namespace}"; PHASE="${2:?phase}"; SVC="${SVC:?set SVC}"
OUT="docs/final/drills/stateful-$(date -u +%Y%m%d)"; mkdir -p "$OUT"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$OUT/timeline.log"; }
sql() { kubectl -n "$NS" exec postgres-0 -- psql -U harbour -d harbour -v ON_ERROR_STOP=1 -At -c "$1"; }
fingerprint() { sql "SELECT count(*)||':'||coalesce(md5(string_agg(id||'/'||note, ',' ORDER BY id)),'empty') FROM drill_ledger"; }
case "$PHASE" in
  seed)   # A = rows that exist before the backup
    sql "CREATE TABLE IF NOT EXISTS drill_ledger(id serial primary key, note text not null)"
    sql "INSERT INTO drill_ledger(note) SELECT 'A-'||g FROM generate_series(1,100) g"
    log "seeded A fingerprint=$(fingerprint)" ;;
  backup) # force a backup now, then record what it contains
    J="manual-backup-$(date +%s)"
    kubectl -n "$NS" create job --from=cronjob/postgres-backup "$J"
    kubectl -n "$NS" wait --for=condition=complete "job/$J" --timeout=120s
    fingerprint > "$OUT/fingerprint-at-backup.txt"
    log "backup $J complete; fingerprint-at-backup=$(cat "$OUT/fingerprint-at-backup.txt")" ;;
  write-after) # B = acknowledged writes AFTER the backup (these define RPO exposure)
    sql "INSERT INTO drill_ledger(note) SELECT 'B-'||g FROM generate_series(1,25) g"
    fingerprint > "$OUT/fingerprint-before-incident.txt"
    log "wrote B; fingerprint-before-incident=$(cat "$OUT/fingerprint-before-incident.txt")" ;;
  kill-db) # drill S2: pod loss — data should survive on the PVC
    ep() { kubectl -n "$NS" get endpoints "$SVC" -o jsonpath='{.subsets[*].addresses[*].ip}'; }
    log "S2 inject: delete pod postgres-0"
    T0=$(date +%s); kubectl -n "$NS" delete pod postgres-0 --wait=false
    until [ -z "$(ep)" ] || [ $(( $(date +%s) - T0 )) -ge 60 ]; do sleep 2; done
    [ -z "$(ep)" ] && log "S2 detected: $SVC endpoints empty after $(( $(date +%s) - T0 ))s" \
                   || log "S2 readiness never dropped (outage shorter than probe window)"
    kubectl -n "$NS" get pods -o wide | tee -a "$OUT/observe.log"
    kubectl -n "$NS" wait --for=condition=ready pod/postgres-0 --timeout=180s
    until [ -n "$(ep)" ]; do sleep 2; done
    log "S2 recovered: RTO=$(( $(date +%s) - T0 ))s; app restarts=$(kubectl -n "$NS" get pods -l app="$SVC" \
      -o jsonpath='{.items[*].status.containerStatuses[0].restartCount}')"
    [ "$(fingerprint)" = "$(cat "$OUT/fingerprint-before-incident.txt")" ] \
      && log "S2 data intact after pod loss" || { log "S2 DATA MISMATCH"; exit 1; } ;;
  destroy) # drill S3: simulated bad migration — logical damage the PVC cannot undo
    log "S3 inject: DELETE half the rows (simulated bad migration)"
    sql "DELETE FROM drill_ledger WHERE id % 2 = 0"; log "after damage fingerprint=$(fingerprint)" ;;
  restore) # runbook step: restore the newest dump onto the live database
    T0=$(date +%s)
    kubectl -n "$NS" exec postgres-0 -- sh -c \
      'f=$(ls -1t /backup/*.dump | head -1); echo "restoring $f"; pg_restore -U harbour -d harbour --clean --if-exists "$f"'
    GOT="$(fingerprint)"; WANT="$(cat "$OUT/fingerprint-at-backup.txt")"
    BEFORE="$(cut -d: -f1 "$OUT/fingerprint-before-incident.txt")"
    log "S3 restore RTO=$(( $(date +%s) - T0 ))s restored=$GOT expected=$WANT"
    log "S3 RPO exposure: acknowledged rows lost = $(( BEFORE - ${GOT%%:*} ))"
    [ "$GOT" = "$WANT" ] || { log "S3 RESTORE MISMATCH"; exit 1; } ;;
  *) echo "phases: seed backup write-after kill-db destroy restore" >&2; exit 2 ;;
esac
```

Run it (note that `ledger` quota and Postgres must be healthy first):

```bash
NS="${SVC}-staging"
for p in seed backup write-after kill-db destroy restore; do platform/drills/stateful-drill.sh "$NS" "$p"; done
```

To hold the database down long enough to *watch* readiness drop (a fast pod recreation can finish inside the probe window), you may suspend reconciliation first — `flux suspend kustomization $SVC -n $NS`, scale the StatefulSet to 0, observe, scale back, `flux resume …` — and record that you did.

What each drill proves — and what it does not:

| Drill | Injects | Expected behaviour | Proves | Does **not** prove |
| --- | --- | --- | --- | --- |
| **S2 pod loss** | Delete `postgres-0` | `/ready` → 503 and the Service drops endpoints (pods stay up, **no restart loop**); StatefulSet recreates pod; PVC reattaches; fingerprints match | Self-healing + data durability across pod loss; readiness is meaningful | Node loss, disk loss, HA |
| **S3 bad migration** | Delete half the rows | Pod is healthy yet **data is wrong**; only a backup helps; restore returns the backup-time state | Backup is *restorable*; RPO exposure is quantified (the 25 `B-` rows are gone) | PITR, restoring into a clean cluster |
| **Prune hazard** (read) | Remove the StatefulSet from Git | PVC from `volumeClaimTemplates` survives; the annotated backup PVC is not pruned | Why §4.2.1 forbids prune on data | A tested cluster rebuild |

**Observe the difference:** S2 recovers automatically; S3 needs a human and a runbook, and it **loses data**. A status page that says HEALTHY during S3 is correct about the pod and wrong about the business — record this in the ADR.

### 4.6.5 Off-cluster copy and the rebuild drill (recommended)

A backup that lives only in the cluster dies with the cluster. Copy one dump out (not into Git) and, if time allows, run a rebuild:

```bash
kubectl -n "$NS" exec postgres-0 -- sh -c 'ls -1t /backup/*.dump | head -1' | tee /tmp/latest-dump.txt
kubectl -n "$NS" cp "postgres-0:$(cat /tmp/latest-dump.txt)" "docs/final/drills/latest.dump"   # gitignored
```

Rebuild drill (optional, destructive; the cluster-level equivalent is P02 §2.7.4): delete the namespace's Postgres PVC *and* pod, let GitOps recreate an empty database, restore from the copied dump, compare the fingerprint. If you skip it, write in ADR 0310: **node/cluster-loss recovery is unproven**.

### 4.6.6 Runbooks and evidence

Two runbooks, both written for someone who is not you:

- `docs/services/$SVC/RUNBOOK.md` — developer-facing: "Not Ready + `database: unreachable`" → check status → documented first action.
- `docs/runbooks/postgres-restore.md` — operator-facing: decision tree (*pod down vs data wrong*), exact restore command, verification query, who approves, and "do **not** delete the PVC to 'fix' it."

Evidence per drill: timeline log, pre/post fingerprints, observe log, the runbook version used (commit), measured RTO/RPO versus the targets, and one improvement raised.

### 4.6.7 Platform reliability beyond drills

Run one *game day*: a person other than the author injects a failure from a card; you respond using the runbook only. Convert each confusion into a platform fix. Also keep one **cost** line (`docs/final/cost.md`: kind = no compute spend; any cloud resources with teardown commands) and one **accessibility** pass over START-HERE and runbooks (headings, link text, no colour-only meaning).

**Verify:** Timeline shows inject → detect → recover → verify for S2 and S3; fingerprints and RTO/RPO are recorded; the runbook alone was sufficient (or the gap is logged).

---

## Section 4.7 — Outcome 5: independent developer acceptance

This repeats the P03 principle at integrated scale: **no author assistance**. The P03 trial tested the golden path; this acceptance tests the *whole platform* including review, trusted build, deployment, a stateful failure and recovery. Use a **different** person from the P03 trial where possible (a returning person is a regression check, labelled as such), and the P03 protocol: observer silent, interventions classified I0–I3, stuck points timed, documented waits subtracted.

### 4.7.1 Acceptance tasks

```text
ACCEPTANCE CARD — Harbour platform (developer role)
A1  Create a new service from the golden path (name: acc-<initials>). Tests pass locally.
A2  Make a small behavioural change, open a pull request and get it merged through the required checks.
A3  Find the image digest your merge produced and show how you know it came from your commit.
A4  Deploy that digest to the approved environment through the documented path.
A5  Tell us whether the service is healthy and how you know; show where the runbook is.
A6  The team reports the service is "not ready". Find out why (a planted dependency fault) and restore it using the runbook.
```

Planting for A6 (author-only failure card): a prior merged change points `DATABASE_HOST` at a non-existent host. Symptom: `/ready` → 503 with `database: unreachable`; pods Running but not Ready; Service has no endpoints. Expected diagnosis: dependency unreachable (not an application crash); expected recovery: revert/promote previous known-good configuration by PR. Do **not** reveal the cause.

**Operator role (recommended):** a second person, given `docs/runbooks/postgres-restore.md` and operator access, performs the S3 restore **without** the author. If you cannot arrange this, record "restore executed by author only" in the limitations register — the independent *developer* acceptance can still pass, but the restore claim stays "author-verified".

### 4.7.2 Pass standard

| Result | Condition | Action |
| --- | --- | --- |
| **PASS** | A1–A6 completed; **zero I2/I3 interventions**; findings recorded and dispositioned | Tick outcome 5 |
| **FAIL** | Any undocumented help, or blocked task | Fix docs/product; **new participant**; record the failed trial |
| **INVALID** | Participant saw Harbour internals or the author prompted | Discard, record why |

```markdown
# ACCEPT-001 — integrated acceptance
| Date | Role (anonymised) | Docs commit | Observer | Environment |
| Task | Start | Stop | Pass? | Documented wait (min) | Stuck points | Interventions (class) |
| A1 … A6 |
Independent time (excl. documented waits): __ min · I2/I3 count: __ · Result: PASS/FAIL
## Findings
| ID | Sev (S1–S3) | Finding | Disposition (fixed/ticket/won't fix + reason) | Re-test |
```

**Honest limits:** one participant yields qualitative evidence; say so. A passing acceptance on a platform whose docs only you can maintain is fragile — note who else could update them.

**Verify:** `ACCEPT-001.md` exists, every finding has a disposition, and S1/S2 findings were fixed and re-tested before you claim the outcome.

---

## Section 4.8 — Reliability, cost and platform improvement

Turn evidence into a backlog; do not leave it as notes.

| Source | Example finding | Platform change |
| --- | --- | --- |
| Acceptance stuck point | Participant could not find the digest after merge | Release summary prints digest + next command (P03) |
| S3 drill | Status says HEALTHY while data is wrong | Add data-freshness/backup-age check to status; document limits |
| Policy denial | Error message did not tell how to fix | Improve Kyverno message with a docs link |
| Game day | Runbook assumed operator access | Split developer vs operator runbooks |

Failure-injection menu (pick, don't do all): pod kill, bad promotion (previous digest recovery), expired/rotated secret, quota exhaustion (`pods 6/6`), missing backup (CronJob suspended → freshness alert), Flux suspended (drift visible). For each, name the **signal** that should reveal it; if there is none, that is the finding.

**Verify:** `docs/final/BACKLOG.md` lists improvements with source evidence and owner; at least one S2+ item from acceptance or drills was fixed and re-verified.

---

## Section 4.9 — Architecture defence

### 4.9.1 What a defence is

A 20-minute walkthrough plus 15 minutes of challenge, given to someone who has read your ADRs. You are judged on **fidelity between claims and evidence** and on **trade-off reasoning**, not on how impressive the stack is.

### 4.9.2 The claims ledger

Create `docs/final/defence/CLAIMS.md`. Every sentence you intend to say aloud appears here:

| Claim | Evidence | Status |
| --- | --- | --- |
| A stranger can create and deploy a service without help | ACCEPT-001 | **Proven** (n=1) |
| Artefacts are traceable to a commit | verify-artifact output | **Proven** for CI-built images |
| Pod loss does not lose data | S2 timeline | **Proven** (kind, single replica) |
| Data can be restored after logical damage | S3 timeline | **Proven**, RPO exposure 25 rows |
| Node/cluster loss is recoverable | — | **Unproven** |
| Platform is secure | policy + RBAC transcript | **Partial** — see LIMITATIONS |

Status values: *Proven · Partial · Unproven*. Claiming more than the ledger supports is the cardinal sin.

### 4.9.3 Question bank (rehearse answers with evidence)

1. Why Kubernetes/Flux here rather than ECS (ADR 0306)? What would change your mind?
2. What does provenance prove, and what can a compromised CI still do?
3. Who can change production-shaped state, by what path, and where is that enforced?
4. A developer needs a database tomorrow — what happens, and who waits?
5. Your RPO target is 5 minutes. Show where it was measured. What if the backup job silently fails?
6. Why is the backup PVC in the same cluster? What does that cost you?
7. What does your status command *not* tell a developer?
8. Which finding from acceptance hurt most, and what changed?
9. What happens when the golden path is wrong for a team?
10. What did you decide **not** to build, and why was that right?
11. If you had one more week, what would you change first and what evidence says so?
12. How much of this does a single maintainer sustain?

### 4.9.4 Rehearsal and scoring

Run the defence with a peer. They score: *evidence for each answer (0–2)*, *honest about limits (0–2)*, *trade-offs named (0–2)*, *consistent with ADRs (0–2)*. Record in `docs/final/defence/REHEARSAL-001.md` with questions you could not answer — each becomes an ADR edit, a limitation entry or a task.

**Verify:** No claim in your slides is missing from `CLAIMS.md`; no `Unproven` item is presented as done.

---

## Section 4.10 — Final Project demonstration rehearsal

### 4.10.1 Map the Required demonstration to evidence

From the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) — tick only when the criterion holds:

| ☐ | Required final-demonstration item | You show | Evidence |
| --- | --- | --- | --- |
| ☐ | Another developer can start from the template or Harbour docs and contribute safely | Acceptance record; template; START-HERE | `ACCEPT-001`, PR via required checks |
| ☐ | A reviewed change triggers build/test and produces a traceable artefact | PR → run → digest → `harbour-verify-artifact` | run URL, digest, attestation output |
| ☐ | An approved environment is selected or provisioned through code and the service is deployed | Tenant manifest, promotion PR, running digest | `platform/tenants/`, Flux status, `imageID` match |
| ☐ | Health is visible; a failure can be investigated and recovered with a documented path | `harbour-status`; S2 and S3 timelines; runbooks | `docs/final/drills/`, runbooks |
| ☐ | Security and access controls for the demo are explained (gaps honest) | Denial transcript; ADR 0309/0312; limitations | `access-denials.txt`, `LIMITATIONS.md` |
| ☐ | Repo has no real secrets; limitations and cost choices are written down | Secret scan output; cost note | scan log, `cost.md` |
| ☐ | Short architecture decisions + PDP reflection (achieved / deferred / learn next) | ADR set; reflection | `docs/decisions/`, `PDP-REFLECTION.md` |

**Optional — only if in your PDP:** AI component explanation (A01–A03) and vendor monitoring onboarding (D08). Mark `N/A — out of scope` otherwise; leaving them blank does not make the project incomplete.

Also confirm the P01–P03 rows are honestly ticked: P01 probes/pod-kill recovery, P02 a documented day-2 operation with RBAC evidence, P03 the independent golden-path trial.

### 4.10.2 Run of show (about 30 minutes)

| Min | Step | Shows |
| --- | --- | --- |
| 0–3 | Problem, users, scope, non-goals | Product framing (P03) |
| 3–8 | Create service from template → PR → required checks | Outcomes 1–2 |
| 8–13 | Merge → digest → verify attestation → promotion PR → Flux deploy | Outcomes 2–3 |
| 13–16 | Controls: denial transcript, policy, identities, honest gaps | Item 5 |
| 16–22 | Status, S2 pod loss (live or recorded timeline), S3 restore with RPO | Outcome 4 |
| 22–25 | Independent acceptance results and what changed | Outcome 5 |
| 25–30 | ADR highlights, limitations, reflection | Items 6–7 |

Prepare a **fallback**: pre-recorded timelines and screenshots *with digests and SHAs visible* (screenshots without identifiers do not count), and a known-good branch. Time-box live drills; do not debug live for more than two minutes.

### 4.10.3 Pre-demo checklist (run it)

```bash
cd "$HARBOUR_ROOT"
git status --porcelain | grep . && { echo "Uncommitted changes"; exit 1; } || true
kubectl config current-context
flux get kustomizations -A
platform/bin/harbour-status "$SVC"
platform/bin/harbour-check-service "$SVC"
for f in docs/final/INTEGRATED-OUTCOME.md docs/final/LIMITATIONS.md docs/final/cost.md \
         docs/final/defence/CLAIMS.md docs/final/acceptance/ACCEPT-001.md \
         docs/final/drills/access-denials.txt docs/runbooks/postgres-restore.md \
         docs/final/PDP-REFLECTION.md; do test -s "$f" || echo "MISSING: $f"; done
ls docs/decisions/03*.md
command -v gitleaks >/dev/null && gitleaks detect --no-banner --redact || echo "Run a secret scan (gitleaks or equivalent)"
git ls-files | grep -E '\.(dump|kubeconfig)$|\.env$' && echo "Forbidden files tracked" || echo "No dumps/kubeconfigs tracked"
```

### 4.10.4 PDP reflection

`docs/final/PDP-REFLECTION.md`, short and honest:

```markdown
## Achieved (with evidence links)
## Deferred (what, why, what it would take)
## Learn next (three items, tied to findings)
## What surprised me / what I would do differently
```

Link it from your Personal Profile and record the demonstration in the [Progress and Evidence Log](../../2%20PDP%20templates/2.4%20Progress%20and%20Evidence%20Log.md). The checklist states acceptance independently of the Progress Log: a calendar milestone never "passes" a row.

**Practice — rehearse:** Run the full run-of-show once for a peer, timing it. Write down every place you improvised; each improvisation is missing documentation.

---

## Section 4.11 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Kyverno denies the Postgres pod | Tag not digest, or missing `runAsNonRoot` / limits | Policy message; resolve and pin the image digest |
| Postgres `CrashLoopBackOff` with permission error | Volume ownership vs `runAsUser: 70` | `kubectl logs`; `fsGroup`; local-path provisioner |
| `promotion-verify` fails on a good digest | Attestation not pushed, repo plan lacks attestations, or wrong image name in overlay | `gh attestation verify` output; workflow permissions |
| Release run cannot attest | Caller lacks `id-token: write` / `attestations: write` | Caller and reusable permissions |
| `/ready` 503 but DB pod Ready | Service name/port wrong or NetworkPolicy blocking | `kubectl exec` into app pod; Service DNS |
| Backup job never completes | Secret missing, PVC bound to other node, quota | `kubectl describe job`; quota usage |
| Restore fingerprint mismatch | Backup taken before seed, or newer dump chosen | `ls -lt /backup`; phase order in timeline |
| Flux reports prune warning on PVC | Missing prune-disabled annotation | Manifest annotation; Kustomization events |
| Participant blocked on access | Token/context steps not in START-HERE | Docs defect — fix, new participant |
| Demo cluster differs from docs | Hand-applied snowflake | `flux get`, `git diff`; reconcile from Git |

---

## Practical Assessment — Chapter 4 — integrated platform, acceptance and defence

Align with the [P04 Course Detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P04%20Platform%20Architecture%20and%20Final%20Project.md) and Final Project Checklist **P04**.

### Required deliverables

1. **Integrated outcome matrix** (`INTEGRATED-OUTCOME.md`) with live evidence links for outcomes 1–5.
2. **ADR set 0306–0313** meeting the quality bar, plus `LIMITATIONS.md`.
3. **Outcome 1–2 evidence:** scaffolded service via PR; failing check blocks merge; merge commit → run → **digest** with tests, **provenance** and SBOM; verification output tying digest to commit; fabricated-digest promotion rejected.
4. **Outcome 3 evidence:** namespaced deployer identity; policy-as-code in CI **and** admission; denial transcript; no secrets in Git; running digest equals verified digest.
5. **Outcome 4 evidence:** status/telemetry for health; stateless drill; **stateful S2 (pod loss) and S3 (logical damage + restore)** with timelines, fingerprints, measured RTO/RPO versus targets; developer and operator runbooks.
6. **Outcome 5 evidence:** `ACCEPT-001` with a developer who did not build Harbour, **no author assistance**, interventions classified, stuck points and findings dispositioned (S1/S2 fixed and re-tested).
7. **Defence evidence:** `CLAIMS.md` with Proven/Partial/Unproven statuses and a recorded peer rehearsal.
8. **Demonstration package:** run of show, pre-demo checklist output, secret scan, cost note, `PDP-REFLECTION.md`, and the ticked Final Project Checklist rows for your in-scope pathway.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Integration | Components work separately | One traceable path commit → digest → deploy → status | Path verified by someone else from docs |
| Trusted build | Tag deployed; no provenance | Tests gate, digest, provenance verified, promotion gated | Verification enforced as required check; limits stated |
| Deployment control | CI has cluster rights; manual applies | Namespaced identity, admission policy, denied-action transcript | Policy tested in CI/admission parity; RBAC gaps closed or ledgered |
| State and failure | Stateless drills only | S2 + S3 with measured RTO/RPO and runbook | Off-cluster copy and rebuild drill; operator restore by independent person |
| Independent acceptance | Self-test or friend helped | Real second developer, zero undocumented help, findings recorded | Re-test after fixes; improvement evidenced |
| Architecture defence | Tool tour | ADRs with alternatives; claims ledger honest | Rehearsed against hostile questions; revisit triggers used |
| Demonstration | Unrehearsed | Timed, mapped to checklist, fallbacks, no secrets | Another person could run it from the docs |
| Honesty | Gaps hidden | Limitations register complete | Unproven items scheduled with evidence needed |

**Completion:** **Competent** on every row. A demo only you can drive, an acceptance with hints, stateless-only recovery, or a screenshot without digests/SHAs does **not** pass.

### Self-check

- Can you trace one digest from merge commit to running pod without a gap?
- Did your independent tester receive **any** undocumented help? (If yes: FAIL, fix, new participant.)
- Did you exercise a **stateful** failure, and can you state the measured RPO and what data was lost?
- Does any claim in your slides lack a `CLAIMS.md` entry or exceed its status?
- Can a developer change cluster state outside Git? Did you try, and is the result in the transcript?
- Did you delete any PVC to "fix" something? (That is a finding, not a recovery.)
- Are secrets absent from the repo and history (scan run)?
- Are optional tracks (AI, D08) marked `N/A — out of scope` rather than silently skipped?

### Example conclusion (evidence still required)

> Option A (kind + Flux; ADR 0306). `ledger` was created from golden path v1; a failing PR was blocked; merge `a1b2c3d` built `ghcr.io/…/ledger@sha256:9f…` with tests, SBOM and attestation; `harbour-verify-artifact` matched the commit; a fabricated digest was rejected by `promotion-verify`. The per-tenant reconciler cannot create namespaces; Kyverno rejected `nginx:latest`; developer view role could not delete pods (cluster-wide `view` recorded as a gap). Postgres StatefulSet drills: S2 pod loss — RTO 74 s, no restart loop, fingerprints equal; S3 damage — restore RTO 21 s, fingerprint matched backup, 25 post-backup rows lost (RPO exposure 3.4 min vs 5 min target). Node loss is **unproven**. Independent acceptance (backend developer, never saw Harbour): A1–A6 passed, 0 I2/I3, 2 S3 findings, independent time 96 min excluding 14 min documented waits. Defence rehearsal exposed an unanswered backup-failure question → freshness check added. P04 checklist ticked; AI and D08 `N/A — out of scope`.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Claim traceability | Verify attestation → commit → merge | Saying "CI built it" |
| Restrict deployment | Namespaced reconciler + admission policy | CI with cluster-admin |
| Recover from pod loss | Observe readiness and PVC reattach | Deleting the PVC |
| Recover from bad data | Restore from tested backup; quantify RPO | Assuming HEALTHY means correct |
| Prove it works | Independent developer, zero hints | Driving the demo yourself |
| Defend a design | Claims ledger with Proven/Partial/Unproven | Presenting aspiration as fact |
| Handle missing evidence | Say "unproven" and schedule it | Hiding it in the slides |

## Glossary

| Term | Meaning |
| --- | --- |
| Integrated outcome | The five-capability platform story: create, review/build, deploy, operate/recover, independent acceptance |
| Provenance (attestation) | Signed statement of how and from what an artefact was built |
| SBOM | Software bill of materials: inventory of an artefact's contents |
| Admission policy | Cluster-side rule that accepts or rejects objects at creation time |
| Tenant | Namespace plus the identity, quota and Flux object the platform grants a service |
| RPO / RTO | Acceptable data-loss window / acceptable recovery time |
| Fingerprint | Row count plus hash of a table, used to prove restored data matches an expected state |
| Claims ledger | Table of statements with evidence and Proven/Partial/Unproven status |
| ADR | Architecture decision record: context, decision, alternatives, consequences, evidence |
| Game day | Planned failure exercise run by someone other than the person responding |

## References

- [Kyverno documentation](https://kyverno.io/docs/) · [Flux multi-tenancy](https://fluxcd.io/flux/installation/configuration/multitenancy/) · [Flux — prune and garbage collection](https://fluxcd.io/flux/components/kustomize/kustomizations/)
- [GitHub artifact attestations](https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations) · [SLSA](https://slsa.dev/spec/v1.0/) · [Sigstore cosign](https://docs.sigstore.dev/cosign/overview/)
- [PostgreSQL — backup and restore](https://www.postgresql.org/docs/current/backup.html) · [Kubernetes StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [CNCF Platforms White Paper](https://tag-app-delivery.cncf.io/whitepapers/platforms/) · [ADR templates (adr.github.io)](https://adr.github.io/)
- [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) · [C03](../4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md) · [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) · [D07](../4.1%20DevOps/D07%20Observability.md) · [DevOps Exit Assessment](../4.1%20DevOps/DevOps%20Exit%20Assessment.md)

**Previous chapter:** [P03 — Internal Developer Platforms and Developer Experience](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) · **Course detail:** [P04](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P04%20Platform%20Architecture%20and%20Final%20Project.md) · **Programme:** [Final Project](../../1%20Foundational%20Documents/1.4%20Final%20Project.md) · **Checklist:** [Final Project Checklist · P04 and final demonstration](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
