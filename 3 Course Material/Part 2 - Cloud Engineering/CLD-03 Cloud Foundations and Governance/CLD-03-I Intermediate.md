# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-037**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-037](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-03-I — CLOUD FOUNDATIONS AND GOVERNANCE — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Foundational account design and service choice: root user versus human identity versus workload role, budgets and idle policy created before any network or compute, a consistent tag set (`Project`, `Owner`, `Environment`, `ExpiryDate`), the foundational services map (compute, registry, data, edge, DNS, logs, workload identity), writing a landing-zone ADR and an ordered teardown policy.

**Out of scope:** Cloud definitions and responsibility basics (CLD-03-B), multi-account organisation policy, compliance evidence and cost engineering (CLD-03-P), operating models, auto-remediation risks and exit costs (CLD-03-E), and AWS CLI mechanics (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Compare managed and self-run options for the Harbour API, database, registry, edge and logs on operational burden, cost and portability, and select with a recorded rationale.
2. Define three identity classes (root, human, workload) and state the rules that apply to each, including MFA and the absence of long-lived keys.
3. Write cost guardrails with a monthly budget, alert thresholds, a notification owner, an idle policy and a list of forbidden-by-default items.
4. Specify a minimal mandatory tag set and explain what each tag enables (cost reports, cleanup, ownership).
5. Write an ordered teardown runbook and a landing-zone ADR whose evidence feeds **PRJ-038**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-03-I — Cloud Foundations and Governance — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-cld-03-i)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write the four foundation documents for a Harbour training account, each under one page: identity baseline, cost guardrails, services map and teardown runbook. Add a comparison table of at least two options for each service with a decision and the reason. State what must never be deleted during teardown.

**Pass criteria:** Every service choice has at least two compared options and a justified decision; guardrails contain concrete numbers, an owner and an idle policy; teardown is ordered (runtime, network, data, then identity and state last) and lists protected items; no document relies on an administrator key stored on disk.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-038 — Evaluate service and responsibility choices** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-038).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
