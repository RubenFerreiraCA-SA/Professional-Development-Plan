# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-022**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-022](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-06-P — OBSERVABILITY AND RELIABILITY — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Choosing SLOs on user journeys; alert design (symptom-based, actionable, burn-rate, page versus ticket, noise review); evidence-led incident investigation with competing hypotheses and a blameless write-up; telemetry pipeline controls (transport security, credentials, personal data, cardinality, retention, ownership); observability as a platform contract; and honest blind spots.

**Out of scope:** Introductory signals and instrumentation (`DEV-06-B`, `DEV-06-I`), and burn-rate derivations, sampling strategy, measurement pitfalls and organisation-wide governance (`DEV-06-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Select an SLO on a user journey (not a component) and write for each SLI the good event, the valid event, the data source, the window and the owner.
2. Design alerts that page on user-visible symptoms, link a runbook (meaning, urgency and owner, verification, mitigation), prefer multi-window burn-rate alerts, separate pages from tickets, and review noisy alerts for deletion, tuning or downgrade.
3. Run an evidence-led incident investigation: symptom and start time in user terms, at least three competing hypotheses before diving, evidence from metrics, traces, logs and deploy history, an attempt to contradict a favoured theory, a reversible action, confirmation that the SLI recovers, and a blameless write-up that records remaining uncertainty.
4. Apply telemetry pipeline controls: encrypted transport, no credentials in source control, no personal data in logs or spans, bounded cardinality and retention, standard conventions so a vendor can be replaced, and named owners; define an observability contract (required attributes, baseline, default SLOs, validation test, starter template).
5. List honest blind spots (no synthetic probes, sampling hiding rare traces, logs without trace ids, metrics without route templates) in the SLO document, and prepare the evidence for **PRJ-023** (an SLI/SLO, alert rationale and response procedure).

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-06-P — Observability and Reliability — Professional](../../../5%20Textbook/Master%20Textbook.md#t-dev-06-p)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-06` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Observability and Reliability — Professional** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Write an SLO document for a critical journey: two SLIs with all five fields, the target and window, the error-budget policy (what happens at 50% and 100% burn) and the blind spots.
2. Write one fast-burn and one slow-burn alert for that SLO, state which pages and which opens a ticket, and attach a runbook following the four-part structure. Explain why you chose these thresholds.
3. Given a described incident (user-facing latency on one route after a deploy), write the investigation: symptom, start time, three hypotheses, the evidence that would support or contradict each, and the reversible action.
4. Produce a telemetry-controls checklist for your pipeline (transport, credentials, personal data, cardinality, retention, ownership) with the evidence for each item.
5. Review one alert that fires without action: decide to delete, tune or downgrade it, and justify.

**Pass criteria — all of the following must hold:**

- The SLIs describe a user journey and each specifies good event, valid event, source, window and owner.
- Pages are symptom-based with a runbook; slow burns create tickets; thresholds are justified by the budget.
- Hypotheses are written before the evidence, and at least one disconfirming check is named.
- Controls are backed by evidence (a config line, a test) rather than intention.
- Blind spots appear in the document, and the alert review reaches a decision with a reason.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-023 — Create an actionable alert and runbook** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-023).

Evidence to record: the SLI/SLO document, an alert rationale and a runbook the on-call can follow alone, plus every item under *Completion criteria* on that project step. Record **PRJ-023** as **Completed** in your progress record before opening the next module.
