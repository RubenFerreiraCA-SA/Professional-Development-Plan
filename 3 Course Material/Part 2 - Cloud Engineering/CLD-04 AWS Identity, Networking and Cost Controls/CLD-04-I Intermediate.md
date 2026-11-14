# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-041**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-041](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-04-I — AWS IDENTITY, NETWORKING AND COST CONTROLS — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Routine AWS access and network paths: a training administrator versus a read-mostly demo operator using readable customer-managed policies, proving permissions without side effects through `aws iam simulate-principal-policy`, the minimal service VPC edge (two public subnets in two AZs, load-balancer security group open to the internet, application security group allowing only the load-balancer group), execution role versus task role, reachability diagnostics against the cloud endpoint, and a cost guardrails document.

**Out of scope:** Identity and VPC basics (CLD-04-B), permission boundaries, conditions, endpoints and policy-evaluation debugging (CLD-04-P), escalation paths, cross-account composition and CIDR planning for an organisation (CLD-04-E), and ECS resilience drills (CLD-05). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Write a least-privilege customer-managed policy for a demo operator and verify allowed and denied actions with the policy simulator instead of creating real resources.
2. Design a VPC edge with a load-balancer security group and an application security group that references the load-balancer group, leaving no open SSH.
3. Differentiate the ECS execution role from the task role and document the human operator, task role and execution role separately.
4. Diagnose a cloud endpoint in order (DNS name, route, port, HTTP status) and map timeout, refused and 502/503 outcomes to likely causes.
5. Produce the application access-path map and identity baseline required by **PRJ-042**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-04-I — AWS Identity, Networking and Cost Controls — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-cld-04-i)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Produce an access-path map for the Harbour service on AWS: the principals (training admin, demo operator, task role, execution role) with policy-simulator evidence of one allowed and one implicitly denied action each, the VPC and security-group layout validated against a CIDR plan, and an ordered diagnostic of the cloud endpoint. Explain what a timeout, a refusal and a 503 would each indicate.

**Pass criteria:** Simulator output shows `allowed` and `implicitDeny` as predicted; the application security group source is a group reference rather than a CIDR; execution and task roles are separate and narrow; the diagnostic order is respected and each symptom maps to a hop.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-042 — Map the application access path** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-042).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
