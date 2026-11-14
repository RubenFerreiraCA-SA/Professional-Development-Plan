# T-PLT-01-E — Expert Depth

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-e"></a>
#### T-PLT-01-E — Expert Depth

**Control-plane mechanics.** The API server validates, authenticates, authorises, runs admission, and persists to etcd. Watches stream changes to controllers, which operate on cached state (informers) and write status back. Everything is *eventually consistent* and level-triggered: controllers react to current state, not to events, so missed events are survivable but ordering assumptions are not. The scheduler filters nodes by constraints (resources, taints, affinity, topology) then scores the survivors. The kubelet reports node and Pod status and enforces limits through the container runtime and cgroups.

**Understanding rollouts precisely.** A Deployment creates a new ReplicaSet and scales it up while scaling the old one down within `maxSurge` and `maxUnavailable`. Progress depends on readiness; a failing readiness probe stalls the rollout safely, with old Pods still serving — whereas a probe that passes for a broken application ships the defect. `progressDeadlineSeconds` marks a stalled rollout failed but does not roll back automatically. Revision history and annotations aid audit; GitOps turns rollback into a revert of desired state.

**Failure modes and their signatures**

| Symptom | Likely cause | Where to look |
| --- | --- | --- |
| `Pending` | Insufficient resources, taints, unbound volume, unschedulable constraints | `describe pod` events |
| `ImagePullBackOff` | Wrong digest, registry auth, network | Events; pull credentials |
| `CrashLoopBackOff` | Application crash, bad config, aggressive liveness | Logs (current and `--previous`) |
| `OOMKilled` | Memory limit too low or leak | `describe` last state; memory history |
| `0/1 Ready`, no restarts | Readiness failing | Probe path and port; dependency |
| Service with no endpoints | Selector mismatch or Pods not ready | `get endpointslices` |
| Intermittent 502 during rollout | Missing `preStop` drain or readiness delay | Timing of termination versus endpoint removal |
| Eviction | Node pressure | Node conditions; QoS class |

**Scheduling at scale.** Topology spread across zones, anti-affinity for critical replicas, taints and tolerations to dedicate nodes, priority classes and preemption to protect important workloads, and the interaction of quotas, requests and autoscaling. Remember that cluster autoscaling adds nodes after Pods are Pending, which takes minutes; headroom or over-provisioning Pods smooth bursts.

**Cluster design choices.** Managed versus self-managed control planes; node pools by workload type; single large cluster versus many small clusters (blast radius and tenancy versus operational overhead); regional versus zonal clusters; upgrade strategy; and which add-ons are platform-owned. There is no best answer — record the decision, its alternatives and revisit conditions.

**API evolution.** Kubernetes versions deprecate and remove APIs. Treat manifest API versions as dependencies; scan for deprecated usage before upgrades; and test controllers and custom resources against the target version.

**A narrated `kubectl apply`, with the signature of each step.**

| # | Step | What happens | Observable evidence |
| --- | --- | --- | --- |
| 1 | Client | `kubectl` reads manifest, discovers API versions, sends the request | `kubectl apply -v=6` shows the call |
| 2 | API server | Authenticates, authorises (RBAC), runs mutating then validating admission, validates the schema | A rejection returns a specific message from the failing stage |
| 3 | etcd write | The object is persisted; a resource version is assigned | `kubectl get deploy -o yaml` shows `resourceVersion`, `generation` |
| 4 | Deployment controller | Observes the new Deployment, creates a ReplicaSet | `kubectl get rs`, event `ScalingReplicaSet` |
| 5 | ReplicaSet controller | Creates Pod objects (no node assigned yet) | Pods `Pending`, `.spec.nodeName` empty |
| 6 | Scheduler | Filters nodes (resources, taints, affinity), scores, binds the Pod to a node | Event `Scheduled`; `.spec.nodeName` set |
| 7 | Kubelet | Sees the bound Pod, pulls images, creates containers via the runtime, mounts volumes, starts probes | Events `Pulling`, `Pulled`, `Created`, `Started` |
| 8 | Readiness | Probe succeeds; endpoint controller adds the Pod to EndpointSlices | Pod `Ready`; `kubectl get endpointslices` lists the IP |
| 9 | Traffic | kube-proxy or the data plane routes Service traffic to the Pod | Requests succeed |

Key idea: components do not call each other; they watch the API server and write state. Controllers are level-triggered, reconciling current state toward desired state, which is why a restarted controller catches up on its own.

**Predicting the signature of four faults.**

| Fault | Status | Event and field signature | Metric signature | First command |
| --- | --- | --- | --- | --- |
| Taint with no matching toleration | `Pending` | `0/3 nodes are available: 3 node(s) had untolerated taint {dedicated: gpu}` | Pending Pods count rises; scheduler failures | `kubectl describe pod` |
| Bad image digest | `ErrImagePull` → `ImagePullBackOff` | `Failed to pull image … not found`; backoff grows | Container waiting reason `ImagePullBackOff` | `kubectl describe pod`; check registry and credentials |
| Liveness probe too strict | `CrashLoopBackOff`; restarts climb | `Liveness probe failed: HTTP probe failed with statuscode: 503`; `Killing` | Restart count; container uptime resets | `kubectl logs --previous`; probe config |
| Node `NotReady` | Node `NotReady`; Pods `Unknown`/evicted after the toleration timeout (default 300 s) | Node conditions `Ready=False/Unknown`; `NodeNotReady` events | `kube_node_status_condition`; Pod rescheduling | `kubectl describe node`; kubelet logs |

**Rolling-update arithmetic.** With `replicas: 4`, `maxSurge: 25%` (1 Pod) and `maxUnavailable: 25%` (1 Pod), Kubernetes may run up to 5 Pods and must keep at least 3 Ready. It starts a new Pod, waits for readiness, then removes an old one. If readiness never succeeds, the rollout stalls at 4 old + 1 new, still serving, and after `progressDeadlineSeconds` the Deployment reports `ProgressDeadlineExceeded` without rolling back. Set `maxUnavailable: 0` for capacity-critical services, and add a `preStop` sleep plus `terminationGracePeriodSeconds` so a terminating Pod is removed from endpoints before it stops accepting connections; otherwise you see brief 502s during rollouts.

**Why a readiness probe that checks the shared database can worsen an outage.** If the database slows, every Pod fails readiness simultaneously, all Pods leave the Service, and the service returns errors to everyone even though most requests might have succeeded from cache or without the database. When the database recovers, all Pods return together and a thundering herd arrives. Prefer a readiness check of the local ability to serve (including a bounded, cached view of dependencies), degrade gracefully, and surface dependency health through metrics and alerts instead.

**Cluster topology: a comparison.**

| Dimension | One shared multi-tenant cluster | Cluster per environment | Cluster per team |
| --- | --- | --- | --- |
| Blast radius | Largest: a bad admission policy or control-plane problem affects all | Prod isolated from non-prod | Smallest per team |
| Cost | Lowest control-plane and idle overhead | Moderate | Highest; duplicated add-ons |
| Upgrade effort | One upgrade, high stakes | A few, can canary in non-prod | Many; needs automation |
| Policy complexity | High: strict tenancy (namespaces, quotas, network policy, admission) | Moderate | Lower per cluster, many clusters to keep aligned |
| Best fit | Small to mid organisations with a strong platform team | Most common default | Strong isolation or regulatory needs, mature fleet tooling |

A reasonable default with stated assumptions: cluster per environment, namespaces per team, with production on its own regional cluster. Revisit when team count, compliance needs or upgrade pain changes.

**What each scheduling control does when a zone is lost.**

| Control | Behaviour in a zone loss | What a training cluster cannot show |
| --- | --- | --- |
| Resource requests | Replacement Pods need free capacity in surviving zones | Real capacity headroom; autoscaler lag (minutes) |
| Topology spread (`maxSkew: 1` across zones) | Keeps replicas balanced beforehand; after the loss, Pods may be Pending if `whenUnsatisfiable: DoNotSchedule` | Multiple real zones |
| Taints and tolerations | Dedicated pools may lack capacity in other zones | Real node pool failures |
| PodDisruptionBudget | Limits voluntary disruption (drains); does not stop involuntary loss | Real node failure behaviour |

To claim zone-failure tolerance, demonstrate it: spread across zones configuration plus evidence from a drill or fault-injection run showing the service staying within its SLO with one zone's nodes cordoned and drained or removed, with capacity enough for the remaining zones.

**API deprecation hygiene.** Before each upgrade, scan manifests and live objects for removed APIs (for example with `kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis`, or a tool such as `pluto`), fix them one minor version ahead of removal, and run controllers and CRDs against the target version in a staging cluster first.

**Mentoring prompts.** Walk through everything that happens, in order, between `kubectl apply` of a Deployment and a request being served by the new Pod. Why can a readiness probe that checks a shared database make an outage worse? What would you need to prove to claim zone-failure tolerance for a workload?

---
