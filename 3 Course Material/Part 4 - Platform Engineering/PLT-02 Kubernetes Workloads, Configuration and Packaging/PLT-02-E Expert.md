# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-075**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-075](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-075](../../../4%20Project%20Document/Project.md#prj-075).

## MODULE PLT-02-E — KUBERNETES WORKLOADS, CONFIGURATION AND PACKAGING — EXPERT

### 1. Topic and Scope

**In scope for this level:** Evaluating workload types, packaging and lifecycle decisions. You choose between Deployment, StatefulSet, DaemonSet and Job, compare Helm, Kustomize and typed configuration languages, reason about custom resources and controllers, server-side apply field ownership, package supply-chain risk and shared-chart design for many teams.

**Out of scope:** Routine manifest writing and rollouts (Beginner to Professional), policy enforcement internals (PLT-03), and the written Harbour comparison (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-02--kubernetes-workloads-configuration-and-packaging) when this matches your current ability: *Evaluate workload types, packaging and lifecycle decisions.* Typical starting point: You can engineer reliable manifests and now need to justify which controller or packaging approach a team should adopt, and when to stop using one.

### 2. Learning Objectives

1. Choose between Deployment, StatefulSet, DaemonSet and Job for four given workloads, covering identity, storage, update ordering and failure semantics.
2. Compare Helm, Kustomize and a typed configuration approach on templating fragility, drift visibility, reviewability and learning cost, and recommend one for Harbour with caveats.
3. Explain server-side apply and field ownership, and predict the conflict when a controller, a human and a HorizontalPodAutoscaler write the same field.
4. Assess the supply-chain risk of a third-party chart (unpinned versions, hooks, privileged defaults, CRDs) and specify controls that reduce it.
5. Prepare the evidence needed for **PRJ-076**: a workload and packaging critique comparing controllers, Helm, Kustomize, stateful workloads and maintenance trade-offs.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-02-E — Kubernetes Workloads, Configuration and Packaging — Expert](../../../5%20Textbook/Master%20Textbook.md#t-plt-02-e) — Read templating pitfalls, custom resources and controllers, server-side apply, package supply chain, the failure-mode table and designing for many teams.

Optional enrichment: the mentoring prompts at the end of the same section. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** A platform team wants one shared chart for sixty services and a database. Argue for or against it, covering workload type choice, upgrade policy, escape hatches and migration cost, and name the evidence that would change your view.

**Pass criteria:** Workload types are matched to semantics; tooling trade-offs are balanced rather than tribal; failure modes and ownership conflicts are identified; a migration or rollback path is described.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-076 — Critique workload and packaging patterns** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-076).

Evidence to record: a comparison table with a recommendation, a failure-mode list and a stated upgrade and deprecation policy. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
