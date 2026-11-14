# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-080**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-080](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-080](../../../4%20Project%20Document/Project.md#prj-080).

## MODULE PLT-04-B — KUBERNETES OPERATIONS, INCIDENTS AND RECOVERY — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Day-two vocabulary and read-only operator practice. You describe what operating a cluster means after the first deployment, follow a triage ladder (status, events, logs, node state), read common Pod statuses (`Pending`, `CrashLoopBackOff`, `ImagePullBackOff`, `OOMKilled`), recognise cordon and drain, and list recovery sources.

**Out of scope:** Fault injection and node drains with disruption budgets (Intermediate), backup, restore and upgrade design (Professional), failure-domain and capacity strategy (Expert), and the Harbour checklist-writing step (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-04--kubernetes-operations-incidents-and-recovery) when this matches your current ability: *Describe cluster health and routine operator tools.* Typical starting point: You can deploy to a cluster but do not know where to look first when something looks wrong.

### 2. Learning Objectives

1. Define day zero, day one and day two operations and give two day-two tasks for the Harbour platform.
2. Run the read-only triage ladder (`kubectl get pods`, `describe pod`, `get events --sort-by=.lastTimestamp`, `logs`, `logs --previous`, `top`) and say what each step answers.
3. Interpret `Pending`, `ImagePullBackOff`, `CrashLoopBackOff`, `OOMKilled` and `Running` but not `Ready`, and name the first command that distinguishes causes.
4. Describe what `cordon`, `drain` and `uncordon` do to scheduling and Pods, and why a drain is not the same as node failure.
5. Prepare the evidence needed for **PRJ-081**: a cluster health checklist covering workload readiness, events, logs and node state for the sample platform, tested on a running workload.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-04-B — Kubernetes Operations, Incidents and Recovery — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-plt-04-b) — Read what day two means, the triage ladder, reading statuses, maintenance vocabulary and the recovery-sources overview.

Optional enrichment: the exercise that breaks a service three different ways. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Deploy a small service to a practice cluster, break it with a bad image tag, then a failing readiness path, then a low memory limit. For each fault record the status shown, the first diagnostic command, and the line of output that gave the cause.

**Pass criteria:** Each fault is diagnosed read-only before any fix; statuses are interpreted correctly; commands are listed in a sensible order; the resulting checklist could be followed by someone else.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-081 — Write a basic cluster health checklist** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-081).

Evidence to record: a health checklist, three annotated fault diagnoses and a note on what the checklist would miss. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
