# T-AIE-05-E — Expert Depth

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-e"></a>
#### T-AIE-05-E — Expert Depth

**Platform architecture for AI at scale.** A central gateway in front of model providers provides authentication, per-team quotas, cost attribution, caching, prompt and response logging with redaction, policy filters, model routing and fallbacks, and a single place to rotate keys or switch providers. The trade-off is an additional critical dependency and a team to run it. Standardise the telemetry schema for AI calls so every team's dashboards and cost reports are comparable.

**Serving self-hosted models.** If you operate models yourself, additional concerns appear: accelerator capacity and scheduling, batching and queueing, model loading time and cold starts, quantisation trade-offs, GPU memory limits and out-of-memory behaviour, autoscaling on queue depth rather than CPU, multi-tenant isolation, and supply-chain checks on model weights (provenance, scanning, pinned digests). Evaluate whether hosted APIs meet cost, latency and data-handling needs before taking on this burden.

**Cost engineering.** Break cost into inputs, outputs, retries, evaluation, embeddings and storage. Techniques: prompt caching for stable prefixes, response caching for repeated queries (with care for personalisation and freshness), routing easy requests to cheaper models, truncation and summarisation of context, batching, bounded retries, and per-feature unit economics (cost per resolved task). Alert on anomalies and on cost per outcome, not only total spend.

**Managing change safely**

| Technique | Use |
| --- | --- |
| Shadow mode | Run a candidate on real traffic without showing results; compare |
| Canary | Expose a small percentage; auto-rollback on metric regression |
| A/B experiments | Measure user-visible impact with proper statistics |
| Version-pinned rollbacks | Redeploy a previous bundle without code changes |
| Evaluation on production samples | Detect real-world drift with privacy controls |

**Failure catalogue**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Provider deprecates a model | Behaviour change forced on a schedule | Track deprecation notices; scheduled re-evaluation |
| Token cost explosion | Prompt bloat, retry storms, abusive use | Budgets, caps, anomaly alerts |
| Data leakage via logs | Full prompts stored without controls | Redaction, short retention, access control |
| Undetected quality drift | No ongoing evaluation | Scheduled evaluation, canary cases |
| Kill switch that does not kill | Untested path, stale PID, wrong process | Drill regularly; use orchestrator-native controls |
| Dependency coupling | Core service blocks on the assistant | Timeouts, isolation, degradation |

**Organisational model.** Define ownership (product, platform, security, data), service levels for the AI feature, an intake process for new AI use cases with risk assessment, an inventory, and a review cadence. Keep a retirement process: unused features are removed, keys revoked and data deleted.

**Central gateway: argue both sides with a decision table.**

| Question | Evidence for a gateway | Evidence against |
| --- | --- | --- |
| How many teams call models? | Five or more teams with separate keys and bills | One or two teams with a shared library |
| Is spend or data handling a concern? | Need per-team budgets, redaction, audit | Low spend, low-risk data |
| Do you need provider portability? | Plan to route and fall back across providers | Single provider accepted |
| Who would run it? | A platform team with on-call and a roadmap | No owner: it becomes a fragile shared dependency |
| What is the latency budget? | Added hop of a few milliseconds is acceptable | Real-time use with a very tight budget |

A gateway is a new tier-1 dependency: it needs its own SLO, capacity plan, rate limits per team, a bypass or fail-open/fail-closed decision documented per use case, and a release process as careful as any shared service. If nobody can staff that, a shared client library with common telemetry may deliver most of the value at lower risk.

**Hosted versus self-hosted: the cheapest decisive experiment.** Pick the real workload, not a benchmark.

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

**Unit economics, worked.** Cost per resolved task = (all costs) ÷ (tasks resolved without human rework). Suppose 100,000 requests/month at 1.2 cents each, a 15% retry rate, and 70% resolved first time:

```text
model cost       = 100,000 × 1.2c × 1.15           = 1,380
embedding+store  =                                    120
evaluation runs  =                                    200
total            =                                  1,700
resolved tasks   = 100,000 × 0.70                  = 70,000
cost per resolved task = 1,700 / 70,000            ~ 2.4c
```

Rank levers by effect and risk: caching repeated prefixes and answers (large, low risk if personalised content is excluded), routing easy cases to a cheaper model (large, needs quality evidence), trimming context (moderate; verify quality), then bounding retries (protects against storms, small direct saving). Raising the first-time resolution rate from 70% to 80% lowers cost per resolved task more than a 10% price discount does, so quality is a cost lever.

**Proving a kill switch without an incident.** Drill it on a schedule, in production-like conditions: flip the switch, confirm within a stated time that (1) the health response reports disabled, (2) no model calls leave the service (provider-side or gateway metrics show zero), (3) users receive the documented refusal, (4) the core service remains healthy, then re-enable and confirm recovery. Use the orchestrator's native control (scale to zero, config flag via the deployment system) instead of a PID file or manual process kill, which can silently target the wrong process. Record the drill's timings; a switch that takes 40 minutes to work is not a kill switch.

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

**Mentoring prompts.** How would you prove that your kill switch works without waiting for an incident? What metrics would tell you that quality has drifted before users complain? What is the cheapest experiment to decide between a hosted API and self-hosting?

---
