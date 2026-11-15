# T-DEV-07-E — Expert Depth

*Chapter: [T-DEV-07 — Datadog Monitoring](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-07-e"></a>
#### T-DEV-07-E — Expert Depth

## Why this matters

By this level you can instrument a service, investigate with traces and logs, define objectives and keep monitoring in reviewed code. The questions that remain are the ones where there is no single correct configuration. Should a large company run one Datadog organisation or several? Where in the pipeline should data be dropped, and who is allowed to decide? What does one extra tag cost across forty teams? How do you move hundreds of services from one monitoring system to another without going blind in between? Each answer is a trade-off between money, risk, autonomy and speed, and each will be wrong in some circumstance.

This section treats monitoring as a **platform** and an **economic system** as much as a technical one. Telemetry is produced by many teams, paid for centrally, consumed under stress, and depended on to detect the failures of everything else, including itself. Expertise here is the ability to design for those facts: to name who pays, who decides and who is woken; to reason with arithmetic rather than adjectives; and to make the default path the correct one.

Markers follow the chapter convention. **[vendor-specific]** marks a Datadog product or behaviour, **[version-specific]** marks anything that depends on a version, plan or current documentation and must be re-verified, and *illustrative* marks example numbers and output. Nothing here quotes real prices or limits; when a number matters, the text shows the formula and asks you to measure. The material assumes the earlier levels: unified service tagging, pipelines, APM, monitors, SLOs, Terraform-managed assets, and cost awareness.

## First principles: the telemetry value chain

Think of observability data as a supply chain with four stages, each of which has its own cost and failure modes.

```text
 produce            ->  transport and process     ->   store and index     ->   consume
 (code, SDK,            (Agent, Collector,             (retention tiers,        (dashboards, monitors,
  libraries, logs)       pipelines, routing)            archives, indexes)       investigations, audits)
 cost: engineering     cost: compute, network,        cost: per-unit price     value: decisions made,
 effort, CPU           operations                     x volume x retention     incidents shortened
```

Three observations organise everything below.

1. **Cost is decided early, mostly by people who do not see the bill.** A developer adds a tag or a log line; the effect appears weeks later in a different budget. The cheapest place to control volume is the earliest one. The most reliable place is the last one. A mature design uses both.
2. **Value is concentrated.** A small part of telemetry answers most investigations: error traces, slow traces, objective-related metrics, deploy markers, a few log fields. Most of the rest is insurance. Insurance can be priced and tiered, not simply purchased in unlimited quantity.
3. **Trust is a feature.** A team that has been burnt by missing data, an alert that never fired or a dashboard that lied stops using the platform. Completeness, correctness and freshness of the telemetry itself are therefore reliability concerns with their own objectives.

## Enterprise architecture

### Organisation topology

**[vendor-specific]** Datadog accounts are organised into *organisations*, which can be linked in parent-child arrangements, hosted on a *site* (region), and divided internally by teams, roles and access controls. **[version-specific]** Feature names, limits and which controls exist for each plan change; use the table as a reasoning template and check current capabilities.

| Topology | Strengths | Weaknesses | Fits when |
| --- | --- | --- | --- |
| One organisation, many teams, role-based access | Shared dashboards, one place to search, simplest identity | Noisy-neighbour risk, shared quotas, blast radius of a bad admin action | Most companies under a single compliance regime |
| One organisation per environment (production apart from non-production) | Production data and keys isolated; separate admin rights | Cross-environment comparison is harder; duplicated setup | Strong separation duties, regulated production |
| One organisation per business unit or tenant | Hard isolation, separate billing and policy | Duplicate platform engineering; no cross-unit view | Mergers, subsidiaries, contractual isolation |
| One organisation per region or data-residency zone | Data stays in a jurisdiction | Global views need federation; sites differ in features | Data-residency obligations |

Choosing is a risk decision, not a preference. Ask four questions: What must be impossible (for example, a non-production engineer reading production logs)? What must be easy (a global incident view)? Who pays, and do they need separate invoices? How will a merger or divestiture be handled? Record the answers; splitting an organisation later is much harder than starting split.

### Identity, access and keys

| Concern | Design |
| --- | --- |
| Human access | Single sign-on with the corporate identity provider; automated provisioning and de-provisioning **[vendor-specific]**; no shared accounts |
| Roles | A small set of standard roles plus custom roles for specific duties (dashboard editor, monitor editor, log reader for one index); read access wider than write access |
| Fine-grained restriction | Restrict who may edit a given monitor or dashboard and who may read particular log indexes **[version-specific]**; keep rules in code where supported |
| API keys | One per cluster or environment so revocation is surgical; stored in a secret manager; rotation automated and rehearsed |
| Application keys | Owned by service accounts, not people; narrow scopes; short review cycle; separate keys for plan and apply pipelines |
| Audit | Review the platform's audit trail for key creation, monitor deletion and role changes **[vendor-specific]** |

Key rotation is a procedure that must be tested before an emergency. A workable shape is: create the new key, distribute it through the secret manager, roll the Agents gradually, confirm by `agent status` and by data arriving under the new key's identity, then delete the old key. Practise it quarterly in a non-production organisation, and write down how long it took.

### Network, egress and the Agent fleet

Agents need outbound access to Datadog's intake endpoints for your site. In locked-down networks, route through a forward proxy or a private connectivity option. **[vendor-specific]** Datadog documents proxy settings and private networking options; **[version-specific]** the list of domains and ports changes, so source it from current documentation and review it when firewall rules are audited. Decide in advance what happens during an egress outage: Agents buffer briefly and then drop, so data in the gap is lost unless another path (a local archive, a second route) exists.

At scale, the Agent is a fleet of software that needs lifecycle management.

| Concern | Practice |
| --- | --- |
| Deployment | One Agent per host (DaemonSet in Kubernetes), deployed by the same tooling as other platform software |
| Version policy | A supported range, with a canary ring first; a monitor on version skew by tag |
| Resource limits | Measure the Agent's own CPU and memory at your scale; set requests and limits from measurement, not from defaults |
| Configuration | Layered: platform defaults in the chart or operator, per-team overrides by label or annotation |
| Cluster-level data | A cluster-level component collects cluster events and metadata once, instead of every node asking the control plane **[vendor-specific]** |

```yaml
# Helm values for the Datadog chart: platform defaults for a production cluster
# [version-specific] key names follow the chart at the time of writing; verify against the chart version you pin
datadog:
  site: datadoghq.com
  apiKeyExistingSecret: datadog-api-key     # created by the secret manager integration, never in values
  clusterName: prod-eu-1
  logs:
    enabled: true
    containerCollectAll: false              # opt-in per workload, not collect-all
  apm:
    socketEnabled: true                     # unix socket: lower overhead than TCP per pod
  dogstatsd:
    socketEnabled: true
    useHostPort: false
  tags:
    - "platform:kubernetes"
    - "region:eu-1"
clusterAgent:
  enabled: true
agents:
  containers:
    agent:
      resources:
        requests: { cpu: 200m, memory: 256Mi }   # illustrative; set from measurements
        limits:   { memory: 512Mi }
```

Two details deserve emphasis. `containerCollectAll: false` forces teams to opt in to log collection, which makes volume a conscious decision. And tags added at the cluster level (cluster name, region) should be few and stable: every tag on every host multiplies metrics and, in some products, host-level costs.

## Telemetry routing

Routing decides which data goes where, in what shape and at what cost. There are several places to do it; each has capabilities the others lack.

| Layer | Can do | Cannot (or should not) do |
| --- | --- | --- |
| Application library | Drop at source: no instrumentation for health checks; bounded tags; sampling decision at the root (head sampling) | Change after deployment; handle policy centrally |
| Datadog Agent | Local collection; log include/exclude rules; basic sampling defaults; secrets handling | Sophisticated multi-destination routing |
| OpenTelemetry Collector | Vendor-neutral processing: attribute deletion, renaming, batching, tail sampling, fan-out to several destinations | Provide vendor features that need vendor SDKs; run unattended without capacity planning |
| Dedicated pipeline layer for logs and metrics **[vendor-specific]** | Parse, filter, redact, enrich and route to multiple destinations before the vendor | Replace good logging discipline |
| Vendor backend | Indexing choices, retention, exclusion, quotas, archives | Undo data that was never sent; recover data that was dropped upstream |

### A Collector design

```yaml
# otel-collector.yaml — gateway mode; [version-specific] component names, connector use, and env syntax
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 25
  attributes/drop_high_cardinality:
    actions:
      - { key: enduser.id,         action: delete }
      - { key: http.request_id,    action: delete }
  probabilistic_sampler/normal:
    sampling_percentage: 5
  batch:
    timeout: 5s
    send_batch_size: 8192

connectors:
  datadog/connector: {}          # computes trace statistics from ALL spans before sampling

exporters:
  datadog:
    api:
      key: ${env:DD_API_KEY}
      site: datadoghq.com

service:
  pipelines:
    traces/stats:                 # every span goes here: counts and latency stay exact
      receivers: [otlp]
      processors: [memory_limiter, attributes/drop_high_cardinality, batch]
      exporters: [datadog/connector]
    traces/sampled:               # only a sample of spans is stored and indexed
      receivers: [otlp]
      processors: [memory_limiter, attributes/drop_high_cardinality, probabilistic_sampler/normal, batch]
      exporters: [datadog]
    metrics:
      receivers: [otlp, datadog/connector]
      processors: [memory_limiter, batch]
      exporters: [datadog]
```

The key idea is in the comment. If a Collector samples spans and the backend then computes request counts from the sampled spans, every rate it reports is wrong by the sampling factor. Computing statistics *before* sampling, and sending those statistics separately, preserves exact rates and error ratios while storing fewer spans. **[version-specific]** Whether this is needed depends on the path you choose, because the vendor Agent computes such statistics itself; confirm the behaviour for your versions with a comparison test before trusting any SLO built on the result.

**Sampling approaches.**

| Approach | Decision point | Strengths | Weaknesses |
| --- | --- | --- | --- |
| Head sampling | At the start of the trace | Cheap; no buffering | Cannot know whether the trace will be an error or slow |
| Tail sampling | After the trace completes | Keeps all errors and slow traces | Needs buffering and all spans of a trace on the same Collector (consistent routing by trace id); memory-hungry |
| Rule-based per service | Configuration per service | Predictable cost by tier | Rules need maintenance |
| Retention filters in the backend **[vendor-specific]** | After ingestion | Keeps selected traces searchable longer | Costs ingest first |

Tail sampling forces an architectural cost. All spans of one trace must reach the same Collector instance, so a first layer of Collectors routes by trace id to a second layer that makes the sampling decision. That means two layers to run, capacity to plan (the second layer holds spans in memory while waiting for traces to complete), and a decision on what to do when the buffer overflows. Use it only where the information gain (keeping every error and slow trace for a high-traffic tier-1 service) is worth the operating burden.

### Routing logs

Logs carry the most volume and often the most sensitive content. Typical routing policy:

| Class | Destination | Retention | Notes |
| --- | --- | --- | --- |
| Errors and warnings from tier 1 | Searchable index | Short to medium | Fast incident search |
| Informational application logs | Archive in your object storage, optionally a small indexed sample | Long, cheap | Rehydrate on demand **[vendor-specific]** |
| Access logs | Metrics generated from logs; a sample indexed | Short | Count and latency are the useful part |
| Security and audit events | Security tooling and a separate, access-controlled archive | By regulation | Not mixed with application indexes |
| Debug logs | Not shipped in production, or enabled temporarily | Hours | Requires a documented switch |

Redaction belongs *before* data leaves your boundary where possible, because a leak that reaches a third party is hard to retract. Test redaction with canary values and treat failing that test as a release blocker.

### Failure behaviour of the path

Every hop has a buffer, and a buffer is a promise to lose data in a defined way. Document, for each hop, what happens under pressure.

| Hop | Under overload | Observable signal | Design response |
| --- | --- | --- | --- |
| Application to Agent | Spans dropped or blocked briefly | Tracer logs; Agent drop counters | Local socket; size limits; alert on drops |
| Agent to intake | Retry, then drop | Forwarder retry and drop counts | Proxy capacity; alert on drop rate |
| Collector queues | Queue full, refusals | Collector's own metrics | Memory limiter; autoscale; shed lower tiers first |
| Backend quotas | Data not indexed when daily quota is reached | Usage page; quota notifications **[vendor-specific]** | Quotas per index so one noisy team cannot starve another |

Define **telemetry service levels** and measure them: the proportion of expected heartbeat samples that arrived, end-to-end latency from event to queryable, and drop rate at each hop. These become the standard by which you can say "our dashboards are trustworthy".

## Cardinality economics

### The arithmetic

A custom metric's series count is the product of each tag's distinct values. A metric `orders.processed` with `env` (3 values), `region` (4) and `status` (5) has \(3 \times 4 \times 5 = 60\) series. Add a `customer_id` tag with 20,000 customers and it becomes 1,200,000 series, a 20,000-fold increase from one line of code. **[vendor-specific]** Custom metrics are typically billed by distinct name and tag-value combinations seen in a period, so the multiplication is a billing multiplication.

A less obvious multiplier is **churn**. In Kubernetes, a tag like `pod_name` takes a new value for every pod. With 40 replicas and 6 rollouts a day there are 240 distinct pod names a day, even though only 40 exist at once. Billing on distinct values seen over a period makes churn expensive. The same applies to container ids, build ids and ephemeral instance names.

```python
# cardinality.py — project series counts before a change ships
from math import prod

def series(tags: dict) -> int:
    return prod(tags.values())

baseline = {
    "orders.processed":   {"env": 3, "region": 4, "status": 5},
    "orders.latency":     {"env": 3, "region": 4, "route": 25},
    "inventory.lookups":  {"env": 3, "region": 4, "outcome": 3},
}

proposals = {
    "add customer_id to orders.processed": ("orders.processed", {"customer_id": 20_000}),
    "add pod_name to orders.latency":      ("orders.latency",   {"pod_name": 240}),
    "add sku_group to inventory.lookups":  ("inventory.lookups", {"sku_group": 12}),
}

base_total = sum(series(t) for t in baseline.values())
print(f"baseline total series: {base_total:,}")
for label, (metric, extra) in proposals.items():
    new = series({**baseline[metric], **extra})
    old = series(baseline[metric])
    delta = new - old
    print(f"{label:42s} {old:>9,} -> {new:>11,}  (+{delta:,}; x{new/old:,.0f}; "
          f"{(base_total+delta)/base_total:,.1f}x total)")
```

```text
# Output (computed from the script above)
baseline total series: 396
add customer_id to orders.processed           60 ->   1,200,000  (+1,199,940; x20,000; 3,031.2x total)
add pod_name to orders.latency               300 ->      72,000  (+71,700; x240; 182.1x total)
add sku_group to inventory.lookups            36 ->         432  (+396; x12; 2.0x total)
```

Read the result as a decision aid in review. The first proposal must be rejected or redesigned (use logs or traces for customer analysis). The second is a churn trap (use a stable grouping such as `deployment` or `version`). The third is cheap and probably useful.

### Where percentiles and distributions fit

Percentiles of latency across many instances cannot be computed from per-instance percentiles. Platforms offer distribution-style metrics that keep enough information to calculate global percentiles at query time. **[vendor-specific]** In Datadog these are *distribution metrics*, and enabling percentile aggregations on many tag combinations can multiply the stored series. **[version-specific]** Pricing and options for this feature have changed; check current rules and enable percentiles only on metrics, and only for tag groupings, that people actually query.

### Separating ingestion from indexing

**[vendor-specific]** For metrics, logs and spans Datadog separates what you *send* from what is *kept searchable or queryable*. For custom metrics, tag configuration can restrict queryable tag combinations so that tags sent by code do not all become billable series. For logs, exclusion filters and archives separate ingestion from indexing. For spans, ingestion controls and retention filters do the same. This gives a powerful but dangerous lever: you can reduce cost without changing code, and you can also remove the ability to answer a question after the fact. Treat each use as a written decision with an owner.

| Product | Ingest side lever | Index side lever | What you lose |
| --- | --- | --- | --- |
| Custom metrics | Library and Agent tag policy | Tag allow-list per metric | Slicing by removed tags |
| Logs | Source level, pipeline drops | Exclusion filters, index per tier | Full-text search on excluded lines |
| Spans | Sampling rules | Retention filters | Individual non-retained traces |

### Retention and sampling by service tier

Decide per tier what to keep, and write down what you will *not* be able to answer afterwards.

| Data | Tier 1 (revenue path) | Tier 3 (internal tool) | What is lost |
| --- | --- | --- | --- |
| Error traces | Keep all | Keep all | Nothing meaningful |
| Slow traces (above objective) | Keep all | Sample about a quarter | Some rare slow requests |
| Normal traces | 1–5% | 0–1% | Inspecting an arbitrary healthy request later |
| Logs | Index errors and warnings; archive the rest | Index errors only | Cheap full-text search on info-level logs after the index window |
| Metrics | Full resolution for objective-related metrics | Default | Fine-grained history after rollup |

Compliance, security investigation and capacity planning are the questions that usually need longer retention; arrange archives for them deliberately rather than extending retention everywhere.

### Unit economics and showback

Absolute spend means little; **cost per unit of business activity** shows trends. Useful ratios are telemetry cost per million requests, per service, per team and per environment.

\[
\text{telemetry cost per million requests} = \frac{\text{monthly cost attributable to the service}}{\text{requests that month} / 10^{6}}
\]

Publish the ratio per service. Teams whose ratio rises without a feature to justify it have either changed logging or tags carelessly, or are seeing growth that the ratio normalises. **[vendor-specific]** Datadog offers usage-attribution features that split cost by tag; **[version-specific]** their availability depends on plan, so validate that your `team` tag is applied consistently, because attribution is only as good as the tags.

Choose between *showback* (teams see their cost) and *chargeback* (teams are billed). Showback changes behaviour at little organisational cost and is the right first step. Chargeback adds incentive and friction: teams may under-instrument to save budget. If you chargeback, protect a baseline of safe telemetry (objective metrics, error traces, heartbeats) outside the team's budget.

### Detecting a spike in hours, not at invoice time

```python
# usage_spike.py — compare two snapshots of series counts per metric; flag growth over a threshold
import json, sys

def load(path):
    with open(path) as handle:
        return json.load(handle)           # {"metric.name": series_count, ...}

def spikes(before, after, factor=1.5, min_new=1_000):
    for name, count in sorted(after.items()):
        old = before.get(name, 0)
        grew = count - old
        if grew >= min_new and (old == 0 or count / old >= factor):
            yield name, old, count

if __name__ == "__main__":
    before, after = load(sys.argv[1]), load(sys.argv[2])
    found = list(spikes(before, after))
    for name, old, new in found:
        print(f"SPIKE {name}: {old:,} -> {new:,}")
    sys.exit(2 if found else 0)
```

A scheduled job that fetches series counts per metric (from your platform's usage or metrics-volume views **[version-specific]**), runs this comparison against yesterday's snapshot and opens a ticket to the metric's owning team is cheap. The more important design decision is *ownership mapping*: a spike on a metric with no owner is a spike nobody fixes. Derive the owner from the metric name prefix or the `team` tag and maintain that mapping as data.

## Multi-team governance

### A model that scales

Governance is the set of agreements that let many teams use shared tooling without chaos and without a ticket queue. The principle is *paved road with guardrails*: a path that is easier than going off it, and limits that make the worst case survivable.

| Asset | Platform team provides | Service team owns | Review cadence |
| --- | --- | --- | --- |
| Tags | Allowed keys (`service`, `env`, `version`, `team`, `tier`), value formats, CI check | Correct values for each service | Quarterly: delete unused keys |
| Monitors | Templates for burn rate, latency, saturation and heartbeat | Thresholds, routing, tuning | Monthly review of monitors that fired but led to no action |
| Dashboards | One standard service dashboard per tier | Extra panels for their own domain | Remove dashboards with no views in 90 days |
| Paging | Escalation policies, integrations | Which monitors page and who is on call | After every incident |
| Logs | Index tiers, exclusion defaults, scrubbing rules, archive | Log levels, fields, structure | Quarterly volume review per team |
| Cost | Visibility per service, budgets | Staying within budget or justifying growth | Monthly cost review |
| Keys and access | Roles, rotation, audit | Using service accounts, no personal keys in automation | Quarterly access review |

**Guardrails versus gates.** A *gate* stops work until someone approves (a ticket to create a monitor). A *guardrail* lets work proceed within safe limits (a template that creates a compliant monitor automatically; a quota that stops one team from consuming everything). Prefer guardrails, because gates scale with the platform team's headcount, and they create the "central observability team as bottleneck" anti-pattern. Keep gates only for high-risk, low-frequency decisions: new organisations, retention extensions, and exceptions to tag policy.

**Policy as code.** Every rule that can be checked by a program should be. Extend the Professional-level lint into a library of rules run in CI and on a schedule:

| Rule | Check | Failure handling |
| --- | --- | --- |
| Tag keys | Required keys present; no unapproved keys; values match patterns | Block in CI for new assets; warn for legacy |
| Ownership | `team` exists in the team registry | Block |
| Routing | A paging monitor names a team handle that exists | Block |
| Runbook | A link that responds | Warn; weekly report |
| No-data decision | Explicit | Block for tier 1 |
| Cost hygiene | Log exclusion filter or archive present for every index | Block |
| Dead assets | A dashboard unused for 90 days; monitor muted for 30 days | Ticket to owner; archive after notice |

**Exceptions.** Every rule needs an exit: a time-limited exception, recorded in code with an owner and expiry date, reviewed when it expires. Without an exception path, people bypass the rule silently; with one, the exceptions become visible data about whether the rule is wrong.

**Tag governance in detail.**

- Maintain a *tag registry* in version control: key, meaning, allowed value format, owner, whether it may appear on metrics (bounded) or only logs and traces (possibly unbounded).
- Distinguish **dimension tags** (small, bounded, used for grouping: `env`, `region`, `tier`, `status`) from **attribute fields** (unbounded, searchable but not metric dimensions: `customer_id`, `order_id`, `request_id`).
- Reserve `service`, `env`, `version` and `team` as platform-owned; teams may add their own prefixed keys within the cardinality budget.
- Review the registry quarterly; a key with no consumers is deleted from code and from tag configurations.

**Delegated administration.** Let teams administer their own monitors, dashboards and log indexes inside their own namespace (naming prefix, team tag, restriction policy), while the platform owns shared resources. Delegation works only when the guardrails are enforced by tooling, not by trust.

### Measuring the programme itself

A monitoring programme is itself a service. Give it objectives.

| Measure | Why it matters | Healthy direction |
| --- | --- | --- |
| Actionability: share of pages that led to a real action | Alert fatigue | Rising; investigate below an agreed floor |
| Coverage: tier-1 services with all standard assets | Blind spots | Approaching all |
| Time to detect for injected faults (from drills) | Real alerting speed | Meeting the service's stated target |
| Share of assets with an owner | Orphans decay | Approaching all |
| Telemetry service levels (completeness, freshness) | Trust | Meeting objectives |
| Cost per million requests by team | Efficiency | Stable or falling unless features justify |
| Time to onboard a new service | Platform usability | Falling |

Measures are conversation starters. A programme that optimises one number (for example, fewer pages) by muting monitors has gamed it. Pair counts with drill results, which cannot be gamed by silence.

## Reliability of the monitoring itself

Monitoring has failure modes of its own. The principle is *independence*: the detection of a failure must not depend on the thing that failed.

| Failure | Symptom | Detection independent of the failing component | Response |
| --- | --- | --- | --- |
| Agent crash on a host | Host data stops | Missing-data monitor on a heartbeat emitted by the service | Restart; check for out-of-memory or bad configuration |
| API key revoked or rotated | All data from a group stops at once | External synthetic check or heartbeat from outside | Re-issue key through the secret manager; confirm rollout |
| Network partition to intake | Data buffered then dropped | Agent status and local queue metrics | Verify egress; consider a regional proxy |
| Vendor intake outage | Everything missing at once | Status feed plus a secondary notification path (chat or email) | Switch to local diagnostics (logs, orchestrator commands, host tools) |
| Collector overload | Gaps for sampled data, delays | Collector's own metrics shipped by a different path | Scale; shed lower tiers first |
| Clock skew | Spans out of order, gaps | Time-synchronisation monitor | Fix time synchronisation; disregard the skewed window |
| Tag drift after deployment | Monitors silently stop matching | "No data for service X" monitor and a CI check on tags | Fix the tag source; add the check |
| Quota reached | Data stops being indexed mid-day | Quota-approach monitors on usage metrics | Raise quota or exclude; protect tier 1 first |

The "monitoring is down" runbook must work *without* the monitoring platform: how to find the failing service from host logs and orchestrator commands, where the on-call contact lives, who may declare an incident when no alert will ever arrive, and where decisions are recorded. Rehearse it by switching off the notification path in a test organisation and seeing whether the team notices within the time you promised.

A synthetic **dead man's switch** is the simplest independent check: a scheduled job outside your infrastructure sends a heartbeat to the platform and the platform alerts on its absence, *and* a second job outside the platform checks that the alert path itself delivers. The two checks look at each other.

## Migration and scale trade-offs

### Moving between monitoring systems

A migration (from a self-hosted stack to a commercial one, between vendors, or consolidating several tools) is the highest-risk moment in a monitoring programme, because you can lose visibility while believing you have it.

| Phase | Goal | Exit criterion |
| --- | --- | --- |
| Inventory | List services, dashboards, alerts, log sources, owners, consumers | Every asset has an owner, or is slated for deletion |
| Triage | Decide per asset: migrate, rebuild, retire | Retire a large share; do not migrate rot |
| Dual-run | Send telemetry to both systems | Both receive equivalent data, verified |
| Parity validation | Compare numbers, alert behaviour and investigation capability | Differences explained, within agreed tolerance |
| Cutover per service | Move paging to the new system | Drill passed on the new system; rollback ready |
| Decommission | Turn off the old system | Cooling-off period; archives retained as required |

**Principles.**

- **Dual-run before cutover.** Parity cannot be reasoned about; it must be measured. For each tier-1 service compare request counts, error ratios and latency percentiles between systems over the same period, and explain differences (sampling, aggregation windows, units, staleness handling).
- **Alert semantics differ.** Rates, windows, staleness handling and "no data" behaviour are not identical across systems. Translating a query textually produces a monitor that looks right and behaves differently. Re-prove each paging alert with a fault drill in the new system.
- **Move the instrumentation to a standard first.** If services emit OpenTelemetry through a Collector, adding a second destination is configuration, not code change. If they use proprietary libraries, migration is an application change across every team; budget accordingly.
- **Plan for rollback per service.** Keep the old paging path alive until the new one has passed a drill and lived through a real incident or two.
- **Retire deliberately.** Dashboards and alerts that nobody owned should not be migrated; they should be deleted with notice.
- **Do not migrate the bill.** Dual-running doubles cost for a period. Plan and approve that cost, and set an end date.

```text
Parity record for one service during dual-run (illustrative)

Service: orders-api   Window: 7 days   Tier: 1
Metric                       Old system     New system     Difference   Explained by
requests (millions)          12.40          12.38          -0.2%        window-edge alignment
error ratio (%)              0.31           0.30           -0.01 pt     rounding
p95 latency (ms)             142            139            -2%          histogram bucketing
paging fired in test drill   yes, 2m10s     yes, 1m55s     -            -
Verdict: PASS. Cutover scheduled; rollback path kept for 14 days.
```

### Scale limits to plan for

Systems fail first where they are not looked at. For a large fleet, check these in a load or soak test rather than discovering them in an incident. **[version-specific]** Specific limits (rates, payload sizes, defaults) change between versions and plans, so find them in current documentation and test your own numbers.

| Area | Failure at scale | Mitigation |
| --- | --- | --- |
| Custom metrics over UDP | Packet loss when the local receive buffer fills during bursts | Unix domain sockets; client-side aggregation; buffer sizing; watch drop counters |
| Agent resource use | Memory and CPU growth with number of checks, containers and log sources | Measure per-node; tune; limit enabled integrations; separate heavy workloads |
| Pod and container churn | Metric series and host objects multiply with short-lived workloads | Stable grouping tags; avoid instance-level tags on metrics |
| API rate limits | Terraform plans and exports throttled | Split state by domain; reduce refresh; cache; stagger scheduled jobs |
| Terraform state size | Slow plans, risky applies | State per environment and domain; modules for repeated patterns |
| Collector gateways | Memory pressure from tail sampling; uneven load | Trace-id aware load balancing; capacity tests; autoscaling on queue length |
| Dashboard and monitor sprawl | Thousands of assets, slow search, unclear ownership | Ownership tags, dead-asset policy, standard templates |
| Alert storms | One root cause pages dozens of teams | Dependency-aware routing and composite or parent monitors **[vendor-specific]**; page the owner of the cause |

**Alert storms** deserve emphasis. When a shared dependency (database, network, identity provider) fails, every service that depends on it alerts at once. Teams that are paged for symptoms cannot see the cause, and the incident commander drowns. Design for this explicitly: dependency-aware grouping, one monitor per shared dependency that pages its owner, suppression of downstream pages while the upstream alert is open, and a status page entry that names the dependency. Verify it with a drill that kills the shared dependency in staging.

### Expert trade-offs at a glance

| Decision | Option A | Option B | Choose A when | Choose B when |
| --- | --- | --- | --- | --- |
| Organisation shape | One organisation | Several | Single compliance regime, strong role controls | Hard isolation, residency or contractual separation |
| Instrumentation | Vendor library | OpenTelemetry | Speed, vendor-only features matter more than portability | Portability matters; many teams; long horizon |
| Collection | Agent only | Agent plus Collector gateway | Simple estates | Routing, fan-out, redaction or tail sampling are needed |
| Sampling | Head | Tail | Cost and simplicity dominate | Keeping every error and slow trace matters |
| Log policy | Index broadly | Index narrowly, archive widely | Small volume; rich search valued | Volume is large; cost-sensitive |
| Ownership | Central observability team | Federated with paved road | Small company; few services | Many teams; need self-service |
| Cost allocation | Showback | Chargeback | Early maturity | Mature; incentive needed, baseline protected |
| Assets | Code only | Code with break-glass | Strict regulation | Operational realism |

## Vendor strategy

Standardise on OpenTelemetry instrumentation and a Collector layer as an abstraction; treat vendor-specific features (proprietary dashboards, notebooks, security products) as value-added with a conscious switching cost. Export monitor and dashboard definitions as code so migration is possible. Evaluate vendors on query power, retention costs, cardinality handling, support, data residency and security attestations. Evaluate with a small proof of concept rather than slides.

| Criterion | Test to run |
| --- | --- |
| Query power | Reproduce your five hardest investigations; time them |
| Cost model | Feed a month of your real volumes into the pricing model; include indexing, custom metrics, spans, logs, retention |
| Cardinality handling | Add a high-cardinality tag on purpose; observe the cost and the controls |
| Portability | Re-point the Collector's export to a second backend; export monitors as code and re-create them |
| Data residency and attestations | Confirm region options and required certifications against your requirements |
| Support and operations | File a real question; measure response and quality |
| Exit | Export your data and definitions; time it and check completeness |

Switching cost is lowest when instrumentation is OpenTelemetry, definitions live in Terraform (or equivalent), and dashboards derive from templates. It is highest where teams have built on proprietary notebooks, bespoke query functions, or vendor-specific agents with no export. Adopt such features knowingly, and record the decision, the owner and the exit path. Contract terms (commitment levels, overage behaviour, notice periods) are part of the architecture: a commitment that your own cost controls could make you under-use is a financial risk.

## Failure modes of the observability programme

- **Alert fatigue.** Pages that no one acts on teach people to mute monitors. Track actionability; retire or tune monitors that are not.
- **Dashboard sprawl.** Dozens of near-duplicate dashboards, none trusted. Standard dashboards per tier and a dead-asset policy.
- **Cost surprises** that arrive after a quarter-end review, because cost was never attributed to a service owner.
- **A central observability team that becomes a bottleneck.** Provide self-service, templates and guardrails instead of tickets.
- **Metrics theatre.** Dashboards of green numbers that no drill has ever tested.
- **Migration by copy-paste.** Alerts translated textually behave differently; the new system "works" until the first incident.
- **Single point of blindness.** Detection, notification and communication all depend on one vendor or one network path.
- **Unowned cleverness.** A brilliant custom pipeline that only one engineer understands.

## Knowledge consolidation

- Telemetry is a value chain; cost is set early, trust depends on telemetry's own completeness and freshness.
- Organisation topology is a risk decision: isolation, ease of global view, billing and merger handling.
- Keys, roles and access are managed like production credentials: scoped, rotated and rehearsed.
- Routing happens at several layers; compute statistics before sampling; tail sampling has an architectural cost.
- Cardinality is multiplication, and churn is a hidden multiplier; project before shipping, and detect spikes by owner in hours.
- Governance means a paved road with guardrails, policy as code, exceptions with expiry and a measured programme.
- Detection of a monitoring failure must be independent of the thing that failed.
- Migration needs dual-run, measured parity, drill-proved alerts and rollback; do not migrate rot.
- Scale fails where nobody looked: UDP buffers, churn, rate limits, state size, alert storms.

## Exercises

**Exercise 1 — Topology decision.** For a fictional company with regulated payments in two regions, an acquired subsidiary and 60 engineering teams, propose an organisation topology, an access model and a billing model. List the three risks you accept and the evidence that would make you revisit.

**Exercise 2 — Key rotation.** In a test organisation, rotate an Agent API key across a small fleet with no data gap. Record the steps, timings, and the evidence that the new key is in use.

**Exercise 3 — Statistics before sampling.** Build a Collector pipeline that samples traces at 5%. First compute request counts from the sampled spans only, then from a pipeline that computes statistics before sampling. Compare both with a known load of N requests.

**Exercise 4 — Cardinality review.** Run the `cardinality.py` script on your own metrics and three proposals from a real change request. Write a review comment for each, with the alternative you recommend.

**Exercise 5 — Spike detector.** Produce two series-count snapshots, add a deliberately high-cardinality tag on one metric between them, and show the detector finding it. Map it to an owner and describe the ticket text.

**Exercise 6 — Governance document.** Write a one-page governance model for a ten-team organisation: asset table, tag registry, exception process and three programme measures. Then name which rule you expect teams to resent most and what you would do about it.

**Exercise 7 — Blind-spot tabletop.** Walk through a vendor intake outage while a customer-facing incident is in progress. State how you detect, communicate and diagnose without the platform.

**Exercise 8 — Alert-storm drill.** In staging, stop a shared dependency used by several services. Count the pages. Redesign routing so exactly one team is paged for the cause, and repeat the drill to prove it.

**Exercise 9 — Migration parity.** Design the parity record for three services during a dual-run: the metrics compared, the tolerance, how differences are explained and the cutover criterion. Say which signals you would not trust to compare.

**Solution notes.**

*Exercise 1.* A strong answer separates regulated payment data (isolated organisation or strict role and index separation per region), the subsidiary (isolated until integration is justified) and the remaining teams (a shared organisation with teams and roles). It accepts duplicated platform work in exchange for isolation and names triggers for revisiting, such as a regulator's interpretation or a measured need for cross-region search. Marks go for stating what must be impossible, not for choosing the most separate design.

*Exercise 2.* Expect a sequence of create, distribute, roll, verify, delete, with a verification that old and new keys are distinguished by the interface or by Agent status. A gap in data suggests that the Agent restarted before the secret was available; check rollout order and secret propagation delay. Record your own timings.

*Exercise 3.* The sampled-only pipeline should report roughly 5% of N hits unless the backend rescales by the sampling rate, and your comparison shows whether your versions do so. The pipeline with a connector should report close to N hits and still store about 5% of traces. If neither matches expectations, check the batching window and the comparison interval before changing the design. **[version-specific]**

*Exercise 4.* Reviews should reject unbounded identifiers for metrics, point to logs or traces for per-customer questions, replace instance names with stable groupings, and approve small bounded tags. Show the series count before and after each recommendation.

*Exercise 5.* The detector should flag the modified metric with its before and after counts. The ticket should name the owner, the change that likely caused it, the series growth, and the deadline for a decision; an owner map that returns nobody is itself a finding.

*Exercise 6.* Look for specific owners, review cadences, a registry with bounded and unbounded categories, exceptions with expiry, and measures paired with drills. The rule teams resent is usually mandatory tagging or log exclusion; the usual remedy is to supply a template that makes compliance automatic and a visible exception path.

*Exercise 7.* A good tabletop names: the independent signal that told you (external probe, status feed, customer reports), the secondary notification path, the commands and local logs used to find the failing service, who declares the incident and where decisions are written. Any step that needs the platform's interface is a gap to close.

*Exercise 8.* Before the redesign, many services page at once with symptom alerts. After it, the shared dependency's own monitor pages its owner, and downstream symptom pages are suppressed or routed to tickets while the upstream alert is open. If downstream teams still page, check the dependency-awareness rule and the evaluation order.

*Exercise 9.* A strong record compares request totals, error ratios, latency percentiles and paging behaviour, with tolerances stated before measurement, differences explained, and a cutover criterion that includes a passed fault drill. Signals you should distrust include anything derived from sampled traces, percentiles averaged across instances, and counters during restarts.

## Mentoring prompts

A team reports "Datadog shows no data": give the ordered checks from the application to the backend, and the checks that make you suspect the platform rather than the team. How would you detect and stop a tag-cardinality cost spike in hours rather than at invoice time, and who gets the ticket? What is the minimum viable set of monitors for a new service, and how do you stop teams muting them? Argue for and against a second Datadog organisation for production. If a vendor doubles its price next year, what in your architecture limits the damage, and what makes it worse? Your tail-sampling tier runs out of memory during an incident: which data do you shed first, and who agreed that in advance?

---
