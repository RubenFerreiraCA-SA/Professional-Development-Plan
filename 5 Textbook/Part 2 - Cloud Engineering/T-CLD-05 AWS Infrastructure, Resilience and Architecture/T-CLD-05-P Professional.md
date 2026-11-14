# T-CLD-05-P — Professional Engineering

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-p"></a>
#### T-CLD-05-P — Professional Engineering

**Set objectives first.** Write RTO and RPO per component and justify them against business impact. For a stateless API behind a load balancer: RTO is scheduling plus start-up plus health-check time; RPO is not applicable. For a database: RPO depends on backup frequency, replication and point-in-time recovery; RTO on restore time and failover.

**Design for failure domains.** A failure domain is the set of things that fail together: instance, rack, AZ, region, account, dependency. Spread replicas across AZs; keep capacity so remaining AZs can absorb load; make health checks accurate (readiness reflects whether traffic should be sent, liveness whether to restart); and avoid cross-AZ chattiness that doubles cost and latency.

**Patterns that make recovery routine**

| Pattern | Effect |
| --- | --- |
| Stateless services with externalised state | Instances are disposable |
| Immutable deployments by digest | Rollback means redeploying a known artefact |
| Rolling or blue/green releases with health gates | A bad release stops early |
| Graceful shutdown and connection draining | Deployments and scaling do not drop requests |
| Timeouts, retries with jitter, circuit breakers | Failures do not cascade |
| Autoscaling with sane limits | Load spikes and cost are bounded |
| Backups with tested restores | Data loss is bounded |

**Data protection.** Managed databases offer automated backups, point-in-time recovery, snapshots, read replicas and multi-AZ standby; they are not interchangeable. Replicas help read scale and some failover; backups protect against deletion and corruption; neither replaces the other. Test restore into a separate environment, measure the time and compare with RTO. Protect infrastructure state with versioning and locking, and rehearse recovery.

**Recovery runbook skeleton**

```markdown
# Recovery: orders-api
## Symptoms        - which signals, which thresholds
## Immediate checks - health URL, service events, target health
## Actions         - ordered, reversible first; who may do what
## Rollback        - previous digest via code; no console edits
## Data            - what is durable, how to restore, how long it takes
## Escalation      - when and to whom
## After           - verify, record evidence, file follow-ups
```

**Cost, quotas and teardown.** Update cost guardrails after architecture changes: whether a NAT is added, load-balancer idle cost, compute count, what will be destroyed after the exercise. Quotas (service limits) can block scale-out or a recovery action; check them proactively. Keep the destroy path tested.

**Honest ADR statements.** "The load balancer spans two AZs; the application is not claimed to tolerate an AZ failure because desired count is one." "Stopping the task is recovered by the scheduler within the RTO measured at 45 seconds." State limitations explicitly.

**Decision guide**

| Question | Answer approach |
| --- | --- |
| Is it HA? | Show placement across failure domains and a test, or do not claim it |
| How fast do we recover? | Measure with a drill; compare to RTO |
| What if the deployment is bad? | Revert the artefact via code; confirm health |
| What is lost if the data store dies? | State RPO from backup evidence |
| What did we not test? | Write it in the record |
