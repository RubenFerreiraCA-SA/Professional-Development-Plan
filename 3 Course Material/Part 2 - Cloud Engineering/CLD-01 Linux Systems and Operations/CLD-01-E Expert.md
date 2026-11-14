# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-031**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-031](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-01-E — LINUX SYSTEMS AND OPERATIONS — EXPERT

### 1. Topic and Scope

**In scope for this level:** Evaluating host security, reliability and automation decisions: kernel behaviours that explain production symptoms (page cache and available memory, cgroup OOM versus host free memory, CPU quota throttling versus saturation, I/O queueing, connection-tracking and ephemeral-port limits), host observability with `perf` and eBPF, failure modes (fork storm, log flood, clock skew, noisy neighbour, update surprise) and fleet-scale choices (immutable images, patch cadence, maximum host age).

**Out of scope:** Introductory commands and permissions (CLD-01-B), unit authoring and triage basics (CLD-01-I), baseline hardening and checklist writing (CLD-01-P), and cloud-provider architecture (CLD-03 onward). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Show with evidence how a process in a memory-limited cgroup can be OOM-killed while the host reports free memory, citing the cgroup limit and the kernel log line.
2. Distinguish CPU saturation from CFS quota throttling using throttling counters and the symptoms users observe.
3. Score a host against hardening guidance (`systemd-analyze security`, `sshd -T`) and decide per finding to accept, remediate or automate, recording residual risk.
4. Classify host failure modes such as fork storms, log floods and clock skew with the detection signal and defence for each.
5. Evaluate patch-and-rebuild strategies for a fleet and state which diagnostics you would refuse to run in production without approval, as required for **PRJ-032**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-01-E — Linux Systems and Operations — Expert](../../../5%20Textbook/Master%20Textbook.md#t-cld-01-e)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write a decision memo evaluating the Harbour host's hardening and automation: include measured evidence for at least two kernel-level behaviours (for example OOM under `MemoryMax` and CPU throttling counters), a scored hardening review with an accept, remediate or automate decision per finding, and a recommendation on mutable versus immutable hosts. Defend it against the challenge: "Why not disable the security module or just add more memory?"

**Pass criteria:** Every claim is backed by a command and its output or counters; each hardening finding carries a decision and residual risk; the memo lists what was not tested and why; recommendations state trade-offs rather than repeating best-practice slogans.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-032 — Evaluate operating-system hardening** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-032).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
