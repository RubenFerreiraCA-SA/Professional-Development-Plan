# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-040**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-040](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-04-B — AWS IDENTITY, NETWORKING AND COST CONTROLS — BEGINNER

### 1. Topic and Scope

**In scope for this level:** AWS entry skills: IAM vocabulary (principal, policy, role, user, MFA, STS), reading a JSON policy line by line (`Effect`, `Action`, `Resource`, default deny, explicit deny wins), confirming identity with `aws sts get-caller-identity`, root-user hygiene, VPC basics (CIDR, subnets, internet gateway, security group, load balancer) and creating a budget with an alert before building.

**Out of scope:** Customer-managed least-privilege design, the policy simulator and VPC edge design (CLD-04-I), permission boundaries, endpoints and access analysis (CLD-04-P), privilege-escalation paths and multi-account CIDR planning (CLD-04-E), and general cloud governance (CLD-03). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Identify the principal, action and resource in a JSON IAM policy and predict whether a given request is allowed, implicitly denied or explicitly denied.
2. Run `aws sts get-caller-identity` after configuring a profile and judge from the ARN whether it is the identity you intended.
3. State the root-user rules (MFA, no access keys, recovery use only) and explain why a role is preferred to a long-lived user.
4. Describe how a VPC, subnets, an internet gateway, a security group and a load balancer fit together for one service.
5. Create a budget alert before any network resources and capture the identity and `AccessDenied` evidence needed for **PRJ-041**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-04-B — AWS Identity, Networking and Cost Controls — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-cld-04-b)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Using a disposable (or simulated) AWS account, create a read-only operator identity, run `aws sts get-caller-identity` with its profile, attempt one action it must not be allowed and quote the `AccessDenied` message, and explain which policy element caused it. Also write the budget JSON with alert thresholds and annotate a four-line IAM policy in plain language.

**Pass criteria:** The ARN returned matches the intended operator; the denial is explained from the policy, not guessed; the budget exists with a notification subscriber before any network resource; no access keys or root usage appear in the evidence.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-041 — Establish AWS training guardrails** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-041).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
