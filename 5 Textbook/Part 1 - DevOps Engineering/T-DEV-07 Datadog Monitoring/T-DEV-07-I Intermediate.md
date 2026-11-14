# T-DEV-07-I — Intermediate Practice

*Chapter: [T-DEV-07 — Datadog Monitoring](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-07-i"></a>
#### T-DEV-07-I — Intermediate Practice

**Infrastructure and container monitoring.** Start with a baseline: host CPU, memory, disk and network; per-container CPU and memory; restarts. Learn to separate *memory pressure* (the container approaches its limit and may be killed) from *an application exception* (errors with normal resource use) by comparing the container memory graph with error rates and logs.

**Logs, APM and correlation.** Produce success, failure and slowness and confirm each leaves evidence. Make logs JSON with the trace and span ids so Datadog can link a log to its trace (and a trace to its logs): configure the log pipeline's trace-id remapper, and verify both directions — from a trace to its logs and from a log to its trace. Break propagation on purpose (drop the trace id from a log format) and restore it.

**Sampling honesty.** Compare the APM trace count with a request-count metric during a busy minute. Missing traces do not mean zero traffic; use metrics for rates and traces for causality.

**Governance for logs.** Add exclusion filters or disable indexing for noisy health checks, scrub sensitive fields (deny-list `password`, `token`, `authorization`), and record retention differences between indexed logs and archives.

**Dashboards, SLOs and monitors.**

- Build a *user-centric* dashboard first: request rate, error ratio, latency percentiles, dependency latency, saturation and the deployed version marker.
- Create an SLO from the SLI you defined in T-DEV-06 (for example, ratio of non-5xx requests on the critical route over 30 days).
- Create two monitors and validate each by inducing the condition: one for user impact (error ratio or latency), one for missing telemetry (no data from the service). Observe the status transitions (OK → Alert → OK; OK → No Data → OK).

**Refine noisy monitors.** Create a deliberately noisy monitor (for example CPU above 5%), watch it flap, then fix it with a longer evaluation window, grouping or a smarter query. Record before and after.

**Troubleshooting**

| Symptom | Likely cause | First check |
| --- | --- | --- |
| No host in the UI | Wrong key or site | `agent status`; key reaches the container |
| No traces | Application pointed at another collector, or wrong host or port | Application environment; Agent APM port |
| Logs not linked to traces | JSON not parsed, remapper missing | Log pipeline; sample log fields |
| Monitor never alerts | Window too long or wrong query | Induce a fault; wait the evaluation window |
| Unexpected large bill | Collect-all logs, high-cardinality tags | Exclusions; tag allow-list |

**Exercise.** Plant a regression (a slow dependency or an error injected for one route), investigate from the dashboard and traces only, fix it and show the SLO recovering.
