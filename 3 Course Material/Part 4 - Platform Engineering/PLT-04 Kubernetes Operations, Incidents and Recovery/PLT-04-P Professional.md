# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-082**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-082](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-082](../../../4%20Project%20Document/Project.md#prj-082).

## MODULE PLT-04-P — KUBERNETES OPERATIONS, INCIDENTS AND RECOVERY — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing response, backup and recovery procedures. You define recovery levels and claim only what you proved, design backup and restore for state, plan upgrades, set an operating cadence, write runbooks for someone who is not you, and structure incident roles and timelines.

**Out of scope:** Routine fault diagnosis (Intermediate), capacity, failure-domain and disaster-recovery strategy at scale (Expert), and the Harbour stateful recovery scenario itself (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-04--kubernetes-operations-incidents-and-recovery) when this matches your current ability: *Design response, backup and recovery procedures.* Typical starting point: You can fix outages and now need to prove you can recover data and run the cluster repeatably.

### 2. Learning Objectives

1. Classify recovery claims into levels (workload restart, namespace rebuild, data restore, cluster rebuild) and state which one your demonstration actually proves.
2. Design a backup and restore procedure for a stateful dependency (logical dump copied out of the cluster, volume snapshot or Velero) with its recovery point and recovery time assumptions.
3. Plan a Kubernetes upgrade (read release notes, check deprecated APIs, upgrade control plane then nodes, verify, roll back or roll forward) and list the checks before and after each stage.
4. Write a runbook with trigger, impact, first checks, decision points, mitigation, verification and escalation that a second person can follow.
5. Prepare the evidence needed for **PRJ-083**: a bounded backup-and-restore or incident-recovery scenario with explicit data-loss limitations and measured recovery time.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-04-P — Kubernetes Operations, Incidents and Recovery — Professional](../../../5%20Textbook/Master%20Textbook.md#t-plt-04-p) — Study recovery levels, backup and restore design, upgrades, the operating cadence, the runbook skeleton, incident management and the decision guide.

Optional enrichment: the etcd snapshot section from the Intermediate chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Back up a small stateful service, delete the namespace, restore, and record time-to-recover and the data written after the backup that was lost. Then write the runbook you used and have a second reader mark where it was unclear.

**Pass criteria:** The restore is verified by reading back known data; data loss is quantified honestly; the recovery level claimed matches what was tested; the runbook is usable by someone who was not present.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-083 — Recover a stateful or operational failure** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-083).

Evidence to record: backup and restore transcripts, measured timings, a data-loss statement and the runbook. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
