# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-046**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-046](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-05-P — AWS INFRASTRUCTURE, RESILIENCE AND ARCHITECTURE — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Reliable, secure infrastructure with recovery: RTO and RPO per component, failure domains and AZ headroom, recovery patterns (stateless services, immutable deploys by digest, rolling or blue/green with health gates, graceful shutdown, timeouts and retries with jitter, autoscaling limits), data protection (backups, point-in-time recovery, snapshots, replicas, multi-AZ standby and tested restores), a recovery runbook, cost and quota checks and honest ADR statements.

**Out of scope:** Vocabulary and first drills (CLD-05-B), the ADR and code workflow for a routine environment (CLD-05-I), series/parallel availability mathematics, gray-failure analysis, game days and multi-region (CLD-05-E), and AWS identity configuration (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Set RTO and RPO for the Harbour API and its data store and justify each against business impact.
2. Run a failure drill with baseline, fault, evidence and recovery, and measure recovery time against the stated RTO.
3. Differentiate backups, replicas and multi-AZ standby and state what each does and does not protect against.
4. Write a recovery runbook (symptoms, immediate checks, actions, rollback by digest, data, escalation, after) that another engineer could follow.
5. Record honest ADR statements, quota and cost effects, and the drill evidence for **PRJ-047**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-05-P — AWS Infrastructure, Resilience and Architecture — Professional](../../../5%20Textbook/Master%20Textbook.md#t-cld-05-p)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Demonstrate one failure and its recovery for the Harbour service and defend it: show the baseline, inject a task failure with desired counts of one and two, present the timestamped health probe and measured recovery time against RTO, supply the recovery runbook, and write three honest ADR sentences including what was not tested. Include a restore-time measurement or a stated reason it is out of reach.

**Pass criteria:** RTO and RPO are justified and the measured time is compared to RTO; the drill evidence is timestamped and shows the count-one versus count-two difference; the runbook is actionable; limitations are written explicitly; recovery uses code or the scheduler, not undocumented manual edits.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-047 — Demonstrate one failure and recovery** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-047).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
