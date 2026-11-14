# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-023**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-023](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-06-E — OBSERVABILITY AND RELIABILITY — EXPERT

### 1. Topic and Scope

**In scope for this level:** Reliability as risk management (error budgets as decision tools, choosing targets, dependency-chain availability); burn-rate mathematics and multi-window alerts; measurement pitfalls (averaged percentiles, sampling bias, coordinated omission, missing data treated as healthy, client versus server view, cardinality blow-up); head versus tail sampling; scale and governance of telemetry; and reliability beyond telemetry (timeouts, retries, circuit breakers, load shedding, game days).

**Out of scope:** Introductory signals, instrumentation, SLO and alert design (`DEV-06-B`, `DEV-06-I`, `DEV-06-P`); implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Use error budgets as decision tools: choose a target deliberately, compute the cost of an extra nine, derive dependency-chain availability as a product, and write a policy for what happens when the budget is exhausted.
2. Compute burn rates for a stated SLO and window (for example a 99.9% SLO over 30 days at a burn rate of 14.4 for one hour consuming 2% of the budget) and justify long-plus-short window pairs for paging and longer windows for tickets.
3. Identify and remedy measurement pitfalls: averaging percentiles, sampling bias, coordinated omission, missing data read as healthy, server-only measurement and cardinality blow-up.
4. Compare head-based and tail-based sampling, decide per service what to keep (all errors, all slow traces, a low percentage of normal traces) and keep metrics unsampled for rates.
5. Design governance and resilience: standardised semantic conventions and a versioned telemetry contract, per-team budgets and retention tiers, and reliability controls telemetry cannot provide (timeouts, retries with jitter, circuit breakers, load shedding, game days).

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-06-E — Observability and Reliability — Expert](../../../5%20Textbook/Master%20Textbook.md#t-dev-06-e)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-06` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Observability and Reliability — Expert** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Work through the arithmetic: error budget in minutes for 99.9% over 30 days; the burn rate that consumes 2% in one hour; and the composite availability of three dependencies at 99.9% each. Show every calculation.
2. Design a multi-window burn-rate alert pair for a 99.9% SLO (page and ticket), stating the windows, burn rates and why each window exists, including the reset behaviour after recovery.
3. Pick four measurement pitfalls and for each describe a concrete symptom in a dashboard and the correction (for example merging histograms before computing percentiles; an absence-of-data alert).
4. Write a sampling policy for a service: head or tail, what is always kept, the sampling percentage for normal traces, what you can and cannot answer afterwards, and the cost trade-off.
5. Mentoring prompts, answered in writing: your SLO is met and users are angry, what is wrong with the SLI? How would you alert on a system with near-zero night traffic? What does it cost to keep every trace and what do you lose by sampling?

**Pass criteria — all of the following must hold:**

- All calculations are correct and the budget policy names an action when the budget is spent.
- The alert pair pairs long and short windows and explains false-page and reset behaviour.
- Pitfall answers are specific and each remedy actually fixes the stated distortion.
- The sampling policy keeps errors and slow traces and does not sample the metrics used for rates.
- Mentoring answers question the SLI's relation to user experience, handle low-traffic ratios (for example minimum-volume or synthetic probes) and quantify trade-offs.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-024 — Run an evidence-led incident review** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-024).

Evidence to record: the incident review with a documented uncertainty section and the alerting or instrumentation improvement it produced, plus every item under *Completion criteria* on that project step. Record **PRJ-024** as **Completed** in your progress record before opening the next module.
