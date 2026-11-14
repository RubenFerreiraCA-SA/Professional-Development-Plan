# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-024**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-024](../../../4%20Project%20Document/Project.md#prj-001).

**Optional track:** this module belongs to the optional Datadog track (`DEV-07`, `PRJ-025` to `PRJ-028`). If your personal PDP excluded the whole Datadog track, record `DEV-07` and its project steps as **Out of scope** and continue with the next active module. If the track is active, all four levels and their steps are mandatory and ordered.

## MODULE DEV-07-B — DATADOG MONITORING — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Datadog's monitoring components and terminology: the data path (application SDK, Agent, backend, humans), API keys, application keys and sites, unified service tagging (`service`, `env`, `version`), and running the Agent next to a service in Compose. This module belongs to the optional Datadog track.

**Out of scope:** Correlating logs, APM and infrastructure, dashboards, SLOs and monitors (`DEV-07-I`), monitors as code, onboarding packages and cost review (`DEV-07-P`), and cardinality economics, vendor strategy and governance (`DEV-07-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Map the Datadog data path (application SDK → Agent → Datadog backend → humans) and state what each part owns: spans and custom metrics, forwarding and infrastructure checks, indexing and monitors, and keys, tag policy and cost.
2. Distinguish `DD_API_KEY` (Agent intake), `DD_APP_KEY` (API and automation, narrow scopes) and `DD_SITE` (regional site), say where each is kept, and explain why a wrong site or missing key is the most common cause of "nothing appears".
3. Apply unified service tagging (`DD_SERVICE`, `DD_ENV`, `DD_VERSION`) and explain how inconsistent tags split a service across pages and break deployment comparison.
4. Run the Agent in Compose with APM and log collection enabled, point a service at it with `DD_AGENT_HOST`, and verify it with `agent status`, noting the port-conflict risk with another collector.
5. Generate successful, failing and slow requests and locate the host, a trace and a log line in the interface, and prepare the evidence for **PRJ-025**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-07-B — Datadog Monitoring — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-dev-07-b)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-07` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Datadog Monitoring — Beginner** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Draw the data path for your Compose setup and label the keys, site and tags that flow through it.
2. Write the Agent service and application environment variables for Compose (without secret values) and show how the API key is kept out of Git (`.gitignore` entry and `git check-ignore -v`).
3. Run `docker exec datadog-agent agent status` (or, with no account, explain which section of its output you would inspect to confirm key validity, APM receiver and log collection).
4. Send success, error and slow requests and record in a table where each appears in the interface (host, service, trace, log) and the tag values observed (`service`, `env`, `version`).
5. Written answers: why might nothing appear after setup, and what are the first three checks in order?

**Pass criteria — all of the following must hold:**

- The data path names Agent, backend and application and lists what each owns.
- Keys are not committed; the explanation separates API and application keys.
- Tag values are consistent across metrics, traces and logs, or the inconsistency is identified.
- The troubleshooting answer starts with key and site, then Agent status, then application target host and port.
- If no paid account was used, a clearly labelled simulation or documented walk-through replaces live screenshots.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-025 — Onboard the sample service to Datadog** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-025).

Evidence to record: the Agent connection check and the service visible (or a documented interpretation of the same), plus every item under *Completion criteria* on that project step. Record **PRJ-025** as **Completed** in your progress record before opening the next module (or **Out of scope** only if the whole Datadog track was excluded in your PDP).
