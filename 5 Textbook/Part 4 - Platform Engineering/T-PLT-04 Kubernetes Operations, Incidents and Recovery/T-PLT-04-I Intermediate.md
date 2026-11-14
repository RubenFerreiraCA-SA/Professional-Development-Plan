# T-PLT-04-I — Intermediate Practice

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-i"></a>
#### T-PLT-04-I — Intermediate Practice

**A fault catalogue to practise on**

| Fault | Injection | Symptom | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Bad digest | Image `@sha256:000…` | `ImagePullBackOff`; rollout stalls; old Pods keep serving | `describe pod` events | Revert the commit |
| Bad readiness path | Probe `/nope` | `0/1 Ready`, no restarts, rollout stalls | `describe`, EndpointSlice | Revert |
| Memory limit too low | `limits.memory: 16Mi` | `OOMKilled`, `CrashLoopBackOff` | `describe` last state | Raise with evidence |
| Quota exhausted | Lower the CPU quota, restart | New Pods never created | `describe rs`, `exceeded quota` events | Fix the quota or right-size |
| Selector drift | Change the Service selector | Service has no endpoints, Pods healthy | `get endpointslices` | Revert |
| NetworkPolicy gap | Remove the DNS allow | Name-resolution timeouts, Pods Ready | DNS test from a Pod | Restore the policy |
| Admission denial | Tagged image via Git | Sync error; no new ReplicaSet | Controller status, API error | Use a digest |

Run the *blind drill*: someone else injects a fault from this table; you diagnose using only the ladder and write a short incident note.

**Ephemeral debugging.** When the image has no shell: `kubectl debug -it <pod> --image=busybox --target=<container>`. It needs RBAC for `pods/ephemeralcontainers` (deliberately not in a developer role) and, under restricted Pod Security, the debug container itself must satisfy the policy.

**Node operations.**

```bash
kubectl cordon worker-2
kubectl drain worker-2 --ignore-daemonsets --delete-emptydir-data --timeout=120s
# ... maintenance ...
kubectl uncordon worker-2
```

Run a drain while a client loop measures availability. A PodDisruptionBudget that cannot be satisfied (for example `minAvailable: 1` with one replica) makes the drain fail with `Cannot evict pod as it would violate the pod's disruption budget`: the budget is doing its job, and a mis-sized one freezes every future upgrade.

**Node failure is not a drain.** On abrupt node loss, Pods remain until taint-based eviction (about five minutes by default) and PDBs do not apply. Observe, record the time to reschedule, and compare with your recovery target.

**Rebuild a namespace from Git with a stopwatch.** Delete the namespace and restore from a single entry point that includes the guardrails (namespace, quota, policies) *before* workloads:

```bash
kubectl delete namespace orders-staging
time kubectl apply -k deploy/platform/staging
kubectl -n orders-staging rollout status deployment/orders-api
```

Order matters on a fresh cluster: namespace → quota and limits → workload.

**etcd snapshot (awareness).** On a cluster you control: `etcdctl snapshot save snapshot.db` with appropriate certificates, then `etcdutl snapshot status`. Restores are delicate — they roll the whole cluster state back. On managed services the provider owns this; know their guarantees.

**Exercise.** Run the node drain with a failing PDB, fix the PDB, repeat successfully and record the client-visible impact.
