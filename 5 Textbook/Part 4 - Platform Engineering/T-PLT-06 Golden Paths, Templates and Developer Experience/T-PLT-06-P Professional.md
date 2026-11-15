# T-PLT-06-P — Professional Engineering

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-p"></a>
#### T-PLT-06-P — Professional Engineering

## Why this matters

At Professional level the golden path is operated for many teams at once, by a platform team that is itself accountable. Four pressures arrive together. Self-service must be *secure*: a developer who can create a namespace by themselves must not be able to create someone else's. Discovery must be *reliable*: ownership data that is wrong sends incidents to the wrong team. The path must be *maintainable*: a hundred generated services will outlive three versions of the template. And the whole thing must be *measured honestly*: "developers like it" is not evidence.

This section treats the golden path as a product with an API, an identity model, an audit trail and a service level. It assumes the Beginner and Intermediate material: path specifications, templates and shared workflows, offline and cluster testing, guardrail messages, deviation records and the feedback loop. The examples use a generic catalogue, a command-line tool and a portal; the ideas apply to any stack.

## First principles: self-service is delegated authority

Self-service means a developer causes something to happen without a platform engineer in the loop. Every self-service action therefore *delegates authority*. Treat it as such and four questions follow naturally:

1. **Who is asking?** (Identity: the developer, not a shared account.)
2. **What may they ask for?** (Authorisation: scoped to teams and services they own.)
3. **Is the request acceptable?** (Policy: names, sizes, environments, images.)
4. **What happened?** (Audit: a durable record of who asked, what changed, what the outcome was.)

```text
 developer ──▶ interface (CLI / portal / API) ──▶ identity check
                                                     │
                                          authorisation: owns this team?
                                                     │
                                             policy: is the request valid?
                                                     │
                                  change recorded as a pull request or API call
                                                     │
                       reconciler applies (with its own, narrower, credentials)
                                                     │
                                          audit record + status visible
```

Notice the last two steps. The developer never holds the credentials that change the cluster. A *reconciler* or *platform service* holds them, and it acts only on requests that passed the earlier steps. This is what lets self-service be both fast and safe.

## Secure self-service: designing the request path

### Prefer requests as data

The safest, most auditable form of self-service is a *change to a file in Git*, reviewed and applied by a reconciler. A tenant request, for example:

```yaml
# tenants/team-orders/tenant.yaml
apiVersion: platform.example.com/v1
kind: Tenant
metadata:
  name: team-orders
spec:
  owners: [group:team-orders]
  environments: [staging, production]
  quota:
    staging:    { pods: 20, cpu: "8",  memory: 16Gi }
    production: { pods: 40, cpu: "16", memory: 32Gi }
  dataClass: internal
```

Why a file in Git rather than a form that calls an API directly? You get review, diff, history, revert and a signed commit for free. The cost is latency (a reviewer) and the need to explain the file format. Where a form is better for the user, let the form *produce* this file as a pull request.

### Classify actions by risk

Not every action deserves the same friction. Match review to blast radius:

| Action | Blast radius | Typical control |
| --- | --- | --- |
| Create a service from a template in your own team's space | Low | Automated validation only |
| Promote a previously released digest to staging | Low | Automated policy; no human |
| Promote to production | Medium | Automated policy plus a required reviewer, or an approved pipeline |
| Raise a quota | Medium | Platform reviewer, response time documented |
| Create a new team namespace | Medium | Platform reviewer |
| Change a shared base manifest or workflow | High | Platform review, canary rollout |
| Grant cross-team access | High | Both owning teams approve |

A review that never rejects anything is theatre, and a review on everything teaches developers to wait. Put human gates only where a human adds judgement that automation cannot, and *measure how often they say no*.

### Guardrails by layer

Enforce the same rule at several layers, so that each layer gives the right feedback at the right time:

| Layer | Example | Developer feedback | Failure mode if this is the only layer |
| --- | --- | --- | --- |
| Scaffold | Name pattern, owner exists | Immediate, in the terminal | Bypassed by editing files |
| Pull-request check | Policy against rendered manifests | In the pull request | Bypassed by direct cluster changes |
| Admission policy | Digest-only images, no privileged pods | At apply time | Late, cryptic if messages are poor |
| Runtime detection | Drift between Git and cluster | In status, alerts | Reactive |

The pull-request check and the admission policy should share one policy source to avoid disagreeing. A rule that passes the check and fails admission is a defect in the platform, not the developer.

```text
policy/
  image-by-digest.rego       # shared source
  no-privileged.rego
  required-labels.rego
  tests/                     # table tests: input, expected allow/deny, expected message
```

Policy needs tests like any code:

```text
test: tag-latest-denied
input:  container image "orders-api:latest"
expect: deny, message contains "image-by-digest" and "docs/how-to/promote.md"
```

## Identity and ownership

### Who is a developer, to the platform?

Self-service falls apart when identity is vague. Decide the model deliberately:

| Question | Recommended answer | Why |
| --- | --- | --- |
| Authentication | The organisation's single sign-on; short-lived credentials | Joiners and leavers handled in one place |
| Groups | Team membership comes from the identity provider, not from files in repositories | One source of truth; leaver removal is automatic |
| Machine identity | Per-pipeline or per-service identity with narrow scope; no shared long-lived tokens | A leaked token has a small blast radius |
| Platform actions | Run as the reconciler's identity, with the *requester's* identity recorded | Authority is narrow; accountability is personal |

### Ownership is data and it rots

An owner field is the most valuable and the most perishable piece of metadata in the catalogue. Teams reorganise, people leave, services get inherited. Make ownership *validated*, not just recorded:

| Check | Frequency | Action on failure |
| --- | --- | --- |
| Owner group exists in the identity provider | On every catalogue change and nightly | Fail the pull request; flag in a report |
| Owner group has at least two active members | Weekly | Notify the group lead |
| Owner has acknowledged ownership in the last 180 days | Quarterly | Ask for confirmation; mark `ownership-unconfirmed` |
| Service has an on-call route | On every change | Block promotion to production without it |
| Unowned service | Daily | Escalate to the nearest owning organisation; start the retirement discussion |

```yaml
# catalog/orders-api.yaml
metadata:
  name: orders-api
  annotations:
    runbook: https://example.com/runbooks/orders-api
    oncall: pagerduty://orders
    ownership/confirmed: "2026-09-30"
spec:
  type: service
  lifecycle: production
  owner: team-orders
  system: checkout
```

The test of good ownership data: *at 03:00, during an incident, can someone answer "who do we page for this service" in under a minute without asking in a chat channel?*

## Discoverability: if it cannot be found, it does not exist

Developers should answer without asking a person: which services exist, who owns this one, where is its runbook, is it healthy, how do I make a new one? A *catalogue* answers these. Make it data first — files in Git — and an interface second.

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

```bash
# regenerate and verify the index
platform/bin/gen-catalog-index > docs/CATALOG.md
git diff --exit-code docs/CATALOG.md || {
  echo "docs/CATALOG.md is stale. Run platform/bin/gen-catalog-index and commit." >&2
  exit 1
}
```

## APIs and the portal

A portal is a *front end* on the platform's capabilities. If those capabilities are only reachable through the portal, the portal is a single point of failure and a barrier to automation. Design the platform as an API first.

### An API-first stance

| Interface | Used by | Why it matters |
| --- | --- | --- |
| Git (files and pull requests) | Everyone, ultimately | The record of truth, reviewable and revertible |
| Command-line tool | Developers and scripts | Fast, scriptable, works in terminals and CI |
| HTTP API | Portal, bots, other tooling | One contract that the portal and automation share |
| Portal | Discovery and low-frequency tasks | Great for finding things and onboarding; poor for repeated work |

A service-creation request through the HTTP API, showing what a stable contract looks like:

```text
POST /v1/services
Authorization: Bearer <user token>
Idempotency-Key: 4f2c9d0e-...

{ "name": "orders-api", "template": "http-python", "version": 3,
  "owner": "team-orders", "parameters": { "datastore": "none" } }

202 Accepted
{ "id": "req_7f31", "status": "pending",
  "links": { "status": "/v1/requests/req_7f31",
             "pullRequest": "https://git.example.com/org/orders-api/pull/1" } }
```

Properties to insist on: *idempotency* (a retry does not create a second service), *asynchrony with status* (long operations return a request id), *explicit versions* of the API and of templates, and *machine-readable errors* with the same quality as human-readable ones.

```text
422 Unprocessable Entity
{ "error": "invalid_name",
  "message": "Name 'Orders_API' must be lowercase letters, digits and hyphens.",
  "example": "orders-api",
  "docs": "https://docs.example.com/reference/naming" }
```

### Portal options — decide with evidence

| Option | Strength | Cost | Use when |
| --- | --- | --- | --- |
| Repository docs, CLI and generated catalogue | Cheap, versioned, testable | Less discoverable; no UI | First iteration; small platform team |
| A portal framework | Rich catalogue, templates, plugins | Heavy build and upgrade burden | Many teams; dedicated capacity |
| Hosted portal products | Fast start | Cost, lock-in | A UI is needed quickly; vendor review done |

The decision test: *would a portal remove a stuck point you observed in a trial?* No trial yet means you do not know what to build.

Portal anti-patterns:

- A portal that duplicates data instead of reading it from the catalogue files, so two sources disagree.
- Plugins nobody owns. Every plugin is code the platform team upgrades forever.
- Workflows only in the UI, with no CLI or API equivalent, so automation cannot reuse them.
- A portal that shows a green tick when the underlying check has not run.

## Documentation as a product

Organise by reader's need (the Diátaxis model): *tutorial* (start here → first service), *how-to* (promote, roll back, read status), *reference* (contract, quotas, allowed environments) and *explanation* (why the platform works this way). Quality rules: every command is copy-pasteable and states expected output with no assumed directory, cluster context or account; errors are documented next to the step that causes them; accessibility basics (descriptive headings and link text, alternative text, no meaning conveyed by colour alone, text equivalents of diagrams — noting that this is not an accessibility audit); and docs are tested with link checks in CI and with real trials.

At scale, add:

| Practice | Why |
| --- | --- |
| Docs versioned with the path | A how-to for template v2 must not be shown for v3 without a notice |
| Search analytics (terms with no result, pages left quickly) | Reveals missing or unfindable content without a trial |
| "Was this page helpful?" with a free-text field routed to owners | Cheap, continuous signal; read the text, ignore the percentage |
| Docs-only dry runs on a schedule | A teammate follows the tutorial without help; findings go to the backlog |

## Operational status a developer can read

A single status command gives a verdict:

```text
$ platform-status orders-api
SERVICE   orders-api   owner: team-orders
ENV       staging      digest: sha256:3f1c...e9a0   source commit: 9d2f...
STATUS    HEALTHY      replicas: 2/2 ready   last reconcile: 40s ago
RUNBOOK   https://example.com/runbooks/orders-api
```

It must not lie: an unpromoted service with zero replicas is `UNKNOWN` or `DOWN`, not `HEALTHY`. Document what it does *not* check.

| Condition | Verdict |
| --- | --- |
| Desired state present, all replicas ready, reconcile recent | HEALTHY |
| Some replicas ready | DEGRADED |
| Desired state present, none ready | DOWN |
| No promotion recorded | UNKNOWN (not deployed) |
| Reconcile older than threshold or Git and cluster disagree | STALE or DRIFTED, with what to do |
| The status system itself cannot reach the cluster | UNKNOWN (status unavailable), never HEALTHY |

## Investigability: the developer's failure path

The on-call developer did not build the platform. Within minutes they must learn *what is wrong* and *the first safe action*. The platform supplies the status command, per-service runbooks, linked telemetry and safe first actions (re-promote a previous digest, never edit live objects).

Runbook quality bar:

| Criterion | Detail |
| --- | --- |
| Starts with a command that produces a verdict | The status command |
| Symptoms in the user's words | Not internal jargon |
| First safe action is reversible | Re-promote a prior digest |
| States when to stop and escalate | A clear boundary |

## Audit: what happened, who did it, can we prove it

Audit is not a feature added later. Self-service without an audit trail is an incident waiting for a question nobody can answer.

| Question an auditor or incident lead asks | Where the answer lives |
| --- | --- |
| Who requested this change? | The pull request author and the platform API request log (with identity) |
| Who approved it? | Review records; branch protection enforces them |
| What exactly changed? | The commit diff |
| Was policy evaluated, with what result? | Check run results; admission logs |
| What is running now versus what was approved? | Status command and drift report |
| Who had access last quarter? | Identity provider group history |

Design points:

- **Immutable enough.** Protected branches, required reviews and signed commits for platform repositories; logs shipped off the system they describe.
- **Link the records.** A request id appears in the pull request, the deployment annotation and the API log, so one id walks the whole chain.
- **Record exceptions as data.** Deviations and policy exemptions have owner, reason, approver and expiry, and appear in a report.
- **Retention is a decision.** State how long logs and records are kept, and why, in writing.

```yaml
# exemption record (data, reviewable, expiring)
id: EX-0042
rule: image-by-digest
subject: service/legacy-reports
reason: vendor image distributed by tag only; digest pinning planned for Q1
approver: security-lead
requested-by: team-reports
expires: 2027-01-31
compensating-control: image scanned nightly; admission log reviewed weekly
```

## Maintainability: keeping a hundred services current

The path's real cost is not building it but keeping its output healthy over years.

| Mechanism | Description | Prevents |
| --- | --- | --- |
| Logic by reference | Reusable workflows and base manifests, versioned | A single fix needing many pull requests |
| Version stamp | `.golden-path.yaml` in generated services | Not knowing who is behind |
| Upgrade pull requests | A bot proposes template changes to generated services | Manual, error-prone upgrades |
| Compatibility rules | Additive changes in a major version; deprecation windows | Surprise breakage |
| Scheduled generation tests | Nightly matrix and lab deployment | Template rot |
| Dashboard of versions in use | Counts of services per template version | Ossification of old versions |

A simple report that makes the problem visible:

```text
template http-python
  v3   31 services
  v2   14 services   (deprecated 2026-08-01, removal 2027-02-01)
  v1    2 services   (past removal date: team-legacy, team-reports)
```

A service past the removal date is a conversation, not an automatic breakage. The platform team owes those teams a migration guide and an offer of help; the teams owe a plan and a date.

## Time to first success

The single most informative developer-experience number for a platform is the time a *new* person needs to reach a first healthy deployment, with only the documentation.

### Defining the measure so it cannot be gamed

| Item | Definition |
| --- | --- |
| Start | Participant is handed the task card and the docs link |
| Stop | Acceptance check passes, the participant gives up, or the time box expires |
| Documented waits | CI runtime, review wait — recorded separately and subtracted |
| Stuck point | Paused beyond two minutes, backtracked or searched without progress; record time, goal, document being read |
| Intervention | The observer says or shows anything not in the written docs |
| Independent completion time | Stop − start − documented waits, counted only with zero undocumented interventions |

Intervention classes: **I0** observer silent (pass-eligible); **I1** observer repeats information verbatim in the docs (a findability defect, still pass-eligible); **I2** observer gives information not in the docs (trial fails); **I3** observer touches the keyboard (trial fails). Answering "just once" is an I2.

### Components of time

Splitting the total shows where to invest:

```text
total time to first healthy deployment: 74 min
  reading and orientation:                   9 min
  prerequisites and access (documented wait: 0 min):  14 min
  scaffold and first pull request:           6 min
  CI and review (documented wait, subtracted): 11 min  -> excluded
  diagnosing a failed check:                18 min   <-- largest stuck point
  deploy verification:                       5 min
  independent completion time:              52 min
```

An eighteen-minute stuck point on one failed check is a far better target than "make everything faster". Fix it, and measure again with a *new* participant (the Expert level explains why).

### Secondary measures

| Measure | Signal | Caution |
| --- | --- | --- |
| Time to second service (returning developer) | The path becomes routine | Different population from first-time users |
| Share of new services created through the path | Adoption | Meaningless without a check that they *stay* on it |
| Median age of generated-service template version | Maintainability | Needs a policy for what is "too old" |
| Support requests per new service | Friction | Normalise by category; falling counts can mean people gave up asking |
| Policy rejections at admission | Guardrail messaging quality | A high count may be good (catching) or bad (late feedback) |

## Operating the platform as a product

| Practice | Minimum |
| --- | --- |
| Support model | `platform-support` and `platform-gap` labels, a stated response target; convert repeated questions into docs or fixes within the week |
| Versioning | Logic in reusable workflows and base manifests so fixes propagate by reference; a version stamp on generated services; deprecation notes and migration guides for breaking changes |
| Roadmap | Ranked by how many developers hit it, how badly and how often, using trial findings and support categories |
| Platform reliability | Template tests, link checks, catalogue freshness, periodic docs-only dry runs |
| Service levels | Stated targets for the scaffold, the API and the status command; published uptime and incident notes |
| Communication | A changelog and a deprecation calendar developers can subscribe to |

### The platform's own service level

The path is a service. Give it objectives, for example:

| Capability | Indicator | Objective |
| --- | --- | --- |
| Scaffold | Share of generation requests that succeed | 99% over 30 days |
| Shared CI workflow | Share of runs failing for platform reasons | below 1% |
| Status command | Median response time; correctness checks against a known fixture | under 3 seconds; 100% correct |
| Support | Time to first human response | one working day |

When the path breaks for everyone at once, that is an incident: declare it, communicate it, write a post-incident review.

## Failure modes at this level

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Self-service as privilege escalation | Request path lets a developer name a team they do not belong to | Authorise against identity-provider groups; test with a negative-case suite |
| Wrong owner on an incident | Ownership data rotted | Validated ownership; confirmation cycle; unowned service report |
| Check passes, admission denies | Two policy sources | One policy source with shared tests |
| Portal shows stale health | Cached or missing check shown as green | Explicit freshness; UNKNOWN as a first-class state |
| Template rot | Generation never tested | Nightly matrix and lab deployment |
| Silent forks | Teams copy and diverge | Version stamp; deviation records; fleet dashboard |
| Audit gap | Reconciler acts with no record of the requester | Carry request id and identity through every step |

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Reduce cognitive load | One complete, supported path | A menu of ten equal options |
| Keep templates alive | CI generates and tests them | Untested scaffolding |
| Make services findable | Catalogue as files, generated index, freshness check | A wiki nobody updates |
| Safe self-service | Requests as reviewed data, reconciler with narrow credentials | Developers holding cluster-admin credentials |
| Trustworthy ownership | Validated against the identity provider, confirmed periodically | A free-text owner field |
| Automation and UI together | API first; portal as one client | Features only reachable in the UI |
| Prove usability | A trial with an independent participant | A demo by the author |
| Handle deviation | Record, expire, treat as a product signal | Silent forks of the path |

## Knowledge consolidation

1. Why does every self-service action delegate authority, and what four questions follow?
2. Why should the pull-request policy check and the admission policy share a source?
3. What are three validations that keep ownership data trustworthy?
4. What properties should an API for service creation have, and why do they matter for retries?
5. What should a status command report when it cannot reach the cluster?
6. Why subtract documented waits from time to first success, and why separate them?
7. What is a platform service-level objective for a scaffold, and who is its customer?

## Exercises

1. **Risk table.** Classify ten platform actions by blast radius and propose a control for each. Identify where a human gate adds judgement and where it only adds delay.
2. **Policy tests.** Write table tests for a rule "no `latest` tags": three allowed, three denied, with the expected message for each.
3. **Ownership validator.** Write a script that checks each catalogue entry's owner against a list of groups and a recent-confirmation date, and reports violations.
4. **API contract.** Specify idempotent service creation: request, success, a validation error and a duplicate request. Explain what the client does on a timeout.
5. **Audit walk.** Pick a recent change in a system you know and trace the request id through identity, review, policy, deployment and status. Note where the chain breaks.
6. **Time split.** Time a colleague following the tutorial, record stuck points and split the total as in the example. Recommend the single most valuable fix.
