# T-AIE-05-B — Beginner Foundations

*Chapter: [T-AIE-05 — LLMOps, Deployment and Monitoring](README.md) · Part 3 — AI Engineering*

<a id="t-aie-05-b"></a>
#### T-AIE-05-B — Beginner Foundations

**What LLMOps is.** LLMOps means operating an LLM *feature*: version it, serve it, observe it, limit it and be able to stop it. For most teams it is not training models; it is running an application whose behaviour depends on a prompt, a tool policy and a model identifier.

| Concern | Classic model operations (training pipelines) | Feature operations (this topic) |
| --- | --- | --- |
| Artefact | Weights, feature stores | Prompt, tool policy, model id, application code |
| Deploy | Training and serving infrastructure | Application deployment or feature flag |
| Change control | Dataset and model lineage | Version pin, changelog, one-action rollback |
| Risk | Silent prediction drift | Cost blow-ups, unsafe tools, stale prompts |
| Stop button | Undeploy the model | A flag that disables the feature |

If your plan starts with "fine-tune a model", check whether you are solving the right problem. Operate the feature you already built first.

**What to version.** One small file can record exactly what ran:

```text
bundle_version: 1.0.0
prompt_version: assistant-prompt-2026-03
tools_policy_version: tools-allow-v2
model_id: example-model-2026-01
git_sha: <commit>
```

Recording a version is not the same as deploying it. Changing the file does not roll back code. Pin metadata *and* an artefact identity (commit or image digest).

**The health endpoint reports AI state.**

```json
{"status": "ok", "ai": {"enabled": true, "bundle_version": "1.0.0", "model_id": "example-model-2026-01"}}
```

If the AI is disabled the core service stays healthy; the assistant is an add-on.

**The stop button.** A single flag disables the feature without redeploying everything:

```bash
export ASSISTANT_ENABLED=false
./scripts/restart-assistant.sh
curl -s localhost:8001/health      # shows "enabled": false
```

**Worked example: three changes, three different identities.** An assistant's behaviour can change without any application code changing:

| What changed | Where it lives | Was the code redeployed? | How to detect it |
| --- | --- | --- | --- |
| Prompt text edited | Prompt file or config | Perhaps not | `prompt_version` in the version file and the health response |
| Tool allow-list widened | Tools policy | Perhaps not | `tools_policy_version` |
| Provider updates the model behind an alias | Provider side | No | Pin a dated `model_id` rather than a floating alias |
| Library upgraded | Application image | Yes | `git_sha` or image digest |

This is why "which version is running?" must be answerable from one place, and why rollback needs *all* of those identities, not just the version file.

**Serving, at a beginner level.** A request travels: client, application endpoint, input checks, prompt assembly, model call (to a hosted API or a self-hosted server), output checks, response. Each hop adds latency and can fail. Operating the feature means setting timeouts and a retry limit on the model call and deciding what to return when it fails (for example a clear "assistant unavailable" message) instead of hanging.

**Vocabulary**

| Term | Meaning |
| --- | --- |
| Model id | The exact model identifier sent to the provider; prefer a dated or versioned id. |
| Version bundle | The recorded set of prompt, tool policy, model and code identities that ran together. |
| Feature flag | A runtime switch that turns behaviour on or off without a new build. |
| Refusal message | The fixed text returned when the feature is off or a request is out of scope. |
| Token | The unit a model reads and writes; usage and cost are measured in tokens. |
| Fail-closed | When uncertain or broken, the feature turns off rather than doing something unsafe. |

**A version file the application reads at start-up**

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

The `status` field describes the core service and stays `ok` when the assistant is off. Only `ai.enabled` changes.

**Refusal when disabled.** When the flag is off, the assistant endpoint should return immediately, without calling the model, with a stable status code and message such as `503 {"error": "assistant_disabled"}`. Check that no model call is made and no cost accrues.

**Common mistakes**

- Editing the version file and believing the system has rolled back.
- Using a floating model alias such as `latest`, so behaviour changes without a deploy.
- Putting the API key in the version file or the health response.
- Making the flag a code change instead of a runtime setting, so turning it off needs a release.
- Having the health check call the model on every probe, which costs money and makes the whole service look unhealthy when the provider is down.

**Evidence for the drill.** Keep the health response before and after, the refusal response, and the command output that proves which artefact (commit or digest) was running. Two outputs with timestamps beat any description.

**Exercise.** Add a version file and a health response that reports it. Flip the flag, restart, confirm the endpoint reports disabled and requests are refused with a clear message.
