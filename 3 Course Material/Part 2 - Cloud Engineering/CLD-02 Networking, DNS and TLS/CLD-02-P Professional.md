# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-034**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-034](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-02-P — NETWORKING, DNS AND TLS — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** An ordered diagnostic method (name, route, port, TLS, process, dependency) written as a runbook that reports evidence rather than conclusions; failure drills with recovery (wrong bind, native firewall drop, dependency down); deciding where TLS terminates (load balancer, reverse proxy, application, mutual TLS) against a threat model; certificate lifecycle with automated renewal and 21-day and 7-day expiry alerts; network design vocabulary (CIDR, subnets, NAT, security group versus network ACL).

**Out of scope:** First commands and path vocabulary (CLD-02-B), individual DNS and TLS drills (CLD-02-I), packet capture and large-scale failures such as conntrack exhaustion and retry storms (CLD-02-E), and AWS-specific security-group implementation (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Write a six-hop diagnostic runbook whose results are stated as evidence (for example "timed out after 3 s from subnet A, succeeded from subnet B").
2. Run a failure drill (baseline, controlled fault, evidence, recovery) and show that the failing hop was identified before anything was restarted.
3. Choose where TLS terminates for a given service and justify the choice against a stated threat model and compliance need.
4. Design certificate issuance, renewal and expiry monitoring, including where private keys are kept and how renewal is tested.
5. Describe a segmented network (CIDR, public and private subnets, NAT, security-group rules) and document it as the security boundary for **PRJ-035**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-02-P — Networking, DNS and TLS — Professional](../../../5%20Textbook/Master%20Textbook.md#t-cld-02-p)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Produce a security-boundary document for the Harbour request path: trust zones, where TLS terminates and why, the certificate renewal and expiry-alert plan, and a network design with CIDR, subnet roles and security-group rules. Attach one drill write-up (baseline, fault, evidence, recovery) that proves you identified the hop before changing anything.

**Pass criteria:** The boundary document names every trust zone and the decision for TLS termination with a threat-model rationale; the expiry plan has concrete thresholds and a tested renewal path; the drill shows read-only diagnosis before change and a verified recovery.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-035 — Explain the security boundary** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-035).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
