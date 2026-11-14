# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-039**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-039](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-03-E — CLOUD FOUNDATIONS AND GOVERNANCE — EXPERT

### 1. Topic and Scope

**In scope for this level:** Critiquing cloud trade-offs and operating models at scale: a landing zone as a product (account vending, baselines, support model), preventive versus detective versus corrective controls and the exception path, failure modes of governance (policy sprawl, shadow accounts, break-glass abuse, orphaned resources, concentration risk), provider-level blast-radius boundaries, RTO/RPO-driven resilience decisions, and cost as an architectural property (unit cost, lock-in and exit cost).

**Out of scope:** Cloud basics (CLD-03-B), account baseline documents (CLD-03-I), single-organisation governance and cost engineering mechanics (CLD-03-P), and the AWS implementation of IAM and VPC (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Choose and defend the first three organisation-level guardrails for a landing zone, with an exception process that has owners and expiry.
2. Compare account-per-environment with account-per-team using blast radius, cost attribution and operational overhead.
3. Analyse governance failure modes (policy sprawl, shadow accounts, break-glass abuse, orphaned resources) and propose a measurable defence for each.
4. Justify or reject multi-region for a workload using RTO, RPO, business impact and hidden shared dependencies, not preference.
5. Evaluate unit cost and exit cost of a design and record the defended constraint set required by **PRJ-040**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-03-E — Cloud Foundations and Governance — Expert](../../../5%20Textbook/Master%20Textbook.md#t-cld-03-e)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write and defend an architecture-constraints paper for Harbour: the top three guardrails and their exception path, a blast-radius analysis from AZ to provider, a numeric case for or against multi-region (RTO, RPO, cost), a unit-cost estimate and a lock-in exit estimate. Answer in writing: "What would convince you that your landing zone is used rather than merely documented?"

**Pass criteria:** Constraints are traceable to a risk or objective; numbers (availability, cost, RTO/RPO) are computed and shown; at least one constraint is argued against and a reason is given for keeping it; usage evidence for the landing zone is a measurable signal, not a document.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-040 — Defend architecture constraints** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-040).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
