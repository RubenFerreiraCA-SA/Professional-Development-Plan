# T-DEV-07 — Datadog Monitoring

*Part 1 — DevOps Engineering*


This topic applies the vendor-neutral observability ideas of T-DEV-06 to a commercial platform, Datadog: its agent, tagging model, logs, application performance monitoring (APM), dashboards, service level objectives and monitors. The skills — data-path mapping, consistent tagging, correlation, governance and cost control — transfer to other vendors.

## Levels


- [Beginner Foundations](T-DEV-07-B%20Beginner.md#t-dev-07-b) — the three signals, the Datadog data path, the Agent, keys and sites, unified service tagging, a first Compose setup, ordered Agent checks, guided read-only exploration, dashboards, monitors and a sample alert interpretation.
- [Intermediate Practice](T-DEV-07-I%20Intermediate.md#t-dev-07-i) — unified service tagging applied and verified, JSON logs and pipelines, APM concepts and reading traces, service maps, monitor design, the correlation routine, and an agent and ingestion troubleshooting ladder.
- [Professional Engineering](T-DEV-07-P%20Professional.md#t-dev-07-p) — SLOs and error budgets, burn-rate monitors, monitoring as code with Terraform, ownership and tiering, cost and retention, incident workflows, and verifiable outcomes with drills and policy checks.
- [Expert Depth](T-DEV-07-E%20Expert.md#t-dev-07-e) — enterprise architecture, telemetry routing, cardinality economics, multi-team governance, reliability of the monitoring itself, and migration and scale trade-offs.

All examples use a neutral `orders-api` service (with a dependency called `inventory`); the chapter re-explains each concept where it first appears. Datadog-specific content is marked **[vendor-specific]**; details that depend on Agent, library, provider or plan versions are marked **[version-specific]** and must be confirmed against current Datadog documentation. Outputs and numbers marked *illustrative* show expected shapes, not measured results or real prices.
