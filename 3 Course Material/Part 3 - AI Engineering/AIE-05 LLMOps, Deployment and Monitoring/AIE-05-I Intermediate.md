# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-065**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-065](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-05-I — LLMOPS, DEPLOYMENT AND MONITORING — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Running and troubleshooting a simple AI feature lifecycle. You expose the assistant as a separate service with the request path enabled check, validation and limits, retrieval, model call, response validation and sanitised telemetry; set token, rate and length limits with distinct error codes; script disable-and-rollback with a safe PID check; and test the integrated path offline.

**Out of scope:** Staged rollouts, SLOs, resilience patterns and runbook design (`AIE-05-P`), gateways, shadow mode and self-hosting (`AIE-05-E`), CI platform configuration, and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Describe the request path from enabled check to returned structured result, naming where each failure produces a distinct status code.
2. Configure input, output, rate and budget limits and show 400 and 429 responses with reason codes such as `question_too_long`, `rate_limited` and `budget_exceeded`.
3. Write a kill-and-rollback procedure that verifies the PID belongs to the assistant, stops it, waits, and confirms core service health, and explain why `pkill -f` is unsafe.
4. Emit one sanitised telemetry line per request containing latency, tokens, bundle version, model id, enabled state, tool denials and outcome category.
5. Write an offline integration test for the disabled path and the limiter, and use real-path output as the evidence for **PRJ-066**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-05-I — LLMOps, Deployment and Monitoring — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-aie-05-i)

Read for: serving the feature as a small HTTP service, the request path, limits that protect cost and safety, the kill-switch and rollback script, monitoring hooks and testing the integrated path.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write the deployment and rollback description for `ops-assistant` as a service: request-path diagram, limits table, version bundle to deploy, the previous bundle to roll back to, the kill-and-rollback script and a verification checklist. Provide telemetry lines produced by real requests (answered, refused, limited, disabled) from a local run using the fake model.

**Pass criteria:** Rollback restores the previous bundle and is verified by health and a test request; telemetry comes through the real request path rather than a helper call; the script avoids broad process matching; no raw questions or secrets are logged.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-066 — Describe a deployment and rollback** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-066).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
