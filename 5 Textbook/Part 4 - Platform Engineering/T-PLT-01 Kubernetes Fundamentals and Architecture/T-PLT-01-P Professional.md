# T-PLT-01-P — Professional Engineering

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-p"></a>
#### T-PLT-01-P — Professional Engineering

## Why this matters

A cluster that runs a demo is not a cluster you can hand to other teams. A production cluster has answered questions the demo never asked. What happens to every workload if one availability zone disappears? If the control plane is unreachable for twenty minutes, what keeps working and what silently stops? How much capacity must stay free so that a node drain or a node loss does not turn into an outage? Which Pods can talk to which, and who decided? When a workload misbehaves at 03:00, who owns it, and can the on-call engineer find that out in one command? And when someone asks "is this service highly available?", what *evidence* — not belief — supports the answer?

Professional practice turns those questions into **explicit, reviewable, testable decisions**: a cluster architecture with stated failure domains, a control plane whose availability is understood, node capacity planned with headroom, network boundaries enforced rather than assumed, ownership written into the objects themselves, and a habit of attaching evidence to every resilience or security claim. This section assumes the Beginner and Intermediate material (spec and status, scheduling, controllers, Services, probes, requests and limits). Examples use the neutral `orders-api` service and placeholder registry names.

A recurring theme: **a Kubernetes feature is a mechanism, not a guarantee.** Each control below reduces a specific risk and leaves others untouched. Learn what each one does *not* do.

## First principles: a cluster as a set of contracts

Treat a production cluster as a set of contracts between the platform and its tenants. If a clause is not written down and testable, assume it is unmet.

| Contract clause | Question it answers | Where it is expressed |
| --- | --- | --- |
| Failure domains | Which failures does the cluster tolerate: Pod, node, zone, control plane? | Cluster topology, node pools, spread rules, drills |
| Capacity | How much headroom exists, and what consumes it? | Allocatable arithmetic, quotas, autoscaler settings |
| Isolation | Who can reach whom, and who can change what? | Namespaces, RBAC, network policy, admission |
| Ownership | Who answers for each object and each add-on? | Labels, annotations, namespace conventions, runbooks |
| Lifecycle | How are rollouts, drains and upgrades done safely? | Rollout strategy, disruption budgets, termination settings |
| Evidence | How do we know any of the above holds? | Drill records, policy reports, dashboards |

## Cluster architecture decisions

Every cluster design is a set of choices with costs. Record each choice, the alternatives you rejected and the condition under which you would revisit it.

| Decision | Options | What you gain | What you pay |
| --- | --- | --- | --- |
| Who runs the control plane | Managed service, or self-managed | Managed: no etcd or API server operations, provider availability targets. Self-managed: full control of flags and versions | Managed: limits on tuning and a provider-defined upgrade cadence. Self-managed: you own etcd backup, certificates and upgrades |
| Topology of the cluster | Zonal, or regional with nodes in three zones | Regional: control plane and nodes survive one zone loss | More cross-zone traffic cost and latency; capacity must exist in each zone |
| Node pools | One pool, or pools by workload type (general, memory-heavy, GPU, system) | Right-sized machines; isolation of noisy workloads; separate upgrade cadence | More pools to size and to keep headroom in |
| Tenancy model | Shared cluster with namespaces, cluster per environment, cluster per team | See the Expert level for the comparison | Blast radius against operational overhead |
| Add-on ownership | Platform-owned (DNS, network plugin, ingress controller, metrics) versus team-installed | Consistent behaviour; one upgrade path | The platform team becomes a dependency for every tenant |

A reasonable default, with stated assumptions: a managed regional control plane, nodes spread across three zones, separate system and workload node pools, namespaces per team, and platform-owned add-ons. Revisit when team count, compliance needs or upgrade pain changes.

**Choose the add-on set deliberately.** A cluster without add-ons cannot do much. At minimum you need: a network plugin (CNI) that enforces network policy, cluster DNS, a metrics source for `kubectl top` and autoscaling, an ingress or gateway controller, a log and metric pipeline, and a certificate and secrets story. Each add-on is a workload that can fail, needs upgrades and has its own failure signature; list them, name an owner and decide which are *critical path* (DNS, network plugin) and which are not.

## Control-plane availability

The control plane stores state and makes decisions; it is not on the data path of running traffic. That distinction determines what an outage costs.

| Control-plane condition | Pods already running | Existing Service traffic | Changes (deploys, scaling) | Self-healing (reschedule, replace) |
| --- | --- | --- | --- | --- |
| Fully available | Normal | Normal | Normal | Normal |
| API server unreachable | Keep running; kubelets continue with last known state | Continues; endpoint changes stop propagating | Impossible | Stops; a crashed container is still restarted locally by the kubelet, but a lost node is not detected |
| etcd lost quorum | As above; API reads and writes fail | As above | Impossible | Stops |
| Scheduler down | Normal | Normal | New Pods stay `Pending` | Replacement Pods are not placed |
| Controller manager down | Normal | Normal | Rollouts, scaling and endpoint updates stall | Replacements are not created |

The practical reading: a control-plane outage is **a loss of the ability to change and to heal**, not an immediate loss of service. It becomes a service outage if something *needs* a change or a heal during the window — a node dies, a certificate expires, a rollout must be reverted, traffic needs to shift.

**What high availability means for the control plane.** A highly available control plane runs several API server instances behind a load balancer and an etcd cluster of an odd number of members (three or five), spread across failure domains. etcd uses a majority quorum: with three members it tolerates one failure, with five it tolerates two; an even number adds cost without tolerating more failures. Scheduler and controller manager run as several instances with leader election; one is active.

**Three controls worth knowing on the API path**

| Control | What it protects | Failure behaviour to understand |
| --- | --- | --- |
| API priority and fairness | The API server from one noisy client starving others | A runaway controller or CI job can still degrade shared latency; identify heavy clients by user agent |
| Admission webhooks | Policy enforced at write time | `failurePolicy: Fail` blocks all matching writes when the webhook is down; `Ignore` lets everything through. Exempt the webhook's own namespace and system namespaces so the cluster can heal |
| etcd size and compaction | Control-plane performance | Large objects, excessive events and unbounded custom resources inflate etcd and slow everything |

**What you must be able to say about control-plane availability**

- *Who runs it,* and what the provider's availability commitment does and does not cover (it usually covers the API endpoint, not your add-ons or your nodes).
- *What state is lost if etcd is lost,* and when it was last restored in a drill. For a self-managed cluster, an etcd backup that has never been restored is a hope, not a backup.
- *How long you can tolerate it being unreachable,* in terms of the changes and heals you would need in that period.
- *What your emergency access path is* if the normal identity provider or a webhook is part of the failure.

```bash
# Is the API healthy, and which components report problems?
kubectl get --raw='/readyz?verbose' | head -30
kubectl get --raw='/livez?verbose'  | head -30

# Self-managed: etcd health and a snapshot (illustrative; endpoints and certificates differ)
ETCDCTL_API=3 etcdctl endpoint health --cluster
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F).db
```

## Node capacity

Capacity planning at the node level starts with a fact that surprises people: **a node's allocatable resources are less than its size.**

```text
node capacity (what the machine has)
  − kube-reserved      (kubelet, runtime)
  − system-reserved    (OS daemons)
  − eviction threshold (memory headroom before the kubelet starts evicting)
  = allocatable        (what the scheduler may hand out as requests)
```

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU:.status.allocatable.cpu,MEM:.status.allocatable.memory,PODS:.status.allocatable.pods
kubectl describe node <node> | sed -n '/Allocated resources/,/Events/p'
```

**Headroom is an availability feature.** The scheduler fills nodes up to their allocatable requests; if the cluster is packed, a node loss or a drain leaves displaced Pods `Pending`. Work the arithmetic for the failure you claim to tolerate.

| Failure to tolerate | Capacity rule | Worked example |
| --- | --- | --- |
| One node lost | Total requests ≤ allocatable of (N − 1) nodes | 6 nodes × 8 vCPU allocatable; plan for 5 × 8 = 40 vCPU of requests, not 48 |
| One zone lost (3 zones) | Total requests ≤ allocatable of the surviving two zones | Each zone holds 1/3; the remaining two must absorb 100% of requests, so average utilisation of requests must stay at or below about 66% |
| Rolling upgrade, one node at a time | One node of headroom, plus surge capacity for Deployments | As node loss, plus `maxSurge` Pods |
| Burst before the autoscaler reacts | Spare capacity or low-priority placeholder Pods that can be preempted | Size to the burst you must absorb during node-start time (minutes) |

Other node-level limits that bite in production:

| Limit | Symptom when exhausted | Where to look |
| --- | --- | --- |
| Pods per node | `Pending`: `Too many pods` | `allocatable.pods`; network plugin address ranges |
| Pod IPs available | New Pods stuck in `ContainerCreating` with network errors | CNI logs and address pool |
| Ephemeral storage | Evictions for `DiskPressure`; Pods evicted for exceeding ephemeral-storage requests | Node conditions; `describe pod` |
| PIDs | Fork failures inside containers | Node and container `pids` limits |
| Volume attach limits per node | `Pending` for volumes that cannot attach | Events on the Pod and the claim |

**Autoscaling is not capacity planning.** The cluster autoscaler adds nodes only when Pods are `Pending` because of insufficient capacity; node start takes minutes. Horizontal Pod autoscaling adds Pods based on a metric but still needs room for them. Both depend on **accurate requests**: an autoscaler scaling on CPU utilisation *relative to the request* produces nonsense when the request was a guess.

**Right-sizing loop.** Measure real usage over a representative period (including peaks), set requests near typical usage and memory limits above the observed peak, then compare requested against used capacity per namespace and review the largest gaps. Over-requested capacity is paid-for waste; under-requested capacity is an outage waiting for the next noisy neighbour.

## Graceful termination and disruption

When a Pod is deleted it is marked `Terminating` and removed from endpoints *in parallel* with the `preStop` hook and `SIGTERM`. Endpoint removal propagates asynchronously, so traffic can still arrive briefly after `SIGTERM`. A short `preStop` sleep gives the network time to catch up.

| Setting | Purpose | Gotcha |
| --- | --- | --- |
| `preStop` sleep | Drain window | The native sleep action needs a recent Kubernetes; otherwise use an `exec` sleep and ensure the binary exists |
| `terminationGracePeriodSeconds` | Maximum shutdown time | Too short cuts off in-flight requests |
| Application handles `SIGTERM` | Clean exit | A 30 s delete means `SIGKILL` was needed |
| PodDisruptionBudget | Limits voluntary evictions (drains, upgrades) | Does nothing for crashes or node failure |
| `topologySpreadConstraints` | Spread across nodes or zones | `ScheduleAnyway` is a preference; `DoNotSchedule` can leave Pods Pending |

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: orders-api }
spec:
  maxUnavailable: 1
  selector:
    matchLabels: { app: orders-api }
---
# Pod template fragment
spec:
  terminationGracePeriodSeconds: 45
  containers:
    - name: api
      lifecycle:
        preStop:
          exec: { command: ["sleep", "10"] }
  topologySpreadConstraints:
    - maxSkew: 1
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels: { app: orders-api }
```

A PodDisruptionBudget with `minAvailable: 1` on a single replica blocks every drain; size budgets against replicas. The grace period must exceed the `preStop` delay plus the application's own drain time, or the kubelet will send `SIGKILL` mid-drain.

## Resource policy

Set memory limits (an OOM kill is a visible failure rather than a noisy neighbour). Many teams omit CPU limits to avoid throttling latency while keeping CPU requests accurate and enforcing quotas; whichever you choose, policy must match it (do not later mandate a CPU limit that you decided against). Size from load testing and history, not guesses.

| Policy element | Purpose | Failure if absent |
| --- | --- | --- |
| Requests on every container | Placement and autoscaling are meaningful | `BestEffort` Pods; overcommitted nodes |
| Memory limit with headroom | Contains leaks and spikes | One Pod can take the node's memory |
| `ResourceQuota` per namespace | Caps a tenant's total claim | One team starves the rest |
| `LimitRange` defaults | Gives sensible values to Pods that omit them | Quota rejections for omitted requests |
| Priority classes (few, documented) | Protects critical workloads under pressure | Critical Pods preempted by batch jobs, or the reverse |

## Network boundaries

The default Kubernetes network is **flat and open**: every Pod can reach every other Pod and, usually, the internet. Namespaces do not change that. Boundaries exist only where you create and enforce them.

| Boundary | Mechanism | What it does not do |
| --- | --- | --- |
| Between workloads | NetworkPolicy, enforced by the network plugin | Has no effect if the plugin does not implement policy; says nothing about application-layer authorisation |
| Between namespaces | Same, using namespace selectors | A namespace is not a network boundary without policy |
| Into the cluster | Service type, ingress or gateway rules, load balancer settings | A `LoadBalancer` Service is public if the cloud provider says so, whatever you meant |
| Out of the cluster | Egress policy, NAT or proxy, DNS controls | Default allows all egress, including to metadata services |
| To the API server | Authentication, RBAC, endpoint access controls | A public API endpoint is reachable by anyone who can authenticate or exploit it |
| Between nodes | Node network and security groups | Pod traffic often rides the node network; node access is cluster access |

A baseline: deny all ingress to a namespace, then allow only declared paths, and allow DNS egress explicitly.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress, namespace: orders }
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-gateway-to-orders-api, namespace: orders }
spec:
  podSelector:
    matchLabels: { app: orders-api }
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: { kubernetes.io/metadata.name: ingress }
          podSelector:
            matchLabels: { app.kubernetes.io/name: gateway }
      ports:
        - { protocol: TCP, port: 8000 }
```

If you later add an egress `Default deny`, you must allow DNS (UDP and TCP port 53 to the cluster DNS Pods) or every lookup fails, and the symptom looks like an application timeout.

**Verify a boundary, do not assume it.** Policy objects existing is not evidence. Test from a Pod that should be denied and a Pod that should be allowed:

```bash
kubectl -n orders run probe --rm -it --image=busybox:1.36 --restart=Never -- wget -qO- -T 3 http://orders-api/health
# expected from an unlisted namespace: timeout; from the allowed gateway: 200
```

Policy is covered more fully in T-PLT-03; the professional point here is that a network boundary is a claim that needs a test.

## Ownership

A cluster shared by many teams fails quietly when nobody knows who owns what. Make ownership a property of the objects, and enforce it.

| Ownership question | Where the answer lives |
| --- | --- |
| Which team owns this workload? | A standard label such as `team`, plus the namespace |
| Who is on call for it? | An annotation pointing to a runbook or on-call rotation |
| Which source of truth produced it? | Label or annotation naming the repository and delivery tool |
| Who may change it? | RBAC role bindings in the namespace |
| Who owns the add-ons it depends on? | A platform catalogue listing each add-on, its owner and its upgrade path |

```yaml
metadata:
  labels:
    app.kubernetes.io/name: orders-api
    app.kubernetes.io/part-of: checkout
    app.kubernetes.io/managed-by: git-delivery
    team: orders
  annotations:
    example.com/runbook: "https://runbooks.example.com/orders-api"
    example.com/oncall: "orders-primary"
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: orders-deployer, namespace: orders }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "configmaps"]
    verbs: ["get", "list", "watch"]
```

Grant the narrowest role that works; `list` and `watch` on Secrets expose values. Prefer binding roles to groups from your identity provider rather than to individuals, and review bindings periodically. A boundary between teams exists only if both RBAC (who may change) and network policy (who may reach) enforce it.

**A platform-versus-team responsibility map**

| Area | Platform owns | Workload team owns |
| --- | --- | --- |
| Cluster, nodes, control plane | Yes | No |
| Add-ons (DNS, network plugin, ingress controller, metrics agents) | Yes | No |
| Namespace, quota, baseline policy | Yes (templates) | Requests within quota |
| Deployment manifests, probes, resources | Review standards | Yes |
| Hostnames and certificates | Controller and issuer | Request and use |
| Application recovery behaviour | Platform tooling | Yes |
| Incident response for the app | Shared escalation path | First responder |

Write it down in the team agreement. Ambiguity in this table is where incidents spend their first hour.

## Secrets are not secret by default

Anyone who can `get` the Secret, or exec into a Pod that mounts it, reads the plaintext.

- Restrict `get`, `list` and `watch` on Secrets by RBAC (`list` returns values).
- Enable encryption at rest for etcd where you control it; managed services offer it.
- Do not commit Secret manifests with values; use an external secrets operator, sealed secrets or a cloud secret manager.
- Prefer mounting as files over environment variables when the app can read files; environment variables leak into crash dumps and child processes.
- Treat etcd backups as sensitive: they contain Secrets.

## Workload kinds

| Workload | Use when | Key properties |
| --- | --- | --- |
| Deployment | Stateless services | Interchangeable Pods |
| StatefulSet | Stable identity or storage | Ordered names, per-Pod volumes, headless Service |
| DaemonSet | One Pod per node | Log agents, network plugins, node exporters |
| Job and CronJob | Run to completion, scheduled | `backoffLimit`, `ttlSecondsAfterFinished`, `concurrencyPolicy` |

A Job can run more than once under retries, so its work must be idempotent; database migrations need a design (expand/contract), not just a Job. Persistence is not durability: a node-local volume survives Pod deletion but not node loss, and is not a backup. Run production databases on managed services unless you have the operational discipline for replication, failover, backups and upgrades.

## Ingress and Gateway

An Ingress or Gateway routes external HTTP(S) to Services, terminating TLS and applying host and path rules. It needs a controller; choose a controller, define ownership of certificates and hostnames, and treat routing configuration as security-relevant. A wildcard host rule or an unreviewed path can expose an internal Service, so route changes deserve the same review as firewall changes.

## Resilience and security evidence

The professional discipline is to **attach evidence to each claim** and to refuse claims the evidence does not support.

**Recovery claims — what you may and may not say**

| Evidence you have | Claim you may make | Claim you may not make |
| --- | --- | --- |
| Pod kill, Deployment replaces, probes show counts | "Recovers from single-Pod loss without intervention; client impact measured as X" | "Highly available" |
| Two replicas on two nodes | "Replicas are scheduled across nodes" | "Survives node or zone failure" on a single-host cluster |
| Node-stop drill | "Pods reschedule after node loss within about T seconds on this cluster" | "Production failover time" |
| PDB defined | "Voluntary disruptions are bounded" | "Crashes and node loss are bounded" |
| Node-local volume | "Data survived a Pod restart" | "Data is durable or backed up" |
| Network policy objects applied | "Policy is configured" | "Traffic is restricted" without a denied-path test |
| Regional control plane | "The API endpoint tolerates one zone loss" | "Workloads tolerate zone loss" |

**An evidence pack for a production workload.** Keep it short and re-runnable:

| Claim | Evidence | How often re-tested |
| --- | --- | --- |
| Survives loss of one node | Drain and node-stop drill result with request error rate and recovery time | Per quarter and after topology changes |
| Rolls out without errors | Rollout under load with error budget impact | Per significant change to probes or termination |
| Spread across zones | `kubectl get pods -o wide` joined to node zone labels | Automated check |
| Cannot be reached from unlisted namespaces | Denied-path test result | In CI for policy changes |
| Secrets not readable by the wrong roles | `kubectl auth can-i` matrix | Per RBAC change |
| Capacity for one zone loss | Allocatable-versus-requests report | Weekly |

```bash
# Spread evidence: Pods by node and zone
kubectl -n orders get pods -l app=orders-api -o wide
kubectl get nodes -L topology.kubernetes.io/zone

# A disruption drill: drain one node under load and watch client-visible errors elsewhere
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data --timeout=300s
kubectl get pods -n orders -w

# Who can read Secrets in a namespace?
kubectl auth can-i get secrets -n orders --as=system:serviceaccount:orders:orders-api
```

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Safe rollouts | `maxUnavailable: 0`, readiness gates, `preStop` drain | Deployments without probes |
| Traffic only to healthy Pods | Accurate readiness | Liveness that depends on a database |
| Prevent noisy neighbours | Requests, memory limits, quotas | BestEffort Pods in shared clusters |
| Survive zone loss | Spread, headroom arithmetic, a drill | Claiming it from configuration alone |
| Predictable control-plane failure | Understand what stops during an outage; test webhook failure policy | Fail-closed webhooks with no exemptions |
| Isolation between teams | Default-deny network policy, RBAC, quotas | Namespaces alone |
| Clear ownership | Required labels and annotations, a responsibility map | Anonymous workloads |
| Config changes | Roll out via Git; hash-triggered restarts | Editing live objects |
| Sensitive values | External secret manager, restricted RBAC | Plaintext Secret manifests in Git |

## What can go wrong: professional failure patterns

| Pattern | What happens | Prevention |
| --- | --- | --- |
| Cluster packed to 90% of requests | A single node loss leaves Pods `Pending` | Headroom rule per failure domain |
| Fail-closed admission webhook outage | Nothing can be created, including the fix | Exempt system namespaces; run webhook with replicas; test failure |
| Default-deny added without DNS egress | Every outbound call times out | Allow DNS first, test from a canary Pod |
| PDB too strict | Drains and upgrades block indefinitely | Size budgets to replicas; alert on blocked evictions |
| Spread with `DoNotSchedule` and a lost zone | Replacement Pods `Pending` | Prefer `ScheduleAnyway` for non-critical, plan capacity for the strict case |
| Requests copied from a template | Autoscaling and placement misbehave | Right-size from measurement |
| Unowned workloads | Nobody responds; cost and risk accumulate | Enforce ownership labels at admission |

## Knowledge consolidation

- A production cluster is a set of **contracts**: failure domains, capacity, isolation, ownership, lifecycle and evidence.
- A control-plane outage is a loss of **change and healing**, not of running traffic; it becomes an outage when something needs to change.
- etcd needs an **odd quorum**; webhooks and priority settings can make the API path itself a failure source.
- **Allocatable is less than capacity**, and headroom for the failure you claim to tolerate is part of the design.
- Autoscaling reacts to **requests and Pending Pods**; it does not substitute for capacity planning.
- The default network is **open**; boundaries exist only where enforced and tested.
- **Ownership belongs in the object**: labels, annotations, namespace and RBAC.
- A claim without evidence is a **belief**; match each claim to a drill, test or report.

## Exercises

**Exercise 1 — Allocatable arithmetic.** On your practice cluster, list each node's capacity and allocatable CPU and memory. Compute total requests and the headroom after losing the largest node. State which failure you can tolerate and which you cannot.

**Exercise 2 — Drain drill.** Deploy `orders-api` with three replicas, a PDB with `maxUnavailable: 1`, and a `preStop` sleep. Drive steady requests, drain a worker, and record errors, Pod movement and recovery time. Repeat after removing the `preStop` and compare.

**Exercise 3 — Break a PDB.** Set `minAvailable: 3` on three replicas and try to drain. Record the message and explain why it is correct behaviour. Repair it.

**Exercise 4 — Enforce a boundary.** Create two namespaces. Prove that a Pod in one reaches a Service in the other. Apply a default-deny ingress policy and an allow rule for one named Pod; record which tests now fail and which pass. (Use a `kind` cluster with a network plugin that enforces policy.)

**Exercise 5 — Webhook failure.** In a disposable cluster, install a validating webhook that is deliberately unreachable with `failurePolicy: Fail`. Observe the effect on creating a Pod, then design the exemptions and replicas that prevent a repeat.

**Exercise 6 — Ownership audit.** Write a command that lists Deployments missing the `team` label across all namespaces. Add the label requirement to a policy proposal and note one exception you would allow.

**Solution notes.**

*Exercise 1.* Allocatable is below capacity on every node; the numbers come from your own cluster. Headroom after losing the largest node is the sum of the other nodes' allocatable CPU and memory minus total requests; if it is negative, those Pods become `Pending` after a loss. A single-host `kind` cluster tolerates no host failure whatever the arithmetic says.

*Exercise 2.* With the `preStop`, errors during the drain should be fewer or absent; without it, brief 502s or resets are plausible as traffic reaches terminating Pods. Treat the difference as the finding. Timings on `kind` are not production numbers.

*Exercise 3.* The eviction is refused with a message that the disruption budget would be violated. That is correct: the budget says no Pod may be unavailable, so no voluntary eviction is allowed. Fix by reducing `minAvailable` or using `maxUnavailable: 1`.

*Exercise 4.* Before the policy, cross-namespace calls succeed. After default deny, calls from unlisted Pods time out while the named Pod still succeeds. If every call still succeeds, the network plugin probably does not enforce policy, which is itself the key finding.

*Exercise 5.* Creates are rejected with a webhook call error; because the webhook's own Pods may be among the things you cannot create, the cluster cannot heal itself. Exempting the webhook's namespace and system namespaces, running multiple replicas and monitoring webhook latency break the loop.

*Exercise 6.* One approach is `kubectl get deploy -A -o json | jq -r '.items[] | select(.metadata.labels.team == null) | "\(.metadata.namespace)/\(.metadata.name)"'`. Exceptions are legitimate when documented with an owner and an expiry date.

## Mentoring prompts

If the API server is unreachable for twenty minutes, what keeps working, what does not, and what event during that window would turn it into an outage? Why does "we have three replicas" not support the claim "we tolerate a zone loss"? What would you ask a team before agreeing to give them a `ClusterRole`? Which of your cluster's add-ons are on the critical path of every workload, and who owns each?

---
