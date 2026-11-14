# T-PLT-04-E — Expert Depth

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-e"></a>
#### T-PLT-04-E — Expert Depth

**Designing for failure domains in Kubernetes.** Control-plane quorum (three or five members across zones), node pools across zones, storage that is zone-aware (a volume bound to one zone pins Pods there), load balancers with cross-zone behaviour, and DNS. For each, ask: what happens on loss of one node, one zone, the control plane, the registry, the identity provider, the cloud API? A cluster is often only as available as its least redundant dependency.

**Control-plane operations.** etcd health (latency, database size, defragmentation), API server saturation (request rates, priority and fairness settings, expensive list calls), admission webhook latency, controller backlog, certificate expiry across components, and the effect of a large number of objects. Restoring etcd rewinds cluster state: nodes and controllers must reconcile with the restored view, and anything created after the snapshot (including Secrets and volume claims) is lost from the cluster's perspective while real resources may still exist. Treat restore as a last resort with a practised procedure.

**Capacity and cost.** Track requests versus usage, bin-packing efficiency, headroom for failures (N+1 by zone), autoscaler behaviour, and the cost of idle capacity. Right-size with data; use priority classes so critical workloads preempt batch; consider spot or preemptible nodes for tolerant workloads with disruption handling.

**Upgrade strategies in depth.** In-place rolling (control plane then node pools with surge), blue/green clusters, and canary node pools. Considerations: version skew, add-on compatibility, workload disruption budgets, long-running Jobs, stateful workloads and storage drivers, API removals, custom resource conversions, and rollback realism (control-plane upgrades are generally not reversible; plan forward fixes and restore paths).

**Disaster recovery design.** Define scenarios and the recovery you commit to: workload loss, namespace deletion, node pool loss, zone loss, control-plane loss, account compromise, region loss, provider outage, data corruption. Map each to procedures, dependencies, RTO and RPO, and test frequency. Keep recovery tooling and credentials outside the failed domain (a runbook stored only inside the broken cluster is useless). Practise full rebuilds from empty infrastructure and measure honestly, including human delays.

**Failure catalogue**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Drain deadlock | PDB cannot be satisfied | Budget review in CI; replicas ≥ budget needs |
| Upgrade breaks workloads | Removed API or add-on incompatibility | Deprecation scanning, staging upgrade, canary pool |
| Restore with orphaned resources | etcd older than real world | Documented reconciliation steps; avoid unless necessary |
| Certificate expiry | Control-plane or webhook certificate lapses | Monitoring, automated rotation, rehearsal |
| Capacity cliff | No headroom after losing a zone | N+1 planning; autoscaler limits; priority classes |
| Backup never tested | Corrupt or incomplete snapshot | Scheduled restore tests with verification queries |
| Runbook rot | Procedures not exercised | Game days; annual cold read by a new engineer |

**Human factors.** On-call load, clear escalation paths, authority to roll back, alert quality and fatigue, access that works during outages (break-glass identities that do not depend on the failing system), and knowledge sharing through drills. Many large incidents are failures of coordination, not of technology.

**Mentoring prompts.** Your cluster's only copy of recovery documentation is in a wiki hosted on that cluster — what is your plan? Explain precisely why restoring an etcd snapshot can be more dangerous than rebuilding from Git. How would you decide whether to upgrade in place or rebuild?

---
