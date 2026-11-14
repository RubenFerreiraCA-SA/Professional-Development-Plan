# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-086**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-086](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-086](../../../4%20Project%20Document/Project.md#prj-086).

## MODULE PLT-05-P — PLATFORM PRODUCT THINKING AND ARCHITECTURE — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing platform offerings and product outcomes. You build an outcome matrix mapping each promise to evidence, define what "trusted" means and does not mean, design promotion that verifies provenance, place policy in both CI and admission, handle secrets and stateful dependencies deliberately, and set health and recovery targets before injecting failures.

**Out of scope:** Boundary and ADR basics (Intermediate), team topology, build-versus-buy and adoption strategy (Expert), and the Harbour platform architecture decision record (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-05--platform-product-thinking-and-architecture) when this matches your current ability: *Design platform offerings and product outcomes.* Typical starting point: You can define a platform service and now need to prove that its outcomes hold end to end.

### 2. Learning Objectives

1. Build an outcome matrix that maps each platform promise (for example "a merged change reaches staging within 30 minutes") to the evidence a user could check.
2. Define "trusted artefact" for the platform, listing what the chain proves (source, build, digest, promotion) and what it does not (absence of vulnerabilities).
3. Place policy checks in CI and at cluster admission and explain what each location catches that the other cannot.
4. Decide how secrets and one stateful dependency enter the platform without storing credentials in Git, and state the recovery limits.
5. Prepare the evidence needed for **PRJ-087**: an architecture decision record with product goal, constraints, initial components, measures of success and links to evidence.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-05-P — Platform Product Thinking and Architecture — Professional](../../../5%20Textbook/Master%20Textbook.md#t-plt-05-p) — Read the integrated outcome matrix, what trusted means, promotion that verifies, approved environments, policy in two places, secrets, stateful dependencies and health targets.

Optional enrichment: the decision guide in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Present the architecture decision for a platform that builds, signs, promotes and runs a stateless service plus one database. For each promised outcome name the evidence, the owner and the failure you would inject to test it.

**Pass criteria:** Each outcome has checkable evidence; trust claims are bounded; policy is placed deliberately in two places; stateful limits are stated; success measures are defined before the failure tests.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-087 — Create a platform architecture decision** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-087).

Evidence to record: an outcome matrix, a platform ADR and a list of failure tests with expected evidence. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
