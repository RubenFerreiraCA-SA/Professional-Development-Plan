# T-PLT-02-B — Beginner Foundations

*Chapter: [T-PLT-02 — Kubernetes Workloads, Configuration and Packaging](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-02-b"></a>
#### T-PLT-02-B — Beginner Foundations

**Why this topic comes after the architecture chapter.** A cluster is only useful once you can describe, in plain objects, the thing you want it to run. This section teaches the small set of workload and configuration objects that describe one stateless web service, then shows why a packaging layer (Kustomize or Helm) sits on top of them. Read the objects first; packaging only makes sense once you know what is being packaged.

**Core vocabulary**

| Term | Meaning |
| --- | --- |
| Pod | The smallest deployable unit: one or more containers sharing a network namespace (one Pod IP) and optional volumes. Pods are disposable. |
| ReplicaSet | A controller that keeps a stated number of identical Pods running. You rarely write one by hand. |
| Deployment | A controller that manages ReplicaSets so you can roll out a new version and roll back. It is the normal way to run a stateless service. |
| Label | A key/value pair on an object, for example `app: orders-api`. Labels are how objects find each other. |
| Selector | A query over labels. A Deployment uses one to find its Pods; a Service uses one to find its endpoints. |
| Service (ClusterIP) | A stable virtual IP and DNS name that load-balances to the ready Pods matching its selector. |
| ConfigMap | Non-secret configuration as key/value pairs or file contents. |
| Secret | Sensitive values, stored base64-encoded and subject to tighter access rules. |
| Probe | A check the kubelet runs against a container: liveness, readiness or startup. |
| Request / limit | The CPU and memory a container is guaranteed (request, used for scheduling) and the ceiling it may use (limit). |
| Namespace | A named scope inside a cluster for grouping and access control. |

**The ownership chain.** You declare a Deployment. The Deployment creates a ReplicaSet. The ReplicaSet creates Pods. Each Pod runs containers. Deleting a Pod owned by a ReplicaSet simply makes the ReplicaSet create a replacement; to remove the service you delete the Deployment.

```text
Deployment orders-api
  └── ReplicaSet orders-api-6d5f9c7b8        (one per Pod template version)
        ├── Pod orders-api-6d5f9c7b8-abcde
        └── Pod orders-api-6d5f9c7b8-fghij
Service orders-api  ──selector app=orders-api──▶  ready Pods only
```

**A Deployment, read line by line**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: orders-staging
  labels: { app: orders-api }
spec:
  replicas: 2                      # desired number of Pods
  selector:
    matchLabels: { app: orders-api }   # which Pods this Deployment owns
  template:                        # the Pod blueprint
    metadata:
      labels: { app: orders-api }      # MUST satisfy the selector above
    spec:
      containers:
        - name: api
          image: registry.example.com/orders-api@sha256:3f1c...e9a0
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef: { name: orders-api-config }
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef: { name: orders-api-db, key: password }
          volumeMounts:
            - { name: app-config, mountPath: /etc/orders, readOnly: true }
          resources:
            requests: { cpu: 100m, memory: 128Mi }
            limits:   { memory: 256Mi }
          startupProbe:
            httpGet: { path: /health, port: 8000 }
            failureThreshold: 30
            periodSeconds: 2
          readinessProbe:
            httpGet: { path: /ready, port: 8000 }
            periodSeconds: 5
          livenessProbe:
            httpGet: { path: /health, port: 8000 }
            periodSeconds: 10
            failureThreshold: 3
      volumes:
        - name: app-config
          configMap: { name: orders-api-files }
```

Field by field: `replicas` is how many Pods you want; `selector.matchLabels` is how the Deployment recognises its own Pods; `template` is the Pod blueprint; `template.metadata.labels` must match the selector or the API server rejects the Deployment; `image` should be pinned by digest or an immutable tag, not `latest`; `containerPort` documents the port the process listens on (it does not open anything by itself).

**A Service, and why Pod IPs are never hard-coded**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: orders-api
  namespace: orders-staging
spec:
  type: ClusterIP
  selector: { app: orders-api }
  ports:
    - { name: http, port: 80, targetPort: 8000 }
```

Pods are replaced constantly, and each replacement gets a new IP. The Service gives clients a stable name (`orders-api.orders-staging.svc.cluster.local`, or just `orders-api` inside the same namespace) and a stable virtual IP. Behind it, Kubernetes maintains a list of endpoints: the IPs of Pods that match the selector **and are ready**. `port` is what clients call; `targetPort` is the container port. A ClusterIP Service is reachable only from inside the cluster.

**ConfigMaps and Secrets: two ways to consume each**

```bash
kubectl create configmap orders-api-config --from-literal=LOG_LEVEL=info --from-literal=PAGE_SIZE=50
kubectl create secret generic orders-api-db --from-literal=password='<generated-value>'
kubectl get secret orders-api-db -o jsonpath='{.data.password}' | base64 -d
```

| Consumption | How | Behaviour to remember |
| --- | --- | --- |
| Environment variable | `env.valueFrom.configMapKeyRef` / `secretKeyRef`, or `envFrom` | Read once when the container starts. Changing the object later does not change a running Pod; restart the Pods. |
| Mounted file | A `volume` of type `configMap` or `secret` plus a `volumeMount` | Files are refreshed eventually when the object changes (not for `subPath` mounts). The application must re-read them. |

**Base64 is not encryption.** The last command above shows the point: anyone who can `get` the Secret can decode it in one step. A Secret is a separate object so that access can be controlled with RBAC and (if configured) encrypted at rest, and so that the value stays out of images and Deployment YAML. It is not safe to commit a Secret manifest to Git. Never put the database password in a ConfigMap, in the image, or in `env.value:` written inline in the Deployment.

**The three probes: what each asks, and what happens on failure**

| Probe | Question | On failure | Typical endpoint |
| --- | --- | --- | --- |
| Startup | "Has the application finished starting?" | Kubelet restarts the container if it never succeeds within `failureThreshold × periodSeconds`. Other probes are held off until it passes. | `/health` |
| Readiness | "Should this Pod receive traffic right now?" | Pod is removed from the Service endpoints. **It is not restarted.** It returns when the probe passes again. | `/ready` |
| Liveness | "Is the process stuck beyond recovery?" | Kubelet **restarts the container**. | `/health` |

The usual beginner mistake is pointing liveness at a dependency check. If the database is down, every Pod then restarts repeatedly and turns a dependency problem into a full outage. Keep liveness cheap and local; put dependency checks in readiness.

**Requests and limits in one paragraph.** The scheduler places a Pod only on a node with enough unreserved CPU and memory to satisfy the sum of its requests. Exceeding a CPU limit throttles the container; exceeding a memory limit kills it (`OOMKilled`). A Pod with no requests can be packed onto an overloaded node. Start with measured requests, then tune.

**First commands**

```bash
kubectl apply -f deployment.yaml -f service.yaml
kubectl get deploy,rs,pods,svc -n orders-staging -o wide
kubectl describe deployment orders-api -n orders-staging     # replicas, strategy, events
kubectl describe pod <pod> -n orders-staging                 # probes, env sources, last state, events
kubectl get endpoints orders-api -n orders-staging           # which Pod IPs are behind the Service
kubectl logs deploy/orders-api -n orders-staging
kubectl rollout status deploy/orders-api -n orders-staging
```

**Common mistakes and how they appear**

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Deployment rejected: selector does not match template labels | Label typo or edited only one side | Compare `spec.selector` and `template.metadata.labels` |
| Service exists but `kubectl get endpoints` is empty | Selector matches no Pod, or no Pod is ready | `kubectl get pods --show-labels`; readiness probe results in `describe pod` |
| `CreateContainerConfigError` | Referenced ConfigMap/Secret or key does not exist | `kubectl describe pod` events |
| `CrashLoopBackOff` right after start | Application error, or liveness probe firing before startup finishes | `kubectl logs --previous`; add a startup probe |
| `Running` but `0/1 Ready` | Readiness probe failing; traffic is correctly withheld | Probe path and port; dependency health |
| `OOMKilled` in last state | Memory limit below real use | `describe pod`; compare usage to limit |
| Config change has no effect | Value was injected as an env var | Restart the rollout: `kubectl rollout restart deploy/orders-api` |

**What a rollout actually does.** Change anything under `spec.template` (the image, an env var, a probe) and the Deployment creates a *new* ReplicaSet, then gradually shifts Pods from the old one to the new one. Changing `replicas` alone does not create a new ReplicaSet; it only rescales the current one. The pace is set by the strategy:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # may run one extra Pod above replicas during the update
      maxUnavailable: 0    # never drop below the desired ready count
```

With `replicas: 2`, `maxSurge: 1` and `maxUnavailable: 0`, Kubernetes starts one new Pod, waits until its readiness probe passes, then terminates one old Pod, and repeats. This is why readiness matters for rollouts and not only for traffic: **a new Pod that never becomes ready stalls the rollout, and the old Pods keep serving.** That is the behaviour you want from a bad release.

```bash
kubectl set image deploy/orders-api api=registry.example.com/orders-api@sha256:7ab2...41cd -n orders-staging
kubectl rollout status deploy/orders-api -n orders-staging       # blocks until done or the deadline passes
kubectl rollout history deploy/orders-api -n orders-staging      # revisions kept (one per ReplicaSet)
kubectl rollout undo deploy/orders-api -n orders-staging         # back to the previous revision
```

Prefer editing the manifest in Git and applying it over `kubectl set image`; the command above is shown so that you can see the mechanism. A hand edit that is not reflected in the file will be overwritten by the next `apply`.

**A worked failure: reading a stalled rollout.** You roll out a new image and `kubectl rollout status` prints "Waiting for deployment "orders-api" rollout to finish: 1 out of 2 new replicas have been updated" and then nothing. Work from the outside in.

```bash
kubectl get pods -n orders-staging -l app=orders-api
# orders-api-6d5f9c7b8-abcde   1/1  Running   0   2d      <- old, still serving
# orders-api-6d5f9c7b8-fghij   1/1  Running   0   2d      <- old, still serving
# orders-api-84c7d6f59-xk2lm   0/1  Running   0   4m      <- new, never ready
kubectl describe pod orders-api-84c7d6f59-xk2lm -n orders-staging | sed -n '/Events/,$p'
# Warning  Unhealthy  Readiness probe failed: HTTP probe failed with statuscode: 503
kubectl logs orders-api-84c7d6f59-xk2lm -n orders-staging
# ERROR  config: missing required setting PAGE_SIZE
```

Reading the evidence: the old ReplicaSet is intact, so users are unaffected; the new Pod is `Running` (the process started) but not `Ready` (the application says it cannot serve); the log gives the cause (a setting the new version requires). The fix is a configuration change, not a restart. Rolling back with `kubectl rollout undo` restores service immediately and buys time; the permanent fix goes through Git. Record the symptom, the command that revealed the cause and the fix; that triple is the evidence format used throughout this chapter.

**Labels: a small design discipline.** The selector of a Deployment is immutable after creation, and a Service selector that is too broad will quietly send traffic to the wrong Pods. Use the standard recommended labels so tools and humans agree on meaning.

| Label | Example | Use |
| --- | --- | --- |
| `app.kubernetes.io/name` | `orders-api` | What the component is; use in selectors |
| `app.kubernetes.io/instance` | `orders-api-staging` | Which installation of it |
| `app.kubernetes.io/version` | `1.8.2` | Informational; never put it in a selector (it would change on every release) |
| `app.kubernetes.io/managed-by` | `kustomize`, `Helm` | Which tool owns the object |

Keep the selector to one or two stable labels. If the selector includes the version, the Deployment can no longer adopt its own next-version Pods.

**Hardening a container: the minimum.** Add a `securityContext` from the first manifest rather than as a later chore.

```yaml
      securityContext:                      # Pod level
        runAsNonRoot: true
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: api
          securityContext:                  # container level
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
```

A read-only root filesystem means the application needs a writable `emptyDir` mounted at `/tmp` if it writes temporary files. Discovering that in staging, from a log line, is far cheaper than discovering it in production.

**Namespaces are a boundary for names, not for the network.** Two Deployments with the same name can live in different namespaces, and a Service in `orders-staging` is reachable from other namespaces by its full DNS name unless a network policy says otherwise. Namespaces give you a scope for quotas and access control; they do not by themselves isolate traffic.

**Why packaging matters.** A real application needs a Deployment, a Service, configuration, probes, resource settings and permissions, often with differences between environments. Copy-pasting YAML into each environment guarantees drift. Packaging tools produce the manifests from shared source plus small, explicit differences. Helm and Kustomize are introduced here only as packaging tools; you do not need to design charts at this level.

**Two common tools**

| Tool | Idea | Strength |
| --- | --- | --- |
| Kustomize | Plain YAML base plus overlays that patch it | No template language; diffs read like YAML; built into `kubectl` |
| Helm | Templated charts with values | Ecosystem of third-party charts; versioned releases |

**Kustomize in miniature**

```text
base/
  deployment.yaml
  service.yaml
  kustomization.yaml          # resources: [deployment.yaml, service.yaml]
overlays/staging/kustomization.yaml
```

```yaml
# overlays/staging/kustomization.yaml
resources: [../../base]
namespace: orders-staging
namePrefix: staging-
patches:
  - target: { kind: Deployment, name: orders-api }
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 2
```

```bash
kubectl kustomize overlays/staging      # render without applying
kubectl apply -k overlays/staging
```

**Helm in miniature**

```bash
helm create orders-api         # scaffold a chart
helm template orders-api ./orders-api -f values-staging.yaml   # render only
helm install orders-api ./orders-api -n orders-staging -f values-staging.yaml
helm list -n orders-staging
helm rollback orders-api 1 -n orders-staging
```

```yaml
# values-staging.yaml
replicaCount: 2
image:
  repository: registry.example.com/orders-api
  digest: sha256:3f1c...e9a0
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits:   { memory: 256Mi }
```

**One owner rule.** A release must have exactly one owner. If a GitOps controller applies Kustomize to a namespace, do not also `helm install` into it.

**Evidence to capture when you describe a workload.** An annotated copy of the Deployment, Service and ConfigMap with each field's purpose in one line; a sketch of Service-to-Pod selection (labels on both sides); and a small table of probe, configuration source and resource settings. Never include a real Secret value in the evidence.

**Exercise 1 (read).** Take the Deployment above. Without running anything, write down: how many Pods will exist, which labels the Service selects, what happens to traffic if `/ready` returns 503 on one Pod, what happens if `/health` fails three times in a row, and where the database password is and is not allowed to appear.

**Exercise 2 (run).** Apply the manifests to a disposable cluster. Break each thing deliberately, one at a time: change a Service selector label, reference a missing ConfigMap key, point readiness at a wrong path. For each break, record the symptom, the command that revealed the cause, and the fix.

**Exercise 3 (compare).** Render the same service with Kustomize and with Helm and compare the output. Note which was easier to read for a reviewer.

**Exercise 4 (roll out and recover).** Deploy version one, then roll out a version that fails readiness (for example, a missing required setting). Confirm that the old Pods keep serving, capture the evidence triple, roll back, and then fix forward by editing the manifest. State in one sentence why the failed rollout did not cause an outage.

**Exercise 5 (harden).** Add the `securityContext` above to your Deployment. Run it, find what breaks (typically a write to a read-only path), and fix it with a mounted `emptyDir` rather than by weakening the context.

**Self-check questions**

1. Why must `template.metadata.labels` satisfy the selector, and why should a version label not be in the selector?
2. A Pod is `Running` but `0/1 Ready`. Is it restarted? Does it receive traffic? What do you check first?
3. You edit a ConfigMap consumed through `envFrom`. Do running Pods see the change? What do you do?
4. Why is a database dependency check wrong in a liveness probe but right in a readiness probe?
5. What is the difference between a CPU limit being exceeded and a memory limit being exceeded?

**Definition of done for this level.** You can write a Deployment, Service, ConfigMap and Secret reference for a stateless service from memory; explain the Deployment-to-Pod ownership chain; diagnose the seven common symptoms in the table using only `get`, `describe`, `logs` and `get endpoints`; perform and reverse a rollout; and explain in one paragraph why a packaging layer exists.
