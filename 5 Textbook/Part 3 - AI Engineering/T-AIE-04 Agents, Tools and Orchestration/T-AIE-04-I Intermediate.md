# T-AIE-04-I — Intermediate Practice

*Chapter: [T-AIE-04 — Agents, Tools and Orchestration](README.md) · Part 3 — AI Engineering*

<a id="t-aie-04-i"></a>
#### T-AIE-04-I — Intermediate Practice

**The dispatcher flow — fixed order.** *Name authorised → arguments valid → approval satisfied → execute.* Each stage fails closed and writes an audit entry.

**Schema validation of arguments.** Validate against schemas defined in code you control (not a file the model could influence): required keys, types, no extra keys.

```python
TOOL_SCHEMAS = {
    "get_health":   {"required": [], "properties": {}},
    "read_runbook": {"required": ["name"], "properties": {"name": str}},
    "restart_service": {"required": ["service"], "properties": {"service": str}},
}

def validate_args(tool: str, args: dict) -> None:
    schema = TOOL_SCHEMAS[tool]
    missing = [k for k in schema["required"] if k not in args]
    extra = [k for k in args if k not in schema["properties"]]
    if missing or extra:
        raise ValueError("schema_validation_failed")
    for k, typ in schema["properties"].items():
        if k in args and not isinstance(args[k], typ):
            raise ValueError("schema_validation_failed")
```

**Constrain tool behaviour, not just names.** `read_runbook` accepts a *basename* and resolves it under one directory; reject separators and `..`. A path-traversal bug turns a read tool into a file-disclosure tool.

```python
from pathlib import Path
RUNBOOKS = Path("docs/runbooks").resolve()

def read_runbook(args):
    name = args["name"]
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("invalid_name")
    target = (RUNBOOKS / name).resolve()
    if RUNBOOKS not in target.parents:
        raise ValueError("outside_allowed_directory")
    return {"text": target.read_text()[:4000]}
```

**Sanitised audit logging.** Log every attempt, allowed *and* denied: tool, outcome, reason, and a *sanitised* view of arguments (an allow-list of keys; secret-like values replaced by `[REDACTED]`) and, on success, a sanitised summary of the result (type, size, selected fields) — never the raw bodies. Both model input and tool output are untrusted for logging purposes.

**An approval gate (training version).** A privileged tool exists in the schema so the deny path is demonstrable. A simple flag such as an environment variable can demonstrate approval once against a handler that does nothing. **That flag is a teaching stub, not production authorisation**: it is process-wide, not tied to a specific call, caller or time window.

**What real approval needs.** Before any real mutating handler exists, require all of:

1. Approval bound to the *exact tool name and exact arguments* (a changed argument voids it).
2. An *actor identity*: who approved, authenticated, and distinct from the model or agent.
3. A *short expiry*: single use or minutes, not the session.
4. *Audit evidence*: durable record of approver, tool, sanitised arguments, time and outcome.

**A deterministic planner for tests.** Drive the loop with a rule-based "mock planner" so tests are free and repeatable:

```python
MAX_STEPS = 4

def run_agent(question, plan, execute, finish):
    observations = []
    for step in range(MAX_STEPS):
        action = plan(question, observations)       # returns a tool call or a final answer
        if action is None:
            return finish(question, observations, reason="no_plan")
        if action["type"] == "final":
            return action["answer"]
        observations.append(execute(action["tool"], action["args"]))
        if observations[-1].get("status") == "denied" and observations[-1].get("escalate"):
            break
    return finish(question, observations, reason="max_steps_or_denied")
```

**Evidence of a blocked attempt.** Record structured proof that an unauthorised call failed (`verdict: blocked`, reason `approval_gate_failed`), not a vague screenshot.

**Exercise.** Implement the dispatcher with the four stages, run an unknown tool, a malformed argument and an unapproved restart, and show three log lines with sanitised arguments.
