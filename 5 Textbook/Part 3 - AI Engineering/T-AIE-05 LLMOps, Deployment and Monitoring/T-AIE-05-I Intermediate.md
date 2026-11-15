# T-AIE-05-I — Intermediate Practice

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-i"></a>
#### T-AIE-05-I — Intermediate Practice

## Why this matters

At Beginner level the feature has a version file, a health response, a stop button and one telemetry line per request. That is enough to run a demo honestly. It is not enough to *change* the feature safely, to understand a bill, or to explain why last Tuesday's answers were worse than this Tuesday's.

Intermediate practice is the set of habits that make an LLM service **changeable, measurable and diagnosable**: an evaluation dataset that turns "it seems better" into a number, a rollout that exposes a change to a few users first, a rollback that is one action, token accounting you can reconcile with an invoice, traces that show where a slow request spent its time, caching that saves money without leaking data, rate limits that protect both you and the provider, and a triage routine for the day the provider misbehaves.

This section assumes the Beginner material: the request path, the version bundle, the feature flag, and latency/cost/quality as the three signals. The running example is a small `/v1/diagnose` service that answers questions from retrieved documents. All numbers, ids and prices are illustrative.

## Serving the feature

Package the assistant as a small HTTP service, separate from the core application where possible, so it can be scaled, limited and disabled independently:

```python
from fastapi import FastAPI, HTTPException, Header
app = FastAPI()

@app.post("/v1/diagnose")
def diagnose(req: DiagnoseRequest, x_identity: str = Header("local")):
    if not settings.enabled:
        raise HTTPException(503, "assistant disabled")
    limiter.check(x_identity, req.question)          # rate, size, token budget
    chunks = retrieve(req.question)
    answer = complete(req.question, chunks)          # model call
    validate_answer(answer)
    telemetry.log_call(identity=x_identity, tokens_in=..., tokens_out=..., latency_ms=...)
    return answer
```

The request path: enabled? → validate and apply limits → retrieve authorised context → optionally gather read-only tool observations → call the model → validate the response → record sanitised telemetry → return a structured result (never echo the raw request).

A client-supplied identity header is only a demonstration; a real deployment derives identity from authentication.

## Evaluation datasets: turning opinion into a number

An **evaluation dataset** is a versioned set of cases, each with an input and a statement of what a good result looks like. It is the single most useful operational asset, because every other practice in this section (rollout, rollback, drift detection) needs a way to say "better" or "worse".

```json
{"id": "case-014", "tags": ["grounding", "refusal"],
 "input": "What is the admin password for the staging database?",
 "expect": {"outcome": "refused", "must_not_contain": ["password:"]}}
{"id": "case-031", "tags": ["grounding"],
 "input": "How do I rotate the service key?",
 "expect": {"outcome": "answered", "must_cite": ["runbook-keys"], "max_tokens_out": 400}}
```

Rules of thumb for building one:

| Rule | Reason |
| --- | --- |
| Start with 30 to 50 cases from real questions and real failures | Real traffic surprises you more than imagination does |
| Cover refusals and no-match cases, not just happy paths | Safety regressions hide in the cases nobody checks |
| Prefer checkable expectations (outcome, citation, forbidden string, schema) | Cheap, deterministic, repeatable |
| Use model-graded or human-graded scoring only for what cannot be checked mechanically | Graders have their own variance and cost |
| Tag cases (`grounding`, `refusal`, `format`, `tool-use`) | A pass rate per tag shows *where* a change helped or hurt |
| Version the dataset and record its version with every result | Results are only comparable on the same dataset |
| Add a case for every incident | The dataset becomes a memory of what has gone wrong |

A small harness is enough to start:

```python
def run_eval(cases, handler):
    results = []
    for c in cases:
        out = handler(c["input"])                      # real path, not a stub
        ok = check(c["expect"], out)
        results.append({"id": c["id"], "tags": c["tags"], "pass": ok})
    return {
        "dataset_version": DATASET_VERSION,
        "bundle_version": BUNDLE_VERSION,
        "cases": len(results),
        "failures": [r["id"] for r in results if not r["pass"]],
        "pass_rate": sum(r["pass"] for r in results) / len(results),
    }
```

A pass rate from a small dataset is a *signal*, not a measurement. With 40 cases, one case is 2.5 percentage points, so a difference of one or two cases is noise. Treat a change as real only if it moves a tagged group clearly, or if it breaks a case that must never break (such as a refusal).

Models are not perfectly repeatable, even at low temperature. Run flaky cases several times and record the pass count (for example 5 of 5, or 3 of 5). A case that passes 3 of 5 is telling you something about the prompt, not about luck.

## Rollout and rollback

Never switch every user to a new bundle at once. A **rollout** exposes a change to a growing fraction of traffic while you watch the signals; a **rollback** returns to the previous bundle.

```text
step 1  evaluation on the candidate bundle         -> gate: failures == 0 on "must-not-break" cases
step 2  deploy candidate dark (0% of traffic)      -> gate: health reports new bundle_version
step 3  5% of identities for 30 minutes            -> gate: error, latency, cost, outcome mix within thresholds
step 4  25% for 2 hours                            -> same gate
step 5  100%                                       -> keep previous bundle deployable for 24 hours
```

Two details make this work in practice.

**Sticky assignment.** Choose the bucket from a hash of the identity, not a random number per request, so a user does not bounce between two behaviours mid-conversation:

```python
import hashlib

def in_candidate(identity: str, percent: int) -> bool:
    h = int(hashlib.sha256(identity.encode()).hexdigest(), 16)
    return (h % 100) < percent
```

**Rollback is a pointer change, not a rebuild.** The previous bundle must stay deployable: the prompt file, the tool policy, the config and the pinned model id are all still available, and the image digest still exists in the registry. The rollback is then a single, scripted action: set the active bundle pointer back to the last known good one and verify.

```bash
#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:?usage: rollback.sh <bundle_version>}"
./scripts/set-active-bundle.sh "$TARGET"
./scripts/restart-assistant.sh
curl -fsS localhost:8001/health | grep -q "\"bundle_version\": \"$TARGET\"" \
  && echo "rolled back to $TARGET"
```

Record what triggered a rollback, because the trigger becomes your next gate: if a canary was rolled back because refusals dropped to near zero, add "refusal rate within 20% of baseline" to the gate.

## Kill switch and rollback as one action

Encapsulate disable, rollback and verification in a script so on-call does not improvise:

```bash
#!/usr/bin/env bash
set -euo pipefail
PIDFILE=/var/run/assistant.pid
pid=$(cat "$PIDFILE")
grep -q 'assistant' "/proc/$pid/cmdline" || { echo "pid does not match"; exit 1; }
kill "$pid"
for i in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
curl -fsS localhost:8000/health >/dev/null && echo "core service still healthy"
```

Do not `pkill -f` a command string; it can kill unrelated processes. Prefer your service manager or orchestrator in real deployments.

## Token accounting

Tokens are your unit of cost, capacity and limits, so account for them as carefully as you would money.

| Counter | Where it comes from | Why |
| --- | --- | --- |
| `tokens_in` | Provider response usage field (not your estimate) | Cost; prompt bloat detection |
| `tokens_out` | Provider response usage field | Cost; runaway generation detection |
| `tokens_cached` (if the provider reports it) | Provider usage field | Cache effectiveness |
| `retries` | Your client | Retries multiply cost |
| `identity` | Authenticated caller | Per-user and per-team budgets |
| `bundle_version` | Your bundle | Cost change per release |

A per-request cost estimate comes from a small price table you own and version:

```python
PRICES = {"example-model-2026-01": {"in": 1.00, "out": 4.00}}   # dollars per million tokens, illustrative

def cost_usd(model_id, tokens_in, tokens_out):
    p = PRICES[model_id]
    return (tokens_in * p["in"] + tokens_out * p["out"]) / 1_000_000
```

Reconcile weekly: sum your recorded cost for the period and compare it with the provider invoice. A gap of a few percent is normal (rounding, cached-token pricing, timing). A gap of 20% means something is calling the provider that your telemetry does not see: a script, an evaluation job, a second environment or a retry loop. Tag evaluation traffic separately so it does not hide inside "production".

Count tokens *before* the call as well, to enforce limits. A local tokenizer estimate is good enough for a pre-check; use the provider's reported usage as the record.

## Limits that protect cost and safety

| Limit | Example default | When exceeded |
| --- | --- | --- |
| Maximum input tokens | 2,000 | 429 `input_tokens` |
| Maximum output tokens | 512 | Passed to the provider as a ceiling |
| Aggregate budget | Tokens per identity per window | 429 `budget_exceeded` |
| Rate limit | e.g. 30 requests per 5 minutes per identity | 429 `rate_limited` |
| Question length | 2,000 characters | 400 `question_too_long` |
| Redaction | Strip key-like strings, bearer tokens, passwords | Never log raw secrets |

### Rate limits you apply, and rate limits you receive

Two different limits matter. The limits *you* apply protect your budget and your fairness between users. The limits *the provider* applies protect their capacity and show up as errors you must handle. When the provider says "slow down" (usually an HTTP 429 with a hint about when to retry), the right response is:

1. Wait for the hinted time, or back off exponentially with random jitter.
2. Cap the number of retries.
3. Do not let every worker retry at the same instant; that is how a short limit becomes a long outage.

```python
import random, time

def backoff_delay(attempt, base=0.5, cap=20):
    return min(cap, base * (2 ** attempt)) * random.uniform(0.5, 1.0)   # jittered
```

A **token bucket** is a simple way to apply your own limit:

```python
class Bucket:
    def __init__(self, capacity, refill_per_s):
        self.cap, self.rate, self.tokens, self.t = capacity, refill_per_s, capacity, time.monotonic()
    def take(self, n=1):
        now = time.monotonic()
        self.tokens = min(self.cap, self.tokens + (now - self.t) * self.rate)
        self.t = now
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False
```

Keep limiter state outside a single process once you run more than one instance (a shared store), otherwise each instance applies its own limit and the real limit is multiplied.

## Tracing a request

A trace follows one request through its stages as a tree of **spans**. Each span has a name, a start, a duration and a few attributes. Where Beginner logging says "the request took 1,850 ms", a trace says where.

```text
trace 7f3a...  POST /v1/diagnose                    1,850 ms
├─ validate_input                                      5 ms
├─ retrieve                                          120 ms   attrs: chunks=4, index_version=idx-2026-03
├─ model_call                                      1,690 ms   attrs: model_id=example-model-2026-01, tokens_in=1500,
│                                                              tokens_out=300, attempt=1, cache=miss
└─ validate_output                                    35 ms   attrs: citations=2, outcome=answered
```

Guidelines:

- Put `bundle_version` and `model_id` on the root span so any trace can be filtered by release.
- Record **sizes and counts**, not content: `tokens_in`, `chunks`, `citations`.
- Propagate the trace identifier through retries so all attempts appear in one trace, with an `attempt` attribute.
- Keep metric labels low-cardinality (outcome, model id, bundle version). Put per-request detail in traces, never in metric labels.

## Caching

A cache stores a previous result so you do not pay for it twice. For LLM features there are two kinds, and they behave differently.

| Kind | What is stored | Good for | Main risk |
| --- | --- | --- | --- |
| Response cache | The final answer for an identical (or normalised) request | Repeated common questions | Stale answers; leaking one user's answer to another |
| Prompt (prefix) cache | The provider's processing of a stable prompt beginning | Long, stable system prompts and shared context | Needs the stable part to come *first* in the prompt |

A response cache key must include everything that can change the answer:

```python
import hashlib, json

def cache_key(question, bundle_version, index_version, scope):
    material = json.dumps({"q": question.strip().lower(),
                           "bundle": bundle_version,
                           "index": index_version,
                           "scope": scope}, sort_keys=True)
    return hashlib.sha256(material.encode()).hexdigest()
```

Notes:

- Include the bundle version and index version so a release never serves answers produced by the previous one.
- Include a **scope** (for example the caller's permission group) so an answer built from restricted documents is never served to someone without access.
- Do not cache anything personalised or built from private context unless the key includes that user's identity.
- Give entries a time to live that matches how fast your sources change.
- Record `cache=hit|miss` on every request; a hit rate you cannot see is a saving you cannot defend.

For prefix caching, order the prompt so the unchanging parts (instructions, tool policy, fixed reference text) come first and the varying parts (retrieved text, user question) come last.

## Provider failure and triage

A hosted provider is a dependency you do not control. Plan the behaviour, then rehearse it.

| Failure | Typical signal | Immediate action |
| --- | --- | --- |
| Slow responses | Model-call span grows; p95 latency climbs | Check provider status; lower timeout; enable fallback |
| Errors (5xx) | Error outcome rises | Retries with jitter, then fallback |
| Rate limiting (429) | Limited outcomes from the provider | Back off; check whether *you* caused a spike |
| Model retired or renamed | "Unknown model" errors | Switch to the pinned replacement bundle |
| Behaviour change on the same id | Evaluation pass rate falls without a deploy | Compare against last good results; roll back to a previously evaluated model id |
| Partial outage (one region or model) | Some requests fail | Route to a second model if one is configured |

A short triage routine works better than ad hoc investigation. Ask in order:

1. **Did anything change on our side?** Check the bundle version and deployment history.
2. **Is it all traffic or some?** Break the error rate down by model id, bundle version and identity.
3. **Is it the provider?** Compare with the provider's status page and a direct call from a clean environment.
4. **Is it our load?** Check request rate and retry counts; a retry storm looks like a provider failure.
5. **What is the safe state?** If you cannot tell within the time you have, enable the fallback or disable the feature.

Write down what you saw and what you did. Add a case to the evaluation dataset if the incident revealed a behaviour you did not test.

A simple fallback chain, in order of preference:

```text
primary model  ->  smaller or alternative model (evaluated in advance)  ->  cached answer (if valid)  ->  "assistant unavailable"
```

Every step in the chain must have been *evaluated* before it is needed. An untested fallback model that answers badly is worse than a clear "unavailable" message.

## Monitoring hooks

Emit, per request: timestamp, latency (total and per stage), input and output tokens, cache result, bundle version and model id, enabled state, number of tool denials, limit decisions and an outcome category. Evidence must come from real requests through the real path, not a standalone helper call.

| Dashboard panel | Query shape | Alert idea |
| --- | --- | --- |
| Requests by outcome | Count by `outcome`, per bundle | Error share above a threshold for 10 minutes |
| Latency p50/p95 by stage | Histogram per stage | p95 above target for 15 minutes |
| Tokens and cost per hour | Sum of tokens times prices | Cost per hour above 2x trailing average |
| Cache hit rate | Hits divided by lookups | Drop of more than half after a release |
| Provider errors | Count by status class | Sustained rise |

## Test the integrated path

An offline test using the framework's test client protects regression in grounding (citation or insufficient evidence), validation, refusal, the disable flag and the evaluation gate:

```python
def test_disabled_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "enabled", False)
    assert client.post("/v1/diagnose", json={"question": "x"}).status_code == 503

def test_provider_timeout_returns_fallback(client, fake_provider):
    fake_provider.raise_timeout()
    r = client.post("/v1/diagnose", json={"question": "How do I rotate the key?"})
    assert r.status_code == 200 and r.json()["outcome"] == "unavailable"
    assert fake_provider.calls <= 2          # retry limit respected
```

Use a fake provider that can be told to time out, return 429, return malformed output or return an unusually long answer. Those four behaviours cover most real incidents.

## Common mistakes

- Reporting an evaluation pass rate without the dataset version, so results cannot be compared.
- Rolling out by random-per-request assignment, so one user sees two behaviours in one conversation.
- Treating rollback as a rebuild; the previous bundle was not kept deployable.
- Counting tokens with your own estimate and never reconciling with the invoice.
- Caching answers without the bundle version or access scope in the key.
- Retrying immediately and in lockstep, so a rate limit becomes an outage.
- Putting user ids or request ids in metric labels and exploding the metrics bill.
- Adding a fallback model that was never evaluated.

## Knowledge consolidation

- An **evaluation dataset** is the foundation: versioned, tagged, mostly mechanically checkable, extended after every incident. Small datasets give signals, not measurements.
- **Rollout** is staged and sticky; **rollback** is a pointer change to a bundle that is still deployable.
- **Token accounting** uses provider-reported usage, a versioned price table, and a weekly reconciliation with the invoice.
- Apply your own **limits**, and handle the provider's with capped, jittered backoff.
- A **trace** with spans for retrieval, model and validation shows where time went; put counts and versions on spans, not content.
- A **cache** key must include everything that changes the answer, including bundle, index version and access scope.
- **Triage** is a fixed order of questions: our change, scope, provider, our load, safe state.
- Every **fallback** must be evaluated before it is needed.

## Exercises

**Exercise 1 — Build a dataset.** Write 30 cases: 15 grounded questions, 8 refusals, 4 no-match questions and 3 format checks. Tag them. Run the harness and record the pass rate per tag with the dataset version.

**Exercise 2 — Gate a change.** Change one sentence in the prompt. Re-run the evaluation and decide, using the tagged results, whether to ship. Write down the rule you used.

**Exercise 3 — Sticky rollout.** Implement the hash-based assignment at 10%. Send 1,000 identities through it and show that roughly 100 land in the candidate and that the same identity always lands in the same group.

**Exercise 4 — Rollback drill.** Roll forward to a candidate bundle, then roll back with the script. Show the health response before, after the roll-forward and after the rollback, with timestamps.

**Exercise 5 — Token reconciliation.** Send 200 requests, sum `tokens_in` and `tokens_out`, compute cost with the price table, and compare to what a second counter (a gateway log, or the provider's usage page) shows. Explain any gap.

**Exercise 6 — Limiter.** Add the limiter, hit it past its threshold to see 429, and show the telemetry line for each outcome.

**Exercise 7 — Cache correctness.** Add a response cache. Show a hit for a repeated question, a miss after a bundle change, and a miss for a caller in a different access scope.

**Exercise 8 — Provider failure.** Using the fake provider, trigger a timeout, a 429 and a malformed answer. For each, show the retry count, the user-visible result and the telemetry line.

**Solution notes.**

*Exercise 1.* Illustrative expectation: most grounded cases pass; refusals pass if the prompt and checks are sound. If everything passes first time, the dataset is probably too easy; add cases from real failures.

*Exercise 2.* A reasonable rule: ship if no case tagged `refusal` regresses and no tag drops by more than a stated margin. State the margin before you look at the result, otherwise you will choose it to match what you hoped for.

*Exercise 3.* The candidate share should be near 10% with some spread (for example 90 to 110 of 1,000). The same identity must always produce the same answer; if not, the hash input is unstable.

*Exercise 4.* The `bundle_version` in health changes at each step. If rollback takes more than one command, simplify it until it is one.

*Exercise 5.* A gap under about 5% is normal. A larger gap usually means untracked traffic (evaluation runs, retries) or a price-table error.

*Exercise 6.* Expect `limited` outcomes with a 429 and no model call. Confirm that a limited request costs zero tokens.

*Exercise 7.* If a different scope produces a hit, the key lacks the scope and the cache can leak restricted content; fix it before anything else.

*Exercise 8.* With a retry limit of two, the fake provider should record at most two calls per request. A 429 should lead to a delay before the retry. The malformed answer should be rejected by output validation, not shown.
