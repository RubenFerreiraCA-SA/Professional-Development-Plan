# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-071**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-071](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-071](../../../4%20Project%20Document/Project.md#prj-071).

## MODULE PLT-01-E — KUBERNETES FUNDAMENTALS AND ARCHITECTURE — EXPERT

### 1. Topic and Scope

**In scope for this level:** Critiquing Kubernetes architecture and its constraints. You narrate the full request path from `kubectl apply` through authentication, authorisation, admission and etcd to kubelet, predict failure signatures, compare cluster topologies (single shared, per-environment, per-team), analyse scheduling constraints, and treat API versions as dependencies.

**Out of scope:** Basic component naming (Beginner), first-time cluster operation (Intermediate), routine environment configuration (Professional) and production-scale benchmarking you cannot reproduce on a training machine.

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-01--kubernetes-fundamentals-and-architecture) when this matches your current ability: *Evaluate Kubernetes architecture, scalability and constraints.* Typical starting point: You can configure clusters and want to defend design choices and predict how they fail under scale or disruption.

### 2. Learning Objectives

1. Narrate in order what happens between `kubectl apply` of a Deployment and a ready Pod, naming API server stages, the etcd write, controller reconciliation, scheduling and kubelet actions.
2. Predict the observable signature (events, status, metrics) of four faults: an unschedulable Pod caused by a taint, `ImagePullBackOff`, `CrashLoopBackOff` from a failing liveness probe, and a `NotReady` node.
3. Compare a shared multi-tenant cluster, cluster-per-environment and cluster-per-team against blast radius, cost, upgrade effort and policy complexity, and recommend one with stated assumptions.
4. Assess scheduling constraints (requests, topology spread, taints and tolerations, PodDisruptionBudgets) and describe what each would do during a zone loss, noting what cannot be tested on a training cluster.
5. Prepare the evidence needed for **PRJ-072**: a written critique covering scheduling, control plane, security and scale limits with a ranked risk list and explicit assumptions.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-01-E — Kubernetes Fundamentals and Architecture — Expert](../../../5%20Textbook/Master%20Textbook.md#t-plt-01-e) — Read control-plane mechanics, understanding rollouts precisely, the failure-signature table, scheduling at scale, cluster design choices and API evolution.

Optional enrichment: the mentoring prompts at the end of the same section. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Defend a cluster design for forty services owned by six teams against challenge questions on blast radius, upgrade sequencing and API deprecation. Include a failure-signature table for four faults and one decision you would revisit at ten times the scale.

**Pass criteria:** The request path is correct and ordered; each fault has a distinguishing signature; alternatives are rejected with reasons; limits of untestable claims are stated; a less experienced engineer could follow the explanation.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-072 — Critique cluster design trade-offs** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-072).

Evidence to record: a design critique with a ranked risk register, a failure-signature table and a list of assumptions that cannot be verified locally. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
