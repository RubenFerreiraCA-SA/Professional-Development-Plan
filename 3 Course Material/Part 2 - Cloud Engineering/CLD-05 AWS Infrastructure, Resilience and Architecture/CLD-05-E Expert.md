# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-047**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-047](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-05-E — AWS INFRASTRUCTURE, RESILIENCE AND ARCHITECTURE — EXPERT

### 1. Topic and Scope

**In scope for this level:** Evaluating architecture strategies and operational economics: availability of components in series and parallel, shared dependencies as availability caps, failure-mode analysis including gray failures, multi-AZ versus backup-and-restore, pilot light, warm standby and multi-region active-active, game days and fault injection with abort conditions, overload and graceful degradation, retry budgets, architectural governance and a limitations register.

**Out of scope:** Vocabulary (CLD-05-B), ADR and infrastructure-as-code workflow (CLD-05-I), single-service recovery runbooks and restore tests (CLD-05-P), and AWS identity and network controls (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Compute composite availability for a dependency graph with serial and parallel components and identify the shared dependency that caps it.
2. Produce a failure-mode table (mode, detection, impact, mitigation, owner) including at least one gray failure.
3. Compare backup-and-restore, pilot light, warm standby and multi-region active-active on recovery time, cost and complexity for a stated business impact.
4. Design a game day with steady-state metrics, hypothesis, blast-radius controls and abort conditions.
5. Evaluate resilience, capacity, cost and portability, then tear down trial resources with verification as required by **PRJ-048**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-05-E — AWS Infrastructure, Resilience and Architecture — Expert](../../../5%20Textbook/Master%20Textbook.md#t-cld-05-e)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Evaluate the Harbour design: compute availability numerically, build the failure-mode table, compare the four recovery strategies with costs, propose a game day, maintain a limitations register, and perform a verified teardown. Answer with numbers: "What evidence, not configuration, would you demand before believing the AZ-failure claim, and why can a second region reduce overall availability?"

**Pass criteria:** Availability figures are calculated and the cap is identified; every strategy comparison has cost and recovery numbers; the game day has abort conditions; the limitations register lists untested claims; teardown is verified by tag queries or equivalent inventory output.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-048 — Evaluate resilience and teardown** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-048).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
