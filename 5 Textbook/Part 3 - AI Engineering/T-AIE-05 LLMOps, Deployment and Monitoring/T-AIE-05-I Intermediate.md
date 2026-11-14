# T-AIE-05-I — Intermediate Practice

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-i"></a>
#### T-AIE-05-I — Intermediate Practice

**Serving the feature.** Package the assistant as a small HTTP service, separate from the core application where possible, so it can be scaled, limited and disabled independently:

```python
from fastapi import FastAPI, HTTPException, Header
app = FastAPI()

@app.post("/v1/diagnose")
def diagnose(req: DiagnoseRequest, x_identity: str = Header("local")):
    if not settings.enabled:
        raise HTTPException(503, "assistant disabled")
    limiter.check(x_identity, req.question)          # rate, size, token budget
    chunks = retrieve(req.question)
    answer = complete(req.question, chunks)          # model call
    validate_answer(answer)
    telemetry.log_call(identity=x_identity, tokens_in=..., tokens_out=..., latency_ms=...)
    return answer
```

The request path: enabled? → validate and apply limits → retrieve authorised context → optionally gather read-only tool observations → call the model → validate the response → record sanitised telemetry → return a structured result (never echo the raw request).

**Limits that protect cost and safety**

| Limit | Example default | When exceeded |
| --- | --- | --- |
| Maximum input tokens | 2,000 | 429 `input_tokens` |
| Maximum output tokens | 512 | Passed to the provider as a ceiling |
| Aggregate budget | Tokens per identity per window | 429 `budget_exceeded` |
| Rate limit | e.g. 30 requests per 5 minutes per identity | 429 `rate_limited` |
| Question length | 2,000 characters | 400 `question_too_long` |
| Redaction | Strip key-like strings, bearer tokens, passwords | Never log raw secrets |

A client-supplied identity header is only a demonstration; a real deployment derives identity from authentication.

**Kill switch and rollback as one action.** Encapsulate disable, rollback and verification in a script so on-call does not improvise:

```bash
#!/usr/bin/env bash
set -euo pipefail
PIDFILE=/var/run/assistant.pid
pid=$(cat "$PIDFILE")
grep -q 'assistant' "/proc/$pid/cmdline" || { echo "pid does not match"; exit 1; }
kill "$pid"
for i in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
curl -fsS localhost:8000/health >/dev/null && echo "core service still healthy"
```

Do not `pkill -f` a command string; it can kill unrelated processes. Prefer your service manager or orchestrator in real deployments.

**Monitoring hooks.** Emit, per request: timestamp, latency, input and output tokens, bundle version and model id, enabled state, number of tool denials, limit decisions and an outcome category. Evidence must come from real requests through the real path, not a standalone helper call.

**Test the integrated path.** An offline test using the framework's test client protects regression in grounding (citation or insufficient evidence), validation, refusal, the disable flag and the evaluation gate:

```python
def test_disabled_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "enabled", False)
    assert client.post("/v1/diagnose", json={"question": "x"}).status_code == 503
```

**Exercise.** Add the limiter, hit it past its threshold to see 429, and show the telemetry line for each outcome.
