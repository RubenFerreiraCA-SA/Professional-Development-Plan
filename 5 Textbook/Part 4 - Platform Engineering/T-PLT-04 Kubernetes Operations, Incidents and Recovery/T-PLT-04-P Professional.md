# T-PLT-04-P — Professional Engineering

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-p"></a>
#### T-PLT-04-P — Professional Engineering

**Recovery levels — claim only what you proved**

| Level | What must work after a rebuild | Evidence |
| --- | --- | --- |
| Workload | Application Ready and serving | Deployment Available; client probe |
| Cluster configuration | Access control, admission, quotas and network policy restored | Access tests, policy denials |
| GitOps | Controller installed, sources reachable, everything reconciled, no hand-applied objects | `flux check`; all Kustomizations Ready |
| Platform | Tenant provisioning and the golden path work again | A new service is created end to end |

Do not call a manual `kubectl apply -k` of the app "GitOps recovered".

**Backup and restore design.**

| Concern | Practice |
| --- | --- |
| Definitions and policy | In Git; the primary disaster-recovery path |
| Persistent data | Application-consistent backups; test restore; off-cluster copy |
| etcd | Regular snapshots, protected, restore drills (if self-managed) |
| Secrets | Recovery means reconnecting the external source, not restoring from Git |
| Identities | Re-issue after rebuild; know what died with the CA |
| Registry | Mirror or back up release images; digests need the registry |

State **RPO and RTO targets** first, then measure. A backup that lives only in the cluster dies with the cluster; keep a copy outside it. Do not delete a data volume to "fix" a database; restore through the documented procedure.

**Upgrades.**

| Rule | Detail (check the current version-skew policy) |
| --- | --- |
| One minor version at a time | Never skip minors on the control plane |
| Control plane first, then nodes | The kubelet must not be newer than the API server |
| Client skew | `kubectl` within one minor of the API server |
| Read release notes and the deprecation guide | Removed APIs break manifests when applied |
| Add-ons (network plugin, ingress, policy engine) | Have their own compatibility matrices |
| Support window | Minor versions are supported for a limited period; plan a cadence |

Pre-flight: check deprecated API usage (metrics and scanning tools), search the repository for old API versions, check chart support matrices, confirm backups and disruption budgets, upgrade a non-production cluster first. For clusters that cannot be upgraded in place, a blue/green cluster (build new, move traffic, retire old) trades cost for safety.

**The operating cadence**

| Frequency | Activity |
| --- | --- |
| Per change | Server-side dry-run, review of platform manifests |
| Weekly | RBAC audit, expired identities, quota headroom |
| Monthly | Namespace rebuild drill; image and vulnerability re-scan |
| Per release or quarterly | Upgrade rehearsal; review of the version-support window |
| Annually | Re-test the runbook with someone who did not write it |

**Runbook skeleton**

```markdown
# Cluster runbook
## Scope and limits   - what this covers, what it does not
## Access             - how to get in, break-glass procedure, how to revoke
## Triage             - the ladder; symptom → first check table
## Procedures         - drain, restore namespace, rotate credentials, upgrade
## Known gaps         - honest list (single node, unencrypted secrets on practice cluster, ...)
## Escalation         - who, when
```

Keep an operation record template (what changed, who approved, evidence, rollback) for every manual intervention.

**Incident management.** Roles (incident lead, communications, operators), a single channel, a timeline kept as you go, stabilise before diagnosing deeply (revert via Git, scale, drain traffic), declare resolution on evidence, and run a blameless review that produces tracked actions. Prefer fixing through Git so the record and the cluster agree.

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Take a node out | Cordon, drain with a measured client loop | Deleting Pods directly |
| Recover from a bad release | Revert desired state in Git | Live edits that Git will undo |
| Back up | Definitions in Git; data via application backups; copy off-cluster | "PVC equals backup" |
| Upgrade | Rehearse, one minor at a time, check deprecations | Skipping versions |
| Claim recovery | State the level you proved | "Disaster recovery works" without a drill |
