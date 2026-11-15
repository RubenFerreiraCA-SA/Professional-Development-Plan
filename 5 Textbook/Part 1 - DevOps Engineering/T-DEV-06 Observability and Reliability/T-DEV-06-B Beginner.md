# T-DEV-06-B — Beginner Foundations

*Chapter: [T-DEV-06 — Observability and Reliability](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-06-b"></a>
#### T-DEV-06-B — Beginner Foundations

## Why this matters

A program you wrote runs on a machine you cannot see, serving people you cannot watch. When it fails, the first report is usually a message from a user. At that point you need to answer a plain question quickly: *what is the system doing now, and what was it doing ten minutes ago?* Without recorded evidence the only method is guessing, and guessing under pressure produces confident, wrong, expensive actions.

**Observability** is making a running system explain itself through the data it emits, so you can ask a question you did not think of in advance and still find an answer. **Reliability** is deciding, in numbers, how well the system must work for its users, and organising your work around that target. This Beginner section builds the vocabulary and the habits from the ground up: what a log, a metric and a trace actually *are*, why each exists, what a dashboard is for, and how to read evidence in a short investigation.

This section assumes you can read simple JSON and have used a terminal. It does not assume you have run a monitoring system. All examples use a neutral fictional service called `orders-api`, which accepts requests such as `GET /v1/orders/{id}` and `POST /v1/orders`, stores data in a database and calls a payment provider. Nothing here depends on any other course material. Outputs marked *illustrative* show the expected shape, not measured results.

## First principles: three questions, three kinds of record

Start with a running program and ask what you might want to know about it afterwards. Almost every question falls into one of three kinds.

1. **"What exactly happened in that one event?"** A user's payment failed at 10:15:04. You want the details of that single occurrence: which order, which error, which code path. The natural record is a **timestamped description of the event**. We call that a **log**.
2. **"How much, how often, how fast — over time?"** You do not want ten million descriptions; you want "about 40 requests per second, 0.4% of them failing, the slowest 1% taking over two seconds". The natural record is a **number sampled or counted over time**. We call that a **metric**.
3. **"Where did this one request spend its time, and what did it call?"** A single request touched a load balancer, your service, a database and a payment provider. You want the path and the time spent at each step. The natural record is a **tree of timed steps belonging to one request**. We call that a **trace**, and each step a **span**.

These are not three brands of tool. They are three *shapes of data*, each answering a different class of question at a different cost.

| Signal | Shape of the data | Answers | Cost profile | Weakness |
| --- | --- | --- | --- | --- |
| Log | One record per event, free or structured text | "What happened in this event?" | Grows with event count; text is large | Hard to see trends; easy to drown in volume |
| Metric | One number per time series per interval | "How is the system behaving over time?" | Grows with the number of distinct series, not with event count | Cannot tell you about one specific request |
| Trace | One tree of spans per request | "Where did this request spend its time?" | Grows with request count times spans per request | Usually sampled, so a specific request may be missing |

## Monitoring and its limits

**Monitoring** is watching for conditions you already know to be important: "is the process up?", "is disk usage below 90%?", "does the health endpoint return 200?". It works by checking known questions against known thresholds. It is cheap, simple and valuable.

Its limit is that it only covers failures somebody anticipated. Consider a real-looking case. The health endpoint of `orders-api` returns `200 OK` as long as the process is alive. A configuration change makes the payment provider reject every request. The process is alive, the CPU is calm, memory is flat, the health check is green — and every checkout fails. Every monitor you set up was green and the service was broken, because none of them measured *what users were trying to do*.

| | Monitoring | Observability |
| --- | --- | --- |
| Typical question | "Is the known check green?" | "Why is this user journey slow today, and only for some users?" |
| Strength | Cheap, clear targets for known failures | Lets you explore unknown failure modes |
| Typical data | Up/down checks, simple thresholds | Rich, correlated logs, metrics and traces |
| Failure mode | Blind to novel faults, falsely reassuring | Noise, cost and cardinality if unconstrained |
| Answer to "something is wrong" | "Which of my known checks fired?" | "What changed, where, and for whom?" |

They are not rivals. Monitoring is the smoke alarm; observability is the ability to find the fire afterwards. And neither replaces resilient design: a timeout, a retry limit or a fallback does more for users than a perfect graph of the outage.

## The request path: where a request can go wrong

Before you can observe a system, draw the path a single request takes. For `orders-api` it looks like this.

```text
 user's browser
      │  1. DNS lookup, TLS, network
      ▼
 load balancer
      │  2. choose an instance, enforce a timeout
      ▼
 orders-api (several instances)
      │  3. parse request, authenticate, run handler
      ├──────────────► database        4. query, wait for rows
      └──────────────► payment provider 5. call over the internet
      ▼
 response travels back to the browser
```

Each arrow and box is a place where time is spent and where failures can occur. Write the list of questions that each place can answer.

| Step | What can go wrong | A signal that would show it |
| --- | --- | --- |
| 1. Network and DNS | Slow lookups, packet loss, certificate expiry | Synthetic check from outside; client-side timing |
| 2. Load balancer | No healthy instances, timeouts, uneven distribution | Load balancer request count, 5xx count, healthy-instance count |
| 3. Service | Slow handler, exceptions, thread pool exhaustion | Request rate, error rate, duration histogram, logs |
| 4. Database | Slow query, lock wait, connection pool full | Database span duration, pool-wait gauge |
| 5. Payment provider | Timeouts, rate limits, outages | Outbound call duration and error count, by provider |

Notice that **a request is measured from several viewpoints, and they disagree**: the load balancer sees requests your service never receives, and the user experiences the whole path. Whenever you read a graph, ask *from whose point of view was this measured?*

## The three levels to observe

Look at three levels: **user experience** (can clients complete the critical request, how often does it fail, how long does it take?), **application and dependencies** (where does time go, which version correlates?) and **platform** (restarts, memory kills, full disk, saturated CPU). Beginners tend to monitor only the platform because those numbers are easiest to collect, yet a service can have calm CPU and be useless to users. Start from user experience and work downward to causes.

## Metrics from first principles

A **metric** is a named series of numbers over time, usually with a few **labels** (also called attributes or dimensions) that split the series into variants. For example, `http_requests_total{route="/v1/orders/{id}", status="200"}` is one series, and the same metric with `status="500"` is another.

Why metrics are cheap: no matter how many requests arrive, a counter is still one number per series. A million requests in an hour does not create a million records; it increments a number a million times, and the monitoring system stores one value every 15 or 30 seconds.

### Metric types

| Type | Behaviour | Example | How you read it |
| --- | --- | --- | --- |
| Counter | Only goes up (resets to 0 on restart) | Total requests, total errors | As a **rate**: how fast it grew |
| Gauge | Goes up and down | In-flight requests, queue depth, memory in use | As the **current value** or its trend |
| Histogram | Counts observations into value ranges ("buckets") | Request duration | As **percentiles**, computed from the buckets |

**Counters and rates.** A counter on its own is not interesting: "3,000,000 requests since the process started" says nothing about now. The useful number is the *rate of change*. Suppose a counter reads 120,000 at 10:00:00 and 123,000 at 10:05:00. The increase is 3,000 over 300 seconds, so the rate is 3,000 ÷ 300 = **10 requests per second**. If the process restarts and the counter drops to 40, a good query engine notices the drop, treats it as a reset and does not report a negative rate. This is why you graph the *rate of a counter*, never the raw counter.

**Gauges.** A gauge is a snapshot ("right now 17 requests are in flight"). A short spike between two samples can be missed entirely, so for bursty events prefer a counter or histogram.

**Histograms and percentiles.** The mean (average) latency is a poor summary, because a few very slow requests hide behind many fast ones — or the reverse. Take 100 requests: 95 take 100 ms and 5 take 5,000 ms.

| Statistic | Value | What it says |
| --- | --- | --- |
| Mean | (95 × 100 + 5 × 5,000) ÷ 100 = 345 ms | Nobody actually experienced 345 ms |
| Median (p50) | 100 ms | The typical request is fine |
| p95 (nearest rank) | 100 ms | The 95th fastest request is still fast |
| p99 | 5,000 ms | One user in a hundred waits five seconds |
| Maximum | 5,000 ms | The worst case |

Here the mean suggests "slightly slow", the median says "fine", and the p99 says "one in 20 users has a terrible experience". The only way to see all of that is to keep the *distribution*. A **histogram** does this by counting how many observations fell into each bucket, for instance "at most 0.1 s", "at most 0.25 s", "at most 0.5 s". Buckets are *cumulative* in the common exposition format: the count for "at most 0.25 s" includes the faster ones.

A worked reading. Over a minute, `orders-api` recorded 1,000 requests with these cumulative bucket counts.

| Bucket (seconds, "at most") | Cumulative count |
| --- | --- |
| 0.1 | 900 |
| 0.25 | 960 |
| 0.5 | 990 |
| 1 | 998 |
| +Inf (everything) | 1,000 |

To estimate the p95, find the 950th request (95% of 1,000). It falls in the 0.25 bucket, because 900 requests are at most 0.1 s and 960 at most 0.25 s. The 950th is the 50th of the 60 requests in that bucket. Assuming they are spread evenly inside the bucket, p95 ≈ 0.1 + (50 ÷ 60) × (0.25 − 0.1) = 0.1 + 0.125 = **0.225 s**. For the p99, the 990th request is the last one in the 0.5 bucket, so p99 ≈ **0.5 s**. Two honest cautions: a percentile estimated from buckets is only as precise as the bucket boundaries, and you cannot recover which individual requests were slow. That is a job for traces and logs.

### Labels: powerful and dangerous

Labels let you slice a metric ("errors for this route only"). But every distinct combination of label values creates a separate series that must be stored and queried. A label with unbounded values, such as a user id or a raw URL like `/v1/orders/98231`, creates a new series for every user or order. That is called a **cardinality** problem and it makes monitoring systems slow and expensive. For now, remember one rule: **label values must come from a small, known set** — route *templates* (`/v1/orders/{id}`), status classes (`2xx`, `5xx`), environment, service name. The Intermediate section puts numbers on this.

## Logs from first principles

A log is a record of one event. Early programs printed free text:

```text
10:15:04 ERROR payment timeout for order 98231 after 2000ms
```

A human can read that line; a program has to guess where the order id starts. Searching "all payment timeouts for orders over a given value" becomes fragile string matching. The remedy is a **structured log**: each event is a set of named fields, usually JSON, so a machine can filter and count by field.

```json
{"ts":"2026-03-01T10:15:04Z","level":"error","service":"orders-api","msg":"payment timeout","error.code":"PAY_TIMEOUT","duration_ms":2000,"trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
```

Each field has a job: `ts` in UTC ISO 8601 orders events across machines; `level` filters noise; `service` says who produced it; `msg` is a short, *stable* sentence (variable values go in fields); `error.code` is a stable code you can count; `duration_ms` is a number, not text in a sentence; `trace_id` links the line to the whole request trace.

**What never belongs in a log.** Passwords, access tokens, API keys, `Authorization` headers, full card numbers and full request bodies that may contain personal data. A log is copied to other systems, retained for months and read by many people. If you need to correlate a user, log a pseudonymous id, not an email address.

## Traces from first principles

A request to `orders-api` is not one thing; it is a chain of smaller operations. A **span** records one operation: its name, start time, duration, status and a few attributes. A **trace** is the set of spans that belong to one request, linked in a parent–child tree. All spans of a request share one **trace id**; each span has its own **span id** and points to its **parent** span.

A trace is often drawn as a waterfall. Here is one for a slow `GET /v1/orders/{id}` (illustrative).

```text
GET /v1/orders/{id}                      0 ────────────────────────────────── 2310 ms
  authenticate                           0 ─ 12 ms
  SELECT orders (database)                 12 ─────────────────────────────── 2252 ms
  render response                                                          2252 ─ 2310 ms
```

Read it from the shape: the whole request took 2,310 ms; authentication took 12 ms; the database query took 2,240 ms (from 12 ms to 2,252 ms); rendering took 58 ms. The time is not in *your* code or authentication; it is waiting for the database. A CPU graph for `orders-api` would not show this at all, because a process waiting for the database is idle. Traces answer "where did the time go?" in a way no aggregate metric can.

To follow a request across services, the trace id must travel with it, usually in an HTTP header. This is called **context propagation**. If one service forgets to pass the header on, the trace breaks into pieces, and you see the request "disappear" at that boundary.

**Sampling.** Recording every span of every request can be very expensive, so systems often keep only some traces. That means **the absence of a trace is not proof the request did not happen**. Use metrics for "how many" and traces for "why this one".

## Frameworks as checklists: golden signals, RED and USE

When you face a service with no idea what to measure, use a checklist rather than inventing graphs.

| Framework | Focus | Signals |
| --- | --- | --- |
| Four golden signals | Any user-facing service | Latency, traffic, errors, saturation |
| RED | Request-driven services | Rate, Errors, Duration |
| USE | Resources such as CPU, disk, a connection pool | Utilisation, Saturation, Errors |

The four golden signals, applied to `orders-api`:

| Signal | Plain meaning | Example measurement | A trap |
| --- | --- | --- | --- |
| Latency | How long requests take | p50, p95 and p99 of request duration for `/v1/orders/{id}` | Failed requests are often fast; mix them with successes and the numbers look better than they are |
| Traffic | How much demand | Requests per second per route | A sudden *drop* in traffic is as alarming as a spike |
| Errors | How often requests fail | Share of responses with status 5xx, plus "successes" that are wrong (a 200 with an error body) | Counting only HTTP codes misses errors expressed in the body |
| Saturation | How full the system is | Connection pool in use ÷ pool size; queue depth; CPU throttling | Saturation usually shows up *before* errors; it is a leading indicator |

**Errors as a ratio, with an example.** In one hour `orders-api` served 10,000 requests and 37 returned 5xx. The error ratio is 37 ÷ 10,000 = 0.37%, so the success ratio is 99.63%. Always use ratios, not raw counts: 37 errors out of 10,000 is a small problem, while 37 errors out of 50 is a disaster, and the raw number cannot tell them apart.

## A basic dashboard

A dashboard is a *picture of questions you ask repeatedly*. A good beginner dashboard for one service answers, from the top of the screen to the bottom, the question "are users OK, and if not, where is the problem?"

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ orders-api · production · last 3 hours          [ deploy markers shown ▲ ] │
├────────────────────────────────────────────────────────────────────────────┤
│ ROW 1: USER IMPACT                                                         │
│  [Request rate by route]   [Error ratio % (5xx ÷ all)]   [p95 / p99 latency]│
├────────────────────────────────────────────────────────────────────────────┤
│ ROW 2: DEPENDENCIES                                                        │
│  [Database query p95]      [Payment call error ratio]    [Payment p95]     │
├────────────────────────────────────────────────────────────────────────────┤
│ ROW 3: SATURATION AND PLATFORM                                             │
│  [DB pool in use ÷ size]   [CPU throttling]   [Memory vs limit]  [Restarts]│
├────────────────────────────────────────────────────────────────────────────┤
│ ROW 4: CHANGE                                                              │
│  [Running version per instance]  [Instances ready ÷ desired]               │
└────────────────────────────────────────────────────────────────────────────┘
```

Design rules that make a dashboard useful:

- **Order by importance.** User impact first, causes below. An on-call person at 03:00 should be able to read the top row and decide "is this real?" in under ten seconds.
- **Label every axis with its unit.** Seconds or milliseconds? Ratio or percent?
- **Show deploy markers.** A vertical line at each deployment shows at a glance whether a change preceded a problem.
- **Use percentiles, not only averages.** Show p50 and p99 together; the gap is information.
- **Keep it small.** If a panel never changed a decision, remove it.

A dashboard is not an alarm. It helps a person who is already looking. To be told *when to look*, you need alerts, which the Intermediate and Professional sections develop.

## An annotated investigation

The point of all this data is to reason from evidence. Follow a short investigation and watch where each conclusion comes from. The scenario: at 10:21 a colleague writes, "orders feel slow since this morning".

**Step 1 — State the symptom in user terms and find its start.** Open the dashboard. Row 1 shows the p95 latency of `GET /v1/orders/{id}` jumping from about 0.2 s to about 2.3 s at **10:14**. The error ratio is unchanged near 0.1%. The symptom is "one route is ten times slower, with no extra errors", beginning at 10:14.

*Why this matters:* we now have a time. Everything that happened *just before* 10:14 is a candidate cause. We also know it is slowness, not failure, which rules out causes that only produce errors.

**Step 2 — Is it one route or everything?** Break the latency panel down by route. Only `/v1/orders/{id}` moved; `POST /v1/orders` is unchanged.

*Why this matters:* a platform-wide cause (CPU saturation, network trouble) would affect every route. A change confined to one route points toward code or a dependency that only this route uses.

**Step 3 — Did something change?** The deploy markers show a vertical line at 10:12: version `1.8.0` was released two minutes before the slowdown. The "running version per instance" panel shows 6 of 6 instances on `1.8.0`.

*Why this matters:* a change shortly before a symptom is a strong lead, but it is a *lead*, not a conclusion. Two things happened close together; that is correlation. We still need to see where the time goes.

**Step 4 — Where is the time spent?** Open one slow trace (illustrative).

```text
GET /v1/orders/{id}   total 2310 ms   status 200   service.version 1.8.0
  authenticate         12 ms
  SELECT orders        2240 ms   db.system=postgresql   db.operation=SELECT
  render response      58 ms
```

The database span accounts for 2,240 of 2,310 ms, about 97% of the request.

*Why this matters:* now we know the time is spent waiting on the database, not in authentication or rendering, and not in `orders-api`'s own CPU. That is also why the CPU graph for the service looked normal.

**Step 5 — Check the log for the same request.** Search the logs by the trace id from the trace.

```json
{"ts":"2026-03-01T10:16:41Z","level":"warn","service":"orders-api","version":"1.8.0","msg":"slow query","db.operation":"SELECT","duration_ms":2240,"trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
```

*Why this matters:* the log agrees with the trace, which strengthens the claim. Two independent signals telling the same story are more convincing than one.

**Step 6 — Form a hypothesis and test it, do not announce it.** The hypothesis: *version 1.8.0 changed the query for this route in a way that makes it slow.* What would **disprove** it? A slow trace from an instance still on `1.7.x`. All six instances are on `1.8.0`, so we cannot test that directly. The evidence is consistent with the hypothesis but cannot yet exclude a database problem that began at the same moment.

**Step 7 — Take a reversible action and confirm.** Rolling back to `1.7.4` is quick and reversible. After the rollback finishes at 10:31, the p95 latency of the route falls back to about 0.2 s within three minutes. The symptom disappeared when the change was reverted, which is strong evidence that `1.8.0` caused it.

**Step 8 — Record what you know and what you do not.** Write down symptom and times, the telemetry, the action, the result and the follow-up ("investigate the query introduced in 1.8.0"). Add what the telemetry *could not* tell you ("no per-query timing inside the database").

The habits: start from user impact, narrow by dimension, look for change, look at a concrete example, corroborate with a second signal, ask what would disprove the theory, act reversibly, confirm with the measurement you started from, and write it down.

## Six questions a responder must answer

1. Are users failing the critical path right now?
2. When did it start?
3. Is it one route or everything?
4. Is the time spent in this service or in a dependency?
5. Did we ship something recently?
6. Is the telemetry itself missing or lying?

Question 6 is easy to forget: a flat line can mean "nothing is happening" or "the data stopped arriving".

## What can go wrong: common mistakes and how they look

| Mistake | How it looks | Better practice |
| --- | --- | --- |
| Secrets in logs | A token visible in a search result | Redact at source; never log headers or bodies wholesale |
| User ids as metric labels | Slow queries, large bills | Route templates and status classes only |
| Trusting a flat line | "No errors" because no data arrived | Check that the series is still being updated |

## Knowledge consolidation

- **Logs** describe events, **metrics** summarise behaviour over time, **traces** follow one request; each answers a different question at a different cost.
- **Monitoring** checks known conditions; **observability** lets you investigate unknown ones. Neither replaces resilient design.
- Use the **golden signals** (or RED/USE) as checklists, and always use **ratios** for errors.
- Read a **counter** as a rate, a **gauge** as a current value, a **histogram** as percentiles; the mean hides the slow tail.
- **Label** values must come from a small, known set.
- A **structured log** has a timestamp, level, service, stable message, named fields and a trace id, and never contains secrets.
- Investigate from **symptom and start time** to **scope**, **change**, **example** and **corroboration**; act reversibly; record uncertainty.

## Exercises

**Exercise 1 — Counter to rate.** A counter `http_requests_total` reads 482,000 at 14:00:00 and 485,600 at 14:10:00. Compute the request rate in requests per second. Then suppose the process restarts at 14:10:00 and at 14:10:30 the counter reads 600. Explain what rate a reasonable system would report for that interval and why a naive subtraction would be wrong.

**Exercise 2 — The mean lies.** A service handled 200 requests: 190 took 80 ms and 10 took 3,000 ms. Compute the mean, the median and the p99 (nearest rank). Write one sentence for an engineering manager saying whether the service "is fast".

**Exercise 3 — Find the blind spots.** For a service you know (or `orders-api`), write the six questions a responder must answer and name the smallest signal that answers each. Mark the ones that have no signal today. Those are your blind spots.

**Exercise 4 — Read the waterfall.** A trace shows `POST /v1/orders` total 1,840 ms, with spans: validate 15 ms; `SELECT customer` 40 ms; payment call 1,700 ms; `INSERT order` 60 ms. Compute the time not covered by child spans and the share taken by the payment call. What would you check next?

**Solution notes.**

*Exercise 1.* The increase is 3,600 over 600 s, so 6 requests per second. After the restart the counter fell from 485,600 to a small number; a naive subtraction (600 − 485,600) gives a large negative number, which is meaningless. A counter-aware rate treats a decrease as a reset to zero and counts the new value from zero, so over the 30 seconds after the restart it would report roughly 600 ÷ 30 = 20 requests per second (exact handling depends on the sample times). The point is that rates handle resets; raw values do not.

*Exercise 2.* Mean = (190 × 80 + 10 × 3,000) ÷ 200 = (15,200 + 30,000) ÷ 200 = 226 ms. Median = 80 ms. p99 nearest rank is the 198th value of 200, which is 3,000 ms (the slowest 10 requests are 5% of traffic). Suggested sentence: "Typically yes, 80 ms, but one request in twenty takes three seconds, so users with that experience would not call it fast." Marks go for naming the share of affected users, not for a particular wording.

*Exercise 3.* There is no single right answer. A strong answer names a *concrete* signal (for example "5xx ratio by route, 1-minute resolution" for question 1; "deploy markers from the pipeline" for question 5; "`up` metric and last-sample age" for question 6) and honestly lists the gaps. Teams usually find question 6 and question 4 unanswered.

*Exercise 4.* The children sum to 15 + 40 + 1,700 + 60 = 1,815 ms, leaving 25 ms in the handler itself. The payment call is 1,700 ÷ 1,840 ≈ 92% of the request. Next, check the payment provider's duration and error metrics over the same period, whether the slowness affects all requests or only some (by region, provider endpoint), and whether the call's timeout is too long for a user-facing request.

---
