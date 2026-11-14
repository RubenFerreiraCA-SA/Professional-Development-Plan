# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-032**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-032](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-02-B — NETWORKING, DNS AND TLS — BEGINNER

### 1. Topic and Scope

**In scope for this level:** The reachability path of one request (name, route, port, TLS, process, dependency) and the first-line command for each hop: `ip -br a`, `ip route get`, `getent hosts`, `dig +short`, `nc -vz`, `curl -sv`. Vocabulary: IP address, port, TCP, HTTP versus HTTPS, what `127.0.0.1` means inside a container, connection refused versus timeout, and `/health` versus `/ready`.

**Out of scope:** DNS record types, TTL planning, firewall rules and deliberate TLS failure drills (CLD-02-I), runbook design, TLS termination and certificate lifecycle (CLD-02-P), packet capture and scale failure modes (CLD-02-E), and cloud VPC constructs (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Order the hops a request crosses from client to dependency and name the command that tests each one.
2. Explain why `127.0.0.1` inside a container is the container itself and what that implies for a service reaching its database.
3. Distinguish "connection refused" from a timeout and say which hop each most likely implicates.
4. Interpret `ip route get`, `getent hosts` and `dig +short` output to confirm that a client has a path and a resolved address.
5. Interpret `/health` 200 alongside `/ready` 503 and draw the labelled network-path diagram required for **PRJ-033**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-02-B — Networking, DNS and TLS — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-cld-02-b)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Run a local service on port 8000 and produce a hop-labelled test log: the service answers; you stop it and show connection refused; you use a wrong port or a blocking rule to show a different symptom. Write one sentence per symptom naming the failing hop, then label each hop on a diagram of the Harbour request path.

**Pass criteria:** Each observation is tagged with its hop; refused and timeout are distinguished using real command output; the diagram shows name, route, port, process and dependency; hops are tested in order and no later hop is tested after an earlier one has failed.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-033 — Draw the service network path** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-033).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
