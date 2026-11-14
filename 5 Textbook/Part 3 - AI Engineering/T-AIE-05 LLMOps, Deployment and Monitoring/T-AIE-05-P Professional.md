# T-AIE-05-P — Professional Engineering

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-p"></a>
#### T-AIE-05-P — Professional Engineering

**Release management for AI features.**

| Change | Risk | Release practice |
| --- | --- | --- |
| Prompt edit | Behaviour shift | Evaluation gate; staged rollout; version tag in logs |
| Model version bump | Behaviour, latency, cost | Regression suite; canary percentage; rollback pin |
| Tool policy change | Safety | Security review; deny-path tests |
| Corpus or index change | Accuracy | Retrieval evaluation; versioned index |
| Parameter change (temperature, limits) | Behaviour, cost | Treated as a release, not a tweak |

Gate pipelines on the evaluation: re-run on the candidate code, assert failure count and minimum case count, and archive the report with the release record. Use feature flags or percentage rollouts for gradual exposure; keep the previous bundle deployable.

**Observability for LLM features**

| Signal | Why |
| --- | --- |
| Latency by stage (retrieval, model, tools) | Find the slow part |
| Tokens in and out; cost per request and per user | Spend control |
| Outcome mix: answered, refused, no-match, error, limited | Behavioural drift |
| Citation rate and no-match rate | Retrieval health |
| Tool call counts and denials | Safety and misuse |
| User feedback and escalation | Quality in the field |
| Provider errors and timeouts | Dependency health |

Use the same tracing and metrics stack as the rest of the system (see T-DEV-06): a trace per request with spans for retrieval, model and tools; metrics with low-cardinality labels; alerts on error rates, latency and cost anomalies; and SLOs for availability and latency of the feature. Be careful with content: prompts and answers can contain sensitive data, so log hashes, sizes and categories by default and gate full-content capture by policy with short retention and access control.

**Resilience.** Timeouts and retries with jitter for provider calls; fallbacks (a smaller model, cached answers, a polite "unavailable" response); circuit breakers; bulkheads so the assistant cannot starve the core service; and graceful degradation: the core product works without the assistant.

**Security and compliance.** Keys in a secret manager, rotated; egress restricted to approved provider endpoints; data processing agreements reviewed; PII minimisation; audit logs; and documented data flows. Pin dependencies; scan the service like any other.

**Runbook for the feature.** Contents: how to disable and re-enable; how to roll back a bundle; how to read the dashboard; provider outage procedure; cost spike procedure; a suspected unsafe output procedure (disable, preserve evidence, add an evaluation case, review).

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Know what ran | Bundle version and git sha in every log line | Unversioned prompts |
| Stop quickly | One scripted action, tested | Multi-step improvisation |
| Control spend | Limits and budgets per identity | Trusting the provider's bill to alert you |
| Detect drift | Outcome-mix metrics and scheduled evaluation | Waiting for complaints |
| Survive provider outages | Timeouts, fallbacks, degradation | Blocking the core service |
