# T-CLD-05-P — Professional Engineering

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-p"></a>
#### T-CLD-05-P — Professional Engineering

## Why this matters

At Professional level the question changes from "can I build a redundant topology?" to "can I prove, to someone who was not in the room, that this system recovers within the objectives, and say precisely what I did not prove?" A reliability claim without evidence is a hypothesis; the work of this section is converting hypotheses into measured, repeatable, documented capabilities, at a cost the business has agreed to.

The running service remains `orders-api`: ECS on Fargate behind an Application Load Balancer across AZs, a Multi-AZ managed database, versioned object storage. The chapter is self-contained.

**Conventions.** *Version-specific* marks behaviour, defaults, limits, identifiers or timings AWS may change; verify before relying on them. *Illustrative* marks a plausible figure used to teach the method; measure your own. Angle brackets are placeholders.

## Objectives first: RTO and RPO per component

Write RTO and RPO per component and justify them against business impact. A single number for "the system" hides the fact that different failures have different recovery paths.

| Component | RTO driver | RPO driver |
| --- | --- | --- |
| Stateless API behind a load balancer | Detection plus scheduling plus start-up plus health-check time | Not applicable: no state |
| Managed database, host or AZ failure | Failover time plus client reconnection | Replication: near zero for synchronous standby |
| Managed database, deletion or corruption | Restore time plus validation plus cutover | Time since last good restore point |
| Object storage | Often not applicable; recovery of deleted objects via versions | Per-change with versioning |
| Infrastructure itself (re-creating from code) | Plan and apply time, quota, image availability | State backup frequency |

**Worked example 1: stateless failure budget.** One task crashes. Both tasks sit behind an ALB with health check interval 10 s, unhealthy threshold 3, healthy threshold 2; the service has `health_check_grace_period_seconds` 60.

| Phase | Mechanism | Illustrative time |
| --- | --- | --- |
| Scheduler notices the stopped task | Service scheduler reacts to the stopped task event | about 5 s |
| Load balancer stops sending to the dead target | 10 s × 3 unhealthy checks | up to 30 s |
| Replacement provisioned and image pulled | Fargate placement plus pull | about 30 s |
| Application starts and listens | Runtime start-up | about 15 s |
| Target considered healthy | 10 s × 2 healthy checks | 20 s |

User-visible error window: up to about 30 s, for roughly half of requests while two targets exist and one is dead, because detection is the only delay users feel. Capacity-restoration time: about 5 + 30 + 15 + 20 = 70 s. These are different numbers, and the second is the one to compare with a capacity RTO. Tightening detection to interval 5 s and threshold 2 gives about 10 s of error window, at the price of more probe traffic and a higher chance that a pause (a garbage collection, a brief CPU stall) removes a healthy target. *Version-specific:* minimum intervals and defaults differ by load-balancer type.

**Worked example 2: database failure budget.** A Multi-AZ database loses its primary host. *Version-specific:* AWS documentation has described Multi-AZ instance deployments as failing over in roughly one to two minutes and Multi-AZ cluster deployments in tens of seconds; verify the current figures for your engine.

| Phase | Illustrative time |
| --- | --- |
| Failure detected and standby promoted | 60–120 s |
| Endpoint name resolves to the new primary | seconds, plus any client DNS cache |
| Connection pools detect broken connections and reconnect | 10–30 s |
| In-flight writes retried (idempotent) | seconds |
| Total write interruption | roughly 2–3 minutes |

The client behaviour is as much a part of the budget as the provider's failover. A pool that waits for a 5-minute TCP timeout before discovering the old connection is dead has just turned a 90 s failover into a 5-minute outage.

**Worked example 3: restore after corruption.** A bad migration deletes rows at 14:07; it is noticed at 14:40. Point-in-time recovery can restore to 14:06 into a *new* instance. Suppose the database is 500 GB.

| Step | Illustrative time |
| --- | --- |
| Decide to restore and choose the target time | 10 min |
| Restore to a new instance | 45 min |
| Validate: row counts, key invariants | 10 min |
| Extract the lost rows or cut over | 20 min |
| **Total** | **about 85 min** |
| RPO achieved | rows written after the target time are lost unless extracted from the live database or logs |

If the business RTO for "service restored" is 30 minutes, this recovery path *cannot* meet it. That is the point of working the example: there are two different objectives.

| Failure class | RTO | RPO | How met |
| --- | --- | --- | --- |
| Host, task or AZ failure | 5 min | near zero | Multi-AZ, multiple tasks, headroom |
| Data corruption or deletion | 2 hours | about 5 min plus extraction of later valid writes | Point-in-time recovery to a new instance, tested |
| Account or region loss | 8 hours | up to 24 h (cross-account, cross-region copy) | Backup copy plus rebuild from code, tested yearly |

Writing three rows rather than one forces the honest conversation about spend. Reducing the corruption RTO from 2 hours to 30 minutes is a design change (for example a delayed replica, logical logs, or rows being soft-deleted), not a configuration tweak.

**RPO is the worst case of the path used.** If the recovery path is "restore the nightly snapshot copied to another region", the RPO is up to 24 hours plus copy time, whatever the Multi-AZ standby could have offered.

## Designing for failure domains

A failure domain is the set of things that fail together: instance, rack, AZ, region, account, dependency. Spread replicas across AZs; keep capacity so remaining AZs can absorb load; make health checks accurate (readiness reflects whether traffic should be sent, liveness whether to restart); and avoid cross-AZ chattiness that doubles cost and latency.

**Static stability.** A design is statically stable if it keeps working when a dependency fails *without needing to make changes or call control-plane APIs during the failure*. The classic example: if one AZ is lost, run enough capacity already in the other AZs to carry peak, rather than relying on launching new instances after the event. During a significant impairment many customers launch capacity simultaneously and the control plane and capacity pools are busiest. Pre-provisioned capacity does not depend on those. *Version-specific:* the data plane (running resources) and control plane (APIs that create or change resources) have different availability characteristics; AWS publishes guidance on this, so read its current form.

**Capacity maths for N+1 across AZs.** Let `P` be peak load in task units, `A` the number of AZs and one AZ allowed to fail. Each surviving AZ carries `P / (A − 1)`, so each AZ must be provisioned for at least that, total `A × P / (A − 1)`.

| AZs | Per-AZ provisioning (P = 12) | Total | Overhead over P |
| --- | --- | --- | --- |
| 2 | 12 | 24 | 100% |
| 3 | 6 | 18 | 50% |
| 4 | 4 | 16 | 33% |

Diminishing returns apply: operating more AZs adds cross-AZ data charges, deployment surface and uneven failure behaviour. For most services two or three is the right answer.

**Failure-domain inventory.** For each dependency, record the domain.

```text
Dependency            Domain          Redundancy                  Tested?
Tasks                 AZ              2 per AZ x 3 AZs            yes (drill 2026-10)
ALB nodes             AZ              one per AZ                  provider-managed
NAT gateway           AZ              one per AZ                  yes
Database              AZ              Multi-AZ standby            failover drill 2026-09
Object storage        Region          multi-AZ storage            n/a
Image registry        Region          replicated copy in 2nd rgn  no
Secrets store         Region          cached at start             no
Deployment pipeline   Account         single                      n/a: human fallback documented
Backups               Account         cross-account copy          restore tested 2026-08
DNS provider          Global          single provider             failover untested
```

Rows marked "no" are the register of unproven claims. The deployment pipeline row matters: if one pipeline deploys every AZ at once, a bad release is one failure domain covering everything.

**Cross-AZ chatter.** If every request fans out to services in other AZs, the user-visible latency and the data-transfer bill both increase, and an impaired AZ affects traffic that never ran there. Prefer AZ-local routing where the dependency is replicated in every AZ, with failover to other AZs when local capacity is unhealthy. *Version-specific:* cross-zone defaults and AZ-aware routing options vary by service.

**Separating accounts and blast radius.** Production and recovery copies should live in different accounts from where mistakes happen. A compromised credential in the workload account should not be able to delete the backup copy.

## Patterns that make recovery routine

| Pattern | Effect |
| --- | --- |
| Stateless services with externalised state | Instances are disposable |
| Immutable deployments by digest | Rollback means redeploying a known artefact |
| Rolling or blue/green releases with health gates | A bad release stops early |
| Graceful shutdown and connection draining | Deployments and scaling do not drop requests |
| Timeouts, retries with jitter, circuit breakers | Failures do not cascade |
| Autoscaling with sane limits | Load spikes and cost are bounded |
| Backups with tested restores | Data loss is bounded |

## Immutable releases

Immutable means you never change a running thing; you replace it with a new, versioned artefact. The properties you gain are repeatability (the same input gives the same release), a precise record of what ran and when, and a rollback that is just the previous artefact.

**Deploy by digest, not by tag.** A tag can be repointed; a digest cannot.

```hcl
# The task definition references an image by digest. CI supplies the digest of the tested build.
variable "orders_api_image_digest" {
  type        = string
  description = "sha256 digest of the tested orders-api image"
}

locals {
  image = "${var.registry}/orders-api@${var.orders_api_image_digest}"
}
```

Each release creates a new task-definition *revision*; the previous revision remains. Rolling back is setting the service to a previous revision (through the same code path, with the previous digest), not rebuilding.

**Rolling release controls.**

| Setting | Meaning | Effect |
| --- | --- | --- |
| Minimum healthy percent | Fraction of desired count that must stay healthy during the deployment | Protects capacity during a rollout |
| Maximum percent | Allowed total tasks during rollout | Allows new tasks before old ones stop |
| Deployment circuit breaker | Stops and optionally rolls back when new tasks repeatedly fail to become healthy | Contains a clearly broken release |
| Health-check grace period | Time before failing health checks counts | Avoids killing slow starters |
| Stop timeout and deregistration delay | Time for graceful shutdown and for in-flight requests | No dropped requests on rollout |

With `desired_count` 4, minimum healthy 100% and maximum 200%, a rollout starts four new tasks, waits until healthy, then stops the old four: capacity never dips, at the cost of temporary double capacity (and a quota check). With minimum 50% and maximum 100%, it replaces two at a time and capacity dips to half: cheaper, riskier. *Version-specific:* defaults and which settings are available differ between deployment controllers and launch types.

**What gates a bad release?** A circuit breaker catches releases that fail to start. It does not catch releases that start fine and return wrong answers. For those, you need canary traffic with automated comparison of error ratio and latency against baseline, or a manual gate with a defined observation period. Document which class of failure each gate catches.

**Blue/green and canary.**

| Strategy | How | Rollback | Costs |
| --- | --- | --- | --- |
| Rolling | Replace tasks progressively | Redeploy previous revision | Low; mixed versions at once |
| Blue/green | Full new fleet beside old, shift traffic | Shift traffic back | Double capacity during the switch |
| Canary | Small percentage first, then more | Remove the canary | Needs weighted routing and metrics comparison |

Mixed versions are the hidden constraint: during any gradual release, two versions run together, so the database schema and the API must be compatible with both.

**Database changes: expand and contract.** Rollback of code is easy; rollback of data is not. Release changes in compatible steps: *expand* (add the new column, keep the old), deploy code that writes both, backfill, switch reads, then *contract* (remove the old column) only after the old code is gone and a rollback window has passed. A destructive migration shipped together with new code makes "roll back the artefact" a lie.

**Graceful shutdown.** On a stop, the orchestrator sends a termination signal and waits for a configured timeout before forcing. The application should stop accepting new work, finish in-flight work and exit within that period. Align three numbers: application drain time, container stop timeout, and load-balancer deregistration delay. If the stop timeout is shorter than the longest request, requests are cut off on every deployment.

```text
Rule: deregistration delay >= longest normal request;  stop timeout > deregistration delay + app drain
Example: longest request 8 s -> delay 15 s -> stop timeout 30 s
```

## Data protection in layers

Managed databases offer automated backups, point-in-time recovery, snapshots, read replicas and multi-AZ standby; they are not interchangeable. Replicas help read scale and some failover; backups protect against deletion and corruption; neither replaces the other.

| Layer | Threat it addresses | Threat it does not address |
| --- | --- | --- |
| Multi-AZ standby | Host and AZ failure | Deletion, corruption (replicated) |
| Point-in-time recovery | Mistaken writes, deletion, corruption | Region loss unless copied; account compromise |
| Snapshots in the same account | Mistaken deletion of rows or instance (if protected) | Account compromise |
| Cross-account, cross-region copies | Account compromise, regional impairment | Slow recovery (restore time); copy lag |
| Immutable or locked backup vault | Ransomware, malicious deletion | Corruption present before the backup |
| Object versioning plus delete protection | Overwrite and delete | Whole-account compromise unless locked or replicated elsewhere |
| Infrastructure state versioning and locking | Corrupt or overwritten state | Missing resources that were never in code |

*Version-specific:* names and capabilities (for example vault locking, multi-party approval, cross-region copy options, snapshot sharing with encrypted volumes) vary by service and change; verify in current documentation.

**Encryption keys are part of the backup.** An encrypted snapshot is useless if the recovery account cannot use the key. Practise a restore in the *recovery* account with the *recovery* permissions, since permission failures at 3 a.m. are a classic reason a documented restore fails.

**Protect infrastructure state.** Keep the remote state versioned, locked during apply, and in an account separate from the workloads it describes. Rehearse recovery of the state itself.

## Tested restore

An untested backup is a hope. A tested restore is a measured procedure with a recorded outcome.

```text
Restore test: orders-db, point in time, into a new instance
Preconditions:   recovery role assumed; KMS key accessible; subnet group and parameter group exist
Step 1 (t0)      Start restore to 2026-11-14T09:30Z               time: __:__
Step 2           Instance available                               time: __:__
Step 3           Run validation: row counts per table, max(order_id), checksum of sample
Step 4           Application smoke test against restored endpoint (read-only)
Step 5           Record elapsed time per step; compare with RTO
Step 6           Delete test instance; confirm cost stops
Pass criteria:   validation matches source at target time; elapsed time < agreed RTO for this failure class
Evidence:        timestamps, validation output, who ran it, version of the runbook used
```

Typical reasons restores fail the first time, which is why rehearsal is valuable:

| Failure | Cause |
| --- | --- |
| Restore cannot start | Missing permissions on the key or role; quota on instances or storage |
| Restore starts but application cannot connect | Wrong subnet group or security group; endpoint name differs |
| Restored data is not what was expected | Wrong target time or time zone; backup retention shorter than assumed |
| Restore is slower than the budget | Database larger than during the previous test; storage warm-up. *Version-specific:* restored volumes may perform below steady state until data is loaded |
| Cutover breaks clients | Cached endpoints or long-lived connections |

Time the restore against the *current* data size, not the size when the runbook was written. Repeat at a frequency tied to change: after major schema changes, after a significant growth step, and at least quarterly for critical data.

## Recovery runbooks

A runbook is for a tired person under pressure. It must start with symptoms, order actions from reversible to irreversible, and say who may do what. The skeleton:

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

A filled excerpt for one scenario:

```markdown
# Scenario: 5xx ratio above 5% for 3 minutes after a deployment
## Symptoms        - alarm "orders-api-5xx-ratio"; healthy hosts 2/2 (so checks pass but requests fail)
## Immediate checks
  1. Last deployment time and digest (deployment log)
  2. Target 5xx versus load-balancer 5xx (dashboard "orders-api / edge")
  3. Log query for first error after deployment time
## Actions (reversible first)
  1. Pause further deployments (freeze label on the pipeline)
  2. If errors began within 15 min of a deployment: redeploy previous digest through the pipeline
  3. If the pipeline is unavailable: use the documented break-glass role; record it in the exception list
## Rollback        - previous digest is the prior release record; never edit the live service by hand
## Data            - if the release wrote bad data, STOP: do not retry writes; go to "Data corruption" runbook
## Escalation      - 10 min without recovery: page the service owner; 30 min: incident commander
## After           - confirm 5xx ratio below 1% for 15 min; attach timeline; open follow-ups
```

Runbook hygiene: link each runbook from its alarm; date and version it; run it in a drill (a runbook that no one has executed contains untested instructions); keep break-glass steps separate with an explicit record requirement.

## Reliability and cost

Reliability is bought; the price should be explicit and proportionate to the impact avoided.

| Design | Relative steady-state cost (illustrative, ratio) | Typical protection |
| --- | --- | --- |
| 1 AZ, 1 task, single-instance DB | 1.0 | Almost none; host loss means an outage |
| 2 AZs, 2 tasks, Multi-AZ DB | about 2 | Task, host and AZ failure, with downtime during DB failover |
| 3 AZs, N+1 sized, Multi-AZ DB, cross-account backups | about 2.5 | Plus AZ loss at peak with less overhead, plus account-level backup safety |
| Plus warm standby in a second region | about 3.5–4 | Region loss in minutes to an hour |
| Active-active across two regions | 4 or more, plus operating cost | Region loss with near-zero interruption, if conflicts are solved |

Use the ratios to frame decisions, never to quote a budget; compute real costs from current pricing and your usage. *Version-specific:* pricing structures (NAT processing, inter-AZ data transfer, load-balancer capacity units) change and differ by region.

**Expected-loss reasoning.** Suppose an hour of `orders-api` outage costs about 4,000 in lost orders and recovery effort (illustrative). If AZ loss is expected once per 10 years, and the single-AZ design takes 4 hours to recover while the multi-AZ design takes 5 minutes, then the avoided expected loss is about `(4 − 0.083) × 4,000 / 10 ≈ 1,570` per year. If multi-AZ adds 12,000 per year, expected loss alone does not justify it; but if the 99.9% availability commitment carries penalties, reputation cost, or the same extra tasks also cover host failures that occur more often (they do), the calculation changes. The point is to write the argument down, with the assumptions visible, rather than to trust a single formula.

**Quotas, limits and teardown.** Update cost guardrails after architecture changes: whether a NAT is added, load-balancer idle cost, compute count, what will be destroyed after the exercise. Quotas (service limits) can block scale-out or a recovery action; check them proactively, including on the *recovery* account and region. Keep the destroy path tested.

```bash
aws service-quotas get-service-quota --service-code fargate --quota-code <quota-code>
aws service-quotas list-requested-service-quota-change-history --service-code fargate
```

## Fault-drill evidence

Professional practice makes a claim about resilience only when evidence supports it. Evidence has a shape.

**The evidence pack for one drill.**

```text
1. Claim under test         "Loss of one AZ's tasks does not breach the 99.9% objective."
2. Hypothesis               "Error ratio stays below 1% and p99 below 800 ms; capacity restored in < 2 min"
3. Preconditions            Version of code and infra; desired count; AZ spread proof; alarm states
4. Injection                What was done, by whom, with what tool, at what time (UTC)
5. Observation              Timeline with timestamps; graphs; log excerpts
6. Result                   Pass, fail or inconclusive against each criterion
7. Gaps                     What the drill did not exercise
8. Actions                  Owner, date, linked ticket
9. Artefacts                Plan files, dashboards, query text, screenshots (stored with the ADR)
```

A **fault-injection service** (AWS Fault Injection Service at the time of writing) runs controlled experiments, with stop conditions tied to alarms and role-limited actions, so a drill can be repeated. A sketch of an experiment template (shape only):

```json
{
  "description": "Stop all orders-api tasks in one AZ (staging)",
  "targets": {
    "azTasks": {
      "resourceType": "aws:ecs:task",
      "resourceTags": { "service": "orders-api", "az": "a" },
      "selectionMode": "ALL"
    }
  },
  "actions": {
    "stopTasks": { "actionId": "aws:ecs:stop-task", "targets": { "Tasks": "azTasks" } }
  },
  "stopConditions": [
    { "source": "aws:cloudwatch:alarm", "value": "<alarm-arn-for-5xx-ratio-above-5-percent>" }
  ],
  "roleArn": "<experiment-role-arn>"
}
```

*Version-specific:* action identifiers, target types and parameters are defined by the fault-injection service and change; confirm in its current action catalogue. The important parts are portable: scoped targets, an abort condition tied to an alarm, a narrow role and a written hypothesis.

**What a drill proves and does not.**

| Drill | Proves | Does not prove |
| --- | --- | --- |
| Stop all tasks in one AZ | Scheduler and load balancer shift traffic; headroom suffices at the test load | Behaviour at peak load; database failover; a real network partition |
| Database forced failover | Failover time, client reconnect, idempotent retries | Restore from backup |
| Restore to a new instance | Backup is usable; time and procedure | Failover; application cutover |
| Bad release rollback | Redeploying the previous digest works | Data rollback after a destructive migration |
| Remove a subnet in config | Placement sensitivity | A real AZ outage (it is a configuration simulation) |

Keep a **claims ledger**: every resilience statement the team makes, the drill that supports it, the date, and the expiry. Claims expire because the system changes: a drill from last year says little about today's code.

```text
Claim                                     Evidence                     Date        Valid until
Tolerates loss of one task                drill D-14 timeline          2026-10-02  2027-04-02
Tolerates one AZ at 60% of peak           game day GD-3 report         2026-09-18  2027-03-18
Restores DB within 2 h from PITR          restore test R-6             2026-08-12  2026-11-12  (EXPIRED)
Survives region loss                      NOT CLAIMED                  -           -
```

## Honest ADR statements

"The load balancer spans two AZs; the application is not claimed to tolerate an AZ failure because desired count is one." "Stopping the task is recovered by the scheduler within the RTO measured at 45 seconds." State limitations explicitly.

## Professional trade-offs

| Decision | Option A | Option B | How to choose |
| --- | --- | --- | --- |
| Health-check strictness | Shallow: process only | Deep: dependencies | Shallow for readiness; deep for alerting; test the dependency-failure case |
| Detection speed | Fast intervals | Slow intervals | Fast when the cost of a bad target is high and probes are cheap; watch for flapping |
| Capacity headroom | Run extra capacity always | Scale on demand | Run headroom for the AZ-loss case; scale for demand |
| Release style | Rolling | Blue/green or canary | Canary when wrong-answer failures are costly and metrics are trustworthy |
| Data recovery | Replica | Backup copy | Both: they address different threats |
| AZs used | 2 | 3 | Three where N+1 cost matters and the region supports it |

## Decision guide

| Question | Answer approach |
| --- | --- |
| Is it HA? | Show placement across failure domains and a test, or do not claim it |
| How fast do we recover? | Measure with a drill; compare to RTO |
| What if the deployment is bad? | Revert the artefact via code; confirm health |
| What is lost if the data store dies? | State RPO from backup evidence |
| What did we not test? | Write it in the record |
| Which RTO applies? | The one for this failure class: task, AZ, data, account, region |
| When does a claim expire? | When the system changes materially, or on the ledger date |

## Knowledge consolidation

- RTO and RPO are per component *and* per failure class; the corruption path is slower than the failover path, and that is normal.
- Distinguish the user-visible error window from capacity-restoration time.
- Static stability means pre-provisioned capacity; compute the N+1 overhead with `A × P / (A − 1)`.
- Deploy by digest, keep revisions, use controlled rollouts, and use expand-and-contract for data changes.
- Layer the data protection: standby, point-in-time recovery, copies in another account, locked backups; test the restore in the recovery account.
- A runbook is valid only after someone has executed it.
- Evidence packs and a claims ledger turn resilience statements into dated, expiring facts.

## Exercises

**Exercise 1 — Timing budget.** For your own `orders-api` health-check settings, compute the user-visible error window and the capacity-restoration time. Then run the drill and compare, line by line.

**Exercise 2 — Two RTOs.** Write RTO and RPO for task failure, AZ loss, data corruption and region loss. For corruption, measure a real restore and state whether the number meets your RTO.

**Exercise 3 — Headroom.** Peak is 20 tasks. Compute total tasks and overhead for 2, 3 and 4 AZs with one AZ allowed to fail. Which would you choose and why?

**Exercise 4 — Release safety.** Configure minimum healthy 100 and maximum 200 for a four-task service, ship a deliberately broken image (fails health check), and record what the circuit breaker does. Then ship an image that starts but returns 500 on one route and record what *does not* stop it.

**Exercise 5 — Runbook execution.** Hand your bad-release runbook to a colleague who did not write it. Time them and list each step where they hesitated or deviated.

**Exercise 6 — Claims ledger.** Write six resilience claims about your system. For each, name the evidence and expiry, or mark it "NOT CLAIMED".

**Solution notes.**

*Exercise 1.* With interval 10, unhealthy 3, healthy 2 and a 30 s start, expect an error window up to 30 s and capacity restoration near 70 s. Discrepancies usually come from the load balancer detecting faster than expected (connection refused is noticed before the threshold), slower Fargate placement, or a grace period that delays checks.

*Exercise 2.* A plausible shape is the three-row table in this section. For corruption, your measured restore plus validation plus cutover may well exceed the 30-minute figure; the correct response is a distinct, justified RTO, or a design change, not a hidden mismatch.

*Exercise 3.* `A × P / (A − 1)`: 2 AZs, 40 tasks (100% overhead); 3 AZs, 30 tasks (50%); 4 AZs, 26.7, so 28 with rounding to 7 per AZ (40%). The three-AZ choice is typically the best balance; four gains little and increases complexity.

*Exercise 4.* The broken-start image should trigger the circuit breaker, stop the rollout and, if rollback is enabled, return to the previous revision. The image that starts and returns 500 on a single route passes health checks and completes the rollout; only canary comparison, alarms or a manual gate would catch it.

*Exercise 5.* Hesitation points indicate ambiguity: missing links, unclear permissions, undefined thresholds. Fix each in the runbook and repeat.

*Exercise 6.* A good ledger has at least one NOT CLAIMED entry and at least one expiry in the near future; if all claims are valid for years, the evidence is probably being over-trusted.
