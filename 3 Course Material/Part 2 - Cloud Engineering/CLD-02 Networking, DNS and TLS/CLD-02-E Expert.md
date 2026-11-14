# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-035**.

A prerequisite step is satisfied when it is marked **Completed** or **Out of scope**. Use **Out of scope** only when your PDP excludes a whole optional track (for example Datadog or AI), never to skip one step inside an active route.

If any required step is neither **Completed** nor **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their status, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-035](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE CLD-02-E — NETWORKING, DNS AND TLS — EXPERT

### 1. Topic and Scope

**In scope for this level:** Analysis of ambiguous reachability failures: layered DNS caches and negative caching, split-horizon DNS, `ndots` query amplification, reading packet captures (retransmissions, `RST`, zero windows, delayed `SYN-ACK`, TLS alerts), MTU black holes, connection-tracking and ephemeral-port exhaustion, asymmetric routing, retry storms, mutual TLS, short-lived certificates and the weakness of revocation, and designing timeouts, jittered backoff and circuit breakers for partial failure.

**Out of scope:** First commands (CLD-02-B), single-hop drills (CLD-02-I), runbook and termination design (CLD-02-P), and cloud-provider network services (CLD-04). Implementation steps stay in the Project Document.

### 2. Learning Objectives

1. Rank competing hypotheses for "works from my laptop, times out from production" and name the experiment that eliminates each one.
2. Read a `tcpdump` capture to distinguish loss, refusal, a filtered path and a TLS alert, citing the packet evidence.
3. Explain how MTU black holes, conntrack or ephemeral-port exhaustion and `ndots` search-path amplification each produce failures that look like application faults.
4. Evaluate mutual TLS, short-lived certificates and pinning, stating the operational cost and failure mode of each.
5. Design timeouts, retry budgets with jitter, idempotency and circuit breakers for a dependency that degrades, and document the incident analysis required by **PRJ-036**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-CLD-02-E — Networking, DNS and TLS — Expert](../../../5%20Textbook/Master%20Textbook.md#t-cld-02-e)

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Investigate an ambiguous reachability incident you reproduce in an isolated network namespace: write the ranked hypothesis list, the ordered experiments with their results, the packet-level evidence that identifies the failing hop and a mitigation plan. Then critique one design choice (for example pinning or aggressive retries) and explain how it could turn a small fault into an outage.

**Pass criteria:** Hypotheses are tested, not asserted; at least one packet-level artefact supports the conclusion; the analysis identifies what could not be determined; the critique states a concrete failure mechanism and a mitigation with trade-offs.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-036 — Investigate complex reachability incidents** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-036).

Evidence to record: follow the completion criteria on that project step. Mark the step as Completed in your progress record before opening the next module.
