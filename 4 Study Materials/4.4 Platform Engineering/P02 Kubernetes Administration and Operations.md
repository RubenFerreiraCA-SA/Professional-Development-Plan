# Chapter 2 — Kubernetes Administration and Operations (P02)

*Platform Engineering textbook · Chapter 2 of 4*

> **Status:** Authored; remediations after audits through `69d15ab` — **awaiting re-review (not signed off)**. Clean-room execution still not claimed.

| | |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [P02 course detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P02%20Kubernetes%20Administration%20and%20Operations.md) (about 48–60 hours). |
| **Prerequisites** | [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) (the hardened Harbour workload on the `harbour-lab` kind cluster, local registry, probe client), [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) (desired state in Git), [D07](../4.1%20DevOps/D07%20Observability.md) (telemetry vocabulary). |

## How to study this chapter

P01 made Harbour a sound **workload**. P02 makes the **cluster around it operable**: who may do what, what limits protect neighbours, what policy refuses unsafe changes, how you diagnose an incident, and how you recover, drain and upgrade without improvising.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Each control is proven by a **denied action**: a guardrail you have never seen say "no" is a guardrail you have not tested.

The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) P02 bar is: *complete a documented day-2 operation (e.g. quota, backup/restore, upgrade drill); an unprivileged identity cannot perform out-of-scope admin actions.* This text teaches [P02 Course Detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P02%20Kubernetes%20Administration%20and%20Operations.md) and feeds [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) (golden paths rely on these guardrails) and [P04](P04%20Platform%20Architecture%20and%20Final%20Project.md).

> **Safety and honesty boundary:** Lab clusters only. Your kind kubeconfig is **cluster-admin by construction** — the first lesson of this chapter is to stop using it for everything. etcd snapshots contain every Secret in cleartext unless encryption at rest is configured; treat them as secrets and keep them out of Git. A kind cluster is one machine: nothing here demonstrates production high availability, and no recovery is "proven" until you have *performed* it and kept the evidence.

### Learning outcomes

1. Distinguish authentication from authorisation and design namespace-scoped, least-privilege RBAC for people and workloads.
2. Create an unprivileged identity, prove allowed and denied actions, and audit RBAC for escalation paths.
3. Apply ResourceQuota, LimitRange and Pod Security Admission, and explain what each does and does not protect.
4. Enforce NetworkPolicy (after **testing** that your CNI enforces it) and an admission policy (digest-only images).
5. Run a structured incident drill from symptom to cause using only cluster evidence and a runbook.
6. Drain and uncordon nodes safely using PodDisruptionBudgets, and explain node-failure behaviour.
7. Back up and recover: rebuild a namespace from Git with a measured recovery time, take an etcd snapshot, and state what is **not** recoverable.
8. Plan and rehearse a version upgrade, and write a day-2 operations runbook and ADRs another engineer can follow.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export LAB_CLUSTER="${LAB_CLUSTER:-harbour-lab}"
export NS="${NS:-harbour-staging}"
export OPS_DIR="${OPS_DIR:-$HOME/.harbour-lab}"     # keys, snapshots: NEVER inside the repo
cd "$HARBOUR_ROOT"
mkdir -p "$OPS_DIR"/{identities,backups} docs/runbooks docs/platform docs/decisions \
         deploy/platform/{staging,cluster}
chmod 700 "$OPS_DIR"

for tool in docker kind kubectl openssl; do command -v "$tool" >/dev/null || { echo "Missing: $tool"; exit 1; }; done
command -v jq >/dev/null || echo "jq recommended for RBAC audit queries"

kubectl config use-context "kind-${LAB_CLUSTER}"
kubectl get nodes
kubectl -n "$NS" get deploy harbour-api           # P01 workload must exist
export IMAGE="$(cat docs/platform/p01-image.txt)"  # digest reference from P01 §1.2.2
type run_probe >/dev/null 2>&1 || echo "Re-define run_probe from P01 §1.4.2 in this shell (consider saving it in docs/platform/lab-functions.sh)"
```

If P01's cluster is gone, rebuild it from your P01 notes first — that rebuild is also practice for §2.7. You need `kind`, `kubectl`, `openssl`, and the P01 registry still running.

---

## Section 2.1 — The day-2 operating model

### 2.1.1 What "day 2" means

Day 0 is design, day 1 is first deployment, **day 2 is everything afterwards**: access changes, capacity limits, incidents, patching, upgrades, backups, and handover. Platform teams are judged here.

| Concern | Question a runbook must answer | Section |
| --- | --- | --- |
| Access | Who can change what, and how do I revoke it? | 2.2 |
| Fairness and capacity | What stops one namespace consuming the cluster? | 2.3 |
| Safety rails | What stops an unsafe workload being admitted? | 2.3–2.4 |
| Incidents | How do I get from symptom to cause quickly? | 2.5 |
| Maintenance | How do I take a node out without an outage? | 2.6 |
| Recovery | What do I restore, from where, in what order, how long? | 2.7 |
| Change | How do I move to the next Kubernetes version? | 2.8 |

### 2.1.2 Who owns what (kind vs managed)

| Layer | On kind (this chapter) | On a managed service (e.g. EKS, from C03 context) | Self-managed kubeadm |
| --- | --- | --- | --- |
| Control plane availability, etcd backup | **You**, but trivially (one node) | Provider | You |
| Node OS / kubelet patching | Rebuild image | You (node groups) or provider (auto modes) | You |
| RBAC, quotas, policy, NetworkPolicy | You | You | You |
| Authentication | Client certificates | Cloud IAM / OIDC mapping | Your choice |
| Workload definitions | You (Git) | You (Git) | You (Git) |

Skills in this chapter on RBAC, policy, drills and runbooks transfer directly. etcd and control-plane mechanics are **awareness** if your target is managed.

### 2.1.3 Desired-state discipline for guardrails

Guardrails are desired state too. Keep them in Git next to the workloads so a rebuilt cluster gets them back:

```text
deploy/
  harbour-api/overlays/staging/     # P01: namespace + workload
  platform/
    staging/                        # RBAC, quota, limits, NetworkPolicy for harbour-staging
      kustomization.yaml
    cluster/                        # cluster-scoped: admission policy
```

Apply order matters on a fresh cluster: namespace → quota/limits → workload. A single Kustomization that includes the staging overlay plus guardrails keeps that ordering inside `kubectl apply -k`.

### 2.1.4 ADR prompt — `docs/decisions/0303-harbour-cluster-operating-model.md`

| Decide | Notes |
| --- | --- |
| Human roles | `platform-admin`, `harbour-developer`, optional `viewer`; what each may do |
| Workload/automation identities | Per-workload ServiceAccounts; token policy |
| How admin access is used | Break-glass vs daily; where kubeconfigs live; expiry |
| Guardrails in scope | Quota, LimitRange, PSA level, NetworkPolicy, digest policy |
| What is **not** protected | e.g. no audit logging, no encryption at rest, no external IdP on kind |
| Who approves guardrail changes | CODEOWNERS on `deploy/platform/` |

---

## Section 2.2 — Identity and access: authentication, RBAC, ServiceAccounts

### 2.2.1 Concept

| Step | Question | Kubernetes mechanism |
| --- | --- | --- |
| Authentication | Who are you? | Client certificate, OIDC token, ServiceAccount token. **There is no `User` object** |
| Authorisation | May you do this? | RBAC (`Role`, `ClusterRole`, bindings) |
| Admission | Is this *object* acceptable? | PSA, validating/mutating policy (§2.3–2.4) |

RBAC is **additive** — there are no deny rules. Least privilege means granting small `Role`s in namespaces rather than `ClusterRole`s cluster-wide.

| RBAC object | Scope | Use |
| --- | --- | --- |
| `Role` + `RoleBinding` | One namespace | Default for teams and workloads |
| `ClusterRole` + `RoleBinding` | Reusable rules, granted per namespace | Share a rule set without cluster-wide grants |
| `ClusterRole` + `ClusterRoleBinding` | Whole cluster | Platform operators only; review every one |

### 2.2.2 Worked example — a developer Role

`deploy/platform/staging/rbac.yaml`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: harbour-developer
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "endpoints", "configmaps", "events"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["delete"]            # lets a developer restart a stuck Pod; the Deployment replaces it
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: harbour-developers
subjects:
  - kind: Group
    name: harbour-developers
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: harbour-developer
  apiGroup: rbac.authorization.k8s.io
```

Deliberately **absent**: `secrets` (any verb — `list` returns values), `pods/exec` and `pods/attach` (shell in the pod, often with mounted credentials), `create` on pods or deployments (bypasses Git/review and admission-by-GitOps), any RBAC verbs, any cluster-scoped resource. Changes to workloads go through Git (D06).

```bash
kubectl create namespace harbour-prod --dry-run=client -o yaml | kubectl apply -f -   # a namespace the developer must NOT reach
kubectl -n "$NS" apply -f deploy/platform/staging/rbac.yaml
```

### 2.2.3 Worked example — a real unprivileged identity (client certificate)

Impersonation (`--as`) is fast for checks, but a **real credential** proves the end-to-end path. kind's API server will sign client certificates through the CSR API.

```bash
ID_DIR="$OPS_DIR/identities"; USER_NAME=alice
openssl genrsa -out "$ID_DIR/$USER_NAME.key" 2048
openssl req -new -key "$ID_DIR/$USER_NAME.key" \
  -subj "/CN=${USER_NAME}/O=harbour-developers" -out "$ID_DIR/$USER_NAME.csr"

cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: ${USER_NAME}
spec:
  request: $(base64 -w0 < "$ID_DIR/$USER_NAME.csr")      # macOS: base64 | tr -d '\\n'
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400                                # short-lived on purpose
  usages: ["client auth"]
EOF
kubectl certificate approve "$USER_NAME"
kubectl get csr "$USER_NAME" -o jsonpath='{.status.certificate}' | base64 -d > "$ID_DIR/$USER_NAME.crt"

kubectl config set-credentials "$USER_NAME" \
  --client-certificate="$ID_DIR/$USER_NAME.crt" --client-key="$ID_DIR/$USER_NAME.key" --embed-certs=true
kubectl config set-context "kind-${LAB_CLUSTER}-${USER_NAME}" \
  --cluster="kind-${LAB_CLUSTER}" --user="$USER_NAME" --namespace="$NS"
kubectl --context "kind-${LAB_CLUSTER}-${USER_NAME}" auth whoami 2>/dev/null || true
```

The certificate's **CN** is the user name and **O** is the group; the `RoleBinding` matched the group. Approving CSRs is itself a privileged act (§2.2.5).

> **Training limitation:** X.509 client certificates **cannot be revoked** before expiry. That is why the lifetime is 24 h here and why production clusters use an identity provider (OIDC/cloud IAM) with short-lived tokens. Record this in ADR 0303.

### 2.2.4 Worked example — prove allowed and denied

```bash
ALICE="kind-${LAB_CLUSTER}-alice"
kubectl --context "$ALICE" get pods                              # allowed
kubectl --context "$ALICE" logs deploy/harbour-api | tail -n 3   # allowed
kubectl --context "$ALICE" get secrets                           # Forbidden
kubectl --context "$ALICE" exec deploy/harbour-api -- id         # Forbidden (pods/exec)
kubectl --context "$ALICE" -n harbour-prod get pods              # Forbidden (other namespace)
kubectl --context "$ALICE" get nodes                             # Forbidden (cluster-scoped)
kubectl --context "$ALICE" create clusterrolebinding x --clusterrole=cluster-admin --user=alice   # Forbidden
kubectl --context "$ALICE" delete deploy harbour-api             # Forbidden
```

**Expected:** the first two succeed; each other line fails with `Error from server (Forbidden): … User "alice" cannot …` naming the verb, resource and namespace. Save all of it to `docs/platform/rbac-evidence.txt` — this is checklist evidence.

Machine-checkable contract (`deploy/platform/staging/test-rbac.sh`) — distinguish Forbidden from auth/connectivity failures; fail the script if the wrong outcome appears:

```bash
#!/usr/bin/env bash
set -euo pipefail
NS="${1:?namespace}"; USER="${2:-alice}"; GROUP="${3:-harbour-developers}"
pass=0; fail=0
assert_yes() {
  if kubectl auth can-i $1 --as "$USER" --as-group "$GROUP" -n "$NS" | grep -qx yes; then
    echo "PASS allow: $1"; pass=$((pass+1))
  else echo "FAIL expected allow: $1"; fail=$((fail+1)); fi
}
assert_no() {
  if kubectl auth can-i $1 --as "$USER" --as-group "$GROUP" -n "$NS" | grep -qx no; then
    echo "PASS deny: $1"; pass=$((pass+1))
  else echo "FAIL expected deny: $1"; fail=$((fail+1)); fi
}
# Live Forbidden (not connection errors)
out="$(kubectl --context "kind-${LAB_CLUSTER}-alice" get secrets -n "$NS" 2>&1 || true)"
echo "$out" | grep -q 'Forbidden' || { echo "FAIL: secrets denial was not Forbidden (got: $out)"; fail=$((fail+1)); }
assert_yes "get pods"
assert_yes "list pods"
assert_no "get secrets"
assert_no "create pods/exec"
assert_no "delete deployments"
assert_no "create namespaces"
# Negative control: a deliberately excessive binding must make assert_no fail — prove the harness works.
echo "Harness check: temporarily bind cluster-admin to alice in a disposable clone only; expect assert_no to fail, then remove."
[ "$fail" -eq 0 ] || exit 1
echo "OK rbac contract ($pass assertions)"
```

Faster listing for humans:

```bash
kubectl auth can-i --list -n "$NS" --as alice --as-group harbour-developers
```

### 2.2.5 Escalation traps — audit for these

| Permission | Why it is dangerous |
| --- | --- |
| `get/list/watch secrets` | Reads credentials, including ServiceAccount token secrets |
| `create pods` / `create deployments` in a namespace | Can mount any Secret or ServiceAccount in that namespace and read it |
| `pods/exec`, `pods/attach` | Interactive access inside workloads |
| `create/update` on `roles`, `rolebindings` without limits | Grant yourself more (Kubernetes blocks escalation unless you hold the verbs, but `escalate`/`bind` bypass this) |
| `escalate`, `bind`, `impersonate` verbs | Explicit escalation primitives |
| `approve` on `certificatesigningrequests` + `sign` on signers | Mint credentials |
| Wildcards (`*` in resources or verbs) | Silently includes future resources |
| `create` on `serviceaccounts/token` | Request tokens for other identities |
| Binding to `system:authenticated` / `system:unauthenticated` | Grants rights to everyone |

Audit queries (read-only, admin context):

```bash
kubectl config use-context "kind-${LAB_CLUSTER}"
kubectl get clusterrolebindings -o json | jq -r '
  .items[] | select(.roleRef.name=="cluster-admin")
  | [.metadata.name, ((.subjects // []) | map(.kind+"/"+.name) | join(","))] | @tsv'
kubectl get rolebindings,clusterrolebindings -A -o json | jq -r '
  .items[] | select([.subjects[]? | .name] | any(. == "system:authenticated" or . == "system:unauthenticated"))
  | .metadata.name'
kubectl get clusterroles,roles -A -o json | jq -r '
  .items[] | select([.rules[]? | (.verbs + .resources)[]] | any(. == "*")) | .metadata.name' | sort -u
```

**Expected:** `cluster-admin` bound only to system-level groups (e.g. `system:masters` or the kubeadm admins group) that you can explain. Built-in roles may contain wildcards; **your** roles must not.

### 2.2.6 Workload and automation identities

Pods run as a `ServiceAccount` (P01 gave Harbour its own with token automount **off**). Automation that talks to the API — a GitOps controller, a CI job — gets its own identity and a namespace-scoped Role.

```bash
kubectl -n "$NS" create serviceaccount ci-reader
kubectl -n "$NS" create role ci-reader --verb=get,list,watch --resource=deployments.apps,pods
kubectl -n "$NS" create rolebinding ci-reader --role=ci-reader --serviceaccount="$NS:ci-reader"
TOKEN="$(kubectl -n "$NS" create token ci-reader --duration=10m)"      # short-lived, not a stored secret
kubectl auth can-i delete deployments -n "$NS" --as "system:serviceaccount:$NS:ci-reader"   # no
```

Avoid long-lived static token Secrets for ServiceAccounts; request **bounded** tokens (`kubectl create token`) or use projected tokens. Reminder from D06: the GitOps controller needs more than read, but should still not be cluster-admin unless your ADR justifies it.

### 2.2.7 Practice — reproduce

1. Write the same Role as a reusable `ClusterRole` bound per namespace with a `RoleBinding`. When is that better?
2. Add `pods/exec` to a **copy** of the role, show alice can now exec, then explain what an attacker with exec in a Pod that mounts credentials gains.
3. Delete the CSR and expire the identity: confirm via `kubectl config` that you removed the user, and note why deleting the CSR does **not** revoke the issued certificate.

### 2.2.8 Verify

- Alice can read logs and Pods in `harbour-staging` and nothing else you listed.
- You can show every `cluster-admin` binding and justify it.
- Your evidence file contains the real `Forbidden` messages (not just `can-i` booleans).

---

## Section 2.3 — Namespaces, quotas, limits and Pod Security

### 2.3.1 Concept

| Control | Protects against | Does **not** protect against |
| --- | --- | --- |
| `ResourceQuota` | A namespace consuming all CPU, memory, object counts | A single Pod hogging within its allowance; node-level contention without requests |
| `LimitRange` | Pods with no requests/limits; absurd per-container sizes | Aggregate overuse (that is quota's job) |
| Pod Security Admission (PSA) | Privileged, host-namespace, root-capable Pods | Application-layer flaws; non-Pod resources |
| `NetworkPolicy` (§2.4) | Lateral movement between Pods | Anything if the CNI does not enforce it |
| Namespaces | Name and RBAC scoping | **Not** a security boundary by themselves |

### 2.3.2 Worked example — quota and defaults

`deploy/platform/staging/quota.yaml`:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: harbour-staging-quota
spec:
  hard:
    pods: "10"
    requests.cpu: 500m
    requests.memory: 1Gi
    limits.memory: 2Gi
    persistentvolumeclaims: "2"
    count/deployments.apps: "5"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: harbour-staging-defaults
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 50m
        memory: 64Mi
      default:
        memory: 256Mi
      max:
        memory: 512Mi
```

Because the quota constrains `limits.memory`, **every** Pod must declare a memory limit — the LimitRange supplies a default so careless Pods are still admitted rather than rejected (or rejected loudly, if you prefer — a policy choice for the ADR). Harbour uses 2 × 100m CPU and 2 × 256Mi; a rolling-update surge Pod adds 100m / 256Mi — still inside the budget.

```bash
kubectl -n "$NS" apply -f deploy/platform/staging/quota.yaml
kubectl -n "$NS" describe resourcequota harbour-staging-quota
```

### 2.3.3 Worked example — hit the quota

```bash
kubectl -n "$NS" scale deploy/harbour-api --replicas=12
sleep 5
kubectl -n "$NS" get deploy harbour-api               # READY stops short of 12
kubectl -n "$NS" describe rs -l app=harbour-api | grep -iE 'exceeded quota|FailedCreate' | head -n 3
kubectl -n "$NS" get events --sort-by=.lastTimestamp | grep -i quota | tail -n 2
kubectl -n "$NS" scale deploy/harbour-api --replicas=2       # restore (Git says 2; D06 reconcile would also revert this)
```

**Expected:** the Deployment reaches only as many Pods as the CPU request quota allows (four or five, not 12: `requests.cpu: 500m` ÷ 100m per Pod, minus the small probe client). `requests.cpu`, not the `pods: "10"` count, is the binding limit. Events say `exceeded quota: harbour-staging-quota, requested: requests.cpu=100m, used: …`. The error is on the **ReplicaSet/events**, not on `kubectl scale` — a classic way to be told "scaled" while nothing happens.

### 2.3.4 Worked example — Pod Security Admission, warn first

PSA levels: `privileged` (no restriction), `baseline` (blocks known escalations), `restricted` (hardened best practice). Modes: `enforce`, `audit`, `warn`. Roll out as **warn → audit → enforce**.

```bash
# What would break? --dry-run=server prints warnings for existing Pods that violate the level:
kubectl label --dry-run=server --overwrite ns "$NS" pod-security.kubernetes.io/enforce=restricted
```

Harbour's P01 Deployment already sets non-root, `RuntimeDefault` seccomp, no privilege escalation and dropped capabilities, so it should print nothing. Make it permanent in `deploy/harbour-api/overlays/staging/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: harbour-staging
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
    harbour.example/policy: digest-required      # used by §2.4.3
```

```bash
kubectl apply -k deploy/harbour-api/overlays/staging
cat <<EOF | kubectl -n "$NS" apply -f -
apiVersion: v1
kind: Pod
metadata: { name: bad-privileged }
spec:
  containers:
    - name: x
      image: ${IMAGE}
      securityContext: { privileged: true }
EOF
```

**Expected:** `Error from server (Forbidden): … violates PodSecurity "restricted:latest": privileged …`. Save it as evidence. Note PSA checks **Pods**, so a Deployment is admitted and the *ReplicaSet* fails to create Pods — read events when a Deployment "does nothing."

### 2.3.5 Practice — reproduce

1. Remove `capabilities.drop: ["ALL"]` from a copy of the Deployment and observe which PSA message appears (baseline would allow it; restricted does not).
2. Move the P01 probe-client Pod to a namespace **without** PSA labels; explain why a debug Pod may need an exemption and who approves it.
3. Show that a quota `pods: "10"` limit counts completed Jobs until they are cleaned up (`ttlSecondsAfterFinished`).

### 2.3.6 Verify

- `describe resourcequota` shows `Used` vs `Hard`; you triggered and read a quota rejection.
- A privileged Pod is refused in `harbour-staging`; Harbour still runs under `restricted`.
- Quota, LimitRange and PSA labels are in Git, not only in the live cluster.

---

## Section 2.4 — Policy: NetworkPolicy and admission

### 2.4.1 Test whether NetworkPolicy is enforced — before relying on it

A `NetworkPolicy` object is accepted by the API server **even if no component enforces it**. Different CNIs differ, and kind's default CNI behaviour varies by version. Prove enforcement:

Save the Calico variant as `infra/kind/harbour-lab-calico.yaml` (below) only if this test shows no enforcement.

```bash
kubectl create namespace np-test
cat <<EOF | kubectl -n np-test apply -f -
apiVersion: v1
kind: Pod
metadata: { name: server, labels: { app: server } }
spec:
  containers:
    - name: s
      image: ${IMAGE}
---
apiVersion: v1
kind: Pod
metadata: { name: client }
spec:
  containers:
    - name: c
      image: ${IMAGE}
      command: ["python", "-c", "import time; time.sleep(3600)"]
EOF
kubectl -n np-test wait --for=condition=Ready pod/server pod/client --timeout=90s
SERVER_IP="$(kubectl -n np-test get pod server -o jsonpath='{.status.podIP}')"
try() { kubectl -n np-test exec client -- python -c "import urllib.request; print(urllib.request.urlopen('http://${SERVER_IP}:8000/health', timeout=3).status)"; }
try                                   # 200 before any policy
cat <<EOF | kubectl -n np-test apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: deny-ingress }
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
EOF
sleep 3; try                          # must now time out if enforced
```

**Expected if enforced:** the second call fails (`timed out`). **If it still prints 200 your CNI does not enforce NetworkPolicy** — everything in §2.4.2 would be decorative. Record the result in ADR 0303 either way. To get enforcement on kind, recreate the cluster without the default CNI and install a policy-capable CNI such as Calico:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
  podSubnet: 192.168.0.0/16
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

```bash
# Pin a real release; follow Calico's current kind guidance:
export CALICO_VERSION="${CALICO_VERSION:-vX.Y.Z}"
kind create cluster --name "$LAB_CLUSTER" --config infra/kind/harbour-lab-calico.yaml --image "$KIND_NODE_IMAGE"
kubectl apply -f "https://raw.githubusercontent.com/projectcalico/calico/${CALICO_VERSION}/manifests/calico.yaml"
kubectl -n kube-system rollout status ds/calico-node --timeout=180s
# Then repeat P01 §1.2.2 registry wiring and re-apply workloads (this is your rebuild drill, §2.7.4).
```

Clean up: `kubectl delete namespace np-test`.

### 2.4.2 Worked example — default deny, then allow what Harbour needs

`deploy/platform/staging/networkpolicies.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
spec:
  podSelector: {}
  policyTypes: ["Egress"]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: harbour-api-ingress
spec:
  podSelector:
    matchLabels: { app: harbour-api }
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - podSelector:
            matchLabels: { app: probe-client }
      ports:
        - { protocol: TCP, port: 8000 }          # the Pod port, not the Service port 80
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: probe-client-egress
spec:
  podSelector:
    matchLabels: { app: probe-client }
  policyTypes: ["Egress"]
  egress:
    - to:
        - podSelector:
            matchLabels: { app: harbour-api }
      ports:
        - { protocol: TCP, port: 8000 }
```

Two details that cause most failures: policies match **Pod** ports after Service translation (8000, not 80), and default-deny egress breaks DNS unless you allow it.

```bash
kubectl -n "$NS" apply -f deploy/platform/staging/networkpolicies.yaml
kubectl -n "$NS" get pods          # still Ready? kubelet probes are node-local and should not be blocked — verify, don't assume
run_probe 30                       # P01 §1.4.2; expect 200s: probe-client → harbour-api allowed
cat <<EOF | kubectl -n "$NS" apply -f -
apiVersion: v1
kind: Pod
metadata: { name: denied-client, labels: { app: denied-client } }
spec:
  restartPolicy: Never
  automountServiceAccountToken: false
  securityContext: { runAsNonRoot: true, runAsUser: 10001, seccompProfile: { type: RuntimeDefault } }
  containers:
    - name: c
      image: ${IMAGE}
      command: ["python", "-c", "import urllib.request; print(urllib.request.urlopen('http://harbour-api/health', timeout=3).status)"]
      securityContext: { allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: { drop: ["ALL"] } }
EOF
sleep 10; kubectl -n "$NS" logs denied-client | tail -n 2     # expect a timeout traceback, not 200
kubectl -n "$NS" delete pod denied-client
```

The unlabelled `denied-client` must fail (it is not in the `harbour-api-ingress` allow list, and its egress is default-denied); the labelled `probe-client` must succeed. The **blocked vs allowed** outputs are the evidence.

#### Connectivity matrix (required before calling NetworkPolicy “done”)

Default-deny is a significant change. One probe succeeding is **not** proof that the platform still works. Record and automate this matrix (save as `docs/platform/networkpolicy-matrix.md` and a script under `deploy/platform/staging/test-connectivity.sh`):

| Flow | From → To | Expect | How to test |
| --- | --- | --- | --- |
| App health (allowed) | `probe-client` → `harbour-api:8000` | Allow | `run_probe` → HTTP 200 |
| Lateral (denied) | `denied-client` → `harbour-api:8000` | Deny | timeout / connection error |
| DNS | any app Pod → `kube-dns:53` | Allow | `nslookup kubernetes.default.svc.cluster.local` from a labelled Pod |
| Observability (if present) | app → OTel/Prometheus collector | Allow or **documented exception** | scrape/export succeeds or gap in LIMITATIONS |
| Ingress controller (if present) | ingress Pod → `harbour-api:8000` | Allow or exception | external request reaches `/health` |
| Egress to registry/CI (usually none from app) | app → Internet | Deny by default | confirm no unexpected egress |

**Reversible apply sequence:** (1) save current policies (`kubectl -n "$NS" get netpol -o yaml > /tmp/netpol-before.yaml`); (2) apply default-deny + allows; (3) run the matrix script (must exit non-zero on any unexpected allow/deny); (4) restore with `kubectl apply -f /tmp/netpol-before.yaml` **or** `kubectl apply -k deploy/platform/staging` from Git; (5) re-run the matrix and confirm baseline restored.

P03/P04 tenants must inherit an equivalent default-deny + DNS allow (and app ingress allow for their probe/status identity) — see tenant post-provisioning checks in P03.

### 2.4.3 Worked example — admission policy: digest-addressed images only

Kubernetes 1.30+ includes `ValidatingAdmissionPolicy` (CEL expressions, no extra controller). `deploy/platform/cluster/vap-require-digest.yaml`:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: harbour-require-image-digest
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: "object.spec.template.spec.containers.all(c, c.image.contains('@sha256:'))"
      message: "All container images must be digest-addressed (repo@sha256:…); mutable tags are not allowed."
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: harbour-require-image-digest
spec:
  policyName: harbour-require-image-digest
  validationActions: ["Deny"]
  matchResources:
    namespaceSelector:
      matchLabels:
        harbour.example/policy: digest-required
```

```bash
kubectl apply -f deploy/platform/cluster/vap-require-digest.yaml
kubectl -n "$NS" create deployment tagged --image=nginx:1.27
```

**Expected:** `ValidatingAdmissionPolicy 'harbour-require-image-digest' … denied request: All container images must be digest-addressed …`. And the P01 overlay (digest) still applies.

| Limitation of this policy | Consequence |
| --- | --- |
| Matches `deployments` only | Bare Pods, StatefulSets, Jobs and `initContainers` are not covered; add rules/expressions deliberately |
| Checked at admission | Existing objects are not rejected retroactively; use `Audit`/`Warn` actions to find them |
| `failurePolicy: Fail` | A broken policy blocks changes — know your rollback (delete the binding) before enabling |
| Does not prove the digest is *good* | Signature/provenance verification (D04) needs a separate admission controller |
| Flux/CI see denials as sync errors | Teach responders to read controller status, not only app Pods |

Ecosystem alternatives (Kyverno, OPA Gatekeeper) add mutation, generation and reporting; choose by need, record in the ADR.

### 2.4.4 Practice — reproduce

1. Switch the binding to `validationActions: ["Warn", "Audit"]`, apply a tagged Deployment, and compare outputs. When is soft rollout wiser than deny?
2. Add a NetworkPolicy allowing a future `ingress` namespace to reach Harbour on 8000, using a namespace label selector.
3. Write the one-command rollback for each guardrail you added (delete policy, delete binding, relabel namespace).

### 2.4.5 Verify

- You have recorded whether NetworkPolicy is enforced, with the before/after test output.
- Unlabelled traffic to Harbour is blocked; legitimate traffic and probes still work.
- A tagged-image Deployment is refused with your message; the digest overlay is admitted.

---

## Section 2.5 — Incident response and troubleshooting

### 2.5.1 A triage ladder

```text
1. Scope      → what is failing, since when, who is affected? (client probe, D07 telemetry)
2. Change     → what changed? (git log on deploy/, kubectl rollout history, events)
3. Workload   → kubectl get pods; describe; logs --previous
4. Platform   → nodes Ready? quota exhausted? admission denials? DNS? NetworkPolicy?
5. Mitigate   → smallest reversible action (rollback via Git, scale, cordon)
6. Verify     → client-side success, not "pods are Running"
7. Record     → timeline, cause, follow-ups
```

Core commands (read-only first):

```bash
kubectl get pods -A -o wide | grep -vE 'Running|Completed' || true
kubectl -n "$NS" get events --sort-by=.lastTimestamp | tail -n 20
kubectl -n "$NS" describe pod <name>              # Events are at the bottom
kubectl -n "$NS" logs <pod> --previous            # the crashed container, not the new one
kubectl -n "$NS" rollout history deploy/harbour-api
kubectl get nodes; kubectl top nodes; kubectl top pods -n "$NS"
kubectl -n "$NS" debug -it <pod> --image=<pinned-debug-image> --target=harbour-api   # ephemeral debug container
```

`kubectl debug` with an ephemeral container is useful when the app image has no shell. It still needs RBAC (`pods/ephemeralcontainers`) — deliberately not in the §2.2 developer role — and under PSA `restricted` the debug container itself must comply.

### 2.5.2 A fault catalogue for Harbour

| Fault | Typical injection | Symptom | Where the evidence is | Fix (via Git where possible) |
| --- | --- | --- | --- | --- |
| Bad digest | Image `@sha256:000…` | `ImagePullBackOff`; rollout stalls; **old pods keep serving** | `describe pod` events | Revert the commit |
| Bad readiness path | Probe `/nope` | `0/1 Ready`, no restarts, rollout stalls | `describe`, EndpointSlice | Revert |
| Memory limit too low | `limits.memory: 16Mi` | `OOMKilled`, `CrashLoopBackOff` | `describe` → `Last State` | Raise with evidence |
| Quota exhausted | Lower `requests.cpu` quota, then restart | New Pods never created | `describe rs`, events `exceeded quota` | Fix quota or right-size |
| Selector drift | Change Service selector | Service has **no endpoints**, Pods healthy | `get endpointslices` | Revert |
| NetworkPolicy gap | Remove DNS allow | Name resolution timeouts, Pods Ready | Client errors; DNS test from a Pod | Restore policy |
| Admission denial | Tagged image via Git | Sync/apply error; no new ReplicaSet | Flux/Kustomization status, API error text | Use a digest |

### 2.5.3 Worked example — blind incident drill

Have a peer inject a fault, or script it yourself so you do not see which one ran:

```bash
inject() {  # writes the answer to a file you do not read until after diagnosing
  local faults=(bad-digest bad-readiness low-memory quota-exhausted selector-drift)
  local pick="${faults[RANDOM % ${#faults[@]}]}"
  echo "$pick" > "$OPS_DIR/last-fault.answer"
  case "$pick" in
    bad-digest)      kubectl -n "$NS" set image deploy/harbour-api harbour-api="localhost:5001/harbour-api@sha256:$(printf '0%.0s' {1..64})" ;;
    bad-readiness)   kubectl -n "$NS" patch deploy harbour-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/nope"}]' ;;
    low-memory)      kubectl -n "$NS" patch deploy harbour-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources","value":{"requests":{"cpu":"100m","memory":"8Mi"},"limits":{"memory":"16Mi"}}}]' ;;
    quota-exhausted) kubectl -n "$NS" patch resourcequota harbour-staging-quota --type=merge -p '{"spec":{"hard":{"requests.cpu":"150m"}}}'; kubectl -n "$NS" rollout restart deploy/harbour-api ;;
    selector-drift)  kubectl -n "$NS" patch svc harbour-api --type=merge -p '{"spec":{"selector":{"app":"harbour-apii"}}}' ;;
  esac >/dev/null
}
run_probe 240 && inject
```

Diagnose using **only** the ladder and `docs/runbooks/harbour-cluster.md`. Write a timeline (`docs/platform/incident-drill-1.md`): detection time, hypotheses ruled out, evidence commands, mitigation, verification (probe log shows recovery), cause. Only then read the answer file. Restore any remaining state with `kubectl apply -k deploy/platform/staging` (§2.7) — and note that for a stuck rollout **old Pods were still serving** unless you chose a fault that removed endpoints.

### 2.5.4 Practice — reproduce

1. Run a second drill with a different fault; compare time-to-diagnosis. Which signals were missing from your runbook?
2. For `selector-drift`, explain why every Pod is `Running` and Ready yet traffic fails, and write the one-line command that finds it.
3. Add a `Detect` line to the runbook for each fault: which D07 signal would page you? (Be honest where none exists yet.)

### 2.5.5 Verify

- Your timeline names the injected fault correctly **without** having seen the answer first, or lists what you missed.
- Verification used client evidence (probe log), not only Pod status.

---

## Section 2.6 — Node operations: cordon, drain and failure

### 2.6.1 Concept

| Action | Effect | Honours PDB? |
| --- | --- | --- |
| `cordon` | Mark node unschedulable; existing Pods stay | n/a |
| `drain` | Cordon, then **evict** Pods via the Eviction API | **Yes** — blocks if it would violate a PDB |
| `delete pod` | Direct deletion | **No** |
| Node failure / crash | Pods stay until taint-based eviction (about 300 s by default) | **No** — PDBs cover voluntary disruption only |

### 2.6.2 Worked example — drain a worker under client load

```bash
kubectl -n "$NS" get pods -o wide                         # note which worker hosts which Pod
run_probe 90; sleep 10
NODE="${LAB_CLUSTER}-worker"
kubectl drain "$NODE" --ignore-daemonsets --delete-emptydir-data --timeout=120s
kubectl -n "$NS" get pods -o wide                         # replacements landed elsewhere
kubectl uncordon "$NODE"
kubectl -n "$NS" wait --for=jsonpath='{.status.phase}'=Succeeded pod/probe-client --timeout=120s
kubectl -n "$NS" logs probe-client | tail -n 1            # ok / bad counts
```

`--delete-emptydir-data` acknowledges that the `emptyDir` volume (Harbour's `/tmp`) is lost with the Pod; `--ignore-daemonsets` is needed because DaemonSet Pods (CNI, proxy) cannot be evicted. Save the output as the maintenance record.

### 2.6.3 Worked example — a PDB that blocks a drain (on purpose)

```bash
kubectl -n "$NS" scale deploy/harbour-api --replicas=1
kubectl -n "$NS" get pdb harbour-api                      # ALLOWED DISRUPTIONS = 0
NODE="$(kubectl -n "$NS" get pod -l app=harbour-api -o jsonpath='{.items[0].spec.nodeName}')"
kubectl drain "$NODE" --ignore-daemonsets --delete-emptydir-data --timeout=30s || echo "drain refused/timed out"
kubectl uncordon "$NODE"
kubectl -n "$NS" scale deploy/harbour-api --replicas=2
```

**Expected:** `Cannot evict pod as it would violate the pod's disruption budget` repeating until the timeout. This is the PDB doing its job. It is also how a mis-sized PDB freezes every future node upgrade — the P01 §1.5.5 lesson. The sustainable fix is *more replicas*, not deleting the PDB.

### 2.6.4 Worked example — node failure (not a drain)

```bash
docker stop "${LAB_CLUSTER}-worker2"
kubectl get nodes -w --request-timeout=60s || true
kubectl describe node "${LAB_CLUSTER}-worker2" | grep -A3 Taints
kubectl -n "$NS" get pods -o wide
docker start "${LAB_CLUSTER}-worker2"
```

Observe `NotReady`, the `unreachable` taint, and the delay before eviction. This is the same drill as P01 §1.10.3 with an operator's questions: how long until Pods reschedule, what traffic is lost, and which alert would have told you?

### 2.6.5 Verify

- Drain output, the post-drain Pod placement, and probe counts are saved.
- You triggered and read a PDB-blocked eviction message, then restored replicas and the node.
- Your notes say a drain proves **voluntary** maintenance only, not crash or zone tolerance.

---

## Section 2.7 — Backup and recovery

### 2.7.1 What you must be able to recover

| Layer | Primary recovery source | Notes |
| --- | --- | --- |
| Workload definitions | **Git** (`deploy/`) | Fastest, auditable; the primary DR path |
| Guardrails (RBAC, quota, policy) | **Git** (`deploy/platform/`) | Include them or the rebuilt cluster is unsafe |
| Cluster state (etcd) | etcd snapshot / provider backup | Awareness on managed services; operational duty if self-managed |
| Persistent data | Application-level backup / volume snapshots / managed DB | **Git cannot restore data** |
| Secrets | Secret manager / out-of-band | Not in Git; recovery means reconnecting the source |
| Identities | IdP; on kind, certs die with the cluster CA | Re-issue after rebuild |
| Images | Registry | A deleted registry makes digests unresolvable — back up or mirror |

### 2.7.2 Worked example — rebuild a namespace from Git, with a stopwatch

First, assemble the single entry point `deploy/platform/staging/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: harbour-staging
resources:
  - ../../harbour-api/overlays/staging   # namespace (with PSA labels) + workload
  - rbac.yaml
  - quota.yaml
  - networkpolicies.yaml
```

```bash
kubectl apply -f deploy/platform/cluster/vap-require-digest.yaml      # cluster-scoped, applied separately
kubectl apply -k deploy/platform/staging                              # confirms the single entry point applies
START=$(date +%s)
kubectl delete namespace "$NS" --wait=true                            # simulate loss
kubectl apply -k deploy/platform/staging
kubectl -n "$NS" wait --for=condition=Available deploy/harbour-api --timeout=180s
echo "RTO (namespace rebuild): $(( $(date +%s) - START )) s" | tee docs/platform/recovery-namespace.txt
run_probe 15; kubectl -n "$NS" logs probe-client | tail -n 2
kubectl -n "$NS" get networkpolicy,resourcequota,rolebinding,pdb
```

If the first apply reports a resource not found because the Namespace was not yet established, re-run it — and record that you needed to. **Expected:** Harbour, quota, policy, RBAC and PDB all return from Git alone; the RTO number is yours to record. Alice's certificate still works (RBAC is rebuilt, the CA is unchanged).

What this did **not** restore: anything in a PVC (`kubectl delete namespace` deleted the claims), Secrets created imperatively, and in-flight requests.

### 2.7.3 Worked example — etcd snapshot (and the honest limits of restore)

```bash
CP="${LAB_CLUSTER}-control-plane"
ETCD="etcd-${CP}"
kubectl -n kube-system exec "$ETCD" -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/lib/etcd/harbour-snap.db
docker cp "${CP}:/var/lib/etcd/harbour-snap.db" "$OPS_DIR/backups/harbour-snap-$(date +%Y%m%d-%H%M).db"
chmod 600 "$OPS_DIR"/backups/*.db
kubectl -n kube-system exec "$ETCD" -- etcdutl snapshot status /var/lib/etcd/harbour-snap.db -w table
docker exec "$CP" rm -f /var/lib/etcd/harbour-snap.db
```

If your etcd image lacks `etcdutl`, use `etcdctl snapshot status` (deprecated but present in older releases). A snapshot you have never restored is a hypothesis, not a backup.

| Fact | Consequence |
| --- | --- |
| The snapshot contains all Secrets in cleartext unless encryption at rest is configured | Protect and expire it like a credential; never commit it |
| It captures cluster **objects**, not PersistentVolume contents | Data needs its own backup |
| Restoring etcd into a running kubeadm control plane means stopping the control-plane static pods, restoring to a new data directory and repointing etcd | Rehearse on a **disposable** cluster before you need it; **do not claim a restore capability you have not performed** |
| Managed Kubernetes hides etcd | Your backups are Git + data + provider guarantees |

**Honest bar for this chapter:** a verified snapshot (`status` output saved) plus a **measured Git rebuild** (§2.7.2 and §2.7.4) is Competent. A full etcd restore rehearsal is **Advanced** and optional.

### 2.7.4 Worked example — rebuild the whole cluster (claim the right recovery level)

Distinguish what you prove. Do **not** call a manual `kubectl apply -k` of the app “GitOps recovered”.

| Recovery level | What must work after rebuild | Evidence |
| --- | --- | --- |
| Workload | App Ready and serving | `deploy` Available; client probe |
| Cluster configuration | RBAC, admission, quota, NetworkPolicy restored | `test-rbac.sh`, policy denials, matrix |
| **GitOps** | Flux installed; GitRepository reachable; Kustomizations Ready; **no** hand-applied app manifests required for steady state | `flux check`; `flux get all -A` |
| Platform | Tenant provisioning / golden path works again | P03 `harbour-create` or tenant reconcile |

**Competent (this chapter):** levels 1–3. Level 4 is strengthened in P03–P04 but should not regress here.

Commit `scripts/bootstrap-flux.sh` (pin versions you tested). For **private** repos, the script must **recreate** the deploy-key / HTTPS-token Secret from out-of-band env vars **before** the GitRepository becomes Ready — controllers alone are not enough.

```bash
#!/usr/bin/env bash
# scripts/bootstrap-flux.sh — install Flux and root reconciliation from Git.
set -euo pipefail
: "${GIT_URL:?set GIT_URL to the Harbour repo URL Flux can read}"
GIT_BRANCH="${GIT_BRANCH:-main}"
FLUX_VERSION="${FLUX_VERSION:-2.4.0}"   # pin; verify against flux releases
# Credential method for private training repos (document choice in ADR 0304):
#   FLUX_GIT_SECRET=flux-system
#   FLUX_GIT_AUTH=https   + GITHUB_TOKEN   (PAT with contents:read)
#   FLUX_GIT_AUTH=ssh    + FLUX_SSH_PRIVATE_KEY_FILE + optional FLUX_SSH_KNOWN_HOSTS_FILE
# Public repos may omit FLUX_GIT_SECRET / FLUX_GIT_AUTH.
command -v flux >/dev/null
flux install --version="$FLUX_VERSION"
if [ -n "${FLUX_GIT_SECRET:-}" ]; then
  FLUX_GIT_AUTH="${FLUX_GIT_AUTH:-https}"
  case "$FLUX_GIT_AUTH" in
    https)
      : "${GITHUB_TOKEN:?set GITHUB_TOKEN to recreate the Flux HTTPS Secret}"
      kubectl -n flux-system create secret generic "$FLUX_GIT_SECRET" \
        --from-literal=username=git \
        --from-literal=password="$GITHUB_TOKEN" \
        --dry-run=client -o yaml | kubectl apply -f -
      ;;
    ssh)
      : "${FLUX_SSH_PRIVATE_KEY_FILE:?set path to deploy-key private key}"
      KH_ARGS=()
      if [ -n "${FLUX_SSH_KNOWN_HOSTS_FILE:-}" ]; then
        KH_ARGS=(--from-file=known_hosts="$FLUX_SSH_KNOWN_HOSTS_FILE")
      else
        ssh-keyscan github.com > /tmp/harbour-known_hosts
        KH_ARGS=(--from-file=known_hosts=/tmp/harbour-known_hosts)
      fi
      kubectl -n flux-system create secret generic "$FLUX_GIT_SECRET" \
        --from-file=identity="$FLUX_SSH_PRIVATE_KEY_FILE" \
        "${KH_ARGS[@]}" \
        --dry-run=client -o yaml | kubectl apply -f -
      ;;
    *) echo "ERROR: FLUX_GIT_AUTH must be https or ssh" >&2; exit 1 ;;
  esac
  kubectl -n flux-system get secret "$FLUX_GIT_SECRET" >/dev/null
  SECRET_REF="--secret-ref=$FLUX_GIT_SECRET"
else
  SECRET_REF=""
fi
# shellcheck disable=SC2086
flux create source git flux-system --url="$GIT_URL" --branch="$GIT_BRANCH" \
  --interval=1m $SECRET_REF \
  --export > /tmp/flux-source.yaml
kubectl apply -f /tmp/flux-source.yaml
flux create kustomization flux-system --source=GitRepository/flux-system \
  --path=./clusters/harbour-local --prune=true --interval=1m
flux check
kubectl -n flux-system wait --for=condition=Ready gitrepository/flux-system --timeout=180s
```

Rebuild sequence (fails closed). After controllers are Ready, prove **functional** reconciliation by applying a **known observable configuration change** (not an empty commit):

```bash
START=$(date +%s)
kind delete cluster --name "$LAB_CLUSTER"
kind create cluster --config infra/kind/harbour-lab.yaml --image "$KIND_NODE_IMAGE"
# re-run P01 §1.2.2 registry wiring
# Private repos: export GITHUB_TOKEN (or FLUX_SSH_PRIVATE_KEY_FILE) so bootstrap recreates the Secret.
export GIT_URL="https://github.com/${GH_OWNER}/harbour-platform.git"   # or SSH URL
export FLUX_GIT_SECRET=flux-system
export FLUX_GIT_AUTH=https                                              # or ssh
./scripts/bootstrap-flux.sh
flux get sources git -A
flux get kustomizations -A
kubectl -n flux-system wait --for=condition=Ready kustomization/flux-system --timeout=300s
# App appears via reconciliation — not a one-shot kubectl apply of the app.
kubectl -n "$NS" wait --for=condition=Available deploy/harbour-api --timeout=300s
./deploy/platform/staging/test-rbac.sh "$NS"
./deploy/platform/staging/test-connectivity.sh "$NS"
# Observable reconciliation proof: change a label Flux must apply; wait until the live object shows it.
PROBE="rebuild-probe-$(date -u +%Y%m%dT%H%M%SZ)"
MARKER_FILE="deploy/harbour-api/overlays/staging/rebuild-probe-label.yaml"
cat > "$MARKER_FILE" <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: harbour-api
spec:
  template:
    metadata:
      labels:
        harbour.example/rebuild-probe: "$PROBE"
EOF
# Ensure the overlay kustomization lists this strategic-merge patch (add once if missing).
grep -q 'rebuild-probe-label.yaml' deploy/harbour-api/overlays/staging/kustomization.yaml \
  || printf '\npatches:\n  - path: rebuild-probe-label.yaml\n' >> deploy/harbour-api/overlays/staging/kustomization.yaml
git add deploy/harbour-api/overlays/staging/
git commit -m "rebuild reconciliation probe $PROBE"
git push
BEFORE="$(kubectl -n flux-system get kustomization flux-system -o jsonpath='{.status.lastAppliedRevision}')"
kubectl -n flux-system annotate gitrepository flux-system reconcile.fluxcd.io/requestedAt="$(date -u +%FT%TZ)" --overwrite
wait_until() { local d=$((SECONDS+$1)); shift; until "$@"; do [ $SECONDS -ge $d ] && return 1; sleep 5; done; }
wait_until 180 bash -c \
  "[ \"\$(kubectl -n flux-system get kustomization flux-system -o jsonpath='{.status.lastAppliedRevision}')\" != \"$BEFORE\" ]"
wait_until 180 bash -c \
  "kubectl -n \"$NS\" get deploy harbour-api -o jsonpath='{.spec.template.metadata.labels.harbour\.example/rebuild-probe}' | grep -qx \"$PROBE\""
echo "OK: Flux applied observable label harbour.example/rebuild-probe=$PROBE" \
  | tee -a docs/platform/recovery-cluster.txt
echo "RTO (cluster rebuild incl. GitOps): $(( $(date +%s) - START )) s" | tee -a docs/platform/recovery-cluster.txt
# Clean up the probe in a follow-up commit once evidence is saved (optional).
```

If you only re-apply manifests with `kubectl apply -k` and never restore Flux + credentials + subsequent reconciliation of an **observable** change, mark GitOps recovery `Unproven`. **alice's kubeconfig is invalid** after rebuild — re-issue in the runbook.

### 2.7.5 Practice — reproduce

1. Time §2.7.2 three times. Which step dominates? Can you reduce it (pre-pulled images, fewer Pods)?
2. Create a PVC with a file in it, delete the namespace, rebuild from Git, and show the data is **gone**. Write the sentence your runbook needs about data.
3. List which of the rebuild steps would differ on a managed cluster.

### 2.7.6 Verify

- `recovery-namespace.txt` and `recovery-cluster.txt` contain real timings from runs you performed.
- A snapshot status output is saved; the snapshot itself is outside the repo with restricted permissions.
- The runbook states clearly what Git does not recover.

---

## Section 2.8 — Upgrades

### 2.8.1 Concepts and rules

| Rule | Detail (verify against the current version-skew policy) |
| --- | --- |
| Upgrade **one minor version at a time** | Never skip minors in a control plane |
| Control plane first, then nodes | `kubelet` must not be newer than the API server; older kubelets are tolerated within a documented skew (up to three minors in recent releases) |
| `kubectl` skew | Within one minor of the API server, either direction |
| Read release notes and the deprecation guide | Removed APIs break manifests silently until applied |
| Add-ons (CNI, ingress, policy engines) have their own compatibility matrices | Upgrade them deliberately, before or after as documented |
| Support window | Kubernetes minors are supported for a limited period (roughly a year); plan a cadence rather than an emergency |

### 2.8.2 Worked example — pre-flight checks

```bash
kubectl version
kubectl get nodes -o custom-columns=NAME:.metadata.name,KUBELET:.status.nodeInfo.kubeletVersion,RUNTIME:.status.nodeInfo.containerRuntimeVersion
# Which deprecated APIs has this cluster actually served recently? (admin context)
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis | head -n 20
# Server-side validation of Git against the *running* version:
kubectl apply --dry-run=server -k deploy/platform/staging
```

Also search Git for old API versions (`grep -R "apiVersion:" deploy/ | sort | uniq -c`) and check third-party charts' support matrices. An empty deprecation metric on a mostly idle lab cluster is **weak evidence** — real clusters have operators and controllers using other APIs.

### 2.8.3 Worked example — the kind-appropriate drill: blue/green cluster

kind cannot upgrade a cluster in place, so rehearse the *application-level* risk instead:

```bash
export NEXT_NODE_IMAGE="kindest/node:vX.Y.Z@sha256:..."        # the next minor, pinned, from kind release notes
cp infra/kind/harbour-lab.yaml /tmp/harbour-next.yaml && sed -i '/^name:/d' /tmp/harbour-next.yaml
kind create cluster --name harbour-lab-next --config /tmp/harbour-next.yaml --image "$NEXT_NODE_IMAGE"
# registry wiring for the new cluster: repeat P01 §1.2.2 with LAB_CLUSTER=harbour-lab-next
kubectl --context kind-harbour-lab-next apply -f deploy/platform/cluster/vap-require-digest.yaml
kubectl --context kind-harbour-lab-next apply -k deploy/platform/staging
kubectl --context kind-harbour-lab-next -n "$NS" wait --for=condition=Available deploy/harbour-api --timeout=180s
run_probe 30     # against the new cluster: set the context first, then repeat the P01 kill test
```

Compare behaviour between the clusters: probes, PSA warnings, policy outcomes, API deprecations. Record differences. When satisfied, delete the old cluster; if not, delete the new one and write down why. This validates **your manifests and guardrails against the new version** — not the upgrade procedure itself.

### 2.8.4 Reading — the in-place procedure (kubeadm), for self-managed clusters

| Step | Command shape | Purpose |
| --- | --- | --- |
| 1. Back up | etcd snapshot (§2.7.3) + Git + data | Rollback source |
| 2. Plan | `kubeadm upgrade plan` | Shows target versions and checks |
| 3. Control plane | `kubeadm upgrade apply vX.Y.Z` (first node); `kubeadm upgrade node` (others) | Upgrades static pods/certs |
| 4. Each worker | `kubectl drain` → upgrade `kubeadm`/`kubelet` packages → `systemctl restart kubelet` → `kubectl uncordon` | Rolling node upgrade, PDB-aware |
| 5. Verify | Nodes `Ready` at the new version; workloads and client probes healthy | Done only when users agree |

Managed services replace steps 3–4 with provider mechanisms but **not** step 1 (data), the PDB requirement, or your verification. A rollback of a control-plane upgrade is not generally supported — that is why you rehearse and snapshot first.

### 2.8.5 ADR prompt — `docs/decisions/0304-harbour-recovery-and-upgrade-posture.md`

Cover: recovery objectives you can *actually* meet (from §2.7 timings); backup scope and cadence; what you do not back up and why; Kubernetes version policy (N-1? cadence?); how upgrades are rehearsed; who approves; and what you do **not** claim (HA, zero-downtime upgrades).

### 2.8.6 Verify

- Pre-flight outputs are saved with the versions involved.
- The blue/green rehearsal found and recorded at least one observation (even "none").
- ADR 0304 exists and its objectives cite measured numbers.

---

## Section 2.9 — The day-2 runbook and operating cadence

### 2.9.1 Runbook skeleton — `docs/runbooks/harbour-cluster.md`

```markdown
# Harbour cluster runbook (training)

## Scope and limits
kind, one host; guardrails: quota, PSA restricted, NetworkPolicy (enforced: yes/no, tested <date>), digest policy.

## Access
Roles, how a new developer is onboarded/offboarded, where admin kubeconfig is kept, cert lifetime.

## Triage
Ladder (copy from §2.5.1) + links to dashboards/alerts.

## Procedures
- Restart / rollback a bad release (Git revert + verify)
- Drain and uncordon a node (§2.6.2) — pre-checks: PDB ALLOWED DISRUPTIONS ≥ 1
- Rebuild namespace from Git (§2.7.2) — last measured RTO: __ s
- Rebuild cluster (§2.7.4) — last measured RTO: __ s
- Take etcd snapshot (§2.7.3) — storage location, retention, encryption
- Upgrade rehearsal (§2.8.3)

## Known gaps
No audit logging; no encryption at rest; certs not revocable; data not covered by Git.

## Escalation
Who, when, how.
```

### 2.9.2 Operation record template

Every day-2 operation leaves a short record (`docs/platform/ops-log/YYYY-MM-DD-<operation>.md`): **intent**, **pre-checks**, **commands run** (exact), **verification**, **result**, **deviations**, **follow-ups**. This is what turns "I did a drain" into evidence a reviewer can accept.

### 2.9.3 Cadence

| Frequency | Activity |
| --- | --- |
| Per change | Server-side dry-run, Git review on `deploy/platform/` |
| Weekly | RBAC audit queries (§2.2.5), expired identities, quota headroom |
| Monthly | Namespace rebuild drill; image/CVE re-scan (D03/D04) |
| Per release / quarterly | Upgrade rehearsal; review the version-support window |
| Annually | Re-test the runbook with someone who did not write it |

---

## Section 2.10 — Troubleshooting field guide

| Symptom | Likely cause | First checks |
| --- | --- | --- |
| `Forbidden` for a legitimate action | Missing verb/resource; wrong namespace; group not mapped | `kubectl auth can-i … --as …`; read the message — it names the missing permission |
| `Forbidden` when it should work (cert user) | Certificate expired or CN/O mismatch | `openssl x509 -in alice.crt -noout -dates -subject` |
| CSR stuck `Pending` | Not approved; wrong `signerName` | `kubectl get csr`; approval is a privileged action |
| Deployment shows `0/N` with no Pods | Admission/quota/PSA failing at ReplicaSet | `describe rs`; events |
| `exceeded quota` | Requests/limits/counts at ceiling | `describe resourcequota`; raise or right-size |
| Pods `Running` but timeouts after policy change | Missing DNS egress; wrong port (Service vs Pod) | Test from a Pod; revisit §2.4.2 |
| Policy "applied" but nothing blocked | CNI does not enforce | Repeat §2.4.1 test |
| Drain hangs | PDB with 0 allowed disruptions; unmanaged Pods | `get pdb`; `kubectl drain` output; add replicas |
| Node `NotReady` | kubelet/runtime/network down | `kubectl describe node`; on kind, `docker ps`, `docker logs <node>` |
| Admission webhook timeout | Webhook backend down with `failurePolicy: Fail` | `kubectl get validatingwebhookconfigurations`; fix backend or relax policy **deliberately** |
| Rebuilt cluster cannot pull images | Registry wiring lost | P01 §1.2.2; `crictl pull` on a node |
| Snapshot command fails | Wrong cert paths / etcd pod name | `kubectl -n kube-system get pods | grep etcd`; inspect the static pod spec |

---

## Practical Assessment — Chapter 2 — operate it, constrain it, recover it

Align with [P02 Course Detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P02%20Kubernetes%20Administration%20and%20Operations.md) and Final Project Checklist P02.

### Required deliverables

1. **RBAC** — a namespace-scoped developer Role/RoleBinding in Git; a real unprivileged identity (certificate or equivalent) with saved evidence of **at least four** `Forbidden` outcomes (secrets, exec, other namespace, cluster-scoped/RBAC change) and the allowed actions; an RBAC audit with `cluster-admin` bindings explained.
2. **Guardrails** — ResourceQuota + LimitRange with a recorded quota rejection; PSA `restricted` on the Harbour namespace with a recorded privileged-Pod rejection; all in Git.
3. **Policy** — the NetworkPolicy enforcement test result (**enforced or not, with evidence**); default-deny plus allow rules with a blocked and an allowed call; the digest-only admission policy with a recorded denial.
4. **Incident drill** — a blind (peer- or script-injected) fault diagnosed with the triage ladder; written timeline; client-side verification.
5. **One documented day-2 operation completed** from: node drain under load; PDB-blocked drain; namespace rebuild from Git with measured RTO; etcd snapshot with verified status; upgrade rehearsal on a second cluster. (Checklist minimum is one; the recovery exercise in deliverable 6 is separately required.)
6. **Recovery exercise** — namespace **and** cluster rebuild from Git with recorded timings; a written statement of what was **not** recovered (data, secrets, identities, anything manual).
7. **Runbook and ADRs** — `docs/runbooks/harbour-cluster.md`, ADR `0303`, ADR `0304`, plus at least one operation record in `docs/platform/ops-log/`.
8. **Limits table** — what your cluster does **not** protect against (no audit logging, certs not revocable, one host, etc.).

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Access control | Uses admin for everything | Least-privilege Role; real identity; multiple denials proven | Escalation-path audit; short-lived tokens/IdP design for production |
| Guardrails | Objects exist | Quota/LimitRange/PSA tested by rejection; in Git | Staged rollout (warn → enforce) with documented exceptions |
| Policy | Policy YAML applied | Enforcement **tested** (or gap recorded); default-deny works; admission denial shown | Policy-as-code tests and audit mode for rollout |
| Incident response | Random kubectl commands | Ladder followed; cause found; client-verified fix | Detect signals mapped to telemetry; postmortem actions |
| Recovery | "I can redeploy" | Measured namespace/cluster RTOs; explicit non-recoverables | Snapshot restore rehearsed on a disposable cluster |
| Upgrades/maintenance | None | Drain/PDB understood; upgrade plan and rehearsal | Version policy with cadence and add-on matrix |
| Runbook honesty | Optimistic | Limits and gaps stated; another engineer can follow | Reviewed by someone else; defects fixed |

**Completion standard:** **Competent** on every row. An unprivileged identity demonstrably cannot do out-of-scope admin; at least one day-2 operation and the recovery exercise are documented with evidence; and no document claims HA or backup capability you did not demonstrate.

### Self-check

- Did the denied outputs come from a **real credential**, not only `can-i`?
- Does every guardrail live in Git so a rebuilt cluster gets it back?
- Did you test NetworkPolicy enforcement, or did you assume it?
- Were your RTO numbers measured this week, on the current layout?
- Can someone who did not build the cluster follow the runbook to drain a node and rebuild the namespace?
- Does anything in your documentation imply high availability, data durability or revocable access that you did not prove?

### Example assessment conclusion (evidence still required)

> `alice` (certificate, 24 h) can read Pods/logs in `harbour-staging`; `get secrets`, `exec`, `harbour-prod` access, node listing and ClusterRoleBinding creation were all Forbidden (`rbac-evidence.txt`). Quota rejection and PSA privileged-Pod rejection recorded. NetworkPolicy enforcement **tested: kindnet did not enforce / Calico enforced** — default-deny with DNS and probe allows verified. Digest-only policy denied `nginx:1.27`. Blind drill (fault: …) diagnosed in N minutes via events and EndpointSlices. Operations: node drain under load (ok/bad = …), PDB-blocked drain demonstrated, namespace rebuild RTO N s, cluster rebuild RTO N s, etcd snapshot verified. Not recovered: PVC data, imperative Secrets, alice's credentials after rebuild. Not claimed: HA, revocation, restore of etcd, audit logging.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Give someone access | Namespace `Role` + group `RoleBinding` | `cluster-admin` "for now" |
| Check a permission | `kubectl auth can-i … --as …` then a real-credential test | Trusting the YAML |
| Cap a team's usage | ResourceQuota + LimitRange | Relying on trust and goodwill |
| Block unsafe Pods | PSA (warn → enforce) | Enforce on day one without a dry run |
| Restrict traffic | Test CNI enforcement, then default-deny + allows | Assuming policies are enforced |
| Enforce a convention | Admission policy with an audit stage | A policy with no rollback path |
| Diagnose | Ladder: scope → change → workload → platform | Deleting Pods first |
| Maintain a node | `drain` with PDB headroom | `delete pod`, then hoping |
| Recover | Git for definitions; data/secrets via their own paths | Assuming Git restores everything |
| Upgrade | Rehearse on a second cluster; one minor at a time | Skipping minors or the deprecation check |

## Glossary

| Term | Definition |
| --- | --- |
| Authentication / authorisation | Establishing identity / deciding what that identity may do |
| RBAC | Role-based access control: additive `Role`/`ClusterRole` rules and bindings |
| ServiceAccount | Identity for workloads and automation |
| CSR | CertificateSigningRequest: API object for issuing client certificates |
| ResourceQuota / LimitRange | Namespace aggregate caps / per-container defaults and bounds |
| PSA | Pod Security Admission: baseline/restricted/privileged levels per namespace |
| NetworkPolicy | Pod-level allow rules, enforced only by a capable CNI |
| ValidatingAdmissionPolicy | Built-in CEL-based admission validation |
| Cordon / drain | Mark unschedulable / evict Pods respecting PDBs |
| PDB | PodDisruptionBudget: limits voluntary evictions |
| etcd snapshot | Point-in-time copy of cluster state (objects, not volume data) |
| RTO / RPO | Time to restore / acceptable data loss window |
| Break-glass | Emergency privileged access outside normal controls, recorded afterwards |

## References

- [RBAC authorisation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) · [Certificates and CSRs](https://kubernetes.io/docs/reference/access-authn-authz/certificate-signing-requests/)
- [Resource quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) · [Limit ranges](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) · [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Network policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [ValidatingAdmissionPolicy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)
- [Safely drain a node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/) · [Disruptions and PDBs](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
- [Operating etcd clusters](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) · [Version skew policy](https://kubernetes.io/releases/version-skew-policy/)
- [Kubernetes security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/)
- CNCF certification curricula (CKA, CKS): check the **current** published curriculum; this chapter does not guarantee exam coverage.

**Previous chapter:** [Chapter 1 — Kubernetes and Cloud-Native Fundamentals](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) · **Course detail:** [P02 — Kubernetes Administration and Operations](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P02%20Kubernetes%20Administration%20and%20Operations.md) · **Next chapter:** [Chapter 3 — Internal Developer Platforms and DevEx](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) · **Checklist:** [Final Project Checklist · P02](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
