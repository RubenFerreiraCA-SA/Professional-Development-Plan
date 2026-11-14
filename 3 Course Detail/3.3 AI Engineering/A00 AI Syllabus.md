# A00 — AI Engineering Syllabus

**Estimated study time:** 96–120 hours  
**Scope:** Applied LLM engineering, tool-using agents with guardrails, and operable LLM feature delivery for Harbour.  
**Pathway status:** **Optional** — exclude freely in your PDP / Capacity Planner. Excluding AI does not make the Final Project incomplete.

AI Engineering adds a **carefully scoped** capability to Harbour: a read-only diagnostics assistant that is evaluated, permissioned and operable — not an unbounded chatbot bolted onto production.

## Discipline objectives

1. Ship a useful, **read-only** AI feature with grounded answers and an evaluation harness.  
2. Orchestrate tool-using agents under **deny-by-default** permissions and an explicit approval gate for anything mutating.  
3. Operate the feature with versioning, monitoring, cost/safety limits and a one-action disable/rollback.  
4. Document limitations so a peer user can see what the assistant must not do.

## Modules

| Module | Focus | Estimated study time | Evidence of capability |
| --- | --- | ---: | --- |
| [A01 — Applied AI and LLM Engineering](A01%20Applied%20AI%20and%20LLM%20Engineering.md) | Prompting, grounding/retrieval, eval, feature boundaries | 32–40 hours | Read-only diagnostics feature; eval cases meet your bar; limitations visible |
| [A02 — Agentic Systems and Orchestration](A02%20Agents%20and%20Orchestration.md) | Tool calling, allow-lists, approval gates, orchestration loops | 32–40 hours | Unauthorised mutating action blocked; approval path documented |
| [A03 — LLMOps and AI Infrastructure](A03%20LLMOps%20and%20AI%20Infrastructure.md) | Versioning, serving, kill switch, cost/safety, monitoring | 32–40 hours | One-action disable/rollback; basic cost/safety limits or monitors |
| **Total** | **3 modules** | **96–120 hours** | **Scoped, evaluated, operable AI path for Harbour** |

Hour ranges are **planning assumptions**. Completion is demonstrated capability, not calendar time.

## Curriculum progression

1. **A01** — Make the assistant useful and honest under evaluation.  
2. **A02** — Let it use tools without giving it the keys to the kingdom.  
3. **A03** — Run it like a product surface: versions, limits, kill switch.

**Relationship to other disciplines:** Prefer a working Harbour API/health path from DevOps (D03+) before deep AI labs. Cloud (C01–C03) is helpful for production-shaped deploy later but **not** required to start A01 with a local/mock provider. Platform Engineering owns broader IDP UX; AI remains an optional increment on the same Final Project.

## Practical outcomes and Final Project

Track Harbour increments on the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) rows A01–A03 when AI is in scope. **End of AI** (optional milestone): Harbour exposes a limited diagnostics assistant with eval evidence, blocked unauthorised mutations, and a documented disable/rollback path.

**Exit scenario:** mock `harbour-diag` answers a known health question with runbook evidence; an unsupported question does not invent a diagnosis; a mutating tool attempt is denied and audited; rate-limit exhaustion is rejected; evaluation re-runs from a clean state and fails CI when any case fails; with core Harbour up, `HARBOUR_AI_REQUIRE_CORE_CHECK=1 ./scripts/disable-harbour-ai.sh` disables AI while capturing fresh core before/after health.

## Completion criteria

- Each in-scope module’s Practical Assessment at **Competent** or better.  
- Checklist A01–A03 acceptance criteria met (or honestly `Adapted:` / `N/A — out of scope`).  
- No provider API keys or production secrets in Git; limitations documented for users.

## Learning content status

| Artifact | Status |
| --- | --- |
| This syllabus + module course-detail | Documentation signed off |
| Textbook chapters | [A01](../../4%20Study%20Materials/4.3%20AI%20Engineering/A01%20Applied%20AI%20and%20LLM%20Engineering.md), [A02](../../4%20Study%20Materials/4.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md), [A03](../../4%20Study%20Materials/4.3%20AI%20Engineering/A03%20LLMOps%20and%20AI%20Infrastructure.md) — documentation signed off (optional Final Project track) |
| Clean-room lab certification | Separate QA workstream — not implied by documentation sign-off |

**Previous discipline:** [Cloud syllabus](../3.2%20Cloud%20Engineering/C00%20Cloud%20Syllabus.md) · **Next module:** [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) · **Next discipline (if skipping AI):** [Platform syllabus](../3.4%20Platform%20Engineering/P00%20Platform%20Syllabus.md)
