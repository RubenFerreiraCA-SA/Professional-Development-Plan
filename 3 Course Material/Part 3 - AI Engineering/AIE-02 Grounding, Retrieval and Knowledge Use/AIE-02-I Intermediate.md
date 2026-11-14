# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-053**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-053](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-02-I — GROUNDING, RETRIEVAL AND KNOWLEDGE USE — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Using retrieval to support an answer. You prepare documents with one topic per section and stable chunk identifiers and metadata, assemble labelled context, require and verify citations in code, compare keyword, embedding and hybrid retrieval, use a similarity threshold to permit no-match, and troubleshoot common retrieval symptoms.

**Out of scope:** Permission filtering and retrieval quality measurement (`AIE-02-P`), corpus governance and lifecycle (`AIE-02-P`), contradictions and index poisoning at depth (`AIE-02-E`), release gates (`AIE-03`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Rewrite a runbook for retrieval with one topic per section, symptom vocabulary, a stable identifier such as `readiness.md#database-unreachable` and owner and review metadata.
2. Assemble a prompt context with labelled `<chunk id=...>` elements and instruct the model to cite only supplied chunk identifiers.
3. Write code that rejects any answer whose citation is not among the chunks supplied, and show it catching a made-up citation.
4. Compare keyword and embedding or fuzzy retrieval on ten paraphrased questions, choose a similarity threshold, and report precision and the no-match cases.
5. Diagnose a retrieval symptom (empty citations on an answerable question, always the same chunk, wrong chunk wins) using the troubleshooting table, and record the attribution evidence for **PRJ-054**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-02-I — Grounding, Retrieval and Knowledge Use — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-aie-02-i)

Read for: preparing a corpus with stable chunk identifiers, context assembly, verifying citations, keyword versus embedding versus hybrid retrieval, similarity thresholds, re-ranking and troubleshooting.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Build a retrieval-and-attribution demonstration for `ops-assistant`: a corpus of at least five chunks with stable ids, retrieval of the top three, a context block, a mock model answer that cites chunk ids, and a citation verifier. Run ten paraphrased questions against keyword and one other method, tabulate hits, misses and no-matches, and add one fault-injection case where the answer cites a file that was never retrieved.

**Pass criteria:** Every cited id is machine-verified against supplied chunks; the fault-injection case is rejected; the comparison table includes at least one failure and its probable cause; the chosen threshold is justified by the observed data.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-054 — Demonstrate retrieval and attribution** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-054).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
