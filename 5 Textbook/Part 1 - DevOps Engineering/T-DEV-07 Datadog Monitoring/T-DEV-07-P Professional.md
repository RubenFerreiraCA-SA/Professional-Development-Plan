# T-DEV-07-P — Professional Engineering

*Chapter: [T-DEV-07 — Datadog Monitoring](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-07-p"></a>
#### T-DEV-07-P — Professional Engineering

## Why this matters

At Intermediate level you can make one service observable and investigate it. Professional work is different in kind: the monitoring you build must keep working when you are not looking, survive staff changes, be reviewed like code, stay within a budget and give evidence that it does what it claims. A dashboard that one engineer built by hand, with monitors nobody owns and a bill nobody attributes, is a liability dressed as an asset.

Five ideas carry this level. **Reliability targets** (service level objectives) turn "is it good enough?" into a number with a budget. **Error-budget monitors** page on how fast that budget is burning, which is a better trigger than any raw threshold. **Infrastructure as code** makes monitors, dashboards and objectives reviewable and reproducible. **Ownership and cost controls** attach every asset and every cost line to a team. **Verifiable outcomes** require that each claim ("this alert works", "this team can respond") is backed by evidence produced on purpose.

Markers follow the chapter convention: **[vendor-specific]** for Datadog features, **[version-specific]** for details to confirm against current documentation (provider, Agent or API version, plan limits), and *illustrative* for example numbers and output. Prices in this text are placeholders, never Datadog's. The running example stays `orders-api` with its dependency `inventory`.

## First principles: targets, budgets and burn

**Service level indicator (SLI).** A measurable proportion of "good" events, for example *requests that returned a non-5xx status*, or *requests faster than 500 ms*. Choose indicators users feel. CPU is a cause, not an experience.

**Service level objective (SLO).** A target for the SLI over a window, such as 99.9% over 30 days.

**Error budget.** What the target permits you to get wrong: \(1 - \text{SLO}\). With 99.9% over 30 days the budget is 0.1% of events, or, thinking in time, \(0.001 \times 43{,}200\) minutes \(= 43.2\) minutes of total outage. With one million requests in the window, that is 1,000 bad requests.

**Burn rate.** How fast the budget is consumed relative to the rate that would exactly exhaust it at the end of the window. A burn rate of 1 uses the budget exactly over the full window; 10 would exhaust it in a tenth of the window.

\[
\text{burn rate} = \frac{\text{observed bad-event fraction}}{1 - \text{SLO}}
\]

\[
\text{fraction of budget consumed} = \text{burn rate} \times \frac{\text{alert window}}{\text{SLO window}}
\]

Worked example. For 30 days (720 hours), a burn rate of 14.4 sustained for one hour consumes \(14.4 \times 1/720 = 2\%\) of the budget. A burn rate of 6 sustained for six hours consumes 5%. A burn rate of 1 sustained for three days consumes 10%. These three pairs form the standard multi-window pattern: fast burns page, slow burns raise tickets.

Why this beats a raw threshold: "error ratio above 2%" has no connection to what you promised. A steady 0.5% error ratio is within a 98% objective yet violates a 99.9% one; a 3% spike for two minutes may be harmless for a 30-day budget. Burn-rate alerts are proportional to risk.

## SLOs in practice

**Choose the SLI carefully.** Decide what counts as good and what to exclude, and write it down.

| Decision | Options | Guidance |
| --- | --- | --- |
| Good event | Status below 500; status below 500 and latency under threshold | Start with availability; add latency as a second SLO, not a hidden condition |
| Client errors (4xx) | Count as good, exclude, or count as bad | Usually good for availability, since the service behaved correctly; decide per route |
| Health checks and synthetic probes | Exclude from the SLI | They inflate good counts and mask real traffic |
| Scope | Per service and route class | One SLO for "checkout" matters more than one for "everything" |
| Window | 7, 30 or 90 days | 30 days is common; shorter windows react faster but are noisier |
| Data source | Trace metrics (computed from all traffic) | Do not compute SLIs from stored sampled traces |

**[vendor-specific]** Datadog supports metric-based SLOs (good events over total events), monitor-based SLOs (the fraction of time a monitor is OK) and, in newer product versions, time-slice SLOs. **[version-specific]** Check which types and query forms your plan and current product support. For this chapter, a metric-based SLO uses trace metrics.

```hcl
terraform {
  required_providers {
    datadog = {
      source  = "DataDog/datadog"
      version = "~> 3.0"      # [version-specific] pin to the major you have tested
    }
  }
}

provider "datadog" {
  api_url = "https://api.${var.dd_site}/"   # API and application keys come from DD_API_KEY and DD_APP_KEY
}

variable "dd_site" {
  type    = string
  default = "datadoghq.com"
}

resource "datadog_service_level_objective" "orders_availability" {
  name        = "orders-api availability (production)"
  type        = "metric"
  description = "Share of requests that do not return a 5xx status. Owner: team-orders."

  query {
    # Good events: all requests that are not 5xx.  Total events: all requests.
    # Metric and tag names come from the web framework's APM integration; verify in Metrics Summary.
    numerator   = "sum:trace.fastapi.request.hits.by_http_status{service:orders-api,env:production,!http.status_class:5xx}.as_count()"
    denominator = "sum:trace.fastapi.request.hits.by_http_status{service:orders-api,env:production}.as_count()"
  }

  thresholds {
    timeframe = "30d"
    target    = 99.9
    warning   = 99.95
  }

  tags = ["service:orders-api", "env:production", "team:team-orders", "tier:1"]
}
```

**[version-specific]** Provider constraint, resource and attribute names, and the trace-metric names (`hits.by_http_status`, `http.status_class`) depend on provider and Datadog APM versions; run `terraform validate` and open the SLO's query preview to confirm it returns data before relying on it.

**Sanity-check an SLO against reality.** A target that is never missed is too loose to guide decisions; one missed constantly is too tight or measures the wrong thing. After a month, review: did the SLO move when users complained? Did incidents show up in the budget? If an outage you remember left the SLO unchanged, the SLI is wrong.

## Error-budget monitors

An SLO is a number; a **budget monitor** turns it into action. **[vendor-specific]** Datadog provides monitors on a metric-based SLO's burn rate and remaining error budget.

| Alert | Burn rate | Long / short window | Budget used at trigger | Response |
| --- | --- | --- | --- | --- |
| Fast burn | 14.4 | 1 h / 5 min | 2% | Page on-call |
| Medium burn | 6 | 6 h / 30 min | 5% | Page in working hours or high-priority ticket |
| Slow burn | 1 | 3 d / 6 h | 10% | Ticket for the owning team |
| Budget low | n/a | Remaining budget below 25% | up to 75% | Freeze risky releases; review reliability work |

The short window confirms the problem is still occurring, so alerts recover quickly after a fix.

```hcl
resource "datadog_monitor" "orders_fast_burn" {
  name    = "orders-api fast error-budget burn (production)"
  type    = "slo alert"
  message = <<-EOT
    {{#is_alert}}
    The orders-api availability budget is burning at more than 14x the sustainable rate.
    At this speed about 2% of the 30-day budget goes in one hour.
    Runbook: https://runbooks.example.com/orders-high-errors
    SLO: see the linked objective; dashboard: https://app.example.com/dashboards/orders
    @team-orders-oncall
    {{/is_alert}}
    {{#is_recovery}}Burn rate has returned below the threshold.{{/is_recovery}}
  EOT

  # [version-specific] burn_rate() query syntax and window options for SLO alerts
  query = "burn_rate(\"${datadog_service_level_objective.orders_availability.id}\").over(\"30d\").long_window(\"1h\").short_window(\"5m\") > 14.4"

  monitor_thresholds {
    critical = 14.4
  }

  tags = ["service:orders-api", "env:production", "team:team-orders", "tier:1", "kind:slo-burn"]
}
```

**Time to detect, worked out.** With steady traffic and a 99.9% SLO, a *total* outage (100% bad) has burn rate 1,000. The one-hour window averages above 14.4 once about \(14.4/1000 = 1.44\%\) of the hour has been bad: roughly 52 seconds. A partial failure with 5% bad events has burn rate 50; the window needs \(14.4/50 \approx 29\%\) of the hour, about 17 minutes. Add evaluation lag. This is the honest answer to "how fast will we know?": seconds for a hard outage, many minutes for a mild one. If that is too slow for the business, the target or the alert design must change; wishing does not.

**Pair budget alerts with symptoms and heartbeat.** Burn-rate monitors need data. If the Agent stops, no events arrive and burn is undefined. Keep a missing-data monitor (Intermediate) for the same service; it is the independent check that the measurement is alive.

## Infrastructure as code for monitoring

**What goes into code.** Monitors, SLOs, dashboards, log pipelines and indexes, metric tag configurations, retention filters and team definitions. **[vendor-specific]** The Datadog Terraform provider covers each with resources such as `datadog_monitor`, `datadog_service_level_objective`, `datadog_dashboard_json`, `datadog_logs_custom_pipeline`, `datadog_logs_index` and `datadog_metric_tag_configuration`. **[version-specific]** Resource availability and schema change between provider versions; read the provider documentation for your pinned version.

**Why code, not the interface.** Review catches thresholds that make no sense; history shows who changed an alert before the incident; the same module creates the monitors for the tenth service as for the first; recovery after accidental deletion is one apply.

**Layout.**

```text
observability/
  modules/
    service-monitoring/        # one module: SLO, burn monitors, heartbeat, dashboard
      main.tf  variables.tf  outputs.tf
  environments/
    production/
      main.tf                  # one module call per service, from a services map
      terraform.tfvars
    staging/
      main.tf
  policy/
    lint_monitors.py           # checks run in CI (see Verifiable outcomes)
```

```hcl
# environments/production/main.tf
variable "services" {
  type = map(object({
    team        = string
    tier        = number
    slo_target  = number
    runbook_url = string
    oncall      = string          # notification handle, e.g. "@team-orders-oncall"
  }))
}

module "service_monitoring" {
  for_each = var.services
  source   = "../../modules/service-monitoring"

  service     = each.key
  env         = "production"
  team        = each.value.team
  tier        = each.value.tier
  slo_target  = each.value.slo_target
  runbook_url = each.value.runbook_url
  oncall      = each.value.oncall
}
```

```hcl
# terraform.tfvars — the onboarding of a service is a reviewed change to this file
services = {
  "orders-api" = {
    team        = "team-orders"
    tier        = 1
    slo_target  = 99.9
    runbook_url = "https://runbooks.example.com/orders"
    oncall      = "@team-orders-oncall"
  }
  "inventory" = {
    team        = "team-inventory"
    tier        = 2
    slo_target  = 99.5
    runbook_url = "https://runbooks.example.com/inventory"
    oncall      = "@team-inventory-oncall"
  }
}
```

**A delivery pipeline.**

```bash
#!/usr/bin/env bash
# ci/monitoring-plan.sh — runs on every pull request
set -euo pipefail
cd observability/environments/production
terraform fmt -check -recursive ../..
terraform init -input=false
terraform validate
terraform plan -input=false -lock-timeout=60s -out=tfplan
terraform show -json tfplan > plan.json      # keep as a build artefact for reviewers

# A separate scheduled job (read-scoped key) exports live monitors and lints them:
#   curl -s -H "DD-API-KEY: $DD_API_KEY" -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
#        "https://api.${DD_SITE}/api/v1/monitor" > monitors.json
#   python3 observability/policy/lint_monitors.py monitors.json
```

Rules that make it safe:

- The plan job uses keys with the **narrowest scopes** the plan requires; the apply job runs only from the main branch with a separate, more privileged key held in the secret store of the CI system. Keys never appear in the repository.
- **Remote state with locking**, because state describes your alerting; two concurrent applies can fight.
- **Drift detection.** A scheduled `terraform plan -detailed-exitcode` returns exit code 2 when reality differs from code (someone edited a monitor in the interface). Treat drift as a ticket: either fold the change into code or revert it.
- **Break-glass.** During an incident, anyone may edit in the interface (muting, tuning). The edit must be reconciled into code within a stated period, or the next apply will quietly undo it.
- **Importing legacy assets.** Bring hand-built monitors under management gradually: `terraform import datadog_monitor.legacy_cpu 1234567`, write the matching resource, and confirm that `plan` shows no changes. **[version-specific]** Newer Terraform versions also support declarative `import` blocks.
- **Protect from accidental destruction.** Mark SLOs and tier-1 paging monitors with `lifecycle { prevent_destroy = true }` where history matters, and require a review for removals.

## Ownership

Every asset has an owner who can answer: should this exist, who is paged, when was it last reviewed?

| Asset | Required metadata | Where it lives |
| --- | --- | --- |
| Service | `service`, `team`, `tier`, runbook, on-call contact, repository | Service catalogue entry and tags **[vendor-specific]** |
| Monitor | `team`, `service`, `env`, runbook link in message, notification handle | Tags and message |
| SLO | Owner, SLI definition, review date | Description and tags |
| Dashboard | Owner, service, audience | Title convention and tags |
| Log index or pipeline | Owning team, retention reason | Resource name and tags |

**Tiering.** A tier describes consequences, not importance in the abstract: tier 1 serves revenue or safety and may page at any hour; tier 2 supports tier 1 and pages in working hours; tier 3 is internal and gets tickets. Tier decides the SLO target, the alert routing, the retention and the sampling policy, so a team cannot buy gold-plated monitoring for a hobby tool.

**Routing.** Page the team that can *act*. A burn alert on `orders-api` caused by `inventory` still pages `team-orders` first, with the dependency visible in the message and the service map; `team-inventory` is paged only on its own SLO. Routing by team handle in the message and by the `team` tag keeps the mapping data, not folklore.

**A standard service dashboard.** Generate one dashboard per service from a module, so every on-call engineer sees the same layout. Order the rows by the questions asked in an incident:

| Row | Content | Why |
| --- | --- | --- |
| 1. Objective | SLO status, remaining budget, active burn monitors | Is the promise at risk? |
| 2. Traffic and errors | Request rate, error ratio, deployment markers | What changed and when? |
| 3. Latency | p50, p95, p99 per resource | Which route is slow? |
| 4. Dependencies | Latency and errors on outgoing calls | Is it ours or downstream? |
| 5. Saturation | Container CPU, memory against limit, restarts | Is a resource the cause? |
| 6. Telemetry health | Agent heartbeat, ingestion lag, log volume | Can we trust the screens above? |

Template variables for `env` and `service` let one definition serve every service; teams add rows for their own domain below the standard ones.

**Review cadence.** Monthly: monitors that fired and led to no action (retire or tune), monitors that never fired (prove or delete), dashboards with no views. After every incident: which alert fired first, which was late, what was missing.

## Cost and retention

Telemetry cost is a product of volume, retention and cardinality. **[vendor-specific]** Datadog's billable units vary by product and plan (host or container counts, indexed log events, ingested log volume, custom metric series, ingested and indexed spans, retention add-ons). **[version-specific]** Read your current contract; the model below uses placeholders.

```python
# cost_estimate.py — a rough monthly model; every price below is a PLACEHOLDER, not a Datadog price.
# Inputs: measure these from your own usage views, then replace the guesses.
hosts                    = 12
log_events_per_day       = 40_000_000
log_indexed_fraction     = 0.15          # after exclusion filters
custom_metric_series     = 18_000
ingested_spans_per_day   = 90_000_000
span_indexed_fraction    = 0.02

# Placeholder unit prices (currency units); replace with your contract values.
P_HOST_MONTH             = 20.0
P_LOG_INDEXED_PER_MILLION= 2.0
P_LOG_INGEST_PER_MILLION = 0.1
P_METRIC_SERIES_MONTH    = 0.005
P_SPAN_INGEST_PER_MILLION= 0.2
P_SPAN_INDEX_PER_MILLION = 1.5

days = 30
lines = {
    "hosts":                hosts * P_HOST_MONTH,
    "log ingest":           log_events_per_day * days / 1e6 * P_LOG_INGEST_PER_MILLION,
    "log index":            log_events_per_day * days * log_indexed_fraction / 1e6 * P_LOG_INDEXED_PER_MILLION,
    "custom metrics":       custom_metric_series * P_METRIC_SERIES_MONTH,
    "span ingest":          ingested_spans_per_day * days / 1e6 * P_SPAN_INGEST_PER_MILLION,
    "span index":           ingested_spans_per_day * days * span_indexed_fraction / 1e6 * P_SPAN_INDEX_PER_MILLION,
}
total = sum(lines.values())
for name, value in sorted(lines.items(), key=lambda kv: -kv[1]):
    print(f"{name:16s} {value:12,.2f}  {value/total:6.1%}")
print(f"{'TOTAL':16s} {total:12,.2f}")
```

The point is not the numbers but the **shape**: which line dominates, and what moves it. With the placeholder inputs above, span ingestion and indexed logs dominate; with your own volumes it may be unbounded metric tags. Often a single exclusion filter, sampling rule or tag allow-list moves cost more than any hardware change.

**Controls to put in code.**

| Cost driver | Control | Example |
| --- | --- | --- |
| Indexed logs | Exclusion filters; index per tier; archive the rest | Index only `status:(error OR warn)` for tier 2 |
| Log volume at source | Log level policy; remove health-check logging | Info logs sampled in the application |
| Custom metric series | Tag allow-lists per metric **[vendor-specific]**; library wrapper that rejects unbounded tags | Keep `status` and `route`; drop `customer_id` |
| Spans | Sampling rules per service; retention filters keep errors and slow traces | Keep all errors, 5% of normal |
| Retention | Short for noisy data; longer, narrow, deliberate for audit data | 15 days indexed; archive for 13 months |

**Make cost visible to owners.** **[vendor-specific]** Datadog publishes estimated-usage metrics. **[version-specific]** Names and availability change; list them in the Metrics Summary rather than copying names from a book. Create a dashboard and a monitor per team on its usage trend, so that a doubling raises a ticket within days, not at invoice time.

**What you cannot answer after retention.** For each tier, write the questions that will be unanswerable: "what did an ordinary request look like 45 days ago?" or "which user saw the error?" If compliance or security needs those answers, arrange longer retention or archives on purpose and name the owner.

## Incident workflows

Monitoring matters at the moment an incident starts. Treat the workflow as a designed system with roles and artefacts.

| Stage | What should be true | Datadog's role **[vendor-specific]** |
| --- | --- | --- |
| Detect | A burn alert pages the owning on-call | Monitors, notification routing |
| Declare | Someone owns the decision; severity set from user impact | Incident record (a product feature; a document works too) |
| Assign roles | Incident commander, investigator, communicator | Fields in the incident record or a pinned note |
| Investigate | Correlation routine, with timestamps | Dashboards, traces, logs, deployment markers |
| Mitigate | Roll back, disable a feature or scale | Verified by the SLI recovering |
| Communicate | A regular update with the same wording rules | Link to the dashboard that defines "recovered" |
| Review | Timeline, contributing factors, follow-ups with owners | Graph and event links as evidence |

**Severity from impact, not feelings.** An example scale (illustrative): *Severity 1*, the critical journey is failing for most users; *Severity 2*, a significant degradation or a partial failure for some users; *Severity 3*, minor impact with a workaround. Tie each severity to who is paged and how often updates go out.

**Evidence discipline.** Write the timeline as you go, always with times and links. Capture the graph that shows the start, the deployment marker, the trace and log that gave the cause, and the graph that shows recovery. This is what turns a review from storytelling into engineering.

**Two drills to run before you need them.**

1. *The regression drill.* Plant a regression in one route (`INVENTORY_DELAY_SECONDS=1.5`). The owning on-call identifies it from the dashboard, follows traces to the slow span, correlates the version, reverts and confirms recovery. Measure time to detect, time to identify and time to recover.
2. *The blind-agent drill.* Stop the Agent, or revoke its key in a test organisation. The user-impact monitors may stay quiet, since there is no data to evaluate, while the missing-data monitor fires. Record exactly which failures each monitor can and cannot see.

## Verifiable outcomes

A claim without evidence is a guess. For each promise your monitoring makes, define the test, produce the evidence and keep it.

| Claim | Test | Evidence to keep |
| --- | --- | --- |
| "A total outage pages within 5 minutes" | Set `INVENTORY_FAIL=true` in staging; time from first failure to notification | Timestamped alert notification, graph |
| "A heartbeat loss is detected" | Stop the Agent | No-data alert with timestamp |
| "Every production monitor has an owner, a runbook and a no-data decision" | Run the lint script against a monitor export | Script output in CI |
| "SLO reflects reality" | Compare SLO movement with a known incident | Screenshot pair, note |
| "Logs never contain credentials" | Send a canary secret; search the index | Search result showing masked or absent |
| "Terraform matches production" | Scheduled drift plan | Plan output with exit code 0 |
| "A new service can be onboarded by a stranger" | A second team uses the package alone | Merged pull request, time taken |

A policy script keeps the second claim honest. It reads a monitor export, which you can create with the read-only API call from Beginner, and fails when a monitor breaks the rules.

```python
#!/usr/bin/env python3
# policy/lint_monitors.py — usage: lint_monitors.py monitors.json
import json
import re
import sys

REQUIRED_TAG_KEYS = {"service", "env", "team"}
RUNBOOK = re.compile(r"https?://\S+")


def tag_keys(monitor):
    return {t.split(":", 1)[0] for t in monitor.get("tags", []) if ":" in t}


def problems(monitor):
    out = []
    missing = REQUIRED_TAG_KEYS - tag_keys(monitor)
    if missing:
        out.append(f"missing tag keys: {sorted(missing)}")
    message = monitor.get("message", "")
    if not RUNBOOK.search(message):
        out.append("message has no runbook or dashboard link")
    if "@" not in message:
        out.append("message notifies nobody")
    options = monitor.get("options", {})
    no_data_decided = "notify_no_data" in options or "on_missing_data" in options
    if monitor.get("type") in {"query alert", "metric alert"} and not no_data_decided:
        out.append("no explicit no-data decision")
    return out


def main(path):
    with open(path) as handle:
        monitors = json.load(handle)
    failed = 0
    for monitor in monitors:
        issues = problems(monitor)
        if issues:
            failed += 1
            print(f"FAIL  {monitor.get('name', monitor.get('id'))}")
            for issue in issues:
                print(f"      - {issue}")
    print(f"{len(monitors) - failed}/{len(monitors)} monitors pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```

```text
# Example run against a two-monitor export, one of which is compliant (exit status 1)
FAIL  CPU high on web
      - missing tag keys: ['env', 'service', 'team']
      - message has no runbook or dashboard link
      - message notifies nobody
      - no explicit no-data decision
1/2 monitors pass
```

**[version-specific]** The export's field names (`options.notify_no_data`, `options.on_missing_data`, `type` values) follow the Datadog API at the time of writing; validate the script against a real export from your account before adopting it as a gate.

**A drill record** makes outcomes auditable. Keep one per drill:

```text
Drill:         total outage on orders-api (staging)           Date: 2026-11-15
Hypothesis:    fast-burn monitor notifies on-call within 5 minutes
Injection:     INVENTORY_FAIL=true at 10:02:10
Observed:      first failed request 10:02:11; alert notification 10:03:20; acknowledged 10:04:05
Result:        PASS (69 s to notify)
Surprises:     message lacked dashboard link; fixed in change #482
Evidence:      screenshots in drill folder; monitor event history exported
Reverted:      INVENTORY_FAIL=false at 10:15:00; monitor recovered 10:19:30
```

## When monitoring as code goes wrong

| Failure | Why it happens | Prevention |
| --- | --- | --- |
| Apply silently deletes a hand-made monitor | The resource was imported incorrectly, or an address changed | Review plans for destroys; protect tier-1 assets |
| Plan is slow or rate-limited | Hundreds of resources refreshed on every run | Split state per environment or domain; scope refresh |
| Everyone edits in the interface | Code path is slower than the interface during incidents | A fast review lane and a break-glass reconciliation rule |
| Thresholds copied everywhere | A module with no inputs for traffic differences | Variables with defaults per tier; review overrides |
| SLO measures the wrong thing | The SLI was chosen for convenience | Compare SLO movement with real incidents each quarter |
| Lint gate becomes a blocker | Rules added without a transition period | Warn first, then enforce, with an owner for the rules |
| Keys with excess scope in CI | One key used for plan and apply | Separate, scoped keys and protected branches |

## Decision on the telemetry path

Compare three routes and record the decision.

| Route | Strengths | Weaknesses |
| --- | --- | --- |
| Vendor tracing library to the Agent | Most complete vendor features; simplest | Vendor coupling in application code |
| OpenTelemetry SDK to the Agent's OTLP intake **[vendor-specific]** | Standard instrumentation; Agent features retained | Some vendor features need extra configuration |
| OpenTelemetry SDK to a Collector with a vendor exporter | Vendor-neutral path; central processing and routing | Extra component to run; sampling and trace-metric subtleties **[version-specific]** |

Record: which route, who owns sampling configuration, how logs are indexed versus archived, who owns monitors, and what you would change to move vendor. Keep standard instrumentation so the vendor can change.

## Professional trade-offs

| Choice | Benefit | Cost |
| --- | --- | --- |
| Everything as code | Review, history, reproducibility | Slower urgent changes; skills needed |
| Strict lint gate | Consistent quality | Friction for teams; false positives |
| Tight SLO | Strong user promise | Burns budget fast; slows delivery |
| Aggressive log exclusion | Lower cost | Fewer facts during an incident |
| Page on burn only | Fewer pages | Needs trustworthy SLIs; slow for mild failures |
| Central dashboards | Consistency | Less fit for a team's own domain |

## Decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Alert in proportion to risk | Burn-rate monitors on an SLO | Raw thresholds with no link to a target |
| Link logs and traces | Trace ids in JSON logs and a remapper | Hoping correlation works |
| Control cost | Exclusions, tag allow-lists, retention, an owner | Collecting everything by default |
| Prove a monitor works | Inducing the condition and keeping the evidence | Assuming a saved query is correct |
| Detect a blind Agent | A missing-data monitor | Only user-impact monitors |
| Keep keys safe | Narrow scopes, a secret manager, separate plan and apply keys | An application key inside the Agent container |
| Change alerts safely | A pull request and a plan | Editing in the interface without reconciling |

## Knowledge consolidation

- An SLO is an SLI plus a target and a window; the error budget is what the target permits.
- Burn rate converts budget into urgency: 14.4 for one hour uses 2% of a 30-day budget. Multi-window alerts split pages from tickets.
- Detection time is arithmetic, not hope: seconds for a hard outage, tens of minutes for a mild one.
- Monitors, SLOs, dashboards and pipelines belong in reviewed code with drift detection and a break-glass rule.
- Every asset has an owner, a tier and a review cadence; routing is data.
- Cost has a shape; find the dominant line and attach it to an owner.
- Incident workflow is a designed system, tested by drills; evidence is captured as you go.
- Verifiable outcomes: every claim has a test, a result and a retained record.

## Exercises

**Exercise 1 — Define an SLI.** For `orders-api`, write the SLI in one sentence, list what you exclude and why, and choose a window. Create the metric-based SLO and prove its query returns data.

**Exercise 2 — Burn arithmetic.** For a 99.5% SLO over 30 days, compute the error budget in minutes, then the burn rate that exhausts it in one day, and the time to trigger a 14.4 burn alert at 100% and at 3% bad events. Show your working.

**Exercise 3 — Fast and slow burn.** Implement fast, medium and slow burn monitors in code. For failure rates of 100%, 5% and 1%, predict which fire and when, drive at least the 100% case live, and compare.

**Exercise 4 — Monitoring as code.** Put an SLO, two monitors and a dashboard under Terraform. Run plan in CI, merge, then edit one monitor in the interface and show that the drift job detects it.

**Exercise 5 — Onboard a second service.** Add `inventory` through the `services` map alone. Count the files touched and the minutes taken; list anything that required knowledge not in the package.

**Exercise 6 — Policy gate.** Export monitors, run the lint script, and fix every failure. Add a rule of your own (for example, tier-1 monitors must set a priority) and show it catching a violation.

**Exercise 7 — Cost model.** Replace the placeholder inputs with your measured volumes and your contract prices. Identify the dominant line, apply one control and record the predicted and actual change.

**Exercise 8 — Two drills.** Run the regression drill and the blind-agent drill, with drill records. For each, state which monitor fired first and which signals were missing.

**Solution notes.**

*Exercise 1.* A strong SLI says "the proportion of non-5xx responses to non-health-check requests on customer routes". If the query preview returns no data, the metric or tag names are wrong for your integration; fix those before anything else.

*Exercise 2.* Budget: \(0.005 \times 43{,}200 = 216\) minutes. Exhausting it in one day means 30 times the sustainable rate, a burn rate of 30. A 14.4 alert at 100% bad events (burn rate 200) needs about \(14.4/200 = 7.2\%\) of the hour, roughly 4.3 minutes; at 3% bad (burn rate 6) a 14.4 burn is never reached, so a fast-burn alert stays silent and the medium or slow alert is the one that catches it. Seeing that gap is the point.

*Exercise 3.* With a 99.9% objective, 100% failures have burn rate 1,000 and trip the fast burn in about a minute; 5% has burn rate 50 and trips the fast burn after roughly 17 minutes of sustained failure (the medium burn also qualifies); 1% has burn rate 10, never reaches 14.4, and trips the medium burn only after about \(6/10\) of its six-hour window, roughly 3.6 hours. Hours-long runs are impractical in a live lab, so drive the 100% case live and verify the others by calculation or in a test organisation with shortened windows. Report measured times against these predictions.

*Exercise 4.* The drift job should return exit code 2 and show the changed attribute. A good answer states whether the interface edit is folded into code or reverted.

*Exercise 5.* A good package means one file changed and little extra knowledge. List every gap (a missing runbook template, an unclear tier) as a fix to the package, not as a note to the next engineer.

*Exercise 6.* The lint script should fail monitors lacking owner tags, runbook links or a no-data decision. Strictness should be introduced as warnings first so teams can fix legacy assets.

*Exercise 7.* Look for a dominant line, a predicted saving before the change, and a measured saving after; explain any difference rather than hiding it.

*Exercise 8.* The regression drill should show the latency monitors or burn alert first, with the trace pointing to the slow span; the blind-agent drill should show only the missing-data monitor, and the record should explicitly name that the user-impact monitors could not see the failure.

## Mentoring prompts

A team asks to page on every error log; how do you respond with an SLO argument? Your burn alert fired at 03:00 and nobody could identify the cause; what missing evidence do you add? A manager wants to cut observability spend by 40%; which three levers do you pull first, and what does each cost in incident capability? Show how you would prove, to someone who does not trust you, that your paging monitors work.

---
