# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-038**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-038](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-03-P — CLOUD FOUNDATIONS AND GOVERNANCE — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Governance and cost-aware deployment: multi-account strategy (management, security/audit, shared services, non-production and production accounts), preventive versus detective controls, a governance control table across identity, logging, network, data, cost and compliance, per-service shared-responsibility matrices, placement trade-offs, and cost engineering (forecast, drivers such as NAT, load balancer and cross-AZ transfer, commitments, showback).

**Out of scope:** Introductory service models and placement (CLD-03-B), account baseline documents (CLD-03-I), landing-zone-as-product operating models, auto-remediation risk and unit economics at scale (CLD-03-E), and AWS IAM or VPC specifics (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Propose an account structure with a stated blast-radius and billing rationale for each account.
2. Write a governance control table covering identity, logging, network, data, cost and compliance with a preventive or detective mechanism for each.
3. Build a shared-responsibility matrix for one managed service (provider guarantees, your configuration, your monitoring, audit evidence).
4. Forecast the monthly and per-lab cost of the Harbour footprint from named cost drivers and define the checks that verify it against billing data.
5. Detect untagged or non-compliant resources against a tag policy and record the baseline required by **PRJ-039**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-03-P — Cloud Foundations and Governance — Professional](../../../5%20Textbook/Master%20Textbook.md#t-cld-03-p)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Produce a governance and cost baseline for Harbour: the account structure, a control table with mechanisms, a tag policy and a compliance check against a sample inventory, a budget definition, and a cost forecast that itemises load balancer, compute, NAT, data transfer and logs. Include a decision table for who authenticates, how services authenticate and how surprise bills are caught.

**Pass criteria:** Each control names a mechanism and an evidence source; the forecast lists every cost driver with its quantity and formula; the tag check demonstrably finds a seeded violation; forecast assumptions and the date of price lookup are recorded.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-039 — Create a governance and cost baseline** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-039).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
