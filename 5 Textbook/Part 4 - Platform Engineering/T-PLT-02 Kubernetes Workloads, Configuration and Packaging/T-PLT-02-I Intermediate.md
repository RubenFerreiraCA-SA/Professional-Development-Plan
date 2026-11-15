# T-PLT-02-I — Intermediate Practice

*Chapter: [T-PLT-02 — Kubernetes Workloads, Configuration and Packaging](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-02-i"></a>
#### T-PLT-02-I — Intermediate Practice

**What changes at this level.** At the beginner level you read and ran one service by hand. Here you make changes safely and repeatably: you control how a rollout proceeds, you diagnose a rollout that does not complete, you manage configuration so that changes roll out predictably, and you package the result so that two environments differ only where they are meant to. Every section ends in something you can demonstrate.

**Choosing deliberately**

| Need | Prefer | Why |
| --- | --- | --- |
| Your own app with environment overlays | Kustomize | No templating logic; patches are plain YAML |
| Third-party software (controllers, databases) | Helm charts | Ecosystem distributes them; values expose supported options |
| A reusable, parameterised package for many teams | Helm or a higher-level template | Values schema, versioned releases |
| Both | Helm for vendors, Kustomize for ours; render Helm to YAML in CI if you need reviewable diffs | Avoid logic leaking into app config |

**Controlling a rollout.** The rolling update strategy has two dials, and a third setting decides when a stalled rollout is declared failed.

```yaml
spec:
  replicas: 4
  minReadySeconds: 10             # a Pod must stay ready this long before it counts as available
  progressDeadlineSeconds: 300    # report failure if no progress for 5 minutes
  revisionHistoryLimit: 5         # old ReplicaSets kept for rollback
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 25%, maxUnavailable: 0 }
```

| Setting | Effect | Trade-off |
| --- | --- | --- |
| `maxUnavailable: 0` | Capacity never drops during the update | Needs spare cluster capacity for the surge Pod |
| `maxSurge: 0, maxUnavailable: 1` | No extra capacity needed | Capacity dips by one Pod; slower on a busy service |
| `minReadySeconds` | Filters out Pods that pass readiness once and then crash | Lengthens every rollout by that time per step |
| `progressDeadlineSeconds` | Turns a silent stall into a `ProgressDeadlineExceeded` condition | Does **not** roll back; it only reports. Your pipeline must act on it |
| `type: Recreate` | Stops all old Pods first | Downtime; acceptable only when two versions must never run together |

Kubernetes never rolls back automatically. A failed rollout leaves the old Pods serving and the new ones not ready; a pipeline step such as `kubectl rollout status --timeout=6m` that exits non-zero is what tells your tooling to stop or revert.

```bash
kubectl rollout status deploy/orders-api -n orders-staging --timeout=6m || {
  kubectl rollout undo deploy/orders-api -n orders-staging
  exit 1
}
```

**Termination: the other half of a safe rollout.** Replacing a Pod means stopping one. The sequence is: the Pod is marked terminating and removed from Service endpoints; `preStop` runs; the container receives `SIGTERM`; after `terminationGracePeriodSeconds` it receives `SIGKILL`. Endpoint removal and `SIGTERM` happen at roughly the same time, so some clients still send requests to a Pod that has begun shutting down.

```yaml
      terminationGracePeriodSeconds: 45
      containers:
        - name: api
          lifecycle:
            preStop:
              exec: { command: ["sleep", "5"] }   # let endpoint removal propagate before SIGTERM
```

The application must handle `SIGTERM` by finishing in-flight requests and then exiting within the grace period. A service that exits instantly on `SIGTERM`, or that ignores it and gets killed after 30 seconds, produces dropped requests on every deploy. Test it: run a steady request loop during a rollout and count the errors.

**Diagnosing a readiness failure.** A readiness failure is the most common reason a rollout "hangs". Work through it in a fixed order, because each step rules out a class of cause.

```bash
kubectl get pods -n orders-staging -l app=orders-api -o wide      # 1. Which Pods, which ReplicaSet hash, how old, which node
kubectl describe pod <new-pod> -n orders-staging                  # 2. Probe definition, last probe result, events
kubectl logs <new-pod> -n orders-staging                          # 3. What the application says
kubectl exec <new-pod> -n orders-staging -- wget -qO- localhost:8000/ready   # 4. Ask the probe's question yourself
kubectl get endpoints orders-api -n orders-staging                # 5. Is the Pod absent from the Service?
```

| Observation | Meaning | Typical cause |
| --- | --- | --- |
| `Readiness probe failed: connection refused` | Nothing listening on that port yet | Wrong port; slow start with no startup probe; app bound to `127.0.0.1` |
| `Readiness probe failed: statuscode: 503` | App is up and says it is not ready | Dependency (database, config) missing; migration pending |
| `Readiness probe failed: context deadline exceeded` | Probe timed out | `timeoutSeconds` (default 1) too low for a slow endpoint |
| Probe passes in `exec`, fails from kubelet | Different network path or Host header | App checks `Host`; bound to loopback only |
| Ready, then not ready, repeatedly | Flapping | Readiness endpoint does expensive work; shared dependency intermittently slow |

Fixes belong at the right layer: correct the port or path in the manifest, add a `startupProbe` for slow starters rather than raising `initialDelaySeconds` on every probe, and raise `timeoutSeconds` only after confirming the endpoint is legitimately slow. Making a readiness probe pass by pointing it at a trivial `/` that always returns 200 hides the problem and sends traffic to Pods that cannot serve it.

**Configuration management: where each kind of value lives.**

| Kind of value | Example | Where | Rollout behaviour |
| --- | --- | --- | --- |
| Build-time constant | Default timeouts compiled in | Image | New image, new rollout |
| Environment difference | Replica count, log level, hostname | Overlay or values file in Git | Rollout on change |
| Behaviour toggle | `FEATURE_X=off` | ConfigMap | Rollout if hash-named; otherwise stale until restart |
| Credential | Database password | Secret from an external source | Rotate the source, then roll Pods |
| Runtime-tunable | Feature flags changed without deploy | A flag service, not a ConfigMap | None; app polls |

**Config change triggers a rollout.** A plain ConfigMap edited in place does not restart any Pod, so running Pods and newly started Pods can hold different configuration for days. Generate ConfigMaps with a content hash in the name so that every change creates a new object and the Deployment's Pod template changes with it.

```yaml
configMapGenerator:
  - name: orders-config
    literals: [LOG_LEVEL=info, FEATURE_X=off]
```

```bash
kubectl kustomize overlays/staging | grep -E 'name: orders-config'
# name: orders-config-8k2g7f5d9b          <- hash suffix; changes whenever the literals change
# change FEATURE_X=on, render again: a new suffix appears and the Deployment references it
```

Change a literal, apply, and watch a new ReplicaSet roll out. The old ConfigMap remains for rollback, so `kubectl rollout undo` restores the *old config together with the old Pods*; that coupling is the main reason to prefer hashed names over in-place edits. For Helm the equivalent is the `checksum/config` annotation shown below.

**Immutability and cleanup.** Hash-named ConfigMaps accumulate. Kustomize prunes only with an explicit ownership label and `kubectl apply --prune` or a GitOps controller; Helm removes superseded objects as part of a release. Check that old generations are cleaned up, but keep at least `revisionHistoryLimit` generations so a rollback still has its config. Setting `immutable: true` on a ConfigMap or Secret protects against accidental edits and reduces API server load, at the price that every change is a new object.

**Writing a good chart**

```yaml
# templates/deployment.yaml (excerpt)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "orders-api.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels: {{- include "orders-api.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels: {{- include "orders-api.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: api
          image: "{{ .Values.image.repository }}@{{ required "image.digest is required" .Values.image.digest }}"
          resources: {{- toYaml .Values.resources | nindent 12 }}
```

Practices: ship a `values.schema.json` to reject bad values early; require the image digest; keep secure defaults (non-root, read-only filesystem, no privilege escalation); use the checksum annotation so config changes roll Pods; keep templates shallow; test with `helm lint`, `helm template` and a policy check.

A minimal schema that catches the most common mistakes:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image"],
  "additionalProperties": false,
  "properties": {
    "replicaCount": { "type": "integer", "minimum": 1, "maximum": 20 },
    "image": {
      "type": "object",
      "required": ["repository", "digest"],
      "properties": {
        "repository": { "type": "string" },
        "digest": { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" }
      }
    }
  }
}
```

`additionalProperties: false` is what turns a typo such as `replicaCout: 3` from a silently ignored line into an install error. Without it, a mistyped value leaves the default in place and the reviewer sees no problem.

**Helm values: layering and review.** Values merge from the chart's `values.yaml`, then each `-f` file in order, then `--set`. Later sources win, and lists are replaced, not merged. Keep a small shared file and one file per environment.

```bash
helm template orders-api ./orders-api -f values/base.yaml -f values/staging.yaml > /tmp/staging.yaml
helm template orders-api ./orders-api -f values/base.yaml -f values/production.yaml > /tmp/production.yaml
diff /tmp/staging.yaml /tmp/production.yaml        # the real, rendered difference between environments
helm get values orders-api -n orders-staging       # what is actually installed
helm upgrade --install orders-api ./orders-api -n orders-staging -f values/base.yaml -f values/staging.yaml --atomic --timeout 6m
```

`--atomic` rolls the release back if the upgrade does not become ready within the timeout; it still needs readiness probes to be meaningful. Avoid `--set` in pipelines: it leaves no reviewable record.

**Overlay patterns.** Use a base for everything shared; overlays for environment differences (replica counts, resource sizes, hostnames, image digest); strategic-merge patches or JSON patches for edits; generators for ConfigMaps with content hashes in names so changes trigger rollouts.

```text
base/                     deployment.yaml  service.yaml  kustomization.yaml
overlays/staging/         kustomization.yaml            patch-replicas.yaml
overlays/production/      kustomization.yaml            patch-replicas.yaml  patch-resources.yaml
```

```yaml
# overlays/production/kustomization.yaml
resources: [../../base]
namespace: orders-prod
images:
  - name: registry.example.com/orders-api
    digest: sha256:7ab2...41cd          # promoted from staging unchanged
patches:
  - path: patch-replicas.yaml
  - path: patch-resources.yaml
configMapGenerator:
  - name: orders-config
    behavior: merge
    literals: [LOG_LEVEL=warn]
```

Guidelines: an overlay should contain only differences; if an overlay copies most of the base, the base is wrong. Avoid more than two layers (base, environment); a third layer for region or tenant is acceptable only when the differences are truly independent. Always render and read the output before applying.

| Pattern | Use for | Caution |
| --- | --- | --- |
| Strategic-merge patch | Adding or changing fields in a known object | Lists of containers merge by name; check the output |
| JSON 6902 patch | Precise replace/remove at a path | Breaks silently if the path moves in the base |
| `images:` transformer | Promoting a digest | Matches by image name, not by container name |
| `components:` | A reusable optional feature (for example metrics sidecar) | Order of components matters |

**Troubleshooting packaging.** Most packaging faults appear at render time or at the first apply, and each has a standard tool.

| Symptom | Cause | Check |
| --- | --- | --- |
| `helm template` error `nil pointer evaluating interface` | A value used but not defined | Add a default or a schema `required` entry |
| Rendered YAML has wrong indentation | `nindent` count wrong | `helm template` and read it; `--debug` prints the failing template |
| `helm upgrade` fails: `rendered manifests contain a resource that already exists` | Object created outside Helm | Check owner annotations; adopt or delete deliberately |
| `field is immutable` on apply | Changed a selector or `volumeClaimTemplates` | Recreate the object; plan a migration |
| Kustomize patch has no effect | Target name or kind does not match after a `namePrefix` | `kubectl kustomize` and search for the target |
| Rollout does not start after a config change | Plain ConfigMap, no hash | Use a generator or checksum annotation |
| Deployment healthy in staging, `CreateContainerConfigError` in production | Secret or key exists only in staging | `kubectl describe pod` events; compare env prerequisites |

**Packaging workflow.** A change should go through the same path every time:

```text
edit base/overlay or values  ->  render (kustomize build / helm template)
  ->  validate (kubeconform or kubectl --dry-run=server, policy check)
  ->  diff rendered output against the current environment
  ->  review  ->  apply (one owner)  ->  rollout status with timeout  ->  record
```

```bash
kubectl kustomize overlays/staging > rendered.yaml
kubectl apply --dry-run=server -f rendered.yaml            # API-server validation, no change
kubectl diff -f rendered.yaml                              # what apply would change live
kubectl apply -f rendered.yaml && kubectl rollout status deploy/orders-api -n orders-staging --timeout=6m
```

`kubectl diff` is the cheapest safety net available to an individual engineer; make it a habit before every apply. Promotion between environments should move the **same image digest** and the **same base**; only the overlay differs.

**Workload shapes in practice.** Write a Job that checks readiness and exits non-zero on failure (`backoffLimit: 1`, `ttlSecondsAfterFinished: 300`, `restartPolicy: Never`, same hardened security context). Write a CronJob with `concurrencyPolicy: Forbid`. Demonstrate that a StatefulSet's Pods keep stable names and volumes across restarts, and that a persistent volume claim outlives the Pod but not a lost node.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: invoice-export }
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid          # never overlap runs
  startingDeadlineSeconds: 600       # skip a run missed by more than 10 minutes
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      ttlSecondsAfterFinished: 86400
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: export
              image: registry.example.com/invoice-export@sha256:5e0d...a713
```

**Autoscaling basics.** A HorizontalPodAutoscaler scales replicas on metrics (CPU utilisation relative to requests by default). It needs a metrics source and correct requests; unknown metrics usually mean no metrics server. Demonstrate scale-out under controlled load, not only that the autoscaler object exists.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: orders-api }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: orders-api }
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 60 } }
```

Because utilisation is measured against the request, a request that is too low makes the autoscaler scale out early, and a request that is too high makes it scale late. When the HPA owns the replica count, remove `replicas` from the manifest in Git; otherwise every apply resets it.

**Resource sizing from evidence.** Start requests near observed p50 to p90 usage, set a memory limit with headroom above the observed peak, and consider leaving the CPU limit unset to avoid throttling while keeping the CPU request meaningful.

```bash
kubectl top pod -n orders-staging --containers
kubectl get pod <pod> -n orders-staging -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'   # OOMKilled?
```

Record the sizing decision and the data behind it; a number with no stated evidence cannot be revisited sensibly.

**Exercise 1 (rollout control).** Deploy a service with four replicas. Release a version that fails readiness and show, with commands, that the old Pods kept serving. Set `progressDeadlineSeconds`, observe the `ProgressDeadlineExceeded` condition, and add a pipeline step that rolls back on timeout.

**Exercise 2 (graceful termination).** Run a request loop against the service during a rollout and count failures. Add a `preStop` sleep and signal handling, repeat, and report the before and after error counts.

**Exercise 3 (packaging).** Convert a service to a chart with a values schema, install it to two namespaces with different values, and demonstrate a config-triggered rollout. Then produce the same result with Kustomize overlays and write a short note on which diff was easier to review.

**Exercise 4 (diagnosis).** Given a Deployment with a wrong readiness port, a missing Secret key and a selector typo, diagnose each from the commands in this section and record symptom, command and fix.

**Self-check questions**

1. Why does `kubectl rollout undo` not need anything from Git, and why is that both useful and dangerous?
2. What does `progressDeadlineSeconds` do, and what does it not do?
3. Why do hash-named ConfigMaps make rollbacks safer than in-place edits?
4. A teammate sets `replicas: 3` in Git and also enables an HPA. What happens at the next apply?
5. Which Helm value source wins when the same key appears in `values.yaml`, a `-f` file and `--set`?

**Definition of done for this level.** You can roll out, pause, diagnose and reverse a release; show that a config change produces a new rollout; produce reviewable rendered diffs between environments; and demonstrate graceful termination and autoscaling with measurements rather than assertions.
