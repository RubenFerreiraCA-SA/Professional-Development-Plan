# T-CLD-05-E — Expert Depth

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-e"></a>
#### T-CLD-05-E — Expert Depth

**Quantifying availability.** Components in series multiply availability (0.999 × 0.999 ≈ 0.998); redundancy in parallel improves it only if failures are independent and failover works. Shared dependencies (a single database, one DNS provider, a global control plane, one deployment pipeline) cap overall availability and create correlated failure. Draw the dependency graph and mark hard dependencies.

**Failure-mode analysis.** For each component, list: failure mode, detection, impact, mitigation, owner. Include gray failures — partial degradation that passes health checks but harms users (slow disks, packet loss, thread pool exhaustion). Health checks should exercise realistic paths with timeouts, without causing cascading restarts when a dependency blips.

**Multi-AZ and multi-region patterns**

| Pattern | Recovery | Cost and complexity |
| --- | --- | --- |
| Single region, multi-AZ active-active | Automatic for AZ loss | Moderate |
| Backup and restore in another region | Hours | Low |
| Pilot light (minimal copy running) | Tens of minutes | Moderate |
| Warm standby | Minutes | High |
| Multi-region active-active | Near zero for data planes | Very high; data consistency and routing challenges |

Choose by business impact and tested capability. Active-active multi-region requires conflict handling, global routing, and operating the failover regularly; an untested failover is a hope.

**Resilience testing.** Move from single drills to game days and automated fault injection: instance termination, dependency latency and errors, AZ evacuation (using provider fault-injection tooling rather than altering configuration), expired credentials and certificates, quota exhaustion. Define steady-state metrics, hypothesis, blast-radius controls and abort conditions. Start in non-production; progress to production only with guardrails.

**Overload and degradation.** Systems fail more often from overload than from component death. Techniques: admission control and load shedding, bulkheads, priority queues, backpressure, adaptive concurrency limits, and graceful degradation (serve cached or reduced content). Retries amplify load; budget them. Autoscaling lags demand, so keep headroom and protect cold start.

**Architectural governance.** Keep decisions in versioned records with revisit triggers; review architecture against reliability, security, cost, operational excellence, performance and sustainability; maintain a limitations register listing known gaps, impact, compensating controls and plan. Measure reality: postmortems feed the register.

**Availability arithmetic, worked.** Suppose `orders-api` needs a load balancer (99.99%), two identical tasks in different AZs (each 99.9% independently), and one database (99.95%).

| Component | Calculation | Availability |
| --- | --- | --- |
| Two tasks in parallel | 1 − (0.001 × 0.001) | 99.9999% |
| Series: load balancer × tasks × database | 0.9999 × 0.999999 × 0.9995 | about 99.94% |

The database alone caps the system near 99.95%, no matter how many tasks you add. Redundancy helps only the part that is replicated. The parallel calculation also assumes independence and that failover works; a shared deployment or a common bad release makes both tasks fail together, so the real figure is lower. Convert to downtime to make the point: 99.94% is about 26 minutes per 30 days; 99.99% is about 4 minutes.

**Failure-mode table, with a gray failure.**

| Mode | Detection | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| Task crash | Scheduler event; target health drops | Brief capacity loss | Desired count ≥ 2 across AZs | Platform |
| AZ outage | Load balancer health per AZ; provider health | Up to half capacity | Capacity headroom (each AZ can carry the load) | Platform |
| Database failover | Replication and connection errors | Seconds to minutes of write failure | Retries with jitter; idempotent writes; tested failover | Service team |
| **Gray: disk latency rising on one task** | p99 latency per task; error budget burn; **health check still 200** | Slow responses for ~half the users | Outlier detection, latency-aware health checks, auto-replace slow targets | Service team |
| **Gray: thread-pool exhaustion** | Queue depth and in-flight request metrics | Timeouts that look like network errors | Concurrency limits, load shedding, bulkheads | Service team |
| Expired certificate | Days-to-expiry metric | Hard outage at expiry | Automated renewal and alert at 21 days | Platform |

Gray failures are dangerous because every binary check says "healthy" while users suffer. The defence is measuring the user-visible experience (latency percentiles, error ratio per target) and comparing instances with each other.

**Choosing a recovery strategy with cost reasoning.**

| Strategy | Typical RTO | Typical RPO | Steady-state cost | Complexity to operate | Suits |
| --- | --- | --- | --- | --- | --- |
| Multi-AZ in one region | Seconds to minutes | Near zero with sync replication | Moderate | Low | Most production workloads |
| Backup and restore elsewhere | Hours | Backup interval | Low | Low (but must be rehearsed) | Tolerant business processes |
| Pilot light | Tens of minutes | Replication lag | Low–moderate | Moderate | Important workloads, moderate downtime tolerance |
| Warm standby | Minutes | Seconds–minutes | High | High | Critical workloads with strong justification |
| Multi-region active-active | Near zero | Near zero in theory; conflicts in practice | Very high | Very high: conflict resolution, global routing, regular failover practice | Rare; only when impact justifies it |

Write the justification as: "Impact of an hour of outage is X; the probability of regional loss is Y per year; option Z reduces expected downtime by W hours at cost C." Include a *why not more* line, which stops architecture drifting upward without evidence.

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

**Overload: why retries bring systems down.** If a dependency slows and each of three layers retries three times, a single user request can become 27 requests to the dependency exactly when it is least able to cope. Controls: a *retry budget* (retries limited to a fraction of original traffic, for example 10%), exponential backoff with jitter, timeouts shorter than the caller's timeout, circuit breakers and load shedding that rejects low-priority work early with a clear 503. Autoscaling lags demand by minutes, so size headroom for the time to scale and protect cold start.

**Limitations register (excerpt).**

| Limitation | Impact | Compensating control | Plan and date |
| --- | --- | --- | --- |
| Single-instance database in staging | Staging outage on failure | Daily snapshot; restore tested monthly | Not planned (non-production) |
| Failover untested for the production database | Unknown real RTO | Documented manual runbook | Test in the next quarter |

**Decision test for a design review.** Ask for evidence, not configuration: a timeline from a drill, a restore with timestamps, a graph of latency during an instance kill. A design claiming AZ tolerance with no drill is a hypothesis.

**Mentoring prompts.** Your design claims AZ-failure tolerance; what evidence, not configuration, would you demand before believing it? Why can adding a second region reduce overall availability? How would you decide, with numbers, whether to invest in multi-region?

---
