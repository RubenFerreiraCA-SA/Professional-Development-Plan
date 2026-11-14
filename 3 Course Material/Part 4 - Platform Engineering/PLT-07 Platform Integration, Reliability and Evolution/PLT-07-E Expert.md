# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-095**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-095](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-095](../../../4%20Project%20Document/Project.md#prj-095).

## MODULE PLT-07-E — PLATFORM INTEGRATION, RELIABILITY AND EVOLUTION — EXPERT

### 1. Topic and Scope

**In scope for this level:** Critiquing platform architecture, reliability and product improvement. You plan evolution and deprecation of the golden path, treat the delivery path as production, anticipate scaling inflection points, govern through automated guardrails rather than approval boards, evaluate platform health, compare build, buy and adopt, and run a final architecture review checklist.

**Out of scope:** Basic integration and demonstrations (Beginner to Professional), vendor negotiation, and organisation-specific budgeting.

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-07--platform-integration-reliability-and-evolution) when this matches your current ability: *Critique platform architecture, reliability and product improvement.* Typical starting point: You can demonstrate an operable platform and now need to defend its architecture and hand it over.

### 2. Learning Objectives

1. Plan a breaking change to a shared reusable workflow so that no team is broken without notice, including versioning, deprecation window, migration tooling and rollback.
2. Identify the single points of failure in the delivery path itself (registry, CI runners, signing key, GitOps controller) and state the mitigation and residual risk for each.
3. Identify the inflection points at which manual support, bespoke exceptions or one-team assumptions stop scaling, and propose the next capability for each.
4. Evaluate platform health using adoption, outcomes, reliability and satisfaction signals, and explain why treating any of them as a target invites gaming.
5. Prepare the evidence needed for **PRJ-096**: a coherent architecture review with independent-user feedback, a trade-off register and a next-improvements roadmap you can hand over.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-07-E — Platform Integration, Reliability and Evolution — Expert](../../../5%20Textbook/Master%20Textbook.md#t-plt-07-e) — Read platform evolution and deprecation, platform reliability engineering, scaling beyond one team, governance without gatekeeping, evaluating platform health, build, buy or adopt and the final architecture review checklist.

Optional enrichment: the mentoring prompts about the breaking-change rollout. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Present and defend the final platform architecture to a reviewer who has read your records. Cover the trade-off register, independent feedback, the weakest claim and the three improvements you would fund next.

**Pass criteria:** Every claim has evidence; every ADR links to a limitation or risk; the weakest claim is named by you rather than the reviewer; the roadmap is ordered by user benefit and risk, with owners.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-096 — Defend and hand over the platform** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-096).

Evidence to record: an architecture review document, a trade-off register, independent feedback and a prioritised roadmap. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
