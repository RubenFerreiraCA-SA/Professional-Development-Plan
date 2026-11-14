# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-051**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-051](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-01-E — LLM FUNDAMENTALS AND PROMPTING — EXPERT

### 1. Topic and Scope

**In scope for this level:** Evaluating robustness, risk and model capability trade-offs. You classify model failures (fabrication, instruction-hierarchy confusion, sycophancy, format drift, position and length effects, distribution shift, non-determinism, provider change), design statistically sound prompt-change experiments, place policy enforcement outside the model, reason about cost and when fine-tuning is the wrong answer, and describe inventory, review and incident practice for AI features.

**Out of scope:** Building retrieval pipelines (`AIE-02`), designing full evaluation programmes and red-teaming (`AIE-03-E`), agent threat models (`AIE-04-E`), gateway and platform operations (`AIE-05-E`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Classify a set of observed failures against the failure taxonomy and propose, for each, a mitigation and a test that would detect a regression.
2. Design a prompt-change experiment with a held-out set, repeated runs, a paired comparison and subgroup reporting, and state which result would cause you to reject the change.
3. Explain why "the system prompt says never do X" is not a security control, and specify which checks live in code outside the model.
4. Apply the economics order (remove context, route to cheaper models, cache, then consider fine-tuning) to argue when fine-tuning is the wrong response to a quality problem.
5. Write a model-limits assessment with scope of claims, evidence, residual risks, owner and incident steps that you could defend in review as **PRJ-052**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-01-E — LLM Fundamentals and Prompting — Expert](../../../5%20Textbook/Master%20Textbook.md#t-aie-01-e)

Read for: the model failure taxonomy, evaluating prompt changes statistically, treating the LLM as an untrusted component, AI economics, and organisational practice and incident process.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Answer the three mentoring prompts in the textbook in writing: why a system-prompt rule is not a security control; how you would evaluate a regression where the assistant starts following instructions found in retrieved documents; and when fine-tuning is the wrong answer to a quality problem. Support each answer with a concrete example from `ops-assistant` and name the evidence that would change your mind.

**Pass criteria:** Answers are specific, use at least four taxonomy entries correctly, include a sample-size or repeated-run argument, name a deterministic check preferred over a model-graded one, and state the limits of what a mock-based test can prove.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-052 — Critically analyse model limits** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-052).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
