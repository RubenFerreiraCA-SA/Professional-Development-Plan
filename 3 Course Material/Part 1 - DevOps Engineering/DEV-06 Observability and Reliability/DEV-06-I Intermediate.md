# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-021**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-021](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-06-I — OBSERVABILITY AND RELIABILITY — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Metrics in practice (route templates, status classes, histograms, label cardinality); logs in practice (minimum fields, diagnostic versus audit); traces in practice (spans, context propagation, sampling); an OpenTelemetry-based vendor-neutral pipeline (OTLP, Collector, resource attributes); correlating a response, a log line and a trace; and SLIs, SLOs, error budgets and a first alert.

**Out of scope:** User-journey SLO design, alert policy, incident method and telemetry governance (`DEV-06-P`), and burn-rate mathematics, sampling theory and organisational telemetry standards (`DEV-06-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Instrument request counts and errors by route template and status class, record latency as a histogram, and explain why p95 values cannot be averaged across instances and why user ids, raw URLs and request ids must not be labels (cardinality).
2. Emit logs with minimum fields (timestamp, severity, service, message, error code, trace and span ids), separating diagnostic from audit events.
3. Explain traces as trees of spans, context propagation across HTTP, and sampling (absence of a trace does not mean absence of a request), and use traces for causality and metrics for rates.
4. Configure an OpenTelemetry pipeline (SDK, OTLP, Collector) with resource attributes `service.name`, `service.version` and `deployment.environment.name`, and prove telemetry failure does not take the service down.
5. Define an SLI (ratio of good to valid events), an SLO and the error budget, compute the budget for a stated window, and write one alert with a `for` duration and a runbook link; prepare the evidence for **PRJ-022**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-06-I — Observability and Reliability — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-dev-06-i)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-06` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Observability and Reliability — Intermediate** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Show a metrics endpoint output where requests are labelled by route template and status class and latency is a histogram. Explain what would go wrong with a raw URL label.
2. Show one request followed end to end: the HTTP response (or request header), the JSON log line and the trace share a trace id. Paste the three artifacts.
3. Stop the telemetry collector while generating requests and show the service still answers and the exporter does not block the request path.
4. For a slow-dependency fault, show the trace with the long dependency span and explain why a CPU graph alone gives an incomplete diagnosis.
5. Define two SLIs, compute the error budget for a 99% SLO over 1,000 requests and over 30 days at a stated request rate, and write a Prometheus-style alert with a `for` clause and runbook annotation. Explain why eight failures in a minute may not need a page.

**Pass criteria — all of the following must hold:**

- Labels are bounded and the cardinality explanation names a cost or query consequence.
- The trace id is demonstrably identical across response, log and trace.
- The collector outage test shows the application continuing to serve requests.
- The trace-versus-CPU explanation identifies which operation or dependency was slow.
- SLI definitions use good/valid events, budget arithmetic is correct, and the page-versus-ticket reasoning refers to the budget.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-022 — Connect metrics, logs and traces** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-022).

Evidence to record: correlated telemetry for one request and a diagnosis of the responsible component in a fault, plus every item under *Completion criteria* on that project step. Record **PRJ-022** as **Completed** in your progress record before opening the next module.
