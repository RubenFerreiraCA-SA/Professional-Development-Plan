# T-CLD-05-I — Intermediate Practice

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-i"></a>
#### T-CLD-05-I — Intermediate Practice

## Why this matters

At Beginner level you learned the pieces and walked a topology on paper. At Intermediate level you build that topology through code, run a drill against it, and read the evidence honestly. The skill being trained is *routine failure analysis*: when something breaks, you can say which failure domain it belongs to, which signal shows it, and which recorded fact tells you whether the design did its job.

The service is still `orders-api`: an ECS service behind an Application Load Balancer across two AZs, with a managed database and object storage. The chapter stays neutral and self-contained.

**Conventions.** *Version-specific* marks a default, limit, timing or feature that AWS may change; verify it in current documentation. *Illustrative* marks the shape of a result, not a measurement. Angle brackets are placeholders.

## Decide before building: the architecture decision record

Make an architecture decision record (ADR) before building. A short ADR is better than an unwritten assumption, and it is the document against which drills are later judged.

```markdown
# ADR-012: orders-api topology (practice environment)

## Compute      ECS service, Fargate, desired count 2, tasks spread across AZ-a and AZ-b
## Network      One VPC; two public subnets for the load balancer, two private subnets for tasks
## Data         Managed database, Multi-AZ; daily snapshot plus point-in-time recovery
## Edge         ALB across both AZs; HTTP health check on /ready; deregistration delay 30 s
## Observe      Logs to a central log group; alarms on 5xx ratio and unhealthy host count
## Recovery     RTO 30 min; RPO 5 min (database), n/a (tasks)
## Cost/limits  NAT gateway per AZ (cost noted); task quota checked; destroy path tested
## Drill        One primary drill: stop one task; hypothesis and abort condition recorded
## Not claimed  AZ-loss tolerance (not yet drilled), multi-region, bad-release recovery
```

Cover compute (service type, desired count, placement), network (VPC, subnets, security groups, listener scheme), data (stateless or stateful, backup and restore, RPO and RTO), edge (load-balancer AZs, health checks), observability (logs, metrics, where recovery evidence goes), cost and limits, and exactly one primary failure drill. The "Not claimed" line is the most valuable: it stops the design being described more generously than the evidence allows.

## Topologies and trade-offs

| Choice | Training-friendly | Production-shaped | Cost or complexity |
| --- | --- | --- | --- |
| Tasks in public subnets with public IPs | Avoids NAT cost | Unusual; prefer private subnets plus NAT or endpoints | NAT is continuous spend |
| Load balancer across two AZs | Cheap enough | Required for serious HA | Hourly plus capacity units |
| Desired count of one | Cheap | Not HA: one failure means an outage until replaced | Extra tasks cost money |
| Managed database, multi-AZ | Optional | Common for durable data | Instance, storage, standby premium |
| Single AZ | Only if the record admits it | Insufficient for most production SLOs | Cheap until the AZ fails |

If your diagram says "multi-AZ HA" while `desired_count` is 1 and there is no data store, the diagram is aspirational.

Three topologies cover most Intermediate work:

```text
A. Single AZ, single task
   ALB(AZ-a) -> task(AZ-a) -> DB(AZ-a)
   Fails: any task, host, AZ or release problem. Use for scratch work only.

B. Two AZs, two tasks, standby database
   ALB(AZ-a,AZ-b) -> task(AZ-a), task(AZ-b) -> DB primary(AZ-a) + standby(AZ-b)
   Survives: task loss, host loss, one AZ (after DB failover), if capacity per AZ is enough.

C. Three AZs, tasks sized so any two carry peak
   ALB(a,b,c) -> tasks spread 1:1:1 or more -> DB multi-AZ
   Survives the same, with lower capacity overhead for the same peak.
```

The decision between B and C is usually capacity arithmetic. If peak needs 6 tasks, topology B needs 6 per AZ (12 total) to survive AZ loss at peak; topology C needs 3 per AZ (9 total). Real systems also weigh data-transfer cost across AZs, per-AZ minimums and the number of AZs available to the account in the region.

## Network dependencies: the invisible failure domains

A task in a private subnet depends on more than the load balancer. Draw every dependency the task touches and ask in which AZ it lives.

| Dependency | Scope | What failure looks like | Mitigation |
| --- | --- | --- | --- |
| NAT gateway | One AZ | Tasks in that AZ cannot reach the internet or public AWS endpoints; those in other AZs are unaffected | One NAT gateway per AZ, each used by its own AZ's route table; or VPC endpoints for AWS services |
| VPC endpoints (interface) | Per-AZ network interfaces | An AZ-specific endpoint fault affects clients using it | Enable the endpoint in each AZ used |
| Route tables | Per subnet association | A wrong route sends traffic nowhere | Manage in code; review plans |
| Security groups | VPC-wide rules | A removed rule drops traffic silently | Test connectivity after changes; keep rules in code |
| DNS resolution | VPC resolver | Slow or failing lookups look like application errors | Cache sensibly; alarm on lookup errors |
| Certificates | Account/region | Expiry produces a hard outage | Managed renewal and expiry alarm |
| Image registry | Region | Tasks cannot start if the image cannot be pulled | Registry endpoints reachable from private subnets; image in the same region |
| Secrets and parameter stores | Region | Start-up fails without secrets | Fetch at start with retry; do not fetch per request without caching |

One pattern repays attention. If all private subnets route outbound traffic through a *single* NAT gateway in AZ-a, then the loss of AZ-a also cuts AZ-b's tasks off from the internet and AWS public endpoints, even though AZ-b is healthy. A multi-AZ service with a single NAT gateway is a single-AZ service for outbound dependencies. Cross-AZ traffic through a shared NAT also incurs data-transfer charges, which is the other reason to have one per AZ. *Version-specific:* check current NAT gateway and data-transfer pricing before making cost claims.

A reliable habit: for each task start-up step (pull image, fetch secrets, reach the database, register with the load balancer, emit logs), name the network path it uses and test it from the private subnet.

## Load balancers and health checks

The load balancer is the system's judge of what is healthy, so the health check is a design decision, not a default.

**Three kinds of check.**

| Check | Question | Where it is used | Failure effect |
| --- | --- | --- | --- |
| Liveness | Is the process alive and not wedged? | Container or orchestrator restart decisions | The process is restarted |
| Readiness | Should this instance receive traffic now? | Load-balancer target health | The instance stops receiving traffic but keeps running |
| Deep (dependency) check | Can it complete a real request path? | Diagnostics, synthetic monitoring | Should alert people; should not by itself remove every instance |

A readiness check that fails whenever the database is slow is dangerous: every target fails at once, the load balancer has no healthy targets, and a partial degradation becomes a total outage. Where all targets are unhealthy, a load balancer typically falls back to sending traffic to all targets anyway (*Version-specific:* confirm the current fail-open behaviour for your load-balancer type), but you should not design on it.

**Settings that govern timing.**

```text
Detection time   ≈ interval × unhealthy_threshold
Recovery trust   ≈ interval × healthy_threshold
Example: interval 10 s, unhealthy 3, healthy 2
         a failed target receives traffic for up to ~30 s; a recovered one waits ~20 s
```

Other settings that matter:

- **Deregistration delay.** Time allowed for in-flight requests when a target is removed. Short requests allow a short delay, which speeds deployments.
- **Slow start.** Gradually ramps traffic to a new target so a cold task is not overwhelmed. *Version-specific:* support and ranges depend on the load-balancer type and algorithm.
- **Cross-zone load balancing.** When enabled, each load-balancer node spreads requests across targets in all enabled AZs; when disabled, each node serves only the targets in its own AZ. *Version-specific:* the default differs between ALB and NLB, and so do the data-transfer implications. Know what your type does. With it disabled and an uneven number of targets per AZ, the small AZ is overloaded.
- **Health-check grace period (ECS and ASG).** A window after start during which failing health checks do not cause termination. Too short and slow-starting tasks are killed in a loop; too long and a broken release lingers.

Check each of these in the real configuration; do not assume defaults.

```bash
aws elbv2 describe-target-groups --target-group-arns <arn> \
  --query 'TargetGroups[0].{interval:HealthCheckIntervalSeconds,timeout:HealthCheckTimeoutSeconds,healthy:HealthyThresholdCount,unhealthy:UnhealthyThresholdCount,path:HealthCheckPath}'
aws elbv2 describe-target-group-attributes --target-group-arn <arn> \
  --query 'Attributes[?Key==`deregistration_delay.timeout_seconds` || Key==`load_balancing.cross_zone.enabled`]'
```

## Scaling

Healing keeps the count at desired; **scaling** changes desired in response to demand. Intermediate practice means choosing a policy deliberately.

| Policy | Idea | Good for | Risk |
| --- | --- | --- | --- |
| Target tracking | Keep a metric (for example average CPU or requests per target) near a target | Most steady, web-style load | Metric lag; wrong metric for the real bottleneck |
| Step scaling | Add or remove capacity in steps by alarm severity | Sharp, known-shape spikes | More tuning; flapping if thresholds sit close |
| Scheduled scaling | Change capacity at known times | Predictable daily or weekly peaks | Out-of-pattern demand is missed |
| Predictive scaling | Forecast load from history and pre-scale | Cyclic traffic | Needs history; verify forecasts. *Version-specific:* availability depends on the service |

Rules that prevent most beginner scaling incidents:

1. **Minimum of two** (across AZs) for anything that claims HA. A minimum of one is a single point of failure that scaling cannot rescue.
2. **Maximum is a safety limit, not a target.** Set it so a runaway loop or a traffic flood cannot create an unbounded bill, and high enough that real demand fits.
3. **Scale on the bottleneck.** If the service is limited by database connections, scaling tasks on CPU only creates more connections and a larger problem.
4. **Account for warm-up.** A new task needs time to start, pass health checks and populate caches. Use warm-up or cooldown settings and keep headroom for that time. *Version-specific:* names and defaults of warm-up and cooldown settings differ per service.
5. **Check quotas.** Service quotas (tasks per account, vCPUs per region, load-balancer targets) can stop scale-out exactly when you need it. Read them before launch.
6. **Scale-in carefully.** Removing capacity at the end of a spike interacts with deployments and health checks; use conservative scale-in.

```bash
aws application-autoscaling describe-scalable-targets --service-namespace ecs
aws application-autoscaling describe-scaling-policies --service-namespace ecs \
  --query 'ScalingPolicies[].[PolicyName,PolicyType]' --output table
aws service-quotas list-service-quotas --service-code ecs --query 'Quotas[].[QuotaName,Value]' --output table
```

## State: where data lives

Every piece of state must have a stated home, a stated durability and a stated restore path. Make this table for your service.

| State | Home | Survives task loss? | Survives AZ loss? | Restore path |
| --- | --- | --- | --- | --- |
| Orders | Managed database (Multi-AZ) | Yes | Yes after failover | Point-in-time recovery or snapshot |
| Uploaded files | Object storage with versioning | Yes | Yes | Previous object version or backup copy |
| User sessions | Shared cache or signed tokens | Only if not in task memory | Depends on the cache's own redundancy | Users log in again, or rebuild the cache |
| Idempotency keys | Database table | Yes | Yes after failover | Same as orders |
| Temporary files | Task scratch disk | No | No | Regenerate |
| Configuration | Code and parameter store | Yes | Yes (region-scoped) | Redeploy from code |
| Infrastructure state | Remote versioned backend | Yes | Depends on the backend | Restore a previous state version |

For each row, name what would be *lost* if the home failed. Temporary files are acceptable only if the system truly regenerates them. A common hidden state is the in-memory session or the "last processed" marker kept in a task. Move it, or write down that the service is not safely replaceable.

**Retries and idempotency.** A database failover or a task replacement produces failed requests that clients retry. If a retry can create a second order, the failure mode is duplicate data, not downtime. Make write operations idempotent (a client-supplied key that the server records) before drills begin.

## Backups and restores

Backups protect against failures that replication copies faithfully: deletion, corruption, a bad migration, ransomware.

| Mechanism | Protects against | RPO shape | Restore shape |
| --- | --- | --- | --- |
| Automated backups with point-in-time recovery (database) | Deletion, corruption, bad writes | Minutes (continuous log capture). *Version-specific:* check the latest restorable time you can actually see | Restores to a *new* database instance; takes time proportional to size |
| Manual or scheduled snapshots | Point-in-time copies kept on purpose | The snapshot interval | Restore to a new instance |
| Object versioning | Overwrite and delete of objects | Per-change | Restore a prior version or remove a delete marker |
| Backup service with retention rules | Central, policy-driven backups across services | Schedule-driven | Restore per recovery point |
| Cross-account or cross-region copy | Account compromise, regional impairment | Copy delay | Restore in the other account or region |
| Infrastructure state versioning | State corruption | Per apply | Restore a state version |

Three rules:

1. **A backup you have not restored is a hope.** Schedule a restore, record the timestamps and compare them with the RTO.
2. **A restore creates something new.** Database point-in-time recovery produces a new instance with a new endpoint; the application, the DNS record or the configuration must be repointed. Practise the repointing too.
3. **Keep a copy beyond the blast radius.** A backup in the same account and region as the data survives hardware failure but not an account-level incident.

```bash
# Restore to a new instance for a restore test (do not overwrite production)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier orders-db \
  --target-db-instance-identifier orders-db-restore-test \
  --restore-time 2026-11-14T09:30:00Z
aws rds wait db-instance-available --db-instance-identifier orders-db-restore-test
# Then run a validation query set, record timings, and delete the test instance.
```

Record these facts from a restore test: the target time, when the restore began, when the instance became available, when validation passed, and the row counts or checksums compared with the source.

## Managed services: what you hand over and what you keep

Managed services (databases, queues, object storage, load balancers) hand the provider the undifferentiated heavy lifting: patching, host replacement, replication. You still own configuration and usage.

| Concern | Provider handles | You still own |
| --- | --- | --- |
| Hardware and host replacement | Yes | Choosing the redundancy option (Multi-AZ, replicas) |
| Patching the engine | Largely, in maintenance windows | Window timing; testing upgrades; application compatibility |
| Replication and failover | Yes, if enabled | Enabling it; client reconnect behaviour; testing it |
| Backups | Mechanism available | Retention, restore testing, copying beyond blast radius |
| Capacity | Within provisioned or auto limits | Right-sizing; limits; connection counts |
| Access and encryption | Features provided | Using them correctly |
| Data correctness | No | Everything |

Treat "managed" as "someone else operates the machine, not the outcome". Whether a service is multi-AZ by default varies by service and setting. *Version-specific:* verify the redundancy behaviour of each service you use in its current documentation.

Another habit: in a failover, the **client** is half of the system. A database failover keeps the endpoint name but changes the address behind it. Clients that cache DNS for long, or keep stale connections, can stay broken after the database has recovered. Test with the real client.

## Implement through code

Change infrastructure code, not the console. Run `plan` before `apply`, keep the plan summary as evidence, and re-read outputs afterwards. Make HA claims measurable: expose `desired_count` as a variable; at two or more, verify task placement across AZs.

```hcl
variable "desired_count" {
  type        = number
  description = "Number of orders-api tasks. >= 2 is required for any HA claim."
  default     = 2

  validation {
    condition     = var.desired_count >= 1
    error_message = "desired_count must be at least 1."
  }
}

resource "aws_lb_target_group" "orders" {
  name_prefix          = "ord-"
  port                 = 8080
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = var.vpc_id
  deregistration_delay = 30

  health_check {
    path                = "/ready"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }
}

resource "aws_ecs_service" "orders_api" {
  name                              = "orders-api"
  cluster                           = aws_ecs_cluster.orders.id
  task_definition                   = aws_ecs_task_definition.orders_api.arn
  desired_count                     = var.desired_count
  launch_type                       = "FARGATE"
  health_check_grace_period_seconds = 60

  network_configuration {
    subnets         = var.private_subnet_ids   # at least two, in different AZs
    security_groups = [aws_security_group.tasks.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.orders.arn
    container_name   = "orders-api"
    container_port   = 8080
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}
```

*Version-specific:* attribute names and defaults depend on the provider version; check the provider documentation for the version pinned in your lock file.

```bash
terraform plan -out=tfplan | tee plan.txt          # keep plan.txt as evidence
terraform show -json tfplan | jq '.resource_changes[] | select(.change.actions != ["no-op"]) | [.address, (.change.actions|join(","))]'
terraform apply tfplan
aws ecs describe-tasks --cluster orders --tasks $(aws ecs list-tasks --cluster orders --query 'taskArns' --output text) \
  --query 'tasks[].[taskArn,availabilityZone,lastStatus]' --output table
```

If every task shows the same AZ, you have one failure domain with several copies. Fix the placement (subnets, service configuration) in code and re-verify.

## Drills

Choose one primary drill and record what it proves.

| Drill | What it proves | What it does not prove |
| --- | --- | --- |
| Stop a task | The scheduler replaces it; time to recover | Multi-instance HA when the count is one |
| Bad deployment via code, then revert | Rollback through code works without console drift | Data rollback |
| Remove a subnet from the service configuration | Sensitivity of placement configuration | An AZ outage; this is a configuration simulation, not a provider failure |
| Restore assumptions (state and backups) | Recovery path for infrastructure state or data | Application correctness |
| Restore a database to a new instance | Backup is usable; measured restore time | Failover behaviour; application repointing unless you also test it |

Do not recover a code-managed resource by editing it imperatively (for example, updating a service's task definition by hand): that creates drift.

A drill needs a hypothesis, an abort condition and a record before you start:

```text
Drill:        stop one orders-api task (desired count 2, two AZs)
Hypothesis:   error ratio stays below 1% and capacity returns within 90 seconds
Abort if:     5xx ratio above 5% for 60 seconds
Window:       practice environment, workday morning, observer present
Evidence:     curl loop output, service events, target health timeline, dashboard screenshot
```

## Observation signals

| Signal | Source | Use |
| --- | --- | --- |
| HTTP health | `curl` to the health URL | Pass or fail recovery |
| Service events | `describe-services` | Why tasks stopped or started |
| Target health | `describe-target-health` | Unhealthy versus draining |
| Logs | The service's log group | Application errors during a bad deployment |
| Load-balancer metrics | Metrics: healthy host count, 5xx counts, target response time | The user-visible shape of the failure |
| Scaling activity | Scaling history and alarms | Whether capacity changed when expected |

Read signals in time order. Build a timeline: when the fault began, when the signal moved, when the first alert fired, when the system recovered, when users stopped seeing errors. Gaps between those moments are the recovery time and the detection time, and they are the numbers to compare with the objectives.

## Routine failure analysis

Failure analysis becomes routine when you ask the same questions in the same order.

```text
1. What is the user-visible symptom?          (errors, slowness, wrong data, nothing)
2. When did it start, and what changed?       (deployments, config, scaling, certificates, quotas)
3. Which failure domain does it match?        (one task, one AZ, all tasks, a dependency, the data)
4. What do the load balancer and targets say? (healthy count, 5xx source: LB or target)
5. What do the service events say?            (stopped tasks, reasons, failed placements)
6. What do the logs say at the failure time?  (errors, timeouts, connection refusals)
7. Is capacity or a quota involved?           (desired vs running, pending reasons, limits)
8. What is the smallest reversible action?    (revert artefact through code, add capacity, wait)
9. Did it work? What did it prove or not?     (record the evidence and the gap)
```

**Worked example.** Users report intermittent errors after a deployment. Step 4: healthy host count is 2 of 2, but target 5xx counts are rising: the targets are healthy and yet failing real requests, so the health check is too shallow. Step 2: a deployment finished 12 minutes ago. Step 6: logs show `connection refused` to a new database setting on both tasks. Step 8: revert the task definition revision through code. Step 9: error ratio returns to baseline in 3 minutes (illustrative). Follow-up actions: make readiness check the database, and add a canary stage so that a configuration error does not hit both tasks together.

The same questions classify different incidents:

| Symptom | Likely domain | First signals | Typical action |
| --- | --- | --- | --- |
| A fraction of requests fail, briefly, once | One task | Service events, target health | None; verify replacement |
| Errors only from users hitting one AZ's load-balancer node | One AZ or cross-zone setting | Per-AZ target health and metrics | Check AZ health; add capacity elsewhere |
| All targets unhealthy at once | Shared dependency or bad release | Logs, recent changes | Revert; fix dependency |
| Desired count high, running count low | Capacity, quota or placement failure | Service events, quotas | Fix limit or subnet; reduce churn |
| Slow but not failing | Overload, gray failure | Latency percentiles, CPU, connections | Scale, shed load, investigate dependency |

## Console exceptions

Maintain a list of anything created or changed by hand, with a follow-up date. An empty list is excellent. Unlisted manual drift is a defect.

```text
Date        Resource                  Change (by hand)           Reason                  Fix-by
2026-11-14  sg-0abc... (tasks)        Added temporary 22/tcp     Debug during drill      2026-11-15 (remove)
```

## Knowledge consolidation

- An ADR records decisions, limits and, above all, what is *not* claimed.
- Network dependencies (NAT, endpoints, DNS, registry, secrets) are failure domains; a single NAT gateway makes outbound access single-AZ.
- Readiness decides traffic; liveness decides restarts; deep checks should alert people without emptying the load balancer.
- Scaling needs a minimum of two, a sensible maximum, the right metric, warm-up allowance and quota headroom.
- Every state has a home, durability and restore path; replication does not replace backup; restores create new resources.
- Evidence beats configuration: a timeline from a drill outranks a diagram.

## Exercises

**Exercise 1 — Stop-task comparison.** Run the stop-task drill with desired count one and two, plot the HTTP status over time and write the difference in two sentences. Include the timeline of events.

**Exercise 2 — Placement proof.** Deploy two tasks. Using only the CLI, prove they are in different AZs. Then reduce the subnets in code to one AZ, plan and apply, and show what changed.

**Exercise 3 — Health check design.** Write two readiness handlers for `orders-api`: one that checks only the process, one that checks the database. Predict and then observe what the load balancer does for each when the database is stopped for 30 seconds. Explain which you would use and why.

**Exercise 4 — Restore test.** Restore the database to a new instance at a time ten minutes in the past. Record start, available and validated times, and compare with the 30-minute RTO. List what you would still need to do to cut over the application.

**Exercise 5 — Dependency map.** List every network and service dependency of a task from image pull to log emission, with the AZ and failure effect of each. Mark any that is a single point of failure.

**Exercise 6 — Capacity.** Peak needs 8 tasks. Calculate total tasks needed to survive one AZ loss at peak for 2 AZs and 3 AZs, and state the extra cost as a percentage.

**Solution notes.**

*Exercise 1.* With one task, expect a period of errors until the replacement is healthy; with two, expect at most a handful. The explanation should cite target health: no healthy target versus one healthy target. If both runs behaved the same, check that two targets were registered and were in different AZs.

*Exercise 2.* `describe-tasks` shows `availabilityZone` per task. After restricting subnets to one AZ, the plan should show a service update, and new tasks should land in one AZ. The outcome shows how fragile placement configuration is.

*Exercise 3.* A process-only check stays healthy during a database stop, so users see errors on database-backed paths while targets stay in service. A database-checking check removes every target and turns partial failure into total unavailability. A pragmatic answer: readiness checks local conditions (can serve, connection pool initialised), with dependency health surfaced by metrics and alarms. Defend your own choice with the observed result.

*Exercise 4.* Restore time depends on database size; do not copy numbers from this text. Cutover needs a new endpoint (configuration or DNS), credential access, connection draining of the old endpoint and a validation query, which is why the restore test measures only part of the recovery.

*Exercise 5.* Expect image registry, secrets, database, object storage, logging and DNS at least. A single NAT gateway or a single interface endpoint in one AZ is a typical single point of failure.

*Exercise 6.* For 8 tasks: 2 AZs need 8 each, total 16, extra 100%. For 3 AZs any two must hold 8, so 4 per AZ, total 12, extra 50%.
