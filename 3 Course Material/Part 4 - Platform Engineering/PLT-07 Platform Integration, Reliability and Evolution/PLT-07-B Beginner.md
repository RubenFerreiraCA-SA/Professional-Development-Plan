# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-092**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-092](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-092](../../../4%20Project%20Document/Project.md#prj-092).

## MODULE PLT-07-B — PLATFORM INTEGRATION, RELIABILITY AND EVOLUTION — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Recognising the integrated platform. You describe the end-to-end path from repository change through build, artefact, infrastructure, deployment and telemetry, explain integration debt, ask "how would I show another person this works?" for each step, and use a first integration checklist.

**Out of scope:** Running integrated demonstrations and drills (Intermediate), reliability, cost and game days (Professional), platform evolution and governance (Expert), and the Harbour architecture-map step (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-07--platform-integration-reliability-and-evolution) when this matches your current ability: *Recognise integrated platform components and basic user flows.* Typical starting point: You have completed individual practices (Git, containers, CI, Kubernetes) but have not yet seen how they join.

### 2. Learning Objectives

1. Draw the end-to-end path for Harbour with at least seven stages (change, review, build, artefact, deploy, run, observe) and name the artefact that crosses each boundary.
2. Explain integration debt and why you get the stateless path green end to end before adding stateful components.
3. For each stage, state the one command, log line or link that proves it works, and mark any stage where you only have a claim.
4. Apply a first integration checklist to a small example service and identify the weakest seam.
5. Prepare the evidence needed for **PRJ-093**: an architecture map connecting code, build, infrastructure, deployment and telemetry with evidence links for each connection.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-07-B — Platform Integration, Reliability and Evolution — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-plt-07-b) — Read putting the pieces together, the end-to-end path, integration debt, evidence not claims and the first integration checklist.

Optional enrichment: the exercise that walks the path with a small example service. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Walk a small example service through the whole path and write, for every stage, the single command or link that proves it. Mark each stage as Proved or Claimed and explain what it would take to prove the claimed ones.

**Pass criteria:** Stages are in a defensible order; every proof is concrete and reproducible; claimed stages are admitted honestly; the weakest seam is identified with a next action.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-093 — Describe the complete learning platform** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-093).

Evidence to record: an annotated architecture map and an evidence index with Proved or Claimed status per connection. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
