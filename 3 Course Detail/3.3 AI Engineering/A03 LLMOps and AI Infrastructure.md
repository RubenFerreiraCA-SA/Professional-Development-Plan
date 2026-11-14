# A03 — LLMOps and AI Infrastructure

| | Details |
| --- | --- |
| **Estimated study time** | 32–40 hours |
| **Prerequisites** | [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md), [A02](A02%20Agents%20and%20Orchestration.md). |
| **Pathway** | Optional AI track. |

## Objective

Operate the Harbour diagnostics AI path like a product surface: pinned versions, serving/health that reports AI state, **one-action disable/rollback**, cost/safety limits, and basic monitoring — with eval regression awareness.

## Outcomes

1. Version prompts, tool policy and model id; keep a short changelog.  
2. Serve the assistant locally (or via Compose) with health reflecting enabled/disabled.  
3. Disable or roll back the AI path in **one documented action** and prove it.  
4. Enforce basic cost/safety limits (tokens, rate, budget) — mockable offline.  
5. Emit structured operational signals (latency, tokens, tool denials) and optionally gate CI on A01 eval JSON.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Versioning and packaging/serving | 8–10 |
| Kill switch, cost/safety limits | 10–12 |
| Monitoring and eval-in-CI mindset | 8–10 |
| Practical Assessment | 6–8 |
| **Total** | **32–40** |

## 1. Version and serve

Pin `app/ai/diagnostics/VERSION` (or equivalent). Health endpoints must report whether AI is enabled.

## 2. Kill switch and rollback

One documented action (e.g. `HARBOUR_AI_ENABLED=false` + restart, or revert VERSION) disables the path. Record evidence.

## 3. Cost, safety and signals

Caps and monitors before “leave it running.” Prefer structured logs over vanity dashboards for the training bar.

## Practical Assessment — operable AI path

**Required evidence:** Deploy/config notes, LLMOps checks (limits/monitors), disable/rollback procedure with proof, version pin.

**Acceptance:** Checklist A03 — you can disable or roll back the AI path in one documented action; basic cost/safety limits or monitors exist.

**Textbook:** [Chapter 3 — LLMOps and AI Infrastructure](../../4%20Study%20Materials/4.3%20AI%20Engineering/A03%20LLMOps%20and%20AI%20Infrastructure.md)

**Previous:** [A02](A02%20Agents%20and%20Orchestration.md) · **Next:** [Platform syllabus](../3.4%20Platform%20Engineering/P00%20Platform%20Syllabus.md) (after optional AI milestone)
