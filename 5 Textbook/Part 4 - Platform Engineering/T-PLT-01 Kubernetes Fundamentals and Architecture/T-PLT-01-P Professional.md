# T-PLT-01-P — Professional Engineering

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-p"></a>
#### T-PLT-01-P — Professional Engineering

**Graceful termination and disruption.** When a Pod is deleted it is marked `Terminating` and removed from endpoints *in parallel* with the `preStop` hook and `SIGTERM`. Endpoint removal propagates asynchronously, so traffic can still arrive briefly after `SIGTERM`. A short `preStop` sleep gives the network time to catch up.

| Setting | Purpose | Gotcha |
| --- | --- | --- |
| `preStop` sleep | Drain window | The native sleep action needs a recent Kubernetes; otherwise use an `exec` sleep and ensure the binary exists |
| `terminationGracePeriodSeconds` | Maximum shutdown time | Too short cuts off in-flight requests |
| Application handles `SIGTERM` | Clean exit | A 30 s delete means `SIGKILL` was needed |
| PodDisruptionBudget | Limits voluntary evictions (drains, upgrades) | Does nothing for crashes or node failure |
| `topologySpreadConstraints` | Spread across nodes or zones | `ScheduleAnyway` is a preference; `DoNotSchedule` can leave Pods Pending |

A PodDisruptionBudget with `minAvailable: 1` on a single replica blocks every drain; size budgets against replicas.

**Resource policy.** Set memory limits (an OOM kill is a visible failure rather than a noisy neighbour). Many teams omit CPU limits to avoid throttling latency while keeping CPU requests accurate and enforcing quotas; whichever you choose, policy must match it (do not later mandate a CPU limit that you decided against). Size from load testing and history, not guesses.

**Secrets are not secret by default.** Anyone who can `get` the Secret, or exec into a Pod that mounts it, reads the plaintext.

- Restrict `get`, `list` and `watch` on Secrets by RBAC (`list` returns values).
- Enable encryption at rest for etcd where you control it; managed services offer it.
- Do not commit Secret manifests with values; use an external secrets operator, sealed secrets or a cloud secret manager.
- Prefer mounting as files over environment variables when the app can read files; environment variables leak into crash dumps and child processes.

**Workload kinds**

| Workload | Use when | Key properties |
| --- | --- | --- |
| Deployment | Stateless services | Interchangeable Pods |
| StatefulSet | Stable identity or storage | Ordered names, per-Pod volumes, headless Service |
| DaemonSet | One Pod per node | Log agents, network plugins, node exporters |
| Job and CronJob | Run to completion, scheduled | `backoffLimit`, `ttlSecondsAfterFinished`, `concurrencyPolicy` |

A Job can run more than once under retries, so its work must be idempotent; database migrations need a design (expand/contract), not just a Job. Persistence is not durability: a node-local volume survives Pod deletion but not node loss, and is not a backup. Run production databases on managed services unless you have the operational discipline for replication, failover, backups and upgrades.

**Ingress and Gateway.** An Ingress or Gateway routes external HTTP(S) to Services, terminating TLS and applying host and path rules. It needs a controller; choose a controller, define ownership of certificates and hostnames, and treat routing configuration as security-relevant.

**NetworkPolicy preview.** By default, Pods can talk to all Pods. A NetworkPolicy restricts traffic, but only if the network plugin enforces it (see T-PLT-03).

**Recovery claims — what you may and may not say**

| Evidence you have | Claim you may make | Claim you may not make |
| --- | --- | --- |
| Pod kill, Deployment replaces, probes show counts | "Recovers from single-Pod loss without intervention; client impact measured as X" | "Highly available" |
| Two replicas on two nodes | "Replicas are scheduled across nodes" | "Survives node or zone failure" on a single-host cluster |
| Node-stop drill | "Pods reschedule after node loss within about T seconds on this cluster" | "Production failover time" |
| PDB defined | "Voluntary disruptions are bounded" | "Crashes and node loss are bounded" |
| Node-local volume | "Data survived a Pod restart" | "Data is durable or backed up" |

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Safe rollouts | `maxUnavailable: 0`, readiness gates, `preStop` drain | Deployments without probes |
| Traffic only to healthy Pods | Accurate readiness | Liveness that depends on a database |
| Prevent noisy neighbours | Requests, memory limits, quotas | BestEffort Pods in shared clusters |
| Config changes | Roll out via Git; hash-triggered restarts | Editing live objects |
| Sensitive values | External secret manager, restricted RBAC | Plaintext Secret manifests in Git |
