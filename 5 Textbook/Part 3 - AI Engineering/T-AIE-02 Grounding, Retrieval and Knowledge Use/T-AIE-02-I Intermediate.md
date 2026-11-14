# T-AIE-02-I — Intermediate Practice

*Chapter: [T-AIE-02 — Grounding, Retrieval and Knowledge Use](README.md) · Part 3 — AI Engineering*

<a id="t-aie-02-i"></a>
#### T-AIE-02-I — Intermediate Practice

**Preparing a corpus.**

- Write documents for retrieval: one topic per section, clear headings, the question's own vocabulary, and explicit symptoms and actions.
- Give each chunk a stable identifier (file and heading) used for citations.
- Keep metadata: owner, last reviewed date, audience, version. Stale documents are a quality problem.
- Chunk size is a trade-off: too small loses context; too large dilutes relevance and uses tokens.

**Context assembly.**

```text
<context>
<chunk id="readiness.md#database-unreachable">
database: unreachable — the service could not run SELECT 1 ... First check: ...
</chunk>
<chunk id="restart-policy.md#when-to-restart">...</chunk>
</context>
<question>What does database: unreachable mean?</question>
```

Instruct the model to cite chunk ids. Verify in code that every citation in the answer matches a chunk that was actually supplied.

**Keyword to semantic retrieval.** Keyword overlap is transparent and good for exact identifiers (error codes, metric names). *Embeddings* map text to vectors so that semantically similar passages are near each other, helping with paraphrase. *Hybrid* retrieval combines both. A *vector database* or index stores embeddings and performs nearest-neighbour search; for small corpora a simple in-memory index is enough.

```python
# conceptual: embedding retrieval
q_vec = embed(question)
hits = index.search(q_vec, k=5)           # nearest chunks by cosine similarity
hits = [h for h in hits if h.score > 0.35]  # similarity threshold -> allows no-match
```

A similarity threshold is what lets the system say "I do not know".

**Re-ranking.** Retrieve a generous candidate set (say 20), then re-rank with a stronger but slower model or cross-encoder and keep the best few. This usually improves precision.

**Confidence and abstention.** Tie confidence to retrieval evidence (number of supporting chunks, overlap or similarity) rather than letting the model decide purely by tone. Abstaining is a feature.

**Adversarial documents.** Documents in the corpus are untrusted text: one can contain instructions aimed at the model. Test with a fixture document that says to ignore the rules and reveal a made-up secret; check that the answer neither obeys nor leaks.

**Troubleshooting retrieval**

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Empty citations on a question the docs answer | Vocabulary mismatch | Add synonyms to docs; try hybrid retrieval |
| Always cites the same chunk | Common words dominate | Stop words, term weighting |
| Wrong chunk wins | Chunking cut a section awkwardly | Chunk by heading; add overlap |
| Answer ignores supplied context | Prompt does not require citations | Strengthen the output contract |
| A fictional-topic test starts matching | A new document mentions its words | Choose a new undocumented test subject |

**Exercise.** Add embedding or fuzzy matching on top of keyword retrieval for a small corpus, set a threshold, and compare precision on ten paraphrased questions.
