# T-AIE-05-B — Beginner Foundations

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-b"></a>
#### T-AIE-05-B — Beginner Foundations

## Why this matters

Building an assistant that answers a question on your laptop is the easy half of the job. The hard half starts the day other people depend on it. A prompt gets edited and answers change. The provider updates a model and the tone shifts. A bill arrives that is ten times what anyone expected. A user finds a way to make the feature say something it should not. In each case the first questions are the same: *what exactly is running, what is it doing right now, and how do I stop it?*

LLMOps is the discipline of being able to answer those questions. For most teams it does not mean training models. It means operating an application whose behaviour depends on a prompt, a tool policy, a retrieval index, some configuration and a model identifier, and whose cost and quality are visible only if you measure them.

This section teaches the beginner foundations: the path a request takes, what to version, how to read the three signals that matter (latency, cost and quality), how to switch a feature off, and what to do when the model call fails. It assumes you can run a small web service and read a JSON response. It does not depend on any other course material, and every example is illustrative: names, numbers and prices are made up to show the shape of the idea.

## First principles: an LLM feature is an application with a moving part

A traditional service behaves the same way tomorrow as today unless you deploy new code. An LLM feature has extra inputs that can change its behaviour without a code deploy:

| Input | Who can change it | Changes behaviour without a code deploy? |
| --- | --- | --- |
| Application code | Developers, through a release | No (a release is visible) |
| Prompt text | Developers, product, sometimes editors | Yes, if stored in a file or config |
| Tool allow-list | Developers, security | Yes, if stored in config |
| Retrieval corpus or index | Content owners, a pipeline | Yes |
| Model behind a name | The provider | Yes, if you use a floating alias |
| Generation settings (temperature, output limit) | Developers | Yes, if stored in config |

Operating the feature means treating *every* row as something that has an identity, a change record and a way back. If you remember one sentence from this topic, make it this one: **an LLM feature changes whenever any of its inputs changes, so every input needs a version.**

## The request path: request to model to response

Follow one request from start to finish. Each hop is a place where time passes, money may be spent, and something can fail.

```text
client
  -> application endpoint            (is the feature enabled? who is asking?)
  -> input checks                    (size, rate, obvious abuse)
  -> context assembly                (prompt template + retrieved text + user question)
  -> model call                      (hosted API or self-hosted server)
  -> output checks                   (format, safety, citations)
  -> response to the client
  -> telemetry written               (latency, tokens, outcome, versions)
```

| Hop | What can go wrong | What operating it means |
| --- | --- | --- |
| Endpoint | Feature is meant to be off but still answers | A runtime flag checked first |
| Input checks | A huge input costs a lot, or a flood of requests arrives | Size and rate limits, with clear error codes |
| Context assembly | Wrong prompt version loaded; retrieval returns nothing | Version recorded; empty-context behaviour decided |
| Model call | Slow, failing, rate-limited by the provider | Timeout, a small retry limit, a fallback message |
| Output checks | Malformed or unsafe answer is returned | Validation before the user sees anything |
| Telemetry | Nothing recorded, so nothing can be diagnosed | One structured line per request |

Notice that only one hop is the model. Most operational problems live in the other hops: a missing flag, a missing timeout, a missing log line. That is good news, because those are ordinary engineering problems.

## What to version

One small file can record exactly what ran:

```text
bundle_version: 1.0.0
prompt_version: assistant-prompt-2026-03
tools_policy_version: tools-allow-v2
dataset_version: eval-set-2026-03
config_version: generation-config-v4
model_id: example-model-2026-01
git_sha: <commit>
```

Call this a **version bundle**: the set of identities that ran together. Four of the entries deserve a closer look because beginners tend to forget them.

- **Model id.** Use a dated or versioned identifier, not a floating alias such as `latest`. An alias lets the provider change behaviour under you.
- **Prompt version.** Prompts are code that happens to be written in English. Give them a version and keep them in source control, not only in an admin screen.
- **Dataset version.** The evaluation dataset (the set of example questions and expected behaviours you test against) changes too. If you cannot say which dataset a test result came from, the result is hard to trust.
- **Config version.** Temperature, output-token limit, retrieval depth and timeouts all change behaviour. Group them and number them.

Recording a version is not the same as deploying it. Changing the file does not roll back code. Pin metadata *and* an artefact identity (a commit or an image digest).

## Worked example: three changes, three different identities

An assistant's behaviour can change without any application code changing:

| What changed | Where it lives | Was the code redeployed? | How to detect it |
| --- | --- | --- | --- |
| Prompt text edited | Prompt file or config | Perhaps not | `prompt_version` in the version file and the health response |
| Tool allow-list widened | Tools policy | Perhaps not | `tools_policy_version` |
| Provider updates the model behind an alias | Provider side | No | Pin a dated `model_id` rather than a floating alias |
| Library upgraded | Application image | Yes | `git_sha` or image digest |

This is why "which version is running?" must be answerable from one place, and why rollback needs *all* of those identities, not just the version file.

## The health endpoint reports AI state

```json
{"status": "ok", "ai": {"enabled": true, "bundle_version": "1.0.0", "model_id": "example-model-2026-01"}}
```

If the AI is disabled the core service stays healthy; the assistant is an add-on. The `status` field describes the core service and `ai.enabled` describes the add-on. Keep those two separate, otherwise turning the assistant off makes the whole service look broken.

A version file the application reads at start-up:

```python
import json, os

def load_version(path="version.json"):
    with open(path) as f:
        return json.load(f)

def health():
    enabled = os.environ.get("ASSISTANT_ENABLED", "true").lower() == "true"
    v = load_version()
    return {"status": "ok",
            "ai": {"enabled": enabled,
                   "bundle_version": v["bundle_version"],
                   "model_id": v["model_id"]}}
```

The health check must not call the model on every probe. A probe runs every few seconds; model calls cost money and fail when the provider is down, which would make your whole service look unhealthy for a reason that has nothing to do with it.

## The stop button

A single flag disables the feature without redeploying everything:

```bash
export ASSISTANT_ENABLED=false
./scripts/restart-assistant.sh
curl -s localhost:8001/health      # shows "enabled": false
```

When the flag is off, the assistant endpoint should return immediately, without calling the model, with a stable status code and message such as `503 {"error": "assistant_disabled"}`. Check that no model call is made and no cost accrues. A kill switch that still spends money is not a kill switch.

## Introduction to monitoring: latency, cost and quality

Three questions describe the health of an LLM feature from the point of view of the people running it. You will meet each in more depth at later levels; here you only need to know what each one is and where to read it.

| Question | Signal | Where it comes from |
| --- | --- | --- |
| Is it fast enough? | Latency: time from request to response, in milliseconds | Timer around the endpoint; timer around the model call |
| Is it affordable? | Cost: tokens in and out, multiplied by a price | Token counts returned by the provider |
| Is it any good? | Quality: did it answer, refuse, cite, or fail? | Outcome category, plus sampled review |

### Latency

Latency is not one number. Users notice the total, but you diagnose with the parts. A typical model-backed request spends most of its time waiting for the model, so measure the model call separately from everything else.

```text
total latency    = 1,850 ms
  input checks   =     5 ms
  retrieval      =   120 ms
  model call     = 1,690 ms
  output checks  =    35 ms
```

If total latency rises and only `model call` rises, the problem is the provider or the prompt length. If `retrieval` rises, look at your search index. Without the breakdown you can only guess.

### Cost

Models are billed in **tokens**: small pieces of text, roughly a few characters each. You pay for tokens in (the prompt) and tokens out (the answer), usually at different prices. Illustrative arithmetic, with made-up prices:

```text
price in  = $1.00 per million tokens
price out = $4.00 per million tokens
one request: 1,500 tokens in, 300 tokens out
cost = 1,500/1,000,000 * 1.00  +  300/1,000,000 * 4.00
     = 0.0015 + 0.0012
     = $0.0027  (about a quarter of a cent)
```

A quarter of a cent sounds like nothing. At 200,000 requests a month it is $540. If a bug doubles the prompt length, that bill rises sharply and nobody notices until the invoice. This is why tokens are recorded on every request.

### Quality

Quality is hardest to measure because there is no single "error rate". Start with a simple outcome category on every request:

| Outcome | Meaning |
| --- | --- |
| `answered` | The model produced an answer that passed output checks |
| `refused` | The feature declined (out of scope, or disabled) |
| `no_match` | Nothing relevant was found, so it said so |
| `error` | A failure on our side or the provider's |
| `limited` | The request was blocked by a rate or size limit |

The mix of these outcomes is a quality signal. If `no_match` suddenly doubles after a content update, retrieval probably broke. If `refused` drops to zero, a safety check may have been removed. You do not need an expert to see those shifts; you need the counts.

## Serving, at a beginner level

A model call goes either to a **hosted API** (a provider runs the model and you send requests over the internet) or to a **self-hosted server** (you run the model on your own machines). For a beginner, assume hosted unless told otherwise; it has far fewer moving parts. Either way, operating it means three decisions, made before the first incident:

1. **Timeout.** How long will you wait before giving up? A request with no timeout can hang for minutes and tie up your service.
2. **Retry limit.** How many times will you try again after a failure? Retrying forever can multiply cost and load. Two retries with a short pause is a common starting point.
3. **Failure response.** What does the user see when the model call fails? A clear "assistant unavailable" message is far better than a spinner that never ends.

```python
import time

def call_model_safely(prompt, max_attempts=2, timeout_s=20):
    for attempt in range(1, max_attempts + 1):
        try:
            return provider_complete(prompt, timeout=timeout_s)   # your client call
        except (TimeoutError, ConnectionError):
            if attempt == max_attempts:
                return None                                        # caller shows the fallback
            time.sleep(0.5 * attempt)                              # short pause, grows each time
    return None
```

The function returns `None` instead of raising, so the endpoint can decide what to show. Keep that decision in one place.

## What a provider failure looks like

Provider failure is not rare, so plan for it. The common shapes:

| Symptom | Likely cause | First reaction |
| --- | --- | --- |
| Timeouts | Provider slow or overloaded | Return the fallback message; check the provider status page |
| Errors with a "rate limit" meaning | You sent more than your quota allows | Slow down; check your own limits |
| Errors about an unknown model | A model id was retired | Check the provider's notices; use your pinned replacement |
| Malformed or empty answers | Prompt or model change | Compare with the last good version bundle |
| Sudden refusals | Provider-side policy change | Test a known question; capture the response |

You will practise fuller triage later. At this level the goal is to know the fallback exists and the first place to look.

## Vocabulary in context

| Term | Meaning |
| --- | --- |
| Model id | The exact model identifier sent to the provider; prefer a dated or versioned id. |
| Version bundle | The recorded set of prompt, tool policy, dataset, config, model and code identities that ran together. |
| Feature flag | A runtime switch that turns behaviour on or off without a new build. |
| Refusal message | The fixed text returned when the feature is off or a request is out of scope. |
| Token | The unit a model reads and writes; usage and cost are measured in tokens. |
| Latency | The time a request takes, usually measured in milliseconds, often split by stage. |
| Fail-closed | When uncertain or broken, the feature turns off rather than doing something unsafe. |
| Fallback | What the feature does when the preferred path fails, such as a simple message. |
| Telemetry | The structured record written for each request so that you can diagnose it later. |
| Evaluation dataset | A fixed set of example questions and expected behaviours used to check quality. |

## One telemetry line per request

The simplest useful monitoring is one structured line per request. It must not contain the user's text or any secret.

```json
{"ts": "2026-03-02T09:14:07Z", "outcome": "answered", "latency_ms": 1850,
 "model_ms": 1690, "tokens_in": 1500, "tokens_out": 300,
 "bundle_version": "1.0.0", "model_id": "example-model-2026-01", "enabled": true}
```

With only these fields you can already answer: how many requests, how fast, how costly, which version, and what happened. Notice what is missing on purpose: the question text, the answer text, any key. Hashes, sizes and categories are safer than content.

## Common mistakes

- Editing the version file and believing the system has rolled back.
- Using a floating model alias such as `latest`, so behaviour changes without a deploy.
- Putting the API key in the version file or the health response.
- Making the flag a code change instead of a runtime setting, so turning it off needs a release.
- Having the health check call the model on every probe, which costs money and makes the whole service look unhealthy when the provider is down.
- Calling the model with no timeout, so one slow provider call ties up a worker for minutes.
- Logging full prompts "just for now" and never removing it.
- Measuring only total latency, so the slow part cannot be found.
- Having no outcome category, so a quality problem looks the same as normal traffic.

## Evidence for the drill

Keep the health response before and after, the refusal response, and the command output that proves which artefact (commit or digest) was running. Two outputs with timestamps beat any description. A drill that is not recorded did not happen.

## Knowledge consolidation

- An LLM feature is an application with extra inputs (prompt, tool policy, corpus, config, model) that can change behaviour without a code deploy.
- The request path has several hops; most operational problems live in the hops around the model, not in the model.
- Version everything: model, prompt, dataset, config, tools policy and code. Record them in one bundle and report it in the health response.
- Recording a version does not roll anything back; pin an artefact identity too.
- The three signals to learn first are latency (split by stage), cost (tokens times price) and quality (an outcome mix).
- Every model call needs a timeout, a retry limit and a defined failure response.
- A feature flag is the stop button. When off, no model call may be made.
- The core service stays healthy when the assistant is off.
- Log hashes, sizes and categories; keep content and secrets out of routine logs.

## Exercises

**Exercise 1 — Version and health.** Add a version file with the bundle fields above and a health response that reports `bundle_version` and `model_id`. Start the service and call the endpoint. Save the output with a timestamp.

**Exercise 2 — Flip the flag.** Set `ASSISTANT_ENABLED=false`, restart, and call both the health endpoint and the assistant endpoint. Confirm health reports `enabled: false` while `status` stays `ok`, and the assistant endpoint refuses with a clear message.

**Exercise 3 — Prove no model call.** With the flag off, send ten requests. Show from a counter, a log or a stub provider that the number of model calls is zero.

**Exercise 4 — Token arithmetic.** Using the made-up prices above, compute the cost of a request with 3,000 tokens in and 500 out. Then compute the monthly cost at 50,000 requests. Finally compute what happens to the monthly cost if the prompt grows to 6,000 tokens.

**Exercise 5 — Provider down.** Point the service at an address that does not answer. Show that it respects the timeout, retries no more than the limit, and returns the "assistant unavailable" message while `/health` for the core service stays `ok`.

**Exercise 6 — Telemetry line.** Make the service write one JSON line per request with the fields above. Send one answered request, one refused request and one limited request, and show the three lines.

**Solution notes.**

*Exercise 1.* Illustrative expectation: the response contains the bundle version and model id from the file. If it does not, check that the file is read at start-up and that the path is correct. Make sure the file contains no key.

*Exercise 2.* After the restart, `ai.enabled` is false. The refusal should be fast, because no model call is made. If the endpoint still answers, the flag is probably read at the wrong place or the old process is still running; confirm which process is listening.

*Exercise 3.* The count should be zero. If you cannot measure it, that is itself the finding: add a counter around the model call before you trust the kill switch.

*Exercise 4.* 3,000 in and 500 out gives 0.003 + 0.002 = $0.005 per request, so $250 a month at 50,000 requests. Doubling the prompt to 6,000 tokens gives 0.006 + 0.002 = $0.008 per request, or $400 a month: a 60% rise from changing only the input. This is why prompt length is a cost control.

*Exercise 5.* With a 20-second timeout and two attempts, the worst case is a little over 40 seconds before the fallback appears. That may be too long for users, so notice whether you would lower the timeout. The point is to choose the numbers deliberately.

*Exercise 6.* The three lines should have different `outcome` values and none should contain the question text. If a line contains content, remove it before moving on.
