# T-DEV-07-E — Expert Depth

*Chapter: [T-DEV-07 — Datadog Monitoring](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-07-e"></a>
#### T-DEV-07-E — Expert Depth

**Platform design questions.** How many tags and what values may a team add before cost becomes unmanageable? Who may create monitors that page, and who reviews them? How do you prevent each team from building a different dashboard for the same service? The answers form a governance model: templates and defaults from the platform team; ownership and tuning by service teams; periodic reviews that delete unused assets.

**Cardinality and cost economics.** Custom metrics are typically billed by unique tag combinations. A single tag with an unbounded value (user id, request id, raw URL) can multiply cost by orders of magnitude. Enforce at three points: code review and libraries (stop labels at the source), the Agent or Collector (drop or aggregate attributes), and the backend (allow-lists, quotas). Track cost per service and surface it to owners.

**Sampling, ingestion controls and retention trade-offs.** Decide per service what to keep: all errors, all slow traces, a low percentage of normal traces. Understand which data is indexed (searchable, expensive) versus ingested and archived (cheaper, slower to query). Document what you cannot answer after retention expires.

**Reliability of the monitoring itself.** Monitoring has failure modes: Agent crash, key revocation, network partitions, intake outage, clock skew and tag drift after a deployment. Mitigate with a heartbeat metric emitted from the service, a monitor on its absence, a secondary notification path for the monitoring platform itself, and a runbook for "monitoring is down". Test it.

**Vendor strategy.** Standardise on OpenTelemetry instrumentation and a Collector layer as an abstraction; treat vendor-specific features (proprietary dashboards, notebooks, security products) as value-added with a conscious switching cost. Export monitor and dashboard definitions as code so migration is possible. Evaluate vendors on query power, retention costs, cardinality handling, support, data residency and security attestations.

**Governance model as a concrete document.** A usable governance model fits on one page and has owners:

| Asset | Platform team provides | Service team owns | Review cadence |
| --- | --- | --- | --- |
| Tags | Allowed keys (`service`, `env`, `version`, `team`, `tier`), value formats, CI check | Correct values for each service | Quarterly: delete unused keys |
| Monitors | Templates for error rate, latency, saturation, heartbeat | Thresholds, routing, tuning | Monthly review of monitors that fired but led to no action |
| Dashboards | One standard service dashboard per tier | Extra panels for their own domain | Remove dashboards with no views in 90 days |
| Paging | Escalation policies, integrations | Which monitors page and who is on call | After every incident |
| Cost | Visibility per service, budgets | Staying within budget or justifying growth | Monthly cost review |

The aim is to make the default path correct (templates and policy-as-code) so that governance is not a ticket queue.

**Cardinality: the arithmetic.** A custom metric's series count is the product of each tag's distinct values. One metric `orders.processed` with `env` (3 values) × `service` (1) × `region` (4) × `status` (5) = 60 series. Add a `customer_id` tag with 20,000 customers and it becomes 1,200,000 series, a 20,000-fold cost increase from one line of code. Rules that work:

| Enforcement point | Control | Example |
| --- | --- | --- |
| Code review and library | Wrapper that only accepts allow-listed tag keys; lint for unbounded values (ids, raw URLs, emails) | A metrics helper that rejects `user_id` at test time |
| Agent or Collector | Drop, hash or aggregate attributes; normalise route templates (`/orders/{id}`, not `/orders/123`) | Collector processor deleting `request_id` |
| Backend | Allow-lists, per-service quotas, alerts on series growth | Alert if a service adds more than 10% new series per day |

Detect a spike in hours: a daily (or hourly) job exports series count by service and metric, compares with a baseline, and notifies the owning team before the invoice does. Keep the owner's name next to every cost line so action is possible.

**Sampling and retention: a decision table per service tier**

| Data | Tier 1 (revenue path) | Tier 3 (internal tool) | What is lost |
| --- | --- | --- | --- |
| Error traces | Keep all | Keep all | Nothing meaningful |
| Slow traces (above objective) | Keep all | Sample 25% | Some rare slow requests |
| Normal traces | 1–5% | 0–1% | Ability to inspect an arbitrary healthy request later |
| Logs | Index errors and warnings; archive the rest | Index errors only | Cheap full-text search on info-level logs after the index window |
| Metrics | Full resolution for objective-related metrics | Default | Fine-grained history after rollup |

Write down, per tier, the questions you *cannot* answer after retention ends (for example "what did an ordinary request look like 45 days ago?"). Compliance, security investigation and capacity planning are the questions that usually need longer retention; arrange archives for them deliberately.

**Monitoring the monitor: failure modes and detections**

| Failure | Symptom | Detection independent of the failing component | Response |
| --- | --- | --- | --- |
| Agent crash on a host | Host data stops | Missing-data monitor on a heartbeat metric emitted by the service | Restart; check for OOM or bad config |
| API key revoked or rotated | All data from a group stops at one time | Synthetic check or heartbeat from outside | Re-issue key via secret manager; confirm rollout |
| Network partition to intake | Data buffered then dropped | Agent status and local queue metrics | Verify egress; consider a regional proxy |
| Vendor intake outage | Everything missing at once | Status page feed plus a secondary notification path (email/chat) | Switch to local diagnostics (logs, `kubectl`, host tools) |
| Clock skew | Spans out of order, gaps | Time-sync monitor | Fix NTP; ignore data from skewed window |
| Tag drift after deployment | Monitors silently stop matching | Monitors on "no data for service X" and a CI check on tags | Fix the tag source; add the check |

The "monitoring is down" runbook should work *without* the monitoring platform: how to find the failing service from logs on the host, where on-call contact lives, and who may declare an incident when no alert will ever arrive.

**Vendor strategy: a way to compare.** Evaluate with a small proof of concept rather than slides.

| Criterion | Test to run |
| --- | --- |
| Query power | Reproduce your five hardest investigations; time them |
| Cost model | Feed a month of your real volumes into the pricing model; include indexing, custom metrics, spans, logs, retention |
| Cardinality handling | Add a high-cardinality tag on purpose; observe the cost and the controls |
| Portability | Re-point the OpenTelemetry Collector export to a second backend; export monitors as code and re-create them |
| Data residency and attestations | Confirm region options and required certifications against your requirements |
| Support and operations | File a real question; measure response and quality |

Switching cost is lowest when instrumentation is OpenTelemetry, definitions live in Terraform (or equivalent), and dashboards are derived from templates. It is highest where teams have built on proprietary notebooks, bespoke query functions, or vendor-specific agents with no export. Adopt such features knowingly, and record the decision.

**Failure modes of the observability programme**

- Alert fatigue: pages that no one acts on teach people to mute monitors. Track actionability, and retire or tune monitors that are not.
- Dashboard sprawl: dozens of near-duplicate dashboards, none trusted.
- Cost surprises that arrive after a quarter-end review, because cost was never attributed to a service owner.
- A "central observability team" that becomes a bottleneck: provide self-service, templates and guardrails instead.

**Mentoring prompts.** A team reports "Datadog shows no data" — give the ordered checks from the application to the backend. How would you detect and stop a tag-cardinality cost spike in hours, not at invoice time? What is the minimum viable set of monitors for a new service, and how do you stop teams from muting them?

---
