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

# After §7.3.3 creates harbour.env.example, copy it once:
#   cp observability/otel/harbour.env.example observability/otel/harbour.env
```

Ensure `.gitignore` includes `observability/otel/harbour.env`. The example file is committed; the local `harbour.env` copy is not.

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
[Compose network harbour-obs]
  Harbour API ──OTLP──► OpenTelemetry Collector ──► Prometheus (metrics)
       │                │
       └── Postgres     └──► Jaeger (traces)
App stdout (structured JSON with trace_id) ──► docker compose logs
```

D03’s Compose deliberately **does not publish** Postgres to the host. This chapter’s working topology therefore runs **Harbour and Postgres on the same Compose network** (`DATABASE_HOST=db`). Do not assume `127.0.0.1:5432` works against an unpublished D03 database.

D08 may swap the right-hand backends for Datadog; keep OTLP + resource attributes stable.

### 7.3.2 Worked example — pinned dependencies

Create `observability/otel/requirements-otel.txt` with this **pinned** set (install from the file — do not freestyle `pip install` unpinned packages):

```text
# observability/otel/requirements-otel.txt
# Pinned for D07 training reproducibility (API 1.28 / instrumentation 0.49b2 line).
fastapi==0.115.5
uvicorn==0.32.1
psycopg[binary]==3.2.3
opentelemetry-api==1.28.2
opentelemetry-sdk==1.28.2
opentelemetry-semantic-conventions==0.49b2
opentelemetry-distro==0.49b2
opentelemetry-exporter-otlp==1.28.2
opentelemetry-exporter-otlp-proto-grpc==1.28.2
opentelemetry-exporter-otlp-proto-http==1.28.2
opentelemetry-instrumentation==0.49b2
opentelemetry-instrumentation-asgi==0.49b2
opentelemetry-instrumentation-fastapi==0.49b2
opentelemetry-instrumentation-logging==0.49b2
opentelemetry-instrumentation-psycopg==0.49b2
opentelemetry-instrumentation-dbapi==0.49b2
opentelemetry-util-http==0.49b2
```

Install into the project venv (failures must be visible — no `|| true`):

```bash
cd "$HARBOUR_ROOT"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip
pip install -r observability/otel/requirements-otel.txt
# Failures must be visible (no || true, no piping away exit codes):
python -c "import opentelemetry, fastapi, psycopg; print('otel-imports-ok')"
opentelemetry-bootstrap -a requirements > /tmp/otel-bootstrap-reqs.txt
wc -l /tmp/otel-bootstrap-reqs.txt
# Instrumentation packages are already pinned above — bootstrap output is a cross-check,
# not a second install source. If bootstrap exits non-zero, stop and fix the environment.
```

If `pip install -r`, the import check, or `opentelemetry-bootstrap` fails, stop and fix versions — do not continue with a partial environment. Commit `requirements-otel.txt` so others reproduce the same set.

### 7.3.3 Worked example — env file from example

Prefer explicit resource attributes (Unified Service Tagging / OTel semantic conventions):

| Attribute | Example |
| --- | --- |
| `service.name` | `harbour-api` |
| `service.version` | git SHA or image digest short form |
| `deployment.environment.name` | `local` / `staging` / `prod` |

Write `observability/otel/harbour.env.example`:

```bash
OTEL_SERVICE_NAME=harbour-api
OTEL_RESOURCE_ATTRIBUTES=service.version=dev,deployment.environment.name=local
# Inside Compose, the API uses the collector hostname (see compose). For rare host-run
# debugging only, you would point at http://127.0.0.1:4317 — not the default path here.
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=none
# Training: short export intervals so metrics appear without multi-minute waits.
# (Defaults can be 60s for periodic metric export — too slow for the §7.4.2 drill.)
OTEL_BSP_SCHEDULE_DELAY=1000
OTEL_METRIC_EXPORT_INTERVAL=5000
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_USER=harbour
DATABASE_PASSWORD=harbour-training-only
DATABASE_NAME=harbour
```

**Create the local file explicitly:**

```bash
cp observability/otel/harbour.env.example observability/otel/harbour.env
# Adjust service.version if you like; keep harbour.env out of git
```

### 7.3.4 Worked example — instrument `/v1/info` (log + counter + optional fail)

Edit `app/harbour_api/main.py`. Add imports and meter/counter near the top (after existing imports), then replace the `/v1/info` handler (and add a training fail route) as follows.

**Imports / meter** (add once):

```python
import json
import logging

from opentelemetry import metrics, trace

logger = logging.getLogger("harbour_api")
logging.basicConfig(level=logging.INFO)

meter = metrics.get_meter("harbour-api")
info_requests = meter.create_counter(
    "harbour.info.requests",
    unit="1",
    description="Count of /v1/info requests by outcome",
)
```

**Replace / extend handlers** (keep your existing `/health` and `/ready`):

```python
@app.get("/v1/info")
def info():
    span = trace.get_current_span()
    ctx = span.get_span_context()
    trace_id = format(ctx.trace_id, "032x") if ctx.is_valid else ""
    span_id = format(ctx.span_id, "016x") if ctx.is_valid else ""
    # Structured log line — same trace_id you will search in Jaeger
    logger.info(
        json.dumps(
            {
                "msg": "info_request",
                "service": "harbour-api",
                "http.route": "/v1/info",
                "trace_id": trace_id,
                "span_id": span_id,
            }
        )
    )
    info_requests.add(1, {"http.route": "/v1/info", "outcome": "success"})
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "trace_id": trace_id,
    }


@app.get("/v1/fail")
def fail_training():
    """Training-only: increments error counter and returns 500 for alert drills."""
    info_requests.add(1, {"http.route": "/v1/fail", "outcome": "error"})
    # Re-use the same counter name with outcome=error so alert ratios have a denominator
    return Response(content='{"status":"fail"}', media_type="application/json", status_code=500)
```

Ensure `Response` is imported from FastAPI (D03 already uses it for `/ready`). Remove `/v1/fail` before any shared environment beyond training.

**Prometheus name:** the OTLP → Prometheus exporter exposes this as **`harbour_info_requests_total`** (dots → underscores, `_total` for counters). That name is the success criterion in §7.4.2.

### 7.3.5 Worked example — two-component Compose topology (API + DB + collector)

D03 does **not** publish Postgres to the host. Use this **working** topology: API and DB share the Compose network; only API `:8000`, Collector OTLP, Jaeger UI and Prometheus are published.

Extend `observability/docker-compose.yml` (full file in §7.4.1 includes `db` + `api`). Build an image that includes the pinned OTel deps (repo root as context so the requirements file is reachable):

```bash
cd "$HARBOUR_ROOT"
# Base app image from D03 first:
docker build -t harbour-api:local \
  --build-arg HARBOUR_COMMIT="$(git rev-parse HEAD)" \
  -f app/Dockerfile app

# Layer pinned OTel deps (context = repo root):
docker build -t harbour-api:otel -f- . <<'DOCKERFILE'
FROM harbour-api:local
USER root
COPY observability/otel/requirements-otel.txt /tmp/requirements-otel.txt
RUN pip install --no-cache-dir -r /tmp/requirements-otel.txt
# Keep the same non-root user your D03 image defines (adjust if named differently):
USER harbour
DOCKERFILE

docker run --rm harbour-api:otel python -c "import opentelemetry; print('otel-in-image-ok')"
```

The D03 image `ENTRYPOINT` is bare `uvicorn`. A Compose `command:` alone does **not** wrap it — Compose replaces `CMD`, not `ENTRYPOINT`. Section 7.4.1 **must** set `entrypoint: ["opentelemetry-instrument"]` plus an explicit `command:` list for uvicorn (mandatory).

**Optional escape hatch (temporary only):** a disposable Compose override that adds `"5432:5432"` on `db` so a **host-run** uvicorn can use `DATABASE_HOST=127.0.0.1` — then remove the publish. Prefer the in-compose API so you do not fight D03’s networking design.

### 7.3.6 Worked example — prove log ↔ trace correlation end-to-end

With the stack up (§7.4.1):

```bash
# Hit info; response body includes trace_id
RESP="$(curl -sS http://127.0.0.1:8000/v1/info)"
echo "$RESP"
TID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["trace_id"])' <<<"$RESP")"
test -n "$TID" && echo "trace_id=${TID}"

# Same ID in API logs:
docker compose -f "$HARBOUR_ROOT/observability/docker-compose.yml" logs api --tail=50 | grep "$TID"

# Same ID in Jaeger UI: http://127.0.0.1:16686 → Search → paste trace id
# or:
xdg-open "http://127.0.0.1:16686/trace/${TID}" 2>/dev/null || echo "Open Jaeger and search ${TID}"
```

**Expected:** One JSON log line with `"trace_id":"<TID>"`, Jaeger shows that trace for `harbour-api`, and the HTTP response `trace_id` matches both.

### 7.3.7 Worked example — DB spans on the same network

```bash
curl -sS http://127.0.0.1:8000/ready
# Jaeger: find a /ready (or info) trace; confirm a DB/client span when readiness queries Postgres
```

**Slow handler vs slow dependency:** add a temporary `time.sleep(2)` in `/v1/info` once; compare span shape to a training route that runs `SELECT pg_sleep(2)` via psycopg. Remove both after the exercise.

### 7.3.8 Challenge — cardinality mistake

Add a **bad** metric label (raw URL with an id) in a throwaway experiment; observe series explosion or document why you refused to merge it. Revert.

**Verify:** Pinned `pip install -r` succeeded; API reaches DB as `db` (not host `127.0.0.1`); one request produced matching response / log / Jaeger `trace_id`; `harbour_info_requests_total` will be queried in §7.4.2.

---

## Section 7.4 — Telemetry pipeline (Collector + backends)

### 7.4.1 Worked example — Compose reference stack (API + DB + pipeline)

`observability/docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: harbour
      POSTGRES_PASSWORD: harbour-training-only
      POSTGRES_DB: harbour
    # No host ports — same design as D03; only reachable as hostname "db"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U harbour -d harbour"]
      interval: 5s
      timeout: 5s
      retries: 10

  api:
    image: harbour-api:otel
    env_file:
      - ./otel/harbour.env
    environment:
      # Compose DNS names win over any host-oriented mistakes:
      DATABASE_HOST: db
      OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
      OTEL_METRIC_EXPORT_INTERVAL: "5000"
      OTEL_BSP_SCHEDULE_DELAY: "1000"
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      otel-collector:
        condition: service_started
    # Mandatory: D03 ENTRYPOINT is uvicorn — command: alone does NOT wrap it.
    # entrypoint replaces ENTRYPOINT; command supplies the instrumented argv.
    entrypoint: ["opentelemetry-instrument"]
    command:
      - uvicorn
      - harbour_api.main:app
      - --host
      - "0.0.0.0"
      - --port
      - "8000"

  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.114.0
    command: ["--config=/etc/otelcol/config.yaml"]
    volumes:
      - ./otel/collector-config.yaml:/etc/otelcol/config.yaml:ro
    ports:
      - "4317:4317"
      - "4318:4318"
      - "8889:8889"
    depends_on:
      - jaeger
      - prometheus

  jaeger:
    image: jaegertracing/all-in-one:1.62
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
    ports:
      - "16686:16686"

  prometheus:
    image: prom/prometheus:v2.55.0
    volumes:
      - ./otel/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./otel/alert-rules.yml:/etc/prometheus/alert-rules.yml:ro
    ports:
      - "9090:9090"
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --web.enable-lifecycle
```

Build `harbour-api:otel` before `compose up` (§7.3.5). Create env **and** a valid alert-rules file **before** the first `docker compose up` (Prometheus mounts this path immediately — §7.5.4 replaces the placeholder with the real rule):

```bash
cp observability/otel/harbour.env.example observability/otel/harbour.env

# Valid empty rule file so Compose/Prometheus can start in chapter order:
cat > observability/otel/alert-rules.yml <<'EOF'
groups: []
EOF
```

Verify instrumentation is actually wrapping uvicorn (not the D03 entrypoint alone):

```bash
docker compose -f observability/docker-compose.yml config | grep -A6 'entrypoint:'
# Expect: entrypoint pointing at opentelemetry-instrument, command listing uvicorn …
```

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

> **Collector/Jaeger wiring note:** If traces do not appear, fix the exporter endpoint against **your** pinned images before changing application code. App → Collector only (`otel-collector:4317` on the Compose network).

`observability/otel/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/alert-rules.yml

scrape_configs:
  - job_name: otel-collector
    static_configs:
      - targets: ["otel-collector:8889"]
```

Start:

```bash
cd "$HARBOUR_ROOT/observability"
test -f otel/alert-rules.yml   # must exist (placeholder groups: [] is fine)
docker compose up -d
docker compose ps
# Prove instrumentation wrapper is active (not bare D03 ENTRYPOINT):
docker compose exec api sh -c 'tr "\0" " " < /proc/1/cmdline; echo'
# Expect cmdline to start with opentelemetry-instrument … uvicorn …
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:16686
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9090
```

### 7.4.2 Worked example — guaranteed metric + a trace

**Success criterion (required):** Prometheus returns a non-empty vector for the **explicit** counter from §7.3.4. Do not rely on a single fixed `sleep` — poll until the series appears (or time out and debug).

Confirm the API process is instrumented before generating traffic:

```bash
cd "$HARBOUR_ROOT/observability"
docker compose exec api sh -c 'tr "\0" " " < /proc/1/cmdline; echo'
# Expect: opentelemetry-instrument … uvicorn … — not bare uvicorn alone
# (Python slim images often lack `ps`; /proc/1/cmdline is portable.)
docker compose logs api --tail=30 | grep -iE 'instrument|otel|exporter' || true
```

```bash
QUERY='harbour_info_requests_total{http_route="/v1/info",outcome="success"}'

for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -sS http://127.0.0.1:8000/v1/info >/dev/null
done

# Poll up to ~90s: metric export interval (5s) + scrape (15s) + slack
deadline=$((SECONDS + 90))
while (( SECONDS < deadline )); do
  body="$(curl -sG 'http://127.0.0.1:9090/api/v1/query' --data-urlencode "query=${QUERY}")"
  if echo "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("data",{}).get("result",[]); sys.exit(0 if r else 1)'; then
    echo "$body" | python3 -m json.tool | head -n 40
    echo "metric-ok"
    break
  fi
  echo "waiting for series…"
  sleep 5
done
echo "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("data",{}).get("result",[]); assert r, "TIMEOUT: harbour_info_requests_total not scraped — check entrypoint, OTEL_METRIC_EXPORT_INTERVAL, collector metrics pipeline"'
```

In the Prometheus UI (Graph): paste

```promql
harbour_info_requests_total{http_route="/v1/info",outcome="success"}
```

**Expected:** poll loop prints `metric-ok` with a numeric `value`. If you hit the timeout assertion: (1) `entrypoint`/`command` as in §7.4.1, (2) `OTEL_METRIC_EXPORT_INTERVAL=5000` in the running container env, (3) Collector metrics pipeline + Prometheus scrape target UP.

**Also required:** Jaeger shows a trace for one of those `/v1/info` calls (§7.3.6 correlation).

**Additional exercise (optional):** explore auto-instrumented HTTP metric names (`http_server_*` / semconv variants) and record whatever your pin exposes — do **not** treat those as the primary pass/fail signal.

### 7.4.3 Worked example — collector outage (application must not die)

```bash
cd "$HARBOUR_ROOT/observability"
curl -sf http://127.0.0.1:8000/ready

docker compose stop otel-collector
for i in $(seq 1 20); do curl -sf http://127.0.0.1:8000/health || echo APP_DOWN; done

docker compose start otel-collector
sleep 5
curl -sf http://127.0.0.1:8000/ready
```

**Expected:** Application HTTP stays up (`APP_DOWN` should not appear). Telemetry may have **gaps**. If the app hangs or crashes on export, fix exporter settings — telemetry must **degrade**, not take the user path down.

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

### 7.5.4 Worked example — Prometheus alert rule (firing ≠ paging)

**Distinguish three layers:**

| Layer | What it means | This section |
| --- | --- | --- |
| Metric | `harbour_info_requests_total` exists | §7.4.2 |
| **Alert rule firing** | Prometheus evaluated the expr true for `for:` duration | **Required** |
| Paging integration | Alertmanager → email/Slack/PagerDuty to a human | **Not claimed** unless you build it |

Replace the placeholder from §7.4.1 (`groups: []`) with the real rule in `observability/otel/alert-rules.yml`:

```yaml
groups:
  - name: harbour-sli
    rules:
      - alert: HarbourInfoErrorRatioHigh
        expr: |
          (
            sum(rate(harbour_info_requests_total{outcome="error"}[1m]))
            /
            clamp_min(sum(rate(harbour_info_requests_total[1m])), 1e-9)
          ) > 0.1
        for: 30s
        labels:
          severity: page
          service: harbour-api
        annotations:
          summary: "Harbour error outcome ratio > 10% (1m rate, sustained 30s)"
          description: "Synthetic or real faults elevated outcome=error on harbour.info.requests."
          runbook_url: "docs/observability/runbook-latency-errors.md"
```

Training windows are intentionally short (`[1m]` + `for: 30s`) so Firing is observable without a multi-minute wait. Production alerts would use longer windows.

Reload Prometheus after replacing the file:

```bash
curl -sS -X POST http://127.0.0.1:9090/-/reload
# If reload fails (file change not visible), restart: docker compose restart prometheus
```

**Evaluate against synthetic failures — sustain until Firing is observed:**

```bash
# Baseline — should NOT fire (success traffic only)
for i in $(seq 1 10); do curl -sS -o /dev/null http://127.0.0.1:8000/v1/info; done
sleep 20
curl -sG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=ALERTS{alertname="HarbourInfoErrorRatioHigh"}' \
  | python3 -m json.tool | head -n 30

# Keep error ratio high and poll until alertstate=firing (or timeout)
deadline=$((SECONDS + 180))
fired=0
while (( SECONDS < deadline )); do
  curl -sS -o /dev/null http://127.0.0.1:8000/v1/fail
  curl -sS -o /dev/null http://127.0.0.1:8000/v1/fail
  curl -sS -o /dev/null http://127.0.0.1:8000/v1/info
  body="$(curl -sG 'http://127.0.0.1:9090/api/v1/query' \
    --data-urlencode 'query=ALERTS{alertname="HarbourInfoErrorRatioHigh",alertstate="firing"}')"
  if echo "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("data",{}).get("result") else 1)'; then
    echo "$body" | python3 -m json.tool | head -n 40
    echo "alert-firing-ok"
    fired=1
    break
  fi
  # Show pending progression occasionally:
  curl -sG 'http://127.0.0.1:9090/api/v1/query' \
    --data-urlencode 'query=ALERTS{alertname="HarbourInfoErrorRatioHigh"}' \
    | python3 -c 'import json,sys; r=json.load(sys.stdin).get("data",{}).get("result",[]); print("alerts:", r or "none")'
  sleep 2
done
test "$fired" = 1 || { echo "TIMEOUT: alert never fired — check rule reload, metric outcomes, evaluation_interval"; exit 1; }
```

Open Prometheus → **Alerts** → `HarbourInfoErrorRatioHigh`. States: **Inactive** → **Pending** (`for:` not yet elapsed) → **Firing**.

**Expected:** the loop prints `alert-firing-ok` with `alertstate="firing"` JSON — not a fixed 80-second hope. Stopping fault injection and waiting for the rate window to empty should clear the alert.

**Paging:** Wiring Alertmanager receivers is optional Advanced work. Recording “alert fired in Prometheus” is **Competent**. Saying “on-call was paged” without Alertmanager/notification proof is not.

`docs/observability/runbook-latency-errors.md`:

```markdown
# Runbook — HarbourInfoErrorRatioHigh

## When this fires
Prometheus alert HarbourInfoErrorRatioHigh is **firing** (error outcome ratio > 10% for 30s).

## Urgency / owner
- Urgency: treat as page-worthy *if* this were production + Alertmanager routed
- Owner: platform-oncall (training: you)
- Training note: firing in Prometheus ≠ a human was notified

## Verify
1. Query harbour_info_requests_total by outcome
2. Jaeger: error/slow spans — app vs DB
3. Recent deploy digest vs service.version
4. Collector health — missing telemetry can hide recovery

## Mitigate
- Stop fault injection / revert bad digest (D06)
- Restore DB if dependency spans fail
- Do not restart pods as the first superstition
```

### 7.5.5 Practice — reproduce

Generate a **short** spike of `/v1/fail` (under the `for: 30s` window) and confirm the alert stays **Pending** or never fires; then run the sustained poll loop until **Firing** is actually observed. Write which pattern you would page and why, with budget math from §7.5.3.

**Verify:** SLIs have precise numerators/denominators; you have JSON or UI evidence of a firing alert; you did not claim a paging channel you did not configure.

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

> Harbour + Postgres on Compose network `db`. API `entrypoint: opentelemetry-instrument` (PID 1 cmdline verified). Pinned deps in `harbour-api:otel`. Placeholder `alert-rules.yml` before first `up`; real rule loaded in §7.5. `/v1/info` log/Jaeger `trace_id` matched. Polled until `harbour_info_requests_total` appeared (`OTEL_METRIC_EXPORT_INTERVAL=5000`). Sustained `/v1/fail` until `HarbourInfoErrorRatioHigh` firing JSON observed. Collector stop: app OK. CONTRACT.md written. No paging vendor claimed.

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

**Previous chapter:** [Chapter 6 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md) · **Course detail:** [D07 — Observability](../../3%20Course%20Detail/3.1%20DevOps/D07%20Observability.md) · **Next chapter:** [Chapter 8 — Datadog](D08%20Datadog.md) · **Checklist:** [Final Project Checklist · D07](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
