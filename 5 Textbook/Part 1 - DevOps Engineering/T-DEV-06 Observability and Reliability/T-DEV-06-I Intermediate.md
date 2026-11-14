# T-DEV-06-I — Intermediate Practice

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-i"></a>
#### T-DEV-06-I — Intermediate Practice

**Metrics in practice.**

- Count requests and errors by *route template* and *status class*, not by raw URL.
- Measure latency with histograms; percentiles from histograms can be aggregated across instances. You cannot average p95 values across instances and call the result the p95.
- Keep **label cardinality** low. Prefer `service.name`, environment, route template and status class. Avoid user ids, raw URLs containing ids, request ids and emails as labels; each unique value creates a new time series, which drives cost and slows queries.

**Logs in practice.** Minimum fields: timestamp, severity, service name, message, a stable error code where applicable, and trace and span identifiers when a request is in flight. Separate *diagnostic* events (help debug incidents) from *audit* events (who changed what; different retention and access).

**Traces in practice.** A trace is a tree of spans; *context propagation* passes the trace id across HTTP and messaging boundaries; *sampling* keeps only some traces, so absence of a trace does not mean the request did not happen. Use metrics for rates and traces for causality.

| Symptom | CPU graph alone | Trace with dependency spans |
| --- | --- | --- |
| Slow database query | May look idle or busy depending on waits | Long client span to the database |
| Slow handler (internal sleep) | CPU low | Long internal span in the service |

"CPU is high after the deploy" is an incomplete diagnosis; it does not say which operation, which dependency or which version.

**A vendor-neutral pipeline.** Instrument with OpenTelemetry, send over OTLP to a Collector, and let the Collector fan out to backends. Resource attributes (`service.name`, `service.version`, `deployment.environment.name`) are the glue.

```python
from opentelemetry import metrics, trace
tracer = trace.get_tracer("orders-api")
meter = metrics.get_meter("orders-api")
requests = meter.create_counter("orders_requests_total")

def get_order(order_id):
    with tracer.start_as_current_span("get_order") as span:
        requests.add(1, {"route": "/v1/orders/{id}"})
        span.set_attribute("order.found", True)   # no PII, no unbounded values
```

```yaml
# collector configuration (simplified)
receivers:
  otlp: { protocols: { grpc: {}, http: {} } }
processors:
  batch: {}
exporters:
  otlphttp/traces: { endpoint: http://trace-backend:4318 }
  prometheus: { endpoint: 0.0.0.0:8889 }
service:
  pipelines:
    traces:  { receivers: [otlp], processors: [batch], exporters: [otlphttp/traces] }
    metrics: { receivers: [otlp], processors: [batch], exporters: [prometheus] }
```

**Telemetry must not take the service down.** Stop the collector and confirm the application keeps serving; exporters should buffer and drop, not block requests.

**Correlation.** Prove a single request can be followed end to end: the HTTP response, the log line and the trace share a trace id.

**SLIs, SLOs and alerts.**

- An *SLI* (service level indicator) is a measured ratio of good events to valid events.
- An *SLO* is a target for the SLI over a window.
- The *error budget* is what the SLO allows to fail.

Example: a 99% SLO over 1,000 requests permits 10 failures. Eight failures in a minute followed by recovery may be well inside budget: open a ticket, don't page. Failures continuing past budget burn are user impact: page with a runbook.

```yaml
groups:
  - name: orders-slo
    rules:
      - alert: OrdersHighErrorRatio
        expr: |
          sum(rate(http_requests_total{service="orders-api",code=~"5.."}[5m]))
          / sum(rate(http_requests_total{service="orders-api"}[5m])) > 0.02
        for: 10m
        labels: { severity: page }
        annotations: { runbook_url: https://runbooks.example.com/orders-high-errors }
```

A firing rule is not necessarily a page: the `for` duration, the threshold and the severity decide who is interrupted.

**Exercise.** Define two SLIs for a service, compute the error budget for a given window and write one alert with a runbook link.
