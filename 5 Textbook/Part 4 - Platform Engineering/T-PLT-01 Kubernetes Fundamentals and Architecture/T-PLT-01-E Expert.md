# T-PLT-01-E — Expert Depth

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-e"></a>
#### T-PLT-01-E — Expert Depth

## Why this level exists

At the Professional level you can build a cluster with stated failure domains, planned headroom and enforced boundaries. The Expert level asks a harder question: **what does Kubernetes actually guarantee, and where does behaviour stop being predictable from the documentation?** The answers live in the control plane's consistency model, in the limits of the controller pattern, in what happens at scale, in the faults that appear only as interactions between components, and in the long-term work of upgrading something that never stops running.

An expert does not memorise more objects. An expert holds a **small number of precise mental models** — the request path, the watch-and-reconcile loop, the scheduling cycle, the version-skew rules — and uses them to predict the signature of a fault *before* looking, to design systems that do not depend on guarantees the platform does not give, and to say clearly what a platform team should and should not own. This section assumes the earlier levels. Examples use `orders-api` and placeholder names. Version-specific figures (limits, default timeouts, skew policy) are stated as they were true at the time of writing; verify them against the version you run.

## Control-plane mechanics

**The API request path.** Every write — from `kubectl`, a controller, a kubelet or a pipeline — passes the same stages in the API server, in this order:

| Stage | What it decides | Failure looks like |
| --- | --- | --- |
| Authentication | Who is calling (certificate, token, OIDC identity) | `Unauthorized` (401) |
| Authorisation | Whether that identity may perform this verb on this resource (RBAC) | `Forbidden` (403), naming the verb and resource |
| Mutating admission | Defaults and injections (sidecars, labels, default resources); webhooks may run here | Object arrives changed; webhook timeout errors |
| Schema validation | Whether the object is well-formed for its version | `Invalid` (422), naming the field |
| Validating admission | Policy checks (quota, Pod security, custom policy) | `Forbidden` or `admission webhook ... denied the request` |
| Persistence | Writing to etcd, assigning `resourceVersion` | Conflict (409) or timeouts under etcd pressure |

Knowing the order lets you read a rejection: a 403 means the call never reached admission; a denial from a named webhook means authentication, authorisation and schema all passed.

**Optimistic concurrency.** Every object carries a `resourceVersion`. An update must name the version it read; if the object changed since, the write fails with a conflict and the writer must re-read and retry. Controllers and clients are written around this. It is why two controllers editing the same field produce a stream of conflicts rather than silent corruption — and why *which party owns which field* is a design question.

**Watches and informers.** Clients do not poll. They open a **watch** against the API server for a resource type and receive a stream of changes since a given `resourceVersion`. Client libraries wrap this in an **informer**: a local cache kept in step by the watch, plus a work queue of keys that need attention. Controllers read from the *cache*, not from the API server, which makes them cheap and also means they may act on slightly stale state. The API server itself serves most reads and watches from a cache in front of etcd, so list and watch load is mostly a memory and CPU matter on API server instances rather than an etcd matter, until a client forces a consistent read or a large uncached list.

**etcd.** The only durable store. It uses the Raft consensus protocol: a write commits when a majority of members have persisted it, so write latency is bounded below by the **disk sync latency of a quorum member** and the network round trip between them. Slow disks cause leader elections, API timeouts and, in the worst case, a cluster that appears to "freeze". Keep etcd on fast local storage with its own alerts for fsync duration and leader changes. Object size and count matter: a default storage quota (about 2 GiB unless raised) stops writes when exceeded, so large configurations, unbounded events or runaway custom resources can bring a cluster to a read-only state.

**Server-side apply and field ownership.** With server-side apply, the API server records which *manager* owns each field. If two managers set the same field to different values, the second gets a conflict unless it forces ownership. This is the mechanism that lets an autoscaler own `spec.replicas` while Git owns the rest of a Deployment, provided the Git side does not also set `replicas`. Inspect ownership with `kubectl get deploy orders-api -o yaml --show-managed-fields`.

**The kubelet's view.** The kubelet watches Pods assigned to its node, converges the runtime to match, reports `status`, and renews a **lease** that the node lifecycle controller uses to decide a node is alive. Resource limits are enforced through the container runtime and cgroups; eviction under pressure is the kubelet's own decision, not the scheduler's.

**Everything is eventually consistent and level-triggered.** Controllers react to current state, not to events, so missed events are survivable but *ordering assumptions are not*. The scheduler filters nodes by constraints (resources, taints, affinity, topology) then scores the survivors.

## A narrated `kubectl apply`, with the signature of each step

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

```bash
kubectl apply -f deploy.yaml -v=6 2>&1 | head -20
kubectl get deploy orders-api -o jsonpath='{.metadata.generation}{" "}{.status.observedGeneration}{"\n"}'
kubectl get events --field-selector involvedObject.name=orders-api --sort-by=.lastTimestamp
```

`generation` increments when the spec changes; `observedGeneration` is the last one the controller processed. A gap between them means the controller has not yet reacted, which is the cleanest test for "is this a controller delay or a real failure?".

## Controller limits

The controller pattern is powerful and has precise limits. Experts design around them.

**1. Eventual consistency has a latency, and it compounds.** Each stage in the chain from step 3 to step 9 above adds a watch delay, a queue delay and sometimes a deliberate backoff. Under load, with thousands of objects, the chain can take seconds to minutes. Anything that assumes "Deployment updated, therefore endpoints updated" is racing the chain. The termination race — a Pod receives `SIGTERM` while some clients still hold its address — is the same limit seen from the other side.

**2. Controllers act on cached, possibly stale state.** A controller may decide using a cache that has not yet seen its own previous write, and then write a conflicting update. Well-written controllers use *expectations* or version checks to avoid acting twice; poorly written custom ones create duplicates. A reconcile loop must be **idempotent**: running it twice must be safe.

**3. Level-triggering means reconcile on state, so it must be convergent.** If the desired state cannot be reached (an image that never pulls, a Pod that can never be scheduled), the controller retries indefinitely with backoff. Nothing "gives up and reports"; failure appears as *state that stays unconverged*. That is why `ProgressDeadlineExceeded` is a *condition*, not an automatic rollback.

**4. Two controllers writing one field fight.** A Deployment manifest in Git that sets `replicas: 3` and a Horizontal Pod Autoscaler that sets 8 will take turns overwriting each other. The symptom is replica counts oscillating on every sync. The fix is ownership: omit `replicas` from the manifest when an autoscaler owns it.

**5. Finalizers can block deletion.** A finalizer is a key in `metadata.finalizers` that tells the API server "do not remove this object until I have cleaned up". If the controller responsible is gone (uninstalled operator, broken webhook), the object sits in `Terminating` forever. A namespace stuck `Terminating` almost always has a resource inside it with an orphaned finalizer.

```bash
kubectl get ns stuck -o jsonpath='{.status.conditions}'
kubectl api-resources --verbs=list --namespaced -o name | xargs -n1 kubectl get -n stuck --ignore-not-found --show-kind
kubectl get <kind> <name> -n stuck -o jsonpath='{.metadata.finalizers}'
```

Removing a finalizer by hand is a last resort: you skip the cleanup the finalizer existed to do (a cloud volume, a load balancer) and may leak the resource.

**6. Garbage collection follows owner references, not intent.** Delete a parent with `--cascade=orphan` and children persist; give a child the wrong owner and it is deleted when that owner is. Cross-namespace owners are not allowed.

**7. A restart is a thundering herd.** When a controller or API server restarts, every informer relists. With many controllers and large clusters this produces a burst of list traffic. API priority and fairness shapes it; clients that ignore backoff worsen it.

**8. Leader election hides split-brain risk behind a lease.** Active/standby controllers rely on a lease object with a duration. A paused or partitioned leader can briefly believe it still leads. Controllers acting on external systems (cloud APIs) must tolerate being run twice for a short window.

**9. Custom controllers inherit all of this.** An operator is a controller you wrote or installed; its reconcile loop, its backoff and its RBAC are now part of your reliability surface. Treat operator upgrades like control-plane upgrades: they change how objects are interpreted.

| Limit | What you may not assume | Design response |
| --- | --- | --- |
| Eventual consistency | "Applied" means "effective" | Check `observedGeneration`, readiness and endpoints; use `rollout status` |
| Stale caches | One reconcile equals one effect | Idempotent reconcile; version checks |
| Unbounded retry | Failure will be reported | Alert on unconverged state and age |
| Shared fields | Two writers can coexist | Single owner per field; server-side apply managers |
| Finalizers | Delete means gone | Monitor `Terminating` age; runbook for orphans |
| Leader election | Exactly one active controller | Idempotent external effects |

## Understanding rollouts precisely

A Deployment creates a new ReplicaSet and scales it up while scaling the old one down within `maxSurge` and `maxUnavailable`. Progress depends on readiness; a failing readiness probe stalls the rollout safely, with old Pods still serving — whereas a probe that passes for a broken application ships the defect. `progressDeadlineSeconds` marks a stalled rollout failed but does not roll back automatically. Revision history and annotations aid audit; GitOps turns rollback into a revert of desired state.

**Rolling-update arithmetic.** With `replicas: 4`, `maxSurge: 25%` (1 Pod) and `maxUnavailable: 25%` (1 Pod), Kubernetes may run up to 5 Pods and must keep at least 3 Ready. It starts a new Pod, waits for readiness, then removes an old one. If readiness never succeeds, the rollout stalls at 4 old + 1 new, still serving, and after `progressDeadlineSeconds` the Deployment reports `ProgressDeadlineExceeded` without rolling back. Set `maxUnavailable: 0` for capacity-critical services, and add a `preStop` sleep plus `terminationGracePeriodSeconds` so a terminating Pod is removed from endpoints before it stops accepting connections; otherwise you see brief 502s during rollouts. Percentages round **up** for surge and **down** for unavailable, so small replica counts behave differently from the percentage suggests: with `replicas: 2` and `maxUnavailable: 25%`, the allowed unavailable count rounds down to zero.

**Two things a rollout does not check.** It checks readiness, not correctness: a Pod that returns `200` on `/ready` while serving wrong data is "healthy". And it checks the new Pods individually, not the *aggregate effect*: a change that doubles database load passes every probe. Progressive delivery tools add metric-gated analysis for exactly this; the Deployment controller does not.

**Why a readiness probe that checks the shared database can worsen an outage.** If the database slows, every Pod fails readiness simultaneously, all Pods leave the Service, and the service returns errors to everyone even though most requests might have succeeded from cache or without the database. When the database recovers, all Pods return together and a thundering herd arrives. Prefer a readiness check of the local ability to serve (including a bounded, cached view of dependencies), degrade gracefully, and surface dependency health through metrics and alerts instead.

## Scheduling at scale

The scheduler works in a **cycle** per Pod: a *scheduling* phase (filter, then score, then pick a node) followed by an asynchronous *binding* phase that writes the assignment. Plugins implement each step, so behaviour is configurable and extensible.

Points that matter at scale:

- In very large clusters the scheduler does not score every feasible node; it samples a percentage, trading optimality for throughput. Placement is good, not optimal.
- Requests, not usage, drive placement. Heavy over-requesting produces expensive, underused clusters; under-requesting produces dense nodes that hit eviction thresholds.
- **Topology spread** across zones, **anti-affinity** for critical replicas, **taints and tolerations** to dedicate nodes, and **priority classes with preemption** to protect important workloads all interact with quotas, requests and autoscaling. A required anti-affinity rule on a Deployment with more replicas than nodes leaves Pods `Pending` by design.
- Preemption evicts lower-priority Pods to make room. It respects grace periods but *not* PodDisruptionBudgets as a hard rule; it only tries to honour them. Teams that run important low-priority batch jobs, or high priority for everything, will discover this at the worst time.
- Binding is permanent. Nothing re-optimises later; a descheduler or deliberate drains are required to rebalance after a topology change.
- Cluster autoscaling adds nodes after Pods are `Pending`, which takes minutes; headroom or over-provisioning Pods (low-priority placeholders that are preempted by real work) smooth bursts.

## Scaling

Scaling has several independent axes, each with its own mechanism and limit.

| Axis | Mechanism | Signal it uses | Limit or lag |
| --- | --- | --- | --- |
| Pods per workload | Horizontal Pod Autoscaler | Resource utilisation relative to **requests**, or custom or external metrics | Metric scrape delay; stabilisation windows; node capacity |
| Pod size | Vertical autoscaling | Observed usage | Usually restarts Pods to apply; do not combine with HPA on the same metric |
| Nodes | Cluster autoscaler or node provisioner | `Pending` Pods that fit on a new node | Node start time (minutes); instance quotas; zone capacity |
| Event-driven workloads | Event-based scalers | Queue depth, stream lag | Depends on the scaler and metric source |

**The HPA formula.** `desiredReplicas = ceil(currentReplicas × currentMetric / targetMetric)`, with a tolerance (by default 10%) inside which nothing changes. Worked example: 4 replicas at an average of 90% CPU utilisation against a target of 60% gives `ceil(4 × 90/60) = 6`. Scale-down uses a stabilisation window (five minutes by default) to avoid flapping. Remember the denominator: utilisation is a percentage *of the request*. Requests that are too high make the HPA never fire; too low, and it fires constantly.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: orders-api }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: orders-api }
  minReplicas: 3
  maxReplicas: 12
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 60 } }
  behavior:
    scaleDown: { stabilizationWindowSeconds: 300 }
    scaleUp:   { policies: [{ type: Percent, value: 100, periodSeconds: 60 }] }
```

**What breaks first as clusters grow.** Documented large-cluster guidance (verify for your version) is on the order of 5,000 nodes, 150,000 Pods and 110 Pods per node. Well before those, practical limits are:

| Pressure | Symptom | Mitigation |
| --- | --- | --- |
| Number of Services and endpoints | Slow rule programming on nodes; propagation delay | Use a data plane that scales better than long rule chains; fewer, larger EndpointSlices |
| DNS query volume | Latency spikes, timeouts under load | Node-local DNS caching; reduce `ndots` for external lookups; fully qualified names |
| API server list and watch load | High latency for everyone | Fewer polling clients; priority and fairness; informers everywhere |
| etcd size and write rate | Slow writes, compaction pressure | Limit events, large objects, churn from CronJobs; clean up Jobs with a TTL |
| Node and Pod churn | Scheduler and controller queue depth | Reduce flapping probes; avoid mass restarts |
| Per-node limits | `Pending` for Pod count, IPs or volume attachments | Plan address ranges and attach limits |

The expert habit is to treat the control plane as a **shared service with a budget**: every controller, operator and CI tool spends from it. Name the largest spenders by user agent and set expectations for new ones.

## Multi-cluster

A second cluster is never free. Be precise about *why* you want one, because each reason implies a different design.

| Reason | Pattern | What it needs | What it does not give you |
| --- | --- | --- | --- |
| Blast-radius isolation | Cluster per environment, tier or team | Fleet tooling; consistent baseline | Application-level resilience on its own |
| Regulatory or data-residency boundaries | Cluster per jurisdiction | Policy about what runs where | Anything about traffic routing |
| Regional failure tolerance | Active-passive or active-active across regions | Global traffic management; data replication; tested failover | Free failover: the data layer decides the real recovery point |
| Upgrade safety | Blue-green clusters; canary clusters | Ability to move traffic and state between clusters | Simplicity: two fleets to manage |
| Scale beyond one control plane | Cells or shards | Routing layer that maps tenants to cells | A uniform view of the platform |

**The hard parts are not in Kubernetes.** Moving workloads between clusters is easy compared with moving *state*, *identity* and *traffic*:

- **State.** A database does not fail over because its application does. The recovery point and recovery time are properties of replication, not of the cluster. An active-active claim without an answer to "where do writes go during a partition?" is not yet a design.
- **Identity.** Service accounts and cluster certificates are local to a cluster. Cross-cluster calls need a trust story: federated workload identity, mutual TLS with a shared root, or gateways.
- **Traffic.** Failover needs health-based routing outside the clusters (DNS or a global load balancer) with realistic health checks and TTLs; client caching can keep sending traffic to a dead region for longer than the TTL says.
- **Configuration.** Drift between clusters is the dominant failure mode. A fleet needs one source of truth, rendered per cluster, with automated drift detection.
- **Discovery.** Service names are cluster-local; cross-cluster discovery needs an explicit mechanism, and a decision about whether callers should be allowed to depend on a remote cluster at all.

A useful rule: *design each cluster to be independently operable, and make cross-cluster dependencies explicit, rare and tested.* A fleet in which cluster B cannot start without cluster A is one larger cluster with a worse failure mode.

## Failure modes and their signatures

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

**Predicting the signature of four faults.**

| Fault | Status | Event and field signature | Metric signature | First command |
| --- | --- | --- | --- | --- |
| Taint with no matching toleration | `Pending` | `0/3 nodes are available: 3 node(s) had untolerated taint {dedicated: gpu}` | Pending Pods count rises; scheduler failures | `kubectl describe pod` |
| Bad image digest | `ErrImagePull` → `ImagePullBackOff` | `Failed to pull image … not found`; backoff grows | Container waiting reason `ImagePullBackOff` | `kubectl describe pod`; check registry and credentials |
| Liveness probe too strict | `CrashLoopBackOff`; restarts climb | `Liveness probe failed: HTTP probe failed with statuscode: 503`; `Killing` | Restart count; container uptime resets | `kubectl logs --previous`; probe config |
| Node `NotReady` | Node `NotReady`; Pods `Unknown`/evicted after the toleration timeout (default 300 s) | Node conditions `Ready=False/Unknown`; `NodeNotReady` events | `kube_node_status_condition`; Pod rescheduling | `kubectl describe node`; kubelet logs |

## Complex faults: a case catalogue

The faults that cost the most are rarely a single component failing. They are **interactions**. Each case below states the symptom, the misleading first theory, the mechanism and the evidence that settles it.

### Case 1 — The cluster that could not heal

*Symptom.* After a node loss, replacement Pods are never created. Everyone can read, nobody can write. *First theory:* the scheduler is broken. *Mechanism:* a fail-closed validating admission webhook ran as Pods *inside* the cluster, on the lost node. Creating its own replacement Pod required passing its own webhook. *Evidence:* API errors naming the webhook and `failurePolicy: Fail`; no scheduler events at all. *Fix and lesson:* exempt the webhook's namespace and system namespaces, run it with spread replicas, and test the failure on purpose. A policy engine is part of the control plane's availability.

### Case 2 — Timeouts at one in five DNS lookups

*Symptom.* Sporadic five-second delays calling an external API from some Pods; metrics show no resource pressure. *First theory:* the external service is slow. *Mechanism:* with the default `ndots: 5`, a lookup of `api.partner.example.com` tries several search-domain suffixes first; under load, UDP packets for parallel A and AAAA queries race through connection tracking on the node and some are dropped, causing the resolver's five-second retry. *Evidence:* packet capture or resolver metrics showing retried queries, DNS latency distribution with a spike at 5 s, and improvement with a trailing-dot FQDN. *Fix:* node-local DNS caching, lower `ndots` for the workload, fully qualified names for external hosts.

### Case 3 — Latency spikes with healthy Pods

*Symptom.* p99 latency spikes every few minutes; no errors, no restarts, CPU usage well below the limit. *Mechanism:* a CPU limit of 500m on a multi-threaded service; the kernel enforces quota per 100 ms period, so a burst that uses the whole quota in the first 30 ms leaves the process throttled for the remaining 70. Average utilisation looks low. *Evidence:* the throttled-periods and throttled-time counters for the container climbing in step with the spikes. *Fix:* raise or remove the CPU limit while keeping an accurate request; reduce concurrency to match the quota.

### Case 4 — Fifty Pods `Terminating` for an hour

*Symptom.* After a node reboot, Pods remain `Terminating`; a StatefulSet will not recreate its member. *Mechanism:* the node is unreachable, so the kubelet cannot confirm the container stopped; StatefulSet semantics forbid two Pods with the same identity, so the controller waits. This is a *safety* property, preventing two writers on one volume. *Evidence:* node `NotReady`, Pod deletion timestamp set, volume still attached. *Fix:* restore the node, or, once certain it is down and fenced, force-delete the Pod and let the volume detach. Force deletion without fencing can corrupt data.

### Case 5 — The upgrade that stalled at node three

*Symptom.* A node drain hangs; the upgrade pipeline times out. *Mechanism:* a PodDisruptionBudget with `minAvailable: 100%` on a single-replica Deployment makes eviction impossible by definition. *Evidence:* the eviction API returns "Cannot evict pod as it would violate the pod's disruption budget"; `kubectl get pdb` shows `ALLOWED DISRUPTIONS 0`. *Fix:* budgets expressed against replicas, an alert on zero allowed disruptions, and a policy that rejects single-replica production workloads with strict budgets.

### Case 6 — The slow control-plane brownout

*Symptom.* Deploys take minutes, `kubectl` is sluggish, controllers lag, but nothing is "down". *Mechanism:* a new operator lists all Pods in the cluster every ten seconds with no informer, and etcd latency rises as the API server serves uncached lists. *Evidence:* API server request metrics by user agent and verb, high latency on `LIST`, etcd request duration. *Fix:* throttle or fix the client; set priority and fairness limits for it; add a review step for operators that touch cluster-wide resources.

### Case 7 — The certificate that expired on a Sunday

*Symptom.* All `kubectl` calls fail with certificate errors; kubelets cannot reach the API. *Mechanism:* a self-managed control plane's serving certificates were issued for a year and not rotated. *Evidence:* certificate expiry dates on the control-plane nodes. *Fix:* automate rotation, alert at thirty days, and know the manual recovery path *before* it is needed.

## Platform boundaries

Kubernetes is a **platform for building platforms**: it provides an API machinery, a scheduler and a model of workloads, and leaves product decisions to you. Expert design is deciding which of those capabilities to expose raw, which to wrap and which to withhold.

| Question | Options | Consideration |
| --- | --- | --- |
| What API do tenants see? | Raw Kubernetes objects, a curated subset, or a higher-level abstraction | Raw maximises flexibility and support burden; abstractions give consistency and a ceiling |
| How strong is tenancy? | Soft (namespaces, quotas, policy) or hard (separate clusters, sandboxed runtimes, dedicated nodes) | Soft tenancy shares a kernel and a control plane; trust the tenants accordingly |
| What can tenants extend? | CRDs, operators, admission webhooks, cluster-scoped objects | Each extension runs with privilege or alters shared behaviour; require review |
| What is the blast radius of one team's mistake? | Quotas on objects as well as resources; policy on cluster-scoped kinds | A tenant creating 100,000 ConfigMaps is an etcd incident |
| How do tenants escape the defaults? | A documented exemption path with owner and expiry | Without one, they bypass the platform |
| What is the platform's contract? | Support levels, upgrade notice, deprecation policy | Tenants plan around it; breaking it is a platform incident |

Three principles help:

1. **Every capability exposed is a capability supported.** If tenants may create `Ingress` objects, you own the controller's behaviour under their mistakes.
2. **Policy belongs at admission, with evidence.** A rule that exists only in documentation is a suggestion; one enforced at admission with a report of violations is a control.
3. **The cluster-scoped objects are the sharp edges.** `ClusterRole`, `CustomResourceDefinition`, `ValidatingWebhookConfiguration`, `PriorityClass`, `StorageClass` and node-level settings change everyone's cluster; restrict who may create them and review changes like infrastructure code.

## Upgrades

A cluster is upgraded forever, and the cost of upgrading compounds with every skipped version.

**Version skew.** Kubernetes publishes a skew policy; at the time of writing the key points are: the control plane is upgraded one minor version at a time (no skipping); kubelets may be several minor versions older than the API server (three, from recent releases) but never newer; kube-controller-manager and the scheduler may lag the API server by one minor; `kubectl` may differ from the API server by one minor in either direction. Always read the policy for your target version rather than relying on this summary.

**An upgrade sequence**

| Phase | Action | Evidence before moving on |
| --- | --- | --- |
| Prepare | Read release notes for removals and behaviour changes; scan for deprecated API usage; verify add-on compatibility; take an etcd backup (self-managed) | Deprecated-API report is empty; compatibility matrix reviewed |
| Rehearse | Upgrade a non-production cluster that matches production's add-ons and policies | Conformance and smoke tests pass; workload SLOs hold |
| Control plane | Upgrade one minor version; wait for health | `/readyz` clean; controllers and webhooks behaving |
| Add-ons | Upgrade network plugin, DNS, ingress controller and metrics to versions supporting the new release, in a safe order | Add-on health; DNS and traffic tests |
| Nodes | Surge or replace node pools; cordon and drain; respect PDBs and capacity headroom | Pod rescheduling clean; no stuck drains |
| Verify | Run end-to-end checks; compare error budgets; record versions | Evidence attached to the change |

**Rollback is not symmetrical.** You can usually roll back a node pool (return to the old image) but rarely the control plane: etcd data may be migrated forward, and downgrade is unsupported or risky. The real rollback for a control-plane upgrade is a *restore from backup into a new cluster*, which is why rehearsal and backup verification matter more than a rollback plan on paper.

**In-place versus replace.** In-place upgrades are cheaper but carry risk to the live cluster; replacing nodes (and, for the highest-stakes platforms, entire clusters) gives you a clean rollback by moving traffic back, at the price of running two. Match the approach to the cost of failure.

**API deprecation hygiene.** Before each upgrade, scan manifests and live objects for removed APIs (for example with `kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis`, or a tool such as `pluto`), fix them one minor version ahead of removal, and run controllers and CRDs against the target version in a staging cluster first. Stored custom resources may also need version migration before an old version is removed from a CRD.

```bash
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis | head
kubectl get nodes -o custom-columns=NAME:.metadata.name,KUBELET:.status.nodeInfo.kubeletVersion
kubectl get crd -o custom-columns=NAME:.metadata.name,STORED:.status.storedVersions
```

## Cluster design choices

Managed versus self-managed control planes; node pools by workload type; single large cluster versus many small clusters (blast radius and tenancy versus operational overhead); regional versus zonal clusters; upgrade strategy; and which add-ons are platform-owned. There is no best answer — record the decision, its alternatives and revisit conditions.

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

## Expert trade-offs

| Tension | One extreme | The other | Defensible position |
| --- | --- | --- | --- |
| Tenancy density versus blast radius | One big shared cluster | Cluster per team | Per environment, namespaces per team, revisit on stated triggers |
| Strict admission versus cluster self-healing | Fail-closed everywhere | Fail-open everywhere | Fail-closed for security-critical rules, with exemptions and replicas; fail-open for advisory rules |
| Autoscaling responsiveness versus cost | Large headroom | Pure reactive scaling | Headroom sized to the burst you must absorb during node start time |
| Upgrade frequency versus stability | Upgrade immediately | Skip versions | Regular cadence one minor behind latest, rehearsed |
| Extensibility versus supportability | Open CRDs and webhooks | Locked-down raw API | Curated extension points with review |
| CPU limits versus predictability | Limits everywhere | None | Accurate requests, memory limits, measured CPU policy |
| Multi-cluster resilience versus complexity | Single region | Active-active everywhere | Active-passive with a tested failover until the data layer justifies more |

A useful expert habit is to **write the sentence before choosing**: "We accept *cost* to reduce *specific risk*, and we will know it failed when *observable signal*." If you cannot complete that sentence, the control is cargo cult.

## Knowledge consolidation

- Every write passes **authentication, authorisation, mutating admission, validation, validating admission and persistence**, in that order; the order makes rejections readable.
- **Optimistic concurrency and watches** make the control plane scalable; they also make every consumer eventually consistent and potentially stale.
- Controllers are **level-triggered and idempotent**; their limits are latency, staleness, unbounded retry, field fights, finalizers and leader-election overlap.
- A rollout checks **readiness, not correctness**, and each Pod, not the aggregate.
- The scheduler **samples, scores and binds once**; rebalancing is a separate act.
- Scaling is several axes, each bounded by **requests, metric lag, node start time and control-plane budget**.
- Multi-cluster work is dominated by **state, identity, traffic and drift**, not by Kubernetes objects.
- The costliest faults are **interactions**: webhooks and self-healing, DNS and connection tracking, quotas and throttling, budgets and drains.
- **Expose only what you will support**; policy belongs at admission with evidence.
- Upgrades obey **skew rules**, depend on **rehearsal and backups**, and roll back asymmetrically.

## Exercises

**Exercise 1 — Trace the request path.** With verbose client logging, apply a Deployment and then apply a manifest that violates a schema and one that violates an admission rule. For each, identify the stage that rejected it from the error alone.

**Exercise 2 — Field ownership.** Create a Deployment with `replicas: 3` by server-side apply from one manager, create an HPA, and apply the manifest again with `replicas: 3`. Show managed fields, observe the fight, and fix it by transferring ownership.

**Exercise 3 — Orphaned finalizer.** In a disposable cluster, create a custom resource with a finalizer whose controller does not exist, delete its namespace, and diagnose why the namespace stays `Terminating`. Describe the cleanup you skip by removing the finalizer.

**Exercise 4 — Reproduce throttling.** Run a multi-threaded service with a CPU limit and generate bursty load. Capture latency percentiles and the container's throttling counters. Fix it in two ways and compare tail latency across at least five runs per variant.

**Exercise 5 — Fail-closed webhook.** Deploy a validating webhook with `failurePolicy: Fail` that runs in the cluster. Remove its Pods and try to create them again. Design the exemptions, replica count and monitoring that make the failure survivable, and test them.

**Exercise 6 — HPA arithmetic.** For three scenarios (target 60%, usage 90% with 4 replicas; usage 55% with 6 replicas; request set far too high), compute the desired replicas by hand. Then run them and compare with the observed behaviour, including the stabilisation window.

**Exercise 7 — Upgrade rehearsal plan.** Write an upgrade runbook for a cluster from minor version N to N+1 with named add-ons. Include the skew rules, the evidence required between phases, the rollback story for each phase, and what you would check about PDBs and capacity beforehand.

**Exercise 8 — Multi-cluster design critique.** Given an active-active two-region design with a single regional database, write a one-page review that names where writes go during a regional partition, the real recovery point and time, and the tests that would substantiate the claim.

**Solution notes.**

*Exercise 1.* Expect a 422-style `Invalid` message naming a field for the schema failure, and a message that cites the admission policy or webhook for the policy failure; a 403 would mean authorisation rejected the call before either. If both look alike, check the verbose output for which request failed and the ordering of stages.

*Exercise 2.* `--show-managed-fields` lists one manager owning `spec.replicas` and another updating it. The fight shows as the replica count flipping on each apply. Fix by removing `replicas` from the applied manifest (so the HPA owns it) or by forcing a single owner deliberately.

*Exercise 3.* The namespace shows a deletion timestamp and a condition naming remaining content; the custom resource carries the finalizer. Removing it frees the namespace but skips whatever cleanup the missing controller would have done (for example deleting an external resource). Recording that cost is the point.

*Exercise 4.* Throttled-time counters should rise during the latency bursts. Both fixes (fewer worker threads; raising or removing the limit while keeping a request) should reduce p99; report ranges across runs, not a single number.

*Exercise 5.* With the webhook's Pods removed and `Fail` in force, creating them is rejected. Surviving designs exempt the webhook namespace (and `kube-system`) via namespace selectors, run at least two spread replicas, and alert on webhook errors. If your test cluster recovers without the exemptions, check that the webhook actually matched the Pods.

*Exercise 6.* Scenario one: `ceil(4 × 90/60) = 6`. Scenario two: `ceil(6 × 55/60) = 6`, and the ratio is within the default 10% tolerance in any case, so no change. Scenario three: utilisation relative to an inflated request stays tiny, so the HPA scales down to `minReplicas` however loaded the service is. Scale-down waits for the stabilisation window.

*Exercise 7.* A strong runbook lists the skew limits for the real version pair, orders control plane, add-ons and nodes, attaches a verification command to each phase, states that control-plane rollback means restore into a new cluster, and checks `kubectl get pdb` for zero allowed disruptions and capacity for one node of headroom.

*Exercise 8.* Look for: an explicit statement that the single database is the failure domain; the recovery point (replication lag at failure) and recovery time (promotion and cut-over); a decision on whether the surviving region can accept writes; health-check and TTL behaviour; and a recurring failover test. A design that claims active-active but has one writable database is active-passive for writes.

## Mentoring prompts

Walk through everything that happens, in order, between `kubectl apply` of a Deployment and a request being served by the new Pod. Why can a readiness probe that checks a shared database make an outage worse? What would you need to prove to claim zone-failure tolerance for a workload? Describe a case where a policy control makes the cluster less able to repair itself, and how you would test for it. Which of your platform's guarantees depend on a controller behaving, and what happens if it stops? What would make you add a second cluster, and what would you refuse to claim when you did?

---
