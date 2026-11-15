# T-DEV-06-E — Expert Depth

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-e"></a>
#### T-DEV-06-E — Expert Depth

## Why this level exists

Professional practice gives you SLOs, error budgets, burn-rate alerts, incident response and postmortems. Expert practice asks where those tools stop being true. The SLO is met and customers are angry. The dashboards are green because the telemetry pipeline died with the service. One instance in four hundred is broken and no alert can see it. A sampling policy that saved money hid the only trace of the bug. An alert that was correct on average pages the same person eleven times a quarter for nothing. And at the top of the organisation someone has to decide, with incomplete data and a clock running, whether to roll back, freeze releases or tell customers.

The skill is not recalling more configuration. It is **predicting how an accepted practice fails**, pricing the cost of the controls you add, and choosing the cheapest control that addresses the failure that matters. This section assumes the earlier levels: the three signals, histograms, label cardinality, SLI specifications, burn rates, the error-budget policy, blameless postmortems. It uses the neutral `orders-api` service. Calculations are exact on stated assumptions; figures labelled *illustrative* (prices, bytes per sample, memory per series) are orders of magnitude to be replaced with your own measurements. Nothing depends on any other course material.

## Reliability engineering as risk management

An error budget is a way of making a risk decision *before* the pressure arrives. While budget remains, take product risk and ship; when it is gone, spend effort on reliability. That mechanism works only under four conditions, and most failures of "SLO programmes" are failures of one of them.

| Condition | What breaks if it fails | Test |
| --- | --- | --- |
| The SLI reflects what users experience | You optimise a number users do not feel; "SLO met, users angry" | Compare SLO state with support contacts and churn over six months |
| The data is trustworthy and complete | Budget accounting is wrong in either direction | Reconcile the SLI against an independent source (load balancer logs versus application metrics) |
| The policy was agreed in advance by someone with authority | The first freeze is overridden and the number stops meaning anything | Is there a signed policy and a recorded exception path? |
| The target is achievable and funded | Permanent exhaustion; the freeze becomes the normal state and is ignored | How many windows in the last year ended with budget exhausted? |

**The cost of nines.** Each extra nine divides the allowed failure by ten but roughly multiplies the cost of delivery by more than ten, because it demands removal of every manual step, redundancy across independent failure domains, and a faster response than humans can give. Convert to minutes before choosing: 99.9% over 30 days permits 43.2 minutes of full outage; 99.99% permits 4.32 minutes, less than a typical human paging cycle (acknowledge, log in, find the dashboard). A 99.99% target is therefore a promise that *recovery is automatic* or that the promise will usually be broken. Choose from what users notice and what the business will fund; a target tighter than your weakest hard dependency is a promise you cannot keep.

**A target is a product decision with a price.** Present options as a table, not a number:

| Option | Error budget (30 days) | Required engineering | Indicative cost multiplier | Customer-visible effect |
| --- | --- | --- | --- | --- |
| 99.5% | 3 h 36 min | Current design plus safe deploys | 1× | Occasional visible outage |
| 99.9% | 43 min | Automated failover, canary, 24/7 on-call | 2–3× | Rare visible outage |
| 99.99% | 4.3 min | Multi-region active-active, no manual step | 10× or more | Outages largely invisible |

The multipliers are illustrative; the point is that the product owner, not the engineer, should choose a row *knowing the price*.

## Telemetry economics: sampling and cardinality

Telemetry is a production workload with its own cost, scaling behaviour and failure modes. At scale, the decisions that matter most are what you keep, for how long, and how much each extra dimension costs.

### The volume arithmetic

**Logs.** `orders-api` at 2,000 requests per second writes three 400-byte lines per request: 2,000 × 3 × 400 B = 2.4 MB/s, which is 2.4 × 10⁶ × 86,400 ≈ **207 GB per day**. At an illustrative ingestion price of $0.50 per GB that is about $104 per day, roughly $3,100 per month, before storage and query costs, and the bill grows linearly with traffic. Halving debug noise saves more than most optimisations to the service itself.

**Traces.** At 1,000 requests per second with 20 spans of 1 KB each: 1,000 × 20 × 1 KB = 20 MB/s = **1.73 TB per day**. Keeping everything is rarely justified.

**Metrics.** A metric's cost scales with *series*, not events. One series sampled every 15 seconds produces 86,400 ÷ 15 = 5,760 samples per day. A histogram with 10 finite buckets, `+Inf`, `_sum` and `_count` is 13 series per label combination; 3,200 combinations give 41,600 series and 41,600 × 5,760 ≈ 240 million samples per day. At an illustrative 1.5 bytes per compressed sample that is about 360 MB per day on disk — modest — but *memory* is the binding constraint, since each active series costs an illustrative 2–4 KB of memory. Then 41,600 series need about 125 MB (at 3 KB), whereas 160 million series would need about 480 GB, which no single server holds. Metrics are cheap until cardinality is unbounded, and then they are not cheap at all.

### Head sampling: cheap, blind and statistically manageable

**Head-based sampling** decides at the start of a trace whether to record it, typically with a fixed probability *p*. It is cheap (no buffering) and consistent (every service honours the decision in the propagated flags), but it is blind to outcome: it discards errors and slow requests at the same rate as healthy ones.

Two quantitative consequences.

1. **Rare events vanish.** If a defect affects 20 requests per day and you sample at *p* = 5%, the probability that *none* of those 20 requests is captured is 0.95²⁰ ≈ **0.36**. More than a third of the time you will have no trace of the bug on a given day. With 100 occurrences it falls to 0.95¹⁰⁰ ≈ 0.006. Head sampling is good for common behaviour and poor for rare failures.
2. **Counts need weighting, and precision depends on the sample size.** Each retained trace represents 1/*p* = 20 requests. If you observe 31 sampled errors, you estimate 31 × 20 = 620 errors, but the relative standard error of a count of *n* sampled events is about 1/√*n* = 1/√31 ≈ 18%, so the true number plausibly lies in 510–730. To know a rate within 10% you need about 100 sampled events. This is why **rates and SLOs must come from unsampled metrics**, not from traces.

### Tail sampling: expensive, targeted and operationally heavy

**Tail-based sampling** waits for the complete trace and then decides, so it can keep all errors and all slow traces. It costs real engineering:

| Cost | Detail |
| --- | --- |
| Buffering | Collectors hold every span until the trace completes (or times out); memory scales with traffic × trace duration |
| Routing | All spans of one trace must reach the same collector instance (consistent hashing by trace id), or the decision is made on partial data |
| Late spans | A span arriving after the decision is dropped or orphaned |
| Policy complexity | Policies interact; a rule that keeps "all traces over the objective" can explode during an incident |
| Failure mode | A collector restart loses the buffer; an overload drops traces exactly when you most need them |

A worked policy for `orders-api`: keep all error traces (0.3% of requests), keep all traces above the latency objective (1.0%, assumed disjoint from errors), and keep 2% of the remainder. Kept fraction = 0.3% + 1.0% + 98.7% × 2% = 3.27%. Storage falls from 1.73 TB to about **57 GB per day**, a reduction of nearly 97%. What you lose is the ability to inspect an arbitrary healthy request later, plus a pipeline that is harder to run.

**Guard the policy against incidents.** If a dependency fails and 40% of requests become "slow" or "error", the policy keeps about 41% of traces instead of 3.3%, a twelve-fold increase in volume at the moment the collector is under most stress. Add a rate cap per policy and a fallback to probabilistic sampling when the cap is hit, and *alert when the cap is reached*, because from that point the sample is no longer representative.

### Cardinality as a budget

Treat series count like any other scarce resource: budget, report, review.

**A worked review.** A team has a budget of 200,000 active series and uses 150,000. A developer proposes adding a `tenant` label (30 values) to a metric that currently has 2,000 series. The metric becomes 2,000 × 30 = 60,000 series, an increase of 58,000. The team would reach 208,000, exceeding its budget by 8,000. Options: drop another label with low diagnostic value; restrict `tenant` to the top five tenants plus `other` (2,000 × 6 = 12,000 series, +10,000, total 160,000, within budget); or record per-tenant detail in logs and traces instead. The review turns a vague worry into a number that can be decided.

Controls, in order of preference: an allow-list of labels in the instrumentation library; enforcement in the Collector (drop or aggregate offending labels); per-tenant or per-team series limits at the backend that *fail the write for the offender* rather than crash the system for everyone; a dashboard of the top series growers with a named owner.

**Wide events versus metrics.** A different design stores one rich event per request (many attributes, high cardinality) in a columnar store and derives aggregates by query. That moves the cost from series count to event volume and gives flexible exploration, at the price of sampling for volume and slower, costlier aggregation than pre-computed metrics. Neither wins in general: pre-aggregated metrics for SLOs and alerts (cheap, reliable, fast), rich events or traces for exploration (flexible, sampled).

### Retention and tiers

| Tier | Contents | Typical retention | Notes |
| --- | --- | --- | --- |
| Hot | Recent metrics, logs, traces at full resolution | Days to two weeks | Fast queries; most expensive |
| Warm | Downsampled metrics, sampled traces, compressed logs | Weeks to months | Trend and capacity analysis |
| Archive | Audit logs and compliance records | Years, as required | Access controlled; restore tested |

Match retention to the question's lifetime: incident diagnosis needs days; capacity planning needs a year of coarse metrics; audit needs what the rules demand. Include a deletion process for personal data on request and test it.

## Measurement pitfalls

| Pitfall | Effect | Remedy |
| --- | --- | --- |
| Averaging percentiles | Wrong tail latency | Merge histogram buckets, then compute the quantile |
| Sampling bias | Traces skew toward errors or toward fast requests | Tail policy by design; rates from unsampled metrics |
| Coordinated omission | Load tests under-report latency | Open-loop load generators |
| Missing data treated as healthy | Silent failure of telemetry | Alert on absence; heartbeat series |
| Client versus server perspective | Server sees only requests that arrived | Synthetic probes and client-side measurement |
| Cardinality blow-up | Cost spikes, slow queries | Allow-lists, budgets, per-tenant limits |
| Rate over a window shorter than the scrape interval | Gaps and spurious zeros | Window of at least four scrape intervals |
| Counter resets during rollouts | Spurious spikes or dips on aggregation | Use rate functions; avoid summing raw counters |

**Percentile arithmetic.** Averaging two instances' p99s is wrong. Instance A handles 1,000 requests with p99 = 200 ms; instance B handles 10 requests with p99 = 2,000 ms. The simple average is 1,100 ms, but B is under 1% of requests, so the fleet p99 is about 200 ms, close to A's, and at most the 10 slowest of B's requests can sit above it. Aggregate buckets first.

**Coordinated omission, in numbers.** A closed-loop load tool sends one request, waits for the response, then sends the next, at a target of 100 requests per second. The server stalls for 10 seconds. The tool records *one* 10-second latency and then resumes at 100 per second. A correct open-loop generator would have sent 1,000 requests during the stall, each of which would have waited between 0 and 10 seconds, averaging about 5 seconds. The closed-loop test reports a 99.9th-percentile latency that looks fine; reality was a 10-second outage for every client during that interval.

**Time-based versus request-based.** A synthetic probe once a minute gives 43,200 probes in 30 days; a 99.9% objective allows 43 failed probes. One probe equals one minute of outage, regardless of traffic at that moment. That is acceptable for availability of a journey with low traffic, but it cannot say how many real users were affected. Use probes to *detect* and request-based SLIs to *account*.

## Incomplete telemetry

Every observability system is a model of the system built from partial, delayed, possibly corrupted data. Experts reason about *what the data cannot say*.

### Failure modes of telemetry

| Failure | What you see | What is actually happening | Defence |
| --- | --- | --- | --- |
| Survivorship | Latency looks fine | Crashed or timed-out requests emit no latency sample | Count started requests as well as finished ones; client-side timing |
| Telemetry shares fate with the service | Dashboards freeze or go empty during the outage | Metrics pipeline runs in the failing cluster or network | Out-of-band probes; heartbeat to an independent system |
| Silent exporter drop | A metric disappears or flatlines | Queue full, exporter blocked, credentials expired | Alert on `up`, last-sample age and exporter drop counters |
| Clock skew | Spans appear to end before they start; events out of order | Hosts disagree about time | Time synchronisation monitoring; rely on span relationships, not wall clocks |
| Broken propagation | Orphan spans, truncated traces | A proxy strips headers; an async hop loses context | Propagation tests in CI; alert on the share of root spans that are not entry points |
| Late data | Graphs revise themselves after the fact | Batch delivery, delayed scrapes, backfill | Evaluate alerts on data older than the expected delay; do not trust the last minute |
| Log loss under pressure | Missing lines during the incident | Disk full, agent back-pressure, rate limiting | Per-source drop counters; sample deliberately rather than drop accidentally |
| Redaction or filtering mistakes | A field is always empty | An overly broad scrubbing rule | Test the pipeline with golden samples |

**Absence is a signal that must be detected on purpose.** A threshold alert on an error ratio says nothing if the denominator disappears. Pair every important symptom alert with an absence alert, and keep a **dead man's switch**: an alert that always fires, routed to an external system that pages when it *stops* arriving. If the monitoring system itself dies, the missing heartbeat is the alarm.

```yaml
groups:
  - name: meta-monitoring
    rules:
      - alert: Watchdog
        expr: vector(1)
        labels: { severity: heartbeat }
        annotations: { summary: "Always firing; the external receiver pages if it stops" }
      - alert: OrdersTelemetryMissing
        expr: absent_over_time(http_requests_total{service="orders-api"}[5m])
        for: 1m
        labels: { severity: page }
        annotations:
          summary: "No orders-api request metrics for 5 minutes"
          runbook_url: https://runbooks.example.com/orders-telemetry-missing
```

### Reasoning when the data is incomplete

Separate **observation** (what a signal shows), **inference** (what you conclude) and **assumption** (what you have not verified). In an incident log write them as different kinds of line, so that when a conclusion fails you can see which assumption carried it. Attach a rough confidence to each hypothesis, and name the cheapest observation that would change your mind. When the telemetry is the suspect, check it against an independent path: compare load balancer counts with application counts; compare a synthetic probe with real traffic; read one raw log line to confirm the dashboard.

## Gray failures

A **gray failure** is a degradation that the system's own health checks do not detect but that users experience: partial, intermittent or confined to a subset of requests. The definition is relational: the failure is *observable to clients and invisible to the component that is supposed to detect failure.*

Examples: one instance of twenty with a corrupted cache; a single availability zone with elevated latency to a dependency; a TLS handshake failing for one client library version; a database replica that serves stale reads; a disk that is slow but not failed; a thread pool at 98% occupancy with response times creeping up while the process is "healthy".

### Why fleet aggregates hide them

Suppose one instance returns errors for every request and all instances receive equal traffic. The fleet-wide error ratio is 1/*N*. Against a 99.9% SLO (burn rate = ratio ÷ 0.001):

| Fleet size *N* | Fleet error ratio | Burn rate | Fast page (14.4)? | Slow page (6)? | Ticket (3)? | Budget gone in |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | 5% | 50 | Yes | Yes | Yes | 14.4 h |
| 100 | 1% | 10 | No (1% is under 1.44%) | Yes, after about 3.6 h | Yes | 3 days |
| 400 | 0.25% | 2.5 | No | No | No | 12 days |

For *N* = 100 the slow page fires when the six-hour average passes 0.6%, which takes 0.6 ÷ 1.0 × 6 h = 3.6 h at a 1% error ratio, by which time 5% of the monthly budget (0.01 × 3.6 ÷ 720 ÷ 0.001 = 5%) is gone. For *N* = 400 no alert fires at all, yet the service burns 8.3% of its budget per day, and if clients stick to instances, 0.25% of users have a service that *never* works for them. The aggregate SLO is a population average; individuals experience particular instances, zones and tenants.

### Detecting gray failures

| Technique | What it catches | Cost |
| --- | --- | --- |
| Per-instance outlier detection (compare each instance to the fleet median) | One bad instance, node or version | Per-instance series; careful threshold |
| SLIs per zone, per tenant tier, per client version | Localised degradation | More series and more alert rules; budget them |
| Client-side or edge measurement | Failures the server never sees | Client telemetry pipeline |
| Synthetic probes from multiple vantage points | Path-specific failures | Probe design and ownership |
| Deep health checks that exercise real dependencies | Corrupted cache, broken credentials | A health check that is itself a failure risk and load |
| Automatic ejection of outliers by the load balancer | Reduces impact while humans investigate | Risk of ejecting too many (capacity collapse); cap the ejected fraction |
| Differential comparison (canary versus baseline) | Behavioural regressions in a new version | Needs enough canary traffic to be statistically meaningful |

The principle: **do not rely on one aggregate; ask whether every segment you care about is separately visible**, and accept that each segment multiplies your series count.

### Retries mask failures and multiply load

Clients that retry hide transient failures at the cost of added load and latency. If each attempt fails independently with probability 0.2 and there are up to 3 attempts, the user-visible failure probability is 0.2³ = **0.8%** (99.2% success), and the expected number of attempts per request is 1 + 0.2 + 0.2² = **1.24**, so 24% extra load. That is a good trade for independent blips. When failures are *correlated* (a dependency is down, so the probability of failure is 1), every request makes 3 attempts: user failure stays at 100% and the failing dependency receives **three times** the load, which can turn a partial failure into a total one. Stack this across three layers of services each retrying three times and the bottom service sees up to 3 × 3 × 3 = 27 calls for each user request.

Consequences for measurement: the server-side error ratio per attempt (20%) differs from the user-visible ratio (0.8%), so decide which one the SLI means. The SLI for user experience should count the outcome after retries and the time to success *including* retries. Consequences for design: retries with exponential back-off and jitter, a **retry budget** (for example, retries limited to 10% of the request rate), a deadline propagated across calls so downstream work stops once the caller has given up, and circuit breakers that stop calling an obviously failing dependency.

## Noisy alerts: the economics of attention

Alerts are a trade between two errors: **false positives** (a page when nothing needs doing) and **false negatives** (no page when users are hurt). Attention is finite, and false positives consume it, which increases the *probability of ignoring the true positive*.

### Measure alert quality

For each paging alert over a quarter, record whether it required action.

- **Precision** = pages that needed action ÷ all pages.
- **Recall** = user-harming incidents that paged ÷ all user-harming incidents.

A worked review. An alert paged 40 times in a quarter; on-call recorded that 6 needed action. Precision is 6 ÷ 40 = **15%**. The 34 false pages, at a median of 20 minutes each to acknowledge, assess and close, cost 680 minutes, over **11 hours** of interrupted sleep and focus, and teach the on-call that this alert is usually noise. During the same quarter there were 8 incidents that harmed users and 6 of them paged: recall 75%. Two incidents were found by customers. The question is not simply "tune this alert" but "what mix of rules gets precision above 50% without letting recall fall below 90%?"

| Cause of noise | Diagnosis | Remedy |
| --- | --- | --- |
| Threshold below normal variation | Fires at daily peaks | Base the threshold on the SLO burn, not on a convenient number |
| Flapping around a threshold | Fires and resolves repeatedly | `for` duration; hysteresis (fire above 2%, resolve below 1%); the short window of a burn alert |
| Duplicates | Five alerts for one cause | Group by cause; inhibit symptoms when a known cause fires |
| Alerts on causes, not symptoms | Fires without user impact | Move to dashboards; keep only the symptom alert |
| Low traffic | Ratios jump on single failures | Minimum-count conditions; longer windows |
| Dead alert | Nobody remembers why it exists | Review owner; delete if no action in two quarters |
| Not actionable | The responder can only watch | Convert to a notification or remove |

### An alert lifecycle

1. **Birth:** a proposed alert states the symptom, who acts, the runbook, and the expected frequency.
2. **Trial:** it runs in non-paging mode for two weeks; count how often it would have paged and whether each was actionable.
3. **Promotion:** only if the trial precision is acceptable.
4. **Review:** monthly, rank alerts by pages, by time spent, by action rate.
5. **Retirement:** delete anything with no action in two quarters; record the decision.

Apply a **page budget** per team (for example, no more than two actionable pages per 12-hour shift on average) and treat exceeding it as a defect in the system, not a call for more resilient engineers.

## When "SLO met, users angry"

This is the characteristic expert diagnosis: the numbers are healthy, the complaints are real. Treat the SLI as a hypothesis that can be wrong.

| Possible cause | Check |
| --- | --- |
| SLI measures the load balancer, not the user's experience | Add client-side or synthetic measurement; compare with browser timing |
| Aggregate hides a segment (one region, one tier, one client version) | Break down by every dimension customers vary on; define SLOs per critical journey |
| Latency percentile too lenient (p50 where users feel p99) | Re-derive the threshold from complaints and from conversion data |
| Failures counted as successes (a 200 response with an error body) | Define success with business semantics; validate the response |
| Retries mask failures but slow users | Measure time to success, including retries |
| The affected users are rare and heavy | Weight by importance (revenue, volume) rather than by request |
| The SLO is over a long window and the incident was brief but severe | Add a short-window objective or a stronger burn alert for severe degradation |
| Excluded traffic is where the pain is | Review the "valid event" definition for exclusions that hide real users |

Whenever customers and the SLO disagree, the SLO is the one that must justify itself.

## Low-traffic systems at the expert level

At night a service with 10 requests per hour can show 100% errors from a single failed request. Over 30 days it handles 7,200 requests, so a 99.9% budget is 7.2 failures; one failure spends about 14% of it. Alert on absolute counts plus ratio, use longer windows, add synthetic probes to maintain a baseline, and evaluate the SLO across the full window. For batch or event-driven systems with long gaps between events, measure *freshness* (age of the newest successful result) instead of request ratios.

## Reliability beyond telemetry

Observability reveals problems; it does not prevent them. Pair it with capacity planning, graceful degradation, timeouts shorter than the caller's deadline, retries with jitter and budgets, circuit breakers, load shedding, bulkheads, safe deployment (canary, automated rollback) and game days.

**Game day, minimal protocol.** Someone other than the author injects a failure (kill a dependency, add latency, partition one zone); the on-call follows the runbook alone, with no hints; an observer records every time the runbook was ambiguous, a dashboard was missing, or an alert did not fire. Each such note becomes a tracked fix. Success is measured by how many fixes the exercise produced, not by whether it went smoothly. Start in staging, graduate to production in a controlled blast radius with an abort condition and a named owner who can stop the exercise.

## Reliability programmes

A programme is a sustained, funded effort to move an organisation's reliability, not a set of tools. Its failure modes are organisational: SLOs nobody owns, postmortem actions that never close, alerts that grow without pruning.

### A maturity ladder

| Stage | Characteristics | Typical next step |
| --- | --- | --- |
| 1. Reactive | Alerts on causes; incidents found by users; no shared definitions | Define SLIs for the top three journeys |
| 2. Measured | SLIs and SLOs exist; dashboards trusted; postmortems written | Adopt burn-rate alerts; error-budget policy signed |
| 3. Managed | Budget drives prioritisation; alerts reviewed monthly; game days run | Reliability work funded on a roadmap; dependency SLOs negotiated |
| 4. Optimised | Telemetry contract automated; capacity and failure injection routine; cost of reliability known | Segment-level SLOs; automated remediation; programme metrics reviewed by leadership |

Skipping stages usually fails: burn-rate alerts on an SLI nobody believes produce confident noise.

### Programme mechanisms

- **Production readiness review.** Before a service takes production traffic: owner, SLOs, dashboards, alerts with runbooks, capacity plan, rollback, dependencies and their SLOs, on-call coverage. The review is a conversation that finds gaps early, not a gate to be passed by ticking boxes.
- **Dependency contracts.** For every hard dependency, write down the availability and latency you assume and the fallback if they are not met. If a dependency's measured SLO is worse than your assumption, you have found a risk before an incident did.
- **Toil budget.** Track repetitive manual operational work; cap it (for example at 50% of an on-call engineer's time) and invest the surplus in automation.
- **Postmortem governance.** Review actions monthly; report completion rate and age of open items; escalate those past due; look across incidents for repeated contributing factors rather than treating each as unique.
- **Segment and ownership clarity.** Every SLO has an owner with the authority to prioritise work against it.
- **Funding.** Reliability work competes with features; the error-budget policy is how that competition is settled explicitly rather than by whoever shouts loudest.

### Measuring the programme honestly

**MTTR (mean time to recover) is a poor headline.** Incident durations are heavy-tailed. Take ten incidents lasting 5, 8, 10, 12, 15, 20, 25, 30, 45 and 480 minutes. The mean is 650 ÷ 10 = **65 minutes**, but the median is (15 + 20) ÷ 2 = **17.5 minutes**, and nine of ten incidents ended within 45 minutes. One extreme incident dominates the mean, so a "20% MTTR improvement" can reflect luck. Report percentiles (median and p90), count incidents by severity, and examine the long tail individually.

Better programme indicators: the share of user-harming incidents detected by alerts before customers reported them (recall); precision of pages; time from start to *mitigation* (not to root cause); budget exhaustion events per year; action-item closure rate; share of services with a current SLO and runbook; page load per on-call shift.

## High-stakes decisions under uncertainty

The most expensive moments are decisions made with partial evidence while the cost keeps accumulating. A few principles are worth rehearsing before they are needed.

**Prefer reversible actions, and compare their expected cost.** A rollback is quick and usually reversible. Suppose a release causes 3% errors at 40 requests per second: 40 × 60 × 0.03 = 72 bad requests per minute. Option A, rollback: 10 minutes to execute and 95% likely to fix. If it fails, the fallback costs another 60 minutes. Expected bad requests ≈ 72 × 10 + 0.05 × (72 × 60) = 720 + 216 = **936**. Option B, roll forward with a fix: 60 minutes, 70% likely to work, and if it fails we roll back after another 10 minutes. Expected ≈ 72 × 60 + 0.3 × (72 × 10) = 4,320 + 216 = **4,536**. Against a 60,000-request budget, A spends about 1.6% and B about 7.6%. The numbers favour rollback by a factor of almost five, unless rollback is irreversible (a destructive migration), in which case the comparison changes. Writing the numbers down in the incident channel turns an argument into an estimate people can challenge.

**Decide who decides.** In an incident the incident commander decides, with advice, after a stated time-box for disagreement. Debate is valuable until the decision; afterwards the team executes.

**Declare early, close deliberately.** Declaring costs a few minutes of attention; a late declaration costs coordination, communication and trust.

**Mitigate before diagnosing, but preserve evidence.** Capture logs, a heap profile or a trace sample before restarting a process; a restart can destroy the only evidence of a leak.

**Communicate uncertainty explicitly.** "We believe the cause is X (confidence moderate); we have not yet ruled out Y; next update at 15:30." Customers and executives handle uncertainty better than silence or false certainty.

**Telemetry changes during an incident are risky.** Increasing log verbosity on a saturated service, turning on full tracing or deploying a new dashboard query can add load to a system that is failing. If the observability changes are necessary, do them on one instance or a small share of traffic first. Conversely, temporarily *disabling* expensive telemetry is a legitimate load-shedding option; record that you did so, because your data will have a hole.

**Freezes and exceptions.** Budget exhausted ahead of a major event (a sales peak): the policy says freeze; the business says ship. The expert's task is to make the trade-off explicit: state the remaining budget, the expected burn if the release goes badly, the rollback plan and the monitoring in place, and have a named executive sign the *recorded exception* with a time limit. The freeze is not sacred and neither is the exception; what is unacceptable is an invisible one.

**Decision log.** Record each significant decision with time, options considered, evidence, the choice and who made it. Reviews read the log to separate decision quality from outcome quality: a good decision can have a bad outcome and the reverse.

**Pre-mortems.** Before a risky change, ask the team to assume it failed and write why. The list of plausible failures becomes the list of signals to watch and rollback triggers to agree beforehand ("if error ratio exceeds 1% for 3 minutes, roll back").

## Case catalogue

### Case 1 — The healthy dashboard of a dead service

An overnight network fault takes down the cluster that hosts both `orders-api` and its metrics pipeline. Every graph flatlines at the last value; the "error ratio" panel shows 0% because the denominator is absent; no alert fires because every rule evaluates to "no data". Customers report the outage forty minutes later. Lesson: telemetry shares fate with the system unless you design otherwise. Out-of-band synthetic probes, a dead man's switch and absence alerts turned the silence into the alarm.

### Case 2 — The one-in-four-hundred instance

A bad node in a fleet of 400 serves errors for the clients stuck to it. The fleet error ratio is 0.25%, burn rate 2.5, below every alert. A customer escalates after two weeks. Per-instance outlier detection, per-zone SLIs and ejection of instances whose error ratio is many times the fleet median would have found it in minutes. Lesson: aggregates measure the average user, not each user.

### Case 3 — The retry multiplier

A database failover takes 40 seconds. Clients retry three times with no back-off and no jitter, and three service tiers each do the same. The database comes back to a synchronised wave of up to 27 times normal load and fails again. The incident lasts 25 minutes instead of 40 seconds. The graphs show the load amplification; the cause is a retry policy that was reasonable in isolation. Lesson: retries must be budgeted, jittered and bounded by deadlines, and the load on a recovering dependency is a measurement you should watch.

### Case 4 — The sampling policy that hid the bug

At a 1% head-sampling rate a defect affecting 30 requests per day produces on average 0.3 traces per day. The chance of capturing no trace on a given day is 0.99³⁰ ≈ 74%. For three weeks, support tickets accumulate and no trace of the failure exists. The team changes to tail sampling that always keeps traces with error status, and the cause is found the first day. Lesson: choose the sampling policy for the questions you need answered about rare failures, and keep unsampled counters so that you know the failures exist.

### Case 5 — The cardinality incident during the incident

A new route embeds an order id in the URL path and the instrumentation labels metrics with the raw path. During a traffic peak, series count rises from 150,000 to over 9 million in an hour. The metrics backend runs out of memory and crashes in the middle of an unrelated outage, taking dashboards and alerts with it. Lesson: the observability stack is production infrastructure; protect it with allow-lists, limits that fail the offender rather than the system, and an alert on series growth.

### Case 6 — The SLO that was met

Checkout availability is 99.95% for the month, comfortably above 99.9%, and support is flooded. The SLI counts HTTP 5xx at the load balancer; the payment step fails with a `200` response and an error message in the body, and mobile clients on a particular version time out client-side before the load balancer records anything. Redefining success with business semantics and adding client-side measurement moves the measured availability to 99.3%. Lesson: the SLI is a claim about user experience and must be validated against complaints.

### Case 7 — The freeze that was overridden

Budget is exhausted two weeks before a major sales event. Leadership overrides the freeze verbally; the release is deployed on a Friday and causes a four-hour partial outage. The postmortem finds that no exception was recorded, nobody owned the risk, and the rollback plan had never been tested. Lesson: exceptions are legitimate and must be explicit, owned, time-limited and accompanied by a tested rollback.

## Expert trade-offs

| Axis | One end | Other end | How an expert decides |
| --- | --- | --- | --- |
| Head versus tail sampling | Cheap, simple, blind to outcome | Targeted, buffered, operationally heavy | Volume and need to capture rare failures; always keep unsampled metrics |
| Metrics versus rich events | Cheap, pre-aggregated, bounded dimensions | Flexible, high-cardinality, costly | Metrics for SLOs and alerts; events for exploration, sampled |
| Retention versus cost | Long, everything | Short, tiered | Match retention to the lifetime of the question; audit separately |
| Fleet aggregate versus per-segment SLOs | One number per service | Many segment objectives | Segment where customers differ materially; budget the extra series |
| Sensitive alerts versus quiet pager | Catch everything | Page rarely | Set a page budget; measure precision and recall; use tickets for slow burns |
| Tight SLO versus velocity | 99.99% | 99.5% | Price per nine; user perception; dependency limits |
| Automation versus human judgement in remediation | Auto-remediate everything | Human always decides | Automate reversible, well-understood actions with rate caps; humans for novel ones |
| Deep health checks versus shallow | Exercise dependencies | Only process liveness | Deep checks catch more but can amplify failure; separate liveness from readiness |
| Telemetry depth versus safety | Verbose tracing everywhere | Minimal | Always bounded exporters; ability to turn verbosity down under stress |
| Centralised platform versus team autonomy | One paved road | Everyone chooses | Strong defaults, a telemetry contract and documented exits |

A useful expert habit is to **write the sentence before choosing**: "We accept *cost* to reduce *specific risk*, and we will know it failed when *observable signal*." If you cannot complete that sentence, the control is cargo cult.

## Knowledge consolidation

- Error budgets work only if the **SLI reflects users, data is trustworthy, the policy was agreed in advance and the target is funded**. Price each nine in minutes and money.
- **Telemetry has economics**: logs scale with events, traces with requests × spans, metrics with series; memory per series, not disk, usually binds first.
- **Head sampling** is cheap and blind: rare events vanish (probability of missing 20 events at 5% is about 0.36) and counts need weighting. **Tail sampling** targets errors and slow requests at the cost of buffering, routing and pipeline complexity. **Rates and SLOs come from unsampled metrics.**
- **Cardinality is a budget**: compute the multiplication before adding a label, enforce limits that fail the offender, and protect the observability stack itself.
- **Telemetry fails**: survivorship, shared fate, silent drops, clock skew, broken propagation, late data. Detect absence on purpose, keep a dead man's switch, and separate observation from inference.
- **Gray failures** hide from health checks and fleet aggregates; look at instances, zones and client versions, and measure after retries as well as per attempt.
- **Retries multiply load** under correlated failure; budget them, jitter them and propagate deadlines.
- **Alert quality** is precision and recall; false pages cost attention. Use a lifecycle, a page budget and symptom-based, burn-rate alerts.
- When the **SLO is met and users are angry**, doubt the SLI.
- **Programmes** need ownership, readiness reviews, dependency contracts, honest metrics (percentiles, not only MTTR) and closed action items.
- In high-stakes decisions, compare **expected cost of reversible options**, decide who decides, communicate uncertainty and keep a decision log; exceptions must be recorded and owned.

## Exercises

**Exercise 1 — Price your telemetry.** For a service you operate (or `orders-api` at a traffic level you choose), compute daily log volume, trace volume under no sampling and under a tail policy you design, and active series for the main histogram. State every assumption (bytes per line, spans per trace, label counts) and the unit price you use. Identify the single largest cost and one change that would reduce it by half without harming your SLO.

**Exercise 2 — Sampling arithmetic.** A defect affects 40 requests per day. Compute the probability that head sampling at 2% captures no trace on a given day, and the expected number of days until the first captured trace. Then design a tail policy that guarantees capture and compute the data volume at 800 requests per second with 15 spans of 1 KB, where 0.4% of requests error, 1.1% are slow and you keep 1.5% of the rest.

**Exercise 3 — Cardinality review.** A team's budget is 120,000 series and it uses 95,000. A proposal adds `customer_tier` (3 values) and `region` (6 values) to a metric with 1,500 series. Compute the new series count, the total and whether the budget holds. Propose an alternative that preserves most of the diagnostic value.

**Exercise 4 — Gray failure.** A fleet of 250 instances with equal traffic has one failing instance (100% errors). Against a 99.95% SLO over 30 days, compute the fleet error ratio, the burn rate, the time to exhaust the budget and which alerts of the standard multi-window set fire. Then design one additional detection that would catch it.

**Exercise 5 — Retry arithmetic.** Each call fails independently with probability 0.1 and a client makes at most 4 attempts. Compute user-visible failure probability and expected attempts. Repeat when the dependency is fully down. Propose a retry budget and say how it changes both numbers.

**Exercise 6 — Alert review.** An alert fired 24 times in a quarter; 5 needed action; during the quarter there were 7 user-harming incidents, 5 of which this class of alert caught. Compute precision and recall. Handling a false page costs 25 minutes; compute the total cost. Propose three changes and predict their effect on precision and recall.

**Exercise 7 — Decision under uncertainty.** A release causes a 2% error ratio at 60 requests per second. Rollback takes 8 minutes and is 90% likely to fix it; a roll-forward fix takes 45 minutes and is 75% likely to work, otherwise a rollback follows (8 minutes). Compute expected bad requests for each, express them as a share of a 100,000-request budget, and state what additional facts could reverse the recommendation.

**Exercise 8 — Telemetry loss tabletop.** Walk through the loss of the entire metrics pipeline during an unrelated outage: how you detect it, what independent signals you use, how you declare the incident, which decisions you postpone, and how you reconstruct the timeline afterwards.

**Solution notes.**

*Exercise 1.* There is no single answer, but check the method: volume = rate × items × size × 86,400; series = product of label cardinalities times histogram multiplier; costs shown per day and per month. A common finding is that logs dominate; the cheapest half-cut is usually removing low-value info-level lines, not reducing retention. Marks go for stated assumptions and for a change that does not degrade the SLO measurement.

*Exercise 2.* Probability of no capture = 0.98⁴⁰ ≈ 0.446. Expected captures per day = 0.8, so the expected number of days until the first captured trace is about 1/0.8 ≈ 1.25 days, with a 44.6% chance of missing the first day entirely. Tail policy volume: kept fraction = 0.4% + 1.1% + 98.5% × 1.5% = 1.5% + 1.4775% = 2.9775%. Raw volume = 800 × 15 × 1 KB = 12 MB/s = 1.0368 TB/day; kept ≈ 30.9 GB/day. The policy guarantees capture because every error trace is retained.

*Exercise 3.* The metric becomes 1,500 × 3 × 6 = 27,000 series, an increase of 25,500. The total would be 95,000 + 25,500 = 120,500, which exceeds 120,000 by 500, so the budget fails narrowly. Alternatives: keep `customer_tier` (3 values) and replace `region` with a coarse `region_group` of 2 values (1,500 × 3 × 2 = 9,000, +7,500, total 102,500), or keep per-region detail only for error metrics, or record the extra dimensions on traces and logs.

*Exercise 4.* Fleet error ratio 1/250 = 0.4%. Budget fraction 0.0005, so burn rate = 0.4% ÷ 0.05% = 8. Time to exhaust: 720 ÷ 8 = 90 hours = 3.75 days. Fast alert (burn rate 14.4 → 0.72%): no. Slow alert (burn rate 6 → 0.3%): yes, once the six-hour average exceeds 0.3%, which at a 0.4% ratio takes 6 × 0.3 ÷ 0.4 = 4.5 hours, by which time 8 × 4.5 ÷ 720 = 5% of the budget is gone. Tickets (3×, 1×) also fire. Additional detection: compare each instance's error ratio to the fleet median and alert if an instance exceeds, say, ten times the median for 10 minutes; or automatic ejection with a cap on the ejected share.

*Exercise 5.* Independent failure with p = 0.1 and 4 attempts: failure probability 0.1⁴ = 0.0001 = 0.01%; expected attempts = 1 + 0.1 + 0.01 + 0.001 = 1.111, so 11.1% extra load. Dependency fully down: failure probability 100%, attempts 4 per request (4× load). With a retry budget of 10% of request volume, extra load is bounded at 1.1× total even when the dependency is down, at the cost that some requests that could have succeeded on retry do not retry during widespread failure. In the independent case the budget binds only marginally (11.1% extra load wanted versus 10% allowed), so user-visible failure rises slightly above 0.01%.

*Exercise 6.* Precision = 5 ÷ 24 ≈ 20.8%. Recall = 5 ÷ 7 ≈ 71.4%. False pages = 19; cost 19 × 25 = 475 minutes, about 7.9 hours. Candidate changes: switch to a burn-rate rule with a short window (raises precision by removing flapping); add a minimum request-count condition (removes low-traffic false pages); add a synthetic probe and an absence alert (raises recall for the missed incidents). Predictions should name direction and rough magnitude and be validated in a non-paging trial.

*Exercise 7.* Bad requests per minute = 60 × 60 × 0.02 = 72. Rollback: 72 × 8 = 576, plus 10% chance of failing and costing another 60 minutes (assumed) = 0.1 × 72 × 60 = 432; expected ≈ 1,008 (state your assumption about the fallback). Roll-forward: 72 × 45 = 3,240, plus 25% chance of failing followed by an 8-minute rollback = 0.25 × 72 × 8 = 144; expected ≈ 3,384. As shares of 100,000: about 1.0% and 3.4%. Facts that could reverse it: the rollback is irreversible or loses data (a migration), the fix is trivially verified, the rollback target also has a known defect, or the error is concentrated in a segment where the roll-forward is faster.

*Exercise 8.* Look for: an external heartbeat or probe that tells you the pipeline is gone; direct evidence from a second path (load balancer logs, synthetic checks, customer-contact volume); explicit postponement of decisions that need unavailable data (capacity changes, budget accounting); safe mitigations that do not depend on dashboards (rollback of the last change); and a reconstruction plan from logs held outside the failed system.

## Mentoring prompts

Your SLO is met and users are angry; what is wrong with the SLI, and how would you find out? How would you design alerting for a system whose traffic is close to zero at night? What does it cost to keep every trace, and what do you lose by sampling? One instance in four hundred is failing; show why no burn-rate alert fires and what you would add. A leader asks you to override the freeze before a major event; what do you need written down before you agree? Pick one alert you own and report its precision and recall.

---
