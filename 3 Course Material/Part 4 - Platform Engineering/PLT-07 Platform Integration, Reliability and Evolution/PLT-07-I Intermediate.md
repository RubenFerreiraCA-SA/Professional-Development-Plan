# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-093**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-093](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-093](../../../4%20Project%20Document/Project.md#prj-093).

## MODULE PLT-07-I — PLATFORM INTEGRATION, RELIABILITY AND EVOLUTION — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Connecting service-delivery components coherently. You plan an integrated demonstration on one declared runtime, define acceptance tasks, run stateful drills if state is in scope, copy backups out of the cluster and test restoring them, and write developer runbooks for someone who is not you.

**Out of scope:** Recognition of components (Beginner), failure-injection menus, game days and platform SLOs (Professional), evolution and governance (Expert), and the Harbour end-to-end journey step itself (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-07--platform-integration-reliability-and-evolution) when this matches your current ability: *Connect service delivery components coherently.* Typical starting point: You know the pieces and now need to run a change from commit to observable deployment and show it works.

### 2. Learning Objectives

1. Choose and record one runtime for the demonstration, then order the build, deploy, observe and recover outcomes you will show.
2. Write acceptance tasks (change a message, promote to staging, roll back) with a pass condition a stranger could check.
3. Run a stateful drill if database state is in scope, record the timeline and say what data could be lost.
4. Copy a database dump out of the cluster, restore it into a clean namespace and verify known rows, explaining why a backup inside the same cluster is not a backup.
5. Prepare the evidence needed for **PRJ-094**: a written path followed from a sample change to a reviewed release and an observable deployment, with timestamps and links.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-07-I — Platform Integration, Reliability and Evolution — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-plt-07-i) — Study the integrated demonstration plan, acceptance tasks, stateful drills, backups that survive the cluster and runbooks for someone who is not you.

Optional enrichment: the exercise that runs drills S1 and S2 and improves a runbook. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Make a small change, push it through review and promotion, and observe it live. Then break the deployment, recover using the runbook only, and record where the runbook was wrong or missing.

**Pass criteria:** The path is traceable from commit to running revision; the recovery follows the runbook as written; at least one runbook defect is found and fixed; evidence includes timestamps and links, not screenshots alone.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-094 — Demonstrate the end-to-end developer journey** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-094).

Evidence to record: a journey log, acceptance results, a drill timeline and a runbook diff. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
