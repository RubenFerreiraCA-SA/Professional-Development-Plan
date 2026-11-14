# T-DEV-07-B — Beginner Foundations

*Chapter: [T-DEV-07 — Datadog Monitoring](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-07-b"></a>
#### T-DEV-07-B — Beginner Foundations

**The data path.**

| Piece | Owns |
| --- | --- |
| Application SDK | Spans, custom metrics, resource attributes |
| Datadog Agent | Receiving and forwarding data, infrastructure checks, log collection |
| Datadog backend | Indexing, querying, monitors, retention, access control |
| Humans | Keys, tag policy, monitor ownership, cost |

Data flows: application → Agent (a local process or container) → Datadog. The Agent also collects host and container metrics and, if enabled, container logs.

**Keys and sites.**

| Setting | Purpose | Where to keep it |
| --- | --- | --- |
| `DD_API_KEY` | Agent data intake | Secret manager or a gitignored environment file |
| `DD_APP_KEY` | API and Terraform automation, narrow scopes | Same; not in the Agent container unless required |
| `DD_SITE` | Which regional site (for example `datadoghq.com` or `datadoghq.eu`) | Safe to commit as an example |

A wrong site or a missing key is the most common reason "nothing appears".

**Unified service tagging.** Three tags tie metrics, traces and logs together:

| Datadog tag | Meaning | Typical environment variable |
| --- | --- | --- |
| `service` | Logical service name | `DD_SERVICE` (or OpenTelemetry's service name) |
| `env` | Environment | `DD_ENV` |
| `version` | Deployed version | `DD_VERSION` |

Inconsistent tags split a service across multiple pages and break deployment comparison.

**Run an Agent in Compose**

```yaml
services:
  datadog-agent:
    image: gcr.io/datadoghq/agent:7
    env_file: [.datadog.env]          # contains DD_API_KEY=..., gitignored
    environment:
      DD_SITE: datadoghq.com
      DD_ENV: staging
      DD_APM_ENABLED: "true"
      DD_LOGS_ENABLED: "true"
      DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL: "true"
      DD_DOGSTATSD_NON_LOCAL_TRAFFIC: "true"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc/:/host/proc/:ro
      - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
    ports: ["8126:8126"]
  api:
    image: orders-api:local
    environment:
      DD_SERVICE: orders-api
      DD_ENV: staging
      DD_VERSION: "1.0.0"
      DD_AGENT_HOST: datadog-agent
```

Check with `docker exec datadog-agent agent status`. If you already ran another collector that owns the same trace port, stop it first or you will get bind errors.

**Vocabulary**

| Term | Meaning |
| --- | --- |
| Metric | A numeric time series, such as request count or CPU usage. |
| Trace / span | A trace is one request's path through services; a span is one timed operation in it. |
| Log | A timestamped event line, ideally structured as JSON. |
| APM | Application performance monitoring: traces and service-level views built from spans. |
| Monitor | A saved condition that alerts when data crosses a threshold or stops arriving. |
| Host / container | The infrastructure object the Agent reports on. |
| Tag | A `key:value` label attached to data, used to filter and group. |
| DogStatsD | The Agent's UDP/StatsD-compatible listener for custom metrics, default port 8125. |

**The three signals, and what each answers.** Metrics answer "is something wrong, and how much?". Traces answer "where in the request did the time go?". Logs answer "what exactly happened in this event?". Datadog's value comes from linking them: a trace shows the related log lines, and a log line carries the trace ID, so you jump from symptom to cause without guessing. That linking only works when the same `service`, `env` and `version` tags are applied everywhere.

**Why tags matter, with an example.** If one process reports `service:orders-api` and another reports `service:orders_api`, Datadog treats them as two services. A deployment comparison for version `1.1.0` then sees only half the traffic. Pick one spelling, set it through environment variables, and keep it in one place.

```text
Healthy:   service:orders-api  env:staging  version:1.0.0
Broken:    service:orders-api  env:stage    version:1.0.0   # "stage" splits staging data
Broken:    service:OrdersAPI   env:staging  (no version)     # new service, no deploy markers
```

**Checking that the Agent works, in order**

```bash
docker exec datadog-agent agent status          # API key valid? forwarder reachable? APM receiver listening?
docker logs datadog-agent 2>&1 | tail -n 30     # key, site or permission errors appear here
docker exec api env | grep '^DD_'               # did the app receive the expected variables?
curl -s http://127.0.0.1:8126/info | head       # is the trace intake answering on the host?
```

Read `agent status` for three things: the API key line shows as valid, the forwarder shows successful transactions, and the APM section shows a receiver with traces received.

**Troubleshooting "nothing appears"**

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Agent status says API key invalid | Wrong key, or key for another organisation | Compare `DD_API_KEY` length and origin; never print the whole key |
| Agent healthy but no data in the interface | Wrong `DD_SITE` for the account's region | Open the interface at the matching site; check the status header |
| Host visible, no traces | App not pointed at the Agent | `DD_AGENT_HOST`; SDK installed and enabled; port 8126 reachable |
| Traces visible, no logs | Log collection not enabled | `DD_LOGS_ENABLED`; container log configuration |
| Agent will not start, port in use | Another collector holds the port | `ss -ltnp \| grep -E '8126\|8125'`; stop the other collector |
| Service appears twice | Inconsistent `service` tag | Compare the variables in each container |

**Keys: handling rules.** The API key can send data into your account, so treat it as a secret. Keep it in a gitignored file or secret manager, rotate it if it appears in a log or screenshot, and prefer separate keys per environment. Application keys carry user permissions; give automation the narrowest scopes it needs.

**Cost awareness.** Datadog charges by hosts, indexed logs, custom metrics, ingested spans and more. Collecting every container log with `CONTAINER_COLLECT_ALL` is convenient for learning but can be expensive in production. Note the setting and plan to narrow it.

**Common mistakes**

- Pasting a key into a Compose file that is then committed.
- Generating only successful requests, then having no failing or slow traces to look at. Create all three kinds on purpose.
- Setting `DD_ENV` only on the Agent, not on the application.
- Judging the setup from the Agent being "up" without finding one trace and one log line in the interface.

**Exercise.** Start the Agent, generate a few successful, failing and slow requests, and find the host, one trace and one log line in the interface. Note which tag values appear.
