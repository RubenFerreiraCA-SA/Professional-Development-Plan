# T-AIE-02-E — Expert Depth

*Chapter: [T-AIE-02 — Grounding, Retrieval and Knowledge Use](README.md) · Part 3 — AI Engineering*

<a id="t-aie-02-e"></a>
#### T-AIE-02-E — Expert Depth

**Retrieval failure modes in production**

| Failure | Mechanism | Mitigation |
| --- | --- | --- |
| Lost in the middle | Long contexts underweight central chunks | Fewer, better chunks; reorder by relevance |
| Embedding drift | Model upgrade changes vector space | Version the index; re-embed together; compare quality |
| Chunk boundary errors | Answer split across chunks | Overlap, parent-document retrieval, hierarchical chunks |
| Stale truth | Docs updated, index not | Event-driven re-indexing, freshness metadata, TTL |
| Contradictory sources | Two documents disagree | Source precedence, date-awareness, surface the conflict |
| Poisoned corpus | Malicious or erroneous document inserted | Review workflow, provenance, anomaly checks |
| Leakage across tenants | Shared index without filters | Per-tenant indexes or enforced filters; test with canaries |

**Advanced retrieval techniques.** Query rewriting and expansion (turn conversational questions into search queries), multi-hop retrieval (retrieve, reason, retrieve again), hypothetical-document embedding, parent-child chunking (retrieve small, supply larger), metadata-aware routing between indexes, and structured retrieval from databases or knowledge graphs for questions that need joins, not paragraphs. Each adds latency, cost and failure modes; adopt only when measurement shows the simpler approach saturates.

**Evaluation at depth.** Construct evaluation sets from real questions; include unanswerable, ambiguous, adversarial and multi-source cases; label the supporting passages; and measure retrieval, grounding (is every claim supported by the cited text), completeness and abstention separately. Automated grounding checks (entailment models or model-graded claim verification) scale but need calibration against human review. Maintain a held-out set that is never used for tuning.

**Governance and privacy.** Know what data is in the index, where it is stored, who can query it and how deletion requests propagate to embeddings and caches. Embeddings can leak information about their sources; protect them as the underlying data. Log queries with care. Align retention with policy.

**Cost and performance.** Latency budget: embedding the query, search, re-ranking, generation. Cache embeddings for popular queries and prefixes, batch re-indexing, use approximate nearest-neighbour indexes with tuned recall, and monitor tail latency. Cost scales with corpus size, query volume and context length.

**Prioritising failure modes for a given corpus.** Rank by likelihood × impact for *your* data rather than treating the table as a checklist.

| Corpus type | Highest-priority failures | Why |
| --- | --- | --- |
| Operations runbooks that change weekly | Stale truth, contradictory sources | Wrong instructions during an incident are costly |
| Multi-tenant customer documents | Cross-tenant leakage | A single leak is a security incident |
| Open ingestion (tickets, wikis, uploads) | Poisoned corpus, prompt-injection inside documents | Anyone can insert text the model will read |
| Large policy library | Chunk boundary errors, lost in the middle | Answers span long sections |

For each prioritised failure define *mechanism, mitigation and signal*: for stale truth the signal is the age of the newest chunk cited versus the source's last-modified time; for leakage it is a canary-document test (below); for contradiction it is disagreement among retrieved passages for the same question.

**Deciding whether an advanced technique is justified.** Measure the simple pipeline first, then ask where the loss is.

| Observation | Diagnosis | Candidate response |
| --- | --- | --- |
| Gold passage rarely in the top 20 | Retrieval failure (query/document mismatch) | Hybrid search, better chunking, query rewriting |
| Gold passage in the top 5 but answer wrong | Generation or context-assembly failure | Fewer chunks, reorder, stricter grounding prompt, check lost-in-the-middle |
| Answer needs facts from two documents | Multi-hop | Multi-hop retrieval, or restructure content |
| Question needs a join or aggregation ("how many tickets last week?") | Wrong tool: paragraphs cannot answer it | Structured retrieval from a database |
| Short chunks lose context; long chunks dilute | Granularity trade-off | Parent-child chunking |

The saturation test: tuning chunk size, top-k and hybrid weights gives less than a pre-agreed improvement (for example under 2 points of recall@k on the evaluation set) over three experiments. Only then add a technique whose cost is measured: added latency, added model calls and added failure modes.

```text
Metric               keyword-only   hybrid+rerank
recall@5             0.71           0.89
grounded answers     0.78           0.88
p95 latency          0.9 s          2.1 s
cost per 1k queries  1.0x           2.6x
```

A defended recommendation reads: "Hybrid with re-ranking is justified for the runbook corpus because grounded answers improved 10 points for 2.6× cost; keyword-only remains for the low-risk FAQ index."

**Proving that access control holds.** Retrieval must filter *before* generation, using the user's entitlement, not after.

```text
1. Create canary documents: CANARY-TENANT-A-7f3, visible only to tenant A, and CANARY-TENANT-B-91c.
2. As tenant A, ask questions designed to retrieve B's canary (including by exact phrase, paraphrase and indirect reference).
3. Assert: the string CANARY-TENANT-B-91c never appears in the answer, citations, retrieved set, logs visible to A, or cached responses.
4. Repeat with cache warmed by B, with revoked access, and with a user belonging to no tenant.
5. Run on every index or retrieval change.
```

Enforce filters in the retrieval layer (per-tenant index or mandatory metadata filter that the caller cannot omit), not in the prompt. Check caches: a response cached under a shared key is a leak that no retrieval filter will stop.

**Deletion propagation.** A request to delete a document must reach every copy:

| Location | Action | Verification |
| --- | --- | --- |
| Source store | Delete or redact | Fetch returns not found |
| Chunk store and vector index | Delete by document ID (including parent and child chunks) | Query by exact phrase returns no hit |
| Embedding cache and query result cache | Invalidate by document ID or time-to-live | Cache lookup after deletion |
| Evaluation sets and logs containing the text | Remove or redact per retention policy | Search in logs |
| Backups and replicas | Expire by policy; document the delay | Retention policy record |

Document the maximum delay before data is truly gone, and state it honestly to the people who asked.

**Evaluation hygiene.** Keep a held-out set that tuning never touches; refresh a portion every release so you detect overfitting to a static set. Report retrieval metrics (recall@k, MRR), grounding (fraction of claims supported), completeness and abstention correctness *separately*, because one aggregate hides which stage failed. Include "unanswerable" questions on purpose: an assistant that always answers has high apparent quality and bad behaviour.

**Operating cost levers.** Latency budget example: embedding 30 ms, search 60 ms, re-rank 250 ms, generation 1.5 s. Re-ranking and generation dominate, so cut candidates before re-ranking and send fewer, better chunks to generation. Watch drift in query distribution; re-run evaluations when new topics arrive.

**Mentoring prompts.** Your retrieval recall at 5 is 92% but answers are still wrong 20% of the time; where do you look next? How would you prove that the assistant cannot reveal a document a user lacks access to? When would you replace a vector index with a database query?

---
