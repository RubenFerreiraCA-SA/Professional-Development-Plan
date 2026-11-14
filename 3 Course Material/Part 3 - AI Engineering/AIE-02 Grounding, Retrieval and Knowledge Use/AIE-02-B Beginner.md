# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-052**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-052](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-02-B — GROUNDING, RETRIEVAL AND KNOWLEDGE USE — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Why grounding and retrieval matter. You explain that model training data is frozen, general and unaware of your systems; define corpus, chunk, retrieval, citation, RAG and no-match; build a keyword-overlap retriever over three small Markdown runbooks with a stop-word list; and show the honest no-match behaviour when nothing relevant exists.

**Out of scope:** Embeddings, hybrid retrieval, re-ranking and chunk metadata (`AIE-02-I`), authorisation and retrieval metrics (`AIE-02-P`), retrieval failure modes in production (`AIE-02-E`), evaluation suites (`AIE-03`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Explain what grounding is and why frozen, general training data cannot answer questions about your own systems.
2. Describe the retrieval flow (question, relevant chunks, context in the prompt, answer, citations) and define corpus, chunk, citation, RAG and no-match.
3. Write three small runbook files with clear headings and judge each as a knowledge source by owner, freshness, scope and trustworthiness.
4. Run a keyword-overlap retriever with a stop-word list and explain what goes wrong without the stop words.
5. Demonstrate one answerable, one unanswerable and one unrelated-words question, showing that the last two give an empty result, as evidence for **PRJ-053**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-02-B — Grounding, Retrieval and Knowledge Use — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-aie-02-b)

Read for: why grounding matters, the retrieval picture, corpus, chunk, citation and no-match vocabulary, a keyword retriever with stop words, and the honest no-match.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Choose and justify a knowledge source for `ops-assistant`: create three short runbooks (for example readiness, restart policy, dependency timeout), list for each its owner, review date and why it is trustworthy, then run the three probe questions through a simple retriever and record the chunks returned. Explain in a short paragraph what the assistant should say for the two questions with no match.

**Pass criteria:** The corpus choice is justified by source quality, not convenience; the retriever returns the right chunk for the answerable question and an empty list for the other two; the explanation says the assistant must state insufficient evidence instead of falling back to the closest document.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-053 — Choose a reliable knowledge source** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-053).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
