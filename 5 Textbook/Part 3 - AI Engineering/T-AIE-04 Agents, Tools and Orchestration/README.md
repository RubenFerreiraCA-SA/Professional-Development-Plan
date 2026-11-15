# T-AIE-04 — Agents, Tools and Orchestration

*Part 3 — AI Engineering*

An agent is a loop you own: the model proposes actions, and your code validates, authorises, executes and bounds them. Almost every property you need from an agentic system (safety, reliability, cost control, auditability) is a property of that controller, not of the prompt.

## Levels

- [Beginner Foundations](T-AIE-04-B%20Beginner.md#t-aie-04-b) — single call versus tool loop, what a tool is, tool schemas, why the model never executes anything, never handing over a shell, deny-by-default allow-lists, stop conditions, a guided read-only agent with a scripted model.
- [Intermediate Practice](T-AIE-04-I%20Intermediate.md#t-aie-04-i) — the dispatcher's fixed order of checks, schema validation, constrained handlers, sanitised audit logging, state machines, budgets, timeouts, retries and idempotency, routing, memory, tracing, deterministic testing.
- [Professional Engineering](T-AIE-04-P%20Professional.md#t-aie-04-p) — tool contracts, delegated permissions, policy outside the model, bound human approval, untrusted data and taint, isolation, tamper-evident audit, resilience, orchestration patterns, agent testing.
- [Expert Depth](T-AIE-04-E%20Expert.md#t-aie-04-e) — threat modelling and adversarial tool chains, multi-agent trade-offs, emergent failure, cost and latency, compensation and sagas, evaluation and governance, and when not to use an agent.

All examples use a neutral `ops-assistant` service; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.
