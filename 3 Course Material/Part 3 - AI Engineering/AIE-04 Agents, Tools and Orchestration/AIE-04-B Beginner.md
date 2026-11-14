# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-060**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-060](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-04-B — AGENTS, TOOLS AND ORCHESTRATION — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Explaining agents, tools and structured calls. You contrast single-shot calls with a tool-using agent loop (plan, tool call, observation, answer), describe a tool as a name, description and argument schema, classify tools as read-only or state-changing, apply the deny-by-default allow-list rule, and explain why the loop must be bounded.

**Out of scope:** Schema validation, path confinement and audit logging (`AIE-04-I`), authorisation models and orchestration patterns (`AIE-04-P`), threat modelling and autonomy governance (`AIE-04-E`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Explain the difference between a single-shot completion and an agent, and why the model proposes calls while your code decides what runs.
2. Describe a tool in terms of name, description and argument schema, and mark `get_health`, `read_runbook`, `list_known_services` and `restart_service` as read-only or state-changing.
3. Explain why a shell, `eval` or unrestricted file write must never be exposed as a tool.
4. Write an exact-match allow-list with a gated set and test a known tool, an unknown tool and a misspelled gated tool such as `restart_servce`, which must fail closed.
5. List four stop conditions for the agent loop and record the permitted-actions table as the evidence for **PRJ-061**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-04-B — Agents, Tools and Orchestration — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-aie-04-b)

Read for: from answering to acting, the agent as a loop you own, tools as named functions with schemas, never handing the model a shell, deny by default and bounding the loop.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Produce a permitted-actions table for `ops-assistant` (tool, purpose, arguments, changes anything yes/no, allowed, gated, rationale), the allow-list code and the recorded results of the three calls in the exercise. Add the four loop stop conditions and the maximum step count you chose.

**Pass criteria:** Only narrow functions are listed; every state-changing tool is gated or denied; the misspelled gated tool returns a denial, not a silent no-op; the step bound is stated.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-061 — List permitted tool actions** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-061).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
