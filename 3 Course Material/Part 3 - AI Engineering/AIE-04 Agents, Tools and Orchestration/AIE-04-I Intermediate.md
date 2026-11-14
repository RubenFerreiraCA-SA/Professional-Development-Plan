# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-061**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-061](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-04-I — AGENTS, TOOLS AND ORCHESTRATION — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Building or diagramming controlled tool interactions. You implement the dispatcher order (name authorised, arguments valid, approval satisfied, execute) with fail-closed stages, validate arguments against schemas held in code, confine `read_runbook` to one directory, write sanitised audit entries for allowed and denied calls, and drive a bounded loop with a deterministic mock planner.

**Out of scope:** Per-user delegated authorisation, orchestration patterns and operational budgets (`AIE-04-P`), threat models and autonomy levels (`AIE-04-E`), real approval infrastructure (Project Document and `AIE-04-P`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Implement the four-stage dispatcher and show each stage failing closed with a distinct reason code.
2. Validate arguments for required keys, types and extra keys, and show a malformed call being rejected before any handler runs.
3. Constrain `read_runbook` to a basename under one directory and show `../secret` and `a/b.md` being rejected.
4. Write audit entries for allowed and denied calls with an allow-list of argument keys, `[REDACTED]` for secret-like values and summaries instead of raw bodies.
5. Run a scripted scenario with a deterministic planner, including an unapproved `restart_service`, and keep the blocked-attempt record as the evidence for **PRJ-062**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-04-I — Agents, Tools and Orchestration — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-aie-04-i)

Read for: the fixed dispatcher order, schema validation, constraining tool behaviour (path confinement), sanitised audit logging, the training approval gate versus real approval, and a deterministic planner.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Implement the dispatcher and mock planner for `ops-assistant`. Run four scenarios: a permitted `get_health` call, an unknown tool, a malformed argument, and an unapproved `restart_service`. Submit the three or four resulting audit log lines with sanitised arguments, a path-traversal test, and one sequence diagram of the allowed call.

**Pass criteria:** Each denial has `verdict: blocked` and a reason code; no raw secret or full tool body appears in logs; the loop ends within `MAX_STEPS`; the write-up states that the approval flag, if used, is a teaching stub and not production authorisation.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-062 — Demonstrate a tool interaction** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-062).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
