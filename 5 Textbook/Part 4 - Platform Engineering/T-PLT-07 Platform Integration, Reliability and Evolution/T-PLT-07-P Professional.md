# T-PLT-07-P — Professional Engineering

*Chapter: [T-PLT-07 — Platform Integration, Reliability and Evolution](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-07-p"></a>
#### T-PLT-07-P — Professional Engineering

## Why this matters

A platform that works on a good day is a demonstration. A platform that you can hand to another team, audit, and recover at three in the morning is an engineering system. The difference is made of properties that no single component supplies: an architecture whose trust boundaries are drawn deliberately, a delivery path with known recovery behaviour, ownership that survives staff changes, runbooks tested by strangers, and evidence that is a by-product of operation rather than a document assembled before a review.

This Professional section is about those cross-cutting properties. It describes the end-to-end architecture as a set of planes and trust boundaries, then works through reliability and recovery, security, ownership, runbooks, evidence and the trade-offs between them. It uses a neutral `orders-api` service on Kubernetes with a GitOps controller; the chapter has no dependency on any other course material. Commands and outputs are illustrative.

## First principles: control plane, data plane, and what depends on what

Separate two things that are easy to blur.

- The **data plane** is what serves users: the running Pods, their network path and their data stores.
- The **control plane** is what *changes* the data plane: the repository, CI, registry, desired-state repository, delivery controller, admission policy and identity provider.

A failure in the control plane usually does **not** stop the data plane. If the registry is down, running Pods keep serving. What stops is the ability to deploy, scale up (new nodes must pull images), roll back and recover. This is the central reliability fact of a platform: **control-plane outages are silent until you need to change something, and you need to change something precisely when something else has gone wrong.**

That gives two questions to ask of every component:

1. *What stops working for users if this is down?* (data-plane impact)
2. *What can we no longer do if this is down?* (control-plane impact)

The second question is the one most designs skip.

## The end-to-end architecture

```text
                       ┌──────────────── IDENTITY PROVIDER ─────────────────┐
                       │  human SSO · CI workload identity · cluster RBAC   │
                       └──┬──────────────┬───────────────┬───────────────┬──┘
                          │              │               │               │
   ┌────────┐   PR   ┌────▼───┐  build ┌─▼──────┐  digest┌▼──────────┐    │
   │Developer├──────►│  Repo  ├───────►│   CI   ├───────►│ Registry  │    │
   └────────┘        └────┬───┘        └────────┘        └─────┬─────┘    │
                          │ promotion PR                       │ pull     │
                     ┌────▼──────────────┐              ┌──────▼──────────▼──┐
                     │ Desired-state repo├─────────────►│ Delivery controller│
                     └───────────────────┘   reconcile  └──────┬─────────────┘
                                                               │ apply (via admission policy)
 CONTROL PLANE ──────────────────────────────────────────────────────────────────────────
 DATA PLANE                                              ┌─────▼──────────────┐
                                                         │ Cluster: Pods, net │──► users
                                                         └─────┬──────────────┘
                              ┌────────────────────────────────┤
                       ┌──────▼──────┐   telemetry      ┌──────▼──────────┐
                       │ Monitoring  │◄─────────────────┤ State: DB, vols │
                       └──────┬──────┘                  └─────────────────┘
                              │ alerts, status
                       ┌──────▼──────┐
                       │ On-call /   │──► rollback or fix PR (back to Repo)
                       │ developer   │
                       └─────────────┘
 Underneath: infrastructure-as-code created cluster, network, storage and accounts.
```

Read the diagram with three lenses.

**The artefact lens.** Commit → image digest → desired state → Pod → telemetry. Each arrow is a contract you can test.

**The trust lens.** Every box trusts something it did not create. The controller trusts Git; the cluster trusts the controller's credentials; admission trusts rules that someone wrote; the registry trusts the pushing identity. Drawing the trust arrows is how you find the places where compromise of one component grants too much.

**The failure lens.** For each box ask the two questions above. The next section turns that into a table.

## Dependency and recovery table

| Component | If it is down: users | If it is down: we cannot | Recovery approach | Recovery objective (example) |
| --- | --- | --- | --- | --- |
| Source host / repository | No impact | Merge, build, promote, roll back via the normal path | Replica or mirror; break-glass procedure for emergency changes | Restore access within 1 hour |
| CI | No impact | Produce new images | Second runner pool; previously built digests remain deployable | Resume builds within 2 hours |
| Registry | New nodes and rescheduled Pods cannot pull | Deploy, scale, recover node loss | Pull-through cache or mirror in a second account; image digests recorded in Git | Serve pulls within 30 minutes |
| Desired-state repo | No impact | Promote, roll back | Mirror; cluster keeps last applied state | Restore within 1 hour |
| Delivery controller | No impact (state frozen) | Apply changes; detect drift | Re-install from Git (bootstrap); data plane unaffected meanwhile | Re-bootstrap within 1 hour |
| Admission policy | Depends on failure mode: fail-closed blocks all deploys *and* rescheduling; fail-open admits unchecked changes | Deploy safely | Documented failure mode; exempt system namespaces; alert on policy-engine health | Engine healthy within 15 minutes |
| Identity provider | Existing sessions persist; new logins and token refresh fail | Authenticate humans, issue short-lived credentials | Break-glass accounts held offline; cached credentials with bounded lifetime | Restore within 1 hour |
| Monitoring | No impact, but blind | Detect, diagnose, verify recovery | Independent minimal health probe outside the platform | Probe independent of the main stack |
| State store | Impact: data unavailable or wrong | Serve data-dependent requests | Backups off-cluster; restore tested | RTO and RPO per data tier |

The "recovery objective" column is an example, not a recommendation. What matters is that the column exists, that someone chose each number against business need, and that each was *demonstrated* in a drill rather than asserted.

### Bootstrapping: the platform that runs the platform

Look for **circular dependencies**: the controller that deploys the monitoring system is monitored by that system; the registry runs in the cluster that pulls from it; the identity provider needs the cluster to start and the cluster needs the identity provider to authorise. Circles are fine in steady state and fatal in cold recovery.

Test the cold start: starting from an empty cluster and a Git repository, can you re-create the platform, and in what order? Write the order down.

```text
Rebuild order (example)
 1. Network, cluster, node pools (infrastructure as code)
 2. Identity bindings and cluster roles
 3. Delivery controller, installed from a pinned manifest
 4. Controller syncs: namespaces, policy engine (admission in audit mode first)
 5. Registry access / mirror credentials
 6. Monitoring stack and alert routes
 7. Workload namespaces; services sync in dependency order
 8. State restores; verification queries; traffic enabled
```

The step "admission in audit mode first" illustrates a typical lesson: a fail-closed policy engine that is not yet ready can block the very components needed to make it ready.

## Reliability and recovery of the delivery path

Treat the delivery path as production. That means it has service-level objectives, capacity, on-call, incident process and rehearsed recovery.

### SLOs for the platform itself

The platform is a service with its own reliability. Choose indicators that reflect what users of the platform (developers) experience:

| SLI | How measured | Example objective |
| --- | --- | --- |
| Promotion success rate | Promotions merged that reach `Synced` and Ready, divided by promotions merged | 99% over 30 days |
| Time from merge to running | Merge timestamp to all-Ready timestamp for a deploy | p95 under 10 minutes |
| Template generation success | Scaffold runs completing with a green first build | 98% |
| Status availability | Synthetic probe of the status command | 99.5% |
| Catalogue freshness | Age of the oldest service entry not refreshed | Under 24 hours |
| Time to first deploy for a new service | From scaffold to first Ready Pod, measured in independent trials | Under 1 working day |
| Support response | Time to first useful reply | Under 4 working hours |

Measure and publish them. Apply the error-budget discipline from site reliability practice: when a platform SLO is burning, platform changes slow down and reliability work takes priority.

```text
Promotion success SLO: 99% over 30 days. Volume: ~900 promotions/month.
Budget: 9 failed promotions/month.
Month so far: 14 failed (7 policy errors, 4 registry timeouts, 3 controller sync errors).
Action: freeze non-urgent platform changes; fix registry timeout (largest controllable cause).
```

### Progressive rollout of platform changes

A change to a shared component (a reusable workflow, a base manifest, a policy bundle) affects every service at once. Roll it out the way you ask product teams to roll out theirs:

1. Test against a *representative set* of services (stateless, stateful, high-traffic, oldest-template).
2. Release to a canary team that agreed in advance.
3. Stage by cohort with a pause for signals between cohorts.
4. Keep a one-step rollback of the platform release.

### Recovery drills

| Drill | Injection | What it proves |
| --- | --- | --- |
| Bad promotion | Promote a digest that fails to start | Rollback through Git works and is timed |
| Expired secret | Rotate or expire a credential | Alerts name the broken credential; rotation procedure works |
| Registry outage | Block pulls from one node pool | Cached images or the mirror keep recovery possible |
| Controller loss | Delete the controller | Re-bootstrap from Git matches the recorded order |
| Policy engine down | Stop the engine | The documented failure mode occurs; alert fires |
| Reconciliation suspended | Suspend sync | Drift is reported and the alert names the owner |
| Node loss | Cordon and drain a node | Workloads reschedule; pulls succeed |
| Missing backup | Suspend the backup job | Freshness alert fires within its threshold |
| Quota exhaustion | Lower a namespace quota | Failure signals are clear; the runbook helps |

**Pick, do not do all.** Choose by *what you have least evidence for*. A drill that confirms a well-practised path is cheap but teaches little.

**Game days.** Someone other than the author injects a failure from a card; you respond using only the runbook. Convert each confusion into a platform fix and record it. Include a cost line: practice clusters cost no compute, but any cloud-based path needs an estimate, a budget alarm and a teardown.

## Security across the whole path

Component security is covered by each tool's own guidance. At platform level the question is how identities, secrets and evidence behave *between* components.

### Identity: short-lived, narrow, per step

| Actor | Credential | Scope | Lifetime |
| --- | --- | --- | --- |
| Developer | SSO session | Repository write via pull request; read-only cluster view | Hours |
| CI build | OIDC workload token exchanged for a registry credential | Push to `orders-api` image name only | Minutes |
| Promotion bot | Short-lived token | Open pull requests on the desired-state repo only | Minutes |
| Delivery controller | Cluster role | Apply manifests in listed namespaces | Long-lived, but scoped and audited |
| Workload | Service account bound to a cloud or secret-store role | Read its own secrets | Token refresh |
| On-call (break-glass) | Elevated role requested with a reason | Time-boxed cluster edit | One hour, recorded |

The aim is that no single credential can both produce and deploy an artefact. If the same identity can push an image *and* edit the desired state, an attacker (or a mistake) with that identity bypasses review entirely.

### Secrets: where they live, how they move

Secrets are never in Git in plain form. Two common patterns: (a) store references in Git and let the workload read from a secret store at start-up using its workload identity; (b) store encrypted values in Git decryptable only by the cluster. Each has failure modes: the reference may point at a secret that was rotated; encrypted values depend on a key whose loss makes Git unreadable. Define rotation, who is alerted when a secret expires and how the key is backed up.

### Supply-chain evidence verified, not stored

An attestation nobody checks is decoration. Verify at **two points**: in the pipeline (`promotion-verify`, early and cheap, with good messages) and at admission (late and hard to bypass). Differences between them are a seam to test. Check *three claims*: the image exists, it was produced by the trusted builder, and its source commit was reviewed.

```yaml
# Admission rule (illustrative, policy-engine neutral)
rule: require-attested-digest
match: Pod in namespaces labelled env in [staging, production]
conditions:
  - image reference must contain "@sha256:"
  - attestation present and signed by identity matching ^https://ci\.example\.com/.+
  - attestation subject digest equals image digest
on_violation: deny
message: "Images must be promoted by digest with a valid build attestation. See docs/promotion."
```

The `message` matters: a denial that tells the developer what to do next is a developer-experience feature and a security control at once.

### Negative testing as security evidence

For each control, write a test that *attempts the forbidden thing* and asserts it is refused:

```bash
# Negative tests: each must FAIL to apply. Exit 0 here would be the bug.
set -u
kubectl apply -f tests/neg/pod-latest-tag.yaml        2>&1 | grep -q "must be promoted by digest"
kubectl apply -f tests/neg/pod-root-user.yaml         2>&1 | grep -q "runAsNonRoot"
kubectl apply -f tests/neg/pod-unattested-digest.yaml 2>&1 | grep -q "attestation"
kubectl apply -f tests/neg/pod-from-other-registry.yaml 2>&1 | grep -q "allowed registries"
echo "all negative cases refused"
```

Run these after every policy change and after every platform upgrade.

## Ownership that survives people

Ownership is the property that someone acts when a seam breaks. It has four ingredients:

| Ingredient | Test |
| --- | --- |
| A named owner (team or rota, not an individual) | Can you find the owner of any seam in under a minute? |
| Authority and access | Can they change the thing without asking someone else? |
| Capacity | Is the work on their backlog with time allocated? |
| A route to them | Does an alert or a ticket reach them automatically? |

Record ownership as data attached to artefacts, not as folklore:

```yaml
# catalogue entry (illustrative)
service: orders-api
owner: team-orders
oncall: rota/orders-primary
tier: standard
runbooks:
  developer: docs/runbook-developer.md
  operator: docs/runbook-operator.md
seams:
  promotion-verify: platform
  retention-policy: platform
  telemetry-emitted: team-orders
data:
  backup: platform-data
  restore-tested: 2026-10-18
```

**Platform on-call.** The platform needs its own on-call with its own severity scale: for example, *Severity 1*: no service can deploy or roll back; *Severity 2*: one cohort affected or a safeguard degraded; *Severity 3*: slow or confusing without blocked work. Define what product teams can expect and when.

**Bus factor.** For each critical seam record who can operate it. If the answer is one person, rotate a second person through an actual drill (not a briefing) this quarter.

## Runbooks that work at 3 a.m.

Runbooks are tested artefacts, not documents. Two audiences need two documents:

- **Developer runbook:** symptoms visible to the service team (status `DEGRADED`, error rate, "not Ready", `database: unreachable`) and the first safe action, usually a rollback through Git.
- **Operator runbook:** decision tree for the platform on-call (Pod down versus data wrong; exact restore command; verification query; who approves; "do not delete the volume to fix this").

Standard shape: *when to use*, *who*, *numbered steps with the expected output*, *how to verify*, *do not*, *escalate to*, *last tested by whom and when*.

```text
Runbook acceptance test
  Reader: someone who did not write it and has the access the runbook assumes
  Setup:  a planted failure from a card, unknown to the reader
  Pass:   the reader restores service using only the runbook; every step output matches
  Fail:   any step needs knowledge or access not stated; any step output differs
  Record: version, tester, duration, confusions → backlog items
```

A runbook with no acceptance test is a hypothesis. Date and version each run, and expire a runbook that has not been tested within a defined period (for example, two quarters) by marking it *stale* in its header.

## Evidence: a by-product of operation

Evidence answers "how do you know?" without a meeting. Prefer evidence that the system produces automatically.

| Claim | Evidence | Freshness |
| --- | --- | --- |
| Only reviewed code reaches production | Branch protection configuration export; merge history showing approvals | Checked weekly by a job |
| Images are built by the trusted pipeline | Attestation verification results in promotion check logs | Per promotion |
| Unsafe changes are refused | Negative-test run output | Per policy change |
| Rollback works | Drill timeline with runbook version | Quarterly |
| Restores work | Restore drill with fingerprint comparison | Quarterly |
| Platform meets its SLOs | Published dashboard and monthly report | Monthly |

Maintain two registers:

- A **claims ledger**: each claim, its evidence link, the date last verified and an owner. A claim with no fresh evidence is shown as *unproven*.
- A **limitations register**: known gaps stated plainly (for example, "restore tested for the primary database, not for the search index"), each with a reason and what it would take to close.

Honest limits are a strength. A reviewer who finds an undeclared gap loses trust in everything else; a reviewer who finds a declared gap with a plan learns that the rest is probably accurate.

## Integration seams: the checklist

| Seam | What commonly goes wrong | Deliberate negative case |
| --- | --- | --- |
| Template ↔ policy | Generated manifests violate admission rules | Scaffold a service and deploy it with no edits |
| CI ↔ registry | Digest not recorded, or recorded for a different build | Compare recorded digest with the registry for ten builds |
| Promotion ↔ verification | Verification checks the attestation but not the source commit | Attest a build of an unmerged branch and try to promote |
| Controller ↔ ownership | Pruning removes something Terraform or a human owns | Create an unmanaged resource in a managed namespace; confirm it is flagged, not pruned |
| Policy ↔ Pod Security ↔ network policy | Stateful component blocked by default-deny or restricted policy | Deploy the database component from the template |
| Status ↔ reality | Status reports healthy because it checks too little | Break the database dependency; status must change |
| Backup ↔ restore | Backups never restored; restore command undocumented | Restore to a scratch environment and compare fingerprints |
| Retention ↔ rollback | Older digests deleted | Pull every digest in the last 30 promotions |
| Identity ↔ pipeline | Credential outlives need or has wider scope | Attempt to use the CI token for another image name |

Test each seam with a deliberate negative case, and record the result with a date.

## Cost, improvement and the backlog

Turn evidence into a backlog; do not leave it as notes.

| Source | Example finding | Platform change |
| --- | --- | --- |
| Acceptance stuck point | The participant could not find the digest after merge | The release summary prints the digest and the next command |
| Stateful drill | Status says HEALTHY while data is wrong | Add a backup-age and data-freshness check; document limits |
| Policy denial | The error did not say how to fix it | Improve the message with a documentation link |
| Game day | The runbook assumed operator access | Split developer and operator runbooks |
| SLO burn | Registry timeouts consumed the promotion budget | Add a pull-through cache; alert on pull latency |

Rank by *evidence of impact* (how many people, how often, how severe) divided by cost, and record what you chose *not* to do. Cost has three parts: compute and storage (including idle environments), people (on-call load, support hours) and opportunity (what the team did not build).

## Professional trade-offs

| Decision | Option A | Option B | How to choose |
| --- | --- | --- | --- |
| Policy failure mode | Fail-closed: safe, can block recovery | Fail-open: available, can admit unsafe changes | Fail-closed for production deploys, with exemptions for system namespaces and a tested break-glass; document it |
| Verification location | Pipeline only: friendly, bypassable | Admission only: strong, late and terse | Both; pipeline for messages, admission for enforcement |
| Number of environments | Few: cheap, less realistic | Many: realistic, costly | Match risk; fewer environments with better evidence beat many unmaintained ones |
| Shared workflow | One versioned workflow: consistent, large blast radius | Per-team pipelines: isolated, divergent | Shared core with version pinning and staged upgrades |
| Controller scope | One controller for all: simple, single point | Per-cluster or per-tenant: contained, more to operate | Per-cluster at least; per-tenant when isolation matters |
| Break-glass | Rare, heavy approval | Easy, audited | Make the safe path faster than break-glass; audit all uses |
| Evidence collection | Manual before reviews | Automated by-product | Automate the claims that are checked most often |
| Backup location | In cluster: fast | Off cluster: survives cluster loss | Off cluster; test restores |

## The demonstration run

Map each required demonstration point to evidence; rehearse a run of show (about thirty minutes); run a pre-demonstration checklist (every evidence link resolves, the environment is clean, backups exist, secrets are not in Git, the limitations register is current); and prepare for a defence: a reviewer's questions about *why* each decision was made and *what you would change at ten times the scale*.

```text
Run of show (30 min)
  0-3   Architecture on one page; the claims ledger summary
  3-10  New service created by a person who is not the author
  10-15 Change → review → trusted build → promotion; three-way match shown
  15-20 Unsafe change refused (negative cases), with the messages
  20-26 Planted failure; recovery by runbook; timeline shown
  26-30 Limitations register; next improvement and why it ranks first
```

**Reflection record.** *Achieved* (with evidence links), *Deferred* (what, why, what it would take), *Learn next* (three items tied to findings), *What surprised me / what I would do differently*. A good reflection is specific and linked to evidence.

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Prove integration | End-to-end run with evidence at each seam | Component-level demos only |
| Improve reliably | Backlog from drills, acceptance and support | Notes that never become work |
| Keep honest | Claims ledger and limitations register | Optimistic summaries |
| Control cost | Budgets, teardown, idle policy | Leaving environments running |
| Hand over | Runbooks tested by someone new | Knowledge in one head |
| Limit blast radius | Staged rollout of platform changes | Updating the shared core for everyone at once |
| Recover from loss | Bootstrap from Git, off-cluster backups, mirrored images | Components that can only be rebuilt from themselves |
| Enforce rules | Verify at pipeline and admission | Trusting stored attestations |

## What can go wrong: a short catalogue

| Failure | How it looks | Defence |
| --- | --- | --- |
| Control-plane outage found during an incident | Rollback impossible because the registry is down | Mirror; test pulls from the mirror; rehearse |
| Fail-closed policy blocks recovery | Nodes drain, Pods cannot reschedule | Exempt system namespaces; alert on engine health |
| One credential does everything | A leaked CI token can deploy to production | Separate producing from deploying identities |
| Evidence is stale | Claims ledger entries a year old | Freshness dates; mark stale entries unproven |
| Runbook never tested | Step 3 refers to a command that no longer exists | Acceptance tests; expiry |
| Backups only in cluster | Cluster loss destroys data and backups | Off-cluster copies; restore drills |
| Metrics gaming | Promotion counts rise while quality falls | Use signals together with qualitative review |

## Knowledge consolidation

- Separate the **data plane** (serves users) from the **control plane** (changes it). Control-plane outages are silent until you need to change something.
- For every component ask: *what stops for users?* and *what can we no longer do?* Write the answers down with a recovery approach and a demonstrated objective.
- Look for **circular dependencies**; rehearse a **cold start** from Git and write the rebuild order.
- The platform has **SLOs** of its own; platform changes roll out **progressively** with representative tests and fast rollback.
- Identities are **short-lived, narrow and per step**; no credential both produces and deploys.
- Verify supply-chain evidence at **two points**; prove controls with **negative tests**.
- Ownership means a named owner, authority, capacity and a route; record it as **data**.
- Runbooks are **tested by strangers**, dated and expired.
- Evidence is a **by-product**; keep a **claims ledger** and a **limitations register**.
- Every decision has a trade-off; write it down with its revisit trigger.

## Exercises

**Exercise 1 — Dependency table.** Fill in the dependency and recovery table for your platform. For each row, state the data-plane and control-plane impact and the recovery you have *demonstrated* (not asserted).

**Exercise 2 — Cold start.** On a practice cluster, delete the delivery controller and rebuild from Git using your written order. Record each step's duration and each surprise. Update the order.

**Exercise 3 — Platform SLOs.** Choose three SLIs, define how each is measured, set objectives, compute the monthly error budget from your promotion volume and write what you will do when 50% of it is burned.

**Exercise 4 — Negative suite.** Write at least six negative tests for your admission rules. Run them; then deliberately weaken one rule and show a test fails.

**Exercise 5 — Credential audit.** List every credential in the delivery path with scope and lifetime. Find any identity that can both publish an artefact and deploy it, and design the split.

**Exercise 6 — Runbook acceptance.** Have someone who did not write a runbook execute it against a planted failure. Record version, duration and confusions, and fix the runbook.

**Exercise 7 — Claims ledger.** Write ten claims about your platform with evidence links and last-verified dates. Mark any that cannot be supported as *unproven* and add them to the limitations register.

**Exercise 8 — Fail-open or fail-closed.** Argue for each failure mode for your production admission policy. Choose one and specify the exemptions, alerts and break-glass that make the choice safe.

**Solution notes.**

*Exercise 1.* Registry and identity rows usually reveal the weakest recovery: both are easy to forget because they rarely fail. If your "demonstrated" column is mostly empty, that is the honest answer and the plan for drills.

*Exercise 2.* Expect ordering surprises: policy engine before system namespaces are exempted, credentials needed before the controller can pull, a bootstrap manifest that referenced a tag. Each belongs in the rebuild order or the pinned bootstrap bundle.

*Exercise 3.* With about 900 promotions a month, a 99% objective gives a budget of 9 failures. At 50% burn (about 4 or 5 failures) a sensible action is to review causes and pause low-value platform changes. Report counts by cause, not just a rate.

*Exercise 4.* A negative suite that stays green after a rule is weakened is not testing the rule. The deliberate weakening proves that the tests can fail.

*Exercise 5.* Common finding: a CI credential with write access to both the registry and the desired-state repository. Splitting means the build identity pushes images and a separate promotion path, with review, changes desired state.

*Exercise 6.* A confusion is any pause where the reader asks someone or guesses. Count them; the number should fall across versions.

*Exercise 7.* Typical unproven claims are about restores of secondary data and about break-glass audit trails. Naming them is the point.

*Exercise 8.* A strong answer chooses fail-closed for production deploys *and* names exemptions for system namespaces, an alert on engine unavailability and a timed break-glass; it also states the cost: a policy-engine outage can delay a rollback.
