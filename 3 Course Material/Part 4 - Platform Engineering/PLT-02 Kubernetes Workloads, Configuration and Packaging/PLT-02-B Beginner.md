# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-072**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-072](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-072](../../../4%20Project%20Document/Project.md#prj-072).

## MODULE PLT-02-B — KUBERNETES WORKLOADS, CONFIGURATION AND PACKAGING — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Reading and describing the core workload and configuration objects for a simple service: Pod, ReplicaSet, Deployment, ClusterIP Service, labels and selectors, ConfigMaps and Secrets (as environment variables and mounted files), liveness, readiness and startup probes, and resource requests. Helm and Kustomize are named only as packaging tools.

**Out of scope:** Writing tuned probes and rollouts (Intermediate), PodDisruptionBudgets and quality gates (Professional), StatefulSets, operators and chart design (Expert), and the Harbour workload write-up itself (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-02--kubernetes-workloads-configuration-and-packaging) when this matches your current ability: *Explain Pods, Deployments, Services and basic config.* Typical starting point: You can run a container but cannot yet read a Deployment manifest line by line or say what a probe does.

### 2. Learning Objectives

1. Read a Deployment manifest and explain `replicas`, `selector`, `template`, `image` and `ports`, including why the selector must match the Pod template labels.
2. Explain how a ClusterIP Service selects Pods through labels and why Pod IP addresses must never be hard-coded.
3. Distinguish ConfigMap from Secret, show two ways to consume each (environment variable and mounted file), and explain why base64 encoding is not encryption.
4. Describe what liveness, readiness and startup probes each ask and what Kubernetes does when each one fails.
5. Prepare the evidence needed for **PRJ-073**: an annotated Pod, Deployment and Service description for the Harbour sample workload with each field's purpose stated.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-02-B — Kubernetes Workloads, Configuration and Packaging — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-plt-02-b) — Read the packaging-motivation material alongside the Kustomize and Helm miniatures to see the same Deployment, Service and ConfigMap rendered both ways.

Optional enrichment: the "One owner rule" note and the probe and configuration discussion in the Intermediate chapter of PLT-01. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Given an unannotated Deployment, Service and ConfigMap for a small web service, annotate every field, predict what happens when the readiness probe fails, and state where the database password should and should not appear.

**Pass criteria:** Every field is explained correctly; the selector-to-label link is traced; the readiness-failure outcome (Pod removed from endpoints, not restarted) is stated; Secret handling is correct and not committed anywhere.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-073 — Describe the sample Kubernetes workload** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-073).

Evidence to record: an annotated manifest set, a diagram of Service-to-Pod selection and a short probe and configuration table. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
