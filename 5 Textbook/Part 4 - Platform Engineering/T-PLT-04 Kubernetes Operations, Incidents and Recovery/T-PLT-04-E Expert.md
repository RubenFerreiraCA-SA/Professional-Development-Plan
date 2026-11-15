# T-PLT-04-E — Expert Depth

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-e"></a>
#### T-PLT-04-E — Expert Depth

## Why this level exists

The earlier levels make one cluster operable by a team. This level is about what changes when the unit of operation is a **fleet**: dozens or hundreds of clusters, thousands of nodes, many tenants, several regions, and failure modes that only appear at scale. The failures are different in kind. A control-plane restart creates a thundering herd; a bad admission policy is delivered to every cluster in minutes; an etcd database fills quietly for months; a certificate authority expires and takes every node with it; an identity provider outage leaves nobody able to log in to fix the thing it broke.

Expert practice is therefore less about commands and more about **structure**: failure domains that bound blast radius, change delivery that is progressive and observable, recovery procedures that are rehearsed from empty infrastructure, reliability programmes that turn incidents into durable improvements, and incident response that works when the platform itself is the casualty. Commands appear where precision matters, especially around etcd. Outputs marked *illustrative* show shapes, not measurements, and every default quoted here should be checked against the versions you run.

## First principles: scale changes the failure physics

Four effects explain most large-scale surprises.

1. **Correlation.** Components that are independent in design share dependencies in practice: one CA, one image registry, one DNS zone, one identity provider, one configuration pipeline, one cloud control plane. A failure that looks like "many things broke" is usually "one shared thing broke". Map shared dependencies explicitly; the dependency graph, not the cluster inventory, defines the real blast radius.
2. **Amplification and retry storms.** When a dependency recovers, every client retries at once. Controllers relist, kubelets re-register, Pods restart, caches refill and connections reopen simultaneously, and the recovering component is knocked over again. Recovery needs back-off, jitter, admission control and sometimes deliberate throttling of the recovery itself.
3. **Metastability.** Some systems have a stable bad state that persists after the trigger is gone: the API server is overloaded because clients retry, and clients retry because the API server is overloaded. Removing the trigger does not restore service; you must reduce load below a threshold (shed, pause controllers, scale down clients) to break the loop.
4. **Rare events become routine.** With 500 clusters, a one-in-a-thousand-per-year fault happens every other day somewhere. Automation must handle common failures unattended, and humans should be reserved for novel ones.

These effects argue for **cells** (independent units that fail separately), **progressive delivery** (small first, observe, widen), and **load-shedding priorities** (decide in advance what to protect). The rest of this section applies them.

## Designing for failure domains in Kubernetes

Control-plane quorum (three or five members across zones), node pools across zones, storage that is zone-aware (a volume bound to one zone pins Pods there), load balancers with cross-zone behaviour, and DNS. For each, ask: what happens on loss of one node, one zone, the control plane, the registry, the identity provider, the cloud API? A cluster is often only as available as its least redundant dependency.

| Domain | Typical loss | What survives | What does not |
| --- | --- | --- | --- |
| Pod / node | Crash, hardware | Replicated workloads with spreading | Singletons; local-disk state |
| Zone | Power, network, provider incident | Workloads spread over zones with headroom | Zonal volumes, single-zone pools, zonal load-balancer targets |
| Control plane (workload plane intact) | API outage | Running Pods keep running; nothing can change | Scaling, scheduling, rollouts, new Pods, controllers' repairs |
| Cluster | Bad upgrade, CA expiry, misconfiguration | Other clusters in the fleet | Everything in that cluster unless replicated elsewhere |
| Region | Provider region outage | Active-active or warm standby elsewhere | Single-region data and dependencies |
| Shared service | Registry, identity provider, DNS, CI | Cached images, break-glass identities | Pulls of uncached images, human logins, deployments |
| Fleet-wide change channel | Bad policy or controller version pushed everywhere | Only what the progressive delivery stopped | Everything it reached |

Two properties deserve emphasis. First, **a running workload does not need the control plane**: during an API outage, existing Pods keep serving, but nothing heals and nothing scales; design workloads to tolerate a control-plane gap of the length of your realistic RTO. Second, **a failure domain must be independent in fact, not in name**: two "independent" clusters that share a registry, a configuration repository and a certificate authority are one failure domain with two Pods inside.

## Control-plane operations in depth

### etcd

etcd is the cluster's only durable state, a Raft-replicated key-value store that must stay below a latency budget and a size quota.

| Signal | Why it matters | Typical action |
| --- | --- | --- |
| Disk fsync latency (WAL) | Raft commits need durable writes; slow disks cause leader elections and API timeouts | Dedicated fast storage; avoid noisy neighbours |
| Leader changes | Frequent changes mean instability | Investigate network, disk, CPU starvation |
| Database size versus quota | Over the quota etcd raises the `NOSPACE` alarm and becomes read-only | Compact, defragment, find the heavy resource, raise quota deliberately |
| Object count and size | Large numbers of Events, Secrets, ConfigMaps, CRs slow list calls | Limit, clean, shard |
| Member health and version | A single bad member can degrade quorum margin | Replace promptly |

```bash
export ETCDCTL_API=3
etcdctl --endpoints=https://10.0.0.11:2379,https://10.0.0.12:2379,https://10.0.0.13:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
  --key=/etc/kubernetes/pki/etcd/healthcheck-client.key \
  endpoint status -w table          # leader, DB size, raft index per member
etcdctl ... endpoint health
etcdctl ... alarm list
etcdctl ... get / --prefix --keys-only | cut -d/ -f3 | sort | uniq -c | sort -rn | head   # objects by resource type
```

A quota breach is a classic slow-motion outage: a controller or CRD creates objects without bound, the database grows for weeks, then the alarm fires and the cluster stops accepting writes. Respond by finding the heavy resource, deleting what is safe, **compacting**, then **defragmenting** each member one at a time (defrag blocks the member while it runs), and finally disarming the alarm. Prevention is monitoring of database size as a percentage of quota with alerts well before it nears, and capping unbounded resources.

### The API server

The API server is the choke point of the platform. Watch request latency and rate by verb and resource, **API Priority and Fairness** rejections (`429`), long-running watch counts, expensive `LIST` calls without pagination or resource-version, webhook latency and error rate, and memory.

| Pattern | Cause | Mitigation |
| --- | --- | --- |
| Slow cluster-wide, 429s | A noisy client or controller listing everything | Identify via audit logs and flow-control metrics; tune flow schemas; fix the client (informers, pagination) |
| Latency tied to creates and updates | Slow admission webhook | Set short timeouts; scope rules; `failurePolicy` decisions; scale webhook |
| Memory growth | Large lists, many watchers | Reduce watch fan-out; limit object sizes; scale control plane |
| Relist storm after restart | All clients re-list at once | Staggered restarts; priority levels that protect system components |

Webhooks deserve a special rule: **a webhook with `failurePolicy: Fail` that covers its own namespace or the system namespaces can deadlock the cluster**, because its Pods cannot be created while it is down. Exclude control-plane and the webhook's own namespace, keep it highly available, and know the emergency procedure to remove its configuration object.

### Certificates and trust

Certificate expiry across components (API server, kubelet client and serving, front-proxy, etcd, webhooks, service-mesh roots, ingress) is a scheduled outage. A root CA with a ten-year life is a ten-year timer that someone must remember. Keep an inventory of every CA and leaf with expiry dates, alert at 90, 30 and 7 days, automate rotation and **rehearse CA rotation**, which is harder than leaf renewal because trust bundles must overlap while old and new coexist.

## Capacity and cost

Track requests versus usage, bin-packing efficiency, headroom for failures (N+1 by zone), autoscaler behaviour, and the cost of idle capacity. Right-size with data; use priority classes so critical workloads preempt batch; consider spot or preemptible nodes for tolerant workloads with disruption handling.

At fleet scale capacity has structure:

| Concern | Expert practice |
| --- | --- |
| **Failure headroom** | Size each zone so the remaining zones absorb the lost one: with three zones, each runs at most about two-thirds utilisation for critical workloads |
| **Priority and preemption** | PriorityClasses define who is evicted; batch must never starve system components |
| **Autoscaler limits** | Cluster autoscalers act on pending Pods and take minutes; they depend on cloud quotas and instance availability. Know the maximum scale-up rate and the cloud quota ceilings |
| **Pod density and IP space** | Pod CIDRs, node `maxPods`, cloud ENI limits and subnet sizes cap the cluster silently; IP exhaustion looks like `FailedCreatePodSandBox` |
| **Node-level limits** | PIDs, file descriptors, conntrack table size, inodes, ephemeral storage |
| **Quotas as policy** | ResourceQuota and LimitRange express fairness; review them as the tenants change |
| **Cost allocation** | Label and attribute cost per tenant; idle requested capacity is a cost the requester should see |

```bash
kubectl get pods -A -o json | jq -r '[.items[] | select(.status.phase=="Pending")] | length'
kubectl describe node <n> | grep -E 'pods|cpu|memory|ephemeral-storage' | head
kubectl get nodes -o json | jq '[.items[].status.allocatable.pods|tonumber] | add'
```

A capacity plan has three horizons: the current headroom (are we safe for the loss of a zone today?), the growth forecast (when does the next node pool, subnet or quota increase need to be requested, given lead times?), and the event calendar (launches, sales, migrations). Test headroom by **actually cordoning a zone** in a non-production fleet and watching whether critical workloads schedule.

## Large-scale failures: a mechanism catalogue

### Control-plane restart and the thundering herd

When an API server returns after an outage, thousands of kubelets, controllers, operators and agents reconnect and re-list. The API server is hit by its heaviest possible request pattern at the moment it is least able to cope. Symptoms: repeated crash or readiness flapping, 429s, rising memory, controllers falling behind. Mitigation: bring control-plane instances back one at a time, rely on API Priority and Fairness to protect leader election and node heartbeats, pause or scale down noisy operators, and use client back-off and jitter. Design operators with informers, caches, bounded concurrency and exponential back-off.

### Mass NotReady and the eviction brake

When many nodes stop reporting, the node lifecycle controller marks them `Unknown`, taints them and begins evictions. To avoid making a network partition worse, it **rate-limits evictions when a large share of nodes in a zone is unhealthy, and in small clusters stops them altogether** (governed by flags such as `--unhealthy-zone-threshold`, `--node-eviction-rate` and `--secondary-node-eviction-rate`; check the defaults of your version). If every zone is unhealthy it assumes the problem is the control plane's own connectivity and halts evictions. This is protective behaviour, and it also means that **a partial outage may not self-heal** by rescheduling Pods; you may have to cordon, replace or repair nodes yourself.

### DNS at scale

CoreDNS is a hot spot: every Pod's lookup passes through it, `ndots:5` multiplies queries for external names, and connection tracking races can drop UDP packets. Symptoms: intermittent 5-second resolution delays, `SERVFAIL`, widespread timeouts. Mitigations: node-local DNS caching, fewer search-path expansions (use fully qualified names, tune `ndots` per workload), autoscaling CoreDNS in proportion to node count, and ensuring network policy always permits DNS.

### Image pull storms and registry dependence

A rollout, a node-pool replacement or a zone recovery causes thousands of nodes to pull the same image at once. Registry rate limits, bandwidth and authentication token endpoints become the bottleneck. Mitigations: regional pull-through caches or mirrors, pre-pulled base images, staggered rollouts, `imagePullPolicy: IfNotPresent` with digests, and **a recovery plan for the registry itself**: if new Pods cannot pull, nothing scales or heals. Know which critical images (CNI, DNS, ingress, the GitOps controller) must be available from a copy outside the registry that failed.

### Node-level exhaustion

| Resource | Failure | Evidence |
| --- | --- | --- |
| conntrack table full | Random connection resets or timeouts | Kernel log `nf_conntrack: table full`; node metrics |
| PIDs | Fork failures; Pods cannot start processes | `pid pressure`; limit per Pod configuration |
| Inodes / disk | `DiskPressure`; evictions; image garbage collection loops | Node condition; `df -i` |
| Ephemeral ports | Outbound connection failures from one workload | `connect: cannot assign requested address` |
| IP addresses | New Pods stuck creating sandboxes | CNI errors; subnet utilisation |

### Cascading failure through add-ons

An upgrade of the CNI, service mesh or policy engine is a fleet-wide change with a **node-level** blast radius, because every Pod depends on it. Treat these as control-plane-grade changes: canary, observe, widen. Keep a documented **fail-open versus fail-closed** decision for each (policy engines, webhooks, mesh sidecars): fail-closed protects security and risks availability; fail-open the reverse. Decide deliberately, per component, in advance.

## etcd and cluster recovery

### Taxonomy: what kind of loss is it?

Choose the procedure by the *kind* of failure; applying the biggest hammer first is a common and costly mistake.

| Situation | Quorum | Recommended approach |
| --- | --- | --- |
| One member down, data intact | Kept (2 of 3) | Restart or replace the member; no cluster-level restore |
| One member lost, data gone | Kept | Remove the member, add a fresh one that syncs from the leader |
| Majority lost, but a surviving member has recent data | Lost | Snapshot the surviving member's data first; then re-form the cluster from it (force-new-cluster), re-adding members |
| Majority lost, no usable member | Lost | Restore all members from a snapshot into a new cluster |
| Data corruption or logical damage (bad deletion, bad controller) | May be intact | Restore from a snapshot to a *separate* environment and extract what you need; restoring in place rewinds everything |
| Whole control plane lost, workloads running | N/A | Rebuild the control plane from backup or from definitions; workload plane keeps serving meanwhile |

### Quorum arithmetic

A cluster of *n* members needs `floor(n/2)+1` to make progress, so 3 tolerate one failure and 5 tolerate two. Even sizes add cost without adding tolerance (4 still tolerate one). More members slow writes, so five is the usual ceiling. Spread members across zones so that **one zone loss cannot take the majority**: three members in three zones, or five in three zones as 2/2/1, where losing a two-member zone still leaves three of five.

### Snapshot and restore

```bash
# Take a snapshot (regularly, from a healthy member, stored off-cluster and encrypted)
etcdctl --endpoints=https://10.0.0.11:2379 --cacert=... --cert=... --key=... snapshot save /backup/etcd-$(date +%F-%H%M).db
etcdutl snapshot status /backup/etcd-2026-11-15-0600.db -w table      # hash, revision, total keys, size

# Restore (each member, from the SAME snapshot, with a NEW cluster identity)
etcdutl snapshot restore /backup/etcd-2026-11-15-0600.db \
  --name etcd-1 --data-dir /var/lib/etcd-restored \
  --initial-cluster etcd-1=https://10.0.0.11:2380,etcd-2=https://10.0.0.12:2380,etcd-3=https://10.0.0.13:2380 \
  --initial-cluster-token etcd-restore-2026-11-15 \
  --initial-advertise-peer-urls https://10.0.0.11:2380
```

Key facts and traps:

- Restore **creates a new cluster identity**; all members must be restored from the same snapshot and started together with matching `--initial-cluster` settings. Old members with old data must not rejoin.
- Stop all API servers (and anything writing to etcd) before restoring, then point the API servers at the restored cluster. Restart in order: etcd, API server, controller manager and scheduler, then kubelets.
- **Time travel.** The restored state is the world as of the snapshot. Objects created later are gone from the API (a Deployment, a Secret, a claim), while their real counterparts, cloud load balancers, volumes and running containers, may still exist. Pods that kubelets are running but the API no longer knows about will be garbage-collected by kubelets or deleted; volumes can be orphaned or bound to the wrong claim. Resources deleted *since* the snapshot reappear and may be re-created in the real world.
- Controllers **reconcile toward the restored desired state**, which can mean destroying things that existed after the snapshot. Pause automation that creates or deletes cloud resources (Cluster API, cloud controllers, GitOps pruning) before bringing the control plane back, then resume deliberately with a diff review.
- Secrets in etcd may be encrypted at rest; **the encryption key is part of the backup**. Without it the snapshot is unreadable.
- Snapshot **age is your RPO** for cluster state. Hourly snapshots mean up to an hour of lost objects.

### Post-restore reconciliation checklist

```text
1. Freeze: pause GitOps pruning, autoscalers, cloud/volume controllers, CI deploys
2. Verify the control plane: readyz, controllers, leader elections, node registrations
3. Diff the world against the restored API: nodes, volumes, load balancers, DNS records
4. Reconcile orphans: bind or release volumes; remove duplicates; recreate objects created after the snapshot from Git
5. Re-issue short-lived credentials and tokens if the snapshot predates rotations
6. Resume automation one controller at a time, watching for unexpected deletions
7. Verify tenants: workload health, data consistency, a customer-view check
8. Record the data window lost and the discrepancies found
```

### Rebuild versus restore

| Question | Favours rebuild from definitions | Favours etcd restore |
| --- | --- | --- |
| Is desired state fully in Git, with data external? | Yes | No |
| Is there runtime state not reproducible (generated objects, operator state, CRs without sources)? | No | Yes |
| How long is each path, as measured in drills? | Shorter | Shorter |
| Is the corruption logical (bad change), so a snapshot may carry it? | Yes | Restore to a point before the damage |
| Is the control plane managed by a provider? | Often rebuild a new cluster | Provider-defined options only |

For many platforms the primary path is **rebuild from empty infrastructure plus restore data**, with etcd restore as the second path for state that cannot be re-derived. Practise both; measure both.

## Fleet operations

### Inventory and desired state

A fleet is manageable only with an authoritative **inventory**: every cluster, its version, region, owner, tier, add-on versions, node pools, certificates' expiry and policy bundle versions. Treat clusters as declarative objects (infrastructure as code, Cluster API or a provider's equivalent) so creating, upgrading and replacing a cluster is a reviewed change, not a ceremony. Measure **drift**: any cluster whose observed state differs from the declared one, including manual changes.

### Cells, tiers and rings

| Concept | Purpose |
| --- | --- |
| **Cell** | An independent cluster (or small set) with its own control plane, add-on instances and data plane; failure and change stay inside it |
| **Tier** | Classification of clusters by criticality and change risk (internal, staging, low-risk production, high-risk production) |
| **Ring** | An ordered wave in a rollout: ring 0 is the platform team's own clusters, ring 1 internal tenants, ring 2 low-risk production, ring 3 critical production |

A change travels ring by ring, with a **bake time** and automated health gates between rings, so that a defect is found on clusters where it does little harm.

### Fleet upgrade programme

```text
Plan:     target version selected; add-on matrix and deprecation scan done fleet-wide
Ring 0:   platform's own clusters + soak (days)
Ring 1:   internal workloads; collect tenant feedback
Ring 2:   a subset of production cells in different regions, never all of one region
Ring 3:   remaining production, high-risk tenants last
Gates:    SLO burn, scheduling latency, API error rate, node-ready percentage, pending Pods, tenant alerts
Controls: pause switch, per-ring concurrency limit, maintenance windows, exclusion list for tenants in freeze
Close:    inventory updated; stragglers tracked with owners and an end date
```

Automate the routine path and keep **humans for exceptions**. Track stragglers: clusters that remain on old versions become the next incident, since the support window ends for them on a date you can compute.

### Configuration and policy at fleet scale

Policy bundles, admission configuration, RBAC baselines and add-on values are fleet-wide *software*. Version them, review them, test them against a representative cluster (including conformance and deny tests), and deliver them through the same rings as binaries. A policy change that denies something previously allowed is a **breaking change**; roll it out in audit/warn mode first, observe violations, communicate, then enforce.

## Rollout safety

The mechanisms that keep a change from becoming an outage:

| Mechanism | Protects against | Caveat |
| --- | --- | --- |
| Server-side dry-run and diff before apply | Syntax and admission failures | Does not predict runtime behaviour |
| `maxUnavailable`, `maxSurge`, `minReadySeconds` | A bad version replacing everything | Needs honest readiness probes |
| Readiness and startup probes that reflect dependencies | Traffic to an unready Pod | Too-strict probes cascade (all Pods unready at once) |
| PodDisruptionBudgets | Voluntary disruption by drains | Do not protect from crashes; can block upgrades if mis-sized |
| Canary or progressive delivery with automated analysis | A defect reaching everyone | Needs good metrics and a gate that is trusted |
| Pause and resume (`kubectl rollout pause`) | Mid-flight inspection | Manual; has to be used in time |
| Topology spread and anti-affinity | A single node or zone taking all replicas | Needs capacity to honour |
| Feature flags decoupled from deploys | Coupling code release to exposure | Flags themselves need hygiene |
| Change freezes and windows | Compounding changes | Do not prevent bugs, only reduce overlap |
| Kill switches for fleet-wide controllers | Runaway automation | Must be tested and reachable during an outage |

For **platform changes** (CNI, ingress, policy engine, node image, kernel parameters), the same discipline applies with higher stakes:

- **Canary node pool.** Introduce the new node image or kubelet version on a small pool with taints; move a few tolerant workloads; observe; then widen.
- **Surge and drain pacing.** Drain nodes in batches sized by what the PDBs and headroom allow, not by the clock.
- **Automated rollback criteria.** Define in advance the metric thresholds at which the pipeline stops or reverses.
- **The "last working version" is an asset.** Keep the previous node image, chart versions and add-on images pinned and pullable.

A rollout gate should consume **customer-facing and platform SLIs**, not just "Pods Ready": error rate, latency, saturation, scheduling latency, node-ready percentage, API error rate.

```yaml
# illustrative progressive-delivery gate for a platform add-on
gate:
  bake: 30m
  require:
    - metric: apiserver_error_ratio_5m      # platform
      lessThan: 0.01
    - metric: pods_pending_over_5m
      lessThan: 20
    - metric: tenant_slo_burn_rate_1h       # customer view
      lessThan: 2
  onFailure: pause-and-page
```

## Upgrade strategies in depth

In-place rolling (control plane then node pools with surge), blue/green clusters, and canary node pools. Considerations: version skew, add-on compatibility, workload disruption budgets, long-running Jobs, stateful workloads and storage drivers, API removals, custom resource conversions, and rollback realism (control-plane upgrades are generally not reversible; plan forward fixes and restore paths).

| Strategy | Strengths | Weaknesses | Use when |
| --- | --- | --- | --- |
| In-place rolling | No duplicate capacity; fast; incremental | Control plane not reversible; long window | Mature platform, rehearsed pipeline |
| Canary node pool | Early signal; reversible at node level | Control-plane risk remains | Node image or kubelet changes |
| Blue/green cluster | Near-instant rollback; clean state | Duplicate cost; data and DNS complexity; drift between blue and green | High-risk upgrades; add-on overhauls; regulated workloads |
| Replace-on-schedule (immutable clusters) | No long-lived drift; upgrade equals rebuild | Needs complete automation and externalised state | Large fleets with strong IaC |

A CRD **storage version** migration or API conversion webhook upgrade deserves its own pre-flight: check that stored objects can be read at the new version, that conversion webhooks are available during the upgrade, and that you can still read after rollback of the *controller*, even if the cluster cannot roll back.

## Reliability programmes

Individual incidents are fixed; **programmes** change the rate and the severity of future incidents.

### Define platform SLOs

Platform reliability should be expressed as service levels *for its users*, the developers and their workloads.

| SLI | Example objective |
| --- | --- |
| API availability (successful requests to the API server) | 99.9% monthly |
| Scheduling latency (time from Pod creation to running, excluding image pull) | 99% within 30 s |
| Node provisioning time | 95% within 5 min |
| Deployment success (rollouts completed without manual intervention) | 98% |
| Cluster upgrade completion within the support window | 100% of clusters |
| Restore drill success and time | Meets stated RTO in the last quarter |

Each SLO has an **error budget**. Burn-rate alerts (fast and slow windows) replace noisy threshold alerts; when the budget is spent, reliability work takes priority over feature work, and that policy is agreed *before* it is needed.

### The incident learning loop

```text
Incident -> blameless review -> contributing factors -> actions (owner, date, priority)
   -> tracked to closure -> verified by an exercise -> reflected in playbooks/alerts/design
```

Measure the loop, not just the incidents: time to detect, time to mitigate, proportion detected by alerts versus customers, action closure rate, repeat incidents by mechanism, and the share of incidents whose playbook existed and worked. **Be careful with MTTR as a target**; it is a heavy-tailed measure that is gamed easily. Use distributions and trends, and read the long incidents individually.

### Toil, risk and readiness

| Mechanism | Purpose |
| --- | --- |
| Toil budget | Cap repetitive manual work (for example under half of on-call engineering time); automate the top item each quarter |
| Risk register | Known systemic risks with owner, likelihood, impact, mitigation date: an honest list, reviewed monthly |
| Operational readiness review | Before a tenant or add-on goes to production: SLOs, alerts, runbooks, capacity, backup and restore evidence |
| Production exercise calendar | Game days, restore drills, CA rotation rehearsal, region failover, each with owner and last-done date |
| Dependency review | Shared services mapped; each has a failure plan |
| Chaos and fault injection | Verify defences continually, with abort criteria and bounded blast radius |

### Reliability maturity, without vanity

A useful self-assessment asks questions that have evidence-backed answers: When did we last restore etcd or rebuild a cluster from empty infrastructure, and how long did it take? What would happen if our identity provider were down for six hours? Which cluster is furthest behind on versions and what is its support end date? What changed in the last three incidents that no alert saw? A programme that cannot answer these is not mature, whatever its dashboards say.

## Disaster recovery design

Define scenarios and the recovery you commit to: workload loss, namespace deletion, node pool loss, zone loss, control-plane loss, account compromise, region loss, provider outage, data corruption. Map each to procedures, dependencies, RTO and RPO, and test frequency. Keep recovery tooling and credentials outside the failed domain (a runbook stored only inside the broken cluster is useless). Practise full rebuilds from empty infrastructure and measure honestly, including human delays.

| Scenario | Recovery path | Dependencies that must survive | RTO / RPO (example, to be measured) | Test cadence |
| --- | --- | --- | --- | --- |
| Namespace deleted | Re-apply from Git; restore data | Git, backup store | Minutes / backup interval | Monthly |
| Node pool lost | Replace pool; reschedule | Cloud API, images | Tens of minutes / none for stateless | Quarterly |
| Zone lost | Rely on spread and headroom | Multi-zone data, headroom | Minutes / replication lag | Twice yearly |
| Control plane lost | Rebuild or restore; reconcile | etcd backups, PKI, encryption keys | Hour(s) / snapshot age | Twice yearly |
| Cluster compromised | Isolate; rebuild clean; rotate trust | Out-of-band access, clean images, secret manager | Hours / backup age | Annually (tabletop plus rebuild) |
| Region lost | Fail over to standby region | Replicated data, DNS control, capacity | Policy-defined | Annually |
| Registry lost | Failover to mirror; rebuild | Mirrored critical images | Hour(s) | Annually |
| Data corruption | Point-in-time restore to isolated target; selective repair | Continuous archive, verified backups | Policy-defined | Quarterly |

The numbers in such a table are targets until a drill has measured them.

## Platform-wide incident response

Some incidents are of the platform itself: the thing that normally *enables* response is damaged. These demand extra structure.

### Characteristics

- **Multi-tenant impact** and the communications load that follows: hundreds of teams ask at once.
- **Tooling dependence**: the CI system, chat, wiki and the cluster that hosts them may be affected, so response channels must be independent.
- **Access dependence**: identity provider, VPN, bastion, single sign-on and certificates may be part of the failure; break-glass identities and out-of-band consoles must exist and be tested.
- **Recovery dependence**: restoring the platform requires the platform's own automation, so a bootstrap path (how to build the first cluster without the platform) must be documented.

### Command structure for a platform incident

| Role | Added expectations |
| --- | --- |
| Incident commander | Decides platform-wide actions (freeze deployments, shed load, declare tenant-impacting maintenance) |
| Tenant liaison | Single channel and status page for product teams; triage of tenant reports; collects "what is broken for you" |
| Platform responders by area | Control plane, networking, storage, identity, add-ons; each reports to the commander |
| Security liaison | Joins when compromise is possible; owns evidence preservation and containment decisions |
| Scribe and a second scribe | Timeline of platform actions *and* of tenant-visible impact |

### Scenario types and first moves

| Scenario | Containment and first moves | Hazards |
| --- | --- | --- |
| **Bad fleet-wide change** (policy, controller, CNI, node image) | Stop the pipeline; pause rings; revert at the source; verify per ring | Reverting in the wrong order; rollbacks that need the broken component |
| **Credential or CA compromise** | Revoke and rotate; isolate affected clusters; preserve audit logs and node images before rebuilding | Rotation breaking all nodes at once; destroying evidence by rebuilding too soon |
| **Control-plane outage** | Protect etcd; bring back instances one at a time; throttle clients | Thundering herd; blind restore that rewinds state |
| **Identity-provider outage** | Break-glass access to clusters; maintain automation using existing tokens where safe | Break-glass abuse; stale tokens expiring mid-incident |
| **Registry or DNS outage** | Switch to mirrors; scale caches; avoid unnecessary Pod restarts that need pulls or lookups | Restarts triggering mass image pulls |
| **Region loss** | Fail over per tested runbook; hold deployments; communicate data-loss window honestly | Split brain; capacity shortfall in the surviving region |

### Containment versus restoration

Compromise-type incidents pull in two directions: restore service quickly, and stop an adversary while preserving evidence. The commander and security liaison decide together, **in writing**, what is preserved (audit logs, snapshots of affected nodes, etcd copy, registry logs) before anything is rebuilt, and what trust is considered burned (secrets, service-account tokens, kubeconfigs, image signing keys). Rebuilding from known-good definitions onto clean infrastructure, with all credentials re-issued, is usually safer than trying to clean a possibly modified cluster.

### Communication at scale

Use a single status page and a regular cadence. Distinguish *platform status* from *your workload status*. Publish what is protected (data, deployments paused) and what tenants should *not* do (mass restarts, scaling up, retrying aggressively), since tenant retries can prolong the incident. After resolution, publish a review that names the mechanism, the actions and the dates.

## Failure catalogue

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Drain deadlock | PDB cannot be satisfied | Budget review in CI; replicas ≥ budget needs |
| Upgrade breaks workloads | Removed API or add-on incompatibility | Deprecation scanning, staging upgrade, canary pool |
| Restore with orphaned resources | etcd older than real world | Documented reconciliation steps; avoid unless necessary |
| Certificate expiry | Control-plane or webhook certificate lapses | Monitoring, automated rotation, rehearsal |
| Capacity cliff | No headroom after losing a zone | N+1 planning; autoscaler limits; priority classes |
| Backup never tested | Corrupt or incomplete snapshot | Scheduled restore tests with verification queries |
| Runbook rot | Procedures not exercised | Game days; annual cold read by a new engineer |
| etcd quota breach | Unbounded object growth | Size alerting; compaction and defrag routine; object caps |
| Webhook deadlock | `Fail` policy covering its own namespace | Exclusions; high availability; emergency removal procedure |
| Thundering herd | Mass reconnect after outage | Back-off, priority levels, staged recovery |
| Fleet-wide bad change | Policy or controller pushed to all clusters | Rings, bake times, gates, kill switch |
| Shared-dependency outage | Registry, DNS, IdP or CA failure | Dependency map, mirrors, break-glass, independent copies |
| Encryption key lost | Snapshot unreadable | Key escrow as part of backup design |

## Human factors

On-call load, clear escalation paths, authority to roll back, alert quality and fatigue, access that works during outages (break-glass identities that do not depend on the failing system), and knowledge sharing through drills. Many large incidents are failures of coordination, not of technology.

Additional points that matter at scale:

- **Authority to act.** The on-call engineer must be able to pause a fleet rollout or declare an incident without seeking permission; pre-delegate it and say so in writing.
- **Sustainable on-call.** Follow-the-sun or well-staffed rotations, compensated, with limits on pages per shift. A team that burns out loses the knowledge that makes recovery fast.
- **Alert quality.** Page on symptoms customers feel and on burn rates; ticket the rest. Track pages per shift and the fraction that were actionable.
- **Deliberate practice for rare events.** Rare large incidents are where skill matters and where experience is thinnest; exercises substitute for the experience that real outages would otherwise supply.
- **Psychological safety.** People report near-misses and say "I do not understand this" only where it is safe to do so. Blameless reviews are an operational control, not a courtesy.
- **Cognitive load under stress.** Checklists, pre-written commands with safe defaults, and explicit "stop and confirm" points for irreversible actions reduce error.
- **Handover quality.** Long incidents need structured handovers: current state, hypotheses ruled in/out, pending actions, who is doing what.

## Expert trade-offs

| Decision | Tension | A defensible stance |
| --- | --- | --- |
| Few large clusters versus many small cells | Efficiency versus blast radius | Cells for critical workloads; automation cost is the limit |
| Managed control plane versus self-managed | Operational load versus control and visibility | Managed unless a requirement forces otherwise; keep an exit plan |
| Restore etcd versus rebuild | Preserves runtime state versus clean slate | Rebuild first for GitOps-complete platforms; restore for non-derivable state |
| Strict fail-closed policy versus availability | Security versus uptime | Decide per control; document emergency exceptions with expiry |
| Fast upgrades versus long soak | Security patches versus risk | Rings and gates let both happen; shorten the path for security fixes |
| Heavy automation versus operator understanding | Scale versus competence | Automate, but exercise manual paths and keep them working |
| Centralised platform versus federated ownership | Consistency versus speed | Central guardrails and tooling; federated tenant operation with clear interfaces |

## Knowledge consolidation

- At scale, failures are correlated through shared dependencies; amplification and metastability turn recoveries into new outages.
- A running workload does not need the control plane, but nothing heals or scales without it; design for the realistic control-plane gap.
- etcd is the durable state: watch fsync latency, size against quota, leader stability; respond to a quota breach with find, compact, defragment, disarm.
- Choose the recovery procedure by the kind of loss; restoring a snapshot rewinds the whole cluster and creates orphans, so pause automation and reconcile deliberately.
- The encryption key and the PKI are part of the backup.
- Fleet operation rests on inventory, declarative clusters, cells, tiers and rings with gates and bake times.
- Rollout safety is layered: dry-run, surge limits, honest probes, budgets, canaries, kill switches, and gates fed by customer-facing signals.
- Reliability programmes use platform SLOs, error budgets, a learning loop with tracked actions, toil and risk management, and exercise calendars.
- Platform-wide incidents damage the tools of response; independent channels, break-glass access and a bootstrap path are prerequisites.
- Containment and evidence preservation must be decided together with restoration when compromise is possible.

## Exercises

**Exercise 1 — Dependency map.** For a fleet you know (or a fictional one with three regions), map the shared dependencies: registry, DNS, identity provider, CA, configuration repository, CI, cloud API. For each, write what fails and what keeps working if it is down for four hours.

**Exercise 2 — etcd quota drill.** On a lab cluster with a deliberately small etcd quota, create objects until the `NOSPACE` alarm fires. Record the symptoms at the API, then compact, defragment each member in turn and clear the alarm. Write the monitoring rule that would have warned you.

**Exercise 3 — Restore with time travel.** On a lab cluster, take a snapshot, create a Deployment, a Secret and a PVC, then restore the snapshot into a rebuilt control plane. List every discrepancy between the API and the real world, and write the reconciliation steps you needed.

**Exercise 4 — Rebuild versus restore.** Measure both for the same lab cluster: rebuild from empty infrastructure plus Git plus data restore, versus etcd restore. Record human waiting time separately, compare, and state when you would choose each.

**Exercise 5 — Fleet upgrade design.** Design a ring plan for 40 clusters across four regions: ring membership, bake times, health gates, concurrency limits, pause switch, and a policy for clusters whose tenants are in a freeze. State how the plan changes for an urgent security patch.

**Exercise 6 — Herd.** In a lab, restart the API server of a cluster running many controllers and nodes while recording request rate, latency and 429s. Add jitter/back-off or priority-level changes and compare.

**Exercise 7 — Platform incident tabletop.** Run a 90-minute tabletop: "a policy update delivered to all rings blocks Pod creation; the wiki and CI run on the same platform; the identity provider is slow." Define roles, independent channels, break-glass use, first containment moves and the review. List which assumptions turned out to be false.

**Exercise 8 — Programme proposal.** Draft a one-page reliability programme for a platform team: three SLOs, an error-budget policy, a quarterly exercise calendar, and the top three risks with owners and dates.

**Solution notes.**

*Exercise 1.* Typical hidden single points: a shared configuration repository whose outage stops every ring; an identity provider needed for human logins and for automation tokens; a registry needed for any Pod start; one DNS zone for all clusters. A good map ends with mitigations (mirrors, cached credentials, break-glass access) and an honest list of what remains unprotected.

*Exercise 2.* Expect writes to fail with a "database space exceeded" style error while reads continue. Recovery is compaction, then defragmentation one member at a time (each pauses while running), then alarm disarm. The monitoring rule should alert on database size as a percentage of quota, well before the limit, and on growth rate.

*Exercise 3.* Typical discrepancies: the Deployment and Secret are absent from the API; the PVC is absent while the real volume still exists and is unbound or orphaned; running containers for the lost Deployment are terminated by kubelets. Reconciliation: recreate objects from Git, re-bind or reattach volumes explicitly, and verify nothing pruned or deleted cloud resources in the meantime.

*Exercise 4.* Rebuild commonly takes longer than people assume because of image pulls, certificate issuance and add-on ordering, while etcd restore can be fast but leaves reconciliation work. Your measurements, not these generalisations, decide. Write down the human decision points; they usually dominate.

*Exercise 5.* A strong plan keeps ring 0 under the platform team's control, never upgrades all clusters of one region in the same wave, uses gates on both platform and tenant SLIs, and allows a compressed path for security patches by shortening bake time but never removing gates or rings.

*Exercise 6.* With defaults, expect a burst of 429s and elevated latency as clients relist. Priority-level protection for node heartbeats and leader election, staggered restarts and client jitter should flatten the peak. Compare the peak request rate and time to steady state.

*Exercise 7.* Typical false assumptions: that the wiki and chat are independent of the platform; that break-glass credentials were recently tested; that the commander can reach the pipeline kill switch; that tenants will wait for updates rather than retry aggressively.

*Exercise 8.* A credible proposal has measurable SLOs with budgets, a stated policy for what happens when a budget is spent, exercises with dates and owners, and risks that are specific ("registry has no mirror") rather than generic.

## Mentoring prompts

- Your cluster's only copy of recovery documentation is in a wiki hosted on that cluster — what is your plan?
- Explain precisely why restoring an etcd snapshot can be more dangerous than rebuilding from Git.
- How would you decide whether to upgrade in place or rebuild?
- A new platform engineer asks why you will not let the fleet upgrade all regions in one weekend "since the staging cluster was fine". What evidence would you show them, and what would change your mind?
- Your SLO dashboard is green, yet tenants say the platform is unreliable. Where do you look first, and what does the disagreement tell you about the SLIs?
- During a compromise investigation, the business demands service back within the hour. How do you negotiate containment, evidence and restoration together?
