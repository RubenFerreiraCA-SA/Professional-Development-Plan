# Chapter 2 — Agents and Orchestration (A02)

*AI Engineering textbook · Chapter 2 of 3*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see [A02 course detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md) (about 32–40 hours). |
| **Prerequisites** | [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) — read-only `harbour-diag` with evaluation and visible limits. |

> **Optional AI track:** Include A01–A03 only if AI is in your PDP Capacity Planner. If you excluded AI, mark Final Project Checklist rows `N/A — out of scope`. That is a complete outcome for a non-AI pathway.

## How to study this chapter

A02 extends A01’s **read-only** `harbour-diag` into a **tool-using agent** with an **allow-list**. The model never gets a raw shell. Mutating or privileged tools are **blocked** unless an explicit **approval gate** passes. The checklist bar is: *a privileged or mutating action is blocked unless the designed approval gate passes; show a failed unauthorised attempt.*

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Prefer `MOCK_LLM` / local stubs so labs run without paid APIs. Tools are **code you control** under `app/ai/diagnostics/`. Log every tool call. Secrets stay in the environment only.

This text teaches [A02 Course Detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md).

> **Safety boundary:** Deny by default. Never expose `subprocess`, `os.system`, or unrestricted filesystem write to the model. Allow-list exact tool names. Fail closed on unknown names. Record deny evidence — a silent ignore is not a pass.

### Learning outcomes

1. Contrast single-shot LLM calls with a bounded agent loop (plan → tool → observe → answer).  
2. Define JSON tool schemas for read-only Harbour diagnostics tools.  
3. Implement `execute_tool(name, args)` with allow-list + deny-by-default.  
4. Gate a deliberately dangerous stub (`restart_service`) behind approval; prove an unauthorised attempt fails with filed evidence.  
5. Bound the orchestration loop with max steps and clear stop conditions.

### Before you begin

Reuse A01 artefacts. Create agent docs **before** coding the loop.

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"

test -d app/ai/diagnostics || {
  echo "Complete A01 harbour-diag under app/ai/diagnostics/ first"
  exit 1
}
test -d docs/ai || {
  echo "Complete A01 docs/ai/ (prompts, eval notes, limits) first"
  exit 1
}

mkdir -p docs/ai/agents docs/decisions docs/runbooks
export PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
export MOCK_LLM="${MOCK_LLM:-1}"
export APPROVE_MUTATIONS="${APPROVE_MUTATIONS:-0}"
python3 -c 'from ai.diagnostics import prompts; print("A01 import ok", prompts.SYSTEM_PROMPT[:24])' \
  || { echo "Fix A01 package layout / PYTHONPATH=$HARBOUR_ROOT/app first"; exit 1; }
python3 -c 'import sys; print(sys.version)'
```

You need: A01 `harbour-diag` runnable locally (or against a documented stub), write access under `$HARBOUR_ROOT`, and mutations **off** by default.

---

## Section 2.1 — Agents vs single-shot LLM calls

### 2.1.1 Concept

| Pattern | What happens | Fits Harbour when… |
| --- | --- | --- |
| Single-shot | One prompt → one completion | Summarising a pasted health blob (A01) |
| Tool-using agent | Model proposes tool calls; **your** code runs them; model continues | Diagnostics need live `get_health` / runbook text |
| Unbounded agent | Model keeps calling until “done” | **Never** — always max steps + allow-list |

An agent is not “smarter ChatGPT.” It is a **loop you own**: the LLM suggests structured actions; your runtime validates, executes (or denies), and feeds observations back.

**Reflect:** If the only way to “let the agent fix things” is giving it a shell, you have not designed tools — you have outsourced production to a text generator.

### 2.1.2 Practice — name the boundary

Write three lines in `docs/ai/agents/agent-boundary.md`: (1) what A01 could do without tools, (2) read-only A02 names, (3) what must never run without approval (name `restart_service`).

**Verify:** The file exists and names `restart_service` as gated.

---

## Section 2.2 — Tool schemas (JSON) for read-only tools

### 2.2.1 Concept

Publish **exact** tool names and argument shapes. The model sees schemas; your code implements handlers. Stubs are fine — behaviour must still fail closed.

| Name | Purpose | Mutating? |
| --- | --- | --- |
| `get_health` | Fetch `/health` or local stub status | No |
| `read_runbook` | Read a basename under `docs/runbooks/` | No (path constrained) |
| `list_known_services` | Fixed inventory stub | No |
| `restart_service` | Privileged stub for the deny demo | **Yes** (gated) |

### 2.2.2 Worked example — schema + stubs

Create `docs/ai/agents/tool-schemas.json`:

```json
{
  "tools": [
    {
      "name": "get_health",
      "description": "Return Harbour health JSON for the configured endpoint or local stub.",
      "parameters": { "type": "object", "properties": {}, "additionalProperties": false }
    },
    {
      "name": "read_runbook",
      "description": "Read a runbook by basename only (no path separators).",
      "parameters": {
        "type": "object",
        "properties": { "name": { "type": "string" } },
        "required": ["name"],
        "additionalProperties": false
      }
    },
    {
      "name": "list_known_services",
      "description": "List known training services from a local inventory stub.",
      "parameters": { "type": "object", "properties": {}, "additionalProperties": false }
    },
    {
      "name": "restart_service",
      "description": "PRIVILEGED stub — must pass approval gate. Does not restart real prod.",
      "parameters": {
        "type": "object",
        "properties": { "service": { "type": "string" } },
        "required": ["service"],
        "additionalProperties": false
      }
    }
  ]
}
```

Add `app/ai/diagnostics/tools.py`:

```python
# app/ai/diagnostics/tools.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

HARBOUR_ROOT = Path(os.environ.get("HARBOUR_ROOT", ".")).resolve()
RUNBOOK_DIR = HARBOUR_ROOT / "docs" / "runbooks"
INVENTORY = [
    {"name": "harbour-api", "tier": "training"},
    {"name": "harbour-diag", "tier": "training"},
]


def get_health(_args: dict[str, Any]) -> dict[str, Any]:
    stub = HARBOUR_ROOT / "docs" / "ai" / "agents" / "health-stub.json"
    if stub.is_file():
        return json.loads(stub.read_text(encoding="utf-8"))
    return {"status": "ok", "source": "inline-stub", "service": "harbour-api"}


def read_runbook(args: dict[str, Any]) -> dict[str, Any]:
    name = str(args.get("name", ""))
    if name != Path(name).name or name in ("", ".", ".."):
        raise ValueError("read_runbook: name must be a basename")
    path = (RUNBOOK_DIR / name).resolve()
    root = RUNBOOK_DIR.resolve()
    if path != root and not str(path).startswith(str(root) + os.sep):
        raise ValueError("read_runbook: path escapes runbook dir")
    if not path.is_file():
        raise FileNotFoundError(f"runbook not found: {name}")
    text = path.read_text(encoding="utf-8")
    return {"name": name, "chars": len(text), "preview": text[:500]}


def list_known_services(_args: dict[str, Any]) -> dict[str, Any]:
    return {"services": list(INVENTORY)}


def restart_service(args: dict[str, Any]) -> dict[str, Any]:
    service = str(args.get("service", ""))
    if not service:
        raise ValueError("restart_service: service required")
    return {
        "ok": True,
        "action": "restart_service",
        "service": service,
        "note": "stub executed after approval — no real restart",
    }
```

Seed stubs:

```bash
printf '%s\n' '{"status":"ok","service":"harbour-api","checks":["liveness"]}' \
  > "$HARBOUR_ROOT/docs/ai/agents/health-stub.json"
printf '%s\n' '# harbour-diag\n\n1. Call get_health\n2. Do not restart without approval\n' \
  > "$HARBOUR_ROOT/docs/runbooks/harbour-diag.md"
```

**Verify:** With `export PYTHONPATH="$HARBOUR_ROOT/app"`, `python3 -c "from ai.diagnostics.tools import get_health; print(get_health({}))"` prints stub JSON.

---

## Section 2.3 — Allow-list + deny-by-default policy

### 2.3.1 Concept

| Rule | Meaning |
| --- | --- |
| Allow-list | Only exact names in a frozenset may run |
| Deny-by-default | Unknown name → reject; do not “best effort” |
| No raw shell | No `bash`, `eval`, or free-form command tool |
| Audit | Every attempt (allow **and** deny) is logged |

Do **not** check permissions with substring matches (`if "restart" in name`). Exact equality only.

### 2.3.2 Worked example — `execute_tool`

Create `app/ai/diagnostics/agent_runtime.py`:

```python
# app/ai/diagnostics/agent_runtime.py
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from ai.diagnostics import tools as tool_impl

HARBOUR_ROOT = Path(os.environ.get("HARBOUR_ROOT", ".")).resolve()
LOG_PATH = HARBOUR_ROOT / "docs" / "ai" / "agents" / "tool-call-log.jsonl"

READ_ONLY: frozenset[str] = frozenset(
    {"get_health", "read_runbook", "list_known_services"}
)
PRIVILEGED: frozenset[str] = frozenset({"restart_service"})
ALLOW_LIST: frozenset[str] = READ_ONLY | PRIVILEGED

HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "get_health": tool_impl.get_health,
    "read_runbook": tool_impl.read_runbook,
    "list_known_services": tool_impl.list_known_services,
    "restart_service": tool_impl.restart_service,
}


def _append_log(entry: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def approval_granted(tool_name: str) -> bool:
    """Fail closed: mutations require APPROVE_MUTATIONS=1 or interactive yes."""
    if tool_name not in PRIVILEGED:
        return True
    if os.environ.get("APPROVE_MUTATIONS", "0") == "1":
        return True
    if os.environ.get("APPROVE_INTERACTIVE", "0") == "1":
        ans = input(f"Approve privileged tool {tool_name}? [y/N] ").strip().lower()
        return ans in ("y", "yes")
    return False


def execute_tool(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    args = dict(args or {})
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    base = {"ts": ts, "tool": name, "args": args}

    if name not in ALLOW_LIST:
        out = {**base, "status": "denied", "reason": "unknown_or_disallowed_tool"}
        _append_log(out)
        return out

    if name in PRIVILEGED and not approval_granted(name):
        out = {
            **base,
            "status": "denied",
            "reason": "approval_gate_failed",
            "hint": "Set APPROVE_MUTATIONS=1 or APPROVE_INTERACTIVE=1 with yes",
        }
        _append_log(out)
        return out

    try:
        result = HANDLERS[name](args)
        out = {**base, "status": "ok", "result": result}
    except Exception as exc:  # noqa: BLE001 — surface to agent observe step
        out = {**base, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
    _append_log(out)
    return out
```

### 2.3.3 Practice — reject unknown and mutating names

```bash
cd "$HARBOUR_ROOT"
export HARBOUR_ROOT APPROVE_MUTATIONS=0 MOCK_LLM=1
python3 <<'PY'
import os
from ai.diagnostics.agent_runtime import execute_tool

print("read-only:", execute_tool("get_health", {}))
print("unknown:", execute_tool("run_shell", {"cmd": "id"}))
print("mutate-blocked:", execute_tool("restart_service", {"service": "harbour-api"}))
PY
```

**Verify:** Unknown → `denied` / `unknown_or_disallowed_tool`. `restart_service` with `APPROVE_MUTATIONS=0` → `denied` / `approval_gate_failed`. Both appear in `docs/ai/agents/tool-call-log.jsonl`.

**Reflect:** Would a typo like `restart_servce` silently no-op or fail closed? It must fail closed.

---

## Section 2.4 — Approval gate for `restart_service`

### 2.4.1 Concept

Privileged tools exist in the schema so the **deny path is demonstrable**. Default: mutations off.

| Gate | Pass condition |
| --- | --- |
| Env flag | `APPROVE_MUTATIONS=1` |
| Interactive | `APPROVE_INTERACTIVE=1` **and** operator types `y` / `yes` |
| Default | Block — write deny evidence |

Never treat “the model asked nicely” as approval.

### 2.4.2 Worked example — approved path (training only)

```bash
export APPROVE_MUTATIONS=1
python3 -c '
from ai.diagnostics.agent_runtime import execute_tool
import json
print(json.dumps(execute_tool("restart_service", {"service": "harbour-api"}), indent=2))
'
export APPROVE_MUTATIONS=0
```

**Verify:** With flag set, status is `ok` and the stub notes no real restart. With flag cleared, the same call is denied.

### 2.4.3 Practice — ADR note

Add `docs/decisions/0102-harbour-agent-tool-policy.md` (adjust number to your scheme): allow-list, deny-by-default, approval gate, and that `restart_service` is a **stub** for assessment evidence — not a production operator.

---

## Section 2.5 — Worked example: unauthorised attempt fails with evidence

### 2.5.1 Concept

Checklist A02 requires a **failed unauthorised attempt** on record. Capture structured JSON — not a vague chat screenshot.

### 2.5.2 Worked example — write deny evidence

```bash
cd "$HARBOUR_ROOT"
export HARBOUR_ROOT APPROVE_MUTATIONS=0 APPROVE_INTERACTIVE=0
mkdir -p docs/ai

python3 <<'PY'
import json, os
from pathlib import Path
from ai.diagnostics.agent_runtime import execute_tool

root = Path(os.environ["HARBOUR_ROOT"]).resolve()
attempt = execute_tool("restart_service", {"service": "harbour-api"})
unknown = execute_tool("delete_cluster", {"name": "prod"})

assert attempt.get("status") == "denied", attempt
assert attempt.get("reason") == "approval_gate_failed", attempt
assert unknown.get("status") == "denied", unknown

evidence = {
    "scenario": "unauthorised_mutating_tool",
    "checklist": "A02 — privileged/mutating action blocked unless approval gate passes",
    "env": {
        "APPROVE_MUTATIONS": os.environ.get("APPROVE_MUTATIONS", "0"),
        "APPROVE_INTERACTIVE": os.environ.get("APPROVE_INTERACTIVE", "0"),
        "MOCK_LLM": os.environ.get("MOCK_LLM", "1"),
    },
    "attempt": attempt,
    "unknown_tool_attempt": unknown,
    "verdict": "blocked",
}
out = root / "docs" / "ai" / "agent-deny-evidence.json"
out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {out}")
PY

# Exact-field checks — avoid brittle substring greps:
python3 <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ["HARBOUR_ROOT"]) / "docs" / "ai" / "agent-deny-evidence.json"
data = json.loads(p.read_text(encoding="utf-8"))
assert data["verdict"] == "blocked"
assert data["attempt"]["status"] == "denied"
assert data["attempt"]["reason"] == "approval_gate_failed"
assert data["attempt"]["tool"] == "restart_service"
print("evidence OK")
PY
```

**Verify:** `docs/ai/agent-deny-evidence.json` exists; `verdict` is `blocked`; `reason` is exactly `approval_gate_failed`. Log the path in your Progress and Evidence Log for A02.

---

## Section 2.6 — Orchestration loop (plan → tool → observe → answer)

### 2.6.1 Concept

| Stop when… | Why |
| --- | --- |
| Model returns a final answer (no tool call) | Normal completion |
| `step >= MAX_STEPS` | Prevent runaway cost / loops |
| Tool returns hard deny you escalate | Human takes over |
| Empty / malformed plan | Fail closed — do not invent tools |

### 2.6.2 Worked example — `MOCK_LLM` planner + loop

```python
# app/ai/diagnostics/agent_loop.py
from __future__ import annotations

import json
import os
from typing import Any

from ai.diagnostics.agent_runtime import execute_tool

MAX_STEPS = int(os.environ.get("AGENT_MAX_STEPS", "4"))


def mock_plan(user_query: str, observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic stub planner — swap for a real provider later without changing execute_tool."""
    q = user_query.lower()
    if not observations:
        if "restart" in q:
            return {
                "type": "tool",
                "name": "restart_service",
                "args": {"service": "harbour-api"},
            }
        return {"type": "tool", "name": "get_health", "args": {}}
    last = observations[-1]
    if last.get("status") == "denied":
        return {
            "type": "final",
            "answer": (
                "I cannot perform that action: tool denied "
                f"({last.get('reason')}). Ask an operator to approve mutations."
            ),
        }
    if last.get("tool") == "get_health" and last.get("status") == "ok":
        return {
            "type": "final",
            "answer": f"Health observation: {json.dumps(last.get('result'))}",
        }
    return {"type": "final", "answer": f"Stopped after observations: {len(observations)}"}


def run_agent(user_query: str) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    for step in range(1, MAX_STEPS + 1):
        plan = mock_plan(user_query, observations)
        steps.append({"step": step, "plan": plan})
        if plan.get("type") == "final":
            return {"ok": True, "steps": steps, "answer": plan.get("answer", "")}
        if plan.get("type") != "tool":
            return {"ok": False, "steps": steps, "error": "malformed_plan"}
        name = str(plan.get("name", ""))
        args = plan.get("args") if isinstance(plan.get("args"), dict) else {}
        obs = execute_tool(name, args)
        observations.append(obs)
        steps[-1]["observation"] = obs
    return {
        "ok": False,
        "steps": steps,
        "error": "max_steps_exceeded",
        "max_steps": MAX_STEPS,
    }
```

### 2.6.3 Practice — demo both paths

```bash
export APPROVE_MUTATIONS=0 MOCK_LLM=1 AGENT_MAX_STEPS=4
python3 <<'PY'
from ai.diagnostics.agent_loop import run_agent
import json
print("=== health path ===")
print(json.dumps(run_agent("What is Harbour health?"), indent=2))
print("=== unauthorised restart path ===")
print(json.dumps(run_agent("Please restart harbour-api"), indent=2))
PY
```

**Verify:** Health path ends with a final answer citing the stub. Restart path observation shows `denied` / `approval_gate_failed`, and the final answer refuses the mutation. §2.5 evidence remains on disk.

**Reflect:** If you later swap `mock_plan` for a paid API, does `execute_tool` still own the allow-list? It must.

---

## Section 2.7 — Troubleshooting

| Symptom | Likely cause | First check |
| --- | --- | --- |
| `ModuleNotFoundError: ai.diagnostics` | Package / `PYTHONPATH` / A01 layout | `export PYTHONPATH=$HARBOUR_ROOT/app`; mirror A01 `ai.diagnostics` imports |
| Deny evidence missing `approval_gate_failed` | Mutations left enabled | `echo "$APPROVE_MUTATIONS"` must be `0` for the fail demo |
| `read_runbook` errors on `../secrets` | Path traversal correctly blocked | Use basename only under `docs/runbooks/` |
| Agent never stops | No max steps / MOCK planner bug | `AGENT_MAX_STEPS`; inspect `steps` in loop result |
| “It worked in chat” but no JSON evidence | UI-only demo | Re-run §2.5 → `docs/ai/agent-deny-evidence.json` |
| Paid API required | Forgot stubs | Keep `MOCK_LLM=1` until A03 |
| Log empty | Wrong `HARBOUR_ROOT` | Confirm `docs/ai/agents/tool-call-log.jsonl` under the same root |

---

## Practical Assessment — Chapter 2 — controlled agent path

Align with [A02 Course Detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md) and Final Project Checklist A02: *A privileged or mutating action is blocked unless the designed approval gate passes; show a failed unauthorised attempt.*

### Required deliverables

1. **Tool permission model** — `docs/ai/agents/tool-schemas.json` + allow-list/`PRIVILEGED` under `app/ai/diagnostics/`.  
2. **`execute_tool`** — unknown names denied; read-only tools succeed; every call logged to `docs/ai/agents/tool-call-log.jsonl`.  
3. **Approval gate** — `restart_service` blocked unless `APPROVE_MUTATIONS=1` or interactive yes.  
4. **Failed unauthorised attempt** — `docs/ai/agent-deny-evidence.json` with exact `status`/`reason` fields.  
5. **Orchestration loop** — plan → tool → observe → answer with `MAX_STEPS`; `MOCK_LLM` path documented.  
6. **ADR / boundary note** — `docs/ai/agents/agent-boundary.md` + short ADR on tool policy.  
7. Optional: one approved-path smoke with flag set, then flag cleared again.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Tool model | Free-form “run command” | JSON schemas + exact allow-list | Path-constrained readers + typed errors |
| Deny path | Hope / UI only | Filed `agent-deny-evidence.json` with gate reason | Unknown-tool deny in same artefact |
| Approval | Always on / always off | Default blocked; explicit env or interactive yes | Dual gate + audit of both outcomes |
| Loop | Unbounded chat | Max steps + clear stop conditions | Swappable planner behind same `execute_tool` |
| Safety | Secrets in prompts | Env-only secrets; no raw shell tool | Traversal tests for `read_runbook` |

**Completion:** **Competent** on every row.

### Self-check

- Does the unauthorised demo run with `APPROVE_MUTATIONS=0`?  
- Is evidence at `docs/ai/agent-deny-evidence.json` with exact field asserts (not substring grep)?  
- Can read-only tools still run while mutations are blocked?  
- Is there **no** tool that executes arbitrary shell?  
- Would a second engineer find schemas, log, and deny evidence without asking you?

### Example conclusion (evidence still required)

> Extended A01 `harbour-diag` with allow-listed tools under `app/ai/diagnostics/`. `execute_tool` denies unknown names and blocks `restart_service` unless `APPROVE_MUTATIONS=1`. Unauthorised attempt filed at `docs/ai/agent-deny-evidence.json` (`approval_gate_failed`). MOCK_LLM loop completes health Q&A within max steps and refuses restart without approval. No raw shell tool; secrets remain in env.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Add a capability | New schema + handler + allow-list entry | Letting the model invent tool names |
| Show checklist A02 | §2.5 deny evidence script | Chat screenshot without JSON |
| Debug a deny | `tool-call-log.jsonl` last lines | Widening allow-list “temporarily” |
| Call a paid model later | Keep `execute_tool` as the only executor | Passing API keys into prompts |
| Leave the lab | `APPROVE_MUTATIONS=0` | Leaving mutations enabled overnight |

## Glossary

| Term | Meaning |
| --- | --- |
| Allow-list | Exact set of tool names the runtime will consider |
| Deny-by-default | Anything not explicitly allowed is rejected |
| Approval gate | Extra human/env check before privileged tools run |
| Orchestration loop | Repeated plan → tool → observe until stop |
| MOCK_LLM | Local deterministic planner so labs need no paid API |
| Fail closed | On doubt or error, block the action |

## References

- [OpenAI function / tool calling (concepts)](https://platform.openai.com/docs/guides/function-calling)  
- [Anthropic tool use (concepts)](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)  
- [OWASP LLM Top 10 — excessive agency](https://owasp.org/www-project-top-10-for-large-language-model-applications/)  
- [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) · [A03](A03%20LLMOps%20and%20AI%20Infrastructure.md) · [AI syllabus](../../3%20Course%20Detail/3.3%20AI%20Engineering/A00%20AI%20Syllabus.md)

**Previous chapter:** [Chapter 1 — Applied AI and LLM Engineering (A01)](A01%20Applied%20AI%20and%20LLM%20Engineering.md) · **Course detail:** [A02](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md) · **Next chapter:** [Chapter 3 — LLMOps and AI Infrastructure (A03)](A03%20LLMOps%20and%20AI%20Infrastructure.md) · **Checklist:** [Final Project Checklist · A02](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
