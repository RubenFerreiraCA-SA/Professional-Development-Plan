# Chapter 1 — Kubernetes and Cloud-Native Fundamentals (P01)

*Platform Engineering textbook · Chapter 1 of 4*

> **Status:** Authored; remediations after audits through `366f6815` — **awaiting re-review (not signed off)**. Clean-room execution still not claimed. Treat version numbers, URLs and kind behaviour as things to **verify on your machine**.

| | |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [P01 course detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) (about 48–60 hours). |
| **Prerequisites** | [D03](../4.1%20DevOps/D03%20Docker%20and%20Containerization.md) (hardened Harbour image, `/health`, `/ready`), [D04](../4.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md) (digests), [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) (kind + Flux, lightly), [C01](../4.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) (ports, DNS, NAT vocabulary). |

## How to study this chapter

D06 used Kubernetes as a *destination* for GitOps. This chapter treats Kubernetes as the **subject**: what the API objects mean, what the control loops actually promise, and how to write a workload definition that **recovers without a human**.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Where a failure mode is subtle (probes, `port-forward`, resource limits), the chapter shows a working sequence first, then breaks it on purpose.

The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) P01 bar is: *workloads become ready with configured probes; after a pod kill, the service recovers under the workload definition alone.* That sentence is deliberately narrow. It does **not** say "Harbour is highly available" — see §1.10 for what you may and may not claim.

This text teaches [P01 Course Detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) and feeds [P02](P02%20Kubernetes%20Administration%20and%20Operations.md) (day-2 operations), [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) (golden paths) and [P04](P04%20Platform%20Architecture%20and%20Final%20Project.md) (integration).

> **Safety and honesty boundary:** Use a disposable local cluster (kind). A kind "node" is a Docker container on **one** machine. Three kind nodes give you scheduling and failover *behaviour* to study — they give you **no** hardware, zone or control-plane redundancy. Never point these labs at a shared or production cluster. Fabricated secrets only. Destroy the cluster when finished.

### Learning outcomes

1. Explain the Kubernetes control plane, node components and the *desired state → reconcile* model, and name what Kubernetes does **not** do for you.
2. Author Deployments, Services and supporting objects for Harbour with correct labels, selectors and rollout strategy.
3. Configure startup, readiness and liveness probes and predict the behaviour of each failing independently.
4. Set resource requests/limits, spread and disruption settings deliberately and explain QoS and OOM behaviour.
5. Inject configuration and secrets without baking them into images, and state the limits of Kubernetes Secrets.
6. Explain Services, cluster DNS, EndpointSlices and why `kubectl port-forward` is not a load-balancing test.
7. Package Harbour with Kustomize and Helm, choose between them in an ADR, and keep images **digest-addressed**.
8. Demonstrate recovery after pod loss from the workload definition alone, with client-side evidence, and state honest availability limits.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export LAB_CLUSTER="${LAB_CLUSTER:-harbour-lab}"
export NS="${NS:-harbour-staging}"
cd "$HARBOUR_ROOT"

for tool in docker kind kubectl; do
  command -v "$tool" >/dev/null || { echo "Missing: $tool"; exit 1; }
done
command -v helm >/dev/null || echo "helm not found — needed for §1.9 (https://helm.sh/docs/intro/install/)"
kubectl version --client
kind version

# Harbour image from D03 must exist locally:
docker image inspect harbour-api:local >/dev/null 2>&1 \
  || (cd app && docker build --build-arg HARBOUR_COMMIT="$(git rev-parse HEAD)" -t harbour-api:local .)

mkdir -p deploy/harbour-api/{base,overlays/staging,tools} deploy/helm docs/decisions docs/platform
```

You need Docker (or a Docker-compatible engine kind supports), `kind`, `kubectl`, and optionally `helm`. About 4 GB of free RAM is comfortable for a three-node kind cluster plus Harbour.

---

## Section 1.1 — The cloud-native model and Kubernetes architecture

### 1.1.1 What "cloud-native" is asking of an application

Cloud-native is not "runs on Kubernetes." It is a set of operating assumptions that platforms like Kubernetes exploit:

| Property | What the platform assumes | Harbour status (from D03) |
| --- | --- | --- |
| Disposable processes | Any instance may be killed and replaced at any time | Stateless API — satisfied |
| Config from the environment | Same image across environments; config injected | `DATABASE_HOST`, `HARBOUR_COMMIT` env vars — satisfied |
| Logs to stdout/stderr | Platform collects; app does not manage log files | Satisfied |
| Health endpoints | Platform can ask "alive?" and "ready?" separately | `/health`, `/ready` — satisfied |
| Graceful shutdown | `SIGTERM` leads to prompt, clean exit | Verify in §1.5 |
| Backing services attached by address | DB is a URL/host, not a localhost process | Optional DB — satisfied when configured |

If one of these is false (for example, the app keeps sessions in memory), Kubernetes will happily schedule it and then expose the flaw during a rollout or node drain.

### 1.1.2 Architecture in one picture

```text
                        ┌──────────────────── control plane ────────────────────┐
 kubectl / Flux ──HTTPS─►  kube-apiserver ──► etcd (cluster state, the database) │
                        │        ▲                                               │
                        │  kube-scheduler (assigns Pods to nodes)                │
                        │  kube-controller-manager (Deployment, ReplicaSet,      │
                        │      Node, EndpointSlice … controllers)                │
                        └────────┬───────────────────────────────────────────────┘
                                 │ watch / report
              ┌──────────────────┴──────────────────┐
         ┌────▼─────────────┐                 ┌─────▼────────────┐
         │ node: worker 1   │                 │ node: worker 2   │
         │ kubelet          │                 │ kubelet          │
         │ container runtime│ (containerd)    │ container runtime│
         │ kube-proxy / CNI │                 │ kube-proxy / CNI │
         │ [Pod][Pod]       │                 │ [Pod]            │
         └──────────────────┘                 └──────────────────┘
```

Key ideas:

- **The API server is the only door to etcd.** Everything — `kubectl`, controllers, kubelets — reads and writes objects through it. This is why RBAC (P02) is the central security control.
- **Controllers reconcile.** You declare `replicas: 2`; a controller observes 1 running Pod and creates another. There is no "start a container" command in the model.
- **Pods are the unit of scheduling**, not containers. A Pod is one or more containers sharing network namespace and volumes.
- **Nodes run the kubelet**, which turns Pod specs into running containers via the container runtime, runs probes, and reports status.

### 1.1.3 What Kubernetes does not do

| Common assumption | Reality |
| --- | --- |
| "It makes my app highly available." | It restarts and reschedules. Availability depends on replicas, spread, probes, disruption budgets, **and** failure domains underneath. |
| "It backs up my data." | It does not. PVCs are storage claims, not backups. |
| "It secures my app." | Defaults are permissive. Security is RBAC, admission policy, NetworkPolicy, image hygiene (P02). |
| "It deploys safely." | A Deployment rolls out *what you tell it*. A bad image with a passing probe still ships. |
| "It scales my database." | Stateful systems need their own replication/failover design. |

### 1.1.4 Training cluster vs production cluster

| Dimension | This chapter (kind) | Production-shaped |
| --- | --- | --- |
| Control plane | One Docker container, single etcd | Multiple control-plane nodes or a managed service across zones |
| Nodes | Docker containers on one host | VMs/instances across failure domains |
| Load balancing | `Service` inside the cluster; `port-forward` for humans | Cloud load balancer / gateway with health checks |
| Storage | Node-local `standard` StorageClass | Replicated or cloud-backed volumes with backup |
| Upgrades | Rebuild cluster | Rolling control-plane + node upgrades |
| Identity | kubeconfig with admin client cert | SSO/OIDC, short-lived credentials |

Record this table's relevant rows in the ADR (§1.2.4). A diagram that implies more than the table allows is a claim you must prove.

---

## Section 1.2 — A lab cluster with a registry, and a digest to deploy

D06 used `kind load docker-image`, which has **no registry digest**. To practise digest-addressed deployment, this chapter adds a **local registry** reachable from kind nodes. Push once, deploy by `@sha256:…`.

### 1.2.1 Worked example — three-node kind cluster

`infra/kind/harbour-lab.yaml` (or `docs/platform/` if you keep `infra/` for Terraform only — record the choice):

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: harbour-lab
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

Pin the node image. kind's release notes list `kindest/node` tags with digests; copy a current pair rather than relying on the default:

```bash
# Example shape — copy a real, current tag@digest from the kind release notes:
export KIND_NODE_IMAGE="${KIND_NODE_IMAGE:-kindest/node:vX.Y.Z@sha256:REPLACE_FROM_KIND_RELEASE_NOTES}"
case "$KIND_NODE_IMAGE" in *REPLACE*) echo "Set KIND_NODE_IMAGE first"; exit 1;; esac

mkdir -p infra/kind
# (create infra/kind/harbour-lab.yaml with the YAML above)
kind create cluster --config infra/kind/harbour-lab.yaml --image "$KIND_NODE_IMAGE"
kubectl cluster-info --context "kind-${LAB_CLUSTER}"
kubectl get nodes -o wide
```

**Expected:** three nodes `Ready`: `harbour-lab-control-plane`, `harbour-lab-worker`, `harbour-lab-worker2`.

### 1.2.2 Worked example — local registry that kind nodes can pull from

This follows the pattern in the [kind local registry guide](https://kind.sigs.k8s.io/docs/user/local-registry/). Read that page; its details change between kind releases.

**Reproducibility bar:** commit `scripts/bootstrap-kind-registry.sh` once you have a working sequence, with a short compatibility matrix (kind version, Kubernetes/`kindest/node` digest, containerd behaviour, registry image **digest**). Until that script exists and has been re-run on a clean machine, do **not** claim a frozen infrastructure baseline — only a studied procedure.

```bash
reg_name="kind-registry"; reg_port="5001"
# Resolve a current registry image digest once, then pin it:
#   docker buildx imagetools inspect registry:2 --format '{{.Manifest.Digest}}'
REG_IMAGE="${REG_IMAGE:-registry@sha256:REPLACE_WITH_RESOLVED_DIGEST}"
if [ "$(docker inspect -f '{{.State.Running}}' "$reg_name" 2>/dev/null || true)" != "true" ]; then
  docker run -d --restart=always -p "127.0.0.1:${reg_port}:5000" \
    --network bridge --name "$reg_name" "$REG_IMAGE"
fi

# Tell each node's containerd that localhost:5001 means the registry container:
REGISTRY_DIR="/etc/containerd/certs.d/localhost:${reg_port}"
for node in $(kind get nodes --name "$LAB_CLUSTER"); do
  docker exec "$node" mkdir -p "$REGISTRY_DIR"
  cat <<EOF | docker exec -i "$node" cp /dev/stdin "$REGISTRY_DIR/hosts.toml"
[host."http://${reg_name}:5000"]
EOF
done

# Attach the registry to the kind network so nodes can reach it by name:
[ "$(docker inspect -f '{{json .NetworkSettings.Networks.kind}}' "$reg_name")" = "null" ] \
  && docker network connect kind "$reg_name"
```

Push Harbour and capture the **digest**:

```bash
docker tag harbour-api:local "localhost:${reg_port}/harbour-api:p01"
docker push "localhost:${reg_port}/harbour-api:p01"

export IMAGE_DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "localhost:${reg_port}/harbour-api:p01" | sed 's/.*@//')"
echo "digest: $IMAGE_DIGEST"            # sha256:…
export IMAGE="localhost:${reg_port}/harbour-api@${IMAGE_DIGEST}"
printf '%s\n' "$IMAGE" > docs/platform/p01-image.txt
```

Verify a node can pull it (this isolates registry problems from manifest problems):

```bash
docker exec "${LAB_CLUSTER}-worker" crictl pull "$IMAGE"
```

> **Limitation:** an HTTP registry on localhost is a training convenience. A production registry uses TLS, authentication, retention policy and image signing (D04). Record this in the ADR.

### 1.2.3 Practice — reproduce

From a deleted cluster (`kind delete cluster --name harbour-lab`), recreate the cluster, registry wiring and `IMAGE` using only your notes. Time it. That time is your first honest **cluster rebuild** number, reused in P02.

### 1.2.4 ADR prompt — `docs/decisions/0301-harbour-kubernetes-runtime.md`

| Decide | Notes |
| --- | --- |
| Runtime substrate for labs | kind, three nodes, local registry |
| What this proves vs does not | Scheduling/failover behaviour: yes. Zone resilience, control-plane HA: **no** |
| Image identity | Digest from registry push; deploy by digest only |
| Relationship to D05 ECS | Different runtime substrate; digests and probes carry over; list what does not (task definitions vs Pod specs) |
| Packaging default | Decided in §1.9 (ADR 0302) |

---

## Section 1.3 — Pods, ReplicaSets and Deployments

### 1.3.1 Concept

| Object | Owns | Why it exists |
| --- | --- | --- |
| Pod | Containers, volumes, network identity | Unit of scheduling; **ephemeral** |
| ReplicaSet | N identical Pods | Keeps the count; you rarely write it directly |
| Deployment | ReplicaSets across versions | Rolling update, rollback, history |
| Labels/selectors | Association | How a ReplicaSet and Service find "their" Pods |

A bare Pod (no controller) that dies **stays dead**. That fact is the whole point of Deployments and the foundation of the P01 checklist item.

### 1.3.2 Worked example — hardened base manifests

This chapter **supersedes** the D06 base with security and lifecycle settings. Commit the change as a normal reviewed change in `deploy/harbour-api/base/`.

`serviceaccount.yaml`:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: harbour-api
automountServiceAccountToken: false   # Harbour never calls the Kubernetes API
```

`deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: harbour-api
  labels:
    app: harbour-api
spec:
  replicas: 2
  revisionHistoryLimit: 5
  progressDeadlineSeconds: 120
  minReadySeconds: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: harbour-api
  template:
    metadata:
      labels:
        app: harbour-api
    spec:
      serviceAccountName: harbour-api
      automountServiceAccountToken: false
      terminationGracePeriodSeconds: 30
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001          # replace with the image UID if app files are not world-readable (§1.3.3)
        runAsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: harbour-api
      containers:
        - name: harbour-api
          image: harbour-api            # overlay pins registry + digest
          ports:
            - name: http
              containerPort: 8000
          envFrom:
            - configMapRef:
                name: harbour-api-config
          startupProbe:
            httpGet: { path: /health, port: http }
            periodSeconds: 2
            failureThreshold: 30        # up to 60 s to start
          readinessProbe:
            httpGet: { path: /ready, port: http }
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 2
          livenessProbe:
            httpGet: { path: /health, port: http }
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              memory: 256Mi             # no CPU limit by design — see §1.5.2
          lifecycle:
            preStop:
              sleep:
                seconds: 5              # needs a recent Kubernetes; see §1.5.4
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir:
            sizeLimit: 64Mi
```

`service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: harbour-api
  labels:
    app: harbour-api
spec:
  type: ClusterIP
  selector:
    app: harbour-api
  ports:
    - name: http
      port: 80
      targetPort: http
```

`pdb.yaml` (used in anger in P02; defined now so the workload definition is complete):

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: harbour-api
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: harbour-api
```

`kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - serviceaccount.yaml
  - deployment.yaml
  - service.yaml
  - pdb.yaml
configMapGenerator:
  - name: harbour-api-config
    literals:
      - HARBOUR_ENV=unset
```

### 1.3.3 Worked example — staging overlay with a digest

```bash
cat > deploy/harbour-api/overlays/staging/namespace.yaml <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: harbour-staging
EOF

cat > deploy/harbour-api/overlays/staging/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: harbour-staging
resources:
  - namespace.yaml
  - ../../base
images:
  - name: harbour-api
    newName: localhost:5001/harbour-api
    digest: ${IMAGE_DIGEST}
configMapGenerator:
  - name: harbour-api-config
    behavior: merge
    literals:
      - HARBOUR_ENV=staging
EOF

kubectl kustomize deploy/harbour-api/overlays/staging | grep -nE 'image:|namespace:|HARBOUR_ENV'
```

**Expected:** `image: localhost:5001/harbour-api@sha256:…`, namespace `harbour-staging`, `HARBOUR_ENV: staging`.

If the container fails with a permission error, discover the image's user and decide whether to align `runAsUser`:

```bash
docker run --rm --entrypoint id harbour-api:local        # uid=…(harbour) gid=…
```

### 1.3.4 Worked example — apply and observe a rollout

```bash
kubectl apply -k deploy/harbour-api/overlays/staging
kubectl -n "$NS" rollout status deploy/harbour-api --timeout=120s
kubectl -n "$NS" get deploy,rs,pods,svc,pdb -o wide
kubectl -n "$NS" get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName,IMAGEID:.status.containerStatuses[0].imageID
```

**Expected:** 2/2 Ready; pods on different workers (the spread constraint is a preference, `ScheduleAnyway`, so verify rather than assume); `IMAGEID` contains your digest.

Useful reading skills:

```bash
kubectl explain deployment.spec.strategy.rollingUpdate
kubectl -n "$NS" describe deploy harbour-api | sed -n '1,40p'
kubectl -n "$NS" get events --sort-by=.lastTimestamp | tail -n 15
```

### 1.3.5 Practice — reproduce

1. Change `HARBOUR_ENV` in the overlay; apply; watch `kubectl rollout status`. Why did Pods restart even though the image did not change? (Hint: generated ConfigMap name suffix — §1.6.)
2. `kubectl -n "$NS" rollout history deploy/harbour-api`; then `kubectl rollout undo` once. Note what Git would now disagree with.
3. Delete the Deployment's Pod selector in a scratch copy and try to apply — read the error. Selectors are **immutable**; know why.

### 1.3.6 Verify

- Pods are not root (`kubectl exec deploy/harbour-api -- id` prints your UID).
- Root filesystem is read-only (`kubectl exec deploy/harbour-api -- sh -c 'touch /x'` fails; `touch /tmp/x` works).
- The running image is addressed by digest.

---

## Section 1.4 — Health: startup, readiness and liveness probes

### 1.4.1 Three questions, three probes

| Probe | Question | Failure action | Harbour endpoint |
| --- | --- | --- | --- |
| `startupProbe` | "Has it finished starting?" | Kill container if it never succeeds; **disables** the other two until success | `/health` |
| `readinessProbe` | "Should it receive traffic right now?" | Remove from Service endpoints; **no restart** | `/ready` |
| `livenessProbe` | "Is it wedged beyond self-recovery?" | **Restart** the container | `/health` |

The classic production incident is a liveness probe that checks a dependency. The database blips, every replica fails liveness, every replica restarts, and a small outage becomes a large one. **Liveness checks the process; readiness checks the ability to serve.** D03 gave Harbour this split; the Deployment above preserves it.

### 1.4.2 Worked example — watch readiness gate traffic

Deploy a throwaway client that polls the Service from **inside** the cluster. Create `deploy/harbour-api/tools/probe-client.yaml` (not part of the Kustomization):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probe-client
  labels:
    app: probe-client
spec:
  restartPolicy: Never
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: client
      image: ${IMAGE}
      env:
        - name: DURATION
          value: "${DURATION}"
      command: ["python", "-c"]
      args:
        - |
          import os, time, urllib.request
          url = os.environ.get("TARGET", "http://harbour-api/ready")
          end = time.time() + int(os.environ.get("DURATION", "90"))
          ok = bad = 0
          while time.time() < end:
              stamp = time.strftime("%H:%M:%S")
              try:
                  with urllib.request.urlopen(url, timeout=1) as r:
                      code = r.status
              except Exception as e:
                  code = type(e).__name__
              if code == 200:
                  ok += 1
              else:
                  bad += 1
              print(stamp, code, flush=True)
              time.sleep(0.2)
          print("SUMMARY ok=%d bad=%d" % (ok, bad), flush=True)
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
      resources:
        requests: { cpu: 10m, memory: 32Mi }
        limits: { memory: 64Mi }
```

Run it (`envsubst` is told exactly which variables to replace, so nothing else in the file is touched):

```bash
run_probe() {  # usage: run_probe [duration_seconds]
  kubectl -n "$NS" delete pod probe-client --ignore-not-found --wait=true
  DURATION="${1:-90}" IMAGE="$IMAGE" envsubst '${IMAGE} ${DURATION}' < deploy/harbour-api/tools/probe-client.yaml \
    | kubectl -n "$NS" apply -f -
}
```

`TARGET` defaults to `http://harbour-api/ready` (readiness semantics: it only succeeds when a ready backend answers). Start it and tail the output:

```bash
run_probe
kubectl -n "$NS" wait --for=condition=Ready pod/probe-client --timeout=60s
kubectl -n "$NS" logs probe-client | tail -n 3        # timestamped 200s; SUMMARY appears when it ends
```

### 1.4.3 Worked example — break readiness, then liveness

**Break readiness only.** Patch the readiness path to something that returns 404 (training only; in a real repo you would change Git instead):

```bash
kubectl -n "$NS" patch deploy harbour-api --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/nope"}]'
kubectl -n "$NS" rollout status deploy/harbour-api --timeout=60s || true
kubectl -n "$NS" get pods
kubectl -n "$NS" get endpointslices -l kubernetes.io/service-name=harbour-api -o yaml | grep -E 'ready|addresses' || true
```

**Expected:** new Pod `Running` but `0/1` Ready; rollout stalls (and with `maxUnavailable: 0` the **old Pods keep serving** — the rollout safeguard working). `progressDeadlineSeconds` eventually marks the rollout `ProgressDeadlineExceeded`. Container restarts stay at 0: readiness never restarts.

Undo: `kubectl -n "$NS" rollout undo deploy/harbour-api`.

**Break liveness only.**

```bash
kubectl -n "$NS" patch deploy harbour-api --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe/httpGet/path","value":"/nope"}]'
sleep 60; kubectl -n "$NS" get pods
kubectl -n "$NS" describe pod -l app=harbour-api | grep -iE 'Liveness probe failed|Killing|Restart Count'
```

**Expected:** `RESTARTS` climbs; events show `Liveness probe failed: HTTP probe failed with statuscode: 404` and `Killing`. Restore with `rollout undo` or reapply the kustomization (`kubectl apply -k …` returns live state to Git — a miniature of D06 drift correction).

### 1.4.4 Probe design rules

| Rule | Reason |
| --- | --- |
| Liveness must be cheap and dependency-free | Avoid cascading restarts |
| Readiness may check critical dependencies — carefully | A shared dependency failure empties **all** endpoints; decide if "degraded but serving" is better |
| Use `startupProbe` instead of a huge `initialDelaySeconds` | Fast detection after start, tolerance for slow start |
| `timeoutSeconds` below `periodSeconds` | Overlapping probes pile up |
| Do not use `exec` probes that fork heavy processes | CPU cost at scale |
| Readiness also governs **rolling updates** | Bad readiness = stuck rollout (safe) or premature traffic (unsafe) |

Remember Harbour's honest wrinkle (D03): without `DATABASE_HOST`, `/ready` reports `database: "unconfigured"` and still returns 200. Readiness then means "accepts traffic," not "database verified."

### 1.4.5 Verify

- Describe, in one sentence each, what happens when only readiness, only liveness, or only startup fails.
- Show `get pods` output for each failure and the matching `describe` events.
- Restore to the Git-defined state and show `rollout status` succeeded.

---

## Section 1.5 — Resources, scheduling and disruption

### 1.5.1 Requests, limits and QoS

| Setting | Used by | Effect |
| --- | --- | --- |
| `requests.cpu/memory` | **Scheduler**, HPA (CPU %), quotas | Capacity reserved for placement decisions |
| `limits.memory` | Kernel cgroup | Exceed it → container **OOMKilled** |
| `limits.cpu` | Kernel CFS quota | Exceed it → **throttled** (slow, not killed) |

QoS class follows from these: `Guaranteed` (requests = limits for all), `Burstable` (some requests), `BestEffort` (none, first to be evicted). Check yours: `kubectl -n "$NS" get pod -l app=harbour-api -o jsonpath='{.items[0].status.qosClass}'` — expect `Burstable`.

### 1.5.2 Design stance (record in ADR 0301)

| Choice | Harbour default | Trade-off |
| --- | --- | --- |
| Memory limit | Set (256Mi) | Protects the node; OOMKill is a visible failure rather than a noisy neighbour |
| CPU limit | **Omitted** | Avoids latency from throttling; relies on requests and quotas to prevent starvation. **Platform policy (P04 Kyverno) must match this choice:** require memory limits + CPU/memory requests; do **not** later mandate CPU limits without migrating this workload. Record the same rule in ADR 0301 and ADR 0309 |
| Requests | Measured, not guessed | Too low → overcommit and noisy neighbours; too high → wasted capacity |

Measure with metrics-server (installed in D06 §6.8.2): `kubectl top pods -n "$NS"`. Production sizing needs load testing and history (D07 telemetry), not a number from this chapter.

### 1.5.3 Worked example — cause an OOMKill on purpose

Use a throwaway Pod with a tiny memory limit, so Harbour's Deployment stays untouched:

```bash
kubectl -n "$NS" run oom-demo --restart=Never --image="$IMAGE" \
  --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":10001},"containers":[{"name":"oom-demo","image":"'"$IMAGE"'","command":["python","-c","x=list(range(20000000)); import time; time.sleep(60)"],"resources":{"limits":{"memory":"64Mi"}}}]}}'
sleep 15
kubectl -n "$NS" get pod oom-demo
kubectl -n "$NS" get pod oom-demo -o jsonpath='{.status.containerStatuses[0].state.terminated.reason}{"\n"}'
kubectl -n "$NS" delete pod oom-demo
```

**Expected:** `OOMKilled` (exit code 137). Distinguish: *OOMKilled* (limit hit) vs *Evicted* (node pressure) vs *Error* (app exited).

### 1.5.4 Graceful termination and disruption

When a Pod is deleted: it is marked `Terminating` and removed from endpoints **in parallel** with `preStop` and `SIGTERM`. Because endpoint removal propagates asynchronously, traffic can still arrive for a moment after `SIGTERM`. A short `preStop` sleep gives proxies time to catch up; `terminationGracePeriodSeconds` bounds how long before `SIGKILL`.

| Setting | Purpose | Gotcha |
| --- | --- | --- |
| `preStop.sleep` | Drain window | The native `sleep` action needs a recent Kubernetes (beta in 1.30, enabled by default); on older clusters use `exec: ["sleep","5"]` and confirm the binary exists in the image |
| `terminationGracePeriodSeconds` | Max shutdown time | Too short → in-flight requests cut off |
| App handles `SIGTERM` | Clean exit | Verify: `kubectl delete pod` should finish in about `preStop` + a second or two, not 30 s (30 s means `SIGKILL`) |
| PodDisruptionBudget | Limits **voluntary** evictions (drain, upgrades) | Does nothing for crashes or node failure |
| `topologySpreadConstraints` | Prefer different nodes | `ScheduleAnyway` is a preference; `DoNotSchedule` can leave Pods `Pending` |

Time a deletion: `time kubectl -n "$NS" delete pod "$(kubectl -n "$NS" get pod -l app=harbour-api -o name | head -n1)"`.

### 1.5.5 Practice — reproduce

1. Explain why the PDB with `minAvailable: 1` on a **single** replica would block every drain (you will meet this in P02 §2.6).
2. Set `maxUnavailable: 1, maxSurge: 0`; roll out a new `HARBOUR_ENV`; watch pod counts with `kubectl get pods -w`. When would you choose this over `maxUnavailable: 0`?
3. Compute total requests for the Deployment (`replicas × requests`). Compare with node allocatable: `kubectl describe node harbour-lab-worker | sed -n '/Allocatable/,/System Info/p'`.

---

## Section 1.6 — Configuration and secrets

### 1.6.1 Where configuration lives

| Mechanism | Use for | Notes |
| --- | --- | --- |
| Env var literal | Tiny, non-sensitive switches | Visible in `describe` |
| `ConfigMap` → `envFrom` / volume | Non-sensitive config | Env changes need a Pod restart; mounted files update eventually (not for `subPath`) |
| `Secret` | Credentials | **Base64-encoded, not encrypted by default** |
| Image build | Code and static assets only | Never environment-specific config or secrets |

### 1.6.2 Worked example — config change triggers a rollout

You already used a generated ConfigMap. Inspect it:

```bash
kubectl -n "$NS" get configmap
kubectl kustomize deploy/harbour-api/overlays/staging | grep -nE 'harbour-api-config'
kubectl -n "$NS" exec deploy/harbour-api -- printenv HARBOUR_ENV
```

Kustomize appends a content hash to the generated name and rewrites references, so editing the literal changes the name → changes the Pod template → **rollout**. A hand-written ConfigMap with a stable name will **not** restart Pods when edited — a common cause of "I changed config and nothing happened."

### 1.6.3 Worked example — Secrets are not secret by default

```bash
kubectl -n "$NS" create secret generic harbour-db-demo \
  --from-literal=DATABASE_PASSWORD='fabricated-not-real'
kubectl -n "$NS" get secret harbour-db-demo -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 -d; echo
kubectl -n "$NS" delete secret harbour-db-demo
```

Anyone able to `get` that Secret (or exec into a Pod that mounts it) reads the plaintext. Therefore:

- Restrict `get/list/watch` on Secrets with RBAC (P02 §2.2) — `list` returns values.
- Enable **encryption at rest** for etcd where you control the control plane (managed services typically offer this).
- Do **not** commit Secret manifests with values. Use an out-of-band mechanism — external secrets operator, sealed secrets, or your cloud secret manager — and record it in an ADR (D06 §6.8.3).
- Prefer mounting as files over env vars when the app can read files (env vars leak into crash dumps and child processes).

### 1.6.4 Verify

- Show a rollout caused only by a ConfigMap literal change.
- Show a Secret value decoded, and state in your notes who could do that on your cluster today (answer: anyone with admin — P02 reduces that set).

---

## Section 1.7 — Networking: Services, DNS and traffic

### 1.7.1 The model

- Every Pod gets its own IP; Pods can reach Pods without NAT (CNI plugin responsibility).
- Pod IPs are ephemeral, so a **Service** gives a stable virtual IP and DNS name that load-balances over **ready** endpoints.
- Services select Pods by label; the **EndpointSlice** controller lists the ready ones; `kube-proxy` (or the CNI) programs the data path.

| Service type | Reachable from | Typical use |
| --- | --- | --- |
| `ClusterIP` | Inside the cluster | Default; internal APIs |
| `NodePort` | Node IP:port | Debugging; building block for load balancers |
| `LoadBalancer` | Cloud load balancer | Cloud-provisioned edge (needs cloud controller; kind has none by default) |
| `ExternalName` | DNS alias | Point at an external hostname |
| Headless (`clusterIP: None`) | DNS returns Pod IPs | StatefulSets, client-side discovery |

### 1.7.2 Worked example — DNS and endpoints

```bash
kubectl -n "$NS" get svc harbour-api
kubectl -n "$NS" get endpointslices -l kubernetes.io/service-name=harbour-api
kubectl -n "$NS" get pods -l app=harbour-api -o wide     # Pod IPs match the endpoints
```

Names resolve as `<svc>.<namespace>.svc.cluster.local`; within the same namespace the short name `harbour-api` works. Prove it from a Pod:

```bash
kubectl -n "$NS" exec deploy/harbour-api -- python -c "
import socket, urllib.request
print(socket.gethostbyname('harbour-api'))
print(urllib.request.urlopen('http://harbour-api.harbour-staging.svc.cluster.local/health').read())"
```

### 1.7.3 Worked example — why `port-forward` misleads

```bash
kubectl -n "$NS" port-forward svc/harbour-api 8080:80 &
PF=$!
sleep 2; curl -s localhost:8080/health
kubectl -n "$NS" delete pod "$(kubectl -n "$NS" get pod -l app=harbour-api -o name | head -n1)"
sleep 5; curl -s -m 2 localhost:8080/health || echo "tunnel may be dead"
kill $PF
```

`port-forward svc/...` resolves **one** backing Pod when it starts and tunnels to it. It does **not** load-balance, and if that Pod dies the tunnel breaks even though the Service is healthy. Use it for human debugging, never as evidence of availability. Use an **in-cluster client loop** (§1.4.2) or a real load balancer path.

### 1.7.4 Ingress and Gateway — awareness, not a lab dependency

| Concept | What it is | Training stance |
| --- | --- | --- |
| Ingress | L7 HTTP routing resource, implemented by a **controller** you install | The API object exists in core Kubernetes; a controller does the work |
| Gateway API | Newer, role-oriented successor (GatewayClass, Gateway, HTTPRoute) | Prefer for new designs; learn its model in P03/P04 |
| Controller choice | Varies (nginx, Envoy-based, cloud-native) | Check each project's **current maintenance status** before adopting; at least one widely used ingress controller has announced its retirement |

Optional lab: install a controller of your choice per its kind documentation, then a minimal Ingress:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: harbour-api
spec:
  rules:
    - host: harbour.localtest.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: harbour-api
                port:
                  name: http
```

kind needs `extraPortMappings` in the cluster config to expose controller ports on the host. TLS termination, certificates and external DNS are production concerns not exercised here.

### 1.7.5 NetworkPolicy — preview

By default all Pods can talk to all Pods. `NetworkPolicy` restricts that, but **only if your CNI enforces it**. P02 §2.4 teaches default-deny and includes a test to prove enforcement; do not assume it.

### 1.7.6 Verify

- Map Service → EndpointSlice → Pod IPs on your cluster.
- Explain why a readiness failure removes a Pod from traffic without restarting it.
- Explain, with evidence, why your `port-forward` test cannot prove recovery.

---

## Section 1.8 — Stateful, batch and node-level workloads

Harbour's API is stateless; a platform still runs other shapes.

| Workload | Use when | Key properties |
| --- | --- | --- |
| `Deployment` | Stateless services | Interchangeable Pods |
| `StatefulSet` | Stable identity/storage | Ordered names (`db-0`), per-Pod PVCs, headless Service |
| `DaemonSet` | One per node | Log agents, CNI, node exporters |
| `Job` / `CronJob` | Run-to-completion, scheduled | `backoffLimit`, `ttlSecondsAfterFinished`, `concurrencyPolicy` |

### 1.8.1 Practice — a Job and a CronJob

Write a `Job` that runs the Harbour image with `python -c` to call `http://harbour-api/ready` and exit non-zero on failure. Use `backoffLimit: 1`, `ttlSecondsAfterFinished: 300`, `restartPolicy: Never`, and the **same** security context as the Deployment (non-root, read-only root, dropped capabilities, no service-account token). Apply it with `envsubst '${IMAGE}'`, then check `kubectl wait --for=condition=complete job/…` and `kubectl logs job/…`. Convert it to a `CronJob` with `concurrencyPolicy: Forbid`.

A Job can run more than once under retries, so its work must be idempotent. Database migrations in particular need a design (D06 §6.7.3), not just a Job.

### 1.8.2 Worked example — persistence is not durability

```bash
cat <<'EOF' | kubectl -n "$NS" apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: scratch }
spec:
  accessModes: ["ReadWriteOnce"]
  resources: { requests: { storage: 64Mi } }
EOF
kubectl -n "$NS" get pvc,storageclass
```

On kind, the default StorageClass (rancher local-path) stores data **on one node's filesystem**. A PVC survives Pod deletion; it does **not** survive node loss or cluster deletion, and it is **not a backup**.

> **Honest scope:** running a production database in Kubernetes is an operations discipline of its own (replication, failover, backups, upgrades). Harbour's recommended path for real data is a managed database (see C03); an in-cluster database is a **training** convenience. Delete the PVC when done: `kubectl -n "$NS" delete pvc scratch`.

---

## Section 1.9 — Packaging: Kustomize and Helm

### 1.9.1 Choosing deliberately

| Need | Prefer | Why |
| --- | --- | --- |
| Our own app, environment overlays, Git diffs that read like YAML | Kustomize | No template language; patches are plain YAML; built into `kubectl` |
| Third-party software (controllers, databases) | Helm charts | Ecosystem distributes them as charts; values expose supported knobs |
| Reusable, parameterised package for many teams | Helm (or higher-level templates, P03) | Values schema, versioned releases |
| Both | Helm for vendors, Kustomize for ours; render Helm to YAML in CI if you need reviewable diffs | Avoid templating logic leaking into app config |

### 1.9.2 Worked example — Harbour as a Helm chart

```text
deploy/helm/harbour-api/
  Chart.yaml
  values.yaml
  templates/
    deployment.yaml
    service.yaml
```

`Chart.yaml`:

```yaml
apiVersion: v2
name: harbour-api
description: Harbour sample API
type: application
version: 0.1.0        # chart version
appVersion: "p01"     # informational; deploys use image.digest
```

`values.yaml`:

```yaml
replicaCount: 2
image:
  repository: localhost:5001/harbour-api
  digest: ""            # required: sha256:…
env:
  HARBOUR_ENV: helm
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits: { memory: 256Mi }
```

`templates/deployment.yaml` (abridged to the parts that differ from §1.3.2 — a real chart carries the full probe/securityContext blocks):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
  labels:
    app: harbour-api
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: harbour-api
  template:
    metadata:
      labels:
        app: harbour-api
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: harbour-api
          image: "{{ .Values.image.repository }}@{{ required "image.digest is required" .Values.image.digest }}"
          ports: [{ name: http, containerPort: 8000 }]
          env:
            {{- range $k, $v := .Values.env }}
            - { name: {{ $k }}, value: {{ $v | quote }} }
            {{- end }}
          readinessProbe: { httpGet: { path: /ready, port: http }, periodSeconds: 5 }
          livenessProbe: { httpGet: { path: /health, port: http }, periodSeconds: 10 }
          resources: {{- toYaml .Values.resources | nindent 12 }}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          volumeMounts: [{ name: tmp, mountPath: /tmp }]
      volumes: [{ name: tmp, emptyDir: {} }]
```

`templates/service.yaml` mirrors §1.3.2 with `{{ .Release.Name }}`.

```bash
helm lint deploy/helm/harbour-api --set image.digest="$IMAGE_DIGEST"
helm template harbour-helm deploy/helm/harbour-api --set image.digest="$IMAGE_DIGEST" \
  | kubectl -n "$NS" apply --dry-run=server -f -
# Real install to a separate namespace so it does not fight the Kustomize release:
kubectl create namespace harbour-helm --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install harbour-helm deploy/helm/harbour-api -n harbour-helm --set image.digest="$IMAGE_DIGEST" --wait --timeout 2m
helm -n harbour-helm list; helm -n harbour-helm history harbour-helm
```

Forgetting `--set image.digest` must **fail** (`required`). That is a template-level guard; compare with the policy guard you will add in P02 §2.4.

**Equivalence warning:** the Helm template above is intentionally abbreviated relative to the hardened Kustomize Deployment (seccomp, `automountServiceAccountToken`, startup probe, etc.). Do **not** claim packaging equivalence unless you either (a) expand the chart to match the hardened base, or (b) run a rendered-manifest comparison / conformance check (`helm template …` vs `kubectl kustomize …`) and document remaining deltas. P03/P04 conformance is the stricter bar.

### 1.9.3 Ownership rule

One release must have **one owner**. If Flux (D06) applies Kustomize to `harbour-staging`, do not also `helm install` into it. The lab uses separate namespaces. Write the rule into ADR 0302.

### 1.9.4 ADR prompt — `docs/decisions/0302-harbour-packaging.md`

Cover: Kustomize vs Helm for Harbour; where vendor charts are pinned (chart version **and** image digests); how digests get into Git (PR, not `--set` on a laptop); how rendered output is validated (`kubectl apply --dry-run=server`, `kubectl diff`, optionally `kubeconform`); and what you refuse to template.

### 1.9.5 Verify

- `kubectl kustomize … | kubectl apply --dry-run=server -f -` succeeds for staging.
- `helm template` output validates server-side; missing digest fails.
- Your ADR names an owner for each namespace.

---

## Section 1.10 — Recovery under the workload definition alone

This section is the checklist acceptance test. The definition of "alone": **no** `kubectl` fix, restart, scale, or manifest edit after the failure. Only the Deployment/ReplicaSet/kubelet/Service machinery you already applied.

### 1.10.1 Worked example — single pod kill with client evidence

```bash
kubectl -n "$NS" rollout status deploy/harbour-api --timeout=60s
run_probe 90                                  # §1.4.2
sleep 10                                      # baseline healthy period
VICTIM="$(kubectl -n "$NS" get pod -l app=harbour-api -o jsonpath='{.items[0].metadata.name}')"
date +%T; kubectl -n "$NS" delete pod "$VICTIM"
kubectl -n "$NS" get pods -w --request-timeout=45s || true
kubectl -n "$NS" wait --for=condition=Ready pod -l app=harbour-api --timeout=60s
kubectl -n "$NS" wait --for=jsonpath='{.status.phase}'=Succeeded pod/probe-client --timeout=120s
kubectl -n "$NS" logs probe-client | tail -n 1        # SUMMARY ok=… bad=…
kubectl -n "$NS" logs probe-client | grep -E '^[0-9:]{8} ' | grep -vc ' 200$'   # non-200 lines
```

**Expected:** replacement Pod with a new name appears; Deployment returns to 2/2; `bad` is **zero or very small** because the other replica kept serving and the terminating Pod's `preStop` window drained connections. Record the exact numbers, whatever they are.

### 1.10.2 Worked example — all pods at once (find the honest limit)

```bash
run_probe 90; sleep 10
kubectl -n "$NS" delete pod -l app=harbour-api
kubectl -n "$NS" wait --for=condition=Ready pod -l app=harbour-api --timeout=90s
kubectl -n "$NS" wait --for=jsonpath='{.status.phase}'=Succeeded pod/probe-client --timeout=120s
kubectl -n "$NS" logs probe-client | grep -E 'SUMMARY|URLError|HTTPError|Timeout' | sort | uniq -c
```

**Expected:** a short burst of errors while replacements start and pass readiness, then recovery with **no human action**. That burst is your measured recovery window. Compare it to what a user could tolerate; if the answer is "none," the design (replicas, startup time, PDB, spread) needs work — not the claim.

### 1.10.3 Optional drill — lose a node

```bash
docker stop "${LAB_CLUSTER}-worker"
kubectl get nodes -w --request-timeout=90s || true
kubectl -n "$NS" get pods -o wide
docker start "${LAB_CLUSTER}-worker"
```

Observe: the node becomes `NotReady`, Kubernetes adds `node.kubernetes.io/unreachable` taints, and Pods on it are only evicted after the default toleration (about 300 s). Meanwhile the Service stops sending traffic to those Pods once they fail readiness/endpoint conditions, and the replica on the other worker serves. Tuning `tolerationSeconds` trades faster rescheduling for more churn on flaky networks — a decision for an ADR, not a default to copy.

### 1.10.4 What you may and may not claim

| Evidence you have | Claim you may make | Claim you may **not** make |
| --- | --- | --- |
| Pod kill → Deployment replaces → probe shows ok/bad counts | "Harbour recovers from single-pod loss without intervention; measured client impact X" | "Harbour is highly available" |
| Two replicas on two kind nodes | "Replicas are scheduled across nodes" | "Survives node/zone failure" (one host, one control plane) |
| Node-stop drill | "Pods reschedule after node loss within ~T seconds on kind" | "Production failover time" |
| PDB defined | "Voluntary disruptions are bounded" | "Crashes and node loss are bounded" |
| Local-path PVC | "Data survived Pod restart" | "Data is durable or backed up" |

### 1.10.5 Reflect

Which parts of the recovery were Kubernetes, and which were **your definition** (probes, replicas, `maxUnavailable: 0`, `preStop`, spread)? If you removed one setting at a time, which would change the `bad` count most? Try it.

---

## Section 1.11 — Troubleshooting field guide

Start with: `kubectl get pods -o wide` → `kubectl describe pod` (Events at the bottom) → `kubectl logs --previous` → `kubectl get events --sort-by=.lastTimestamp`.

| Symptom | Likely cause | First checks |
| --- | --- | --- |
| `ImagePullBackOff` / `ErrImagePull` | Wrong name/digest; registry unreachable from node; missing pull secret | `describe` events; `docker exec <node> crictl pull "$IMAGE"` |
| `CrashLoopBackOff` | App exits; liveness kills it; read-only fs write | `logs --previous`; exit code; probe events |
| `CreateContainerConfigError` | Missing ConfigMap/Secret; `runAsNonRoot` with non-numeric image user | `describe` message text |
| `Pending` (unschedulable) | Requests exceed node capacity; taints; unbound PVC; `DoNotSchedule` spread | `describe` → `FailedScheduling` |
| Running but `0/1` Ready | Readiness probe failing | Probe path/port; `curl` from inside the Pod; app dependency |
| Service has no endpoints | Selector/labels mismatch; no Pods ready; wrong `targetPort` name | `get endpointslices`; `get pods --show-labels` |
| `OOMKilled` | Memory limit too low or leak | `describe`; `kubectl top`; raise limit **with evidence** |
| Rollout stuck | New Pods never ready; `maxUnavailable: 0` with no spare capacity | `rollout status`; `describe rs`; `progressDeadlineSeconds` |
| Connection works then breaks | Used `port-forward`; Pod replaced | Use in-cluster client |
| `Forbidden` | RBAC | P02 §2.2 |

---

## Practical Assessment — Chapter 1 — sound workloads that recover

Align with [P01 Course Detail](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) and Final Project Checklist P01.

### Required deliverables

1. **Cluster record** — kind config, pinned node image reference, registry wiring notes, and the measured **cluster rebuild time** from §1.2.3.
2. **Manifests in Git** — `deploy/harbour-api/` base + staging overlay (Kustomize) with digest-addressed image, non-root, read-only root filesystem, dropped capabilities, resource requests and a memory limit.
3. **Probe evidence** — startup, readiness and liveness configured; recorded outputs for readiness-failure (no restart, traffic removed, old Pods kept serving) **and** liveness-failure (restarts) experiments.
4. **Recovery demo (compulsory client-facing evidence)** — single-pod kill **and** all-pod delete with in-cluster client-loop logs, quantified `ok`/`bad` (non-200) counts during termination, and a statement that **no manual intervention** occurred after the kill. Controller `Ready 2/2` alone does **not** pass.
5. **Networking notes** — Service → EndpointSlice → Pod mapping; why `port-forward` was not used as evidence.
6. **Configuration/secret note** — ConfigMap-triggered rollout shown; Secret limitations and your chosen handling path stated; no real secrets in Git.
7. **Packaging ADRs** — `0301` (runtime substrate, honest limits, resource stance) and `0302` (Kustomize vs Helm, ownership, digest handling), plus a validated Helm chart or a written reason you did not need one.
8. **Availability claims table** — what you claim and prove, and what you explicitly do not (§1.10.4 adapted to your results).

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Workload definition | Pod or Deployment that runs | Deployment with labels, strategy, security context, resources, digest | PDB + spread + graceful shutdown verified by test |
| Probes | Probe copied from a blog | Three probes with separate semantics; failure experiments recorded | Probe design rationale tied to Harbour dependencies and rollout safety |
| Recovery | "I deleted the pod and it came back" | Client-side measured impact, no manual steps, kill-all window recorded | Node-loss drill with eviction timing explained |
| Networking | Used `port-forward` | Service/DNS/EndpointSlice explained with evidence | Gateway/Ingress path or NetworkPolicy-ready design |
| Config & secrets | Env vars in image or Git | ConfigMap rollout; Secret caveats; out-of-band handling named | Secret mount strategy and rotation notes |
| Packaging | One YAML file | Kustomize overlays + digest; ADR on Helm vs Kustomize | Rendered-diff validation in CI |
| Honesty | "HA on Kubernetes" | Claims table bounded by kind limits | Training-to-production gap list with cost/risk |

**Completion standard:** **Competent** on every row. Another engineer can apply your overlay to a fresh kind cluster, see workloads ready under probes, kill a Pod and see recovery from the Deployment alone — and knows what you did **not** prove.

### Self-check

- Is every image reference in Git digest-addressed (or is the exception written down)?
- Did you ever repair the workload with `kubectl` after the kill? If yes, the test is invalid.
- Could the client loop have been fooled by a surviving replica? Did you also run the kill-all test?
- Does your ADR say "kind is one host" anywhere a reader might assume resilience?
- Are probes tied to what Harbour *actually* checks (including the `unconfigured` database state)?

### Example assessment conclusion (evidence still required)

> kind cluster `harbour-lab` (1 control-plane, 2 workers, one host) with a local registry. Harbour deployed from `deploy/harbour-api/overlays/staging` by digest `sha256:…`; non-root, read-only rootfs, memory limit 256Mi, no CPU limit by ADR 0301. Readiness failure left 0/1 Ready with zero restarts while old Pods served; liveness failure produced restarts. Single-pod kill: `ok=…, bad=…`; all-pod delete: errors for ~N s then recovery without intervention. Helm chart validated server-side; ADR 0302 keeps Kustomize for Harbour and Helm for vendors. Not claimed: node/zone HA, durable storage, production load behaviour.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Run a stateless service | Deployment + Service + probes + requests | Bare Pods |
| Gate traffic | Readiness probe | Restarting to "fix" readiness |
| Detect a wedged process | Cheap liveness, no dependencies | Liveness that checks the DB |
| Prove recovery | In-cluster client loop + kill test | `port-forward` + "it came back" |
| Pin an image | `repo@sha256:…` via overlay | `:latest` or mutable tags |
| Change config | Generated ConfigMap hash → rollout | Editing a stable ConfigMap and hoping |
| Handle credentials | Out-of-band secret manager/operator | Secret YAML with values in Git |
| Package our app / vendor software | Kustomize / Helm | Two owners of one release |
| Claim availability | State replicas, spread, failure domains tested | "Kubernetes makes it HA" |

## Glossary

| Term | Definition |
| --- | --- |
| Control plane | API server, etcd, scheduler, controller manager |
| Kubelet | Node agent that runs Pods and probes |
| Pod | Smallest schedulable unit; one or more containers |
| ReplicaSet / Deployment | Maintains N Pods / manages ReplicaSets across versions |
| Selector / label | Key-value tagging and the query that uses it |
| Probe | Kubelet health check: startup, readiness, liveness |
| EndpointSlice | List of ready backend addresses for a Service |
| QoS class | Guaranteed / Burstable / BestEffort — eviction priority |
| OOMKilled | Container exceeded its memory limit |
| PDB | PodDisruptionBudget — bounds voluntary evictions |
| Digest | Content hash identifying an image immutably |
| Kustomize / Helm | Overlay-based vs template/chart-based packaging |

## References

- [Kubernetes concepts](https://kubernetes.io/docs/concepts/) · [Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Workloads: Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Resource management for Pods](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Pod lifecycle and termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Services and networking](https://kubernetes.io/docs/concepts/services-networking/)
- [Secrets good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [kind](https://kind.sigs.k8s.io/) · [kind local registry](https://kind.sigs.k8s.io/docs/user/local-registry/)
- [Kustomize](https://kubectl.docs.kubernetes.io/references/kustomize/) · [Helm docs](https://helm.sh/docs/)
- CNCF certification curricula (CKAD, KCNA): check the **current** published curriculum and map objectives yourself; this chapter does not guarantee exam coverage.

**Previous chapter:** [DevOps — D06 GitOps, Automation and Operations](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) · **Course detail:** [P01 — Kubernetes and Cloud-Native Fundamentals](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) · **Next chapter:** [Chapter 2 — Kubernetes Administration and Operations](P02%20Kubernetes%20Administration%20and%20Operations.md) · **Checklist:** [Final Project Checklist · P01](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
