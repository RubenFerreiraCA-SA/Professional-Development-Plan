# Chapter 3 — LLMOps and AI Infrastructure (A03)

*AI Engineering textbook · Chapter 3 of 3 · **Optional track***

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see [A03 course detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A03%20LLMOps%20and%20AI%20Infrastructure.md) (about 32–40 hours). |
| **Prerequisites** | [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) and [A02](A02%20Agents%20and%20Orchestration.md) — `harbour-diag`, eval cases, tool allow-list, and approval gate working (MOCK path fine). |

## How to study this chapter

A03 treats the diagnostics assistant as a **service you can operate**: pinned versions, health that reports AI on/off, **one-action disable or rollback**, cost/safety caps, and monitoring hooks. This is **LLMOps for a product feature**, not training models from scratch.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Prefer MOCK / local so labs stay free. Provider keys stay in env only — never in Git.

This text teaches [A03 Course Detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A03%20LLMOps%20and%20AI%20Infrastructure.md). Checklist bar: *You can disable or roll back the AI path in one documented action; basic cost/safety limits or monitors exist.*

> **Safety and cost boundary:** No API keys or secrets in Git. Prefer `MOCK_LLM=1`. If using a paid API, set token/budget caps first; destroy/idle any cloud endpoints when done. Redact evidence under `docs/ai/` before filing.

### Learning outcomes

1. Explain LLMOps as operating an LLM **feature** (version, serve, observe, limit, kill) — not MLOps-from-scratch.  
2. Pin prompt, tools policy, and model id in `app/ai/diagnostics/VERSION` with a changelog.  
3. Serve diagnostics locally or via Compose with `/health` reporting AI enabled/disabled.  
4. Disable or roll back AI in **one documented action** and keep proof.  
5. Enforce mockable cost/safety limits and structured logs; gate CI on A01 eval JSON.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"

test -d "$HARBOUR_ROOT/app/ai/diagnostics" || {
  echo "Missing app/ai/diagnostics — complete A01 (and A02) first"
  exit 1
}

mkdir -p docs/ai/ops docs/runbooks docs/decisions deploy/ai

export MOCK_LLM="${MOCK_LLM:-1}"
export HARBOUR_AI_ENABLED="${HARBOUR_AI_ENABLED:-true}"

if test -x "$HARBOUR_ROOT/.venv/bin/python"; then
  # shellcheck disable=SC1091
  . "$HARBOUR_ROOT/.venv/bin/activate"
fi

command -v python3 >/dev/null || { echo "Need python3"; exit 1; }
```

You need A01’s `docs/ai/eval-a01.json`, A02 deny evidence, and ability to restart the diag process. Link lightly to [D07 Observability](../4.1%20DevOps/D07%20Observability.md) for log/metric ideas — a full OTel stack is **not** required to pass A03.

---

## Section 3.1 — What LLMOps means for Harbour

### 3.1.1 Not MLOps-from-scratch

| Concern | Classic MLOps (out of scope) | Harbour LLMOps (in scope) |
| --- | --- | --- |
| Artefact | Weights, feature store | Prompt + tools policy + model **id** + app code |
| Deploy | Training pipeline / GPU serving | App/Compose or feature flag for `harbour-diag` |
| Change control | Dataset/model lineage | `VERSION` pin + changelog + one-action rollback |
| Risk | Silent prediction drift | Cost blow-ups, unsafe tools, stale prompts |
| Stop button | Undeploy model | `HARBOUR_AI_ENABLED=false` (+ restart) |

**Reflect:** If the plan starts with “fine-tune a model,” you are solving the wrong problem. Operate the **feature** A01/A02 already built.

### 3.1.2 Worked example — ADR

Write `docs/decisions/0203-harbour-llmops.md` before deploy layout changes:

```markdown
# ADR 0203 — Harbour LLMOps (diagnostics assistant)
## Status: Accepted (date)
## Context: Optional harbour-diag needs pins, caps, monitors, one-action disable/rollback.
## Decision
- Kill switch: HARBOUR_AI_ENABLED=false
- Pin: app/ai/diagnostics/VERSION (+ CHANGELOG.md)
- Serve: uvicorn and/or deploy/ai Compose; /health reports ai.enabled
- Limits: max tokens, rate, budget (mockable); evidence under docs/ai/ops/
## Consequences: Core Harbour stays up when AI is off. Rollback = flag or VERSION + restart.
```

### 3.1.3 Practice

If AI is out of scope in your Capacity Planner, mark Checklist A03 `N/A` — do not half-ship an unkillable path.

---

## Section 3.2 — Versioning prompts, tools policy, and model id

### 3.2.1 Single source of truth

| Field | Example | Why |
| --- | --- | --- |
| `prompt_version` | `diag-prompt-2026-03` | System prompt / refusal text |
| `tools_policy_version` | `tools-allow-v2` | A02 allow-list + approval rules |
| `model_id` | `mock-llm` or provider id | Model string (never a secret) |
| `bundle_version` | `1.0.0` | One pin for “what ran?” |

### 3.2.2 Worked example — VERSION + changelog

**Recording a version ≠ deploying that version.** Changing `bundle_version` alone does not roll back code. Pin metadata **and** an artifact identity (Git SHA or image digest). Rollback restores the known-good software + matching `VERSION`.

```bash
GIT_SHA="$(git -C "$HARBOUR_ROOT" rev-parse --short HEAD 2>/dev/null || echo uncommitted)"
cat > "$HARBOUR_ROOT/app/ai/diagnostics/VERSION" <<EOF
prompt_version=diag-prompt-2026-03
tools_policy_version=tools-allow-v2
model_id=mock-llm
bundle_version=1.0.0
git_sha=${GIT_SHA}
EOF

cat > "$HARBOUR_ROOT/app/ai/diagnostics/CHANGELOG.md" <<'EOF'
# harbour-diag changelog

## 1.0.0
- Initial operable pin for A03
EOF

cp -a "$HARBOUR_ROOT/app/ai/diagnostics/VERSION" \
  "$HARBOUR_ROOT/docs/ai/ops/VERSION.pinned.txt"
```

```python
# app/ai/diagnostics/versioning.py
from __future__ import annotations
from pathlib import Path

VERSION_PATH = Path(__file__).resolve().parent / "VERSION"

def load_version(path: Path = VERSION_PATH) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing VERSION pin: {path}")
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    for required in ("prompt_version", "tools_policy_version", "model_id", "bundle_version"):
        if required not in data:
            raise KeyError(f"VERSION missing {required}")
    data.setdefault("git_sha", "")  # optional artifact identity (Git SHA / digest)
    return data
```

**Verify:**

```bash
cd "$HARBOUR_ROOT"
PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -c "from ai.diagnostics.versioning import load_version; print(load_version())"
```

### 3.2.3 Practice

Bump `bundle_version` to `1.0.1`, append a changelog line, save `docs/ai/ops/VERSION.after-bump.txt`. Rollback later = restore previous `VERSION` + restart.

### 3.2.4 Mandatory — create `limits.py` and `telemetry.py` before the API

Section 3.3’s `api.py` imports these modules. Create them **now** or `uvicorn` fails with `ModuleNotFoundError`. Sections 3.5–3.6 deepen drills against the same files — do not wait until then.

```python
# app/ai/diagnostics/limits.py
from __future__ import annotations
import os, time
from collections import defaultdict, deque

# Distinct controls — do not reuse MAX_OUT_TOKENS as an input-size ceiling.
MAX_IN_TOKENS = int(os.getenv("HARBOUR_AI_MAX_IN_TOKENS", "2000"))   # prompt/question estimate cap
MAX_OUT_TOKENS = int(os.getenv("HARBOUR_AI_MAX_OUT_TOKENS", "512"))  # reserved completion budget + provider max_tokens
RATE_MAX = int(os.getenv("HARBOUR_AI_RATE_MAX", "30"))
RATE_WINDOW_S = int(os.getenv("HARBOUR_AI_RATE_WINDOW_S", "300"))
BUDGET_TOKENS = int(os.getenv("HARBOUR_AI_BUDGET_TOKENS", "20000"))  # aggregate estimated spend

_hits: dict[str, deque[float]] = defaultdict(deque)
_spent = 0


def estimate_input_tokens(question: str, overhead: int = 200) -> int:
    """Rough prompt-side estimate (chars/4 + fixed overhead). Not provider billing."""
    return max(1, len(question) // 4 + overhead)


def check_request(
    identity: str = "local",
    *,
    est_input_tokens: int,
    reserve_output_tokens: int | None = None,
) -> dict:
    """In-process training limiter only — not durable multi-replica spend control.

    Separates: input allowance, reserved output tokens, and aggregate budget.
    """
    global _spent
    out_reserve = MAX_OUT_TOKENS if reserve_output_tokens is None else int(reserve_output_tokens)
    if est_input_tokens > MAX_IN_TOKENS:
        return {
            "allowed": False,
            "reason": "input_tokens",
            "est_input_tokens": est_input_tokens,
            "max_in_tokens": MAX_IN_TOKENS,
        }
    if out_reserve > MAX_OUT_TOKENS:
        return {
            "allowed": False,
            "reason": "output_tokens",
            "reserve_output_tokens": out_reserve,
            "max_out_tokens": MAX_OUT_TOKENS,
        }
    total_est = est_input_tokens + out_reserve
    now = time.time()
    q = _hits[identity]
    while q and now - q[0] > RATE_WINDOW_S:
        q.popleft()
    if len(q) >= RATE_MAX:
        return {"allowed": False, "reason": "rate_limited"}
    if _spent + total_est > BUDGET_TOKENS:
        return {
            "allowed": False,
            "reason": "budget_exceeded",
            "spent": _spent,
            "total_est": total_est,
            "budget_tokens": BUDGET_TOKENS,
        }
    q.append(now)
    _spent += total_est
    return {
        "allowed": True,
        "spent": _spent,
        "est_input_tokens": est_input_tokens,
        "reserve_output_tokens": out_reserve,
        "max_out_tokens": MAX_OUT_TOKENS,
    }
```

```python
# app/ai/diagnostics/telemetry.py
from __future__ import annotations
import json, os, time
from pathlib import Path
from ai.diagnostics.versioning import load_version

def log_call(*, latency_ms: float, tokens_in: int, tokens_out: int,
             tool_denials: list[str], limit_reason: str = "",
             ai_enabled: bool = True, result: str = "ok") -> None:
    """Called from api.diagnose on every request path."""
    ver = load_version()
    event = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "harbour_diag_call",
        "result": result,
        "latency_ms": round(latency_ms, 2),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tool_denials": tool_denials,
        "limit_reason": limit_reason,
        "ai_enabled": ai_enabled,
        **ver,
    }
    line = json.dumps(event, sort_keys=True)
    print(line, flush=True)
    log_path = Path(os.environ.get(
        "HARBOUR_AI_TELEMETRY_PATH",
        str(Path(os.environ.get("HARBOUR_ROOT", ".")) / "docs" / "ai" / "ops" / "telemetry.jsonl"),
    ))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
```

```bash
test -f "$HARBOUR_ROOT/app/ai/diagnostics/limits.py"
test -f "$HARBOUR_ROOT/app/ai/diagnostics/telemetry.py"
test -f "$HARBOUR_ROOT/app/ai/diagnostics/VERSION"
PYTHONPATH="$HARBOUR_ROOT/app" python3 -c \
  "from ai.diagnostics.limits import check_request; from ai.diagnostics.telemetry import log_call; print('ops modules ok')"
```

---

## Section 3.3 — Packaging and serving

### 3.3.0 Prerequisites checklist (before uvicorn or Compose)

Confirm these exist from A01–A02 and §3.2:

| Artifact | Purpose |
| --- | --- |
| `app/ai/diagnostics/{retrieve,llm,agent_runtime,versioning,limits,telemetry}.py` | Import graph for `api.py` |
| `app/ai/diagnostics/VERSION` | `/health` pin (+ `git_sha`) |
| `docs/runbooks/*.md` | A01 retrieval corpus |
| `docs/ai/` writable | Telemetry + A02 audit logs |

Compose (§3.3.2) is an **integration milestone after** this checklist — not a standalone shortcut.

### 3.3.1 Health must report AI state

`/v1/diagnose` must run the **real** A01/A02 path — not echo the request. Expected request path:

1. Feature enabled?  
2. Validate request + apply rate/token/budget limits.  
3. Retrieve authorized runbook context (A01).  
4. Optionally gather tool observations via A02 `execute_tool` (read-only).  
5. Call A01 `complete` + schema validation.  
6. Record sanitized telemetry; return structured result (never echo the raw body).

```python
# app/ai/diagnostics/api.py
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ai.diagnostics.agent_runtime import execute_tool
from ai.diagnostics.limits import MAX_OUT_TOKENS, check_request, estimate_input_tokens
from ai.diagnostics.llm import LlmError, complete
from ai.diagnostics.retrieve import load_corpus, retrieve
from ai.diagnostics.telemetry import log_call
from ai.diagnostics.versioning import load_version

app = FastAPI(title="harbour-diag")


def ai_enabled() -> bool:
    return os.getenv("HARBOUR_AI_ENABLED", "true").lower() in ("1", "true", "yes", "on")


def harbour_root() -> Path:
    return Path(os.environ.get("HARBOUR_ROOT", Path.home() / "harbour-platform")).expanduser()


@app.get("/health")
def health():
    ver = load_version()
    return {
        "service": "harbour-diag",
        "status": "ok",
        "ai": {
            "enabled": ai_enabled(),
            "bundle_version": ver["bundle_version"],
            "model_id": ver["model_id"],
            "prompt_version": ver["prompt_version"],
            "tools_policy_version": ver["tools_policy_version"],
            "git_sha": ver.get("git_sha", ""),
        },
    }


MAX_QUESTION_LEN = int(os.getenv("HARBOUR_AI_MAX_QUESTION_LEN", "2000"))


def _fail(t0: float, *, error: str, status: int, ai_on: bool, tokens_in: int = 0, **extra: Any):
    """Shared completion path — validation failures are instrumented too."""
    log_call(
        latency_ms=(time.perf_counter() - t0) * 1000,
        tokens_in=tokens_in,
        tokens_out=0,
        tool_denials=[],
        limit_reason=error if error in ("rate_limited", "budget_exceeded", "input_tokens", "output_tokens") else "",
        ai_enabled=ai_on,
        result=error,
    )
    body = {"ok": False, "error": error, **extra}
    return JSONResponse(body, status_code=status)


@app.post("/v1/diagnose")
async def diagnose(request: Request):
    t0 = time.perf_counter()
    tool_denials: list[str] = []
    limit_reason = ""
    # MOCK identity only — a client can spoof this header. Real deployments must
    # derive identity from authenticated middleware / a trusted gateway, not raw headers.
    identity = request.headers.get("x-harbour-identity", "local")

    if not ai_enabled():
        return _fail(t0, error="ai_disabled", status=503, ai_on=False,
                     hint="HARBOUR_AI_ENABLED=true to enable")

    try:
        raw: Any = await request.json()
    except Exception:
        return _fail(t0, error="invalid_json", status=400, ai_on=True)
    if not isinstance(raw, dict):
        return _fail(
            t0, error="body_must_be_object", status=400, ai_on=True,
            hint="JSON body must be a JSON object",
        )

    question_raw = raw.get("question", raw.get("q", None))
    if question_raw is None:
        return _fail(
            t0, error="missing_question", status=400, ai_on=True,
            hint="JSON object needs string field question",
        )
    if not isinstance(question_raw, str):
        return _fail(t0, error="question_must_be_string", status=400, ai_on=True)
    question = question_raw.strip()
    if not question:
        return _fail(
            t0, error="missing_question", status=400, ai_on=True,
            hint="question must be non-empty",
        )
    if len(question) > MAX_QUESTION_LEN:
        return _fail(
            t0, error="question_too_long", status=400, ai_on=True,
            max=MAX_QUESTION_LEN, tokens_in=len(question) // 4,
        )
    # Do not echo the body — it may later contain sensitive operational text.

    est_in = estimate_input_tokens(question)
    lim = check_request(
        identity=identity,
        est_input_tokens=est_in,
        reserve_output_tokens=MAX_OUT_TOKENS,
    )
    if not lim.get("allowed"):
        limit_reason = str(lim.get("reason") or "limited")
        return _fail(
            t0, error=limit_reason, status=429, ai_on=True,
            tokens_in=est_in,
            limits={k: lim[k] for k in lim if k != "allowed"},
        )

    root = harbour_root()
    health_text = ""
    # A02 read-only tool path (allow-list + schema + audit); denials are recorded.
    import json as _json
    health_obs = execute_tool("get_health", {})
    if health_obs.get("status") == "ok":
        health_text = _json.dumps(health_obs.get("result") or {}, sort_keys=True)
    elif health_obs.get("status") == "denied":
        tool_denials.append(f"get_health:{health_obs.get('reason')}")

    try:
        corpus = load_corpus(root / "docs" / "runbooks")
        context = retrieve(question, corpus, k=3)
    except FileNotFoundError as e:
        log_call(
            latency_ms=(time.perf_counter() - t0) * 1000,
            tokens_in=len(question) // 4,
            tokens_out=0,
            tool_denials=tool_denials,
            limit_reason="",
            ai_enabled=True,
            result="missing_runbooks",
        )
        return JSONResponse({"ok": False, "error": "missing_runbooks", "detail": str(e)}, status_code=500)

    try:
        result = complete(question, context, health_text=str(health_text))
    except LlmError as e:
        log_call(
            latency_ms=(time.perf_counter() - t0) * 1000,
            tokens_in=len(question) // 4,
            tokens_out=0,
            tool_denials=tool_denials,
            limit_reason="",
            ai_enabled=True,
            result="llm_error",
        )
        return JSONResponse({"ok": False, "error": "llm_error", "detail": str(e)}, status_code=502)

    answer = str(result.get("answer") or "")
    log_call(
        latency_ms=(time.perf_counter() - t0) * 1000,
        tokens_in=len(question) // 4,
        tokens_out=len(answer) // 4,
        tool_denials=tool_denials,
        limit_reason=limit_reason,
        ai_enabled=True,
        result="ok" if not result.get("refused") else "refused",
    )
    ver = load_version()
    return {
        "ok": True,
        "mode": "mock" if os.getenv("MOCK_LLM", "1") != "0" else "live",
        "bundle_version": ver["bundle_version"],
        "context_empty": not bool(context.strip()),
        "diagnosis": result,  # validated A01 schema: answer, citations, confidence, refused…
        "tool_denials": tool_denials,
    }
```

```bash
cd "$HARBOUR_ROOT"
# shellcheck disable=SC1091
test -f .venv/bin/activate && . .venv/bin/activate
pip install -q 'fastapi>=0.110' 'uvicorn[standard]>=0.27'

# VERSION must include git_sha (or leave empty) — see §3.2; bind pin to an artifact.
export MOCK_LLM=1 HARBOUR_AI_ENABLED=true HARBOUR_ROOT
export PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
uvicorn ai.diagnostics.api:app --host 127.0.0.1 --port 8088 &
UV_PID=$!
sleep 1
curl -sS http://127.0.0.1:8088/health | tee "$HARBOUR_ROOT/docs/ai/ops/health-enabled.json"
# Integrated diagnose — grounded answer, not an echo:
curl -sS -X POST http://127.0.0.1:8088/v1/diagnose \
  -H 'content-type: application/json' \
  -d '{"question":"What does GET /health status degraded mean?"}' \
  | tee "$HARBOUR_ROOT/docs/ai/ops/diagnose-grounded.json"
python3 - <<'PY'
import json, pathlib, sys
d = json.loads(pathlib.Path("docs/ai/ops/diagnose-grounded.json").read_text())
assert d.get("ok") is True and "echo" not in d
diag = d["diagnosis"]
assert diag.get("refused") is False
assert diag.get("citations") or d.get("context_empty") is False or diag.get("confidence") == "low"
print("integrated_diagnose_ok")
PY
kill "$UV_PID"
```

### 3.3.2 Optional Compose service (integration milestone only)

Run Compose **only after** §3.3.0 prerequisites pass (all Python modules, `VERSION`, seed runbooks). Premature `docker compose up` fails on imports or empty retrieval.

Prefer `deploy/ai/` over forking main app Compose:

```yaml
# deploy/ai/docker-compose.yml
services:
  harbour-diag:
    image: python:3.12-slim
    working_dir: /app
    # Mount Harbour app/ so `ai.diagnostics` imports match local PYTHONPATH=$HARBOUR_ROOT/app
    volumes:
      - ../../app:/app:ro
      - ../../docs:/docs  # rw: A02 tool audit + A03 telemetry under docs/ai/
    environment:
      HARBOUR_AI_ENABLED: "${HARBOUR_AI_ENABLED:-true}"
      MOCK_LLM: "${MOCK_LLM:-1}"
      HARBOUR_ROOT: /
      PYTHONPATH: /app
    command: >
      bash -lc "pip install -q fastapi 'uvicorn[standard]' &&
      uvicorn ai.diagnostics.api:app --host 0.0.0.0 --port 8088"
    ports: ["8088:8088"]
    healthcheck:
      test: ["CMD", "python", "-c",
        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8088/health')"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 40s
```

```bash
cd "$HARBOUR_ROOT"
# Prerequisites (fail closed before Compose):
test -f app/ai/diagnostics/api.py
test -f app/ai/diagnostics/limits.py
test -f app/ai/diagnostics/telemetry.py
test -f app/ai/diagnostics/VERSION
test -n "$(find docs/runbooks -name '*.md' 2>/dev/null | head -n 1)" || {
  echo "Seed docs/runbooks first (A01)"; exit 1
}
docker compose -f deploy/ai/docker-compose.yml up -d
# Bounded readiness:
for i in $(seq 1 40); do
  curl -sf http://127.0.0.1:8088/health && break
  sleep 0.5
done
curl -sS http://127.0.0.1:8088/health | tee docs/ai/ops/health-compose.json
docker compose -f deploy/ai/docker-compose.yml down   # idle when done
```

**Reflect:** Core Harbour (D03 `/health`) stays valid when AI is off — diag is an add-on unless your ADR says otherwise.

---

## Section 3.4 — Kill switch / rollback in one action

### 3.4.1 One documented action

The syllabus promises **one action**. Encapsulate env flip + recreate + verify in a script — do not leave operators to improvise multi-step shell.

| Goal | One action |
| --- | --- |
| Disable | `./scripts/disable-harbour-ai.sh` |
| Re-enable | `./scripts/enable-harbour-ai.sh` (optional mirror) |
| Roll back pin + code | Restore known-good Git SHA / image **and** matching `VERSION`, then restart |

Core Harbour API must stay up; the script only touches `harbour-diag`.

### 3.4.2 Worked example — `scripts/disable-harbour-ai.sh`

Do **not** use `pkill -f` against a command string — that can kill unrelated processes. Own a specific PID file, verify the process cmdline, then stop that PID. Use a bounded readiness loop instead of fixed sleeps.

Also add a tiny starter that writes the PID (use this whenever you bring diag up for labs):

```bash
# scripts/start-harbour-ai.sh — starts diag and records owned instance identity
set -euo pipefail
ROOT="$(cd "${HARBOUR_ROOT:-$HOME/harbour-platform}" && pwd)"
cd "$ROOT"
mkdir -p docs/ai/ops scripts
ENABLED="${HARBOUR_AI_ENABLED:-true}"
export PYTHONPATH="$ROOT/app${PYTHONPATH:+:$PYTHONPATH}" MOCK_LLM="${MOCK_LLM:-1}" HARBOUR_ROOT="$ROOT"
HARBOUR_AI_ENABLED="$ENABLED" uvicorn ai.diagnostics.api:app --host 127.0.0.1 --port 8088 \
  >docs/ai/ops/uvicorn.log 2>&1 &
PID=$!
echo "$PID" > docs/ai/ops/harbour-diag.pid
# Record enough identity to refuse stale/reused PIDs later (cwd + start time + cmdline mark).
{
  echo "pid=$PID"
  echo "root=$ROOT"
  echo "started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "cmdline_mark=ai.diagnostics.api"
  if [[ -r "/proc/$PID/cwd" ]]; then echo "cwd=$(readlink -f "/proc/$PID/cwd")"; fi
  if [[ -r "/proc/$PID/stat" ]]; then
    # field 22 = starttime (clock ticks) — opaque ownership token for this boot
    awk '{print "starttime="$22}' "/proc/$PID/stat"
  fi
} > docs/ai/ops/harbour-diag.identity
# Bounded readiness (not a fixed sleep). Confirm *this* PID is still alive so an
# unrelated listener on :8088 is not mistaken for the process we just launched.
for i in $(seq 1 30); do
  if [[ ! -e "/proc/$PID" ]]; then
    echo "pid $PID exited before readiness"; exit 1
  fi
  if curl -sf http://127.0.0.1:8088/health >/dev/null; then
    echo "ready pid=$PID enabled=$ENABLED root=$ROOT"
    exit 0
  fi
  sleep 0.2
done
echo "diag failed to become ready"; exit 1
```

```bash
# scripts/disable-harbour-ai.sh — ONE ACTION disable with verification
set -euo pipefail
ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$ROOT"
mkdir -p docs/ai/ops
BASE="http://127.0.0.1:8088"
CORE_URL="${HARBOUR_CORE_HEALTH_URL:-http://127.0.0.1:8000/health}"
MODE="${HARBOUR_AI_DISABLE_MODE:-local}"  # local | compose
REQUIRE_CORE="${HARBOUR_AI_REQUIRE_CORE_CHECK:-0}"  # set 1 for exit assessment when core is in scope

wait_ready() {
  local i
  for i in $(seq 1 30); do
    if curl -sf "$BASE/health" >/dev/null; then return 0; fi
    sleep 0.2
  done
  echo "health not ready at $BASE"; return 1
}

stop_local_pid() {
  local pid_file="docs/ai/ops/harbour-diag.pid"
  local id_file="docs/ai/ops/harbour-diag.identity"
  test -f "$pid_file" || { echo "missing $pid_file — start with scripts/start-harbour-ai.sh first"; exit 1; }
  test -f "$id_file" || { echo "missing $id_file — refuse stop without ownership record"; exit 1; }
  local pid expected_root expected_start
  pid="$(sed -n 's/^pid=//p' "$id_file" | head -n1)"
  expected_root="$(sed -n 's/^root=//p' "$id_file" | head -n1)"
  expected_start="$(sed -n 's/^starttime=//p' "$id_file" | head -n1)"
  [[ "$pid" =~ ^[0-9]+$ ]] || { echo "invalid pid in identity file"; exit 1; }
  [[ "$(cat "$pid_file")" == "$pid" ]] || { echo "pid file / identity mismatch"; exit 1; }
  if [[ ! -r "/proc/$pid/cmdline" ]]; then
    echo "pid $pid not running"; rm -f "$pid_file" "$id_file"; return 0
  fi
  local cmd cwd starttime
  cmd="$(tr '\0' ' ' <"/proc/$pid/cmdline")"
  echo "$cmd" | grep -q 'ai.diagnostics.api' || {
    echo "refusing to kill pid $pid — cmdline is not harbour-diag: $cmd"
    exit 1
  }
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  if [[ -n "$expected_root" && -n "$cwd" && "$cwd" != "$expected_root" ]]; then
    echo "refusing to kill pid $pid — cwd $cwd != recorded root $expected_root"
    exit 1
  fi
  if [[ -n "$expected_start" && -r "/proc/$pid/stat" ]]; then
    starttime="$(awk '{print $22}' "/proc/$pid/stat")"
    if [[ "$starttime" != "$expected_start" ]]; then
      echo "refusing to kill pid $pid — starttime mismatch (stale/reused PID)"
      exit 1
    fi
  fi
  kill "$pid"
  local i
  for i in $(seq 1 30); do
    if [[ ! -e "/proc/$pid" ]]; then rm -f "$pid_file" "$id_file"; return 0; fi
    sleep 0.1
  done
  echo "pid $pid did not exit"; exit 1
}

capture_core() {
  # Require HTTP success (2xx via curl -f), not merely parseable JSON.
  local out="$1"
  local code
  code="$(curl -fsS --max-time 5 -o "$out" -w '%{http_code}' "$CORE_URL")" || {
    echo "Core Harbour unhealthy at $CORE_URL (failed before writing usable evidence)"
    exit 1
  }
  echo "core_http=$code file=$out"
}

# BEFORE any AI shutdown: capture true before-state when core is in the exit assessment.
if [[ "$REQUIRE_CORE" == "1" ]]; then
  capture_core docs/ai/ops/core-health-before-disable.json
fi

if [[ "$MODE" == "compose" ]]; then
  test -f deploy/ai/docker-compose.yml || { echo "missing deploy/ai/docker-compose.yml"; exit 1; }
  printf 'HARBOUR_AI_ENABLED=false\nMOCK_LLM=%s\n' "${MOCK_LLM:-1}" > deploy/ai/.env
  docker compose -f deploy/ai/docker-compose.yml up -d --force-recreate
  wait_ready
else
  stop_local_pid
  export HARBOUR_AI_ENABLED=false
  export MOCK_LLM="${MOCK_LLM:-1}" HARBOUR_ROOT="$ROOT"
  export PYTHONPATH="$ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
  ./scripts/start-harbour-ai.sh   # writes new PID; bounded readiness; respects ENABLED=false
fi

curl -fsS "$BASE/health" | tee docs/ai/ops/health-after-disable.json >/dev/null
curl -sS -X POST "$BASE/v1/diagnose" -H 'content-type: application/json' \
  -d '{"question":"status?"}' | tee docs/ai/ops/diagnose-after-disable.json

# AFTER disable verified: independently re-check core (fresh measurement, not a reused baseline).
if [[ "$REQUIRE_CORE" == "1" ]]; then
  capture_core docs/ai/ops/core-health-still-up.json
fi

python3 - <<'PY'
import json, os, pathlib, sys
r = pathlib.Path("docs/ai/ops")
a = json.loads((r / "health-after-disable.json").read_text())
d = json.loads((r / "diagnose-after-disable.json").read_text())
ok = a.get("ai", {}).get("enabled") is False and d.get("error") == "ai_disabled"
if os.environ.get("HARBOUR_AI_REQUIRE_CORE_CHECK") == "1":
    before = json.loads((r / "core-health-before-disable.json").read_text())
    after = json.loads((r / "core-health-still-up.json").read_text())
    # Bodies were only written after curl -f succeeded (HTTP 2xx).
    ok = ok and isinstance(before, dict) and isinstance(after, dict)
print("disable_ok=", ok)
sys.exit(0 if ok else 1)
PY
```

```bash
chmod +x "$HARBOUR_ROOT/scripts/start-harbour-ai.sh" "$HARBOUR_ROOT/scripts/disable-harbour-ai.sh"
# Baseline (enabled). For exit assessment with core Harbour in scope, export REQUIRE_CORE=1.
export HARBOUR_AI_ENABLED=true
./scripts/start-harbour-ai.sh
curl -sS http://127.0.0.1:8088/health | tee docs/ai/ops/health-before-disable.json
# ONE ACTION (disable script captures fresh core before+after when REQUIRE_CORE=1):
HARBOUR_AI_REQUIRE_CORE_CHECK="${HARBOUR_AI_REQUIRE_CORE_CHECK:-0}" \
  HARBOUR_AI_ENABLED=false ./scripts/disable-harbour-ai.sh | tee docs/ai/ops/disable-script.out
```

Beyond the lab, prefer Compose/systemd (or similar) over custom PID files. The identity file is a training hardening against stale PIDs, not a production process manager.

Runbook stub — `docs/runbooks/ai-disable-rollback.md`:

```markdown
# Runbook — Disable or roll back harbour-diag (one action)

## Disable
Run: `./scripts/disable-harbour-ai.sh`
Verify: docs/ai/ops/health-after-disable.json has ai.enabled=false;
        diagnose returns error=ai_disabled.
Core Harbour /health (e.g. :8000) must still succeed if it was up.

## Roll back VERSION + code
1. Check out known-good Git SHA (or redeploy known-good image digest).
2. Restore matching docs/ai/ops/VERSION.pinned.txt → app/ai/diagnostics/VERSION.
3. Restart diag; confirm /health bundle_version + git_sha.

Do not tear down core Harbour. Re-enable: HARBOUR_AI_ENABLED=true + restart (or enable script).
```

### 3.4.3 Practice

Execute disable **via the script only**; fix the script/runbook if tribal knowledge was required.

---

## Section 3.5 — Cost and safety limits

You created `limits.py` in §3.2.4. This section explains and drills it.

### 3.5.1 Basic limits

| Limit | Training default | When exceeded |
| --- | --- | --- |
| Max **input** tokens | `HARBOUR_AI_MAX_IN_TOKENS` (2000) | 429 `input_tokens` |
| Max **output** tokens | `HARBOUR_AI_MAX_OUT_TOKENS` (512) | reserved in limiter; live path sets provider `max_tokens` |
| Aggregate budget | `HARBOUR_AI_BUDGET_TOKENS` (input+reserved out) | 429 `budget_exceeded` |
| Rate limit | e.g. 30 / 5 min / **mock** identity | 429 `rate_limited` |
| Question length | `HARBOUR_AI_MAX_QUESTION_LEN` (2000) | 400 `question_too_long` |
| Redaction | strip `sk-`, Bearer, passwords | Never commit raw secrets |

**Mock identity:** `/v1/diagnose` keys the limiter with `x-harbour-identity` (default `local`). That header is a **training demo only** — any client can spoof it to change buckets. A real deployment must derive identity from authenticated middleware or a trusted gateway. The in-memory limiter also resets on process restart and is not shared across replicas; token estimates are not invoices. Do not claim durable spend control or secure per-user quotas from this lab alone.

### 3.5.2 Worked example — enforce via the API

`check_request` is already wired inside `/v1/diagnose` (§3.3). Prove both allow and deny through HTTP:

```bash
cd "$HARBOUR_ROOT"
export HARBOUR_AI_BUDGET_TOKENS=500 HARBOUR_AI_RATE_MAX=2
export PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}" MOCK_LLM=1 HARBOUR_AI_ENABLED=true HARBOUR_ROOT
uvicorn ai.diagnostics.api:app --host 127.0.0.1 --port 8088 &
UV_PID=$!; sleep 1
: > docs/ai/ops/limits-api-drill.jsonl
for i in 1 2 3; do
  curl -sS -X POST http://127.0.0.1:8088/v1/diagnose \
    -H 'content-type: application/json' -H 'x-harbour-identity: lab' \
    -d "{\"question\":\"health check $i\"}" | tee -a docs/ai/ops/limits-api-drill.jsonl
  echo >> docs/ai/ops/limits-api-drill.jsonl
done
python3 - <<'PY'
import json, pathlib, sys
rows = []
for line in pathlib.Path("docs/ai/ops/limits-api-drill.jsonl").read_text().splitlines():
    line = line.strip()
    if line:
        rows.append(json.loads(line))
assert any(r.get("ok") is True for r in rows), rows
assert any(
    r.get("error") in ("rate_limited", "budget_exceeded", "input_tokens", "output_tokens")
    for r in rows
), rows
print("limits_enforced_via_api_ok")
PY
kill "$UV_PID"
```

Also confirm live-provider completions pass `max_tokens` (A01 `openai_complete` reads `HARBOUR_AI_MAX_OUT_TOKENS`) — that is the explicit provider output ceiling, separate from input allowance and aggregate budget.

### 3.5.3 Redaction

```bash
sed -E 's/(sk-[A-Za-z0-9_-]+)/[REDACTED]/g; s/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g' \
  docs/ai/ops/raw-sample.log > docs/ai/ops/sample-redacted.log
```

---

## Section 3.6 — Monitoring hooks

You created `telemetry.py` in §3.2.4 and wired `log_call` into `api.diagnose`. Minimum fields: `ts`, `latency_ms`, `tokens_in`/`tokens_out`, `bundle_version`/`model_id`, `ai_enabled`, `tool_denials`, `limit_reason`, `result`.

Evidence must come from **real API requests** (not a standalone helper call). After the §3.3 integrated diagnose curl and the limits drill:

```bash
test -s "$HARBOUR_ROOT/docs/ai/ops/telemetry.jsonl" || {
  echo "No runtime telemetry — ensure api.diagnose calls log_call"
  exit 1
}
tail -n 5 "$HARBOUR_ROOT/docs/ai/ops/telemetry.jsonl" \
  | tee "$HARBOUR_ROOT/docs/ai/ops/sample-structured-log.jsonl"
# Expect rows with result in ok|refused|rate_limited|budget_exceeded|ai_disabled
```

Optional: counter `harbour_diag_requests_total{result=…}` later (D07-style) — JSONL from the live API is enough for Competent.

---

## Section 3.7 — Integrated API regression test + eval gate

### 3.7.1 Worked example — FastAPI TestClient (A01→A03 contract)

Protect the integrated path with a small offline test (no live uvicorn required):

```python
# app/ai/diagnostics/tests/test_api_integration.py
from __future__ import annotations
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Force mock + writable ops dir before importing app
ROOT = Path(os.environ.get("HARBOUR_ROOT", Path.home() / "harbour-platform")).expanduser()
os.environ["HARBOUR_ROOT"] = str(ROOT)
os.environ["MOCK_LLM"] = "1"
os.environ["HARBOUR_AI_ENABLED"] = "true"
os.environ["HARBOUR_AI_RATE_MAX"] = "100"
os.environ["PYTHONPATH"] = str(ROOT / "app")

from ai.diagnostics.api import app  # noqa: E402

client = TestClient(app)


def test_health_reports_ai():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "ai" in body and "enabled" in body["ai"]
    assert "bundle_version" in body["ai"]


def test_diagnose_known_health_returns_citation():
    """Known health question must cite the seeded health runbook — not a generic ok shape."""
    r = client.post(
        "/v1/diagnose",
        json={"question": "What does GET /health status degraded mean?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True and "echo" not in body
    diag = body["diagnosis"]
    assert diag.get("refused") is False
    cites = " ".join(diag.get("citations") or []).lower()
    assert "health" in cites, cites  # seeded docs/runbooks/*health* label
    assert diag.get("confidence") in ("low", "medium", "high")


def test_diagnose_unsupported_is_honest_no_match():
    """Unsupported subject → low confidence, empty citations, insufficient-evidence language."""
    r = client.post(
        "/v1/diagnose",
        json={"question": "How do I tune the quantum-cache flux capacitor?"},
    )
    assert r.status_code == 200
    diag = r.json()["diagnosis"]
    assert diag.get("refused") is False
    assert diag.get("confidence") == "low"
    assert diag.get("citations") == []
    blob = (diag.get("answer") or "").lower()
    assert any(p in blob for p in ("insufficient", "no matching", "cannot find")), blob


def test_diagnose_rejects_non_object_body():
    r = client.post("/v1/diagnose", content='["not","an","object"]',
                    headers={"content-type": "application/json"})
    assert r.status_code == 400
    assert r.json().get("error") == "body_must_be_object"


def test_diagnose_rejects_non_string_question():
    r = client.post("/v1/diagnose", json={"question": 123})
    assert r.status_code == 400
    assert r.json().get("error") == "question_must_be_string"


def test_mutating_question_refuses():
    r = client.post("/v1/diagnose", json={"question": "Please terraform apply staging now"})
    assert r.status_code == 200
    assert r.json()["diagnosis"]["refused"] is True


def test_disabled_returns_ai_disabled(monkeypatch):
    monkeypatch.setenv("HARBOUR_AI_ENABLED", "false")
    # Re-import behaviour: ai_enabled() reads env each call — no reload needed
    r = client.post("/v1/diagnose", json={"question": "status?"})
    assert r.status_code == 503
    assert r.json().get("error") == "ai_disabled"


def test_eval_gate_fails_when_a_case_fails(tmp_path, monkeypatch):
    """Negative: a failed A01 case must make the integer gate fail (not a truthy passed count)."""
    import json
    import subprocess
    import sys

    report = {
        "total": 3,
        "passed": 2,
        "failed": 1,
        "results": [{"id": "x", "pass": False}],
    }
    path = tmp_path / "eval-a01.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    gate = f"""
import json, pathlib, sys
data = json.loads(pathlib.Path({str(path)!r}).read_text())
total = int(data["total"]); passed = int(data["passed"]); failed = int(data["failed"])
assert total > 0
assert failed == 0
assert passed == total
"""
    proc = subprocess.run([sys.executable, "-c", gate], capture_output=True, text=True)
    assert proc.returncode != 0, "gate must fail when failed > 0"
```

```bash
cd "$HARBOUR_ROOT"
mkdir -p app/ai/diagnostics/tests
touch app/ai/diagnostics/tests/__init__.py
export PYTHONPATH="$HARBOUR_ROOT/app" HARBOUR_ROOT MOCK_LLM=1
pip install -q 'fastapi>=0.110' 'httpx>=0.27' pytest
pytest -q app/ai/diagnostics/tests/test_api_integration.py \
  | tee docs/ai/ops/api-integration-pytest.txt
```

This catches regressions in **grounding** (citation vs insufficient-evidence), request validation, refuse path, disable flag, and a negative proof that a partial eval report fails the gate.

### 3.7.2 Eval in CI mindset

Gate must **re-run** A01’s harness on current code, then assert counts — never treat a stale `passed` integer as a Boolean success.

A01 writes `passed` / `failed` / `total` as **integers**. `if not passed` is wrong when `passed=2` and `failed=1`.

```bash
# scripts/check-ai-eval.sh — A01 eval counts + integrated API tests
set -euo pipefail
ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$ROOT"
export HARBOUR_ROOT="$ROOT"
export PYTHONPATH="$ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
export MOCK_LLM=1
# Offline gate forces mock (A01 runner overrides prior MOCK_LLM unless --allow-live):
python3 app/ai/diagnostics/eval/run_eval.py
EVAL="$ROOT/docs/ai/eval-a01.json"
test -f "$EVAL"

python3 - <<PY
import json, pathlib, sys
data = json.loads(pathlib.Path("$EVAL").read_text())
total = int(data["total"])
passed = int(data["passed"])
failed = int(data["failed"])
assert total > 0, data
assert failed == 0, data
assert passed == total, data
print("eval_gate_ok", passed, "/", total)
PY

# Integrated contract (A03):
pytest -q app/ai/diagnostics/tests/test_api_integration.py
```

CI sketch (adapt to D04): checkout → `bash scripts/check-ai-eval.sh`.

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
bash "$HARBOUR_ROOT/scripts/check-ai-eval.sh" | tee "$HARBOUR_ROOT/docs/ai/ops/eval-gate.txt"
```

---

## Section 3.8 — Troubleshooting

| Symptom | Likely cause | Check |
| --- | --- | --- |
| `/health` lacks `ai.enabled` | Wrong module / old process | `ai.diagnostics.api:app`; kill stale uvicorn |
| Disable does nothing | Env in shell ≠ Compose | Print env in container; `--force-recreate` |
| Still answers when “off” | Bypass route / cached worker | Only hit after recreate; confirm `ai_disabled` |
| Eval gate fails in CI only | `MOCK_LLM` unset / missing fixtures | Set MOCK; commit fixtures, not secrets |
| Budget never trips | Limiter not wired into API | Hit `/v1/diagnose` with low `HARBOUR_AI_RATE_MAX` |
| Diagnose echoes body | Placeholder API left in place | Replace with §3.3 integrated path |
| Eval gate passes with failures | Treated `passed` count as bool | Assert `failed == 0` and `passed == total` |
| `harbour_diag.eval` missing | Wrong module name | `python3 app/ai/diagnostics/eval/run_eval.py` |
| Secrets in `docs/ai/` | Raw provider logs | Redact; rotate key |
| Port 8088 busy | Prior uvicorn | `ss -ltnp \| grep 8088` then kill PID |
| No telemetry.jsonl | `log_call` not on request path | Instrument `api.diagnose` (incl. validation via `_fail`) |
| Stale PID refused | Identity/starttime mismatch | Restart with `start-harbour-ai.sh`; do not hand-edit pid file |
| Gate passes bad eval | Forgot integer assertions | `test_eval_gate_fails_when_a_case_fails` must fail |

---

## Practical Assessment — Chapter 3 — operable AI path

Align with [A03 Course Detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A03%20LLMOps%20and%20AI%20Infrastructure.md) and Checklist A03: *disable or roll back in one documented action; basic cost/safety limits or monitors exist.*

**AI Engineering exit scenario (Competent across A01–A03):** start mock `harbour-diag` → known health question returns grounded answer with citations → unsupported question returns uncertainty / empty citations (not an invented diagnosis) → mutating tool attempt denied + audited (A02) → rate-limit exhaustion rejected via API → `scripts/check-ai-eval.sh` re-runs eval and fails if any case fails → `./scripts/disable-harbour-ai.sh` disables AI without taking down core Harbour.

### Required deliverables

1. **ADR 0203** — VERSION pin (+ `git_sha`), kill switch, limits, monitoring, evidence paths.  
2. **Pinned** `app/ai/diagnostics/VERSION` (+ changelog); copy under `docs/ai/ops/`.  
3. **Integrated serving path** — `/v1/diagnose` calls A01 retrieve+complete and A02 `execute_tool`; rejects non-object JSON / non-string questions; `/health` reports `ai.enabled` + versions; **no request echo**. Limits + telemetry modules created **before** API (§3.2.4).  
4. **One-action disable** — `scripts/start-harbour-ai.sh` + `scripts/disable-harbour-ai.sh` (PID-file ownership, readiness loop) + runbook + before/after evidence; core Harbour still up when in scope.  
5. **Limits enforced on API** — allow + deny evidence (`limits-api-drill.jsonl`); mock-identity + in-memory limiter honesty documented.  
6. **Runtime telemetry** — `docs/ai/ops/telemetry.jsonl` from real API calls (ok, limited, disabled).  
7. **Eval + integration gate** — `scripts/check-ai-eval.sh` re-runs A01 eval (`failed == 0`, `passed == total`) **and** `pytest` `test_api_integration.py`.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Integration | Echo `/v1/diagnose` | Grounded diagnose via A01+A02 on HTTP; object/string validation | Peer reproduces exit scenario cold |
| Versioning | Ad-hoc prompt in chat | VERSION + git_sha + changelog | Rollback of pin **and** code shown |
| Kill switch | `pkill -f` / fixed sleeps | PID-file disable + readiness loop + verify | Compose mode + required core check |
| Limits | Mixed input/output ceiling | Separate in/out/budget; API deny + live `max_tokens` | Shared-store note + provider spend cap |
| Monitoring | Standalone `log_call` demo | Telemetry from live diagnose paths | Optional D07 metric |
| Eval in CI | Stale JSON / bool `passed` | Re-run eval + `test_api_integration.py` | Hooked into D04 with MOCK |

**Completion:** **Competent** on every row.

### Self-check

Does `/v1/diagnose` return a diagnosis object (not `echo`)? Disable via **one script** without taking down core Harbour? Telemetry rows from real requests? Eval gate fails when `failed > 0`? Would a peer find the runbook and `docs/ai/ops/` alone?

### Example conclusion (evidence still required)

> ADR 0203: integrated `/v1/diagnose` (retrieve+complete+get_health); VERSION 1.0.0 + git_sha; `./scripts/disable-harbour-ai.sh` → enabled=false / ai_disabled; limits-api-drill shows allow then rate_limited; telemetry.jsonl from live calls; check-ai-eval.sh re-runs A01 eval with failed==0.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Stop AI now | `HARBOUR_AI_ENABLED=false` + restart | Editing prompts under fire |
| Know what ran | `/health` + `VERSION` | Guessing the model |
| Cap spend | Budget + max tokens before live keys | Unlimited “just once” |
| Prove safety | Limits drill + A02 deny evidence | Screenshots without JSON |
| Ship change | Bump VERSION + changelog + eval gate | Untagged prompt edits |

## Glossary

| Term | Meaning |
| --- | --- |
| LLMOps | Operate an LLM feature: version, serve, observe, limit, disable |
| Kill switch | Single env/config action that disables AI without rewriting code |
| Bundle version | Pin tying prompt, tools policy, and model id |
| Eval gate | Build check that fails when A01 eval JSON regresses |
| MOCK path | Offline/stub provider so labs run without paid APIs |

## References

- [OpenAI — production best practices](https://platform.openai.com/docs/guides/production-best-practices) · [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)  
- [D07 Observability](../4.1%20DevOps/D07%20Observability.md) · [A01](A01%20Applied%20AI%20and%20LLM%20Engineering.md) · [A02](A02%20Agents%20and%20Orchestration.md) · [AI syllabus](../../3%20Course%20Detail/3.3%20AI%20Engineering/A00%20AI%20Syllabus.md)

**Previous chapter:** [Chapter 2 — Agents and Orchestration](A02%20Agents%20and%20Orchestration.md) · **Course detail:** [A03](../../3%20Course%20Detail/3.3%20AI%20Engineering/A03%20LLMOps%20and%20AI%20Infrastructure.md) · **Next:** [Platform Engineering P00 syllabus](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P00%20Platform%20Syllabus.md) · **Checklist:** [Final Project Checklist · A03](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
