# T-AIE-04-B — Beginner Foundations

*Chapter: [T-AIE-04 — Agents, Tools and Orchestration](README.md) · Part 3 — AI Engineering*

<a id="t-aie-04-b"></a>
#### T-AIE-04-B — Beginner Foundations

**From answering to acting.** A single-shot call turns a prompt into text. An *agent* lets the model propose *actions* — calls to tools — which your code runs, then feeds the results back so the model can continue. The model never touches your systems directly; your program decides what actually runs.

| Pattern | What happens | Fits when |
| --- | --- | --- |
| Single-shot | One prompt, one completion | Summarising a pasted payload |
| Tool-using agent | Model proposes calls; your code validates and executes; model continues | The answer needs live data |
| Unbounded agent | Model loops until it says done | Never — always bound the loop |

An agent is not a smarter chatbot. It is a *loop you own*: plan → tool call → observation → answer.

**Tools.** A tool is a function with a name, a description and an argument schema. The model sees the schema; your code implements the handler.

| Tool | Purpose | Changes anything? |
| --- | --- | --- |
| `get_health` | Fetch a service's health status | No |
| `read_runbook` | Read one runbook by name | No (path constrained) |
| `list_known_services` | Return a fixed inventory | No |
| `restart_service` | Restart a service | **Yes** — needs approval |

**Never hand the model a shell.** No `subprocess`, no `eval`, no unrestricted file writes. Expose a small set of narrow functions.

**The first rule: deny by default.**

```python
ALLOWED_TOOLS = frozenset({"get_health", "read_runbook", "list_known_services", "restart_service"})
GATED_TOOLS = frozenset({"restart_service"})

def execute_tool(name: str, args: dict, approved: bool = False):
    if name not in ALLOWED_TOOLS:                 # exact equality, not substring checks
        return {"status": "denied", "reason": "unknown_or_disallowed_tool"}
    # ... validate args, then check approval, then run
```

A typo such as `restart_servce` must fail closed, not do nothing silently.

**Bound the loop.** Stop when the model returns a final answer, when a maximum number of steps is reached, when a tool returns a hard denial you escalate, or when the plan is empty or malformed.

**Exercise.** Write the allow-list function, call it with a known tool, an unknown tool and a misspelled gated tool, and record the three results.
