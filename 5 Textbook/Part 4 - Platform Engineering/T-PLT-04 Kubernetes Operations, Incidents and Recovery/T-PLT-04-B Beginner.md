# T-PLT-04-B — Beginner Foundations

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-b"></a>
#### T-PLT-04-B — Beginner Foundations

**What "day two" means.** Day zero is design, day one is the first deployment, and **day two is everything afterwards**: access changes, capacity limits, incidents, patching, upgrades, backups and handover. Platform teams are judged here.

| Concern | The question a runbook must answer |
| --- | --- |
| Access | Who can change what, and how do I revoke it? |
| Fairness and capacity | What stops one namespace consuming the cluster? |
| Safety rails | What stops an unsafe workload being admitted? |
| Incidents | How do I get from symptom to cause quickly? |
| Maintenance | How do I take a node out without an outage? |
| Recovery | What do I restore, from where, in what order, how long? |
| Change | How do I move to the next Kubernetes version? |

**A triage ladder (read-only first).**

```bash
kubectl get pods -n <ns> -o wide
kubectl describe pod <pod> -n <ns>              # events at the bottom
kubectl logs <pod> -n <ns> --previous           # logs from the crashed instance
kubectl get events -n <ns> --sort-by=.lastTimestamp
kubectl get endpointslices -n <ns>
kubectl top pods -n <ns>
kubectl rollout status deployment/<name> -n <ns>
```

Work from the outside in: is it running, is it ready, does the Service have endpoints, does DNS resolve, is policy blocking, are resources exhausted?

**Reading statuses**

| Status | Usually means |
| --- | --- |
| Pending | Not scheduled: resources, taints, volume binding |
| ContainerCreating (long) | Image pull or volume mount trouble |
| ImagePullBackOff | Image or credentials problem |
| CrashLoopBackOff | The process keeps exiting |
| Running but 0/1 Ready | Readiness probe failing |
| Terminating (stuck) | Finalizer, node unreachable, or ungraceful shutdown |

**Maintenance vocabulary**

| Action | Effect |
| --- | --- |
| `cordon` | Mark a node unschedulable; existing Pods stay |
| `drain` | Cordon, then evict Pods via the Eviction API (honours disruption budgets) |
| `delete pod` | Direct deletion (does not honour budgets) |

**Recovery sources, at a glance.**

| Layer | Recovery source |
| --- | --- |
| Workload definitions | Git |
| Cluster policies and access rules | Git |
| Cluster state (etcd) | Snapshot or provider backup |
| Persistent data | Application-level backup, snapshots, managed database |
| Secrets | Secret manager |
| Images | Registry |

**Exercise.** Deploy a service, break it three different ways (bad image digest, bad readiness path, memory limit too low) and write down the status and the evidence line for each.
