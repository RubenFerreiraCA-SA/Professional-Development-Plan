# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-020**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-020](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-06-B — OBSERVABILITY AND RELIABILITY — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Monitoring versus observability; the three levels to observe (user experience, application and dependencies, platform); the golden signals, RED and USE checklists; metrics, logs and traces and their metric types (counter, gauge, histogram); a first structured log line; and the six questions a responder must answer.

**Out of scope:** Instrumentation, label cardinality, OpenTelemetry pipelines, SLIs and alerts (`DEV-06-I`), alert design and incident method (`DEV-06-P`), and burn-rate mathematics and sampling theory (`DEV-06-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Distinguish monitoring (known checks) from observability (asking new questions) and state one strength and one failure mode of each.
2. Distinguish the three levels to observe (user experience, application and dependencies, platform) and apply the four golden signals, RED and USE to a request-driven service and to a resource.
3. Describe metrics, logs and traces by what each is good for, and choose the right metric type (counter, gauge, histogram) for requests, in-flight requests and latency.
4. Write and read a structured JSON log line with timestamp, level, service, message, error code and trace id, and name what must never be logged (passwords, tokens, `Authorization` headers, personal data).
5. Write the six responder questions with the smallest signal that answers each, identify blind spots, and prepare the evidence for **PRJ-021**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-06-B — Observability and Reliability — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-dev-06-b)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-06` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Observability and Reliability — Beginner** in your own words, without undocumented help, and keep the outputs with your progress record.

1. For a service you know (or Harbour), choose one critical user journey and list one signal at each of the three levels for it. Name which golden signal each represents.
2. Classify ten example measurements (requests per second, queue depth, request duration, error count, CPU use, memory use, deploys, ...) as counter, gauge or histogram and justify any that are not obvious.
3. Write one structured JSON log line for an error event and annotate each field. Identify two things that must not appear in it.
4. Write the six responder questions and, for each, the smallest signal that answers it. Mark any question that has no signal today as a blind spot.
5. Written answer: when is monitoring enough, and when does a team need observability? Give a concrete example of an unknown-failure scenario.

**Pass criteria — all of the following must hold:**

- Signals cover user experience, application and platform levels, and each is mapped to a golden signal or RED/USE item.
- Metric types are correct for counters, gauges and latency distributions, and a histogram is justified for percentiles.
- The log line is valid JSON with a trace id, and the exclusions list covers credentials and personal data.
- Blind spots are identified honestly instead of claiming every question is answered.
- The monitoring-versus-observability answer is concrete and not a definition restatement.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-021 — Record meaningful service health signals** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-021).

Evidence to record: the user journey, the captured logs and the metric that answers one of the six questions, plus every item under *Completion criteria* on that project step. Record **PRJ-021** as **Completed** in your progress record before opening the next module.
