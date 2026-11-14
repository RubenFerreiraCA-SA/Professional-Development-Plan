# T-DEV-06-E — Expert Depth

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-e"></a>
#### T-DEV-06-E — Expert Depth

**Reliability engineering as risk management.** Error budgets turn reliability into a decision tool: while budget remains, ship; when it is exhausted, prioritise reliability work. That only works if the SLO reflects user experience, the data is trustworthy and leadership honours the policy. Choose targets deliberately: each extra nine costs disproportionately, and a dependency chain's availability is the product of its parts.

**Burn-rate mathematics.** For a 30-day window and a 99.9% SLO, a burn rate of 1 consumes the budget exactly at window end. A burn rate of 14.4 for one hour consumes 2% of the 30-day budget; commonly, alerts pair a long and a short window (for example 1 hour and 5 minutes) at a high burn rate for paging, and longer windows at lower rates for tickets. The short window makes the alert reset quickly after recovery; the long window prevents paging on blips.

**Measurement pitfalls**

| Pitfall | Effect | Remedy |
| --- | --- | --- |
| Averaging percentiles | Wrong tail latency | Merge histograms, then compute |
| Sampling bias | Traces skew toward errors or toward fast requests | Tail-based sampling by policy, plus metrics for rates |
| Coordinated omission | Load tests under-report latency | Open-loop load generators |
| Missing data treated as healthy | Silent failure of telemetry | Alert on absence of data; heartbeat series |
| Client vs server perspective | Server sees only requests that arrived | Synthetic probes and client-side measurement |
| Cardinality blow-up | Cost spikes, slow queries | Deny-lists, budgets, per-tenant limits |

**Sampling strategy.** Head-based sampling decides at the start of a trace and is cheap but blind to outcome. Tail-based sampling decides after seeing the whole trace and can keep all errors and slow traces, at the cost of buffering and operational complexity. Always keep metrics unsampled for rates.

**Scale and governance.** Standardise semantic conventions and resource attributes organisation-wide; version the telemetry contract; treat telemetry schema changes like API changes. Control spend with per-team budgets and showback. Define retention tiers (hot, warm, archive), access control for sensitive logs and a process for deletion on request.

**Reliability beyond telemetry.** Observability reveals problems; it does not prevent them. Pair it with capacity planning, graceful degradation, timeouts, retries with jitter and budgets, circuit breakers, load shedding and game days in which someone other than the author injects a failure and the on-call follows the runbook alone. Convert each confusion into a platform fix.

**The cost of nines, in minutes.** Convert targets to allowed downtime before choosing one.

| SLO | Error budget (30 days) | Allowed full outage | What it typically demands |
| --- | --- | --- | --- |
| 99% | 1% | about 7 h 12 min | Basic redundancy; manual recovery acceptable |
| 99.9% | 0.1% | about 43 min | Automated failover, safe deploys, 24/7 response |
| 99.99% | 0.01% | about 4 min 19 s | Multi-AZ everywhere, automatic remediation, no manual step in recovery |

A dependency chain multiplies: three components each at 99.9% give about 99.7% overall (0.999³), so you cannot promise 99.9% to users if you hard-depend on three such services without redundancy. Choose a target from what users notice and what the business will fund; a target tighter than the weakest dependency is a promise you cannot keep.

**An error-budget policy that people follow.**

```text
Budget remaining > 50%:   normal release cadence.
Budget remaining 10-50%:  releases need a rollback plan reviewed by the on-call; reliability items prioritised.
Budget exhausted:         feature releases paused (security and reliability fixes only) until the 30-day
                          window recovers or the product owner and engineering lead record an explicit exception.
Review:                   monthly, with the SLI definition, data quality and exceptions list.
```

The policy works only when someone with authority has agreed to it before the budget is spent. Write the exception path too: an unrecorded exception is how policy dies.

**Burn-rate alert table (30-day, 99.9% SLO).**

| Burn rate | Budget consumed if sustained for | Time to exhaust the whole budget | Alert |
| --- | --- | --- | --- |
| 14.4 | 2% in 1 hour | 50 hours | Page: long window 1 h and short window 5 min both above 14.4 |
| 6 | 5% in 6 hours | 5 days | Page or urgent ticket: 6 h and 30 min windows both above 6 |
| 3 | 10% in 1 day | 10 days | Ticket: 1 day and 2 h windows |
| 1 | 100% in 30 days | 30 days | Trend report |

Arithmetic: burn rate × (alert window ÷ SLO window) = fraction of budget consumed; 14.4 × (1/720) = 2%. The long window prevents paging on brief spikes; the short window lets the alert clear within minutes after recovery, so on-call is not paged for a problem that is already over.

**Low-traffic systems.** At night a service with 10 requests per hour can show 100% errors from a single failed request. Alert on absolute error counts plus ratio, use longer windows, add synthetic probes to keep a baseline of traffic, and evaluate the SLO across the whole window instead of a short slice.

**Diagnosing "SLO met, users angry".**

| Possible cause | Check |
| --- | --- |
| SLI measures the load balancer, not the user's experience | Add client-side or synthetic measurement |
| Aggregate hides a segment (one region, one customer tier) | Break down by dimension; SLOs per critical journey |
| Latency percentile too lenient (p50 instead of p99) | Review the threshold against complaints |
| Failures counted as "successes" (a 200 with an error body) | Define success with business semantics |
| Client retries mask failures but slow users | Measure time to success, including retries |

**Percentile arithmetic.** Averaging two instances' p99s is wrong: if instance A has p99 = 200 ms over 1,000 requests and B has p99 = 2,000 ms over 10, the fleet p99 is closer to A's. Aggregate histograms (buckets) first, then calculate the quantile. Coordinated omission example: a load tool that waits for each response before sending the next, when the server stalls for 10 s, records one slow request instead of the hundreds it should have sent in that interval, hiding the stall.

**Cost of keeping everything, and what sampling loses.** 1,000 requests per second with 20 spans of 1 KB is about 20 MB/s, roughly 1.7 TB per day for traces alone. Tail-based sampling that keeps all errors, all requests above the latency objective, and 2% of the rest typically reduces this by more than 90%, at the cost of: not being able to inspect an arbitrary healthy request later, collector memory for buffering traces until they complete, and an operationally harder pipeline. Keep metrics derived from *unsampled* data for rates, so SLOs do not depend on the sampling policy.

**Game day, minimal protocol.** Someone other than the author injects a failure (kill a dependency, add latency); the on-call follows the runbook alone, with no hints; an observer records every time the runbook was ambiguous, a dashboard was missing, or an alert did not fire. Each such note becomes a tracked fix. Success is measured by how many fixes the exercise produced, not by whether it went smoothly.

**Mentoring prompts.** Your SLO is met and users are angry — what is wrong with the SLI? How would you design alerting for a system whose traffic is near zero at night? What does it cost to keep every trace, and what do you lose by sampling?

---
