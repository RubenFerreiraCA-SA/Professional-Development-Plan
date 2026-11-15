# T-DEV-07-I — Intermediate Practice

*Chapter: [T-DEV-07 — Datadog Monitoring](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-07-i"></a>
#### T-DEV-07-I — Intermediate Practice

## Why this matters

At Beginner level you proved the data path works: an Agent, a service, a few traces and log lines. Real investigations ask more. A customer reports failed orders, and you must decide in minutes whether the cause is the deployment that went out an hour ago, a slow dependency, a saturated container or a collector that quietly stopped. To answer that you need signals that *agree about what they describe*, logs that can be followed to traces, a picture of who calls whom, and monitors that fire for the right reasons and stay quiet otherwise.

This section covers the practices that make that possible: unified service tagging applied properly, APM concepts you can read, log pipelines, service maps, monitor design and a repeatable correlation routine. It closes with a troubleshooting ladder for the cases where data does not arrive. It assumes the Beginner section: the Agent, `DD_*` variables, the three signals, tags and the idea of a monitor. Markers follow the chapter convention: **[vendor-specific]** for Datadog features, **[version-specific]** for details to re-check against current documentation, and *illustrative* for example output.

## Running example

The Beginner stack grows by one service so that there is a dependency to map and a place for latency to hide: `orders-api` calls `inventory`.

```text
client -> orders-api (port 8000) -> inventory (port 8001)
                |                        |
                +---- traces, logs, metrics ----> datadog-agent -> Datadog
```

```python
# inventory.py — a dependency whose behaviour we can degrade on purpose
import os, time, logging
from fastapi import FastAPI, HTTPException

log = logging.getLogger("inventory")
app = FastAPI()
DELAY = float(os.getenv("INVENTORY_DELAY_SECONDS", "0"))   # set to 1.5 to simulate a slow dependency
FAIL = os.getenv("INVENTORY_FAIL", "false") == "true"      # set to true to simulate failures


@app.get("/stock/{sku}")
def stock(sku: str):
    time.sleep(DELAY)
    if FAIL:
        log.error("stock lookup failed for sku=%s", sku)
        raise HTTPException(status_code=503, detail="stock backend unavailable")
    return {"sku": sku, "available": 12}
```

```python
# orders-api: a route that depends on inventory (add to the Beginner app.py)
import os
import requests

INVENTORY = os.getenv("INVENTORY_URL", "http://inventory:8001")


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    log.info("loading order")
    r = requests.get(f"{INVENTORY}/stock/sku-{order_id % 5}", timeout=3)
    if r.status_code >= 500:
        log.error("inventory call failed with status %s", r.status_code)
        raise HTTPException(status_code=502, detail="dependency failed")
    return {"order_id": order_id, "stock": r.json()}
```

Both services use the same image, with a different `command` for `inventory` and its own `DD_SERVICE`. Note that the *route* `/orders/{order_id}` is a template. Trace resources and metric tags should carry the template, not the raw URL `/orders/42`, otherwise every order identifier becomes a distinct value. This is the same cardinality rule from the Beginner section, applied to traces.

## First principles: unified service tagging, applied

Unified service tagging gives every signal the same three coordinates, `service`, `env` and `version`. It matters in practice because each Datadog feature joins on them: the service page filters traces by `service` and `env`, deployment comparison groups by `version`, and logs link to traces when their `service` and `env` agree with the trace's.

Tags reach data through several paths. A good setup uses **one authoritative source per signal** and avoids two paths writing different values.

| Signal | Primary source of the three tags | Common mistake |
| --- | --- | --- |
| Traces | `DD_SERVICE`, `DD_ENV`, `DD_VERSION` read by the tracing library | Library defaults the service to the process name |
| Logs | Same variables, via trace-correlation fields in each log line, or container labels | Logs collected by the Agent carry the container's tags but a different `service` |
| Metrics (custom) | Variables on the sending process and tags in the metric call | Metric tagged `environment:` while everything else uses `env:` |
| Container and host metrics | Tags the Agent derives from container labels or environment | `env` set on the application container only |

**[vendor-specific]** In Docker, the Agent can read standard labels from a container. In Kubernetes the equivalent is a set of pod labels. Both are alternatives to setting variables on the application; use whichever your platform standard prefers, but never both with different values.

```yaml
# Docker labels the Agent reads to tag a container's metrics and logs (alternative to env vars)
services:
  api:
    labels:
      com.datadoghq.tags.service: orders-api
      com.datadoghq.tags.env: staging
      com.datadoghq.tags.version: "1.1.0"
```

**[version-specific]** Label and variable names, and whether the Agent applies them to logs, depend on Agent version and platform. Verify with a query rather than assuming.

**Verify tags with evidence, not assumption.** Pick a trace, a log line and a container metric for the same service and compare the three tags.

| Check | Where | Expected |
| --- | --- | --- |
| Trace tags | Open a trace, inspect the root span's tags | `service`, `env`, `version` present and correct |
| Log tags | Open a log line, inspect attributes | The same three values |
| Metric tags | Metrics Explorer, filter `service:orders-api`, group by `version` | One line per deployed version |

If a signal is missing a tag, you have found the next fix. A "service" that appears only in traces, or an `env` value that exists in one signal but not another, is the usual reason that correlation silently fails.

**Tag drift.** Between releases, someone renames `env:prod` to `env:production`, or a base image changes the default service name. Monitors that filter on the old value stop matching and go quiet. Defences: set the values in one deployment template, add a CI check that fails on an unknown `env` or `service`, and keep a monitor that fires when an expected service has no data.

## Logs: structured, correlated, governed

### Structure and trace correlation

A log line is searchable by field only if it is structured. Emit JSON, and include the identifiers that link it to a trace.

```python
# logging setup with trace correlation fields (ddtrace injects dd.* attributes into log records)
import logging, sys

FORMAT = (
    '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
    '"message":"%(message)s",'
    '"dd.trace_id":"%(dd.trace_id)s","dd.span_id":"%(dd.span_id)s",'
    '"dd.service":"%(dd.service)s","dd.env":"%(dd.env)s","dd.version":"%(dd.version)s"}'
)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(FORMAT))
logging.getLogger().handlers = [handler]
logging.getLogger().setLevel(logging.INFO)
```

**[version-specific]** The injected attribute names (`dd.trace_id` and similar) and the need for `DD_LOGS_INJECTION=true` follow the Datadog tracing libraries at the time of writing; other languages differ. A free-text `message` containing quotes will break this naive JSON, so use a proper JSON formatter library in real code, with the same field names.

```json
{"time":"2026-11-15 09:14:03,112","level":"ERROR","logger":"orders-api","message":"inventory call failed with status 503","dd.trace_id":"7204419951012330001","dd.span_id":"1841209911226203","dd.service":"orders-api","dd.env":"staging","dd.version":"1.1.0"}
```

*Illustrative sample line.* Each field has a job: `level` becomes the log's status, `dd.service`/`dd.env`/`dd.version` carry the unified tags, and the two identifiers join the line to its trace.

### Pipelines

**[vendor-specific]** Datadog processes each log through a **pipeline**: an ordered list of processors that parse the raw line and promote fields to the attributes the platform understands. Most useful processors are:

| Processor | Job | Example |
| --- | --- | --- |
| Grok parser | Extracts fields from unstructured text | Pull `status` and `duration_ms` from an NGINX line |
| Date remapper | Sets the event time from a field | Use `time`, not the arrival time |
| Status remapper | Sets severity from a field | Map `level` to the log status |
| Service remapper | Sets the service from a field | Map `dd.service` |
| Trace ID remapper | Links a log to its trace | Map `dd.trace_id` |
| Attribute remapper | Renames fields to standard names | `http.status` to `http.status_code` |

JSON logs that use the standard field names are largely processed automatically; pipelines are for non-standard names and unstructured formats. Order matters, since later processors see earlier results. Before changing a pipeline, record one sample log and what it looks like before and after.

An unstructured example and its parser, to show the pattern:

```text
# raw line
2026-11-15T09:14:03Z WARN checkout order=4821 latency_ms=1840 upstream=inventory

# grok rule (Datadog grok syntax) producing attributes
checkout_rule %{date("yyyy-MM-dd'T'HH:mm:ssZZ"):timestamp}\s+%{word:level}\s+%{word:module}\s+order=%{integer:order_id}\s+latency_ms=%{integer:duration_ms}\s+upstream=%{word:upstream}
```

**[version-specific]** Grok helper names and date patterns are Datadog-specific; use the pipeline's built-in sample tester to confirm a rule matches before saving.

### Ingestion, indexing and exclusion

Logs have a cost structure with two separate decisions. **Ingestion** means Datadog receives and processes the event. **Indexing** means the event is stored in a searchable index for a retention period, which costs more. **[vendor-specific]** Datadog lets you ingest everything, then choose what to index with *exclusion filters*, and optionally archive all of it to your own object storage at lower cost.

| Policy | Example | Trade-off |
| --- | --- | --- |
| Exclude noisy, low-value lines | Health-check requests; debug level in production | Cannot search them later, though they can still feed metrics |
| Index errors and warnings, sample info | Keep all `error`, 10% of `info` | Some individual info events are lost |
| Archive everything | Full logs in object storage | Cheaper retention, slower to reach |
| Scrub sensitive fields | Remove `password`, `token`, `authorization` | Must be tested; a missed field is a leak |

Do the scrubbing check by sending a line with a fake secret and confirming it is masked or absent in the interface. Record what was excluded and why, so no one later wonders why the lines are missing.

## APM: reading traces and service-level metrics

**[vendor-specific]** APM turns spans into several views. Know the vocabulary:

| Term | Meaning | Example for `orders-api` |
| --- | --- | --- |
| Service | A unit that does work, named by `service` | `orders-api`, `inventory` |
| Operation (span name) | The kind of work a span records | `fastapi.request`, `requests.request` |
| Resource | The specific thing worked on | `GET /orders/{order_id}` |
| Span tags | Key-value details on one span | `http.status_code`, `error` |
| Trace | All spans for one request | Request through both services |

**[version-specific]** Operation names depend on the library and integration (for example the web framework integration's name). Find yours in the interface before writing a query that uses it.

**Trace metrics versus stored traces.** Datadog computes request counts, error counts and latency distributions per service and resource, and these *trace metrics* are designed to reflect all traffic. The individual traces you can open, however, are a sampled subset. Hence the rule from Beginner, now with a reason: use metrics (or trace metrics) for *rates*, and traces for *causes*. If you want to know "how many errors per minute?", read the metric. If you want to know "why did this one fail?", open a trace. Missing a particular trace does not mean it did not happen. **[version-specific]** Which data is computed before sampling and how sampling is configured differ by library version and by whether you route through a Collector; confirm in the ingestion settings.

**Reading a trace.** Open a slow `GET /orders/{order_id}` trace and read it top to bottom:

```text
Trace (illustrative): 1.82 s total

orders-api   fastapi.request  GET /orders/{order_id}            |==========================| 1820 ms
orders-api     requests.request  GET inventory                   |  ======================  | 1770 ms
inventory        fastapi.request  GET /stock/{sku}                 |  ====================    | 1600 ms
```

Reading rules: find the widest span *that has no wider child explaining it*; here the time is inside `inventory`, not in `orders-api`. Look at span tags for the error flag and HTTP status. Compare the span duration to a healthy trace of the same resource: a trace is only slow relative to what is normal.

**Latency percentiles.** Chart p50, p95 and p99, not the mean. A mean of 120 ms can coexist with a p99 of 2 s. Percentiles taken per resource avoid mixing a fast route with a slow one; percentiles over *averaged* values do not add up, so prefer percentile aggregation provided by the platform, and be wary of averaging per-instance percentiles. **[vendor-specific]** Datadog offers distribution metrics for aggregated percentiles; their cost model differs from ordinary custom metrics, so check before using widely.

**Errors.** A span is marked as an error when the library records an exception or an error status. Not every HTTP 4xx is an error by default; whether a given status counts as an error is a library setting. Decide deliberately whether a 404 on an order lookup is an application error or normal, and check that traces reflect the decision, otherwise error-rate monitors will mislead.

## Service maps and dependencies

**[vendor-specific]** A service map draws services as nodes and calls as edges, derived from client and server spans. It shows who depends on whom, the request rate and error rate along each edge, and which node is unhealthy.

| Use | How |
| --- | --- |
| Blast radius | Before a change to `inventory`, see which services call it |
| Localise a fault | Red edge into `inventory` while upstream edges are fine points downstream |
| Spot surprises | A service that calls something nobody listed as a dependency |
| Find missing instrumentation | A node with calls going out but nothing recorded inside it |

Limitations to remember. A service map shows only what is instrumented: an uninstrumented queue or third party appears as a thin dashed edge or not at all. Asynchronous work through a message queue often breaks the trace unless context is propagated explicitly. Datadog can infer databases and external services from client spans, but how a dependency is named (and whether it merges) depends on library settings. **[version-specific]** Treat the map as a hypothesis generator and confirm with a trace.

## Monitors: design for action

A monitor is only as good as its query. Read this metric monitor query carefully:

```text
avg(last_10m):sum:trace.fastapi.request.errors{service:orders-api,env:production}.as_count()
 / sum:trace.fastapi.request.hits{service:orders-api,env:production}.as_count() > 0.02
```

It says: over the last ten minutes, errors divided by hits for one service in one environment is above 2%. Each part is a decision.

| Part | Decision | Consequence of a poor choice |
| --- | --- | --- |
| Aggregation and window | `avg(last_10m)` | Too short flaps on bursts; too long is slow to detect |
| Scope | `{service:..., env:...}` | Missing `env` mixes staging noise into production |
| Ratio, not count | errors / hits | A count alert fires on busy hours and misses quiet failures |
| `as_count()` | Counts, not rates | Rates divide differently and can mislead ratios |
| Threshold and recovery | `> 0.02`, optional recovery value | No recovery threshold causes flapping near the line |

**[version-specific]** The metric names (`trace.<operation>.hits` and `.errors`) come from the APM integration; confirm yours in the Metrics Summary.

**Monitor behaviours you must understand.**

- **Evaluation window and delay.** Monitors evaluate on a schedule; metrics arrive with a short lag. An *evaluation delay* setting avoids evaluating incomplete recent data. A longer window needs more data to cross a threshold and so reacts later.
- **Simple versus multi-alert.** Simple alert gives one notification for the whole query. Multi-alert splits by a tag such as `host` or `resource` and evaluates each group independently. Choose the grouping that matches the unit of action.
- **No data handling.** Decide for each monitor whether missing data should alert, stay silent or resolve. For a service that must always receive traffic, notify on no data. For a batch job that runs hourly, it should not.
- **Recovery and re-notification.** Decide whether a monitor re-notifies while still alerting, and who is told on recovery.
- **Message.** State the user impact, link the runbook and dashboard, name the owner, and include context variables such as the group and value. Messages use handles to route (a team handle or an on-call integration). **[vendor-specific]**

```text
{{#is_alert}}
orders-api error ratio is {{value}} (threshold {{threshold}}) in production.
Impact: customers may see failed order pages. Start: https://runbooks.example.com/orders-high-errors
Dashboard: https://app.example.com/dashboards/orders  (replace with your dashboard URL)
@team-orders-oncall
{{/is_alert}}
{{#is_no_data}}
No orders-api telemetry in the last 20 minutes. Check the service, the Agent and the key BEFORE assuming users are fine.
@team-orders-oncall
{{/is_no_data}}
```

**[version-specific]** Template variables and conditional blocks differ across monitor types; test a message through the notification preview before relying on it.

**A minimum set for a new service.** Start with exactly three, so that each has a distinct purpose:

| Monitor | Question | Type |
| --- | --- | --- |
| User impact | Are users getting errors or slow responses? | Error ratio and a p95 latency threshold |
| Missing telemetry | Can we still see the service? | No-data on request metric or heartbeat |
| Saturation | Is a resource about to run out? | Container memory against limit, restarts |

Prove each by inducing the condition and observing the transition (OK, then Alert, then OK; OK, then No Data, then OK). A monitor that has never been seen to fire is unproven.

**Noise and flapping.** Create a deliberately sensitive monitor (for example CPU above 5%), watch it flap, then fix it: a longer window, a recovery threshold, grouping, or a different query. Record before and after. Your goal is *fewer, more actionable* alerts.

## The correlation routine

When something is wrong, follow the same short routine every time. It keeps you out of random clicking.

1. **Scope.** Which service, environment and version? Is it all traffic, one route, one host?
2. **When.** Find the start time on a graph. Compare with the version marker: did a deploy precede it?
3. **Symptom to trace.** From the service page, open traces for the affected resource filtered to errors or high duration, in the window.
4. **Trace to cause.** Read the slowest or failing span. Is it in this service or a dependency?
5. **Trace to logs.** Open the logs for that trace; read the message and fields around the failing span.
6. **Cause to change.** Which change matches the timing (version, configuration, dependency state)?
7. **Verify the fix.** After the mitigation, the metric returns to baseline and the monitor recovers. Without this, you only believe it is fixed.

A worked example, illustrative. Set `INVENTORY_DELAY_SECONDS=1.5` on `inventory` and redeploy as version `1.1.1`. On the service page, p95 latency for `GET /orders/{order_id}` rises from about 60 ms to about 1.6 s at the deployment marker, while the error ratio stays flat. A slow trace shows the time inside the `inventory` span. The `inventory` logs show nothing unusual at warning level, because the delay is a plain sleep, so the logs *do not* explain it; the trace does. The change that fits is `1.1.1` on `inventory`. Setting the delay back and redeploying brings p95 back to baseline. Note two lessons: a latency problem need not leave any error log, and the version tag on the dependency is what pinpointed the change.

## Agent and ingestion troubleshooting

Work the ladder from the application to the platform, and stop at the first rung that fails.

| Rung | Question | Command or place | Typical finding |
| --- | --- | --- | --- |
| 1 | Does the process emit data at all? | App logs; tracer startup output | Library not enabled, wrong entrypoint |
| 2 | Does the app have the right configuration? | `docker compose exec api env \| grep '^DD_'` | Missing `DD_AGENT_HOST`, wrong `DD_ENV` |
| 3 | Can the app reach the Agent? | `docker compose exec api sh -c 'getent hosts datadog-agent'`; trace intake `/info` | Name wrong, port blocked, wrong network |
| 4 | Is the Agent healthy? | `agent status`; `agent health` | Component not running, port conflict |
| 5 | Is the Agent receiving? | `agent status`, APM and logs sections | Zero traces received; log source not found |
| 6 | Is the Agent forwarding? | Forwarder section; Agent log | Key invalid, wrong site, proxy or egress blocked |
| 7 | Is the platform showing it? | Interface at the correct site, time range, filters | Wrong time window; query filter excludes data |
| 8 | Was it filtered on purpose? | Exclusion filters, sampling, retention | Excluded log, sampled trace, expired data |

Diagnostic commands to know. **[version-specific]**

```bash
docker compose exec datadog-agent agent status          # overall: key, forwarder, APM, logs, DogStatsD
docker compose exec datadog-agent agent health          # which internal components are healthy
docker compose exec datadog-agent agent configcheck     # which integrations and log sources were loaded
docker compose exec datadog-agent agent diagnose        # built-in connectivity and configuration checks
docker compose exec datadog-agent agent flare           # bundle diagnostics for Datadog support; REVIEW it before sending (may contain hostnames and config)
```

To see more from the tracing library, enable its startup and debug output on the application:

```yaml
environment:
  DD_TRACE_DEBUG: "false"           # set to "true" only temporarily; output is verbose
  DD_TRACE_STARTUP_LOGS: "true"     # [version-specific] prints the effective tracer configuration at start
```

A trace that is sent but not stored may have been sampled out; a log that is collected but not searchable may have been excluded; metrics may exist but under an unexpected tag. Tools to separate these: query the raw metric by its name to prove the platform has any data; search logs with the filters cleared and a wide time window; look at the ingestion and exclusion settings.

**Common ingestion failures.**

| Symptom | Cause | Fix |
| --- | --- | --- |
| Agent status shows traces dropped | Sampling limit reached, or malformed spans | Inspect the APM section; adjust sampling deliberately |
| Logs missing for one container only | Container excluded or logs not configured | `configcheck`; labels that include or exclude logs |
| DogStatsD metrics absent | Wrong host or port; UDP not reachable across containers | Non-local traffic enabled; correct `DD_AGENT_HOST` |
| Duplicate hosts | Two Agents (one on host, one in a container) report the same machine | Run one Agent per host |
| Time misaligned | Host clock wrong | Fix time synchronisation |
| Intermittent gaps | Agent restarted or out of memory | Container restarts; Agent memory limits |

## What can go wrong: a short catalogue

| Failure | Why | Prevention |
| --- | --- | --- |
| Correlation silently broken | Trace id missing from log fields, or service names differ | Verify both directions on every service at onboarding |
| Alerts never fire | Query matches no data after a tag change | A no-data monitor; test by inducing the fault |
| Alerts fire constantly | Window too short, threshold too close to normal | Window and recovery tuning; review monthly |
| Large unexpected bill | Collect-all logs, unbounded tag values | Exclusions, tag allow-lists, an owner |
| Sensitive data in telemetry | Raw bodies and headers logged | Scrubbing rules, tested with a fake secret |
| Dashboards that nobody trusts | Many near-duplicates, unknown owners | One standard dashboard per service; owner tag |

## Knowledge consolidation

- Unified service tagging is a join key. Verify the three tags in a trace, a log line and a metric; drift breaks monitors silently.
- JSON logs with trace identifiers and a pipeline that maps them link logs and traces in both directions.
- Ingestion and indexing are separate decisions; exclusion filters and archives manage cost.
- Trace metrics are for rates; stored traces are for causes. Read a trace by finding the widest span without an explanatory child.
- Use percentiles, never the mean alone, and use route templates, never raw URLs.
- A service map is a hypothesis about dependencies; verify with traces.
- A monitor is a decision about window, scope, ratio, no-data and message. Prove it by inducing the condition.
- Follow the correlation routine: scope, when, trace, cause, logs, change, verify.
- Troubleshoot data arrival from the application towards the platform and stop at the first failing rung.

## Exercises

**Exercise 1 — Tag audit.** For `orders-api` and `inventory`, compare `service`, `env` and `version` in one trace, one log line and one container metric each. Produce a table of what you found. Then deliberately set `DD_ENV` differently on `inventory` and describe which features stop joining.

**Exercise 2 — Correlate in both directions.** Switch the application to the JSON log format. From a failing trace, find its log line; from the log line, jump to the trace. Then remove the trace identifier from the format, repeat, and record what breaks.

**Exercise 3 — Pipeline and scrub.** Add a log line with a fake `authorization=Bearer abc123` and a health-check line. Configure scrubbing and an exclusion for health checks. Show, with queries, that the secret is masked and the health lines are not indexed.

**Exercise 4 — Sampling honesty.** During a one-minute burst of known size, compare your request count, the trace-metric hit count and the number of individually stored traces. Explain each difference.

**Exercise 5 — Monitors that earn trust.** Build the three-monitor set. Induce each condition (inventory failures, an Agent stop, a container memory squeeze) and screenshot or export each state transition with timestamps.

**Exercise 6 — Noisy monitor.** Create a monitor on CPU above 5%. Record how often it changes state in an hour, then tune window, recovery or scope until it changes state only for real events. Record before and after.

**Exercise 7 — Planted regression.** Have a partner set `INVENTORY_DELAY_SECONDS` on `inventory` without telling you. Using only the dashboard, traces, and the correlation routine, find the cause, state the evidence and show recovery.

**Exercise 8 — Ladder drill.** Break the pipeline in each of three ways in turn: wrong `DD_SITE`, wrong `DD_AGENT_HOST`, log collection disabled. For each, name the rung where the ladder first fails and quote the evidence.

**Solution notes.**

*Exercise 1.* Expect the three tags to be present on traces and logs when both variables and log injection are configured; container metrics may carry `env` from the Agent's configuration rather than from the application. With a different `DD_ENV` on `inventory`, its traces move to another environment, the service map may split, and logs may still link to traces only if the log's `env` matches the trace's.

*Exercise 2.* With the trace identifier present, the log opens its trace and the trace lists its log lines. Removing the identifier breaks the log-to-trace jump and, typically, the trace-to-log view; metrics and traces still work. This shows that correlation is a property of the log format, not of Datadog.

*Exercise 3.* The secret should appear masked or removed in the indexed event; health-check lines should be absent from the index but may still be countable if you create a metric from logs before exclusion. If the secret survives, your rule's pattern did not match the field name or format.

*Exercise 4.* Your request count is the truth for what you sent; trace metrics should be close to it; stored traces will usually be fewer because of sampling. Differences smaller than a few percent can come from timing at the window edges. Report ranges from several runs.

*Exercise 5.* Look for: user-impact monitor going to Alert while the Agent is still up; the missing-data monitor going to No Data when the Agent is stopped while the user-impact monitor stays quiet; the saturation monitor responding to a memory limit that is too small. If a transition does not happen, check evaluation window and no-data settings before rewriting the query.

*Exercise 6.* A sensible fix lengthens the window or adds a recovery threshold rather than raising the threshold until the monitor can never fire. A defensible result is "fewer than a handful of state changes per day, each matching a real event".

*Exercise 7.* A strong write-up names the scope, the start time against a deployment marker, the slow span, the owning service, the logs that did or did not help, and the metric returning to baseline after the fix.

*Exercise 8.* A wrong site fails at rung 6 with an authentication or forwarding error; a wrong host fails at rung 3 or 5 with zero traces received; disabled log collection fails at rung 5 for logs while traces still work.

---
