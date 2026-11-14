# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-063**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-063](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-04-E — AGENTS, TOOLS AND ORCHESTRATION — EXPERT

### 1. Topic and Scope

**In scope for this level:** Evaluating autonomous workflow risk and reliability. You enumerate assets, actors and entry points, name attack classes (direct and indirect injection, confused deputy, tool poisoning, exfiltration, excessive agency, memory poisoning), break at least one leg of the private-data / untrusted-content / outbound-action combination, evaluate trajectories and safety violations over many trials, and define autonomy levels with owners and sign-off.

**Out of scope:** Basic dispatcher and allow-list implementation (`AIE-04-B`, `AIE-04-I`), single-tool approval design (`AIE-04-P`), platform gateways and cost governance (`AIE-05-E`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Produce a threat model for a ticket-triage agent listing assets, actors, entry points and the attack classes that apply to each.
2. Apply the dangerous-combination test to the agent and justify which leg you remove first.
3. Design a trajectory evaluation with seeded faults, many trials and metrics for success rate, steps, cost per task and safety violations.
4. Define autonomy levels (suggest only, act with approval, act within limits, act in a sandbox) per tool and the sign-off required to raise a level.
5. Describe what a replayable trace must contain, and record a defended autonomy recommendation as **PRJ-064**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-04-E — Agents, Tools and Orchestration — Expert](../../../5%20Textbook/Master%20Textbook.md#t-aie-04-e)

Read for: threat modelling an agent, the dangerous combination of capabilities, protocol and ecosystem risk, reliability of long-running agents, evaluating trajectories, governance for autonomy and the failure catalogue.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write an autonomy evaluation for a hypothetical agent that triages support tickets and can read a ticket queue, search runbooks and draft replies. Include the threat model, the leg you would remove first and why, the autonomy level you would grant each tool, a simulated trajectory test plan with seeded faults, and answers to the textbook mentoring prompts, including how to give an agent a destructive tool safely and who must be in the loop.

**Pass criteria:** The threat model is specific to the agent, not generic; the chosen control removes capability instead of relying on instructions; the test plan states trials and metrics; the recommendation records who owns the agent and how an incident is handled.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-064 — Evaluate agent autonomy** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-064).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
