# T-DEV-07-P — Professional Engineering

*Chapter: [T-DEV-07 — Datadog Monitoring](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-07-p"></a>
#### T-DEV-07-P — Professional Engineering

**Incident response in the platform.** Run two drills. In the first, a planted regression degrades one route: identify it from the dashboard, follow traces to the slow span, correlate logs and the deployed version, revert, and confirm recovery. In the second, make the Agent a blind spot (stop it or break its key): the user-impact monitor may remain quiet while the *missing-data* monitor fires. Understand which failures each monitor can and cannot see.

**Monitors as code.** Manage monitors, dashboards and SLOs with Terraform so they are reviewed, versioned and reproducible:

```hcl
resource "datadog_monitor" "orders_error_ratio" {
  name    = "orders-api error ratio (staging)"
  type    = "query alert"
  query   = "sum(last_10m):sum:trace.http.request.errors{service:orders-api,env:staging}.as_count() / sum:trace.http.request.hits{service:orders-api,env:staging}.as_count() > 0.02"
  message = "Error ratio above 2%. Runbook: https://runbooks.example.com/orders-high-errors @team-orders"
  monitor_thresholds { critical = 0.02 }
  notify_no_data    = true
  no_data_timeframe = 20
  tags = ["service:orders-api", "env:staging", "owner:team-orders"]
}
```

Run a preflight (validate, plan) in CI with scoped application keys, and keep keys out of the repository.

**An onboarding package for other services.** Make Datadog a reusable platform service:

| Item | Content |
| --- | --- |
| Required tags | `service`, `env`, `version`, `owner` |
| Instrumentation | Library and configuration, log format with trace ids |
| Starter assets | Dashboard template, SLO template, monitor templates |
| Ownership | Who owns monitors and who receives pages |
| Cost and cardinality rules | Tag allow-list, log exclusion defaults, retention |

Prove it by onboarding a second service using only the package.

**Privacy, permissions, retention and cost review**

| Topic | Control or limitation to record |
| --- | --- |
| Who can see APM and logs | Roles and teams |
| API and application key scopes | Least privilege, rotation |
| Personal data in logs and spans | Scrubbing, exclusions, tested |
| High-cardinality tags | Deny-list (user id, raw URL) |
| Retention and indexing | Plan limits |
| Estimated monthly ingest | Rough calculation from volume and list price |
| Unused dashboards and monitors | A named cleanup owner |

**Decision on the telemetry path.** Compare: OTLP straight to the Agent; the vendor tracing library; or the vendor-neutral Collector with a vendor exporter. Record which stays vendor-neutral, how sampling is set, who owns monitors, and how logs are indexed versus archived. Keep standard instrumentation so the vendor can change.

**Decision guide**

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Link logs and traces | Trace ids in JSON logs and a remapper | Hoping correlation works |
| Control cost | Exclusions, tag allow-list, retention | Collecting everything by default |
| Prove a monitor works | Induce the condition and observe the transition | Assuming a saved query is correct |
| Detect a blind Agent | A missing-data monitor | Only user-impact monitors |
| Keep keys safe | Narrow scopes, secret manager | App key inside the Agent container |
