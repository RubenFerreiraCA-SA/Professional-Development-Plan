# T-DEV-05-E — Expert Depth

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-e"></a>
#### T-DEV-05-E — Expert Depth

**Reconciliation theory.** A reconciler is a control loop: observe, diff, act, repeat. Its guarantees are eventual, not transactional. Consequences: ordering across objects needs explicit dependencies (`dependsOn`, health checks, sync waves); failures are retried, so actions must be idempotent; a controller with too little visibility will thrash against another controller managing the same field (field-ownership conflicts); and "Ready" means whatever the health checks define, so weak checks yield false confidence.

**Trust boundary design.** The strongest property of pull-based delivery is that production credentials stay inside the environment. Preserve it: do not let CI hold cluster-admin; make promotion a Git write with review; use read-only credentials for sources; scope tenant reconcilers to their namespaces; and protect the desired-state repository more strictly than application code, because merging there is deploying.

**Multi-tenancy and scale.** Typical designs give each tenant a namespace, quota, network policy and a reconciler service account restricted to that namespace. Platform-owned objects (policies, cluster add-ons) live in a separate tree with a separate owner. Beware of cluster-scoped resources slipping into tenant paths; admission policy or controller configuration should reject them.

**Promotion and environment topology.** Options include branch-per-environment, directory-per-environment and repository-per-environment. Directory-per-environment on one branch makes the diff between environments reviewable and avoids merge drift; branches invite divergence. Image-update automation can open pull requests that bump digests; keep review and tests in the loop. Promotion should be monotonic and verifiable: the same digest, with evidence of source and build.

**Disaster recovery.** Distinguish recovery levels and claim only what you proved: *workload* (application serving), *cluster configuration* (access control, policy and quotas restored), *GitOps* (controller installed, sources reachable, everything reconciled with no hand-applied objects) and *platform* (tenant provisioning works again). Rehearse by rebuilding a cluster from Git and time it. Identify what Git cannot restore: data, secrets, identities issued by a certificate authority that died with the cluster, and registry contents.

**Failure catalogue**

| Failure | Mechanism | Mitigation |
| --- | --- | --- |
| Prune deletes the wrong thing | Ownership overlap | Ownership lists, prune exclusions, review of removals |
| Flapping | Two writers for one field | Single owner, server-side apply field management |
| Stuck reconciliation | Failed health check, bad dependency | Timeouts, alerts on not-Ready duration |
| Silent success | Health check too weak | Application-level readiness, post-deploy verification |
| Credential sprawl | Many deploy keys | Central identity, rotation, minimal scope |
| Rollback ineffective | Data migration, external side effects | Expand/contract, feature flags |

**Progressive delivery in depth.** Canary analysis compares a baseline and a canary using metrics (error ratio, latency percentiles) and aborts automatically on regression. It needs trustworthy telemetry (see T-DEV-06), traffic shaping and a rollback that is cheaper than the failure. Without those, a canary is just a slow rollout.

**Mentoring prompts.** Why is "Git is the source of truth" false during an incident, and how do you restore it afterwards? Which of your controls would still protect production if the desired-state repository's maintainer account were compromised? How would you design the exception process for suspending reconciliation?

---
