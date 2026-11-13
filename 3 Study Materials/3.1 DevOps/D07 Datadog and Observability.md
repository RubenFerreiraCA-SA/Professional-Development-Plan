# D07 — Datadog and Observability

| | Details |
| --- | --- |
| **Estimated study time** | 24–36 hours |
| **Prerequisites** | [D03 — Docker and Containerization](D03%20Docker%20and%20Containerization.md), [D04 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md), [D06 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md), and familiarity with HTTP, distributed services and structured application logs. |

## Objective

Design **observability as a platform capability**: make it straightforward for teams to understand system behaviour, identify failures and take action without excessive telemetry cost or alert fatigue. Use Datadog as the reference tool while building portable instrumentation and reliability concepts.

## Outcomes

1. Distinguish metrics, logs, traces, profiles, events and synthetic checks, and choose each for a specific diagnostic question.
2. Instrument a multi-service workload with useful service boundaries, trace context, structured logs and actionable metrics.
3. Build dashboards around user journeys, service health and dependencies—not only CPU charts.
4. Define SLIs, realistic SLOs, error budgets and actionable alerts appropriate for an internal platform.
5. Diagnose latency, errors and resource saturation using correlation across telemetry signals.
6. Apply safe telemetry handling, cardinality controls, retention policies, privacy safeguards and spend management.
7. Deliver reusable monitoring conventions and incident-response runbooks that application teams can adopt.

## 1. Observability architecture and telemetry design

Study the difference between **monitoring known failure modes** and investigating **unknown failure modes**. Define what must be observable for a service, dependency and platform control plane.

Understand:
- Metrics (counters, gauges, histograms/distributions) and why aggregation semantics matter.
- Logs as event records; structured fields, severity, correlation IDs, meaningful errors and redaction.
- Distributed traces, spans, propagation context, sampling and the trace/log relationship.
- Infrastructure signals such as OOM termination, network failures, container restarts and scheduling pressure.
- Events, synthetic checks and real-user monitoring as additional perspectives.

**Architecture decision:** Choose a vendor-neutral instrumentation path (for example OpenTelemetry SDK and collector where appropriate) and describe how data reaches Datadog. Separate application instrumentation from agent deployment and backend-specific configuration.

**Lab:** Instrument an API and database operation; demonstrate a request moving through service boundaries with a trace ID and matching structured logs. Avoid including personal data, tokens or secrets in attributes.

## 2. Collect trustworthy signals

Deploy Datadog agents or a suitable collector to the local/isolated environment.

- Collect host/container and application metrics.
- Centralise structured application logs; define service, environment and version tags consistently.
- Instrument application transactions and database calls with tracing or APM.
- Verify collection across redeployments and explain missing telemetry.
- Measure the effects of sampling, buffering and collector failure; distinguish lost telemetry from a healthy service.

**Failure drill:** disable the telemetry collector or break exporter connectivity. Explain what diagnostics remain available locally and how you would detect a blind spot in the monitoring system itself.

**Security review:** inspect what is sent to the provider. Exclude credentials and protected data, enforce scoped ingest/API credentials and document retention and access restrictions.

## 3. Investigate latency, failure and saturation

Create a realistic performance incident in the Final Project service:

1. Introduce an intentionally slow database query or an overloaded dependency in a sandbox.
2. Generate repeatable load using a controlled load-test tool.
3. Identify the **user-facing symptom** first (error rate, request duration, availability).
4. Correlate traces, logs and metrics to isolate the failing service or operation.
5. Apply a remedy, rerun the test and document whether the symptom improved.

Distinguish **cause** from correlation: a CPU spike occurring alongside a slow endpoint does not prove CPU was the root cause. Check timing, dependency behaviour and the deployment/version context.

**Deliverable:** An investigation note recording symptom, evidence, hypothesis, diagnostic path, cause or remaining uncertainty and corrective action.

## 4. Service objectives and alerting

Define practical service-level indicators (SLIs) and objectives (SLOs), for example:
- Availability: percentage of valid requests completed successfully.
- Latency: percentage of user-relevant requests below a target duration.
- Platform workflow reliability: successful deployments or environment provisioning within an agreed service target.

Select thresholds based on the user journey and a sensible measurement window. Explain error budgets, burn rates and why a healthy infrastructure dashboard can coexist with a broken product.

**Build two alert types:**
1. A user-impacting service alert (error rate or fast SLO burn).
2. A platform/telemetry health alert (for example failed collection or high controller failure rate).

For each alert define owner, urgency, route, suppression conditions, runbook, validation method and expected action. Exercise an alert and verify the notification destination in a controlled environment. Do not route training alerts into real incident channels without permission.

## 5. Cost, governance and developer experience

High-cardinality labels (such as user IDs or raw request URLs), unbounded logs and overly aggressive tracing can make observability expensive and less useful.

**Review:**
- Cardinality, metric/tag budgets, sampling and trace retention trade-offs.
- Log ingestion, indexing/retention and reasons to retain or drop specific events.
- Environment access and data governance, especially production visibility.
- Dashboard versioning and infrastructure-as-code for monitors when supported.
- The interface offered to teams: common service tags, starter dashboards, recommended SLIs and onboarding instructions.

**Platform exercise:** Create an observability starter kit for a second demo service. Explain which fields, alerts and baseline dashboards are standard, which are configurable and how owners request exceptions. This should be a reusable **golden path**, not a custom dashboard hand-built for each team.

## Practical Assessment — investigate a degraded service

**Scenario:** A previously healthy application becomes slow after deployment, while an infrastructure component is also reporting resource pressure. Your task is to identify the actual cause, restore service and make the diagnostic path reproducible.

**Required evidence:**

1. A working telemetry pipeline with application logs, metrics and traces linked by stable service identifiers.
2. A dashboard showing user-facing availability/latency and relevant dependencies, not just host resource usage.
3. At least one load-induced or deployment-induced incident with a documented hypothesis and evidence-led resolution.
4. SLIs, SLO definitions and at least two tested, actionable monitors with routing and runbooks.
5. A privacy/cardinality/retention review explaining the expected telemetry cost drivers.
6. A reusable monitoring starter configuration suitable for another service.

**Acceptance:** A different engineer can identify the impaired service, follow the same diagnostic evidence, decide whether a rollback is justified and understand the expected alert response. Screenshots alone are insufficient without a reproducible scenario and interpretation.

## Further learning

- [Datadog — Documentation](https://docs.datadoghq.com/)
- [Datadog — APM](https://docs.datadoghq.com/tracing/)
- [OpenTelemetry — Documentation](https://opentelemetry.io/docs/)
- [Google SRE — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

**Previous:** [D06 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md) · **Next:** [Cloud Engineering overview](../3.2%20Cloud%20Engineering/CLOUD%20Overview.md)
