# T-AIE-02 — Grounding, Retrieval and Knowledge Use

*Part 3 — AI Engineering*


A model answers from frozen, general patterns; your systems, documents and rules are not among them. Grounding supplies the specific, current text the model must rely on, retrieval chooses that text, and verification checks that the answer stays within it. Most "the AI is wrong" reports turn out to be retrieval, corpus or access-control problems.

## Levels


- [Beginner Foundations](T-AIE-02-B%20Beginner.md#t-aie-02-b) — parametric versus contextual knowledge, grounding versus retrieval versus generation, corpus and chunks, stable ids, keyword retrieval with a relevance floor, a worked trusted-context answer, citations and their validation, the honest no-match, freshness.
- [Intermediate Practice](T-AIE-02-I%20Intermediate.md#t-aie-02-i) — chunking trade-offs and overlap, embeddings and cosine similarity, hybrid retrieval with rank fusion, re-ranking and context budgets, confidence and abstention, index updates with content hashes, injection fixtures, diagnosing low-quality answers with a labelled set.
- [Professional Engineering](T-AIE-02-P%20Professional.md#t-aie-02-p) — access control and tenancy models, fail-closed retrieval, caches and logs as leak paths, freshness metrics, claims with verifiable quotes, answer-or-abstain policy, prompt injection through knowledge, evaluation gates, lifecycle and design trade-offs.
- [Expert Depth](T-AIE-02-E%20Expert.md#t-aie-02-e) — failure mechanisms, re-ranking limits, query planning, ANN indexes and scale, hybrid alternatives, distribution shift, provenance and trust tiers, retrieval versus fine-tuning, grader calibration, proving isolation and deletion, subtle failures and metamorphic tests.

All examples use a neutral `orders-api` service with a small set of runbooks; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.
