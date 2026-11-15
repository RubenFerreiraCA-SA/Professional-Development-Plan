# T-PLT-05-P — Professional Engineering

*Chapter: [T-PLT-05 — Platform Product Thinking and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-05-p"></a>
#### T-PLT-05-P — Professional Engineering

## Why this matters

A platform that serves ten teams can run on goodwill. A platform that serves a hundred cannot. At that scale, every question has a price: why does this team exist, what does it promise, how will anyone know when it breaks the promise, what does it cost, who pays, and what will it stop doing to make room for something new? Professional practice turns the instincts of the earlier levels into **explicit, reviewable, funded commitments**: a strategy that names what the platform is for, architecture decisions that can be audited, team interfaces that are designed rather than accumulated, service level objectives that make promises testable, a roadmap that expresses bets rather than wishes, a cost model that survives a budget review, and outcome measures that say whether any of it worked.

This section assumes the Beginner and Intermediate material (jobs to be done, golden paths, catalogue, prioritisation, ADR basics). Examples use the fictional `orders-api` service and the `checkout` and `payments` teams; registry names such as `registry.example.com` are placeholders.

A recurring theme: **every commitment must be small enough to keep and specific enough to fail.**

## An integrated outcome matrix

Define the platform's promises as outcomes a user could verify, and map each to evidence.

| Outcome | Capabilities it integrates | Evidence |
| --- | --- | --- |
| 1. A developer creates a service | Template, repository governance, container build | The service exists with owner and runbook; review gate was required |
| 2. A reviewed change triggers a trusted build | Review and branch protection, CI, registry | Pull request, run, digest, attestation |
| 3. Self-service deployment under identity and policy | Infrastructure as code, GitOps, access control, templates | Tenant manifests, promotion pull request, policy denial transcript |
| 4. Health, failure and recovery are visible and rehearsed | Observability, orchestration, operations | Drill timelines, runbooks, status output |
| 5. An independent developer succeeds without help | Everything | An acceptance record |

Nothing counts as done without a link to evidence you can open. Optional capabilities (AI features, a specific monitoring vendor) are marked "not in scope" rather than half-delivered, with an equivalent bar recorded if a substitute is used.

## Product strategy for a platform

A strategy is a set of choices about where to concentrate scarce effort. A useful platform strategy has the structure of a *diagnosis, guiding policy and coherent actions*.

| Part | Question | Example |
| --- | --- | --- |
| Diagnosis | What is the real problem, supported by evidence? | New services take 11 working days to reach production because of access, environment and pipeline set-up |
| Guiding policy | What approach will we take, and what will we refuse? | One golden path for stateless services; no bespoke pipelines; exits are documented, not blocked |
| Coherent actions | What concrete work follows? | Template, tenant automation, status command, support route |
| Exclusions | What will we not do? | General application hosting; per-team toolchains |
| Evidence of success | How will we know in two quarters? | Median time to first deploy under one day; adoption above 70 percent by voluntary choice |

**A strategy that excludes nothing is a wish list.** If every item in the strategy could be justified by any team, no team has been disappointed, and nothing has been chosen.

**The platform value chain.** Connect platform work to the outcomes the organisation cares about.

| Level | Example measure | Who cares |
| --- | --- | --- |
| Platform activity | Features shipped, tickets closed | The platform team |
| Platform outcome | Time to first deploy; self-service rate | Platform users |
| Delivery outcome | Lead time, deploy frequency, change failure rate, restore time | Engineering leadership |
| Business outcome | Time to market for features; incident cost avoided | Executives |

Report upward through the chain, but be honest about causation. The platform *contributes* to delivery performance; it rarely *causes* it alone.

**Build, buy, adopt or compose.** For each capability record the decision and why.

| Option | Choose when | Hidden cost |
| --- | --- | --- |
| Build | The capability is specific to your context and a differentiator for your users | Permanent maintenance; the team becomes a vendor |
| Buy | The capability is a commodity with a good market | Integration, lock-in, per-seat costs, limited customisation |
| Adopt open source | Strong community; you can operate it | You carry upgrades, security patches and on-call |
| Compose | A thin layer joins existing tools behind one interface | The seams are yours to maintain |

A short rule: *buy or adopt the commodity, build the glue that encodes your golden path*.

## Architecture decision records at scale

At the Intermediate level an ADR records one decision. At scale you also need a *practice*: how decisions are proposed, reviewed, linked and retired.

**An ADR lifecycle**

| State | Meaning |
| --- | --- |
| Proposed | Under review; has a named reviewer from an affected team |
| Accepted | Decision in force; implementation tracked |
| Superseded | Replaced by a later ADR, linked both ways |
| Deprecated | No longer relevant; kept for history |
| Rejected | Considered and declined, with reasons (also valuable) |

**What makes an ADR good**

| Property | Test |
| --- | --- |
| Single decision | One sentence states what was decided |
| Honest alternatives | At least two real options, with the reason each lost |
| Consequences in both directions | Costs are named, not just benefits |
| Evidence | Links to measurements, trials or incidents |
| Revisit trigger | A condition that would reopen it, ideally measurable |
| Findable | Indexed by topic and linked from the affected code or manifests |

**Architecture fitness checks.** Where a decision has a testable consequence, test it automatically. If an ADR says "CI holds no cluster credentials", a check can assert it.

```bash
# Fails if any workflow in the repository references a cluster credential secret
if grep -R --include='*.yml' -nE 'KUBECONFIG|CLUSTER_ADMIN_TOKEN' .github/workflows; then
  echo "ADR-007 violated: CI must not hold cluster credentials" >&2
  exit 1
fi
echo "ADR-007 holds"
```

A decision that cannot fail a check is a preference.

**Decision hygiene.** Review ADRs quarterly: close proposals older than a month, mark superseded ones, and list those whose revisit triggers have fired.

## Team interfaces designed on purpose

At the Beginner level you met the three interaction modes. Professionally, you design them per team and per capability, and you change them as maturity changes.

**An interface specification**

| Field | Example |
| --- | --- |
| Capability | Service deployment |
| Interaction mode | X-as-a-service for stateless services; collaboration for first stateful service |
| Consumer | Stream-aligned teams |
| Contract | Pull request to desired-state repository; promotion check; documented limits |
| Support | Business hours, response in 4 working hours; incident route for the platform's own failures |
| Change notice | Breaking changes announced 30 days ahead; deprecation policy published |
| Exit | Documented step-off with owner |

**Cognitive load budgeting.** Stream-aligned teams have a limited budget. List what the platform expects each team to understand and keep the list short.

```text
Team: checkout (6 engineers)
Platform concepts required to ship: service template, promotion pull request, status command,
                                    runbook format, three SLO fields
Concepts the team chooses to learn:  resource tuning, retry policy
Concepts hidden by the platform:     reconciler identities, admission policy details, registry layout
Review: quarterly; remove one required concept per quarter if possible
```

A platform that adds a required concept should say which it removes.

**Anti-patterns in team interfaces**

| Anti-pattern | Mechanism | Defence |
| --- | --- | --- |
| Permanent collaboration | The platform pairs forever; nothing becomes self-service | Time-box; define the exit criterion for each pairing |
| Gatekeeping | The platform reviews every change | Replace reviews with automated policy; review exceptions only |
| Shadow platform | A product team builds its own because the central one is slow | Treat as research; absorb or support the better parts |
| Embedded dependency | A platform engineer is seconded to one team permanently | Rotate; convert the work into a capability |
| Unclear escalation | Incidents bounce between teams | A written route, rehearsed |

**Enabling work.** Sometimes the right move is a *facilitating* mode: a short programme that coaches teams on a practice, then steps back. Measure it by how soon teams no longer need it.

## Promises and SLOs for the platform

A platform's promises must be **measurable, small and honest**. Service level objectives (SLOs) turn promises into numbers that can be missed.

**Terms**

| Term | Meaning |
| --- | --- |
| SLI (indicator) | A measurement of behaviour a user cares about, expressed as a ratio of good to total events |
| SLO (objective) | A target for the SLI over a window |
| Error budget | The allowed amount of failure implied by the SLO |
| SLA (agreement) | An external or contractual promise with consequences; rare for internal platforms |

**Platform SLIs users feel**

| Capability | SLI | Example SLO |
| --- | --- | --- |
| Service creation | Share of creation requests that produce a deployable service without human intervention | 95 percent over 30 days |
| Deployment pipeline | Share of valid changes that reach a healthy running state within 15 minutes of merge | 99 percent over 30 days |
| Status and logs | Share of queries answered within 5 seconds | 99 percent over 30 days |
| Support | Share of support requests acknowledged within the response target | 95 percent over 30 days |
| Documentation | Share of sampled pages verified within the last 90 days | 90 percent |

**Choosing a number.** Start from what users need, check what you currently achieve, and set the SLO slightly beyond current performance only if you can afford the work. An SLO of 99.99 percent on a platform run by four people is a fiction.

**Error budgets and decisions.** An error budget tells you when to stop shipping features.

```text
SLO: 99% of valid changes reach healthy state within 15 minutes (30-day window)
Budget: 1% of ~4,000 deployments = ~40 slow or failed deployments
Consumed to date: 31 (78%)
Policy: above 75% consumed, freeze new pipeline features; spend time on reliability.
        Above 100%: reliability work only until the window recovers.
```

The *policy* is the valuable part. An error budget with no decision attached is a graph.

**Separate platform health from user health.** A platform can be up while a user's deployment is failing because of their code. Define SLIs on the part the platform controls, and give users a way to tell which side a failure belongs to.

**Publish promises with exclusions.** A published promise names what it excludes: planned maintenance, a runtime version outside support, workloads outside the golden path.

## Roadmaps: bets with evidence

A roadmap is a communication tool and a record of bets. A feature list with dates is a promise nobody can keep.

**Now / next / later with outcomes**

| Horizon | Contents | Commitment |
| --- | --- | --- |
| Now (this quarter) | Work in progress, each with an outcome and a measure | High; changes announced |
| Next (following quarter) | Candidates with hypotheses and the evidence required to proceed | Medium; subject to discovery |
| Later (beyond) | Themes, not features | Low; direction only |

**Frame work as outcomes**

```text
Outcome: new services reach production without waiting for access
Measure: median wait for access, now 2 days, target under 1 hour
Hypothesis: role bundles granted at service creation remove 90% of access requests
Evidence needed before "next" becomes "now": 3 of 5 interviewed teams confirm access is the top blocker
Stopping condition: if median wait is not under 4 hours after one quarter, revisit
```

A feature list says "add role bundles". An outcome statement says why, how much and when to stop.

**Roadmap hygiene**

| Practice | Why |
| --- | --- |
| Show what you removed, not only what you added | Prevents a roadmap that only grows |
| Reserve capacity for operations and foundations | Keeps upgrades from becoming emergencies |
| Publish "not doing" with reasons | Builds trust and prevents repeated requests |
| Review with users quarterly | Keeps the roadmap tied to real pain |
| Distinguish commitments from intentions | Avoids broken promises |

**Deprecation is a roadmap item.** Retiring a template, a runtime version or a tool needs an owner, a migration path, a date, a measure of remaining users and a way to help the last ones.

## Funding and cost

A platform consumes money, and someone decides how much. The question is whether the decision is informed.

**Cost categories**

| Category | Examples | Notes |
| --- | --- | --- |
| People | Platform engineers, product manager, support rotation | Usually the largest share |
| Infrastructure | Compute, storage, network, registries, observability backends | Scales with usage |
| Licences and services | Portal, scanning, observability vendors | Often per seat or per volume |
| Opportunity cost | What users do instead of product work when the platform fails | Hard to measure, easy to ignore |

**Funding models**

| Model | Mechanism | Strengths | Weaknesses |
| --- | --- | --- | --- |
| Central budget | Funded as shared overhead | Simple; encourages use | No price signal; vulnerable to cuts |
| Showback | Show each team the cost it drives, without charging | Visibility; low friction | Little behavioural effect on its own |
| Chargeback | Charge teams for usage | Price signal; fairness | Overhead; teams avoid the platform; disputes over allocation |
| Hybrid | Fund the platform centrally; charge for expensive optional resources | Balanced | Needs clear rules for what is optional |

A common compromise is central funding of the base path and showback or chargeback for expensive extras, such as large environments or special runtimes.

**Unit costs.** Express cost per unit users understand.

```text
Platform cost (quarter):                       $1,260,000
  People (14 FTE)                                $980,000
  Infrastructure                                 $190,000
  Licences                                        $90,000
Active services on the golden path:                  210
Cost per service per month:                        ~$2,000
Estimated developer time saved per service per month: 12 hours  x $85 = $1,020
Reading: the platform does not pay for itself on time saved per service alone;
         the case rests on reliability, security posture and lead time.
```

An honest cost model can come out unflattering. A platform whose value case depends on assumptions the team has not tested should say so.

**Cost anti-patterns**

| Anti-pattern | Mechanism | Defence |
| --- | --- | --- |
| Invisible cost | Nobody sees the bill | Showback by team and service |
| Savings that move cost | The platform cuts its cost by pushing work to users | Measure total cost, including user time |
| Zombie capacity | Environments nobody uses | Expiry and ownership labels; scheduled clean-up |
| Vendor creep | Tools adopted for one team spread silently | Review each licence against the strategy |

## What "trusted" means — and does not

| Control | Claim it supports | What it does *not* prove |
| --- | --- | --- |
| Required review plus code owners | A second person saw the change | That the reviewer understood it |
| Required tests | Known regressions are blocked | The absence of bugs |
| Immutable digest | The same bytes run everywhere | That the bytes are safe |
| Provenance attestation | This digest was built by this workflow from this commit | That the source or workflow is benign; a compromised build system could sign anything |
| SBOM | You know the contents | That the contents are free of vulnerabilities |

**Promotion that verifies before it moves.** A promotion check binds *digest → expected source repository → approved workflow → required commit on the protected release branch*, and rejects on any mismatch. An attestation alone is not enough: the check must also compare the source commit against policy. The release process writes a small evidence record per digest so promotion can look up the allowed commit.

```json
{"commit": "9d2f...", "workflow": "release", "image": "registry.example.com/orders-api@sha256:3f1c...", "ref": "refs/heads/main", "event": "push"}
```

One page shows the chain: merge commit → run URL → digest → attestation commit → promotion pull request. Without a break in that chain, the artefact is traceable.

## Environments, identity and policy

| Question | Platform answer to record |
| --- | --- |
| Which environments can a developer promote to? | Staging by tool; production-shaped environments need a platform reviewer, not self-service |
| Who applies manifests? | A per-tenant reconciler identity with rights only inside its namespace |
| What can CI do? | Push images and attestations — no cluster credentials |
| What can a developer do in the cluster? | Read-only status; changes by pull request |

**Policy in two places.** Policy in CI (an offline evaluator, no credentials) gives fast feedback; policy at admission catches everything that bypassed CI. Use the *same* rules. Distinguish offline CI evaluation from live admission probes, which need a disposable cluster and show which layer (policy engine, Pod Security, RBAC) produced a denial.

**Secrets.** No secret lives in Git. For a demonstration database, an operator creates the credential out of band; record who creates it, how it rotates and the limitation of the environment (for example, base64 in etcd, unencrypted). Production-shaped options (an external secrets operator, sealed secrets or SOPS) are the next step.

**Stateful dependencies deliberately.** State is expensive to get wrong, so add it as an opt-in platform component with a documented human gate. It must satisfy the tenant's restricted Pod Security and default-deny network policy, with explicit allow rules for the application and database.

## Health and recovery targets before injecting failures

| Signal | Where | Healthy |
| --- | --- | --- |
| Pod Ready and restarts | Status tool, `kubectl` | Ready; restarts stable |
| Readiness body | `/ready` | `database: query_ok` — an authenticated query, not a TCP connect |
| Application contract | Write then read an entry | The same entry returns |
| Service endpoints | `kubectl get endpoints` | Non-empty |
| Backup freshness | Newest successful job and off-cluster copy | Within target age |

Set targets (for example RTO ≤ 3 minutes to a working read-write path) and report both measured recovery time and *estimated recovery-point age* (incident time minus last completed backup).

## Outcome measures: did the platform change anything?

Outputs are what you ship. Outcomes are what changes for users. Impact is what changes for the organisation. Professional practice tracks all three, and does not confuse them.

**A measurement plan**

| Outcome | Baseline | Target | Source | Review |
| --- | --- | --- | --- | --- |
| Median time to first deploy | 11 working days | under 1 day | Workflow timestamps | Monthly |
| Share of services with owner and runbook | 52 percent | 95 percent | Catalogue validation | Monthly |
| Self-service rate for creation | 60 percent | 90 percent | Support tags and workflow data | Quarterly |
| Change failure rate on the path | 14 percent | under 8 percent | Deployment records | Quarterly |
| Developer sentiment (would you recommend the path?) | 38 | 60 | Survey | Quarterly |

**Baselines before launch.** Without a baseline you can only say that numbers are now what they are. Capture the baseline before you change anything, even roughly.

**Attribution cautions**

| Trap | Description | Defence |
| --- | --- | --- |
| Survivorship | Only happy early adopters are measured | Include non-adopters and leavers |
| Confounding | Delivery improved for other reasons | Compare adopters and non-adopters with similar teams where possible |
| Metric gaming | Counts increase without value | Pair each metric with a counter-metric |
| Averages | Hide the long tail | Percentiles and segments |

**Counter-metrics.** Pair every target with the thing it could damage: speed with change failure rate, adoption with developer sentiment, ticket closure with reopen rate.

**Retire measures.** Remove a metric when it has no decision attached or has saturated, and say so in the review.

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Describe the platform | Outcomes with evidence links | A feature list |
| State direction | Diagnosis, guiding policy, exclusions | A list of every request |
| Explain trust | A claims table with "does not prove" columns | "Signed, therefore secure" |
| Record decisions | ADRs with alternatives, revisit triggers and fitness checks | Slide-deck architecture |
| Design team interfaces | Per-capability mode, contract, exit | Permanent collaboration or gatekeeping |
| Promise reliability | SLOs with error-budget policy | Aspirational nines |
| Plan | Outcome roadmap with stopping conditions | Dated feature list |
| Fund | Unit costs, showback, honest value case | Hidden cost or untested savings |
| Be honest | A limitations register from day one | Discovering limits during the demonstration |
| Handle state | Opt-in component, explicit human gate, restore drill | Treating a volume as a backup |

## Knowledge consolidation

- A **strategy** is diagnosis, guiding policy, coherent actions and *exclusions*; without exclusions it is a wish list.
- Link platform activity to **outcomes and delivery performance**, and be honest about contribution versus causation.
- At scale, ADRs need a **lifecycle**, honest alternatives, revisit triggers and **fitness checks** where a decision is testable.
- Design **team interfaces** per capability, with contract, support, change notice and exit; budget cognitive load and require that new concepts replace old ones.
- **SLOs** make promises measurable; an **error-budget policy** turns them into decisions.
- A **roadmap** expresses outcomes, hypotheses and stopping conditions, shows what was removed and reserves capacity for foundations.
- **Funding** needs unit costs and an honest value case; choose a model deliberately.
- "Trusted" claims come with **what they do not prove**; promotion verifies before it moves.
- **Outcome measures** require baselines, counter-metrics and attention to attribution.

## Exercises

**Exercise 1 — Strategy page.** Write a one-page strategy for a platform you know, with diagnosis, guiding policy, actions, exclusions and evidence of success. Delete any exclusion that nobody would argue with.

**Exercise 2 — Build, buy, adopt, compose.** Take five capabilities of a platform and assign one option to each, with the hidden cost you accept.

**Exercise 3 — ADR with a fitness check.** Write an ADR whose consequence can be checked automatically, then write the check.

**Exercise 4 — Interface specification.** For two capabilities, write interface specifications with mode, contract, support, change notice and exit. State what would make you change the mode.

**Exercise 5 — Platform SLOs.** Choose three SLIs a developer would notice, set SLOs justified by current data, compute the error budget in events and write the policy for consumption above 75 and 100 percent.

**Exercise 6 — Outcome roadmap.** Write a now/next/later roadmap with at least two outcome statements, each with a measure, hypothesis, evidence required and stopping condition. List two things you removed.

**Exercise 7 — Unit cost.** Build a unit-cost table for a platform (invent plausible numbers). State the reading you would present honestly.

**Exercise 8 — Measurement plan.** Write a measurement plan with baselines, targets, sources, reviews and one counter-metric per target. Identify the attribution trap most likely to affect you.

**Solution notes.**

*Exercise 1.* An exclusion is real if a team would be disappointed by it. "We will not build bespoke pipelines" qualifies; "we will not build bad software" does not.

*Exercise 2.* Hidden costs are the point: "buy" often hides integration and lock-in; "adopt" hides on-call; "build" hides permanent maintenance. A strong answer names who will carry each.

*Exercise 3.* A good check is cheap, runs in CI and fails loudly. If you cannot write one, restate the ADR's consequence until it is observable.

*Exercise 4.* Look for a documented exit and a change-notice period. Changing the mode is usually triggered by repeated interventions (move from X-as-a-service to facilitating) or stable use (move from collaboration to X-as-a-service).

*Exercise 5.* With 4,000 deployments per window, a 99 percent objective permits about 40 failures. The policy at 75 and 100 percent should state who decides and what stops.

*Exercise 6.* Check that every outcome has a number and a way to fail. Roadmaps that only add items indicate missing prioritisation.

*Exercise 7.* Unflattering readings are normal. A model that always shows large savings has probably not been challenged.

*Exercise 8.* Counter-metrics are paired as in the text (speed with failure rate, adoption with sentiment). The likeliest trap is survivorship: early adopters are enthusiastic.
