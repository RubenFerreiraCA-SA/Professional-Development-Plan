# T-DEV-06 — Observability and Reliability

*Part 1 — DevOps Engineering*


Observability is the ability to ask new questions about a running system from its outputs. Reliability work turns that ability into explicit targets (service level objectives), alerts worth waking someone for and investigations that follow evidence.

## Levels


- [Beginner Foundations](T-DEV-06-B%20Beginner.md#t-dev-06-b) — logs, metrics and traces from first principles, the limits of monitoring, the request path, golden signals, a basic dashboard, an annotated investigation, common mistakes.
- [Intermediate Practice](T-DEV-06-I%20Intermediate.md#t-dev-06-i) — structured logs, trace and span anatomy, OpenTelemetry concepts, metric types and label cardinality, dashboards, alerts and routing, a typical incident diagnosed from queries.
- [Professional Engineering](T-DEV-06-P%20Professional.md#t-dev-06-p) — SLIs and SLOs, error budgets, burn rates, paging versus tickets, incident response, postmortems, telemetry as a platform product, worked calculations.
- [Expert Depth](T-DEV-06-E%20Expert.md#t-dev-06-e) — sampling and cardinality economics, incomplete telemetry, gray failures, noisy alerts, reliability programmes, high-stakes decisions, a case catalogue and expert trade-offs.

All examples use a neutral `orders-api` service; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.
