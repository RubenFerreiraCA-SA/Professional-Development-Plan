# T-DEV-06-I — Intermediate Practice

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-i"></a>
#### T-DEV-06-I — Intermediate Practice

## Why this matters

At the Beginner level you learned what logs, metrics and traces are. At the Intermediate level you have to *produce* them: decide the fields in a log line, the labels on a metric, the attributes on a span, and the queries behind a dashboard and an alert. These choices are cheap to make on day one and very expensive to change after twenty services have copied them. They also decide whether, during an incident, you can answer "which route, which version, which dependency?" in two minutes or two hours.

This section assumes the Beginner vocabulary: counters, gauges, histograms, golden signals, structured logs. It uses the neutral `orders-api` service, written in Python for the code examples; the ideas carry to any language. Query examples use PromQL-style syntax because it is widely understood, and outputs marked *illustrative* show shape, not measured results. Nothing here depends on other course material.

## Structured logs in practice

### A minimum schema

Agree on a small set of fields every service emits. Without agreement each team invents its own names (`level`, `severity`, `lvl`) and cross-service queries become impossible.

| Field | Type | Notes |
| --- | --- | --- |
| `ts` | string, UTC ISO 8601 | Millisecond precision or better; never local time |
| `level` | enum | `debug`, `info`, `warn`, `error` |
| `service` | string | Same value as the telemetry resource attribute `service.name` |
| `version` | string | Build or release identifier; the field that links a symptom to a change |
| `env` | string | `production`, `staging` |
| `msg` | string | Short, stable sentence; no embedded variable values |
| `error.code` | string, optional | Stable code (`PAY_TIMEOUT`); the unit you count and alert on |
| `trace_id`, `span_id` | string, when a request is in flight | 32 and 16 hexadecimal characters |
| `duration_ms` | number, optional | Numbers as numbers, not text |

**Stable messages, variable fields.** Compare:

```text
msg="payment failed for order 98231 after 2003ms: gateway timeout"
```

```json
{"msg":"payment failed","order.id":"98231","duration_ms":2003,"error.code":"PAY_GATEWAY_TIMEOUT"}
```

The first produces a different string for every event, so "how many payment failures per hour?" requires pattern matching. The second can be grouped by `msg` or `error.code` directly. A good test is *can I count this event by grouping on one field?*

### A JSON log formatter with trace correlation

```python
import json, logging, sys, time
from opentelemetry import trace

class JsonFormatter(logging.Formatter):
    def format(self, record):
        ctx = trace.get_current_span().get_span_context()
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
                  + f".{int(record.msecs):03d}Z",
            "level": record.levelname.lower(),
            "service": "orders-api",
            "version": "1.8.0",
            "msg": record.getMessage(),
        }
        if ctx.is_valid:
            entry["trace_id"] = format(ctx.trace_id, "032x")
            entry["span_id"] = format(ctx.span_id, "016x")
        for key, value in getattr(record, "fields", {}).items():
            entry[key] = value
        if record.exc_info:
            entry["error.stack"] = self.formatException(record.exc_info)
        return json.dumps(entry, separators=(",", ":"))

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

log = logging.getLogger("orders")
log.warning("slow query", extra={"fields": {"db.operation": "SELECT", "duration_ms": 2240}})
```

Points worth noticing: the stack trace goes into *one field* of *one JSON line*, so a multi-line exception is not scattered across the log store as separate events; logs go to standard output and the platform collects them (the application does not manage files); and the trace id comes from the active span, so you do not pass it around by hand.

### Levels, volume and sampling of logs

- `error` should mean "a person may need to look". If 90% of your `error` lines are expected (a user typed a wrong password), the level is wrong for them.
- `debug` logging in production is a temporary switch, scoped to one service or one request, with an expiry. A permanent `debug` level can multiply log volume by ten.
- Logs cost by volume. A service at 500 requests per second that writes three 400-byte lines per request produces 500 × 3 × 400 = 600,000 bytes per second, about 52 GB per day. Decide what each line is *for*. A line nobody queries and no alert uses is cost without value.
- Do not log inside tight loops. One line per item in a batch of 100,000 items is 100,000 lines; log a summary (count, duration, failures).

### Diagnostic events versus audit events

Keep them in separate streams. Diagnostic events help debug incidents: short retention, engineer access, some loss acceptable, sampling allowed. Audit events record who changed what: long retention, restricted tamper-evident storage, loss is a defect, never sampled. An engineer reading diagnostic logs should not thereby be able to read, alter or delete the audit trail.

## Traces and spans in detail

### Anatomy of a span

A span is a record of one operation. The fields you need to know:

| Field | Meaning |
| --- | --- |
| Trace id | 16 bytes, shared by every span in the request; 32 hexadecimal characters |
| Span id | 8 bytes, unique for this span; 16 hexadecimal characters |
| Parent span id | Which span started this one; empty for the root |
| Name | Low-cardinality operation name: `GET /v1/orders/{id}`, `SELECT orders` |
| Kind | `server` (handles an incoming request), `client` (makes an outgoing call), `internal`, `producer`, `consumer` |
| Start time and duration | When and how long |
| Attributes | Key-value details: `http.response.status_code`, `db.system`, `order.found` |
| Events | Timestamped points inside the span, such as an exception |
| Status | `unset`, `ok` or `error`. By convention only mark `error` when the operation failed from the caller's standpoint |
| Links | References to related spans in other traces (batch jobs consuming many messages) |

**Span names must be low cardinality.** `GET /v1/orders/98231` as a name produces a different operation for every order, which makes grouping impossible. Use the route template and put the id in an attribute if you must.

### Context propagation

For a trace to cross a network boundary, the caller sends the trace context in a header and the callee reads it. The W3C Trace Context standard defines the `traceparent` header.

```text
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             │  └───────── trace id (32 hex) ─────┘ └ parent span id (16 hex) ┘ └ flags
             └ version
```

The last field carries flags; the lowest bit is `1` when the caller sampled the trace. The callee creates its own spans as children of the span id in the header. In code, instrumentation libraries inject and extract this automatically for common HTTP clients and servers; you write it by hand when you cross a boundary they do not cover, such as a message queue.

```python
from opentelemetry import trace
from opentelemetry.propagate import inject, extract
from opentelemetry.trace import SpanKind, Status, StatusCode

tracer = trace.get_tracer("orders-api")

def publish_order_event(order_id: str, queue):
    with tracer.start_as_current_span("orders.created publish", kind=SpanKind.PRODUCER):
        headers = {}
        inject(headers)                      # writes traceparent into the dict
        queue.send({"order_id": order_id}, headers=headers)

def handle_message(message):
    ctx = extract(message.headers)           # reads traceparent
    with tracer.start_as_current_span("orders.created process",
                                      context=ctx, kind=SpanKind.CONSUMER) as span:
        try:
            charge_customer(message.body["order_id"])
        except TimeoutError as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, "payment timeout"))
            raise
```

When a trace "breaks" mid-way, check in this order: did the caller inject the header; did a proxy or gateway strip it; did the callee extract it before starting its span; did a thread or async boundary lose the active context?

### Why traces complement metrics

| Symptom | CPU graph alone | Trace with dependency spans |
| --- | --- | --- |
| Slow database query | May look idle or busy depending on waits | Long client span to the database |
| Slow handler (internal sleep or lock) | CPU low | Long internal span in the service |
| Slow downstream call | CPU low | Long client span to that dependency |
| Retry storm | CPU slightly higher | Several repeated client spans under one parent |

"CPU is high after the deploy" is an incomplete diagnosis; it does not say which operation, which dependency or which version. Use metrics for rates and alert conditions, and traces for causality on specific requests.

## OpenTelemetry concepts

**OpenTelemetry** (OTel) is a vendor-neutral set of APIs, SDKs, conventions and a wire protocol for emitting telemetry. The pieces you need to name correctly:

| Piece | What it is | Why it matters |
| --- | --- | --- |
| API | Interfaces your code calls (`tracer.start_as_current_span`, `counter.add`) | Application and library code depend only on this, so libraries can be instrumented without choosing a backend |
| SDK | The implementation: samplers, processors, exporters | Chosen at application start-up by whoever runs the service |
| Resource | Attributes describing *the thing producing telemetry*: `service.name`, `service.version`, `deployment.environment.name`, host, pod | Attached to every signal; the glue that lets you filter by service and version |
| Instrumentation scope | Name and version of the library that produced the data | Lets you see which library created a span |
| Signals | Traces, metrics, logs | Three data types sharing one resource model |
| OTLP | The OpenTelemetry protocol (over gRPC or HTTP) | The common wire format between SDK, Collector and backend |
| Collector | A separate process that receives, processes and exports telemetry | Decouples the application from backends; place for batching, filtering, redaction, sampling |
| Semantic conventions | Standard attribute names (`http.request.method`, `db.system`) | Dashboards and queries work across services and languages |
| Auto-instrumentation | Agents or libraries that instrument common frameworks without code changes | Fast baseline coverage; supplement with manual spans for business operations |

**Automatic versus manual instrumentation.** Start with automatic: HTTP server and client, database drivers and message clients give you a trace skeleton for free. Then add manual spans for operations that matter to the business (`reserve_stock`, `price_basket`) and attributes that help diagnosis (`order.items_count`). Resist the urge to wrap every function in a span: a trace with 600 spans per request is expensive and unreadable.

```python
from opentelemetry import metrics, trace

tracer = trace.get_tracer("orders-api")
meter = metrics.get_meter("orders-api")
orders_total = meter.create_counter("orders_requests_total", description="Requests by route and outcome")
payment_seconds = meter.create_histogram("payment_call_duration_seconds", unit="s")

def get_order(order_id):
    with tracer.start_as_current_span("get_order") as span:
        orders_total.add(1, {"route": "/v1/orders/{id}"})
        order = repo.find(order_id)
        span.set_attribute("order.found", order is not None)   # bounded value; no PII
        return order
```

### A vendor-neutral pipeline

```yaml
# Collector configuration (simplified)
receivers:
  otlp:
    protocols:
      grpc: {}
      http: {}
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 400
  batch: {}
exporters:
  otlphttp/traces:
    endpoint: http://trace-backend:4318
  prometheus:
    endpoint: 0.0.0.0:8889
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlphttp/traces]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
```

The `memory_limiter` processor protects the Collector itself; it should come first in the chain so it can refuse data before memory runs out.

**Telemetry must not take the service down.** Test it: stop the Collector and confirm `orders-api` keeps serving. Exporters should buffer a bounded amount and then drop, never block a request. Run this test once on purpose, in staging, and record the result; a telemetry outage that becomes a service outage is a classic own goal.

**Correlation test.** Prove one request can be followed end to end: take an `X-Request-Id` or trace id from the HTTP response, find the log line with that id, open the trace with that id. If any link fails, fix it before you need it.

## Metric types and labels, in depth

### Choosing the type

| Type | Use for | Do not use for |
| --- | --- | --- |
| Counter | Events that accumulate: requests, errors, bytes sent, jobs completed | Values that can decrease |
| Up-down counter | Sums that rise and fall by increments: items in a queue, active sessions | Anything you can instead sample as a gauge |
| Gauge | A value you read at a moment: temperature, current queue length, pool size | Counting events (a spike between samples is lost) |
| Histogram | Distributions: latency, response size, queue wait | Values with very few distinct outcomes |
| Summary (older style) | Client-side precomputed quantiles | Anything you need to aggregate across instances: precomputed quantiles cannot be merged |

**Naming conventions help.** Use base units (`seconds`, `bytes`) and suffix counters with `_total`. `http_request_duration_seconds` is unambiguous; `latency` is not.

### Histograms and bucket design

A histogram's accuracy depends on its bucket boundaries. If your latency objective is 300 ms, the boundary at 0.3 s must exist, otherwise you cannot count "requests faster than 300 ms" exactly. Choose boundaries around the thresholds you care about.

```text
Buckets (seconds): 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 2.5, 5, 10, +Inf
```

Percentiles from buckets are aggregable: sum the bucket rates across instances first, then compute the quantile.

```text
# p95 latency by route, aggregated over all instances (illustrative PromQL)
histogram_quantile(
  0.95,
  sum by (le, route) (rate(http_request_duration_seconds_bucket{service="orders-api"}[5m]))
)
```

The inner `sum by (le, route)` must keep `le`; the quantile function needs the buckets. And never average per-instance p95 values: one busy instance and one idle instance contribute very different numbers of requests.

### Labels and the arithmetic of cardinality

Every distinct combination of label values is a separate time series. Count them before you ship.

| Label | Distinct values |
| --- | --- |
| `route` (templates) | 40 |
| `status_class` (`2xx` to `5xx`) | 4 |
| `instance` | 20 |
| `method` | 4 (but only about 80 valid route–method pairs in practice) |

For a counter: 40 routes × 4 status classes × 20 instances = **3,200 series**. Fine.

For a histogram with 10 finite buckets, each combination also produces one `+Inf` bucket, a `_sum` and a `_count`: 13 series per combination. So 3,200 × 13 = **41,600 series** from one histogram.

Now someone adds `user_id` as a label on the counter, with 50,000 active users: 3,200 × 50,000 = **160,000,000 series**. The monitoring system will run out of memory, queries will time out and the bill will arrive. The problem is not that the label is "wrong" in the abstract, but that its value set is *unbounded and growing*. A safe rule: a label may be added only if you can state its maximum number of distinct values and that number is small.

| Wanted question | Wrong approach | Right approach |
| --- | --- | --- |
| "Which user is failing?" | `user_id` label | Log with `user.id`; search logs or traces |
| "Which order is slow?" | `order_id` label | Trace; attribute on the span |
| "Which URL?" | Raw path label | Route template label |
| "Which customer tier?" | Customer name label | `tier` label (3 values) |
| "Which exact error?" | Error message label | `error_code` label from a fixed list |

**Exemplars** link a metric point to a representative trace id, so you can click from a p99 spike to an example slow trace without putting the trace id into a label.

## Dashboards that survive an incident

### Dashboard types

| Type | Question | Contents |
| --- | --- | --- |
| Service overview (RED) | "Are users OK, where is it wrong?" | Request rate, error ratio, latency percentiles per route; dependency health |
| Resource (USE) | "Is this resource saturated?" | CPU, memory, pool, disk, queue: utilisation, saturation, errors |
| Dependency | "Is the thing we call healthy from our side?" | Outbound request rate, errors and latency by dependency |
| Deployment | "Did the release change anything?" | Metrics split by `version`, deploy annotations |

### Rules for dashboard design

- **One question per dashboard**, answered from top to bottom. Link to deeper dashboards instead of piling panels on one.
- **Ratios and percentiles**, with explicit units and fixed, honest axes (starting at zero for ratios unless you have a reason).
- **Variables** for `service`, `environment` and `route` so one dashboard serves many services; but keep a *default* view that works with no clicks.
- **Annotations** for deploys, feature flags, config changes and incidents. Half of all diagnosis is "what changed at that moment?".
- **Split by version** during and after a rollout. A canary that is 5% of traffic is invisible in a fleet-wide average.
- **Show absence.** A panel that shows nothing is ambiguous; add a "last sample age" or `up` panel so missing data is visible.

### Queries behind a service overview (illustrative PromQL)

```text
# Request rate per route
sum by (route) (rate(http_requests_total{service="orders-api"}[5m]))

# Error ratio (5xx share of valid requests; excludes health checks)
sum(rate(http_requests_total{service="orders-api", code=~"5..", route!="/healthz"}[5m]))
/
sum(rate(http_requests_total{service="orders-api", route!="/healthz"}[5m]))

# p99 latency by version, to spot a bad release
histogram_quantile(0.99,
  sum by (le, version) (rate(http_request_duration_seconds_bucket{service="orders-api"}[5m])))

# Saturation: database pool in use over capacity
db_pool_in_use{service="orders-api"} / db_pool_size{service="orders-api"}
```

**Choose the rate window deliberately.** A `rate(...[5m])` window averages over five minutes. It should span at least four scrape intervals (with a 15-second scrape, at least one minute) so a single missed scrape does not produce gaps. Longer windows smooth noise but delay detection; shorter windows react faster but jump around.

## Alerts

### Symptoms versus causes

An alert interrupts a person. It must be justified by *user impact* or *imminent* user impact.

| Alert on (symptom) | Put on a dashboard (cause) |
| --- | --- |
| Error ratio of the checkout journey above target | CPU at 85% |
| p99 latency above objective for 10 minutes | Garbage collection pause time |
| No successful payments for 5 minutes during business hours | One instance restarted once |
| Disk will fill within 4 hours (saturation, leading) | Disk at 70% |

Cause-based alerts have two failure modes: they fire without users being hurt (noise), and they miss problems whose cause you did not predict (blind spots). Symptom alerts catch all causes, including unforeseen ones, and the dashboards help you find which.

### Anatomy of an alert rule

```yaml
groups:
  - name: orders-api
    rules:
      - alert: OrdersHighErrorRatio
        expr: |
          sum(rate(http_requests_total{service="orders-api",code=~"5..",route!="/healthz"}[5m]))
          /
          sum(rate(http_requests_total{service="orders-api",route!="/healthz"}[5m])) > 0.02
        for: 10m
        labels:
          severity: page
          team: orders
        annotations:
          summary: "orders-api error ratio above 2% for 10 minutes"
          runbook_url: https://runbooks.example.com/orders-high-errors
```

Each element has a job.

| Element | Job | Trade-off |
| --- | --- | --- |
| `expr` | The condition | A fixed threshold is crude; the Professional section replaces it with burn rate |
| `for` | The condition must hold this long | Longer reduces false alarms from blips but delays detection by the same amount |
| `severity` | Decides who is interrupted and how | A rule marked `page` that nobody acts on trains people to ignore pages |
| `runbook_url` | What it means, how to verify, how to mitigate | Without it the on-call must reinvent the investigation at 03:00 |
| Routing labels | Which team receives it | Wrong routing is a common cause of slow response |

A firing rule is not necessarily a page. The threshold, the `for` duration and the severity together decide *who is interrupted*. A rule with severity `ticket` creates a work item for working hours.

### Notification routing

```yaml
# Alertmanager-style routing (simplified)
route:
  receiver: team-chat
  group_by: [alertname, service]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - matchers: [severity="page"]
      receiver: on-call-pager
    - matchers: [severity="ticket"]
      receiver: ticket-queue
inhibit_rules:
  - source_matchers: [alertname="DatabaseDown"]
    target_matchers: [alertname="OrdersHighErrorRatio"]
    equal: [service]
receivers:
  - name: on-call-pager
  - name: ticket-queue
  - name: team-chat
```

*Grouping* turns 40 related alerts into one notification; *inhibition* silences symptoms when a known cause is already firing; `repeat_interval` controls how often a still-firing alert reminds people. Test routing the way you test code: send a synthetic alert and confirm the right person receives it.

### Alert hygiene

Every alert has an owner and a runbook link; alerts that fire without needing action are deleted, tuned or downgraded within a week; missing data is alerted on explicitly (`absent(up{service="orders-api"})` or a heartbeat series); silences have an expiry and a reason.

## A typical incident, diagnosed from queries

Scenario: at 14:05 the checkout error alert fires: `OrdersHighErrorRatio` for `orders-api` (5xx above 2% for 10 minutes). Follow the diagnosis by evidence.

**1. Confirm and scope.** Open the service overview. The error ratio reads 6.1% since 13:52. Split by route:

```text
sum by (route) (rate(http_requests_total{service="orders-api",code=~"5.."}[5m]))
```

*Illustrative result:* `POST /v1/orders` produces nearly all the 5xx; `GET /v1/orders/{id}` is near zero. So reads are healthy and the write path is failing.

**2. Latency or errors?** The write route's p99 rose from 0.4 s to 2.0 s at the same time, and 2.0 s is exactly the client timeout configured for the payment call. A latency that clusters at a round number is a strong hint of a *timeout*.

**3. Which dependency?** Check outbound metrics by dependency:

```text
sum by (dependency) (rate(outbound_requests_total{service="orders-api",outcome="error"}[5m]))
```

*Illustrative result:* `dependency="payments"` errors jumped; `dependency="database"` is flat. The payment provider is the suspect.

**4. Corroborate with traces.** Open three slow `POST /v1/orders` traces. In each, the span `payments.charge` lasts 2,000 ms and ends with status `error` and event `timeout`. Everything else in the trace is normal.

**5. Corroborate with logs.** Query logs by `error.code="PAY_TIMEOUT"` grouped by `version`.

```text
version=1.8.0: 412 events
```

Only one version exists in production, so that grouping does not discriminate. Check by payment *region* instead: all errors come from calls to the provider's EU endpoint; calls to its US endpoint succeed. That is a better discriminator than the version.

**6. Is it us?** Did we deploy? The deploy annotations show nothing since the previous day. Did we change the provider configuration? A config-change annotation exists at 13:49: the EU endpoint URL was updated. Seven minutes later the errors began.

**7. Act reversibly.** Revert the config to the previous endpoint. Within two minutes, the `payments` error ratio and the checkout error ratio fall. The alert resolves after the `for` window clears. Confirm using the original measurement (checkout error ratio) rather than assuming.

**8. What would a stricter investigator add?** The hypothesis "the new EU endpoint is slow or unreachable from our network" fits all the evidence, but we have not looked at the provider's own status or at DNS and TLS timing from our side. State that gap in the write-up and add a synthetic probe for each provider endpoint.

Compare the method with the Beginner investigation: symptom, scope, dimension, example, corroboration, change, reversible action, confirmation. The queries get more specific; the structure does not change.

## SLIs, SLOs and error budgets, a first look

Before the Professional section develops these, learn the definitions.

- An **SLI** (service level indicator) is a measured ratio of *good events* to *valid events*, for example "successful requests ÷ valid requests".
- An **SLO** (service level objective) is a target for the SLI over a window, for example "99.5% over 30 days".
- The **error budget** is what the SLO allows to fail: 100% − SLO.

**Worked example.** `orders-api` serves 1,000 requests per hour at steady rate, so 720,000 in 30 days. A 99.5% SLO allows 0.5% to fail: 3,600 failed requests in the window. If the service had one hour with 8 failed requests out of 1,000, that is 0.8% for the hour — worse than the target for that hour — but only 8 ÷ 3,600 ≈ 0.22% of the 30-day budget. A ticket would be reasonable; a page would be an overreaction. If instead 400 of 1,000 requests failed in that hour, the hour consumed 400 ÷ 3,600 = 11% of the monthly budget in 60 minutes: that is user impact worth interrupting a person.

The difference between the two cases is *how fast the budget is being spent*, which is exactly what burn-rate alerting measures.

## What can go wrong: a catalogue

| Problem | How it appears | Likely cause | Remedy |
| --- | --- | --- | --- |
| Dashboards disagree | Two panels show different error ratios | Different denominators (health checks included in one), different windows | Define the SLI once; reuse the query |
| Alert fires, nothing is wrong | Short spike beyond threshold | No `for`, tiny traffic, noisy metric | Add `for`, use ratio plus minimum count |
| Alert never fires during an outage | Dashboards red, silence on the pager | Metric missing, label mismatch after rename, routing error | Alert on absent data; test routing; use symptom metrics |
| Broken traces | Trace stops at a service | Header stripped or not extracted | Check propagation in order: inject, proxy, extract, context loss |
| High cost | Rising bill, slow queries | Label cardinality, debug logs left on | Cardinality budget, per-service quotas |
| Telemetry outage becomes service outage | Requests blocked on exporter | Synchronous export | Async, bounded buffers, drop on overflow |
| Percentile surprises | Fleet p99 does not match any instance | Averaged per-instance percentiles | Aggregate buckets, then compute quantile |
| Logs without context | Cannot find the related trace | No trace id in logs | Inject trace id in the formatter |

## Knowledge consolidation

- Agree a **small log schema** across services; use **stable messages** and named fields; put the trace id on every log line in a request.
- A **span** has a name (low cardinality), kind, attributes, events and status; **context propagation** (`traceparent`) lets a trace cross services, and breaks where a boundary does not pass it.
- **OpenTelemetry** separates API from SDK, attaches a **Resource** to all signals and uses **OTLP** and a **Collector** to decouple applications from backends.
- Choose metric types deliberately; use **histograms** for latency, aggregate buckets before computing percentiles, and place bucket boundaries at your thresholds.
- **Cardinality** is the product of label value counts, multiplied again by histogram buckets; any unbounded label is a defect.
- Dashboards answer **one question each**, show units, versions and deploy annotations, and make absent data visible.
- **Alert on symptoms**, use `for` and severity consciously, give every alert an owner and a runbook, and test routing.
- Telemetry must **fail safe**: the service survives a Collector outage.
- An SLO turns "is it bad?" into arithmetic: the budget is consumed at a rate, and the rate decides page versus ticket.

## Exercises

**Exercise 1 — Make logs queryable.** Take five log lines from a service you know. Rewrite each as a structured record following the minimum schema. For each, state the question the line now answers and which field you would group by.

**Exercise 2 — Cardinality budget.** A service has 60 route templates, 5 status classes, 30 instances and a latency histogram with 12 finite buckets. Compute the series count for the counter and for the histogram. A developer proposes adding `customer_id` (8,000 customers). Compute the new counter series count and write the review comment you would leave.

**Exercise 3 — Propagation test.** In a development environment, make a request through two services and show that the trace has spans from both under one trace id. Then remove the header injection in the caller and describe what the trace looks like. Restore it.

**Exercise 4 — Collector outage drill.** Run `orders-api` with the Collector, generate steady load, stop the Collector for two minutes and record request success rate and latency throughout. State whether exporters blocked requests, and fix it if they did.

**Exercise 5 — Write an alert.** For a service with SLI "successful requests ÷ valid requests" and SLO 99.5% over 30 days, write the budget in requests for a service with 500,000 requests per month. Then write one alert rule using a ratio and a `for` clause, with severity and a runbook link, and explain which part of the rule decides whether someone is woken.

**Exercise 6 — Diagnose from a table.** Given: error ratio rose from 0.1% to 4% at 09:40; the deploy log shows release 2.3.1 at 09:35; p99 for route `/v1/search` rose from 0.3 s to 5 s while other routes are unchanged; traces for `/v1/search` show a 4.8-second span `search-index.query`; the search index dashboard shows a reindex job started at 09:38. List three competing hypotheses, the evidence for and against each, and the one measurement that would best separate them.

**Solution notes.**

*Exercise 1.* A good answer keeps messages stable (`"payment failed"`, not a sentence with the order id), moves variable data into fields and names a grouping field such as `error.code`. If your line cannot be counted by one field, it is still free text.

*Exercise 2.* Counter: 60 × 5 × 30 = 9,000 series. Histogram: each combination has 12 buckets + `+Inf` + `_sum` + `_count` = 15 series, so 9,000 × 15 = 135,000 series. With `customer_id`: 9,000 × 8,000 = 72,000,000 series for the counter alone. Review comment: reject the label; explain that the value set is unbounded and multiplies every other label; propose logging `customer.id` and using traces, or a bounded `tier` label if the aim is segmentation.

*Exercise 3.* With the header removed, the callee starts a new trace with a different trace id, so you see two unrelated traces rather than one tree: the request "disappears" at the boundary. If you see one tree even without the injection, check whether a proxy or an auto-instrumentation layer is injecting it for you.

*Exercise 4.* Expected: request success rate and latency stay unchanged while telemetry drops. If latency rose or requests failed, the exporter is synchronous or its queue is unbounded and blocking; switch to an asynchronous batch exporter with a bounded queue that drops on overflow. Record the numbers before and after the fix.

*Exercise 5.* Budget = 0.5% × 500,000 = 2,500 failed requests per month. An example rule: error ratio > 0.02 over 5 minutes for 10 minutes, severity `page`, runbook linked. The `severity` label together with routing decides whether anyone is woken; the `for` clause decides how long the condition must persist first. A thoughtful answer notes that a fixed 2% threshold is arbitrary relative to the budget, and looks ahead to burn-rate alerts.

*Exercise 6.* Hypotheses: (1) release 2.3.1 changed the search query; (2) the reindex job started at 09:38 is competing for index resources; (3) a dependency of the index (storage) is slow. Evidence for (1): release five minutes before; against: the symptom began after 09:38, not 09:35, and only the search route is affected. For (2): timing matches 09:38 and the span is the index query; against: no direct measure of index load given. For (3): none given. The best separating measurement is the index query latency split by `version` while the reindex job is running and, if possible, pausing the reindex job (a reversible action) and seeing whether latency recovers. If the symptom persists after the pause, hypothesis (1) rises.

## Mentoring prompts

Explain why putting `user_id` on a metric is a mistake, and what you would do instead. Why can you not average p95 values from two instances? Describe what happens to a trace if one proxy strips the `traceparent` header. What is the difference between an alert's `for` duration and its threshold, and how does each trade detection speed against false alarms?

---
