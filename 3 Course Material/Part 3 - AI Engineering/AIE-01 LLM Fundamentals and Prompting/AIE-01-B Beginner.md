# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-048**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-048](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-01-B — LLM FUNDAMENTALS AND PROMPTING — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Foundations and vocabulary of LLM use. You define token, context window, prompt, system prompt, temperature, completion and hallucination; separate the system, user and assistant roles; explain why a scoped, read-only assistant (the running `ops-assistant` example) is a safer product than a general chatbot; and write and probe a first system prompt with three test questions.

**Out of scope:** Output validation code, pre-checks and few-shot design (`AIE-01-I`), versioned prompts, model pinning and injection testing (`AIE-01-P`), failure taxonomies and statistical comparison (`AIE-01-E`), retrieval (`AIE-02`), evaluation suites (`AIE-03`), tools (`AIE-04`), deployment (`AIE-05`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Define token, context window, system prompt, temperature, completion and hallucination, and say which of cost, length, repeatability or trust each one affects.
2. Explain why an LLM predicts the next token instead of looking facts up, and why a fluent answer can still be wrong.
3. Distinguish the system, user and assistant roles, and state which one carries fixed product policy and which carries untrusted input.
4. Write a scope statement for a read-only assistant (purpose, allowed inputs, expected output format, at least three refusals) and turn it into a system prompt.
5. Probe the prompt with one answerable, one unrelated and one change-request question, record the results honestly, and use them as the evidence for **PRJ-049**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-01-B — LLM Fundamentals and Prompting — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-aie-01-b)

Read for: tokens and context windows, system versus user roles, hallucination, and why a scoped read-only assistant beats an "ask anything" chatbot.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Using `ops-assistant` (a read-only assistant that answers operators' questions about a service from its runbooks) as the example, write a one-page note containing: (a) the seven vocabulary terms above, each defined in your own words with a one-line example; (b) a scope statement; (c) the system prompt; and (d) a table of three probe questions (answerable, unrelated, "please deploy the new version") with the actual or mock-provider reply, a pass/fail verdict and one change you would make.

**Pass criteria:** All seven terms are accurate; the scope names at least three refusals; all three probes were actually run (a mock provider is acceptable if stated) and at least one observation or failure is recorded; the note states that the assistant can be wrong and is read-only.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-049 — Define the AI use case** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-049).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
