# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-056**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-056](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-03-B — AI EVALUATION, SAFETY AND QUALITY — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Basic quality, safety and hallucination concepts. You explain why looking at a few answers is not evaluation, write evaluation cases with explicit expectations, name the four behaviours every assistant needs (grounded in-scope answer, refusal of mutation or out-of-scope requests, honest no-match, insufficient evidence for undocumented topics), and state what a passing result does not prove.

**Out of scope:** Model-graded and human review, adversarial and injection cases, and CI gating (`AIE-03-I`), release thresholds and over-refusal analysis (`AIE-03-P`), measurement validity and red-teaming (`AIE-03-E`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Explain the difference between trying a few prompts and running a fixed evaluation set after every change.
2. Name the four behaviours an assistant needs covered and give one example question for each.
3. Write a rubric of at least five criteria for `ops-assistant` (for example refusal correctness, empty citations when no evidence, citation points to supplied text, valid schema, no secrets) with a pass condition for each.
4. Define hallucination, groundedness, over-refusal and under-refusal and give one example of each.
5. State in one paragraph what a pass on your cases proves and what it does not, ready to attach to **PRJ-057**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-03-B — AI Evaluation, Safety and Quality — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-aie-03-b)

Read for: why evaluate, the shape of an evaluation case, the four behaviours every assistant needs, a tiny runner, and what a pass does and does not prove.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write the quality rubric for `ops-assistant` as a table (criterion, how it is checked, pass condition, whether it is deterministic or needs judgement), then write six JSON evaluation cases covering the four behaviours. Add a short "what a pass does not prove" statement.

**Pass criteria:** Each rubric criterion is observable and checkable without opinion; the six cases cover all four behaviours; the limitation statement explicitly says that passing does not prove the assistant never hallucinates.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-057 — Define an AI quality rubric** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-057).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
