# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-066**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-066](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-05-P — LLMOPS, DEPLOYMENT AND MONITORING — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing measurable, safe AI delivery and rollback. You treat prompt, model, tool-policy, corpus and parameter changes as releases with evaluation gates and staged exposure; choose signals (latency by stage, tokens and cost, outcome mix, citation and no-match rate, tool denials, feedback); set SLOs and alerts; protect content in telemetry; add timeouts, fallbacks and degradation; and write the feature runbook.

**Out of scope:** Gateway architecture, shadow mode, A/B statistics and self-hosted serving (`AIE-05-E`), the basic service and limiter (`AIE-05-I`), evaluation design (`AIE-03`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Create a change-risk table mapping prompt, model, tool-policy, corpus and parameter changes to the release practice each requires.
2. Choose the per-request signals and low-cardinality metric labels for `ops-assistant`, and say which anomaly each signal would reveal.
3. Define an availability and latency SLO for the feature and two alerts (for example no-match rate spike, cost per request anomaly) with a response action for each.
4. Specify what is logged by default (hashes, sizes, categories), when full content capture is allowed, retention and access control.
5. Write the feature runbook (disable, roll back, read dashboard, provider outage, cost spike, suspected unsafe output) and keep a simulated alert walkthrough as evidence for **PRJ-067**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-05-P — LLMOps, Deployment and Monitoring — Professional](../../../5%20Textbook/Master%20Textbook.md#t-aie-05-p)

Read for: release management for AI changes, observability signals for LLM features, resilience, security and compliance, the feature runbook and the decision guide.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Define the observability and operating design for `ops-assistant`: metrics and log schema, an SLO document, two alerts with thresholds, a data-handling table for telemetry, resilience behaviour for a provider timeout (timeout, one jittered retry, fallback message) and a runbook. Demonstrate by replaying synthetic telemetry that one alert fires and the runbook leads to disabling the feature.

**Pass criteria:** The signals separate behavioural drift from errors; telemetry contains no prompts by default; the provider-outage path degrades without blocking the core service; the alert walkthrough ends with a verified state and a new evaluation case if unsafe output was suspected.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-067 — Observe AI service quality** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-067).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
