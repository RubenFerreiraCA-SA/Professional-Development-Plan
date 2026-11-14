# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-036**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-036](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-03-B — CLOUD FOUNDATIONS AND GOVERNANCE — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Cloud vocabulary and placement: IaaS, PaaS, SaaS, containers and serverless; who owns each layer under shared responsibility; region versus availability zone and why one AZ or one node is not high availability; mapping each Harbour component (API, database, edge, logs) from its local form to a cloud shape; first safety rules (training account, budget alarm, no root for daily work, no keys in source control, tags).

**Out of scope:** Account and identity structure, budgets and tag policy as documents (CLD-03-I), multi-account governance and cost engineering (CLD-03-P), landing-zone operating models, concentration risk and unit economics (CLD-03-E), and AWS service syntax (CLD-04 and CLD-05). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Classify a given workload as IaaS, PaaS, SaaS, container or serverless and state what you manage and what the provider manages.
2. Fill a shared-responsibility table for a small service (guest OS patching, managed database engine, application code, security-group rules) and defend each owner.
3. Explain what a single-AZ or single-node deployment does and does not survive, and what a two-AZ layout adds.
4. Build a placement table mapping the Harbour API, database, edge and logs from local development to a cloud shape.
5. State the four first safety rules for a training account and record the needs classification required by **PRJ-037**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-03-B — Cloud Foundations and Governance — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-cld-03-b)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** For the Harbour sample service, classify each component as IaaS, PaaS, SaaS or container/serverless, produce the placement table (local versus cloud), draw a diagram with a user, load balancer, two application instances in two AZs and a database marking who patches each box, and list what a single-AZ failure would do to users.

**Pass criteria:** Each component has a service model and an owner for patching and configuration; the diagram shows two AZs with correct responsibility labels; the failure statement is honest about single-node limits; the four safety rules are stated.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-037 — Classify the training system's cloud needs** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-037).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
