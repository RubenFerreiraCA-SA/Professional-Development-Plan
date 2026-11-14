# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-070**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-070](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-070](../../../4%20Project%20Document/Project.md#prj-070).

## MODULE PLT-01-P — KUBERNETES FUNDAMENTALS AND ARCHITECTURE — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing how workloads interact with a cluster and choosing environments. You decide between namespace-per-environment and cluster-per-environment, set requests and limits and predict the QoS class, reason about graceful termination and PodDisruptionBudgets, and state what a single-host kind cluster can and cannot prove.

**Out of scope:** First-time cluster creation (Intermediate), control-plane mechanics and large-scale scheduling (Expert), security policy design (PLT-03) and the Harbour configuration write-up itself (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-01--kubernetes-fundamentals-and-architecture) when this matches your current ability: *Design workload-to-cluster interactions and environment choices.* Typical starting point: You can build and break a practice cluster and now need to justify configuration decisions for dev, staging and production.

### 2. Learning Objectives

1. Choose between namespace-per-environment and cluster-per-environment for Harbour and justify the choice with isolation, cost, upgrade and blast-radius criteria.
2. Specify requests and limits for the sample service, predict its QoS class (Guaranteed, Burstable, BestEffort) and explain how missing requests affect scheduling and eviction.
3. Explain graceful termination in order (endpoint removal, `preStop`, `SIGTERM`, `terminationGracePeriodSeconds`, `SIGKILL`) and how a PodDisruptionBudget changes a node drain.
4. State exactly which claims a single-host kind cluster supports (rollouts, probes, Services) and which it cannot (zone failure, real load balancers, node hardware faults).
5. Prepare the evidence needed for **PRJ-071**: documented deployment architecture with an environment-separation decision record and an explicit list of training-cluster limits.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-01-P — Kubernetes Fundamentals and Architecture — Professional](../../../5%20Textbook/Master%20Textbook.md#t-plt-01-p) — Study graceful termination and disruption, resource policy, workload kinds and the decision guide; skim the Ingress and NetworkPolicy previews.

Optional enrichment: the "Recovery claims — what you may and may not say" passage in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Given a service with dev, staging and production needs and a laptop-only budget, write a one-page cluster configuration recommendation. Include two rejected alternatives, requests and limits with the resulting QoS class, and the termination sequence of one Pod during a rolling update.

**Pass criteria:** The decision cites explicit criteria; at least three limits of the training cluster are named; the termination order is correct; QoS class matches the stated requests and limits; every claim can be traced to a command or document.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-071 — Choose an appropriate cluster configuration** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-071).

Evidence to record: an environment-separation decision record, annotated resource settings, and a limits-of-the-training-cluster statement. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
