# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-044**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-044](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-05-B — AWS INFRASTRUCTURE, RESILIENCE AND ARCHITECTURE — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Describing common AWS infrastructure components and resilience vocabulary: availability, resilience, HA, RTO, RPO, stateless versus stateful; the reference shape (load balancer across two AZs, container service with identical tasks and a scheduler, managed database, central logs); the self-healing test of stopping a task; and honest wording about what a deployment does and does not tolerate.

**Out of scope:** Architecture decision records and infrastructure-as-code changes (CLD-05-I), RTO/RPO set per component with runbooks and tested restores (CLD-05-P), availability mathematics, failure-mode analysis and multi-region patterns (CLD-05-E), and IAM or VPC configuration (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Define availability, resilience, HA, RTO and RPO and give a one-line example of each for the Harbour API.
2. Label a reference diagram (load balancer, AZs, tasks, scheduler, database, logs) and say which parts are stateless and which stateful.
3. Predict what users experience when one task stops with a desired count of one and with a desired count of two.
4. Describe the self-healing drill and the commands that list tasks, stop a task and probe health.
5. Write honest resilience statements and select the design that **PRJ-045** requires, with its limits.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-05-B — AWS Infrastructure, Resilience and Architecture — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-cld-05-b)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Choose a deployable AWS design for Harbour from at least two options and justify the choice. For three failures in your diagram (task stops, AZ unavailable, database lost) write what the user would experience, the recovery mechanism and the RTO/RPO you can honestly claim. Rewrite one overclaiming sentence ("the system is highly available") into a defensible one.

**Pass criteria:** Every failure has an experience, mechanism and honest objective; the diagram labels stateless versus stateful; the chosen design lists its limitations; no claim of HA is made without placement or test evidence.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-045 — Select a deployable AWS design** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-045).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
