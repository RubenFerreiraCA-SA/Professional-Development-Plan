# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-074**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-074](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-074](../../../4%20Project%20Document/Project.md#prj-074).

## MODULE PLT-02-P — KUBERNETES WORKLOADS, CONFIGURATION AND PACKAGING — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Engineering reliable, secure manifests and deployment patterns. You design rolling-update settings (`maxSurge`, `maxUnavailable`), PodDisruptionBudgets, topology spread, `securityContext` and resource policy, gate manifests with `helm lint`, `kubeconform` and `kubectl diff`, apply the one-owner rule, and rehearse a controlled failure and rollback from version-controlled manifests.

**Out of scope:** First-time manifest authoring (Intermediate), critique of templating languages and operators (Expert), cluster-wide admission policy (PLT-03) and the Harbour rollout demonstration steps (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-02--kubernetes-workloads-configuration-and-packaging) when this matches your current ability: *Engineer reliable, secure manifests and deployment patterns.* Typical starting point: You can ship a working Deployment and now need to prove it survives rollout, disruption and drift.

### 2. Learning Objectives

1. Choose `maxSurge`, `maxUnavailable`, replica count and a PodDisruptionBudget so that a rolling update and a node drain keep a defined number of Pods available.
2. Harden a Deployment with `securityContext` (non-root, read-only root filesystem, dropped capabilities), resource requests and limits, and explain which failure each setting prevents.
3. Build a manifest quality gate using `helm lint` or `kubectl kustomize`, schema validation (`kubeconform`) and `kubectl diff`, and say what each stage catches and misses.
4. Apply the one-owner rule to a release so a controller, a human and an autoscaler do not fight over the same fields, and explain how drift would be detected.
5. Prepare the evidence needed for **PRJ-075**: version-controlled manifests deployed from Git, a controlled failure (bad image or failing probe), recovery by rollback, and the timeline.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-02-P — Kubernetes Workloads, Configuration and Packaging — Professional](../../../5%20Textbook/Master%20Textbook.md#t-plt-02-p) — Read packaging as a platform API, quality gates for manifests, ownership and drift, chart upgrade policy, configuration management rules and the decision guide.

Optional enrichment: the autoscaling-in-production notes and the chart compatibility policy in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Present a Deployment, PodDisruptionBudget and manifest gate for a stateless service. Predict the outcome of a bad-image rollout and a node drain, run both on a practice cluster, and explain any difference between prediction and result.

**Pass criteria:** Settings keep the stated availability during both events; the quality gate rejects at least one deliberately broken manifest; ownership of each object is named; the recovery is shown from a recorded revision, not by manual patching.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-075 — Demonstrate rollout and workload resilience** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-075).

Evidence to record: gated manifests in Git, a failure-and-recovery timeline with `kubectl rollout` output, and a drift or ownership note. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
