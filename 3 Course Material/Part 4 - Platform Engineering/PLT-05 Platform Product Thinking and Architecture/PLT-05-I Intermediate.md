# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-085**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-085](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-085](../../../4%20Project%20Document/Project.md#prj-085).

## MODULE PLT-05-I — PLATFORM PRODUCT THINKING AND ARCHITECTURE — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Defining a platform service boundary. You explain why a portal alone is not a platform, write a platform contract showing who owns what, choose and state one primary runtime scope, describe architecture as text that diffs in Git, record architecture decision records, and keep a limitations register of honest gaps.

**Out of scope:** Persona and brief writing (Beginner), outcome matrices and verified promotion (Professional), team topology and organisational strategy (Expert), and the Harbour service-boundary decision itself (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-05--platform-product-thinking-and-architecture) when this matches your current ability: *Describe a golden-path service and its user journey.* Typical starting point: You know who the platform serves and now need to draw a boundary around what you will and will not support.

### 2. Learning Objectives

1. Choose one small platform offering (for example "deploy a stateless service to Kubernetes") and write its boundary: included, excluded and escape hatch.
2. Produce an ownership table splitting responsibility between platform team and service team for build, deploy, configuration, secrets, on-call and upgrades.
3. State the supported runtime scope and explain what a team must do if its workload falls outside it.
4. Write one architecture decision record (context, decision, alternatives, consequences) and link it to a limitation it accepts.
5. Prepare the evidence needed for **PRJ-086**: a platform service boundary with explicit ownership and support expectations, and a limitations register with at least five honest entries.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-05-I — Platform Product Thinking and Architecture — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-plt-05-i) — Study why a portal alone is not a platform, the platform contract, runtime scope, architecture views as text, ADR guidance and the limitations register.

Optional enrichment: the exercise that writes an ownership table and a five-entry limitations register. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Write the ownership table and limitations register for a platform that deploys stateless services to one Kubernetes cluster. Include one decision record and one explicit support-hours statement.

**Pass criteria:** Every responsibility has exactly one owner; the register includes gap, impact, compensating control and fix-by date for each row; the ADR lists a rejected alternative; support expectations are measurable.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-086 — Define a platform service boundary** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-086).

Evidence to record: a service-boundary document, an ownership table, a limitations register and one ADR. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
