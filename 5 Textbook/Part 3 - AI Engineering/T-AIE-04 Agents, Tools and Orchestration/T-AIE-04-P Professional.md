# T-AIE-04-P — Professional Engineering

*Chapter: [T-AIE-04 — Agents, Tools and Orchestration](README.md) · Part 3 — AI Engineering*

<a id="t-aie-04-p"></a>
#### T-AIE-04-P — Professional Engineering

**Design principles for agentic systems**

| Principle | Practice |
| --- | --- |
| Least capability | Fewest tools, narrowest arguments, read-only by default |
| Deny by default | Exact allow-list; unknown means fail closed |
| Policy outside the model | Authorisation, limits and approvals enforced in code |
| Bounded autonomy | Maximum steps, tokens, cost and wall-clock time |
| Human in the loop for impact | Approvals for irreversible or high-impact actions |
| Reversibility | Prefer actions that can be undone; support dry-run |
| Observability | Trace every step: prompts, tool calls, results, decisions |
| Idempotency | Tools tolerate retries without repeating side effects |

**Tool design.** Write descriptions that state when *not* to use the tool. Return small, structured results with explicit error codes. Make argument names unambiguous. Split broad tools into narrow ones. Return errors the model can act on, but avoid leaking internal detail.

**Authorisation model.** Tools should execute with the *end user's* delegated permissions or a narrowly scoped service identity — never a shared administrator. Check authorisation inside the tool for every call; do not assume the model's request is legitimate. Record on whose behalf the action ran.

**Untrusted data in the loop.** Tool results and retrieved documents can carry injected instructions. Keep the privilege of the agent small enough that a successful injection cannot do serious damage; treat anything derived from untrusted content as untrusted when it reaches a tool argument; and require approval for actions influenced by external content when stakes are high.

**Orchestration patterns**

| Pattern | Description | When |
| --- | --- | --- |
| Prompt chain | Fixed sequence of calls | Predictable multi-step tasks |
| Router | A classifier chooses a specialised path | Distinct task types |
| Plan then execute | Create a plan, validate it, execute steps | Longer tasks needing review |
| Orchestrator and workers | A coordinator delegates to specialised agents | Parallelisable or specialised subtasks |
| Evaluator loop | Generate, critique, refine within bounds | Quality-sensitive output |

Prefer the simplest pattern that works; each additional agent multiplies failure modes, cost and debugging effort. State is explicit: persist task state outside the model, with resumability and timeouts.

**Testing agents.** Unit-test each tool; test the dispatcher with allowed, denied, malformed and adversarial calls; run scripted scenarios with the deterministic planner; evaluate end-to-end behaviour on a golden set including "must refuse" and "must escalate" cases; and record traces for failures.

**Operational limits.** Per-request and per-user budgets for steps, tokens and tool calls; timeouts per tool; circuit breakers on failing dependencies; concurrency limits; and a kill switch (see T-AIE-05).

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Give the model capabilities | Narrow tools with schemas | A shell or raw API access |
| Gate dangerous actions | Action-specific approval with identity and expiry | A global "approve" flag in production |
| Keep logs safe | Sanitised arguments and result summaries | Raw bodies or secrets in audit logs |
| Control cost | Step, token and time budgets | Open-ended loops |
| Debug failures | Full traces of steps and decisions | Only final answers |
