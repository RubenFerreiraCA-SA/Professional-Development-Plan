# T-CLD-05-I — Intermediate Practice

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-i"></a>
#### T-CLD-05-I — Intermediate Practice

**Make an architecture decision record before building.** Cover: compute (service type, desired count, placement), network (VPC, subnets, security groups, listener scheme), data (stateless or stateful, backup and restore, RPO and RTO), edge (load-balancer AZs, health checks), observability (logs, metrics, where recovery evidence goes), cost and limits, and exactly one primary failure drill.

**Topology trade-offs**

| Choice | Training-friendly | Production-shaped | Cost or complexity |
| --- | --- | --- | --- |
| Tasks in public subnets with public IPs | Avoids NAT cost | Unusual; prefer private subnets plus NAT or endpoints | NAT is continuous spend |
| Load balancer across two AZs | Cheap enough | Required for serious HA | Hourly plus capacity units |
| Desired count of one | Cheap | Not HA: one failure means an outage until replaced | Extra tasks cost money |
| Managed database, multi-AZ | Optional | Common for durable data | Instance, storage, standby premium |
| Single AZ | Only if the record admits it | Insufficient for most production SLOs | Cheap until the AZ fails |

If your diagram says "multi-AZ HA" while `desired_count` is 1 and there is no data store, the diagram is aspirational.

**Implement through code.** Change infrastructure code, not the console. Run `plan` before `apply`, keep the plan summary as evidence, and re-read outputs afterwards. Make HA claims measurable: expose `desired_count` as a variable; at two or more, verify task placement across AZs:

```bash
aws ecs describe-tasks --cluster orders --tasks $(aws ecs list-tasks --cluster orders --query 'taskArns' --output text) \
  --query 'tasks[].[taskArn,availabilityZone,lastStatus]' --output table
```

**Drills — choose one primary and record what it proves.**

| Drill | What it proves | What it does not prove |
| --- | --- | --- |
| Stop a task | The scheduler replaces it; time to recover | Multi-instance HA when the count is one |
| Bad deployment via code, then revert | Rollback through code works without console drift | Data rollback |
| Remove a subnet from the service configuration | Sensitivity of placement configuration | An AZ outage — this is a configuration simulation, not a provider failure |
| Restore assumptions (state and backups) | Recovery path for infrastructure state or data | Application correctness |

Do not recover a code-managed resource by editing it imperatively (for example, updating a service's task definition by hand) — that creates drift.

**Observation signals.**

| Signal | Source | Use |
| --- | --- | --- |
| HTTP health | `curl` to the health URL | Pass or fail recovery |
| Service events | `describe-services` | Why tasks stopped or started |
| Target health | `describe-target-health` | Unhealthy versus draining |
| Logs | The service's log group | Application errors during a bad deployment |

**Console exceptions.** Maintain a list of anything created or changed by hand, with a follow-up date. An empty list is excellent. Unlisted manual drift is a defect.

**Exercise.** Run the stop-task drill with desired count one and two, plot the HTTP status over time and write the difference in two sentences.
