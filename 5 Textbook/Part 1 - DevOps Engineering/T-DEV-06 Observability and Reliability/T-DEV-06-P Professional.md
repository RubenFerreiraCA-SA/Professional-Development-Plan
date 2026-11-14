# T-DEV-06-P — Professional Engineering

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-p"></a>
#### T-DEV-06-P — Professional Engineering

**Choose user journeys, not components.** An SLO should describe something a user would notice: successful critical reads, readiness of a dependency gate, successful and timely deployment reconciliation. Measure from the perspective closest to the user. Write for each SLI: the good event, the valid event, the data source, the window and the owner.

**Alert design.**

| Principle | Practice |
| --- | --- |
| Alert on symptoms | Page on user-visible impact; use causes for diagnosis dashboards |
| Every page is actionable | Link a runbook: what it means, urgency and owner, how to verify, how to mitigate |
| Prefer burn-rate alerts | Multi-window, multi-burn-rate alerts catch fast and slow budget loss with fewer false pages |
| Separate pages from tickets | Slow burns open tickets; fast burns page |
| Review noisy alerts | Delete, tune or downgrade anything that repeatedly fires without action |

**Evidence-led incident investigation.** Follow the sequence:

1. **Symptom and start time**, stated in user terms.
2. **At least three competing hypotheses** written before deep diving.
3. **Evidence** from metrics, traces, logs, deploy history and dependency health.
4. **Contradict**: actively seek evidence that kills a favourite theory.
5. **Reversible action**: revert or fix, then confirm the SLI recovers.
6. **Write-up** with timeline, contributing factors, preventive change and *remaining uncertainty*.

```markdown
# Incident YYYY-MM-DD
## Symptom        ## Timeline        ## Hypotheses (>=3)
## Action taken   ## SLI after       ## Follow-ups
## What the telemetry could not tell us
```

Blameless reviews focus on conditions and system design, not individuals.

**Telemetry pipeline controls.**

| Control | Expectation |
| --- | --- |
| Transport security | Encrypt to backends in production |
| Credentials | None in source control; use secret stores |
| Personal data | Redact; no request bodies in spans or logs |
| Cardinality and retention | Bounded labels, defined retention, budgets |
| Provider boundary | Keep standard conventions so a vendor can be replaced |
| Ownership | Who owns the collector, SDK versions and sampling defaults |

**Observability as a platform product.** Give teams a *contract*: required resource attributes, an instrumentation baseline, default SLOs, sampling and retention budget, a validation test and a starter template. With a contract, a new service copies a starter and passes a validation test; without it, each team invents metric names and misses trace propagation.

**Honest blind spots.** List what you cannot see: no synthetic probes, sampling may hide rare traces, logs without trace ids, metrics without route templates. State them in the SLO document.

**Decision guide**

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Measure user pain | SLI from the client's perspective | Component health only |
| Control cost | Bounded labels, sampling, retention | Raw URLs or user ids as labels |
| Page responsibly | Symptom alerts with runbooks | Cause-based alerts for everything |
| Investigate | Hypotheses, evidence, contradiction | Anchoring on the first theory |
| Keep the app safe | Non-blocking exporters, tested collector outage | Synchronous telemetry in the request path |
