# T-AIE-02-E — Expert Depth

*Chapter: [T-AIE-02 — Grounding, Retrieval and Knowledge Use](README.md) · Part 3 — AI Engineering*

<a id="t-aie-02-e"></a>
#### T-AIE-02-E — Expert Depth

## Why this level exists

By the Professional level a retrieval system has access control, freshness metrics, verification and an evaluation set. It works. The Expert questions begin where "it works" stops being informative: the evaluation set was built last year from questions that no longer resemble the traffic; recall at 5 is 92% and answers are still wrong one time in five; a model upgrade quietly changed the vector space; a document that is both correct and cited is nonetheless being *used* in a way its author never intended.

This level is about **diagnosing by mechanism, deciding by measurement, and knowing what the numbers cannot tell you**. It covers failure modes in production, re-ranking and query planning, retrieval at scale, alternatives to plain hybrid search, distribution shift, provenance, when retrieval is the wrong tool (and fine-tuning or a database is the right one), proofs of access control and deletion, and a catalogue of subtle failures that pass ordinary tests.

It assumes the Professional material. The `orders-api` runbooks continue as the running example, now with a larger and more varied corpus. Figures marked *illustrative* show the shape of a result; they are not measurements, and the right numbers for your system come only from your own evaluation set.

## Retrieval failure modes in production

| Failure | Mechanism | Mitigation |
| --- | --- | --- |
| Lost in the middle | Long contexts underweight central chunks | Fewer, better chunks; reorder by relevance |
| Embedding drift | Model upgrade changes vector space | Version the index; re-embed together; compare quality |
| Chunk boundary errors | Answer split across chunks | Overlap, parent-document retrieval, hierarchical chunks |
| Stale truth | Docs updated, index not | Event-driven re-indexing, freshness metadata, TTL |
| Contradictory sources | Two documents disagree | Source precedence, date-awareness, surface the conflict |
| Poisoned corpus | Malicious or erroneous document inserted | Review workflow, provenance, anomaly checks |
| Leakage across tenants | Shared index without filters | Per-tenant indexes or enforced filters; test with canaries |

Read the table as a set of *mechanisms*, each with a different detectable signal. "The answers got worse" is a symptom; the mechanism tells you which instrument to look at. Lost-in-the-middle shows up as gold chunk present but answer wrong, correlated with the chunk's position in the prompt. Embedding drift shows up as a step change in recall at the deploy time of the embedding model, with no change in the corpus. Chunk boundary errors show up as the gold chunk retrieved but missing a condition ("unless the replica is lagging"). Poisoning shows up as a recent corpus edit that moves a frequent answer.

## Advanced retrieval techniques

Query rewriting and expansion (turn conversational questions into search queries), multi-hop retrieval (retrieve, reason, retrieve again), hypothetical-document embedding, parent-child chunking (retrieve small, supply larger), metadata-aware routing between indexes, and structured retrieval from databases or knowledge graphs for questions that need joins, not paragraphs. Each adds latency, cost and failure modes; adopt only when measurement shows the simpler approach saturates.

The sections that follow take the main techniques in turn, with the mechanism, the cost and the test that tells you whether it earns its place.

## Re-ranking in depth

A first-stage retriever must be fast over the whole corpus, so it compares *independently computed* representations: the question vector against precomputed chunk vectors, or sparse term statistics. It cannot let the question and the chunk interact. A **cross-encoder** reader takes question and chunk together and scores their relevance, and is typically much more accurate and too slow to run over a whole corpus. The pipeline is therefore *recall-oriented first stage, precision-oriented second stage*.

```text
corpus ─► first stage (hybrid, top N=50..200, cheap) ─► rerank (cross-encoder, top M=5..8) ─► prompt
```

Decisions that matter:

| Decision | Effect | How to decide |
| --- | --- | --- |
| Candidate depth N | Larger N raises the ceiling on recall but multiplies rerank cost linearly | Plot recall@N of the first stage; pick N where the curve flattens; the reranker cannot recover what N excluded |
| Output depth M | More chunks give more context and more distractors | Measure claim support versus M on the labelled set |
| Truncation | Rerankers have a maximum input length; long chunks are cut silently | Check the model's limit; rerank on chunk text plus heading, not an unbounded blob |
| Score use | Reranker scores are not calibrated probabilities and shift between models | Use them for ordering; calibrate abstention thresholds on labelled data per model |
| Latency | Cost is N times the cross-encoder pass per request | Batch candidates; cap N; consider a smaller model with distillation if latency binds |

Two properties of re-ranking are easy to miss. First, **the reranker's ceiling is the first stage's recall at N**: if the gold chunk is not among the candidates, no reranker finds it, so measure first-stage recall@N separately and fix retrieval before buying rerank capacity. Second, **a reranker can hurt**: trained on a different domain it may prefer fluent generic passages over a terse authoritative table, or favour longer chunks. Always compare with and without it on your set, per question class, because an aggregate gain can hide a regression on exactly the exact-identifier questions that matter during incidents.

Position bias and duplicates matter too. If near-duplicate chunks (an old and a new version of a runbook, or overlap-created twins) dominate the top, the context is spent on one fact repeated. **Maximal marginal relevance** selects chunks by balancing relevance against similarity to those already chosen:

```python
def mmr(cands: dict[str, float], sim, lam: float = 0.7, k: int = 3) -> list[str]:
    """cands: chunk id -> relevance; sim(a, b) -> similarity between two chunks in [0, 1]."""
    chosen: list[str] = []
    pool = dict(cands)
    while pool and len(chosen) < k:
        best = max(pool, key=lambda c: (lam * pool[c] - (1 - lam) * max((sim(c, s) for s in chosen), default=0), c))
        chosen.append(best)
        pool.pop(best)
    return chosen

# mmr({"a": 0.9, "a2": 0.88, "b": 0.7}, sim) with sim(a, a2) = 0.95 and all other pairs 0.1
# -> ["a", "b", "a2"]      the near-duplicate a2 is deferred behind the distinct chunk b
```

Diversity is a hypothesis, not a free lunch: for a question whose answer *is* the repeated fact (the same warning appearing in three runbooks), diversification can drop the corroboration that raises confidence. Test it.

## Query planning

Real questions are not search queries. "And what about the replica?" is meaningless without the previous turn; "why did last night's deploy break checkout and is it related to the database thing from Tuesday?" is three questions. **Query planning** is the stage that turns user input into one or more retrieval actions.

| Technique | What it does | When it earns its place | Cost and risk |
| --- | --- | --- | --- |
| Conversation resolution | Rewrite a follow-up into a standalone query using recent turns | Multi-turn assistants; pronoun-heavy questions | The rewrite can add facts the user never said; log the rewrite |
| Query expansion | Add synonyms and related terms | Vocabulary mismatch the corpus cannot be edited to fix | Drift: expansions that pull in off-topic chunks |
| Decomposition | Split a compound question into sub-queries, retrieve for each, merge | Questions needing facts from different documents | Latency multiplies; sub-answers must be reconciled |
| Routing | Choose which index or tool (runbooks, tickets, a metrics API, a database) to query | Heterogeneous knowledge sources | A wrong route silently returns nothing relevant |
| Hypothetical-document embedding | Have a model write a plausible answer and embed that instead of the question | Short, vague questions against long documents | Embeds the model's guess; can bias toward its own invention |
| Step-back or abstraction | Retrieve the general principle, then the specific case | Questions where policy and case live in different documents | Extra round trip |

A planner is itself a model call, so it has all the failure modes of generation: it can misroute, over-decompose and hallucinate constraints. The discipline is to make its output **inspectable and testable**:

```json
{
  "standalone_query": "orders-api replica lag readiness database slow",
  "sub_queries": [],
  "route": ["runbooks"],
  "filters": {"product": "orders-api", "version": "2.x"},
  "needs_structured_data": false
}
```

Log the plan with the answer. Evaluate the planner on its own cases: given a transcript, was the standalone query faithful? Was the route right? Does routing a question about counts ("how many readiness failures last week?") to a metrics query, rather than to paragraphs, happen reliably? Keep **a fallback**: if the planner's output is invalid or its sub-queries retrieve nothing, fall back to the raw question against the default index, and record that the fallback fired.

Decomposition deserves a specific warning. Merging retrieved sets from several sub-queries can double-count the same chunk and can distort the apparent evidence, so deduplicate by chunk id, keep per-sub-query provenance (which sub-question each chunk was retrieved for), and let the generator see that structure. Multi-hop questions where the second query depends on the first answer ("find the service that owns the failing job, then its runbook") need an iterative loop with a **hop limit** and a stop condition, otherwise a confused planner will loop.

## Retrieval at scale

For thousands of chunks, brute-force scoring is fine. At millions or billions the retrieval layer becomes a systems problem, with its own trade-offs.

**Approximate nearest-neighbour (ANN) indexes** trade exactness for speed. Two families are common.

| Family | Idea | Main knobs | Trade-off |
| --- | --- | --- | --- |
| Graph-based (e.g. HNSW) | Navigate a layered proximity graph from coarse to fine | Graph connectivity at build time; search breadth at query time | High recall and low latency; memory-hungry; deletes and updates are awkward |
| Partition-based (e.g. IVF) | Cluster vectors; search only the nearest clusters | Number of clusters; clusters probed per query | Lower memory; recall depends on how many clusters are probed |
| Compression (e.g. product quantisation) | Store compressed vectors | Compression ratio | Large memory saving; some recall loss, often recovered by re-scoring top candidates with full vectors |

Whatever the family, **recall is a tunable property**, not a given. Measure ANN recall against exact search on a sample (what fraction of the true top-k does the index return?), then set the search-time knob to the cheapest value that meets your target, and re-measure when the corpus grows by an order of magnitude or the embedding model changes. An "approximate" index with 85% recall of the exact top 10 silently lowers your system's recall ceiling before any reranker or model touches the question.

Scale concerns beyond the index algorithm:

| Concern | Issue | Response |
| --- | --- | --- |
| Memory | Vectors times dimension times bytes; graph overhead | Lower dimension (if the model supports it), quantise, shard, memory-map |
| Sharding | One shard cannot hold or serve everything | Shard by tenant or domain when queries are scoped; scatter-gather when they are not, accepting tail latency from the slowest shard |
| Filtering | Metadata filters combined with ANN can hurt recall: a very selective filter may leave too few reachable candidates | Pre-filter for highly selective predicates (or use per-tenant indexes); verify recall *under the filters actually used* |
| Updates | Incremental inserts and deletes can degrade graph quality over time | Periodic rebuild into a fresh index; alias switch; tombstone and compact |
| Ingestion throughput | Re-embedding a large corpus after a model change takes days of compute | Build the new index in parallel, verify, switch; budget the cost |
| Hot queries | Popular questions dominate traffic | Cache results *keyed with tenant and permission scope*; invalidate on document change |
| Tail latency | p99 set by the slowest stage or shard | Per-stage deadlines; return degraded results rather than time out; hedged requests for read-only calls |

The filtering row is a classic subtle failure: an ANN index performs beautifully in the benchmark, then recall collapses for the tenant that owns 0.1% of the data because the filter removes almost every graph neighbour the search would have visited. The test is to evaluate recall for **small tenants and narrow filters**, not the global average.

## Hybrid and its alternatives

The default advanced design is dense vectors plus keyword retrieval fused by rank. It is a good default, not a law.

| Approach | Mechanism | Strengths | Weaknesses |
| --- | --- | --- | --- |
| Lexical (BM25) | Term frequency and rarity, normalised by length | Exact identifiers, rare terms, transparent, cheap | Vocabulary mismatch; no semantics |
| Dense single-vector | One embedding per chunk | Paraphrase, cross-lingual transfer in some models | Blurs identifiers and qualifiers; one vector must summarise a whole chunk |
| Learned sparse (SPLADE-style) | A model expands a chunk into weighted terms, searched like keywords | Semantic expansion with an inverted index; interpretable terms | Index size; model dependency |
| Late interaction (ColBERT-style) | Many small vectors per chunk; match token to token | High quality on varied domains; fine-grained matching | Much larger index; more complex serving |
| Cross-encoder re-ranking | Joint reading of question and chunk | Precision | Only viable on a short candidate list |
| Structured retrieval (SQL, APIs, knowledge graphs) | Query the system of record | Counts, joins, current state, exact values | Needs a planner and schema knowledge; wrong query is silent |
| Generated answers cached as documents | Store previously verified answers as retrievable items | Fast, consistent for repeated questions | Staleness; error amplification if the stored answer was wrong |

For reference, plain BM25 is short enough to read and, over a small corpus, to check by hand:

```python
import math
from collections import Counter

def bm25_scores(query_terms: list[str], docs: dict[str, list[str]], k1: float = 1.2, b: float = 0.75):
    """docs: chunk id -> list of terms. Returns chunk id -> BM25 score."""
    N = len(docs)
    avgdl = sum(len(d) for d in docs.values()) / N
    df = Counter(t for d in docs.values() for t in set(d))
    scores = {}
    for cid, d in docs.items():
        tf = Counter(d)
        s = 0.0
        for t in query_terms:
            if t not in tf:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))          # rarer terms count more
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avgdl))  # saturating, length-normalised
        scores[cid] = s
    return scores

# docs = {"a": "database unreachable check host".split(),
#         "b": "database slow check load check".split(),
#         "c": "restart policy hung process".split()}
# bm25_scores(["database", "unreachable"], docs) -> {"a": 1.498, "b": 0.442, "c": 0.0}   (rounded)
```

The two features that make it better than raw overlap are visible in the code: term rarity (`idf`) so that a word appearing in every chunk contributes nothing, and length normalisation (`b`) so that a long chunk does not win just by containing more words.

**Choosing among alternatives** is an evidence question, so state the decision as a hypothesis with a test.

| If the measured loss is | Hypothesis | Cheapest test |
| --- | --- | --- |
| Exact identifiers retrieved poorly | Dense blurring | Add or increase the lexical leg; check on identifier-heavy questions only |
| Paraphrased questions missed | Vocabulary gap | Add dense or learned-sparse; compare per question class |
| Gold chunk found but lacking the qualifier | Granularity | Parent-document retrieval; hierarchical chunks |
| Questions about counts or state | Wrong tool | Route to structured retrieval |
| Very long, heterogeneous corpus with high quality demands | Single-vector capacity | Pilot late interaction on a sample; measure index size and latency |

Keep fusion honest. Rank fusion has weights (how much each leg counts) and a depth (how many candidates each leg contributes). Tune them on the labelled set, **separately for question classes** if the traffic has distinct classes; a weighting tuned on prose questions can hurt error-code lookups. And remember that fusion cannot abstain: the abstention logic must sit on the legs' raw signals.

## Distribution shift

A retrieval system is tuned against a snapshot of questions and documents. Both move.

| Shift | Example | Effect | Signal |
| --- | --- | --- | --- |
| Query drift | A new product launches; questions mention names the corpus has not seen | Recall falls on new topics; abstention rises | Rising abstention, new high-frequency terms with no retrieval hits |
| Corpus drift | A reorganisation renames services; old and new vocabulary coexist | Mismatch between question and document vocabulary | Falling recall on queries using one of the names |
| Content-style drift | Docs migrate from prose to tables | Chunkers and embeddings behave differently | Rising chunk-boundary failures; token counts shift |
| Embedding-model drift | A provider updates a hosted model | Vectors change meaning for new text only, or the whole space | Step change in recall at upgrade time; new vs old chunk score gap |
| Label drift | The "right answer" changes (policy change) | Gold labels are wrong | Evaluation passes while users complain; labels older than the policy |
| Adversarial drift | New phrasing of injection attempts | Controls fail on novel patterns | New corpus edits matching suspicious patterns; failed canaries |

Detection comes from monitoring the *inputs* as well as outputs. One practical device is to compare the distribution of question topics (cluster the query embeddings, or bucket by routing label) in a recent window against a reference window, using a divergence measure such as the **population stability index (PSI)**:

```python
import math

def psi(expected: dict[str, float], actual: dict[str, float], eps: float = 1e-4) -> float:
    """expected/actual: topic -> share of queries (each summing to about 1)."""
    total = 0.0
    for k in set(expected) | set(actual):
        e = max(expected.get(k, 0), eps)
        a = max(actual.get(k, 0), eps)
        total += (a - e) * math.log(a / e)
    return total

# psi({"x": .5, "y": .5}, {"x": .5, "y": .5})                       -> 0.0
# psi({"x": .6, "y": .3, "z": .1}, {"x": .3, "y": .3, "z": .4})     -> 0.624
```

A common rule of thumb reads under 0.1 as stable, 0.1 to 0.25 as moderate shift and over 0.25 as major; those bands are conventions inherited from other fields, not laws, so calibrate against the moments when your own quality dropped. The divergence says *something changed*, not what; follow it with an inspection of the topics that grew.

The response to shift is operational: refresh part of the evaluation set from recent real questions every release (keeping a frozen held-out portion to detect overfitting), add content for the topics that grew, keep a **queue of questions that abstained** as the content roadmap, version embeddings with dated indexes, and schedule re-calibration of thresholds after every model or corpus change of size.

## Provenance and trust

At scale the question is not only "is this chunk relevant" but "where did this text come from, who vouched for it, and has it been altered since?"

**Provenance record per chunk.** Alongside text and ids, store: the source system and URL or path, the revision (commit or version id) of the source, the author and approver, the ingestion time and pipeline version, the content hash of the source revision and of the chunk, and a **trust tier** (reviewed runbook, internal wiki, user ticket, external web).

| Use | How provenance helps |
| --- | --- |
| Precedence | The ranker or assembler prefers higher trust tiers when chunks conflict |
| Injection response | When a poisoned page is found, query by author, source and time to find every chunk it touched and which answers cited it |
| Audit | "What was the assistant told when it gave this answer on the 3rd?" is answerable from index version plus chunk revision |
| Display | The user sees the source, revision and approval date, not just a title |
| Deletion | A source revision maps to all derived chunks, vectors and caches |

Make **ingestion a controlled pipeline**, not a folder watcher. Verify that source revisions come from approved locations; record the commit; refuse unsigned or unreviewed content for the authoritative tier; and keep the chunking code and its version in the provenance record, since a change in chunking is a change in what the model reads. Hash chains or signed manifests of the ingested set make silent tampering detectable: the index build verifies that each chunk's source hash matches the reviewed revision.

**Citation laundering** is the subtle trust failure of the grounded era. An answer cites a reputable-looking chunk id, and users treat the citation as endorsement. But the chunk may be a low-trust ticket quoting a wrong claim, or a wiki note summarising a policy imprecisely. Mitigation: display the trust tier and revision with the citation, never let a low-tier chunk support a high-stakes claim by itself, and require a higher-tier chunk for actions with consequences (deploy, delete, spend).

**Poisoning response.** Prepare the playbook before you need it: identify the offending revision, disable its chunks by provenance query, invalidate affected caches, list the answers served from it in the incident window (from logs with index versions and chunk ids), notify affected users, add the pattern to monitoring and the case to the evaluation set.

## Retrieval, fine-tuning and other ways to give a model knowledge

"Should we fine-tune instead?" is a recurring question, and usually the wrong first one. The options solve different problems.

| Approach | What it changes | Good for | Poor for |
| --- | --- | --- | --- |
| Retrieval (RAG) | What the model *reads* in this request | Facts that change; large corpora; citations; access control; deletion | Teaching a style or skill; tasks needing no external fact; very low latency budgets |
| Fine-tuning | The model's *weights* | Format, tone, domain vocabulary, consistent task behaviour, shorter prompts | Fast-changing facts; per-user permissions; citations; guaranteed forgetting |
| Long context (supply a whole document) | What the model reads, without selection | Small corpora; single-document questions | Large corpora; cost; attention dilution on long inputs |
| Tool and database calls | Where the answer is computed | Counts, state, joins, current values | Unstructured explanation |
| Prompt or rules | Instructions | Format, constraints, short stable facts | Anything large or changing |
| Combination | Fine-tune for behaviour, retrieve for facts | Mature products | The effort of maintaining both |

A decision structure:

| Question | If yes |
| --- | --- |
| Do facts change faster than you can retrain? | Retrieval (or tools); not fine-tuning for facts |
| Must you cite sources and show provenance? | Retrieval |
| Must different users see different knowledge? | Retrieval with access control; fine-tuned weights cannot enforce per-user permissions |
| Must you be able to delete a document and prove it is gone? | Retrieval; deleting knowledge from weights is not a reliable operation |
| Is the problem *how* the model answers (format, tone, task skill), not *what* it knows? | Fine-tune or prompt |
| Is the answer a number from a system of record? | Tool or database |

Failure patterns in the wrong choice: fine-tuning a model on runbooks to "teach" it the procedures yields fluent, uncited, undated, unauditable answers that look right until a procedure changes; building elaborate retrieval to force a consistent report format wastes effort that a fine-tune or a better output schema would solve. And note a quiet interaction: a fine-tuned model that has absorbed facts may *prefer* its memory to a conflicting retrieved chunk, so a fresher document loses the argument. Test that conflict explicitly with a planted updated fact.

## Evaluation at depth

Construct evaluation sets from real questions; include unanswerable, ambiguous, adversarial and multi-source cases; label the supporting passages; and measure retrieval, grounding (is every claim supported by the cited text), completeness and abstention separately. Automated grounding checks (entailment models or model-graded claim verification) scale but need calibration against human review. Maintain a held-out set that is never used for tuning.

Calibration deserves specifics. Take a sample of answers (a few hundred, stratified by question class), have humans grade claim support, run the automated grader on the same sample, and compute agreement and, more usefully, the grader's **false-accept rate** (the share of human-judged unsupported claims it passes). A grader that rarely rejects is worse than none because it creates confidence. Re-run the calibration when the model, the prompt or the corpus changes materially. Report intervals, not point estimates: with 200 labelled questions a difference of three points is within noise, and a change that "improved recall by 3 points" on that set has not been shown to improve anything. For comparisons between two configurations on the same questions, use paired comparisons (count the questions where one wins and the other loses) rather than comparing two aggregate scores.

**Leakage between sets.** Evaluation questions written by the same person who wrote the documents tend to reuse the documents' phrasing, flattering keyword retrieval; questions copied into prompts as few-shot examples contaminate the set; questions seen during threshold tuning no longer measure generalisation. Keep provenance for evaluation items too.

## Governance and privacy

Know what data is in the index, where it is stored, who can query it and how deletion requests propagate to embeddings and caches. Embeddings can leak information about their sources; protect them as the underlying data. Log queries with care. Align retention with policy.

Embedding inversion research has shown that, under some conditions, text can be partially reconstructed from its embedding, and membership of a document in an index can sometimes be inferred. The practical consequence is policy, not panic: classify the vector store at the sensitivity of its most sensitive source, encrypt it, restrict network access, do not send sensitive chunks to third-party embedding services your data policy does not cover, and treat exports of vectors as exports of data.

## Cost and performance

Latency budget: embedding the query, search, re-ranking, generation. Cache embeddings for popular queries and prefixes, batch re-indexing, use approximate nearest-neighbour indexes with tuned recall, and monitor tail latency. Cost scales with corpus size, query volume and context length.

## Prioritising failure modes for a given corpus

Rank by likelihood × impact for *your* data rather than treating the table as a checklist.

| Corpus type | Highest-priority failures | Why |
| --- | --- | --- |
| Operations runbooks that change weekly | Stale truth, contradictory sources | Wrong instructions during an incident are costly |
| Multi-tenant customer documents | Cross-tenant leakage | A single leak is a security incident |
| Open ingestion (tickets, wikis, uploads) | Poisoned corpus, prompt-injection inside documents | Anyone can insert text the model will read |
| Large policy library | Chunk boundary errors, lost in the middle | Answers span long sections |

For each prioritised failure define *mechanism, mitigation and signal*: for stale truth the signal is the age of the newest chunk cited versus the source's last-modified time; for leakage it is a canary-document test (below); for contradiction it is disagreement among retrieved passages for the same question.

## Deciding whether an advanced technique is justified

Measure the simple pipeline first, then ask where the loss is.

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

### Reading the gap between recall and correctness

The mentoring prompt below asks why recall at 5 is 92% yet answers are wrong 20% of the time. Work it as a diagnosis, not a guess. With 92% recall, a missing gold chunk explains at most 8 of the 20 points of wrong answers (up to 40% of failures); at least 12 points, or 60% of failures, arise after retrieval. Sample fifty wrong answers and label each with the first stage that failed:

| Label | Count (illustrative) | Reading |
| --- | --- | --- |
| Gold chunk absent from top 5 | 8 | The retrieval loss the recall number already counted |
| Gold present, answer ignored it | 10 | Context assembly: buried, outranked by a distractor, or prompt too weak |
| Gold present, answer used it, overstated | 12 | Generation: claim exceeds the text; verification is not catching it |
| Gold present but outdated or wrong | 7 | Corpus problem: the "gold" label itself is stale |
| Gold present, correct answer, grader wrong | 6 | Evaluation problem: the 20% is partly measurement error |
| Question ambiguous or unanswerable | 7 | Missing clarification or abstention |

Read it as a plan: the largest classes are overstatement and ignored context, so fewer and better-ordered chunks, quote-level verification and a support check come before more retrieval work; the stale-gold and grader-error rows say the evaluation set needs repair before further tuning means anything.

## Proving that access control holds

Retrieval must filter *before* generation, using the user's entitlement, not after.

```text
1. Create canary documents: CANARY-TENANT-A-7f3, visible only to tenant A, and CANARY-TENANT-B-91c.
2. As tenant A, ask questions designed to retrieve B's canary (including by exact phrase, paraphrase and indirect reference).
3. Assert: the string CANARY-TENANT-B-91c never appears in the answer, citations, retrieved set, logs visible to A, or cached responses.
4. Repeat with cache warmed by B, with revoked access, and with a user belonging to no tenant.
5. Run on every index or retrieval change.
```

Enforce filters in the retrieval layer (per-tenant index or mandatory metadata filter that the caller cannot omit), not in the prompt. Check caches: a response cached under a shared key is a leak that no retrieval filter will stop.

Extend the canary approach to the cases that are easy to forget:

| Scenario | What the test must show |
| --- | --- |
| Narrow filter with ANN | Recall for the smallest tenant is acceptable *and* no foreign candidate appears under any `k` or filter fallback |
| Filter failure path | If the permission lookup errors or times out, retrieval returns nothing; it does not widen the filter |
| Derived content | Summaries, query suggestions, "related questions" and evaluation exports contain no foreign canary |
| Timing and size side channels | Latency or result count does not reveal that a forbidden document matched (measure for the same query with and without the foreign canary present) |
| Revocation | After a user loses a group, the next query within the agreed lag, and every query after it, excludes that group's canary |
| Re-embedding or index swap | The canary suite runs against the *new* index before the alias switch |

State what the test does not prove: canaries show that the paths you thought of are closed. Pair them with a design review of every code path that reads the index and every store that holds text derived from it.

## Deletion propagation

A request to delete a document must reach every copy:

| Location | Action | Verification |
| --- | --- | --- |
| Source store | Delete or redact | Fetch returns not found |
| Chunk store and vector index | Delete by document ID (including parent and child chunks) | Query by exact phrase returns no hit |
| Embedding cache and query result cache | Invalidate by document ID or time-to-live | Cache lookup after deletion |
| Evaluation sets and logs containing the text | Remove or redact per retention policy | Search in logs |
| Backups and replicas | Expire by policy; document the delay | Retention policy record |

Document the maximum delay before data is truly gone, and state it honestly to the people who asked.

Two points complete the picture. **Derived answers**: if the deleted document supported cached or stored answers (a verified-answer cache, saved conversations), those must be found through provenance (which chunks fed which answers) and removed or flagged. **Models**: if any fine-tuning or distillation used the text, deletion cannot be guaranteed from the weights, which is one of the reasons to keep knowledge in retrieval rather than in training data when deletion rights apply.

## Subtle failures that pass ordinary tests

These are the failures that survive a green evaluation dashboard. Each is paired with the check that exposes it.

| Failure | Mechanism | How it hides | Exposing check |
| --- | --- | --- | --- |
| Quote-valid, claim-invalid | A real quote is attached to a claim it does not support | Citation and quote checks pass | Entailment check; human sample of cited pairs |
| Qualifier loss | "Do not restart unless the replica lags" becomes "do not restart" | Both versions sound right; the retrieved chunk is correct | Questions whose answers hinge on exceptions; gold labels include the qualifier |
| Negation blur | Dense retrieval treats "restart" and "do not restart" as near | Topic-level recall looks fine | Paired positive and negative probe questions |
| Unit and version mix-ups | Timeouts in seconds versus milliseconds; advice for release 1.x applied to 2.x | Numbers look plausible | Version and unit metadata; questions that vary the version |
| Temporal confusion | "Current" policy retrieved from a superseded page that is still indexed | Page has a recent *edit* date but old content | Supersession links; as-of queries |
| Near-duplicate dominance | Ten copies of the same text fill the top | Recall@k counts the gold chunk once | Duplicate rate in top-k; MMR experiments |
| Boilerplate retrieval | Headers, footers and navigation text embed similarly across chunks | Many irrelevant but high-scoring chunks | Inspect top hits for common text; strip boilerplate before chunking |
| Title leakage | A strongly worded title makes all its chunks match | Gold chunk ranks high for the wrong reasons | Ablate titles; test sections whose content contradicts the title |
| Hubness | In high dimensions some vectors are near to many queries | A few chunks appear for unrelated questions | Count how often each chunk is retrieved; investigate the heaviest |
| Threshold decay | Calibrated threshold stops fitting after a model or corpus change | Abstention rate drifts slowly | Track abstention against a labelled unanswerable sample |
| Citation shuffling | Model cites the right ids but attached to the wrong claims | Set-level citation checks pass | Per-claim citation checks with quotes |
| Reranker truncation | Long chunks cut before the relevant sentence | Reranker scores the preamble only | Compare scores for the chunk's full text versus its truncated form |
| Cache poisoning by ordering | A first, badly grounded answer is cached and served repeatedly | Cache hit rate looks healthy | Cache only validated answers; include index version in the key |
| Evaluation overfitting | Weights and thresholds tuned until the fixed set is perfect | Dashboards rise while users disagree | Held-out set; refresh a slice each release; paired comparisons |

Many of these appear only when you ask the system the *same question in controlled variants*: add a qualifier, swap a version, negate the instruction, paraphrase, ask in two registers. Build a **metamorphic test set** from such pairs. The invariant is explicit ("changing the version in the question must change the cited chunk"; "a paraphrase must not change the answer"), and violations are bugs even without gold labels.

## Release discipline for the retrieval layer

Treat changes to the retrieval layer as releases with the same ceremony as application deploys: a versioned index built beside the live one, an evaluation gate (retrieval, grounding, canary, injection, metamorphic), a shadow period where the candidate answers a sample of live traffic and the differences are reviewed, an alias switch, and a rollback that is a switch back. Record, with each release, the embedding model version, chunker version, thresholds, rerank model, index build id and evaluation results.

## Evaluation hygiene

Keep a held-out set that tuning never touches; refresh a portion every release so you detect overfitting to a static set. Report retrieval metrics (recall@k, MRR), grounding (fraction of claims supported), completeness and abstention correctness *separately*, because one aggregate hides which stage failed. Include "unanswerable" questions on purpose: an assistant that always answers has high apparent quality and bad behaviour.

## Operating cost levers

Latency budget example: embedding 30 ms, search 60 ms, re-rank 250 ms, generation 1.5 s. Re-ranking and generation dominate, so cut candidates before re-ranking and send fewer, better chunks to generation. Watch drift in query distribution; re-run evaluations when new topics arrive.

| Lever | Saves | Risk |
| --- | --- | --- |
| Lower candidate depth N | Rerank time linearly | Recall ceiling falls; measure recall@N first |
| Fewer chunks to generation | Tokens, latency, distraction | A needed second chunk is dropped; test multi-source questions |
| Smaller or distilled reranker | Latency and cost | Quality loss on hard cases; compare per class |
| Cache validated answers for frequent questions | Whole pipeline | Staleness, scope leaks; key by tenant, permission and index version |
| Route simple questions to keyword-only | Embedding and rerank cost | A misrouted paraphrase question; keep a confidence-based escalation |
| Batch re-embedding off-peak | Compute cost | Longer lag for corrections; keep an express path for urgent changes |
| Quantised vectors | Memory | Recall loss; re-score top candidates with full vectors |

## Expert trade-offs

| Trade-off | Position A | Position B | What decides it |
| --- | --- | --- | --- |
| Precision versus recall | Few, high-confidence chunks | Many chunks, let the model sort | The cost of a wrong answer relative to a missed one |
| Sophistication versus operability | Planner, router, reranker, multi-hop | Hybrid and a good corpus | Measured saturation, and whether the team can debug the pipeline at 3 a.m. |
| Verification depth versus latency | Existence and quote checks | Support-check model on every claim | The cost of an unsupported claim in this domain |
| Freshness versus consistency | Re-index on every change | Release index versions | Whether users are harmed more by lag or by an answer changing mid-incident |
| Shared versus isolated infrastructure | Shared index, filters, canaries | Isolated per tenant | Contractual requirements and the ability to prove separation |
| Retrieval versus training | Keep knowledge outside the model | Fine-tune for behaviour | Deletion, citation and per-user access requirements |
| Automation versus human review | Auto-ingest everything | Review authoritative content | Who can write to the corpus, and how bad a poisoned page would be |

Defend an expert recommendation by stating the **binding constraint**, the **evidence** (a labelled-set result with an interval, a canary pass, a drift measurement), the **cost accepted** and the **signal that would make you revisit**.

## Knowledge consolidation

- Diagnose by **mechanism**: each failure mode has a distinct signal; read the right instrument before changing the system.
- **Re-ranking** is bounded by first-stage recall at N; it can help or hurt per question class; **MMR** trades diversity against relevance and must be tested.
- **Query planning** (resolution, expansion, decomposition, routing) is itself a fallible model stage: make its output inspectable, test it separately, keep a fallback and a hop limit.
- At **scale**, ANN recall is a tunable property to measure against exact search, especially **under narrow filters** and for **small tenants**.
- **Hybrid** is a default, not a law: lexical, dense, learned-sparse, late-interaction and structured retrieval each answer specific measured losses.
- **Distribution shift** in queries, corpus, models and labels needs monitoring of inputs (for example PSI over topic shares) and an operational response.
- **Provenance** and **trust tiers** enable precedence, audit, poisoning response and deletion; beware **citation laundering**.
- Choose **retrieval, fine-tuning, long context, tools or prompts** by what must be true: changing facts, citations, per-user access, deletion, or behaviour.
- Calibrate **automated graders** against humans, report **uncertainty**, use **paired comparisons**, and guard against **evaluation leakage**.
- **Prove** access control and deletion with tests that include failure paths, side channels and derived content, and say what the tests do not prove.
- The hardest failures **pass ordinary tests**; use **metamorphic** variants and sampled human review to find them.

## Exercises

**Exercise 1 — Ceiling and reranker.** On a labelled set of at least fifty questions, measure first-stage recall@N for N in {5, 10, 20, 50}. Add a re-ranker (a real cross-encoder or a stand-in scoring function) with M=5. Report end-to-end recall@5 with and without it, overall and for identifier-heavy versus paraphrased questions. Explain why the best end-to-end result cannot exceed recall@N.

**Exercise 2 — Query planner under test.** Write twenty multi-turn transcripts, including follow-ups with pronouns, compound questions and counting questions. Specify the expected standalone query, route and filters for each, and score a planner (model or rules). Include five cases where the planner's output is invalid and show the fallback.

**Exercise 3 — ANN recall under filters.** Build an ANN index over a corpus with one large and one tiny tenant. Measure ANN recall versus exact search globally, then for the tiny tenant with a mandatory filter. Tune the search breadth until the tiny tenant meets the target and report the latency cost.

**Exercise 4 — Shift detection.** Take two windows of questions (real or simulated) with a new topic introduced in the second. Compute topic shares, PSI, and the list of terms with the largest share growth and zero retrieval hits. Write the content-roadmap entry this produces.

**Exercise 5 — Provenance and a poisoning drill.** Attach provenance records to every chunk. Insert a poisoned page. Using only provenance and logs, list the chunks it produced, the answers that cited them, and the caches to invalidate. Time the drill and record what was missing.

**Exercise 6 — Choose the mechanism.** For each need, choose retrieval, fine-tuning, long context, a tool call or a prompt, and justify with the decision table: (a) answers in a house style; (b) the current on-call rota; (c) a 40-page vendor manual used by one team; (d) per-customer contract terms with deletion rights; (e) a stable ten-line escalation policy.

**Exercise 7 — Grader calibration.** Grade a hundred answers by hand for claim support. Run an automated grader on the same answers. Compute agreement and false-accept rate, and decide whether the grader may gate a release. Report an interval for the false-accept rate.

**Exercise 8 — Metamorphic suite.** Write fifteen controlled variant pairs (qualifier added, version changed, instruction negated, paraphrase, unit changed). State the invariant for each and run your pipeline. Triage each violation to a mechanism from the subtle-failures table.

**Exercise 9 — Prove isolation.** Implement the canary suite, including the revoked-access, filter-failure and index-swap cases. Introduce one deliberate bug (a cache key without tenant, or a fallback that drops the filter on error) and show the suite catching it.

**Solution notes.**

*Exercise 1.* Illustrative expectations: recall@N rises steeply then flattens, and the knee tells you the useful depth. The reranker usually helps paraphrase questions more than identifier questions, and may slightly hurt the latter; if it does, route identifier-shaped queries around it or blend with the lexical score. The bound holds because the reranker only reorders candidates it was given.

*Exercise 2.* Expect the planner to succeed on simple follow-ups and fail on compound questions with implicit references. The most valuable result is the fallback test: when the plan is invalid the raw question goes to the default index and a counter increments. Review a sample of rewrites for added facts, which are the dangerous errors.

*Exercise 3.* The tiny tenant's recall is typically far below the global figure at default breadth, because the filter leaves few reachable neighbours. Raising search breadth or switching that tenant to its own index restores recall; record the latency, memory and operating cost of each option so the choice is explicit.

*Exercise 4.* The terms with large growth and no hits are the roadmap: write one content item per cluster of such terms, with an owner. A PSI above the major-shift band should come with a named topic, not just a number.

*Exercise 5.* The drill should be able to answer from records alone: which revision, which author, which chunks, which index versions, which answers. Missing items usually include "which answers" (answer logs lacked chunk ids) and "which caches" (no mapping from chunk to cached answers); fix those as findings.

*Exercise 6.* Reasonable choices: (a) fine-tune or prompt; (b) tool call, because it is current state from a system of record; (c) long context if the manual fits and usage is low, retrieval otherwise; (d) retrieval with per-tenant isolation, because of deletion rights and access control; (e) prompt, since it is short and stable. If you argued differently, the useful part is naming the deciding requirement.

*Exercise 7.* A grader with a high false-accept rate must not gate releases on its own; use it for triage and keep human sampling as the gate. With a hundred items an interval is wide (for example, 2 false accepts out of 20 unsupported claims is a range that includes both harmless and unacceptable values), so say what additional sample size would narrow it.

*Exercise 8.* Expect violations on negation, qualifier and version pairs, and few on simple paraphrase. Triage each to the likely mechanism: negation to dense blur, qualifier to chunk granularity or generation overstatement, version to missing metadata. The fix list is the output of the exercise.

*Exercise 9.* A cache key without tenant fails the "cache warmed by B" scenario; a filter-dropping fallback fails the permission-lookup-error scenario. If your suite passed with the bug present, the suite has a gap; add the scenario it missed and re-run.

## Mentoring prompts

Your retrieval recall at 5 is 92% but answers are still wrong 20% of the time; where do you look next, and what would you label to find out? How would you prove that the assistant cannot reveal a document a user lacks access to, including through caches, logs and timing? When would you replace a vector index with a database query? A re-ranker raises overall recall but error-code lookups got worse; what do you do? Your abstention rate fell by half after a model upgrade; list three hypotheses and the check for each. A reviewer asks why the team did not fine-tune on the runbooks; give the answer in terms of the requirements that decide it. What does a valid quote not prove, and what would you add? Which of your controls still hold if one low-trust source starts supplying poisoned text, and which depend on everyone behaving?

---
