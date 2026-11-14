# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-090**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-090](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-090](../../../4%20Project%20Document/Project.md#prj-090).

## MODULE PLT-06-P — GOLDEN PATHS, TEMPLATES AND DEVELOPER EXPERIENCE — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing supported self-service flows with evidence. You make services discoverable, write documentation by reader need (tutorial, how-to, reference, explanation), design a single status command with an explicit UNKNOWN state, build investigability for on-call developers, set a runbook quality bar, compare portal options with evidence, and define a measurement protocol before running a trial.

**Out of scope:** Template construction (Intermediate), running and analysing independent trials in depth and template governance at scale (Expert), and the Harbour cold-read demonstration (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-06--golden-paths-templates-and-developer-experience) when this matches your current ability: *Design supported self-service flows with evidence.* Typical starting point: You can build starter material and now need to show another person can use it unaided.

### 2. Learning Objectives

1. Design a discovery path so a developer can answer "what exists, who owns it, how do I use it" without asking a person.
2. Organise platform documentation using the four reader needs (tutorial, how-to, reference, explanation) and identify which one a given failing page is missing.
3. Specify a status command or page that returns a verdict (healthy, degraded, unhealthy, UNKNOWN) with freshness checks, and explain why a silent healthy state is dangerous.
4. Define the protocol for a cold-read trial before running it: participants, tasks, success definition, observer rules, intervention levels and metrics.
5. Prepare the evidence needed for **PRJ-091**: a second person follows the guide (or a documented cold read is performed), with errors recorded, ranked and fixed.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-06-P — Golden Paths, Templates and Developer Experience — Professional](../../../5%20Textbook/Master%20Textbook.md#t-plt-06-p) — Study discoverability, documentation as a product, operational status, investigability, the runbook quality bar, portal options, the measurement protocol and operating the platform as a product.

Optional enrichment: the decision guide in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Give a colleague the platform guide with no help and observe a cold read. Record where they hesitated, what they asked and what they changed in their approach, then convert three findings into ranked fixes.

**Pass criteria:** Observer rules were followed and interventions logged; findings are separated into guide, tool and participant causes; at least one fix is applied and re-checked; counts are reported without implied statistical precision.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-091 — Demonstrate self-service with guardrails** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-091).

Evidence to record: a trial protocol, an observer log, a ranked findings list and one verified fix. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
