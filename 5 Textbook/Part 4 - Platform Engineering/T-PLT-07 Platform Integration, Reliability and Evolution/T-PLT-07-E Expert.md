# T-PLT-07-E — Expert Depth

*Chapter: [T-PLT-07 — Platform Integration, Reliability and Evolution](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-07-e"></a>
#### T-PLT-07-E — Expert Depth

## Why this level exists

At the Professional level the platform is one well-engineered system with known seams, tested recovery and honest evidence. At Expert level three things change. The system is no longer one system: dozens of teams, several clusters and many shared components interact, so failures *propagate* in ways no component owner designed. The system is no longer static: every interface the platform exposes is a promise to people who are not in the room, and changing it is a migration. And the claim "developers can use it" can no longer rest on the authors' judgement; it needs evidence from people who had no part in building it.

This section covers whole-platform failure propagation, cross-domain policy, evolution and deprecation, migration and resilience at organisational scale, validation by independent users, and hard design cases where every option has a cost. It uses the neutral `orders-api` service as a running example; the chapter has no dependency on any other course material. Commands and numbers are illustrative.

## Whole-platform failure propagation

### Failure is a graph problem

A component diagram shows what is *intended* to depend on what. A failure graph shows what *actually* breaks when something fails, including dependencies nobody drew. To build one, record for every component not just its declared inputs but its **runtime dependencies** (what it calls while operating), its **start-up dependencies** (what it needs to come up), and its **ambient dependencies** (DNS, time synchronisation, certificates, the network, the identity provider).

```text
Declared:     CI ──► Registry ──► Cluster
Actually:     CI ──► Registry ──► Cluster
               │         │           │
               ▼         ▼           ▼
             Identity   DNS        Admission webhook ──► Policy engine ──► Cluster API
               │         │           │
               └──── Clock / certificates ◄──────────────┘
```

Questions that turn the graph into findings:

1. **What is the shared fate?** If DNS fails, which of the supposedly independent components fail together? Independence claims ("a second registry gives redundancy") collapse if both registries sit behind the same DNS zone, the same credentials or the same account.
2. **What is the critical path for recovery?** Which components must work to *fix* the thing that is broken? A rollback that needs the registry, the identity provider and the policy engine has three dependencies, and an incident that disables one of them blocks the fix.
3. **What fails closed, and what fails open?** Every dependency needs a documented answer.

### Propagation mechanisms

| Mechanism | How it spreads | Example | Defence |
| --- | --- | --- | --- |
| Shared fate | One underlying fault disables several "independent" components | DNS outage stops pulls, identity refresh and telemetry at once | Map shared dependencies; test independence by injecting the fault |
| Retry amplification | Clients retry failed calls, multiplying load on a struggling dependency | Controller and nodes retry a degraded registry; it never recovers | Exponential backoff with jitter; retry budgets; circuit breakers |
| Thundering herd | Many actors resume at once after an outage | All clusters resync and pull images simultaneously after a registry recovery | Staggered resync, rate limits, pull-through caches |
| Fail-closed cascade | A safety control that cannot reach its dependency blocks everything | Admission webhook down with `failurePolicy: Fail` blocks even the Pods that run the webhook | Exempt the policy engine's own namespace; alert on engine health |
| Fail-open drift | A control silently stops enforcing | A webhook set to `Ignore` admits unattested images during an engine outage | Alert when enforcement is degraded; reconcile after recovery by auditing what was admitted |
| Configuration blast radius | One edit reaches all consumers | A base manifest change alters resource limits for every service | Staged rollout; representative tests; ownership of shared files |
| Time and expiry | Credentials, certificates or tokens expire together | A CA or signing key expires on one day for the fleet | Expiry inventory; staggered issuance; alerts well ahead |
| Observability collapse | The system that shows the failure fails with it | Monitoring runs in the affected cluster | An independent minimal probe outside the platform |
| Humans as coupling | The same on-call people handle many failures | One incident exhausts the people who would handle the next | Separate rotas; escalation; incident limits |

### Hidden dependencies: a worked trace

A team reports that no deployments are happening. The controller shows `Synced` for old revisions and does not see the new commit.

```text
Observation 1: promotion PR merged 40 min ago; controller still reports previous revision.
Hypothesis A: controller cannot reach the repository.
  Check:   controller logs → "authentication failed: token expired"
  Finding: the controller's deploy credential for the desired-state repo expired.
Why did it not alert?
  Expiry alert existed for production credentials; this one was created under a different naming pattern.
Why did the old state keep serving?
  The data plane is independent; the control plane failed silently.
Why did the rollback plan not trigger?
  Nobody was rolling back; there was simply nothing happening.
Fix:     rotate credential; add the pattern to the expiry inventory; alert on
         "no new revision observed for N minutes despite merged commits".
```

The final control matters: a **negative-space alert** detects *the absence of an expected event* (merged commits with no corresponding reconciliation) rather than the presence of an error. Most control-plane failures are silent and are caught only this way.

### Recovery ordering and the dependency cycle

Draw the recovery graph and find its **minimum bootstrap set**: the smallest group of components that, once restored by hand, lets everything else restore itself. Typical members: a copy of the infrastructure code, a copy of the desired-state repository, credentials to fetch both, and a pinned bundle for the controller. If a necessary item is held only inside the thing it restores (the credential to the registry is stored in the cluster whose images come from that registry), you have found a bootstrap cycle.

```text
Bootstrap set check
  Held outside the platform?              yes / no
  Reachable if the primary cloud account is unavailable?   yes / no
  Reachable if the identity provider is down?              yes / no
  Last restored from, by whom, how long it took:           date / person / duration
```

A bootstrap set that has never been used is untested. A failure of the recovery procedure during a real incident is a second incident on top of the first.

### Platform blast radius, measured

Estimate the radius of each shared artefact as *services affected × criticality × time to detect × time to roll back*. A reusable workflow used by 200 services with a 30-minute detection time has a radius an order of magnitude larger than a template change that only affects new services. Use the number to decide where to spend rollout machinery.

| Shared artefact | Consumers | Detection | Rollback | Rollout approach |
| --- | --- | --- | --- | --- |
| Reusable CI workflow | All services | Next pipeline run | Version pin revert | Canary teams, staged cohorts |
| Base manifest library | All services at next sync | Next sync | Revert and resync | Staged by environment then cohort |
| Policy bundle | All admissions | Next deploy | Previous bundle | Audit mode, then enforce by namespace |
| Controller upgrade | One cluster | Immediate | Reinstall previous | One cluster at a time |
| Registry credentials | Many pulls | Next pull | Re-issue | Overlapping validity |

## Cross-domain policy

Policy in a platform is not one rule set. It is several layers owned by different parties that must compose without surprising anyone.

### Layers of policy

| Layer | Owner | Example rule | Where it applies |
| --- | --- | --- | --- |
| Organisation | Security, legal, finance | Customer data stays in approved regions; images only from approved registries | Everywhere, non-negotiable |
| Platform | Platform team | Pods run non-root; resource limits set; promotion by digest | All workloads on the platform |
| Tier | Platform with risk owners | Production requires attested images; regulated data requires encryption and audit | By classification |
| Team | Service team | Extra readiness checks; stricter quotas | Their namespaces |

Composition rules to settle in advance:

1. **Precedence.** Higher layers override lower layers; lower layers may only tighten, never loosen.
2. **Conflict reporting.** When two rules conflict, the system reports it; it does not silently pick one.
3. **Exceptions.** An exception is a record with an owner, a reason, a scope, an expiry and a compensating control. Exceptions expire; renewal requires review.
4. **Version skew.** Policy bundles are versioned. Define how many versions may coexist in the fleet and how skew is detected.

```yaml
# Exception record (illustrative)
id: EXC-2026-031
rule: require-nonroot
scope: namespace=orders, workload=legacy-reporter
reason: vendor image requires root to bind a privileged port
compensating: read-only root filesystem; no service account token; network policy deny-all egress
owner: team-orders
approved_by: security-risk
expires: 2027-02-28
review: 2027-01-31
```

Count exceptions and measure their age. A growing, ageing exception list is a signal that either the rule is wrong or the path does not fit the workload (see the failure catalogue).

### Fail-open versus fail-closed, by domain

There is no single right answer; choose per control and record the reason.

| Control | Failure mode choice | Reasoning | Compensation |
| --- | --- | --- | --- |
| Admission for production images | Fail-closed | Unsafe image reaching production is the larger harm | Exempt system namespaces; break-glass; alert on engine health |
| Admission for development namespaces | Fail-open with audit | Availability of developer iteration matters more | Audit log reviewed; weekly report |
| Identity for deployments | Fail-closed | Unauthenticated deploys are unacceptable | Offline break-glass accounts |
| Cost guardrails | Fail-open with alert | Blocking production on a cost tool outage is wrong | Alert; later reconcile |
| Image scanning gate | Fail-closed for new images, fail-open for rollback of an already-deployed digest | A known previous digest is safer than none | Explicit rule: rollback to previously deployed digests bypasses new-scan requirement |

The last row shows a general principle: **the policy that gates change must not block the change that restores a known-good state**, or an incident can be prolonged by the control meant to prevent harm.

### Testing policy as code

Policy is code and needs tests, versioning and review.

```text
policy/
  rules/require-attested-digest.rego
  tests/
    allow/signed-digest-staging.yaml        # must be admitted
    deny/latest-tag.yaml                    # must be refused with message M1
    deny/unattested-digest.yaml             # must be refused with message M2
    deny/other-registry.yaml                # must be refused with message M3
  fixtures/
    exceptions.yaml
  CHANGELOG.md
```

Run the suite on every policy change, run a *historical replay* (re-evaluate last month's admitted manifests under the new bundle and report what would now be denied), and release new policy first in audit mode. The replay turns "this seems right" into "this would have denied 14 workloads, here are the owners".

### Policy and the user's experience

Every denial is a support interaction. Measure *time to compliance after first denial* and the share of denials that lead to a support ticket. Improve messages (what, why, how to fix, link) until the numbers fall. A policy that is correct but unusable produces bypass culture (see failure catalogue).

## Evolution and deprecation

### Everything the platform exposes is an interface

Interfaces include the template parameters, the shared workflow inputs, the base manifest values, the catalogue schema, the CLI commands, the policy messages and the documented paths. Each has consumers whose code or habits depend on it. Treat these as **versioned contracts** with a compatibility policy.

```text
Compatibility policy (example)
  Patch (x.y.Z):  no change visible to consumers; can be rolled out immediately.
  Minor (x.Y.0):  additive; old inputs keep working; new behaviour opt-in or safe by default.
  Major (X.0.0):  may break; requires notice, migration guide, automation and a support window.
  Support:        the current and previous major version are supported; older versions are removed on a published date.
  Notice:         breaking changes announced at least 90 days before removal; security-driven changes may be shorter, with an explicit rationale.
```

### The deprecation lifecycle

Deprecation is a managed process with states, owners and measurements:

| State | Meaning | Platform actions | Consumer experience |
| --- | --- | --- | --- |
| Announced | Replacement exists; removal date set | Publish guide; start adoption tracking | Notice in docs, CLI and tickets |
| Warned | Using the old way produces a visible warning | Add warnings to CI and the status view; open bulk pull requests | Warnings with a link; a pull request already waiting |
| Restricted | New use of the old way is blocked; existing use continues | Block new adopters; prioritise help to the remaining | Existing services unaffected until deadline |
| Removed | Old way no longer works | Remove after confirming zero users or an agreed exception | Failure message names the replacement |
| Archived | History retained | Keep the decision record and migration guide | Reference only |

The golden rule is that **deprecation without migration support is abandonment**. Support means the new path is at least as easy as the old, an automated change is offered for the common case, the platform team handles the awkward cases with the owners, and an exception route exists with an expiry.

### Migration automation: the bulk change pipeline

For a change that touches many repositories, automate the pull requests and the tracking.

```bash
# Find all services still on workflow v1 (illustrative)
platformctl catalogue list --format json \
  | jq -r '.[] | select(.workflow_version | startswith("v1")) | .repo' > targets.txt

# Open one pull request per repo with an identical, reviewable change
while read -r repo; do
  gh repo clone "$repo" "work/$repo" -- --depth 1
  ( cd "work/$repo" \
    && git switch -c platform/workflow-v2 \
    && sed -i 's#ci-workflows/.github/workflows/build.yml@v1#ci-workflows/.github/workflows/build.yml@v2#' .github/workflows/*.yml \
    && git commit -am "ci: move to platform workflow v2 (see docs/migrate-v2)" \
    && gh pr create --fill --label platform-migration )
done < targets.txt
```

Adoption tracking is then a number with a trend, a list of stragglers and an owner for each:

```text
workflow v1 → v2 migration, day 45 of 90
  merged: 137 / 212 (65%)
  open PRs awaiting owner: 49   (median age 9 days)
  blocked (needs platform help): 11   → each has a named platform engineer
  exception requests: 15   (expiry set; compensating notes recorded)
  projected completion at current rate: day 82
```

Each stage of the migration has a **kill criterion**: if the change failure rate in migrated services rises above a threshold, pause, diagnose and fix before continuing.

### Evolving without freezing

Three tensions recur:

1. **Stability versus improvement.** Consumers want stability; the platform must improve. Resolve with the compatibility policy and a predictable cadence, not by avoiding change.
2. **One path versus many.** Forcing everyone onto one path fails when workloads differ. A shared core with supported variants, and a documented escape hatch with a cost (the team takes on more operations), keeps the path honest.
3. **Capability versus load.** Every added capability adds upgrade and security work. Maintain a **capability register** with owner, consumers, cost and a retirement review. Retire what no one uses.

Keep a **decision log** (why added, why retired) so that future teams do not repeat arguments or revive something removed for a reason.

## Migration and resilience at organisational scale

### Migrating a core component without downtime

Replacing the registry, controller, ingress layer or cluster generation is the platform's hardest class of change, because the platform runs everything and can only be migrated using itself. The reliable pattern is **parallel run with graduated cutover**:

```text
Phase 0  Design: define compatibility, rollback, and success measures; pick pilot services.
Phase 1  Build the new component alongside the old; no traffic or no ownership change.
Phase 2  Shadow: new component mirrors the old (reads, dry-run reconcile, copy of images).
         Compare outputs. Differences are findings.
Phase 3  Pilot: a few volunteer services move; the old path remains available.
Phase 4  Waves: cohorts by risk, lowest risk first; pause criteria between waves.
Phase 5  Cutover of defaults: new services use the new path; old path restricted.
Phase 6  Decommission: after a defined quiet period, with a rollback window.
```

Rules that keep it safe:

- **Reversibility until the last wave.** Each wave can be undone independently; test the undo for the first wave.
- **No flag days.** A migration that requires everything to move at once converts a hard problem into an outage.
- **Dual-write or dual-read with comparison where state is involved.** Compare before cutover; do not trust the new system's own report of success.
- **Own the long tail.** The last 10% of services take longer than the first 90%: legacy dependencies, absent owners, unusual workloads. Plan platform engineering time for them or accept running both systems longer.

### Cell-based and tiered architecture

At large scale, replace "one platform" with **cells**: independent, identical instances of the platform (clusters with their own controller, registry mirror and policy bundle) serving a subset of teams or regions. The benefits are bounded blast radius, independent upgrade, and a deployment unit for platform changes themselves.

| Property | One shared platform | Cells |
| --- | --- | --- |
| Blast radius of a bad platform change | All teams | One cell, if rollout is cell-by-cell |
| Upgrade strategy | Big upgrade with large risk | Staged, with canary cells |
| Operational cost | Lower | Higher: each cell needs monitoring, on-call tooling, capacity |
| Consistency | Easy | Needs automation and conformance tests across cells |
| Cross-team sharing | Easy | Needs explicit shared services (catalogue, identity) |

Cells do not remove shared dependencies: identity, the catalogue and the source of truth are usually global and need their own resilience. Draw them explicitly as the **global control plane** and examine their failure behaviour more strictly than anything else.

### Fleet management

When clusters multiply, treat cluster add-ons and Kubernetes versions as a fleet:

- Inventory every cluster's version and add-on versions, automatically.
- Upgrade in rings: development, a low-risk cell, then the rest, with soak time and automatic checks between rings.
- Define a *support window* for versions and enforce it with visible dashboards and bulk work.
- Test the upgrade path continuously in a replica environment rather than in production first.

### Organisational resilience

Reliability is also a property of the organisation:

- **Ownership transitions.** A team that dissolves or a maintainer who leaves must trigger a catalogue-driven handover; orphaned services are visible in a report.
- **On-call load.** Measure pages per engineer, night-time interruptions and repeat causes. Protect people from becoming the coupling in the system.
- **Knowledge distribution.** Rotate engineers through the operations of each seam; test knowledge by drills, not briefings.
- **Incident learning.** Reviews produce backlog items with owners and dates; verify closure by re-running the scenario.
- **Capacity for the unplanned.** Reserve a fraction of platform capacity for incidents and urgent migrations; a team planned at 100% cannot respond.

## Independent-user validation

### Why independence matters

The authors of a platform know which commands to run, which errors to ignore and which document is out of date. Their experience says almost nothing about a newcomer's. A claim that the platform is usable needs *independent users* — people who had no part in building or documenting it — performing real tasks under observation.

### Designing a validation study

```text
Validation protocol (example)
  Question:     Can an engineer new to the platform deploy and recover a service unaided?
  Participants: 6-8 engineers, none involved in building the platform;
                a mix of experience (junior, mid, senior) and background.
  Tasks:        T1 create service from template and reach first Ready Pod
                T2 make and promote a change
                T3 diagnose and recover a planted failure using only the runbook
                T4 explain what blocked an unsafe action and why
  Rules:        think aloud; the facilitator does not help; hints are logged and counted;
                a timer runs; a task is stopped after a pre-agreed limit (a failure, not an error).
  Measures:     completion (yes / yes with hints / no), time, hint count and type,
                error count, stuck points, confidence ratings before and after.
  Analysis:     stuck points by seam; severity (blocker, major, minor); repeat across participants.
  Output:       findings with evidence → backlog → fix → re-test with new participants.
```

Key design choices:

- **Fresh participants for re-tests.** Someone who has done the task once is no longer a newcomer. Keep a pool, or accept that a re-test with the same person measures something different.
- **Realistic tasks.** Planted failures should resemble real incidents, not puzzles; success should not depend on luck.
- **Observer discipline.** The facilitator records, does not coach, and writes hints down verbatim. A silent pause of several minutes is data.
- **Separate usability from capability.** Distinguish "could not find the digest" (a platform defect) from "did not know what a digest is" (a training gap). Both matter; they have different fixes.

### Reading small-sample results

With six or eight participants you cannot estimate a population rate precisely. For example, if 5 of 6 complete a task, the plausible range for the true completion rate is wide (roughly 40% to 99%). Use small studies for what they do well: **finding problems**. A stuck point that affects two of six people will recur for a large share of future users. Do not claim "83% success"; claim "five of six completed; the sixth stalled at step 4, which two others needed hints for".

| Result pattern | Interpretation | Action |
| --- | --- | --- |
| Many participants stall at the same step | A defect in documentation or tooling at that step | Fix and re-test with fresh participants |
| Different participants stall at different steps | Several small defects; or a general complexity problem | Cluster by seam; consider simplifying the path |
| Everyone completes, slowly | The path works but is costly | Measure time per step; remove the slowest steps |
| Senior engineers succeed; juniors do not | The path assumes background knowledge | Add explanation, defaults or training |
| Success only with hints | The unaided claim is false | Report the claim honestly; fix the hint topics |

### Longitudinal evidence

One study is a snapshot. Complement it with continuing signals: time to first deploy for each new service, support ticket categories, the proportion of services off the path and why, and short surveys after real tasks. Use quantitative signals to see *what*, and qualitative sessions to learn *why*.

**Guard against self-deception.** Common biases: selecting friendly participants, letting the facilitator hint, redefining success after the fact, ignoring failures that "could not happen in real life", and counting hints as completions. State the protocol before running the study and publish negative results.

## Hard design cases

Each case below has no free option. Work through requirements, options, failure behaviour, cost and a revisit trigger before reading the discussion.

### Case 1 — The admission webhook that blocked its own recovery

A policy engine runs as Pods in the cluster and validates all Pod creations (`failurePolicy: Fail`). A node pool upgrade evicts the engine's Pods; replacement Pods cannot be created because admission calls the unavailable engine. Everything stalls, including the Pods needed to run the engine.

*Discussion.* The fault is a self-referential dependency. Options: exempt the policy engine's namespace from its own webhook; run the engine on a dedicated, separately-upgraded node pool with disruption budgets; run enough replicas across failure domains; and alert on engine unavailability *before* a rescheduling event. Changing to `Ignore` removes the stall but allows unchecked workloads for the outage's duration; if you choose it, reconcile afterwards by auditing what was admitted. The deeper lesson is to write the failure mode into the design and test it by stopping the engine in a drill.

### Case 2 — The reusable workflow update on Friday

The platform team merges an improvement to a shared build workflow referenced as `@main` by 180 services. A subtle change in cache keys makes builds fail on some runners. By the time anyone looks, pipelines have failed for two hours.

*Discussion.* Referencing a mutable ref gives every consumer the change at once. Remedies: version the workflow and have consumers pin a tag or digest; roll out by cohort using a bulk change; run the workflow against a representative service matrix before release; and publish a "pause" switch. Cost: pinned versions mean consumers lag and the platform team must support multiple versions. Mitigate by automating version bumps as pull requests that run the consumer's own pipeline first.

### Case 3 — Two registries, one failure

To avoid a registry single point of failure the team adds a mirror in a second region. During an outage of the primary registry's cloud account, the mirror cannot be reached either because it authenticates through the same identity provider, shares a DNS zone and its sync job runs in the same account.

*Discussion.* Redundancy that shares fate is not redundancy. Establish independence along each axis: account, credentials, DNS, network path and the control plane that syncs the mirror. Test by injecting each failure separately. Also decide *what the mirror contains*: every digest in the release record, or only the most recent? A mirror that holds only recent images does not support rollback to older releases.

### Case 4 — The migration with no owner for the last forty services

A controller replacement is 85% complete. The remaining services are owned by teams that were reorganised; some owners cannot be identified.

*Discussion.* Use the catalogue to assign each orphaned service a temporary owner (the nearest team or the platform), classify by criticality and traffic, and decide per service: migrate with the platform's help, freeze and run both systems with a decommission date, or retire. Publish the list and the dates; avoid indefinite dual running, which doubles operations cost. Decide the policy for services nobody claims: after notice, scale to zero or archive, with an easy restore.

### Case 5 — The audit that wants evidence for all of last year

An auditor asks for proof that every production change last year was reviewed, built by the trusted pipeline and policy-checked. Evidence exists in pieces across systems with different retention.

*Discussion.* Evidence that is a by-product of operation can be queried; evidence assembled from memory cannot. Design the **evidence ledger** at the start: for every production change store commit, reviewers, attestation result, policy decision and deployment identity in an append-only store with retention matching obligations. For past gaps, report them honestly with the compensating evidence you have; do not manufacture records. Cost: storage and a small pipeline; benefit: an audit becomes a query.

### Case 6 — The platform that is too successful

Adoption passes 90% and the platform team is the bottleneck for exceptions, new capabilities and incident help. Teams begin building private shortcuts.

*Discussion.* Success shifts the problem from adoption to scale. Move from a ticket queue to self-service for the common cases; split the platform into a stable core and extension points owned by capability teams; publish an inner-source contribution route; track queue time as an SLI; and set a policy for which requests the platform declines. Declining well (with a documented reason and an alternative) is part of product management.

### Case 7 — Metrics that make everyone look good

The platform dashboard shows deployment frequency rising and change failure rate falling. Developers report that deploys are more stressful. Investigation shows teams split changes into tiny deploys and reclassify failures as "incidents, not failures".

*Discussion.* A metric becomes a target and stops measuring. Pair quantitative measures with qualitative research; define measures precisely and audit the definitions; compare metrics that pull in opposite directions (frequency against failure rate against restore time); and never use them to rank teams.

## Evaluating platform health

| Dimension | Signals |
| --- | --- |
| Adoption | Share of services on the path (voluntary), new-service rate, deviation count and age |
| Experience | Trial results, stuck-point trends, survey ratings, support categories |
| Delivery performance | Lead time, deployment frequency, change failure rate, restore time (as signals, not targets) |
| Reliability | Platform SLOs, incident frequency and duration |
| Cost | Platform run cost, per-service cost, idle capacity |
| Sustainability | Team load, on-call burden, bus factor, backlog age |

## Scaling beyond one team

Typical inflection points: dozens of services (manual support stops scaling), several teams with different needs (one path is insufficient), regulatory or audit requirements (evidence automation), and multiple clusters or regions (fleet management). Responses include a self-service tenant provisioning API, multiple supported paths with a shared core, policy bundles by risk tier, a fleet manager for cluster add-ons and upgrades, and cost allocation per team.

**Governance without gatekeeping.** Prefer automated guardrails and visible standards to approval boards. Make secure, compliant behaviour the default and measure deviation. Where human approval remains (production access, new data classes), define response times and keep audit trails. Evidence for auditors should be a by-product of normal operation: change records, review histories, policy results, access reviews.

**Build, buy or adopt.** For each capability compare building, adopting open source, and buying: total cost including operations and upgrades, fit to your path, extensibility, security posture, exit costs and team skills. Record the decision with a revisit trigger. Beware assembling many projects, each with its own upgrade and security treadmill, into something one person must carry.

## Failure catalogue

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Platform change outage | Shared component changed for everyone at once | Staged rollout, representative tests, rollback |
| Adoption cliff | The path stops fitting new workloads | Product research, multiple paths, escape hatch |
| Governance bypass culture | Controls too slow, teams route around | Make the compliant path faster; measure deviation |
| Tool sprawl | Too many components for the team to operate | Thinnest viable platform; retire aggressively |
| Single-person dependency | One maintainer holds the knowledge | Pairing, runbooks, rotation, documentation tests |
| Metric gaming | Targets on DORA or adoption numbers | Use as signals; pair with qualitative research |
| Silent control-plane failure | Controller or credentials fail, nothing alerts | Negative-space alerts for expected events that did not occur |
| Shared-fate redundancy | "Independent" copies share DNS, identity or account | Axis-by-axis independence tests |
| Recovery that needs the broken thing | Rollback blocked by registry or policy outage | Minimum bootstrap set; documented rollback exemptions |
| Exception sprawl | Exceptions never expire | Expiry and review; investigate rules with many exceptions |
| Migration long tail | Last services never move | Named owners, dates, retirement policy |

## Expert trade-offs

| Decision | Cost of choosing too far one way | Cost of choosing too far the other | Typical resolution |
| --- | --- | --- | --- |
| Centralise versus federate platform ownership | Bottleneck, slow response | Divergence, duplicated effort, inconsistent security | Stable shared core; owned extension points |
| One shared platform versus cells | Large blast radius | Higher operating cost, consistency drift | Cells when blast radius or regulation demands; automation first |
| Strict versus flexible policy | Bypass culture | Unsafe defaults | Tight defaults, expiring exceptions, measured deviation |
| Frequent versus slow platform releases | Constant churn for consumers | Large risky upgrades | Predictable cadence; semantic versioning; automated bumps |
| Deep versus thin platform | Capability sprawl | Teams rebuild shared mechanics | Thinnest viable platform; retire aggressively |
| Evidence ledger versus agility | Overhead on every change | Audit pain, no proof | Capture automatically; no manual steps in the path |
| Build for scale now versus later | Over-engineering | Painful migration | Design interfaces for change; defer machinery until an inflection point is visible |

**Final architecture review checklist.** Does every claim have evidence? Is every ADR linked to a limitation or a revisit trigger? Can a stranger operate the platform from the runbooks? Has each failure drill been run by someone other than the author? Which unproven claims are presented as unproven? What is the next most valuable improvement, and what evidence ranks it first? What is the minimum bootstrap set and when was it last used? Which shared artefact has the largest blast radius and how is it rolled out? Which deprecations are running, with what adoption numbers?

## Knowledge consolidation

- Failures **propagate through runtime, start-up and ambient dependencies**; draw the failure graph, not just the component diagram.
- Redundancy that shares **fate** (DNS, identity, account) is not redundancy; test independence by injecting each fault.
- Control-plane failures are **silent**; use negative-space alerts that detect expected events that did not happen.
- Find the **minimum bootstrap set** and rehearse recovery from it; remove bootstrap cycles.
- Policy has **layers, precedence and expiring exceptions**; test it as code, replay history, and ship in audit mode first.
- Choose fail-open or fail-closed **per control**, and never let the gate on change block the change that restores a known-good state.
- Every platform surface is an **interface**: version it, announce, warn, restrict, remove, with migration support at each step.
- Migrate core components by **parallel run and graduated cutover**; own the long tail.
- Use **cells** to bound blast radius at scale; give the global control plane the strictest scrutiny.
- Validate with **independent users**, pre-registered protocols, counted hints and honest small-sample claims.
- Metrics are **signals, not targets**; pair them with qualitative research.

## Exercises

**Exercise 1 — Failure graph.** Draw the failure graph for your platform including runtime, start-up and ambient dependencies. List three shared-fate pairs you had not previously recorded, and state a test that would confirm each.

**Exercise 2 — Negative-space alert.** Design an alert for "merged promotion commits with no reconciliation within N minutes". Define N, the data sources, the false-positive cases and who is paged. Test it by suspending the controller.

**Exercise 3 — Bootstrap set.** Identify the minimum bootstrap set for your platform. Mark each item *held outside*, *reachable under identity-provider failure* and *last used*. Plan a drill that uses only the set to rebuild a practice cluster.

**Exercise 4 — Policy replay.** Take a policy rule you plan to tighten. Re-evaluate the last 30 days of admitted manifests under the new rule and produce a report of what would now be denied, grouped by owner, with a rollout plan.

**Exercise 5 — Deprecation plan.** Choose a platform interface (a template parameter, a workflow input, a CLI command). Write the compatibility policy, the state timeline, the bulk-change automation, the adoption measures and the kill criteria.

**Exercise 6 — Core migration.** Write a phase plan for replacing the delivery controller with a different one. Include shadow comparison, pilot services, wave criteria, reversibility tests and decommission conditions.

**Exercise 7 — Validation study.** Write a protocol for evaluating time to first deploy with six independent participants. Specify tasks, stopping rules, measures, hint logging and how you will report a 5-of-6 result honestly. Run a pilot with one person and revise.

**Exercise 8 — Blast-radius ranking.** List your shared artefacts. Estimate services affected, detection time and rollback time for each, rank them and match each with a rollout approach.

**Exercise 9 — Design case.** Pick one of the hard cases and write a one-page design: requirements, three options, failure behaviour of each, cost and a revisit trigger. Present it to a colleague and record the objections.

**Solution notes.**

*Exercise 1.* Typical new pairs: DNS with identity and telemetry; the clock with certificates and token validity; one cloud account with the registry, its mirror and the CI runners. Tests: block the shared dependency in a non-production environment and observe which "independent" components fail.

*Exercise 2.* N should reflect the normal reconciliation interval plus a margin, not a round number. Expected false positives include repository outages and intentional pauses; handle them by suppressing during announced maintenance. The test should show the alert firing when the controller is suspended and clearing when it resumes.

*Exercise 3.* Common findings: the credential to fetch the desired-state repository lives only in the cluster; the bootstrap manifest references a mutable tag; nobody knows the order. Each becomes a fix: out-of-band copies, pinned versions, a written rebuild order.

*Exercise 4.* A good report names owners and counts, and proposes a staged enforcement date by namespace. If the report is empty, check that the replay actually evaluated the tightened rule and used real manifests.

*Exercise 5.* Look for a warning that appears where the developer will see it, a bulk pull request already open, and a removal date that follows measured adoption rather than the calendar alone.

*Exercise 6.* Strong plans compare *outputs* during shadow mode (what each controller would apply) and keep the old controller able to resume ownership during the first waves. Weak plans move everything on a single date.

*Exercise 7.* The honest statement for 5 of 6 is a description of what happened and where the sixth stalled, not a percentage. Pilot runs usually expose unclear tasks and missing consent or recording logistics; fix those first.

*Exercise 8.* The reusable pipeline workflow and the base manifest library usually top the ranking because every service consumes them. The rollout approach should be stricter than for a template used only by new services.

*Exercise 9.* Marks go for naming what each option costs and the failure behaviour under the stated fault, not for choosing the most elaborate design. A good revisit trigger is concrete, such as "re-evaluate when the number of clusters exceeds ten".

## Mentoring prompts

A platform-wide reusable workflow needs a breaking change; design the rollout so no team is surprised and no team is blocked. How would you tell whether falling adoption is a product problem, a communication problem or a sign the path is no longer needed? What is the smallest set of capabilities with which you would launch a platform for a ten-person engineering organisation, and why? Which of your recovery paths depend on a component that would itself be down in the incident you are preparing for? Describe an exception you would refuse to grant, and what you would offer the requester instead. If an independent-user study showed that everyone completed the task but only with hints, what would you report and what would you change first?

---
