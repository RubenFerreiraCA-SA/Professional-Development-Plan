# Chapter 8 — Datadog (D08)

*DevOps Engineering textbook · Chapter 8 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D08 course detail](../../3%20Course%20Detail/3.1%20DevOps/D08%20Datadog.md) (about 24–36 hours). |
| **Prerequisites** | [D07 — Observability](D07%20Observability.md) completed (instrumented Harbour + OTel habits); authorised Datadog trial/sandbox account; Docker Compose. |

## How to study this chapter

D07 built a **vendor-neutral** pipeline. D08 turns that into an **operable Datadog monitoring service**: Agent ingestion, APM/logs correlation, dashboards, SLOs, monitors, incident drills and a reusable onboarding package for a second team/service.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Where Agent mounts, OTLP intake, monitors or costs go wrong, this chapter **shows a working sequence first**, then asks you to reproduce it.

This text teaches [D08 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D08%20Datadog.md). The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) may mark D08 `N/A` for personalised IDP acceptance if you prove an equivalent ops bar on the D07 stack — **that does not remove D08 from the full DevOps curriculum**. Completing this chapter is required for “full DevOps syllabus complete.”

> **Safety, privacy and cost boundary:** Use a **training** Datadog org/site only. Never put `DD_API_KEY` / `DD_APP_KEY` in Git. Use synthetic demo data only — no production PII. Confirm plan limits and estimated ingest cost **before** enabling high-cardinality tags or “collect all logs.” Do not page a real on-call rotation with training monitors without permission. Destroy or disable Agents when finished.

> **Continuity from D07:** Keep the OpenTelemetry instrumentation in Harbour. This chapter’s default path is **OTLP → Datadog Agent** (Unified Service Tagging aligned with D07 resource attributes). You may instead use `ddtrace` or a Collector `datadog` exporter — record the choice in an ADR and note sampling/feature differences.

### Learning outcomes

1. Explain Datadog Agent, APM, logs, monitors and access boundaries.
2. Deploy a least-privilege Agent and verify health/intake.
3. Correlate metrics, traces and logs with stable `service` / `env` / `version` tags.
4. Build user-centric dashboards and SLOs (not only host graphs).
5. Implement and **validate** two monitors (user impact + missing telemetry).
6. Investigate regressions and Agent blind spots with competing hypotheses.
7. Ship Terraform (or equivalent) config-as-code plus a second-service onboarding package.
8. Review privacy, cardinality, retention and cost controls.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"
test -f observability/docker-compose.yml || echo "Complete D07 Compose stack first"
test -f observability/otel/requirements-otel.txt
mkdir -p observability/datadog docs/observability/datadog terraform/datadog
# Keys live only in a gitignored env file (created in §8.2):
#   observability/datadog/datadog.env
grep -n 'datadog.env' .gitignore 2>/dev/null || echo 'observability/datadog/datadog.env' >> .gitignore
```

You need: D07 Harbour image/instrumentation habits, a Datadog account with permission to create API + Application keys, and browser access to the Datadog UI for your site (`datadoghq.com`, `datadoghq.eu`, etc.).

---

## Section 8.1 — Architecture and trust boundaries

### 8.1.1 Map the data path

```text
Harbour (OTel SDK) ──OTLP──► Datadog Agent ──► Datadog intake (metrics / APM / logs)
                                      │
                         host/container integrations (CPU, restarts, …)
```

| Piece | Owns |
| --- | --- |
| App SDK (D07) | Spans, custom metrics, resource attributes |
| Datadog Agent | Receive/forward, infra checks, log collection |
| Datadog backend | Indexing, query, monitors, retention, RBAC |
| Humans | Keys, tag policy, monitor ownership, cost |

### 8.1.2 Unified Service Tagging

Align D07 attributes with Datadog’s `service` / `env` / `version`:

| Datadog tag | OTel / env |
| --- | --- |
| `service` | `OTEL_SERVICE_NAME` / `service.name` → also set `DD_SERVICE` |
| `env` | `deployment.environment.name` → `DD_ENV` |
| `version` | `service.version` → `DD_VERSION` |

Inconsistent tags shatter APM service pages and deployment comparison.

### 8.1.3 Keys and sites

| Secret | Purpose | Store |
| --- | --- | --- |
| `DD_API_KEY` | Agent / ingest | gitignored env / secret manager |
| `DD_APP_KEY` | Terraform / API automation (narrow scopes) | same — **not** in Agent container unless required |
| `DD_SITE` | `datadoghq.com` / `datadoghq.eu` / … | committed example OK |

**ADR prompt** (`docs/decisions/0008-datadog-path.md`): OTLP→Agent vs `ddtrace` vs Collector exporter; site; who owns monitors; sampling; log indexing vs archival.

**Verify:** You can sketch the path and name which key the Agent needs versus which key Terraform needs.

---

## Section 8.2 — Deploy the Agent (working Compose path)

### 8.2.1 Worked example — credentials file

`observability/datadog/datadog.env.example` (commit this):

```bash
DD_SITE=datadoghq.eu
DD_API_KEY=replace-me
# Optional for later Terraform on your laptop — never bake into the Agent image:
# DD_APP_KEY=replace-me
DD_ENV=local
DD_HOSTNAME=harbour-local
```

```bash
cp observability/datadog/datadog.env.example observability/datadog/datadog.env
# Edit datadog.env with a real training API key — do not commit
```

### 8.2.2 Worked example — Agent service + OTLP intake

Add to `observability/docker-compose.yml` (or `observability/docker-compose.datadog.yml` that you merge with `-f`). **Pin** the Agent image tag.

```yaml
  datadog-agent:
    image: gcr.io/datadoghq/agent:7.57.0
    env_file:
      - ./datadog/datadog.env
    environment:
      DD_API_KEY: "${DD_API_KEY}"  # prefer env_file only; avoid shell export leaks in shared history
      DD_SITE: "${DD_SITE:-datadoghq.eu}"
      DD_HOSTNAME: harbour-local
      DD_APM_ENABLED: "true"
      DD_APM_NON_LOCAL_TRAFFIC: "true"
      DD_OTLP_CONFIG_RECEIVER_PROTOCOLS_GRPC_ENDPOINT: "0.0.0.0:4317"
      DD_OTLP_CONFIG_RECEIVER_PROTOCOLS_HTTP_ENDPOINT: "0.0.0.0:4318"
      DD_LOGS_ENABLED: "true"
      DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL: "true"
      DD_CONTAINER_EXCLUDE: "name:datadog-agent"
      DD_PROCESS_AGENT_ENABLED: "false"
      DD_DOGSTATSD_NON_LOCAL_TRAFFIC: "true"
    ports:
      # If otel-collector still binds host 4317, stop that service or use a compose
      # override that removes host publish from the collector for the D08 lab.
      - "4317:4317"
      - "4318:4318"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc/:/host/proc/:ro
      - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
    pid: host
```

> **Port conflict with D07 Collector:** Only one process should publish host `4317` for the lab. For D08, **stop** `otel-collector` (and Jaeger if unused) *or* run a compose override that points Harbour at `datadog-agent` and leaves the Collector off. Do not dual-bind.

Point Harbour at the Agent (Compose `api` environment — mandatory override for this chapter):

```yaml
  api:
    environment:
      DATABASE_HOST: db
      OTEL_EXPORTER_OTLP_ENDPOINT: http://datadog-agent:4317
      OTEL_METRIC_EXPORT_INTERVAL: "5000"
      OTEL_BSP_SCHEDULE_DELAY: "1000"
      DD_SERVICE: harbour-api
      DD_ENV: local
      DD_VERSION: dev
    # Keep D07 mandatory instrumentation wrapper:
    entrypoint: ["opentelemetry-instrument"]
    command:
      - uvicorn
      - harbour_api.main:app
      - --host
      - "0.0.0.0"
      - --port
      - "8000"
    depends_on:
      db:
        condition: service_healthy
      datadog-agent:
        condition: service_started
```

### 8.2.3 Worked example — bring-up and Agent health

```bash
cd "$HARBOUR_ROOT/observability"
test -f datadog/datadog.env
# Ensure API key is not the placeholder:
grep -q 'replace-me' datadog/datadog.env && echo "EDIT datadog.env FIRST" && exit 1

# Avoid 4317 clash with D07 collector if still defined:
docker compose stop otel-collector jaeger 2>/dev/null || true

docker compose up -d db datadog-agent api
docker compose ps

# Agent status (agent image includes its CLI):
docker compose exec datadog-agent agent status | head -n 80
docker compose exec datadog-agent agent status | grep -iE 'API Key|OTLP|APM|Reporter|Forwarder' || true
```

**Expected:** Agent reports a valid API key / forwarder success (wording varies by version). OTLP receiver listening. No repeated auth failures in `docker compose logs datadog-agent --tail=50`.

In the Datadog UI: **Infrastructure → Host Map** (or Fleet) → host `harbour-local` appears within a few minutes.

### 8.2.4 Practice — reproduce

From a fresh shell, re-check Agent status and that `api` PID 1 still starts with `opentelemetry-instrument`:

```bash
docker compose exec api sh -c 'tr "\0" " " < /proc/1/cmdline; echo'
```

### 8.2.5 Challenge — least privilege

Document which mounts you granted (`docker.sock`, `/proc`, cgroup) and what an attacker with Agent-container access could learn. Note one mount you would remove in a locked-down Kubernetes DaemonSet and what visibility you would lose.

**Verify:** Host visible in UI; Agent status healthy; Harbour still serves `/health`.

---

## Section 8.3 — Infrastructure and container monitoring

### 8.3.1 Worked example — baseline dashboard inputs

Generate load and inspect container metrics for `harbour-api` / compose project:

```bash
for i in $(seq 1 30); do curl -sS http://127.0.0.1:8000/v1/info >/dev/null; done
```

In Datadog: container CPU/memory for the API container; confirm tags include `service:harbour-api` / `env:local` when present.

Create (UI or later Terraform) a simple **infrastructure** dashboard widget: container RSS/CPU, restart count if available.

### 8.3.2 Worked example — memory pressure vs application exception

**Drill A — application fault (D07 `/v1/fail`):**

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/v1/fail
```

Find the error in APM/logs (§8.4). Infrastructure may look fine.

**Drill B — stop Agent (telemetry gap, app healthy):**

```bash
curl -sf http://127.0.0.1:8000/ready
docker compose stop datadog-agent
for i in $(seq 1 20); do curl -sf http://127.0.0.1:8000/health || echo APP_DOWN; done
# UI: metrics/traces go stale — do not interpret as "service healthy because no alerts"
docker compose start datadog-agent
```

**Expected:** `APP_DOWN` does not appear. Datadog shows a **visibility gap**. Record timestamps for both drills.

### 8.3.3 Optional — OOM style termination

If your Compose API has a tight `mem_limit`, force an OOM in training and compare Agent/container exit vs app logs. If you skip this, document why (resource constraints) — still complete Drill A/B.

**Verify:** You can explain how tagging lets you jump from host/container → service.

---

## Section 8.4 — Logs, APM and correlation

### 8.4.1 Worked example — produce success, fail and slow

```bash
# Success
RESP="$(curl -sS http://127.0.0.1:8000/v1/info)"
echo "$RESP"
TID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["trace_id"])' <<<"$RESP")"

# Fail
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/v1/fail

# Slow (temporary): add sleep in /v1/info only for this drill, rebuild/restart api, then remove
```

### 8.4.2 Worked example — navigate Service → Trace → Span → Log

In Datadog APM:

1. Open service `harbour-api` / env `local`.  
2. Find a recent trace; open the flame graph.  
3. Identify DB/client span when `/ready` or DB work runs (D07 two-component path).  
4. From a span, open **related logs** (or search logs for `@trace_id:${TID}` / the hex id your logger emits).  

**Expected:** Same `trace_id` as the JSON log line from D07’s `/v1/info` handler. If logs lack correlation, fix logger fields or Agent log collection — do not claim correlation you cannot click through.

### 8.4.3 Worked example — break and restore propagation

Temporarily point a second HTTP call (if you added `harbour-deps`) without propagating context, **or** strip W3C `traceparent` on an outbound call. Observe a broken parent/child relationship. Restore instrumentation. Document before/after.

### 8.4.4 Sampling honesty

Compare APM trace count to request metrics for a busy minute. **Missing traces ≠ zero traffic** under sampling. Prefer metrics for rates; traces for causality.

### 8.4.5 Governance — logs

In Datadog Log Management (training):

- Add an **exclusion filter** or disable indexing for noisy health checks if volume is high.  
- Demonstrate or document **sensitive data scrubbing** (e.g. deny-list `password`, `token`).  
- Note retention for indexed vs online archives per your plan.

**Practice — reproduce:** Change `DD_VERSION`, restart API, show a new version appears on traces after traffic.

**Verify:** Success/fail/slow each leave evidence; correlation works after a version bump.

---

## Section 8.5 — Dashboards, SLOs and monitors

### 8.5.1 Worked example — service dashboard (user-centric)

Build a dashboard `Harbour API — local` with widgets for:

| Widget | Signal |
| --- | --- |
| Requests / errors | APM hits or custom `harbour.info.requests` if exported |
| Latency | p95 from APM |
| Version | `version` tag / deployment |
| Dependency | DB time or error spans |
| Resource | Container CPU/RSS |
| Telemetry health | Agent up / intake (or monitor status) |

Export JSON to `docs/observability/datadog/dashboard-harbour-api.json` (UI share/export) for version control.

### 8.5.2 Worked example — SLO from D07 SLI

Create an SLO in Datadog tied to your critical-read SLI (metric-based or monitor-based — pick what your plan supports). Use a **short training window** if needed, but label it as training.

Document target (e.g. 99%), window and what burns the budget — same arithmetic discipline as D07 §7.5.

### 8.5.3 Worked example — two monitors (configure + validate)

**Monitor 1 — customer impact** (error rate / fail traffic):

- Query: APM error rate on `service:harbour-api` **or** metric derived from your custom counter if visible in Datadog.  
- Threshold: e.g. error rate > 10% for 5 minutes (training may use 5–10 minutes evaluation; shorten only if the UI allows and you still wait for **Alert** state).  
- Severity / owner / runbook URL (`docs/observability/datadog/runbook-errors.md`).  
- Notify: a **training** email or `@webhook` you control — **not** production on-call.  
- Missing data: document “ignore” vs “show no data” choice.

**Monitor 2 — missing telemetry**:

- Query: Agent / host not reporting, or no APM hits for `service:harbour-api` when you expect traffic (choose a signal Datadog exposes for Agent downtime).  
- Validation: `docker compose stop datadog-agent` until the monitor alerts; restart Agent; confirm recovery.  
- Runbook: `docs/observability/datadog/runbook-missing-telemetry.md` — distinguish “app down” vs “blind.”

**Validation protocol (both monitors):**

```text
1. Record monitor ID + query screenshot/JSON
2. Induce condition ( /v1/fail loop  OR  stop Agent )
3. Wait until Datadog shows Alert (poll UI — do not claim Alert after a fixed sleep alone)
4. Mitigate (stop faults / start Agent)
5. Confirm recovery (OK / No Data → OK as designed)
```

| Claim | Evidence |
| --- | --- |
| Monitor **configured** | Query + thresholds saved |
| Monitor **Alert observed** | UI state or Events timeline |
| On-call **paged** | Only if your training notify target received a message |

### 8.5.4 Noisy threshold refinement

Create a deliberately noisy CPU > 5% monitor, observe flapping, then fix with longer window / grouping / smarter query. Record before/after.

**Verify:** Dashboard + SLO exist; both monitors have Alert-observed validation notes.

---

## Section 8.6 — Incident response in Datadog

### 8.6.1 Worked example — planted regression

Plant **one** cause in the sandbox (slow handler, slow DB, or bad version). Optionally raise container CPU with a burn loop so CPU correlates misleadingly.

Follow:

1. Symptom + time window  
2. ≥3 hypotheses  
3. APM + logs + infra + version tags  
4. Contradict at least one hypothesis  
5. Mitigate (revert code/digest or fix DB)  
6. Verify **D07 SLI** recovery, not only green CPU  
7. Write `docs/observability/datadog/incident-YYYYMMDD.md`

### 8.6.2 Worked example — Agent blind spot (second drill)

Stop Agent while app serves traffic (§8.3.2). Show in the write-up how a responder recognises **loss of visibility** (Monitor 2, stale metrics) versus a silent healthy service.

**Practice — reproduce:** Cold investigation notes without the plant spoilers.

**Verify:** Incident note includes contradicting evidence and a monitoring gap follow-up.

---

## Section 8.7 — Datadog as a reusable platform service

### 8.7.1 Worked example — Terraform for a monitor (minimum as-code)

`terraform/datadog/providers.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    datadog = {
      source  = "DataDog/datadog"
      version = "~> 3.46"
    }
  }
}

provider "datadog" {
  api_key = var.dd_api_key
  app_key = var.dd_app_key
  api_url = var.dd_api_url # e.g. https://api.datadoghq.eu/
}
```

`terraform/datadog/variables.tf` — keys via env `TF_VAR_dd_api_key` / `TF_VAR_dd_app_key` or a secret backend — **never** commit `terraform.tfvars` with real keys.

`terraform/datadog/monitor_missing_agent.tf`:

```hcl
resource "datadog_monitor" "harbour_agent_missing" {
  name    = "harbour-local: Datadog Agent / host not reporting"
  type    = "service check"
  # Adjust query to a check your Agent actually emits (e.g. datadog.agent.up).
  # If service checks differ on your site, use an equivalent metric monitor —
  # the requirement is managed-as-code + validated Alert, not this exact string.
  query   = "\"datadog.agent.up\".over(\"host:harbour-local\").by(\"host\").last(2).count_by_status()"
  message = """
Agent/host telemetry missing for harbour-local.
Runbook: docs/observability/datadog/runbook-missing-telemetry.md
Notify: training channel only @${var.training_notify}
"""
  monitor_thresholds {
    critical = 1
  }
  notify_no_data    = true
  no_data_timeframe = 10
  tags              = ["service:harbour-api", "env:local", "managed:terraform"]
}
```

```bash
cd "$HARBOUR_ROOT/terraform/datadog"
export TF_VAR_dd_api_key='…' TF_VAR_dd_app_key='…'   # not logged to git
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

**Expected:** plan shows create; UI shows the managed monitor; second plan is empty (or intentional drift). Then validate Alert by stopping the Agent (§8.5.3) — Terraform create alone is not validation.

### 8.7.2 Worked example — onboarding package

`docs/observability/datadog/ONBOARDING.md`:

```markdown
# Datadog onboarding — Harbour platform

## Required tags
service, env, version (match OTel resource attributes)

## Instrumentation
- Prefer OTLP → platform Agent endpoint
- Structured logs with trace_id; no PII/secrets

## Starter assets
- Dashboard template: dashboard-harbour-api.json (clone + replace service)
- Monitors: customer-impact + missing-telemetry (Terraform module path …)
- Runbooks: …

## Ownership
- Service owner for Monitor 1
- Platform owner for Agent / Monitor 2

## Cost / cardinality
- Allowed metric tags: …
- Log exclusion defaults: …
```

### 8.7.3 Worked example — second service (`harbour-worker`)

Minimal second component under `app/harbour_worker/main.py`:

```python
from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health():
    return {"status": "ok", "service": "harbour-worker"}
```

Compose service (same Agent OTLP endpoint; **different** `DD_SERVICE` / `OTEL_SERVICE_NAME`):

```yaml
  worker:
    image: harbour-api:otel   # or a thin image with FastAPI + OTel pins
    working_dir: /work
    volumes:
      - ../app:/work/app:ro
    environment:
      OTEL_SERVICE_NAME: harbour-worker
      OTEL_EXPORTER_OTLP_ENDPOINT: http://datadog-agent:4317
      OTEL_METRIC_EXPORT_INTERVAL: "5000"
      DD_SERVICE: harbour-worker
      DD_ENV: local
      DD_VERSION: dev
    entrypoint: ["opentelemetry-instrument"]
    command:
      - uvicorn
      - harbour_worker.main:app
      - --host
      - "0.0.0.0"
      - --port
      - "8001"
    ports:
      - "8001:8001"
    depends_on:
      - datadog-agent
```

```bash
curl -sS http://127.0.0.1:8001/health
# Datadog APM: service harbour-worker appears after traffic
```

1. Clone dashboard/monitors with `service:harbour-worker` (or Terraform `for_each`).  
2. Record which steps were self-service vs needed platform help.  
3. List one automation to add next (module variable `service_name`).

**Verify:** Second service visible; onboarding doc alone almost sufficient for a colleague.

---

## Section 8.8 — Privacy, permissions, retention and cost

### 8.8.1 Review checklist (complete in writing)

| Topic | Your control / limitation |
| --- | --- |
| Who can view APM/logs | Roles / teams |
| API/App key scopes | Least privilege; rotation note |
| PII in logs/spans | Scrubbing / exclusions tested |
| High-cardinality tags | Deny-list (user id, raw URL) |
| Log retention / indexing | Plan limits recorded |
| Estimated monthly ingest | Rough calc from training volume × list price |
| Unused dashboards/monitors | Cleanup owner |

**Verify:** The review file exists under `docs/observability/datadog/governance.md`.

---

## Section 8.9 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| No host in UI | Bad API key / wrong `DD_SITE` | `agent status`; key not `replace-me` |
| No traces | App still pointed at old Collector; Agent OTLP off | `OTEL_EXPORTER_OTLP_ENDPOINT`; Agent OTLP config |
| Port bind error | Collector and Agent both on host 4317 | Stop collector for D08 lab |
| Bare uvicorn | Missing `entrypoint: opentelemetry-instrument` | `/proc/1/cmdline` |
| Logs without traces | Collection off / no trace_id field | Log pipeline; D07 logger JSON |
| Monitor never Alerts | Window too long / wrong query / no notify wait | Induce fault; poll UI until Alert |
| Huge bill surprise | Container collect-all + high cardinality | Exclusions; tag allowlist |

---

## Practical Assessment — Chapter 8 — operate the observability platform

Align with [D08 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D08%20Datadog.md) and Final Project Checklist D08.

### Required deliverables

1. Documented Agent install with infra + logs + APM intake working.  
2. Correlated traces, logs, versions and dependency evidence for Harbour.  
3. User-centric dashboard + SLI/SLO configuration.  
4. Two validated monitors (user impact + missing telemetry) with runbooks and ownership.  
5. Application degradation drill with evidence-led fix and SLI recovery.  
6. Telemetry pipeline failure drill and response notes.  
7. Version-controlled onboarding/config package applied to a **second** service.  
8. Privacy / permissions / retention / cost review.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Intake | Agent installed | OTLP/APM/logs + UST consistent | Collector dual-path or K8s DaemonSet hardened |
| Correlation | Separate signals | Click-through trace↔log↔version | Broken propagation found and fixed |
| Monitors | Created in UI | Both validated to Alert + recover | Terraform-managed + notify proof |
| Incidents | Restarted stuff | Hypotheses + contradict + SLI verify | Separates CPU coincidence from cause |
| Platform | One service | Second service via onboarding doc | Module/automation for new services |
| Governance | Ignored cost | Written review with controls | Measured ingest + tag policy enforced |

**Completion standard:** **Competent** on every row. Another engineer can diagnose a regression, recognise a blind Agent and onboard a service from the package without tribal knowledge. Screenshots alone fail.

### Self-check

- Does `/proc/1/cmdline` show `opentelemetry-instrument`?  
- Did you stop the D07 Collector clash on `4317` deliberately?  
- Can you show Alert → recover for **both** monitors?  
- Is the second service using the package, not a one-off clickpath?  
- Are keys absent from Git?

### Example assessment conclusion (evidence still required)

> Training Datadog EU site; Agent `7.57.0` with OTLP; Harbour OTLP→Agent after Collector stopped. UST `harbour-api`/`local`/`dev`. Trace_id matched logs. Dashboard + SLO filed. Monitors: error-ratio Alert under `/v1/fail`; missing-telemetry Alert with Agent stopped — both recovered. Incident write-up contradicted CPU-only theory. Terraform manages missing-telemetry monitor. `harbour-worker` onboarded from ONBOARDING.md. Governance notes retention and tag deny-list. Keys only in `datadog.env`.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Get traces into DD | OTLP endpoint → Agent; check `agent status` | Leaving app on dead Collector port |
| Prove correlation | Same trace_id in log + APM | Assuming UI adjacency without IDs |
| Page-worthy signal | User-impact monitor + runbook | CPU-only pages |
| Spot blindness | Missing-telemetry monitor + Agent stop drill | “No alerts ⇒ healthy” |
| Onboard a team | ONBOARDING.md + Terraform module | Clickops per service |
| Control cost | Exclusions + cardinality allowlist | `collect all` forever |

## Glossary

| Term | Definition |
| --- | --- |
| Unified Service Tagging | Consistent `service`/`env`/`version` across signals |
| APM | Application performance monitoring (traces/services) |
| Intake | Datadog’s receive path for Agent payloads |
| Indexed log | Log searchable in hot storage (costs more) |
| Monitor Alert | Datadog evaluated state — not necessarily a human page |
| Application key | API automation credential (Terraform), broader than ingest |

## References

- [Datadog docs](https://docs.datadoghq.com/)
- [Datadog Agent](https://docs.datadoghq.com/agent/)
- [OTLP intake](https://docs.datadoghq.com/opentelemetry/)
- [Datadog APM](https://docs.datadoghq.com/tracing/)
- [Unified Service Tagging](https://docs.datadoghq.com/getting_started/tagging/unified_service_tagging/)
- [SLOs](https://docs.datadoghq.com/service_management/service_level_objectives/)
- [Datadog Terraform provider](https://registry.terraform.io/providers/DataDog/datadog/latest/docs)
- [OpenTelemetry](https://opentelemetry.io/docs/)

**Previous chapter:** [Chapter 7 — Observability](D07%20Observability.md) · **Course detail:** [D08 — Datadog](../../3%20Course%20Detail/3.1%20DevOps/D08%20Datadog.md) · **Next:** [Cloud Engineering overview](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/CLOUD%20Overview.md) · **Checklist:** [Final Project Checklist · D08](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
