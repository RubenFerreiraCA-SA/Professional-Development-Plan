# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-081**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-081](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-081](../../../4%20Project%20Document/Project.md#prj-081).

## MODULE PLT-04-I — KUBERNETES OPERATIONS, INCIDENTS AND RECOVERY — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Troubleshooting routine workload and node incidents. You work through a fault catalogue, use `kubectl debug` with ephemeral containers, cordon and drain nodes with PodDisruptionBudgets in play, observe how node loss differs from a planned drain, and rebuild a namespace from Git with a stopwatch.

**Out of scope:** Read-only vocabulary (Beginner), backup and upgrade engineering (Professional), capacity and control-plane operations at scale (Expert), and the Harbour outage-diagnosis steps (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-04--kubernetes-operations-incidents-and-recovery) when this matches your current ability: *Troubleshoot service and workload incidents.* Typical starting point: You know the triage ladder and now need to diagnose real faults, including ones where the image has no shell.

### 2. Learning Objectives

1. Diagnose five catalogue faults (bad image, wrong readiness path, missing ConfigMap key, failing dependency, insufficient resources) using only `kubectl` evidence, and record the signature of each.
2. Use `kubectl debug -it <pod> --image=busybox --target=<container>` to inspect a distroless container and explain what an ephemeral container can and cannot change.
3. Cordon and drain a node with a PodDisruptionBudget that blocks the drain, fix the PDB or replica count, repeat, and record client-visible availability.
4. Explain how abrupt node loss differs from a drain (taint-based eviction delays, Pods stuck `Terminating`), and what that means for recovery time claims.
5. Prepare the evidence needed for **PRJ-082**: an injected or simulated unavailable-Pod incident with a timestamped, structured diagnosis and a verified fix.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-04-I — Kubernetes Operations, Incidents and Recovery — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-plt-04-i) — Work through the fault catalogue, ephemeral debugging, node operations, why node failure is not a drain, and the namespace rebuild from Git.

Optional enrichment: the etcd snapshot awareness section. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Inject a fault into a two-replica service without telling yourself which one (use a random choice or a colleague's card). Diagnose it with a written timeline from first alert to verified recovery, and state the one signal that would have caught it earlier.

**Pass criteria:** The timeline has timestamps; diagnosis is evidence-led rather than trial-and-error; the fix is verified from the client side; the earlier-detection signal is concrete.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-082 — Diagnose a routine workload outage** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-082).

Evidence to record: an incident timeline, command transcripts and a short prevention note. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
