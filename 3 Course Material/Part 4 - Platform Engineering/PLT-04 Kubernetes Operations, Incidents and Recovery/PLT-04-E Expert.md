# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-083**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-083](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-083](../../../4%20Project%20Document/Project.md#prj-083).

## MODULE PLT-04-E — KUBERNETES OPERATIONS, INCIDENTS AND RECOVERY — EXPERT

### 1. Topic and Scope

**In scope for this level:** Critiquing reliability, upgrades and operational responsibility. You design for failure domains, evaluate control-plane health signals, plan capacity with headroom, compare upgrade strategies (in-place, blue/green clusters), define disaster-recovery scenarios and objectives, and account for human factors such as on-call load.

**Out of scope:** Procedural backup and restore steps (Professional), routine diagnosis (Intermediate), vendor-specific managed-service tutorials and benchmarking you cannot reproduce locally.

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-04--kubernetes-operations-incidents-and-recovery) when this matches your current ability: *Critique reliability, upgrades and operational responsibility.* Typical starting point: You can run recoveries and now must defend an operating model against failure-domain, upgrade and organisational risks.

### 2. Learning Objectives

1. Identify the failure domains of a cluster (node, zone, control plane, network, registry, DNS, identity provider) and state which ones a given design survives.
2. Compare in-place rolling, surge, and blue/green cluster upgrades on risk, cost, rollback speed and state handling, and recommend one with preconditions.
3. Set recovery objectives for three scenarios (workload loss, namespace deletion, regional loss), state what recovery you commit to, and what evidence supports each commitment.
4. Evaluate human factors (on-call load, escalation authority, alert quality, access during an outage) and identify one failure where the documentation depends on the system that failed.
5. Prepare the evidence needed for **PRJ-084**: a defended operating and recovery strategy covering day-two work, upgrade path, recovery objectives and failure-domain assumptions.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-04-E — Kubernetes Operations, Incidents and Recovery — Expert](../../../5%20Textbook/Master%20Textbook.md#t-plt-04-e) — Read failure domains, control-plane operations, capacity and cost, upgrade strategies in depth, disaster-recovery design, the failure catalogue and human factors.

Optional enrichment: the mentoring prompts at the end of the same section. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Your only recovery documentation lives in a wiki hosted on the cluster you must recover. Redesign the operating model: where documentation and credentials live, how recovery is rehearsed, and what you would tell the business about the true recovery time.

**Pass criteria:** Single points of failure are found, including non-technical ones; objectives are justified rather than invented; the proposal distinguishes tested from assumed; trade-offs and cost are acknowledged.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-084 — Defend an operating and recovery strategy** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-084).

Evidence to record: a strategy document with a failure-domain table, recovery objectives and a rehearsal plan. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
