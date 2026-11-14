# A01 — Applied AI and LLM Engineering

| | Details |
| --- | --- |
| **Estimated study time** | 32–40 hours |
| **Prerequisites** | Working Harbour health/runbook path from DevOps (D03+) strongly recommended; provider API optional if using the mock LLM path. |
| **Pathway** | Optional AI track — skip freely if AI is out of PDP scope. |

## Objective

Build a **scoped, read-only** Harbour diagnostics assistant (`harbour-diag`): grounded answers over runbooks/health context, an evaluation harness, and user-visible limitations — without any path that mutates production state.

## Outcomes

1. Separate system/user prompts and require structured answers (or explicit refusal) when out of scope.  
2. Ground responses in Harbour docs/runbooks (lightweight retrieval is enough).  
3. Run an evaluation suite (including no-match / insufficient-evidence cases) and record pass/fail evidence.  
4. Validate structured model responses; empty retrieval must not invent diagnoses.  
5. Document feature boundaries so a peer user can see what the assistant must not do.  
6. Keep provider secrets out of Git; offline eval must force mock unless explicitly opted into live.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Scope, prompting and structured outputs | 8–10 |
| Grounding / retrieval over runbooks | 8–10 |
| Evaluation harness and boundary docs | 10–12 |
| Practical Assessment | 6–8 |
| **Total** | **32–40** |

## 1. Prompting and scope

Define `harbour-diag` as operator assistance, not a general chatbot. System prompts must refuse infra mutation, secret exfiltration and out-of-scope product advice.

## 2. Grounding

Retrieve from `docs/runbooks/` (and related Harbour notes) before answering. Prefer simple, reproducible retrieval over an unmanaged vector-database snowflake.

## 3. Evaluation

Maintain golden cases under `app/ai/diagnostics/eval/`. Record results (e.g. `docs/ai/eval-a01.json`). Fail closed when the bar is not met.

## Practical Assessment — read-only diagnostics with eval

**Required evidence:** Feature boundary docs, runnable assistant (mock OK), eval results meeting your bar, user-visible limitations text, no secrets in Git.

**Acceptance:** Checklist A01 — the feature cannot mutate production state in the demo; agreed evaluation cases meet your bar; limitations are visible to a user.

**Textbook:** [Chapter 1 — Applied AI and LLM Engineering](../../4%20Study%20Materials/4.3%20AI%20Engineering/A01%20Applied%20AI%20and%20LLM%20Engineering.md)

**Previous:** [A00 — AI syllabus](A00%20AI%20Syllabus.md) · **Next:** [A02 — Agentic Systems and Orchestration](A02%20Agents%20and%20Orchestration.md)
