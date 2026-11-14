# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-049**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-049](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-01-I — LLM FUNDAMENTALS AND PROMPTING — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Repeatable prompt design and inspection. You build prompts with role, scope, delimited inputs, an output contract, behaviour under uncertainty and examples; choose among few-shot, decomposition, step-by-step prompts, output constraints and lower temperature; treat output as untrusted input and validate it; add a cheap mutation pre-check; and compare prompt variants against a small rubric using a deterministic fake provider.

**Out of scope:** Bounded repair loops, prompt versioning, model pinning and privacy design (`AIE-01-P`), statistical comparison and failure taxonomy (`AIE-01-E`), retrieval (`AIE-02`), full evaluation suites and release gates (`AIE-03`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Build a system prompt containing role, scope with explicit refusals, labelled inputs, an output schema, uncertainty behaviour and one example, and point to where each part appears.
2. Choose between few-shot examples, decomposition, step-by-step prompting, output constraints and lower temperature for a given symptom, and justify the choice.
3. Implement a validator that rejects missing keys, a confidence outside low/medium/high, a refusal without a reason and an empty answer, and show four invalid payloads being rejected.
4. Run at least two prompt variants against the same fixed questions with a deterministic fake provider and score them with an explicit rubric rather than impression.
5. Diagnose a symptom (ignores the format, invents sources, obeys text inside a document, inconsistent tone) to its likely cause and fix, and prepare the comparison table for **PRJ-050**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-01-I — LLM Fundamentals and Prompting — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-aie-01-i)

Read for: prompt anatomy, few-shot and decomposition techniques, validating model output in code, deterministic pre-checks, offline fake models and the common-failures table.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Take two variants of the `ops-assistant` system prompt (for example loose wording versus the full anatomy with delimited `<context>` and an output contract). Run both on at least six fixed questions, including one answerable, one unanswerable and one change request, using a fake provider. Submit the prompts, the validator, a results table scored by a rubric you wrote (for example valid schema, refuses mutation, empty citations when no evidence, no invented source) and a decision note naming the winning variant and why.

**Pass criteria:** The rubric was written before scoring; both variants were run on identical inputs; every invalid-payload test is rejected by code, not by eye; the decision note cites rubric scores and names one limitation of the comparison (small set, fake provider).

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-050 — Design and compare prompts** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-050).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
