# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-043**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-043](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-04-E — AWS IDENTITY, NETWORKING AND COST CONTROLS — EXPERT

### 1. Topic and Scope

**In scope for this level:** Assessing multi-account, compliance and threat-model decisions in AWS: workforce federation and workload identity federation, privilege-escalation paths (`iam:PassRole`, policy edits, trust-policy changes, access-key creation, privileged compute), composition of trust, resource, endpoint, service-control and boundary policies, confused-deputy conditions (`aws:SourceArn`, `aws:SourceAccount`), network trade-offs (NAT, endpoints, transit gateway, shared VPC, inspection), organisation-wide CIDR planning, cost forensics and failure modes (leaked key, overbroad role, public resource, cost runaway, lockout).

**Out of scope:** IAM and VPC basics (CLD-04-B), operator policies and edge design (CLD-04-I), least-privilege tightening and boundaries for one account (CLD-04-P), and resilience patterns (CLD-05). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Identify privilege-escalation paths in a set of IAM policies and explain why `iam:PassRole` without restriction is dangerous.
2. Add confused-deputy conditions to a cross-service trust relationship and describe the attack they prevent.
3. Construct and verify a non-overlapping CIDR plan for fifty accounts across three regions that leaves room for acquisitions.
4. Perform cost forensics on a spike by breaking it down by service, usage type and tag, and propose a guardrail rather than a memo.
5. Assess the security and financial risk of the Harbour design, ranked by likelihood and impact, as required by **PRJ-044**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-04-E — AWS Identity, Networking and Cost Controls — Expert](../../../5%20Textbook/Master%20Textbook.md#t-cld-04-e)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Review a supplied set of Harbour IAM policies and a cost export: report each escalation path found, the confused-deputy exposure, a verified CIDR plan for fifty accounts across three regions, the likely cause of the cost spike, and a ranked risk register with a guardrail for each top risk. Answer: "How would you detect that a role now has more permissions than its owners intended?"

**Pass criteria:** Every finding cites the policy statement or data row it comes from; the CIDR plan is checked by a script showing no overlap; risks are ranked with reasons and mapped to preventive controls; detection of permission drift is a repeatable mechanism.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-044 — Review security and financial risk** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-044).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
