# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-025**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-025](../../../4%20Project%20Document/Project.md#prj-001).

**Optional track:** this module belongs to the optional Datadog track (`DEV-07`, `PRJ-025` to `PRJ-028`). If your personal PDP excluded the whole Datadog track, record `DEV-07` and its project steps as **Out of scope** and continue with the next active module. If the track is active, all four levels and their steps are mandatory and ordered.

## MODULE DEV-07-I — DATADOG MONITORING — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Infrastructure and container baseline monitoring; logs, APM and log-trace correlation (including breaking and restoring propagation); sampling honesty; log governance (exclusion filters, scrubbing, retention); user-centric dashboards, SLOs and two validated monitors (user impact and missing telemetry); refining noisy monitors; and troubleshooting. This module belongs to the optional Datadog track.

**Out of scope:** Monitors as code, incident drills, onboarding packages and privacy/cost review (`DEV-07-P`), and cardinality economics, ingestion strategy, monitoring reliability and vendor strategy (`DEV-07-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Set up an infrastructure and container baseline (host CPU, memory, disk and network, per-container CPU/memory and restarts) and separate memory pressure from an application exception by comparing memory graphs with error rates and logs.
2. Produce JSON logs carrying trace and span ids, configure the trace-id remapper, and verify correlation in both directions (trace → logs and log → trace); break propagation on purpose and restore it.
3. Compare APM trace counts with a request-count metric to show sampling effects, and explain why missing traces do not mean zero traffic.
4. Apply log governance: exclusion filters or no indexing for noisy health checks, scrubbing of sensitive fields (`password`, `token`, `authorization`), and a record of retention differences between indexed logs and archives.
5. Build a user-centric dashboard, an SLO from an SLI, and two monitors (user impact and missing telemetry) validated by inducing each condition and observing the transitions OK → Alert → OK and OK → No Data → OK; refine one noisy monitor; prepare the evidence for **PRJ-026**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-07-I — Datadog Monitoring — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-dev-07-i)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-07` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Datadog Monitoring — Intermediate** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Show two graphs side by side for the same period: container memory approaching its limit and error rate. Explain which pattern indicates memory pressure and which an application exception.
2. Show a trace with its linked logs and a log with its linked trace. Then remove the trace id from the log format, show the link breaks, and restore it.
3. During a counted loop of 200 requests compare the number of traces you can find with the request-count metric and explain the difference.
4. Show a log exclusion filter for health checks and a scrubbing rule. Produce a log containing a fake password field and show it redacted.
5. Create an error-ratio monitor and a no-data monitor, induce each condition, and paste the status transitions. Then show a deliberately noisy monitor (for example CPU above 5%), the flapping, and the fixed query with before and after.

**Pass criteria — all of the following must hold:**

- The memory-versus-exception reasoning uses both graphs and logs, not one metric.
- Correlation works in both directions and the induced break is observable.
- The sampling explanation distinguishes trace sampling from metric counts.
- Sensitive values are redacted in a tested example, not simply stated as redacted.
- Both monitors show observed transitions, and the noisy monitor's fix reduces flapping with before/after evidence.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-026 — Correlate operational evidence** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-026).

Evidence to record: a view or query that connects service health, logs and APM traces, or an equivalent documented walk-through, plus every item under *Completion criteria* on that project step. Record **PRJ-026** as **Completed** in your progress record before opening the next module (or **Out of scope** only if the whole Datadog track was excluded in your PDP).
