# T-AIE-02-P — Professional Engineering

*Chapter: [T-AIE-02 — Grounding, Retrieval and Knowledge Use](README.md) · Part 3 — AI Engineering*

<a id="t-aie-02-p"></a>
#### T-AIE-02-P — Professional Engineering

**Designing a retrieval system.**

| Decision | Options and guidance |
| --- | --- |
| Corpus governance | Who may add documents; review; deletion; sensitive content excluded |
| Chunking | By structure (headings, functions), with modest overlap; keep identifiers |
| Indexing | Keyword, vector or hybrid; refresh on document change |
| Filtering | Metadata filters (audience, product, version) before ranking |
| Authorisation | Enforce user permissions *at retrieval time*; never retrieve what the user may not see |
| Ranking | Hybrid scoring, optional re-ranker, thresholds for abstention |
| Context budget | Limit chunks and tokens; order by relevance |
| Freshness | Re-index on change; show last-reviewed dates |

**Authorisation is part of retrieval.** If the assistant can read a document the user cannot, the assistant becomes a way around access control. Filter candidate chunks by the requesting user's permissions before they reach the model, and keep audit logs of what was retrieved.

**Citations as a control.** Require citations; validate that they refer to supplied chunks; surface them to users so they can verify; and measure *citation correctness* (does the cited text support the claim?), which is stronger than just checking that a citation exists.

**Quality measurement for retrieval.** Evaluate retrieval separately from generation. With a labelled set of questions and the chunks that should answer them, track recall at k (was the right chunk retrieved) and precision, plus no-match accuracy (does it abstain on unanswerable questions). Many "model" errors are retrieval errors.

**Knowledge lifecycle.** Treat the corpus as a product: assign owners, schedule reviews, remove stale pages, add a feedback path ("this answer was wrong") that creates a ticket and a new evaluation case, and version the index so you can roll back.

**Prompt-injection through knowledge.** Sanitise or label retrieved text; keep the assistant read-only; never execute instructions found in documents; render outputs safely (escape HTML, avoid auto-following links); and monitor for suspicious patterns in corpus changes.

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Reduce fabrication | Ground in supplied chunks, require citations | Relying on parametric knowledge |
| Exact identifiers | Keyword or hybrid retrieval | Vector-only search for error codes |
| Honest "I don't know" | Threshold, empty context, low-confidence response | Falling back to the nearest document |
| Respect access control | Filter by permissions at retrieval | Post-filtering the model's answer |
| Improve quality | Fix documents and retrieval first | Prompt-only "be accurate" |
