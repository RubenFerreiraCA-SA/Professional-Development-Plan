# T-AIE-04-B — Beginner Foundations

*Chapter: [T-AIE-04 — Agents, Tools and Orchestration](README.md) · Part 3 — AI Engineering*

<a id="t-aie-04-b"></a>
#### T-AIE-04-B — Beginner Foundations

## Why this matters

A language model on its own can only produce text. It cannot look up today's status of a service, read a file, or restart anything. The moment you let it *request* those things, you have crossed from a system that answers into a system that acts, and the engineering questions change. The question is no longer only "is the answer good?" but "what exactly can this thing do, who decided that, and what stops it when it goes wrong?"

This level builds the vocabulary and the safe defaults. You will learn the difference between a single model call and a tool loop, what a tool really is, why the model never runs anything itself, how to deny everything that is not explicitly allowed, how to stop a loop, and how to build a small read-only agent whose behaviour you can read line by line. It assumes you can read short Python and that you know a model call takes text in and returns text out. Nothing in this chapter needs a particular model vendor or framework; the loop is ordinary code.

The running example is an `ops-assistant` that answers questions about a few internal services. Everything it can do is a function you write.

## First principles: the model proposes, your code disposes

The most important sentence in this chapter is this one: **the model never executes anything**. A model produces a structured *request* ("please call `get_health` with `service=billing-api`"). Your program receives that request as data, decides whether to honour it, runs the function itself if it does, and then shows the result back to the model as more text. The model is a planner and a writer; your code is the only thing with hands.

That makes an agent a *loop you own*:

```text
question
   │
   ▼
┌───────────────┐   proposes   ┌──────────────────────┐
│     model     │ ───────────▶ │ your code: validate, │
│ (text in/out) │              │ authorise, execute   │
│               │ ◀─────────── │                      │
└───────────────┘  observation └──────────────────────┘
   │
   ▼  (when the model returns a final answer, or a limit stops the loop)
answer
```

Three consequences follow, and every later level builds on them.

1. **Anything the model says is untrusted input.** A tool name, an argument, even a plausible-looking JSON object is a suggestion from a system that can be wrong, confused or manipulated.
2. **Safety lives in your code, not in the prompt.** "Please never delete files" is a request. Not exposing a delete function is a guarantee.
3. **The loop has to end.** A model will happily keep asking for tools. Termination is your job.

## Single call versus tool loop

Not every task needs an agent. The cheapest, most predictable design that works is the right one.

| Pattern | What happens | Cost and latency | Fits when |
| --- | --- | --- | --- |
| Single call | One prompt, one completion | One round trip | The needed facts are already in the prompt: summarise a pasted payload, classify a ticket, rewrite a paragraph |
| Single call plus fixed retrieval | Your code fetches known data, puts it in the prompt, calls once | One model call plus your fetch | You know in advance exactly what to fetch (always the last 20 log lines) |
| Tool loop (agent) | Model proposes calls; your code validates and runs them; model continues | Several model calls, each larger than the last | *Which* data is needed depends on what earlier steps found |
| Unbounded loop | Model loops until it decides it is done | Unpredictable | Never. Always bound the loop |

A practical test: **can you write down the steps before the request arrives?** If yes, write them as ordinary code and use the model only where language is needed (summarising, extracting, choosing a label). If the steps depend on intermediate results you cannot enumerate, a tool loop earns its cost.

Two examples with the same topic:

- "Summarise this alert text" → single call. Everything is already in front of the model.
- "Why is billing-api unhealthy?" → tool loop. The model may need the health status, then the runbook for that service, then perhaps a second service the runbook mentions. You cannot list the steps in advance.

An agent is a chatbot wrapped in a controller; reliability comes from the controller.

## What a tool is

A **tool** has four parts:

| Part | Who sees it | Purpose |
| --- | --- | --- |
| Name | Model and code | The identifier the model uses to request it, for example `get_health` |
| Description | Model | Plain-language statement of what it does and when *not* to use it |
| Argument schema | Model and code | The shape of the arguments: names, types, which are required |
| Handler | Code only | The function that actually runs |

The model sees the first three. It never sees the handler or the credentials the handler uses. A typical schema, written as JSON Schema, looks like this:

```json
{
  "name": "get_health",
  "description": "Return the current health status of one known service. Read-only. Do not use to restart anything.",
  "parameters": {
    "type": "object",
    "properties": {
      "service": {"type": "string", "description": "Exact service name, for example orders-api"}
    },
    "required": ["service"],
    "additionalProperties": false
  }
}
```

`additionalProperties: false` matters: it says "no unexpected keys", so a model cannot slip an extra argument into a call. Remember, though, that a schema shown to the model is only a *request for good behaviour*. Your code must check the arguments again, because the model can still emit anything.

Tools for the example, sorted by what they can change:

| Tool | Purpose | Changes anything? |
| --- | --- | --- |
| `list_known_services` | Return a fixed inventory | No |
| `get_health` | Fetch one service's health status | No |
| `read_runbook` | Read one runbook by name | No, and the path is constrained |
| `restart_service` | Restart a service | **Yes**. Needs approval; not available in this level's agent |

Start every agent with **read-only tools**. A read-only agent can still be wrong, but it cannot damage anything by being wrong.

## Never hand the model a shell

The temptation is one powerful tool: "run any command", "evaluate any expression", "call any URL". It is easy to write and makes demos impressive. It also makes the model's capability equal to whatever your program's account can do.

| Tempting tool | What it really grants | Narrow replacement |
| --- | --- | --- |
| `run_command(cmd)` | Anything the host user can do | `get_health(service)`, `list_known_services()` |
| `eval(expression)` | Arbitrary code execution | A calculator tool that parses numbers and four operators |
| `read_file(path)` | Any readable file, including keys | `read_runbook(name)` resolved under one directory |
| `http_get(url)` | Requests to internal addresses and metadata endpoints | `fetch_status(service)` that builds its own fixed URL |
| `sql(query)` | Read or modify any table | `get_order_total(order_id)` with a parameterised query |

The pattern is the same each time: replace "do anything" with several functions that each do one thing, and keep the dangerous parts (paths, URLs, queries) assembled by your code, not by the model. **A tool is a hole in the wall. Make each hole the smallest it can be.**

## The first rule: deny by default

Your dispatcher is the single place where a requested call becomes a real call. Build it so that anything not explicitly allowed fails *closed*, meaning it is refused and recorded, never silently ignored and never run.

```python
ALLOWED_TOOLS = frozenset({"list_known_services", "get_health", "read_runbook"})

def execute_tool(name: str, args: dict):
    if name not in ALLOWED_TOOLS:          # exact membership, never substring or prefix matching
        return {"status": "denied", "reason": "unknown_or_disallowed_tool"}
    # ... check arguments, then run the handler
```

Three details matter:

- **Exact matching.** `name in ALLOWED_TOOLS` is an equality check. A check such as `name.startswith("get_")` would one day allow `get_secrets`.
- **A visible failure.** A typo such as `restart_servce` must produce a clear `denied` result, not a quiet `None`. The model can then correct itself or give up, and your logs show what happened.
- **One allow-list, defined in code.** The allow-list is a constant in your source, reviewed like any other code. It is not read from a file or a message the model could influence.

## Reading arguments safely

Tool arguments are model output, so check them before use. At Beginner level the minimum is:

1. The arguments are a dictionary.
2. Every required key is present.
3. No unknown keys are present.

Later levels add types, ranges and length limits. Even this minimum prevents accidents: a model that forgets `service` gets a refusal instead of a crash, and one that adds `force=true` gets a refusal instead of a surprise.

## Stop conditions: how the loop ends

A loop without a stop condition is a bug waiting for a bad prompt. Decide in advance every way the loop can end.

| Stop condition | Meaning | What you return |
| --- | --- | --- |
| Final answer | The model produced text instead of a tool call | The answer |
| Step limit reached | Too many iterations without a final answer | A clear "could not complete" message with what was observed |
| Hard denial | A tool call was refused in a way the model must not retry around | An escalation to a human, not another attempt |
| Malformed action | The model's output is neither a valid tool call nor a final answer | An error; never guess what it meant |

The step limit is the one beginners forget, and it is the most important. Choose a small number (three to ten for a simple assistant) and make hitting it visible in logs. A step limit of 5 means the worst case is five model calls, which you can budget and test.

## A guided build: a read-only agent

The model in this build is a small *scripted function*, not a real language model. That is deliberate. It lets you run the whole loop for free, get the same result every time, and focus on the controller. Swapping in a real model later changes only the function that proposes actions.

Project layout:

```text
ops-assistant/
├── agent.py
├── tools.py
└── runbooks/
    └── orders-api.md
```

`tools.py` holds the handlers and a registry that names each tool and its required arguments:

```python
from pathlib import Path

RUNBOOKS = Path(__file__).parent.joinpath("runbooks").resolve()
STATUS = {"orders-api": "healthy", "billing-api": "degraded", "search-api": "healthy"}


def list_known_services(args):
    return {"services": sorted(STATUS)}


def get_health(args):
    service = args["service"]
    if service not in STATUS:
        return {"error": "unknown_service"}
    return {"service": service, "status": STATUS[service]}


def read_runbook(args):
    name = args["name"]
    if "/" in name or "\\" in name or name.startswith("."):
        return {"error": "invalid_name"}
    target = (RUNBOOKS / f"{name}.md").resolve()
    if target.parent != RUNBOOKS or not target.is_file():
        return {"error": "not_found"}
    return {"text": target.read_text()[:2000]}


TOOLS = {
    "list_known_services": {"handler": list_known_services, "required": []},
    "get_health": {"handler": get_health, "required": ["service"]},
    "read_runbook": {"handler": read_runbook, "required": ["name"]},
}
```

Notice what is *not* here: no write, no network, no shell. `read_runbook` accepts a plain name, rejects path separators and leading dots, resolves the final path, and checks that the file really sits directly inside the runbook directory. That last check is what stops `../../etc/passwd` from becoming a file-disclosure tool.

`agent.py` holds the dispatcher, the scripted model and the loop:

```python
from tools import TOOLS

MAX_STEPS = 5


def execute_tool(name, args):
    if name not in TOOLS:                                   # deny by default
        return {"status": "denied", "reason": "unknown_tool"}
    spec = TOOLS[name]
    if not isinstance(args, dict) or any(k not in args for k in spec["required"]):
        return {"status": "denied", "reason": "bad_arguments"}
    if set(args) - set(spec["required"]):                   # no unexpected keys
        return {"status": "denied", "reason": "bad_arguments"}
    return {"status": "ok", "result": spec["handler"](args)}


def scripted_model(question, observations):
    """A stand-in for a real model: returns a tool call or a final answer."""
    q = question.lower()
    if not observations:
        if "health" in q:
            service = next((s for s in ("orders-api", "billing-api", "search-api") if s in q), "")
            return {"type": "tool_call", "tool": "get_health", "args": {"service": service}}
        return {"type": "tool_call", "tool": "list_known_services", "args": {}}
    return {"type": "final", "text": f"Observed: {observations[-1]}"}


def run_agent(question, model=scripted_model):
    observations = []
    for step in range(1, MAX_STEPS + 1):
        action = model(question, observations)
        if action.get("type") == "final":
            return {"answer": action["text"], "steps": step, "stopped": "final_answer"}
        if action.get("type") != "tool_call":
            return {"answer": None, "steps": step, "stopped": "malformed_action"}
        outcome = execute_tool(action.get("tool"), action.get("args"))
        print(f"step {step}: {action['tool']} {action['args']} -> {outcome['status']}")
        observations.append(outcome)
    return {"answer": None, "steps": MAX_STEPS, "stopped": "max_steps"}


if __name__ == "__main__":
    print(run_agent("What is the health of billing-api?"))
```

Run it:

```bash
python3 agent.py
```

Illustrative output:

```text
step 1: get_health {'service': 'billing-api'} -> ok
{'answer': "Observed: {'status': 'ok', 'result': {'service': 'billing-api', 'status': 'degraded'}}", 'steps': 2, 'stopped': 'final_answer'}
```

### Reading the trace

Every agent shares this loop:

1. `run_agent` calls the model with the question and an empty list of observations.
2. The model returns a *tool call*. It is only a dictionary at this point.
3. `execute_tool` checks the name against the registry, checks the arguments, and only then calls the handler.
4. The result, wrapped with a `status`, is appended to `observations`.
5. The model is called again with the new observation, sees a result, and returns a final answer.
6. The loop returns, recording `steps: 2` and `stopped: final_answer`.

Two model calls for one tool call: the model call that *asks* and the model call that *answers*. That is why agents cost more than single calls, and why the step limit is a cost limit as well as a safety limit.

### Break it on purpose

Watch the controls work. Try three experiments.

1. **An unknown tool.** Make the scripted model propose `restart_servce`. The loop should print `denied` and the observation should say `unknown_tool`.
2. **A malformed call.** Make it propose `get_health` with `{"service": "a", "force": true}`. The dispatcher should refuse it with `bad_arguments`.
3. **A runaway model.** Replace the scripted model with one that always proposes `list_known_services`. The loop should stop after exactly five steps with `stopped: max_steps`.

Illustrative result of the third experiment:

```text
step 1: list_known_services {} -> ok
step 2: list_known_services {} -> ok
step 3: list_known_services {} -> ok
step 4: list_known_services {} -> ok
step 5: list_known_services {} -> ok
{'answer': None, 'steps': 5, 'stopped': 'max_steps'}
```

Without `MAX_STEPS`, this program never returns; with a real model, that means it keeps spending.

## Vocabulary in context

| Term | Meaning here |
| --- | --- |
| Agent | A loop in which a model proposes actions and your code runs them |
| Tool | A named function with a description and an argument schema |
| Tool call | A model-produced request to run a tool; data, not an action |
| Observation | The result of a tool call, fed back to the model as text |
| Dispatcher | The code that turns a requested call into a checked, executed call |
| Allow-list | The exact set of tool names that may run |
| Escalate | Hand a decision to a human instead of continuing |

## What can go wrong: common mistakes and how they look

| Mistake | Symptom | Fix |
| --- | --- | --- |
| No step limit | The program never returns, or the bill grows | Always `for step in range(MAX_STEPS)` |
| Substring or prefix allow-list | A new tool named `get_secrets` is silently allowed | Exact membership in a constant set |
| A generic `run_command` tool | The agent can do anything the host can | Narrow, single-purpose tools |
| Trusting arguments because the schema was shown | A call with extra or missing keys reaches a handler | Validate in the dispatcher, always |
| Returning `None` for denials | Nobody can tell a refusal from a bug | Return a structured `denied` result and log it |
| Reading a path built from model text | `../` reads files outside the runbook directory | Reject separators, resolve, confirm the parent directory |
| Putting secrets in the prompt "so the tool can use them" | The model can repeat them in its output | Keep credentials in handlers; the model never sees them |
| Letting the model decide when it is done with no limit | Endless loops on ambiguous questions | Final answer, step limit and malformed-action stops |
| Treating tool output as instructions | A document says "ignore the rules" and the model obeys | Treat all tool output as data; later levels cover defences |
| Testing only with a real model | Flaky, slow, expensive tests | Test the loop with a scripted model first |

## Knowledge consolidation

- An agent is a **loop you own**: the model proposes, your code validates, authorises and executes, and the result goes back to the model.
- The model **never executes anything**; every tool call is untrusted data until your code accepts it.
- Use a **single call** when everything needed is already in the prompt or fixed in advance; use a **tool loop** only when the next step depends on what earlier steps found.
- A tool is a name, a description, an argument schema and a handler. The model sees the first three; **only code sees the handler**.
- **Deny by default.** One constant allow-list, exact matching, visible failures.
- Never expose a shell or a raw API. Replace "do anything" with narrow functions that assemble paths, URLs and queries themselves.
- **Every loop has stop conditions**: final answer, step limit, hard denial, malformed action. The step limit is also a cost limit.
- Start with **read-only** tools. Gate anything that changes state (the next levels explain how).
- A **scripted model** makes the loop testable, free and repeatable.

## Exercises

**Exercise 1 — Allow-list.** Write `execute_tool` with an exact allow-list. Call it with a known tool, an unknown tool, and the misspelled `restart_servce`. Record the three results exactly.

**Exercise 2 — Build and run.** Create the `ops-assistant` project. Run the question "What is the health of billing-api?". Write down the number of steps, the tool called and the final answer.

**Exercise 3 — Break it.** Make the scripted model propose each of: an unknown tool, a call with an extra key, a call with a missing key, and an endless sequence of `list_known_services`. For each, record the `stopped` value or the denial reason.

**Exercise 4 — Path safety.** Call `read_runbook` with `orders-api`, with `../agent`, with `.hidden`, and with `sub/file`. Explain which check rejected each.

**Exercise 5 — Single call or loop?** For each task, choose single call, single call with fixed retrieval, or tool loop, and justify the choice in one sentence: (a) classify a support email into one of four labels; (b) find out which of three services is degraded and show its runbook; (c) rewrite an incident summary in plain English; (d) answer "has anything unhealthy happened this week?" using a status API.

**Solution notes.**

*Exercise 1.* Expected: the known tool passes the allow-list; the unknown tool returns `{"status": "denied", "reason": "unknown_or_disallowed_tool"}`; `restart_servce` returns the same denial. The point is that the misspelling does not slide through and does not fail silently. If your function returned `None` for any case, change it to a structured denial.

*Exercise 2.* Expected: two steps (one tool call, one final answer), `get_health` with `service` `billing-api`, and an answer that mentions `degraded`. If you see more steps, check that your scripted model returns `final` once an observation exists.

*Exercise 3.* Unknown tool: `unknown_tool`. Extra key and missing key: `bad_arguments`. The endless sequence: `stopped: max_steps` after exactly `MAX_STEPS` steps. Note that denials do not end the loop in this simple version, which is acceptable here but is something the Intermediate level improves with escalation.

*Exercise 4.* `orders-api` is read. `../agent` is rejected because it contains a path separator. `.hidden` is rejected because it starts with a dot. `sub/file` is rejected because it contains a separator. If you tried a symbolic link in the runbook directory pointing elsewhere, the resolve-then-check-parent step is what catches it; this is worth testing yourself.

*Exercise 5.* (a) Single call: all information is in the email. (b) Tool loop: which service is degraded determines which runbook to read. (c) Single call: the text is already provided. (d) Tool loop if the model must decide which endpoints and time ranges to query; single call with fixed retrieval if your code can always fetch the same weekly summary and the model only phrases it. Good answers name the *reason* (are the steps known in advance?), not just the label.
