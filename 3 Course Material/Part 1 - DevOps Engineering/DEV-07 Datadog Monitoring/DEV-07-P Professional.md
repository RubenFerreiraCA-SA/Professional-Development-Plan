# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-026**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-026](../../../4%20Project%20Document/Project.md#prj-001).

**Optional track:** this module belongs to the optional Datadog track (`DEV-07`, `PRJ-025` to `PRJ-028`). If your personal PDP excluded the whole Datadog track, record `DEV-07` and its project steps as **Out of scope** and continue with the next active module. If the track is active, all four levels and their steps are mandatory and ordered.

## MODULE DEV-07-P — DATADOG MONITORING — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Incident drills in Datadog (a planted regression and a blind Agent); monitors, dashboards and SLOs managed as code with Terraform; an onboarding package for other services (required tags, instrumentation, starter assets, ownership, cost rules); privacy, permissions, retention and cost review; and the decision on the telemetry path (OTLP to the Agent, vendor library, or Collector with vendor exporter). This module belongs to the optional Datadog track.

**Out of scope:** Introductory components and tagging (`DEV-07-B`), correlation and first monitors (`DEV-07-I`), and organisation-wide governance, cardinality economics and vendor strategy (`DEV-07-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Run two incident drills: a planted regression on one route (found from a dashboard, followed through traces to the slow span, correlated with logs and the deployed version, reverted and confirmed) and a blind-Agent drill showing that a user-impact monitor may stay quiet while a missing-data monitor fires.
2. Manage a monitor, a dashboard and an SLO with Terraform (`datadog_monitor` with query, thresholds, `notify_no_data`, owner tags and a runbook link), run `validate` and `plan` as a preflight with scoped application keys, and keep keys out of the repository.
3. Create an onboarding package so other services can reuse Datadog: required tags (`service`, `env`, `version`, `owner`), instrumentation and log format, dashboard/SLO/monitor templates, ownership of pages, and cost and cardinality rules.
4. Complete a privacy, permissions, retention and cost review: who can see APM and logs, API/application key scopes and rotation, personal data in logs and spans, high-cardinality tag deny-list, retention and indexing limits, an estimated monthly ingest and a cleanup owner.
5. Decide the telemetry path (OTLP to the Agent, the vendor tracing library, or the Collector with a vendor exporter), record which parts stay vendor-neutral, sampling, monitor ownership and log indexing versus archiving, and prepare the evidence for **PRJ-027**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-07-P — Datadog Monitoring — Professional](../../../5%20Textbook/Master%20Textbook.md#t-dev-07-p)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-07` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Datadog Monitoring — Professional** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Run the two drills (or document equivalent simulations) and for each state what each monitor could and could not see. Include the status transitions of the missing-data monitor.
2. Write the Terraform for one monitor and one dashboard (or SLO), including `notify_no_data`, owner tags and a runbook link. Show `terraform validate` and `plan` output, and describe how keys are supplied.
3. Write the onboarding package index (required tags, instrumentation snippet, starter templates, owners, cost rules) and a validation test that fails when `service`, `env`, `version` or `owner` is missing.
4. Complete the review table with at least eight rows (access, key scopes, personal data, deny-list tags, retention/indexing, estimated monthly ingest with its calculation, unused assets cleanup) and the evidence for each row.
5. Write the telemetry-path decision comparing the three options on vendor neutrality, effort, sampling control and cost, and state your choice.

**Pass criteria — all of the following must hold:**

- The drills show that the two monitors detect different failure classes and why.
- Terraform validates, the plan output is reviewed, the application key is scoped and no key is in Git.
- The onboarding validation test fails for an incomplete service and passes for a complete one.
- The ingest estimate shows its inputs and arithmetic, and the deny-list names at least user id and raw URL.
- The path decision includes a concrete reason to keep instrumentation vendor-neutral.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-027 — Build useful dashboards and monitors** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-027).

Evidence to record: a concise service dashboard and monitors proven to separate application incidents from missing telemetry, plus every item under *Completion criteria* on that project step. Record **PRJ-027** as **Completed** in your progress record before opening the next module (or **Out of scope** only if the whole Datadog track was excluded in your PDP).
