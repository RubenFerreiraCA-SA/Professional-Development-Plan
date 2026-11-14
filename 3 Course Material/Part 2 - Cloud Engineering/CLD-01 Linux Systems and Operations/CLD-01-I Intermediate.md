# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-029**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-029](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-01-I — LINUX SYSTEMS AND OPERATIONS — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Operating Linux services: a dedicated unprivileged service user, systemd units (`User=`, `EnvironmentFile=`, `Restart=on-failure`, `LimitNOFILE`), `systemctl` and `journalctl` workflow, inspecting a process through `/proc/<pid>/fd`, `lsof` and `strace`, and the six-step triage sequence (process, listener, logs, file access, resource pressure, dependency). Symptom-to-cause pairs: full disk or inodes, OOM killer, I/O wait, `Too many open files`.

**Out of scope:** First-contact commands and permission vocabulary (CLD-01-B), sandboxing directives, SSH hardening, backup and restore proofs and operator checklists (CLD-01-P), cgroup throttling, eBPF and fleet patching (CLD-01-E), and DNS or TLS path analysis (CLD-02). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Write a systemd unit that runs a service as an unprivileged user with `EnvironmentFile`, `Restart=on-failure` and `LimitNOFILE`, and read its state from `systemctl status` and `journalctl -u`.
2. Use `namei -l` and `sudo -u <user> test -r` to prove why a service account cannot read its configuration, then fix owner, group or mode precisely rather than loosening to `777`.
3. Match a symptom to its cause using the resource-pressure table (disk or inode exhaustion, OOM kill, I/O wait, descriptor limit) and name the command that confirms each.
4. Inspect a running process with `/proc/<pid>/fd`, `lsof -p` and `ss -ltnp` to find what it holds open and where it listens.
5. Apply the six-step triage sequence to a deliberately broken toy service and capture the before and after evidence required by **PRJ-030**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-01-I — Linux Systems and Operations — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-cld-01-i)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Create a service user and a unit file for a toy program, make its environment file unreadable, and produce a written triage log: the command and output at each of the six triage steps, the root-cause line from the journal, the minimal permission fix and the verification after restart. Add a short section on how you would tell this fault apart from an OOM kill and from disk exhaustion, naming the exact commands.

**Pass criteria:** Root cause is read from journal output before any restart; the fix uses owner, group or mode and is verified with `sudo -u`; OOM and disk alternatives are ruled out with named commands and output; the service is restored and re-checked with `ss` and `curl`.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-030 — Diagnose a system fault** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-030).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
