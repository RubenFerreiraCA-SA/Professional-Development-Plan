# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-045**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-045](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-05-I — AWS INFRASTRUCTURE, RESILIENCE AND ARCHITECTURE — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Provisioning or assessing a routine service architecture: an ADR written before building (compute, network, data, edge, observability, cost, exactly one drill), topology trade-offs (public-subnet tasks versus NAT, load-balancer AZs, desired count one versus two, multi-AZ database), implementing through infrastructure code with plan before apply, verifying task placement across AZs, choosing a primary drill and recording what it does and does not prove, and a console-exceptions list.

**Out of scope:** Resilience vocabulary and the first self-healing observation (CLD-05-B), RTO/RPO objectives, runbooks and tested restores (CLD-05-P), availability mathematics, game days and multi-region (CLD-05-E), and IAM or VPC fundamentals (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Write an ADR before building that covers compute, network, data, edge, observability, cost and exactly one primary failure drill.
2. Evaluate topology trade-offs and spot an aspirational diagram (for example claiming multi-AZ while `desired_count` is one).
3. Express infrastructure as code with `desired_count` as a variable, keep the `plan` summary as evidence and re-read outputs after apply.
4. Verify task placement across AZs with `aws ecs describe-tasks` and map observation signals (HTTP health, service events, target health, logs) to drill outcomes.
5. Describe or provision the isolated environment for **PRJ-046** and record a console-exceptions list.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-05-I — AWS Infrastructure, Resilience and Architecture — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-cld-05-i)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Produce the ADR and infrastructure code for an isolated Harbour environment (provisioned, or described with plan-only output): include the plan summary, a table showing what your chosen drill proves and does not prove, a placement check for desired count two, and the console-exceptions list (empty is acceptable). Explain the difference between recovering a code-managed resource through code versus editing it by hand.

**Pass criteria:** The ADR exists before the code and names exactly one drill; the plan summary precedes any apply; limits of the drill are stated; drift handling is explained; no resource is created or changed by hand without being listed.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-046 — Describe or provision an isolated environment** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-046).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
