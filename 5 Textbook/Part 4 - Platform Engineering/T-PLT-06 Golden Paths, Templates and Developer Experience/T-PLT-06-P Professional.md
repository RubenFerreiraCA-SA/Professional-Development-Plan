# T-PLT-06-P — Professional Engineering

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-p"></a>
#### T-PLT-06-P — Professional Engineering

**Discoverability: if it cannot be found, it does not exist.** Developers should answer without asking a person: which services exist, who owns this one, where is its runbook, is it healthy, how do I make a new one? A *catalogue* answers these. Make it data first — files in Git — and an interface second.

```yaml
# catalog/orders-api.yaml (portal-compatible shape)
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: orders-api
  description: Order lookup API
  annotations:
    runbook: https://example.com/runbooks/orders-api
spec:
  type: service
  lifecycle: production
  owner: team-orders
```

Generate a human-readable index in CI and fail the build when it is stale (`git diff --exit-code docs/CATALOG.md`). Check catalogue freshness and owners automatically.

**Documentation as a product.** Organise by reader's need (the Diátaxis model): *tutorial* (start here → first service), *how-to* (promote, roll back, read status), *reference* (contract, quotas, allowed environments) and *explanation* (why the platform works this way). Quality rules: every command is copy-pasteable and states expected output with no assumed directory, cluster context or account; errors are documented next to the step that causes them; accessibility basics (descriptive headings and link text, alternative text, no meaning conveyed by colour alone, text equivalents of diagrams — noting that this is not an accessibility audit); and docs are tested with link checks in CI and with real trials.

**Operational status a developer can read.** A single status command that gives a verdict:

```text
$ platform-status orders-api
SERVICE   orders-api   owner: team-orders
ENV       staging      digest: sha256:3f1c...e9a0   source commit: 9d2f...
STATUS    HEALTHY      replicas: 2/2 ready   last reconcile: 40s ago
RUNBOOK   https://example.com/runbooks/orders-api
```

It must not lie: an unpromoted service with zero replicas is `UNKNOWN` or `DOWN`, not `HEALTHY`. Document what it does *not* check.

**Investigability: the developer's failure path.** The on-call developer did not build the platform. Within minutes they must learn *what is wrong* and *the first safe action*. The platform supplies the status command, per-service runbooks, linked telemetry and safe first actions (re-promote a previous digest, never edit live objects).

**Runbook quality bar**

| Criterion | Detail |
| --- | --- |
| Starts with a command that produces a verdict | The status command |
| Symptoms in the user's words | Not internal jargon |
| First safe action is reversible | Re-promote a prior digest |
| States when to stop and escalate | A clear boundary |

**Portal options — decide with evidence**

| Option | Strength | Cost | Use when |
| --- | --- | --- | --- |
| Repository docs, CLI and generated catalogue | Cheap, versioned, testable | Less discoverable; no UI | First iteration; small platform team |
| A portal framework | Rich catalogue, templates, plugins | Heavy build and upgrade burden | Many teams; dedicated capacity |
| Hosted portal products | Fast start | Cost, lock-in | A UI is needed quickly; vendor review done |

The decision test: *would a portal remove a stuck point you observed in a trial?* No trial yet means you do not know what to build.

**Measuring the platform — protocol defined before the trial**

| Item | Definition |
| --- | --- |
| Start | Participant is handed the task card and the docs link |
| Stop | Acceptance check passes, the participant gives up, or the time box expires |
| Documented waits | CI runtime, review wait — recorded separately and subtracted |
| Stuck point | Paused beyond two minutes, backtracked or searched without progress; record time, goal, document being read |
| Intervention | The observer says or shows anything not in the written docs |
| Independent completion time | Stop − start − documented waits, counted only with zero undocumented interventions |

Intervention classes: **I0** observer silent (pass-eligible); **I1** observer repeats information verbatim in the docs (a findability defect, still pass-eligible); **I2** observer gives information not in the docs (trial fails); **I3** observer touches the keyboard (trial fails). Answering "just once" is an I2.

**Operating the platform as a product**

| Practice | Minimum |
| --- | --- |
| Support model | `platform-support` and `platform-gap` labels, a stated response target; convert repeated questions into docs or fixes within the week |
| Versioning | Logic in reusable workflows and base manifests so fixes propagate by reference; a version stamp on generated services; deprecation notes and migration guides for breaking changes |
| Roadmap | Ranked by how many developers hit it, how badly and how often, using trial findings and support categories |
| Platform reliability | Template tests, link checks, catalogue freshness, periodic docs-only dry runs |

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Reduce cognitive load | One complete, supported path | A menu of ten equal options |
| Keep templates alive | CI generates and tests them | Untested scaffolding |
| Make services findable | Catalogue as files, generated index, freshness check | A wiki nobody updates |
| Prove usability | A trial with an independent participant | A demo by the author |
| Handle deviation | Record, expire, treat as a product signal | Silent forks of the path |
