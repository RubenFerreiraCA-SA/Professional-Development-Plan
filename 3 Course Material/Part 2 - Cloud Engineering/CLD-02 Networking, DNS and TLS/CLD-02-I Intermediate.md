# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-033**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-033](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-02-I — NETWORKING, DNS AND TLS — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** The DNS chain and record types (A/AAAA, CNAME, MX, TXT, NS), TTL and negative caching, choosing a resolver with `dig @server` and `dig +trace`, host versus container DNS, `ip route get` decisions, bind address (`127.0.0.1` versus `0.0.0.0`) checked with `ss -ltn`, host firewalls (`nftables`) versus cloud security groups, and TLS essentials (chain, SAN, validity) including reproducing TLS failures without `curl -k`.

**Out of scope:** First-contact path vocabulary (CLD-02-B), written diagnostic runbooks, TLS termination design and certificate automation (CLD-02-P), packet capture, MTU and exhaustion failures (CLD-02-E), and AWS security groups and VPC design (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Resolve a name through each layer (`getent`, `dig`, `dig @resolver`, `dig +trace`) and identify where a wrong or stale answer originates.
2. Explain how TTL and negative caching affect a planned DNS change and why the TTL must be lowered before the change, not after.
3. Separate a loopback-only bind from a firewall drop using `ss -ltn` and the refused-versus-timeout difference.
4. Reproduce protocol mismatch, hostname mismatch, untrusted CA and expired-certificate failures with `openssl` and `curl` without `-k`, recording the exact error text.
5. Run a one-change-at-a-time firewall experiment with recovery and capture the evidence required by **PRJ-034**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-02-I — Networking, DNS and TLS — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-cld-02-i)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** You are given two incidents: a service reachable by IP but not by name from one client, and a service that works locally but not from another host. Write a diagnosis for each, quoting the command output that separates DNS, bind-address and firewall causes. Then tabulate four TLS failures you reproduced (protocol, name, untrusted CA, expired) with the exact error line, the check that failed and the fix.

**Pass criteria:** Each diagnosis rules out the alternative causes with command output; the TLS table shows four distinct error lines produced without `curl -k`; firewall changes are one at a time with a tested recovery; TTL advice is correct and timed before the change.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-034 — Diagnose name resolution and connectivity** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-034).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
