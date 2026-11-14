# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-027**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-027](../../../4%20Project%20Document/Project.md#prj-001).

**Optional track:** this module belongs to the optional Datadog track (`DEV-07`, `PRJ-025` to `PRJ-028`). If your personal PDP excluded the whole Datadog track, record `DEV-07` and its project steps as **Out of scope** and continue with the next active module. If the track is active, all four levels and their steps are mandatory and ordered.

## MODULE DEV-07-E — DATADOG MONITORING — EXPERT

### 1. Topic and Scope

**In scope for this level:** Enterprise onboarding, governance, pricing and portability: governance models for tags, monitors and dashboards; cardinality and cost economics enforced at code review, Agent/Collector and backend; sampling, ingestion controls and retention trade-offs; reliability of the monitoring system itself; and vendor strategy (OpenTelemetry and Collector abstraction, exportable definitions, evaluation criteria). This module belongs to the optional Datadog track.

**Out of scope:** Introductory terminology, first correlation, dashboards and monitors, and a single service's onboarding package (`DEV-07-B`, `DEV-07-I`, `DEV-07-P`); implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Design a governance model: how many tags and which values a team may add, who may create paging monitors and who reviews them, how duplicate dashboards are prevented, and what the platform team supplies versus what service teams own, with periodic cleanup reviews.
2. Quantify cardinality and cost (custom metrics billed by unique tag combinations) and enforce limits at three points: code review and libraries, the Agent or Collector, and backend allow-lists and quotas, with cost per service surfaced to owners.
3. Decide per service what to keep (all errors, all slow traces, a low percentage of normal traces), distinguish indexed from archived data, and document what cannot be answered after retention expires.
4. Design for the reliability of monitoring itself: Agent crash, key revocation, network partition, intake outage, clock skew and tag drift, mitigated by a service heartbeat metric, a missing-data monitor, a secondary notification path and a tested "monitoring is down" runbook.
5. Set vendor strategy: standardise on OpenTelemetry and a Collector layer, treat proprietary features as value-added with a conscious switching cost, keep monitor and dashboard definitions as code, and evaluate vendors on query power, retention cost, cardinality handling, support, data residency and security attestations.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-07-E — Datadog Monitoring — Expert](../../../5%20Textbook/Master%20Textbook.md#t-dev-07-e)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-07` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Datadog Monitoring — Expert** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Draft a governance model (one to two pages) covering tag policy, monitor and dashboard ownership, review rules for paging monitors, cleanup cadence and what the platform provides by default.
2. Estimate the monthly cost impact of adding one unbounded tag (for example user id) to a metric: state the assumptions and arithmetic, and describe where you would stop it at each of the three enforcement points.
3. Write a sampling and retention policy for three service classes (critical, standard, batch): what is kept, what is indexed, what is archived and what questions become unanswerable.
4. Write the ordered checks for "Datadog shows no data" from the application to the backend, and the design (heartbeat, secondary path, runbook) that detects monitoring failure itself.
5. Write a vendor evaluation matrix with at least six criteria and an exit plan listing what is portable (OpenTelemetry, Collector, definitions as code) and what is not.

**Pass criteria — all of the following must hold:**

- The governance model assigns owners and review rules, and includes a mechanism that deletes unused assets.
- The cost estimate shows assumptions and multiplication, and each enforcement point names a concrete control.
- The retention policy states the loss of answerable questions honestly.
- The no-data checks are ordered by data path and include key/site, Agent, network, tags and monitor query; the design includes a path that does not depend on the monitored platform.
- The exit plan lists specific portable assets and the realistic cost of leaving proprietary features.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-028 — Publish a reusable onboarding method** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-028).

Evidence to record: the onboarding method, the cost/cardinality/privacy assessment and a vendor lock-in analysis, plus every item under *Completion criteria* on that project step. Record **PRJ-028** as **Completed** in your progress record before opening the next module (or **Out of scope** only if the whole Datadog track was excluded in your PDP).
