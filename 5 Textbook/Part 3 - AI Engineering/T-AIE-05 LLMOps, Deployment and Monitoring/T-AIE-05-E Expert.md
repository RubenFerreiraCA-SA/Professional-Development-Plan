# T-AIE-05-E — Expert Depth

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-e"></a>
#### T-AIE-05-E — Expert Depth

## Why this level exists

Professional practice makes one AI feature safe to run. Expert practice is about what changes when there are *many* features, *several* providers, regulated or high-stakes use, and an organisation that must answer questions from auditors, customers and its own finance team about systems whose behaviour nobody can fully specify.

The expert questions are structural. How do you route traffic across models and providers without losing the ability to say what answered a given request? How do you notice that the world your prompts were written for has moved? What do you do in the first hour of an incident where the system's output may have harmed someone, and what must you be able to prove afterwards? What can you retain, for how long, and who may see it? What does capacity actually cost when utilisation is uneven? How do you express a release policy that is more complicated than "5%, 25%, 100%"?

This section assumes the Beginner, Intermediate and Professional material: version bundles, evaluation datasets and gates, staged rollout, token accounting, tracing, caching, rate limits, drift detection, cost ceilings, escalation, safety monitoring, fallbacks and ownership. It does not assume any specific vendor. Every number, name and price below is illustrative, chosen to make the arithmetic and the reasoning visible; none is a benchmark or a quote.

## First principles: operating what you cannot fully specify

Three properties make LLM operations different from operating conventional services, and each drives a design choice at this level.

1. **The behaviour is not a function you wrote.** You can version it, sample it and constrain it, but you cannot enumerate it. Evidence is statistical, and evidence ages.
2. **The dependency can change without telling you, or tell you on a schedule you do not control.** A provider retires a model on a date; another adjusts behaviour behind a stable id. Your reliability depends on practices for *detecting* and *absorbing* change, not on preventing it.
3. **Harm is possible and attribution is hard.** When an output causes harm, the questions "which model, which prompt, which context, which policy, who approved it?" must be answerable from records that exist before the incident.

The consequence is an operating stance: **make every decision reconstructible, every change reversible, every dependency substitutable and every cost attributable.** The sections below are ways of buying each of those.

## Platform architecture for AI at scale

A central gateway in front of model providers provides authentication, per-team quotas, cost attribution, caching, prompt and response logging with redaction, policy filters, model routing and fallbacks, and a single place to rotate keys or switch providers. The trade-off is an additional critical dependency and a team to run it. Standardise the telemetry schema for AI calls so every team's dashboards and cost reports are comparable.

**Central gateway: argue both sides with a decision table.**

| Question | Evidence for a gateway | Evidence against |
| --- | --- | --- |
| How many teams call models? | Five or more teams with separate keys and bills | One or two teams with a shared library |
| Is spend or data handling a concern? | Need per-team budgets, redaction, audit | Low spend, low-risk data |
| Do you need provider portability? | Plan to route and fall back across providers | Single provider accepted |
| Who would run it? | A platform team with on-call and a roadmap | No owner: it becomes a fragile shared dependency |
| What is the latency budget? | Added hop of a few milliseconds is acceptable | Real-time use with a very tight budget |

A gateway is a new tier-1 dependency: it needs its own SLO, capacity plan, rate limits per team, a bypass or fail-open/fail-closed decision documented per use case, and a release process as careful as any shared service. If nobody can staff that, a shared client library with common telemetry may deliver most of the value at lower risk.

### The standard call record

Whatever the architecture, define one record for every model call so that cost, quality and audit questions can be answered across teams. Illustrative schema:

```json
{
  "call_id": "c-8f21",
  "trace_id": "t-77a0",
  "ts": "2026-05-04T10:22:31Z",
  "team": "support-eng",
  "feature": "support-assist",
  "tier": 2,
  "bundle_version": "2.3.0",
  "route": {"policy": "route-v6", "primary": "provider-a/model-x-2026-01", "served_by": "provider-b/model-y-2026-02",
            "reason": "primary_timeout"},
  "usage": {"tokens_in": 1480, "tokens_cached": 900, "tokens_out": 310, "retries": 1},
  "cost_usd": 0.0041,
  "latency_ms": {"total": 2100, "provider": 1880, "gateway": 6},
  "data_class": "customer-messages",
  "outcome": "answered",
  "safety": {"input_flags": [], "output_flags": [], "tool_denials": 0}
}
```

Note `served_by` and `reason`: when routing is dynamic, the system that *answered* differs from the system you *intended*. If the record only holds the intended model, every analysis of quality by model is wrong.

## Multi-model and multi-provider operation

Using more than one model is attractive for resilience, cost and quality-per-task. It also multiplies what you must evaluate and explain.

### Why route at all

| Motivation | Mechanism | What you must prove |
| --- | --- | --- |
| Resilience to a provider outage | Failover to a second provider | The second path meets quality *and* data-handling requirements |
| Cost | Send easy requests to a cheaper model | Quality parity on the routed share |
| Quality per task | Different models for extraction, drafting, classification | Per-task evaluation, not a blended number |
| Negotiating position and exit | Demonstrated ability to move | The move has actually been rehearsed |
| Latency | Fast model for interactive steps | Latency gain without unacceptable quality loss |

### Routing policies

Routing policy is configuration with consequences; version it like code and release it through the same gates.

```yaml
route: route-v6
rules:
  - match: {task: classify, data_class: [public, internal]}
    primary: provider-a/small-2026-01
    fallback: [provider-b/small-2026-02]
  - match: {task: draft_reply, tier: 2}
    primary: provider-a/large-2026-01
    fallback: [provider-b/large-2026-02]
    shadow: provider-c/large-2026-03          # not served; compared offline
  - match: {data_class: [restricted]}
    primary: selfhosted/model-z-2026-01
    fallback: []                                # restricted data never leaves; fail closed
limits:
  max_fallback_depth: 1
  fallback_share_alert: 0.10                    # alert if >10% of traffic is on fallback
```

Design points:

- **Data classes constrain the route.** A restricted class may have *no* external fallback; failing closed is the compliant behaviour.
- **Bound fallback depth.** Cascading through three providers multiplies latency and obscures the cause.
- **Alert on fallback share.** A fallback that quietly serves 40% of traffic is a hidden migration.
- **Shadow before promotion.** Run the candidate on a copy of real requests, discard its output, and compare offline.

### Heterogeneity costs

Different models differ in more than quality. Maintain a **capability matrix** per route, reviewed on every change:

| Property | Why it matters operationally |
| --- | --- |
| Context window and tokenizer | Same text, different token counts; limits and budgets change |
| Output format reliability (schema adherence) | Validators and retries behave differently |
| Tool-calling conventions | Tool schemas and parsing may need adapters |
| System-prompt sensitivity | A prompt tuned for one model may regress on another |
| Refusal and safety behaviour | Safety evaluation must be repeated per model |
| Rate limits and error semantics | Backoff and breaker settings differ |
| Data handling terms and region | Compliance differs per provider |
| Deprecation policy | Lifecycle and re-evaluation schedule differ |

Two practical rules follow. First, **a prompt is tuned to a model**; treat a prompt-model pair as the unit you evaluate and release, not the prompt alone. Second, **tokenizers differ**, so cost, truncation and limits must be computed per model, not with a single estimate.

### Evaluating the routed system

A routed system is a different system from any one of its models. Evaluate it as one.

```text
Evaluation of route-v6
  1. Per-model evaluation on the full dataset (each path alone).
  2. Router evaluation: for each case, did the router choose the intended path? (classification accuracy of the router)
  3. End-to-end evaluation through the router with fault injection:
       - primary timeouts at 100%       -> measure pass rate on fallback path
       - primary at 30% errors          -> measure pass rate and latency
       - fallback also failing          -> confirm fail-closed behaviour
  4. Cost: simulated month at observed traffic mix and expected fallback share
  5. Sign-off: pass rate on each path within tolerance of baseline; router accuracy above threshold
```

A subtle failure: a **router that sends hard cases to the cheap model** because its own classifier is weak. The blended pass rate looks fine because easy cases dominate; the hard-case tag collapses. Always report pass rate per tag and per path.

### Exit and substitutability

Substitutability is a property you test, not claim. Run a **provider exit rehearsal** at a stated cadence:

```text
Provider exit rehearsal (annual, or on contract change)
  scope:       one tier-2 feature, one week of mirrored traffic
  steps:       1) route 100% of mirrored traffic to the alternative; 2) run full evaluation and canary suite;
               3) measure cost and latency; 4) list prompt, tool-schema and validator changes needed;
               5) estimate engineering-weeks to cut over for real
  deliverable: a cutover plan with a number of weeks and a list of blockers
```

If the answer is "we cannot move in under six months", then you have a single-provider dependency, whatever the architecture diagram says.

## Distribution shift

**Distribution shift** means the inputs, the context, or the relationship between inputs and good answers changes after you evaluated. The Professional section named input, knowledge and model drift; at expert level the task is to separate the kinds of shift, detect them with appropriate statistics, and decide what response each one warrants.

| Kind | What changed | Example | Response |
| --- | --- | --- | --- |
| Covariate shift | Distribution of inputs | New market brings a new language and slang | Extend dataset; maybe prompt and retrieval changes |
| Concept shift | What a correct answer is | Policy changes; yesterday's right answer is wrong | Update knowledge sources and expected outputs; re-run gates |
| Prior shift | Mix of intents | A launch makes billing questions 40% of traffic | Re-weight evaluation; check per-intent performance |
| Context shift | Retrieved material changes | Index rebuild; documents rewritten | Retrieval evaluation; citation validity |
| Adversarial shift | Attackers adapt | New injection technique spreads | Safety cases; filter updates |
| Model shift | Provider behaviour changes | Silent model update | Scheduled canary suite; pin ids |

### Detecting input shift

Compare current inputs with a reference window using a distance on a low-dimensional summary (topic labels, language, length, embedding cluster membership). A common approach is the **population stability index** over bins:

```text
PSI = sum over bins of (p_now - p_ref) * ln(p_now / p_ref)

Illustrative reading (a convention, not a law):
  < 0.10   little shift
  0.10-0.25 moderate; investigate
  > 0.25   large; treat as a change in the system's operating conditions
```

```python
import math

def psi(ref, now, eps=1e-6):
    total = 0.0
    for k in set(ref) | set(now):
        p, q = max(ref.get(k, 0), eps), max(now.get(k, 0), eps)
        total += (q - p) * math.log(q / p)
    return total
```

Cautions:

- **A distance tells you something moved, not that it matters.** Combine it with per-segment quality: a shift in a segment where you are strong is benign; a shift toward a segment where your pass rate is low is not.
- **Choose the summary deliberately.** Length can shift with no semantic change; topic can shift with no length change. Use several.
- **Control for seasonality.** Compare against the same weekday and hour, or against a seasonally adjusted reference.
- **Set the response before the alert.** For example: PSI above 0.25 on topic mix triggers a dataset review within a week, not an automatic prompt change.

### Detecting quality shift without labels

Most production traffic has no ground truth. Combine weak signals and read them together:

| Signal | Behaviour under shift | Caveat |
| --- | --- | --- |
| Abstention and no-match rate | Rises when inputs leave the knowledge | Also rises with a broken index |
| Citation validity (does the cited passage support the claim?) | Falls when retrieval degrades | Needs a checker |
| Self-consistency (same question, several samples) | Disagreement rises on unfamiliar inputs | Costs extra calls; sample only |
| Output length and format-failure rate | Moves with model changes | Style changes can be benign |
| User correction, edit distance on drafts, escalation | Direct field signal | Sparse and biased toward unhappy users |
| Graded sample (model-graded, human-calibrated) | Closest to truth | Costly; keep small and regular |

Treat any one as weak evidence and require **two independent signals** before declaring a quality incident, unless the signal is a safety category.

### Responding to shift: update, constrain or stop

| Option | When it fits | Cost |
| --- | --- | --- |
| Extend evaluation and retrieval, keep behaviour | Shift is within the feature's remit | Moderate; ongoing |
| Constrain scope (refuse out-of-distribution intents, route to a human) | Shift moves into areas the feature handles badly | Product impact; clear messaging |
| Roll back to a bundle validated for the earlier regime | Shift came from your own change | Low |
| Stop the feature for a segment | Harm risk and no near-term fix | High; decide in advance |

Writing down which option applies to which kind of shift *before* it happens is what separates an operated system from a monitored one.

## High-stakes incident response

For features whose output can affect safety, money, legal standing or health, incident response must anticipate harm, evidence and obligation. The basic escalation tiers from the Professional section remain; this adds what is specific to high stakes.

### Priorities in the first hour

```text
Minute 0-10   Contain.     Disable or constrain the feature (pre-granted authority). Do not diagnose first.
Minute 10-30  Preserve.    Freeze evidence: bundle record, routing decisions, call records, relevant traces,
                           retrieved context ids, policy versions. Suspend deletion jobs for affected data.
Minute 30-60  Scope.       Which users, which period, which versions? Use call records keyed by bundle and route.
              Notify.      Incident commander, legal/compliance and security as per the notification matrix.
Afterwards    Remediate.   Contact affected parties as policy requires; correct outputs where possible.
```

**Contain before you understand.** A fallback or disable action that can be reversed is cheaper than another hour of exposure.

### Evidence that must exist before the incident

| Evidence | Purpose | Failure if absent |
| --- | --- | --- |
| Version bundle and release record per request | Reconstruct what ran | Cannot scope the incident |
| Routing decision and `served_by` | Know which model answered | Wrong attribution |
| Retrieved context identifiers (not necessarily content) | Know what the model was shown | Cannot tell retrieval failure from model failure |
| Policy and tool-permission versions | Know what the system was allowed to do | Cannot assess authority breach |
| Human approval records for the release | Accountability | Dispute over process |
| Content for flagged and sampled requests, under retention policy | Review actual outputs | Argument from memory |
| Action audit log for tools with side effects | Know what actually happened | Cannot remediate |

The tension between preserving evidence and minimising retained data is resolved by **tiered capture**: identifiers and metadata for everything; content for samples and flagged requests; legal hold overrides routine deletion for affected data after an incident is declared.

### Human-in-the-loop controls

For high-stakes actions, design the control so that a human review is *real*: a reviewer who sees a hundred drafts an hour approves them all. Measure it.

| Control | Metric that shows it works |
| --- | --- |
| Human approval before a side-effecting action | Rejection rate and time per review (a rate near zero or time of a few seconds suggests rubber-stamping) |
| Sampled post-hoc review | Disagreement rate between reviewers and the system |
| Escalation to a specialist | Share escalated; correctness of escalation decisions |
| Two-person rule for policy changes | Rate of changes caught in review |

### Post-incident learning

A review should produce changes in *controls*, not only text:

```text
Review output
  1. Timeline reconstructed from records (and gaps in records noted as findings).
  2. Contributing factors: model, prompt, retrieval, policy, process, monitoring.
  3. What detected it, and when would we have detected it without that signal?
  4. Changes: new evaluation cases, gate rules, alerts, limits, runbook edits, training.
  5. Owner and date for each change; follow-up check that they landed.
```

Track **time to detect**, **time to contain** and **time to scope** as service-level indicators for incident handling. Drill them.

### Drilling the kill switch without an incident

**Proving a kill switch without an incident.** Drill it on a schedule, in production-like conditions: flip the switch, confirm within a stated time that (1) the health response reports disabled, (2) no model calls leave the service (provider-side or gateway metrics show zero), (3) users receive the documented refusal, (4) the core service remains healthy, then re-enable and confirm recovery. Use the orchestrator's native control (scale to zero, config flag via the deployment system) instead of a PID file or manual process kill, which can silently target the wrong process. Record the drill's timings; a switch that takes 40 minutes to work is not a kill switch.

## Governance

Governance is the set of decisions about *what is allowed to run* and *who decides*, made explicit and auditable.

### Intake, tiering and approval

Every new AI use case enters through a short intake. Tier determines review depth.

| Tier | Typical characteristics | Required before launch |
| --- | --- | --- |
| 1 (low) | Internal, read-only, no personal data | Team lead approval; registered in inventory; standard telemetry |
| 2 (medium) | Customer-facing or personal data, no autonomous actions | Security review; evaluation with safety cases; privacy assessment; runbook; drill |
| 3 (high) | Autonomous actions or consequential decisions about people | Formal risk assessment; independent evaluation review; human oversight design; staged launch with sign-off; ongoing audit |
| Prohibited | Uses the organisation has decided not to allow | Not launched |

### The inventory

An inventory that is not connected to reality decays. Generate as much as possible from the gateway and release records:

```yaml
feature: support-assist
tier: 2
owner: support-engineering
purpose: draft replies to customer support messages for agent review
data_classes: [customer-messages, internal-docs]
models: [provider-a/large-2026-01, provider-b/large-2026-02]
tools: [lookup_order (read), search_kb (read), draft_reply (write-draft)]
human_oversight: agent reviews every draft before sending
last_evaluation: 2026-04-02
known_limitations: [weak on billing disputes, English-only evaluation]
last_drill: 2026-03-20
review_due: 2026-07-01
retire_if: no traffic for 90 days
```

Make the inventory *authoritative for deployment*: the gateway should refuse calls from features that are not registered, or whose review is overdue by more than a grace period. That turns the inventory from a document into a control.

### Policy as code

Rules that can be checked mechanically should be:

```text
policy: data_class_routing
  deny if feature.data_class includes "restricted" and route.provider not in ["selfhosted"]
policy: retention
  deny if capture.retention_days > 30 and capture.purpose != "incident_hold"
policy: tools
  deny if tier < 3 and tool.side_effect not in ["none", "draft"]
policy: review_overdue
  deny if feature.review_due < today - 14 days
```

Evaluate policies at deploy time (so a release that violates them fails the pipeline) and at run time (so a configuration change cannot bypass them). Keep policies versioned, reviewed and tested with positive and negative examples.

### Change control and separation of duties

For tier 2 and 3, the person who writes a prompt or tool policy should not be the only person who approves it. The release record shows both. Emergency changes are permitted through the narrow path described earlier, and are reviewed after the fact within a fixed time.

### Regulatory and contractual obligations

Obligations vary by jurisdiction and contract, so do not hard-code a legal theory in an engineering document; make them *inputs* to the policies above. Typical categories to track per feature: whether personal data is processed and in which region; whether decisions affecting individuals are made or supported; transparency or disclosure duties to users; record-keeping duties; and provider contractual limits (for example no training on your data, region restrictions). Record each as a field in the inventory and check it in the policy engine. Ask the legal function to own the *meaning* of each field; engineering owns that the field is enforced.

## Retention and data lifecycle

Operating AI features generates sensitive data: prompts, retrieved text, answers, feedback and evaluation samples. Each has purposes that justify keeping it and risks that argue for deleting it.

| Data | Purpose | Default retention (illustrative) | Handling |
| --- | --- | --- | --- |
| Call metadata (ids, sizes, tokens, outcome, versions) | Cost, reliability, audit | 13 months | No content; low risk |
| Traces with content hashes and counts | Debugging | 30 days | No raw content |
| Full prompt and answer content for sampled requests | Quality review | 14 to 30 days | Redacted; restricted access; deleted on schedule |
| Flagged requests (safety, user report) | Investigation | 90 days, or until case closed | Restricted; access logged |
| Evaluation datasets | Regression | Life of feature | May contain real-derived text; scrub and review |
| Incident evidence | Legal and learning | Per legal hold | Frozen; only authorised access |
| Embeddings and indexes | Retrieval | Life of source document | Must be deletable when the source is deleted |

Points that experts get right:

- **Deletion must propagate.** If a user requests deletion, or a source document is withdrawn, every derived copy must go: caches, embeddings, indexes, evaluation samples, sampled review stores, backups on their schedule. Map the data flow and test deletion end to end.
- **Caches are data stores.** A response cache that holds personal content has a retention period and a deletion path.
- **Provider-side retention is part of your retention.** Record what each provider retains and for how long, and whether zero-retention terms apply to your account and the specific endpoints you use.
- **Redaction before storage, not after.** Redacting at read time leaves sensitive data at rest.
- **Evaluation data is production data in disguise.** Datasets built from real inputs inherit the obligations of those inputs.
- **Access to review stores is itself audited.**

```text
Deletion test (quarterly)
  1. Create a synthetic user and a synthetic document with a unique marker string.
  2. Generate traffic that touches both: calls, cache entries, traces, sampled review, feedback.
  3. Issue a deletion for the user and the document.
  4. Search every store for the marker after the stated deletion window.
  5. Any hit is a finding with an owner and a date.
```

## Capacity and economics

### Hosted versus self-hosted: the cheapest decisive experiment

If you operate models yourself, additional concerns appear: accelerator capacity and scheduling, batching and queueing, model loading time and cold starts, quantisation trade-offs, GPU memory limits and out-of-memory behaviour, autoscaling on queue depth rather than CPU, multi-tenant isolation, and supply-chain checks on model weights (provenance, scanning, pinned digests). Evaluate whether hosted APIs meet cost, latency and data-handling needs before taking on this burden. Pick the real workload, not a benchmark.

```text
Sample:      500 representative production requests (with data-handling approval), plus 50 hard cases.
Arms:        (A) hosted API, (B) self-hosted candidate on one accelerator.
Measure:     quality on the evaluation set; p50/p95 latency under realistic concurrency; cost per 1,000 requests;
             cold-start time; failure behaviour (out-of-memory, queueing); operational hours to run it for a week.
Decision:    Self-host only if quality is within tolerance AND monthly volume makes cost per request lower
             than the hosted price after including engineering time, idle accelerator cost and on-call.
```

| Factor | Hosted | Self-hosted |
| --- | --- | --- |
| Cost shape | Pay per token; scales with use | Fixed accelerator cost; cheap only at high, steady utilisation |
| Latency | Network hop; provider variability | Controllable; cold starts for model load |
| Data handling | Contractual controls; data leaves your boundary | Stays inside; you own security |
| Capacity | Provider quotas | Accelerator availability and scheduling |
| Supply chain | Provider's responsibility | You verify weights: provenance, scanning, pinned digests |

### The break-even calculation

Self-hosting converts a variable cost into a fixed one, so utilisation decides.

```text
Hosted:
  price per request = 1.2 cents                                  (illustrative blended price)
  monthly cost      = requests * 0.012

Self-hosted (illustrative):
  accelerator nodes: 2 (one active, one for redundancy) at 2,600 per node per month = 5,200
  engineering and on-call allocation                                              = 3,000
  storage, network, monitoring                                                      =   400
  fixed total                                                                       = 8,600 per month
  variable (power and other usage-based) ~ 0.1 cent per request

Break-even requests per month:
  8,600 + 0.001 * R = 0.012 * R
  R = 8,600 / 0.011 ~ 782,000 requests per month

At 300,000 requests: hosted = 3,600; self-hosted = 8,900. Hosted wins by a wide margin.
At 2,000,000 requests: hosted = 24,000; self-hosted = 10,600. Self-hosting wins -- if one node serves the peak.
```

The calculation hides three assumptions that experts check:

1. **Capacity at peak.** If peak concurrency needs four nodes rather than one, the fixed cost doubles and the break-even moves out.
2. **Quality parity.** A cheaper model that resolves fewer tasks costs more per *resolved* task.
3. **Utilisation.** An accelerator that is busy 20% of the time costs five times as much per useful request as one busy 100% of the time.

### Capacity planning for self-hosted serving

| Concept | Why it matters |
| --- | --- |
| Throughput (tokens per second per accelerator) | Sets requests per node at your output lengths |
| Concurrency and batching | Batching raises throughput but adds queueing latency |
| Time to first token and tokens per second | Two latency components users feel differently |
| Queue depth | The best autoscaling signal; CPU is misleading |
| Cold start (model load) | Scaling out takes minutes, so scale on forecasts and queue depth early |
| Headroom | Keep spare capacity for failures and spikes; a node loss should not breach the SLO |
| Context length mix | Long contexts consume memory and reduce concurrent capacity |

```text
Illustrative sizing
  peak: 40 requests/second
  mean output: 300 tokens, mean input: 1,200 tokens
  one node sustains 1,800 output tokens/second at the target latency
  required output throughput = 40 * 300 = 12,000 tokens/s  -> 12,000 / 1,800 = 6.7 -> 7 nodes
  add N+1 headroom                                      -> 8 nodes
  trough: 5 requests/second                             -> 1 node needed, 7 mostly idle unless scaled or shared
```

The gap between peak and trough is where the money goes. Options: scale on queue depth with pre-warming; run lower-priority batch work on idle capacity; or serve the peak from a hosted provider (burst to hosted) and the baseline from self-hosted capacity. The last option is attractive but forces you to maintain two evaluated paths with matching data-handling terms.

### Unit economics, worked

Cost per resolved task = (all costs) ÷ (tasks resolved without human rework). Suppose 100,000 requests/month at 1.2 cents each, a 15% retry rate, and 70% resolved first time:

```text
model cost       = 100,000 × 1.2c × 1.15           = 1,380
embedding+store  =                                    120
evaluation runs  =                                    200
total            =                                  1,700
resolved tasks   = 100,000 × 0.70                  = 70,000
cost per resolved task = 1,700 / 70,000            ~ 2.4c
```

Rank levers by effect and risk: caching repeated prefixes and answers (large, low risk if personalised content is excluded), routing easy cases to a cheaper model (large, needs quality evidence), trimming context (moderate; verify quality), then bounding retries (protects against storms, small direct saving). Raising the first-time resolution rate from 70% to 80% lowers cost per resolved task more than a 10% price discount does, so quality is a cost lever.

```text
Check: resolution 70% -> 80%
  resolved = 80,000; total cost unchanged (1,700)   -> 2.1c per resolved task   (-12.5%)
Check: 10% price discount on model cost only
  model cost = 1,242; total = 1,562; resolved 70,000 -> 2.2c                      (-8.2%)
```

### Cost engineering techniques

Break cost into inputs, outputs, retries, evaluation, embeddings and storage. Techniques: prompt caching for stable prefixes, response caching for repeated queries (with care for personalisation and freshness), routing easy requests to cheaper models, truncation and summarisation of context, batching, bounded retries, and per-feature unit economics (cost per resolved task). Alert on anomalies and on cost per outcome, not only total spend.

**Commitments and discounts.** Reserved or committed-spend agreements reduce unit price but turn variable cost into a commitment. Size a commitment to your *floor* of predictable usage, not the average, and re-check each quarter; unused commitment is pure waste, and a commitment to a model you are about to retire is worse.

**Showback and chargeback.** Attribute spend to teams through the call record. Showback (report) changes behaviour surprisingly often; chargeback (bill) requires trust in the attribution, so reconcile it first.

## Serving self-hosted models: further concerns

Additional concerns for self-hosting that interact with operations:

| Concern | Operational consequence |
| --- | --- |
| Weight provenance and integrity | Pin by digest; verify signatures or hashes; scan before promotion |
| Licence terms | Record in the inventory; check permitted uses |
| Quantisation | Changes quality and speed; a quantised model is a different model for evaluation purposes |
| Out-of-memory under long contexts | Enforce context caps *before* the server; test the limit |
| Noisy neighbours on shared accelerators | Isolate tenants or set quotas; measure tail latency |
| Model update process | Treat a weight update as a release with the same gate |
| Observability | GPU memory, queue depth, batch size, time to first token, tokens per second |

## Complex release policies

The staged rollout from earlier levels is the simplest policy. Real organisations need richer ones.

### Segmented rollout

Not all traffic is equal. Expose a change first to the segments where an error is cheapest, and last where it is costliest.

```yaml
rollout_policy: segmented-v2
segments:
  - name: internal-staff        # tolerant, can report quickly
    exposure: [100]
    hold_hours: 24
  - name: free-tier
    exposure: [5, 25, 100]
    hold_hours: [4, 12, 0]
  - name: paid-standard
    exposure: [5, 25, 100]
    hold_hours: [24, 24, 0]
  - name: regulated-customers   # last; requires explicit sign-off
    exposure: [100]
    requires: [feature_owner, security, compliance]
```

### Multi-signal gates and guard metrics

Use a primary metric (what the change aims to improve), **guard metrics** (what it must not harm) and **hard stops** (categorical safety signals).

```text
Change: new prompt aims to reduce escalations.
  primary:    escalation rate        -> expect -10% relative
  guards:     cost per request       -> <= +10%
              p95 latency            -> <= +15%
              refusal rate           -> within +/-30% of baseline
              citation validity      -> no drop > 1 point
  hard stops: any confirmed unsafe output; any secret-pattern leak; any tool denial bypass
  decision:   promote if primary improves AND all guards hold AND no hard stop,
              evaluated at pre-agreed sample sizes
```

### Experiments with proper statistics

When the question is user-visible impact (not just safety), run an A/B experiment, not a canary. A canary asks "is it broken?"; an experiment asks "is it better?".

- Decide the primary metric, the minimum detectable effect and the sample size *before* starting.
- Assign by stable identity hash; do not peek and stop early on a good-looking result without a sequential method.
- Beware **interference**: shared caches, shared rate limits and conversation history can leak effects between arms.
- Beware **novelty effects** and day-of-week effects; run at least a full weekly cycle for user-behaviour metrics.
- Report intervals, not just point estimates.

An illustrative sample-size sketch for a proportion (such as resolved-first-time): detecting a change from 70% to 73% with conventional error rates needs on the order of several thousand requests per arm. If your traffic cannot supply that in a reasonable time, use offline evaluation and a canary instead, and say so rather than declaring victory from a few hundred requests.

### Interdependent changes and release trains

When a prompt, a retrieval index and a model version change together, attribution is lost. Prefer **one change at a time** for anything that can affect behaviour. When a coordinated change is unavoidable (a new model requires a new prompt), release it as one bundle with one gate and one rollback, and label it as such in the record.

```text
Rules
  - One behavioural change per release train slot, unless declared as a bundle.
  - Freeze windows: no behavioural changes during peak events or immediately before a holiday.
  - Provider-forced changes (retirement dates) get reserved slots on the calendar, working backward from the deadline.
  - Emergency path: only subtractive changes (disable, narrow, revert).
```

### Retirement calendar and forced migrations

Providers retire models on their schedule. Make it a process.

```text
Retirement process
  T-120 days  Notice received -> register in inventory; owner assigned; candidate replacement chosen
  T-90        Replacement evaluated (dataset + canary suite + shadow); prompt adjustments identified
  T-60        Rollout to non-critical segments; cost and latency impact reviewed
  T-30        Rollout to remaining segments with segmented policy
  T-14        Old id removed from routing; verify no residual calls (gateway metrics)
  T-0         Deadline; keep rollback only if the provider still serves the id
```

### Rollback that actually works

A rollback is possible only if the previous bundle remains runnable. List the preconditions and test them:

| Precondition | How it fails | Check |
| --- | --- | --- |
| Previous model id still available | Provider retired it | Retirement calendar; periodic call test |
| Previous prompt, tool policy and config retrievable | Overwritten in place | Immutable storage; versioned artefacts |
| Previous index version intact | Index rebuilt in place | Keep N versions; alias pointer |
| Previous image digest present | Registry retention pruned it | Retention protects release-record digests |
| Data or schema compatibility | New bundle wrote data the old one cannot read | Backward-compatible changes; migration plan |
| Cache poisoned by the bad bundle | Responses cached under shared keys | Bundle version in cache key; flush by version |

Notice the last row: after rolling back, **bad answers can persist in caches** if the key does not include the bundle version. This is a common reason a rollback "did not work".

## Failure catalogue

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Provider deprecates a model | Behaviour change forced on a schedule | Track deprecation notices; scheduled re-evaluation |
| Token cost explosion | Prompt bloat, retry storms, abusive use | Budgets, caps, anomaly alerts |
| Data leakage via logs | Full prompts stored without controls | Redaction, short retention, access control |
| Undetected quality drift | No ongoing evaluation | Scheduled evaluation, canary cases |
| Kill switch that does not kill | Untested path, stale PID, wrong process | Drill regularly; use orchestrator-native controls |
| Dependency coupling | Core service blocks on the assistant | Timeouts, isolation, degradation |
| Router sends hard cases to cheap model | Weak router; blended metrics hide it | Per-tag and per-path evaluation |
| Silent fallback becomes the norm | No alert on fallback share | Fallback-share alert; state visible |
| Rollback serves stale bad answers | Cache key lacks bundle version | Version in key; flush on rollback |
| Evaluation overfit | Prompt tuned to the dataset | Held-out set; production sampling |
| Gate relaxed in the same change | Dataset or margin edited with the release | Pin dataset version; separate review |
| Deletion that does not propagate | Copies in caches, indexes, review stores | End-to-end deletion test |
| Reviewer rubber-stamping | Volume too high, time too short | Measure rejection rate and review time |
| Capacity cliff at peak | Sizing on average load | Size on peak with headroom; queue-depth scaling |

## Case catalogue

### Case 1 — The alias that moved

A feature calls `provider-a/large` with no date. One Thursday the provider points the alias at a newer model. Answers get longer and cite less. No release occurred, so nothing in the deployment history explains it; the nightly canary suite does, falling six points. Lesson: pin dated ids, run scheduled evaluation, and record `served_by` on every call.

### Case 2 — The fallback nobody noticed

A provider has intermittent timeouts for two weeks. The gateway fails over to a second provider for 35% of traffic. Costs rise and a few answers regress on billing questions, because the second path was evaluated only on the general dataset. No alert fires because success rate is steady. Lesson: alert on fallback share and evaluate each path per tag.

### Case 3 — The rollback that did not roll back

After a bad release, the team rolls back the bundle. Complaints continue for an hour. The response cache is keyed by question and index version only; entries created by the bad prompt keep being served. Lesson: include the bundle version in the key and flush by version on rollback.

### Case 4 — The cheap router

A router sends requests it classifies as "simple" to a small model. The classifier is trained on a dataset that underrepresents refund disputes, so disputes go to the small model. Overall pass rate drops by one point, within noise; the dispute tag drops by 20. Lesson: gate on per-tag pass rate and report by path.

### Case 5 — The review that approved everything

A high-stakes drafting tool requires an agent to approve each draft. After a volume increase, review time falls to four seconds and the rejection rate to under one percent. An audit finds an incorrect policy statement approved hundreds of times. Lesson: measure the human control; reduce volume per reviewer or change the design.

### Case 6 — The deletion that left a copy

A user's deletion request is honoured in the primary database. The sampled-review store, the embedding index and the response cache keep derived copies for weeks. A quarterly deletion test with a marker string finds them. Lesson: map derived data and test deletion end to end.

### Case 7 — The commitment to a retiring model

A team signs a 12-month spend commitment at a discount for a model the provider retires in five months. The replacement is priced differently and the commitment is only partially usable. Lesson: tie commitments to the retirement calendar and size them to a stable floor.

### Case 8 — The idle accelerators

A self-hosted deployment is sized for a launch peak. Steady traffic is a fifth of the peak and cost per request is five times the estimate. Lesson: size on measured peak and trough, scale on queue depth, share capacity with batch work or burst to a hosted path.

## Expert trade-offs

| Axis | One end | Other end | How an expert decides |
| --- | --- | --- | --- |
| Single provider versus multi-provider | Simplicity, deep integration | Resilience, leverage, more evaluation work | Criticality of the feature and a rehearsed exit; do not add a provider you will not evaluate |
| Gateway versus library | Central control and attribution | Fewer moving parts | Number of teams, need for policy enforcement, ability to staff on-call |
| Hosted versus self-hosted | Low fixed cost, vendor dependence | Control, fixed cost, operational burden | Volume, utilisation, data-handling constraints, quality parity measured on your workload |
| Content capture versus privacy | Evidence for review and incidents | Minimal data at rest | Tiered capture, short retention, access audit |
| Gate strictness versus delivery speed | Block on small regressions | Fast shipping | Strict on must-not-break; margin above measured noise |
| Automation versus human oversight | Automatic actions | Human approval | Tier; measured effectiveness of the human control |
| Canary versus experiment | Safety check | Impact measurement | Ask "is it broken?" or "is it better?" and size accordingly |
| Commitments versus flexibility | Lower unit price | Freedom to move | Commit to the stable floor; align with retirement dates |

A useful expert habit is to **write the sentence before choosing**: "We accept *cost* to reduce *specific risk*, and we will know it failed when *observable signal*." If you cannot complete that sentence, the control is cargo cult.

## Operating model

Define ownership (product, platform, security, data), service levels for the AI feature, an intake process for new AI use cases with risk assessment, an inventory, and a review cadence. Keep a retirement process: unused features are removed, keys revoked and data deleted.

**Drift metrics that move before users complain.**

| Signal | What it tells you |
| --- | --- |
| Scheduled evaluation pass rate (canary suite every night) | Behaviour regression, provider change |
| Refusal and abstention rate versus baseline | Prompt or model shift; abuse |
| Citation validity rate | Retrieval or grounding failure |
| Output length and schema-failure rate | Format drift |
| Thumbs-down or escalation rate | User-visible quality |
| Input distribution (topics, languages, lengths) | New traffic the prompts never saw |

**Operating model, minimum contents.**

```text
Owners:          product (outcomes), platform (gateway/serving), security (risk review), data (sources).
Intake:          one page: purpose, data classes, users, actions the model can take, risk tier, evaluation plan.
Tiering:         low (read-only, internal) -> approval by team lead; high (actions, customer data) -> security review.
Inventory:       feature, owner, version bundle, data flows, last evaluation date, limitations.
Review cadence:  quarterly per feature; immediate after incidents or provider deprecation notices.
Retirement:      no traffic for 90 days -> remove, revoke keys, delete data and indexes, update inventory.
```

## Knowledge consolidation

- Operate what you cannot fully specify by making decisions **reconstructible**, changes **reversible**, dependencies **substitutable** and costs **attributable**.
- A **standard call record** with intended and actual route makes cross-team analysis honest.
- **Multi-provider** operation multiplies evaluation: prompt-model pairs are the unit; data classes constrain routes; fallback depth and share are bounded and alerted; exit is rehearsed.
- **Distribution shift** has kinds; detect with summaries and distances, confirm with two independent signals, and choose update, constrain or stop in advance.
- **High-stakes incident response** is contain, preserve, scope; the evidence must exist beforehand, and human controls must be measured.
- **Governance** is intake, tiering, an authoritative inventory, policy as code and separation of duties; legal owns meaning, engineering owns enforcement.
- **Retention** is a data lifecycle: tiered capture, propagated deletion, caches and provider retention included, tested end to end.
- **Capacity economics** is utilisation: compute break-even, size on peak and trough, and judge by cost per *resolved* task.
- **Release policy** can be segmented, guarded by primary, guard and hard-stop metrics, experiment-based where impact is the question, and calendar-driven for forced migrations.
- **Rollback** works only if every identity, including caches, can return.

## Exercises

**Exercise 1 — Call record.** Define the standard call record for your organisation. Instrument one feature to emit it with `route.served_by`. Produce a report of cost by team and by model from the records alone.

**Exercise 2 — Route and evaluate.** Write a routing policy with a primary, a fallback and a shadow. Evaluate each path per tag, then evaluate the system with the primary failing at 100% and at 30%. Report pass rate, latency and cost under each fault.

**Exercise 3 — Exit rehearsal.** Run a one-week mirrored-traffic rehearsal to an alternative provider for one feature. Produce the cutover plan with an effort estimate and a blockers list.

**Exercise 4 — Shift detection.** Compute topic-mix PSI week on week for your traffic (or a synthetic stream). Define in advance the response to each band, then inject a synthetic shift and show the alert and the chosen response.

**Exercise 5 — Incident game day.** Simulate a high-stakes incident: a report that a draft contained incorrect advice. Measure time to contain, to preserve evidence and to scope affected requests. List what evidence was missing.

**Exercise 6 — Human control.** For a feature with human approval, compute rejection rate and median review time for a week. Decide whether the control is effective, and what you would change.

**Exercise 7 — Policy as code.** Implement three policies (data-class routing, retention, review overdue) and test each with a passing and a failing example, at deploy time and run time.

**Exercise 8 — Deletion test.** Run the marker-string deletion test across traffic, cache, traces, review store and index. Report every store where the marker persists.

**Exercise 9 — Break-even.** Using your own numbers, compute break-even volume for self-hosting, including peak sizing and headroom. State the three assumptions most likely to be wrong.

**Exercise 10 — Release policy.** Write a segmented release policy with primary, guard and hard-stop metrics for a real change. Run it on a synthetic regression and show where it stops.

**Solution notes.**

*Exercise 1.* If cost by model does not reconcile with the invoice, check for traffic outside the instrumented path and for retries recorded as separate calls. The point of the report is to show that attribution works without anyone's memory.

*Exercise 2.* Expect the fallback path to show a lower pass rate on at least one tag. The finding is not that it is lower, but whether the loss is within a tolerance you accepted in advance. At a 30% error rate on the primary, latency usually rises more than pass rate falls, because retries and fallbacks add time.

*Exercise 3.* Typical blockers: prompts tuned to the old model, tool-schema differences, tokenizer-driven truncation, and data-handling terms that were never reviewed for the alternative. A rehearsal that reports no blockers has probably not looked hard enough.

*Exercise 4.* PSI above your chosen band should trigger the pre-agreed response (such as a dataset review), not an automatic change. If you cannot say what the alert causes, remove it or define the response.

*Exercise 5.* Common gaps: no record of retrieved context ids, no routing decision, content already deleted by routine retention, and no named incident commander. Each gap becomes an action item with an owner.

*Exercise 6.* A median review time of a few seconds with a near-zero rejection rate indicates rubber-stamping. Options: reduce volume per reviewer, sample instead of reviewing all, add targeted checks, or redesign the workflow so the system escalates uncertain cases only.

*Exercise 7.* A policy that has never failed a test is untested. Include a negative example for each, and check the run-time path as well as the pipeline.

*Exercise 8.* Expect at least one surprising store (a cache, a feedback table or a backup). Record when it will expire naturally and decide whether that is acceptable.

*Exercise 9.* The most fragile assumptions are usually peak concurrency, quality parity on hard cases and utilisation. Recompute with a pessimistic value for each.

*Exercise 10.* The policy should stop on the guard or hard-stop metric you injected, at the sample size you pre-agreed. If it needed a person to notice, add the missing metric or threshold.

**Mentoring prompts.** How would you prove that your kill switch works without waiting for an incident? What metrics would tell you that quality has drifted before users complain? What is the cheapest experiment to decide between a hosted API and self-hosting? If your primary provider vanished tomorrow, how many weeks until you were serving traffic elsewhere, and how do you know? Which of your human review controls would still work at ten times the volume?
