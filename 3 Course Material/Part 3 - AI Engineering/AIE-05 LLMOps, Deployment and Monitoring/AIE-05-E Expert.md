# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-067**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-067](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-05-E — LLMOPS, DEPLOYMENT AND MONITORING — EXPERT

### 1. Topic and Scope

**In scope for this level:** Evaluating LLM operations, cost, governance and scaling. You compare a central gateway with direct provider calls, weigh hosted APIs against self-hosting, break cost into inputs, outputs, retries, evaluation, embeddings and storage, choose shadow, canary, A/B and version-pinned rollback techniques, and define ownership, intake, inventory, review and retirement for AI features.

**Out of scope:** Basic versioning and health reporting (`AIE-05-B`), per-service limiter and telemetry (`AIE-05-I`), SLO and runbook design for one feature (`AIE-05-P`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Argue for or against a central AI gateway for a multi-team organisation, listing the capabilities gained, the new dependency and the team needed to run it.
2. Produce a hosted-versus-self-hosted comparison covering cost, latency, data handling, accelerator capacity, cold starts and supply-chain checks on weights, and design the cheapest decisive experiment.
3. Build a unit-economics model (cost per resolved task) and rank cost levers in the order of caching, routing, context trimming and bounded retries.
4. Define how you would prove the kill switch works without an incident, and select the metrics that reveal quality drift before users complain.
5. Write an AI operating model (owners, intake with risk assessment, inventory, review cadence, retirement) that you can defend as **PRJ-068**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-05-E — LLMOps, Deployment and Monitoring — Expert](../../../5%20Textbook/Master%20Textbook.md#t-aie-05-e)

Read for: platform architecture for AI at scale, serving self-hosted models, cost engineering, managing change safely, the failure catalogue and organisational model.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write a defence document for the `ops-assistant` operating model, addressing the three textbook mentoring prompts: how to prove the kill switch works without waiting for an incident, which metrics show quality drift early, and the cheapest experiment to choose between hosted API and self-hosting. Include a cost sheet with assumptions, a change-management plan using shadow and canary, and the ownership and retirement process.

**Pass criteria:** Claims are tied to stated assumptions and evidence; the kill-switch drill is scripted and repeatable; the cost model includes evaluation and retries, not only inference; the retirement process revokes keys and deletes data.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-068 — Defend the AI operating model** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-068).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
