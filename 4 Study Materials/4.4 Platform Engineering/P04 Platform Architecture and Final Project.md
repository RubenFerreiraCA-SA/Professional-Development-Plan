# Chapter 4 — Platform Architecture and Final Project (P04)

*Platform Engineering textbook · Chapter 4 of 4*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [P04 course detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P04%20Platform%20Architecture%20and%20Final%20Project.md) (about 40–50 hours, plus time to recruit an independent developer). |
| **Prerequisites** | [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md), [P02](P02%20Kubernetes%20Administration%20and%20Operations.md) and [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) (golden path, scaffold, self-service guardrails, trial protocol). The DevOps ([D04](../4.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md), [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md), [D07](../4.1%20DevOps/D07%20Observability.md)) and Cloud ([C02–C03](../4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md)) Harbour path is preferred. AI optional. |
| **Status** | Authored; corrections after audit `ff921e0` — **not signed off** |

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

`platform/bin/harbour-verify-artifact` turns "I trust the build" into a command that **binds** digest → expected source repository → approved workflow → expected commit (or rejects):

```bash
#!/usr/bin/env bash
set -euo pipefail
# usage: harbour-verify-artifact <oci-ref@sha256:…> [--expect-commit <sha>] [--expect-workflow <name>]
REF="${1:?}"; shift || true
EXPECT_COMMIT=""; EXPECT_WORKFLOW="${HARBOUR_EXPECT_WORKFLOW:-}"
EXPECT_REPO="${HARBOUR_EXPECT_REPO:-${GITHUB_REPOSITORY:-}}"
while [ $# -gt 0 ]; do
  case "$1" in
    --expect-commit) EXPECT_COMMIT="$2"; shift 2 ;;
    --expect-workflow) EXPECT_WORKFLOW="$2"; shift 2 ;;
    --expect-repo) EXPECT_REPO="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ "$REF" =~ @sha256:[0-9a-f]{64}$ ]] || { echo "ERROR: reference must be pinned by digest" >&2; exit 1; }
SUBJECT_DIGEST="${REF##*@}"
OWNER="${REF#ghcr.io/}"; OWNER="${OWNER%%/*}"
[ -n "$EXPECT_REPO" ] || { echo "ERROR: set HARBOUR_EXPECT_REPO or GITHUB_REPOSITORY" >&2; exit 1; }
[ -n "$EXPECT_WORKFLOW" ] || { echo "ERROR: set HARBOUR_EXPECT_WORKFLOW or --expect-workflow" >&2; exit 1; }
docker buildx imagetools inspect "$REF" >/dev/null
RAW="$(gh attestation verify "oci://$REF" --repo "$EXPECT_REPO" --format json)"
# Field paths differ across gh versions — pin yours after one inspect of $RAW.
COMMIT="$(printf '%s' "$RAW" | jq -r '.[0].verificationResult.signature.certificate.sourceRepositoryDigest // empty')"
WORKFLOW="$(printf '%s' "$RAW" | jq -r '.[0].verificationResult.signature.certificate.githubWorkflowName // empty')"
REPO="$(printf '%s' "$RAW" | jq -r '.[0].verificationResult.signature.certificate.sourceRepositoryURI // empty')"
printf 'subject=%s\nrepo=%s\nworkflow=%s\ncommit=%s\n' "$SUBJECT_DIGEST" "$REPO" "$WORKFLOW" "$COMMIT"
echo "$REPO" | grep -q "$EXPECT_REPO" || { echo "FAIL: attestation repo mismatch (want $EXPECT_REPO)" >&2; exit 1; }
[ "$WORKFLOW" = "$EXPECT_WORKFLOW" ] || { echo "FAIL: workflow mismatch want=$EXPECT_WORKFLOW got=$WORKFLOW" >&2; exit 1; }
if [ -n "$EXPECT_COMMIT" ]; then
  case "$COMMIT" in
    "$EXPECT_COMMIT"|sha1:"$EXPECT_COMMIT"|sha256:"$EXPECT_COMMIT") ;;
    *) echo "FAIL: commit mismatch want=$EXPECT_COMMIT got=$COMMIT" >&2; exit 1 ;;
  esac
fi
echo "VERIFIED: $REF bound to $EXPECT_REPO / $EXPECT_WORKFLOW / ${EXPECT_COMMIT:-any-recorded-commit}"
```

An attestation that only proves “some workflow in this owner built something” is **not** enough for promotion.

Make promotion **impossible without verification** with an **always-on** required check (D04 lesson: path filters must not be the required check itself). `.github/workflows/promotion-verify.yml`:

```yaml
name: promotion-verify
on:
  pull_request:          # no paths: filter — required checks must always report
permissions:
  contents: read
  attestations: read
  packages: read
jobs:
  gate:
    runs-on: ubuntu-latest
    env:
      GH_TOKEN: ${{ github.token }}
      HARBOUR_EXPECT_REPO: ${{ github.repository }}
      HARBOUR_EXPECT_WORKFLOW: reusable-release.yml   # set to your real release workflow file/name
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - name: Substantive verify only when promotion overlays change
        run: |
          set -euo pipefail
          mapfile -t FILES < <(git diff --name-only "origin/${{ github.base_ref }}"...HEAD -- \
            'deploy/*/overlays/*/kustomization.yaml' || true)
          if [ "${#FILES[@]}" -eq 0 ]; then
            echo "No promotion overlays changed — gate reports success (D04 always-on pattern)."
            exit 0
          fi
          for f in "${FILES[@]}"; do
            grep -q UNPROMOTED "$f" && { echo "skip $f (unpromoted sentinel)"; continue; }
            img="$(sed -nE 's/^[[:space:]]+newName:[[:space:]]+(.*)$/\1/p' "$f" | head -1)"
            d="$(grep -oE 'digest: sha256:[0-9a-f]{64}' "$f" | head -1 | cut -d' ' -f2)"
            [ -n "$img" ] && [ -n "$d" ] || { echo "FAIL: cannot parse image/digest in $f"; exit 1; }
            platform/bin/harbour-verify-artifact "${img}@${d}" \
              --expect-workflow "$HARBOUR_EXPECT_WORKFLOW"
          done
```

Test with a **fabricated digest** — the gate must fail. Test with an unrelated docs-only PR — the gate must succeed (not stay pending/skipped).

### 4.4.4 Review and branch protection are part of the trust story

Verify, don't assume (D01/D04):

```bash
# assumes the repository name equals the directory name; otherwise set REPO explicitly
gh api "repos/$GH_OWNER/$(basename "$HARBOUR_ROOT")/branches/main/protection" \
  | jq '{reviews: .required_pull_request_reviews.required_approving_review_count,
         codeowners: .required_pull_request_reviews.require_code_owner_reviews,
         checks: .required_status_checks.contexts, admins: .enforce_admins.enabled}'
```

Required checks must include the service validate job, `policy` and `promotion-verify` (**always reports**). If your plan cannot enforce this, write the gap into `LIMITATIONS.md` with a compensating control (e.g. you do not self-approve; a second reviewer is the independent tester).

**Practice — reproduce:** (1) Open a PR that breaks a test; show it is unmergeable. (2) Fix, merge, and record commit SHA, workflow run URL and digest. (3) Run `harbour-verify-artifact` with `--expect-commit` / `--expect-workflow` and show a mismatched workflow is rejected. (4) Promote a **fabricated** digest and show `promotion-verify` fails. (5) Open a docs-only PR and show `promotion-verify` still reports success.

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

`platform/policy/harbour-baseline.yaml` (rule-level `failureAction` requires a recent Kyverno; older releases use `spec.validationFailureAction` — check your version's docs). Enable **Pod controller autogeneration** so matching `Pod` also evaluates generated Pod templates from Deployments/StatefulSets/Jobs — required for CI `kyverno apply` on rendered Kustomize output:

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

Confirm autogen is active for this policy version (`kubectl get clusterpolicy harbour-baseline -o yaml | grep -A20 autogen` or check Kyverno docs for your chart). If your Kyverno version does **not** autogen from Pod→Deployment, change `kinds` to include `Deployment`, `StatefulSet` and `Job` explicitly — then re-run the negative fixtures below.

**Relationship to P02:** P02 §2.4.3 shows a built-in `ValidatingAdmissionPolicy` for digest-addressed **Deployments**, and says plainly that StatefulSets, Jobs and bare Pods are not covered. Kyverno's Pod-level rules (with autogen) cover them. Use one mechanism per rule, or run both and note the overlap in ADR 0309. NetworkPolicy and Pod Security admission remain additional controls — list any you did *not* apply in `LIMITATIONS.md`.

Commit it to `platform/policy/` and reconcile it through the platform Kustomization. **CI and admission must reject the same forbidden configurations.** A green `kyverno apply` with zero applicable rules is a false pass.

`platform/bin/harbour-policy-check` (used by the required `policy` job):

```bash
#!/usr/bin/env bash
set -euo pipefail
NAME="${1:?service}"
POLICY="platform/policy/harbour-baseline.yaml"
FIXDIR="platform/policy/fixtures"
mkdir -p "$FIXDIR"
# 1) Positive: rendered overlay must pass, and report which rules applied.
kubectl kustomize "deploy/$NAME/overlays/staging" > /tmp/rendered.yaml
OUT="$(kyverno apply "$POLICY" --resource /tmp/rendered.yaml --policy-report 2>&1)" || {
  echo "$OUT"; echo "FAIL: rendered overlay rejected"; exit 1; }
echo "$OUT"
echo "$OUT" | grep -Eqi 'require-image-digest|pass|Pass' \
  || { echo "FAIL: digest rule not evidently evaluated — inspect kyverno output; do not treat skip as pass"; exit 1; }

# 2) Negative fixtures — each MUST fail both CLI apply and (separately) live admission.
cat > "$FIXDIR/bad-mutable-tag.yaml" <<'EOF'
apiVersion: v1
kind: Pod
metadata: {name: bad-tag, namespace: default}
spec:
  containers: [{name: c, image: nginx:latest}]
EOF
cat > "$FIXDIR/bad-root-no-limits.yaml" <<'EOF'
apiVersion: v1
kind: Pod
metadata: {name: bad-root, namespace: default}
spec:
  containers:
    - name: c
      image: nginx@sha256:0000000000000000000000000000000000000000000000000000000000000001
EOF

kyverno apply "$POLICY" --resource "$FIXDIR/bad-mutable-tag.yaml" && {
  echo "FAIL: mutable-tag fixture was accepted by CLI"; exit 1; }
kyverno apply "$POLICY" --resource "$FIXDIR/bad-root-no-limits.yaml" && {
  echo "FAIL: root/no-limits fixture was accepted by CLI"; exit 1; }

# 3) Live admission must reject the same shapes (cluster with policy reconciled).
NS="${NAME}-staging"
kubectl -n "$NS" delete pod policy-probe-bad --ignore-not-found --wait=false
if kubectl -n "$NS" run policy-probe-bad --image=nginx:latest --restart=Never 2>/tmp/adm.err; then
  echo "FAIL: admission accepted nginx:latest"; kubectl -n "$NS" delete pod policy-probe-bad --ignore-not-found; exit 1
fi
grep -qiE 'digest|harbour-baseline|blocked|denied|violation' /tmp/adm.err \
  || { echo "FAIL: admission error did not cite policy (got: $(cat /tmp/adm.err))"; exit 1; }
echo "OK: CI CLI and admission reject the same forbidden shapes for $NAME"
```

**Required standard for sign-off:** *the same forbidden configuration fails in CI and at Kubernetes admission*, and skipped/unmatched rules are not counted as passes.

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
  kubectl -n "${SVC}-staging" run bad --image=nginx:latest --as="$SA" 2>&1 | tee /tmp/adm-tag.txt | tail -n 3
  grep -qiE 'digest|harbour-baseline|denied|violation|blocked' /tmp/adm-tag.txt
  echo "# policy CLI rejects the same fixture"
  platform/bin/harbour-policy-check "$SVC"
  echo "# promotion to an unapproved environment is refused"
  platform/bin/harbour-promote "$SVC" prod "sha256:$(printf '0%.0s' {1..64})" 2>&1
} | tee docs/final/drills/access-denials.txt
```

Expect `yes`, `no`, `no`, `no`, an admission denial quoting the policy message, a successful `harbour-policy-check`, and the promotion error. If any `no` is `yes`, you have found a privilege gap — fix it or record it.

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
  volumeClaimTemplates:
    - metadata: {name: data}
      spec: {accessModes: [ReadWriteOnce], resources: {requests: {storage: 1Gi}}}
---
apiVersion: v1
kind: Service
metadata: {name: postgres}
spec: {clusterIP: None, selector: {app: postgres}, ports: [{name: pg, port: 5432}]}
---
# Backup PVC is separate from the data volume and used only by backup Jobs.
# Do NOT mount the same RWO PVC on both the StatefulSet and a concurrent Job unless
# you have proved your StorageClass allows it (kind local-path typically does not).
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-backup
  annotations: {kustomize.toolkit.fluxcd.io/prune: disabled}
spec: {accessModes: [ReadWriteOnce], resources: {requests: {storage: 1Gi}}}
```

`platform/components/postgres/backup-cronjob.yaml` (training cadence: every 5 minutes). The Job alone mounts the backup PVC; it connects to Postgres over the network:

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

**Backup durability bar (compulsory for any recovery claim):** (1) prove at least **two** successful CronJob runs produce distinct dump files; (2) copy a chosen dump **off-cluster** (`kubectl cp` to `~/harbour-backups/`); (3) restore that chosen file later. A CronJob object alone is not evidence.

Add `kustomization.yaml` listing both files; include the component in `deploy/$SVC/overlays/staging/kustomization.yaml`:

```yaml
resources: [../../base, ../../../../platform/components/postgres]
patches:
  - target: {kind: Deployment, name: ledger}   # use your $SVC name
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env
        value:
          - {name: DATABASE_HOST, value: postgres}
          - {name: DATABASE_USER, value: harbour}
          - {name: DATABASE_NAME, value: harbour}
          - {name: DATABASE_PASSWORD, valueFrom: {secretKeyRef: {name: postgres-credentials, key: password}}}
```

Make readiness and the **business data contract** real. TCP-only `/ready` is insufficient for P04. Replace the relevant handlers in `services/$SVC/main.py`:

```python
import os, psycopg
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI()

def _dsn() -> str:
    return (
        f"host={os.environ['DATABASE_HOST']} dbname={os.environ['DATABASE_NAME']} "
        f"user={os.environ['DATABASE_USER']} password={os.environ['DATABASE_PASSWORD']}"
    )

def _conn():
    return psycopg.connect(_dsn(), connect_timeout=2)

@app.on_event("startup")
def migrate():
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS ledger_entries(
                 id bigserial PRIMARY KEY,
                 note text NOT NULL,
                 created_at timestamptz NOT NULL DEFAULT now())"""
        )
        c.commit()

@app.get("/ready")
def ready():
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ready", "database": "query_ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not-ready", "database": str(e.__class__.__name__)})

class EntryIn(BaseModel):
    note: str = Field(min_length=1, max_length=200)

@app.post("/v1/entries")
def write_entry(body: EntryIn):
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO ledger_entries(note) VALUES (%s) RETURNING id, note, created_at",
            (body.note,),
        )
        row = cur.fetchone()
        c.commit()
    return {"id": row[0], "note": row[1], "created_at": row[2].astimezone(timezone.utc).isoformat()}

@app.get("/v1/entries/{entry_id}")
def read_entry(entry_id: int):
    with _conn() as c, c.cursor() as cur:
        cur.execute("SELECT id, note, created_at FROM ledger_entries WHERE id=%s", (entry_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "missing")
    return {"id": row[0], "note": row[1], "created_at": row[2].astimezone(timezone.utc).isoformat()}

@app.get("/v1/entries")
def list_entries():
    with _conn() as c, c.cursor() as cur:
        cur.execute("SELECT id, note, created_at FROM ledger_entries ORDER BY id")
        rows = cur.fetchall()
    return {
        "count": len(rows),
        "entries": [
            {"id": r[0], "note": r[1], "created_at": r[2].astimezone(timezone.utc).isoformat()}
            for r in rows
        ],
    }
```

Ship through the **normal** path (PR → build → verify → promote). Add `psycopg[binary]` to the service dependencies. **Honest limits:** single replica; kind storage is local disk; in-cluster backup PVC still shares cluster fate until you copy dumps off-cluster.

### 4.6.2 Define health and recovery targets first

Write them in ADR 0310/0311 *before* injecting failures:

| Signal | Where | Healthy |
| --- | --- | --- |
| Pod Ready / restarts | `harbour-status`, `kubectl get pods` | Ready; restarts stable; exit 0 |
| Readiness body | `/ready` | `database: query_ok` (authenticated query, not TCP) |
| Application contract | `POST/GET /v1/entries` | write then read returns the same note |
| Service endpoints | `kubectl get endpoints $SVC` | non-empty |
| Backup freshness | newest successful Job + off-cluster copy | < 10 min old; file exists outside cluster |
| SLI (if D07 stack present) | `docs/observability/slo-harbour.md` pattern | availability objective met |

Targets (training, state yours): **RTO ≤ 3 min** until `/ready` is `query_ok` **and** `GET /v1/entries` succeeds; **RPO** measured as wall-clock gap between last acknowledged write timestamp and backup completion timestamp (not only row counts). They are *hypotheses* until measured.

### 4.6.3 Stateless drill (brief)

Delete one `$SVC` pod; with two replicas the Service keeps serving (D06 §6.8.1). Record time to full readiness. This is C03-class evidence — necessary, not sufficient.

### 4.6.4 Stateful drills — the script

`platform/drills/stateful-drill.sh` (run phases in order). Evidence is **application HTTP** plus SQL support — SQL alone does not pass:

```bash
#!/usr/bin/env bash
set -euo pipefail
NS="${1:?namespace}"; PHASE="${2:?phase}"; SVC="${SVC:?set SVC}"
OUT="docs/final/drills/stateful-$(date -u +%Y%m%d)"; mkdir -p "$OUT" ~/harbour-backups
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$OUT/timeline.log"; }
# Port-forward the app Service for HTTP checks (business path).
PF_PID=""
app_pf() {
  kubectl -n "$NS" port-forward "svc/$SVC" 18080:80 >/tmp/pf-ledger.log 2>&1 & PF_PID=$!
  for i in $(seq 1 30); do curl -sf http://127.0.0.1:18080/ready >/dev/null && return 0; sleep 1; done
  return 1
}
app_stop_pf() { [ -n "${PF_PID}" ] && kill "$PF_PID" 2>/dev/null || true; PF_PID=""; }
trap app_stop_pf EXIT
http() { curl -sf -H 'content-type: application/json' "$@"; }
app_count() { http http://127.0.0.1:18080/v1/entries | python3 -c 'import sys,json; print(json.load(sys.stdin)["count"])'; }
app_notes() { http http://127.0.0.1:18080/v1/entries | python3 -c 'import sys,json; print(",".join(e["note"] for e in json.load(sys.stdin)["entries"]))'; }
case "$PHASE" in
  seed)
    app_pf
    for i in $(seq 1 20); do
      http -d "{\"note\":\"A-$i\"}" http://127.0.0.1:18080/v1/entries >/dev/null
    done
    date -u +%FT%TZ > "$OUT/last_ack_before_backup.txt"
    log "seeded via HTTP count=$(app_count) last_ack=$(cat "$OUT/last_ack_before_backup.txt")"
    app_stop_pf ;;
  backup)
    J="manual-backup-$(date +%s)"
    kubectl -n "$NS" create job --from=cronjob/postgres-backup "$J"
    kubectl -n "$NS" wait --for=condition=complete "job/$J" --timeout=120s
    date -u +%FT%TZ > "$OUT/backup_completed_at.txt"
    # Copy the newest dump off-cluster (compulsory for recovery claims).
    POD="$(kubectl -n "$NS" get pods -l job-name="$J" -o jsonpath='{.items[0].metadata.name}')"
    DUMP="$(kubectl -n "$NS" exec "$POD" -- sh -c 'ls -1t /backup/*.dump | head -1')"
    kubectl -n "$NS" cp "$POD:$DUMP" "$HOME/harbour-backups/$(basename "$DUMP")"
    echo "$HOME/harbour-backups/$(basename "$DUMP")" > "$OUT/offcluster-backup.path"
    app_pf; app_count > "$OUT/count-at-backup.txt"; app_notes > "$OUT/notes-at-backup.txt"; app_stop_pf
    log "backup $J complete at $(cat "$OUT/backup_completed_at.txt"); offcluster=$(cat "$OUT/offcluster-backup.path"); http_count=$(cat "$OUT/count-at-backup.txt")" ;;
  write-after)
    app_pf
    for i in $(seq 1 5); do
      RESP="$(http -d "{\"note\":\"B-$i\"}" http://127.0.0.1:18080/v1/entries)"
      echo "$RESP" | tee -a "$OUT/ack-after-backup.jsonl"
      echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["created_at"])' \
        >> "$OUT/ack_timestamps_after_backup.txt"
    done
    date -u +%FT%TZ > "$OUT/last_ack_before_incident.txt"
    app_count > "$OUT/count-before-incident.txt"
    log "wrote B via HTTP; count=$(cat "$OUT/count-before-incident.txt"); last_ack=$(cat "$OUT/last_ack_before_incident.txt")"
    app_stop_pf ;;
  kill-db)
    app_pf || true
    log "S2 inject: delete pod postgres-0"
    T0=$(date +%s); kubectl -n "$NS" delete pod postgres-0 --wait=false
    # Wait until app readiness fails (HTTP 503) — service-level detection.
    until ! curl -sf http://127.0.0.1:18080/ready >/dev/null; do
      [ $(( $(date +%s) - T0 )) -ge 90 ] && break; sleep 1
    done
    log "S2 detected not-ready after $(( $(date +%s) - T0 ))s"
    kubectl -n "$NS" wait --for=condition=ready pod/postgres-0 --timeout=180s
    until curl -sf http://127.0.0.1:18080/ready | grep -q query_ok; do sleep 2; done
    GOT="$(app_count)"; WANT="$(cat "$OUT/count-before-incident.txt")"
    log "S2 recovered RTO=$(( $(date +%s) - T0 ))s http_count=$GOT expected=$WANT"
    [ "$GOT" = "$WANT" ] || { log "S2 HTTP DATA MISMATCH"; exit 1; }
    app_stop_pf ;;
  destroy)
    app_pf
    # Logical damage through SQL (simulates bad migration); app still "healthy" but wrong.
    kubectl -n "$NS" exec postgres-0 -- psql -U harbour -d harbour -c \
      "DELETE FROM ledger_entries WHERE note LIKE 'A-%' AND id % 2 = 0"
    log "S3 damaged; http_count=$(app_count) (pod may still be Ready)"
    app_stop_pf ;;
  restore)
    T0=$(date +%s)
    BACKUP="$(cat "$OUT/offcluster-backup.path")"
    [ -f "$BACKUP" ] || { log "missing off-cluster backup"; exit 1; }
    # Restore chosen off-cluster dump into the live database (training path).
    kubectl -n "$NS" cp "$BACKUP" "postgres-0:/tmp/restore.dump"
    kubectl -n "$NS" exec postgres-0 -- \
      pg_restore -U harbour -d harbour --clean --if-exists /tmp/restore.dump
    app_pf
    until curl -sf http://127.0.0.1:18080/ready | grep -q query_ok; do sleep 2; done
    GOT="$(app_count)"; WANT="$(cat "$OUT/count-at-backup.txt")"
    # RPO in time: gap between last acknowledged post-backup write and backup completion.
    python3 - <<PY | tee -a "$OUT/rpo-report.txt"
from datetime import datetime, timezone
backup = datetime.fromisoformat(open("$OUT/backup_completed_at.txt").read().strip().replace("Z", "+00:00"))
acks = [datetime.fromisoformat(l.strip().replace("Z", "+00:00"))
        for l in open("$OUT/ack_timestamps_after_backup.txt") if l.strip()]
last = max(acks)
gap = (last - backup.astimezone(timezone.utc)).total_seconds()
before = int(open("$OUT/count-before-incident.txt").read())
at_b = int(open("$OUT/count-at-backup.txt").read())
print(f"RPO_time_seconds={gap:.1f} (last_ack_after_backup - backup_completed)")
print(f"RPO_rows_lost={before - at_b}")
PY
    log "S3 restore service-RTO=$(( $(date +%s) - T0 ))s http_count=$GOT expected=$WANT"
    [ "$GOT" = "$WANT" ] || { log "S3 HTTP RESTORE MISMATCH"; exit 1; }
    # Spot-check one known note through HTTP
    http http://127.0.0.1:18080/v1/entries | grep -q '"note": "A-1"' || { log "missing A-1 via HTTP"; exit 1; }
    app_stop_pf ;;
  *) echo "phases: seed backup write-after kill-db destroy restore" >&2; exit 2 ;;
esac
```

Run it (Postgres and ledger must be healthy first; run `harbour-status "$SVC"` and confirm exit 0):

```bash
NS="${SVC}-staging"
# Prove recurring backups before the incident drill:
kubectl -n "$NS" create job --from=cronjob/postgres-backup "warmup-a-$(date +%s)"
sleep 30
kubectl -n "$NS" create job --from=cronjob/postgres-backup "warmup-b-$(date +%s)"
for p in seed backup write-after kill-db destroy restore; do platform/drills/stateful-drill.sh "$NS" "$p"; done
```

What each drill proves — and what it does not:

| Drill | Injects | Expected behaviour | Proves | Does **not** prove |
| --- | --- | --- | --- | --- |
| **S2 pod loss** | Delete `postgres-0` | `/ready` → 503 (`query_ok` lost); Service drops endpoints; recreate; HTTP counts match | Self-healing + data durability **through the app** | Node/disk loss, HA |
| **S3 bad migration** | Delete rows in DB | App may stay Ready yet HTTP list is wrong; restore from **off-cluster** dump; HTTP matches backup-time notes | Restorable backup; **time-based RPO** + row loss | PITR, clean-cluster rebuild |
| **Prune hazard** (read) | Remove StatefulSet from Git | Data PVC survives; annotated backup PVC not pruned | Why prune must never target data | Full platform GitOps rebuild (see P02 §2.7.4) |

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
