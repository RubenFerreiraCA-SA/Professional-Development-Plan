# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-069**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-069](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-069](../../../4%20Project%20Document/Project.md#prj-069).

## MODULE PLT-01-I — KUBERNETES FUNDAMENTALS AND ARCHITECTURE — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Creating, inspecting and deleting a disposable cluster. You create a kind cluster from a config file, manage kubeconfig contexts, apply Deployment and Service manifests declaratively, read events and `describe` output, and follow label selectors from Service to EndpointSlice to Pod.

**Out of scope:** Vocabulary-only recognition (covered at Beginner), environment-separation design and QoS reasoning (Professional), control-plane internals and scheduling theory (Expert), and the written cluster-start procedure itself (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-01--kubernetes-fundamentals-and-architecture) when this matches your current ability: *Inspect a cluster and basic resources.* Typical starting point: You can read a `kubectl get` listing but need practice building a cluster and diagnosing why a Service has no endpoints.

### 2. Learning Objectives

1. Create a kind cluster with one control-plane and two worker nodes from a config file, confirm it with `kubectl get nodes`, and delete it cleanly with `kind delete cluster`.
2. Identify the active kubeconfig context and use `kubectl config get-contexts` and `use-context` to avoid applying changes to the wrong cluster.
3. Apply a Deployment and Service declaratively and describe each lifecycle state observed (Pending, ContainerCreating, Running, Terminating) using `kubectl get events --sort-by=.lastTimestamp` and `kubectl describe pod`.
4. Follow selectors from Service to EndpointSlice to Pod, and diagnose a Service with no endpoints caused by a label mismatch.
5. Prepare the evidence needed for **PRJ-070**: a cluster-creation transcript, resource-lifecycle notes and a teardown confirmation from a disposable learning cluster.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-01-I — Kubernetes Fundamentals and Architecture — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-plt-01-i) — Work through declarative manifests, the Services and DNS discussion and the exercise that breaks readiness and liveness in turn.

Optional enrichment: the notes on kubeconfig contexts and namespaces in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** On a fresh kind cluster, deploy a two-replica workload and break it twice: first with a wrong image tag, then with a Service selector that does not match the Pod labels. For each fault state the first command you ran, the output that proves the cause, and the fix.

**Pass criteria:** Both faults are diagnosed from `describe`, events or EndpointSlices rather than guesswork; fixes are verified with a successful request or `Running` Pods; the cluster is deleted and `kind get clusters` no longer lists it.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-070 — Start a disposable learning cluster** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-070).

Evidence to record: the cluster config and creation transcript, annotated lifecycle observations for one Deployment, and proof of teardown. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
