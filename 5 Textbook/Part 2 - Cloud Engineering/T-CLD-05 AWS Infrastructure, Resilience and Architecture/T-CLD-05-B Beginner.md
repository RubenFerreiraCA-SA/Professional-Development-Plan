# T-CLD-05-B — Beginner Foundations

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-b"></a>
#### T-CLD-05-B — Beginner Foundations

**Failure is normal.** Instances stop, zones lose power, deployments go wrong, disks fill. Architecture is deciding in advance what happens.

**Basic vocabulary**

| Term | Meaning |
| --- | --- |
| Availability | Fraction of time a service works |
| Resilience | Ability to continue or recover when components fail |
| High availability (HA) | Designing so a single failure does not cause an outage |
| RTO | Recovery time objective: how long recovery may take |
| RPO | Recovery point objective: how much data loss is acceptable |
| Stateless | Holds no data that must survive a restart |
| Stateful | Holds data that must be preserved |

**A simple architecture.** Users reach a load balancer in two AZs. The load balancer forwards to a container service that runs a number of identical tasks. A scheduler replaces failed tasks. A managed database (if needed) lives behind the service. Logs go to a central service.

**The self-healing test.** The simplest drill is to stop a running task and watch the scheduler start a replacement while the load balancer routes around the gap. With one task, there will be a short outage — which teaches why one instance is not high availability.

```bash
aws ecs list-tasks --cluster orders --service-name orders-api
aws ecs stop-task --cluster orders --task <task-arn> --reason "resilience drill"
while true; do curl -s -o /dev/null -w '%{http_code}\n' https://orders.example.com/health; sleep 2; done
```

**Honest wording.** "ECS replaced the task in about 40 seconds with `desired_count` 1" is a true statement. "The system is highly available" is not.

**Worked example: what each design tolerates.** Suppose `orders-api` runs behind a load balancer across two AZs.

| Design | One task stops | One AZ is lost | Database host fails | A bad release goes out |
| --- | --- | --- | --- | --- |
| 1 task, 1 AZ, single-instance database | Outage until the scheduler starts a replacement (tens of seconds to minutes) | Full outage until recovery | Outage; data restored to the last backup (RPO applies) | Outage until rollback |
| 2 tasks across 2 AZs, single-instance database | No visible outage; the load balancer routes around the gap | Half capacity; service continues | Outage until recovery or restore | Both tasks run the bad code unless a rollout is gradual |
| 2 tasks across 2 AZs, database with a standby in another AZ | No visible outage | Continues after a brief database failover | Short interruption during failover | Needs rollout controls; replication does not protect against bad releases |

Each added component protects against a specific failure and nothing else. Replication does not protect against deleting rows; two tasks do not protect against shipping a bug.

**Stateless and stateful, and why it matters.** A stateless task can be killed at any moment because nothing it holds is unique; a replacement is identical. State (orders, uploads, sessions) must live somewhere durable: the managed database, object storage or a shared cache. The practical rule: keep tasks stateless and concentrate the effort of resilience on the few stateful components.

**RTO and RPO with a number attached.** For `orders-api`: RTO of 30 minutes means the service must be back within half an hour of a major failure; RPO of 5 minutes means losing at most five minutes of orders is acceptable. Those two numbers drive spending. A 5-minute RPO needs frequent backups or replication; a 24-hour RPO is satisfied by a nightly snapshot. Availability is stated as a percentage, but it is more intuitive as downtime per month:

| Availability | Downtime per 30 days |
| --- | --- |
| 99% | about 7 hours 12 minutes |
| 99.9% | about 43 minutes |
| 99.99% | about 4 minutes 19 seconds |

**The three desired-count cases.**

```bash
aws ecs describe-services --cluster orders --services orders-api \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'
aws ecs update-service --cluster orders --service orders-api --desired-count 2
aws elbv2 describe-target-health --target-group-arn <arn>
```

With `desired_count` 1, stopping the task gives a gap during which the load balancer has no healthy target, so users see 5xx errors. With 2, one target remains healthy and users are served throughout. Record what you observed, with timestamps, rather than what you expected.

**Common mistakes**

- Calling a deployment "highly available" because it uses a managed service. Ask which failures were actually tested.
- Placing both tasks in the same AZ, which gives two copies but one failure domain.
- Storing uploaded files on a task's local disk, then losing them on replacement.
- Having backups but never restoring one. An untested backup is a hope.

**Label this diagram.** Draw users, load balancer, two AZs with a task in each, scheduler, database and log service. Colour stateless boxes one way and stateful boxes another, and write the failure each box protects against.

**Exercise.** List three things that could fail in your architecture diagram and write what the user would experience for each.
