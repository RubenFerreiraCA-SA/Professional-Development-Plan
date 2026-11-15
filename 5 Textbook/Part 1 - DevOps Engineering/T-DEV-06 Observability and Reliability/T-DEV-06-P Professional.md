# T-DEV-06-P — Professional Engineering

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-p"></a>
#### T-DEV-06-P — Professional Engineering

## Why this matters

Intermediate practice gives you telemetry and alerts that fire. Professional practice answers a harder question: *how reliable does this service need to be, how do we know whether it is, and what do we do when it is not?* Without an explicit answer, reliability becomes an argument. Product wants features, operations wants stability, the on-call person wants sleep, and every party quotes a different graph. A **service level objective** (SLO) turns that argument into arithmetic that all parties agreed before the incident. An **error budget** converts the arithmetic into a decision rule. **Burn-rate alerts** wake people only when the budget is being spent fast enough to matter. **Incident response** and **postmortems** make the response repeatable and the learning durable.

This section assumes the Intermediate material: structured telemetry, histograms, label discipline, PromQL-style queries, alert rules and routing. Everything uses the neutral `orders-api` service and its `POST /v1/orders` (checkout) and `GET /v1/orders/{id}` (read) routes. Worked calculations are exact arithmetic on stated assumptions; outputs marked *illustrative* show shape rather than measurement. Nothing depends on any other course material.

## First principles: reliability is a number someone chose

No service is 100% reliable, and the last increments cost the most. A target must therefore be a *chosen* number, justified by what users notice and what the organisation will pay for. Three definitions anchor everything.

| Term | Definition | Example for `orders-api` |
| --- | --- | --- |
| SLI (service level indicator) | A measured ratio: good events ÷ valid events | Share of valid `POST /v1/orders` requests that succeed in under 800 ms |
| SLO (service level objective) | A target for the SLI over a window | 99.5% over a rolling 30 days |
| Error budget | 100% − SLO: the amount of "badness" the target tolerates | 0.5% of valid requests in the window |

A fourth term is often confused with the SLO. An **SLA** (service level agreement) is a contractual promise with consequences, usually looser than the internal SLO. Set the SLO tighter than any SLA so that you notice trouble before you owe a refund.

**Why a ratio of events and not a ratio of time?** Time-based availability ("the service was up 99.9% of minutes") treats a minute at 3 requests per second the same as a minute at 3,000, and it cannot describe partial failure. An event-based SLI weights each user's request equally and handles partial failure naturally: if 5% of requests fail, the SLI says so.

## Choosing SLIs: user journeys, not components

An SLO should describe something a user would notice. "CPU below 70%" is not one; "orders can be placed" is. Choose a small number of **critical user journeys** and write an SLI for each.

### The SLI specification

For each SLI write down five things. If you cannot, the SLI is not ready.

| Item | Question | Example: checkout success |
| --- | --- | --- |
| Good event | What counts as success from the user's side? | Response status below 500 *and* order persisted *and* response within 800 ms |
| Valid event | Which events are in the denominator? | `POST /v1/orders` requests that reached the service with well-formed bodies; exclude health checks, load tests, and client errors (4xx) that are the caller's fault |
| Data source | Where is it measured? | Load balancer logs for the outermost view; application histogram for detail |
| Window | Over what period is the target evaluated? | Rolling 30 days |
| Owner | Who answers when it degrades and who may change the definition? | The orders team |

**Which 4xx errors count?** A `400 Bad Request` caused by a malformed client request is not the service's failure. But a `429 Too Many Requests` caused by your own rate limiter wrongly throttling legitimate users, or a `404` caused by your own broken routing, is. Decide explicitly, write the rule down, and keep it stable; changing the definition quietly changes the history.

### Latency SLIs from histograms

Express a latency SLI as a *fraction*, not as a percentile: "at least 99% of requests complete in under 300 ms". A fraction can be summed over time and over instances, and it works directly with the error budget. With a histogram that has a bucket boundary at 0.3 s:

```text
good  = rate(http_request_duration_seconds_bucket{route="/v1/orders",le="0.3"}[5m])
valid = rate(http_request_duration_seconds_count{route="/v1/orders"}[5m])
sli   = good / valid
```

If in a five-minute window the total rate is 100 requests per second and 97 of those per second fall in buckets up to 0.3 s, the SLI for that window is 97 ÷ 100 = 97%, which is below a 99% objective. The boundary at 0.3 s must exist in the histogram; add it before you need the number.

### Measure from near the user, and know what you cannot see

| Measurement point | Sees | Misses |
| --- | --- | --- |
| Application metrics | Requests that reached the code; internal detail | Requests dropped before the service; time in the network |
| Load balancer or gateway | All requests reaching the edge, including those the app never saw | Browser-side rendering; DNS; client-side retries |
| Synthetic probe | A scripted journey from outside, even at low traffic | Real user variety; only checks what the script checks |
| Real-user or client-side measurement | The user's actual experience | Noisy; privacy considerations; availability of the client telemetry itself |

The best practical default is **the outermost server-side measurement you can trust, plus synthetic probes for journeys with low traffic.** State in the SLO document what remains invisible.

### Setting the target

Choose the objective from the bottom up: what level of failure would users notice, what do dependencies allow, and what would extra nines cost? Convert targets to allowed downtime first, because a percentage hides the cost.

| SLO | Error budget (30 days = 43,200 min) | Allowed total outage | What it typically demands |
| --- | --- | --- | --- |
| 99% | 1% | 432 min = 7 h 12 min | Basic redundancy; manual recovery acceptable |
| 99.5% | 0.5% | 216 min = 3 h 36 min | Reliable deploys, on-call in working hours plus escalation |
| 99.9% | 0.1% | 43.2 min | Automated failover, safe deployments, 24/7 response |
| 99.95% | 0.05% | 21.6 min | Redundancy across failure domains, rapid automated rollback |
| 99.99% | 0.01% | 4.32 min (4 min 19 s) | Multi-zone everywhere, automatic remediation, no manual step in recovery |

Two practical bounds:

- **You cannot be more reliable than what you hard-depend on.** If three components in series each achieve 99.9%, the chain achieves about 0.999³ = 0.997003, i.e. 99.70%. Promising 99.9% to users on top of them without redundancy is a promise you cannot keep.
- **Redundancy helps only if failures are independent.** Two independent replicas each at 99% give 1 − 0.01² = 99.99%. If they share a database, a deployment pipeline or a region, the real number is far lower; model the shared part separately.

## Error budgets

The error budget is the SLO's complement, expressed in a unit you can spend.

**Worked example 1 — the budget in requests.** `orders-api` handles about 2,000,000 valid checkout requests per day, so 60,000,000 in 30 days. A 99.9% SLO gives a budget of 0.1% × 60,000,000 = **60,000 bad requests** in the window.

**Worked example 2 — what an incident costs.** At a peak of 40 requests per second, a fault causes 5% of checkout requests to fail for 20 minutes.

- Requests during the incident: 40 × 20 × 60 = 48,000.
- Bad requests: 5% × 48,000 = 2,400.
- Share of the monthly budget consumed: 2,400 ÷ 60,000 = **4%**.
- Burn rate during the incident: error ratio ÷ budget fraction = 5% ÷ 0.1% = **50**. At that rate the entire 30-day budget would be gone in 720 h ÷ 50 = 14.4 hours.

**Worked example 3 — tracking pace.** If 40% of the monthly budget is gone after 12 of 30 days, the elapsed fraction of the window is 12 ÷ 30 = 0.40, so the average burn rate to date is 0.40 ÷ 0.40 = 1.0: exactly on pace. If instead 70% is gone after 12 days, the burn rate is 0.70 ÷ 0.40 = 1.75, and at that pace the budget runs out after about 12 ÷ 0.70 ≈ 17 days — thirteen days early.

### The error-budget policy

The budget is a decision tool only if the organisation agreed in advance what happens as it is spent. Write it down and have someone with authority sign it.

```text
Budget remaining > 50%:   normal release cadence.
Budget remaining 10-50%:  every release needs a rollback plan reviewed by the on-call;
                          reliability items are prioritised ahead of new features.
Budget exhausted:         feature releases paused (security and reliability fixes only) until
                          the rolling window recovers or the product owner and engineering lead
                          record an explicit, time-limited exception.
Review:                   monthly, covering the SLI definition, data quality and the exception list.
```

The exception path matters as much as the freeze. An unrecorded exception is how policy dies: one skipped freeze, and the number stops meaning anything.

**What counts against the budget.** Decide in advance and write it down: planned maintenance (usually counts, because users cannot tell the difference), dependency failures (usually counts: you chose the dependency), failures caused by abusive traffic (policy decision), and incidents in a canary slice (counts proportionally by requests).

## Burn rates and alert design

### From threshold to burn rate

A fixed threshold alert ("error ratio above 2% for 10 minutes") has no relationship to the SLO. Against a 99.9% SLO, 2% is a 20× burn, which is extreme; yet a steady 0.3% error ratio, which never trips that rule, exhausts the budget in 10 days. A **burn-rate** alert asks the right question: *at the current error ratio, how fast is the budget being spent?*

Definitions, for an SLO of 99.9% (budget fraction 0.001) over a 30-day (720-hour) window:

- **Burn rate** = observed error ratio ÷ budget fraction. A burn rate of 1 spends exactly the whole budget by the end of the window.
- **Budget consumed in a window** = burn rate × (alert window ÷ SLO window).
- **Time to exhaust** = SLO window ÷ burn rate.

| Burn rate | Equivalent error ratio | Budget consumed if sustained for | Time to exhaust the whole budget |
| --- | --- | --- | --- |
| 14.4 | 1.44% | 2% in 1 hour (14.4 × 1/720) | 50 hours |
| 6 | 0.6% | 5% in 6 hours (6 × 6/720) | 5 days |
| 3 | 0.3% | 10% in 1 day (3 × 24/720) | 10 days |
| 1 | 0.1% | 100% in 30 days | 30 days |

### Multiple windows

Each alert pairs a **long window** with a **short window**, and requires *both* to exceed the threshold.

- The **long window** ensures the problem is large enough to matter: a one-minute blip cannot spend 2% of a month.
- The **short window** (about one twelfth of the long one) makes the alert *reset quickly* after the problem ends, so the on-call is not still being paged an hour after recovery.

| Severity | Long window | Short window | Burn rate | Budget at stake | Action |
| --- | --- | --- | --- | --- | --- |
| Page | 1 h | 5 min | 14.4 | 2% in 1 h | Wake someone |
| Page | 6 h | 30 min | 6 | 5% in 6 h | Wake someone (or urgent ticket in business hours) |
| Ticket | 1 day | 2 h | 3 | 10% in 1 day | Work item for the owning team |
| Ticket | 3 days | 6 h | 1 | 10% in 3 days | Prioritise in planning |

Express this with recording rules so the expressions are readable and cheap.

```yaml
groups:
  - name: orders-slo-recording
    interval: 30s
    rules:
      - record: orders:sli_error_ratio:rate5m
        expr: |
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders",code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders"}[5m]))
      - record: orders:sli_error_ratio:rate30m
        expr: |
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders",code=~"5.."}[30m]))
          /
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders"}[30m]))
      - record: orders:sli_error_ratio:rate1h
        expr: |
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders",code=~"5.."}[1h]))
          /
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders"}[1h]))
      - record: orders:sli_error_ratio:rate6h
        expr: |
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders",code=~"5.."}[6h]))
          /
          sum(rate(http_requests_total{service="orders-api",route="/v1/orders"}[6h]))
  - name: orders-slo-alerts
    rules:
      - alert: OrdersErrorBudgetBurnFast
        expr: |
          orders:sli_error_ratio:rate1h > (14.4 * 0.001)
          and
          orders:sli_error_ratio:rate5m > (14.4 * 0.001)
        labels: { severity: page, slo: checkout-availability }
        annotations:
          summary: "Checkout burning 2% of the 30-day budget per hour"
          runbook_url: https://runbooks.example.com/orders-slo-burn
      - alert: OrdersErrorBudgetBurnSlow
        expr: |
          orders:sli_error_ratio:rate6h > (6 * 0.001)
          and
          orders:sli_error_ratio:rate30m > (6 * 0.001)
        labels: { severity: page, slo: checkout-availability }
        annotations:
          summary: "Checkout burning 5% of the 30-day budget per 6 hours"
          runbook_url: https://runbooks.example.com/orders-slo-burn
```

Check a threshold by hand: 14.4 × 0.001 = 0.0144, an error ratio of 1.44%. Sustained for one hour, that spends 14.4 × (1 ÷ 720) = 2% of the 30-day budget, matching the table.

### Detection time and the cost of detection

Burn-rate alerts do not detect instantly; they detect when enough budget has burned. For the fast alert, the long window needs its average error ratio above 1.44%. In a total outage (100% errors) starting from a clean hour, the one-hour average crosses 1.44% after 0.0144 × 60 min = **0.864 min ≈ 52 seconds**, and the 5-minute window crosses after 4.3 seconds, so detection takes about a minute (plus rule evaluation time). For a partial outage with error ratio *e*, the detection time is about 0.864 min ÷ *e*. At 10% errors that is 8.6 minutes; at 2%, 43 minutes; at 1.44% it is the full hour; below 1.44% the fast alert never fires and the slow alerts take over.

Notice a pleasing property: whatever the error ratio, the budget consumed at detection is about 2%. The alert is designed to fire when a fixed fraction of the budget is gone. Tightening the threshold (say burn rate 7.2 over 1 hour, consuming 1%) detects sooner but pages more often on events that would have healed themselves.

### Principles of alert design

| Principle | Practice |
| --- | --- |
| Alert on symptoms | Page on user-visible impact; use causes on diagnosis dashboards |
| Every page is actionable | A runbook: what it means, urgency and owner, how to verify, how to mitigate, who to escalate to |
| Prefer burn-rate alerts | Multi-window, multi-burn-rate alerts catch fast and slow budget loss with fewer false pages than fixed thresholds |
| Separate pages from tickets | Slow burns open tickets; fast burns page |
| Review noisy alerts | Delete, tune or downgrade anything that repeatedly fires without action |
| Test the alert path | Synthetic alert through routing to a human, quarterly |
| Alert on telemetry loss | A silent metric is not a healthy metric |

### Paging versus ticketing: a decision rule

Ask three questions of every proposed page.

1. **Is it urgent?** Will users be hurt, or a budget burned materially, before the next working day?
2. **Is it actionable?** Is there something a human can do now that a machine has not already done?
3. **Is it novel?** Does it require judgement, or could automation handle it?

If any answer is "no", it should not wake a person. A condition that is urgent but not actionable (an upstream provider is down and you have no failover) is a *status notification*; send it to a channel and to incident communications, not to a pager. A condition that is actionable but not urgent (disk will fill in nine days) is a *ticket*.

| Condition | Urgent | Actionable | Route |
| --- | --- | --- | --- |
| Checkout burning 2% of budget per hour | Yes | Yes | Page |
| Checkout burning 10% of budget per day | No (days) | Yes | Ticket |
| A single instance restarted once | No | No | Dashboard only |
| Disk predicted full in 3 hours | Yes | Yes | Page |
| Payment provider status page shows incident | Yes | Limited | Notify channel; incident comms |
| Certificate expires in 21 days | No | Yes | Ticket (with automation preferred) |

**A paging budget.** Treat on-call interruptions as a budget too: a reasonable aspiration is no more than about two actionable pages per 12-hour shift on average. Beyond that, people stop responding well, and the alert design itself, not the engineers, is the defect.

## Low-traffic and low-volume services

A service that receives 10 requests per hour overnight will show a 100% error ratio when one request fails. Over 30 days it handles 10 × 720 = 7,200 requests, so a 99.9% budget is 7.2 failures; a single failed request spends about 14% of it. Ratio alerts on short windows are therefore meaningless.

Practical remedies: alert on absolute error counts *and* ratios together ("more than 5 errors and ratio above 5%"); use longer windows; add synthetic probes (one per minute) that provide a baseline of traffic with a known good outcome; evaluate the SLO over the whole window rather than a thin slice; and treat the SLO as the primary reporting tool, with fewer pages.

## Evidence-led incident response

### Roles

Small incidents need one person. Larger ones need clear roles, even if one person holds two of them.

| Role | Responsibility |
| --- | --- |
| Incident commander (IC) | Owns the response: sets priorities, assigns work, decides escalation. Does *not* debug |
| Operations lead | Hands on the system: investigates, proposes and executes mitigations |
| Communications lead | Updates stakeholders and users at a steady cadence; protects the IC from interruptions |
| Scribe | Records timeline, hypotheses, decisions and times as they happen |

### Severity levels

Define severity by *impact*, so the label guides response and communication.

| Level | Typical impact | Response |
| --- | --- | --- |
| SEV1 | Critical journey unavailable or data loss for most users | Immediate page, IC assigned, executive communication, updates every 30 minutes |
| SEV2 | Critical journey degraded for a large share of users | Page, IC if lasting beyond 30 minutes, updates every hour |
| SEV3 | Limited impact or a workaround exists | Ticket, handled in working hours |
| SEV4 | No user impact; defect or risk noted | Backlog |

Severity can change as facts change. Err towards declaring early and downgrading; declaring late costs more than declaring unnecessarily.

### The first fifteen minutes

1. **Acknowledge** the page; say so where the team can see.
2. **State the symptom in user terms and the start time.** "Checkout error ratio 6% since 13:52."
3. **Declare** an incident if criteria are met; assign IC and, if needed, communications.
4. **Look for the quick reversible action** before a deep diagnosis: recent deploy, config change or feature flag? Roll back first, understand later. *Mitigate before you find the root cause.*
5. **Write down at least three competing hypotheses** before diving into one.
6. **Gather evidence** from metrics, traces, logs, deploy history and dependency health; seek evidence that *contradicts* your favourite theory.
7. **Take one reversible action at a time** and confirm with the SLI you started with. Two simultaneous changes make the outcome uninterpretable.
8. **Communicate** on a fixed cadence even when there is nothing new: "still investigating; no change; next update 14:30".

### Mitigation toolkit

| Mitigation | When it fits | Caution |
| --- | --- | --- |
| Roll back the release | Symptom began after a deploy | Database migrations may not be reversible |
| Disable a feature flag | A new feature correlates with the symptom | Flag state itself must be observable |
| Shift traffic away from a bad zone or region | Failure is localised | Capacity of the remaining zones |
| Shed load or degrade gracefully | Saturation or retry storm | Decide who is shed; communicate |
| Scale out | Demonstrated saturation | Does not fix a dependency bottleneck; may amplify it |
| Restart | Resource leak, stuck state | Destroys evidence; capture first, and do not treat a restart as a fix |
| Failover a dependency | Provider or database outage | Rehearsed? Data consistency? |

### Communication template

```text
[14:10] SEV2 — Checkout degraded
Impact: ~6% of checkout attempts failing since 13:52 (users see "payment error").
Status: Investigating. Likely related to a configuration change at 13:49; reverting.
Next update: 14:30 or sooner if status changes.
Incident commander: <name>
```

Write for the reader who knows nothing: impact first, no jargon, a next-update time, a named owner.

## Postmortems

A **postmortem** (or incident review) is a written account of an incident whose purpose is *to change the system so that the same class of failure is less likely or less harmful*. It is **blameless**: it examines conditions and design, not individuals, because if the honest account of "what happened" leads to punishment, people stop giving honest accounts. Blameless does not mean consequence-free for ignoring agreed process; it means the *default question is "why did this seem a reasonable thing to do at the time, and what in our system made it easy?"*

### A template

```markdown
# Incident 2026-03-01 — Checkout errors after configuration change

## Summary
Between 13:52 and 14:12 (20 min) about 5% of checkout requests failed. Cause: ...

## Impact
48,000 requests in the window; ~2,400 failed. 4% of the 30-day error budget.
No data loss. Support contacts: 31.

## Timeline (UTC)
13:49  Config change deployed (EU payment endpoint URL updated).
13:52  Error ratio begins to rise.
14:05  Page: OrdersErrorBudgetBurnFast. Acknowledged 14:06.
14:09  Hypotheses: (1) new endpoint slow, (2) provider outage, (3) our release.
14:11  Config reverted. 
14:12  Error ratio returns to baseline.

## Detection
How we found out, and how long after the start (13 minutes). Why not sooner.

## Contributing factors
- Config change had no canary or staged rollout.
- No synthetic probe for the EU endpoint.
- Payment timeout equals the user-facing timeout (no room for a fallback).

## What went well / what was lucky
...

## Action items
| Action | Owner | Due | Type |
| ... |

## What the telemetry could not tell us
Whether the provider's EU endpoint was slow or unreachable from our network.
```

### Writing good action items

| Weak | Strong |
| --- | --- |
| "Be more careful with config changes" | "Roll out payment config changes to one instance first and compare error ratios for 10 minutes before proceeding (owner, date)" |
| "Improve monitoring" | "Add a synthetic probe for each payment endpoint, one per minute, paging only through the SLO burn alert (owner, date)" |
| "Add more tests" | "Add a test that fails when the payment timeout exceeds the checkout timeout minus 500 ms" |

Classify items by what they change: *prevent* (reduce the chance), *detect* (find it sooner), *mitigate* (reduce the impact or speed recovery). A review with only "prevent" items is usually wishful. Track completion; a postmortem whose actions are never closed teaches the organisation that postmortems do not matter.

### Reviewing the review

After each major incident, ask: was the SLO informative (did it reflect the user pain)? Did the alerts fire at the right time? Was the runbook accurate? Did the on-call have what they needed? Convert each *confusion* into a platform or documentation fix.

## Telemetry as a platform product

Individual teams invent inconsistent telemetry unless a platform gives them a *contract*.

| Contract element | Expectation |
| --- | --- |
| Required resource attributes | `service.name`, `service.version`, `deployment.environment.name`, team owner |
| Instrumentation baseline | HTTP server and client, database, messaging; trace propagation enabled |
| Default SLIs | Request-based availability and latency SLIs generated from standard metrics |
| Sampling and retention | Default sampling; retention per tier (hot, warm, archive) |
| Label and cardinality budget | Maximum series per service, enforced and reported |
| Validation test | A CI check that a new service emits the required attributes |
| Starter template | A repository template where the contract is already satisfied |

With a contract, a new service copies a starter and passes a validation test; without it, each team invents metric names and misses trace propagation.

### Telemetry pipeline controls

| Control | Expectation |
| --- | --- |
| Transport security | Encrypt to backends in production |
| Credentials | None in source control; use a secret store |
| Personal data | Redact; no request bodies in spans or logs |
| Cardinality and retention | Bounded labels, defined retention, budgets |
| Provider boundary | Keep standard conventions so a vendor can be replaced |
| Ownership | Who owns the Collector, SDK versions and sampling defaults |
| Availability | The pipeline has its own SLO and alerts |

## Honest blind spots

Every SLO document should list what the numbers cannot see: no synthetic probes for a journey; sampling may hide rare traces; logs without trace ids; metrics without route templates; a measurement point that excludes client-side failures. A stated limitation is a managed risk. A hidden one is a surprise waiting for an incident.

## Worked calculation set

1. **Downtime to budget.** SLO 99.95% over 30 days: budget fraction 0.0005; total minutes 43,200; allowed outage 43,200 × 0.0005 = 21.6 minutes.
2. **Request budget.** 12,000,000 requests per month at 99.9%: 12,000 bad requests.
3. **Incident cost.** 30 minutes at 25 requests per second with 8% errors: requests 25 × 1,800 = 45,000; bad 3,600; against a 60,000-request budget that is 6%; burn rate 8% ÷ 0.1% = 80.
4. **Does it page?** A steady 0.4% error ratio for 36 hours against a 99.9% SLO: burn rate 4. The 14.4 and 6 alerts do not fire (0.4% is below 0.6%). The 3× ticket alert fires (1 day window above 0.3%). Total consumed in 36 hours: 4 × 36/720 = 20%. That is correctly handled as a ticket within a day, but the budget is draining at a pace that exhausts it in 7.5 days; the ticket should be prioritised accordingly.
5. **Chain.** A checkout journey needs the API (99.95%), database (99.99%) and payment provider (99.9%) in series: 0.9995 × 0.9999 × 0.999 = 0.9984 (about 99.84%). A 99.9% objective is not supported; options are to loosen the objective, make payment asynchronous with a retry queue (so the user-visible dependency is only the API and database), or add a second provider.
## Decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Measure user pain | SLI from the client's perspective, per journey | Component health only |
| Set a target | Convert nines to minutes; check dependency chain | Choosing "99.99%" because it sounds good |
| Control cost | Bounded labels, sampling, retention tiers | Raw URLs or user ids as labels |
| Page responsibly | Burn-rate alerts with runbooks | Cause-based alerts for everything |
| Investigate | Hypotheses, evidence, contradiction | Anchoring on the first theory |
| Keep the app safe | Non-blocking exporters, tested collector outage | Synchronous telemetry in the request path |
| Learn from failure | Blameless postmortem with owned, dated actions | Generic "be careful" action items |

## Knowledge consolidation

- An **SLI** is good events ÷ valid events; an **SLO** is a target over a window; the **error budget** is what remains of 100%. The SLI must be specified: good event, valid event, source, window, owner.
- Choose **user journeys**, measure near the user, state what is invisible, and express latency SLIs as **fractions** under a threshold using a bucket boundary at that threshold.
- Convert the target to **minutes and requests** before choosing it; chained hard dependencies multiply.
- The **error-budget policy** is agreed in advance and has an explicit exception path.
- **Burn rate** = error ratio ÷ budget fraction; **budget consumed** = burn rate × (window ÷ SLO window); alerts pair a long and a short window so they catch real problems and reset quickly.
- A page must be **urgent, actionable and novel**; slow burns are tickets.
- Incident response means **symptom and start time, hypotheses, evidence, one reversible action at a time, communication on a cadence**; mitigate before finding the root cause.
- Postmortems are **blameless**, produce **owned, dated, specific actions** of types prevent, detect and mitigate, and record what the telemetry could not tell.
- A telemetry **contract** makes consistent, safe, affordable observability the default.

## Exercises

**Exercise 1 — Write an SLI specification.** For a journey in a service you know (or `GET /v1/orders/{id}`), write the five items: good event, valid event, data source, window, owner. Decide how 4xx responses are treated and justify it.

**Exercise 2 — Budget arithmetic.** A service handles 90,000,000 valid requests per 30 days with a 99.95% SLO. Compute the budget in requests and in minutes of full outage. An incident lasts 45 minutes at an average of 30 requests per second with a 12% error ratio. Compute requests, bad requests, budget share and burn rate.

**Exercise 3 — Thresholds.** For a 99.5% SLO over 30 days, compute the error ratios corresponding to burn rates 14.4, 6, 3 and 1. Compute the budget fraction consumed in 1 hour at 14.4 and in 6 hours at 6.

**Exercise 4 — Will it page?** Using the multi-window table for a 99.9% SLO, state which alerts fire in each case: (a) 100% errors for 3 minutes then recovery; (b) 2% errors continuing for 2 hours; (c) 0.5% errors continuing for 3 days; (d) 0.05% errors continuing indefinitely.

**Exercise 5 — Dependency chain.** A journey depends in series on four components at 99.95%, 99.9%, 99.99% and 99.8%. Compute the combined availability. Which single improvement gives the most benefit? Propose a design change that would raise the combined number without changing any component.

**Exercise 6 — Run a mock incident.** In staging, introduce a latency fault into a dependency while a colleague who does not know the cause acts as on-call. Observe the first fifteen minutes. Produce a timeline, three hypotheses at 10 minutes, and a postmortem using the template, with at least one action each of the types prevent, detect and mitigate.

**Solution notes.**

*Exercise 1.* A strong answer defines good events using business semantics (the response was correct and fast enough), excludes health checks and load tests from valid events, names the data source and its blind spots, and picks a single owner. For 4xx: usually excluded as caller errors, except where the service itself causes them (own rate limiting, own routing).

*Exercise 2.* Budget fraction 0.0005, so 90,000,000 × 0.0005 = 45,000 bad requests; full outage minutes 43,200 × 0.0005 = 21.6. Incident: requests 30 × 45 × 60 = 81,000; bad 12% × 81,000 = 9,720; budget share 9,720 ÷ 45,000 = 21.6%; burn rate 12% ÷ 0.05% = 240. (At burn rate 240 the whole budget would be gone in 720 ÷ 240 = 3 hours.)

*Exercise 3.* Budget fraction 0.005. Error ratios: 14.4 × 0.5% = 7.2%; 6 × 0.5% = 3%; 3 × 0.5% = 1.5%; 1 × 0.5% = 0.5%. Consumed: 14.4 × 1/720 = 2%; 6 × 6/720 = 5%. The fractions of budget consumed do not depend on the SLO; the error ratios do.

*Exercise 4.* (a) 100% errors for 3 minutes: the one-hour average passes 1.44% after about 52 seconds and the 5-minute average passes it within seconds, so the fast page fires. After recovery the 5-minute window clears within about five minutes, so the page resolves quickly even though the 1-hour window stays elevated; that is the purpose of the short window. The outage consumed 3 ÷ 43,200 ≈ 0.007% of the window's traffic, about 6.9% of the 0.1% budget. (b) 2% for 2 hours is burn rate 20: the fast page fires (once the 1-hour average exceeds 1.44%, after about 43 minutes) and the slow page does too. (c) 0.5% for 3 days is burn rate 5: below 6, so no page; the burn-rate-3 ticket alert fires, and so eventually does the burn-rate-1 ticket. (d) 0.05% is burn rate 0.5: nothing fires and the budget is being spent at half pace, which is acceptable.

*Exercise 5.* 0.9995 × 0.999 × 0.9999 × 0.998 ≈ 0.99640, about 99.64%. The weakest component (99.8%) dominates; improving it to 99.95% raises the product to about 99.79%. A design change: make that dependency asynchronous or optional with a degraded fallback, or add a redundant independent instance (two independent 99.8% units give 1 − 0.002² = 99.9996%), recognising that independence must be real.

*Exercise 6.* Expect that the first ten minutes go to confirming the symptom and finding the start time, and that the first hypothesis is often wrong. The most valuable output is the list of moments when the on-call lacked a signal or a runbook step; each should become an action item.

## Mentoring prompts

Why does a burn-rate alert need two windows? Your SLO is met and users complain; what do you check first? What would you say to a product manager who asks for 99.99% because "downtime is bad"? How would you write an action item that a reviewer can verify was done?

---
