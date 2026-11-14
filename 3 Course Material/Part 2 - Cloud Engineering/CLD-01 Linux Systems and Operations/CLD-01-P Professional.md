# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-030**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-030](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-01-P — LINUX SYSTEMS AND OPERATIONS — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Safe, repeatable host operation: baseline hardening (key-only SSH, no direct root login, dedicated users, systemd sandboxing with `ProtectSystem`, `PrivateTmp`, `NoNewPrivileges`), off-host logging, explicit limits (`MemoryMax`, `CPUQuota`, `TasksMax`), backups of data directories with a proven restore, immutable-over-mutable thinking and writing an operator checklist that puts read-only diagnosis before change.

**Out of scope:** Kernel-level diagnosis (page cache, cgroup throttling, eBPF) and fleet patch strategy (CLD-01-E), basic unit authoring and first triage (CLD-01-I), basic commands (CLD-01-B), and network-path diagnosis (CLD-02). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Write a service unit that uses `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp` and explicit `ReadWritePaths`, and justify each directive against a named threat.
2. Back up a service data directory and prove restoration into a clean location by comparing checksums and recording the measured restore time against a stated objective.
3. Author an operator checklist that separates read-only diagnosis from changes, with preconditions, rollback steps and a record of who changed what and when.
4. Choose between hand-patching a host and rebuilding it from a template, defending the choice with drift and recoverability arguments.
5. Dry-run the checklist against an injected fault and keep the evidence that **PRJ-031** requires.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-01-P — Linux Systems and Operations — Professional](../../../5%20Textbook/Master%20Textbook.md#t-cld-01-p)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Deliver an operator checklist for the Harbour host and defend it through a worked incident: a service starts flapping after a configuration change. Show the checklist steps in the order you follow them, mark which are read-only, give the command that reveals the cause, the rollback, and where the change is recorded. Include a restore test of the service's data directory with checksums and the measured duration.

**Pass criteria:** Someone else could follow the checklist without verbal context; read-only steps precede every change; restoration is proven with matching checksums and a measured time; every destructive command has a stated guard (snapshot, rebuild path or approval).

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-031 — Write an operator checklist** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-031).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
