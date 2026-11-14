# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-028**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-028](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-01-B — LINUX SYSTEMS AND OPERATIONS — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Reading a Linux host as an operator: identify who you are (`whoami`, `id`, `sudo -l`), decode `ls -l` permission bits and `chmod`/`chown` effects, list processes (`ps`, `top`) and listening sockets (`ss -ltnp`), read service logs (`journalctl -u`, `tail`) and check disk and memory (`df -h`, `du`, `free -h`). The mental model: a service is a process owned by a user, holding a port, writing logs and limited by the files that user may read.

**Out of scope:** Writing systemd units, service users and sandbox options (CLD-01-I and CLD-01-P), triage of OOM kills, inode exhaustion and file-descriptor limits (CLD-01-I), hardening, backups and restore proofs (CLD-01-P), cgroups and kernel diagnostics (CLD-01-E), and network-path testing (CLD-02). Hands-on implementation steps live only in the Project Document.

### 2. Learning Objectives

1. Decode permission strings such as `-rw-r-----` together with `id` output to state which user or group can read, write or execute a given file.
2. Read `ps` output (PID, PPID, owning user, command) and stop a process with SIGTERM, explaining why SIGKILL is a last resort.
3. Connect a listening port in `ss -ltnp` to the owning process and to the HTTP response seen with `curl`.
4. Choose the correct log source (`journalctl -u <unit>`, `/var/log/...`) for one service and read its most recent entries for the cause of a symptom.
5. Use `df -h`, `du -sh` and `free -h` to say whether disk or memory could explain a symptom, and record those observations as the evidence for **PRJ-029**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-01-B — Linux Systems and Operations — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-cld-01-b)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Start a small server on port 8000 as a non-root user, then, with real command output pasted into your record, answer: (a) why a service user `app` gets `Permission denied` opening a `-rw-------` file owned by `alice`, and what the correct fix is instead of `chmod 777`; (b) which command shows who is listening on port 8000 and how its output changes after you stop the process; (c) which log command you run first for a managed service and what a full filesystem looks like in `df -h`.

**Pass criteria:** Three permission strings are decoded correctly; PID, port and HTTP response are linked with real output taken before and after stopping the server; `chmod 777` and `kill -9` are rejected as first responses with reasons; no claim is made without a command that supports it.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-029 — Inspect the service host** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-029).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
