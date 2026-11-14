# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-062**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-062](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-04-P — AGENTS, TOOLS AND ORCHESTRATION — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing safe orchestration and approval gates. You apply least capability and deny by default, bind approvals to the exact tool, arguments, actor and a short expiry, run tools under delegated or narrowly scoped identities, treat tool and document output as untrusted, choose the simplest orchestration pattern that works, and set step, token, cost and time budgets with a kill switch.

**Out of scope:** Threat modelling of attack classes and autonomy governance (`AIE-04-E`), the basic dispatcher mechanics (`AIE-04-I`), release criteria (`AIE-03-P`), service deployment (`AIE-05`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Write the approval contract for `restart_service`: bound to exact tool and arguments, approver identity distinct from the model, single use or minutes of validity, and durable audit evidence.
2. Demonstrate that changing one argument voids an approval, that an expired approval is refused and that a second use is refused.
3. Decide the identity each tool runs as and show that authorisation is checked inside the tool on every call, not assumed from the model's request.
4. Show that a tool argument derived from untrusted retrieved content is flagged and requires approval, and explain which pattern (chain, router, plan-then-execute) you chose and why.
5. Set budgets for steps, tokens, tool calls and wall-clock time plus a kill switch, and keep the test results as the evidence for **PRJ-063**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-04-P — Agents, Tools and Orchestration — Professional](../../../5%20Textbook/Master%20Textbook.md#t-aie-04-p)

Read for: agent design principles, tool design, authorisation model, untrusted data in the loop, orchestration patterns, testing agents and operational limits.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Design and demonstrate privileged-action protection for `ops-assistant`'s `restart_service` using a handler that only records a dry-run. Provide the approval contract, tests for argument change, expiry, reuse and missing identity, the budget table, and a short decision on why the orchestration pattern is the simplest that works.

**Pass criteria:** All four negative tests (changed argument, expired, reused, unidentified approver) block the call; the handler never performs a real restart; budgets are numeric; the design states which capability was removed rather than guarded.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-063 — Protect privileged actions** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-063).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
