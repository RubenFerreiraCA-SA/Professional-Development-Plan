# T-AIE-04-E — Expert Depth

*Chapter: [T-AIE-04 — Agents, Tools and Orchestration](README.md) · Part 3 — AI Engineering*

<a id="t-aie-04-e"></a>
#### T-AIE-04-E — Expert Depth

**Threat modelling an agent.** Enumerate assets (data, credentials, systems the tools can reach), actors (users, the model, third-party content, attackers) and entry points (user input, retrieved documents, tool results, memory, other agents). Common attack classes: *direct injection* (user instructs the model to misbehave), *indirect injection* (instructions hidden in content the agent reads), *confused deputy* (agent uses its privileges for an attacker's request), *tool poisoning* (a malicious tool description or server), *data exfiltration* (leaking via links, images, tool arguments or logs), *excessive agency* (more capability than needed), and *memory poisoning* (persisting malicious instructions).

The dangerous combination to avoid in a single agent: access to private data, exposure to untrusted content, and the ability to send data out or make changes. Break at least one leg by design: separate agents with different privileges, human approval at the boundary, or removing the outbound channel.

**Protocol and ecosystem considerations.** Standards for exposing tools to models (such as the Model Context Protocol) make integration easy and widen the attack surface: treat third-party tool servers like third-party code — review, pin versions, sandbox, restrict network and credentials, and watch for description changes after approval.

**Reliability of long-running agents.** Failure modes: loops without progress, compounding errors across steps, context bloat, tool timeouts, partial side effects after a crash, and non-determinism between runs. Defences: explicit state machines or workflows for the parts that must be deterministic; checkpoints; idempotent, compensating actions; progress detection; summarised memory with provenance; and replayable traces for debugging.

**Evaluation of agents.** Evaluate trajectories as well as outcomes: did it use the right tools in a reasonable order, avoid forbidden ones, stay within budget, and recover from tool errors? Build simulated environments with seeded faults; measure success rate, cost per task, steps, and safety violations; run many trials because behaviour varies; and track regressions across model versions.

**Governance for autonomy.** Define autonomy levels (suggest only, act with approval, act within limits, act freely within a sandbox) per tool and per context; require explicit sign-off to raise a level; log decisions for audit; review incidents. Consider organisational accountability: a named owner for every deployed agent and its tools.

**Failure catalogue**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Path traversal in a "read" tool | Unvalidated filename | Resolve and confine paths; test with `..` |
| Approval laundering | Flag approves any later call | Bind approval to tool, arguments, actor, expiry |
| Exfiltration through rendering | Model emits a link or image whose URL encodes data | Output filtering, no auto-fetch, allow-listed domains |
| Runaway cost | Loop with expensive tool calls | Budgets, circuit breakers, alerts |
| Silent tool change | Third-party description or behaviour updated | Pin, hash, diff-review, sandbox |
| Over-broad service account | One credential for all tools | Per-tool identities, short-lived credentials |

**Mentoring prompts.** Which leg of the "lethal combination" would you remove first for an agent that triages support tickets, and why? How do you give an agent a destructive tool safely, and who must be in the loop? What would a replayable trace need to contain for you to debug a rare failure after the fact?

---
