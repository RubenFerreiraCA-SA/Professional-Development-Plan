# T-PLT-05-E — Expert Depth

*Chapter: [T-PLT-05 — Platform Product Thinking and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-05-e"></a>
#### T-PLT-05-E — Expert Depth

## Why this level exists

At the Professional level you can run a platform as a product with a strategy, promises, a roadmap and a budget. At the Expert level the questions change character. They stop being "how do we do this well?" and become "what happens to this system, and to the people in it, over years?" Platforms do not usually fail because a component was badly chosen. They fail because the organisation around them changes: the sponsor leaves, the company doubles, a merger brings a second stack, a cost-cutting year removes the support rotation, or incentives quietly reward the wrong behaviour. The technical design that was right in year one becomes a liability in year four, and nobody wrote down which assumption has expired.

This section covers the operating models that organisations choose, the economics that sustain or starve a platform, multi-tenant architecture and its failure modes, the balance between governance and autonomy, how a platform evolves, how migrations succeed or stall, and the incentive failures that undermine all of it. It assumes the earlier levels and uses the fictional `orders-api`, `checkout` and `payments` names; the chapter depends on no other course material.

A recurring theme: **in a platform, the organisation is part of the architecture, and its incentives are load-bearing.**

## Platform as a product organisation

A platform team has a product manager function (even if shared), user research, a roadmap ranked by *how many developers hit a problem, how badly, how often*, a support model with response targets, and non-goals that protect focus. Treat internal users as customers who can decline: if use is mandatory you cannot learn whether the platform is good. Mandate only what safety requires (for example, production admission policy) and compete on experience for the rest.

**The thinnest viable platform.** Start with the smallest set that delivers a complete path, then add capabilities in response to measured stuck points. Overbuilt platforms fail by adding portals, operators and abstractions before basics (documented onboarding, a template that works, reliable CI) are reliable. Maintenance cost grows with every component; one maintainer cannot sustain many.

**Team topology and boundaries.** Define what the platform team provides as a *service* (self-service), a *capability* (enablement and consulting) or *collaboration* (temporary pairing). Align with cognitive-load thinking: the platform absorbs extraneous load (undifferentiated plumbing) so stream-aligned teams focus on their domain. Define explicit interaction modes and revisit them as maturity changes.

## Operating models

How a platform is staffed, owned and positioned in the organisation is a design choice with consequences. Five models are common, each with a typical failure.

| Model | Description | Works when | Typical failure |
| --- | --- | --- | --- |
| Central platform team | One team builds and runs the platform for all | Organisation of tens to low hundreds of engineers; shared runtime | Becomes a bottleneck and ticket queue as demand outgrows the team |
| Federated platform | Several platform teams own different layers or domains (runtime, data, delivery, security) | Larger organisations; domains with different users | Inconsistent interfaces; users face several front doors |
| Platform with embedded engineers | Platform engineers placed in product teams, with a shared practice | Early adoption and hard cases | Embedded engineers become permanent staff of the host team |
| Community or inner-source model | Product teams contribute to the platform under platform-team stewardship | Mature culture, strong review practice | Contributions stall without review capacity; quality varies |
| Product-team-owned tooling only | No platform team; each team owns its tooling | Small organisations | Duplicated effort; inconsistent security and reliability |

**Choosing a model.** Ask five questions.

1. How many teams, and how different are their needs?
2. How much of the delivery path is truly common?
3. What do we need to guarantee centrally (security, compliance, cost)?
4. Where does platform knowledge live, and how many people hold it?
5. What will the organisation fund for three years rather than one?

**Layered platforms.** Larger organisations often layer: a foundation layer (cloud accounts, networking, identity), a runtime layer (clusters, registries), a delivery layer (pipelines, release control) and an experience layer (portal, command line, templates). Each layer has customers: the layer above and the end users. A layer that does not know its customer builds the wrong thing.

| Layer | Primary customers | Typical promise |
| --- | --- | --- |
| Foundation | Runtime and security teams | Accounts, networks and identity provisioned within an agreed time |
| Runtime | Delivery layer and some product teams | Clusters available, upgraded within support windows |
| Delivery | Product teams | Merged changes reach production by the golden path |
| Experience | Product developers | Tasks completed by following one coherent interface |

**Interfaces between layers are the most fragile part.** A runtime upgrade that silently breaks the delivery layer costs more than either layer's internal failures. Specify each inter-layer interface with versions, compatibility policy and change notice, and test it in CI on both sides.

**Platform team health.** A team that cannot sustain its own operation will not sustain the platform. Watch: on-call load per engineer, proportion of unplanned work, bus factor per component, tenure and attrition, and the share of time spent on the roadmap rather than on interrupts. A platform team spending more than half of its time on interrupts has become the human API.

| Indicator | Warning level | Action |
| --- | --- | --- |
| Unplanned work | Over 50 percent of capacity for two quarters | Pause roadmap; automate the top three interrupts |
| On-call pages per engineer per week | Beyond what the team agreed as sustainable | Fix the noisiest alerts; add rotation depth |
| Components with a single maintainer | Any critical component | Pair, document, rotate |
| Attrition | Two or more departures in a year | Review workload and recognition, not only hiring |

## Economics of a platform

At Professional level you measured cost and value. At Expert level you reason about the *economic structure*: what scales, what is fixed, and where the value case breaks.

**Fixed, variable and step costs**

| Cost type | Examples | Behaviour |
| --- | --- | --- |
| Fixed | Core team, base clusters, licences with minimums | Do not shrink when usage shrinks |
| Variable | Compute, storage, observability volume | Grows with usage |
| Step | A new cluster, a second region, another support rotation | Appears when a threshold is crossed |
| Hidden | Time users spend working around the platform | Never appears on the platform's bill |

A platform that serves forty teams and then grows to eighty may need a step change in staffing, not a proportional increase. Plan for the steps, not the average.

**Where platforms create value**

| Value source | Mechanism | How to measure |
| --- | --- | --- |
| Time saved | Less repeated plumbing per team | Task-level time before and after |
| Risk reduced | Fewer misconfigurations, faster patching, enforced controls | Findings, incidents attributable to configuration, time to patch |
| Consistency | Easier hiring, mobility, support | Onboarding time, cross-team transfers |
| Option value | Ability to change infrastructure underneath without product disruption | Past migrations completed without product team work |
| Negative externalities avoided | Fewer outages that spread across teams | Incident blast radius history |

Time saved is the easiest to claim and the easiest to overstate. Risk and option value often carry the real case, and they are harder to prove.

**Break-even reasoning.** A rough test: the platform pays for itself when the sum of time saved, incidents avoided and risk reduced exceeds its total cost *including the hidden costs placed on users*.

```text
Annual platform cost                                   $5,000,000
Product engineers served                                     400
Fully loaded cost per engineer                          $180,000
Minimum time saved per engineer to break even on time alone:
   $5,000,000 / (400 x $180,000) = 6.9% of working time (~2.8 hours per week)
Reading: if trials show 1 hour per week saved, the case must be made on risk
         and option value, and those claims need evidence of their own.
```

**Economies and diseconomies of scale.** Shared services reduce cost per team as adoption rises, until coordination costs rise. Signs of diseconomies: a growing backlog of requests that need platform engineering, long review chains, and a platform team that cannot say no.

**Pricing signals.** If the platform is free at the point of use, demand is unconstrained and expensive options are overused. If it is chargeable, teams may avoid valuable safe defaults. Many mature platforms use *free defaults, priced extras and quotas*, so that safe behaviour costs nothing and expensive behaviour has a visible price.

| Resource | Treatment | Reason |
| --- | --- | --- |
| Golden-path service in a standard environment | Free, within quota | Removes friction from the safe choice |
| Large or long-lived environments | Showback with expiry | Reveals cost; limits zombies |
| Premium runtimes or special hardware | Chargeback or approval | Real marginal cost |
| Security and observability baselines | Always on, not optional | Safety should not depend on budget |

**Cost of delay and cost of the human gate.** A human approval step has a cost: waiting time multiplied by number of requests multiplied by the cost of blocked engineers. Compute it. Gates that cannot justify their cost should be automated or removed.

```text
Gate: manual approval for new environment
Requests per quarter: 120   Median wait: 1.5 days   Engineers blocked: 2
Blocked effort (conservative 25% productivity): 120 x 1.5 x 2 x 0.25 x 8 hours = 720 hours
Value of the gate: prevented 3 misconfigurations in the last year
Reading: automate with policy checks; keep human review only for exceptions.
```

## Multi-tenant architecture

A platform serves many teams from shared infrastructure. **Tenancy** is the set of rules that decide what tenants share, what is isolated and what happens when a tenant misbehaves. It is an economic choice as much as a technical one.

**What a tenant is.** A tenant is the unit of isolation and accountability: a team, a product, a business unit or a customer. Define it explicitly; many tenancy problems come from ambiguity ("whose is this namespace?").

**Isolation spectrum**

| Model | Isolation | Cost | Typical use |
| --- | --- | --- | --- |
| Shared cluster, namespace per tenant | Logical; shared kernel, control plane and nodes | Lowest | Trusted internal teams |
| Shared cluster with dedicated node pools | Compute isolation; shared control plane | Medium | Noisy or sensitive workloads |
| Cluster per tenant (or per group) | Strong control-plane and blast-radius isolation | High; operational multiplication | Regulated workloads; very different requirements |
| Account or subscription per tenant | Strongest administrative separation | Highest overhead; strong billing separation | Business units; separate compliance regimes |

Isolation has several dimensions. A tenancy design should address each explicitly.

| Dimension | Question | Typical control |
| --- | --- | --- |
| Identity and access | Can tenant A act on tenant B's resources? | Per-tenant roles bound to namespaces; no shared admin credentials |
| Network | Can A's workloads talk to B's? | Default-deny policies with explicit allows |
| Compute and memory | Can A starve B? | Quotas, limits, priorities, dedicated pools for noisy workloads |
| Storage and data | Can A read B's data? | Separate volumes, encryption keys and access policy per tenant |
| Control plane | Can A's API usage degrade B's? | Rate limits on controllers and admission; cluster-wide quotas on object counts |
| Observability | Can A see B's logs and metrics? | Tenant labels and query scoping |
| Cost | Can we attribute cost per tenant? | Labels, namespace-level metering |
| Failure | Can A's failure take down B? | Blast-radius design: separate failure domains for critical tenants |

**The noisy neighbour and the control plane.** Compute quotas are easy; control-plane limits are not. A tenant that creates thousands of objects or a misbehaving controller can degrade a shared API for everyone. Apply quotas to object counts, rate limit custom controllers and monitor control-plane latency per tenant.

**A tenant manifest as the contract.** Provisioning a tenant should be one reviewed change that creates all the isolation in one place.

```yaml
apiVersion: platform.example/v1
kind: Tenant
metadata:
  name: team-checkout
spec:
  owner: team-checkout
  tier: standard
  environments: [staging, production]
  quota:
    cpu: "40"
    memory: 160Gi
    objects: 2000
  network:
    defaultDeny: true
    allowEgress: [payments-api.platform.svc]
  identity:
    deployer: sa-team-checkout-deployer
    admins: [group:checkout-leads]
  cost:
    centre: CC-4410
  evidence:
    approvedBy: platform-reviewer
    reviewDate: 2026-06-14
```

**Tenant lifecycle.** Isolation is not complete without lifecycle: onboarding, quota change, transfer of ownership, offboarding with data deletion and credential revocation. Offboarding is the commonly neglected step, and orphaned tenants are a security and cost problem.

**Failure modes of multi-tenancy**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Shared admin credential | One credential spans tenants | Per-tenant identities; no shared break-glass without audit |
| Quota bypass | A tenant creates resources outside quota (cluster-scoped objects, custom resources) | Admission policy restricting object kinds; count quotas |
| Cross-tenant data path | A shared cache, message bus or log pipeline exposes data | Tenant-scoped keys and access in every shared service |
| Upgrade coupling | A shared runtime upgrade breaks one tenant's workload | Staged rollout by tier; compatibility testing; deprecation notices |
| Silent cost transfer | One tenant's usage inflates shared cost | Metering and showback |
| Orphaned tenants | Team disbanded; resources and access remain | Owner validation; expiry; offboarding workflow |

**When shared tenancy is the wrong answer.** If tenants cannot trust each other, if regulations require separation, or if the cost of a cross-tenant incident is unbounded, a stronger isolation model is warranted, whatever its cost. Write the threat model before choosing.

## Governance versus autonomy

Every platform sits on a tension. Governance keeps the organisation safe, compliant and consistent. Autonomy lets teams move quickly and adapt to their context. Too much governance produces gatekeeping and shadow platforms; too much autonomy produces fragmentation and unmanaged risk.

**A spectrum of control**

| Level | Description | Example |
| --- | --- | --- |
| Mandate | Not optional; enforced by technology | Admission policy requiring signed images in production |
| Standard with exceptions | The default; teams may deviate with a recorded exception | The golden-path template; exceptions reviewed quarterly |
| Recommendation | Guidance with supporting tools | Preferred libraries |
| Free choice | Teams decide | Internal code structure; test frameworks |

**Decide the level by risk and reversibility.**

| Decision type | Risk if wrong | Reversible? | Suggested level |
| --- | --- | --- | --- |
| Security baseline for production | High; affects others | Hard | Mandate, enforced automatically |
| Deployment mechanism | Medium | Moderate | Standard with exceptions |
| Observability format | Medium | Moderate | Standard; flexible content |
| Language and framework | Low to medium | Hard within a team | Recommendation |
| Internal code design | Low | Easy | Free choice |

**Guardrails, not gates.** A *guardrail* prevents harm automatically without a person in the loop and without blocking safe behaviour. A *gate* needs a person. Replace gates with guardrails where possible, and keep gates where judgement is genuinely required, with a time-boxed service level.

**The exception process.** Exceptions are information. A well-run exception process records the reason, the owner, the risk accepted, the compensating control, an expiry date and who approved it. Review them in aggregate: a frequent exception means the standard is wrong; a rare one means it works.

```text
Exception EX-2026-031
Team: payments   Standard: golden-path pipeline   Requested: custom build for a signed hardware module
Reason: toolchain not supported by shared runners
Risk accepted: build not covered by shared provenance workflow
Compensating control: reproducible build on isolated runner, manual attestation by platform
Expiry: 2026-12-31   Approved by: platform lead and security partner
Review trigger: shared runner supports the toolchain
```

**Policy as code with graded enforcement.** Introduce rules in stages: *audit* (report only), *warn* (visible to developers), *enforce* (block). Staging builds trust and finds false positives before they cause outages.

| Stage | Behaviour | Goal |
| --- | --- | --- |
| Audit | Log violations; no impact | Discover prevalence and false positives |
| Warn | Developer sees a message and a fix | Give time to adapt |
| Enforce | Block | Hold the line |
| Review | Check exceptions and false-positive rate | Retire or refine the rule |

**Autonomy needs support.** Granting autonomy without capability produces unsafe teams. Pair autonomy with defaults, documentation and a support route; otherwise "freedom" is simply unsupported risk.

**Who governs the governors.** A platform team that writes policy has power over other teams. Give policies an owner, a change process visible to affected teams, representation from users in review, and an appeal route. Policy that nobody can challenge becomes folklore.

## Evolution of a platform

Platforms age. Their purpose, users and technology change. Plan for evolution as deliberately as for construction.

**Maturity stages**

| Stage | Characteristics | Priority |
| --- | --- | --- |
| Emerging | A few scripts and wiki pages; heroics | Find the most common painful task; solve it end to end |
| Defined | A golden path for the common case; some self-service | Reliability and onboarding |
| Managed | Metrics, SLOs, roadmaps; support model | Reduce toil; expand coverage by evidence |
| Optimised | Self-service by default; continuous improvement | Deprecate; simplify; extend selectively |
| Declining | Features nobody maintains; rising interrupts | Retire parts; rebuild the core of value |

Maturity models describe where you are, not where you must reach. A small organisation can remain "Defined" and be well served.

**Assumption expiry.** Every design rests on assumptions about team count, runtime, traffic, staffing and risk appetite. List them in the ADR set, with the signal that would show each has expired.

| Assumption | Signal that it expired |
| --- | --- |
| One runtime suffices | More than 20 percent of new services need another |
| Four engineers can support the platform | Interrupt rate above half of capacity |
| Namespace tenancy is adequate | A regulated workload arrives |
| Teams are co-located in one time zone | Support requests arrive across three time zones |
| The vendor roadmap fits our needs | Two consecutive releases miss a requirement |

**Platform erosion.** Even without growth, platforms erode: documentation falls behind, templates drift from current practice, dependencies age, owners leave. Reserve capacity for hygiene and track a *freshness score* (percentage of templates built on supported versions, documentation verified in the last 90 days, catalogue records verified).

**The abstraction trap.** Platforms hide complexity behind abstractions. Abstractions leak, and users eventually need to look beneath them. Design **escape hatches** and **visibility**: let users see the generated artefacts, explain what happened and, where safe, override a default with an owned exception. A platform that hides everything makes debugging impossible; one that hides nothing has not reduced load.

| Abstraction level | Strength | Weakness |
| --- | --- | --- |
| Thin (templates and conventions) | Transparent; easy to leave | Users carry more knowledge |
| Medium (declarative service definition) | Concise; policy can attach | A new language to learn; leaks under unusual needs |
| Thick (a custom platform API hiding the runtime) | Very low load for common cases | A product to maintain; hard for unusual cases; lock-in |

Prefer the thinnest abstraction that removes the observed load. Thickness is a cost you pay every year.

**Versioning the platform contract.** Treat templates, APIs and the command line as versioned interfaces. Announce changes, support N and N-1, publish migration guides and measure who is still on old versions.

**Sunsetting.** Retiring a capability needs: an owner, a replacement, a date, a measurement of remaining users, outreach to each, a freeze on new use and a final switch-off with a rollback window.

## Migration

A platform exists to be adopted, and adoption is a migration: from the old way, to the new. Many platforms succeed technically and fail in migration.

**Why migrations stall**

| Cause | Mechanism |
| --- | --- |
| Migration is the users' work, not the platform's | Product teams have no capacity; the platform has no authority |
| The benefit goes to the platform, the cost to the user | Nobody volunteers |
| The long tail | The last 20 percent has unusual requirements and takes 80 percent of effort |
| Parallel running without an end date | Two systems forever |
| No measurable progress | Nobody knows the true remaining scope |

**Migration strategies**

| Strategy | Description | Best when | Risk |
| --- | --- | --- | --- |
| Big bang | All at once, on a date | Small, tightly coupled estate | High blast radius |
| Strangler | New traffic or services use the new path; old ones migrate over time | Most platform adoption | Needs a hard end date or it never completes |
| Lift and shift first | Move as is, then improve | Hard deadline (contract end, data centre exit) | Carries technical debt |
| Platform-led migration | The platform team performs the migration for teams | High value, few users, complex | Does not scale; platform becomes the bottleneck |
| Self-service migration with tooling | Automated analysis, generated changes, tracked progress | Many similar services | Tooling investment; the long tail |

**A migration plan**

```text
Goal: all services on the golden path delivery by 2027-03-31
Scope: 210 services; inventory from catalogue; 38 flagged "unusual"
Waves:
  Wave 0 (pilot, 5 services, volunteers): learn; fix tooling
  Wave 1 (60 services, standard shape): automated pull requests; owners review
  Wave 2 (100 services): same; office hours
  Wave 3 (long tail, 45 services): paired migration or documented exception
Incentives: new production access only on the path from 2026-12-01
Measures: services migrated; services blocked and why; time per migration
Exit: old pipeline switched off 2027-04-30 after 30-day read-only notice
Rollback: per-service rollback to old pipeline until switch-off
```

**Make migration cheap for users.** The platform should do as much of the work as possible: generate the pull request, run the checks, explain the diff. A migration that needs two days of attention from each of 200 teams costs 400 engineer-days; a tool that reduces it to two hours costs less than it takes to argue about.

**Incentives and deadlines.** Voluntary adoption is a signal; migration of an existing estate usually needs a firm date and a clear carrot, such as new capabilities only on the new path, and a stick, such as the old path losing support. A migration with neither will not finish.

**Track the tail honestly.**

| Status | Meaning |
| --- | --- |
| Migrated | On the path; evidence recorded |
| In progress | Owner and date |
| Blocked | A named reason the platform could fix |
| Exception | Approved, with expiry and compensating control |
| Retiring | Service will be decommissioned |

Blocked items are a roadmap input. If many services are blocked on the same missing capability, build it.

**Switch-off discipline.** Old systems should be switched off, not abandoned. Announce, make read-only, wait, then remove. A "temporary" parallel system that remains for two years doubles the operations cost and the attack surface.

## Incentive failures

Platform outcomes follow incentives, not intentions. Most platform failures that look technical are incentive failures in disguise.

| Failure | Incentive | Result | Defence |
| --- | --- | --- | --- |
| Metric gaming | The platform team is rewarded for adoption count | Teams are pushed on to the path regardless of fit; satisfaction falls | Pair adoption with sentiment and exit rate |
| Resume-driven platform | Engineers are rewarded for building impressive systems | Overbuilt, hard to maintain | Reward outcomes and deletions; require ADR evidence |
| Cover-your-back governance | A security or compliance function is blamed for incidents, not for friction | Excessive gates | Measure the cost of gates; share accountability |
| Local optimisation | Each team optimises its own metric | Duplicated tooling; missing shared concerns | Shared goals; explicit platform funding |
| Throw-it-over-the-wall | Product teams are rewarded for features, not for operability | Operability debt; the platform absorbs the risk | Include reliability in team goals; production readiness reviews |
| Hero culture | Heroic firefighting is praised more than prevention | Fragile systems; burnout | Recognise prevention; blameless review |
| Capacity starvation | The platform is funded as cost, not investment | Foundations decay; incidents | Reserve capacity; show the cost of deferral |
| Shadow IT | Official path is slower than workarounds | Parallel platforms | Treat as research; fix the path |
| Vanity roadmaps | Leadership rewards visible launches | Shiny features; hidden decay | Roadmaps show removal and hygiene |

**Goodhart's law.** When a measure becomes a target, it ceases to be a good measure. Defences: pair metrics with counter-metrics, rotate them, include qualitative review and keep them away from individual performance reviews.

**Align incentives deliberately.** Ask of every important behaviour: *what does the system reward?* If production readiness is not rewarded for product teams, it will not happen. If deletion is not rewarded for platform teams, nothing will be deleted.

**Perverse effects of mandates.** A mandate without capacity creates malicious compliance: the box is ticked, the intent is lost. The remedy is to make the right behaviour the easy behaviour and to audit outcomes, not artefacts.

## Architecture defence

A defence is a walkthrough followed by challenge by someone who has read your records. You are judged on *fidelity between claims and evidence* and on *trade-off reasoning*, not on how impressive the stack is. Keep a claims ledger with status values *Proven*, *Partial* and *Unproven*.

| Claim | Evidence | Status |
| --- | --- | --- |
| A stranger can create and deploy a service without help | Acceptance record | Proven (n = 1) |
| Artefacts are traceable to a commit | Verification output | Proven for CI-built images |
| Pod loss does not lose data | Drill timeline | Proven (practice cluster, single replica) |
| Node or cluster loss is recoverable | — | Unproven |
| The platform is secure | Policy and access transcripts | Partial — see limitations |

Claiming more than the ledger supports is the cardinal sin. Rehearse with a peer who scores *evidence for each answer, honesty about limits, named trade-offs* and *consistency with the decision records*.

**Questions a reviewer will ask**

1. Why this runtime rather than the alternative, and what would change your mind?
2. What does provenance prove, and what can a compromised build system still do?
3. Who can change production-shaped state, by what path, and where is that enforced?
4. A developer needs a database tomorrow — what happens, and who waits?
5. Where was your recovery-point target measured, and what if the backup job silently fails?
6. What does your status command *not* tell a developer?
7. What happens when the golden path is wrong for a team?
8. What did you decide not to build, and why was that right?
9. How much of this can a single maintainer sustain?
10. Which assumption in your ADRs is closest to expiring, and what is the signal?
11. If funding halves next year, what do you stop, and in what order?
12. How would a tenant's failure affect another tenant, and where was that tested?

## Failure catalogue (organisational)

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Portal-first platform | Interface built before the path works | Trial before tooling; the decision test "would this remove an observed stuck point?" |
| Ticket queue with extra steps | Human gates for routine work | Automate; keep only designed, time-boxed human gates |
| Mandated mediocrity | Forced adoption of a poor path | Voluntary adoption signals; fast iteration |
| Unowned platform | Maintainer leaves | Documentation, runbooks, bus factor ≥ 2 |
| Overclaiming | Slides exceed evidence | Claims ledger reviewed by someone else |
| Silent gaps | Limitations discovered in incidents | Register maintained continuously |
| Stalled migration | Two systems indefinitely | End date, tail tracking, switch-off discipline |
| Leaky tenancy | Shared resource crosses a boundary | Per-dimension isolation review; tenant tests |
| Governance drift | Rules nobody can challenge | Policy owners, appeals, graded enforcement |

## Case catalogue

### Case 1 — The golden path nobody walked

A platform team ships a polished path and measures adoption by templates created. Numbers look excellent; incident rates do not move. Investigation shows that teams create the template, then replace its pipeline within a week because it does not support their test setup. The metric counted creation, not retention. Lesson: measure sustained use and exits, interview the people who left, and treat replacement as the most valuable feedback.

### Case 2 — The shared controller

A team installs a custom controller in the shared cluster to automate environment creation. A bug causes a reconciliation loop that issues thousands of API calls, degrading the control plane for every tenant. Quotas on compute held; no limit existed on object creation or controller request rates. Lesson: control-plane protection is part of tenancy design; every controller needs request limits, ownership and a kill switch.

### Case 3 — The migration that finished at 85 percent

A pipeline migration reaches 85 percent, then stalls because remaining services have unusual build steps. Two systems run for two years, with security patches applied to both. The programme had no end date and no mechanism to help the tail. Lesson: set the switch-off date at the start, fund tail migration explicitly and give each blocked service a named platform fix or an approved exception.

### Case 4 — The gate that nobody could remove

A manual security review for every new environment is introduced after one incident. Volume grows, wait times reach a week, and teams begin reusing old environments to avoid the queue, creating a worse risk. The review stopped no issue in the following year, but nobody dared remove it. Lesson: compute the cost of a gate, replace it with automated policy and a sampled review, and set a review date when the gate is created.

### Case 5 — The platform that was cut

During a cost-saving year the platform's support rotation is removed and the roadmap frozen. Interrupts rise, upgrades are delayed and an expired certificate in a shared component causes an outage. The savings were real, the avoided costs invisible. Lesson: record the cost of deferral before cuts, keep a minimum viable capacity for operations and hygiene, and make the risk visible to the funder.

## Expert trade-offs

| Tension | One side | Other side | Resolution |
| --- | --- | --- | --- |
| Consistency versus fit | One path for all | Paths per workload type | A small number of paths, each justified by evidence; documented exits |
| Thin versus thick abstraction | Transparent templates | A custom platform API | Thinnest abstraction that removes the observed load |
| Central versus federated | One team, one front door | Several domain platform teams | Federate behind one experience layer |
| Mandate versus voluntary | Guaranteed adoption | Honest signal | Mandate safety; compete on experience |
| Shared tenancy versus isolation | Low cost | Strong blast-radius limits | By tenant risk tier |
| Build versus buy | Fit and control | Speed and market maturity | Buy commodities; build the glue |
| Speed of migration versus tail care | Finish fast | Help the awkward cases | A date, a tool and a funded tail |
| Governance versus autonomy | Control | Speed | Guardrails by risk and reversibility; exceptions as data |
| Chargeback versus central funding | Price signal | Low friction | Free defaults, priced extras |
| Roadmap breadth versus operational health | More features | Reliability and hygiene | A visible reserved share |

A useful expert habit is to **write the sentence before choosing**: "We accept *cost* to reduce *specific risk*, and we will know it failed when *observable signal*." If you cannot complete that sentence, the decision is cargo cult.

## Knowledge consolidation

- The **operating model** (central, federated, embedded, inner-source) is a design choice with typical failures; layered platforms need versioned, tested interfaces between layers.
- **Platform economics** have fixed, variable, step and hidden costs; value comes from time, risk, consistency and option value, and a break-even calculation shows which claims need evidence.
- **Pricing signals** work best as free safe defaults, priced extras and quotas; compute the cost of human gates.
- **Multi-tenancy** is a spectrum of isolation across identity, network, compute, data, control plane, observability, cost and failure; a tenant manifest and lifecycle make it explicit.
- **Governance and autonomy** are balanced by risk and reversibility; guardrails beat gates; exceptions are data; enforcement is staged.
- **Evolution** requires assumption expiry signals, hygiene capacity, the thinnest effective abstraction, versioned contracts and disciplined sunsetting.
- **Migration** succeeds with a date, tooling, a funded tail, honest tracking and switch-off; parallel systems are expensive.
- **Incentives** explain most platform failures; pair metrics with counter-metrics and ask what the system rewards.
- A **claims ledger** (*Proven*, *Partial*, *Unproven*) keeps a defence honest.

## Exercises

**Exercise 1 — Choose an operating model.** For an organisation with 300 engineers across 12 product teams and three regulatory regimes, choose an operating model, justify it using the five questions and name its typical failure and your defence.

**Exercise 2 — Break-even.** Build the break-even calculation for a platform with your own numbers. Identify which value sources you can evidence and which you cannot, and what experiment would convert one into evidence.

**Exercise 3 — Cost of a gate.** Pick a human approval step. Compute its annual cost in blocked effort and compare it with the harm it prevents. Propose an automated guardrail and a sampled review.

**Exercise 4 — Tenancy review.** Take a shared-cluster design and walk the eight isolation dimensions. For each, state the control, the evidence that it works and one test you would run. Identify the weakest dimension.

**Exercise 5 — Tenant lifecycle.** Write the onboarding, quota change, ownership transfer and offboarding steps for a tenant, including what is deleted and what is retained for audit.

**Exercise 6 — Governance staging.** Choose a policy rule. Design its audit, warn and enforce stages, the metric that triggers progression and the exception process.

**Exercise 7 — Assumption register.** List eight assumptions underlying a platform and the signal that would show each has expired. Rank by closeness to expiry.

**Exercise 8 — Migration plan.** Write a migration plan for 150 services, with waves, tooling, incentives, tail handling, end date and rollback. Include how you will report progress honestly.

**Exercise 9 — Incentive audit.** Choose three behaviours you want from product teams and three from the platform team. For each, state what the current system rewards, and one change to align it.

**Exercise 10 — Claims ledger.** Write ten claims about a platform, with evidence and status. Identify the weakest and the cheapest experiment that would upgrade it.

**Solution notes.**

*Exercise 1.* A defensible answer is often a central platform team with a federated layer for the regulated domains, behind one experience layer. Marks go for naming the failure (multiple front doors, bottleneck) and a concrete defence (a single catalogue and interface; published service levels), not for a particular model.

*Exercise 2.* Be sceptical of time saved alone: a required saving of several hours per engineer per week is often not demonstrable. Risk and option value need their own evidence, such as past migrations completed without product team effort or time to patch a widespread vulnerability.

*Exercise 3.* Typical results show hundreds of hours blocked per year against a handful of prevented issues. The point is not that review is useless but that a sampled or automated control usually captures most of the value at lower cost.

*Exercise 4.* The weakest dimension is commonly the control plane or observability scoping, because compute quotas get attention first. Tests include creating objects at scale in one tenant while measuring API latency in another, and querying logs across tenant labels.

*Exercise 5.* Offboarding should revoke identities, delete or archive data under policy, release quotas and update the catalogue; audit records should outlive the tenant. A lifecycle without offboarding is incomplete.

*Exercise 6.* Progression should depend on a false-positive rate and a violation trend, not on a calendar date. A good exception process has owner, expiry and compensating control.

*Exercise 7.* Typical near-expiry assumptions are staffing capacity and runtime coverage. Signals should be numbers collected routinely.

*Exercise 8.* Look for an end date, a funded tail and tooling that does most of the work. A plan that depends on volunteers alone will stall.

*Exercise 9.* Typical misalignment: product teams are rewarded for features, not operability; platform teams for creation, not deletion. Changes might include production-readiness goals in team objectives and recognition for retiring components.

*Exercise 10.* Most ledgers contain more *Partial* and *Unproven* claims than authors expect. The cheapest upgrade is often a timed independent trial or a restore drill.

## Mentoring prompts

How would you decide whether your organisation needs a portal? Draft the three non-goals that would protect your platform from becoming a general-purpose PaaS. Which claim in your own ledger is weakest, and what is the cheapest experiment that would upgrade it? If your platform were funded at half its current level, what would you stop first and what risk would that create? Which team in your organisation has the strongest incentive to bypass the platform, and what does that tell you? Which assumption in your decision records is most likely to expire next year, and what would you do on the day it does? Describe a migration you have seen stall and say what end date, tool or incentive would have finished it.

---
