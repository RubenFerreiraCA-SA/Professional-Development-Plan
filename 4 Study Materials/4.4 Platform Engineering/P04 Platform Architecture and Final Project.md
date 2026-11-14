# Chapter 4 — Platform Architecture and Final Project (P04)

*Platform Engineering textbook · Chapter 4 of 4*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [P04 course detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P04%20Platform%20Architecture%20and%20Final%20Project.md) (about 40–50 hours, plus time to recruit an independent developer). |
| **Prerequisites** | [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md), [P02](P02%20Kubernetes%20Administration%20and%20Operations.md) and [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) (golden path, scaffold, self-service guardrails, trial protocol). The DevOps ([D04](../4.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md), [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md), [D07](../4.1%20DevOps/D07%20Observability.md)) and Cloud ([C02–C03](../4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md)) Harbour path is preferred. AI optional. |
| **Status** | Authored; Gate 1 suites ready — **documentation review pending** (not signed off; clean-room not implied). Charter: [GATE1-ACCEPTANCE-CHARTER.md](../../1%20Foundational%20Documents/GATE1-ACCEPTANCE-CHARTER.md). Canonical scripts: [reference/harbour/](../../reference/harbour/) |

> **Canonical Harbour examples** live in [`../../reference/harbour/`](../../reference/harbour/) — textbooks cite those files as source of truth. When a fenced example and a reference file diverge, trust the reference tree.

### Dependency and deliverables map

| | |
| --- | --- |
| **Prior chapters** | P01–P03 (golden path, tenants, Flux); D04/D06 (trusted build, GitOps); C03 optional |
| **Files you create** | ADRs 0306–0312; `docs/final/INTEGRATED-OUTCOME.md`; policy + promotion workflows; Postgres component; stateful drill evidence; acceptance + defence packs |
| **Copy from reference** | [`reference/harbour/`](../../reference/harbour/) scripts, workflows, fixtures, `TOOLCHAIN.md` |
| **End state** | Five integrated outcomes evidenced; independent acceptance recorded; Final Project P04 rows defensible |

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
docs/final/drills/stateful-<RUN_ID>/
```

### 4.2.3 The limitations register

Create `docs/final/LIMITATIONS.md` now, not the night before the demo. One row per honest gap: *Gap · Impact · Compensating control · Would fix by*. Typical entries: kind is single-node; `view` developer role is cluster-wide; secrets are base64 in etcd; backups share the cluster's fate; attestations depend on the CI platform plan.

**Practice — reproduce:** Write ADR 0306 and 0310 with real values from your environment. Every `…` must be provable from a command or file.

**Verify:** A reader can find, for each ADR, an evidence link and a stated limitation.

---

## Section 4.3 — Outcome 1: a developer creates a service

> **Integrated pathway (run once before claiming P03+P04 together):** boundaries between chapters are where earlier audits found defects. Prefer this sequence over isolated chapter checks: (1) `harbour-new-service` from P03’s CLI; (2) rendered manifests pass restricted PSA dry-run **and** `harbour-policy-check` / Kyverno; (3) build + attest + release-manifest artifact; (4) promote with attestation checked against `platform/policy/approved-signer-workflows.txt` (fully-qualified signer paths, not display names); (5) Flux deploys the exact verified digest (`imageID` match); (6) add the Postgres dependency and re-run allow/deny NetworkPolicy matrix; (7) seed → verified backup → damage → Flux-suspended maintenance → restore → prove snapshot equivalence with `restore-verify-before-resume.sh`; (8) only then resume reconciliation and confirm the app serves the restored records. Record the run under `docs/final/INTEGRATED-OUTCOME.md`.

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

Add tests as a gate, build with provenance/SBOM, attest the digest, and **produce the release manifest** that promotion requires. Replace the `release` job in `.github/workflows/service-release.yml`:

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
      image: ${{ steps.meta.outputs.image }}
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
      # Release-manifest producer (immutable CI artifact — not a silent laptop step).
      - name: Write release manifest
        env:
          SVC: ${{ inputs.service }}
          DIGEST: ${{ steps.push.outputs.digest }}
          IMAGE: ${{ steps.meta.outputs.image }}
        run: |
          set -euo pipefail
          mkdir -p "docs/releases/${SVC}"
          # digest is already "sha256:…"
          MAN="docs/releases/${SVC}/${DIGEST}.json"
          # workflow = display name (informational). signer_workflow = fully-qualified
          # path used by gh attestation verify --signer-workflow (security principal).
          jq -n \
            --arg commit "${{ github.sha }}" \
            --arg workflow "${{ github.workflow }}" \
            --arg signer_workflow "${{ github.repository }}/.github/workflows/service-release.yml" \
            --arg image "${IMAGE}@${DIGEST}" \
            --arg run "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}" \
            --arg ref "${{ github.ref }}" \
            --arg event "${{ github.event_name }}" \
            '{commit:$commit, workflow:$workflow, signer_workflow:$signer_workflow, image:$image, run_url:$run, ref:$ref, event:$event}' > "$MAN"
          echo "Wrote $MAN"
      - uses: actions/upload-artifact@v4
        with:
          name: release-manifest-${{ inputs.service }}-${{ github.sha }}
          path: docs/releases/${{ inputs.service }}/${{ steps.push.outputs.digest }}.json
          if-no-files-found: error
          retention-days: 30
```

**Release-manifest lifecycle (required):**

| Stage | Who / what | Artifact |
| --- | --- | --- |
| Produce | Release workflow after push+attest | `docs/releases/<svc>/<digest>.json` uploaded as a workflow artifact |
| Review into Git | Human opens promotion PR; includes the downloaded manifest **and** the overlay digest pin | Manifest content must match attestation (promotion-verify enforces) |
| Consume | `promotion-verify` + `harbour-verify-artifact` | Exact commit/workflow/image; no undocumented copy |

Callers (`<svc>-release.yml`) must grant `id-token: write` and `attestations: write`, and must trigger only on **`push` to `main`** (no `workflow_dispatch` — see P03). **Limitation:** private-repo attestations may need a paid plan; document the gap or use cosign keyless if unavailable.

### 4.4.3 Worked example — verify before you promote

`platform/bin/harbour-verify-artifact` binds digest → expected source repository → approved workflow → **required** commit on the **protected release branch** (rejects if any mismatch). An attestation alone is not enough: the attested source commit must appear in `main` history.

Release workflows must write `docs/releases/<svc>/<digest>.json` (example: `{"commit":"<sha>","workflow":"<name>","image":"<ref@digest>","ref":"refs/heads/main","event":"push"}`) so promotion can look up the allowed source commit.

```bash
#!/usr/bin/env bash
set -euo pipefail
# usage: harbour-verify-artifact <oci-ref@sha256:…> --expect-commit <sha> \
#          (--approved-workflows-file <path> | --expect-workflow <name>) \
#          [--require-branch main]
REF="${1:?}"; shift
EXPECT_COMMIT=""; EXPECT_WORKFLOW=""; APPROVED_FILE=""
REQUIRE_BRANCH="${HARBOUR_REQUIRE_BRANCH:-main}"
EXPECT_REPO="${HARBOUR_EXPECT_REPO:-${GITHUB_REPOSITORY:-}}"
while [ $# -gt 0 ]; do
  case "$1" in
    --expect-commit) EXPECT_COMMIT="$2"; shift 2 ;;
    --expect-workflow) EXPECT_WORKFLOW="$2"; shift 2 ;;
    --approved-workflows-file) APPROVED_FILE="$2"; shift 2 ;;
    --expect-repo) EXPECT_REPO="$2"; shift 2 ;;
    --require-branch) REQUIRE_BRANCH="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ "$REF" =~ @sha256:[0-9a-f]{64}$ ]] || { echo "ERROR: reference must be pinned by digest" >&2; exit 1; }
SUBJECT_DIGEST="${REF##*@}"
[ -n "$EXPECT_REPO" ] || { echo "ERROR: set HARBOUR_EXPECT_REPO or GITHUB_REPOSITORY" >&2; exit 1; }
[ -n "$EXPECT_COMMIT" ] || { echo "ERROR: --expect-commit required for promotion" >&2; exit 1; }
[ -n "$APPROVED_FILE" ] || [ -n "$EXPECT_WORKFLOW" ] \
  || { echo "ERROR: pass --approved-workflows-file (preferred) or --expect-workflow" >&2; exit 1; }
docker buildx imagetools inspect "$REF" >/dev/null
# Pin gh ≥ 2.102.0 (patches workflow-prefix and case-insensitive source-ref matching).
GH_VER="$(gh --version | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
python3 - "$GH_VER" <<'PY' || exit 1
import sys
want = (2, 102, 0)
got = tuple(int(x) for x in sys.argv[1].split("."))
if got < want:
    print(f"FAIL: gh {sys.argv[1]} < 2.102.0 — upgrade (signer-workflow/source-ref security fixes)", file=sys.stderr)
    sys.exit(1)
print(f"OK: gh {sys.argv[1]} meets minimum 2.102.0")
PY
gh attestation verify --help >/dev/null 2>&1 \
  || { echo "FAIL: gh missing 'attestation verify'" >&2; exit 1; }
# Allow-list entries are *fully-qualified signing-workflow paths* for --signer-workflow,
# e.g. owner/repo/.github/workflows/service-release.yml — NOT githubWorkflowName display names.
if [ -n "$APPROVED_FILE" ]; then
  [ -f "$APPROVED_FILE" ] || { echo "FAIL: missing allow-list $APPROVED_FILE" >&2; exit 1; }
  mapfile -t APPROVED_SIGNERS < <(grep -vE '^\s*(#|$)' "$APPROVED_FILE")
  [ "${#APPROVED_SIGNERS[@]}" -ge 1 ] || { echo "FAIL: empty allow-list $APPROVED_FILE" >&2; exit 1; }
elif [ -n "$EXPECT_WORKFLOW" ]; then
  APPROVED_SIGNERS=("$EXPECT_WORKFLOW")
fi
for s in "${APPROVED_SIGNERS[@]}"; do
  [[ "$s" == */.github/workflows/*.yml ]] || [[ "$s" == */.github/workflows/*.yaml ]] \
    || { echo "FAIL: allow-list entry must be owner/repo/.github/workflows/file.yml (got: $s)" >&2; exit 1; }
done
VERIFY_ARGS=(--repo "$EXPECT_REPO" --format json
  --source-digest "$EXPECT_COMMIT"
  --source-ref "refs/heads/${REQUIRE_BRANCH}")
RAW=""; MATCHED_SIGNER=""
for signer in "${APPROVED_SIGNERS[@]}"; do
  set +e
  RAW="$(gh attestation verify "oci://$REF" "${VERIFY_ARGS[@]}" --signer-workflow "$signer" 2>/tmp/harbour-attest.err)"
  rc=$?
  set -e
  if [ "$rc" -eq 0 ] && [ -n "$RAW" ]; then MATCHED_SIGNER="$signer"; break; fi
done
[ -n "$MATCHED_SIGNER" ] || {
  echo "FAIL: no attestation matched approved signer-workflow + source-ref/digest" >&2
  cat /tmp/harbour-attest.err >&2 || true
  exit 1
}
# Certificate fields: display name is informational; signer path was enforced by gh.
# Still require ref/trigger/commit/repo — absent fields fail (no soft skip).
printf '%s' "$RAW" > /tmp/harbour-attest.json
SELECTED="$(MATCHED_SIGNER="$MATCHED_SIGNER" EXPECT_COMMIT="$EXPECT_COMMIT" \
  REQUIRE_BRANCH="$REQUIRE_BRANCH" EXPECT_REPO="$EXPECT_REPO" python3 - <<'PY'
import json, os, sys
data = json.load(open("/tmp/harbour-attest.json"))
want_signer = os.environ["MATCHED_SIGNER"].lower()
want_commit = os.environ["EXPECT_COMMIT"]
want_ref = "refs/heads/" + os.environ["REQUIRE_BRANCH"]
want_repo = os.environ["EXPECT_REPO"].lower()

def canon(r):
    r = (r or "").lower()
    for p in ("https://github.com/", "git@github.com:"):
        if r.startswith(p): r = r[len(p):]
    return r.removesuffix(".git").rstrip("/")

for item in data if isinstance(data, list) else [data]:
    cert = (((item or {}).get("verificationResult") or {}).get("signature") or {}).get("certificate") or {}
    display = cert.get("githubWorkflowName") or ""
    # Job/reusable workflow identity when present (path-like); do not equate to display name.
    job_wf = (cert.get("jobWorkflowRef") or cert.get("githubWorkflowFileRef") or "").lower()
    commit = cert.get("sourceRepositoryDigest") or ""
    ref = cert.get("githubWorkflowRef") or ""
    trigger = cert.get("githubWorkflowTrigger") or ""
    repo = canon(cert.get("sourceRepositoryURI") or "")
    commit_ok = commit in {want_commit, f"sha1:{want_commit}", f"sha256:{want_commit}"}
    if not commit_ok: continue
    if not ref or ref != want_ref: continue
    if not trigger or trigger != "push": continue
    if not repo or repo != canon(want_repo): continue
    # If the certificate exposes a path-like job workflow ref, it must match the allow-listed signer.
    if job_wf and want_signer not in job_wf and job_wf not in want_signer:
        continue
    json.dump({
        "signer_workflow": want_signer,
        "display_name": display,
        "commit": commit, "ref": ref, "trigger": trigger, "repo": repo,
    }, sys.stdout)
    sys.exit(0)
print("FAIL: attestations returned but certificate identity contract unmet", file=sys.stderr)
sys.exit(1)
PY
)" || exit 1
SIGNER="$(printf '%s' "$SELECTED" | jq -r .signer_workflow)"
DISPLAY="$(printf '%s' "$SELECTED" | jq -r .display_name)"
COMMIT="$(printf '%s' "$SELECTED" | jq -r .commit)"
ATT_REF="$(printf '%s' "$SELECTED" | jq -r .ref)"
ATT_TRIGGER="$(printf '%s' "$SELECTED" | jq -r .trigger)"
REPO="$(printf '%s' "$SELECTED" | jq -r .repo)"
printf 'subject=%s\nrepo=%s\nsigner_workflow=%s\ndisplay_name=%s\ncommit=%s\nref=%s\ntrigger=%s\n' \
  "$SUBJECT_DIGEST" "$REPO" "$SIGNER" "$DISPLAY" "$COMMIT" "$ATT_REF" "$ATT_TRIGGER"
STRIP_COMMIT="${COMMIT#sha1:}"; STRIP_COMMIT="${STRIP_COMMIT#sha256:}"
git fetch --no-tags origin "refs/heads/${REQUIRE_BRANCH}:refs/remotes/origin/${REQUIRE_BRANCH}" \
  || { echo "FAIL: git fetch origin/$REQUIRE_BRANCH failed — refuse to verify against stale tips" >&2; exit 1; }
TIP_BEFORE="$(git rev-parse "origin/$REQUIRE_BRANCH")"
if ! git cat-file -e "${STRIP_COMMIT}^{commit}" 2>/dev/null; then
  git fetch --no-tags --deepen=500 origin "$REQUIRE_BRANCH" \
    || git fetch --no-tags --unshallow origin "$REQUIRE_BRANCH" \
    || { echo "FAIL: cannot deepen history to reach $STRIP_COMMIT" >&2; exit 1; }
fi
TRIES=0
while ! git merge-base --is-ancestor "$STRIP_COMMIT" "origin/$REQUIRE_BRANCH" 2>/dev/null; do
  TRIES=$((TRIES + 1))
  [ "$TRIES" -le 5 ] || {
    echo "FAIL: attested commit $STRIP_COMMIT is not an ancestor of origin/$REQUIRE_BRANCH" >&2
    exit 1
  }
  git fetch --no-tags --deepen=500 origin "$REQUIRE_BRANCH" \
    || { echo "FAIL: deepen fetch failed while locating $STRIP_COMMIT" >&2; exit 1; }
done
TIP="$(git rev-parse "origin/$REQUIRE_BRANCH")"
echo "protected_branch_tip=$TIP (pre_fetch_tip=$TIP_BEFORE)" >&2
echo "VERIFIED: $REF signer=$SIGNER commit=$EXPECT_COMMIT on $REQUIRE_BRANCH@$TIP"
```

Always-on required check `.github/workflows/promotion-verify.yml`. Diff failures and multi-image overlays **fail closed** (never treat as docs-only / empty verification):

**Canonical workflow + helper** (copy into your Harbour repo; do not maintain a divergent textbook copy):
- [`reference/harbour/.github/workflows/promotion-verify.yml`](../../reference/harbour/.github/workflows/promotion-verify.yml)
- [`reference/harbour/platform/bin/harbour-promote-verify-images.py`](../../reference/harbour/platform/bin/harbour-promote-verify-images.py)

> **Gate 1 remediations:** **C-02** — render the overlay first (`kubectl kustomize`); skip attestation only when **all** rendered workloads are disabled (unpromoted sentinel + replicas 0). **H-02** — verify **every** complete image reference (not merely distinct digests); fail closed if enumeration yields zero refs.

**Promotion hand-off (P03 → P04):** download artifact `release-manifest-<svc>-<sha>` into `docs/releases/<svc>/<digest>.json` before opening the promotion PR. The gate verifies **rendered** workload images (`kubectl kustomize`), so a base-only `deployment.yaml` change cannot silently skip provenance.

Create and protect `platform/policy/approved-signer-workflows.txt` — one **fully-qualified signing-workflow path** per line, e.g. `your-org/harbour-platform/.github/workflows/service-release.yml`. CODEOWNERS: platform reviewers only. Display names are informational only.

**Required negative tests:** (1) fabricated digest fails; (2) missing manifest fails; (3) non-allow-listed signer path fails; (4) real digest + `UNPROMOTED` comment still verifies; (5) commit not on `main` fails; (6) multi-image / undigested render fails; (7) **base-only** image change without matching release manifest fails; (8) broken git base-ref fails the gate; (9) docs-only PR succeeds; (10) **base-only second runnable workload** (extra Deployment/Job with an unapproved digest) must fail; (11) **two repos sharing one digest** must both verify (per-ref, not per-digest-only).


> **Checkpoint — promotion:** `promotion-verify` is always-on; rendered images are verified via the canonical helper; negative tests (1)–(11) recorded.

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

**Practice — reproduce:** (1) Open a PR that breaks a test; show it is unmergeable. (2) Fix, merge, and record commit SHA, workflow run URL and digest. (3) Run `harbour-verify-artifact` with `--expect-commit` and `--approved-workflows-file` pointing at signer **paths**; show a non-allow-listed signer is rejected. (4) Promote a **fabricated** digest and show `promotion-verify` fails. (5) Open a multi-image overlay PR and show the gate exits nonzero. (6) Open a docs-only PR and show `promotion-verify` still reports success.

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

Policy in CI gives fast feedback; policy at admission catches everything that bypasses CI. Use the **same** rules in both. Install Kyverno with the pin from [`TOOLCHAIN.md`](../../reference/harbour/TOOLCHAIN.md) (**H-04** — never float `latest`):

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/ && helm repo update
helm upgrade --install kyverno kyverno/kyverno -n kyverno --create-namespace --version 3.3.6
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
    # Apply digest checks to containers + optional init/ephemeral containers.
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
            =(initContainers):
              - image: "*@sha256:*"
            =(ephemeralContainers):
              - image: "*@sha256:*"
    - name: require-nonroot-memory-limit
      match: {any: [{resources: {kinds: [Pod]}}]}
      exclude: {any: [{resources: {namespaces: [kube-system, kyverno, flux-system, local-path-storage, platform-system]}}]}
      validate:
        failureAction: Enforce
        message: "Pods must run as non-root; app/init containers forbid privilege escalation and set memory limits. CPU limits optional (ADR 0301/0309)."
        pattern:
          spec:
            securityContext: {runAsNonRoot: true}
            =(initContainers):
              - securityContext: {allowPrivilegeEscalation: false}
                resources:
                  requests: {cpu: "?*", memory: "?*"}
                  limits: {memory: "?*"}
            containers:
              - securityContext: {allowPrivilegeEscalation: false}
                resources:
                  requests: {cpu: "?*", memory: "?*"}
                  limits: {memory: "?*"}
    # Ephemeral containers (kubectl debug) cannot set resources in Kubernetes — apply
    # digest (above) + privilege restrictions only.
    - name: require-ephemeral-no-privilege
      match: {any: [{resources: {kinds: [Pod]}}]}
      exclude: {any: [{resources: {namespaces: [kube-system, kyverno, flux-system, local-path-storage, platform-system]}}]}
      validate:
        failureAction: Enforce
        message: "Ephemeral containers must not escalate privilege (resources are forbidden by the API)."
        pattern:
          spec:
            =(ephemeralContainers):
              - securityContext: {allowPrivilegeEscalation: false}
```

> **Workload model:** golden-path services may use init containers. Ephemeral containers get **digest + no privilege escalation** only — Kubernetes rejects `resources` on ephemeral containers, so requiring requests/limits would ban legitimate `kubectl debug`. Lab: attach a debug container and confirm admission still enforces digest/security.

**Platform-wide resource policy (explicit):** P01 omits CPU *limits* to avoid throttling; P04 must **not** contradict that. Kyverno requires memory limits + CPU/memory *requests*. CPU limits remain allowed but not mandatory. Document in ADR 0309. Re-render P01 Harbour, a P03 golden-path service, Postgres and the backup Job through `harbour-policy-check` — all must pass the same suite.

Confirm autogen is active. If your Kyverno version does not autogen Pod→Deployment, include `Deployment`, `StatefulSet` and `Job` in `kinds` explicitly.

**Relationship to P02:** NetworkPolicy and Pod Security admission remain additional controls. List any you did *not* apply in `LIMITATIONS.md`.

### Offline CI vs live admission (do not conflate)

| Stage | Tooling | Cluster credentials? |
| --- | --- | --- |
| PR CI (`policy` job) | `kyverno apply` + structured policy-report parse; negative fixtures | **No** |
| Integration / disposable cluster | Live admission probes; distinguish Kyverno vs PSA vs RBAC messages | Yes (lab only) |

**Shared report parser** — one module, used by the positive path, negative fixtures, and unit tests (do not duplicate denial rules inline):

**Canonical module:** [`reference/harbour/platform/bin/kyverno_deny.py`](../../reference/harbour/platform/bin/kyverno_deny.py)

> **Gate 1 remediation (H-03):** `warn` is rejected (fail-closed); multi-document PolicyReports are merged; optional `expected_resources` coverage fails if a required resource never appears. Offline unit coverage: [`reference/harbour/tests/test_kyverno_deny.py`](../../reference/harbour/tests/test_kyverno_deny.py).

**Canonical offline checker:** [`reference/harbour/platform/bin/harbour-policy-check`](../../reference/harbour/platform/bin/harbour-policy-check) — for required PR checks. Pin the Kyverno CLI (**v1.13.4**, see `TOOLCHAIN.md`) and **fail closed** on fail/skip/warn/missing rules. That pin emits a YAML `ClusterPolicyReport` via `--policy-report`; parse via `kyverno_deny.py` (wgpolicyk8s.io/v1alpha2).

Negative and positive fixtures live under [`reference/harbour/tests/fixtures/`](../../reference/harbour/tests/fixtures/) (mutable tag, missing memory limit, bad init, privileged ephemeral, good ephemeral). Copy them into `platform/policy/fixtures/` (or point the checker at the reference tree) and keep them in sync with the canonical suite.

Complete required PR workflow `.github/workflows/policy.yml` (always-on; no cluster credentials). Pin CLI **and** verify the tarball checksum (record the SHA256 from the Kyverno release assets for your pin).

**Canonical workflow:** [`reference/harbour/.github/workflows/policy.yml`](../../reference/harbour/.github/workflows/policy.yml)

> **Gate 1 remediation (C-01):** the job now runs `harbour-check-service` for **every** tenant under `platform/tenants/` **and** `harbour-policy-check` for every staging overlay — not only when `deploy/` changes.

**Required-check tests:** (1) PR that introduces `image: nginx:latest` must fail `policy`; (2) docs-only PR must still get a completed `policy` check (always-on). Live `harbour-policy-admit` stays lab-only.

> **Checkpoint — policy CI:** `policy` always reports; tenant contract (C-01) + offline Kyverno fixtures green; mutable-tag PR fails the required check.

`platform/bin/harbour-policy-admit` — **lab/integration only** (not the PR required check). Isolates Kyverno digest denial from PSA rejection by using a restricted-compliant Pod that only violates the image rule, then proves the ephemeral rule against the real `pods/ephemeralcontainers` subresource (`kubectl debug` / patch), not offline Pod YAML alone.

**Canonical script:** [`reference/harbour/platform/bin/harbour-policy-admit`](../../reference/harbour/platform/bin/harbour-policy-admit)

> **Gate 1 remediation (M-01):** require `HARBOUR_PULLABLE_DIGEST_IMG` and `HARBOUR_PULLABLE_DBG_IMG` (pullable `image@sha256:…` refs). Resolve them with the helpers in [`TOOLCHAIN.md`](../../reference/harbour/TOOLCHAIN.md); do not use non-pullable placeholder digests for live admission.

**Required standard:** same forbidden configuration fails offline CI and (in the lab) at admission — including the ephemeralcontainers subresource path; skipped rules are not passes; PSA vs Kyverno vs RBAC denials are distinguishable in evidence. Live admit requires pullable digests via `HARBOUR_PULLABLE_*` (M-01 / `TOOLCHAIN.md`).


> **Checkpoint — admission:** live `harbour-policy-admit` denies mutable tag and privileged ephemeral with pullable digests (M-01); PSA vs Kyverno messages distinguishable in evidence.

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
  echo "# offline policy gate (no cluster) rejects forbidden fixtures"
  platform/bin/harbour-policy-check "$SVC"
  echo "# live admission: Kyverno digest + ephemeralcontainers privilege denials"
  platform/bin/harbour-policy-admit "${SVC}-staging"
  echo "# promotion to an unapproved environment is refused"
  platform/bin/harbour-promote "$SVC" prod "sha256:$(printf '0%.0s' {1..64})" 2>&1
} | tee docs/final/drills/access-denials.txt
```

Expect `yes`/`no`/`no`/`no`, offline policy OK, Kyverno-specific admission denial, and the promotion error.

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

Stateful services were out of P03's v1 golden path because they are expensive to get wrong. Add Postgres as a **platform component** the service opts into (StatefulSet and PVC concepts: P01 §1.8). This is a documented human gate: raise the tenant quota (`pods: "8"`, `requests.cpu: "1"`, `requests.memory: 1Gi`, `limits.memory: 2Gi` — **no `limits.cpu`**, matching P01/P03 optional CPU limits) through a reviewed edit of `platform/tenants/$SVC/tenant.yaml`.

P03's tenant already enforces **restricted** PSA and **default-deny** NetworkPolicy. Postgres must therefore (a) satisfy restricted Pod Security and (b) receive explicit allow rules — otherwise the first P04 startup fails under the controls P03 just taught.

`platform/components/postgres/statefulset.yaml` (pin digest: `docker buildx imagetools inspect postgres:16-alpine --format '{{.Manifest.Digest}}'`). Security contexts match **restricted** (non-root, drop ALL, RuntimeDefault seccomp, no privilege escalation):

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
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 70
        runAsGroup: 70
        fsGroup: 70
        seccompProfile: {type: RuntimeDefault}
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
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: false   # Postgres needs writable PGDATA; document the exception
            capabilities: {drop: [ALL]}
          resources:
            requests: {cpu: 100m, memory: 128Mi}
            limits: {memory: 256Mi}          # CPU limit optional — platform policy matches P01 ADR 0301
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
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-backup
  annotations: {kustomize.toolkit.fluxcd.io/prune: disabled}
spec: {accessModes: [ReadWriteOnce], resources: {requests: {storage: 1Gi}}}
```

`platform/components/postgres/networkpolicy.yaml` — **required** with the StatefulSet (version-controlled, not a laptop snowflake):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: postgres-ingress}
spec:
  podSelector: {matchLabels: {app: postgres}}
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector: {matchLabels: {app: ledger}}          # set to $SVC label
        - podSelector: {matchLabels: {app: postgres-backup}}
      ports: [{protocol: TCP, port: 5432}]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: ledger-egress-postgres}
spec:
  podSelector: {matchLabels: {app: ledger}}
  policyTypes: [Egress]
  egress:
    - to: [{podSelector: {matchLabels: {app: postgres}}}]
      ports: [{protocol: TCP, port: 5432}]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: postgres-backup-egress}
spec:
  podSelector: {matchLabels: {app: postgres-backup}}
  policyTypes: [Egress]
  egress:
    - to: [{podSelector: {matchLabels: {app: postgres}}}]
      ports: [{protocol: TCP, port: 5432}]
```

**Negative NetPol test (required):** from another tenant namespace, a Pod must **not** reach `postgres.${SVC}-staging.svc:5432`. Record timeout evidence in `docs/final/drills/netpol-postgres.txt`.

`platform/components/postgres/backup-cronjob.yaml` (restricted-compatible; label `app: postgres-backup` for NetPol):

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
        metadata: {labels: {app: postgres-backup}}
        spec:
          restartPolicy: Never
          automountServiceAccountToken: false
          securityContext:
            runAsNonRoot: true
            runAsUser: 70
            runAsGroup: 70
            fsGroup: 70
            seccompProfile: {type: RuntimeDefault}
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
              securityContext:
                allowPrivilegeEscalation: false
                capabilities: {drop: [ALL]}
              resources:
                requests: {cpu: 50m, memory: 64Mi}
                limits: {memory: 128Mi}
              volumeMounts: [{name: backup, mountPath: /backup}]
          volumes: [{name: backup, persistentVolumeClaim: {claimName: postgres-backup}}]
```

Prove admission before relying on Flux:

```bash
# Validate the *assembled* staging overlay (includes patches + component), not a raw directory with -f.
kubectl apply --dry-run=server -k "deploy/${SVC}/overlays/staging"
# Then apply for real / via Git; confirm pods become Ready under restricted PSA.
```

**Backup durability bar:** (1) ≥2 successful dumps on the PVC; (2) copy a chosen dump **off-cluster via a running helper Pod** (§4.6.4) — never `exec` a completed Job; (3) restore that file later.

`platform/components/postgres/kustomization.yaml`:

```yaml
resources: [statefulset.yaml, backup-cronjob.yaml, networkpolicy.yaml]
```

Include the component and wire env in `deploy/$SVC/overlays/staging/kustomization.yaml` (patch the NetPol `app: ledger` label if `$SVC` differs):

```yaml
resources: [../../base, ../../../../platform/components/postgres]
patches:
  - target: {kind: Deployment, name: ledger}
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env
        value:
          - {name: DATABASE_HOST, value: postgres}
          - {name: DATABASE_USER, value: harbour}
          - {name: DATABASE_NAME, value: harbour}
          - {name: DATABASE_PASSWORD, valueFrom: {secretKeyRef: {name: postgres-credentials, key: password}}}
```

### Application contract — **complete** `services/$SVC/main.py`

Do **not** paste a second `app = FastAPI()` over the P03 scaffold. Replace the whole file with this complete module so `/health` (liveness), `/ready` (query-backed), and `/v1/entries` coexist and existing tests still import `app`:

```python
import os
from datetime import timezone

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="ledger")  # keep the service name from the scaffold


def _dsn() -> str:
    return (
        f"host={os.environ['DATABASE_HOST']} dbname={os.environ['DATABASE_NAME']} "
        f"user={os.environ['DATABASE_USER']} password={os.environ['DATABASE_PASSWORD']}"
    )


def _conn():
    return psycopg.connect(_dsn(), connect_timeout=2)


@app.on_event("startup")
def migrate() -> None:
    if not os.getenv("DATABASE_HOST"):
        return
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS ledger_entries(
                 id bigserial PRIMARY KEY,
                 note text NOT NULL,
                 created_at timestamptz NOT NULL DEFAULT now())"""
        )
        c.commit()


@app.get("/health")
def health():
    """Liveness — process is up. Do not depend on the database here."""
    return {"status": "ok", "service": "ledger"}


@app.get("/ready")
def ready():
    if not os.getenv("DATABASE_HOST"):
        return {"status": "ready", "database": "unconfigured"}
    try:
        with _conn() as c, c.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ready", "database": "query_ok"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not-ready", "database": e.__class__.__name__},
        )


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
    return {
        "id": row[0],
        "note": row[1],
        "created_at": row[2].astimezone(timezone.utc).isoformat(),
    }


@app.get("/v1/entries/{entry_id}")
def read_entry(entry_id: int):
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT id, note, created_at FROM ledger_entries WHERE id=%s", (entry_id,)
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "missing")
    return {
        "id": row[0],
        "note": row[1],
        "created_at": row[2].astimezone(timezone.utc).isoformat(),
    }


@app.get("/v1/entries")
def list_entries():
    with _conn() as c, c.cursor() as cur:
        cur.execute("SELECT id, note, created_at FROM ledger_entries ORDER BY id")
        rows = cur.fetchall()
    return {
        "count": len(rows),
        "entries": [
            {
                "id": r[0],
                "note": r[1],
                "created_at": r[2].astimezone(timezone.utc).isoformat(),
            }
            for r in rows
        ],
    }
```

Update `services/$SVC/test_main.py` to keep `/health` and add a DB-unconfigured readiness case; add `psycopg[binary]` to `requirements.txt`. Ship through the **normal** path (PR → build → verify → promote).

**Honest limits:** single replica; kind storage is local disk; backup PVC shares cluster fate until dumps are copied off-cluster.

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

Targets (training, state yours): **RTO ≤ 3 min** until `/ready` is `query_ok` **and** `GET /v1/entries` succeeds. Report both **estimated recovery-point age** (`incident_time − backup_completed_at`, an approximation of when `pg_dump` finished writing — not a precise recoverable-LSn boundary) and **acknowledged records lost**. They are *hypotheses* until measured.

### 4.6.3 Stateless drill (brief)

Delete one `$SVC` pod; with two replicas the Service keeps serving (D06 §6.8.1). Record time to full readiness. This is C03-class evidence — necessary, not sufficient.

### 4.6.4 Stateful drills — the script

**Canonical runnable script:** copy [`reference/harbour/platform/drills/stateful-drill.sh`](../../reference/harbour/platform/drills/stateful-drill.sh) into `platform/drills/stateful-drill.sh` (G1-04). Any shortened outline below is **illustrative** — the reference file is authoritative for `suspend`/`copy`/`pg_restore` injection, backup checksum verification, and compare-before-resume.

`platform/drills/stateful-drill.sh` (run phases in order). Evidence is **application HTTP**; SQL is support only. Completed Job pods are **never** `exec`'d — backups are copied via a running helper that mounts the backup PVC.

```bash
#!/usr/bin/env bash
set -euo pipefail
NS="${1:?namespace}"; PHASE="${2:?phase}"; SVC="${SVC:?set SVC}"
# Isolate each experiment under a unique run dir. Subsequent phases of the *same*
# experiment reuse HARBOUR_DRILL_OUT or /tmp/harbour-stateful-out.path.
if [ -n "${HARBOUR_DRILL_OUT:-}" ]; then
  OUT="$HARBOUR_DRILL_OUT"
elif [ "${HARBOUR_DRILL_NEW:-0}" != "1" ] && [ -f /tmp/harbour-stateful-out.path ]; then
  OUT="$(cat /tmp/harbour-stateful-out.path)"
else
  RUN_ID="${HARBOUR_DRILL_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
  OUT="docs/final/drills/stateful-$RUN_ID"
fi
mkdir -p "$OUT" ~/harbour-backups
echo "$OUT" > /tmp/harbour-stateful-out.path
export HARBOUR_DRILL_OUT="$OUT"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$OUT/timeline.log"; }
wait_until() { # usage: wait_until <seconds> <description> -- <command...>
  local deadline=$(( $(date +%s) + $1 )); shift; local desc="$1"; shift
  [ "$1" = "--" ] && shift
  until "$@"; do
    [ $(date +%s) -ge "$deadline" ] && { log "TIMEOUT waiting for: $desc"; return 1; }
    sleep 2
  done
}
PF_PID=""
MAINT=0
DB_UNSAFE=0
assert_pf_alive() {
  kill -0 "$PF_PID" 2>/dev/null || { log "INVALID MEASUREMENT: port-forward PID $PF_PID exited"; return 1; }
}
# Returns: "CODE BODY" on HTTP response; "TRANSPORT <reason>" if curl fails.
http_probe() {
  local url="$1" out code
  assert_pf_alive || { echo "TRANSPORT pf_dead"; return 0; }
  set +e
  out="$(curl -sS --max-time 5 -o /tmp/http_body -w '%{http_code}' "$url" 2>/tmp/http_err)"
  local rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "TRANSPORT curl_rc=${rc}:$(tr '\n' ' ' </tmp/http_err)"
    return 0
  fi
  echo "$out $(tr '\n' ' ' </tmp/http_body)"
}
app_pf() {
  app_stop_pf
  kubectl -n "$NS" port-forward "svc/$SVC" 18080:80 >/tmp/pf-ledger.log 2>&1 & PF_PID=$!
  wait_until 30 "port-forward HTTP health" -- bash -c '
    r=$(curl -sS --max-time 2 -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/health || true)
    [[ "$r" =~ ^[0-9]+$ ]]
  '
  assert_pf_alive
}
app_stop_pf() { [ -n "${PF_PID:-}" ] && kill "$PF_PID" 2>/dev/null || true; PF_PID=""; }
# Combined EXIT trap: port-forward cleanup always; maintenance resume when safe.
cleanup_on_exit() {
  if [ "${MAINT:-0}" = "1" ]; then
    if [ "${DB_UNSAFE:-0}" = "1" ]; then
      # Incomplete restore: do NOT resume writers. Leave Flux suspended; require operator.
      log "cleanup: DB_UNSAFE=1 — leaving Flux suspended and app scaled down; operator must verify DB"
      echo "REQUIRES_OPERATOR db_unsafe $(date -u +%FT%TZ)" | tee -a "$OUT/maintenance-cleanup.txt"
      kubectl -n "$NS" annotate kustomization "$SVC" \
        harbour.example/maintenance=operator-required --overwrite || true
    else
      log "cleanup: safe resume after pre-restore failure (MAINT trap)"
      flux resume kustomization "$SVC" -n "$NS" || log "cleanup: flux resume failed"
      kubectl -n "$NS" annotate kustomization "$SVC" harbour.example/maintenance- --overwrite || true
      flux reconcile kustomization "$SVC" -n "$NS" --with-source || true
      echo "trap-safe-resume $(date -u +%FT%TZ)" >> "$OUT/maintenance-cleanup.txt"
    fi
  fi
  app_stop_pf
}
trap cleanup_on_exit EXIT
http() { curl -sf --max-time 5 -H 'content-type: application/json' "$@"; }
app_json() { http http://127.0.0.1:18080/v1/entries; }
app_count() { app_json | python3 -c 'import sys,json; print(json.load(sys.stdin)["count"])'; }
notes_include() {
  local want="$1"
  app_json | WANT="$want" python3 -c 'import os,sys,json; notes={e["note"] for e in json.load(sys.stdin)["entries"]}; sys.exit(0 if os.environ["WANT"] in notes else 1)'
}
# Running helper mounts the backup PVC (RWO: stop backup Jobs first if needed).
backup_helper() {
  kubectl -n "$NS" delete pod backup-helper --ignore-not-found --wait=true
  kubectl -n "$NS" run backup-helper --restart=Never \
    --image="postgres@sha256:REPLACE_WITH_RESOLVED_DIGEST" \
    --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":70,"runAsGroup":70,"fsGroup":70,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"backup-helper","image":"postgres@sha256:REPLACE_WITH_RESOLVED_DIGEST","command":["sleep","3600"],"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}},"resources":{"requests":{"cpu":"10m","memory":"32Mi"},"limits":{"memory":"64Mi"}},"volumeMounts":[{"name":"backup","mountPath":"/backup"}]}],"volumes":[{"name":"backup","persistentVolumeClaim":{"claimName":"postgres-backup"}}]}}'
  kubectl -n "$NS" wait --for=condition=Ready pod/backup-helper --timeout=60s
}
case "$PHASE" in
  seed)
    app_pf
    wait_until 60 "ready query_ok" -- bash -c 'curl -sf http://127.0.0.1:18080/ready | grep -q query_ok'
    for i in $(seq 1 20); do http -d "{\"note\":\"A-$i\"}" http://127.0.0.1:18080/v1/entries >/dev/null; done
    date -u +%FT%TZ > "$OUT/last_ack_before_backup.txt"
    log "seeded via HTTP count=$(app_count)"
    app_stop_pf ;;
  backup)
    J="manual-backup-$(date +%s)"
    kubectl -n "$NS" create job --from=cronjob/postgres-backup "$J"
    kubectl -n "$NS" wait --for=condition=complete "job/$J" --timeout=120s
    date -u +%FT%TZ > "$OUT/backup_completed_at.txt"
    backup_helper
    DUMP="$(kubectl -n "$NS" exec backup-helper -- sh -c 'ls -1t /backup/*.dump | head -1')"
    [ -n "$DUMP" ] || { log "no dump on backup PVC"; exit 1; }
    # Restorability checks: size, checksum, and pg_restore --list (custom format).
    SUM_IN="$(kubectl -n "$NS" exec backup-helper -- sha256sum "$DUMP" | awk '{print $1}')"
    kubectl -n "$NS" exec backup-helper -- \
      pg_restore -l "$DUMP" >/tmp/pg_restore_list.txt
    grep -q 'TABLE DATA\|TABLE' /tmp/pg_restore_list.txt \
      || { log "dump does not list table objects"; exit 1; }
    DEST="$HOME/harbour-backups/$(basename "$DUMP")"
    kubectl -n "$NS" cp "backup-helper:$DUMP" "$DEST"
    SUM_OUT="$(sha256sum "$DEST" | awk '{print $1}')"
    [ "$SUM_IN" = "$SUM_OUT" ] || { log "checksum mismatch in=$SUM_IN out=$SUM_OUT"; exit 1; }
    echo "$SUM_OUT" > "$OUT/backup.sha256"
    echo "$DEST" > "$OUT/offcluster-backup.path"
    log "backup artifact sha256=$SUM_OUT bytes=$(wc -c <"$DEST")"
    kubectl -n "$NS" delete pod backup-helper --wait=false
    app_pf
    wait_until 60 "ready query_ok" -- bash -c 'curl -sf http://127.0.0.1:18080/ready | grep -q query_ok'
    app_count > "$OUT/count-at-backup.txt"
    app_json > "$OUT/entries-at-backup.json"
    log "backup complete; offcluster=$(cat "$OUT/offcluster-backup.path"); http_count=$(cat "$OUT/count-at-backup.txt")"
    app_stop_pf ;;
  write-after)
    app_pf
    for i in $(seq 1 5); do
      RESP="$(http -d "{\"note\":\"B-$i\"}" http://127.0.0.1:18080/v1/entries)"
      echo "$RESP" | tee -a "$OUT/ack-after-backup.jsonl"
      echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["created_at"])' \
        >> "$OUT/ack_timestamps_after_backup.txt"
    done
    date -u +%FT%TZ > "$OUT/incident_before.txt"
    app_count > "$OUT/count-before-incident.txt"
    log "wrote B; count=$(cat "$OUT/count-before-incident.txt")"
    app_stop_pf ;;
  kill-db)
    app_pf
    log "S2 inject: delete pod postgres-0"
    T0=$(date +%s); kubectl -n "$NS" delete pod postgres-0 --wait=false
    # Accept only HTTP 503 as expected readiness loss — not transport/pf failure.
    wait_until 90 "HTTP 503 readiness" -- bash -c '
      r=$(curl -sS --max-time 5 -o /tmp/body -w "%{http_code}" http://127.0.0.1:18080/ready || echo TRANSPORT)
      kill -0 '"$PF_PID"' 2>/dev/null || exit 1
      [ "$r" = "503" ]
    '
    log "S2 detected HTTP 503 after $(( $(date +%s) - T0 ))s body=$(tr '\n' ' ' </tmp/body)"
    kubectl -n "$NS" wait --for=condition=ready pod/postgres-0 --timeout=180s
    wait_until 180 "ready query_ok after S2" -- bash -c '
      kill -0 '"$PF_PID"' 2>/dev/null || exit 1
      curl -sf http://127.0.0.1:18080/ready | grep -q query_ok
    '
    GOT="$(app_count)"; WANT="$(cat "$OUT/count-before-incident.txt")"
    log "S2 recovered RTO=$(( $(date +%s) - T0 ))s http_count=$GOT expected=$WANT"
    [ "$GOT" = "$WANT" ] || { log "S2 HTTP DATA MISMATCH"; exit 1; }
    app_stop_pf ;;
  destroy)
    date -u +%FT%TZ > "$OUT/incident_at.txt"
    kubectl -n "$NS" exec postgres-0 -- psql -U harbour -d harbour -c \
      "DELETE FROM ledger_entries WHERE note LIKE 'A-%' AND id % 2 = 0"
    app_pf
    log "S3 damaged; http_count=$(app_count)"
    app_stop_pf ;;
  restore)
    # SHORTENED OUTLINE — Gate 1 order (H-01). Do not resume before equivalence.
    # Canonical gate: platform/drills/restore-verify-before-resume.sh
    #   (uses harbour-restore-compare.py + db-export-json.sh)
    T0=$(date +%s)
    BACKUP="$(cat "$OUT/offcluster-backup.path")"
    [ -f "$BACKUP" ] || { log "missing off-cluster backup"; exit 1; }
    DESIRED="$(kubectl -n "$NS" get deploy "$SVC" -o jsonpath='{.spec.replicas}')"
    echo "${DESIRED:-2}" > "$OUT/desired-replicas.txt"
    MAINT=1
    DB_UNSAFE=0
    flux suspend kustomization "$SVC" -n "$NS"
    kubectl -n "$NS" annotate kustomization "$SVC" harbour.example/maintenance=restore --overwrite
    kubectl -n "$NS" scale deploy/"$SVC" --replicas=0
    kubectl -n "$NS" wait --for=delete pod -l "app=$SVC" --timeout=120s
    # Optional: HARBOUR_RESTORE_FAIL_AFTER=suspend|copy|pg_restore
    kubectl -n "$NS" cp "$BACKUP" "postgres-0:/tmp/restore.dump"
    DB_UNSAFE=1
    kubectl -n "$NS" exec postgres-0 -- \
      pg_restore -U harbour -d harbour --clean --if-exists /tmp/restore.dump
    case "${HARBOUR_RESTORE_FAIL_AFTER:-}" in
      pg_restore) log "injected failure after pg_restore (DB_UNSAFE → operator required)"; exit 42 ;;
    esac
    # AFTER pg_restore and BEFORE DB_UNSAFE=0 / flux resume — prove equivalence.
    NS="$NS" OUT="$OUT" platform/drills/restore-verify-before-resume.sh
    DB_UNSAFE=0
    flux resume kustomization "$SVC" -n "$NS"
    kubectl -n "$NS" annotate kustomization "$SVC" harbour.example/maintenance- --overwrite
    MAINT=0
    flux reconcile kustomization "$SVC" -n "$NS" --with-source
    kubectl -n "$NS" rollout status deploy/"$SVC" --timeout=180s
    app_pf
    wait_until 180 "ready query_ok after restore" -- bash -c '
      kill -0 '"$PF_PID"' 2>/dev/null || exit 1
      curl -sf http://127.0.0.1:18080/ready | grep -q query_ok
    '
    # Optional RPO report (incident − backup timestamps) — keep from prior evidence files.
    log "S3 restore service-RTO=$(( $(date +%s) - T0 ))s"
    app_stop_pf ;;
  *) echo "phases: seed backup write-after kill-db destroy restore" >&2; exit 2 ;;
esac
```


> **Gate 1 remediation (H-01 / M-02):** AFTER `pg_restore` and BEFORE clearing `DB_UNSAFE=0` / `flux resume`, call canonical [`platform/drills/restore-verify-before-resume.sh`](../../reference/harbour/platform/drills/restore-verify-before-resume.sh). Shared compare: [`harbour-restore-compare.py`](../../reference/harbour/platform/bin/harbour-restore-compare.py) + [`db-export-json.sh`](../../reference/harbour/platform/bin/db-export-json.sh). Do **not** treat resume-then-compare as the recommended path.

Run it (Postgres and ledger must be healthy first; run `harbour-status "$SVC"` and confirm exit 0):

```bash
NS="${SVC}-staging"
# Prove recurring backups before the incident drill:
kubectl -n "$NS" create job --from=cronjob/postgres-backup "warmup-a-$(date +%s)"
sleep 30
kubectl -n "$NS" create job --from=cronjob/postgres-backup "warmup-b-$(date +%s)"
# Start a fresh evidence directory for this experiment, then reuse it across phases.
rm -f /tmp/harbour-stateful-out.path
unset HARBOUR_DRILL_OUT
HARBOUR_DRILL_NEW=1 platform/drills/stateful-drill.sh "$NS" seed
export HARBOUR_DRILL_OUT="$(cat /tmp/harbour-stateful-out.path)"
for p in backup write-after kill-db destroy restore; do
  platform/drills/stateful-drill.sh "$NS" "$p"
done
echo "Evidence: $HARBOUR_DRILL_OUT"
# Failure-path proofs (required): suspend/copy → safe resume + healthy app;
# pg_restore → writers remain stopped until operator authorises recovery.
DESIRED_REPLICAS="$(kubectl -n "$NS" get deploy "$SVC" -o jsonpath='{.spec.replicas}')"
for stage in suspend copy; do
  HARBOUR_RESTORE_FAIL_AFTER="$stage" platform/drills/stateful-drill.sh "$NS" restore \
    && { echo "FAIL: injected $stage should exit nonzero"; exit 1; } || true
  {
    flux get kustomization "$SVC" -n "$NS"
    flux get kustomization "$SVC" -n "$NS" | grep -qi Suspended \
      && { echo "FAIL: Flux still Suspended after safe-path failure ($stage)"; exit 1; }
    flux reconcile kustomization "$SVC" -n "$NS" --with-source
    kubectl -n "$NS" rollout status deploy/"$SVC" --timeout=180s
    NOW="$(kubectl -n "$NS" get deploy "$SVC" -o jsonpath='{.spec.replicas}')"
    [ "$NOW" = "$DESIRED_REPLICAS" ] \
      || { echo "FAIL: replicas after $stage failure=$NOW want=$DESIRED_REPLICAS"; exit 1; }
    kubectl -n "$NS" wait --for=condition=Ready pod -l "app=$SVC" --timeout=180s
    # Stateful Ledger: /ready must return HTTP 200 with query_ok. /health alone is insufficient.
    kubectl -n "$NS" port-forward "svc/$SVC" 18081:80 >/tmp/pf-recover-$stage.log 2>&1 &
    PF_REC=$!
    sleep 2
    READY_CODE="$(curl -sS --max-time 5 -o /tmp/ready-body -w '%{http_code}' http://127.0.0.1:18081/ready || echo 000)"
    kill "$PF_REC" 2>/dev/null || true
    [ "$READY_CODE" = "200" ] || { echo "FAIL: /ready HTTP $READY_CODE after $stage"; exit 1; }
    grep -q query_ok /tmp/ready-body \
      || { echo "FAIL: /ready body missing query_ok (got: $(cat /tmp/ready-body))"; exit 1; }
    echo "OK: safe failure $stage → Flux resumed, replicas=$NOW, /ready query_ok" \
      | tee -a "$HARBOUR_DRILL_OUT/restore-fail-$stage.txt"
  } | tee -a "$HARBOUR_DRILL_OUT/restore-fail-$stage.txt"
done
# Unsafe path: inject after pg_restore — writers must remain stopped.
flux suspend kustomization "$SVC" -n "$NS" || true
HARBOUR_RESTORE_FAIL_AFTER=pg_restore platform/drills/stateful-drill.sh "$NS" restore \
  && { echo "FAIL: injected pg_restore should exit nonzero"; exit 1; } || true
grep -q REQUIRES_OPERATOR "$HARBOUR_DRILL_OUT/maintenance-cleanup.txt" \
  || { echo "FAIL: missing operator-required marker after unsafe restore"; exit 1; }
flux get kustomization "$SVC" -n "$NS" | tee -a "$HARBOUR_DRILL_OUT/restore-fail-pg_restore.txt" \
  | grep -qi Suspended \
  || { echo "FAIL: expected Flux still Suspended after unsafe restore"; exit 1; }
APP_PODS="$(kubectl -n "$NS" get pods -l "app=$SVC" --no-headers 2>/dev/null | wc -l)"
[ "$APP_PODS" = "0" ] \
  || { echo "FAIL: writers still running after unsafe restore (pods=$APP_PODS)"; exit 1; }
echo "OK: unsafe restore left Flux suspended and writers stopped" \
  | tee -a "$HARBOUR_DRILL_OUT/restore-fail-pg_restore.txt"
# Operator recovery: full snapshot equivalence *before* resuming writers.
# Count alone is insufficient after a deliberately partial pg_restore failure.
# Canonical compare (H-01 / M-02) — not ad-hoc TSV parsing:
NS="$NS" OUT="$HARBOUR_DRILL_OUT" platform/drills/restore-verify-before-resume.sh
# (wraps db-export-json.sh + harbour-restore-compare.py; see reference/harbour/)
flux resume kustomization "$SVC" -n "$NS"
kubectl -n "$NS" annotate kustomization "$SVC" harbour.example/maintenance- --overwrite || true
flux reconcile kustomization "$SVC" -n "$NS" --with-source
kubectl -n "$NS" rollout status deploy/"$SVC" --timeout=180s
# Post-resume: app must be queryable (/ready query_ok), not merely listening (/health).
kubectl -n "$NS" port-forward "svc/$SVC" 18082:80 >/tmp/pf-operator-resume.log 2>&1 &
PF_OP=$!
sleep 2
READY_CODE="$(curl -sS --max-time 5 -o /tmp/op-ready-body -w '%{http_code}' http://127.0.0.1:18082/ready || echo 000)"
kill "$PF_OP" 2>/dev/null || true
[ "$READY_CODE" = "200" ] || { echo "FAIL: /ready HTTP $READY_CODE after operator resume"; exit 1; }
grep -q query_ok /tmp/op-ready-body \
  || { echo "FAIL: /ready missing query_ok after operator resume"; exit 1; }
echo "OK: operator resume → /ready query_ok" | tee -a "$HARBOUR_DRILL_OUT/operator-db-check.txt"
```

What each drill proves — and what it does not:

| Drill | Injects | Expected behaviour | Proves | Does **not** prove |
| --- | --- | --- | --- | --- |
| **S2 pod loss** | Delete `postgres-0` | `/ready` → 503 (`query_ok` lost); Service drops endpoints; recreate; HTTP counts match | Self-healing + data durability **through the app** | Node/disk loss, HA |
| **S3 bad migration** | Delete rows in DB | App may stay Ready yet HTTP list is wrong; restore from **off-cluster** dump; HTTP matches backup-time notes | Restorable backup; **time-based RPO** + row loss | PITR, clean-cluster rebuild |
| **Prune hazard** (read) | Remove StatefulSet from Git | Data PVC survives; annotated backup PVC not pruned | Why prune must never target data | Full platform GitOps rebuild (see P02 §2.7.4) |

**Observe the difference:** S2 recovers automatically; S3 needs a human and a runbook, and it **loses data**. A status page that says HEALTHY during S3 is correct about the pod and wrong about the business — record this in the ADR.


> **Checkpoint — restore:** equivalence proven via `restore-verify-before-resume.sh` **before** `DB_UNSAFE=0` / Flux resume; unsafe `pg_restore` injection left writers stopped.

### 4.6.5 Off-cluster copy and the rebuild drill (recommended)

A backup that lives only in the cluster dies with the cluster. Copy one dump out (not into Git) and, if time allows, run a rebuild:

```bash
# Use a *running* helper that mounts postgres-backup — never exec a completed Job pod.
# (Same helper pattern as stateful-drill.sh backup phase.)
# Prefer the active experiment dir if you just ran the drill loop; else start a backup phase.
OUT="${HARBOUR_DRILL_OUT:-$(cat /tmp/harbour-stateful-out.path 2>/dev/null || true)}"
if [ -z "${OUT:-}" ] || [ ! -f "$OUT/offcluster-backup.path" ]; then
  platform/drills/stateful-drill.sh "$NS" backup
  OUT="$(cat /tmp/harbour-stateful-out.path)"
fi
cp "$(cat "$OUT/offcluster-backup.path")" \
  "docs/final/drills/latest.dump"   # gitignored; verify size > 0
```

Rebuild drill (optional, destructive; the cluster-level equivalent is P02 §2.7.4): delete the namespace's Postgres PVC *and* pod, let GitOps recreate an empty database, restore from the copied dump, compare HTTP entry counts. If you skip it, write in ADR 0310: **node/cluster-loss recovery is unproven**.

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

**Index by failed command / error:**

| Error / command | See row |
| --- | --- |
| `policy` + missing tenant PSA/NetPol | Tenant contract… |
| `promotion-verify` + base-only second Deployment | Base-only… |
| `assert_expected_passes` / `warn` | Kyverno report… |
| `harbour-policy-admit` missing env | Pullable digest… |
| `restore-verify-before-resume` mismatch | Restore fingerprint… |
| Kyverno denies Postgres | Kyverno denies… |
| `ImagePullBackOff` / attestation | `promotion-verify` fails… |

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Tenant contract / `policy` fails without `deploy/` change | PSA or `default-deny-all` removed (C-01) | `harbour-check-service`; restore tenant controls |
| Base-only second runnable workload fails promotion | Unapproved image under disabled scaffold (C-02) | Render with `kubectl kustomize`; verify every ref |
| Kyverno report accepts `warn` as pass | Parser bug — use canonical `kyverno_deny.py` (H-03) | [`reference/harbour/tests/test_kyverno_deny.py`](../../reference/harbour/tests/test_kyverno_deny.py) |
| Pullable digest env missing for admit | Placeholder digests (M-01) | Set `HARBOUR_PULLABLE_*` per [`TOOLCHAIN.md`](../../reference/harbour/TOOLCHAIN.md) |
| Kyverno denies the Postgres pod | Tag not digest, or missing `runAsNonRoot` / limits | Policy message; resolve and pin the image digest |
| Postgres `CrashLoopBackOff` with permission error | Volume ownership vs `runAsUser: 70` | `kubectl logs`; `fsGroup`; local-path provisioner |
| `promotion-verify` fails on a good digest | Attestation not pushed, repo plan lacks attestations, or wrong image name in overlay | `gh attestation verify` output; workflow permissions |
| Release run cannot attest | Caller lacks `id-token: write` / `attestations: write` | Caller and reusable permissions |
| `/ready` 503 but DB pod Ready | Service name/port wrong or NetworkPolicy blocking | `kubectl exec` into app pod; Service DNS |
| Backup job never completes | Secret missing, PVC bound to other node, quota | `kubectl describe job`; quota usage |
| Restore fingerprint mismatch | Backup taken before seed, or newer dump chosen; or writers resumed too early | Run `restore-verify-before-resume.sh` **before** Flux resume (H-01) |
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
