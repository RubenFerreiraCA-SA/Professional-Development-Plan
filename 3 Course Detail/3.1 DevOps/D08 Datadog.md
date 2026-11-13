# D08 — Datadog

| | Details |
| --- | --- |
| **Estimated study time** | 24–36 hours |
| **Prerequisites** | [D07 — Observability](D07%20Observability.md), the instrumented Final Project application, familiarity with container/Kubernetes diagnostics, and access to an authorised Datadog account or suitable training environment. |

## Objective

Turn the observability principles established in D07 into an **operational, reusable monitoring service in Datadog**. Implement ingestion, application performance monitoring, dashboards, service-level objectives and alert routing; then demonstrate that another engineering team can diagnose an incident through a supported, secure and cost-conscious platform interface.

Datadog is the specific tool for this module. The concepts behind each exercise—instrumentation, telemetry correlation, reliable alerting and governance—remain transferable to other products.

## Outcomes

1. Explain Datadog's telemetry architecture: agents, integrations, ingestion, indexing, APM, monitoring and access boundaries.
2. Deploy and maintain the Datadog Agent in a container or Kubernetes environment with the minimum necessary privileges.
3. Configure metrics, structured logs and distributed tracing with consistent service/environment/version attribution.
4. Build dashboards that express user experience, service dependencies and deployment context rather than just host resources.
5. Implement, test and maintain SLOs, monitors, routing and response runbooks.
6. Investigate latency, failed deployments and collector blind spots using correlated Datadog evidence.
7. Provision observability configuration as code where appropriate and create an onboarding pattern for new services.
8. Assess access control, sensitive data, tag cardinality, log retention, telemetry volume and the recurring cost of operating the service.

## 1. Datadog architecture and setup

Map the path from the application's existing OpenTelemetry instrumentation to Datadog:

- Agent or collector responsibilities versus SDK/library instrumentation.
- Infrastructure metrics, container/Kubernetes integration, log collection and APM traces.
- `service`, `env` and `version` tags and the relationship to resource attributes and Unified Service Tagging.
- Data ingestion versus log indexing, queryable trace retention and metric-series cardinality.
- Account/site configuration, API and application keys, credential scoping and role-based access.

**Architecture exercise:** Choose an instrumentation/export route. You may use Datadog's SDK/instrumentation, supported OpenTelemetry export, or a combination; document any functionality or sampling differences. Keep credentials in a local secret store, protected platform secret or supported workload identity mechanism—not the repository.

**Lab:** Configure an isolated Datadog environment and deploy its Agent to the Final Project's sandbox (Compose, a host or Kubernetes as appropriate). Capture agent health and effective collection configuration. Use only non-sensitive demo data and verify costs/plan restrictions before enabling ingestion.

## 2. Infrastructure and container monitoring

Implement baseline monitoring for CPU/memory pressure, container restarts, network errors, database health and application readiness.

- Install the integration using the least access required; review host mounts, socket permissions and container capabilities.
- Ensure service names, environments and deployment versions are stable and consistent.
- Trace an infrastructure alert back to the affected workload; distinguish pod replacement, OOM termination, node pressure and application exceptions.
- Confirm what remains visible after the Agent or collector stops reporting.

**Failure drills:** Force a memory-limit termination in a sandbox, then interrupt the collector. Compare what Datadog reports and what the workload's own logs and runtime events report. Document delays and telemetry gaps.

**Evidence:** an infrastructure dashboard, a reproducible failure and an explanation of how tagging enables service-level investigation.

## 3. Logs and APM implementation

Use the instrumented API/database path from D07 and configure Datadog APM and structured log ingestion.

**Instrumentation contract:**
- Service, environment, version and operation names are stable.
- Requests propagate trace context across a service or queue boundary.
- Database/dependency spans reveal latency and errors.
- Logs contain trace correlation identifiers without exposing user payloads or credentials.
- Useful error classifications and response codes are distinguishable from expected failures.

**Lab:** Generate successful, failed and slow requests. Navigate from an affected service to a trace, from the trace to the dependency span and from the span to matching log entries. Confirm that trace/log correlation continues after deploying a different application version.

**Failure exercise:** Break context propagation deliberately; investigate the missing relationship and fix it. Compare a sampled trace view with aggregate request-rate/error metrics to avoid interpreting trace sampling as total request counts.

**Governance:** Configure suitable log exclusion/retention rules, test sensitive-field masking and explain whether a given log is indexed, stored or discarded.

## 4. Dashboards, SLOs and actionable monitors

Build a service dashboard covering:

- Request traffic, error rate and latency.
- Application version and recent deployment indicators.
- Important dependencies, queue/database behaviour and resource pressure.
- SLI progress relative to an agreed SLO and known telemetry gaps.

Implement at least **two monitors**:

1. A customer-impact monitor driven by error rate, latency or an SLO burn-rate strategy appropriate to available Datadog features.
2. A platform/telemetry monitor detecting missing agents, stalled collection or infrastructure failures that affect investigation.

For each monitor provide the actual query/configuration, thresholds, severity, owner, notification route, runbook URL, missing-data handling and a controlled validation test.

**Design review:** Compare alerts based on raw resource thresholds with alerts tied to user impact. Demonstrate one noisy threshold and refine it using appropriate evaluation windows, grouping, suppression or routing. Avoid sending test alerts to genuine on-call channels without permission.

## 5. Incident response in Datadog

**Scenario:** A new release increases HTTP latency while container CPU also rises. A failing database operation and an unrelated worker process are competing explanations.

Investigate entirely in a sandbox:

1. Define the user-facing incident and establish its time window.
2. Use Datadog service views, APM traces, logs, dependency metrics, dashboards and deployment/version tags to evaluate competing hypotheses.
3. Identify the evidence that distinguishes the true regression from coincidental load.
4. Apply and document a mitigation (safe rollback, configuration correction, database improvement or controlled traffic reduction).
5. Re-run the original test and verify recovery against the D07 SLI, not only a green infrastructure indicator.
6. Write a concise incident note with timeline, root cause or uncertainty, monitoring gaps, follow-up work and runbook updates.

**Second drill:** Stop the Agent or exporter while the application stays healthy. Show how to recognise this as a loss of visibility rather than silently reporting a healthy service.

## 6. Datadog as a reusable platform service

Use Terraform's Datadog provider or an approved configuration-as-code mechanism for at least part of the setup—such as a dashboard, monitors or SLOs. Protect credentials and review changes as you would for application infrastructure.

Create an onboarding package for another demo service:

- A service-tagging and tracing convention with documented exceptions.
- Recommended instrumentation, log schema and baseline metrics.
- A starter dashboard and monitor set that can be parameterised by service and environment.
- On-call ownership, notification routing, troubleshooting entry points and runbook templates.
- Access controls for service owners and central platform operators.
- Controls for retention, sampling, high-cardinality dimensions, unused dashboards and spend.

**Practical exercise:** Onboard a second small service from the package. Record which steps were self-service, which required platform intervention and what should be automated next.

## Practical Assessment — operate the observability platform

**Scenario:** Two application teams share the Datadog monitoring service. One experiences a real application regression; the other loses telemetry. Demonstrate that the platform distinguishes these conditions and supports a proportionate response.

**Required evidence:**

1. A documented Agent/collector installation with working infrastructure, log and APM ingestion.
2. Correlated request traces, structured logs, service versions and dependency metrics for the Final Project application.
3. A user-centric dashboard plus SLI/SLO configuration representing actual service objectives.
4. Two tested monitors with actionable routes, ownership and runbooks, including missing-telemetry behaviour.
5. Reproducible application degradation with evidence-led diagnosis, mitigation and recovery.
6. Reproducible telemetry pipeline failure and a documented response.
7. A version-controlled onboarding/configuration package applied to a second service.
8. A privacy, permissions, retention and cost review with explicit controls or recorded provider limitations.

**Acceptance:** Another engineer can follow the recorded Datadog evidence to diagnose the regression, recognise a collector blind spot and onboard an additional service without relying on undocumented expertise. A dashboard screenshot alone is insufficient.

## Further learning

- [Datadog Documentation](https://docs.datadoghq.com/)
- [Datadog Agent](https://docs.datadoghq.com/agent/)
- [Datadog APM](https://docs.datadoghq.com/tracing/)
- [Datadog Unified Service Tagging](https://docs.datadoghq.com/getting_started/tagging/unified_service_tagging/)
- [Datadog SLOs](https://docs.datadoghq.com/service_management/service_level_objectives/)
- [Datadog Terraform Provider](https://registry.terraform.io/providers/DataDog/datadog/latest/docs)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)

**Textbook:** [Chapter 8 — Datadog](../../4%20Study%20Materials/4.1%20DevOps/D08%20Datadog.md)

**Previous:** [D07 — Observability](D07%20Observability.md) · **Next:** [Cloud Engineering overview](../3.2%20Cloud%20Engineering/CLOUD%20Overview.md)
