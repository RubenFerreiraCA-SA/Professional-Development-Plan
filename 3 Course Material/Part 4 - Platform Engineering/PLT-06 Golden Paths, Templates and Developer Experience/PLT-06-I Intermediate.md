# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-089**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-089](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-089](../../../4%20Project%20Document/Project.md#prj-089).

## MODULE PLT-06-I — GOLDEN PATHS, TEMPLATES AND DEVELOPER EXPERIENCE — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Creating reusable starter material and safe self-service. You treat a template as a product artefact, design the layout of a generated service, write a scaffolding command with input validation, test the template offline and in a cluster, set guardrails as the product, promote by pull request, and define an escape-hatch deviation record.

**Out of scope:** First-use documentation (Beginner), discoverability, status commands and measurement protocols (Professional), independent trials and template governance at scale (Expert), and the written Harbour template specification (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-06--golden-paths-templates-and-developer-experience) when this matches your current ability: *Create clear onboarding and reusable starter instructions.* Typical starting point: You can write onboarding and now need a template that generates a service that passes the platform's own checks.

### 2. Learning Objectives

1. Design the file layout of a generated service (source, Dockerfile, manifests, CI config, README, ownership metadata) and state which files the user may edit.
2. Write a scaffolding command that validates name, owner and environment inputs and refuses invalid values with a useful message.
3. Test the template offline (render, lint, schema validation) and in a disposable cluster, and explain what each layer would miss.
4. Define guardrails (resource limits, non-root, probes required, approved registry) as automated checks and demonstrate one failing when a generated probe is deleted.
5. Prepare the evidence needed for **PRJ-090**: a specification of a simple template with ownership metadata and a minimal happy-path workflow from generation to a promoted pull request.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-06-I — Golden Paths, Templates and Developer Experience — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-plt-06-i) — Study the template as a product artefact, the generated layout, scaffolding with validation, template testing, safe self-service, promotion by pull request and deviation records.

Optional enrichment: the exercise that deletes a readiness probe and confirms the checker fails. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Generate a service from a template, delete its readiness probe, and confirm the guardrail check fails. Fix the service, promote it through a pull request, and record a deviation entry for one deliberate departure from the path.

**Pass criteria:** The check fails for the right reason and passes after the fix; ownership metadata is present; the deviation record states what, why, who approved and when it expires.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-090 — Define reusable starter material** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-090).

Evidence to record: a template specification, the generated tree, a failing and passing check output and a deviation record. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
