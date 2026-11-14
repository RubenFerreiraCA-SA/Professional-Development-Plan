# Chapter 2 — Agents and Orchestration (A02)

*AI Engineering textbook · Chapter 2 of 3*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see [A02 course detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md) (about 32–40 hours). |
| **Prerequisites** | [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) — read-only `harbour-diag` with evaluation and visible limits. |

> **Optional AI track:** Include A01–A03 only if AI is in your PDP Capacity Planner. If you excluded AI, mark Final Project Checklist rows `N/A — out of scope`. That is a complete outcome for a non-AI pathway.

## How to study this chapter

A02 extends A01’s **read-only** `harbour-diag` into a **tool-using agent** with an **allow-list**. The model never gets a raw shell. Mutating or privileged tools are **blocked** unless an explicit **approval gate** passes. The checklist bar is: *a privileged or mutating action is blocked unless the designed approval gate passes; show a failed unauthorised attempt.*

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Prefer `MOCK_LLM` / local stubs so labs run without paid APIs. Tools are **code you control** under `app/ai/diagnostics/`. Log every tool call (with sanitized arguments — never raw `args`). Secrets stay in the environment only.

This text teaches [A02 Course Detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md).

> **Safety boundary:** Deny by default. Never expose `subprocess`, `os.system`, or unrestricted filesystem write to the model. Allow-list exact tool names. Fail closed on unknown names. Record deny evidence — a silent ignore is not a pass.

> **Training gate ≠ production authorisation:** `APPROVE_MUTATIONS=1` in this chapter is a **training stub only** — it lets you demonstrate the approved path against a no-op `restart_service`. It is **not** a production approval mechanism. See the callouts in §2.3.2 and §2.4.

### Learning outcomes

1. Contrast single-shot LLM calls with a bounded agent loop (plan → tool → observe → answer).  
2. Define JSON tool schemas for read-only Harbour diagnostics tools.  
3. Implement `execute_tool(name, args)` with allow-list + deny-by-default, **schema validation of arguments**, and **sanitized audit logging**.  
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

Add `app/ai/diagnostics/tool_schemas.py` — an **embedded copy** of the parameter schemas above, so the runtime validates against code you control (not a file the model could influence). Keep it identical to `docs/ai/agents/tool-schemas.json`:

```python
# app/ai/diagnostics/tool_schemas.py
from __future__ import annotations

from typing import Any

# Must match docs/ai/agents/tool-schemas.json ("parameters" per tool name).
TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "get_health": {"type": "object", "properties": {}, "additionalProperties": False},
    "read_runbook": {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
        "additionalProperties": False,
    },
    "list_known_services": {"type": "object", "properties": {}, "additionalProperties": False},
    "restart_service": {
        "type": "object",
        "properties": {"service": {"type": "string"}},
        "required": ["service"],
        "additionalProperties": False,
    },
}
```

Seed stubs:

```bash
printf '%s\n' '{"status":"ok","service":"harbour-api","checks":["liveness"]}' \
  > "$HARBOUR_ROOT/docs/ai/agents/health-stub.json"
printf '%s\n' '# harbour-diag\n\n1. Call get_health\n2. Do not restart without approval\n' \
  > "$HARBOUR_ROOT/docs/runbooks/harbour-diag.md"
```

**Verify:** With `export PYTHONPATH="$HARBOUR_ROOT/app"`, `python3 -c "from ai.diagnostics.tools import get_health; print(get_health({}))"` prints stub JSON. Then confirm the embedded schemas have not drifted from the published JSON:

```bash
python3 - <<'PY'
import json, os
from pathlib import Path
from ai.diagnostics.tool_schemas import TOOL_SCHEMAS

doc = json.loads((Path(os.environ["HARBOUR_ROOT"]) / "docs/ai/agents/tool-schemas.json").read_text(encoding="utf-8"))
published = {t["name"]: t["parameters"] for t in doc["tools"]}
assert published == TOOL_SCHEMAS, "tool_schemas.py drifted from tool-schemas.json"
print("schemas in sync")
PY
```

---

## Section 2.3 — Allow-list + deny-by-default policy

### 2.3.1 Concept

| Rule | Meaning |
| --- | --- |
| Allow-list | Only exact names in a frozenset may run |
| Deny-by-default | Unknown name → reject; do not “best effort” |
| Schema validation | Arguments must satisfy the tool's schema (required keys, types, no extra keys) **before** approval or execution |
| No raw shell | No `bash`, `eval`, or free-form command tool |
| Audit | Every attempt (allow **and** deny) is logged — with **sanitized** args, never raw `args` |

**Dispatcher flow (fixed order):** name authorised → arguments valid → approval satisfied → execute. Each stage fails closed and writes a log entry.

Do **not** check permissions with substring matches (`if "restart" in name`). Exact equality only.

### 2.3.2 Worked example — `execute_tool`

> **⚠ TRAINING GATE ONLY — NOT A PRODUCTION AUTHORISATION CONTROL.**
> `approval_granted()` below checks `APPROVE_MUTATIONS=1` (or an interactive `y`). That is a **training stub**: a process-wide flag that is not bound to any specific call, caller, or time window. **Never reuse it to guard a real mutating handler.**
> Before any real mutating handler exists, you must require **action-specific approval** bound to: the **exact tool name** + **exact arguments** + **actor identity** + a **short expiry**, with **audit evidence** of who approved what and when. (Designing that full authorisation framework is out of scope for this chapter — the boundary is the point.)

Create `app/ai/diagnostics/agent_runtime.py`:

```python
# app/ai/diagnostics/agent_runtime.py
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

from ai.diagnostics import tools as tool_impl
from ai.diagnostics.tool_schemas import TOOL_SCHEMAS

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

# Fail at import time if a tool is allow-listed without a schema (or vice versa).
if set(TOOL_SCHEMAS) != set(ALLOW_LIST) or set(HANDLERS) != set(ALLOW_LIST):
    raise RuntimeError("ALLOW_LIST, HANDLERS and TOOL_SCHEMAS must list the same tools")

# --- Minimal JSON-schema validation (required keys + types + no extras) ---
_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def validate_args(name: str, args: dict[str, Any]) -> str | None:
    """Return None if args satisfy the tool schema, else a short reason (never echoes values)."""
    schema = TOOL_SCHEMAS.get(name)
    if schema is None:
        return "no_schema_for_tool"
    props: dict[str, Any] = schema.get("properties", {})
    for key in schema.get("required", []):
        if key not in args:
            return f"missing_required:{key}"
    if schema.get("additionalProperties") is False:
        extra = [k for k in args if k not in props]
        if extra:
            return f"unexpected_properties:{len(extra)}"
    for key, spec in props.items():
        if key not in args:
            continue
        declared = spec.get("type")
        expected = _JSON_TYPES.get(declared)  # unknown declared type -> fail closed
        value = args[key]
        if expected is None:
            return f"unsupported_schema_type:{key}"
        if isinstance(value, bool) and declared in ("integer", "number"):
            return f"wrong_type:{key}:expected_{declared}"
        if not isinstance(value, expected):
            return f"wrong_type:{key}:expected_{declared}"
    return None


# --- Audit sanitisation: never write raw args to the log ---
# Only these keys per tool are ever logged. A future tool gets NO logged values until you add it here.
AUDIT_KEYS: dict[str, frozenset[str]] = {
    "get_health": frozenset(),
    "read_runbook": frozenset({"name"}),
    "list_known_services": frozenset(),
    "restart_service": frozenset({"service"}),
}
MAX_AUDIT_VALUE_LEN = 64
MAX_AUDIT_KEY_LEN = 40
MAX_DROPPED_KEYS = 10
SECRET_RE = re.compile(
    r"(sk-[a-z0-9_-]{8,}"                                  # API-key-like
    r"|bearer\s+\S+"                                       # auth header values
    r"|api[_-]?key|token|secret|passw(or)?d|authorization"  # secret-ish words
    r"|[a-z0-9+/_=-]{32,})",                               # long opaque blobs
    re.IGNORECASE,
)


def _safe_str(text: str) -> str:
    if SECRET_RE.search(text):
        return "[REDACTED]"
    if len(text) > MAX_AUDIT_VALUE_LEN:
        return f"[TRUNCATED len={len(text)}]"
    return text


def _audit_args(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Allow-listed keys only; values redacted/truncated; other keys recorded by name only."""
    keep = AUDIT_KEYS.get(name, frozenset())  # unknown tool -> keep nothing
    clean: dict[str, Any] = {}
    for key, value in args.items():
        if key not in keep:
            continue
        if isinstance(value, str):
            clean[key] = _safe_str(value)
        elif value is None or isinstance(value, (bool, int, float)):
            clean[key] = value
        else:
            clean[key] = f"<omitted:{type(value).__name__}>"
    dropped = sorted(_safe_str(str(k)[:MAX_AUDIT_KEY_LEN]) for k in args if k not in keep)
    if dropped:
        clean["_dropped_keys"] = dropped[:MAX_DROPPED_KEYS]
    return clean


def _append_log(entry: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def approval_granted(tool_name: str) -> bool:
    """Fail closed: mutations require APPROVE_MUTATIONS=1 or interactive yes.

    TRAINING STUB ONLY. This is NOT production authorisation. A real mutating handler
    needs approval bound to exact tool name + args + actor identity + short expiry,
    with audit evidence. Do not reuse this flag to guard real actions.
    """
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
    # Never log raw args: sanitise once, reuse for every outcome.
    base = {"ts": ts, "tool": name, "args": _audit_args(name, args)}

    # 1) Name authorised?
    if name not in ALLOW_LIST:
        out = {**base, "status": "denied", "reason": "unknown_or_disallowed_tool"}
        _append_log(out)
        return out

    # 2) Arguments valid? (before approval, so bad calls never reach the gate or handler)
    problem = validate_args(name, args)
    if problem is not None:
        out = {
            **base,
            "status": "denied",
            "reason": "schema_validation_failed",
            "detail": problem,
        }
        _append_log(out)
        return out

    # 3) Approval satisfied? (training stub — see callout above)
    if name in PRIVILEGED and not approval_granted(name):
        out = {
            **base,
            "status": "denied",
            "reason": "approval_gate_failed",
            "hint": "Training gate: APPROVE_MUTATIONS=1 or APPROVE_INTERACTIVE=1 with yes (not production approval)",
        }
        _append_log(out)
        return out

    # 4) Execute
    try:
        result = HANDLERS[name](args)
        out = {**base, "status": "ok", "result": result}
    except Exception as exc:  # noqa: BLE001 — surface to agent observe step
        # Exception text can echo caller input, so scrub it like any other logged string.
        out = {**base, "status": "error", "error": f"{type(exc).__name__}: {_safe_str(str(exc))}"}
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

### 2.3.4 Practice — schema validation + sanitized log evidence

Prove the order *name → args → approval → execute*, and that the log never holds raw args or secrets. Note the invalid `restart_service` call is rejected for its **arguments** even though approval is also off — validation runs first.

```bash
cd "$HARBOUR_ROOT"
export HARBOUR_ROOT APPROVE_MUTATIONS=0 MOCK_LLM=1
python3 <<'PY'
import json, os
from pathlib import Path
from ai.diagnostics.agent_runtime import execute_tool, LOG_PATH

root = Path(os.environ["HARBOUR_ROOT"]).resolve()
SECRET = "sk-test-0123456789abcdef"

cases = {
    "missing_required": execute_tool("read_runbook", {}),
    "wrong_type": execute_tool("restart_service", {"service": 42}),
    "extra_secret_key": execute_tool("read_runbook", {"name": "harbour-diag.md", "api_key": SECRET}),
    "secret_value": execute_tool("read_runbook", {"name": SECRET}),
    "long_value": execute_tool("read_runbook", {"name": "a b " * 50}),
}
for label in ("missing_required", "wrong_type", "extra_secret_key"):
    r = cases[label]
    assert r["status"] == "denied" and r["reason"] == "schema_validation_failed", (label, r)
    assert "result" not in r  # handler never ran
assert cases["wrong_type"]["reason"] != "approval_gate_failed"  # args checked before approval

blob = json.dumps(cases)
assert SECRET not in blob and "a b " * 50 not in blob, "raw value leaked into log entries"
assert SECRET not in LOG_PATH.read_text(encoding="utf-8"), "secret reached tool-call-log.jsonl"
assert cases["extra_secret_key"]["args"]["_dropped_keys"] == ["[REDACTED]"]  # key name looks secret-like

out_dir = root / "docs" / "ai" / "agents"
(out_dir / "schema-validation-evidence.json").write_text(
    json.dumps({"checklist": "A02 — schema validated before approval/execute", "cases": cases},
               indent=2, sort_keys=True) + "\n", encoding="utf-8")
with (out_dir / "sanitized-log-sample.jsonl").open("w", encoding="utf-8") as fh:
    for label, entry in cases.items():
        fh.write(json.dumps({"case": label, **entry}, sort_keys=True) + "\n")
print("wrote schema-validation-evidence.json and sanitized-log-sample.jsonl")
PY
```

**Verify:** The three schema cases are `denied` / `schema_validation_failed` with a short `detail` (no values echoed). Log entries show only allow-listed arg keys; the secret-like value is `[REDACTED]`, the 200-character value is `[TRUNCATED len=200]`, and unexpected keys appear only by name in `_dropped_keys` (secret-like names are themselves `[REDACTED]`). The secret string appears **nowhere** in `tool-call-log.jsonl`.

**Reflect:** If you add a fifth tool tomorrow and forget `AUDIT_KEYS`, what gets logged? (Nothing but dropped key names — that is the point.)

---

## Section 2.4 — Approval gate for `restart_service`

> **⚠ `APPROVE_MUTATIONS=1` IS A TRAINING STUB ONLY.**
> It exists so you can *see* the approved path once, against a handler that does nothing. It is a global environment flag: it is not tied to a particular call, requester, or moment. **It is not acceptable approval for any real mutation.**
>
> **Before any real mutating handler**, require all of:
> 1. **Action-specific approval** — bound to the **exact tool name + exact args** (a changed argument invalidates the approval).
> 2. **Actor identity** — who approved, authenticated, and distinct from the model/agent.
> 3. **Short expiry** — approval is single-use or valid for minutes, not for the session.
> 4. **Audit evidence** — a durable record of approver, tool, args (sanitized per §2.3.2), time, and outcome.
>
> You are **not** asked to build this framework here. Do not ship `restart_service` (or any mutating tool) to a real system on the strength of this chapter's gate.

### 2.4.1 Concept

Privileged tools exist in the schema so the **deny path is demonstrable**. Default: mutations off.

| Gate | Pass condition |
| --- | --- |
| Env flag | `APPROVE_MUTATIONS=1` |
| Interactive | `APPROVE_INTERACTIVE=1` **and** operator types `y` / `yes` |
| Default | Block — write deny evidence |

Both passing conditions are **training gates** (see callout above), not production authorisation.

Never treat “the model asked nicely” as approval.

### 2.4.2 Worked example — approved path (training only)

```bash
# TRAINING STUB ONLY — never use this flag to authorise a real mutation (see §2.4 callout).
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

Add `docs/decisions/0102-harbour-agent-tool-policy.md` (adjust number to your scheme): allow-list, deny-by-default, approval gate, and that `restart_service` is a **stub** for assessment evidence — not a production operator. Also record that argument schemas are validated before approval, and that audit logs hold sanitized args only.

Also write `docs/ai/agents/training-gate-disclaimer.md` stating, in your own words: (1) `APPROVE_MUTATIONS=1` / `APPROVE_INTERACTIVE` are **training stubs only**; (2) a real mutating handler requires approval bound to **exact tool name + args + actor identity + short expiry**, with **audit evidence**; (3) this lab does **not** implement that.

```bash
test -s "$HARBOUR_ROOT/docs/ai/agents/training-gate-disclaimer.md" && \
  python3 - <<'PY'
import os
from pathlib import Path
t = Path(os.environ["HARBOUR_ROOT"], "docs/ai/agents/training-gate-disclaimer.md").read_text(encoding="utf-8").lower()
for needle in ("training", "expiry", "actor", "audit"):
    assert needle in t, f"disclaimer missing: {needle}"
print("disclaimer OK")
PY
```

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

> **Scope — mock-agent implementation.** The planner in this chapter is a **deterministic mock** (`mock_plan`): keyword rules, no model, no provider API. The outcome you build and are assessed on is a **mock-agent implementation** of the plan → tool → observe → answer loop around a real, enforcing `execute_tool`. A **provider tool-calling protocol** (function-calling with OpenAI, Anthropic, etc.) is an **additional / advanced exercise**, **not claimed** by the Practical Assessment.

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
    """MOCK-AGENT planner: deterministic keyword rules, no LLM, no provider tool-calling.

    Swapping in a provider is an advanced exercise; execute_tool must stay the only executor.
    """
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

**Reflect:** If you later swap `mock_plan` for a paid API, does `execute_tool` still own the allow-list, schema validation and audit sanitising? It must.

**Advanced exercise (optional, not assessed):** Replace `mock_plan` with a provider tool-calling adapter that maps the provider's tool-call payload onto `execute_tool(name, args)`, publishing `tool-schemas.json` as the provider's tool definitions. Keep `MOCK_LLM=1` as the default and do not change `execute_tool`'s checks. The Practical Assessment does **not** require this.

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
| `schema_validation_failed` on a valid-looking call | Extra key, wrong type, or schema copy drifted | Read `detail`; re-run the §2.2.2 sync check |
| `RuntimeError: ALLOW_LIST, HANDLERS and TOOL_SCHEMAS...` | Tool added in one place only | Add schema + handler + allow-list entry (+ `AUDIT_KEYS`) together |

---

## Practical Assessment — Chapter 2 — controlled agent path

Align with [A02 Course Detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md) and Final Project Checklist A02: *A privileged or mutating action is blocked unless the designed approval gate passes; show a failed unauthorised attempt.*

### Required deliverables

1. **Tool permission model** — `docs/ai/agents/tool-schemas.json` + embedded `tool_schemas.py` + allow-list/`PRIVILEGED` under `app/ai/diagnostics/`.  
2. **`execute_tool`** — flow is name authorised → arguments valid → approval satisfied → execute; unknown names denied; read-only tools succeed; every call logged to `docs/ai/agents/tool-call-log.jsonl` via `_audit_args` (never raw `args`).  
3. **Approval gate** — `restart_service` blocked unless `APPROVE_MUTATIONS=1` or interactive yes (**training stub only**).  
4. **Failed unauthorised attempt** — `docs/ai/agent-deny-evidence.json` with exact `status`/`reason` fields.  
5. **Orchestration loop** — plan → tool → observe → answer with `MAX_STEPS`; `MOCK_LLM` path documented. Labelled as a **mock-agent implementation**; provider tool-calling is an advanced exercise and is **not** required.  
6. **ADR / boundary note** — `docs/ai/agents/agent-boundary.md` + short ADR on tool policy.  
7. **Schema validation evidence** — `docs/ai/agents/schema-validation-evidence.json` (§2.3.4): missing-required and wrong-type calls return `denied` / `schema_validation_failed`, checked before approval, handler never run.  
8. **Sanitized log sample** — `docs/ai/agents/sanitized-log-sample.jsonl` (§2.3.4): allow-listed arg keys only, secret-like values redacted, long values truncated, no raw secret anywhere in `tool-call-log.jsonl`.  
9. **Training-gate disclaimer** — `docs/ai/agents/training-gate-disclaimer.md` (§2.4.3): `APPROVE_MUTATIONS` is a training stub; real mutations need approval bound to tool + args + actor + short expiry + audit evidence.  
10. Optional: one approved-path smoke with flag set, then flag cleared again.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Tool model | Free-form “run command” | JSON schemas + exact allow-list | Path-constrained readers + typed errors |
| Deny path | Hope / UI only | Filed `agent-deny-evidence.json` with gate reason | Unknown-tool deny in same artefact |
| Approval | Always on / always off | Default blocked; explicit env or interactive yes; disclaimed as training-only | Dual gate + audit of both outcomes |
| Validation & audit | Raw `args` logged; no arg checks | Schema checked before approval; sanitized log sample filed | Allow-listed audit keys per tool + drift check of schema copies |
| Loop | Unbounded chat | Max steps + clear stop conditions | Swappable planner behind same `execute_tool` |
| Safety | Secrets in prompts | Env-only secrets; no raw shell tool | Traversal tests for `read_runbook` |

**Completion:** **Competent** on every row.

### Self-check

- Does the unauthorised demo run with `APPROVE_MUTATIONS=0`?  
- Is evidence at `docs/ai/agent-deny-evidence.json` with exact field asserts (not substring grep)?  
- Can read-only tools still run while mutations are blocked?  
- Is there **no** tool that executes arbitrary shell?  
- Do invalid args fail with `schema_validation_failed` *before* the approval gate, with evidence filed?  
- Does the log hold only sanitized args (no secret-like values, no blind dump of unknown keys)?  
- Does `training-gate-disclaimer.md` say `APPROVE_MUTATIONS` is not production authorisation?  
- Is the loop described as a mock-agent implementation (provider tool-calling not claimed)?  
- Would a second engineer find schemas, log, and deny evidence without asking you?

### Example conclusion (evidence still required)

> Extended A01 `harbour-diag` with allow-listed tools under `app/ai/diagnostics/`. `execute_tool` denies unknown names and blocks `restart_service` unless `APPROVE_MUTATIONS=1`. Unauthorised attempt filed at `docs/ai/agent-deny-evidence.json` (`approval_gate_failed`). Arguments are schema-validated before the (training-stub) approval gate, and audit logs hold sanitized args only (`docs/ai/agents/schema-validation-evidence.json`, `sanitized-log-sample.jsonl`). `APPROVE_MUTATIONS` is disclaimed as training-only in `training-gate-disclaimer.md`. The deterministic mock-agent loop completes health Q&A within max steps and refuses restart without approval; provider tool-calling is not claimed. No raw shell tool; secrets remain in env.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Add a capability | New schema + handler + allow-list entry | Letting the model invent tool names |
| Show checklist A02 | §2.5 deny evidence script | Chat screenshot without JSON |
| Debug a deny | `tool-call-log.jsonl` last lines | Widening allow-list “temporarily” |
| Call a paid model later | Keep `execute_tool` as the only executor | Passing API keys into prompts |
| Leave the lab | `APPROVE_MUTATIONS=0` | Leaving mutations enabled overnight |
| Log a tool call | `_audit_args(name, args)` | Dumping raw `args` into the log |
| Make a mutation real | Per-call approval: tool + args + actor + expiry + audit | Reusing `APPROVE_MUTATIONS=1` |

## Glossary

| Term | Meaning |
| --- | --- |
| Allow-list | Exact set of tool names the runtime will consider |
| Deny-by-default | Anything not explicitly allowed is rejected |
| Approval gate | Extra human/env check before privileged tools run (here: a **training stub**, not production authorisation) |
| Schema validation | Checking tool args against the published schema (required keys, types) before approval/execution |
| Sanitized audit log | Log entries with allow-listed arg keys only; secret-like/long values redacted or truncated |
| Orchestration loop | Repeated plan → tool → observe until stop |
| MOCK_LLM | Local deterministic planner so labs need no paid API |
| Mock-agent implementation | The deterministic `mock_plan` loop assessed here; provider tool-calling is an advanced extra |
| Fail closed | On doubt or error, block the action |

## References

- [OpenAI function / tool calling (concepts)](https://platform.openai.com/docs/guides/function-calling)  
- [Anthropic tool use (concepts)](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)  
- [OWASP LLM Top 10 — excessive agency](https://owasp.org/www-project-top-10-for-large-language-model-applications/)  
- [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) · [A03](A03%20LLMOps%20and%20AI%20Infrastructure.md) · [AI syllabus](../../3%20Course%20Detail/3.3%20AI%20Engineering/A00%20AI%20Syllabus.md)

**Previous chapter:** [Chapter 1 — Applied AI and LLM Engineering (A01)](A01%20Applied%20AI%20and%20LLM%20Engineering.md) · **Course detail:** [A02](../../3%20Course%20Detail/3.3%20AI%20Engineering/A02%20Agents%20and%20Orchestration.md) · **Next chapter:** [Chapter 3 — LLMOps and AI Infrastructure (A03)](A03%20LLMOps%20and%20AI%20Infrastructure.md) · **Checklist:** [Final Project Checklist · A02](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
