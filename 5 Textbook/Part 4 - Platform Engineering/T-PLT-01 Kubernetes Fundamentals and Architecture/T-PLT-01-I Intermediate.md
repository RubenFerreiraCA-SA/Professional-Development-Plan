# T-PLT-01-I — Intermediate Practice

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-i"></a>
#### T-PLT-01-I — Intermediate Practice

## Why this matters

At the Beginner level you learned the vocabulary and watched a Deployment replace a Pod. Intermediate practice is about **predicting** what the cluster will do and **explaining** it when it does something else. Why is this Pod `Pending` and that one not? Why did a Service stop sending traffic to a Pod that is still `Running`? Why was a container killed even though the node had spare memory? Each of those has a mechanical answer in the scheduler, a controller, the network model or the kernel's resource accounting, and each leaves evidence you can read.

This section assumes the Beginner material (spec and status, Deployments, Services, labels, `kubectl get/describe/logs`) and a working `kind` cluster with one control-plane node and two workers. Examples use the neutral `orders-api` service; registry names are placeholders. The aim is a habit: **form a hypothesis from how the component works, then confirm it with one command.**

## Declarative manifests

Write YAML and apply it, rather than running imperative commands. Files can be reviewed, diffed and stored in Git.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  labels: { app: orders-api }
spec:
  replicas: 2
  selector:
    matchLabels: { app: orders-api }
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }
  template:
    metadata:
      labels: { app: orders-api }
    spec:
      serviceAccountName: orders-api
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: api
          image: registry.example.com/orders-api@sha256:3f1c...e9a0
          ports: [{ containerPort: 8000 }]
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          resources:
            requests: { cpu: 100m, memory: 128Mi }
            limits:   { memory: 256Mi }
          startupProbe:   { httpGet: { path: /health, port: 8000 }, failureThreshold: 30, periodSeconds: 2 }
          readinessProbe: { httpGet: { path: /ready,  port: 8000 }, periodSeconds: 5 }
          livenessProbe:  { httpGet: { path: /health, port: 8000 }, periodSeconds: 10 }
---
apiVersion: v1
kind: Service
metadata: { name: orders-api }
spec:
  selector: { app: orders-api }
  ports: [{ port: 80, targetPort: 8000 }]
```

```bash
kubectl diff -f deploy.yaml            # what would change, before it changes
kubectl apply -f deploy.yaml
kubectl rollout status deployment/orders-api
kubectl describe deployment orders-api
kubectl rollout history deployment/orders-api
kubectl rollout undo deployment/orders-api
kubectl get events --sort-by=.lastTimestamp
```

`kubectl apply` compares your file with the last applied configuration and the live object, then sends only the difference. `kubectl diff` previews that. Fields that other actors set (for example a replica count managed by an autoscaler) can conflict with the file; decide which party owns each field and do not let two owners fight.

## Scheduling: how a Pod gets a node

The scheduler handles every Pod with an empty `spec.nodeName`. For each one it runs two phases.

| Phase | Question | Examples of what it uses |
| --- | --- | --- |
| **Filter** | Which nodes are *possible*? | Enough unreserved CPU and memory for the Pod's **requests**; matching `nodeSelector` or required node affinity; tolerated taints; free ports and attachable volumes; topology rules marked required |
| **Score** | Which possible node is *best*? | Spreading, balanced resource use, preferred affinity, image already present |

If no node survives filtering, the Pod stays `Pending`, and the scheduler records *why per node* in an event:

```text
0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
2 Insufficient memory.
```

Read that line as a sum over nodes: the control-plane node was excluded by a taint, both workers lacked memory. The scheduler decides from **requests**, not from live usage; a node can be nearly idle and still be "full" because its Pods *reserved* the capacity.

| Control | What it does | Typical use | Trap |
| --- | --- | --- | --- |
| `nodeSelector` | Only nodes carrying a label | Pin to a hardware pool | A typo leaves the Pod `Pending` forever |
| Node affinity | Required or preferred node label rules | Zone or hardware preference | `preferred` is only a hint |
| Pod anti-affinity | Avoid nodes already running matching Pods | Keep replicas apart | `required` with more replicas than nodes leaves Pods `Pending` |
| Taints and tolerations | Nodes repel Pods unless they tolerate the taint | Dedicated pools, control-plane isolation | A toleration allows placement but does not require it |
| Topology spread | Keep replicas balanced across zones or nodes | Resilience across failure domains | `whenUnsatisfiable: DoNotSchedule` can strand Pods |
| Priority classes | Higher-priority Pods may evict lower ones | Protect critical workloads | Preemption surprises the evicted team |

A spread constraint for `orders-api`:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels: { app: orders-api }
```

Taints are applied to nodes, tolerations to Pods:

```bash
kubectl taint nodes practice-worker dedicated=batch:NoSchedule
kubectl describe node practice-worker | grep -i taint
kubectl taint nodes practice-worker dedicated=batch:NoSchedule-   # trailing dash removes it
```

Scheduling is a **one-time decision**: once a Pod is bound to a node, the scheduler does not move it when things change. Rebalancing needs a deliberate eviction or a separate tool.

## Controllers: who owns what

A controller is a loop: read desired state, read observed state, act on the difference. Your Deployment involves a chain of them, and the chain is visible through **owner references**.

```text
Deployment orders-api
   └─ owns ReplicaSet orders-api-7d9c5f      (one per revision of the Pod template)
         └─ owns Pod orders-api-7d9c5f-abcde
```

```bash
kubectl get pod <pod> -o jsonpath='{.metadata.ownerReferences[*].kind}{"\n"}'
kubectl get rs -l app=orders-api
kubectl describe rs <replicaset>
```

Ownership has three consequences you will meet in practice:

1. **Garbage collection.** Delete a Deployment and its ReplicaSets and Pods are deleted with it, because the owner is gone.
2. **Hand edits are overwritten.** Edit a Pod owned by a ReplicaSet and the change vanishes at the next replacement. Change the *owner's template*.
3. **Orphans and adoption.** A ReplicaSet adopts any Pod whose labels match its selector and which has no controller. Reuse of labels across workloads can make controllers fight over Pods; give each workload a unique label set.

**What a rollout does.** Changing anything in the Pod template (image, environment, probes) changes the template hash and creates a *new* ReplicaSet. Changing `replicas` does not. The Deployment controller then scales the new ReplicaSet up and the old one down in steps bounded by `maxSurge` (extra Pods allowed above `replicas`) and `maxUnavailable` (Pods allowed below). With `replicas: 2`, `maxSurge: 1`, `maxUnavailable: 0`, it starts one new Pod, waits for it to be ready, removes one old Pod, and repeats. Readiness gates progress, which is why a probe that never succeeds stalls the rollout *safely*, with the old Pods still serving.

**Level-triggered, not event-triggered.** Controllers compare current state with desired state whenever they run; they do not depend on having seen every event. If a controller restarts, it reads the world and carries on. This is why you can reason about Kubernetes by asking "what is the difference now?" rather than "what happened?".

| Workload controller | Maintains | Reach for it when |
| --- | --- | --- |
| Deployment | Interchangeable Pods with rolling updates | Stateless services |
| StatefulSet | Pods with stable names and per-Pod storage | Systems needing identity (see the Professional level) |
| DaemonSet | One Pod per matching node | Node agents |
| Job, CronJob | Pods that run to completion | Batch work, scheduled tasks |

**Rollout arithmetic, worked.** Take `replicas: 4`, `maxSurge: 1`, `maxUnavailable: 1`. Kubernetes may run up to five Pods and must keep at least three Ready. It can therefore start one new Pod and terminate one old Pod at the same time. With `maxUnavailable: 0` it must wait for the new Pod to be Ready before removing any old one, which preserves capacity but needs room for the surge Pod. If the cluster has no spare capacity, the surge Pod is `Pending` and the rollout stalls; the failure is in the *scheduler's* arithmetic, not the application.

```bash
kubectl set image deployment/orders-api api=registry.example.com/orders-api@sha256:<new-digest>
kubectl rollout status deployment/orders-api --timeout=120s
kubectl get rs -l app=orders-api -o wide      # old and new ReplicaSets, with counts
kubectl rollout history deployment/orders-api --revision=2
```

**A Pending Pod, traced end to end.** Suppose one new Pod stays `Pending` during a rollout. (1) `kubectl describe pod` shows `FailedScheduling: 0/3 nodes are available: 2 Insufficient memory, 1 node(s) had untolerated taint`. (2) `kubectl describe node` on a worker shows `Allocated resources` with memory requests at 95% of allocatable, even though `kubectl top node` shows 40% used. (3) The cause is reservation, not usage: other Pods *requested* more memory than they use. (4) The choices are to lower over-generous requests (from measurement), add a node, or accept a smaller surge. Each step used one command and eliminated one hypothesis.

## Networking and service discovery

The Kubernetes network model makes three promises, implemented by the network plugin (CNI):

- Every Pod gets its own IP address.
- Any Pod can reach any other Pod's IP without translation, across nodes.
- Agents on a node (such as the kubelet) can reach the Pods on that node.

Whether Pods are *allowed* to talk is a separate policy question (a later chapter); by default, they are.

**Services and DNS.** Every Pod has its own IP; Pod IPs are ephemeral; a Service gives a stable virtual address and DNS name (`orders-api.<namespace>.svc.cluster.local`) that load-balances across *ready* endpoints.

| Service type | Reachable from | Typical use |
| --- | --- | --- |
| `ClusterIP` | Inside the cluster | Default internal APIs |
| `NodePort` | Node address and port | Debugging, building block |
| `LoadBalancer` | A cloud load balancer | External exposure (needs a cloud controller) |
| `ExternalName` | DNS alias | Point at an external host |
| Headless (`clusterIP: None`) | DNS returns Pod addresses | StatefulSets, client-side discovery |

**How a Service knows its Pods.** The control plane watches Pods matching the Service's selector and records the *ready* ones as **EndpointSlices**. A node-level component (kube-proxy or the network plugin's data plane) turns those slices into forwarding rules. A Pod that fails readiness is removed from the slice, which is how readiness controls traffic.

```bash
kubectl get endpointslices -l kubernetes.io/service-name=orders-api
kubectl get endpoints orders-api
kubectl run -it --rm dns-test --image=busybox:1.36 --restart=Never -- nslookup orders-api
```

**DNS names.** Inside a namespace, the short name `orders-api` resolves. From another namespace use `orders-api.<namespace>` or the full `orders-api.<namespace>.svc.cluster.local`. The Pod's resolver is configured with search domains and `ndots`, so short names are expanded in order, which also means a lookup of an external name can trigger several failed queries first; that matters when DNS is slow.

`kubectl port-forward` tunnels through the API server to one Pod; it bypasses the Service's load balancing and readiness behaviour, so a success there does not prove the Service works.

**A discovery fault ladder.** When a caller cannot reach `orders-api`, test one rung at a time:

| Rung | Test | If it fails |
| --- | --- | --- |
| Name resolves | `nslookup orders-api` from a Pod in the same namespace | DNS add-on unhealthy, or wrong namespace in the name |
| Service has endpoints | `kubectl get endpointslices` | Selector mismatch, or Pods not ready |
| Pod answers directly | `curl <pod-ip>:8000/health` from a debug Pod | Application, port or probe problem |
| Service port maps correctly | `curl orders-api:80/health` | `targetPort` does not match the container port |
| Policy allows it | Compare with a Pod in an unrestricted namespace | A network policy or mesh rule |

**Exposing outside the cluster.** An Ingress or Gateway routes external HTTP(S) to Services; it needs a controller installed. For a practice cluster, `port-forward` is enough.

## Probes: three questions

| Probe | Question | Failure action |
| --- | --- | --- |
| `startupProbe` | Has it finished starting? | Kill the container if it never succeeds; disables the other probes until success |
| `readinessProbe` | Should it receive traffic now? | Remove from Service endpoints; no restart |
| `livenessProbe` | Is it wedged beyond self-recovery? | Restart the container |

The classic incident: a liveness probe that checks a dependency. The database blips, every replica fails liveness and restarts, and a small outage becomes a large one. **Liveness checks the process; readiness checks whether it should serve.**

| Rule | Reason |
| --- | --- |
| Liveness is cheap and dependency-free | Avoid cascading restarts |
| Readiness may check critical dependencies — carefully | A shared dependency failure empties all endpoints |
| Use `startupProbe` instead of a huge `initialDelaySeconds` | Fast detection after start, tolerance for slow start |
| `timeoutSeconds` shorter than `periodSeconds` | Probes do not pile up |
| Avoid heavy `exec` probes | CPU cost at scale |

Break each probe deliberately, observe `kubectl get pods` and `describe` events for each failure, then restore.

## Resources: requests, limits and quality of service

| Setting | Used by | Effect |
| --- | --- | --- |
| `requests` | Scheduler, autoscaler, quotas | Capacity reserved for placement |
| `limits.memory` | Kernel control group | Exceeded: container is OOM-killed |
| `limits.cpu` | Kernel CPU quota | Exceeded: throttled (slow, not killed) |

CPU is **compressible** (the kernel can slow you down); memory is **not** (the kernel can only kill). That asymmetry shapes policy: a memory limit produces a visible failure, a CPU limit produces invisible slowness.

Quality-of-service classes follow from requests and limits: `Guaranteed` (every container has requests equal to limits), `Burstable` (some request set), `BestEffort` (none). Under node memory pressure, the kubelet evicts `BestEffort` first, then `Burstable` Pods using more than they requested, and `Guaranteed` last.

```bash
kubectl top nodes
kubectl top pods
kubectl describe node <node> | sed -n '/Allocated resources/,/Events/p'
kubectl get pod <pod> -o jsonpath='{.status.qosClass}{"\n"}'
```

`kubectl top` needs the metrics add-on. Measure usage before setting requests; too low causes overcommit and noisy neighbours, too high wastes capacity. Cause an OOM kill on purpose and read `Last State: OOMKilled` and `Exit Code: 137` in `describe`.

**Namespace guardrails.** A `ResourceQuota` caps the total requests, limits or object counts in a namespace; a `LimitRange` sets defaults and bounds per container.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: team-orders, namespace: orders }
spec:
  hard: { requests.cpu: "4", requests.memory: 8Gi, limits.memory: 16Gi, pods: "30" }
---
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: orders }
spec:
  limits:
    - type: Container
      defaultRequest: { cpu: 100m, memory: 128Mi }
      default: { memory: 256Mi }
```

With a quota on requests, a Pod without requests is rejected unless a `LimitRange` supplies defaults. Quota failures appear as errors at creation (`exceeded quota`), not as `Pending` Pods.

## Namespaces in practice

Namespaces are where names, quotas and access rules attach. Keep a habit of setting the context's default namespace so commands cannot silently hit the wrong one.

```bash
kubectl config get-contexts
kubectl config set-context --current --namespace=orders
kubectl get pods -A                          # all namespaces
kubectl auth can-i create deployments -n orders
```

Cross-namespace calls use the DNS form above. A namespace does not isolate the *network* or the *nodes*: Pods from different namespaces can reach each other and share node capacity until you add network policy, quotas and scheduling rules.

## Configuration and secrets

| Mechanism | Use for | Notes |
| --- | --- | --- |
| Environment literal | Tiny non-sensitive switches | Visible in `describe` |
| ConfigMap | Non-sensitive config | Env changes need a restart; mounted files update eventually |
| Secret | Credentials | Base64-encoded, not encrypted by default |
| Image build | Code and static assets only | Never environment-specific config or secrets |

A change to a ConfigMap does not restart Pods by itself; use a hash annotation or a tool that triggers a rollout.

```yaml
# Pod template fragment: the annotation changes whenever the rendered config changes,
# which changes the template hash and therefore triggers a rolling update.
metadata:
  annotations:
    checksum/config: "<hash of the rendered ConfigMap>"
spec:
  containers:
    - name: api
      envFrom:
        - configMapRef: { name: orders-api-config }
      volumeMounts:
        - { name: tls, mountPath: /etc/orders/tls, readOnly: true }
  volumes:
    - name: tls
      secret: { secretName: orders-api-tls }
```

Variables taken from a ConfigMap are read at container start, so an updated value is invisible to a running container until it restarts; files mounted from a ConfigMap or Secret are refreshed in place after a delay, but only if the application re-reads them. Reading a Secret with `kubectl get secret -o yaml` returns base64, which is encoding rather than protection.

## A practice cluster that can fail on purpose

A single-node cluster hides most scheduling behaviour. Use a control plane and two workers, then rehearse node-level events:

```bash
kubectl get nodes
kubectl label node practice-worker tier=general
kubectl cordon practice-worker2                         # no new Pods; existing keep running
kubectl rollout restart deployment/orders-api           # new Pods avoid the cordoned node
kubectl drain practice-worker2 --ignore-daemonsets --delete-emptydir-data
kubectl uncordon practice-worker2
```

`cordon` marks a node unschedulable; `drain` additionally evicts its Pods (respecting disruption budgets) so they are recreated elsewhere. To see involuntary failure, stop a worker's container (`docker stop practice-worker2`) and watch `kubectl get nodes -w`: the node turns `NotReady` after about 40 seconds, but its Pods are only evicted after the default five-minute toleration, so a Pod can look `Running` on a dead node for minutes. A practice cluster teaches these timings qualitatively; do not quote them as production numbers.

## Diagnostics: from symptom to cause

Work from the outside in, and let each answer choose the next command.

| Symptom | Likely causes | First evidence | Next step |
| --- | --- | --- | --- |
| `Pending`, no events about scheduling | Scheduler not running, or Pod has an unschedulable `schedulerName` | `kubectl -n kube-system get pods` | Fix the scheduler or the name |
| `Pending` with `Insufficient cpu/memory` | Requests exceed free capacity | Event line per node | Lower requests, add nodes, or remove other Pods |
| `Pending` with `untolerated taint` | Node taint with no toleration | `describe node` taints | Add toleration or remove taint |
| `Pending` with unbound PersistentVolumeClaim | No matching volume or storage class | `kubectl get pvc` | Fix the claim or storage class |
| `ImagePullBackOff` | Wrong name, missing credentials, network | Event text | Correct image or pull secret |
| `CrashLoopBackOff` | Application error, bad config, aggressive liveness | `logs --previous`, `describe` exit code | Fix cause; relax liveness |
| `OOMKilled` | Memory limit below real use | `describe` Last State | Raise limit; investigate leak |
| `Running`, `0/1` Ready | Readiness failing | `describe` probe events | Fix path, port, dependency |
| Service has no endpoints | Selector mismatch or no ready Pods | `get endpointslices` | Fix labels or readiness |
| Rollout stuck | New Pods never ready, or quota exhausted | `rollout status`, `describe rs` | Fix Pods, then `rollout undo` if needed |
| Intermittent 502 during rollout | Termination races endpoint removal | Timing of deletes against errors | Drain window (Professional level) |

**An investigation template.** Write three lines before you change anything: *Observed* (the exact status and event), *Hypothesis* (the component and mechanism you suspect), *Test* (the one command that would refute it). Changing things before you can state the hypothesis turns diagnosis into guessing.

## What can go wrong: common mistakes

| Mistake | Consequence | Better practice |
| --- | --- | --- |
| No requests set | `BestEffort` Pods, poor placement, first to be evicted | Set requests from measurement |
| Memory limit equal to typical use | OOM kills on every spike | Headroom above observed peak |
| Same label set on unrelated workloads | Controllers adopt each other's Pods; Services mix backends | Unique `app` plus component labels |
| `kubectl edit` on live objects | Drift from Git; lost at next apply | Change the file, review, apply |
| Treating `Running` as healthy | Broken app receives traffic | Real readiness probe |
| Reading only the current logs of a crash-looping Pod | The error is in the previous container | Use `--previous` |
| Draining without a disruption budget | All replicas can leave together | Define a PodDisruptionBudget (Professional level) |

## Knowledge consolidation

- The scheduler **filters on requests and constraints, then scores**; it never looks at live usage and never moves a Pod after binding.
- A `Pending` event line is a **per-node sum of reasons**; read it literally.
- Controllers form an **ownership chain**; edit the owner, not the child, and keep label sets unique.
- A rollout is a **new ReplicaSet** scaled up and down within `maxSurge` and `maxUnavailable`, gated by readiness.
- Services route to **ready EndpointSlice members**; DNS, endpoints, Pod and policy are four separate rungs to test.
- **Liveness checks the process, readiness checks whether it should serve.**
- **CPU throttles, memory kills.** Requests drive placement; limits drive enforcement.
- Quotas fail at **creation time**; capacity shortages fail as `Pending`.
- State a hypothesis and a refuting test before changing anything.

## Exercises

**Exercise 1 — Predict the schedule.** In the three-node `kind` cluster, label one worker `tier=general` and deploy `orders-api` with `nodeSelector: {tier: general}`. Then change the label value in the selector to `genral`. Predict, then confirm, the Pod status and the exact event wording.

**Exercise 2 — Taint and tolerate.** Taint one worker with `dedicated=batch:NoSchedule`. Scale `orders-api` to six replicas and record where the Pods land. Add a toleration and observe whether Pods are *required* to land on the tainted node.

**Exercise 3 — Ownership.** For one running Pod, follow `ownerReferences` up to the Deployment. Delete the Deployment with `--cascade=orphan`, observe what remains, then create a ReplicaSet with a matching selector and watch it adopt the Pods.

**Exercise 4 — Break each probe.** Deploy the manifest. Break readiness (wrong path), then liveness (an endpoint that returns 500), then startup (a very short `failureThreshold`), one at a time. Record the effect on endpoints and restarts for each.

**Exercise 5 — Resources.** Set a memory limit of `64Mi` on a process that allocates more, and read `OOMKilled` and the exit code. Then set a CPU limit that throttles a busy loop, and compare its throughput with and without the limit.

**Exercise 6 — Walk the ladder.** Deliberately break discovery three ways (selector typo, wrong `targetPort`, readiness failing). For each, list which rung of the fault ladder first fails.

**Solution notes.**

*Exercise 1.* The first deployment places Pods on the labelled worker. With the typo, Pods stay `Pending` with an event like `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`. The scheduler cannot tell a typo from a deliberate rule; it reports the mismatch.

*Exercise 2.* Without a toleration no Pods land on the tainted worker; with six replicas the other worker (and possibly the control plane, if untainted in your setup) carries them. A toleration only *permits* placement; to force it you need node affinity or a selector as well.

*Exercise 3.* The chain is Pod → ReplicaSet → Deployment. With `--cascade=orphan`, the ReplicaSet and Pods remain without an owner. A new ReplicaSet whose selector matches adopts the orphaned Pods. This is why label discipline matters.

*Exercise 4.* Readiness failure: Pods `Running` but `0/1`, endpoints empty, no restarts, rollout stalls. Liveness failure: restart count climbs and `Killing` events appear. Startup failure with too-low `failureThreshold`: restarts before the application is up, even though the app is fine. Exact counts vary.

*Exercise 5.* `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`. The CPU-limited loop runs visibly slower while the container stays healthy. Record throughput numbers from your own runs.

*Exercise 6.* Selector typo: rung 2 (no endpoints). Wrong `targetPort`: rung 4 (the Pod answers directly but not through the Service). Readiness failing: rung 2 (endpoints exist only for ready Pods, so none).

## Mentoring prompts

Why can a node with 5% CPU usage refuse a new Pod? What is the difference in operator experience between a CPU limit that is too low and a memory limit that is too low? A Service has endpoints but clients still fail: which rungs remain? Explain why editing a Pod by hand is both ineffective and a symptom of a process problem.

---
