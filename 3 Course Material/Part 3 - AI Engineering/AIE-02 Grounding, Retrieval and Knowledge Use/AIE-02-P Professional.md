# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-054**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-054](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-02-P — GROUNDING, RETRIEVAL AND KNOWLEDGE USE — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing evidence-aware retrieval and evaluating its failure cases. You decide chunking, indexing, filtering and context budgets; enforce user permissions at retrieval time; treat citations as a control and measure citation correctness; measure recall at k, precision and no-match accuracy separately from generation; and define behaviour for missing evidence and for two sources that disagree.

**Out of scope:** Embedding drift, multi-hop retrieval and tenant-leak proofs at depth (`AIE-02-E`), release gates and rubric design (`AIE-03`), agent tools (`AIE-04`), deployment and monitoring (`AIE-05`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Produce a retrieval design table covering corpus governance, chunking, indexing, filtering, authorisation, ranking, context budget and freshness, with a decision for each.
2. Show with a test that a user without permission for a runbook never causes it to be retrieved, rather than filtering after the model answers.
3. Define the assistant's behaviour for missing evidence (low confidence, no citations, escalation hint) and for conflicting evidence (source precedence by date or owner, conflict surfaced to the user).
4. Measure recall at 3, precision and no-match accuracy on a labelled question set and say which "model errors" were in fact retrieval errors.
5. Create a feedback path (wrong-answer report to ticket to new evaluation case) and document the cases as the evidence for **PRJ-055**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-02-P — Grounding, Retrieval and Knowledge Use — Professional](../../../5%20Textbook/Master%20Textbook.md#t-aie-02-p)

Read for: retrieval design decisions, authorisation at retrieval time, citations as a control, retrieval quality metrics, knowledge lifecycle and decision guide.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** For `ops-assistant`, build a labelled set of at least twelve questions: answerable, unanswerable, ambiguous and two with conflicting runbooks (for example two different restart thresholds). Document the missing-evidence and conflict policies, run the set, report recall at 3, precision and no-match accuracy, and show the answers for the conflict cases. Add a permission test with a restricted runbook.

**Pass criteria:** Conflicts are shown to the user with both sources rather than silently resolved; the restricted document is excluded before ranking; metrics are computed from labels, not eyeballed; at least one retrieval failure leads to a documented fix and a new case.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-055 — Handle missing or conflicting evidence** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-055).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
