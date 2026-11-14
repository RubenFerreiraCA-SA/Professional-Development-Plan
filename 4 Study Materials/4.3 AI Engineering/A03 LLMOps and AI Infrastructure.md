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

```bash
cat > "$HARBOUR_ROOT/app/ai/diagnostics/VERSION" <<'EOF'
prompt_version=diag-prompt-2026-03
tools_policy_version=tools-allow-v2
model_id=mock-llm
bundle_version=1.0.0
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

---

## Section 3.3 — Packaging and serving

### 3.3.1 Health must report AI state

```python
# app/ai/diagnostics/api.py
from __future__ import annotations
import os
from fastapi import FastAPI
from ai.diagnostics.versioning import load_version

app = FastAPI(title="harbour-diag")

def ai_enabled() -> bool:
    return os.getenv("HARBOUR_AI_ENABLED", "true").lower() in ("1", "true", "yes", "on")

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
        },
    }

@app.post("/v1/diagnose")
def diagnose(payload: dict):
    if not ai_enabled():
        return {"ok": False, "error": "ai_disabled", "hint": "HARBOUR_AI_ENABLED=true to enable"}
    return {
        "ok": True,
        "mode": "mock" if os.getenv("MOCK_LLM", "1") == "1" else "live",
        "echo": payload,
    }
```

```bash
cd "$HARBOUR_ROOT"
# shellcheck disable=SC1091
test -f .venv/bin/activate && . .venv/bin/activate
pip install -q 'fastapi>=0.110' 'uvicorn[standard]>=0.27'

export MOCK_LLM=1 HARBOUR_AI_ENABLED=true
export PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
uvicorn ai.diagnostics.api:app --host 127.0.0.1 --port 8088 &
UV_PID=$!
sleep 1
curl -sS http://127.0.0.1:8088/health | tee "$HARBOUR_ROOT/docs/ai/ops/health-enabled.json"
kill "$UV_PID"
```

### 3.3.2 Optional Compose service

Prefer `deploy/ai/` over forking main app Compose:

```yaml
# deploy/ai/docker-compose.yml
services:
  harbour-diag:
    image: python:3.12-slim
    working_dir: /app
    # Mount Harbour app/ so `ai.diagnostics` imports match local PYTHONPATH=$HARBOUR_ROOT/app
    volumes: [../../app:/app:ro]
    environment:
      HARBOUR_AI_ENABLED: "${HARBOUR_AI_ENABLED:-true}"
      MOCK_LLM: "${MOCK_LLM:-1}"
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
docker compose -f deploy/ai/docker-compose.yml up -d
curl -sS http://127.0.0.1:8088/health | tee docs/ai/ops/health-compose.json
docker compose -f deploy/ai/docker-compose.yml down   # idle when done
```

**Reflect:** Core Harbour (D03 `/health`) stays valid when AI is off — diag is an add-on unless your ADR says otherwise.

---

## Section 3.4 — Kill switch / rollback in one action

### 3.4.1 One documented action

| Goal | One action |
| --- | --- |
| Disable | `HARBOUR_AI_ENABLED=false` + restart diag |
| Roll back pin | Restore known-good `VERSION` + restart |

A second engineer must succeed from the runbook alone.

### 3.4.2 Worked example — disable drill

```bash
cd "$HARBOUR_ROOT"
mkdir -p docs/ai/ops docs/runbooks
export PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}" MOCK_LLM=1

serve() { uvicorn ai.diagnostics.api:app --host 127.0.0.1 --port 8088 & UV_PID=$!; sleep 1; }
probe() {
  local tag="$1"
  curl -sS http://127.0.0.1:8088/health | tee "docs/ai/ops/health-${tag}.json"
  curl -sS -X POST http://127.0.0.1:8088/v1/diagnose \
    -H 'content-type: application/json' -d '{"q":"status?"}' \
    | tee "docs/ai/ops/diagnose-${tag}.json"
}

export HARBOUR_AI_ENABLED=true; serve; probe before-disable; kill "$UV_PID"
# ONE ACTION — kill switch + restart
export HARBOUR_AI_ENABLED=false; serve; probe after-disable; kill "$UV_PID"

python3 - <<'PY'
import json, pathlib, sys
r = pathlib.Path("docs/ai/ops")
b = json.loads((r/"health-before-disable.json").read_text())
a = json.loads((r/"health-after-disable.json").read_text())
d = json.loads((r/"diagnose-after-disable.json").read_text())
ok = b["ai"]["enabled"] is True and a["ai"]["enabled"] is False and d.get("error") == "ai_disabled"
print("disable_drill_ok=", ok); sys.exit(0 if ok else 1)
PY
```

Runbook stub — `docs/runbooks/ai-disable-rollback.md`:

```markdown
# Runbook — Disable or roll back harbour-diag (one action)

## Disable
1. HARBOUR_AI_ENABLED=false (Compose `.env` or process env).
2. Restart diag only: `docker compose -f deploy/ai/docker-compose.yml up -d --force-recreate`
3. Verify health `"enabled": false`; file docs/ai/ops/ evidence.

## Roll back VERSION
1. Restore VERSION from docs/ai/ops/VERSION.pinned.txt (or git).
2. Restart; confirm /health bundle_version matches.

Do not tear down core Harbour. Re-enable: HARBOUR_AI_ENABLED=true + restart.
```

### 3.4.3 Practice

Execute disable once **from the runbook only**; fix the runbook if tribal knowledge was required.

---

## Section 3.5 — Cost and safety limits

### 3.5.1 Basic limits

| Limit | Training default | When exceeded |
| --- | --- | --- |
| Max output tokens | e.g. 512 | Deny / truncate before call |
| Rate limit | e.g. 30 / 5 min / identity | 429 or tool denial |
| Budget | mock tokens/day | `budget_exceeded` |
| Redaction | strip `sk-`, Bearer, passwords | Never commit raw secrets |

### 3.5.2 Worked example — mockable limiter

```python
# app/ai/diagnostics/limits.py
from __future__ import annotations
import os, time
from collections import defaultdict, deque

MAX_OUT_TOKENS = int(os.getenv("HARBOUR_AI_MAX_TOKENS", "512"))
RATE_MAX = int(os.getenv("HARBOUR_AI_RATE_MAX", "30"))
RATE_WINDOW_S = int(os.getenv("HARBOUR_AI_RATE_WINDOW_S", "300"))
BUDGET_TOKENS = int(os.getenv("HARBOUR_AI_BUDGET_TOKENS", "20000"))

_hits: dict[str, deque[float]] = defaultdict(deque)
_spent = 0

def check_request(identity: str = "local", est_tokens: int = 200) -> dict:
    global _spent
    now = time.time()
    q = _hits[identity]
    while q and now - q[0] > RATE_WINDOW_S:
        q.popleft()
    if len(q) >= RATE_MAX:
        return {"allowed": False, "reason": "rate_limited"}
    if _spent + est_tokens > BUDGET_TOKENS:
        return {"allowed": False, "reason": "budget_exceeded"}
    if est_tokens > MAX_OUT_TOKENS:
        return {"allowed": False, "reason": "max_tokens"}
    q.append(now)
    _spent += est_tokens
    return {"allowed": True, "spent": _spent, "max_tokens": MAX_OUT_TOKENS}
```

```bash
cd "$HARBOUR_ROOT"
export HARBOUR_AI_BUDGET_TOKENS=500 HARBOUR_AI_RATE_MAX=3
export PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<'PY' | tee docs/ai/ops/limits-drill.json
import json
from ai.diagnostics.limits import check_request
results = [check_request("lab", est_tokens=200) for _ in range(4)]
results.append(check_request("lab", est_tokens=400))
print(json.dumps(results, indent=2))
assert any(r.get("reason") in ("rate_limited", "budget_exceeded") for r in results)
PY
```

Wire `check_request` **before** model/tool execution in `/v1/diagnose` for Competent→Advanced.

### 3.5.3 Redaction

```bash
sed -E 's/(sk-[A-Za-z0-9_-]+)/[REDACTED]/g; s/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g' \
  docs/ai/ops/raw-sample.log > docs/ai/ops/sample-redacted.log
```

---

## Section 3.6 — Monitoring hooks

Emit one JSON object per diagnose call. Minimum fields: `ts`, `latency_ms`, `tokens_in`/`tokens_out`, `bundle_version`/`model_id`, `ai_enabled`, `tool_denials`, `limit_reason`.

```python
# app/ai/diagnostics/telemetry.py
from __future__ import annotations
import json, time, sys
from ai.diagnostics.versioning import load_version

def log_call(*, latency_ms: float, tokens_in: int, tokens_out: int,
             tool_denials: list[str], limit_reason: str = "",
             ai_enabled: bool = True) -> None:
    ver = load_version()
    print(json.dumps({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "harbour_diag_call",
        "latency_ms": round(latency_ms, 2),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tool_denials": tool_denials,
        "limit_reason": limit_reason,
        "ai_enabled": ai_enabled,
        **ver,
    }), flush=True)
```

```bash
cd "$HARBOUR_ROOT"
export PYTHONPATH="$HARBOUR_ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<'PY' | tee docs/ai/ops/sample-structured-log.jsonl
from ai.diagnostics.telemetry import log_call
log_call(latency_ms=42.5, tokens_in=120, tokens_out=80,
         tool_denials=["restart_service"], limit_reason="")
PY
```

Optional: counter `harbour_diag_requests_total{result=…}` later (D07-style) — structured logs + evidence files are enough for Competent.

---

## Section 3.7 — Eval in CI mindset

Gate builds on A01’s `docs/ai/eval-a01.json`.

```bash
# scripts/check-ai-eval.sh
set -euo pipefail
ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
EVAL="$ROOT/docs/ai/eval-a01.json"
test -f "$EVAL" || { echo "Missing $EVAL — run A01 eval first"; exit 1; }

python3 - <<PY
import json, pathlib, sys
data = json.loads(pathlib.Path("$EVAL").read_text())
passed = data.get("passed")
if passed is None:
    summary = data.get("summary") or {}
    failed = int(summary.get("failed", summary.get("fail", 1)))
    passed = failed == 0
if not passed:
    print("EVAL REGRESSION:", data)
    sys.exit(1)
print("eval_gate_ok")
PY
```

CI sketch (adapt to D04): checkout → `MOCK_LLM=1 python -m harbour_diag.eval` → `bash scripts/check-ai-eval.sh`.

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
test -f "$HARBOUR_ROOT/docs/ai/eval-a01.json" || { echo "Re-run A01 eval first"; exit 1; }
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
| Budget never trips | Limiter not wired | Call `check_request` before model/tools |
| Secrets in `docs/ai/` | Raw provider logs | Redact; rotate key |
| Port 8088 busy | Prior uvicorn | `ss -ltnp \| grep 8088` then kill PID |

---

## Practical Assessment — Chapter 3 — operable AI path

Align with [A03 Course Detail](../../3%20Course%20Detail/3.3%20AI%20Engineering/A03%20LLMOps%20and%20AI%20Infrastructure.md) and Checklist A03: *disable or roll back in one documented action; basic cost/safety limits or monitors exist.*

### Required deliverables

1. **ADR 0203** — VERSION pin, kill switch, limits, monitoring, evidence paths.  
2. **Pinned** `app/ai/diagnostics/VERSION` (+ changelog); copy under `docs/ai/ops/`.  
3. **Serving path** — uvicorn and/or `deploy/ai` Compose; `/health` reports `ai.enabled` + versions.  
4. **One-action disable/rollback** — `docs/runbooks/ai-disable-rollback.md` + before/after evidence.  
5. **Limits** — mockable token/rate/budget deny (`limits-drill.json`).  
6. **Monitoring** — structured log sample (`sample-structured-log.jsonl`).  
7. **Eval gate** — `scripts/check-ai-eval.sh` (or equivalent) against `docs/ai/eval-a01.json`.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Versioning | Ad-hoc prompt in chat | VERSION + changelog committed | Pin rollback shown via `/health` |
| Kill switch | Comment-out code | `HARBOUR_AI_ENABLED=false` + restart; runbook + evidence | Peer can flip via Compose/env alone |
| Limits | “Be careful” | Mock rate/budget/max-tokens deny JSON | Wired into `/v1/diagnose` |
| Monitoring | Unstructured print | JSON: latency, tokens, denials | Optional metric / D07 note |
| Eval in CI | Eval once locally | Gate script fails on regression | Hooked into D04/CI with MOCK |

**Completion:** **Competent** on every row.

### Self-check

Disable without taking down core Harbour? `/health` shows `"enabled": false`? Secrets redacted? MOCK still works? Would a peer find the runbook and `docs/ai/ops/` alone?

### Example conclusion (evidence still required)

> ADR 0203: diag :8088; VERSION 1.0.0; kill switch + recreate → enabled=false / ai_disabled; limits-drill shows deny; structured log + eval gate under MOCK; Compose down when idle.

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
