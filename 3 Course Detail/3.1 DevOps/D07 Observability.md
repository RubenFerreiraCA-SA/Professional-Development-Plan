# D07 — Observability

| | Details |
| --- | --- |
| **Estimated study time** | 18–28 hours |
| **Prerequisites** | [D03 — Docker and Containerization](D03%20Docker%20and%20Containerization.md), [D04 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md), [D06 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md); familiarity with HTTP, databases, distributed services and structured logging. |

## Objective

Design **observability as a reliable, vendor-independent platform capability**. Develop the engineering judgement to identify important service behaviour, instrument applications correctly, design meaningful service objectives, diagnose unfamiliar failures and balance the usefulness of telemetry against privacy, complexity and cost.

This module establishes the principles and implements a small, working **OpenTelemetry-based reference environment**. [D08 — Datadog](D08%20Datadog.md) builds on that foundation to operate a complete observability service with a specific provider.

## Outcomes

1. Differentiate monitoring and observability and select appropriate signals for known and unknown failure modes.
2. Understand and correctly instrument metrics, structured logs, distributed traces, events and relevant profiles or synthetic checks.
3. Explain context propagation, sampling, high-cardinality dimensions, metric aggregation and the limitations of telemetry.
4. Develop service-oriented SLIs, realistic SLOs, error-budget policies and actionable alerts.
5. Investigate failures systematically using symptoms, hypotheses, correlated evidence and controlled experiments.
6. Design a secure telemetry pipeline including application instrumentation, collector/agent, processing, storage and query/visualisation.
7. Define a reusable observability contract that development teams can adopt with minimal platform-specific knowledge.

## 1. Observability and engineering questions

**Monitoring** usually answers known questions such as “is the service available?” **Observability** supports answering new questions about internal behaviour from externally collected signals. Neither is a substitute for resilient system design.

Consider three levels of observation:

- **User experience:** Can users complete their critical workflows? What is the error rate, duration and availability?
- **Application and dependencies:** Where does time go? Which dependency, database operation or deployment version correlates with the symptom?
- **Platform:** Are containers restarting, network paths failing, reconciliation loops stuck or resources exhausted?

Contrast the **four golden signals** (latency, traffic, errors, saturation) and the **RED** and **USE** methods. Explain why no one framework replaces understanding the system.

**Exercise:** For the Final Project API, write down six incident questions a responder must answer. Map each question to the smallest useful telemetry signals and diagnostic queries. Identify blind spots.

## 2. Metrics, logs, traces and causality

### Metrics

Differentiate counters, gauges, histograms and distributions. Explain rates, aggregation windows, percentiles, histogram buckets and why you cannot reliably average service-level percentiles across instances.

Design semantic dimensions such as `service.name`, `deployment.environment.name`, route template, operation type and dependency name. Explain why user IDs, raw URLs and request IDs should **not** generally be metric labels.

### Logs and events

Use structured logs with timestamps, severity, service identity, stable error codes, request/trace correlation and an intelligible message. Explain why logging entire request bodies or credentials is dangerous.

Differentiate a diagnostic event from an audit event. Decide what must be retained, protected and searchable.

### Distributed traces

Explain trace IDs, span IDs, parent/child relationships, propagation across HTTP and asynchronous boundaries, span status and baggage. Discuss sampling trade-offs: a missing trace does not prove an operation never occurred.

**Lab:** Instrument a request that moves through an API and database or second service. Generate correlated logs and spans. Show that one request can be followed across boundaries and distinguish request latency from time spent in dependencies.

**Interpretation exercise:** Compare a real slow database call with an artificially slow request handler. Show why a dashboard displaying only aggregate CPU utilisation cannot reliably distinguish them.

## 3. Telemetry pipeline design

Draw the complete data path:

`application → SDK/auto-instrumentation → collector or agent → processing/sampling → backend → dashboards/alerts`

Cover:

- Push versus pull collection and delivery trade-offs.
- OpenTelemetry semantic conventions, resource attributes, instrumentation libraries and exporter choice.
- Collector pipelines, processors, batching, queue limits, backpressure, retries and sampling.
- Cardinality growth, data retention, aggregation and ingestion/indexing costs.
- Encryption in transit, credentials, access control, masking/redaction and personally identifiable data.
- Failure behaviour when a collector or backend is unavailable: telemetry should degrade gracefully rather than routinely break application requests.

**Lab:** Use an OpenTelemetry Collector with a local compatible backend or diagnostic exporter. Start with a trace and metric, introduce a controlled collector outage, and record application impact, dropped data and recovery behaviour.

**Design decision:** State what will remain provider-neutral and where a vendor-specific integration will be permitted.

## 4. SLIs, SLOs and effective alerting

Choose two critical user journeys for the application and one platform workflow (for example deployment success or environment provisioning).

For each, define:

| Component | Required decision |
| --- | --- |
| SLI | Precise numerator/denominator or measurement; avoid ambiguous “uptime” labels |
| SLO | Target and evaluation window justified by user expectations |
| Data source | Instrumentation and query that yield the SLI |
| Error budget | Acceptable failure within the evaluation window, with a clear interpretation |
| Alert | User-impacting condition, urgency, owner, route and first diagnostic action |
| Runbook | Verification, probable causes, mitigation, recovery and escalation |

Distinguish SLIs from contractual SLAs and discuss burn-rate alerts, false positives, missing data and alert fatigue. Do not use infrastructure-only thresholds as a substitute for user experience.

**Exercise:** Calculate the error budget for a chosen SLO and use synthetic request data to evaluate a short-lived spike versus sustained degradation. Explain which merits paging and which is better suited to a ticket or dashboard.

## 5. Evidence-led incident investigation

**Scenario:** A rollout coincides with rising API latency and elevated container CPU. A database is also reporting slower responses.

Investigate in an isolated environment:

1. Define the user-visible symptom and when it began.
2. Form competing hypotheses: application regression, database latency, exhausted pool, CPU contention or instrumentation failure.
3. Examine traces, request metrics, logs, deployment changes and dependency signals.
4. Run a controlled test to discriminate hypotheses; record evidence that *contradicts* an initial theory.
5. Apply a reversible corrective action, confirm the user-facing SLI and document what remains uncertain.
6. Produce a brief incident timeline, contributing factors and a preventive improvement.

Emphasise that correlation alone is not causation. A rollback is justified by evidence and operational risk, not just because a deployment occurred nearby in time.

## 6. Observability as a platform product

Define a minimal **observability contract** for teams onboarding to the future Internal Developer Platform:

- Required service, environment, version and ownership attributes.
- Standard HTTP/server/database instrumentation and trace propagation.
- Baseline user-facing metrics, structured logging and privacy restrictions.
- SLI/SLO documentation and ownership of alert response.
- Sampling, retention and telemetry budget expectations.
- Developer-facing starter configuration and a test that validates instrumentation.

Compare onboarding effort for a new service **with and without** the starter contract. Record how a developer will find dashboards, traces and runbooks.

## Practical Assessment — design and diagnose an observable service

Deliver evidence independent of any particular commercial monitoring vendor:

1. A documented telemetry architecture and an instrumented two-component request path with correlated logs/traces and useful metrics.
2. A reproducible local or sandbox collection/export pipeline, including a collector/backend failure test.
3. Two justified application SLIs/SLOs and one platform workflow SLI, plus error-budget examples.
4. A well-defined alert and runbook for a user-impacting condition, with rationale for urgency and ownership.
5. An investigation of a deliberately degraded service, including competing hypotheses, evidence and verified remediation.
6. A reusable instrumentation/onboarding contract with privacy and cardinality controls.

**Acceptance:** Another engineer can reproduce the failure, trace it to the cause using the available evidence, and explain which telemetry would be unreliable or absent. The work must demonstrate **diagnostic reasoning**, not merely that dashboards contain data.

## Further learning

- [OpenTelemetry — Documentation](https://opentelemetry.io/docs/)
- [OpenTelemetry — Concepts](https://opentelemetry.io/docs/concepts/)
- [OpenTelemetry — Collector](https://opentelemetry.io/docs/collector/)
- [Google SRE — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Google SRE — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)

**Previous:** [D06 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md) · **Next:** [D08 — Datadog](D08%20Datadog.md)
