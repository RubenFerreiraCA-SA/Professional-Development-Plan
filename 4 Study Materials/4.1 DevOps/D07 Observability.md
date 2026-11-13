# Chapter 7 — Observability (D07)

*DevOps Engineering textbook · Chapter 7 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D07 course detail](../../3%20Course%20Detail/3.1%20DevOps/D07%20Observability.md) (about 18–28 hours). |
| **Prerequisites** | [D03](D03%20Docker%20and%20Containerization.md), [D04](D04%20CICD%20and%20Build%20Automation.md), [D06](D06%20GitOps%20Automation%20and%20Operations.md); HTTP, databases, structured logging. |

## How to study this chapter

Observability is a **platform capability**: instrument once with open standards, collect through a pipeline you control, and answer **new** questions during incidents — not only the questions you guessed when you wrote the dashboard.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Where exporters, collectors or SLOs are easy to misread, this chapter **shows a working sequence first**, then asks you to reproduce it, then adds a harder challenge.

Examples extend **Harbour API** with **OpenTelemetry (OTel)** and a local Compose stack (`observability/`) using the Collector plus compatible open backends (Prometheus + Jaeger). [D08 — Datadog](../../3%20Course%20Detail/3.1%20DevOps/D08%20Datadog.md) reuses these principles with a commercial backend — keep this chapter **vendor-neutral**. This text teaches [D07 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D07%20Observability.md). The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) D07 bar is: *a responder who did not plant the fault can answer your documented incident questions using only telemetry and the runbook, then verify remediation.*

> **Safety and privacy boundary:** Use synthetic/demo data only. Do not log credentials, tokens, full request bodies or real PII. Destroy sandbox stacks when finished. Telemetry backends hold sensitive operational data — treat access like production logs.

> **Platform note:** You may run this stack with Docker Compose on a laptop (fastest for the collector outage drill) or beside the kind cluster from D06. You are building a **reference observability path**, not requiring Datadog yet.

### Learning outcomes

1. Differentiate monitoring and observability; map user, app and platform questions to signals.
2. Instrument metrics, structured logs and distributed traces with correct semantics and cardinality hygiene.
3. Explain propagation, sampling, aggregation limits and what missing telemetry does *not* prove.
4. Define SLIs/SLOs, error budgets and actionable alerts with runbooks.
5. Investigate failures with competing hypotheses and contradicting evidence.
6. Operate a secure OTel pipeline including a collector/backend failure test.
7. Publish a reusable observability contract for IDP onboarding.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"
test -f app/harbour_api/main.py || echo "Need Harbour API from D03"
docker compose version
python3 --version
mkdir -p observability/otel docs/observability
```

---

## Section 7.1 — Observability and the questions you must answer

### 7.1.1 Monitoring vs observability

| | Monitoring | Observability |
| --- | --- | --- |
| Typical question | “Is the known check green?” | “Why is *this* user journey slow *today*?” |
| Strength | Cheap, clear SLOs for known failure modes | Explore unknown failure modes from signals |
| Failure mode | Blind to novel faults | Noise, cost and cardinality if unconstrained |

Neither replaces resilient design (D03 probes, D06 rollbacks, capacity).

### 7.1.2 Three levels of observation

| Level | Example questions |
| --- | --- |
| User experience | Can clients complete `GET /ready` / critical API calls? Error rate? Latency? |
| Application / dependencies | Where does time go — handler vs DB? Which version/deploy correlates? |
| Platform | Restarts, OOM, Flux stuck, disk full, saturated CPU? |

### 7.1.3 Golden signals, RED and USE

| Framework | Focus |
| --- | --- |
| Four golden signals | Latency, traffic, errors, saturation |
| RED (request-driven) | Rate, Errors, Duration |
| USE (resources) | Utilisation, Saturation, Errors |

No single framework replaces system understanding — use them as checklists.

### 7.1.4 Worked example — six incident questions for Harbour

Write these into `docs/observability/incident-questions.md` (adapt wording, keep the mapping discipline):

| # | Question a responder must answer | Smallest useful signals |
| --- | --- | --- |
| 1 | Are users failing the critical path right now? | Request success ratio / SLO burn; `/ready` if it gates traffic |
| 2 | When did it start? | Metric change point; deploy timestamp (D04/D06) |
| 3 | Is it one route or everything? | Latency/error by `http.route` |
| 4 | Is time in Harbour or in a dependency? | Trace span breakdown (server vs db client) |
| 5 | Did we ship a bad digest? | `service.version` / image digest on resource attrs vs Git |
| 6 | Is telemetry itself lying or missing? | Collector health; gap in series; sampling notes |

**Blind spots to list explicitly:** no synthetics yet; sampling may hide rare traces; logs without trace IDs; metrics without route templates.

**Practice — reproduce:** Add two platform questions (Flux reconcile failed; pod restart loop) and map signals.

**Verify:** Another engineer can read the table and know what to open first.

---

## Section 7.2 — Metrics, logs, traces and causality

### 7.2.1 Metrics

| Type | Use |
| --- | --- |
| Counter | Requests, errors (monotonic) — usually **rate** in queries |
| Gauge | In-flight, pool size, replicas |
| Histogram / explicit buckets | Latency distributions → percentiles |

**Aggregation traps:** You cannot average p95 across instances and call it “the” p95. Prefer histograms merged correctly, or compute percentiles from the histogram/distribution backend.

**Label / attribute hygiene (cardinality):**

| Prefer | Avoid as metric labels |
| --- | --- |
| `service.name`, `deployment.environment.name`, route **template**, status class | User IDs, raw URLs with IDs, request IDs, emails |

High cardinality explodes cost and query latency.

### 7.2.2 Structured logs

Minimum fields: timestamp, severity, `service.name`, message, stable `error.code` when applicable, **trace_id** / **span_id** when a request is in flight.

**Never** log passwords, tokens, `Authorization` headers or full bodies with PII.

Differentiate **diagnostic** events (debug an incident) from **audit** events (who changed what — retention and access differ).

### 7.2.3 Distributed traces

| Concept | Meaning |
| --- | --- |
| Trace | One end-to-end request (many spans) |
| Span | Timed operation with parent/child links |
| Propagation | Trace context on HTTP (and later async) boundaries |
| Sampling | Not every trace is kept — **absence ≠ “never happened”** |

### 7.2.4 Interpretation exercise (concept before tooling)

| Symptom | Aggregate CPU alone | Traces + dependency spans |
| --- | --- | --- |
| Slow DB query | May look “idle” or busy depending on wait | Long **client** span to DB |
| Slow handler (`time.sleep`) | CPU may be low | Long **internal** span in the app |

**Reflect:** Why is “CPU is high after deploy” an incomplete diagnosis?

---

## Section 7.3 — Instrument Harbour (working path)

### 7.3.1 Target architecture (vendor-neutral)

```text
Harbour API ──OTLP──► OpenTelemetry Collector ──► Prometheus (metrics)
                     │
                     └──► Jaeger (traces)
App stdout logs (structured) ──► (optional) Collector filelog / keep in Docker logs for training
```

D08 may swap the right-hand side for Datadog; keep OTLP + resource attributes stable.

### 7.3.2 Worked example — dependencies

From `app/` (or repo root with your existing venv from D03):

```bash
cd "$HARBOUR_ROOT"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip
pip install \
  "fastapi" "uvicorn" "psycopg[binary]" \
  "opentelemetry-distro" \
  "opentelemetry-exporter-otlp" \
  "opentelemetry-instrumentation-fastapi" \
  "opentelemetry-instrumentation-asgi" \
  "opentelemetry-instrumentation-logging" \
  "opentelemetry-instrumentation-psycopg"
opentelemetry-bootstrap -a install || true
```

Pin versions in `app/requirements.txt` when you settle on a working set — do not leave “whatever pip resolved today” undocumented.

### 7.3.3 Worked example — resource attributes and OTLP export

Prefer explicit resource attributes (Unified Service Tagging / OTel semantic conventions):

| Attribute | Example |
| --- | --- |
| `service.name` | `harbour-api` |
| `service.version` | git SHA or image digest short form |
| `deployment.environment.name` | `local` / `staging` / `prod` |

`observability/otel/harbour.env.example` (copy to a **gitignored** local env file):

```bash
OTEL_SERVICE_NAME=harbour-api
OTEL_RESOURCE_ATTRIBUTES=service.version=dev,deployment.environment.name=local
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=none
# Fail soft: do not crash requests if the collector is down (batch exporter defaults)
OTEL_BSP_SCHEDULE_DELAY=5000
```

### 7.3.4 Worked example — run with auto-instrumentation

With Postgres from D03 Compose **or** DB-free (readiness `unconfigured`):

```bash
cd "$HARBOUR_ROOT"
set -a && source observability/otel/harbour.env && set +a
# If using D03 db:
# export DATABASE_HOST=127.0.0.1 DATABASE_PORT=5432 DATABASE_USER=harbour \
#   DATABASE_PASSWORD=harbour-training-only DATABASE_NAME=harbour

opentelemetry-instrument \
  uvicorn harbour_api.main:app --app-dir app --host 127.0.0.1 --port 8000
```

In another terminal (collector must be up — §7.4):

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/ready
curl -sS http://127.0.0.1:8000/v1/info
```

**Expected:** App answers; after collector is running, spans appear for HTTP server (and DB client spans when `DATABASE_HOST` is set and instrumentation is active).

### 7.3.5 Worked example — structured log ↔ trace correlation

Ensure logging instrumentation injects trace context (auto-instrumentation often does). Verify one log line during a request contains a trace id, **or** add a tiny helper that logs correlation fields — without logging bodies:

```python
# Training snippet — call from a request handler; do not log secrets or payloads
from opentelemetry import trace

span = trace.get_current_span()
ctx = span.get_span_context()
if ctx.is_valid:
    print(
        {"msg": "request_handled", "trace_id": format(ctx.trace_id, "032x"),
         "span_id": format(ctx.span_id, "016x"), "service": "harbour-api"}
    )
```

```bash
curl -sS http://127.0.0.1:8000/v1/info >/dev/null
# Match the printed trace_id to a Jaeger trace
```

**Practice — reproduce:** Capture one trace id from Jaeger and show the matching log line (or document if logs stay local-only for training).

### 7.3.5b Two-component request path (API + database)

Checklist and course detail require a path across **two components**. Harbour API + Postgres (D03 Compose) is the default:

1. Start Postgres via your D03 Compose file; set `DATABASE_*` as in D03.  
2. Confirm `/ready` returns `database` not `unconfigured`.  
3. Generate traffic that touches the DB (readiness already does an authenticated check in the improved D03 code — use that, or a small read endpoint).  
4. In Jaeger, open a trace and identify **server** span vs **db** client span (or equivalent psycopg spans).  

If you cannot run Postgres, add a tiny second HTTP service (`harbour-deps`) that sleeps or returns JSON and call it from Harbour with an instrumented HTTP client — still two components, still one trace. Document which option you used.

### 7.3.6 Worked example — slow handler vs slow dependency

1. Temporarily add a training-only route or use an existing path; inject `time.sleep(2)` in the handler once, hit it, find the span that is long **inside** the app.
2. Remove the sleep. With DB configured, run a deliberately slow query (e.g. `SELECT pg_sleep(2)`) behind a training-only endpoint **or** pause Postgres briefly and watch client spans / readiness — prefer a controlled `pg_sleep` so you do not confuse outage with slowness.
3. Record screenshots/notes: same “slow request” symptom; different span shapes.

**Verify:** You can explain the difference without looking at host CPU alone.

### 7.3.7 Challenge — cardinality mistake

Add a **bad** metric label (raw URL with an id) in a throwaway experiment; observe series explosion or document why you refused to merge it. Revert.

---

## Section 7.4 — Telemetry pipeline (Collector + backends)

### 7.4.1 Worked example — Compose reference stack

`observability/docker-compose.yml`:

```yaml
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.114.0
    command: ["--config=/etc/otelcol/config.yaml"]
    volumes:
      - ./otel/collector-config.yaml:/etc/otelcol/config.yaml:ro
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8889:8889"   # Prometheus exporter scrape (collector metrics bridge)
    depends_on:
      - jaeger
      - prometheus

  jaeger:
    image: jaegertracing/all-in-one:1.62
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
    ports:
      - "16686:16686" # UI
      - "4317"        # internal — app talks to collector, not Jaeger directly

  prometheus:
    image: prom/prometheus:v2.55.0
    volumes:
      - ./otel/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
```

> **Image tags:** Pin versions as above or newer known-good pins; if a tag moves, update deliberately and record it. Jaeger’s all-in-one accepts OTLP; the **app still exports to the Collector**, which forwards — that matches the platform shape (central pipeline).

`observability/otel/collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
  memory_limiter:
    check_interval: 2s
    limit_mib: 256

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889
  debug:
    verbosity: basic

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger, debug]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus, debug]
```

> **Collector/Jaeger wiring note:** Contrib collector + Jaeger OTLP ports have shifted across versions. If traces do not appear, fix the exporter endpoint against **your** pinned images (Jaeger OTLP gRPC often on `4317` inside the compose network) before changing application code. Keep the app → Collector contract stable (`4317`/`4318` on localhost). Only the Collector should publish `4317`/`4318` to the host so Harbour never bypasses the pipeline “just to make the demo work.”

`observability/otel/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: otel-collector
    static_configs:
      - targets: ["otel-collector:8889"]
```

Start:

```bash
cd "$HARBOUR_ROOT/observability"
docker compose up -d
docker compose ps
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:16686
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9090
```

### 7.4.2 Worked example — see a trace and a metric

```bash
# App exporting to collector (§7.3), then:
for i in 1 2 3 4 5; do curl -sS http://127.0.0.1:8000/v1/info >/dev/null; done
```

Open Jaeger UI → service `harbour-api` → Find Traces. Open Prometheus → query for HTTP metrics your instrumentation exposes (names depend on OTel semconv version — search `http_server` / `http.server` style metrics; document the **exact** names you see).

**Expected:** At least one trace with a server span; Prometheus shows a non-empty series related to Harbour traffic **or** you document the metric name gap and export a custom counter — honesty over fake screenshots.

### 7.4.3 Worked example — collector outage (application must not die)

```bash
cd "$HARBOUR_ROOT/observability"
# Baseline: app healthy
curl -sf http://127.0.0.1:8000/ready

docker compose stop otel-collector
# Generate traffic while collector is down
for i in $(seq 1 20); do curl -sf http://127.0.0.1:8000/health || echo APP_DOWN; done

docker compose start otel-collector
sleep 5
curl -sf http://127.0.0.1:8000/ready
# Note: some in-flight export buffers may drop — that is OK if requests succeeded
```

**Expected:** Application HTTP stays up (`APP_DOWN` should not appear). Telemetry may have **gaps**. Record: request success vs dropped spans/metrics. If the app hangs or crashes on export, fix exporter settings (timeouts, batch processor) — telemetry must **degrade**, not take the user path down.

### 7.4.4 Security and cost controls (minimum)

| Control | Training expectation |
| --- | --- |
| TLS to backends | Local insecure OK; document prod must encrypt |
| Credentials | None in git; Compose env files gitignored |
| PII | Redact; no bodies in spans/logs |
| Cardinality / retention | Short local retention; no unbounded labels |
| Provider boundary | OTLP + conventions stay; D08 may add vendor exporter |

**ADR prompt** (`docs/decisions/0007-observability-pipeline.md`): what stays provider-neutral; sampling defaults; who owns collector vs app SDK versions.

### 7.4.5 Practice — reproduce

Stop Jaeger only (collector up, exporter failing). Observe collector logs/retries and app health. Restore.

**Verify:** Diagram in the ADR matches what you ran; outage notes include “app OK / telemetry gap.”

---

## Section 7.5 — SLIs, SLOs and alerting

### 7.5.1 Choose journeys

| Journey | Type |
| --- | --- |
| Clients receive non-5xx on critical read (`/v1/info` or your real critical route) | Application |
| `/ready` success when DB is configured (dependency gate) | Application |
| Flux Kustomization Ready / successful reconcile for Harbour staging (from D06) | Platform |

### 7.5.2 Worked example — define SLI/SLO tables

`docs/observability/slo-harbour.md`:

```markdown
## SLI A — critical read availability
- **SLI:** count(successful critical reads) / count(all critical reads)
  Successful = HTTP status < 500 (define precisely; exclude 401 if auth is expected).
- **SLO:** 99% over 28 days (training may use 24h window with synthetic traffic — say so).
- **Data source:** OTel HTTP metrics by route template, or access logs with care.
- **Error budget:** 1% of requests in the window may fail the SLI.
- **Alert:** burn or sustained error ratio above threshold for N minutes → page owner.
- **Runbook:** link to docs/observability/runbook-latency-errors.md

## SLI B — readiness when DB required
- **SLI:** fraction of `/ready` probes returning 200 when `DATABASE_HOST` is set.
- **SLO:** 99.5% over 24h in staging (training).
- …

## SLI C — platform deploy reconcile
- **SLI:** harbour-api-staging Flux Kustomization Ready=True at sample times / successful reconciles.
- **SLO:** …
```

**SLA vs SLO:** SLO is an internal target; SLA is a contractual promise — do not confuse them.

### 7.5.3 Worked example — error budget arithmetic

For a 99% SLO over 1000 synthetic requests, budget = 10 failed SLI events.  

| Pattern | Failed in window | Action |
| --- | --- | --- |
| 8 failures in 1 minute, then healthy | Likely within budget if rare | Ticket / watch — often **do not page** |
| Failures continuing past budget burn | User impact sustained | **Page** with runbook |

Burn-rate alerts (SRE workbook) are Advanced — document qualitatively if you do not automate them yet.

### 7.5.4 Worked example — alert + runbook (user-impacting)

`docs/observability/runbook-latency-errors.md`:

```markdown
# Runbook — Harbour critical read errors / latency

## When this fires
Error ratio or p95 latency on critical route exceeds threshold for N minutes.

## Urgency / owner
- Urgency: page if burn/sustained user impact; ticket if brief spike under budget
- Owner: platform-oncall (training: you)

## Verify
1. Prometheus / metrics: error ratio by route
2. Jaeger: slow or error spans — app vs DB
3. Recent deploy digest (D04/D06) vs `service.version`
4. Collector health — rule out “missing telemetry” false alarm

## Mitigate
- Revert bad desired-state / digest (D06) if evidence implicates deploy
- Restore dependency if DB spans show failure
- Do not restart pods as the first superstition

## Escalate
…
```

Wire a **simple** alert in Prometheus Alertmanager **or** document a manual threshold check you performed on synthetic bad traffic — do not claim a paging integration you did not build.

### 7.5.5 Practice — reproduce

Generate a short spike of 500s (temporary fault injection) vs sustained faults; write which one you would page and why, with budget math.

**Verify:** SLIs have precise numerators/denominators; alerts point at user impact + first diagnostic step.

---

## Section 7.6 — Evidence-led incident investigation

### 7.6.1 Worked example — plant a degradation scenario

Use an isolated environment. Pick **one** planted cause (do not tell your future self in the same note you will use as “responder evidence” — or pair with a friend):

| Plant | How (training) |
| --- | --- |
| Slow handler | Temporary `sleep` in a route |
| Slow DB | `pg_sleep` / missing index simulation |
| Bad deploy correlation | Change `service.version` / ship a bad digest then revert |
| CPU contention | In-pod burn (D06-style) while traffic runs |
| Telemetry gap | Stop collector and notice blind spot |

### 7.6.2 Investigation protocol (follow in order)

1. **Symptom + start time** — user-visible; when it began.  
2. **Competing hypotheses** — write ≥3 before deep diving.  
3. **Evidence** — metrics, traces, logs, deploy history, dependency signals.  
4. **Contradict** — actively seek evidence that kills a favourite theory.  
5. **Reversible action** — fix/revert; confirm SLI moves.  
6. **Write-up** — timeline, factors, preventive change, **remaining uncertainty**.

`docs/observability/incident-YYYYMMDD.md` template:

```markdown
## Symptom
## Timeline
## Hypotheses
| Hypothesis | Evidence for | Evidence against | Status |
## Action taken
## SLI after
## Follow-ups
## What telemetry could not tell us
```

### 7.6.3 Practice — reproduce

Run the protocol on a fault you did **not** plant (checklist standard), or cold-start after a night away from your own plant notes.

**Challenge:** Show a case where deploy time correlated but was **not** causal (telemetry gap or dependency blip).

**Verify:** Write-up includes contradicting evidence and does not equate correlation with causation.

---

## Section 7.7 — Observability as a platform product

### 7.7.1 Worked example — observability contract

`docs/observability/CONTRACT.md`:

```markdown
# Harbour / IDP observability contract (D07)

## Required resource attributes
- service.name, service.version, deployment.environment.name
- Ownership annotation / team label documented in service catalog stub

## Instrumentation baseline
- OTLP export to platform Collector endpoint
- HTTP server metrics + traces; DB client spans when a DB is used
- Structured logs with severity + trace correlation; no PII/secrets

## SLOs
- Each service publishes ≥1 user journey SLI/SLO owner + runbook link

## Sampling / retention / budget
- Default trace sampling: ___ (state training default)
- Metric label allowlist: ___
- Log retention: ___

## Validation test
- Smoke: traffic produces ≥1 trace and a metric series within 5 minutes
- Failure: app remains healthy if Collector is down (document gap)

## Developer starter
- Link to observability/otel/harbour.env.example and compose stack
- “How to find” dashboards/traces/runbooks: …
```

### 7.7.2 Onboarding with vs without the contract

| | Without contract | With contract |
| --- | --- | --- |
| New service | Invents metric names, misses trace propagation | Copy starter + pass validation test |
| Incident | “Which Grafana?” | Known Jaeger/Prom URLs + runbook |

**Practice — reproduce:** Time-box inventing instrumentation for a fictional second service with only the contract as input.

**Verify:** Contract lists privacy and cardinality rules, not only “install an agent.”

---

## Section 7.8 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| No traces in Jaeger | App→Collector URL wrong; pipeline exporter; service name | Collector logs; `OTEL_EXPORTER_OTLP_ENDPOINT` |
| App slow/crash when backend down | Sync export / hard failure on export | Batch exporter; outage drill results |
| Metrics empty | Wrong scrape; name change in semconv | Prom targets; list metric names |
| Huge Prometheus load | High-cardinality labels | Label allowlist; drop processor |
| Trace missing but user saw error | Sampling or drop under backpressure | Document uncertainty; check logs |
| Alert flapping | Threshold without burn/window | Sustained condition; error budget |

---

## Practical Assessment — Chapter 7 — design and diagnose

Align with [D07 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D07%20Observability.md) and Final Project Checklist D07.

### Required deliverables

1. Telemetry architecture diagram + instrumented path (API + dependency or second component) with correlated logs/traces and useful metrics.  
2. Reproducible local/sandbox Collector pipeline + **collector/backend failure test** (app healthy; telemetry gap recorded).  
3. Two application SLIs/SLOs + one platform SLI with error-budget examples.  
4. Alert definition + runbook for a user-impacting condition (urgency and owner justified).  
5. Investigation write-up of a degraded service: competing hypotheses, contradicting evidence, verified remediation.  
6. Reusable observability contract with privacy and cardinality controls.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Signals | Dashboards exist | Metrics+logs+traces correlated on a request | Profiles/synthetics or explicit sampling policy |
| Pipeline | Agent “works” | Collector path + outage degrade behaviour | Backpressure/retention cost controls |
| SLOs | Vague uptime | Precise SLIs, budgets, user-impact alerts | Burn-rate alerting |
| Diagnosis | Restarted pods | Hypothesis-driven with contradicting evidence | Separates causal deploy from coincidence |
| Platform | One-off setup | Written contract + validation smoke test | Second service onboarded via contract only |

**Completion standard:** **Competent** on every row. Another engineer can reproduce the failure, find the cause from telemetry + runbook, and say what would be unreliable or missing.

### Self-check

- Can a stranger answer your six incident questions from signals alone?  
- Does stopping the Collector leave Harbour serving traffic?  
- Are SLI formulas precise enough to disagree about?  
- Did you keep PII and secrets out of telemetry?  
- Is D08 clearly optional for Final Project vendor choice, while D07 remains required?

### Example assessment conclusion (evidence still required)

> Harbour exports OTLP to a Compose Collector → Prometheus/Jaeger. Traces show HTTP vs DB time. Collector stop: `/ready` stayed OK; spans gapped. SLIs A/B/C documented with budget math. Planted slow-DB incident: hypotheses listed; handler-sleep theory contradicted by span shape; fix verified. CONTRACT.md used as onboarding checklist. No Datadog required for D07.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Know if users are hurt | SLI / golden signals | Only node CPU |
| Know where time went | Trace span waterfall | Averaging unrelated p95s |
| Add a dimension | Route template / status class | User id on metrics |
| Survive backend outage | Async batch export + test | Sync export on request path |
| Page a human | Sustained user-impact + runbook | Alert on every blip |
| Onboard a team | CONTRACT.md + smoke test | “Install vendor agent somehow” |

## Glossary

| Term | Definition |
| --- | --- |
| SLI | Quantitative measure of user-facing reliability |
| SLO | Target value for an SLI over a window |
| Error budget | Allowed unreliability under the SLO |
| Cardinality | Number of unique label combinations |
| Propagation | Passing trace context across process boundaries |
| Sampling | Keeping a subset of traces |
| OTLP | OpenTelemetry Protocol (app → collector/backend) |

## References

- [OpenTelemetry docs](https://opentelemetry.io/docs/)
- [OpenTelemetry concepts](https://opentelemetry.io/docs/concepts/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Semantic conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Google SRE — Monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Google SRE — Service level objectives](https://sre.google/sre-book/service-level-objectives/)
- [SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)

**Previous chapter:** [Chapter 6 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md) · **Course detail:** [D07 — Observability](../../3%20Course%20Detail/3.1%20DevOps/D07%20Observability.md) · **Next chapter:** Chapter 8 — Datadog (not yet authored) · **Checklist:** [Final Project Checklist · D07](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
