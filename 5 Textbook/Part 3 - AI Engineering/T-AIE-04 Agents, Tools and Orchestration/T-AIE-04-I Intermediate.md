# T-AIE-04-I — Intermediate Practice

*Chapter: [T-AIE-04 — Agents, Tools and Orchestration](README.md) · Part 3 — AI Engineering*

<a id="t-aie-04-i"></a>
#### T-AIE-04-I — Intermediate Practice

## Why this matters

The Beginner agent is a loop that is safe because it is tiny: three read-only tools, one step limit, a scripted model. Real assistants are not tiny. Tools fail halfway, time out, return garbage, or succeed twice. Questions need different handling depending on what they are. Conversations grow until the model forgets the beginning. And when something goes wrong, the only evidence is whatever you chose to record.

Intermediate practice is the set of mechanisms that make an agent *predictable under failure*: a dispatcher with a fixed order of checks, real argument validation, a state machine instead of a bare loop, retries and timeouts that distinguish "try again" from "give up", a router that avoids the open-ended loop when it is not needed, memory that stays bounded, tracing that lets you reconstruct a run, and budgets that guarantee termination. It assumes the Beginner material: tools, the model-proposes-code-disposes loop, deny by default, and stop conditions.

The running example is still `ops-assistant`, now with a privileged tool, `restart_service`, that exists in the schema so that the *denial path* can be built and tested before any real mutation exists.

## First principles: the controller owns the guarantees

A model decides *what to try*. It cannot guarantee *what will not happen*. Every property you need from the system must therefore be stated as something the controller enforces:

| Property you want | Mechanism that provides it | What the model contributes |
| --- | --- | --- |
| Only approved capabilities run | Allow-list and approval checks in the dispatcher | Nothing; it only proposes |
| Bad input never reaches a handler | Schema validation in code | Nothing |
| The run ends | Budgets and a state machine | Nothing |
| The run can be diagnosed | Structured traces and audit entries | Nothing |
| Answers are useful | Prompts, tool descriptions, routing | Almost everything |

Reliability work is almost entirely on the left of this table. When an agent misbehaves, ask first which guarantee was missing from the controller, not how to phrase the prompt differently.

## The dispatcher: a fixed order of checks

Every requested call passes the same four stages, in the same order. Each stage fails closed and writes an audit entry.

```text
requested call
   │
   ▼  1. name authorised?          no → denied: unknown_tool
   ▼  2. arguments valid?          no → denied: schema_validation_failed
   ▼  3. approval satisfied?       no → denied: approval_gate_failed (escalate)
   ▼  4. execute (timeout, retry)  fail → error: <code>, retryable or not
   ▼
result (always a structured object with a status)
```

The order is deliberate. Authorising the *name* first means you never parse arguments for a tool that should not exist. Validating arguments before approval means a human is never asked to approve a malformed call. Approval comes before execution, always.

### Schema validation

Validate against schemas defined in code you control, never in a file or a message the model could influence. Check required keys, types, no extra keys and length limits.

```python
TOOL_SCHEMAS = {
    "get_health":      {"required": ["service"], "properties": {"service": str}, "max_len": {"service": 64}},
    "read_runbook":    {"required": ["name"],    "properties": {"name": str},    "max_len": {"name": 64}},
    "restart_service": {"required": ["service"], "properties": {"service": str}, "max_len": {"service": 64}},
}


class ToolError(Exception):
    def __init__(self, code, retryable=False):
        super().__init__(code)
        self.code, self.retryable = code, retryable


def validate_args(tool, args):
    schema = TOOL_SCHEMAS[tool]
    if not isinstance(args, dict):
        raise ToolError("schema_validation_failed")
    missing = [k for k in schema["required"] if k not in args]
    extra = [k for k in args if k not in schema["properties"]]
    if missing or extra:
        raise ToolError("schema_validation_failed")
    for key, typ in schema["properties"].items():
        if key in args:
            if not isinstance(args[key], typ):
                raise ToolError("schema_validation_failed")
            if typ is str and len(args[key]) > schema["max_len"].get(key, 256):
                raise ToolError("schema_validation_failed")
```

Two notes. First, `isinstance(True, int)` is `True` in Python, so if you add integer fields, reject booleans explicitly. Second, validation checks *shape*, not *meaning*: `service="orders-api; drop"` is a valid string. Meaning is checked by the handler against a known inventory, as in the next section.

### Constrain behaviour, not just names

A tool named `read_runbook` that accepts any path is a file-disclosure tool wearing a safe name. Constrain what the handler does with the argument. Accept a basename, resolve it under one directory, reject separators and leading dots, and confirm the resolved parent.

```python
from pathlib import Path

RUNBOOKS = Path("docs/runbooks").resolve()


def read_runbook(args):
    name = args["name"]
    if "/" in name or "\\" in name or name.startswith("."):
        raise ToolError("invalid_name")
    target = (RUNBOOKS / f"{name}.md").resolve()
    if target.parent != RUNBOOKS or not target.is_file():   # catches symlinks that resolve elsewhere
        raise ToolError("not_found")
    return {"text": target.read_text()[:4000]}
```

Test it with `..`, absolute paths, a symlink pointing outside the directory, and a very long name. The truncation at 4000 characters is also a control: it bounds how much text enters the model's context from a single call.

### The dispatcher itself

```python
def dispatch(tool, args, handlers, log, trace_id, approved=False):
    """Fixed order: name -> arguments -> approval -> execute. Each stage fails closed."""
    if tool not in TOOL_SCHEMAS or tool not in handlers:
        audit(log, trace_id, tool, "blocked", "unknown_tool", args)
        return {"status": "denied", "reason": "unknown_tool"}
    try:
        validate_args(tool, args)
    except ToolError as exc:
        audit(log, trace_id, tool, "blocked", exc.code, args)
        return {"status": "denied", "reason": exc.code}
    if tool in GATED and not approved:
        audit(log, trace_id, tool, "blocked", "approval_gate_failed", args)
        return {"status": "denied", "reason": "approval_gate_failed", "escalate": True}
    try:
        result = handlers[tool](args)
    except ToolError as exc:
        audit(log, trace_id, tool, "error", exc.code, args)
        return {"status": "error", "reason": exc.code, "retryable": exc.retryable}
    audit(log, trace_id, tool, "ok", "executed", args)
    return {"status": "ok", "result": result}
```

Every return value is a structured object with a `status`. That is a contract with the loop: the loop never has to guess whether `None` meant "nothing found" or "something broke".

## Sanitised audit logging

Log every attempt, *allowed and denied*. A log that only records successes cannot show an attack. Record the tool, outcome, reason, a trace identifier and a **sanitised** view of the arguments: an allow-list of keys you are willing to log, with secret-like names replaced by `[REDACTED]` and values truncated. On success, record a summary of the result (type, size, selected fields), never the raw body.

```python
import re, time

SECRET_LIKE = re.compile(r"(token|secret|password|key)", re.I)


def sanitise(args, allowed_keys):
    out = {}
    for key, value in (args.items() if isinstance(args, dict) else []):
        if key not in allowed_keys:
            continue
        out[key] = "[REDACTED]" if SECRET_LIKE.search(key) else str(value)[:80]
    return out


def audit(log, trace_id, tool, outcome, reason, args):
    entry = {"ts": round(time.time(), 3), "trace": trace_id, "tool": str(tool)[:64],
             "outcome": outcome, "reason": reason, "args": sanitise(args, {"service", "name"})}
    log.append(entry)
    return entry
```

Note `str(tool)[:64]`: the *tool name itself* is model output and can be arbitrarily long or contain control characters. Treat everything the model produced as untrusted for logging as well.

Three audit lines from an unknown tool, a malformed argument and an unapproved restart (illustrative):

```text
{'ts': 1794725685.952, 'trace': 't', 'tool': 'rm_rf', 'outcome': 'blocked', 'reason': 'unknown_tool', 'args': {}}
{'ts': 1794725685.952, 'trace': 't', 'tool': 'get_health', 'outcome': 'blocked', 'reason': 'schema_validation_failed', 'args': {'service': '5'}}
{'ts': 1794725685.952, 'trace': 't', 'tool': 'restart_service', 'outcome': 'blocked', 'reason': 'approval_gate_failed', 'args': {'service': 'orders-api'}}
```

This is *structured evidence of a blocked attempt* (`outcome: blocked`, reason `approval_gate_failed`), which is what you show when asked to prove a control works. A screenshot of a chat is not evidence.

## From a loop to a state machine

A bare `for` loop hides what the agent is doing. Writing the controller as an explicit **state machine** makes every transition visible, testable and loggable.

| State | Meaning | Allowed next states |
| --- | --- | --- |
| `PLAN` | Ask the model for the next action | `ACT`, `DONE`, `STOPPED` |
| `ACT` | Dispatch one tool call | `PLAN`, `ESCALATED`, `STOPPED` |
| `DONE` | The model returned a final answer | terminal |
| `ESCALATED` | A hard denial needs a human | terminal |
| `STOPPED` | A budget or a malformed action ended the run | terminal |

Terminal states are the point: the run *must* end in one of them, and each carries a reason. Compare that with a loop that "falls off the end".

```python
def run(question, model, handlers, log, budget=None):
    budget, trace_id = budget or Budget(), uuid.uuid4().hex[:8]
    state, history = "PLAN", []
    while True:
        stop = budget.exceeded()
        if stop:
            return {"state": "STOPPED", "reason": stop, "trace": trace_id, "history": history}
        if state == "PLAN":
            budget.steps += 1
            action = model(question, history)
            if action.get("type") == "final":
                return {"state": "DONE", "answer": action["text"], "trace": trace_id, "history": history}
            if action.get("type") != "tool_call":
                return {"state": "STOPPED", "reason": "malformed_action", "trace": trace_id, "history": history}
            state = "ACT"
        elif state == "ACT":
            budget.tool_calls += 1
            outcome = dispatch(action["tool"], action.get("args"), handlers, log, trace_id)
            history.append({"call": action, "outcome": outcome})
            if outcome.get("escalate"):
                return {"state": "ESCALATED", "reason": outcome["reason"], "trace": trace_id, "history": history}
            state = "PLAN"
```

Two behaviours deserve attention. A *hard denial* (`escalate: true`) ends the run in `ESCALATED`. The model is not allowed to retry around a refusal; a human decides. And every `return` carries a `reason`, so "why did it stop?" always has an answer.

## Bounded execution: budgets

A step limit is the minimum. A real budget limits several dimensions at once, because a run can be cheap in steps and expensive in time, or the reverse.

```python
import time


class Budget:
    def __init__(self, max_steps=6, max_tool_calls=4, max_seconds=20.0, clock=time.monotonic):
        self.max_steps, self.max_tool_calls, self.max_seconds = max_steps, max_tool_calls, max_seconds
        self.steps = self.tool_calls = 0
        self.clock, self.start = clock, clock()

    def exceeded(self):
        if self.steps >= self.max_steps:
            return "max_steps"
        if self.tool_calls >= self.max_tool_calls:
            return "max_tool_calls"
        if self.clock() - self.start > self.max_seconds:
            return "deadline"
        return None
```

Inject the clock (`clock=`) so tests can simulate a deadline without sleeping. In production add a token budget: count input and output tokens reported by the model API, because context grows with every step and a ten-step run costs far more than ten times a one-step run.

| Budget | Protects against | Typical starting value for an assistant |
| --- | --- | --- |
| Steps | Endless planning | 5 to 8 |
| Tool calls | Expensive or noisy tools | 3 to 6 |
| Wall-clock deadline | A user waiting forever | 15 to 30 seconds interactive |
| Tokens | Runaway cost and context overflow | Set from measured typical runs, plus margin |
| Same-call repeats | Loops with no progress | Stop at 2 identical calls |

The last row is cheap and effective: if the model proposes the *identical* tool call with identical arguments twice in a row, it is not making progress. End the run or return a pointed error.

## Timeouts, retries and idempotency

Tools talk to networks, and networks fail. Decide, for each failure, whether trying again can help.

| Failure | Retryable? | Reason |
| --- | --- | --- |
| Timeout from a read-only tool | Yes, a few times | The cause may be transient |
| `503` or connection reset | Yes, with backoff | Transient |
| `404`, "unknown service" | No | The answer will not change |
| Schema validation failure | No | The model must change its call |
| Timeout from a *mutating* tool | **Not automatically** | The action may have happened; retrying can repeat it |
| Denied by policy | Never | Retrying around a denial is an attack pattern |

```python
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

_POOL = ThreadPoolExecutor(max_workers=4)


def call_with_timeout(fn, args, seconds):
    future = _POOL.submit(fn, args)
    try:
        return future.result(timeout=seconds)
    except FutureTimeout:
        raise ToolError("tool_timeout", retryable=True)   # the worker thread may still be running


def with_retries(fn, args, attempts=3, base=0.2, timeout=2.0, sleep=time.sleep):
    for attempt in range(1, attempts + 1):
        try:
            return call_with_timeout(fn, args, timeout)
        except ToolError as exc:
            if not exc.retryable or attempt == attempts:
                raise
            sleep(random.uniform(0, base * 2 ** (attempt - 1)))   # exponential backoff, full jitter
```

Details that matter:

- **Jitter** (the random sleep) prevents many clients from retrying in lockstep and hammering a recovering service.
- **A timeout does not cancel the work.** The thread keeps running. For tools that matter, use a client library's own timeout (a socket or HTTP timeout) so the work really stops, and keep this wrapper as a backstop.
- **Retry only idempotent operations.** An operation is *idempotent* if doing it twice has the same effect as doing it once. Reads are. "Restart service X" is nearly so; "charge this card" is not. For non-idempotent tools, pass an idempotency key so a retry is recognised as a repeat.
- **Retries multiply budgets.** Three attempts at two seconds each is six seconds of your twenty-second deadline. Count retries in the tool-call budget or give them a separate small one.

Test retries without waiting by injecting `sleep=lambda s: None`, as the exercises do.

## Errors the model can use

When a tool fails, the model sees the failure as text. Make that text *useful and safe*.

| Instead of | Return | Why |
| --- | --- | --- |
| A Python traceback | `{"status": "error", "reason": "upstream_unavailable", "retryable": true}` | No internal paths or library versions leak, and the model learns whether to retry |
| An empty string | `{"status": "ok", "result": {"error": "unknown_service"}}` or a typed error | The model cannot tell "no data" from "broken" otherwise |
| "Something went wrong" | A stable error code and a one-line hint ("service must be one of the list") | Lets the model correct its next call |
| A very long error body | A truncated code and message | Protects context and the log |

Stable error codes are also what your tests and dashboards count. A free-text error cannot be graphed.

## Routing: do not use the open loop when you do not need it

A **router** sends each request down the cheapest path that can handle it. For `ops-assistant` there are three: a fixed "health" path, a fixed "runbook" path, and the open-ended agent loop for everything else.

```python
ROUTES = {
    "health": ("health", "status", "down", "degraded"),
    "runbook": ("runbook", "procedure", "how do i"),
}


def route(question):
    q = question.lower()
    hits = [name for name, words in ROUTES.items() if any(w in q for w in words)]
    if len(hits) == 1:
        return hits[0]
    return "clarify" if not hits else "agent"      # ambiguous -> open-ended path with its full budget
```

Start with rules; they are free, deterministic and testable. Graduate to a small classifier model only when rules visibly fail, and then keep the rules for the cases that must never be misrouted. Always give the router a defined fallback ("ask a clarifying question") instead of letting unclear requests fall into the most capable, most expensive path. Log the route chosen, because "wrong route" is a common root cause and it is invisible otherwise.

A fixed path is still allowed to call the model, for example to phrase the result of `get_health`. What it does not get is the freedom to choose arbitrary tools.

## Memory: what the model sees next step

An agent has several kinds of memory, with different risks.

| Kind | What it is | Risk | Control |
| --- | --- | --- | --- |
| Working memory | The messages and observations for this run | Context fills up; old facts are lost | Trim and summarise |
| Run state | Task status held by your code | Lost on crash | Persist outside the model |
| Long-term memory | Facts stored across sessions | Stale or poisoned entries | Provenance, expiry, review |

The model has no memory except what you put in front of it. Keep working memory bounded by keeping the newest items verbatim and collapsing older ones:

```python
def trim_history(history, max_items=6):
    """Keep the newest items verbatim; replace older ones by a one-line summary of what was tried."""
    if len(history) <= max_items:
        return history
    old, recent = history[:-max_items], history[-max_items:]
    summary = {"summary": f"{len(old)} earlier steps: " + ", ".join(h["call"]["tool"] for h in old)}
    return [summary] + recent
```

The summary here is built by code from structured data, not by asking a model to summarise, which keeps it deterministic. If you do use a model to summarise, remember that a summary is a *derived* artefact: it can drop the one fact that mattered and can carry forward injected text. Keep the original in the trace.

Never store untrusted content as a "fact" in long-term memory without recording where it came from. Provenance (source, time, who or what wrote it) is what lets you later purge everything that came from one bad source.

## Tracing: reconstruct a run after the fact

An audit entry says *what was attempted*. A **trace** says *how the run unfolded*: which route, which model call, which tool, how long each took, what the controller decided. Generate one trace identifier per run and attach it to every span and audit entry.

```python
class Tracer:
    def __init__(self, sink):
        self.sink = sink

    def span(self, trace, name, **fields):
        start = time.monotonic()

        def end(**more):
            self.sink.append({"trace": trace, "span": name,
                              "ms": round((time.monotonic() - start) * 1000, 1), **fields, **more})
        return end
```

Usage: `end = tracer.span(trace_id, "tool:get_health", tool="get_health")` before the call and `end(outcome="ok")` after. Useful fields per span: route, step number, state, tool, outcome code, duration, token counts, retry count, and the budget remaining. Do not put raw prompts or tool bodies in traces that many people can read; log sizes and hashes, and store full content only where access is controlled.

A trace answers questions you cannot answer otherwise: "Which step took twelve seconds?", "How many runs ended in `max_tool_calls` this week?", "Did the denial happen before or after the model saw the document?"

## The approval gate: a training version, and what real approval needs

`restart_service` exists in the schema so the deny path can be demonstrated. A simple flag, such as `approved=True` passed to `dispatch`, is enough to show the gate working against a handler that does nothing. **That flag is a teaching stub, not production authorisation.** It is process-wide, not tied to a particular call, caller or time.

Before any real mutating handler exists, require all of:

1. Approval bound to the *exact tool name and exact arguments*. A changed argument voids it.
2. An *actor identity*: who approved, authenticated, and distinct from the model or agent.
3. A *short expiry*: single use or minutes, never the whole session.
4. *Audit evidence*: a durable record of approver, tool, sanitised arguments, time and outcome.

The Professional level builds this properly. For now, notice that the dispatcher already routes a gated call to `ESCALATED` without running it, which is the safe default whenever approval is absent.

## Testing with a deterministic planner

A scripted planner makes agent tests free and repeatable. Test the controller, not the model.

```python
def test_loop_bounded_and_escalates():
    always = lambda q, h: {"type": "tool_call", "tool": "get_health", "args": {"service": "x"}}
    r = run("q", always, HANDLERS, [], Budget(max_tool_calls=3))
    assert r["state"] == "STOPPED" and r["reason"] == "max_tool_calls"

    restart = lambda q, h: {"type": "tool_call", "tool": "restart_service", "args": {"service": "orders-api"}}
    assert run("q", restart, HANDLERS, [])["state"] == "ESCALATED"


def test_retry_then_success():
    calls = {"n": 0}

    def flaky(args):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ToolError("upstream_503", retryable=True)
        return "ok"

    assert with_retries(flaky, {}, sleep=lambda s: None) == "ok" and calls["n"] == 3
```

A minimum test set for the controller: unknown tool, malformed arguments, unapproved gated tool, non-retryable error is not retried, retryable error is retried a bounded number of times, timeout is reported with a code, every budget dimension ends the run, and the same-call-repeat rule triggers. None of these needs a model.

## Troubleshooting routine

When an agent run goes wrong, work from the cheapest evidence outward.

| Symptom | First check | Likely cause |
| --- | --- | --- |
| Run ended `STOPPED: max_steps` | Trace: was the same call repeated? | No progress detection; tool returns unhelpful errors |
| Run ended `STOPPED: deadline` | Span durations | One slow tool, or retries consuming the deadline |
| Many `schema_validation_failed` | Audit log reasons | Tool description is ambiguous; argument names are confusing |
| `unknown_tool` entries | Audit log tool names | The model invents tools; the description list is stale |
| Answer ignores a tool result | The history passed to the next model call | Trimming dropped it, or the result was too large and truncated |
| Wrong route | Route logged in trace | Keyword rules overlap; add a test for the failing phrase |
| Intermittent failures | Retry counts and error codes | A flaky dependency; missing backoff or jitter |

Always ask for the trace identifier first. Without one, you are debugging from a screenshot.

## Knowledge consolidation

- The **controller enforces the guarantees**; the model only proposes. Fix missing guarantees in code before editing prompts.
- The dispatcher runs a **fixed order**: name, arguments, approval, execute. Each stage fails closed and writes an audit entry.
- Validate against **schemas defined in code**; check shape in the dispatcher and meaning in the handler. Constrain what handlers do with arguments, not only what tools are named.
- **Audit allowed and denied calls** with sanitised arguments and result summaries; treat model output as untrusted for logging too.
- An explicit **state machine** with terminal states and reasons makes runs testable and explainable.
- **Budgets** cover steps, tool calls, wall-clock time and tokens, and repeated identical calls. Inject the clock in tests.
- **Retry only what is retryable and idempotent**, with backoff and jitter; a timeout is not a cancellation; never retry around a denial.
- Return **structured, stable error codes**; do not leak tracebacks.
- A **router** keeps simple requests off the open loop; give it a fallback and log its choice.
- Working memory must be **bounded**; summaries lose information; long-term memory needs provenance.
- A **trace identifier** per run ties routes, spans, audit entries and budgets together.
- The approval flag in this section is a **teaching stub**; real approval needs binding, identity, expiry and evidence.

## Exercises

**Exercise 1 — The dispatcher.** Implement the four stages and run: an unknown tool, a malformed argument (a number where a string is expected), and an unapproved `restart_service`. Show three audit lines with sanitised arguments and distinct reasons.

**Exercise 2 — Hostile arguments.** Add tests that call `read_runbook` with `..`, an absolute path, a 10,000-character name and a symlink in the runbook directory that points outside it. Confirm each is rejected and that the audit log truncates the long name.

**Exercise 3 — State machine proof.** Using a scripted model, drive the controller into each terminal state: `DONE`, `ESCALATED`, and `STOPPED` for three different reasons. For each, record the returned `reason`.

**Exercise 4 — Retry behaviour.** Write a tool that fails twice with a retryable error, then succeeds, and another that fails once with a non-retryable error. Assert the call counts (3 and 1). Then make a tool that sleeps longer than the timeout and assert the `tool_timeout` code.

**Exercise 5 — No-progress detection.** Add a rule that stops a run when the same tool is called with the same arguments twice in a row. Write a test that triggers it and report the terminal reason you chose.

**Exercise 6 — Route it.** Write ten example questions and the route you expect for each. Run them through `route`. Find at least one that is misrouted and fix the rules without breaking the others; keep all ten as regression tests.

**Exercise 7 — Memory.** Generate a history of twenty tool calls and apply `trim_history`. Show that the newest six remain intact. Describe one fact that a summary would lose and how you would preserve it.

**Solution notes.**

*Exercise 1.* Expected reasons: `unknown_tool`, `schema_validation_failed`, `approval_gate_failed`, with outcome `blocked` in all three. The number argument is logged as the string `'5'`, because sanitisation converts values to truncated strings. If you see the raw object, your sanitiser is leaking structure into the log.

*Exercise 2.* `..`, an absolute path and a name containing a separator are rejected by the separator or dot check. The long name is rejected by the length limit before the handler runs, and the audit entry holds at most 80 characters of it. The symlink case is rejected by the resolve-then-check-parent step; if it is not, you are checking the string rather than the resolved path.

*Exercise 3.* `DONE` when the model returns a final answer; `ESCALATED` with `approval_gate_failed` when it proposes `restart_service`; `STOPPED` with `max_steps`, `max_tool_calls` or `malformed_action` depending on the script. Using a simulated clock you can also produce `deadline`.

*Exercise 4.* The flaky tool should be called three times and the non-retryable tool once. The sleeping tool should raise an error whose code is `tool_timeout`, and its worker thread may keep running after the error, which is the point to remember.

*Exercise 5.* Any clear terminal reason is acceptable, for example `no_progress`. A good solution compares tool name *and* arguments, not name alone: calling `get_health` for two different services is progress.

*Exercise 6.* A typical misroute is a question containing both "status" and "runbook", which hits two routes and goes to the open agent. Whether that is correct is a design decision; write it down. The regression-test habit is the point.

*Exercise 7.* The newest six entries are verbatim and one summary item precedes them. A summary built from tool names loses the *arguments* and the *results*; preserve what matters by also keeping a small list of key facts (services found unhealthy) updated by code as observations arrive.
