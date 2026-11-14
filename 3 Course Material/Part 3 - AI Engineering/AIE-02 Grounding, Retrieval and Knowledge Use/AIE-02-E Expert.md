# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-055**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-055](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-02-E — GROUNDING, RETRIEVAL AND KNOWLEDGE USE — EXPERT

### 1. Topic and Scope

**In scope for this level:** Critiquing retrieval quality, governance and architecture. You analyse production failure modes (lost in the middle, embedding drift, chunk boundary errors, stale truth, contradictory sources, poisoned corpus, cross-tenant leakage), judge when query rewriting, multi-hop, parent-child chunking or structured retrieval are justified by measurement, and assess deletion, privacy and cost.

**Out of scope:** Basic keyword retrieval and citation checks (`AIE-02-B`, `AIE-02-I`), routine permission filtering (`AIE-02-P`), general evaluation programme design (`AIE-03-E`), platform-level gateways (`AIE-05-E`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Map each production failure mode to a mechanism, a mitigation and a monitoring or test signal, and prioritise them for a given corpus.
2. Decide with evidence whether an advanced technique (query rewriting, multi-hop, parent-child chunks, structured retrieval from a database) is justified, naming the measurement that would show the simple approach has saturated.
3. Design a test that would prove the assistant cannot reveal a document the user lacks access to, including canary documents and per-tenant checks.
4. Explain how a deletion request propagates to the index, embeddings, caches and logs, and what retention applies to queries.
5. Compare at least two architectures (for example keyword only versus hybrid with re-ranking) on quality, latency, cost and operability, and record a defended recommendation as **PRJ-056**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-02-E — Grounding, Retrieval and Knowledge Use — Expert](../../../5%20Textbook/Master%20Textbook.md#t-aie-02-e)

Read for: retrieval failure modes, advanced techniques and when to adopt them, evaluation at depth, governance and privacy of embeddings, and latency and cost.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Answer the textbook mentoring prompts in writing: recall at 5 is 92% but answers are wrong 20% of the time, where do you look next; how would you prove the assistant cannot reveal a restricted document; and when would you replace a vector index with a database query. Then write a one-page architecture comparison for `ops-assistant` with a decision, stated assumptions and a rollback plan for the index.

**Pass criteria:** The diagnosis separates retrieval, grounding, completeness and abstention errors; the confidentiality proof includes negative tests and canaries; the recommendation states what would make you reverse it; cost and latency are estimated, not ignored.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-056 — Evaluate retrieval architecture** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-056).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
