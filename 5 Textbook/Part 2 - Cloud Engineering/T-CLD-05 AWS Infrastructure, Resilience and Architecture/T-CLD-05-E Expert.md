# T-CLD-05-E — Expert Depth

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-e"></a>
#### T-CLD-05-E — Expert Depth

## Why this matters

Expert work in resilience is mostly the discipline of distrust: distrust of independence assumptions, of health checks, of durability claims, of failover paths nobody has used and of averages. The recurring pattern in large failures is not that a component died but that a *correlation* nobody had drawn on the diagram made the redundancy worthless: a shared dependency, a shared release, a shared control plane, a retry loop that turned a blip into a flood.

This section gives you the mathematics to quantify those effects, the vocabulary to describe gray failures and overload, the practice (game days, fault injection) to expose them, the architecture patterns (cells, shuffle sharding, multi-region) to limit their reach, and the honesty about what data recovery physically can and cannot do. The service is still `orders-api`, behind an ALB across AZs, with a managed database and versioned object storage. The chapter is self-contained.

**Conventions.** *Version-specific* marks AWS behaviour, defaults, limits or identifiers that can change; verify against current documentation. *Illustrative* marks numbers chosen to teach a method. Cases at the end are fictional composites.

## Availability mathematics

**Series and parallel.** Components in series multiply availability (0.999 × 0.999 ≈ 0.998); redundancy in parallel improves it only if failures are independent and failover works. Shared dependencies (a single database, one DNS provider, a global control plane, one deployment pipeline) cap overall availability and create correlated failure. Draw the dependency graph and mark hard dependencies.

**Downtime table (30 days = 43,200 minutes).**

| Availability | Unavailability | Downtime per 30 days |
| --- | --- | --- |
| 99% | 1 × 10⁻² | 7 h 12 min |
| 99.9% | 1 × 10⁻³ | 43.2 min |
| 99.95% | 5 × 10⁻⁴ | 21.6 min |
| 99.99% | 1 × 10⁻⁴ | 4.32 min |
| 99.999% | 1 × 10⁻⁵ | 25.9 s |

**Availability arithmetic, worked.** Suppose `orders-api` needs a load balancer (99.99%), two identical tasks in different AZs (each 99.9% independently), and one database (99.95%).

| Component | Calculation | Availability |
| --- | --- | --- |
| Two tasks in parallel | 1 − (0.001 × 0.001) | 99.9999% |
| Series: load balancer × tasks × database | 0.9999 × 0.999999 × 0.9995 | about 99.94% |

The database alone caps the system near 99.95%, no matter how many tasks you add. Redundancy helps only the part that is replicated. The parallel calculation also assumes independence and that failover works; a shared deployment or a common bad release makes both tasks fail together, so the real figure is lower. Convert to downtime to make the point: 99.94% is about 26 minutes per 30 days; 99.99% is about 4 minutes.

**Common-cause failure: the beta-factor model.** Independence is the assumption most often false. A standard simplification: with per-component unavailability `u` and a fraction `β` of failures caused by a common cause that hits both copies, the unavailability of a pair is approximately

```text
u_pair ≈ (1 − β)² · u²  +  β · u        (for small u, about u² + β·u)
```

For the two tasks above, `u = 0.001`. With `β = 0` the pair has `u_pair = 10⁻⁶` (99.9999%). With `β = 0.1`, meaning one failure in ten is a shared cause such as a bad release, `u_pair ≈ 10⁻⁶ + 10⁻⁴ ≈ 1.01 × 10⁻⁴`, which is about 99.99%. A tenth of failures being common-cause removes two of the six nines the independence maths promised. The lesson is not the exact β; it is that the term `β · u` dominates quickly, so reducing correlation (staged releases, diverse dependencies, per-cell isolation) improves availability more than adding a third copy.

**From MTBF and MTTR.** Availability is also `MTBF / (MTBF + MTTR)`: mean time between failures over that plus mean time to recover.

| MTBF | MTTR | Availability |
| --- | --- | --- |
| 30 days | 4 hours | 99.45% |
| 30 days | 30 minutes | 99.93% |
| 30 days | 5 minutes | 99.988% |
| 90 days | 30 minutes | 99.98% |

For most software systems it is cheaper to cut MTTR (detection, automation, rehearsed runbooks) than to extend MTBF, because failure frequency is driven by change and by components you do not control. This is why drills and automation are availability work, not extras.

**Request-level maths and fan-out.** A request that must call `k` dependencies in series, each 99.9% available, succeeds with probability `0.999^k`. For `k = 10` that is 99.0%, ten times the unavailability of any one dependency. The same arithmetic applies to latency: if each of ten parallel calls has a 1% chance of a slow response (above its own p99), the chance that at least one is slow is `1 − 0.99¹⁰ ≈ 9.6%`. Fan-out turns each dependency's tail into the caller's median problem. Controls: fewer hard dependencies on the request path, fallbacks and caches for soft ones, hedged requests with care, and explicit timeouts shorter than the caller's budget.

**Error budgets.** An SLO of 99.9% over 30 days gives a budget of 43.2 minutes. Budget burn rate (how fast you consume the budget relative to the allowance) is a better alert signal than raw error counts: a burn rate of 14.4 sustained for an hour spends about 2% of a 30-day budget (illustrative thresholds from common practice). Drills and game days spend budget deliberately; account for them.

**Dependency graph review.** For each request type, list hard dependencies (request fails without them), soft dependencies (degraded without them) and background dependencies (affect later). Then ask for each hard dependency: its published availability, its failure domain, whether you have a tested fallback, and whether *its* dependencies overlap with others you use. Two services that look independent but both rely on the same DNS provider, identity provider or region control plane are not independent.

## Failure-mode analysis

For each component, list: failure mode, detection, impact, mitigation, owner. Include gray failures: partial degradation that passes health checks but harms users (slow disks, packet loss, thread pool exhaustion). Health checks should exercise realistic paths with timeouts, without causing cascading restarts when a dependency blips.

| Mode | Detection | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| Task crash | Scheduler event; target health drops | Brief capacity loss | Desired count ≥ 2 across AZs | Platform |
| AZ outage | Load balancer health per AZ; provider health | Up to half capacity | Capacity headroom (each AZ can carry the load) | Platform |
| Database failover | Replication and connection errors | Seconds to minutes of write failure | Retries with jitter; idempotent writes; tested failover | Service team |
| **Gray: disk latency rising on one task** | p99 latency per task; error budget burn; **health check still 200** | Slow responses for ~half the users | Outlier detection, latency-aware health checks, auto-replace slow targets | Service team |
| **Gray: thread-pool exhaustion** | Queue depth and in-flight request metrics | Timeouts that look like network errors | Concurrency limits, load shedding, bulkheads | Service team |
| Expired certificate | Days-to-expiry metric | Hard outage at expiry | Automated renewal and alert at 21 days | Platform |

Gray failures are dangerous because every binary check says "healthy" while users suffer. The defence is measuring the user-visible experience (latency percentiles, error ratio per target) and comparing instances with each other.

## Gray failures in depth

A gray failure is a state in which a component is degraded in a way that the system's own failure detectors do not register, while an application or user perceives it as failed. Characteristics: partial, intermittent, observer-dependent and long-lived because nothing triggers recovery.

**Why detectors miss it.**

| Detector | Why it passes |
| --- | --- |
| Shallow HTTP health check | The `/health` route does no real work and sits in a different thread pool |
| TCP connect check | The port accepts connections while handlers are stuck |
| Averages | One slow target in ten barely moves the mean |
| Per-service dashboards | The failing link is between two services, and each looks fine from its own side |
| Provider status page | The fault is below the threshold of an acknowledged event |

**A worked dilution.** Six targets; one has a failing disk and returns errors for 5% of requests, and its health check passes. The fleet-wide error ratio is `5% × 1/6 ≈ 0.83%`, under a 1% alert threshold. Yet the experience is concentrated. With per-request random routing, a user making 20 requests sees at least one failure with probability `1 − (1 − 0.05/6)^20 ≈ 15%`. With sticky connections, the one-sixth of users pinned to the bad target see at least one failure in 20 requests with probability `1 − 0.95^20 ≈ 64%`, and retries multiply their pain. The exact figures depend on routing; the principle is that aggregate metrics hide concentrated failure.

**Detection techniques.**

- **Per-target comparison.** Compare each target's error ratio and p99 with the fleet median; flag outliers (for example worse than three times the median for several minutes).
- **Differential observability.** Measure from several viewpoints (caller side, callee side, synthetic probes from different AZs) and alert when they disagree.
- **Real-path probes.** Synthetic transactions that exercise write and read paths, authenticated, from outside the VPC.
- **Passive health.** Eject targets that exhibit consecutive errors or latency outliers (outlier detection), with a cap on the fraction ejected so a systemic fault cannot eject the entire fleet.
- **Canary comparisons.** Compare new and old versions on the same traffic.

**Responses.** Auto-replace the outlier; reduce its weight; or shift away from the AZ if several targets in it are bad. Guard against false positives: if a dependency slows everything equally, per-target comparison finds no outlier and instead the dependency graph and saturation metrics must show it. Do not let a gray-failure detector cause the next outage by ejecting healthy capacity; require a cap, a hold-down period and an alert.

## Overload, metastability and degradation

Systems fail more often from overload than from component death. A particularly nasty variant is the **metastable failure**: a trigger (a brief slowdown, a cache flush, a deployment) pushes the system into a state where a sustaining effect (retry storms, cold caches, queue backlog) keeps it overloaded *after the trigger is gone*. Removing the trigger does not restore service; only reducing load or breaking the feedback loop does.

**Little's law as a diagnostic.** Concurrency in a system equals arrival rate multiplied by time spent in the system: `L = λ × W`. A service handling 200 requests per second at 100 ms holds about 20 requests in flight. If a dependency slows to 2 s, the same arrival rate needs 400 in flight; a pool of 100 workers saturates and the queue grows without bound. This is thread-pool exhaustion in one line, and it shows why the *first* symptom of a slow dependency is that the *caller* runs out of capacity.

**Retry amplification.** If a dependency slows and each of three layers retries three times, a single user request can become 27 requests to the dependency exactly when it is least able to cope. Controls: a *retry budget* (retries limited to a fraction of original traffic, for example 10%), exponential backoff with jitter, timeouts shorter than the caller's timeout, circuit breakers and load shedding that rejects low-priority work early with a clear 503.

```text
Retry budget rule: allow a retry only if retries_in_last_minute < 10% of requests_in_last_minute
Backoff with full jitter: sleep = random(0, min(cap, base * 2^attempt))
Deadline propagation: the caller's remaining time is passed down; the callee gives up when it expires
```

**Techniques.** Admission control and load shedding, bulkheads, priority queues, backpressure, adaptive concurrency limits and graceful degradation (serve cached or reduced content). Autoscaling lags demand by minutes, so keep headroom and protect cold start.

| Technique | Problem solved | Cost or risk |
| --- | --- | --- |
| Load shedding at the edge | Protects the core under overload | Some users get 503s on purpose; needs priority classes |
| Bulkheads (separate pools per dependency) | One slow dependency cannot consume every worker | Capacity is split; some pools idle |
| Circuit breaker | Stops hammering a failing dependency | Wrong thresholds cause flapping |
| Cache with stale-serve | Hides dependency blips | Staleness must be acceptable |
| Queue-based buffering | Absorbs bursts | Unbounded queues delay failure and increase latency; bound them |
| Cold-start protection (slow start, warm pools) | New instances not crushed on arrival | More configuration; extra standing cost. *Version-specific:* options differ per service |

**Breaking a metastable loop in practice.** Shed load until the system is below its saturated state, hold the shed until caches and queues drain, then restore traffic gradually. During recovery, deliberately lower retries, disable non-essential background work, and avoid autoscaling reacting to artefacts. Write this down as a runbook, because the first time you reason about it should not be during the incident.

## Multi-AZ and multi-region patterns

| Pattern | Recovery | Cost and complexity |
| --- | --- | --- |
| Single region, multi-AZ active-active | Automatic for AZ loss | Moderate |
| Backup and restore in another region | Hours | Low |
| Pilot light (minimal copy running) | Tens of minutes | Moderate |
| Warm standby | Minutes | High |
| Multi-region active-active | Near zero for data planes | Very high; data consistency and routing challenges |

Choose by business impact and tested capability. Active-active multi-region requires conflict handling, global routing, and operating the failover regularly; an untested failover is a hope.

**Choosing a recovery strategy with cost reasoning.**

| Strategy | Typical RTO | Typical RPO | Steady-state cost | Complexity to operate | Suits |
| --- | --- | --- | --- | --- | --- |
| Multi-AZ in one region | Seconds to minutes | Near zero with sync replication | Moderate | Low | Most production workloads |
| Backup and restore elsewhere | Hours | Backup interval | Low | Low (but must be rehearsed) | Tolerant business processes |
| Pilot light | Tens of minutes | Replication lag | Low–moderate | Moderate | Important workloads, moderate downtime tolerance |
| Warm standby | Minutes | Seconds–minutes | High | High | Critical workloads with strong justification |
| Multi-region active-active | Near zero | Near zero in theory; conflicts in practice | Very high | Very high: conflict resolution, global routing, regular failover practice | Rare; only when impact justifies it |

Write the justification as: "Impact of an hour of outage is X; the probability of regional loss is Y per year; option Z reduces expected downtime by W hours at cost C." Include a *why not more* line, which stops architecture drifting upward without evidence.

**The failover mechanism is itself a component.** Every multi-region design has a mechanism that moves traffic and promotes data: DNS records with health checks, a global traffic manager, a promoted replica, a script. Its availability is in series with everything else, and it is used rarely, so it rots.

| Mechanism | Strength | Weakness |
| --- | --- | --- |
| DNS failover with health checks | Simple, widely supported | Recursive resolvers and clients may cache beyond the TTL; failover time is TTL plus detection plus client behaviour |
| Anycast or global accelerator style routing | Fast traffic shifting at the network layer | Provider-specific; still needs correct health signals. *Version-specific:* capabilities and limits differ by product |
| Application-level routing (client picks region) | Full control | Clients must be updated; complexity |
| Manual promotion by runbook | Avoids split-brain false positives | Slow; depends on humans |

*Detection time plus TTL is the floor.* With health checks that need 3 failures at 10 s intervals and a DNS TTL of 60 s, the best case is about `30 + 60 = 90 s` until the first clients move, and long-tail clients that ignore TTL take longer. *Version-specific:* when planning failover, prefer actions on the **data plane** (for example health-check-driven DNS answers already deployed) over actions that require the **control plane** (creating or editing resources) during the event; control planes are the more likely to be degraded in a major impairment. AWS has documented that some global services' control planes are homed in a single region, which should shape how you build failover. Verify the current statement in AWS documentation.

**Data in more than one region.**

| Data pattern | RPO | Conflict handling | Caveat |
| --- | --- | --- | --- |
| Asynchronous replica promoted on failover | Replication lag at the time of failure (seconds to minutes) | None needed: one writer | Writes in the lag window are lost or must be reconciled; failback needs a re-seed |
| Multi-writer replication (for example global tables in a key-value store) | Seconds | Usually last-writer-wins by timestamp; may lose updates | Application must tolerate lost updates or use commutative data types |
| Object replication across regions | Typically seconds to minutes (*Version-specific:* some options carry a time-bound objective) | Last write wins per object | Deletes and versioning behaviour need configuration review |
| Backups copied across regions | Backup interval plus copy time | N/A | Restore time grows with size |

**Why a second region can reduce availability.** More moving parts in series (replication, failover automation, health checks); more deployment surface and configuration drift; correlated shared dependencies still present (the same code, the same pipeline, the same identity provider); a failover that triggers *falsely* causes an outage that would not have happened; and a team that cannot operate two regions well. A second region improves availability only to the extent that its failover is simple, tested and independent. Measure the number of *unplanned* failovers and *failed* failover exercises as first-class metrics.

**Split-brain and fencing.** Two regions each believing they are primary will accept divergent writes. Use a single arbitration source, require quorum or a human decision for promotion, and fence the old primary (block writes at the data layer, not merely at the edge) before promoting a new one. Then plan reconciliation: some writes in the lag window may exist only in the old primary.

**Failback is a second migration.** Returning to the original region means re-seeding data, validating, and shifting traffic again, often under less pressure but with new risk. Test failback in drills, not only failover.

## Durability, integrity and what "eleven nines" means

Durability is the probability that an object is *not lost* over a period. Provider designs commonly state it as a number of nines per year (for example 99.999999999%, eleven nines, for standard object storage classes; *Version-specific:* check the current statement for each storage class, including one-zone classes whose AZ-loss behaviour is different).

**Meaning in numbers.** An annual durability of 99.999999999% implies an expected loss of 1 object in 10¹¹ per year. With 10 million objects, the expected annual loss is `10⁷ × 10⁻¹¹ = 10⁻⁴` objects, or about one object in 10,000 years. Such numbers describe *media and infrastructure failure*. They say nothing about:

| Threat | Covered by durability design? | What covers it |
| --- | --- | --- |
| Hardware or AZ loss | Yes, within the stated design | Provider design |
| Accidental or malicious deletion | No | Versioning, object lock, separate-account replication |
| Application bug that overwrites valid data | No | Versioning; point-in-time logs; validation |
| Corruption before upload | No | End-to-end checksums at upload |
| Encryption key deletion | No: data becomes unreadable | Key deletion protections and waiting periods; key backup policy |
| Account closure or compromise | No | Copies in another account |

**Integrity.** Durability is not integrity. Use end-to-end checksums (compute at the producer, store, compare at the consumer) and periodic verification of backups and archives; silent corruption caught after the backup rotation window is unrecoverable. *Version-specific:* services offer additional checksum algorithms and verification features; adopt the current recommended ones.

**Correlated loss in your own design.** Replicating objects between buckets in the *same account* with the same delete permissions provides availability, not protection against an operator or attacker who can delete both. Durable means "survives the failures that matter", and the failures that matter include the people who hold the credentials.

## Data recovery limits

Recovery is bounded by physics and process, and Expert practice states those bounds.

**Restore throughput.** Time to restore is at least `size / sustained throughput`, plus fixed costs.

| Data size | Sustained throughput | Minimum copy time |
| --- | --- | --- |
| 500 GB | 200 MB/s | 2,500 s, about 42 min |
| 5 TB | 200 MB/s | 25,000 s, about 6.9 h |
| 50 TB | 200 MB/s | 250,000 s, about 2.9 days |
| 50 TB | 2 GB/s (parallelised) | 25,000 s, about 6.9 h |

Throughput is itself limited by the service, the network, the target storage and the account limits; parallelise where the design allows. *Version-specific:* restored block volumes or databases may be usable before all data has been loaded from the backing store, with slower first access; "available" is not the same as "performing at full speed". Measure *time to performance*, not only time to availability.

**Retention versus detection.** You can restore only to a point inside the retention window. If corruption goes unnoticed for 10 days and retention is 7 days, every restore point already contains the corruption. Set retention from detection capability, not from habit: `retention ≥ detection time + decision time + margin`. Keep long-retention snapshots (monthly, yearly) for slow-burn problems, subject to cost and legal requirements.

**RPO is measured from the last known-good state, not from the failure.** In logical corruption, the moment that matters is the last time the data was *correct*, which may be well before anyone noticed. If a faulty job has been quietly writing wrong totals for six hours, restoring to "just before we noticed" loses the right data and keeps the wrong data. Recovery becomes reconstruction: restore to the last good point into a side database, then replay or re-derive the valid changes from event logs, upstream systems or business records.

**Point-in-time recovery limits.** Typically restores to a new instance; has a latest restorable time slightly behind now; does not carry over every setting automatically; and cannot recover what the log never contained. Checks for expert review: Can you restore to a specific transaction boundary? Do you retain the logical change log for reconstruction? How do you re-apply the writes made after the target time?

**Dependencies of recovery.** A recovery can fail because of what it depends on: identity (cannot assume the recovery role), keys (cannot decrypt), network (no route to the restored database), images (registry unreachable), secrets (store unreachable), quotas, and your own tooling (the CI system is down). List them and rehearse recovery with the production tooling *unavailable*.

| Limit | Consequence | Mitigation |
| --- | --- | --- |
| Restore throughput | RTO grows with data size | Smaller blast radius (cells, partitions); parallel restore; keep a warm replica for faster scenarios |
| Retention shorter than detection time | No clean restore point | Detection investment; long-term snapshots |
| Replication copies corruption | Standby is also corrupt | Delayed replica; point-in-time recovery; logical change log |
| Key or identity loss | Data present but unusable | Protect keys; multi-account recovery identity |
| Backup written by the compromised party | Backups can be tampered with | Locked, cross-account, least-privilege backup chain |
| Unknown recoverability | The first real restore is the test | Scheduled, timed restores with validation |

## Blast radius

Blast radius is the portion of users, data or capacity affected by a single failure. Reduce it by design so that most failures are small.

**Cells.** Partition the system into independent, identical *cells*, each serving a subset of customers and containing its own compute, data and dependencies, with a thin router in front. A failure inside a cell affects only its customers. With 10 cells, a bad deployment to one cell exposes 10% of customers, and you can stop. The cost is operational: more instances of everything, a router that is now critical, and rebalancing data between cells.

**Shuffle sharding.** Instead of assigning each customer to one shard, assign each to a random small *subset* of workers. Suppose 8 workers and each customer uses 2 of them. The number of possible pairs is `C(8,2) = 28`. A poison customer who crashes its workers takes down its 2; another customer is fully affected only if they share *both*, which has probability `1/28 ≈ 3.6%`, and clients can retry on their other worker so even those two often survive partially. By contrast with plain sharding in 4 groups of 2, the affected fraction is 25%. More workers per pool and larger combinations drive the shared-fate probability down quickly.

```text
Workers: 8     Subset size: 2     Combinations: C(8,2) = 28
Plain 4 shards of 2:      one poison customer impacts 25% of customers
Shuffle sharding (2 of 8): one poison customer fully impacts about 3.6% of customers
```

**Deployment blast radius.** Treat every change as an experiment with a radius: one task, one cell, one AZ, one region, everything, in waves with bake time between them and automatic halt on alarm. Configuration, feature flags, certificates and infrastructure changes are deployments too, and many of the largest outages were configuration changes that reached everything at once.

| Wave | Scope | Bake time | Gate |
| --- | --- | --- | --- |
| 0 | Test environment | 1 h | Automated tests |
| 1 | One task in one cell | 30 min | Error ratio and latency within baseline |
| 2 | One AZ in one region | 2 h | Same, plus no new alarms |
| 3 | Remaining AZs in one region | 4 h | Same |
| 4 | Next regions, one at a time | 4 h each | Same |

**Account and organisational blast radius.** Separate accounts for production, recovery copies, logging and tooling. Limit the permissions that can delete backups or disable logging. Use organisation-level guardrails to prevent the most damaging actions even by administrators of one account. *Version-specific:* the available control mechanisms (service control policies, backup vault locks, resource-based policies) change; check current capabilities.

**Control-plane and quota blast radius.** An API rate limit, a quota or a control-plane event can stop recovery. Avoid recovery plans in which hundreds of resources must be created simultaneously; keep capacity pre-provisioned where recovery time matters, and pre-request quota increases in recovery regions.

## Resilience testing and game days

Move from single drills to game days and automated fault injection: instance termination, dependency latency and errors, AZ evacuation (using provider fault-injection tooling rather than altering configuration), expired credentials and certificates, quota exhaustion. Define steady-state metrics, hypothesis, blast-radius controls and abort conditions. Start in non-production; progress to production only with guardrails.

**Game day design (template).**

```text
Hypothesis:      With one AZ's tasks stopped, p99 latency stays under 800 ms and error ratio under 1%.
Steady state:    Request rate ~ normal; error ratio < 0.5%; p99 < 500 ms for the last 30 minutes.
Injection:       Stop all tasks in AZ-a using the provider's fault-injection service (scoped by tag).
Blast radius:    Staging, one service, business hours, on-call staffed, 20-minute duration.
Abort if:        Error ratio > 5% for 2 minutes, or any customer-facing alert in production-like tests.
Observers:       One person watching dashboards, one with the abort button, one recording the timeline.
After:           Record observed vs expected, action items with owners, update the failure-mode table.
```

Always define abort conditions *before* injecting; a test without them is just an outage you caused. Progress from staging to production only after you have repeatedly passed in staging, and start with the lowest-impact injection.

**A maturity ladder.**

| Level | Practice | Evidence produced |
| --- | --- | --- |
| 1 | Tabletop: walk through a failure on paper | Gaps in the runbook and ownership |
| 2 | Single-component drills in staging | Measured recovery times |
| 3 | Game days with several people and realistic load in staging | Cross-team timeline; action items |
| 4 | Automated, repeatable fault experiments with stop conditions | Regression evidence per release |
| 5 | Production experiments within a small blast radius | Real-world confidence; error budget spend |

**Hypothesis catalogue.** Start from questions whose wrong answers are expensive.

| Hypothesis | Injection | What a wrong answer reveals |
| --- | --- | --- |
| "Losing an AZ does not breach the SLO" | Stop all tasks in one AZ; optionally disrupt network connectivity for the AZ's subnets | Headroom, cross-AZ dependencies, the NAT trap |
| "Database failover is invisible to users" | Force a failover | Pool behaviour, retry idempotency, DNS caching |
| "A slow dependency degrades gracefully" | Inject 2 s latency into a dependency | Missing timeouts, retry storms, pool exhaustion |
| "We can recover from an expired credential" | Revoke or expire a credential in staging | Alert and rotation gaps |
| "We can scale out during an impairment" | Throttle API or exhaust a quota in staging | Reliance on control-plane actions |
| "Deploys halt on bad releases" | Ship a canary that returns errors on one route | Gates that detect only crash-class failures |
| "Restore meets RTO with tooling unavailable" | Restore with CI and a primary role disabled | Hidden dependencies on production tooling |

**Scoring a game day.** For each hypothesis record: *held*, *held with surprises*, or *failed*. A failed hypothesis with a good record is a successful game day. A game day that finds nothing is either an exceptionally good system or a poorly designed experiment; vary the injections.

## Architectural governance

Keep decisions in versioned records with revisit triggers; review architecture against reliability, security, cost, operational excellence, performance and sustainability; maintain a limitations register listing known gaps, impact, compensating controls and plan. Measure reality: postmortems feed the register.

**Limitations register (excerpt).**

| Limitation | Impact | Compensating control | Plan and date |
| --- | --- | --- | --- |
| Single-instance database in staging | Staging outage on failure | Daily snapshot; restore tested monthly | Not planned (non-production) |
| Failover untested for the production database | Unknown real RTO | Documented manual runbook | Test in the next quarter |
| Single deployment pipeline for all cells | Bad pipeline change reaches everything | Wave gates; break-glass procedure | Split pipelines by cell group, next half-year |

**ADR revisit triggers.** Each ADR names the conditions that reopen it: data size crossing a threshold (restore time exceeds RTO), traffic growth, a postmortem blaming the decision, a provider capability change, a cost shift, or a regulatory change.

**Decision test for a design review.** Ask for evidence, not configuration: a timeline from a drill, a restore with timestamps, a graph of latency during an instance kill. A design claiming AZ tolerance with no drill is a hypothesis.

## Disaster-recovery cases

Fictional composites, written to practise reasoning rather than to report events.

**Case 1: Regional impairment, warm standby.** `orders-api` runs in region R1 with a warm standby in R2: database replica with asynchronous replication (typical lag 2–5 s), a minimal task count in R2, DNS failover with 60 s TTL. A regional service impairment degrades R1's load balancing; checks fail.

| Time | Event |
| --- | --- |
| T+0 | Error ratio rises; alarm fires at T+3 min |
| T+8 | Incident commander declares regional failover after a decision call (the runbook requires human approval) |
| T+12 | Replica in R2 promoted; replication lag at the time was 4 s, so a few seconds of writes are at risk |
| T+15 | R2 tasks scaled from 2 to production count (pre-requested quota allowed it) |
| T+19 | DNS answers switch; clients move over the following minutes as TTLs expire |
| T+30 | 95% of traffic served from R2 |
| T+45 | Reconciliation: 11 orders found in R1's logs but not in R2; replayed manually |

What worked: static quota, rehearsed promotion, human gate against a false positive. What hurt: scale-up from 2 tasks took four minutes and a cold cache; the decision call took longer than the technical steps. Lessons: measure *decision time* as a recovery component; pre-scale more; automate the reconciliation query; failback was planned as a separate project with its own drill.

**Case 2: Credential compromise and deletion.** An attacker with a workload-account administrator role deletes the production database, its snapshots in that account and the log group. The same account contained the only backups.

Outcome in a design without separation: no restorable data. Outcome in the improved design: backups were copied to a separate recovery account under a locked vault with a retention period no workload role can shorten; the recovery account has no workload credentials. Recovery: new account bootstrap from code (3 h), restore from the vault (6 h for 4 TB, mostly copy time), key access validated beforehand, data six hours stale per the copy schedule. Lessons: **the backup chain's blast radius must not include the identity that can destroy production**; RPO is the copy schedule; recovery must be rehearsed in the recovery account with its own identity and keys; compromise changes the question from "how fast" to "can we trust what we restore".

**Case 3: Silent corruption.** A release introduces a rounding bug in a billing field; it is detected nine days later by a customer. Retention is seven days; monthly snapshots exist.

The nearest restore point containing correct data is the monthly snapshot from 21 days ago. Recovery is reconstruction: restore the monthly snapshot to a side instance, take the event log (retained 30 days) from that point, replay with the fixed code, compare to production, and apply corrections to the live database in controlled batches. Elapsed: 4 days of engineering, not hours. Lessons: retention below detection time removes clean points; event logs make reconstruction possible; the fix included a daily invariants check (totals reconcile to the ledger) cutting detection time to under a day, and retention was raised to 35 days for the database snapshots.

**Case 4: Gray failure in one AZ.** After a provider-side network degradation (below the status-page threshold), the packet loss on paths into AZ-b rises to 3%. Health checks pass. p99 latency doubles for users routed there; retries from the front tier increase load; databases show more connection resets. Dashboards by service look yellow, not red.

The signal that broke through: a comparison of per-AZ p99 latency and error ratio, which flagged AZ-b as an outlier three times the median. Action: shift traffic away from AZ-b by changing weights or draining, and watch the other AZs' headroom (they had it, because static capacity was sized for AZ loss). Lessons: per-AZ views are mandatory; the capacity that makes an AZ evacuation possible must already exist; rehearse "evacuate an AZ that is not dead".

## Expert trade-offs

| Tension | Considerations |
| --- | --- |
| More redundancy vs more complexity | Each redundant path is a component with its own failure modes; remove what you cannot test |
| Fast detection vs false positives | Aggressive checks remove healthy capacity during blips; apply caps and hold-down |
| Automation vs human gate for failover | Automation is fast but risks false failover; humans are slow but add judgement; choose per failure class |
| Headroom vs cost | Pre-provisioned capacity is the cost of static stability; quantify it against expected loss |
| Cells vs consolidation | Cells reduce blast radius and raise operating cost; choose granularity by customer impact |
| Retention vs cost and privacy | Longer retention improves recoverability and increases cost and regulatory exposure |
| Multi-region vs multi-account | Many incidents are account-level; separation of accounts is often a better first step than a second region |

## Knowledge consolidation

- Availability maths is a model: series multiplies, parallel helps only with independence, and the common-cause term `β · u` usually dominates.
- Cutting MTTR is typically cheaper than extending MTBF; fan-out multiplies both unavailability and tail latency.
- Gray failures pass binary checks; find them with per-target and per-AZ comparison, with caps against false ejection.
- Overload and metastability are sustained by feedback loops (retries, cold caches); break the loop, not just the trigger.
- A failover mechanism is a component: it has latency (detection plus TTL), control-plane dependencies and false-positive risk.
- Durability covers infrastructure loss, not deletion, corruption, key loss or account compromise.
- Data recovery is limited by throughput, retention versus detection time, and the last known-good point; recovery has its own dependencies.
- Blast radius is reduced by cells, shuffle sharding, staged deployment and account separation.
- Game days produce evidence; claims without evidence are hypotheses.

## Mentoring prompts

Your design claims AZ-failure tolerance; what evidence, not configuration, would you demand before believing it? Why can adding a second region reduce overall availability? How would you decide, with numbers, whether to invest in multi-region? A teammate says "the data is in eleven-nines storage, so we do not need backups"; how do you respond? Your retention is seven days and your slowest-detected incident took ten; what do you change?

## Exercises

**Exercise 1 — Series and parallel with correlation.** Components: load balancer 99.99%, three tasks each 99.9%, database 99.95%. Compute system availability assuming independence and assuming a common-cause fraction β of 0.05 for the tasks (for three tasks use `u_tasks ≈ β·u + ((1 − β)·u)³`). State which assumption you would defend and why.

**Exercise 2 — MTTR versus MTBF.** A service fails every 45 days on average and takes 2 hours to recover. Compute availability. Compare with halving MTTR and with doubling MTBF. Which investment is likely cheaper and why?

**Exercise 3 — Fan-out.** A page calls 12 backends, each 99.95% available. Compute the page's availability if all are hard dependencies. Then if three are made soft (with fallbacks that always succeed). Compute the probability that at least one of 12 backends exceeds its p99 latency.

**Exercise 4 — Restore bounds.** Database 8 TB, sustained restore throughput 400 MB/s, validation 30 minutes, cutover 20 minutes. Compute the minimum RTO for a restore-based recovery. State what you would change to hit a 2-hour RTO.

**Exercise 5 — Retention.** Detection time for logical corruption is typically 3 days, with a worst case of 12 days; decision time up to 1 day. Set retention for daily database restore points, and state what else you would keep.

**Exercise 6 — Shuffle sharding.** A pool has 12 workers; each tenant uses 3. Compute the number of distinct assignments and the probability that a random second tenant shares all three workers with a poison tenant. Compare with 4 plain shards of 3.

**Exercise 7 — Game day.** Write a complete game-day plan for the hypothesis "a slow database degrades `orders-api` gracefully": steady state, injection, abort conditions, observers, expected result and the single most likely failure.

**Exercise 8 — DR reasoning.** Choose a recovery strategy for a workload whose outage costs 30,000 per hour, with a regional loss expected once per 20 years, 3-hour restore-based recovery, and warm standby costing 90,000 per year. Compute expected annual loss for each and discuss what the calculation leaves out.

**Solution notes.**

*Exercise 1.* Independent: tasks in parallel `1 − 0.001³ = 1 − 10⁻⁹`; series `0.9999 × (1 − 10⁻⁹) × 0.9995 ≈ 0.99940`, 99.94%. With β = 0.05: `u_tasks ≈ 0.05 × 0.001 + (0.95 × 0.001)³ ≈ 5 × 10⁻⁵ + 8.6 × 10⁻¹⁰ ≈ 5 × 10⁻⁵`, so tasks ≈ 99.995%; series ≈ `0.9999 × 0.99995 × 0.9995 ≈ 0.99935`, 99.93%. The database dominates in both cases, and the difference between assumptions is small *because* the database already caps the system; the correlation matters more when the replicated tier is the weakest link.

*Exercise 2.* `A = 45 d / (45 d + 2 h)`: 1,080 h / 1,082 h = 99.815%. Halving MTTR (1 h): 1,080 / 1,081 = 99.907%. Doubling MTBF (90 d): 2,160 / 2,162 = 99.907%. Equal effect here; halving MTTR (automation, runbooks) is usually the cheaper lever because MTBF depends on change rate and external factors.

*Exercise 3.* `0.9995^12 ≈ 0.99402`, 99.40%. With nine hard: `0.9995^9 ≈ 0.99551`, 99.55%. Slow response: `1 − 0.99^12 ≈ 11.4%`.

*Exercise 4.* 8 TB = 8,000,000 MB / 400 MB/s = 20,000 s ≈ 5.6 h, plus 50 min, so about 6.4 h minimum. To reach 2 h: shrink what must be restored first (partition or cell, restore the hot subset first), raise parallelism, keep a warm replica or delayed replica, or accept a different objective for that failure class.

*Exercise 5.* Retention ≥ 12 days + 1 day + margin, for example 21 days of daily points. Also keep monthly or weekly long-term snapshots, and an event log long enough to replay.

*Exercise 6.* `C(12,3) = 220` assignments; probability of sharing all three with the poison tenant is `1/220 ≈ 0.45%`. Plain 4 shards of 3: 25% share the shard.

*Exercise 7.* Look for: steady state with numbers; injection through latency (not an outage); an abort condition tied to a user-facing alarm; observers with defined roles; expected result such as degraded p99 with cache serving; most likely failure: missing timeout and retries causing pool exhaustion (Little's law).

*Exercise 8.* Restore-based: expected loss `3 h × 30,000 / 20 = 4,500` per year. Warm standby with, say, 15-minute recovery: `0.25 × 30,000 / 20 = 375` plus 90,000 cost, so the expected loss avoided (about 4,125 per year) is far smaller than the 90,000 cost: warm standby is not justified on regional-loss expectation alone. The calculation leaves out other benefits (the standby also helps with partial regional problems, bad deployments if used for blue/green, regulatory requirements), reputational damage, variance in outage length and the chance that the restore path fails when needed.
