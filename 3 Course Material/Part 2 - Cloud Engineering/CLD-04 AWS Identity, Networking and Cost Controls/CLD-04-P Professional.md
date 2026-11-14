# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-042**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-042](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-04-P — AWS IDENTITY, NETWORKING AND COST CONTROLS — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Least-privilege landing-zone controls and cost guardrails: starting from zero and tightening with last-accessed data, permission boundaries, conditions (source VPC endpoint, MFA, tags), separate plan, apply, audit and break-glass roles, the order for debugging `AccessDenied` (identity, boundary, session, organisation, resource, conditions), layered network security, VPC endpoints versus NAT cost, cost controls in operation and an evidence-of-control pack.

**Out of scope:** Principal and VPC vocabulary (CLD-04-B), readable operator policies and VPC edge basics (CLD-04-I), privilege-escalation analysis, confused-deputy defences, cost forensics and CIDR planning across an organisation (CLD-04-E), and application resilience (CLD-05). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Tighten an over-broad policy to specific actions and resource ARNs using last-accessed information and record what each removal proves.
2. Add a permission boundary and at least one condition (MFA, source endpoint or tag) and verify the effect with simulation.
3. Debug an `AccessDenied` by walking identity policy, boundary, session policy, organisation policy, resource policy and conditions in order.
4. Compare VPC endpoint cost with NAT cost for a stated data volume and recommend one.
5. Apply a change with reviewed, planned and recorded discipline and assemble the evidence pack for **PRJ-043**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-04-P — AWS Identity, Networking and Cost Controls — Professional](../../../5%20Textbook/Master%20Textbook.md#t-cld-04-p)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Take a deliberately over-broad Harbour policy, reduce it to least privilege with evidence of removed permissions, add a permission boundary and one condition, and demonstrate by simulation what is allowed and denied. Then record the change as it would pass review (plan, approval, apply, verification) and give an NAT-versus-endpoint cost comparison with the formula.

**Pass criteria:** No wildcard actions remain without justification; simulation shows both retained and removed permissions; the change record shows plan before apply and a verification step; the cost comparison is arithmetic you can re-run.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-043 — Apply least privilege and change discipline** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-043).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
