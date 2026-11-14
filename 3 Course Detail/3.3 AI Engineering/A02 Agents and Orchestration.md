# A02 — Agentic Systems and Orchestration

| | Details |
| --- | --- |
| **Estimated study time** | 32–40 hours |
| **Prerequisites** | [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md). |
| **Pathway** | Optional AI track. |

## Objective

Extend `harbour-diag` into a **tool-using agent** with deny-by-default permissions: allow-listed read tools, an explicit approval gate for anything mutating, and evidence of a blocked unauthorised attempt.

## Outcomes

1. Define tool schemas for read-only Harbour helpers (health, runbook, inventory).  
2. Implement allow-list + deny-by-default tool execution with argument schema validation (no raw shell for the model).  
3. Gate a mutating stub behind a **training** approval control that defaults to deny; document that production needs action-specific authorisation.  
4. Sanitize tool audit logs; run a bounded mock-agent loop with stop conditions.  
5. Prove an unauthorised mutating call fails and record the evidence.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Tool schemas and allow-list policy | 8–10 |
| Approval gate and deny evidence | 8–10 |
| Orchestration loop and failure modes | 10–12 |
| Practical Assessment | 6–8 |
| **Total** | **32–40** |

## 1. Tools as code you control

The model proposes tool names and arguments; **your** executor decides. Unknown tools fail closed.

## 2. Approval gate

Mutating tools require an explicit gate (env flag and/or interactive approval). Default: blocked. Log every attempt.

## 3. Orchestration

Cap steps; stop on final answer, deny, or budget. Prefer mock LLM paths for reproducible labs.

## Practical Assessment — controlled agent path

**Required evidence:** Tool permission model, approval-flow description, failed unauthorised attempt evidence (e.g. `docs/ai/agent-deny-evidence.json`), failure-mode notes.

**Acceptance:** Checklist A02 — a privileged or mutating action is **blocked** unless the designed approval gate passes; show a failed unauthorised attempt.

**Textbook:** [Chapter 2 — Agents and Orchestration](../../4%20Study%20Materials/4.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md)

**Previous:** [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) · **Next:** [A03 — LLMOps and AI Infrastructure](A03%20LLMOps%20and%20AI%20Infrastructure.md)
