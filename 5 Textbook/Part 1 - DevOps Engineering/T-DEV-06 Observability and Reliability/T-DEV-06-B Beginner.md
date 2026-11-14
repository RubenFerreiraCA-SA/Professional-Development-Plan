# T-DEV-06-B — Beginner Foundations

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-b"></a>
#### T-DEV-06-B — Beginner Foundations

**Monitoring versus observability.**

| | Monitoring | Observability |
| --- | --- | --- |
| Typical question | "Is the known check green?" | "Why is this user journey slow today?" |
| Strength | Cheap, clear targets for known failures | Explore unknown failure modes |
| Failure mode | Blind to novel faults | Noise, cost and cardinality if unconstrained |

Neither replaces resilient design.

**Three levels to observe.** *User experience* (can clients complete the critical request, how often does it fail, how long does it take?), *application and dependencies* (where does time go, which version correlates?) and *platform* (restarts, memory kills, disk full, saturated CPU, stuck deployments).

**Frameworks as checklists**

| Framework | Focus |
| --- | --- |
| Four golden signals | Latency, traffic, errors, saturation |
| RED (request-driven services) | Rate, Errors, Duration |
| USE (resources) | Utilisation, Saturation, Errors |

**The three signal types**

| Signal | What it is | Good for |
| --- | --- | --- |
| Metrics | Numbers over time | Trends, alerts, capacity |
| Logs | Timestamped event records | Detail about one event |
| Traces | A request's path across components as timed spans | Where the time went and what called what |

**Metric types.** A *counter* only goes up (requests, errors) and is usually queried as a rate. A *gauge* goes up and down (in-flight requests, queue depth). A *histogram* records value distributions so you can compute percentiles.

**A first structured log line**

```json
{"ts":"2026-03-01T10:15:04Z","level":"error","service":"orders-api","msg":"payment timeout","error.code":"PAY_TIMEOUT","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
```

Structured logs are machine-parseable; the trace id lets you jump from a log line to the whole request trace. Never log passwords, tokens, `Authorization` headers or full bodies containing personal data.

**Six questions a responder must answer**

1. Are users failing the critical path right now?
2. When did it start?
3. Is it one route or everything?
4. Is the time spent in this service or a dependency?
5. Did we ship something recently?
6. Is the telemetry itself missing or lying?

**Exercise.** For a service you know, write these six questions and name the smallest signal that answers each. Note which have no signal today — those are your blind spots.
