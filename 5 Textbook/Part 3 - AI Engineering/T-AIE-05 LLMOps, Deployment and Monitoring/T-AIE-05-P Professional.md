# T-AIE-05-P — Professional Engineering

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-p"></a>
#### T-AIE-05-P — Professional Engineering

## Why this matters

At Intermediate level one engineer can ship a change carefully: run the evaluation, roll out to a few users, watch the dashboard, roll back if needed. Professional practice is what remains true when there are several engineers, several releases a week, a finance team asking about spend, a security team asking about misuse, and a customer-facing commitment about availability.

The professional questions are about **systems of control**, not individual techniques. Who is allowed to release a prompt change, and what evidence must they attach? What happens automatically when the pass rate falls? Who gets paged when cost per hour triples at 03:00, and what are they allowed to do about it? How do you know quality has drifted when nobody has complained? When a fallback engages, who knows, and who decides to stop it?

This section assumes the Beginner and Intermediate material: version bundles, evaluation datasets, staged rollout, token accounting, tracing, caching, rate limits and basic triage. It focuses on eval-gated releases, drift detection, cost ceilings, escalation, safety monitoring, fallback design, ownership and reliability. The running example is a customer-support assistant called `support-assist` with a retrieval index and three read-only tools. All numbers, thresholds and names are illustrative.

## First principles: an AI release is a release of behaviour

A conventional release changes code, and tests describe expected behaviour. An AI release changes *behaviour that tests only sample*. Two consequences follow, and they shape everything else here.

1. **Passing tests is evidence, not proof.** An evaluation covers a finite set of cases; production covers the world. Release practice must therefore combine pre-release evaluation, staged exposure and post-release monitoring. No one of the three is enough.
2. **Everything that shifts behaviour is a release.** Prompt edits, model version changes, tool policy changes, index rebuilds and parameter tweaks all need the same discipline. The cheap-looking change ("just a temperature tweak") is the one most often shipped without a gate.

| Change | Risk | Release practice |
| --- | --- | --- |
| Prompt edit | Behaviour shift | Evaluation gate; staged rollout; version tag in logs |
| Model version bump | Behaviour, latency, cost | Regression suite; canary percentage; rollback pin |
| Tool policy change | Safety | Security review; deny-path tests |
| Corpus or index change | Accuracy | Retrieval evaluation; versioned index |
| Parameter change (temperature, limits) | Behaviour, cost | Treated as a release, not a tweak |
| Provider-side change under a stable id | Behaviour, silently | Scheduled evaluation; drift alerts |

## Eval-gated releases

A **gate** is an automated check that a release cannot pass without evidence. The evaluation gate is the central one, but it works only if it is specific.

### Anatomy of a gate

```text
Gate: evaluation (runs in CI on the candidate bundle)
  inputs:      candidate bundle, dataset version D, baseline results B (from the last released bundle on D)
  assertions:
    - case count >= 200                                  (guards against a gutted dataset)
    - all "must-not-break" cases pass                    (refusals, secret handling, tool denials)
    - pass rate overall >= baseline - 1.0 point
    - pass rate per tag  >= baseline - 3.0 points
    - mean output tokens <= baseline * 1.15              (cost guard)
    - p95 latency (staging, fixed load) <= baseline * 1.20
  outputs:     report archived with the release record; pass/fail status on the pull request
```

Design principles:

- **Compare to a baseline, not only to a threshold.** An absolute threshold ("90%") is blind to a drop from 98%. A relative one catches it.
- **Assert the case count.** Otherwise someone can make the gate pass by deleting hard cases.
- **Separate must-not-break from nice-to-have.** A drop in a stylistic tag is a discussion. A failure on a secret-handling case is a block.
- **Pin the dataset version in the gate, and change the dataset in its own reviewed change.** Otherwise a release can pass by relaxing the dataset in the same pull request.
- **Measure noise.** Run the baseline on the same dataset several times and record the spread. A gate tighter than the noise will fail randomly and be bypassed.

### Handling model non-determinism in the gate

```python
def gate(candidate_runs, baseline_runs, margin):
    """Each *_runs is a list of per-run pass rates on the same dataset version."""
    cand = sum(candidate_runs) / len(candidate_runs)
    base = sum(baseline_runs) / len(baseline_runs)
    spread = max(baseline_runs) - min(baseline_runs)
    allowed_drop = max(margin, spread)          # never tighter than the measured noise
    return cand >= base - allowed_drop
```

Three to five runs per side is typically enough to see the noise. Record the runs, not only the mean.

### Model-graded evaluation, carefully

Some qualities (helpfulness, tone, faithfulness to retrieved text) cannot be checked by string matching. A second model can grade them, but treat the grader as a measuring instrument that needs calibration:

| Practice | Why |
| --- | --- |
| Pin and version the grader model and its prompt | A changing grader makes results incomparable |
| Calibrate on 50 to 100 human-labelled cases; record agreement | Know how far to trust it |
| Use the grader for relative comparisons, not absolute claims | Graders have systematic bias |
| Keep mechanical checks for anything mechanical | Cheaper, deterministic |
| Spot-check disagreements by hand each release | Catch grader failure modes |

### The release record

Every release produces a record that can be read months later:

```yaml
release: support-assist-2026-04-02-a
bundle_version: 2.3.0
git_sha: <commit>
image_digest: sha256:<digest>
model_id: example-model-2026-01
prompt_version: support-prompt-2026-04
tools_policy_version: tools-allow-v5
index_version: idx-2026-04-01
config_version: generation-config-v7
dataset_version: eval-set-2026-04
eval_report: reports/2026-04-02-a.json
baseline: support-assist-2026-03-26-b
approvals: [product, security]      # security required because tools policy changed
rollout: {dark: 0, canary: 5, steps: [25, 100]}
previous_bundle_deployable_until: 2026-04-09
```

The release record is the thing you read during an incident to answer "what changed?". If it cannot answer that in a minute, improve it.

### Release policies by change type

| Change type | Gate | Rollout | Approvers |
| --- | --- | --- | --- |
| Prompt text, low-risk | Full evaluation | 5%, 25%, 100% over one day | Feature owner |
| Model version bump | Full evaluation plus shadow comparison | 5% for 24 hours, then staged | Feature owner and platform |
| Tool policy widening | Evaluation plus deny-path tests plus review | 1% for 48 hours | Feature owner and security |
| Index rebuild | Retrieval evaluation (recall on known questions) | Swap index version behind a flag | Content owner |
| Emergency fix (disable a behaviour) | Smoke test only | Immediate | On-call, reviewed next day |

An emergency path must exist, and it must be *narrow*: it may remove or disable behaviour, but should not add new capabilities without the full gate.

## Staged rollout with automatic decisions

A canary that relies on a person watching a dashboard fails at 02:00. Encode the decision:

```yaml
canary:
  steps: [5, 25, 100]
  hold_minutes: [30, 120, 0]
  min_requests_per_step: 500
  abort_if:
    - metric: error_rate
      op: ">"
      value: baseline + 1.0pp
    - metric: p95_latency_ms
      op: ">"
      value: baseline * 1.25
    - metric: cost_per_request
      op: ">"
      value: baseline * 1.20
    - metric: refusal_rate
      op: outside
      value: [baseline * 0.7, baseline * 1.3]
    - metric: schema_failure_rate
      op: ">"
      value: 0.5pp
  on_abort: rollback_to_previous_and_page_owner
```

The `min_requests_per_step` line matters. Without enough traffic a canary makes no statistical sense, and a quiet period at 5% can pass trivially. For low-volume features, use longer holds or run evaluation on sampled production inputs rather than relying on live metrics alone.

## Drift

**Drift** is the gradual or sudden change in a feature's behaviour or inputs without a release you made. In an LLM feature, there are four common sources, and each has a different signal.

| Source | Example | Signal |
| --- | --- | --- |
| Model drift | Provider updates behaviour behind an id; or retires one | Scheduled evaluation pass rate; output length; refusal rate |
| Input drift | New product launch brings new vocabulary and languages | Input topic, length and language distribution |
| Knowledge drift | Documents change; the index is stale or rebuilt | Citation validity; no-match rate; retrieval evaluation |
| Behavioural drift from your own change | A "small" config tweak | Release-correlated shifts in outcome mix |

### Scheduled evaluation

Run a **canary suite** (a small, stable, high-signal subset of the evaluation dataset) on a schedule against the production configuration, independent of releases. If the pass rate drops with no release, the provider or the data changed.

```text
Nightly canary suite
  cases:        60 (the must-not-break set plus 30 representative cases)
  frequency:    every 24 hours, and after every provider notice
  runs:         3 per case, record pass counts
  alert:        pass rate < baseline - noise margin for 2 consecutive runs -> page the feature owner
  record:       results keyed by date, bundle_version, model_id
```

### Production sampling

Offline evaluation misses what real users ask. Sample a small fraction of production requests (with consent and the privacy controls from the security section below), grade them (automatically where possible, by humans for a smaller subset), and track the trend. Sampled evaluation answers "is the dataset still representative?" as much as "is the feature still good?". When sampled failures fall outside what the dataset covers, add them.

### Input distribution monitoring

```text
Weekly input profile
  topic mix (classifier labels):   share per topic, compared with the last 4 weeks
  language mix:                    share per language
  input length:                    median and p95 tokens
  no-match rate by topic:          which topics the index cannot answer
  alert:                           any topic share changes by more than 5 points week on week
```

A shift that appears here *before* quality metrics move is the early warning. When it fires, ask whether the dataset, the index or the prompt needs new cases.

## Cost ceilings

Monitoring cost after the fact is a report; a **cost ceiling** is a control. Define ceilings at several scopes, with a different action at each.

| Scope | Ceiling | Action when approached (80%) | Action when reached |
| --- | --- | --- | --- |
| Request | Maximum input and output tokens | Log; truncate context | Reject or truncate |
| Identity | Tokens per window | Warn in response headers | 429 `budget_exceeded` |
| Feature per hour | Cost per hour | Page owner; tighten rate limits | Degrade (smaller model, shorter context) |
| Feature per day or month | Budget | Notify owner and finance | Disable non-essential paths; require approval to continue |
| Whole account | Provider-side spend cap if available | Page platform | Fail closed for non-critical features |

```python
def admit(identity, feature, est_cost):
    if spend.hour(feature) + est_cost > CEILING_HOUR[feature]:
        return Decision.DEGRADE        # cheaper path, still serves
    if spend.day(identity) + est_cost > CEILING_DAY_PER_IDENTITY:
        return Decision.REJECT
    return Decision.ALLOW
```

Design notes:

- **Prefer degrade to reject for the whole feature.** Rejecting everyone because of one heavy user is an outage you built yourself.
- **Count retries and agent loops.** The worst bill spikes come from loops (an agent that calls tools repeatedly, or a client that retries on a malformed response).
- **Bound tool-loop depth** and total tokens per conversation.
- **Alert on cost per outcome**, not only total spend. A rise in cost per resolved task with flat total spend means quality fell.
- **Separate evaluation spend.** An evaluation job that runs every commit can quietly become your largest cost; give it its own budget.
- **Test the ceiling.** In a staging environment with a low ceiling, confirm that approaching it degrades and reaching it rejects, and that alerts fire.

## Escalation

Monitoring that does not reach a person with authority is decoration. Define who is told, how fast, and what they may do.

```text
Severity 1  Unsafe output reaching users, data exposure, or total feature outage on a critical path
            page: on-call + feature owner + security (immediately)
            authority: on-call may disable the feature without approval
Severity 2  Quality or cost materially worse; fallback engaged for > 30 minutes
            page: feature owner during hours; on-call after hours
            authority: roll back the last bundle; engage fallback
Severity 3  Drift signal, canary failure, elevated no-match rate
            ticket: feature owner, next working day
            authority: block further releases until reviewed
```

Principles:

- **Authority is pre-granted.** On-call must not need to find a manager to press the stop button. If the kill switch needs approval at 03:00 it will not be used.
- **Escalate on categories, not only thresholds.** "Any confirmed unsafe output" is Severity 1 regardless of volume.
- **Give the first responder a decision tree**, not a dashboard tour:

```text
Alert: refusal rate dropped to near zero
  1. Did a release go out in the last 24h?           yes -> roll back, then investigate
  2. Is the safety check still invoked?              no  -> disable feature; Severity 1
  3. Does the canary suite's refusal tag pass?       no  -> disable feature; Severity 1
  4. Otherwise                                       -> Severity 3, owner reviews sampled outputs
```

- **Close the loop.** After every incident add an evaluation case, a gate rule or an alert. If none of those changed, the incident will recur.

## Safety monitoring

Safety is monitored continuously because evaluation covers only what you thought of.

| Signal | What it can show | Typical handling |
| --- | --- | --- |
| Tool-call denials by tool and identity | Probing, misconfigured policy | Alert on spikes; review top identities |
| Output-filter hits by category | Unsafe or sensitive content attempts | Trend per release; sample for review |
| Prompt-injection indicators in retrieved content or inputs | Attack or poisoned documents | Quarantine sources; add evaluation cases |
| Secret or personal-data patterns in outputs | Leakage | Block, count, Severity 1 if reached users |
| Refusal rate versus baseline | Safety checks weakened or over-tight | Alert both directions |
| Actions requested versus actions taken (for tools with side effects) | Policy bypass | Reconcile with audit logs |
| User reports ("this was wrong or unsafe") | What automation missed | Triage queue with a response-time target |

A practical set-up:

```text
1. Defence in the path: input checks, tool allow-list, output filters (fail closed).
2. Counters for each defence: invoked, triggered, bypassed (by design) -- a defence that is never invoked is a finding.
3. Sampled human review: e.g. 50 outputs a week, stratified by outcome and by tool use.
4. A report-an-answer button and a triage queue with an owner.
5. Every confirmed issue adds an evaluation case and, where relevant, a filter rule.
```

Logging content for review conflicts with privacy. Resolve it with policy: default to hashes, sizes and categories; capture full content only for sampled or flagged requests, with redaction, restricted access and short retention. Review access should itself be logged.

## Fallbacks and degradation design

Intermediate level introduced a fallback chain. Professionally, each fallback is a *designed state* with an owner, an evaluation and a way out.

| State | Trigger | Behaviour | Who knows | Exit |
| --- | --- | --- | --- | --- |
| Normal | Healthy | Primary model, full context | Dashboard | n/a |
| Degraded-A | Primary p95 above target, or hourly cost ceiling approached | Shorter context; smaller output cap | Metric and annotation on dashboards | Primary healthy for 15 minutes |
| Degraded-B | Primary error rate high | Alternative model (evaluated) | Ticket opened automatically | Primary healthy for 30 minutes, manual confirmation |
| Cached-only | All models failing | Serve valid cached answers; others get "unavailable" | Page | Manual |
| Off | Kill switch or safety event | Refusal message | Page | Manual after review |

Rules for fallback design:

1. **Evaluate every fallback on the dataset** and record its pass rate. A fallback may be lower quality, but you must know *how* much.
2. **Make state visible.** Put the current state in a metric, a health field and a dashboard annotation. Silent degradation is how a "temporary" fallback runs for six weeks.
3. **Use hysteresis.** Require sustained health before returning to normal, otherwise the system flaps.
4. **Do not fall back across a policy boundary.** A fallback provider must satisfy the same data-handling requirements as the primary; otherwise a failure becomes a compliance event.
5. **Fail closed for actions.** If the safety layer is unavailable, tools with side effects must be disabled, not allowed.
6. **Test with injected faults.** Use a fault-injecting fake provider in staging to prove each transition.

## Reliability engineering for AI features

### Service levels

An AI feature needs service levels that reflect both availability and quality.

| SLI | Definition | Example SLO |
| --- | --- | --- |
| Availability | Share of requests that receive a non-error response | 99.5% over 30 days |
| Latency | Share of requests completed under a target | 95% under 4 s |
| Quality (proxy) | Canary suite pass rate; sampled graded pass rate | Canary at or above baseline minus margin |
| Safety | Confirmed unsafe outputs reaching users | Zero, with any occurrence reviewed |
| Cost efficiency | Cost per resolved task | Within budget band |

Count a degraded-but-served response as available but track the share of traffic served in degraded states as its own indicator. An **error budget** (the allowed amount of unreliability) then works as usual: when it is spent, slow down releases and prioritise reliability work.

### Isolation and dependency control

- **Bulkheads.** Give the assistant its own worker pool, connection pool and rate limits so a slow provider cannot starve the core service.
- **Timeouts at every layer**, with the outer timeout larger than the sum of inner ones, so budgets compose.
- **Circuit breaker** on the provider call:

```python
class Breaker:
    def __init__(self, threshold=5, reset_s=30):
        self.fail, self.threshold, self.reset_s, self.opened = 0, threshold, reset_s, None
    def allow(self):
        if self.opened and time.monotonic() - self.opened < self.reset_s:
            return False
        return True
    def record(self, ok):
        if ok:
            self.fail, self.opened = 0, None
        else:
            self.fail += 1
            if self.fail >= self.threshold:
                self.opened = time.monotonic()
```

- **Idempotency for actions.** If the assistant triggers a side effect and the call is retried, the action must not run twice.
- **Load shedding.** Under overload, drop low-priority traffic (batch, evaluation) before interactive requests.

### Observability

Use the same tracing and metrics stack as the rest of the system (see T-DEV-06): a trace per request with spans for retrieval, model and tools; metrics with low-cardinality labels; alerts on error rates, latency and cost anomalies; and SLOs for availability and latency of the feature. Be careful with content: prompts and answers can contain sensitive data, so log hashes, sizes and categories by default and gate full-content capture by policy with short retention and access control.

| Signal | Why |
| --- | --- |
| Latency by stage (retrieval, model, tools) | Find the slow part |
| Tokens in and out; cost per request and per user | Spend control |
| Outcome mix: answered, refused, no-match, error, limited | Behavioural drift |
| Citation rate and no-match rate | Retrieval health |
| Tool call counts and denials | Safety and misuse |
| Fallback state and time in state | Hidden degradation |
| User feedback and escalation | Quality in the field |
| Provider errors and timeouts | Dependency health |

## Ownership

Without named owners, every alert is someone else's problem.

| Role | Owns | Typical decisions |
| --- | --- | --- |
| Feature owner (product/engineering) | Outcomes, release approvals, evaluation dataset content | Ship or hold; accept a quality trade-off |
| Platform | Serving, gateway or client library, telemetry schema, rollout tooling | Capacity, provider contracts, shared limits |
| Security | Tool policy, data flows, safety review | Approve tool widening; accept residual risk |
| Data/content owners | Sources and index freshness | Retire or fix documents |
| On-call | Immediate response | Disable, roll back, engage fallback |
| Finance or FinOps | Budget bands | Approve ceiling changes |

Document ownership in a one-page service record per feature:

```yaml
service: support-assist
owner_team: support-engineering
escalation: [oncall-support-ai, security-oncall]
tier: 2
data_classes: [customer-messages, internal-docs]
tools: [lookup_order (read), search_kb (read), draft_reply (write-draft)]
dashboards: [support-assist-overview, support-assist-cost]
runbook: runbooks/support-assist.md
slos: {availability: 99.5, latency_p95_s: 4, canary_pass_rate: ">= baseline - 2pp"}
budget: {month_usd: 4000, ceiling_hour_usd: 15}
last_kill_switch_drill: 2026-03-20
last_full_review: 2026-02-28
```

## Security, privacy and compliance in operation

Keys live in a secret manager and are rotated; egress is restricted to approved provider endpoints; data processing agreements are reviewed before a new provider is used; personal data is minimised before it reaches a prompt; audit logs record who changed which bundle; and data flows are documented. Pin dependencies, and scan the service like any other.

| Control | Operational check |
| --- | --- |
| Key rotation | Drill: rotate in staging; confirm no outage and no key in logs |
| Egress allow-list | Attempt a call to an unapproved host; confirm it fails |
| Log redaction | Send a known fake secret; confirm it never appears in logs or traces |
| Retention | Confirm that content captured for review is deleted on schedule |
| Access to captured content | Review the access log monthly |
| Provider change | Re-check data handling and region before routing traffic |

## Runbook for the feature

Contents: how to disable and re-enable; how to roll back a bundle; how to read the dashboard; provider outage procedure; cost spike procedure; a suspected unsafe output procedure (disable, preserve evidence, add an evaluation case, review). A runbook that has not been used in a drill is a hypothesis.

```text
Cost spike procedure
  1. Confirm: cost per hour vs trailing 7-day same-hour average. > 2x?
  2. Scope: by bundle_version, identity, feature path, cache hit rate, retries.
  3. Quick controls (in order): tighten identity limits; enable Degraded-A; disable the heaviest path.
  4. Find cause: prompt length change, retry loop, cache miss storm, abusive identity, evaluation job.
  5. Record: spend during the incident; add an alert or ceiling that would have caught it sooner.
```

## Professional trade-offs

| Axis | One end | Other end | How to decide |
| --- | --- | --- | --- |
| Gate strictness versus release speed | Block on any regression | Advisory only | Strict for must-not-break; relative margins elsewhere |
| Canary length versus traffic | Long holds | Fast steps | Hold until minimum request counts are met |
| Fallback quality versus availability | Disable when degraded | Serve with a weaker model | Evaluate the weaker model; decide per use case and risk |
| Content capture versus privacy | Capture everything | Capture nothing | Sample and redact; short retention |
| Cost ceiling firmness | Hard stop | Soft alert | Degrade before reject; hard stop for non-critical paths |
| Model-graded versus human evaluation | Graded only | Human only | Mechanical first, grader for the rest, humans for calibration |

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Know what ran | Bundle version and git sha in every log line | Unversioned prompts |
| Stop quickly | One scripted action, tested, with pre-granted authority | Multi-step improvisation |
| Control spend | Limits, ceilings and budgets per identity and feature | Trusting the provider's bill to alert you |
| Detect drift | Outcome-mix metrics, nightly canary suite, input profile | Waiting for complaints |
| Survive provider outages | Timeouts, evaluated fallbacks, visible degradation state | Blocking the core service |
| Ship safely | Baseline-relative gates; staged rollout with automatic abort | Manual dashboard watching |
| Keep safety honest | Defence counters; sampled review; incident-to-test loop | Assuming filters work because they exist |

## Knowledge consolidation

- An AI release is a release of **behaviour**; every input that shifts behaviour is a release.
- A **gate** compares to a baseline, asserts case count, separates must-not-break from the rest, and accounts for non-determinism.
- The **release record** lets you answer "what changed?" within a minute.
- **Canary decisions are encoded**, with minimum request counts and automatic rollback.
- **Drift** has four sources; detect it with scheduled canary evaluation, production sampling and input profiles.
- **Cost ceilings** act at several scopes; degrade before rejecting; count loops and retries.
- **Escalation** needs categories, pre-granted authority and a decision tree, and ends with a new test or alert.
- **Safety monitoring** counts defences as well as incidents; a defence never invoked is a finding.
- **Fallbacks** are designed, evaluated, visible states with hysteresis and no policy-boundary crossing.
- **Reliability** combines SLOs for availability, latency, quality and safety with bulkheads, timeouts and breakers.
- **Ownership** is written down per feature.

## Exercises

**Exercise 1 — Write the gate.** For your dataset, write the gate assertions as a configuration (case count, must-not-break, relative margins, cost and latency guards). Run the baseline three times and record the noise. Adjust margins to be above the noise.

**Exercise 2 — Defeat the gate.** Try to ship a bad prompt that passes your gate (for example by removing hard cases, or by lowering a margin in the same change). Document how you did it, then close the loophole.

**Exercise 3 — Release record.** Produce a release record for one real release with all identities, the approvals and the rollback plan. Ask a colleague to answer "what changed since the last release?" using only the record.

**Exercise 4 — Canary abort.** Configure automatic abort rules and simulate a regression (for example slower responses or more tokens per request). Show that the canary aborts and rolls back, with timestamps.

**Exercise 5 — Drift detection.** Schedule a canary suite. Inject a drift (change the fake provider's behaviour without a release) and show the alert and the evidence.

**Exercise 6 — Cost ceiling.** Set low ceilings in staging. Show allow, degrade and reject decisions, and the alerts at 80% and 100%.

**Exercise 7 — Escalation drill.** Run a game day in which an unsafe output is reported. Time how long until the feature is disabled, and who made the decision.

**Exercise 8 — Fallback transitions.** Using fault injection, drive the feature through Normal, Degraded-A, Degraded-B, Cached-only and Off, and back. Show state visibility at each step and the hysteresis on exit.

**Solution notes.**

*Exercise 1.* Expect noise of one to three percentage points on a small dataset. If your margin is smaller than the spread you measured, the gate will fail at random; widen the margin or enlarge the dataset.

*Exercise 2.* Common loopholes: deleting failing cases, editing the dataset in the same change as the prompt, comparing against a stale baseline, and averaging a bad tag into a good overall number. Close them with case-count assertions, a pinned dataset version, a baseline taken from the last release and per-tag margins.

*Exercise 3.* If the colleague needs to open more than the record and the report, a field is missing.

*Exercise 4.* The abort should come from the rules, not from a person. If a person had to notice, add the missing metric.

*Exercise 5.* The alert should fire after the second consecutive failing run. Record the time between injection and alert; that is your detection delay.

*Exercise 6.* Degrade should keep the feature serving at lower cost; reject should apply only at the stated scope. If one heavy identity can cause a global rejection, change the scope.

*Exercise 7.* A good result is under ten minutes from report to disabled, with the decision made by on-call alone. Anything slower points to authority or tooling gaps.

*Exercise 8.* Each state should be visible in the metric, health field and dashboard. If recovery happens at the first healthy minute, add hysteresis.
